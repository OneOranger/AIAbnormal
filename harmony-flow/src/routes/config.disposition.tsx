import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Wand2, ArrowLeft, Power, PowerOff, Pencil, Sparkles, MessageSquareWarning, CheckCircle2, XCircle, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import type { DispositionPolicy, FeedbackRecord, DispositionAction } from "@/lib/pipeline-types";
import { CATEGORIES, CATEGORY_META, RISK_LEVEL_META } from "@/lib/taxonomy";

export const Route = createFileRoute("/config/disposition")({
  component: DispositionPage,
  head: () => ({ meta: [{ title: "自动处置 + 反馈 · PayGuard AI" }] }),
});

const ACTION_LABEL: Record<DispositionAction, string> = {
  intercept: "立即拦截",
  review: "人工复核",
  release: "放行",
  auto_refund: "自动退款",
  force_2fa: "强制二次验证",
  freeze_account: "冻结账户",
  add_blacklist: "加入黑名单",
  watchlist: "加入观察名单",
  notify_user: "通知用户",
  escalate: "升级人工",
};

function DispositionPage() {
  const [tab, setTab] = useState<"policies" | "feedback">("policies");
  const [policies, setPolicies] = useState<DispositionPolicy[]>([]);
  const [feedback, setFeedback] = useState<FeedbackRecord[]>([]);
  const [editing, setEditing] = useState<DispositionPolicy | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.listPolicies(), api.listFeedback()]).then(([p, f]) => {
      setPolicies(p);
      setFeedback(f);
    });
  }, []);

  const totals = useMemo(() => {
    const exec = policies.reduce((s, p) => s + p.executedCount24h, 0);
    const reversed = policies.reduce((s, p) => s + p.reversedCount24h, 0);
    const correct = feedback.filter((f) => f.isCorrect).length;
    const accuracy = feedback.length ? correct / feedback.length : 0;
    return { exec, reversed, accuracy, savedLoss: feedback.reduce((s, f) => s + (f.estimatedSavedLoss ?? 0), 0) };
  }, [policies, feedback]);

  async function toggle(p: DispositionPolicy) {
    setPolicies((arr) => arr.map((x) => (x.id === p.id ? { ...x, enabled: !x.enabled } : x)));
    await api.togglePolicy(p.id, !p.enabled);
    flash(`策略「${p.name}」已${!p.enabled ? "启用" : "停用"}`);
  }
  function flash(msg: string) { setToast(msg); setTimeout(() => setToast(null), 2200); }

  return (
    <div className="p-6 lg:p-8 max-w-[1600px] mx-auto space-y-5">
      <div>
        <Link to="/analysis" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground mb-1.5">
          <ArrowLeft className="h-3 w-3" /> 返回 AI 推理链路
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <Wand2 className="h-6 w-6 text-success" /> 自动处置 + 反馈
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          链路第 4 环 · 处置策略编排 · 高置信自动执行 · 人工反馈回流 RAG / 模型再训练
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Stat label="24h 处置数" value={totals.exec.toLocaleString()} />
        <Stat label="人工撤回" value={totals.reversed} tone="warn" />
        <Stat label="AI 准确率" value={`${(totals.accuracy * 100).toFixed(1)}%`} tone="primary" />
        <Stat label="估算挽损" value={`¥${totals.savedLoss.toLocaleString()}`} tone="success" />
      </div>

      {/* Tabs */}
      <div className="inline-flex rounded-lg border border-border bg-card p-0.5">
        <TabBtn active={tab === "policies"} onClick={() => setTab("policies")}>处置策略 ({policies.length})</TabBtn>
        <TabBtn active={tab === "feedback"} onClick={() => setTab("feedback")}>反馈记录 ({feedback.length})</TabBtn>
      </div>

      {tab === "policies" ? (
        <div className="space-y-3">
          {policies.sort((a, b) => b.priority - a.priority).map((p) => (
            <div key={p.id} className="rounded-xl border border-border bg-card p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-base font-semibold">{p.name}</span>
                    <span className="text-[10.5px] num px-1.5 py-0.5 rounded bg-muted">优先级 {p.priority}</span>
                    {p.autoExecute && <span className="text-[10.5px] px-1.5 py-0.5 rounded bg-success/10 text-success">自动执行</span>}
                    {p.requireHumanApproval && <span className="text-[10.5px] px-1.5 py-0.5 rounded bg-warning/10 text-warning">需审批</span>}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{p.description}</p>

                  <div className="flex flex-wrap items-center gap-2 mt-3 text-[11px]">
                    <span className="text-muted-foreground">触发:</span>
                    <span className="px-1.5 py-0.5 rounded bg-muted">
                      {p.category === "all" ? "全部类别" : CATEGORY_META[p.category].label}
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-muted">
                      {p.riskLevel === "all" ? "全部等级" : RISK_LEVEL_META[p.riskLevel].label}
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-muted num">分 ≥ {p.minScore}</span>
                    <span className="px-1.5 py-0.5 rounded bg-muted num">置信 ≥ {p.minConfidence}%</span>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 mt-2 text-[11px]">
                    <span className="text-muted-foreground">动作:</span>
                    <span className="px-2 py-0.5 rounded bg-primary/10 text-primary font-medium">{ACTION_LABEL[p.primaryAction]}</span>
                    {p.secondaryActions.map((a) => (
                      <span key={a} className="px-2 py-0.5 rounded bg-muted">{ACTION_LABEL[a]}</span>
                    ))}
                  </div>
                </div>

                <div className="flex flex-col items-end gap-1.5 shrink-0">
                  <div className="inline-flex gap-1">
                    <button onClick={() => toggle(p)} className="p-1.5 rounded hover:bg-accent">
                      {p.enabled ? <PowerOff className="h-3.5 w-3.5" /> : <Power className="h-3.5 w-3.5 text-success" />}
                    </button>
                    <button onClick={() => setEditing(p)} className="p-1.5 rounded hover:bg-accent">
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                  </div>
                  <span className={`text-[11px] ${p.enabled ? "text-success" : "text-muted-foreground"}`}>
                    {p.enabled ? "● 生效中" : "○ 已停用"}
                  </span>
                </div>
              </div>

              {/* metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-3 pt-3 border-t border-border text-xs">
                <Mini label="24h 执行" value={p.executedCount24h.toLocaleString()} />
                <Mini label="成功率" value={`${(p.successRate * 100).toFixed(1)}%`} tone="success" />
                <Mini label="人工撤回" value={p.reversedCount24h} tone={p.reversedCount24h > 20 ? "warn" : undefined} />
                <Mini label="平均耗时" value={`${p.avgProcessingMs} ms`} />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <div className="p-4 border-b border-border flex items-center gap-2 text-xs text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            反馈记录回流: 标注样本 → 知识库 (RAG) + 模型再训练队列,持续优化 AI 决策准确率
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/40">
                <tr className="text-left text-xs text-muted-foreground">
                  <th className="px-3 py-2.5 font-medium">订单</th>
                  <th className="px-3 py-2.5 font-medium">AI 建议</th>
                  <th className="px-3 py-2.5 font-medium">最终动作</th>
                  <th className="px-3 py-2.5 font-medium">反馈类型</th>
                  <th className="px-3 py-2.5 font-medium">复核人</th>
                  <th className="px-3 py-2.5 font-medium">备注</th>
                  <th className="px-3 py-2.5 font-medium text-right">回流</th>
                </tr>
              </thead>
              <tbody>
                {feedback.slice(0, 30).map((f) => (
                  <tr key={f.id} className="border-t border-border hover:bg-muted/30">
                    <td className="px-3 py-2.5 num text-xs">{f.orderNo}</td>
                    <td className="px-3 py-2.5 text-xs">{ACTION_LABEL[f.aiSuggestion]}</td>
                    <td className="px-3 py-2.5 text-xs">
                      <span className="font-medium">{ACTION_LABEL[f.finalAction]}</span>
                      {f.aiSuggestion !== f.finalAction && (
                        <span className="ml-1 text-[10.5px] text-[color:var(--risk-high)]">已修改</span>
                      )}
                    </td>
                    <td className="px-3 py-2.5">
                      <FeedbackPill type={f.feedbackType} />
                    </td>
                    <td className="px-3 py-2.5 text-xs">{f.reviewer}</td>
                    <td className="px-3 py-2.5 text-xs text-muted-foreground max-w-[280px] truncate" title={f.comment}>{f.comment}</td>
                    <td className="px-3 py-2.5 text-right">
                      <div className="inline-flex gap-1">
                        {f.fedToRAG && <span title="已入 RAG" className="text-[10px] px-1.5 py-0.5 rounded bg-info/10 text-info">RAG</span>}
                        {f.fedToTraining && <span title="已入训练队列" className="text-[10px] px-1.5 py-0.5 rounded bg-primary/10 text-primary">训练</span>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {editing && <PolicyEditor policy={editing} onClose={() => setEditing(null)} onSaved={(p) => {
        setPolicies((arr) => arr.map((x) => (x.id === p.id ? p : x)));
        setEditing(null);
        flash("策略已保存");
      }} />}

      {toast && <div className="fixed bottom-6 right-6 px-4 py-2.5 rounded-lg bg-foreground text-background text-sm shadow-lg">{toast}</div>}
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string | number; tone?: "primary" | "success" | "warn" }) {
  const color = tone === "primary" ? "var(--primary)" : tone === "success" ? "var(--success)" : tone === "warn" ? "var(--warning)" : "var(--foreground)";
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="text-[11px] text-muted-foreground">{label}</div>
      <div className="num text-2xl font-semibold mt-1" style={{ color }}>{value}</div>
    </div>
  );
}
function Mini({ label, value, tone }: { label: string; value: string | number; tone?: "success" | "warn" }) {
  const color = tone === "success" ? "var(--success)" : tone === "warn" ? "var(--warning)" : "var(--foreground)";
  return (
    <div>
      <div className="text-[10.5px] text-muted-foreground">{label}</div>
      <div className="num font-semibold mt-0.5" style={{ color }}>{value}</div>
    </div>
  );
}
function TabBtn({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick} className={`px-4 h-8 text-sm rounded-md font-medium transition-colors ${active ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"}`}>
      {children}
    </button>
  );
}
function FeedbackPill({ type }: { type: FeedbackRecord["feedbackType"] }) {
  const meta: Record<FeedbackRecord["feedbackType"], { label: string; icon: typeof CheckCircle2; color: string }> = {
    confirm: { label: "确认正确", icon: CheckCircle2, color: "var(--success)" },
    override: { label: "人工修改", icon: RefreshCw, color: "var(--warning)" },
    partial_correct: { label: "部分正确", icon: MessageSquareWarning, color: "var(--info)" },
    false_positive: { label: "误杀", icon: XCircle, color: "var(--risk-high)" },
    false_negative: { label: "漏判", icon: XCircle, color: "var(--risk-critical)" },
  };
  const m = meta[type];
  const Icon = m.icon;
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium px-1.5 py-0.5 rounded" style={{ background: `color-mix(in oklab, ${m.color} 12%, transparent)`, color: m.color }}>
      <Icon className="h-3 w-3" /> {m.label}
    </span>
  );
}

function PolicyEditor({ policy, onClose, onSaved }: { policy: DispositionPolicy; onClose: () => void; onSaved: (p: DispositionPolicy) => void }) {
  const [form, setForm] = useState<DispositionPolicy>(policy);
  const [saving, setSaving] = useState(false);
  async function save() {
    setSaving(true);
    await api.upsertPolicy(form);
    onSaved({ ...form, updatedAt: new Date().toISOString() });
    setSaving(false);
  }
  const ALL_ACTIONS = Object.keys(ACTION_LABEL) as DispositionAction[];
  return (
    <div className="fixed inset-0 z-50 bg-black/30 flex items-stretch justify-end" onClick={onClose}>
      <div className="w-full max-w-xl bg-card border-l border-border h-full overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="px-5 h-14 border-b border-border flex items-center justify-between sticky top-0 bg-card">
          <div className="font-semibold">编辑处置策略</div>
          <button onClick={onClose} className="p-1.5 rounded hover:bg-accent">×</button>
        </div>
        <div className="p-5 space-y-4">
          <Field label="策略名称"><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" /></Field>
          <Field label="描述"><textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} className="input" /></Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="类别">
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value as DispositionPolicy["category"] })} className="input">
                <option value="all">全部</option>
                {CATEGORIES.map((c) => <option key={c} value={c}>{CATEGORY_META[c].label}</option>)}
              </select>
            </Field>
            <Field label="风险等级">
              <select value={form.riskLevel} onChange={(e) => setForm({ ...form, riskLevel: e.target.value as DispositionPolicy["riskLevel"] })} className="input">
                <option value="all">全部</option>
                {Object.entries(RISK_LEVEL_META).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
              </select>
            </Field>
            <Field label="风险分阈值"><input type="number" value={form.minScore} onChange={(e) => setForm({ ...form, minScore: +e.target.value })} className="input num" /></Field>
            <Field label="置信度阈值 %"><input type="number" value={form.minConfidence} onChange={(e) => setForm({ ...form, minConfidence: +e.target.value })} className="input num" /></Field>
            <Field label="优先级"><input type="number" value={form.priority} onChange={(e) => setForm({ ...form, priority: +e.target.value })} className="input num" /></Field>
            <Field label="冷却分钟"><input type="number" value={form.cooldownMinutes} onChange={(e) => setForm({ ...form, cooldownMinutes: +e.target.value })} className="input num" /></Field>
          </div>

          <Field label="主要动作">
            <select value={form.primaryAction} onChange={(e) => setForm({ ...form, primaryAction: e.target.value as DispositionAction })} className="input">
              {ALL_ACTIONS.map((a) => <option key={a} value={a}>{ACTION_LABEL[a]}</option>)}
            </select>
          </Field>
          <Field label="次要动作 (可多选)">
            <div className="flex flex-wrap gap-1.5">
              {ALL_ACTIONS.map((a) => {
                const on = form.secondaryActions.includes(a);
                return (
                  <button key={a} type="button"
                    onClick={() => setForm({ ...form, secondaryActions: on ? form.secondaryActions.filter((x) => x !== a) : [...form.secondaryActions, a] })}
                    className={`px-2.5 h-7 rounded-md text-xs border ${on ? "bg-primary/10 border-primary/30 text-primary" : "border-border"}`}
                  >{ACTION_LABEL[a]}</button>
                );
              })}
            </div>
          </Field>

          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.autoExecute} onChange={(e) => setForm({ ...form, autoExecute: e.target.checked })} /> 自动执行 (无需人工)</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.requireHumanApproval} onChange={(e) => setForm({ ...form, requireHumanApproval: e.target.checked })} /> 需要人工审批</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.feedbackRequired} onChange={(e) => setForm({ ...form, feedbackRequired: e.target.checked })} /> 强制反馈回流</label>
          </div>

          <Field label="通知渠道">
            <div className="flex flex-wrap gap-1.5">
              {(["email", "sms", "webhook", "im"] as const).map((c) => {
                const on = form.notifyChannels.includes(c);
                return (
                  <button key={c} type="button"
                    onClick={() => setForm({ ...form, notifyChannels: on ? form.notifyChannels.filter((x) => x !== c) : [...form.notifyChannels, c] })}
                    className={`px-2.5 h-7 rounded-md text-xs border ${on ? "bg-primary/10 border-primary/30 text-primary" : "border-border"}`}
                  >{c}</button>
                );
              })}
            </div>
          </Field>
        </div>
        <div className="px-5 h-14 border-t border-border flex items-center justify-end gap-2 sticky bottom-0 bg-card">
          <button onClick={onClose} className="px-3 h-8 rounded-md border border-border text-sm">取消</button>
          <button onClick={save} disabled={saving} className="px-3 h-8 rounded-md bg-primary text-primary-foreground text-sm font-medium disabled:opacity-50">
            {saving ? "保存中..." : "保存"}
          </button>
        </div>
        <style>{`.input{display:block;width:100%;min-height:36px;padding:8px 10px;border:1px solid var(--input);border-radius:6px;background:transparent;font-size:13px;line-height:1.5;}`}</style>
      </div>
    </div>
  );
}
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block"><div className="text-xs font-medium text-muted-foreground mb-1.5">{label}</div>{children}</label>;
}
