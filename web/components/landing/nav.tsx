import Link from "next/link";

export function Nav() {
  return (
    <header className="fixed inset-x-0 top-0 z-40 flex justify-center px-4 pt-4">
      <nav
        className="flex w-full max-w-3xl items-center gap-3 rounded-full border border-line bg-surface/70 px-4 py-2.5 sm:px-5 sm:py-3
                   shadow-[0_8px_32px_rgba(0,0,0,0.18)] backdrop-blur-xl backdrop-saturate-150 dark:shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
      >
        <span className="shrink-0 whitespace-nowrap font-display text-sm font-medium tracking-tight text-foreground">
          Dravyavati Atlas
        </span>
        <div className="-mx-1 ml-auto flex min-w-0 items-center gap-4 overflow-x-auto px-1 text-sm text-fog [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          <a href="#method" className="shrink-0 whitespace-nowrap transition-colors hover:text-foreground">
            Method
          </a>
          <a href="#sources" className="shrink-0 whitespace-nowrap transition-colors hover:text-foreground">
            Sources
          </a>
          <Link href="/analysis" className="shrink-0 whitespace-nowrap transition-colors hover:text-foreground">
            Analysis
          </Link>
          <Link
            href="/atlas"
            data-cursor-hover
            className="shrink-0 whitespace-nowrap rounded-full bg-channel/15 px-3 py-1.5 font-medium text-channel-dim transition-colors hover:bg-channel/25 dark:text-channel"
          >
            Open atlas
          </Link>
        </div>
      </nav>
    </header>
  );
}
