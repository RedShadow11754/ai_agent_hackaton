/**
 * TypeScript mirrors of the backend Pydantic schemas (`backend/app/schemas`).
 *
 * Keep these in sync with the API contract. Hard rule 5: there is no "safe"
 * status or band anywhere in these types.
 */

export type IndicatorStatus = "detected" | "not_detected" | "not_assessable";

export type RiskBand = "High" | "Elevated" | "Moderate" | "Low / Inconclusive";

export type ActivityKind = "tool_call" | "tool_result" | "error" | "approval" | "save";

export interface Evidence {
  /** Inclusive character offset into the original message. */
  start: number;
  /** Exclusive character offset into the original message. */
  end: number;
  /** Exactly message.slice(start, end). */
  text: string;
}

export interface Indicator {
  id: string;
  label: string;
  status: IndicatorStatus;
  detail: string;
  evidence: Evidence[];
  weight?: number | null;
}

export interface RiskBreakdownItem {
  indicator_id: string;
  label: string;
  status: IndicatorStatus;
  weight: number;
  points: number;
  reason: string;
}

export interface RiskAssessment {
  score: number;
  band: RiskBand;
  breakdown: RiskBreakdownItem[];
}

export interface UrlFinding {
  /** Raw string as pasted. Render defanged via UrlList, never as a link. */
  url: string;
  defanged: string;
  host: string;
  observations: string[];
}

export interface AttackStep {
  index: number;
  description: string;
  intent: string;
  evidence: Evidence[];
}

export interface GuidanceRef {
  /** Real guidance ID from the database, e.g. "SEC-01". */
  id: string;
  title: string;
  body: string;
  tags: string[];
}

export interface ValidationResult {
  passed: boolean;
  issues: string[];
}

export interface ActivityEntry {
  id?: number | null;
  investigation_id?: string | null;
  incident_id?: string | null;
  created_at?: string | null;
  kind: ActivityKind;
  tool_name?: string | null;
  payload: Record<string, unknown>;
}

export interface AssessmentResponse {
  type: "assessment";
  investigation_id: string;
  urls: UrlFinding[];
  indicators: Indicator[];
  evidence: Evidence[];
  attack_sequence: AttackStep[];
  guidance: GuidanceRef[];
  risk: RiskAssessment;
  assessment: string;
  next_steps: string[];
  draft: string;
  validation: ValidationResult;
  activity: ActivityEntry[];
}

export interface ClarificationResponse {
  type: "clarification";
  investigation_id: string;
  question: string;
}

export type InvestigateResponse = AssessmentResponse | ClarificationResponse;

export interface InvestigateRequest {
  message: string;
  sender?: string | null;
  context?: string | null;
}

export interface CreateIncidentRequest {
  approved: boolean;
  payload: AssessmentResponse;
  /** Original message text, stored with the incident for the record. */
  message?: string;
  reviewed_by?: string | null;
  draft_edited?: boolean;
  draft?: string | null;
}

export interface IncidentCreatedResponse {
  id: string;
  status: string;
}

export interface IncidentSummary {
  id: string;
  created_at: string;
  risk_band: string;
  risk_score: number;
  status: string;
  message_preview: string;
}

export interface IncidentDetail {
  id: string;
  created_at: string;
  approved_at?: string | null;
  reviewed_by?: string | null;
  status: string;
  message: string;
  assessment: AssessmentResponse;
}

/** Uniform error shape returned by every API route. */
export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
  };
}
