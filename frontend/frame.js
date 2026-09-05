/**
* FRAME DEFAULT v1.0.0
* 基础布局模块，适用于 ROLAND、TIPHERETH 版本的仓鼠存储管理器。
* 使用时请确保在 HTML 中引入该模块。
* 将屏幕划分为3个区域
* 文档详见 frame-default.md
*/

// 固定区域数量
const BLOCK_COUNT = 3;

// 区域元素数组
let blocks = [];

// 页面管理栈
let page_stack = [];
let current_page_index = -1;

// 获取upbar元素
let upbar = null;

/**
* 初始化布局
*/
function initLayout() {
    // 获取upbar元素
    upbar = document.getElementById('upbar');
    
    // 获取主容器
    const main = document.getElementById('main');
    if (!main) {
        console.error('布局模块：无法找到主容器');
        return;
    }
    
    // 设置主容器样式
    main.style.position = 'relative';
    main.style.width = '100vw';
    main.style.minHeight = '100vh';
    main.style.paddingTop = '60px'; // 为 #upbar 留出空间
    main.style.boxSizing = 'border-box';
    //main.style.opacity = '0.85';
    main.style.backgroundColor = 'rgba(248, 248, 255, 0.65)';
    main.style.zIndex = '10';
    
    // 清空主容器
    main.innerHTML = '';
    
    // 创建3个区域
    for (let i = 0; i < BLOCK_COUNT; i++) {
        const block = document.createElement('div');
        block.id = `block-${i}`;
        block.style.backgroundColor = 'rgba(255, 255, 255, 0.35)';
        block.style.border = '1px solid #ddd';
        block.style.borderRadius = '4px';
        block.style.padding = '10px';
        block.style.boxSizing = 'border-box';
        block.style.overflow = 'auto';
        
        main.appendChild(block);
        blocks.push(block);
    }
    
    // 统一区域样式
    const commonStyle = {
        backgroundColor: 'rgba(255, 255, 255, 0.35)',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
    };
    
    // 定义间距
    const spacing = 20; // 区域之间的间距
    
    // 调整区域3的大小和位置，与 #tree-map-container 完全一致
    const block3 = blocks[2];
    if (block3) {
        block3.style.position = 'absolute';
        block3.style.bottom = '20px';
        block3.style.left = '20px';
        block3.style.width = 'calc(100% - 300px)'; // 与 #tree-map-container 宽度一致
        block3.style.height = 'calc(50% - 60px)';
        block3.style.borderRadius = '8px';
        block3.style.padding = '10px';
        Object.assign(block3.style, commonStyle);
    }
    
    // 调整区域2的大小和位置（右下角）
    const block2 = blocks[1];
    if (block2) {
        block2.style.position = 'absolute';
        block2.style.bottom = '20px';
        block2.style.right = '20px';
        block2.style.width = '240px'; // 与原来的右侧菜单宽度一致
        block2.style.height = 'calc(50% - 60px)';
        block2.style.borderRadius = '8px';
        block2.style.padding = '10px';
        Object.assign(block2.style, commonStyle);
    }
    
    // 计算第一行区域的宽度（两个区域宽度相同，且有间距）
    const firstRowBlockWidth = `calc(50% - ${spacing * 1.5}px)`;
    
    // 调整区域0的大小和位置（左上角）
    const block0 = blocks[0];
    if (block0) {
        block0.style.position = 'absolute';
        block0.style.top = '80px'; // 增加顶部间距
        block0.style.left = '20px';
        block0.style.width = 'calc(100% - 40px)'; // 第一行两个区域宽度相同
        block0.style.height = 'calc(50% - 60px)'; // 增加高度，留出更多间距
        block0.style.borderRadius = '8px';
        block0.style.padding = '10px';
        Object.assign(block0.style, commonStyle);
    }
    
    // 初始化页面管理栈，将根页面(main)压入栈中
    page_stack = [main];
    current_page_index = 0;
    // 根页面默认显示，不需要设置display属性
    
    // 初始化upbar显示状态
    if (upbar) {
        upbar.style.display = ''; // 显示upbar
    }
    
    console.log('布局模块初始化完成，创建了', BLOCK_COUNT, '个区域');
}

