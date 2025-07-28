# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import os
import sys
import subprocess
import winreg
import ctypes
from pathlib import Path
import datetime
from Crypto.Cipher import AES
from lib import CleanToolsCore
from i18n import init_i18n, get_translator, t

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
    # 初始化国际化
    program_path = Path(__file__).parent
    init_i18n(program_path)
    
    # 改进的管理员权限检查
    if not is_admin():
        result = messagebox.askyesno(
            t("permission_prompt_title"), 
            t("permission_prompt_message")
        )
        if result:
            if run_as_admin():
                sys.exit(0)  # 成功启动管理员版本，退出当前进程
            else:
                messagebox.showerror(t("error"), t("permission_elevation_failed"))
        else:
            messagebox.showwarning(
                t("warning"), 
                t("permission_warning_message")
            )
    
    # 创建主窗口
    root = tk.Tk()
    admin_suffix = f" ({t('admin_mode')})" if is_admin() else f" ({t('normal_user_mode')})"
    root.title(t("app_title") + admin_suffix)
    
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
        
        # 获取翻译器实例
        self.translator = get_translator()
        
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
        
        admin_status = t('admin_mode') if self.is_admin else t('normal_user_mode')
        ttk.Label(status_frame, text=admin_status, font=("Arial", 10, "bold")).pack(side="left")
        
        # 设置按钮
        ttk.Button(status_frame, text=t('settings'), command=self.open_settings).pack(side="right")
        
        # 系统管理按钮区域
        system_frame = ttk.LabelFrame(self.root, text=t('system_management'))
        system_frame.pack(fill="x", padx=10, pady=5)
        
        btn_frame = ttk.Frame(system_frame)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(btn_frame, text=t('pagefile_management'), command=self.open_pagefile_manager).pack(side="left", padx=5)
        ttk.Button(btn_frame, text=t('hibernate_management'), command=self.open_hibernate_manager).pack(side="left", padx=5)
        ttk.Button(btn_frame, text=t('folder_migration'), command=self.open_folder_migration).pack(side="left", padx=5)
        
        # 主内容区域
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 左侧：规则选择区域
        left_frame = ttk.LabelFrame(main_frame, text=t('rule_list'))
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # 规则列表
        self.rule_listbox = tk.Listbox(left_frame)
        self.rule_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.rule_listbox.bind("<<ListboxSelect>>", self.on_rule_select)
        
        # 规则操作按钮
        rule_btn_frame = ttk.Frame(left_frame)
        rule_btn_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(rule_btn_frame, text=t('new_rule'), command=self.create_new_rule).pack(side="left", padx=2)
        ttk.Button(rule_btn_frame, text=t('edit_rule'), command=self.edit_rule).pack(side="left", padx=2)
        ttk.Button(rule_btn_frame, text=t('delete_rule'), command=self.delete_rule).pack(side="left", padx=2)
        ttk.Button(rule_btn_frame, text=t('import_rule'), command=self.import_rule).pack(side="left", padx=2)
        
        # 右侧：规则信息显示
        right_frame = ttk.LabelFrame(main_frame, text=t('rule_info'))
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        self.info_text = scrolledtext.ScrolledText(right_frame, height=15)
        self.info_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 清理操作区域
        clean_frame = ttk.LabelFrame(self.root, text=t('clean_operation'))
        clean_frame.pack(fill="x", padx=10, pady=5)
        
        # 开始清理按钮
        self.clean_btn = ttk.Button(clean_frame, text=t('start_clean'), command=self.start_clean)
        self.clean_btn.pack(pady=10)
        
        # 创建进度条区域
        self.create_progress_area()
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(self.root, text=t('operation_log'))
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def create_progress_area(self):
        """创建专门的进度条区域"""
        # 进度条区域 - 使用更紧凑的布局
        self.progress_frame = ttk.LabelFrame(self.root, text=t('operation_progress'))
        self.progress_frame.pack(fill="x", padx=10, pady=(5, 0))
        
        # 内容容器
        content_frame = ttk.Frame(self.progress_frame)
        content_frame.pack(fill="x", padx=8, pady=8)
        
        # 状态标签和百分比 - 同一行显示
        status_frame = ttk.Frame(content_frame)
        status_frame.pack(fill="x", pady=(0, 5))
        
        self.progress_status = ttk.Label(status_frame, text=t("ready"), font=("Arial", 9))
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

    def update_progress(self, value=0, status=None, detail=""):
        """更新进度条 - 统一的进度更新接口"""
        # 更新进度条值
        self.progress_bar['value'] = max(0, min(100, value))
        
        # 更新百分比显示
        self.progress_percent.config(text=f"{int(value)}%")
        
        # 更新状态文本
        if status is None:
            status = t("ready")
        self.progress_status.config(text=status)
        
        # 更新详细信息（可选）
        if detail:
            self.progress_detail.config(text=detail)
        
        # 强制更新界面
        self.root.update_idletasks()

    def reset_progress(self):
        """重置进度条"""
        self.update_progress(0, t("ready"), "")

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
        
        self.progress_status.config(text=f"❌ {t('error')}")
        self.progress_detail.config(text=message)
        
        # 3秒后恢复正常样式
        self.root.after(3000, self.reset_progress_style)

    def show_progress_complete(self, message):
        """显示进度完成状态"""
        self.progress_bar['value'] = 100
        self.progress_percent.config(text="100%")
        self.progress_status.config(text=f"✅ {t('complete')}")
        self.progress_detail.config(text=message)

    def reset_progress_style(self):
        """重置进度条样式"""
        self.progress_bar.config(style="Custom.Horizontal.TProgressbar")
        self.reset_progress()
    
    def refresh_ui(self):
        """刷新界面文本"""
        # 销毁所有子组件
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 重新创建界面
        self.create_widgets()
        self.load_rules()
        
        # 更新窗口标题
        admin_suffix = f" ({t('admin_mode')})" if self.is_admin else f" ({t('normal_user_mode')})"
        self.root.title(t("app_title") + admin_suffix)
    
    def start_clean(self):
        """开始清理"""
        if not self.current_rule:
            messagebox.showwarning(t("warning"), t("select_rule_first"))
            return
        
        try:
            # 重置进度条
            self.reset_progress()
            
            rule_info = self.rules_data[self.current_rule]
            
            # 安全检查
            self.update_progress(10, t("security_check"), t("verifying_rule_integrity"))
            
            # 检查是否为加密文件且存在安全问题
            if rule_info.get('is_encrypted', False):
                if rule_info.get('is_tampered', False) or rule_info.get('cannot_verify', False):
                    self.show_progress_error(t("security_verification_failed"))
                    
                    integrity_status = rule_info.get('integrity_status', 'unknown')
                    integrity_message = rule_info.get('integrity_message', '')
                    
                    if integrity_status == 'tampered':
                        error_msg = t("security_tampered_error", details=integrity_message)
                        self.log(f"[{t('security_blocked')}] {t('rule_tampered_detected')}: {self.current_rule} - {integrity_message}")
                        messagebox.showerror(t("security_error"), error_msg)
                        return
                    elif integrity_status in ['cannot_verify', 'error']:
                        error_msg = t("security_cannot_verify_error", details=integrity_message)
                        self.log(f"[{t('security_blocked')}] {t('rule_integrity_unverifiable')}: {self.current_rule} - {integrity_message}")
                        messagebox.showerror(t("security_error"), error_msg)
                        return
                else:
                    # 执行前最后一次验证
                    rule_dir = rule_info.get('rule_dir')
                    original_author = rule_info.get('Auther', 'Unknown')
                    
                    try:
                        is_valid, message = self.core.security_manager.verify_integrity(rule_dir, original_author)
                        if not is_valid:
                            self.show_progress_error(t("tampered_before_execution"))
                            error_msg = t("security_tampered_before_execution", details=message)
                            self.log(f"[{t('security_blocked')}] {t('rule_tampered_before_execution')}: {self.current_rule} - {message}")
                            messagebox.showerror(t("security_error"), error_msg)
                            return
                    except Exception as e:
                        self.show_progress_error(t("security_verification_failed"))
                        error_msg = t("security_verification_exception", details=str(e))
                        self.log(f"[{t('security_blocked')}] {t('security_verification_exception_log')}: {self.current_rule} - {str(e)}")
                        messagebox.showerror(t("security_error"), error_msg)
                        return
            
            # 记录开始执行的日志
            self.log(f"[{t('security_passed')}] {t('start_executing_verified_rule')}: {self.current_rule}")
            
            self.clean_btn.config(state="disabled")
            
            # 执行清理
            self.update_progress(40, t("executing_clean"), t("executing_rule", rule_name=self.current_rule))
            
            # 执行实际清理，带进度回调
            success = self.core.execute_clean_rule(
                rule_info, 
                self.log_callback,
                self.update_progress
            )
            
            if success:
                self.show_progress_complete(t("clean_completed", rule_name=self.current_rule))
                self.log(t("clean_completed", rule_name=self.current_rule))
                messagebox.showinfo(t("complete"), t("clean_operation_completed"))
            else:
                self.show_progress_error(t("clean_process_error"))
                messagebox.showerror(t("error"), t("clean_process_error"))
                
        except Exception as e:
            self.show_progress_error(t("clean_failed", error=str(e)))
            self.log(t("clean_failed", error=str(e)))
            messagebox.showerror(t("error"), t("clean_failed", error=str(e)))
        finally:
            self.clean_btn.config(state="normal")
    
    def create_new_rule(self):
        """创建新规则"""
        dialog = RuleEditorDialog(self.root, t("create_new_rule"))
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            rule_name = dialog.result['Name']
            rule_path = self.core.save_rule(dialog.result)
            if rule_path:
                self.log(t("rule_saved_to", path=rule_path))
                messagebox.showinfo(t("success"), t("rule_created_success", rule_name=rule_name, path=rule_path))
                self.load_rules()
            else:
                messagebox.showerror(t("error"), t("save_rule_failed"))
        else:
            self.log(t("dialog_no_result"))
    
    def edit_rule(self):
        """编辑规则"""
        if not self.current_rule:
            messagebox.showwarning(t("warning"), t("select_rule_first"))
            return
        
        # 检测是否为加密文件
        if self.is_encrypted_rule(self.current_rule):
            messagebox.showerror(t("error"), t("encrypted_rule_cannot_edit"))
            return
            
        rule_info = self.rules_data[self.current_rule]
        dialog = RuleEditorDialog(self.root, t("edit_rule"), rule_info)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            rule_path = self.core.save_rule(dialog.result)
            if rule_path:
                self.log(t("rule_updated", path=rule_path))
                messagebox.showinfo(t("success"), t("rule_update_success"))
                self.load_rules()
            else:
                messagebox.showerror(t("error"), t("save_rule_failed"))
    
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
                    if 'random_key' in content or t("encrypted_file_marker") in content:
                        return True
            
            return False
        except:
            return False
    
    def delete_rule(self):
        """删除规则"""
        if not self.current_rule:
            messagebox.showwarning(t("warning"), t("select_rule_first"))
            return
        
        if messagebox.askyesno(t("confirm"), t("confirm_delete_rule", rule_name=self.current_rule)):
            if self.core.delete_rule(self.current_rule):
                self.log(t("rule_deleted", rule_name=self.current_rule))
                messagebox.showinfo(t("success"), t("rule_delete_success"))
                self.current_rule = None
                self.load_rules()
                self.info_text.config(state="normal")
                self.info_text.delete(1.0, tk.END)
                self.info_text.config(state="disabled")
            else:
                messagebox.showerror(t("error"), t("delete_rule_failed"))
    
    def import_rule(self):
        """导入规则"""
        file_path = filedialog.askopenfilename(
            title=t("select_rule_file"),
            filetypes=[(t("compressed_files"), "*.zip"), (t("all_files"), "*.*")]
        )
        
        if file_path:
            if self.core.import_rule(file_path):
                self.log(t("rule_import_success", path=file_path))
                self.load_rules()
            else:
                self.log(t("rule_import_failed", path=file_path))
    
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
                info_text += f"\n\n=== {t('security_status')} ==="
                info_text += f"\n{t('file_type')}: 🔒 {t('encrypted_file')}"
                
                integrity_status = rule_info.get('integrity_status', 'unknown')
                integrity_message = rule_info.get('integrity_message', '')
                
                if integrity_status == 'valid':
                    info_text += f"\n{t('integrity')}: ✅ {t('verification_passed')}"
                elif integrity_status == 'tampered':
                    info_text += f"\n{t('integrity')}: ❌ {t('file_tampered')}"
                    info_text += f"\n{t('execution_status')}: 🚫 {t('execution_prohibited')}"
                    info_text += f"\n{t('details')}: {integrity_message}"
                elif integrity_status == 'cannot_verify':
                    info_text += f"\n{t('integrity')}: ⚠️ {t('cannot_verify')}"
                    info_text += f"\n{t('execution_status')}: 🚫 {t('execution_prohibited')}"
                    info_text += f"\n{t('details')}: {integrity_message}"
                elif integrity_status == 'error':
                    info_text += f"\n{t('integrity')}: ❌ {t('verification_error')}"
                    info_text += f"\n{t('execution_status')}: 🚫 {t('execution_prohibited')}"
                    info_text += f"\n{t('details')}: {integrity_message}"
                else:
                    info_text += f"\n{t('integrity')}: ⚠️ {t('status_unknown')}"
                    info_text += f"\n{t('execution_status')}: 🚫 {t('execution_prohibited')}"
            else:
                info_text += f"\n\n=== {t('security_status')} ==="
                info_text += f"\n{t('file_type')}: 📄 {t('normal_file')}"
                info_text += f"\n{t('execution_status')}: ✅ {t('execution_allowed')}"
            
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
        dialog = SettingsDialog(self.root, self)
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
        info_frame = ttk.LabelFrame(self.dialog, text=t("rule_info"))
        info_frame.pack(fill="x", padx=10, pady=5)
        
        # 规则名称
        ttk.Label(info_frame, text=f"{t('rule_name')}:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.name_entry = ttk.Entry(info_frame, width=50)
        self.name_entry.grid(row=0, column=1, padx=5, pady=2)
        
        # 版本
        ttk.Label(info_frame, text=f"{t('version')}:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.version_entry = ttk.Entry(info_frame, width=50)
        self.version_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # 作者
        ttk.Label(info_frame, text=f"{t('author')}:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.author_entry = ttk.Entry(info_frame, width=50)
        self.author_entry.grid(row=2, column=1, padx=5, pady=2)
        
        # 描述
        ttk.Label(info_frame, text=f"{t('description')}:").grid(row=3, column=0, sticky="nw", padx=5, pady=2)
        self.desc_text = tk.Text(info_frame, height=3, width=50)
        self.desc_text.grid(row=3, column=1, padx=5, pady=2)
        
        # 规则内容
        content_frame = ttk.LabelFrame(self.dialog, text=t("rule_content"))
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.content_text = scrolledtext.ScrolledText(content_frame, height=15)
        self.content_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 加密选项
        encrypt_frame = ttk.Frame(self.dialog)
        encrypt_frame.pack(fill="x", padx=10, pady=5)
        
        self.encrypt_var = tk.BooleanVar()
        ttk.Checkbutton(encrypt_frame, text=f"🔒 {t('encrypt_save_option')}", variable=self.encrypt_var).pack(side="left")
        
        # 按钮区域
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text=t("save"), command=self.save_rule).pack(side="right", padx=5)
        ttk.Button(btn_frame, text=t("cancel"), command=self.cancel).pack(side="right")
        
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
            messagebox.showerror(t("error"), t("enter_rule_name"))
            return
        
        version = self.version_entry.get().strip() or "1.0"
        author = self.author_entry.get().strip() or "Unknown"
        description = self.desc_text.get(1.0, tk.END).strip() or "none"
        content = self.content_text.get(1.0, tk.END).strip()
        
        if not content:
            messagebox.showerror(t("error"), t("enter_rule_content"))
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
    def __init__(self, parent, main_app):
        self.main_app = main_app
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(t("settings"))
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 设置图标
        try:
            self.dialog.iconbitmap("icon.ico")
        except:
            pass
        
        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 100))
        
        # 存储UI组件引用以便更新
        self.ui_components = {}
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建设置界面组件"""
        # 清除现有组件
        for widget in self.dialog.winfo_children():
            widget.destroy()
        
        # 语言设置区域
        lang_frame = ttk.LabelFrame(self.dialog, text=t("language_settings"))
        lang_frame.pack(fill="x", padx=10, pady=10)
        self.ui_components['lang_frame'] = lang_frame
        
        # 语言选择
        lang_label = ttk.Label(lang_frame, text=f"{t('select_language')}:")
        lang_label.pack(anchor="w", padx=10, pady=(10, 5))
        self.ui_components['lang_label'] = lang_label
        
        self.language_var = tk.StringVar()
        language_combo = ttk.Combobox(lang_frame, textvariable=self.language_var, state="readonly")
        
        # 获取可用语言
        translator = get_translator()
        if translator:
            available_languages = translator.get_available_languages()
            language_combo['values'] = list(available_languages.values())
            
            # 设置当前语言
            current_lang = translator.current_language
            current_display = available_languages.get(current_lang, current_lang)
            self.language_var.set(current_display)
            
            # 保存语言代码映射
            self.lang_code_map = {v: k for k, v in available_languages.items()}
        
        language_combo.pack(fill="x", padx=10, pady=(0, 10))
        language_combo.bind('<<ComboboxSelected>>', self.on_language_change)
        self.ui_components['language_combo'] = language_combo
        
        # 其他设置区域
        other_frame = ttk.LabelFrame(self.dialog, text=t("other_settings"))
        other_frame.pack(fill="x", padx=10, pady=10)
        self.ui_components['other_frame'] = other_frame
        
        # 关于程序按钮
        about_btn = ttk.Button(other_frame, text=t("about_program"), command=self.show_about)
        about_btn.pack(pady=10)
        self.ui_components['about_btn'] = about_btn
        
        # 关闭按钮
        close_btn = ttk.Button(self.dialog, text=t("close"), command=self.dialog.destroy)
        close_btn.pack(pady=10)
        self.ui_components['close_btn'] = close_btn
    
    def refresh_ui_text(self):
        """刷新界面文本（不重新创建组件）"""
        # 更新窗口标题
        self.dialog.title(t("settings"))
        
        # 更新各个组件的文本
        if 'lang_frame' in self.ui_components:
            self.ui_components['lang_frame'].config(text=t("language_settings"))
        
        if 'lang_label' in self.ui_components:
            self.ui_components['lang_label'].config(text=f"{t('select_language')}:")
        
        if 'other_frame' in self.ui_components:
            self.ui_components['other_frame'].config(text=t("other_settings"))
        
        if 'about_btn' in self.ui_components:
            self.ui_components['about_btn'].config(text=t("about_program"))
        
        if 'close_btn' in self.ui_components:
            self.ui_components['close_btn'].config(text=t("close"))
    
    def on_language_change(self, event):
        """语言改变事件"""
        selected_display = self.language_var.get()
        selected_code = self.lang_code_map.get(selected_display)
        
        if selected_code:
            translator = get_translator()
            if translator and selected_code != translator.current_language:
                # 切换语言
                translator.set_language(selected_code)
                
                # 刷新设置对话框的文本
                self.refresh_ui_text()
                
                # 更新语言选择下拉框的值
                if translator:
                    available_languages = translator.get_available_languages()
                    if 'language_combo' in self.ui_components:
                        self.ui_components['language_combo']['values'] = list(available_languages.values())
                        current_display = available_languages.get(selected_code, selected_code)
                        self.language_var.set(current_display)
                        # 更新语言代码映射
                        self.lang_code_map = {v: k for k, v in available_languages.items()}
                
                # 刷新主界面
                self.main_app.refresh_ui()
                
                # 显示语言切换成功消息（现在使用新语言）
                messagebox.showinfo(t("success"), t("language_changed_success"))
    
    def show_about(self):
        """显示关于信息"""
        about_text = f"{t('app_title')}\n\n" \
                    f"{t('version')}: 2.0\n" \
                    f"{t('app_description')}\n\n" \
                    f"{t('features')}:\n" \
                    f"• {t('feature_rule_system')}\n" \
                    f"• {t('feature_encryption')}\n" \
                    f"• {t('feature_integrity')}\n" \
                    f"• {t('feature_pagefile')}\n" \
                    f"• {t('feature_hibernate')}\n" \
                    f"• {t('feature_progress')}\n" \
                    f"• {t('feature_multilang')}"
        
        messagebox.showinfo(t("about_clean_tools"), about_text)

class PageFileManagerDialog:
    """页面文件管理对话框"""
    def __init__(self, parent, core):
        self.core = core
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(t("pagefile_management"))
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 100))
        
        self.create_widgets()
        self.check_current_status()  
    
    def create_widgets(self):
        """创建页面文件管理界面"""
        # 当前状态显示
        status_frame = ttk.LabelFrame(self.dialog, text=t("current_pagefile_status"))
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=8)
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 设置区域
        setting_frame = ttk.LabelFrame(self.dialog, text=t("pagefile_settings"))
        setting_frame.pack(fill="x", padx=10, pady=5)
        
        # 驱动器选择
        ttk.Label(setting_frame, text=f"{t('target_drive')}:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.drive_var = tk.StringVar(value="C")
        drive_combo = ttk.Combobox(setting_frame, textvariable=self.drive_var, values=["C", "D", "E", "F"], width=10)
        drive_combo.grid(row=0, column=1, padx=5, pady=2)
        
        # 初始大小
        ttk.Label(setting_frame, text=f"{t('initial_size_mb')}:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.initial_var = tk.StringVar(value="1024")
        ttk.Entry(setting_frame, textvariable=self.initial_var, width=15).grid(row=1, column=1, padx=5, pady=2)
        
        # 最大大小
        ttk.Label(setting_frame, text=f"{t('maximum_size_mb')}:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.maximum_var = tk.StringVar(value="2048")
        ttk.Entry(setting_frame, textvariable=self.maximum_var, width=15).grid(row=2, column=1, padx=5, pady=2)
        
        # 系统管理选项
        self.system_managed_var = tk.BooleanVar()
        ttk.Checkbutton(setting_frame, text=t("system_managed_pagefile"), 
                       variable=self.system_managed_var, 
                       command=self.toggle_manual_settings).grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text=t("check_current_status"), command=self.check_current_status).pack(side="left", padx=5)
        ttk.Button(button_frame, text=t("apply_settings"), command=self.apply_settings).pack(side="left", padx=5)
        ttk.Button(button_frame, text=t("disable_pagefile"), command=self.disable_pagefile).pack(side="left", padx=5)
        ttk.Button(button_frame, text=t("close"), command=self.dialog.destroy).pack(side="right", padx=5)
        
        # 初始化显示当前状态
        self.check_current_status()
    
    def toggle_manual_settings(self):
        """切换手动/自动设置"""
        if self.system_managed_var.get():
            # 禁用手动输入
            for widget in self.dialog.winfo_children():
                if isinstance(widget, ttk.LabelFrame) and widget.cget("text") == t("pagefile_settings"):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Entry):
                            child.config(state="disabled")
        else:
            # 启用手动输入
            for widget in self.dialog.winfo_children():
                if isinstance(widget, ttk.LabelFrame) and widget.cget("text") == t("pagefile_settings"):
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
                    self.status_text.insert(tk.END, f"{t('current_pagefile_config')}:\n\n")
                    self.status_text.insert(tk.END, output)
                else:
                    self.status_text.insert(tk.END, t("no_pagefile_config_found"))
            else:
                # 备用方案：使用系统信息命令
                try:
                    result2 = subprocess.run(["systeminfo"], capture_output=True, text=True, shell=True)
                    if result2.returncode == 0:
                        lines = result2.stdout.split('\n')
                        pagefile_info = [line for line in lines if '页面文件' in line or 'Page File' in line]
                        if pagefile_info:
                            self.status_text.insert(tk.END, f"{t('pagefile_info')}:\n\n")
                            for info in pagefile_info:
                                self.status_text.insert(tk.END, info.strip() + "\n")
                        else:
                            self.status_text.insert(tk.END, t("no_pagefile_info_found"))
                    else:
                        self.status_text.insert(tk.END, t("query_failed", error=result.stderr))
                except:
                    self.status_text.insert(tk.END, t("cannot_query_pagefile_status"))
                
        except Exception as e:
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, t("query_pagefile_error", error=str(e)))

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
                    messagebox.showerror(t("error"), t("enter_valid_numbers"))
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
                messagebox.showinfo(t("success"), t("pagefile_settings_applied"))
                self.check_current_status()  # 刷新状态显示
            else:
                messagebox.showerror(t("error"), t("setting_failed", error=result.stderr))
                
        except Exception as e:
            messagebox.showerror(t("error"), t("apply_settings_error", error=str(e)))

    def disable_pagefile(self):
        """禁用页面文件"""
        if messagebox.askyesno(t("confirm"), t("confirm_disable_pagefile")):
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
                    messagebox.showinfo(t("success"), t("pagefile_disabled"))
                    self.check_current_status()  # 刷新状态显示
                else:
                    messagebox.showerror(t("error"), t("disable_failed", error=result.stderr))
                    
            except Exception as e:
                messagebox.showerror(t("error"), t("disable_pagefile_error", error=str(e)))

class HibernateManagerDialog:
    """休眠管理对话框"""
    def __init__(self, parent, core):
        self.core = core
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(t("hibernate_management"))
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建休眠管理界面"""
        # 当前状态显示
        status_frame = ttk.LabelFrame(self.dialog, text=t("current_hibernate_status"))
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=10)
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text=t("check_hibernate_status"), command=self.check_hibernate_status).pack(side="left", padx=5)
        ttk.Button(button_frame, text=t("enable_hibernate"), command=self.enable_hibernate).pack(side="left", padx=5)
        ttk.Button(button_frame, text=t("disable_hibernate"), command=self.disable_hibernate).pack(side="left", padx=5)
        ttk.Button(button_frame, text=t("close"), command=self.dialog.destroy).pack(side="right", padx=5)
        
        # 初始化显示当前状态
        self.check_hibernate_status()
    
    def check_hibernate_status(self):
        """检查休眠状态"""
        try:
            # 使用powercfg命令查询休眠状态
            result = subprocess.run(["powercfg", "/a"], capture_output=True, text=True, shell=True)
            
            self.status_text.delete(1.0, tk.END)
            
            if result.returncode == 0:
                self.status_text.insert(tk.END, f"{t('system_power_status')}:\n\n")
                self.status_text.insert(tk.END, result.stdout)
            else:
                self.status_text.insert(tk.END, t("query_failed", error=result.stderr))
                
        except Exception as e:
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, t("query_hibernate_error", error=str(e)))
    
    def enable_hibernate(self):
        """启用休眠"""
        try:
            result = subprocess.run(["powercfg", "/hibernate", "on"], 
                                  capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                messagebox.showinfo(t("success"), t("hibernate_enabled"))
                self.check_hibernate_status()  # 刷新状态显示
            else:
                messagebox.showerror(t("error"), t("enable_failed", error=result.stderr))
                
        except Exception as e:
            messagebox.showerror(t("error"), t("enable_hibernate_error", error=str(e)))
    
    def disable_hibernate(self):
        """禁用休眠"""
        if messagebox.askyesno(t("confirm"), t("confirm_disable_hibernate")):
            try:
                result = subprocess.run(["powercfg", "/hibernate", "off"], 
                                      capture_output=True, text=True, shell=True)
                
                if result.returncode == 0:
                    messagebox.showinfo(t("success"), t("hibernate_disabled"))
                    self.check_hibernate_status()  # 刷新状态显示
                else:
                    messagebox.showerror(t("error"), t("disable_failed", error=result.stderr))
                    
            except Exception as e:
                messagebox.showerror(t("error"), t("disable_hibernate_error", error=str(e)))

class FolderMigrationDialog:
    """用户目录迁移对话框"""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"📁 {t('folder_migration_tool')}")
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
            "Desktop": {"name": t("desktop"), "reg_key": "Desktop", "shell_folder": "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}"},
            "Downloads": {"name": t("downloads"), "reg_key": "{374DE290-123F-4565-9164-39C4925E467B}", "shell_folder": "{374DE290-123F-4565-9164-39C4925E467B}"},
            "Documents": {"name": t("documents"), "reg_key": "Personal", "shell_folder": "{F42EE2D3-909F-4907-8871-4C22FC0BF756}"},
            "Pictures": {"name": t("pictures"), "reg_key": "My Pictures", "shell_folder": "{33E28130-4E1E-4676-835A-98395C3BC3BB}"},
            "Videos": {"name": t("videos"), "reg_key": "My Video", "shell_folder": "{18989B1D-99B5-455B-841C-AB7C74E4DDFC}"},
            "Music": {"name": t("music"), "reg_key": "My Music", "shell_folder": "{4BD8D571-6D19-48D3-BE97-422220080E43}"}
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
        info_frame = ttk.LabelFrame(main_frame, text=f"📋 {t('function_description')}")
        info_frame.pack(fill="x", pady=(0, 10))
        
        info_text = t("folder_migration_description")
        ttk.Label(info_frame, text=info_text, justify="left").pack(padx=10, pady=10)
        
        # 目录列表框架
        list_frame = ttk.LabelFrame(main_frame, text=f"📁 {t('user_folder_list')}")
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # 创建表格
        columns = (t("folder_name"), t("current_path"), t("status"))
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        # 设置列标题和宽度
        self.tree.heading(t("folder_name"), text=t("folder_name"))
        self.tree.heading(t("current_path"), text=t("current_path"))
        self.tree.heading(t("status"), text=t("status"))
        
        self.tree.column(t("folder_name"), width=100, minwidth=80)
        self.tree.column(t("current_path"), width=400, minwidth=200)
        self.tree.column(t("status"), width=100, minwidth=80)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        
        # 操作按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(btn_frame, text=f"🔄 {t('refresh_status')}", command=self.refresh_current_paths).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text=f"📁 {t('migrate_selected_folder')}", command=self.migrate_selected_folder).pack(side="left", padx=5)
        ttk.Button(btn_frame, text=f"↩️ {t('restore_default_location')}", command=self.restore_default_location).pack(side="left", padx=5)
        ttk.Button(btn_frame, text=f"❌ {t('close')}", command=self.dialog.destroy).pack(side="right")
        
        # 状态栏
        self.status_var = tk.StringVar(value=t("ready"))
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
            return default_paths.get(folder_key, t("unknown"))
            
        except Exception as e:
            return t("read_failed", error=str(e))
    
    def refresh_current_paths(self):
        """刷新当前路径显示"""
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
                    # 添加各个文件夹信息
        username = os.environ.get('USERNAME', 'User')
        default_paths = {
            "Desktop": f"C:\\Users\\{username}\\Desktop",
            "Downloads": f"C:\\Users\\{username}\\Downloads", 
            "Documents": f"C:\\Users\\{username}\\Documents",
            "Pictures": f"C:\\Users\\{username}\\Pictures",
            "Videos": f"C:\\Users\\{username}\\Videos",
            "Music": f"C:\\Users\\{username}\\Music"
        }
        
        for folder_key, folder_info in self.folder_mapping.items():
            folder_name = folder_info["name"]
            current_path = self.get_current_folder_path(folder_key)
            default_path = default_paths.get(folder_key, t("unknown"))
            
            # 判断状态
            if current_path == default_path:
                status = t("default_location")
            elif current_path.startswith(t("read_failed")):
                status = t("read_error")
            else:
                status = t("custom_location")
            
            self.tree.insert("", "end", values=(folder_name, current_path, status))
    
    def migrate_selected_folder(self):
        """迁移选中的文件夹"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning(t("warning"), t("select_folder_first"))
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
            messagebox.showerror(t("error"), t("unrecognized_folder"))
            return
        
        # 选择目标路径
        target_path = filedialog.askdirectory(
            title=t("select_target_location", folder=folder_name),
            initialdir="C:\\"
        )
        
        if not target_path:
            return
        
        # 检查是否选择了根目录
        if len(target_path) <= 3:  # 如 "C:\" 
            messagebox.showerror(t("error"), t("cannot_migrate_to_root"))
            return
        
        # 创建目标文件夹路径
        target_folder_path = os.path.join(target_path, folder_key)
        
        # 确认迁移
        confirm_msg = t("confirm_migration", 
                       folder=folder_name,
                       current=current_path, 
                       target=target_folder_path)
        
        if not messagebox.askyesno(t("confirm_migration_title"), confirm_msg):
            return
        
        try:
            self.status_var.set(t("migrating_folder", folder=folder_name))
            self.dialog.update()
            
            # 执行迁移
            success = self.perform_migration(folder_key, current_path, target_folder_path)
            
            if success:
                messagebox.showinfo(t("success"), t("migration_completed", folder=folder_name))
                self.refresh_current_paths()
            else:
                messagebox.showerror(t("failed"), t("migration_failed", folder=folder_name))
                
        except Exception as e:
            messagebox.showerror(t("error"), t("migration_error", error=str(e)))
        finally:
            self.status_var.set(t("ready"))
    
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
            messagebox.showwarning(t("warning"), t("select_folder_first"))
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
            messagebox.showerror(t("error"), t("unrecognized_folder"))
            return
        
        # 计算默认路径
        username = os.environ.get('USERNAME', 'User')
        default_path = f"C:\\Users\\{username}\\{folder_key}"
        
        if current_path == default_path:
            messagebox.showinfo(t("info"), t("already_default_location", folder=folder_name))
            return
        
        # 确认恢复
        confirm_msg = t("confirm_restore",
                       folder=folder_name,
                       current=current_path,
                       default=default_path)
        
        if not messagebox.askyesno(t("confirm_restore_title"), confirm_msg):
            return
        
        try:
            self.status_var.set(t("restoring_folder", folder=folder_name))
            self.dialog.update()
            
            # 执行恢复
            success = self.perform_migration(folder_key, current_path, default_path)
            
            if success:
                messagebox.showinfo(t("success"), t("restore_completed", folder=folder_name))
                self.refresh_current_paths()
            else:
                messagebox.showerror(t("failed"), t("restore_failed", folder=folder_name))
                
        except Exception as e:
            messagebox.showerror(t("error"), t("restore_error", error=str(e)))
        finally:
            self.status_var.set(t("ready"))
    
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
    # 获取程序路径
    program_path = Path(__file__).parent
    
    # 初始化国际化
    init_i18n(program_path)
    
    # 改进的管理员权限检查
    if not is_admin():
        result = messagebox.askyesno(
            t("permission_prompt_title"), 
            t("permission_prompt_message")
        )
        if result:
            if run_as_admin():
                sys.exit(0)  # 成功启动管理员版本，退出当前进程
            else:
                messagebox.showerror(t("error"), t("permission_elevation_failed"))
        else:
            messagebox.showwarning(
                t("warning"), 
                t("permission_warning_message")
            )
    
    # 创建主窗口
    root = tk.Tk()
    admin_suffix = f" ({t('admin_mode')})" if is_admin() else f" ({t('normal_user_mode')})"
    root.title(t("app_title") + admin_suffix)
    
    # 创建应用程序实例
    app = CleanToolsGUI(root)
    
    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    main()