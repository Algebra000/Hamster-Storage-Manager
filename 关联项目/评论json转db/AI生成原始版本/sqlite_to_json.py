#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把无损关系化 SQLite 恢复为与输入逐字节相同的 JSON。

使用方法：
    python sqlite_to_json.py example.sqlite -o restored.json

真正的重建逻辑位于 json_to_sqlite.py 的 ``restore_database``，两个命令共用
同一套表结构定义。恢复程序会先检查 SQLite 完整性和外键，再计算输出 SHA-256；
哈希或字节数与源文件记录不一致时会拒绝写出文件。
"""

import argparse
import sqlite3
import sys
from pathlib import Path

from json_to_sqlite import restore_database


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="从无损关系化 SQLite 恢复哈希完全一致的 JSON。"
    )
    parser.add_argument("database", type=Path, help="输入 SQLite 数据库")
    parser.add_argument("-o", "--output", type=Path, help="输出 JSON 路径")
    parser.add_argument(
        "--overwrite", action="store_true", help="允许覆盖已存在的输出 JSON"
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = args.output or args.database.with_name(
        args.database.stem + ".restored.json"
    )
    try:
        result = restore_database(args.database, output, args.overwrite)
    except (OSError, ValueError, sqlite3.Error) as exc:
        print("恢复失败：{}".format(exc), file=sys.stderr)
        return 1

    print("SQLite -> JSON 完成：{}".format(output.resolve()))
    print("恢复文件 SHA-256：{}".format(result["sha256"]))
    print("恢复文件字节数：{}".format(result["bytes"]))
    print("哈希校验：与原 JSON 完全一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())