import os
import shutil
from .utils import zip_directory, unzip_file, copy_directory, get_timestamp, create_dir

class BackupRestore:
    def __init__(self):
        pass

    def backup(self, source_dir, backup_path, compress=True, callback=None):
        """
        备份目录
        :param source_dir: 源目录路径
        :param backup_path: 备份文件或目录路径
        :param compress: 是否压缩备份
        :param callback: 进度回调函数，接收当前进度百分比
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
                # 压缩备份
                timestamp = get_timestamp()
                backup_file = os.path.join(backup_path, f"backup_{timestamp}.zip")
                create_dir(os.path.dirname(backup_file))
                zip_directory(source_dir, backup_file)
                if callback:
                    callback(100)
                return backup_file
            else:
                # 直接复制
                timestamp = get_timestamp()
                backup_dir = os.path.join(backup_path, f"backup_{timestamp}")
                copy_directory(source_dir, backup_dir)
                if callback:
                    callback(100)
                return backup_dir
        except Exception as e:
            if callback:
                callback(-1, str(e))
            raise

    def restore(self, backup_file, restore_path, callback=None):
        """
        还原备份
        :param backup_file: 备份文件或目录路径
        :param restore_path: 还原目标路径
        :param callback: 进度回调函数，接收当前进度百分比
        :return: 还原结果
        """
        try:
            if not os.path.exists(backup_file):
                raise Exception(f"备份文件不存在: {backup_file}")

            # 创建还原路径目录
            create_dir(restore_path)

            if backup_file.endswith('.zip'):
                # 解压缩还原
                unzip_file(backup_file, restore_path)
                if callback:
                    callback(100)
            else:
                # 直接复制还原
                # 找到备份目录中的实际内容
                backup_contents = os.listdir(backup_file)
                if backup_contents:
                    source_content = os.path.join(backup_file, backup_contents[0])
                    if os.path.isdir(source_content):
                        # 复制目录内容
                        for item in os.listdir(source_content):
                            s = os.path.join(source_content, item)
                            d = os.path.join(restore_path, item)
                            if os.path.isdir(s):
                                copy_directory(s, d)
                            else:
                                shutil.copy2(s, d)
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

            info = {
                'path': backup_file,
                'size': os.path.getsize(backup_file) if os.path.isfile(backup_file) else 0,
                'is_compressed': backup_file.endswith('.zip'),
                'backup_time': os.path.getmtime(backup_file)
            }
            return info
        except Exception:
            return None
