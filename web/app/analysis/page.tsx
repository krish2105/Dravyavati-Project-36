"use client";

import { SiteHeader } from "@/components/site-header";
import { motion } from "motion/react";
import { ChainageProfile } from "@/components/charts/chainage-profile";
import { CooccurrenceMatrix } from "@/components/charts/cooccurrence-matrix";
import { ImportanceTornado } from "@/components/charts/importance-tornado";
import { HotspotTable } from "@/components/atlas/hotspot-table";
import { WeightStudio } from "@/components/charts/weight-studio";
import { useJson, type Analytics, type FeatureImportance } from "@/lib/analytics";

const ease = [0.16, 1, 0.3, 1] as const;

function Panel({
  title,
  subtitle,
  children,
  delay = 0,
  className = "",
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  // Deliberately never animates opacity from 0. If the animation frame loop
  // never runs — a background tab, prefers-reduced-motion, a low-power device
  // — anything starting at opacity 0 stays invisible forever. On a document
  // like this the content must always be readable; motion is polish only, so
  // the entrance is a small translate on already-visible content.
  return (
    <motion.section
      initial={{ y: 14 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease, delay }}
      className={`rounded-2xl border border-line bg-surface p-4 sm:p-5 ${className}`}
    >
      <h2 className="font-display text-base font-medium text-foreground">{title}</h2>
      {subtitle && <p className="mt-0.5 mb-4 text-xs leading-relaxed text-fog">{subtitle}</p>}
      {!subtitle && <div className="mb-4" />}
      {children}
    </motion.section>
  );
}

export default function AnalysisPage() {
  const analytics = useJson<Analytics>("/data/analytics.json");
  const importance = useJson<FeatureImportance>("/data/feature_importance.json");

  return (
    <div className="min-h-screen w-full">
      <SiteHeader badge="Analysis" />

      <main className="mx-auto w-full max-w-7xl space-y-4 p-3 sm:p-4">
        {!analytics && (
          <p className="py-20 text-center font-mono text-xs text-fog">Loading analysis…</p>
        )}

        {analytics && (
          <>
            <Panel
              title="Constraint profile along the corridor"
              subtitle="Composite score per 100 m chainage, with the Monte Carlo 90% interval behind it. Shaded columns mark medium and high severity; amber dots are robust hotspots."
            >
              <ChainageProfile profile={analytics.profile} />
            </Panel>

            <div className="grid gap-4 lg:grid-cols-2">
              <Panel
                title="Robust hotspot corridors"
                subtitle={`${analytics.hotspot_corridors.length} contiguous stretches survive a ±35% reweighting of every constraint.`}
                delay={0.05}
              >
                <HotspotTable corridors={analytics.hotspot_corridors} />
              </Panel>

              <Panel
                title="What drives the ranking"
                subtitle="Modelled, not measured — a surrogate explaining this atlas's own composite."
                delay={0.1}
              >
                {importance ? (
                  <ImportanceTornado data={importance} />
                ) : (
                  <p className="text-sm text-fog">Feature importance unavailable.</p>
                )}
              </Panel>
            </div>

            <Panel
              title="Reweighting studio"
              subtitle="The pack requires weights to be configurable rather than hardcoded. Move any weight and the composite, banding and ranking recompute live in the browser."
              delay={0.12}
            >
              <WeightStudio />
            </Panel>

            <Panel
              title="Constraint co-occurrence"
              subtitle="Where constraints stack. Compound problems are invisible in any single-constraint view."
              delay={0.15}
            >
              <CooccurrenceMatrix
                labels={analytics.cooccurrence.labels}
                matrix={analytics.cooccurrence.matrix}
              />
            </Panel>

            <Panel title="Method and limits" delay={0.2}>
              <dl className="grid gap-x-8 gap-y-2 text-xs sm:grid-cols-2">
                {[
                  ["Segments analysed", `${analytics.corridor.segments} × 100 m = ${analytics.corridor.length_km} km`],
                  ["Constraint categories", String(analytics.corridor.constraint_count)],
                  [
                    "Mean 90% CI width",
                    analytics.uncertainty.mean_ci_width !== null
                      ? analytics.uncertainty.mean_ci_width.toFixed(3)
                      : "—",
                  ],
                  ["Anomalous combinations", `${analytics.anomalies} segments (Isolation Forest)`],
                  [
                    "IRC:86-2018 curve check",
                    `${analytics.irc86.segments_below} segments below ${analytics.irc86.min_radius_m} m minimum radius`,
                  ],
                  ["Cross-drainage candidates", `${analytics.crossings.cross_drainage} distinct locations`],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-4 border-b border-line/60 py-1.5">
                    <dt className="text-fog">{k}</dt>
                    <dd className="text-right font-mono tabular-nums text-foreground">{v}</dd>
                  </div>
                ))}
              </dl>
              <p className="mt-4 text-[11px] leading-relaxed text-fog">
                Screening-grade, not design-grade. Every layer traces to a public URL recorded in
                data/SOURCES.md with an access date. Power-line and military layers are low confidence
                because OpenStreetMap coverage for them in Jaipur is incomplete; the built-up growth layer is
                low confidence because NDBI is a proxy index, not a land-cover classification. All findings
                require verification against field survey.
              </p>
            </Panel>
          </>
        )}
      </main>
    </div>
  );
}
