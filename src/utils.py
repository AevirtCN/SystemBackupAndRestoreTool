import os
import shutil
import zipfile
import datetime

# 获取当前时间戳，用于备份文件名
def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# 创建目录（如果不存在）
def create_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# 压缩文件和目录
def zip_directory(source_dir, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(source_dir))
                zipf.write(file_path, arcname)

# 解压缩文件
def unzip_file(zip_path, extract_dir):
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        zipf.extractall(extract_dir)

# 复制文件和目录
def copy_directory(source_dir, dest_dir):
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    shutil.copytree(source_dir, dest_dir)

# 获取文件大小
def get_file_size(file_path):
    if os.path.isfile(file_path):
        return os.path.getsize(file_path)
    elif os.path.isdir(file_path):
        total_size = 0
        for root, _, files in os.walk(file_path):
            for file in files:
                total_size += os.path.getsize(os.path.join(root, file))
        return total_size
    return 0

# 格式化文件大小
def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"
