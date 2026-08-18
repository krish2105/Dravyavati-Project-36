"use client";

import { Counter } from "./counter";
import { useJson, type Analytics } from "@/lib/analytics";

/**
 * Reads the pipeline's own output rather than carrying hardcoded figures.
 * These drifted once already — the hero claimed 36 km and 12 categories
 * while the pipeline had moved to 41.2 km and 13, which is precisely the
 * kind of silent divergence this project's provenance rule exists to stop.
 *
 * Both lengths are shown deliberately. ~36 km is the length reported in
 * press coverage of the proposed project; 41.2 km is what this
 * reconstruction actually measures. Presenting only one would either hide
 * our own result or imply we matched a figure we did not.
 */
export function HeroStats() {
  const analytics = useJson<Analytics>("/data/analytics.json");
  const lengthKm = analytics?.corridor.length_km;
  const categories = analytics?.corridor.constraint_count;

  return (
    <div className="flex flex-wrap items-end gap-x-10 gap-y-6 pt-4 sm:gap-x-12">
      <div>
        <div className="font-display text-4xl text-foreground">
          <span className="text-fog">~36</span>
          <span className="text-fog"> / </span>
          {lengthKm ? <Counter to={Math.round(lengthKm * 10) / 10} /> : "41.2"}
          <span className="text-2xl"> km</span>
        </div>
        <p className="mt-1 max-w-xs text-sm text-fog">
          proposed length as reported, against {lengthKm ? lengthKm.toFixed(1) : "41.2"} km
          reconstructed here from public channel geometry
        </p>
      </div>
      <div>
        <div className="font-display text-4xl text-foreground">
          <Counter to={categories ?? 13} />
        </div>
        <p className="mt-1 text-sm text-fog">constraint categories scored per segment</p>
      </div>
      <div>
        <div className="font-display text-4xl text-foreground">
          <Counter to={analytics?.corridor.segments ?? 413} />
        </div>
        <p className="mt-1 text-sm text-fog">100 m chainage segments</p>
      </div>
    </div>
  );
}
