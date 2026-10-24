/**
 * "New Investigation" home page (Step 1 of 4) for Message Investigator.
 * Text-only suspicious-message triage tool for an IT helpdesk analyst.
 */

import { useState, useCallback } from "react";
import { Shield, Loader2, AlertCircle, ChevronDown, ChevronUp } from "lucide-react";

/** Demo messages — all fictitious, reserved domains only (hard rule 7). */
const DEMO_MESSAGES: Record<string, { sender: string; body: string }> = {
  "Password request": {
    sender: "IT Support <it-support@secure-login.test>",
    body: `Dear user,

Your account password expires today. You must reset it immediately or lose access to email and payroll.

Reset now: hxxps://secure-login[.]test/portal/reset?user=analyst

Thank you,
IT Support`,
  },
  "IP link + urgency": {
    sender: "Payroll <payroll@intranet.example>",
    body: `Your payslip is ready.

Download it here: hxxp://192.0.2.45/payslip.pdf

Reply urgently if you cannot access it.`,
  },
  "Lookalike domain": {
    sender: "Accounts <billing@payroll-update.example>",
    body: `Hi,

Please note we have changed our bank details for the open invoice.
Kindly pay the attached invoice today and confirm the transfer.
This is confidential - do not discuss it with anyone else.

Thanks,
Accounts Team`,
  },
  "Legitimate message": {
    sender: "HR Team <hr@hr-portal.example>",
    body: `Reminder: the office will be closed on the public holiday next Monday.

No action is needed. Details are on the HR portal as usual.`,
  },
  "Too short": {
    sender: "Unknown",
    body: "hi, is this you?",
  },
};

const MAX_CHARS = 3000;

