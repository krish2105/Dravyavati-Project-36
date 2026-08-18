import type { ReactNode } from "react";

/** Shared primitives for the prose/reference pages. Kept deliberately plain:
 *  these pages are read, not browsed, so legibility beats decoration. */

export function DocPage({
  title,
  lede,
  children,
}: {
  title: string;
  lede: string;
  children: ReactNode;
}) {
  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 sm:py-12">
      <h1 className="font-display text-2xl font-medium tracking-tight text-foreground sm:text-3xl">
        {title}
      </h1>
      <p className="mt-2 text-sm leading-relaxed text-fog sm:text-base">{lede}</p>
      <div className="mt-8 space-y-8">{children}</div>
    </main>
  );
}

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <h2 className="font-display text-base font-medium text-foreground sm:text-lg">{title}</h2>
      <div className="mt-3 space-y-3 text-sm leading-relaxed text-fog">{children}</div>
    </section>
  );
}

export function Rows({ rows }: { rows: [string, ReactNode][] }) {
  return (
    <dl className="divide-y divide-line border-y border-line">
      {rows.map(([k, v]) => (
        <div key={k} className="grid gap-1 py-3 sm:grid-cols-[minmax(0,13rem)_1fr] sm:gap-4">
          <dt className="text-xs font-medium text-foreground sm:text-sm">{k}</dt>
          <dd className="text-xs leading-relaxed text-fog sm:text-sm">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

export function Confidence({ level }: { level: "high" | "medium" | "low" }) {
  const style = {
    high: "bg-channel/15 text-channel-dim dark:text-channel",
    medium: "bg-fog/15 text-fog",
    low: "bg-flag/15 text-flag",
  }[level];
  return (
    <span className={`rounded-full px-2 py-0.5 font-mono text-[10px] uppercase tracking-wide ${style}`}>
      {level}
    </span>
  );
}
