"""模型版本仓库 — 桥接 ml/registry.py,提供 list/promote 接口给 API。"""
from typing import List, Dict, Any
from app.ml.registry import get_registry
from app.ml.serving.ensemble import DEFAULT_WEIGHTS


def list_serving_models() -> List[Dict[str, Any]]:
    """列出当前在线服务的模型 + 元信息 + 权重。"""
    reg = get_registry()
    out = []
    for name, weight in DEFAULT_WEIGHTS.items():
        meta = reg.meta(name)
        out.append({
            "name": name,
            "loaded": reg.has(name),
            "weight": weight,
            "metrics": {k: meta.get(k) for k in ["auc", "f1", "precision", "recall"]},
            "train_samples": meta.get("train_samples"),
            "gate_passed": meta.get("gate_passed", False),
        })
    return out
