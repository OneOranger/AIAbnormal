"""ML Pipelines — 每个模型独立目录,按 01→05 阶段组织。

目录骨架(对齐 backend-design-v1 §3.5):
  ml/pipelines/{model_name}/
    ├─ 01_build_samples.py   样本构建
    ├─ 02_feature_eng.py     特征工程
    ├─ 03_train.py           训练
    ├─ 04_evaluate.py        评估(必须通过门槛才上线)
    ├─ 05_register.py        注册到 ModelRegistry
    └─ config.yaml           超参

7 个模型:
  - fraud_xgb          (主力欺诈打分,XGBoost)
  - ato_deepfm         (账户接管,DeepFM-like 简化版)
  - fraud_graphsage    (团伙欺诈,GraphSAGE-like 简化版)
  - anomaly_iforest    (无监督兜底,IsolationForest)
  - behavior_lstm      (行为序列,LSTM-AE 简化版)
  - recon_match        (对账模糊匹配,LightGBM/GBDT)
  - chargeback_pred    (拒付预测,XGBoost)
"""
