import type { Asset } from "../types/asset";
import type {
  AnomalyResult,
  FailurePrediction,
} from "../types/prediction";
import type { ReadinessResponse } from "../types/readiness";
import type { MaintenanceRecommendation } from "../types/maintenance";

/**
 * Canonical demo asset from the integration contract.
 */
export const demoAsset: Asset = {
  asset_id: "AS-1047",
  name: "Asset AS-1047",
  status: "OPERATIONAL",
  component_id: "COMP-BRG-01",
  component_name: "Main Bearing",
  criticality: "HIGH",
  last_service: "2026-03-12",
};

/**
 * Additional dashboard assets.
 */
export const dashboardAssets: Asset[] = [
  demoAsset,

  {
    asset_id: "AS-1032",
    name: "Asset AS-1032",
    status: "OPERATIONAL",
    component_id: "COMP-ENG-02",
    component_name: "Engine Assembly",
    criticality: "MEDIUM",
    last_service: "2026-03-08",
  },

  {
    asset_id: "AS-1088",
    name: "Asset AS-1088",
    status: "OPERATIONAL",
    component_id: "COMP-HYD-03",
    component_name: "Hydraulic System",
    criticality: "MEDIUM",
    last_service: "2026-03-05",
  },
];

/**
 * Failure prediction for the canonical demo asset.
 *
 * Note:
 * failure_probability is a probability.
 * It must NOT be interpreted as RUL.
 */
export const demoFailurePrediction: FailurePrediction = {
  prediction_id: "PRED-1047-001",
  asset_id: "AS-1047",
  component_id: "COMP-BRG-01",
  failure_probability: 0.87,
  risk_category: "HIGH",
  timestamp: "2026-09-13T09:30:00Z",
};

/**
 * Anomaly result for the canonical demo asset.
 */
export const demoAnomaly: AnomalyResult = {
  asset_id: "AS-1047",
  component_id: "COMP-BRG-01",
  anomaly_score: 0.91,
  anomaly_status: "HIGH",
  anomaly_severity: "HIGH",
  sensor: "Vibration",
  timestamp: "2026-09-13T09:25:00Z",
};

/**
 * Mission readiness result.
 *
 * Canonical missions:
 * MSN-001 = Training
 * MSN-002 = Patrol
 * MSN-003 = Strike
 */
export const missionReadiness: ReadinessResponse[] = [
  {
    asset_id: "AS-1047",
    mission_id: "MSN-001",
    readiness_score: 94,
    readiness_status: "CONDITIONALLY_READY",
    reasons: [
      "High vibration anomaly detected",
      "Elevated failure probability",
      "Bearing inspection recommended",
    ],
    evidence: [
      "Vibration anomaly score: 0.91",
      "Failure probability: 0.87",
      "Component criticality: HIGH",
    ],
    timestamp: "2026-09-13T09:35:00Z",
  },

  {
    asset_id: "AS-1047",
    mission_id: "MSN-002",
    readiness_score: 82,
    readiness_status: "CONDITIONALLY_READY",
    reasons: [
      "Elevated component risk",
      "Maintenance recommended before extended operation",
    ],
    evidence: [
      "Failure probability: 0.87",
      "High-severity vibration anomaly",
    ],
    timestamp: "2026-09-13T09:35:00Z",
  },

  {
    asset_id: "AS-1047",
    mission_id: "MSN-003",
    readiness_score: 61,
    readiness_status: "NOT_READY",
    reasons: [
      "High-criticality component at elevated failure risk",
      "Bearing inspection required before mission",
    ],
    evidence: [
      "Failure probability: 0.87",
      "Vibration anomaly severity: HIGH",
      "Component criticality: HIGH",
    ],
    timestamp: "2026-09-13T09:35:00Z",
  },
];

/**
 * Maintenance recommendation generated from the existing
 * prediction / anomaly / readiness evidence.
 */
export const maintenanceRecommendations: MaintenanceRecommendation[] = [
  {
    recommendation_id: "REC-1047-001",
    asset_id: "AS-1047",
    component_id: "COMP-BRG-01",
    priority: "HIGH",
    action: "Inspect and replace main bearing if required",
    reason:
      "High vibration anomaly combined with elevated failure probability",
    risk: "Potential bearing failure",
    mission_impact:
      "May prevent high-criticality mission deployment",
    urgency: "HIGH",
    status: "OPEN",
  },
];

/**
 * Dashboard summary values.
 *
 * These are presentation-level values used by the current
 * dashboard UI and can later be replaced by API aggregation.
 */
export const dashboardSummary = {
  fleetHealth: 98.4,
  activeAlerts: 2,
  activeAlertLevel: "LOW",
  missionReadiness: 94,
  operationalProgress: 87,
  breakdown: 6,
  maintenance: 5,
  onlineAssets: 98,
};

/**
 * Mission schedule shown on the dashboard.
 */
export const missionSchedule = [
  {
    mission_id: "MSN-001",
    name: "Training",
    priority: "LOW",
    readiness_status: "READY",
  },
  {
    mission_id: "MSN-002",
    name: "Patrol",
    priority: "MEDIUM",
    readiness_status: "CONDITIONALLY_READY",
  },
  {
    mission_id: "MSN-003",
    name: "Strike",
    priority: "HIGH",
    readiness_status: "NOT_READY",
  },
];