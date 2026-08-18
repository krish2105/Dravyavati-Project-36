"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/atlas", label: "Atlas" },
  { href: "/analysis", label: "Analysis" },
  { href: "/segments", label: "Segments" },
  { href: "/method", label: "Method" },
  { href: "/sources", label: "Sources" },
  { href: "/limitations", label: "Limits" },
];

/**
 * One header for every interior page. Previously each page rolled its own,
 * which is why the title wrapped to two lines and collided with the pills on
 * a phone. Constraints that keep it aligned at every width: the brand never
 * wraps, the nav scrolls horizontally instead of reflowing, and nothing
 * depends on there being room for all of it at once.
 */
export function SiteHeader({ badge }: { badge?: string }) {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-surface/95 backdrop-blur">
      <div className="flex h-12 items-center gap-3 px-3 sm:px-4">
        <Link
          href="/"
          className="flex shrink-0 items-center gap-2 text-sm font-medium text-foreground transition-colors hover:text-channel-dim dark:hover:text-channel"
        >
          <span aria-hidden>←</span>
          <span className="whitespace-nowrap">Dravyavati Atlas</span>
        </Link>

        {badge && (
          <span className="hidden shrink-0 rounded-full bg-channel/15 px-2.5 py-0.5 font-mono text-[10px] uppercase tracking-wide text-channel-dim dark:text-channel sm:inline">
            {badge}
          </span>
        )}

        <nav className="-mx-1 ml-auto flex min-w-0 items-center gap-1 overflow-x-auto px-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {NAV.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`shrink-0 whitespace-nowrap rounded-full px-2.5 py-1 text-xs transition-colors ${
                  active
                    ? "bg-channel/15 font-medium text-channel-dim dark:text-channel"
                    : "text-fog hover:text-foreground"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
          <a
            href="/brief/Dravyavati_Corridor_Constraint_Atlas_Brief.pdf"
            className="ml-1 shrink-0 whitespace-nowrap rounded-full border border-line px-2.5 py-1 text-xs text-foreground transition-colors hover:border-channel"
          >
            PDF
          </a>
        </nav>
      </div>
    </header>
  );
}
