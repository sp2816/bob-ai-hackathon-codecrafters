/**
 * AssetSentinel — API Types
 *
 * Exactly mirrors FastAPI/Pydantic response models.
 * Do NOT add fields not present in the backend schemas.
 * Do NOT import these for readiness calculations — that is the backend's job.
 */

// ── Asset ──────────────────────────────────────────────────────────────────
export interface ApiAsset {
  asset_id: string;
  asset_name: string;
  asset_type: string;
  unit: string;
  operational_hours: number;
  current_status: string; // READY | CONDITIONALLY_READY | NOT_READY
  readiness_score: number | null;
}

// ── Prediction / Anomaly ───────────────────────────────────────────────────
export type RiskCategory = "LOW" | "MEDIUM" | "HIGH";
export type AnomalyStatus = "NORMAL" | "HIGH";
export type AnomalySeverity = "LOW" | "MEDIUM" | "HIGH";

export interface ApiPrediction {
  prediction_id: string;
  asset_id: string;
  component_id: string;
  failure_probability: number; // 0–1, NOT RUL
  risk_category: RiskCategory;
  timestamp: string;
}

export interface ApiAnomaly {
  anomaly_id: string;
  asset_id: string;
  component_id: string;
  anomaly_score: number;
  anomaly_status: AnomalyStatus;
  anomaly_severity: AnomalySeverity;
  sensor: string;
  timestamp: string;
}

// ── Readiness ──────────────────────────────────────────────────────────────
export type ReadinessStatus = "READY" | "CONDITIONALLY_READY" | "NOT_READY";

export interface ApiEvidenceObject {
  asset_id: string;
  component: string;
  failure_risk: number;
  risk_level: string;
  anomaly: {
    sensor: string;
    severity: string;
  };
  maintenance: {
    hours_since_service: number;
    inspection_status: string;
  };
  criticality: string;
  mission_impact: string;
}

export interface ApiReadinessResult {
  result_id: string;
  asset_id: string;
  mission_id: string | null;
  readiness_score: number;
  readiness_status: ReadinessStatus;
  reasons: string[] | null;
  evidence: ApiEvidenceObject[] | Record<string, unknown> | null;
  timestamp: string;
}

// ── Fleet ──────────────────────────────────────────────────────────────────
export interface ApiFleetSummary {
  total: number;
  counts: {
    READY: number;
    CONDITIONALLY_READY: number;
    NOT_READY: number;
    UNKNOWN: number;
  };
}

// ── Maintenance ────────────────────────────────────────────────────────────
export type MaintenanceRecommendationStatus = "OPEN" | "IN_PROGRESS" | "RESOLVED";

export interface ApiMaintenanceRecommendation {
  recommendation_id: string;
  asset_id: string;
  component_id: string;
  priority: number; // numeric rank from the priority engine
  action: string;
  reason: string;
  risk: string;
  mission_impact: string;
  urgency: string;
  status: MaintenanceRecommendationStatus;
}

// ── Notifications ──────────────────────────────────────────────────────────
export interface ApiNotification {
  id: string;
  title: string;
  message: string;
  severity: string;
  source: string;
  asset_id: string | null;
  timestamp: string;
}
