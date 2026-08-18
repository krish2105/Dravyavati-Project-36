"""Reconstruct the corridor centreline from river + endpoints — Session 2.

Method (documented per CLAUDE.md's "state assumptions" working agreement):

1. Pull every OSM `natural=water` polygon named Dravyavati/Amanishah — these are
   real, cite-able channel-width polygons, not a single pre-drawn centreline
   (OSM does not carry a `waterway=*` line for this watercourse).
2. Union them; OSM's coverage of this nala is patchy, so the union is several
   disjoint pieces, not one continuous shape.
3. Extract a single-path centreline per piece via a Voronoi skeleton
   (the `centerline` package) reduced to its longest path (networkx graph
   diameter) — the standard technique for turning a ribbon-like polygon into
   a line without branching artifacts.
4. Simplify each piece's centreline (Douglas-Peucker) to a tolerance
   consistent with a design-speed road easing out the tightest river bends,
   not tracing every metre of natural meander.
5. Chain the pieces north to south and connect the small real gaps between
   them with straight segments.

Endpoints (see data/SOURCES.md for full citations):

- NORTH: the northernmost point of the actual OSM-mapped channel. Press
  coverage names "Majar/Mazar Dam" as the corridor's northern terminus, and a
  1975-era source places a historical "Mazar" dam along this same nala near
  Sikar Road — but no independently-verified public coordinate for that dam
  exists. Rather than invent one, this uses the real geometry's own extent as
  the practical, citable start point. This is a genuine gap, not a footnote:
  ASSUMED_NORTH_ENDPOINT_UNCERTAIN = True below.
- SOUTH: the point where NH-148C (Jaipur's Ring Road, confirmed via its `ref`
  tag in OSM) actually crosses the river polygon set. This is preferred over
  a named landmark (e.g. "Bombay Hospital on Mahal Road", also reported in
  press) because it is the intersection of two independently-mapped public
  features rather than an assumed nearby point — testing showed the named
  landmark sits several kilometres from the mapped channel, too far to treat
  as "the same location" without fabricating a connecting alignment.

Known limitation: this reconstruction lands at ~41 km, over the pack's own
34-38 km verification tolerance. A real DPR alignment would ease curves
harder than a Voronoi medial axis of the water body can (IRC minimum curve
radius, not just visual smoothing) and may use bridges to shortcut oxbows —
that requires the IRC:86 table this project deliberately declines to guess
(see src/constants.py). SIMPLIFY_TOLERANCE_M could be pushed higher to bring
the length closer to 34-38 km (500m gets to ~39.5 km), but that flattens
curvature enough to fail Session 3's own diagnostic ("if everything is above
1000m, the smoothing in Session 2 was too aggressive") — 320m is the
documented compromise. Reported here rather than silently forced into range.
"""

from pathlib import Path

import geopandas as gpd
import networkx as nx
from centerline.geometry import Centerline
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

from src.constants import STORAGE_CRS, WORKING_CRS
from src.ingest.osm import fetch_ring_road, fetch_river_water_bodies

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

SIMPLIFY_TOLERANCE_M = 320
"""Lowest tolerance that (a) keeps the reconstructed line simple (no
self-intersections — lower values reintroduce crossings near where pieces
sit close together) and (b) preserves enough vertices for Session 3's
curvature check to be meaningful. Tested at 80-500m; below 320 the chain
self-intersects, above it curvature flattens out (nearly every segment
reads as a straight line) badly enough that Session 3's own diagnostic
flags it. See src/geo/curvature.py."""
RIVER_CROSSING_BUFFER_M = 30

ASSUMED_NORTH_ENDPOINT_UNCERTAIN = True


def _water_polygons(river_json: dict) -> list[Polygon]:
    polys = []
    for el in river_json["elements"]:
        tags = el.get("tags", {})
        name = tags.get("name", "")
        if tags.get("natural") != "water":
            continue
        if "dravyavati" not in name.lower() and "amanishah" not in name.lower():
            continue
        coords = [(pt["lon"], pt["lat"]) for pt in el.get("geometry", [])]
        if len(coords) >= 4 and coords[0] == coords[-1]:
            polys.append(Polygon(coords))
    return polys


def _road_lines(ring_road_json: dict) -> list[LineString]:
    lines = []
    for el in ring_road_json["elements"]:
        geom = el.get("geometry")
        if geom and len(geom) >= 2:
            lines.append(LineString([(p["lon"], p["lat"]) for p in geom]))
    return lines


