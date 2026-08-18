"use client";

import { useState } from "react";
import Link from "next/link";
import { MapShell } from "@/components/atlas/map-shell";
import { ProvenanceBanner } from "@/components/atlas/provenance-banner";
import { LegendPanel } from "@/components/atlas/legend-panel";
import { SensitivitySlider } from "@/components/atlas/sensitivity-slider";
import { KpiStrip } from "@/components/atlas/kpi-strip";

export default function AtlasPage() {
  const [showRobustOnly, setShowRobustOnly] = useState(false);

  return (
    <div className="flex h-screen w-full flex-col">
      <header className="z-30 flex items-center justify-between border-b border-line bg-surface px-4 py-2.5">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-sm font-medium text-fog transition-colors hover:text-foreground">
            ← Dravyavati Atlas
          </Link>
          <span className="rounded-full bg-channel/15 px-2.5 py-0.5 font-mono text-[10px] uppercase tracking-wide text-channel-dim dark:text-channel">
            Screening-grade
          </span>
        </div>
        <p className="hidden font-mono text-[11px] text-fog sm:block">
          Screening-grade, not design-grade. All findings require verification against field
          survey.
        </p>
      </header>

      <KpiStrip />

      <div className="flex flex-1 overflow-hidden">
        <aside className="hidden w-72 shrink-0 overflow-y-auto border-r border-line bg-surface md:block">
          <LegendPanel />
        </aside>

        <div className="relative flex-1">
          <ProvenanceBanner />
          <MapShell showRobustOnly={showRobustOnly} />
          <SensitivitySlider showRobustOnly={showRobustOnly} onChange={setShowRobustOnly} />
        </div>
      </div>
    </div>
  );
}
