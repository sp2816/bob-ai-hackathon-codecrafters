import {
  Activity,
  CheckCircle2,
  Package,
  RefreshCw,
  TriangleAlert,
} from "lucide-react";
import { useEffect, useState } from "react";
import { getAssets } from "../services/api";
import type { ApiAsset } from "../types/api";

function readinessToUiStatus(status: string): "Healthy" | "Warning" | "Standby" {
  if (status === "READY") return "Healthy";
  if (status === "NOT_READY") return "Warning";
  return "Standby";
}

function StatusIcon({ status }: { status: "Healthy" | "Warning" | "Standby" }) {
  if (status === "Warning")
    return <TriangleAlert className="h-[18px] w-[18px]" style={{ color: "var(--danger-text)" }} strokeWidth={1.8} />;
  if (status === "Standby")
    return <Activity className="h-[18px] w-[18px]" style={{ color: "var(--warning-text)" }} strokeWidth={1.8} />;
  return <CheckCircle2 className="h-[18px] w-[18px]" style={{ color: "var(--success-text)" }} strokeWidth={1.8} />;
}

function scoreToPercent(score: number | null): number {
  if (score === null) return 50;
  return Math.round(score * 100);
}

function StatusBadge({ status }: { status: "Healthy" | "Warning" | "Standby" }) {
  if (status === "Healthy") return <span className="badge-ready">READY</span>;
  if (status === "Warning") return <span className="badge-not-ready">NOT READY</span>;
  return <span className="badge-conditional">CONDITIONAL</span>;
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
    <div className="space-y-6">
      {/* Page header */}
      <section className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <p className="eyebrow">Fleet Management</p>
          <h1 className="page-title mt-2">Assets</h1>
          <p className="body-text mt-2 max-w-xl">
            Monitor fleet health, component condition, and operational status across all registered assets.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={fetchAssets}
            className="btn-secondary-sm"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
          <span
            className="badge-info"
            style={{ padding: "6px 12px" }}
          >
            {loading ? "…" : `${assets.length} Assets`}
          </span>
        </div>
      </section>

      {/* Summary KPI cards */}
      <section className="grid gap-4 md:grid-cols-3">
        {/* Healthy */}
        <article
          className="card rounded-xl p-5"
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.transform = "translateY(-2px)"; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.transform = ""; }}
          style={{ transition: "transform 200ms ease" }}
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">Ready</p>
              <div className="mt-3 text-[40px] font-bold leading-none tracking-[-0.05em]" style={{ color: "var(--success-text)" }}>
                {loading ? "—" : healthy}
              </div>
              <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
                Assets ready for deployment
              </p>
            </div>
            <div className="icon-container-success">
              <CheckCircle2 className="h-5 w-5" strokeWidth={1.8} />
            </div>
          </div>
        </article>

        {/* Not ready */}
        <article
          className="card rounded-xl p-5"
          style={{
            border: "1px solid var(--danger-border)",
            transition: "transform 200ms ease",
          }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.transform = "translateY(-2px)"; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.transform = ""; }}
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow" style={{ color: "var(--danger-text)" }}>Not Ready</p>
              <div className="mt-3 text-[40px] font-bold leading-none tracking-[-0.05em]" style={{ color: "var(--danger-text)" }}>
                {loading ? "—" : warning}
              </div>
              <p className="mt-2 text-xs" style={{ color: "var(--danger-text)", opacity: 0.7 }}>
                Requires immediate attention
              </p>
            </div>
            <div className="icon-container-danger">
              <TriangleAlert className="h-5 w-5" strokeWidth={1.8} />
            </div>
          </div>
        </article>

        {/* Standby */}
        <article
          className="card rounded-xl p-5"
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.transform = "translateY(-2px)"; }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.transform = ""; }}
          style={{ transition: "transform 200ms ease" }}
        >
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">Conditional</p>
              <div className="mt-3 text-[40px] font-bold leading-none tracking-[-0.05em]" style={{ color: "var(--warning-text)" }}>
                {loading ? "—" : standby}
              </div>
              <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
                Conditionally ready
              </p>
            </div>
            <div className="icon-container-warning">
              <Activity className="h-5 w-5" strokeWidth={1.8} />
            </div>
          </div>
        </article>
      </section>

      {/* Asset table */}
      <section className="card rounded-xl overflow-hidden">
        <div
          className="flex items-center justify-between px-6 py-4"
          style={{ borderBottom: "1px solid var(--border-default)" }}
        >
          <div>
            <p className="eyebrow">Fleet</p>
            <h2 className="section-title mt-1">Asset Health</h2>
            <p className="body-text mt-1 text-xs">
              Current readiness, operational hours, and health index per asset.
            </p>
          </div>
          <Package className="h-5 w-5" style={{ color: "var(--text-muted)" }} strokeWidth={1.5} />
        </div>

        {loading && (
          <div className="px-6 py-10 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            Loading assets…
          </div>
        )}

        {error && (
          <div className="px-6 py-10 text-center">
            <p className="text-sm" style={{ color: "var(--danger-text)" }}>{error}</p>
            <button
              type="button"
              onClick={fetchAssets}
              className="mt-3 text-xs font-semibold underline"
              style={{ color: "var(--text-brand)" }}
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && assets.length === 0 && (
          <div className="px-6 py-10 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            No assets found. Run the seed script to populate the database.
          </div>
        )}

        {!loading && !error && (
          <div>
            {assets.map((asset) => {
              const uiStatus = readinessToUiStatus(asset.current_status);
              const healthPct = scoreToPercent(asset.readiness_score);
              const fillClass =
                uiStatus === "Healthy"
                  ? "progress-fill-success"
                  : uiStatus === "Warning"
                  ? "progress-fill-danger"
                  : "progress-fill-warning";

              return (
                <div
                  key={asset.asset_id}
                  className="px-6 py-5 transition-colors duration-100"
                  style={{ borderBottom: "1px solid var(--border-subtle)" }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--surface-elevated)"; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = ""; }}
                >
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    {/* Left: asset info */}
                    <div className="flex min-w-0 items-start gap-4">
                      <div className="mt-0.5">
                        <StatusIcon status={uiStatus} />
                      </div>
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-[13px] font-bold" style={{ color: "var(--text-primary)" }}>
                            {asset.asset_id}
                          </span>
                          <StatusBadge status={uiStatus} />
                        </div>
                        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
                          {asset.asset_name}
                        </p>

                        <div className="mt-3 grid grid-cols-2 gap-x-8 gap-y-2 sm:grid-cols-3">
                          <div>
                            <p className="data-label">Type</p>
                            <p className="mt-1 text-[13px] font-medium" style={{ color: "var(--text-primary)" }}>
                              {asset.asset_type}
                            </p>
                          </div>
                          <div>
                            <p className="data-label">Op. Hours</p>
                            <p className="mt-1 text-[13px] font-medium" style={{ color: "var(--text-primary)" }}>
                              {asset.operational_hours.toLocaleString()} h
                            </p>
                          </div>
                          <div>
                            <p className="data-label">Unit</p>
                            <p className="mt-1 text-[13px] font-medium" style={{ color: "var(--text-primary)" }}>
                              {asset.unit}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Right: health score */}
                    <div className="flex flex-col items-end gap-1 sm:shrink-0 sm:text-right">
                      <span
                        className="text-[32px] font-bold leading-none tracking-[-0.05em]"
                        style={{
                          color:
                            uiStatus === "Healthy"
                              ? "var(--success-text)"
                              : uiStatus === "Warning"
                              ? "var(--danger-text)"
                              : "var(--warning-text)",
                        }}
                      >
                        {healthPct}%
                      </span>
                      <p className="text-[10px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>
                        Readiness index
                      </p>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="progress-track mt-4">
                    <div className={fillClass} style={{ width: `${Math.max(healthPct, 2)}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Footer status row */}
      <section
        className="grid overflow-hidden rounded-xl sm:grid-cols-2"
        style={{
          backgroundColor: "var(--surface-card)",
          border: "1px solid var(--border-default)",
        }}
      >
        <div
          className="flex items-center gap-3 px-5 py-4"
          style={{ borderBottom: "1px solid var(--border-default)" }}
        >
          <div className="icon-container-success h-9 w-9">
            <CheckCircle2 className="h-4 w-4" strokeWidth={1.8} />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>
              Fleet Status
            </p>
            <p className="mt-0.5 text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              {loading ? "Loading…" : `${healthy} asset${healthy !== 1 ? "s" : ""} currently operational`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 px-5 py-4 sm:border-l" style={{ borderColor: "var(--border-default)" }}>
          <div className="icon-container-brand h-9 w-9">
            <Activity className="h-4 w-4" strokeWidth={1.8} />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>
              Monitoring
            </p>
            <p className="mt-0.5 text-sm font-medium" style={{ color: "var(--text-primary)" }}>
              Continuous health monitoring enabled
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Assets;