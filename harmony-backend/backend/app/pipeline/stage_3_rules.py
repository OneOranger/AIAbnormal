"""Stage 2: rules engine execution and hard-intercept detection."""
import time
from typing import Any, Dict, List, Tuple

from app.rules import get_engine as get_rule_engine

HARD_INTERCEPT_RULE_SCORE = 60


def evaluate_rules(ctx: Dict[str, Any]) -> Tuple[List[Any], int, Dict[str, Any]]:
    started_at = time.time()
    hits = get_rule_engine().evaluate(ctx)
    rule_score = sum(hit.score_delta for hit in hits)
    return hits, rule_score, {
        "stage": "2_rules",
        "ms": int((time.time() - started_at) * 1000),
        "hit_count": len(hits),
        "rule_score": rule_score,
        "hit_codes": [hit.code for hit in hits],
    }


def is_hard_intercept(hits: List[Any], rule_score: int) -> bool:
    return rule_score >= HARD_INTERCEPT_RULE_SCORE and any(hit.action == "intercept" for hit in hits)


def serialize_hits(hits: List[Any]) -> List[Dict[str, Any]]:
    return [hit.__dict__ for hit in hits]
