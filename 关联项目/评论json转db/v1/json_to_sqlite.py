#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成便于比较不同时间点的 B 站评论 v1 SQLite 快照。

核心表：
* main：普通顶层评论；一级键直接成为列。
* top：带 is_top=true 的置顶顶层评论；列结构与 main 相同。
* reply：replies 中的评论；结构与 main 相同，但 replies 自身不入库。
* member：每条评论独立一行，parent 是引用它的评论 rpid，同一用户不合并。
* content：每条评论独立一行，parent 同样是评论 rpid。

reply_control 过滤掉动态 time_desc 等字段，只保留 max_line、location、
translation_switch、support_share 后作为 JSON 字符串保存。member/content 两列保存
子表 parent 的引用。其他字典和列表值（包括 member/content 内的二级及更深字段）直接存为
紧凑 JSON 字符串。为快速比较快照，评论行生成 _volatile_hash，member/content
生成 _data_hash；compare_databases.py 先比较哈希，再展开真正变化的字段。

使用：
    python json_to_sqlite.py ../example.json -o 1.db
    python json_to_sqlite.py newest.json -o 2.db
    python compare_databases.py 1.db 2.db -o changes.json
"""

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

SCHEMA_VERSION="v1.1"
VOLATILE_FIELDS: Tuple[str,...] = (
    "count","rcount","state","fansgrade","attr","like","action","invisible",
    "reply_control"
)
SKIPPED={"replies"}
REPLY_CONTROL_FIELDS=("max_line","location","translation_switch","support_share")
SPECIAL={"member","content"}


def quote_identifier(name: str) -> str:
    """安全引用由 JSON 键得到的 SQLite 列名。"""
    if "\x00" in name:
        raise ValueError("JSON 键包含 NUL，不能用作 SQLite 列名")
    return '"'+name.replace('"','""')+'"'


def reject_constant(text: str) -> None:
    raise ValueError("JSON 出现非标准数值：{}".format(text))


def load_comments(path: Path) -> List[Dict[str,Any]]:
    with path.open("r",encoding="utf-8-sig") as file:
        data=json.load(file,parse_constant=reject_constant)
    if not isinstance(data,list):
        raise ValueError("v1 要求 JSON 顶层是列表")
    if any(not isinstance(item,dict) for item in data):
        raise ValueError("顶层列表的每一项都必须是字典")
    return data


def comment_rpid(comment: Dict[str,Any]) -> int:
    value=comment.get("rpid_str",comment.get("rpid"))
    if value in (None,""):
        raise ValueError("评论缺少 rpid/rpid_str")
    try:
        result=int(value)
    except (TypeError,ValueError) as error:
        raise ValueError("无效 rpid：{!r}".format(value)) from error
    if not -(2**63) <= result <= 2**63-1:
        raise ValueError("rpid 超出 SQLite 64 位整数范围：{}".format(result))
    return result



def compact_json(value: Any,sort_keys=False) -> str:
    return json.dumps(value,ensure_ascii=False,sort_keys=sort_keys,
                      separators=(",",":"),allow_nan=False)


def database_value(value: Any) -> Any:
    """嵌套值直接放 JSON 字符串；标量保持 SQLite 原生类型。"""
    if isinstance(value,(dict,list)):
        return compact_json(value)
    if isinstance(value,bool):
        return int(value)
    if isinstance(value,int) and not -(2**63) <= value <= 2**63-1:
        return str(value)
    return value


def reply_control_value(value: Any) -> Optional[str]:
    """只保留稳定且有业务价值的 reply_control 白名单字段。"""
    if value is None:
        return None
    if not isinstance(value,dict):
        raise ValueError("reply_control 必须是字典或 null")
    filtered={key:value[key] for key in REPLY_CONTROL_FIELDS if key in value}
    return compact_json(filtered)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(compact_json(value,sort_keys=True).encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda:file.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()


def iter_replies(comment: Dict[str,Any]) -> Iterator[Dict[str,Any]]:
    """递归展开 replies；每个回复仅进入 reply 表，不进入 main。"""
    replies=comment.get("replies")
    if replies is None:
        return
    if not isinstance(replies,list):
        raise ValueError("评论 {} 的 replies 不是列表或 null".format(comment_rpid(comment)))
    for reply in replies:
        if not isinstance(reply,dict):
            raise ValueError("评论 {} 含非字典回复".format(comment_rpid(comment)))
        yield reply
        yield from iter_replies(reply)


def key_union(objects: Iterable[Dict[str,Any]],skipped: Sequence[str]=()) -> List[str]:
    """按首次出现顺序收集字段，确保两个快照的常见字段列名稳定。"""
    result: List[str]=[]
    seen=set()
    skipped_set=set(skipped)
    for obj in objects:
        for key in obj:
            if key not in skipped_set and key not in seen:
                seen.add(key)
                result.append(key)
    return result


def check_reserved(keys: Sequence[str],reserved: Sequence[str],table: str) -> None:
    """检查 keys（用户定义的键名列表）中是否有与 reserved（系统保留字列表）重复的项，如果有就抛出异常。"""
    conflicts=sorted(set(keys).intersection(reserved))
    if conflicts:
        raise ValueError("{} 键与内部列冲突：{}".format(table,",".join(conflicts)))


def create_entity_table(db: sqlite3.Connection,table: str,keys: Sequence[str]) -> None:
    """member/content 的 parent 是评论 rpid，也是唯一主键。"""
    check_reserved(keys,("parent","_comment_kind","_data_hash"),table)
    definitions=[
        "parent INTEGER PRIMARY KEY",
        "_comment_kind TEXT NOT NULL CHECK(_comment_kind IN ('main','reply'))",
        "_data_hash TEXT NOT NULL",
    ]+[quote_identifier(key) for key in keys]
    db.execute("CREATE TABLE {}({})".format(quote_identifier(table),",".join(definitions)))


def create_comment_table(db: sqlite3.Connection,table: str,keys: Sequence[str]) -> None:
    """main/reply 使用同一组一级键。"""
    check_reserved(keys,("_volatile_hash",),table)
    if "rpid" not in keys:
        raise ValueError("评论缺少 rpid 键")
    definitions=[]
    for key in keys:
        if key=="rpid": definitions.append("rpid INTEGER PRIMARY KEY")
        elif key in SPECIAL: definitions.append("{} INTEGER".format(quote_identifier(key)))
        else: definitions.append(quote_identifier(key))
    definitions.append("_volatile_hash TEXT NOT NULL")

    definitions.extend(("FOREIGN KEY(member) REFERENCES member(parent)",
                        "FOREIGN KEY(content) REFERENCES content(parent)"))
    db.execute("CREATE TABLE {}({})".format(quote_identifier(table),",".join(definitions)))

def insert_entity(db: sqlite3.Connection,table: str,parent: int,kind: str,
                  data: Any,keys: Sequence[str]) -> Optional[int]:
    """每条评论单独插入 member/content；即使 mid 相同也不会合并。"""
    if not isinstance(data,dict):
        return None
    columns=["parent","_comment_kind","_data_hash"]+list(keys)
    values=[parent,kind,stable_hash(data)]
    values.extend(database_value(data.get(key)) if key in data else None for key in keys)
    db.execute("INSERT INTO {}({}) VALUES({})".format(
        quote_identifier(table),
        ",".join(quote_identifier(column) for column in columns),
        ",".join("?" for _ in columns)),values)
    return parent


def volatile_hash(comment: Dict[str,Any]) -> str:
    # 不区分字段缺失和显式 null；两者写入 SQLite 后都是 NULL。
    values={field:comment.get(field) for field in VOLATILE_FIELDS}
    # 必须与 reply_control 数据库列使用相同的四键过滤结果，避免 time_desc
    # 等被丢弃的动态字段造成无意义的哈希变化。
    values["reply_control"]=reply_control_value(comment.get("reply_control"))
    return stable_hash(values)



def insert_comment(db: sqlite3.Connection,table: str,comment: Dict[str,Any],
                   comment_keys: Sequence[str],member_keys: Sequence[str],
                   content_keys: Sequence[str]) -> int:
    rpid=comment_rpid(comment)
    # top 也是顶层评论，实体表沿用 main 类型以兼容早期 v1.1 的约束。
    kind="reply" if table=="reply" else "main"
    member_ref=insert_entity(db,"member",rpid,kind,comment.get("member"),member_keys)
    content_ref=insert_entity(db,"content",rpid,kind,comment.get("content"),content_keys)
    columns=list(comment_keys)+["_volatile_hash"]
    values: List[Any]=[]
    for key in comment_keys:
        if key=="rpid": values.append(rpid)
        elif key=="member": values.append(member_ref)
        elif key=="content": values.append(content_ref)
        elif key=="reply_control": values.append(reply_control_value(comment.get(key)))
        else: values.append(database_value(comment.get(key)) if key in comment else None)
    values.append(volatile_hash(comment))

    db.execute("INSERT INTO {}({}) VALUES({})".format(
        quote_identifier(table),
        ",".join(quote_identifier(column) for column in columns),
        ",".join("?" for _ in columns)),values)
    return rpid


def create_indexes(db: sqlite3.Connection,keys: Sequence[str]) -> None:
    """rpid 主键自动有索引；这里补充评论树和时间/用户查询索引。"""
    for table in ("main","top","reply"):
        for key in ("mid","ctime","like","parent","root"):
            if key in keys:
                db.execute("CREATE INDEX {} ON {}({})".format(
                    quote_identifier("idx_{}_{}".format(table,key)),
                    quote_identifier(table),quote_identifier(key)))



def create_database_from_comments(main_comments: List[Dict[str,Any]],output: Path,
                                  overwrite=False,source_name="comments",
                                  source_sha256: Optional[str]=None,
                                  extra_metadata: Optional[Dict[str,Any]]=None) -> Dict[str,int]:
    """把内存中的评论列表直接写成 v1.1 数据库。"""
    if not isinstance(main_comments,list):
        raise ValueError("评论数据必须是列表")
    if any(not isinstance(item,dict) for item in main_comments):
        raise ValueError("评论列表的每一项都必须是字典")
    output=output.resolve()
    if output.exists():
        if not overwrite:
            raise FileExistsError("输出已存在；请添加 --overwrite：{}".format(output))
        output.unlink()
    output.parent.mkdir(parents=True,exist_ok=True)

    source_comments=main_comments
    top_comments=[comment for comment in source_comments if comment.get("is_top") is True]
    main_comments=[comment for comment in source_comments if comment.get("is_top") is not True]
    reply_comments=[
        reply for parent in main_comments+top_comments for reply in iter_replies(parent)
    ]
    all_comments=main_comments+top_comments+reply_comments
    comment_keys=key_union(all_comments,SKIPPED)
    for key in ("member","content"):
        if key not in comment_keys: comment_keys.append(key)
    members=[x["member"] for x in all_comments if isinstance(x.get("member"),dict)]
    contents=[x["content"] for x in all_comments if isinstance(x.get("content"),dict)]
    member_keys=key_union(members)
    content_keys=key_union(contents)

    db: Optional[sqlite3.Connection]=None
    try:
        db=sqlite3.connect(str(output))
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("CREATE TABLE _metadata(metadata_key TEXT PRIMARY KEY,metadata_value TEXT NOT NULL)")
        create_entity_table(db,"member",member_keys)
        create_entity_table(db,"content",content_keys)
        create_comment_table(db,"main",comment_keys)
        create_comment_table(db,"top",comment_keys)
        create_comment_table(db,"reply",comment_keys)
        with db:
            for comment in main_comments:
                insert_comment(db,"main",comment,comment_keys,member_keys,content_keys)
            for comment in top_comments:
                insert_comment(db,"top",comment,comment_keys,member_keys,content_keys)
            for comment in reply_comments:
                insert_comment(db,"reply",comment,comment_keys,member_keys,content_keys)
            create_indexes(db,comment_keys)
            metadata={
                "schema_version":SCHEMA_VERSION,
                "source_name":str(source_name),
                "source_sha256":source_sha256 or stable_hash(source_comments),
                "created_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "main_count":str(len(main_comments)),
                "top_count":str(len(top_comments)),
                "reply_count":str(len(reply_comments)),
                "volatile_fields":",".join(VOLATILE_FIELDS),
                "reply_control_fields":",".join(REPLY_CONTROL_FIELDS),
            }
            if extra_metadata:
                conflicts=set(metadata).intersection(extra_metadata)
                if conflicts:
                    raise ValueError("附加元数据覆盖保留键：{}".format(",".join(sorted(conflicts))))
                metadata.update({str(key):str(value) for key,value in extra_metadata.items()})
            db.executemany("INSERT INTO _metadata VALUES(?,?)",metadata.items())
        return {
            "main":len(main_comments),"top":len(top_comments),
            "reply":len(reply_comments),
            "member":db.execute("SELECT COUNT(*) FROM member").fetchone()[0],
            "content":db.execute("SELECT COUNT(*) FROM content").fetchone()[0],
        }
    except Exception:
        if db is not None:
            db.close(); db=None
        if output.exists(): output.unlink()
        raise
    finally:
        if db is not None: db.close()


def create_database(source: Path,output: Path,overwrite=False) -> Dict[str,int]:
    """读取 JSON 文件并生成完整快照。"""
    source,output=source.resolve(),output.resolve()
    if not source.is_file():
        raise FileNotFoundError("找不到输入 JSON：{}".format(source))
    if source==output:
        raise ValueError("输入 JSON 和输出数据库不能相同")
    return create_database_from_comments(
        load_comments(source),output,overwrite,
        source_name=source.name,source_sha256=file_hash(source)
    )


def build_parser() -> argparse.ArgumentParser:
    here=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser(description="生成 B 站评论 v1 快照数据库")
    parser.add_argument("input_json",nargs="?",type=Path,default=here.parent/"example.json")
    parser.add_argument("-o","--output",type=Path,help="默认生成 v1/1.db")
    parser.add_argument("--overwrite",action="store_true")
    return parser


def main() -> int:
    args=build_parser().parse_args()
    output=args.output or Path(__file__).resolve().parent/"1.db"
    try:
        result=create_database(args.input_json,output,args.overwrite)
    except (OSError,ValueError,TypeError,json.JSONDecodeError,sqlite3.Error) as error:
        print("转换失败：{}".format(error),file=sys.stderr)
        return 1
    print("v1 快照生成完成：{}".format(output.resolve()))
    print("main：{} 条".format(result["main"]))
    print("top：{} 条".format(result["top"]))
    print("reply：{} 条".format(result["reply"]))
    print("member：{} 条".format(result["member"]))
    print("content：{} 条".format(result["content"]))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
