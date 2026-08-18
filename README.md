# Dravyavati Corridor Constraint Atlas

> **Screening-grade, not design-grade.** Built on open data for constraint triage.
> All findings require verification against field survey.

A chainage-indexed geospatial constraint register for a proposed ~36 km elevated corridor
following the Dravyavati River through Jaipur, Rajasthan. Every 100 m along a
publicly-reconstructed alignment, thirteen categories of engineering constraint are scored
0–3 and paired with a confidence rating.

**Independent open-data analysis — not affiliated with JDA or any consultancy. No project
data was used.**

| | |
|---|---|
| **Live atlas** | https://dravyavati-atlas.vercel.app |
| **Interactive analysis** | https://dravyavati-atlas.vercel.app/analysis |
| **Screening brief (PDF)** | [`web/public/brief/`](web/public/brief/) |
| **Provenance ledger** | [`data/SOURCES.md`](data/SOURCES.md) |

---

## Headline findings

| Metric | Value |
|---|---|
| Corridor reconstructed | 41.2 km, 413 × 100 m segments |
| Constraint categories | 13, each scored 0–3 with a paired confidence tag |
| Robust hotspot corridors | 6 stretches whose severity band survives a ±35% reweighting |
| Railway crossings | 2 distinct |
| Metro interfaces | 6 segments operational · 8 under construction · 25 proposed |
| Cross-drainage candidates | 23 distinct locations |
| Below IRC:86-2018 min radius | 12 segments (150 m minimum, 60 km/h design speed) |
| Corridor buffer unbuilt | 99.5% mean across segments |
| Mean 90% uncertainty interval | 0.40 composite points |

The neural surrogate ranks **proximity to existing elevated structure** as the dominant
driver of the composite (permutation importance 0.41), ahead of entry–exit feasibility and
hydraulic sensitivity. Habitation proximity — the intuitive first guess for an urban
corridor — ranks well below these.

---

## What this is, and is not

**Is:** a triage instrument for deciding where survey effort and design attention should go
first, reproducible end-to-end from public sources with no credentials and no licensed
software.

**Is not:** a design document, a hydraulic analysis, a structural assessment, or an alignment
recommendation. It does not substitute for topographical survey, GPR utility mapping, or
geotechnical investigation.

---

## Method

1. **Alignment** — OSM `natural=water` polygons for the Dravyavati/Amanishah channel are
   unioned and reduced to a centreline via a Voronoi medial axis, taking the longest path
   through the skeleton graph. The southern endpoint is the point where NH-148C actually
   crosses the channel, preferred over a press-named landmark because it is the intersection
   of two independently-mapped public features.
2. **Chainage** — the centreline is cut into 100 m segments keyed on `chainage_m`, the join
   key for every downstream layer.
3. **Curvature** — radius per segment via three-point circumscribed circle, compared against
   IRC:86-2018 Table 8.2 (transcribed from the published standard, not recalled).
4. **Constraint scoring** — thirteen categories from OpenStreetMap, building footprints,
   WorldPop, Copernicus GLO-30 and Sentinel-2.
5. **Composite + sensitivity** — equal-weight composite, then a ±35% sweep of every weight.
   Only chainages whose severity band survives the entire sweep are reported.
6. **ML layer** — Monte Carlo uncertainty, DBSCAN corridor clustering, Isolation Forest
   anomaly detection, and a neural surrogate with permutation importance.

### Design rule for the ML layer

No model here predicts a quantity this repository has no ground truth for. There is no
observed traffic count, no tendered cost and no gauged flood record in this data, so nothing
outputs one. Every method is either **unsupervised** (finds structure already present) or a
**surrogate** that explains the composite the pipeline computed itself. That is what keeps
the output answerable when an engineer asks where a number came from.

---

## Hard invariants

Enforced in code and asserted by the test suite — see [`CLAUDE.md`](CLAUDE.md).

1. **Provenance.** Every layer traces to a public URL in `data/SOURCES.md` with an access
   date. If a source cannot be cited, the layer does not exist.
