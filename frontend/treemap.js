// 树状图模块的区域索引
const TREEMAP_JS_MODULE_INDEX = 2;

// 颜色映射
const TREEMAP_COLOR_MAP = {
    'image': '#87CEEB',      // 淡蓝色
    'video': '#FFB6C1',      // 淡粉色
    'audio': '#98FB98',      // 淡绿色
    'document': '#F0E68C',   // 卡其色
    'sourcecode': '#DDA0DD', // 梅红色
    'script': '#F0E68C',     // 卡其色
    'database': '#B0C4DE',   // 淡钢蓝
    'config': '#CD853F',     // 秘鲁色
    'executable': '#C0C0C0', // 银色
    'zip': '#DEB887',        // 实木色
    'fonts': '#E6E6FA',      // 薰衣草色
    'system': '#A9A9A9',     // 暗灰色
    'folder': '#F5F5DC',     // 米色
    'fragmented': '#D3D3D3', // 浅灰色
    'other': '#FFFFFF'       // 白色
};

/**
* 树状图绘制器
* 实现交替水平/垂直分割的矩形树状图
*/
class TreeMapDrawer {
    constructor(container_element) {
        this.container = container_element;
        this.tooltip = null;
        this.brickTexture = null; // 缓存纹理
        this.createTooltip();
    }
    
    createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'tooltip';
        this.tooltip.style.display = 'none';
        this.tooltip.style.maxWidth = '300px';
        this.tooltip.style.whiteSpace = 'normal';
        this.tooltip.style.wordWrap = 'break-word';
        this.tooltip.style.lineHeight = '1.4';
        document.body.appendChild(this.tooltip);
    }
    
    showTooltip(event, text) {
        // 设置文本内容
        this.tooltip.textContent = text;
        
        // 设置最大宽度和自动换行
        this.tooltip.style.maxWidth = '300px';
        this.tooltip.style.whiteSpace = 'normal';
        this.tooltip.style.wordWrap = 'break-word';
        this.tooltip.style.lineHeight = '1.4';
        
        // 先临时显示以获取尺寸
        this.tooltip.style.display = 'block';
        this.tooltip.style.visibility = 'hidden';
        
        // 获取 tooltip 的尺寸
        const tooltipRect = this.tooltip.getBoundingClientRect();
        const tooltipWidth = tooltipRect.width;
        const tooltipHeight = tooltipRect.height;
        
        // 获取视口尺寸
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // 鼠标位置
        const mouseX = event.clientX;
        const mouseY = event.clientY;
        
        // 默认偏移量（相对于鼠标指针）
        const offsetX = 15;
        const offsetY = 15;
        
        // 计算初始位置（鼠标右下方）
        let left = mouseX + offsetX;
        let top = mouseY + offsetY;
        
        // 检查右侧边界（如果超出右边界，显示在鼠标左侧）
        if (left + tooltipWidth > viewportWidth - 10) {
            left = mouseX - tooltipWidth - offsetX;
            // 如果左侧也超出，则贴在左边界
            if (left < 10) {
                left = 10;
            }
        }
        
        // 检查左侧边界
        if (left < 10) {
            left = 10;
        }
        
        // 检查底部边界（如果超出底部，显示在鼠标上方）
        if (top + tooltipHeight > viewportHeight - 10) {
            top = mouseY - tooltipHeight - offsetY;
            // 如果上方也超出，则贴在顶部
            if (top < 10) {
                top = 10;
            }
        }
        
        // 检查顶部边界
        if (top < 10) {
            top = 10;
        }
        
        // 应用最终位置
        this.tooltip.style.left = left + 'px';
        this.tooltip.style.top = top + 'px';
        this.tooltip.style.visibility = 'visible';
    }
    
    hideTooltip() {
        this.tooltip.style.display = 'none';
        this.tooltip.style.visibility = 'hidden';
    }
    
    /**
     * 绘制树状图
     * @param {Object} node - 当前节点
     * @param {Object} rect - 矩形区域 {x, y, width, height}
     * @param {number} depth - 当前深度（0=根目录）
     * @param {string} direction - 分割方向 ('horizontal' 或 'vertical')
     */
    // 生成根目录颜色的方法
    generateRootColors(count) {
        const colors = [];
        const hueStep = 360 / count;
        
        for (let i = 0; i < count; i++) {
            const hue = (i * hueStep) % 360;
            // 高饱和度、高亮度的颜色
            const color = `hsl(${hue}, 80%, 60%)`;
            colors.push(color);
        }
        
        return colors;
    }
    
    // 生成根目录颜色映射
    getRootColorMap(children) {
        // 过滤掉散碎文件组，只为实际的根目录生成颜色
        const validChildren = children.filter(child => child.type !== 'fragmented_group');
        const colors = this.generateRootColors(validChildren.length);
        const colorMap = {};
        
        let colorIndex = 0;
        children.forEach((child, index) => {
            if (child.type !== 'fragmented_group') {
                colorMap[child.path] = colors[colorIndex];
                colorIndex++;
            }
        });
        
        return colorMap;
    }
    
    // 省略路径，保留末尾部分，根据像素宽度计算
    truncatePath(path, maxWidth) {
        // 创建临时元素用于测量
        const tempSpan = document.createElement('span');
        tempSpan.style.visibility = 'hidden';
        tempSpan.style.position = 'absolute';
        tempSpan.style.font = '12px Arial, sans-serif'; // 使用与标签相同的字体
        tempSpan.style.whiteSpace = 'nowrap';
        document.body.appendChild(tempSpan);
        
        // 首先测试完整路径
        tempSpan.textContent = path;
        if (tempSpan.offsetWidth <= maxWidth) {
            document.body.removeChild(tempSpan);
            return path;
        }
        
        const parts = path.split(/[\\/]/);
        let result = '';
        
        // 从末尾开始，直到宽度不超过 maxWidth
        for (let i = parts.length - 1; i >= 0; i--) {
            const part = parts[i];
            const testResult = part + (result ? '/' + result : '');
            tempSpan.textContent = testResult;
            
            if (tempSpan.offsetWidth <= maxWidth) {
                result = testResult;
            } else {
                // 尝试添加省略号
                const ellipsisResult = '...' + result;
                tempSpan.textContent = ellipsisResult;
                if (tempSpan.offsetWidth <= maxWidth) {
                    result = ellipsisResult;
                }
                break;
            }
        }
        
        document.body.removeChild(tempSpan);
        return result;
    }
    
    draw(node, rect, depth = 0, direction = 'horizontal', rootColorMap = null) {
        if (!node || node.size === 0) return;
        
        // 如果是文件，直接绘制矩形
        if (node.type === 'file') {
            this.drawRect(node, rect, depth, rootColorMap);
            return;
        }
        
        // 如果是散碎文件组，不在这里绘制，由父节点最后统一处理
        if (node.type === 'fragmented_group') {
            return;
        }
        
        // 如果是文件夹且有子项
        const children = node.children || [];
        if (children.length === 0) {
            this.drawRect(node, rect, depth, rootColorMap);
            return;
        }
        
        // 为根目录（depth === 1）的文件夹节点绘制矩形，添加彩色边框
        if (depth === 1 && node.type === 'folder') {
            const rootRectDiv = this.drawRect(node, rect, depth, rootColorMap);
            // 为根目录矩形添加事件阻止，防止子项事件冒泡
            if (rootRectDiv) {
                rootRectDiv.addEventListener('mousemove', (e) => {
                    e.stopPropagation();
                });
                rootRectDiv.addEventListener('mouseleave', (e) => {
                    e.stopPropagation();
                });
            }
        }
        
        // 分离正常子项和散碎文件组
        const normalChildren = [];
        let fragmentedGroup = null;
        
        for (const child of children) {
            if (child.type === 'fragmented_group') {
                fragmentedGroup = child;
            } else {
                normalChildren.push(child);
            }
        }
        
        // 计算正常子项的总大小
        const validNormalChildren = normalChildren.filter(c => c.size > 0);
        
        // 如果没有正常子项，直接绘制文件夹
        if (validNormalChildren.length === 0) {
            this.drawRect(node, rect, depth, rootColorMap);
            return;
        }
        
        // 根据深度确定分割方向
        let currentDirection;
        if (depth === 0 || depth === 1) {
            // 根目录间和根目录的一级子目录间使用垂直分割（左右排列）
            currentDirection = 'horizontal';
            // 生成根目录颜色映射
            if (depth === 0) {
                rootColorMap = this.getRootColorMap(validNormalChildren);
            }
        } else {
            // 二级及以上子目录，根据深度奇偶性交替分割方向
            // 深度为偶数：水平分割（上下排列）
            // 深度为奇数：垂直分割（左右排列）
            currentDirection = depth % 2 === 0 ? 'vertical' : 'horizontal';
        }
        
        // 计算下一级的分割方向
        const nextDirection = currentDirection === 'horizontal' ? 'vertical' : 'horizontal';
        
        // 计算正常子项占用的空间比例
        const normalTotalSize = validNormalChildren.reduce((sum, c) => sum + c.size, 0);
        const normalRatio = normalTotalSize / node.size;
        
        // 计算子项的绘制区域（为根目录添加内边距）
        let childRectOffset = { x: 0, y: 0 };
        if (depth === 1 && node.type === 'folder') {
            // 为根目录添加内边距，避免子项覆盖边框
            childRectOffset = { x: 2, y: 2 };
        }
        
        // 先绘制正常子项（占满整个矩形）
        if (currentDirection === 'vertical') {
            // 垂直分割：按高度比例
            let currentY = rect.y + childRectOffset.y;
            const availableHeight = rect.height - 2 * childRectOffset.y;
            for (const child of validNormalChildren) {
                const ratio = child.size / normalTotalSize;
                const childHeight = availableHeight * normalRatio * ratio;
                const childRect = {
                    x: rect.x + childRectOffset.x,
                    y: currentY,
                    width: rect.width - 2 * childRectOffset.x,
                    height: childHeight
                };
                this.draw(child, childRect, depth + 1, nextDirection, rootColorMap);
                currentY += childHeight;
            }
            
            // 如果有散碎文件组，在剩余空间绘制（最底部）
            if (fragmentedGroup && fragmentedGroup.size > 0) {
                const fragmentedHeight = availableHeight * (1 - normalRatio);
                // 确保散碎文件组有足够的空间显示
                if (fragmentedHeight > 0) {
                    const fragmentedRect = {
                        x: rect.x + childRectOffset.x,
                        y: currentY,
                        width: rect.width - 2 * childRectOffset.x,
                        height: fragmentedHeight
                    };
                    this.drawRect(fragmentedGroup, fragmentedRect, depth, rootColorMap);
                }
            }
        } else {
            // 水平分割：按宽度比例
            let currentX = rect.x + childRectOffset.x;
            const availableWidth = rect.width - 2 * childRectOffset.x;
            for (const child of validNormalChildren) {
                const ratio = child.size / normalTotalSize;
                const childWidth = availableWidth * normalRatio * ratio;
                const childRect = {
                    x: currentX,
                    y: rect.y + childRectOffset.y,
                    width: childWidth,
                    height: rect.height - 2 * childRectOffset.y
                };
                this.draw(child, childRect, depth + 1, nextDirection, rootColorMap);
                currentX += childWidth;
            }
            
            // 如果有散碎文件组，在剩余空间绘制（最右侧）
            if (fragmentedGroup && fragmentedGroup.size > 0) {
                const fragmentedWidth = availableWidth * (1 - normalRatio);
                // 确保散碎文件组有足够的空间显示
                if (fragmentedWidth > 0) {
                    const fragmentedRect = {
                        x: currentX,
                        y: rect.y + childRectOffset.y,
                        width: fragmentedWidth,
                        height: rect.height - 2 * childRectOffset.y
                    };
                    this.drawRect(fragmentedGroup, fragmentedRect, depth, rootColorMap);
                }
            }
        }
    }
    
    /**
     * 生成纹理的 dataURL（用于背景）
     * @param {string} baseColor - 基础颜色
     * @param {string} patternType - 纹理类型 ('brick', 'crosshatch', 'dots')
     */
    generateTexture(baseColor, patternType = 'brick') {
        const canvas = document.createElement('canvas');
        const size = 20; // 纹理单元大小
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d');
        
        // 填充背景色
        ctx.fillStyle = baseColor;
        ctx.fillRect(0, 0, size, size);
        
        // 设置纹理颜色（稍深或稍浅）
        ctx.fillStyle = this.adjustColor(baseColor, -30);
        ctx.strokeStyle = this.adjustColor(baseColor, -30);
        ctx.lineWidth = 1;
        
        if (patternType === 'brick') {
            // 砖墙纹理
            const brickHeight = size / 3;
            // 第一行砖块
            ctx.fillRect(0, 0, size, brickHeight - 1);
            ctx.fillRect(size/2, brickHeight, size/2, brickHeight - 1);
            // 第二行砖块
            ctx.fillRect(0, brickHeight, size/2, brickHeight - 1);
            ctx.fillRect(size/2, brickHeight * 2, size/2, brickHeight - 1);
            // 第三行砖块
            ctx.fillRect(0, brickHeight * 2, size, brickHeight - 1);
            
            // 添加砖缝线条
            ctx.beginPath();
            ctx.strokeStyle = this.adjustColor(baseColor, -50);
            for (let i = 1; i <= 2; i++) {
                ctx.moveTo(0, brickHeight * i);
                ctx.lineTo(size, brickHeight * i);
                ctx.stroke();
            }
            ctx.moveTo(size/2, brickHeight);
            ctx.lineTo(size/2, brickHeight * 2);
            ctx.stroke();
            
        } else if (patternType === 'crosshatch') {
            // 交叉阴影纹理
            ctx.beginPath();
            for (let i = -size; i <= size; i += 4) {
                ctx.moveTo(i, 0);
                ctx.lineTo(i + size, size);
                ctx.moveTo(i, size);
                ctx.lineTo(i + size, 0);
            }
            ctx.stroke();
            
        } else if (patternType === 'dots') {
            // 点阵纹理
            ctx.fillStyle = this.adjustColor(baseColor, -40);
            for (let x = 4; x < size; x += 5) {
                for (let y = 4; y < size; y += 5) {
                    ctx.beginPath();
                    ctx.arc(x, y, 1.5, 0, Math.PI * 2);
                    ctx.fill();
                }
            }
        }
        
        return canvas.toDataURL();
    }

    /**
     * 调整颜色亮度
     * @param {string} color - 十六进制颜色
     * @param {number} percent - 调整百分比（负数为变暗，正数为变亮）
     */
    adjustColor(color, percent) {
        // 解析十六进制颜色
        let r, g, b;
        if (color.startsWith('#')) {
            r = parseInt(color.slice(1, 3), 16);
            g = parseInt(color.slice(3, 5), 16);
            b = parseInt(color.slice(5, 7), 16);
        } else {
            // 如果是颜色名称，返回默认颜色
            return '#888888';
        }
        
        // 调整亮度
        r = Math.min(255, Math.max(0, r + (r * percent / 100)));
        g = Math.min(255, Math.max(0, g + (g * percent / 100)));
        b = Math.min(255, Math.max(0, b + (b * percent / 100)));
        
        // 转换回十六进制
        return `#${Math.round(r).toString(16).padStart(2, '0')}${Math.round(g).toString(16).padStart(2, '0')}${Math.round(b).toString(16).padStart(2, '0')}`;
    }

    /**
     * 绘制单个矩形
     */
    drawRect(node, rect, depth, rootColorMap) {
        //if (rect.width < 2 || rect.height < 2) return;
        
        // 获取颜色
        let color = TREEMAP_COLOR_MAP[node.file_type] || TREEMAP_COLOR_MAP['other'];
        
        // 为散碎文件组使用特殊颜色和纹理
        const isFragmented = (node.type === 'fragmented_group');
        if (isFragmented) {
            color = TREEMAP_COLOR_MAP['fragmented'];
        }
        
        // 创建矩形元素
        const rectDiv = document.createElement('div');
        rectDiv.className = 'treemap-rect';
        
        // 添加文件夹/文件边框样式
        if (node.type === 'folder') {
            rectDiv.classList.add('treemap-rect-folder');
        } else {
            rectDiv.classList.add('treemap-rect-file');
        }
        
        // 设置样式
        rectDiv.style.left = rect.x + 'px';
        rectDiv.style.top = rect.y + 'px';
        rectDiv.style.width = rect.width + 'px';
        rectDiv.style.height = rect.height + 'px';
        rectDiv.style.backgroundColor = color;
        rectDiv.style.position = 'absolute';
        
        // 如果是散碎文件组，添加纹理背景
        if (isFragmented) {
            // 生成砖墙纹理（可以缓存以避免重复生成）
            if (!this.brickTexture) {
                this.brickTexture = this.generateTexture(color, 'dots');
            }
            rectDiv.style.backgroundImage = `url(${this.brickTexture})`;
            rectDiv.style.backgroundRepeat = 'repeat';
            rectDiv.style.backgroundColor = color; // 作为后备颜色
        }
        
        // 为根目录添加特殊样式（深度为1的文件夹，即多个根目录中的每个根目录）
        if (depth === 1 && node.type === 'folder' && rootColorMap) {
            // 添加根目录矩形类
            rectDiv.classList.add('root-directory-rect');
            
            // 设置根目录矩形的 z-index 为 0，确保子项在上方
            rectDiv.style.zIndex = '0';
            
            // 使用根目录颜色作为边框颜色
            const borderColor = rootColorMap[node.path] || '#333';
            rectDiv.style.border = `2px solid ${borderColor}`;
            
            // 添加左上角凸起显示路径
            if (rect.width > 60 && rect.height > 20) {
                const label = document.createElement('div');
                label.className = 'root-directory-label';
                label.style.position = 'absolute';
                
                // 计算标签相对于 #tree-map-container 的位置
                // #tree-map-container 有 10px padding，.treemap 有 20px marginTop
                const labelLeft = 10 + rect.x; // 10px 是 #tree-map-container 的 padding-left
                const labelTop = 11; // 10px 是 #tree-map-container 的 padding-top，标签位于 .treemap 容器的上方
                
                label.style.left = labelLeft + 'px';
                label.style.top = labelTop + 'px'; // 将标签移到矩形外侧上方
                label.style.backgroundColor = borderColor;
                label.style.color = 'white';
                label.style.padding = '2px 6px';
                label.style.fontSize = '12px';
                label.style.fontWeight = 'bold';
                label.style.borderRadius = '2px 2px 0 0';
                label.style.zIndex = '10';
                label.style.whiteSpace = 'nowrap';
                label.style.overflow = 'hidden';
                label.style.textOverflow = 'ellipsis';
                
                // 计算最大宽度（不超过矩形宽度的一半）
                const maxLabelWidth = rect.width / 2;
                label.style.maxWidth = maxLabelWidth + 'px';
                
                // 省略路径，保留末尾部分
                const truncatedPath = this.truncatePath(node.path, maxLabelWidth-10);
                label.textContent = truncatedPath;
                
                // 将标签添加到 #tree-map-container 中，避免被 .treemap 容器的 overflow: hidden 裁剪
                this.container.parentElement.appendChild(label);
            }
        }
        
        // 存储节点信息用于悬停提示
        rectDiv.dataset.name = node.name;
        rectDiv.dataset.path = node.path;
        rectDiv.dataset.size = node.size;
        rectDiv.dataset.type = node.type;
        
        // 添加悬停事件
        rectDiv.addEventListener('mousemove', (e) => {
            const sizeText = this.formatSize(node.size);
            let typeText;
            if (node.type === 'folder') {
                typeText = '📁 文件夹';
            } else if (node.type === 'file') {
                typeText = '📄 文件';
            } else if (node.type === 'fragmented_group') {
                typeText = `📦 散碎文件组 (包含 ${node.fragmented_count} 个文件/文件夹)`;
            } else {
                typeText = '📄 未知';
            }
            const info = `${typeText}: ${node.name}\n路径: ${node.path}\n大小: ${sizeText}`;
            this.showTooltip(e, info);
        });
        
        rectDiv.addEventListener('mouseleave', () => {
            this.hideTooltip();
        });
        
        // 点击事件
        rectDiv.addEventListener('click', () => {
            console.log('点击:', node.name, node.path);
            // 可以在这里添加点击展开深层的逻辑
        });
        
        this.container.appendChild(rectDiv);
        
        // 返回创建的矩形元素
        return rectDiv;
    }
    
    /**
    * 格式化文件大小
    */
    formatSize(bytes) {
        if (bytes === 0) return '0 B';
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i];
    }
    
    /**
    * 清空并重新绘制
    */
    render(rootNode, containerWidth, containerHeight) {
        // 清空容器
        this.container.innerHTML = '';
        
        // 移除旧的根目录标签
        const oldLabels = this.container.parentElement.querySelectorAll('.root-directory-label');
        oldLabels.forEach(label => label.remove());
        
        if (!rootNode) {
            this.container.innerHTML = '<div class="loading">无数据</div>';
            return;
        }
        
        // 设置容器样式
        this.container.style.position = 'relative';
        this.container.style.width = containerWidth + 'px';
        this.container.style.height = containerHeight + 'px';
        
        // 绘制根节点
        const rootRect = {
            x: 0,
            y: 0,
            width: containerWidth,
            height: containerHeight
        };
        
        this.draw(rootNode, rootRect, 0, 'horizontal', null);
    }
    
    /**
    * 获取容器尺寸（响应式）
    */
    getContainerSize() {
        const parent = this.container.parentElement;
        const width = parent.clientWidth - 148; // 减去菜单栏宽度和间距
        const height = parent.clientHeight - 42;
        //console.log(width, height);
        return { width, height };
        
        /*return { width: 1200, height: 300 };*/
    }
}


