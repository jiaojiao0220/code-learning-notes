#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 12:53
"""搜索模块 - 实时搜索和素材抓取"""

from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import json
import re


class SearchClient:
	"""搜索客户端，支持多种搜索源"""

	def __init__(self, tavily_api_key: Optional[str] = None):
		self.tavily_api_key = tavily_api_key
		self.session = requests.Session()
		self.session.headers.update({
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
		})

	def search(self, query: str, num_results: int = 5) -> List[Dict]:
		"""统一搜索接口，自动选择搜索源"""
		# 优先使用Tavily
		if self.tavily_api_key:
			return self._search_tavily(query, num_results)
		else:
			# 使用免费搜索（需要自建SearXNG）
			return self._search_searxng(query, num_results)

	def _search_tavily(self, query: str, num_results: int) -> List[Dict]:
		"""使用Tavily API搜索"""
		try:
			from tavily import TavilyClient
			client = TavilyClient(api_key=self.tavily_api_key)

			response = client.search(
				query=query,
				search_depth="basic",
				max_results=num_results
			)

			results = []
			for result in response.get("results", []):
				results.append({
					"title": result.get("title", ""),
					"content": result.get("content", ""),
					"url": result.get("url", ""),
					"score": result.get("score", 0)
				})
			return results
		except Exception as e:
			print(f"Tavily搜索失败: {e}")
			return []

	def _search_searxng(self, query: str, num_results: int) -> List[Dict]:
		"""使用自建的SearXNG搜索（需要自己搭建）"""
		# SearXNG API地址，需要自己配置
		searxng_url = "http://localhost:8888/search"

		try:
			response = self.session.get(
				searxng_url,
				params={"q": query, "format": "json"},
				timeout=10
			)

			if response.status_code == 200:
				data = response.json()
				results = []
				for result in data.get("results", [])[:num_results]:
					results.append({
						"title": result.get("title", ""),
						"content": result.get("content", ""),
						"url": result.get("url", ""),
						"score": result.get("score", 0)
					})
				return results
		except:
			pass

		# 降级：使用简单爬虫搜索微信公众号文章
		return self._search_wechat(query, num_results)

	def _search_wechat(self, query: str, num_results: int) -> List[Dict]:
		"""搜索微信公众号文章（简化版）"""
		# 注：完整实现需要微信搜一搜的爬虫，这里返回空
		print("提示：未配置搜索服务，请设置Tavily API Key或自建SearXNG")
		return []

	def fetch_article_content(self, url: str) -> Optional[str]:
		"""抓取文章内容"""
		try:
			response = self.session.get(url, timeout=10)
			response.raise_for_status()

			soup = BeautifulSoup(response.text, 'html.parser')

			# 移除script和style标签
			for script in soup(["script", "style"]):
				script.decompose()

			# 获取文本
			text = soup.get_text()

			# 清理空白
			lines = (line.strip() for line in text.splitlines())
			chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
			text = ' '.join(chunk for chunk in chunks if chunk)

			return text[:5000]  # 限制长度
		except Exception as e:
			print(f"抓取失败: {e}")
			return None

	def search_hot_topics(self, category: str = "news") -> List[str]:
		"""获取热搜话题"""
		# 简化版，返回常见话题
		hot_topics = {
			"news": ["社会热点", "政策变化", "经济动态"],
			"tech": ["人工智能", "互联网", "科技产品"],
			"life": ["职场", "情感", "健康"]
		}
		return hot_topics.get(category, [])