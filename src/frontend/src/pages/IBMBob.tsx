import {
  Activity,
  Bot,
  CheckCircle2,
  RefreshCw,
  Send,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  getFleetReadinessSummary,
  getMaintenanceRecommendations,
  getMissionReadiness,
  sendChatMessage,
} from "../services/api";
import type { ApiFleetSummary, ApiMaintenanceRecommendation, ApiReadinessResult } from "../types/api";

interface ChatMessage {
  id: number;
  sender: "bob" | "operator";
  text: string;
}

const suggestions = [
  "Which assets need attention?",
  "Show today's maintenance priorities",
  "What is the current fleet readiness?",
  "Explain the latest warning",
];


function IBMBob() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      sender: "bob",
      text: "Hello. I'm IBM BOB, your mission intelligence assistant. I explain fleet health, asset warnings, maintenance priorities, predictions, and mission readiness based on the AssetSentinel backend.",
    },
  ]);
  const [input, setInput] = useState("");
  const [summary, setSummary] = useState<ApiFleetSummary | null>(null);
  const [recs, setRecs] = useState<ApiMaintenanceRecommendation[]>([]);
  const [msnResults, setMsnResults] = useState<ApiReadinessResult[]>([]);
  const [contextLoading, setContextLoading] = useState(true);
  const endRef = useRef<HTMLDivElement>(null);

  const fetchContext = async () => {
    setContextLoading(true);
    try {
      const [fleetSummary, maintenance, msn001, msn002, msn003] = await Promise.allSettled([
        getFleetReadinessSummary(),
        getMaintenanceRecommendations(),
        getMissionReadiness("MSN-001"),
        getMissionReadiness("MSN-002"),
        getMissionReadiness("MSN-003"),
      ]);

      if (fleetSummary.status === "fulfilled") setSummary(fleetSummary.value);
      if (maintenance.status === "fulfilled") setRecs(maintenance.value);

      const allMsn: ApiReadinessResult[] = [];
      for (const r of [msn001, msn002, msn003]) {
        if (r.status === "fulfilled") allMsn.push(...r.value);
      }
      setMsnResults(allMsn);
    } finally {
      setContextLoading(false);
    }
  };

  useEffect(() => { fetchContext(); }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (value?: string) => {
    const question = (value ?? input).trim();
    if (!question) return;

    setMessages((prev) => [
      ...prev,
      { id: Date.now(), sender: "operator", text: question },
    ]);
    setInput("");

    try {
      const { response } = await sendChatMessage(question);
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, sender: "bob", text: response },
      ]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, sender: "bob", text: "Error: Unable to reach the backend chat service." },
      ]);
    }
  };

  const readyCount    = summary?.counts.READY ?? 0;
  const notReadyCount = summary?.counts.NOT_READY ?? 0;
  const total         = summary?.total ?? 0;
  const fleetHealthPct = total > 0 ? Math.round((readyCount / total) * 100) : 0;
  const highRecs      = recs.filter((r) => r.urgency === "HIGH").length;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <section className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <p className="eyebrow">Mission Intelligence</p>
          <h1 className="page-title mt-2 flex items-center gap-3">
            <span>IBM BOB</span>
            <span
              className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold"
              style={{
                background: "linear-gradient(135deg, color-mix(in srgb, var(--brand-500) 15%, transparent), color-mix(in srgb, var(--brand-500) 8%, transparent))",
                border: "1px solid color-mix(in srgb, var(--brand-500) 30%, transparent)",
                color: "var(--text-brand)",
              }}
            >
              <Sparkles className="h-3.5 w-3.5" />
              AI Copilot
            </span>
          </h1>
          <p className="body-text mt-2 max-w-xl">
            Your operational intelligence assistant — explains backend-computed fleet health,
            maintenance, predictions, and mission readiness.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={fetchContext}
            disabled={contextLoading}
            className="btn-secondary-sm"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            {contextLoading ? "Loading…" : "Refresh context"}
          </button>
          <span
            className="inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold"
            style={{
              backgroundColor: "var(--success-bg)",
              border: "1px solid var(--success-border)",
              color: "var(--success-text)",
            }}
          >
            <span className="pulse-online" />
            {contextLoading ? "Loading" : "Online"}
          </span>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_300px]">

        {/* ── Chat panel ───────────────────────────────────────── */}
        <article
          className="flex min-h-[620px] flex-col overflow-hidden rounded-xl"
          style={{
            backgroundColor: "var(--surface-card)",
            border: "1px solid var(--border-default)",
            boxShadow: "var(--chat-panel-shadow)",
          }}
        >
          {/* Chat header */}
          <div
            className="flex items-center justify-between px-6 py-4"
            style={{
              borderBottom: "1px solid var(--border-default)",
              background: "linear-gradient(135deg, color-mix(in srgb, var(--brand-500) 8%, transparent) 0%, transparent 60%)",
            }}
          >
            <div className="flex items-center gap-3">
              <div
                className="flex h-10 w-10 items-center justify-center rounded-xl"
                style={{
                  background: "linear-gradient(135deg, var(--brand-700), var(--brand-500))",
                  boxShadow: "0 0 16px rgba(175,23,99,0.35)",
                }}
              >
                <Bot className="h-5 w-5 text-white" strokeWidth={1.7} />
              </div>
              <div>
                <p className="text-[14px] font-bold" style={{ color: "var(--text-primary)" }}>IBM BOB</p>
                <p className="mt-0.5 text-[10px] font-semibold uppercase tracking-[0.14em]" style={{ color: "var(--text-muted)" }}>
                  Fleet Intelligence Assistant
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="status-dot-ready" />
              <span className="text-[11px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--success-text)" }}>
                Ready
              </span>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 space-y-5 overflow-y-auto px-6 py-6">
            {messages.map((msg) => {
              const isOperator = msg.sender === "operator";
              return (
                <div key={msg.id} className={`flex ${isOperator ? "justify-end" : "justify-start"}`}>
                  <div className={`flex max-w-[760px] gap-3 ${isOperator ? "flex-row-reverse" : "flex-row"}`}>
                    {/* Avatar */}
                    <div
                      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[9px] font-bold"
                      style={
                        isOperator
                          ? { backgroundColor: "var(--surface-elevated)", color: "var(--text-secondary)", border: "1px solid var(--border-default)" }
                          : {
                              background: "linear-gradient(135deg, var(--brand-700), var(--brand-500))",
                              color: "#fff",
                              boxShadow: "0 0 10px rgba(175,23,99,0.3)",
                            }
                      }
                    >
                      {isOperator ? (
                        <span>OP</span>
                      ) : (
                        <Bot className="h-4 w-4" strokeWidth={1.7} />
                      )}
                    </div>

                    {/* Bubble */}
                    <div
                      className="rounded-2xl px-5 py-3.5"
                      style={
                        isOperator
                          ? {
                              background: "linear-gradient(135deg, var(--brand-700), var(--brand-600))",
                              color: "#fff",
                              borderTopRightRadius: "4px",
                            }
                          : {
                              backgroundColor: "var(--surface-elevated)",
                              border: "1px solid var(--border-default)",
                              color: "var(--text-primary)",
                              borderTopLeftRadius: "4px",
                              borderLeft: "2px solid var(--brand-500)",
                            }
                      }
                    >
                      <p
                        className="whitespace-pre-line text-[13px] leading-6"
                        style={{ color: isOperator ? "#fff" : "var(--text-primary)" }}
                      >
                        {msg.text}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}

            {/* Live system insight */}
            <div
              className="rounded-xl p-4"
              style={{
                background: "color-mix(in srgb, var(--brand-500) 6%, var(--surface-card))",
                border: "1px solid color-mix(in srgb, var(--brand-500) 20%, transparent)",
              }}
            >
              <div className="flex items-start gap-3">
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" style={{ color: "var(--text-brand)" }} strokeWidth={1.7} />
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.12em]" style={{ color: "var(--text-brand)" }}>
                    Live System Insight
                  </p>
                  <p className="mt-1.5 text-[12px] leading-5" style={{ color: "var(--text-secondary)" }}>
                    {contextLoading
                      ? "Loading fleet context…"
                      : summary
                      ? `Fleet: ${readyCount}/${total} READY · ${notReadyCount} NOT READY · ${highRecs} high-urgency maintenance item(s).`
                      : "Backend context unavailable. Refresh context to reconnect."}
                  </p>
                </div>
              </div>
            </div>

            <div ref={endRef} />
          </div>

          {/* Suggestions */}
          <div
            className="px-6 py-3"
            style={{ borderTop: "1px solid var(--border-default)" }}
          >
            <p className="mb-2.5 text-[10px] font-semibold uppercase tracking-[0.12em]" style={{ color: "var(--text-muted)" }}>
              Suggested questions
            </p>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => sendMessage(s)}
                  className="rounded-lg px-3 py-1.5 text-[12px] font-medium transition-all duration-150"
                  style={{
                    backgroundColor: "var(--surface-elevated)",
                    border: "1px solid var(--border-default)",
                    color: "var(--text-secondary)",
                  }}
                  onMouseEnter={(e) => {
                    (e.currentTarget as HTMLElement).style.backgroundColor = "rgba(175,23,99,0.1)";
                    (e.currentTarget as HTMLElement).style.borderColor = "rgba(175,23,99,0.3)";
                    (e.currentTarget as HTMLElement).style.color = "var(--text-brand)";
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLElement).style.backgroundColor = "var(--surface-elevated)";
                    (e.currentTarget as HTMLElement).style.borderColor = "var(--border-default)";
                    (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)";
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Input */}
          <div className="p-4" style={{ borderTop: "1px solid var(--border-default)", backgroundColor: "var(--surface-base)" }}>
            <form
              onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
              className="flex items-center gap-3 rounded-xl px-4 py-2.5"
              style={{
                backgroundColor: "var(--surface-card)",
                border: "1px solid var(--border-default)",
              }}
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask IBM BOB about your fleet…"
                className="min-w-0 flex-1 bg-transparent text-[13px] outline-none"
                style={{
                  color: "var(--text-primary)",
                }}
              />
              <button
                type="submit"
                disabled={!input.trim()}
                aria-label="Send message"
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-40"
                style={{
                  background: "linear-gradient(135deg, var(--brand-700), var(--brand-500))",
                }}
              >
                <Send className="h-4 w-4" strokeWidth={1.8} />
              </button>
            </form>
          </div>
        </article>

        {/* ── Intelligence sidebar ─────────────────────────────── */}
        <article className="card rounded-xl overflow-hidden">
          <div
            className="px-5 py-4"
            style={{
              borderBottom: "1px solid var(--border-default)",
              background: "linear-gradient(135deg, color-mix(in srgb, var(--brand-500) 8%, transparent) 0%, transparent 60%)",
            }}
          >
            <p className="eyebrow">Intelligence</p>
            <h2 className="section-title mt-1">System Context</h2>
          </div>

          {/* Fleet health */}
          <div className="px-5 py-4" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
            <div className="flex items-center justify-between">
              <span className="data-label">Fleet health</span>
              <span className="text-[15px] font-bold" style={{ color: "var(--success-text)" }}>
                {contextLoading ? "…" : `${fleetHealthPct}%`}
              </span>
            </div>
            <div className="progress-track mt-2">
              <div className="progress-fill-success" style={{ width: `${Math.max(fleetHealthPct, 2)}%` }} />
            </div>
          </div>

          {/* READY assets */}
          <div className="px-5 py-4" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" style={{ color: "var(--success-text)" }} strokeWidth={1.7} />
                <span className="data-label">READY assets</span>
              </div>
              <span className="text-[15px] font-bold" style={{ color: "var(--success-text)" }}>
                {contextLoading ? "…" : `${readyCount} / ${total}`}
              </span>
            </div>
            <div className="progress-track mt-2">
              <div className="progress-fill-success" style={{ width: `${Math.max(fleetHealthPct, 2)}%` }} />
            </div>
          </div>

          {/* NOT READY */}
          <div className="px-5 py-4" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TriangleAlert className="h-4 w-4" style={{ color: "var(--danger-text)" }} strokeWidth={1.7} />
                <span className="data-label">NOT READY</span>
              </div>
              <span className="text-[15px] font-bold" style={{ color: "var(--danger-text)" }}>
                {contextLoading ? "…" : notReadyCount}
              </span>
            </div>
            {!contextLoading && notReadyCount === 0 && (
              <p className="mt-1.5 text-[11px]" style={{ color: "var(--text-muted)" }}>
                No assets flagged NOT_READY
              </p>
            )}
          </div>

          {/* Maintenance queue */}
          <div className="px-5 py-4" style={{ borderBottom: "1px solid var(--border-subtle)" }}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4" style={{ color: "var(--warning-text)" }} strokeWidth={1.7} />
                <span className="data-label">Maintenance queue</span>
              </div>
              <span className="text-[15px] font-bold" style={{ color: "var(--warning-text)" }}>
                {contextLoading ? "…" : recs.length}
              </span>
            </div>
            {!contextLoading && highRecs > 0 && (
              <div className="mt-1.5 flex items-center gap-1.5">
                <TriangleAlert className="h-3 w-3" style={{ color: "var(--danger-text)" }} strokeWidth={1.8} />
                <p className="text-[11px] font-semibold" style={{ color: "var(--danger-text)" }}>
                  {highRecs} HIGH urgency
                </p>
              </div>
            )}
          </div>

          {/* Evidence */}
          <div className="px-5 py-4">
            <div className="flex items-start gap-3">
              <div className="icon-container-brand h-8 w-8 shrink-0">
                <ShieldCheck className="h-4 w-4" strokeWidth={1.7} />
              </div>
              <div>
                <p className="text-[12px] font-semibold" style={{ color: "var(--text-primary)" }}>
                  Evidence layer active
                </p>
                <p className="mt-1 text-[11px] leading-4" style={{ color: "var(--text-muted)" }}>
                  All responses trace to backend-computed evidence.
                </p>
              </div>
            </div>
          </div>
        </article>
      </section>

      {/* Status footer */}
      <section
        className="grid overflow-hidden rounded-xl sm:grid-cols-3"
        style={{ backgroundColor: "var(--surface-card)", border: "1px solid var(--border-default)" }}
      >
        <div className="flex items-center gap-3 px-5 py-4" style={{ borderRight: "1px solid var(--border-default)" }}>
          <div className="icon-container-brand h-9 w-9">
            <Bot className="h-4 w-4" strokeWidth={1.8} />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>AI Assistant</p>
            <p className="mt-0.5 text-sm font-medium" style={{ color: "var(--text-primary)" }}>IBM BOB is ready</p>
          </div>
        </div>
        <div className="flex items-center gap-3 border-b px-5 py-4 sm:border-b-0 sm:border-r" style={{ borderColor: "var(--border-default)" }}>
          <div className="icon-container-success h-9 w-9">
            <Activity className="h-4 w-4" strokeWidth={1.8} />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>Fleet Data</p>
            <p className="mt-0.5 text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              {contextLoading ? "Loading…" : "Backend context loaded"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 px-5 py-4">
          <div className="icon-container-info h-9 w-9">
            <ShieldCheck className="h-4 w-4" strokeWidth={1.8} />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>Evidence</p>
            <p className="mt-0.5 text-sm font-medium" style={{ color: "var(--text-primary)" }}>Recommendations traceable</p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default IBMBob;