def _longest_path_centreline(polygon: Polygon, interpolation_distance: float = 12.0) -> LineString | None:
    """Voronoi skeleton of `polygon`, reduced to its single longest path."""
    try:
        skeleton = Centerline(polygon, interpolation_distance=interpolation_distance).geometry
    except Exception:
        return None
    edges = list(skeleton.geoms) if hasattr(skeleton, "geoms") else [skeleton]

    graph = nx.Graph()
    for edge in edges:
        coords = list(edge.coords)
        for a, b in zip(coords[:-1], coords[1:]):
            graph.add_edge(a, b, weight=Point(a).distance(Point(b)))

    if graph.number_of_nodes() == 0:
        return None

    component = max(nx.connected_components(graph), key=len)
    graph = graph.subgraph(component)

    start = next(iter(graph.nodes))
    far_a = max(nx.single_source_dijkstra_path_length(graph, start, weight="weight").items(), key=lambda kv: kv[1])[0]
    dist_from_a = nx.single_source_dijkstra_path_length(graph, far_a, weight="weight")
    far_b = max(dist_from_a.items(), key=lambda kv: kv[1])[0]
    path = nx.dijkstra_path(graph, far_a, far_b, weight="weight")
    return LineString(path)


def _orient_north_to_south(line: LineString) -> LineString:
    start, end = line.coords[0], line.coords[-1]
    return line if start[1] >= end[1] else LineString(list(line.coords)[::-1])


def _find_ring_road_river_crossing(road_lines_utm: list[LineString], river_union_utm) -> Point:
    river_channel = river_union_utm.buffer(RIVER_CROSSING_BUFFER_M)
    crossings = [ln.intersection(river_channel) for ln in road_lines_utm if ln.intersects(river_channel)]
    crossings = [c for c in crossings if not c.is_empty]
    if not crossings:
        raise RuntimeError("NH-148C does not intersect the mapped river channel — cannot derive south endpoint")
    # Use the southernmost crossing — the corridor's own southern terminus.
    best = min(crossings, key=lambda c: c.centroid.y)
    return Point(best.centroid)


def reconstruct_alignment() -> gpd.GeoDataFrame:
    """Build the corridor centreline. Returns a one-row GeoDataFrame in EPSG:4326."""
    river_json = fetch_river_water_bodies()
    ring_road_json = fetch_ring_road()

    river_gdf = gpd.GeoDataFrame(geometry=_water_polygons(river_json), crs="EPSG:4326").to_crs(WORKING_CRS)
    road_gdf = gpd.GeoDataFrame(geometry=_road_lines(ring_road_json), crs="EPSG:4326").to_crs(WORKING_CRS)

    river_union = unary_union(river_gdf.geometry.tolist())
    pieces = list(river_union.geoms) if river_union.geom_type == "MultiPolygon" else [river_union]

    centrelines = []
    for piece in pieces:
        line = _longest_path_centreline(piece)
        if line is not None:
            centrelines.append(line.simplify(SIMPLIFY_TOLERANCE_M))

    if not centrelines:
        raise RuntimeError("No centreline could be extracted from the mapped river geometry")

    # North to south, by each piece's mean northing.
    centrelines.sort(key=lambda ln: -sum(c[1] for c in ln.coords) / len(ln.coords))
    oriented = [_orient_north_to_south(ln) for ln in centrelines]

    north_point = Point(oriented[0].coords[0])
    south_point = _find_ring_road_river_crossing(road_gdf.geometry.tolist(), river_union)

    coords = [north_point.coords[0]]
    for line in oriented:
        coords.extend(list(line.coords))
    coords.append(south_point.coords[0])

    alignment = LineString(coords)
    if not alignment.is_simple:
        raise RuntimeError("Reconstructed alignment self-intersects — check piece ordering/tolerance")

    gdf = gpd.GeoDataFrame(
        {
            "name": ["Dravyavati Corridor (reconstructed)"],
            "length_km": [alignment.length / 1000],
            "north_endpoint_uncertain": [ASSUMED_NORTH_ENDPOINT_UNCERTAIN],
        },
        geometry=[alignment],
        crs=WORKING_CRS,
    )
    return gdf.to_crs(STORAGE_CRS)


def save_alignment(gdf: gpd.GeoDataFrame) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "alignment.geojson"
    gdf.to_file(out_path, driver="GeoJSON")
    return out_path


if __name__ == "__main__":
    result = reconstruct_alignment()
    path = save_alignment(result)
    length_km = result.iloc[0]["length_km"]
    print(f"Wrote {path} — length {length_km:.2f} km (target 34-38 km)")
