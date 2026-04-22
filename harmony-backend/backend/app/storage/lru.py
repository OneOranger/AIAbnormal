"""LRU 内存缓存 — 文档 §5.2 InMemoryStore 规范实现。

GenericRepo 已实现 dict 全量加载,此处补一个简易 LRU 包装,用于:
  - 高频订单详情查询(避免每次扫描全量 dict)
  - inference 缓存

业务层应通过 get_lru_cache() 获取实例。
"""
from collections import OrderedDict
from threading import RLock
from typing import Any, Optional


class LRUCache:
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self._d: OrderedDict[str, Any] = OrderedDict()
        self._lock = RLock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._d:
                return None
            self._d.move_to_end(key)
            return self._d[key]

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._d:
                self._d.move_to_end(key)
            self._d[key] = value
            if len(self._d) > self.capacity:
                self._d.popitem(last=False)

    def stats(self) -> dict:
        return {"size": len(self._d), "capacity": self.capacity}


_orders_lru = LRUCache(capacity=10000)
_infer_lru = LRUCache(capacity=2000)


def get_orders_lru() -> LRUCache:
    return _orders_lru


def get_infer_lru() -> LRUCache:
    return _infer_lru
