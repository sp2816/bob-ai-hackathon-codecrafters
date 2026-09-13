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

function urgencyTextColor(urgency: string) {
  if (urgency === "HIGH") return "text-[#B95F46]";
  if (urgency === "MEDIUM") return "text-[#9A7650]";
  return "text-[#69784F]";
}

function urgencyBgColor(urgency: string) {
  if (urgency === "HIGH") return "bg-[#F1D9D0]";
  if (urgency === "MEDIUM") return "bg-[#EFE3CE]";
  return "bg-[#E0E7D6]";
}

/**
 * Deduplicate recommendations — keep the highest-priority entry per
 * (asset_id, component_id) pair. This handles the case where the DB contains
 * both a legacy seeded REC and a freshly generated REC for the same component.
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
      fetchRecs();
    } catch {
      setRunMsg("Failed to run readiness pipeline. Ensure the backend is running.");
    } finally {
      setRunning(false);
    }
  };

  const highUrgency = recs.filter((r) => r.urgency === "HIGH").length;
  const medUrgency = recs.filter((r) => r.urgency === "MEDIUM").length;
  const lowUrgency = recs.filter((r) => r.urgency === "LOW").length;

  return (
    <div className="space-y-7">
      <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="eyebrow">Fleet Maintenance</p>
          <h1 className="mt-2 text-[42px] font-semibold leading-none tracking-[-0.055em] text-[#3B2A20] sm:text-[48px]">
            Maintenance
          </h1>
          <p className="mt-3 max-w-xl text-[13px] leading-6 text-[#806B59]">
            Backend-computed maintenance recommendations from Member 3's Maintenance Priority Engine.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleRunReadiness}
            disabled={running}
            className="flex items-center gap-1.5 rounded-full border border-[#C2CEAE] bg-[#DDE5D1] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#596842] hover:bg-[#CDD9C1] disabled:opacity-50"
          >
            <Zap className="h-3 w-3" />
            {running ? "Running…" : "Run Readiness"}
          </button>
          <button
            type="button"
            onClick={fetchRecs}
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
              <p className="eyebrow">High Urgency</p>
              <div className="mt-4 text-[42px] font-light leading-none tracking-[-0.06em] text-[#B95F46]">
                {loading ? "—" : highUrgency}
              </div>
              <p className="mt-3 text-[10px] text-[#A66B5A]">Immediate attention required</p>
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#F1D9D0]">
              <TriangleAlert className="h-4 w-4 text-[#B95F46]" strokeWidth={1.7} />
            </div>
          </div>
        </article>

        <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">Medium Urgency</p>
              <div className="mt-4 text-[42px] font-light leading-none tracking-[-0.06em] text-[#9A7650]">
                {loading ? "—" : medUrgency}
              </div>
              <p className="mt-3 text-[10px] text-[#9B8977]">Planned maintenance events</p>
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#EFE3CE]">
              <CalendarClock className="h-4 w-4 text-[#9A7650]" strokeWidth={1.7} />
            </div>
          </div>
        </article>

        <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">Low Urgency</p>
              <div className="mt-4 text-[42px] font-light leading-none tracking-[-0.06em] text-[#69784F]">
                {loading ? "—" : lowUrgency}
              </div>
              <p className="mt-3 text-[10px] text-[#9B8977]">Within planned service cycle</p>
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#E0E7D6]">
              <CheckCircle2 className="h-4 w-4 text-[#69784F]" strokeWidth={1.7} />
            </div>
          </div>
        </article>
      </section>

      {/* Recommendations list */}
      <section className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
        <div className="flex items-center justify-between px-6 py-5">
          <div>
            <p className="eyebrow">Maintenance Queue</p>
            <h2 className="mt-2 text-[21px] font-semibold tracking-[-0.025em] text-[#4A3528]">
              Prioritized recommendations
            </h2>
            <p className="mt-2 text-[11px] text-[#9B8977]">
              Ranked by Member 3's Maintenance Priority Engine — not sorted by failure probability alone.
            </p>
          </div>
          <Wrench className="h-5 w-5 text-[#806B59]" strokeWidth={1.5} />
        </div>

        {loading && (
          <div className="border-t border-[#E8DED1] px-6 py-8 text-center text-[12px] text-[#9B8977]">
            Loading recommendations…
          </div>
        )}

        {error && (
          <div className="border-t border-[#E8DED1] px-6 py-8 text-center">
            <p className="text-[12px] text-[#B95F46]">{error}</p>
            <button type="button" onClick={fetchRecs} className="mt-3 text-[11px] font-semibold text-[#69784F] underline">
              Retry
            </button>
          </div>
        )}

        {!loading && !error && recs.length === 0 && (
          <div className="border-t border-[#E8DED1] px-6 py-8 text-center text-[12px] text-[#9B8977]">
            No recommendations found. Click "Run Readiness" to generate them.
          </div>
        )}

        {!loading && !error && (
          <div>
            {recs.map((rec) => (
              <article key={rec.recommendation_id} className="border-t border-[#E8DED1] px-6 py-6">
                <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-3">
                      <ClipboardCheck
                        className={`h-4 w-4 ${urgencyTextColor(rec.urgency)}`}
                        strokeWidth={1.7}
                      />
                      <div>
                        <p className="font-mono text-[12px] font-semibold text-[#4A3528]">
                          {rec.recommendation_id}
                        </p>
                        <p className="mt-1 text-[10px] text-[#9B8977]">
                          {rec.asset_id} · {rec.component_id}
                        </p>
                      </div>

                      <span
                        className={`rounded-full px-3 py-1.5 text-[8px] font-semibold uppercase tracking-[0.12em] ${urgencyBgColor(rec.urgency)} ${urgencyTextColor(rec.urgency)}`}
                      >
                        {rec.urgency}
                      </span>

                      <span className="rounded-full border border-[#D8CBB9] bg-[#F5EEE4] px-3 py-1.5 text-[8px] font-semibold uppercase tracking-[0.12em] text-[#806B59]">
                        Priority #{rec.priority}
                      </span>

                      <span className="rounded-full border border-[#D8CBB9] bg-[#F5EEE4] px-3 py-1.5 text-[8px] font-semibold uppercase tracking-[0.12em] text-[#806B59]">
                        {rec.status}
                      </span>
                    </div>

                    <div className="mt-5 grid gap-4 sm:grid-cols-3">
                      <div>
                        <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">Risk</p>
                        <p className={`mt-2 text-[12px] font-semibold ${urgencyTextColor(rec.risk)}`}>{rec.risk}</p>
                      </div>
                      <div>
                        <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                          Mission impact
                        </p>
                        <p className="mt-2 text-[12px] text-[#5D4535]">{rec.mission_impact}</p>
                      </div>
                      <div>
                        <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">Urgency</p>
                        <p className={`mt-2 text-[12px] font-semibold ${urgencyTextColor(rec.urgency)}`}>
                          {rec.urgency}
                        </p>
                      </div>
                    </div>

                    <div className="mt-5 rounded-xl border border-[#E4D8C9] bg-[#F5EEE4] px-4 py-3">
                      <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                        Action
                      </p>
                      <p className="mt-1 text-[11px] leading-5 text-[#5D4535]">{rec.action}</p>
                      <p className="mt-2 text-[9px] text-[#9B8977]">{rec.reason}</p>
                    </div>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="grid gap-0 overflow-hidden rounded-2xl border border-[#DED2C0] bg-[#EEE5D7] md:grid-cols-2">
        <div className="flex items-center gap-3 px-6 py-5">
          <CheckCircle2 className="h-5 w-5 text-[#69784F]" strokeWidth={1.5} />
          <div>
            <p className="text-[13px] font-semibold text-[#4A3528]">Maintenance control operational</p>
            <p className="mt-1 text-[11px] text-[#9B8977]">
              Recommendations are ranked by Member 3's weighted priority formula.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 border-t border-[#DED2C0] px-6 py-5 md:border-l md:border-t-0">
          <CalendarClock className="h-5 w-5 text-[#69784F]" strokeWidth={1.5} />
          <div>
            <p className="text-[13px] font-semibold text-[#4A3528]">Evidence-backed prioritisation</p>
            <p className="mt-1 text-[11px] text-[#9B8977]">
              Failure risk, criticality, mission impact, and urgency drive ranking.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Maintenance;
