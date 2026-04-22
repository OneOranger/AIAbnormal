"""所有 pipeline 共用的样本构建/评估门槛/注册工具。"""
from __future__ import annotations
from typing import Dict, Any, List, Tuple
import numpy as np
from loguru import logger

from app.storage.bootstrap import ensure_initialized, feedback_repo
from app.storage import orders_repo
from app.ml.features import to_matrix, build_label
from app.ml.registry import get_registry


# ============ Step 1: Sample Construction ============
def build_samples(min_samples: int = 50) -> Tuple[np.ndarray, np.ndarray, List[Any]]:
    """统一样本构建。来源: 历史订单 + 人工反馈强标签(若有)。"""
    ensure_initialized()
    orders = orders_repo.list_all()
    if len(orders) < min_samples:
        raise RuntimeError(f"样本不足 ({len(orders)} < {min_samples})")

    # 用反馈表强化正样本(confirm=拦截+isCorrect=true 视为强阳)
    feedback_index: Dict[str, int] = {}
    for fb in feedback_repo.list_all():
        if fb.feedbackType == "confirm" and fb.finalAction == "intercept":
            feedback_index[fb.orderNo] = 1
        elif fb.feedbackType == "false_positive":
            feedback_index[fb.orderNo] = 0

    X = to_matrix(orders)
    y = np.array([
        feedback_index.get(o.orderNo, build_label(o)) for o in orders
    ], dtype=np.int32)

    logger.info(f"📦 build_samples: {len(orders)} samples, pos_rate={y.mean():.3f}, "
                f"feedback_strong={len(feedback_index)}")
    return X, y, orders


# ============ Step 4: Evaluation Gates ============
EVAL_GATES = {
    "auc_min": 0.80,           # 文档 0.92 是稳定期目标,演示用 0.80 起步
    "f1_min": 0.50,
    "psi_max": 0.20,
}


def gate_check(metrics: Dict[str, float]) -> Tuple[bool, str]:
    if metrics.get("auc", 0) < EVAL_GATES["auc_min"]:
        return False, f"AUC {metrics.get('auc'):.3f} < {EVAL_GATES['auc_min']}"
    if metrics.get("f1", 0) < EVAL_GATES["f1_min"]:
        return False, f"F1 {metrics.get('f1'):.3f} < {EVAL_GATES['f1_min']}"
    return True, "ok"


# ============ Step 5: Register ============
def register(name: str, model: Any, meta: Dict[str, Any]) -> None:
    get_registry().save(name, model, meta)
    logger.info(f"✅ Registered {name}: {meta}")
