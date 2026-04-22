"""一键重训全部 7 个 ML 模型 — 调用 ml/scheduler 统一入口。"""
from app.ml.scheduler.retrain_jobs import retrain_all

if __name__ == "__main__":
    res = retrain_all()
    print("=" * 60)
    for name, r in res.items():
        status = "✅" if r.get("ok") else "❌"
        print(f"{status} {name}: {r.get('meta') or r.get('error')}")
