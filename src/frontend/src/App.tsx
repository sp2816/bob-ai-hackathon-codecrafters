import {
  Activity,
  CheckCircle2,
  Clock3,
  RefreshCw,
  Shield,
  ShieldCheck,
  TriangleAlert,
  Wrench,
  Zap,
} from "lucide-react";
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

function getBestMissionReadiness(results: ApiReadinessResult[]): { status: string; score: number | null } {
  if (results.length === 0) return { status: "UNKNOWN", score: null };

  const latestByAsset = new Map<string, ApiReadinessResult>();
  for (const r of results) {
    if (!latestByAsset.has(r.asset_id) || new Date(r.timestamp) > new Date(latestByAsset.get(r.asset_id)!.timestamp)) {
      latestByAsset.set(r.asset_id, r);
    }
  }
  const latestResults = Array.from(latestByAsset.values());

  const ready = latestResults.filter((r) => r.readiness_status === "READY");
  if (ready.length > 0) return { status: "READY", score: Math.min(...ready.map((r) => r.readiness_score)) };

  const cond = latestResults.filter((r) => r.readiness_status === "CONDITIONALLY_READY");
  if (cond.length > 0) return { status: "CONDITIONALLY_READY", score: Math.min(...cond.map((r) => r.readiness_score)) };

  const notReady = latestResults.filter((r) => r.readiness_status === "NOT_READY");
  if (notReady.length > 0) return { status: "NOT_READY", score: Math.min(...notReady.map((r) => r.readiness_score)) };

  return { status: "UNKNOWN", score: null };
}

// ── Mini health sparkline ───────────────────────────────────────────────────
function MiniHealthChart() {
  return (
    <div style={{ color: "var(--brand-500)" }}>
      <svg viewBox="0 0 220 60" className="h-[56px] w-full" preserveAspectRatio="none" aria-label="Fleet health trend">
        <defs>
          <linearGradient id="healthFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--brand-500)" stopOpacity="0.35" />
            <stop offset="100%" stopColor="var(--brand-500)" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path
          d="M0 48 C18 51, 25 38, 42 41 C58 45, 64 26, 82 31 C97 35, 103 20, 120 26 C137 33, 142 14, 159 20 C177 26, 186 6, 202 12 C209 15, 214 7, 220 4 L220 60 L0 60 Z"
          fill="url(#healthFill)"
        />
        <path
          d="M0 48 C18 51, 25 38, 42 41 C58 45, 64 26, 82 31 C97 35, 103 20, 120 26 C137 33, 142 14, 159 20 C177 26, 186 6, 202 12 C209 15, 214 7, 220 4"
          fill="none"
          stroke="var(--brand-500)"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        <circle cx="220" cy="4" r="3.5" fill="var(--brand-500)" />
        <circle cx="220" cy="4" r="6" fill="var(--brand-500)" fillOpacity="0.2" />
      </svg>
    </div>
  );
}

// ── Readiness Ring ─────────────────────────────────────────────────────────
function ReadinessRing({ score }: { score: number }) {
  const radius = 48;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - score / 100);
  const color = score >= 70 ? "var(--success-text)" : score >= 40 ? "var(--warning-text)" : "var(--danger-text)";

  return (
    <div className="relative flex h-[116px] w-[116px] items-center justify-center">
      <svg viewBox="0 0 116 116" className="absolute inset-0 h-full w-full -rotate-90">
        <circle cx="58" cy="58" r={radius} fill="none" stroke="var(--border-strong)" strokeWidth="8" />
        <circle
          cx="58"
          cy="58"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="relative text-center">
        <div className="text-[26px] font-bold leading-none tracking-[-0.04em]" style={{ color }}>
          {score}%
        </div>
        <div className="mt-1 text-[8px] font-semibold uppercase tracking-[0.14em]" style={{ color: "var(--text-muted)" }}>
          Ready
        </div>
      </div>
    </div>
  );
}

