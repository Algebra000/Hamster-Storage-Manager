# server.py - 主后端服务
import asyncio
import websockets
import json
import os
import importlib

USE_PORT = 8768 #要使用的端口
BACK_VERSION = 'ROLAND 1.0.0'

# 获取脚本所在目录的绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))

# 加载 global_config.json
global_config_path = os.path.join(script_dir, 'config', 'global_config.json')
base_dirs = []
global_config = {}

if os.path.exists(global_config_path) and os.path.isfile(global_config_path):
    try:
        with open(global_config_path, 'r', encoding='utf-8') as f:
            global_config = json.load(f)
            base_dirs = global_config.get('base_dir', [])
            print(f"成功加载全局配置，根目录列表: {base_dirs}")
    except Exception as e:
        print(f"加载全局配置失败: {e}")
else:
    print("全局配置文件不存在，使用默认根目录列表")
    base_dirs = ["./"]
    global_config['base_dir'] = base_dirs

# 处理根目录列表
real_base_dirs = []
for base_dir in base_dirs:
    real_path = os.path.abspath(os.path.join(script_dir, base_dir))
    if os.path.exists(real_path):
        real_base_dirs.append(real_path)
    else:
        print(f"根目录不存在: {real_path}")

print(f"实际根目录列表: {real_base_dirs}")
global_config['base_dir'] = real_base_dirs

# 模块管理
class ModuleManager:
    def __init__(self):
        self.modules = {}
        self.load_modules()
    
    def load_modules(self):
        """加载模块"""
        # 加载 module_config.json
        model_config_path = os.path.join(script_dir, 'config', 'module_config.json')
        if os.path.exists(model_config_path) and os.path.isfile(model_config_path):
            try:
                with open(model_config_path, 'r', encoding='utf-8') as f:
                    model_config = json.load(f)
                    for module_name, module_info in model_config.get('modules', {}).items():
                        if module_info.get('enabled', True):
                            self.load_module(module_name, module_info)
            except Exception as e:
                print(f"加载模块配置失败: {e}")
        else:
            print("模块配置文件不存在,未加载任何模块")
            # 加载默认模块
            #self.load_default_modules()
    
    def load_module(self, module_name, module_info):
        """加载单个模块"""
        try:
            # 导入模块
            module_path = module_info.get('path')
            if module_path:
                # 动态导入模块
                module = importlib.import_module(module_path.replace('/', '.'))
                # 调用模块工厂函数创建实例
                if hasattr(module, 'create_module'):
                    module_instance = module.create_module(global_config, BACK_VERSION)
                    self.modules[module_name] = module_instance
                    print(f"成功加载模块: {module_name}")
                else:
                    print(f"模块 {module_name} 缺少 create_module 函数")
            else:
                print(f"模块 {module_name} 缺少路径配置")
        except Exception as e:
            print(f"加载模块 {module_name} 失败: {e}")
    
    # def load_default_modules(self):
    #     """加载默认模块"""
    #     # 加载树状图模块
    #     try:
    #         from treemap_back import create_module as create_treemap_module
    #         treemap_module = create_treemap_module()
    #         self.modules['treemap'] = treemap_module
    #         print("成功加载默认模块: treemap")
    #     except Exception as e:
    #         print(f"加载默认模块失败: {e}")
    
    def get_module(self, module_name):
        """获取模块实例"""
        return self.modules.get(module_name)

# 初始化模块管理器
module_manager = ModuleManager()

async def handler(websocket, path=None):
    print("客户端已连接")
    try:
        pathstr = "; ".join(real_base_dirs)
        # 发送当前路径信息
        message = json.dumps({
            "command": 'SET_NOWPATH',
            'path': pathstr
        })
        await websocket.send(message)
        
        # 初始化模块连接
        for module_name, module in module_manager.modules.items():
            await module.when_connect(websocket)
        
        # 发送模块初始配置
        # treemap_module = module_manager.get_module('treemap')
        # if treemap_module:
        #     await treemap_module.send_initial_config(websocket)
        #     # 扫描目录结构并发送数据
        #     await treemap_module.scan_directory_structure(websocket, real_base_dirs)

        # 保持连接，等待客户端请求更多数据
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                data = json.loads(response)
                
                # 处理不同的命令
                for module_name, module in module_manager.modules.items():
                    await module.message_proc(websocket, data)
                
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                break

    except websockets.exceptions.ConnectionClosed:
        print("客户端断开连接")
    except Exception as e:
        print(f"处理过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 无论是正常断线、协议异常还是服务任务被取消，都统一回收连接资源。
        for module_name, module in module_manager.modules.items():
            try:
                await module.when_disconnect(websocket)
            except Exception as cleanup_error:
                print(f"模块 {module_name} 断线清理失败: {cleanup_error}")

async def main():
    print(f"准备启动WebSocket服务器，端口: {USE_PORT}")
    try:
        async with websockets.serve(handler, "localhost", USE_PORT):
            print("WebSocket服务器启动在 ws://localhost:{}".format(USE_PORT))
            await asyncio.Future()  # 永久运行
    except Exception as e:
        print(f"启动服务器时出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        for module_name, module in module_manager.modules.items():
            shutdown = getattr(module, 'shutdown', None)
            if shutdown:
                try:
                    await shutdown()
                except Exception as cleanup_error:
                    print(f"模块 {module_name} 关闭清理失败: {cleanup_error}")

if __name__ == "__main__":
    asyncio.run(main())
