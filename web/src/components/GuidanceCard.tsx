/** One internal guidance passage, cited by its real database ID. */

import type { GuidanceRef } from "../types/api";

export function GuidanceCard({ guidance }: { guidance: GuidanceRef }) {
  return (
    <article className="rounded-md border border-slate-200 bg-white p-4">
      <header className="flex items-baseline gap-2">
        <span className="rounded bg-slate-900 px-2 py-0.5 text-xs font-semibold text-white">
          {guidance.id}
        </span>
        <h3 className="text-sm font-semibold text-slate-900">{guidance.title}</h3>
      </header>
      <p className="mt-2 text-sm text-slate-600">{guidance.body}</p>
      {guidance.tags.length > 0 ? (
        <p className="mt-2 text-xs text-slate-400">tags: {guidance.tags.join(", ")}</p>
      ) : null}
    </article>
  );
}
