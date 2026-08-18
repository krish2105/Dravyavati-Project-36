const ROWS: { label: string; swatch: string }[] = [
  { label: "Low — bottom 70% of segments", swatch: "bg-channel" },
  { label: "Medium — 70th–90th percentile", swatch: "bg-[#c98f4a]" },
  { label: "High — top 10% of segments", swatch: "bg-flag" },
];

export function LegendPanel() {
  return (
    <div className="p-4 text-sm">
      <h2 className="font-display text-sm font-medium text-foreground">Composite severity</h2>
      <ul className="mt-3 space-y-2">
        {ROWS.map((r) => (
          <li key={r.label} className="flex items-center gap-2 text-xs text-fog">
            <span className={`h-3 w-3 shrink-0 rounded-sm ${r.swatch}`} aria-hidden />
            {r.label}
          </li>
        ))}
      </ul>
      <div className="mt-3 flex items-center gap-2 text-xs text-fog">
        <span className="h-3 w-3 shrink-0 rounded-sm border-2 border-flag/60" aria-hidden />
        Robust hotspot (stable under ±35% reweighting)
      </div>
      <p className="mt-4 border-t border-line pt-3 text-[11px] leading-relaxed text-fog">
        Equal-weight composite across all 12 constraints. Click a segment on the map for its
        full breakdown. See{" "}
        <code className="rounded bg-surface-muted px-1 py-0.5 font-mono text-[0.9em]">
          data/SOURCES.md
        </code>{" "}
        for provenance and confidence per layer.
      </p>
    </div>
  );
}
