#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import hashlib
import hmac
import secrets
import struct
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

class SecurityManager:
    """安全管理器 - 处理规则文件的加密和完整性校验"""
    
    def __init__(self):
        self.salt_size = 32
        self.key_size = 32  # AES-256
        self.iv_size = 16
        self.tag_size = 16
        self.iterations = 100000
    
    def generate_key(self, password: str, salt: bytes) -> bytes:
        """使用PBKDF2生成密钥"""
        return PBKDF2(password, salt, self.key_size, count=self.iterations, hmac_hash_module=SHA256)
    
    def encrypt_data(self, data: bytes, password: str) -> bytes:
        """加密数据"""
        try:
            # 生成随机盐值和IV
            salt = get_random_bytes(self.salt_size)
            iv = get_random_bytes(self.iv_size)
            
            # 生成密钥
            key = self.generate_key(password, salt)
            
            # AES-GCM加密
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
            ciphertext, tag = cipher.encrypt_and_digest(data)
            
            # 组合所有数据：盐值 + IV + 标签 + 密文
            encrypted_data = salt + iv + tag + ciphertext
            
            return encrypted_data
            
        except Exception as e:
            raise Exception(f"加密失败: {str(e)}")
    
    def decrypt_data(self, encrypted_data: bytes, password: str) -> bytes:
        """解密数据"""
        try:
            # 提取各部分
            salt = encrypted_data[:self.salt_size]
            iv = encrypted_data[self.salt_size:self.salt_size + self.iv_size]
            tag = encrypted_data[self.salt_size + self.iv_size:self.salt_size + self.iv_size + self.tag_size]
            ciphertext = encrypted_data[self.salt_size + self.iv_size + self.tag_size:]
            
            # 生成密钥
            key = self.generate_key(password, salt)
            
            # AES-GCM解密
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
            data = cipher.decrypt_and_verify(ciphertext, tag)
            
            return data
            
        except Exception as e:
            raise Exception(f"解密失败: {str(e)}")
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """计算文件SHA-256哈希"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            raise Exception(f"计算文件哈希失败: {str(e)}")
    
    def create_integrity_file(self, rule_file_path: Path, info_file_path: Path, 
                            author_name: str) -> Path:
        """创建完整性校验文件"""
        try:
            # 计算文件哈希
            rule_hash = self.calculate_file_hash(rule_file_path)
            info_hash = self.calculate_file_hash(info_file_path)
            
            # 获取文件大小
            rule_size = rule_file_path.stat().st_size
            info_size = info_file_path.stat().st_size
            
            # 创建完整性数据
            integrity_data = {
                'rule_file': {
                    'hash': rule_hash,
                    'size': rule_size,
                    'path': str(rule_file_path.name)
                },
                'info_file': {
                    'hash': info_hash,
                    'size': info_size,
                    'path': str(info_file_path.name)
                },
                'author': author_name,
                'timestamp': str(int(os.path.getmtime(rule_file_path)))
            }
            
            # 序列化数据
            import json
            json_data = json.dumps(integrity_data, sort_keys=True).encode('utf-8')
            
            # 使用作者名作为密钥加密
            encrypted_data = self.encrypt_data(json_data, author_name)
            
            # 保存到.integrity文件
            integrity_file = rule_file_path.parent / f"{rule_file_path.stem}.integrity"
            with open(integrity_file, 'wb') as f:
                f.write(encrypted_data)
            
            return integrity_file
            
        except Exception as e:
            raise Exception(f"创建完整性文件失败: {str(e)}")
    
    def verify_integrity(self, rule_dir: Path, author_name: str) -> tuple:
        """验证文件完整性"""
        try:
            rule_file = rule_dir / "rule.clean"
            info_file = rule_dir / "info.cleantool"
            integrity_file = rule_dir / "rule.integrity"
            
            # 检查文件是否存在
            if not all(f.exists() for f in [rule_file, info_file, integrity_file]):
                return False, "缺少必要文件"
            
            # 读取完整性文件
            with open(integrity_file, 'rb') as f:
                encrypted_data = f.read()
            
            # 解密完整性数据
            try:
                json_data = self.decrypt_data(encrypted_data, author_name)
                import json
                integrity_data = json.loads(json_data.decode('utf-8'))
            except:
                return False, "完整性文件已损坏或密钥错误"
            
            # 验证规则文件
            current_rule_hash = self.calculate_file_hash(rule_file)
            current_rule_size = rule_file.stat().st_size
            
            if (current_rule_hash != integrity_data['rule_file']['hash'] or 
                current_rule_size != integrity_data['rule_file']['size']):
                return False, "规则文件已被篡改"
            
            # 验证信息文件
            current_info_hash = self.calculate_file_hash(info_file)
            current_info_size = info_file.stat().st_size
            
            if (current_info_hash != integrity_data['info_file']['hash'] or 
                current_info_size != integrity_data['info_file']['size']):
                return False, "信息文件已被篡改"
            
            return True, "文件完整性验证通过"
            
        except Exception as e:
            return False, f"验证过程出错: {str(e)}"
    
    def create_secure_rule(self, rule_dir: Path, rule_data: dict) -> bool:
        """创建安全规则"""
        try:
            # 创建规则目录
            rule_dir.mkdir(exist_ok=True)
            
            # 处理作者名遮蔽
            original_author = rule_data['Auther']
            if len(original_author) <= 1:
                masked_author = "*"
            elif len(original_author) == 2:
                masked_author = original_author[0] + "*"
            else:
                # 保留第一个字符，其余用*替换
                masked_author = original_author[0] + "*" * (len(original_author) - 1)
            
            # 添加加密标识
            encrypted_author_info = f"{masked_author} - 此文件为加密文件"
            
            # 保存info.cleantool
            info_file = rule_dir / "info.cleantool"
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write(f"Name\n{{\n    {rule_data['Name']}\n}}\n")
                f.write(f"version\n{{\n    {rule_data['version']}\n}}\n")
                f.write(f"Auther\n{{\n    {encrypted_author_info}\n}}\n")
                f.write(f"information\n{{\n    {rule_data['information']}\n}}\n")
                
                # 添加随机密钥（明钥）
                random_key = secrets.token_hex(16)
                f.write(f"random_key\n{{\n    {random_key}\n}}\n")
            
            # 保存rule.clean
            rule_file = rule_dir / "rule.clean"
            with open(rule_file, 'w', encoding='utf-8') as f:
                f.write(rule_data['rules'])
            
            # 创建完整性校验文件（使用原始作者名作为密钥）
            self.create_integrity_file(rule_file, info_file, original_author)
            
            return True
            
        except Exception as e:
            print(f"创建安全规则失败: {str(e)}")
            return False
    
    def get_security_status(self, rules_data: dict) -> dict:
        """获取所有规则的安全状态"""
        status = {
            'total_rules': len(rules_data),
            'secure_rules': 0,
            'compromised_rules': [],
            'missing_integrity': []
        }
        
        for rule_name, rule_info in rules_data.items():
            rule_dir = rule_info.get('rule_dir')
            author = rule_info.get('Auther', 'Unknown')
            
            if rule_dir:
                integrity_file = rule_dir / "rule.integrity"
                if integrity_file.exists():
                    is_valid, message = self.verify_integrity(rule_dir, author)
                    if is_valid:
                        status['secure_rules'] += 1
                    else:
                        status['compromised_rules'].append({
                            'name': rule_name,
                            'reason': message
                        })
                else:
                    status['missing_integrity'].append(rule_name)
        
        return status