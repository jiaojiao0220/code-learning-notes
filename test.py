#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/6/1 19:29
# from tavily import TavilyClient
#
# tavily_client = TavilyClient(api_key="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")
# response = tavily_client.search("外国人感受中餐的魅力")
#
# print(response)

# !/usr/bin/env python3
"""全面扫描项目所有Python文件的依赖"""

import ast
import sys
from pathlib import Path
from collections import defaultdict

# 标准库列表（完整版）
STDLIB = {
	# 基础
	'sys', 'os', 'io', 're', 'json', 'time', 'datetime', 'math', 'random',
	'pathlib', 'collections', 'itertools', 'functools', 'typing', 'abc',
	'argparse', 'logging', 'configparser', 'copy', 'pickle', 'hashlib',
	'base64', 'urllib', 'http', 'socket', 'ssl', 'subprocess', 'threading',
	'multiprocessing', 'queue', 'tempfile', 'shutil', 'glob', 'fnmatch',
	'string', 'textwrap', 'pprint', 'traceback', 'warnings', 'contextlib',
	'importlib', 'pkgutil', 'inspect', 'ast', 'tokenize', 'token', 'keyword',
	'codecs', 'encodings', 'enum', 'struct', 'array', 'weakref', 'copyreg',
	'sched', 'bisect', 'heapq', 'statistics', 'decimal', 'fractions',
	'calendar', 'zoneinfo', 'gettext', 'locale', 'unicodedata', 'difflib',
	'filecmp', 'fileinput', 'linecache', 'zipfile', 'tarfile', 'gzip', 'bz2',
	'lzma', 'zipimport', 'runpy', 'compileall', 'py_compile', 'dis', 'pickletools',
	# 网络和并发
	'asyncio', 'concurrent', 'multiprocessing', 'signal', 'select', 'selectors',
	# HTML/XML
	'html', 'xml', 'xmlrpc',
	# 其他
	'curses', 'dbm', 'sqlite3', 'csv', 'shelve', 'plistlib', 'binascii',
	'hashlib', 'hmac', 'secrets', 'uuid', 'token', 'keyword', 'builtins',
	# 类型相关
	'ctypes', 'crypt', 'fcntl', 'grp', 'pwd', 'spwd', 'termios', 'tty',
}

# 导入名到包名的映射
PACKAGE_MAP = {
	# Web框架
	'streamlit': 'streamlit',
	'flask': 'Flask',
	'django': 'Django',
	'fastapi': 'fastapi',
	'chainlit': 'chainlit',
	'gradio': 'gradio',

	# HTTP客户端
	'requests': 'requests',
	'aiohttp': 'aiohttp',
	'httpx': 'httpx',
	'urllib3': 'urllib3',

	# LLM相关
	'openai': 'openai',
	'ollama': 'ollama',
	'anthropic': 'anthropic',
	'langchain': 'langchain',
	'langgraph': 'langgraph',
	'langsmith': 'langsmith',
	'tiktoken': 'tiktoken',
	'transformers': 'transformers',
	'sentence_transformers': 'sentence-transformers',
	'huggingface_hub': 'huggingface-hub',

	# 向量数据库
	'chromadb': 'chromadb',
	'pinecone': 'pinecone-client',
	'qdrant_client': 'qdrant-client',
	'weaviate': 'weaviate-client',
	'faiss': 'faiss-cpu',

	# 搜索API
	'tavily': 'tavily-python',
	'google_search': 'google-search-results',
	'serpapi': 'serpapi',

	# 数据处理
	'pandas': 'pandas',
	'numpy': 'numpy',
	'scipy': 'scipy',
	'sklearn': 'scikit-learn',
	'joblib': 'joblib',

	# 配置和工具
	'pydantic': 'pydantic',
	'yaml': 'PyYAML',
	'toml': 'toml',
	'tomli': 'tomli',
	'dotenv': 'python-dotenv',
	'loguru': 'loguru',
	'rich': 'rich',
	'tqdm': 'tqdm',
	'click': 'click',
	'typer': 'typer',

	# 异步和并发
	'celery': 'celery',
	'redis': 'redis',
	'asyncio': 'asyncio',  # 标准库，但提示

	# 其他
	'beautifulsoup4': 'beautifulsoup4',
	'bs4': 'beautifulsoup4',
	'markdown': 'markdown',
	'mistune': 'mistune',
	'jinja2': 'jinja2',
}


