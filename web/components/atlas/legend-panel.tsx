const ROWS: { label: string; swatch: string; note: string }[] = [
  { label: "0 — no constraint", swatch: "bg-channel/20", note: "" },
  { label: "1 — minor", swatch: "bg-channel/50", note: "" },
  { label: "2 — moderate", swatch: "bg-flag/60", note: "" },
  { label: "3 — severe", swatch: "bg-flag", note: "" },
];

export function LegendPanel() {
  return (
    <div
      className="absolute left-4 top-28 z-10 hidden w-64 rounded-2xl border border-line bg-surface/90 p-4
                 text-sm shadow-[0_8px_24px_rgba(0,0,0,0.18)] backdrop-blur-md dark:shadow-[0_8px_24px_rgba(0,0,0,0.5)] sm:block"
    >
      <h2 className="font-display text-sm font-medium text-foreground">Composite severity</h2>
      <ul className="mt-3 space-y-2">
        {ROWS.map((r) => (
          <li key={r.label} className="flex items-center gap-2 text-xs text-fog">
            <span className={`h-3 w-3 rounded-sm ${r.swatch}`} aria-hidden />
            {r.label}
          </li>
        ))}
      </ul>
      <p className="mt-4 border-t border-line pt-3 text-[11px] leading-relaxed text-fog">
        River geometry: OpenStreetMap, fetched live. Scores: placeholder — Sessions 2–7 of the
        build plan have not run.
      </p>
    </div>
  );
}