// ── KPI Card ───────────────────────────────────────────────────────────────
function KpiCard({
  label,
  value,
  sublabel,
  icon: Icon,
  iconVariant = "brand",
  valueColor,
  loading,
}: {
  label: string;
  value: string | number;
  sublabel?: string;
  icon: React.ElementType;
  iconVariant?: "brand" | "success" | "warning" | "danger" | "info";
  valueColor?: string;
  loading?: boolean;
}) {
  const iconClass = `icon-container-${iconVariant}`;
  return (
    <article
      className="card rounded-xl p-5"
      style={{ transition: "box-shadow 200ms ease, transform 200ms ease" }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.transform = "translateY(-2px)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.transform = "translateY(0)";
      }}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <p className="eyebrow">{label}</p>
          <div
            className="mt-3 text-[36px] font-bold leading-none tracking-[-0.05em]"
            style={{ color: valueColor ?? "var(--text-primary)" }}
          >
            {loading ? <span style={{ color: "var(--text-muted)" }}>—</span> : value}
          </div>
          {sublabel && (
            <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
              {loading ? "Loading…" : sublabel}
            </p>
          )}
        </div>
        <div className={iconClass}>
          <Icon className="h-5 w-5" strokeWidth={1.8} />
        </div>
      </div>
    </article>
  );
}

// ── Dashboard ──────────────────────────────────────────────────────────────

