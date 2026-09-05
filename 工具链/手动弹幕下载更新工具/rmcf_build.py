import json
import os
import re

#想要保留什么时间段里的弹幕？请输入时间范围，只有这个范围里的弹幕才会被添加到dm.js\n时间范围格式 <小时>h<分钟>m<秒>s-<小时>h<分钟>m<秒>s，空输入默认保留所有弹幕。\n例如：0h30m0s-1h0m0s\n")


def parse_time(time_str):
    match = re.match(r'(\d+)h(\d+)m(\d+)s', time_str)
    if match:
        hours, minutes, seconds = match.groups()
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    return None

def format_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours}h{minutes}m{secs}s"

def parse_time_range(range_str):
    if '-' not in range_str:
        return None
    start, end = range_str.split('-')
    start_sec = parse_time(start)
    end_sec = parse_time(end)
    if start_sec is not None and end_sec is not None:
        return [start_sec, end_sec]
    return None

def input_time_filter():
    filters = []
    while True:
        line = input("想要保留什么时间段里的弹幕？请输入时间范围，只有这个范围里的弹幕才会被添加到dm.js\n时间范围格式 <小时>h<分钟>m<秒>s-<小时>h<分钟>m<秒>s，空输入默认保留所有弹幕。\n例如：0h30m0s-1h0m0s\n")
        if line == '':
            break
        parsed = parse_time_range(line)
        if parsed:
            filters.append(parsed)
            print(f"已添加过滤器: {parsed}")
            break
        else:
            print("格式错误，请重新输入")
    return filters

def input_cut_time():
    while True:
        line = input("如果过滤器截出的弹幕网站源视频有片头而本地视频没有，请输入这个片头时间（单位秒），空输入默认为0：")
        if line == '':
            return 0
        try:
            return float(line)
        except ValueError:
            print("请输入有效数字")

def input_add_time():
    add_times = []
    print("如果过滤器截出的弹幕网站源视频片段有删减而本地视频完整，那么请输入被删减的片段\033[91m在本地视频里的\033[0m时间段。\n格式：\n<小时>h<分钟>m<秒>s-<小时>h<分钟>m<秒>s <小时>h<分钟>m<秒>s-<小时>h<分钟>m<秒>s ......\n不同时间段用空格隔开，空输入跳过。\n")
    line = input("例如：0h30m0s-1h0m0s 1h30m0s-2h0m0s\n")
    if line == '':
        return add_times
    
    time_ranges = line.split()
    for time_range in time_ranges:
        parsed = parse_time_range(time_range)
        if parsed:
            add_times.append(parsed)
            print(f"已添加补偿段: {parsed}")
        else:
            print(f"格式错误，跳过: {time_range}")
    return add_times

def input_add_time_text():
    text = input("请输入add_time_text（删减片段的说明文字），空输入默认为\"(此处为B站删减片段)\"：\n")
    return text if text != '' else "(此处为B站删减片段)"

def build_rmcf_item():
    item = {}
    item['dmsrc-file'] = input("请输入弹幕源文件名（例如：dm.json）：\n")
    item['time_filter'] = input_time_filter()
    item['cut_time'] = input_cut_time()
    item['add_time'] = input_add_time()
    item['add_time_text'] = input_add_time_text()
    return item

def main():
    config = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rmcf_path = os.path.join(script_dir, "rmcf.json")

    if os.path.exists(rmcf_path):
        print(f"检测到已存在的配置文件: {rmcf_path}")
        load_choice = input("是否加载现有配置？(y/n，空输入默认为n)：")
        if load_choice.lower() == 'y':
            try:
                with open(rmcf_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"已加载 {len(config)} 个配置项")
            except Exception as e:
                print(f"加载失败: {e}，将重新创建")

    while True:
        print("\n" + "="*50)
        print("当前配置列表：")
        for i, item in enumerate(config):
            print(f"  {i+1}. {item['dmsrc-file']}")
        print("="*50)
        print("1. 添加新的弹幕源配置(默认选项)")
        print("2. 编辑现有配置")
        print("3. 删除配置")
        print("4. 保存并退出")
        print("5. 放弃更改并退出")
        choice = input("请选择操作（空输入默认为1）：\n")

        if choice == '' or choice == '1':
            while True:
                new_item = build_rmcf_item()
                config.append(new_item)
                print(f"已添加配置: {new_item['dmsrc-file']}")
                next_choice = input("是否继续添加配置？空输入则继续，有输入停止")
                if next_choice == '':
                    continue
                else:
                    break

        elif choice == '2':
            if not config:
                print("没有可编辑的配置项")
                continue
            idx = input(f"请输入要编辑的配置编号（1-{len(config)}）：\n")
            try:
                idx = int(idx) - 1
                if 0 <= idx < len(config):
                    old_file = config[idx]['dmsrc-file']
                    print(f"正在编辑: {old_file}")
                    new_item = build_rmcf_item()
                    config[idx] = new_item
                    print(f"已更新配置")
                else:
                    print("编号无效")
            except ValueError:
                print("请输入有效数字")

        elif choice == '3':
            if not config:
                print("没有可删除的配置项")
                continue
            idx = input(f"请输入要删除的配置编号（1-{len(config)}）：\n")
            try:
                idx = int(idx) - 1
                if 0 <= idx < len(config):
                    removed = config.pop(idx)
                    print(f"已删除配置: {removed['dmsrc-file']}")
                else:
                    print("编号无效")
            except ValueError:
                print("请输入有效数字")

        elif choice == '4':
            try:
                with open(rmcf_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
                print(f"配置已保存到: {rmcf_path}")
            except Exception as e:
                print(f"保存失败: {e}")
            return

        elif choice == '5':
            print("已放弃更改")
            return

        else:
            print("无效选择")

if __name__ == "__main__":
    main()