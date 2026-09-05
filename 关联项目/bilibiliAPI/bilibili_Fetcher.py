from bilibili_api import Credential
from bilibili_api import video
import asyncio
import os
import json

import bilibili_api

os.environ['NO_PROXY'] = 'bilibili.com,api.bilibili.com,*.bilibili.com,127.0.0.1,localhost'

class Bilibili_Fetcher:
    def __init__(self):
        self.basedir = os.path.dirname(os.path.abspath(__file__))
        self.cookie_path = os.path.join(self.basedir, 'cookie.json')
        SESSDATA = ""
        bili_jct = ""
        buvid3 = ""
        self.use_cookie = False
        if not os.path.exists(self.cookie_path):
            print(f"[Bilibili信息抓取模块] Cookie 文件不存在")
            self.cookie = {}
        else:
            with open(self.cookie_path, 'r', encoding='utf-8') as f:
                self.cookie = json.load(f)
            SESSDATA = self.cookie.get("SESSDATA", "")
            bili_jct = self.cookie.get("bili_jct", "")
            buvid3 = self.cookie.get("buvid3", "")
            if SESSDATA and bili_jct and buvid3:
                self.use_cookie = True
            else:
                print(f"[Bilibili信息抓取模块] Cookie 文件内容错误")
        if self.use_cookie:
            self.credential = Credential(sessdata=SESSDATA, bili_jct=bili_jct, buvid3=buvid3)
        else:
            self.credential = None

    def get_video_danmakus(self, bvid: str, page: int = 0) -> list | int:
        if self.use_cookie:
            v = video.Video(bvid=bvid, credential=self.credential)
            try:
                dms = v.get_danmakus(page)
            except asyncio.TimeoutError as e:
                print(f"[Bilibili信息抓取模块] 网络连接超时！")
                return 0x01
            else:
                dmlist = []
                for dm in dms:
                    typestr = ""
                    if dm.mode == 1:
                        typestr = "scroll"
                    elif dm.mode == 5:
                        typestr = "top"
                    else:
                        typestr = "bottom"
                    dmdic = {
                        "time": dm.dm_time,
                        "text": dm.text,
                        "send_time": dm.send_time,
                        "color": dm.color,
                        "id_str": dm.id_str,
                        "mode": dm.mode,
                        "font_size": dm.font_size,
                        "is_sub": dm.is_sub,
                        "uid": dm.uid,
                    }
                    dmlist.append(dmdic)
                return dmlist
        else:
            return []
        
