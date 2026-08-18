"""Copernicus GLO-30 DEM ingest — Session 6 (constraint 12: hydraulic sensitivity).

Fetched directly from the public AWS Open Data bucket (no auth, no API key)
rather than OpenTopography, which requires a key. Tile naming is
`Copernicus_DSM_COG_10_N{lat}_00_E{lon}_00_DEM` — the `_10_` is Copernicus's
own product-type code, not the resolution (this bucket is the 30m/GLO-30
product despite that code; verified by content, see data/SOURCES.md).
"""

from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"

DEM_BUCKET = "https://copernicus-dem-30m.s3.amazonaws.com"


def _tile_name(lat_deg: int, lon_deg: int) -> str:
    ns = "N" if lat_deg >= 0 else "S"
    ew = "E" if lon_deg >= 0 else "W"
    return f"Copernicus_DSM_COG_10_{ns}{abs(lat_deg):02d}_00_{ew}{abs(lon_deg):03d}_00_DEM"


def fetch_dem_tile(lat_deg: int, lon_deg: int, force: bool = False) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    name = _tile_name(lat_deg, lon_deg)
    out_path = RAW_DIR / f"{name}.tif"
    if out_path.exists() and not force:
        return out_path
    url = f"{DEM_BUCKET}/{name}/{name}.tif"
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    return out_path


def fetch_dem_for_bbox(bbox: tuple[float, float, float, float]) -> list[Path]:
    """bbox = (south, west, north, east) in degrees. Fetches every 1x1 degree
    tile the bbox touches."""
    south, west, north, east = bbox
    import math

    lat_range = range(math.floor(south), math.floor(north) + 1)
    lon_range = range(math.floor(west), math.floor(east) + 1)
    return [fetch_dem_tile(lat, lon) for lat in lat_range for lon in lon_range]


if __name__ == "__main__":
    from src.ingest.osm import CORRIDOR_BBOX

    tiles = fetch_dem_for_bbox(CORRIDOR_BBOX)
    for t in tiles:
        print(f"{t} ({t.stat().st_size / 1e6:.1f} MB)")
