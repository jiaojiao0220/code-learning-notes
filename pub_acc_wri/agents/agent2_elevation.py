#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 12:56

"""Agent 2：立意升维智能体 - 决定文章深度和格局"""

from typing import Dict, Any
from .base import BaseAgent, AgentContext


class ElevationAgent(BaseAgent):
	"""以小见大、挖根源、三维升华"""

	def __init__(self, llm_client=None, model_name: str = None):
		super().__init__(llm_client, model_name)

	def _get_system_prompt(self) -> str:
		return """你是文章立意提升专家。你的任务是：
				1. 避免浅显、俗套、流水账
				2. 执行三条强制规则：
				   - 小事必须"以小见大"
				   - 现象必须挖到社会根源
				   - 结尾必须人文/时代/哲理三维升华
				输出格式：标准立意 + 个人视角槽位 + 融合建议"""

	def execute(self, context: AgentContext) -> AgentContext:
		topic = context.topic
		genre = context.classification.get("genre", "现象说理")
		user_input = context.user_input
		personal_story = user_input.get("story", "无个人经历")
		personal_opinion = user_input.get("opinion", "无个人观点")
		prompt = f"""话题：「{topic}」
					文体类型：{genre}
					用户提供的信息：
						- 个人经历：{personal_story if personal_story else "无"}
						- 独特观点：{personal_opinion if personal_opinion else "无"}
						- 素材：{context.materials if context.materials else "无"}
					请按以下步骤输出（JSON格式）：
					
					1. 标准立意：以主流价值为导向的深度解读
					2. 个人视角槽位：预留2-3个可插入个人经历/观点的地方
					3. 融合建议：如何将个人视角与标准立意结合
					
					输出格式：
					{{
					  "standard_elevation": {{
					    "core_idea": "核心论点（一句话）",
					    "root_cause": "社会根源分析",
					    "three_dimensions": {{
					      "humanity": "人文维度升华",
					      "era": "时代维度升华",
					      "philosophy": "哲理维度升华"
					    }}
					  }},
					  "personal_slots": [
					    {{"position": "开头/中间/结尾", "suggestion": "可以插入什么样的个人经历"}},
					    {{"position": "开头/中间/结尾", "suggestion": "可以插入什么样的独特观点"}}
					  ],
					  "integration_advice": "融合建议说明"
					}}
					"""

		response = self._call_llm(prompt, temperature=0.6)
		elevation = self._extract_json(response)

		context.elevation = elevation

		# 如果有个人素材，生成融合后的立意文本
		if personal_story or personal_opinion:
			context.elevation["fused"] = self._fuse_personal_view(
				elevation, personal_story, personal_opinion
			)

		return context

	def _fuse_personal_view(self, elevation: Dict, story: str, opinion: str) -> str:
		"""融合个人视角生成立意文本"""
		prompt = f"""请将以下个人素材融合到立意中，生成一段200字以内的开篇立意段落：

					标准立意核心：{elevation.get('standard_elevation', {}).get('core_idea', '')}
					
					个人经历：{story}
					独特观点：{opinion}
					
					要求：自然过渡，不突兀，保持专业度但有温度。"""

		return self._call_llm(prompt, temperature=0.7)