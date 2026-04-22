"""存储 bootstrap — 首次启动用 mock 工厂填充数据。"""
from loguru import logger

from app.config import settings
from app.schemas.pipeline import (
    RiskRule, MLModel, AgentConfig, KnowledgeBase, DispositionPolicy, FeedbackRecord,
)
from app.mocks.order_factory import generate_orders
from app.mocks.recon_factory import generate_recon
from app.mocks.pipeline_factory import (
    generate_rules, generate_models, generate_agents,
    generate_kbs, generate_policies, generate_feedback,
)

from . import orders_repo, recon_repo
from .generic_repo import GenericRepo


# ============ 全局仓库实例 ============
rules_repo = GenericRepo[RiskRule]("rules", RiskRule)
models_repo = GenericRepo[MLModel]("models", MLModel)
agents_repo = GenericRepo[AgentConfig]("agents", AgentConfig)
kbs_repo = GenericRepo[KnowledgeBase]("kbs", KnowledgeBase)
policies_repo = GenericRepo[DispositionPolicy]("policies", DispositionPolicy)
feedback_repo = GenericRepo[FeedbackRecord]("feedback", FeedbackRecord)


_initialized = False


def ensure_initialized() -> None:
    """如果运行时数据为空,用 mock 工厂填充一次。"""
    global _initialized
    if _initialized:
        return

    if settings.MOCK_DATA_ENABLED:
        # Orders / recon / feedback are demo business data. They can be disabled
        # for real-flow tests that ingest production-like local JSONL files.
        if not orders_repo.list_all():
            logger.info(f"🌱 Seeding {settings.MOCK_ORDER_COUNT} orders...")
            orders_repo.reset_with(generate_orders())

        if not recon_repo.list_all():
            logger.info(f"🌱 Seeding {settings.MOCK_RECON_COUNT} recon records...")
            recon_repo.reset_with(generate_recon())
    else:
        logger.info("MOCK_DATA_ENABLED=false, skip demo orders/reconciliation/feedback seeding")
        # Load existing JSONL files if the tester has already imported local data.
        orders_repo.list_all()
        recon_repo.list_all()

    if settings.SEED_DEFAULT_CONFIG:
        if not rules_repo.list_all():
            logger.info("🌱 Seeding rules ...")
            rules_repo.reset_with(generate_rules())
        if not models_repo.list_all():
            logger.info("🌱 Seeding models ...")
            models_repo.reset_with(generate_models())
        if not agents_repo.list_all():
            logger.info("🌱 Seeding agents ...")
            agents_repo.reset_with(generate_agents())
        if not kbs_repo.list_all():
            logger.info("🌱 Seeding knowledge bases ...")
            kbs_repo.reset_with(generate_kbs())
        if not policies_repo.list_all():
            logger.info("🌱 Seeding policies ...")
            policies_repo.reset_with(generate_policies())
    elif not settings.SEED_DEFAULT_CONFIG:
        logger.info("SEED_DEFAULT_CONFIG=false, skip rules/models/agents/policies seeding")

    if settings.MOCK_DATA_ENABLED and not feedback_repo.list_all():
        feedback_repo.reset_with(generate_feedback())

    _initialized = True
    logger.info("✅ Storage initialized")


def force_reseed() -> None:
    """强制重新生成所有 mock 数据(脚本调用)。"""
    logger.warning("⚠ Force re-seeding all mock data...")
    orders_repo.reset_with(generate_orders())
    recon_repo.reset_with(generate_recon())
    rules_repo.reset_with(generate_rules())
    models_repo.reset_with(generate_models())
    agents_repo.reset_with(generate_agents())
    kbs_repo.reset_with(generate_kbs())
    policies_repo.reset_with(generate_policies())
    feedback_repo.reset_with(generate_feedback())
    logger.info("✅ Re-seed complete")
