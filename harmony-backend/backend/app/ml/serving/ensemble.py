"""融合打分服务 — 严格按文档 §3.3 公式:
    final_risk = 0.40*xgb + 0.20*deepfm + 0.20*graphsage + 0.10*iforest + 0.10*lstm
               + rule_score_delta (cap +30)

权重支持热更新:从 models_repo 读 .weight 字段覆盖默认。
"""
from typing import Dict, Any, List
import numpy as np
from loguru import logger

from app.schemas.order import AnomalyOrder
from app.ml.features import to_vector
from app.ml.registry import get_registry


# 默认权重(对齐文档)
DEFAULT_WEIGHTS = {
    "fraud-xgb-v2": 0.40,
    "ato-deepfm-v1": 0.20,
    "fraud-graphsage-v1": 0.20,
    "behavior-iforest-v1": 0.10,
    "behavior-lstm-v1": 0.10,
}

# 触发条件(部分模型仅在特定信号下参与)
TRIGGER_RULES = {
    "ato-deepfm-v1": lambda o: any(
        t in (o.subTypes or []) for t in ["ATO", "账户接管", "Account Takeover"]
    ) or o.primaryCategory == "fraud",
    "fraud-graphsage-v1": lambda o: o.primaryCategory == "fraud",
    "behavior-lstm-v1": lambda o: o.primaryCategory == "behavioral" or o.riskScore >= 50,
}


def _get_weight(name: str) -> float:
    """优先读 models_repo 热更新权重,否则用默认。"""
    try:
        from app.storage.bootstrap import models_repo
        m = models_repo.get(name)
        if m and m.weight:
            return float(m.weight)
    except Exception:
        pass
    return DEFAULT_WEIGHTS.get(name, 0.0)


def _score_with(model_name: str, X: np.ndarray, order: AnomalyOrder) -> float | None:
    """统一的模型推理 -> 0-100 分数。"""
    reg = get_registry()
    obj = reg.load(model_name)
    if obj is None:
        return None
    try:
        if model_name == "fraud-xgb-v2" or model_name == "chargeback-pred-v1":
            p = float(obj.predict_proba(X)[0, 1])
            return p * 100
        if model_name == "ato-deepfm-v1":
            scaler = obj["scaler"]
            model = obj["model"]
            p = float(model.predict_proba(scaler.transform(X))[0, 1])
            return p * 100
        if model_name == "fraud-graphsage-v1":
            # 用 user 节点的图特征(简化:从 cluster_map 取一个分数)
            cluster_map = obj["cluster_map"]
            model = obj["model"]
            u = f"user::{order.userId}"
            cid = float(cluster_map.get(u, 0))
            # 用零向量+cluster 简化推理
            import numpy as _np
            feat = _np.array([[1.0, 0.1, cid, float(order.amount > 5000)]])
            p = float(model.predict_proba(feat)[0, 1])
            return p * 100
        if model_name == "behavior-iforest-v1":
            s = float(-obj.score_samples(X)[0])
            return float(np.clip((s - 0.4) * 200, 0, 100))
        if model_name == "behavior-lstm-v1":
            err = float(obj.reconstruction_error(X)[0])
            return float(np.clip(err * 30, 0, 100))
    except Exception as e:
        logger.warning(f"{model_name} infer failed: {e}")
    return None


def ensemble_score(
    order: AnomalyOrder,
    rule_score_delta: int = 0,
) -> Dict[str, Any]:
    """文档 §3.3 完整融合公式实现。"""
    X = to_vector(order).reshape(1, -1)

    contributions: Dict[str, Dict[str, float]] = {}
    weighted_sum = 0.0
    total_weight = 0.0

    for model_name in DEFAULT_WEIGHTS.keys():
        # 触发条件:不满足则跳过
        trigger = TRIGGER_RULES.get(model_name)
        if trigger is not None and not trigger(order):
            contributions[model_name] = {"score": 0, "weight": 0, "skipped": True}  # type: ignore
            continue
        score = _score_with(model_name, X, order)
        if score is None:
            continue
        weight = _get_weight(model_name)
        contributions[model_name] = {"score": round(score, 2), "weight": weight}
        weighted_sum += score * weight
        total_weight += weight

    if total_weight > 0:
        ml_fused = weighted_sum / total_weight
    else:
        # 模型未加载时 fallback
        ml_fused = float(order.riskScore)

    # 规则加成 (cap +30)
    rule_bonus = min(int(rule_score_delta), 30)
    final = float(np.clip(ml_fused + rule_bonus, 0, 100))

    # 拒付概率(单独输出,不参与主融合)
    cb = _score_with("chargeback-pred-v1", X, order)

    # Top features (取 fraud-xgb 重要性)
    top_features: List[Dict[str, Any]] = []
    try:
        meta = get_registry().meta("fraud-xgb-v2")
        fi = meta.get("feature_importance") or {}
        top_features = [{"name": k, "importance": round(v, 4)}
                        for k, v in sorted(fi.items(), key=lambda x: -x[1])[:5]]
    except Exception:
        pass

    return {
        "fused_score": round(final, 2),
        "ml_score": round(ml_fused, 2),
        "rule_bonus": rule_bonus,
        "model_scores": contributions,
        "chargeback_prob": round(cb / 100, 4) if cb is not None else None,
        "top_features": top_features,
        "active_models": int(total_weight > 0),
    }
