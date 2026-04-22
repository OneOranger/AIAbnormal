"""特征工程 — 把 AnomalyOrder 转成 ML 模型可用的数值向量。"""
from typing import Dict, List
import numpy as np

from app.schemas.order import AnomalyOrder

HIGH_RISK_COUNTRIES = {"RU", "NG", "PH", "TR", "VE", "BR"}
HIGH_RISK_DEVICES = {"Headless Chrome", "Emulator-X86"}
HIGH_RISK_CHANNELS = {"bank_transfer", "paypal"}

FEATURE_NAMES = [
    "amount_log", "is_high_risk_country", "is_high_risk_device",
    "is_high_risk_channel", "subtype_count", "evidence_count",
    "evidence_avg_weight", "tags_count",
    "is_cross_border", "is_large_amount",
]


def extract_features(order: AnomalyOrder) -> Dict[str, float]:
    avg_w = (sum(e.weight for e in order.evidence) / len(order.evidence)) if order.evidence else 0.0
    return {
        "amount_log": float(np.log1p(order.amount)),
        "is_high_risk_country": float(order.ipCountry in HIGH_RISK_COUNTRIES),
        "is_high_risk_device": float(order.device in HIGH_RISK_DEVICES),
        "is_high_risk_channel": float(order.channel in HIGH_RISK_CHANNELS),
        "subtype_count": float(len(order.subTypes)),
        "evidence_count": float(len(order.evidence)),
        "evidence_avg_weight": float(avg_w),
        "tags_count": float(len(order.tags)),
        "is_cross_border": float(order.ipCountry != "CN"),
        "is_large_amount": float(order.amount > 10000),
    }


def to_vector(order: AnomalyOrder) -> np.ndarray:
    feats = extract_features(order)
    return np.array([feats[n] for n in FEATURE_NAMES], dtype=np.float32)


def to_matrix(orders: List[AnomalyOrder]) -> np.ndarray:
    return np.vstack([to_vector(o) for o in orders])


def build_label(order: AnomalyOrder) -> int:
    """启发式标签 — 高风险=1。真实场景应来自人工标注/反馈表。"""
    return 1 if order.riskScore >= 65 else 0