let treemap_have_content = false;
/**
* 处理接收到的目录结构数据
*/
function treemapProcessDirectoryStructure(data) {
    console.log('收到目录结构数据:', data);
    
    // 获取分配的区域
    const block = get_block(TREEMAP_JS_MODULE_INDEX);
    if (!block) {
        console.error('树状图模块：无法获取区域');
        return;
    }
    
    // 确保区域的布局设置正确
    block.style.display = 'flex';
    block.style.flexDirection = 'row';
    block.style.gap = '10px';
    
    // 移除加载提示、旧的树状图和旧的根目录标签，但保留菜单栏
    const loadingElement = block.querySelector('.loading');
    if (loadingElement) {
        loadingElement.remove();
    }
    
    const oldTreemap = block.querySelector('.treemap');
    if (oldTreemap) {
        oldTreemap.remove();
    }
    
    // 移除旧的根目录标签
    const oldLabels = block.querySelectorAll('.root-directory-label');
    oldLabels.forEach(label => label.remove());
    
    // 创建新的树状图容器
    const mapDiv = document.createElement('div');
    mapDiv.className = 'treemap';
    mapDiv.style.flex = '1'; // 确保树状图容器占据剩余空间
    const menuBar = block.querySelector('.treemap-menu');
    if (menuBar) {
        menuBar.style.display = 'flex';
    }
    block.insertBefore(mapDiv, menuBar); // 添加到菜单栏之前，确保在菜单栏左侧

    // 创建TreeMapDrawer实例并绘制树状图
    const drawer = new TreeMapDrawer(mapDiv);
    const { width, height } = drawer.getContainerSize();
    console.log(width, height);
    drawer.render(data, width, height);
    treemap_have_content = true;
    
    // 移除旧的窗口大小变化监听
    window.removeEventListener('resize', window.treemapResizeListener);
    
    // 保存新的窗口大小变化监听函数
    window.treemapResizeListener = () => {
        const newSize = drawer.getContainerSize();
        console.log(newSize);
        drawer.render(data, newSize.width, newSize.height);
    };
    
    // 添加新的窗口大小变化监听
    window.addEventListener('resize', window.treemapResizeListener);
}