2. **No fabricated numbers.** Design-standard values are read from cited documents or left
   as an explicit TODO. A wrong IRC value is worse than a missing one.
3. **Projection.** All spatial analysis in EPSG:32643; storage and serving in EPSG:4326.
   Conversions are explicit. Any distance computed in degrees is a bug — and one such bug
   was caught this way during development.
4. **Screening-grade.** Every output carries the disclaimer string.
5. **Chainage is the primary key.** One row per 100 m segment; if an analysis cannot be
   expressed per-chainage, it does not belong here.
6. **Uncertainty is a column, not a footnote.** Every score carries a confidence value, and
   those values drive the Monte Carlo perturbation scale rather than sitting inert.

---

## Where this is weakest

Stated plainly, because these are the parts most likely to be wrong:

- **Power lines and military areas (low confidence)** — OSM coverage for both is incomplete
  in Jaipur. Absence in this analysis is a gap in the source data, not evidence of absence
  on the ground.
- **Built-up growth (low confidence)** — a Sentinel-2 spectral index (NDBI), not a land-cover
  classification. Bare soil here can mimic built-up signal, so only the 2018→2026 *change* is
  scored, never an absolute value.
- **Hydraulic sensitivity (low confidence)** — GLO-30 at 30 m cannot resolve a rectified
  channel cross-section. Relative screening index over contributing area only. Not an afflux
  figure, not a flood claim.
- **Alignment length** — the channel-following reconstruction is 41.2 km against a reported
  ~36 km. This is now quantified rather than left open: applying curve easing reaches
  **36.43 km (within 1.2% of the reported figure)** at the cost of departing the mapped
  channel by up to **875 m** to cut meanders, while improving IRC:86 curvature compliance.
  Both alignments are published; scoring stays on the channel-following one because it
  carries no easing assumptions. See `src/geo/eased_alignment.py`. Chainages still will not
  correspond one-to-one with a DPR's.
- **Land-use zoning is absent** — the approved Zonal Development Plan sheets were obtained,
  but they are ~10,800 × 15,000 px scans with no embedded CRS. Georeferencing them needs
  hand-picked control points, and a mis-registered layer would assign wrong land use to real
  chainages, so no zoning attribute is attached to any chainage. Left undone deliberately.

### Correction to the original brief

The project was scoped against the "Jaipur Master Plan 2047". **That document is not an
approved statutory plan** — it is in preparation, with public reporting indicating a 2027–28
release and an expansion from 18 to 27 planning zones. The plan in force remains **Master
Plan 2025, approved 2011**. The approved Zonal Development Plans were fetched instead. Any
screening work citing a 2047 land-use position today is citing a document that does not yet
exist.

---

## Repository layout

```
src/
  ingest/     osm.py · dem.py · buildings.py · population.py · sentinel.py
  geo/        alignment.py · chainage.py · curvature.py · validation.py
  scoring/    interfaces.py · land.py · hydraulic.py · metro.py · growth.py
              drainage.py · composite.py
  ml/         analysis.py
  export/     web.py · brief.py
data/
  SOURCES.md          provenance ledger — every URL and access date
  raw/                gitignored
  processed/          alignment.geojson · chainage.geojson · chainage_risk.parquet
web/                  Next.js + MapLibre GL viewer
tests/                projection, chainage, scoring and composite integrity
```

---

## Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

```bash
python -m src.scoring.composite   # full pipeline -> chainage_risk.parquet
python -m src.ml.analysis         # ML layer, writes back into the parquet
python -m src.export.web          # web assets
python -m src.export.brief        # the PDF brief
pytest                            # invariant checks
```

```bash
cd web && npm install && npm run dev
```

Each `src/` module also runs standalone (`python -m src.geo.chainage`) for inspecting one
stage in isolation.

---

## Licence and attribution

Analysis code is provided as-is for review. Source data remains under its own licences:
OpenStreetMap © OpenStreetMap contributors (ODbL), Copernicus DEM and Sentinel-2 under
Copernicus terms, WorldPop under CC-BY 4.0. See [`data/SOURCES.md`](data/SOURCES.md).
