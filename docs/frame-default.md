# FRAME DEFAULT v1.0.0 开发文档

## <span style="color: blue;">▎</span> 概述

该js文件是仓鼠存储管理器的**基础布局模块**，适用于 ROLAND、TIPHERETH 版本。该模块负责管理页面布局、区域分配、页面栈以及模块生命周期。

## <span style="color: blue;">▎</span> 使用方法

在 HTML 中所有功能模块前引入该模块，即可开始使用。

```html
<head>
    ......
    <script src="frame.js"></script>
    ......(各种功能模块)......
</head>
```
在使用前，确保已加载该模块。

## <span style="color: blue;">▎</span> 架构设计

### 核心概念

| 概念 | 说明 |
|------|------|
| **固定区域** | 页面上预设3个显示区域，用于放置不同的功能模块 |
| **临时区域** | 支持动态创建区域，用于特殊场景的临时展示 |
| **页面管理栈** | 管理多个页面的切换，支持页面的压入和弹出 |
| **模块生命周期** | 通过回调函数管理模块的显示/隐藏状态切换 |

### 布局结构

```
┌─────────────────────────────────────────────────────────────┐
│                        #upbar                              │
│  (顶部导航栏，默认高度60px)                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    block-0 (区域0)                  │   │
│  │  位置：左上角，宽度100%-40px，高度50%-60px          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────┐  ┌─────────────────────┐   │
│  │      block-2 (区域2)        │  │    block-1 (区域1)  │   │
│  │ 位置：左下角，宽度100%-300px │  │ 位置：右下角        │   │
│  │ 高度：50%-60px              │  │ 宽度：240px         │   │
│  │                             │  │ 高度：50%-60px      │   │
│  └─────────────────────────────┘  └─────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## <span style="color: blue;">▎</span> 标准 API 参考

本布局模块提供区域、页面栈、通知和菜单栏等接口，接口约定见[布局模块标准](总设计文档/模块化设计思路.md#布局模块)。

### 必要接口

#### 1. `get_block(index)`

获取指定索引的区域元素

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| index | number | 是 | 区域索引，0-2为固定区域，>=3为临时区域 |

**返回值：** `HTMLElement | null` - 区域元素或 null

**示例：**
```javascript
const block0 = get_block(0); // 获取第一个固定区域
const tempBlock = get_block(3); // 获取第一个已经通过create_new_block注册的临时区域
```

#### 2. `set_when_show(index, callback)`

设置区域显示时的回调函数

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| index | number | 是 | 区域索引 |
| callback | function | 是 | 显示时执行的回调函数 |

**示例：**
```javascript
set_when_show(0, () => {
    console.log('区域0即将显示');
    // 初始化模块逻辑
});
```

**回调执行**
传入的这个回调函数会在以下几种时刻执行：

1. 与后端连接成功后，随即执行所有固定区域的活跃回调。
2. 调用show_module激活指定区域的模块时，执行该区域的活跃回调。
3. 调用pop_page并返回到根页面时，执行所有固定区域的活跃回调。
4. 断开连接时会调用一次pop_page返回根页面，因此也会执行一次活跃回调。

#### 3. `set_when_hide(index, callback)`

设置区域隐藏时的回调函数

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| index | number | 是 | 区域索引 |
| callback | function | 是 | 隐藏时执行的回调函数 |

**示例：**
```javascript
set_when_hide(0, () => {
    console.log('区域0即将隐藏');
    // 清理模块资源
});
```

**回调执行**
传入的这个回调函数会在以下三种时刻执行：

1. 调用hide_module休眠指定区域的模块时，执行该区域的睡眠回调。
2. 调用new_page时，一定会执行所有固定区域的睡眠回调。

#### 4. `create_new_block(block)`

注册一个临时区域

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| block | HTMLElement | 是 | 要注册的区域元素 |

**返回值：** `number` - 分配的区域索引，失败返回 -1

**示例：**
```javascript
const tempDiv = document.createElement('div');
tempDiv.style.cssText = 'width: 300px; height: 200px;';
const index = create_new_block(tempDiv); // 返回 3
```

#### 5. `show_module(index)`

激活指定区域的模块（执行活跃回调）

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| index | number | 是 | 区域索引 |

**示例：**
```javascript
show_module(0); // 激活区域0的模块
```

#### 6. `hide_module(index)`

休眠指定区域的模块（执行睡眠回调）

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| index | number | 是 | 区域索引 |

**示例：**
```javascript
hide_module(0); // 休眠区域0的模块
```

#### 7. `new_page()`

创建新页面并压入页面栈

**返回值：** `HTMLElement` - 新建的空白页元素

**行为：**
- 隐藏当前页面
- 创建新的全屏页面
- 隐藏 upbar
- 执行所有固定区域的睡眠回调

**示例：**
```javascript
const newPage = new_page();
newPage.innerHTML = '<h1>新页面内容</h1>';
```

#### 8. `pop_page(num)`

从页面栈弹出指定数量的页面

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| num | number | 是 | 要弹出的页面数量 |

**返回值：** `number` - 实际弹出的页面数量

**行为：**
- 执行弹出页面的清理函数（cleanFuncList）
- 显示新的当前页面
- 如果回到根页面，显示 upbar 并执行所有固定区域的活跃回调

**示例：**
```javascript
pop_page(1); // 弹出一个页面
pop_page(256); // 弹出所有页面，回到根页面
```

### 必要的对象

#### `cleanFuncList`

new_page()返回页面对象的属性，它是一个清理函数列表，在使用pop_page()弹出页面时会依次执行。

**使用方式：**
```javascript
const page = new_page();
page.cleanFuncList.push(() => {
    // 清理资源，如销毁播放器、移除事件监听器等
    player.destroy();
});
```

## <span style="color: blue;">▎</span> 执行顺序与生命周期管理

### 主html被打开时的执行顺序

```
......(所有模块加载完毕)
        ↓
