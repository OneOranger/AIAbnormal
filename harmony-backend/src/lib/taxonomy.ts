import type { AnomalyCategory } from "./types";

export const CATEGORY_META: Record<
  AnomalyCategory,
  { label: string; color: string; description: string; subTypes: string[] }
> = {
  fraud: {
    label: "欺诈类",
    color: "var(--risk-critical)",
    description: "占比最高的异常,涵盖盗刷、合成身份、ATO、深度伪造等",
    subTypes: [
      "合成身份欺诈",
      "账户接管(ATO)",
      "新账户欺诈(NAF)",
      "首方欺诈/APP诈骗",
      "钱骡欺诈",
      "深度伪造社工",
      "支付页面劫持",
      "信用卡盗刷",
      "商业邮件入侵(BEC)",
    ],
  },
  behavioral: {
    label: "行为异常",
    color: "var(--risk-high)",
    description: "金额/频率/时间/设备等行为模式异常",
    subTypes: [
      "突发大额",
      "高频小额刷单",
      "夜间大额",
      "IP/设备跳变",
      "高风险地区",
      "支付方式突变",
      "重复批量下单",
      "设备指纹异常",
      "关联关系异常",
    ],
  },
  system: {
    label: "系统/配置",
    color: "var(--info)",
    description: "后台配置、回调延迟、重复入账等系统级异常",
    subTypes: ["配置错误", "重复支付", "回调延迟丢失", "API集成故障", "状态同步失败"],
  },
  reconciliation: {
    label: "对账不一致",
    color: "var(--chart-2)",
    description: "时序/金额/汇率/手续费等对账差异(融入AI对账模块)",
    subTypes: [
      "时序差异",
      "数据录入错误",
      "缺失交易",
      "重复条目",
      "部分支付/拆分",
      "币种汇率差",
      "手续费未同步",
      "结算延迟",
      "退款未对齐",
    ],
  },
  chargeback: {
    label: "拒付争议",
    color: "var(--risk-high)",
    description: "Chargeback、友好欺诈、商品不符等争议",
    subTypes: ["欺诈拒付", "商户错误拒付", "友好欺诈", "商品服务不符", "未收到货"],
  },
  merchant: {
    label: "商户侧",
    color: "var(--warning)",
    description: "商户欺诈、高退款率、高风险业务",
    subTypes: ["商户欺诈", "高退款率", "高争议率", "高风险行业", "纠纷未处理"],
  },
  user: {
    label: "用户非欺诈",
    color: "var(--chart-3)",
    description: "用户误操作、季节性波动等非欺诈异常",
    subTypes: ["误操作重复下单", "财务困难拒付", "季节性波动"],
  },
  compliance: {
    label: "合规/规则",
    color: "var(--chart-4)",
    description: "黑名单、AML、高风险行业等合规命中",
    subTypes: ["黑名单命中", "反洗钱触发", "高风险行业", "实时风控触发", "刷单/退款异常"],
  },
};

export const CATEGORIES = Object.keys(CATEGORY_META) as AnomalyCategory[];

export const RISK_LEVEL_META = {
  critical: { label: "致命", color: "var(--risk-critical)", min: 85 },
  high: { label: "高", color: "var(--risk-high)", min: 65 },
  medium: { label: "中", color: "var(--risk-medium)", min: 40 },
  low: { label: "低", color: "var(--risk-low)", min: 0 },
} as const;

export const STATUS_META = {
  pending_review: { label: "待复核", color: "var(--warning)" },
  intercepted: { label: "已拦截", color: "var(--risk-critical)" },
  released: { label: "已放行", color: "var(--success)" },
  refunded: { label: "已退款", color: "var(--info)" },
  observing: { label: "观察中", color: "var(--chart-2)" },
  resolved: { label: "已闭环", color: "var(--success)" },
  escalated: { label: "已升级", color: "var(--risk-high)" },
} as const;

export const CHANNEL_META = {
  alipay: { label: "支付宝", color: "#1677FF" },
  wechat: { label: "微信支付", color: "#07C160" },
  unionpay: { label: "银联", color: "#E60012" },
  visa: { label: "Visa", color: "#1A1F71" },
  mastercard: { label: "Mastercard", color: "#EB001B" },
  stripe: { label: "Stripe", color: "#635BFF" },
  paypal: { label: "PayPal", color: "#003087" },
  applepay: { label: "Apple Pay", color: "#000000" },
  bank_transfer: { label: "银行转账", color: "#64748b" },
} as const;
