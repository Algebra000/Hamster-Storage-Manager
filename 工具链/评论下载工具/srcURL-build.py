import os
import json
import re
#from bilibili_api import bangumi
from bilibili_api import Credential
from html.parser import HTMLParser
import httpx

os.environ['NO_PROXY'] = 'bilibili.com,api.bilibili.com,*.bilibili.com,127.0.0.1,localhost'

use_cookie = {}
with open("cookie.json","r") as f:
    use_cookie = json.load(f)
credential_ = Credential(sessdata=use_cookie["SESSDATA"],
  bili_jct=use_cookie["bili_jct"], 
  buvid3=use_cookie["buvid3"])

def is_num_str(str: str)->bool:
    """
    判断字符串是否为数字
    """
    try:
        int(str)
        return True
    except ValueError:
        return False

class _ScriptParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.current_script = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            self.in_script = True
            self.current_script = []

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.in_script:
            self.scripts.append("".join(self.current_script))
            self.current_script = []
            self.in_script = False

    def handle_data(self, data):
        if self.in_script:
            self.current_script.append(data)


def extract_json_from_scripts(html: str) -> list:
    """
    提取 HTML 中所有 <script> 标签里的合法 JSON 对象。

    只返回顶层为 dict 的 JSON：
        {...}

    不返回顶层 JSON 数组：
        [...]

    仅使用 Python 标准库。
    """
    parser = _ScriptParser()
    parser.feed(html)

    decoder = json.JSONDecoder()
    result = []

    for script in parser.scripts:
        i = 0

        while i < len(script):
            # 只寻找 JSON Object
            if script[i] != "{":
                i += 1
                continue

            try:
                obj, end = decoder.raw_decode(script, i)

                if isinstance(obj, dict):
                    result.append(obj)

                # 成功解析后直接跳过整个 JSON，
                # 防止其内部嵌套 dict 被重复提取
                i = end

            except json.JSONDecodeError:
                i += 1

    return result

def convert_ep_to_BV(ep_id: int, credential: Credential)->str:
    """
    将番剧ID转换为BV号
    """
    def try_get_bv_in_json(dic: dict)->str:
        """
        从JSON字典中提取BV号
        """
        try:
            bvid_ = dic["data"]["result"]["arc"]["bvid"]
        except KeyError:
            bvid_ = ""
        return bvid_

    
    url=f"https://www.bilibili.com/bangumi/play/ep{ep_id}"
    try:
        resp = httpx.get(
            url,
            cookies=credential.get_cookies(),
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
        )
    except Exception as e:
        print(f"获取番剧剧集ep{ep_id}详情失败: {e}")
        return ""
    else:
        content = resp.text
        objects = extract_json_from_scripts(content)
        bvid = ""
        for obj in objects:
            if ("status" in obj) and ("data" in obj):
                bvid = try_get_bv_in_json(obj)
                if bvid:
                    break
       
    return bvid


def bili_video_url_parse(url: str)->dict:
    """
    解析B站视频URL，返回视频信息
    """
    out = {
        "bvid": "",
        "p": 1
    }
    
    if url.startswith("https://www.bilibili.com/video/"):
        value_str = url[31:]
        if not value_str.startswith("BV"):
            print(f"URL{url}不是BV号URL")
            return {}
        value_list = value_str.split("/?")
        if len(value_list) == 1:
            value_list = value_list[0].split("?")
        if len(value_list) == 1:
            out["bvid"] = value_list[0]
        elif len(value_list) == 2:
            out["bvid"] = value_list[0]
            params_list = value_list[1].split("&")
            for param in params_list:
                if param.startswith("p"):
                    key_value = param.split("=")
                    if len(key_value) == 2 and is_num_str(key_value[-1]):
                        out["p"] = int(key_value[1])
                    else:
                        print(f"URL{url}不合法的p参数格式")
                        break
        else:
            print(f"URL{url}不合法")
            return {}
    elif url.startswith("https://www.bilibili.com/bangumi/play/"):
        value_str = url[38:]
        if not value_str.startswith("ep"):
            print(f"URL{url}不是ep号番剧URL")
            return {}
        value_list = value_str.split("/?")
        ep_id_str = ''
        value_list_ = []
        for i in range(len(value_list)):
            value_list_ += value_list[i].split("?")
        value_list = value_list_
        if len(value_list) == 1 or len(value_list) == 2:
            ep_id_str = value_list[0][2:]
        else:
            print(f"URL{url}不合法")
            return {}
        ep_id = 0
        if not is_num_str(ep_id_str):
            print(f"URL{url}不合法的ep号格式")
            return {}
        else:
            ep_id = int(ep_id_str)
        bv = convert_ep_to_BV(ep_id, credential_)
        if not bv:
            print(f"URL{url}解析失败: 无法获取BV号")
            return {}
        out["bvid"] = bv
    else:
        print(f"URL{url}不是B站视频URL")
        return {}
    return out

