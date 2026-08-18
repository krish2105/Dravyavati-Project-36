"use client";

import { useMemo, useState } from "react";
import { BAND_COLOR, type ProfilePoint } from "@/lib/analytics";

/**
 * The signature view: composite score against distance along the corridor,
 * with the Monte Carlo 90% band behind it. This is how a corridor engineer
 * actually reads a route — chainage on the x-axis, not a map.
 */
export function ChainageProfile({
  profile,
  onHover,
}: {
  profile: ProfilePoint[];
  onHover?: (p: ProfilePoint | null) => void;
}) {
  const [cursor, setCursor] = useState<number | null>(null);

  const W = 1000;
  const H = 260;
  const PAD = { top: 16, right: 16, bottom: 30, left: 40 };

  const { maxX, maxY, linePath, bandPath } = useMemo(() => {
    if (!profile.length) return { maxX: 1, maxY: 1, linePath: "", bandPath: "" };
    const maxX = Math.max(...profile.map((p) => p.chainage_m));
    const maxY = Math.max(...profile.map((p) => (isFinite(p.p95) ? p.p95 : p.composite))) * 1.1;

    const sx = (m: number) => PAD.left + (m / maxX) * (W - PAD.left - PAD.right);
    const sy = (v: number) => H - PAD.bottom - (v / maxY) * (H - PAD.top - PAD.bottom);

    const linePath = profile.map((p, i) => `${i ? "L" : "M"}${sx(p.chainage_m)},${sy(p.composite)}`).join(" ");

    const hasBand = profile.every((p) => isFinite(p.p05) && isFinite(p.p95));
    const upper = profile.map((p, i) => `${i ? "L" : "M"}${sx(p.chainage_m)},${sy(p.p95)}`).join(" ");
    const lower = [...profile].reverse().map((p) => `L${sx(p.chainage_m)},${sy(p.p05)}`).join(" ");
    const bandPath = hasBand ? `${upper} ${lower} Z` : "";

    return { maxX, maxY, linePath, bandPath };
  }, [profile]);

  if (!profile.length) return null;

  const sx = (m: number) => PAD.left + (m / maxX) * (W - PAD.left - PAD.right);
  const sy = (v: number) => H - PAD.bottom - (v / maxY) * (H - PAD.top - PAD.bottom);

  const active = cursor !== null ? profile[cursor] : null;

  function handleMove(e: React.MouseEvent<SVGSVGElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * W;
    const m = ((x - PAD.left) / (W - PAD.left - PAD.right)) * maxX;
    let best = 0;
    let bestD = Infinity;
    profile.forEach((p, i) => {
      const d = Math.abs(p.chainage_m - m);
      if (d < bestD) {
        bestD = d;
        best = i;
      }
    });
    setCursor(best);
    onHover?.(profile[best]);
  }

  const ticks = Array.from({ length: Math.floor(maxX / 5000) + 1 }, (_, i) => i * 5000);

  return (
    <div className="w-full">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full"
        style={{ height: "clamp(200px, 26vw, 280px)" }}
        onMouseMove={handleMove}
        onMouseLeave={() => {
          setCursor(null);
          onHover?.(null);
        }}
        role="img"
        aria-label="Composite constraint score along the corridor, with 90% uncertainty band"
      >
        {[0.25, 0.5, 0.75, 1].map((f) => (
          <line
            key={f}
            x1={PAD.left}
            x2={W - PAD.right}
            y1={sy(maxY * f)}
            y2={sy(maxY * f)}
            stroke="var(--line)"
            strokeWidth={1}
          />
        ))}

        {bandPath && <path d={bandPath} fill="var(--channel)" opacity={0.16} />}

        {profile.map((p) =>
          p.band !== "low" ? (
            <rect
              key={p.chainage_m}
              x={sx(p.chainage_m)}
              y={PAD.top}
              width={Math.max((W - PAD.left - PAD.right) / profile.length, 1.2)}
              height={H - PAD.top - PAD.bottom}
              fill={BAND_COLOR[p.band]}
              opacity={p.band === "high" ? 0.16 : 0.08}
            />
          ) : null,
        )}

        <path d={linePath} fill="none" stroke="var(--foreground)" strokeWidth={1.6} opacity={0.9} />

        {profile.map((p) =>
          p.robust ? (
            <circle key={p.chainage_m} cx={sx(p.chainage_m)} cy={sy(p.composite)} r={3} fill="var(--flag)" />
          ) : null,
        )}

        {ticks.map((t) => (
          <g key={t}>
            <line x1={sx(t)} x2={sx(t)} y1={H - PAD.bottom} y2={H - PAD.bottom + 4} stroke="var(--fog)" />
            <text x={sx(t)} y={H - 10} textAnchor="middle" fontSize={11} fill="var(--fog)" fontFamily="var(--font-mono)">
              {t / 1000}k
            </text>
          </g>
        ))}
        <text x={4} y={sy(maxY) + 4} fontSize={10} fill="var(--fog)" fontFamily="var(--font-mono)">
          {maxY.toFixed(1)}
        </text>
        <text x={10} y={H - PAD.bottom} fontSize={10} fill="var(--fog)" fontFamily="var(--font-mono)">
          0
        </text>

        {active && (
          <g>
            <line
              x1={sx(active.chainage_m)}
              x2={sx(active.chainage_m)}
              y1={PAD.top}
              y2={H - PAD.bottom}
              stroke="var(--foreground)"
              strokeWidth={1}
              opacity={0.5}
            />
            <circle cx={sx(active.chainage_m)} cy={sy(active.composite)} r={4.5} fill="var(--foreground)" />
          </g>
        )}
      </svg>

      <div className="mt-1 flex flex-wrap items-center justify-between gap-x-4 gap-y-1 font-mono text-[11px] text-fog">
        <span>
          {active
            ? `ch ${active.chainage_m} m · composite ${active.composite.toFixed(2)} · 90% CI [${active.p05.toFixed(2)}–${active.p95.toFixed(2)}] · ${active.band}${active.robust ? " · robust" : ""}${active.anomaly ? " · anomalous" : ""}`
            : "Hover the profile for per-chainage detail"}
        </span>
        <span className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-3 rounded-sm bg-channel/30" /> 90% CI
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-flag" /> robust hotspot
          </span>
        </span>
      </div>
    </div>
  );
}
