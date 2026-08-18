# DRAVYAVATI CORRIDOR CONSTRAINT ATLAS
## Claude Code Deliverable Pack

**Author:** Krishna Mathur
**Date:** August 2026
**Target:** Screening-grade geospatial constraint register for the proposed 36 km elevated corridor along the Dravyavati River, Jaipur
**Build time:** 8 Claude Code sessions, ~1 week at 3–4 hrs/session
**Machine:** MacBook M4 Pro (all sessions — no GPU needed)

---

## 0. WHAT THIS IS AND IS NOT

**This is:** a chainage-indexed screening tool that flags, every 100 m along a publicly-reconstructed corridor alignment, where twelve categories of engineering constraint are likely to bind. It is built entirely on open data and is reproducible by anyone.

**This is not:** a design document, a hydraulic analysis, a structural assessment, or an alignment recommendation. It does not substitute for topographical survey, GPR utility mapping, or geotechnical investigation.

**Write this sentence on every output, every slide, every README:**

> Screening-grade, not design-grade. Built on open data for constraint triage. All findings require verification against field survey.

Engineers relax when they hear this. It is also true, which is why it works.

---

## 1. THE PROVENANCE RULE (non-negotiable)

Every geometry, every number, every layer in this repo must be traceable to a publicly accessible source, recorded in `data/SOURCES.md` with a URL and access date.

**Reason:** you have seen a non-public consultancy progress deck. Nothing derived from it may enter this repository. The corridor is publicly reconstructible — the river channel is mapped in OpenStreetMap and visible on satellite imagery, and the endpoints (Majar Dam in the north, Mahal Road / NH-148C Ring Road in the south) are stated in press coverage of the project. Reconstruct from those. Do not digitise from the deck's imagery, do not use its chainage labels, do not screenshot it.

**Consequence:** the artifact is publishable on GitHub, safe to show in interviews, and safe to send to JDA without exposing whoever shared the deck with you. If a chainage in your atlas happens to match theirs, that is convergent method, not leaked data — and it is a far stronger demonstration.

**Practical test before every commit:** could a stranger with no access to anything private rebuild this exact file from the URLs in SOURCES.md? If no, the file does not ship.

---

## 2. CLAUDE.md

Create this at repo root. Claude Code reads it every session.

```markdown
# Dravyavati Corridor Constraint Atlas

## What we are building
A chainage-indexed geospatial constraint register for a proposed ~36 km elevated
corridor following the Dravyavati River through Jaipur, Rajasthan. Output is a
single parquet file (chainage_risk.parquet) plus a web map that renders it.

## Hard invariants — never violate

1. PROVENANCE. Every layer traces to a public URL recorded in data/SOURCES.md
   with an access date. No exceptions. If a source cannot be cited, the layer
   does not exist.

2. NO FABRICATED NUMBERS. If a design standard value is needed (curve radii,
   PCU factors, clearance envelopes), do not recall it from memory. Either read
   it from a cited document or leave a TODO with the exact code clause to look
   up. A wrong IRC value is worse than a missing one.

3. PROJECTION. All spatial analysis in EPSG:32643 (WGS84 / UTM zone 43N).
   Store and serve in EPSG:4326. Convert explicitly at boundaries, never
   implicitly. Any distance/area computed in degrees is a bug.

4. SCREENING-GRADE. Every output carries the disclaimer string from
   src/constants.py. This is a triage tool, not a design tool.

5. CHAINAGE IS THE PRIMARY KEY. Everything joins on chainage_m (integer metres
   from corridor start, 100 m increments). One row per segment. If an analysis
   cannot be expressed per-chainage, it does not belong in the atlas.

6. UNCERTAINTY IS A COLUMN, NOT A FOOTNOTE. Every score carries a paired
   confidence value in {high, medium, low} based on source data quality.
   OSM power line coverage in Jaipur is patchy — anything derived from it is
   low confidence and must say so on the map.

## Style
- Python 3.11+, geopandas / shapely / rasterio / pyproj
- Functions over classes. No abstraction until the third repetition.
- Each src/ module runs standalone: `python -m src.geo.chainage`
- Raw data is gitignored. Processed outputs are committed (they are small).
- No notebooks in the pipeline. Notebooks are for looking, src/ is for building.

## Working agreement
- State assumptions before implementing. If two readings of a task exist, say so.
- Define the verification check before writing the code that needs verifying.
- Touch only what the current task requires.
- If a simpler approach exists, propose it before building the complex one.
```

