import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { Send, Sparkles, Brain, Search, FileSpreadsheet, TrendingUp, Bot, User } from "lucide-react";
import { api } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

export const Route = createFileRoute("/agent/")({
  component: AgentPage,
  head: () => ({ meta: [{ title: "AI Agent · PayGuard AI" }] }),
});

const QUICK_PROMPTS = [
  { icon: Search, label: "分析订单 PAY202604000123", text: "分析订单 PAY202604000123 的根因" },
  { icon: FileSpreadsheet, label: "昨天对账差异 Top5", text: "昨天对账差异 Top5" },
  { icon: TrendingUp, label: "近 7 天欺诈趋势", text: "近 7 天欺诈趋势分析" },
  { icon: Brain, label: "为高风险地区生成临时规则", text: "为 RU/NG + 大额海外渠道组合生成临时风控规则" },
];

const WELCOME: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content: [
    "您好,我是 **支付风控 AI Agent** 👋",
    "",
    "我可以帮你完成:",
    "- 🔎 任意订单的根因分析与处置建议",
    "- 📊 跨渠道对账差异查询与凭证生成",
    "- 📈 欺诈趋势解读与策略建议",
    "- 🛠 chargeback 回复 / 风控规则 DSL 生成",
    "",
    "试试左下角的快捷指令,或直接输入你的问题 👇",
  ].join("\n"),
  timestamp: new Date().toISOString(),
};

function AgentPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function send(text?: string) {
    const content = (text ?? input).trim();
    if (!content || loading) return;

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    // Get full reply from API mock
    const fullReply = await api.chatComplete(newMessages);
    // Stream chars to simulate
    const assistantId = `a-${Date.now()}`;
    setMessages((prev) => [...prev, { id: assistantId, role: "assistant", content: "", timestamp: new Date().toISOString() }]);
    let i = 0;
    const chunkSize = 4;
    const interval = setInterval(() => {
      i += chunkSize;
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, content: fullReply.slice(0, i) } : m)),
      );
      if (i >= fullReply.length) {
        clearInterval(interval);
        setLoading(false);
      }
    }, 18);
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Sidebar */}
      <aside className="hidden lg:flex w-72 flex-col border-r border-border bg-card/40">
        <div className="p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-md bg-gradient-to-br from-primary to-[oklch(0.65_0.2_280)] flex items-center justify-center">
              <Bot className="h-4 w-4 text-primary-foreground" />
            </div>
            <div>
              <div className="text-sm font-semibold">支付风控 Agent</div>
              <div className="text-[11px] text-success inline-flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-success" /> 在线
              </div>
            </div>
          </div>
        </div>

        <div className="p-3">
          <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wide mb-2 px-1">
            快捷指令
          </div>
          <div className="space-y-1">
            {QUICK_PROMPTS.map((p) => {
              const Icon = p.icon;
              return (
                <button
                  key={p.label}
                  onClick={() => send(p.text)}
                  disabled={loading}
                  className="w-full text-left px-2.5 py-2 rounded-md hover:bg-accent transition-colors text-xs flex items-center gap-2 disabled:opacity-50"
                >
                  <Icon className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  <span className="truncate">{p.label}</span>
                </button>
              );
            })}
          </div>

          <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wide mt-5 mb-2 px-1">
            可调用能力
          </div>
          <div className="space-y-1.5 px-1">
            {[
              "查询订单 / 用户 / 商户",
              "调用风控规则引擎",
              "因果图谱推理",
              "RAG 知识库检索",
              "对账匹配 + 凭证生成",
              "支付网关 API (拦截/退款)",
            ].map((t) => (
              <div key={t} className="flex items-center gap-2 text-[11px] text-muted-foreground">
                <Sparkles className="h-2.5 w-2.5 text-primary" />
                {t}
              </div>
            ))}
          </div>
        </div>

        <div className="mt-auto p-3 border-t border-border text-[11px] text-muted-foreground">
          <div className="flex justify-between">
            <span>本会话 Token</span>
            <span className="num">{(messages.reduce((s, m) => s + m.content.length, 0) * 1.3).toFixed(0)}</span>
          </div>
          <div className="flex justify-between mt-1">
            <span>模型</span>
            <span className="font-medium text-foreground">gemini-3-flash</span>
          </div>
        </div>
      </aside>

      {/* Chat */}
      <div className="flex-1 flex flex-col min-w-0">
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 lg:px-8 py-6">
          <div className="max-w-3xl mx-auto space-y-5">
            {messages.map((m) => (
              <Message key={m.id} message={m} />
            ))}
            {loading && (
              <div className="flex items-start gap-3">
                <div className="h-7 w-7 rounded-md bg-primary/10 text-primary flex items-center justify-center shrink-0">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="flex items-center gap-1 pt-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Input */}
        <div className="border-t border-border bg-card/60 backdrop-blur p-4">
          <div className="max-w-3xl mx-auto">
            <div className="rounded-xl border border-border bg-background focus-within:ring-2 focus-within:ring-ring/40 transition-all">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
                placeholder="例如:分析订单 PAY202604000123 的根因 (Enter 发送 / Shift+Enter 换行)"
                rows={2}
                className="w-full resize-none px-4 py-3 bg-transparent text-sm focus:outline-none"
              />
              <div className="flex items-center justify-between px-3 pb-2">
                <div className="text-[11px] text-muted-foreground">
                  支持自然语言查询订单 · 对账 · 趋势 · 规则生成
                </div>
                <button
                  onClick={() => send()}
                  disabled={loading || !input.trim()}
                  className="inline-flex items-center gap-1.5 px-3 h-8 rounded-md bg-primary text-primary-foreground text-xs font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send className="h-3.5 w-3.5" /> 发送
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Message({ message }: { message: ChatMessage }) {
  if (message.role === "user") {
    return (
      <div className="flex items-start gap-3 justify-end">
        <div className="rounded-2xl rounded-tr-sm bg-primary text-primary-foreground px-4 py-2.5 text-sm max-w-[80%] whitespace-pre-wrap">
          {message.content}
        </div>
        <div className="h-7 w-7 rounded-md bg-muted text-muted-foreground flex items-center justify-center shrink-0">
          <User className="h-4 w-4" />
        </div>
      </div>
    );
  }
  return (
    <div className="flex items-start gap-3">
      <div className="h-7 w-7 rounded-md bg-primary/10 text-primary flex items-center justify-center shrink-0">
        <Bot className="h-4 w-4" />
      </div>
      <div className="flex-1 min-w-0 rounded-2xl rounded-tl-sm bg-card border border-border px-4 py-3 text-sm">
        <Markdown content={message.content} />
      </div>
    </div>
  );
}

// Lightweight markdown renderer (just enough for our mock replies)
function Markdown({ content }: { content: string }) {
  const lines = content.split("\n");
  const blocks: React.ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i]!;

    // Table block: starts with `|`
    if (line.startsWith("|") && lines[i + 1]?.startsWith("|") && lines[i + 1]!.includes("---")) {
      const headers = line.split("|").slice(1, -1).map((s) => s.trim());
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && lines[i]!.startsWith("|")) {
        rows.push(lines[i]!.split("|").slice(1, -1).map((s) => s.trim()));
        i++;
      }
      blocks.push(
        <div key={key++} className="overflow-x-auto my-2 rounded-md border border-border">
          <table className="w-full text-xs">
            <thead className="bg-muted/60 text-muted-foreground">
              <tr>
                {headers.map((h, j) => (
                  <th key={j} className="text-left px-2 py-1.5 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, j) => (
                <tr key={j} className="border-t border-border">
                  {r.map((c, k) => (
                    <td key={k} className="px-2 py-1.5 num">{renderInline(c)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }

    if (line.startsWith("- ")) {
      const items: string[] = [];
      while (i < lines.length && lines[i]!.startsWith("- ")) {
        items.push(lines[i]!.slice(2));
        i++;
      }
      blocks.push(
        <ul key={key++} className="list-disc pl-5 space-y-1 my-1.5">
          {items.map((it, j) => (
            <li key={j}>{renderInline(it)}</li>
          ))}
        </ul>,
      );
      continue;
    }

    if (line.startsWith("**") && line.endsWith("**")) {
      blocks.push(
        <div key={key++} className="font-semibold mt-2 mb-1">
          {line.slice(2, -2)}
        </div>,
      );
      i++;
      continue;
    }

    if (line.trim() === "") {
      i++;
      continue;
    }

    blocks.push(
      <p key={key++} className="leading-relaxed my-1">
        {renderInline(line)}
      </p>,
    );
    i++;
  }

  return <div className="space-y-1">{blocks}</div>;
}

function renderInline(text: string): React.ReactNode {
  // bold **x** + italic _x_
  const parts: React.ReactNode[] = [];
  const regex = /\*\*([^*]+)\*\*|_([^_]+)_|`([^`]+)`/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let key = 0;
  while ((m = regex.exec(text))) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    if (m[1]) parts.push(<strong key={key++}>{m[1]}</strong>);
    else if (m[2]) parts.push(<em key={key++} className="text-muted-foreground">{m[2]}</em>);
    else if (m[3]) parts.push(<code key={key++} className="px-1 py-0.5 rounded bg-muted text-[11px]">{m[3]}</code>);
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}
