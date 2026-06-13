#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 12:56

"""Agent 1：文体分类智能体 - 从rules加载模板"""

from utils.logger_config import logger
from typing import Dict, Any
from .base import BaseAgent, AgentContext, GENRE_TEMPLATES, STYLE_RULES


class ClassifierAgent(BaseAgent):
	"""自动识别5大文体和4种风格"""

	def __init__(self, llm_client=None, model_name: str = None):
		super().__init__(llm_client, model_name)

	def _get_system_prompt(self) -> str:
		genre_list = "、".join(GENRE_TEMPLATES.keys())
		style_list = "、".join(STYLE_RULES.keys())

		return f"""你是公众号文章分类专家。给定一个话题，你需要判断：
                    1. 文体类型（从以下5类选择）：{genre_list}
                    2. 写作风格（从以下4类选择）：{style_list}
                    分类规则：
                    {self._get_classification_rules()}
                    输出必须是严格的JSON格式。"""

	def _get_classification_rules(self) -> str:
		"""从模板中提取分类规则"""
		rules = []
		for genre, template in GENRE_TEMPLATES.items():
			keywords = template.get("keywords", [])
			if keywords:
				rules.append(f"- 含{keywords} → {genre}")
		return "\n".join(rules)

	def execute(self, context: AgentContext) -> AgentContext:
		topic = context.topic
		user_input = context.user_input
		user_story = user_input.get("story","无用户经历")
		user_option = user_input.get("opinion","无用户观点")
		prompt = f"""话题：[{topic}]
                    用户输入：
                        个人经历：[{user_story}]；
                        个人观点: [{user_option}]
                    请输出JSON格式的分类结果：
                    { 
                        {
                            "genre": "文体类型",
                            "style": "写作风格",
                            "reason": "简要分类理由（一句话）"
                        } 
                    }"""

		response = self._call_llm(prompt, temperature=0.2)
		classification = self._extract_json(response)

		# 验证并确保默认值
		valid_genres = list(GENRE_TEMPLATES.keys())
		valid_styles = list(STYLE_RULES.keys())

		if classification.get("genre") not in valid_genres:
			logger.warning(f"无效文体类型：{classification['genre']}")
			classification["genre"] = "现象说理"

		if classification.get("style") not in valid_styles:
			logger.warning(f"无效写作风格：{classification['style']}")
			classification["style"] = "官媒沉稳风"

		context.classification = classification

		# # 存储对应的模板和规则（从加载的规则中获取）
		# context.outline_template = GENRE_TEMPLATES.get(
		# 	classification["genre"],
		# 	GENRE_TEMPLATES["现象说理"]
		# )
		# context.style_rules = STYLE_RULES.get(
		# 	classification["style"],
		# 	GENRE_TEMPLATES["官媒沉稳风"]
		# )
		return context


if __name__ == "__main__":
	agent = ClassifierAgent()
	context = AgentContext(topic="如何评价《唐顿庄园》？")
	result = agent.execute(context)
	print(result.to_dict())
