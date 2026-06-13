#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 12:53

"""LLM客户端 - 支持多API类型，完全解耦"""

from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass
from abc import ABC, abstractmethod
import hashlib
import json

from pydantic import BaseModel, Field

class LLMConfig(BaseModel):
    api_type: str = "openai_compatible"
    base_url: str = ""
    api_key: str = ""
    model_name: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    frequency_penalty: float = 0.1
    presence_penalty: float = 0.1


class BaseLLMProvider(ABC):
    """LLM提供者抽象基类"""

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """同步调用"""
        pass

    @abstractmethod
    async def achat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """异步调用"""
        pass

    @abstractmethod
    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """流式调用"""
        pass


class OpenAICompatibleProvider(BaseLLMProvider):
    """OpenAI兼容API提供者（支持OpenAI、DeepSeek、硅基流动、智谱等）"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._init_client()

    def _init_client(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(
                base_url=self.config.base_url,
                api_key=self.config.api_key,
                timeout=60.0
            )
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        temperature = kwargs.get('temperature', self.config.temperature)
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        for i in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=self.config.top_p,
                    frequency_penalty=self.config.frequency_penalty,
                    presence_penalty=self.config.presence_penalty
                )
                result = response.choices[0].message.content
                if result and result.strip():
                    return result
                else:print(f"LLM调用失败: 响应结果为空。尝试重试...")
            except Exception as e:
                print(f"LLM调用失败: {e} 重试中第{i+1}次")
        print("LLM调用失败: 重试次数已用完")
        return ""

    async def achat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.chat, messages, **kwargs)

    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        temperature = kwargs.get('temperature', self.config.temperature)
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)

        try:
            stream = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"流式调用失败: {e}")


class OllamaProvider(BaseLLMProvider):
    """Ollama本地提供者"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._init_client()

    def _init_client(self):
        try:
            import ollama
            self.ollama = ollama
        except ImportError:
            raise ImportError("请安装 ollama: pip install ollama")

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        temperature = kwargs.get('temperature', self.config.temperature)

        try:
            response = self.ollama.chat(
                model=self.config.model_name,
                messages=messages,
                options={"temperature": temperature}
            )
            return response['message']['content']
        except Exception as e:
            print(f"Ollama调用失败: {e}")
            return ""

    async def achat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.chat, messages, **kwargs)

    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        temperature = kwargs.get('temperature', self.config.temperature)

        try:
            stream = self.ollama.chat(
                model=self.config.model_name,
                messages=messages,
                options={"temperature": temperature},
                stream=True
            )

            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
        except Exception as e:
            print(f"流式调用失败: {e}")


class LLMClient:
    """统一的LLM客户端，支持多API类型和缓存"""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or self._load_config_from_yaml()
        self._provider = self._create_provider()
        self._cache: Dict[str, str] = {}
        self._cache_enabled = True

    def _load_config_from_yaml(self) -> LLMConfig:
        """从YAML配置文件加载配置"""
        try:
            from config import get_active_llm_config
            raw_config = get_active_llm_config()

            # 从config/llm_config.yaml获取active_type
            from config import load_llm_config
            full_config = load_llm_config()
            api_type = full_config.get("active_type", "openai_compatible")

            return LLMConfig(
                api_type=api_type,
                base_url=raw_config.get("base_url", ""),
                api_key=raw_config.get("api_key", ""),
                model_name=raw_config.get("model_name", ""),
                temperature=raw_config.get("temperature", 0.7),
                max_tokens=raw_config.get("max_tokens", 4096),
                top_p=raw_config.get("top_p", 0.9),
                frequency_penalty=raw_config.get("frequency_penalty", 0.1),
                presence_penalty=raw_config.get("presence_penalty", 0.1)
            )
        except Exception as e:
            print(f"加载配置失败，使用默认配置: {e}")
            return LLMConfig(
                api_type="openai_compatible",
                base_url="http://localhost:11434",
                model_name="qwen2.5:14b-instruct-q4_K_M"
            )

    def _create_provider(self) -> BaseLLMProvider:
        """根据配置创建对应的Provider"""
        if self.config.api_type == "openai_compatible":
            return OpenAICompatibleProvider(self.config)
        elif self.config.api_type == "ollama":
            return OllamaProvider(self.config)
        else:
            # 默认使用OpenAI兼容
            return OpenAICompatibleProvider(self.config)

    def _get_cache_key(self, messages: List[Dict], temperature: float) -> str:
        """生成缓存key"""
        content = f"{messages}{temperature}"
        return hashlib.md5(content.encode()).hexdigest()

    def chat(self,
             messages: List[Dict[str, str]],
             temperature: Optional[float] = None,
             use_cache: bool = True) -> str:
        """同步调用LLM"""
        temp = temperature or self.config.temperature

        if use_cache and self._cache_enabled:
            cache_key = self._get_cache_key(messages, temp)
            if cache_key in self._cache:
                return self._cache[cache_key]

        result = self._provider.chat(messages, temperature=temp)

        if use_cache and self._cache_enabled and result:
            self._cache[cache_key] = result

        return result

    async def achat(self,
                    messages: List[Dict[str, str]],
                    temperature: Optional[float] = None) -> str:
        """异步调用LLM"""
        temp = temperature or self.config.temperature
        return await self._provider.achat(messages, temperature=temp)

    async def stream_chat(self,
                          messages: List[Dict[str, str]],
                          temperature: Optional[float] = None) -> AsyncGenerator[str, None]:
        """流式调用LLM"""
        temp = temperature or self.config.temperature
        async for chunk in self._provider.stream_chat(messages, temperature=temp):
            yield chunk

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()

    def set_cache_enabled(self, enabled: bool):
        """设置是否启用缓存"""
        self._cache_enabled = enabled

    def switch_provider(self, api_type: str):
        """切换API提供者"""
        self.config.api_type = api_type
        self._provider = self._create_provider()
        self.clear_cache()


# 全局实例
_default_client = None


def get_llm_client() -> LLMClient:
    """获取全局LLM客户端实例"""
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client