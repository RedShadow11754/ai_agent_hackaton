/** Step indicator for the investigate -> results -> review -> save flow. */

import { useLocation } from "react-router-dom";

const STEPS: { label: string; path: string }[] = [
  { label: "1. Paste", path: "/" },
  { label: "2. Results", path: "/results" },
  { label: "3. Review", path: "/review" },
  { label: "4. Incidents", path: "/incidents" },
];

export function Stepper() {
  const { pathname } = useLocation();
  const currentIndex = Math.max(
    0,
    STEPS.findIndex((step) => step.path !== "/" && pathname.startsWith(step.path)),
  );

  return (
    <ol className="flex flex-wrap items-center gap-2 text-xs" aria-label="Progress">
      {STEPS.map((step, index) => {
        const isCurrent = index === currentIndex;
        return (
          <li
            key={step.path}
            className={[
              "rounded-full border px-3 py-1",
              isCurrent
                ? "border-slate-900 bg-slate-900 text-white"
                : "border-slate-200 bg-white text-slate-500",
            ].join(" ")}
            aria-current={isCurrent ? "step" : undefined}
          >
            {step.label}
          </li>
        );
      })}
    </ol>
  );
}
