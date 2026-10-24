/** Shown when the agent needs one clarifying question instead of guessing. */

export function ClarificationPrompt({
  question,
  onEditMessage,
}: {
  question: string;
  onEditMessage: () => void;
}) {
  return (
    <section className="rounded-md border border-amber-300 bg-amber-50 p-4">
      <h2 className="text-sm font-semibold text-amber-900">One question before we assess</h2>
      <p className="mt-2 text-sm text-amber-900">{question}</p>
      <button
        type="button"
        onClick={onEditMessage}
        className="mt-3 rounded border border-amber-400 bg-white px-3 py-1.5 text-sm text-amber-900"
      >
        Edit the message
      </button>
    </section>
  );
}
