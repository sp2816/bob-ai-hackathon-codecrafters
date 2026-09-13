import type { ReactNode } from "react";
import { useState } from "react";

import Header from "./Header";
import Sidebar from "./Sidebar";

interface AppShellProps {
  children: ReactNode;
  currentPage: string;
  onNavigate: (page: string) => void;
}

function AppShell({
  children,
  currentPage,
  onNavigate,
}: AppShellProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-[#F7F1E7] text-[#3B2A20]">
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed((value) => !value)}
        currentPage={currentPage}
        onNavigate={onNavigate}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header currentPage={currentPage} />

        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-[1700px] px-5 py-6 sm:px-7 sm:py-7 lg:px-9 lg:py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

export default AppShell;