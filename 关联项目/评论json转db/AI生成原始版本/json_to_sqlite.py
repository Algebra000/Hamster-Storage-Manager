#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 UTF-8 JSON 无损、完整地关系化到 SQLite。

设计目标：
1. 数据库不保存完整对象/数组的 raw JSON 字符串。
2. 每个对象、数组、键和值都单独解析，字典值通过外键指向另一个节点。
3. ``sqlite_to_json.py`` 可逐字节恢复源 JSON，SHA-256 必须完全一致。

为什么不用 json.load/json.dump
-----------------------------
普通 JSON 解析会丢掉缩进、CRLF/LF、键顺序、重复键、数字的 1/1.0/1e0
写法，以及“中”和“\\u4e2d”的区别。它们语义可能相同，文件哈希却不同。
因此本程序既保存解析后的值，也把不可推导的字符串词法、数字词法和标点间
空白拆成独立列。注意：单个标量词法不是完整 raw JSON 对象。

主要表：
* json_documents：文件哈希、BOM、根节点引用和文档首尾空白。
* json_nodes：所有 JSON 值的公共节点及类型。
* json_objects/json_arrays：对象和数组节点。
* json_object_members：对象键及 value_node_id 外键。
* json_array_items：数组元素及 value_node_id 外键。
* json_strings/json_numbers/json_booleans/json_nulls：标量专用表。

运行：
    python json_to_sqlite.py example.json -o example.sqlite
    python json_to_sqlite.py example.json -o example.sqlite --overwrite

只使用 Python 标准库，兼容 Python 3.8。
"""

import argparse
import codecs
import hashlib
import json
import math
import re
import sqlite3
import sys
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional, Tuple


NUMBER_RE = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")


SCHEMA_SQL = r"""
PRAGMA foreign_keys = ON;

CREATE TABLE json_documents (
    document_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    source_size INTEGER NOT NULL,
    source_sha256 TEXT NOT NULL,
    encoding_name TEXT NOT NULL,
    has_utf8_bom INTEGER NOT NULL CHECK (has_utf8_bom IN (0, 1)),
    leading_whitespace TEXT NOT NULL,
    root_node_id INTEGER,
    trailing_whitespace TEXT NOT NULL,
    FOREIGN KEY (root_node_id) REFERENCES json_nodes(node_id)
);

-- 公共节点只保存类型；具体内容必须存在于对应的专用表。
CREATE TABLE json_nodes (
    node_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    node_type TEXT NOT NULL CHECK (
        node_type IN ('object','array','string','number','boolean','null')
    ),
    FOREIGN KEY (document_id) REFERENCES json_documents(document_id) ON DELETE CASCADE
);

CREATE TABLE json_objects (
    node_id INTEGER PRIMARY KEY,
    -- 仅空对象需要，例如 {   } 中的三个空格。
    empty_inner_whitespace TEXT,
    FOREIGN KEY (node_id) REFERENCES json_nodes(node_id) ON DELETE CASCADE
);

CREATE TABLE json_arrays (
    node_id INTEGER PRIMARY KEY,
    empty_inner_whitespace TEXT,
    FOREIGN KEY (node_id) REFERENCES json_nodes(node_id) ON DELETE CASCADE
);

CREATE TABLE json_object_members (
    object_node_id INTEGER NOT NULL,
    member_index INTEGER NOT NULL,
    leading_whitespace TEXT NOT NULL,
    -- key_text 便于查询；key_lexeme 保留引号与原始转义。
    key_text TEXT NOT NULL,
    key_lexeme TEXT NOT NULL,
    before_colon_whitespace TEXT NOT NULL,
    after_colon_whitespace TEXT NOT NULL,
    -- 若值是字典，该 ID 同时对应 json_objects 中的一行。
    value_node_id INTEGER NOT NULL,
    after_value_whitespace TEXT NOT NULL,
    has_comma INTEGER NOT NULL CHECK (has_comma IN (0, 1)),
    PRIMARY KEY (object_node_id, member_index),
    FOREIGN KEY (object_node_id) REFERENCES json_objects(node_id) ON DELETE CASCADE,
    FOREIGN KEY (value_node_id) REFERENCES json_nodes(node_id)
);

CREATE TABLE json_array_items (
    array_node_id INTEGER NOT NULL,
    item_index INTEGER NOT NULL,
    leading_whitespace TEXT NOT NULL,
    value_node_id INTEGER NOT NULL,
    after_value_whitespace TEXT NOT NULL,
    has_comma INTEGER NOT NULL CHECK (has_comma IN (0, 1)),
    PRIMARY KEY (array_node_id, item_index),
    FOREIGN KEY (array_node_id) REFERENCES json_arrays(node_id) ON DELETE CASCADE,
    FOREIGN KEY (value_node_id) REFERENCES json_nodes(node_id)
);