/**
* 获取指定索引的区域
* @param {number} index - 区域索引
* @returns {HTMLElement|null} 区域元素
*/
function get_block(index) {
    if (typeof index !== 'number' || index < 0) {
        console.warn('布局模块：无效的区域索引', index);
        return null;
    }
    
    // 首先检查是否是固定区域
    if (index < BLOCK_COUNT) {
        return blocks[index] || null;
    }
    
    // 然后检查是否是临时区域
    const temp_block = temp_blocks.find(block => block.index === index);
    return temp_block ? temp_block.element : null;
}

// 页面加载时初始化布局
if (typeof onload_func_list !== 'undefined') {
    onload_func_list.push(initLayout);
} else {
    // 如果没有 onload_func_list，则直接在页面加载时初始化
    window.addEventListener('load', initLayout);
}

// 导出 get_block 方法
if (typeof window !== 'undefined') {
    window.get_block = get_block;
}

// 区域状态和回调函数
let block_show_list = [false, false, false, false];
let when_show_callback_list = [null, null, null, null];
let when_hide_callback_list = [null, null, null, null];

// 临时区域管理
let temp_blocks = [];
let next_temp_index = BLOCK_COUNT;

/**
* 设置区域显示时的回调函数
* @param {number} index - 区域索引
* @param {function} callback - 回调函数
*/
function set_when_show(index, callback) {
    if (typeof index !== 'number' || index < 0) {
        console.warn('布局模块：无效的区域索引', index);
        return;
    }
    
    // 确保回调列表有足够的空间
    if (index >= when_show_callback_list.length) {
        when_show_callback_list[index] = null;
        when_hide_callback_list[index] = null;
        block_show_list[index] = false;
    }
    
    when_show_callback_list[index] = callback;
}

/**
* 设置区域隐藏时的回调函数
* @param {number} index - 区域索引
* @param {function} callback - 回调函数
*/
function set_when_hide(index, callback) {
    if (typeof index !== 'number' || index < 0) {
        console.warn('布局模块：无效的区域索引', index);
        return;
    }
    
    // 确保回调列表有足够的空间
    if (index >= when_hide_callback_list.length) {
        when_show_callback_list[index] = null;
        when_hide_callback_list[index] = null;
        block_show_list[index] = false;
    }
    
    when_hide_callback_list[index] = callback;
}

/**
* 向frame.js注册一个临时区域
* @param {HTMLElement} block - 区域元素
* @returns {number} 注册成功的区域索引
*/
function create_new_block(block) {
    if (!block || !(block instanceof HTMLElement)) {
        console.error('布局模块：无效的区域元素');
        return -1;
    }
    
    // 分配临时区域索引
    const index = next_temp_index++;
    
    // 存储临时区域
    temp_blocks.push({
        index: index,
        element: block
    });
    
    console.log('布局模块：创建临时区域，索引为', index);
    return index;
}

/**
* 执行指定区域的活跃回调函数
* @param {number} index - 区域索引
*/
function show_module(index) {
    if (typeof index !== 'number' || index < 0) {
        console.warn('布局模块：无效的区域索引', index);
        return;
    }
    
    // 检查区域是否已经显示
    if (block_show_list[index]) {
        return;
    }
    
    // 执行活跃回调函数
    const callback = when_show_callback_list[index];
    if (callback) {
        try {
            callback();
            block_show_list[index] = true;
            console.log('布局模块：激活模块，索引为', index);
        } catch (error) {
            console.error('布局模块：执行活跃回调函数失败', error);
        }
    }
}

/**
* 执行指定区域的睡眠回调函数
* @param {number} index - 区域索引
*/
function hide_module(index) {
    if (typeof index !== 'number' || index < 0) {
        console.warn('布局模块：无效的区域索引', index);
        return;
    }
    
    // 检查区域是否已经隐藏
    if (!block_show_list[index]) {
        return;
    }
    
    // 执行睡眠回调函数
    const callback = when_hide_callback_list[index];
    if (callback) {
        try {
            callback();
            block_show_list[index] = false;
            console.log('布局模块：休眠模块，索引为', index);
        } catch (error) {
            console.error('布局模块：执行睡眠回调函数失败', error);
        }
    }
}

// 导出方法
if (typeof window !== 'undefined') {
    window.get_block = get_block;
    window.set_when_show = set_when_show;
    window.set_when_hide = set_when_hide;
    window.create_new_block = create_new_block;
    window.show_module = show_module;
    window.hide_module = hide_module;
    window.new_page = new_page;
    window.pop_page = pop_page;
}

