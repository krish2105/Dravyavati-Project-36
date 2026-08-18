"use client";

import { useEffect, useMemo, useState } from "react";

/**
 * Live reweighting. The pack's §5 requirement is that weights are a config
 * dict rather than hardcoded, and that the reader can see which chainages
 * survive a reweighting. This makes that interactive: move a weight, and the
 * composite, the severity banding and the ranked chainages all recompute in
 * the browser from the same per-segment scores the pipeline exported.
 *
 * The banding is percentile-based against whatever distribution the current
 * weights produce, exactly as the Python side does it — so "high severity"
 * always means the top decile of *this* weighting, not a fixed cutoff that
 * would classify everything as low.
 */

const CONSTRAINTS: { key: string; label: string }[] = [
  { key: "railway_crossing_score", label: "Railway crossing" },
  { key: "metro_interface_score", label: "Metro interface" },
  { key: "existing_elevated_structure_score", label: "Existing elevated structure" },
  { key: "major_arterial_crossing_score", label: "Major arterial crossing" },
  { key: "restricted_military_area_score", label: "Restricted / military" },
  { key: "entry_exit_feasibility_score", label: "Entry–exit feasibility" },
  { key: "curve_severity_score", label: "Curve severity" },
  { key: "eht_line_crossing_score", label: "EHT line crossing" },
  { key: "dam_check_structure_score", label: "Dam / check structure" },
  { key: "land_availability_score", label: "Land availability" },
  { key: "habitation_proximity_score", label: "Habitation proximity" },
  { key: "builtup_growth_score", label: "Built-up growth" },
  { key: "hydraulic_sensitivity_index", label: "Hydraulic sensitivity" },
];

type Row = Record<string, number>;

export function WeightStudio() {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [weights, setWeights] = useState<Record<string, number>>(
    Object.fromEntries(CONSTRAINTS.map((c) => [c.key, 1])),
  );

  useEffect(() => {
    fetch("/data/chainage_risk.geojson")
      .then((r) => r.json())
      .then((g) =>
        setRows(
          g.features
            .map((f: { properties: Row }) => f.properties)
            .sort((a: Row, b: Row) => a.chainage_m - b.chainage_m),
        ),
      )
      .catch(() => setRows(null));
  }, []);

  const result = useMemo(() => {
    if (!rows) return null;
    const total = Object.values(weights).reduce((a, b) => a + b, 0) || 1;

    const composites = rows.map((r) => {
      let sum = 0;
      for (const c of CONSTRAINTS) {
        const raw = r[c.key] ?? 0;
        // The hydraulic layer is stored 0-1; everything else is 0-3.
        const value = c.key === "hydraulic_sensitivity_index" ? raw * 3 : raw;
        sum += (weights[c.key] ?? 0) * value;
      }
      return sum / total;
    });

    const sorted = [...composites].sort((a, b) => a - b);
    const q = (p: number) => sorted[Math.min(Math.floor(p * sorted.length), sorted.length - 1)];
    const highCut = q(0.9);
    const medCut = q(0.7);

    const bands = composites.map((v) => (v >= highCut ? "high" : v >= medCut ? "medium" : "low"));
    const counts = bands.reduce<Record<string, number>>(
      (acc, b) => ({ ...acc, [b]: (acc[b] ?? 0) + 1 }),
      { high: 0, medium: 0, low: 0 },
    );

    const top = composites
      .map((v, i) => ({ chainage: rows[i].chainage_m, value: v, band: bands[i] }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8);

    return { counts, top, max: Math.max(...composites) };
  }, [rows, weights]);

  const isDefault = CONSTRAINTS.every((c) => weights[c.key] === 1);

  if (!rows) return <p className="text-sm text-fog">Loading segment scores…</p>;

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_15rem]">
      <div>
        <div className="mb-3 flex items-center justify-between gap-3">
          <p className="text-xs text-fog">
            Drag a weight to rebalance the composite. Everything recomputes from the exported
            per-segment scores.
          </p>
          <button
            type="button"
            onClick={() => setWeights(Object.fromEntries(CONSTRAINTS.map((c) => [c.key, 1])))}
            disabled={isDefault}
            className="shrink-0 rounded-full border border-line px-2.5 py-1 text-[11px] text-fog transition-colors enabled:hover:border-channel enabled:hover:text-foreground disabled:opacity-40"
          >
            Reset
          </button>
        </div>

        <div className="space-y-2">
          {CONSTRAINTS.map((c) => (
            <div key={c.key} className="grid grid-cols-[minmax(7rem,12rem)_1fr_2.2rem] items-center gap-2 sm:gap-3">
              <label htmlFor={`w-${c.key}`} className="truncate text-xs text-fog" title={c.label}>
                {c.label}
              </label>
              <input
                id={`w-${c.key}`}
                type="range"
                min={0}
                max={2}
                step={0.05}
                value={weights[c.key]}
                onChange={(e) =>
                  setWeights((w) => ({ ...w, [c.key]: Number(e.target.value) }))
                }
                className="w-full accent-channel"
              />
              <span
                className={`text-right font-mono text-[11px] tabular-nums ${
                  weights[c.key] === 1 ? "text-fog" : "text-foreground"
                }`}
              >
                {weights[c.key].toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      </div>

      <aside className="space-y-4">
        <div>
          <h3 className="mb-2 font-mono text-[10px] uppercase tracking-wide text-fog">
            Severity under these weights
          </h3>
          <dl className="space-y-1 text-xs">
            {(["high", "medium", "low"] as const).map((band) => (
              <div key={band} className="flex justify-between">
                <dt className="capitalize text-fog">{band}</dt>
                <dd
                  className={`font-mono tabular-nums ${
                    band === "high"
                      ? "text-flag"
                      : band === "medium"
                        ? "text-[#c98f4a]"
                        : "text-channel-dim dark:text-channel"
                  }`}
                >
                  {result?.counts[band] ?? 0}
                </dd>
              </div>
            ))}
          </dl>
        </div>

        <div>
          <h3 className="mb-2 font-mono text-[10px] uppercase tracking-wide text-fog">
            Highest-scoring chainages
          </h3>
          <ol className="space-y-1 text-xs">
            {result?.top.map((t) => (
              <li key={t.chainage} className="flex justify-between gap-2">
                <span className="font-mono tabular-nums text-foreground">
                  {(t.chainage / 1000).toFixed(1)} km
                </span>
                <span className="font-mono tabular-nums text-fog">{t.value.toFixed(2)}</span>
              </li>
            ))}
          </ol>
        </div>

        <p className="border-t border-line pt-2 text-[11px] leading-relaxed text-fog">
          Bands are percentiles of the current distribution, not fixed cutoffs. A chainage that only
          appears at the top under one weighting is an artefact of that choice — the robust list on
          this page is the one that survived every weighting tested.
        </p>
      </aside>
    </div>
  );
}
