"""Detailed metro interface per chainage — Phase 1a.

Replaces Session 4's single boolean "does the corridor cross a metro line"
flag with a status-aware one. That distinction is the whole point: an
operational line is a fixed constraint to design around, a line under
construction is a *coordination* problem with another live project, and a
proposed line is a planning risk that may still move.

Status is read from OSM's own tagging:
  railway=subway|light_rail  -> operational
  railway=construction       -> under construction
  railway=proposed           -> proposed

Stations get their own, wider buffer: an interface near a station box is
materially harder than one over plain running tunnel/viaduct.
"""

from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, Point

from src.constants import WORKING_CRS
from src.geo.validation import require_working_crs
from src.ingest.osm import fetch_cached

REPO_ROOT = Path(__file__).resolve().parents[2]

LINE_BUFFER_M = 200
STATION_BUFFER_M = 350

STATUS_SCORE = {"operational": 3, "construction": 3, "proposed": 2}


def fetch_metro_detail(bbox: tuple[float, float, float, float] = (26.70, 75.60, 27.05, 76.05)) -> dict:
    south, west, north, east = bbox
    query = f"""
    [out:json][timeout:90];
    (
      way["railway"~"^(subway|light_rail|construction|proposed)$"]({south},{west},{north},{east});
      node["railway"="station"]["station"~"subway|light_rail"]({south},{west},{north},{east});
      node["public_transport"="station"]["subway"="yes"]({south},{west},{north},{east});
      relation["route"~"^(subway|light_rail)$"]({south},{west},{north},{east});
    );
    out geom;
    """
    return fetch_cached("osm_metro_detail_raw", query)


def _status_of(tags: dict) -> str | None:
    railway = tags.get("railway")
    if railway in {"subway", "light_rail"}:
        return "operational"
    if railway == "construction":
        # construction:railway tells us what it's becoming
        target = tags.get("construction") or tags.get("construction:railway") or ""
        return "construction" if target in {"subway", "light_rail", ""} else None
    if railway == "proposed":
        target = tags.get("proposed") or tags.get("proposed:railway") or ""
        return "proposed" if target in {"subway", "light_rail", ""} else None
    return None


def _metro_layers(data: dict) -> tuple[dict[str, gpd.GeoDataFrame], gpd.GeoDataFrame]:
    by_status: dict[str, list] = {"operational": [], "construction": [], "proposed": []}
    stations = []

    for el in data["elements"]:
        tags = el.get("tags", {})
        if el["type"] == "node" and "lat" in el:
            if tags.get("railway") == "station" or tags.get("public_transport") == "station":
                stations.append(Point(el["lon"], el["lat"]))
            continue
        if el["type"] != "way" or not el.get("geometry"):
            continue
        status = _status_of(tags)
        if status is None:
            continue
        coords = [(p["lon"], p["lat"]) for p in el["geometry"]]
        if len(coords) >= 2:
            by_status[status].append(LineString(coords))

    gdfs = {
        status: gpd.GeoDataFrame(geometry=geoms, crs="EPSG:4326").to_crs(WORKING_CRS)
        if geoms
        else gpd.GeoDataFrame(geometry=[], crs=f"EPSG:{WORKING_CRS}")
        for status, geoms in by_status.items()
    }
    station_gdf = (
        gpd.GeoDataFrame(geometry=stations, crs="EPSG:4326").to_crs(WORKING_CRS)
        if stations
        else gpd.GeoDataFrame(geometry=[], crs=f"EPSG:{WORKING_CRS}")
    )
    return gdfs, station_gdf


@require_working_crs
def score_metro_detail(segments: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    data = fetch_metro_detail()
    layers, stations = _metro_layers(data)

    out = segments.copy()
    line_buffers = segments.geometry.buffer(LINE_BUFFER_M)
    station_buffers = segments.geometry.buffer(STATION_BUFFER_M)

    scores = [0] * len(segments)
    statuses: list[str] = ["none"] * len(segments)

    for status in ("proposed", "construction", "operational"):  # ascending severity
        gdf = layers[status]
        if gdf.empty:
            continue
        union = gdf.geometry.union_all()
        for i, buf in enumerate(line_buffers):
            if buf.intersects(union):
                scores[i] = max(scores[i], STATUS_SCORE[status])
                statuses[i] = status

    near_station = [False] * len(segments)
    if not stations.empty:
        station_union = stations.geometry.union_all()
        for i, buf in enumerate(station_buffers):
            near_station[i] = bool(buf.intersects(station_union))

    out["metro_interface_score"] = scores
    out["metro_interface_status"] = statuses
    out["metro_near_station"] = near_station
    # Operational/under-construction alignments are well mapped in OSM; the
    # "proposed" tagging is the shakier part, so this is medium not high.
    out["metro_interface_confidence"] = ["high" if s in {"operational", "construction"} else "medium" for s in statuses]
    return out


if __name__ == "__main__":
    from src.geo.chainage import load_alignment_working_crs, segment_chainage

    alignment = load_alignment_working_crs()
    segments = segment_chainage(alignment)
    scored = score_metro_detail(segments)

    print("metro interface status:", scored["metro_interface_status"].value_counts().to_dict())
    print("segments near a metro station:", int(scored["metro_near_station"].sum()))
