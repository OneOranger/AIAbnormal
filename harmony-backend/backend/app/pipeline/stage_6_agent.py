"""Stage 5: multi-agent reasoning with ML fallback."""
import time
from typing import Any, Dict, List, Tuple

from loguru import logger

from app.agents import run_graph
from app.schemas.order import AnomalyOrder


async def run_agent_analysis(
    order: AnomalyOrder,
    rule_hits: List[Dict[str, Any]],
    ml: Dict[str, Any],
    fused_score: float,
    route: str,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    started_at = time.time()
    try:
        agent_out = await run_graph(order.model_dump(), rule_hits, ml)
    except Exception as exc:
        logger.exception(f"Agent failed, fallback to ML: {exc}")
        agent_out = {
            "final": {
                "primary_category": order.primaryCategory,
                "risk_score": fused_score,
                "confidence": 60,
                "root_cause": "Agent failed; fallback to ML/rule decision.",
                "rca_summary": "Degraded path based on ML score.",
                "evidence": [],
                "suggestions": [],
            },
            "agents": [],
            "degraded": True,
        }

    final_decision = agent_out.get("final") or {}
    stage = {
        "stage": "5_agent",
        "ms": int((time.time() - started_at) * 1000),
        "specialist_count": final_decision.get("specialist_count", 0),
        "depth": "deep" if route in ("agent_deep", "agent_deep_human") else "light",
        "human_required": route == "agent_deep_human",
        "degraded": bool(agent_out.get("degraded")),
    }
    return agent_out, final_decision, stage
