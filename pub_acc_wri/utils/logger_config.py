#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 19:08

from loguru import logger
import os
import sys

# 1. 确保日志文件夹存在
os.makedirs("logs", exist_ok=True)

# 2. 清空默认自带的处理器
logger.remove()

# 3. 统一日志格式
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}"

# 4. 添加控制台输出
logger.add(
    sys.stderr,
    format=LOG_FORMAT,
    level="DEBUG"
)

# 5. 添加日志文件输出，自动按天切割、自动清理
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    format=LOG_FORMAT,
    rotation="00:00",    # 每天0点分割
    retention="7 days",  # 保留7天日志
    encoding="utf-8",
    level="INFO"
)

# 对外导出日志对象
__all__ = ["logger"]