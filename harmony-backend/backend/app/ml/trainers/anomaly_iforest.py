"""训练 IsolationForest 行为异常检测 — 无监督。"""
import numpy as np
from sklearn.ensemble import IsolationForest
from loguru import logger

from app.storage.bootstrap import ensure_initialized
from app.storage import orders_repo
from app.ml.features import to_matrix
from app.ml.registry import get_registry


def train() -> dict:
    ensure_initialized()
    orders = orders_repo.list_all()
    X = to_matrix(orders)
    model = IsolationForest(
        n_estimators=200, contamination=0.18,
        random_state=42, n_jobs=2,
    )
    model.fit(X)
    scores = -model.score_samples(X)  # 越大越异常
    meta = {
        "train_samples": int(len(X)),
        "anomaly_threshold": float(np.percentile(scores, 82)),
        "score_mean": float(scores.mean()),
        "score_std": float(scores.std()),
    }
    get_registry().save("behavior-iforest-v1", model, meta)
    logger.info(f"✅ behavior-iforest-v1 trained: threshold={meta['anomaly_threshold']:.3f}")
    return meta


if __name__ == "__main__":
    print(train())
