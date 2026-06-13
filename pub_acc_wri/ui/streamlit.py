#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: jiaojiao
"""Streamlit UI - 完整的Web界面，支持配置管理"""

import streamlit as st
import sys
from pathlib import Path
import time

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import AgentContext, create_agent_chain, run_full_pipeline
from core.llm_client import LLMClient, LLMConfig
from core.config_manager import get_config_manager
from core.workflow import create_orchestrator

# 页面配置
st.set_page_config(
	page_title="公众号文章生成器",
	page_icon="📝",
	layout="wide",
	initial_sidebar_state="expanded"
)


def init_session_state():
	"""初始化session状态"""
	if "generated_articles" not in st.session_state:
		st.session_state.generated_articles = []
	if "current_article" not in st.session_state:
		st.session_state.current_article = None
	if "config_loaded" not in st.session_state:
		st.session_state.config_loaded = False
		st.session_state.llm_config = None
		st.session_state.app_config = None
		st.session_state.active_provider = None


def load_configs():
	"""加载配置到session state"""
	if not st.session_state.config_loaded:
		config_manager = get_config_manager()
		st.session_state.llm_config = config_manager.load_llm_config()
		st.session_state.app_config = config_manager.load_app_config()
		st.session_state.active_provider = config_manager.get_active_provider_config()
		st.session_state.config_loaded = True
		st.session_state.config_manager = config_manager


def save_llm_config():
	"""保存LLM配置"""
	config_manager = st.session_state.config_manager
	if config_manager.save_llm_config(st.session_state.llm_config):
		st.success("✅ LLM配置已保存")
		# 重新加载配置
		st.session_state.active_provider = config_manager.get_active_provider_config()
		return True
	else:
		st.error("❌ 保存失败")
		return False


def save_app_config():
	"""保存应用配置"""
	config_manager = st.session_state.config_manager
	if config_manager.save_app_config(st.session_state.app_config):
		st.success("✅ 应用配置已保存")
		return True
	else:
		st.error("❌ 保存失败")
		return False


