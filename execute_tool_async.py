#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/6/14 23:33
import asyncio
from typing import List, Dict, Union
from concurrent.futures import ThreadPoolExecutor

class ToolRegistry:
    """模拟原有工具注册器，仅演示用"""
    def execute_tool(self, tool_name: str, input_data: str) -> str:
        import time
        time.sleep(2)
        return f"{tool_name} 执行结果：{input_data}"


class ToolManager:
    def __init__(self, max_workers: int = 10, max_concurrent: int = 5, default_timeout: float = 10.0):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.registry = ToolRegistry()
        self.sem = asyncio.Semaphore(max_concurrent)  # 异步并发限流
        self.default_timeout = default_timeout

    async def execute_tool_async(self, tool_name: str, input_data: str) -> str:
        loop = asyncio.get_running_loop()
        async with self.sem:
            fut = loop.run_in_executor(
                self.executor,
                self.registry.execute_tool,
                tool_name,
                input_data
            )
            try:
                return await asyncio.wait_for(fut, timeout=self.default_timeout)
            except asyncio.TimeoutError:
                raise Exception(f"【超时】工具 {tool_name} 超过 {self.default_timeout}s 未返回")

    async def execute_tools_parallel(self, tasks: List[Dict[str, str]]) -> List[Union[str, Exception]]:
        print(f"🚀 开始并行执行 {len(tasks)} 个工具任务")
        async_tasks = []
        for task in tasks:
            tn = task["tool_name"]
            ti = task["input_data"]
            async_tasks.append(self.execute_tool_async(tn, ti))

        # 异常不中断批量任务
        results = await asyncio.gather(*async_tasks, return_exceptions=True)
        print(f"✅ 所有工具任务执行完成")
        return results


# 调用测试
async def main():
    tm = ToolManager(max_concurrent=3)
    task_list = [
        {"tool_name": "Search", "input_data": "query1"},
        {"tool_name": "Calc", "input_data": "1+2"},
        {"tool_name": "ReadFile", "input_data": "data.txt"},
        {"tool_name": "API", "input_data": "xxx"}
    ]
    res_list = await tm.execute_tools_parallel(task_list)
    for idx, res in enumerate(res_list):
        if isinstance(res, Exception):
            print(f"任务{idx} 失败: {res}")
        else:
            print(f"任务{idx} 成功: {res}")

if __name__ == "__main__":
    asyncio.run(main())