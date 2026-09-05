# classify_shower 模块介绍

## 一、模块概述

classify_shower（分类展示模块）是仓鼠存储管理器的核心功能模块之一，用于分类展示库中的8种资源类型。模块采用前后端分离架构，前端负责界面展示与用户交互，后端负责数据处理与数据库管理。

### 资源分类

| 分类名称 | 图标 | 描述 |
|---------|------|------|
| 视频 | cs_video_svg_string | 相册、番剧、电影等 |
| 图片 | cs_image_svg_string | 照片、漫画、画作等 |
| 音频 | cs_audio_svg_string | 录音、音乐等 |
| 项目 | cs_project_svg_string | 程序项目、作业项目等 |
| 电子书 & 文献 | cs_book_svg_string | 小说、教材、论文等 |
| 网页 & 笔记 | cs_web_svg_string | 网页杂物、笔记等 |
| 软件 & 游戏 | cs_game_svg_string | 系统镜像、软件、galgame等 |
| 其他 | cs_other_svg_string | 聊天记录、特殊意义文件等 |

---

## 二、已实现功能

### 2.1 主界面（分类选择页）

**前端实现：** `classifyShowerInit()` 函数

- 8个分类项以网格/ flex布局展示
- 每个分类项包含：SVG图标、名称、描述
- 鼠标悬停动画效果（背景变浅 + 轻微上浮）
- 点击分类项进入对应板块

### 2.2 番剧板块

#### 2.2.1 侧边栏

**前端实现：** `CS_AnimeWidget` 类

- **排序方式选择框**：支持按年份(y=year)、按入库时间(y=entry_time)、按拼音首字母(y=pinyin)
- **正序/逆序切换**：滑块按钮控制，`sortOrder` 参数（asc/desc）
- **标签筛选**：
  - 勾选框启用/禁用筛选
  - 输入框显示已选标签（逗号分隔）
  - OK按钮应用筛选
  - "选择标签"按钮弹出大菜单框
- **标签选择菜单**：
  - 显示所有标签（按拼音首字母排序）
  - 正选/反选模式切换
  - 确定按钮确认选择
- **刷新数据库按钮**：触发后端重新扫描目录

**后端实现：** `ClassifyShowerModule` 类

- `get_anime_list()` - 获取番剧列表
- `get_all_tags()` - 获取所有标签
- `scan_anime_category()` - 扫描番剧目录重建数据库

#### 2.2.2 主展示区

**前端实现：** `CS_AnimeWidget` 类

- 海报展示区：两行五列，共10个番剧卡片
- 每个卡片包含：
  - 海报图片（毛玻璃容器 + object-fit:contain）
  - 番剧名称（较大字体）
  - 年份和标签（较小字体，溢出省略号）
- 搜索框 + 搜索按钮
- 分页框：显示当前页/总页数，支持点击页码或"下一页"换页

#### 2.2.3 番剧详情页

**前端实现：** `CS_AnimeDetailWidget` 类

- 返回按钮（圆形图标，蓝底白图标）
- 内容区域：居中白色半透明圆角容器（70%宽度）
- 左侧：海报图片
- 右侧信息区：
  - 番剧名称
  - 时间（年/月，未知显示"时间未知"）
  - 全部标签（蓝色标签样式）
  - 简介标题 + 简介内容（无简介显示"无简介"）
  - 简介来源（存在时显示链接）
  - 弹幕状态（粉红色"有弹幕" / 灰色"无弹幕"）
  - 弹幕来源标签（蓝底白字）
  - 剧集按钮列表

**剧集按钮样式：**
- 尺寸：120px宽度，12px内边距
- 布局：两行（左对齐）
  - 第一行：集数（大号深色粗体）
  - 第二行：剧集名（小号浅灰色）
- 右上角弹幕标记（粉底白字"有弹幕"）
- 无名称时集数居中显示
- 悬停效果：白色→蓝色渐变，0.3s过渡

**后端实现：** `get_anime_detail()` 方法

- 从数据库读取基本信息
- 从 `__MD__.json` 读取元数据
- 检测弹幕文件（`xxx.files/dm.js`）
- 收集弹幕来源（从 `xxx.files/dm-info.json`）
- 处理剧集列表（支持 episode-map 自定义映射）

---

## 三、未实现功能

### 3.1 相册板块

图片资源的分类展示功能尚未实现。目前仅有视频（番剧）板块的完整实现。

### 3.2 其他7个资源板块

除番剧外的其他7个分类（图片、音频、项目、电子书、网页、软件游戏、其他）仅有主界面入口，尚未实现各自的具体功能模块。

### 3.3 自定义分类功能

根据 `后端设计.txt`，计划支持用户自定义分类（中类、小类），但尚未实现。

### 3.4 视频播放集成

详情页的剧集按钮点击后应跳转到视频播放界面，但目前仅有按钮样式，尚未实现点击事件处理和视频播放功能。

### 3.5 搜索功能

前端有搜索框UI，但搜索功能（`GET_ANIME_BY_NAME` 命令）尚未在后端实现。

---

## 四、数据结构

### 4.1 数据库表

