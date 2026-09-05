import asyncio
import os
from bilibili_api import Credential, Danmaku
from bilibili_api import comment, sync
import json
from bilibili_api.utils.network import Api
import time
import aiohttp.http_exceptions as aiohttp_http_exceptions
import aiohttp.client_exceptions

DANMAKU_BVID = "BV1THN36xET6"
COMMENT_AID = 116943705082663 #116929259897784 #116931558378107 #115973126364952

ENABLE_DANMAKU_TEST = False
ENABLE_COMMENT_TEST = True


os.environ['NO_PROXY'] = 'bilibili.com,api.bilibili.com,*.bilibili.com,127.0.0.1,localhost'

from bilibili_api import video

use_cookie = {}
with open("cookie.json","r") as f:
    use_cookie = json.load(f)

credential_ = Credential(sessdata=use_cookie["SESSDATA"],
  bili_jct=use_cookie["bili_jct"], 
  buvid3=use_cookie["buvid3"])


def get_image_name_by_URL(url: str) -> str:
    if not url:
        return ""
    return os.path.basename(url)

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
    cmt = comment.Comment(credential=credential, rpid=rpid, oid=oid, type_=comment.CommentResourceType.VIDEO)
    index = 1
    while True:
        try:
            replies_dic = await cmt.get_sub_comments(page_index=index)
        except Exception as e:
            print(f"获取子评论失败: {e}")
            return False
        replies = replies_dic.get("replies", [])
        if not replies:
             break
        index += 1
        await asyncio.sleep(0.1)
        cmt_dict["replies"].extend(replies)
    # with open('replies-test.json', 'w', encoding='utf-8') as f:
    #     json.dump(cmt_dict, f, ensure_ascii=False, indent=4)
    print(f"获取到{len(cmt_dict['replies'])}条子评论")
    return True

def remap_avatar_item_layers_to_local(
    avatar_item_layers_list:list, 
    to_download_resources_URL:dict
    ) :
    next_list = avatar_item_layers_list
    list_list = []
    while True:
        if list_list:
            next_list = list_list[0]
            list_list.pop(0)
        if not next_list:
            break
        for layer in next_list:
            new_layers = layer.get("layers", None)
            if new_layers:
                list_list.append(new_layers)
            resource = layer.get("resource", None)
            if resource:
                res_type = resource.get("res_type", None)
                if res_type == 3:
                    res_image = resource.get("res_image", None)
                    if res_image:
                        image_src = res_image.get("image_src", None)
                        if image_src:
                           img_remote = image_src.get("remote", None)
                           if img_remote:
                               url = img_remote.get("url", '')
                               if url:
                                   type_name = save_url_to_dict(url, to_download_resources_URL)
                                   img_name = get_image_name_by_URL(url)
                                   img_remote["url"] = f"./comment-resource/{type_name}/{img_name}"
                elif res_type == 4:
                    res_animation = resource.get("res_animation", None)
                    if res_animation:
                        webp_src = res_animation.get("webp_src", None)
                        if webp_src:
                            remote = webp_src.get("remote", None)
                            if remote:
                                url = remote.get("url", '')
                                if url:
                                    type_name = save_url_to_dict(url, to_download_resources_URL)
                                    img_name = get_image_name_by_URL(url)
                                    remote["url"] = f"./comment-resource/{type_name}/{img_name}"
        next_list = []

def save_url_to_dict(
    url:str,
    to_download_resources_URL:dict
    ) -> str:
    """
    将URL添加到to_download_resources_URL字典的对应列表中。
    根据URL的类型自动分类，将其放到对应的列表中。
    :param url: 要添加的URL
    :param to_download_resources_URL: 资源URL字典
    :return: 分类后的URL类型名称(文件夹名称)
    """
    numind = url.find("hdslb.com/bfs/") + 14
    if numind >14:
        type_name = url[numind:]
        if type_name.startswith("face"):
            to_download_resources_URL["avatar"].add(url)
            return "avatar"
        elif type_name.startswith("garb"):
            to_download_resources_URL["pendant"].add(url)
            return "pendant"
        elif type_name.startswith("baselabs"):
            to_download_resources_URL["baselabs"].add(url)
            return "baselabs"
        elif type_name.startswith("activity-plat"):
            to_download_resources_URL["pendant"].add(url)
            return "pendant"
        else:
            to_download_resources_URL["others"].add(url)
            return "others"
    else:
        to_download_resources_URL["others"].add(url)
        return "others"

