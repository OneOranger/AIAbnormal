"""Step 3+4+5: train + evaluate + register。"""
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
from loguru import logger

from app.ml.pipelines._common import build_samples, gate_check, register
from app.ml.features import FEATURE_NAMES
from . import CONFIG


def train() -> dict:
    X, y, _ = build_samples()
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=CONFIG["test_size"],
        random_state=CONFIG["random_state"], stratify=y,
    )
    model = xgb.XGBClassifier(
        n_estimators=CONFIG["hyper"]["n_estimators"],
        max_depth=CONFIG["hyper"]["max_depth"],
        learning_rate=CONFIG["hyper"]["learning_rate"],
        objective="binary:logistic", eval_metric="auc",
        tree_method="hist", n_jobs=2,
    )
    model.fit(X_tr, y_tr)
    proba = model.predict_proba(X_te)[:, 1]
    pred = (proba >= 0.5).astype(int)
    auc = float(roc_auc_score(y_te, proba))
    prec, rec, f1, _ = precision_recall_fscore_support(y_te, pred, average="binary", zero_division=0)
    meta = {
        "auc": round(auc, 4), "precision": round(float(prec), 4),
        "recall": round(float(rec), 4), "f1": round(float(f1), 4),
        "train_samples": int(len(X_tr)), "test_samples": int(len(X_te)),
        "feature_importance": dict(zip(FEATURE_NAMES, model.feature_importances_.tolist())),
        "weight": CONFIG["weight"],
    }
    ok, reason = gate_check(meta)
    meta["gate_passed"] = ok
    meta["gate_reason"] = reason
    if not ok:
        logger.warning(f"⚠ {CONFIG['name']} gate FAILED: {reason} — 仍注册便于演示,生产环境应阻止上线")
    register(CONFIG["name"], model, meta)
    return meta


if __name__ == "__main__":
    print(train())
