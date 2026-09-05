import asyncio
import hashlib
import os
import sqlite3
from bilibili_api import Credential
from bilibili_api import comment
import json
from bilibili_api.utils.network import Api
from bilibili_api.utils.aid_bvid_transformer import bvid2aid
import time
import aiohttp.http_exceptions as aiohttp_http_exceptions
import aiohttp.client_exceptions
from html.parser import HTMLParser
import httpx
from datetime import datetime, timezone
from pathlib import Path

os.environ['NO_PROXY'] = 'bilibili.com,api.bilibili.com,*.bilibili.com,127.0.0.1,localhost'


COMMENT_DB_SCHEMA_VERSION = "v1.1"
COMMENT_VOLATILE_FIELDS = (
    "count", "rcount", "state", "fansgrade",
    "attr", "like", "action", "invisible", "reply_control",
)
COMMENT_SKIPPED_FIELDS = {"replies"}
COMMENT_REPLY_CONTROL_FIELDS = (
    "max_line", "location", "translation_switch", "support_share",
)


def quote_db_identifier(name: str) -> str:
    """安全引用由 B 站 JSON 键产生的 SQLite 表名或列名。"""
    if "\x00" in name:
        raise ValueError("评论键包含 NUL，不能用作 SQLite 标识符")
    return '"' + name.replace('"', '""') + '"'


def compact_json(value, sort_keys=False) -> str:
    """字典和列表按照 v1.1 规则保存为紧凑 JSON 文本。"""
    return json.dumps(
        value, ensure_ascii=False, sort_keys=sort_keys,
        separators=(",", ":"), allow_nan=False,
    )


def database_value(value):
    """嵌套结构保存为 JSON 字符串，标量尽量保留 SQLite 原生类型。"""
    if isinstance(value, (dict, list)):
        return compact_json(value)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int) and not -(2 ** 63) <= value <= 2 ** 63 - 1:
        return str(value)
    return value


def reply_control_value(value):
    """过滤动态 time_desc 等字段，只保存四个稳定键的 JSON 文本。"""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("reply_control 必须是字典或 null")
    filtered = {
        key: value[key]
        for key in COMMENT_REPLY_CONTROL_FIELDS
        if key in value
    }
    return compact_json(filtered)


def stable_hash(value) -> str:
    data = compact_json(value, sort_keys=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def comment_rpid(comment_dict: dict) -> int:
    value = comment_dict.get("rpid_str", comment_dict.get("rpid"))
    if value in (None, ""):
        raise ValueError("评论缺少 rpid/rpid_str")
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"无效 rpid：{value!r}") from error
    if not -(2 ** 63) <= result <= 2 ** 63 - 1:
        raise ValueError(f"rpid 超出 SQLite 64 位整数范围：{result}")
    return result


def iter_nested_replies(comment_dict: dict):
    """按原顺序迭代所有层级回复，不复制回复字典。"""
    replies = comment_dict.get("replies")
    if replies is None:
        return
    if not isinstance(replies, list):
        raise ValueError(f"评论 {comment_rpid(comment_dict)} 的 replies 不是列表或 null")
    stack = list(reversed(replies))
    while stack:
        reply = stack.pop()
        if not isinstance(reply, dict):
            raise ValueError(f"评论 {comment_rpid(comment_dict)} 含非字典回复")
        yield reply
        children = reply.get("replies")
        if children is None:
            continue
        if not isinstance(children, list):
            raise ValueError(f"回复 {comment_rpid(reply)} 的 replies 不是列表或 null")
        stack.extend(reversed(children))


