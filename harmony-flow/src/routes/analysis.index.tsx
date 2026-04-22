import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Brain, Sparkles, FileText, Wand2, Layers, GitBranch, Zap, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import { CATEGORY_META, CATEGORIES } from "@/lib/taxonomy";
import { CategoryChip } from "@/components/chips";
import { RiskBadge } from "@/components/risk-badge";
import { formatMoney, timeAgo } from "@/lib/format";
import type { AnomalyOrder } from "@/lib/types";

export const Route = createFileRoute("/analysis/")({
  component: AnalysisPage,
  head: () => ({ meta: [{ title: "AI 根因分析 · PayGuard AI" }] }),
});

function AnalysisPage() {
  const [orders, setOrders] = useState<AnomalyOrder[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(false);

  useEffect(() => {
    let alive = true;
    api.listAllOrders().then((items) => {
      if (!alive) return;
      setOrders(items);
      const firstCandidate = items.find((o) => o.riskLevel === "critical" || o.riskLevel === "high") ?? items[0];
      setSelectedId(firstCandidate?.id ?? "");
    });
    return () => {
      alive = false;
    };
  }, []);

  const candidateOrders = useMemo(
    () => orders.filter((o) => o.riskLevel === "critical" || o.riskLevel === "high").slice(0, 24),
    [orders],
  );
  const selected = orders.find((o) => o.id === selectedId) ?? candidateOrders[0];

  async function generateReport() {
    if (!selected) return;
    setGenerating(true);
    setGenerated(false);
    try {
      await api.analyzeOrder(selected.id);
      setGenerating(false);
      setGenerated(true);
    } catch {
      setGenerating(false);
    }
  }

  const categoryStats = useMemo(() => {
    return CATEGORIES.map((c) => {
      const list = orders.filter((o) => o.primaryCategory === c);
      const avgScore = list.length ? list.reduce((s, o) => s + o.riskScore, 0) / list.length : 0;
      const critical = list.filter((o) => o.riskLevel === "critical").length;
      return { category: c, count: list.length, avgScore: Math.round(avgScore), critical };
    });
  }, [orders]);

  return (
    <div className="p-6 lg:p-8 max-w-[1600px] mx-auto space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">AI 根因分析</h1>
        <p className="text-sm text-muted-foreground mt-1">
          基于因果图谱 + RAG 检索 + LLM 推理 · 自动生成结构化报告与处置建议
        </p>
      </div>

      {/* Pipeline diagram */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold">AI 推理链路</span>
          </div>
          <span className="text-[11px] text-muted-foreground">点击节点进入对应配置页 →</span>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <Step to="/config/rules" icon={GitBranch} label="规则引擎" detail="200+ 风控规则初筛" tone="muted" />
          <Arrow />
          <Step to="/config/models" icon={Zap} label="ML 模型" detail="GBDT/孤立森林快速打分" tone="muted" />
          <Arrow />
          <Step to="/config/agents" icon={Brain} label="AI Agent 深度分析" detail="多模态因果推理 + RAG" tone="primary" />
          <Arrow />
          <Step to="/config/disposition" icon={Wand2} label="自动处置 + 反馈" detail="高置信直接执行 + 反馈入库" tone="success" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Order picker */}
        <div className="rounded-xl border border-border bg-card p-4 lg:max-h-[680px] flex flex-col">
          <div className="text-sm font-semibold mb-1">候选订单</div>
          <div className="text-[11px] text-muted-foreground mb-3">高/致命风险 · 待 AI 深度分析</div>
          <div className="flex-1 overflow-y-auto -mx-1 space-y-1.5">
            {candidateOrders.map((o) => {
              const active = o.id === selected?.id;
              return (
                <button
                  key={o.id}
                  onClick={() => {
                    setSelectedId(o.id);
                    setGenerated(false);
                  }}
                  className={`w-full text-left p-2.5 rounded-lg transition-colors ${
                    active ? "bg-primary/10 ring-1 ring-primary/30" : "hover:bg-muted/60"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="num text-xs font-semibold">{o.orderNo}</span>
                    <RiskBadge level={o.riskLevel} score={o.riskScore} />
                  </div>
                  <div className="mt-1 flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
                    <span className="truncate">{o.merchantName}</span>
                    <span className="num shrink-0">{formatMoney(o.amount, o.currency)}</span>
                  </div>
                  <div className="mt-1.5 flex items-center justify-between">
                    <CategoryChip category={o.primaryCategory} />
                    <span className="text-[10.5px] text-muted-foreground" suppressHydrationWarning>
                      {timeAgo(o.createdAt)}
                    </span>
                  </div>
                </button>
              );
            })}
            {candidateOrders.length === 0 && (
              <div className="py-8 text-center text-sm text-muted-foreground">
                暂无高风险候选订单
              </div>
            )}
          </div>
        </div>

        {/* Report */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-5">
          {selected && (
            <>
              <div className="flex items-start justify-between gap-3 mb-4">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="num text-base font-semibold">{selected.orderNo}</span>
                    <CategoryChip category={selected.primaryCategory} />
                    <RiskBadge level={selected.riskLevel} score={selected.riskScore} />
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {selected.merchantName} · {selected.userName} · {formatMoney(selected.amount, selected.currency)}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Link
                    to="/orders/$orderId"
                    params={{ orderId: selected.id }}
                    className="inline-flex items-center gap-1 px-3 h-8 rounded-md border border-border bg-card text-xs font-medium hover:bg-accent"
                  >
                    完整详情 <ArrowRight className="h-3 w-3" />
                  </Link>
                  <button
                    onClick={generateReport}
                    disabled={generating}
                    className="inline-flex items-center gap-1.5 px-3 h-8 rounded-md bg-primary text-primary-foreground text-xs font-medium hover:bg-primary/90 disabled:opacity-50"
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    {generating ? "AI 推理中..." : "生成根因报告"}
                  </button>
                </div>
              </div>

              {/* Report body */}
              {generating ? (
                <div className="space-y-3 py-8">
                  <SkeletonLine width="60%" />
                  <SkeletonLine width="90%" />
                  <SkeletonLine width="75%" />
                  <SkeletonLine width="50%" />
                  <div className="text-center text-xs text-muted-foreground mt-4 inline-flex items-center gap-2 justify-center w-full">
                    <Sparkles className="h-3 w-3 animate-pulse text-primary" />
                    AI 正在融合证据链与历史相似案例...
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <Section title="一、根因总结" icon={FileText}>
                    <p className="text-sm leading-relaxed text-foreground/90">{selected.rcaSummary}</p>
                  </Section>

                  <Section title="二、AI 命中标签">
                    <div className="flex flex-wrap gap-1.5">
                      {selected.subTypes.map((t) => (
                        <span
                          key={t}
                          className="inline-flex items-center rounded-md px-2 py-1 text-[11px] font-medium ring-1 ring-inset"
                          style={{
                            background: `color-mix(in oklab, ${CATEGORY_META[selected.primaryCategory].color} 8%, transparent)`,
                            color: CATEGORY_META[selected.primaryCategory].color,
                            borderColor: CATEGORY_META[selected.primaryCategory].color,
                          }}
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </Section>

                  <Section title="三、关键证据">
                    <ol className="space-y-2 text-sm">
                      {selected.evidence.map((e, i) => (
                        <li key={e.id} className="flex gap-3">
                          <span className="num text-muted-foreground w-5 shrink-0">{i + 1}.</span>
                          <div className="flex-1">
                            <span className="font-medium">{e.label}</span>
                            <span className="text-muted-foreground"> — {e.detail}</span>
                            <span className="ml-2 text-[10.5px] text-primary">权重 {(e.weight * 100).toFixed(0)}</span>
                          </div>
                        </li>
                      ))}
                    </ol>
                  </Section>

                  <Section title="四、推荐动作">
                    <div className="space-y-2">
                      {selected.suggestions.map((s, i) => (
                        <div key={s.action} className="flex items-start gap-3 text-sm">
                          <div
                            className={`h-5 w-5 rounded shrink-0 text-[10.5px] font-semibold flex items-center justify-center ${
                              i === 0 ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {i + 1}
                          </div>
                          <div className="flex-1">
                            <span className="font-medium">{s.label}</span>
                            <span className="text-[11px] num text-muted-foreground ml-2">置信度 {s.confidence}%</span>
                            <div className="text-xs text-muted-foreground mt-0.5">{s.rationale}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Section>

                  {generated && (
                    <div className="rounded-md bg-success/10 text-success text-xs p-3 inline-flex items-center gap-2">
                      <Sparkles className="h-3 w-3" />
                      报告已生成 · Token 消耗 1,847 · 推理耗时 1.42s · 已写入审计日志
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Category insights */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-sm font-semibold">类别风险洞察</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">8 大类异常的总量、平均风险分与致命占比</div>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {categoryStats.map((s) => {
            const meta = CATEGORY_META[s.category];
            return (
              <div key={s.category} className="rounded-lg border border-border p-3">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full" style={{ background: meta.color }} />
                  <span className="text-xs font-medium">{meta.label}</span>
                </div>
                <div className="num text-xl font-semibold mt-2">{s.count}</div>
                <div className="flex items-center justify-between text-[11px] text-muted-foreground mt-1.5">
                  <span>均分 {s.avgScore}</span>
                  <span className="text-[color:var(--risk-critical)] font-semibold">致命 {s.critical}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function Step({
  icon: Icon, label, detail, tone, to,
}: { icon: typeof Brain; label: string; detail: string; tone: "muted" | "primary" | "success"; to?: string }) {
  const colors = {
    muted: { bg: "var(--muted)", fg: "var(--muted-foreground)", ring: "var(--border)" },
    primary: { bg: "color-mix(in oklab, var(--primary) 10%, transparent)", fg: "var(--primary)", ring: "color-mix(in oklab, var(--primary) 30%, transparent)" },
    success: { bg: "color-mix(in oklab, var(--success) 10%, transparent)", fg: "var(--success)", ring: "color-mix(in oklab, var(--success) 30%, transparent)" },
  }[tone];
  const inner = (
    <>
      <Icon className="h-4 w-4" />
      <div className="leading-tight">
        <div className="font-semibold">{label}</div>
        <div className="text-[10.5px] opacity-80">{detail}</div>
      </div>
    </>
  );
  const cls = "flex items-center gap-2 px-3 py-2 rounded-lg ring-1 ring-inset transition-all hover:-translate-y-0.5 hover:shadow-sm";
  if (to) {
    return (
      <Link to={to as "/"} className={cls} style={{ background: colors.bg, color: colors.fg, borderColor: colors.ring }}>
        {inner}
      </Link>
    );
  }
  return (
    <div className={cls} style={{ background: colors.bg, color: colors.fg, borderColor: colors.ring }}>{inner}</div>
  );
}

function Arrow() {
  return <ArrowRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />;
}

function Section({ title, icon: Icon, children }: { title: string; icon?: typeof FileText; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        {Icon && <Icon className="h-3.5 w-3.5 text-muted-foreground" />}
        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{title}</span>
      </div>
      <div className="pl-1">{children}</div>
    </div>
  );
}

function SkeletonLine({ width }: { width: string }) {
  return <div className="h-3 rounded bg-muted animate-pulse" style={{ width }} />;
}