def remap_cmt_to_local(
    cmt_dict:dict, 
    to_download_resources_URL:dict
    ) :
    """
    映射弹幕字典到本地资源。
    该函数会解析弹幕字典，将其中的资源URL放到to_download_resources_URL字典的
    对应列表中，同时将弹幕字典中的资源URL替换为其将要被下载到的本地资源路径。
    （该函数没有下载功能，需要后续代码根据to_download_resources_URL字典下载资源）
    :param cmt_dict: 弹幕字典
    :param to_download_resources_URL: 资源URL字典
    """
    mumber_info = cmt_dict.get("member", None)
    if mumber_info:
        avatar_url = mumber_info.get("avatar", '')
        if avatar_url:
            to_download_resources_URL["avatar"].add(avatar_url)
            avatar_img_name = get_image_name_by_URL(avatar_url)
            mumber_info["avatar"] = f"./comment-resource/avatar/{avatar_img_name}"
        vip_info = mumber_info.get("vip", None)
        if vip_info:
            vip_lable_info = vip_info.get("label", None)
            if vip_lable_info:
                vip_img_url = vip_lable_info.get("img_label_uri_hans_static", '')
                if vip_img_url:
                    vip_img_name = get_image_name_by_URL(vip_img_url)
                    to_download_resources_URL["vip"].add(vip_img_url)
                    vip_lable_info["img_label_uri_hans_static"] = f"./comment-resource/vip/{vip_img_name}"
                vip_img_url1 = vip_lable_info.get("img_label_uri_hant_static", '')
                if vip_img_url1:
                    to_download_resources_URL["vip"].add(vip_img_url1)
                    vip_img_name1 = get_image_name_by_URL(vip_img_url1)
                    vip_lable_info["img_label_uri_hant_static"] = f"./comment-resource/vip/{vip_img_name1}"

                vip_annual_img_url = vip_lable_info.get("path", '')
                if vip_annual_img_url:
                    to_download_resources_URL["vip"].add(vip_annual_img_url)
                    vip_annual_img_name = get_image_name_by_URL(vip_annual_img_url)
                    vip_lable_info["path"] = f"./comment-resource/vip/{vip_annual_img_name}"

                img_label_uri_hans = vip_lable_info.get("img_label_uri_hans", '')#超级大会员动态星标
                if img_label_uri_hans:
                    to_download_resources_URL["vip"].add(img_label_uri_hans)
                    img_label_uri_hans_name = get_image_name_by_URL(img_label_uri_hans)
                    vip_lable_info["img_label_uri_hans"] = f"./comment-resource/vip/{img_label_uri_hans_name}"
                
                img_label_uri_hant = vip_lable_info.get("img_label_uri_hant", '')#超级大会员动态星标
                if img_label_uri_hant:
                    to_download_resources_URL["vip"].add(img_label_uri_hant)
                    img_label_uri_hant_name = get_image_name_by_URL(img_label_uri_hant)
                    vip_lable_info["img_label_uri_hant"] = f"./comment-resource/vip/{img_label_uri_hant_name}"

        user_sailing_info = mumber_info.get("user_sailing", None)      
        if user_sailing_info:
            cardbg_info = user_sailing_info.get("cardbg", None)
            if cardbg_info:
                cardbg_img_url = cardbg_info.get("image", '')
                if cardbg_img_url:
                    to_download_resources_URL["card"].add(cardbg_img_url)
                    cardbg_img_name = get_image_name_by_URL(cardbg_img_url)
                    cardbg_info["image"] = f"./comment-resource/card/{cardbg_img_name}"
        
        pendant_info = mumber_info.get("pendant", None)
        if pendant_info:
            pendant_img_url = pendant_info.get("image", '')
            if pendant_img_url:
                to_download_resources_URL["pendant"].add(pendant_img_url)
                pendant_img_name = get_image_name_by_URL(pendant_img_url)
                pendant_info["image"] = f"./comment-resource/pendant/{pendant_img_name}"
        
        nft_info = mumber_info.get("nft_interaction", None) #彩钻标识(拥有数字藏品)
        if nft_info:
            region_info = nft_info.get("region", None)
            if region_info:
                region_img_url = region_info.get("icon", '')
                if region_img_url:
                    to_download_resources_URL["vip"].add(region_img_url)
                    region_img_name = get_image_name_by_URL(region_img_url)
                    region_info["icon"] = f"./comment-resource/vip/{region_img_name}"
        
        avatar_item = mumber_info.get("avatar_item", None)
        if avatar_item:
            layers = avatar_item.get("layers", [])
            if layers:
                remap_avatar_item_layers_to_local(layers,to_download_resources_URL)

            fallback_layers = avatar_item.get("fallback_layers", None)
            if fallback_layers:
                layers_2 = fallback_layers.get("layers", [])
                if layers_2:
                    remap_avatar_item_layers_to_local(layers_2,to_download_resources_URL)
    
    content_info = cmt_dict.get("content", None)
    if content_info:
        emote = content_info.get("emote", None)
        if emote:
            for emote_ in emote.keys():
                emote_url = emote[emote_].get("url", '')
                if emote_url:
                    to_download_resources_URL["emoji"].add(emote_url)
                    emote[emote_]["url"] = f"./comment-resource/emoji/{get_image_name_by_URL(emote_url)}"

        pic_info = content_info.get("pictures", [])
        for pic_ in pic_info:
            pic_url = pic_.get("img_src", '')
            if pic_url:
                to_download_resources_URL["picture"].add(pic_url)
                pic_["img_src"] = f"./comment-resource/picture/{get_image_name_by_URL(pic_url)}"
            
            pic_vip_icon_url = pic_.get("top_right_icon", '')
            if pic_vip_icon_url:
                to_download_resources_URL["vip"].add(pic_vip_icon_url)
                pic_["top_right_icon"] = f"./comment-resource/vip/{get_image_name_by_URL(pic_vip_icon_url)}"

        jump_url_info = content_info.get("jump_url", None)
        if jump_url_info:
            for jump_, jump_info in jump_url_info.items():
                jump_icon_url = jump_info.get("prefix_icon", '')
                if jump_icon_url:
                    to_download_resources_URL["icons"].add(jump_icon_url)
                    jump_url_info[jump_]["prefix_icon"] = f"./comment-resource/icons/{get_image_name_by_URL(jump_icon_url)}"
            

    replies = cmt_dict.get("replies", None)
    if replies:
        for reply in replies:
            rep_member_info = reply.get("member", None)
            if rep_member_info:
                rep_avatar_url = rep_member_info.get("avatar", '')
                if rep_avatar_url:
                    to_download_resources_URL["avatar"].add(rep_avatar_url)
                    rep_avatar_img_name = get_image_name_by_URL(rep_avatar_url)
                    rep_member_info["avatar"] = f"./comment-resource/avatar/{rep_avatar_img_name}"
                
                rep_vip_info = rep_member_info.get("vip", None)
                if rep_vip_info:
                    rep_vip_lable_info = rep_vip_info.get("label", None)
                    if rep_vip_lable_info:
                        rep_vip_img_url = rep_vip_lable_info.get("img_label_uri_hans_static", '')
                        if rep_vip_img_url:
                            rep_vip_img_name = get_image_name_by_URL(rep_vip_img_url)
                            to_download_resources_URL["vip"].add(rep_vip_img_url)
                            rep_vip_lable_info["img_label_uri_hans_static"] = f"./comment-resource/vip/{rep_vip_img_name}"
                        rep_vip_img_url1 = rep_vip_lable_info.get("img_label_uri_hant_static", '')
                        if rep_vip_img_url1:
                            to_download_resources_URL["vip"].add(rep_vip_img_url1)
                            rep_vip_img_name1 = get_image_name_by_URL(rep_vip_img_url1)
                            rep_vip_lable_info["img_label_uri_hant_static"] = f"./comment-resource/vip/{rep_vip_img_name1}"

                        rep_vip_annual_img_url = rep_vip_lable_info.get("path", None)
                        if rep_vip_annual_img_url:
                            to_download_resources_URL["vip"].add(rep_vip_annual_img_url)
                            rep_vip_annual_img_name = get_image_name_by_URL(rep_vip_annual_img_url)
                            rep_vip_lable_info["path"] = f"./comment-resource/vip/{rep_vip_annual_img_name}"
                        
                        rep_vip_img_url2 = rep_vip_lable_info.get("img_label_uri_hant", None)
                        if rep_vip_img_url2:
                            to_download_resources_URL["vip"].add(rep_vip_img_url2)
                            rep_vip_img_name2 = get_image_name_by_URL(rep_vip_img_url2)
                            rep_vip_lable_info["img_label_uri_hant"] = f"./comment-resource/vip/{rep_vip_img_name2}"

                        rep_img_label_uri_hans = rep_vip_lable_info.get("img_label_uri_hans", '')
                        if rep_img_label_uri_hans:
                            to_download_resources_URL["vip"].add(rep_img_label_uri_hans)
                            rep_img_label_uri_hans_name = get_image_name_by_URL(rep_img_label_uri_hans)
                            rep_vip_lable_info["img_label_uri_hans"] = f"./comment-resource/vip/{rep_img_label_uri_hans_name}"
                
                rep_pendant_info = rep_member_info.get("pendant", None)
                if rep_pendant_info:
                    rep_pendant_img_url = rep_pendant_info.get("image", '')
                    if rep_pendant_img_url:
                        to_download_resources_URL["pendant"].add(rep_pendant_img_url)
                        rep_pendant_img_name = get_image_name_by_URL(rep_pendant_img_url)
                        rep_pendant_info["image"] = f"./comment-resource/pendant/{rep_pendant_img_name}"

                rep_nft_info = rep_member_info.get("nft_interaction", None) #彩钻标识(拥有数字藏品)
                if rep_nft_info:
                    rep_region_info = rep_nft_info.get("region", None)
                    if rep_region_info:
                        rep_region_img_url = rep_region_info.get("icon", '')
                        if rep_region_img_url:
                            to_download_resources_URL["vip"].add(rep_region_img_url)
                            rep_region_img_name = get_image_name_by_URL(rep_region_img_url)
                            rep_region_info["icon"] = f"./comment-resource/vip/{rep_region_img_name}"
                
                rep_avatar_item = rep_member_info.get("avatar_item", None)
                if rep_avatar_item:
                    layers = rep_avatar_item.get("layers", [])
                    if layers:
                        remap_avatar_item_layers_to_local(layers,to_download_resources_URL)
                    
                    rep_fallback_layers = rep_avatar_item.get("fallback_layers", {})
                    if rep_fallback_layers:
                        layers_1 = rep_fallback_layers.get("layers", [])
                        if layers_1:
                            remap_avatar_item_layers_to_local(layers_1,to_download_resources_URL)

            rep_content_info = reply.get("content", None)
            if rep_content_info:
                emote = rep_content_info.get("emote", None)
                if emote:
                    for emote_ in emote.keys():
                        emote_url = emote[emote_].get("url", '')
                        if emote_url:
                            to_download_resources_URL["emoji"].add(emote_url)
                            emote[emote_]["url"] = f"./comment-resource/emoji/{get_image_name_by_URL(emote_url)}"

                rep_pic_info = rep_content_info.get("pictures", [])
                for pic_ in rep_pic_info:
                    pic_url = pic_.get("img_src", '')
                    if pic_url:
                        to_download_resources_URL["picture"].add(pic_url)
                        pic_["img_src"] = f"./comment-resource/picture/{get_image_name_by_URL(pic_url)}"

                    vip_icon_url = pic_.get("top_right_icon", '')
                    if vip_icon_url:
                        to_download_resources_URL["vip"].add(vip_icon_url)
                        vip_icon_img_name = get_image_name_by_URL(vip_icon_url)
                        pic_["top_right_icon"] = f"./comment-resource/vip/{vip_icon_img_name}"

                rep_jump_url_info = rep_content_info.get("jump_url", None)
                if rep_jump_url_info:
                    for jump_1, jump_info1 in rep_jump_url_info.items():
                        rep_jump_icon_url = jump_info1.get("prefix_icon", '')
                        if rep_jump_icon_url:
                            to_download_resources_URL["icons"].add(rep_jump_icon_url)
                            rep_jump_url_info[jump_1]["prefix_icon"] = f"./comment-resource/icons/{get_image_name_by_URL(rep_jump_icon_url)}"
                

