/** POST /api/investigate - runs the agent. Saves nothing. */

import type { InvestigateRequest, InvestigateResponse } from "../types/api";
import { apiFetch } from "./client";

/**
 * Send one pasted message for investigation.
 *
 * Text only: the backend never fetches any URL found in the message.
 * Returns either a clarification question or a full assessment.
 *
 * TODO: expose an AbortSignal so the analyst can cancel a slow request.
 */
export async function investigate(
  request: InvestigateRequest,
  signal?: AbortSignal,
): Promise<InvestigateResponse> {
  return apiFetch<InvestigateResponse>("/api/investigate", {
    method: "POST",
    body: JSON.stringify(request),
    signal,
  });
}
