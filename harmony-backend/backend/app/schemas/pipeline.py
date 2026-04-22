"""推理链路 4 模块 schemas — 对应前端 pipeline-types.ts。"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from .order import AnomalyCategory, RiskLevel

# ============ 1. 规则引擎 ============
RuleStatus = Literal["active", "shadow", "draft", "disabled"]
RuleAction = Literal["intercept", "review", "score", "tag", "release"]
RuleScope = Literal["realtime", "offline", "both"]


class RiskRule(BaseModel):
    id: str
    code: str
    name: str
    category: AnomalyCategory
    description: str
    status: RuleStatus
    scope: RuleScope
    priority: int
    condition: str
    action: RuleAction
    scoreDelta: int
    hitCount24h: int
    hitCount7d: int
    precision: float
    recall: float
    falsePositiveRate: float
    owner: str
    updatedAt: str
    createdAt: str
    version: int
    tags: List[str]


# ============ 2. ML 模型 ============
ModelStatus = Literal["online", "shadow", "training", "offline"]
ModelAlgo = Literal[
    "GBDT", "IsolationForest", "XGBoost", "LightGBM",
    "DeepFM", "GraphSAGE", "AutoEncoder",
]
FeatureType = Literal["numeric", "categorical", "embedding", "graph"]


class MLFeature(BaseModel):
    name: str
    importance: float
    type: FeatureType


class MLModel(BaseModel):
    id: str
    name: str
    algo: ModelAlgo
    version: str
    status: ModelStatus
    category: str  # AnomalyCategory | "all"
    description: str
    threshold: float
    weight: float
    auc: float
    precision: float
    recall: float
    f1: float
    ks: float
    qps: int
    p99Latency: int
    driftScore: float
    lastTrainedAt: str
    nextRetrainAt: str
    trainSamples: int
    features: List[MLFeature]
    owner: str
    abTestRatio: Optional[float] = None


# ============ 3. AI Agent ============
LLMProvider = Literal["qwen-max", "deepseek-v3", "gpt-4o", "claude-sonnet", "private-llm"]
AgentTrigger = Literal["auto", "manual", "rule_escalation", "low_confidence"]


class AgentTool(BaseModel):
    name: str
    description: str
    enabled: bool
    callCount24h: int


class KnowledgeBase(BaseModel):
    id: str
    name: str
    type: Literal["rule_doc", "case_history", "regulation", "merchant_profile", "fraud_pattern"]
    documentCount: int
    vectorCount: int
    lastIndexedAt: str
    embedding: Literal["bge-large-zh", "text-embedding-3-large", "m3e-large"]


class AgentConfig(BaseModel):
    id: str
    name: str
    description: str
    enabled: bool
    provider: LLMProvider
    model: str
    temperature: float
    topP: float
    maxTokens: int
    triggers: List[AgentTrigger]
    triggerScore: int
    triggerCategories: List[AnomalyCategory]
    enableMultimodal: bool
    enableCausalGraph: bool
    enableRAG: bool
    ragTopK: int
    ragKnowledgeBases: List[str]
    tools: List[AgentTool]
    systemPrompt: str
    enableHallucinationCheck: bool
    enableFactGrounding: bool
    enableSensitiveFilter: bool
    callCount24h: int
    avgLatencyMs: int
    avgTokens: int
    costUSD24h: float
    hallucinationRate: float


# ============ 4. 处置 + 反馈 ============
DispositionAction = Literal[
    "intercept", "review", "release", "auto_refund",
    "force_2fa", "freeze_account", "add_blacklist",
    "watchlist", "notify_user", "escalate",
]


class DispositionPolicy(BaseModel):
    id: str
    name: str
    description: str
    enabled: bool
    priority: int
    category: str  # AnomalyCategory | "all"
    riskLevel: str  # RiskLevel | "all"
    minScore: int
    minConfidence: int
    primaryAction: DispositionAction
    secondaryActions: List[DispositionAction]
    autoExecute: bool
    requireHumanApproval: bool
    notifyChannels: List[Literal["email", "sms", "webhook", "im"]]
    feedbackRequired: bool
    cooldownMinutes: int
    executedCount24h: int
    successRate: float
    reversedCount24h: int
    avgProcessingMs: int
    updatedAt: str


class FeedbackRecord(BaseModel):
    id: str
    orderNo: str
    originalAction: DispositionAction
    aiSuggestion: DispositionAction
    finalAction: DispositionAction
    reviewer: str
    reviewedAt: str
    isCorrect: bool
    feedbackType: Literal["confirm", "override", "partial_correct", "false_positive", "false_negative"]
    comment: str
    fedToRAG: bool
    fedToTraining: bool
    ruleSuggestion: Optional[str] = None
    estimatedSavedLoss: Optional[float] = None
