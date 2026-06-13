#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 12:56

"""公众号文章生成器 - 主入口"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_config():
    """加载配置"""
    from config import load_app_config, load_llm_config
    app_config = load_app_config()
    llm_config = load_llm_config()
    return app_config, llm_config


def run_cli():
    """命令行模式"""
    parser = argparse.ArgumentParser(description="公众号文章生成器")
    parser.add_argument("topic", help="文章话题")
    parser.add_argument("--story", help="个人经历", default="")
    parser.add_argument("--opinion", help="独特观点", default="")
    parser.add_argument("--output", help="输出文件路径", default="output.md")
    parser.add_argument("--review-mode", help="复审模式",
                        choices=["loose", "standard", "strict"], default="standard")

    args = parser.parse_args()

    from agents import AgentContext, create_agent_chain, run_full_pipeline
    from core.llm_client import LLMClient

    # 创建LLM客户端（自动从配置加载）
    llm_client = LLMClient()

    # 加载应用配置
    app_config, _ = load_config()

    # 创建Agent链
    agents = create_agent_chain(
        llm_client=llm_client,
        review_mode=args.review_mode,
        enable_search=app_config.get("search", {}).get("enable_search", False),
        tavily_api_key=app_config.get("search", {}).get("tavily_api_key")
    )

    context = AgentContext(
        topic=args.topic,
        user_input={
            "answers": {
                "story": args.story,
                "opinion": args.opinion
            }
        }
    )

    print(f"正在生成文章：{args.topic}")

    try:
        result = run_full_pipeline(context, agents)

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result.final_article)

        print(f"文章已保存到：{args.output}")
        print(f"字数: {len(result.final_article)}")
    except Exception as e:
        print(f"生成失败: {e}")
        sys.exit(1)


def run_ui():
    """UI模式"""
    import subprocess
    ui_path = PROJECT_ROOT / "ui" / "streamlit.py"
    if not ui_path.exists():
        print(f"错误: 找不到UI文件 {ui_path}")
        sys.exit(1)
    subprocess.run(["streamlit", "run", str(ui_path)])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "ui":
            run_ui()
        elif sys.argv[1] == "cli":
            sys.argv.pop(1)
            run_cli()
        else:
            print("使用方法:")
            print("  python main.py ui        # 启动Web界面")
            print("  python main.py cli --topic '话题'  # 命令行模式")
    else:
        print("使用方法:")
        print("  python main.py ui        # 启动Web界面")
        print("  python main.py cli --topic '话题'  # 命令行模式")