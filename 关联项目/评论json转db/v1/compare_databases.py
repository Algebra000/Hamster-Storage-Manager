#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速比较两个 v1 评论快照数据库并生成 JSON 差异报告。

比较分两阶段：
1. 使用 SQLite ATTACH，把 1.db 和 2.db 同时挂到一个内存连接，按 rpid/parent
   主键做 JOIN，并比较生成时保存的短哈希。这一步只扫描索引和少量列。
2. 仅对哈希不同的行批量读取完整数据，列出具体字段的旧值和新值。

这比把两个上万行数据库全部读进 Python 再逐行搜索快得多，内存占用也更低。

使用：
    python compare_databases.py 1.db 2.db -o changes.json
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from json_to_sqlite import SCHEMA_VERSION, VOLATILE_FIELDS, quote_identifier


def qualified(schema: str,table: str) -> str:
    if schema not in ("old_db","new_db"):
        raise ValueError("未知附加数据库别名：{}".format(schema))
    return quote_identifier(schema)+"."+quote_identifier(table)


def metadata(db: sqlite3.Connection,schema: str) -> Dict[str,str]:
    rows=db.execute("SELECT metadata_key,metadata_value FROM {}".format(
        qualified(schema,"_metadata"))).fetchall()
    return {row[0]:row[1] for row in rows}


def table_columns(db: sqlite3.Connection,schema: str,table: str) -> List[str]:
    sql="PRAGMA {}.table_info({})".format(schema,quote_identifier(table))
    return [row[1] for row in db.execute(sql)]


def table_exists(db: sqlite3.Connection,schema: str,table: str) -> bool:
    return db.execute(
        "SELECT 1 FROM {}.sqlite_master WHERE type='table' AND name=?".format(schema),
        (table,),
    ).fetchone() is not None


def id_difference(db: sqlite3.Connection,table: str,key: str,
                  left_schema: str,right_schema: str) -> List[int]:
    """找出只存在于 left、而不存在于 right 的主键。"""
    sql="""
        SELECT l.{key}
        FROM {left} AS l
        LEFT JOIN {right} AS r ON r.{key}=l.{key}
        WHERE r.{key} IS NULL
        ORDER BY l.{key}
    """.format(key=quote_identifier(key),left=qualified(left_schema,table),
               right=qualified(right_schema,table))
    return [int(row[0]) for row in db.execute(sql)]


def changed_ids(db: sqlite3.Connection,table: str,key: str,hash_column: str) -> List[int]:
    """利用主键 JOIN 和行哈希筛选真正发生变化的共有行。"""
    sql="""
        SELECT n.{key}
        FROM {new} AS n
        JOIN {old} AS o ON o.{key}=n.{key}
        WHERE o.{hash_col} IS NOT n.{hash_col}
        ORDER BY n.{key}
    """.format(key=quote_identifier(key),new=qualified("new_db",table),
               old=qualified("old_db",table),hash_col=quote_identifier(hash_column))
    return [int(row[0]) for row in db.execute(sql)]


def chunks(values: Sequence[int],size: int=800) -> Iterable[Sequence[int]]:
    """SQLite 默认参数数量有限，因此把大量主键分块查询。"""
    for start in range(0,len(values),size):
        yield values[start:start+size]


def fetch_rows(db: sqlite3.Connection,schema: str,table: str,key: str,
               ids: Sequence[int]) -> Dict[int,sqlite3.Row]:
    result: Dict[int,sqlite3.Row]={}
    for group in chunks(ids):
        placeholders=",".join("?" for _ in group)
        sql="SELECT * FROM {} WHERE {} IN ({})".format(
            qualified(schema,table),quote_identifier(key),placeholders)
        for row in db.execute(sql,list(group)):
            result[int(row[key])]=row
    return result



def row_changes(old: sqlite3.Row,new: sqlite3.Row,fields: Sequence[str]) -> Dict[str,Any]:
    """比较字段值；字段不存在与字段值为 null 均按 None 处理。"""
    changes: Dict[str,Any]={}
    for field in fields:
        old_value=old[field] if field in old.keys() else None
        new_value=new[field] if field in new.keys() else None
        if old_value!=new_value:
            changes[field]={"old":old_value,"new":new_value}
    return changes


def compare_table(db: sqlite3.Connection,table: str,key: str,hash_column: str,
                  fields: Optional[Sequence[str]]=None) -> Dict[str,Any]:
    """比较一张逻辑表，返回新增、删除和变化详情。"""
    added=id_difference(db,table,key,"new_db","old_db")
    removed=id_difference(db,table,key,"old_db","new_db")
    changed=changed_ids(db,table,key,hash_column)
    if fields is None:
        old_columns=set(table_columns(db,"old_db",table))
        new_columns=set(table_columns(db,"new_db",table))
        ignored={key,"_comment_kind","_data_hash"}
        fields=sorted((old_columns|new_columns)-ignored)
    old_rows=fetch_rows(db,"old_db",table,key,changed)
    new_rows=fetch_rows(db,"new_db",table,key,changed)
    details=[]
    for row_id in changed:
        changes=row_changes(old_rows[row_id],new_rows[row_id],fields)
        details.append({key:row_id,"fields":changes})
    return {
        "added_count":len(added),"added":added,
        "removed_count":len(removed),"removed":removed,
        "changed_count":len(changed),"changed":details,
    }


