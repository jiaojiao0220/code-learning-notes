#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author : jiaojiao
# @Time : 2026/6/16 16:03


# 多查询扩展（MQE）
def _prompt_mqe(query: str, n: int) -> List[str]:
	"""使用LLM生成多样化的查询扩展"""
	try:
		from ...core.llm import HelloAgentsLLM
		llm = HelloAgentsLLM()
		prompt = [
			{"role": "system", "content": "你是检索查询扩展助手。生成语义等价或互补的多样化查询。使用中文，简短，避免标点。"},
			{"role": "user", "content": f"原始查询：{query}\n请给出{n}个不同表述的查询，每行一个。"}
		]
		text = llm.invoke(prompt)
		lines = [ln.strip("- \t") for ln in (text or "").splitlines()]
		outs = [ln for ln in lines if ln]
		return outs[:n] or [query]
	except Exception:
		return [query]


# 假设文档嵌入（HyDE）
def _prompt_hyde(query: str) -> Optional[str]:
	"""生成假设性文档用于改善检索"""
	try:
		from ...core.llm import HelloAgentsLLM
		llm = HelloAgentsLLM()
		prompt = [
			{"role": "system", "content": "根据用户问题，先写一段可能的答案性段落，用于向量检索的查询文档（不要分析过程）。"},
			{"role": "user", "content": f"问题：{query}\n请直接写一段中等长度、客观、包含关键术语的段落。"}
		]
		return llm.invoke(prompt)
	except Exception:
		return None


# 扩展检索框架
def search_vectors_expanded(
		store=None,
		query: str = "",
		top_k: int = 8,
		rag_namespace: Optional[str] = None,
		only_rag_data: bool = True,
		score_threshold: Optional[float] = None,
		enable_mqe: bool = False,
		mqe_expansions: int = 2,
		enable_hyde: bool = False,
		candidate_pool_multiplier: int = 4,
) -> List[Dict]:
	"""
	Search with query expansion using unified embedding and Qdrant.
	"""
	if not query:
		return []

	# 创建默认存储
	if store is None:
		store = _create_default_vector_store()

	# 查询扩展
	expansions: List[str] = [query]

	if enable_mqe and mqe_expansions > 0:
		expansions.extend(_prompt_mqe(query, mqe_expansions))
	if enable_hyde:
		hyde_text = _prompt_hyde(query)
		if hyde_text:
			expansions.append(hyde_text)

	# 去重和修剪
	uniq: List[str] = []
	for e in expansions:
		if e and e not in uniq:
			uniq.append(e)
	expansions = uniq[: max(1, len(uniq))]

	# 分配候选池
	pool = max(top_k * candidate_pool_multiplier, 20)
	per = max(1, pool // max(1, len(expansions)))

	# 构建RAG数据过滤器
	where = {"memory_type": "rag_chunk"}
	if only_rag_data:
		where["is_rag_data"] = True
		where["data_source"] = "rag_pipeline"
	if rag_namespace:
		where["rag_namespace"] = rag_namespace

	# 收集所有扩展查询的结果
	agg: Dict[str, Dict] = {}
	for q in expansions:
		qv = embed_query(q)
		hits = store.search_similar(
			query_vector=qv,
			limit=per,
			score_threshold=score_threshold,
			where=where
		)
		for h in hits:
			mid = h.get("metadata", {}).get("memory_id", h.get("id"))
			s = float(h.get("score", 0.0))
			if mid not in agg or s > float(agg[mid].get("score", 0.0)):
				agg[mid] = h

	# 按分数排序返回
	merged = list(agg.values())
	merged.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
	return merged[:top_k]
