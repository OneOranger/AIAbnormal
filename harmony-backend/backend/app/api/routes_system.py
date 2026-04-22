"""阶段 0 — 外部进单接口 + 系统监控。"""
from fastapi import APIRouter, BackgroundTasks
from app.schemas.order import AnomalyOrder
from app.storage import orders_repo
from app.pipeline import process_order
from app.ml.monitoring.perf_tracker import get_pipeline_tracker
from app.ml.serving.model_registry import list_serving_models
from app.storage import runtime_log

router = APIRouter()


@router.post("/ingest")
async def ingest_order(order: dict, bg: BackgroundTasks):
    """外部系统投递订单 → 自动入仓 + 异步跑流水线。

    payload 至少包含: orderNo, userId, amount, currency, channel, ipCountry, device。
    """
    try:
        o = AnomalyOrder(**order)
    except Exception as e:
        return {"ok": False, "error": f"invalid order schema: {e}"}
    orders_repo.update(o)
    bg.add_task(_run_pipeline, o)
    return {"ok": True, "orderNo": o.orderNo, "status": "queued"}


async def _run_pipeline(order: AnomalyOrder):
    await process_order(order)


@router.get("/system/perf")
async def perf_stats():
    """流水线性能统计 — QPS / P99 / 错误率。"""
    return get_pipeline_tracker().stats()


@router.get("/system/models")
async def system_models():
    """7 个 ML 模型在线状态 + 权重 + 指标。"""
    return list_serving_models()


@router.get("/system/inferences")
async def recent_inferences(n: int = 50):
    """最近 N 次推理快照(全链路审计)。"""
    return {"items": runtime_log.recent_inferences(n)}


@router.get("/system/actions")
async def recent_actions(n: int = 50):
    return {"items": runtime_log.recent_actions(n)}
