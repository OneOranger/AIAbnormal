import { createFileRoute, Link, useRouter, notFound } from "@tanstack/react-router";
import { useState } from "react";
import {
  ArrowLeft,
  Sparkles,
  ShieldCheck,
  ShieldX,
  Eye,
  Receipt,
  MessageSquare,
  Network,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Copy,
  Globe,
  Smartphone,
  Fingerprint,
  Clock,
  Brain,
} from "lucide-react";
import { CATEGORY_META, CHANNEL_META } from "@/lib/taxonomy";
import { CategoryChip, StatusChip, Tag } from "@/components/chips";
import { RiskBadge } from "@/components/risk-badge";
import { formatMoney, formatDateTime } from "@/lib/format";
import { api } from "@/lib/api";

export const Route = createFileRoute("/orders/$orderId")({
  loader: async ({ params }) => {
    const order = await api.getOrder(params.orderId);
    if (!order) throw notFound();
    return { order };
  },
  component: OrderDetail,
  notFoundComponent: () => (
    <div className="p-12 text-center">
      <div className="text-sm text-muted-foreground">该订单不存在</div>
      <Link to="/orders" className="text-primary text-sm hover:underline mt-2 inline-block">
        返回订单列表
      </Link>
    </div>
  ),
  head: ({ loaderData }) => ({
    meta: [{ title: `${(loaderData as { order: { orderNo: string } } | undefined)?.order.orderNo ?? "订单"} · AI 根因报告` }],
  }),
});

const ACTION_ICONS = {
  intercept: ShieldX,
  review: Eye,
  release: ShieldCheck,
  auto_refund: Receipt,
  observe: Clock,
  dispute_reply: MessageSquare,
} as const;

