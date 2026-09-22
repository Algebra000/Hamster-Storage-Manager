# settings() 函数

该函数位于 `backend\classify_shower_back.py` 中，其往往在初次安装该模块时调用，用于初始化该模块的配置以使得模块能够正常运行。下面是该函数的实际功能。

---

具体来说，该函数首先尝试读取 `backend\config\classify_shower_config.json`(可能不存在,不存在新建该文件)，创建的初始空白 `classify_shower_config.json` 文件内容为：

```json

{
  "custom-class": {},
  "video-config": {
    "danmaku-config": {},
    "ffmpeg-path": "",
    "comment-config": {}
  }
}

```



## 验证并初始化FFmpeg路径

查看 `classify_shower_config.json` 中 `video-config.ffmpeg-path` 是否有值并验证该版本ffmpeg是否可用，为此还需要单独写一个判断ffmpeg是否有本模块需要的功能的函数。关于该模块用到的ffmpeg功能见 [添加播放其他格式容器视频的支持](视频播放页.md#添加播放其他格式容器视频的支持) 。

如果没能成功获取到合适版本的ffmpeg，检测用户是否有ffmpeg系统环境变量(不一定是win系统)，若有则验证是否可用，若可用那么将该地址写入 `video-config.ffmpeg-path`。若不可用则循环询问用户是否有准备ffmpeg可执行文件，用户可以选择填入地址和现场下载(空输入)，填入地址后若通过验证那么结束，若没有通过验证则再次询问。现场下载普通版 ffmpeg 后将下载的地址填入 `video-config.ffmpeg-path`

