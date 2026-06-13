#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 12:52
"""公众号文章生成Agent系统 - 混合架构"""

from .base import AgentContext
from .agent0_input import InputAgent
from .agent1_classifier import ClassifierAgent
from .agent2_elevation import ElevationAgent
from .agent3_outline import OutlineAgent
from .agent4_material import MaterialAgent
from .agent5_polish import PolishAgent
from .agent6_review import ReviewAgent
from .agent_title import TitleAgent


def create_agent_chain(llm_client=None,
                       review_mode: str = "standard",
                       enable_search: bool = False,
                       tavily_api_key: str = None):
    """创建完整的Agent处理链（依赖注入）"""
    return {
        "input": InputAgent(llm_client),
        "classifier": ClassifierAgent(llm_client),
        "elevation": ElevationAgent(llm_client),
        "outline": OutlineAgent(llm_client),
        "title":TitleAgent(llm_client),
        "material": MaterialAgent(llm_client, enable_search=enable_search,
                                   tavily_api_key=tavily_api_key),
        "polish": PolishAgent(llm_client),
        "review": ReviewAgent(llm_client, review_mode=review_mode)
    }


def run_full_pipeline(context: AgentContext, agents: dict) -> AgentContext:
    """运行完整的Agent流水线"""
    if context.user_input.get("answers"):
        context = agents["input"].execute(context)
        context = agents["classifier"].execute(context)
        context = agents["elevation"].execute(context)
        context = agents["title"].execute(context)
        context = agents["outline"].execute(context)
        context = agents["material"].execute(context)
        context = agents["polish"].execute(context)
        context = agents["review"].execute(context)
    return context


__all__ = [
    'AgentContext',
    'InputAgent',
    'ClassifierAgent',
    'ElevationAgent',
    'OutlineAgent',
    'TitleAgent',
    'MaterialAgent',
    'PolishAgent',
    'ReviewAgent',
    'create_agent_chain',
    'run_full_pipeline'
]