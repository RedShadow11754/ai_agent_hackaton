/** Top-level layout: header, step indicator, safety notice, and page content. */

import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

import { NoticeBanner } from "./NoticeBanner";
import { Stepper } from "./Stepper";

/** Primary navigation entries. */
const NAV_ITEMS: { to: string; label: string }[] = [
  { to: "/", label: "Investigate" },
  { to: "/results", label: "Results" },
  { to: "/review", label: "Review & save" },
  { to: "/incidents", label: "Incidents" },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-4 py-3">
          <div>
            <p className="text-sm font-semibold text-slate-900">
              Suspicious Message Investigation
            </p>
            <p className="text-xs text-slate-500">IT helpdesk analyst console</p>
          </div>
          <nav className="flex flex-wrap gap-1" aria-label="Main">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  [
                    "rounded px-3 py-1.5 text-sm",
                    isActive
                      ? "bg-slate-900 text-white"
                      : "text-slate-600 hover:bg-slate-100",
                  ].join(" ")
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-4 py-6">
        <Stepper />
        <NoticeBanner>
          Analysis is text-only. The agent never opens links, and nothing is saved until you
          approve it.
        </NoticeBanner>
        {children}
      </main>

      <footer className="mx-auto max-w-5xl px-4 pb-8 pt-2 text-xs text-slate-400">
        Demo data is fictitious. Messages are never labelled &ldquo;safe&rdquo; - the lowest
        result is Low / Inconclusive.
      </footer>
    </div>
  );
}
