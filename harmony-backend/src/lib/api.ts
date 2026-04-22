// API abstraction layer — swap with real backend later
// All UI calls go through this so backend can be plugged in without UI changes.
import type { AnomalyOrder, ReconRecord, ChatMessage } from "./types";
import type {
  RiskRule, MLModel, AgentConfig, KnowledgeBase, DispositionPolicy, FeedbackRecord,
} from "./pipeline-types";
import { MOCK_ORDERS, MOCK_RECON } from "./mock-data";
import {
  MOCK_RULES, MOCK_MODELS, MOCK_AGENTS, MOCK_KBS, MOCK_POLICIES, MOCK_FEEDBACK,
} from "./pipeline-mock";

// To switch to the real backend, set VITE_API_BASE_URL.
const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function queryString(params: Record<string, unknown> = {}) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    qs.set(key, String(value));
  });
  const s = qs.toString();
  return s ? `?${s}` : "";
}

async function fetchJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const r = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`${r.status} ${text || r.statusText}`);
  }
  return r.json() as Promise<T>;
}

export interface OrderListParams {
  page?: number;
  pageSize?: number;
  category?: string;
  riskLevel?: string;
  status?: string;
  search?: string;
}

export const api = {
  async listOrders(params: OrderListParams = {}): Promise<{ items: AnomalyOrder[]; total: number }> {
    if (API_BASE) {
      return fetchJson(`/orders${queryString(params)}`);
    }
    await sleep(120);
    let items = MOCK_ORDERS;
    if (params.category && params.category !== "all") items = items.filter((o) => o.primaryCategory === params.category);
    if (params.riskLevel && params.riskLevel !== "all") items = items.filter((o) => o.riskLevel === params.riskLevel);
    if (params.status && params.status !== "all") items = items.filter((o) => o.status === params.status);
    if (params.search) {
      const s = params.search.toLowerCase();
      items = items.filter(
        (o) =>
          o.orderNo.toLowerCase().includes(s) ||
          o.userName.toLowerCase().includes(s) ||
          o.merchantName.toLowerCase().includes(s) ||
          o.userId.toLowerCase().includes(s),
      );
    }
    const total = items.length;
    const page = params.page ?? 1;
    const pageSize = params.pageSize ?? 20;
    return { items: items.slice((page - 1) * pageSize, page * pageSize), total };
  },

  async listAllOrders(params: Omit<OrderListParams, "page" | "pageSize"> = {}): Promise<AnomalyOrder[]> {
    const { items } = await this.listOrders({ ...params, page: 1, pageSize: 5000 });
    return items;
  },

  async getOrder(id: string): Promise<AnomalyOrder | undefined> {
    if (API_BASE) {
      try {
        return await fetchJson(`/orders/${encodeURIComponent(id)}`);
      } catch (e) {
        if (e instanceof Error && e.message.startsWith("404")) return undefined;
        throw e;
      }
    }
    await sleep(80);
    return MOCK_ORDERS.find((o) => o.id === id || o.orderNo === id);
  },

  async executeAction(orderId: string, action: string): Promise<{ ok: true; message: string }> {
    if (API_BASE) {
      return fetchJson(`/orders/${encodeURIComponent(orderId)}/actions`, {
        method: "POST",
        body: JSON.stringify({ action }),
      });
    }
    await sleep(420);
    return { ok: true, message: `已对订单 ${orderId} 执行动作: ${action}` };
  },

  async analyzeOrder(orderId: string): Promise<{ ok: true; trace: unknown }> {
    if (API_BASE) {
      return fetchJson(`/orders/${encodeURIComponent(orderId)}/analyze`, { method: "POST" });
    }
    await sleep(1000);
    return { ok: true, trace: { orderId, mode: "frontend-mock", stages: [] } };
  },

  async listRecon(params: { status?: string; channel?: string; search?: string } = {}): Promise<ReconRecord[]> {
    if (API_BASE) {
      return fetchJson(`/reconciliation${queryString(params)}`);
    }
    await sleep(100);
    let items = MOCK_RECON;
    if (params.status && params.status !== "all") items = items.filter((r) => r.status === params.status);
    if (params.channel && params.channel !== "all") items = items.filter((r) => r.channel === params.channel);
    if (params.search) {
      const s = params.search.toLowerCase();
      items = items.filter((r) => r.internalRef.toLowerCase().includes(s) || r.channelRef.toLowerCase().includes(s));
    }
    return items;
  },

  async runReconMatch(): Promise<{ ok: true; total: number; matched: number; discrepancy: number; message: string }> {
    if (API_BASE) {
      return fetchJson("/reconciliation/match", { method: "POST" });
    }
    await sleep(900);
    const matched = MOCK_RECON.filter((r) => r.status === "matched").length;
    return {
      ok: true,
      total: MOCK_RECON.length,
      matched,
      discrepancy: MOCK_RECON.length - matched,
      message: "前端 mock 对账完成",
    };
  },

  async chatComplete(messages: ChatMessage[]): Promise<string> {
    if (API_BASE) {
      const data = await fetchJson<{ content: string }>("/agent/chat", { method: "POST", body: JSON.stringify({ messages }) });
      return data.content as string;
    }
    // Local mock — a templated response
    await sleep(300);
    const last = messages[messages.length - 1]?.content ?? "";
    return mockAssistantReply(last);
  },

  // ============== 规则引擎 ==============
  async listRules(params: { category?: string; status?: string; search?: string } = {}): Promise<RiskRule[]> {
    if (API_BASE) {
      return fetchJson(`/rules${queryString(params)}`);
    }
    await sleep(80);
    let items = MOCK_RULES;
    if (params.category && params.category !== "all") items = items.filter((r) => r.category === params.category);
    if (params.status && params.status !== "all") items = items.filter((r) => r.status === params.status);
    if (params.search) {
      const s = params.search.toLowerCase();
      items = items.filter((r) => r.name.toLowerCase().includes(s) || r.code.toLowerCase().includes(s));
    }
    return items;
  },
  async upsertRule(rule: Partial<RiskRule>): Promise<{ ok: true; id: string }> {
    if (API_BASE) {
      return fetchJson("/rules", { method: "POST", body: JSON.stringify(rule) });
    }
    await sleep(300);
    return { ok: true, id: rule.id ?? `rule-${Date.now()}` };
  },
  async toggleRule(id: string, enabled: boolean): Promise<{ ok: true }> {
    if (API_BASE) {
      return fetchJson(`/rules/${encodeURIComponent(id)}/toggle`, { method: "POST", body: JSON.stringify({ enabled }) });
    }
    await sleep(180);
    return { ok: true };
  },

  // ============== ML 模型 ==============
  async listModels(): Promise<MLModel[]> {
    if (API_BASE) {
      return fetchJson("/models");
    }
    await sleep(80);
    return MOCK_MODELS;
  },
  async updateModelConfig(id: string, patch: Partial<MLModel>): Promise<{ ok: true }> {
    if (API_BASE) {
      return fetchJson(`/models/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(patch) });
    }
    await sleep(280);
    return { ok: true };
  },
  async retrainModel(id: string): Promise<{ ok: true; jobId: string }> {
    if (API_BASE) {
      return fetchJson(`/models/${encodeURIComponent(id)}/retrain`, { method: "POST" });
    }
    await sleep(400);
    return { ok: true, jobId: `job-${Date.now()}` };
  },

  // ============== AI Agent ==============
  async listAgents(): Promise<AgentConfig[]> {
    if (API_BASE) {
      return fetchJson("/agents");
    }
    await sleep(80);
    return MOCK_AGENTS;
  },
  async listKnowledgeBases(): Promise<KnowledgeBase[]> {
    if (API_BASE) {
      return fetchJson("/agents/kb");
    }
    await sleep(80);
    return MOCK_KBS;
  },
  async updateAgent(id: string, patch: Partial<AgentConfig>): Promise<{ ok: true }> {
    if (API_BASE) {
      return fetchJson(`/agents/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(patch) });
    }
    await sleep(280);
    return { ok: true };
  },
  async testAgent(id: string, input: string): Promise<{ ok: true; output: string; tokens: number; latencyMs: number }> {
    if (API_BASE) {
      return fetchJson(`/agents/${encodeURIComponent(id)}/test`, { method: "POST", body: JSON.stringify({ input }) });
    }
    await sleep(900);
    return {
      ok: true,
      output: `**测试输出**\n\n基于输入「${input.slice(0, 40)}…」,Agent 推理完成。\n\n- 命中知识库片段: 6\n- 调用工具: queryGraph, fetchUserHistory\n- 结论: 高置信度欺诈 (92%)`,
      tokens: Math.floor(900 + Math.random() * 800),
      latencyMs: Math.floor(800 + Math.random() * 600),
    };
  },

  // ============== 自动处置 + 反馈 ==============
  async listPolicies(): Promise<DispositionPolicy[]> {
    if (API_BASE) {
      return fetchJson("/policies");
    }
    await sleep(80);
    return MOCK_POLICIES;
  },
  async upsertPolicy(p: Partial<DispositionPolicy>): Promise<{ ok: true; id: string }> {
    if (API_BASE) {
      return fetchJson("/policies", { method: "POST", body: JSON.stringify(p) });
    }
    await sleep(280);
    return { ok: true, id: p.id ?? `pol-${Date.now()}` };
  },
  async togglePolicy(id: string, enabled: boolean): Promise<{ ok: true }> {
    if (API_BASE) {
      return fetchJson(`/policies/${encodeURIComponent(id)}/toggle`, { method: "POST", body: JSON.stringify({ enabled }) });
    }
    await sleep(180);
    return { ok: true };
  },
  async listFeedback(params: { type?: string; reviewer?: string } = {}): Promise<FeedbackRecord[]> {
    if (API_BASE) {
      return fetchJson(`/feedback${queryString(params)}`);
    }
    await sleep(80);
    let items = MOCK_FEEDBACK;
    if (params.type && params.type !== "all") items = items.filter((f) => f.feedbackType === params.type);
    return items;
  },
  async submitFeedback(fb: Partial<FeedbackRecord>): Promise<{ ok: true; id: string }> {
    if (API_BASE) {
      return fetchJson("/feedback", { method: "POST", body: JSON.stringify(fb) });
    }
    await sleep(280);
    return { ok: true, id: `fb-${Date.now()}` };
  },
};

