// AI 推理链路 4 个配置模块的领域模型
// 1) 规则引擎  2) ML 模型  3) AI Agent  4) 自动处置 + 反馈

import type { AnomalyCategory, RiskLevel } from "./types";

// ============== 1. 规则引擎 ==============
export type RuleStatus = "active" | "shadow" | "draft" | "disabled";
export type RuleAction = "intercept" | "review" | "score" | "tag" | "release";
export type RuleScope = "realtime" | "offline" | "both";

export interface RiskRule {
  id: string;
  code: string; // R-FRAUD-001
  name: string;
  category: AnomalyCategory;
  description: string;
  status: RuleStatus;
  scope: RuleScope;
  priority: number; // 1-100
  // DSL 条件 (字符串展示)
  condition: string;
  action: RuleAction;
  scoreDelta: number; // 命中后风险分加成
  hitCount24h: number;
  hitCount7d: number;
  precision: number; // 0-1 精确率
  recall: number; // 0-1 召回率
  falsePositiveRate: number;
  owner: string;
  updatedAt: string;
  createdAt: string;
  version: number;
  tags: string[];
}

// ============== 2. ML 模型 ==============
export type ModelStatus = "online" | "shadow" | "training" | "offline";
export type ModelAlgo = "GBDT" | "IsolationForest" | "XGBoost" | "LightGBM" | "DeepFM" | "GraphSAGE" | "AutoEncoder";

export interface MLFeature {
  name: string;
  importance: number; // 0-1
  type: "numeric" | "categorical" | "embedding" | "graph";
}

export interface MLModel {
  id: string;
  name: string;
  algo: ModelAlgo;
  version: string; // v2.4.1
  status: ModelStatus;
  category: AnomalyCategory | "all";
  description: string;
  // 评分配置
  threshold: number; // 0-100  分数阈值
  weight: number; // 0-1  在融合中的权重
  // 性能指标
  auc: number;
  precision: number;
  recall: number;
  f1: number;
  ks: number; // KS值
  // 在线指标
  qps: number;
  p99Latency: number; // ms
  driftScore: number; // 0-1 PSI
  lastTrainedAt: string;
  nextRetrainAt: string;
  trainSamples: number;
  features: MLFeature[];
  owner: string;
  // A/B 实验
  abTestRatio?: number; // 0-1
}

// ============== 3. AI Agent ==============
export type LLMProvider = "qwen-max" | "deepseek-v3" | "gpt-4o" | "claude-sonnet" | "private-llm";
export type AgentTrigger = "auto" | "manual" | "rule_escalation" | "low_confidence";

export interface AgentTool {
  name: string;
  description: string;
  enabled: boolean;
  callCount24h: number;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  type: "rule_doc" | "case_history" | "regulation" | "merchant_profile" | "fraud_pattern";
  documentCount: number;
  vectorCount: number;
  lastIndexedAt: string;
  embedding: "bge-large-zh" | "text-embedding-3-large" | "m3e-large";
}

export interface AgentConfig {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  // LLM
  provider: LLMProvider;
  model: string;
  temperature: number;
  topP: number;
  maxTokens: number;
  // 触发
  triggers: AgentTrigger[];
  triggerScore: number; // 风险分超过此值触发
  triggerCategories: AnomalyCategory[];
  // 推理配置
  enableMultimodal: boolean;
  enableCausalGraph: boolean;
  enableRAG: boolean;
  ragTopK: number;
  ragKnowledgeBases: string[]; // KB ids
  // 工具
  tools: AgentTool[];
  // Prompt
  systemPrompt: string;
  // 防护
  enableHallucinationCheck: boolean;
  enableFactGrounding: boolean;
  enableSensitiveFilter: boolean;
  // 运行指标
  callCount24h: number;
  avgLatencyMs: number;
  avgTokens: number;
  costUSD24h: number;
  hallucinationRate: number;
}

// ============== 4. 自动处置 + 反馈 ==============
export type DispositionAction =
  | "intercept"
  | "review"
  | "release"
  | "auto_refund"
  | "force_2fa"
  | "freeze_account"
  | "add_blacklist"
  | "watchlist"
  | "notify_user"
  | "escalate";

export interface DispositionPolicy {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  priority: number;
  // 触发条件
  category: AnomalyCategory | "all";
  riskLevel: RiskLevel | "all";
  minScore: number;
  minConfidence: number; // AI 置信度阈值
  // 动作
  primaryAction: DispositionAction;
  secondaryActions: DispositionAction[];
  // 执行模式
  autoExecute: boolean; // 是否自动执行(否则只建议)
  requireHumanApproval: boolean;
  notifyChannels: ("email" | "sms" | "webhook" | "im")[];
  // 反馈回流
  feedbackRequired: boolean;
  cooldownMinutes: number; // 同用户冷却
  // 指标
  executedCount24h: number;
  successRate: number;
  reversedCount24h: number; // 被人工撤回数
  avgProcessingMs: number;
  updatedAt: string;
}

export interface FeedbackRecord {
  id: string;
  orderNo: string;
  originalAction: DispositionAction;
  aiSuggestion: DispositionAction;
  finalAction: DispositionAction;
  reviewer: string;
  reviewedAt: string;
  // 反馈
  isCorrect: boolean; // AI 判断是否正确
  feedbackType: "confirm" | "override" | "partial_correct" | "false_positive" | "false_negative";
  comment: string;
  // 影响
  fedToRAG: boolean;
  fedToTraining: boolean;
  ruleSuggestion?: string; // AI 基于反馈生成的规则建议
  estimatedSavedLoss?: number;
}