class StreamingCommentDatabaseWriter:
    """独立的 v1.1 流式写库器；每页写完即可释放该页评论对象。"""

    def __init__(self, output_path: Path, source_url: str, bvid: str, aid: int):
        self.output_path = Path(output_path).resolve()
        self.temporary_path = self.output_path.with_name(self.output_path.name + ".tmp")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None
        self.finished = False
        self.main_count = 0
        self.top_count = 0
        self.reply_count = 0
        self.source_url = source_url
        self.bvid = bvid
        self.aid = aid
        self.source_hasher = hashlib.sha256()
        self.comment_columns = {"rpid", "member", "content", "_volatile_hash"}
        self.entity_columns = {
            "member": {"parent", "_comment_kind", "_data_hash"},
            "content": {"parent", "_comment_kind", "_data_hash"},
        }

        self._remove_temporary_files()
        self.connection = sqlite3.connect(str(self.temporary_path))
        self.connection.execute("PRAGMA foreign_keys=ON")
        self._create_initial_schema()

    def _remove_temporary_files(self):
        """只清理由本写库器固定命名的临时数据库及 SQLite 辅助文件。"""
        for path in (
            self.temporary_path,
            Path(str(self.temporary_path) + "-journal"),
            Path(str(self.temporary_path) + "-wal"),
            Path(str(self.temporary_path) + "-shm"),
        ):
            if path.exists():
                path.unlink()

    def _create_initial_schema(self):
        self.connection.execute(
            "CREATE TABLE _metadata("
            "metadata_key TEXT PRIMARY KEY, metadata_value TEXT NOT NULL)"
        )
        for table_name in ("member", "content"):
            self.connection.execute(
                f'CREATE TABLE {quote_db_identifier(table_name)}('
                "parent INTEGER PRIMARY KEY,"
                "_comment_kind TEXT NOT NULL "
                "CHECK(_comment_kind IN ('main','reply')),"
                "_data_hash TEXT NOT NULL)"
            )
        # top 单独保存置顶评论；实体表仍把 top 视为顶层 main，兼容旧 v1.1。
        for table_name in ("main", "top", "reply"):
            self.connection.execute(
                f'CREATE TABLE {quote_db_identifier(table_name)}('
                "rpid INTEGER PRIMARY KEY,"
                "member INTEGER,"
                "content INTEGER,"
                "_volatile_hash TEXT NOT NULL,"
                "FOREIGN KEY(member) REFERENCES member(parent),"
                "FOREIGN KEY(content) REFERENCES content(parent))"
            )
        self.connection.commit()

    def _ensure_comment_columns(self, comment_dict: dict):
        """分页过程中遇到新一级键时，同时扩展三张评论表。"""
        for key in comment_dict:
            if key in COMMENT_SKIPPED_FIELDS or key in self.comment_columns:
                continue
            if key == "_volatile_hash":
                raise ValueError(f"评论键与内部列冲突：{key}")
            quoted_key = quote_db_identifier(key)
            for table_name in ("main", "top", "reply"):
                self.connection.execute(
                    f'ALTER TABLE {quote_db_identifier(table_name)} '
                    f'ADD COLUMN {quoted_key}'
                )
            self.comment_columns.add(key)

    def _ensure_entity_columns(self, table_name: str, data: dict):
        reserved = {"parent", "_comment_kind", "_data_hash"}
        conflicts = reserved.intersection(data)
        if conflicts:
            raise ValueError(
                f"{table_name} 键与内部列冲突：{','.join(sorted(conflicts))}"
            )
        for key in data:
            if key in self.entity_columns[table_name]:
                continue
            self.connection.execute(
                f'ALTER TABLE {quote_db_identifier(table_name)} '
                f'ADD COLUMN {quote_db_identifier(key)}'
            )
            self.entity_columns[table_name].add(key)

    def _insert_entity(self, table_name: str, parent: int, kind: str, data):
        if not isinstance(data, dict):
            return None
        self._ensure_entity_columns(table_name, data)
        columns = ["parent", "_comment_kind", "_data_hash"] + list(data.keys())
        values = [parent, kind, stable_hash(data)]
        values.extend(database_value(value) for value in data.values())
        self.connection.execute(
            "INSERT INTO {}({}) VALUES({})".format(
                quote_db_identifier(table_name),
                ",".join(quote_db_identifier(column) for column in columns),
                ",".join("?" for _ in columns),
            ), values,
        )
        return parent

    def _volatile_hash(self, comment_dict: dict) -> str:
        values = {
            field: comment_dict.get(field)
            for field in COMMENT_VOLATILE_FIELDS
        }
        # 与实际入库值保持一致，不能让被过滤的 time_desc 影响快照比较。
        values["reply_control"] = reply_control_value(
            comment_dict.get("reply_control")
        )
        return stable_hash(values)

    def _insert_comment(self, table_name: str, comment_dict: dict):
        self._ensure_comment_columns(comment_dict)
        rpid = comment_rpid(comment_dict)
        kind = "reply" if table_name == "reply" else "main"
        member_ref = self._insert_entity(
            "member", rpid, kind, comment_dict.get("member")
        )
        content_ref = self._insert_entity(
            "content", rpid, kind, comment_dict.get("content")
        )
        columns = ["rpid", "member", "content", "_volatile_hash"]
        values = [rpid, member_ref, content_ref, self._volatile_hash(comment_dict)]
        for key, value in comment_dict.items():
            if key in COMMENT_SKIPPED_FIELDS or key in {
                "rpid", "member", "content", "_volatile_hash"
            }:
                continue
            columns.append(key)
            if key == "reply_control":
                values.append(reply_control_value(value))
            else:
                values.append(database_value(value))
        self.connection.execute(
            "INSERT INTO {}({}) VALUES({})".format(
                quote_db_identifier(table_name),
                ",".join(quote_db_identifier(column) for column in columns),
                ",".join("?" for _ in columns),
            ), values,
        )

    def write_main_comment(self, comment_dict: dict):
        """写入一条主评论及其回复；对象不会被写库器长期持有。"""
        self._insert_comment("main", comment_dict)
        reply_count = 0
        for reply in iter_nested_replies(comment_dict):
            self._insert_comment("reply", reply)
            reply_count += 1
        encoded = compact_json(comment_dict, sort_keys=True).encode("utf-8")
        self.source_hasher.update(len(encoded).to_bytes(8, "big"))
        self.source_hasher.update(encoded)
        self.main_count += 1
        self.reply_count += reply_count

    def write_top_comment(self, comment_dict: dict):
        """写入一条置顶评论及其回复；置顶评论不重复写入 main。"""
        self._insert_comment("top", comment_dict)
        reply_count = 0
        for reply in iter_nested_replies(comment_dict):
            self._insert_comment("reply", reply)
            reply_count += 1
        encoded = compact_json(comment_dict, sort_keys=True).encode("utf-8")
        self.source_hasher.update(len(encoded).to_bytes(8, "big"))
        self.source_hasher.update(encoded)
        self.top_count += 1
        self.reply_count += reply_count

    def commit_page(self):
        """一页处理结束后提交，使该页 Python 对象可以立即回收。"""
        self.connection.commit()

    def _create_indexes(self):
        for table_name in ("main", "top", "reply"):
            for key in ("mid", "ctime", "like", "parent", "root"):
                if key not in self.comment_columns:
                    continue
                self.connection.execute(
                    "CREATE INDEX {} ON {}({})".format(
                        quote_db_identifier(f"idx_{table_name}_{key}"),
                        quote_db_identifier(table_name),
                        quote_db_identifier(key),
                    )
                )

    def finalize(self):
        """补索引和元数据，校验成功后原子替换正式 comment.db。"""
        if self.finished:
            raise RuntimeError("评论数据库已经完成")
        try:
            self._create_indexes()
            metadata = {
                "schema_version": COMMENT_DB_SCHEMA_VERSION,
                "source_name": self.source_url,
                "source_sha256": self.source_hasher.hexdigest(),
                "source_hash_mode": "streamed-top-level-comments-v2",
                "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "main_count": str(self.main_count),
                "top_count": str(self.top_count),
                "reply_count": str(self.reply_count),
                "volatile_fields": ",".join(COMMENT_VOLATILE_FIELDS),
                "reply_control_fields": ",".join(COMMENT_REPLY_CONTROL_FIELDS),
                "source_url": self.source_url,
                "bvid": self.bvid,
                "aid": str(self.aid),
            }
            self.connection.executemany(
                "INSERT INTO _metadata VALUES(?,?)", metadata.items()
            )
            self.connection.commit()
            foreign_key_errors = self.connection.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()
            if foreign_key_errors:
                raise sqlite3.IntegrityError(
                    f"评论数据库外键检查失败：{foreign_key_errors[:3]}"
                )
            integrity = self.connection.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise sqlite3.DatabaseError(f"评论数据库完整性检查失败：{integrity}")
            member_count = self.connection.execute(
                "SELECT COUNT(*) FROM member"
            ).fetchone()[0]
            content_count = self.connection.execute(
                "SELECT COUNT(*) FROM content"
            ).fetchone()[0]
            self.connection.close()
            self.connection = None
            os.replace(self.temporary_path, self.output_path)
            self.finished = True
        except Exception:
            self.abort()
            raise
        result = {
            "main": self.main_count, "top": self.top_count,
            "reply": self.reply_count,
            "member": member_count, "content": content_count,
        }
        print(f"评论数据库已生成：{self.output_path}")
        print(
            "数据库记录：main={main}，top={top}，reply={reply}，"
            "member={member}，content={content}".format(**result)
        )
        return self.output_path, result

    def abort(self):
        """回滚并删除半成品；不会修改已有的正式 comment.db。"""
        if self.connection is not None:
            try:
                self.connection.rollback()
            finally:
                self.connection.close()
                self.connection = None
        if not self.finished:
            self._remove_temporary_files()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.finished:
            self.abort()
        return False

