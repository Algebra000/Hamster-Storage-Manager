import asyncio
import os
from bilibili_api import Credential, Danmaku
import json
from bilibili_api import video
import time
from bilibili_api.utils.network import ResponseCodeException
from bilibili_api.utils.network import get_aiohttp_session
import re
import colorama

colorama.init()

os.environ['NO_PROXY'] = 'bilibili.com,api.bilibili.com,*.bilibili.com,127.0.0.1,localhost'

async def download_dm_by_bv(bv: str, p: int = 1, credential: Credential = None, save_path: str = None):
    """
    根据BV号下载视频的弹幕文件

    Args:
        bv: B站视频BV号
        p: 分P号，从1开始
        credential: 登录凭证
        save_path: 保存文件路径，默认为 {bv}_p{p}.json
    
    Returns:
        str: 保存的文件路径，失败返回 None
    """


    v = video.Video(bvid=bv, credential=credential)
    try:
        dms = await v.get_danmakus(page_index=p - 1)
    except asyncio.TimeoutError as e:
        print(f"[Bilibili信息抓取模块] 获取弹幕失败: {e}")
        return None
    except ResponseCodeException as e:
        print(f"[Bilibili信息抓取模块] 稿件已失效: {e}")
        return None
    
    dmlist = []
    for dm in dms:
        if not dm.text:
            continue
        
        if dm.mode == 1:
            typestr = "scroll"
        elif dm.mode == 4:
            typestr = "bottom"
        elif dm.mode == 5:
            typestr = "top"
        elif dm.mode == 7:
            typestr = "special"
        else:
            typestr = "other"

        is_colorful = False
        if dm.colorful:
            is_colorful = True
        
        dmdic = {
                "time": dm.dm_time,
                "text": dm.text,
                "type": typestr,
                "color": f"#{str(dm.color).zfill(6)}",
                "dmid": dm.id_str,
                "is-colorful": is_colorful, # 是否为大会员专属彩色弹幕
                "like-count": dm.like_count,
                "oid": dm.oid,
                "font-size": dm.font_size,
                "send-time": dm.send_time,
                "weight": dm.weight,
                "uhash": dm.crc32_id,
                "src": "B站"
            }
        dmlist.append(dmdic)
    
    save_filename = save_path or f"{bv}_p{p}.json"
    with open(save_filename, 'w', encoding='utf-8') as f:
        f.write(json.dumps(dmlist, ensure_ascii=False, indent=4))
    
    return save_filename


