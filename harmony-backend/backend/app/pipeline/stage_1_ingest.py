"""Stage 0/1 entry marker for pipeline traces."""
import time
from typing import Any, Dict


def mark_ingest(trace: Dict[str, Any], started_at: float, source: str = "internal_api") -> None:
    trace["stages"].append({
        "stage": "0_ingest",
        "ts_ms": int((time.time() - started_at) * 1000),
        "source": source,
    })
