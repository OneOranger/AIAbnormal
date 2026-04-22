"""训练 XGBoost 欺诈分类器 — 用 mock orders 做监督学习。
真实场景: 标签来自人工反馈表 + 历史确认案例。
"""
from typing import Tuple
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
from loguru import logger

from app.storage.bootstrap import ensure_initialized
from app.storage import orders_repo
from app.ml.features import to_matrix, build_label, FEATURE_NAMES
from app.ml.registry import get_registry


def train() -> dict:
    ensure_initialized()
    orders = orders_repo.list_all()
    if len(orders) < 50:
        raise RuntimeError("订单数据不足,无法训练")
    X = to_matrix(orders)
    y = np.array([build_label(o) for o in orders], dtype=np.int32)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = xgb.XGBClassifier(
        n_estimators=120, max_depth=5, learning_rate=0.1,
        objective="binary:logistic", eval_metric="auc",
        tree_method="hist", n_jobs=2,
    )
    model.fit(X_tr, y_tr)
    proba = model.predict_proba(X_te)[:, 1]
    pred = (proba >= 0.5).astype(int)
    auc = float(roc_auc_score(y_te, proba))
    prec, rec, f1, _ = precision_recall_fscore_support(y_te, pred, average="binary", zero_division=0)

    importance = model.feature_importances_.tolist()
    feature_importance = dict(zip(FEATURE_NAMES, importance))
    meta = {
        "auc": round(auc, 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1": round(float(f1), 4),
        "train_samples": int(len(X_tr)),
        "test_samples": int(len(X_te)),
        "feature_importance": feature_importance,
    }
    get_registry().save("fraud-xgb-v2", model, meta)
    logger.info(f"✅ fraud-xgb-v2 trained: AUC={auc:.4f}, F1={f1:.4f}")
    return meta


if __name__ == "__main__":
    print(train())
