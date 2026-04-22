"""阶段 0 — 外部进单接口 + 系统监控。"""
from datetime import datetime
from typing import Any, Dict, get_args
from fastapi import APIRouter, BackgroundTasks
from app.schemas.order import AnomalyOrder, Evidence, AISuggestion, PaymentChannel, Currency
from app.storage import orders_repo
from app.pipeline import process_order
from app.ml.monitoring.perf_tracker import get_pipeline_tracker
from app.ml.serving.model_registry import list_serving_models
from app.storage import runtime_log

router = APIRouter()


HIGH_RISK_COUNTRIES = {"RU", "NG", "PH", "TR"}


def _first(payload: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return default


def _risk_level(score: int) -> str:
    if score >= 85:
        return "critical"
    if score >= 65:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _coerce_payment_event(payload: Dict[str, Any]) -> AnomalyOrder:
    """Accept either full AnomalyOrder or a production-style minimal payment event.

    Minimal event fields are intentionally close to production systems:
    orderNo/userId/amount/currency/channel/ip/device/merchantId.
    Missing AI fields are initialized so the 9-stage pipeline can enrich them.
    """
    try:
        return AnomalyOrder(**payload)
    except Exception:
        pass

    now = datetime.utcnow().isoformat() + "Z"
    amount = float(_first(payload, "amount", "orderAmount", "payAmount", default=0))
    ip_country = str(_first(payload, "ipCountry", "country", "countryCode", default="CN")).upper()
    device = str(_first(payload, "device", "deviceModel", "userAgent", default="Unknown Device"))
    channel = str(_first(payload, "channel", "paymentChannel", default="bank_transfer")).lower()
    if channel not in get_args(PaymentChannel):
        channel = "bank_transfer"
    currency = str(_first(payload, "currency", default="CNY")).upper()
    if currency not in get_args(Currency):
        currency = "CNY"

    risk_score = 20
    reasons = []
    if amount >= 50000:
        risk_score += 35
        reasons.append("大额交易")
    elif amount >= 10000:
        risk_score += 20
        reasons.append("金额高于常规阈值")
    if ip_country in HIGH_RISK_COUNTRIES:
        risk_score += 25
        reasons.append("高风险国家/地区 IP")
    if "headless" in device.lower() or "emulator" in device.lower():
        risk_score += 25
        reasons.append("可疑设备环境")
    risk_score = min(risk_score, 99)
    primary_category = "fraud" if risk_score >= 65 else "behavioral" if risk_score >= 40 else "user"
    sub_types = reasons or ["生产事件待模型研判"]

    evidence = [
        Evidence(
            id="ingest-ev-1",
            type="ml",
            label="生产事件初始评分",
            detail=f"基于金额/IP/设备的入仓初始风险分={risk_score}",
            weight=0.55,
        )
    ]
    if ip_country in HIGH_RISK_COUNTRIES:
        evidence.append(Evidence(
            id="ingest-ev-2",
            type="ip",
            label="高风险地区",
            detail=f"ipCountry={ip_country}",
            weight=0.7,
        ))

    suggestions = [
        AISuggestion(
            action="review" if risk_score >= 40 else "release",
            label="进入风控流水线复核" if risk_score >= 40 else "低风险放行",
            confidence=75,
            rationale="入仓后将继续经过规则、ML、Agent 和处置策略链路。",
        )
    ]

    order_no = str(_first(
        payload,
        "orderNo", "order_no", "transactionId", "tradeNo",
        default=f"PAY{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
    ))
    user_id = str(_first(payload, "userId", "user_id", "payerId", default="U-UNKNOWN"))
    merchant_id = str(_first(payload, "merchantId", "merchant_id", default="M-UNKNOWN"))

    return AnomalyOrder(
        id=str(_first(payload, "id", default=order_no)),
        orderNo=order_no,
        createdAt=str(_first(payload, "createdAt", "eventTime", "payTime", default=now)),
        amount=amount,
        currency=currency,  # type: ignore[arg-type]
        channel=channel,  # type: ignore[arg-type]
        merchantName=str(_first(payload, "merchantName", "merchant_name", default=merchant_id)),
        merchantId=merchant_id,
        userId=user_id,
        userName=str(_first(payload, "userName", "user_name", default=user_id)),
        userIp=str(_first(payload, "userIp", "ip", "clientIp", default="0.0.0.0")),
        ipCountry=ip_country,
        device=device,
        deviceFingerprint=str(_first(payload, "deviceFingerprint", "deviceId", default=f"FP-{user_id}-{order_no}")),
        status="pending_review" if risk_score >= 40 else "released",
        primaryCategory=primary_category,  # type: ignore[arg-type]
        subTypes=sub_types,
        riskScore=risk_score,
        riskLevel=_risk_level(risk_score),  # type: ignore[arg-type]
        confidence=75,
        tags=[f"#{x}" for x in sub_types],
        evidence=evidence,
        suggestions=suggestions,
        rootCause=" + ".join(sub_types),
        rcaSummary=f"生产事件已入仓,初始风险分 {risk_score}; 后续流水线会生成完整根因。",
        similarCases=0,
    )


@router.post("/ingest")
async def ingest_order(order: dict, bg: BackgroundTasks):
    """外部系统投递订单 → 自动入仓 + 异步跑流水线。

    payload 至少包含: orderNo, userId, amount, currency, channel, ipCountry, device。
    """
    try:
        o = _coerce_payment_event(order)
    except Exception as e:
        return {"ok": False, "error": f"invalid order schema: {e}"}
    orders_repo.update(o)
    runtime_log.log_new_order({"order_no": o.orderNo, "source": "ingest_api", "amount": o.amount})
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
