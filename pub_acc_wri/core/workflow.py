#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 13:08
"""工作流编排器 - 串联所有Agent"""

# from utils.logger_config import logger
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import json
from pathlib import Path

from pydantic import BaseModel


class WorkflowStatus(Enum):
	"""工作流状态"""
	PENDING = "pending"
	RUNNING = "running"
	COMPLETED = "completed"
	FAILED = "failed"


# 原来（dataclass）
# @dataclass
# class WorkflowStep:
#     name: str
#     agent: Any
#     status: WorkflowStatus = WorkflowStatus.PENDING
#     duration: float = 0.0
#     error: Optional[str] = None
#     result: Any = None

# # 改为（Pydantic）
# class WorkflowStep(BaseModel):
#     name: str
#     agent: Any
#     status: WorkflowStatus = WorkflowStatus.PENDING
#     duration: float = 0.0
#     error: Optional[str] = None
#     result: Any = None
#
#     class Config:
#         arbitrary_types_allowed = True  # 允许任意类型（因为 agent 和 result 是 Any）

from typing import Protocol


# # 定义 Agent 接口
# class AgentProtocol(Protocol):
# 	def execute(self, context: Any) -> Any: ...
#
# 	def _get_system_prompt(self) -> str: ...


class WorkflowStep(BaseModel):
	"""工作流步骤"""
	name: str
	agent: Any  # 使用协议类型，而不是 Any
	status: WorkflowStatus = WorkflowStatus.PENDING
	duration: float = 0.0
	error: Optional[str] = None
	result: Any = None

	class Config:
		arbitrary_types_allowed = True


class WorkflowOrchestrator:
	"""工作流编排器"""

	# 文件顶部不导入 logger

	def _get_logger(self):
		"""需要时才导入"""
		from utils.logger_config import logger
		return logger


	def __init__(self, agents: Dict[str, Any]):
		self.agents = agents
		self.steps = self._build_steps()
		self.callbacks = {
			"on_workflow_start": [],
			"on_step_start": [],
			"on_step_end": [],
			"on_workflow_end": []
		}
		self.logs = []

	def _build_steps(self) -> list:
		"""构建步骤列表"""
		# step_order = ["input", "classifier", "elevation", "outline", "title", "material", "polish", "review"]
		step_order = ["classifier", "elevation", "outline", "title", "material", "polish", "review"]
		steps = []

		for name in step_order:
			if name in self.agents:
				steps.append(WorkflowStep(name=name, agent=self.agents[name]))

		return steps

	def on(self, event: str, callback: Callable):
		"""注册回调函数"""
		if event in self.callbacks:
			self.callbacks[event].append(callback)

	def _trigger(self, event: str, data: Any = None):
		"""触发回调"""
		for callback in self.callbacks.get(event, []):
			try:
				callback(data)
			except Exception as e:
				print(f"回调执行失败: {e}")

	def _log(self, message: str, level: str = "INFO"):
		"""记录日志"""
		log_entry = {
			"timestamp": time.time(),
			"level": level,
			"message": message
		}
		self.logs.append(log_entry)
		# print(f"[{level}] {message}")
		logger = self._get_logger()  # 用的时候再导入
		logger.info(log_entry)

	def run(self, context: Any, stop_on_error: bool = True) -> Any:
		"""运行工作流"""
		self._log("工作流开始执行")
		self._trigger("on_workflow_start", context)

		for step in self.steps:
			self._log(f"执行步骤: {step.name}")
			self._trigger("on_step_start", {"step": step.name, "context": context})

			step.status = WorkflowStatus.RUNNING
			start_time = time.time()

			try:
				# 执行Agent
				result = step.agent.execute(context)
				step.result = result
				step.duration = time.time() - start_time
				step.status = WorkflowStatus.COMPLETED

				# 更新context（如果返回了新的context）
				if result is not None:
					context = result

				self._log(f"步骤 {step.name} 完成，耗时 {step.duration:.2f}s")
				self._trigger("on_step_end", {"step": step.name, "context": context, "duration": step.duration})

			except Exception as e:
				step.status = WorkflowStatus.FAILED
				step.error = str(e)
				step.duration = time.time() - start_time
				self._log(f"步骤 {step.name} 失败: {e}", "ERROR")
				# self._trigger("on_step_end", {"step": step.name, "context": context, "duration": step.duration})

				if stop_on_error:
					break

		workflow_status = all(s.status == WorkflowStatus.COMPLETED for s in self.steps)
		self._trigger("on_workflow_end", {
			"context": context,
			"success": workflow_status,
			"logs": self.logs
		})

		if workflow_status:
			self._log("工作流执行成功")
		else:
			self._log("工作流执行失败", "ERROR")

		return context

	def get_summary(self) -> Dict:
		"""获取执行摘要"""
		return {
			"total_steps": len(self.steps),
			"completed_steps": sum(1 for s in self.steps if s.status == WorkflowStatus.COMPLETED),
			"failed_steps": sum(1 for s in self.steps if s.status == WorkflowStatus.FAILED),
			"total_duration": sum(s.duration for s in self.steps),
			"steps": [
				{
					"name": s.name,
					"status": s.status.value,
					"duration": s.duration,
					"error": s.error
				}
				for s in self.steps
			]
		}

# def export_logs(self, filepath: str):
# 	"""导出日志"""
# 	with open(filepath, 'w', encoding='utf-8') as f:
# 		json.dump(self.logs, f, ensure_ascii=False, indent=2)


def create_orchestrator(
		llm_client=None,
		review_mode: str = "standard",
		enable_search: bool = False,
		tavily_api_key: str = None):
	"""创建完整的工作流编排器（依赖注入）"""
	from agents import (
		InputAgent, ClassifierAgent, ElevationAgent, TitleAgent,
		OutlineAgent, MaterialAgent, PolishAgent, ReviewAgent
	)

	agents = {
		"input": InputAgent(llm_client),
		"classifier": ClassifierAgent(llm_client),
		"elevation": ElevationAgent(llm_client),
		"outline": OutlineAgent(llm_client),
		"title": TitleAgent(llm_client),
		"material": MaterialAgent(llm_client, enable_search, tavily_api_key),
		"polish": PolishAgent(llm_client),
		"review": ReviewAgent(llm_client, review_mode)
	}

	return WorkflowOrchestrator(agents)
