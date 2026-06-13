#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 12:58

"""基础Agent类和通用工具 - 使用抽象LLM客户端"""

import json
import re
from typing import Dict, Any, List, Optional
# from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from pathlib import Path
import yaml
from utils.logger_config import logger
from pydantic import BaseModel, Field

# 加载规则（从rules目录）
def load_rules():
    """从rules目录加载所有规则"""
    rules_dir = Path(__file__).parent.parent / "rules"

    with open(rules_dir / "genre_templates.yaml", 'r', encoding='utf-8') as f:
        genre_templates = yaml.safe_load(f)

    with open(rules_dir / "style_rules.yaml", 'r', encoding='utf-8') as f:
        style_rules = yaml.safe_load(f)

    with open(rules_dir / "review_rules.yaml", 'r', encoding='utf-8') as f:
        review_rules = yaml.safe_load(f)

    with open(rules_dir / "title_strategy.yaml", 'r', encoding='utf-8') as f:
        title_rules = yaml.safe_load(f)
    return genre_templates, style_rules, review_rules, title_rules


# 全局规则
GENRE_TEMPLATES, STYLE_RULES, REVIEW_RULES, TITLE_RULES = load_rules()

# @dataclass
# class AgentContext:
#     """Agent执行的上下文，贯穿整个流程"""
#     topic = ""
#     user_input = field(default_factory=dict)
#     classification = field(default_factory=dict)
#     elevation = field(default_factory=dict)
#     outline = field(default_factory=dict)
#     materials = field(default_factory=list)
#     draft = ""
#     polished = ""
#     review = field(default_factory=dict)
#     final_article = ""
#
#     def to_dict(self):
#         return {
#             "topic": self.topic,
#             "user_input": self.user_input,
#             "classification": self.classification,
#             "elevation": self.elevation,
#             "outline": self.outline,
#             "materials": self.materials,
#             "draft": self.draft,
#             "polished": self.polished,
#             "review": self.review,
#             "final_article": self.final_article
#         }


class AgentContext(BaseModel):
    """Agent执行的上下文，贯穿整个流程"""
    topic: str = ""
    user_input: Dict[str, Any] = Field(default_factory=dict)
    classification: Dict[str, str] = Field(default_factory=dict)
    title: str = ""
    # outline_template: Dict[str, Any] = Field(default_factory=dict)
    # style_rules: Dict[str, Any] = Field(default_factory=dict)
    elevation: Dict[str, Any] = Field(default_factory=dict)
    outline: Dict[str, Any] = Field(default_factory=dict)
    materials: List[Dict[str, str]] = Field(default_factory=list)
    draft: str = ""
    polished: str = ""
    review: Dict[str, Any] = Field(default_factory=dict)
    final_article: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class BaseAgent(ABC):
    """所有Agent的基类 - 依赖抽象LLM客户端"""

    def __init__(self, llm_client=None, model_name: str = None):
        """
        初始化Agent

        Args:
            llm_client: LLM客户端实例（必须传入，实现依赖注入）
            model_name: 模型名称（可选，如果不传则使用llm_client的默认配置）
        """
        if llm_client is None:
            from core.llm_client import get_llm_client
            self.llm_client = get_llm_client()
        else:
            self.llm_client = llm_client

        self.model_name = model_name

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """返回Agent的系统提示词"""
        pass

    @abstractmethod
    def execute(self, context: AgentContext) -> AgentContext:
        """执行Agent的主要逻辑"""
        pass

    def _call_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """调用LLM"""
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt}
        ]

        logger.info(f"LLM输入：{prompt}")
        response = self.llm_client.chat(messages, temperature=temperature)
        logger.info(f"LLM输出：{response}")

        return response

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """从LLM返回的文本中提取JSON"""
        if not text:
            return {}

        # 尝试匹配JSON块
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            text = match.group(1)

        # 尝试直接解析
        try:
            return json.loads(text)
        except:
            # 如果失败，尝试提取第一个{}块
            brace_pattern = r'\{.*\}'
            match = re.search(brace_pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
            return {}

    def _clean_text(self, text: str) -> str:
        """清理生成的文本"""
        if not text:
            return ""

        # 移除常见的AI套话
        patterns_to_remove = [
            (r'首先[，,]\s*', ''),
            (r'其次[，,]\s*', ''),
            (r'最后[，,]\s*', ''),
            (r'综上所述\s*', ''),
            (r'总而言之\s*', ''),
            (r'在当今社会\s*', ''),
        ]
        for pattern, replacement in patterns_to_remove:
            text = re.sub(pattern, replacement, text)

        # 确保段落间有适当间距
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()