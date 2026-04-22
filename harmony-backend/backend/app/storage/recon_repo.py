"""对账仓库。"""
from typing import List
from threading import RLock
from loguru import logger

from app.config import settings
from app.schemas.recon import ReconRecord
from .jsonl_store import read_all, write_all

_FILE = settings.runtime_path / "recon.jsonl"
_lock = RLock()
_records: List[ReconRecord] = []
_loaded = False


def _ensure_loaded():
    global _loaded
    if _loaded:
        return
    with _lock:
        if _loaded:
            return
        for r in read_all(_FILE):
            try:
                _records.append(ReconRecord(**r))
            except Exception as e:
                logger.warning(f"Skip invalid recon record: {e}")
        _loaded = True
        logger.info(f"📦 Loaded {len(_records)} recon records")


def reset_with(records: List[ReconRecord]) -> None:
    global _loaded
    with _lock:
        _records.clear()
        _records.extend(records)
        write_all(_FILE, [r.model_dump() for r in records])
        _loaded = True


def list_all() -> List[ReconRecord]:
    _ensure_loaded()
    return list(_records)
