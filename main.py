# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import os
import sys
import subprocess  # 新增
import winreg
import ctypes
from pathlib import Path
import datetime
from Crypto.Cipher import AES
from lib import CleanToolsCore

def is_admin():
    """检查是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def run_as_admin():
    """以管理员权限重新运行程序"""
    if is_admin():
        return True
    else:
        try:
            # 获取当前脚本的完整路径
            script_path = os.path.abspath(sys.argv[0])
            params = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else ''
            
            result = ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                f'"{script_path}" {params}', 
                None, 
                1
            )
            return result > 32  # ShellExecute 返回值大于32表示成功
        except Exception as e:
            print(f"权限提升失败: {e}")
            return False

def main():
    """主函数"""
    # 改进的管理员权限检查
    if not is_admin():
        result = messagebox.askyesno(
            "权限提示", 
            "此程序需要管理员权限才能正常运行。\n\n是否以管理员身份重新启动？"
        )
        if result:
            if run_as_admin():
                sys.exit(0)  # 成功启动管理员版本，退出当前进程
            else:
                messagebox.showerror("错误", "无法获取管理员权限，程序将以普通权限运行")
        else:
            messagebox.showwarning(
                "警告", 
                "没有管理员权限，某些功能可能无法正常使用"
            )
    
    # 创建主窗口
    root = tk.Tk()
    root.title("Clean Tools" + (" (管理员)" if is_admin() else " (普通用户)"))
    
    # 创建应用程序实例
    app = CleanToolsGUI(root)
    
    # 启动主循环
    root.mainloop()

class CleanToolsGUI:
    def __init__(self, root):
        self.root = root
        self.root.geometry("900x700")
        
        # 检查管理员权限
        self.is_admin = is_admin()
        
        # 初始化核心组件
        program_path = Path(__file__).parent
        self.core = CleanToolsCore(program_path)
        
        # 初始化变量
        self.current_rule = None
        self.rules_data = {}
        
        # 创建界面
        self.create_widgets()
        self.load_rules()
        
        # 设置图标（如果存在）
        icon_path = program_path / "icon.ico"
        if icon_path.exists():
            try:
                self.root.iconbitmap(str(icon_path))
            except:
                pass
    
    def create_widgets(self):
        """创建界面组件"""
        # 管理员状态显示
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        admin_status = "🔑 管理员模式" if self.is_admin else "⚠️ 普通用户模式"
        ttk.Label(status_frame, text=admin_status, font=("Arial", 10, "bold")).pack(side="left")
        
        # 设置按钮
        ttk.Button(status_frame, text="⚙️ 设置", command=self.open_settings).pack(side="right")
        
        # 系统管理按钮区域
        system_frame = ttk.LabelFrame(self.root, text="🔧 系统管理")
        system_frame.pack(fill="x", padx=10, pady=5)
        
        btn_frame = ttk.Frame(system_frame)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(btn_frame, text="📄 页面文件管理", command=self.open_pagefile_manager).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="💤 休眠管理", command=self.open_hibernate_manager).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📁 目录迁移", command=self.open_folder_migration).pack(side="left", padx=5)
        
        # 主内容区域
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 左侧：规则选择区域
        left_frame = ttk.LabelFrame(main_frame, text="📋 规则列表")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # 规则列表
        self.rule_listbox = tk.Listbox(left_frame)
        self.rule_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.rule_listbox.bind("<<ListboxSelect>>", self.on_rule_select)
        
        # 规则操作按钮
        rule_btn_frame = ttk.Frame(left_frame)
        rule_btn_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(rule_btn_frame, text="➕ 新建", command=self.create_new_rule).pack(side="left", padx=2)
        ttk.Button(rule_btn_frame, text="✏️ 编辑", command=self.edit_rule).pack(side="left", padx=2)
        ttk.Button(rule_btn_frame, text="🗑️ 删除", command=self.delete_rule).pack(side="left", padx=2)
        ttk.Button(rule_btn_frame, text="📥 导入", command=self.import_rule).pack(side="left", padx=2)
        
        # 右侧：规则信息显示
        right_frame = ttk.LabelFrame(main_frame, text="📄 规则信息")
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.info_text = scrolledtext.ScrolledText(right_frame, height=15)
        self.info_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 清理操作区域
        clean_frame = ttk.LabelFrame(self.root, text="🧹 清理操作")
        clean_frame.pack(fill="x", padx=10, pady=5)
        
        # 开始清理按钮
        self.clean_btn = ttk.Button(clean_frame, text="🚀 开始清理", command=self.start_clean)
        self.clean_btn.pack(pady=10)
        
        # 创建进度条区域
        self.create_progress_area()
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(self.root, text="📝 操作日志")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def create_progress_area(self):
        """创建专门的进度条区域"""
        # 进度条区域 - 使用更紧凑的布局
        self.progress_frame = ttk.LabelFrame(self.root, text="📊 操作进度")
        self.progress_frame.pack(fill="x", padx=10, pady=(5, 0))
        
        # 内容容器
        content_frame = ttk.Frame(self.progress_frame)
        content_frame.pack(fill="x", padx=8, pady=8)
        
        # 状态标签和百分比 - 同一行显示
        status_frame = ttk.Frame(content_frame)
        status_frame.pack(fill="x", pady=(0, 5))
        
        self.progress_status = ttk.Label(status_frame, text="就绪", font=("Arial", 9))
        self.progress_status.pack(side="left")
        
        self.progress_percent = ttk.Label(status_frame, text="0%", font=("Arial", 9, "bold"))
        self.progress_percent.pack(side="right")
        
        # 进度条 - 自适应宽度
        self.progress_bar = ttk.Progressbar(
            content_frame, 
            mode='determinate', 
            style="Custom.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill="x", pady=(0, 5))
        
        # 详细信息标签 - 可选显示
        self.progress_detail = ttk.Label(
            content_frame, 
            text="", 
            font=("Arial", 8), 
            foreground="gray"
        )
        self.progress_detail.pack(fill="x")
        
        # 初始化进度条样式
        self.setup_progress_style()

    def setup_progress_style(self):
        """设置进度条样式"""
        style = ttk.Style()
        
        # 自定义进度条样式
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#E0E0E0',
            background='#4CAF50',
            lightcolor='#4CAF50',
            darkcolor='#4CAF50',
            borderwidth=1,
            relief='flat'
        )

    def update_progress(self, value=0, status="就绪", detail=""):
        """更新进度条 - 统一的进度更新接口"""
        # 更新进度条值
        self.progress_bar['value'] = max(0, min(100, value))
        
        # 更新百分比显示
        self.progress_percent.config(text=f"{int(value)}%")
        
        # 更新状态文本
        self.progress_status.config(text=status)
        
        # 更新详细信息（可选）
        if detail:
            self.progress_detail.config(text=detail)
        
        # 强制更新界面
        self.root.update_idletasks()

    def reset_progress(self):
        """重置进度条"""
        self.update_progress(0, "就绪", "")

    def show_progress_error(self, message):
        """显示进度错误状态"""
        # 临时改变进度条颜色为红色
        style = ttk.Style()
        style.configure(
            "Error.Horizontal.TProgressbar",
            troughcolor='#E0E0E0',
            background='#F44336',
            lightcolor='#F44336',
            darkcolor='#F44336'
        )
        self.progress_bar.config(style="Error.Horizontal.TProgressbar")
        
        self.progress_status.config(text="❌ 错误")
        self.progress_detail.config(text=message)
        
        # 3秒后恢复正常样式
        self.root.after(3000, self.reset_progress_style)

    def show_progress_complete(self, message):
        """显示进度完成状态"""
        self.progress_bar['value'] = 100
        self.progress_percent.config(text="100%")
        self.progress_status.config(text="✅ 完成")
        self.progress_detail.config(text=message)

    def reset_progress_style(self):
        """重置进度条样式"""
        self.progress_bar.config(style="Custom.Horizontal.TProgressbar")
        self.reset_progress()
    
    def start_clean(self):
        """开始清理"""
        if not self.current_rule:
            messagebox.showwarning("警告", "请先选择一个规则")
            return
        
        try:
            # 重置进度条
            self.reset_progress()
            
            rule_info = self.rules_data[self.current_rule]
            
            # 安全检查
            self.update_progress(10, "🔍 安全检查", "验证规则完整性...")
            
            # 检查是否为加密文件且存在安全问题
            if rule_info.get('is_encrypted', False):
                if rule_info.get('is_tampered', False) or rule_info.get('cannot_verify', False):
                    self.show_progress_error("安全验证失败")
                    
                    integrity_status = rule_info.get('integrity_status', 'unknown')
                    integrity_message = rule_info.get('integrity_message', '')
                    
                    if integrity_status == 'tampered':
                        error_msg = f"安全限制: 检测到文件篡改，禁止执行清理操作！\n\n" \
                                   f"篡改详情: {integrity_message}\n\n" \
                                   f"建议: 请重新导入或创建该规则。"
                        self.log(f"[安全阻止] 检测到规则篡改: {self.current_rule} - {integrity_message}")
                        messagebox.showerror("安全错误", error_msg)
                        return
                    elif integrity_status in ['cannot_verify', 'error']:
                        error_msg = f"安全限制: 无法验证文件完整性，禁止执行清理操作！\n\n" \
                                   f"详情: {integrity_message}\n\n" \
                                   f"建议: 请重新导入或创建该规则。"
                        self.log(f"[安全阻止] 无法验证规则完整性: {self.current_rule} - {integrity_message}")
                        messagebox.showerror("安全错误", error_msg)
                        return
                else:
                    # 执行前最后一次验证
                    rule_dir = rule_info.get('rule_dir')
                    original_author = rule_info.get('Auther', 'Unknown')
                    
                    try:
                        is_valid, message = self.core.security_manager.verify_integrity(rule_dir, original_author)
                        if not is_valid:
                            self.show_progress_error("执行前检测到文件篡改")
                            error_msg = f"安全限制: 执行前检测到文件篡改！\n\n" \
                                       f"篡改详情: {message}\n\n" \
                                       f"建议: 请重新导入或创建该规则。"
                            self.log(f"[安全阻止] 执行前检测到规则篡改: {self.current_rule} - {message}")
                            messagebox.showerror("安全错误", error_msg)
                            return
                    except Exception as e:
                        self.show_progress_error("安全验证失败")
                        error_msg = f"安全限制: 安全验证失败，禁止执行清理操作！\n\n" \
                                   f"错误详情: {str(e)}\n\n" \
                                   f"建议: 请检查文件完整性或重新创建规则。"
                        self.log(f"[安全阻止] 安全验证异常: {self.current_rule} - {str(e)}")
                        messagebox.showerror("安全错误", error_msg)
                        return
            
            # 记录开始执行的日志
            self.log(f"[安全通过] 开始执行已验证的规则: {self.current_rule}")
            
            self.clean_btn.config(state="disabled")
            
            # 执行清理
            self.update_progress(40, "🧹 执行清理", f"正在执行规则: {self.current_rule}")
            
            # 执行实际清理，带进度回调
            success = self.core.execute_clean_rule(
                rule_info, 
                self.log_callback,
                self.update_progress
            )
            
            if success:
                self.show_progress_complete(f"清理完成: {self.current_rule}")
                self.log(f"清理完成: {self.current_rule}")
                messagebox.showinfo("完成", "清理操作已完成")
            else:
                self.show_progress_error("清理过程中出现错误")
                messagebox.showerror("错误", "清理过程中出现错误")
                
        except Exception as e:
            self.show_progress_error(f"清理失败: {str(e)}")
            self.log(f"清理失败: {str(e)}")
            messagebox.showerror("错误", f"清理失败: {str(e)}")
        finally:
            self.clean_btn.config(state="normal")
    
    def create_new_rule(self):
        """创建新规则"""
        dialog = RuleEditorDialog(self.root, "新建规则")
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            rule_name = dialog.result['Name']
            rule_path = self.core.save_rule(dialog.result)
            if rule_path:
                self.log(f"规则已保存到: {rule_path}")
                messagebox.showinfo("成功", f"规则 '{rule_name}' 创建成功！\n保存路径: {rule_path}")
                self.load_rules()
            else:
                messagebox.showerror("错误", "保存规则失败")
        else:
            self.log("对话框没有返回结果")
    
    def edit_rule(self):
        """编辑规则"""
        if not self.current_rule:
            messagebox.showwarning("警告", "请先选择一个规则")
            return
        
        # 检测是否为加密文件
        if self.is_encrypted_rule(self.current_rule):
            messagebox.showerror("错误", "此规则为加密文件，无法编辑！\n\n如需修改，请先删除后重新创建。")
            return
            
        rule_info = self.rules_data[self.current_rule]
        dialog = RuleEditorDialog(self.root, "编辑规则", rule_info)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            rule_path = self.core.save_rule(dialog.result)
            if rule_path:
                self.log(f"规则已更新: {rule_path}")
                messagebox.showinfo("成功", "规则更新成功！")
                self.load_rules()
            else:
                messagebox.showerror("错误", "保存规则失败")
    
    def is_encrypted_rule(self, rule_name):
        """检测规则是否为加密文件"""
        try:
            rule_dir = self.core.rule_path / rule_name.replace(' ', '_')
            
            # 检测1：是否存在 rule.integrity 文件
            integrity_file = rule_dir / "rule.integrity"
            if integrity_file.exists():
                return True
            
            # 检测2：检查info.cleantool文件内容
            info_file = rule_dir / "info.cleantool"
            if info_file.exists():
                with open(info_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'random_key' in content or '此文件为加密文件' in content:
                        return True
            
            return False
        except:
            return False
    
    def delete_rule(self):
        """删除规则"""
        if not self.current_rule:
            messagebox.showwarning("警告", "请先选择一个规则")
            return
        
        if messagebox.askyesno("确认", f"确定要删除规则 '{self.current_rule}' 吗？"):
            if self.core.delete_rule(self.current_rule):
                self.log(f"规则已删除: {self.current_rule}")
                messagebox.showinfo("成功", "规则删除成功")
                self.current_rule = None
                self.load_rules()
                self.info_text.config(state="normal")
                self.info_text.delete(1.0, tk.END)
                self.info_text.config(state="disabled")
            else:
                messagebox.showerror("错误", "删除规则失败")
    
    def import_rule(self):
        """导入规则"""
        file_path = filedialog.askopenfilename(
            title="选择规则文件",
            filetypes=[("压缩文件", "*.zip"), ("所有文件", "*.*")]
        )
        
        if file_path:
            if self.core.import_rule(file_path):
                self.log(f"规则导入成功: {file_path}")
                self.load_rules()
            else:
                self.log(f"规则导入失败: {file_path}")
    
    def on_rule_select(self, event):
        """规则选择事件"""
        selection = self.rule_listbox.curselection()
        if selection:
            self.current_rule = self.rule_listbox.get(selection[0])
            self.update_rule_info()
    
    def update_rule_info(self):
        """更新规则信息显示"""
        self.info_text.config(state="normal")
        self.info_text.delete(1.0, tk.END)
        
        if self.current_rule and self.current_rule in self.rules_data:
            rule_info = self.rules_data[self.current_rule]
            info_text = self.core.format_rule_info(rule_info)
            
            # 添加安全状态信息
            if rule_info.get('is_encrypted', False):
                info_text += "\n\n=== 安全状态 ==="
                info_text += "\n文件类型: 🔒 加密文件"
                
                integrity_status = rule_info.get('integrity_status', 'unknown')
                integrity_message = rule_info.get('integrity_message', '')
                
                if integrity_status == 'valid':
                    info_text += "\n完整性: ✅ 验证通过"
                elif integrity_status == 'tampered':
                    info_text += "\n完整性: ❌ 文件已被篡改"
                    info_text += "\n执行状态: 🚫 禁止执行"
                    info_text += f"\n详情: {integrity_message}"
                elif integrity_status == 'cannot_verify':
                    info_text += "\n完整性: ⚠️ 无法验证"
                    info_text += "\n执行状态: 🚫 禁止执行"
                    info_text += f"\n详情: {integrity_message}"
                elif integrity_status == 'error':
                    info_text += "\n完整性: ❌ 验证出错"
                    info_text += "\n执行状态: 🚫 禁止执行"
                    info_text += f"\n详情: {integrity_message}"
                else:
                    info_text += "\n完整性: ⚠️ 状态未知"
                    info_text += "\n执行状态: 🚫 禁止执行"
            else:
                info_text += "\n\n=== 安全状态 ==="
                info_text += "\n文件类型: 📄 普通文件"
                info_text += "\n执行状态: ✅ 允许执行"
            
            self.info_text.insert(1.0, info_text)
        
        self.info_text.config(state="disabled")
    
    def load_rules(self):
        """加载规则列表"""
        self.rule_listbox.delete(0, tk.END)
        self.rules_data = self.core.load_rules()
        
        for rule_name in self.rules_data.keys():
            self.rule_listbox.insert(tk.END, rule_name)
    
    def log_callback(self, message):
        """日志回调函数"""
        self.log(message)
    
    def log(self, message):
        """记录日志"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        
        # 同时写入日志文件
        self.core.write_log(log_message)
    
    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self.root)
        self.root.wait_window(dialog.dialog)
    
    def open_pagefile_manager(self):
        """打开页面文件管理器"""
        dialog = PageFileManagerDialog(self.root, self.core)
        self.root.wait_window(dialog.dialog)
    
    def open_hibernate_manager(self):
        """打开休眠管理器"""
        dialog = HibernateManagerDialog(self.root, self.core)
        self.root.wait_window(dialog.dialog)
    
    def open_folder_migration(self):
        """打开目录迁移对话框"""
        dialog = FolderMigrationDialog(self.root)
        self.root.wait_window(dialog.dialog)

