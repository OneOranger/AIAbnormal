"""定时重训任务 — 文档 §3.4 Step 7。"""
from loguru import logger


# 模型 → 训练入口映射
RETRAIN_JOBS = {
    "fraud-xgb-v2": "app.ml.pipelines.fraud_xgb.train",
    "ato-deepfm-v1": "app.ml.pipelines.ato_deepfm.train",
    "fraud-graphsage-v1": "app.ml.pipelines.fraud_graphsage.train",
    "behavior-iforest-v1": "app.ml.pipelines.anomaly_iforest.train",
    "behavior-lstm-v1": "app.ml.pipelines.behavior_lstm.train",
    "recon-match-v1": "app.ml.pipelines.recon_match.train",
    "chargeback-pred-v1": "app.ml.pipelines.chargeback_pred.train",
}


def retrain_one(model_name: str) -> dict:
    import importlib
    mod_path = RETRAIN_JOBS.get(model_name)
    if not mod_path:
        return {"ok": False, "error": f"unknown model {model_name}"}
    try:
        mod = importlib.import_module(mod_path)
        meta = mod.train()
        return {"ok": True, "model": model_name, "meta": meta}
    except Exception as e:
        logger.exception(f"retrain {model_name} failed")
        return {"ok": False, "error": str(e)}


def retrain_all() -> dict:
    out = {}
    for m in RETRAIN_JOBS.keys():
        out[m] = retrain_one(m)
    return out


def weekly_retrain_job():
    """每周凌晨触发的全量重训。"""
    logger.info("⏰ Weekly retrain triggered")
    res = retrain_all()
    ok_count = sum(1 for v in res.values() if v.get("ok"))
    logger.info(f"✅ Weekly retrain done: {ok_count}/{len(res)} succeeded")
    return res


def drift_check_job():
    """每 6 小时漂移检测占位 — 真实场景从 inferences.jsonl 读分数分布。"""
    from app.ml.monitoring.drift_detector import detect_drift
    from app.storage.runtime_log import recent_inference_scores
    out = {}
    baseline = list(range(0, 100))  # 占位:均匀分布作 baseline
    for model in ["fraud-xgb-v2", "behavior-iforest-v1"]:
        recent = recent_inference_scores(model, n=200)
        if recent:
            out[model] = detect_drift(model, recent, baseline)
    if out:
        logger.info(f"🔍 Drift check: {out}")
    return out
