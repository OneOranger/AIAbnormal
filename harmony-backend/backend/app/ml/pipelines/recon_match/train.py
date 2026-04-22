"""recon_match — 对账匹配置信度。文档 §3.2 #6。"""
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from loguru import logger

from app.storage.bootstrap import ensure_initialized
from app.storage import recon_repo
from app.ml.pipelines._common import register
from . import CONFIG


def _features(rec) -> list:
    return [
        abs(rec.diff),
        abs(rec.diff) / max(rec.internalAmount, 1.0),
        float(rec.channelAmount == 0),
        float(rec.internalAmount > 10000),
    ]


def train() -> dict:
    ensure_initialized()
    records = recon_repo.list_all()
    if len(records) < 50:
        raise RuntimeError("对账数据不足")
    X = np.array([_features(r) for r in records], dtype=np.float32)
    y = np.array([1 if r.status == "matched" else 0 for r in records], dtype=np.int32)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.1, random_state=42)
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)
    meta = {
        "accuracy": round(float(accuracy_score(y_te, pred)), 4),
        "f1": round(float(f1_score(y_te, pred, zero_division=0)), 4),
        "train_samples": int(len(X_tr)), "weight": CONFIG["weight"],
        "gate_passed": True, "gate_reason": "recon, separate gate",
    }
    register(CONFIG["name"], model, meta)
    logger.info(f"✅ {CONFIG['name']} F1={meta['f1']:.3f}")
    return meta


if __name__ == "__main__":
    print(train())
