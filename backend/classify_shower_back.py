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
        # 拼音字典
        self.pinyin_dict = {}
        # 加载拼音字典
        self.load_pinyin_dict()
        # 加载配置
        self.load_config()
        self.init_components()
        # 初始化数据库
        self.init_database()
        print("[分类展示模块] 模块初始化完成")

    def init_components(self):
        """集中创建组件；后续图片、音频组件在此加入 components 即可。"""
        self.video = ClassifyShowerVideo(
            global_config=self.global_config,
            get_config=lambda: self.config,
            script_dir=self.script_dir,
            save_config=self.save_config,
        )
        self.components: List[ClassifyShowerComponent] = [self.video]

    def load_pinyin_dict(self):
        """
        从 pinyin.txt 文件加载拼音字典（不保留声调，只取第一个拼音）
        """
        pinyin_file_path = os.path.join(self.module_dir, 'pinyin.txt')
        tone_map = {
            'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
            'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
            'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
            'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
            'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
            'ǖ': 'v', 'ǘ': 'v', 'ǚ': 'v', 'ǜ': 'v',
            'ü': 'v'
        }
        
        try:
            with open(pinyin_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if ':' not in line:
                    continue
                code_part, pinyin_part = line.split(':', 1)
                unicode_hex = code_part.strip()[2:]
                try:
                    hanzi = chr(int(unicode_hex, 16))
                except (ValueError, OverflowError):
                    continue
                # 只取第一个拼音
                first_pinyin = pinyin_part.strip().split(',')[0].strip()
                # 去掉声调
                pinyin = ''.join(tone_map.get(ch, ch) for ch in first_pinyin)
                self.pinyin_dict[hanzi] = pinyin
            
            print(f"[分类展示模块] 拼音字典加载成功，共 {len(self.pinyin_dict)} 个汉字")
        except Exception as e:
            print(f"[分类展示模块] 拼音字典加载失败: {e}")
        
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

    def init_database(self):
        """初始化数据库"""
        # 确保模块目录存在
        if not os.path.exists(self.module_dir):
            os.makedirs(self.module_dir)
        
        # 连接数据库
        self.db_conn = sqlite3.connect(self.db_path)
        self.db_cursor = self.db_conn.cursor()
        
        # 创建番剧表
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS anime (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                root_path TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                name_pinyin TEXT DEFAULT '',
                year INTEGER,
                month INTEGER,
                cover_path TEXT,
                episode_count INTEGER DEFAULT 0,
                entry_time INTEGER DEFAULT 0,
                last_watch_order INTEGER DEFAULT 0,
                last_watch_time INTEGER DEFAULT 0,
                last_video_time REAL DEFAULT 0.0,
                has_danmaku INTEGER DEFAULT 0
            )
        ''')

        # 创建标签表
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS tag (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                pinyin TEXT DEFAULT ''
            )
        ''')
        
        # 创建番剧-标签关联表
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS anime_tag (
                anime_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (anime_id, tag_id),
                FOREIGN KEY (anime_id) REFERENCES anime(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建索引加速查询
        self.db_cursor.execute('CREATE INDEX IF NOT EXISTS idx_anime_tag_anime ON anime_tag(anime_id)')
        self.db_cursor.execute('CREATE INDEX IF NOT EXISTS idx_anime_tag_tag ON anime_tag(tag_id)')
        
        self.db_conn.commit()
        print(f"[分类展示模块] 数据库初始化完成: {self.db_path}")

        #self.build_database()
    
    def build_database(self):
        """建立数据库，扫描所有分类的文件"""
        print("[分类展示模块] 开始建立数据库...")
        
        # 获取根目录列表
        base_dirs = self.global_config.get('base_dir', [])
        
        # 扫描番剧分类
        self.scan_anime_category(base_dirs)
        
        print("[分类展示模块] 数据库建立完成")
    
    def scan_anime_category(self, base_dirs: List[str]):
        """扫描番剧分类"""
        print("[分类展示模块] 扫描番剧分类...")

        existing_paths = set()

        for base_dir in base_dirs:
            if not os.path.exists(base_dir):
                print(f"[分类展示模块] 目录不存在: {base_dir}")
                continue

            for root, dirs, files in os.walk(base_dir):
                if '__MD__.json' in files:
                    md_path = os.path.join(root, '__MD__.json')
                    try:
                        with open(md_path, 'r', encoding='utf-8') as f:
                            md_data = json.load(f)

                        type_val = md_data.get('type')
                        is_anime = (type_val == '番剧') or (isinstance(type_val, list) and '番剧' in type_val)
                        if is_anime:
                            self.process_anime_folder(root, md_data)
                            existing_paths.add(root)
                    except Exception as e:
                        print(f"[分类展示模块] 处理 __MD__.json 失败: {md_path}, 错误: {e}")

        self.cleanup_missing_anime(existing_paths)

    def cleanup_missing_anime(self, existing_paths: set):
        """清理已不存在的番剧条目"""
        try:
            self.db_cursor.execute('SELECT id, root_path FROM anime')
            all_anime = self.db_cursor.fetchall()

            removed_count = 0
            for anime_id, root_path in all_anime:
                if root_path not in existing_paths:
                    self.db_cursor.execute('DELETE FROM anime_tag WHERE anime_id = ?', (anime_id,))
                    self.db_cursor.execute('DELETE FROM anime WHERE id = ?', (anime_id,))
                    removed_count += 1
                    print(f"[分类展示模块] 移除不存在的番剧: {root_path}")

            if removed_count > 0:
                self.db_conn.commit()
            print(f"[分类展示模块] 清理完成，移除了 {removed_count} 个不存在的番剧条目")
        except Exception as e:
            print(f"[分类展示模块] 清理不存在的番剧失败: {e}")
    
    def process_anime_folder(self, folder_path: str, md_data: Dict):
        """处理番剧文件夹"""
        root_path = folder_path
        name = md_data.get('name', '')
        year = md_data.get('year')
        month = md_data.get('month')
        tags_list = md_data.get('item', [])
        cover_path = md_data.get('cover', '')
        entry_time = md_data.get('entry-time', 0)

        if cover_path and not os.path.isabs(cover_path):
            cover_path = os.path.normpath(os.path.join(folder_path, cover_path))

        episode_count = self.count_video_episodes(folder_path)
        name_pinyin = self.get_pinyin(name)

        # 读取观看历史
        last_watch_order = 0
        last_watch_time = 0
        last_video_time = 0.0
        history_path = os.path.join(root_path, '__HISTORY__.json')
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                if 'order' in history_data:
                    last_watch_order = history_data['order']
                if 'view-time' in history_data:
                    last_watch_time = history_data['view-time']
                if 'video-time' in history_data:
                    last_video_time = history_data['video-time']
            except Exception as e:
                print(f"[分类展示模块] 读取 __HISTORY__.json 失败: {e}")

        # 检查是否有弹幕（只要有一集有rmcf.json就算有弹幕）
        has_danmaku = 0
        video_extensions = set(ext.lower() for ext in video_type_list)
        try:
            for f in os.listdir(root_path):
                if any(f.lower().endswith(ext) for ext in video_extensions):
                    dm_dir = os.path.join(root_path, f'{f}@meta')
                    dmcf_path = os.path.join(dm_dir, 'rmcf.json')
                    if os.path.exists(dmcf_path):
                        has_danmaku = 1
                        break
        except Exception as e:
            print(f"[分类展示模块] 检查弹幕失败: {e}")

        try:
            self.db_cursor.execute('SELECT id FROM anime WHERE root_path = ?', (root_path,))
            existing = self.db_cursor.fetchone()
            if existing:
                anime_id = existing[0]
                self.db_cursor.execute('DELETE FROM anime_tag WHERE anime_id = ?', (anime_id,))
            else:
                anime_id = None

            self.db_cursor.execute('''
                INSERT OR REPLACE INTO anime (root_path, name, name_pinyin, year, month, cover_path, episode_count, entry_time, last_watch_order, last_watch_time, last_video_time, has_danmaku)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (root_path, name, name_pinyin, year, month, cover_path, episode_count, entry_time, last_watch_order, last_watch_time, last_video_time, has_danmaku))

            #if anime_id is None:
            self.db_cursor.execute('SELECT id FROM anime WHERE root_path = ?', (root_path,))
            anime_id = self.db_cursor.fetchone()[0]

            for tag_name in tags_list:
                tag_name = tag_name.strip()
                if not tag_name:
                    continue

                tag_pinyin = self.get_pinyin(tag_name)
                self.db_cursor.execute('INSERT OR IGNORE INTO tag (name, pinyin) VALUES (?, ?)', (tag_name, tag_pinyin))
                self.db_cursor.execute('SELECT id FROM tag WHERE name = ?', (tag_name,))
                tag_id = self.db_cursor.fetchone()[0]
                self.db_cursor.execute('INSERT OR IGNORE INTO anime_tag (anime_id, tag_id) VALUES (?, ?)', (anime_id, tag_id))

            self.db_conn.commit()
            print(f"[分类展示模块] 添加番剧: {name} ({year}), 剧集数: {episode_count}, 标签: {tags_list}")
        except Exception as e:
            print(f"[分类展示模块] 添加番剧失败: {name}, 错误: {e}")

    

    def get_pinyin(self, name: str) -> str:
        """获取中文名称的拼音首字母"""
        if not name:
            return ''
        
        result = ''
        for char in name:
            if char in self.pinyin_dict:
                pinyin = self.pinyin_dict[char]
                if pinyin:
                    result += pinyin[0]
            else:
                # 如果不在字典中，直接使用字符的小写形式
                result += char.lower()
        
        return result
    
    def count_video_episodes(self, folder_path: str) -> int:
        """统计文件夹下的视频文件数量"""
        count = 0
        video_extensions = set(ext.lower() for ext in video_type_list)
        
        try:
            for entry in os.scandir(folder_path):
                if entry.is_file():
                    ext = os.path.splitext(entry.name)[1].lstrip('.')
                    if ext in video_extensions:
                        count += 1
        except Exception as e:
            print(f"[分类展示模块] 统计视频文件失败: {folder_path}, 错误: {e}")
        
        return count
    
    def get_all_anime(self) -> List[Dict]:
        """获取所有番剧数据"""
        self.db_cursor.execute('''
            SELECT a.root_path, a.name, a.year, a.cover_path, a.episode_count, GROUP_CONCAT(t.name) as tags
            FROM anime a
            LEFT JOIN anime_tag at ON a.id = at.anime_id
            LEFT JOIN tag t ON at.tag_id = t.id
            GROUP BY a.id
            ORDER BY a.year DESC, a.name
        ''')
        rows = self.db_cursor.fetchall()
        
        anime_list = []
        for row in rows:
            anime_list.append({
                'root_path': row[0],
                'name': row[1],
                'year': row[2],
                'cover_path': row[3],
                'episode_count': row[4],
                'tags': row[5].split(',') if row[5] else []
            })
        
        return anime_list

    def get_all_tags(self) -> List[str]:
        """获取所有不重复的标签"""
        self.db_cursor.execute('SELECT name FROM tag ORDER BY name')
        rows = self.db_cursor.fetchall()

        return [row[0] for row in rows]

    def get_all_tags_with_id(self) -> List[Dict]:
        """获取所有标签（带ID和拼音）"""
        self.db_cursor.execute('SELECT id, name, pinyin FROM tag ORDER BY pinyin ASC, name ASC')
        rows = self.db_cursor.fetchall()
        return [{'id': row[0], 'name': row[1], 'pinyin': row[2] or ''} for row in rows]

    def get_anime_detail(self, anime_id: int) -> Dict:
        """获取番剧详情

        Args:
            anime_id: 番剧ID

        Returns:
            包含番剧详情的字典
        """
        self.db_cursor.execute('''
            SELECT id, root_path, name, name_pinyin, year, month, cover_path, episode_count, entry_time
            FROM anime WHERE id = ?
        ''', (anime_id,))
        row = self.db_cursor.fetchone()

        if not row:
            return {}

        anime = {
            'id': row[0],
            'rootPath': row[1],
            'name': row[2],
            'pinyin': row[3] or '',
            'year': row[4],
            'month': row[5],
            'coverPath': row[6],
            'episodeCount': row[7],
            'entryTime': row[8]
        }

        md_path = os.path.join(row[1], '__MD__.json')
        if os.path.exists(md_path):
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    md_data = json.load(f)
                anime['mdName'] = md_data.get('name', '')
                anime['mdYear'] = md_data.get('year')
                anime['mdMonth'] = md_data.get('month')
                anime['tags'] = md_data.get('item', [])
                anime['introduction'] = md_data.get('introduction')
                anime['introductionSrc'] = md_data.get('introduction-src')
                anime['episodeMap'] = md_data.get('episode-map', [])
            except Exception as e:
                print(f"[分类展示模块] 读取__MD__.json失败: {e}")
                anime['tags'] = []
                anime['introduction'] = None
                anime['introductionSrc'] = None
                anime['episodeMap'] = []
        else:
            anime['tags'] = []
            anime['introduction'] = None
            anime['introductionSrc'] = None
            anime['episodeMap'] = []

        has_danmu = False
        danmu_sources = set()
        root_path = row[1]
        video_files = []

        if anime['episodeMap']:
            for ep in anime['episodeMap']:
                video_files.append({
                    'order': ep.get('order'),
                    'path': ep.get('path'),
                    'name': ep.get('name', '')
                })
        else:
            if os.path.exists(root_path):
                for f in os.listdir(root_path):
                    if f.lower().endswith(tuple(f'.{ext}' for ext in video_type_list)):
                        video_files.append({
                            'order': len(video_files) + 1,
                            'path': f,
                            'name': ''
                        })
            video_files.sort(key=lambda x: x['path'])
            for i in range(len(video_files)):
                video_files[i]['order'] = i + 1 # 重置为正确的剧集顺序


        anime['episodes'] = []
        for ep in video_files:
            video_name = ep['path']
            dm_dir = os.path.join(root_path, f'{video_name}@meta')
            dmcf_json_path = os.path.join(dm_dir, 'rmcf.json')
            dm_info_path = os.path.join(dm_dir, 'dm-info.json')

            has_ep_danmu = os.path.exists(dmcf_json_path)
            if has_ep_danmu:
                has_danmu = True

            ep_danmu_sources = []
            if os.path.exists(dm_info_path):
                try:
                    with open(dm_info_path, 'r', encoding='utf-8') as f:
                        dm_info = json.load(f)
                    dm_src_list = dm_info.get('dm-src', [])
                    for src in dm_src_list:
                        src_name = src.get('name', '')
                        if src_name:
                            danmu_sources.add(src_name)
                            ep_danmu_sources.append(src_name)
                except Exception as e:
                    print(f"[分类展示模块] 读取dm-info.json失败: {e}")

            anime['episodes'].append({
                'order': ep['order'],
                'name': ep['name'],
                'path': ep['path'],
                'hasDanmu': has_ep_danmu,
                'danmuSources': ep_danmu_sources
            })

        anime['hasDanmu'] = has_danmu
        anime['danmuSources'] = list(danmu_sources)

        self.db_cursor.execute('''
            SELECT t.name FROM tag t
            JOIN anime_tag at ON t.id = at.tag_id
            WHERE at.anime_id = ?
        ''', (anime_id,))
        anime['dbTags'] = [row[0] for row in self.db_cursor.fetchall()]

        #print(f"[分类展示模块] 剧集信息: {anime['episodes']}")
        return anime

    def get_anime_page(self, page: int = 1, page_size: int = 10, sort_by: str = 'year',
                       sort_order: str = 'DESC',
                       tag_filter_enabled: bool = False, selected_tags: List[int] = None) -> Dict:
        """获取番剧分页数据

        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            sort_by: 排序方式 ('year', 'addtime', 'pinyin')
            sort_order: 排序顺序 ('DESC' 降序, 'ASC' 升序)
            tag_filter_enabled: 是否启用标签筛选
            selected_tags: 选中的标签ID列表

        Returns:
            包含番剧列表、总数、所有标签的字典
        """
        if selected_tags is None:
            selected_tags = []

        order_symbol = sort_order.upper() if sort_order.upper() in ('ASC', 'DESC') else 'DESC'

        if sort_by == 'year':
            order_clause = f'ORDER BY a.year {order_symbol}, a.name'
        elif sort_by == 'addtime':
            order_clause = f'ORDER BY a.entry_time {order_symbol}, a.name'
        elif sort_by == 'pinyin':
            order_clause = f'ORDER BY a.name_pinyin {order_symbol}, a.name'
        else:
            order_clause = f'ORDER BY a.year {order_symbol}, a.name'

        # 构建标签筛选条件
        if tag_filter_enabled and selected_tags:
            placeholders = ','.join('?' * len(selected_tags))
            tag_filter_clause = f'AND t.id IN ({placeholders})'
            tag_filter_params = selected_tags
        else:
            tag_filter_clause = ''
            tag_filter_params = []

        # 获取总数
        if tag_filter_enabled and selected_tags:
            count_query = '''
                SELECT COUNT(DISTINCT a.id)
                FROM anime a
                JOIN anime_tag at ON a.id = at.anime_id
                JOIN tag t ON at.tag_id = t.id
                WHERE t.id IN ({placeholders})
                GROUP BY a.id
                HAVING COUNT(DISTINCT t.id) >= {tag_count}
            '''.format(placeholders=','.join('?' * len(selected_tags)), tag_count=len(selected_tags))
            self.db_cursor.execute(count_query, tag_filter_params)
            total = len(self.db_cursor.fetchall())
        else:
            self.db_cursor.execute('SELECT COUNT(*) FROM anime')
            total = self.db_cursor.fetchone()[0]

        # 计算分页
        offset = (page - 1) * page_size

        # 获取番剧列表
        if tag_filter_enabled and selected_tags:
            query = '''
                SELECT a.id, a.root_path, a.name, a.year, a.cover_path, a.episode_count, a.name_pinyin,
                       GROUP_CONCAT(DISTINCT t.name) as tags,
                       GROUP_CONCAT(DISTINCT t.id) as tag_ids
                FROM anime a
                LEFT JOIN anime_tag at ON a.id = at.anime_id
                LEFT JOIN tag t ON at.tag_id = t.id
                WHERE a.id IN (
                    SELECT DISTINCT a.id
                    FROM anime a
                    JOIN anime_tag at ON a.id = at.anime_id
                    JOIN tag t ON at.tag_id = t.id
                    WHERE t.id IN ({placeholders})
                    GROUP BY a.id
                    HAVING COUNT(DISTINCT t.id) >= {tag_count}
                )
                GROUP BY a.id
                {order_clause}
                LIMIT ? OFFSET ?
            '''.format(placeholders=','.join('?' * len(selected_tags)), tag_count=len(selected_tags), order_clause=order_clause)
            params = tag_filter_params + [page_size, offset]
        else:
            query = f'''
                SELECT a.id, a.root_path, a.name, a.year, a.cover_path, a.episode_count, a.name_pinyin,
                       GROUP_CONCAT(DISTINCT t.name) as tags,
                       GROUP_CONCAT(DISTINCT t.id) as tag_ids
                FROM anime a
                LEFT JOIN anime_tag at ON a.id = at.anime_id
                LEFT JOIN tag t ON at.tag_id = t.id
                GROUP BY a.id
                {order_clause}
                LIMIT ? OFFSET ?
            '''
            params = [page_size, offset]

        self.db_cursor.execute(query, params)
        rows = self.db_cursor.fetchall()
        print(rows)
        anime_list = []
        for row in rows:
            tag_ids_str = row[8] or ''
            tag_ids = [int(tid) for tid in tag_ids_str.split(',') if tid]
            tags_str = row[7] or ''
            tags = tags_str.split(',') if tags_str else []

            anime_list.append({
                'id': row[0],
                'root_path': row[1],
                'name': row[2],
                'year': row[3],
                'poster': row[4],
                'episode_count': row[5],
                'name_pinyin': row[6] or '',
                'tags': tags,
                'tag_ids': tag_ids
            })

        # 获取所有标签
        all_tags = self.get_all_tags_with_id()

        return {
            'animeList': anime_list,
            'total': total,
            'allTags': all_tags,
            'page': page,
            'pageSize': page_size,
            'totalPages': (total + page_size - 1) // page_size if page_size > 0 else 1
        }

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
        db_conn = getattr(self, 'db_conn', None)
        if db_conn is not None:
            db_conn.close()
            self.db_conn = None
            self.db_cursor = None

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
            tags = self.get_all_tags()
            message = json.dumps({
                'command': 'ALL_TAGS',
                'data': tags
            }, ensure_ascii=False)
            await websocket.send(message)
            print(f"[分类展示模块] 发送所有标签，共 {len(tags)} 个")

        elif command == 'GET_ANIME_PAGE':
            widget_id = data.get('widgetId', '')
            page = data.get('page', 1)
            page_size = data.get('pageSize', 10)
            sort_by = data.get('sortBy', 'year')
            sort_order = data.get('sortOrder', 'DESC')
            tag_filter_enabled = data.get('tagFilterEnabled', False)
            selected_tags = data.get('selectedTags', [])

            print(f"[分类展示模块] 收到获取番剧分页请求: page={page}, sortBy={sort_by}, sortOrder={sort_order}, tagFilter={tag_filter_enabled}")
            result = self.get_anime_page(page, page_size, sort_by, sort_order, tag_filter_enabled, selected_tags)

            message = json.dumps({
                'command': 'ANIME_PAGE_DATA',
                'widgetId': widget_id,
                'animeList': result['animeList'],
                'total': result['total'],
                'allTags': result['allTags'],
                'page': result['page'],
                'pageSize': result['pageSize'],
                'totalPages': result['totalPages']
            }, ensure_ascii=False)
            await websocket.send(message)
            print(f"[分类展示模块] 发送番剧分页数据，共 {len(result['animeList'])} 条")

        elif command == 'GET_ANIME_DETAIL':
            widget_id = data.get('widgetId', '')
            anime_id = data.get('animeId')
            print(f"[分类展示模块] 收到获取番剧详情请求: animeId={anime_id}")
            result = self.get_anime_detail(anime_id)
            message = json.dumps({
                'command': 'ANIME_DETAIL_DATA',
                'widgetId': widget_id,
                'animeDetail': result
            }, ensure_ascii=False)
            await websocket.send(message)
            print(f"[分类展示模块] 发送番剧详情数据")

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
