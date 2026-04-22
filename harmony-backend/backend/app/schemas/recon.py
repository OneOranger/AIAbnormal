"""对账 schemas — 对应前端 ReconRecord。"""
from typing import Literal, Optional
from pydantic import BaseModel, Field
from .order import PaymentChannel

ReconStatus = Literal["matched", "unmatched", "discrepancy", "duplicate", "missing"]
ReconDiffType = Literal[
    "timing", "amount", "fx", "fee",
    "duplicate", "missing", "partial", "format",
]


class ReconRecord(BaseModel):
    id: str
    date: str
    internalRef: str
    channelRef: str
    internalAmount: float
    channelAmount: float
    diff: float
    channel: PaymentChannel
    status: ReconStatus
    diffType: Optional[ReconDiffType] = None
    rootCause: Optional[str] = None
    aiSuggestion: Optional[str] = None
    matchedConfidence: float = Field(..., ge=0, le=1)
