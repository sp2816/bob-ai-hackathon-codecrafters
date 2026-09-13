import {
  Bell,
  ChevronDown,
  ChevronRight,
  Home,
  UserCircle,
} from "lucide-react";

interface HeaderProps {
  currentPage: string;
}

const pageLabels: Record<string, string> = {
  dashboard: "Dashboard",
  assets: "Assets",
  predictions: "Predictions",
  maintenance: "Maintenance",
  "ibm-bob": "IBM Bob",
};

function Header({ currentPage }: HeaderProps) {
  const currentLabel = pageLabels[currentPage] ?? "Dashboard";

  return (
    <header className="flex h-[92px] shrink-0 items-center justify-between border-b border-[#DED2C0] bg-[#F7F1E7] px-7 lg:px-9">
      {/* Breadcrumbs */}
      <div className="flex min-w-0 items-center gap-2">
        <Home
          className="h-4 w-4 shrink-0 text-[#806B59]"
          strokeWidth={1.5}
        />

        <span className="text-[11px] text-[#A39484]">
          Breadcrumbs
        </span>

        <ChevronRight
          className="h-3.5 w-3.5 shrink-0 text-[#B6A593]"
          strokeWidth={1.5}
        />

        <span className="truncate text-[11px] font-medium text-[#4A3528]">
          {currentLabel}
        </span>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-5">
        {/* Notifications */}
        <button
          type="button"
          aria-label="Notifications"
          className="relative flex h-9 w-9 items-center justify-center rounded-full text-[#806B59] transition-colors hover:bg-[#EEE5D7]"
        >
          <Bell
            className="h-[18px] w-[18px]"
            strokeWidth={1.5}
          />

          <span className="absolute right-[7px] top-[6px] h-1.5 w-1.5 rounded-full bg-[#B95F46]" />
        </button>

        {/* Divider */}
        <div className="h-8 w-px bg-[#DED2C0]" />

        {/* Operator profile */}
        <button
          type="button"
          className="flex items-center gap-3 rounded-full border border-[#DED2C0] bg-[#EEE5D7] px-3 py-2 transition-colors hover:bg-[#E7DDCD]"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#E2D7C7] text-[#806B59]">
            <UserCircle
              className="h-5 w-5"
              strokeWidth={1.5}
            />
          </span>

          <span className="hidden text-left sm:block">
            <span className="block text-[11px] font-medium text-[#3B2A20]">
              OP / Operator
            </span>

            <span className="mt-0.5 block text-[8px] font-medium uppercase tracking-[0.14em] text-[#A39484]">
              Mission Control
            </span>
          </span>

          <ChevronDown
            className="h-4 w-4 text-[#8B7968]"
            strokeWidth={1.5}
          />
        </button>
      </div>
    </header>
  );
}

export default Header;