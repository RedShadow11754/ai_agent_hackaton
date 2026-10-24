/** "/results" - read-only assessment: indicators, evidence, risk, guidance. */

import { useNavigate } from "react-router-dom";

import { ActivityLog } from "../components/ActivityLog";
import { AttackSequence } from "../components/AttackSequence";
import { ClarificationPrompt } from "../components/ClarificationPrompt";
import { EvidenceHighlight } from "../components/EvidenceHighlight";
import { GuidanceCard } from "../components/GuidanceCard";
import { IndicatorCard } from "../components/IndicatorCard";
import { RiskBadge } from "../components/RiskBadge";
import { UncertaintyBanner } from "../components/UncertaintyBanner";
import { UrlList } from "../components/UrlList";
import { useInvestigation } from "../state/InvestigationContext";
import type { Indicator } from "../types/api";

/** Map indicator IDs to their display group. */
function groupIndicators(indicators: Indicator[]): Record<string, Indicator[]> {
  const groups: Record<string, Indicator[]> = {
    "Link and sender signals": [],
    "Content and request signals": [],
    "Social-engineering tactics": [],
  };

  for (const ind of indicators) {
    if (ind.status !== "detected") continue; // Only show detected

    if (
      ind.id === "link_present" ||
      ind.id === "sender_domain_mismatch" ||
      ind.id === "ip_literal_host" ||
      ind.id === "attachment_present"
    ) {
      groups["Link and sender signals"].push(ind);
    } else if (
      ind.id === "urgency_language" ||
      ind.id === "credential_request" ||
      ind.id === "payment_change"
    ) {
      groups["Content and request signals"].push(ind);
    } else {
      // urgency, authority_impersonation, secrecy, fear, reward
      groups["Social-engineering tactics"].push(ind);
    }
  }

  // Remove empty groups
  return Object.fromEntries(
    Object.entries(groups).filter(([, items]) => items.length > 0),
  );
}

export function ResultsPage() {
  const navigate = useNavigate();
  const { message, assessment, clarification } = useInvestigation();

  if (clarification) {
    return (
      <div className="space-y-4">
        <h1 className="text-lg font-semibold text-slate-900">Results</h1>
        <ClarificationPrompt
          question={clarification.question}
          onEditMessage={() => navigate("/")}
        />
      </div>
    );
  }

  if (!assessment) {
    return (
      <div className="space-y-4">
        <h1 className="text-lg font-semibold text-slate-900">Results</h1>
        <p className="text-sm text-slate-500">
          No investigation yet. Start on the Investigate page.
        </p>
      </div>
    );
  }

  const groupedIndicators = groupIndicators(assessment.indicators);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">Results</h1>
          <p className="text-xs text-slate-400">{assessment.investigation_id}</p>
        </div>
        <RiskBadge band={assessment.risk.band} score={assessment.risk.score} />
      </header>

      {/* Hard rule 5: never state or imply that the message is safe. */}
      <UncertaintyBanner message={assessment.assessment} score={assessment.risk.score} />

      {assessment.validation.passed ? null : (
        <div
          role="alert"
          className="rounded-md border border-red-300 bg-red-50 p-4 text-sm text-red-800"
        >
          <p className="font-medium">
            This assessment did not pass validation and cannot be saved.
          </p>
          <ul className="mt-1 list-inside list-disc">
            {assessment.validation.issues.map((issue) => (
              <li key={issue}>{issue}</li>
            ))}
          </ul>
        </div>
      )}

      <section>
        <h2 className="text-sm font-semibold text-slate-800">Message</h2>
        <pre className="message-text mt-2 max-h-64 overflow-auto rounded-md border border-slate-200 bg-white p-3 text-slate-800">
          {message}
        </pre>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slate-800">Indicators</h2>
        {Object.entries(groupedIndicators).length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">
            No indicators were detected. This does not mean the message is safe.
          </p>
        ) : (
          <div className="mt-2 space-y-4">
            {Object.entries(groupedIndicators).map(([groupName, indicators]) => (
              <div key={groupName}>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">
                  {groupName}
                </h3>
                <div className="grid gap-3 sm:grid-cols-2">
                  {indicators.map((indicator) => (
                    <IndicatorCard key={indicator.id} indicator={indicator} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slate-800">Evidence</h2>
        <div className="mt-2">
          <EvidenceHighlight message={message} evidence={assessment.evidence} />
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slate-800">Links (defanged)</h2>
        <div className="mt-2">
          <UrlList urls={assessment.urls} />
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slate-800">Likely attack sequence</h2>
        <div className="mt-2">
          <AttackSequence steps={assessment.attack_sequence} />
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slate-800">Guidance</h2>
        <div className="mt-2 space-y-3">
          {assessment.guidance.length === 0 ? (
            <p className="text-sm text-slate-500">No matching internal guidance was found.</p>
          ) : (
            assessment.guidance.map((item) => <GuidanceCard key={item.id} guidance={item} />)
          )}
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slate-800">Next steps</h2>
        <ul className="mt-2 list-inside list-disc text-sm text-slate-700">
          {assessment.next_steps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ul>
      </section>

      <ActivityLog entries={assessment.activity} />

      <button
        type="button"
        onClick={() => navigate("/review")}
        className="rounded bg-slate-900 px-5 py-2.5 text-sm font-medium text-white"
      >
        Review and save
      </button>
    </div>
  );
}
