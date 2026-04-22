"""ato_deepfm — 账户接管检测,DeepFM 概念简化为 sklearn MLP + 交叉特征。
真实场景应用 PyTorch DeepFM,这里用 MLPClassifier 等价演示。
"""
CONFIG = {
    "name": "ato-deepfm-v1",
    "algo": "DeepFM",
    "hyper": {"hidden_layer_sizes": (32, 16), "max_iter": 200, "learning_rate_init": 0.01},
    "test_size": 0.2,
    "random_state": 42,
    "weight": 0.20,    # 文档 §3.3
}
