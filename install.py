import os
import json
import time
import importlib
import sys


def show_base_dir(path_list):
    print("当前管理的资源根目录有：")
    print("————————————————————————")
    index = 0
    for path in path_list:
        print(f" {index}. {path}")
        index += 1
    print("————————————————————————")
    print("")

def edit_base_dir(path_list) -> bool:
    """
    编辑操作根目录，返回False表示退出编辑
    """
    print("支持的操作指令如下（不区分大小写）：\n\n 1. del <序号>\n删除指定序号的资源根目录\n例如：del 0 删掉序号为0的资源根目录。\n\n 2. add <路径>\n添加指定路径为要管理的资源目录。\n例如：add D:/我的资源/\n 添加“D:/我的资源/”为要管理的资源目录\n\n 3. 无输入退出编辑\n\n请输入指令：")
    cmd = input(">")
    if not cmd:
        return False
    cmd = cmd.strip()
    if len(cmd) <= 4:
        print("未知指令。\n\a")
        return True
    try:
        cmd_keyword = cmd[:4].lower()
    except Exception:
        print("未知指令。\n\a")
        return True
    if cmd_keyword == "del ":
        try:
            index = int(cmd[4:].strip())
        except ValueError:
            print("失败，应该在del指令后输入一个整数序号。\n\a")
            return True
        if index < 0 or index >= len(path_list):
            print("\a失败，del指令后序号超出范围。\n")
            return True
        path_list.pop(index)
        print(f"删除成功")
        show_base_dir(path_list)
        return True

    elif cmd_keyword == "add ":
        path = cmd[4:].strip()
        if not path:
            print("\a失败，应该在add指令后输入一个路径。\n")
            return True
        try:
            path = os.path.normpath(path)
        except Exception as e:
            print(f"添加失败，路径格式错误。\n\a")
            return True
        path_list.append(path)
        print(f"添加成功，当前操作根目录为：")
        show_base_dir(path_list)
        return True

    else:
        print("未知指令。\n\a")
        return True

def set_all_module(mods):
    """
    设置所有模块的配置
    mods: 所有已安装模块的列表，每个元素是一个元组: (module_name, module_info)
    """
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    original_dir = os.getcwd()
    original_sys_path = sys.path[:]
    try:
        # 与后端运行时保持一致，支持模块导入 config 及使用相对配置路径。
        sys.path.insert(0, backend_dir)
        for module_name, module_info in mods:
            try:
                os.chdir(backend_dir)
                module_path = module_info.get("path")
                if not isinstance(module_path, str) or not module_path.strip():
                    print(f"跳过模块 {module_name}：未配置有效的 path。")
                    continue
                module = importlib.import_module(module_path.replace('/', '.'))
                settings = getattr(module, "settings", None)
                if not callable(settings):
                    print(f"跳过模块 {module_name}：没有可调用的配置函数。")
                    continue
                print(f"\n开始配置模块 {module_name}：")
                settings()
                print(f"模块 {module_name} 配置完成。")
            except Exception as e:
                print(f"模块 {module_name} 配置失败：{e}")
    finally:
        os.chdir(original_dir)
        sys.path[:] = original_sys_path


print("欢迎安装仓鼠存储管理器\n")
time.sleep(0.8)
print("现在我们确定一下必要的配置，以使得软件能够正常运行。")
global_config = {}
path_list = []
if os.path.exists("./backend/config/global_config.json"):
    try:
        with open("./backend/config/global_config.json", "r", encoding="utf-8") as f:
            global_config = json.load(f)
        path_list = global_config.get("base_dir", [])
        if not isinstance(path_list, list):
            raise ValueError("base_dir 必须是一个列表")
        print("检测到已有配置文件，成功加载配置文件。")
        print("首先我们先设置要管理的资源目录有哪些，管理器将管理这些目录下的所有文件和文件夹。")
        show_base_dir(path_list)

    except Exception as e:
        print(f"加载配置文件时出错：{e}")
        print("我们将从头开始设置。")
        print("首先我们先设置要管理的资源目录有哪些，管理器将管理这些目录下的所有文件和文件夹。")
else:
    print("我们将从头开始配置软件。")
    print("首先我们先设置要管理的资源目录有哪些，管理器将管理这些目录下的所有文件和文件夹。")
while edit_base_dir(path_list):
    time.sleep(2)
global_config["base_dir"] = path_list
with open("./backend/config/global_config.json", "w", encoding="utf-8") as f:
    json.dump(global_config, f, ensure_ascii=False, indent=4)
print("全局配置完成，已保存全局配置\n 接下来扫描模块配置文件\n")
module_config = {
    "modules": {}
}
if os.path.exists("./backend/config/module_config.json"):
    try:
        with open("./backend/config/module_config.json", "r", encoding="utf-8") as f:
            module_config = json.load(f)
        mods = module_config.get('modules', {}).items()
        if len(mods) > 0:
            print("检测到管理器目前已安装以下模块：")
            for module_name, module_info in mods:
                print(module_name)
            choice_2 = input("\n是否继续配置这些模块？无输入将继续配置，输入任何字符回车将跳过。")
            if not choice_2:
                set_all_module(mods)

        else:
            print("管理器目前没有安装任何模块。\n")
    except Exception as e:
        print(f"检测到原有模块配置文件未能成功读取，将默认没有安装任何模块。\n")
        choice_1 = input("是否尝试以空的模块配置文件覆盖现在的模块配置文件？无输入将尝试覆盖，输入任何字符回车将跳过。")
        if choice_1:
            try:
                with open("./backend/config/module_config.json", "w", encoding="utf-8") as f:
                    json.dump(module_config, f, ensure_ascii=False, indent=4)
                print("已成功覆盖模块配置文件。\n")
                time.sleep(0.8)
            except Exception as e:
                print(f"覆盖模块配置文件时出错。\n\a")
                module_config = {}
else:
    with open("./backend/config/module_config.json", "w", encoding="utf-8") as f:
        json.dump(module_config, f, ensure_ascii=False, indent=4)
    print("./backend/config/module_config.json 文件不存在，已创建空的模块配置文件，默认没有安装任何模块。")