CREATE TABLE json_strings (
    node_id INTEGER PRIMARY KEY,
    decoded_value TEXT NOT NULL,
    -- 为区分 "中" 与 "\\u4e2d"，精确恢复时必须保留单个字符串词法。
    source_lexeme TEXT NOT NULL,
    FOREIGN KEY (node_id) REFERENCES json_nodes(node_id) ON DELETE CASCADE
);

CREATE TABLE json_numbers (
    node_id INTEGER PRIMARY KEY,
    source_lexeme TEXT NOT NULL,
    is_integer INTEGER NOT NULL CHECK (is_integer IN (0, 1)),
    -- 便于 SQL 运算；超出 64 位或精度时仍由 source_lexeme 无损保留。
    integer_value INTEGER,
    real_value REAL,
    FOREIGN KEY (node_id) REFERENCES json_nodes(node_id) ON DELETE CASCADE
);

CREATE TABLE json_booleans (
    node_id INTEGER PRIMARY KEY,
    boolean_value INTEGER NOT NULL CHECK (boolean_value IN (0, 1)),
    FOREIGN KEY (node_id) REFERENCES json_nodes(node_id) ON DELETE CASCADE
);

CREATE TABLE json_nulls (
    node_id INTEGER PRIMARY KEY,
    FOREIGN KEY (node_id) REFERENCES json_nodes(node_id) ON DELETE CASCADE
);

