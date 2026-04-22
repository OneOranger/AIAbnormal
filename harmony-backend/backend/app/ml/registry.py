"""模型注册表 — 加载/保存/热更新训练好的 .pkl。"""
import pickle
from pathlib import Path
from typing import Any, Dict, Optional
from threading import RLock
from loguru import logger

from app.config import settings


class ModelRegistry:
    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._meta: Dict[str, dict] = {}
        self._lock = RLock()

    def save(self, name: str, model: Any, meta: Optional[dict] = None) -> Path:
        path = settings.models_path / f"{name}.pkl"
        with path.open("wb") as f:
            pickle.dump({"model": model, "meta": meta or {}}, f)
        with self._lock:
            self._models[name] = model
            self._meta[name] = meta or {}
        logger.info(f"💾 Saved model {name} → {path}")
        return path

    def load(self, name: str) -> Optional[Any]:
        with self._lock:
            if name in self._models:
                return self._models[name]
        path = settings.models_path / f"{name}.pkl"
        if not path.exists():
            return None
        with path.open("rb") as f:
            data = pickle.load(f)
        with self._lock:
            self._models[name] = data["model"]
            self._meta[name] = data.get("meta", {})
        return data["model"]

    def meta(self, name: str) -> dict:
        if name not in self._meta:
            self.load(name)
        return self._meta.get(name, {})

    def has(self, name: str) -> bool:
        if name in self._models:
            return True
        return (settings.models_path / f"{name}.pkl").exists()


_registry: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