use_cookie = {}
with open("cookie.json","r") as f:
    use_cookie = json.load(f)
credential_ = Credential(sessdata=use_cookie["SESSDATA"],
  bili_jct=use_cookie["bili_jct"], 
  buvid3=use_cookie["buvid3"])

def get_image_name_by_URL(url: str) -> str:
    if not url:
        return ""
    return os.path.basename(url)

async def get_sub_comment_by_dict(
    cmt_dict:dict, 
    credential:Credential
    ) -> bool:
    """
    获取某条评论字典的所有子评论。获取到的子评论会放到cmt_dict的"replies"列表中。
    :param cmt_dict: 评论字典
    :param credential: Bilibili API凭证对象
    """
    rpid = cmt_dict.get("rpid", 0)
    oid = cmt_dict.get("oid", 0)
    type_ = cmt_dict.get("type", 0)
    if not (rpid and oid and type_):
        return False
    cmt_dict["replies"] = []
    cmt = comment.Comment(credential=credential, rpid=rpid, oid=oid, type_=comment.CommentResourceType.VIDEO)
    index = 1
    while True:
        try:
            replies_dic = await cmt.get_sub_comments(page_index=index)
        except Exception as e:
            print(f"获取子评论失败: {e}")
            return False
        replies = replies_dic.get("replies", [])
        if not replies:
             break
        index += 1
        await asyncio.sleep(0.1)
        cmt_dict["replies"].extend(replies)
    # with open('replies-test.json', 'w', encoding='utf-8') as f:
    #     json.dump(cmt_dict, f, ensure_ascii=False, indent=4)
    print(f"获取到{len(cmt_dict['replies'])}条子评论")
    return True

