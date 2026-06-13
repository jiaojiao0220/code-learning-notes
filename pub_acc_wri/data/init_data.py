#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 13:09
"""初始化数据 - 导入示例文章和素材"""

import json
from pathlib import Path
from data import ARTICLES_DIR, MATERIALS_DIR


def init_sample_articles():
	"""初始化示例文章"""
	sample_articles = [
		{
			"title": "为什么年轻人不想加班了",
			"topic": "职场",
			"genre": "现象说理",
			"content": """
# 为什么年轻人不想加班了

## 现象体感
最近和几个95后聊天，发现他们对加班的态度出奇一致：能不加班就不加班。

## 群众共鸣
这不是懒惰，而是性价比的重新计算...
""",
			"created_at": "2024-01-01"
		}
	]

	for article in sample_articles:
		filepath = ARTICLES_DIR / f"{article['title'][:20]}.json"
		with open(filepath, 'w', encoding='utf-8') as f:
			json.dump(article, f, ensure_ascii=False, indent=2)


def init_sample_materials():
	"""初始化示例素材"""
	sample_materials = [
		{
			"content": "马云说：员工离职，要么钱没给够，要么心委屈了。",
			"source": "马云演讲",
			"category": "名人名言",
			"tags": ["职场", "管理"]
		},
		{
			"content": "《2023职场报告》显示，76%的年轻人认为工作生活平衡比高薪更重要。",
			"source": "某招聘平台",
			"category": "数据报告",
			"tags": ["职场", "数据"]
		}
	]

	for material in sample_materials:
		filepath = MATERIALS_DIR / f"{material['tags'][0]}_{material['source']}.json"
		with open(filepath, 'w', encoding='utf-8') as f:
			json.dump(material, f, ensure_ascii=False, indent=2)


def init_all():
	"""初始化所有数据"""
	print("初始化示例文章...")
	init_sample_articles()
	print("初始化示例素材...")
	init_sample_materials()
	print("数据初始化完成！")


if __name__ == "__main__":
	init_all()