import {
  Activity,
  Bot,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  Package,
  Shield,
  Wrench,
  Calculator,
} from "lucide-react";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  currentPage: string;
  onNavigate: (page: string) => void;
}

const navigation = [
  { label: "Dashboard",    icon: LayoutDashboard, page: "dashboard" },
  { label: "Assets",       icon: Package,         page: "assets" },
  { label: "Predictions",  icon: Activity,        page: "predictions" },
  { label: "Maintenance",  icon: Wrench,          page: "maintenance" },
  { label: "IBM Bob",      icon: Bot,             page: "ibm-bob" },
  { label: "Cost Settings",icon: Calculator,      page: "cost-assumptions" },
];

function Sidebar({ collapsed, onToggle, currentPage, onNavigate }: SidebarProps) {
  return (
    <aside
      style={{
        backgroundColor: "var(--surface-card)",
        borderRight: "1px solid var(--border-default)",
        transition: "background-color 0.2s ease, border-color 0.2s ease",
      }}
      className={`flex h-screen shrink-0 flex-col ${
        collapsed ? "w-[68px]" : "w-[240px]"
      }`}
    >
      {/* Brand */}
      <div
        className={`flex h-[64px] shrink-0 items-center ${
          collapsed ? "justify-center" : "px-5"
        }`}
        style={{ borderBottom: "1px solid var(--border-default)" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
            style={{
              background: "linear-gradient(135deg, var(--brand-700), var(--brand-500))",
              boxShadow: "0 0 14px rgba(111,66,193,0.3)",
            }}
          >
            <Shield className="h-4 w-4 text-white" strokeWidth={2} />
          </div>

          {!collapsed && (
            <div>
              <div
                className="text-[15px] font-bold tracking-[-0.03em]"
                style={{ color: "var(--text-primary)" }}
              >
                AssetSentinel
              </div>
              <div
                className="mt-0.5 text-[9px] font-semibold uppercase tracking-[0.18em]"
                style={{ color: "var(--text-muted)" }}
              >
                Mission Intelligence
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className={`flex-1 py-4 ${collapsed ? "px-2" : "px-3"}`}>
        {!collapsed && (
          <p
            className="mb-2 px-2 text-[9px] font-semibold uppercase tracking-[0.2em]"
            style={{ color: "var(--text-muted)" }}
          >
            Workspace
          </p>
        )}

        <div className="space-y-0.5">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = currentPage === item.page;

            return (
              <button
                key={item.page}
                type="button"
                title={collapsed ? item.label : undefined}
                onClick={() => onNavigate(item.page)}
                className={`group relative flex w-full items-center rounded-lg transition-all duration-150 ${
                  collapsed ? "justify-center px-2 py-3" : "gap-3 px-3 py-2.5"
                }`}
                style={
                  active
                    ? {
                        backgroundColor: "color-mix(in srgb, var(--brand-500) 12%, transparent)",
                        color: "var(--text-brand)",
                        borderLeft: "3px solid var(--brand-500)",
                        paddingLeft: collapsed ? undefined : "9px",
                      }
                    : {
                        color: "var(--text-secondary)",
                        backgroundColor: "transparent",
                        borderLeft: "3px solid transparent",
                        paddingLeft: collapsed ? undefined : "9px",
                      }
                }
                onMouseEnter={(e) => {
                  if (!active) {
                    (e.currentTarget as HTMLElement).style.backgroundColor =
                      "var(--surface-elevated)";
                    (e.currentTarget as HTMLElement).style.color = "var(--text-primary)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!active) {
                    (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";
                    (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)";
                  }
                }}
              >
                <Icon
                  className="h-[18px] w-[18px] shrink-0"
                  strokeWidth={active ? 2 : 1.7}
                />

                {!collapsed && (
                  <span className={`text-[13px] ${active ? "font-semibold" : "font-medium"}`}>
                    {item.label}
                  </span>
                )}

                {collapsed && active && (
                  <span
                    className="absolute right-1 top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-full"
                    style={{ backgroundColor: "var(--brand-500)" }}
                  />
                )}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      <div
        className="px-3 pb-5 pt-4"
        style={{ borderTop: "1px solid var(--border-default)" }}
      >
        {!collapsed && (
          <div className="mb-4 flex items-center gap-2.5 px-2">
            <span className="pulse-online" />
            <div>
              <p className="text-[10px] font-medium" style={{ color: "var(--text-muted)" }}>
                System status
              </p>
              <p className="mt-0.5 text-[12px] font-semibold" style={{ color: "var(--success-text)" }}>
                All operational
              </p>
            </div>
          </div>
        )}

        <button
          type="button"
          onClick={onToggle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className={`flex w-full items-center rounded-lg px-2 py-2 text-[11px] font-medium transition-all duration-150 ${
            collapsed ? "justify-center" : "gap-2"
          }`}
          style={{ color: "var(--text-muted)" }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.color = "var(--text-primary)";
            (e.currentTarget as HTMLElement).style.backgroundColor = "var(--surface-elevated)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.color = "var(--text-muted)";
            (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";
          }}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" strokeWidth={1.6} />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4" strokeWidth={1.6} />
              <span>Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;