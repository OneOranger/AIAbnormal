"""Stage 4: fused-risk routing."""

ROUTE_RELEASE_BELOW = 30
ROUTE_LIGHT_BELOW = 60
ROUTE_DEEP_BELOW = 85


def route_by_score(fused_score: float) -> str:
    if fused_score < ROUTE_RELEASE_BELOW:
        return "release_direct"
    if fused_score < ROUTE_LIGHT_BELOW:
        return "agent_light"
    if fused_score < ROUTE_DEEP_BELOW:
        return "agent_deep"
    return "agent_deep_human"


def risk_level_from_score(score: float) -> str:
    if score >= 85:
        return "critical"
    if score >= 65:
        return "high"
    if score >= 40:
        return "medium"
    return "low"
