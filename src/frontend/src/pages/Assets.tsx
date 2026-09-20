import {
  Activity,
  AlertTriangle,
  CheckCircle,
  CheckCircle2,
  ChevronRight,
  Cpu,
  Loader2,
  Package,
  Plus,
  RefreshCw,
  TriangleAlert,
  X,
  Zap,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { createAsset, getAssets, getMaintenanceRecommendations } from "../services/api";
import type {
  ApiAsset,
  AssetCreateRequest,
  AssetCreateResponse,
  SensorCondition,
  ApiMaintenanceRecommendation,
} from "../types/api";
import { formatCurrency } from "../services/api";

// ── Readiness helpers (display-only, no calculations) ─────────────────────

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

// ── Loading stage text ─────────────────────────────────────────────────────

const PIPELINE_STAGES = [
  "Persisting asset data…",
  "Running ML inference…",
  "Evaluating readiness…",
  "Generating maintenance recommendations…",
];

// ── Result card ────────────────────────────────────────────────────────────

function ResultCard({ result }: { result: AssetCreateResponse }) {
  const rStatus = result.readiness.readiness_status;
  const uiStatus = readinessToUiStatus(rStatus);
  const riskPct = Math.round(result.prediction.failure_probability * 100);
  const scorePct = Math.round(result.readiness.readiness_score * 100);

  const statusColor =
    uiStatus === "Healthy"
      ? "var(--success-text)"
      : uiStatus === "Warning"
      ? "var(--danger-text)"
      : "var(--warning-text)";

  return (
    <div
      style={{
        marginTop: "1.25rem",
        borderRadius: "0.75rem",
        border: `1px solid ${uiStatus === "Healthy" ? "var(--success-border)" : uiStatus === "Warning" ? "var(--danger-border)" : "var(--warning-border)"}`,
        background: "var(--surface-elevated)",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "0.875rem 1.25rem",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
        }}
      >
        {uiStatus === "Healthy" ? (
          <CheckCircle className="h-5 w-5" style={{ color: "var(--success-text)" }} />
        ) : uiStatus === "Warning" ? (
          <AlertTriangle className="h-5 w-5" style={{ color: "var(--danger-text)" }} />
        ) : (
          <Activity className="h-5 w-5" style={{ color: "var(--warning-text)" }} />
        )}
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>
            Analysis Complete
          </p>
          <p className="mt-0.5 text-sm font-bold" style={{ color: "var(--text-primary)" }}>
            {result.asset.asset_id} — {result.asset.asset_name}
          </p>
        </div>
        <span
          style={{
            marginLeft: "auto",
            padding: "3px 10px",
            borderRadius: "999px",
            fontSize: "11px",
            fontWeight: 700,
            letterSpacing: "0.05em",
            color: statusColor,
            background: `color-mix(in srgb, ${statusColor} 12%, transparent)`,
            border: `1px solid color-mix(in srgb, ${statusColor} 30%, transparent)`,
          }}
        >
          {rStatus.replace("_", " ")}
        </span>
      </div>

      {/* Metrics grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0" }}>
        {[
          {
            label: "Readiness Index",
            value: `${scorePct}%`,
            icon: <Zap className="h-3.5 w-3.5" />,
            color: statusColor,
          },
          {
            label: "Failure Risk",
            value: `${riskPct}%`,
            sub: result.prediction.risk_category,
            icon: <Cpu className="h-3.5 w-3.5" />,
            color:
              result.prediction.risk_category === "HIGH"
                ? "var(--danger-text)"
                : result.prediction.risk_category === "MEDIUM"
                ? "var(--warning-text)"
                : "var(--success-text)",
          },
          {
            label: "Anomaly",
            value: result.anomaly.anomaly_status,
            sub:
              result.anomaly.anomaly_status === "HIGH"
                ? `${result.anomaly.anomaly_severity} on ${result.anomaly.sensor}`
                : "None detected",
            icon: <Activity className="h-3.5 w-3.5" />,
            color:
              result.anomaly.anomaly_status === "HIGH"
                ? "var(--danger-text)"
                : "var(--success-text)",
          },
          {
            label: "Maintenance",
            value: result.recommendation
              ? `P${result.recommendation.priority} — ${result.recommendation.urgency}`
              : "None required",
            sub: result.recommendation?.action.slice(0, 40) ?? "",
            icon: <Package className="h-3.5 w-3.5" />,
            color: result.recommendation
              ? result.recommendation.urgency === "HIGH"
                ? "var(--danger-text)"
                : "var(--warning-text)"
              : "var(--success-text)",
          },
        ].map((m, i) => (
          <div
            key={i}
            style={{
              padding: "0.875rem 1.25rem",
              borderRight: i % 2 === 0 ? "1px solid var(--border-subtle)" : "none",
              borderBottom: i < 2 ? "1px solid var(--border-subtle)" : "none",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", color: m.color }}>
              {m.icon}
              <p className="data-label" style={{ color: "var(--text-muted)" }}>{m.label}</p>
            </div>
            <p className="mt-1 text-sm font-bold" style={{ color: m.color }}>{m.value}</p>
            {m.sub && (
              <p className="mt-0.5 text-[10px]" style={{ color: "var(--text-muted)" }}>{m.sub}</p>
            )}
          </div>
        ))}
      </div>

      {/* Reasons */}
      {result.readiness.reasons.length > 0 && (
        <div style={{ padding: "0.875rem 1.25rem", borderTop: "1px solid var(--border-subtle)" }}>
          <p className="data-label mb-2">Readiness Reasons</p>
          <ul style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
            {result.readiness.reasons.map((r, i) => (
              <li key={i} style={{ display: "flex", alignItems: "flex-start", gap: "0.5rem" }}>
                <ChevronRight className="mt-0.5 h-3 w-3 shrink-0" style={{ color: "var(--text-muted)" }} />
                <span className="text-[11px]" style={{ color: "var(--text-secondary)" }}>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Economic Impact */}
      {result.recommendation?.economic_impact && (
        <div style={{ padding: "1rem 1.25rem", borderTop: "1px solid var(--border-subtle)", background: "color-mix(in srgb, var(--brand-accent) 4%, transparent)" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.75rem" }}>
            <p className="data-label" style={{ color: "var(--text-primary)", fontWeight: 700 }}>ECONOMIC IMPACT</p>
            <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "4px", background: "color-mix(in srgb, var(--warning-text) 15%, transparent)", color: "var(--warning-text)", fontWeight: 600 }}>MODELED ESTIMATE</span>
          </div>
          
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
            <div style={{ padding: "0.75rem", borderRadius: "0.5rem", border: "1px solid var(--border-subtle)", background: "var(--surface-card)" }}>
              <p className="text-[10px] font-bold uppercase tracking-[0.05em]" style={{ color: "var(--danger-text)" }}>WITHOUT ASSETSENTINEL (Traditional)</p>
              <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>Monitoring + Inspection + Prev. Maint. + Expected Failure</p>
              <p className="mt-2 text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                {formatCurrency(result.recommendation.economic_impact.traditional.total)}
              </p>
            </div>
            <div style={{ padding: "0.75rem", borderRadius: "0.5rem", border: "1px solid var(--border-subtle)", background: "var(--surface-card)" }}>
              <p className="text-[10px] font-bold uppercase tracking-[0.05em]" style={{ color: "var(--success-text)" }}>WITH ASSETSENTINEL</p>
              <p className="mt-1 text-xs" style={{ color: "var(--text-muted)" }}>Existing Sensors + Planned Intervention & Downtime</p>
              <p className="mt-2 text-lg font-bold" style={{ color: "var(--text-primary)" }}>
                {formatCurrency(result.recommendation.economic_impact.assetsentinel.total)}
              </p>
            </div>
          </div>
          
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.75rem", borderRadius: "0.5rem", background: "var(--brand-accent)", color: "white" }}>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.05em] opacity-80">POTENTIAL COST AVOIDED</p>
              <p className="text-xl font-bold">
                {formatCurrency(result.recommendation.economic_impact.potential_cost_avoided)}
              </p>
            </div>
          </div>
          
          <p className="mt-3 text-[10px] text-center" style={{ color: "var(--text-muted)" }}>
            * Modeled estimate based on synthetic data and configurable demo cost assumptions. Note: AssetSentinel does NOT replace physical sensors.
          </p>
        </div>
      )}

      <div style={{ padding: "0.5rem 1.25rem 0.75rem", textAlign: "right" }}>
        <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>{result.pipeline_note}</p>
      </div>
    </div>
  );
}

// ── Section label ─────────────────────────────────────────────────────────

function SectionLabel({ n, label }: { n: number; label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.625rem", marginBottom: "1rem" }}>
      <span
        style={{
          width: "1.5rem",
          height: "1.5rem",
          borderRadius: "50%",
          background: "var(--brand-accent)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "11px",
          fontWeight: 700,
          color: "#fff",
          flexShrink: 0,
        }}
      >
        {n}
      </span>
      <p className="text-[11px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>
        {label}
      </p>
    </div>
  );
}

// ── Form field helpers ────────────────────────────────────────────────────

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <p className="data-label mb-1">{label}{hint && <span style={{ color: "var(--text-muted)", fontWeight: 400 }}> — {hint}</span>}</p>
      {children}
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.5rem 0.75rem",
  borderRadius: "0.5rem",
  border: "1px solid var(--border-default)",
  background: "var(--surface-input, var(--surface-elevated))",
  color: "var(--text-primary)",
  fontSize: "13px",
  outline: "none",
  transition: "border-color 150ms ease",
};

function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      style={{ ...inputStyle, ...props.style }}
      onFocus={e => { e.target.style.borderColor = "var(--brand-accent)"; }}
      onBlur={e => { e.target.style.borderColor = "var(--border-default)"; }}
    />
  );
}

function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      style={{ ...inputStyle, ...props.style }}
      onFocus={e => { e.target.style.borderColor = "var(--brand-accent)"; }}
      onBlur={e => { e.target.style.borderColor = "var(--border-default)"; }}
    />
  );
}