class RuleEditorDialog:
    def __init__(self, parent, title, rule_info=None):
        self.result = None
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.create_widgets(rule_info)
    
    def create_widgets(self, rule_info):
        """创建对话框组件"""
        # 规则信息输入区域
        info_frame = ttk.LabelFrame(self.dialog, text="规则信息")
        info_frame.pack(fill="x", padx=10, pady=5)
        
        # 规则名称
        ttk.Label(info_frame, text="规则名称:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.name_entry = ttk.Entry(info_frame, width=50)
        self.name_entry.grid(row=0, column=1, padx=5, pady=2)
        
        # 版本
        ttk.Label(info_frame, text="版本:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.version_entry = ttk.Entry(info_frame, width=50)
        self.version_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # 作者
        ttk.Label(info_frame, text="作者:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.author_entry = ttk.Entry(info_frame, width=50)
        self.author_entry.grid(row=2, column=1, padx=5, pady=2)
        
        # 描述
        ttk.Label(info_frame, text="描述:").grid(row=3, column=0, sticky="nw", padx=5, pady=2)
        self.desc_text = tk.Text(info_frame, height=3, width=50)
        self.desc_text.grid(row=3, column=1, padx=5, pady=2)
        
        # 规则内容
        content_frame = ttk.LabelFrame(self.dialog, text="规则内容")
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.content_text = scrolledtext.ScrolledText(content_frame, height=15)
        self.content_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 加密选项
        encrypt_frame = ttk.Frame(self.dialog)
        encrypt_frame.pack(fill="x", padx=10, pady=5)
        
        self.encrypt_var = tk.BooleanVar()
        ttk.Checkbutton(encrypt_frame, text="🔒 加密保存（推荐用于重要规则）", variable=self.encrypt_var).pack(side="left")
        
        # 按钮区域
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="保存", command=self.save_rule).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="取消", command=self.cancel).pack(side="right")
        
        # 如果是编辑模式，填充现有数据
        if rule_info:
            self.name_entry.insert(0, rule_info.get('Name', ''))
            self.version_entry.insert(0, rule_info.get('version', '1.0'))
            self.author_entry.insert(0, rule_info.get('Auther', ''))
            self.desc_text.insert(1.0, rule_info.get('information', ''))
            
            # 加载规则内容
            rule_file = rule_info.get('rule_file')
            if rule_file and rule_file.exists():
                try:
                    with open(rule_file, 'r', encoding='utf-8') as f:
                        self.content_text.insert(1.0, f.read())
                except:
                    pass
    
    def save_rule(self):
        """保存规则"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("错误", "请输入规则名称")
            return
        
        version = self.version_entry.get().strip() or "1.0"
        author = self.author_entry.get().strip() or "Unknown"
        description = self.desc_text.get(1.0, tk.END).strip() or "none"
        content = self.content_text.get(1.0, tk.END).strip()
        
        if not content:
            messagebox.showerror("错误", "请输入规则内容")
            return
        
        self.result = {
            'Name': name,
            'version': version,
            'Auther': author,
            'information': description,
            'rules': content,
            'encrypted': self.encrypt_var.get()
        }
        
        self.dialog.destroy()
    
    def cancel(self):
        """取消"""
        self.dialog.destroy()

class SettingsDialog:
    """设置对话框"""
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("设置")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 设置图标
        try:
            self.dialog.iconbitmap("icon.ico")
        except:
            pass
        
        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 100))
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建设置界面组件"""
        # 设置选项区域
        options_frame = ttk.LabelFrame(self.dialog, text="设置选项")
        options_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 关于程序按钮
        ttk.Button(options_frame, text="关于程序", command=self.show_about).pack(pady=10)
        
        # 关闭按钮
        ttk.Button(self.dialog, text="关闭", command=self.dialog.destroy).pack(pady=10)
    
    def show_about(self):
        """显示关于信息"""
        about_text = "Clean Tools\n\n" \
                    "版本: 2.0\n" \
                    "一个强大的系统清理工具\n\n" \
                    "功能特性:\n" \
                    "• 规则化清理系统\n" \
                    "• 加密规则支持\n" \
                    "• 完整性验证\n" \
                    "• 页面文件管理\n" \
                    "• 休眠设置管理\n" \
                    "• 实时进度显示"
        
        messagebox.showinfo("关于 Clean Tools", about_text)

class PageFileManagerDialog:
    """页面文件管理对话框"""
    def __init__(self, parent, core):
        self.core = core
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("页面文件管理")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 100))
        
        self.create_widgets()
        self.check_current_status()  
    
    def create_widgets(self):
        """创建页面文件管理界面"""
        # 当前状态显示
        status_frame = ttk.LabelFrame(self.dialog, text="当前页面文件状态")
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=8)
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 设置区域
        setting_frame = ttk.LabelFrame(self.dialog, text="页面文件设置")
        setting_frame.pack(fill="x", padx=10, pady=5)
        
        # 驱动器选择
        ttk.Label(setting_frame, text="目标驱动器:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.drive_var = tk.StringVar(value="C")
        drive_combo = ttk.Combobox(setting_frame, textvariable=self.drive_var, values=["C", "D", "E", "F"], width=10)
        drive_combo.grid(row=0, column=1, padx=5, pady=2)
        
        # 初始大小
        ttk.Label(setting_frame, text="初始大小(MB):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.initial_var = tk.StringVar(value="1024")
        ttk.Entry(setting_frame, textvariable=self.initial_var, width=15).grid(row=1, column=1, padx=5, pady=2)
        
        # 最大大小
        ttk.Label(setting_frame, text="最大大小(MB):").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.maximum_var = tk.StringVar(value="2048")
        ttk.Entry(setting_frame, textvariable=self.maximum_var, width=15).grid(row=2, column=1, padx=5, pady=2)
        
        # 系统管理选项
        self.system_managed_var = tk.BooleanVar()
        ttk.Checkbutton(setting_frame, text="让系统管理页面文件大小", 
                       variable=self.system_managed_var, 
                       command=self.toggle_manual_settings).grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="查看当前状态", command=self.check_current_status).pack(side="left", padx=5)
        ttk.Button(button_frame, text="应用设置", command=self.apply_settings).pack(side="left", padx=5)
        ttk.Button(button_frame, text="禁用页面文件", command=self.disable_pagefile).pack(side="left", padx=5)
        ttk.Button(button_frame, text="关闭", command=self.dialog.destroy).pack(side="right", padx=5)
        
        # 初始化显示当前状态
        self.check_current_status()
    
    def toggle_manual_settings(self):
        """切换手动/自动设置"""
        if self.system_managed_var.get():
            # 禁用手动输入
            for widget in self.dialog.winfo_children():
                if isinstance(widget, ttk.LabelFrame) and widget.cget("text") == "页面文件设置":
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Entry):
                            child.config(state="disabled")
        else:
            # 启用手动输入
            for widget in self.dialog.winfo_children():
                if isinstance(widget, ttk.LabelFrame) and widget.cget("text") == "页面文件设置":
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Entry):
                            child.config(state="normal")
    
    def check_current_status(self):
        """检查当前页面文件状态"""
        try:
            # 使用PowerShell查询页面文件信息
            powershell_cmd = 'Get-WmiObject -Class Win32_PageFileUsage | Select-Object Name, AllocatedBaseSize, CurrentUsage | Format-Table -AutoSize'
            result = subprocess.run(["powershell", "-Command", powershell_cmd], 
                                  capture_output=True, text=True, shell=True)
            
            self.status_text.delete(1.0, tk.END)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    self.status_text.insert(tk.END, "当前页面文件配置:\n\n")
                    self.status_text.insert(tk.END, output)
                else:
                    self.status_text.insert(tk.END, "未找到页面文件配置信息")
            else:
                # 备用方案：使用系统信息命令
                try:
                    result2 = subprocess.run(["systeminfo"], capture_output=True, text=True, shell=True)
                    if result2.returncode == 0:
                        lines = result2.stdout.split('\n')
                        pagefile_info = [line for line in lines if '页面文件' in line or 'Page File' in line]
                        if pagefile_info:
                            self.status_text.insert(tk.END, "页面文件信息:\n\n")
                            for info in pagefile_info:
                                self.status_text.insert(tk.END, info.strip() + "\n")
                        else:
                            self.status_text.insert(tk.END, "未找到页面文件信息")
                    else:
                        self.status_text.insert(tk.END, f"查询失败: {result.stderr}")
                except:
                    self.status_text.insert(tk.END, "无法查询页面文件状态")
                
        except Exception as e:
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, f"查询页面文件状态时出错: {str(e)}")

    def apply_settings(self):
        """应用页面文件设置"""
        try:
            drive = self.drive_var.get()
            
            if self.system_managed_var.get():
                # 设置为系统管理 - 使用PowerShell
                powershell_cmd = f'$cs = Get-WmiObject -Class Win32_ComputerSystem; $cs.AutomaticManagedPagefile = $true; $cs.Put()'
                result = subprocess.run(["powershell", "-Command", powershell_cmd], 
                                      capture_output=True, text=True, shell=True)
            else:
                # 手动设置大小
                initial = self.initial_var.get()
                maximum = self.maximum_var.get()
                
                if not initial.isdigit() or not maximum.isdigit():
                    messagebox.showerror("错误", "请输入有效的数字")
                    return
                
                # 使用PowerShell设置页面文件大小
                powershell_cmd = f'''
                $cs = Get-WmiObject -Class Win32_ComputerSystem
                $cs.AutomaticManagedPagefile = $false
                $cs.Put()
                
                $pf = Get-WmiObject -Class Win32_PageFileSetting -Filter "SettingID='{drive}:\\pagefile.sys'"
                if ($pf) {{
                    $pf.InitialSize = {initial}
                    $pf.MaximumSize = {maximum}
                    $pf.Put()
                }} else {{
                    $pf = ([WMIClass]"Win32_PageFileSetting").CreateInstance()
                    $pf.Name = "{drive}:\\pagefile.sys"
                    $pf.InitialSize = {initial}
                    $pf.MaximumSize = {maximum}
                    $pf.Put()
                }}
                '''
                result = subprocess.run(["powershell", "-Command", powershell_cmd], 
                                      capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                messagebox.showinfo("成功", "页面文件设置已应用，重启后生效")
                self.check_current_status()  # 刷新状态显示
            else:
                messagebox.showerror("错误", f"设置失败: {result.stderr}")
                
        except Exception as e:
            messagebox.showerror("错误", f"应用设置时出错: {str(e)}")

    def disable_pagefile(self):
        """禁用页面文件"""
        if messagebox.askyesno("确认", "确定要禁用页面文件吗？这可能影响系统性能。"):
            try:
                drive = self.drive_var.get()
                # 使用PowerShell禁用页面文件
                powershell_cmd = f'''
                $cs = Get-WmiObject -Class Win32_ComputerSystem
                $cs.AutomaticManagedPagefile = $false
                $cs.Put()
                
                $pf = Get-WmiObject -Class Win32_PageFileSetting -Filter "SettingID='{drive}:\\pagefile.sys'"
                if ($pf) {{
                    $pf.Delete()
                }}
                '''
                result = subprocess.run(["powershell", "-Command", powershell_cmd], 
                                      capture_output=True, text=True, shell=True)
                
                if result.returncode == 0:
                    messagebox.showinfo("成功", "页面文件已禁用，重启后生效")
                    self.check_current_status()  # 刷新状态显示
                else:
                    messagebox.showerror("错误", f"禁用失败: {result.stderr}")
                    
            except Exception as e:
                messagebox.showerror("错误", f"禁用页面文件时出错: {str(e)}")

class HibernateManagerDialog:
    """休眠管理对话框"""
    def __init__(self, parent, core):
        self.core = core
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("休眠管理")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建休眠管理界面"""
        # 当前状态显示
        status_frame = ttk.LabelFrame(self.dialog, text="当前休眠状态")
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=10)
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="检查休眠状态", command=self.check_hibernate_status).pack(side="left", padx=5)
        ttk.Button(button_frame, text="启用休眠", command=self.enable_hibernate).pack(side="left", padx=5)
        ttk.Button(button_frame, text="禁用休眠", command=self.disable_hibernate).pack(side="left", padx=5)
        ttk.Button(button_frame, text="关闭", command=self.dialog.destroy).pack(side="right", padx=5)
        
        # 初始化显示当前状态
        self.check_hibernate_status()
    
    def check_hibernate_status(self):
        """检查休眠状态"""
        try:
            # 使用powercfg命令查询休眠状态
            result = subprocess.run(["powercfg", "/a"], capture_output=True, text=True, shell=True)
            
            self.status_text.delete(1.0, tk.END)
            
            if result.returncode == 0:
                self.status_text.insert(tk.END, "系统电源状态:\n\n")
                self.status_text.insert(tk.END, result.stdout)
            else:
                self.status_text.insert(tk.END, f"查询失败: {result.stderr}")
                
        except Exception as e:
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, f"查询休眠状态时出错: {str(e)}")
    
    def enable_hibernate(self):
        """启用休眠"""
        try:
            result = subprocess.run(["powercfg", "/hibernate", "on"], 
                                  capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                messagebox.showinfo("成功", "休眠功能已启用")
                self.check_hibernate_status()  # 刷新状态显示
            else:
                messagebox.showerror("错误", f"启用失败: {result.stderr}")
                
        except Exception as e:
            messagebox.showerror("错误", f"启用休眠时出错: {str(e)}")
    
    def disable_hibernate(self):
        """禁用休眠"""
        if messagebox.askyesno("确认", "确定要禁用休眠功能吗？"):
            try:
                result = subprocess.run(["powercfg", "/hibernate", "off"], 
                                      capture_output=True, text=True, shell=True)
                
                if result.returncode == 0:
                    messagebox.showinfo("成功", "休眠功能已禁用")
                    self.check_hibernate_status()  # 刷新状态显示
                else:
                    messagebox.showerror("错误", f"禁用失败: {result.stderr}")
                    
            except Exception as e:
                messagebox.showerror("错误", f"禁用休眠时出错: {str(e)}")

class FolderMigrationDialog:
    """用户目录迁移对话框"""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📁 用户目录迁移工具")
        self.dialog.geometry("800x600")
        self.dialog.resizable(True, True)
        
        # 设置图标
        try:
            icon_path = Path(__file__).parent / "icon.ico"
            if icon_path.exists():
                self.dialog.iconbitmap(str(icon_path))
        except:
            pass
        
        # 用户目录映射
        self.folder_mapping = {
            "Desktop": {"name": "桌面", "reg_key": "Desktop", "shell_folder": "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}"},
            "Downloads": {"name": "下载", "reg_key": "{374DE290-123F-4565-9164-39C4925E467B}", "shell_folder": "{374DE290-123F-4565-9164-39C4925E467B}"},
            "Documents": {"name": "文档", "reg_key": "Personal", "shell_folder": "{F42EE2D3-909F-4907-8871-4C22FC0BF756}"},
            "Pictures": {"name": "图片", "reg_key": "My Pictures", "shell_folder": "{33E28130-4E1E-4676-835A-98395C3BC3BB}"},
            "Videos": {"name": "视频", "reg_key": "My Video", "shell_folder": "{18989B1D-99B5-455B-841C-AB7C74E4DDFC}"},
            "Music": {"name": "音乐", "reg_key": "My Music", "shell_folder": "{4BD8D571-6D19-48D3-BE97-422220080E43}"}
        }
        
        self.create_widgets()
        self.refresh_current_paths()
        
        # 设置为模态对话框
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 说明文本
        info_frame = ttk.LabelFrame(main_frame, text="📋 功能说明")
        info_frame.pack(fill="x", pady=(0, 10))
        
        info_text = (
            "此工具可以将用户目录（桌面、下载、文档等）迁移到其他位置，\n"
            "有助于释放C盘空间。迁移过程会自动移动现有文件。\n\n"
            "⚠️ 重要提示：\n"
            "• 迁移前请确保目标位置有足够空间\n"
            "• 建议先备份重要数据\n"
            "• 不要迁移到分区根目录，请创建子文件夹"
        )
        ttk.Label(info_frame, text=info_text, justify="left").pack(padx=10, pady=10)
        
        # 目录列表框架
        list_frame = ttk.LabelFrame(main_frame, text="📁 用户目录列表")
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # 创建表格
        columns = ("目录名称", "当前路径", "状态")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        # 设置列标题和宽度
        self.tree.heading("目录名称", text="目录名称")
        self.tree.heading("当前路径", text="当前路径")
        self.tree.heading("状态", text="状态")
        
        self.tree.column("目录名称", width=100, minwidth=80)
        self.tree.column("当前路径", width=400, minwidth=200)
        self.tree.column("状态", width=100, minwidth=80)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        
        # 操作按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(btn_frame, text="🔄 刷新状态", command=self.refresh_current_paths).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="📁 迁移选中目录", command=self.migrate_selected_folder).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="↩️ 恢复默认位置", command=self.restore_default_location).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ 关闭", command=self.dialog.destroy).pack(side="right")
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief="sunken")
        status_bar.pack(fill="x", pady=(5, 0))
        
    def get_current_folder_path(self, folder_key):
        """获取当前文件夹路径"""
        try:
            import winreg
            
            # 首先尝试从 User Shell Folders 读取
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
                    reg_key = self.folder_mapping[folder_key]["reg_key"]
                    path, _ = winreg.QueryValueEx(key, reg_key)
                    # 展开环境变量
                    return os.path.expandvars(path)
            except (FileNotFoundError, OSError):
                pass
            
            # 如果失败，尝试从 Shell Folders 读取
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                    reg_key = self.folder_mapping[folder_key]["reg_key"]
                    path, _ = winreg.QueryValueEx(key, reg_key)
                    return path
            except (FileNotFoundError, OSError):
                pass
            
            # 如果都失败，返回默认路径
            username = os.environ.get('USERNAME', 'User')
            default_paths = {
                "Desktop": f"C:\\Users\\{username}\\Desktop",
                "Downloads": f"C:\\Users\\{username}\\Downloads",
                "Documents": f"C:\\Users\\{username}\\Documents",
                "Pictures": f"C:\\Users\\{username}\\Pictures",
                "Videos": f"C:\\Users\\{username}\\Videos",
                "Music": f"C:\\Users\\{username}\\Music"
            }
            return default_paths.get(folder_key, "未知")
            
        except Exception as e:
            return f"读取失败: {str(e)}"
    
    def refresh_current_paths(self):
        """刷新当前路径显示"""
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 添加每个文件夹的信息
        for folder_key, folder_info in self.folder_mapping.items():
            current_path = self.get_current_folder_path(folder_key)
            
            # 判断状态
            username = os.environ.get('USERNAME', 'User')
            default_path = f"C:\\Users\\{username}"
            
            if current_path.startswith(default_path):
                status = "默认位置"
            elif os.path.exists(current_path):
                status = "已迁移"
            else:
                status = "路径无效"
            
            self.tree.insert("", "end", values=(folder_info["name"], current_path, status))
        
        self.status_var.set("路径信息已刷新")
    
    def migrate_selected_folder(self):
        """迁移选中的文件夹"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要迁移的目录")
            return
        
        # 获取选中项的信息
        item = selection[0]
        values = self.tree.item(item, "values")
        folder_name = values[0]
        current_path = values[1]
        
        # 找到对应的文件夹键
        folder_key = None
        for key, info in self.folder_mapping.items():
            if info["name"] == folder_name:
                folder_key = key
                break
        
        if not folder_key:
            messagebox.showerror("错误", "无法识别选中的文件夹")
            return
        
        # 选择目标路径
        target_path = filedialog.askdirectory(
            title=f"选择 {folder_name} 的新位置",
            initialdir="D:\\"
        )
        
        if not target_path:
            return
        
        # 创建目标文件夹路径
        target_folder_path = os.path.join(target_path, folder_key)
        
        # 确认迁移
        confirm_msg = (
            f"确定要将 {folder_name} 从\n"
            f"{current_path}\n"
            f"迁移到\n"
            f"{target_folder_path}\n\n"
            f"此操作将移动所有现有文件，是否继续？"
        )
        
        if not messagebox.askyesno("确认迁移", confirm_msg):
            return
        
        try:
            self.status_var.set(f"正在迁移 {folder_name}...")
            self.dialog.update()
            
            # 执行迁移
            success = self.perform_migration(folder_key, current_path, target_folder_path)
            
            if success:
                messagebox.showinfo("成功", f"{folder_name} 迁移完成！")
                self.refresh_current_paths()
            else:
                messagebox.showerror("失败", f"{folder_name} 迁移失败，请查看详细错误信息")
                
        except Exception as e:
            messagebox.showerror("错误", f"迁移过程中发生错误：{str(e)}")
        finally:
            self.status_var.set("就绪")
    
    def perform_migration(self, folder_key, current_path, target_path):
        """执行实际的迁移操作"""
        try:
            import winreg
            import shutil
            
            # 1. 创建目标目录
            os.makedirs(target_path, exist_ok=True)
            
            # 2. 如果源目录存在且不同于目标目录，移动文件
            if os.path.exists(current_path) and os.path.abspath(current_path) != os.path.abspath(target_path):
                # 移动所有文件和子目录
                for item in os.listdir(current_path):
                    source_item = os.path.join(current_path, item)
                    target_item = os.path.join(target_path, item)
                    
                    if os.path.isdir(source_item):
                        shutil.move(source_item, target_item)
                    else:
                        shutil.move(source_item, target_item)
                
                # 删除空的源目录
                try:
                    os.rmdir(current_path)
                except OSError:
                    pass  # 目录可能不为空或被占用
            
            # 3. 更新注册表
            reg_key = self.folder_mapping[folder_key]["reg_key"]
            
            # 更新 User Shell Folders
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                              r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders", 
                              0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, reg_key, 0, winreg.REG_EXPAND_SZ, target_path)
            
            # 更新 Shell Folders
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                              r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders", 
                              0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, reg_key, 0, winreg.REG_SZ, target_path)
            
            # 4. 刷新资源管理器
            self.refresh_explorer()
            
            return True
            
        except Exception as e:
            print(f"迁移失败: {str(e)}")
            return False
    
    def restore_default_location(self):
        """恢复默认位置"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要恢复的目录")
            return
        
        # 获取选中项的信息
        item = selection[0]
        values = self.tree.item(item, "values")
        folder_name = values[0]
        current_path = values[1]
        
        # 找到对应的文件夹键
        folder_key = None
        for key, info in self.folder_mapping.items():
            if info["name"] == folder_name:
                folder_key = key
                break
        
        if not folder_key:
            messagebox.showerror("错误", "无法识别选中的文件夹")
            return
        
        # 计算默认路径
        username = os.environ.get('USERNAME', 'User')
        default_path = f"C:\\Users\\{username}\\{folder_key}"
        
        if current_path == default_path:
            messagebox.showinfo("提示", f"{folder_name} 已经在默认位置")
            return
        
        # 确认恢复
        confirm_msg = (
            f"确定要将 {folder_name} 从\n"
            f"{current_path}\n"
            f"恢复到默认位置\n"
            f"{default_path}\n\n"
            f"此操作将移动所有现有文件，是否继续？"
        )
        
        if not messagebox.askyesno("确认恢复", confirm_msg):
            return
        
        try:
            self.status_var.set(f"正在恢复 {folder_name}...")
            self.dialog.update()
            
            # 执行恢复
            success = self.perform_migration(folder_key, current_path, default_path)
            
            if success:
                messagebox.showinfo("成功", f"{folder_name} 已恢复到默认位置！")
                self.refresh_current_paths()
            else:
                messagebox.showerror("失败", f"{folder_name} 恢复失败，请查看详细错误信息")
                
        except Exception as e:
            messagebox.showerror("错误", f"恢复过程中发生错误：{str(e)}")
        finally:
            self.status_var.set("就绪")
    
    def refresh_explorer(self):
        """刷新资源管理器"""
        try:
            # 通知系统文件夹位置已更改
            import ctypes
            from ctypes import wintypes
            
            # 定义常量
            SHCNE_ASSOCCHANGED = 0x08000000
            SHCNF_IDLIST = 0x0000
            
            # 调用 SHChangeNotify
            ctypes.windll.shell32.SHChangeNotify(
                SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None
            )
            
        except Exception:
            pass  # 忽略刷新失败

def main():
    """主函数"""
    # 改进的管理员权限检查
    if not is_admin():
        result = messagebox.askyesno(
            "权限提示", 
            "此程序需要管理员权限才能正常运行。\n\n是否以管理员身份重新启动？"
        )
        if result:
            if run_as_admin():
                sys.exit(0)  # 成功启动管理员版本，退出当前进程
            else:
                messagebox.showerror("错误", "无法获取管理员权限，程序将以普通权限运行")
        else:
            messagebox.showwarning(
                "警告", 
                "没有管理员权限，某些功能可能无法正常使用"
            )
    
    # 创建主窗口
    root = tk.Tk()
    root.title("Clean Tools" + (" (管理员)" if is_admin() else " (普通用户)"))
    
    # 创建应用程序实例
    app = CleanToolsGUI(root)
    
    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    main()