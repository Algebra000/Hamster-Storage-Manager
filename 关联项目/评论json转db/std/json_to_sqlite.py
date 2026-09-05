#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标准层级版：把列表字典转换为容易阅读的 SQLite 表。

规则：顶层列表中的每个字典成为 ``main`` 一行，一级键成为 main 的列；
字典值保存子表 row_id，列表值保存 std_lists.list_id。子字典继续按相同方式
生成层级表。数据库不保存完整 raw JSON，只保证恢复后的键、值、层级和数组
顺序相同，不要求缩进或文件哈希相同。

辅助表 std_object_keys 用于区分缺失键和 null、记录单元格类型及引用表；
std_schema_tables/std_schema_columns 记录动态表结构；std_list_items 保存列表顺序。

使用：
    python json_to_sqlite.py example.json -o example_std.sqlite
    python sqlite_to_json.py example_std.sqlite -o restored.json
"""

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

PathKey = Tuple[str, ...]
ROOT_PATH: PathKey = ("$[]",)
MIN_INT, MAX_INT = -(2 ** 63), 2 ** 63 - 1

BASE_SCHEMA = r"""
PRAGMA foreign_keys=ON;
CREATE TABLE std_metadata(
    metadata_key TEXT PRIMARY KEY,
    metadata_value TEXT NOT NULL
);
CREATE TABLE std_schema_tables(
    table_name TEXT PRIMARY KEY,
    json_path TEXT NOT NULL UNIQUE,
    object_depth INTEGER NOT NULL
);
CREATE TABLE std_schema_columns(
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    json_key TEXT NOT NULL,
    column_order INTEGER NOT NULL,
    PRIMARY KEY(table_name,column_name),
    UNIQUE(table_name,json_key),
    FOREIGN KEY(table_name) REFERENCES std_schema_tables(table_name)
);
-- 每个对象行实际出现的键；由此区分“缺失”和“存在但为 null”。
CREATE TABLE std_object_keys(
    table_name TEXT NOT NULL,
    object_row_id INTEGER NOT NULL,
    key_order INTEGER NOT NULL,
    column_name TEXT NOT NULL,
    json_key TEXT NOT NULL,
    value_kind TEXT NOT NULL CHECK(value_kind IN
        ('string','integer','real','boolean','null','object','list')),
    reference_table TEXT,
    PRIMARY KEY(table_name,object_row_id,key_order),
    FOREIGN KEY(table_name) REFERENCES std_schema_tables(table_name),
    FOREIGN KEY(reference_table) REFERENCES std_schema_tables(table_name)
);
CREATE TABLE std_lists(
    list_id INTEGER PRIMARY KEY AUTOINCREMENT,
    json_path TEXT NOT NULL
);
CREATE TABLE std_list_items(
    list_id INTEGER NOT NULL,
    item_index INTEGER NOT NULL,
    value_kind TEXT NOT NULL CHECK(value_kind IN
        ('string','integer','real','boolean','null','object','list')),
    scalar_value,
    reference_table TEXT,
    reference_id INTEGER,
    PRIMARY KEY(list_id,item_index),
    FOREIGN KEY(list_id) REFERENCES std_lists(list_id) ON DELETE CASCADE,
    FOREIGN KEY(reference_table) REFERENCES std_schema_tables(table_name)
);
CREATE TABLE std_root_items(
    item_index INTEGER PRIMARY KEY,
    main_row_id INTEGER NOT NULL
);
CREATE INDEX idx_object_keys_lookup
    ON std_object_keys(table_name,object_row_id);
