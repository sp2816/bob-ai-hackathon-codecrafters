import { Activity, CheckCircle2, Clock3, RefreshCw, ShieldCheck, TriangleAlert, Wrench, Zap } from "lucide-react";
import { useEffect, useState } from "react";

import AppShell from "./components/layout/AppShell";
import Assets from "./pages/Assets";
import Predictions from "./pages/Predictions";
import Maintenance from "./pages/Maintenance";
import IBMBob from "./pages/IBMBob";

import {
  getFleetReadinessSummary,
  getAssets,
  getMissionReadiness,
  getMaintenanceRecommendations,
  runMlPipeline,
  runReadinessPipeline,
} from "./services/api";
import type { ApiFleetSummary, ApiAsset, ApiReadinessResult, ApiMaintenanceRecommendation } from "./types/api";

// ── Helpers ────────────────────────────────────────────────────────────────

const MISSION_IDS = ["MSN-001", "MSN-002", "MSN-003"] as const;
const MISSION_NAMES: Record<string, string> = {
  "MSN-001": "Training",
  "MSN-002": "Patrol",
  "MSN-003": "Strike",
};
const MISSION_PRIORITY: Record<string, string> = {
  "MSN-001": "LOW",
  "MSN-002": "MEDIUM",
  "MSN-003": "HIGH",
};

function readinessStatusForMission(results: ApiReadinessResult[]): string {
  if (results.length === 0) return "UNKNOWN";
  if (results.some((r) => r.readiness_status === "NOT_READY")) return "NOT_READY";
  if (results.some((r) => r.readiness_status === "CONDITIONALLY_READY")) return "CONDITIONALLY_READY";
  return "READY";
}

// ── Mini health chart (static sparkline — decorative trend only) ───────────
function MiniHealthChart() {
  return (
    <svg viewBox="0 0 220 70" className="h-[68px] w-full" preserveAspectRatio="none" aria-label="Fleet health trend">
      <defs>
        <linearGradient id="healthFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#69784F" stopOpacity="0.28" />
          <stop offset="100%" stopColor="#69784F" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path
        d="M0 53 C18 56, 25 43, 42 46 C58 50, 64 31, 82 36 C97 40, 103 25, 120 31 C137 38, 142 19, 159 25 C177 31, 186 11, 202 17 C209 20, 214 12, 220 9 L220 70 L0 70 Z"
        fill="url(#healthFill)"
      />
      <path
        d="M0 53 C18 56, 25 43, 42 46 C58 50, 64 31, 82 36 C97 40, 103 25, 120 31 C137 38, 142 19, 159 25 C177 31, 186 11, 202 17 C209 20, 214 12, 220 9"
        fill="none"
        stroke="#69784F"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <circle cx="220" cy="9" r="4" fill="#69784F" />
    </svg>
  );
}

function ReadinessRing({ score }: { score: number }) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - score / 100);

  return (
    <div className="relative flex h-[126px] w-[126px] items-center justify-center">
      <svg viewBox="0 0 126 126" className="absolute inset-0 h-full w-full -rotate-90">
        <circle cx="63" cy="63" r={radius} fill="none" stroke="#E1D6C6" strokeWidth="9" />
        <circle
          cx="63"
          cy="63"
          r={radius}
          fill="none"
          stroke="#69784F"
          strokeWidth="9"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="relative text-center">
        <div className="text-[29px] font-light leading-none tracking-[-0.05em] text-[#3B2A20]">{score}%</div>
        <div className="mt-1 text-[7px] font-semibold uppercase tracking-[0.15em] text-[#9B8977]">Ready</div>
      </div>
    </div>
  );
}

// ── Dashboard ──────────────────────────────────────────────────────────────