#### anime 表
```sql
CREATE TABLE IF NOT EXISTS anime (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    root_path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    name_pinyin TEXT DEFAULT '',
    year INTEGER,
    month INTEGER,
    cover_path TEXT,
    episode_count INTEGER DEFAULT 0,
    entry_time INTEGER DEFAULT 0
)
```

#### tag 表
```sql
CREATE TABLE IF NOT EXISTS tag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    pinyin TEXT DEFAULT ''
)
```

#### anime_tag 关联表
```sql
CREATE TABLE IF NOT EXISTS anime_tag (
    anime_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (anime_id, tag_id),
    FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE
)
```

### 4.2 __MD__.json 结构
```json
{
    "type": "番剧",
    "name": "番剧名称",
    "names": ["别名1", "别名2"],
    "cover": "./cover.webp",
    "item": ["标签1", "标签2"],
    "year": 2021,
    "month": 1,
    "entry-time": 12345678,
    "introduction": "简介内容",
    "introduction-src": {
        "src-name": "来源名称",
        "src-url": "来源链接"
    },
    "episode-map": [
        {"order": 1, "path": "视频路径.mp4", "name": "集名"}
    ]
}
```

---

## 五、前后端通信协议

### 5.1 命令列表

| 命令名 | 方向 | 功能 | 参数 |
|--------|------|------|------|
| GET_ANIME_PAGE | 前端→后端 | 获取番剧分页数据 | page, pageSize, sortBy, sortOrder, tags |
| ANIME_PAGE_DATA | 后端→前端 | 返回番剧分页数据 | animeList, total, allTags |
| GET_ANIME_ALL_TAGS | 前端→后端 | 获取所有标签 | - |
| ANIME_ALL_TAGS | 后端→前端 | 返回所有标签 | tags[] |
| REBUILD_DATABASE | 前端→后端 | 重建数据库 | - |
| DATABASE_REBUILD_COMPLETE | 后端→前端 | 重建完成通知 | - |
| GET_ANIME_DETAIL | 前端→后端 | 获取番剧详情 | animeId |
| ANIME_DETAIL_DATA | 后端→前端 | 返回番剧详情 | animeDetail对象 |
| GET_ANIME_BY_NAME | 前端→后端 | 搜索番剧 | name |
| SCAN_ANIME_CATEGORY | 前端→后端 | 扫描番剧目录 | - |

### 5.2 消息格式

```javascript
// 发送格式
{
    command: "命令名",
    widgetId: "组件唯一标识",
    ...其他参数
}

// 接收格式
{
    command: "响应命令名",
    widgetId: "组件唯一标识",
    ...数据字段
}
```

---

## 六、页面布局与样式

### 6.1 页面管理

使用 `frame.js` 提供的页面栈管理：

- `new_page()` - 创建新页面，压入页面栈
- `pop_page(num)` - 弹出页面，触发清理回调
- 每个页面拥有 `classify_shower_cleanFuncList` 数组存储清理函数

### 6.2 详情页布局

```
+------------------------------------------+
|                              [返回][主页] |  <- 返回菜单栏（绝对定位右上角）
|                                          |
|   +----------------------------------+   |
|   |                                  |   |
|   |  [海报]    名称                   |   |  <- 白色半透明容器
|   |           时间 |标签|标签|...     |   |     70%宽度居中
|   |           -------------------    |   |
|   |           简介                   |   |
|   |           来源链接               |   |
|   |           -------------------    |   |
|   |           弹幕 状态 来源: [标签]  |   |
|   |           -------------------    |   |
|   |           剧集                   |   |
|   |           [第1集][第2集][...     |   |
|   |                                  |   |
|   +----------------------------------+   |
|                                          |
+------------------------------------------+
```

---

## 七、模块文件结构

```
项目根目录/
├── backend/
│   └── classify_shower_back.py      # 后端模块
│       ├── ClassifyShowerModule     # 主类
│       ├── get_anime_list()         # 获取番剧列表
│       ├── get_anime_detail()        # 获取番剧详情
│       ├── scan_anime_category()     # 扫描目录
│       ├── cleanup_missing_anime()   # 清理失效条目
│       ├── get_pinyin()             # 拼音转换
│       └── load_pinyin_dict()       # 加载拼音字典
│   └── pinyin.txt                   # 拼音字典文件
│
├── frontend/
│   └── classify_shower.js           # 前端模块
│       ├── cs_*_svg_string          # SVG图标常量
│       ├── cs_CLASSIFICATIONS        # 分类数据
│       ├── classifyShowerInit()     # 初始化函数
│       ├── CS_AnimeWidget            # 番剧列表组件
│       └── CS_AnimeDetailWidget     # 番剧详情组件
│
└── design/
    └── classify_shower/
        ├── classify_shower模块介绍.txt  # 本文档
        ├── 后端设计.txt                 # 后端设计说明
        └── 页面设计.txt                 # 页面设计说明
```

---

## 八、待办事项

- [ ] 实现图片（相册）板块
- [ ] 实现其他7个资源板块
- [ ] 实现自定义分类功能（config/classify_shower_config.json）
- [ ] 实现剧集按钮点击跳转视频播放
- [ ] 实现番剧搜索功能（GET_ANIME_BY_NAME）
- [ ] 添加标签选择菜单的滚动条和正选/反选逻辑
- [ ] 完善数据库迁移机制
- [ ] 添加错误处理和加载状态提示
