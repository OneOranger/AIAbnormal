"""FastAPI 应用入口。"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys

from app.config import settings
from app.api import (
    routes_orders, routes_recon, routes_agent, routes_rules,
    routes_models, routes_agents_config, routes_policies, routes_system,
)
from app.storage import bootstrap as storage_bootstrap
from app.tasks.scheduler import start_scheduler, stop_scheduler

# ---- Logging ----
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL,
           format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<7}</level> | <cyan>{name}:{line}</cyan> | {message}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Starting {settings.APP_NAME} ({settings.APP_ENV})")
    storage_bootstrap.ensure_initialized()
    # 索引 RAG 种子文档
    try:
        from app.rag import index_seed_docs
        index_seed_docs()
    except Exception as e:
        logger.warning(f"RAG seed skipped: {e}")
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("👋 Shutdown complete")


app = FastAPI(
    title="AI Payment Anomaly Analysis API",
    description="多 Agent (10个) + 7 ML 模型 + 规则引擎 + 9 阶段流水线 + 反馈闭环",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exc(request, exc):
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"ok": False, "error": str(exc)})


@app.get("/health", tags=["System"])
async def health():
    from app.llm.factory import get_active_provider_name
    from app.ml.serving.model_registry import list_serving_models
    models = list_serving_models()
    return {
        "ok": True, "service": settings.APP_NAME, "env": settings.APP_ENV,
        "llm_provider": get_active_provider_name(),
        "version": "2.0.0",
        "ml_models_loaded": sum(1 for m in models if m["loaded"]),
        "ml_models_total": len(models),
    }


@app.get("/", tags=["System"])
async def root():
    return {"message": "AI Payment Anomaly Backend v2", "docs": "/docs", "health": "/health"}


# ---- 路由注册 ----
app.include_router(routes_orders.router, prefix="/orders", tags=["Orders"])
app.include_router(routes_recon.router, prefix="/reconciliation", tags=["Reconciliation"])
app.include_router(routes_agent.router, prefix="/agent", tags=["Agent Chat"])
app.include_router(routes_rules.router, prefix="/rules", tags=["Rules Engine"])
app.include_router(routes_models.router, prefix="/models", tags=["ML Models"])
app.include_router(routes_agents_config.router, prefix="/agents", tags=["Agent Config"])
app.include_router(routes_policies.router, prefix="", tags=["Disposition & Feedback"])
app.include_router(routes_system.router, prefix="", tags=["System & Monitoring"])
