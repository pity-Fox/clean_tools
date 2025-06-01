#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import os
import sys
import ctypes
from pathlib import Path

# 导入自定义模块
try:
    from lib import CleanToolsCore
    from pass_module import SecurityManager
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

def is_admin():
    """检查是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """以管理员权限重新启动程序"""
    try:
        if sys.argv[-1] != 'asadmin':
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([script] + sys.argv[1:] + ['asadmin'])
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, params, None, 1
            )
            return True
    except Exception as e:
        print(f"申请管理员权限失败: {e}")
        return False
    return False

def request_admin_privileges():
    """申请管理员权限"""
    if not is_admin():
        # 显示权限申请对话框
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        result = messagebox.askyesno(
            "权限申请",
            "Clean Tools 需要管理员权限来执行系统清理操作。\n\n"
            "是否以管理员权限重新启动程序？\n\n"
            "注意：某些清理功能需要管理员权限才能正常工作。",
            icon="question"
        )
        
        root.destroy()
        
        if result:
            # 用户同意，尝试以管理员权限重启
            if run_as_admin():
                sys.exit(0)  # 退出当前进程
            else:
                # 重启失败，询问是否继续
                root = tk.Tk()
                root.withdraw()
                continue_result = messagebox.askyesno(
                    "权限申请失败",
                    "无法获取管理员权限。\n\n"
                    "是否继续以普通用户权限运行？\n\n"
                    "警告：某些功能可能无法正常工作。",
                    icon="warning"
                )
                root.destroy()
                
                if not continue_result:
                    sys.exit(1)
        else:
            # 用户拒绝，询问是否继续
            root = tk.Tk()
            root.withdraw()
            continue_result = messagebox.askyesno(
                "权限确认",
                "您选择不使用管理员权限。\n\n"
                "是否继续以普通用户权限运行？\n\n"
                "警告：某些清理功能可能无法正常工作。",
                icon="warning"
            )
            root.destroy()
            
            if not continue_result:
                sys.exit(1)
    
    return is_admin()

class CleanToolsGUI:
    def __init__(self, root):
        self.root = root
        self.root.geometry("950x750")
        self.root.resizable(True, True)
        
        # 检查管理员权限状态
        self.is_admin = is_admin()
        
        # 获取程序路径
        self.program_path = Path(os.path.dirname(os.path.abspath(sys.argv[0])))
        
        # 初始化核心组件
        self.core = CleanToolsCore(self.program_path)
        self.security = SecurityManager()
        
        # 当前选中的规则
        self.current_rule = None
        self.rules_data = {}
        
        # 创建界面
        self.create_widgets()
        self.load_rules()
        
    def create_widgets(self):
        """创建主界面"""
        # 主标题
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill="x", padx=10, pady=5)
        
        title_label = ttk.Label(title_frame, text="Clean Tools", 
                               font=("Arial", 24, "bold"))
        title_label.pack(side="left")
        
        # 权限状态显示
        if self.is_admin:
            status_label = ttk.Label(title_frame, text="🛡️ 管理员权限", 
                                   font=("Arial", 10), foreground="green")
        else:
            status_label = ttk.Label(title_frame, text="⚠️ 普通用户权限", 
                                   font=("Arial", 10), foreground="orange")
        status_label.pack(side="right")
        
        # 设置按钮
        settings_btn = ttk.Button(title_frame, text="设置", 
                                 command=self.open_settings)
        settings_btn.pack(side="right", padx=5)
        
        # 主要内容区域
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 左侧规则选择区域
        left_frame = ttk.LabelFrame(main_frame, text="清理规则")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # 规则列表
        self.rule_listbox = tk.Listbox(left_frame, height=8)
        self.rule_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.rule_listbox.bind("<<ListboxSelect>>", self.on_rule_select)
        
        # 规则操作按钮
        rule_btn_frame = ttk.Frame(left_frame)
        rule_btn_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(rule_btn_frame, text="新建规则", 
                  command=self.create_new_rule).pack(side="left", padx=2)
        ttk.Button(rule_btn_frame, text="编辑规则", 
                  command=self.edit_rule).pack(side="left", padx=2)
        ttk.Button(rule_btn_frame, text="删除规则", 
                  command=self.delete_rule).pack(side="left", padx=2)
        ttk.Button(rule_btn_frame, text="导入规则", 
                  command=self.import_rule).pack(side="left", padx=2)
        
        # 右侧规则信息和操作区域
        right_frame = ttk.LabelFrame(main_frame, text="规则信息")
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # 规则信息显示
        self.info_text = scrolledtext.ScrolledText(right_frame, height=10, 
                                                  state="disabled")
        self.info_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 清理操作区域
        clean_frame = ttk.LabelFrame(self.root, text="清理操作")
        clean_frame.pack(fill="x", padx=10, pady=5)
        
        # 清理按钮
        clean_btn_frame = ttk.Frame(clean_frame)
        clean_btn_frame.pack(fill="x", padx=5, pady=5)
        
        self.clean_btn = ttk.Button(clean_btn_frame, text="开始清理", 
                                   command=self.start_clean)
        self.clean_btn.pack(side="left", padx=5)
        
        ttk.Button(clean_btn_frame, text="清理日志", 
                  command=self.clear_logs).pack(side="left", padx=5)
        
        # 进度条
        progress_frame = ttk.Frame(clean_frame)
        progress_frame.pack(fill="x", padx=5, pady=5)
        
        self.progress = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.progress.pack(pady=5)
            
        # 日志显示区域
        log_frame = ttk.LabelFrame(self.root, text="操作日志")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
    def create_new_rule(self):
        """创建新规则"""
        dialog = RuleEditorDialog(self.root, "新建规则")
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            rule_name = dialog.result['Name']  # 改为大写N，与save_rule方法中的键名一致
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
        dialog = RuleEditorDialog(self.root, "编辑规则", rule_info)  # 添加title参数
        self.root.wait_window(dialog.dialog)  # 等待对话框关闭
        
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
            
            # 检测2：检查 info.cleantool 文件内容
            info_file = rule_dir / "info.cleantool"
            if info_file.exists():
                with open(info_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # 检测是否包含 random_key
                    if 'random_key' in content:
                        return True
                    
                    # 检测是否包含加密标识
                    if '此文件为加密文件' in content:
                        return True
            
            return False
            
        except Exception as e:
            # 如果检测过程出错，为安全起见返回True（禁止编辑）
            self.log(f"检测加密文件时出错: {str(e)}")
            return True
    
    def delete_rule(self):
        """删除规则"""
        if not self.current_rule:
            messagebox.showwarning("警告", "请先选择一个规则")
            return
            
        if messagebox.askyesno("确认", f"确定要删除规则 '{self.current_rule}' 吗？"):
            if self.core.delete_rule(self.current_rule):
                self.log(f"规则已删除: {self.current_rule}")
                self.load_rules()
                self.current_rule = None
                self.update_rule_info()
    
    def import_rule(self):
        """导入规则"""
        file_path = filedialog.askopenfilename(
            title="选择规则文件",
            filetypes=[("压缩文件", "*.zip"), ("所有文件", "*.*")]
        )
        
        if file_path and self.core.import_rule(file_path):
            self.log(f"规则导入成功: {file_path}")
            self.load_rules()
    
    def start_clean(self):
        """开始清理"""
        if not self.current_rule:
            messagebox.showwarning("警告", "请先选择一个规则")
            return
        
        # 检查规则是否被篡改或无法验证
        rule_info = self.rules_data[self.current_rule]
        
        # 检查是否无法验证
        if rule_info.get('cannot_verify', False):
            error_msg = f"安全限制: 无法验证规则文件的完整性，禁止执行清理操作！\n\n" \
                       f"原因: {rule_info.get('integrity_message', '未知错误')}\n\n" \
                       f"建议: 请重新导入或创建该规则。"
            self.log(f"[安全阻止] 尝试执行无法验证的规则: {self.current_rule}")
            messagebox.showerror("安全错误", error_msg)
            return
        
        # 检查是否被篡改
        if rule_info.get('is_tampered', False):
            error_msg = f"安全限制: 检测到规则文件被篡改，禁止执行清理操作！\n\n" \
                       f"篡改详情: {rule_info.get('integrity_message', '未知错误')}\n\n" \
                       f"建议: 请重新导入或创建该规则。"
            self.log(f"[安全阻止] 尝试执行被篡改的规则: {self.current_rule}")
            messagebox.showerror("安全错误", error_msg)
            return
        
        # 对于加密文件，再次验证完整性
        if rule_info.get('is_encrypted', False):
            try:
                rule_dir = rule_info['rule_dir']
                integrity_file = rule_dir / "rule.integrity"
                
                if integrity_file.exists():
                    original_author = rule_info.get('Auther', 'Unknown')
                    if '*' in original_author:  # 作者名被掩码，无法验证
                        error_msg = f"安全限制: 无法验证加密文件的完整性（作者名已掩码），禁止执行清理操作！\n\n" \
                                   f"建议: 请联系原作者或重新创建规则。"
                        self.log(f"[安全阻止] 尝试执行无法验证的加密规则: {self.current_rule}")
                        messagebox.showerror("安全错误", error_msg)
                        return
                    else:
                        # 执行前最后一次验证
                        is_valid, message = self.core.security_manager.verify_integrity(rule_dir, original_author)
                        if not is_valid:
                            error_msg = f"安全限制: 执行前检测到文件篡改！\n\n" \
                                       f"篡改详情: {message}\n\n" \
                                       f"建议: 请重新导入或创建该规则。"
                            self.log(f"[安全阻止] 执行前检测到规则篡改: {self.current_rule} - {message}")
                            messagebox.showerror("安全错误", error_msg)
                            return
            except Exception as e:
                error_msg = f"安全限制: 安全验证失败，禁止执行清理操作！\n\n" \
                           f"错误详情: {str(e)}\n\n" \
                           f"建议: 请检查文件完整性或重新创建规则。"
                self.log(f"[安全阻止] 安全验证异常: {self.current_rule} - {str(e)}")
                messagebox.showerror("安全错误", error_msg)
                return
            
        # 记录开始执行的日志
        self.log(f"[安全通过] 开始执行已验证的规则: {self.current_rule}")
        
        self.clean_btn.config(state="disabled")
        self.progress['value'] = 0
        self.progress.start(10)
        
        try:
            success = self.core.execute_clean_rule(rule_info, self.log_callback)
            
            if success:
                self.log("清理完成")
                messagebox.showinfo("完成", "清理操作已完成")
            else:
                messagebox.showerror("错误", "清理过程中出现错误")
                
        except Exception as e:
            self.log(f"清理过程出错: {str(e)}")
            messagebox.showerror("错误", f"清理失败: {str(e)}")
        finally:
            self.clean_btn.config(state="normal")
            self.progress.stop()
    
    def clear_logs(self):
        """清理日志"""
        if self.core.clear_logs():
            self.log_text.delete(1.0, tk.END)
            self.log("日志已清理")
            messagebox.showinfo("成功", "日志清理完成")
    
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
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        
        # 同时写入日志文件
        self.core.write_log(log_message)
    
    def open_settings(self):
        """打开设置"""
        SettingsDialog(self.root)

class RuleEditorDialog:
    def __init__(self, parent, title, rule_data=None):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("550x650")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.create_widgets(rule_data)
        
    def create_widgets(self, rule_data):
        """创建对话框控件"""
        # 基本信息
        info_frame = ttk.LabelFrame(self.dialog, text="规则信息")
        info_frame.pack(fill="x", padx=10, pady=5)
        
        # 规则名称
        ttk.Label(info_frame, text="规则名称:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.name_entry = ttk.Entry(info_frame, width=40)
        self.name_entry.grid(row=0, column=1, padx=5, pady=2)
        
        # 版本
        ttk.Label(info_frame, text="版本:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.version_entry = ttk.Entry(info_frame, width=40)
        self.version_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # 作者
        ttk.Label(info_frame, text="作者:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.author_entry = ttk.Entry(info_frame, width=40)
        self.author_entry.grid(row=2, column=1, padx=5, pady=2)
        
        # 在作者输入框后添加加密选项
        # 加密选项
        encrypt_frame = ttk.LabelFrame(self.dialog, text="安全选项")
        encrypt_frame.pack(fill="x", padx=10, pady=5)
        
        self.encrypt_var = tk.BooleanVar()
        encrypt_check = ttk.Checkbutton(encrypt_frame, text="启用规则加密保护(注意:一但启用该保护文件将不能被修改!!(至少此程序改不了))", 
                                       variable=self.encrypt_var)
        encrypt_check.pack(anchor="w", padx=5, pady=5)
        
        # 加密说明
        encrypt_info = ttk.Label(encrypt_frame, 
                                text="⚠️ 启用加密后，将使用作者名作为密钥保护规则文件",
                                font=("Arial", 9))
        encrypt_info.pack(anchor="w", padx=5, pady=2)
        
        # 描述
        ttk.Label(info_frame, text="描述:").grid(row=3, column=0, sticky="nw", padx=5, pady=2)
        self.info_text = tk.Text(info_frame, width=40, height=3)
        self.info_text.grid(row=3, column=1, padx=5, pady=2)
        
        # 规则内容
        rules_frame = ttk.LabelFrame(self.dialog, text="清理规则")
        rules_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 规则说明
        help_text = "规则格式说明:\n" \
                   "cl <路径> - 清理指定路径的文件或文件夹\n" \
                   "system <命令> - 执行系统命令\n" \
                   "# 开头的行为注释"
        ttk.Label(rules_frame, text=help_text, font=("Consolas", 9)).pack(anchor="w", padx=5, pady=2)
        
        self.rules_text = scrolledtext.ScrolledText(rules_frame, height=15)
        self.rules_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 按钮
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(btn_frame, text="保存", command=self.save_rule).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side="right")
        
        # 填充现有数据
        if rule_data:
            self.name_entry.insert(0, rule_data.get('Name', ''))
            self.version_entry.insert(0, rule_data.get('version', '1.0'))
            self.author_entry.insert(0, rule_data.get('Auther', ''))
            self.info_text.insert(1.0, rule_data.get('information', ''))
            
            # 加载规则内容
            rule_file = rule_data.get('rule_file')
            if rule_file and rule_file.exists():
                try:
                    with open(rule_file, 'r', encoding='utf-8') as f:
                        self.rules_text.insert(1.0, f.read())
                except:
                    pass
        else:
            self.version_entry.insert(0, "1.0")
            
    def save_rule(self):
        """保存规则"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("错误", "请输入规则名称")
            return
            
        author = self.author_entry.get().strip() or 'Unknown'
        
        # 检查加密选项
        if self.encrypt_var.get() and author == 'Unknown':
            messagebox.showerror("错误", "启用加密时必须输入作者名（用作加密密钥）")
            return
            
        self.result = {
            'Name': name,
            'version': self.version_entry.get().strip() or '1.0',
            'Auther': author,
            'information': self.info_text.get(1.0, tk.END).strip() or 'none',
            'rules': self.rules_text.get(1.0, tk.END).strip(),
            'encrypted': self.encrypt_var.get()  # 添加加密标志
        }
        
        self.dialog.destroy()

class SettingsDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("设置")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 100))
        
        self.create_widgets()
        
    def create_widgets(self):
        """创建设置界面"""
        # 设置选项
        settings_frame = ttk.LabelFrame(self.dialog, text="设置选项")
        settings_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ttk.Button(settings_frame, text="关于程序", 
                  command=self.show_about).pack(pady=10)
        
        # 关闭按钮
        ttk.Button(self.dialog, text="关闭", 
                  command=self.dialog.destroy).pack(pady=10)
    
    def show_about(self):
        """显示关于信息"""
        about_text = "Clean Tools v4.0 GUI\n\n" \
                    "一个功能强大的系统清理工具\n\n" \
                    "作者: Clstone\n" \
                    "哔哩哔哩:氯堡拾稿(bili_35253359115)"
                    
        messagebox.showinfo("关于 Clean Tools", about_text)

def check_file_integrity():
    """检查文件完整性"""
    required_files = {
        'lib.py': '核心逻辑库',
        'pass_module.py': '加密模块'
    }
    
    missing_files = []
    for file_name, description in required_files.items():
        if not Path(file_name).exists():
            missing_files.append(f"{file_name} ({description})")
    
    if missing_files:
        error_msg = "程序启动失败！\n\n缺少以下必要文件:\n\n" + "\n".join(missing_files)
        error_msg += "\n\n请确保所有文件都在同一目录下。"
        
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("文件完整性检查失败", error_msg)
        root.destroy()
        return False
    
    return True

