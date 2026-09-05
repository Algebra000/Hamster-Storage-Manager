#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标准层级版 SQLite→JSON 恢复程序。

使用：
    python sqlite_to_json.py example_std.sqlite -o restored.json

恢复后会计算只关心键和值的语义 SHA-256，并与数据库记录比较。这个标准版
不要求输出 JSON 的空白、换行和源文件哈希相同。
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from json_to_sqlite import restore_database


def main() -> int:
    parser = argparse.ArgumentParser(description="恢复标准层级版 SQLite 中的 JSON")
    parser.add_argument("database",type=Path)
    parser.add_argument("-o","--output",type=Path)
    parser.add_argument("--overwrite",action="store_true")
    args = parser.parse_args()
    output = args.output or args.database.with_name(args.database.stem+".restored.json")
    try:
        result = restore_database(args.database,output,args.overwrite)
    except (OSError,ValueError,TypeError,json.JSONDecodeError,sqlite3.Error) as exc:
        print("恢复失败：{}".format(exc),file=sys.stderr)
        return 1
    print("标准版 SQLite -> JSON 完成：{}".format(output.resolve()))
    print("顶层字典：{} 条".format(result["items"]))
    print("语义 SHA-256：{}".format(result["fingerprint"]))
    print("键和值校验：完全一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())