def scan_file(filepath):
	"""扫描单个文件的导入"""
	imports = set()

	try:
		with open(filepath, 'r', encoding='utf-8') as f:
			content = f.read()

		tree = ast.parse(content)

		for node in ast.walk(tree):
			if isinstance(node, ast.Import):
				for alias in node.names:
					top_module = alias.name.split('.')[0]
					imports.add(top_module)

			elif isinstance(node, ast.ImportFrom):
				if node.module:
					top_module = node.module.split('.')[0]
					imports.add(top_module)

	except Exception as e:
		print(f"⚠️ 扫描 {filepath} 出错: {e}")

	return imports


def scan_project(project_root):
	"""扫描整个项目"""
	all_imports = set()
	file_imports = defaultdict(set)

	# 查找所有Python文件
	py_files = list(Path(project_root).rglob('*.py'))

	# 排除虚拟环境等目录
	exclude_dirs = {'venv', 'env', '.venv', '__pycache__', '.git', 'dist', 'build', 'site-packages'}
	py_files = [f for f in py_files if not any(ex in f.parts for ex in exclude_dirs)]

	print(f"📁 找到 {len(py_files)} 个Python文件\n")

	for py_file in py_files:
		imports = scan_file(py_file)
		if imports:
			file_imports[py_file] = imports
			all_imports.update(imports)

	return all_imports, file_imports


def filter_third_party(imports):
	"""过滤出第三方包"""
	third_party = set()
	unknown = set()

	for imp in sorted(imports):
		# 跳过标准库
		if imp in STDLIB:
			continue

		# 检查映射
		if imp in PACKAGE_MAP:
			third_party.add(PACKAGE_MAP[imp])
		else:
			unknown.add(imp)

	return third_party, unknown


def generate_requirements(deps, unknown):
	"""生成requirements.txt"""

	# 已知依赖
	known_deps = sorted(set(deps))

	# 添加版本约束（基于常见版本）
	version_map = {
		'streamlit': '>=1.28.0',
		'openai': '>=1.0.0',
		'langchain': '>=0.1.0',
		'chromadb': '>=0.4.0',
		'tavily-python': '>=0.3.0',
		'pydantic': '>=2.0.0',
		'PyYAML': '>=6.0',
		'requests': '>=2.31.0',
		'python-dotenv': '>=1.0.0',
		'loguru': '>=0.7.0',
		'tqdm': '>=4.66.0',
		'click': '>=8.1.0',
		'ollama': '>=0.1.0',
	}

	with open('requirements.txt', 'w', encoding='utf-8') as f:
		f.write("# 自动生成的依赖列表\n")
		f.write("# 生成时间: 请运行 pip install -r requirements.txt\n\n")

		f.write("# 核心框架\n")
		for dep in known_deps:
			if dep in version_map:
				f.write(f"{dep}{version_map[dep]}\n")
			else:
				f.write(f"{dep}\n")

		if unknown:
			f.write("\n# ⚠️ 未识别的导入（请手动检查）\n")
			for imp in sorted(unknown):
				f.write(f"# 需要检查: {imp}\n")

	print(f"\n✅ 已生成 requirements.txt")

	if unknown:
		print("\n⚠️ 需要手动确认的包:")
		for imp in sorted(unknown):
			print(f"  - {imp}")

		# 生成备选方案
		with open('requirements-manual-check.txt', 'w', encoding='utf-8') as f:
			f.write("# 需要手动确认的导入\n")
			for imp in sorted(unknown):
				f.write(f"{imp}\n")


def main():
	"""主函数"""
	project_root = sys.argv[1] if len(sys.argv) > 1 else '.'

	print("🔍 开始扫描项目依赖...")
	print(f"📂 项目路径: {Path(project_root).absolute()}\n")

	# 扫描
	all_imports, file_imports = scan_project(project_root)

	# 显示扫描结果
	print("📊 扫描结果:")
	for py_file, imports in file_imports.items():
		if imports:
			rel_path = py_file.relative_to(project_root)
			print(f"  📄 {rel_path}: {', '.join(sorted(imports))}")

	# 过滤第三方包
	third_party, unknown = filter_third_party(all_imports)

	print(f"\n📦 发现的导入总数: {len(all_imports)}")
	print(f"📦 第三方包数量: {len(third_party)}")
	print(f"❓ 未识别导入: {len(unknown)}")

	# 生成依赖文件
	generate_requirements(third_party, unknown)

	# 显示统计
	print("\n📋 第三方包列表:")
	for dep in sorted(third_party):
		print(f"  - {dep}")


if __name__ == '__main__':
	main()