function Dashboard() {
  const [summary, setSummary] = useState<ApiFleetSummary | null>(null);
  const [assets, setAssets] = useState<ApiAsset[]>([]);
  const [missionReadiness, setMissionReadiness] = useState<
    Array<{ mission_id: string; status: string; score: number | null }>
  >([]);
  const [maintenanceCount, setMaintenanceCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [runMsg, setRunMsg] = useState<string | null>(null);
  const [runMsgType, setRunMsgType] = useState<"success" | "danger">("success");

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

      const resolved: Array<{ mission_id: string; status: string; score: number | null }> = [];
      MISSION_IDS.forEach((id, i) => {
        const r = msnResults[i];
        if (r?.status === "fulfilled") {
          resolved.push({ mission_id: id, ...getBestMissionReadiness(r.value) });
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
      setRunMsg("ML + Readiness pipelines refreshed successfully.");
      setRunMsgType("success");
      await fetchAll();
    } catch {
      setRunMsg("Pipeline failed. Ensure the backend is running.");
      setRunMsgType("danger");
    } finally {
      setRunning(false);
    }
  };

  const readyCount    = summary?.counts.READY ?? 0;
  const notReadyCount = summary?.counts.NOT_READY ?? 0;
  const condCount     = summary?.counts.CONDITIONALLY_READY ?? 0;
  const totalCount    = summary?.total ?? 0;

  const fleetHealthPct    = totalCount > 0 ? Math.round((readyCount / totalCount) * 100) : 0;
  const readyMissions     = missionReadiness.filter((m) => m.status === "READY").length;
  const missionReadinessPct =
    missionReadiness.length > 0 ? Math.round((readyMissions / missionReadiness.length) * 100) : 0;

  const statusBadgeForMission = (status: string) => {
    if (status === "READY") return "badge-ready";
    if (status === "NOT_READY") return "badge-not-ready";
    if (status === "CONDITIONALLY_READY") return "badge-medium";
    return "badge-neutral";
  };

  return (
    <>
      <div className="space-y-6">
        {/* Page header */}
        <section className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <p className="eyebrow">Mission Control</p>
            <h1 className="page-title mt-2">Dashboard</h1>
            <p className="body-text mt-2 max-w-xl">
              Fleet health, mission readiness, predictive risk, and maintenance intelligence.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleRunAll}
              disabled={running}
              className="btn-ai-sm"
            >
              <Zap className="h-3.5 w-3.5" />
              {running ? "Running…" : "Refresh All"}
            </button>
            <button
              type="button"
              onClick={fetchAll}
              className="btn-secondary-sm"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Reload
            </button>
          </div>
        </section>

        {/* Run message banner */}
        {runMsg && (
          <div className={runMsgType === "success" ? "banner-success" : "banner-danger"}>
            {runMsg}
          </div>
        )}

        {/* KPI Cards row */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard
            label="Total Assets"
            value={totalCount}
            sublabel={`${totalCount} assets monitored`}
            icon={Shield}
            iconVariant="brand"
            loading={loading}
          />
          <KpiCard
            label="Ready"
            value={readyCount}
            sublabel={`${fleetHealthPct}% fleet health`}
            icon={CheckCircle2}
            iconVariant="success"
            valueColor="var(--success-text)"
            loading={loading}
          />
          <KpiCard
            label="Conditionally Ready"
            value={condCount}
            sublabel="Require attention"
            icon={Activity}
            iconVariant="warning"
            valueColor="var(--warning-text)"
            loading={loading}
          />
          <KpiCard
            label="Not Ready"
            value={notReadyCount}
            sublabel="Immediate action needed"
            icon={TriangleAlert}
            iconVariant="danger"
            valueColor="var(--danger-text)"
            loading={loading}
          />
        </section>

        {/* Fleet health + mission readiness */}
        <section className="grid gap-4 lg:grid-cols-3">

          {/* Fleet health card — wide */}
          <article className="card rounded-xl lg:col-span-2">
            <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: "1px solid var(--border-default)" }}>
              <div>
                <p className="eyebrow">Fleet</p>
                <h2 className="card-title mt-1">Asset Health Overview</h2>
              </div>
              <Activity className="h-5 w-5" style={{ color: "var(--text-muted)" }} strokeWidth={1.5} />
            </div>

            {loading && (
              <div className="px-5 py-6 text-center text-sm" style={{ color: "var(--text-muted)" }}>
                Loading assets…
              </div>
            )}

            <div>
              {assets.map((asset) => {
                const healthPct = asset.readiness_score !== null ? Math.round(asset.readiness_score * 100) : 50;
                const isReady = asset.current_status === "READY";
                const isNotReady = asset.current_status === "NOT_READY";

                const fillClass = isReady
                  ? "progress-fill-success"
                  : isNotReady
                  ? "progress-fill-danger"
                  : "progress-fill-warning";

                const dotClass = isReady
                  ? "status-dot-ready"
                  : isNotReady
                  ? "status-dot-danger"
                  : "status-dot-warning";

                return (
                  <div
                    key={asset.asset_id}
                    className="px-5 py-3.5 transition-colors duration-100"
                    style={{ borderBottom: "1px solid var(--border-subtle)" }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--surface-elevated)"; }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = ""; }}
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex min-w-0 items-center gap-2.5">
                        <span className={dotClass} />
                        <span className="font-mono text-[12px] font-semibold" style={{ color: "var(--text-primary)" }}>
                          {asset.asset_id}
                        </span>
                        <span className="hidden text-xs sm:inline" style={{ color: "var(--text-muted)" }}>
                          {asset.asset_name}
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-[18px] font-bold leading-none tracking-[-0.04em]" style={{
                          color: isReady ? "var(--success-text)" : isNotReady ? "var(--danger-text)" : "var(--warning-text)"
                        }}>
                          {healthPct}%
                        </span>
                        <span className={`badge-sm ${isReady ? "badge-ready" : isNotReady ? "badge-not-ready" : "badge-conditional"}`}
                          style={{ padding: "2px 8px" }}>
                          {asset.current_status.replace(/_/g, " ")}
                        </span>
                      </div>
                    </div>
                    <div className="progress-track mt-2.5">
                      <div className={fillClass} style={{ width: `${Math.max(healthPct, 2)}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </article>

          {/* Mission readiness card */}
          <article className="card rounded-xl">
            <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: "1px solid var(--border-default)" }}>
              <div>
                <p className="eyebrow">Schedule</p>
                <h2 className="card-title mt-1">Mission Readiness</h2>
              </div>
              <Clock3 className="h-5 w-5" style={{ color: "var(--text-muted)" }} strokeWidth={1.5} />
            </div>

            {/* Readiness ring */}
            <div className="flex flex-col items-center px-5 py-5" style={{ borderBottom: "1px solid var(--border-default)" }}>
              {!loading && <ReadinessRing score={missionReadinessPct} />}
              {loading && (
                <div className="flex h-[116px] items-center text-sm" style={{ color: "var(--text-muted)" }}>
                  Loading…
                </div>
              )}
              <p className="mt-3 text-xs" style={{ color: "var(--text-muted)" }}>
                {loading ? "" : `${readyMissions} / ${missionReadiness.length} missions ready`}
              </p>
            </div>

            {/* Mission list */}
            <div>
              {MISSION_IDS.map((id) => {
                const result = missionReadiness.find((m) => m.mission_id === id);
                const status = result?.status ?? "UNKNOWN";
                const score = result?.score;
                const priority = MISSION_PRIORITY[id];

                return (
                  <div
                    key={id}
                    className="grid grid-cols-[1fr_auto] items-center gap-3 px-5 py-3"
                    style={{ borderBottom: "1px solid var(--border-subtle)" }}
                  >
                    <div>
                      <p className="text-[13px] font-semibold" style={{ color: "var(--text-primary)" }}>
                        {MISSION_NAMES[id]}
                      </p>
                      <div className="mt-0.5 flex items-center gap-2">
                        <span className="font-mono text-[10px]" style={{ color: "var(--text-muted)" }}>
                          {id}
                        </span>
                        {score !== undefined && score !== null && (
                          <span className="text-[10px] font-semibold" style={{ color: "var(--text-primary)" }}>
                            Score: {Math.round(score * 100)}%
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`badge-sm ${
                        priority === "HIGH" ? "badge-high" : priority === "MEDIUM" ? "badge-medium" : "badge-low"
                      }`} style={{ padding: "2px 8px" }}>
                        {priority}
                      </span>
                      <p className="mt-1 text-[10px] font-semibold uppercase tracking-[0.08em]" style={{
                        color: status === "READY" ? "var(--success-text)" : status === "NOT_READY" ? "var(--danger-text)" : "var(--warning-text)"
                      }}>
                        {status === "CONDITIONALLY_READY" ? "CONDITIONAL" : status.replace(/_/g, " ")}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </article>
        </section>

        {/* Fleet health sparkline + quick stats */}
        <section className="grid gap-4 lg:grid-cols-3">
          {/* Fleet health trend */}
          <article className="card rounded-xl p-5 lg:col-span-2">
            <div className="flex items-start justify-between">
              <div>
                <p className="eyebrow">Fleet Health</p>
                <div className="mt-2 flex items-baseline gap-3">
                  <span className="text-[40px] font-bold leading-none tracking-[-0.05em]" style={{ color: "var(--text-brand)" }}>
                    {loading ? "—" : `${fleetHealthPct}%`}
                  </span>
                  <span className="text-sm" style={{ color: "var(--text-muted)" }}>
                    {loading ? "" : `${readyCount} / ${totalCount} READY`}
                  </span>
                </div>
              </div>
              <div className="icon-container-brand">
                <Activity className="h-5 w-5" strokeWidth={1.8} />
              </div>
            </div>
            <div className="mt-4">
              <MiniHealthChart />
            </div>
            <div className="mt-2 flex items-center gap-1.5">
              <span className="status-dot-brand" />
              <span className="text-[11px]" style={{ color: "var(--text-muted)" }}>
                Fleet health trend (decorative indicator)
              </span>
            </div>
          </article>

          {/* Quick stats column */}
          <div className="space-y-4">
            <article className="card rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="icon-container-success h-9 w-9">
                  <ShieldCheck className="h-4.5 w-4.5" strokeWidth={1.8} />
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>
                    Telemetry
                  </p>
                  <p className="mt-0.5 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                    {loading ? "…" : `${totalCount} assets monitored`}
                  </p>
                </div>
              </div>
            </article>

            <article className="card rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="icon-container-warning h-9 w-9">
                  <Wrench className="h-4.5 w-4.5" strokeWidth={1.8} />
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>
                    Maintenance
                  </p>
                  <p className="mt-0.5 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                    {maintenanceCount === null ? "…" : `${maintenanceCount} recommendations`}
                  </p>
                </div>
              </div>
            </article>

            <article className="card rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="icon-container-info h-9 w-9">
                  <ShieldCheck className="h-4.5 w-4.5" strokeWidth={1.8} />
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>
                    Evidence Layer
                  </p>
                  <p className="mt-0.5 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                    All traceable
                  </p>
                </div>
              </div>
            </article>
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
      case "assets":      return <Assets />;
      case "predictions": return <Predictions />;
      case "maintenance": return <Maintenance />;
      case "ibm-bob":     return <IBMBob />;
      case "dashboard":
      default:            return <Dashboard />;
    }
  };

  return (
    <AppShell currentPage={currentPage} onNavigate={(p) => setCurrentPage(p as Page)}>
      {renderPage()}
    </AppShell>
  );
}

export default App;