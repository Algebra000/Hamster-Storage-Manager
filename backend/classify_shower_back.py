# classify_shower_back.py - 分类展示模块的后端实现，适用于 ROLAND 版本的仓鼠存储管理器。
import os
import json
import sqlite3
from typing import List, Dict, Protocol

# 导入文件类型列表
from config.file_type import video_type_list


from classify_shower_video import (
    ClassifyShowerVideo,
    classify_shower_check_ffmpeg, classify_shower_download_ffmpeg, settings,
)
from classify_shower_db_manager import DatabaseManager



class ClassifyShowerComponent(Protocol):
    """媒体组件的接入约定；具体组件无需继承此类型。"""

    async def handle_message(self, websocket, data) -> bool: ...
    async def when_connect(self, websocket) -> None: ...
    async def when_disconnect(self, websocket) -> None: ...
    async def shutdown(self) -> None: ...


class ClassifyShowerModule:
    def __init__(self, global_config):
        # 初始化模块配置
        self.global_config = global_config
        # 获取脚本所在目录的绝对路径
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        # 配置文件路径
        self.config_path = os.path.join(self.script_dir, 'config', 'classify_shower_config.json')
        self.config = {}
        self.module_dir = os.path.join(self.script_dir, 'classify_shower')
        # 数据库路径
        self.db_path = os.path.join(self.module_dir, 'classify_shower.db')
        #self.load_pinyin_dict()
        self.database_manager = DatabaseManager(self.module_dir, self.db_path)
        # 加载配置
        self.load_config()
        self.init_components()
        print("[分类展示模块] 模块初始化完成")

    def init_components(self):
        """集中创建组件；后续图片、音频组件在此加入 components 即可。"""
        self.video = ClassifyShowerVideo(
            global_config=self.global_config,
            get_config=lambda: self.config,
            script_dir=self.script_dir,
            save_config=self.save_config,
            database_manager=self.database_manager,
        )
        self.components: List[ClassifyShowerComponent] = [self.video]

        
    def load_config(self):
        """加载分类展示模块配置"""
        if os.path.exists(self.config_path) and os.path.isfile(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    print(f"[分类展示模块] 配置加载成功")
            except Exception as e:
                print(f"[分类展示模块] 配置加载失败: {e}")
        else:
            print(f"[分类展示模块] 配置文件不存在，将使用默认配置")
    
    def save_config(self):
        """保存分类展示模块配置"""
        # 确保config目录存在
        config_dir = os.path.join(self.script_dir, 'config')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"[分类展示模块] 配置保存成功")
        except Exception as e:
            print(f"[分类展示模块] 配置保存失败: {e}")

    def build_database(self):
            """建立数据库，扫描所有分类的文件"""
            print("[分类展示模块] 开始建立数据库...")
            
            # 获取根目录列表
            base_dirs = self.global_config.get('base_dir', [])
            
            # 扫描番剧分类
            self.video.scan_anime_category(base_dirs)
            
            print("[分类展示模块] 数据库建立完成")
    
    # def get_all_anime(self) -> List[Dict]:
    #     """获取所有番剧数据"""
    #     self.db_cursor.execute('''
    #         SELECT a.root_path, a.name, a.year, a.cover_path, a.episode_count, GROUP_CONCAT(t.name) as tags
    #         FROM anime a
    #         LEFT JOIN anime_tag at ON a.id = at.anime_id
    #         LEFT JOIN tag t ON at.tag_id = t.id
    #         GROUP BY a.id
    #         ORDER BY a.year DESC, a.name
    #     ''')
    #     rows = self.db_cursor.fetchall()
        
    #     anime_list = []
    #     for row in rows:
    #         anime_list.append({
    #             'root_path': row[0],
    #             'name': row[1],
    #             'year': row[2],
    #             'cover_path': row[3],
    #             'episode_count': row[4],
    #             'tags': row[5].split(',') if row[5] else []
    #         })
        
    #     return anime_list

    async def when_connect(self, websocket):
        """当连接建立时调用"""
        for component in self.components:
            await component.when_connect(websocket)
        print("[分类展示模块] 连接建立成功")
        #self.add_pinyin_column()
        #self.update_anime_pinyin()

    async def when_disconnect(self, websocket):
        """当连接断开时调用"""
        for component in self.components:
            await component.when_disconnect(websocket)
        print("[分类展示模块] 连接断开")

    async def shutdown(self):
        """服务退出时回收全部 FFmpeg 流和数据库连接。"""
        for component in self.components:
            await component.shutdown() 
        self.database_manager.close()

    async def message_proc(self, websocket, data):
        """分发视频评论消息及分类浏览消息。"""
        for component in self.components:
            if await component.handle_message(websocket, data):
                return
        command = data.get('command')

        if command == 'CLASSIFY_SHOWER_ACTIVATED':
            print("[分类展示模块] 收到激活消息")
            #await self.send_classify_data(websocket)

        elif command == 'GET_ALL_TAGS':
            print("[分类展示模块] 收到获取所有标签请求")
            tags = self.database_manager.get_all_tags()
            message = json.dumps({
                'command': 'ALL_TAGS',
                'data': tags
            }, ensure_ascii=False)
            await websocket.send(message)
            print(f"[分类展示模块] 发送所有标签，共 {len(tags)} 个")

        elif command == 'REFRESH_ANIME_DATABASE':
            widget_id = data.get('widgetId', '')
            print("[分类展示模块] 收到刷新数据库请求")
            self.build_database()
            message = json.dumps({
                'command': 'DATABASE_REBUILD_COMPLETE',
                'widgetId': widget_id
            }, ensure_ascii=False)
            await websocket.send(message)
            print("[分类展示模块] 数据库重建完成")

        else:
            print(f"[分类展示模块] 收到未知命令: {command}")

# 模块工厂函数，用于创建模块实例
def create_module(global_config, back_version):
    return ClassifyShowerModule(global_config)
