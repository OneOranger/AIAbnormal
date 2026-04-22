"""异常订单 schemas — 严格对应前端 src/lib/types.ts 的 AnomalyOrder。"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

AnomalyCategory = Literal[
    "fraud", "behavioral", "system", "reconciliation",
    "chargeback", "merchant", "user", "compliance",
]
RiskLevel = Literal["critical", "high", "medium", "low"]
OrderStatus = Literal[
    "pending_review", "intercepted", "released",
    "refunded", "observing", "resolved", "escalated",
]
PaymentChannel = Literal[
    "alipay", "wechat", "unionpay", "visa", "mastercard",
    "stripe", "paypal", "applepay", "bank_transfer",
]
EvidenceType = Literal["device", "ip", "behavior", "pattern", "rule", "graph", "ml"]
SuggestionAction = Literal[
    "intercept", "review", "release", "auto_refund", "observe", "dispute_reply",
]
Currency = Literal["CNY", "USD", "EUR"]


class Evidence(BaseModel):
    id: str
    type: EvidenceType
    label: str
    detail: str
    weight: float = Field(..., ge=0, le=1)


class AISuggestion(BaseModel):
    action: SuggestionAction
    label: str
    confidence: int = Field(..., ge=0, le=100)
    rationale: str
    estimatedLoss: Optional[float] = None


class AnomalyOrder(BaseModel):
    id: str
    orderNo: str
    createdAt: str  # ISO
    amount: float
    currency: Currency
    channel: PaymentChannel
    merchantName: str
    merchantId: str
    userId: str
    userName: str
    userIp: str
    ipCountry: str
    device: str
    deviceFingerprint: str
    status: OrderStatus
    primaryCategory: AnomalyCategory
    subTypes: List[str]
    riskScore: int = Field(..., ge=0, le=100)
    riskLevel: RiskLevel
    confidence: int = Field(..., ge=0, le=100)
    tags: List[str]
    evidence: List[Evidence]
    suggestions: List[AISuggestion]
    rootCause: str
    rcaSummary: str
    similarCases: int


class OrderListResponse(BaseModel):
    items: List[AnomalyOrder]
    total: int


class ActionRequest(BaseModel):
    action: str


class ActionResponse(BaseModel):
    ok: bool = True
    message: str
