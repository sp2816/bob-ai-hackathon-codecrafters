import {
  Activity,
  Bot,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  Package,
  Wrench,
} from "lucide-react";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  currentPage: string;
  onNavigate: (page: string) => void;
}

const navigation = [
  {
    label: "Dashboard",
    icon: LayoutDashboard,
    page: "dashboard",
  },
  {
    label: "Assets",
    icon: Package,
    page: "assets",
  },
  {
    label: "Predictions",
    icon: Activity,
    page: "predictions",
  },
  {
    label: "Maintenance",
    icon: Wrench,
    page: "maintenance",
  },
  {
    label: "IBM Bob",
    icon: Bot,
    page: "ibm-bob",
  },
];

function Sidebar({
  collapsed,
  onToggle,
  currentPage,
  onNavigate,
}: SidebarProps) {
  return (
    <aside
      className={`flex h-screen shrink-0 flex-col border-r border-[#DED2C0] bg-[#E9DDCB] transition-all duration-200 ${
        collapsed ? "w-[72px]" : "w-[250px]"
      }`}
    >
      {/* Brand */}
      <div
        className={`flex h-[92px] shrink-0 items-center border-b border-[#DED2C0] ${
          collapsed ? "justify-center" : "px-6"
        }`}
      >
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#69784F] text-[11px] font-bold tracking-wide text-[#FBF8F2] shadow-sm">
            AS
          </div>

          {!collapsed && (
            <div>
              <div className="text-[17px] font-semibold tracking-[-0.035em] text-[#3B2A20]">
                AssetSentinel
              </div>

              <div className="mt-1 text-[9px] font-medium uppercase tracking-[0.18em] text-[#8B7968]">
                Mission Intelligence
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-8">
        {!collapsed && (
          <p className="mb-4 px-3 text-[9px] font-semibold uppercase tracking-[0.2em] text-[#9B8977]">
            Workspace
          </p>
        )}

        <div className="space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = currentPage === item.page;

            return (
              <button
                key={item.page}
                type="button"
                title={collapsed ? item.label : undefined}
                onClick={() => onNavigate(item.page)}
                className={`
                  group flex w-full items-center rounded-full
                  px-4 py-3
                  transition-all duration-150
                  ${collapsed ? "justify-center" : "gap-3.5"}
                  ${
                    active
                      ? "bg-[#AAB98A] text-[#3B2A20] shadow-sm"
                      : "text-[#4D382B] hover:bg-[#E1D3C0]"
                  }
                `}
              >
                <Icon
                  className={`h-[19px] w-[19px] shrink-0 ${
                    active ? "text-[#3B2A20]" : "text-[#6D5748]"
                  }`}
                  strokeWidth={1.7}
                />

                {!collapsed && (
                  <span
                    className={`text-[14px] ${
                      active ? "font-semibold" : "font-medium"
                    }`}
                  >
                    {item.label}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </nav>

      {/* System status */}
      <div className="border-t border-[#DED2C0] px-5 py-6">
        <div
          className={`flex items-start ${
            collapsed ? "justify-center" : "gap-3"
          }`}
        >
          <span className="relative mt-1 flex h-3 w-3 shrink-0 items-center justify-center">
            <span className="absolute h-3 w-3 rounded-full bg-[#69784F] opacity-20" />
            <span className="relative h-2 w-2 rounded-full bg-[#69784F]" />
          </span>

          {!collapsed && (
            <div>
              <p className="text-[10px] font-medium text-[#8B7968]">
                System status:
              </p>

              <p className="mt-1 text-[13px] font-semibold text-[#596842]">
                All operational
              </p>
            </div>
          )}
        </div>

        {/* Collapse */}
        <button
          type="button"
          onClick={onToggle}
          className="mt-6 flex w-full items-center justify-center gap-2 border-t border-[#DED2C0] pt-4 text-[#8B7968] transition-colors hover:text-[#3B2A20]"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" strokeWidth={1.6} />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4" strokeWidth={1.6} />

              <span className="text-[9px] font-semibold uppercase tracking-[0.12em]">
                Collapse
              </span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;