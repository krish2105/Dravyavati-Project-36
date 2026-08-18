"use client";

export function SensitivitySlider({
  showRobustOnly,
  onChange,
}: {
  showRobustOnly: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <div
      className="absolute bottom-24 left-1/2 z-10 w-[min(90vw,28rem)] -translate-x-1/2 rounded-2xl border border-line
                 bg-surface/90 p-4 shadow-[0_8px_24px_rgba(0,0,0,0.18)] backdrop-blur-md dark:shadow-[0_8px_24px_rgba(0,0,0,0.5)] sm:bottom-6"
    >
      <div className="flex items-center justify-between gap-3 text-xs text-fog">
        <span className={showRobustOnly ? "" : "font-medium text-foreground"}>All constrained segments</span>
        <button
          type="button"
          role="switch"
          aria-checked={showRobustOnly}
          onClick={() => onChange(!showRobustOnly)}
          className="relative h-6 w-11 shrink-0 rounded-full bg-line transition-colors data-[on=true]:bg-flag"
          data-on={showRobustOnly}
        >
          <span
            className="absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-surface shadow transition-transform"
            style={{ transform: showRobustOnly ? "translateX(20px)" : "translateX(0)" }}
          />
        </button>
        <span className={showRobustOnly ? "font-medium text-foreground" : ""}>Robust hotspots only</span>
      </div>
      <p className="mt-2 text-[11px] text-fog">
        Robust = severity band unchanged across a ±35% sweep of every constraint weight (pack
        §5's reweighting sensitivity pass). {showRobustOnly ? "Showing" : "Highlighting"} the
        chainages worth mentioning out loud, not artefacts of one weighting choice.
      </p>
    </div>
  );
}