def render_sidebar():
	"""渲染侧边栏配置"""
	config_manager = st.session_state.config_manager

	with st.sidebar:
		st.header("⚙️ 配置")

		# 使用Tabs组织配置
		tab1, tab2, tab3 = st.tabs(["🔌 LLM配置", "⚙️ 工作流", "📊 统计"])

		with tab1:
			st.subheader("LLM提供商")

			# 获取可用提供商
			providers = config_manager.get_available_providers()
			provider_options = {p["id"]: p["name"] for p in providers}
			current_active = st.session_state.llm_config.get("active_type", "openai_compatible")

			selected_provider = st.selectbox(
				"选择LLM提供商",
				options=list(provider_options.keys()),
				format_func=lambda x: provider_options.get(x, x),
				index=list(provider_options.keys()).index(current_active) if current_active in provider_options else 0,
				key="provider_select"
			)

			# 如果切换了提供商，更新配置
			if selected_provider != current_active:
				st.session_state.llm_config["active_type"] = selected_provider
				save_llm_config()
				st.rerun()

			st.divider()

			# 显示当前提供商的配置
			st.subheader(f"配置: {provider_options.get(selected_provider, selected_provider)}")

			current_config = st.session_state.llm_config.get(selected_provider, {})

			# 根据提供商类型显示不同的配置项
			if selected_provider == "ollama":
				new_base_url = st.text_input(
					"Ollama地址",
					value=current_config.get("base_url", "http://localhost:11434"),
					key="ollama_url"
				)
				new_model = st.text_input(
					"模型名称",
					value=current_config.get("model_name", "qwen2.5:14b-instruct-q4_K_M"),
					key="ollama_model",
					help="可用模型: ollama list 查看"
				)

				if st.button("应用Ollama配置", key="apply_ollama"):
					st.session_state.llm_config[selected_provider]["base_url"] = new_base_url
					st.session_state.llm_config[selected_provider]["model_name"] = new_model
					if save_llm_config():
						st.rerun()

			elif selected_provider == "custom":
				new_base_url = st.text_input(
					"API地址",
					value=current_config.get("base_url", "http://localhost:8080/v1"),
					key="custom_url"
				)
				new_api_key = st.text_input(
					"API Key",
					value=current_config.get("api_key", ""),
					type="password",
					key="custom_key"
				)
				new_model = st.text_input(
					"模型名称",
					value=current_config.get("model_name", "custom-model"),
					key="custom_model"
				)

				if st.button("应用自定义配置", key="apply_custom"):
					st.session_state.llm_config[selected_provider]["base_url"] = new_base_url
					st.session_state.llm_config[selected_provider]["api_key"] = new_api_key
					st.session_state.llm_config[selected_provider]["model_name"] = new_model
					if save_llm_config():
						st.rerun()

			else:  # openai_compatible
				new_base_url = st.selectbox(
					"API地址",
					options=[
						"https://api.openai.com/v1",
						"https://api.deepseek.com/v1",
						"https://api.siliconflow.cn/v1",
						"https://open.bigmodel.cn/api/paas/v4",
						"自定义"
					],
					key="base_url_select"
				)

				if new_base_url == "自定义":
					new_base_url = st.text_input(
						"自定义API地址",
						value=current_config.get("base_url", "https://api.openai.com/v1"),
						key="custom_base_url",
						help="streamlit178行"
					)

				new_api_key = st.text_input(
					"API Key",
					value=current_config.get("api_key", ""),
					type="password",
					key="api_key",
					help="从提供商网站获取"
				)

				new_model = st.text_input(
					"模型名称",
					value=current_config.get("model_name", "gpt-4o-mini"),
					key="model_name",
					help="例如: gpt-4o-mini, deepseek-chat, glm-4-flash"
				)

				col1, col2 = st.columns(2)
				with col1:
					new_temp = st.slider(
						"温度", 0.0, 1.0,
						value=current_config.get("temperature", 0.7),
						step=0.05,
						key="temperature",
						help="越高越有创意，越低越保守"
					)
				with col2:
					new_max_tokens = st.number_input(
						"最大Token", 512, 1000000,
						value=current_config.get("max_tokens", 4096),
						step=512,
						key="max_tokens"
					)

				if st.button("应用OpenAI配置", key="apply_openai"):
					st.session_state.llm_config[selected_provider]["base_url"] = new_base_url
					st.session_state.llm_config[selected_provider]["api_key"] = new_api_key
					st.session_state.llm_config[selected_provider]["model_name"] = new_model
					st.session_state.llm_config[selected_provider]["temperature"] = new_temp
					st.session_state.llm_config[selected_provider]["max_tokens"] = new_max_tokens
					if save_llm_config():
						st.rerun()

			st.divider()

			# 重置按钮
			col1, col2 = st.columns(2)
			with col1:
				if st.button("🔄 重置默认配置", use_container_width=True):
					if config_manager.reset_to_defaults():
						st.session_state.config_loaded = False
						st.success("已重置为默认配置，请刷新页面")
						st.rerun()
			with col2:
				st.caption("⚠️ 重置会清空所有配置")

		with tab2:
			st.subheader("工作流配置")

			# 复审模式
			review_mode = st.select_slider(
				"复审严格度",
				options=["loose", "standard", "strict"],
				value=st.session_state.app_config.get("workflow", {}).get("review_mode", "standard"),
				key="review_mode",
				help="宽松：只检查结构；标准：检查结构和逻辑；严格：全部检查"
			)

			# 实时搜索
			enable_search = st.checkbox(
				"启用实时搜索",
				value=st.session_state.app_config.get("workflow", {}).get("enable_search", False),
				key="enable_search",
				help="需要配置Tavily API Key"
			)

			if enable_search:
				tavily_key = st.text_input(
					"Tavily API Key",
					value=st.session_state.app_config.get("search", {}).get("tavily_api_key", ""),
					type="password",
					key="tavily_key",
					help="从 tavily.com 获取"
				)
				st.session_state.app_config["search"]["tavily_api_key"] = tavily_key

			# 停止条件
			stop_on_error = st.checkbox(
				"错误时停止",
				value=st.session_state.app_config.get("workflow", {}).get("stop_on_error", True),
				key="stop_on_error"
			)

			# 保存按钮
			if st.button("💾 保存工作流配置", use_container_width=True):
				if "workflow" not in st.session_state.app_config:
					st.session_state.app_config["workflow"] = {}
				st.session_state.app_config["workflow"]["review_mode"] = review_mode
				st.session_state.app_config["workflow"]["enable_search"] = enable_search
				st.session_state.app_config["workflow"]["stop_on_error"] = stop_on_error
				save_app_config()

		with tab3:
			st.subheader("使用统计")
			if st.session_state.generated_articles:
				st.metric("生成文章数", len(st.session_state.generated_articles))
				total_words = sum(len(a) for a in st.session_state.generated_articles)
				st.metric("总字数", f"{total_words:,}")
			else:
				st.info("暂无生成记录")

			st.divider()

			# 当前配置摘要
			st.subheader("当前配置摘要")
			active = st.session_state.active_provider
			st.markdown(f"""
            - **LLM提供商**: {active.get('api_type', 'unknown')}
            - **模型**: {active.get('model_name', 'unknown')}
            - **温度**: {active.get('temperature', 0.7)}
            - **复审模式**: {review_mode if 'review_mode' in dir() else st.session_state.app_config.get('workflow', {}).get('review_mode', 'standard')}
            """)


