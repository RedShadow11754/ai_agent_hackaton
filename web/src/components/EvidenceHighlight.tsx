/**
 * Renders quoted evidence spans. When `message` is supplied the spans are
 * highlighted inside the original text; otherwise the quotes are listed.
 *
 * Hard rule 6: all text is rendered as plain text - never dangerouslySetInnerHTML.
 */

import type { Evidence } from "../types/api";

function quoteOf(message: string, evidence: Evidence): string {
  // Prefer the exact slice so a bad offset is visible rather than hidden.
  return message.slice(evidence.start, evidence.end) || evidence.text;
}

export function EvidenceHighlight({
  message,
  evidence,
}: {
  message: string;
  evidence: Evidence[];
}) {
  if (evidence.length === 0) {
    return <p className="text-xs text-slate-400">No supporting quotes.</p>;
  }

  return (
    <ul className="space-y-1">
      {evidence.map((span) => (
        <li
          key={`${span.start}-${span.end}`}
          className="rounded border-l-2 border-amber-400 bg-amber-50 px-2 py-1 text-xs text-slate-700"
        >
          <span className="message-text">{quoteOf(message, span)}</span>
          <span className="ml-2 text-slate-400">
            [chars {span.start}-{span.end}]
          </span>
        </li>
      ))}
    </ul>
  );
}
