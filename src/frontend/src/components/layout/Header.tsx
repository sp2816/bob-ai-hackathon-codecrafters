import { Bell, ChevronRight, Moon, Sun, UserCircle, CheckCircle2 } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { getNotifications } from "../../services/api";
import type { ApiNotification } from "../../types/api";

interface HeaderProps {
  currentPage: string;
  theme: "dark" | "light";
  onToggleTheme: () => void;
}

const pageLabels: Record<string, string> = {
  dashboard:   "Dashboard",
  assets:      "Assets",
  predictions: "Predictions",
  maintenance: "Maintenance",
  "ibm-bob":   "IBM Bob",
};

function Header({ currentPage, theme, onToggleTheme }: HeaderProps) {
  const currentLabel = pageLabels[currentPage] ?? "Dashboard";

  const [notifications, setNotifications] = useState<ApiNotification[]>([]);
  const [unreadIds, setUnreadIds] = useState<Set<string>>(new Set());
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const fetchNotifs = async () => {
    setLoading(true);
    try {
      const data = await getNotifications();
      setNotifications(data);
      
      const readSet = new Set(JSON.parse(localStorage.getItem("read_notifications") || "[]"));
      const newUnread = new Set<string>();
      for (const n of data) {
        if (!readSet.has(n.id)) {
          newUnread.add(n.id);
        }
      }
      setUnreadIds(newUnread);
    } catch (e) {
      console.error("Failed to load notifications", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifs();
    const handleRefresh = () => fetchNotifs();
    window.addEventListener("refresh-notifications", handleRefresh);
    return () => window.removeEventListener("refresh-notifications", handleRefresh);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleMarkAllRead = () => {
    const allIds = notifications.map(n => n.id);
    const readSet = new Set([...JSON.parse(localStorage.getItem("read_notifications") || "[]"), ...allIds]);
    localStorage.setItem("read_notifications", JSON.stringify(Array.from(readSet)));
    setUnreadIds(new Set());
  };

  return (
    <header
      className="flex h-[60px] shrink-0 items-center justify-between px-6 lg:px-8 relative z-50"
      style={{
        backgroundColor: "var(--surface-card)",
        borderBottom: "1px solid var(--border-default)",
      }}
    >
      {/* Breadcrumbs */}
      <div className="flex min-w-0 items-center gap-2">
        <span className="text-[12px]" style={{ color: "var(--text-muted)" }}>
          AssetSentinel
        </span>
        <ChevronRight className="h-3.5 w-3.5 shrink-0" style={{ color: "var(--border-strong)" }} strokeWidth={1.5} />
        <span
          className="text-[12px] font-semibold"
          style={{ color: "var(--text-brand)" }}
        >
          {currentLabel}
        </span>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-2 relative">

        {/* Theme toggle */}
        <button
          type="button"
          onClick={onToggleTheme}
          aria-label="Toggle theme"
          className="flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-150"
          style={{ color: "var(--text-muted)" }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = "var(--surface-elevated)";
            (e.currentTarget as HTMLElement).style.color = "var(--text-primary)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";
            (e.currentTarget as HTMLElement).style.color = "var(--text-muted)";
          }}
        >
          {theme === "dark" ? (
            <Sun className="h-[17px] w-[17px]" strokeWidth={1.6} />
          ) : (
            <Moon className="h-[17px] w-[17px]" strokeWidth={1.6} />
          )}
        </button>

        {/* Notifications */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            aria-label="Notifications"
            onClick={() => setIsOpen(!isOpen)}
            className="relative flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-150"
            style={{ 
              color: isOpen ? "var(--text-primary)" : "var(--text-muted)",
              backgroundColor: isOpen ? "var(--surface-elevated)" : "transparent"
            }}
            onMouseEnter={(e) => {
              if (!isOpen) {
                (e.currentTarget as HTMLElement).style.backgroundColor = "var(--surface-elevated)";
                (e.currentTarget as HTMLElement).style.color = "var(--text-primary)";
              }
            }}
            onMouseLeave={(e) => {
              if (!isOpen) {
                (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";
                (e.currentTarget as HTMLElement).style.color = "var(--text-muted)";
              }
            }}
          >
            <Bell className="h-[17px] w-[17px]" strokeWidth={1.5} />
            {unreadIds.size > 0 && (
              <span
                className="absolute right-[5px] top-[3px] flex h-3.5 w-3.5 items-center justify-center rounded-full text-[9px] font-bold text-white"
                style={{ backgroundColor: "var(--danger-text)" }}
              >
                {unreadIds.size}
              </span>
            )}
          </button>

          {isOpen && (
            <div 
              className="absolute right-0 mt-2 w-80 rounded-xl overflow-hidden shadow-lg"
              style={{
                backgroundColor: "var(--surface-card)",
                border: "1px solid var(--border-default)",
                boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.2)"
              }}
            >
              <div 
                className="flex items-center justify-between px-4 py-3"
                style={{ borderBottom: "1px solid var(--border-subtle)", backgroundColor: "var(--surface-elevated)" }}
              >
                <h3 className="text-sm font-semibold text-primary" style={{ color: "var(--text-primary)"}}>Notifications</h3>
                {unreadIds.size > 0 && (
                  <button 
                    onClick={handleMarkAllRead}
                    className="text-xs font-medium transition-colors"
                    style={{ color: "var(--text-brand)" }}
                    onMouseEnter={e => e.currentTarget.style.textDecoration = "underline"}
                    onMouseLeave={e => e.currentTarget.style.textDecoration = "none"}
                  >
                    Mark all as read
                  </button>
                )}
              </div>

              <div className="max-h-[400px] overflow-y-auto">
                {loading && notifications.length === 0 ? (
                  <div className="px-4 py-8 text-center text-xs" style={{ color: "var(--text-muted)" }}>
                    Loading notifications...
                  </div>
                ) : notifications.length === 0 ? (
                  <div className="px-4 py-8 text-center flex flex-col items-center">
                    <CheckCircle2 className="h-8 w-8 mb-2" style={{ color: "var(--success-text)", opacity: 0.5 }} />
                    <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>All caught up!</span>
                    <span className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>No new alerts to display.</span>
                  </div>
                ) : (
                  <ul className="divide-y" style={{ borderColor: "var(--border-subtle)" }}>
                    {notifications.map(n => {
                      const isUnread = unreadIds.has(n.id);
                      return (
                        <li 
                          key={n.id} 
                          className="px-4 py-3 transition-colors"
                          style={{
                            backgroundColor: isUnread ? "color-mix(in srgb, var(--brand-500) 5%, transparent)" : "transparent"
                          }}
                          onMouseEnter={e => e.currentTarget.style.backgroundColor = "var(--surface-overlay)"}
                          onMouseLeave={e => e.currentTarget.style.backgroundColor = isUnread ? "color-mix(in srgb, var(--brand-500) 5%, transparent)" : "transparent"}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <span 
                              className="text-xs font-bold"
                              style={{ 
                                color: n.severity === "CRITICAL" || n.severity === "HIGH" 
                                  ? "var(--danger-text)" 
                                  : "var(--warning-text)" 
                              }}
                            >
                              {n.severity === "CRITICAL" || n.severity === "HIGH" ? "🔴 " : "🟡 "}{n.title}
                            </span>
                            <span className="text-[10px]" style={{ color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                              {new Date(n.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            </span>
                          </div>
                          <p className="text-xs mt-1 leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                            {n.message}
                          </p>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="h-6 w-px mx-1" style={{ backgroundColor: "var(--border-default)" }} />

        {/* Operator profile */}
        <button
          type="button"
          className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 transition-all duration-150"
          style={{
            border: "1px solid var(--border-default)",
            backgroundColor: "var(--surface-elevated)",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = "var(--surface-overlay)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.backgroundColor = "var(--surface-elevated)";
          }}
        >
          <span
            className="flex h-6 w-6 items-center justify-center rounded-md"
            style={{ backgroundColor: "rgba(175,23,99,0.15)", color: "var(--text-brand)" }}
          >
            <UserCircle className="h-4 w-4" strokeWidth={1.5} />
          </span>
          <span className="hidden text-left sm:block">
            <span className="block text-[11px] font-semibold" style={{ color: "var(--text-primary)" }}>
              Operator
            </span>
            <span className="mt-0.5 block text-[9px] font-medium uppercase tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>
              Mission Control
            </span>
          </span>
        </button>
      </div>
    </header>
  );
}

export default Header;