function mockAssistantReply(input: string): string {
  const txt = input.toLowerCase();
  if (/订单|order|分析/.test(txt)) {
    return [
      "**根因分析报告**",
      "",
      "根据知识库 + 实时特征,我对您查询的订单生成如下结论:",
      "",
      "- **主分类**: 欺诈类 / 账户接管(ATO)",
      "- **风险评分**: 92 / 100  (置信度 96%)",
      "- **核心证据**:",
      "  1. 用户在 11 分钟内跨越 3 个国家登录 (CN→TR→RU)",
      "  2. 设备指纹首次出现且为 Headless Chrome",
      "  3. 命中团伙图谱:与 7 个已标欺诈账户共享 IP /24 段",
      "- **建议动作**: ① 立即拦截 ② 强制二次验证 ③ 加入观察名单 30 天",
      "",
      "_证据链与相似案例已附在右侧详情面板。_",
    ].join("\n");
  }
  if (/对账|recon|差异/.test(txt)) {
    return [
      "**对账差异 Top 5 (近 24h)**",
      "",
      "| 序号 | 渠道 | 类型 | 差异金额 | AI 建议 |",
      "|---|---|---|---|---|",
      "| 1 | Stripe | 手续费未同步 | ¥-1,284.50 | 自动生成手续费分录 |",
      "| 2 | 支付宝 | 时序差异 | — | T+2 自动重对账 |",
      "| 3 | 微信支付 | 重复条目 | ¥+826.00 | 标记重复并冲销 |",
      "| 4 | Visa | 汇率差异 | ¥-42.18 | 计入汇兑损益 |",
      "| 5 | 银联 | 缺失交易 | ¥1,500.00 | 已发起渠道补单 |",
      "",
      "需要我对其中某一条生成自动调整凭证吗?",
    ].join("\n");
  }
  if (/欺诈|fraud|趋势/.test(txt)) {
    return [
      "**欺诈趋势速报 (最近 7 天)**",
      "",
      "- 欺诈类订单同比 +18.4%,主要由 **合成身份** 与 **APP 推送支付欺诈** 驱动",
      "- 高风险地区: 🇷🇺 RU (+34%)、🇳🇬 NG (+22%)",
      "- 命中团伙图谱集群 3 个,涉及 47 个账户、12 台设备",
      "- 模型建议:对 RU/NG + 大额海外渠道组合启用临时强规则",
    ].join("\n");
  }
  return [
    "您好,我是 **支付风控 AI Agent**。我可以帮你:",
    "",
    "- 🔎 分析任意订单的根因 (例: `分析订单 PAY202604000123`)",
    "- 📊 查询对账差异 (例: `昨天对账差异 Top5`)",
    "- 📈 解读欺诈趋势 (例: `近 7 天欺诈趋势`)",
    "- 🛠 生成 chargeback 回复 / 调整凭证 / 风控规则建议",
    "",
    "试试左侧的快捷指令 👉",
  ].join("\n");
}