function Dashboard() {
  const [summary, setSummary] = useState<ApiFleetSummary | null>(null);
  const [assets, setAssets] = useState<ApiAsset[]>([]);
  const [missionReadiness, setMissionReadiness] = useState<
    Array<{ mission_id: string; status: string }>
  >([]);
  const [maintenanceCount, setMaintenanceCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [runMsg, setRunMsg] = useState<string | null>(null);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [fleetSummary, fleetAssets, recs, ...msnResults] = await Promise.allSettled([
        getFleetReadinessSummary(),
        getAssets(),
        getMaintenanceRecommendations(),
        ...MISSION_IDS.map((id) => getMissionReadiness(id)),
      ]);

      if (fleetSummary.status === "fulfilled") setSummary(fleetSummary.value);
      if (fleetAssets.status === "fulfilled") setAssets(fleetAssets.value);
      if (recs.status === "fulfilled") setMaintenanceCount(recs.value.length);

      const resolved: Array<{ mission_id: string; status: string }> = [];
      MISSION_IDS.forEach((id, i) => {
        const r = msnResults[i];
        if (r?.status === "fulfilled") {
          resolved.push({
            mission_id: id,
            status: readinessStatusForMission(r.value),
          });
        }
      });
      setMissionReadiness(resolved);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const handleRunAll = async () => {
    setRunning(true);
    setRunMsg(null);
    try {
      await runMlPipeline();
      await runReadinessPipeline();
      setRunMsg("ML + Readiness pipelines refreshed. Reloading dashboard…");
      await fetchAll();
    } catch {
      setRunMsg("Pipeline failed. Ensure the backend is running.");
    } finally {
      setRunning(false);
    }
  };

  const readyCount = summary?.counts.READY ?? 0;
  const notReadyCount = summary?.counts.NOT_READY ?? 0;
  const totalCount = summary?.total ?? 0;

  // Fleet health as percentage of READY assets
  const fleetHealthPct = totalCount > 0 ? Math.round((readyCount / totalCount) * 100) : 0;

  // Mission readiness % = missions that are READY out of known missions
  const readyMissions = missionReadiness.filter((m) => m.status === "READY").length;
  const missionReadinessPct =
    missionReadiness.length > 0 ? Math.round((readyMissions / missionReadiness.length) * 100) : 0;

  return (
    <>
      <div className="space-y-7">
        <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
          <div>
            <p className="eyebrow">Mission Control</p>
            <h1 className="mt-2 text-[42px] font-semibold leading-none tracking-[-0.055em] text-[#3B2A20] sm:text-[48px]">
              Dashboard
            </h1>
            <p className="mt-3 max-w-xl text-[13px] leading-6 text-[#806B59]">
              Fleet health, mission readiness, predictive risk, and maintenance intelligence in one operational view.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleRunAll}
              disabled={running}
              className="flex items-center gap-1.5 rounded-full border border-[#C2CEAE] bg-[#DDE5D1] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#596842] hover:bg-[#CDD9C1] disabled:opacity-50"
            >
              <Zap className="h-3 w-3" />
              {running ? "Running…" : "Refresh All"}
            </button>
            <button
              type="button"
              onClick={fetchAll}
              className="flex items-center gap-1.5 rounded-full border border-[#D8CBB9] bg-[#EEE5D7] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#806B59] hover:bg-[#E5D8C5]"
            >
              <RefreshCw className="h-3 w-3" />
              Reload
            </button>
          </div>
        </section>

        {runMsg && (
          <div className="rounded-xl border border-[#C2CEAE] bg-[#DDE5D1] px-4 py-3 text-[11px] text-[#596842]">
            {runMsg}
          </div>
        )}

        {/* Top KPI cards */}
        <section className="grid gap-5 lg:grid-cols-3">
          {/* Fleet Health */}
          <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
            <div className="flex items-start justify-between">
              <div>
                <p className="eyebrow">Fleet Health</p>
                <h2 className="mt-4 text-[15px] font-semibold text-[#4A3528]">Overall asset health</h2>
              </div>
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#E0E7D6]">
                <Activity className="h-4 w-4 text-[#69784F]" strokeWidth={1.7} />
              </div>
            </div>
            <div className="mt-5 flex items-end justify-between gap-4">
              <div>
                <div className="text-[44px] font-light leading-none tracking-[-0.06em] text-[#3B2A20]">
                  {loading ? "—" : `${fleetHealthPct}%`}
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <span className="moss-dot" />
                  <span className="text-[10px] text-[#69784F]">
                    {loading ? "Loading…" : `${readyCount} / ${totalCount} assets READY`}
                  </span>
                </div>
              </div>
              <div className="w-[48%]">
                <MiniHealthChart />
              </div>
            </div>
          </article>

          {/* Active Alerts */}
          <article className="rounded-2xl border-2 border-[#C96D52] bg-[#FBF4EE] p-6 shadow-[0_8px_30px_rgba(155,75,50,0.05)]">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#A85B45]">Active Alerts</p>
                <h2 className="mt-4 text-[15px] font-semibold text-[#4A3528]">Fleet attention</h2>
              </div>
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#F0D8CF]">
                <TriangleAlert className="h-4 w-4 text-[#B95F46]" strokeWidth={1.7} />
              </div>
            </div>
            <div className="mt-5">
              <div className="text-[44px] font-light leading-none tracking-[-0.06em] text-[#B95F46]">
                {loading ? "—" : notReadyCount}{" "}
                <span className="text-[20px] font-normal">(NOT READY)</span>
              </div>
              <div className="mt-4 flex items-center gap-2">
                <span className="terracotta-dot" />
                <span className="text-[10px] text-[#A85B45]">
                  {loading ? "Loading…" : `${summary?.counts.CONDITIONALLY_READY ?? 0} conditionally ready`}
                </span>
              </div>
            </div>
          </article>

          {/* Mission Readiness */}
          <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
            <div className="flex items-start justify-between">
              <div>
                <p className="eyebrow">Mission Readiness</p>
                <h2 className="mt-4 text-[15px] font-semibold text-[#4A3528]">Fleet assessment</h2>
              </div>
              <ShieldCheck className="h-5 w-5 text-[#69784F]" strokeWidth={1.6} />
            </div>
            <div className="mt-2 flex items-center justify-between">
              <div>
                <div className="text-[44px] font-light leading-none tracking-[-0.06em] text-[#3B2A20]">
                  {loading ? "—" : `${missionReadinessPct}%`}
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <span className="moss-dot" />
                  <span className="text-[10px] text-[#69784F]">
                    {loading ? "Loading…" : `${readyMissions} / ${missionReadiness.length} missions ready`}
                  </span>
                </div>
              </div>
              {!loading && <ReadinessRing score={missionReadinessPct} />}
            </div>
          </article>
        </section>

        {/* Asset health + Mission schedule */}
        <section className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
          {/* Asset list from backend */}
          <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
            <div className="flex items-center justify-between px-6 py-5">
              <div>
                <p className="eyebrow">Fleet</p>
                <h2 className="mt-2 text-[17px] font-semibold text-[#4A3528]">Asset health</h2>
              </div>
              <Activity className="h-5 w-5 text-[#806B59]" strokeWidth={1.5} />
            </div>

            {loading && (
              <div className="border-t border-[#E8DED1] px-6 py-6 text-center text-[11px] text-[#9B8977]">
                Loading assets…
              </div>
            )}

            <div>
              {assets.map((asset) => {
                const healthPct =
                  asset.readiness_score !== null ? Math.round(asset.readiness_score * 100) : 50;
                const isWarning = asset.current_status === "NOT_READY";

                return (
                  <div key={asset.asset_id} className="border-t border-[#E8DED1] px-6 py-5">
                    <div className="flex items-start justify-between gap-5">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span
                            className={`h-2 w-2 rounded-full ${
                              asset.current_status === "READY"
                                ? "bg-[#69784F]"
                                : asset.current_status === "NOT_READY"
                                  ? "bg-[#B95F46]"
                                  : "bg-[#A69A89]"
                            }`}
                          />
                          <span className="font-mono text-[11px] font-semibold text-[#4A3528]">
                            {asset.asset_id}
                          </span>
                          <span className="hidden text-[10px] text-[#9B8977] sm:inline">{asset.asset_name}</span>
                        </div>
                        <p className="mt-2 text-[10px] text-[#806B59]">{asset.asset_type} · {asset.unit}</p>
                      </div>

                      <div className="text-right">
                        <span className="text-[20px] font-light tracking-[-0.04em] text-[#3B2A20]">
                          {healthPct}%
                        </span>
                        <p
                          className={`mt-1 text-[8px] font-semibold uppercase tracking-[0.1em] ${
                            isWarning ? "text-[#B95F46]" : "text-[#69784F]"
                          }`}
                        >
                          {asset.current_status.replace(/_/g, " ")}
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 soft-progress">
                      <div
                        className={isWarning ? "terracotta-progress" : "moss-progress"}
                        style={{ width: `${Math.max(healthPct, 3)}%` }}
                      />
                    </div>
                    <div className="mt-2 flex justify-between">
                      <span className="text-[8px] text-[#A39484]">{asset.operational_hours.toLocaleString()} op. hours</span>
                      <span className="text-[8px] text-[#A39484]">Readiness index</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </article>

          {/* Mission schedule from backend */}
          <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
            <div className="flex items-center justify-between px-6 py-5">
              <div>
                <p className="eyebrow">Schedule</p>
                <h2 className="mt-2 text-[17px] font-semibold text-[#4A3528]">Mission readiness</h2>
              </div>
              <Clock3 className="h-5 w-5 text-[#806B59]" strokeWidth={1.5} />
            </div>

            {loading && (
              <div className="border-t border-[#E8DED1] px-6 py-6 text-center text-[11px] text-[#9B8977]">
                Loading missions…
              </div>
            )}

            <div>
              {MISSION_IDS.map((id) => {
                const result = missionReadiness.find((m) => m.mission_id === id);
                const status = result?.status ?? "UNKNOWN";

                return (
                  <div
                    key={id}
                    className="grid grid-cols-[48px_1fr_auto] items-center gap-3 border-t border-[#E8DED1] px-6 py-5"
                  >
                    <span className="font-mono text-[10px] text-[#9B8977]">{id}</span>

                    <div>
                      <p className="text-[12px] font-semibold text-[#4A3528]">{MISSION_NAMES[id]}</p>
                      <p className="mt-1 text-[9px] text-[#A39484]">{id}</p>
                    </div>

                    <div className="text-right">
                      <span
                        className={`rounded-full border px-2 py-1 text-[7px] font-semibold uppercase tracking-[0.1em] ${
                          MISSION_PRIORITY[id] === "HIGH"
                            ? "border-[#D8A394] bg-[#F0D8CF] text-[#B95F46]"
                            : MISSION_PRIORITY[id] === "MEDIUM"
                              ? "border-[#D8C8A9] bg-[#EEE2CD] text-[#876D47]"
                              : "border-[#C8D2B7] bg-[#E2E8D9] text-[#69784F]"
                        }`}
                      >
                        {MISSION_PRIORITY[id]}
                      </span>

                      <p
                        className={`mt-2 text-[7px] font-semibold uppercase tracking-[0.12em] ${
                          status === "READY"
                            ? "text-[#69784F]"
                            : status === "NOT_READY"
                              ? "text-[#B95F46]"
                              : status === "UNKNOWN"
                                ? "text-[#A69A89]"
                                : "text-[#927B66]"
                        }`}
                      >
                        {status === "CONDITIONALLY_READY" ? "CONDITIONAL" : status.replace(/_/g, " ")}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </article>
        </section>

        {/* Status bar */}
        <section className="grid overflow-hidden rounded-2xl border border-[#DED2C0] bg-[#EEE5D7] sm:grid-cols-3">
          <div className="flex items-center gap-3 border-b border-[#DED2C0] px-5 py-4 sm:border-b-0 sm:border-r">
            <CheckCircle2 className="h-5 w-5 text-[#69784F]" strokeWidth={1.5} />
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#6F5B4A]">Telemetry</p>
              <p className="mt-1 text-[10px] text-[#978575]">
                {loading ? "…" : `${totalCount} assets monitored`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 border-b border-[#DED2C0] px-5 py-4 sm:border-b-0 sm:border-r">
            <Wrench className="h-5 w-5 text-[#B95F46]" strokeWidth={1.5} />
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#6F5B4A]">Maintenance</p>
              <p className="mt-1 text-[10px] text-[#978575]">
                {maintenanceCount === null ? "…" : `${maintenanceCount} recommendations queued`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 px-5 py-4">
            <ShieldCheck className="h-5 w-5 text-[#69784F]" strokeWidth={1.5} />
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#6F5B4A]">Evidence Layer</p>
              <p className="mt-1 text-[10px] text-[#978575]">All recommendations traceable</p>
            </div>
          </div>
        </section>
      </div>
    </>
  );
}

// ── App router ─────────────────────────────────────────────────────────────

type Page = "dashboard" | "assets" | "predictions" | "maintenance" | "ibm-bob";

function App() {
  const [currentPage, setCurrentPage] = useState<Page>("dashboard");

  const renderPage = () => {
    switch (currentPage) {
      case "assets":
        return <Assets />;
      case "predictions":
        return <Predictions />;
      case "maintenance":
        return <Maintenance />;
      case "ibm-bob":
        return <IBMBob />;
      case "dashboard":
      default:
        return <Dashboard />;
    }
  };

  return (
    <AppShell currentPage={currentPage} onNavigate={(p) => setCurrentPage(p as Page)}>
      {renderPage()}
    </AppShell>
  );
}

export default App;