---

## 3. REPO SCAFFOLD

```
dravyavati-atlas/
├── CLAUDE.md
├── README.md                    # screening-grade disclaimer at the top
├── pyproject.toml
├── .gitignore                   # data/raw/, data/interim/, .env
├── data/
│   ├── SOURCES.md               # the provenance ledger — every URL + date
│   ├── raw/                     # gitignored
│   ├── interim/                 # gitignored
│   └── processed/
│       ├── alignment.geojson    # the reconstructed corridor centreline
│       ├── chainage.geojson     # 100 m segments
│       └── chainage_risk.parquet  # THE deliverable
├── src/
│   ├── constants.py             # CRS, disclaimer string, buffer widths, weights
│   ├── ingest/
│   │   ├── osm.py               # roads, rail, metro, power, military, water
│   │   ├── dem.py               # Copernicus GLO-30
│   │   ├── buildings.py         # Google Open Buildings v3
│   │   └── population.py        # WorldPop / Meta HRSL
│   ├── geo/
│   │   ├── alignment.py         # reconstruct centreline from river + endpoints
│   │   ├── chainage.py          # segment into 100 m units
│   │   └── curvature.py         # radius of curvature per segment
│   ├── scoring/
│   │   ├── interfaces.py        # challenges 01–09: discrete crossings
│   │   ├── land.py              # challenges 10–11: land + habitation
│   │   ├── hydraulic.py         # challenge 12: channel geometry screening
│   │   └── composite.py         # roll-up + sensitivity
│   └── export/
│       └── web.py               # parquet -> geojson for the viewer
├── web/                         # Next.js + MapLibre GL, deploy to Vercel
└── tests/
    └── test_geo.py              # projection + chainage integrity
```

---

## 4. DATA SOURCES

Record each in `data/SOURCES.md` with access date on first download.

| Layer | Source | Access | Notes |
|---|---|---|---|
| River channel, roads, rail, metro | OpenStreetMap | `osmnx` / Overpass API | Primary geometry source |
| Building footprints | Google Open Buildings v3 | Public GCS bucket / Earth Engine | Excellent India coverage |
| Elevation | Copernicus DEM GLO-30 | OpenTopography API or AWS Open Data | 30 m — adequate for screening only |
| Population | WorldPop 100 m or Meta HRSL | worldpop.org / HDX | Constrained UN-adjusted 2020+ |
| Land use / built-up change | Sentinel-2 L2A | Copernicus Data Space Ecosystem | For habitation growth since 2018 |
| Indian admin/ward boundaries | Datameet India maps | github.com/datameet | Census 2011 vintage |
| Land use plan | Jaipur Master Plan 2047 | jda.rajasthan.gov.in | PDF — georeference manually |
| Project endpoints & length | Press coverage (PTI/ThePrint, First India, ConstructionWorld) | Web | Cite for alignment reconstruction |
| DPR tender scope | JDA tender portal, Tender ID 6226125001 | jdafa.rajasthan.gov.in | Public ToR — read it fully |

**Known data quality problems, state these on the map:**
- OSM `power=line` coverage in Jaipur is incomplete. EHT crossings flagged from OSM are *candidates*, not confirmed. Cross-check each against satellite imagery for transmission tower shadows before publishing.
- OSM `landuse=military` boundaries are frequently absent or approximate in India. The deck references a military area interface; if OSM does not show one, record that as an acknowledged gap rather than concluding none exists.
- GLO-30 at 30 m cannot resolve a rectified channel cross-section. Hydraulic output is a *relative* screening index only — never an absolute conveyance figure.

