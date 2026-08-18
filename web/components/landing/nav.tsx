import Link from "next/link";

export function Nav() {
  return (
    <header className="fixed inset-x-0 top-0 z-40 flex justify-center px-4 pt-4">
      <nav
        className="flex w-full max-w-3xl items-center justify-between rounded-full border border-line bg-surface/70 px-5 py-3
                   shadow-[0_8px_32px_rgba(0,0,0,0.18)] backdrop-blur-xl backdrop-saturate-150 dark:shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
      >
        <span className="font-display text-sm font-medium tracking-tight text-foreground">
          Dravyavati Atlas
        </span>
        <div className="flex items-center gap-6 text-sm text-fog">
          <a href="#method" className="transition-colors hover:text-foreground">
            Method
          </a>
          <a href="#sources" className="transition-colors hover:text-foreground">
            Sources
          </a>
          <Link
            href="/atlas"
            data-cursor-hover
            className="rounded-full bg-channel/15 px-4 py-1.5 font-medium text-channel-dim transition-colors hover:bg-channel/25 dark:text-channel"
          >
            Open atlas
          </Link>
        </div>
      </nav>
    </header>
  );
}
