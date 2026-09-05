//执行完get_animate_banner_json.js再执行这个

/**
 * 从 Proxy(Array) 对象中下载所有 resource 图片（顺序下载，每张间隔1秒）
 * @param {Proxy|Array} proxyArray - 包含 resources 的 Proxy 数组对象
 * @param {Object} options - 下载选项
 * @param {number} options.interval - 下载间隔（毫秒），默认 1000ms
 * @param {boolean} options.useLayerName - 是否使用图层名称作为文件名，默认 true
 * @returns {Promise<void>}
 */
let downloadAllResources = async function(proxyArray, options = {}) {
    // 默认配置
    let config = {
        interval: 1000,  // 默认间隔 1 秒
        useLayerName: true,
        includeIndex: true
    };
    
    // 合并配置
    for (let key in options) {
        if (options.hasOwnProperty(key)) {
            config[key] = options[key];
        }
    }
    
    // 检查参数
    if (!proxyArray || !Array.isArray(proxyArray)) {
        console.error('❌ 参数错误：需要传入一个数组对象');
        return;
    }
    
    // 收集所有需要下载的图片信息
    let imageList = [];
    
    for (let i = 0; i < proxyArray.length; i++) {
        let layer = proxyArray[i];
        
        if (!layer || !layer.resources || !Array.isArray(layer.resources)) {
            console.warn(`⚠️ 图层 ${i} 没有 resources 属性，跳过`);
            continue;
        }
        
        for (let j = 0; j < layer.resources.length; j++) {
            let resource = layer.resources[j];
            
            if (!resource || !resource.src) {
                console.warn(`⚠️ 图层 ${i} 的资源 ${j} 没有 src，跳过`);
                continue;
            }
            
            let layerName = layer.name || `layer_${layer.id || i}`;
            let fileName = '';
            
            if (config.useLayerName && layerName) {
                fileName = layerName;
            } else {
                fileName = `layer_${layer.id || i}`;
            }
            
            if (config.includeIndex) {
                fileName = `${String(i).padStart(3, '0')}_${fileName}`;
            }
            
            if (layer.resources.length > 1) {
                fileName = `${fileName}_resource_${j}`;
            }
            
            // 从 URL 提取扩展名
            let extension = 'png';
            let urlMatch = resource.src.match(/\.(png|jpg|jpeg|gif|webp|svg|bmp|ico)$/i);
            if (urlMatch) {
                extension = urlMatch[1].toLowerCase();
            }
            
            // 清理文件名
            fileName = fileName.replace(/[<>:"/\\|?*\x00-\x1F]/g, '_');
            fileName = `${fileName}.${extension}`;
            
            imageList.push({
                src: resource.src,
                fileName: fileName,
                layerName: layerName,
                index: i
            });
        }
    }
    
    console.log(`📥 准备下载 ${imageList.length} 张图片，每张间隔 ${config.interval}ms`);
    console.log('⏳ 开始下载，请耐心等待...\n');
    
    let successCount = 0;
    let failCount = 0;
    let failedList = [];
    
    // 顺序下载每张图片
    for (let i = 0; i < imageList.length; i++) {
        let image = imageList[i];
        let currentNum = i + 1;
        
        try {
            console.log(`⬇️ [${currentNum}/${imageList.length}] 下载中: ${image.fileName}`);
            
            // 下载图片
            let response = await fetch(image.src);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            let blob = await response.blob();
            
            // 创建下载链接
            let url = URL.createObjectURL(blob);
            let link = document.createElement('a');
            link.href = url;
            link.download = image.fileName;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // 延迟释放 URL
            setTimeout(function() {
                URL.revokeObjectURL(url);
            }, 1000);
            
            successCount++;
            console.log(`✅ [${currentNum}/${imageList.length}] 下载成功: ${image.fileName}`);
            
        } catch (error) {
            failCount++;
            failedList.push({
                fileName: image.fileName,
                error: error.message
            });
            console.error(`❌ [${currentNum}/${imageList.length}] 下载失败: ${image.fileName} - ${error.message}`);
        }
        
        // 如果不是最后一张，等待间隔时间
        if (i < imageList.length - 1) {
            console.log(`⏰ 等待 ${config.interval}ms 后下载下一张...\n`);
            await new Promise(function(resolve) {
                setTimeout(resolve, config.interval);
            });
        }
    }
    
    // 输出统计信息
    console.log('\n📊 下载统计:');
    console.log(`   总图片数: ${imageList.length}`);
    console.log(`   成功: ${successCount}`);
    console.log(`   失败: ${failCount}`);
    
    if (failCount > 0) {
        console.log('\n❌ 失败的图片:');
        for (let item of failedList) {
            console.log(`   - ${item.fileName}: ${item.error}`);
        }
        
        // 提供重试函数
        console.log('\n💡 如需重试失败的图片，可以查看 failedList 变量');
    }
    
    console.log('\n🎉 下载任务完成！');
    
    // 返回结果
    return {
        total: imageList.length,
        success: successCount,
        fail: failCount,
        failedList: failedList,
        imageList: imageList
    };
};

downloadAllResources(window.animebar_proxyArray);