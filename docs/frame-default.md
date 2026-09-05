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

本布局模块严格遵循布局模块API规范，实现了8个必要接口。

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
