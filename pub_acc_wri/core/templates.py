#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 12:54
"""模板管理 - 从rules目录加载规则"""

from typing import Dict, Any, List, Optional
import yaml
from pathlib import Path


class TemplateManager:
    """模板管理器，从rules目录加载文体结构和风格规则"""

    def __init__(self, rules_dir: str = "./rules"):
        self.rules_dir = Path(rules_dir)
        self.genre_templates = {}
        self.style_rules = {}
        self.review_rules = {}

        self._load_templates()

    def _load_templates(self):
        """从YAML文件加载模板"""
        # 加载文体模板
        genre_file = self.rules_dir / "genre_templates.yaml"
        if genre_file.exists():
            with open(genre_file, 'r', encoding='utf-8') as f:
                self.genre_templates = yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"找不到规则文件: {genre_file}")

        # 加载风格规则
        style_file = self.rules_dir / "style_rules.yaml"
        if style_file.exists():
            with open(style_file, 'r', encoding='utf-8') as f:
                self.style_rules = yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"找不到规则文件: {style_file}")

        # 加载复审规则
        review_file = self.rules_dir / "review_rules.yaml"
        if review_file.exists():
            with open(review_file, 'r', encoding='utf-8') as f:
                self.review_rules = yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"找不到规则文件: {review_file}")

    def get_genre_template(self, genre: str) -> Dict:
        """获取指定文体的模板"""
        return self.genre_templates.get(genre, self.genre_templates.get("现象说理", {}))

    def get_style_rules(self, style: str) -> Dict:
        """获取指定风格的规则"""
        return self.style_rules.get(style, self.style_rules.get("官媒沉稳风", {}))

    def get_review_rules(self, mode: str) -> Dict:
        """获取指定模式的复审规则"""
        return self.review_rules.get(mode, self.review_rules.get("standard", {}))

    def list_genres(self) -> List[str]:
        """列出所有文体"""
        return list(self.genre_templates.keys())

    def list_styles(self) -> List[str]:
        """列出所有风格"""
        return list(self.style_rules.keys())

    def reload(self):
        """重新加载规则"""
        self._load_templates()


# 全局实例
_default_manager = None

def get_template_manager() -> TemplateManager:
    """获取全局模板管理器实例"""
    global _default_manager
    if _default_manager is None:
        _default_manager = TemplateManager()
    return _default_manager