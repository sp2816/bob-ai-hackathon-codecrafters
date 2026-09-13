import {
  Activity,
  Bot,
  CheckCircle2,
  RefreshCw,
  Send,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  getFleetReadinessSummary,
  getMaintenanceRecommendations,
  getMissionReadiness,
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

/**
 * Build a context-aware response from real backend data.
 * IBM BOB explains backend-computed results — it does not calculate anything itself.
 */
function buildBobResponse(
  question: string,
  summary: ApiFleetSummary | null,
  recs: ApiMaintenanceRecommendation[],
  msnResults: ApiReadinessResult[],
): string {
  const text = question.toLowerCase();

  if (!summary) {
    return "I cannot access the fleet backend at the moment. Please ensure the backend is running and try refreshing.";
  }

  const { total, counts } = summary;

  if (text.includes("readiness") || text.includes("ready") || text.includes("fleet")) {
    const readyPct = total > 0 ? Math.round((counts.READY / total) * 100) : 0;
    const notReadyAssets = msnResults
      .filter((r) => r.readiness_status === "NOT_READY")
      .map((r) => r.asset_id);
    const unique = [...new Set(notReadyAssets)];
    return (
      `Current fleet readiness: ${counts.READY} of ${total} assets are READY (${readyPct}%). ` +
      `${counts.NOT_READY} asset(s) are NOT_READY. ` +
      (unique.length > 0
        ? `Assets flagged NOT_READY: ${unique.join(", ")}. `
        : "") +
      `${counts.CONDITIONALLY_READY} asset(s) are conditionally ready.`
    );
  }

  if (text.includes("attention") || text.includes("focus") || text.includes("priority")) {
    if (recs.length === 0) {
      return "No maintenance recommendations are currently queued. Run the readiness pipeline to generate fresh recommendations.";
    }
    const top = recs.slice(0, 3);
    const parts = top.map(
      (r) => `${r.asset_id} / ${r.component_id} — ${r.action} (urgency: ${r.urgency})`,
    );
    return (
      `Top ${top.length} maintenance priority item(s) from the Maintenance Priority Engine:\n` +
      parts.join("\n")
    );
  }

  if (text.includes("maintenance") || text.includes("service") || text.includes("repair")) {
    if (recs.length === 0) {
      return "No maintenance recommendations are currently in the queue. Click 'Run Readiness' to refresh.";
    }
    const high = recs.filter((r) => r.urgency === "HIGH");
    return (
      `There are ${recs.length} recommendation(s) in the maintenance queue. ` +
      `${high.length} are HIGH urgency. ` +
      (high.length > 0
        ? `Top action: ${high[0].action} for ${high[0].asset_id}.`
        : "All items are medium or low urgency.")
    );
  }

  if (text.includes("warning") || text.includes("alert") || text.includes("risk")) {
    const notReady = counts.NOT_READY;
    if (notReady === 0) {
      return "No assets are currently flagged as NOT_READY. The fleet is operating within acceptable thresholds.";
    }
    const topRec = recs.find((r) => r.urgency === "HIGH");
    return (
      `${notReady} asset(s) are currently NOT_READY. ` +
      (topRec
        ? `Highest priority action: ${topRec.action} for ${topRec.asset_id} / ${topRec.component_id}.`
        : "Check the Maintenance page for prioritised recommendations.")
    );
  }

  if (text.includes("health")) {
    const readyPct = total > 0 ? Math.round((counts.READY / total) * 100) : 0;
    return (
      `Fleet health: ${readyPct}% of assets (${counts.READY}/${total}) are READY. ` +
      `${counts.NOT_READY} are NOT_READY and ${counts.CONDITIONALLY_READY} are conditionally ready.`
    );
  }

  return (
    "I can help explain fleet health, asset risk, maintenance priorities, mission readiness, and active warnings. " +
    "My responses are derived from the AssetSentinel backend — I do not independently calculate readiness or failure risk. " +
    "Try one of the suggested questions below."
  );
}

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

  useEffect(() => {
    fetchContext();
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = (value?: string) => {
    const question = (value ?? input).trim();
    if (!question) return;

    const response = buildBobResponse(question, summary, recs, msnResults);

    setMessages((prev) => [
      ...prev,
      { id: Date.now(), sender: "operator", text: question },
      { id: Date.now() + 1, sender: "bob", text: response },
    ]);
    setInput("");
  };

  const readyCount = summary?.counts.READY ?? 0;
  const notReadyCount = summary?.counts.NOT_READY ?? 0;
  const total = summary?.total ?? 0;
  const fleetHealthPct = total > 0 ? Math.round((readyCount / total) * 100) : 0;
  const highRecs = recs.filter((r) => r.urgency === "HIGH").length;

  return (
    <div className="space-y-7">
      <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="eyebrow">Mission Intelligence</p>
          <h1 className="mt-2 text-[42px] font-semibold leading-none tracking-[-0.055em] text-[#3B2A20] sm:text-[48px]">
            IBM BOB
          </h1>
          <p className="mt-3 max-w-xl text-[13px] leading-6 text-[#806B59]">
            Your operational intelligence assistant — explains backend-computed fleet health,
            maintenance, predictions, and mission readiness.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={fetchContext}
            disabled={contextLoading}
            className="flex items-center gap-1.5 rounded-full border border-[#D8CBB9] bg-[#EEE5D7] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#806B59] hover:bg-[#E5D8C5] disabled:opacity-50"
          >
            <RefreshCw className="h-3 w-3" />
            {contextLoading ? "Loading…" : "Refresh context"}
          </button>
          <span className="flex items-center gap-2 rounded-full border border-[#C2CEAE] bg-[#DDE5D1] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#596842]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#69784F]" />
            {contextLoading ? "Loading" : "Online"}
          </span>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_330px]">
        {/* Chat panel */}
        <article className="flex min-h-[620px] flex-col overflow-hidden rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-center justify-between border-b border-[#E8DED1] px-6 py-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#69784F] text-[#FBF8F2]">
                <Bot className="h-5 w-5" strokeWidth={1.6} />
              </div>
              <div>
                <p className="text-[13px] font-semibold text-[#4A3528]">IBM BOB</p>
                <p className="mt-1 text-[9px] uppercase tracking-[0.12em] text-[#9B8977]">
                  Fleet Intelligence Assistant
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-[#69784F]" />
              <span className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#69784F]">Ready</span>
            </div>
          </div>

          <div className="flex-1 space-y-6 overflow-y-auto px-6 py-7 sm:px-8">
            {messages.map((msg) => {
              const isOperator = msg.sender === "operator";
              return (
                <div key={msg.id} className={`flex ${isOperator ? "justify-end" : "justify-start"}`}>
                  <div className={`flex max-w-[760px] gap-3 ${isOperator ? "flex-row-reverse" : "flex-row"}`}>
                    <div
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                        isOperator ? "bg-[#E2D7C7] text-[#806B59]" : "bg-[#E0E7D6] text-[#69784F]"
                      }`}
                    >
                      {isOperator ? (
                        <span className="text-[9px] font-semibold">OP</span>
                      ) : (
                        <Bot className="h-4 w-4" strokeWidth={1.6} />
                      )}
                    </div>
                    <div
                      className={`rounded-2xl px-5 py-4 ${
                        isOperator
                          ? "rounded-tr-md bg-[#69784F] text-[#FBF8F2]"
                          : "rounded-tl-md border border-[#DED2C0] bg-[#F4ECE1]"
                      }`}
                    >
                      <p
                        className={`whitespace-pre-line text-[12px] leading-6 ${
                          isOperator ? "text-[#FBF8F2]" : "text-[#5D4535]"
                        }`}
                      >
                        {msg.text}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}

            {/* Live system insight */}
            <div className="ml-0 rounded-xl border border-[#C8D2B7] bg-[#E8EDDF] p-4 sm:ml-11">
              <div className="flex items-start gap-3">
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-[#69784F]" strokeWidth={1.6} />
                <div>
                  <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#596842]">
                    Current system insight
                  </p>
                  <p className="mt-2 text-[11px] leading-5 text-[#69784F]">
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
          <div className="border-t border-[#E8DED1] px-6 py-4">
            <p className="mb-3 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
              Suggested questions
            </p>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => sendMessage(s)}
                  className="rounded-full border border-[#D8CBB9] bg-[#F4ECE1] px-3 py-2 text-[9px] font-medium text-[#806B59] transition-colors hover:bg-[#EDE2D2] hover:text-[#4A3528]"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Input */}
          <div className="border-t border-[#E8DED1] bg-[#F7F1E7] p-4">
            <form
              onSubmit={(e) => { e.preventDefault(); sendMessage(); }}
              className="flex items-center gap-3 rounded-xl border border-[#D8CBB9] bg-[#FBF8F2] px-4 py-2"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask IBM BOB about your fleet…"
                className="min-w-0 flex-1 bg-transparent py-2 text-[12px] text-[#4A3528] outline-none placeholder:text-[#A39484]"
              />
              <button
                type="submit"
                disabled={!input.trim()}
                aria-label="Send message"
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#69784F] text-[#FBF8F2] transition-opacity disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Send className="h-4 w-4" strokeWidth={1.7} />
              </button>
            </form>
          </div>
        </article>

        {/* Right intelligence panel — backend data */}
        <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-start justify-between border-b border-[#E8DED1] px-6 py-5">
            <div>
              <p className="eyebrow">Intelligence</p>
              <h2 className="mt-2 text-[21px] font-semibold tracking-[-0.025em] text-[#4A3528]">
                System context
              </h2>
            </div>
            <Activity className="h-5 w-5 text-[#806B59]" strokeWidth={1.5} />
          </div>

          <div>
            {/* Fleet health */}
            <div className="border-b border-[#E8DED1] px-6 py-5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#806B59]">Fleet health</span>
                <span className="text-[13px] font-semibold text-[#69784F]">
                  {contextLoading ? "…" : `${fleetHealthPct}%`}
                </span>
              </div>
              <div className="soft-progress mt-3">
                <div className="moss-progress" style={{ width: `${Math.max(fleetHealthPct, 3)}%` }} />
              </div>
            </div>

            {/* Readiness */}
            <div className="border-b border-[#E8DED1] px-6 py-5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#806B59]">READY assets</span>
                <span className="text-[13px] font-semibold text-[#69784F]">
                  {contextLoading ? "…" : `${readyCount} / ${total}`}
                </span>
              </div>
              <div className="soft-progress mt-3">
                <div className="moss-progress" style={{ width: `${Math.max(fleetHealthPct, 3)}%` }} />
              </div>
            </div>

            {/* Alerts */}
            <div className="border-b border-[#E8DED1] px-6 py-5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#806B59]">NOT READY</span>
                <span className="text-[13px] font-semibold text-[#B95F46]">
                  {contextLoading ? "…" : notReadyCount}
                </span>
              </div>
              {!contextLoading && notReadyCount === 0 && (
                <p className="mt-2 text-[9px] text-[#A39484]">No assets flagged NOT_READY</p>
              )}
            </div>

            {/* Maintenance */}
            <div className="border-b border-[#E8DED1] px-6 py-5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#806B59]">Maintenance queue</span>
                <span className="text-[13px] font-semibold text-[#9A7650]">
                  {contextLoading ? "…" : recs.length}
                </span>
              </div>
              {!contextLoading && highRecs > 0 && (
                <div className="mt-2 flex items-center gap-1.5">
                  <TriangleAlert className="h-3 w-3 text-[#B95F46]" strokeWidth={1.7} />
                  <p className="text-[9px] text-[#B95F46]">{highRecs} HIGH urgency</p>
                </div>
              )}
            </div>

            {/* Evidence */}
            <div className="px-6 py-5">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="h-4 w-4 text-[#69784F]" strokeWidth={1.6} />
                <div>
                  <p className="text-[10px] font-semibold text-[#4A3528]">Evidence layer active</p>
                  <p className="mt-1 text-[9px] leading-4 text-[#9B8977]">
                    All responses trace to backend-computed evidence.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </article>
      </section>

      <section className="grid overflow-hidden rounded-2xl border border-[#DED2C0] bg-[#EEE5D7] sm:grid-cols-3">
        <div className="flex items-center gap-3 border-b border-[#DED2C0] px-5 py-4 sm:border-b-0 sm:border-r">
          <Bot className="h-5 w-5 text-[#69784F]" strokeWidth={1.5} />
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#6F5B4A]">AI Assistant</p>
            <p className="mt-1 text-[10px] text-[#978575]">IBM BOB is ready</p>
          </div>
        </div>
        <div className="flex items-center gap-3 border-b border-[#DED2C0] px-5 py-4 sm:border-b-0 sm:border-r">
          <Activity className="h-5 w-5 text-[#69784F]" strokeWidth={1.5} />
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#6F5B4A]">Fleet Data</p>
            <p className="mt-1 text-[10px] text-[#978575]">
              {contextLoading ? "Loading…" : "Backend context loaded"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 px-5 py-4">
          <ShieldCheck className="h-5 w-5 text-[#69784F]" strokeWidth={1.5} />
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#6F5B4A]">Evidence</p>
            <p className="mt-1 text-[10px] text-[#978575]">Recommendations remain traceable</p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default IBMBob;