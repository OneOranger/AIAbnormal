import { cn } from "@/lib/utils";
import { CATEGORY_META } from "@/lib/taxonomy";
import type { AnomalyCategory, OrderStatus } from "@/lib/types";
import { STATUS_META } from "@/lib/taxonomy";

export function CategoryChip({ category, className }: { category: AnomalyCategory; className?: string }) {
  const meta = CATEGORY_META[category];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset",
        className,
      )}
      style={{
        background: `color-mix(in oklab, ${meta.color} 10%, transparent)`,
        color: meta.color,
        borderColor: meta.color,
      }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: meta.color }} />
      {meta.label}
    </span>
  );
}

export function StatusChip({ status }: { status: OrderStatus }) {
  const meta = STATUS_META[status];
  return (
    <span
      className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset"
      style={{
        background: `color-mix(in oklab, ${meta.color} 10%, transparent)`,
        color: meta.color,
        borderColor: `color-mix(in oklab, ${meta.color} 30%, transparent)`,
      }}
    >
      {meta.label}
    </span>
  );
}

export function Tag({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={cn("inline-flex items-center rounded-md bg-muted px-1.5 py-0.5 text-[10.5px] text-muted-foreground", className)}>
      {children}
    </span>
  );
}
