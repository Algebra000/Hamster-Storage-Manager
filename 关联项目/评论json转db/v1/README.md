# B 站评论 JSON → SQLite（v1 快照版）

这一版面向“同一个视频在不同时间抓取评论后，快速比较两个快照”的用途。它不追求逐字节还原输入 JSON，而是把评论数据拆成便于索引和比较的表。

当前数据库内部结构版本为 `v1.1`。删除 `_present_keys` 和 `_main_rpid` 前生成的旧 v1 数据库，以及 `_volatile_hash` 尚未覆盖 `reply_control` 的早期 v1.1 数据库，都需要重新转换，不能与新快照混合比较。比较器会根据 `_metadata.volatile_fields` 拒绝混用不同哈希口径的数据库。

## 表结构

- `main`：普通顶层评论。JSON 的一级键各自成为列；`replies` 不入表。`reply_control` 仅保留 `max_line`、`location`、`translation_switch`、`support_share` 四个键，并保存为紧凑 JSON 字符串。
- `top`：置顶顶层评论，列结构和处理规则与 `main` 相同。下载器读取接口的 `top_replies`；JSON 转换器则把带 `is_top: true` 的条目放入此表。置顶评论不会在 `main` 中重复保存。
- `reply`：`replies` 中递归展开的回复，列结构与 `main` 相同。原始 `parent` 表示直接父回复，原始 `root` 表示根评论；楼中楼场景下两者不一定相等。
- `member`：每条评论的用户快照。`parent` 是引用它的评论 `rpid`，也是本表主键。同一个用户发布两条评论时会产生两行，不会按 `mid` 合并。
- `content`：每条评论的内容快照，`parent` 规则与 `member` 相同。
- `_metadata`：保存结构版本、源文件 SHA-256、生成时间和行数，便于确认两个数据库的来源。

`main`、`top`、`reply` 的 `member`、`content` 都保存对应子表的 `parent`。除这两个特殊对象外，字典和列表使用紧凑 JSON 文本直接存储；标量尽量保存为 SQLite 的原生值。为兼容已经生成的 v1.1 数据库，`member._comment_kind` 和 `content._comment_kind` 中的 `top` 实体仍记为 `main`，实际归属可由同一 `parent` 是否位于 `top` 表判断。

内部列 `_volatile_hash` 和 `_data_hash` 用于快速筛选变化行。这些列以下划线开头，不属于 B 站返回的业务字段。`_volatile_hash` 刻意只覆盖 `count`、`rcount`、`state`、`fansgrade`、`attr`、`like`、`action`、`invisible`、`reply_control` 九个关注字段；其中 `reply_control` 使用四键过滤后的入库字符串计算，不受 `time_desc` 影响。

## 生成两个快照

```powershell
python json_to_sqlite.py ..\example.json -o 1.db
python json_to_sqlite.py 新抓取的评论.json -o 2.db
```

输出文件已存在时，只有显式添加 `--overwrite` 才会覆盖。

## 快速比较

```powershell
python compare_databases.py 1.db 2.db -o changes.json
```

比较器通过 SQLite `ATTACH DATABASE` 同时挂载两个数据库：先利用 `rpid`/`parent` 主键和哈希找到新增、删除及疑似变化的行，再只读取变化行的完整字段。`main`、`top`、`reply` 详细比较 `count`、`rcount`、`state`、`fansgrade`、`attr`、`like`、`action`、`invisible`、`reply_control`；`member` 和 `content` 比较全部字段。比较早期没有 `top` 表的 v1.1 数据库时，缺少的 `top` 表按空表处理。

## 判断“删评”的前提

只有两次抓取的对象、排序/游标范围、分页深度和回复展开范围完全一致，而且两次抓取都成功完成时，`2.db` 中缺失的 `rpid` 才能可靠地解释为删评或被隐藏。如果第二次抓取漏页、提前结束、接口只返回热门评论，缺失行也会出现在 `removed` 中，但那不是数据库结构能够独自判定的真实删评。
