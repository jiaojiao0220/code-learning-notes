#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 12:57
"""Agent 5：文笔润色智能体 - 使用加载的风格规则"""

from typing import Dict, Any, List
from .base import BaseAgent, AgentContext, STYLE_RULES, GENRE_TEMPLATES
from utils.logger_config import logger


class PolishAgent(BaseAgent):
	"""根据风格标签进行文笔润色，模拟人类写作特征"""

	def __init__(self, llm_client=None, model_name: str = None):
		super().__init__(llm_client, model_name)

	def _get_system_prompt(self) -> str:
		return """你是文章润色专家。你的任务是：
				1. 将初稿改写成指定风格
				2. 执行风格规则（长短句结合、排比递进、设问引导等）
				3. 增加画面感、金句密度
				4. 避免AI套话
				输出：润色后的完整文章 + 精修建议清单
				"""

	def execute(self, context: AgentContext) -> AgentContext:
		draft = context.draft
		if not draft:
			draft = self._generate_draft(context)

		style = context.classification.get("style", "官媒沉稳风")
		style_rules = STYLE_RULES.get(style, STYLE_RULES["官媒沉稳风"])
		elevation = context.elevation.get("standard_elevation", "")

		# 获取风格参数
		sentence_length = style_rules.get("sentence_length", "mixed")
		golden_density = style_rules.get("golden_sentence_density", 500)
		allow_emoji = style_rules.get("allow_emoji", False)
		pronoun = style_rules.get("pronoun", "我们")
		features = style_rules.get("features", [])
		temperature = style_rules.get("temperature", 0.7)

		prompt = f"""请将以下文章初稿润色为「{style}」风格。

			风格特征：
			- 句子长度：{sentence_length}
			- 金句密度：每{golden_density}字至少1个金句
			- 允许emoji：{allow_emoji}
			- 人称代词：{pronoun}
			- 核心特征：{', '.join(features)}
			
			文章立意升华方向：
			- 人文维度：{elevation.get('three_dimensions', {}).get('humanity', '')}
			- 时代维度：{elevation.get('three_dimensions', {}).get('era', '')}
			
			初稿内容：
			{draft}
			
			润色要求：
			1. 开篇有吸引力（用故事、问题或反常识观点）
			2. 段落长度控制在5行以内
			3. 每{golden_density}字至少有一句可加粗的金句
			4. 结尾必须三维升华
			5. 删除"首先、其次、最后、综上所述"等套话
			6. 增加设问、反问、排比等修辞
			7. 润色后的完整文章必须使用markdown格式
			
			输出格式：
			```json
			{{
			  "polished_article": "润色后的完整文章",
			  "golden_sentences": ["金句1", "金句2"],
			  ]
			}}
			"""

		response = self._call_llm(prompt, temperature=temperature)
		result = self._extract_json(response)

		polished = result.get("polished_article", draft)
		polished = self._clean_text(polished)

		context.polished = polished
		# context.review = context.review or {}
		# context.review["golden_sentences"] = result.get("golden_sentences", [])
		# context.review["polish_suggestions"] = result.get("polish_suggestions", [])

		return context

	def _generate_draft(self, context: AgentContext) -> str:
		"""如果没有初稿，先生成初稿"""
		outline = context.outline
		materials = context.materials
		elevation = context.elevation
		genre = context.classification.get("genre", "现象说理")
		# 获取该文体的标准结构（从加载的模板）
		template = GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["现象说理"])
		structure = template.get("structure", [])
		word_count_range = template.get("word_count", {"min": 1000, "max": 1800})
		personal_slots = context.elevation.get("personal_slots", [])
		three_dimensions = elevation.get("three_dimensions", {})
		prompt = f"""请根据以下内容生成文章初稿：
		
			标题：{context.user_input.get("title_options", context.topic)}
			
			文体：
			{genre}
			
			文体结构：
			{structure}
			
		
			立意核心：
			{elevation.get('standard_elevation', "").get('core_idea', '')}
			个人视角：
			{personal_slots}。
            在标准立意的框架下，将个人经历作为具体案例嵌入开头、中间和结尾，使抽象观点具象化；例如，在社会根源分析中融入个人观察到的动漫影 响，在三维升华时结合个人成长故事，如从童年看动漫到成年坚守正义的历程，使文章既有深度又充满治愈的个人色彩。
            三维视角：
            {context.elevation["standard_elevation"].get("three_dimensions", "")}。
			大纲：
			{self._format_outline(outline)}
			
			素材：
			{self._format_materials(materials)}
			
			字数范围：
			{word_count_range['min']}-{word_count_range['max']}字
			
			要求：
			
			按大纲结构逐段写作
			
			每个段落采用"论点→论据→金句/过渡"结构
			
			适当插入素材
						
			不要使用"首先、其次、最后"
			"""

		try:
			re = self._call_llm(prompt, temperature=0.7)
			return re
		except Exception as e:
			logger.error(f"Failed to generate draft: {e}")

		return None

	def _format_outline(self, outline: Dict) -> str:
		"""格式化大纲"""
		sections = outline.get("sections", [])
		text = []
		for s in sections:
			step = s.get("step", "")
			points = s.get("key_points", [])
			text.append(f"\n## {step}")
			text.extend([f"- {p}" for p in points])
		return "\n".join(text)

	def _format_materials(self, materials: List) -> str:
		"""格式化素材"""
		if not materials:
			return "无特殊素材"
		text = []
		for m in materials[:3]:
			section = m.get("section", "")
		for material_type in ["living_material", "online_material", "professional_material", "cultural_material"]:
			material = m.get(material_type, {})
			if material.get("content"):
				text.append(f"\n[{section}]{material_type}: {material['content'][:200]}")
		return "\n".join(text) if text else "无特殊素材"
