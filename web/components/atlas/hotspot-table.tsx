"use client";

import type { HotspotCorridor } from "@/lib/analytics";
import { km } from "@/lib/analytics";

/**
 * Pack §7 page 2: the robust hotspot table. Chainage, extent, why it
 * matters. Nothing else — no recommendation, no alignment opinion.
 */
export function HotspotTable({ corridors }: { corridors: HotspotCorridor[] }) {
  if (!corridors.length) {
    return <p className="text-sm text-fog">No robust hotspot corridors at the current weighting.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[36rem] border-collapse text-sm">
        <thead>
          <tr className="border-b border-line text-left font-mono text-[10px] uppercase tracking-wide text-fog">
            <th className="py-2 pr-4 font-normal">Extent</th>
            <th className="py-2 pr-4 font-normal">Length</th>
            <th className="py-2 pr-4 font-normal">Mean composite</th>
            <th className="py-2 font-normal">Leading constraints</th>
          </tr>
        </thead>
        <tbody>
          {corridors.map((c) => (
            <tr key={c.id} className="border-b border-line/60 align-top">
              <td className="py-3 pr-4 font-mono text-xs tabular-nums text-foreground">
                {km(c.start_m)} – {km(c.end_m)}
              </td>
              <td className="py-3 pr-4 font-mono text-xs tabular-nums text-fog">
                {((c.end_m - c.start_m) / 1000).toFixed(1)} km
              </td>
              <td className="py-3 pr-4">
                <span className="inline-flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-flag" aria-hidden />
                  <span className="font-mono text-xs tabular-nums text-foreground">
                    {c.mean_composite.toFixed(2)}
                  </span>
                </span>
              </td>
              <td className="py-3 text-xs text-fog">
                {c.top_drivers.map((d) => `${d.label} (${d.mean_score.toFixed(1)})`).join(" · ")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-3 text-[11px] leading-relaxed text-fog">
        Robust = severity band unchanged across a ±35% sweep of every constraint weight. Contiguous robust
        segments are grouped into corridors by DBSCAN over chainage. These are the stretches worth raising;
        anything that appears under only one weighting is an artefact of that weighting, not a finding.
      </p>
    </div>
  );
}
