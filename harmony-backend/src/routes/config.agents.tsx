import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Brain, ArrowLeft, Sparkles, Database, Wrench, Shield, PlayCircle, Save } from "lucide-react";
import { api } from "@/lib/api";
import type { AgentConfig, KnowledgeBase, LLMProvider } from "@/lib/pipeline-types";
import { CATEGORIES, CATEGORY_META } from "@/lib/taxonomy";

export const Route = createFileRoute("/config/agents")({
  component: AgentsPage,
  head: () => ({ meta: [{ title: "AI Agent 配置 · PayGuard AI" }] }),
});

const PROVIDERS: { value: LLMProvider; label: string }[] = [
  { value: "qwen-max", label: "通义千问 Max" },
  { value: "deepseek-v3", label: "DeepSeek V3" },
  { value: "gpt-4o", label: "OpenAI GPT-4o" },
  { value: "claude-sonnet", label: "Claude Sonnet" },
  { value: "private-llm", label: "私有部署 LLM" },
];

function AgentsPage() {
  const [agents, setAgents] = useState<AgentConfig[]>([]);
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [testInput, setTestInput] = useState("分析订单 PAY202604000123 的根因");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ output: string; tokens: number; latencyMs: number } | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.listAgents(), api.listKnowledgeBases()]).then(([a, k]) => {
      setAgents(a);
      setKbs(k);
      setActiveId(a[0]?.id ?? "");
    });
  }, []);

  const active = agents.find((a) => a.id === activeId);

  async function patch(p: Partial<AgentConfig>) {
    if (!active) return;
    setAgents((arr) => arr.map((a) => (a.id === active.id ? { ...a, ...p } : a)));
    await api.updateAgent(active.id, p);
    flash("配置已保存");
  }
  async function runTest() {
    if (!active) return;
    setTesting(true);
    setTestResult(null);
    const r = await api.testAgent(active.id, testInput);
    setTestResult(r);
    setTesting(false);
  }
  function flash(msg: string) { setToast(msg); setTimeout(() => setToast(null), 2200); }

  return (
    <div className="p-6 lg:p-8 max-w-[1600px] mx-auto space-y-5">
      <div>
        <Link to="/analysis" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground mb-1.5">
          <ArrowLeft className="h-3 w-3" /> 返回 AI 推理链路
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <Brain className="h-6 w-6 text-primary" /> AI Agent 配置
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          链路第 3 环 · LLM 选型 / RAG 知识库 / 工具调用 / 触发条件 / 幻觉防护
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
        {/* Agent 列表 */}
        <div className="space-y-1.5">
          {agents.map((a) => (
            <button
              key={a.id}
              onClick={() => { setActiveId(a.id); setTestResult(null); }}
              className={`w-full text-left p-3 rounded-lg border transition-colors ${a.id === activeId ? "bg-primary/10 border-primary/30" : "border-border hover:bg-muted/60"}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold">{a.name}</span>
                <span className={`h-2 w-2 rounded-full ${a.enabled ? "bg-success" : "bg-muted-foreground"}`} />
              </div>
              <div className="text-[11px] text-muted-foreground mt-0.5 line-clamp-2">{a.description}</div>
              <div className="flex items-center gap-2 text-[10.5px] num text-muted-foreground mt-2">
                <span>{a.provider}</span>·<span>{a.callCount24h.toLocaleString()} 次/24h</span>
              </div>
            </button>
          ))}
        </div>

        {active && (
          <div className="lg:col-span-3 space-y-4">
            {/* 头部 */}
            <div className="rounded-xl border border-border bg-card p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-base font-semibold">{active.name}</span>
                    <label className="inline-flex items-center gap-1.5 text-xs cursor-pointer">
                      <input type="checkbox" checked={active.enabled} onChange={(e) => patch({ enabled: e.target.checked })} />
                      <span className={active.enabled ? "text-success" : "text-muted-foreground"}>{active.enabled ? "已启用" : "已停用"}</span>
                    </label>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{active.description}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                <KV label="24h 调用" value={active.callCount24h.toLocaleString()} />
                <KV label="平均延迟" value={`${active.avgLatencyMs} ms`} />
                <KV label="平均 Tokens" value={active.avgTokens.toLocaleString()} />
                <KV label="24h 成本" value={`$${active.costUSD24h.toFixed(2)}`} tone="primary" />
              </div>
            </div>

            {/* LLM 配置 */}
            <Section icon={Sparkles} title="LLM 调用配置">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Field label="LLM 提供方">
                  <select value={active.provider} onChange={(e) => patch({ provider: e.target.value as LLMProvider })} className="input">
                    {PROVIDERS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
                  </select>
                </Field>
                <Field label="模型版本"><input value={active.model} onChange={(e) => patch({ model: e.target.value })} className="input num" /></Field>
                <Field label="最大 Tokens"><input type="number" value={active.maxTokens} onChange={(e) => patch({ maxTokens: +e.target.value })} className="input num" /></Field>
              </div>
              <div className="grid grid-cols-2 gap-4 mt-4">
                <SliderField label="Temperature" value={active.temperature} step={0.05} min={0} max={1} onChange={(v) => patch({ temperature: v })} />
                <SliderField label="Top P" value={active.topP} step={0.05} min={0} max={1} onChange={(v) => patch({ topP: v })} />
              </div>
              <Field label="System Prompt">
                <textarea value={active.systemPrompt} onChange={(e) => patch({ systemPrompt: e.target.value })} rows={4} className="input" />
              </Field>
            </Section>

            {/* 触发 */}
            <Section icon={Brain} title="触发条件">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <SliderField label="触发风险分阈值" value={active.triggerScore} min={0} max={100} step={1} onChange={(v) => patch({ triggerScore: v })} />
                <Field label="触发模式 (多选)">
                  <div className="flex flex-wrap gap-1.5">
                    {(["auto", "manual", "rule_escalation", "low_confidence"] as const).map((t) => {
                      const on = active.triggers.includes(t);
                      return (
                        <button
                          key={t}
                          onClick={() => patch({ triggers: on ? active.triggers.filter((x) => x !== t) : [...active.triggers, t] })}
                          className={`px-2.5 h-7 rounded-md text-xs border ${on ? "bg-primary/10 border-primary/30 text-primary" : "border-border"}`}
                        >
                          {t}
                        </button>
                      );
                    })}
                  </div>
                </Field>
              </div>
              <Field label="触发类别 (多选)">
                <div className="flex flex-wrap gap-1.5">
                  {CATEGORIES.map((c) => {
                    const on = active.triggerCategories.includes(c);
                    return (
                      <button
                        key={c}
                        onClick={() => patch({ triggerCategories: on ? active.triggerCategories.filter((x) => x !== c) : [...active.triggerCategories, c] })}
                        className={`px-2.5 h-7 rounded-md text-xs border ${on ? "border-primary/40" : "border-border"}`}
                        style={on ? { background: `color-mix(in oklab, ${CATEGORY_META[c].color} 12%, transparent)`, color: CATEGORY_META[c].color } : {}}
                      >
                        {CATEGORY_META[c].label}
                      </button>
                    );
                  })}
                </div>
              </Field>
            </Section>

            {/* RAG */}
            <Section icon={Database} title="RAG 知识库">
              <div className="flex items-center gap-4 mb-3 flex-wrap">
                <ToggleField label="启用 RAG" checked={active.enableRAG} onChange={(v) => patch({ enableRAG: v })} />
                <ToggleField label="启用因果图谱" checked={active.enableCausalGraph} onChange={(v) => patch({ enableCausalGraph: v })} />
                <ToggleField label="启用多模态" checked={active.enableMultimodal} onChange={(v) => patch({ enableMultimodal: v })} />
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-muted-foreground">Top K</span>
                  <input type="number" value={active.ragTopK} onChange={(e) => patch({ ragTopK: +e.target.value })} className="w-16 h-7 px-2 rounded border border-input bg-transparent num" />
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {kbs.map((k) => {
                  const on = active.ragKnowledgeBases.includes(k.id);
                  return (
                    <label key={k.id} className={`flex items-start gap-2.5 p-3 rounded-lg border cursor-pointer transition-colors ${on ? "border-primary/40 bg-primary/5" : "border-border hover:bg-muted/40"}`}>
                      <input
                        type="checkbox"
                        checked={on}
                        onChange={() => patch({ ragKnowledgeBases: on ? active.ragKnowledgeBases.filter((x) => x !== k.id) : [...active.ragKnowledgeBases, k.id] })}
                        className="mt-0.5"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium">{k.name}</div>
                        <div className="text-[11px] text-muted-foreground mt-0.5 num">
                          {k.documentCount.toLocaleString()} 文档 · {k.vectorCount.toLocaleString()} 向量 · {k.embedding}
                        </div>
                      </div>
                    </label>
                  );
                })}
              </div>
            </Section>

            {/* 工具 */}
            <Section icon={Wrench} title="工具调用 (Function Calling)">
              <div className="space-y-2">
                {active.tools.map((t, i) => (
                  <div key={t.name} className="flex items-center gap-3 p-2.5 rounded-lg border border-border">
                    <input
                      type="checkbox"
                      checked={t.enabled}
                      onChange={(e) => {
                        const tools = [...active.tools];
                        tools[i] = { ...t, enabled: e.target.checked };
                        patch({ tools });
                      }}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="num text-sm font-medium">{t.name}</div>
                      <div className="text-[11px] text-muted-foreground">{t.description}</div>
                    </div>
                    <span className="num text-[11px] text-muted-foreground">{t.callCount24h.toLocaleString()} 次/24h</span>
                  </div>
                ))}
              </div>
            </Section>

            {/* 防护 */}
            <Section icon={Shield} title="幻觉防护与合规">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <ToggleField label="幻觉检测" checked={active.enableHallucinationCheck} onChange={(v) => patch({ enableHallucinationCheck: v })} />
                <ToggleField label="事实 Grounding" checked={active.enableFactGrounding} onChange={(v) => patch({ enableFactGrounding: v })} />
                <ToggleField label="敏感信息过滤" checked={active.enableSensitiveFilter} onChange={(v) => patch({ enableSensitiveFilter: v })} />
              </div>
              <div className="mt-3 text-xs text-muted-foreground">
                当前幻觉率: <span className="num font-semibold text-foreground">{(active.hallucinationRate * 100).toFixed(2)}%</span>
              </div>
            </Section>

            {/* 测试 */}
            <Section icon={PlayCircle} title="Playground 在线测试">
              <textarea value={testInput} onChange={(e) => setTestInput(e.target.value)} rows={2} className="input" placeholder="输入测试 Prompt..." />
              <div className="flex items-center justify-between mt-3">
                <button onClick={runTest} disabled={testing} className="inline-flex items-center gap-1.5 px-3 h-8 rounded-md bg-primary text-primary-foreground text-xs font-medium disabled:opacity-50">
                  <PlayCircle className="h-3.5 w-3.5" /> {testing ? "推理中..." : "运行"}
                </button>
                {testResult && (
                  <div className="text-[11px] text-muted-foreground num">
                    Tokens: <span className="text-foreground font-semibold">{testResult.tokens}</span> · 延迟: <span className="text-foreground font-semibold">{testResult.latencyMs} ms</span>
                  </div>
                )}
              </div>
              {testResult && (
                <pre className="mt-3 p-3 rounded-lg bg-muted/40 text-xs whitespace-pre-wrap leading-relaxed">{testResult.output}</pre>
              )}
            </Section>
          </div>
        )}
      </div>

      {toast && (
        <div className="fixed bottom-6 right-6 px-4 py-2.5 rounded-lg bg-foreground text-background text-sm shadow-lg inline-flex items-center gap-2">
          <Save className="h-3.5 w-3.5" /> {toast}
        </div>
      )}

      <style>{`.input{display:block;width:100%;min-height:36px;padding:8px 10px;border:1px solid var(--input);border-radius:6px;background:transparent;font-size:13px;line-height:1.5;}`}</style>
    </div>
  );
}

function KV({ label, value, tone }: { label: string; value: string; tone?: "primary" }) {
  return (
    <div className="rounded-lg border border-border p-3">
      <div className="text-[10.5px] text-muted-foreground">{label}</div>
      <div className="num text-base font-semibold mt-0.5" style={{ color: tone === "primary" ? "var(--primary)" : "var(--foreground)" }}>{value}</div>
    </div>
  );
}
function Section({ icon: Icon, title, children }: { icon: typeof Brain; title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <div className="flex items-center gap-2 text-sm font-semibold mb-4"><Icon className="h-4 w-4 text-primary" /> {title}</div>
      <div className="space-y-3">{children}</div>
    </div>
  );
}
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <div className="text-xs font-medium text-muted-foreground mb-1.5">{label}</div>
      {children}
    </label>
  );
}
function SliderField({ label, value, min, max, step, onChange }: { label: string; value: number; min: number; max: number; step: number; onChange: (v: number) => void }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
        <span className="num text-sm font-semibold">{value}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(+e.target.value)} className="w-full accent-primary" />
    </div>
  );
}
function ToggleField({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="inline-flex items-center gap-2 text-xs cursor-pointer">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span>{label}</span>
    </label>
  );
}
