#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 12:52
"""数据目录 - 存储和管理数据"""

from pathlib import Path

DATA_DIR = Path(__file__).parent
CHROMA_DB_DIR = DATA_DIR / "chroma_db"
ARTICLES_DIR = DATA_DIR / "my_articles"
MATERIALS_DIR = DATA_DIR / "materials"

# 确保目录存在
for dir_path in [CHROMA_DB_DIR, ARTICLES_DIR, MATERIALS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)