/**
* 新建空白页
* 当前页面将被隐藏(display属性)，新建的空白页将压入页面管理栈，即将在页面上显示
* @returns {HTMLElement} 新建的空白页元素
*/
function new_page() {
    // 隐藏当前页面
    if (current_page_index >= 0 && current_page_index < page_stack.length) {
        const currentPage = page_stack[current_page_index];
        currentPage.setAttribute('pre-display', currentPage.style.display || '');
        currentPage.style.display = 'none';
    }
    
    // 创建新的空白页
    const newPage = document.createElement('div');
    newPage.className = 'page';
    newPage.cleanFuncList = [];
    newPage.style.position = 'absolute';
    newPage.style.top = '0';
    newPage.style.left = '0';
    newPage.style.width = '100%';
    newPage.style.height = '100%';
    newPage.style.backgroundColor = 'rgba(248, 248, 255, 0.65)';
    newPage.style.zIndex = '20';
    //newPage.style.opacity = '0.85';
    
    // 将新页面添加到body或main容器中
    // const main = document.getElementById('main');
    // if (main) {
    //     main.appendChild(newPage);
    // } else {
    document.body.appendChild(newPage);
    //}
    
    // 压入页面管理栈
    page_stack.push(newPage);
    current_page_index = page_stack.length - 1;
    
    // 隐藏upbar
    if (upbar) {
        upbar.style.display = 'none';
    }
    
    console.log('布局模块：创建新页面，栈深度:', page_stack.length);

    for (let i = 0; i < BLOCK_COUNT; i++) {
        if (when_hide_callback_list[i]) {
            when_hide_callback_list[i]();
            block_show_list[i] = false;
        }
    }
    return newPage;
}

/**
* 从页面管理栈里弹出num个页面
* 如果num大于页面管理栈里的页面数量-1，那么弹出所有页面只剩根页面
* @param {number} num - 要弹出的页面数量
*/
function pop_page(num) {
    if (typeof num !== 'number' || num < 1) {
        console.warn('布局模块：无效的弹出数量', num);
        return 0;
    }
    
    // 计算最多能弹出的页面数（至少保留根页面）
    const maxPop = page_stack.length - 1;
    const actualPop = Math.min(num, maxPop);
    
    if (actualPop === 0) {
        console.log('布局模块：已在根页面，无法弹出更多');
        return 0;
    }
    
    // 弹出页面
    for (let i = 0; i < actualPop; i++) {
        const poppedPage = page_stack.pop();
        if (poppedPage && poppedPage.parentElement) {
            if (poppedPage.cleanFuncList) {
                poppedPage.cleanFuncList.forEach(func => func());
            }
            poppedPage.parentElement.removeChild(poppedPage);
        }
    }
    
    // 更新当前页面索引
    current_page_index = page_stack.length - 1;
    
    // 显示当前页面
    if (current_page_index >= 0) {
        const currentPage = page_stack[current_page_index];
        const preDisplay = currentPage.getAttribute('pre-display');
        currentPage.style.display = preDisplay !== null ? preDisplay : '';
    }
    
    // 如果回到根页面，显示upbar
    if (current_page_index === 0 && upbar) {
        upbar.style.display = '';
        // 执行所有固定区域的活跃回调函数
        for (let i = 0; i < BLOCK_COUNT; i++) {
            if (when_show_callback_list[i]) {
                when_show_callback_list[i]();
                block_show_list[i] = true;
            }
        }
    } else if (upbar) {
        // 否则隐藏upbar
        upbar.style.display = 'none';
    }
    
    console.log('布局模块：弹出', actualPop, '个页面，剩余:', page_stack.length);
    return actualPop;
}

// 连接成功时激活所有固定区域对应模块
if (typeof when_connect_func_list !== 'undefined'){
    when_connect_func_list.push(() => {
        for (let i = 0; i < BLOCK_COUNT; i++) {
            if (when_show_callback_list[i]) {
                when_show_callback_list[i]();
                block_show_list[i] = true;
            }
        }
        }
    );
}

// 断开连接时弹出所有页面
if (typeof when_disconnect_func_list !== 'undefined'){
    when_disconnect_func_list.push(() => {
        pop_page(page_stack.length - 1);
        }
    );
}
