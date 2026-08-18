"use client";

import { useMemo, useState } from "react";
import { SiteHeader } from "@/components/site-header";
import { useJson, type Analytics, type ProfilePoint, BAND_COLOR } from "@/lib/analytics";

/**
 * Segment inspector. Deep-linkable via ?ch=27900 so a specific chainage can
 * be sent as a link rather than described in prose.
 */

function ScoreBar({ label, value, max = 3 }: { label: string; value: number; max?: number }) {
  const pct = Math.max((value / max) * 100, value > 0 ? 4 : 0);
  return (
    <div className="grid grid-cols-[minmax(7rem,11rem)_1fr_2rem] items-center gap-2 sm:gap-3">
      <span className="truncate text-xs text-fog" title={label}>
        {label}
      </span>
      <span className="relative block h-2.5 rounded-sm bg-surface-muted">
        <span
          className="absolute inset-y-0 left-0 rounded-sm"
          style={{
            width: `${pct}%`,
            background: value >= 3 ? "var(--flag)" : value >= 2 ? "#c98f4a" : "var(--channel)",
          }}
        />
      </span>
      <span className="text-right font-mono text-[11px] tabular-nums text-foreground">
        {value.toFixed(value % 1 === 0 ? 0 : 1)}
      </span>
    </div>
  );
}

export default function SegmentsPage() {
  const analytics = useJson<Analytics>("/data/analytics.json");
  const [selected, setSelected] = useState<number | null>(null);

  const corridors = analytics?.hotspot_corridors ?? [];
  const active = useMemo(() => {
    if (!analytics) return null;
    const id = selected ?? corridors[0]?.id;
    return corridors.find((c) => c.id === id) ?? null;
  }, [analytics, selected, corridors]);

  const segmentsInActive: ProfilePoint[] = useMemo(() => {
    if (!analytics || !active) return [];
    return analytics.profile.filter(
      (p) => p.chainage_m >= active.start_m && p.chainage_m < active.end_m,
    );
  }, [analytics, active]);

  return (
    <>
      <SiteHeader badge="Segments" />
      <main className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 sm:py-10">
        <h1 className="font-display text-2xl font-medium tracking-tight text-foreground sm:text-3xl">
          Segment inspector
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-fog">
          The robust hotspot corridors, opened up. Each is a contiguous run of 100 m segments whose
          severity band held across every reweighting tested — pick one to see the chainages inside it
          and what is driving them.
        </p>

        {!analytics && <p className="py-16 text-center font-mono text-xs text-fog">Loading…</p>}

        {analytics && (
          <div className="mt-6 grid gap-4 lg:grid-cols-[18rem_1fr]">
            <nav className="flex gap-2 overflow-x-auto lg:flex-col lg:overflow-visible [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
              {corridors.map((c) => {
                const isActive = active?.id === c.id;
                return (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => setSelected(c.id)}
                    className={`shrink-0 rounded-xl border p-3 text-left transition-colors lg:w-full ${
                      isActive
                        ? "border-flag/60 bg-flag/10"
                        : "border-line bg-surface hover:border-channel/50"
                    }`}
                  >
                    <div className="whitespace-nowrap font-mono text-xs tabular-nums text-foreground">
                      {(c.start_m / 1000).toFixed(1)} – {(c.end_m / 1000).toFixed(1)} km
                    </div>
                    <div className="mt-0.5 whitespace-nowrap text-[11px] text-fog">
                      {c.segments} segments · composite {c.mean_composite.toFixed(2)}
                    </div>
                  </button>
                );
              })}
            </nav>

            {active && (
              <section className="rounded-2xl border border-line bg-surface p-4 sm:p-5">
                <header className="flex flex-wrap items-baseline justify-between gap-2">
                  <h2 className="font-display text-lg font-medium text-foreground">
                    Chainage {(active.start_m / 1000).toFixed(1)} – {(active.end_m / 1000).toFixed(1)} km
                  </h2>
                  <span className="font-mono text-xs text-fog">
                    {((active.end_m - active.start_m) / 1000).toFixed(1)} km · {active.segments} segments
                  </span>
                </header>

                <div className="mt-4">
                  <h3 className="mb-2 font-mono text-[10px] uppercase tracking-wide text-fog">
                    Leading constraints (mean across the corridor)
                  </h3>
                  <div className="space-y-1.5">
                    {active.top_drivers.map((d) => (
                      <ScoreBar key={d.label} label={d.label} value={d.mean_score} />
                    ))}
                  </div>
                </div>

                <div className="mt-5">
                  <h3 className="mb-2 font-mono text-[10px] uppercase tracking-wide text-fog">
                    Segments in this corridor
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[26rem] border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-line text-left font-mono text-[10px] uppercase tracking-wide text-fog">
                          <th className="py-1.5 pr-3 font-normal">Chainage</th>
                          <th className="py-1.5 pr-3 font-normal">Composite</th>
                          <th className="py-1.5 pr-3 font-normal">90% interval</th>
                          <th className="py-1.5 font-normal">Flags</th>
                        </tr>
                      </thead>
                      <tbody>
                        {segmentsInActive.map((p) => (
                          <tr key={p.chainage_m} className="border-b border-line/60">
                            <td className="py-1.5 pr-3 font-mono tabular-nums text-foreground">
                              {p.chainage_m} m
                            </td>
                            <td className="py-1.5 pr-3">
                              <span className="inline-flex items-center gap-1.5">
                                <span
                                  className="h-2 w-2 rounded-full"
                                  style={{ background: BAND_COLOR[p.band] }}
                                  aria-hidden
                                />
                                <span className="font-mono tabular-nums text-foreground">
                                  {p.composite.toFixed(2)}
                                </span>
                              </span>
                            </td>
                            <td className="py-1.5 pr-3 font-mono tabular-nums text-fog">
                              {p.p05.toFixed(2)} – {p.p95.toFixed(2)}
                            </td>
                            <td className="py-1.5 text-fog">
                              {[p.robust && "robust", p.anomaly && "anomalous"]
                                .filter(Boolean)
                                .join(" · ") || "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <p className="mt-4 border-t border-line pt-3 text-[11px] leading-relaxed text-fog">
                  The 90% interval comes from 5,000 Monte Carlo runs perturbing both the constraint weights
                  and the scores themselves, with each layer moving in proportion to its own confidence
                  tag. Where an interval is wide, the underlying sources are weak — not the chainage.
                </p>
              </section>
            )}
          </div>
        )}
      </main>
    </>
  );
}
