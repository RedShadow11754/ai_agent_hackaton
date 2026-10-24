/** "/review" - edit the draft, then approve and save (or discard). */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ActivityLog } from "../components/ActivityLog";
import { ApprovalPanel } from "../components/ApprovalPanel";
import { GuidanceDraftEditor } from "../components/GuidanceDraftEditor";
import { RiskBadge } from "../components/RiskBadge";
import { useInvestigation } from "../state/InvestigationContext";

export function ReviewPage() {
  const navigate = useNavigate();
  const { message, assessment } = useInvestigation();
  const [draft, setDraft] = useState("");
  const [draftEdited, setDraftEdited] = useState(false);

  // Seed the editor from the model's draft whenever a new assessment arrives.
  useEffect(() => {
    setDraft(assessment?.draft ?? "");
    setDraftEdited(false);
  }, [assessment]);

  if (!assessment) {
    return (
      <div className="space-y-4">
        <h1 className="text-lg font-semibold text-slate-900">Review and save</h1>
        <p className="text-sm text-slate-500">
          Nothing to review yet. Investigate a message first.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-lg font-semibold text-slate-900">Review and save</h1>
        <RiskBadge band={assessment.risk.band} score={assessment.risk.score} />
      </header>

      {assessment.validation.passed ? null : (
        <div role="alert" className="rounded-md border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          <p className="font-medium">Validation issues</p>
          <ul className="mt-1 list-inside list-disc">
            {assessment.validation.issues.map((issue) => (
              <li key={issue}>{issue}</li>
            ))}
          </ul>
        </div>
      )}

      <GuidanceDraftEditor
        value={draft}
        onChange={(next) => {
          setDraft(next);
          setDraftEdited(next !== assessment.draft);
        }}
      />

      <ApprovalPanel
        payload={assessment}
        message={message}
        draft={draft}
        draftEdited={draftEdited}
        onSaved={(incidentId) => navigate(`/incidents/${incidentId}`)}
      />

      <ActivityLog entries={assessment.activity} />

      <button
        type="button"
        onClick={() => navigate("/results")}
        className="text-sm text-slate-500 underline"
      >
        Back to results
      </button>
    </div>
  );
}