def remap_avatar_item_layers_to_local(
    avatar_item_layers_list:list, 
    to_download_resources_URL:dict
    ) :
    next_list = avatar_item_layers_list
    list_list = []
    while True:
        if list_list:
            next_list = list_list[0]
            list_list.pop(0)
        if not next_list:
            break
        for layer in next_list:
            new_layers = layer.get("layers", None)
            if new_layers:
                list_list.append(new_layers)
            resource = layer.get("resource", None)
            if resource:
                res_type = resource.get("res_type", None)
                if res_type == 3:
                    res_image = resource.get("res_image", None)
                    if res_image:
                        image_src = res_image.get("image_src", None)
                        if image_src:
                           img_remote = image_src.get("remote", None)
                           if img_remote:
                               url = img_remote.get("url", '')
                               if url:
                                   type_name = save_url_to_dict(url, to_download_resources_URL)
                                   img_name = get_image_name_by_URL(url)
                                   img_remote["url"] = f"./comment-resource/{type_name}/{img_name}"
                elif res_type == 4:
                    res_animation = resource.get("res_animation", None)
                    if res_animation:
                        webp_src = res_animation.get("webp_src", None)
                        if webp_src:
                            remote = webp_src.get("remote", None)
                            if remote:
                                url = remote.get("url", '')
                                if url:
                                    type_name = save_url_to_dict(url, to_download_resources_URL)
                                    img_name = get_image_name_by_URL(url)
                                    remote["url"] = f"./comment-resource/{type_name}/{img_name}"
        next_list = []

def save_url_to_dict(
    url:str,
    to_download_resources_URL:dict
    ) -> str:
    """
    将URL添加到to_download_resources_URL字典的对应列表中。
    根据URL的类型自动分类，将其放到对应的列表中。
    :param url: 要添加的URL
    :param to_download_resources_URL: 资源URL字典
    :return: 分类后的URL类型名称(文件夹名称)
    """
    numind = url.find("hdslb.com/bfs/") + 14
    if numind >14:
        type_name = url[numind:]
        if type_name.startswith("face"):
            to_download_resources_URL["avatar"].add(url)
            return "avatar"
        elif type_name.startswith("garb"):
            to_download_resources_URL["pendant"].add(url)
            return "pendant"
        elif type_name.startswith("baselabs"):
            to_download_resources_URL["baselabs"].add(url)
            return "baselabs"
        elif type_name.startswith("activity-plat"):
            to_download_resources_URL["pendant"].add(url)
            return "pendant"
        else:
            to_download_resources_URL["others"].add(url)
            return "others"
    else:
        to_download_resources_URL["others"].add(url)
        return "others"