def build_dm(basepath: str) -> bool:
    """
    整合不同历史版本的弹幕数据并构建弹幕目录

    Args:
        basepath: 要在其中构建弹幕目录的路径，包含已经下载好的所有弹幕文件的raw目录
    Returns:
        bool: 是否成功构建弹幕文件目录
    """
    raw_dir = os.path.join(basepath, 'raw')
    if not (os.path.exists(raw_dir) and os.path.isdir(raw_dir)):
        print(f"raw目录不存在: {raw_dir}")
        return False
    json_files = [f for f in os.listdir(raw_dir) if f.endswith('.json')]
    
    if not json_files:
        print("错误：raw 目录中没有 JSON 文件")
        return False
    
    categories = {}
    
    for filename in json_files:
        match = re.match(r'^(.+)-(\d+)\.json$', filename)
        if match:
            base_name = match.group(1)
            if re.search(r'-\d+$', base_name):
                continue
        else:
            base_name = filename[:-5]
        
        if re.search(r'-\d+$', base_name):
            continue
        
        if base_name not in categories:
            categories[base_name] = []
        categories[base_name].append(filename)
    
    for base_name, files in categories.items():
        all_danmaku = []
        seen_dmids = set()
        seen_oids = set()
        
        is_src_changed = False #这个视频的弹幕源是否发生过更换

        for filename in files:
            filepath = os.path.join(raw_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        if len(data)>0:
                            seen_oids.add(data[0].get('oid',0))
                            if len(seen_oids) > 1:
                                is_src_changed = True
                        all_danmaku.extend(data)
            except Exception as e:
                print(f"读取文件 {filename} 时出错: {e}")

        #也要判断是否存在现有的弹幕文件，存在则合并
        output_path = os.path.join(basepath, f"{base_name}.json")
        if os.path.exists(output_path) and os.path.isfile(output_path):
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                all_danmaku.extend(existing_data)
            except Exception as e:
                    print(f"读取文件 {output_path} 时出错: {e}")

        unique_danmaku = []
        if is_src_changed:
            print(colorama.Fore.YELLOW + "################################")
            print("           警告！！！")
            print(f"{base_name} 的弹幕源发生过更换, 将采用基于时间和内容的去重策略。")
            print("请着重注意一下本弹幕源的合并结果。")
            print("################################" + colorama.Style.RESET_ALL)
            for item in all_danmaku:
                vd_time = item.get('time',0)
                vd_text = item.get('text','')
                send_time = item.get('send-time','')
                total_key = (vd_time, vd_text, send_time)
                if total_key not in seen_dmids:
                    seen_dmids.add(total_key)
                    unique_danmaku.append(item)
        else:
            for item in all_danmaku:
                dmid = item.get('dmid')
                if dmid and dmid not in seen_dmids:
                    seen_dmids.add(dmid)
                    unique_danmaku.append(item)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(unique_danmaku, f, ensure_ascii=False, indent=4)
        
        print(f"已生成 {output_path}，共 {len(unique_danmaku)} 条弹幕")

def build_rmcf(basepath: str) -> bool:
    """
    构建重映射配置文件

    Args:
        basepath: 要在其中构建重映射配置文件的路径，包含已经下载好的所有弹幕文件的raw目录
    Returns:
        bool: 是否成功构建重映射配置文件
    """
    rmcf_list = []
    pre_rmcf_dir = os.path.join(basepath, 'rmcf.json')
    if os.path.exists(pre_rmcf_dir):
        with open(pre_rmcf_dir, 'r', encoding='utf-8') as f:
            try:
                rmcf_list = json.load(f)
            except json.JSONDecodeError:
                choice = input(f"文件{pre_rmcf_dir}内容不是有效的JSON格式，是否新建列表并覆盖文件内容?无输入默认覆盖原文件，有输入则放弃构建rmcf.json")
                if choice:
                    return False
    rmcf_filename_list = {rmcf_list[ind].get("dmsrc-file", ""): ind for ind in range(len(rmcf_list))}
    srcURL_path = os.path.join(basepath, 'dm-srcURL.json')
    if not os.path.exists(srcURL_path):
        print(f"错误：dm-srcURL.json文件不存在: {srcURL_path}")
        return False
    with open(srcURL_path, 'r', encoding='utf-8') as f:
        src_list = json.load(f)
    for item in src_list:
        rmcf_info = item.get("rmcf", {})
        if rmcf_info:
            dmsrc_file = rmcf_info.get("dmsrc-file", "")
            ind_ = rmcf_filename_list.get(dmsrc_file, -1)
            if ind_ != -1:
                rmcf_list[ind_] = rmcf_info
                print(f"已覆盖 {dmsrc_file} 的重映射配置")
            else:
                rmcf_list.append(rmcf_info)
                rmcf_filename_list[dmsrc_file] = len(rmcf_list) - 1
    
    with open(pre_rmcf_dir, 'w', encoding='utf-8') as f:
        json.dump(rmcf_list, f, ensure_ascii=False, indent=4)
    print(f"已生成 {pre_rmcf_dir}，共 {len(rmcf_list)} 条重映射配置")






async def main():
    use_cookie = {}
    if not os.path.exists('cookie.json'):
        print("cookie.json 文件不存在，将退出程序")
        return
    with open('cookie.json', 'r', encoding='utf-8') as f:
        use_cookie = json.load(f)
        
    is_auto_build = not input("下载完成后是否需要自动构建弹幕目录？有输入不自动构建，无输入默认自动构建")
    
    credential_ = Credential(
        sessdata=use_cookie["SESSDATA"],
        bili_jct=use_cookie["bili_jct"],
        buvid3=use_cookie["buvid3"]
    )

    with open('./basepath.json', 'r', encoding='utf-8') as f:
        basepath_list = json.load(f)

    for i in basepath_list:
        dm_srcURL_path = os.path.join(i, 'dm-srcURL.json')
        if not (os.path.exists(i) and os.path.isdir(i) and os.path.exists(dm_srcURL_path)):
            print(f"路径不存在或 {dm_srcURL_path} 不存在: {i}")
            continue

        dm_dir = os.path.join(i, 'raw')
        if not os.path.exists(dm_dir):
            os.makedirs(dm_dir)

        with open(dm_srcURL_path, 'r', encoding='utf-8') as f:
            src_list = json.load(f)

        for item in src_list:
            src = item.get("src")
            bv = item.get("BV")
            p = item.get("p", 1)
            name = item.get("name")

            dm_path = os.path.join(dm_dir, f"{name}.json")
            new_path = dm_path
            if os.path.exists(dm_path):
                # print(f"文件已存在: {dm_path}")
                num = 1
                while True:
                    num += 1
                    new_path = os.path.join(dm_dir, f"{name}-{num}.json")
                    if not os.path.exists(new_path):
                        break

            if src == "B站":
                print(f"正在下载: {bv} P{p} -> {name}")
                result = await download_dm_by_bv(bv, p, credential_, new_path)
                if result:
                    print(f"下载完成: {result}")
                else:
                    print(f"下载失败: {bv} P{p}")
            
            time.sleep(2)
            
        print(f"目录完成: {i}")

        if is_auto_build:
            print(f"正在构建弹幕目录: {i}")
            build_dm(i)
            print(f"正在生成或更新重映射配置文件: {i}")
            build_rmcf(i)
        else:
            choose = input(f"是否需要手动构建弹幕目录和重映射配置文件？无输入默认开始构建，有输入跳过")
            if not choose:
                print(f"正在构建弹幕目录: {i}")
                build_dm(i)
                print(f"正在生成或更新重映射配置文件: {i}")
                build_rmcf(i)
    try:
        session = get_aiohttp_session()
        await session.close()
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())
