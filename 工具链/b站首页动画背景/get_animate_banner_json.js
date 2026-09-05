//使用方法，document.querySelector(".animated-banner").querySelectorAll("img")
//然后其中找到一动态img断点后执行该js

/**
 * 将 Proxy(Array) 对象转换为格式化的 JSON 字符串
 * @param {Proxy|Array|Object} proxyArray - Proxy 包装的数组或其他对象
 * @param {number} indent - 缩进空格数，默认 2
 * @returns {string} 格式化的 JSON 字符串
 */
let proxyArrayToFormattedJSON = function(proxyArray, indent = 4) {
    /**
     * 深拷贝函数，处理 Proxy 和循环引用
     */
    let deepClone = function(obj, seen = new WeakMap()) {
        // 基本类型直接返回
        if (obj === null || typeof obj !== 'object') {
            return obj;
        }
        
        // 检查循环引用
        if (seen.has(obj)) {
            return seen.get(obj);
        }
        
        // 处理 Date
        if (obj instanceof Date) {
            let dateClone = new Date(obj);
            return dateClone;
        }
        
        // 处理 RegExp
        if (obj instanceof RegExp) {
            let regExpClone = new RegExp(obj);
            return regExpClone;
        }
        
        // 处理 Map
        if (obj instanceof Map) {
            let mapClone = new Map();
            seen.set(obj, mapClone);
            for (let [key, value] of obj) {
                mapClone.set(key, deepClone(value, seen));
            }
            return mapClone;
        }
        
        // 处理 Set
        if (obj instanceof Set) {
            let setClone = new Set();
            seen.set(obj, setClone);
            for (let value of obj) {
                setClone.add(deepClone(value, seen));
            }
            return setClone;
        }
        
        // 处理数组
        if (Array.isArray(obj)) {
            let arrClone = [];
            seen.set(obj, arrClone);
            for (let i = 0; i < obj.length; i++) {
                arrClone[i] = deepClone(obj[i], seen);
            }
            return arrClone;
        }
        
        // 处理普通对象
        let objClone = {};
        seen.set(obj, objClone);
        
        // 获取所有可枚举属性（包括继承的）
        for (let key of Object.keys(obj)) {
            try {
                objClone[key] = deepClone(obj[key], seen);
            } catch (e) {
                console.warn(`无法克隆属性 ${key}:`, e);
                objClone[key] = undefined;
            }
        }
        
        return objClone;
    };
    
    // 先尝试直接序列化
    try {
        // 对于大多数 Proxy 对象，直接 JSON.stringify 应该能工作
        let jsonString = JSON.stringify(proxyArray, null, indent);
        return jsonString;
    } catch (error) {
        console.warn('直接 JSON.stringify 失败，使用深度克隆方法:', error);
        // 如果失败，先深拷贝再序列化
        let clonedObj = deepClone(proxyArray);
        let jsonString = JSON.stringify(clonedObj, null, indent);
        return jsonString;
    }
};

// 使用示例：
// 假设你已经有了目标数组（比如之前搜索到的 window.__foundTargetArray）
let jsonString = proxyArrayToFormattedJSON(f);
console.log(jsonString);
window.animebar_proxyArray = f;

