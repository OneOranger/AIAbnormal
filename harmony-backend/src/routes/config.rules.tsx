import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import {
  GitBranch, Plus, Search, Filter, Power, PowerOff, Pencil, Sparkles, ArrowLeft, Save, X, TrendingUp, AlertTriangle,
} from "lucide-react";
import { api } from "@/lib/api";
import type { RiskRule, RuleStatus } from "@/lib/pipeline-types";
import { CATEGORIES, CATEGORY_META } from "@/lib/taxonomy";
import { CategoryChip } from "@/components/chips";

export const Route = createFileRoute("/config/rules")({
  component: RulesPage,
  head: () => ({ meta: [{ title: "规则引擎配置 · PayGuard AI" }] }),
});

const STATUS_META: Record<RuleStatus, { label: string; color: string; bg: string }> = {
  active: { label: "生效", color: "var(--success)", bg: "color-mix(in oklab, var(--success) 12%, transparent)" },
  shadow: { label: "影子", color: "var(--info)", bg: "color-mix(in oklab, var(--info) 12%, transparent)" },
  draft: { label: "草稿", color: "var(--warning)", bg: "color-mix(in oklab, var(--warning) 12%, transparent)" },
  disabled: { label: "停用", color: "var(--muted-foreground)", bg: "var(--muted)" },
};

