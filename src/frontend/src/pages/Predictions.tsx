import {
  Activity,
  ArrowUpRight,
  CheckCircle2,
  RefreshCw,
  ShieldAlert,
  TriangleAlert,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";
import { getPredictions, getAnomalies, runMlPipeline } from "../services/api";
import type { ApiPrediction, ApiAnomaly } from "../types/api";

function riskTextColor(risk: string) {
  if (risk === "HIGH") return "text-[#B95F46]";
  if (risk === "MEDIUM") return "text-[#9A7650]";
  return "text-[#69784F]";
}

function riskBgColor(risk: string) {
  if (risk === "HIGH") return "bg-[#F1D9D0]";
  if (risk === "MEDIUM") return "bg-[#EFE3CE]";
  return "bg-[#E0E7D6]";
}

function riskIcon(risk: string) {
  if (risk === "HIGH") return <TriangleAlert className="h-4 w-4 text-[#B95F46]" strokeWidth={1.7} />;
  if (risk === "MEDIUM") return <ShieldAlert className="h-4 w-4 text-[#9A7650]" strokeWidth={1.7} />;
  return <CheckCircle2 className="h-4 w-4 text-[#69784F]" strokeWidth={1.7} />;
}

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

function Predictions() {
  const [predictions, setPredictions] = useState<ApiPrediction[]>([]);
  const [anomalies, setAnomalies] = useState<ApiAnomaly[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [runMsg, setRunMsg] = useState<string | null>(null);

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
      fetchData();
    } catch {
      setRunMsg("Failed to run ML pipeline. Ensure the backend is running.");
    } finally {
      setRunning(false);
    }
  };

  const deduped = predictions;
  const highRisk = deduped.filter((p) => p.risk_category === "HIGH").length;
  const medRisk = deduped.filter((p) => p.risk_category === "MEDIUM").length;
  const lowRisk = deduped.filter((p) => p.risk_category === "LOW").length;

  return (
    <div className="space-y-7">
      <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="eyebrow">Predictive Intelligence</p>
          <h1 className="mt-2 text-[42px] font-semibold leading-none tracking-[-0.055em] text-[#3B2A20] sm:text-[48px]">
            Predictions
          </h1>
          <p className="mt-3 max-w-xl text-[13px] leading-6 text-[#806B59]">
            Member 2 ML-generated failure probabilities and anomaly detections across the fleet.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleRunMl}
            disabled={running}
            className="flex items-center gap-1.5 rounded-full border border-[#C2CEAE] bg-[#DDE5D1] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#596842] hover:bg-[#CDD9C1] disabled:opacity-50"
          >
            <Zap className="h-3 w-3" />
            {running ? "Running…" : "Run ML"}
          </button>
          <button
            type="button"
            onClick={fetchData}
            className="flex items-center gap-1.5 rounded-full border border-[#D8CBB9] bg-[#EEE5D7] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#806B59] hover:bg-[#E5D8C5]"
          >
            <RefreshCw className="h-3 w-3" />
            Refresh
          </button>
        </div>
      </section>

      {runMsg && (
        <div className="rounded-xl border border-[#C2CEAE] bg-[#DDE5D1] px-4 py-3 text-[11px] text-[#596842]">
          {runMsg}
        </div>
      )}

      {/* Summary cards */}
      <section className="grid gap-5 md:grid-cols-3">
        <article className="rounded-2xl border border-[#E1B7A9] bg-[#FBF3EF] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">High Risk</p>
              <div className="mt-4 text-[42px] font-light leading-none tracking-[-0.06em] text-[#B95F46]">
                {loading ? "—" : highRisk}
              </div>
              <p className="mt-3 text-[10px] text-[#A66B5A]">Components requiring intervention</p>
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#F1D9D0]">
              <TriangleAlert className="h-4 w-4 text-[#B95F46]" strokeWidth={1.7} />
            </div>
          </div>
        </article>

        <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">Moderate Risk</p>
              <div className="mt-4 text-[42px] font-light leading-none tracking-[-0.06em] text-[#9A7650]">
                {loading ? "—" : medRisk}
              </div>
              <p className="mt-3 text-[10px] text-[#9B8977]">Closer monitoring recommended</p>
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#EFE3CE]">
              <ShieldAlert className="h-4 w-4 text-[#9A7650]" strokeWidth={1.7} />
            </div>
          </div>
        </article>

        <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">Low Risk</p>
              <div className="mt-4 text-[42px] font-light leading-none tracking-[-0.06em] text-[#69784F]">
                {loading ? "—" : lowRisk}
              </div>
              <p className="mt-3 text-[10px] text-[#9B8977]">Operating within forecast</p>
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#E0E7D6]">
              <CheckCircle2 className="h-4 w-4 text-[#69784F]" strokeWidth={1.7} />
            </div>
          </div>
        </article>
      </section>

      {/* Prediction list */}
      <section className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
        <div className="flex items-center justify-between px-6 py-5">
          <div>
            <p className="eyebrow">Fleet Forecast</p>
            <h2 className="mt-2 text-[21px] font-semibold tracking-[-0.025em] text-[#4A3528]">
              Asset risk outlook
            </h2>
            <p className="mt-2 text-[11px] text-[#9B8977]">
              Member 2 Random Forest failure probabilities — not RUL estimates.
            </p>
          </div>
          <Activity className="h-5 w-5 text-[#806B59]" strokeWidth={1.5} />
        </div>

        {loading && (
          <div className="border-t border-[#E8DED1] px-6 py-8 text-center text-[12px] text-[#9B8977]">
            Loading predictions…
          </div>
        )}

        {error && (
          <div className="border-t border-[#E8DED1] px-6 py-8 text-center">
            <p className="text-[12px] text-[#B95F46]">{error}</p>
            <button type="button" onClick={fetchData} className="mt-3 text-[11px] font-semibold text-[#69784F] underline">
              Retry
            </button>
          </div>
        )}

        {!loading && !error && deduped.length === 0 && (
          <div className="border-t border-[#E8DED1] px-6 py-8 text-center text-[12px] text-[#9B8977]">
            No predictions found. Click "Run ML" to generate predictions.
          </div>
        )}

        {!loading && !error && (
          <div>
            {deduped.map((pred) => {
              const anomaly = anomalyFor(anomalies, pred.asset_id, pred.component_id);
              const riskPct = Math.round(pred.failure_probability * 100);

              return (
                <article key={pred.prediction_id} className="border-t border-[#E8DED1] px-6 py-6">
                  <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-3">
                        {riskIcon(pred.risk_category)}
                        <div>
                          <p className="font-mono text-[12px] font-semibold text-[#4A3528]">{pred.asset_id}</p>
                          <p className="mt-1 text-[10px] text-[#9B8977]">{pred.component_id}</p>
                        </div>
                        <span
                          className={`ml-2 rounded-full px-3 py-1.5 text-[8px] font-semibold uppercase tracking-[0.12em] ${riskBgColor(pred.risk_category)} ${riskTextColor(pred.risk_category)}`}
                        >
                          {pred.risk_category} risk
                        </span>
                      </div>

                      <div className="mt-5 grid gap-4 sm:grid-cols-3">
                        <div>
                          <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                            Failure probability
                          </p>
                          <p className="mt-2 text-[12px] font-semibold text-[#5D4535]">{riskPct}%</p>
                        </div>

                        <div>
                          <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                            Anomaly status
                          </p>
                          <div className="mt-2 flex items-center gap-2">
                            {anomaly ? (
                              <>
                                <ArrowUpRight
                                  className={`h-4 w-4 ${anomaly.anomaly_status === "HIGH" ? "rotate-90 text-[#B95F46]" : "text-[#69784F]"}`}
                                  strokeWidth={1.5}
                                />
                                <p className="text-[12px] text-[#5D4535]">
                                  {anomaly.anomaly_status} · {anomaly.sensor}
                                </p>
                              </>
                            ) : (
                              <p className="text-[12px] text-[#9B8977]">No anomaly</p>
                            )}
                          </div>
                        </div>

                        <div>
                          <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                            Severity
                          </p>
                          <p className="mt-2 text-[12px] text-[#5D4535]">
                            {anomaly ? anomaly.anomaly_severity : "LOW"}
                          </p>
                        </div>
                      </div>

                      <div className="mt-5">
                        <div className="flex items-center justify-between">
                          <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                            Failure probability
                          </p>
                          <span className="text-[10px] font-medium text-[#806B59]">{riskPct}%</span>
                        </div>
                        <div className="mt-2 h-2 overflow-hidden rounded-full bg-[#E5DACA]">
                          <div
                            className={`h-full rounded-full ${pred.risk_category === "HIGH" ? "bg-[#B95F46]" : pred.risk_category === "MEDIUM" ? "bg-[#9A7650]" : "bg-[#69784F]"}`}
                            style={{ width: `${riskPct}%` }}
                          />
                        </div>
                      </div>

                      <div className="mt-4 rounded-xl border border-[#E4D8C9] bg-[#F5EEE4] px-4 py-3">
                        <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                          Timestamp
                        </p>
                        <p className="mt-1 text-[11px] leading-5 text-[#5D4535]">
                          {new Date(pred.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      <section className="grid gap-0 overflow-hidden rounded-2xl border border-[#DED2C0] bg-[#EEE5D7] md:grid-cols-2">
        <div className="flex items-center gap-3 px-6 py-5">
          <CheckCircle2 className="h-5 w-5 text-[#69784F]" strokeWidth={1.5} />
          <div>
            <p className="text-[13px] font-semibold text-[#4A3528]">Prediction engine operational</p>
            <p className="mt-1 text-[11px] text-[#9B8977]">
              Results are stored and served from the Member 1 backend.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 border-t border-[#DED2C0] px-6 py-5 md:border-l md:border-t-0">
          <Activity className="h-5 w-5 text-[#69784F]" strokeWidth={1.5} />
          <div>
            <p className="text-[13px] font-semibold text-[#4A3528]">Member 2 ML pipeline</p>
            <p className="mt-1 text-[11px] text-[#9B8977]">
              Click "Run ML" to refresh predictions and anomaly detections.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Predictions;