---

## 5. THE SCORING MODEL

Twelve constraint categories, each mapped to a computable proxy. Score each 0–3 per 100 m segment (0 = no constraint, 3 = severe).

| # | Constraint | Computable proxy | Source | Confidence |
|---|---|---|---|---|
| 01 | Railway crossing | Alignment ∩ `railway=rail`, ±150 m | OSM | High |
| 02 | Metro interface | Alignment ∩ metro alignment, ±200 m | OSM | High |
| 03 | Existing elevated structure | `bridge=yes` or `layer>0` within 100 m | OSM | High |
| 04 | Major arterial crossing | ∩ `highway` in {trunk, primary, secondary} | OSM | High |
| 05 | Restricted/military area | `landuse=military` ∩ 200 m buffer | OSM | **Low** |
| 06 | Entry–exit feasibility | Distance to nearest arterial × unbuilt area within 150 m | Derived | Medium |
| 07 | Curve severity | Radius of curvature per segment vs. IRC:86 minimum | Geometry | High |
| 08 | EHT line crossing | ∩ `power=line`, tagged voltage ≥ 66 kV | OSM | **Low** |
| 09 | Dam / check structure | `waterway` in {dam, weir} within 100 m | OSM + visual | Medium |
| 10 | Land availability | % of 60 m corridor buffer with zero building footprint | Open Buildings | High |
| 11 | Habitation proximity | Building count + population within 100 m buffer | Open Buildings + WorldPop | High |
| 12 | Hydraulic sensitivity | Channel width × upstream contributing area, normalised | DEM | **Low** |

### Two values you must look up — do not let Claude guess them

1. **IRC:86-2018 minimum horizontal curve radius** for the design speeds in play (60–80 kmph urban). This drives constraint 07 entirely. Get the actual table. The alignment options under consideration differ mainly in speed-band distribution, so this is the number that separates them.
2. **IRC:106 PCU equivalency factors** for Indian urban mixed traffic. Not needed for the Atlas, but needed the moment you touch traffic data. Have it ready.

### Composite score

```
composite = Σ (weight_i × score_i)
```

Ship with equal weights as the default and make weights a config dict, not hardcoded. Then run the sensitivity pass: which chainages change severity band under any plausible reweighting? Those are the *robust* hotspots, and they are the only ones you should mention out loud. A hotspot that only appears under one weighting is an artefact of your assumptions, not a finding.

**This sensitivity output is the single most credible thing in the deliverable.** It demonstrates you know your own model's limits, which is the trait that separates an analyst from someone with a GIS licence.

---

## 6. SESSION PLAN

Each session states its verification check. Do not proceed to the next session until the check passes.

### Session 1 — Scaffold and provenance
Set up repo, `pyproject.toml`, `constants.py`, `.gitignore`, empty `SOURCES.md`. Write `tests/test_geo.py` with one test asserting that any GeoDataFrame passed to an analysis function is in EPSG:32643.
**Verify:** `pytest` passes. Test fails correctly when handed an EPSG:4326 frame.

### Session 2 — Alignment reconstruction
Pull the Dravyavati channel from OSM. Reconstruct a centreline from Majar Dam to the NH-148C Ring Road junction. Smooth to a continuous LineString. Record every source in SOURCES.md.
**Verify:** total length is 34–38 km. Endpoints within 500 m of publicly documented locations. Geometry is a single unbroken LineString with no self-intersections.

### Session 3 — Chainage segmentation and curvature
Segment into 100 m units keyed on `chainage_m`. Compute radius of curvature per segment via three-point circumscribed circle.
**Verify:** segment count ≈ length/100 ± 2. No null radii. Radius distribution is plausible — a river-following alignment should show plenty of sub-500 m radii; if everything is above 1000 m, the smoothing in Session 2 was too aggressive.

