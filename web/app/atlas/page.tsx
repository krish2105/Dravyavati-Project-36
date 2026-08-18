import Link from "next/link";
import { MapShell } from "@/components/atlas/map-shell";
import { SampleDataBanner } from "@/components/atlas/sample-data-banner";
import { LegendPanel } from "@/components/atlas/legend-panel";
import { SensitivitySlider } from "@/components/atlas/sensitivity-slider";

export default function AtlasPage() {
  return (
    <div className="flex h-screen w-full flex-col">
      <header className="z-30 flex items-center justify-between border-b border-line bg-surface px-4 py-2.5">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-sm font-medium text-fog transition-colors hover:text-foreground">
            ← Dravyavati Atlas
          </Link>
          <span className="rounded-full bg-flag/15 px-2.5 py-0.5 font-mono text-[10px] uppercase tracking-wide text-flag">
            Sample data
          </span>
        </div>
        <p className="hidden font-mono text-[11px] text-fog sm:block">
          Screening-grade, not design-grade. All findings require verification against field
          survey.
        </p>
      </header>

      <div className="relative flex-1">
        <SampleDataBanner />
        <LegendPanel />
        <MapShell />
        <SensitivitySlider />
      </div>
    </div>
  );
}
