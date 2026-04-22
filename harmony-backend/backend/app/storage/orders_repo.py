"""订单仓库 — JSONL + 内存索引,启动时全量加载到 dict。"""
from typing import Dict, List, Optional
from threading import RLock
from loguru import logger

from app.config import settings
from app.schemas.order import AnomalyOrder
from .jsonl_store import read_all, write_all

_FILE = settings.runtime_path / "orders.jsonl"
_lock = RLock()
_orders: Dict[str, AnomalyOrder] = {}
_loaded = False


def _ensure_loaded():
    global _loaded
    if _loaded:
        return
    with _lock:
        if _loaded:
            return
        records = read_all(_FILE)
        for r in records:
            try:
                o = AnomalyOrder(**r)
                _orders[o.id] = o
            except Exception as e:
                logger.warning(f"Skip invalid order record: {e}")
        _loaded = True
        logger.info(f"📦 Loaded {len(_orders)} orders from {_FILE}")


def reset_with(orders: List[AnomalyOrder]) -> None:
    """整库重置(bootstrap 用)。"""
    global _loaded
    with _lock:
        _orders.clear()
        for o in orders:
            _orders[o.id] = o
        write_all(_FILE, [o.model_dump() for o in orders])
        _loaded = True


def list_all() -> List[AnomalyOrder]:
    _ensure_loaded()
    return list(_orders.values())


def get(order_id_or_no: str) -> Optional[AnomalyOrder]:
    _ensure_loaded()
    if order_id_or_no in _orders:
        return _orders[order_id_or_no]
    for o in _orders.values():
        if o.orderNo == order_id_or_no:
            return o
    return None


def update(order: AnomalyOrder) -> None:
    with _lock:
        _ensure_loaded()
        _orders[order.id] = order
        # 全量重写(简化,演示规模 ≤万 OK)
        write_all(_FILE, [o.model_dump() for o in _orders.values()])