/**
* 初始化树状图模块
* 按照规范，这里不直接调用get_block，而是在set_when_show回调中调用
*/
function treemapInit() {
    console.log('树状图模块：初始化完成，等待区域激活');
    
    // 添加样式（只添加一次）
    if (!document.getElementById('treemap-style')) {
        const style = document.createElement('style');
        style.id = 'treemap-style';
        style.textContent = `
            .treemap {
                position: relative;
                flex: 1;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                overflow: visible; /* 确保根目录矩形的下边框不被裁剪 */
                min-width: 100px;
                /*min-height: 100px;  确保最小高度 */
                margin-top: 20px; /* 将顶部下移20像素，为标签留出空间 */
                box-sizing: border-box; /* 确保边框包含在高度计算中 */
            }
            
            .treemap-rect {
                position: absolute;
                border: 1px solid rgba(0, 0, 0, 0.1);
                box-sizing: border-box;
                transition: opacity 0.2s;
            }
            
            .treemap-rect:hover {
                filter: brightness(0.95);
                z-index: 10;
                border-color: #00ff0d !important;
                box-shadow: 0 0 10px rgb(248, 255, 249);
                border-width: 3px;
            }
            
            .treemap-rect-folder {
                border: 1px solid rgba(0, 0, 0, 0.2);
            }
            
            .treemap-rect-file {
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
            
            .root-directory-rect {
                position: relative;
                border: 2px solid #333;
                border-radius: 2px;
            }
            
            .root-directory-label {
                position: absolute;
                background-color: #333;
                color: white;
                padding: 2px 6px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 2px 2px 0 0;
                z-index: 10;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .tooltip {
                position: fixed;
                background-color: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 1000;
                pointer-events: none;
                max-width: 300px;
                white-space: normal;
                word-wrap: break-word;
                line-height: 1.4;
            }
            
            .loading {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100%;
                font-size: 16px;
                color: #666;
            }
            
            .menu-input {
                padding: 8px 2px 8px 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
                width: 100%;
                box-sizing: border-box;
                height: 32px;
            }
            
            /* 增大输入框上下箭头并调整位置 */
            input[type="number"] {
                -moz-appearance: textfield;
                appearance: textfield;
            }
            
            input[type="number"]::-webkit-inner-spin-button {
                height: 30px;
                width: 20px;
                cursor: pointer;
                margin-left: -10px;
            }
            
            input[type="number"]::-webkit-outer-spin-button {
                height: 30px;
                width: 20px;
                cursor: pointer;
                margin-left: -10px;
            }
            
            input[type="number"]::-moz-inner-spin-button {
                height: 30px;
                width: 20px;
                cursor: pointer;
                margin-left: -10px;
            }
            
            .menu-input.error {
                border-color: #f44336;
                background-color: #ffebee;
            }
            
            .menu-error {
                color: red;
                font-size: 12px;
                margin-left: 5px;
                margin-right: 15px;
            }
            
            .treemap-menu {
                position: relative;
                width: 120px;
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                padding: 10px;
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
                gap: 5px;
                flex-shrink: 0;
                overflow-y: auto;
            }
                
            .menu-item {
                display: flex;
                flex-direction: column;
                gap: 5px;
            }
            
            .menu-label {
                font-size: 12px;
                font-weight: bold;
                color: #333;
            }
            
            .menu-button {
                padding: 8px 12px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                transition: background-color 0.2s ease;
            }
            
            .menu-button:hover {
                background-color: #45a049;
            }
            
            .menu-select {
                padding: 6px 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 12px;
                background-color: white;
                width: 100%;
            }
            
            .menu-select-sm {
                padding: 6px 4px;
                font-size: 11px;
                flex-shrink: 0;
                width: auto;
            }
            
            #percentage-input {
                width: 60px;
            }
        `;
        document.head.appendChild(style);
    }
}

