export function SensitivitySlider() {
  return (
    <div
      className="absolute bottom-24 left-1/2 z-10 w-[min(90vw,28rem)] -translate-x-1/2 rounded-2xl border border-line
                 bg-surface/90 p-4 shadow-[0_8px_24px_rgba(0,0,0,0.18)] backdrop-blur-md dark:shadow-[0_8px_24px_rgba(0,0,0,0.5)] sm:bottom-6"
    >
      <div className="flex items-center justify-between text-xs text-fog">
        <span>Equal weights</span>
        <span>Reweighting sensitivity</span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        defaultValue={50}
        disabled
        aria-label="Constraint reweighting sensitivity — inert until Session 7's sensitivity pass runs"
        className="mt-2 w-full accent-channel opacity-50"
      />
      <p className="mt-2 text-[11px] text-fog">
        Inert placeholder — wired up once Session 7 produces the robust-hotspot reweighting
        sweep.
      </p>
    </div>
  );
}
