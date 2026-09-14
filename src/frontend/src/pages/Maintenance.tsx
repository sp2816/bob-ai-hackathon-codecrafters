import {
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  RefreshCw,
  TriangleAlert,
  Wrench,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";
import { getMaintenanceRecommendations, runReadinessPipeline } from "../services/api";
import type { ApiMaintenanceRecommendation } from "../types/api";

function UrgencyBadge({ urgency }: { urgency: string }) {
  if (urgency === "HIGH") return <span className="badge-high">{urgency}</span>;
  if (urgency === "MEDIUM") return <span className="badge-medium">{urgency}</span>;
  return <span className="badge-low">{urgency}</span>;
}

function PriorityBadge({ priority }: { priority: number }) {
  const isTop = priority <= 2;
  return (
    <span
      className="badge"
      style={
        isTop
          ? {
              backgroundColor: "rgba(175,23,99,0.12)",
              border: "1px solid rgba(175,23,99,0.3)",
              color: "var(--text-brand)",
            }
          : {
              backgroundColor: "var(--surface-elevated)",
              border: "1px solid var(--border-default)",
              color: "var(--text-secondary)",
            }
      }
    >
      Priority #{priority}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "COMPLETED") return <span className="badge-ready">{status}</span>;
  if (status === "OVERDUE")   return <span className="badge-not-ready">{status}</span>;
  return <span className="badge-neutral">{status}</span>;
}

/**
 * Deduplicate recommendations — keep the highest-priority entry per
 * (asset_id, component_id) pair.
 */
function deduplicateRecs(recs: ApiMaintenanceRecommendation[]): ApiMaintenanceRecommendation[] {
  const best = new Map<string, ApiMaintenanceRecommendation>();
  for (const r of recs) {
    const key = `${r.asset_id}|${r.component_id}`;
    const existing = best.get(key);
    if (!existing || r.priority < existing.priority) {
      best.set(key, r);
    }
  }
  return Array.from(best.values()).sort((a, b) => a.priority - b.priority);
}

function Maintenance() {
  const [recs, setRecs] = useState<ApiMaintenanceRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [runMsg, setRunMsg] = useState<string | null>(null);
  const [runMsgType, setRunMsgType] = useState<"success" | "danger">("success");

  const fetchRecs = () => {
    setLoading(true);
    setError(null);
    getMaintenanceRecommendations()
      .then((data) => setRecs(deduplicateRecs(data)))
      .catch(() => setError("Unable to load maintenance recommendations from the backend."))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchRecs(); }, []);

  const handleRunReadiness = async () => {
    setRunning(true);
    setRunMsg(null);
    try {
      const result = await runReadinessPipeline();
      const gen = result.generated;
      setRunMsg(
        `Readiness pipeline complete — ${gen.readiness_results_generated ?? 0} readiness results, ${gen.maintenance_recommendations_generated ?? 0} recommendations generated.`,
      );
      setRunMsgType("success");
      fetchRecs();
    } catch {
      setRunMsg("Failed to run readiness pipeline. Ensure the backend is running.");
      setRunMsgType("danger");
    } finally {
      setRunning(false);
    }
  };

  const highUrgency = recs.filter((r) => r.urgency === "HIGH").length;
  const medUrgency  = recs.filter((r) => r.urgency === "MEDIUM").length;
  const lowUrgency  = recs.filter((r) => r.urgency === "LOW").length;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <section className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <p className="eyebrow">Fleet Maintenance</p>
          <h1 className="page-title mt-2">Maintenance</h1>
          <p className="body-text mt-2 max-w-xl">
            Backend-computed maintenance recommendations from the Maintenance Priority Engine.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleRunReadiness}
            disabled={running}
            className="btn-primary"
          >
            <Zap className="h-4 w-4" />
            {running ? "Running…" : "Run Readiness"}
          </button>
          <button
            type="button"
            onClick={fetchRecs}
            className="btn-secondary-sm"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
        </div>
      </section>

      {runMsg && (
        <div className={runMsgType === "success" ? "banner-success" : "banner-danger"}>
          {runMsg}
        </div>
      )}

      {/* Summary KPI cards */}
      <section className="grid gap-4 md:grid-cols-3">
        <article
          className="card rounded-xl p-5"
          style={{ border: "1px solid var(--danger-border)", transition: "transform 200ms ease" }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.transform = "translateY(-2px)"; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.transform = ""; }}
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow" style={{ color: "var(--danger-text)" }}>High Urgency</p>
              <div className="mt-3 text-[40px] font-bold leading-none tracking-[-0.05em]" style={{ color: "var(--danger-text)" }}>
                {loading ? "—" : highUrgency}
              </div>
              <p className="mt-2 text-xs" style={{ color: "var(--danger-text)", opacity: 0.7 }}>
                Immediate attention required
              </p>
            </div>
            <div className="icon-container-danger">
              <TriangleAlert className="h-5 w-5" strokeWidth={1.8} />
            </div>
          </div>
        </article>

        <article
          className="card rounded-xl p-5"
          style={{ transition: "transform 200ms ease" }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.transform = "translateY(-2px)"; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.transform = ""; }}
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">Medium Urgency</p>
              <div className="mt-3 text-[40px] font-bold leading-none tracking-[-0.05em]" style={{ color: "var(--warning-text)" }}>
                {loading ? "—" : medUrgency}
              </div>
              <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
                Planned maintenance events
              </p>
            </div>
            <div className="icon-container-warning">
              <CalendarClock className="h-5 w-5" strokeWidth={1.8} />
            </div>
          </div>
        </article>

        <article
          className="card rounded-xl p-5"
          style={{ transition: "transform 200ms ease" }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.transform = "translateY(-2px)"; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.transform = ""; }}
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">Low Urgency</p>
              <div className="mt-3 text-[40px] font-bold leading-none tracking-[-0.05em]" style={{ color: "var(--success-text)" }}>
                {loading ? "—" : lowUrgency}
              </div>
              <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
                Within planned service cycle
              </p>
            </div>
            <div className="icon-container-success">
              <CheckCircle2 className="h-5 w-5" strokeWidth={1.8} />
            </div>
          </div>
        </article>
      </section>

      {/* Recommendations list */}
      <section className="card rounded-xl overflow-hidden">
        <div
          className="flex items-center justify-between px-6 py-4"
          style={{ borderBottom: "1px solid var(--border-default)" }}
        >
          <div>
            <p className="eyebrow">Maintenance Queue</p>
            <h2 className="section-title mt-1">Prioritized Recommendations</h2>
            <p className="body-text mt-1 text-xs">
              Ranked by the Maintenance Priority Engine — failure risk, criticality, mission impact, and urgency drive ranking.
            </p>
          </div>
          <Wrench className="h-5 w-5" style={{ color: "var(--text-muted)" }} strokeWidth={1.5} />
        </div>

        {loading && (
          <div className="px-6 py-10 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            Loading recommendations…
          </div>
        )}

        {error && (
          <div className="px-6 py-10 text-center">
            <p className="text-sm" style={{ color: "var(--danger-text)" }}>{error}</p>
            <button type="button" onClick={fetchRecs} className="mt-3 text-xs font-semibold underline" style={{ color: "var(--text-brand)" }}>
              Retry
            </button>
          </div>
        )}

        {!loading && !error && recs.length === 0 && (
          <div className="px-6 py-10 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            No recommendations found. Click <strong style={{ color: "var(--text-brand)" }}>Run Readiness</strong> to generate them.
          </div>
        )}

        {!loading && !error && (
          <div>
            {recs.map((rec) => {
              const isTopPriority = rec.priority <= 2;
              const isHighUrgency = rec.urgency === "HIGH";

              return (
                <article
                  key={rec.recommendation_id}
                  className="px-6 py-5 transition-colors duration-100"
                  style={{
                    borderBottom: "1px solid var(--border-subtle)",
                    ...(isTopPriority
                      ? { borderLeft: "3px solid var(--brand-500)" }
                      : isHighUrgency
                      ? { borderLeft: "3px solid var(--danger-text)" }
                      : {}),
                  }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--surface-elevated)"; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = ""; }}
                >
                  {/* Header */}
                  <div className="flex flex-wrap items-center gap-2.5">
                    <ClipboardCheck
                      className="h-[18px] w-[18px] shrink-0"
                      style={{
                        color: isHighUrgency ? "var(--danger-text)" : isTopPriority ? "var(--text-brand)" : "var(--text-muted)",
                      }}
                      strokeWidth={1.8}
                    />
                    <div>
                      <p className="font-mono text-[13px] font-bold" style={{ color: "var(--text-primary)" }}>
                        {rec.recommendation_id}
                      </p>
                      <p className="mt-0.5 text-xs" style={{ color: "var(--text-muted)" }}>
                        {rec.asset_id} · {rec.component_id}
                      </p>
                    </div>
                    <PriorityBadge priority={rec.priority} />
                    <UrgencyBadge urgency={rec.urgency} />
                    <StatusBadge status={rec.status} />
                  </div>

                  {/* Metrics grid */}
                  <div className="mt-4 grid gap-3 sm:grid-cols-3">
                    <div
                      className="rounded-lg p-3"
                      style={{ backgroundColor: "var(--surface-elevated)", border: "1px solid var(--border-default)" }}
                    >
                      <p className="data-label">Risk</p>
                      <p
                        className="mt-1.5 text-[15px] font-bold"
                        style={{
                          color:
                            rec.risk === "HIGH"
                              ? "var(--danger-text)"
                              : rec.risk === "MEDIUM"
                              ? "var(--warning-text)"
                              : "var(--success-text)",
                        }}
                      >
                        {rec.risk}
                      </p>
                    </div>

                    <div
                      className="rounded-lg p-3"
                      style={{ backgroundColor: "var(--surface-elevated)", border: "1px solid var(--border-default)" }}
                    >
                      <p className="data-label">Mission Impact</p>
                      <p className="mt-1.5 text-[13px] font-semibold" style={{ color: "var(--text-primary)" }}>
                        {rec.mission_impact}
                      </p>
                    </div>

                    <div
                      className="rounded-lg p-3"
                      style={{ backgroundColor: "var(--surface-elevated)", border: "1px solid var(--border-default)" }}
                    >
                      <p className="data-label">Urgency</p>
                      <p
                        className="mt-1.5 text-[15px] font-bold"
                        style={{
                          color:
                            rec.urgency === "HIGH"
                              ? "var(--danger-text)"
                              : rec.urgency === "MEDIUM"
                              ? "var(--warning-text)"
                              : "var(--success-text)",
                        }}
                      >
                        {rec.urgency}
                      </p>
                    </div>
                  </div>

                  {/* Action box */}
                  <div
                    className="mt-3 rounded-lg px-4 py-3"
                    style={{ backgroundColor: "var(--surface-elevated)", border: "1px solid var(--border-default)" }}
                  >
                    <p className="data-label">Recommended Action</p>
                    <p className="mt-1.5 text-[13px] font-medium leading-5" style={{ color: "var(--text-primary)" }}>
                      {rec.action}
                    </p>
                    {rec.reason && (
                      <p className="mt-1.5 text-xs leading-5" style={{ color: "var(--text-muted)" }}>
                        {rec.reason}
                      </p>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      {/* Footer */}
      <section
        className="grid overflow-hidden rounded-xl md:grid-cols-2"
        style={{ backgroundColor: "var(--surface-card)", border: "1px solid var(--border-default)" }}
      >
        <div className="flex items-center gap-3 px-5 py-4">
          <div className="icon-container-success h-9 w-9">
            <CheckCircle2 className="h-4 w-4" strokeWidth={1.8} />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>
              Maintenance Control
            </p>
            <p className="mt-0.5 text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              Priority Engine operational
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 border-t px-5 py-4 md:border-l md:border-t-0" style={{ borderColor: "var(--border-default)" }}>
          <div className="icon-container-brand h-9 w-9">
            <CalendarClock className="h-4 w-4" strokeWidth={1.8} />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>
              Evidence-Backed
            </p>
            <p className="mt-0.5 text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              Failure risk, mission impact &amp; urgency drive ranking
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Maintenance;
