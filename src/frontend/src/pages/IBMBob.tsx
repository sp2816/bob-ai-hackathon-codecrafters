import {
  Activity,
  Bot,
  CheckCircle2,
  Clock3,
  Send,
  ShieldCheck,
  TriangleAlert,
  Wrench,
} from "lucide-react";
import { useState } from "react";

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

const initialMessages: ChatMessage[] = [
  {
    id: 1,
    sender: "bob",
    text: "Hello. I'm IBM BOB, your mission intelligence assistant. I can help you understand fleet health, asset warnings, maintenance priorities, predictions, and mission readiness.",
  },
  {
    id: 2,
    sender: "operator",
    text: "What should I focus on right now?",
  },
  {
    id: 3,
    sender: "bob",
    text: "The highest-priority item is AS-1032. Its health index is 81% and its Engine Assembly is currently flagged for warning. I recommend reviewing its maintenance status before the next deployment.",
  },
];

function getBobResponse(question: string): string {
  const text = question.toLowerCase();

  if (
    text.includes("attention") ||
    text.includes("focus") ||
    text.includes("priority")
  ) {
    return "AS-1032 Engine Assembly should receive the highest attention. Its health index is 81% and the asset is currently flagged for warning. After that, review the upcoming maintenance window for AS-1088.";
  }

  if (
    text.includes("maintenance") ||
    text.includes("service") ||
    text.includes("repair")
  ) {
    return "The recommended maintenance priority is AS-1032 first, followed by AS-1088. AS-1032 should be inspected before its next deployment, while AS-1088 can be scheduled for its upcoming preventive service window.";
  }

  if (
    text.includes("readiness") ||
    text.includes("ready") ||
    text.includes("fleet")
  ) {
    return "Current fleet readiness is strong. Overall fleet health is approximately 92%, with mission readiness at 94%. Two assets have active warnings that should remain under observation.";
  }

  if (
    text.includes("warning") ||
    text.includes("alert") ||
    text.includes("risk")
  ) {
    return "The main warning is associated with AS-1032 Engine Assembly. Its current health index is 81%. I recommend an inspection and maintenance review before the next mission cycle.";
  }

  if (text.includes("health")) {
    return "Fleet health is currently stable at approximately 92%. AS-1032 is the primary asset requiring attention, while the remaining fleet is operating within acceptable monitoring thresholds.";
  }

  return "I can help with fleet health, asset risk, maintenance priorities, mission readiness, and active warnings. Try one of the suggested questions below.";
}