function RulesPage() {
  const [rules, setRules] = useState<RiskRule[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [status, setStatus] = useState("all");
  const [editing, setEditing] = useState<RiskRule | null>(null);
  const [creating, setCreating] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    api.listRules().then(setRules);
  }, []);

  const filtered = useMemo(() => {
    return rules.filter((r) => {
      if (category !== "all" && r.category !== category) return false;
      if (status !== "all" && r.status !== status) return false;
      if (search && !r.name.toLowerCase().includes(search.toLowerCase()) && !r.code.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [rules, search, category, status]);

  const stats = useMemo(() => ({
    total: rules.length,
    active: rules.filter((r) => r.status === "active").length,
    shadow: rules.filter((r) => r.status === "shadow").length,
    hits24h: rules.reduce((s, r) => s + r.hitCount24h, 0),
    avgPrecision: rules.length ? rules.reduce((s, r) => s + r.precision, 0) / rules.length : 0,
  }), [rules]);

  async function toggle(r: RiskRule) {
    const next = r.status === "active" ? "disabled" : "active";
    setRules((rs) => rs.map((x) => (x.id === r.id ? { ...x, status: next } : x)));
    await api.toggleRule(r.id, next === "active");
    flash(`规则 ${r.code} 已${next === "active" ? "启用" : "停用"}`);
  }
  function flash(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 2200);
  }

  return (
    <div className="p-6 lg:p-8 max-w-[1600px] mx-auto space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <Link to="/analysis" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground mb-1.5">
            <ArrowLeft className="h-3 w-3" /> 返回 AI 推理链路
          </Link>
          <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
            <GitBranch className="h-6 w-6 text-primary" /> 规则引擎配置
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            链路第 1 环 · 实时初筛 · 命中规则进入 ML 模型打分,精确率漂移由 AI 持续监控
          </p>
        </div>
        <button
          onClick={() => setCreating(true)}
          className="inline-flex items-center gap-1.5 px-4 h-9 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" /> 新增规则
        </button>
      </div>

      {/* 概览指标 */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <Stat label="规则总数" value={stats.total} />
        <Stat label="生效中" value={stats.active} tone="success" />
        <Stat label="影子运行" value={stats.shadow} tone="info" />
        <Stat label="24h 命中" value={stats.hits24h.toLocaleString()} />
        <Stat label="平均精确率" value={`${(stats.avgPrecision * 100).toFixed(1)}%`} tone="primary" />
      </div>

      {/* 筛选 */}
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索规则名称或编码"
              className="w-full h-9 pl-8 pr-3 rounded-md border border-input bg-background text-sm"
            />
          </div>
          <Filter className="h-3.5 w-3.5 text-muted-foreground ml-1" />
          <select value={category} onChange={(e) => setCategory(e.target.value)} className="h-9 px-2 rounded-md border border-input bg-background text-sm">
            <option value="all">全部类别</option>
            {CATEGORIES.map((c) => <option key={c} value={c}>{CATEGORY_META[c].label}</option>)}
          </select>
          <select value={status} onChange={(e) => setStatus(e.target.value)} className="h-9 px-2 rounded-md border border-input bg-background text-sm">
            <option value="all">全部状态</option>
            <option value="active">生效</option>
            <option value="shadow">影子</option>
            <option value="draft">草稿</option>
            <option value="disabled">停用</option>
          </select>
          <span className="text-xs text-muted-foreground ml-auto">{filtered.length} 条</span>
        </div>
      </div>

      {/* 规则表 */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/40">
              <tr className="text-left text-xs text-muted-foreground">
                <th className="px-3 py-2.5 font-medium">编码 / 名称</th>
                <th className="px-3 py-2.5 font-medium">类别</th>
                <th className="px-3 py-2.5 font-medium">条件 (DSL)</th>
                <th className="px-3 py-2.5 font-medium">动作</th>
                <th className="px-3 py-2.5 font-medium text-right">24h 命中</th>
                <th className="px-3 py-2.5 font-medium text-right">精确率</th>
                <th className="px-3 py-2.5 font-medium">状态</th>
                <th className="px-3 py-2.5 font-medium text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => {
                const sm = STATUS_META[r.status];
                return (
                  <tr key={r.id} className="border-t border-border hover:bg-muted/30">
                    <td className="px-3 py-2.5">
                      <div className="num text-[11px] text-muted-foreground">{r.code}</div>
                      <div className="font-medium">{r.name}</div>
                      <div className="text-[10.5px] text-muted-foreground mt-0.5">v{r.version} · {r.owner}</div>
                    </td>
                    <td className="px-3 py-2.5"><CategoryChip category={r.category} /></td>
                    <td className="px-3 py-2.5">
                      <code className="num text-[11px] bg-muted/50 px-1.5 py-0.5 rounded text-foreground/80 max-w-[260px] inline-block truncate">
                        {r.condition}
                      </code>
                    </td>
                    <td className="px-3 py-2.5">
                      <span className="text-xs">{r.action}</span>
                      <div className="text-[10.5px] text-muted-foreground">+{r.scoreDelta} 分</div>
                    </td>
                    <td className="px-3 py-2.5 text-right num">{r.hitCount24h.toLocaleString()}</td>
                    <td className="px-3 py-2.5 text-right">
                      <div className="num text-xs">{(r.precision * 100).toFixed(1)}%</div>
                      <div className={`text-[10.5px] ${r.falsePositiveRate > 0.05 ? "text-[color:var(--risk-high)]" : "text-muted-foreground"}`}>
                        FP {(r.falsePositiveRate * 100).toFixed(1)}%
                      </div>
                    </td>
                    <td className="px-3 py-2.5">
                      <span
                        className="inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium"
                        style={{ background: sm.bg, color: sm.color }}
                      >
                        {sm.label}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      <div className="inline-flex gap-1">
                        <button
                          onClick={() => toggle(r)}
                          className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground"
                          title={r.status === "active" ? "停用" : "启用"}
                        >
                          {r.status === "active" ? <PowerOff className="h-3.5 w-3.5" /> : <Power className="h-3.5 w-3.5" />}
                        </button>
                        <button
                          onClick={() => setEditing(r)}
                          className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground"
                          title="编辑"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* AI 建议 */}
      <div className="rounded-xl border border-primary/20 bg-primary/5 p-4">
        <div className="flex items-center gap-2 text-sm font-semibold mb-2">
          <Sparkles className="h-4 w-4 text-primary" /> AI 规则优化建议
        </div>
        <div className="space-y-2 text-sm">
          <Suggestion icon={TrendingUp} text="规则 R-BHV-002 召回率下降 8.4% (近 7 天),建议放宽阈值: tx_count_5min > 6" />
          <Suggestion icon={AlertTriangle} text="规则 R-FRD-003 误杀率 12% 偏高,建议补充设备白名单" tone="warn" />
          <Suggestion icon={Sparkles} text="新增建议: 同 IP /24 段 + 新设备 + 大额 → review (基于近 30 天反馈聚合)" tone="primary" />
        </div>
      </div>

      {/* 编辑/新建抽屉 */}
      {(editing || creating) && (
        <RuleEditor
          rule={editing}
          onClose={() => { setEditing(null); setCreating(false); }}
          onSaved={(r) => {
            if (editing) setRules((rs) => rs.map((x) => (x.id === r.id ? r : x)));
            else setRules((rs) => [r, ...rs]);
            setEditing(null);
            setCreating(false);
            flash(`规则 ${r.code} 已保存`);
          }}
        />
      )}

      {toast && (
        <div className="fixed bottom-6 right-6 px-4 py-2.5 rounded-lg bg-foreground text-background text-sm shadow-lg">{toast}</div>
      )}
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string | number; tone?: "success" | "info" | "primary" }) {
  const color = tone === "success" ? "var(--success)" : tone === "info" ? "var(--info)" : tone === "primary" ? "var(--primary)" : "var(--foreground)";
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div className="num text-2xl font-semibold mt-1" style={{ color }}>{value}</div>
    </div>
  );
}

function Suggestion({ icon: Icon, text, tone }: { icon: typeof Sparkles; text: string; tone?: "warn" | "primary" }) {
  const color = tone === "warn" ? "var(--warning)" : tone === "primary" ? "var(--primary)" : "var(--muted-foreground)";
  return (
    <div className="flex items-start gap-2 text-foreground/90">
      <Icon className="h-3.5 w-3.5 mt-0.5 shrink-0" style={{ color }} />
      <span>{text}</span>
      <button className="ml-auto text-[11px] text-primary hover:underline shrink-0">采纳</button>
    </div>
  );
}

function RuleEditor({ rule, onClose, onSaved }: { rule: RiskRule | null; onClose: () => void; onSaved: (r: RiskRule) => void }) {
  const [form, setForm] = useState<RiskRule>(
    rule ?? {
      id: `rule-new-${Date.now()}`,
      code: "R-NEW-001",
      name: "",
      category: "fraud",
      description: "",
      status: "draft",
      scope: "realtime",
      priority: 60,
      condition: "",
      action: "review",
      scoreDelta: 20,
      hitCount24h: 0,
      hitCount7d: 0,
      precision: 0,
      recall: 0,
      falsePositiveRate: 0,
      owner: "当前用户",
      updatedAt: new Date().toISOString(),
      createdAt: new Date().toISOString(),
      version: 1,
      tags: [],
    },
  );
  const [saving, setSaving] = useState(false);

  async function save() {
    setSaving(true);
    await api.upsertRule(form);
    onSaved({ ...form, updatedAt: new Date().toISOString() });
    setSaving(false);
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/30 flex items-stretch justify-end" onClick={onClose}>
      <div className="w-full max-w-xl bg-card border-l border-border h-full overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="px-5 h-14 border-b border-border flex items-center justify-between sticky top-0 bg-card">
          <div className="font-semibold">{rule ? `编辑规则 · ${rule.code}` : "新增规则"}</div>
          <button onClick={onClose} className="p-1.5 rounded hover:bg-accent"><X className="h-4 w-4" /></button>
        </div>
        <div className="p-5 space-y-4">
          <Field label="规则编码"><input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="input" /></Field>
          <Field label="规则名称"><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" /></Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="类别">
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value as RiskRule["category"] })} className="input">
                {CATEGORIES.map((c) => <option key={c} value={c}>{CATEGORY_META[c].label}</option>)}
              </select>
            </Field>
            <Field label="作用范围">
              <select value={form.scope} onChange={(e) => setForm({ ...form, scope: e.target.value as RiskRule["scope"] })} className="input">
                <option value="realtime">实时</option>
                <option value="offline">离线</option>
                <option value="both">实时+离线</option>
              </select>
            </Field>
          </div>
          <Field label="DSL 条件 (示例: device.headless = true AND amount > 5000)">
            <textarea value={form.condition} onChange={(e) => setForm({ ...form, condition: e.target.value })} rows={3} className="input num text-xs" />
          </Field>
          <div className="grid grid-cols-3 gap-3">
            <Field label="动作">
              <select value={form.action} onChange={(e) => setForm({ ...form, action: e.target.value as RiskRule["action"] })} className="input">
                <option value="intercept">拦截</option>
                <option value="review">复核</option>
                <option value="score">仅打分</option>
                <option value="tag">仅打标</option>
                <option value="release">放行</option>
              </select>
            </Field>
            <Field label="风险分加成"><input type="number" value={form.scoreDelta} onChange={(e) => setForm({ ...form, scoreDelta: +e.target.value })} className="input num" /></Field>
            <Field label="优先级"><input type="number" value={form.priority} onChange={(e) => setForm({ ...form, priority: +e.target.value })} className="input num" /></Field>
          </div>
          <Field label="描述"><textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} className="input" /></Field>
          <Field label="状态">
            <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value as RuleStatus })} className="input">
              <option value="draft">草稿</option>
              <option value="shadow">影子运行</option>
              <option value="active">生效</option>
              <option value="disabled">停用</option>
            </select>
          </Field>
        </div>
        <div className="px-5 h-14 border-t border-border flex items-center justify-end gap-2 sticky bottom-0 bg-card">
          <button onClick={onClose} className="px-3 h-8 rounded-md border border-border text-sm">取消</button>
          <button onClick={save} disabled={saving} className="inline-flex items-center gap-1.5 px-3 h-8 rounded-md bg-primary text-primary-foreground text-sm font-medium disabled:opacity-50">
            <Save className="h-3.5 w-3.5" /> {saving ? "保存中..." : "保存"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <div className="text-xs font-medium text-muted-foreground mb-1">{label}</div>
      {children}
      <style>{`.input{display:block;width:100%;height:36px;padding:0 10px;border:1px solid var(--input);border-radius:6px;background:transparent;font-size:13px;}textarea.input{height:auto;padding:8px 10px;line-height:1.5;}`}</style>
    </label>
  );
}
