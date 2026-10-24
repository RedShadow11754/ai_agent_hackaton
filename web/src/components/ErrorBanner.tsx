/** Error display with an optional Retry action. */

import { ApiError } from "../api/client";

function describe(error: unknown): { code: string; message: string } {
  if (error instanceof ApiError) {
    return { code: error.code, message: error.message };
  }
  if (error instanceof Error) {
    return { code: "UNEXPECTED_ERROR", message: error.message };
  }
  return { code: "UNEXPECTED_ERROR", message: String(error) };
}

export function ErrorBanner({
  error,
  onRetry,
}: {
  error: unknown;
  onRetry?: () => void;
}) {
  const { code, message } = describe(error);

  return (
    <div
      role="alert"
      className="mt-3 rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800"
    >
      <p className="font-medium">{code}</p>
      <p className="mt-1">{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-2 rounded border border-red-400 bg-white px-3 py-1 text-xs font-medium"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}