export default function InvestigatePage() {
  // Form state
  const [message, setMessage] = useState("");
  const [sender, setSender] = useState("");
  const [showOptional, setShowOptional] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Handle demo chip click
  const fillDemo = useCallback((key: string) => {
    const demo = DEMO_MESSAGES[key];
    if (demo) {
      setSender(demo.sender);
      setMessage(demo.body);
      setError(null);
    }
  }, []);

  // Textarea change handler with 3000-char limit
  const handleMessageChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    if (val.length <= MAX_CHARS) {
      setMessage(val);
      if (error) setError(null);
    }
  };

  // Simulate analyze action
  const handleAnalyze = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) {
      setError("Message text is required.");
      return;
    }
    if (message.length > MAX_CHARS) {
      setError(`Message exceeds ${MAX_CHARS} characters.`);
      return;
    }
    setLoading(true);
    setError(null);
    // In a real app, this would call the API and navigate to /results
    setTimeout(() => {
      setLoading(false);
      console.log("Analyze:", { message, sender });
      // navigate("/results");
    }, 800);
  };

  // Character count for display
  const charCount = message.length;
  const isOverLimit = charCount > MAX_CHARS;
  const isNearLimit = charCount > MAX_CHARS * 0.9;

  return (
    <div className="min-h-screen bg-[var(--page-bg)] font-sans text-[var(--text-body)]">
      {/* CSS variables injected via global styles or Tailwind config */}
      <style jsx global>{`
        :root {
          --page-bg: #F8FAFC;
          --card-bg: #FFFFFF;
          --card-border: #E2E8F0;
          --accent: #4F46E5;
          --accent-hover: #4338CE;
          --accent-active: #3730A3;
          --accent-tint: #EEF2FF;
          --text-heading: #0F172A;
          --text-body: #475569;
          --text-muted: #94A3B8;
          --inactive-bg: #E2E8F0;
          --info-bg: #EFF6FF;
          --info-border: #BFDBFE;
          --info-text: #1E3A8A;
          --info-icon: #2563EB;
          --demo-label: #15803D;
          --status-detected-bg: #FEF2F2;
          --status-detected-text: #DC2626;
          --status-not-bg: #F8FAFC;
          --status-not-text: #94A3B8;
          --evidence-bg: #FEF9C3;
          --evidence-border: #EAB308;
          --textarea-border: #CBD5E1;
          --disabled-bg: #C7D2FE;
          --error-border: #DC2626;
          --error-bg: #FEF2F2;
          --error-text: #DC2626;
        }
      `}</style>

      {/* 1. Top bar */}
      <header className="border-b border-[var(--card-border)] bg-white sticky top-0 z-10">
        <div className="mx-auto max-w-4xl px-4 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-[8px] bg-[var(--accent)] flex items-center justify-center">
              <span className="text-white font-bold text-lg">M</span>
            </div>
            <span className="text-lg font-semibold text-[var(--text-heading)]">
              Message Investigator
            </span>
          </div>

          <nav className="flex items-center gap-1 ml-auto" role="tablist" aria-label="Main navigation">
            <button
              role="tab"
              aria-selected="true"
              className="px-3 py-1.5 rounded-lg text-sm font-medium bg-[var(--accent-tint)] text-[var(--accent)] transition-colors duration-150"
            >
              New
            </button>
            <button
              role="tab"
              aria-selected="false"
              className="px-3 py-1.5 rounded-lg text-sm font-medium text-[var(--text-muted)] hover:text-[var(--text-body)] hover:bg-[var(--card-border)] transition-colors duration-150"
            >
              Saved Incidents
            </button>
          </nav>

          <div className="flex items-center gap-3 text-xs text-[var(--text-muted)] ml-4">
            <span className="flex items-center gap-1">
              Text-only analysis
            </span>
            <span className="w-px h-4 bg-[var(--card-border)]" aria-hidden="true" />
            <span className="flex items-center gap-1">
              Links are never opened
            </span>
            <span className="w-px h-4 bg-[var(--card-border)]" aria-hidden="true" />
            <span className="text-[var(--demo-label)] font-medium">
              Demo, fictitious data only
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-8">
        {/* 2. Stepper */}
        <nav className="mb-6 flex gap-2 overflow-x-auto pb-2" aria-label="Investigation steps">
          {[
            { label: "Investigate", step: 1, active: true },
            { label: "Results", step: 2, active: false },
            { label: "Review", step: 3, active: false },
            { label: "Saved", step: 4, active: false },
          ].map(({ label, step, active }) => (
            <button
              key={label}
              type="button"
              disabled
              className={`flex flex-col items-center gap-1 px-4 py-3 rounded-full transition-all duration-150 whitespace-nowrap ${
                active
                  ? "bg-[var(--accent)] text-white shadow-sm"
                  : "bg-[var(--inactive-bg)] text-[var(--text-body)]"
              }`}
            >
              <span className="flex items-center gap-1">
                <span className="text-sm font-semibold">{step}</span>
                <span className="font-medium">{label}</span>
              </span>
            </button>
          ))}
        </nav>

        {/* 3. Centered main card */}
        <div className="mx-auto max-w-2xl">
          <article className="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[16px] shadow-[0_1px_3px_rgba(15,23,42,0.06)] p-6 md:p-8">
            {/* Eyebrow + Title + Description */}
            <header className="mb-6">
              <p className="text-[11px] uppercase tracking-[0.08em] font-semibold text-[var(--text-muted)] mb-2">
                TEXT-ONLY TRIAGE · STEP 01
              </p>
              <h1 className="text-[28px] font-bold text-[var(--text-heading)] mb-2">
                New investigation
              </h1>
              <p className="text-[14px] text-[var(--text-body)]">
                Paste a suspicious message to analyze indicators, risk level, and suggested guidance.
              </p>
            </header>

            {/* Demo chips */}
            <section className="mb-6">
              <label className="block text-xs font-medium text-[var(--text-muted)] mb-2">
                Try a demo message
              </label>
              <div className="flex flex-wrap gap-2" role="group" aria-label="Demo messages">
                {Object.keys(DEMO_MESSAGES).map((key) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => fillDemo(key)}
                    className="px-3 py-1.5 text-[13px] font-medium rounded-[8px] bg-white border border-[var(--card-border)] hover:border-[var(--accent)] hover:bg-[var(--accent-tint)] transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:ring-offset-2"
                  >
                    {key}
                  </button>
                ))}
              </div>
            </section>

            {/* Suspicious message textarea */}
            <section className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <label htmlFor="message" className="block text-sm font-medium text-[var(--text-heading)]">
                  Suspicious message
                </label>
                <span className="px-2 py-0.5 text-[11px] font-medium text-[var(--text-muted)] bg-[var(--inactive-bg)] rounded-full">
                  Required
                </span>
              </div>

              <div className="relative">
                <textarea
                  id="message"
                  rows={5}
                  className="w-full min-h-[120px] resize-y font-mono text-[14px] text-[var(--text-heading)] bg-white border rounded-lg p-4 transition-all duration-150
                    border-[var(--textarea-border)]
                    placeholder:[var(--text-muted)]
                    focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:ring-opacity-30 focus:border-transparent
                    disabled:opacity-50
                    ${error ? "border-[var(--error-border)] bg-[var(--error-bg)]" : ""}
                    ${isOverLimit ? "border-[var(--error-border)]" : ""}"
                  placeholder="Paste the full message here, including any links as plain text…"
                  value={message}
                  onChange={handleMessageChange}
                  maxLength={MAX_CHARS}
                  disabled={loading}
                  aria-describedby={error ? "message-error" : charCount > 0 ? "message-count" : undefined}
                  aria-invalid={!!error}
                />
                {/* Character counter */}
                <div className="absolute bottom-2 right-2 flex items-center gap-1 pointer-events-none">
                  <span
                    id="message-count"
                    className={`text-[11px] font-mono tabular-nums transition-colors duration-150 ${
                      isOverLimit
                        ? "text-[var(--error-text)]"
                        : isNearLimit
                        ? "text-amber-600"
                        : "text-[var(--text-muted)]"
                    }`}
                    aria-live="polite"
                  >
                    {charCount} / {MAX_CHARS}
                  </span>
                </div>
              </div>

              {error && (
                <p id="message-error" className="mt-2 text-[13px] text-[var(--error-text)] flex items-center gap-1" role="alert">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
                  {error}
                </p>
              )}
            </section>

            {/* Optional details expand */}
            <section className="mb-6">
              <button
                type="button"
                onClick={() => setShowOptional((v) => !v)}
                className="flex items-center gap-1 text-sm font-medium text-[var(--accent)] hover:text-[var(--accent-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:ring-offset-2 rounded"
                aria-expanded={showOptional}
              >
                <span>+ Add optional details</span>
                {showOptional ? (
                  <ChevronUp className="w-4 h-4" aria-hidden="true" />
                ) : (
                  <ChevronDown className="w-4 h-4" aria-hidden="true" />
                )}
              </button>

              {showOptional && (
                <div className="mt-4 space-y-4 animate-in slide-in-from-top-2 duration-150">
                  <div>
                    <label htmlFor="sender" className="block text-sm font-medium text-[var(--text-heading)] mb-1">
                      Sender (optional)
                    </label>
                    <input
                      id="sender"
                      type="text"
                      className="w-full px-3 py-2 text-[14px] text-[var(--text-heading)] bg-white border-[var(--textarea-border)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:ring-opacity-30 focus:border-transparent transition-all duration-150"
                      placeholder="e.g., IT Support <it-support@secure-login.test>"
                      value={sender}
                      onChange={(e) => setSender(e.target.value)}
                      disabled={loading}
                    />
                  </div>
                </div>
              )}
            </section>

            {/* Info banner */}
            <section className="mb-6">
              <div
                className="flex items-start gap-3 p-4 bg-[var(--info-bg)] border border-[var(--info-border)] rounded-lg"
                role="note"
              >
                <Shield
                  className="w-5 h-5 flex-shrink-0 text-[var(--info-icon)] mt-0.5"
                  aria-hidden="true"
                />
                <div className="text-sm text-[var(--info-text)] leading-relaxed">
                  <span className="font-medium">Links are extracted as text and are never opened.</span>{" "}
                  Analysis is text-only.
                </div>
              </div>
            </section>

            {/* Footer row: helper text + Analyze button */}
            <footer className="pt-4 border-t border-[var(--card-border)] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <p className="text-[12px] text-[var(--text-muted)]">
                Only message text is checked. No URLs are fetched or opened.
              </p>
              <button
                type="submit"
                form="investigate-form"
                disabled={!message.trim() || charCount > MAX_CHARS || loading}
                className="w-full sm:w-auto px-6 py-2.5 rounded-[10px] text-[14px] font-semibold text-white bg-[var(--accent)] hover:bg-[var(--accent-hover)] active:bg-[var(--accent-active)] disabled:bg-[var(--disabled-bg)] disabled:cursor-not-allowed disabled:hover:bg-[var(--disabled-bg)] transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:ring-offset-2 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                    <span>Analyzing…</span>
                  </>
                ) : (
                  <>
                    <span>Analyze Message</span>
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                      <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </>
                )}
              </button>
            </footer>
          </article>
        </div>
      </main>

      {/* 4. Page footer */}
      <footer className="border-t border-[var(--card-border)] bg-white mt-8">
        <div className="mx-auto max-w-4xl px-4 py-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-[12px] text-[var(--text-muted)]">
          <span>Message Investigator</span>
          <span>Fictitious demo data · Not a security verdict</span>
        </div>
      </footer>

      {/* Hidden form for Enter-to-submit */}
      <form id="investigate-form" onSubmit={handleAnalyze} className="hidden" />
    </div>
  );
}