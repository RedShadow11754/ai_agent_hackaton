/** "/incidents" - list of saved incidents (newest first). */

import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { listIncidents } from "../api/incidents";
import { ErrorBanner } from "../components/ErrorBanner";

export function IncidentsPage() {
  const incidents = useQuery({ queryKey: ["incidents"], queryFn: listIncidents });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-lg font-semibold text-slate-900">Incidents</h1>
        <p className="mt-1 text-sm text-slate-600">
          Saved investigations, newest first. Saving always required analyst approval.
        </p>
      </header>

      {incidents.isError ? (
        <ErrorBanner error={incidents.error} onRetry={() => void incidents.refetch()} />
      ) : null}

      {incidents.isLoading ? <p className="text-sm text-slate-500">Loading...</p> : null}

      {incidents.data && incidents.data.length === 0 ? (
        <p className="text-sm text-slate-500">No incidents have been saved yet.</p>
      ) : null}

      {incidents.data && incidents.data.length > 0 ? (
        <ul className="divide-y divide-slate-200 rounded-md border border-slate-200 bg-white">
          {incidents.data.map((incident) => (
            <li key={incident.id} className="px-4 py-3">
              <Link to={`/incidents/${incident.id}`} className="text-sm font-medium text-slate-900 underline">
                {incident.id}
              </Link>
              <p className="text-xs text-slate-500">
                {incident.risk_band} (score {incident.risk_score}) - {incident.status}
              </p>
              <p className="mt-1 truncate text-sm text-slate-600">{incident.message_preview}</p>
            </li>
          ))}
        </ul>
      ) : null}

      {/* TODO: add pagination, a status filter, and a risk-band filter. */}
    </div>
  );
}
