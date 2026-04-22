import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import {
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  Copy,
  XCircle,
  Sparkles,
  Upload,
  Search,
  Loader2,
  ArrowRight,
} from "lucide-react";
import { api } from "@/lib/api";
import { CHANNEL_META } from "@/lib/taxonomy";
import { formatMoney, formatDateTime } from "@/lib/format";
import type { ReconRecord, ReconStatus } from "@/lib/types";

export const Route = createFileRoute("/reconciliation/")({
  component: ReconPage,
  head: () => ({ meta: [{ title: "AI 智能对账 · PayGuard AI" }] }),
});

const STATUS_META: Record<ReconStatus, { label: string; color: string; icon: typeof CheckCircle2 }> = {
  matched: { label: "已匹配", color: "var(--success)", icon: CheckCircle2 },
  unmatched: { label: "未匹配", color: "var(--warning)", icon: AlertCircle },
  discrepancy: { label: "差异", color: "var(--warning)", icon: AlertCircle },
  duplicate: { label: "重复", color: "var(--info)", icon: Copy },
  missing: { label: "缺失", color: "var(--risk-critical)", icon: XCircle },
};

const DIFF_LABEL = {
  timing: "时序差异",
  amount: "金额差异",
  fx: "汇率差异",
  fee: "手续费差异",
  duplicate: "重复条目",
  missing: "缺失交易",
  partial: "部分支付",
  format: "格式错误",
};

