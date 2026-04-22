"""LangGraph 风格的 9-Agent 编排 — 完整实现 v2。

流水线 (与 backend-design-v1.md 对齐):
  Supervisor (路由)
    ├─→ Triage              (8大类多标签打标)
    ├─→ Knowledge           (RAG 检索,供后续 Specialist 引用)
    ├─→ 并行 Specialists    (按 triage.needs_specialist 分发)
    │    ├─ Fraud
    │    ├─ Behavior
    │    ├─ Recon
    │    ├─ Chargeback
    │    └─ Compliance
    ├─→ Supervisor.merge    (聚合 + 幻觉校验 → 最终决策)
    ├─→ Action              (二次校验,生成执行计划) — 由 orchestrator 触发
    └─→ Report              (生成自然语言报告) — 异步

LangGraph 安装失败时降级到纯 async 编排 (功能完全等价)。
"""
import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger

from .specialist import (
    SpecialistAgent, TriageAgent, KnowledgeAgent,
    ActionAgent, ReportAgent, SupervisorAgent,
)

# ============= 9 个 Agent 实例 (单例) =============
SUPERVISOR = SupervisorAgent()
TRIAGE = TriageAgent()
KNOWLEDGE = KnowledgeAgent()
ACTION = ActionAgent()
REPORT = ReportAgent()

FRAUD = SpecialistAgent("fraud_agent", "fraud", "fraud")
BEHAVIOR = SpecialistAgent("behavior_agent", "behavior", "behavioral")
RECON = SpecialistAgent("recon_agent", "recon", "reconciliation")
CHARGEBACK = SpecialistAgent("chargeback_agent", "chargeback", "chargeback")
COMPLIANCE = SpecialistAgent("compliance_agent", "compliance", "compliance")

ALL_AGENTS = [
    SUPERVISOR, TRIAGE, KNOWLEDGE, ACTION, REPORT,
    FRAUD, BEHAVIOR, RECON, CHARGEBACK, COMPLIANCE,
]

CATEGORY_TO_SPECIALIST = {
    "fraud": FRAUD,
    "behavioral": BEHAVIOR,
    "reconciliation": RECON,
    "chargeback": CHARGEBACK,
    "compliance": COMPLIANCE,
}


def _select_specialists(triage_result: Dict[str, Any], fallback_category: str) -> List[SpecialistAgent]:
    """按 triage 输出选 Specialist。triage 失败则按 order.primaryCategory 兜底。"""
    needs = triage_result.get("needs_specialist") if isinstance(triage_result, dict) else None
    if not needs:
        primary = triage_result.get("primary_category") if isinstance(triage_result, dict) else None
        needs = [primary or fallback_category]
    chosen = []
    for cat in needs:
        agent = CATEGORY_TO_SPECIALIST.get(cat)
        if agent and agent not in chosen:
            chosen.append(agent)
    return chosen or [CATEGORY_TO_SPECIALIST.get(fallback_category, FRAUD)]


async def run_graph(order: Dict[str, Any], rule_hits: List[Dict[str, Any]],
                    ml_scores: Dict[str, Any]) -> Dict[str, Any]:
    """运行 9-Agent 完整流程,返回最终决策 + 各 Agent trace。"""
    fallback_category = order.get("primaryCategory", "fraud")
    trace: List[Dict[str, Any]] = []

    # ───────── Step 1: Triage + Knowledge 并行 ─────────
    rag_query = (
        f"{fallback_category} {' '.join(order.get('subTypes', []))} "
        f"{order.get('amount')} {order.get('channel')} {order.get('ipCountry')}"
    )
    triage_task = TRIAGE.run(order, rule_hits, ml_scores)
    knowledge_task = KNOWLEDGE.run(rag_query, top_k=5)
    triage_out, knowledge_out = await asyncio.gather(triage_task, knowledge_task)
    trace.append(triage_out)
    trace.append(knowledge_out)

    triage_result = triage_out.get("result", {}) if isinstance(triage_out.get("result"), dict) else {}
    rag_hits_for_specialist = knowledge_out.get("result", {}).get("hits", [])
    # 把 KnowledgeAgent 的 hits 适配成 SpecialistAgent 期望的 doc 结构
    rag_compat = [{"doc": {"title": h["title"], "content": h["snippet"]}, "score": h["score"]}
                  for h in rag_hits_for_specialist]

    # ───────── Step 2: 并行 Specialists ─────────
    specialists = _select_specialists(triage_result, fallback_category)
    logger.info(f"🤖 Supervisor → {len(specialists)} specialists: {[s.name for s in specialists]}")
    specialist_results = await asyncio.gather(
        *[s.run(order, rule_hits, ml_scores, rag_hits=rag_compat) for s in specialists],
        return_exceptions=False,
    )
    trace.extend(specialist_results)

    # ───────── Step 3: Supervisor 聚合 ─────────
    supervisor_out = await SUPERVISOR.merge(triage_out, specialist_results, knowledge_out)
    trace.append(supervisor_out)

    parsed = supervisor_out.get("result", {}) if isinstance(supervisor_out.get("result"), dict) else {}
    if "error" in supervisor_out or not parsed or "primary_category" not in parsed:
        # 兜底:取第一个 valid specialist 的输出
        valid = [s for s in specialist_results if "error" not in s and isinstance(s.get("result"), dict)]
        if valid:
            parsed = valid[0].get("result", {})

    fused = ml_scores.get("fused_score", order.get("riskScore", 50))
    final = {
        "primary_category": parsed.get("primary_category", fallback_category),
        "secondary_categories": triage_result.get("secondary_categories", []),
        "sub_types": triage_result.get("sub_types", []),
        "risk_score": parsed.get("risk_score", fused),
        "confidence": parsed.get("confidence", 80),
        "root_cause": parsed.get("root_cause") or parsed.get("summary") or "AI 多 Agent 综合分析",
        "rca_summary": parsed.get("rca_summary") or parsed.get("summary") or "Supervisor 已聚合各 Specialist 结论",
        "evidence": parsed.get("evidence", []),
        "suggestions": parsed.get("suggestions", []),
        "specialist_count": len(specialists),
        "rag_hits": len(rag_hits_for_specialist),
    }
    return {"final": final, "agents": trace}


async def run_action_agent(order: Dict[str, Any], policy: Optional[Dict[str, Any]],
                           agent_decision: Dict[str, Any]) -> Dict[str, Any]:
    """供 orchestrator Stage 8 调用 — 处置二次校验。"""
    return await ACTION.run(order, policy, agent_decision)


async def run_report_agent(order: Dict[str, Any], final_decision: Dict[str, Any],
                           agent_traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    """供 /agent/chat 或定时报告调用 — 自然语言报告。"""
    return await REPORT.run(order, final_decision, agent_traces)
