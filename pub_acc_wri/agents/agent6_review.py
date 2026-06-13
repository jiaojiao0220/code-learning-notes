#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/5/31 12:57

"""Agent 6：自我复审智能体 - 使用加载的复审规则"""

from typing import Dict, Any
from .base import BaseAgent, AgentContext, REVIEW_RULES


class ReviewAgent(BaseAgent):
    """全自动自检6项，不合格自动重写"""

    def __init__(self, llm_client=None, model_name: str = None,
                 review_mode: str = "standard"):
        super().__init__(llm_client, model_name)
        self.review_mode = review_mode
        self.rules = REVIEW_RULES.get(review_mode, REVIEW_RULES["standard"])

    def _get_system_prompt(self) -> str:
        checks = self.rules.keys()
        return f"""你是文章质量评审专家。你需要检查文章是否满足以下标准：
                {self._format_checks()}

                输出：检查结果 + 修改建议 + 是否需要重写"""

    def _format_checks(self) -> str:
        """格式化检查项"""
        checks_desc = {
            "check_structure": "结构标准：符合文体固定骨架",
            "check_logic": "逻辑递进：论点层层深入，不跳跃",
            "check_dialectic": "辩证思维：有不同角度的分析，不极端",
            "check_reverse_priority": "本末倒置：主要矛盾和次要矛盾分清",
            "check_emotion": "情绪过剩：不煽动、不偏激",
            "check_elevation": "立意高远：结尾有升华"
        }

        lines = []
        for key, desc in checks_desc.items():
            if self.rules.get(key, False):
                lines.append(f"- {desc}")

        return "\n".join(lines) if lines else "无额外检查项"

    def execute(self, context: AgentContext) -> AgentContext:
        article = context.polished or context.draft
        genre = context.classification.get("genre", "现象说理")

        # 1. 执行各项检查
        checks = self._run_checks(article, genre)

        # 2. 判断是否需要重写
        need_rewrite = self._need_rewrite(checks)

        # 3. 如果需要重写且规则允许自动重写
        max_rounds = self.rules.get("max_rewrite_rounds", 0)
        rewrite_count = 0

        while need_rewrite and rewrite_count < max_rounds:
            article = self._rewrite_article(article, checks, context)
            checks = self._run_checks(article, genre)
            need_rewrite = self._need_rewrite(checks)
            rewrite_count += 1

        context.final_article = f"主题：{context.user_input.get('title_options',context.topic)}"+article
        context.review["checks"] = checks
        context.review["mode"] = self.review_mode
        context.review["rewrite_count"] = rewrite_count

        return context

    def _run_checks(self, article: str, genre: str) -> Dict[str, bool]:
        """执行各项检查"""
        # 构建需要检查的项
        active_checks = [k for k, v in self.rules.items() if v and k.startswith("check_")]

        if not active_checks:
            return {"all_passed": True}

        prompt = f"""请检查以下文章：

			文章内容：
			{article}...
			
			文体类型：{genre}
			
			需要检查的项：
			{', '.join(active_checks)}
			
			请输出JSON格式的检查结果：
			{{
			  {', '.join([f'"{check}": true/false' for check in active_checks])},
			  "issues": ["问题1", "问题2"],
			  "suggestions": ["修改建议1", "修改建议2"]
			}}
			
			检查标准参考：
			- check_structure：是否包含该文体的标准步骤
			- check_logic：是否有"现象→原因→对策"等递进
			- check_dialectic：是否出现"一方面...另一方面..."或"但是"
			- check_reverse_priority：是否抓住了主要矛盾
			- check_emotion：感叹号不超过{self.rules.get('thresholds', {}).get('max_exclamation', 5)}个，没有极端词汇
			- check_elevation：结尾是否升华到时代/人文/哲理
			"""

        response = self._call_llm(prompt, temperature=0.2)
        checks = self._extract_json(response)

        return checks

    def _need_rewrite(self, checks: Dict[str, bool]) -> bool:
        """判断是否需要重写"""
        if not self.rules.get("auto_rewrite", False):
            return False

        # 找出所有检查项
        check_items = [v for k, v in checks.items() if k.startswith("check_")]

        if not check_items:
            return False

        failed_count = sum(1 for v in check_items if not v)

        if self.review_mode == "loose":
            return failed_count >= 1
        elif self.review_mode == "standard":
            return failed_count >= 2
        else:  # strict
            return failed_count > 0

    def _rewrite_article(self, article: str, checks: Dict, context: AgentContext) -> str:
        """根据检查结果重写文章"""
        issues = checks.get("issues", [])
        suggestions = checks.get("suggestions", [])

        prompt = f"""请根据以下问题重写文章：

			原文：
			
			{article[:2000]}...
			
			发现的问题：
			{chr(10).join(['- ' + i for i in issues])}
			
			修改建议：
			{chr(10).join(['- ' + s for s in suggestions])}
			
			重写要求：
			1. 保持原有核心观点不变
			2. 只修改有问题的部分
			3. 确保修改后符合文体规范
			4. 保持语言风格一致
			
			请输出重写后的完整文章：
			"""

        return self._call_llm(prompt, temperature=0.8)