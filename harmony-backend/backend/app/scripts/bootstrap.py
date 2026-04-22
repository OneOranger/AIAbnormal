"""一键初始化 — 生成 mock + 训练 7 个 ML 模型 + 索引 RAG。"""
from loguru import logger


def main():
    logger.info("=" * 60)
    logger.info("🚀 AI Payment Anomaly Backend - Bootstrap v2")
    logger.info("=" * 60)

    # 1. 种子数据
    from app.storage import bootstrap as sb
    sb.ensure_initialized()

    # 2. 训练 7 个模型
    logger.info("\n📚 Training 7 ML models (≈60s)...")
    from app.ml.scheduler.retrain_jobs import retrain_all
    res = retrain_all()
    for name, r in res.items():
        if r.get("ok"):
            m = r.get("meta", {})
            logger.info(f"  ✅ {name}: AUC={m.get('auc', '-')}, F1={m.get('f1', '-')}")
        else:
            logger.error(f"  ❌ {name}: {r.get('error')}")

    # 3. RAG
    logger.info("\n📖 Indexing RAG seed docs...")
    try:
        from app.rag import index_seed_docs
        index_seed_docs()
    except Exception as e:
        logger.warning(f"RAG indexing skipped: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("✅ Bootstrap complete. Run: uvicorn app.main:app --reload")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