def main():
    """主函数"""
    # 申请管理员权限
    admin_status = request_admin_privileges()
    
    # 检查文件完整性
    if not check_file_integrity():
        sys.exit(1)
    
    # 检查加密库依赖
    try:
        from Crypto.Cipher import AES
    except ImportError:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "依赖缺失", 
            "缺少加密库依赖！\n\n请安装 pycryptodome:\n\npip install pycryptodome"
        )
        root.destroy()
        return
    
    # 启动主程序
    root = tk.Tk()
    app = CleanToolsGUI(root)
    
    # 在标题栏显示权限状态
    if admin_status:
        root.title("Clean Tools - 安全清理工具 [管理员权限]")
    else:
        root.title("Clean Tools - 安全清理工具 [普通用户权限]")
    
    root.mainloop()

if __name__ == "__main__":
    main()


def manage_encrypted_rules(self):
    """管理加密规则"""
    messagebox.showinfo("加密管理", "加密规则管理功能")

def decrypt_rule(self):
    """解密规则"""
    messagebox.showinfo("解密规则", "规则解密功能")

# 删除check_update方法，添加新的compress_rules方法
def compress_rules(self):
    """压缩rule目录下的所有文件"""
    import zipfile
    import os
    from datetime import datetime
    
    try:
        # 获取当前时间作为文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"rules_backup_{timestamp}.zip"
        zip_path = os.path.join(os.getcwd(), zip_filename)
        
        rule_dir = "rule"
        if not os.path.exists(rule_dir):
            messagebox.showwarning("警告", "rule目录不存在")
            return
            
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(rule_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.getcwd())
                    zipf.write(file_path, arcname)
        
        messagebox.showinfo("成功", f"规则目录已压缩完成！\n压缩包路径: {zip_path}")
        
    except Exception as e:
        messagebox.showerror("错误", f"压缩失败: {str(e)}")