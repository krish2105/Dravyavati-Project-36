"""Challenges 01-09: discrete crossings — Session 4.

Each constraint scores a chainage segment 0 (no constraint) or 3 (the
corridor buffer intersects a real feature) — a binary crossing/no-crossing
proxy, since these are all "does the alignment cross X" questions, not
graded severity ones. Confidence follows pack §5's table exactly: OSM power
and military layers are marked low confidence per CLAUDE.md invariant 6.

Constraint 06 (entry-exit feasibility) is partially computed here — the
"distance to nearest arterial" half. The "unbuilt area within 150m" half
needs Google Open Buildings (Session 5) and is left as a TODO column rather
than guessed, per CLAUDE.md invariant 2.
"""

from pathlib import Path

import geopandas as gpd

from src.constants import IRC_86_2018_MIN_RADIUS_M, WORKING_CRS
from src.geo.validation import require_working_crs
from src.ingest.osm import fetch_interface_layers, fetch_river_water_bodies

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

Confidence = str  # "high" | "medium" | "low"

BUFFERS_M = {
    "railway_crossing": 150,
    "metro_interface": 200,
    "existing_elevated_structure": 100,
    "major_arterial_crossing": 50,
    "restricted_military_area": 200,
    "eht_line_crossing": 150,
    "dam_check_structure": 100,
}

CONFIDENCE: dict[str, Confidence] = {
    "railway_crossing": "high",
    "metro_interface": "high",
    "existing_elevated_structure": "high",
    "major_arterial_crossing": "high",
    "restricted_military_area": "low",
    "entry_exit_feasibility": "medium",
    "curve_severity": "high",
    "eht_line_crossing": "low",
    "dam_check_structure": "medium",
}

DESIGN_SPEED_KMH = 60  # lower bound of the pack's 60-80 km/h urban band — conservative


def _elements_to_gdf(elements: list[dict], predicate) -> gpd.GeoDataFrame:
    """Turn matching Overpass elements (nodes or ways with geometry) into a GeoDataFrame."""
    from shapely.geometry import LineString, Point

    geoms = []
    for el in elements:
        if not predicate(el.get("tags", {})):
            continue
        if el["type"] == "node" and "lat" in el:
            geoms.append(Point(el["lon"], el["lat"]))
        elif el["type"] == "way" and el.get("geometry"):
            coords = [(p["lon"], p["lat"]) for p in el["geometry"]]
            if len(coords) >= 2:
                geoms.append(LineString(coords))
    if not geoms:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    return gpd.GeoDataFrame(geometry=geoms, crs="EPSG:4326").to_crs(WORKING_CRS)


@require_working_crs
def _score_by_proximity(segments: gpd.GeoDataFrame, features: gpd.GeoDataFrame, buffer_m: float) -> "list[int]":
    if features.empty:
        return [0] * len(segments)
    feature_union = features.geometry.union_all()
    return [3 if seg.buffer(buffer_m).intersects(feature_union) else 0 for seg in segments.geometry]


def score_interfaces(segments: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Add score/confidence columns for constraints 01-05, 07-09, plus the
    partial constraint 06 distance component."""
    interface_json = fetch_interface_layers()
    elements = interface_json["elements"]

    railways = _elements_to_gdf(elements, lambda t: t.get("railway") == "rail")
    metro = _elements_to_gdf(elements, lambda t: t.get("railway") in {"subway", "light_rail"})
    bridges = _elements_to_gdf(
        elements, lambda t: t.get("bridge") == "yes" or (t.get("layer", "0").lstrip("-").isdigit() and int(t.get("layer", "0")) > 0)
    )
    arterials = _elements_to_gdf(elements, lambda t: t.get("highway") in {"trunk", "primary", "secondary"})
    military = _elements_to_gdf(elements, lambda t: t.get("landuse") == "military")
    power = _elements_to_gdf(elements, lambda t: t.get("power") == "line")
    dams = _elements_to_gdf(elements, lambda t: t.get("waterway") in {"dam", "weir"})

    out = segments.copy()

    out["railway_crossing_score"] = _score_by_proximity(segments, railways, BUFFERS_M["railway_crossing"])
    out["railway_crossing_confidence"] = CONFIDENCE["railway_crossing"]

    out["metro_interface_score"] = _score_by_proximity(segments, metro, BUFFERS_M["metro_interface"])
    out["metro_interface_confidence"] = CONFIDENCE["metro_interface"]

    out["existing_elevated_structure_score"] = _score_by_proximity(segments, bridges, BUFFERS_M["existing_elevated_structure"])
    out["existing_elevated_structure_confidence"] = CONFIDENCE["existing_elevated_structure"]

    out["major_arterial_crossing_score"] = _score_by_proximity(segments, arterials, BUFFERS_M["major_arterial_crossing"])
    out["major_arterial_crossing_confidence"] = CONFIDENCE["major_arterial_crossing"]

    out["restricted_military_area_score"] = _score_by_proximity(segments, military, BUFFERS_M["restricted_military_area"])
    out["restricted_military_area_confidence"] = CONFIDENCE["restricted_military_area"]

    out["eht_line_crossing_score"] = _score_by_proximity(segments, power, BUFFERS_M["eht_line_crossing"])
    out["eht_line_crossing_confidence"] = CONFIDENCE["eht_line_crossing"]

    out["dam_check_structure_score"] = _score_by_proximity(segments, dams, BUFFERS_M["dam_check_structure"])
    out["dam_check_structure_confidence"] = CONFIDENCE["dam_check_structure"]

    # Constraint 07: curve severity vs IRC:86-2018 Table 8.2 (see data/SOURCES.md).
    min_radius = IRC_86_2018_MIN_RADIUS_M[DESIGN_SPEED_KMH]["se_4pct"]
    if "radius_m" in out.columns:
        out["curve_severity_score"] = (out["radius_m"] < min_radius).astype(int) * 3
        out["curve_severity_confidence"] = CONFIDENCE["curve_severity"]
        out["irc86_min_radius_m"] = min_radius
    else:
        out["curve_severity_score"] = None  # TODO: run src/geo/curvature.py first

    # Constraint 06, partial: distance to nearest major arterial. The unbuilt-area
    # half needs Session 5's building footprints — left as an explicit TODO, not guessed.
    if not arterials.empty:
        arterial_union = arterials.geometry.union_all()
        out["entry_exit_distance_to_arterial_m"] = [seg.distance(arterial_union) for seg in segments.geometry]
    else:
        out["entry_exit_distance_to_arterial_m"] = None
    out["entry_exit_feasibility_score"] = None  # TODO(Session 5): combine with unbuilt-area fraction
    out["entry_exit_feasibility_confidence"] = CONFIDENCE["entry_exit_feasibility"]

    return out


def save_interfaces(gdf: gpd.GeoDataFrame) -> Path:
    from src.constants import STORAGE_CRS

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "chainage.geojson"
    gdf.to_crs(STORAGE_CRS).to_file(out_path, driver="GeoJSON")
    return out_path


if __name__ == "__main__":
    from src.geo.chainage import load_alignment_working_crs, segment_chainage
    from src.geo.curvature import compute_curvature

    alignment = load_alignment_working_crs()
    segments = segment_chainage(alignment)
    segments = compute_curvature(alignment, segments)
    scored = score_interfaces(segments)
    path = save_interfaces(scored)

    railway_crossings = (scored["railway_crossing_score"] == 3).sum()
    print(f"Wrote {path} — {railway_crossings} segments with a railway crossing (target: ~2 ± 1)")
