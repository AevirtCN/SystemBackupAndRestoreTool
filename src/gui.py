import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import json
from .backup_restore import BackupRestore
from .utils import format_size
from . import __version__

class BackupRestoreGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"系统备份还原工具 - V{__version__}")
        self.root.geometry("700x550")
        self.root.resizable(True, True)
        # 设置窗口图标（如果有）
        # self.root.iconbitmap("icon.ico")

        self.backup_restore = BackupRestore()

        # 设置主题颜色
        self.style = ttk.Style()
        try:
            # 尝试使用系统主题
            self.style.theme_use('vista')
        except:
            pass
        
        # 自定义样式
        self.style.configure('TLabelFrame', padding=10, relief='ridge')
        self.style.configure('TButton', padding=5)
        self.style.configure('TProgressbar', thickness=15)

        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建标题标签
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, pady=10)
        title_label = ttk.Label(title_frame, text="系统备份还原工具", font=('微软雅黑', 16, 'bold'))
        title_label.pack(anchor=tk.CENTER)

        # 创建标签页
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # 备份标签页
        self.backup_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.backup_tab, text="备份")

        # 还原标签页
        self.restore_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.restore_tab, text="还原")

        # 设置标签页
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="设置")

        # 初始化备份标签页
        self.init_backup_tab()

        # 初始化还原标签页
        self.init_restore_tab()

        # 初始化设置标签页
        self.init_settings_tab()

        # 加载配置
        self.config_file = os.path.join(os.path.expanduser("~"), ".backup_restore_config.json")
        self.load_config()

    def init_backup_tab(self):
        """初始化备份标签页"""
        # 创建备份标签页的主框架
        backup_main_frame = ttk.Frame(self.backup_tab, padding=10)
        backup_main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 源目录选择
        source_frame = ttk.LabelFrame(backup_main_frame, text="源目录", padding=15)
        source_frame.pack(fill=tk.X, pady=10)

        self.source_var = tk.StringVar()
        source_entry = ttk.Entry(source_frame, textvariable=self.source_var, font=('微软雅黑', 10))
        source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        source_button = ttk.Button(source_frame, text="浏览", command=self.select_source_dir, width=10)
        source_button.pack(side=tk.RIGHT)

        # 备份路径选择
        backup_frame = ttk.LabelFrame(backup_main_frame, text="备份路径", padding=15)
        backup_frame.pack(fill=tk.X, pady=10)

        self.backup_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop", "backups"))
        backup_entry = ttk.Entry(backup_frame, textvariable=self.backup_var, font=('微软雅黑', 10))
        backup_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        backup_button = ttk.Button(backup_frame, text="浏览", command=self.select_backup_dir, width=10)
        backup_button.pack(side=tk.RIGHT)

        # 备份选项
        options_frame = ttk.LabelFrame(backup_main_frame, text="备份选项", padding=15)
        options_frame.pack(fill=tk.X, pady=10)

        # 压缩选项
        compress_frame = ttk.Frame(options_frame)
        compress_frame.pack(anchor=tk.W, pady=5)
        self.compress_var = tk.BooleanVar(value=True)
        compress_check = ttk.Checkbutton(compress_frame, text="压缩备份", variable=self.compress_var)
        compress_check.pack(anchor=tk.W)

        # 备份按钮
        button_frame = ttk.Frame(backup_main_frame)
        button_frame.pack(fill=tk.X, pady=15)

        # 居中按钮
        button_center_frame = ttk.Frame(button_frame)
        button_center_frame.pack(anchor=tk.CENTER)
        
        self.backup_button = ttk.Button(button_center_frame, text="开始备份", command=self.start_backup, width=15)
        self.backup_button.pack(side=tk.LEFT, padx=(0, 20))

        self.cancel_backup_button = ttk.Button(button_center_frame, text="取消", command=self.cancel_backup, state=tk.DISABLED, width=10)
        self.cancel_backup_button.pack(side=tk.LEFT)

        # 进度条
        progress_frame = ttk.LabelFrame(backup_main_frame, text="备份进度", padding=15)
        progress_frame.pack(fill=tk.X, pady=10)
        
        self.backup_progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.backup_progress.pack(fill=tk.X, pady=5)

        # 状态信息
        self.backup_status = tk.StringVar(value="就绪")
        status_label = ttk.Label(progress_frame, textvariable=self.backup_status, font=('微软雅黑', 10))
        status_label.pack(anchor=tk.W, pady=5)

        # 备份线程
        self.backup_thread = None
        self.backup_cancelled = False

    def init_restore_tab(self):
        """初始化还原标签页"""
        # 创建还原标签页的主框架
        restore_main_frame = ttk.Frame(self.restore_tab, padding=10)
        restore_main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 备份文件选择
        backup_file_frame = ttk.LabelFrame(restore_main_frame, text="备份文件", padding=15)
        backup_file_frame.pack(fill=tk.X, pady=10)

        self.restore_file_var = tk.StringVar()
        backup_file_entry = ttk.Entry(backup_file_frame, textvariable=self.restore_file_var, font=('微软雅黑', 10))
        backup_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        backup_file_button = ttk.Button(backup_file_frame, text="浏览", command=self.select_restore_file, width=10)
        backup_file_button.pack(side=tk.RIGHT)

        # 还原路径选择
        restore_frame = ttk.LabelFrame(restore_main_frame, text="还原路径", padding=15)
        restore_frame.pack(fill=tk.X, pady=10)

        self.restore_path_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop", "restore"))
        restore_entry = ttk.Entry(restore_frame, textvariable=self.restore_path_var, font=('微软雅黑', 10))
        restore_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        restore_button = ttk.Button(restore_frame, text="浏览", command=self.select_restore_dir, width=10)
        restore_button.pack(side=tk.RIGHT)

        # 还原按钮
        button_frame = ttk.Frame(restore_main_frame)
        button_frame.pack(fill=tk.X, pady=15)

        # 居中按钮
        button_center_frame = ttk.Frame(button_frame)
        button_center_frame.pack(anchor=tk.CENTER)
        
        self.restore_button = ttk.Button(button_center_frame, text="开始还原", command=self.start_restore, width=15)
        self.restore_button.pack(side=tk.LEFT, padx=(0, 20))

        self.cancel_restore_button = ttk.Button(button_center_frame, text="取消", command=self.cancel_restore, state=tk.DISABLED, width=10)
        self.cancel_restore_button.pack(side=tk.LEFT)

        # 进度条
        progress_frame = ttk.LabelFrame(restore_main_frame, text="还原进度", padding=15)
        progress_frame.pack(fill=tk.X, pady=10)
        
        self.restore_progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.restore_progress.pack(fill=tk.X, pady=5)

        # 状态信息
        self.restore_status = tk.StringVar(value="就绪")
        status_label = ttk.Label(progress_frame, textvariable=self.restore_status, font=('微软雅黑', 10))
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

    def init_settings_tab(self):
        """初始化设置标签页"""
        # 创建设置标签页的主框架
        settings_main_frame = ttk.Frame(self.settings_tab, padding=10)
        settings_main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 常规设置
        general_frame = ttk.LabelFrame(settings_main_frame, text="常规设置", padding=15)
        general_frame.pack(fill=tk.X, pady=10)
        
        # 默认备份路径设置
        backup_path_frame = ttk.Frame(general_frame)
        backup_path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(backup_path_frame, text="默认备份路径:", width=15).pack(side=tk.LEFT, padx=(0, 10))
        self.default_backup_path_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop", "backups"))
        backup_path_entry = ttk.Entry(backup_path_frame, textvariable=self.default_backup_path_var, font=('微软雅黑', 10))
        backup_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(backup_path_frame, text="浏览", command=self.select_default_backup_path, width=10).pack(side=tk.RIGHT)
        
        # 默认还原路径设置
        restore_path_frame = ttk.Frame(general_frame)
        restore_path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(restore_path_frame, text="默认还原路径:", width=15).pack(side=tk.LEFT, padx=(0, 10))
        self.default_restore_path_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop", "restore"))
        restore_path_entry = ttk.Entry(restore_path_frame, textvariable=self.default_restore_path_var, font=('微软雅黑', 10))
        restore_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(restore_path_frame, text="浏览", command=self.select_default_restore_path, width=10).pack(side=tk.RIGHT)
        
        # 默认压缩设置
        compress_frame = ttk.Frame(general_frame)
        compress_frame.pack(fill=tk.X, pady=5)
        
        self.default_compress_var = tk.BooleanVar(value=True)
        compress_check = ttk.Checkbutton(compress_frame, text="默认启用压缩备份", variable=self.default_compress_var)
        compress_check.pack(anchor=tk.W)
        
        # 关于信息
        about_frame = ttk.LabelFrame(settings_main_frame, text="关于", padding=15)
        about_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(about_frame, text="系统备份还原工具", font=('微软雅黑', 12, 'bold')).pack(anchor=tk.W, pady=5)
        ttk.Label(about_frame, text=f"版本: V{__version__}").pack(anchor=tk.W, pady=2)
        ttk.Label(about_frame, text="作者: AevirtCN").pack(anchor=tk.W, pady=2)
        ttk.Label(about_frame, text="许可证: MIT").pack(anchor=tk.W, pady=2)
        ttk.Label(about_frame, text="描述: 一个简单易用的系统备份还原工具").pack(anchor=tk.W, pady=2)
        
        # 保存按钮
        button_frame = ttk.Frame(settings_main_frame)
        button_frame.pack(fill=tk.X, pady=15)
        
        # 居中按钮
        button_center_frame = ttk.Frame(button_frame)
        button_center_frame.pack(anchor=tk.CENTER)
        
        ttk.Button(button_center_frame, text="保存设置", command=self.save_settings, width=15).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Button(button_center_frame, text="恢复默认", command=self.restore_defaults, width=15).pack(side=tk.LEFT)

    def select_default_backup_path(self):
        """选择默认备份路径"""
        directory = filedialog.askdirectory(title="选择默认备份路径")
        if directory:
            self.default_backup_path_var.set(directory)

    def select_default_restore_path(self):
        """选择默认还原路径"""
        directory = filedialog.askdirectory(title="选择默认还原路径")
        if directory:
            self.default_restore_path_var.set(directory)

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 加载默认备份路径
                if 'default_backup_path' in config:
                    self.default_backup_path_var.set(config['default_backup_path'])
                    self.backup_var.set(config['default_backup_path'])
                
                # 加载默认还原路径
                if 'default_restore_path' in config:
                    self.default_restore_path_var.set(config['default_restore_path'])
                    self.restore_path_var.set(config['default_restore_path'])
                
                # 加载默认压缩设置
                if 'default_compress' in config:
                    self.default_compress_var.set(config['default_compress'])
                    self.compress_var.set(config['default_compress'])
        except Exception as e:
            print(f"加载配置文件失败: {e}")

    def save_settings(self):
        """保存设置"""
        try:
            config = {
                'default_backup_path': self.default_backup_path_var.get(),
                'default_restore_path': self.default_restore_path_var.get(),
                'default_compress': self.default_compress_var.get()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            # 更新当前会话的设置
            self.backup_var.set(self.default_backup_path_var.get())
            self.restore_path_var.set(self.default_restore_path_var.get())
            self.compress_var.set(self.default_compress_var.get())
            
            messagebox.showinfo("成功", "设置已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存设置失败: {str(e)}")

    def restore_defaults(self):
        """恢复默认设置"""
        default_backup_path = os.path.join(os.path.expanduser("~"), "Desktop", "backups")
        default_restore_path = os.path.join(os.path.expanduser("~"), "Desktop", "restore")
        
        self.default_backup_path_var.set(default_backup_path)
        self.default_restore_path_var.set(default_restore_path)
        self.default_compress_var.set(True)
        
        messagebox.showinfo("成功", "已恢复默认设置，请点击保存设置")
