import { Bell, ChevronRight, Moon, Sun, UserCircle } from "lucide-react";

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

  return (
    <header
      className="flex h-[60px] shrink-0 items-center justify-between px-6 lg:px-8"
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
      <div className="flex items-center gap-2">

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
        <button
          type="button"
          aria-label="Notifications"
          className="relative flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-150"
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
          <Bell className="h-[17px] w-[17px]" strokeWidth={1.5} />
          <span
            className="absolute right-[7px] top-[5px] h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: "var(--danger-text)" }}
          />
        </button>

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