// 保存阈值设置的变量
let treemapSavedPercentageValue = 0.5; // 默认值
let treemapSavedSizeValue = 10; // 默认值
let treemapSavedSizeUnit = 'MB'; // 默认值

/**
* 初始化树状图菜单事件
*/
function treemapInitMenuEvents() {
    // 初始化保存的值
    treemapSavedPercentageValue = parseFloat(document.getElementById('percentage-input').value) || 0.5;
    treemapSavedSizeValue = parseInt(document.getElementById('size-input').value) || 10;
    treemapSavedSizeUnit = document.getElementById('size-unit').value || 'MB';
    
    // 刷新按钮事件
    document.getElementById('refresh-btn').addEventListener('click', function() {
        if (socket && socket.isConnected()) {
            socket.send(JSON.stringify({ command: 'REFRESH' }));
            console.log('发送刷新请求');
        } else {
            console.log('未连接到后端，无法发送刷新请求');
        }
        console.log('刷新按钮点击');
    });
    
    // 树状图深度输入事件
    const depthInput = document.getElementById('depth-input');
    const depthError = document.getElementById('depth-error');
    
    depthInput.addEventListener('input', function() {
        const value = parseInt(this.value);
        if (isNaN(value) || value < 1 || value > 256) {
            this.classList.add('error');
            depthError.textContent = '请输入1-256之间的整数';
        } else {
            this.classList.remove('error');
            depthError.textContent = '';
        }
    });
    
    depthInput.addEventListener('change', function() {
        const value = parseInt(this.value);
        if (!isNaN(value) && value >= 1 && value <= 256) {
            if (socket && socket.isConnected()) {
                socket.send(JSON.stringify({ 
                    command: 'SET_DEPTH', 
                    depth: value 
                }));
                console.log('发送深度设置:', value);
            }
        }
    });
    
    // 散碎文件阈值模式切换
    const thresholdMode = document.getElementById('threshold-mode');
    const percentageMode = document.getElementById('percentage-mode');
    const sizeMode = document.getElementById('size-mode');
    const percentageInput = document.getElementById('percentage-input');
    const sizeInput = document.getElementById('size-input');
    const sizeUnit = document.getElementById('size-unit');
    
    thresholdMode.addEventListener('change', function() {
        const mode = this.value;
        
        // 保存当前模式的值
        if (mode === 'percentage') {
            // 保存大小模式的值
            treemapSavedSizeValue = parseInt(sizeInput.value) || 10;
            treemapSavedSizeUnit = sizeUnit.value || 'MB';
            // 恢复百分比模式的值
            percentageInput.value = treemapSavedPercentageValue;
            percentageMode.style.display = 'inline';
            sizeMode.style.display = 'none';
        } else {
            // 保存百分比模式的值
            treemapSavedPercentageValue = parseFloat(percentageInput.value) || 0.5;
            // 恢复大小模式的值
            sizeInput.value = treemapSavedSizeValue;
            sizeUnit.value = treemapSavedSizeUnit;
            percentageMode.style.display = 'none';
            sizeMode.style.display = 'inline';
        }
        
        // 向后端发送模式改变消息
        if (socket && socket.isConnected()) {
            const value = mode === 'percentage' ? parseFloat(percentageInput.value) : parseInt(sizeInput.value);
            const unit = sizeUnit.value;
            
            socket.send(JSON.stringify({ 
                command: 'SET_THRESHOLD', 
                mode: mode,
                threshold: value,
                unit: unit
            }));
            console.log('发送阈值模式设置:', mode, value, unit);
        }
    });
    
    // 百分比输入验证
    const percentageError = document.getElementById('percentage-error');
    
    percentageInput.addEventListener('input', function() {
        const value = parseFloat(this.value);
        if (isNaN(value) || value < 0 || value > 100) {
            this.classList.add('error');
            percentageError.textContent = '请输入0-100之间的数值';
        } else {
            this.classList.remove('error');
            percentageError.textContent = '';
        }
    });
    
    percentageInput.addEventListener('change', function() {
        const value = parseFloat(this.value);
        if (!isNaN(value) && value >= 0 && value <= 100) {
            // 更新保存的百分比值
            treemapSavedPercentageValue = value;
            if (socket && socket.isConnected()) {
                socket.send(JSON.stringify({ 
                    command: 'SET_THRESHOLD', 
                    mode: 'percentage',
                    threshold: value 
                }));
                console.log('发送阈值设置(百分比):', value);
            }
        }
    });
    
    // 文件大小输入验证
    const sizeError = document.getElementById('size-error');
    
    sizeInput.addEventListener('input', function() {
        const value = parseInt(this.value);
        if (isNaN(value) || value < 1) {
            this.classList.add('error');
            sizeError.textContent = '请输入大于0的整数';
        } else {
            this.classList.remove('error');
            sizeError.textContent = '';
        }
    });
    
    sizeInput.addEventListener('change', function() {
        const value = parseInt(this.value);
        const unit = sizeUnit.value;
        if (!isNaN(value) && value >= 1) {
            // 更新保存的大小值
            treemapSavedSizeValue = value;
            if (socket && socket.isConnected()) {
                socket.send(JSON.stringify({ 
                    command: 'SET_THRESHOLD', 
                    mode: 'size',
                    threshold: value,
                    unit: unit
                }));
                console.log('发送阈值设置(大小):', value, unit);
            }
        }
    });
    
    sizeUnit.addEventListener('change', function() {
        const value = parseInt(sizeInput.value);
        const unit = this.value;
        if (!isNaN(value) && value >= 1) {
            // 更新保存的单位值
            treemapSavedSizeUnit = unit;
            if (socket && socket.isConnected()) {
                socket.send(JSON.stringify({ 
                    command: 'SET_THRESHOLD', 
                    mode: 'size',
                    threshold: value,
                    unit: unit
                }));
                console.log('发送阈值设置(单位):', value, unit);
            }
        }
    });
}

