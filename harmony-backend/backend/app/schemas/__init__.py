"""Pydantic schemas — 与前端 src/lib/types.ts + pipeline-types.ts 1:1 对齐。
字段命名、可选性、类型必须严格一致,否则前端字段会缺失。
"""
from .order import (
    AnomalyOrder, Evidence, AISuggestion,
    AnomalyCategory, RiskLevel, OrderStatus, PaymentChannel,
    OrderListResponse, ActionRequest, ActionResponse,
)
from .recon import ReconRecord, ReconStatus, ReconDiffType
from .pipeline import (
    RiskRule, MLModel, MLFeature, AgentConfig, AgentTool,
    KnowledgeBase, DispositionPolicy, FeedbackRecord,
)
from .chat import ChatMessage, ChatRequest, ChatResponse

__all__ = [
    "AnomalyOrder", "Evidence", "AISuggestion",
    "AnomalyCategory", "RiskLevel", "OrderStatus", "PaymentChannel",
    "OrderListResponse", "ActionRequest", "ActionResponse",
    "ReconRecord", "ReconStatus", "ReconDiffType",
    "RiskRule", "MLModel", "MLFeature", "AgentConfig", "AgentTool",
    "KnowledgeBase", "DispositionPolicy", "FeedbackRecord",
    "ChatMessage", "ChatRequest", "ChatResponse",
]
