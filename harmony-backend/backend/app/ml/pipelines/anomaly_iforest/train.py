"""IsolationForest — 文档 §3.2 兜底无监督模型,权重 0.10。"""
import numpy as np
from sklearn.ensemble import IsolationForest
from loguru import logger

from app.ml.pipelines._common import build_samples, register
from . import CONFIG


def train() -> dict:
    X, _, _ = build_samples()
    model = IsolationForest(n_estimators=200, contamination=0.18, random_state=42, n_jobs=2)
    model.fit(X)
    scores = -model.score_samples(X)
    meta = {
        "train_samples": int(len(X)),
        "anomaly_threshold": float(np.percentile(scores, 82)),
        "score_mean": float(scores.mean()),
        "score_std": float(scores.std()),
        "weight": CONFIG["weight"],
        "gate_passed": True, "gate_reason": "unsupervised, no AUC gate",
    }
    register(CONFIG["name"], model, meta)
    logger.info(f"✅ {CONFIG['name']} threshold={meta['anomaly_threshold']:.3f}")
    return meta


if __name__ == "__main__":
    print(train())
