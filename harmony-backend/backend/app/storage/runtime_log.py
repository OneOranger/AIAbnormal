"""runtime/*.jsonl 全链路审计写入 + 读取 — 文档 §5.1 + §6.1 阶段8。

四种文件:
  new_orders.jsonl    (阶段1 进单埋点)
  inferences.jsonl    (阶段8 推理快照)
  actions.jsonl       (阶段7 处置动作)
  feedback.jsonl      (阶段9 人工反馈) — 已由 GenericRepo 处理

提供 append + 近 N 条读取(漂移/监控用)。
"""
from typing import List, Dict, Any
import time

from app.config import settings
from .jsonl_store import append, iter_records


_NEW_ORDERS = settings.runtime_path / "new_orders.jsonl"
_INFERENCES = settings.runtime_path / "inferences.jsonl"
_ACTIONS = settings.runtime_path / "actions.jsonl"


def log_new_order(order_dict: Dict[str, Any]) -> None:
    append(_NEW_ORDERS, {"ts": time.time(), **order_dict})


def log_inference(snapshot: Dict[str, Any]) -> None:
    append(_INFERENCES, {"ts": time.time(), **snapshot})


def log_action(action_dict: Dict[str, Any]) -> None:
    append(_ACTIONS, {"ts": time.time(), **action_dict})


def recent_inferences(n: int = 100) -> List[Dict[str, Any]]:
    """读最近 N 条推理快照(顺序读所有,取尾部)。"""
    if not _INFERENCES.exists():
        return []
    items = list(iter_records(_INFERENCES))
    return items[-n:]


def recent_inference_scores(model_name: str, n: int = 200) -> List[float]:
    """提取近 N 次推理中某模型的分数。"""
    out: List[float] = []
    for r in recent_inferences(n):
        ms = r.get("ml", {}).get("model_scores", {})
        v = ms.get(model_name)
        if isinstance(v, dict) and "score" in v:
            out.append(float(v["score"]))
    return out


def recent_actions(n: int = 100) -> List[Dict[str, Any]]:
    if not _ACTIONS.exists():
        return []
    items = list(iter_records(_ACTIONS))
    return items[-n:]
