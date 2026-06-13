#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 12:57
"""Agent 4：素材填充智能体 - 软硬素材融合"""

from typing import Dict, Any, List
import requests
from .base import BaseAgent, AgentContext
from utils.logger_config import logger

class MaterialAgent(BaseAgent):
	"""自动匹配四类素材：生活化、网络热点、专业原理、人文素材"""

	def __init__(self, model_name: str = "",
	             enable_search: bool = False,
	             tavily_api_key: str = None):
		super().__init__(model_name)
		self.enable_search = enable_search
		self.tavily_api_key = tavily_api_key

	def _get_system_prompt(self) -> str:
		return """你是素材检索专家。根据文章主题和大纲，匹配四类素材：
				1. 生活化共情素材：普通人能共鸣的场景
				2. 网络热点/网友声音：最近的讨论、金句
				3. 专业原理/权威信息：数据、研究、专家观点
				4. 诗词人文/文化素材：经典引用、人文典故
			每类素材至少提供1个，附上使用建议。"""

	def execute(self, context: AgentContext) -> AgentContext:
		topic = context.topic
		outline = context.outline
		sections = outline.get("sections", [])

		# 提取关键搜索词
		search_terms = self._extract_search_terms(topic, sections)
		logger.info(f"提取搜索关键词: {search_terms}")

		# 1. 使用LLM生成/检索素材
		# prompt = f"""主题：「{topic}」
		# 	大纲要点：{self._format_outline(sections)}
		#
		# 	请为每个大纲步骤匹配素材（JSON格式）：
		# 	{{
		# 		"materials": [
		# 		{{
		# 		    "section": "步骤名称",
		# 		    "living_material": {{"content": "生活化素材", "usage": "使用建议"}},
		# 		    "online_material": {{"content": "网络热点", "usage": "使用建议"}},
		# 		    "professional_material": {{"content": "专业素材", "usage": "使用建议"}},
		# 		    "cultural_material": {{"content": "人文素材", "usage": "使用建议"}}
		# 		}}
		# 		]
		# 	}}
		# 		"""
		#
		# response = self._call_llm(prompt, temperature=0.6)
		# context.materials = self._extract_json(response)

		# 2. 如果启用实时搜索，补充网络素材
		logger.info(self.enable_search,self.tavily_api_key,search_terms)
		if self.enable_search and self.tavily_api_key and search_terms:
			logger.info(f"启用实时搜索，关键词: {search_terms}，开始搜索：")
			search_results = self._search_online(search_terms)
			logger.info(f"搜索结果: {search_results}，搜索结束")
			# if search_results:
			# 	self._merge_search_results(materials, search_results)

			context.materials = search_results
		return context

	def _extract_search_terms(self, topic: str, sections: List) -> List[str]:
		"""提取用于搜索的关键词"""
		prompt = f"""从以下主题和大纲中提取3-5个搜索关键词（用于查找实时资讯）：
				主题：{topic}
				大纲：{self._format_outline(sections[:3])}
				
				输出JSON数组：["关键词1", "关键词2"]
				"""

		response = self._call_llm(prompt, temperature=0.3)
		terms = self._extract_json(response)
		logger.info(f"{type(terms)}")
		return terms if isinstance(terms, list) else []

	def _search_online(self, terms: List[str]) -> Dict:
		"""使用Tavily API进行实时搜索"""
		if not self.tavily_api_key:
			return {}

		try:
			from tavily import TavilyClient
			client = TavilyClient(api_key=self.tavily_api_key)

			query = " ".join(terms[:3])
			response = client.search(query=query, search_depth="basic", max_results=3)

			results = {}
			for result in response.get("results", []):
				results[result.get("title", "")] = result.get("content", "")
			logger.info(f"搜索结果: {results}")
			return results
		except Exception as e:
			print(f"搜索失败: {e}")
			return {}

	def _merge_search_results(self, materials: Dict, search_results: Dict):
		"""将搜索结果合并到素材中"""
		if not materials.get("materials"):
			return

		# 将搜索结果添加到第一个section的online_material
		first_section = materials["materials"][0]
		search_text = "\n".join([f"- {k}: {v[:200]}..." for k, v in search_results.items()])
		first_section["online_material"] = {
			"content": search_text,
			"usage": "作为最新案例或数据支撑"
		}

	def _format_outline(self, sections: List) -> str:
		"""格式化大纲为字符串"""
		if not sections:
			return "无"
		return "\n".join([f"- {s.get('step', '')}: {', '.join(s.get('key_points', []))}"
		                  for s in sections[:5]])
