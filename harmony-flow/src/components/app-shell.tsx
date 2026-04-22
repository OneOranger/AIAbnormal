import { Link, useLocation } from "@tanstack/react-router";
import {
  LayoutDashboard,
  ShieldAlert,
  Brain,
  FileSpreadsheet,
  MessageSquare,
  Settings2,
  Activity,
  Sparkles,
  GitBranch,
  Zap,
  Wand2,
} from "lucide-react";
import { cn } from "@/lib/utils";

type NavItem = { to: string; label: string; icon: typeof LayoutDashboard; exact?: boolean };
const NAV: NavItem[] = [
  { to: "/", label: "概览", icon: LayoutDashboard, exact: true },
  { to: "/orders", label: "异常订单", icon: ShieldAlert },
  { to: "/analysis", label: "AI 根因分析", icon: Brain },
  { to: "/reconciliation", label: "AI 智能对账", icon: FileSpreadsheet },
  { to: "/agent", label: "Agent 对话", icon: MessageSquare },
];
const CONFIG_NAV: NavItem[] = [
  { to: "/config/rules", label: "规则引擎", icon: GitBranch },
  { to: "/config/models", label: "ML 模型", icon: Zap },
  { to: "/config/agents", label: "AI Agent", icon: Brain },
  { to: "/config/disposition", label: "处置 + 反馈", icon: Wand2 },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <aside className="hidden md:flex w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar">
        <div className="flex items-center gap-2.5 px-5 h-16 border-b border-sidebar-border">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-primary to-[oklch(0.65_0.2_280)]">
            <Sparkles className="h-4 w-4 text-primary-foreground" />
          </div>
          <div className="leading-tight">
            <div className="text-sm font-semibold text-sidebar-foreground">PayGuard AI</div>
            <div className="text-[11px] text-muted-foreground">异常订单智能处理</div>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {NAV.map((item) => {
            const active = item.exact ? pathname === item.to : pathname.startsWith(item.to);
            const Icon = item.icon;
            return (
              <Link
                key={item.to}
                to={item.to as "/"}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}

          <div className="pt-4 pb-1.5 px-3 text-[10.5px] uppercase tracking-wider text-muted-foreground/70 font-semibold">
            AI 推理链路配置
          </div>
          {CONFIG_NAV.map((item) => {
            const active = pathname.startsWith(item.to);
            const Icon = item.icon;
            return (
              <Link
                key={item.to}
                to={item.to as "/"}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t border-sidebar-border">
          <div className="rounded-lg bg-accent p-3">
            <div className="flex items-center gap-2 text-xs font-medium text-accent-foreground">
              <Activity className="h-3.5 w-3.5" /> 实时风控引擎
            </div>
            <div className="mt-1.5 flex items-center justify-between text-[11px] text-muted-foreground">
              <span>QPS</span>
              <span className="num font-semibold text-success">8,432</span>
            </div>
            <div className="mt-1 flex items-center justify-between text-[11px] text-muted-foreground">
              <span>P99 延迟</span>
              <span className="num font-semibold">1.34s</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-border bg-card/60 backdrop-blur flex items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="md:hidden flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary">
                <Sparkles className="h-3.5 w-3.5 text-primary-foreground" />
              </div>
              <span className="text-sm font-semibold">PayGuard AI</span>
            </div>
            <div className="hidden md:flex items-center gap-2 text-sm">
              <span className="text-muted-foreground">规则引擎</span>
              <span className="text-muted-foreground">→</span>
              <span className="text-muted-foreground">传统 ML 初筛</span>
              <span className="text-muted-foreground">→</span>
              <span className="font-semibold text-primary">AI Agent 深度分析</span>
              <span className="text-muted-foreground">→</span>
              <span className="text-muted-foreground">闭环反馈</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 text-xs text-muted-foreground">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-60"></span>
                <span className="relative inline-flex h-2 w-2 rounded-full bg-success"></span>
              </span>
              引擎运行正常
            </div>
            <button className="p-2 rounded-md hover:bg-accent transition-colors">
              <Settings2 className="h-4 w-4 text-muted-foreground" />
            </button>
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary to-[oklch(0.7_0.18_320)] text-primary-foreground text-xs font-semibold flex items-center justify-center">
              FA
            </div>
          </div>
        </header>

        <main className="flex-1 min-w-0">{children}</main>
      </div>
    </div>
  );
}
