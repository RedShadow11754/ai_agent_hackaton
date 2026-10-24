/** Ordered attack sequence. Every step cites evidence offsets. */

import type { AttackStep } from "../types/api";
import { EvidenceHighlight } from "./EvidenceHighlight";

export function AttackSequence({ steps }: { steps: AttackStep[] }) {
  if (steps.length === 0) {
    return (
      <p className="text-sm text-slate-500">
        No attack sequence was inferred. This does not mean the message is safe.
      </p>
    );
  }

  return (
    <ol className="space-y-3">
      {steps.map((step) => (
        <li key={step.index} className="rounded-md border border-slate-200 bg-white p-4">
          <p className="text-sm font-medium text-slate-900">
            Step {step.index}. {step.description}
          </p>
          {step.intent ? (
            <p className="mt-1 text-sm text-slate-600">Likely intent: {step.intent}</p>
          ) : null}
          <div className="mt-2">
            <EvidenceHighlight message="" evidence={step.evidence} />
          </div>
        </li>
      ))}
    </ol>
  );
}
