#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 20:03

"""Agent：标题生成智能体 - 基于大纲生成多个爆款标题方案"""

from typing import Dict, Any, List
from .base import BaseAgent, AgentContext,TITLE_RULES
from utils.logger_config import logger

class TitleAgent(BaseAgent):
    """生成3-5个标题方案，包含不同风格和策略"""

    def __init__(self, llm_client=None, model_name: str = None):
        super().__init__(llm_client, model_name)
        self.title_rules = None

    def _get_system_prompt(self) -> str:
        return """你是公众号爆款标题专家。你的任务是：
                1. 根据大纲生成3-5个不同风格的标题
                2. 每个标题必须符合微信公众号平台算法偏好
                3. 标注每个标题的策略类型和预期效果
                4. 给出最终推荐建议"""

    def execute(self, context: AgentContext) -> AgentContext:
        topic = context.topic
        genre = context.classification.get("genre")
        style = context.classification.get("style")
        outline = context.outline

        self.title_rules = [dict(i) for i in TITLE_RULES["title_strategies"] if TITLE_RULES["title_strategies"]]
        print(self.title_rules)

        prompt = f"""话题：{topic}
                    体裁：{genre}
                    风格：{style}
                    大纲结构：{outline.get('sections', [])}
                    
                    请生成5个标题方案，基于以下策略：
                    {self.title_rules}
                    选取适配文体和大纲立意的标题方案，并给出推荐理由。
                    
                    输出JSON格式：
                    {{
                      "titles": [
                        {{
                          "text": "标题内容",
                          "strategy": "策略类型",
                          "strengths": "优势说明",
                          "expected_ctr": "预期点击率评级（高/中/低）"
                        }}
                      ],
                      "recommendation": "最终推荐的标题索引（1-5）",
                      "reason": "推荐理由"
                    }}
                    """

        response = self._call_llm(prompt, temperature=0.7)
        title_data = self._extract_json(response)

        # 存储到 context
        index_recommendation = int(title_data["recommendation"])
        logger.info(f"推荐的标题索引：{index_recommendation}")
        recommended_index = int(input("请输入推荐的标题索引："))
        logger.info(f"{type(title_data)},  {type(title_data.get('titles',''))}")
        # context.user_input["title_options"] = title_data["titles"][index_recommendation - 1]["text"]
        context.user_input["title_options"] = title_data["titles"][recommended_index - 1]["text"]
        logger.info(f"最终标题索引：{title_data['recommendation']}")
        return context
