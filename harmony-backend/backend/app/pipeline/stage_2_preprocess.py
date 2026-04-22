"""Stage 1: normalize and enrich incoming orders for downstream scoring."""
import time
from typing import Any, Dict, Tuple

from app.schemas.order import AnomalyOrder
from app.storage import runtime_log


def preprocess_order(order: AnomalyOrder) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    started_at = time.time()
    ctx = order.model_dump()
    ctx["amount"] = order.amount
    ctx["geo"] = {"distinct_country_1h": 1}
    ctx["device"] = {"headless": "headless" in order.device.lower(), "new": False}
    ctx["hour"] = int(order.createdAt[11:13]) if len(order.createdAt) >= 13 else 12
    runtime_log.log_new_order({"order_no": order.orderNo, "amount": order.amount, "stage": "preprocess"})
    return ctx, {"stage": "1_preprocess", "ms": int((time.time() - started_at) * 1000)}
