/** One indicator with its tri-state status and supporting evidence. */

import type { Indicator, IndicatorStatus } from "../types/api";
import { EvidenceHighlight } from "./EvidenceHighlight";

const STATUS_LABELS: Record<IndicatorStatus, string> = {
  detected: "Detected",
  not_detected: "Not detected",
  not_assessable: "Not assessable",
};

const STATUS_STYLES: Record<IndicatorStatus, string> = {
  detected: "text-red-700",
  not_detected: "text-slate-600",
  not_assessable: "text-slate-400",
};

export function IndicatorCard({ indicator }: { indicator: Indicator }) {
  return (
    <article className="rounded-md border border-slate-200 bg-white p-4">
      <header className="flex items-start justify-between gap-3">
        <h3 className="text-sm font-semibold text-slate-900">{indicator.label}</h3>
        <span className={`text-xs font-medium ${STATUS_STYLES[indicator.status]}`}>
          {STATUS_LABELS[indicator.status]}
        </span>
      </header>
      {indicator.detail ? (
        <p className="mt-2 text-sm text-slate-600">{indicator.detail}</p>
      ) : null}
      {indicator.evidence.length > 0 ? (
        <div className="mt-3">
          {/* Offsets are relative to the message; show the quoted spans only. */}
          <EvidenceHighlight message="" evidence={indicator.evidence} />
        </div>
      ) : null}
    </article>
  );
}
