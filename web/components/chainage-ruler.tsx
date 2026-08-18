"use client";

import { cn } from "@/lib/utils";

/**
 * The atlas's own primary key (chainage_m, 100 m segments) made visible.
 * Used as the landing hero's signature element and reused, unmodified,
 * as the atlas map's ruler — same motif, two contexts.
 */
export function ChainageRuler({
  lengthM = 36000,
  majorStepM = 5000,
  orientation = "vertical",
  className,
}: {
  lengthM?: number;
  majorStepM?: number;
  orientation?: "vertical" | "horizontal";
  className?: string;
}) {
  const majors = Math.floor(lengthM / majorStepM);
  const ticks = Array.from({ length: majors + 1 }, (_, i) => i * majorStepM);
  const isVertical = orientation === "vertical";

  return (
    <div
      role="img"
      aria-label={`Chainage ruler, 0 to ${lengthM.toLocaleString()} metres, major ticks every ${majorStepM.toLocaleString()} m`}
      className={cn(
        "relative flex font-mono text-[10px] text-fog",
        isVertical ? "h-full w-10 flex-col justify-between" : "h-10 w-full flex-row justify-between",
        className,
      )}
    >
      <div
        className={cn(
          "absolute bg-line",
          isVertical ? "left-1/2 top-0 h-full w-px -translate-x-1/2" : "left-0 top-1/2 h-px w-full -translate-y-1/2",
        )}
      />
      {ticks.map((m) => (
        <div
          key={m}
          className={cn(
            "relative flex items-center",
            isVertical ? "flex-row gap-2" : "flex-col gap-1",
          )}
        >
          <span
            className={cn("block bg-channel", isVertical ? "h-px w-3" : "h-3 w-px")}
            aria-hidden
          />
          <span className="tabular-nums">{(m / 1000).toFixed(0)}k</span>
        </div>
      ))}
    </div>
  );
}
