// Deterministic mock data generator for anomaly orders + reconciliation
import type {
  AnomalyOrder,
  AnomalyCategory,
  PaymentChannel,
  Evidence,
  AISuggestion,
  RiskLevel,
  OrderStatus,
  ReconRecord,
  ReconStatus,
  ReconDiffType,
} from "./types";
import { CATEGORY_META, CATEGORIES } from "./taxonomy";

// --- seeded RNG so data is stable across reloads ---
function mulberry32(seed: number) {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(20260421);

function pick<T>(arr: readonly T[]): T {
  return arr[Math.floor(rand() * arr.length)]!;
}
function pickN<T>(arr: readonly T[], n: number): T[] {
  const copy = [...arr];
  const out: T[] = [];
  for (let i = 0; i < n && copy.length; i++) {
    out.push(copy.splice(Math.floor(rand() * copy.length), 1)[0]!);
  }
  return out;
}
function range(min: number, max: number): number {
  return min + rand() * (max - min);
}
function intRange(min: number, max: number): number {
  return Math.floor(range(min, max + 1));
}

const FIRST_NAMES = ["李", "王", "张", "刘", "陈", "杨", "黄", "赵", "周", "吴", "Wang", "Smith", "Garcia", "Müller"];
const LAST_NAMES = ["明", "伟", "芳", "娜", "强", "磊", "敏", "静", "涛", "霞", "Lee", "Chen", "Patel"];
const MERCHANTS = [
  "云耀数码旗舰店",
  "悦购国际",
  "极速优选",
  "ShopSmart Inc",
  "GameTopUp Pro",
  "云端会员订阅",
  "海外购精选",
  "Quick Recharge",
  "LuxLife Boutique",
  "盛世彩金平台",
  "CryptoFastPay",
  "EduOnline 课程",
];
const COUNTRIES = ["CN", "US", "RU", "NG", "BR", "VN", "PH", "TR", "ID", "MY"];
const HIGH_RISK = ["RU", "NG", "PH", "TR"];
const DEVICES = ["iPhone 15 Pro", "Pixel 8", "Xiaomi 14", "Samsung S24", "Huawei Mate60", "Emulator-X86", "Headless Chrome"];
const CHANNELS: PaymentChannel[] = [
  "alipay",
  "wechat",
  "unionpay",
  "visa",
  "mastercard",
  "stripe",
  "paypal",
  "applepay",
  "bank_transfer",
];

const SUB_TAGS_FOR_EVIDENCE: Record<string, Evidence["type"]> = {
  设备: "device",
  IP: "ip",
  行为: "behavior",
  规则: "rule",
  图谱: "graph",
  模型: "ml",
};

function makeIp(country: string): string {
  if (country === "CN") return `${intRange(110, 220)}.${intRange(0, 255)}.${intRange(0, 255)}.${intRange(0, 255)}`;
  return `${intRange(1, 254)}.${intRange(0, 255)}.${intRange(0, 255)}.${intRange(0, 255)}`;
}

function makeName(): string {
  const f = pick(FIRST_NAMES);
  const l = pick(LAST_NAMES);
  return f + l;
}

function makeOrderNo(i: number): string {
  return `PAY${(202604000000 + i).toString()}`;
}

function makeUserId(i: number): string {
  return `U${100000 + i}`;
}

function makeMerchantId(name: string): string {
  return "M" + Math.abs(name.split("").reduce((a, c) => a + c.charCodeAt(0), 0)).toString().padStart(6, "0");
}

const RCA_TEMPLATES: Record<AnomalyCategory, string[]> = {
  fraud: [
    "用户身份证件与历史画像匹配度仅 18%,设备指纹首次出现且 IP 来自高风险地区,综合判定为合成身份欺诈尝试。",
    "登录行为在 15 分钟内跨越 3 个国家,密码重置后立即发起大额支付,符合典型账户接管(ATO)特征。",
    "支付页面 JS 文件 hash 与官方版本不一致,检测到 Magecart 类卡号嗅探脚本注入。",
  ],
  behavioral: [
    "近 1 小时同一设备发起 23 笔小额订单,金额方差极小,存在刷单/套现风险。",
    "用户首次切换至高风险海外渠道,且金额超过历史 P99 的 6 倍,行为偏离严重。",
    "夜间 02:14 突发大额订单,与用户历史 7 天作息曲线显著背离。",
  ],
  system: [
    "支付回调 webhook 在 12 分钟内重试 5 次仍未收到 ACK,导致订单状态在订单中心未更新。",
    "营销系统配置的优惠模板存在变量缺失,触发 0.8 折扣异常计算,影响 1,247 笔订单。",
    "渠道侧 SDK 版本与服务端 API 协议不一致,部分订单 amount 字段精度丢失。",
  ],
  reconciliation: [
    "渠道入账时间晚于内部记账 36 小时,属于跨日时序差异,非真实差异。",
    "渠道实际入账金额扣除了 0.6% 手续费,内部账面未同步,差额 ¥18.42。",
    "同一笔交易在渠道对账文件中出现 2 次,疑似渠道重复推送。",
  ],
  chargeback: [
    "持卡人发起拒付,理由为 'item not received',但物流签收记录显示已签收。判定为友好欺诈。",
    "客户投诉商品与描述不符,商户未在 7 天内响应,争议升级为拒付。",
  ],
  merchant: [
    "该商户近 30 天退款率 28%,远高于行业均值 3%,触发高退款率风控规则。",
    "商户经营范围与申报类目不符,实际销售品类涉及高风险目录。",
  ],
  user: ["用户在 2 分钟内提交 3 笔相同订单,误操作可能性高,系统建议合并处理。", "退款理由为'冲动消费',无欺诈特征,可正常受理。"],
  compliance: ["收款方命中 AML 黑名单(命中规则: SDN-2024-0451),已自动拦截并上报。", "交易金额触发 CNY 50,000 大额申报阈值,需补充资料。"],
};

function makeEvidenceFor(cat: AnomalyCategory, country: string, device: string): Evidence[] {
  const all: Evidence[] = [
    { id: "", type: "device", label: "设备指纹首次出现", detail: `Fingerprint 与历史 0 次匹配 · ${device}`, weight: 0.85 },
    { id: "", type: "ip", label: "IP 跳变", detail: `1 小时内跨越 ${intRange(2, 4)} 个国家`, weight: 0.78 },
    { id: "", type: "behavior", label: "夜间大额", detail: "02:00-05:00 时间段且金额 > P99", weight: 0.7 },
    { id: "", type: "rule", label: "命中规则 R-${id}", detail: "高风险地区 + 高频小额", weight: 0.9 },
    { id: "", type: "graph", label: "团伙关联图谱", detail: `与 ${intRange(3, 18)} 个已标欺诈账户共享设备/IP`, weight: 0.92 },
    { id: "", type: "ml", label: "GBDT 风险评分", detail: `score=${range(0.7, 0.99).toFixed(3)}`, weight: 0.75 },
    { id: "", type: "behavior", label: "支付方式突变", detail: "首次使用海外信用卡", weight: 0.6 },
  ];
  const k = cat === "fraud" ? intRange(4, 6) : intRange(2, 4);
  const items = pickN(all, k).map((e, i) => ({ ...e, id: `EV-${i + 1}` }));
  if (HIGH_RISK.includes(country)) items[0]!.weight = Math.min(1, items[0]!.weight + 0.05);
  return items;
}

function makeSuggestionsFor(cat: AnomalyCategory, score: number, amount: number): AISuggestion[] {
  const out: AISuggestion[] = [];
  if (score >= 85) {
    out.push({
      action: "intercept",
      label: "立即拦截订单",
      confidence: Math.min(99, Math.round(score + range(2, 8))),
      rationale: "风险分超过拦截阈值且证据链充分,建议直接拦截避免资损。",
      estimatedLoss: Math.round(amount),
    });
    out.push({
      action: "review",
      label: "转人工高级复核",
      confidence: Math.round(score - 8),
      rationale: "如需保留转化,可移交一线复核同事二次审核。",
    });
    out.push({
      action: "auto_refund",
      label: "已扣款则自动退款",
      confidence: Math.round(score - 12),
      rationale: "若已完成扣款,建议自动发起原路退款并标记观察。",
    });
  } else if (score >= 60) {
    out.push({ action: "review", label: "转人工复核", confidence: Math.round(score + 5), rationale: "风险中等,建议人工二次研判后放行。" });
    out.push({
      action: "observe",
      label: "标记观察 30 天",
      confidence: Math.round(score - 5),
      rationale: "加入观察名单,持续监控后续订单。",
    });
    out.push({ action: "release", label: "条件放行", confidence: Math.round(score - 15), rationale: "可在收集补充资料后放行。" });
  } else {
    out.push({ action: "release", label: "正常放行", confidence: Math.round(95 - score), rationale: "风险较低,无明显欺诈特征。" });
    out.push({ action: "observe", label: "标记观察", confidence: 60, rationale: "保留风控记录用于模型迭代。" });
  }
  if (cat === "chargeback") {
    out.push({
      action: "dispute_reply",
      label: "AI 生成争议回复",
      confidence: 88,
      rationale: "已聚合物流签收 + 服务记录,可一键生成 chargeback 回复模板。",
    });
  }
  return out;
}

function riskLevelOf(score: number): RiskLevel {
  if (score >= 85) return "critical";
  if (score >= 65) return "high";
  if (score >= 40) return "medium";
  return "low";
}

function makeOrder(i: number): AnomalyOrder {
  // Weighted category distribution (matches industry data)
  const r = rand();
  let cat: AnomalyCategory;
  if (r < 0.42) cat = "fraud";
  else if (r < 0.6) cat = "behavioral";
  else if (r < 0.72) cat = "reconciliation";
  else if (r < 0.8) cat = "chargeback";
  else if (r < 0.86) cat = "system";
  else if (r < 0.91) cat = "merchant";
  else if (r < 0.96) cat = "compliance";
  else cat = "user";

  const meta = CATEGORY_META[cat];
  const subTypes = pickN(meta.subTypes, intRange(1, 3));
  const country = cat === "fraud" || cat === "compliance" ? pick(HIGH_RISK) : pick(COUNTRIES);
  const device = pick(DEVICES);
  const channel = pick(CHANNELS);
  const merchant = pick(MERCHANTS);
  const userName = makeName();

  // Risk score per category
  let baseScore: number;
  if (cat === "fraud") baseScore = range(70, 99);
  else if (cat === "compliance") baseScore = range(75, 98);
  else if (cat === "chargeback") baseScore = range(55, 92);
  else if (cat === "behavioral") baseScore = range(45, 90);
  else if (cat === "merchant") baseScore = range(50, 88);
  else if (cat === "system") baseScore = range(30, 75);
  else if (cat === "reconciliation") baseScore = range(20, 60);
  else baseScore = range(10, 50);
  const riskScore = Math.round(baseScore);
  const confidence = Math.round(range(72, 99));

  const amount = Math.round(
    cat === "fraud" || cat === "chargeback" ? range(500, 99000) : cat === "behavioral" ? range(50, 8000) : range(20, 12000),
  );

  // Status correlated to risk
  let status: OrderStatus;
  if (riskScore >= 85) status = pick(["intercepted", "pending_review", "escalated"] as const);
  else if (riskScore >= 60) status = pick(["pending_review", "observing", "intercepted"] as const);
  else status = pick(["released", "resolved", "observing"] as const);

  // Created within the last 14 days
  const createdAt = new Date(Date.now() - rand() * 14 * 86400_000).toISOString();

  const evidence = makeEvidenceFor(cat, country, device);
  const suggestions = makeSuggestionsFor(cat, riskScore, amount);
  const rcaSummary = pick(RCA_TEMPLATES[cat]);

  const tags = [
    `#${meta.label}`,
    ...subTypes.map((s) => `#${s}`),
    HIGH_RISK.includes(country) ? "#高风险地区" : "",
    riskScore >= 85 ? "#致命风险" : riskScore >= 65 ? "#高风险" : "",
    device.includes("Emulator") || device.includes("Headless") ? "#可疑设备" : "",
  ].filter(Boolean);

  return {
    id: `O${(1000000 + i).toString()}`,
    orderNo: makeOrderNo(i),
    createdAt,
    amount,
    currency: channel === "alipay" || channel === "wechat" || channel === "unionpay" ? "CNY" : pick(["USD", "EUR", "CNY"] as const),
    channel,
    merchantName: merchant,
    merchantId: makeMerchantId(merchant),
    userId: makeUserId(i),
    userName,
    userIp: makeIp(country),
    ipCountry: country,
    device,
    deviceFingerprint: `FP-${(rand() * 1e10).toString(36).slice(0, 12).toUpperCase()}`,
    status,
    primaryCategory: cat,
    subTypes,
    riskScore,
    riskLevel: riskLevelOf(riskScore),
    confidence,
    tags,
    evidence,
    suggestions,
    rootCause: subTypes.join(" + "),
    rcaSummary,
    similarCases: intRange(3, 240),
  };
}

export const MOCK_ORDERS: AnomalyOrder[] = Array.from({ length: 1240 }, (_, i) => makeOrder(i)).sort(
  (a, b) => +new Date(b.createdAt) - +new Date(a.createdAt),
);

// --- Reconciliation mock ---
function makeReconRecord(i: number): ReconRecord {
  const channel = pick(CHANNELS);
  const internalAmount = Math.round(range(20, 50000) * 100) / 100;
  let channelAmount = internalAmount;
  let status: ReconStatus = "matched";
  let diffType: ReconDiffType | undefined;
  let rootCause: string | undefined;
  let aiSuggestion: string | undefined;
  let matchedConfidence = 99;

  const r = rand();
  if (r < 0.62) {
    // matched
  } else if (r < 0.78) {
    // fee diff
    const fee = Math.round(internalAmount * 0.006 * 100) / 100;
    channelAmount = Math.round((internalAmount - fee) * 100) / 100;
    status = "discrepancy";
    diffType = "fee";
    rootCause = `渠道扣除 0.6% 手续费 ¥${fee.toFixed(2)},内部账面未同步`;
    aiSuggestion = "自动生成手续费分录,借: 财务费用-渠道手续费 / 贷: 银行存款";
    matchedConfidence = 96;
  } else if (r < 0.86) {
    status = "discrepancy";
    diffType = "timing";
    rootCause = `渠道入账时间晚于内部 ${intRange(12, 72)} 小时,跨日时序差异`;
    aiSuggestion = "无需调整,T+2 自动重对账";
    matchedConfidence = 92;
  } else if (r < 0.92) {
    status = "missing";
    diffType = "missing";
    channelAmount = 0;
    rootCause = "渠道对账文件中缺失该笔交易";
    aiSuggestion = "已发起渠道补单查询工单 #RC-{id}";
    matchedConfidence = 0;
  } else if (r < 0.96) {
    status = "duplicate";
    diffType = "duplicate";
    channelAmount = internalAmount * 2;
    rootCause = "渠道对账文件中存在重复条目";
    aiSuggestion = "标记其中一条为重复并冲销";
    matchedConfidence = 88;
  } else {
    status = "discrepancy";
    diffType = "fx";
    channelAmount = Math.round(internalAmount * range(0.96, 1.04) * 100) / 100;
    rootCause = "跨币种汇率差异 (实时汇率 vs 记账汇率)";
    aiSuggestion = "计入汇兑损益科目";
    matchedConfidence = 90;
  }

  return {
    id: `RC${(500000 + i).toString()}`,
    date: new Date(Date.now() - rand() * 7 * 86400_000).toISOString(),
    internalRef: `INT-${(800000 + i).toString()}`,
    channelRef: status === "missing" ? "—" : `CH-${(700000 + i).toString()}`,
    internalAmount,
    channelAmount,
    diff: Math.round((channelAmount - internalAmount) * 100) / 100,
    channel,
    status,
    diffType,
    rootCause,
    aiSuggestion,
    matchedConfidence,
  };
}

export const MOCK_RECON: ReconRecord[] = Array.from({ length: 480 }, (_, i) => makeReconRecord(i));

// --- helpers used by UI ---
export function ordersByCategory() {
  const map = new Map<AnomalyCategory, number>();
  CATEGORIES.forEach((c) => map.set(c, 0));
  MOCK_ORDERS.forEach((o) => map.set(o.primaryCategory, (map.get(o.primaryCategory) ?? 0) + 1));
  return Array.from(map.entries()).map(([k, v]) => ({ category: k, count: v }));
}

export function ordersTimeline(days = 14) {
  const buckets: Record<string, { date: string; total: number; critical: number; high: number }> = {};
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(Date.now() - i * 86400_000);
    const key = d.toISOString().slice(5, 10);
    buckets[key] = { date: key, total: 0, critical: 0, high: 0 };
  }
  MOCK_ORDERS.forEach((o) => {
    const key = o.createdAt.slice(5, 10);
    if (buckets[key]) {
      buckets[key].total += 1;
      if (o.riskLevel === "critical") buckets[key].critical += 1;
      if (o.riskLevel === "high") buckets[key].high += 1;
    }
  });
  return Object.values(buckets);
}
