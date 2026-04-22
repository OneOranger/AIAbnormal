"""9 阶段数据流水线 — 严格对齐 backend-design-v1 §6.1。

阶段 0  Ingest             外部进入
阶段 1  Preprocess         字段归一化 + 写 new_orders.jsonl
阶段 2  Rules              规则匹配 + 硬拦截短路
阶段 3  ML Ensemble        7 模型融合(文档 §3.3 公式)
阶段 4  Risk Aggregator    四档路由 (<30 release / <60 轻 / <85 深 / ≥85 强人审)
阶段 5  Multi-Agent        Triage + Knowledge + Specialists + Supervisor
阶段 6  Disposition        匹配 active policy
阶段 7  Action             ActionAgent 二次校验 + 执行 + 写 actions.jsonl
阶段 8  Persist + Push     写 inferences.jsonl 全快照
阶段 9  Feedback Loop      埋点等待人工(由 /feedback API 触发)

时延预算:短路 <200ms / 标准 <2.5s / SLA P99 <3s
"""
import time
from typing import Dict, Any, List
from loguru import logger

from app.schemas.order import AnomalyOrder
from app.rules import get_engine as get_rule_engine
from app.ml.inference import score_order
from app.agents import run_graph, run_action_agent
from app.storage import orders_repo
from app.storage.bootstrap import policies_repo
from app.storage import runtime_log
from app.ml.monitoring.perf_tracker import get_pipeline_tracker


# ---- 路由阈值 (文档 §6.1 阶段 4) ----
ROUTE_RELEASE_BELOW = 30
ROUTE_LIGHT_BELOW = 60
ROUTE_DEEP_BELOW = 85
# >=85 强制人工

# ---- 短路条件 (文档 §6.1 阶段 2) ----
HARD_INTERCEPT_RULE_SCORE = 60   # 规则分加总 ≥60 → 直接拦截

# ---- 时延预算 (文档 §6.2) ----
SLA_SHORT_CIRCUIT_MS = 200
SLA_STANDARD_MS = 2500
SLA_P99_MS = 3000


def _route(fused: float) -> str:
    if fused < ROUTE_RELEASE_BELOW:
        return "release_direct"
    if fused < ROUTE_LIGHT_BELOW:
        return "agent_light"
    if fused < ROUTE_DEEP_BELOW:
        return "agent_deep"
    return "agent_deep_human"


