/** Colour-coded risk band pill. Hard rule 5: there is no "safe" band. */

import type { RiskBand } from "../types/api";

const BAND_STYLES: Record<RiskBand, string> = {
  High: "bg-red-100 text-red-800 border-red-300",
  Elevated: "bg-orange-100 text-orange-800 border-orange-300",
  Moderate: "bg-amber-100 text-amber-800 border-amber-300",
  "Low / Inconclusive": "bg-slate-100 text-slate-700 border-slate-300",
};

export function RiskBadge({ band, score }: { band: RiskBand; score?: number }) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-medium ${BAND_STYLES[band]}`}
    >
      {band}
      {typeof score === "number" ? (
        <span className="text-xs font-normal opacity-70">score {score}/100</span>
      ) : null}
    </span>
  );
}