CREATE INDEX idx_list_items_lookup ON std_list_items(list_id,item_index);
"""


def quote_identifier(name: str) -> str:
    """安全引用动态表名/列名；SQL 参数占位符不能代替标识符。"""
    if "\x00" in name:
        raise ValueError("SQLite 标识符不能包含 NUL")
    return '"' + name.replace('"', '""') + '"'


def fingerprint(value: Any) -> str:
    """只关心键和值、不关心排版的规范化 SHA-256。"""
    data = json.dumps(value,ensure_ascii=False,sort_keys=True,
                      separators=(",",":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def path_text(path: PathKey) -> str:
    return "/".join(path)


def scalar_to_db(value: Any) -> Tuple[str, Any]:
    """把标量转成 SQLite 值；bool 要在 int 之前判断。"""
    if value is None:
        return "null", None
    if isinstance(value,bool):
        return "boolean", int(value)
    if isinstance(value,int):
        return "integer", value if MIN_INT <= value <= MAX_INT else str(value)
    if isinstance(value,float):
        return "real", value
    if isinstance(value,str):
        return "string", value
    raise TypeError("未知 JSON 标量：{}".format(type(value).__name__))


def scalar_from_db(kind: str, value: Any) -> Any:
    if kind == "null": return None
    if kind == "boolean": return bool(value)
    if kind == "integer": return int(value)
    if kind == "real": return float(value)
    if kind == "string": return value
    raise ValueError("{} 不是标量类型".format(kind))


class SchemaCollector:
    """第一遍扫描：收集每个字典路径的全部键。"""
    def __init__(self) -> None:
        self.keys: "OrderedDict[PathKey, OrderedDict[str, None]]" = OrderedDict()
        self.depths: Dict[PathKey,int] = {}

    def collect_root(self, root: Any) -> None:
        if not isinstance(root,list) or any(not isinstance(x,dict) for x in root):
            raise ValueError("标准版要求顶层是列表，且每个元素都是字典")
        for obj in root:
            self.collect_object(obj,ROOT_PATH,1)

    def collect_object(self,obj: Dict[str,Any],path: PathKey,depth: int) -> None:
        keys = self.keys.setdefault(path,OrderedDict())
        self.depths[path] = depth
        for key,value in obj.items():
            keys.setdefault(key,None)
            if isinstance(value,dict):
                self.collect_object(value,path+(key,),depth+1)
            elif isinstance(value,list):
                self.collect_list(value,path+(key+"[]",),depth+1)

    def collect_list(self,values: Sequence[Any],path: PathKey,depth: int) -> None:
        for value in values:
            if isinstance(value,dict):
                self.collect_object(value,path,depth)
            elif isinstance(value,list):
                self.collect_list(value,path+("[]",),depth)


def readable(text: str) -> str:
    text = re.sub(r"[^0-9A-Za-z_\u4e00-\u9fff]+","_",text).strip("_")
    return text[:36] or "object"


def assign_table_names(schema: SchemaCollector) -> Dict[PathKey,str]:
    """main 固定；子表名包含层级、路径和短哈希，既可读又不会冲突。"""
    result: Dict[PathKey,str] = {ROOT_PATH:"main"}
    for path in schema.keys:
        if path == ROOT_PATH:
            continue
        label = readable("_".join(path[1:]).replace("[]","_item"))
        suffix = hashlib.sha1(path_text(path).encode("utf-8")).hexdigest()[:6]
        result[path] = "level_{}_{}_{}".format(schema.depths[path],label,suffix)
    return result


def assign_columns(keys: Sequence[str]) -> Dict[str,str]:
    """正常键直接作为列名；空键、NUL 或大小写冲突才生成替代列名。"""
    result: Dict[str,str] = {}
    used = {"row_id"}
    for index,key in enumerate(keys):
        candidate = key
        folded = {name.casefold() for name in used}
        if not candidate or "\x00" in candidate or candidate.casefold() in folded:
            candidate = "column_{:04d}".format(index)
        result[key] = candidate
        used.add(candidate)
    return result


def key_for_column(columns: Dict[str,str],column: str) -> str:
    for key,value in columns.items():
        if value == column:
            return key
    raise KeyError(column)

class StandardWriter:
    """第二遍写入：动态建表，并让字典/列表值保存引用 ID。"""
    def __init__(self,db: sqlite3.Connection,schema: SchemaCollector):
        self.db = db
        self.schema = schema
        self.tables = assign_table_names(schema)
        self.columns: Dict[PathKey,Dict[str,str]] = {}

    def create_tables(self) -> None:
        """main 的列是一级键；每个子字典路径也生成同类实体表。"""
        for path,keys_map in self.schema.keys.items():
            table = self.tables[path]
            columns = assign_columns(list(keys_map.keys()))
            self.columns[path] = columns
            definitions = ",".join(quote_identifier(x) for x in columns.values())
            sql = "CREATE TABLE {}(row_id INTEGER PRIMARY KEY AUTOINCREMENT{}{})".format(
                quote_identifier(table),"," if definitions else "",definitions)
            self.db.execute(sql)
            self.db.execute("INSERT INTO std_schema_tables VALUES(?,?,?)",
                            (table,path_text(path),self.schema.depths[path]))
            for order,(json_key,column) in enumerate(columns.items()):
                self.db.execute("INSERT INTO std_schema_columns VALUES(?,?,?,?)",
                                (table,column,json_key,order))

    def store_object(self,obj: Dict[str,Any],path: PathKey) -> int:
        """子节点先写入，父对象列随后保存子 row_id/list_id。"""
        table = self.tables[path]
        column_map = self.columns[path]
        values: Dict[str,Any] = {}
        metadata: List[Tuple[int,str,str,Optional[str]]] = []
        for order,(key,value) in enumerate(obj.items()):
            column = column_map[key]
            ref_table: Optional[str] = None
            if isinstance(value,dict):
                child_path = path+(key,)
                stored = self.store_object(value,child_path)
                kind = "object"
                ref_table = self.tables[child_path]
            elif isinstance(value,list):
                stored = self.store_list(value,path+(key+"[]",))
                kind = "list"
            else:
                kind,stored = scalar_to_db(value)
            values[column] = stored
            metadata.append((order,column,kind,ref_table))

        if values:
            names = list(values)
            sql = "INSERT INTO {}({}) VALUES({})".format(
                quote_identifier(table),
                ",".join(quote_identifier(x) for x in names),
                ",".join("?" for _ in names))
            cur = self.db.execute(sql,[values[x] for x in names])
        else:
            cur = self.db.execute("INSERT INTO {} DEFAULT VALUES".format(
                quote_identifier(table)))
        row_id = int(cur.lastrowid)

        for order,column,kind,ref_table in metadata:
            self.db.execute("INSERT INTO std_object_keys VALUES(?,?,?,?,?,?,?)",
                (table,row_id,order,column,key_for_column(column_map,column),kind,ref_table))
        return row_id

    def store_list(self,values: Sequence[Any],item_path: PathKey) -> int:
        """列表自身一行，元素按 item_index 存放并引用对象/子列表。"""
        cur = self.db.execute("INSERT INTO std_lists(json_path) VALUES(?)",
                              (path_text(item_path),))
        list_id = int(cur.lastrowid)
        for index,value in enumerate(values):
            scalar = ref_table = ref_id = None
            if isinstance(value,dict):
                kind = "object"
                ref_table = self.tables[item_path]
                ref_id = self.store_object(value,item_path)
            elif isinstance(value,list):
                kind = "list"
                ref_id = self.store_list(value,item_path+("[]",))
            else:
                kind,scalar = scalar_to_db(value)
            self.db.execute("INSERT INTO std_list_items VALUES(?,?,?,?,?,?)",
                            (list_id,index,kind,scalar,ref_table,ref_id))
        return list_id


def create_database(source: Path,database: Path,overwrite=False) -> Dict[str,Any]:
    """创建标准版数据库；任一步失败都会回滚并删除不完整新库。"""
    source,database = source.resolve(),database.resolve()
    if not source.is_file():
        raise FileNotFoundError("找不到输入 JSON：{}".format(source))
    if source == database:
        raise ValueError("输入 JSON 和输出数据库不能是同一文件")
    if database.exists():
        if not overwrite:
            raise FileExistsError("数据库已存在；请添加 --overwrite：{}".format(database))
        database.unlink()
    database.parent.mkdir(parents=True,exist_ok=True)
    with source.open("r",encoding="utf-8-sig") as file:
        root = json.load(file)
    schema = SchemaCollector()
    schema.collect_root(root)
    db: Optional[sqlite3.Connection] = None
    try:
        db = sqlite3.connect(str(database))
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript(BASE_SCHEMA)
        with db:
            writer = StandardWriter(db,schema)
            writer.create_tables()
            db.execute("INSERT INTO std_metadata VALUES('source_name',?)",(source.name,))
            db.execute("INSERT INTO std_metadata VALUES('semantic_sha256',?)",
                       (fingerprint(root),))
            db.execute("INSERT INTO std_metadata VALUES('root_type','list_of_objects')")
            for index,item in enumerate(root):
                row_id = writer.store_object(item,ROOT_PATH)
                db.execute("INSERT INTO std_root_items VALUES(?,?)",(index,row_id))
        table_count = db.execute("SELECT COUNT(*) FROM std_schema_tables").fetchone()[0]
        return {"items":len(root),"tables":table_count,"fingerprint":fingerprint(root)}
    except Exception:
        if db is not None:
            db.close()
            db = None
        if database.exists():
            database.unlink()
        raise
    finally:
        if db is not None:
            db.close()

class StandardReader:
    """读取动态实体表，按照 std_object_keys 恢复对象。"""
    def __init__(self,db: sqlite3.Connection):
        self.db = db

    def object(self,table: str,row_id: int) -> Dict[str,Any]:
        row = self.db.execute(
            "SELECT * FROM {} WHERE row_id=?".format(quote_identifier(table)),
            (row_id,)).fetchone()
        if row is None:
            raise ValueError("表 {} 中没有 row_id={}".format(table,row_id))
        result: Dict[str,Any] = {}
        metas = self.db.execute(
            "SELECT * FROM std_object_keys WHERE table_name=? AND object_row_id=? "
            "ORDER BY key_order",(table,row_id)).fetchall()
        for meta in metas:
            kind = meta["value_kind"]
            stored = row[meta["column_name"]]
            if kind == "object":
                if meta["reference_table"] is None or stored is None:
                    raise ValueError("对象引用缺少表名或 row_id")
                value = self.object(meta["reference_table"],int(stored))
            elif kind == "list":
                if stored is None:
                    raise ValueError("列表引用缺少 list_id")
                value = self.list_value(int(stored))
            else:
                value = scalar_from_db(kind,stored)
            result[meta["json_key"]] = value
        return result

    def list_value(self,list_id: int) -> List[Any]:
        if self.db.execute("SELECT 1 FROM std_lists WHERE list_id=?",(list_id,)).fetchone() is None:
            raise ValueError("找不到 list_id={}".format(list_id))
        result: List[Any] = []
        rows = self.db.execute(
            "SELECT * FROM std_list_items WHERE list_id=? ORDER BY item_index",
            (list_id,)).fetchall()
        for expected,row in enumerate(rows):
            if row["item_index"] != expected:
                raise ValueError("list_id={} 的 item_index 不连续".format(list_id))
            kind = row["value_kind"]
            if kind == "object":
                if row["reference_table"] is None or row["reference_id"] is None:
                    raise ValueError("列表对象元素的引用不完整")
                value = self.object(row["reference_table"],int(row["reference_id"]))
            elif kind == "list":
                if row["reference_id"] is None:
                    raise ValueError("嵌套列表引用不完整")
                value = self.list_value(int(row["reference_id"]))
            else:
                value = scalar_from_db(kind,row["scalar_value"])
            result.append(value)
        return result


def restore_database(database: Path,output: Path,overwrite=False) -> Dict[str,Any]:
    """从数据库恢复 JSON，并用语义指纹核对所有键和值。"""
    database,output = database.resolve(),output.resolve()
    if not database.is_file():
        raise FileNotFoundError("找不到数据库：{}".format(database))
    if database == output:
        raise ValueError("输入数据库和输出 JSON 不能是同一文件")
    if output.exists() and not overwrite:
        raise FileExistsError("输出已存在；请添加 --overwrite：{}".format(output))
    db = sqlite3.connect(str(database))
    db.row_factory = sqlite3.Row
    try:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("SQLite 完整性检查失败")
        fk_errors = db.execute("PRAGMA foreign_key_check").fetchall()
        if fk_errors:
            raise ValueError("SQLite 外键检查失败：{}".format(fk_errors))
        reader = StandardReader(db)
        root: List[Any] = []
        for expected,row in enumerate(db.execute(
                "SELECT * FROM std_root_items ORDER BY item_index")):
            if row["item_index"] != expected:
                raise ValueError("顶层列表 item_index 不连续")
            root.append(reader.object("main",row["main_row_id"]))
        expected_hash = db.execute(
            "SELECT metadata_value FROM std_metadata "
            "WHERE metadata_key='semantic_sha256'").fetchone()
        if expected_hash is None:
            raise ValueError("数据库缺少 semantic_sha256")
        actual_hash = fingerprint(root)
        if actual_hash != expected_hash[0]:
            raise ValueError("键值校验失败：期望 {}，实际 {}".format(
                expected_hash[0],actual_hash))
        output.parent.mkdir(parents=True,exist_ok=True)
        with output.open("w",encoding="utf-8",newline="\n") as file:
            json.dump(root,file,ensure_ascii=False,indent=4)
            file.write("\n")
        return {"items":len(root),"fingerprint":actual_hash}
    finally:
        db.close()


def build_parser() -> argparse.ArgumentParser:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="标准层级版 JSON→SQLite 转换器")
    parser.add_argument("input_json",nargs="?",type=Path,default=here/"example.json")
    parser.add_argument("-o","--output",type=Path,
                        help="默认生成 std/example_std.sqlite")
    parser.add_argument("--overwrite",action="store_true",help="允许重建已有数据库")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = args.output or Path(__file__).resolve().parent/"example_std.sqlite"
    try:
        result = create_database(args.input_json,output,args.overwrite)
    except (OSError,ValueError,TypeError,json.JSONDecodeError,sqlite3.Error) as exc:
        print("转换失败：{}".format(exc),file=sys.stderr)
        return 1
    print("标准版 JSON -> SQLite 完成：{}".format(output.resolve()))
    print("顶层字典：{} 条".format(result["items"]))
    print("字典层级表：{} 张".format(result["tables"]))
    print("语义 SHA-256：{}".format(result["fingerprint"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())