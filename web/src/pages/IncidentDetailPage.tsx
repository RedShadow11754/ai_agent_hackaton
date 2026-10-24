/** "/incidents/:id" - one saved incident with its full assessment and audit log. */

import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { getIncident, getIncidentActivity } from "../api/incidents";
import { ActivityLog } from "../components/ActivityLog";
import { AttackSequence } from "../components/AttackSequence";
import { ErrorBanner } from "../components/ErrorBanner";
import { EvidenceHighlight } from "../components/EvidenceHighlight";
import { GuidanceCard } from "../components/GuidanceCard";
import { IndicatorCard } from "../components/IndicatorCard";
import { RiskBadge } from "../components/RiskBadge";
import { UrlList } from "../components/UrlList";

export function IncidentDetailPage() {
  const { id = "" } = useParams<{ id: string }>();

  const incident = useQuery({
    queryKey: ["incident", id],
    queryFn: () => getIncident(id),
    enabled: id.length > 0,
  });

  const activity = useQuery({
    queryKey: ["incident", id, "activity"],
    queryFn: () => getIncidentActivity(id),
    enabled: id.length > 0,
  });

  if (incident.isError) {
    return (
      <div className="space-y-4">
        <h1 className="text-lg font-semibold text-slate-900">Incident {id}</h1>
        <ErrorBanner error={incident.error} onRetry={() => void incident.refetch()} />
      </div>
    );
  }

  if (!incident.data) {
    return (
      <div className="space-y-4">
        <h1 className="text-lg font-semibold text-slate-900">Incident {id}</h1>
        <p className="text-sm text-slate-500">Loading incident...</p>
      </div>
    );
  }

  const { assessment } = incident.data;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">Incident {incident.data.id}</h1>
          <p className="text-xs text-slate-500">
            saved {incident.data.created_at} - {incident.data.status}
            {incident.data.reviewed_by ? ` - reviewed by ${incident.data.reviewed_by}` : ""}
          </p>
        </div>
        <RiskBadge band={assessment.risk.band} score={assessment.risk.score} />
      </header>

      <section>
        <h2 className="text-sm font-semibold text-slate-800">Original message</h2>
        <pre className="message-text mt-2 max-h-64 overflow-auto rounded-md border border-slate-200 bg-white p-3 text-slate-800">
          {incident.data.message}
        </pre>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slate-800">Indicators</h2>
        <div className="mt-2 grid gap-3 sm:grid-cols-2">
          {assessment.indicators.map((indicator) => (
            <IndicatorCard key={indicator.id} indicator={indicator} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slate-800">Evidence</h2>
        <div className="mt-2">
          <EvidenceHighlight message={incident.data.message} evidence={assessment.evidence} />
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slate-800">Links (defanged)</h2>
        <div className="mt-2">
          <UrlList urls={assessment.urls} />
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slate-800">Attack sequence</h2>
        <div className="mt-2">
          <AttackSequence steps={assessment.attack_sequence} />
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slate-800">Guidance cited</h2>
        <div className="mt-2 space-y-3">
          {assessment.guidance.map((item) => (
            <GuidanceCard key={item.id} guidance={item} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-sm font-semibold text-slate-800">Draft sent to the user</h2>
        <pre className="message-text mt-2 rounded-md border border-slate-200 bg-white p-3 text-slate-800">
          {assessment.draft}
        </pre>
      </section>

      <ActivityLog entries={activity.data ?? assessment.activity} />

      {/* TODO: add a status control (e.g. mark as closed) with its own audit entry. */}
    </div>
  );
}