async def process_order(order: AnomalyOrder) -> Dict[str, Any]:
    """端到端 9 阶段处理一个订单。返回完整 trace + 时延预算评估。"""
    trace: Dict[str, Any] = {"order_no": order.orderNo, "stages": []}
    t0 = time.time()
    error_flag = False

    try:
        # ───────── 阶段 0: Ingest ─────────
        trace["stages"].append({
            "stage": "0_ingest",
            "ts_ms": int((time.time() - t0) * 1000),
            "source": "internal_api",
        })

        # ───────── 阶段 1: Preprocess ─────────
        s1 = time.time()
        ctx = order.model_dump()
        ctx["amount"] = order.amount
        ctx["geo"] = {"distinct_country_1h": 1}
        ctx["device"] = {"headless": "Headless" in order.device, "new": False}
        ctx["hour"] = int(order.createdAt[11:13]) if len(order.createdAt) >= 13 else 12
        runtime_log.log_new_order({"order_no": order.orderNo, "amount": order.amount})
        trace["stages"].append({"stage": "1_preprocess", "ms": int((time.time() - s1) * 1000)})

        # ───────── 阶段 2: Rules ─────────
        s2 = time.time()
        hits = get_rule_engine().evaluate(ctx)
        rule_score = sum(h.score_delta for h in hits)
        trace["stages"].append({
            "stage": "2_rules",
            "ms": int((time.time() - s2) * 1000),
            "hit_count": len(hits),
            "rule_score": rule_score,
            "hit_codes": [h.code for h in hits],
        })

        # ───────── 短路: 高分硬拦截 ─────────
        if rule_score >= HARD_INTERCEPT_RULE_SCORE and any(
            h.action == "intercept" for h in hits
        ):
            order.status = "intercepted"
            orders_repo.update(order)
            trace["short_circuit"] = "rule_hard_intercept"
            runtime_log.log_action({
                "order_no": order.orderNo, "action": "intercept",
                "reason": "rule_hard_intercept", "rule_score": rule_score,
            })
            total_ms = int((time.time() - t0) * 1000)
            trace["total_ms"] = total_ms
            trace["sla"] = "short_circuit_ok" if total_ms < SLA_SHORT_CIRCUIT_MS else "short_circuit_slow"
            trace["final_decision"] = {"primary_action": "intercept", "via": "rule_short_circuit"}
            runtime_log.log_inference({"trace": trace, "ml": None, "agent": None})
            return trace

        # ───────── 阶段 3: ML 融合打分 ─────────
        s3 = time.time()
        ml = score_order(order, rule_score_delta=rule_score)
        trace["stages"].append({"stage": "3_ml_ensemble", "ms": int((time.time() - s3) * 1000), "scores": ml})

        # ───────── 阶段 4: Risk Aggregator + 路由 ─────────
        fused = ml.get("fused_score", float(order.riskScore))
        route = _route(fused)
        trace["stages"].append({
            "stage": "4_route", "fused_score": fused, "route": route,
        })

        # 直放短路
        if route == "release_direct":
            order.status = "released"
            orders_repo.update(order)
            trace["short_circuit"] = "low_risk_release"
            total_ms = int((time.time() - t0) * 1000)
            trace["total_ms"] = total_ms
            trace["sla"] = "short_circuit_ok" if total_ms < SLA_SHORT_CIRCUIT_MS else "short_circuit_slow"
            trace["final_decision"] = {"primary_action": "release", "via": "low_risk_short_circuit"}
            runtime_log.log_inference({"trace": trace, "ml": ml, "agent": None})
            return trace

        # ───────── 阶段 5: Multi-Agent ─────────
        s5 = time.time()
        try:
            agent_out = await run_graph(
                order.model_dump(),
                [h.__dict__ for h in hits],
                ml,
            )
        except Exception as e:
            # 文档 §2.3 降级策略:Agent 故障 → ML 评分 + 默认策略
            logger.exception(f"Agent failed, fallback to ML: {e}")
            agent_out = {"final": {
                "primary_category": order.primaryCategory,
                "risk_score": fused, "confidence": 60,
                "root_cause": "Agent 故障,基于 ML 评分降级决策",
                "rca_summary": "降级路径", "evidence": [], "suggestions": [],
            }, "agents": [], "degraded": True}

        final_decision = agent_out.get("final")
        agent_trace = agent_out
        trace["stages"].append({
            "stage": "5_agent",
            "ms": int((time.time() - s5) * 1000),
            "specialist_count": final_decision.get("specialist_count") if final_decision else 0,
            "depth": "deep" if route in ("agent_deep", "agent_deep_human") else "light",
            "human_required": route == "agent_deep_human",
        })

        # ───────── 阶段 6: Disposition Engine ─────────
        s6 = time.time()
        chosen_policy = None
        for p in sorted(policies_repo.list_all(), key=lambda x: -x.priority):
            if not p.enabled:
                continue
            if p.category not in ("all", order.primaryCategory):
                continue
            if fused < p.minScore:
                continue
            chosen_policy = p
            break
        trace["stages"].append({
            "stage": "6_disposition", "ms": int((time.time() - s6) * 1000),
            "policy": chosen_policy.id if chosen_policy else None,
            "auto_execute": chosen_policy.autoExecute if chosen_policy else False,
        })

        # ───────── 阶段 7: Action Agent + 执行 ─────────
        action_out = None
        s7 = time.time()
        if chosen_policy and final_decision:
            action_out = await run_action_agent(
                order.model_dump(),
                chosen_policy.model_dump() if hasattr(chosen_policy, "model_dump") else dict(chosen_policy),
                final_decision,
            )
            ar = action_out.get("result", {}) if isinstance(action_out.get("result"), dict) else {}
            validated = ar.get("validated", True)
            executed = False
            # 强制人工的不自动执行
            if validated and chosen_policy.autoExecute and route != "agent_deep_human":
                if chosen_policy.primaryAction == "intercept":
                    order.status = "intercepted"
                elif chosen_policy.primaryAction == "release":
                    order.status = "released"
                elif chosen_policy.primaryAction == "auto_refund":
                    order.status = "refunded"
                orders_repo.update(order)
                executed = True
                runtime_log.log_action({
                    "order_no": order.orderNo,
                    "action": chosen_policy.primaryAction,
                    "policy": chosen_policy.id,
                    "via": "auto",
                })
            trace["stages"].append({
                "stage": "7_action", "ms": int((time.time() - s7) * 1000),
                "validated": validated, "executed": executed,
                "human_required": route == "agent_deep_human",
                "skip_reason": ar.get("skip_reason"),
            })
        else:
            trace["stages"].append({
                "stage": "7_action", "ms": int((time.time() - s7) * 1000),
                "executed": False, "skip_reason": "no policy or no agent decision",
            })

        # ───────── 阶段 8: Persist 全链路快照 ─────────
        snapshot = {
            "trace": trace, "ml": ml, "agent": agent_trace, "action": action_out,
        }
        runtime_log.log_inference(snapshot)
        trace["stages"].append({"stage": "8_persist", "logged": True})

        # ───────── 阶段 9: Feedback (埋点等待) ─────────
        trace["stages"].append({"stage": "9_feedback", "awaiting_human": True})

        trace["final_decision"] = final_decision
        trace["agent_trace"] = agent_trace
        trace["action_trace"] = action_out

    except Exception as e:
        error_flag = True
        logger.exception("Pipeline failed")
        trace["error"] = str(e)

    # ---- SLA 评估 ----
    total_ms = int((time.time() - t0) * 1000)
    trace["total_ms"] = total_ms
    if total_ms < SLA_SHORT_CIRCUIT_MS:
        trace["sla"] = "short_circuit_ok"
    elif total_ms < SLA_STANDARD_MS:
        trace["sla"] = "standard_ok"
    elif total_ms < SLA_P99_MS:
        trace["sla"] = "p99_ok"
    else:
        trace["sla"] = "slo_breach"

    # 性能埋点
    get_pipeline_tracker().record(total_ms, error=error_flag)

    return trace
