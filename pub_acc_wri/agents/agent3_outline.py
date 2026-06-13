#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 12:57
"""Agent 3：大纲生成智能体 - 使用加载的模板"""

from typing import Dict, Any, List
from .base import BaseAgent, AgentContext, GENRE_TEMPLATES


class OutlineAgent(BaseAgent):
    """根据文体自动套用固定结构，并增加可选弹性节点"""

    def __init__(self, llm_client=None, model_name: str = None):
        super().__init__(llm_client, model_name)

    def _get_system_prompt(self) -> str:
        return """你是文章大纲生成专家。你的任务是：
                1. 严格遵守给定文体的标准结构骨架
                2. 在每个标准步骤后，可选地增加或者减少弹性分支
                3. 确保逻辑递进、层层深入
                4，必须围绕主题展开
                输出格式：结构化的多级大纲。"""

    def execute(self, context: AgentContext) -> AgentContext:
        topic = context.topic
        genre = context.classification.get("genre", "现象说理")
        style = context.classification.get("style", "官媒沉稳风")
        elevation = context.elevation.get("standard_elevation", {})
        # 获取该文体的标准结构（从加载的模板）
        template = GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["现象说理"])
        structure = template.get("structure", [])
        # personal_slots = elevation.get("personal_slots", [])
        three_dimensions = elevation.get("three_dimensions", {})
        user_input = context.user_input
        personal_story = user_input.get("story", "无个人经历")
        personal_opinion = user_input.get("opinion", "无个人观点")
        prompt = f"""话题：「{topic}」。
                    文体：{genre}。
                    风格：{style}。
                    用户提供的信息：
						- 个人经历：{personal_story if personal_story else "无"}
						- 独特观点：{personal_opinion if personal_opinion else "无"}
                    核心立意：{elevation.get('core_idea', '待定')}。
                    个人视角：{context.elevation.get("personal_slots")}。
                    在标准立意的框架下，将个人经历作为具体案例嵌入开头、中间和结尾，使抽象观点具象化；例如，在社会根源分析中融入个人观察到的动漫影 响，在三维升华时结合个人成长故事，如从童年看动漫到成年坚守正义的历程，使文章既有深度又充满治愈的个人色彩。
                    三维视角：{elevation.get("three_dimensions", "")}。
                    标准结构骨架（必须包含）：
                    {self._format_structure(structure)}
                    
                    要求：
                    1. 严格按照上述骨架生成大纲，不可省略任一步骤
                    2. 每个步骤下展开2-3个要点
                    3. 根据风格调整表达方式
                    
                    请输出完整的大纲（JSON格式）：
                    {{
                      "sections": [
                        {{
                          "step": "步骤名称",
                          "key_points": ["要点1", "要点2"],
                          "elastic_options": ["可选分支1（如果需要）", "可选分支2"]
                        }}
                      ],
                    }}
                    """
        # 48行删除的"title": "建议标题（含数字、情感词、结果承诺）",

        response = self._call_llm(prompt, temperature=0.5)
        outline = self._extract_json(response)

        # 确保结构完整性
        if len(outline.get("sections", [])) < len(structure):
            existing_steps = [s.get("step") for s in outline.get("sections", [])]
            for step in structure:
                if step not in existing_steps:
                    outline.setdefault("sections", []).append({
                        "step": step,
                        "key_points": ["待展开"],
                        "elastic_options": []
                    })

        context.outline = outline
        return context

    def _format_structure(self, structure: List[str]) -> str:
        """格式化结构列表为字符串"""
        if not structure:
            return "无固定结构"
        return "\n".join([f"{i+1}. {s}" for i, s in enumerate(structure)])