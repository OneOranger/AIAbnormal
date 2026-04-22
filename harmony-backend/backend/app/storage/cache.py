"""DiskCache 封装 — 替代 Redis,纯本地文件,进程间共享。"""
from diskcache import Cache
from app.config import settings

_cache: Cache | None = None


def get_cache() -> Cache:
    global _cache
    if _cache is None:
        _cache = Cache(directory=str(settings.cache_path), size_limit=int(2e9))
    return _cache
