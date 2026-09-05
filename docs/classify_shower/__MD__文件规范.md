# __MD__.json 文件规范

本文档描述了分类展示模块（classify_shower）中使用的 `__MD__.json` 文件格式规范。

---

## 番剧文件夹的__MD__规范

### 文件位置

`__MD__.json` 文件必须位于番剧文件夹的根目录下。

### 文件格式

JSON 格式，UTF-8 编码。

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string \| string[] | 是 | 类型标识。值为 `"番剧"` 或包含 `"番剧"` 的列表（如 `["番剧", "动漫电影"]`） |
| name | string | 是 | 番剧正式名称 |
| names | string[] | 否 | 别名列表（简称、俗称等） |
| cover | string | 否 | 封面图片路径。支持相对路径（相对于番剧文件夹）或绝对路径 |
| item | string[] | 否 | 标签/分类列表 |
| introduction | string | 否 | 作品简介 |
| introduction-src | object | 否 | 简介来源信息 |
| introduction-src.src-name | string | 否 | 来源名称（如 `"维基百科"`） |
| introduction-src.src-url | string | 否 | 来源链接 |
| year | number | 是 | 年份 |
| month | number | 否 | 月份（1-12） |
| entry-time | number | 是 | 入库时间戳（Unix 时间戳，单位：秒） |
| episode-map | object[] | 否 | 剧集映射列表（用于自定义剧集顺序） |
| episode-map[].order | number | 否 | 剧集序号 |
| episode-map[].path | string | 否 | 视频文件名 |
| episode-map[].name | string | 否 | 剧集名称 |

### 详细说明

#### 1. type 字段

`type` 字段用于标识文件夹类型。分类展示模块会识别以下两种情况：

- 字符串类型：`"番剧"`
- 列表类型：包含 `"番剧"` 的列表，如 `["番剧", "动漫电影"]`

只要满足任一情况，该文件夹就会被识别为番剧文件夹。

#### 2. item 字段

`item` 字段是标签列表，用于给番剧分类。标签会被保存到数据库中，并用于筛选功能。

标签处理逻辑：
- 标签会自动去除首尾空白
- 空标签会被忽略
- 重复标签会被自动去重

#### 3. cover 字段

`cover` 字段用于指定封面图片。

- 支持相对路径（如 `"./cover.webp"`）
- 支持绝对路径
- 如果未指定，系统会尝试使用文件夹内的默认封面

#### 4. introduction-src 字段

`introduction-src` 字段用于记录简介的来源信息，示例：

```json
{
    "src-name": "维基百科",
    "src-url": "https://zh.wikipedia.org/wiki/..."
}
```

#### 5. episode-map 字段

`episode-map` 字段用于自定义剧集的显示顺序和名称。如果未提供，系统会按文件名排序并自动编号。

示例：

```json
{
    "episode-map": [
        {
            "order": 1,
            "path": "ep01.mp4",
            "name": "第一集 序章"
        },
        {
            "order": 2,
            "path": "ep02.mp4",
            "name": "第二集 开端"
        }
    ]
}
```

---

### 完整示例

#### 示例 1：基础版本

```json
{
    "type": "番剧",
    "name": "葬送的芙莉莲 第二季",
    "names": [],
    "cover": "./FrierenS2.png",
    "item": ["异世界", "故事", "冒险"],
    "introduction": "北宇治字幕组简日内嵌版本。资源来自kisssub.org(爱恋动漫)",
    "year": 2026,
    "month": 3,
    "entry-time": 1777388003
}
```

#### 示例 2：包含简介来源和别名

```json
{
    "type": "番剧",
    "name": "回复术士的重启人生",
    "names": ["棍勇", "棍之勇者成名录"],
    "cover": "./cover.webp",
    "item": ["猎奇", "16+", "暗黑"],
    "introduction": "《回复术士的重启人生》（日语：回復術士のやり直し）是日本作家月夜泪在成为小说家吧上连载的网络小说，以及其后由KADOKAWA的角川Sneaker文库出版的轻小说。故事讲述拥有治愈能力、但遭冒险队伍凌辱虐待的少年凯亚尔，因缘际会返回成为【愈】之勇者前的时间点，向曾经加害自己与亲友的仇人复仇的经历。",
    "introduction-src": {
        "src-name": "维基百科",
        "src-url": "https://zh.wikipedia.org/wiki/%E5%9B%9E%E5%BE%A9%E8%A1%93%E5%A3%AB%E7%9A%84%E9%87%8D%E5%95%9F%E4%BA%BA%E7%94%9F"
    },
    "year": 2021,
    "entry-time": 12345678
}
```

#### 示例 3：类型为列表

```json
{
    "type": ["番剧", "动漫电影"],
    "name": "超时空辉夜姬!(H264)",
    "names": ["超时空辉夜姬"],
    "cover": "./cover.webp",
    "item": ["百合", "催泪", "H264"],
    "introduction": "《超时空辉夜姬！》（日语：超かぐや姫！ 英语：Cosmic Princess Kaguya!）是Studio Colorido与STUDIO CHROMATO制作的原创网络动画电影，于2026年1月22日由网飞独占上映，并有小说、漫画等衍生作品。资源来自kisssub.org(爱恋动漫)",
    "year": 2026,
    "month": 1,
    "entry-time": 1777390003
}
```

---

### 后端处理逻辑

1. **数据库存储字段**
   - `root_path`: 番剧文件夹路径
   - `name`: 番剧名称（来自 `name` 字段）
   - `name_pinyin`: 拼音首字母（自动生成）
   - `year`: 年份
   - `month`: 月份
   - `cover_path`: 封面路径
   - `episode_count`: 剧集数（自动统计）
   - `entry_time`: 入库时间戳

2. **标签处理**
   - 标签保存到 `tag` 表
   - 番剧与标签的关联保存到 `anime_tag` 表
   - 使用 `INSERT OR IGNORE` 避免重复标签

3. **剧集统计**
   - 自动统计文件夹下的视频文件数量
   - 支持的视频格式：`.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`

4. **动态读取**
   - 除数据库存储的字段外，其他字段（`introduction`、`introduction-src`、`episode-map` 等）在请求番剧详情时从 `__MD__.json` 动态读取
