import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { zodValidator, fallback } from "@tanstack/zod-adapter";
import { z } from "zod";
import { useMemo, useState } from "react";
import { Search, Filter, Download, Sparkles, ChevronLeft, ChevronRight } from "lucide-react";

import { CATEGORIES, CATEGORY_META, STATUS_META } from "@/lib/taxonomy";
import { CategoryChip, StatusChip, Tag } from "@/components/chips";
import { RiskBadge, RiskScoreBar } from "@/components/risk-badge";
import { formatMoney, timeAgo } from "@/lib/format";

const searchSchema = z.object({
  category: fallback(z.string(), "all").default("all"),
  riskLevel: fallback(z.string(), "all").default("all"),
  status: fallback(z.string(), "all").default("all"),
  q: fallback(z.string(), "").default(""),
  page: fallback(z.number(), 1).default(1),
});

export const Route = createFileRoute("/orders/")({
  validateSearch: zodValidator(searchSchema),
  component: OrdersPage,
  head: () => ({ meta: [{ title: "异常订单 · PayGuard AI" }] }),
});

import { MOCK_ORDERS } from "@/lib/mock-data";

function OrdersPage() {
  const { category, riskLevel, status, q, page } = Route.useSearch();
  const navigate = useNavigate({ from: Route.fullPath });
  const [searchInput, setSearchInput] = useState(q);

  return (
    <OrdersInner
      cat={category}
      rl={riskLevel}
      st={status}
      q={q}
      page={page}
      navigate={navigate}
      searchInput={searchInput}
      setSearchInput={setSearchInput}
    />
  );
}

