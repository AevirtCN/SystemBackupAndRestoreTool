import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
from .backup_restore import BackupRestore
from .utils import format_size

class BackupRestoreGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("系统备份还原工具")
        self.root.geometry("600x500")
        self.root.resizable(True, True)

        self.backup_restore = BackupRestore()

        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建标签页
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 备份标签页
        self.backup_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.backup_tab, text="备份")

        # 还原标签页
        self.restore_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.restore_tab, text="还原")

        # 初始化备份标签页
        self.init_backup_tab()

        # 初始化还原标签页
        self.init_restore_tab()

    def init_backup_tab(self):
        """初始化备份标签页"""
        # 源目录选择
        source_frame = ttk.LabelFrame(self.backup_tab, text="源目录", padding="10")
        source_frame.pack(fill=tk.X, pady=10)

        self.source_var = tk.StringVar()
        source_entry = ttk.Entry(source_frame, textvariable=self.source_var, width=50)
        source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        source_button = ttk.Button(source_frame, text="浏览", command=self.select_source_dir)
        source_button.pack(side=tk.RIGHT)

        # 备份路径选择
        backup_frame = ttk.LabelFrame(self.backup_tab, text="备份路径", padding="10")
        backup_frame.pack(fill=tk.X, pady=10)

        self.backup_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop", "backups"))
        backup_entry = ttk.Entry(backup_frame, textvariable=self.backup_var, width=50)
        backup_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        backup_button = ttk.Button(backup_frame, text="浏览", command=self.select_backup_dir)
        backup_button.pack(side=tk.RIGHT)

        # 压缩选项
        compress_frame = ttk.LabelFrame(self.backup_tab, text="备份选项", padding="10")
        compress_frame.pack(fill=tk.X, pady=10)

        self.compress_var = tk.BooleanVar(value=True)
        compress_check = ttk.Checkbutton(compress_frame, text="压缩备份", variable=self.compress_var)
        compress_check.pack(anchor=tk.W)

        # 备份按钮
        button_frame = ttk.Frame(self.backup_tab)
        button_frame.pack(fill=tk.X, pady=10)

        self.backup_button = ttk.Button(button_frame, text="开始备份", command=self.start_backup)
        self.backup_button.pack(side=tk.LEFT, padx=(0, 10))

        self.cancel_backup_button = ttk.Button(button_frame, text="取消", command=self.cancel_backup, state=tk.DISABLED)
        self.cancel_backup_button.pack(side=tk.LEFT)

        # 进度条
        self.backup_progress = ttk.Progressbar(self.backup_tab, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.backup_progress.pack(fill=tk.X, pady=10)

        # 状态信息
        self.backup_status = tk.StringVar(value="就绪")
        status_label = ttk.Label(self.backup_tab, textvariable=self.backup_status)
        status_label.pack(anchor=tk.W, pady=5)

        # 备份线程
        self.backup_thread = None
        self.backup_cancelled = False

    def init_restore_tab(self):
        """初始化还原标签页"""
        # 备份文件选择
        backup_file_frame = ttk.LabelFrame(self.restore_tab, text="备份文件", padding="10")
        backup_file_frame.pack(fill=tk.X, pady=10)

        self.restore_file_var = tk.StringVar()
        backup_file_entry = ttk.Entry(backup_file_frame, textvariable=self.restore_file_var, width=50)
        backup_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        backup_file_button = ttk.Button(backup_file_frame, text="浏览", command=self.select_restore_file)
        backup_file_button.pack(side=tk.RIGHT)

        # 还原路径选择
        restore_frame = ttk.LabelFrame(self.restore_tab, text="还原路径", padding="10")
        restore_frame.pack(fill=tk.X, pady=10)

        self.restore_path_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop", "restore"))
        restore_entry = ttk.Entry(restore_frame, textvariable=self.restore_path_var, width=50)
        restore_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        restore_button = ttk.Button(restore_frame, text="浏览", command=self.select_restore_dir)
        restore_button.pack(side=tk.RIGHT)

        # 还原按钮
        button_frame = ttk.Frame(self.restore_tab)
        button_frame.pack(fill=tk.X, pady=10)

        self.restore_button = ttk.Button(button_frame, text="开始还原", command=self.start_restore)
        self.restore_button.pack(side=tk.LEFT, padx=(0, 10))

        self.cancel_restore_button = ttk.Button(button_frame, text="取消", command=self.cancel_restore, state=tk.DISABLED)
        self.cancel_restore_button.pack(side=tk.LEFT)

        # 进度条
        self.restore_progress = ttk.Progressbar(self.restore_tab, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.restore_progress.pack(fill=tk.X, pady=10)

        # 状态信息
        self.restore_status = tk.StringVar(value="就绪")
        status_label = ttk.Label(self.restore_tab, textvariable=self.restore_status)
        status_label.pack(anchor=tk.W, pady=5)

        # 还原线程
        self.restore_thread = None
        self.restore_cancelled = False

    def select_source_dir(self):
        """选择源目录"""
        directory = filedialog.askdirectory(title="选择要备份的目录")
        if directory:
            self.source_var.set(directory)

    def select_backup_dir(self):
        """选择备份路径"""
        directory = filedialog.askdirectory(title="选择备份保存路径")
        if directory:
            self.backup_var.set(directory)

    def select_restore_file(self):
        """选择备份文件"""
        filetypes = [
            ("备份文件", "*.zip"),
            ("所有文件", "*.*")
        ]
        file_path = filedialog.askopenfilename(title="选择备份文件", filetypes=filetypes)
        if not file_path:
            # 如果没有选择文件，尝试选择目录
            file_path = filedialog.askdirectory(title="选择备份目录")
        if file_path:
            self.restore_file_var.set(file_path)

    def select_restore_dir(self):
        """选择还原路径"""
        directory = filedialog.askdirectory(title="选择还原目标路径")
        if directory:
            self.restore_path_var.set(directory)

    def start_backup(self):
        """开始备份"""
        source_dir = self.source_var.get()
        backup_path = self.backup_var.get()

        if not source_dir:
            messagebox.showerror("错误", "请选择源目录")
            return

        if not backup_path:
            messagebox.showerror("错误", "请选择备份路径")
            return

        # 禁用按钮
        self.backup_button.config(state=tk.DISABLED)
        self.cancel_backup_button.config(state=tk.NORMAL)
        self.backup_status.set("正在备份...")
        self.backup_progress['value'] = 0

        # 重置取消标志
        self.backup_cancelled = False

        # 启动备份线程
        self.backup_thread = threading.Thread(target=self.run_backup, args=(source_dir, backup_path))
        self.backup_thread.daemon = True
        self.backup_thread.start()

        # 检查线程状态
        self.root.after(100, self.check_backup_thread)

    def run_backup(self, source_dir, backup_path):
        """运行备份任务"""
        try:
            def callback(progress, error=None):
                if self.backup_cancelled:
                    raise Exception("备份已取消")
                if progress == -1:
                    self.backup_status.set(f"错误: {error}")
                    self.backup_progress['value'] = 0
                else:
                    self.backup_progress['value'] = progress
                    self.backup_status.set(f"备份进度: {progress}%")

            result = self.backup_restore.backup(
                source_dir=source_dir,
                backup_path=backup_path,
                compress=self.compress_var.get(),
                callback=callback
            )

            if not self.backup_cancelled:
                backup_size = format_size(os.path.getsize(result) if os.path.isfile(result) else 0)
                self.backup_status.set(f"备份完成！备份文件: {result} (大小: {backup_size})")
                messagebox.showinfo("成功", f"备份完成！\n备份文件: {result}")
        except Exception as e:
            if not self.backup_cancelled:
                self.backup_status.set(f"错误: {str(e)}")
                messagebox.showerror("错误", f"备份失败: {str(e)}")

    def check_backup_thread(self):
        """检查备份线程状态"""
        if self.backup_thread and self.backup_thread.is_alive():
            self.root.after(100, self.check_backup_thread)
        else:
            # 恢复按钮状态
            self.backup_button.config(state=tk.NORMAL)
            self.cancel_backup_button.config(state=tk.DISABLED)

    def cancel_backup(self):
        """取消备份"""
        self.backup_cancelled = True
        self.backup_status.set("正在取消备份...")

    def start_restore(self):
        """开始还原"""
        backup_file = self.restore_file_var.get()
        restore_path = self.restore_path_var.get()

        if not backup_file:
            messagebox.showerror("错误", "请选择备份文件")
            return

        if not restore_path:
            messagebox.showerror("错误", "请选择还原路径")
            return

        # 禁用按钮
        self.restore_button.config(state=tk.DISABLED)
        self.cancel_restore_button.config(state=tk.NORMAL)
        self.restore_status.set("正在还原...")
        self.restore_progress['value'] = 0

        # 重置取消标志
        self.restore_cancelled = False

        # 启动还原线程
        self.restore_thread = threading.Thread(target=self.run_restore, args=(backup_file, restore_path))
        self.restore_thread.daemon = True
        self.restore_thread.start()

        # 检查线程状态
        self.root.after(100, self.check_restore_thread)

    def run_restore(self, backup_file, restore_path):
        """运行还原任务"""
        try:
            def callback(progress, error=None):
                if self.restore_cancelled:
                    raise Exception("还原已取消")
                if progress == -1:
                    self.restore_status.set(f"错误: {error}")
                    self.restore_progress['value'] = 0
                else:
                    self.restore_progress['value'] = progress
                    self.restore_status.set(f"还原进度: {progress}%")

            result = self.backup_restore.restore(
                backup_file=backup_file,
                restore_path=restore_path,
                callback=callback
            )

            if not self.restore_cancelled:
                self.restore_status.set(f"还原完成！还原路径: {restore_path}")
                messagebox.showinfo("成功", f"还原完成！\n还原路径: {restore_path}")
        except Exception as e:
            if not self.restore_cancelled:
                self.restore_status.set(f"错误: {str(e)}")
                messagebox.showerror("错误", f"还原失败: {str(e)}")

    def check_restore_thread(self):
        """检查还原线程状态"""
        if self.restore_thread and self.restore_thread.is_alive():
            self.root.after(100, self.check_restore_thread)
        else:
            # 恢复按钮状态
            self.restore_button.config(state=tk.NORMAL)
            self.cancel_restore_button.config(state=tk.DISABLED)

    def cancel_restore(self):
        """取消还原"""
        self.restore_cancelled = True
        self.restore_status.set("正在取消还原...")
