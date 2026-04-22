"""Nine-stage order processing pipeline aligned with backend-design-v1.md."""
import time
from typing import Any, Dict

from loguru import logger

from app.schemas.order import AnomalyOrder
from app.storage import orders_repo, runtime_log
from app.ml.monitoring.perf_tracker import get_pipeline_tracker

from .stage_1_ingest import mark_ingest
from .stage_2_preprocess import preprocess_order
from .stage_3_rules import evaluate_rules, is_hard_intercept, serialize_hits
from .stage_4_ml import score_with_models
from .stage_5_router import route_by_score
from .stage_6_agent import run_agent_analysis
from .stage_7_disposition import select_policy
from .stage_8_action import execute_action
from .stage_8_persist import persist_snapshot
from .stage_9_feedback import feedback_marker


SLA_SHORT_CIRCUIT_MS = 200
SLA_STANDARD_MS = 2500
SLA_P99_MS = 3000


def _finish(trace: Dict[str, Any], started_at: float, *, error: bool = False) -> Dict[str, Any]:
    total_ms = int((time.time() - started_at) * 1000)
    trace["total_ms"] = total_ms
    if total_ms < SLA_SHORT_CIRCUIT_MS:
        trace["sla"] = "short_circuit_ok"
    elif total_ms < SLA_STANDARD_MS:
        trace["sla"] = "standard_ok"
    elif total_ms < SLA_P99_MS:
        trace["sla"] = "p99_ok"
    else:
        trace["sla"] = "slo_breach"
    get_pipeline_tracker().record(total_ms, error=error)
    return trace


async def process_order(order: AnomalyOrder) -> Dict[str, Any]:
    """Run one order through ingest, preprocess, rules, ML, Agent, action and feedback markers."""
    started_at = time.time()
    trace: Dict[str, Any] = {"order_no": order.orderNo, "stages": []}
    error_flag = False

    try:
        mark_ingest(trace, started_at)

        ctx, stage = preprocess_order(order)
        trace["stages"].append(stage)

        hits, rule_score, stage = evaluate_rules(ctx)
        trace["stages"].append(stage)
        hit_dicts = serialize_hits(hits)

        if is_hard_intercept(hits, rule_score):
            order.status = "intercepted"
            orders_repo.update(order)
            trace["short_circuit"] = "rule_hard_intercept"
            trace["final_decision"] = {"primary_action": "intercept", "via": "rule_short_circuit"}
            runtime_log.log_action({
                "order_no": order.orderNo,
                "action": "intercept",
                "reason": "rule_hard_intercept",
                "rule_score": rule_score,
            })
            trace["stages"].append(persist_snapshot({"trace": trace, "ml": None, "agent": None}))
            return _finish(trace, started_at)

        ml, stage = score_with_models(order, rule_score)
        trace["stages"].append(stage)

        fused = float(ml.get("fused_score", order.riskScore))
        route = route_by_score(fused)
        trace["stages"].append({"stage": "4_route", "fused_score": fused, "route": route})

        if route == "release_direct":
            order.status = "released"
            orders_repo.update(order)
            trace["short_circuit"] = "low_risk_release"
            trace["final_decision"] = {"primary_action": "release", "via": "low_risk_short_circuit"}
            trace["stages"].append(persist_snapshot({"trace": trace, "ml": ml, "agent": None}))
            return _finish(trace, started_at)

        agent_trace, final_decision, stage = await run_agent_analysis(order, hit_dicts, ml, fused, route)
        trace["stages"].append(stage)

        chosen_policy, stage = select_policy(order, fused, final_decision)
        trace["stages"].append(stage)

        action_trace, stage = await execute_action(order, chosen_policy, final_decision, route)
        trace["stages"].append(stage)

        trace["final_decision"] = final_decision
        trace["agent_trace"] = agent_trace
        trace["action_trace"] = action_trace
        trace["stages"].append(persist_snapshot({
            "trace": trace,
            "ml": ml,
            "agent": agent_trace,
            "action": action_trace,
        }))
        trace["stages"].append(feedback_marker())

    except Exception as exc:
        error_flag = True
        logger.exception("Pipeline failed")
        trace["error"] = str(exc)

    return _finish(trace, started_at, error=error_flag)
