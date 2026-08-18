"use client";

import type { FeatureImportance } from "@/lib/analytics";

/**
 * Permutation importance from the neural surrogate: how much worse the
 * surrogate reproduces the composite when each constraint is shuffled.
 * Answers "which constraint is actually driving the ranking", which is the
 * question a reviewer asks immediately after seeing a ranked list.
 */
export function ImportanceTornado({ data }: { data: FeatureImportance }) {
  const max = Math.max(...data.features.map((f) => f.importance + f.std), 0.0001);

  return (
    <div>
      <ul className="space-y-1.5">
        {data.features.map((f) => {
          const pct = (f.importance / max) * 100;
          const errPct = (f.std / max) * 100;
          return (
            <li key={f.label} className="grid grid-cols-[minmax(9rem,14rem)_1fr_3.5rem] items-center gap-3">
              <span className="truncate text-xs text-fog" title={f.label}>
                {f.label}
              </span>
              <span className="relative block h-3 rounded-sm bg-surface-muted">
                <span
                  className="absolute inset-y-0 left-0 rounded-sm bg-channel"
                  style={{ width: `${Math.max(pct, 0.5)}%` }}
                />
                <span
                  className="absolute inset-y-0 border-x border-fog/50"
                  style={{ left: `${Math.max(pct - errPct, 0)}%`, width: `${errPct * 2}%` }}
                  aria-hidden
                />
              </span>
              <span className="text-right font-mono text-[11px] tabular-nums text-foreground">
                {f.importance.toFixed(3)}
              </span>
            </li>
          );
        })}
      </ul>
      <p className="mt-3 border-t border-line pt-2 text-[11px] leading-relaxed text-fog">
        Multi-layer perceptron (64/32) fitted to reproduce the composite from the constraint vector,
        R² <span className="font-mono text-foreground">{data.surrogate_r2.toFixed(3)}</span>. Bars show mean
        permutation importance over 20 repeats; the lighter span is ±1 SD. This explains the composite we
        computed — it does not predict any quantity measured outside this repository.
      </p>
    </div>
  );
}
