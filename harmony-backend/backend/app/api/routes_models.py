"""ML 模型路由 — 接入 ml/scheduler 7 模型重训。"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks
from loguru import logger

from app.schemas.pipeline import MLModel
from app.storage.bootstrap import models_repo
from app.ml.scheduler.retrain_jobs import retrain_one, RETRAIN_JOBS

router = APIRouter()


@router.get("", response_model=List[MLModel])
async def list_models():
    return models_repo.list_all()


@router.patch("/{model_id}")
async def update_model(model_id: str, patch: dict):
    updated = models_repo.patch(model_id, patch)
    return {"ok": bool(updated)}


def _retrain_job(model_id: str):
    """后台真实训练 — 走 ml/scheduler 7 模型映射。"""
    if model_id not in RETRAIN_JOBS:
        logger.info(f"No trainer for {model_id}, skipped")
        return
    res = retrain_one(model_id)
    if res.get("ok"):
        meta = res.get("meta", {})
        models_repo.patch(model_id, {
            "auc": meta.get("auc", 0),
            "precision": meta.get("precision", 0),
            "recall": meta.get("recall", 0),
            "f1": meta.get("f1", 0),
            "trainSamples": meta.get("train_samples", 0),
            "lastTrainedAt": datetime.utcnow().isoformat() + "Z",
        })


@router.post("/{model_id}/retrain")
async def retrain_model(model_id: str, bg: BackgroundTasks):
    import time
    job_id = f"job-{int(time.time())}"
    bg.add_task(_retrain_job, model_id)
    return {"ok": True, "jobId": job_id}
