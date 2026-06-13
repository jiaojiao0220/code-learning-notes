#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 14:33
"""配置管理器 - 支持前端读写配置"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from copy import deepcopy


class ConfigManager:
	"""配置管理器，支持读取和写入配置"""

	def __init__(self, config_dir: str = None):
		if config_dir is None:
			config_dir = Path(__file__).parent.parent / "config"
		self.config_dir = Path(config_dir)
		self.llm_config_path = self.config_dir / "llm_config.yaml"
		self.app_config_path = self.config_dir / "app_config.yaml"

		# 确保目录存在
		self.config_dir.mkdir(parents=True, exist_ok=True)

		# 默认配置（当文件不存在时使用）
		self.default_llm_config = {
			"active_type": "openai_compatible",
			"openai_compatible": {
				"base_url": "https://api.openai.com/v1",
				"api_key": "",
				"model_name": "gpt-4o-mini",
				"temperature": 0.7,
				"max_tokens": 4096,
				"top_p": 0.9,
				"frequency_penalty": 0.1,
				"presence_penalty": 0.1
			},
			"ollama": {
				"base_url": "http://localhost:11434",
				"model_name": "qwen2.5:14b-instruct-q4_K_M",
				"temperature": 0.7,
				"max_tokens": 4096,
				"top_p": 0.9,
				"frequency_penalty": 0.1,
				"presence_penalty": 0.1
			},
			"custom": {
				"base_url": "http://localhost:8080/v1",
				"api_key": "",
				"model_name": "custom-model",
				"temperature": 0.7,
				"max_tokens": 4096,
				"top_p": 0.9,
				"frequency_penalty": 0.1,
				"presence_penalty": 0.1
			}
		}

		self.default_app_config = {
			"workflow": {
				"review_mode": "standard",
				"enable_search": False,
				"stop_on_error": True
			},
			"vector_store": {
				"persist_directory": "./data/chroma_db"
			},
			"search": {
				"tavily_api_key": "",
				"searxng_url": "http://localhost:8888/search"
			},
			"ui": {
				"default_topic": "为什么年轻人不想加班了",
				"max_history": 20
			}
		}

	def load_llm_config(self) -> Dict[str, Any]:
		"""加载LLM配置，如果文件不存在则创建默认配置"""
		if not self.llm_config_path.exists():
			self._save_llm_config(self.default_llm_config)
			return deepcopy(self.default_llm_config)

		with open(self.llm_config_path, 'r', encoding='utf-8') as f:
			return yaml.safe_load(f) or deepcopy(self.default_llm_config)

	def save_llm_config(self, config: Dict[str, Any]) -> bool:
		"""保存LLM配置"""
		try:
			self._save_llm_config(config)
			return True
		except Exception as e:
			print(f"保存LLM配置失败: {e}")
			return False

	def _save_llm_config(self, config: Dict[str, Any]):
		"""内部保存LLM配置"""
		with open(self.llm_config_path, 'w', encoding='utf-8') as f:
			yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

	def load_app_config(self) -> Dict[str, Any]:
		"""加载应用配置"""
		if not self.app_config_path.exists():
			self._save_app_config(self.default_app_config)
			return deepcopy(self.default_app_config)

		with open(self.app_config_path, 'r', encoding='utf-8') as f:
			return yaml.safe_load(f) or deepcopy(self.default_app_config)

	def save_app_config(self, config: Dict[str, Any]) -> bool:
		"""保存应用配置"""
		try:
			self._save_app_config(config)
			return True
		except Exception as e:
			print(f"保存应用配置失败: {e}")
			return False

	def _save_app_config(self, config: Dict[str, Any]):
		"""内部保存应用配置"""
		with open(self.app_config_path, 'w', encoding='utf-8') as f:
			yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

	def get_active_provider_config(self) -> Dict[str, Any]:
		"""获取当前激活的LLM提供者配置"""
		llm_config = self.load_llm_config()
		active_type = llm_config.get("active_type", "openai_compatible")
		provider_config = llm_config.get(active_type, {})

		return {
			"api_type": active_type,
			**provider_config
		}

	def get_available_providers(self) -> list:
		"""获取所有可用的LLM提供者列表"""
		llm_config = self.load_llm_config()
		providers = []
		for key in ["openai_compatible", "ollama", "custom"]:
			if key in llm_config:
				providers.append({
					"id": key,
					"name": self._get_provider_name(key),
					"config": llm_config[key]
				})
		return providers

	def _get_provider_name(self, provider_id: str) -> str:
		"""获取提供者的显示名称"""
		names = {
			"openai_compatible": "OpenAI兼容 (OpenAI/DeepSeek/硅基流动)",
			"ollama": "Ollama (本地)",
			"custom": "自定义API"
		}
		return names.get(provider_id, provider_id)

	def switch_provider(self, provider_id: str) -> bool:
		"""切换LLM提供者"""
		llm_config = self.load_llm_config()
		if provider_id in llm_config:
			llm_config["active_type"] = provider_id
			return self.save_llm_config(llm_config)
		return False

	def update_provider_config(self, provider_id: str, config: Dict[str, Any]) -> bool:
		"""更新指定提供者的配置"""
		llm_config = self.load_llm_config()
		if provider_id in llm_config:
			# 合并配置，保留未修改的字段
			for key, value in config.items():
				if value is not None:
					llm_config[provider_id][key] = value
			return self.save_llm_config(llm_config)
		return False

	def reset_to_defaults(self) -> bool:
		"""重置所有配置到默认值"""
		try:
			self._save_llm_config(self.default_llm_config)
			self._save_app_config(self.default_app_config)
			return True
		except Exception as e:
			print(f"重置配置失败: {e}")
			return False


# 全局实例
_default_manager = None


def get_config_manager() -> ConfigManager:
	"""获取全局配置管理器实例"""
	global _default_manager
	if _default_manager is None:
		_default_manager = ConfigManager()
	return _default_manager