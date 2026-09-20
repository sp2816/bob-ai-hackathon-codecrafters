import {
  Activity,
  Bot,
  CheckCircle2,
  MessageSquare,
  MoreVertical,
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

interface Conversation {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: ChatMessage[];
}

const suggestions = [
  "Which assets need attention?",
  "Show today's maintenance priorities",
  "What is the potential cost avoided by using AssetSentinel?",
  "Explain the latest warning",
];

function IBMBob() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [isInitialized, setIsInitialized] = useState(false);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameTitle, setRenameTitle] = useState("");
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const [summary, setSummary] = useState<ApiFleetSummary | null>(null);
  const [recs, setRecs] = useState<ApiMaintenanceRecommendation[]>([]);
  const [msnResults, setMsnResults] = useState<ApiReadinessResult[]>([]);
  const [contextLoading, setContextLoading] = useState(true);
  const endRef = useRef<HTMLDivElement>(null);

  // Load from localStorage on mount and deduplicate
  useEffect(() => {
    if (isInitialized) return;
    
    const savedConvos = localStorage.getItem("ibm_bob_chat_history");
    const savedActiveId = localStorage.getItem("ibm_bob_active_chat_id");

    let parsedConvos: Conversation[] = [];
    if (savedConvos) {
      try {
        const parsed = JSON.parse(savedConvos);
        if (Array.isArray(parsed)) {
          const unique = [];
          const seen = new Set();
          for (const c of parsed) {
            if (!seen.has(c.id)) {
              seen.add(c.id);
              unique.push(c);
            }
          }
          parsedConvos = unique;
        }
      } catch (e) {
        console.error("Failed to parse chat history");
      }
    }

    if (parsedConvos.length > 0) {
      setConversations(parsedConvos);
      if (savedActiveId && parsedConvos.some(c => c.id === savedActiveId)) {
        setActiveId(savedActiveId);
      } else {
        setActiveId(parsedConvos[0].id);
      }
    } else {
      const newId = Date.now().toString();
      setConversations([{
        id: newId,
        title: "New Conversation",
        createdAt: Date.now(),
        updatedAt: Date.now(),
        messages: []
      }]);
      setActiveId(newId);
    }
    
    setIsInitialized(true);
  }, [isInitialized]);

  // Save to localStorage when conversations change
  useEffect(() => {
    if (isInitialized && conversations.length > 0) {
      localStorage.setItem("ibm_bob_chat_history", JSON.stringify(conversations));
    }
  }, [conversations, isInitialized]);

  // Save activeId to localStorage
  useEffect(() => {
    if (isInitialized && activeId) {
      localStorage.setItem("ibm_bob_active_chat_id", activeId);
    }
  }, [activeId, isInitialized]);

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

  const activeConversation = conversations.find(c => c.id === activeId);
  const messagesToDisplay = activeConversation?.messages || [];

  useEffect(() => {
    endRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messagesToDisplay, isTyping, activeId]);

  const createNewChat = () => {
    const newId = Date.now().toString();
    const newConvo: Conversation = {
      id: newId,
      title: "New Conversation",
      createdAt: Date.now(),
      updatedAt: Date.now(),
      messages: []
    };
    setConversations(prev => [newConvo, ...prev]);
    setActiveId(newId);
  };

  const startRename = (c: Conversation) => {
    setMenuOpenId(null);
    setRenameTitle(c.title);
    setRenamingId(c.id);
  };

  const saveRename = (id: string) => {
    if (!renameTitle.trim()) {
      setRenamingId(null);
      return;
    }
    setConversations(prev => prev.map(c => 
      c.id === id ? { ...c, title: renameTitle.trim() } : c
    ));
    setRenamingId(null);
  };

  const confirmDelete = (id: string) => {
    setMenuOpenId(null);
    setDeleteConfirmId(id);
  };

  const executeDelete = () => {
    if (!deleteConfirmId) return;
    const idToDelete = deleteConfirmId;
    setDeleteConfirmId(null);
    
    setConversations(prev => {
      const next = prev.filter(c => c.id !== idToDelete);
      
      if (next.length === 0) {
        const newId = Date.now().toString();
        next.push({
          id: newId,
          title: "New Conversation",
          createdAt: Date.now(),
          updatedAt: Date.now(),
          messages: []
        });
        setTimeout(() => setActiveId(newId), 0);
      } else if (activeId === idToDelete) {
        setTimeout(() => setActiveId(next[0].id), 0);
      }
      
      return next;
    });
  };

  const sendMessage = async (value?: string) => {
    const question = (value ?? input).trim();

    if (!question || isTyping || !activeId) return;

    setInput("");
    setIsTyping(true);

    const userMessage: ChatMessage = {
      id: Date.now(),
      sender: "operator",
      text: question,
    };

    setConversations(prev => prev.map(c => {
      if (c.id === activeId) {
        const isFirstMessage = c.messages.length === 0;
        return {
          ...c,
          title: isFirstMessage ? (question.length > 25 ? question.slice(0, 25) + "..." : question) : c.title,
          updatedAt: Date.now(),
          messages: [...c.messages, userMessage]
        };
      }
      return c;
    }));

    try {
      const { response } = await sendChatMessage(question);
      
      const bobMessage: ChatMessage = {
        id: Date.now() + 1,
        sender: "bob",
        text: response,
      };

      setConversations(prev => prev.map(c => {
        if (c.id === activeId) {
          return {
            ...c,
            updatedAt: Date.now(),
            messages: [...c.messages, bobMessage]
          };
        }
        return c;
      }));
    } catch (e) {
      const errorMessage: ChatMessage = {
        id: Date.now() + 1,
        sender: "bob",
        text: "Error: Unable to reach the backend chat service.",
      };
      setConversations(prev => prev.map(c => {
        if (c.id === activeId) {
          return {
            ...c,
            updatedAt: Date.now(),
            messages: [...c.messages, errorMessage]
          };
        }
        return c;
      }));
    } finally {
      setIsTyping(false);
    }
  };

  const readyCount = summary?.counts.READY ?? 0;
  const notReadyCount = summary?.counts.NOT_READY ?? 0;
  const total = summary?.total ?? 0;
  const fleetHealthPct = total > 0 ? Math.round((readyCount / total) * 100) : 0;
  const highRecs = recs.filter((r) => r.urgency === "HIGH").length;

  const formatMessage = (text: string) => {
    const lines = text.split("\n");

    const formatBold = (line: string) => {
      const parts = line.split(/(\*\*.*?\*\*)/g);

      return parts.map((part, index) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return (
            <strong key={index}>
              {part.slice(2, -2)}
            </strong>
          );
        }

        return part;
      });
    };

    return (
      <div className="space-y-1">
        {lines.map((line, index) => {
          const trimmedLine = line.trim();

          if (!trimmedLine) {
            return <div key={index} className="h-2" />;
          }

          if (
            trimmedLine.startsWith("- ") ||
            trimmedLine.startsWith("* ") ||
            trimmedLine.startsWith("• ")
          ) {
            const content = trimmedLine.replace(/^[-*•]\s+/, "");

            return (
              <div key={index} className="flex gap-2">
                <span>•</span>
                <span>{formatBold(content)}</span>
              </div>
            );
          }

          if (/^\d+\.\s/.test(trimmedLine)) {
            return (
              <div key={index}>
                {formatBold(trimmedLine)}
              </div>
            );
          }

          return (
            <div key={index}>
              {formatBold(trimmedLine)}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="space-y-6 relative">
      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setDeleteConfirmId(null)}>
          <div 
            className="p-6 rounded-xl border border-[var(--border-default)] w-[320px] shadow-2xl"
            style={{ backgroundColor: "var(--surface-card)" }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-bold text-[var(--danger-text)] mb-2">Delete Chat?</h3>
            <p className="text-[13px] leading-5 text-[var(--text-secondary)] mb-6">
              Are you sure you want to delete this conversation? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button 
                onClick={() => setDeleteConfirmId(null)} 
                className="btn-secondary-sm px-4"
              >
                Cancel
              </button>
              <button 
                onClick={executeDelete} 
                className="btn-sm px-4"
                style={{ backgroundColor: "var(--danger)", color: "white" }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

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

      <section className="grid gap-5 lg:grid-cols-[280px_minmax(0,1fr)] xl:grid-cols-[300px_minmax(0,1fr)]">

        {/* ── Chat History (LEFT) ───────────────────────────────────────── */}
        <article className="flex flex-col h-[calc(100vh-220px)] min-h-[400px] max-h-[760px] overflow-hidden rounded-xl card">
          <div
            className="px-5 py-4"
            style={{
              borderBottom: "1px solid var(--border-default)",
              background: "linear-gradient(135deg, color-mix(in srgb, var(--brand-500) 8%, transparent) 0%, transparent 60%)",
            }}
          >
            <p className="eyebrow">Chat History</p>
            <div className="mt-3">
              <button
                type="button"
                onClick={createNewChat}
                className="w-full flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-[13px] font-semibold transition-all duration-150"
                style={{
                  backgroundColor: "var(--surface-elevated)",
                  border: "1px dashed var(--border-strong)",
                  color: "var(--text-primary)",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.backgroundColor = "var(--surface-overlay)";
                  (e.currentTarget as HTMLElement).style.borderColor = "var(--brand-500)";
                  (e.currentTarget as HTMLElement).style.color = "var(--text-brand)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.backgroundColor = "var(--surface-elevated)";
                  (e.currentTarget as HTMLElement).style.borderColor = "var(--border-strong)";
                  (e.currentTarget as HTMLElement).style.color = "var(--text-primary)";
                }}
              >
                + New Chat
              </button>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-3 space-y-1">
            <p className="px-2 mb-2 mt-1 text-[10px] font-semibold uppercase tracking-[0.12em]" style={{ color: "var(--text-muted)" }}>
              Recent Chats
            </p>
            {conversations.map(c => {
              const isActive = activeId === c.id;
              const isRenaming = renamingId === c.id;
              
              return (
                <div key={c.id} className="relative group">
                  <div
                    onClick={() => { if (!isRenaming) setActiveId(c.id); }}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors duration-150 ${isRenaming ? '' : 'cursor-pointer'}`}
                    style={{
                      backgroundColor: isActive ? "var(--surface-elevated)" : "transparent",
                      border: isActive ? "1px solid var(--border-default)" : "1px solid transparent",
                    }}
                  >
                    <MessageSquare className="h-4 w-4 shrink-0" style={{ color: isActive ? "var(--brand-500)" : "var(--text-muted)" }} />
                    
                    {isRenaming ? (
                      <input
                        autoFocus
                        value={renameTitle}
                        onChange={(e) => setRenameTitle(e.target.value)}
                        onBlur={() => saveRename(c.id)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') saveRename(c.id);
                          if (e.key === 'Escape') setRenamingId(null);
                        }}
                        onClick={(e) => e.stopPropagation()}
                        className="flex-1 bg-transparent text-[13px] outline-none border-b border-[var(--brand-500)] text-[var(--text-primary)] px-1"
                      />
                    ) : (
                      <span className="truncate flex-1 text-[13px] font-medium" style={{ color: isActive ? "var(--text-primary)" : "var(--text-secondary)" }}>
                        {c.title}
                      </span>
                    )}
                    
                    {!isRenaming && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setMenuOpenId(menuOpenId === c.id ? null : c.id);
                        }}
                        className={`shrink-0 p-1 rounded-md transition-opacity duration-200 ${menuOpenId === c.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}
                        style={{ color: "var(--text-muted)", backgroundColor: menuOpenId === c.id ? "var(--surface-overlay)" : "transparent" }}
                      >
                        <MoreVertical className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                  
                  {/* Options Dropdown */}
                  {menuOpenId === c.id && (
                    <>
                      <div className="fixed inset-0 z-10" onClick={(e) => { e.stopPropagation(); setMenuOpenId(null); }} />
                      <div 
                        className="absolute right-2 top-10 w-36 rounded-lg border shadow-xl z-20 overflow-hidden"
                        style={{ backgroundColor: "var(--surface-card)", borderColor: "var(--border-strong)" }}
                      >
                        <button
                          onClick={(e) => { e.stopPropagation(); startRename(c); }}
                          className="w-full text-left px-4 py-2 text-[12px] font-medium transition-colors hover:bg-[var(--surface-elevated)] text-[var(--text-primary)] border-b border-[var(--border-default)]"
                        >
                          Rename Chat
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); confirmDelete(c.id); }}
                          className="w-full text-left px-4 py-2 text-[12px] font-medium transition-colors hover:bg-[var(--danger-bg)] text-[var(--danger-text)]"
                        >
                          Delete Chat
                        </button>
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>
        </article>

        {/* ── Chat panel (RIGHT) ───────────────────────────────────────── */}
        <article
          className="flex h-[calc(100vh-220px)] min-h-[400px] max-h-[760px] flex-col overflow-hidden rounded-xl"
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
          <div className="min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-6">
            
            {/* Welcome Screen (only when empty) */}
            {messagesToDisplay.length === 0 && (
              <>
                <div className="flex justify-start">
                  <div className="flex max-w-[760px] gap-3 flex-row">
                    <div
                      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[9px] font-bold"
                      style={{
                        background: "linear-gradient(135deg, var(--brand-700), var(--brand-500))",
                        color: "#fff",
                        boxShadow: "0 0 10px rgba(175,23,99,0.3)",
                      }}
                    >
                      <Bot className="h-4 w-4" strokeWidth={1.7} />
                    </div>
                    <div
                      className="rounded-2xl px-5 py-3.5"
                      style={{
                        backgroundColor: "var(--surface-elevated)",
                        border: "1px solid var(--border-default)",
                        color: "var(--text-primary)",
                        borderTopLeftRadius: "4px",
                        borderLeft: "2px solid var(--brand-500)",
                      }}
                    >
                      <div className="whitespace-pre-line text-[13px] leading-6" style={{ color: "var(--text-primary)" }}>
                        Hello. I'm IBM BOB, your mission intelligence assistant. I explain fleet health, asset warnings, maintenance priorities, predictions, and mission readiness based on the AssetSentinel backend.
                      </div>
                    </div>
                  </div>
                </div>

                <div
                  className="rounded-xl p-4 mt-2"
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
                            ? `Fleet: ${readyCount}/${total} READY · ${notReadyCount} NOT READY · ${highRecs} high-urgency maintenance item(s). Modeled Cost Avoided: ₹${summary.economics?.fleet_potential_cost_avoided?.toLocaleString(undefined, { maximumFractionDigits: 0 }) || 0}.`
                            : "Backend context unavailable. Refresh context to reconnect."}
                      </p>
                      
                      {/* Backend-Authoritative Economics Explanation */}
                      <div className="mt-3 p-3 rounded border border-[var(--border-strong)]" style={{ backgroundColor: "var(--surface-elevated)" }}>
                        <p className="text-[11px] font-semibold" style={{ color: "var(--text-brand)" }}>Economic Model Synchronization Active</p>
                        <p className="text-[11px] mt-1" style={{ color: "var(--text-secondary)" }}>
                          IBM Bob calculates all ROI, Economic Impact, and Cost Avoidance using the authoritative backend CostEngine. Cost Assumptions configured by operators are passed to the backend, which models each asset individually based on failure probability and decision paths.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Conversation Messages */}
            {messagesToDisplay.map((msg) => {
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
                      <div
                        className="whitespace-pre-line text-[13px] leading-6"
                        style={{ color: isOperator ? "#fff" : "var(--text-primary)" }}
                      >
                        {formatMessage(msg.text)}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}

            {isTyping && (
              <div className="flex justify-start">
                <div className="flex max-w-[760px] gap-3">
                  <div
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
                    style={{
                      background: "linear-gradient(135deg, var(--brand-700), var(--brand-500))",
                      color: "#fff",
                      boxShadow: "0 0 10px rgba(175,23,99,0.3)",
                    }}
                  >
                    <Bot className="h-4 w-4" strokeWidth={1.7} />
                  </div>
                  <div
                    className="flex items-center gap-1.5 rounded-2xl px-5 py-4"
                    style={{
                      backgroundColor: "var(--surface-elevated)",
                      border: "1px solid var(--border-default)",
                      borderTopLeftRadius: "4px",
                      borderLeft: "2px solid var(--brand-500)",
                    }}
                  >
                    <span className="typing-dot typing-dot-1" />
                    <span className="typing-dot typing-dot-2" />
                    <span className="typing-dot typing-dot-3" />
                  </div>
                </div>
              </div>
            )}
            
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
                disabled={isTyping}
                placeholder={
                  isTyping
                    ? "IBM BOB is thinking…"
                    : "Ask IBM BOB about your fleet…"
                }
                className="min-w-0 flex-1 bg-transparent text-[13px] outline-none disabled:opacity-60"
                style={{
                  color: "var(--text-primary)",
                }}
              />
              <button
                type="submit"
                disabled={!input.trim() || isTyping}
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
