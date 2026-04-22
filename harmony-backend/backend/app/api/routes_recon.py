"""对账路由。"""
import time
from typing import Optional, List
from fastapi import APIRouter
from app.schemas.recon import ReconRecord
from app.storage import recon_repo
from app.storage import runtime_log

router = APIRouter()


@router.get("", response_model=List[ReconRecord])
async def list_recon(status: Optional[str] = None, channel: Optional[str] = None,
                     search: Optional[str] = None):
    items = recon_repo.list_all()
    if status and status != "all":
        items = [r for r in items if r.status == status]
    if channel and channel != "all":
        items = [r for r in items if r.channel == channel]
    if search:
        s = search.lower()
        items = [r for r in items if s in r.internalRef.lower() or s in r.channelRef.lower()]
    return items


@router.post("/match")
async def run_recon_match():
    """触发一次本地 AI 对账匹配。

    当前无数据库阶段不改写源记录,而是基于 data/runtime/recon.jsonl 做一次
    全量扫描和汇总,用于前端“一键对账”按钮、审计日志和后续接入真实渠道流水。
    """
    t0 = time.time()
    items = recon_repo.list_all()
    matched = sum(1 for r in items if r.status == "matched")
    discrepancy = len(items) - matched
    total_diff = round(sum(abs(r.diff) for r in items), 2)
    runtime_log.log_action({
        "action": "reconciliation_match",
        "total": len(items),
        "matched": matched,
        "discrepancy": discrepancy,
        "total_diff": total_diff,
    })
    return {
        "ok": True,
        "total": len(items),
        "matched": matched,
        "discrepancy": discrepancy,
        "totalDiff": total_diff,
        "durationMs": int((time.time() - t0) * 1000),
        "message": "AI 对账匹配完成",
    }
