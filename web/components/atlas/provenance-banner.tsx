export function ProvenanceBanner() {
  return (
    <div
      role="status"
      className="pointer-events-none absolute inset-x-0 top-0 z-20 flex justify-center px-4 pt-4"
    >
      <div
        className="pointer-events-auto flex max-w-full items-start gap-2 rounded-2xl border border-flag/40 bg-flag/15
                   px-4 py-2 text-xs text-foreground shadow-[0_8px_24px_rgba(0,0,0,0.18)] backdrop-blur-md sm:rounded-full sm:items-center"
      >
        <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-flag sm:mt-0" aria-hidden />
        <p>
          <strong className="font-semibold">Screening-grade, not design-grade.</strong>{" "}
          <span className="hidden sm:inline">
            Real pipeline output, every layer cited in data/SOURCES.md.
          </span>{" "}
          Verify against field survey.
        </p>
      </div>
    </div>
  );
}