页面加载完成
		↓
按顺序执行onload_func_list里的函数
最先执行frame.js注册的函数，清空#main元素并建立所有固定区域
并将其添加到#main元素里
		↓
尝试连接后端
		↓
成功连接后端
		↓
console.log('连接成功');
		↓
遍历执行when_connect_func_list里的函数
		↓
执行frame.js注册到when_connect_func_list的函数
		↓
执行所有固定区域使用set_when_show注册的活跃回调  
        ↓
    ......
```


### 模块生命周期流程图

```
模块注册
    ↓
set_when_show() / set_when_hide()
    ↓
show_module(index)
    ↓
执行 when_show_callback
    ↓
模块活跃状态
    ↓
hide_module(index) / 页面切换
    ↓
执行 when_hide_callback
    ↓
模块休眠状态
```

## <span style="color: blue;">▎</span> 初始化机制

### 页面加载时

```javascript
// 如果存在 onload_func_list，则注册到加载列表
if (typeof onload_func_list !== 'undefined') {
    onload_func_list.push(initLayout);
} else {
    // 否则直接监听页面加载
    window.addEventListener('load', initLayout);
}
```

### 连接成功时

```javascript
// 如果存在 when_connect_func_list
when_connect_func_list.push(() => {
    // 激活所有固定区域的模块
    for (let i = 0; i < BLOCK_COUNT; i++) {
        if (when_show_callback_list[i]) {
            when_show_callback_list[i]();
            block_show_list[i] = true;
        }
    }
});
```

### 断开连接时

```javascript
// 如果存在 when_disconnect_func_list
when_disconnect_func_list.push(() => {
    // 弹出所有页面，回到根页面
    pop_page(page_stack.length - 1);
});
```

## <span style="color: blue;">▎</span>最佳实践

### 1. 模块注册模式

```javascript
// 在模块初始化时注册生命周期回调
class MyModule {
    constructor() {
        this.blockIndex = 0; // 使用区域0
        this.init();
    }
    
    init() {
        set_when_show(this.blockIndex, () => this.onShow());
        set_when_hide(this.blockIndex, () => this.onHide());
    }
    