def remap_cmt_to_local(
    cmt_dict:dict, 
    to_download_resources_URL:dict
    ) :
    """
    映射评论字典到本地资源。
    该函数会解析评论字典，将其中的资源URL放到to_download_resources_URL字典的
    对应列表中，同时将评论字典中的资源URL替换为其将要被下载到的本地资源路径。
    （该函数没有下载功能，需要后续代码根据to_download_resources_URL字典下载资源）
    :param cmt_dict: 评论字典
    :param to_download_resources_URL: 资源URL字典
    """
    mumber_info = cmt_dict.get("member", None)
    if mumber_info:
        avatar_url = mumber_info.get("avatar", '')
        if avatar_url:
            to_download_resources_URL["avatar"].add(avatar_url)
            avatar_img_name = get_image_name_by_URL(avatar_url)
            mumber_info["avatar"] = f"./comment-resource/avatar/{avatar_img_name}"
        vip_info = mumber_info.get("vip", None)
        if vip_info:
            vip_lable_info = vip_info.get("label", None)
            if vip_lable_info:
                vip_img_url = vip_lable_info.get("img_label_uri_hans_static", '')
                if vip_img_url:
                    vip_img_name = get_image_name_by_URL(vip_img_url)
                    to_download_resources_URL["vip"].add(vip_img_url)
                    vip_lable_info["img_label_uri_hans_static"] = f"./comment-resource/vip/{vip_img_name}"
                vip_img_url1 = vip_lable_info.get("img_label_uri_hant_static", '')
                if vip_img_url1:
                    to_download_resources_URL["vip"].add(vip_img_url1)
                    vip_img_name1 = get_image_name_by_URL(vip_img_url1)
                    vip_lable_info["img_label_uri_hant_static"] = f"./comment-resource/vip/{vip_img_name1}"

                vip_annual_img_url = vip_lable_info.get("path", '')
                if vip_annual_img_url:
                    to_download_resources_URL["vip"].add(vip_annual_img_url)
                    vip_annual_img_name = get_image_name_by_URL(vip_annual_img_url)
                    vip_lable_info["path"] = f"./comment-resource/vip/{vip_annual_img_name}"

                img_label_uri_hans = vip_lable_info.get("img_label_uri_hans", '')#超级大会员动态星标
                if img_label_uri_hans:
                    to_download_resources_URL["vip"].add(img_label_uri_hans)
                    img_label_uri_hans_name = get_image_name_by_URL(img_label_uri_hans)
                    vip_lable_info["img_label_uri_hans"] = f"./comment-resource/vip/{img_label_uri_hans_name}"
                
                img_label_uri_hant = vip_lable_info.get("img_label_uri_hant", '')#超级大会员动态星标
                if img_label_uri_hant:
                    to_download_resources_URL["vip"].add(img_label_uri_hant)
                    img_label_uri_hant_name = get_image_name_by_URL(img_label_uri_hant)
                    vip_lable_info["img_label_uri_hant"] = f"./comment-resource/vip/{img_label_uri_hant_name}"

        user_sailing_info = mumber_info.get("user_sailing", None)      
        if user_sailing_info:
            cardbg_info = user_sailing_info.get("cardbg", None)
            if cardbg_info:
                cardbg_img_url = cardbg_info.get("image", '')
                if cardbg_img_url:
                    to_download_resources_URL["card"].add(cardbg_img_url)
                    cardbg_img_name = get_image_name_by_URL(cardbg_img_url)
                    cardbg_info["image"] = f"./comment-resource/card/{cardbg_img_name}"
        
        pendant_info = mumber_info.get("pendant", None)
        if pendant_info:
            pendant_img_url = pendant_info.get("image", '')
            if pendant_img_url:
                to_download_resources_URL["pendant"].add(pendant_img_url)
                pendant_img_name = get_image_name_by_URL(pendant_img_url)
                pendant_info["image"] = f"./comment-resource/pendant/{pendant_img_name}"
        
        nft_info = mumber_info.get("nft_interaction", None) #彩钻标识(拥有数字藏品)
        if nft_info:
            region_info = nft_info.get("region", None)
            if region_info:
                region_img_url = region_info.get("icon", '')
                if region_img_url:
                    to_download_resources_URL["vip"].add(region_img_url)
                    region_img_name = get_image_name_by_URL(region_img_url)
                    region_info["icon"] = f"./comment-resource/vip/{region_img_name}"
        
        avatar_item = mumber_info.get("avatar_item", None)
        if avatar_item:
            layers = avatar_item.get("layers", [])
            if layers:
                remap_avatar_item_layers_to_local(layers,to_download_resources_URL)

            fallback_layers = avatar_item.get("fallback_layers", None)
            if fallback_layers:
                layers_2 = fallback_layers.get("layers", [])
                if layers_2:
                    remap_avatar_item_layers_to_local(layers_2,to_download_resources_URL)
    
    content_info = cmt_dict.get("content", None)
    if content_info:
        emote = content_info.get("emote", None)
        if emote:
            for emote_ in emote.keys():
                emote_url = emote[emote_].get("url", '')
                if emote_url:
                    to_download_resources_URL["emoji"].add(emote_url)
                    emote[emote_]["url"] = f"./comment-resource/emoji/{get_image_name_by_URL(emote_url)}"

        pic_info = content_info.get("pictures", [])
        for pic_ in pic_info:
            pic_url = pic_.get("img_src", '')
            if pic_url:
                to_download_resources_URL["picture"].add(pic_url)
                pic_["img_src"] = f"./comment-resource/picture/{get_image_name_by_URL(pic_url)}"
            
            pic_vip_icon_url = pic_.get("top_right_icon", '')
            if pic_vip_icon_url:
                to_download_resources_URL["vip"].add(pic_vip_icon_url)
                pic_["top_right_icon"] = f"./comment-resource/vip/{get_image_name_by_URL(pic_vip_icon_url)}"

        jump_url_info = content_info.get("jump_url", None)
        if jump_url_info:
            for jump_, jump_info in jump_url_info.items():
                jump_icon_url = jump_info.get("prefix_icon", '')
                if jump_icon_url:
                    to_download_resources_URL["icons"].add(jump_icon_url)
                    jump_url_info[jump_]["prefix_icon"] = f"./comment-resource/icons/{get_image_name_by_URL(jump_icon_url)}"
            

    replies = cmt_dict.get("replies", None)
    if replies:
        for reply in replies:
            rep_member_info = reply.get("member", None)
            if rep_member_info:
                rep_avatar_url = rep_member_info.get("avatar", '')
                if rep_avatar_url:
                    to_download_resources_URL["avatar"].add(rep_avatar_url)
                    rep_avatar_img_name = get_image_name_by_URL(rep_avatar_url)
                    rep_member_info["avatar"] = f"./comment-resource/avatar/{rep_avatar_img_name}"
                
                rep_vip_info = rep_member_info.get("vip", None)
                if rep_vip_info:
                    rep_vip_lable_info = rep_vip_info.get("label", None)
                    if rep_vip_lable_info:
                        rep_vip_img_url = rep_vip_lable_info.get("img_label_uri_hans_static", '')
                        if rep_vip_img_url:
                            rep_vip_img_name = get_image_name_by_URL(rep_vip_img_url)
                            to_download_resources_URL["vip"].add(rep_vip_img_url)
                            rep_vip_lable_info["img_label_uri_hans_static"] = f"./comment-resource/vip/{rep_vip_img_name}"
                        rep_vip_img_url1 = rep_vip_lable_info.get("img_label_uri_hant_static", '')
                        if rep_vip_img_url1:
                            to_download_resources_URL["vip"].add(rep_vip_img_url1)
                            rep_vip_img_name1 = get_image_name_by_URL(rep_vip_img_url1)
                            rep_vip_lable_info["img_label_uri_hant_static"] = f"./comment-resource/vip/{rep_vip_img_name1}"

                        rep_vip_annual_img_url = rep_vip_lable_info.get("path", None)
                        if rep_vip_annual_img_url:
                            to_download_resources_URL["vip"].add(rep_vip_annual_img_url)
                            rep_vip_annual_img_name = get_image_name_by_URL(rep_vip_annual_img_url)
                            rep_vip_lable_info["path"] = f"./comment-resource/vip/{rep_vip_annual_img_name}"
                        
                        rep_vip_img_url2 = rep_vip_lable_info.get("img_label_uri_hant", None)
                        if rep_vip_img_url2:
                            to_download_resources_URL["vip"].add(rep_vip_img_url2)
                            rep_vip_img_name2 = get_image_name_by_URL(rep_vip_img_url2)
                            rep_vip_lable_info["img_label_uri_hant"] = f"./comment-resource/vip/{rep_vip_img_name2}"

                        rep_img_label_uri_hans = rep_vip_lable_info.get("img_label_uri_hans", '')
                        if rep_img_label_uri_hans:
                            to_download_resources_URL["vip"].add(rep_img_label_uri_hans)
                            rep_img_label_uri_hans_name = get_image_name_by_URL(rep_img_label_uri_hans)
                            rep_vip_lable_info["img_label_uri_hans"] = f"./comment-resource/vip/{rep_img_label_uri_hans_name}"
                
                rep_pendant_info = rep_member_info.get("pendant", None)
                if rep_pendant_info:
                    rep_pendant_img_url = rep_pendant_info.get("image", '')
                    if rep_pendant_img_url:
                        to_download_resources_URL["pendant"].add(rep_pendant_img_url)
                        rep_pendant_img_name = get_image_name_by_URL(rep_pendant_img_url)
                        rep_pendant_info["image"] = f"./comment-resource/pendant/{rep_pendant_img_name}"

                rep_nft_info = rep_member_info.get("nft_interaction", None) #彩钻标识(拥有数字藏品)
                if rep_nft_info:
                    rep_region_info = rep_nft_info.get("region", None)
                    if rep_region_info:
                        rep_region_img_url = rep_region_info.get("icon", '')
                        if rep_region_img_url:
                            to_download_resources_URL["vip"].add(rep_region_img_url)
                            rep_region_img_name = get_image_name_by_URL(rep_region_img_url)
                            rep_region_info["icon"] = f"./comment-resource/vip/{rep_region_img_name}"
                
                rep_avatar_item = rep_member_info.get("avatar_item", None)
                if rep_avatar_item:
                    layers = rep_avatar_item.get("layers", [])
                    if layers:
                        remap_avatar_item_layers_to_local(layers,to_download_resources_URL)
                    
                    rep_fallback_layers = rep_avatar_item.get("fallback_layers", {})
                    if rep_fallback_layers:
                        layers_1 = rep_fallback_layers.get("layers", [])
                        if layers_1:
                            remap_avatar_item_layers_to_local(layers_1,to_download_resources_URL)

            rep_content_info = reply.get("content", None)
            if rep_content_info:
                emote = rep_content_info.get("emote", None)
                if emote:
                    for emote_ in emote.keys():
                        emote_url = emote[emote_].get("url", '')
                        if emote_url:
                            to_download_resources_URL["emoji"].add(emote_url)
                            emote[emote_]["url"] = f"./comment-resource/emoji/{get_image_name_by_URL(emote_url)}"

                rep_pic_info = rep_content_info.get("pictures", [])
                for pic_ in rep_pic_info:
                    pic_url = pic_.get("img_src", '')
                    if pic_url:
                        to_download_resources_URL["picture"].add(pic_url)
                        pic_["img_src"] = f"./comment-resource/picture/{get_image_name_by_URL(pic_url)}"

                    vip_icon_url = pic_.get("top_right_icon", '')
                    if vip_icon_url:
                        to_download_resources_URL["vip"].add(vip_icon_url)
                        vip_icon_img_name = get_image_name_by_URL(vip_icon_url)
                        pic_["top_right_icon"] = f"./comment-resource/vip/{vip_icon_img_name}"

                rep_jump_url_info = rep_content_info.get("jump_url", None)
                if rep_jump_url_info:
                    for jump_1, jump_info1 in rep_jump_url_info.items():
                        rep_jump_icon_url = jump_info1.get("prefix_icon", '')
                        if rep_jump_icon_url:
                            to_download_resources_URL["icons"].add(rep_jump_icon_url)
                            rep_jump_url_info[jump_1]["prefix_icon"] = f"./comment-resource/icons/{get_image_name_by_URL(rep_jump_icon_url)}"
                