def render_input_form():
	"""渲染输入表单"""
	st.header("✍️ 文章信息")

	col1, col2 = st.columns([2, 1])

	with col1:
		# 从配置读取默认话题
		default_topic = st.session_state.app_config.get("ui", {}).get("default_topic", "为什么年轻人不想加班了")

		topic = st.text_area(
			"**话题**",
			placeholder=default_topic,
			height=80,
			help="这是生成文章的核心主题，建议具体、有讨论空间",
			key="topic_input"
		)

	with col2:
		st.markdown("**示例话题**")
		examples = [
			"为什么年轻人不想加班",
			"AI会取代人类吗",
			"我家楼下的包子铺关了",
			"写给30岁的自己"
		]
		for example in examples:
			if st.button(f"📌 {example}", key=f"example_{example}"):
				st.session_state.topic_input = example
				st.rerun()

	st.markdown("---")

	st.subheader("📖 可选信息（让文章更有温度）")
	st.caption("💡 提示：提供个人经历和独特观点，文章质量可提升30%以上")

	col1, col2 = st.columns(2)

	with col1:
		personal_story = st.text_area(
			"**个人经历**",
			placeholder="我经历过的一件事...（20-100字）\n\n例如：我有个朋友每天加班到10点，结果体检一堆毛病...",
			height=120,
			help="真实经历会让文章更有说服力"
		)

	with col2:
		personal_opinion = st.text_area(
			"**独特观点**",
			placeholder="我的不同看法...（20-100字）\n\n例如：不是年轻人懒，是加班没有性价比，公司给的太少...",
			height=120,
			help="与主流不同的观点会让文章更有价值"
		)

	return {
		"topic": topic,
		"personal_story": personal_story,
		"personal_opinion": personal_opinion
	}


def render_generation_controls():
	"""渲染生成控制按钮"""
	col1, col2, col3 = st.columns([1, 1, 1])

	with col1:
		generate_btn = st.button("🚀 生成文章", type="primary", use_container_width=True)

	with col2:
		clear_btn = st.button("🗑️ 清空内容", use_container_width=True)

	with col3:
		download_btn = st.button("📥 下载文章", use_container_width=True,
		                         disabled=not st.session_state.current_article)

	return generate_btn, clear_btn, download_btn


def render_article_display(article: str):
	"""渲染文章显示"""
	if not article:
		return

	st.markdown("---")

	# 标签页
	tab1, tab2, tab3 = st.tabs(["📄 预览", "📝 Markdown", "🔍 分析"])

	with tab1:
		st.markdown(article)

	with tab2:
		st.code(article, language="markdown")

	with tab3:
		# 文章分析
		word_count = len(article)
		para_count = article.count('\n\n') + 1
		sentence_count = article.count('。') + article.count('！') + article.count('？')

		col1, col2, col3, col4 = st.columns(4)
		with col1:
			st.metric("字数", word_count)
		with col2:
			st.metric("段落数", para_count)
		with col3:
			st.metric("句子数", sentence_count)
		with col4:
			st.metric("预估阅读", f"{max(1, word_count // 300)}分钟")


def render_history():
	"""渲染历史记录"""
	if st.session_state.generated_articles:
		with st.expander("📚 历史记录", expanded=False):
			for i, article in enumerate(reversed(st.session_state.generated_articles[-10:])):
				preview = article[:100] + "..." if len(article) > 100 else article
				col1, col2 = st.columns([4, 1])
				with col1:
					st.caption(preview)
				with col2:
					if st.button("📄 查看", key=f"history_{i}"):
						st.session_state.current_article = article
						st.rerun()


