"use client";

import { useEffect, useState } from "react";

type Stats = {
  lengthKm: number;
  segments: number;
  railwayCrossings: number;
  metroInterfaces: number;
  arterialCrossings: number;
  damStructures: number;
  ehtCrossings: number;
  belowIrcRadius: number;
  ircMinRadius: number;
  pctUnbuilt: number;
  buildingsNear: number;
  segmentsWithBuildings: number;
  high: number;
  medium: number;
  low: number;
  robustHotspots: number;
};

function countClusters(flags: boolean[]): number {
  let count = 0;
  let prev = false;
  for (const f of flags) {
    if (f && !prev) count++;
    prev = f;
  }
  return count;
}

export function KpiStrip() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    fetch("/data/chainage_risk.geojson")
      .then((r) => r.json())
      .then((geojson) => {
        type Props = Record<string, number | string | boolean>;
        const rows: Props[] = geojson.features
          .map((f: { properties: Props }) => f.properties)
          .sort((a: Props, b: Props) => (a.chainage_m as number) - (b.chainage_m as number));

        const flag = (key: string) => rows.map((r) => r[key] === 3);
        const lengthKm = rows.reduce((s, r) => s + (r.segment_length_m as number), 0) / 1000;
        const buildingsNear = rows.reduce((s, r) => s + (r.habitation_building_count as number), 0);
        const avgFracBuilt = rows.reduce((s, r) => s + (r.land_availability_frac_built as number), 0) / rows.length;

        setStats({
          lengthKm,
          segments: rows.length,
          railwayCrossings: countClusters(flag("railway_crossing_score")),
          metroInterfaces: countClusters(flag("metro_interface_score")),
          arterialCrossings: countClusters(flag("major_arterial_crossing_score")),
          damStructures: countClusters(flag("dam_check_structure_score")),
          ehtCrossings: countClusters(flag("eht_line_crossing_score")),
          belowIrcRadius: rows.filter((r) => r.curve_severity_score === 3).length,
          ircMinRadius: (rows[0]?.irc86_min_radius_m as number) ?? 150,
          pctUnbuilt: (1 - avgFracBuilt) * 100,
          buildingsNear,
          segmentsWithBuildings: rows.filter((r) => (r.habitation_building_count as number) > 0).length,
          high: rows.filter((r) => r.severity_band === "high").length,
          medium: rows.filter((r) => r.severity_band === "medium").length,
          low: rows.filter((r) => r.severity_band === "low").length,
          robustHotspots: rows.filter((r) => r.robust_hotspot === true).length,
        });
      })
      .catch(() => setStats(null));
  }, []);

  const v = (n: number | undefined, digits = 0) => (stats ? n!.toFixed(digits) : "—");

  return (
    <div className="grid grid-cols-1 gap-px border-b border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
      <section className="bg-surface p-4">
        <h2 className="font-mono text-[10px] uppercase tracking-wide text-fog">Corridor scale</h2>
        <div className="mt-1 font-display text-2xl font-medium tabular-nums text-foreground">
          {v(stats?.lengthKm, 1)} km
        </div>
        <p className="text-xs text-fog">reconstructed corridor · target 34–38 km</p>
        <dl className="mt-3 space-y-1 text-xs text-fog">
          <div className="flex justify-between">
            <dt>Segments analysed</dt>
            <dd className="tabular-nums text-foreground">{v(stats?.segments)}</dd>
          </div>
          <div className="flex justify-between">
            <dt>Constraint categories</dt>
            <dd className="tabular-nums text-foreground">12</dd>
          </div>
        </dl>
      </section>

      <section className="bg-surface p-4">
        <h2 className="font-mono text-[10px] uppercase tracking-wide text-fog">Crossings &amp; compliance</h2>
        <div className="mt-1 font-display text-2xl font-medium tabular-nums text-foreground">
          {v(stats?.belowIrcRadius)}
        </div>
        <p className="text-xs text-fog">segments below IRC:86 {stats?.ircMinRadius ?? 150}m min radius (60 km/h)</p>
        <dl className="mt-3 space-y-1 text-xs text-fog">
          <div className="flex justify-between">
            <dt>Railway crossings</dt>
            <dd className="tabular-nums text-foreground">{v(stats?.railwayCrossings)}</dd>
          </div>
          <div className="flex justify-between">
            <dt>Major arterial crossings</dt>
            <dd className="tabular-nums text-foreground">{v(stats?.arterialCrossings)}</dd>
          </div>
          <div className="flex justify-between">
            <dt>Dam / check structures</dt>
            <dd className="tabular-nums text-foreground">{v(stats?.damStructures)}</dd>
          </div>
          <div className="flex justify-between text-flag">
            <dt>EHT line crossings</dt>
            <dd className="tabular-nums">{v(stats?.ehtCrossings)} · low confidence</dd>
          </div>
        </dl>
      </section>

      <section className="bg-surface p-4">
        <h2 className="font-mono text-[10px] uppercase tracking-wide text-fog">Land &amp; habitation</h2>
        <div className="mt-1 font-display text-2xl font-medium tabular-nums text-foreground">
          {v(stats?.pctUnbuilt, 1)}%
        </div>
        <p className="text-xs text-fog">of the 60m corridor buffer is unbuilt (mean across segments)</p>
        <dl className="mt-3 space-y-1 text-xs text-fog">
          <div className="flex justify-between">
            <dt>Buildings within 100m (approx.)</dt>
            <dd className="tabular-nums text-foreground">{v(stats?.buildingsNear)}</dd>
          </div>
          <div className="flex justify-between">
            <dt>Segments with any building nearby</dt>
            <dd className="tabular-nums text-foreground">
              {v(stats?.segmentsWithBuildings)} / {v(stats?.segments)}
            </dd>
          </div>
        </dl>
      </section>

      <section className="bg-surface p-4">
        <h2 className="font-mono text-[10px] uppercase tracking-wide text-fog">Robustness</h2>
        <div className="mt-1 font-display text-2xl font-medium tabular-nums text-foreground">
          {v(stats?.robustHotspots)}
        </div>
        <p className="text-xs text-fog">robust hotspots · stable under ±35% reweighting</p>
        <dl className="mt-3 space-y-1 text-xs">
          <div className="flex justify-between">
            <dt className="text-fog">High severity</dt>
            <dd className="tabular-nums text-flag">{v(stats?.high)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-fog">Medium severity</dt>
            <dd className="tabular-nums text-[#c98f4a]">{v(stats?.medium)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-fog">Low severity</dt>
            <dd className="tabular-nums text-channel-dim dark:text-channel">{v(stats?.low)}</dd>
          </div>
        </dl>
      </section>
    </div>
  );
}