async def download_resourses_URL_dict(to_download_resources_URL: dict , base_path: str , credential_:Credential, time_strip: float = 0.2) -> None:
    for key in to_download_resources_URL.keys():
        key_path = os.path.join(base_path, key)
        os.makedirs(key_path, exist_ok=True)
        for url in to_download_resources_URL[key]:
            #imgbytes = await Api(url = url, method="GET",  credential=credential_).request(byte= True)
            target_file = os.path.join(key_path, get_image_name_by_URL(url))
            if os.path.exists(target_file):
                print(f"{target_file} 已存在")
                continue 
            try:
                imgbytes = await Api(url = url, method="GET",  credential=credential_).request(byte= True)
            except aiohttp_http_exceptions.ContentLengthError as e:
                print(f"\033[93m下载 {target_file} 触发风控: {e}\033[0m")
                print(f"等待 60 秒后重试")
                await asyncio.sleep(60)
                imgbytes = await Api(url = url, method="GET",  credential=credential_).request(byte= True)
            except asyncio.exceptions.TimeoutError as e:
                print(f"\033[93m下载 {target_file} 请求过于频繁已被限流: {e}\033[0m")
                print(f"等待 60 秒后重试")
                await asyncio.sleep(60)
                imgbytes = await Api(url = url, method="GET",  credential=credential_).request(byte= True)
            except (TimeoutError, aiohttp.client_exceptions.ClientConnectorError) as e:
                print(f"下载 {target_file} 与服务器连接中断: {e}")
                print(f"等待 30 秒后重试")
                await asyncio.sleep(30)
                imgbytes = await Api(url = url, method="GET",  credential=credential_).request(byte= True)

            with open(target_file, "wb") as f:
                f.write(imgbytes)
            print(f"已下载 {target_file}")
            time.sleep(time_strip)

