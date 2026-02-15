import os
import shutil
import zipfile
import datetime
import concurrent.futures
from functools import partial

# 获取当前时间戳，用于备份文件名
def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# 创建目录（如果不存在）
def create_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# 分段压缩大文件
def zip_large_file(zipf, file_path, arcname, chunk_size=8192*1024):
    """
    分段压缩大文件，避免一次性读取整个文件到内存
    :param zipf: ZipFile对象
    :param file_path: 源文件路径
    :param arcname: 压缩文件中的路径
    :param chunk_size: 分块大小，默认8MB
    """
    # 创建ZipInfo对象
    zinfo = zipfile.ZipInfo.from_file(file_path, arcname)
    zinfo.compress_type = zipfile.ZIP_DEFLATED
    
    # 写入文件头
    with open(file_path, 'rb') as f:
        zipf.writestr(zinfo, '')
        
        # 分段写入文件内容
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            zipf.writestr(zinfo, chunk, append=True)

# 压缩单个文件（支持大文件分段处理）
def zip_single_file(zipf, source_dir, file_path):
    arcname = os.path.relpath(file_path, os.path.dirname(source_dir))
    file_size = os.path.getsize(file_path)
    
    # 如果文件大于100MB，使用分段压缩
    if file_size > 100 * 1024 * 1024:
        zip_large_file(zipf, file_path, arcname)
    else:
        zipf.write(file_path, arcname)

# 压缩文件和目录（多线程）
def zip_directory(source_dir, output_path, max_workers=4, callback=None):
    files_to_zip = []
    # 先收集所有文件
    for root, _, files in os.walk(source_dir):
        for file in files:
            files_to_zip.append(os.path.join(root, file))
    
    total_files = len(files_to_zip)
    processed_files = 0
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 使用线程池并行压缩
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 绑定zipf和source_dir参数
            zip_func = partial(zip_single_file, zipf, source_dir)
            
            # 提交所有任务
            futures = {executor.submit(zip_func, file_path): file_path for file_path in files_to_zip}
            
            # 处理完成的任务
            for future in concurrent.futures.as_completed(futures):
                processed_files += 1
                if callback:
                    progress = int((processed_files / total_files) * 100)
                    callback(progress)

# 分段解压缩大文件
def extract_large_file(zipf, extract_dir, member, chunk_size=8192*1024):
    """
    分段解压缩大文件，避免一次性读取整个文件到内存
    :param zipf: ZipFile对象
    :param extract_dir: 解压目录
    :param member: ZipInfo对象
    :param chunk_size: 分块大小，默认8MB
    """
    # 计算目标文件路径
    target_path = os.path.join(extract_dir, member.filename)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    # 分段读取并写入
    with zipf.open(member) as zf, open(target_path, 'wb') as f:
        while True:
            chunk = zf.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)

# 解压缩单个文件（支持大文件分段处理）
def extract_single_file(zipf, extract_dir, member):
    # 如果文件大于100MB，使用分段解压缩
    if member.file_size > 100 * 1024 * 1024:
        extract_large_file(zipf, extract_dir, member)
    else:
        zipf.extract(member, extract_dir)

# 解压缩文件（多线程）
def unzip_file(zip_path, extract_dir, max_workers=4, callback=None):
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        members = zipf.infolist()
        total_members = len(members)
        processed_members = 0
        
        # 使用线程池并行解压缩
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 绑定zipf和extract_dir参数
            extract_func = partial(extract_single_file, zipf, extract_dir)
            
            # 提交所有任务
            futures = {executor.submit(extract_func, member): member for member in members}
            
            # 处理完成的任务
            for future in concurrent.futures.as_completed(futures):
                processed_members += 1
                if callback:
                    progress = int((processed_members / total_members) * 100)
                    callback(progress)

# 分段复制大文件
def copy_large_file(src, dst, chunk_size=8192*1024):
    """
    分段复制大文件，避免一次性读取整个文件到内存
    :param src: 源文件路径
    :param dst: 目标文件路径
    :param chunk_size: 分块大小，默认8MB
    """
    with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
        while True:
            chunk = fsrc.read(chunk_size)
            if not chunk:
                break
            fdst.write(chunk)

# 复制单个文件（支持大文件分段处理）
def copy_single_file(src, dst):
    file_size = os.path.getsize(src)
    # 如果文件大于100MB，使用分段复制
    if file_size > 100 * 1024 * 1024:
        copy_large_file(src, dst)
    else:
        shutil.copy2(src, dst)

# 复制文件和目录（多线程）
def copy_directory(source_dir, dest_dir, max_workers=4, callback=None):
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir)
    
    files_to_copy = []
    # 先收集所有文件
    for root, _, files in os.walk(source_dir):
        for file in files:
            src_path = os.path.join(root, file)
            rel_path = os.path.relpath(src_path, source_dir)
            dst_path = os.path.join(dest_dir, rel_path)
            # 确保目标目录存在
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            files_to_copy.append((src_path, dst_path))
    
    total_files = len(files_to_copy)
    processed_files = 0
    
    # 使用线程池并行复制
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = {executor.submit(copy_single_file, src, dst): (src, dst) for src, dst in files_to_copy}
        
        # 处理完成的任务
        for future in concurrent.futures.as_completed(futures):
            processed_files += 1
            if callback:
                progress = int((processed_files / total_files) * 100)
                callback(progress)

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
