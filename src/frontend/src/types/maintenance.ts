export type MaintenancePriority =
  | "LOW"
  | "MEDIUM"
  | "HIGH"
  | "CRITICAL";

export type MaintenanceUrgency =
  | "LOW"
  | "MEDIUM"
  | "HIGH"
  | "IMMEDIATE";

export type MaintenanceStatus =
  | "OPEN"
  | "IN_PROGRESS"
  | "COMPLETED";

export interface MaintenanceRecommendation {
  recommendation_id: string;
  asset_id: string;
  component_id: string;
  priority: MaintenancePriority;
  action: string;
  reason: string;
  risk: string;
  mission_impact: string;
  urgency: MaintenanceUrgency;
  status: MaintenanceStatus;
}