### Session 4 — OSM interface layers (constraints 01–09)
Ingest rail, metro, roads, power, military, water structures. Intersect with the corridor buffer. Score each segment.
**Verify:** railway crossings detected = 2 ± 1 (matches publicly reported project description). Every layer has a confidence tag. Power and military layers explicitly marked low confidence.

### Session 5 — Land and habitation (constraints 10–11)
Google Open Buildings within a 200 m corridor buffer. Compute unbuilt fraction within 60 m, building count and population within 100 m.
**Verify:** spot-check five segments against current satellite imagery. Dense-urban segments (Mansarovar, Aatish Market area) must score 3 on habitation; peri-urban southern segments must score 0–1. If that gradient is inverted, the buffer geometry is wrong.

### Session 6 — Hydraulic screening (constraint 12)
GLO-30 DEM. Derive approximate channel width and upstream contributing area per segment. Normalise into a relative sensitivity index.
**Verify:** index increases monotonically downstream (contributing area only grows). Output column is named `hydraulic_sensitivity_index` — never `afflux`, never `flood_risk`. Naming discipline here protects you.

### Session 7 — Composite and sensitivity
Roll up. Run the reweighting sweep. Produce the ranked robust-hotspot list.
**Verify:** `chainage_risk.parquet` has one row per segment, no nulls, every score column paired with a confidence column. Robust hotspot list is 8–20 entries — if it is 100, the model has no discrimination; if it is 2, the weights are degenerate.

### Session 8 — Web viewer
Next.js + MapLibre GL. Corridor coloured by composite score, click-through to per-segment constraint breakdown, layer toggles, sensitivity slider. Disclaimer permanently visible in the header, not buried in an About page. Deploy to Vercel.
**Verify:** loads under 3 s on mobile. Disclaimer visible without scrolling. Every layer has a source attribution in the UI.

---

## 7. WHAT YOU ACTUALLY SEND THEM

Not the repo. Not a GitHub link as the opening move.

**Send:** a two-page PDF plus one live URL.

Page 1: the map, the method in five bullets, the disclaimer, and the sentence *"Built entirely on open data, independently of JDA and Monarch — no project data was used."* That sentence does more work than anything else in the document.

Page 2: the robust hotspot table. Chainage, constraint type, confidence, and one line on why it matters. Nothing else. No recommendations. No alignment opinion. No hydraulic conclusions.

**The ask, at the end, in one sentence:** *"If any of this is useful, I'd value 20 minutes to hear where the method is wrong."*

That framing works because it is not a pitch and it is not a request for data. It invites correction, which engineers find almost impossible to refuse, and correction requires them to tell you what they actually know — which is how you find out whether the alignment is frozen, when the feasibility gate is, and whether there is a sub-consultancy slot, without having asked any of those questions directly.

**Route it through your contact.** Do not cold-email the Technical Director. Ask your contact whether they would be comfortable passing it on, and accept a no.

---

## 8. WHAT COMES AFTER

If the meeting happens, the second build is the Alignment Decision Engine — but now with *their* criteria and *their* weights, which is the only version of it worth building. If they engage further, the third is the Traffic Survey Pipeline, and that is where the budget, the recurring work, and the PRAVAAH unlock all live.

Do not mention builds two and three in the first contact. One artifact, one ask.

---

## 9. FAILURE MODES TO WATCH

- **Scope creep into design.** The moment you find yourself computing span lengths or pier spacing, stop. That is Monarch's job and doing it badly is how you lose the room.
- **Over-claiming on hydraulics.** This river has a documented flood and encroachment history and the rejuvenation project is politically sensitive. A screening index is defensible; a flood claim is not, and it is the one error that could genuinely embarrass your contact.
- **Publishing before the provenance audit.** Run the stranger test on every file before the repo goes public.
- **Building all eight sessions before showing anyone.** After Session 5 you have enough to have a conversation. Consider having it then.
