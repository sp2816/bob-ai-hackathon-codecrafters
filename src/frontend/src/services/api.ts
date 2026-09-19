/**
 * AssetSentinel — API Service Layer
 *
 * All backend communication goes through here.
 * Do NOT calculate readiness, failure risk, or maintenance priority here.
 * The backend is the single source of truth for all computed values.
 */
import axios from "axios";
import type {
  ApiAsset,
  ApiPrediction,
  ApiAnomaly,
  ApiReadinessResult,
  ApiFleetSummary,
  ApiMaintenanceRecommendation,
  ApiNotification,
  AssetCreateRequest,
  AssetCreateResponse,
  ApiCostAssumption,
  ApiTimelineItem,
} from "../types/api";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://127.0.0.1:8000";

const http = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 15_000,
});

// ── Assets ─────────────────────────────────────────────────────────────────

export async function getAssets(): Promise<ApiAsset[]> {
  const { data } = await http.get<ApiAsset[]>("/assets/");
  return data;
}

export async function getAsset(assetId: string): Promise<ApiAsset> {
  const { data } = await http.get<ApiAsset>(`/assets/${assetId}`);
  return data;
}

/**
 * Add a new asset and run the full ML + Readiness + Maintenance pipeline.
 * Uses extended timeout (60s) because single-component ML inference can take several seconds.
 * Returns complete analysis results from the backend — no frontend calculations.
 */
export async function createAsset(request: AssetCreateRequest): Promise<AssetCreateResponse> {
  const { data } = await http.post<AssetCreateResponse>("/assets/", request, {
    timeout: 60_000,
  });
  window.dispatchEvent(new Event("refresh-notifications"));
  return data;
}

// ── Predictions / Anomalies ────────────────────────────────────────────────

export async function getPredictions(): Promise<ApiPrediction[]> {
  const { data } = await http.get<ApiPrediction[]>("/predictions/");
  return data;
}

export async function getAnomalies(): Promise<ApiAnomaly[]> {
  const { data } = await http.get<ApiAnomaly[]>("/predictions/anomalies");
  return data;
}

// ── Readiness ──────────────────────────────────────────────────────────────

export async function getFleetReadinessSummary(): Promise<ApiFleetSummary> {
  const { data } = await http.get<ApiFleetSummary>("/fleet/readiness-summary");
  return data;
}

export async function getMissionReadiness(missionId: string): Promise<ApiReadinessResult[]> {
  const { data } = await http.get<ApiReadinessResult[]>(`/missions/${missionId}/readiness`);
  return data;
}

export async function getFleet(): Promise<ApiAsset[]> {
  const { data } = await http.get<ApiAsset[]>("/fleet/");
  return data;
}

// ── Maintenance ────────────────────────────────────────────────────────────

export async function getMaintenanceRecommendations(): Promise<ApiMaintenanceRecommendation[]> {
  const { data } = await http.get<ApiMaintenanceRecommendation[]>("/maintenance/recommendations");
  return data;
}

export async function getCostAssumptions(): Promise<ApiCostAssumption[]> {
  const { data } = await http.get<ApiCostAssumption[]>("/cost-assumptions/");
  return data;
}

export async function updateCostAssumption(componentType: string, payload: Partial<ApiCostAssumption>): Promise<ApiCostAssumption> {
  const { data } = await http.put<ApiCostAssumption>(`/cost-assumptions/${componentType}`, payload);
  return data;
}

export async function getAssetTimeline(assetId: string): Promise<{ timeline: ApiTimelineItem[] }> {
  const { data } = await http.get<{ timeline: ApiTimelineItem[] }>(`/maintenance/timeline/${assetId}`);
  return data;
}

// ── Pipeline triggers ──────────────────────────────────────────────────────

export async function runMlPipeline(): Promise<{ status: string; stored: Record<string, number> }> {
  const { data } = await http.post("/fleet/run-ml");
  window.dispatchEvent(new Event("refresh-notifications"));
  return data;
}

export async function runReadinessPipeline(): Promise<{ status: string; generated: Record<string, number> }> {
  const { data } = await http.post("/fleet/run-readiness");
  window.dispatchEvent(new Event("refresh-notifications"));
  return data;
}

// ── Notifications ──────────────────────────────────────────────────────────

export async function getNotifications(): Promise<ApiNotification[]> {
  const { data } = await http.get<ApiNotification[]>("/notifications/");
  return data;
}

// ── Chat ───────────────────────────────────────────────────────────────────

export async function sendChatMessage(message: string): Promise<{ response: string }> {
  const { data } = await http.post<{ response: string }>("/chat/", { message });
  return data;
}

// ── Shared Utilities ───────────────────────────────────────────────────────

export function formatCurrency(value: number | undefined | null): string {
  if (value === undefined || value === null) return "₹0";
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(value);
}
