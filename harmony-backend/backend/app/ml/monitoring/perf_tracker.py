"""性能埋点 — QPS / P99 / 错误率,纯内存滑窗。"""
import time
from collections import deque
from threading import RLock
from typing import Dict


class PerfTracker:
    def __init__(self, window: int = 1000):
        self._lat = deque(maxlen=window)
        self._err = deque(maxlen=window)
        self._ts = deque(maxlen=window)
        self._lock = RLock()

    def record(self, latency_ms: int, error: bool = False):
        with self._lock:
            self._lat.append(latency_ms)
            self._err.append(1 if error else 0)
            self._ts.append(time.time())

    def stats(self) -> Dict:
        with self._lock:
            if not self._lat:
                return {"qps": 0, "p99_ms": 0, "error_rate": 0.0, "samples": 0}
            now = time.time()
            recent = [t for t in self._ts if now - t < 60]
            sorted_lat = sorted(self._lat)
            p99_idx = max(0, int(len(sorted_lat) * 0.99) - 1)
            return {
                "qps": round(len(recent) / 60, 2),
                "p99_ms": int(sorted_lat[p99_idx]),
                "p50_ms": int(sorted_lat[len(sorted_lat) // 2]),
                "error_rate": round(sum(self._err) / len(self._err), 4),
                "samples": len(self._lat),
            }


_PIPELINE_TRACKER = PerfTracker()


def get_pipeline_tracker() -> PerfTracker:
    return _PIPELINE_TRACKER
