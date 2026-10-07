import os
import sqlite3
from typing import List, Dict 

class DatabaseManager:
    """数据库管理类，负责数据库操作和连接。"""
    def __init__(self, module_dir: str, db_path: str):
        self.module_dir = module_dir
        self.db_path = db_path
        # 拼音字典
        # 拼音字典
        self.pinyin_dict = {}
        # 加载拼音字典
        self.load_pinyin_dict()
        # 初始化数据库
        self.init_database()


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
    
    def close(self):
        """关闭数据库连接"""
        db_conn = getattr(self, 'db_conn', None)
        if db_conn is not None:
            db_conn.close()
            self.db_conn = None
            self.db_cursor = None