CREATE INDEX idx_nodes_document_type ON json_nodes(document_id, node_type);
CREATE INDEX idx_members_key ON json_object_members(key_text);
CREATE INDEX idx_members_value ON json_object_members(value_node_id);
CREATE INDEX idx_items_value ON json_array_items(value_node_id);
"""


def digest(data: bytes) -> str:
    """计算任务唯一验收标准 SHA-256。"""
    return hashlib.sha256(data).hexdigest()


def read_source(path: Path) -> Tuple[bytes, str, bool]:
    """从 bytes 解码，避免 read_text 在不同系统上转换 CRLF/LF。"""
    source = path.read_bytes()
    has_bom = source.startswith(codecs.BOM_UTF8)
    body = source[len(codecs.BOM_UTF8):] if has_bom else source
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("输入文件不是有效 UTF-8：{}".format(exc)) from exc
    return source, text, has_bom


class LosslessParser:
    """递归下降解析器：看到对象/数组时继续解析其内部值。"""

    def __init__(self, text: str, db: sqlite3.Connection, document_id: int):
        self.text = text
        self.db = db
        self.document_id = document_id
        self.pos = 0

    def fail(self, message: str) -> ValueError:
        nearby = self.text[max(0, self.pos-20):self.pos+20]
        nearby = nearby.replace("\r", "\\r").replace("\n", "\\n")
        return ValueError("字符 {} 附近：{}；{!r}".format(self.pos, message, nearby))

    def whitespace(self) -> str:
        """JSON 只允许空格、Tab、CR、LF 四种空白。"""
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] in " \t\r\n":
            self.pos += 1
        return self.text[start:self.pos]

    def expect(self, token: str) -> None:
        if not self.text.startswith(token, self.pos):
            raise self.fail("应出现 {!r}".format(token))
        self.pos += len(token)

    def node(self, kind: str) -> int:
        cur = self.db.execute(
            "INSERT INTO json_nodes(document_id,node_type) VALUES(?,?)",
            (self.document_id, kind),
        )
        return int(cur.lastrowid)

    def document(self) -> Tuple[str, int, str]:
        leading = self.whitespace()
        if self.pos == len(self.text):
            raise self.fail("文档只有空白，没有 JSON 值")
        root = self.value()
        trailing = self.whitespace()
        if self.pos != len(self.text):
            raise self.fail("根值之后仍有非空白内容")
        return leading, root, trailing

    def value(self) -> int:
        if self.pos >= len(self.text):
            raise self.fail("意外到达文件末尾")
        ch = self.text[self.pos]
        if ch == "{": return self.object()
        if ch == "[": return self.array()
        if ch == '"': return self.string_value()
        if ch == "t": return self.boolean(True)
        if ch == "f": return self.boolean(False)
        if ch == "n": return self.null()
        if ch == "-" or ch.isdigit(): return self.number()
        raise self.fail("无法识别值起始字符 {!r}".format(ch))

    def string_token(self) -> Tuple[str, str]:
        """返回（解码值，带双引号的精确源词法）。"""
        if self.pos >= len(self.text) or self.text[self.pos] != '"':
            raise self.fail("字符串应以双引号开始")
        start = self.pos
        self.pos += 1
        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch == '"':
                self.pos += 1
                lexeme = self.text[start:self.pos]
                try:
                    return json.loads(lexeme), lexeme
                except json.JSONDecodeError as exc:
                    raise self.fail("字符串转义无效：{}".format(exc)) from exc
            if ch == "\\":
                self.pos += 2
            else:
                if ord(ch) < 0x20:
                    raise self.fail("字符串含未转义控制字符")
                self.pos += 1
        raise self.fail("字符串没有结束双引号")

    def string_value(self) -> int:
        decoded, lexeme = self.string_token()
        node_id = self.node("string")
        self.db.execute(
            "INSERT INTO json_strings VALUES(?,?,?)", (node_id, decoded, lexeme)
        )
        return node_id

    def number(self) -> int:
        match = NUMBER_RE.match(self.text, self.pos)
        if not match:
            raise self.fail("数字格式无效")
        lexeme = match.group(0)
        self.pos = match.end()
        is_int = "." not in lexeme and "e" not in lexeme.lower()
        integer_value = None
        real_value = None
        if is_int:
            value = int(lexeme)
            if -(2**63) <= value <= 2**63-1:
                integer_value = value
        else:
            value = float(lexeme)
            if math.isfinite(value):
                real_value = value
        node_id = self.node("number")
        self.db.execute(
            "INSERT INTO json_numbers VALUES(?,?,?,?,?)",
            (node_id, lexeme, int(is_int), integer_value, real_value),
        )
        return node_id

    def boolean(self, value: bool) -> int:
        self.expect("true" if value else "false")
        node_id = self.node("boolean")
        self.db.execute("INSERT INTO json_booleans VALUES(?,?)", (node_id, int(value)))
        return node_id

    def null(self) -> int:
        self.expect("null")
        node_id = self.node("null")
        self.db.execute("INSERT INTO json_nulls VALUES(?)", (node_id,))
        return node_id

    def object(self) -> int:
        self.expect("{")
        node_id = self.node("object")
        self.db.execute("INSERT INTO json_objects VALUES(?,NULL)", (node_id,))
        leading = self.whitespace()
        if self.pos < len(self.text) and self.text[self.pos] == "}":
            self.pos += 1
            self.db.execute(
                "UPDATE json_objects SET empty_inner_whitespace=? WHERE node_id=?",
                (leading, node_id),
            )
            return node_id

        index = 0
        while True:
            key_text, key_lexeme = self.string_token()
            before_colon = self.whitespace()
            self.expect(":")
            after_colon = self.whitespace()
            value_id = self.value()
            after_value = self.whitespace()
            if self.pos >= len(self.text):
                raise self.fail("对象没有结束右大括号")
            ch = self.text[self.pos]
            if ch == ",":
                comma = 1
                self.pos += 1
            elif ch == "}":
                comma = 0
                self.pos += 1
            else:
                raise self.fail("对象成员后应为逗号或右大括号")
            self.db.execute(
                "INSERT INTO json_object_members VALUES(?,?,?,?,?,?,?,?,?,?)",
                (node_id,index,leading,key_text,key_lexeme,before_colon,
                 after_colon,value_id,after_value,comma),
            )
            index += 1
            if not comma:
                return node_id
            leading = self.whitespace()
            if self.pos < len(self.text) and self.text[self.pos] == "}":
                raise self.fail("对象末尾不允许多余逗号")

    def array(self) -> int:
        self.expect("[")
        node_id = self.node("array")
        self.db.execute("INSERT INTO json_arrays VALUES(?,NULL)", (node_id,))
        leading = self.whitespace()
        if self.pos < len(self.text) and self.text[self.pos] == "]":
            self.pos += 1
            self.db.execute(
                "UPDATE json_arrays SET empty_inner_whitespace=? WHERE node_id=?",
                (leading, node_id),
            )
            return node_id

        index = 0
        while True:
            value_id = self.value()
            after_value = self.whitespace()
            if self.pos >= len(self.text):
                raise self.fail("数组没有结束右方括号")
            ch = self.text[self.pos]
            if ch == ",":
                comma = 1
                self.pos += 1
            elif ch == "]":
                comma = 0
                self.pos += 1
            else:
                raise self.fail("数组元素后应为逗号或右方括号")
            self.db.execute(
                "INSERT INTO json_array_items VALUES(?,?,?,?,?,?)",
                (node_id,index,leading,value_id,after_value,comma),
            )
            index += 1
            if not comma:
                return node_id
            leading = self.whitespace()
            if self.pos < len(self.text) and self.text[self.pos] == "]":
                raise self.fail("数组末尾不允许多余逗号")


def create_database(source_path: Path, database_path: Path, overwrite=False) -> Dict[str, object]:
    """完整解析 JSON，并在一个事务中写入数据库。"""
    source_path = source_path.resolve()
    database_path = database_path.resolve()
    if not source_path.is_file():
        raise FileNotFoundError("找不到输入 JSON：{}".format(source_path))
    if source_path == database_path:
        raise ValueError("输入与输出不能是同一文件")
    if database_path.exists():
        if not overwrite:
            raise FileExistsError("数据库已存在；请添加 --overwrite：{}".format(database_path))
        database_path.unlink()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    source, text, has_bom = read_source(source_path)
    db = None
    try:
        db = sqlite3.connect(str(database_path))
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript(SCHEMA_SQL)
        with db:
            cur = db.execute(
                "INSERT INTO json_documents VALUES(NULL,?,?,?,?,?,?,NULL,?)",
                (source_path.name,len(source),digest(source),"utf-8",int(has_bom),"",""),
            )
            document_id = int(cur.lastrowid)
            leading, root_id, trailing = LosslessParser(text, db, document_id).document()
            db.execute(
                "UPDATE json_documents SET leading_whitespace=?,root_node_id=?,"
                "trailing_whitespace=? WHERE document_id=?",
                (leading,root_id,trailing,document_id),
            )
        counts = dict(db.execute(
            "SELECT node_type,COUNT(*) FROM json_nodes GROUP BY node_type"
        ).fetchall())
        return {"document_id":document_id,"sha256":digest(source),
                "bytes":len(source),"counts":counts}
    except Exception:
        if db is not None:
            db.close()
            db = None
        if database_path.exists():
            database_path.unlink()
        raise
    finally:
        if db is not None:
            db.close()


class DatabaseRenderer:
    """从关系表递归重建节点；lru_cache 避免重复查询同一节点。"""
    def __init__(self, db: sqlite3.Connection, document_id: int):
        self.db = db
        self.document_id = document_id

    @lru_cache(maxsize=None)
    def render(self, node_id: int) -> str:
        row = self.db.execute(
            "SELECT node_type FROM json_nodes WHERE node_id=? AND document_id=?",
            (node_id,self.document_id),
        ).fetchone()
        if row is None:
            raise ValueError("找不到节点 {}".format(node_id))
        kind = row[0]
        if kind == "object": return self.object(node_id)
        if kind == "array": return self.array(node_id)
        if kind == "string":
            return self.required("SELECT source_lexeme FROM json_strings WHERE node_id=?", node_id)[0]
        if kind == "number":
            return self.required("SELECT source_lexeme FROM json_numbers WHERE node_id=?", node_id)[0]
        if kind == "boolean":
            return "true" if self.required("SELECT boolean_value FROM json_booleans WHERE node_id=?", node_id)[0] else "false"
        if kind == "null":
            self.required("SELECT node_id FROM json_nulls WHERE node_id=?", node_id)
            return "null"
        raise ValueError("未知节点类型 {}".format(kind))

    def required(self, sql: str, node_id: int) -> sqlite3.Row:
        row = self.db.execute(sql,(node_id,)).fetchone()
        if row is None:
            raise ValueError("节点 {} 缺少专用表记录".format(node_id))
        return row

    def object(self, node_id: int) -> str:
        inner = self.required(
            "SELECT empty_inner_whitespace FROM json_objects WHERE node_id=?", node_id
        )[0]
        rows = self.db.execute(
            "SELECT * FROM json_object_members WHERE object_node_id=? ORDER BY member_index",
            (node_id,),
        ).fetchall()
        if not rows:
            if inner is None: raise ValueError("空对象 {} 缺少空白记录".format(node_id))
            return "{" + inner + "}"
        parts = ["{"]
        for expected,row in enumerate(rows):
            if row["member_index"] != expected:
                raise ValueError("对象 {} 的成员序号不连续".format(node_id))
            parts.extend((row["leading_whitespace"],row["key_lexeme"],
                          row["before_colon_whitespace"],":",row["after_colon_whitespace"],
                          self.render(row["value_node_id"]),row["after_value_whitespace"]))
            if row["has_comma"]: parts.append(",")
            elif expected != len(rows)-1: raise ValueError("对象中间成员缺少逗号")
        if rows[-1]["has_comma"]: raise ValueError("对象末成员不应有逗号")
        parts.append("}")
        return "".join(parts)

    def array(self, node_id: int) -> str:
        inner = self.required(
            "SELECT empty_inner_whitespace FROM json_arrays WHERE node_id=?", node_id
        )[0]
        rows = self.db.execute(
            "SELECT * FROM json_array_items WHERE array_node_id=? ORDER BY item_index",
            (node_id,),
        ).fetchall()
        if not rows:
            if inner is None: raise ValueError("空数组 {} 缺少空白记录".format(node_id))
            return "[" + inner + "]"
        parts = ["["]
        for expected,row in enumerate(rows):
            if row["item_index"] != expected:
                raise ValueError("数组 {} 的元素序号不连续".format(node_id))
            parts.extend((row["leading_whitespace"],self.render(row["value_node_id"]),
                          row["after_value_whitespace"]))
            if row["has_comma"]: parts.append(",")
            elif expected != len(rows)-1: raise ValueError("数组中间元素缺少逗号")
        if rows[-1]["has_comma"]: raise ValueError("数组末元素不应有逗号")
        parts.append("]")
        return "".join(parts)


def restore_database(database_path: Path, output_path: Path, overwrite=False) -> Dict[str, object]:
    """恢复 JSON；哈希或字节数不一致时拒绝写出。"""
    database_path = database_path.resolve()
    output_path = output_path.resolve()
    if not database_path.is_file():
        raise FileNotFoundError("找不到数据库：{}".format(database_path))
    if database_path == output_path:
        raise ValueError("输入数据库和输出 JSON 不能是同一个文件")
    if output_path.exists() and not overwrite:
        raise FileExistsError("输出已存在；请添加 --overwrite：{}".format(output_path))
    db = sqlite3.connect(str(database_path))
    db.row_factory = sqlite3.Row
    try:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("SQLite 完整性检查失败")
        fk_errors = db.execute("PRAGMA foreign_key_check").fetchall()
        if fk_errors:
            raise ValueError("SQLite 外键检查失败：{}".format(fk_errors))
        docs = db.execute("SELECT * FROM json_documents ORDER BY document_id").fetchall()
        if len(docs) != 1:
            raise ValueError("数据库必须且只能包含一个 JSON 文档，实际为 {}".format(len(docs)))
        doc = docs[0]
        if doc["root_node_id"] is None:
            raise ValueError("文档根节点为空")
        text = (doc["leading_whitespace"] +
                DatabaseRenderer(db,doc["document_id"]).render(doc["root_node_id"]) +
                doc["trailing_whitespace"])
        data = text.encode("utf-8")
        if doc["has_utf8_bom"]:
            data = codecs.BOM_UTF8 + data
        actual = digest(data)
        if actual != doc["source_sha256"] or len(data) != doc["source_size"]:
            raise ValueError("恢复校验失败：期望 {} / {} 字节，实际 {} / {} 字节".format(
                doc["source_sha256"],doc["source_size"],actual,len(data)))
        output_path.parent.mkdir(parents=True,exist_ok=True)
        output_path.write_bytes(data)
        return {"sha256":actual,"bytes":len(data),"source_name":doc["source_name"]}
    finally:
        db.close()


def parser() -> argparse.ArgumentParser:
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description="把 JSON 无损关系化到 SQLite。")
    p.add_argument("input_json",nargs="?",type=Path,default=here/"example.json")
    p.add_argument("-o","--output",type=Path,help="默认生成同名 .sqlite 文件")
    p.add_argument("--overwrite",action="store_true",help="允许重建已有数据库")
    return p


def main() -> int:
    args = parser().parse_args()
    output = args.output or args.input_json.with_suffix(".sqlite")
    try:
        result = create_database(args.input_json,output,args.overwrite)
    except (OSError,ValueError,json.JSONDecodeError,sqlite3.Error) as exc:
        print("转换失败：{}".format(exc),file=sys.stderr)
        return 1
    print("JSON -> SQLite 完成：{}".format(output.resolve()))
    print("源文件 SHA-256：{}".format(result["sha256"]))
    print("源文件字节数：{}".format(result["bytes"]))
    print("节点分类统计：{}".format(result["counts"]))
    print("恢复：python sqlite_to_json.py \"{}\" -o restored.json".format(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())