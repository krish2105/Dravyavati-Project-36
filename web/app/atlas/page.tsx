"use client";

import { useState } from "react";
import { MapShell } from "@/components/atlas/map-shell";
import { LegendPanel } from "@/components/atlas/legend-panel";
import { SiteHeader } from "@/components/site-header";
import { useJson, type Analytics } from "@/lib/analytics";

/**
 * Command-centre layout. The map is the hero surface and owns all remaining
 * height; everything else is chrome around it.
 *
 * The previous version stacked a six-tile KPI grid, a sidebar, a floating
 * banner and a floating slider, which on a phone pushed the map almost
 * entirely off-screen and left the header title wrapping into the pills.
 * Here the rail collapses to a drawer under `lg`, the stat bar scrolls
 * horizontally rather than reflowing into a tall grid, and the map keeps a
 * usable minimum height at every width.
 */

function StatBar({ analytics }: { analytics: Analytics | null }) {
  const items = analytics
    ? [
        { label: "Reconstructed", value: `${analytics.corridor.length_km.toFixed(1)} km` },
        { label: "Segments", value: String(analytics.corridor.segments) },
        { label: "Constraints", value: String(analytics.corridor.constraint_count) },
        { label: "Robust hotspots", value: String(analytics.robust_hotspots), accent: true },
        { label: "High severity", value: String(analytics.severity.high ?? 0), accent: true },
        { label: "Rail crossings", value: String(analytics.crossings.railway) },
        { label: "Cross-drainage", value: String(analytics.crossings.cross_drainage) },
        { label: "Below IRC radius", value: String(analytics.irc86.segments_below) },
      ]
    : [];

  return (
    <div className="flex items-stretch gap-px overflow-x-auto border-b border-line bg-line [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      {items.length === 0 && <div className="bg-surface px-4 py-2 text-xs text-fog">Loading…</div>}
      {items.map((it) => (
        <div key={it.label} className="shrink-0 bg-surface px-4 py-2">
          <div
            className={`font-display text-lg leading-tight tabular-nums ${
              it.accent ? "text-flag" : "text-foreground"
            }`}
          >
            {it.value}
          </div>
          <div className="whitespace-nowrap text-[10px] uppercase tracking-wide text-fog">{it.label}</div>
        </div>
      ))}
    </div>
  );
}

export default function AtlasPage() {
  const [showRobustOnly, setShowRobustOnly] = useState(false);
  const [railOpen, setRailOpen] = useState(false);
  const analytics = useJson<Analytics>("/data/analytics.json");

  return (
    <div className="flex h-[100dvh] flex-col overflow-hidden">
      <SiteHeader badge="Screening-grade" />
      <StatBar analytics={analytics} />

      <div className="relative flex min-h-0 flex-1">
        {/* Rail: in flow from lg, an overlay drawer below it. */}
        <aside
          className={`absolute inset-y-0 left-0 z-30 w-72 max-w-[85vw] overflow-y-auto border-r border-line bg-surface transition-transform lg:static lg:z-auto lg:w-72 lg:max-w-none lg:translate-x-0 ${
            railOpen ? "translate-x-0 shadow-2xl" : "-translate-x-full lg:shadow-none"
          }`}
        >
          <LegendPanel />
        </aside>

        {railOpen && (
          <button
            type="button"
            aria-label="Close legend"
            onClick={() => setRailOpen(false)}
            className="absolute inset-0 z-20 bg-black/40 lg:hidden"
          />
        )}

        <div className="relative min-h-0 min-w-0 flex-1">
          <MapShell showRobustOnly={showRobustOnly} />

          {/* Controls float over the map, wrapping instead of overlapping. */}
          <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex flex-wrap items-start justify-between gap-2 p-3">
            <button
              type="button"
              onClick={() => setRailOpen(true)}
              className="pointer-events-auto rounded-full border border-line bg-surface/95 px-3 py-1.5 text-xs text-foreground shadow-lg backdrop-blur transition-colors hover:border-channel lg:hidden"
            >
              Legend
            </button>

            <button
              type="button"
              role="switch"
              aria-checked={showRobustOnly}
              onClick={() => setShowRobustOnly((v) => !v)}
              className={`pointer-events-auto ml-auto flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs shadow-lg backdrop-blur transition-colors ${
                showRobustOnly
                  ? "border-flag/60 bg-flag/20 text-foreground"
                  : "border-line bg-surface/95 text-fog hover:border-channel"
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${showRobustOnly ? "bg-flag" : "bg-fog/50"}`}
                aria-hidden
              />
              Robust hotspots only
            </button>
          </div>

          <p className="pointer-events-none absolute inset-x-0 bottom-0 z-10 bg-gradient-to-t from-background/95 via-background/80 to-transparent pb-16 pl-3 pr-20 pt-8 text-[10px] leading-relaxed text-fog sm:pb-8 sm:pl-4 sm:pr-24 sm:text-[11px]">
            Screening-grade, not design-grade. Real pipeline output, every layer cited in
            data/SOURCES.md. Verify against field survey.
          </p>
        </div>
      </div>
    </div>
  );
}
