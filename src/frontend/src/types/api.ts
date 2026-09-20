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
  economics?: {
    fleet_traditional_cost: number;
    fleet_assetsentinel_cost: number;
    fleet_potential_cost_avoided: number;
    fleet_deployment_cost: number;
    fleet_net_economic_benefit: number;
    fleet_roi_percent: number;
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
  decision?: string | null;
  economic_impact?: {
    traditional: {
      monitoring_cost: number;
      inspection_cost: number;
      preventive_maintenance_cost: number;
      expected_reactive_failure_cost: number;
      total: number;
    };
    assetsentinel: {
      sensor_data_cost: number;
      planned_inspection_cost: number;
      planned_intervention_cost: number;
      planned_downtime_cost: number;
      residual_failure_cost: number;
      total: number;
    };
    potential_cost_avoided: number;
    deployment_cost: number;
    net_economic_benefit: number;
    roi_percent: number;
  } | null;
  timeline?: ApiTimelineItem[] | null;
}

export interface ApiCostAssumption {
  component_type: string;
  inspection_cost: number;
  repair_cost: number;
  replacement_cost: number;
  failure_impact_cost: number;
  monitoring_cost_traditional: number;
  inspection_cost_traditional: number;
  preventive_maintenance_traditional: number;
  sensor_data_cost_assetsentinel: number;
  assetsentinel_deployment_cost: number;
  residual_failure_probability_multiplier: number;
  emergency_intervention_cost: number;
  emergency_maintenance_cost: number;
  downtime_cost_per_hour: number;
  planned_downtime_hours: number;
  emergency_downtime_hours: number;
  mission_disruption_cost: number;
}

export interface ApiTimelineItem {
  action: string;
  urgency: string;
  time: string;
  reason: string;
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

// ── Add Asset (POST /assets/) ───────────────────────────────────────────────

/** Synthetic condition profile for ML feature generation. Not historical telemetry. */
export type SensorCondition = "NORMAL" | "DEGRADING" | "CRITICAL";
export type AssetCriticality = "LOW" | "MEDIUM" | "HIGH";
export type MaintenanceStatus = "COMPLETED" | "OVERDUE" | "SCHEDULED";
export type MaintenanceType = "inspection" | "service" | "repair";

export interface ComponentInput {
  component_id: string;
  component_type: string;
  criticality: AssetCriticality;
  operating_hours: number;
  life_limit?: number;
  service_interval_hours: number;
  installation_date?: string;
}

export interface SensorInput {
  /** Synthetic condition profile driving the deterministic observation window */
  condition: SensorCondition;
  vibration: number;
  temperature: number;
  pressure: number;
  RPM: number;
}

export interface MaintenanceInput {
  maintenance_type: MaintenanceType;
  maintenance_date: string;
  technician_action: string;
  status: MaintenanceStatus;
  hours_since_service: number;
  notes?: string;
}

export interface AssetCreateRequest {
  asset_id: string;
  asset_name: string;
  asset_type: string;
  unit: string;
  operational_hours: number;
  component: ComponentInput;
  sensors: SensorInput;
  maintenance: MaintenanceInput;
}

export interface PredictionSummary {
  prediction_id: string;
  failure_probability: number;
  risk_category: RiskCategory;
}

export interface AnomalySummary {
  anomaly_id: string;
  anomaly_status: AnomalyStatus;
  anomaly_severity: AnomalySeverity;
  sensor: string;
}

export interface ReadinessSummary {
  readiness_status: ReadinessStatus;
  readiness_score: number;
  reasons: string[];
}

export interface RecommendationSummary {
  recommendation_id: string;
  action: string;
  priority: number;
  urgency: string;
  risk: string;
  decision?: string | null;
  economic_impact?: Record<string, any> | null;
}

export interface AssetCreateResponse {
  asset: ApiAsset;
  prediction: PredictionSummary;
  anomaly: AnomalySummary;
  readiness: ReadinessSummary;
  recommendation: RecommendationSummary | null;
  pipeline_note: string;
}
