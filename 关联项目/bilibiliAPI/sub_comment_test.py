import asyncio
import os
from bilibili_api import Credential, Danmaku
from bilibili_api import comment, sync
import json
from bilibili_api.utils.network import Api
import time

os.environ['NO_PROXY'] = 'bilibili.com,api.bilibili.com,*.bilibili.com,127.0.0.1,localhost'

use_cookie = {}
with open("cookie.json","r") as f:
    use_cookie = json.load(f)

credential_ = Credential(sessdata=use_cookie["SESSDATA"],
  bili_jct=use_cookie["bili_jct"], 
  buvid3=use_cookie["buvid3"])

test_cmt_dict = {
    "rpid": 288514730433,
    "oid": 115973126364952,
    "type": 1,
}


async def get_sub_comment_by_dict(
    cmt_dict:dict, 
    credential:Credential
    ) -> bool:
    """
    获取某条评论字典的所有子评论。获取到的子评论会放到cmt_dict的"replies"列表中。
    :param cmt_dict: 评论字典
    :param credential: Bilibili API凭证对象
    """
    rpid = cmt_dict.get("rpid", 0)
    oid = cmt_dict.get("oid", 0)
    type_ = cmt_dict.get("type", 0)
    if not (rpid and oid and type_):
        return False
    cmt_dict["replies"] = []
    cmt = comment.Comment(credential=credential_, rpid=rpid, oid=oid, type_=comment.CommentResourceType.VIDEO)
    index = 1
    while True:
        replies_dic = await cmt.get_sub_comments(page_index=index)
        replies = replies_dic.get("replies", [])
        if not replies:
             break
        await asyncio.sleep(0.1)
        index += 1
        cmt_dict["replies"].extend(replies)
    # with open('replies-test.json', 'w', encoding='utf-8') as f:
    #     json.dump(cmt_dict, f, ensure_ascii=False, indent=4)
    print(f"获取到{len(cmt_dict['replies'])}条子评论")

asyncio.run(get_sub_comment_by_dict(test_cmt_dict, credential_))
