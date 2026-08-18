import { Reveal } from "./reveal";

const SOURCES = [
  { label: "River channel, roads, rail, metro", source: "OpenStreetMap" },
  { label: "Building footprints", source: "Google Open Buildings v3" },
  { label: "Elevation", source: "Copernicus DEM GLO-30" },
  { label: "Population", source: "WorldPop / Meta HRSL" },
  { label: "Project endpoints & length", source: "Public press coverage" },
  { label: "DPR tender scope", source: "JDA tender portal (public ToR)" },
];

export function SourcesFooter() {
  return (
    <footer id="sources" className="mx-auto w-full max-w-6xl px-6 py-28 sm:px-10">
      <Reveal className="max-w-2xl">
        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-channel-dim dark:text-channel">
          Provenance
        </p>
        <h2 className="mt-3 font-display text-3xl font-medium tracking-tight text-foreground sm:text-4xl">
          Every layer traces to a public URL.
        </h2>
        <p className="mt-4 text-fog">
          Built entirely on open data, independently of JDA and any consultancy — no project
          data was used. The full ledger, with access dates, lives in{" "}
          <code className="rounded bg-surface-muted px-1.5 py-0.5 font-mono text-[0.85em]">
            data/SOURCES.md
          </code>
          .
        </p>
      </Reveal>

      <div className="mt-10 grid grid-cols-1 gap-px overflow-hidden rounded-2xl border border-line bg-line sm:grid-cols-2">
        {SOURCES.map((s) => (
          <div key={s.label} className="flex items-center justify-between gap-4 bg-background px-6 py-4">
            <span className="text-sm text-foreground">{s.label}</span>
            <span className="text-right font-mono text-xs text-fog">{s.source}</span>
          </div>
        ))}
      </div>

      <p className="mt-16 text-xs text-fog">
        Dravyavati Corridor Constraint Atlas — independent open-data analysis, not affiliated
        with any consultancy or government body.
      </p>
    </footer>
  );
}
