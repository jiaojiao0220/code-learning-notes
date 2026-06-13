#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 14:13
"""配置模块"""

from pathlib import Path
import yaml


CONFIG_DIR = Path(__file__).parent


def load_llm_config() -> dict:
    """加载LLM配置"""
    config_path = CONFIG_DIR / "llm_config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def load_app_config() -> dict:
    """加载应用配置"""
    config_path = CONFIG_DIR / "app_config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def get_active_llm_config() -> dict:
    """获取当前激活的LLM配置"""
    llm_config = load_llm_config()
    active_type = llm_config.get("active_type", "openai_compatible")
    return llm_config.get(active_type, {})