import asyncio
import os
from bilibili_api import Credential, Danmaku
from bilibili_api import comment, sync
import json
from bilibili_api.utils.network import Api
import time
import aiohttp.http_exceptions as aiohttp_http_exceptions

URL_JSON_PATH = "resources-URL.json"

with open(URL_JSON_PATH, 'r', encoding='utf-8') as f:
    to_download_resources_URL = json.load(f)


def get_image_name_by_URL(url: str) -> str:
    if not url:
        return ""
    return os.path.basename(url)

def URL_skip(url_list: list, skip_file_name_list: list) -> list:
    return [url for url in url_list if get_image_name_by_URL(url) not in skip_file_name_list]

base_path = "./comment-resource/"
use_cookie = {
    "SESSDATA":"d302a7b3,1799430067,6406c*72CjAMhrMtIxlgrph7nmjW4l-4kmCJhyyE0DJsefXNjrr8qUuCpP3Y_JBqoLDvxNq4eWsSVm9jWW1UN1BjTzd1Yml2Y25DY0MxQ0lndEtYY2FSVjV3blJ5azV3NVBNODhEeG5IR19zUXMxa2hfTktfdW9ocGpmNXJERnJsdC1IX3hLUmtWdzlvNXVnIIEC",
    "bili_jct":"e879e117e76c28190b756f898ccc60f0",
    "buvid3":"B25FEA33-6B46-3C5E-A18A-C3E53763A9F932854infoc"
}

# use_cookie = {
#     "SESSDATA":"adedc65e%2C1762922652%2C49cf3%2A51CjDY4gBlocko40Qwo16KhMaFvccww4rFFKeNCURUEN9hEBlD2t_0Zj92oPECNZBWwF8SVnBhQ1NxQUFkUkk1clJ3WUp0QXR3MEJQSm8xdmJ3dlctUzJOQldXMmp3Qzl4UHJZN1JUcXdfUVRzZ2Jsb2wya2dzaU1xVEJlUGlxd2NLTV9qWVJ0V3ZnIIEC",
#     "bili_jct":"8fe597bfefad11937b62ade21974effe",
#     "buvid3":"B25FEA33-6B46-3C5E-A18A-C3E53763A9F932854infoc"
# }

credential_ = Credential(sessdata=use_cookie["SESSDATA"],
  bili_jct=use_cookie["bili_jct"], 
  buvid3=use_cookie["buvid3"])

async def main():
    for key in to_download_resources_URL.keys():
        key_path = os.path.join(base_path, key)
        skip_list = []
        if os.path.exists(key_path):
            skip_list = os.listdir(key_path)
            to_download_resources_URL[key] = URL_skip(to_download_resources_URL[key], skip_list)
        os.makedirs(key_path, exist_ok=True)
        for url in to_download_resources_URL[key]:
            target_file = os.path.join(key_path, get_image_name_by_URL(url))
            if os.path.exists(target_file):
                print(f"{target_file} 已存在")
                continue 
            try:
                imgbytes = await Api(url = url, method="GET",  credential=credential_).request(byte= True)
            except aiohttp_http_exceptions.ContentLengthError as e:
                print(f"\033[93m下载 {target_file} 触发风控: {e}\033[0m")
                print(f"等待 60 秒后重试")
                await asyncio.sleep(60)
                imgbytes = await Api(url = url, method="GET",  credential=credential_).request(byte= True)
            except asyncio.exceptions.TimeoutError as e:
                print(f"\033[93m下载 {target_file} 请求过于频繁已被限流: {e}\033[0m")
                print(f"等待 60 秒后重试")
                await asyncio.sleep(60)
                imgbytes = await Api(url = url, method="GET",  credential=credential_).request(byte= True)
                
            with open(target_file, "wb") as f:
                f.write(imgbytes)
            print(f"已下载 {target_file}")
            await asyncio.sleep(0.3)

asyncio.run(main())
