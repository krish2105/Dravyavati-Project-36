# Data Sources

Every layer used in this atlas is recorded here with a public URL and access date **before**
it is used anywhere else in the repo. See `CLAUDE.md` (once written — Session 1's Python
scaffold is paused, see `docs/superpowers/specs/2026-08-18-dravyavati-atlas-frontend-design.md`)
for the full provenance rule. Practical test: a stranger with no private access should be able
to rebuild every file in this repo from the URLs below.

| Layer | Source | Access | Notes |
|---|---|---|---|
| Dravyavati River / Amanishah Nala channel geometry (21 way segments, `natural=water`+`water=river`, name ~ "Dravyavati\|Amanishah") | OpenStreetMap, via Overpass API (`overpass-api.de/api/interpreter`) | 2026-08-18 | Used in the `/atlas` prototype shell (`web/public/data/dravyavati-river.geojson`) to render the real river channel. This is the *currently-mapped* channel, not the reconstructed 36 km corridor alignment — that reconstruction (Majar Dam to NH-148C Ring Road) is pack §6 Session 2 scope and has not run. © OpenStreetMap contributors, data available under the Open Database License (ODbL). |
