"""Agent 工具集 — 供 Specialist 调用。"""
from typing import Dict, Any, List
from app.storage import orders_repo
from app.rag import retrieve as rag_retrieve
from app.ml.inference import score_order


def query_user_history(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """获取用户历史订单。"""
    history = [o for o in orders_repo.list_all() if o.userId == user_id]
    history.sort(key=lambda o: o.createdAt, reverse=True)
    return [o.model_dump() for o in history[:limit]]


def query_graph_neighbors(order: Dict[str, Any]) -> Dict[str, Any]:
    """简化的图谱查询: 同 IP /24 段 + 同设备指纹的账户。"""
    if not order.get("userIp"):
        return {"neighbors": [], "cluster_size": 0}
    ip_prefix = ".".join(order["userIp"].split(".")[:3])
    same_subnet = [o for o in orders_repo.list_all()
                   if o.userIp.startswith(ip_prefix + ".") and o.userId != order.get("userId")]
    same_device = [o for o in orders_repo.list_all()
                   if o.deviceFingerprint == order.get("deviceFingerprint") and o.userId != order.get("userId")]
    return {
        "subnet_neighbors": len(set(o.userId for o in same_subnet)),
        "device_neighbors": len(set(o.userId for o in same_device)),
        "cluster_size": len(set([o.userId for o in same_subnet + same_device])),
    }


def call_ml(order_dict: Dict[str, Any]) -> Dict[str, Any]:
    from app.schemas.order import AnomalyOrder
    return score_order(AnomalyOrder(**order_dict))


def rag_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    return rag_retrieve(query, top_k=top_k)