def compare_optional_table(db: sqlite3.Connection,table: str,key: str,
                           hash_column: str,
                           fields: Optional[Sequence[str]]=None) -> Dict[str,Any]:
    """兼容尚无 top 表的早期 v1.1：缺表等价于一张空表。"""
    old_exists=table_exists(db,"old_db",table)
    new_exists=table_exists(db,"new_db",table)
    if old_exists and new_exists:
        return compare_table(db,table,key,hash_column,fields)
    empty={
        "added_count":0,"added":[],"removed_count":0,"removed":[],
        "changed_count":0,"changed":[],
    }
    if not old_exists and not new_exists:
        return empty
    schema="new_db" if new_exists else "old_db"
    ids=[int(row[0]) for row in db.execute(
        "SELECT {} FROM {} ORDER BY {}".format(
            quote_identifier(key),qualified(schema,table),quote_identifier(key)
        )
    )]
    if new_exists:
        empty["added"],empty["added_count"]=ids,len(ids)
    else:
        empty["removed"],empty["removed_count"]=ids,len(ids)
    return empty


def compare_databases(old_path: Path,new_path: Path) -> Dict[str,Any]:
    """挂载两个只读快照，完成五张核心表的比较。"""
    old_path,new_path=old_path.resolve(),new_path.resolve()
    if not old_path.is_file(): raise FileNotFoundError("找不到旧数据库：{}".format(old_path))
    if not new_path.is_file(): raise FileNotFoundError("找不到新数据库：{}".format(new_path))
    db=sqlite3.connect(":memory:")
    db.row_factory=sqlite3.Row
    try:
        db.execute("ATTACH DATABASE ? AS old_db",(str(old_path),))
        db.execute("ATTACH DATABASE ? AS new_db",(str(new_path),))
        old_meta,new_meta=metadata(db,"old_db"),metadata(db,"new_db")
        if old_meta.get("schema_version")!=SCHEMA_VERSION:
            raise ValueError("旧数据库不是 {} 结构".format(SCHEMA_VERSION))
        if new_meta.get("schema_version")!=SCHEMA_VERSION:
            raise ValueError("新数据库不是 {} 结构".format(SCHEMA_VERSION))
        expected_volatile_fields=",".join(VOLATILE_FIELDS)
        if old_meta.get("volatile_fields")!=expected_volatile_fields:
            raise ValueError("旧数据库的 _volatile_hash 字段口径与当前 v1.1 标准不一致，请重新生成")
        if new_meta.get("volatile_fields")!=expected_volatile_fields:
            raise ValueError("新数据库的 _volatile_hash 字段口径与当前 v1.1 标准不一致，请重新生成")
        # 附加完成后切成只读，防止比较过程意外修改快照。
        db.execute("PRAGMA query_only=ON")
        report={
            "schema_version":SCHEMA_VERSION,
            "generated_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "old_database":str(old_path),"new_database":str(new_path),
            "old_metadata":old_meta,"new_metadata":new_meta,
            "main":compare_table(db,"main","rpid","_volatile_hash",VOLATILE_FIELDS),
            "top":compare_optional_table(
                db,"top","rpid","_volatile_hash",VOLATILE_FIELDS),
            "reply":compare_table(db,"reply","rpid","_volatile_hash",VOLATILE_FIELDS),
            # parent 就是评论 rpid。同一用户在不同评论中的两行会分别比较。
            "member":compare_table(db,"member","parent","_data_hash"),
            "content":compare_table(db,"content","parent","_data_hash"),
        }
        return report
    finally:
        db.close()


def print_summary(report: Dict[str,Any]) -> None:
    print("快照比较完成")
    for table in ("main","top","reply","member","content"):
        result=report[table]
        print("{}：新增 {}，删除 {}，变化 {}".format(
            table,result["added_count"],result["removed_count"],result["changed_count"]))


def build_parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description="快速比较两个 B 站评论 v1 快照数据库")
    parser.add_argument("old_database",type=Path,help="较早生成的 1.db")
    parser.add_argument("new_database",type=Path,help="较晚生成的 2.db")
    parser.add_argument("-o","--output",type=Path,default=Path("changes.json"),
                        help="差异报告路径，默认 changes.json")
    parser.add_argument("--overwrite",action="store_true",help="允许覆盖已有报告")
    return parser


def main() -> int:
    args=build_parser().parse_args()
    output=args.output.resolve()
    if output.exists() and not args.overwrite:
        print("比较失败：报告已存在，请添加 --overwrite：{}".format(output),file=sys.stderr)
        return 1
    try:
        report=compare_databases(args.old_database,args.new_database)
        output.parent.mkdir(parents=True,exist_ok=True)
        with output.open("w",encoding="utf-8",newline="\n") as file:
            json.dump(report,file,ensure_ascii=False,indent=2)
            file.write("\n")
    except (OSError,ValueError,json.JSONDecodeError,sqlite3.Error) as error:
        print("比较失败：{}".format(error),file=sys.stderr)
        return 1
    print_summary(report)
    print("详细报告：{}".format(output))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