// 注册到 onload_func_list
if (typeof onload_func_list !== 'undefined') {
    onload_func_list.push(treemapInit);
}

// 设置活跃回调函数
if (typeof window.set_when_show !== 'undefined') {
    window.set_when_show(TREEMAP_JS_MODULE_INDEX, function() {
        console.log('树状图模块：区域显示，发送活跃状态消息');
        
        // 获取区域（按照规范，get_block应该在回调函数中调用）
        const block = get_block(TREEMAP_JS_MODULE_INDEX);
        if (!block) {
            console.error('树状图模块：无法获取区域');
            return;
        }
        
        // 初始化树状图（如果尚未初始化）
        if (!block.querySelector('.treemap-menu')) {
            console.log('树状图模块：初始化树状图');
            
            // 设置区域样式
            block.style.display = 'flex';
            block.style.flexDirection = 'row';
            block.style.padding = '10px';
            block.style.boxSizing = 'border-box';
            
            // 添加加载提示
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.textContent = '⏳ 正在加载数据...';
            loadingDiv.style.flex = '1';
            loadingDiv.style.display = 'flex';
            loadingDiv.style.justifyContent = 'center';
            loadingDiv.style.alignItems = 'center';
            
            // 创建菜单栏
            const menuDiv = document.createElement('div');
            menuDiv.className = 'treemap-menu';
            
            // 添加刷新按钮
            const refreshBtn = document.createElement('button');
            refreshBtn.id = 'refresh-btn';
            refreshBtn.className = 'menu-button';
            refreshBtn.textContent = '刷新';
            menuDiv.appendChild(refreshBtn);
            
            // 添加树状图深度设置
            const depthDiv = document.createElement('div');
            depthDiv.className = 'menu-item';
            depthDiv.innerHTML = `
                <div class="menu-label">树状图深度:</div>
                <input type="number" class="menu-input" id="depth-input" min="1" value="3">
                <span class="menu-error" id="depth-error"></span>
            `;
            menuDiv.appendChild(depthDiv);
            
            // 添加散碎文件阈值设置
            const thresholdDiv = document.createElement('div');
            thresholdDiv.className = 'menu-item';
            thresholdDiv.innerHTML = `
                <div class="menu-label">散碎文件阈值:</div>
                <select class="menu-select" id="threshold-mode">
                    <option value="percentage">占用总大小的百分比</option>
                    <option value="size">按文件实际大小</option>
                </select>
                <div id="percentage-mode" style="display: inline;">
                    <input type="number" class="menu-input" id="percentage-input" min="0" max="100" step="0.1" value="0.5"> %
                    <span class="menu-error" id="percentage-error"></span>
                </div>
                <div id="size-mode" style="display: none;">
                    <input type="number" class="menu-input" id="size-input" min="1" value="10">
                    <select class="menu-select menu-select-sm" id="size-unit">
                        <option value="KB">KB</option>
                        <option value="MB" selected>MB</option>
                        <option value="GB">GB</option>
                    </select>
                    <span class="menu-error" id="size-error"></span>
                </div>
            `;
            menuDiv.appendChild(thresholdDiv);
            
            block.appendChild(loadingDiv);
            block.appendChild(menuDiv);
            
            // 初始化菜单事件
            treemapInitMenuEvents();
        }
        
        // 向后端发送消息，通知树状图模块已激活
        if (socket && socket.isConnected()) {
            socket.send(JSON.stringify({
                command: 'TREEMAP_ACTIVATED'
            }));
            console.log('树状图模块：已发送激活消息');
        }
    });
}

