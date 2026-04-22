"""ato_deepfm 训练 — 用账户类规则+ML标签作为弱监督。"""
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
from sklearn.preprocessing import StandardScaler
from loguru import logger

from app.ml.pipelines._common import build_samples, gate_check, register
from . import CONFIG


def train() -> dict:
    X, y, orders = build_samples()
    # ATO 标签 = 子类型含 "ATO" 或 "账户接管"
    y_ato = np.array([
        1 if any(t in (o.subTypes or []) for t in ["ATO", "账户接管", "Account Takeover"]) else 0
        for o in orders
    ], dtype=np.int32)
    if y_ato.sum() < 5:
        # 兜底用通用标签
        y_ato = y
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    X_tr, X_te, y_tr, y_te = train_test_split(
        Xs, y_ato, test_size=CONFIG["test_size"],
        random_state=CONFIG["random_state"],
        stratify=y_ato if y_ato.sum() > 1 else None,
    )
    model = MLPClassifier(
        hidden_layer_sizes=CONFIG["hyper"]["hidden_layer_sizes"],
        max_iter=CONFIG["hyper"]["max_iter"],
        learning_rate_init=CONFIG["hyper"]["learning_rate_init"],
        random_state=42,
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
    # 把 scaler 一起序列化
    register(CONFIG["name"], {"model": model, "scaler": scaler}, meta)
    logger.info(f"✅ {CONFIG['name']} AUC={auc:.3f}")
    return meta


if __name__ == "__main__":
    print(train())
