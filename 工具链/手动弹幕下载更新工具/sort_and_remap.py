import json
import os
import time

def get_time(item):
    time_val = item.get('time')
    if time_val is None:
        item['time'] = 0
        return 0
    try:
        return float(time_val)
    except (ValueError, TypeError):
        return 0

def apply_time_filter(danmaku_list, time_filter):
    if not time_filter:
        return danmaku_list
    filtered = []
    for dm in danmaku_list:
        time = get_time(dm)
        start_time = time_filter[0][0]
        for range_start, range_end in time_filter:
            if range_start < start_time:
                start_time = range_start
        dm['time'] = time - start_time
        for range_start, range_end in time_filter:
            if range_start <= time <= range_end:
                filtered.append(dm)
                break
    return filtered

def apply_remap(time, cut_time, add_time_list):
    if cut_time > 0:
        first_time = 2 * cut_time
        a = 1 / (4 * cut_time)
        if time < first_time:
            time = a * time * time
        else:
            time = time - cut_time

    if add_time_list:
        sorted_add_time = sorted(add_time_list, key=lambda x: x[0])
        for start, end in sorted_add_time:
            if time > start:
                time = time + (end - start)
    return time

def process_config(input_file, config):
    with open(input_file, 'r', encoding='utf-8') as f:
        danmaku_list = json.load(f)

    time_filter = config.get('time_filter', [])
    cut_time = config.get('cut_time', 0)
    add_time = config.get('add_time', [])

    filtered = apply_time_filter(danmaku_list, time_filter)
    sorted_list = sorted(filtered, key=get_time)

    for item in sorted_list:
        time = get_time(item)
        time = apply_remap(time, cut_time, add_time)
        item['time'] = time

    return sorted_list

def get_source_info(danmaku_list):
    src_dict = {}
    for dm in danmaku_list:
        src = dm.get('src', '未知')
        send_time = dm.get('send-time', 0)
        if src not in src_dict:
            src_dict[src] = {'send_times': [], 'count': 0}
        src_dict[src]['send_times'].append(send_time)
        src_dict[src]['count'] += 1

    dm_src_list = []
    for name, data in src_dict.items():
        update_time = max(data['send_times']) if data['send_times'] else 0
        dm_src_list.append({
            'name': name,
            'url': '',
            'update-time': update_time,
            'dm-count': data['count']
        })
    return dm_src_list

def main():
    folder_path = input("请输入要处理的文件夹路径：\n").strip()
    if not folder_path:
        print("路径不能为空")
        return

    folder_path = os.path.abspath(folder_path)
    rmcf_path = os.path.join(folder_path, "rmcf.json")

    if not os.path.exists(rmcf_path):
        print(f"错误: 找不到配置文件 {rmcf_path}")
        return

    with open(rmcf_path, 'r', encoding='utf-8') as f:
        config_list = json.load(f)

    print(f"加载了 {len(config_list)} 个配置项\n")

    all_danmaku = []
    all_source_info = []

    for i, config in enumerate(config_list):
        dmsrc_file = config.get('dmsrc-file', '')
        print(f"[{i+1}/{len(config_list)}] 处理: {dmsrc_file}")

        input_file = os.path.join(folder_path, dmsrc_file)
        if not os.path.exists(input_file):
            print(f"  错误: 文件不存在 {input_file}")
            continue

        processed = process_config(input_file, config)
        print(f"  处理了 {len(processed)} 条弹幕")
        all_danmaku.extend(processed)

        source_info = get_source_info(processed)
        all_source_info.extend(source_info)

    all_danmaku = sorted(all_danmaku, key=get_time)
    print(f"\n合并后共 {len(all_danmaku)} 条弹幕")

    build_time = int(time.time())

    dm_info = {
        'dm-src': all_source_info,
        'dmjs-build-time': build_time,
        'dm-count': len(all_danmaku)
    }

    json_str = json.dumps(all_danmaku, ensure_ascii=False)
    output_content = f"const danmakuOpt_raw = {{speed:0.75,items:{json_str}}};function load_dm_opt(){{return danmakuOpt_raw;}}"

    output_file = os.path.join(folder_path, "dm.js")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output_content)
    print(f"成功: 已将排序后的数据写入 {output_file}")

    info_file = os.path.join(folder_path, "dm-info.json")
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(dm_info, f, ensure_ascii=False, indent=4)
    print(f"成功: 已将信息写入 {info_file}")

if __name__ == "__main__":
    main()