    onShow() {
        // 初始化DOM、绑定事件、发起数据请求
        const block = get_block(this.blockIndex);
        block.innerHTML = '<div>模块内容</div>';
    }
    
    onHide() {
        // 清理DOM、移除事件监听器、取消请求
        const block = get_block(this.blockIndex);
        block.innerHTML = '';
    }
}
```

### 2. 新页面创建模式

```javascript
function openPlayerPage(videoPath) {
    const page = new_page();
    
    // 创建播放器容器
    const playerContainer = document.createElement('div');
    playerContainer.id = 'player-container';
    page.appendChild(playerContainer);
    
    // 添加清理函数
    page.cleanFuncList.push(() => {
        // 销毁播放器
        if (window.player) {
            window.player.destroy();
            window.player = null;
        }
    });
    
    // 初始化播放器
    window.player = createPlayer(playerContainer, videoPath);
}
```

### 3. 临时区域使用模式

```javascript
function showModal(content) {
    // 创建模态框元素
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 400px;
        padding: 20px;
        background: white;
        border-radius: 8px;
        z-index: 1000;
    `;
    modal.innerHTML = content;
    
    // 注册为临时区域
    const index = create_new_block(modal);
    
    // 添加关闭按钮
    const closeBtn = document.createElement('button');
    closeBtn.textContent = '关闭';
    closeBtn.onclick = () => {
        // 移除临时区域
        modal.remove();
        // 注意：临时区域需要手动管理生命周期
    };
    modal.appendChild(closeBtn);
    
    document.body.appendChild(modal);
    return index;
}
```


## <span style="color: blue;">▎</span>注意事项

1. **区域索引范围**：固定区域索引为 0-2，临时区域从 3 开始自动分配
2. **清理函数**：新页面的清理函数应添加到 `cleanFuncList`，确保资源被正确释放
3. **回调执行时机**：`show_module` 和 `hide_module` 会检查当前状态，避免重复执行。

## <span style="color: blue;">▎</span> 兼容性

- 支持现代浏览器（Chrome、Firefox、Safari、Edge）
- 需要 ES6+ 支持

---

*文档版本：v1.0.0*  
*适用于：ROLAND、TIPHERETH 版本的仓鼠存储管理器*  
*最后更新：2026年5月*


## 全局菜单栏

菜单栏为功能模块提供统一的页面操作入口，由 `frontend/frame.js` 实现。它包含基础页面菜单和外加按钮列表：基础页面菜单显示“返回上一页”和“回首页”两个按钮，外加按钮由功能模块按需要提供。各菜单栏分别保存自己的按钮列表，图标、业务点击逻辑由功能模块决定，布局模块负责挂载、排列和列表变动动画。公共约定见[布局模块标准](总设计文档/模块化设计思路.md#布局模块)。

### 创建菜单栏与基础按钮

功能模块在页面容器准备好后调用 `createBackButtons(container)`。该方法创建菜单栏元素，把两个基础按钮插入其中，再将菜单栏挂到 `container` 并返回菜单栏元素。容器需提供定位上下文，例如设置 `position: relative`；后续增删按钮使用这里返回的对象作为 `menuBar` 参数。

菜单栏采用绝对定位，距容器顶部10px、右侧20px，层级为100。背景为浅蓝半透明色，圆角20px，带阴影，上下内边距8px、左右12px。两个基础按钮均为40×40px的蓝色圆形按钮，使用30×30px白色 SVG 图标，间隔10px。鼠标移入时颜色加深并缩放到1.05倍，移出时恢复。

`createBackButtons()` 的内部函数 `createIconButton()` 创建按钮并绑定点击和悬停行为。当前返回按钮调用 `pop_page(1)`；首页按钮实际调用 `pop_page(256)`，最多弹出256页，页面栈保留根页面。布局标准要求首页操作回到根页面，因此当前数值写法在可弹出页面超过256个时不能保证到达根页面。这是现有实现与标准的差异。

### 外加按钮的排列与插入

`frameMenuButtons` 是以菜单栏元素为键、按钮数组为值的 WeakMap。创建菜单栏时为它登记空数组，基础按钮不计入数组。外加按钮位于菜单栏背景左侧，宽高均为40px、顶部距菜单栏8px；索引0最靠近菜单栏，后续索引依次向左排列。索引为 `index` 的按钮使用 `right: calc(100% + 10px + index * 50px)` 对应的位置，其中50px为40px按钮宽度加10px间距。

调用 `insertMenuButton(menuBar, index, button)` 时，布局模块先检查菜单栏登记和索引范围，再把 HTML 元素 `button` 挂到菜单栏，设置插入位置并加入数组。索引允许为0到当前数组长度，方法返回插入的元素。插入后调用 `layoutMenuButtons()` 重新排列，原位置及后续按钮向左移动50px，之前的按钮保持原位。

例如列表原为 `[A, B]`，A最靠近菜单栏，B在A左侧。在索引1插入C后，列表成为 `[A, C, B]`，A不动，B向左移动50px，为C腾出位置。`appendMenuButton(menuBar, button)` 取得当前数组长度后调用插入方法，因此追加按钮出现在最左侧，返回值同样是该元素。

### 移除按钮与查询索引

`removeMenuButton(menuBar, index)` 从数组中取出指定位置的元素，取消它尚未完成的位置动画，将它从 DOM 中移除，再重新排列剩余按钮，最后返回被移除元素。例如从 `[A, C, B]` 移除索引1，B向右移动50px，列表恢复为 `[A, B]`。移除不会清除元素上的业务监听器，调用方可以把返回的元素移动到其他容器，或重新加入菜单栏。

`getMenuButtonIndex(menuBar, button)` 查询元素当前在该菜单栏数组中的位置；未登记菜单栏或元素不在列表中时返回-1。由于其他模块可能改变列表，移除前应重新查询索引。模块应通过接口移除已登记按钮，再改变其归属，避免数组中的记录与 DOM 不一致。

插入、追加、移除接口收到未登记菜单栏时抛出 `TypeError`。插入的按钮不是 HTML 元素、已经存在于目标数组中，或仍挂在另一菜单栏且已登记在其数组中时，也抛出 `TypeError`。插入和移除的索引必须是整数：插入允许等于数组长度，移除必须小于数组长度；越界或不是整数时抛出 `RangeError`。

### 列表变动动画与生命周期

`layoutMenuButtons()` 先读取剩余按钮各自的屏幕横坐标，再取消旧动画并根据新索引设置最终位置，随后重新读取横坐标。两次位置之差作为动画的初始横向位移，逐渐过渡到0，时长240毫秒，缓动为 `ease-out`。这种处理使按钮在 DOM 已处于最终布局时，仍从操作前的可见位置平滑移动过去；连续操作时也从当前显示的位置开始。

位置动画使用 `translate` 属性，按钮悬停缩放使用 `transform`，两者分别控制位移与缩放。只有位置发生变化且元素提供 `animate()` 方法时才创建动画，否则直接呈现最终布局。`frameMenuAnimations` 以按钮元素为键保存最近的动画，供下一次排列或移除时取消。

列表和动画记录都保存在 WeakMap 中，不依靠全局强引用长期保留已退出页面的元素。移除按钮只处理 DOM 归属与位置动画，模块注册在全局列表或其他长期对象上的业务监听器仍由模块通过页面 `cleanFuncList` 清理。

### 评论按钮的接入

评论入口通过 `insertMenuButton(menuBar, 0, commentPanel)` 成为第一个外加按钮。评论组件展开面板前查询按钮当前索引，调用 `removeMenuButton()` 后将同一元素移入播放器右侧；收起时重新插入索引0。布局模块负责其余按钮的240毫秒移位，评论组件负责自身420毫秒的面板形变及播放器布局动画。

```javascript
const menuBar = createBackButtons(container);
const button = document.createElement('button');
button.textContent = '筛选';
button.title = '筛选内容';
appendMenuButton(menuBar, button);
const index = getMenuButtonIndex(menuBar, button);
if (index >= 0) removeMenuButton(menuBar, index);
```