# classify_shower_video.py - 视频播放、弹幕、观看记录及评论功能。
import os
import html
import asyncio
import datetime
import json
import re
import sqlite3
import struct
import subprocess
from collections import OrderedDict
from bisect import bisect_left
from pathlib import Path
from typing import Callable, Dict, Optional
import time
import uuid
import platform
from http.client import HTTPException
import shutil
import tarfile
import tempfile
import zipfile
from urllib.request import Request, urlopen
from typing import List, Dict, Protocol

from video_timestamp_repair import MP4StreamTimestampRepair, MP4TimestampMetadata, run_in_thread
#from classify_shower_back import DatabaseManager
from classify_shower_db_manager import DatabaseManager

# 导入文件类型列表
from config.file_type import video_type_list

COMMENT_DATABASE_SCHEMA_VERSION = "v1.1"
REPLY_PAGE_SIZE = 5
COMMENT_REPLY_CONTROL_FIELDS = (
    "max_line", "location", "translation_switch", "support_share",
)
COMMENT_SOURCE_INFO_EDITABLE_KEYS = {"src-name"}
COMMENT_ENTITY_JSON_COLUMNS = {
    "member": {
        "senior", "level_info", "pendant", "nameplate", "official_verify",
        "vip", "fans_detail", "user_sailing", "user_sailing_v2",
        "nft_interaction", "avatar_item",
    },
    "content": {
        "members", "jump_url", "pictures", "emote",
        "at_name_to_mid", "at_name_to_mid_str",
    },
}
COMMENT_CONFIG_DEFAULTS = {
    "page-size": 20,
    "sort-by": "time",
    "mark-deleted": False,
    "only-deleted": False,
    "only-vip": False,
    "word-filter-enabled": False,
    "word-count": 0,
    "word-direction": "above",
}


def _open_comment_database_readonly(database_path):
    r"""以只查询模式打开本地或 UNC 路径上的 SQLite 评论数据库。

    不能在这里使用 ``Path.as_uri() + '?mode=ro'``：UNC 路径会被转换为
    ``file://server/share/...``，而 Windows 自带的 SQLite 通常未启用
    SQLITE_ALLOW_URI_AUTHORITY，会报 ``invalid uri authority``。直接传入原始
    ``\\server\share\...`` 路径可正常访问，再用 query_only 禁止 SQL 写操作。
    """
    database_path = os.fspath(database_path)
    if not os.path.isfile(database_path):
        raise FileNotFoundError(f"评论数据库不存在: {database_path}")
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA query_only=ON")
    return connection

#[DEBUG-START] 性能调试代码，release时删掉
# 临时评论性能诊断开关；排查结束后可关闭。
COMMENT_PERF_DEBUG = True



class CommentPerformanceTrace:
    def __init__(self, request_id):
        self.request_id = request_id
        self.started = self.previous = time.perf_counter()
        self.records = []

    def step(self, label, **details):
        if not COMMENT_PERF_DEBUG:
            return
        now = time.perf_counter()
        self.records.append((label, (now - self.previous) * 1000,
                             (now - self.started) * 1000, details))
        self.previous = now

    def report(self):
        # 请求结束后统一输出，避免每阶段终端打印影响后续阶段计时。
        for label, elapsed, total, details in self.records:
            print(f"[评论性能][{self.request_id}] {label}: {elapsed:.2f} ms "
                  f"(累计 {total:.2f} ms) {details}")
#[DEBUG-END]

#[DEBUG-START] 视频跳转耗时诊断，release时删掉
from contextvars import ContextVar
VIDEO_SEEK_TRACE = ContextVar("video_seek_trace", default=None)

class VideoSeekPerformanceTrace:
    def __init__(self, request_id):
        self.request_id = request_id
        self.started = self.previous = time.perf_counter()

    def step(self, label, **details):
        now = time.perf_counter()
        elapsed = (now - self.previous) * 1000
        total = (now - self.started) * 1000
        self.previous = now
        print(f"[视频跳转耗时][{self.request_id}] {label}: {elapsed:.2f} ms "
              f"(后端累计 {total:.2f} ms) {details}")
#[DEBUG-END]

class CommentPageConnectionManager:
    """缓存最近一个来源的只读连接，以及最近一组筛选条件的分页准备结果。"""

    def __init__(self, idle_timeout=60.0):
        self.idle_timeout = max(0.0, float(idle_timeout))
        self.database_path = None
        self.connection = None
        self.idle_handle = None
        self.query_cache = None

    @staticmethod
    def normalize_path(database_path):
        return os.path.normcase(os.path.abspath(os.path.normpath(
            os.fspath(database_path)
        )))

    def acquire(self, database_path):
        normalized_path = self.normalize_path(database_path)
        if self.connection is not None \
                and normalized_path == self.database_path:
            self.touch(self.connection)
            return self.connection

        # 切换评论来源时先释放上一个数据库，再按原有方式检查并打开新库。
        self.close()
        connection = _open_comment_database_readonly(normalized_path)
        self.database_path = normalized_path
        self.connection = connection
        self.touch(connection)
        return connection

    def touch(self, connection):
        if connection is not self.connection:
            return
        if self.idle_handle is not None:
            self.idle_handle.cancel()
            self.idle_handle = None
        if self.idle_timeout <= 0:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        self.idle_handle = loop.call_later(self.idle_timeout, self.close)

    def discard(self, connection):
        """查询异常时仅丢弃发生异常的当前缓存连接。"""
        if connection is self.connection:
            self.close()

    def close(self):
        self.query_cache = None
        if self.idle_handle is not None:
            self.idle_handle.cancel()
            self.idle_handle = None
        connection = self.connection
        self.connection = None
        self.database_path = None
        if connection is not None:
            try:
                connection.close()
            except sqlite3.Error as error:
                print(f"[分类展示模块] 关闭评论页面数据库连接失败: {error}")


def _comment_table_columns(connection, table_name):
    return [
        row[1]
        for row in connection.execute(f'PRAGMA table_info("{table_name}")')
    ]


