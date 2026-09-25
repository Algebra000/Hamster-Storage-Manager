import asyncio
import hashlib
import json
import os
import re
import shutil
import sqlite3
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import sys

import aiohttp.client_exceptions
import aiohttp.http_exceptions as aiohttp_http_exceptions
import colorama
from bilibili_api import Credential, Danmaku, comment, video
from bilibili_api.utils.aid_bvid_transformer import bvid2aid
from bilibili_api.utils.network import Api, ResponseCodeException, get_aiohttp_session

colorama.init()


def print_error(message):
    """以红色输出完整错误信息，并在末尾恢复终端颜色。"""
    print(
        colorama.Fore.RED + str(message) + colorama.Style.RESET_ALL
    )


os.environ['NO_PROXY'] = 'bilibili.com,api.bilibili.com,*.bilibili.com,127.0.0.1,localhost'

async def download_dm_by_bv(bv: str, p: int = 1, credential: Credential = None, save_path: str = None):
    """
    根据BV号下载视频的弹幕文件

    Args:
        bv: B站视频BV号
        p: 分P号，从1开始
        credential: 登录凭证
        save_path: 保存文件路径，默认为 {bv}_p{p}.json

    Returns:
        str: 保存的文件路径，失败返回 None
    """


    v = video.Video(bvid=bv, credential=credential)
    try:
        dms = await v.get_danmakus(page_index=p - 1)
    except asyncio.TimeoutError as e:
        print_error(f"[Bilibili信息抓取模块] 获取弹幕失败: {e}")
        return None
    except ResponseCodeException as e:
        print(f"[Bilibili信息抓取模块] 稿件已失效: {e}")
        return None

    dmlist = []
    for dm in dms:
        if not dm.text:
            continue

        if dm.mode == 1:
            typestr = "scroll"
        elif dm.mode == 4:
            typestr = "bottom"
        elif dm.mode == 5:
            typestr = "top"
        elif dm.mode == 7:
            typestr = "special"
        else:
            typestr = "other"

        is_colorful = False
        if dm.colorful:
            is_colorful = True

        dmdic = {
                "time": dm.dm_time,
                "text": dm.text,
                "type": typestr,
                "color": f"#{str(dm.color).zfill(6)}",
                "dmid": dm.id_str,
                "is-colorful": is_colorful, # 是否为大会员专属彩色弹幕
                "like-count": dm.like_count,
                "oid": dm.oid,
                "font-size": dm.font_size,
                "send-time": dm.send_time,
                "weight": dm.weight,
                "uhash": dm.crc32_id,
                "src": "B站"
            }
        dmlist.append(dmdic)

    save_filename = save_path or f"{bv}_p{p}.json"
    with open(save_filename, 'w', encoding='utf-8') as f:
        f.write(json.dumps(dmlist, ensure_ascii=False, indent=4))

    return save_filename


