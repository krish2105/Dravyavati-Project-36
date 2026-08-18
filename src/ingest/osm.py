"""OSM ingest via Overpass API — rail, metro, roads, power, military, water.

Every fetch here is a real network call against the public Overpass API. Raw
responses are cached to data/raw/ (gitignored) so re-running the pipeline
doesn't hammer the public endpoint.
"""

import json
import time
from pathlib import Path

import requests

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"

# Generous bbox covering the full Jaipur metro area the corridor could plausibly
# span: (south, west, north, east).
JAIPUR_BBOX = (26.60, 75.50, 27.15, 76.05)

# Tighter bbox = alignment.geojson's bounds + ~2km margin. Session 4+ layers use
# this instead of JAIPUR_BBOX — much faster, and cuts Overpass rate-limit risk.
CORRIDOR_BBOX = (26.7298, 75.7362, 26.9774, 75.9701)


def _looks_valid(data: dict) -> bool:
    # A healthy mirror stamps an ISO timestamp here. A stale/broken mirror (seen
    # from third-party mirrors outside the two listed above) returns a bare
    # integer instead and silently reports zero elements for everything.
    stamp = data.get("osm3s", {}).get("timestamp_osm_base", "")
    return bool(stamp) and stamp[:1].isdigit() and "-" in stamp


def query_overpass(query: str, timeout: int = 60, retries: int = 6) -> dict:
    last_error = None
    for attempt in range(retries):
        for endpoint in OVERPASS_ENDPOINTS:
            try:
                resp = requests.post(endpoint, data={"data": query}, timeout=timeout + 15)
                if resp.status_code == 429:
                    last_error = requests.HTTPError("429 Too Many Requests")
                    continue
                resp.raise_for_status()
                data = resp.json()
                if not _looks_valid(data):
                    last_error = RuntimeError(f"malformed response from {endpoint}")
                    continue
                return data
            except (requests.RequestException, json.JSONDecodeError) as exc:
                last_error = exc
        time.sleep(2 ** attempt * 5)  # 5s, 10s, 20s, 40s
    raise RuntimeError(f"All Overpass endpoints failed after {retries} rounds: {last_error}")


def _cache_path(name: str) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    return RAW_DIR / f"{name}.json"


def fetch_cached(name: str, query: str, force: bool = False) -> dict:
    path = _cache_path(name)
    if path.exists() and not force:
        return json.loads(path.read_text())
    data = query_overpass(query)
    path.write_text(json.dumps(data))
    return data


def fetch_river_water_bodies(bbox: tuple[float, float, float, float] = JAIPUR_BBOX) -> dict:
    """natural=water polygons named Dravyavati/Amanishah — real, cite-able channel geometry."""
    south, west, north, east = bbox
    query = f"""
    [out:json][timeout:60];
    (
      way["natural"="water"]["name"~"Dravyavati|Amanishah",i]({south},{west},{north},{east});
    );
    out geom;
    """
    return fetch_cached("osm_dravyavati_river_raw", query)


def fetch_ring_road(bbox: tuple[float, float, float, float] = JAIPUR_BBOX) -> dict:
    """NH-148C / Jaipur Outer Ring Road — used to find the real river crossing (southern endpoint)."""
    south, west, north, east = bbox
    query = f"""
    [out:json][timeout:60];
    (
      way["highway"]["ref"~"NH.?148C",i]({south},{west},{north},{east});
      way["highway"]["name"~"Ring Road",i]({south},{west},{north},{east});
    );
    out geom;
    """
    return fetch_cached("osm_ringroad_raw", query)


def fetch_interface_layers(bbox: tuple[float, float, float, float] = CORRIDOR_BBOX) -> dict:
    """Constraints 01-05, 08-09 in a single Overpass request (rail, metro, bridges,
    major arterials, military, power lines, dams/weirs). One request instead of
    seven — Overpass's public endpoints rate-limit aggressively per-IP, and this
    project already leans on them heavily elsewhere in the pipeline."""
    south, west, north, east = bbox
    query = f"""
    [out:json][timeout:90];
    (
      way["railway"="rail"]({south},{west},{north},{east});
      way["railway"~"subway|light_rail"]({south},{west},{north},{east});
      way["highway"]["bridge"="yes"]({south},{west},{north},{east});
      way["highway"]["layer"~"^[1-9]"]({south},{west},{north},{east});
      way["highway"~"^(trunk|primary|secondary)$"]({south},{west},{north},{east});
      way["landuse"="military"]({south},{west},{north},{east});
      relation["landuse"="military"]({south},{west},{north},{east});
      way["power"="line"]({south},{west},{north},{east});
      node["waterway"~"^(dam|weir)$"]({south},{west},{north},{east});
      way["waterway"~"^(dam|weir)$"]({south},{west},{north},{east});
    );
    out geom;
    """
    return fetch_cached("osm_interface_layers_raw", query)


if __name__ == "__main__":
    river = fetch_river_water_bodies()
    ring = fetch_ring_road()
    print(f"river elements: {len(river['elements'])}, ring road elements: {len(ring['elements'])}")
    interfaces = fetch_interface_layers()
    print(f"interface layers (rail/metro/bridges/arterials/military/power/dams): {len(interfaces['elements'])} elements")
