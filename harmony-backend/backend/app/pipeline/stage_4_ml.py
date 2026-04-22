"""Stage 3: ML ensemble scoring."""
import time
from typing import Any, Dict, Tuple

from app.ml.inference import score_order
from app.schemas.order import AnomalyOrder


def score_with_models(order: AnomalyOrder, rule_score: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    started_at = time.time()
    ml = score_order(order, rule_score_delta=rule_score)
    return ml, {"stage": "3_ml_ensemble", "ms": int((time.time() - started_at) * 1000), "scores": ml}