def is_num_str(str: str)->bool:
    """
    判断字符串是否为数字
    """
    try:
        int(str)
        return True
    except ValueError:
        return False

class _ScriptParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.current_script = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            self.in_script = True
            self.current_script = []

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.in_script:
            self.scripts.append("".join(self.current_script))
            self.current_script = []
            self.in_script = False

    def handle_data(self, data):
        if self.in_script:
            self.current_script.append(data)


def extract_json_from_scripts(html: str) -> list:
    """
    提取 HTML 中所有 <script> 标签里的合法 JSON 对象。

    只返回顶层为 dict 的 JSON：
        {...}

    不返回顶层 JSON 数组：
        [...]

    仅使用 Python 标准库。
    """
    parser = _ScriptParser()
    parser.feed(html)

    decoder = json.JSONDecoder()
    result = []

    for script in parser.scripts:
        i = 0

        while i < len(script):
            # 只寻找 JSON Object
            if script[i] != "{":
                i += 1
                continue

            try:
                obj, end = decoder.raw_decode(script, i)

                if isinstance(obj, dict):
                    result.append(obj)

                # 成功解析后直接跳过整个 JSON，
                # 防止其内部嵌套 dict 被重复提取
                i = end

            except json.JSONDecodeError:
                i += 1

    return result

def convert_ep_to_BV(ep_id: int, credential: Credential)->str:
    """
    将番剧ID转换为BV号
    """
    def try_get_bv_in_json(dic: dict)->str:
        """
        从JSON字典中提取BV号
        """
        try:
            bvid_ = dic["data"]["result"]["arc"]["bvid"]
        except KeyError:
            bvid_ = ""
        return bvid_

    
    url=f"https://www.bilibili.com/bangumi/play/ep{ep_id}"
    try:
        resp = httpx.get(
            url,
            cookies=credential.get_cookies(),
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
        )
    except httpx.ConnectError as e:
        print(f"获取番剧剧集ep{ep_id}详情失败，网络连接异常！:\n {e}")
        return ""
    except Exception as e:
        print(f"获取番剧剧集ep{ep_id}详情失败: {e}")
        return ""
    else:
        content = resp.text
        objects = extract_json_from_scripts(content)
        bvid = ""
        for obj in objects:
            if ("status" in obj) and ("data" in obj):
                bvid = try_get_bv_in_json(obj)
                if bvid:
                    break
       
    return bvid


def bili_video_url_parse(url: str)->dict:
    """
    解析B站视频URL，返回视频信息
    """
    out = {
        "bvid": "",
        "p": 1
    }
    
    if url.startswith("https://www.bilibili.com/video/"):
        value_str = url[31:]
        if not value_str.startswith("BV"):
            print(f"URL{url}不是BV号URL")
            return {}
        value_list = value_str.split("/?")
        if len(value_list) == 1:
            value_list = value_list[0].split("?")
        if len(value_list) == 1:
            out["bvid"] = value_list[0]
        elif len(value_list) == 2:
            out["bvid"] = value_list[0]
            params_list = value_list[1].split("&")
            for param in params_list:
                if param.startswith("p"):
                    key_value = param.split("=")
                    if len(key_value) == 2 and is_num_str(key_value[-1]):
                        out["p"] = int(key_value[1])
                    else:
                        print(f"URL{url}不合法的p参数格式")
                        break
        else:
            print(f"URL{url}不合法")
            return {}
    elif url.startswith("https://www.bilibili.com/bangumi/play/"):
        value_str = url[38:]
        if not value_str.startswith("ep"):
            print(f"URL{url}不是ep号番剧URL")
            return {}
        value_list = value_str.split("/?")
        ep_id_str = ''
        value_list_ = []
        for i in range(len(value_list)):
            value_list_ += value_list[i].split("?")
        value_list = value_list_
        if len(value_list) == 1 or len(value_list) == 2:
            ep_id_str = value_list[0][2:]
        else:
            print(f"URL{url}不合法")
            return {}
        ep_id = 0
        if not is_num_str(ep_id_str):
            print(f"URL{url}不合法的ep号格式")
            return {}
        else:
            ep_id = int(ep_id_str)
        bv = convert_ep_to_BV(ep_id, credential_)
        if not bv:
            print(f"URL{url}解析失败: 无法获取BV号")
            return {}
        out["bvid"] = bv
    else:
        print(f"URL{url}不是B站视频URL")
        return {}
    return out

