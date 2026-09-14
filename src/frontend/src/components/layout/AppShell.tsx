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
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  const toggleTheme = () =>
    setTheme((t) => (t === "dark" ? "light" : "dark"));

  return (
    <div
      data-theme={theme}
      className="flex h-screen overflow-hidden"
      style={{ backgroundColor: "var(--surface-base)", color: "var(--text-primary)" }}
    >
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed((v) => !v)}
        currentPage={currentPage}
        onNavigate={onNavigate}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header
          currentPage={currentPage}
          theme={theme}
          onToggleTheme={toggleTheme}
        />

        <main
          className="flex-1 overflow-y-auto"
          style={{ backgroundColor: "var(--surface-base)" }}
        >
          <div className="mx-auto w-full max-w-[1700px] px-5 py-6 sm:px-7 sm:py-7 lg:px-9 lg:py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

export default AppShell;