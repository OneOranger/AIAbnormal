"""Storage bootstrap for seed data and local JSONL runtime data."""
from loguru import logger

from app.config import settings
from app.schemas.order import AnomalyOrder
from app.schemas.recon import ReconRecord
from app.schemas.pipeline import (
    RiskRule,
    MLModel,
    AgentConfig,
    KnowledgeBase,
    DispositionPolicy,
    FeedbackRecord,
)
from app.mocks.order_factory import generate_orders
from app.mocks.recon_factory import generate_recon
from app.mocks.pipeline_factory import (
    generate_rules,
    generate_models,
    generate_agents,
    generate_kbs,
    generate_policies,
    generate_feedback,
)

from . import orders_repo, recon_repo
from .generic_repo import GenericRepo
from .jsonl_store import read_json_array, write_json_array


rules_repo = GenericRepo[RiskRule]("rules", RiskRule)
models_repo = GenericRepo[MLModel]("models", MLModel)
agents_repo = GenericRepo[AgentConfig]("agents", AgentConfig)
kbs_repo = GenericRepo[KnowledgeBase]("kbs", KnowledgeBase)
policies_repo = GenericRepo[DispositionPolicy]("policies", DispositionPolicy)
feedback_repo = GenericRepo[FeedbackRecord]("feedback", FeedbackRecord)


_initialized = False


def _as_dicts(items):
    return [item.model_dump() if hasattr(item, "model_dump") else item for item in items]


def _seed_file(name: str):
    return settings.seed_path / f"{name}.json"


def _create_seed(name: str, generator):
    items = generator()
    write_json_array(_seed_file(name), _as_dicts(items))
    return items


def _load_or_create_seed(name: str, model_cls, generator):
    """Load storage/seeds/*.json, generating it once when it is absent."""
    path = _seed_file(name)
    records = read_json_array(path)
    if not records:
        logger.info(f"Seed file missing, creating: {path}")
        return _create_seed(name, generator)
    return [model_cls(**record) for record in records]


def ensure_initialized() -> None:
    """Initialize runtime repositories from storage/seeds when needed."""
    global _initialized
    if _initialized:
        return

    if settings.MOCK_DATA_ENABLED:
        # Demo business data. Disable this for real-flow tests and use /ingest
        # or app.scripts.ingest_events to write production-like events.
        if not orders_repo.list_all():
            logger.info(f"Seeding {settings.MOCK_ORDER_COUNT} orders from storage/seeds/orders.json")
            orders_repo.reset_with(_load_or_create_seed("orders", AnomalyOrder, generate_orders))

        if not recon_repo.list_all():
            logger.info(f"Seeding {settings.MOCK_RECON_COUNT} recon records from storage/seeds/recon.json")
            recon_repo.reset_with(_load_or_create_seed("recon", ReconRecord, generate_recon))
    else:
        logger.info("MOCK_DATA_ENABLED=false, skip demo orders/reconciliation/feedback seeding")
        orders_repo.list_all()
        recon_repo.list_all()

    if settings.SEED_DEFAULT_CONFIG:
        if not rules_repo.list_all():
            logger.info("Seeding rules from storage/seeds/rules.json")
            rules_repo.reset_with(_load_or_create_seed("rules", RiskRule, generate_rules))
        if not models_repo.list_all():
            logger.info("Seeding models from storage/seeds/models.json")
            models_repo.reset_with(_load_or_create_seed("models", MLModel, generate_models))
        if not agents_repo.list_all():
            logger.info("Seeding agents from storage/seeds/agents.json")
            agents_repo.reset_with(_load_or_create_seed("agents", AgentConfig, generate_agents))
        if not kbs_repo.list_all():
            logger.info("Seeding knowledge bases from storage/seeds/kbs.json")
            kbs_repo.reset_with(_load_or_create_seed("kbs", KnowledgeBase, generate_kbs))
        if not policies_repo.list_all():
            logger.info("Seeding policies from storage/seeds/policies.json")
            policies_repo.reset_with(_load_or_create_seed("policies", DispositionPolicy, generate_policies))
    else:
        logger.info("SEED_DEFAULT_CONFIG=false, skip rules/models/agents/policies seeding")

    if settings.MOCK_DATA_ENABLED and not feedback_repo.list_all():
        feedback_repo.reset_with(_load_or_create_seed("feedback", FeedbackRecord, generate_feedback))

    _initialized = True
    logger.info("Storage initialized")


def force_reseed() -> None:
    """Regenerate seed JSON files and reset runtime repositories."""
    logger.warning("Force re-seeding all mock data and config seeds...")
    orders_repo.reset_with(_create_seed("orders", generate_orders))
    recon_repo.reset_with(_create_seed("recon", generate_recon))
    rules_repo.reset_with(_create_seed("rules", generate_rules))
    models_repo.reset_with(_create_seed("models", generate_models))
    agents_repo.reset_with(_create_seed("agents", generate_agents))
    kbs_repo.reset_with(_create_seed("kbs", generate_kbs))
    policies_repo.reset_with(_create_seed("policies", generate_policies))
    feedback_repo.reset_with(_create_seed("feedback", generate_feedback))
    logger.info("Re-seed complete")
