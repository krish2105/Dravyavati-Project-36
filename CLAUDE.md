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
