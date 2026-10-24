/**
 * Shown wherever a result is uncertain. Background color reflects the risk score:
 * green (0) -> yellow (50) -> red (100). Exists so the UI never implies that a
 * lack of detected indicators means the message is safe.
 */

export function UncertaintyBanner({
  message,
  score,
}: {
  message: string;
  /** Risk score 0-100, used for the gradient background. */
  score?: number;
}) {
  // Clamp score to 0-100
  const clamped = typeof score === "number" ? Math.max(0, Math.min(100, score)) : 50;

  // Interpolate between green (0), amber (50), red (100)
  const hue = Math.round((1 - clamped / 100) * 120); // 120 = green, 0 = red
  const bgStyle: React.CSSProperties = {
    background: `hsl(${hue}, 70%, 92%)`,
    borderColor: `hsl(${hue}, 70%, 60%)`,
  };

  return (
    <div
      role="status"
      className="rounded-md border px-4 py-3 text-sm text-slate-800"
      style={bgStyle}
    >
      <span className="font-medium">Uncertainty: </span>
      {message}
    </div>
  );
}
