import {
  Bell,
  ChevronDown,
  Home,
  UserRound,
} from "lucide-react";

function Header() {
  return (
    <header className="shrink-0 border-b border-[#DED2C0] bg-[#F7F1E7]">
      <div className="flex min-h-[82px] items-center justify-between gap-5 px-5 sm:px-7 lg:px-9">
        {/* Breadcrumbs */}
        <div className="flex min-w-0 items-center gap-2 text-[#725B49]">
          <Home
            className="h-[15px] w-[15px] shrink-0"
            strokeWidth={1.6}
          />

          <span className="text-[12px] text-[#9B8977]">
            Breadcrumbs
          </span>

          <span className="text-[#B2A18F]">›</span>

          <span className="text-[12px] font-medium text-[#5D4535]">
            Assets
          </span>

          <span className="text-[#B2A18F]">›</span>

          <span className="text-[12px] font-medium text-[#5D4535]">
            Predictions
          </span>
        </div>

        {/* Right controls */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            aria-label="Notifications"
            className="relative rounded-full p-2.5 text-[#806B59] transition-colors hover:bg-[#EDE2D2]"
          >
            <Bell
              className="h-[17px] w-[17px]"
              strokeWidth={1.6}
            />

            <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-[#B95F46]" />
          </button>

          <div className="hidden h-7 w-px bg-[#DED2C0] sm:block" />

          {/* Operator badge */}
          <button
            type="button"
            className="flex items-center gap-3 rounded-full border border-[#DED2C0] bg-[#EEE5D7] px-3 py-2 text-left transition-colors hover:bg-[#E7DAC8]"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#D7C8B4] text-[#5D4535]">
              <UserRound
                className="h-4 w-4"
                strokeWidth={1.7}
              />
            </span>

            <span className="hidden sm:block">
              <span className="block text-[11px] font-semibold text-[#4A3528]">
                OP / Operator
              </span>

              <span className="mt-0.5 block text-[8px] uppercase tracking-[0.12em] text-[#9B8977]">
                Mission Control
              </span>
            </span>

            <ChevronDown
              className="h-4 w-4 text-[#8B7968]"
              strokeWidth={1.5}
            />
          </button>
        </div>
      </div>
    </header>
  );
}

export default Header;