function ReconPage() {
  const [statusFilter, setStatusFilter] = useState<"all" | ReconStatus>("all");
  const [channelFilter, setChannelFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [running, setRunning] = useState(false);
  const [matchProgress, setMatchProgress] = useState(0);
  const [voucherFor, setVoucherFor] = useState<string | null>(null);
  const [records, setRecords] = useState<ReconRecord[]>([]);
  const [allRecords, setAllRecords] = useState<ReconRecord[]>([]);

  useEffect(() => {
    let alive = true;
    api.listRecon({ status: statusFilter, channel: channelFilter, search }).then((items) => {
      if (alive) setRecords(items);
    });
    return () => {
      alive = false;
    };
  }, [statusFilter, channelFilter, search]);

  useEffect(() => {
    let alive = true;
    api.listRecon().then((items) => {
      if (alive) setAllRecords(items);
    });
    return () => {
      alive = false;
    };
  }, []);

  const stats = useMemo(() => {
    const total = allRecords.length;
    const matched = allRecords.filter((r) => r.status === "matched").length;
    const discrepancy = allRecords.filter((r) => r.status === "discrepancy").length;
    const missing = allRecords.filter((r) => r.status === "missing").length;
    const duplicate = allRecords.filter((r) => r.status === "duplicate").length;
    const totalDiff = allRecords.reduce((s, r) => s + Math.abs(r.diff), 0);
    return { total, matched, discrepancy, missing, duplicate, totalDiff, matchRate: total ? ((matched / total) * 100).toFixed(1) : "0.0" };
  }, [allRecords]);

  function runMatch() {
    setRunning(true);
    setMatchProgress(0);
    const refresh = api.runReconMatch()
      .then(() => Promise.all([api.listRecon({ status: statusFilter, channel: channelFilter, search }), api.listRecon()]))
      .then(([filteredItems, allItems]) => {
        setRecords(filteredItems);
        setAllRecords(allItems);
      })
      .catch(() => undefined);
    const id = setInterval(() => {
      setMatchProgress((p) => {
        const next = p + Math.random() * 12 + 5;
        if (next >= 100) {
          clearInterval(id);
          refresh.finally(() => setTimeout(() => setRunning(false), 400));
          return 100;
        }
        return next;
      });
    }, 200);
  }

  return (
    <div className="p-6 lg:p-8 max-w-[1600px] mx-auto space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">AI 智能对账</h1>
          <p className="text-sm text-muted-foreground mt-1">
            多渠道模糊匹配 · 差异根因 · 自动生成调整凭证
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-3 py-2 text-xs font-medium hover:bg-accent">
            <Upload className="h-3.5 w-3.5" /> 上传对账文件
          </button>
          <button
            onClick={runMatch}
            disabled={running}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
          >
            {running ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
            {running ? "AI 匹配中..." : "AI 一键对账"}
          </button>
        </div>
      </div>

      {/* AI matching progress */}
      {running && (
        <div className="rounded-xl border border-primary/30 bg-primary/[0.04] p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Sparkles className="h-4 w-4 text-primary animate-pulse" />
              AI 智能匹配中 · 模糊容差 ±0.01元 · 参考号语义匹配
            </div>
            <span className="num text-xs font-semibold text-primary">{Math.floor(matchProgress)}%</span>
          </div>
          <div className="h-2 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary to-[oklch(0.7_0.18_280)] transition-all duration-200"
              style={{ width: `${matchProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* KPI */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <Stat label="总记录数" value={stats.total.toLocaleString()} />
        <Stat label="自动匹配率" value={`${stats.matchRate}%`} tone="success" delta={`${stats.matched} 笔已匹配`} />
        <Stat label="差异" value={stats.discrepancy.toString()} tone="warning" />
        <Stat label="缺失" value={stats.missing.toString()} tone="critical" />
        <Stat label="累计差异金额" value={formatMoney(stats.totalDiff)} tone="warning" />
      </div>

      {/* Filters */}
      <div className="rounded-xl border border-border bg-card p-3 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索内部参考号 / 渠道参考号..."
            className="w-full pl-8 pr-3 h-9 rounded-md bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-ring/40"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as ReconStatus | "all")}
          className="h-9 rounded-md bg-background border border-input px-2 text-xs"
        >
          <option value="all">全部状态</option>
          <option value="matched">已匹配</option>
          <option value="discrepancy">差异</option>
          <option value="duplicate">重复</option>
          <option value="missing">缺失</option>
        </select>
        <select
          value={channelFilter}
          onChange={(e) => setChannelFilter(e.target.value)}
          className="h-9 rounded-md bg-background border border-input px-2 text-xs"
        >
          <option value="all">全部渠道</option>
          {Object.entries(CHANNEL_META).map(([k, v]) => (
            <option key={k} value={k}>
              {v.label}
            </option>
          ))}
        </select>
        <span className="text-xs text-muted-foreground">{records.length.toLocaleString()} 条结果</span>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="overflow-x-auto max-h-[600px]">
          <table className="w-full text-sm">
            <thead className="bg-muted/40 text-xs text-muted-foreground sticky top-0">
              <tr>
                <th className="text-left font-medium px-4 py-2.5">日期</th>
                <th className="text-left font-medium px-4 py-2.5">内部参考</th>
                <th className="text-left font-medium px-4 py-2.5">渠道参考</th>
                <th className="text-left font-medium px-4 py-2.5">渠道</th>
                <th className="text-right font-medium px-4 py-2.5">内部金额</th>
                <th className="text-right font-medium px-4 py-2.5">渠道金额</th>
                <th className="text-right font-medium px-4 py-2.5">差额</th>
                <th className="text-left font-medium px-4 py-2.5">状态 / 类型</th>
                <th className="text-left font-medium px-4 py-2.5">AI 处置</th>
              </tr>
            </thead>
            <tbody>
              {records.slice(0, 200).map((r) => {
                const sm = STATUS_META[r.status];
                const Icon = sm.icon;
                const channelLabel = CHANNEL_META[r.channel].label;
                return (
                  <tr key={r.id} className="border-t border-border/60 hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-2.5 text-xs text-muted-foreground whitespace-nowrap">{formatDateTime(r.date)}</td>
                    <td className="px-4 py-2.5 num text-xs">{r.internalRef}</td>
                    <td className="px-4 py-2.5 num text-xs">{r.channelRef}</td>
                    <td className="px-4 py-2.5 text-xs">
                      <span
                        className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10.5px]"
                        style={{ background: `color-mix(in oklab, ${CHANNEL_META[r.channel].color} 12%, transparent)`, color: CHANNEL_META[r.channel].color }}
                      >
                        {channelLabel}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 num text-right">{formatMoney(r.internalAmount)}</td>
                    <td className="px-4 py-2.5 num text-right">{r.channelAmount === 0 ? "—" : formatMoney(r.channelAmount)}</td>
                    <td className={`px-4 py-2.5 num text-right font-semibold ${r.diff === 0 ? "" : r.diff > 0 ? "text-[color:var(--info)]" : "text-[color:var(--risk-high)]"}`}>
                      {r.diff === 0 ? "—" : (r.diff > 0 ? "+" : "") + formatMoney(r.diff)}
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-1.5">
                        <Icon className="h-3.5 w-3.5" style={{ color: sm.color }} />
                        <span className="text-xs font-medium" style={{ color: sm.color }}>
                          {sm.label}
                        </span>
                        {r.diffType && (
                          <span className="text-[10.5px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                            {DIFF_LABEL[r.diffType]}
                          </span>
                        )}
                      </div>
                      {r.rootCause && <div className="text-[11px] text-muted-foreground mt-0.5 max-w-md">{r.rootCause}</div>}
                    </td>
                    <td className="px-4 py-2.5">
                      {r.aiSuggestion ? (
                        <button
                          onClick={() => setVoucherFor(r.id)}
                          className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                        >
                          <Sparkles className="h-3 w-3" /> 生成调整凭证
                        </button>
                      ) : (
                        <span className="text-[11px] text-muted-foreground">无需处置</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Voucher modal */}
      {voucherFor && (
        <div
          className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4"
          onClick={() => setVoucherFor(null)}
        >
          <div className="bg-card rounded-xl border border-border max-w-lg w-full p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-2 mb-1">
              <FileSpreadsheet className="h-4 w-4 text-primary" />
              <span className="text-base font-semibold">AI 自动调整凭证</span>
            </div>
            <div className="text-xs text-muted-foreground mb-4">
              基于差异类型与会计科目映射规则,AI 已生成以下凭证
            </div>
            {(() => {
              const r = allRecords.find((x) => x.id === voucherFor) ?? records.find((x) => x.id === voucherFor);
              if (!r) return null;
              return (
                <div className="space-y-3">
                  <div className="rounded-lg bg-muted/40 p-3 text-xs space-y-1">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">凭证编号</span>
                      <span className="num font-medium">VC-{Date.now().toString().slice(-8)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">对账记录</span>
                      <span className="num">{r.internalRef}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">差异金额</span>
                      <span className="num font-semibold">{formatMoney(Math.abs(r.diff))}</span>
                    </div>
                  </div>
                  <div className="rounded-lg border border-border overflow-hidden text-xs">
                    <table className="w-full">
                      <thead className="bg-muted/60">
                        <tr>
                          <th className="text-left p-2 font-medium">科目</th>
                          <th className="text-right p-2 font-medium">借方</th>
                          <th className="text-right p-2 font-medium">贷方</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr className="border-t border-border">
                          <td className="p-2">财务费用 - 渠道手续费</td>
                          <td className="p-2 text-right num">{formatMoney(Math.abs(r.diff))}</td>
                          <td className="p-2 text-right num text-muted-foreground">—</td>
                        </tr>
                        <tr className="border-t border-border">
                          <td className="p-2">银行存款 - {CHANNEL_META[r.channel].label}</td>
                          <td className="p-2 text-right num text-muted-foreground">—</td>
                          <td className="p-2 text-right num">{formatMoney(Math.abs(r.diff))}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div className="rounded-md bg-primary/5 p-3 text-xs text-foreground/80">
                    <div className="font-medium mb-1 text-primary">AI 说明</div>
                    {r.aiSuggestion}
                  </div>
                  <div className="flex justify-end gap-2 pt-2">
                    <button
                      onClick={() => setVoucherFor(null)}
                      className="px-3 h-8 rounded-md border border-border bg-card text-xs hover:bg-accent"
                    >
                      取消
                    </button>
                    <button
                      onClick={() => setVoucherFor(null)}
                      className="px-3 h-8 rounded-md bg-primary text-primary-foreground text-xs font-medium hover:bg-primary/90 inline-flex items-center gap-1"
                    >
                      推送至财务系统 <ArrowRight className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  delta,
  tone = "default",
}: {
  label: string;
  value: string;
  delta?: string;
  tone?: "default" | "success" | "warning" | "critical";
}) {
  const colorMap = {
    default: "var(--foreground)",
    success: "var(--success)",
    warning: "oklch(0.5 0.13 75)",
    critical: "var(--risk-critical)",
  };
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="num text-xl font-semibold mt-1.5" style={{ color: colorMap[tone] }}>
        {value}
      </div>
      {delta && <div className="text-[11px] text-muted-foreground mt-1">{delta}</div>}
    </div>
  );
}