function OrderDetail() {
  const { order } = Route.useLoaderData() as { order: import("@/lib/types").AnomalyOrder };
  const router = useRouter();
  const [executing, setExecuting] = useState<string | null>(null);
  const [executed, setExecuted] = useState<string | null>(null);

  async function handleExecute(action: string) {
    setExecuting(action);
    await api.executeAction(order.id, action);
    setExecuting(null);
    setExecuted(action);
    setTimeout(() => router.invalidate(), 600);
  }

  const channelMeta = CHANNEL_META[order.channel];

  return (
    <div className="p-6 lg:p-8 max-w-[1500px] mx-auto space-y-5">
      <Link to="/orders" className="text-xs text-muted-foreground hover:text-foreground inline-flex items-center gap-1">
        <ArrowLeft className="h-3 w-3" /> 返回订单列表
      </Link>

      {/* Header */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-semibold num">{order.orderNo}</h1>
              <CategoryChip category={order.primaryCategory} />
              <StatusChip status={order.status} />
              <RiskBadge level={order.riskLevel} score={order.riskScore} />
            </div>
            <div className="text-sm text-muted-foreground mt-2 flex flex-wrap gap-x-4 gap-y-1">
              <span>{formatDateTime(order.createdAt)}</span>
              <span className="inline-flex items-center gap-1">
                <span className="h-2 w-2 rounded-full" style={{ background: channelMeta.color }} /> {channelMeta.label}
              </span>
              <span>商户: {order.merchantName}</span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-semibold num">{formatMoney(order.amount, order.currency)}</div>
            <div className="text-xs text-muted-foreground mt-1">置信度 {order.confidence}% · 相似案例 {order.similarCases}</div>
          </div>
        </div>

        {/* Tags row */}
        <div className="mt-4 flex flex-wrap gap-1.5">
          {order.tags.map((t) => (
            <Tag key={t}>{t}</Tag>
          ))}
        </div>
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left: facts */}
        <div className="space-y-5">
          <Card title="交易主体">
            <KV icon={Globe} label="用户 IP" value={`${order.userIp} · ${order.ipCountry}`} />
            <KV icon={Smartphone} label="设备" value={order.device} />
            <KV icon={Fingerprint} label="设备指纹" value={order.deviceFingerprint} mono />
            <KV label="用户" value={`${order.userName} (${order.userId})`} />
            <KV label="商户" value={`${order.merchantName} (${order.merchantId})`} />
            <KV label="支付渠道" value={channelMeta.label} />
          </Card>

          <Card title="AI 命中标签">
            <div className="flex flex-wrap gap-1.5">
              {order.subTypes.map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium ring-1 ring-inset"
                  style={{
                    background: `color-mix(in oklab, ${CATEGORY_META[order.primaryCategory].color} 8%, transparent)`,
                    color: CATEGORY_META[order.primaryCategory].color,
                    borderColor: CATEGORY_META[order.primaryCategory].color,
                  }}
                >
                  {t}
                </span>
              ))}
            </div>
          </Card>
        </div>

        {/* Center: AI rationale */}
        <div className="lg:col-span-2 space-y-5">
          {/* RCA report */}
          <div className="rounded-xl border border-primary/20 bg-gradient-to-br from-primary/[0.04] to-card p-5">
            <div className="flex items-center gap-2 mb-3">
              <div className="h-7 w-7 rounded-md bg-primary/10 flex items-center justify-center">
                <Brain className="h-4 w-4 text-primary" />
              </div>
              <div>
                <div className="text-sm font-semibold">AI 根因分析报告</div>
                <div className="text-[11px] text-muted-foreground">
                  Lovable AI · 因果图谱 + RAG · 推理耗时 1.42s
                </div>
              </div>
              <button className="ml-auto p-1.5 rounded-md hover:bg-accent">
                <Copy className="h-3.5 w-3.5 text-muted-foreground" />
              </button>
            </div>
            <p className="text-sm leading-relaxed text-foreground/90">{order.rcaSummary}</p>

            <div className="mt-4 grid grid-cols-3 gap-3">
              <Stat label="风险评分" value={order.riskScore.toString()} suffix="/ 100" tone="critical" />
              <Stat label="模型置信度" value={`${order.confidence}%`} tone="primary" />
              <Stat label="相似历史案例" value={order.similarCases.toString()} tone="info" />
            </div>
          </div>

          {/* Evidence chain */}
          <Card title="证据链" icon={Network}>
            <div className="space-y-2.5">
              {order.evidence.map((e, i) => (
                <div key={e.id} className="flex items-start gap-3 p-3 rounded-lg bg-muted/40 hover:bg-muted/60 transition-colors">
                  <div className="h-6 w-6 rounded-md bg-primary/10 text-primary text-[11px] font-semibold flex items-center justify-center shrink-0">
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium">{e.label}</span>
                      <Tag>{e.type}</Tag>
                    </div>
                    <div className="text-xs text-muted-foreground mt-0.5">{e.detail}</div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-[11px] text-muted-foreground">权重</div>
                    <div className="num text-sm font-semibold">{(e.weight * 100).toFixed(0)}</div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* AI Suggestions */}
          <Card title="AI 处理建议" icon={Sparkles}>
            <div className="space-y-2.5">
              {order.suggestions.map((s, i) => {
                const Icon = ACTION_ICONS[s.action];
                const isExecuting = executing === s.action;
                const isExecuted = executed === s.action;
                const isPrimary = i === 0;
                return (
                  <div
                    key={s.action}
                    className={`flex items-center gap-3 p-3 rounded-lg border transition-colors ${
                      isPrimary ? "border-primary/30 bg-primary/[0.03]" : "border-border bg-card"
                    }`}
                  >
                    <div
                      className={`h-9 w-9 rounded-md flex items-center justify-center shrink-0 ${
                        isPrimary ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-medium">{s.label}</span>
                        <span className="text-[11px] num text-muted-foreground">置信度 {s.confidence}%</span>
                        {isPrimary && (
                          <span className="inline-flex items-center gap-1 text-[10px] text-primary font-semibold">
                            <Sparkles className="h-2.5 w-2.5" /> AI 推荐
                          </span>
                        )}
                      </div>
                      <div className="text-[11.5px] text-muted-foreground mt-0.5 leading-relaxed">{s.rationale}</div>
                    </div>
                    <button
                      onClick={() => handleExecute(s.action)}
                      disabled={!!executing || !!executed}
                      className={`shrink-0 inline-flex items-center gap-1 px-3 h-8 rounded-md text-xs font-medium transition-all ${
                        isExecuted
                          ? "bg-success text-success-foreground"
                          : isPrimary
                          ? "bg-primary text-primary-foreground hover:bg-primary/90"
                          : "border border-border bg-card hover:bg-accent"
                      } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                      {isExecuting ? (
                        <>
                          <Loader2 className="h-3 w-3 animate-spin" /> 执行中
                        </>
                      ) : isExecuted ? (
                        <>
                          <CheckCircle2 className="h-3 w-3" /> 已执行
                        </>
                      ) : (
                        "执行"
                      )}
                    </button>
                  </div>
                );
              })}
            </div>

            {executed && (
              <div className="mt-3 flex items-start gap-2 p-3 rounded-md bg-success/10 text-success text-xs">
                <CheckCircle2 className="h-3.5 w-3.5 mt-0.5" />
                <div>
                  动作已通过支付网关 API 提交,已记录到审计日志,反馈数据将自动回流模型训练池。
                </div>
              </div>
            )}
          </Card>

          {/* Risk graph placeholder */}
          <Card title="团伙关联图谱" icon={Network}>
            <div className="relative h-48 rounded-lg bg-gradient-to-br from-muted/40 to-muted/10 overflow-hidden">
              <FraudGraph riskLevel={order.riskLevel} />
            </div>
            <div className="mt-3 text-xs text-muted-foreground flex items-center gap-2">
              <AlertTriangle className="h-3 w-3" />
              发现该用户与 <span className="text-foreground font-semibold">{order.similarCases}</span> 个历史欺诈账户存在共享设备/IP/收款方关系
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Card({
  title,
  icon: Icon,
  children,
}: {
  title?: string;
  icon?: typeof Sparkles;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      {title && (
        <div className="flex items-center gap-2 mb-3">
          {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
          <span className="text-sm font-semibold">{title}</span>
        </div>
      )}
      {children}
    </div>
  );
}

function KV({ icon: Icon, label, value, mono }: { icon?: typeof Globe; label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-start gap-2 py-1.5 text-xs">
      {Icon && <Icon className="h-3.5 w-3.5 text-muted-foreground shrink-0 mt-0.5" />}
      <span className="text-muted-foreground w-20 shrink-0">{label}</span>
      <span className={`flex-1 ${mono ? "font-mono text-[11px]" : ""}`}>{value}</span>
    </div>
  );
}

function Stat({ label, value, suffix, tone }: { label: string; value: string; suffix?: string; tone: "primary" | "critical" | "info" }) {
  const c = { primary: "var(--primary)", critical: "var(--risk-critical)", info: "var(--info)" }[tone];
  return (
    <div className="rounded-lg bg-card border border-border p-3">
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div className="mt-1 num text-xl font-semibold" style={{ color: c }}>
        {value}
        {suffix && <span className="text-xs text-muted-foreground ml-1 font-normal">{suffix}</span>}
      </div>
    </div>
  );
}

function FraudGraph({ riskLevel }: { riskLevel: string }) {
  const nodes = [
    { x: 50, y: 50, r: 20, color: "var(--risk-critical)", label: "本账号", primary: true },
    { x: 18, y: 28, r: 8 },
    { x: 78, y: 22, r: 7 },
    { x: 82, y: 60, r: 9 },
    { x: 22, y: 75, r: 8 },
    { x: 50, y: 88, r: 7 },
    { x: 12, y: 55, r: 6 },
    { x: 92, y: 40, r: 6 },
    { x: 38, y: 12, r: 5 },
    { x: 65, y: 80, r: 7 },
  ];
  return (
    <svg viewBox="0 0 100 100" className="w-full h-full" preserveAspectRatio="xMidYMid meet">
      {nodes.slice(1).map((n, i) => (
        <line
          key={i}
          x1={50}
          y1={50}
          x2={n.x}
          y2={n.y}
          stroke="var(--risk-high)"
          strokeWidth={0.3}
          strokeOpacity={0.5}
          strokeDasharray="1 1"
        />
      ))}
      {nodes.map((n, i) => (
        <g key={i}>
          <circle
            cx={n.x}
            cy={n.y}
            r={n.r / 6}
            fill={n.color ?? "var(--risk-high)"}
            opacity={n.primary ? 1 : 0.6}
          />
          {n.primary && (
            <circle cx={n.x} cy={n.y} r={n.r / 4} fill="none" stroke="var(--risk-critical)" strokeWidth={0.2} opacity={0.4}>
              <animate attributeName="r" values="3;6;3" dur="2.5s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.5;0;0.5" dur="2.5s" repeatCount="indefinite" />
            </circle>
          )}
        </g>
      ))}
      <text x={50} y={48} textAnchor="middle" fontSize={2.4} fill="var(--card)" fontWeight={600}>
        本账号
      </text>
    </svg>
  );
}
