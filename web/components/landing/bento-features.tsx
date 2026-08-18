import { Reveal } from "./reveal";
import { cn } from "@/lib/utils";

type Confidence = "High" | "Medium" | "Low";

const CONSTRAINTS: { n: string; name: string; source: string; confidence: Confidence }[] = [
  { n: "01", name: "Railway crossing", source: "OSM", confidence: "High" },
  { n: "02", name: "Metro interface", source: "OSM", confidence: "High" },
  { n: "03", name: "Existing elevated structure", source: "OSM", confidence: "High" },
  { n: "04", name: "Major arterial crossing", source: "OSM", confidence: "High" },
  { n: "05", name: "Restricted / military area", source: "OSM", confidence: "Low" },
  { n: "06", name: "Entry–exit feasibility", source: "Derived", confidence: "Medium" },
  { n: "07", name: "Curve severity", source: "Geometry", confidence: "High" },
  { n: "08", name: "EHT line crossing", source: "OSM", confidence: "Low" },
  { n: "09", name: "Dam / check structure", source: "OSM + visual", confidence: "Medium" },
  { n: "10", name: "Land availability", source: "Open Buildings", confidence: "High" },
  { n: "11", name: "Habitation proximity", source: "Open Buildings + WorldPop", confidence: "High" },
  { n: "12", name: "Hydraulic sensitivity", source: "DEM", confidence: "Low" },
];

const confidenceStyle: Record<Confidence, string> = {
  High: "bg-channel/15 text-channel-dim dark:text-channel",
  Medium: "bg-fog/15 text-fog",
  Low: "bg-flag/15 text-flag",
};

export function BentoFeatures() {
  return (
    <section id="method" className="mx-auto w-full max-w-6xl px-6 py-28 sm:px-10">
      <Reveal className="max-w-2xl">
        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-channel-dim dark:text-channel">
          The method
        </p>
        <h2 className="mt-3 font-display text-3xl font-medium tracking-tight text-foreground sm:text-4xl">
          Twelve constraint categories, scored 0–3 per 100 m segment.
        </h2>
        <p className="mt-4 text-fog">
          Each category is a computable proxy against public geometry — never a design
          judgment. Confidence is scored alongside every category, not buried in a footnote:
          where the underlying open data is thin, the map says so.
        </p>
      </Reveal>

      <div className="mt-12 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {CONSTRAINTS.map((c, i) => (
          <Reveal key={c.n} delay={Math.min(i * 0.04, 0.3)}>
            <div className="group h-full rounded-2xl border border-line bg-surface p-6 transition-colors hover:border-channel/40">
              <div className="flex items-start justify-between gap-3">
                <span className="font-mono text-xs text-fog">{c.n}</span>
                <span
                  className={cn(
                    "rounded-full px-2.5 py-0.5 font-mono text-[10px] uppercase tracking-wide",
                    confidenceStyle[c.confidence],
                  )}
                >
                  {c.confidence}
                </span>
              </div>
              <h3 className="mt-4 text-base font-medium text-foreground">{c.name}</h3>
              <p className="mt-1 text-xs text-fog">{c.source}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
