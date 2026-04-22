"""Stage 7/8: action-agent validation and gateway-action simulation."""
import time
from typing import Any, Dict, Optional, Tuple

from app.agents import run_action_agent
from app.schemas.order import AnomalyOrder
from app.schemas.pipeline import DispositionPolicy
from app.storage import orders_repo, runtime_log

STATUS_BY_ACTION = {
    "intercept": "intercepted",
    "release": "released",
    "auto_refund": "refunded",
    "review": "pending_review",
    "force_2fa": "pending_review",
    "freeze_account": "escalated",
    "add_blacklist": "intercepted",
    "watchlist": "observing",
    "notify_user": "observing",
    "escalate": "escalated",
}


async def execute_action(
    order: AnomalyOrder,
    policy: Optional[DispositionPolicy],
    final_decision: Dict[str, Any],
    route: str,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    started_at = time.time()
    if not policy or not final_decision:
        return None, {
            "stage": "7_action",
            "ms": int((time.time() - started_at) * 1000),
            "executed": False,
            "skip_reason": "no policy or no agent decision",
        }

    action_out = await run_action_agent(order.model_dump(), policy.model_dump(), final_decision)
    result = action_out.get("result", {}) if isinstance(action_out.get("result"), dict) else {}
    validated = result.get("validated", True)
    human_required = route == "agent_deep_human" or policy.requireHumanApproval
    executed = False

    if validated and policy.autoExecute and not human_required:
        order.status = STATUS_BY_ACTION.get(policy.primaryAction, "pending_review")  # type: ignore[assignment]
        orders_repo.update(order)
        executed = True
        runtime_log.log_action({
            "order_no": order.orderNo,
            "action": policy.primaryAction,
            "secondary_actions": policy.secondaryActions,
            "policy": policy.id,
            "via": "auto",
        })

    return action_out, {
        "stage": "7_action",
        "ms": int((time.time() - started_at) * 1000),
        "validated": validated,
        "executed": executed,
        "human_required": human_required,
        "skip_reason": result.get("skip_reason"),
    }
