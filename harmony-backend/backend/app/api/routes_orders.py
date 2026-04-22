"""订单路由 — 对应前端 api.listOrders / getOrder / executeAction。"""
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.schemas.order import OrderListResponse, ActionRequest, ActionResponse, AnomalyOrder
from app.storage import orders_repo
from app.pipeline import process_order

router = APIRouter()


@router.get("", response_model=OrderListResponse)
async def list_orders(
    page: int = 1, pageSize: int = 20,
    category: Optional[str] = None, riskLevel: Optional[str] = None,
    status: Optional[str] = None, search: Optional[str] = None,
):
    items = orders_repo.list_all()
    if category and category != "all":
        items = [o for o in items if o.primaryCategory == category]
    if riskLevel and riskLevel != "all":
        items = [o for o in items if o.riskLevel == riskLevel]
    if status and status != "all":
        items = [o for o in items if o.status == status]
    if search:
        s = search.lower()
        items = [o for o in items if s in o.orderNo.lower() or s in o.userName.lower()
                 or s in o.merchantName.lower() or s in o.userId.lower()]
    total = len(items)
    start = (page - 1) * pageSize
    return OrderListResponse(items=items[start:start + pageSize], total=total)


@router.get("/{order_id}", response_model=AnomalyOrder)
async def get_order(order_id: str):
    o = orders_repo.get(order_id)
    if not o:
        raise HTTPException(404, "Order not found")
    return o


@router.post("/{order_id}/actions", response_model=ActionResponse)
async def execute_action(order_id: str, req: ActionRequest, bg: BackgroundTasks):
    o = orders_repo.get(order_id)
    if not o:
        raise HTTPException(404, "Order not found")
    status_map = {
        "intercept": "intercepted", "release": "released",
        "auto_refund": "refunded", "review": "pending_review",
        "observe": "observing", "escalate": "escalated",
    }
    if req.action in status_map:
        o.status = status_map[req.action]  # type: ignore
        orders_repo.update(o)
    return ActionResponse(ok=True, message=f"已对订单 {o.orderNo} 执行: {req.action}")


@router.post("/{order_id}/analyze")
async def analyze_order(order_id: str):
    """触发完整 9 阶段流水线 — 演示用。"""
    o = orders_repo.get(order_id)
    if not o:
        raise HTTPException(404, "Order not found")
    trace = await process_order(o)
    return {"ok": True, "trace": trace}
