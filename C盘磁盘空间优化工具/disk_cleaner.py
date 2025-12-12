# -*- coding: utf-8 -*-
"""
@Description :  脚本： C盘磁盘空间优化工具（GUI版本）
@Author : sundi
@Created  : 2025/1/15
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import threading
import shutil


def format_file_size(size):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def get_folder_size(folder_path, progress_callback=None, stop_flag=None):
    """计算文件夹大小"""
    total_size = 0
    file_count = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            # 检查停止标志
            if stop_flag and stop_flag():
                return None
            
            # 报告当前扫描的目录
            if progress_callback:
                progress_callback(dirpath, file_count)
            
            for filename in filenames:
                # 检查停止标志
                if stop_flag and stop_flag():
                    return None
                    
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                    # 每扫描100个文件更新一次进度
                    if progress_callback and file_count % 100 == 0:
                        progress_callback(dirpath, file_count)
                except (OSError, FileNotFoundError, PermissionError):
                    continue
    except (OSError, PermissionError):
        pass
    return total_size


def scan_cleanup_targets(progress_callback=None, stop_flag=None):
    """扫描可清理的目标"""
    cleanup_items = []
    
    # 定义所有要扫描的目标路径
    scan_targets = [
        {
            'paths': [
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Temp'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
            ],
            'category': '临时文件',
            'description': 'Windows临时文件',
            'name': '临时文件'
        },
        {
            'paths': [os.path.join(os.environ.get('TEMP', ''))],
            'category': '临时文件',
            'description': '用户临时文件',
            'name': '用户临时文件'
        },
        {
            'paths': [os.path.join(drive, '$Recycle.Bin') for drive in ['C:\\', 'D:\\', 'E:\\'] if os.path.exists(drive)],
            'category': '回收站',
            'description': '回收站',
            'name': '回收站'
        },
        {
            'paths': [os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'SoftwareDistribution', 'Download')],
            'category': '系统文件',
            'description': 'Windows更新下载缓存',
            'name': 'Windows更新缓存'
        },
        {
            'paths': [
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Logs'),
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'System32', 'LogFiles'),
            ],
            'category': '日志文件',
            'description': '系统日志文件',
            'name': '日志文件'
        },
        {
            'paths': [os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Prefetch')],
            'category': '系统文件',
            'description': '系统预读文件',
            'name': 'Prefetch文件'
        },
    ]
    
    total_targets = sum(len(target['paths']) for target in scan_targets)
    current_target = 0
    
    for target_group in scan_targets:
        # 检查停止标志
        if stop_flag and stop_flag():
            break
            
        for temp_path in target_group['paths']:
            # 检查停止标志
            if stop_flag and stop_flag():
                break
                
            if temp_path and os.path.exists(temp_path):
                current_target += 1
                try:
                    # 创建文件夹扫描的内部回调
                    base_message = f"{target_group['name']}: {temp_path}"
                    
                    def folder_progress_callback(dirpath, file_count):
                        if progress_callback:
                            # 只更新当前路径，保持总进度不变
                            detail_msg = f"{base_message}\n📁 {dirpath} ({file_count} 个文件)"
                            progress_callback(detail_msg, current_target, total_targets)
                    
                    if progress_callback:
                        progress_callback(f"开始扫描 {base_message}", current_target, total_targets)
                    
                    size = get_folder_size(temp_path, folder_progress_callback if progress_callback else None, stop_flag)
                    # 如果返回None，说明被中断了
                    if size is None:
                        break
                    if size > 0:
                        cleanup_items.append({
                            'path': temp_path,
                            'type': '文件夹',
                            'size': size,
                            'category': target_group['category'],
                            'description': target_group['description']
                        })
                except Exception:
                    pass
    
    return cleanup_items


def scan_folder_contents(folder_path, max_items=1000):
    """扫描文件夹内容（限制数量以避免内存问题）"""
    items = []
    count = 0
    
    try:
        for root, dirs, files in os.walk(folder_path):
            if count >= max_items:
                break
            
            # 添加文件夹
            for dir_name in dirs:
                if count >= max_items:
                    break
                dir_path = os.path.join(root, dir_name)
                try:
                    size = get_folder_size(dir_path)
                    items.append({
                        'path': dir_path,
                        'type': '文件夹',
                        'size': size
                    })
                    count += 1
                except Exception:
                    continue
            
            # 添加文件
            for file_name in files:
                if count >= max_items:
                    break
                file_path = os.path.join(root, file_name)
                try:
                    size = os.path.getsize(file_path)
                    items.append({
                        'path': file_path,
                        'type': '文件',
                        'size': size
                    })
                    count += 1
                except Exception:
                    continue
    except Exception:
        pass
    
    return items


class DiskCleaner:
    def __init__(self, root):
        self.root = root
        self.root.title("C盘磁盘空间优化工具")
        self.root.geometry("1000x900")
        self.root.resizable(True, True)
        # 设置最小窗口大小，确保列表区域有足够空间
        self.root.minsize(1000, 850)

        # 存储扫描结果
        self.cleanup_items = []  # 可清理的项目列表
        self.selected_items = {}  # 选中的项目 {path: size}
        self.folder_contents = {}  # 文件夹内容缓存 {folder_path: [items]}
        
        # 扫描动画相关
        self.scan_animation_frames = ["🔄", "⚙️", "🔍", "📂"]
        self.scan_animation_index = 0
        self.scan_animation_running = False
        self.scan_animation_job = None
        
        # 扫描控制相关
        self.scan_stop_flag = False
        self.scan_thread = None
        
        # 设置窗口居中
        self.center_window()

        # 创建界面
        self.create_widgets()

    def center_window(self):
        """窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题区域
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 30))

        # 标题容器（包含标题和按钮，整体居中）
        title_container = ttk.Frame(title_frame)
        title_container.pack()

        title_label = ttk.Label(
            title_container,
            text="C盘磁盘空间优化工具",
            font=('微软雅黑', 20, 'bold'),
            bootstyle=PRIMARY
        )
        title_label.pack(side=tk.LEFT)

        # 信息按钮（紧靠标题）
        info_button = ttk.Button(
            title_container,
            text="ℹ️",
            command=self.show_about,
            bootstyle=OUTLINE,
            width=1
        )
        info_button.pack(side=tk.LEFT, padx=(8, 0))

        subtitle_label = ttk.Label(
            title_frame,
            text="扫描并清理C盘中的临时文件、回收站等，释放磁盘空间",
            font=('微软雅黑', 10),
            bootstyle=SECONDARY
        )
        subtitle_label.pack(pady=(8, 0))

        # 操作按钮框架
        action_frame = ttk.Labelframe(
            main_frame,
            text="🔍 扫描操作",
            padding=20,
            bootstyle=INFO
        )
        action_frame.pack(fill=tk.X, pady=(0, 20))

        # 第一行：按钮和动画图标
        button_row = ttk.Frame(action_frame)
        button_row.pack(fill=tk.X, pady=(0, 10))

        self.scan_button = ttk.Button(
            button_row,
            text="🔍 开始扫描",
            command=self.toggle_scan,
            bootstyle=PRIMARY,
            width=20
        )
        self.scan_button.pack(side=tk.LEFT, padx=(0, 10))

        # 扫描动画图标（初始隐藏）
        self.scan_icon_label = ttk.Label(
            button_row,
            text="",
            font=('微软雅黑', 14)
        )
        self.scan_icon_label.pack(side=tk.LEFT, padx=(0, 10))

        # 统计信息
        self.stats_label = ttk.Label(
            button_row,
            text="",
            font=('微软雅黑', 10),
            bootstyle=SECONDARY
        )
        self.stats_label.pack(side=tk.LEFT)

        # 第二行：进度条
        progress_frame = ttk.Frame(action_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 8))

        self.progress_label = ttk.Label(
            progress_frame,
            text="",
            font=('微软雅黑', 9),
            bootstyle=SECONDARY
        )
        self.progress_label.pack(anchor=tk.W, pady=(0, 5))

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            bootstyle=INFO,
            length=400
        )
        self.progress_bar.pack(fill=tk.X)

        # 第三行：当前扫描路径（滚动显示）
        self.current_path_label = ttk.Label(
            action_frame,
            text="",
            font=('微软雅黑', 9),
            bootstyle=INFO,
            wraplength=800,
            anchor=tk.W,
            justify=tk.LEFT
        )
        self.current_path_label.pack(fill=tk.X, anchor=tk.W)

        # 可清理项目列表框架（固定最小高度，避免被挤压）
        list_frame = ttk.Labelframe(
            main_frame,
            text="📋 可清理项目",
            padding=20,
            bootstyle=INFO
        )
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # 工具栏（全选/取消全选/查看详情）
        toolbar_frame = ttk.Frame(list_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        self.select_all_button = ttk.Button(
            toolbar_frame,
            text="✅ 全选",
            command=self.select_all,
            bootstyle=OUTLINE,
            width=12,
            state=tk.DISABLED
        )
        self.select_all_button.pack(side=tk.LEFT, padx=(0, 10))

        self.deselect_all_button = ttk.Button(
            toolbar_frame,
            text="❌ 取消全选",
            command=self.deselect_all,
            bootstyle=OUTLINE,
            width=12,
            state=tk.DISABLED
        )
        self.deselect_all_button.pack(side=tk.LEFT, padx=(0, 10))

        self.view_details_button = ttk.Button(
            toolbar_frame,
            text="👁️ 查看详情",
            command=self.view_details,
            bootstyle=OUTLINE,
            width=12,
            state=tk.DISABLED
        )
        self.view_details_button.pack(side=tk.LEFT)

        # 创建Treeview和滚动条
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # 创建滚动条
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 创建Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("category", "description", "size", "path"),
            show="tree headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            selectmode="extended"
        )

        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        # 配置列
        self.tree.heading("#0", text="选择")
        self.tree.heading("category", text="类别")
        self.tree.heading("description", text="描述")
        self.tree.heading("size", text="大小")
        self.tree.heading("path", text="路径")

        self.tree.column("#0", width=50, anchor=tk.CENTER)
        self.tree.column("category", width=100, anchor=tk.W)
        self.tree.column("description", width=200, anchor=tk.W)
        self.tree.column("size", width=120, anchor=tk.E)
        self.tree.column("path", width=400, anchor=tk.W)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 存储复选框变量
        self.checkbox_vars = {}

        # 状态显示区域
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 20))

        status_title = ttk.Label(
            status_frame,
            text="状态：",
            font=('微软雅黑', 10, 'bold')
        )
        status_title.pack(side=tk.LEFT, padx=(0, 10))

        self.status_label = ttk.Label(
            status_frame,
            text="✓ 就绪",
            font=('微软雅黑', 10),
            bootstyle=SUCCESS
        )
        self.status_label.pack(side=tk.LEFT)

        # 执行按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        self.clean_button = ttk.Button(
            button_frame,
            text="🗑️ 清理选中项目",
            command=self.start_clean,
            bootstyle=DANGER,
            width=30,
            state=tk.DISABLED
        )
        self.clean_button.pack(pady=5)

    def show_about(self):
        """显示关于信息"""
        about_window = ttk.Toplevel(self.root)
        about_window.title("关于")
        about_window.geometry("500x400")
        about_window.resizable(False, False)

        # 居中显示
        about_window.update_idletasks()
        x = (about_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (about_window.winfo_screenheight() // 2) - (400 // 2)
        about_window.geometry(f'500x400+{x}+{y}')

        # 主框架
        main_frame = ttk.Frame(about_window, padding=30)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(
            main_frame,
            text="C盘磁盘空间优化工具",
            font=('微软雅黑', 16, 'bold'),
            bootstyle=PRIMARY
        )
        title_label.pack(pady=(0, 20))

        # 作者信息
        author_label = ttk.Label(
            main_frame,
            text="作者：sundi@k1-energy.com",
            font=('微软雅黑', 12)
        )
        author_label.pack(pady=(0, 10))

        # 版本信息
        version_label = ttk.Label(
            main_frame,
            text="版本：1.0.0",
            font=('微软雅黑', 10),
            bootstyle=SECONDARY
        )
        version_label.pack(pady=(0, 20))

        # 关闭按钮
        close_button = ttk.Button(
            main_frame,
            text="确定",
            command=about_window.destroy,
            bootstyle=PRIMARY,
            width=15
        )
        close_button.pack()

        # 设置焦点
        about_window.focus_set()
        about_window.grab_set()  # 模态窗口

    def update_status(self, message, color="black"):
        """更新状态"""
        # 根据颜色选择样式和前缀
        if color == "green":
            bootstyle = SUCCESS
            prefix = "✓ "
        elif color == "blue":
            bootstyle = INFO
            prefix = "⏳ "
        elif color == "red":
            bootstyle = DANGER
            prefix = "✗ "
        else:
            bootstyle = SUCCESS
            prefix = ""

        # 更新标签样式和文本
        self.status_label.configure(bootstyle=bootstyle, text=prefix + message)
        self.root.update()

    def update_scan_progress(self, message, current, total):
        """更新扫描进度（在主线程中调用）"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar['value'] = percentage
            self.progress_label.config(text=f"扫描进度: {current}/{total} ({percentage}%)")
        
        # 处理长路径显示（如果路径太长，只显示最后部分）
        if len(message) > 100:
            display_message = "..." + message[-97:]
        else:
            display_message = message
        self.current_path_label.config(text=f"📂 {display_message}")
        self.root.update_idletasks()

    def scan_cleanup_targets(self):
        """扫描可清理目标（在后台线程中执行）"""
        try:
            self.update_status("正在扫描C盘可清理项目...", "blue")
            
            # 定义进度回调函数
            def progress_callback(message, current=0, total=0):
                if not self.scan_stop_flag:  # 只有在未停止时才更新
                    self.root.after(0, lambda: self.update_scan_progress(message, current, total))
            
            # 定义停止标志检查函数
            def stop_flag():
                return self.scan_stop_flag
            
            items = scan_cleanup_targets(progress_callback=progress_callback, stop_flag=stop_flag)
            
            # 如果被停止，不更新结果
            if self.scan_stop_flag:
                self.root.after(0, lambda: self.update_status("扫描已取消", "red"))
                self.root.after(0, lambda: self.progress_label.config(text="扫描已取消"))
                self.root.after(0, lambda: self.current_path_label.config(text=""))
                self.root.after(0, lambda: self.progress_bar.config(value=0))
                return
            
            self.cleanup_items = items
            
            # 在主线程中更新UI
            self.root.after(0, self.update_treeview)
            
            # 停止进度条动画
            self.root.after(0, lambda: self.progress_bar.config(value=100))
            self.root.after(0, lambda: self.current_path_label.config(text=""))
            
            if items:
                total_size = sum(item['size'] for item in items)
                self.root.after(0, lambda: self.update_status(
                    f"扫描完成！找到 {len(items)} 个可清理项目，可释放 {format_file_size(total_size)}", "green"
                ))
                self.root.after(0, lambda: self.select_all_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.deselect_all_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.view_details_button.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.progress_label.config(text="扫描完成！"))
            else:
                self.root.after(0, lambda: self.update_status("扫描完成！未找到可清理项目", "green"))
                self.root.after(0, lambda: self.progress_label.config(text="未找到可清理项目"))
                
        except Exception as e:
            if not self.scan_stop_flag:  # 只有在未停止时才显示错误
                self.root.after(0, lambda: self.update_status("扫描失败", "red"))
                self.root.after(0, lambda: self.progress_label.config(text="扫描失败"))
                self.root.after(0, lambda: self.current_path_label.config(text=""))
                self.root.after(0, lambda: messagebox.showerror("错误", f"扫描失败：\n{str(e)}"))
        finally:
            # 停止扫描动画
            self.root.after(0, self.stop_scan_animation)
            # 恢复按钮状态
            self.root.after(0, self.reset_scan_button)

    def start_scan_animation(self):
        """启动扫描动画"""
        self.scan_animation_running = True
        self.animate_scan_icon()

    def animate_scan_icon(self):
        """动画扫描图标"""
        if self.scan_animation_running:
            icon = self.scan_animation_frames[self.scan_animation_index]
            self.scan_icon_label.config(text=icon)
            self.scan_animation_index = (self.scan_animation_index + 1) % len(self.scan_animation_frames)
            self.scan_animation_job = self.root.after(200, self.animate_scan_icon)

    def stop_scan_animation(self):
        """停止扫描动画"""
        self.scan_animation_running = False
        if self.scan_animation_job:
            self.root.after_cancel(self.scan_animation_job)
            self.scan_animation_job = None
        self.scan_icon_label.config(text="")

    def toggle_scan(self):
        """切换扫描状态（开始/停止）"""
        if self.scan_stop_flag is False and self.scan_thread and self.scan_thread.is_alive():
            # 当前正在扫描，执行停止操作
            self.stop_scan()
        else:
            # 当前未扫描，执行开始扫描
            self.start_scan()
    
    def start_scan(self):
        """开始扫描（在新线程中执行）"""
        # 清空之前的结果
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.checkbox_vars.clear()
        self.selected_items.clear()
        self.cleanup_items = []
        self.clean_button.config(state=tk.DISABLED)
        self.select_all_button.config(state=tk.DISABLED)
        self.deselect_all_button.config(state=tk.DISABLED)
        self.view_details_button.config(state=tk.DISABLED)
        self.stats_label.config(text="")
        
        # 重置进度条
        self.progress_bar['value'] = 0
        self.progress_label.config(text="准备开始扫描...")
        self.current_path_label.config(text="")
        
        # 重置停止标志
        self.scan_stop_flag = False
        
        # 更新按钮状态
        self.scan_button.config(text="⏹️ 停止扫描", bootstyle=DANGER)

        # 启动扫描动画
        self.start_scan_animation()

        # 在新线程中执行，避免界面卡顿
        self.scan_thread = threading.Thread(target=self.scan_cleanup_targets, daemon=True)
        self.scan_thread.start()
    
    def stop_scan(self):
        """停止扫描"""
        self.scan_stop_flag = True
        self.scan_button.config(text="⏳ 正在停止...", state=tk.DISABLED)
        self.update_status("正在停止扫描...", "blue")
    
    def reset_scan_button(self):
        """重置扫描按钮状态"""
        self.scan_stop_flag = False
        self.scan_button.config(text="🔍 开始扫描", bootstyle=PRIMARY, state=tk.NORMAL)

    def update_treeview(self):
        """更新Treeview显示可清理项目"""
        # 清空现有内容
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.checkbox_vars.clear()
        self.selected_items.clear()

        # 填充数据
        total_size = 0
        for item in self.cleanup_items:
            path = item['path']
            category = item['category']
            description = item['description']
            size = item['size']
            item_type = item['type']
            
            total_size += size

            # 创建复选框变量
            var = tk.BooleanVar()
            self.checkbox_vars[path] = var

            # 插入节点
            item_id = self.tree.insert(
                "",
                tk.END,
                text="☐",
                values=(category, description, format_file_size(size), path),
                tags=(path, item_type)
            )

            # 绑定复选框点击事件
            def make_toggle_handler(item_id, path):
                return lambda e: self.toggle_checkbox(e, item_id, path)
            
            self.tree.tag_bind(
                path,
                "<Button-1>",
                make_toggle_handler(item_id, path)
            )

        # 更新统计信息
        self.stats_label.config(
            text=f"共找到 {len(self.cleanup_items)} 个可清理项目，总大小：{format_file_size(total_size)}"
        )

    def toggle_checkbox(self, event, item_id, path):
        """切换复选框状态"""
        var = self.checkbox_vars.get(path)
        if var:
            var.set(not var.get())
            is_checked = var.get()
            self.tree.item(item_id, text="☑" if is_checked else "☐")
            
            # 更新选中项目字典
            if is_checked:
                item = next((item for item in self.cleanup_items if item['path'] == path), None)
                if item:
                    self.selected_items[path] = item['size']
            else:
                self.selected_items.pop(path, None)
            
            # 更新按钮状态
            self.clean_button.config(state=tk.NORMAL if self.selected_items else tk.DISABLED)

    def select_all(self):
        """全选"""
        for path, var in self.checkbox_vars.items():
            if not var.get():
                var.set(True)
                item = next((item for item in self.cleanup_items if item['path'] == path), None)
                if item:
                    self.selected_items[path] = item['size']
        
        # 更新树视图
        for item_id in self.tree.get_children():
            path = self.tree.item(item_id)["tags"][0]
            self.tree.item(item_id, text="☑")
        
        self.clean_button.config(state=tk.NORMAL)

    def deselect_all(self):
        """取消全选"""
        for var in self.checkbox_vars.values():
            var.set(False)
        
        self.selected_items.clear()
        
        # 更新树视图
        for item_id in self.tree.get_children():
            self.tree.item(item_id, text="☐")
        
        self.clean_button.config(state=tk.DISABLED)

    def view_details(self):
        """查看选中项目的详情（显示文件夹内容）"""
        selected_paths = [path for path, var in self.checkbox_vars.items() if var.get()]
        
        if not selected_paths:
            messagebox.showwarning("警告", "请先选择要查看的项目")
            return
        
        # 创建详情窗口
        detail_window = ttk.Toplevel(self.root)
        detail_window.title("清理项目详情")
        detail_window.geometry("900x600")
        detail_window.resizable(True, True)

        # 居中显示
        detail_window.update_idletasks()
        x = (detail_window.winfo_screenwidth() // 2) - (900 // 2)
        y = (detail_window.winfo_screenheight() // 2) - (600 // 2)
        detail_window.geometry(f'900x600+{x}+{y}')

        # 主框架
        main_frame = ttk.Frame(detail_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(
            main_frame,
            text="将要删除的文件和文件夹列表",
            font=('微软雅黑', 14, 'bold'),
            bootstyle=PRIMARY
        )
        title_label.pack(pady=(0, 15))

        # Treeview和滚动条
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        detail_tree = ttk.Treeview(
            tree_frame,
            columns=("type", "size", "path"),
            show="tree headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        scrollbar_y.config(command=detail_tree.yview)
        scrollbar_x.config(command=detail_tree.xview)

        detail_tree.heading("#0", text="路径")
        detail_tree.heading("type", text="类型")
        detail_tree.heading("size", text="大小")
        detail_tree.heading("path", text="完整路径")

        detail_tree.column("#0", width=400, anchor=tk.W)
        detail_tree.column("type", width=80, anchor=tk.CENTER)
        detail_tree.column("size", width=120, anchor=tk.E)
        detail_tree.column("path", width=500, anchor=tk.W)

        detail_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 加载详情（在新线程中）
        def load_details():
            try:
                detail_window.update()
                status_label = ttk.Label(
                    main_frame,
                    text="正在加载详情...",
                    font=('微软雅黑', 10),
                    bootstyle=INFO
                )
                status_label.pack(pady=(10, 0))
                detail_window.update()

                for path in selected_paths:
                    # 添加主项目
                    item = next((item for item in self.cleanup_items if item['path'] == path), None)
                    if item:
                        parent_id = detail_tree.insert(
                            "",
                            tk.END,
                            text=os.path.basename(path) or path,
                            values=(item['type'], format_file_size(item['size']), path),
                            tags=("main_item",)
                        )
                        
                        # 如果是文件夹，加载内容
                        if os.path.isdir(path):
                            try:
                                contents = scan_folder_contents(path, max_items=500)
                                for content in contents[:500]:  # 限制显示数量
                                    detail_tree.insert(
                                        parent_id,
                                        tk.END,
                                        text=os.path.basename(content['path']),
                                        values=(content['type'], format_file_size(content['size']), content['path']),
                                        tags=("content_item",)
                                    )
                            except Exception:
                                pass
                
                status_label.destroy()
                detail_window.update()
            except Exception as e:
                status_label.config(text=f"加载失败：{str(e)}", bootstyle=DANGER)

        # 关闭按钮
        close_button = ttk.Button(
            main_frame,
            text="关闭",
            command=detail_window.destroy,
            bootstyle=PRIMARY,
            width=15
        )
        close_button.pack(pady=(15, 0))

        # 在新线程中加载详情
        thread = threading.Thread(target=load_details, daemon=True)
        thread.start()

    def clean_files(self):
        """清理选中的文件（在后台线程中执行）"""
        try:
            selected_paths = list(self.selected_items.keys())
            
            if not selected_paths:
                messagebox.showwarning("警告", "请先选择要清理的项目")
                self.update_status("就绪", "green")
                self.clean_button.config(state=tk.NORMAL, text="🗑️ 清理选中项目")
                return

            # 显示将要删除的路径列表
            detail_text = "将要删除以下项目：\n\n"
            total_size = sum(self.selected_items.values())
            for i, path in enumerate(selected_paths, 1):
                detail_text += f"{i}. {path}\n"
            detail_text += f"\n总大小：{format_file_size(total_size)}\n"
            detail_text += "\n此操作不可恢复！确定要继续吗？"

            result = messagebox.askyesno(
                "确认清理",
                detail_text,
                icon="warning"
            )

            if not result:
                self.update_status("已取消清理", "green")
                self.clean_button.config(state=tk.NORMAL, text="🗑️ 清理选中项目")
                return

            # 执行清理
            self.update_status(f"正在清理 {len(selected_paths)} 个项目...", "blue")
            deleted_count = 0
            failed_count = 0
            freed_size = 0
            failed_files = []

            for path in selected_paths:
                try:
                    if os.path.exists(path):
                        if os.path.isdir(path):
                            shutil.rmtree(path, ignore_errors=True)
                        else:
                            os.remove(path)
                        deleted_count += 1
                        freed_size += self.selected_items[path]
                    else:
                        failed_count += 1
                        failed_files.append(f"{path} (文件不存在)")
                except PermissionError:
                    failed_count += 1
                    failed_files.append(f"{path} (权限不足)")
                except Exception as e:
                    failed_count += 1
                    failed_files.append(f"{path} ({str(e)})")

            # 在主线程中更新UI
            if failed_count == 0:
                self.root.after(0, lambda: self.update_status(
                    f"清理完成！成功清理 {deleted_count} 个项目，释放 {format_file_size(freed_size)}", "green"
                ))
                self.root.after(0, lambda: messagebox.showinfo(
                    "成功",
                    f"✨ 清理完成！\n\n成功清理 {deleted_count} 个项目\n释放空间：{format_file_size(freed_size)}"
                ))
            else:
                self.root.after(0, lambda: self.update_status(
                    f"清理完成！成功 {deleted_count} 个，失败 {failed_count} 个，释放 {format_file_size(freed_size)}", "red"
                ))
                failed_msg = "\n".join(failed_files[:10])
                if len(failed_files) > 10:
                    failed_msg += f"\n... 还有 {len(failed_files) - 10} 个项目清理失败"
                self.root.after(0, lambda: messagebox.showwarning(
                    "部分失败",
                    f"清理完成！\n\n成功清理 {deleted_count} 个项目\n释放空间：{format_file_size(freed_size)}\n失败 {failed_count} 个项目：\n{failed_msg}"
                ))

            # 重新扫描
            self.root.after(0, self.start_scan)

        except Exception as e:
            self.root.after(0, lambda: self.update_status("清理失败", "red"))
            self.root.after(0, lambda: messagebox.showerror("错误", f"清理失败：\n{str(e)}"))
        finally:
            self.root.after(0, lambda: self.clean_button.config(state=tk.NORMAL, text="🗑️ 清理选中项目"))

    def start_clean(self):
        """开始清理（在新线程中执行）"""
        if not self.selected_items:
            messagebox.showwarning("警告", "请先选择要清理的项目")
            return

        self.clean_button.config(state=tk.DISABLED, text="⏳ 正在清理...")

        # 在新线程中执行，避免界面卡顿
        thread = threading.Thread(target=self.clean_files, daemon=True)
        thread.start()


if __name__ == "__main__":
    # 使用 ttkbootstrap 创建窗口，应用现代化主题
    root = ttk.Window(themename="cosmo")  # 可选主题: cosmo, flatly, litera, minty, pulse, sandstone, united, yeti
    app = DiskCleaner(root)
    root.mainloop()

