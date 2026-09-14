import {
  Activity,
  AlertOctagon,
  CheckCircle2,
  RefreshCw,
  ShieldAlert,
  TriangleAlert,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";
import { getPredictions, getAnomalies, runMlPipeline } from "../services/api";
import type { ApiPrediction, ApiAnomaly } from "../types/api";

/** Deduplicate predictions — keep highest failure_probability per component. */
function deduplicatePredictions(preds: ApiPrediction[]): ApiPrediction[] {
  const best = new Map<string, ApiPrediction>();
  for (const p of preds) {
    const key = `${p.asset_id}|${p.component_id}`;
    const existing = best.get(key);
    if (!existing || p.failure_probability > existing.failure_probability) {
      best.set(key, p);
    }
  }
  return Array.from(best.values()).sort((a, b) => b.failure_probability - a.failure_probability);
}

/** Find the most severe anomaly for a component, if any. */
function anomalyFor(anomalies: ApiAnomaly[], assetId: string, componentId: string): ApiAnomaly | undefined {
  return anomalies
    .filter((a) => a.asset_id === assetId && a.component_id === componentId)
    .sort((a, b) => {
      const sev = { HIGH: 3, MEDIUM: 2, LOW: 1 };
      return (sev[b.anomaly_severity] ?? 0) - (sev[a.anomaly_severity] ?? 0);
    })[0];
}

function RiskBadge({ risk }: { risk: string }) {
  if (risk === "HIGH") return <span className="badge-high">{risk} RISK</span>;
  if (risk === "MEDIUM") return <span className="badge-medium">{risk} RISK</span>;
  return <span className="badge-low">{risk} RISK</span>;
}

function SeverityBadge({ severity }: { severity: string }) {
  if (severity === "HIGH") return <span className="badge-high badge-sm">{severity}</span>;
  if (severity === "MEDIUM") return <span className="badge-medium badge-sm">{severity}</span>;
  return <span className="badge-low badge-sm">{severity}</span>;
}

function RiskIcon({ risk }: { risk: string }) {
  if (risk === "HIGH")
    return <TriangleAlert className="h-5 w-5" style={{ color: "var(--danger-text)" }} strokeWidth={1.8} />;
  if (risk === "MEDIUM")
    return <ShieldAlert className="h-5 w-5" style={{ color: "var(--warning-text)" }} strokeWidth={1.8} />;
  return <CheckCircle2 className="h-5 w-5" style={{ color: "var(--success-text)" }} strokeWidth={1.8} />;
}

function Predictions() {
  const [predictions, setPredictions] = useState<ApiPrediction[]>([]);
  const [anomalies, setAnomalies] = useState<ApiAnomaly[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [runMsg, setRunMsg] = useState<string | null>(null);
  const [runMsgType, setRunMsgType] = useState<"success" | "danger">("success");

  const fetchData = () => {
    setLoading(true);
    setError(null);
    Promise.all([getPredictions(), getAnomalies()])
      .then(([preds, anoms]) => {
        setPredictions(deduplicatePredictions(preds));
        setAnomalies(anoms);
      })
      .catch(() => setError("Unable to load predictions from the backend."))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  const handleRunMl = async () => {
    setRunning(true);
    setRunMsg(null);
    try {
      const result = await runMlPipeline();
      setRunMsg(`ML pipeline complete — ${result.stored.predictions ?? 0} predictions, ${result.stored.anomalies ?? 0} anomalies stored.`);
      setRunMsgType("success");
      fetchData();
    } catch {
      setRunMsg("Failed to run ML pipeline. Ensure the backend is running.");
      setRunMsgType("danger");
    } finally {
      setRunning(false);
    }
  };

  const deduped   = predictions;
  const highRisk  = deduped.filter((p) => p.risk_category === "HIGH").length;
  const medRisk   = deduped.filter((p) => p.risk_category === "MEDIUM").length;
  const lowRisk   = deduped.filter((p) => p.risk_category === "LOW").length;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <section className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <p className="eyebrow">Predictive Intelligence</p>
          <h1 className="page-title mt-2">Predictions</h1>
          <p className="body-text mt-2 max-w-xl">
            ML-generated failure probabilities and anomaly detections across the fleet.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleRunMl}
            disabled={running}
            className="btn-ai"
          >
            <Zap className="h-4 w-4" />
            {running ? "Running ML…" : "Run ML Analysis"}
          </button>
          <button
            type="button"
            onClick={fetchData}
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
              <p className="eyebrow" style={{ color: "var(--danger-text)" }}>High Risk</p>
              <div className="mt-3 text-[40px] font-bold leading-none tracking-[-0.05em]" style={{ color: "var(--danger-text)" }}>
                {loading ? "—" : highRisk}
              </div>
              <p className="mt-2 text-xs" style={{ color: "var(--danger-text)", opacity: 0.7 }}>
                Components requiring intervention
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
              <p className="eyebrow">Moderate Risk</p>
              <div className="mt-3 text-[40px] font-bold leading-none tracking-[-0.05em]" style={{ color: "var(--warning-text)" }}>
                {loading ? "—" : medRisk}
              </div>
              <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
                Closer monitoring recommended
              </p>
            </div>
            <div className="icon-container-warning">
              <ShieldAlert className="h-5 w-5" strokeWidth={1.8} />
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
              <p className="eyebrow">Low Risk</p>
              <div className="mt-3 text-[40px] font-bold leading-none tracking-[-0.05em]" style={{ color: "var(--success-text)" }}>
                {loading ? "—" : lowRisk}
              </div>
              <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
                Operating within forecast
              </p>
            </div>
            <div className="icon-container-success">
              <CheckCircle2 className="h-5 w-5" strokeWidth={1.8} />
            </div>
          </div>
        </article>
      </section>

      {/* Prediction cards */}
      <section className="card rounded-xl overflow-hidden">
        <div
          className="flex items-center justify-between px-6 py-4"
          style={{ borderBottom: "1px solid var(--border-default)" }}
        >
          <div>
            <p className="eyebrow">Fleet Forecast</p>
            <h2 className="section-title mt-1">Asset Risk Outlook</h2>
            <p className="body-text mt-1 text-xs">
              Random Forest failure probabilities — not RUL estimates.
            </p>
          </div>
          <Activity className="h-5 w-5" style={{ color: "var(--text-muted)" }} strokeWidth={1.5} />
        </div>

        {loading && (
          <div className="px-6 py-10 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            Loading predictions…
          </div>
        )}

        {error && (
          <div className="px-6 py-10 text-center">
            <p className="text-sm" style={{ color: "var(--danger-text)" }}>{error}</p>
            <button type="button" onClick={fetchData} className="mt-3 text-xs font-semibold underline" style={{ color: "var(--text-brand)" }}>
              Retry
            </button>
          </div>
        )}

        {!loading && !error && deduped.length === 0 && (
          <div className="px-6 py-10 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            No predictions found. Click <strong style={{ color: "var(--text-brand)" }}>Run ML Analysis</strong> to generate predictions.
          </div>
        )}

        {!loading && !error && (
          <div>
            {deduped.map((pred) => {
              const anomaly = anomalyFor(anomalies, pred.asset_id, pred.component_id);
              const riskPct = Math.round(pred.failure_probability * 100);
              const isHigh  = pred.risk_category === "HIGH";
              const isMed   = pred.risk_category === "MEDIUM";

              const fillClass = isHigh
                ? "progress-fill-danger"
                : isMed
                ? "progress-fill-warning"
                : "progress-fill-success";

              return (
                <article
                  key={pred.prediction_id}
                  className="px-6 py-5 transition-colors duration-100"
                  style={{
                    borderBottom: "1px solid var(--border-subtle)",
                    ...(isHigh ? { borderLeft: "3px solid var(--danger-text)" } : {}),
                  }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--surface-elevated)"; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = ""; }}
                >
                  {/* Header row */}
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-3">
                        <RiskIcon risk={pred.risk_category} />
                        <div>
                          <p className="font-mono text-[13px] font-bold" style={{ color: "var(--text-primary)" }}>
                            {pred.asset_id}
                          </p>
                          <p className="mt-0.5 text-xs" style={{ color: "var(--text-muted)" }}>
                            {pred.component_id}
                          </p>
                        </div>
                        <RiskBadge risk={pred.risk_category} />
                        {isHigh && (
                          <span className="badge-sm" style={{
                            padding: "2px 8px",
                            backgroundColor: "var(--danger-bg)",
                            border: "1px solid var(--danger-border)",
                            color: "var(--danger-text)",
                            borderRadius: "4px",
                            fontSize: "10px",
                            fontWeight: 600,
                          }}>
                            ⚠ INTERVENTION REQUIRED
                          </span>
                        )}
                      </div>

                      {/* Metrics grid */}
                      <div className="mt-4 grid gap-4 sm:grid-cols-3">
                        {/* Failure probability */}
                        <div
                          className="rounded-lg p-3"
                          style={{ backgroundColor: "var(--surface-elevated)", border: "1px solid var(--border-default)" }}
                        >
                          <p className="data-label">Failure Probability</p>
                          <p
                            className="mt-1.5 text-[22px] font-bold leading-none tracking-[-0.04em]"
                            style={{
                              color: isHigh ? "var(--danger-text)" : isMed ? "var(--warning-text)" : "var(--success-text)",
                            }}
                          >
                            {riskPct}%
                          </p>
                          <div className="progress-track mt-2.5">
                            <div className={fillClass} style={{ width: `${riskPct}%` }} />
                          </div>
                        </div>

                        {/* Anomaly status */}
                        <div
                          className="rounded-lg p-3"
                          style={{ backgroundColor: "var(--surface-elevated)", border: "1px solid var(--border-default)" }}
                        >
                          <p className="data-label">Anomaly Status</p>
                          {anomaly ? (
                            <div className="mt-1.5">
                              <div className="flex items-center gap-1.5">
                                <AlertOctagon className="h-4 w-4" style={{ color: "var(--warning-text)" }} strokeWidth={1.8} />
                                <span className="text-[13px] font-semibold" style={{ color: "var(--text-primary)" }}>
                                  {anomaly.anomaly_status}
                                </span>
                              </div>
                              <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                                Sensor: {anomaly.sensor}
                              </p>
                            </div>
                          ) : (
                            <div className="mt-1.5 flex items-center gap-1.5">
                              <CheckCircle2 className="h-4 w-4" style={{ color: "var(--success-text)" }} strokeWidth={1.8} />
                              <span className="text-[13px] font-medium" style={{ color: "var(--text-muted)" }}>
                                No anomaly
                              </span>
                            </div>
                          )}
                        </div>

                        {/* Severity */}
                        <div
                          className="rounded-lg p-3"
                          style={{ backgroundColor: "var(--surface-elevated)", border: "1px solid var(--border-default)" }}
                        >
                          <p className="data-label">Anomaly Severity</p>
                          <div className="mt-1.5">
                            <SeverityBadge severity={anomaly ? anomaly.anomaly_severity : "LOW"} />
                            {anomaly && (
                              <p className="mt-1.5 text-xs" style={{ color: "var(--text-muted)" }}>
                                Sensor: {anomaly.sensor}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Timestamp */}
                      <div
                        className="mt-3 rounded-lg px-4 py-2.5"
                        style={{ backgroundColor: "var(--surface-elevated)", border: "1px solid var(--border-default)" }}
                      >
                        <div className="flex items-center gap-2">
                          <span className="data-label">Recorded</span>
                          <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
                            {new Date(pred.timestamp).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      {/* Footer status */}
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
              Prediction engine
            </p>
            <p className="mt-0.5 text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              Results stored via Member 1 backend
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 border-t px-5 py-4 md:border-l md:border-t-0" style={{ borderColor: "var(--border-default)" }}>
          <div className="icon-container-brand h-9 w-9">
            <Activity className="h-4 w-4" strokeWidth={1.8} />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>
              ML Pipeline
            </p>
            <p className="mt-0.5 text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              Click "Run ML Analysis" to refresh
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Predictions;
