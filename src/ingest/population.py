"""WorldPop population ingest — Session 5 (constraint 11: habitation proximity).

WorldPop's 2020 India population-density GeoTIFF (30 arc-second / ~1km cells,
UN-adjusted) is a small (~18MB), directly downloadable file — no auth needed.
The pack names "WorldPop 100m" as an option; the 100m-resolution product is
tiled per-state/region rather than one national file and is materially
harder to locate a stable direct URL for, so this uses WorldPop's national
1km product instead. Documented here, not silently substituted — see
data/SOURCES.md.
"""

from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"

WORLDPOP_URL = "https://data.worldpop.org/GIS/Population_Density/Global_2000_2020_1km/2020/IND/ind_pd_2020_1km.tif"


def fetch_worldpop_density(force: bool = False) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / "worldpop_ind_pd_2020_1km.tif"
    if out_path.exists() and not force:
        return out_path
    resp = requests.get(WORLDPOP_URL, timeout=120)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    return out_path


if __name__ == "__main__":
    path = fetch_worldpop_density()
    print(f"Wrote {path} ({path.stat().st_size / 1e6:.1f} MB)")