def main():
	"""主函数"""
	init_session_state()
	load_configs()

	st.title("📝 公众号文章生成器")
	st.caption("基于混合架构的智能写作助手 | 6Agent链式工作流 | 支持多LLM提供商")

	# 侧边栏配置
	render_sidebar()

	# 主区域
	input_data = render_input_form()
	generate_btn, clear_btn, download_btn = render_generation_controls()

	# 处理按钮事件
	if generate_btn and input_data["topic"]:
		with st.spinner("🤖 AI正在思考，请稍候... 这可能需要30-60秒"):
			try:
				# 获取当前配置
				config_manager = st.session_state.config_manager
				active_config = config_manager.get_active_provider_config()
				app_config = st.session_state.app_config

				# 创建LLM客户端
				llm_config = LLMConfig(
					api_type=active_config.get("api_type", "openai_compatible"),
					base_url=active_config.get("base_url", ""),
					api_key=active_config.get("api_key", ""),
					model_name=active_config.get("model_name", ""),
					temperature=active_config.get("temperature", 0.7),
					max_tokens=active_config.get("max_tokens", 4096)
				)
				llm_client = LLMClient(llm_config)

				# 创建上下文
				context = AgentContext(
					topic=input_data["topic"],
					user_input={
							"story": input_data.get("personal_story", "无个人经历"),
							"opinion": input_data.get("personal_opinion", "无个人独特观点")
					}
				)

				# 获取工作流配置
				review_mode = app_config.get("workflow", {}).get("review_mode", "standard")
				enable_search = app_config.get("workflow", {}).get("enable_search", False)
				tavily_api_key = app_config.get("search", {}).get("tavily_api_key", "")

				# 使用 WorkflowOrchestrator 创建工作流
				orchestrator = create_orchestrator(
					llm_client=llm_client,
					review_mode=review_mode,
					enable_search=enable_search,
					tavily_api_key=tavily_api_key if enable_search else None
				)

				# 添加回调以显示进度
				progress_bar = st.progress(0)
				status_text = st.empty()

				def on_step_start(data):
					step_name = data["step"]
					status_text.text(f"⏳ 正在执行: {step_name}")

				def on_workflow_end(data):
					if data["success"]:
						status_text.text("✅ 工作流执行完成")
						progress_bar.progress(100)
					else:
						status_text.text("❌ 工作流执行失败")

				orchestrator.on("on_step_start", on_step_start)
				orchestrator.on("on_workflow_end", on_workflow_end)

				# 执行工作流
				start_time = time.time()
				result = orchestrator.run(context, stop_on_error=True)
				duration = time.time() - start_time

				#
				# # 创建Agent链（依赖注入）、
				# agents = create_agent_chain(
				#     llm_client=llm_client,
				#     review_mode=review_mode,
				#     enable_search=enable_search,
				#     tavily_api_key=tavily_api_key if enable_search else None
				# )
				#
				# # 执行工作流
				# start_time = time.time()
				# result = run_full_pipeline(context, agents)
				# duration = time.time() - start_time

				# 保存结果
				st.session_state.current_article = result.final_article
				st.session_state.generated_articles.append(result.final_article)

				# 显示成功信息
				st.success(f"✅ 生成完成！耗时 {duration:.1f} 秒")

				# 显示金句
				if result.review.get("golden_sentences"):
					with st.expander("✨ 金句提取"):
						for sentence in result.review["golden_sentences"]:
							st.markdown(f"> {sentence}")

				# 显示修改建议
				if result.review.get("polish_suggestions"):
					with st.expander("💡 润色建议"):
						for suggestion in result.review["polish_suggestions"]:
							st.markdown(f"- {suggestion}")

			except Exception as e:
				st.error(f"生成失败：{e}")
				st.exception(e)

	elif generate_btn and not input_data["topic"]:
		st.warning("请输入话题")

	if clear_btn:
		st.session_state.current_article = None
		st.rerun()

	if download_btn and st.session_state.current_article:
		st.download_button(
			label="📥 下载Markdown",
			data=st.session_state.current_article,
			file_name=f"article_{int(time.time())}.md",
			mime="text/markdown",
			key="download"
		)

	# 显示当前文章
	render_article_display(st.session_state.current_article)

	# 显示历史
	render_history()

	# 页脚
	st.markdown("---")
	st.caption("💡 提示：个人经历和独特观点会让文章质量提升30%以上 | 配置保存在 config/ 目录下")


if __name__ == "__main__":
	main()
