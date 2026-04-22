"""Stage 6: disposition policy matching."""
import time
from typing import Any, Dict, Optional, Tuple

from app.schemas.order import AnomalyOrder
from app.schemas.pipeline import DispositionPolicy
from app.storage.bootstrap import policies_repo
from app.pipeline.stage_5_router import risk_level_from_score


def select_policy(
    order: AnomalyOrder,
    fused_score: float,
    final_decision: Dict[str, Any],
) -> Tuple[Optional[DispositionPolicy], Dict[str, Any]]:
    started_at = time.time()
    category = final_decision.get("primary_category") or order.primaryCategory
    confidence = int(final_decision.get("confidence") or order.confidence or 0)
    risk_level = risk_level_from_score(fused_score)

    chosen = None
    for policy in sorted(policies_repo.list_all(), key=lambda item: -item.priority):
        if not policy.enabled:
            continue
        if policy.category not in ("all", category):
            continue
        if policy.riskLevel not in ("all", risk_level):
            continue
        if fused_score < policy.minScore:
            continue
        if confidence < policy.minConfidence:
            continue
        chosen = policy
        break

    return chosen, {
        "stage": "6_disposition",
        "ms": int((time.time() - started_at) * 1000),
        "policy": chosen.id if chosen else None,
        "category": category,
        "risk_level": risk_level,
        "confidence": confidence,
        "auto_execute": chosen.autoExecute if chosen else False,
    }
