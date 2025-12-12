# -*- coding: utf-8 -*-
"""
@Description :  脚本： 文件去重工具（GUI版本）
@Author : sundi
@Created  : 2025/1/15
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import threading
import hashlib
from collections import defaultdict


def calculate_md5(file_path):
    """计算文件的MD5值"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        return None


def scan_files(directory):
    """扫描目录下所有文件并计算MD5"""
    file_dict = defaultdict(list)
    total_files = 0
    processed_files = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            total_files += 1
            file_path = os.path.join(root, file)
            try:
                md5_hash = calculate_md5(file_path)
                if md5_hash:
                    file_dict[md5_hash].append(file_path)
                processed_files += 1
            except Exception as e:
                continue
    
    # 找出重复的文件（MD5相同的文件组，且数量大于1）
    duplicates = {md5: paths for md5, paths in file_dict.items() if len(paths) > 1}
    
    return duplicates, total_files, processed_files


class FileDeduplicator:
    def __init__(self, root):
        self.root = root
        self.root.title("文件去重工具")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # 存储扫描结果
        self.duplicates = {}  # {md5: [file_paths]}
        self.duplicate_items = []  # 存储所有重复文件项 [(md5, file_path, group_index), ...]
        self.keep_files = {}  # {md5: keep_file_path} 每个重复组保留的文件
        
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
            text="文件去重工具",
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
            text="通过MD5对比快速查找并删除重复文件",
            font=('微软雅黑', 10),
            bootstyle=SECONDARY
        )
        subtitle_label.pack(pady=(8, 0))

        # 文件夹选择框架
        folder_frame = ttk.Labelframe(
            main_frame,
            text="📁 选择文件夹",
            padding=20,
            bootstyle=INFO
        )
        folder_frame.pack(fill=tk.X, pady=(0, 20))

        folder_input_frame = ttk.Frame(folder_frame)
        folder_input_frame.pack(fill=tk.X)
        folder_input_frame.grid_columnconfigure(0, weight=1)

        self.folder_entry = ttk.Entry(folder_input_frame, font=('微软雅黑', 10))
        self.folder_entry.grid(row=0, column=0, sticky=tk.W + tk.E, padx=(0, 10))

        browse_button = ttk.Button(
            folder_input_frame,
            text="📂 浏览",
            command=self.select_folder,
            bootstyle=OUTLINE,
            width=14
        )
        browse_button.grid(row=0, column=1, sticky=tk.W)

        scan_button = ttk.Button(
            folder_frame,
            text="🔍 开始扫描",
            command=self.start_scan,
            bootstyle=PRIMARY,
            width=20
        )
        scan_button.pack(pady=(15, 0))

        # 重复文件列表框架
        list_frame = ttk.Labelframe(
            main_frame,
            text="📋 重复文件列表",
            padding=20,
            bootstyle=INFO
        )
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # 工具栏（全选/取消全选）
        toolbar_frame = ttk.Frame(list_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        self.select_all_button = ttk.Button(
            toolbar_frame,
            text="✅ 全选",
            command=self.select_all,
            bootstyle=OUTLINE,
            width=12
        )
        self.select_all_button.pack(side=tk.LEFT, padx=(0, 10))

        self.deselect_all_button = ttk.Button(
            toolbar_frame,
            text="❌ 取消全选",
            command=self.deselect_all,
            bootstyle=OUTLINE,
            width=12
        )
        self.deselect_all_button.pack(side=tk.LEFT)

        # 统计信息
        self.stats_label = ttk.Label(
            toolbar_frame,
            text="",
            font=('微软雅黑', 10),
            bootstyle=SECONDARY
        )
        self.stats_label.pack(side=tk.RIGHT)

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
            columns=("file_path", "file_size", "group"),
            show="tree headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            selectmode="extended"
        )

        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        # 配置列
        self.tree.heading("#0", text="选择")
        self.tree.heading("file_path", text="文件路径")
        self.tree.heading("file_size", text="文件大小")
        self.tree.heading("group", text="重复组")

        self.tree.column("#0", width=50, anchor=tk.CENTER)
        self.tree.column("file_path", width=500, anchor=tk.W)
        self.tree.column("file_size", width=100, anchor=tk.E)
        self.tree.column("group", width=80, anchor=tk.CENTER)

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

        self.delete_button = ttk.Button(
            button_frame,
            text="🗑️ 删除选中文件",
            command=self.start_delete,
            bootstyle=DANGER,
            width=30,
            state=tk.DISABLED
        )
        self.delete_button.pack(pady=5)

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
            text="文件去重工具",
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

    def select_folder(self):
        """选择文件夹"""
        folder = filedialog.askdirectory(title="选择要扫描的文件夹")
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)

    def format_file_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def update_treeview(self):
        """更新Treeview显示重复文件（使用折叠的父子节点结构）"""
        # 清空现有内容
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.checkbox_vars.clear()
        self.duplicate_items.clear()
        self.keep_files.clear()

        # 填充数据
        group_index = 1
        for md5_hash, file_paths in self.duplicates.items():
            # 为每个重复组选择保留文件（按路径排序，选择最短的）
            sorted_paths = sorted(file_paths, key=lambda x: (len(x), x))
            keep_file = sorted_paths[0]
            self.keep_files[md5_hash] = keep_file
            
            # 其他重复文件
            duplicate_files = [p for p in sorted_paths if p != keep_file]
            
            # 获取保留文件信息
            try:
                keep_file_size = os.path.getsize(keep_file)
                keep_file_size_str = self.format_file_size(keep_file_size)
            except:
                keep_file_size_str = "未知"
            
            # 创建父节点（保留文件，不可勾选）
            parent_id = self.tree.insert(
                "",
                tk.END,
                text="📁",  # 使用文件夹图标表示父节点
                values=(f"🔒 {keep_file}", keep_file_size_str, f"组{group_index} [保留]"),
                tags=("keep_file", md5_hash)
            )
            
            # 创建子节点（其他重复文件，可勾选）
            for file_path in duplicate_files:
                try:
                    file_size = os.path.getsize(file_path)
                    file_size_str = self.format_file_size(file_size)
                except:
                    file_size_str = "未知"

                # 创建复选框变量
                var = tk.BooleanVar()
                self.checkbox_vars[file_path] = var

                # 插入子节点
                child_id = self.tree.insert(
                    parent_id,
                    tk.END,
                    text="☐",
                    values=(file_path, file_size_str, ""),
                    tags=("duplicate_file", file_path, md5_hash)
                )

                # 绑定复选框点击事件（使用默认参数避免闭包问题）
                def make_toggle_handler(item, path):
                    return lambda e: self.toggle_checkbox(e, item, path)
                
                self.tree.tag_bind(
                    file_path,
                    "<Button-1>",
                    make_toggle_handler(child_id, file_path)
                )

                self.duplicate_items.append((md5_hash, file_path, group_index))

            # 展开父节点（默认展开）
            self.tree.item(parent_id, open=True)
            
            group_index += 1

        # 更新统计信息
        total_duplicates = sum(len(paths) for paths in self.duplicates.values())
        duplicate_groups = len(self.duplicates)
        self.stats_label.config(
            text=f"共找到 {duplicate_groups} 组重复文件，共 {total_duplicates} 个文件"
        )

    def toggle_checkbox(self, event, item_id, file_path):
        """切换复选框状态（仅对子节点有效）"""
        # 检查是否是保留文件（父节点），如果是则不允许勾选
        tags = self.tree.item(item_id)["tags"]
        if tags and "keep_file" in tags:
            return  # 保留文件不可勾选
        
        # 允许点击整行切换复选框
        var = self.checkbox_vars.get(file_path)
        if var:
            var.set(not var.get())
            self.tree.item(item_id, text="☑" if var.get() else "☐")

    def select_all(self):
        """全选（仅选择可删除的重复文件，跳过保留文件）"""
        def select_children(parent_id):
            """递归选择所有子节点"""
            for item_id in self.tree.get_children(parent_id):
                tags = self.tree.item(item_id)["tags"]
                if tags and "duplicate_file" in tags:
                    file_path = tags[1] if len(tags) > 1 else None
                    if file_path and file_path in self.checkbox_vars:
                        var = self.checkbox_vars[file_path]
                        var.set(True)
                        self.tree.item(item_id, text="☑")
                # 递归处理子节点
                select_children(item_id)
        
        # 遍历所有父节点
        for parent_id in self.tree.get_children():
            select_children(parent_id)

    def deselect_all(self):
        """取消全选（仅取消可删除的重复文件）"""
        def deselect_children(parent_id):
            """递归取消选择所有子节点"""
            for item_id in self.tree.get_children(parent_id):
                tags = self.tree.item(item_id)["tags"]
                if tags and "duplicate_file" in tags:
                    file_path = tags[1] if len(tags) > 1 else None
                    if file_path and file_path in self.checkbox_vars:
                        var = self.checkbox_vars[file_path]
                        var.set(False)
                        self.tree.item(item_id, text="☐")
                # 递归处理子节点
                deselect_children(item_id)
        
        # 遍历所有父节点
        for parent_id in self.tree.get_children():
            deselect_children(parent_id)

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

    def scan_files(self):
        """扫描文件（在后台线程中执行）"""
        try:
            folder_path = self.folder_entry.get().strip()
            if not folder_path:
                messagebox.showerror("错误", "请选择要扫描的文件夹")
                self.update_status("就绪", "green")
                return

            if not os.path.exists(folder_path):
                messagebox.showerror("错误", "文件夹路径不存在")
                self.update_status("就绪", "green")
                return

            self.update_status("正在扫描文件并计算MD5...", "blue")
            duplicates, total_files, processed_files = scan_files(folder_path)

            self.duplicates = duplicates

            # 在主线程中更新UI
            self.root.after(0, self.update_treeview)
            
            if duplicates:
                duplicate_count = sum(len(paths) for paths in duplicates.values())
                self.root.after(0, lambda: self.update_status(
                    f"扫描完成！找到 {len(duplicates)} 组重复文件，共 {duplicate_count} 个文件", "green"
                ))
                self.root.after(0, lambda: self.delete_button.config(state=tk.NORMAL))
            else:
                self.root.after(0, lambda: self.update_status("扫描完成！未找到重复文件", "green"))
                self.root.after(0, lambda: self.delete_button.config(state=tk.DISABLED))

        except Exception as e:
            self.root.after(0, lambda: self.update_status("扫描失败", "red"))
            self.root.after(0, lambda: messagebox.showerror("错误", f"扫描失败：\n{str(e)}"))

    def start_scan(self):
        """开始扫描（在新线程中执行）"""
        folder_path = self.folder_entry.get().strip()
        if not folder_path:
            messagebox.showerror("错误", "请选择要扫描的文件夹")
            return

        if not os.path.exists(folder_path):
            messagebox.showerror("错误", "文件夹路径不存在")
            return

        # 清空之前的结果
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.checkbox_vars.clear()
        self.duplicate_items.clear()
        self.duplicates = {}
        self.keep_files.clear()
        self.delete_button.config(state=tk.DISABLED)
        self.stats_label.config(text="")

        # 在新线程中执行，避免界面卡顿
        thread = threading.Thread(target=self.scan_files, daemon=True)
        thread.start()

    def delete_files(self):
        """删除选中的文件（在后台线程中执行）"""
        try:
            # 获取选中的文件（仅从子节点获取，排除保留文件）
            selected_files = []
            
            def collect_selected(parent_id):
                """递归收集选中的文件"""
                for item_id in self.tree.get_children(parent_id):
                    tags = self.tree.item(item_id)["tags"]
                    if tags and "duplicate_file" in tags:
                        # 这是可删除的重复文件
                        file_path = tags[1] if len(tags) > 1 else None
                        if file_path and file_path in self.checkbox_vars:
                            var = self.checkbox_vars[file_path]
                            if var.get():
                                selected_files.append(file_path)
                    # 递归处理子节点
                    collect_selected(item_id)
            
            # 遍历所有父节点
            for parent_id in self.tree.get_children():
                collect_selected(parent_id)

            if not selected_files:
                messagebox.showwarning("警告", "请先选择要删除的文件")
                self.update_status("就绪", "green")
                self.delete_button.config(state=tk.NORMAL, text="🗑️ 删除选中文件")
                return

            # 确认删除
            result = messagebox.askyesno(
                "确认删除",
                f"确定要删除选中的 {len(selected_files)} 个文件吗？\n\n此操作不可恢复！",
                icon="warning"
            )

            if not result:
                self.update_status("已取消删除", "green")
                self.delete_button.config(state=tk.NORMAL, text="🗑️ 删除选中文件")
                return

            # 执行删除
            self.update_status(f"正在删除 {len(selected_files)} 个文件...", "blue")
            deleted_count = 0
            failed_count = 0
            failed_files = []

            for file_path in selected_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        deleted_count += 1
                    else:
                        failed_count += 1
                        failed_files.append(file_path)
                except Exception as e:
                    failed_count += 1
                    failed_files.append(f"{file_path} ({str(e)})")

            # 在主线程中更新UI
            if failed_count == 0:
                self.root.after(0, lambda: self.update_status(
                    f"删除完成！成功删除 {deleted_count} 个文件", "green"
                ))
                self.root.after(0, lambda: messagebox.showinfo(
                    "成功",
                    f"✨ 删除完成！\n\n成功删除 {deleted_count} 个文件"
                ))
            else:
                self.root.after(0, lambda: self.update_status(
                    f"删除完成！成功 {deleted_count} 个，失败 {failed_count} 个", "red"
                ))
                failed_msg = "\n".join(failed_files[:10])
                if len(failed_files) > 10:
                    failed_msg += f"\n... 还有 {len(failed_files) - 10} 个文件删除失败"
                self.root.after(0, lambda: messagebox.showwarning(
                    "部分失败",
                    f"删除完成！\n\n成功删除 {deleted_count} 个文件\n失败 {failed_count} 个文件：\n{failed_msg}"
                ))

            # 重新扫描或更新列表
            self.root.after(0, self.refresh_after_delete)

        except Exception as e:
            self.root.after(0, lambda: self.update_status("删除失败", "red"))
            self.root.after(0, lambda: messagebox.showerror("错误", f"删除失败：\n{str(e)}"))
        finally:
            self.root.after(0, lambda: self.delete_button.config(state=tk.NORMAL, text="🗑️ 删除选中文件"))

    def refresh_after_delete(self):
        """删除后刷新列表"""
        # 移除已删除的文件
        new_duplicates = {}
        for md5_hash, file_paths in self.duplicates.items():
            existing_paths = [path for path in file_paths if os.path.exists(path)]
            if len(existing_paths) > 1:  # 如果还有重复的
                new_duplicates[md5_hash] = existing_paths

        self.duplicates = new_duplicates
        self.update_treeview()

        if not self.duplicates:
            self.delete_button.config(state=tk.DISABLED)
            self.update_status("所有重复文件已清理完成！", "green")

    def start_delete(self):
        """开始删除（在新线程中执行）"""
        # 检查是否有选中的文件（仅检查子节点）
        has_selected = False
        
        def check_selected(parent_id):
            """递归检查是否有选中的文件"""
            nonlocal has_selected
            if has_selected:
                return
            for item_id in self.tree.get_children(parent_id):
                tags = self.tree.item(item_id)["tags"]
                if tags and "duplicate_file" in tags:
                    file_path = tags[1] if len(tags) > 1 else None
                    if file_path and file_path in self.checkbox_vars:
                        var = self.checkbox_vars[file_path]
                        if var.get():
                            has_selected = True
                            return
                check_selected(item_id)
        
        # 遍历所有父节点
        for parent_id in self.tree.get_children():
            check_selected(parent_id)
            if has_selected:
                break

        if not has_selected:
            messagebox.showwarning("警告", "请先选择要删除的文件")
            return

        self.delete_button.config(state=tk.DISABLED, text="⏳ 正在删除...")

        # 在新线程中执行，避免界面卡顿
        thread = threading.Thread(target=self.delete_files, daemon=True)
        thread.start()


if __name__ == "__main__":
    # 使用 ttkbootstrap 创建窗口，应用现代化主题
    root = ttk.Window(themename="cosmo")  # 可选主题: cosmo, flatly, litera, minty, pulse, sandstone, united, yeti
    app = FileDeduplicator(root)
    root.mainloop()

