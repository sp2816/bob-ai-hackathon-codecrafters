export type RiskCategory =
  | "LOW"
  | "MEDIUM"
  | "HIGH";

export type AnomalyStatus =
  | "NORMAL"
  | "HIGH";

export type AnomalySeverity =
  | "LOW"
  | "MEDIUM"
  | "HIGH";

export interface FailurePrediction {
  prediction_id: string;
  asset_id: string;
  component_id: string;
  failure_probability: number;
  risk_category: RiskCategory;
  timestamp: string;
}

export interface AnomalyResult {
  asset_id: string;
  component_id: string;
  anomaly_score: number;
  anomaly_status: AnomalyStatus;
  anomaly_severity: AnomalySeverity;
  sensor: string;
  timestamp: string;
}