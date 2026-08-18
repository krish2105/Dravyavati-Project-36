import { SplitText } from "./split-text";
import { Counter } from "./counter";
import { MagneticButton } from "./magnetic-button";
import { ChainageRuler } from "../chainage-ruler";

export function Hero() {
  return (
    <section className="relative flex min-h-screen w-full flex-col justify-center overflow-hidden px-6 pt-28 pb-20 sm:px-10 lg:pl-28">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_60%_50%_at_20%_0%,rgba(47,168,160,0.16),transparent_60%),radial-gradient(ellipse_50%_40%_at_90%_100%,rgba(232,162,61,0.10),transparent_60%)]"
      />

      <ChainageRuler
        className="absolute left-4 top-24 bottom-24 hidden sm:flex lg:left-10"
      />

      <div className="mx-auto flex w-full max-w-4xl flex-col gap-8">
        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-channel-dim dark:text-channel">
          Independent open-data screening — Jaipur, Rajasthan
        </p>

        <h1 className="font-display text-[length:var(--step-hero)] font-medium leading-[0.98] tracking-tight text-foreground">
          <SplitText text="Every 100 metres of the" />
          <br />
          <SplitText text="Dravyavati corridor," className="text-channel-dim dark:text-channel" />
          <br />
          <SplitText text="mapped for what will resist it." />
        </h1>

        <div className="flex flex-wrap items-end gap-x-12 gap-y-6 pt-4">
          <div>
            <div className="font-display text-4xl text-foreground">
              <Counter to={36} suffix=" km" />
            </div>
            <p className="mt-1 text-sm text-fog">reconstructed corridor, Majar Dam → NH-148C</p>
          </div>
          <div>
            <div className="font-display text-4xl text-foreground">
              <Counter to={12} />
            </div>
            <p className="mt-1 text-sm text-fog">constraint categories scored per segment</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-5 pt-4">
          <MagneticButton href="/atlas">Open the atlas →</MagneticButton>
          <a
            href="#sources"
            data-cursor-hover
            className="text-sm font-medium text-fog transition-colors hover:text-foreground"
          >
            See every source cited
          </a>
        </div>

        <p className="max-w-xl border-l-2 border-flag/70 pl-4 pt-6 text-sm leading-relaxed text-fog">
          Screening-grade, not design-grade. Built on open data for constraint triage. All
          findings require verification against field survey.
        </p>
      </div>
    </section>
  );
}