def parse_time(time_str):
    match = re.match(r'(\d+)h(\d+)m(\d+)s', time_str)
    if match:
        hours, minutes, seconds = match.groups()
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    return None

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

# def input_add_time_text():
#     text = input("请输入add_time_text（删减片段的说明文字），空输入默认为\"(此处为B站删减片段)\"：\n")
#     return text if text != '' else "(此处为B站删减片段)"


def ask_rmcf(rmcf_info: dict):
    """
    询问用户配置重映射时间轴
    """
    rmcf_info['time_filter'] = input_time_filter()
    rmcf_info['cut_time'] = input_cut_time()
    rmcf_info['add_time'] = input_add_time()
    # rmcf_info['add_time_text'] = input_add_time_text()



target_path = "./dm-srcURL.json"
info_list = []
is_exit = False

if os.path.exists(target_path):
    print(f"检测到文件dm-srcURL.json已存在，尝试读取文件内容")
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            info_list = json.load(f)
    except json.JSONDecodeError:
        if input(f"文件{target_path}内容不是有效的JSON格式，是否新建列表？空输入将清空该文件内容并新建列表，有输入退出"):
            is_exit = True
        else:
            print("将新建列表并覆盖文件内容")
            info_list = []
    else:
        print("当前已有的弹幕源：")
        num = 0
        for item in info_list:
            num += 1
            nm = item.get("name","")
            bv = item.get("BV","")
            p = item.get("p", 1)
            print(f"{num}. {nm}: BV = {bv}, p = {p}")
        print("将在已有列表基础上追加新的弹幕源")

if not is_exit:
    while True:
        srcURL = input("请输入视频所在的B站URL,空输入退出：")
        if not srcURL:
            break
        rmcf_info = {
            "dmsrc-file": "",
            "time_filter": [],
            "cut_time": 0,
            "add_time": [],
            "add_time_text": "(此处为B站删减片段)"
        }
        have_rmcf = input("是否需要重映射时间轴？有输入开始配置，无输入跳过")
        if have_rmcf:
            ask_rmcf(rmcf_info)
        video_info = bili_video_url_parse(srcURL)
        if video_info:
            dm_num = 1
            namelist = [item.get("name","") for item in info_list]
            while f"dm{dm_num}" in namelist:
                dm_num += 1
            bv_p_list = [(item.get("BV", ""), item.get("p", 1)) for item in info_list]
            if (video_info.get("bvid", ""), video_info.get("p", 1)) in bv_p_list:
                print("该弹幕源已存在，无需重复添加")
                continue
            rmcf_info["dmsrc-file"] = f"dm{dm_num}.json"
            new_item = {
                "src": "B站",
                "BV": video_info.get("bvid", ""),
                "p": video_info.get("p", 1),
                "name": f"dm{dm_num}",
                "rmcf": rmcf_info
            }
            info_list.append(new_item)
        else:
            print("解析失败")
            continue
    
    print("当前已有的弹幕源：")
    num_ = 0
    for item in info_list:
        num_ += 1
        nm = item.get("name","")
        bv = item.get("BV","")
        p = item.get("p", 1)
        print(f"{num_}. {nm}: BV = {bv}, p = {p}")
    choice = input("是否确认保存？无输入则保存并退出，有输入则直接退出")
    if not choice:
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(info_list, f, ensure_ascii=False, indent=4)
        print("已保存弹幕源列表")