def _decode_comment_entity_value(table_name, column_name, value):
    """恢复 v1.1 数据库里以 JSON 文本保存的 member/content 结构字段。"""
    if value is None or column_name not in COMMENT_ENTITY_JSON_COLUMNS[table_name]:
        return value
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _decode_comment_reply_control(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            value = {}
    if not isinstance(value, dict):
        return {}
    return {
        key: value[key]
        for key in COMMENT_REPLY_CONTROL_FIELDS
        if key in value
    }


def _comment_chunks(values, size=800):
    for start in range(0, len(values), size):
        yield values[start:start + size]


def _load_comment_entity_rows(connection, table_name, parent_ids):
    """只加载当前页主评论及其回复引用的 member/content，控制内存占用。"""
    result = {}
    parent_ids = sorted(set(parent_ids))
    for group in _comment_chunks(parent_ids):
        placeholders = ",".join("?" for _ in group)
        query = f'SELECT * FROM "{table_name}" WHERE parent IN ({placeholders})'
        for row in connection.execute(query, group):
            parent = int(row["parent"])
            entity = {}
            for column_name in row.keys():
                if column_name in {"parent", "_comment_kind", "_data_hash"}:
                    continue
                value = row[column_name]
                if value is None:
                    continue
                entity[column_name] = _decode_comment_entity_value(
                    table_name, column_name, value
                )
            result[parent] = entity
    return result


def _comment_rows_to_dicts(rows, members, contents):
    result = []
    for row in rows:
        comment = {}
        for column_name in row.keys():
            if column_name.startswith("_") or column_name in {"member", "content"}:
                continue
            value = row[column_name]
            if value is None:
                continue
            if column_name == "reply_control":
                value = _decode_comment_reply_control(value)
            comment[column_name] = value
        rpid = int(row["rpid"])
        comment["member"] = members.get(rpid, {})
        comment["content"] = contents.get(rpid, {})
        result.append(comment)
    return result


def _comment_integer_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _find_comment_main_rpid(reply, main_ids, replies_by_rpid):
    root = _comment_integer_id(reply.get("root_str") or reply.get("root"))
    if root in main_ids:
        return root
    current = _comment_integer_id(reply.get("parent_str") or reply.get("parent"))
    visited = set()
    while current is not None and current not in visited:
        if current in main_ids:
            return current
        visited.add(current)
        parent_reply = replies_by_rpid.get(current)
        if parent_reply is None:
            break
        current = _comment_integer_id(
            parent_reply.get("parent_str") or parent_reply.get("parent")
        )
    return None


def _select_comment_replies(connection, main_ids):
    """加载当前页顶层评论关联的全部回复。"""
    result = {}
    main_ids = sorted(set(main_ids))
    reply_columns = set(_comment_table_columns(connection, "reply"))
    if not main_ids or not {"root", "parent"}.issubset(reply_columns):
        return []
    for group in _comment_chunks(main_ids, 400):
        placeholders = ",".join("?" for _ in group)
        query = (
            'SELECT * FROM "reply" '
            f'WHERE root IN ({placeholders}) OR parent IN ({placeholders})'
        )
        for row in connection.execute(query, list(group) + list(group)):
            result[int(row["rpid"])] = row
    return sorted(
        result.values(),
        key=lambda row: (
            _comment_integer_id(row["ctime"]) or 0,
            int(row["rpid"]),
        ),
    )


def _comment_vip_json(value):
    if not value:
        return 0
    try:
        value = json.loads(value) if isinstance(value, str) else value
    except (TypeError, json.JSONDecodeError):
        return 0
    return int(isinstance(value, dict) and value.get("vipStatus") == 1)


def _deleted_comment_candidates(connection, deleted_rpids):
    """从删除 ID 反查回复归属，只读取命中回复的 root/parent。

    保留原筛选语义：顶层评论自身被删除，或者有被删除的回复以它作为
    root/parent 时，都显示该顶层评论。候选中的回复 ID、0 和不存在的 ID
    不会匹配顶层表，不需要额外扫描 main/top 来逐一核实。
    """
    candidates = {int(value) for value in deleted_rpids}
    for group in _comment_chunks(sorted(candidates), 800):
        placeholders = ','.join('?' for _ in group)
        rows = connection.execute(
            'SELECT root,parent FROM reply '
            f'WHERE rpid IN ({placeholders})', group,
        )
        for row in rows:
            for value in row:
                rpid = _comment_integer_id(value)
                if rpid is not None:
                    candidates.add(rpid)
    return candidates


def _build_comment_where(keyword, only_deleted, only_vip,
                         word_filter_enabled, word_count, word_direction,
                         deleted_candidates=None):
    conditions = []
    params = []
    if keyword:
        escaped = str(keyword).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        conditions.append("COALESCE(content.message, '') LIKE ? ESCAPE '\\'")
        params.append(f"%{escaped}%")
    if only_deleted:
        if deleted_candidates is None:
            raise ValueError('删除筛选需要预先查询候选评论 ID')
        # 仅拼接经 int 转换的整数，不包含外部 SQL 文本；避免大删除列表超过
        # SQLite 绑定参数上限。计数和分页复用同一条件，不再逐条回查回复。
        ids = ','.join(str(int(value)) for value in sorted(deleted_candidates))
        conditions.append(f'comment.rpid IN ({ids})' if ids else '0')
    if only_vip:
        conditions.append("cs_is_vip(member.vip) = 1")
    if word_filter_enabled:
        comparator = "<=" if word_direction == "below" else ">="
        conditions.append(f"LENGTH(COALESCE(content.message, '')) {comparator} ?")
        params.append(max(0, int(word_count)))
    return (" WHERE " + " AND ".join(conditions) if conditions else ""), params


def _comment_filter_joins(where_sql):
    """只关联筛选实际使用的表；where_sql 仅来自 _build_comment_where。

    无筛选时的 COUNT 不需要读取正文和用户记录，尤其应避免在 UNC 库上
    对每条评论额外执行两次主键查找。关键词参数独立绑定，不参与此判断。
    """
    joins = []
    if 'content.' in where_sql:
        joins.append('LEFT JOIN content ON content.parent=comment.rpid ')
    if 'member.' in where_sql:
        joins.append('LEFT JOIN member ON member.parent=comment.rpid ')
    return ''.join(joins)


def _select_comment_table_rows(connection, table_name, sort_by, reverse,
                               offset, limit, where_sql, where_params):
    if table_name not in {"top", "main"}:
        raise ValueError("不允许的评论表")
    sort_column = "like" if sort_by == "like" else "ctime"
    direction = "DESC" if reverse else "ASC"
    query = (
        f'SELECT comment.* FROM "{table_name}" AS comment '
        f'{_comment_filter_joins(where_sql)}'
        f'{where_sql} ORDER BY comment."{sort_column}" {direction}, '
        f'comment.rpid {direction} LIMIT ? OFFSET ?'
    )
    return connection.execute(
        query, list(where_params) + [limit, offset]
    ).fetchall()


def _count_comment_table_rows(connection, table_name, where_sql, where_params):
    if table_name not in {"top", "main"}:
        raise ValueError("不允许的评论表")
    query = (
        f'SELECT COUNT(*) FROM "{table_name}" AS comment '
        f'{_comment_filter_joins(where_sql)}'
        f'{where_sql}'
    )
    return int(connection.execute(query, where_params).fetchone()[0])


def load_comment_page_from_database(database_path, sort_by, page, page_size,
                                    keyword="", only_deleted=False,
                                    only_vip=False, word_filter_enabled=False,
                                    word_count=0, word_direction="above",
                                    deleted_rpids=None,
                                    connection_manager=None, perf=None,
                                    deleted_loader=None, query_scope=None):
    """按 top + main 的连续序列筛选并还原一页 v1.1 评论。"""
    sort_by = sort_by if sort_by in {"like", "time"} else "time"
    page_size = min(max(int(page_size), 1), 200)
    requested_page = max(int(page), 1)
    # 直接调用时，删除 ID 的变化也是失效条件；页面请求使用延迟加载器，
    # 让缓存命中时连 deletelist 文件都不必重新打开。
    supplied_deleted = frozenset(int(value) for value in (deleted_rpids or []))
    database_path = os.path.abspath(os.path.normpath(os.fspath(database_path)))
    owns_connection = connection_manager is None
    #[DEBUG-START] 性能调试代码，release时删掉
    reused = (not owns_connection and connection_manager.connection is not None
              and connection_manager.database_path ==
              connection_manager.normalize_path(database_path))
    #[DEBUG-END]
    connection = (
        _open_comment_database_readonly(database_path)
        if owns_connection else connection_manager.acquire(database_path)
    )
    connection.row_factory = sqlite3.Row
    connection.create_function("cs_is_vip", 1, _comment_vip_json)
    # 页码和每页条数不影响候选集合与总数，故不包含在缓存键里。
    query_key = (database_path, query_scope, sort_by, keyword, only_deleted,
                 only_vip, word_filter_enabled, word_count, word_direction,
                 deleted_loader is not None, supplied_deleted)
    cached = connection_manager.query_cache if connection_manager else None
    if cached is not None and cached['key'] != query_key:
        connection_manager.query_cache = None
        cached = None
    #[DEBUG-START] 性能调试代码，release时删掉
    if perf:
        perf.step('获取连接及注册函数', reused=reused, database=database_path,
                  page=requested_page, pageSize=page_size, sortBy=sort_by,
                  keywordEnabled=bool(keyword), onlyDeleted=only_deleted,
                  onlyVip=only_vip, wordFilterEnabled=word_filter_enabled)
    #[DEBUG-END]
    try:
        if cached is None:
            deleted_rpids = (
                {int(value) for value in deleted_loader()}
                if deleted_loader is not None else set(supplied_deleted)
            )
            #[DEBUG-START] 性能调试代码，release时删掉
            if perf:
                perf.step('加载删除列表（准备缓存未命中）', rows=len(deleted_rpids))
            #[DEBUG-END]
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            required = {"_metadata", "main", "reply", "member", "content"}
            missing = required - tables
            if missing:
                raise ValueError("数据库缺少表：" + ", ".join(sorted(missing)))
            metadata = dict(connection.execute(
                "SELECT metadata_key,metadata_value FROM _metadata"
            ))
            if metadata.get("schema_version") != COMMENT_DATABASE_SCHEMA_VERSION:
                raise ValueError(
                    f"评论数据库版本 {metadata.get('schema_version')!r}，"
                    f"当前只支持 {COMMENT_DATABASE_SCHEMA_VERSION!r}"
                )

            #[DEBUG-START] 性能调试代码，release时删掉
            if perf:
                perf.step('读取表结构及元数据')
            #[DEBUG-END]
            deleted_candidates = (
                _deleted_comment_candidates(connection, deleted_rpids)
                if only_deleted else None
            )
            #[DEBUG-START] 性能调试代码，release时删掉
            if perf and only_deleted:
                perf.step('删除 ID 反查 root/parent', deletedIds=len(deleted_rpids),
                          candidateIds=len(deleted_candidates))
            #[DEBUG-END]
            where_sql, where_params = _build_comment_where(
                keyword, only_deleted, only_vip, word_filter_enabled,
                word_count, word_direction,
                deleted_candidates=deleted_candidates,
            )
            top_count = (
                _count_comment_table_rows(connection, "top", where_sql, where_params)
                if "top" in tables else 0
            )
            #[DEBUG-START] 性能调试代码，release时删掉
            if perf:
                perf.step('top 筛选计数', rows=top_count)
            #[DEBUG-END]
            main_count = _count_comment_table_rows(
                connection, "main", where_sql, where_params
            )
            #[DEBUG-START] 性能调试代码，release时删掉
            if perf:
                perf.step('main 筛选计数', rows=main_count)
            #[DEBUG-END]
            if connection_manager is not None:
                connection_manager.query_cache = {
                    'key': query_key,
                    'deleted_rpids': deleted_rpids,
                    'deleted_candidates': deleted_candidates,
                    'where_sql': where_sql,
                    'where_params': where_params,
                    'top_count': top_count,
                    'main_count': main_count,
                }
        else:
            # 同一浏览会话的分页快照：不访问文件系统、不检查元数据、不重算。
            deleted_rpids = cached['deleted_rpids']
            where_sql, where_params = cached['where_sql'], cached['where_params']
            top_count, main_count = cached['top_count'], cached['main_count']
            #[DEBUG-START] 性能调试代码，release时删掉
            if perf:
                perf.step('复用分页准备缓存（跳过步骤1—5）',
                          deletedIds=len(deleted_rpids),
                          topCount=top_count, mainCount=main_count)
            #[DEBUG-END]
        total_count = top_count + main_count
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        selected_page = min(requested_page, total_pages)
        start = (selected_page - 1) * page_size
        end = min(start + page_size, total_count)

        top_rows = []
        if start < top_count:
            top_limit = max(0, min(end, top_count) - start)
            if top_limit:
                top_rows = _select_comment_table_rows(
                    connection, "top", sort_by, True,
                    start, top_limit, where_sql, where_params,
                )
        #[DEBUG-START] 性能调试代码，release时删掉
        if perf:
            perf.step('top 排序分页查询', rows=len(top_rows))
        #[DEBUG-END]
        main_start = max(start - top_count, 0)
        main_limit = max(0, end - max(start, top_count))
        main_rows = []
        if main_limit:
            main_rows = _select_comment_table_rows(
                connection, "main", sort_by, True,
                main_start, main_limit, where_sql, where_params,
            )

        #[DEBUG-START] 性能调试代码，release时删掉
        if perf:
            perf.step('main 排序分页查询', rows=len(main_rows), offset=main_start)
        #[DEBUG-END]
        parent_ids = [int(row["rpid"]) for row in top_rows + main_rows]
        reply_rows = _select_comment_replies(connection, parent_ids)
        #[DEBUG-START] 性能调试代码，release时删掉
        if perf:
            perf.step('查询本页全部回复并排序', rows=len(reply_rows))
        #[DEBUG-END]
        all_ids = parent_ids + [int(row["rpid"]) for row in reply_rows]
        members = _load_comment_entity_rows(connection, "member", all_ids)
        #[DEBUG-START] 性能调试代码，release时删掉
        if perf:
            perf.step('查询并解析 member', rows=len(members))
        #[DEBUG-END]
        contents = _load_comment_entity_rows(connection, "content", all_ids)
        #[DEBUG-START] 性能调试代码，release时删掉
        if perf:
            perf.step('查询并解析 content', rows=len(contents))
        #[DEBUG-END]
        top_comments = _comment_rows_to_dicts(top_rows, members, contents)
        main_comments = _comment_rows_to_dicts(main_rows, members, contents)
        replies = _comment_rows_to_dicts(reply_rows, members, contents)
        #[DEBUG-START] 性能调试代码，release时删掉
        if perf:
            perf.step('评论与回复字典组装')
        #[DEBUG-END]
        if connection_manager is not None:
            connection_manager.touch(connection)
    except Exception:
        if connection_manager is not None:
            connection_manager.discard(connection)
        raise
    finally:
        if owns_connection:
            connection.close()

    for comment in top_comments:
        comment["is_top"] = True
    top_level = top_comments + main_comments
    main_by_rpid = {int(item["rpid"]): item for item in top_level}
    replies_by_rpid = {int(item["rpid"]): item for item in replies}
    main_ids = set(main_by_rpid)
    for comment in top_level:
        comment["replies"] = []
        comment["_is_deleted"] = int(comment["rpid"]) in deleted_rpids
    for reply in replies:
        reply["_is_deleted"] = int(reply["rpid"]) in deleted_rpids
        owner = _find_comment_main_rpid(reply, main_ids, replies_by_rpid)
        if owner is not None:
            main_by_rpid[owner]["replies"].append(reply)
    #[DEBUG-START] 性能调试代码，release时删掉
    if perf:
        perf.step('归属回复及删除标记', comments=len(top_level), replies=len(replies))
    #[DEBUG-END]
    return {
        "comments": top_level,
        "totalCount": total_count,
        "page": selected_page,
        "requestedPage": requested_page,
        "pageSize": page_size,
        "totalPages": total_pages,
    }


def _comment_file_uri(root, relative_path):
    relative_path = str(relative_path or "").replace("\\", "/").lstrip("./")
    # resource_root 在进入评论渲染链路前已经规范化为绝对路径。这里不能再调用
    # Path.resolve()：对 UNC 路径而言，每个 src 都会触发一次网络文件系统查询。
    # 纯字符串规范化即可生成同样的 file URI，且不会访问磁盘或网络共享。
    absolute_path = os.path.abspath(os.path.normpath(
        os.path.join(os.fspath(root), relative_path)
    ))
    return Path(absolute_path).as_uri()


def remap_url_to_absolute(url, resource_root, basic_resource_folder):
    """把单个评论资源 URL 映射成前端可加载的绝对 file URI。"""
    if not isinstance(url, str):
        return url
    normalized = url.replace("\\", "/")
    for prefix in ("./comment-resource/", "comment-resource/"):
        if normalized.startswith(prefix):
            return _comment_file_uri(
                Path(resource_root) / 'comment-resource',
                normalized[len(prefix):],
            )
    for prefix in ("./bilibili-resource/", "bilibili-resource/"):
        if normalized.startswith(prefix):
            return _comment_file_uri(
                Path(resource_root) / basic_resource_folder,
                normalized[len(prefix):],
            )
    return url


def build_comment_font_style(resource_root, basic_resource_folder):
    """生成放在 CS_COMMENT_HTML 最前方、路径已重映射的字体声明。"""
    harmony_font = remap_url_to_absolute(
        './bilibili-resource/HarmonyOS-Regular-subset1.woff',
        resource_root, basic_resource_folder,
    )
    fans_font = remap_url_to_absolute(
        './bilibili-resource/fans-num.ttf',
        resource_root, basic_resource_folder,
    )
    return f'''<style>
        @font-face {{
            font-family: "HarmonyOS_Regular";
            src: url("{harmony_font}") format("woff");
        }}
        @font-face {{
            font-family: 'fans-num';
            src: url("{fans_font}") format("truetype");
        }}
    </style>'''


def calculate_time_desc(ctime):
    now = datetime.datetime.now().timestamp()
    diff = int(now - ctime)
    if diff < 60:
        return f"{diff}秒前"
    elif diff < 3600:
        return f"{diff // 60}分钟前"
    elif diff < 86400:
        return f"{diff // 3600}小时前"
    else:
        return f"{diff // 86400}天前发布"


css_style_trans_dict = {
    "borderRadius": "border-radius",
    "boxSizing": "box-sizing",
}

def build_avatar_html(avatar_item, base_width, base_height,
                      resource_root, basic_resource_folder):
    if not avatar_item:
        return ""
    
    container_size = avatar_item.get("container_size", {})
    canvas_width = container_size.get("width", 1.8) * base_width
    canvas_height = container_size.get("height", 1.8) * base_height
    
    layers_data = avatar_item.get("layers", [])
    if not layers_data:
        fallback_layers = avatar_item.get("fallback_layers", {})
        layers_data = fallback_layers.get("layers", [])
    
    layers_html = parse_layers(
        layers_data, base_width, base_height,
        resource_root, basic_resource_folder,
    )
    
    return f'<div class="avatar-canvas" style="width: {int(canvas_width)}px; height: {int(canvas_height)}px;">{layers_html}</div>'


def parse_layers(layers_data, base_width, base_height,
                 resource_root, basic_resource_folder):
    if not layers_data:
        return ""

    result = ""
    # 栈式DFS：("layer", layer_dict) 处理图层，("close", None) 闭合div
    stack = []
    for layer in reversed(layers_data):
        stack.append(("layer", layer))

    while stack:
        task_type, task_data = stack.pop()

        if task_type == "close":
            result += '</div>'
            continue

        layer = task_data
        visible = layer.get("visible", False)

        general_spec = layer.get("general_spec", {})
        pos_spec = general_spec.get("pos_spec", {})
        size_spec = general_spec.get("size_spec", {})
        render_spec = general_spec.get("render_spec", {})

        coordinate_pos = pos_spec.get("coordinate_pos", 2)
        axis_x = pos_spec.get("axis_x", 0.9)
        axis_y = pos_spec.get("axis_y", 0.9)
        width = size_spec.get("width", 1) * base_width
        height = size_spec.get("height", 1) * base_height
        opacity = render_spec.get("opacity", 1)

        if coordinate_pos == 1:
            x = int(axis_x * base_width)
            y = int(axis_y * base_height)
        else:
            x = int(axis_x * base_width - width / 2)
            y = int(axis_y * base_height - height / 2)

        if visible:
            layer_style = f"left: {x}px; top: {y}px; width: {int(width)}px; height: {int(height)}px;"
        else:
            layer_style = ""
        if opacity != 1:
            layer_style += f" opacity: {opacity};"

        img_html = ""
        if visible:
            resource = layer.get("resource", {})
            res_type = resource.get("res_type", 0)

            if res_type == 4:
                res_animation = resource.get("res_animation", {})
                webp_src = res_animation.get("webp_src", {})
                remote = webp_src.get("remote", {})
                img_url = remote.get("url", "")
            elif res_type == 3:
                res_image = resource.get("res_image", {})
                image_src = res_image.get("image_src", {})
                src_type = image_src.get("src_type", 1)
                if src_type == 2:
                    local_id = image_src.get("local", 0)
                    img_url = f"./bilibili-resource/res-local{local_id}.png"
                else:
                    remote = image_src.get("remote", {})
                    img_url = remote.get("url", "")
            else:
                img_url = ""

            if img_url:
                img_url = remap_url_to_absolute(
                    img_url, resource_root, basic_resource_folder
                )
                layer_config = layer.get("layer_config", {})
                tags = layer_config.get("tags", {})
                general_cfg = tags.get("GENERAL_CFG", {})
                general_config = general_cfg.get("general_config", {})
                web_css_style = general_config.get("web_css_style", {})

                img_style_parts = [f"width: {int(width)}px; height: {int(height)}px;"]
                for key, value in web_css_style.items():
                    css_key = css_style_trans_dict.get(key, key)
                    img_style_parts.append(f"{css_key}: {value};")
                img_style = "; ".join(img_style_parts)

                img_html = f'<img src="{img_url}" style="{img_style}">'

        sub_layers = layer.get("layers", [])
        if sub_layers:
            # 先压入闭合任务（最后执行），再压入子图层（逆序保证顺序一致）
            stack.append(("close", None))
            for sub_layer in reversed(sub_layers):
                stack.append(("layer", sub_layer))
            result += f'<div class="avatar-layer" style="{layer_style}">{img_html}'
        else:
            result += f'<div class="avatar-layer" style="{layer_style}">{img_html}</div>'

    return result


def render_comment_message(content, resource_root, basic_resource_folder):
    """只扫描原始正文一次；生成的标签不再参与表情、关键词替换。"""
    message = str(content.get("message", "") or "")
    replacements = {}
    for key, data in (content.get("emote", {}) or {}).items():
        if not key:
            continue
        src = remap_url_to_absolute(
            data.get("url", ""), resource_root, basic_resource_folder,
        )
        if not src:
            continue
        size = (data.get("meta", {}) or {}).get("size", 1)
        style = ""
        if size != 1:
            pixels = 25 * int(size)
            style = f' style="max-width: {pixels}px; max-height: {pixels}px;"'
        replacements[key] = (
            f'<img src="{html.escape(src, quote=True)}" '
            f'alt="{html.escape(key, quote=True)}" '
            f'title="{html.escape(str(data.get("text", "")), quote=True)}"{style}>'
        )

    for key, data in (content.get("jump_url", {}) or {}).items():
        if not key:
            continue
        icon = remap_url_to_absolute(
            data.get("prefix_icon", ""), resource_root, basic_resource_folder,
        )
        title = data.get("title", "")
        position = data.get("icon_position", 0)
        # 保留原来的图标、标题以及前置/后置图标显示条件。
        if not icon or not title or position not in (0, 1):
            continue
        href = str(data.get("pc_url", "") or key)
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("BV"):
            href = "https://www.bilibili.com/video/" + href
        title_html = html.escape(str(title))
        icon_src = html.escape(icon, quote=True)
        if position == 0:
            body = f'<img src="{icon_src}" alt="链接" width="18" height="18">{title_html}'
        else:
            body = (
                f'{title_html}<img src="{icon_src}" alt="链接" '
                'style="max-width: 18px; max-height: 18px; margin: 0px;">'
            )
        replacements[key] = (
            f'<a href="{html.escape(href, quote=True)}" '
            f'class="cs-cmt-v1-jump-link" target="_blank">{body}</a>'
        )

    if not replacements:
        return html.escape(message)

    # 同一位置优先最长匹配：完整链接优先于其中的 share 等短关键词。
    # finditer 始终读取原始 message，绝不会扫描刚生成的 href/src/title。
    pattern = re.compile("|".join(
        re.escape(key) for key in sorted(replacements, key=len, reverse=True)
    ))
    parts = []
    cursor = 0
    for match in pattern.finditer(message):
        parts.append(html.escape(message[cursor:match.start()]))
        parts.append(replacements[match.group(0)])
        cursor = match.end()
    parts.append(html.escape(message[cursor:]))
    return "".join(parts)


def comment_to_comment_html(comment, resource_root, basic_resource_folder,
                            mark_deleted=False):
    '''
    将一条评论转换为对应的HTML字符串
    '''
    comment_id = comment.get("rpid", 0)
    deleted_comment_class = (
        " cs-cmt-v1-deleted-data"
        if mark_deleted and comment.get("_is_deleted") else ""
    )
    member = comment.get("member", {})
    content = comment.get("content", {})
    reply_control = comment.get("reply_control", {})
    replies = comment.get("replies", []) or []

    username = member.get("uname", "匿名用户")
    level = member.get("level_info", {}).get("current_level", 0)
    vip_status = member.get("vip", {}).get("vipStatus", 0)
    is_senior_member = member.get("is_senior_member", 0)
    avatar_item = member.get("avatar_item", {})

    is_vip = vip_status == 1
    username_class = (
        "cs-cmt-v1-username cs-cmt-v1-vip-username"
        if is_vip else "cs-cmt-v1-username"
    )
    avatar_html = build_avatar_html(
        avatar_item, 48, 48, resource_root, basic_resource_folder
    )

    level_svg = "level_h.svg" if (level == 6 and is_senior_member == 1) else f"level_{level}.svg"
    level_src = remap_url_to_absolute(
        f'./bilibili-resource/{level_svg}',
        resource_root, basic_resource_folder,
    )
    like_icon_src = remap_url_to_absolute(
        './bilibili-resource/like.svg',
        resource_root, basic_resource_folder,
    )
    dislike_icon_src = remap_url_to_absolute(
        './bilibili-resource/dislike.svg',
        resource_root, basic_resource_folder,
    )

    pictures = content.get("pictures", []) or []
    message_html = render_comment_message(
        content, resource_root, basic_resource_folder,
    )


    pictures_html = ""
    all_srcs = [
        remap_url_to_absolute(
            pic.get("img_src", ""), resource_root, basic_resource_folder
        )
        for pic in pictures if pic.get("img_src")
    ]
    if len(all_srcs) == 1:
        img_src = all_srcs[0]
        pictures_html = f'\n            <div class="cs-cmt-v1-comment-picture cs-cmt-v1-single"><img src="{img_src}" alt="评论图片" data-cs-cmt-preview></div>'
    elif len(all_srcs) > 1:
        pictures_html = '\n            <div class="cs-cmt-v1-comment-picture cs-cmt-v1-grid">'
        for i, img_src in enumerate(all_srcs):
            pictures_html += f'\n                <div class="cs-cmt-v1-picture-item" data-cs-cmt-preview><img src="{img_src}" alt="评论图片"></div>'
        pictures_html += '\n            </div>'

    like_count = comment.get("like", 0)
    like_count_html = f'<span>{like_count}</span>' if like_count > 0 else ''
    location = reply_control.get("location", "")
    ctime = comment.get("ctime", 0)
    time_desc = calculate_time_desc(ctime)
    timestamp = datetime.datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M:%S")

    cardbg_html = ""
    user_sailing = member.get("user_sailing", {})
    if user_sailing and "cardbg" in user_sailing:
        cardbg = user_sailing["cardbg"]
        if cardbg:
            cardbg_image = remap_url_to_absolute(
                cardbg.get("image", ""),
                resource_root, basic_resource_folder,
            )
            cardbg_jump_url = cardbg.get("jump_url", "")
            cardbg_name = cardbg.get("name", "")
            cardbg_id = cardbg.get("id", "")
            fan = cardbg.get("fan", {})
            num_prefix = fan.get("num_prefix", "")
            num_desc = fan.get("num_desc", "")
            color_format = fan.get("color_format", {})
            if type(color_format) != dict:
                color_format = {}
            colors = color_format.get("colors", ["#B8C7D0FF", "#A2A7B0FF"])
            gradients = color_format.get("gradients", [0, 100])
            gradient_parts = []
            for i, color in enumerate(colors):
                color_hex = color.replace("FF", "") if color.endswith("FF") else color
                percent = gradients[i] if i < len(gradients) else (100 if i == len(colors) - 1 else 0)
                gradient_parts.append(f"{color_hex} {percent}%")
            gradient_style = f"background-image: linear-gradient(135deg, {', '.join(gradient_parts)}); -webkit-text-fill-color: transparent; background-clip: text;"
            cardbg_html = f"""
            <a href="{cardbg_jump_url}" class="cs-cmt-v1-cardBg" target="_blank">
                <img src="{cardbg_image}" alt="{cardbg_name}">
                <div class="cs-cmt-v1-card-text" style="{gradient_style}">
                    <span>{num_prefix}</span>
                    <span>{num_desc}</span>
                </div>
                <div class="cs-cmt-v1-tooltip">
                    <div class="cs-cmt-v1-tooltip-name">{cardbg_name}</div>
                    <div class="cs-cmt-v1-tooltip-id">ID: {cardbg_id}</div>
                </div>
            </a>"""

    mid = member.get("mid", "")
    profile_url = f"https://space.bilibili.com/{mid}" if mid else ""

    comment_html = f"""
        <div class="cs-cmt-v1-comment-item{deleted_comment_class}">
            {cardbg_html}
            <div class="cs-cmt-v1-comment-header">
                <a href="{profile_url}" class="cs-cmt-v1-avatar" target="_blank">
                    {avatar_html}
                </a>
                <div class="cs-cmt-v1-user-info">
                    <div class="{username_class}">
                        {username}
                        <img class="cs-cmt-v1-level-badge" src="{level_src}" alt="Lv.{level}">
                    </div>
                    <div class="cs-cmt-v1-meta-info">
                        <span>{time_desc}</span>
                        {f'<span>{location}</span>' if location else ''}
                    </div>
                </div>
            </div>
            <div class="cs-cmt-v1-comment-content">{message_html}</div>{pictures_html}
            <div class="cs-cmt-v1-comment-footer">
                <span class="cs-cmt-v1-timestamp">{timestamp}</span>
                <div class="cs-cmt-v1-action-btn">
                    <img src="{like_icon_src}" alt="赞" width="16" height="16">
                    {like_count_html}
                </div>
                <div class="cs-cmt-v1-action-btn">
                    <img src="{dislike_icon_src}" alt="踩" width="16" height="16">
                </div>
            </div>"""

    if replies:
        total_replies = len(replies)
        comment_html += f"""
            <div class="cs-cmt-v1-reply-section">
                <div class="cs-cmt-v1-reply-container" id="cs-cmt-v1-reply-container-{comment_id}">"""
        
        for idx, reply in enumerate(replies):
            reply_member = reply.get("member", {})
            reply_content = reply.get("content", {})
            reply_reply_control = reply.get("reply_control", {})

            reply_username = reply_member.get("uname", "匿名用户")
            reply_level = reply_member.get("level_info", {}).get("current_level", 0)
            reply_vip_status = reply_member.get("vip", {}).get("vipStatus", 0)
            reply_is_senior_member = reply_member.get("is_senior_member", 0)
            reply_avatar_item = reply_member.get("avatar_item", {})

            reply_is_vip = reply_vip_status == 1
            reply_username_class = (
                "cs-cmt-v1-reply-username cs-cmt-v1-vip-username"
                if reply_is_vip else "cs-cmt-v1-reply-username"
            )
            reply_avatar_html = build_avatar_html(
                reply_avatar_item, 36, 36,
                resource_root, basic_resource_folder,
            )

            reply_level_svg = "level_h.svg" if (reply_level == 6 and reply_is_senior_member == 1) else f"level_{reply_level}.svg"
            reply_level_src = remap_url_to_absolute(
                f'./bilibili-resource/{reply_level_svg}',
                resource_root, basic_resource_folder,
            )

            reply_pictures = reply_content.get("pictures", []) or []
            reply_message_html = render_comment_message(
                reply_content, resource_root, basic_resource_folder,
            )


            reply_pictures_html = ""
            reply_all_srcs = [
                remap_url_to_absolute(
                    pic.get("img_src", ""), resource_root,
                    basic_resource_folder,
                )
                for pic in reply_pictures if pic.get("img_src")
            ]
            if len(reply_all_srcs) == 1:
                img_src = reply_all_srcs[0]
                reply_pictures_html = f'\n                        <div class="cs-cmt-v1-comment-picture cs-cmt-v1-single"><img src="{img_src}" alt="评论图片" data-cs-cmt-preview></div>'
            elif len(reply_all_srcs) > 1:
                reply_pictures_html = '\n                        <div class="cs-cmt-v1-comment-picture cs-cmt-v1-grid">'
                for i, img_src in enumerate(reply_all_srcs):
                    reply_pictures_html += f'\n                            <div class="cs-cmt-v1-picture-item" data-cs-cmt-preview><img src="{img_src}" alt="评论图片"></div>'
                reply_pictures_html += '\n                        </div>'

            reply_like = reply.get("like", 0)
            reply_like_html = f'<span>{reply_like}</span>' if reply_like > 0 else ''
            reply_location = reply_reply_control.get("location", "")
            reply_ctime = reply.get("ctime", 0)
            reply_time = calculate_time_desc(reply_ctime)
            reply_timestamp = datetime.datetime.fromtimestamp(reply_ctime).strftime("%Y-%m-%d %H:%M:%S")
            reply_mid = reply_member.get("mid", "")
            reply_profile_url = f"https://space.bilibili.com/{reply_mid}" if reply_mid else ""
            deleted_reply_class = (
                " cs-cmt-v1-deleted-data"
                if mark_deleted and reply.get("_is_deleted") else ""
            )

            display_style = ' style="display: none;"' if total_replies > 2 and idx >= 2 else ''

            comment_html += f"""
                    <div class="cs-cmt-v1-reply-item{deleted_reply_class}" data-reply-index="{idx}"{display_style}>
                        <div class="cs-cmt-v1-reply-header">
                            <a href="{reply_profile_url}" class="cs-cmt-v1-reply-avatar" target="_blank">
                                {reply_avatar_html}
                            </a>
                            <div>
                                <div class="{reply_username_class}">
                                    {reply_username}
                                    <img class="cs-cmt-v1-level-badge" src="{reply_level_src}" alt="Lv.{reply_level}">
                                </div>
                                <div class="cs-cmt-v1-reply-meta">
                                    {reply_time}
                                    {f' · {reply_location}' if reply_location else ''}
                                </div>
                            </div>
                        </div>
                        <div class="cs-cmt-v1-reply-content">{reply_message_html}</div>{reply_pictures_html}
                        <div class="cs-cmt-v1-reply-footer">
                            <span class="cs-cmt-v1-timestamp">{reply_timestamp}</span>
                            <div class="cs-cmt-v1-action-btn">
                                <img src="{like_icon_src}" alt="赞" width="16" height="16">
                                {reply_like_html}
                            </div>
                            <div class="cs-cmt-v1-action-btn">
                                <img src="{dislike_icon_src}" alt="踩" width="16" height="16">
                            </div>
                        </div>
                    </div>"""
        
        comment_html += """
                </div>"""
        
        if total_replies > 2:
            expand_display = ''
            if total_replies <= REPLY_PAGE_SIZE:
                pagination_display = ' style="display: none;"'
                pagination_html = ''
            else:
                pagination_display = ' style="display: none;"'
                total_pages = (total_replies + REPLY_PAGE_SIZE - 1) // REPLY_PAGE_SIZE
                pagination_html = f'<span class="cs-cmt-v1-page-count">共{total_pages}页</span><span class="cs-cmt-v1-page-num cs-cmt-v1-active">1</span>'
                if total_pages > 1:
                    pagination_html += f'<span class="cs-cmt-v1-page-btn" data-cs-cmt-action="reply-page" data-comment-id="{comment_id}" data-page="2" data-total-count="{total_replies}">下一页</span>'
                pagination_html += f'<span class="cs-cmt-v1-page-btn" data-cs-cmt-action="toggle-replies" data-comment-id="{comment_id}" data-total-count="{total_replies}">收起</span>'
            
            comment_html += f"""
                <div class="cs-cmt-v1-reply-expand-btn"{expand_display} data-cs-cmt-action="toggle-replies" data-comment-id="{comment_id}" data-total-count="{total_replies}">共{total_replies}条回复，点击查看</div>"""
            
            if total_replies > REPLY_PAGE_SIZE:
                comment_html += f"""
                <div class="cs-cmt-v1-reply-pagination" id="cs-cmt-v1-reply-pagination-{comment_id}"{pagination_display}>
                    {pagination_html}
                </div>"""
        
        comment_html += """
            </div>"""

    comment_html += """
        </div>"""
    return comment_html

class ClassifyShowerVideo:
    """独立的视频与评论组件，配置访问和保存能力由构造参数注入。"""

    VIDEO_STREAM_HIGH_WATER_SECONDS = 30.0
    # 这里只允许能直接封装进 fMP4、且主流 Chromium MSE 有解码能力的视频编码。
    # MPEG-4 Part 2（DivX/Xvid）虽然能放进 MP4，但浏览器通常无法解码，不能流复制。
    VIDEO_CODEC_MIME_MAP = {
        'h264': 'avc1.640028',
        'hevc': 'hvc1.1.6.L120.B0',
        'av1': 'av01.0.08M.08',
        'vp9': 'vp09.00.10.08'
    }
    SUPPORTED_VIDEO_CODECS = frozenset(VIDEO_CODEC_MIME_MAP)
    # AAC 是当前 fMP4/MSE 传输链路唯一保证跨浏览器可用的音频输出格式。
    SUPPORTED_AUDIO_CODECS = frozenset({'aac'})

    def __init__(self, *, global_config: Dict, get_config: Callable[[], Dict],
                 script_dir: str, save_config: Callable[[], None], database_manager: DatabaseManager):
        """初始化视频任务、缓存与评论连接管理器。"""
        self.global_config = global_config
        self._get_config = get_config
        self.script_dir = script_dir
        self.save_config = save_config
        # 每个 WebSocket、每个播放器组件至多保留一个 FFmpeg 流任务。
        self.video_streams = {}
        self.video_preparations = {}
        self.video_request_tasks = {}
        self.media_probe_cache = OrderedDict()
        self.video_repair_metadata_cache = OrderedDict()
        self.media_probe_tasks = {}
        self.video_keyframe_cache = OrderedDict()
        self.video_keyframe_tasks = {}
        self.video_keyframe_status = OrderedDict()
        self.video_index_semaphore = asyncio.Semaphore(1)
        # 正常评论页面查询复用最近一个数据库连接；切换来源或闲置后自动关闭。
        self.comment_page_connection_manager = CommentPageConnectionManager(
            idle_timeout=1800.0
        )
        self.database_manager = database_manager

    @property
    def config(self):
        """每次取得当前配置，主模块重新加载配置后也不会持有旧字典。"""
        return self._get_config()

    @staticmethod
    def is_path_within(base_path: str, target_path: str) -> bool:
        """判断目标是否位于根目录内；不同盘符或不同 UNC 共享直接视为不匹配。"""
        try:
            normalized_base = os.path.normcase(os.path.realpath(os.path.abspath(base_path)))
            normalized_target = os.path.normcase(os.path.realpath(os.path.abspath(target_path)))
            return os.path.commonpath([normalized_base, normalized_target]) == normalized_base
        except ValueError:
            # Windows 在比较不同盘符，或本地路径与 UNC 路径时会抛出 ValueError。
            return False

    @staticmethod
    def is_resolved_path_within(base_path, target_path):
        """仅用于已经 realpath 解析的路径，避免重复访问网络文件系统。"""
        base = os.path.normcase(base_path)
        target = os.path.normcase(target_path)
        try:
            return os.path.commonpath([base, target]) == base
        except ValueError:
            return False

    def scan_anime_category(self, base_dirs: List[str]):
        """扫描番剧分类"""
        print("[分类展示模块] 扫描番剧分类...")

        existing_paths = set()

        for base_dir in base_dirs:
            if not os.path.exists(base_dir):
                print(f"[分类展示模块] 目录不存在: {base_dir}")
                continue

            for root, dirs, files in os.walk(base_dir):
                if '__MD__.json' in files:
                    md_path = os.path.join(root, '__MD__.json')
                    try:
                        with open(md_path, 'r', encoding='utf-8') as f:
                            md_data = json.load(f)

                        type_val = md_data.get('type')
                        is_anime = (type_val == '番剧') or (isinstance(type_val, list) and '番剧' in type_val)
                        if is_anime:
                            self.process_anime_folder(root, md_data)
                            existing_paths.add(root)
                    except Exception as e:
                        print(f"[分类展示模块] 处理 __MD__.json 失败: {md_path}, 错误: {e}")

        self.cleanup_missing_anime(existing_paths)

    def cleanup_missing_anime(self, existing_paths: set):
        """清理已不存在的番剧条目"""
        try:
            self.database_manager.db_cursor.execute('SELECT id, root_path FROM anime')
            all_anime = self.database_manager.db_cursor.fetchall()

            removed_count = 0
            for anime_id, root_path in all_anime:
                if root_path not in existing_paths:
                    self.database_manager.db_cursor.execute('DELETE FROM anime_tag WHERE anime_id = ?', (anime_id,))
                    self.database_manager.db_cursor.execute('DELETE FROM anime WHERE id = ?', (anime_id,))
                    removed_count += 1
                    print(f"[分类展示模块] 移除不存在的番剧: {root_path}")
            
            if removed_count > 0:
                self.database_manager.db_conn.commit()
            print(f"[分类展示模块] 清理完成，移除了 {removed_count} 个不存在的番剧条目")
        except Exception as e:
            print(f"[分类展示模块] 清理不存在的番剧失败: {e}")
    
    def process_anime_folder(self, folder_path: str, md_data: Dict):
        """处理番剧文件夹"""
        root_path = folder_path
        name = md_data.get('name', '')
        year = md_data.get('year')
        month = md_data.get('month')
        tags_list = md_data.get('item', [])
        cover_path = md_data.get('cover', '')
        entry_time = md_data.get('entry-time', 0)

        if cover_path and not os.path.isabs(cover_path):
            cover_path = os.path.normpath(os.path.join(folder_path, cover_path))

        episode_count = self.count_video_episodes(folder_path)
        name_pinyin = self.database_manager.get_pinyin(name)

        # 读取观看历史
        last_watch_order = 0
        last_watch_time = 0
        last_video_time = 0.0
        history_path = os.path.join(root_path, '__HISTORY__.json')
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                if 'order' in history_data:
                    last_watch_order = history_data['order']
                if 'view-time' in history_data:
                    last_watch_time = history_data['view-time']
                if 'video-time' in history_data:
                    last_video_time = history_data['video-time']
            except Exception as e:
                print(f"[分类展示模块] 读取 __HISTORY__.json 失败: {e}")

        # 检查是否有弹幕（只要有一集有rmcf.json就算有弹幕）
        has_danmaku = 0
        video_extensions = set(ext.lower() for ext in video_type_list)
        try:
            for f in os.listdir(root_path):
                if any(f.lower().endswith(ext) for ext in video_extensions):
                    dm_dir = os.path.join(root_path, f'{f}@meta')
                    dmcf_path = os.path.join(dm_dir, 'rmcf.json')
                    if os.path.exists(dmcf_path):
                        has_danmaku = 1
                        break
        except Exception as e:
            print(f"[分类展示模块] 检查弹幕失败: {e}")

        try:
            self.database_manager.db_cursor.execute('SELECT id FROM anime WHERE root_path = ?', (root_path,))
            existing = self.database_manager.db_cursor.fetchone()
            if existing:
                anime_id = existing[0]
                self.database_manager.db_cursor.execute('DELETE FROM anime_tag WHERE anime_id = ?', (anime_id,))
            else:
                anime_id = None

            self.database_manager.db_cursor.execute('''
                INSERT OR REPLACE INTO anime (root_path, name, name_pinyin, year, month, cover_path, episode_count, entry_time, last_watch_order, last_watch_time, last_video_time, has_danmaku)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (root_path, name, name_pinyin, year, month, cover_path, episode_count, entry_time, last_watch_order, last_watch_time, last_video_time, has_danmaku))

            #if anime_id is None:
            self.database_manager.db_cursor.execute('SELECT id FROM anime WHERE root_path = ?', (root_path,))
            anime_id = self.database_manager.db_cursor.fetchone()[0]

            for tag_name in tags_list:
                tag_name = tag_name.strip()
                if not tag_name:
                    continue

                tag_pinyin = self.database_manager.get_pinyin(tag_name)
                self.database_manager.db_cursor.execute('INSERT OR IGNORE INTO tag (name, pinyin) VALUES (?, ?)', (tag_name, tag_pinyin))
                self.database_manager.db_cursor.execute('SELECT id FROM tag WHERE name = ?', (tag_name,))
                tag_id = self.database_manager.db_cursor.fetchone()[0]
                self.database_manager.db_cursor.execute('INSERT OR IGNORE INTO anime_tag (anime_id, tag_id) VALUES (?, ?)', (anime_id, tag_id))

            self.database_manager.db_conn.commit()
            print(f"[分类展示模块] 添加番剧: {name} ({year}), 剧集数: {episode_count}, 标签: {tags_list}")
        except Exception as e:
            print(f"[分类展示模块] 添加番剧失败: {name}, 错误: {e}")

    def count_video_episodes(self, folder_path: str) -> int:
        """统计文件夹下的视频文件数量"""
        count = 0
        video_extensions = set(ext.lower() for ext in video_type_list)
        
        try:
            for entry in os.scandir(folder_path):
                if entry.is_file():
                    ext = os.path.splitext(entry.name)[1].lstrip('.')
                    if ext in video_extensions:
                        count += 1
        except Exception as e:
            print(f"[分类展示模块] 统计视频文件失败: {folder_path}, 错误: {e}")
        
        return count


    def get_anime_detail(self, anime_id: int) -> Dict:
        """获取番剧详情

        Args:
            anime_id: 番剧ID

        Returns:
            包含番剧详情的字典
        """
        self.database_manager.db_cursor.execute('''
            SELECT id, root_path, name, name_pinyin, year, month, cover_path, episode_count, entry_time
            FROM anime WHERE id = ?
        ''', (anime_id,))
        row = self.database_manager.db_cursor.fetchone()

        if not row:
            return {}

        anime = {
            'id': row[0],
            'rootPath': row[1],
            'name': row[2],
            'pinyin': row[3] or '',
            'year': row[4],
            'month': row[5],
            'coverPath': row[6],
            'episodeCount': row[7],
            'entryTime': row[8]
        }

        md_path = os.path.join(row[1], '__MD__.json')
        if os.path.exists(md_path):
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    md_data = json.load(f)
                anime['mdName'] = md_data.get('name', '')
                anime['mdYear'] = md_data.get('year')
                anime['mdMonth'] = md_data.get('month')
                anime['tags'] = md_data.get('item', [])
                anime['introduction'] = md_data.get('introduction')
                anime['introductionSrc'] = md_data.get('introduction-src')
                anime['episodeMap'] = md_data.get('episode-map', [])
            except Exception as e:
                print(f"[分类展示模块] 读取__MD__.json失败: {e}")
                anime['tags'] = []
                anime['introduction'] = None
                anime['introductionSrc'] = None
                anime['episodeMap'] = []
        else:
            anime['tags'] = []
            anime['introduction'] = None
            anime['introductionSrc'] = None
            anime['episodeMap'] = []

        has_danmu = False
        danmu_sources = set()
        root_path = row[1]
        video_files = []

        if anime['episodeMap']:
            for ep in anime['episodeMap']:
                video_files.append({
                    'order': ep.get('order'),
                    'path': ep.get('path'),
                    'name': ep.get('name', '')
                })
        else:
            if os.path.exists(root_path):
                for f in os.listdir(root_path):
                    if f.lower().endswith(tuple(f'.{ext}' for ext in video_type_list)):
                        video_files.append({
                            'order': len(video_files) + 1,
                            'path': f,
                            'name': ''
                        })
            video_files.sort(key=lambda x: x['path'])
            for i in range(len(video_files)):
                video_files[i]['order'] = i + 1 # 重置为正确的剧集顺序


        anime['episodes'] = []
        for ep in video_files:
            video_name = ep['path']
            dm_dir = os.path.join(root_path, f'{video_name}@meta')
            dmcf_json_path = os.path.join(dm_dir, 'rmcf.json')
            dm_info_path = os.path.join(dm_dir, 'dm-info.json')

            has_ep_danmu = os.path.exists(dmcf_json_path)
            if has_ep_danmu:
                has_danmu = True

            ep_danmu_sources = []
            if os.path.exists(dm_info_path):
                try:
                    with open(dm_info_path, 'r', encoding='utf-8') as f:
                        dm_info = json.load(f)
                    dm_src_list = dm_info.get('dm-src', [])
                    for src in dm_src_list:
                        src_name = src.get('name', '')
                        if src_name:
                            danmu_sources.add(src_name)
                            ep_danmu_sources.append(src_name)
                except Exception as e:
                    print(f"[分类展示模块] 读取dm-info.json失败: {e}")

            anime['episodes'].append({
                'order': ep['order'],
                'name': ep['name'],
                'path': ep['path'],
                'hasDanmu': has_ep_danmu,
                'danmuSources': ep_danmu_sources
            })

        anime['hasDanmu'] = has_danmu
        anime['danmuSources'] = list(danmu_sources)

        self.database_manager.db_cursor.execute('''
            SELECT t.name FROM tag t
            JOIN anime_tag at ON t.id = at.tag_id
            WHERE at.anime_id = ?
        ''', (anime_id,))
        anime['dbTags'] = [row[0] for row in self.database_manager.db_cursor.fetchall()]

        #print(f"[分类展示模块] 剧集信息: {anime['episodes']}")
        return anime

    def get_anime_page(self, page: int = 1, page_size: int = 10, sort_by: str = 'year',
                       sort_order: str = 'DESC',
                       tag_filter_enabled: bool = False, selected_tags: List[int] = None) -> Dict:
        """获取番剧分页数据

        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            sort_by: 排序方式 ('year', 'addtime', 'pinyin')
            sort_order: 排序顺序 ('DESC' 降序, 'ASC' 升序)
            tag_filter_enabled: 是否启用标签筛选
            selected_tags: 选中的标签ID列表

        Returns:
            包含番剧列表、总数、所有标签的字典
        """
        if selected_tags is None:
            selected_tags = []

        order_symbol = sort_order.upper() if sort_order.upper() in ('ASC', 'DESC') else 'DESC'

        if sort_by == 'year':
            order_clause = f'ORDER BY a.year {order_symbol}, a.name'
        elif sort_by == 'addtime':
            order_clause = f'ORDER BY a.entry_time {order_symbol}, a.name'
        elif sort_by == 'pinyin':
            order_clause = f'ORDER BY a.name_pinyin {order_symbol}, a.name'
        else:
            order_clause = f'ORDER BY a.year {order_symbol}, a.name'

        # 构建标签筛选条件
        if tag_filter_enabled and selected_tags:
            placeholders = ','.join('?' * len(selected_tags))
            tag_filter_clause = f'AND t.id IN ({placeholders})'
            tag_filter_params = selected_tags
        else:
            tag_filter_clause = ''
            tag_filter_params = []

        # 获取总数
        if tag_filter_enabled and selected_tags:
            count_query = '''
                SELECT COUNT(DISTINCT a.id)
                FROM anime a
                JOIN anime_tag at ON a.id = at.anime_id
                JOIN tag t ON at.tag_id = t.id
                WHERE t.id IN ({placeholders})
                GROUP BY a.id
                HAVING COUNT(DISTINCT t.id) >= {tag_count}
            '''.format(placeholders=','.join('?' * len(selected_tags)), tag_count=len(selected_tags))
            self.database_manager.db_cursor.execute(count_query, tag_filter_params)
            total = len(self.database_manager.db_cursor.fetchall())
        else:
            self.database_manager.db_cursor.execute('SELECT COUNT(*) FROM anime')
            total = self.database_manager.db_cursor.fetchone()[0]

        # 计算分页
        offset = (page - 1) * page_size

        # 获取番剧列表
        if tag_filter_enabled and selected_tags:
            query = '''
                SELECT a.id, a.root_path, a.name, a.year, a.cover_path, a.episode_count, a.name_pinyin,
                       GROUP_CONCAT(DISTINCT t.name) as tags,
                       GROUP_CONCAT(DISTINCT t.id) as tag_ids
                FROM anime a
                LEFT JOIN anime_tag at ON a.id = at.anime_id
                LEFT JOIN tag t ON at.tag_id = t.id
                WHERE a.id IN (
                    SELECT DISTINCT a.id
                    FROM anime a
                    JOIN anime_tag at ON a.id = at.anime_id
                    JOIN tag t ON at.tag_id = t.id
                    WHERE t.id IN ({placeholders})
                    GROUP BY a.id
                    HAVING COUNT(DISTINCT t.id) >= {tag_count}
                )
                GROUP BY a.id
                {order_clause}
                LIMIT ? OFFSET ?
            '''.format(placeholders=','.join('?' * len(selected_tags)), tag_count=len(selected_tags), order_clause=order_clause)
            params = tag_filter_params + [page_size, offset]
        else:
            query = f'''
                SELECT a.id, a.root_path, a.name, a.year, a.cover_path, a.episode_count, a.name_pinyin,
                       GROUP_CONCAT(DISTINCT t.name) as tags,
                       GROUP_CONCAT(DISTINCT t.id) as tag_ids
                FROM anime a
                LEFT JOIN anime_tag at ON a.id = at.anime_id
                LEFT JOIN tag t ON at.tag_id = t.id
                GROUP BY a.id
                {order_clause}
                LIMIT ? OFFSET ?
            '''
            params = [page_size, offset]

        self.database_manager.db_cursor.execute(query, params)
        rows = self.database_manager.db_cursor.fetchall()
        print(rows)
        anime_list = []
        for row in rows:
            tag_ids_str = row[8] or ''
            tag_ids = [int(tid) for tid in tag_ids_str.split(',') if tid]
            tags_str = row[7] or ''
            tags = tags_str.split(',') if tags_str else []

            anime_list.append({
                'id': row[0],
                'root_path': row[1],
                'name': row[2],
                'year': row[3],
                'poster': row[4],
                'episode_count': row[5],
                'name_pinyin': row[6] or '',
                'tags': tags,
                'tag_ids': tag_ids
            })

        # 获取所有标签
        all_tags = self.database_manager.get_all_tags_with_id()

        return {
            'animeList': anime_list,
            'total': total,
            'allTags': all_tags,
            'page': page,
            'pageSize': page_size,
            'totalPages': (total + page_size - 1) // page_size if page_size > 0 else 1
        }



    def resolve_video_path(self, root_path: str, video_path: str) -> str:
        """解析并校验前端提交的视频路径，禁止越出已配置的资源目录。"""
        #[DEBUG-START]
        trace = VIDEO_SEEK_TRACE.get()
        #[DEBUG-END]
        if not root_path or not video_path:
            raise ValueError("缺少视频路径")

        root_path = os.path.realpath(os.path.abspath(root_path))
        #[DEBUG-START]
        if trace:
            trace.step('番剧根目录规范化完成')
        #[DEBUG-END]
        full_path = os.path.realpath(os.path.abspath(os.path.join(root_path, video_path)))
        #[DEBUG-START]
        if trace:
            trace.step('视频完整路径规范化完成')
        #[DEBUG-END]
        if not self.is_resolved_path_within(root_path, full_path):
            raise ValueError("视频路径超出番剧目录")

        #[DEBUG-START]
        if trace:
            trace.step('番剧目录边界检查完成')
        #[DEBUG-END]
        allowed_roots = [
            os.path.realpath(os.path.abspath(path))
            for path in self.global_config.get('base_dir', [])
        ]
        #[DEBUG-START]
        if trace:
            trace.step('配置资源根目录规范化完成')
        #[DEBUG-END]
        if allowed_roots and not any(self.is_resolved_path_within(path, full_path) for path in allowed_roots):
            raise ValueError("视频路径不在已配置的资源目录中")
        #[DEBUG-START]
        if trace:
            trace.step('配置资源目录边界检查完成')
        #[DEBUG-END]
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"视频文件不存在: {full_path}")
        #[DEBUG-START]
        if trace:
            trace.step('视频文件存在性检查完成')
        #[DEBUG-END]
        return full_path

    def get_ffmpeg_path(self) -> str:
        #[DEBUG-START]
        trace = VIDEO_SEEK_TRACE.get()
        #[DEBUG-END]
        ffmpeg_path = self.config.get('video-config', {}).get('ffmpeg-path', '')
        if not ffmpeg_path:
            raise FileNotFoundError("未在 classify_shower_config.json 中配置 video-config.ffmpeg-path")
        ffmpeg_path = os.path.expandvars(os.path.expanduser(ffmpeg_path))
        #[DEBUG-START]
        if trace:
            trace.step('FFmpeg 配置读取与变量展开完成')
        #[DEBUG-END]
        if not os.path.isfile(ffmpeg_path):
            raise FileNotFoundError(f"FFmpeg 不存在: {ffmpeg_path}")
        #[DEBUG-START]
        if trace:
            trace.step('FFmpeg 文件存在性检查完成')
        #[DEBUG-END]
        return ffmpeg_path

    def read_video_playback_policy(self, video_path):
        """仅明确的 JSON false 触发普通 MP4 修复；读取失败保持原播放策略。"""
        force = False
        video_stream = ''
        compat_file = ''
        status = 'not-mp4'
        if video_path:
            status = 'missing-or-unreadable'
            metadata_path = os.path.realpath(video_path + '@meta')
            meta_file = os.path.realpath(os.path.join(metadata_path, '__meta'))
            # 元数据符号链接同样不能绕过视频所在资源目录边界。
            if self.is_path_within(os.path.dirname(video_path), meta_file):
                try:
                    if os.path.getsize(meta_file) > 65536:
                        raise ValueError('__meta 文件超过读取大小上限')
                    with open(meta_file, 'r', encoding='utf-8-sig') as source:
                        data = json.load(source)
                    if isinstance(data, dict):
                        value = data.get('mp4-timestamps-valid')
                        force = Path(video_path).suffix.lower() == '.mp4' and value is False
                        stream_value = data.get('video-stream')
                        video_stream = stream_value if isinstance(stream_value, str) else ''
                        status = 'false' if force else 'default'
                except (OSError, ValueError):
                    pass
            if video_stream == 'H265':
                candidate = os.path.realpath(os.path.join(
                    os.path.dirname(video_path), '__COMPAT__', os.path.basename(video_path)))
                if self.is_path_within(os.path.dirname(video_path), candidate) and os.path.isfile(candidate):
                    compat_file = candidate
        #[DEBUG-START]
        print(f'[视频播放策略] 元数据状态={status} 修复缓冲播放={force} 文件={video_path}')
        #[DEBUG-END]
        return {'force-buffered-playback': force,
                'video-stream': video_stream, 'compat_file': compat_file,
                'buffered-playback-reason': 'mp4-timestamps-invalid' if force else None}

    VIDEO_METADATA_CACHE_LIMIT = 32

    async def cached_repair_metadata(self, cache_key, ffmpeg_path, video_path):
        cache = self.video_repair_metadata_cache
        if cache_key in cache:
            cache.move_to_end(cache_key)
            return cache[cache_key]
        metadata = await run_in_thread(MP4TimestampMetadata, video_path)
        if self.video_metadata_key(ffmpeg_path, video_path) != cache_key:
            raise ValueError('读取修复元数据期间视频或 FFmpeg 已变化，请重新播放')
        self.store_video_metadata(cache, cache_key, metadata)
        # 样本表比媒体探测结果大，最多缓存4部视频、合计50万个样本。
        while len(cache) > 4 or sum(len(item.positions) for item in cache.values()) > 500000:
            cache.popitem(last=False)
        return metadata

    @staticmethod
    def video_metadata_key(ffmpeg_path, video_path):
        """文件或工具更新后自动失效；缓存不替代播放前的路径权限检查。"""
        def signature(path):
            info = os.stat(path)
            return (os.path.normcase(os.path.abspath(path)), info.st_size,
                    info.st_mtime_ns, info.st_ctime_ns)
        return signature(video_path), signature(ffmpeg_path)

    def store_video_metadata(self, cache, key, value):
        # 同一路径的旧版本无需保留。
        for old in list(cache):
            if old[0][0] == key[0][0]:
                del cache[old]
        cache[key] = value
        while len(cache) > self.VIDEO_METADATA_CACHE_LIMIT:
            cache.popitem(last=False)

    async def cached_probe_video(self, key, ffmpeg_path, video_path):
        if key in self.media_probe_cache:
            self.media_probe_cache.move_to_end(key)
            return dict(self.media_probe_cache[key])
        task = self.media_probe_tasks.get(key)
        if task is None:
            async def probe():
                try:
                    result = await asyncio.get_running_loop().run_in_executor(
                        None, self.probe_video, ffmpeg_path, video_path)
                    if self.video_metadata_key(ffmpeg_path, video_path) == key:
                        self.store_video_metadata(self.media_probe_cache, key, dict(result))
                    return result
                finally:
                    self.media_probe_tasks.pop(key, None)
            task = asyncio.create_task(probe())
            self.media_probe_tasks[key] = task
            task.add_done_callback(lambda done: done.exception() if not done.cancelled() else None)
        return dict(await asyncio.shield(task))

    BACKWARD_INDEX_CONTAINERS = {'.mp4', '.m4v', '.mov', '.mkv', '.webm'}
    FORWARD_INDEX_CONTAINERS = {'.ts', '.mts', '.m2ts'}

    def video_index_state(self, key, video_path):
        if Path(video_path).suffix.lower() not in (self.BACKWARD_INDEX_CONTAINERS | self.FORWARD_INDEX_CONTAINERS):
            return 'unsupported-container'
        if key in self.video_keyframe_cache:
            return 'ready'
        return self.video_keyframe_status.get(key, {}).get('state', 'not-started')

    def ensure_video_keyframe_index(self, key, ffmpeg_path, video_path):
        """后台顺序扫描压缩包；同一文件共享任务，最多一个扫描进程。"""
        if self.video_index_state(key, video_path) == 'unsupported-container':
            return
        if key in self.video_keyframe_cache or key in self.video_keyframe_tasks:
            return
        previous = self.video_keyframe_status.get(key, {})
        if previous.get('retryAfter', 0) > time.monotonic():
            return
        if len(self.video_keyframe_tasks) >= self.VIDEO_METADATA_CACHE_LIMIT:
            self.store_video_metadata(self.video_keyframe_status, key, {'state': 'queue-full'})
            return
        self.store_video_metadata(self.video_keyframe_status, key, {'state': 'queued'})
        self.video_keyframe_tasks[key] = asyncio.create_task(
            self.build_video_keyframe_index(key, ffmpeg_path, video_path))

    async def build_video_keyframe_index(self, key, ffmpeg_path, video_path):
        process = None
        #[DEBUG-START]
        index_started = time.perf_counter()
        #[DEBUG-END]
        try:
            async with self.video_index_semaphore:
                self.store_video_metadata(self.video_keyframe_status, key, {'state': 'building'})
                process = await asyncio.create_subprocess_exec(
                    ffmpeg_path, '-hide_banner', '-nostdin', '-nostats',
                    '-dump', '-debug_ts', '-i', video_path,
                    '-map', '0:v:0', '-an', '-sn', '-dn', '-c:v', 'copy',
                    '-f', 'null', 'pipe:1',
                    stdin=asyncio.subprocess.DEVNULL, stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                frames = []
                packet_is_key = False
                first_video_index = None
                # dump 给出关键帧标记，debug_ts 给出精度更高且经过输入起点归一化的 PTS。
                async def scan():
                    nonlocal packet_is_key, first_video_index
                    while True:
                        raw = await process.stderr.readline()
                        if not raw:
                            break
                        line = raw.decode('utf-8', errors='replace').strip()
                        if line.startswith('stream #'):
                            packet_is_key = False
                        elif line.startswith('keyframe='):
                            packet_is_key = line == 'keyframe=1'
                        elif line.startswith('demuxer+ffmpeg ->') and 'type:video' in line:
                            stream = re.search(r'ist_index:(\d+)', line)
                            if stream and first_video_index is None:
                                first_video_index = stream.group(1)
                            pts = re.search(r'pkt_pts_time:(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)', line, re.I)
                            if (packet_is_key and pts and stream
                                    and stream.group(1) == first_video_index):
                                dts = re.search(r'pkt_dts_time:(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)', line, re.I)
                                if dts:
                                    frames.append((float(dts.group(1)), float(pts.group(1))))
                    return await process.wait()
                # 网络盘或异常文件不能无限占用扫描进程；失败时继续使用原定位方式。
                code = await asyncio.wait_for(scan(), timeout=300)
                if code != 0 or not frames:
                    raise ValueError('未取得完整关键帧索引')
                if self.video_metadata_key(ffmpeg_path, video_path) == key:
                    self.store_video_metadata(self.video_keyframe_cache, key,
                                              {'decode': tuple(sorted(set(frames))),
                                               'presentation': tuple(sorted(set(pts for _, pts in frames)))})
                    self.store_video_metadata(self.video_keyframe_status, key, {'state': 'ready'})
                else:
                    self.store_video_metadata(self.video_keyframe_status, key, {'state': 'file-changed'})
                #[DEBUG-START]
                print(f"[视频关键帧索引] 建立完成: {(time.perf_counter()-index_started)*1000:.2f} ms "
                      f"关键帧数={len(frames)} 文件={video_path}")
                #[DEBUG-END]
        except asyncio.CancelledError:
            self.store_video_metadata(self.video_keyframe_status, key, {'state': 'cancelled'})
            raise
        except Exception as e:
            self.store_video_metadata(self.video_keyframe_status, key,
                                      {'state': 'failed', 'error': str(e),
                                       'retryAfter': time.monotonic() + 60})
            #[DEBUG-START]
            print(f"[视频关键帧索引] 建立失败，保留逐次定位: {e}")
            #[DEBUG-END]
            pass
        finally:
            await self.stop_ffmpeg_process(process, drain_stderr=True)
            self.video_keyframe_tasks.pop(key, None)

    async def cached_align_video_keyframe(self, key, ffmpeg_path, video_path, requested_time):
        frames = self.video_keyframe_cache.get(key)
        suffix = Path(video_path).suffix.lower()
        if frames is not None and suffix in (self.BACKWARD_INDEX_CONTAINERS | self.FORWARD_INDEX_CONTAINERS):
            self.video_keyframe_cache.move_to_end(key)
            # TS 流复制按 PTS 丢弃请求时间之前的数据；带输入索引的容器
            # 从前一个解码关键帧起步。分别索引，避免 B 帧的 DTS/PTS 混用。
            if suffix in self.FORWARD_INDEX_CONTAINERS:
                points = frames['presentation']
                index = bisect_left(points, requested_time)
                if index >= len(points):
                    return requested_time
                candidate = points[index]
            else:
                points = frames['decode']
                index = bisect_left(points, (requested_time, float('-inf')))
                if index > 0:
                    candidate = points[index - 1][1]
                elif points:
                    candidate = points[0][1]
                else:
                    return requested_time
            if 0.05 < candidate - requested_time <= 30:
                return candidate
            return requested_time
        return await asyncio.get_running_loop().run_in_executor(
            None, self.align_seek_to_video_keyframe, ffmpeg_path, video_path, requested_time)

    def probe_h264_codec_string(self, ffmpeg_path: str, video_path: str) -> Optional[str]:
        """从 FFmpeg 生成的 avcC 中提取准确的 RFC 6381 H.264 codec 字符串。"""
        try:
            result = subprocess.run([
                ffmpeg_path, '-hide_banner', '-loglevel', 'error',
                '-i', video_path, '-map', '0:v:0', '-an', '-c', 'copy',
                '-frames:v', '1',
                '-movflags', 'frag_keyframe+empty_moov+default_base_moof',
                '-f', 'mp4', 'pipe:1'
            ], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            marker = result.stdout.find(b'avcC')
            # avcC: configurationVersion, AVCProfileIndication,
            # profile_compatibility, AVCLevelIndication
            if marker >= 0 and len(result.stdout) >= marker + 8:
                return 'avc1.' + result.stdout[marker + 5:marker + 8].hex().upper()
        except Exception as e:
            print(f"[分类展示模块] 提取 H.264 codec 信息失败: {e}")
        return None

    def align_seek_to_video_keyframe(self, ffmpeg_path: str, video_path: str,
                                     requested_time: float) -> float:
        """把流复制 Seek 对齐到下一个视频关键帧，避免音频和视频从不同时间起步。"""
        if requested_time <= 0:
            return 0.0
        try:
            result = subprocess.run([
                ffmpeg_path, '-hide_banner', '-loglevel', 'info', '-debug_ts',
                '-ss', f'{requested_time:.6f}', '-i', video_path,
                '-map', '0:v:0', '-an', '-c', 'copy', '-frames:v', '1',
                '-f', 'null', 'pipe:1'
            ], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            output = result.stderr.decode('utf-8', errors='replace')
            match = re.search(
                r'muxer <- type:video .*?pkt_pts_time:'
                r'(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)',
                output, flags=re.IGNORECASE
            )
            if not match:
                return requested_time

            keyframe_delay = float(match.group(1))
            if keyframe_delay <= 0.05 or keyframe_delay > 30:
                return requested_time
            return requested_time + keyframe_delay
        except Exception as e:
            print(f"[分类展示模块] Seek 关键帧探测失败，使用原时间: {e}")
            return requested_time

    def probe_video(self, ffmpeg_path: str, video_path: str) -> Dict:
        """利用 FFmpeg 的快速输入探测获取时长和 MSE 所需的 codec MIME。"""
        result = subprocess.run(
            [ffmpeg_path, '-hide_banner', '-i', video_path],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        output = result.stderr.decode('utf-8', errors='replace')
        duration_match = re.search(r'Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)', output)
        duration = 0.0
        if duration_match:
            duration = (int(duration_match.group(1)) * 3600
                        + int(duration_match.group(2)) * 60
                        + float(duration_match.group(3)))

        video_match = re.search(r'Video:\s*([^,\s]+)', output)
        audio_match = re.search(r'Audio:\s*([^,\s]+)', output)
        if not video_match:
            raise ValueError("FFmpeg 未探测到视频轨道")

        video_codec = video_match.group(1).lower()
        video_supported = video_codec in self.SUPPORTED_VIDEO_CODECS
        source_audio_codec = audio_match.group(1).lower() if audio_match else None
        audio_transcoded = bool(
            source_audio_codec and source_audio_codec not in self.SUPPORTED_AUDIO_CODECS
        )
        output_audio_codec = 'aac' if audio_transcoded else source_audio_codec
        if video_codec == 'h264':
            detected_video_codec = self.probe_h264_codec_string(ffmpeg_path, video_path)
        else:
            detected_video_codec = None
        codecs = [detected_video_codec or self.VIDEO_CODEC_MIME_MAP.get(video_codec, video_codec)]
        if output_audio_codec:
            codecs.append('mp4a.40.2')
        return {
            'duration': duration,
            'videoCodec': video_codec,
            'videoSupported': video_supported,
            'sourceAudioCodec': source_audio_codec,
            'audioCodec': output_audio_codec,
            'audioTranscoded': audio_transcoded,
            'mimeType': 'video/mp4; codecs="{}"'.format(','.join(codecs))
        }

    async def send_stream_json(self, websocket, command: str, **data):
        await websocket.send(json.dumps({'command': command, **data}, ensure_ascii=False))

    def pack_video_chunk(self, stream_id: str, widget_id: str, sequence: int,
                         payload: bytes, segment_type: str) -> bytes:
        header = json.dumps({
            'type': 'VIDEO_STREAM_CHUNK',
            'streamId': stream_id,
            'widgetId': widget_id,
            'sequence': sequence,
            'segmentType': segment_type
        }, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        return b'HSV1' + struct.pack('>I', len(header)) + header + payload

    @staticmethod
    def extract_mp4_boxes(buffer: bytearray, end_of_stream: bool = False):
        """从 FFmpeg 管道数据中取出完整的顶层 ISO-BMFF box。"""
        boxes = []
        while len(buffer) >= 8:
            box_size = int.from_bytes(buffer[0:4], byteorder='big')
            header_size = 8
            if box_size == 1:
                if len(buffer) < 16:
                    break
                box_size = int.from_bytes(buffer[8:16], byteorder='big')
                header_size = 16
            elif box_size == 0:
                if not end_of_stream:
                    break
                box_size = len(buffer)

            if box_size < header_size:
                raise ValueError('FFmpeg 输出了无效的 MP4 box 长度')
            # 防止损坏的长度字段让服务端无限缓存；正常的两秒分片远小于此值。
            if box_size > 128 * 1024 * 1024:
                raise ValueError('FFmpeg 输出的单个 MP4 box 超过 128 MB')
            if len(buffer) < box_size:
                break

            box_type = bytes(buffer[4:8])
            boxes.append((box_type, bytes(buffer[:box_size])))
            del buffer[:box_size]
        return boxes

    @staticmethod
    def list_mp4_boxes(data: bytes, start: int = 0, end: Optional[int] = None):
        """列出一段完整 ISO-BMFF 数据中的直属子 box。"""
        boxes = []
        end = len(data) if end is None else min(end, len(data))
        offset = start
        while offset + 8 <= end:
            box_size = int.from_bytes(data[offset:offset + 4], byteorder='big')
            header_size = 8
            if box_size == 1:
                if offset + 16 > end:
                    break
                box_size = int.from_bytes(data[offset + 8:offset + 16], byteorder='big')
                header_size = 16
            elif box_size == 0:
                box_size = end - offset
            if box_size < header_size or offset + box_size > end:
                break
            boxes.append((offset, box_size, bytes(data[offset + 4:offset + 8]), header_size))
            offset += box_size
        return boxes

    @classmethod
    def read_mp4_track_timescales(cls, init_segment: bytes) -> Dict[int, int]:
        """从 moov 的 tkhd/mdhd 建立 track id 到 timescale 的映射。"""
        timescales = {}
        for moov_offset, moov_size, box_type, moov_header in cls.list_mp4_boxes(init_segment):
            if box_type != b'moov':
                continue
            moov_end = moov_offset + moov_size
            for trak_offset, trak_size, trak_type, trak_header in cls.list_mp4_boxes(
                    init_segment, moov_offset + moov_header, moov_end):
                if trak_type != b'trak':
                    continue
                track_id = None
                timescale = None
                trak_end = trak_offset + trak_size
                for child_offset, child_size, child_type, child_header in cls.list_mp4_boxes(
                        init_segment, trak_offset + trak_header, trak_end):
                    content_offset = child_offset + child_header
                    if child_type == b'tkhd' and content_offset + 24 <= len(init_segment):
                        version = init_segment[content_offset]
                        track_id_offset = content_offset + 4 + (16 if version == 1 else 8)
                        track_id = int.from_bytes(
                            init_segment[track_id_offset:track_id_offset + 4], byteorder='big'
                        )
                    elif child_type == b'mdia':
                        child_end = child_offset + child_size
                        for mdia_offset, mdia_size, mdia_type, mdia_header in cls.list_mp4_boxes(
                                init_segment, content_offset, child_end):
                            if mdia_type != b'mdhd':
                                continue
                            mdhd_content = mdia_offset + mdia_header
                            if mdhd_content + 24 > len(init_segment):
                                continue
                            version = init_segment[mdhd_content]
                            timescale_offset = mdhd_content + 4 + (16 if version == 1 else 8)
                            timescale = int.from_bytes(
                                init_segment[timescale_offset:timescale_offset + 4],
                                byteorder='big'
                            )
                if track_id is not None and timescale:
                    timescales[track_id] = timescale
        return timescales

    @classmethod
    def read_mp4_fragment_start(cls, media_segment: bytes,
                                track_timescales: Dict[int, int]) -> Optional[float]:
        """读取 moof 内各轨道 tfdt，返回该媒体分段的最早时间。"""
        starts = []
        for moof_offset, moof_size, box_type, moof_header in cls.list_mp4_boxes(media_segment):
            if box_type != b'moof':
                continue
            moof_end = moof_offset + moof_size
            for traf_offset, traf_size, traf_type, traf_header in cls.list_mp4_boxes(
                    media_segment, moof_offset + moof_header, moof_end):
                if traf_type != b'traf':
                    continue
                track_id = None
                base_decode_time = None
                traf_end = traf_offset + traf_size
                for child_offset, child_size, child_type, child_header in cls.list_mp4_boxes(
                        media_segment, traf_offset + traf_header, traf_end):
                    content_offset = child_offset + child_header
                    if child_type == b'tfhd' and content_offset + 8 <= len(media_segment):
                        track_id = int.from_bytes(
                            media_segment[content_offset + 4:content_offset + 8],
                            byteorder='big'
                        )
                    elif child_type == b'tfdt' and content_offset + 8 <= len(media_segment):
                        version = media_segment[content_offset]
                        value_size = 8 if version == 1 else 4
                        value_offset = content_offset + 4
                        if value_offset + value_size > child_offset + child_size:
                            continue
                        base_decode_time = int.from_bytes(
                            media_segment[value_offset:value_offset + value_size],
                            byteorder='big'
                        )
                timescale = track_timescales.get(track_id)
                if timescale and base_decode_time is not None:
                    starts.append(base_decode_time / timescale)
        return min(starts) if starts else None

    @staticmethod
    async def stop_ffmpeg_process(process, drain_stderr=False, trace=None):
        """终止进程并同步排空 stdout，防止 PIPE 背压阻止 asyncio wait 完成。

        调用方必须先停止 stdout 消费；stderr 仍有收集任务时由该任务排空。
        """
        if not process:
            return
        #[DEBUG-START]
        if trace:
            trace.step('主 FFmpeg 进程开始回收', pid=process.pid, returncode=process.returncode)
        #[DEBUG-END]
        async def drain_reader(reader):
            if reader:
                while await reader.read(64 * 1024):
                    pass
        async def drain_output():
            readers = [process.stdout]
            if drain_stderr:
                readers.append(process.stderr)
            await asyncio.gather(*(drain_reader(reader) for reader in readers))
        drain_task = asyncio.create_task(drain_output())
        try:
            if process.returncode is None:
                try:
                    process.terminate()
                except ProcessLookupError:
                    pass
            try:
                await asyncio.wait_for(process.wait(), timeout=2)
            except asyncio.TimeoutError:
                #[DEBUG-START]
                print(f"[视频进程回收] 终止等待超时，强制回收 pid={process.pid}")
                #[DEBUG-END]
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                await process.wait()
            #[DEBUG-START]
            if trace:
                trace.step('主 FFmpeg 退出等待完成', returncode=process.returncode)
            #[DEBUG-END]
            await drain_task
            #[DEBUG-START]
            if trace:
                trace.step('主 FFmpeg 输出管道排空完成')
            #[DEBUG-END]
        finally:
            if not drain_task.done():
                drain_task.cancel()
            await asyncio.gather(drain_task, return_exceptions=True)

    async def cancel_video_stream(self, websocket, widget_id: str, cleanup_trace=None):
        requests = self.video_request_tasks.get(websocket, {})
        request_task = requests.get(widget_id)
        if request_task and request_task is not asyncio.current_task():
            requests.pop(widget_id, None)
            request_task.cancel()
            await asyncio.gather(request_task, return_exceptions=True)
        if not requests:
            self.video_request_tasks.pop(websocket, None)
        pending = self.video_preparations.get(websocket, {})
        pending.pop(widget_id, None)
        if not pending:
            self.video_preparations.pop(websocket, None)
        sessions = self.video_streams.get(websocket, {})
        session = sessions.pop(widget_id, None)
        if session:
            task = session.get('task')
            process = session.get('process')
            timestamp_repair = session.get('timestampRepair')
            #[DEBUG-START]
            session['cancelTrace'] = cleanup_trace
            if cleanup_trace:
                cleanup_trace.step('旧输出任务开始取消', pid=process.pid if process else None,
                                   taskDone=task.done() if task else True)
            #[DEBUG-END]
            # 先给两个写入者发出停止请求，不把它们留到输出任务 finally 才终止。
            if task and task is not asyncio.current_task():
                task.cancel()
            if timestamp_repair:
                timestamp_repair.request_stop()
            if process and process.returncode is None:
                try:
                    process.terminate()
                except ProcessLookupError:
                    pass
            #[DEBUG-START]
            if cleanup_trace:
                cleanup_trace.step('旧主进程与辅助进程终止请求已发出')
            #[DEBUG-END]
            if task and task is not asyncio.current_task():
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
            if process:
                # 预启动的输出进程可能尚未交给输出任务执行。
                await self.stop_ffmpeg_process(process, drain_stderr=True)
            # 输出任务可能尚未开始执行，不能只依赖它的 finally 回收辅助进程。
            if timestamp_repair:
                await timestamp_repair.close(cleanup_trace)
            #[DEBUG-START]
            if cleanup_trace:
                cleanup_trace.step('旧输出任务回收完成')
            #[DEBUG-END]
        if not sessions:
            self.video_streams.pop(websocket, None)

    async def extend_video_stream_buffer(self, websocket, data):
        """按前端水位请求放行同一个 FFmpeg 进程的后续数据。"""
        widget_id = data.get('widgetId', '')
        session = self.video_streams.get(websocket, {}).get(widget_id)
        if not session or data.get('streamId') != session.get('streamId'):
            return
        try:
            buffer_until = max(0.0, float(data.get('bufferUntil', 0) or 0))
        except (TypeError, ValueError):
            return
        duration = float(session.get('duration', 0) or 0)
        if duration > 0:
            buffer_until = min(buffer_until, duration)
        if buffer_until > session.get('bufferUntil', 0.0) + 0.05:
            session['bufferUntil'] = buffer_until
            session['flowEvent'].set()

    async def create_video_output_process(self, ffmpeg_path, video_path, start_time,
                                          source_audio_codec=None, transcode_audio=False,
                                          timestamp_repair=False, fragment_duration=2000000):
        """启动流复制进程；修复路径可在确认实际起点期间并行准备管道输出。"""
        command = [ffmpeg_path, '-hide_banner', '-loglevel', 'warning']
        if timestamp_repair:
            command.extend(['-ignore_editlist', '1', '-noaccurate_seek'])
        if start_time > 0:
            command.extend(['-ss', f'{start_time:.9f}'])
        command.extend([
            '-i', video_path,
            '-map', '0:v:0', '-map', '0:a:0?', '-sn', '-dn',
            '-c:v', 'copy'
        ])
        if timestamp_repair:
            command.extend(['-copypriorss', '1'])
        if transcode_audio:
            # 音频转码远轻于视频转码；不加 -re，让 FFmpeg 按缓冲水位尽快产出 AAC。
            # 统一采样到 48 kHz AAC-LC，避免 AMR 这类低采样率输入触发 AAC 码率上限。
            command.extend([
                '-c:a', 'aac', '-profile:a', 'aac_low',
                '-ar:a', '48000', '-b:a', '128k'
            ])
        elif source_audio_codec:
            command.extend(['-c:a', 'copy'])
        if source_audio_codec == 'aac' and not transcode_audio:
            # MPEG-TS 中的 AAC 通常采用 ADTS，比特流必须转换后才能写入 MP4。
            command.extend(['-bsf:a', 'aac_adtstoasc'])
        command.extend([
            '-avoid_negative_ts', 'make_zero',
            # 等首个媒体包经过 bitstream filter 后再写 moov，否则 TS/ADTS AAC
            # 的 esds 会缺少 AudioSpecificConfig，Chromium 将拒绝初始化段。
            '-movflags', 'frag_keyframe+empty_moov+default_base_moof+delay_moov',
            '-frag_duration', str(fragment_duration), '-f', 'mp4', 'pipe:1'
        ])
        return await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

    async def stream_ffmpeg_output(self, websocket, widget_id: str, stream_id: str,
                                   ffmpeg_path: str, video_path: str, start_time: float,
                                   source_audio_codec: Optional[str] = None,
                                   transcode_audio: bool = False):
        session = self.video_streams[websocket][widget_id]
        timestamp_repair = session.get('timestampRepair')
        process = None
        stderr_task = None
        #[DEBUG-START] 视频跳转耗时诊断，release时删掉
        seek_perf = session.get('debugSeekPerformance')
        debug_first_output = True
        debug_first_init = True
        debug_first_media = True
        if seek_perf:
            seek_perf.step('输出任务开始执行')
        #[DEBUG-END]
        try:
            process = session.get('process')
            if process is None:
                process = await self.create_video_output_process(
                    ffmpeg_path, video_path, start_time, source_audio_codec, transcode_audio)
            session['process'] = process
            #[DEBUG-START] 视频跳转耗时诊断，release时删掉
            if seek_perf:
                seek_perf.step('FFmpeg 输出进程就绪', pid=process.pid, prestarted=bool(timestamp_repair))
            #[DEBUG-END]

            async def collect_stderr():
                chunks = []
                while True:
                    chunk = await process.stderr.read(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    if sum(map(len, chunks)) > 65536:
                        chunks = chunks[-8:]
                return b''.join(chunks).decode('utf-8', errors='replace')

            stderr_task = asyncio.create_task(collect_stderr())
            sequence = 0

            mp4_buffer = bytearray()
            pending_boxes = []
            pending_box_types = []
            track_timescales = {}
            first_fragment_time = None

            async def send_segment(segment_type: str):
                nonlocal sequence, first_fragment_time
                #[DEBUG-START] 视频跳转耗时诊断，release时删掉
                nonlocal debug_first_init, debug_first_media
                #[DEBUG-END]
                payload = b''.join(pending_boxes)
                if not payload:
                    return
                #[DEBUG-START]
                debug_segment = bool(seek_perf and sequence <= 16)
                debug_stats = {}
                debug_ready_at = time.perf_counter()
                if debug_segment:
                    print(f'[视频分段耗时][{seek_perf.request_id}] 分片就绪 '
                          f'{dict(streamId=stream_id, sequence=sequence, segmentType=segment_type, bytes=len(payload), elapsedMs=(debug_ready_at-seek_perf.started)*1000)}')
                #[DEBUG-END]
                if segment_type == 'init':
                    if timestamp_repair:
                        timestamp_repair.init_segment(payload)
                    track_timescales.update(self.read_mp4_track_timescales(payload))
                    if not track_timescales:
                        raise ValueError('无法从 fMP4 初始化段读取轨道 timescale')
                elif segment_type == 'media':
                    fragment_time = self.read_mp4_fragment_start(payload, track_timescales)
                    if fragment_time is None:
                        raise ValueError('无法从 fMP4 媒体段读取 tfdt 时间')
                    if first_fragment_time is None:
                        first_fragment_time = fragment_time
                    media_offset = max(0.0, fragment_time - first_fragment_time)
                    fragment_time_in_video = start_time + media_offset
                    flow_event = session['flowEvent']
                    while fragment_time_in_video > session['bufferUntil'] + 0.05:
                        flow_event.clear()
                        # clear 和 wait 之间可能刚收到新的放行请求，必须重新检查。
                        if fragment_time_in_video <= session['bufferUntil'] + 0.05:
                            continue
                        await flow_event.wait()
                    #[DEBUG-START]
                    debug_repair_at = time.perf_counter()
                    debug_stats['flowWaitMs'] = (debug_repair_at - debug_ready_at) * 1000
                    #[DEBUG-END]
                    if timestamp_repair:
                        payload = await timestamp_repair.repair_segment(payload,
                            #[DEBUG-START]
                            debug_stats=debug_stats,
                            #[DEBUG-END]
                        )
                    #[DEBUG-START]
                    debug_stats['repairMs'] = (time.perf_counter() - debug_repair_at) * 1000
                    if debug_segment:
                        print(f'[视频分段耗时][{seek_perf.request_id}] 分片修复完成 '
                              f'{dict(streamId=stream_id, sequence=sequence, **debug_stats)}')
                    #[DEBUG-END]
                #[DEBUG-START]
                debug_send_at = time.perf_counter()
                #[DEBUG-END]
                await websocket.send(self.pack_video_chunk(
                    stream_id, widget_id, sequence, payload, segment_type
                ))
                #[DEBUG-START] 视频跳转耗时诊断，release时删掉
                if debug_segment:
                    debug_sent_at = time.perf_counter()
                    print(f'[视频分段耗时][{seek_perf.request_id}] 分片发送完成 '
                          f'{dict(streamId=stream_id, sequence=sequence, sendMs=(debug_sent_at-debug_send_at)*1000, elapsedMs=(debug_sent_at-seek_perf.started)*1000)}')
                if seek_perf and segment_type == 'init' and debug_first_init:
                    debug_first_init = False
                    seek_perf.step('首个初始化段发送完成', bytes=len(payload))
                if seek_perf and segment_type == 'media' and debug_first_media:
                    debug_first_media = False
                    seek_perf.step('首个媒体段发送完成', bytes=len(payload))
                #[DEBUG-END]
                sequence += 1
                pending_boxes.clear()
                pending_box_types.clear()

            async def process_boxes(boxes):
                for box_type, box in boxes:
                    # mfra 是文件末尾的随机访问索引，实时 MSE 播放不需要它。
                    if box_type == b'mfra':
                        continue
                    pending_boxes.append(box)
                    pending_box_types.append(box_type)
                    if box_type == b'moov':
                        await send_segment('init')
                    elif box_type == b'mdat' and b'moof' in pending_box_types:
                        await send_segment('media')

            while True:
                chunk = await process.stdout.read(256 * 1024)
                if not chunk:
                    break
                #[DEBUG-START] 视频跳转耗时诊断，release时删掉
                if seek_perf and debug_first_output:
                    debug_first_output = False
                    seek_perf.step('首次读到 FFmpeg 输出', bytes=len(chunk))
                #[DEBUG-END]
                mp4_buffer.extend(chunk)
                await process_boxes(self.extract_mp4_boxes(mp4_buffer))

            await process_boxes(self.extract_mp4_boxes(mp4_buffer, end_of_stream=True))
            if mp4_buffer:
                raise ValueError('FFmpeg 输出在 MP4 box 中途结束')
            if pending_boxes and any(box_type != b'mfra' for box_type in pending_box_types):
                raise ValueError('FFmpeg 输出包含不完整的 MP4 逻辑分段')

            return_code = await process.wait()
            stderr_text = await stderr_task
            if return_code == 0:
                await self.send_stream_json(
                    websocket, 'VIDEO_STREAM_ENDED', widgetId=widget_id, streamId=stream_id
                )
            else:
                error_line = stderr_text.strip().splitlines()[-1] if stderr_text.strip() else 'FFmpeg 退出'
                await self.send_stream_json(
                    websocket, 'VIDEO_STREAM_ERROR', widgetId=widget_id,
                    streamId=stream_id, error=error_line
                )
        except asyncio.CancelledError:
            #[DEBUG-START] 视频跳转耗时诊断，release时删掉
            if seek_perf:
                seek_perf.step('旧输出任务收到取消（含此前播放等待时间）')
            #[DEBUG-END]
            await self.stop_ffmpeg_process(process,
                #[DEBUG-START]
                trace=session.get('cancelTrace')
                #[DEBUG-END]
            )
            raise
        except Exception as e:
            await self.stop_ffmpeg_process(process,
                #[DEBUG-START]
                trace=session.get('cancelTrace')
                #[DEBUG-END]
            )
            #[DEBUG-START] 视频跳转耗时诊断，release时删掉
            if seek_perf:
                seek_perf.step('输出任务失败', error=str(e))
            #[DEBUG-END]
            await self.send_stream_json(
                websocket, 'VIDEO_STREAM_ERROR', widgetId=widget_id,
                streamId=stream_id, error=str(e)
            )
        finally:
            if timestamp_repair:
                await timestamp_repair.close(
                    #[DEBUG-START]
                    trace=session.get('cancelTrace')
                    #[DEBUG-END]
                )
            if stderr_task and not stderr_task.done():
                stderr_task.cancel()
            if stderr_task:
                try:
                    await stderr_task
                except (asyncio.CancelledError, Exception):
                    pass
            sessions = self.video_streams.get(websocket, {})
            current = sessions.get(widget_id)
            if current and current.get('streamId') == stream_id:
                sessions.pop(widget_id, None)
            if not sessions:
                self.video_streams.pop(websocket, None)

    async def start_video_stream(self, websocket, data):
        widget_id = data.get('widgetId', '')
        requested_start_time = max(0.0, float(data.get('startTime', 0) or 0))
        start_time = requested_start_time
        #[DEBUG-START] 视频跳转耗时诊断，release时删掉
        seek_perf = None
        if data.get('command') == 'SEEK_VIDEO_STREAM':
            seek_perf = VideoSeekPerformanceTrace(data.get('debugSeekId') or uuid.uuid4().hex)
            seek_perf.step('收到跳转请求', widgetId=widget_id, requestedTime=requested_start_time)
        #[DEBUG-END]
        await self.cancel_video_stream(websocket, widget_id,
            #[DEBUG-START]
            cleanup_trace=seek_perf
            #[DEBUG-END]
        )
        #[DEBUG-START] 视频跳转耗时诊断，release时删掉
        if seek_perf:
            seek_perf.step('旧任务与 FFmpeg 进程回收完成')
        #[DEBUG-END]
        stream_id = uuid.uuid4().hex
        preparation = {}
        timestamp_repair = None
        output_start_task = None
        prepared_process = None
        repair_handed_over = False
        self.video_preparations.setdefault(websocket, {})[widget_id] = preparation
        def is_current():
            return self.video_preparations.get(websocket, {}).get(widget_id) is preparation
        try:
            #[DEBUG-START]
            trace_token = VIDEO_SEEK_TRACE.set(seek_perf)
            #[DEBUG-END]
            try:
                video_path = self.resolve_video_path(data.get('rootPath'), data.get('videoPath'))
                ffmpeg_path = self.get_ffmpeg_path()
            finally:
                #[DEBUG-START]
                VIDEO_SEEK_TRACE.reset(trace_token)
                #[DEBUG-END]
                pass
            #[DEBUG-START] 视频跳转耗时诊断，release时删掉
            if seek_perf:
                seek_perf.step('路径与 FFmpeg 配置检查完成')
            #[DEBUG-END]
            policy = self.read_video_playback_policy(video_path)
            #[DEBUG-START]
            if seek_perf:
                seek_perf.step('播放策略读取完成')
            #[DEBUG-END]
            cache_key = self.video_metadata_key(ffmpeg_path, video_path)
            #[DEBUG-START]
            if seek_perf:
                seek_perf.step('媒体文件签名检查完成')
            #[DEBUG-END]
            if policy['force-buffered-playback']:
                #[DEBUG-START]
                repair_cache_hit = cache_key in self.video_repair_metadata_cache
                #[DEBUG-END]
                metadata = await self.cached_repair_metadata(cache_key, ffmpeg_path, video_path)
                timestamp_repair = MP4StreamTimestampRepair(video_path, metadata)
                #[DEBUG-START]
                if seek_perf:
                    seek_perf.step('修复样本表准备完成', cacheHit=repair_cache_hit)
                #[DEBUG-END]
                if not is_current():
                    return
            timestamp_result = 'streaming' if timestamp_repair else 'not-requested'
            preparation['mediaPath'] = video_path
            #[DEBUG-START]
            probe_cache_hit = cache_key in self.media_probe_cache
            if seek_perf:
                seek_perf.step('媒体探测缓存查询完成', cacheHit=probe_cache_hit)
            #[DEBUG-END]
            media_info = await self.cached_probe_video(cache_key, ffmpeg_path, video_path)
            if not is_current():
                return
            #[DEBUG-START] 视频跳转耗时诊断，release时删掉
            if seek_perf:
                seek_perf.step('媒体编码与时长探测完成', cacheHit=probe_cache_hit)
            #[DEBUG-END]
            if not media_info['videoSupported']:
                print(
                    f"[分类展示模块] 不支持的视频编码: {media_info['videoCodec']}，"
                    "不会启动流进程或发送二进制数据"
                )
                await self.send_stream_json(
                    websocket, 'VIDEO_STREAM_UNSUPPORTED', widgetId=widget_id,
                    streamId=stream_id, mediaType='video',
                    videoPath=data.get('videoPath'), videoCodec=media_info['videoCodec'],
                    supportedVideoCodecs=sorted(self.SUPPORTED_VIDEO_CODECS),
                    requestId=data.get('requestId'),
                    message='不支持该视频的视频编码格式'
                )
                return
            if media_info.get('audioTranscoded'):
                print(
                    f"[分类展示模块] 音频编码 {media_info['sourceAudioCodec']} "
                    "将实时转码为 AAC"
                )
            if media_info['duration'] > 0:
                start_time = min(start_time, max(0.0, media_info['duration'] - 0.1))
            if timestamp_repair:
                output_start_task = asyncio.create_task(self.create_video_output_process(
                    ffmpeg_path, video_path, start_time,
                    media_info.get('sourceAudioCodec'), media_info.get('audioTranscoded', False),
                    timestamp_repair=True,
                    fragment_duration=1000000 if data.get('command') == 'SEEK_VIDEO_STREAM' else 2000000))
                start_time = await timestamp_repair.start(ffmpeg_path, start_time)
                prepared_process = await asyncio.shield(output_start_task)
                #[DEBUG-START]
                if seek_perf:
                    seek_perf.step('修复流关键帧定位完成', actualTime=start_time)
                #[DEBUG-END]
            elif start_time > 0:
                #[DEBUG-START]
                index_state = self.video_index_state(cache_key, video_path)
                index_cache_hit = index_state == 'ready'
                index_error = self.video_keyframe_status.get(cache_key, {}).get('error')
                #[DEBUG-END]
                aligned_start_time = await self.cached_align_video_keyframe(
                    cache_key, ffmpeg_path, video_path, start_time)
                if media_info['duration'] > 0:
                    aligned_start_time = min(
                        aligned_start_time, max(0.0, media_info['duration'] - 0.1)
                    )
                if abs(aligned_start_time - start_time) > 0.05:
                    print(
                        f"[分类展示模块] Seek 从 {start_time:.3f}s "
                        f"对齐到视频关键帧 {aligned_start_time:.3f}s"
                    )
                start_time = aligned_start_time
                #[DEBUG-START] 视频跳转耗时诊断，release时删掉
                if seek_perf:
                    seek_perf.step('关键帧定位完成', actualTime=start_time, cacheHit=index_cache_hit,
                                   indexState=index_state, indexError=index_error)
                #[DEBUG-END]
            if not is_current():
                return
            await self.send_stream_json(
                websocket, 'VIDEO_STREAM_READY', widgetId=widget_id,
                videoPath=data.get('videoPath'), requestId=data.get('requestId'),
                playbackMode='timestamp-repair' if policy['force-buffered-playback'] else 'remux',
                timestampResult=timestamp_result,
                streamId=stream_id, startTime=start_time,
                requestedStartTime=requested_start_time,
                bufferHighWaterSeconds=self.VIDEO_STREAM_HIGH_WATER_SECONDS,
                **media_info
            )
            if not is_current():
                return
            initial_buffer_until = start_time + self.VIDEO_STREAM_HIGH_WATER_SECONDS
            #[DEBUG-START] 视频跳转耗时诊断，release时删掉
            if seek_perf:
                seek_perf.step('VIDEO_STREAM_READY 发送完成', streamId=stream_id)
            #[DEBUG-END]
            if media_info['duration'] > 0:
                initial_buffer_until = min(initial_buffer_until, media_info['duration'])
            session = {
                'streamId': stream_id,
                'mediaPath': video_path,
                'timestampRepair': timestamp_repair,
                'process': prepared_process,
                'task': None,
                'duration': media_info['duration'],
                'bufferUntil': initial_buffer_until,
                'flowEvent': asyncio.Event()
            }
            self.video_streams.setdefault(websocket, {})[widget_id] = session
            repair_handed_over = True
            #[DEBUG-START] 视频跳转耗时诊断，release时删掉
            if seek_perf:
                session['debugSeekPerformance'] = seek_perf
            #[DEBUG-END]
            if not timestamp_repair:
                self.ensure_video_keyframe_index(cache_key, ffmpeg_path, video_path)
            session['task'] = asyncio.create_task(self.stream_ffmpeg_output(
                websocket, widget_id, stream_id, ffmpeg_path, video_path, start_time,
                media_info.get('sourceAudioCodec'), media_info.get('audioTranscoded', False)
            ))
        except Exception as e:
            if not is_current():
                return
            #[DEBUG-START] 视频跳转耗时诊断，release时删掉
            if seek_perf:
                seek_perf.step('准备跳转失败', error=str(e))
            #[DEBUG-END]
            await self.send_stream_json(
                websocket, 'VIDEO_STREAM_ERROR', widgetId=widget_id,
                streamId=stream_id, error=str(e),
                videoPath=data.get('videoPath'), requestId=data.get('requestId')
            )
    
        finally:
            if timestamp_repair and not repair_handed_over:
                timestamp_repair.request_stop()
                # 取消准备时仍完整取得并回收两个进程，重复取消不打断清理。
                async def discard_preparation():
                    try:
                        if output_start_task is not None:
                            try:
                                process = await output_start_task
                            except Exception:
                                # 创建失败时没有进程句柄，保留原准备异常或取消结果。
                                return
                            await self.stop_ffmpeg_process(process, drain_stderr=True)
                    finally:
                        await timestamp_repair.close()
                await asyncio.shield(discard_preparation())
            if is_current():
                self.video_preparations[websocket].pop(widget_id, None)
                if not self.video_preparations[websocket]:
                    self.video_preparations.pop(websocket, None)

    def make_danmaku_data(self, remap_config_list, dm_dir):
        """根据重映射配置从dm_dir目录读取弹幕数据"""
        def get_time(item):
            time_val = item.get('time')
            if time_val is None:
                item['time'] = 0
                return 0
            try:
                return float(time_val)
            except (ValueError, TypeError):
                return 0

        def apply_time_filter(danmaku_list, time_filter):
            if not time_filter:
                return danmaku_list
            filtered = []
            for dm in danmaku_list:
                time = get_time(dm)
                start_time = time_filter[0][0]
                for range_start, range_end in time_filter:
                    if range_start < start_time:
                        start_time = range_start
                if start_time < 0:
                    start_time = 0 # 如果不希望将选择器选择范围的最早时间对齐到 0，那就额外加入一个负值范围
                dm['time'] = time - start_time
                for range_start, range_end in time_filter:
                    if range_start <= time <= range_end:
                        filtered.append(dm)
                        break
            return filtered

        def apply_remap(time, cut_time, add_time_list):
            if cut_time > 0:
                first_time = 2 * cut_time
                a = 1 / (4 * cut_time)
                if time < first_time:
                    time = a * time * time
                else:
                    time = time - cut_time

            if add_time_list:
                sorted_add_time = sorted(add_time_list, key=lambda x: x[0])
                for start, end in sorted_add_time:
                    if time > start:
                        time = time + (end - start)
            return time

        def process_config(input_file, config):
            with open(input_file, 'r', encoding='utf-8') as f:
                danmaku_list = json.load(f)
            time_filter = config.get('time_filter', [])
            cut_time = config.get('cut_time', 0)
            add_time = config.get('add_time', [])
            filtered = apply_time_filter(danmaku_list, time_filter)
            sorted_list = sorted(filtered, key=get_time)
            for item in sorted_list:
                time = get_time(item)
                time = apply_remap(time, cut_time, add_time)
                item['time'] = time
            return sorted_list

        def get_source_info(danmaku_list):
            src_dict = {}
            for dm in danmaku_list:
                src = dm.get('src', '未知')
                send_time = dm.get('send-time', 0)
                if src not in src_dict:
                    src_dict[src] = {'send_times': [], 'count': 0}
                src_dict[src]['send_times'].append(send_time)
                src_dict[src]['count'] += 1

            dm_src_list = []
            for name, data in src_dict.items():
                update_time = max(data['send_times']) if data['send_times'] else 0
                dm_src_list.append({
                    'name': name,
                    'url': '',
                    'update-time': update_time,
                    'dm-count': data['count']
                })
            return dm_src_list

        folder_path = os.path.abspath(dm_dir)
        config_list = remap_config_list
        print(f"[分类展示模块] 加载了 {len(config_list)} 个弹幕映射配置项\n")
        all_danmaku = []
        all_source_info = []

        for i, config in enumerate(config_list):
            dmsrc_file = config.get('dmsrc-file', '')
            print(f"[分类展示模块] [{i+1}/{len(config_list)}] 处理: {dmsrc_file}")

            input_file = os.path.join(folder_path, dmsrc_file)
            if not os.path.exists(input_file):
                print(f"[分类展示模块] 错误: 文件不存在 {input_file}")
                continue

            processed = process_config(input_file, config)
            print(f"[分类展示模块] 处理了 {len(processed)} 条弹幕")
            all_danmaku.extend(processed)

            source_info = get_source_info(processed)
            all_source_info.extend(source_info)

        all_danmaku = sorted(all_danmaku, key=get_time)
        print(f"[分类展示模块] 合并后共 {len(all_danmaku)} 条弹幕")

        build_time = int(time.time())

        dm_info = {
            'dm-src': all_source_info,
            'dmjs-build-time': build_time,
            'dm-count': len(all_danmaku)
        }
        info_file = os.path.join(folder_path, "dm-info.json")
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(dm_info, f, ensure_ascii=False, indent=4)
        print(f"[分类展示模块] 成功将弹幕信息写入 {info_file}")

        # 获取用户保存的弹幕配置
        danmaku_config = self.config.get('video-config', {}).get('danmaku-config', {
            'speed': 0.75,
            'fontsizeScale': 1.0,
            'area': 0.75
        })
        
        danmaku_option = {
            "speed": danmaku_config.get('speed', 0.75),
            "fontsizeScale": danmaku_config.get('fontsizeScale', 16),
            "area": danmaku_config.get('area', 0.75),
            "items": all_danmaku  
        }

        return danmaku_option

    def get_comment_config(self, updates=None):
        """取得评论面板配置；缺少默认项或有设置更新时写回配置文件。"""
        video_config = self.config.setdefault('video-config', {})
        config = video_config.setdefault('comment-config', {})
        changed = False
        for key, value in COMMENT_CONFIG_DEFAULTS.items():
            if key not in config:
                config[key] = value
                changed = True
        if updates:
            for key, value in updates.items():
                if key in COMMENT_CONFIG_DEFAULTS and config.get(key) != value:
                    config[key] = value
                    changed = True
        if changed:
            self.save_config()
        return dict(config)


    @staticmethod
    def read_comment_json(path, expected_type, default):
        if not os.path.isfile(path):
            return default
        try:
            with open(path, 'r', encoding='utf-8') as file:
                value = json.load(file)
            return value if isinstance(value, expected_type) else default
        except (OSError, json.JSONDecodeError) as error:
            print(f"[分类展示模块] 读取评论配置失败 {path}: {error}")
            return default

    @staticmethod
    def write_comment_json(path, value):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        temporary_path = path + '.tmp'
        with open(temporary_path, 'w', encoding='utf-8') as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
        os.replace(temporary_path, path)

    @staticmethod
    def inspect_comment_database(database_path):
        """读取来源元数据、评论数（main + top）以及回复数（reply）。"""
        path = Path(database_path).resolve()
        connection = _open_comment_database_readonly(path)
        try:
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            if not {'_metadata', 'main', 'reply'}.issubset(tables):
                raise ValueError('评论数据库缺少 _metadata、main 或 reply 表')
            metadata = dict(connection.execute(
                'SELECT metadata_key,metadata_value FROM _metadata'
            ))
            comment_count = int(connection.execute(
                'SELECT COUNT(*) FROM main'
            ).fetchone()[0])
            if 'top' in tables:
                comment_count += int(connection.execute(
                    'SELECT COUNT(*) FROM "top"'
                ).fetchone()[0])
            reply_count = int(connection.execute(
                'SELECT COUNT(*) FROM reply'
            ).fetchone()[0])
            return metadata, comment_count, reply_count
        finally:
            connection.close()

    @staticmethod
    def comment_created_timestamp(metadata):
        value = metadata.get('created_at_utc', '')
        if not value:
            return 0
        try:
            return int(datetime.datetime.fromisoformat(
                value.replace('Z', '+00:00')
            ).timestamp())
        except (ValueError, TypeError):
            return 0

    def collect_comment_info(self, metadata_path):
        """按 cmif -> cm-list -> 数据库回退顺序组装评论来源信息。"""
        # 重新打开评论面板/切换剧集后，下一页请求重新读取删除列表和统计。
        self.comment_page_connection_manager.query_cache = None
        config = self.get_comment_config()
        record_path = os.path.join(metadata_path, '__COMMENT-RECORD__.json')
        record = self.read_comment_json(record_path, dict, {})
        cmif_path = os.path.join(metadata_path, 'cmif.json')
        comment_dir = os.path.join(os.path.dirname(metadata_path), '__COMMENT__')
        update_dir = os.path.join(comment_dir, 'update')
        cm_list_path = os.path.join(comment_dir, 'cm-list.json')
        cmif = self.read_comment_json(cmif_path, list, [])
        if not cmif:
            return {
                'totalCount': 0,
                'sources': [],
                'config': config,
                'record': record,
                'metadataPath': metadata_path,
                'cmListPath': cm_list_path,
            }

        cm_list = self.read_comment_json(cm_list_path, dict, {})
        by_file_name = {
            str(value.get('file-name')): (bvid, value)
            for bvid, value in cm_list.items()
            if isinstance(value, dict) and value.get('file-name')
        }
        sources = []
        cm_list_changed = False
        for item in cmif:
            if not isinstance(item, dict):
                continue
            file_name = str(item.get('comment-srcfile', '')).strip()
            if not re.fullmatch(r'cm\d+\.db', file_name, re.I):
                continue
            database_path = os.path.realpath(os.path.join(comment_dir, file_name))
            if not os.path.isfile(database_path):
                print(f"[分类展示模块] 跳过不存在的评论数据库: {database_path}")
                continue

            bvid, list_entry = by_file_name.get(file_name, ('', {}))
            list_entry = dict(list_entry) if isinstance(list_entry, dict) else {}
            required_keys = {'update-time', 'comment-count', 'reply-count'}
            needs_database = not bvid or not required_keys.issubset(list_entry)
            metadata = {}
            if needs_database:
                try:
                    metadata, comment_count, reply_count = self.inspect_comment_database(
                        database_path
                    )
                except Exception as error:
                    print(f"[分类展示模块] 解析评论数据库失败 {database_path}: {error}")
                    continue
                bvid = bvid or str(metadata.get('bvid', ''))
                if not bvid:
                    print(f"[分类展示模块] 评论数据库缺少 bvid: {database_path}")
                    continue
                list_entry.update({
                    'file-name': file_name,
                    'aid': int(metadata.get('aid', 0) or 0),
                    'update-time': self.comment_created_timestamp(metadata),
                    'comment-count': comment_count,
                    'reply-count': reply_count,
                })
                cm_list[bvid] = list_entry
                by_file_name[file_name] = (bvid, list_entry)
                cm_list_changed = True

            source_name = str(list_entry.get('src-name', '') or '').strip()
            if not source_name:
                source_name = bvid
                list_entry['src-name'] = source_name
                cm_list[bvid] = list_entry
                by_file_name[file_name] = (bvid, list_entry)
                cm_list_changed = True
                print(
                    f"[分类展示模块] 评论来源缺少 src-name，"
                    f"已使用 BV 号补全: {bvid}"
                )

            resource_folder = str(item.get('resource-folder', '') or '').strip()
            basic_folder = str(item.get('basic-resfolder') or 'bilibili-resource')
            sources.append({
                'bvid': bvid,
                'databasePath': database_path,
                'updateDir': update_dir if os.path.isdir(update_dir) else '',
                'sourceName': source_name,
                'sourceType': str(item.get('src') or 'B站'),
                'commentCount': max(0, int(list_entry.get('comment-count', 0) or 0)),
                'replyCount': max(0, int(list_entry.get('reply-count', 0) or 0)),
                'updateTime': max(0, int(list_entry.get('update-time', 0) or 0)),
                'resource-folder': resource_folder,
                'basicResourceFolder': basic_folder,
                'fileName': file_name,
            })

        if cm_list_changed:
            self.write_comment_json(cm_list_path, cm_list)
        return {
            'totalCount': sum(source['commentCount'] for source in sources),
            'sources': sources,
            'config': config,
            'record': record,
            'metadataPath': metadata_path,
            'cmListPath': cm_list_path,
        }

    def set_comment_source_info(self, data):
        """修改 cm-list.json 中一个评论来源允许编辑的字段。"""
        cm_list_path = str(data.get('cmListPath', '') or '').strip()
        if not cm_list_path:
            raise ValueError('缺少 cm-list.json 路径')
        cm_list_path = os.path.realpath(os.path.abspath(
            os.path.normpath(cm_list_path)
        ))
        if os.path.basename(cm_list_path).lower() != 'cm-list.json':
            raise ValueError('评论来源信息文件必须为 cm-list.json')

        allowed_roots = [
            os.path.realpath(os.path.abspath(path))
            for path in self.global_config.get('base_dir', [])
        ]
        if allowed_roots and not any(
                self.is_path_within(root, cm_list_path) for root in allowed_roots):
            raise ValueError('cm-list.json 不在已配置的资源目录中')
        if not os.path.isfile(cm_list_path):
            raise FileNotFoundError(f'cm-list.json 不存在: {cm_list_path}')

        bvid = str(data.get('bvid', '') or '').strip()
        if not bvid:
            raise ValueError('缺少评论来源 BV 号')
        key = str(data.get('key', '') or '').strip()
        if key not in COMMENT_SOURCE_INFO_EDITABLE_KEYS:
            raise ValueError(f'不允许修改评论来源字段: {key or "(空)"}')
        value = str(data.get('value', '') or '').strip()
        if not value:
            raise ValueError('评论来源名称不能为空')
        if len(value) > 200:
            raise ValueError('评论来源名称不能超过 200 个字符')

        try:
            with open(cm_list_path, 'r', encoding='utf-8') as file:
                cm_list = json.load(file)
        except json.JSONDecodeError as error:
            raise ValueError(f'cm-list.json 格式错误: {error}') from error
        if not isinstance(cm_list, dict):
            raise ValueError('cm-list.json 顶层必须为字典')
        target = cm_list.get(bvid)
        if not isinstance(target, dict):
            raise ValueError(f'cm-list.json 中没有评论来源 {bvid}')

        target[key] = value
        self.write_comment_json(cm_list_path, cm_list)
        return {
            'cmListPath': cm_list_path,
            'bvid': bvid,
            'key': key,
            'value': value,
        }

    def load_comment_deletelist(self, database_path, update_dir):
        """读取 cmN.deletelist；缺失时从同来源全部增量数据库重建。"""
        if not update_dir:
            return set()
        update_dir = os.path.realpath(os.path.abspath(update_dir))
        expected_update_dir = os.path.realpath(os.path.join(
            os.path.dirname(database_path), 'update'
        ))
        if update_dir != expected_update_dir or not os.path.isdir(update_dir):
            return set()
        stem = os.path.splitext(os.path.basename(database_path))[0]
        deletelist_path = os.path.join(update_dir, stem + '.deletelist')
        if os.path.isfile(deletelist_path):
            values = self.read_comment_json(deletelist_path, list, [])
            return {
                int(value) for value in values
                if not isinstance(value, bool) and str(value).lstrip('-').isdigit()
            }

        deleted = set()
        pattern = re.compile(re.escape(stem) + r'-\d+\.db$', re.I)
        for name in sorted(os.listdir(update_dir)):
            if not pattern.fullmatch(name):
                continue
            delta_path = Path(update_dir, name).resolve()
            connection = _open_comment_database_readonly(delta_path)
            try:
                exists = connection.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' "
                    "AND name='_deleted_records'"
                ).fetchone()
                if exists:
                    deleted.update(
                        int(row[0]) for row in connection.execute(
                            'SELECT DISTINCT rpid FROM _deleted_records'
                        )
                    )
            finally:
                connection.close()
        self.write_comment_json(deletelist_path, sorted(deleted))
        return deleted

    def save_comment_read_record(self, metadata_path, bvid, page, page_count):
        record = {
            'view-time': int(time.time()),
            'last-read-src-BV': str(bvid or ''),
            'last-read-page': max(1, int(page)),
            'last-pagecount': min(max(1, int(page_count)), 200),
        }
        record_path = os.path.join(metadata_path, '__COMMENT-RECORD__.json')
        try:
            self.write_comment_json(record_path, record)
            return True
        except OSError as error:
            print(f"[分类展示模块] 保存评论阅读记录失败 {record_path}: {error}")
            return False

    def build_comment_html_response(self, data, perf=None):
        metadata_path = str(data.get('metadataPath', '') or '').strip()
        if not metadata_path:
            raise ValueError('缺少视频元数据文件夹路径')
        metadata_path = os.path.abspath(os.path.normpath(metadata_path))
        database_path = str(data.get('databasePath', '') or '').strip()
        if not database_path:
            raise ValueError('缺少评论数据库路径')
        database_path = os.path.abspath(os.path.normpath(database_path))
        if not re.fullmatch(r'cm\d+\.db', os.path.basename(database_path), re.I):
            raise ValueError('评论数据库文件名不符合 cm<number>.db 规则')
        normalized_database_path = os.path.normcase(database_path)
        allowed_roots = [
            os.path.normcase(os.path.abspath(os.path.normpath(path)))
            for path in self.global_config.get('base_dir', [])
        ]
        database_in_allowed_root = not allowed_roots
        for allowed_root in allowed_roots:
            try:
                if os.path.commonpath([
                    allowed_root, normalized_database_path
                ]) == allowed_root:
                    database_in_allowed_root = True
                    break
            except ValueError:
                continue
        if not database_in_allowed_root:
            raise ValueError('评论数据库不在已配置的资源目录中')
        sort_by = data.get('sortBy', 'time')
        if sort_by not in {'time', 'like'}:
            sort_by = 'time'
        page = max(1, int(data.get('page', 1) or 1))
        page_size = min(max(int(data.get('pageSize', 20) or 20), 1), 200)
        keyword = str(data.get('keyword', '') or '').strip()
        if not bool(data.get('keywordEnabled', bool(keyword))):
            keyword = ''
        mark_deleted = bool(data.get('markDeleted', False))
        only_deleted = bool(data.get('onlyDeleted', False))
        only_vip = bool(data.get('onlyVip', False))
        word_filter_enabled = bool(data.get('wordFilterEnabled', False))
        word_count = max(0, int(data.get('wordCount', 0) or 0))
        word_direction = 'below' if data.get('wordDirection') == 'below' else 'above'
        update_dir = str(data.get('updateDir', '') or '')
        #[DEBUG-START] 性能调试代码，release时删掉
        if perf:
            perf.step('解析路径和请求参数')
        #[DEBUG-END]
        if not update_dir:
            mark_deleted = False
            only_deleted = False
        needs_deleted = mark_deleted or only_deleted
        # 数据库连接及筛选准备缓存统一控制生命周期。仅缓存未命中才读取文件。
        deleted_loader = (
            lambda: self.load_comment_deletelist(database_path, update_dir)
        ) if needs_deleted else None
        query_scope = (
            data.get('widgetId', ''),
            CommentPageConnectionManager.normalize_path(metadata_path),
            CommentPageConnectionManager.normalize_path(update_dir) if update_dir else '',
            mark_deleted,
        )

        result = load_comment_page_from_database(
            database_path, sort_by, page, page_size,
            keyword=keyword,
            only_deleted=only_deleted,
            only_vip=only_vip,
            word_filter_enabled=word_filter_enabled,
            word_count=word_count,
            word_direction=word_direction,
            deleted_loader=deleted_loader,
            query_scope=query_scope,
            connection_manager=self.comment_page_connection_manager,
            perf=perf,
        )
        resource_root = str(data.get('resourcePath', '') or '').strip()
        if not resource_root:
            raise ValueError('缺少评论资源根目录路径')
        # resourcePath 来自 CS_COMMENT_INFO 返回的 resource-folder 计算结果。
        # 此处仅作不访问文件系统的字符串规范化，不检查其中的目录或资源文件。
        resource_root = os.path.abspath(os.path.normpath(resource_root))
        basic_folder = str(
            data.get('basicResourceFolder') or 'bilibili-resource'
        ).strip() or 'bilibili-resource'
        #[DEBUG-START] 性能调试代码，release时删掉
        if perf:
            perf.step('资源目录参数处理')
        #[DEBUG-END]
        result['html'] = build_comment_font_style(
            resource_root, basic_folder
        ) + ''.join(
            comment_to_comment_html(
                comment, resource_root, basic_folder,
                mark_deleted=mark_deleted,
            )
            for comment in result['comments']
        )
        #[DEBUG-START] 性能调试代码，release时删掉
        if perf:
            perf.step('生成 HTML 及资源 URL', htmlChars=len(result['html']))
        #[DEBUG-END]
        result.pop('comments', None)
        result['databasePath'] = database_path

        config_updates = {
            'sort-by': sort_by,
            'mark-deleted': mark_deleted,
            'only-deleted': only_deleted,
            'only-vip': only_vip,
            'word-filter-enabled': word_filter_enabled,
            'word-count': word_count,
            'word-direction': word_direction,
        }
        if bool(data.get('updatePageSizeDefault', False)):
            config_updates['page-size'] = page_size
        self.get_comment_config(config_updates)
        #[DEBUG-START] 性能调试代码，release时删掉
        if perf:
            perf.step('读取或保存评论配置')
        #[DEBUG-END]
        if bool(data.get('updateReadRecord', False)) \
                or result['page'] != result['requestedPage']:
            self.save_comment_read_record(
                metadata_path, data.get('bvid', ''), result['page'], page_size
            )
        #[DEBUG-START] 性能调试代码，release时删掉
        if perf:
            perf.step('按需保存阅读记录')
        #[DEBUG-END]
        return result



    ######################
    #以下实现必要的接口
    ######################

    async def when_connect(self, websocket):
        """视频与评论资源按需创建，连接建立时无需额外初始化。"""

    async def when_disconnect(self, websocket):
        """取消此连接下的全部视频请求与 FFmpeg 流。"""
        widget_ids = (set(self.video_streams.get(websocket, {})) | set(self.video_preparations.get(websocket, {}))
                      | set(self.video_request_tasks.get(websocket, {})))
        for widget_id in widget_ids:
            await self.cancel_video_stream(websocket, widget_id)

    async def shutdown(self):
        """回收视频任务、元数据缓存及评论数据库连接。"""
        connections = set(self.video_streams) | set(self.video_preparations) | set(self.video_request_tasks)
        for websocket in connections:
            await self.when_disconnect(websocket)
        self.video_preparations.clear()
        metadata_tasks = list(self.video_keyframe_tasks.values()) + list(self.media_probe_tasks.values())
        for task in metadata_tasks:
            task.cancel()
        await asyncio.gather(*metadata_tasks, return_exceptions=True)
        self.video_keyframe_cache.clear()
        self.media_probe_cache.clear()
        self.video_repair_metadata_cache.clear()
        self.comment_page_connection_manager.close()

    async def handle_message(self, websocket, data) -> bool:
        """处理视频、弹幕和评论消息；返回是否已处理。"""
        command = data.get('command')

        if command == 'GET_ANIME_PAGE':
            widget_id = data.get('widgetId', '')
            page = data.get('page', 1)
            page_size = data.get('pageSize', 10)
            sort_by = data.get('sortBy', 'year')
            sort_order = data.get('sortOrder', 'DESC')
            tag_filter_enabled = data.get('tagFilterEnabled', False)
            selected_tags = data.get('selectedTags', [])

            print(f"[分类展示模块] 收到获取番剧分页请求: page={page}, sortBy={sort_by}, sortOrder={sort_order}, tagFilter={tag_filter_enabled}")
            result = self.get_anime_page(page, page_size, sort_by, sort_order, tag_filter_enabled, selected_tags)

            message = json.dumps({
                'command': 'ANIME_PAGE_DATA',
                'widgetId': widget_id,
                'animeList': result['animeList'],
                'total': result['total'],
                'allTags': result['allTags'],
                'page': result['page'],
                'pageSize': result['pageSize'],
                'totalPages': result['totalPages']
            }, ensure_ascii=False)
            await websocket.send(message)
            print(f"[分类展示模块] 发送番剧分页数据，共 {len(result['animeList'])} 条")

        elif command == 'GET_ANIME_DETAIL':
            widget_id = data.get('widgetId', '')
            anime_id = data.get('animeId')
            print(f"[分类展示模块] 收到获取番剧详情请求: animeId={anime_id}")
            result = self.get_anime_detail(anime_id)
            message = json.dumps({
                'command': 'ANIME_DETAIL_DATA',
                'widgetId': widget_id,
                'animeDetail': result
            }, ensure_ascii=False)
            await websocket.send(message)
            print(f"[分类展示模块] 发送番剧详情数据")

        elif command in ('START_VIDEO_STREAM', 'SEEK_VIDEO_STREAM'):
            # 请求接收不能被全片解码阻塞，否则 CANCEL/切换剧集无法及时处理。
            widget_id = data.get('widgetId', '')
            previous = self.video_request_tasks.get(websocket, {}).get(widget_id)
            if previous:
                previous.cancel()
                await asyncio.gather(previous, return_exceptions=True)
            task = asyncio.create_task(self.start_video_stream(websocket, data))
            self.video_request_tasks.setdefault(websocket, {})[widget_id] = task
            def completed(done):
                tasks = self.video_request_tasks.get(websocket, {})
                if tasks.get(widget_id) is done:
                    tasks.pop(widget_id, None)
                if not tasks:
                    self.video_request_tasks.pop(websocket, None)
                if not done.cancelled():
                    done.exception()
            task.add_done_callback(completed)

        elif command == 'CANCEL_VIDEO_STREAM':
            await self.cancel_video_stream(websocket, data.get('widgetId', ''))

        elif command == 'BUFFER_VIDEO_STREAM':
            await self.extend_video_stream_buffer(websocket, data)

        elif command == 'GET_CS_VIDEO_DATA':
            widget_id = data.get('widgetId', '')
            root_path = data.get('rootPath')
            video_path = data.get('videoPath')
            print(f"[分类展示模块] 收到获取视频数据请求: rootPath={root_path}, videoPath={video_path}")
            
            playback_policy = {'force-buffered-playback': False, 'buffered-playback-reason': None,
                               'video-stream': '', 'compat_file': ''}
            try:
                resolved_video = self.resolve_video_path(root_path, video_path)
                playback_policy = self.read_video_playback_policy(resolved_video)
                if playback_policy['compat_file']:
                    playback_policy['compat_file'] = os.path.relpath(
                        playback_policy['compat_file'], os.path.realpath(root_path)).replace(os.sep, '/')
            except (OSError, ValueError, TypeError):
                pass
            danmaku_data = []
            has_danmaku = False
            auto_seek_time = 0
            if root_path and video_path:
                dm_dir = os.path.join(root_path, f'{video_path}@meta')
                dmcf_json_path = os.path.join(dm_dir, 'rmcf.json')
                
                if os.path.exists(dmcf_json_path):
                    try:
                        with open(dmcf_json_path, 'r', encoding='utf-8') as f:
                            remap_config = json.load(f)
                        danmaku_data = self.make_danmaku_data(remap_config, dm_dir)
                        has_danmaku = True
                        print(f"[分类展示模块] 读取 rmcf.json 成功")
                    except Exception as e:
                        print(f"[分类展示模块] 读取 rmcf.json 失败: {e}")
                
                # 读取观看记录
                record_path = os.path.join(dm_dir, '__RECORD__.json')
                if os.path.exists(record_path):
                    try:
                        with open(record_path, 'r', encoding='utf-8') as f:
                            record_data = json.load(f)
                        if 'video-time' in record_data:
                            auto_seek_time = record_data['video-time']
                        print(f"[分类展示模块] 读取观看记录成功: {auto_seek_time}")
                    except Exception as e:
                        print(f"[分类展示模块] 读取 __RECORD__.json 失败: {e}")

            message = json.dumps({
                'command': 'CS_VIDEO_DATA',
                'widgetId': widget_id,
                'has-danmaku': has_danmaku,
                'danmaku-data': danmaku_data,
                'auto-seek-time': auto_seek_time,
                'videoPath': video_path,
                'requestId': data.get('requestId'),
                **playback_policy
            }, ensure_ascii=False)
            await websocket.send(message)

        elif command == 'CS_GET_COMMENT_INFO':
            widget_id = data.get('widgetId', '')
            request_id = data.get('requestId', '')
            try:
                metadata_path = str(data.get('metadataPath', '') or '').strip()
                if not metadata_path:
                    raise ValueError('缺少视频元数据文件夹路径')
                metadata_path = os.path.abspath(os.path.normpath(metadata_path))
                result = self.collect_comment_info(metadata_path)
                message = {
                    'command': 'CS_COMMENT_INFO',
                    'widgetId': widget_id,
                    'requestId': request_id,
                    **result,
                }
                print(
                    f"[分类展示模块] 发送评论来源信息，共 "
                    f"{len(result['sources'])} 个来源、{result['totalCount']} 条评论"
                )
            except Exception as error:
                print(f"[分类展示模块] 获取评论来源信息失败: {error}")
                message = {
                    'command': 'CS_COMMENT_ERROR',
                    'widgetId': widget_id,
                    'requestId': request_id,
                    'stage': 'info',
                    'error': str(error),
                }
            await websocket.send(json.dumps(message, ensure_ascii=False))

        elif command == 'CS_GET_COMMENT_HTML':
            widget_id = data.get('widgetId', '')
            request_id = data.get('requestId', '')
            #[DEBUG-START] 性能调试代码，release时删掉
            perf = CommentPerformanceTrace(request_id) if COMMENT_PERF_DEBUG else None
            #[DEBUG-END]
            try:
                result = self.build_comment_html_response(data,
                #[DEBUG-START] 性能调试代码，release时删掉
                 perf=perf
                #[DEBUG-END]
                 )
                if result['page'] != result['requestedPage']:
                    await websocket.send(json.dumps({
                        'command': 'CS_COMMENT_SETPAGE',
                        'widgetId': widget_id,
                        'requestId': request_id,
                        'page': result['page'],
                        'totalPages': result['totalPages'],
                    }, ensure_ascii=False))
                message = {
                    'command': 'CS_COMMENT_HTML',
                    'widgetId': widget_id,
                    'requestId': request_id,
                    **result,
                }
                print(
                    f"[分类展示模块] 发送第 {result['page']}/"
                    f"{result['totalPages']} 页评论 HTML"
                )
            except Exception as error:
                print(f"[分类展示模块] 生成评论 HTML 失败: {error}")
                message = {
                    'command': 'CS_COMMENT_ERROR',
                    'widgetId': widget_id,
                    'requestId': request_id,
                    'stage': 'html',
                    'error': str(error),
                }
            payload = json.dumps(message, ensure_ascii=False)
            #[DEBUG-START] 性能调试代码，release时删掉
            if perf:
                perf.step('响应组装及 JSON 序列化', chars=len(payload),
                          command=message['command'])
            #[DEBUG-END]
            try:
                await websocket.send(payload)
            finally:
                #[DEBUG-START] 性能调试代码，release时删掉
                if perf:
                    perf.step('WebSocket send 等待')
                    perf.report()
                #[DEBUG-END]
                pass

        elif command == 'CS_SET_COMMENT_SOURCEINFO':
            widget_id = data.get('widgetId', '')
            request_id = data.get('requestId', '')
            try:
                result = self.set_comment_source_info(data)
                message = {
                    'command': 'CS_COMMENT_SOURCEINFO_SET',
                    'widgetId': widget_id,
                    'requestId': request_id,
                    **result,
                }
                print(
                    f"[分类展示模块] 已更新评论来源 "
                    f"{result['bvid']} 的 {result['key']}"
                )
            except Exception as error:
                print(f"[分类展示模块] 修改评论来源信息失败: {error}")
                message = {
                    'command': 'CS_COMMENT_ERROR',
                    'widgetId': widget_id,
                    'requestId': request_id,
                    'stage': 'source-info',
                    'error': str(error),
                }
            await websocket.send(json.dumps(message, ensure_ascii=False))

        elif command == 'SAVE_WATCH_RECORD':
            widget_id = data.get('widgetId', '')
            root_path = data.get('rootPath')
            video_path = data.get('videoPath')
            video_time = data.get('videoTime', 0)
            episode_order = data.get('episodeOrder', 0)
            print(f"[分类展示模块] 收到保存观看记录请求: rootPath={root_path}, videoPath={video_path}, videoTime={video_time}, episodeOrder={episode_order}")
            
            success = False
            if root_path and video_path:
                try:
                    dm_dir = os.path.join(root_path, f'{video_path}@meta')
                    
                    # 确保目录存在
                    os.makedirs(dm_dir, exist_ok=True)
                    
                    # 保存 __RECORD__.json
                    record_path = os.path.join(dm_dir, '__RECORD__.json')
                    record_data = {
                        'view-time': int(time.time()),
                        'video-time': video_time
                    }
                    with open(record_path, 'w', encoding='utf-8') as f:
                        json.dump(record_data, f, ensure_ascii=False, indent=2)
                    
                    # 保存 __HISTORY__.json
                    history_path = os.path.join(root_path, '__HISTORY__.json')
                    history_data = {
                        'order': episode_order,
                        'path': video_path,
                        'view-time': int(time.time()),
                        'video-time': video_time
                    }
                    with open(history_path, 'w', encoding='utf-8') as f:
                        json.dump(history_data, f, ensure_ascii=False, indent=2)
                    
                    print(f"[分类展示模块] 观看记录保存成功")
                    success = True
                except Exception as e:
                    print(f"[分类展示模块] 保存观看记录失败: {e}")
            
            message = json.dumps({
                'command': 'WATCH_RECORD_SAVED',
                'widgetId': widget_id,
                'success': success
            }, ensure_ascii=False)
            await websocket.send(message)

        elif command == 'GET_DANMAKU_CONFIG':
            widget_id = data.get('widgetId', '')
            print("[分类展示模块] 收到获取弹幕配置请求")
            # 获取弹幕配置，不存在则使用默认值
            danmaku_config = self.config.get('video-config', {}).get('danmaku-config', {
                'speed': 0.75,
                'fontsizeScale': 1.0,
                'area': 0.75
            })
            message = json.dumps({
                'command': 'DANMAKU_CONFIG',
                'widgetId': widget_id,
                'danmakuConfig': danmaku_config
            }, ensure_ascii=False)
            await websocket.send(message)
            print("[分类展示模块] 发送弹幕配置")

        elif command == 'SET_DANMAKU_CONFIG':
            widget_id = data.get('widgetId', '')
            danmaku_config = data.get('danmakuConfig', {})
            print(f"[分类展示模块] 收到设置弹幕配置请求: {danmaku_config}")
            # 确保配置结构存在
            if 'video-config' not in self.config:
                self.config['video-config'] = {}
            self.config['video-config']['danmaku-config'] = danmaku_config
            # 保存配置
            self.save_config()
            message = json.dumps({
                'command': 'DANMAKU_CONFIG_SAVED',
                'widgetId': widget_id,
                'success': True
            }, ensure_ascii=False)
            await websocket.send(message)
            print("[分类展示模块] 弹幕配置保存成功")

        else:
            return False
        return True

def classify_shower_check_ffmpeg(ffmpeg_path: str):
    """返回 (是否可用, 说明)，检测组件并实际执行视频复制、音频转码及管道输出。

    不要求视频编码器：播放器只复制视频。微型 H.264 样本是一帧 16x16
    黑色视频（SPS/PPS/IDR），检测过程不读取用户媒体，也不使用 ffprobe。
    """
    def run(arguments, payload=None):
        result = subprocess.run(
            [ffmpeg_path, '-hide_banner', '-nostdin'] + arguments,
            input=payload, stdin=subprocess.DEVNULL if payload is None else None,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        if result.returncode:
            raise ValueError(result.stderr.decode('utf-8', errors='replace')[-1500:]
                             or f'FFmpeg 返回 {result.returncode}')
        return result.stdout

    try:
        if not isinstance(ffmpeg_path, str) or not os.path.isfile(ffmpeg_path):
            return False, '可执行文件不存在'
        version = run(['-version']).decode('utf-8', errors='replace').splitlines()
        if not version or not version[0].startswith('ffmpeg version '):
            return False, '该文件不是 FFmpeg'

        # 按组件名称而非描述判断，兼容同一解码器的整数/浮点实现。
        demuxers = run(['-demuxers']).decode('utf-8', errors='replace')
        available = set()
        for line in demuxers.splitlines():
            match = re.match(r'\s*D\s+(\S+)\s', line)
            if match:
                available.update(match.group(1).split(','))
        missing = {'mov', 'matroska', 'avi', 'mpegts', 'mpeg', 'flv', 'asf', 'ogg', 'rm'} - available
        if missing:
            return False, '缺少容器读取支持：' + ', '.join(sorted(missing))
        decoders = run(['-decoders']).decode('utf-8', errors='replace')
        available = set(re.findall(r'^\s*A[.A-Z]{5}\s+(\S+)', decoders, re.MULTILINE))
        for alternatives in ({'aac', 'aac_fixed'}, {'mp3', 'mp3float'}, {'ac3', 'ac3_fixed'},
                             {'opus', 'libopus'}, {'amrnb', 'libopencore_amrnb'},
                             {'amrwb', 'libopencore_amrwb'}, {'pcm_s16le'}):
            if not alternatives & available:
                return False, '缺少音频解码器：' + '/'.join(sorted(alternatives))

        with tempfile.TemporaryDirectory(prefix='classify-ffmpeg-check-') as temp:
            video = Path(temp) / 'sample.h264'
            video.write_bytes(bytes.fromhex(
                '000000016742c00ad91ec044000003000400000300123c489920'
                '0000000168cb83cb200000000165888404bc98a00038a380'))
            inputs = ['-loglevel', 'error', '-r', '2', '-i', str(video), '-f', 's16le',
                      '-ar', '8000', '-ac', '1', '-i', 'pipe:0',
                      '-map', '0:v:0', '-map', '1:a:0', '-sn', '-dn', '-c:v', 'copy',
                      '-c:a', 'aac', '-profile:a', 'aac_low', '-ar:a', '48000', '-b:a', '128k']
            fragments = ['-avoid_negative_ts', 'make_zero', '-movflags',
                         'frag_keyframe+empty_moov+default_base_moof+delay_moov',
                         '-frag_duration', '2000000', '-f', 'mp4', 'pipe:1']
            # Seek 探测使用 debug_ts 和 null 输出，不要求解码/重新编码视频。
            run(['-loglevel', 'info', '-debug_ts', '-i', str(video),
                 '-map', '0:v:0', '-an', '-c', 'copy', '-frames:v', '1',
                 '-f', 'null', 'pipe:1'])
            # 8 kHz PCM -> 48 kHz AAC-LC；H.264 保持流复制。
            output = run(inputs + fragments, b'\0' * 8000)
            for marker in (b'ftyp', b'moov', b'avcC', b'esds', b'moof', b'mdat'):
                if marker not in output:
                    return False, 'fMP4 管道输出不完整：缺少 ' + marker.decode()
            # 模拟 TS/ADTS AAC 输入，验证播放器的 aac_adtstoasc 复制路径。
            transport = run(inputs + ['-f', 'mpegts', 'pipe:1'], b'\0' * 8000)
            output = run(['-loglevel', 'error', '-f', 'mpegts', '-i', 'pipe:0',
                          '-map', '0:v:0', '-map', '0:a:0?', '-c', 'copy',
                          '-bsf:a', 'aac_adtstoasc'] + fragments, transport)
            if not all(marker in output for marker in (b'avcC', b'esds', b'moof', b'mdat')):
                return False, 'TS/AAC 重封装输出不完整'
        return True, version[0]
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return False, str(exc)


def classify_shower_download_ffmpeg() -> str:
    """下载普通静态构建，验证后安装到本模块 config/use/ffmpeg 目录。"""
    system, machine = platform.system(), platform.machine().lower()
    # 来源均列于 https://ffmpeg.org/download.html 。不用系统包管理器或管理员权限。
    if system == 'Windows' and machine in ('amd64', 'x86_64'):
        url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
    elif system == 'Linux' and machine in ('amd64', 'x86_64', 'aarch64', 'arm64'):
        architecture = 'linux64' if machine in ('amd64', 'x86_64') else 'linuxarm64'
        url = ('https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/'
               f'ffmpeg-master-latest-{architecture}-gpl.tar.xz')
    elif system == 'Darwin' and machine in ('amd64', 'x86_64'):
        url = 'https://evermeet.cx/ffmpeg/getrelease/zip'
    else:
        raise ValueError(f'暂不支持自动下载 {system}/{machine} 构建，请手动准备本平台的 FFmpeg')

    destination = Path(__file__).resolve().parent / 'config' / 'use' / 'ffmpeg'
    destination.mkdir(parents=True, exist_ok=True)
    executable_name = 'ffmpeg.exe' if system == 'Windows' else 'ffmpeg'
    print(f'正在下载 FFmpeg：{url}，请稍候……')
    with tempfile.TemporaryDirectory(prefix='download-', dir=destination) as temp:
        archive = Path(temp) / 'archive'
        request = Request(url, headers={'User-Agent': 'HamsterStorageManager/1.0'})
        with urlopen(request, timeout=60) as response, archive.open('wb') as target:
            shutil.copyfileobj(response, target)
        executable = Path(temp) / executable_name
        # 只读取目标二进制到固定路径，不按压缩包中的路径解压（避免路径穿越/符号链接）。
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as package:
                members = [m for m in package.infolist()
                           if not m.is_dir() and m.filename.split('/')[-1] == executable_name]
                if len(members) != 1:
                    raise ValueError('下载包中没有唯一的 FFmpeg 可执行文件')
                with package.open(members[0]) as source, executable.open('wb') as target:
                    shutil.copyfileobj(source, target)
        else:
            with tarfile.open(archive, 'r:*') as package:
                members = [m for m in package.getmembers()
                           if m.isfile() and m.name.split('/')[-1] == executable_name]
                if len(members) != 1:
                    raise ValueError('下载包中没有唯一的 FFmpeg 可执行文件')
                with package.extractfile(members[0]) as source, executable.open('wb') as target:
                    shutil.copyfileobj(source, target)
        executable.chmod(0o755)
        valid, reason = classify_shower_check_ffmpeg(str(executable))
        if not valid:
            raise ValueError('下载的 FFmpeg 不可用：' + reason)
        installed = destination / executable_name
        os.replace(executable, installed)
    return str(installed)


def settings():
    """安装向导：依次检查配置、PATH、用户输入或下载的 FFmpeg，并保存路径。"""
    backend_dir = Path(__file__).resolve().parent
    config_path = backend_dir / 'config' / 'classify_shower_config.json'
    try:
        with config_path.open('r', encoding='utf-8') as file:
            config = json.load(file)
    except FileNotFoundError:
        config = {'custom-class': {}, 'video-config': {
            'danmaku-config': {}, 'ffmpeg-path': '', 'comment-config': {}}}
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open('x', encoding='utf-8') as file:
            json.dump(config, file, ensure_ascii=False, indent=2)
    # 损坏的配置明确报错，不覆盖用户已有的分类、弹幕或评论配置。
    if not isinstance(config, dict):
        raise ValueError('classify_shower_config.json 的根节点必须是对象')
    video_config = config.setdefault('video-config', {})
    if not isinstance(video_config, dict):
        raise ValueError('video-config 必须是对象')

    def check_path(value):
        if not isinstance(value, str) or not value.strip():
            return None
        value = os.path.expandvars(os.path.expanduser(value.strip().strip('"').strip("'")))
        try:
            path = Path(value)
            if not path.is_absolute():
                path = backend_dir / path
            path = str(path.resolve())
        except (OSError, ValueError, RuntimeError) as exc:
            print(f'路径无效：{exc}')
            return None
        print(f'正在验证 FFmpeg：{path}')
        valid, reason = classify_shower_check_ffmpeg(path)
        print(('验证通过：' if valid else '验证失败：') + reason)
        return path if valid else None

    ffmpeg_path = check_path(video_config.get('ffmpeg-path'))
    if not ffmpeg_path:
        system_path = shutil.which('ffmpeg')
        if system_path:
            ffmpeg_path = check_path(os.path.abspath(system_path))
    while not ffmpeg_path:
        value = input('请输入 FFmpeg 可执行文件路径，或直接回车下载普通版（Ctrl+C 取消）：').strip()
        if value:
            ffmpeg_path = check_path(value)
        else:
            try:
                ffmpeg_path = classify_shower_download_ffmpeg()
            except (OSError, ValueError, EOFError, HTTPException, tarfile.TarError, zipfile.BadZipFile) as exc:
                print(f'下载失败：{exc}，请重试或输入已有可执行文件路径。')

    video_config['ffmpeg-path'] = ffmpeg_path
    # 原子替换，避免保存中断时留下半个 JSON 文件。
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=config_path.parent,
                                         suffix='.tmp', delete=False) as file:
            temporary_path = Path(file.name)
            json.dump(config, file, ensure_ascii=False, indent=2)
            file.write('\n')
        os.replace(temporary_path, config_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    print(f'FFmpeg 已配置：{ffmpeg_path}')
