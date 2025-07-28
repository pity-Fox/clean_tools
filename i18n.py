# -*- coding: utf-8 -*-

import json
import os
from pathlib import Path

class I18n:
    def __init__(self, program_path, default_language='zh_CN'):
        self.program_path = Path(program_path)
        self.lang_path = self.program_path / "lang"
        self.current_language = default_language
        self.translations = {}
        self.fallback_translations = {}
        
        # 确保语言目录存在
        self.lang_path.mkdir(exist_ok=True)
        
        # 加载翻译
        self.load_translations()
    
    def load_translations(self):
        """加载翻译文件"""
        try:
            # 加载当前语言
            current_file = self.lang_path / f"{self.current_language}.json"
            if current_file.exists():
                with open(current_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
            
            # 加载中文作为后备语言
            if self.current_language != 'zh_CN':
                fallback_file = self.lang_path / "zh_CN.json"
                if fallback_file.exists():
                    with open(fallback_file, 'r', encoding='utf-8') as f:
                        self.fallback_translations = json.load(f)
        except Exception as e:
            print(f"加载语言文件时出错: {e}")
            self.translations = {}
            self.fallback_translations = {}
    
    def _(self, key, **kwargs):
        """获取翻译文本"""
        # 首先尝试当前语言
        text = self.translations.get(key)
        
        # 如果没有找到，尝试后备语言
        if text is None:
            text = self.fallback_translations.get(key)
        
        # 如果还是没有找到，返回键名
        if text is None:
            text = key
        
        # 处理格式化参数
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass
        
        return text
    
    def set_language(self, language_code):
        """设置语言"""
        if language_code != self.current_language:
            self.current_language = language_code
            self.load_translations()
            self.save_language_preference()
    
    def get_available_languages(self):
        """获取可用语言列表"""
        languages = {}
        
        # 扫描lang目录中的JSON文件
        if self.lang_path.exists():
            for file_path in self.lang_path.glob("*.json"):
                lang_code = file_path.stem
                
                # 语言代码到显示名称的映射
                language_names = {
                    'zh_CN': '简体中文',
                    'en_US': 'English',
                    'ja_JP': '日本語',
                    'fr_FR': 'Français',
                    'de_DE': 'Deutsch',
                    'es_ES': 'Español',
                    'ru_RU': 'Русский',
                    'ko_KR': '한국어',
                    'it_IT': 'Italiano',
                    'pt_BR': 'Português (Brasil)'
                }
                
                display_name = language_names.get(lang_code, lang_code)
                languages[lang_code] = display_name
        
        return languages
    
    def save_language_preference(self):
        """保存语言偏好设置"""
        try:
            config_file = self.program_path / "config.json"
            config = {}
            
            # 如果配置文件存在，先读取现有配置
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 更新语言设置
            config['language'] = self.current_language
            
            # 保存配置
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存语言偏好设置时出错: {e}")
    
    def load_language_preference(self):
        """加载语言偏好设置"""
        try:
            config_file = self.program_path / "config.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    saved_language = config.get('language', 'zh_CN')
                    if saved_language != self.current_language:
                        self.set_language(saved_language)
        except Exception as e:
            print(f"加载语言偏好设置时出错: {e}")

# 全局翻译器实例
_translator = None

def init_i18n(program_path, default_language='zh_CN'):
    """初始化国际化"""
    global _translator
    _translator = I18n(program_path, default_language)
    _translator.load_language_preference()

def get_translator():
    """获取翻译器实例"""
    return _translator

def t(key, **kwargs):
    """翻译函数的简写"""
    if _translator:
        return _translator._(key, **kwargs)
    return key