async def download_resourses_URL_dict(to_download_resources_URL: dict , base_path: str , credential_:Credential, time_strip: float = 0.2) -> None:
    for key in to_download_resources_URL.keys():
        key_path = os.path.join(base_path, key)
        os.makedirs(key_path, exist_ok=True)
        for url in to_download_resources_URL[key]:
            #imgbytes = await Api(url = url, method="GET",  credential=credential_).request(byte= True)
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
            except (TimeoutError, aiohttp.client_exceptions.ClientConnectorError) as e:
                print(f"下载 {target_file} 与服务器连接中断: {e}")
                print(f"等待 30 秒后重试")
                await asyncio.sleep(30)
                imgbytes = await Api(url = url, method="GET",  credential=credential_).request(byte= True)

            with open(target_file, "wb") as f:
                f.write(imgbytes)
            print(f"已下载 {target_file}")
            time.sleep(time_strip)







async def main() -> None:                                                 # 轮训间隔建议 >=1s
    v = video.Video(bvid=DANMAKU_BVID, credential=credential_)

    if ENABLE_DANMAKU_TEST:

        try:
            dms = await v.get_danmakus(0)
        except asyncio.TimeoutError as e:
            print(f"[Bilibili信息抓取模块] 获取弹幕失败: {e}")
            return
        with open('dm1.json', 'w', encoding='utf-8') as f:
            dmlist = []
            for dm in dms:
                #print(f"{dm.text},{dm.send_time},{dm.dm_time},color={dm.color},id={dm.id_},id_str={dm.id_str},mode={dm.mode},font_size={dm.font_size},is_sub={dm.is_sub},uid={dm.uid}")
                if not dm.text:
                    continue
                typestr = ""
                if dm.mode == 1:
                    typestr = "scroll"
                elif dm.mode == 5:
                    typestr = "top"
                elif dm.mode == 7:
                    typestr = "special"
                else:
                    typestr = "bottom"

                is_colorful = False
                if dm.colorful:
                    is_colorful = True
                # dmdic = {
                #     "text": dm.text,
                #     "send_time": dm.send_time,
                #     "dm_time": dm.dm_time,
                #     "color": dm.color,
                #     "id_str": dm.id_str,
                #     "mode": dm.mode,
                #     "font_size": dm.font_size,
                #     "is_sub": dm.is_sub,
                #     "uid": dm.uid,
                #     "like_count": dm.like_count,
                #     "is_not_special": dm.is_not_special,
                #     "oid": dm.oid,
                #     "action": dm.action,
                # }
                dmdic = {
                    "time": dm.dm_time,
                    "text": dm.text,
                    "type": typestr,
                    "color": f"#{dm.color}",
                    "dmid": dm.id_str,
                    "is-colorful": is_colorful, # 是否为大会员专属彩色弹幕
                    "like-count": dm.like_count,
                    "oid": dm.oid,
                    "font-size": dm.font_size,
                    "send-time": dm.send_time,
                    "weight": dm.weight,
                    "src": "B站"
                }
                dmlist.append(dmdic)
            f.write(json.dumps(dmlist, ensure_ascii=False, indent=4))
    
    #下面开始获取评论
    if not ENABLE_COMMENT_TEST:
        return
    
    # 存储评论
    comments = []
    # 刷新次数（约等于页码）
    page = 1
    # 每次提供的 offset (pagination_str)
    pag = ""

    while True:
        # 获取评论 使用aid 115973126364952
        c = await comment.get_comments_lazy(COMMENT_AID, comment.CommentResourceType.VIDEO, offset=pag, credential=credential_)
        # with open('comment.json', 'w', encoding='utf-8') as f:
        #     f.write(json.dumps(c, ensure_ascii=False, indent=4))
        pagination_dict = c["cursor"]["pagination_reply"]
        #print(pagination_dict)
        is_break = False
        if pagination_dict.get("next_offset", 404) == 404:# 没有更多评论了
            is_break = True
        else:
            pag = pagination_dict["next_offset"]
        replies = c["replies"]
        if replies is None:
            # 未登录时只能获取到前20条评论
            # 此时增加页码会导致c为空字典
            break

        # 存储评论
        comments.extend(replies)
        # 增加页码
        page += 1
        if is_break:
            break

        #time.sleep(5)
        # 只刷新 5 次（约等于 5 页）
        # if page > 20:
        #     break

    # 打印评论
    # for cmt in comments:
    #     print(f"{cmt["member"]['uname']}: {cmt['content']['message']}")

    # 打印评论总数
    print(f"\n\n共有 {len(comments)} 条评论（不含子评论）,共 {page - 1} 页")




    #解析下载好的评论字典，使用remap_cmt_to_local函数获取所有需要下载的资源URL
    to_download_resources_URL = {
        "avatar": set(), 
        "vip": set(), 
        "emoji": set(),
        "card": set(),
        "pendant": set(),
        "picture": set(),
        "icons": set(),
        "baselabs": set(),
        "others": set()
        }

    # 处理子评论并映射资源URL
    for cmt_dict in comments:
        reply_count = cmt_dict.get("rcount", 0)
        reply_data = cmt_dict.get("replies", [])
        if not reply_data:
            remap_cmt_to_local(cmt_dict, to_download_resources_URL)
            continue
        if reply_count > len(reply_data):
            result = await get_sub_comment_by_dict(cmt_dict, credential_)
            if not result:
                print(f"获取子评论失败")
                remap_cmt_to_local(cmt_dict, to_download_resources_URL)
                continue
        remap_cmt_to_local(cmt_dict, to_download_resources_URL)

    with open('comment.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(comments, ensure_ascii=False, indent=4))
    
    with open('resources-URL.json', 'w', encoding='utf-8') as f:
        for key in to_download_resources_URL.keys():
            to_download_resources_URL[key] = list(to_download_resources_URL[key])
        f.write(json.dumps(to_download_resources_URL, ensure_ascii=False, indent=4))

    base_path = "./comment-resource/"
    await download_resourses_URL_dict(to_download_resources_URL, base_path, credential_, 0.3)

    # imgbytes = await Api(url = "https://i0.hdslb.com/bfs/emote/2caafee2e5db4db72104650d87810cc2c123fc86.png", method="GET",  credential=credential_).request(byte= True)
    # with open("test.png", "wb") as f:
    #     f.write(imgbytes)







if __name__ == "__main__":
    asyncio.run(main())