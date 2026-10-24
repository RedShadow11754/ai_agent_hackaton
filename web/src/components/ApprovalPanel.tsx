/**
 * Approval gate UI: a checkbox plus Approve & Save / Discard.
 *
 * Hard rule 2: the save button stays disabled until the analyst ticks the box,
 * and the request always carries approved: true. The backend re-checks this and
 * returns 403 APPROVAL_REQUIRED otherwise.
 */

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { createIncident } from "../api/incidents";
import type { AssessmentResponse } from "../types/api";
import { ErrorBanner } from "./ErrorBanner";

export function ApprovalPanel({
  payload,
  message,
  draft,
  draftEdited,
  onSaved,
}: {
  payload: AssessmentResponse;
  /** Original message text, saved alongside the assessment. */
  message: string;
  draft: string;
  draftEdited: boolean;
  onSaved?: (incidentId: string) => void;
}) {
  const [approved, setApproved] = useState(false);

  const save = useMutation({
    mutationFn: () =>
      createIncident({
        approved: true,
        payload,
        message,
        draft: draftEdited ? draft : null,
        draft_edited: draftEdited,
      }),
    onSuccess: (created) => onSaved?.(created.id),
  });

  return (
    <section className="rounded-md border border-slate-300 bg-white p-4">
      <h2 className="text-sm font-semibold text-slate-900">Approve and save</h2>

      <label className="mt-3 flex items-start gap-2 text-sm text-slate-700">
        <input
          type="checkbox"
          className="mt-1"
          checked={approved}
          onChange={(event) => setApproved(event.target.checked)}
        />
        <span>
          I reviewed the assessment and the draft, and I approve saving this as an
          incident.
        </span>
      </label>

      {save.isError ? <ErrorBanner error={save.error} onRetry={() => save.mutate()} /> : null}

      {save.isSuccess ? (
        <p className="mt-3 text-sm text-emerald-700">
          Saved as {save.data.id} ({save.data.status}).
        </p>
      ) : null}

      <div className="mt-4 flex gap-2">
        <button
          type="button"
          disabled={!approved || save.isPending}
          onClick={() => save.mutate()}
          className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
        >
          {save.isPending ? "Saving..." : "Approve & Save"}
        </button>
        <button
          type="button"
          onClick={() => setApproved(false)}
          className="rounded border border-slate-300 px-4 py-2 text-sm text-slate-700"
        >
          Discard approval
        </button>
      </div>
    </section>
  );
}
