"""规则 / 模型 / Agent / 处置 / KB / 反馈 — 通用 in-memory + JSONL 仓库。"""
from typing import List, Dict, Optional, TypeVar, Generic, Type
from threading import RLock
from pathlib import Path
from loguru import logger
from pydantic import BaseModel

from app.config import settings
from .jsonl_store import read_all, write_all, append

T = TypeVar("T", bound=BaseModel)


class GenericRepo(Generic[T]):
    def __init__(self, name: str, model_cls: Type[T]):
        self.name = name
        self.model_cls = model_cls
        self.file: Path = settings.runtime_path / f"{name}.jsonl"
        self._items: Dict[str, T] = {}
        self._lock = RLock()
        self._loaded = False

    def _ensure(self):
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            for r in read_all(self.file):
                try:
                    obj = self.model_cls(**r)
                    self._items[getattr(obj, "id")] = obj
                except Exception as e:
                    logger.warning(f"[{self.name}] skip: {e}")
            self._loaded = True
            logger.info(f"📦 Loaded {len(self._items)} {self.name}")

    def reset_with(self, items: List[T]):
        with self._lock:
            self._items.clear()
            for it in items:
                self._items[getattr(it, "id")] = it
            write_all(self.file, [i.model_dump() for i in items])
            self._loaded = True

    def list_all(self) -> List[T]:
        self._ensure()
        return list(self._items.values())

    def get(self, id_: str) -> Optional[T]:
        self._ensure()
        return self._items.get(id_)

    def upsert(self, item: T) -> T:
        with self._lock:
            self._ensure()
            self._items[getattr(item, "id")] = item
            write_all(self.file, [i.model_dump() for i in self._items.values()])
            return item

    def patch(self, id_: str, patch: dict) -> Optional[T]:
        with self._lock:
            self._ensure()
            cur = self._items.get(id_)
            if not cur:
                return None
            data = cur.model_dump()
            data.update(patch)
            new_obj = self.model_cls(**data)
            self._items[id_] = new_obj
            write_all(self.file, [i.model_dump() for i in self._items.values()])
            return new_obj

    def append_record(self, item: T):
        """对 feedback 这种 append-only 场景直接追加。"""
        with self._lock:
            self._ensure()
            self._items[getattr(item, "id")] = item
            append(self.file, item.model_dump())
