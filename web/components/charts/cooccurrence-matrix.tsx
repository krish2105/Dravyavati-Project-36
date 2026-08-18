"use client";

import { useState } from "react";

/**
 * Which constraints fire together, and how often. A per-constraint view
 * hides compound risk: a chainage that is moderate on six things at once
 * is a harder engineering problem than one that is severe on a single
 * thing, and only a pairwise view surfaces that.
 */
export function CooccurrenceMatrix({ labels, matrix }: { labels: string[]; matrix: number[][] }) {
  const [hover, setHover] = useState<{ i: number; j: number } | null>(null);
  if (!labels.length) return null;

  const max = Math.max(...matrix.flatMap((row, i) => row.filter((_, j) => i !== j)), 1);
  const cell = 26;
  const labelW = 190;
  const size = labels.length * cell;

  return (
    <div className="overflow-x-auto">
      <svg
        width={labelW + size + 8}
        height={labelW + size + 8}
        role="img"
        aria-label="Constraint co-occurrence matrix"
        className="max-w-full"
      >
        {labels.map((label, i) => (
          <text
            key={`row-${label}`}
            x={labelW - 8}
            y={labelW + i * cell + cell / 2 + 4}
            textAnchor="end"
            fontSize={11}
            fill={hover?.i === i || hover?.j === i ? "var(--foreground)" : "var(--fog)"}
          >
            {label}
          </text>
        ))}
        {labels.map((label, j) => (
          <text
            key={`col-${label}`}
            x={labelW + j * cell + cell / 2}
            y={labelW - 8}
            textAnchor="start"
            fontSize={11}
            fill={hover?.i === j || hover?.j === j ? "var(--foreground)" : "var(--fog)"}
            transform={`rotate(-90 ${labelW + j * cell + cell / 2} ${labelW - 8})`}
          >
            {label}
          </text>
        ))}

        {matrix.map((row, i) =>
          row.map((value, j) => {
            const diagonal = i === j;
            const intensity = diagonal ? 0 : value / max;
            return (
              <rect
                key={`${i}-${j}`}
                x={labelW + j * cell}
                y={labelW + i * cell}
                width={cell - 2}
                height={cell - 2}
                rx={3}
                fill={diagonal ? "var(--surface-muted)" : "var(--flag)"}
                opacity={diagonal ? 0.5 : 0.12 + intensity * 0.88}
                stroke={hover && hover.i === i && hover.j === j ? "var(--foreground)" : "none"}
                strokeWidth={1.5}
                onMouseEnter={() => setHover({ i, j })}
                onMouseLeave={() => setHover(null)}
              />
            );
          }),
        )}
      </svg>

      <p className="mt-2 font-mono text-[11px] text-fog">
        {hover && hover.i !== hover.j
          ? `${labels[hover.i]} + ${labels[hover.j]} — ${matrix[hover.i][hover.j]} segments score ≥2 on both`
          : "Cell darkness = number of segments scoring ≥2 on both constraints. Diagonal muted."}
      </p>
    </div>
  );
}