// 注册到 message_proc_func_list
if (typeof message_proc_func_list !== 'undefined') {
    message_proc_func_list.push(function(data) {
        if (data.command === 'DIRECTORY_STRUCTURE') {
            treemapProcessDirectoryStructure(data.data);
        } else if (data.command === 'SET_CONFIG') {
            console.log('收到配置信息:', data);
            // 更新树状图深度
            const depthInput = document.getElementById('depth-input');
            if (depthInput && data.depth) {
                depthInput.value = data.depth;
            }
            // 更新阈值模式
            const thresholdMode = document.getElementById('threshold-mode');
            const percentageMode = document.getElementById('percentage-mode');
            const sizeMode = document.getElementById('size-mode');
            if (thresholdMode && data.threshold_mode) {
                thresholdMode.value = data.threshold_mode;
                // 更新UI显示
                if (data.threshold_mode === 'percentage') {
                    percentageMode.style.display = 'inline';
                    sizeMode.style.display = 'none';
                } else {
                    percentageMode.style.display = 'none';
                    sizeMode.style.display = 'inline';
                }
            }
            // 更新百分比值
            const percentageInput = document.getElementById('percentage-input');
            if (percentageInput && data.threshold_percentage) {
                percentageInput.value = data.threshold_percentage;
                // 更新保存的百分比值
                treemapSavedPercentageValue = parseFloat(data.threshold_percentage) || 0.5;
            }
            // 更新大小值和单位
            const sizeInput = document.getElementById('size-input');
            const sizeUnit = document.getElementById('size-unit');
            if (sizeInput && data.threshold_size) {
                sizeInput.value = data.threshold_size;
                // 更新保存的大小值
                treemapSavedSizeValue = parseInt(data.threshold_size) || 10;
            }
            if (sizeUnit && data.threshold_unit) {
                sizeUnit.value = data.threshold_unit;
                // 更新保存的单位值
                treemapSavedSizeUnit = data.threshold_unit;
            }
        }
    });
}