function OrdersInner({
  cat,
  rl,
  st,
  q,
  page,
  navigate,
  searchInput,
  setSearchInput,
}: {
  cat: string;
  rl: string;
  st: string;
  q: string;
  page: number;
  navigate: ReturnType<typeof useNavigate>;
  searchInput: string;
  setSearchInput: (s: string) => void;
}) {
  const PAGE_SIZE = 20;

  const filtered = useMemo(() => {
    let items = MOCK_ORDERS;
    if (cat !== "all") items = items.filter((o) => o.primaryCategory === cat);
    if (rl !== "all") items = items.filter((o) => o.riskLevel === rl);
    if (st !== "all") items = items.filter((o) => o.status === st);
    if (q.trim()) {
      const s = q.toLowerCase();
      items = items.filter(
        (o) =>
          o.orderNo.toLowerCase().includes(s) ||
          o.userName.toLowerCase().includes(s) ||
          o.merchantName.toLowerCase().includes(s) ||
          o.userId.toLowerCase().includes(s),
      );
    }
    return items;
  }, [cat, rl, st, q]);

  const total = filtered.length;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const items = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const counts = useMemo(() => {
    const m: Record<string, number> = { all: MOCK_ORDERS.length };
    CATEGORIES.forEach((c) => (m[c] = MOCK_ORDERS.filter((o) => o.primaryCategory === c).length));
    return m;
  }, []);

  function setSearch(patch: Record<string, string | number>) {
    navigate({ search: (prev) => ({ ...prev, ...patch, page: patch.page ?? 1 }) as never });
  }

  return (
    <div className="p-6 lg:p-8 space-y-5 max-w-[1600px] mx-auto">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">异常订单</h1>
          <p className="text-sm text-muted-foreground mt-1">
            AI 自动分类打标 · {total.toLocaleString()} 笔异常订单 · 8 大类 50+ 子类
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-3 py-2 text-xs font-medium hover:bg-accent">
            <Download className="h-3.5 w-3.5" /> 导出
          </button>
          <button className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90">
            <Sparkles className="h-3.5 w-3.5" /> 批量 AI 处置
          </button>
        </div>
      </div>

      {/* Category tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        <CategoryTab label="全部" count={counts.all} active={cat === "all"} onClick={() => setSearch({ category: "all" })} />
        {CATEGORIES.map((c) => (
          <CategoryTab
            key={c}
            label={CATEGORY_META[c].label}
            count={counts[c] ?? 0}
            color={CATEGORY_META[c].color}
            active={cat === c}
            onClick={() => setSearch({ category: c })}
          />
        ))}
      </div>

      {/* Filters */}
      <div className="rounded-xl border border-border bg-card p-3 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") setSearch({ q: searchInput });
            }}
            placeholder="搜索订单号 / 用户 / 商户..."
            className="w-full pl-8 pr-3 h-9 rounded-md bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-ring/40"
          />
        </div>
        <Select
          value={rl}
          onChange={(v) => setSearch({ riskLevel: v })}
          options={[
            { value: "all", label: "全部风险" },
            { value: "critical", label: "致命" },
            { value: "high", label: "高" },
            { value: "medium", label: "中" },
            { value: "low", label: "低" },
          ]}
        />
        <Select
          value={st}
          onChange={(v) => setSearch({ status: v })}
          options={[
            { value: "all", label: "全部状态" },
            ...Object.entries(STATUS_META).map(([k, v]) => ({ value: k, label: v.label })),
          ]}
        />
        <div className="text-xs text-muted-foreground inline-flex items-center gap-1">
          <Filter className="h-3 w-3" />
          {total.toLocaleString()} 条结果
        </div>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/40 text-xs text-muted-foreground">
              <tr>
                <th className="text-left font-medium px-4 py-2.5">订单号</th>
                <th className="text-left font-medium px-4 py-2.5">商户 / 用户</th>
                <th className="text-left font-medium px-4 py-2.5">金额</th>
                <th className="text-left font-medium px-4 py-2.5">主分类</th>
                <th className="text-left font-medium px-4 py-2.5">AI 子标签</th>
                <th className="text-left font-medium px-4 py-2.5">风险分</th>
                <th className="text-left font-medium px-4 py-2.5">状态</th>
                <th className="text-left font-medium px-4 py-2.5">时间</th>
              </tr>
            </thead>
            <tbody>
              {items.map((o) => (
                <tr key={o.id} className="border-t border-border/60 hover:bg-muted/30 transition-colors">
                  <td className="px-4 py-3">
                    <Link to="/orders/$orderId" params={{ orderId: o.id }} className="font-medium text-primary hover:underline num">
                      {o.orderNo}
                    </Link>
                    <div className="text-[11px] text-muted-foreground mt-0.5">{o.channel.toUpperCase()}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-xs font-medium">{o.merchantName}</div>
                    <div className="text-[11px] text-muted-foreground">
                      {o.userName} · {o.userId} · {o.ipCountry}
                    </div>
                  </td>
                  <td className="px-4 py-3 num font-semibold">{formatMoney(o.amount, o.currency)}</td>
                  <td className="px-4 py-3"><CategoryChip category={o.primaryCategory} /></td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1 max-w-[260px]">
                      {o.subTypes.slice(0, 3).map((t) => (
                        <Tag key={t}>{t}</Tag>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3"><RiskScoreBar score={o.riskScore} /></td>
                  <td className="px-4 py-3"><StatusChip status={o.status} /></td>
                  <td className="px-4 py-3 text-xs text-muted-foreground" suppressHydrationWarning>
                    {timeAgo(o.createdAt)}
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={8} className="text-center py-10 text-sm text-muted-foreground">
                    暂无符合条件的订单
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-border bg-muted/20 text-xs text-muted-foreground">
          <div>
            第 {page} / {pageCount} 页 · 每页 {PAGE_SIZE} 条
          </div>
          <div className="flex items-center gap-1">
            <button
              disabled={page <= 1}
              onClick={() => setSearch({ page: page - 1 })}
              className="p-1.5 rounded-md border border-border bg-card disabled:opacity-40 disabled:cursor-not-allowed hover:bg-accent"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
            </button>
            <button
              disabled={page >= pageCount}
              onClick={() => setSearch({ page: page + 1 })}
              className="p-1.5 rounded-md border border-border bg-card disabled:opacity-40 disabled:cursor-not-allowed hover:bg-accent"
            >
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function CategoryTab({
  label,
  count,
  color,
  active,
  onClick,
}: {
  label: string;
  count: number;
  color?: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`shrink-0 inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium border transition-all ${
        active ? "bg-primary text-primary-foreground border-primary shadow-sm" : "bg-card border-border hover:bg-accent"
      }`}
    >
      {color && !active && <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />}
      {label}
      <span className={`num text-[10.5px] px-1.5 rounded ${active ? "bg-white/20" : "bg-muted"}`}>{count}</span>
    </button>
  );
}

function Select({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="h-9 rounded-md bg-background border border-input px-2 text-xs focus:outline-none focus:ring-2 focus:ring-ring/40"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}
