#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 12:56

"""Agent 0：输入准备智能体 - 收集用户素材和观点"""

from typing import Dict, Any
from .base import BaseAgent, AgentContext


class InputAgent(BaseAgent):
	"""引导用户提供低成本高回报的信息"""

	def __init__(self, llm_client=None, model_name: str = None):
		super().__init__(llm_client, model_name)

	def _get_system_prompt(self) -> str:
		return """你是公众号写作的输入准备助手。你的任务是引导用户提供3个关键信息：
			1. 个人经历/故事（如果有）
			2. 独特观点（与主流不同的看法）
			3. 独家素材（数据、图片、案例等）
			这些信息将直接决定文章质量。请友好、简洁地提问。"""

	def execute(self, context: AgentContext) -> AgentContext:
		"""收集用户输入"""
		topic = context.topic

		# 构建提问Prompt
		prompt = f"""用户要写的话题是：[{topic}]
				请输出3个引导性问题，帮助用户提供有价值的信息：
				格式要求（严格输出JSON）：
				{ 
					{
						"story_question": "关于个人经历的问题",
						"opinion_question": "关于独特观点的问题",
						"material_question": "关于独家素材的问题"
					} 
				}
				问题要求：
					- 每个问题不超过20字
					- 具体、可回答、不需要长篇大论
					- 示例风格：「你有过类似经历吗？」「你对这事和主流有啥不同看法？」
				"""

		response = self._call_llm(prompt, temperature=0.3)
		questions = self._extract_json(response)

		# 这里在实际使用中需要与用户交互
		# 简化版：直接存储问题模板，后续由UI层处理
		context.user_input = {
			"questions": questions,
			"answers": {}  # 待用户填写
		}

		return context

	def collect_answers(self, context: AgentContext, answers: Dict[str, str]) -> AgentContext:
		"""收集用户回答（由UI层调用）"""
		context.user_input["answers"] = answers
		return context

if __name__ == "__main__":
	agent = InputAgent()
	context = AgentContext(topic="如何评价2023年6月13日上海世博会?")
	context = agent.execute(context)
	print(context.user_input)