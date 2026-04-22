"""Stage 9: feedback-loop marker. Real feedback is submitted via /feedback."""
from typing import Any, Dict


def feedback_marker() -> Dict[str, Any]:
    return {"stage": "9_feedback", "awaiting_human": True}