function IBMBob() {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState("");

  const sendMessage = (value?: string) => {
    const question = (value ?? input).trim();

    if (!question) {
      return;
    }

    const operatorMessage: ChatMessage = {
      id: Date.now(),
      sender: "operator",
      text: question,
    };

    const bobMessage: ChatMessage = {
      id: Date.now() + 1,
      sender: "bob",
      text: getBobResponse(question),
    };

    setMessages((currentMessages) => [
      ...currentMessages,
      operatorMessage,
      bobMessage,
    ]);

    setInput("");
  };

  return (
    <div className="space-y-7">
      {/* PAGE HEADER */}
      <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="eyebrow">Mission Intelligence</p>

          <h1 className="mt-2 text-[42px] font-semibold leading-none tracking-[-0.055em] text-[#3B2A20] sm:text-[48px]">
            IBM BOB
          </h1>

          <p className="mt-3 max-w-xl text-[13px] leading-6 text-[#806B59]">
            Your operational intelligence assistant for fleet health,
            maintenance, predictions, and mission readiness.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="rounded-full border border-[#D8CBB9] bg-[#EEE5D7] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#806B59]">
            AI Assistant
          </span>

          <span className="flex items-center gap-2 rounded-full border border-[#C2CEAE] bg-[#DDE5D1] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#596842]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#69784F]" />
            Online
          </span>
        </div>
      </section>

      {/* MAIN AREA */}
      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_330px]">
        {/* CHAT PANEL */}
        <article className="flex min-h-[620px] flex-col overflow-hidden rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          {/* CHAT HEADER */}
          <div className="flex items-center justify-between border-b border-[#E8DED1] px-6 py-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#69784F] text-[#FBF8F2]">
                <Bot className="h-5 w-5" strokeWidth={1.6} />
              </div>

              <div>
                <p className="text-[13px] font-semibold text-[#4A3528]">
                  IBM BOB
                </p>

                <p className="mt-1 text-[9px] uppercase tracking-[0.12em] text-[#9B8977]">
                  Fleet Intelligence Assistant
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-[#69784F]" />

              <span className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#69784F]">
                Ready
              </span>
            </div>
          </div>

          {/* CHAT MESSAGES */}
          <div className="flex-1 space-y-6 overflow-y-auto px-6 py-7 sm:px-8">
            {messages.map((chatMessage) => {
              const isOperator = chatMessage.sender === "operator";

              return (
                <div
                  key={chatMessage.id}
                  className={`flex ${
                    isOperator ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`flex max-w-[760px] gap-3 ${
                      isOperator ? "flex-row-reverse" : "flex-row"
                    }`}
                  >
                    {/* AVATAR */}
                    <div
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                        isOperator
                          ? "bg-[#E2D7C7] text-[#806B59]"
                          : "bg-[#E0E7D6] text-[#69784F]"
                      }`}
                    >
                      {isOperator ? (
                        <span className="text-[9px] font-semibold">OP</span>
                      ) : (
                        <Bot className="h-4 w-4" strokeWidth={1.6} />
                      )}
                    </div>

                    {/* MESSAGE */}
                    <div
                      className={`rounded-2xl px-5 py-4 ${
                        isOperator
                          ? "rounded-tr-md bg-[#69784F] text-[#FBF8F2]"
                          : "rounded-tl-md border border-[#DED2C0] bg-[#F4ECE1]"
                      }`}
                    >
                      <p
                        className={`text-[12px] leading-6 ${
                          isOperator
                            ? "text-[#FBF8F2]"
                            : "text-[#5D4535]"
                        }`}
                      >
                        {chatMessage.text}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}

            {/* SYSTEM INSIGHT */}
            <div className="ml-0 rounded-xl border border-[#C8D2B7] bg-[#E8EDDF] p-4 sm:ml-11">
              <div className="flex items-start gap-3">
                <ShieldCheck
                  className="mt-0.5 h-4 w-4 shrink-0 text-[#69784F]"
                  strokeWidth={1.6}
                />

                <div>
                  <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#596842]">
                    Current system insight
                  </p>

                  <p className="mt-2 text-[11px] leading-5 text-[#69784F]">
                    Fleet health is currently stable. One asset requires
                    attention and one asset remains under preventive
                    monitoring.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* SUGGESTIONS */}
          <div className="border-t border-[#E8DED1] px-6 py-4">
            <p className="mb-3 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
              Suggested questions
            </p>

            <div className="flex flex-wrap gap-2">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => sendMessage(suggestion)}
                  className="rounded-full border border-[#D8CBB9] bg-[#F4ECE1] px-3 py-2 text-[9px] font-medium text-[#806B59] transition-colors hover:bg-[#EDE2D2] hover:text-[#4A3528]"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>

          {/* INPUT */}
          <div className="border-t border-[#E8DED1] bg-[#F7F1E7] p-4">
            <form
              onSubmit={(event) => {
                event.preventDefault();
                sendMessage();
              }}
              className="flex items-center gap-3 rounded-xl border border-[#D8CBB9] bg-[#FBF8F2] px-4 py-2"
            >
              <input
                type="text"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ask IBM BOB about your fleet..."
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

        {/* RIGHT INTELLIGENCE PANEL */}
        <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-start justify-between border-b border-[#E8DED1] px-6 py-5">
            <div>
              <p className="eyebrow">Intelligence</p>

              <h2 className="mt-2 text-[21px] font-semibold tracking-[-0.025em] text-[#4A3528]">
                System context
              </h2>
            </div>

            <Activity
              className="h-5 w-5 text-[#806B59]"
              strokeWidth={1.5}
            />
          </div>

          <div>
            {/* FLEET HEALTH */}
            <div className="border-b border-[#E8DED1] px-6 py-5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#806B59]">
                  Fleet health
                </span>

                <span className="text-[13px] font-semibold text-[#69784F]">
                  92%
                </span>
              </div>

              <div className="soft-progress mt-3">
                <div
                  className="moss-progress"
                  style={{ width: "92%" }}
                />
              </div>
            </div>

            {/* READINESS */}
            <div className="border-b border-[#E8DED1] px-6 py-5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#806B59]">
                  Mission readiness
                </span>

                <span className="text-[13px] font-semibold text-[#69784F]">
                  94%
                </span>
              </div>

              <div className="soft-progress mt-3">
                <div
                  className="moss-progress"
                  style={{ width: "94%" }}
                />
              </div>
            </div>

            {/* ACTIVE ALERTS */}
            <div className="border-b border-[#E8DED1] px-6 py-5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#806B59]">
                  Active alerts
                </span>

                <span className="text-[13px] font-semibold text-[#B95F46]">
                  2
                </span>
              </div>

              <p className="mt-2 text-[9px] text-[#A39484]">
                No critical fleet-wide alerts
              </p>
            </div>

            {/* EVIDENCE */}
            <div className="px-6 py-5">
              <div className="flex items-center gap-3">
                <CheckCircle2
                  className="h-4 w-4 text-[#69784F]"
                  strokeWidth={1.6}
                />

                <div>
                  <p className="text-[10px] font-semibold text-[#4A3528]">
                    Evidence layer active
                  </p>

                  <p className="mt-1 text-[9px] leading-4 text-[#9B8977]">
                    Recommendations remain traceable to fleet data.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </article>
      </section>

      {/* BOTTOM STATUS */}
      <section className="grid overflow-hidden rounded-2xl border border-[#DED2C0] bg-[#EEE5D7] sm:grid-cols-3">
        <div className="flex items-center gap-3 border-b border-[#DED2C0] px-5 py-4 sm:border-b-0 sm:border-r">
          <Bot
            className="h-5 w-5 text-[#69784F]"
            strokeWidth={1.5}
          />

          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#6F5B4A]">
              AI Assistant
            </p>

            <p className="mt-1 text-[10px] text-[#978575]">
              IBM BOB is ready
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 border-b border-[#DED2C0] px-5 py-4 sm:border-b-0 sm:border-r">
          <Activity
            className="h-5 w-5 text-[#69784F]"
            strokeWidth={1.5}
          />

          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#6F5B4A]">
              Fleet Data
            </p>

            <p className="mt-1 text-[10px] text-[#978575]">
              Operational context available
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 px-5 py-4">
          <ShieldCheck
            className="h-5 w-5 text-[#69784F]"
            strokeWidth={1.5}
          />

          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#6F5B4A]">
              Evidence
            </p>

            <p className="mt-1 text-[10px] text-[#978575]">
              Recommendations remain traceable
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default IBMBob;