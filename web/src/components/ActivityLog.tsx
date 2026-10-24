/** Collapsible audit log of tool calls, results, errors, approvals, and saves. */

import { useState } from "react";

import type { ActivityEntry } from "../types/api";

const KIND_STYLES: Record<ActivityEntry["kind"], string> = {
  tool_call: "text-sky-700",
  tool_result: "text-slate-600",
  error: "text-red-700",
  approval: "text-emerald-700",
  save: "text-emerald-800",
};

export function ActivityLog({ entries }: { entries: ActivityEntry[] }) {
  const [open, setOpen] = useState(false);

  return (
    <section className="rounded-md border border-slate-200 bg-white">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-slate-800"
        aria-expanded={open}
      >
        <span>Activity log ({entries.length})</span>
        <span className="text-xs text-slate-400">{open ? "hide" : "show"}</span>
      </button>

      {open ? (
        <ol className="border-t border-slate-200 px-4 py-3">
          {entries.length === 0 ? (
            <li className="text-xs text-slate-400">No activity recorded yet.</li>
          ) : (
            entries.map((entry, index) => (
              <li
                key={entry.id ?? `${entry.kind}-${index}`}
                className="border-b border-slate-100 py-2 last:border-0"
              >
                <p className={`text-xs font-medium ${KIND_STYLES[entry.kind]}`}>
                  {entry.kind}
                  {entry.tool_name ? `: ${entry.tool_name}` : ""}
                  {entry.created_at ? (
                    <span className="ml-2 font-normal text-slate-400">{entry.created_at}</span>
                  ) : null}
                </p>
                {Object.keys(entry.payload).length > 0 ? (
                  <pre className="mt-1 overflow-x-auto text-xs text-slate-500">
                    {JSON.stringify(entry.payload, null, 2)}
                  </pre>
                ) : null}
              </li>
            ))
          )}
        </ol>
      ) : null}
    </section>
  );
}
