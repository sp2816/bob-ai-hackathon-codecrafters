import { Activity, Box, CheckCircle2, TriangleAlert, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { getAssets } from "../services/api";
import type { ApiAsset } from "../types/api";

function readinessToUiStatus(status: string): "Healthy" | "Warning" | "Standby" {
  if (status === "READY") return "Healthy";
  if (status === "NOT_READY") return "Warning";
  return "Standby"; // CONDITIONALLY_READY or unknown
}

function StatusIcon({ status }: { status: "Healthy" | "Warning" | "Standby" }) {
  if (status === "Warning") return <TriangleAlert className="h-4 w-4 text-[#B95F46]" strokeWidth={1.7} />;
  if (status === "Standby") return <Activity className="h-4 w-4 text-[#A69A89]" strokeWidth={1.7} />;
  return <CheckCircle2 className="h-4 w-4 text-[#69784F]" strokeWidth={1.7} />;
}

function statusTextColor(status: "Healthy" | "Warning" | "Standby") {
  if (status === "Warning") return "text-[#B95F46]";
  if (status === "Standby") return "text-[#A69A89]";
  return "text-[#69784F]";
}

function progressColor(status: "Healthy" | "Warning" | "Standby") {
  return status === "Warning" ? "bg-[#B95F46]" : "bg-[#69784F]";
}

/** Convert readiness_score (0–1) to a 0–100 health % for display. */
function scoreToPercent(score: number | null): number {
  if (score === null) return 50;
  return Math.round(score * 100);
}

function Assets() {
  const [assets, setAssets] = useState<ApiAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAssets = () => {
    setLoading(true);
    setError(null);
    getAssets()
      .then(setAssets)
      .catch(() => setError("Unable to load assets from the backend."))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchAssets(); }, []);

  const healthy = assets.filter((a) => readinessToUiStatus(a.current_status) === "Healthy").length;
  const warning = assets.filter((a) => readinessToUiStatus(a.current_status) === "Warning").length;
  const standby = assets.filter((a) => readinessToUiStatus(a.current_status) === "Standby").length;

  return (
    <div className="space-y-7">
      <section className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="eyebrow">Fleet Management</p>
          <h1 className="mt-2 text-[42px] font-semibold leading-none tracking-[-0.055em] text-[#3B2A20] sm:text-[48px]">
            Assets
          </h1>
          <p className="mt-3 max-w-xl text-[13px] leading-6 text-[#806B59]">
            Monitor fleet health, component condition, service history, and operational status across all registered assets.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={fetchAssets}
            title="Refresh assets"
            className="flex items-center gap-1.5 rounded-full border border-[#D8CBB9] bg-[#EEE5D7] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#806B59] hover:bg-[#E5D8C5]"
          >
            <RefreshCw className="h-3 w-3" />
            Refresh
          </button>
          <span className="rounded-full border border-[#C2CEAE] bg-[#DDE5D1] px-3 py-2 text-[9px] font-semibold uppercase tracking-[0.12em] text-[#596842]">
            {loading ? "…" : `${assets.length} Assets`}
          </span>
        </div>
      </section>

      {/* Summary cards */}
      <section className="grid gap-5 md:grid-cols-3">
        <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">Healthy</p>
              <div className="mt-4 text-[42px] font-light leading-none tracking-[-0.06em] text-[#3B2A20]">
                {loading ? "—" : healthy}
              </div>
              <p className="mt-3 text-[10px] text-[#69784F]">Assets ready for deployment</p>
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#E0E7D6]">
              <CheckCircle2 className="h-4 w-4 text-[#69784F]" strokeWidth={1.7} />
            </div>
          </div>
        </article>

        <article className="rounded-2xl border-2 border-[#C96D52] bg-[#FBF4EE] p-6 shadow-[0_8px_30px_rgba(155,75,50,0.05)]">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#A85B45]">Warning</p>
              <div className="mt-4 text-[42px] font-light leading-none tracking-[-0.06em] text-[#B95F46]">
                {loading ? "—" : warning}
              </div>
              <p className="mt-3 text-[10px] text-[#A85B45]">Requires attention</p>
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#F0D8CF]">
              <TriangleAlert className="h-4 w-4 text-[#B95F46]" strokeWidth={1.7} />
            </div>
          </div>
        </article>

        <article className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] p-6 shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">Standby</p>
              <div className="mt-4 text-[42px] font-light leading-none tracking-[-0.06em] text-[#3B2A20]">
                {loading ? "—" : standby}
              </div>
              <p className="mt-3 text-[10px] text-[#9B8977]">Conditionally ready</p>
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#EEE8DE]">
              <Activity className="h-4 w-4 text-[#A69A89]" strokeWidth={1.7} />
            </div>
          </div>
        </article>
      </section>

      {/* Asset list */}
      <section className="rounded-2xl border border-[#DED2C0] bg-[#FBF8F2] shadow-[0_8px_30px_rgba(91,70,48,0.04)]">
        <div className="flex items-center justify-between px-6 py-5">
          <div>
            <p className="eyebrow">Fleet</p>
            <h2 className="mt-2 text-[21px] font-semibold tracking-[-0.025em] text-[#4A3528]">Asset health</h2>
            <p className="mt-2 text-[11px] text-[#9B8977]">
              Current readiness status and operational hours for each asset.
            </p>
          </div>
          <Box className="h-5 w-5 text-[#806B59]" strokeWidth={1.5} />
        </div>

        {loading && (
          <div className="border-t border-[#E8DED1] px-6 py-8 text-center text-[12px] text-[#9B8977]">
            Loading assets…
          </div>
        )}

        {error && (
          <div className="border-t border-[#E8DED1] px-6 py-8 text-center">
            <p className="text-[12px] text-[#B95F46]">{error}</p>
            <button
              type="button"
              onClick={fetchAssets}
              className="mt-3 text-[11px] font-semibold text-[#69784F] underline"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && assets.length === 0 && (
          <div className="border-t border-[#E8DED1] px-6 py-8 text-center text-[12px] text-[#9B8977]">
            No assets found. Run the seed script to populate the database.
          </div>
        )}

        {!loading && !error && (
          <div>
            {assets.map((asset) => {
              const uiStatus = readinessToUiStatus(asset.current_status);
              const healthPct = scoreToPercent(asset.readiness_score);
              return (
                <div key={asset.asset_id} className="border-t border-[#E8DED1] px-6 py-6">
                  <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0">
                      <div className="flex items-center gap-3">
                        <StatusIcon status={uiStatus} />
                        <div>
                          <p className="font-mono text-[12px] font-semibold text-[#4A3528]">{asset.asset_id}</p>
                          <p className="mt-1 text-[10px] text-[#9B8977]">{asset.asset_name}</p>
                        </div>
                      </div>

                      <div className="mt-4 grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">Type</p>
                          <p className="mt-1 text-[12px] text-[#5D4535]">{asset.asset_type}</p>
                        </div>
                        <div>
                          <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-[#9B8977]">
                            Op. Hours
                          </p>
                          <p className="mt-1 text-[12px] text-[#5D4535]">
                            {asset.operational_hours.toLocaleString()} h
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="text-left sm:text-right">
                      <span className="text-[28px] font-light tracking-[-0.05em] text-[#3B2A20]">
                        {healthPct}%
                      </span>
                      <p
                        className={`mt-1 text-[8px] font-semibold uppercase tracking-[0.12em] ${statusTextColor(uiStatus)}`}
                      >
                        {uiStatus}
                      </p>
                    </div>
                  </div>

                  <div className="mt-5">
                    <div className="soft-progress h-2">
                      <div
                        className={`h-full rounded-full ${progressColor(uiStatus)}`}
                        style={{ width: `${Math.max(healthPct, 3)}%` }}
                      />
                    </div>
                    <div className="mt-2 flex justify-between">
                      <span className="text-[8px] text-[#A39484]">Unit: {asset.unit}</span>
                      <span className="text-[8px] text-[#A39484]">Readiness index</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section className="grid overflow-hidden rounded-2xl border border-[#DED2C0] bg-[#EEE5D7] sm:grid-cols-2">
        <div className="flex items-center gap-3 border-b border-[#DED2C0] px-5 py-4 sm:border-b-0 sm:border-r">
          <CheckCircle2 className="h-5 w-5 text-[#69784F]" strokeWidth={1.5} />
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#6F5B4A]">Fleet Status</p>
            <p className="mt-1 text-[10px] text-[#978575]">
              {loading ? "Loading…" : `${healthy} asset${healthy !== 1 ? "s" : ""} currently operational`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 px-5 py-4">
          <Activity className="h-5 w-5 text-[#69784F]" strokeWidth={1.5} />
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#6F5B4A]">Monitoring</p>
            <p className="mt-1 text-[10px] text-[#978575]">Continuous health monitoring enabled</p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Assets;