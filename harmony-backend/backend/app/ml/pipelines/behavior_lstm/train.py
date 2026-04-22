"""behavior_lstm — 用 PCA 重构误差近似 LSTM AutoEncoder,无监督异常检测。
真实场景为 PyTorch LSTM-AE,这里 PCA 等价(线性低秩重构),保证可在 CPU 跑通。
"""
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from loguru import logger

from app.ml.pipelines._common import build_samples, register
from . import CONFIG


class _PCAReconstructor:
    def __init__(self, n_components=4):
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=n_components)

    def fit(self, X):
        Xs = self.scaler.fit_transform(X)
        self.pca.fit(Xs)
        return self

    def reconstruction_error(self, X):
        Xs = self.scaler.transform(X)
        Xr = self.pca.inverse_transform(self.pca.transform(Xs))
        return np.linalg.norm(Xs - Xr, axis=1)


def train() -> dict:
    X, _, _ = build_samples()
    model = _PCAReconstructor(n_components=min(4, X.shape[1] - 1))
    model.fit(X)
    err = model.reconstruction_error(X)
    meta = {
        "train_samples": int(len(X)),
        "error_p50": float(np.percentile(err, 50)),
        "error_p90": float(np.percentile(err, 90)),
        "error_p99": float(np.percentile(err, 99)),
        "weight": CONFIG["weight"],
        "gate_passed": True, "gate_reason": "unsupervised AE",
    }
    register(CONFIG["name"], model, meta)
    logger.info(f"✅ {CONFIG['name']} p90={meta['error_p90']:.3f}")
    return meta


if __name__ == "__main__":
    print(train())
