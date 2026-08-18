# Dravyavati Corridor Constraint Atlas

> Screening-grade, not design-grade. Built on open data for constraint triage. All findings require verification against field survey.

A chainage-indexed geospatial constraint register for a proposed ~36 km elevated corridor
following the Dravyavati River through Jaipur, Rajasthan. Independent open-data analysis —
not affiliated with any consultancy or government body.

## What this is

Every 100 m along the proposed corridor, twelve categories of engineering constraint
(railway/metro/road crossings, restricted areas, curve severity, land availability,
habitation proximity, hydraulic sensitivity, and more) are scored 0–3 and paired with a
confidence rating. Built entirely on publicly-reconstructible open data — see
[`data/SOURCES.md`](data/SOURCES.md) for every source and access date.

## What this is not

A design document, a hydraulic analysis, a structural assessment, or an alignment
recommendation. It does not substitute for topographical survey, GPR utility mapping, or
geotechnical investigation.

## Repository layout

- `src/` — the Python pipeline (ingest → geo → scoring → export), see [`CLAUDE.md`](CLAUDE.md)
  for the hard invariants every module follows.
- `data/` — `SOURCES.md` (the provenance ledger), `raw/`/`interim/` (gitignored),
  `processed/` (committed outputs, including the deliverable `chainage_risk.parquet`).
- `web/` — the Next.js + MapLibre GL viewer.
- `tests/` — projection and chainage integrity checks.

## Build plan

Eight sessions, each with its own verification check, documented in
[`DRAVYAVATI_ATLAS_claude_code_pack.md`](DRAVYAVATI_ATLAS_claude_code_pack.md).
