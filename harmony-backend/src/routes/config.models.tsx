import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Zap, ArrowLeft, RefreshCw, Sliders, TrendingUp, Activity, Sparkles, Cpu } from "lucide-react";
import { api } from "@/lib/api";
import type { MLModel } from "@/lib/pipeline-types";
import { CATEGORY_META } from "@/lib/taxonomy";

export const Route = createFileRoute("/config/models")({
  component: ModelsPage,
  head: () => ({ meta: [{ title: "ML 模型配置 · PayGuard AI" }] }),
});

function ModelsPage() {
  const [models, setModels] = useState<MLModel[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [retraining, setRetraining] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    api.listModels().then((m) => {
      setModels(m);
      setActiveId(m[0]?.id ?? "");
    });
  }, []);

  const active = models.find((m) => m.id === activeId);
  const totals = useMemo(() => ({
    online: models.filter((m) => m.status === "online").length,
    shadow: models.filter((m) => m.status === "shadow").length,
    qps: models.reduce((s, m) => s + m.qps, 0),
    avgAuc: models.length ? models.reduce((s, m) => s + m.auc, 0) / models.length : 0,
  }), [models]);

  async function retrain(id: string) {
    setRetraining(id);
    await api.retrainModel(id);
    setRetraining(null);
    flash(`已触发模型重训任务`);
  }
  async function updatePatch(patch: Partial<MLModel>) {
    if (!active) return;
    setModels((ms) => ms.map((m) => (m.id === active.id ? { ...m, ...patch } : m)));
    await api.updateModelConfig(active.id, patch);
    flash("配置已保存");
  }
  function flash(msg: string) { setToast(msg); setTimeout(() => setToast(null), 2200); }

  return (
    <div className="p-6 lg:p-8 max-w-[1600px] mx-auto space-y-5">
      <div>
        <Link to="/analysis" className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground mb-1.5">
          <ArrowLeft className="h-3 w-3" /> 返回 AI 推理链路
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <Zap className="h-6 w-6 text-primary" /> ML 模型配置
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          链路第 2 环 · 多模型融合打分 · 阈值/权重/A-B 实验/重训计划
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Stat label="在线模型" value={totals.online} icon={Activity} tone="success" />
        <Stat label="影子模式" value={totals.shadow} icon={Sparkles} tone="info" />
        <Stat label="总 QPS" value={totals.qps.toLocaleString()} icon={Cpu} />
        <Stat label="平均 AUC" value={totals.avgAuc.toFixed(3)} icon={TrendingUp} tone="primary" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* 模型列表 */}
        <div className="rounded-xl border border-border bg-card p-3 space-y-1.5 lg:max-h-[720px] overflow-y-auto">
          {models.map((m) => {
            const sel = m.id === activeId;
            const statusColor = m.status === "online" ? "var(--success)" : m.status === "shadow" ? "var(--info)" : m.status === "training" ? "var(--warning)" : "var(--muted-foreground)";
            return (
              <button
                key={m.id}
                onClick={() => setActiveId(m.id)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${sel ? "bg-primary/10 ring-1 ring-primary/30" : "hover:bg-muted/60"}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-semibold">{m.name}</span>
                  <span className="h-2 w-2 rounded-full" style={{ background: statusColor }} />
                </div>
                <div className="flex items-center gap-2 text-[11px] text-muted-foreground mt-0.5">
                  <span className="num">{m.algo}</span> · <span className="num">{m.version}</span>
                </div>
                <div className="flex items-center justify-between text-[10.5px] mt-2">
                  <span className="text-muted-foreground">AUC</span>
                  <span className="num font-semibold">{m.auc.toFixed(3)}</span>
                </div>
                <div className="flex items-center justify-between text-[10.5px]">
                  <span className="text-muted-foreground">权重</span>
                  <span className="num font-semibold">{(m.weight * 100).toFixed(0)}%</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* 模型详情 */}
        {active && (
          <div className="lg:col-span-2 space-y-4">
            <div className="rounded-xl border border-border bg-card p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-base font-semibold">{active.name}</span>
                    <span className="num text-xs px-1.5 py-0.5 rounded bg-muted">{active.algo}</span>
                    <span className="num text-xs text-muted-foreground">{active.version}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1.5">{active.description}</p>
                </div>
                <button
                  onClick={() => retrain(active.id)}
                  disabled={retraining === active.id}
                  className="inline-flex items-center gap-1.5 px-3 h-8 rounded-md border border-border text-xs font-medium hover:bg-accent disabled:opacity-50"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${retraining === active.id ? "animate-spin" : ""}`} />
                  {retraining === active.id ? "排队中..." : "立即重训"}
                </button>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-4">
                <Metric label="AUC" value={active.auc.toFixed(3)} />
                <Metric label="精确率" value={`${(active.precision * 100).toFixed(1)}%`} />
                <Metric label="召回率" value={`${(active.recall * 100).toFixed(1)}%`} />
                <Metric label="F1" value={active.f1.toFixed(3)} />
                <Metric label="KS" value={active.ks.toFixed(2)} />
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
                <Metric label="QPS" value={active.qps.toLocaleString()} />
                <Metric label="P99 延迟" value={`${active.p99Latency} ms`} />
                <Metric label="PSI 漂移" value={active.driftScore.toFixed(2)} tone={active.driftScore > 0.1 ? "warn" : "ok"} />
                <Metric label="训练样本" value={`${(active.trainSamples / 1e6).toFixed(1)}M`} />
              </div>
            </div>

            {/* 评分配置 */}
            <div className="rounded-xl border border-border bg-card p-5">
              <div className="flex items-center gap-2 text-sm font-semibold mb-4">
                <Sliders className="h-4 w-4 text-primary" /> 打分配置
              </div>
              <div className="space-y-5">
                <SliderRow
                  label="风险分阈值"
                  hint="≥ 此值进入 AI Agent 深度分析"
                  value={active.threshold}
                  min={0} max={100}
                  onChange={(v) => updatePatch({ threshold: v })}
                />
                <SliderRow
                  label="融合权重"
                  hint="本模型在多模型融合中的占比"
                  value={Math.round(active.weight * 100)}
                  min={0} max={100} suffix="%"
                  onChange={(v) => updatePatch({ weight: v / 100 })}
                />
                <SliderRow
                  label="A/B 实验流量"
                  hint="影子/灰度时该模型接收的流量比例"
                  value={Math.round((active.abTestRatio ?? 1) * 100)}
                  min={0} max={100} suffix="%"
                  onChange={(v) => updatePatch({ abTestRatio: v / 100 })}
                />
              </div>
            </div>

            {/* 特征重要性 */}
            <div className="rounded-xl border border-border bg-card p-5">
              <div className="flex items-center gap-2 text-sm font-semibold mb-4">
                <TrendingUp className="h-4 w-4 text-primary" /> 特征重要性 Top {active.features.length}
              </div>
              <div className="space-y-2">
                {[...active.features].sort((a, b) => b.importance - a.importance).map((f) => (
                  <div key={f.name} className="flex items-center gap-3 text-xs">
                    <span className="num w-44 truncate">{f.name}</span>
                    <span className="px-1.5 py-0.5 rounded bg-muted text-[10px] text-muted-foreground">{f.type}</span>
                    <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-primary" style={{ width: `${(f.importance / 0.3) * 100}%` }} />
                    </div>
                    <span className="num w-10 text-right">{(f.importance * 100).toFixed(1)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* 适用类别 */}
            <div className="rounded-xl border border-border bg-card p-4 text-xs text-muted-foreground">
              <span>适用类别: </span>
              <span className="font-medium text-foreground">
                {active.category === "all" ? "全部异常类别" : CATEGORY_META[active.category].label}
              </span>
              <span className="mx-2">·</span>
              <span>负责人: <span className="text-foreground font-medium">{active.owner}</span></span>
              <span className="mx-2">·</span>
              <span>下次重训: <span className="num text-foreground font-medium">{new Date(active.nextRetrainAt).toLocaleDateString()}</span></span>
            </div>
          </div>
        )}
      </div>

      {toast && (
        <div className="fixed bottom-6 right-6 px-4 py-2.5 rounded-lg bg-foreground text-background text-sm shadow-lg">{toast}</div>
      )}
    </div>
  );
}

function Stat({ label, value, icon: Icon, tone }: { label: string; value: string | number; icon: typeof Zap; tone?: "success" | "info" | "primary" }) {
  const color = tone === "success" ? "var(--success)" : tone === "info" ? "var(--info)" : tone === "primary" ? "var(--primary)" : "var(--foreground)";
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-muted-foreground">{label}</span>
        <Icon className="h-3.5 w-3.5 text-muted-foreground" />
      </div>
      <div className="num text-2xl font-semibold mt-1" style={{ color }}>{value}</div>
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: "warn" | "ok" }) {
  return (
    <div className="rounded-lg border border-border p-3">
      <div className="text-[10.5px] text-muted-foreground">{label}</div>
      <div
        className="num text-base font-semibold mt-0.5"
        style={{ color: tone === "warn" ? "var(--warning)" : tone === "ok" ? "var(--success)" : "var(--foreground)" }}
      >
        {value}
      </div>
    </div>
  );
}

function SliderRow({ label, hint, value, min, max, suffix, onChange }: { label: string; hint?: string; value: number; min: number; max: number; suffix?: string; onChange: (v: number) => void }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <div>
          <div className="text-xs font-medium">{label}</div>
          {hint && <div className="text-[10.5px] text-muted-foreground">{hint}</div>}
        </div>
        <span className="num text-sm font-semibold tabular-nums">{value}{suffix ?? ""}</span>
      </div>
      <input
        type="range"
        min={min} max={max} value={value}
        onChange={(e) => onChange(+e.target.value)}
        className="w-full accent-primary"
      />
    </div>
  );
}
