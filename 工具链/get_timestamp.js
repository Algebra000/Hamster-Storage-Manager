//本脚本用于在浏览器控制台执行以获取当前时间戳

// 获取当前时间戳（秒级）
const nowSeconds = Math.floor(Date.now() / 1000);
console.log("当前时间戳（秒）:", nowSeconds);

// 获取当前时间戳（毫秒级）
const nowMilliseconds = Date.now();
console.log("当前时间戳（毫秒）:", nowMilliseconds);

// 同时输出对应的可读时间（本地时区）
console.log("当前时间（本地）:", new Date().toLocaleString());