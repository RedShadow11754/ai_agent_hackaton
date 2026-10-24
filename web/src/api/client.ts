/**
 * Fetch wrapper: one place that knows the base path, the error envelope, and
 * JSON encoding. Never attach secrets here (hard rule 4).
 */

import type { ApiErrorBody } from "../types/api";

/** Error carrying the backend's `{code, message}` envelope. */
export class ApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

/** Type guard for the shared error envelope. */
function isApiErrorBody(value: unknown): value is ApiErrorBody {
  if (typeof value !== "object" || value === null) return false;
  const error = (value as { error?: unknown }).error;
  return (
    typeof error === "object" &&
    error !== null &&
    typeof (error as { code?: unknown }).code === "string"
  );
}

/**
 * Perform a JSON request against the API.
 *
 * @throws {ApiError} for any non-2xx response, including network failures.
 *
 * TODO: add an AbortController timeout and a single retry for 502/503.
 */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
    });
  } catch (cause) {
    throw new ApiError(0, "NETWORK_ERROR", `Could not reach the API: ${String(cause)}`);
  }

  const body: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    if (isApiErrorBody(body)) {
      throw new ApiError(response.status, body.error.code, body.error.message);
    }
    throw new ApiError(response.status, "HTTP_ERROR", response.statusText);
  }

  return body as T;
}
