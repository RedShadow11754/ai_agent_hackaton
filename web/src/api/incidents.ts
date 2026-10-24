/** Incident endpoints. Saving requires approved=true (hard rule 2). */

import type {
  CreateIncidentRequest,
  IncidentCreatedResponse,
  IncidentDetail,
  IncidentSummary,
} from "../types/api";
import { apiFetch } from "./client";

/**
 * Save a reviewed incident.
 *
 * The backend rejects `approved: false` with 403 APPROVAL_REQUIRED, so the
 * ApprovalPanel must only call this after the analyst ticks the checkbox.
 *
 * TODO: surface the generated INC-#### id in the UI after success.
 */
export async function createIncident(
  request: CreateIncidentRequest,
): Promise<IncidentCreatedResponse> {
  return apiFetch<IncidentCreatedResponse>("/api/incidents", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/** List recent incidents (newest first). TODO: implement the backend route. */
export async function listIncidents(): Promise<IncidentSummary[]> {
  return apiFetch<IncidentSummary[]>("/api/incidents");
}

/** Fetch one incident with its full assessment. */
export async function getIncident(id: string): Promise<IncidentDetail> {
  return apiFetch<IncidentDetail>(`/api/incidents/${encodeURIComponent(id)}`);
}

/** Fetch the audit trail for one incident. */
export async function getIncidentActivity(id: string): Promise<IncidentDetail["assessment"]["activity"]> {
  return apiFetch(`/api/incidents/${encodeURIComponent(id)}/activity`);
}
