"""PSI 漂移检测 — 文档 §3.4 Step 7。"""
from typing import List, Dict
import numpy as np


def psi(expected: List[float], actual: List[float], buckets: int = 10) -> float:
    """Population Stability Index。<0.1 稳定; 0.1-0.25 轻度漂移; >0.25 严重漂移。"""
    if not expected or not actual:
        return 0.0
    e = np.asarray(expected, dtype=float)
    a = np.asarray(actual, dtype=float)
    breakpoints = np.percentile(e, np.linspace(0, 100, buckets + 1))
    breakpoints[0] -= 1e-6
    breakpoints[-1] += 1e-6
    e_hist, _ = np.histogram(e, bins=breakpoints)
    a_hist, _ = np.histogram(a, bins=breakpoints)
    e_pct = np.clip(e_hist / len(e), 1e-6, None)
    a_pct = np.clip(a_hist / len(a), 1e-6, None)
    return float(np.sum((a_pct - e_pct) * np.log(a_pct / e_pct)))


def detect_drift(model_name: str, recent_scores: List[float], baseline_scores: List[float]) -> Dict:
    val = psi(baseline_scores, recent_scores)
    level = "stable" if val < 0.1 else "warning" if val < 0.25 else "critical"
    return {"model": model_name, "psi": round(val, 4), "level": level,
            "should_retrain": val >= 0.25}
