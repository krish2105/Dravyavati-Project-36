# Dravyavati Corridor Constraint Atlas — Frontend Prototype Design

**Date:** 2026-08-18
**Status:** Approved (pivot from Session 1 Python backend scaffold, see `DRAVYAVATI_ATLAS_claude_code_pack.md`)

## Why this exists

The pack's own 8-session plan puts the web viewer at Session 8, after the full scoring
pipeline. The user asked to pivot early and build a frontend prototype now — a floating
theme toggle and "modern UI" treatment, end-to-end. The Python backend scaffold (originally
planned as Session 1) is paused, not abandoned.

The real audience for the eventual live URL (per pack §7) is a JDA/engineering Technical
Director being asked to trust a screening tool — not a portfolio audience. That shaped the
two-mode split below: one view to demonstrate craft, one view that has to read as credible
engineering software.

## Decisions (from brainstorming)

1. **Two modes, one app.** `/` is a bold, Awwwards-style landing page. `/atlas` is a sober,
   dense app shell. Both share one floating theme toggle mounted in the root layout, so theme
   state persists across routes.
2. **Real data over fake data.** The atlas view pulls the actual Dravyavati river line from
   OpenStreetMap (Overpass API) — real, cite-able geometry — rather than an invented shape.
   Constraint *scores* don't exist yet (Sessions 2–7 haven't run), so those stay hard-coded
   placeholders with a permanent on-map "SAMPLE DATA — pipeline not yet run" banner. This
   keeps faith with the pack's own no-fabrication / provenance invariants even in a UI-first
   detour: the one real layer we touch gets logged in `data/SOURCES.md` with a URL and access
   date, same as every other layer would.
3. **Local preview only.** No deployment this round. Verify via the in-app Browser tool.
4. **UI element scope**, informed by 2026 trend research (sources in prior chat turn):
   - Bento grid for the 12-constraint method section — current default pattern, not overused.
   - Glassmorphism as an accent (nav bar, a few cards) — restrained, not the whole surface.
   - Kinetic type / scroll reveals on the **hero headline and section transitions only** —
     real teams don't animate body copy because it fights screen readers, SEO, and Core Web
     Vitals.
   - Magnetic buttons + custom cursor on the landing page's primary CTA — landing-only, off
     in the atlas view (professional-tool cursor stays default there).
   - Floating theme toggle: fixed position, sun/moon morph animation, its own elevation/shadow
     so it doesn't disappear against either theme's background.

## Architecture

Single Next.js (App Router, TypeScript) app in `web/`, matching the pack's own scaffold
(`DRAVYAVATI_ATLAS_claude_code_pack.md` §3 lists `web/` as the Next.js + MapLibre target).

```
web/
├── app/
│   ├── layout.tsx          # ThemeProvider + floating ThemeToggle mounted once, global fonts
│   ├── page.tsx            # landing (bold mode)
│   └── atlas/
│       └── page.tsx        # atlas shell (sober mode)
├── components/
│   ├── theme-toggle.tsx    # floating sun/moon morph toggle (motion + next-themes)
│   ├── landing/
│   │   ├── hero.tsx
│   │   ├── bento-features.tsx
│   │   ├── magnetic-button.tsx
│   │   └── custom-cursor.tsx
│   └── atlas/
│       ├── map-shell.tsx        # MapLibre GL wrapper
│       ├── sample-data-banner.tsx
│       ├── legend-panel.tsx
│       └── sensitivity-slider.tsx  # inert placeholder, wired up in pack Session 7
├── lib/
│   └── smooth-scroll.ts    # Lenis setup
└── public/
    └── data/
        └── dravyavati-river.geojson   # real OSM geometry, cited in data/SOURCES.md
```

Root-level (outside `web/`, shared with the eventual Python backend):
```
data/
└── SOURCES.md   # provenance ledger — records the OSM river fetch now
```

Each component is self-contained: `ThemeToggle` doesn't know about the map, `MapShell`
doesn't know about the hero. The two routes only share the theme provider and design tokens.

## Tech stack

- Next.js (App Router) + TypeScript + Tailwind CSS + shadcn/ui primitives
- `motion` (Framer Motion successor) — theme toggle morph, magnetic button, micro-interactions
- GSAP + ScrollTrigger — hero kinetic headline, section-transition reveals only
- Lenis — smooth scroll, landing page only
- `next-themes` — light/dark/system state
- MapLibre GL JS — atlas map rendering

## Data handling & provenance

A one-time Overpass API query fetches the Dravyavati river way(s)/relation in Jaipur and
saves the result as a static GeoJSON asset at build time (not a live runtime call — avoids
Overpass rate-limit flakiness in the deployed app). The fetch's query, source URL, and access
date get appended to `data/SOURCES.md`. The map renders this real line; every constraint score
column is a placeholder and is visually marked as such at all times, never just in a footnote —
consistent with the pack's own "uncertainty is a column, not a footnote" invariant applied to
"this isn't real yet" as the most extreme case of low confidence.

## Accessibility & edge cases

- Respect `prefers-reduced-motion`: kinetic type and scroll-linked animation degrade to a
  simple fade/no-op.
- Theme toggle keyboard-operable, visible focus ring, `aria-label` reflecting current/target
  state.
- Atlas legend and banner are readable without hover — no information conveyed by hover alone,
  given the eventual audience may include reviewers accessing the tool under real scrutiny.
- Mobile breakpoint check on both routes (viewport ≥ 375px).

## Verification

- `npm run dev` in `web/`, load `/` and `/atlas` in the in-app Browser tool.
- Toggle theme on `/`, navigate to `/atlas`, confirm the theme persisted.
- Confirm the atlas map renders the real river line (not a placeholder box) and the sample-data
  banner is visible without scrolling.
- Resize to mobile width, re-check both routes.
- Confirm `data/SOURCES.md` has a row for the OSM river fetch with URL + access date before
  calling this done.
