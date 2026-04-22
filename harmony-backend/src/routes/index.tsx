import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo } from "react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import {
  ShieldAlert,
  TrendingUp,
  Brain,
  FileSpreadsheet,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  Activity,
} from "lucide-react";
import { MOCK_ORDERS, ordersByCategory, ordersTimeline } from "@/lib/mock-data";
import { CATEGORY_META } from "@/lib/taxonomy";
import { CategoryChip, StatusChip } from "@/components/chips";
import { RiskBadge } from "@/components/risk-badge";
import { formatMoney, timeAgo } from "@/lib/format";

export const Route = createFileRoute("/")({
  component: Overview,
  head: () => ({ meta: [{ title: "概览 · PayGuard AI" }] }),
});

function Overview() {
  const stats = useMemo(() => {
    const total = MOCK_ORDERS.length;
    const critical = MOCK_ORDERS.filter((o) => o.riskLevel === "critical").length;
    const intercepted = MOCK_ORDERS.filter((o) => o.status === "intercepted").length;
    const pending = MOCK_ORDERS.filter((o) => o.status === "pending_review").length;
    const savedAmount = MOCK_ORDERS.filter((o) => o.status === "intercepted").reduce((s, o) => s + o.amount, 0);
    return { total, critical, intercepted, pending, savedAmount };
  }, []);

  const byCat = useMemo(() => ordersByCategory(), []);
  const timeline = useMemo(() => ordersTimeline(14), []);
  const topOrders = MOCK_ORDERS.slice(0, 6);

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-[1600px] mx-auto">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">运营概览</h1>
        <p className="text-sm text-muted-foreground mt-1">
          AI 驱动的支付异常订单全景看板 · 数据每 30 秒刷新
        </p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="今日异常订单"
          value={stats.total.toLocaleString()}
          delta="+12.4%"
          icon={ShieldAlert}
          tone="primary"
        />
        <KpiCard
          label="致命风险"
          value={stats.critical.toLocaleString()}
          delta="+3.2%"
          icon={AlertTriangle}
          tone="critical"
        />
        <KpiCard
          label="AI 自动拦截"
          value={stats.intercepted.toLocaleString()}
          delta={`节省 ${formatMoney(stats.savedAmount)}`}
          icon={CheckCircle2}
          tone="success"
        />
        <KpiCard label="待人工复核" value={stats.pending.toLocaleString()} delta="平均 8 分钟响应" icon={Activity} tone="warning" />
      </div>

      {/* Module entries */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ModuleCard
          to="/orders"
          icon={ShieldAlert}
          title="异常订单看板"
          desc="8 大类 50+ 子类异常实时打标,多维筛选与处置"
          accent="oklch(0.55 0.18 265)"
        />
        <ModuleCard
          to="/analysis"
          icon={Brain}
          title="AI 根因分析"
          desc="证据链 + 因果图谱 + Top3 处理动作 + 一键执行"
          accent="oklch(0.6 0.2 320)"
        />
        <ModuleCard
          to="/reconciliation"
          icon={FileSpreadsheet}
          title="AI 智能对账"
          desc="多渠道模糊匹配,差异根因 + 自动调整凭证"
          accent="oklch(0.65 0.16 200)"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-sm font-semibold">异常订单趋势 · 近 14 天</div>
              <div className="text-xs text-muted-foreground mt-0.5">致命/高风险订单分层堆叠</div>
            </div>
            <span className="inline-flex items-center gap-1 text-xs text-success">
              <TrendingUp className="h-3 w-3" /> 拦截率提升 6.8%
            </span>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={timeline}>
              <defs>
                <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="oklch(0.55 0.18 265)" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="oklch(0.55 0.18 265)" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="g2" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="oklch(0.55 0.24 25)" stopOpacity={0.6} />
                  <stop offset="100%" stopColor="oklch(0.55 0.24 25)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.92 0.008 250)" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: "oklch(0.52 0.02 255)" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "oklch(0.52 0.02 255)" }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  background: "var(--card)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Area type="monotone" dataKey="total" stroke="oklch(0.55 0.18 265)" fill="url(#g1)" strokeWidth={2} />
              <Area type="monotone" dataKey="critical" stroke="oklch(0.55 0.24 25)" fill="url(#g2)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <div className="text-sm font-semibold mb-1">异常类别分布</div>
          <div className="text-xs text-muted-foreground mb-4">基于 AI 主分类标签</div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={byCat}
                dataKey="count"
                nameKey="category"
                innerRadius={48}
                outerRadius={80}
                paddingAngle={2}
                stroke="var(--card)"
                strokeWidth={2}
              >
                {byCat.map((entry) => (
                  <Cell key={entry.category} fill={CATEGORY_META[entry.category].color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
                formatter={(v: number, _n, p) => [v, CATEGORY_META[(p.payload as { category: keyof typeof CATEGORY_META }).category].label]}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-1.5 text-[11px] mt-2">
            {byCat.map((c) => (
              <div key={c.category} className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-sm" style={{ background: CATEGORY_META[c.category].color }} />
                <span className="text-muted-foreground">{CATEGORY_META[c.category].label}</span>
                <span className="num ml-auto font-semibold">{c.count}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Recent high-risk */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-sm font-semibold">最新高风险订单</div>
            <div className="text-xs text-muted-foreground mt-0.5">AI 自动打标 · 点击查看根因报告</div>
          </div>
          <Link to="/orders" className="text-xs text-primary hover:underline inline-flex items-center gap-1">
            查看全部 <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
        <div className="overflow-x-auto -mx-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground border-b border-border">
                <th className="font-medium py-2 px-2">订单号</th>
                <th className="font-medium py-2 px-2">商户 / 用户</th>
                <th className="font-medium py-2 px-2">金额</th>
                <th className="font-medium py-2 px-2">类别</th>
                <th className="font-medium py-2 px-2">风险</th>
                <th className="font-medium py-2 px-2">状态</th>
                <th className="font-medium py-2 px-2">时间</th>
              </tr>
            </thead>
            <tbody>
              {topOrders.map((o) => (
                <tr key={o.id} className="border-b border-border/60 hover:bg-muted/40 transition-colors">
                  <td className="py-2.5 px-2">
                    <Link to="/orders/$orderId" params={{ orderId: o.id }} className="font-medium text-primary hover:underline">
                      {o.orderNo}
                    </Link>
                  </td>
                  <td className="py-2.5 px-2">
                    <div className="text-xs">{o.merchantName}</div>
                    <div className="text-[11px] text-muted-foreground">{o.userName} · {o.userId}</div>
                  </td>
                  <td className="py-2.5 px-2 num font-semibold">{formatMoney(o.amount, o.currency)}</td>
                  <td className="py-2.5 px-2"><CategoryChip category={o.primaryCategory} /></td>
                  <td className="py-2.5 px-2"><RiskBadge level={o.riskLevel} score={o.riskScore} /></td>
                  <td className="py-2.5 px-2"><StatusChip status={o.status} /></td>
                  <td className="py-2.5 px-2 text-xs text-muted-foreground">{timeAgo(o.createdAt)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Bar chart of subtypes */}
      <Card>
        <div className="text-sm font-semibold mb-1">分类目订单量 (TOP)</div>
        <div className="text-xs text-muted-foreground mb-4">用于策略迭代和模型训练优先级</div>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={byCat}>
            <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.92 0.008 250)" vertical={false} />
            <XAxis
              dataKey="category"
              tick={{ fontSize: 11, fill: "oklch(0.52 0.02 255)" }}
              tickFormatter={(v) => CATEGORY_META[v as keyof typeof CATEGORY_META].label}
              axisLine={false}
              tickLine={false}
            />
            <YAxis tick={{ fontSize: 11, fill: "oklch(0.52 0.02 255)" }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
              formatter={(v: number) => [v, "订单数"]}
              labelFormatter={(v) => CATEGORY_META[v as keyof typeof CATEGORY_META].label}
            />
            <Bar dataKey="count" radius={[6, 6, 0, 0]}>
              {byCat.map((entry) => (
                <Cell key={entry.category} fill={CATEGORY_META[entry.category].color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}

function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-border bg-card p-5 shadow-sm ${className ?? ""}`}>{children}</div>
  );
}

function KpiCard({
  label,
  value,
  delta,
  icon: Icon,
  tone,
}: {
  label: string;
  value: string;
  delta: string;
  icon: typeof ShieldAlert;
  tone: "primary" | "critical" | "success" | "warning";
}) {
  const colors = {
    primary: { bg: "oklch(0.55 0.18 265 / 0.1)", fg: "oklch(0.55 0.18 265)" },
    critical: { bg: "oklch(0.55 0.24 25 / 0.1)", fg: "oklch(0.55 0.24 25)" },
    success: { bg: "oklch(0.65 0.16 155 / 0.1)", fg: "oklch(0.5 0.16 155)" },
    warning: { bg: "oklch(0.78 0.15 75 / 0.18)", fg: "oklch(0.5 0.13 75)" },
  }[tone];
  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs text-muted-foreground">{label}</div>
          <div className="text-2xl font-semibold mt-1.5 num">{value}</div>
          <div className="text-[11px] mt-1.5" style={{ color: colors.fg }}>{delta}</div>
        </div>
        <div className="h-9 w-9 rounded-lg flex items-center justify-center" style={{ background: colors.bg }}>
          <Icon className="h-4 w-4" style={{ color: colors.fg }} />
        </div>
      </div>
    </Card>
  );
}

function ModuleCard({
  to,
  icon: Icon,
  title,
  desc,
  accent,
}: {
  to: string;
  icon: typeof Brain;
  title: string;
  desc: string;
  accent: string;
}) {
  return (
    <Link to={to as "/"} className="group">
      <Card className="hover:border-primary/40 hover:shadow-md transition-all cursor-pointer h-full">
        <div className="flex items-start gap-3">
          <div
            className="h-10 w-10 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: `color-mix(in oklab, ${accent} 12%, transparent)` }}
          >
            <Icon className="h-5 w-5" style={{ color: accent }} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-semibold">{title}</span>
              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{desc}</p>
          </div>
        </div>
      </Card>
    </Link>
  );
}
