import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/lib/types";
import { RISK_LEVEL_META } from "@/lib/taxonomy";

const COLOR: Record<RiskLevel, string> = {
  critical: "bg-[color:var(--risk-critical)]/12 text-[color:var(--risk-critical)] ring-[color:var(--risk-critical)]/30",
  high: "bg-[color:var(--risk-high)]/12 text-[color:var(--risk-high)] ring-[color:var(--risk-high)]/30",
  medium: "bg-[color:var(--risk-medium)]/15 text-[oklch(0.45_0.12_75)] ring-[color:var(--risk-medium)]/40",
  low: "bg-[color:var(--risk-low)]/12 text-[oklch(0.4_0.13_155)] ring-[color:var(--risk-low)]/30",
};

export function RiskBadge({ level, score, className }: { level: RiskLevel; score?: number; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-semibold ring-1 ring-inset",
        COLOR[level],
        className,
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current"></span>
      {RISK_LEVEL_META[level].label}
      {score !== undefined && <span className="num ml-0.5">{score}</span>}
    </span>
  );
}

export function RiskScoreBar({ score }: { score: number }) {
  const color = score >= 85 ? "var(--risk-critical)" : score >= 65 ? "var(--risk-high)" : score >= 40 ? "var(--risk-medium)" : "var(--risk-low)";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 rounded-full bg-muted overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${score}%`, background: color }} />
      </div>
      <span className="num text-xs font-semibold" style={{ color }}>
        {score}
      </span>
    </div>
  );
}
