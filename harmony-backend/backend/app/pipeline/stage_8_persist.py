"""Stage 8: persist full inference snapshots for audit."""
from typing import Any, Dict

from app.storage import runtime_log


def persist_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    runtime_log.log_inference(snapshot)
    return {"stage": "8_persist", "logged": True}
