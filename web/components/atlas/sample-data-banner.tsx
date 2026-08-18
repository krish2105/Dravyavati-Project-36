export function SampleDataBanner() {
  return (
    <div
      role="status"
      className="pointer-events-none absolute inset-x-0 top-0 z-20 flex justify-center px-4 pt-4"
    >
      <div
        className="pointer-events-auto flex max-w-xl items-center gap-3 rounded-xl border border-flag/40 bg-flag/15
                   px-4 py-2.5 text-xs text-foreground shadow-[0_8px_24px_rgba(0,0,0,0.18)] backdrop-blur-md"
      >
        <span className="h-2 w-2 shrink-0 rounded-full bg-flag" aria-hidden />
        <p>
          <strong className="font-semibold">SAMPLE DATA — pipeline not yet run.</strong>{" "}
          The river line is real (OpenStreetMap, cited in{" "}
          <code className="rounded bg-surface-muted px-1 py-0.5 font-mono text-[0.9em]">
            data/SOURCES.md
          </code>
          ). Every constraint score below is a placeholder pending the scoring pipeline.
        </p>
      </div>
    </div>
  );
}
