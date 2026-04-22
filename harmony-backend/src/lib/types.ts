// Core domain types for the AI payment anomaly system

export type AnomalyCategory =
  | "fraud"
  | "behavioral"
  | "system"
  | "reconciliation"
  | "chargeback"
  | "merchant"
  | "user"
  | "compliance";

export type RiskLevel = "critical" | "high" | "medium" | "low";

export type OrderStatus =
  | "pending_review"
  | "intercepted"
  | "released"
  | "refunded"
  | "observing"
  | "resolved"
  | "escalated";

export type PaymentChannel =
  | "alipay"
  | "wechat"
  | "unionpay"
  | "visa"
  | "mastercard"
  | "stripe"
  | "paypal"
  | "applepay"
  | "bank_transfer";

export interface Evidence {
  id: string;
  type: "device" | "ip" | "behavior" | "pattern" | "rule" | "graph" | "ml";
  label: string;
  detail: string;
  weight: number; // 0-1
}

export interface AISuggestion {
  action: "intercept" | "review" | "release" | "auto_refund" | "observe" | "dispute_reply";
  label: string;
  confidence: number; // 0-100
  rationale: string;
  estimatedLoss?: number;
}

export interface AnomalyOrder {
  id: string;
  orderNo: string;
  createdAt: string; // ISO
  amount: number;
  currency: "CNY" | "USD" | "EUR";
  channel: PaymentChannel;
  merchantName: string;
  merchantId: string;
  userId: string;
  userName: string;
  userIp: string;
  ipCountry: string;
  device: string;
  deviceFingerprint: string;
  status: OrderStatus;
  // AI labels
  primaryCategory: AnomalyCategory;
  subTypes: string[]; // e.g. ["合成身份", "IP跳变"]
  riskScore: number; // 0-100
  riskLevel: RiskLevel;
  confidence: number; // 0-100
  tags: string[];
  evidence: Evidence[];
  suggestions: AISuggestion[];
  rootCause: string;
  rcaSummary: string;
  similarCases: number;
}

// Reconciliation
export type ReconStatus = "matched" | "unmatched" | "discrepancy" | "duplicate" | "missing";
export type ReconDiffType =
  | "timing"
  | "amount"
  | "fx"
  | "fee"
  | "duplicate"
  | "missing"
  | "partial"
  | "format";

export interface ReconRecord {
  id: string;
  date: string;
  internalRef: string;
  channelRef: string;
  internalAmount: number;
  channelAmount: number;
  diff: number;
  channel: PaymentChannel;
  status: ReconStatus;
  diffType?: ReconDiffType;
  rootCause?: string;
  aiSuggestion?: string;
  matchedConfidence: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  attachments?: { type: "table" | "chart" | "order"; data: unknown }[];
}
