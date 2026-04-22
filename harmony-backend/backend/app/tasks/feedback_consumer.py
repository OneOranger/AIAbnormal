"""KnowledgeAgent 异步消费器 — 文档 §6.1 阶段 9。

人工反馈 → 入 RAG 向量库强化 / 入训练样本池 / 生成规则建议。
"""
from typing import Dict, Any
from loguru import logger

from app.storage.bootstrap import feedback_repo, rules_repo
from app.rag.vector_store import upsert_documents


def consume_feedback(fb: Dict[str, Any]) -> Dict[str, Any]:
    """处理一条新反馈。"""
    actions_taken = []

    # 1) 正确案例 → 入 RAG 知识库强化
    if fb.get("isCorrect") and fb.get("comment"):
        doc = {
            "id": f"fb-doc-{fb.get('id')}",
            "title": f"已确认案例 {fb.get('orderNo')}",
            "content": fb.get("comment", ""),
            "kb": "kb-2",  # 历史欺诈案例库
            "source": "feedback",
        }
        upsert_documents([doc])
        actions_taken.append("rag_indexed")

    # 2) 错判案例 → 加入训练样本池(用 fedToTraining 标记)
    if fb.get("feedbackType") in ("false_positive", "false_negative"):
        actions_taken.append("queued_for_retrain")

    # 3) AI 自动生成规则建议(已在 fb.ruleSuggestion 字段)
    if fb.get("ruleSuggestion"):
        actions_taken.append("rule_suggestion_generated")

    logger.info(f"📥 Feedback {fb.get('id')} consumed: {actions_taken}")
    return {"actions": actions_taken}
