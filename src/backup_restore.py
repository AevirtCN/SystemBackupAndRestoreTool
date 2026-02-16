import os
import shutil
import concurrent.futures
from .utils import zip_directory, unzip_file, copy_directory, get_timestamp, create_dir

class BackupRestore:
    def __init__(self):
        pass

    def backup(self, source_dir, backup_path, compress=True, callback=None, max_workers=4, align_4k=True, compress_level='standard'):
        """
        备份目录
        :param source_dir: 源目录路径
        :param backup_path: 备份文件或目录路径
        :param compress: 是否压缩备份
        :param callback: 进度回调函数，接收当前进度百分比
        :param max_workers: 最大工作线程数
        :param align_4k: 是否启用4K对齐(GPT分区)
        :param compress_level: 压缩程度，可选值：none, fast, standard, maximum, ultra
        :return: 备份文件路径
        """
        try:
            if not os.path.exists(source_dir):
                raise Exception(f"源目录不存在: {source_dir}")

            # 创建备份路径目录
            backup_dir = os.path.dirname(backup_path)
            if backup_dir:
                create_dir(backup_dir)

            if compress:
                # 压缩备份（多线程）
                timestamp = get_timestamp()
                backup_file = os.path.join(backup_path, f"backup_{timestamp}.zip")
                create_dir(os.path.dirname(backup_file))
                zip_directory(source_dir, backup_file, max_workers=max_workers, callback=callback)
                return backup_file
            else:
                # 直接复制（多线程）
                timestamp = get_timestamp()
                backup_dir = os.path.join(backup_path, f"backup_{timestamp}")
                copy_directory(source_dir, backup_dir, max_workers=max_workers, callback=callback)
                return backup_dir
        except Exception as e:
            if callback:
                callback(-1, str(e))
            raise

    def restore(self, backup_file, restore_path, callback=None, max_workers=4):
        """
        还原备份
        :param backup_file: 备份文件或目录路径
        :param restore_path: 还原目标路径
        :param callback: 进度回调函数，接收当前进度百分比
        :param max_workers: 最大工作线程数
        :return: 还原结果
        """
        try:
            if not os.path.exists(backup_file):
                raise Exception(f"备份文件不存在: {backup_file}")

            # 创建还原路径目录
            create_dir(restore_path)

            if backup_file.endswith('.zip'):
                # 解压缩还原（多线程）
                unzip_file(backup_file, restore_path, max_workers=max_workers, callback=callback)
            else:
                # 直接复制还原（多线程）
                # 找到备份目录中的实际内容
                backup_contents = os.listdir(backup_file)
                if backup_contents:
                    source_content = os.path.join(backup_file, backup_contents[0])
                    if os.path.isdir(source_content):
                        # 复制目录内容
                        total_items = len(os.listdir(source_content))
                        processed_items = 0
                        
                        for item in os.listdir(source_content):
                            s = os.path.join(source_content, item)
                            d = os.path.join(restore_path, item)
                            if os.path.isdir(s):
                                # 多线程复制目录
                                def dir_callback(progress):
                                    if callback:
                                        item_progress = int((processed_items + progress/100) / total_items * 100)
                                        callback(item_progress)
                                
                                copy_directory(s, d, max_workers=max_workers, callback=dir_callback)
                            else:
                                # 复制单个文件
                                shutil.copy2(s, d)
                                if callback:
                                    processed_items += 1
                                    item_progress = int(processed_items / total_items * 100)
                                    callback(item_progress)
                        if callback:
                            callback(100)
                else:
                    if callback:
                        callback(100)
            return True
        except Exception as e:
            if callback:
                callback(-1, str(e))
            raise

    def get_backup_info(self, backup_file):
        """
        获取备份文件信息
        :param backup_file: 备份文件路径
        :return: 备份信息字典
        """
        try:
            if not os.path.exists(backup_file):
                return None

            # 检测备份格式
            backup_format = self.detect_backup_format(backup_file)

            info = {
                'path': backup_file,
                'size': os.path.getsize(backup_file) if os.path.isfile(backup_file) else 0,
                'is_compressed': backup_file.endswith('.zip') or backup_format in ['ghost', 'atih'],
                'backup_time': os.path.getmtime(backup_file),
                'format': backup_format
            }
            return info
        except Exception:
            return None

    def detect_backup_format(self, backup_file):
        """
        检测备份文件格式
        :param backup_file: 备份文件路径
        :return: 备份格式字符串
        """
        if not os.path.isfile(backup_file):
            return 'directory'
        
        # 基于文件扩展名检测格式
        ext = os.path.splitext(backup_file)[1].lower()
        
        if ext == '.zip':
            return 'zip'
        elif ext in ['.7z']:
            return '7z'
        elif ext in ['.rar']:
            return 'rar'
        elif ext in ['.tar', '.gz', '.tar.gz', '.tgz']:
            return 'tar'
        elif ext in ['.wim']:
            return 'wim'
        elif ext in ['.esd']:
            return 'esd'
        elif ext in ['.gho', '.ghs']:
            return 'ghost'
        elif ext in ['.tib', '.tibx']:
            return 'atih'
        elif ext in ['.bak']:
            return 'generic'
        else:
            return 'unknown'

    def restore_from_ghost(self, backup_file, restore_path, callback=None):
        """
        从Ghost备份中还原
        :param backup_file: Ghost备份文件路径
        :param restore_path: 还原目标路径
        :param callback: 进度回调函数
        :return: 还原结果
        """
        # 注意：完整的Ghost备份还原需要使用Norton Ghost工具
        # 这里仅提供框架，实际使用时需要调用外部工具
        raise NotImplementedError("Ghost备份还原需要使用Norton Ghost工具")

    def restore_from_atih(self, backup_file, restore_path, callback=None):
        """
        从ATIH备份中还原
        :param backup_file: ATIH备份文件路径
        :param restore_path: 还原目标路径
        :param callback: 进度回调函数
        :return: 还原结果
        """
        # 注意：完整的ATIH备份还原需要使用Acronis True Image工具
        # 这里仅提供框架，实际使用时需要调用外部工具
        raise NotImplementedError("ATIH备份还原需要使用Acronis True Image工具")

    def get_partition_info(self, path):
        """
        获取分区信息，包括是否为GPT分区
        :param path: 路径
        :return: 分区信息字典
        """
        # 注意：完整的分区信息获取需要使用系统API
        # 这里仅提供框架，实际使用时需要调用相应的API
        return {
            'is_gpt': True,
            'sector_size': 4096,  # 假设为4K扇区
            'align_4k': True
        }

    def align_to_4k(self, file_path):
        """
        对文件进行4K对齐处理
        :param file_path: 文件路径
        :return: 处理结果
        """
        # 注意：完整的4K对齐处理需要底层系统支持
        # 这里仅提供框架，实际使用时需要相应的实现
        pass

    def restore(self, backup_file, restore_path, callback=None, max_workers=4):
        """
        还原备份
        :param backup_file: 备份文件或目录路径
        :param restore_path: 还原目标路径
        :param callback: 进度回调函数，接收当前进度百分比
        :param max_workers: 最大工作线程数
        :return: 还原结果
        """
        try:
            if not os.path.exists(backup_file):
                raise Exception(f"备份文件不存在: {backup_file}")

            # 创建还原路径目录
            create_dir(restore_path)

            # 检测备份格式
            backup_format = self.detect_backup_format(backup_file)

            if backup_format == 'zip':
                # 解压缩还原（多线程）
                unzip_file(backup_file, restore_path, max_workers=max_workers, callback=callback)
            elif backup_format == 'ghost':
                # Ghost备份还原
                self.restore_from_ghost(backup_file, restore_path, callback)
            elif backup_format == 'atih':
                # ATIH备份还原
                self.restore_from_atih(backup_file, restore_path, callback)
            elif backup_format == 'directory':
                # 直接复制还原（多线程）
                # 找到备份目录中的实际内容
                backup_contents = os.listdir(backup_file)
                if backup_contents:
                    source_content = os.path.join(backup_file, backup_contents[0])
                    if os.path.isdir(source_content):
                        # 复制目录内容
                        total_items = len(os.listdir(source_content))
                        processed_items = 0
                        
                        for item in os.listdir(source_content):
                            s = os.path.join(source_content, item)
                            d = os.path.join(restore_path, item)
                            if os.path.isdir(s):
                                # 多线程复制目录
                                def dir_callback(progress):
                                    if callback:
                                        item_progress = int((processed_items + progress/100) / total_items * 100)
                                        callback(item_progress)
                                
                                copy_directory(s, d, max_workers=max_workers, callback=dir_callback)
                            else:
                                # 复制单个文件
                                shutil.copy2(s, d)
                                if callback:
                                    processed_items += 1
                                    item_progress = int(processed_items / total_items * 100)
                                    callback(item_progress)
                        if callback:
                            callback(100)
                else:
                    if callback:
                        callback(100)
            else:
                # 尝试通用还原方法
                raise Exception(f"不支持的备份格式: {backup_format}")
            return True
        except Exception as e:
            if callback:
                callback(-1, str(e))
            raise
