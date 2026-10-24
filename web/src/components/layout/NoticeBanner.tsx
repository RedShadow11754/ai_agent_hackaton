/** Informational banner used for the safety/scope notice at the top of the app. */

import type { ReactNode } from "react";

export function NoticeBanner({ children }: { children: ReactNode }) {
  return (
    <div
      role="note"
      className="rounded-md border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900"
    >
      {children}
    </div>
  );
}
