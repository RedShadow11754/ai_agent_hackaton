/**
 * Lists URLs as DEFANGED, non-clickable plain text.
 *
 * Hard rule 1: nothing here is ever fetched or linked. Hard rule 6: no anchors,
 * no dangerouslySetInnerHTML - just text an analyst can read without clicking.
 */

import type { UrlFinding } from "../types/api";

/** Convert a URL to a non-clickable display form, e.g. hxxps://host[.]tld. */
export function defang(url: string): string {
  return url
    .replace(/^https:/i, "hxxps:")
    .replace(/^http:/i, "hxxp:")
    .replace(/\./g, "[.]")
    .replace(/@/g, "[at]");
}

export function UrlList({ urls }: { urls: UrlFinding[] }) {
  if (urls.length === 0) {
    return <p className="text-sm text-slate-500">No URLs found in the message text.</p>;
  }

  return (
    <ul className="space-y-3">
      {urls.map((finding) => (
        <li key={finding.url} className="rounded-md border border-slate-200 bg-white p-3">
          <p className="message-text select-all text-slate-900">
            {finding.defanged || defang(finding.url)}
          </p>
          {finding.host ? (
            <p className="mt-1 text-xs text-slate-500">host: {finding.host}</p>
          ) : null}
          {finding.observations.length > 0 ? (
            <ul className="mt-2 list-inside list-disc text-xs text-slate-600">
              {finding.observations.map((observation) => (
                <li key={observation}>{observation}</li>
              ))}
            </ul>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
