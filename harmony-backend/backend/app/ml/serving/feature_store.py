"""在线特征仓库 — 用 DiskCache 存近实时聚合特征(替代 Redis Feature Store)。

对齐文档 §3.4 Step 2:在线/离线特征一致性。
"""
from typing import Dict, Any, Optional
from app.storage.cache import get_cache


_PREFIX = "feat::"


def get(user_id: str) -> Optional[Dict[str, Any]]:
    return get_cache().get(_PREFIX + user_id)


def put(user_id: str, features: Dict[str, Any], ttl: int = 3600) -> None:
    get_cache().set(_PREFIX + user_id, features, expire=ttl)


def increment(user_id: str, key: str, delta: int = 1) -> int:
    cache = get_cache()
    full = _PREFIX + user_id
    feats = cache.get(full) or {}
    feats[key] = int(feats.get(key, 0)) + delta
    cache.set(full, feats, expire=3600)
    return feats[key]
