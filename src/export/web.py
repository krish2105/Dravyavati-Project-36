"""parquet -> geojson for the viewer — Session 8.

Reads the Session 7 deliverable (chainage_risk.parquet, EPSG:4326 already)
and writes web/public/data/chainage_risk.geojson for the Next.js viewer.
"""

from pathlib import Path

import geopandas as gpd

REPO_ROOT = Path(__file__).resolve().parents[2]
PARQUET_PATH = REPO_ROOT / "data" / "processed" / "chainage_risk.parquet"
WEB_DATA_DIR = REPO_ROOT / "web" / "public" / "data"


def export_for_web() -> Path:
    gdf = gpd.read_parquet(PARQUET_PATH)
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = WEB_DATA_DIR / "chainage_risk.geojson"
    gdf.to_file(out_path, driver="GeoJSON")
    return out_path


if __name__ == "__main__":
    path = export_for_web()
    print(f"Wrote {path}")
