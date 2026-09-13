export type ReadinessStatus =
  | "READY"
  | "CONDITIONALLY_READY"
  | "NOT_READY";

export interface ReadinessResponse {
  asset_id: string;
  mission_id: string;
  readiness_score: number;
  readiness_status: ReadinessStatus;
  reasons: string[];
  evidence: string[];
  timestamp: string;
}