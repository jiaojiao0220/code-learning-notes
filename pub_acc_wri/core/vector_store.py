#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 12:53
"""向量数据库管理 - 存储历史文章、金句、素材"""

import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import hashlib


class VectorStore:
	"""本地向量数据库，用于存储和检索文章素材"""

	def __init__(self, persist_directory: str = "./data/chroma_db"):
		self.persist_directory = persist_directory
		self.client = chromadb.PersistentClient(path=persist_directory)

		# 使用默认的embedding函数（本地）
		self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

		# 集合名称
		self.collections = {
			"articles": "my_articles",  # 我的历史文章
			"golden_sentences": "golden_sentences",  # 金句库
			"materials": "materials",  # 素材库
			"templates": "templates"  # 模板库
		}

		# 初始化集合
		self._init_collections()

	def _init_collections(self):
		"""初始化所有集合"""
		for name, collection_name in self.collections.items():
			try:
				self.client.get_collection(collection_name)
			except:
				self.client.create_collection(
					name=collection_name,
					embedding_function=self.embedding_fn
				)

	def add_article(self, article: Dict[str, Any]):
		"""添加历史文章"""
		collection = self.client.get_collection(self.collections["articles"])

		# 生成唯一ID
		article_id = hashlib.md5(
			f"{article.get('title', '')}{article.get('content', '')}".encode()
		).hexdigest()

		collection.upsert(
			ids=[article_id],
			documents=[article.get("content", "")],
			metadatas=[{
				"title": article.get("title", ""),
				"topic": article.get("topic", ""),
				"genre": article.get("genre", ""),
				"created_at": article.get("created_at", "")
			}]
		)
		return article_id

	def search_articles(self, query: str, n_results: int = 5) -> List[Dict]:
		"""搜索相关历史文章"""
		collection = self.client.get_collection(self.collections["articles"])

		results = collection.query(
			query_texts=[query],
			n_results=n_results
		)

		return self._format_results(results)

	def add_golden_sentence(self, sentence: str, context: str = "", tags: List[str] = None):
		"""添加金句"""
		collection = self.client.get_collection(self.collections["golden_sentences"])

		sentence_id = hashlib.md5(sentence.encode()).hexdigest()

		collection.upsert(
			ids=[sentence_id],
			documents=[sentence],
			metadatas=[{
				"context": context,
				"tags": json.dumps(tags or [])
			}]
		)
		return sentence_id

	def search_golden_sentences(self, query: str, n_results: int = 10) -> List[str]:
		"""搜索金句"""
		collection = self.client.get_collection(self.collections["golden_sentences"])

		results = collection.query(
			query_texts=[query],
			n_results=n_results
		)

		return results.get("documents", [[]])[0]

	def add_material(self, material: Dict[str, str], category: str):
		"""添加素材"""
		collection = self.client.get_collection(self.collections["materials"])

		material_id = hashlib.md5(material.get("content", "").encode()).hexdigest()

		collection.upsert(
			ids=[material_id],
			documents=[material.get("content", "")],
			metadatas=[{
				"category": category,
				"source": material.get("source", ""),
				"tags": json.dumps(material.get("tags", []))
			}]
		)
		return material_id

	def search_materials(self, query: str, category: Optional[str] = None, n_results: int = 5) -> List[Dict]:
		"""搜索素材"""
		collection = self.client.get_collection(self.collections["materials"])

		# 构建where条件
		where = {"category": category} if category else None

		results = collection.query(
			query_texts=[query],
			n_results=n_results,
			where=where
		)

		return self._format_results(results)

	def _format_results(self, results: Dict) -> List[Dict]:
		"""格式化搜索结果"""
		formatted = []
		documents = results.get("documents", [[]])[0]
		metadatas = results.get("metadatas", [[]])[0]
		distances = results.get("distances", [[]])[0]

		for doc, meta, dist in zip(documents, metadatas, distances):
			formatted.append({
				"content": doc,
				"metadata": meta,
				"score": 1 - dist if dist else 1.0
			})

		return formatted

	def delete_collection(self, name: str):
		"""删除集合"""
		if name in self.collections:
			try:
				self.client.delete_collection(self.collections[name])
			except:
				pass


# 全局实例
_default_store = None


def get_vector_store() -> VectorStore:
	"""获取全局向量库实例"""
	global _default_store
	if _default_store is None:
		_default_store = VectorStore()
	return _default_store