async def main():
    srcURL = input("请输入视频评论所在视频的B站BV号URL,空输入退出：")
    if not srcURL:
        return
    video_info = bili_video_url_parse(srcURL)
    if not video_info:
        print("URL解析失败！")
        return 
    bvid = video_info["bvid"]
    av = bvid2aid(bvid)

    # 资源 URL 集合仍需保留到最后统一下载；评论正文则不再跨页保存在内存中。
    to_download_resources_URL = {
        "avatar": set(),
        "vip": set(),
        "emoji": set(),
        "card": set(),
        "pendant": set(),
        "picture": set(),
        "icons": set(),
        "baselabs": set(),
        "others": set(),
    }

    total_comments = 0
    total_top_comments = 0
    written_top_rpids = set()
    page = 1
    pag = ""

    # 只把当前 API 页及当前正在补全子评论的主评论保留在内存中。
    # 每页写入并提交后清空 replies，下一次循环即可回收旧页对象。
    with StreamingCommentDatabaseWriter(
        Path("comment.db"), srcURL, bvid, av
    ) as database_writer:
        while True:
            response = await comment.get_comments_lazy(
                av,
                comment.CommentResourceType.VIDEO,
                offset=pag,
                credential=credential_,
            )
            pagination_dict = response["cursor"]["pagination_reply"]
            is_last_page = pagination_dict.get("next_offset", 404) == 404
            if not is_last_page:
                pag = pagination_dict["next_offset"]

            replies = response["replies"]
            if replies is None:
                # 未登录时通常只能取得前若干条，后续请求可能返回 None。
                break

            top_replies = response.get("top_replies") or []
            if not isinstance(top_replies, list):
                raise ValueError("top_replies 不是列表或 null")
            for top_comment in top_replies:
                top_rpid = comment_rpid(top_comment)
                if top_rpid in written_top_rpids:
                    continue
                reply_count = top_comment.get("rcount", 0)
                reply_data = top_comment.get("replies") or []
                if reply_count > len(reply_data):
                    result = await get_sub_comment_by_dict(
                        top_comment, credential_
                    )
                    if not result:
                        print(
                            f"置顶评论 {top_rpid} 获取完整子评论失败，"
                            "将保存当前已取得的数据"
                        )
                remap_cmt_to_local(top_comment, to_download_resources_URL)
                database_writer.write_top_comment(top_comment)
                written_top_rpids.add(top_rpid)
                total_top_comments += 1

            for cmt_dict in replies:
                if comment_rpid(cmt_dict) in written_top_rpids:
                    continue
                reply_count = cmt_dict.get("rcount", 0)
                reply_data = cmt_dict.get("replies") or []
                if reply_count > len(reply_data):
                    result = await get_sub_comment_by_dict(cmt_dict, credential_)
                    if not result:
                        print(
                            f"评论 {cmt_dict.get('rpid', 0)} 获取完整子评论失败，"
                            "将保存当前已取得的数据"
                        )

                remap_cmt_to_local(cmt_dict, to_download_resources_URL)
                database_writer.write_main_comment(cmt_dict)
                total_comments += 1
                del reply_data

            # Python 的 for 循环变量会在循环结束后继续引用最后一条评论。
            if replies:
                del cmt_dict
            database_writer.commit_page()
            print(f"第 {page} 页已写入数据库，本页 {len(replies)} 条主评论")
            page += 1

            # 主动释放当前页对评论字典的引用；写库器不会保存这些对象。
            replies.clear()
            del replies
            del response

            if is_last_page:
                break

        database_writer.finalize()

    print(
        f"\n\n共有 {total_comments} 条评论（不含子评论），"
        f"另有 {total_top_comments} 条置顶评论，共 {page - 1} 页"
    )
    with open('resources-URL.json', 'w', encoding='utf-8') as f:
        for key in to_download_resources_URL.keys():
            to_download_resources_URL[key] = list(to_download_resources_URL[key])
        f.write(json.dumps(to_download_resources_URL, ensure_ascii=False, indent=4))

    base_path = "./comment-resource/"
    await download_resourses_URL_dict(to_download_resources_URL, base_path, credential_, 0.3)


if __name__ == "__main__":
    asyncio.run(main())
