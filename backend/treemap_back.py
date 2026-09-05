# treemap_back.py - 树状图模块的后端实现
import os
import json
from collections import defaultdict
import time
from concurrent.futures import ThreadPoolExecutor

from config.file_type import *

class TreemapModule:
    def __init__(self, global_config):
        # 初始化模块配置
        self.DRAW_TREE_MAX_DEPTH = 5
        self.FRAGMENTED_THRESHOLD_MODE = 'percentage'  # 'percentage' 或 'size'
        self.FRAGMENTED_THRESHOLD_PERCENTAGE = 0.5  # 百分比模式下的值（0-100）
        self.FRAGMENTED_THRESHOLD_SIZE = 10  # 大小模式下的值
        self.FRAGMENTED_THRESHOLD_UNIT = 'MB'  # 大小模式下的单位（B/KB/MB）
        
        # 获取脚本所在目录的绝对路径
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 配置文件路径
        self.config_path = os.path.join(self.script_dir, 'config', 'treemap_config.json')
        
        # 加载配置
        self.load_config()
        
        # 初始化文件类型映射
        self.EXT_TO_TYPE = self.get_ext_to_type()
        self.global_config = global_config
    
    def load_config(self):
        """加载树状图配置"""
        if os.path.exists(self.config_path) and os.path.isfile(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.DRAW_TREE_MAX_DEPTH = config.get('draw_tree_max_depth', self.DRAW_TREE_MAX_DEPTH)
                    self.FRAGMENTED_THRESHOLD_MODE = config.get('fragmented_threshold_mode', self.FRAGMENTED_THRESHOLD_MODE)
                    self.FRAGMENTED_THRESHOLD_PERCENTAGE = config.get('fragmented_threshold_percentage', self.FRAGMENTED_THRESHOLD_PERCENTAGE)
                    self.FRAGMENTED_THRESHOLD_SIZE = config.get('fragmented_threshold_size', self.FRAGMENTED_THRESHOLD_SIZE)
                    self.FRAGMENTED_THRESHOLD_UNIT = config.get('fragmented_threshold_unit', self.FRAGMENTED_THRESHOLD_UNIT)
                    print(f"[树状图模块] 配置加载成功: 深度={self.DRAW_TREE_MAX_DEPTH}, 模式={self.FRAGMENTED_THRESHOLD_MODE}, 百分比值={self.FRAGMENTED_THRESHOLD_PERCENTAGE}, 大小值={self.FRAGMENTED_THRESHOLD_SIZE}, 单位={self.FRAGMENTED_THRESHOLD_UNIT}")
            except Exception as e:
                print(f"[树状图模块] 配置加载失败: {e}")
    
    def save_config(self):
        """保存树状图配置"""
        # 确保config目录存在
        config_dir = os.path.join(self.script_dir, 'config')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        config = {
            'draw_tree_max_depth': self.DRAW_TREE_MAX_DEPTH,
            'fragmented_threshold_mode': self.FRAGMENTED_THRESHOLD_MODE,
            'fragmented_threshold_percentage': self.FRAGMENTED_THRESHOLD_PERCENTAGE,
            'fragmented_threshold_size': self.FRAGMENTED_THRESHOLD_SIZE,
            'fragmented_threshold_unit': self.FRAGMENTED_THRESHOLD_UNIT
        }
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"[树状图模块] 配置保存成功: {config}")
        except Exception as e:
            print(f"[树状图模块] 配置保存失败: {e}")
    
    def get_ext_to_type(self):
        """创建后缀名到类型的映射字典"""
        ext_to_type = defaultdict(lambda: 'other')

        # 填充后缀名映射
        for ext in image_type_list:
            ext_to_type[ext.lower()] = 'image'
        for ext in video_type_list:
            ext_to_type[ext.lower()] = 'video'
        for ext in audio_type_list:
            ext_to_type[ext.lower()] = 'audio'
        for ext in document_type_list:
            ext_to_type[ext.lower()] = 'document'
        for ext in sourcecode_type_list:
            ext_to_type[ext.lower()] = 'sourcecode'
        for ext in script_type_list:
            ext_to_type[ext.lower()] = 'script'
        for ext in database_type_list:
            ext_to_type[ext.lower()] = 'database'
        for ext in dataseg_type_list:
            ext_to_type[ext.lower()] = 'dataseg'
        for ext in tempfile_type_list:
            ext_to_type[ext.lower()] = 'tempfile'
        for ext in executable_type_list:
            ext_to_type[ext.lower()] = 'executable'
        for ext in shortcut_type_list:
            ext_to_type[ext.lower()] = 'shortcut'
        for ext in zip_type_list:
            ext_to_type[ext.lower()] = 'zip'
        for ext in fonts_type_list:
            ext_to_type[ext.lower()] = 'fonts'
        for ext in config_type_list:
            ext_to_type[ext.lower()] = 'config'
        for ext in system_type_list:
            ext_to_type[ext.lower()] = 'system'
        for ext in vm_type_list:
            ext_to_type[ext.lower()] = 'vm'
        return ext_to_type
    
    def get_file_type(self, file_path):
        """根据文件扩展名判断文件类型"""
        # 获取扩展名
        _, ext = os.path.splitext(file_path)
        ext = ext.lstrip('.').lower()

        # 使用预构建的映射字典直接查找
        return self.EXT_TO_TYPE.get(ext, 'other')
    
    def add_file_type_info(self, root_node):
        """为节点添加文件类型信息（用于前端颜色显示）"""
        if not root_node:
            return root_node

        # 使用栈进行迭代遍历
        stack = [root_node]

        while stack:
            node = stack.pop()

            # 为当前节点添加类型信息
            if node['type'] == 'file':
                node['file_type'] = self.get_file_type(node['path'])
            elif node['type'] == 'folder':
                node['file_type'] = 'folder'
            elif node['type'] == 'fragmented_group':
                node['file_type'] = 'fragmented'
            elif node['type'] == 'unknown':
                node['file_type'] = 'unknown'

            # 将子节点加入栈中继续遍历
            if 'children' in node:
                for child in node['children']:
                    stack.append(child)

        return root_node
    
    def get_folder_total_size(self, path):
        """计算文件夹的总大小（不展开结构）"""
        total_size = 0
        try:
            # 使用os.walk()的替代方案，使用os.scandir()递归遍历
            stack = [path]
            while stack:
                current_path = stack.pop()
                try:
                    with os.scandir(current_path) as entries:
                        for entry in entries:
                            # 跳过隐藏文件/文件夹
                            if entry.name.startswith('.'):
                                continue
                            
                            if entry.is_dir(follow_symlinks=False):
                                stack.append(entry.path)
                            else:
                                try:
                                    # 使用entry.stat()获取文件大小，减少系统调用
                                    total_size += entry.stat().st_size
                                except (OSError, PermissionError):
                                    continue
                except PermissionError:
                    continue
        except Exception:
            pass
        return total_size
    
    def process_directory(self, node, path, current_depth, max_depth):
        """处理单个目录的扫描"""
        try:
            # 使用os.scandir()代替os.listdir()，减少系统调用
            with os.scandir(path) as entries:
                children = []
                dir_items = []

                for entry in entries:
                    # 跳过隐藏文件
                    if entry.name.startswith('.'):
                        continue

                    if entry.is_dir(follow_symlinks=False):
                        if current_depth + 1 < max_depth:
                            child_node = {
                                'name': entry.name,
                                'path': entry.path,
                                'size': 0,
                                'type': 'folder',
                                'children': []
                            }
                            children.append(child_node)
                            dir_items.append((child_node, entry.path, current_depth + 1))
                        else:
                            child_info = {
                                'name': entry.name,
                                'path': entry.path,
                                'size': self.get_folder_total_size(entry.path),
                                'type': 'folder',
                                'is_truncated': True
                            }
                            children.append(child_info)
                    else:
                        try:
                            # 使用entry.stat()获取文件大小，减少系统调用
                            file_size = entry.stat().st_size
                            child_info = {
                                'name': entry.name,
                                'path': entry.path,
                                'size': file_size,
                                'type': 'file'
                            }
                            children.append(child_info)
                        except (OSError, PermissionError):
                            continue
        except PermissionError:
            node['error'] = 'Permission denied'
            return

        node['children'] = children

        # 递归处理子目录
        for child_node, item_path, child_depth in dir_items:
            self.process_directory(child_node, item_path, child_depth, max_depth)

        # 计算当前节点大小
        total_size = 0
        for child in node['children']:
            total_size += child['size']
        node['size'] = total_size
    
    def get_folder_size_with_depth(self, path, max_depth=3, current_depth=0):
        """扫描目录，返回目录大小和文件/子目录信息"""
        try:
            # 获取文件/文件夹的基本信息
            if os.path.isfile(path):
                return {
                    'name': os.path.basename(path),
                    'path': path,
                    'size': os.path.getsize(path),
                    'type': 'file'
                }

            # 如果是文件夹，使用迭代方式处理
            root_node = {
                'name': os.path.basename(path),
                'path': path,
                'size': 0,
                'type': 'folder',
                'children': []
            }

            # 使用栈来模拟递归，每个元素为 (当前节点, 当前路径, 当前深度, 是否已处理子项)
            stack = [(root_node, path, current_depth, False)]

            while stack:
                current_node, current_path, depth, processed = stack.pop()

                if not processed:
                    # 第一次处理，获取子项列表
                    try:
                        # 使用os.scandir()代替os.listdir()，减少系统调用
                        with os.scandir(current_path) as entries:
                            children = []
                            dir_items = []  # 存储需要并行处理的目录

                            for entry in entries:
                                # 跳过隐藏文件
                                if entry.name.startswith('.'):
                                    continue

                                if entry.is_dir(follow_symlinks=False):
                                    # 检查是否达到最大深度
                                    if depth + 1 < max_depth:
                                        # 继续扫描子文件夹
                                        child_node = {
                                            'name': entry.name,
                                            'path': entry.path,
                                            'size': 0,
                                            'type': 'folder',
                                            'children': []
                                        }
                                        children.append(child_node)
                                        dir_items.append((child_node, entry.path, depth + 1))
                                    else:
                                        # 达到最大深度，只计算总大小，不展开内容
                                        child_info = {
                                            'name': entry.name,
                                            'path': entry.path,
                                            'size': self.get_folder_total_size(entry.path),
                                            'type': 'folder',
                                            'is_truncated': True  # 标记为被截断的文件夹
                                        }
                                        children.append(child_info)
                                else:
                                    # 文件
                                    try:
                                        # 使用entry.stat()获取文件大小，减少系统调用
                                        file_size = entry.stat().st_size
                                        child_info = {
                                            'name': entry.name,
                                            'path': entry.path,
                                            'size': file_size,
                                            'type': 'file'
                                        }
                                        children.append(child_info)
                                    except (OSError, PermissionError):
                                        # 无法读取的文件
                                        continue
                    except PermissionError:
                        # 无权限访问的文件夹
                        current_node['error'] = 'Permission denied'
                        continue

                    current_node['children'] = children
                    
                    # 并行处理子目录
                    if dir_items:
                        # 限制线程池大小，避免过多线程导致系统负载过高
                        max_workers = min(8, len(dir_items))
                        with ThreadPoolExecutor(max_workers=max_workers) as executor:
                            # 为每个子目录创建一个任务
                            futures = []
                            for child_node, item_path, child_depth in dir_items:
                                # 提交任务到线程池
                                future = executor.submit(self.process_directory, child_node, item_path, child_depth, max_depth)
                                futures.append(future)
                            
                            # 等待所有任务完成
                            for future in futures:
                                try:
                                    future.result()
                                except Exception as e:
                                    print(f"处理目录时出错: {e}")
                    
                    # 将当前节点重新压入栈，标记为已处理
                    stack.append((current_node, current_path, depth, True))
                else:
                    # 第二次处理，计算大小
                    total_size = 0
                    for child in current_node['children']:
                        total_size += child['size']
                    current_node['size'] = total_size

            return root_node

        except Exception as e:
            return {
                'name': os.path.basename(path),
                'path': path,
                'size': 0,
                'type': 'unknown',
                'error': str(e)
            }
    
    def process_fragmented_items(self, root_node, root_total_size, threshold_percent=0.5):
        """处理散碎文件：将占根目录百分比小于阈值的项合并为'散碎文件'"""
        # 同时处理 'folder' 和 'directory' 类型的节点
        if root_node.get('type') not in ['folder', 'directory']:
            return root_node

        # 如果根目录大小为0，无法计算百分比
        if root_total_size == 0:
            return root_node

        print(f"[树状图模块] 开始处理散碎文件，阈值: {threshold_percent}%")
        print(f"[树状图模块] 根目录总大小: {root_total_size / (1024 ** 3):.2f} GB")

        # 使用栈进行迭代处理，每个元素为 (node, parent_node, parent_children_index)
        # 先进行深度优先遍历，收集所有需要处理的节点
        stack = [(root_node, None, None)]
        nodes_to_process = []  # 存储需要处理的节点及其父节点信息

        # 第一遍：遍历所有节点，收集需要处理的文件夹节点
        while stack:
            node, parent, child_index = stack.pop()

            # 处理文件夹节点和目录节点
            if node.get('type') in ['folder', 'directory']:
                # 只将文件夹节点添加到处理列表中
                if node.get('type') == 'folder':
                    nodes_to_process.append((node, parent, child_index))

                # 将子节点加入栈中继续遍历，无论子节点类型是什么
                children = node.get('children', [])
                for i, child in enumerate(children):
                    stack.append((child, node, i))

        print(f"[树状图模块] 收集到 {len(nodes_to_process)} 个文件夹节点需要处理")

        # 第二遍：从最深层开始处理（逆序），这样确保子节点先处理完
        for node, parent, child_index in reversed(nodes_to_process):
            children = node.get('children', [])
            if not children:
                continue

            total_size = node['size']
            if total_size == 0:
                continue

            # 分类：正常项和散碎项（基于相对于根目录的百分比）
            normal_items = []
            fragmented_items = []
            fragmented_size = 0

            for child in children:
                child_size = child['size']
                # 计算相对于根目录的百分比
                percentage = (child_size / root_total_size) * 100

                if percentage < threshold_percent:
                    # 属于散碎项
                    fragmented_items.append(child)
                    fragmented_size += child_size
                else:
                    # 正常项
                    normal_items.append(child)

            # 如果有散碎项，将它们合并为一个"散碎文件"项
            if fragmented_items:
                # 按大小排序，使显示更有序（大文件在前）
                fragmented_items.sort(key=lambda x: x['size'], reverse=True)

                # 创建散碎文件组
                fragmented_group = {
                    'name': '📦 散碎文件',
                    'path': node['path'],
                    'size': fragmented_size,
                    'type': 'fragmented_group',
                    'children': fragmented_items,  # 保留原始子项（用于详细信息）
                    'fragmented_count': len(fragmented_items),
                    'threshold': threshold_percent
                }

                # 替换children：正常项 + 散碎文件组
                node['children'] = normal_items + [fragmented_group]

                # 添加统计信息
                node['fragmented_info'] = {
                    'total_fragmented': len(fragmented_items),
                    'total_fragmented_size': fragmented_size,
                    'threshold': threshold_percent,
                    'relative_to_root': True
                }
            else:
                # 没有散碎项，保持原有子项
                node['children'] = normal_items

            # 按大小排序（可选，使显示更有序）
            if node['children']:
                node['children'].sort(key=lambda x: x['size'], reverse=True)

        return root_node

    
    async def handle_refresh(self, websocket, real_base_dirs):
        """处理刷新请求"""
        print("[树状图模块] 收到刷新请求，重新扫描目录...")
        scan_start_time = time.time()
        
        # 处理多个根目录
        directory_structure = {
            'name': 'Multiple Roots',
            'path': '',
            'size': 0,
            'type': 'directory',
            'children': []
        }

        for base_dir in real_base_dirs:
            try:
                root_data = self.get_folder_size_with_depth(base_dir, max_depth=self.DRAW_TREE_MAX_DEPTH - 1)  # 减少一级深度
                directory_structure['children'].append(root_data)
                directory_structure['size'] += root_data['size']
                print(f"[树状图模块] 扫描完成根目录: {base_dir}, 大小: {root_data['size'] / (1024 ** 3):.2f} GB")
            except Exception as e:
                print(f"[树状图模块] 扫描根目录失败 {base_dir}: {e}")
        
        scan_elapsed = time.time() - scan_start_time
        print(f"[树状图模块] 扫描完成，总耗时: {scan_elapsed:.2f}秒")
        print(f"[树状图模块] 总大小: {directory_structure['size'] / (1024 ** 3):.2f} GB")
        
        # 添加文件类型信息
        self.add_file_type_info(directory_structure)
        
        # 处理散碎文件
        root_total_size = directory_structure['size']
        
        # 根据当前设置的阈值模式计算阈值
        if self.FRAGMENTED_THRESHOLD_MODE == 'percentage':
            threshold_percent = self.FRAGMENTED_THRESHOLD_PERCENTAGE
            print(f"[树状图模块] 使用百分比阈值: {threshold_percent}%")
        else:
            # 将大小阈值转换为字节
            threshold_bytes = self.FRAGMENTED_THRESHOLD_SIZE
            if self.FRAGMENTED_THRESHOLD_UNIT == 'KB':
                threshold_bytes *= 1024
            elif self.FRAGMENTED_THRESHOLD_UNIT == 'MB':
                threshold_bytes *= 1024 * 1024
            # 转换为相对于总大小的百分比
            threshold_percent = (threshold_bytes / root_total_size) * 100 if root_total_size > 0 else 0.5
            print(f"[树状图模块] 使用大小阈值: {self.FRAGMENTED_THRESHOLD_SIZE} {self.FRAGMENTED_THRESHOLD_UNIT} ({threshold_percent:.2f}%)")
        
        directory_structure = self.process_fragmented_items(directory_structure, root_total_size, threshold_percent=threshold_percent)
        
        # 发送目录结构数据
        structure_message = json.dumps({
            "command": 'DIRECTORY_STRUCTURE',
            "data": directory_structure
        }, ensure_ascii=False)
        await websocket.send(structure_message)
        print("[树状图模块] 刷新后的目录结构数据已发送")
    
    async def handle_request_deeper(self, websocket, data):
        """处理深层请求"""
        folder_path = data.get('path')
        if folder_path and os.path.exists(folder_path):
            deeper_data = self.get_folder_size_with_depth(folder_path, max_depth=self.DRAW_TREE_MAX_DEPTH)
            self.add_file_type_info(deeper_data)
            # 对于深层请求，使用该文件夹的大小作为基准
            folder_total_size = deeper_data['size']
            
            # 根据当前设置的阈值模式计算阈值
            if self.FRAGMENTED_THRESHOLD_MODE == 'percentage':
                threshold_percent = self.FRAGMENTED_THRESHOLD_PERCENTAGE
            else:
                # 将大小阈值转换为字节
                threshold_bytes = self.FRAGMENTED_THRESHOLD_SIZE
                if self.FRAGMENTED_THRESHOLD_UNIT == 'KB':
                    threshold_bytes *= 1024
                elif self.FRAGMENTED_THRESHOLD_UNIT == 'MB':
                    threshold_bytes *= 1024 * 1024
                # 转换为相对于当前文件夹的百分比
                threshold_percent = (threshold_bytes / folder_total_size) * 100 if folder_total_size > 0 else 0.5
            
            deeper_data = self.process_fragmented_items(deeper_data, folder_total_size, threshold_percent=threshold_percent)
            await websocket.send(json.dumps({
                "command": 'DEEPER_STRUCTURE',
                "data": deeper_data
            }, ensure_ascii=False))
    
    async def handle_set_depth(self, data):
        """处理设置树状图深度请求"""
        depth = data.get('depth', 3)
        if isinstance(depth, int) and 1 <= depth <= 256:
            self.DRAW_TREE_MAX_DEPTH = depth
            print(f"[树状图模块] 树状图深度已设置为: {depth}")
            # 保存配置
            self.save_config()
    
    async def handle_set_threshold(self, data):
        """处理设置散碎文件阈值请求"""
        mode = data.get('mode', 'percentage')
        threshold = data.get('threshold', 0.5)
        unit = data.get('unit', 'MB')
        
        if mode == 'percentage':
            if isinstance(threshold, (int, float)) and 0 <= threshold <= 100:
                self.FRAGMENTED_THRESHOLD_MODE = 'percentage'
                self.FRAGMENTED_THRESHOLD_PERCENTAGE = threshold
                # 保存配置
                self.save_config()
        elif mode == 'size':
            if isinstance(threshold, int) and threshold > 0 and unit in ['B', 'KB', 'MB']:
                self.FRAGMENTED_THRESHOLD_MODE = 'size'
                self.FRAGMENTED_THRESHOLD_SIZE = threshold
                self.FRAGMENTED_THRESHOLD_UNIT = unit
                # 保存配置
                self.save_config()
    
    async def send_initial_config(self, websocket):
        """发送初始配置"""
        # 发送当前配置
        config_message = json.dumps({
            "command": 'SET_CONFIG',
            "depth": self.DRAW_TREE_MAX_DEPTH,
            "threshold_mode": self.FRAGMENTED_THRESHOLD_MODE,
            "threshold_percentage": self.FRAGMENTED_THRESHOLD_PERCENTAGE,
            "threshold_size": self.FRAGMENTED_THRESHOLD_SIZE,
            "threshold_unit": self.FRAGMENTED_THRESHOLD_UNIT
        })
        await websocket.send(config_message)
        print(f"[树状图模块] 已发送当前配置: 深度={self.DRAW_TREE_MAX_DEPTH}, 模式={self.FRAGMENTED_THRESHOLD_MODE}, 百分比值={self.FRAGMENTED_THRESHOLD_PERCENTAGE}, 大小值={self.FRAGMENTED_THRESHOLD_SIZE}, 单位={self.FRAGMENTED_THRESHOLD_UNIT}")
    
    async def scan_directory_structure(self, websocket, real_base_dirs):
        """扫描目录结构并发送数据"""
        print("[树状图模块] 开始扫描目录...")
        scan_start_time = time.time()

        # 处理多个根目录
        directory_structure = {
            'name': 'Multiple Roots',
            'path': '',
            'size': 0,
            'type': 'directory',
            'children': []
        }

        for base_dir in real_base_dirs:
            try:
                root_data = self.get_folder_size_with_depth(base_dir, max_depth=self.DRAW_TREE_MAX_DEPTH - 1)  # 减少一级深度，因为根目录会作为子节点
                directory_structure['children'].append(root_data)
                directory_structure['size'] += root_data['size']
                print(f"[树状图模块] 扫描完成根目录: {base_dir}, 大小: {root_data['size'] / (1024 ** 3):.2f} GB")
            except Exception as e:
                print(f"[树状图模块] 扫描根目录失败 {base_dir}: {e}")

        scan_elapsed = time.time() - scan_start_time
        print(f"[树状图模块] 扫描完成，总耗时: {scan_elapsed:.2f}秒")
        print(f"[树状图模块] 总大小: {directory_structure['size'] / (1024 ** 3):.2f} GB")

        # 添加文件类型信息
        print("[树状图模块] 添加文件类型信息...")
        type_start = time.time()
        self.add_file_type_info(directory_structure)
        type_elapsed = time.time() - type_start
        print(f"[树状图模块] 添加类型信息耗时: {type_elapsed:.3f}秒")

        # 处理散碎文件
        frag_start = time.time()
        root_total_size = directory_structure['size']  # 获取总大小
        
        # 根据当前设置的阈值模式计算阈值
        if self.FRAGMENTED_THRESHOLD_MODE == 'percentage':
            threshold_percent = self.FRAGMENTED_THRESHOLD_PERCENTAGE
        else:
            # 将大小阈值转换为字节
            threshold_bytes = self.FRAGMENTED_THRESHOLD_SIZE
            if self.FRAGMENTED_THRESHOLD_UNIT == 'KB':
                threshold_bytes *= 1024
            elif self.FRAGMENTED_THRESHOLD_UNIT == 'MB':
                threshold_bytes *= 1024 * 1024
            # 转换为相对于总大小的百分比
            threshold_percent = (threshold_bytes / root_total_size) * 100 if root_total_size > 0 else 0.5
        
        directory_structure = self.process_fragmented_items(directory_structure, root_total_size, threshold_percent=threshold_percent)
        frag_elapsed = time.time() - frag_start

        # 发送目录结构数据
        structure_message = json.dumps({
            "command": 'DIRECTORY_STRUCTURE',
            "data": directory_structure
        }, ensure_ascii=False)
        await websocket.send(structure_message)
        print("[树状图模块] 目录结构数据已发送")

    ######################
    #以下实现必要的接口
    ######################

    async def when_connect(self, websocket):
        """当连接建立时调用"""
        print("[树状图模块] 连接建立成功")
        
    async def when_disconnect(self, websocket):
        """当连接断开时调用"""
        print("[树状图模块] 连接断开")

    async def message_proc(self, websocket, data):
        """处理消息"""
        #print(f"[树状图模块] 收到消息: {data}")
        if data.get('command') == 'REQUEST_DEEPER':
            # 处理深层请求
            await self.handle_request_deeper(websocket, data)
        
        elif data.get('command') == 'REFRESH':
            # 处理刷新请求
            await self.handle_refresh(websocket, self.global_config.get('base_dir', []))
        
        elif data.get('command') == 'SET_DEPTH':
            # 处理设置树状图深度请求
            await self.handle_set_depth(data)
        
        elif data.get('command') == 'SET_THRESHOLD':
            # 处理设置散碎文件阈值请求
            await self.handle_set_threshold(data)
        
        elif data.get('command') == 'TREEMAP_ACTIVATED':
            # 处理树状图模块激活请求
            print("[树状图模块] 收到激活消息，发送初始配置和目录结构")
            # 发送初始配置
            await self.send_initial_config(websocket)
            # 扫描目录结构并发送数据
            await self.scan_directory_structure(websocket, self.global_config.get('base_dir', []))
            

# 模块工厂函数，用于创建模块实例
def create_module(global_config, back_version):
    return TreemapModule(global_config)
