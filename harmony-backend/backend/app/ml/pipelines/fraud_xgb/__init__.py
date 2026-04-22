"""fraud_xgb 配置(等价 yaml,Python dict 便于直接 import)。"""
CONFIG = {
    "name": "fraud-xgb-v2",
    "algo": "XGBoost",
    "hyper": {"n_estimators": 150, "max_depth": 5, "learning_rate": 0.1},
    "test_size": 0.2,
    "random_state": 42,
    "weight": 0.40,    # 文档 §3.3 主力权重
}
