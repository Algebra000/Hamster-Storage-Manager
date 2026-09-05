/**
* 基础布局模块
* 将屏幕划分为4个区域
*/

// 区域数量
const BLOCK_COUNT = 4;

// 区域元素数组
let blocks = [];

/**
* 初始化布局
*/
function initLayout() {
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
    main.style.opacity = '0.85';
    main.style.backgroundColor = 'ghostwhite';
    main.style.zIndex = '10';
    
    // 清空主容器
    main.innerHTML = '';
    
    // 创建4个区域
    for (let i = 0; i < BLOCK_COUNT; i++) {
        const block = document.createElement('div');
        block.id = `block-${i}`;
        block.style.backgroundColor = '#f0f0f0';
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
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
    };
    
    // 定义间距
    const spacing = 20; // 区域之间的间距
    
    // 调整区域3的大小和位置，与 #tree-map-container 完全一致
    const block3 = blocks[3];
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
    const block2 = blocks[2];
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
        block0.style.width = firstRowBlockWidth; // 第一行两个区域宽度相同
        block0.style.height = 'calc(50% - 60px)'; // 增加高度，留出更多间距
        block0.style.borderRadius = '8px';
        block0.style.padding = '10px';
        Object.assign(block0.style, commonStyle);
    }
    
    // 调整区域1的大小和位置（右上角）
    const block1 = blocks[1];
    if (block1) {
        block1.style.position = 'absolute';
        block1.style.top = '80px'; // 增加顶部间距
        block1.style.right = '20px';
        block1.style.width = firstRowBlockWidth; // 第一行两个区域宽度相同
        block1.style.height = 'calc(50% - 60px)'; // 增加高度，留出更多间距
        block1.style.borderRadius = '8px';
        block1.style.padding = '10px';
        Object.assign(block1.style, commonStyle);
    }
    
    console.log('布局模块初始化完成，创建了', BLOCK_COUNT, '个区域');
}

/**
* 获取指定索引的区域
* @param {number} index - 区域索引
* @returns {HTMLElement|null} 区域元素
*/
function get_block(index) {
    if (typeof index !== 'number' || index < 0 || index >= BLOCK_COUNT) {
        console.warn('布局模块：无效的区域索引', index);
        return null;
    }
    
    return blocks[index];
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

let block_show_list = [false, false, false, false];
let when_show_callback_list = [null, null, null, null];
let when_hide_callback_list = [null, null, null, null];

function set_when_show(index, callback) {
    if (typeof index !== 'number' || index < 0 || index >= BLOCK_COUNT) {
        console.warn('布局模块：无效的区域索引', index);
        return;
    }
    when_show_callback_list[index] = callback;
}

function set_when_hide(index, callback) {
    if (typeof index !== 'number' || index < 0 || index >= BLOCK_COUNT) {
        console.warn('布局模块：无效的区域索引', index);
        return;
    }
    when_hide_callback_list[index] = callback;
}

if (typeof window !== 'undefined') {
    window.set_when_show = set_when_show;
    window.set_when_hide = set_when_hide;
}

if (typeof when_connect_func_list !== 'undefined'){
    when_connect_func_list.push(() => {
        for (let i = 0; i < BLOCK_COUNT; i++) {
            if (when_show_callback_list[i]) {
                when_show_callback_list[i]();
            }
        }
        }
    );
}