def build_dm(basepath: str) -> bool:
    """
    整合不同历史版本的弹幕数据并构建弹幕目录

    Args:
        basepath: 要在其中构建弹幕目录的路径，包含已经下载好的所有弹幕文件的raw目录
    Returns:
        bool: 是否成功构建弹幕文件目录
    """
    raw_dir = os.path.join(basepath, 'raw')
    if not (os.path.exists(raw_dir) and os.path.isdir(raw_dir)):
        print_error(f"raw目录不存在: {raw_dir}")
        return False
    json_files = [f for f in os.listdir(raw_dir) if f.endswith('.json')]

    if not json_files:
        print_error("错误：raw 目录中没有 JSON 文件")
        return False

    categories = {}

    for filename in json_files:
        match = re.match(r'^(.+)-(\d+)\.json$', filename)
        if match:
            base_name = match.group(1)
            if re.search(r'-\d+$', base_name):
                continue
        else:
            base_name = filename[:-5]

        if re.search(r'-\d+$', base_name):
            continue

        if base_name not in categories:
            categories[base_name] = []
        categories[base_name].append(filename)

    for base_name, files in categories.items():
        all_danmaku = []
        seen_dmids = set()
        seen_oids = set()

        is_src_changed = False #这个视频的弹幕源是否发生过更换

        for filename in files:
            filepath = os.path.join(raw_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        if len(data)>0:
                            seen_oids.add(data[0].get('oid',0))
                            if len(seen_oids) > 1:
                                is_src_changed = True
                        all_danmaku.extend(data)
            except Exception as e:
                print_error(f"读取文件 {filename} 时出错: {e}")

        #也要判断是否存在现有的弹幕文件，存在则合并
        output_path = os.path.join(basepath, f"{base_name}.json")
        if os.path.exists(output_path) and os.path.isfile(output_path):
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                all_danmaku.extend(existing_data)
            except Exception as e:
                    print_error(f"读取文件 {output_path} 时出错: {e}")

        unique_danmaku = []
        if is_src_changed:
            print(colorama.Fore.YELLOW + "################################")
            print("           警告！！！")
            print(f"{base_name} 的弹幕源发生过更换, 将采用基于时间和内容的去重策略。")
            print("请着重注意一下本弹幕源的合并结果。")
            print("################################" + colorama.Style.RESET_ALL)
            for item in all_danmaku:
                vd_time = item.get('time',0)
                vd_text = item.get('text','')
                send_time = item.get('send-time','')
                total_key = (vd_time, vd_text, send_time)
                if total_key not in seen_dmids:
                    seen_dmids.add(total_key)
                    unique_danmaku.append(item)
        else:
            for item in all_danmaku:
                dmid = item.get('dmid')
                if dmid and dmid not in seen_dmids:
                    seen_dmids.add(dmid)
                    unique_danmaku.append(item)

        output_path = os.path.join(basepath, f"{base_name}.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(unique_danmaku, f, ensure_ascii=False, indent=4)

        print(f"已生成 {output_path}，共 {len(unique_danmaku)} 条弹幕")

def build_rmcf(basepath: str) -> bool:
    """
    构建重映射配置文件

    Args:
        basepath: 要在其中构建重映射配置文件的路径，包含已经下载好的所有弹幕文件的raw目录
    Returns:
        bool: 是否成功构建重映射配置文件
    """
    rmcf_list = []
    pre_rmcf_dir = os.path.join(basepath, 'rmcf.json')
    if os.path.exists(pre_rmcf_dir):
        with open(pre_rmcf_dir, 'r', encoding='utf-8') as f:
            try:
                rmcf_list = json.load(f)
            except json.JSONDecodeError:
                choice = input(f"文件{pre_rmcf_dir}内容不是有效的JSON格式，是否新建列表并覆盖文件内容?无输入默认覆盖原文件，有输入则放弃构建rmcf.json")
                if choice:
                    return False
    rmcf_filename_list = {rmcf_list[ind].get("dmsrc-file", ""): ind for ind in range(len(rmcf_list))}
    srcURL_path = os.path.join(basepath, 'dm-srcURL.json')
    if not os.path.exists(srcURL_path):
        print_error(f"错误：dm-srcURL.json文件不存在: {srcURL_path}")
        return False
    with open(srcURL_path, 'r', encoding='utf-8') as f:
        src_list = json.load(f)
    for item in src_list:
        rmcf_info = item.get("rmcf", {})
        if rmcf_info:
            dmsrc_file = rmcf_info.get("dmsrc-file", "")
            ind_ = rmcf_filename_list.get(dmsrc_file, -1)
            if ind_ != -1:
                rmcf_list[ind_] = rmcf_info
                print(f"已覆盖 {dmsrc_file} 的重映射配置")
            else:
                rmcf_list.append(rmcf_info)
                rmcf_filename_list[dmsrc_file] = len(rmcf_list) - 1

    with open(pre_rmcf_dir, 'w', encoding='utf-8') as f:
        json.dump(rmcf_list, f, ensure_ascii=False, indent=4)
    print(f"已生成 {pre_rmcf_dir}，共 {len(rmcf_list)} 条重映射配置")






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
        # top 是独立的置顶评论表；member/content 中仍把它视为顶层 main，
        # 这样可兼容已经生成的 v1.1 实体表约束。
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
        # 三张评论表共享 rpid；临时唯一索引也覆盖没有 member/content 的评论。
        # 仅用于本次流式写入，不改变最终数据库的 v1.1 格式。
        self.connection.execute(
            'CREATE TEMP TABLE _written_comments('
            'rpid INTEGER PRIMARY KEY, table_name TEXT NOT NULL)'
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
        rpid = comment_rpid(comment_dict)
        # 列扩展放在保存点外，回滚单条写入时保持列缓存与实际表结构一致。
        self._ensure_comment_columns(comment_dict)
        for entity in ("member", "content"):
            data = comment_dict.get(entity)
            if isinstance(data, dict):
                self._ensure_entity_columns(entity, data)
        # 保存点必须嵌套在页事务内，否则 RELEASE 会逐条提交。
        if not self.connection.in_transaction:
            self.connection.execute("BEGIN")
        self.connection.execute("SAVEPOINT insert_comment")
        registering = True
        try:
            # 正常路径直接 INSERT，由 SQLite 唯一约束检测重复，不预先 SELECT。
            self.connection.execute(
                'INSERT INTO temp._written_comments VALUES(?,?)', (rpid, table_name)
            )
            registering = False
            self._insert_comment_rows(table_name, comment_dict, rpid)
        except Exception as error:
            self.connection.execute("ROLLBACK TO insert_comment")
            self.connection.execute("RELEASE insert_comment")
            # 只恢复 ID 登记表的主键冲突，实体/评论的其他约束错误照常抛出。
            # Python 3.8 没有 sqlite_errorcode；精确匹配表和列，兼容旧版 sqlite3。
            if not (registering and isinstance(error, sqlite3.IntegrityError)
                    and str(error) == "UNIQUE constraint failed: _written_comments.rpid"):
                raise
            existing = self.connection.execute(
                'SELECT table_name FROM temp._written_comments WHERE rpid=?', (rpid,)
            ).fetchone()
            if existing is None:
                raise
            if table_name == "top" and existing[0] == "main":
                # 后续页才出现的置顶项只移动分类，保留同一组实体与回复。
                self.connection.execute("SAVEPOINT promote_comment")
                try:
                    self.connection.execute(
                        'INSERT INTO top SELECT * FROM main WHERE rpid=?', (rpid,)
                    )
                    self.connection.execute('DELETE FROM main WHERE rpid=?', (rpid,))
                    self.connection.execute(
                        "UPDATE temp._written_comments SET table_name='top' WHERE rpid=?",
                        (rpid,),
                    )
                except Exception:
                    self.connection.execute("ROLLBACK TO promote_comment")
                    raise
                finally:
                    self.connection.execute("RELEASE promote_comment")
                self.main_count -= 1
                self.top_count += 1
            return False
        else:
            self.connection.execute("RELEASE insert_comment")
            return True

    def _insert_comment_rows(self, table_name: str, comment_dict: dict, rpid: int):
        """在调用方的保存点内写入实体及评论。"""
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
        inserted = self._insert_comment("main", comment_dict)
        reply_count = 0
        for reply in iter_nested_replies(comment_dict):
            reply_count += int(self._insert_comment("reply", reply))
        encoded = compact_json(comment_dict, sort_keys=True).encode("utf-8")
        self.source_hasher.update(len(encoded).to_bytes(8, "big"))
        self.source_hasher.update(encoded)
        self.main_count += int(inserted)
        self.reply_count += reply_count

    def write_top_comment(self, comment_dict: dict):
        """写入一条置顶评论及其回复；置顶评论不重复写入 main。"""
        inserted = self._insert_comment("top", comment_dict)
        reply_count = 0
        for reply in iter_nested_replies(comment_dict):
            reply_count += int(self._insert_comment("reply", reply))
        encoded = compact_json(comment_dict, sort_keys=True).encode("utf-8")
        self.source_hasher.update(len(encoded).to_bytes(8, "big"))
        self.source_hasher.update(encoded)
        self.top_count += int(inserted)
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

def get_image_name_by_URL(url: str) -> str:
    if not url:
        return ""
    # 查询参数不是文件名的一部分，Windows 路径也不允许包含问号。
    return os.path.basename(urlsplit(url).path)

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
            print_error(f"获取子评论失败: {e}")
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


COMMENT_RESOURCE_TYPES = (
    "avatar", "vip", "emoji", "card", "pendant",
    "picture", "icons", "baselabs", "others",
)
COMMENT_DELTA_SCHEMA_VERSION = "v1"
SCRIPT_DIR = Path(__file__).resolve().parent
BILIBILI_RESOURCE_ZIP = SCRIPT_DIR / "bilibili-resource.zip"
COMMENT_DATABASE_NAME = re.compile(r"^cm([1-9][0-9]*)\.db$")
COMMENT_RAW_DATABASE_FILE = re.compile(
    r"^(cm[1-9][0-9]*\.db)(?:\.tmp)?(?:-(?:journal|wal|shm))?$"
)
# 由 main() 启动时询问决定；默认保守地保留损坏文件并抛出详细错误。
OVERWRITE_DAMAGED_JSON_FILES = False


def load_json_file(path: Path, expected_type, default):
    """读取工具生成的 JSON，并把损坏位置和原因写入异常信息。"""
    path = Path(path)
    if not path.exists():
        return default

    def handle_damaged_file(reason, original_error=None):
        message = f"JSON 文件 {path} {reason}"
        if not OVERWRITE_DAMAGED_JSON_FILES:
            if original_error is None:
                raise ValueError(message)
            raise ValueError(message) from original_error
        print_error(
            f"检测到损坏的 JSON 文件，已按本次运行设置用默认"
            f"{expected_type.__name__}内容覆盖：{path}；原因：{reason}"
        )
        write_json_file(path, default)
        return default

    try:
        raw_data = path.read_bytes()
    except OSError as error:
        raise OSError(
            f"无法读取 JSON 文件 {path}：{type(error).__name__}: {error}"
        ) from error
    if not raw_data:
        return handle_damaged_file(
            f"为空（0 字节）；顶层应为 {expected_type.__name__}"
        )
    try:
        text = raw_data.decode("utf-8")
    except UnicodeDecodeError as error:
        return handle_damaged_file(
            f"不是有效的 UTF-8 文本：第 {error.start} 个字节附近"
            f"无法解码（{error.reason}）",
            error,
        )
    if not text.strip():
        return handle_damaged_file(
            f"仅包含空白字符（{len(raw_data)} 字节）；"
            f"顶层应为 {expected_type.__name__}"
        )
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        context_start = max(0, error.pos - 50)
        context_end = min(len(text), error.pos + 50)
        context = text[context_start:context_end]
        return handle_damaged_file(
            f"格式错误：第 {error.lineno} 行、"
            f"第 {error.colno} 列（字符位置 {error.pos}）：{error.msg}；"
            f"错误位置附近内容={context!r}",
            error,
        )
    if not isinstance(data, expected_type):
        return handle_damaged_file(
            f"的顶层结构类型错误："
            f"实际为 {type(data).__name__}，应为 {expected_type.__name__}"
        )
    return data


def write_json_file(path: Path, data) -> None:
    """先写同目录临时文件，再原子替换正式 JSON。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(path.name + ".tmp")
    try:
        with temporary_path.open("w", encoding="utf-8", newline="\n") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
            file.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def atomic_copy(source: Path, destination: Path) -> None:
    """复制数据库并原子覆盖目标，避免中途失败留下半个文件。"""
    source, destination = Path(source), Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_name(destination.name + ".copy.tmp")
    try:
        shutil.copy2(source, temporary_path)
        os.replace(temporary_path, destination)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def open_sqlite_database_readonly(database_path: Path):
    r"""以只查询方式打开本地或 UNC SQLite 数据库，不转换成 file URI。"""
    database_path = Path(database_path)
    if not database_path.is_file():
        raise FileNotFoundError(f"评论数据库不存在：{database_path}")
    # UNC 转成 file://server/share/... 后，部分 Windows SQLite 会报
    # invalid uri authority。直接传原始路径，再用 query_only 禁止写入。
    connection = sqlite3.connect(str(database_path))
    connection.execute("PRAGMA query_only=ON")
    return connection


def cleanup_comment_raw_files(raw_dir: Path, file_name: str = None) -> None:
    """清除评论下载过程留下的正式临时库及 SQLite 边车文件。"""
    raw_dir = Path(raw_dir)
    if not raw_dir.is_dir():
        return
    for path in raw_dir.iterdir():
        if not path.is_file():
            continue
        match = COMMENT_RAW_DATABASE_FILE.fullmatch(path.name)
        if not match or (file_name is not None and match.group(1) != file_name):
            continue
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def comment_source_run_key(comment_dir: Path, bvid: str) -> tuple:
    """同一次运行中，以“共享评论目录 + BV”唯一标识一次评论抓取。"""
    normalized_dir = os.path.normcase(str(Path(comment_dir).resolve()))
    return normalized_dir, bvid


def build_cm_src_url(metadata_dir: Path) -> list:
    """把 dm-srcURL.json 中的 BV 来源合并到 cm-srcURL.json。"""
    metadata_dir = Path(metadata_dir)
    dm_path = metadata_dir / "dm-srcURL.json"
    cm_path = metadata_dir / "cm-srcURL.json"
    dm_sources = load_json_file(dm_path, list, [])
    cm_sources = load_json_file(cm_path, list, [])
    merged = []
    seen_bvids = set()
    for item in dm_sources:
        if not isinstance(item, dict):
            raise ValueError(f"{dm_path} 中含有非字典来源")
        bv = str(item.get("BV", "")).strip()
        if not bv or bv in seen_bvids:
            continue
        seen_bvids.add(bv)
        # 评论来源名称独立于弹幕来源名称，不能沿用 dm1、dm2 等名称。
        merged.append({"src": "B站", "BV": bv})
    for index, item in enumerate(merged, start=1):
        item["name"] = f"来源{index}"
    # 保留 cm-srcURL.json 中手工补充、但当前 dm-srcURL.json 没有的 BV。
    for item in cm_sources:
        if not isinstance(item, dict):
            raise ValueError(f"{cm_path} 中含有非字典来源")
        bv = str(item.get("BV", "")).strip()
        if not bv or bv in seen_bvids:
            continue
        seen_bvids.add(bv)
        merged.append(item)# 原封不动的保留 cm-srcURL.json 中的已有项
    write_json_file(cm_path, merged)
    print(f"已生成或更新评论来源文件：{cm_path}，共 {len(merged)} 个 BV 来源")
    return merged


def empty_resource_urls() -> dict:
    return {name: set() for name in COMMENT_RESOURCE_TYPES}


def merge_resource_urls(path: Path, discovered: dict) -> dict:
    """合并历史与本次资源 URL，并持久化为稳定排序的列表。"""
    existing = load_json_file(path, dict, {})
    merged = empty_resource_urls()
    for category in COMMENT_RESOURCE_TYPES:
        old_values = existing.get(category, [])
        if old_values is None:
            old_values = []
        if not isinstance(old_values, list):
            raise ValueError(f"{path} 的 {category} 必须是列表")
        merged[category].update(str(url) for url in old_values if url)
        merged[category].update(
            str(url) for url in discovered.get(category, set()) if url
        )
    serializable = {key: sorted(values) for key, values in merged.items()}
    write_json_file(path, serializable)
    return serializable


async def download_comment_resources(resource_urls: dict, base_path: Path,
                                     credential: Credential) -> None:
    """下载缺失资源；URL 已登记但本地缺失的文件也会补齐。"""
    base_path = Path(base_path)
    for category in COMMENT_RESOURCE_TYPES:
        category_path = base_path / category
        category_path.mkdir(parents=True, exist_ok=True)
        for url in resource_urls.get(category, []):
            file_name = get_image_name_by_URL(url)
            if not file_name:
                print(f"跳过无法取得文件名的资源 URL：{url}")
                continue
            target_file = category_path / file_name
            if target_file.is_file():
                continue
            image_bytes = None
            for attempt in range(3):
                try:
                    image_bytes = await Api(
                        url=url, method="GET", credential=credential
                    ).request(byte=True)
                    break
                except (
                    aiohttp_http_exceptions.ContentLengthError,
                    asyncio.TimeoutError,
                    TimeoutError,
                    aiohttp.client_exceptions.ClientConnectorError,
                ) as error:
                    if attempt == 2:
                        print_error(
                            f"资源下载失败，稍后可再次运行补齐：{url}：{error}"
                        )
                        break
                    delay = 30 if isinstance(
                        error,
                        (TimeoutError, aiohttp.client_exceptions.ClientConnectorError),
                    ) else 60
                    print_error(f"下载资源失败，{delay} 秒后重试：{url}：{error}")
                    await asyncio.sleep(delay)
                except Exception as error:
                    print_error(f"资源下载失败，稍后可再次运行补齐：{url}：{error}")
                    break
            if image_bytes is None:
                continue
            temporary_path = target_file.with_name(target_file.name + ".tmp")
            try:
                with temporary_path.open("wb") as file:
                    file.write(image_bytes)
                os.replace(temporary_path, target_file)
                print(f"已下载评论资源：{target_file}")
            finally:
                if temporary_path.exists():
                    temporary_path.unlink()
            await asyncio.sleep(0.3)


def ensure_bilibili_resources(comment_dir: Path) -> None:
    """按压缩包文件清单检查并补齐 bilibili-resource。"""
    comment_dir = Path(comment_dir)
    if not BILIBILI_RESOURCE_ZIP.is_file():
        raise FileNotFoundError(f"缺少基础评论资源包：{BILIBILI_RESOURCE_ZIP}")
    root = comment_dir.resolve()
    with zipfile.ZipFile(BILIBILI_RESOURCE_ZIP, "r") as archive:
        missing = []
        for info in archive.infolist():
            target = (root / Path(info.filename)).resolve()
            if target != root and root not in target.parents:
                raise ValueError(f"资源压缩包包含越界路径：{info.filename}")
            if not info.is_dir() and not target.is_file():
                missing.append(info)
        for info in missing:
            archive.extract(info, root)
    if missing:
        print(f"已从 {BILIBILI_RESOURCE_ZIP.name} 补齐 {len(missing)} 个基础评论资源")


def validate_comment_filename(file_name: str) -> int:
    match = COMMENT_DATABASE_NAME.fullmatch(str(file_name))
    if not match:
        raise ValueError(f"cm-list.json 中存在不安全或不合法的文件名：{file_name!r}")
    return int(match.group(1))


def allocate_comment_filename(cm_list: dict, comment_dir: Path) -> str:
    used = {
        str(info.get("file-name"))
        for info in cm_list.values()
        if isinstance(info, dict) and info.get("file-name")
    }
    number = 1
    while True:
        file_name = f"cm{number}.db"
        if (
            file_name not in used
            and not (comment_dir / file_name).exists()
            and not (comment_dir / "update" / file_name).exists()
            and not (comment_dir / "update" / f"cm{number}.deletelist").exists()
            and not (comment_dir / "raw" / file_name).exists()
        ):
            return file_name
        number += 1


def delta_paths(update_dir: Path, file_name: str) -> list:
    number = validate_comment_filename(file_name)
    pattern = re.compile(rf"^cm{number}-([1-9][0-9]*)\.db$")
    result = []
    for path in Path(update_dir).iterdir():
        match = pattern.fullmatch(path.name)
        if match and path.is_file():
            result.append((int(match.group(1)), path))
    return [path for _, path in sorted(result)]


def next_delta_path(update_dir: Path, file_name: str) -> Path:
    number = validate_comment_filename(file_name)
    suffix = 1
    while True:
        path = Path(update_dir) / f"cm{number}-{suffix}.db"
        if not path.exists():
            return path
        suffix += 1


def comment_deletelist_path(update_dir: Path, file_name: str) -> Path:
    """返回某个评论来源的历史删除 rpid 列表路径。"""
    number = validate_comment_filename(file_name)
    return Path(update_dir) / f"cm{number}.deletelist"


def deleted_rpids_from_delta(delta_path: Path) -> set:
    """读取一个增量数据库中第二次快照已经缺失的全部 rpid。"""
    delta_path = Path(delta_path)
    connection = open_sqlite_database_readonly(delta_path)
    try:
        table_exists = connection.execute(
            "SELECT 1 FROM sqlite_master "
            "WHERE type='table' AND name='_deleted_records'"
        ).fetchone()
        if not table_exists:
            raise ValueError(f"增量数据库缺少 _deleted_records 表：{delta_path}")
        return {
            int(row[0])
            for row in connection.execute(
                "SELECT DISTINCT rpid FROM _deleted_records"
            )
        }
    finally:
        connection.close()


def write_comment_deletelist(update_dir: Path, file_name: str,
                             deleted_rpids) -> Path:
    """将删除记录按数值排序、去重后原子写为 JSON 列表。"""
    normalized = set()
    for rpid in deleted_rpids:
        if isinstance(rpid, bool):
            raise ValueError("deletelist 中的 rpid 不能是布尔值")
        try:
            normalized.add(int(rpid))
        except (TypeError, ValueError) as error:
            raise ValueError(f"deletelist 中存在无效 rpid：{rpid!r}") from error
    path = comment_deletelist_path(update_dir, file_name)
    write_json_file(path, sorted(normalized))
    return path


def rebuild_comment_deletelist(update_dir: Path, file_name: str,
                               deltas: list = None) -> Path:
    """以全部历史增量为准，重新构建某来源的 deletelist。"""
    if deltas is None:
        deltas = delta_paths(update_dir, file_name)
    deleted_rpids = set()
    for delta in deltas:
        deleted_rpids.update(deleted_rpids_from_delta(delta))
    return write_comment_deletelist(update_dir, file_name, deleted_rpids)


def merge_delta_into_deletelist(update_dir: Path, file_name: str,
                                delta_path: Path) -> Path:
    """把一个新增量中的删除记录并入现有 deletelist。"""
    path = comment_deletelist_path(update_dir, file_name)
    existing = load_json_file(path, list, [])
    deleted_rpids = list(existing)
    deleted_rpids.extend(deleted_rpids_from_delta(delta_path))
    return write_comment_deletelist(update_dir, file_name, deleted_rpids)


def comment_database_counts(database_path: Path) -> tuple:
    """返回最终合并库评论数（main + top）和回复数（reply）。"""
    database_path = Path(database_path)
    connection = open_sqlite_database_readonly(database_path)
    try:
        validate_comment_database(connection, "main")
        comment_count = connection.execute(
            'SELECT COUNT(*) FROM "main"'
        ).fetchone()[0]
        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='top'"
        ).fetchone():
            comment_count += connection.execute(
                'SELECT COUNT(*) FROM "top"'
            ).fetchone()[0]
        reply_count = connection.execute(
            'SELECT COUNT(*) FROM "reply"'
        ).fetchone()[0]
        return int(comment_count), int(reply_count)
    finally:
        connection.close()


def database_metadata(connection: sqlite3.Connection, schema: str) -> dict:
    if schema not in {"main", "old_db", "new_db", "delta_db"}:
        raise ValueError(f"非法数据库 schema：{schema}")
    rows = connection.execute(
        f'SELECT metadata_key,metadata_value FROM {schema}."_metadata"'
    ).fetchall()
    return {str(key): str(value) for key, value in rows}


def validate_comment_database(connection: sqlite3.Connection, schema: str) -> dict:
    metadata = database_metadata(connection, schema)
    if metadata.get("schema_version") != COMMENT_DB_SCHEMA_VERSION:
        raise ValueError(f"{schema} 不是 {COMMENT_DB_SCHEMA_VERSION} 评论数据库")
    expected = ",".join(COMMENT_VOLATILE_FIELDS)
    if metadata.get("volatile_fields") != expected:
        raise ValueError(f"{schema} 的 _volatile_hash 字段口径与当前九字段标准不一致")
    return metadata


def table_columns(connection: sqlite3.Connection, schema: str, table: str) -> list:
    return [
        (str(row[1]), str(row[2] or ""))
        for row in connection.execute(
            f'PRAGMA {schema}.table_info({quote_db_identifier(table)})'
        ).fetchall()
    ]


def schema_has_table(connection: sqlite3.Connection, schema: str,
                     table: str) -> bool:
    if schema not in {"main", "old_db", "new_db", "delta_db"}:
        raise ValueError(f"非法数据库 schema：{schema}")
    return connection.execute(
        f"SELECT 1 FROM {schema}.sqlite_master "
        "WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def _ensure_comment_top_table(connection: sqlite3.Connection) -> None:
    """在当前连接补齐旧版 top 表；事务和最终校验由调用方负责。"""
    if not schema_has_table(connection, "main", "top"):
        row = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='main'"
        ).fetchone()
        if not row or not row[0]:
            raise ValueError("旧评论数据库缺少 main 表")
        create_sql, replacements = re.subn(
            r'^(CREATE\s+TABLE\s+)(?:"main"|main)',
            r'\1"top"', row[0], count=1, flags=re.IGNORECASE,
        )
        if replacements != 1:
            raise ValueError("无法从 main 表升级 top 表")
        connection.execute(create_sql)
        top_columns = {
            name for name, _ in table_columns(connection, "main", "top")
        }
        for key in ("mid", "ctime", "like", "parent", "root"):
            if key in top_columns:
                connection.execute(
                    f'CREATE INDEX {quote_db_identifier(f"idx_top_{key}")} '
                    f'ON "top"({quote_db_identifier(key)})'
                )
    connection.execute(
        "INSERT INTO _metadata(metadata_key,metadata_value) VALUES('top_count','0') "
        "ON CONFLICT(metadata_key) DO NOTHING"
    )


def ensure_comment_database_top_table(database_path: Path) -> None:
    """把旧 v1.1 快照就地补齐为空的 top 表和 top_count 元数据。"""
    connection = sqlite3.connect(Path(database_path))
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        validate_comment_database(connection, "main")
        _ensure_comment_top_table(connection)
        connection.commit()
        foreign_key_errors = connection.execute(
            "PRAGMA main.foreign_key_check"
        ).fetchall()
        if foreign_key_errors:
            raise sqlite3.IntegrityError(
                f"升级 top 表后外键检查失败：{foreign_key_errors[:3]}"
            )
        integrity_result = connection.execute(
            "PRAGMA main.integrity_check"
        ).fetchall()
        if integrity_result != [("ok",)]:
            raise sqlite3.DatabaseError(
                f"升级 top 表后完整性检查失败：{integrity_result[:3]}"
            )
    finally:
        connection.close()


def clone_snapshot_table(connection: sqlite3.Connection, table: str) -> None:
    row = connection.execute(
        "SELECT sql FROM new_db.sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    if not row or not row[0]:
        raise ValueError(f"新评论数据库缺少表：{table}")
    connection.execute(row[0])


def sql_id_set(connection: sqlite3.Connection, statement: str) -> set:
    return {int(row[0]) for row in connection.execute(statement)}


def copy_selected_rows(connection: sqlite3.Connection, source_schema: str,
                       table: str, key: str, ids: set) -> None:
    if not ids:
        return
    connection.execute("DROP TABLE IF EXISTS temp._selected_rows")
    connection.execute("CREATE TEMP TABLE _selected_rows(row_id INTEGER PRIMARY KEY)")
    connection.executemany(
        "INSERT INTO temp._selected_rows VALUES(?)",
        ((row_id,) for row_id in sorted(ids)),
    )
    columns = [name for name, _ in table_columns(connection, source_schema, table)]
    quoted_columns = ",".join(quote_db_identifier(name) for name in columns)
    connection.execute(
        f'INSERT INTO {quote_db_identifier(table)}({quoted_columns}) '
        f'SELECT {quoted_columns} FROM {source_schema}.{quote_db_identifier(table)} '
        f'WHERE {quote_db_identifier(key)} IN '
        '(SELECT row_id FROM temp._selected_rows)'
    )
    connection.execute("DROP TABLE temp._selected_rows")


def create_comment_delta(old_path: Path, new_path: Path, output_path: Path,
                         bvid: str, aid: int) -> dict:
    """保存新增/变化记录的完整新版本，并另存第二次缺失记录清单。"""
    old_path, new_path, output_path = map(Path, (old_path, new_path, output_path))
    ensure_comment_database_top_table(old_path)
    ensure_comment_database_top_table(new_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(output_path.name + ".tmp")
    if temporary_path.exists():
        temporary_path.unlink()
    connection = sqlite3.connect(temporary_path)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("ATTACH DATABASE ? AS old_db", (str(old_path.resolve()),))
        connection.execute("ATTACH DATABASE ? AS new_db", (str(new_path.resolve()),))
        validate_comment_database(connection, "old_db")
        validate_comment_database(connection, "new_db")
        connection.execute(
            "CREATE TABLE _delta_metadata("
            "metadata_key TEXT PRIMARY KEY,metadata_value TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE _changes("
            "comment_kind TEXT NOT NULL "
            "CHECK(comment_kind IN ('main','top','reply')) ,"
            "rpid INTEGER NOT NULL,operation TEXT NOT NULL "
            "CHECK(operation IN ('insert','update')) ,"
            "comment_changed INTEGER NOT NULL,member_changed INTEGER NOT NULL ,"
            "content_changed INTEGER NOT NULL,PRIMARY KEY(comment_kind,rpid))"
        )
        connection.execute(
            "CREATE TABLE _deleted_records("
            "comment_kind TEXT NOT NULL "
            "CHECK(comment_kind IN ('main','top','reply')) ,"
            "rpid INTEGER NOT NULL,PRIMARY KEY(comment_kind,rpid))"
        )
        connection.execute(
            "CREATE TABLE _target_metadata("
            "metadata_key TEXT PRIMARY KEY,metadata_value TEXT NOT NULL)"
        )
        for table in ("member", "content", "main", "top", "reply"):
            clone_snapshot_table(connection, table)

        all_upserts = set()
        upserts_by_table = {}
        total_deleted = total_inserted = total_updated = 0
        for table in ("main", "top", "reply"):
            quoted_table = quote_db_identifier(table)
            added = sql_id_set(connection, f'''
                SELECT n.rpid FROM new_db.{quoted_table} AS n
                LEFT JOIN old_db.{quoted_table} AS o ON o.rpid=n.rpid
                WHERE o.rpid IS NULL
            ''')
            removed = sql_id_set(connection, f'''
                SELECT o.rpid FROM old_db.{quoted_table} AS o
                LEFT JOIN new_db.{quoted_table} AS n ON n.rpid=o.rpid
                WHERE n.rpid IS NULL
            ''')
            comment_changed = sql_id_set(connection, f'''
                SELECT n.rpid FROM new_db.{quoted_table} AS n
                JOIN old_db.{quoted_table} AS o ON o.rpid=n.rpid
                WHERE n._volatile_hash IS NOT o._volatile_hash
            ''')
            member_changed = sql_id_set(connection, f'''
                SELECT n.rpid FROM new_db.{quoted_table} AS n
                JOIN old_db.{quoted_table} AS o ON o.rpid=n.rpid
                LEFT JOIN new_db.member AS ne ON ne.parent=n.rpid
                LEFT JOIN old_db.member AS oe ON oe.parent=n.rpid
                WHERE n.member IS NOT o.member OR ne._data_hash IS NOT oe._data_hash
            ''')
            content_changed = sql_id_set(connection, f'''
                SELECT n.rpid FROM new_db.{quoted_table} AS n
                JOIN old_db.{quoted_table} AS o ON o.rpid=n.rpid
                LEFT JOIN new_db.content AS ne ON ne.parent=n.rpid
                LEFT JOIN old_db.content AS oe ON oe.parent=n.rpid
                WHERE n.content IS NOT o.content OR ne._data_hash IS NOT oe._data_hash
            ''')
            upserts = added | comment_changed | member_changed | content_changed
            upserts_by_table[table] = upserts
            all_upserts.update(upserts)
            for rpid in sorted(upserts):
                connection.execute(
                    "INSERT INTO _changes VALUES(?,?,?,?,?,?)",
                    (
                        table, rpid, "insert" if rpid in added else "update",
                        int(rpid in added or rpid in comment_changed),
                        int(rpid in added or rpid in member_changed),
                        int(rpid in added or rpid in content_changed),
                    ),
                )
            connection.executemany(
                "INSERT INTO _deleted_records VALUES(?,?)",
                ((table, rpid) for rpid in sorted(removed)),
            )
            total_deleted += len(removed)
            total_inserted += len(added)
            total_updated += len(upserts - added)


        copy_selected_rows(connection, "new_db", "member", "parent", all_upserts)
        copy_selected_rows(connection, "new_db", "content", "parent", all_upserts)
        for table in ("main", "top", "reply"):
            copy_selected_rows(
                connection, "new_db", table, "rpid", upserts_by_table[table]
            )
        connection.execute(
            "INSERT INTO _target_metadata "
            "SELECT metadata_key,metadata_value FROM new_db._metadata"
        )
        metadata = {
            "delta_schema_version": COMMENT_DELTA_SCHEMA_VERSION,
            "comment_schema_version": COMMENT_DB_SCHEMA_VERSION,
            "volatile_fields": ",".join(COMMENT_VOLATILE_FIELDS),
            "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "bvid": bvid,
            "aid": str(aid),
            "insert_count": str(total_inserted),
            "update_count": str(total_updated),
            "delete_count": str(total_deleted),
        }
        connection.executemany(
            "INSERT INTO _delta_metadata VALUES(?,?)", metadata.items()
        )
        connection.commit()
        foreign_key_errors = connection.execute(
            "PRAGMA main.foreign_key_check"
        ).fetchall()
        if foreign_key_errors:
            raise sqlite3.IntegrityError(
                f"增量数据库外键检查失败：{foreign_key_errors[:3]}"
            )
        integrity_result = connection.execute(
            "PRAGMA main.integrity_check"
        ).fetchall()
        if integrity_result != [("ok",)]:
            raise sqlite3.DatabaseError(
                f"增量数据库完整性检查失败：{integrity_result[:3]}"
            )
    except Exception:
        connection.close()
        if temporary_path.exists():
            temporary_path.unlink()
        raise
    else:
        connection.close()
        os.replace(temporary_path, output_path)
    print(
        f"已生成增量库：{output_path}，新增 {total_inserted}，"
        f"变化 {total_updated}，缺失 {total_deleted}"
    )
    return {
        "insert": total_inserted,
        "update": total_updated,
        "delete": total_deleted,
    }


def delta_metadata(connection: sqlite3.Connection) -> dict:
    rows = connection.execute(
        "SELECT metadata_key,metadata_value FROM delta_db._delta_metadata"
    ).fetchall()
    return {str(key): str(value) for key, value in rows}


def ensure_delta_columns(connection: sqlite3.Connection, table: str) -> None:
    target = {name for name, _ in table_columns(connection, "main", table)}
    for name, column_type in table_columns(connection, "delta_db", table):
        if name in target:
            continue
        type_sql = f" {column_type}" if column_type else ""
        connection.execute(
            f'ALTER TABLE {quote_db_identifier(table)} '
            f'ADD COLUMN {quote_db_identifier(name)}{type_sql}'
        )


def insert_attached_rows(connection: sqlite3.Connection, table: str) -> None:
    columns = [name for name, _ in table_columns(connection, "delta_db", table)]
    quoted_columns = ",".join(quote_db_identifier(name) for name in columns)
    connection.execute(
        f'INSERT INTO {quote_db_identifier(table)}({quoted_columns}) '
        f'SELECT {quoted_columns} FROM delta_db.{quote_db_identifier(table)}'
    )


def _apply_attached_comment_delta(connection: sqlite3.Connection,
                                  delta_path: Path) -> None:
    """应用已附加的 delta_db；不提交、不扫描全库。"""
    metadata = delta_metadata(connection)
    if metadata.get("delta_schema_version") != COMMENT_DELTA_SCHEMA_VERSION:
        raise ValueError(f"不支持的评论增量数据库：{delta_path}")
    if metadata.get("volatile_fields") != ",".join(COMMENT_VOLATILE_FIELDS):
        raise ValueError(f"增量库的九字段哈希口径不一致：{delta_path}")
    delta_comment_tables = ["main", "reply"]
    if schema_has_table(connection, "delta_db", "top"):
        delta_comment_tables.insert(1, "top")
    for table in ("member", "content", *delta_comment_tables):
        ensure_delta_columns(connection, table)
    connection.execute("CREATE TEMP TABLE _apply_ids(rpid INTEGER PRIMARY KEY)")
    for table in delta_comment_tables:
        connection.execute(
            f"INSERT OR IGNORE INTO temp._apply_ids "
            f"SELECT rpid FROM delta_db.{quote_db_identifier(table)}"
        )
    # 同一 rpid 的整组记录用最新版本替换；删除清单不参与历史合并。
    connection.execute(
        "DELETE FROM main WHERE rpid IN (SELECT rpid FROM temp._apply_ids)"
    )
    connection.execute(
        "DELETE FROM reply WHERE rpid IN (SELECT rpid FROM temp._apply_ids)"
    )
    connection.execute(
        "DELETE FROM top WHERE rpid IN (SELECT rpid FROM temp._apply_ids)"
    )
    connection.execute(
        "DELETE FROM member WHERE parent IN (SELECT rpid FROM temp._apply_ids)"
    )
    connection.execute(
        "DELETE FROM content WHERE parent IN (SELECT rpid FROM temp._apply_ids)"
    )
    insert_attached_rows(connection, "member")
    insert_attached_rows(connection, "content")
    for table in delta_comment_tables:
        insert_attached_rows(connection, table)
    connection.execute("DROP TABLE temp._apply_ids")


def _finish_comment_merge(connection: sqlite3.Connection) -> None:
    """合并完成后更新计数和元数据，并统一校验最终结果。"""
    main_count = connection.execute("SELECT COUNT(*) FROM main").fetchone()[0]
    top_count = connection.execute("SELECT COUNT(*) FROM top").fetchone()[0]
    reply_count = connection.execute("SELECT COUNT(*) FROM reply").fetchone()[0]
    metadata_updates = {
        "schema_version": COMMENT_DB_SCHEMA_VERSION,
        "volatile_fields": ",".join(COMMENT_VOLATILE_FIELDS),
        "source_name": "merged-comment-history",
        "source_hash_mode": "merged-comment-history-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "main_count": str(main_count),
        "top_count": str(top_count),
        "reply_count": str(reply_count),
    }
    connection.executemany(
        "INSERT INTO _metadata(metadata_key,metadata_value) VALUES(?,?) "
        "ON CONFLICT(metadata_key) DO UPDATE "
        "SET metadata_value=excluded.metadata_value",
        metadata_updates.items(),
    )
    foreign_key_errors = connection.execute(
        "PRAGMA main.foreign_key_check"
    ).fetchall()
    if foreign_key_errors:
        raise sqlite3.IntegrityError(
            f"合并数据库外键检查失败：{foreign_key_errors[:3]}"
        )
    integrity_result = connection.execute(
        "PRAGMA main.integrity_check"
    ).fetchall()
    if integrity_result != [("ok",)]:
        raise sqlite3.DatabaseError(
            f"合并数据库完整性检查失败：{integrity_result[:3]}"
        )


def apply_comment_delta(database_path: Path, delta_path: Path) -> None:
    """把增量中的新增/变化覆盖到合并库；刻意忽略删除清单。"""
    ensure_comment_database_top_table(database_path)
    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        validate_comment_database(connection, "main")
        connection.execute(
            "ATTACH DATABASE ? AS delta_db", (str(Path(delta_path).resolve()),)
        )
        connection.execute("BEGIN IMMEDIATE")
        _apply_attached_comment_delta(connection, delta_path)
        _finish_comment_merge(connection)
        connection.commit()
    except Exception:
        if connection.in_transaction:
            connection.rollback()
        raise
    finally:
        connection.close()


def rebuild_merged_database(update_dir: Path, file_name: str,
                            merged_path: Path) -> None:
    """重放全部历史增量，并同步重建该来源的 deletelist。"""
    update_dir, merged_path = Path(update_dir), Path(merged_path)
    baseline = update_dir / file_name
    if not baseline.is_file():
        if merged_path.is_file():
            print(f"警告：缺少历史基库，使用现有合并库建立检查点：{baseline}")
            atomic_copy(merged_path, baseline)
        else:
            raise FileNotFoundError(f"找不到评论基库：{baseline}")
    temporary_path = merged_path.with_name(merged_path.name + ".rebuild.tmp")
    deltas = delta_paths(update_dir, file_name)
    deleted_rpids = set()
    connection = None
    try:
        shutil.copy2(baseline, temporary_path)
        # 这些设置仅用于可丢弃的重建临时库，绝不能用于正式库的增量更新。
        # 异常时关闭并删除整个临时库，不依赖回滚恢复；正式库保持原样。
        connection = sqlite3.connect(temporary_path)
        connection.execute("PRAGMA journal_mode=OFF")
        connection.execute("PRAGMA synchronous=OFF")
        connection.execute("PRAGMA temp_store=MEMORY")
        connection.execute("PRAGMA cache_size=-65536")  # 页缓存约 64 MiB
        # 避免删除每个实体时扫描所有引用表，最后统一检查外键。
        connection.execute("PRAGMA foreign_keys=OFF")
        validate_comment_database(connection, "main")
        if deltas:
            _ensure_comment_top_table(connection)
            connection.commit()
        for delta in deltas:
            # 每次只附加一个增量，兼容任意数量历史库；保留原始路径以支持 UNC。
            if not delta.is_file():
                raise FileNotFoundError(f"找不到评论增量库：{delta}")
            connection.execute(
                "ATTACH DATABASE ? AS delta_db",
                (str(delta.resolve()),),
            )
            connection.execute("BEGIN")
            _apply_attached_comment_delta(connection, delta)
            deleted_rpids.update(
                int(row[0]) for row in connection.execute(
                    "SELECT rpid FROM delta_db._deleted_records"
                )
            )
            # DETACH 要求当前事务结束；禁用临时库日志后不再逐增量写回滚日志。
            connection.commit()
            connection.execute("DETACH DATABASE delta_db")
        if deltas:
            _finish_comment_merge(connection)
        else:
            # 无增量时保持基库表结构和元数据不变，也校验后才发布。
            foreign_key_errors = connection.execute(
                "PRAGMA main.foreign_key_check"
            ).fetchmany(3)
            if foreign_key_errors:
                raise sqlite3.IntegrityError(
                    f"合并数据库外键检查失败：{foreign_key_errors}"
                )
            integrity_result = connection.execute(
                "PRAGMA main.integrity_check"
            ).fetchall()
            if integrity_result != [("ok",)]:
                raise sqlite3.DatabaseError(
                    f"合并数据库完整性检查失败：{integrity_result[:3]}"
                )
        connection.commit()
        # 校验成功后关闭连接并同步文件，以便 Windows 原子替换。
        connection.close()
        connection = None
        with temporary_path.open("rb+") as database_file:
            os.fsync(database_file.fileno())
        os.replace(temporary_path, merged_path)
        write_comment_deletelist(update_dir, file_name, deleted_rpids)
    finally:
        if connection is not None:
            connection.close()
        if temporary_path.exists():
            temporary_path.unlink()
    print(f"已从基库和 {len(deltas)} 个增量库重建：{merged_path}")


async def download_comment_database(bvid: str, output_path: Path,
                                    credential: Credential,
                                    resources: dict) -> int:
    """分页抓取一个 BV 的评论，处理完当前页便写入 v1.1 SQLite。"""
    aid = bvid2aid(bvid)
    source_url = f"https://www.bilibili.com/video/{bvid}"
    page = 1
    offset = ""
    total_comments = 0
    total_top_comments = 0
    written_top_rpids = set()
    with StreamingCommentDatabaseWriter(
        Path(output_path), source_url, bvid, aid
    ) as database_writer:
        while True:
            response = await comment.get_comments_lazy(
                aid,
                comment.CommentResourceType.VIDEO,
                offset=offset,
                credential=credential,
            )
            pagination = response["cursor"]["pagination_reply"]
            next_offset = pagination.get("next_offset", 404)
            is_last_page = next_offset == 404
            if not is_last_page:
                offset = next_offset
            replies = response.get("replies")
            if replies is None:
                print(f"{bvid} 后续评论页为空，结束本次抓取")
                break
            top_replies = response.get("top_replies") or []
            if not isinstance(top_replies, list):
                raise ValueError(f"{bvid} 的 top_replies 不是列表或 null")
            for top_comment in top_replies:
                top_rpid = comment_rpid(top_comment)
                # 接口可能在每一页重复携带相同置顶评论，只写入一次。
                if top_rpid in written_top_rpids:
                    continue
                reply_count = top_comment.get("rcount", 0)
                current_replies = top_comment.get("replies") or []
                if reply_count > len(current_replies):
                    completed = await get_sub_comment_by_dict(
                        top_comment, credential
                    )
                    if not completed:
                        print(
                            f"置顶评论 {top_rpid} 的子评论未完全取得，"
                            "保存当前已取得内容"
                        )
                remap_cmt_to_local(top_comment, resources)
                database_writer.write_top_comment(top_comment)
                written_top_rpids.add(top_rpid)
                total_top_comments += 1
            for comment_dict in replies:
                # 极少数接口响应会同时在 replies 中返回置顶项，避免重复入库。
                if comment_rpid(comment_dict) in written_top_rpids:
                    continue
                reply_count = comment_dict.get("rcount", 0)
                current_replies = comment_dict.get("replies") or []
                if reply_count > len(current_replies):
                    completed = await get_sub_comment_by_dict(
                        comment_dict, credential
                    )
                    if not completed:
                        print(
                            f"评论 {comment_dict.get('rpid', 0)} 的子评论未完全取得，"
                            "保存当前已取得内容"
                        )
                remap_cmt_to_local(comment_dict, resources)
                database_writer.write_main_comment(comment_dict)
                total_comments += 1
                del current_replies
            if replies:
                # 循环变量会继续引用最后一条评论，主动释放其可能很大的回复列表。
                del comment_dict
            database_writer.commit_page()
            print(f"{bvid} 第 {page} 页已写入，本页 {len(replies)} 条主评论")
            page += 1
            replies.clear()
            del replies, response
            if is_last_page:
                break
        database_writer.finalize()
        total_comments = database_writer.main_count
        total_top_comments = database_writer.top_count
    print(
        f"{bvid} 评论下载完成，共 {total_comments} 条主评论，"
        f"{total_top_comments} 条置顶评论"
    )
    return aid


def update_cmif(metadata_dir: Path, file_name: str) -> None:
    """在 cmif.json 中登记评论数据库引用。"""
    cmif_path = Path(metadata_dir) / "cmif.json"
    cmif = load_json_file(cmif_path, list, [])
    found = False
    changed = False
    for item in cmif:
        if not isinstance(item, dict):
            raise ValueError(f"{cmif_path} 中含有非字典配置")
        if item.get("comment-srcfile") == file_name:
            found = True
    if not found:
        cmif.append({
            "comment-srcfile": file_name,
            "resource-folder": "",
            "basic-resfolder": "bilibili-resource",
            "src": "B站",
        })
        changed = True
    if changed:
        write_json_file(cmif_path, cmif)


async def process_comment_sources(metadata_dir: Path, sources: list,
                                  credential: Credential,
                                  processed_comment_sources: dict = None) -> None:
    metadata_dir = Path(metadata_dir)
    comment_dir = metadata_dir.parent / "__COMMENT__"
    raw_dir = comment_dir / "raw"
    update_dir = comment_dir / "update"
    raw_dir.mkdir(parents=True, exist_ok=True)
    update_dir.mkdir(parents=True, exist_ok=True)
    cm_list_path = comment_dir / "cm-list.json"
    cm_list = load_json_file(cm_list_path, dict, {})
    if not cm_list_path.exists():
        write_json_file(cm_list_path, cm_list)
    cmif_path = metadata_dir / "cmif.json"
    if not cmif_path.exists():
        write_json_file(cmif_path, [])
    discovered_resources = empty_resource_urls()
    if processed_comment_sources is None:
        processed_comment_sources = {}
    # 上一次异常退出可能留下临时库；新一轮开始时一并回收。
    cleanup_comment_raw_files(raw_dir)

    try:
        for source in sources:
            if not isinstance(source, dict) or source.get("src") != "B站":
                continue
            bvid = str(source.get("BV", "")).strip()
            if not bvid:
                continue
            source_name = str(source.get("name") or bvid).strip()
            try:
                aid = bvid2aid(bvid)
                existing = cm_list.get(bvid)
                if existing is not None and not isinstance(existing, dict):
                    raise ValueError(f"{cm_list_path} 中 {bvid} 的值必须是字典")
                if existing is not None and not str(
                    existing.get("src-name", "") or ""
                ).strip():
                    # cm-srcURL.json 中缺少 name 时，source_name 已回退为 BV 号。
                    existing["src-name"] = source_name
                    write_json_file(cm_list_path, cm_list)
                    print(
                        f"评论来源缺少 src-name，已自动补全："
                        f"{bvid} -> {source_name}"
                    )
                run_key = comment_source_run_key(comment_dir, bvid)
                if existing:
                    file_name = str(existing.get("file-name", ""))
                    validate_comment_filename(file_name)
                    # 引用登记不依赖本次更新成功；已有合并库即可供该剧集使用。
                    update_cmif(metadata_dir, file_name)
                    processed_file = processed_comment_sources.get(run_key)
                    if processed_file is not None:
                        if processed_file != file_name:
                            raise ValueError(
                                f"同一评论目录中 {bvid} 的文件映射发生冲突："
                                f"{processed_file} / {file_name}"
                            )
                        print(
                            f"评论来源本次运行已下载，跳过重复抓取："
                            f"{source_name}（{bvid}）-> {file_name}"
                        )
                        continue

                    merged_path = comment_dir / file_name
                    print("合并增量库中......")
                    rebuild_merged_database(update_dir, file_name, merged_path)
                    raw_path = raw_dir / file_name
                    try:
                        await download_comment_database(
                            bvid, raw_path, credential, discovered_resources
                        )
                        delta_path = next_delta_path(update_dir, file_name)
                        create_comment_delta(
                            merged_path, raw_path, delta_path, bvid, aid
                        )
                        apply_comment_delta(merged_path, delta_path)
                        merge_delta_into_deletelist(
                            update_dir, file_name, delta_path
                        )
                    finally:
                        # 下载、建增量或合并任一步失败，都不保留 raw 临时库。
                        cleanup_comment_raw_files(raw_dir, file_name)
                else:
                    file_name = allocate_comment_filename(cm_list, comment_dir)
                    baseline_path = update_dir / file_name
                    await download_comment_database(
                        bvid, baseline_path, credential, discovered_resources
                    )
                    atomic_copy(baseline_path, comment_dir / file_name)
                    write_comment_deletelist(update_dir, file_name, [])

                comment_count, reply_count = comment_database_counts(
                    comment_dir / file_name
                )
                current = dict(existing or {})
                current.update({
                    "file-name": file_name,
                    "aid": aid,
                    "update-time": int(time.time()),
                    "comment-count": comment_count,
                    "reply-count": reply_count,
                })
                if existing is None:
                    current["src-name"] = source_name
                cm_list[bvid] = current
                write_json_file(cm_list_path, cm_list)
                update_cmif(metadata_dir, file_name)
                processed_comment_sources[run_key] = file_name
                print(f"评论来源处理完成：{source_name}（{bvid}）-> {file_name}")
            except Exception as error:
                print_error(
                    f"评论来源处理失败：{source_name}（{bvid}）："
                    f"{type(error).__name__}: {error}"
                )

        resources_path = comment_dir / "resources-URL.json"
        all_resources = merge_resource_urls(resources_path, discovered_resources)
        await download_comment_resources(
            all_resources, comment_dir / "comment-resource", credential
        )
        ensure_bilibili_resources(comment_dir)
    finally:
        cleanup_comment_raw_files(raw_dir)


async def main():
    global OVERWRITE_DAMAGED_JSON_FILES
    if not os.path.exists("cookie.json"):
        print_error("cookie.json 文件不存在，将退出程序")
        return
    with open("cookie.json", "r", encoding="utf-8") as file:
        use_cookie = json.load(file)

    is_auto_build = not input(
        "下载完成后是否需要自动构建弹幕目录并自动根据弹幕来源下载对应评论数据？"
        "有输入不自动构建，无输入默认全自动下载构建(您只需等待)"
    )
    OVERWRITE_DAMAGED_JSON_FILES = not input(
        "是否默认覆盖已经损坏的文件？"
        "无输入则自动覆盖损坏文件，有输入则保留损坏文件"
    )
    credential_ = Credential(
        sessdata=use_cookie["SESSDATA"],
        bili_jct=use_cookie["bili_jct"],
        buvid3=use_cookie["buvid3"],
    )
    with open("./basepath.json", "r", encoding="utf-8") as file:
        basepath_list = json.load(file)

    processed_comment_sources = {}
    for basepath in basepath_list:
        metadata_dir = Path(basepath)
        dm_src_url_path = metadata_dir / "dm-srcURL.json"
        if not metadata_dir.is_dir() or not dm_src_url_path.is_file():
            print_error(f"路径不存在或 {dm_src_url_path} 不存在：{metadata_dir}")
            continue
        dm_dir = metadata_dir / "raw"
        dm_dir.mkdir(parents=True, exist_ok=True)
        with dm_src_url_path.open("r", encoding="utf-8") as file:
            source_list = json.load(file)

        for item in source_list:
            source = item.get("src")
            bvid = item.get("BV")
            page = item.get("p", 1)
            name = item.get("name")
            dm_path = dm_dir / f"{name}.json"
            new_path = dm_path
            if dm_path.exists():
                number = 2
                while True:
                    new_path = dm_dir / f"{name}-{number}.json"
                    if not new_path.exists():
                        break
                    number += 1
            if source == "B站":
                print(f"正在下载弹幕：{bvid} P{page} -> {name}")
                result = await download_dm_by_bv(
                    bvid, page, credential_, str(new_path)
                )
                if result:
                    print(f"弹幕下载完成：{result}")
                else:
                    print_error(f"弹幕下载失败：{bvid} P{page}")
            await asyncio.sleep(2)

        print(f"弹幕来源下载完成：{metadata_dir}")
        should_build_dm = is_auto_build
        if not is_auto_build:
            should_build_dm = not input(
                "是否需要手动构建弹幕目录和重映射配置文件？"
                "无输入默认开始构建，有输入跳过"
            )
        if should_build_dm:
            print(f"正在构建弹幕目录：{metadata_dir}")
            build_dm(str(metadata_dir))
            print(f"正在生成或更新重映射配置文件：{metadata_dir}")
            build_rmcf(str(metadata_dir))

        should_download_comments = is_auto_build
        if not is_auto_build:
            should_download_comments = not input(
                f"是否需要根据 {dm_src_url_path} 下载并构建对应评论数据？"
                "无输入默认开始下载，有输入跳过"
            )
        if should_download_comments:
            try:
                comment_sources = build_cm_src_url(metadata_dir)
                await process_comment_sources(
                    metadata_dir, comment_sources, credential_,
                    processed_comment_sources,
                )
            except Exception as error:
                print_error(
                    f"评论目录构建失败：{metadata_dir}："
                    f"{type(error).__name__}: {error}"
                )

    try:
        session = get_aiohttp_session()
        await session.close()
    except Exception:
        pass


if __name__ == "__main__":
    print("实际解释器：", sys.executable)
    print("Python 版本：", sys.version)
    asyncio.run(main())
