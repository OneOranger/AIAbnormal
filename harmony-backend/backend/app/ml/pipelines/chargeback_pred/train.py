"""chargeback_pred — 用 chargeback 类订单作为正样本训练拒付概率。"""
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
from loguru import logger

from app.ml.pipelines._common import build_samples, gate_check, register
from . import CONFIG


def train() -> dict:
    X, _, orders = build_samples()
    y = np.array([1 if o.primaryCategory == "chargeback" else 0 for o in orders], dtype=np.int32)
    if y.sum() < 5:
        # 没有拒付样本时,把高分单当弱标
        y = np.array([1 if o.riskScore >= 75 else 0 for o in orders], dtype=np.int32)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42,
        stratify=y if y.sum() > 1 else None,
    )
    model = xgb.XGBClassifier(
        n_estimators=120, max_depth=4, learning_rate=0.1,
        objective="binary:logistic", eval_metric="auc", n_jobs=2,
    )
    model.fit(X_tr, y_tr)
    proba = model.predict_proba(X_te)[:, 1]
    pred = (proba >= 0.5).astype(int)
    try:
        auc = float(roc_auc_score(y_te, proba))
    except Exception:
        auc = 0.5
    prec, rec, f1, _ = precision_recall_fscore_support(y_te, pred, average="binary", zero_division=0)
    meta = {
        "auc": round(auc, 4), "precision": round(float(prec), 4),
        "recall": round(float(rec), 4), "f1": round(float(f1), 4),
        "train_samples": int(len(X_tr)), "weight": CONFIG["weight"],
    }
    meta["gate_passed"], meta["gate_reason"] = gate_check(meta)
    register(CONFIG["name"], model, meta)
    logger.info(f"✅ {CONFIG['name']} AUC={auc:.3f}")
    return meta


if __name__ == "__main__":
    print(train())