if (typeof when_disconnect_func_list !== 'undefined') {
    when_disconnect_func_list.push(function() {
        // 清空树状图容器，但保留菜单栏
        const treeMapContainer = get_block(TREEMAP_JS_MODULE_INDEX);
        if (treeMapContainer) {
            // 保存菜单栏
            const menuBar = treeMapContainer.querySelector('.treemap-menu');
            
            // 清空容器内容
            treeMapContainer.innerHTML = '';
            
            // 重新添加菜单栏（如果存在）
            if (menuBar) {
                treeMapContainer.appendChild(menuBar);
                // 隐藏菜单栏
                menuBar.style.display = 'none';
            }
            
            // 添加未连接提示
            const loadingDiv = document.createElement('div');
            loadingDiv.id = 'treemap-unconnected-div';
            loadingDiv.className = 'loading';
            loadingDiv.textContent = '⛔ 未连接后端，请检查服务是否启动';
            loadingDiv.style.color = '#999';
            loadingDiv.style.fontSize = '14px';
            loadingDiv.style.flex = '1';
            loadingDiv.style.display = 'flex';
            loadingDiv.style.justifyContent = 'center';
            loadingDiv.style.alignItems = 'center';
            treeMapContainer.appendChild(loadingDiv);
            treemap_have_content = false;
        }
    });
}

if (typeof when_connect_func_list !== 'undefined') {
    when_connect_func_list.push(function() {
        const block = get_block(TREEMAP_JS_MODULE_INDEX);
        const loadingElement = block.querySelector('#treemap-unconnected-div');
        if (loadingElement) {
            loadingElement.remove();
        }
        // if (treemap_have_content) {
        //     return;//对于小目录，有可能此时数据已经加载成功
        // }
        // // 添加加载提示
        // const loadingDiv = document.createElement('div');
        // loadingDiv.className = 'loading';
        // loadingDiv.textContent = '⏳ 正在加载数据...';
        // loadingDiv.style.flex = '1';
        // loadingDiv.style.display = 'flex';
        // loadingDiv.style.justifyContent = 'center';
        // loadingDiv.style.alignItems = 'center';
        // block.appendChild(loadingDiv);

    });
}
