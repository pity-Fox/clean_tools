# -*- coding: utf-8 -*-

import os
import sys
import shutil
import json
import zipfile
import tempfile
import subprocess
import datetime
from pathlib import Path
from tkinter import messagebox
from pass_module import SecurityManager

class CleanToolsCore:
    def __init__(self, program_path):
        self.program_path = Path(program_path)
        self.rule_path = self.program_path / "rule"
        self.logs_path = self.program_path / "logs"
        self.security_manager = SecurityManager()
        
        # 确保必要目录存在
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        self.rule_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)
    
    def save_rule(self, rule_data, rule_name=None):
        """保存规则"""
        try:
            if not rule_name:
                rule_name = rule_data['Name'].replace(' ', '_')
                
            rule_dir = self.rule_path / rule_name
            rule_dir.mkdir(exist_ok=True)
            
            # 检查是否需要加密
            if rule_data.get('encrypted', False):
                # 使用加密方式保存
                if self.security_manager.create_secure_rule(rule_dir, rule_data):
                    return str(rule_dir)
                else:
                    raise Exception("加密保存失败")
            else:
                # 普通方式保存
                # 保存info.cleantool
                info_file = rule_dir / "info.cleantool"
                with open(info_file, 'w', encoding='utf-8') as f:
                    f.write(f"Name\n{{\n    {rule_data['Name']}\n}}\n")
                    f.write(f"version\n{{\n    {rule_data['version']}\n}}\n")
                    f.write(f"Auther\n{{\n    {rule_data['Auther']}\n}}\n")
                    f.write(f"information\n{{\n    {rule_data['information']}\n}}\n")
                    
                # 保存rule.clean
                rule_file = rule_dir / "rule.clean"
                with open(rule_file, 'w', encoding='utf-8') as f:
                    f.write(rule_data['rules'])
            
            return str(rule_dir)
            
        except Exception as e:
            messagebox.showerror("错误", f"保存规则失败: {str(e)}")
            return None
    
    def delete_rule(self, rule_name):
        """删除规则"""
        try:
            rule_dir = self.rule_path / rule_name.replace(' ', '_')
            if rule_dir.exists():
                shutil.rmtree(rule_dir)
                return True
        except Exception as e:
            messagebox.showerror("错误", f"删除规则失败: {str(e)}")
        return False
    
    def import_rule(self, file_path):
        """导入规则"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_ref.extractall(temp_dir)
                    
                    temp_path = Path(temp_dir)
                    imported_count = 0
                    
                    for item in temp_path.iterdir():
                        if item.is_dir():
                            info_file = item / "info.cleantool"
                            rule_file = item / "rule.clean"
                            
                            if info_file.exists() and rule_file.exists():
                                target_dir = self.rule_path / item.name
                                if target_dir.exists():
                                    if not messagebox.askyesno("确认", f"规则 '{item.name}' 已存在，是否覆盖？"):
                                        continue
                                    shutil.rmtree(target_dir)
                                
                                shutil.copytree(item, target_dir)
                                imported_count += 1
                    
                    if imported_count > 0:
                        messagebox.showinfo("成功", f"成功导入 {imported_count} 个规则")
                        return True
                    else:
                        messagebox.showwarning("警告", "未找到有效的规则文件")
                        
        except Exception as e:
            messagebox.showerror("错误", f"导入规则失败: {str(e)}")
        return False
    
    def load_rules(self):
        """加载规则列表"""
        rules_data = {}
        
        if not self.rule_path.exists():
            return rules_data
            
        for rule_dir in self.rule_path.iterdir():
            if rule_dir.is_dir():
                info_file = rule_dir / "info.cleantool"
                rule_file = rule_dir / "rule.clean"
                integrity_file = rule_dir / "rule.integrity"
                
                if info_file.exists():
                    try:
                        rule_info = self.parse_info_file(info_file)
                        rule_info['rule_dir'] = rule_dir
                        rule_info['rule_file'] = rule_file
                        
                        # 检查是否为加密文件
                        is_encrypted = False
                        tampered = False
                        cannot_verify = False
                        
                        # 检测加密标识
                        try:
                            with open(info_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if (integrity_file.exists() or 
                                    'random_key' in content or 
                                    '此文件为加密文件' in content):
                                    is_encrypted = True
                        except:
                            pass
                        
                        # 如果是加密文件，进行完整性验证
                        if is_encrypted and integrity_file.exists():
                            try:
                                # 获取原始作者名（去除*号掩码）
                                original_author = rule_info.get('Auther', 'Unknown')
                                if '*' in original_author:
                                    # 无法验证的情况
                                    cannot_verify = True
                                    log_message = f"安全警告: 无法验证加密文件 {rule_dir.name} 的完整性 - 作者名已被掩码，禁止执行清理操作"
                                    print(log_message)
                                    self.write_log(f"[安全警告] {log_message}\n")
                                    rule_info['integrity_status'] = 'cannot_verify'
                                    rule_info['integrity_message'] = '无法验证 - 作者名已掩码，禁止执行'
                                else:
                                    # 验证文件完整性
                                    is_valid, message = self.security_manager.verify_integrity(rule_dir, original_author)
                                    rule_info['integrity_status'] = 'valid' if is_valid else 'tampered'
                                    rule_info['integrity_message'] = message
                                    
                                    if not is_valid:
                                        tampered = True
                                        log_message = f"安全警告: 检测到文件篡改 {rule_dir.name} - {message}，禁止执行清理操作"
                                        print(log_message)
                                        self.write_log(f"[安全警告] {log_message}\n")
                            except Exception as e:
                                cannot_verify = True
                                log_message = f"安全警告: 完整性验证出错 {rule_dir.name}: {str(e)}，禁止执行清理操作"
                                print(log_message)
                                self.write_log(f"[安全警告] {log_message}\n")
                                rule_info['integrity_status'] = 'error'
                                rule_info['integrity_message'] = f'验证出错: {str(e)}，禁止执行'
                        
                        rule_info['is_encrypted'] = is_encrypted
                        rule_info['is_tampered'] = tampered
                        rule_info['cannot_verify'] = cannot_verify
                        
                        # 加载所有规则到列表中（包括无法验证的），但标记状态
                        rule_name = rule_info['Name']
                        rules_data[rule_name] = rule_info
                        
                        # 记录跳过的规则
                        if tampered:
                            log_message = f"规则 {rule_dir.name} 已被篡改，已加载但禁止执行"
                            print(log_message)
                            self.write_log(f"[安全提示] {log_message}\n")
                        elif cannot_verify:
                            log_message = f"规则 {rule_dir.name} 无法验证完整性，已加载但禁止执行"
                            print(log_message)
                            self.write_log(f"[安全提示] {log_message}\n")
                            
                    except Exception as e:
                        log_message = f"加载规则失败 {rule_dir.name}: {str(e)}"
                        print(log_message)
                        self.write_log(f"[错误] {log_message}\n")
        
        return rules_data
    
    def parse_info_file(self, info_file):
        """解析info.cleantool文件"""
        rule_info = {
            'Name': 'Unknown',
            'version': '1.0',
            'Auther': 'Unknown',
            'information': 'none'
        }
        
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            lines = content.split('\n')
            current_key = None
            current_value = []
            
            for line in lines:
                line = line.strip()
                if line in ['Name', 'version', 'Auther', 'information']:
                    if current_key:
                        rule_info[current_key] = '\n'.join(current_value).strip()
                    current_key = line
                    current_value = []
                elif line and not line.startswith('{') and not line.startswith('}'):
                    current_value.append(line)
            
            if current_key:
                rule_info[current_key] = '\n'.join(current_value).strip()
                
        except Exception as e:
            print(f"解析info文件失败: {e}")
            
        return rule_info
    
    def format_rule_info(self, rule_info):
        """格式化规则信息显示"""
        info_text = f"规则名称: {rule_info['Name']}\n"
        info_text += f"版本: {rule_info['version']}\n"
        info_text += f"作者: {rule_info['Auther']}\n"
        info_text += f"描述: {rule_info['information']}\n\n"
        
        # 显示规则内容
        rule_file = rule_info.get('rule_file')
        if rule_file and rule_file.exists():
            try:
                with open(rule_file, 'r', encoding='utf-8') as f:
                    rules_content = f.read()
                info_text += "规则内容:\n" + rules_content
            except:
                info_text += "无法读取规则内容"
        
        return info_text
    
    def execute_clean_rule(self, rule_info, log_callback=None, progress_callback=None):
        """执行清理规则"""
        try:
            rule_file = rule_info.get('rule_file')
            if not rule_file or not rule_file.exists():
                if log_callback:
                    log_callback("规则文件不存在")
                return False
            
            if log_callback:
                log_callback(f"开始执行清理规则: {rule_info['Name']}")
            
            with open(rule_file, 'r', encoding='utf-8') as f:
                rules = f.readlines()
            
            total_rules = len([line for line in rules if line.strip() and not line.strip().startswith('#')])
            current_rule = 0
            
            for line in rules:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                try:
                    current_rule += 1
                    progress = int((current_rule / total_rules) * 100) if total_rules > 0 else 0
                    
                    if progress_callback:
                        progress_callback(progress, "🧹 清理中", f"处理规则 {current_rule}/{total_rules}")
                    
                    if line.startswith('cl '):
                        # 清理路径
                        path = line[3:].strip()
                        self.clean_path(path, log_callback)
                    elif line.startswith('system '):
                        # 执行系统命令
                        command = line[7:].strip()
                        self.execute_system_command(command, log_callback)
                    else:
                        if log_callback:
                            log_callback(f"未知规则格式: {line}")
                        
                except Exception as e:
                    if log_callback:
                        log_callback(f"执行规则失败 '{line}': {str(e)}")
            
            return True
            
        except Exception as e:
            if log_callback:
                log_callback(f"执行规则时出错: {str(e)}")
            return False
    
    def clean_path(self, path, log_callback):
        """清理指定路径"""
        try:
            path_obj = Path(path)
            if path_obj.exists():
                if path_obj.is_file():
                    path_obj.unlink()
                    if log_callback:
                        log_callback(f"已删除文件: {path}")
                elif path_obj.is_dir():
                    # 删除目录中的所有文件，但保留目录结构
                    for item in path_obj.rglob('*'):
                        if item.is_file():
                            try:
                                item.unlink()
                            except:
                                pass
                    if log_callback:
                        log_callback(f"已清理目录: {path}")
            else:
                if log_callback:
                    log_callback(f"路径不存在: {path}")
        except Exception as e:
            if log_callback:
                log_callback(f"清理路径失败 {path}: {str(e)}")
    
    def execute_system_command(self, command, log_callback):
        """执行系统命令"""
        try:
            if log_callback:
                log_callback(f"执行命令: {command}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                if log_callback:
                    log_callback(f"命令执行成功")
                    if result.stdout:
                        log_callback(f"输出: {result.stdout.strip()}")
            else:
                if log_callback:
                    log_callback(f"命令执行失败，返回码: {result.returncode}")
                    if result.stderr:
                        log_callback(f"错误: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            if log_callback:
                log_callback(f"命令执行超时: {command}")
        except Exception as e:
            if log_callback:
                log_callback(f"执行命令失败 {command}: {str(e)}")
    
    def clear_logs(self):
        """清理日志"""
        try:
            if self.logs_path.exists():
                shutil.rmtree(self.logs_path)
            self.logs_path.mkdir(exist_ok=True)
            return True
        except Exception as e:
            messagebox.showerror("错误", f"清理日志失败: {str(e)}")
            return False
    
    def write_log(self, message):
        """写入日志文件"""
        try:
            log_file = self.logs_path / "clean.log"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(message)
        except:
            pass
    
    def get_pagefile_info(self):
        """获取页面文件信息"""
        try:
            result = subprocess.run(
                'wmic pagefile list /format:list',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout
            return "无法获取页面文件信息"
        except Exception as e:
            return f"获取页面文件信息失败: {str(e)}"
    
    def set_pagefile(self, drive, initial_size, max_size, system_managed=False):
        """设置页面文件"""
        try:
            if system_managed:
                # 启用系统管理的页面文件
                command = f'wmic pagefileset where name="{drive}:\\pagefile.sys" set InitialSize=0,MaximumSize=0'
            else:
                # 设置自定义大小
                command = f'wmic pagefileset where name="{drive}:\\pagefile.sys" set InitialSize={initial_size},MaximumSize={max_size}'
            
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            return result.returncode == 0, result.stderr if result.returncode != 0 else "设置成功"
        except Exception as e:
            return False, str(e)
    
    def disable_pagefile(self, drive):
        """禁用页面文件"""
        try:
            command = f'wmic pagefileset where name="{drive}:\\pagefile.sys" delete'
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            return result.returncode == 0, result.stderr if result.returncode != 0 else "禁用成功"
        except Exception as e:
            return False, str(e)
    
    def get_hibernate_status(self):
        """获取休眠状态"""
        try:
            result = subprocess.run(
                'powercfg /query SCHEME_CURRENT SUB_SLEEP HIBERNATEIDLE',
                shell=True, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout
            return "无法获取休眠状态"
        except Exception as e:
            return f"获取休眠状态失败: {str(e)}"
    
    def set_hibernate(self, enable=True):
        """启用或禁用休眠"""
        try:
            command = 'powercfg /hibernate on' if enable else 'powercfg /hibernate off'
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            return result.returncode == 0, result.stderr if result.returncode != 0 else ("休眠已启用" if enable else "休眠已禁用")
        except Exception as e:
            return False, str(e)