// ── Add Asset Modal ───────────────────────────────────────────────────────

const SENSOR_PROFILE_INFO: Record<SensorCondition, { label: string; desc: string; color: string }> = {
  NORMAL: {
    label: "Normal",
    desc: "Within operational spec — healthy baseline",
    color: "var(--success-text)",
  },
  DEGRADING: {
    label: "Degrading",
    desc: "Early wear signs — elevated readings",
    color: "var(--warning-text)",
  },
  CRITICAL: {
    label: "Critical",
    desc: "Anomalous readings — immediate attention required",
    color: "var(--danger-text)",
  },
};

interface AddAssetModalProps {
  onClose: () => void;
  onSuccess: (result: AssetCreateResponse) => void;
}

function AddAssetModal({ onClose, onSuccess }: AddAssetModalProps) {
  const [stage, setStage] = useState<number | null>(null); // null = not submitting
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AssetCreateResponse | null>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  // ── Form state ────────────────────────────────────────────────────────
  const today = new Date().toISOString().split("T")[0];

  const [assetId, setAssetId] = useState("AS-");
  const [assetName, setAssetName] = useState("");
  const [assetType, setAssetType] = useState("aircraft");
  const [unit, setUnit] = useState("Unit-Alpha");
  const [opHours, setOpHours] = useState("1000");

  const [compId, setCompId] = useState("");
  const [compType, setCompType] = useState("main_bearing");
  const [criticality, setCriticality] = useState<"LOW" | "MEDIUM" | "HIGH">("MEDIUM");
  const [compOpHours, setCompOpHours] = useState("1000");
  const [lifeLimit, setLifeLimit] = useState("5000");
  const [svcInterval, setSvcInterval] = useState("300");

  const [condition, setCondition] = useState<SensorCondition>("NORMAL");
  const [vibration, setVibration] = useState("3.0");
  const [temperature, setTemperature] = useState("75.0");
  const [pressure, setPressure] = useState("100.0");
  const [rpm, setRpm] = useState("2800");

  const [maintType, setMaintType] = useState<"inspection" | "service" | "repair">("inspection");
  const [maintDate, setMaintDate] = useState(today);
  const [techAction, setTechAction] = useState("Routine inspection");
  const [maintStatus, setMaintStatus] = useState<"COMPLETED" | "OVERDUE" | "SCHEDULED">("COMPLETED");
  const [hoursSinceSvc, setHoursSinceSvc] = useState("150");

  // Auto-suggest component ID from asset ID
  useEffect(() => {
    const suffix = assetId.replace(/^[A-Z]+-/, "").replace(/\D/g, "");
    if (suffix) {
      setCompId(`${compType === "main_bearing" ? "BRG" : compType === "engine" ? "ENG" : compType === "hydraulics" ? "HYD" : compType === "avionics" ? "AVI" : "LND"}-${suffix}`);
    }
  }, [assetId, compType]);

  // Sync comp operating hours with asset hours by default
  useEffect(() => {
    setCompOpHours(opHours);
  }, [opHours]);

  // Update sensor defaults when condition changes
  useEffect(() => {
    if (condition === "NORMAL") {
      setVibration("3.0"); setTemperature("75.0"); setPressure("100.0"); setRpm("2800");
    } else if (condition === "DEGRADING") {
      setVibration("5.5"); setTemperature("86.0"); setPressure("83.0"); setRpm("2400");
    } else {
      setVibration("9.5"); setTemperature("98.0"); setPressure("65.0"); setRpm("1800");
    }
  }, [condition]);

  const stageRef = useRef(0);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    stageRef.current = 0;
    setStage(0);

    // Animate through loading stages
    const stageTimer = setInterval(() => {
      stageRef.current = Math.min(stageRef.current + 1, PIPELINE_STAGES.length - 1);
      setStage(stageRef.current);
    }, 1800);

    const request: AssetCreateRequest = {
      asset_id: assetId.trim().toUpperCase(),
      asset_name: assetName.trim() || assetId.trim().toUpperCase(),
      asset_type: assetType,
      unit: unit.trim(),
      operational_hours: parseFloat(opHours) || 0,
      component: {
        component_id: compId.trim().toUpperCase(),
        component_type: compType,
        criticality,
        operating_hours: parseFloat(compOpHours) || 0,
        life_limit: parseFloat(lifeLimit) || undefined,
        service_interval_hours: parseFloat(svcInterval) || 300,
      },
      sensors: {
        condition,
        vibration: parseFloat(vibration) || 0,
        temperature: parseFloat(temperature) || 0,
        pressure: parseFloat(pressure) || 0,
        RPM: parseFloat(rpm) || 0,
      },
      maintenance: {
        maintenance_type: maintType,
        maintenance_date: maintDate,
        technician_action: techAction.trim(),
        status: maintStatus,
        hours_since_service: parseFloat(hoursSinceSvc) || 0,
      },
    };

    try {
      const resp = await createAsset(request);
      clearInterval(stageTimer);
      setStage(null);
      setResult(resp);
      onSuccess(resp);
    } catch (err: unknown) {
      clearInterval(stageTimer);
      setStage(null);
      let msg = "An error occurred. Please check the backend is running.";
      if (err && typeof err === "object" && "response" in err) {
        const axiosErr = err as { response?: { data?: { detail?: string }; status?: number } };
        if (axiosErr.response?.status === 409) {
          msg = `Asset ID '${request.asset_id}' already exists. Try a different ID.`;
        } else if (axiosErr.response?.data?.detail) {
          msg = axiosErr.response.data.detail;
        }
      }
      setError(msg);
    }
  }

  const isSubmitting = stage !== null;
  const profileInfo = SENSOR_PROFILE_INFO[condition];

  return (
    <div
      ref={overlayRef}
      onClick={e => { if (e.target === overlayRef.current && !isSubmitting && !result) onClose(); }}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "rgba(0,0,0,0.6)",
        backdropFilter: "blur(4px)",
        padding: "1rem",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "42rem",
          maxHeight: "90vh",
          overflowY: "auto",
          borderRadius: "1rem",
          background: "var(--surface-card)",
          border: "1px solid var(--border-default)",
          boxShadow: "0 24px 64px rgba(0,0,0,0.4)",
        }}
      >
        {/* Modal header */}
        <div
          style={{
            position: "sticky",
            top: 0,
            zIndex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "1rem 1.5rem",
            borderBottom: "1px solid var(--border-default)",
            background: "var(--surface-card)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.625rem" }}>
            <div className="icon-container-brand" style={{ width: "2rem", height: "2rem" }}>
              <Plus className="h-4 w-4" />
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>
                Fleet Management
              </p>
              <h2 className="section-title mt-0">Add Asset & Analyze</h2>
            </div>
          </div>
          {!isSubmitting && (
            <button
              type="button"
              onClick={onClose}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "2rem",
                height: "2rem",
                borderRadius: "0.5rem",
                border: "1px solid var(--border-default)",
                background: "transparent",
                color: "var(--text-muted)",
                cursor: "pointer",
              }}
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        <div style={{ padding: "1.5rem" }}>
          {/* Loading state */}
          {isSubmitting && (
            <div style={{ textAlign: "center", padding: "2rem 1rem" }}>
              <Loader2
                className="mx-auto h-10 w-10 animate-spin"
                style={{ color: "var(--brand-accent)" }}
              />
              <p className="mt-4 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                {PIPELINE_STAGES[stage ?? 0]}
              </p>
              <div style={{ marginTop: "1.5rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {PIPELINE_STAGES.map((s, i) => (
                  <div
                    key={i}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      opacity: i <= (stage ?? 0) ? 1 : 0.3,
                      transition: "opacity 400ms ease",
                    }}
                  >
                    {i < (stage ?? 0) ? (
                      <CheckCircle className="h-4 w-4 shrink-0" style={{ color: "var(--success-text)" }} />
                    ) : i === (stage ?? 0) ? (
                      <Loader2 className="h-4 w-4 shrink-0 animate-spin" style={{ color: "var(--brand-accent)" }} />
                    ) : (
                      <div style={{ width: "1rem", height: "1rem", borderRadius: "50%", border: "1px solid var(--border-default)" }} />
                    )}
                    <span className="text-xs" style={{ color: i <= (stage ?? 0) ? "var(--text-primary)" : "var(--text-muted)" }}>{s}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Result */}
          {!isSubmitting && result && (
            <div>
              <ResultCard result={result} />
              <button
                type="button"
                onClick={onClose}
                className="btn-primary mt-4"
                style={{ width: "100%" }}
              >
                Done
              </button>
            </div>
          )}

          {/* Form */}
          {!isSubmitting && !result && (
            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
              {/* Error */}
              {error && (
                <div
                  style={{
                    padding: "0.75rem 1rem",
                    borderRadius: "0.5rem",
                    background: "color-mix(in srgb, var(--danger-text) 10%, transparent)",
                    border: "1px solid var(--danger-border)",
                    color: "var(--danger-text)",
                    fontSize: "13px",
                  }}
                >
                  {error}
                </div>
              )}

              {/* Section 1 — Asset */}
              <section>
                <SectionLabel n={1} label="Asset" />
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.875rem" }}>
                  <Field label="Asset ID">
                    <Input
                      required
                      value={assetId}
                      onChange={e => setAssetId(e.target.value)}
                      placeholder="AS-2001"
                      pattern="[A-Za-z]{2}-[0-9]{3,6}"
                      title="Format: XX-NNNN (e.g. AS-2001)"
                    />
                  </Field>
                  <Field label="Asset Name">
                    <Input
                      value={assetName}
                      onChange={e => setAssetName(e.target.value)}
                      placeholder="Aircraft 2001"
                    />
                  </Field>
                  <Field label="Asset Type">
                    <Select value={assetType} onChange={e => setAssetType(e.target.value)}>
                      <option value="aircraft">Aircraft</option>
                      <option value="rotary_wing">Rotary Wing</option>
                      <option value="ground_vehicle">Ground Vehicle</option>
                      <option value="maritime">Maritime</option>
                      <option value="fixed_wing">Fixed Wing</option>
                    </Select>
                  </Field>
                  <Field label="Unit">
                    <Input
                      required
                      value={unit}
                      onChange={e => setUnit(e.target.value)}
                      placeholder="Unit-Alpha"
                    />
                  </Field>
                  <Field label="Operational Hours">
                    <Input
                      type="number"
                      required
                      min={0}
                      step={1}
                      value={opHours}
                      onChange={e => setOpHours(e.target.value)}
                    />
                  </Field>
                </div>
              </section>

              {/* Section 2 — Component */}
              <section>
                <SectionLabel n={2} label="Component" />
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.875rem" }}>
                  <Field label="Component ID">
                    <Input
                      required
                      value={compId}
                      onChange={e => setCompId(e.target.value)}
                      placeholder="BRG-2001"
                    />
                  </Field>
                  <Field label="Component Type">
                    <Select value={compType} onChange={e => setCompType(e.target.value)}>
                      <option value="main_bearing">Main Bearing</option>
                      <option value="engine">Engine</option>
                      <option value="hydraulics">Hydraulics</option>
                      <option value="avionics">Avionics</option>
                      <option value="landing_gear">Landing Gear</option>
                    </Select>
                  </Field>
                  <Field label="Criticality">
                    <Select
                      value={criticality}
                      onChange={e => setCriticality(e.target.value as "LOW" | "MEDIUM" | "HIGH")}
                    >
                      <option value="LOW">LOW</option>
                      <option value="MEDIUM">MEDIUM</option>
                      <option value="HIGH">HIGH</option>
                    </Select>
                  </Field>
                  <Field label="Life Limit (hours)" hint="optional">
                    <Input
                      type="number"
                      min={0}
                      step={100}
                      value={lifeLimit}
                      onChange={e => setLifeLimit(e.target.value)}
                      placeholder="5000"
                    />
                  </Field>
                  <Field label="Service Interval (hrs)" hint="for ML">
                    <Input
                      type="number"
                      required
                      min={50}
                      step={50}
                      value={svcInterval}
                      onChange={e => setSvcInterval(e.target.value)}
                      placeholder="300"
                    />
                  </Field>
                </div>
              </section>

              {/* Section 3 — Sensor Condition */}
              <section>
                <SectionLabel n={3} label="Synthetic Sensor Condition Profile" />
                <p
                  style={{
                    fontSize: "11px",
                    color: "var(--text-muted)",
                    marginBottom: "0.875rem",
                    padding: "0.5rem 0.75rem",
                    borderRadius: "0.5rem",
                    border: "1px solid var(--border-subtle)",
                    background: "var(--surface-elevated)",
                  }}
                >
                  Select a condition profile. The backend generates a deterministic 20-reading observation window from this profile — not real historical telemetry. Same inputs produce identical ML results every run.
                </p>

                {/* Profile radio */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.625rem", marginBottom: "1rem" }}>
                  {(["NORMAL", "DEGRADING", "CRITICAL"] as SensorCondition[]).map((c) => {
                    const info = SENSOR_PROFILE_INFO[c];
                    const selected = condition === c;
                    return (
                      <button
                        key={c}
                        type="button"
                        onClick={() => setCondition(c)}
                        style={{
                          padding: "0.625rem 0.5rem",
                          borderRadius: "0.5rem",
                          border: `1.5px solid ${selected ? info.color : "var(--border-default)"}`,
                          background: selected
                            ? `color-mix(in srgb, ${info.color} 10%, transparent)`
                            : "transparent",
                          cursor: "pointer",
                          textAlign: "center",
                          transition: "all 150ms ease",
                        }}
                      >
                        <p className="text-[12px] font-bold" style={{ color: info.color }}>
                          {info.label}
                        </p>
                        <p className="text-[10px] mt-0.5" style={{ color: "var(--text-muted)" }}>
                          {info.desc}
                        </p>
                      </button>
                    );
                  })}
                </div>

                {/* Sensor values */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.875rem" }}>
                  <Field label="Vibration" hint="mm/s RMS">
                    <Input
                      type="number"
                      required
                      min={0}
                      max={50}
                      step={0.1}
                      value={vibration}
                      onChange={e => setVibration(e.target.value)}
                    />
                  </Field>
                  <Field label="Temperature" hint="°C">
                    <Input
                      type="number"
                      required
                      min={0}
                      max={200}
                      step={0.5}
                      value={temperature}
                      onChange={e => setTemperature(e.target.value)}
                    />
                  </Field>
                  <Field label="Pressure" hint="bar">
                    <Input
                      type="number"
                      required
                      min={0}
                      max={500}
                      step={1}
                      value={pressure}
                      onChange={e => setPressure(e.target.value)}
                    />
                  </Field>
                  <Field label="RPM">
                    <Input
                      type="number"
                      required
                      min={0}
                      max={20000}
                      step={100}
                      value={rpm}
                      onChange={e => setRpm(e.target.value)}
                    />
                  </Field>
                </div>
              </section>

              {/* Section 4 — Maintenance */}
              <section>
                <SectionLabel n={4} label="Maintenance" />
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.875rem" }}>
                  <Field label="Inspection Type">
                    <Select
                      value={maintType}
                      onChange={e => setMaintType(e.target.value as "inspection" | "service" | "repair")}
                    >
                      <option value="inspection">Inspection</option>
                      <option value="service">Service</option>
                      <option value="repair">Repair</option>
                    </Select>
                  </Field>
                  <Field label="Inspection Status">
                    <Select
                      value={maintStatus}
                      onChange={e => setMaintStatus(e.target.value as "COMPLETED" | "OVERDUE" | "SCHEDULED")}
                    >
                      <option value="COMPLETED">COMPLETED</option>
                      <option value="OVERDUE">OVERDUE</option>
                      <option value="SCHEDULED">SCHEDULED</option>
                    </Select>
                  </Field>
                  <Field label="Last Service Date">
                    <Input
                      type="date"
                      required
                      value={maintDate}
                      onChange={e => setMaintDate(e.target.value)}
                      max={today}
                    />
                  </Field>
                  <Field label="Hours Since Service">
                    <Input
                      type="number"
                      required
                      min={0}
                      step={1}
                      value={hoursSinceSvc}
                      onChange={e => setHoursSinceSvc(e.target.value)}
                    />
                  </Field>
                  <Field label="Technician Action" hint="optional">
                    <Input
                      value={techAction}
                      onChange={e => setTechAction(e.target.value)}
                      placeholder="Routine inspection"
                      style={{ gridColumn: "1 / -1" }}
                    />
                  </Field>
                </div>
              </section>

              {/* Submit */}
              <div style={{ display: "flex", gap: "0.75rem", paddingTop: "0.25rem" }}>
                <button
                  type="button"
                  onClick={onClose}
                  className="btn-secondary-sm"
                  style={{ flex: 1, justifyContent: "center" }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  style={{ flex: 2, display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem" }}
                >
                  <Zap className="h-4 w-4" />
                  Add Asset &amp; Analyze
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main Assets page ───────────────────────────────────────────────────────

function Assets() {
  const [assets, setAssets] = useState<ApiAsset[]>([]);
  const [recommendations, setRecommendations] = useState<ApiMaintenanceRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  const fetchAssets = () => {
    setLoading(true);
    setError(null);
    Promise.all([getAssets(), getMaintenanceRecommendations()])
      .then(([assetsData, recsData]) => {
        setAssets(assetsData);
        setRecommendations(recsData);
      })
      .catch(() => setError("Unable to load assets from the backend."))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchAssets(); }, []);

  const healthy = assets.filter((a) => readinessToUiStatus(a.current_status) === "Healthy").length;
  const warning = assets.filter((a) => readinessToUiStatus(a.current_status) === "Warning").length;
  const standby = assets.filter((a) => readinessToUiStatus(a.current_status) === "Standby").length;

  function handleSuccess(result: AssetCreateResponse) {
    setShowModal(false);
    fetchAssets();
    const rStatus = result.readiness.readiness_status.replace("_", " ");
    setSuccessBanner(
      `${result.asset.asset_id} added — ${rStatus} (risk: ${result.prediction.risk_category})`
    );
    setTimeout(() => setSuccessBanner(null), 8000);
  }

  return (
    <div className="space-y-6">
      {showModal && (
        <AddAssetModal
          onClose={() => setShowModal(false)}
          onSuccess={handleSuccess}
        />
      )}

      {/* Success banner */}
      {successBanner && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0.75rem 1.25rem",
            borderRadius: "0.75rem",
            background: "color-mix(in srgb, var(--success-text) 10%, transparent)",
            border: "1px solid var(--success-border)",
            color: "var(--success-text)",
            fontSize: "13px",
            fontWeight: 600,
            animation: "fadeIn 300ms ease",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <CheckCircle className="h-4 w-4 shrink-0" />
            {successBanner}
          </div>
          <button
            type="button"
            onClick={() => setSuccessBanner(null)}
            style={{ background: "none", border: "none", cursor: "pointer", color: "inherit", opacity: 0.7 }}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

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
          <button
            type="button"
            onClick={() => setShowModal(true)}
            className="btn-primary"
            id="add-asset-btn"
            style={{ gap: "0.375rem" }}
          >
            <Plus className="h-4 w-4" />
            Add Asset
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
            No assets found. Run the seed script to populate the database, or use Add Asset above.
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

              const rec = recommendations.find((r) => r.asset_id === asset.asset_id);
              return (
                <div
                  key={asset.asset_id}
                  className="px-6 py-5 transition-colors duration-100"
                  style={{ borderBottom: "1px solid var(--border-subtle)", cursor: "pointer" }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--surface-elevated)"; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = ""; }}
                  onClick={() => setSelectedAssetId(asset.asset_id)}
                >
                  <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    {/* Left: asset info */}
                    <div className="flex min-w-0 items-start gap-4 flex-1">
                      <div className="mt-0.5">
                        <StatusIcon status={uiStatus} />
                      </div>
                      <div className="min-w-0 w-full">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-[13px] font-bold" style={{ color: "var(--text-primary)" }}>
                            {asset.asset_id}
                          </span>
                          <StatusBadge status={uiStatus} />
                        </div>
                        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
                          {asset.asset_name}
                        </p>

                        <div className="mt-3 grid grid-cols-2 gap-x-8 gap-y-4 sm:grid-cols-4 w-full">
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
                        
                        {/* Compact Business Impact Summary */}
                        {rec && (
                          <div className="mt-4 pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between">
                            <div className="flex gap-6">
                              <div>
                                <p className="text-[10px] uppercase font-bold text-[var(--text-muted)]">Action</p>
                                <p className="text-[13px] font-bold mt-0.5" style={{ color: "var(--brand-accent)" }}>{rec.decision || "INSPECT"}</p>
                              </div>
                              <div>
                                <p className="text-[10px] uppercase font-bold text-[var(--text-muted)]">Potential Cost Avoided</p>
                                <p className="text-[13px] font-bold mt-0.5" style={{ color: (rec.economic_impact?.potential_cost_avoided ?? 0) >= 0 ? "var(--success-text)" : "var(--danger-text)" }}>
                                  {(rec.economic_impact?.potential_cost_avoided ?? 0) >= 0 ? "+" : ""}{formatCurrency(rec.economic_impact?.potential_cost_avoided ?? 0)}
                                </p>
                              </div>
                              <div>
                                <p className="text-[10px] uppercase font-bold text-[var(--text-muted)]">Net Economic Benefit</p>
                                <p className="text-[13px] font-bold mt-0.5" style={{ color: "var(--text-primary)" }}>
                                  {formatCurrency(rec.economic_impact?.net_economic_benefit)}
                                </p>
                              </div>
                            </div>
                            <button className="btn-secondary-sm">View Economic Impact</button>
                          </div>
                        )}

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
      {/* Asset Detail Modal */}
      {selectedAssetId && (() => {
        const asset = assets.find(a => a.asset_id === selectedAssetId);
        const rec = recommendations.find(r => r.asset_id === selectedAssetId);
        if (!asset) return null;
        return (
          <div
            style={{
              position: "fixed", inset: 0, zIndex: 50, display: "flex", alignItems: "center", justifyContent: "center",
              background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)", padding: "1rem",
            }}
            onClick={(e) => { if (e.target === e.currentTarget) setSelectedAssetId(null); }}
          >
            <div style={{ width: "100%", maxWidth: "48rem", maxHeight: "90vh", overflowY: "auto", borderRadius: "1rem", background: "var(--surface-card)", border: "1px solid var(--border-default)", boxShadow: "0 24px 64px rgba(0,0,0,0.4)" }}>
              <div style={{ position: "sticky", top: 0, zIndex: 1, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1.25rem 1.5rem", borderBottom: "1px solid var(--border-default)", background: "var(--surface-card)" }}>
                <div>
                  <h2 className="text-lg font-bold">Asset Detail: {asset.asset_id}</h2>
                  <p className="text-xs text-[var(--text-muted)]">{asset.asset_name}</p>
                </div>
                <button onClick={() => setSelectedAssetId(null)} className="btn-secondary-sm"><X className="h-4 w-4" /></button>
              </div>
              <div className="p-6 space-y-6">
                {/* Economic Impact Section */}
                <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-primary)] border-b border-[var(--border-subtle)] pb-2">Economic Impact</h3>
                
                {rec?.economic_impact ? (
                  <div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Left: Traditional */}
                      <div className="p-4 rounded-xl border border-[var(--danger-border)] bg-[rgba(235,50,35,0.03)] space-y-3">
                        <p className="text-xs font-bold uppercase text-[var(--danger-text)]">Without AssetSentinel</p>
                        <div className="flex justify-between items-center text-sm border-b border-dashed border-[var(--danger-border)] pb-1">
                          <span className="text-[var(--text-secondary)]">Traditional Monitoring</span>
                          <span className="font-mono">{formatCurrency(rec.economic_impact.traditional?.monitoring_cost)}</span>
                        </div>
                        <div className="flex justify-between items-center text-sm border-b border-dashed border-[var(--danger-border)] pb-1">
                          <span className="text-[var(--text-secondary)]">Inspection</span>
                          <span className="font-mono">{formatCurrency(rec.economic_impact.traditional?.inspection_cost)}</span>
                        </div>
                        <div className="flex justify-between items-center text-sm border-b border-dashed border-[var(--danger-border)] pb-1">
                          <span className="text-[var(--text-secondary)]">Preventive Maintenance</span>
                          <span className="font-mono">{formatCurrency(rec.economic_impact.traditional?.preventive_maintenance_cost)}</span>
                        </div>
                        <div className="flex justify-between items-center text-sm border-b border-dashed border-[var(--danger-border)] pb-1">
                          <span className="text-[var(--text-secondary)]">Expected Reactive Failure</span>
                          <span className="font-mono">{formatCurrency(rec.economic_impact.traditional?.expected_reactive_failure_cost)}</span>
                        </div>
                        <div className="flex justify-between items-center pt-2">
                          <span className="text-sm font-bold text-[var(--danger-text)]">TOTAL</span>
                          <span className="font-mono font-bold text-[15px] text-[var(--danger-text)]">{formatCurrency(rec.economic_impact.traditional?.total)}</span>
                        </div>
                      </div>

                      {/* Right: AssetSentinel */}
                      <div className="p-4 rounded-xl border border-[var(--success-border)] bg-[rgba(35,136,114,0.03)] space-y-3">
                        <p className="text-xs font-bold uppercase text-[var(--success-text)]">With AssetSentinel</p>
                        <div className="flex justify-between items-center text-sm border-b border-dashed border-[var(--success-border)] pb-1">
                          <span className="text-[var(--text-secondary)]">Existing Sensor/Data</span>
                          <span className="font-mono">{formatCurrency(rec.economic_impact.assetsentinel?.sensor_data_cost)}</span>
                        </div>
                        <div className="flex justify-between items-center text-sm border-b border-dashed border-[var(--success-border)] pb-1">
                          <span className="text-[var(--text-secondary)]">Planned Intervention</span>
                          <span className="font-mono">{formatCurrency(rec.economic_impact.assetsentinel?.planned_intervention_cost + (rec.economic_impact.assetsentinel?.planned_inspection_cost || 0))}</span>
                        </div>
                        <div className="flex justify-between items-center text-sm border-b border-dashed border-[var(--success-border)] pb-1">
                          <span className="text-[var(--text-secondary)]">Planned Downtime</span>
                          <span className="font-mono">{formatCurrency(rec.economic_impact.assetsentinel?.planned_downtime_cost)}</span>
                        </div>
                        <div className="flex justify-between items-center text-sm border-b border-dashed border-[var(--success-border)] pb-1">
                          <span className="text-[var(--text-secondary)]">Residual Failure Exposure</span>
                          <span className="font-mono">{formatCurrency(rec.economic_impact.assetsentinel?.residual_failure_cost)}</span>
                        </div>
                        <div className="flex justify-between items-center pt-2">
                          <span className="text-sm font-bold text-[var(--success-text)]">TOTAL</span>
                          <span className="font-mono font-bold text-[15px] text-[var(--success-text)]">{formatCurrency(rec.economic_impact.assetsentinel?.total)}</span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Highlight Section */}
                    <div className="mt-6 p-5 rounded-xl bg-[var(--surface-elevated)] border border-[var(--border-default)] flex flex-wrap justify-around items-center gap-4">
                      <div className="text-center">
                        <p className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)] mb-1">Potential Cost Avoided</p>
                        <p className="text-xl font-bold font-mono" style={{ color: (rec.economic_impact.potential_cost_avoided ?? 0) >= 0 ? "var(--success-text)" : "var(--danger-text)" }}>
                          {(rec.economic_impact.potential_cost_avoided ?? 0) >= 0 ? "+" : ""}{formatCurrency(rec.economic_impact.potential_cost_avoided ?? 0)}
                        </p>
                      </div>
                      <div className="w-px h-10 bg-[var(--border-subtle)] hidden sm:block"></div>
                      <div className="text-center">
                        <p className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)] mb-1">Net Economic Benefit</p>
                        <p className="text-xl font-bold font-mono text-[var(--text-primary)]">
                          {formatCurrency(rec.economic_impact.net_economic_benefit)}
                        </p>
                      </div>
                      <div className="w-px h-10 bg-[var(--border-subtle)] hidden sm:block"></div>
                      <div className="text-center">
                        <p className="text-[11px] font-bold uppercase tracking-wider text-[var(--brand-accent)] mb-1">Estimated ROI</p>
                        <p className="text-xl font-bold font-mono text-[var(--brand-accent)]">
                          {rec.economic_impact.roi_percent?.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-[var(--text-muted)]">No economic impact available. Run Readiness pipeline.</p>
                )}
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
}

export default Assets;