/** Editable reply draft the analyst reviews before saving. */

export function GuidanceDraftEditor({
  value,
  onChange,
}: {
  value: string;
  onChange: (next: string) => void;
}) {
  return (
    <div>
      <label
        htmlFor="guidance-draft"
        className="block text-sm font-medium text-slate-700"
      >
        Reply draft (edit before sending)
      </label>
      <textarea
        id="guidance-draft"
        className="mt-1 h-40 w-full rounded-md border border-slate-300 p-3 font-mono text-sm"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
      <p className="mt-1 text-xs text-slate-400">
        Editing the draft sets draft_edited=true when you save.
      </p>
    </div>
  );
}
