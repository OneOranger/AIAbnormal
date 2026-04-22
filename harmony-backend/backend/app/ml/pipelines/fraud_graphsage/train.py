"""fraud_graphsage — 用 networkx 构图(用户-设备-IP)+ LogReg 学中心性 → 团伙分。
真实场景为 PyG GraphSAGE,这里用图特征 + LR 等价演示,产出可解释 cluster_id。
"""
from collections import defaultdict
import numpy as np
import networkx as nx
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
from loguru import logger

from app.ml.pipelines._common import build_samples, gate_check, register
from . import CONFIG


def _build_graph(orders):
    G = nx.Graph()
    for o in orders:
        u = f"user::{o.userId}"
        d = f"dev::{o.device}"
        ip = f"ip::{o.ipCountry}"
        G.add_node(u, kind="user")
        G.add_node(d, kind="device")
        G.add_node(ip, kind="ip")
        G.add_edge(u, d)
        G.add_edge(u, ip)
        G.add_edge(d, ip)
    return G


def _node_features(G, orders):
    deg = dict(G.degree())
    try:
        bc = nx.betweenness_centrality(G, k=min(50, len(G.nodes)))
    except Exception:
        bc = {n: 0.0 for n in G.nodes}
    feats = []
    cluster_id = {}
    for i, comp in enumerate(nx.connected_components(G)):
        for n in comp:
            cluster_id[n] = i
    for o in orders:
        u = f"user::{o.userId}"
        feats.append([
            float(deg.get(u, 0)),
            float(bc.get(u, 0.0)),
            float(cluster_id.get(u, 0)),
            float(o.amount > 5000),
        ])
    return np.array(feats, dtype=np.float32), cluster_id


def train() -> dict:
    _, y, orders = build_samples()
    G = _build_graph(orders)
    X, cluster_map = _node_features(G, orders)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = LogisticRegression(max_iter=500)
    model.fit(X_tr, y_tr)
    proba = model.predict_proba(X_te)[:, 1]
    try:
        auc = float(roc_auc_score(y_te, proba))
    except Exception:
        auc = 0.5
    pred = (proba >= 0.5).astype(int)
    prec, rec, f1, _ = precision_recall_fscore_support(y_te, pred, average="binary", zero_division=0)
    n_clusters = len(set(cluster_map.values()))
    meta = {
        "auc": round(auc, 4), "precision": round(float(prec), 4),
        "recall": round(float(rec), 4), "f1": round(float(f1), 4),
        "train_samples": int(len(X_tr)),
        "n_clusters": n_clusters, "n_nodes": G.number_of_nodes(),
        "weight": CONFIG["weight"],
    }
    meta["gate_passed"], meta["gate_reason"] = gate_check(meta)
    register(CONFIG["name"], {"model": model, "cluster_map": cluster_map}, meta)
    logger.info(f"✅ {CONFIG['name']} AUC={auc:.3f} clusters={n_clusters}")
    return meta


if __name__ == "__main__":
    print(train())
