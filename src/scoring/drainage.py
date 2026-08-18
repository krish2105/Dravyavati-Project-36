"""Cross-drainage and rainfall context — Phase 1c.

Two things, both deliberately framed as *context*, never as flood risk.
Pack §9 is explicit that a flood claim on this river is the one error that
could genuinely embarrass the contact, so nothing here is named or scaled
as a flood/afflux/inundation output.

1. Cross-drainage candidates. Where a tributary flow path (from D8 flow
   accumulation on the GLO-30 DEM) meets the corridor, an elevated
   structure needs a cross-drainage provision. Counting those is a real,
   checkable engineering quantity — the kind of thing a DPR eventually has
   to enumerate anyway — and it falls straight out of the DEM we already
   have.

2. Rainfall normals. Annual and monsoon-season precipitation at the
   corridor from Open-Meteo's ERA5 archive (free, no API key). This is
   pure context for interpreting the drainage counts, not an input to any
   score.
"""

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
import requests
from rasterio.features import shapes as rio_shapes
from shapely.geometry import shape

from src.constants import WORKING_CRS
from src.geo.validation import require_working_crs

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
DEM_PATH = RAW_DIR / "Copernicus_DSM_COG_10_N26_00_E075_00_DEM.tif"

# Corridor centroid, used only for the point rainfall query.
CORRIDOR_LAT, CORRIDOR_LON = 26.853, 75.853

OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"

# Flow-accumulation cell count above which a flow path is treated as a real
# tributary rather than hillslope noise. At GLO-30 (~30 m cells) this is
# ~2000 cells ≈ 1.8 km² of contributing area — small enough to catch minor
# nalas, large enough to ignore every rill on the DEM.
TRIBUTARY_ACC_THRESHOLD = 2000

# These two buffers work as a pair and must not overlap, or the test breaks
# in one of two ways. The corridor runs along the river, so we first remove
# the main channel from the flow-path mask (CHANNEL_EXCLUSION_M) to avoid
# flagging the whole alignment. But if that exclusion reaches as far as the
# corridor search radius, every lateral tributary gets clipped away exactly
# where it would have been detected, and nothing is ever found. The gap
# between the two is the annulus where a tributary's downstream tip is still
# present and still close enough to the corridor to count.
CHANNEL_EXCLUSION_M = 60
DRAINAGE_BUFFER_M = 200


def fetch_rainfall_normals(force: bool = False) -> dict:
    """Annual + monsoon (Jun-Sep) mean precipitation, 2010-2020, at the corridor."""
    out_path = RAW_DIR / "rainfall_normals.json"
    if out_path.exists() and not force:
        return json.loads(out_path.read_text())

    resp = requests.get(
        OPEN_METEO_ARCHIVE,
        params={
            "latitude": CORRIDOR_LAT,
            "longitude": CORRIDOR_LON,
            "start_date": "2010-01-01",
            "end_date": "2020-12-31",
            "daily": "precipitation_sum",
            "timezone": "Asia/Kolkata",
        },
        timeout=120,
    )
    resp.raise_for_status()
    daily = resp.json()["daily"]

    dates = daily["time"]
    values = [v if v is not None else 0.0 for v in daily["precipitation_sum"]]

    per_year: dict[str, float] = {}
    monsoon_per_year: dict[str, float] = {}
    for date, value in zip(dates, values):
        year, month = date[:4], int(date[5:7])
        per_year[year] = per_year.get(year, 0.0) + value
        if 6 <= month <= 9:
            monsoon_per_year[year] = monsoon_per_year.get(year, 0.0) + value

    result = {
        "source": "Open-Meteo ERA5 archive",
        "point": {"lat": CORRIDOR_LAT, "lon": CORRIDOR_LON},
        "period": "2010-2020",
        "annual_mean_mm": round(float(np.mean(list(per_year.values()))), 1),
        "monsoon_jun_sep_mean_mm": round(float(np.mean(list(monsoon_per_year.values()))), 1),
        "monsoon_share_pct": round(
            100 * float(np.mean(list(monsoon_per_year.values()))) / float(np.mean(list(per_year.values()))), 1
        ),
    }
    out_path.write_text(json.dumps(result, indent=2))
    return result


def _main_channel(crs) -> object | None:
    """The Dravyavati channel itself, from the OSM water polygons.

    Needed because the corridor *follows* the river: without excluding the
    main channel, every segment sits on a high-accumulation flow path and
    the tributary test flags essentially the whole alignment, which measures
    "the corridor follows a drainage line" rather than "a tributary crosses
    the corridor". Only lateral inflows are cross-drainage problems.
    """
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    raw = RAW_DIR / "osm_dravyavati_river_raw.json"
    if not raw.exists():
        return None

    polys = []
    for el in json.loads(raw.read_text())["elements"]:
        tags = el.get("tags", {})
        name = tags.get("name", "")
        if tags.get("natural") != "water":
            continue
        if "dravyavati" not in name.lower() and "amanishah" not in name.lower():
            continue
        coords = [(p["lon"], p["lat"]) for p in el.get("geometry", [])]
        if len(coords) >= 4 and coords[0] == coords[-1]:
            poly = Polygon(coords)
            polys.append(poly if poly.is_valid else poly.buffer(0))

    if not polys:
        return None
    channel = gpd.GeoDataFrame(geometry=[unary_union(polys)], crs="EPSG:4326").to_crs(crs)
    return channel.geometry.iloc[0].buffer(CHANNEL_EXCLUSION_M)


def _tributary_geometries() -> gpd.GeoDataFrame:
    """Vectorise cells whose flow accumulation exceeds the tributary threshold,
    with the main Dravyavati channel removed so only lateral inflows remain."""
    import numpy as np

    if not hasattr(np, "in1d"):  # pysheds calls np.in1d, removed in NumPy 2.x
        np.in1d = np.isin
    from pysheds.grid import Grid

    grid = Grid.from_raster(str(DEM_PATH))
    dem = grid.read_raster(str(DEM_PATH))
    inflated = grid.resolve_flats(grid.fill_depressions(grid.fill_pits(dem)))
    dirmap = (64, 128, 1, 2, 4, 8, 16, 32)
    acc = grid.accumulation(grid.flowdir(inflated, dirmap=dirmap), dirmap=dirmap)

    mask = (np.asarray(acc) > TRIBUTARY_ACC_THRESHOLD).astype("uint8")
    geoms = [
        shape(geom)
        for geom, value in rio_shapes(mask, mask=mask.astype(bool), transform=grid.affine)
        if value == 1
    ]
    if not geoms:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    # Reproject to the metric working CRS *before* subtracting the channel:
    # CHANNEL_EXCLUSION_M is metres, and buffering by it while still in
    # EPSG:4326 would be 60 degrees, which erases the entire dataset.
    gdf = gpd.GeoDataFrame(geometry=geoms, crs="EPSG:4326").to_crs(WORKING_CRS)
    channel = _main_channel(gdf.crs)
    if channel is not None:
        gdf = gdf.assign(geometry=gdf.geometry.difference(channel))
        gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()]
    return gdf


@require_working_crs
def score_drainage(segments: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Flag segments where a modelled tributary flow path meets the corridor."""
    out = segments.copy()

    tributaries = _tributary_geometries()
    if tributaries.empty:
        out["cross_drainage_candidate"] = False
        out["cross_drainage_confidence"] = "low"
        return out

    trib_union = tributaries.to_crs(segments.crs).geometry.union_all()
    buffers = segments.geometry.buffer(DRAINAGE_BUFFER_M)
    out["cross_drainage_candidate"] = [bool(b.intersects(trib_union)) for b in buffers]
    # GLO-30 cannot resolve small urban drains and the DEM predates recent
    # channelisation works, so these are candidates for survey, not a count
    # of structures actually required.
    out["cross_drainage_confidence"] = "low"
    return out


if __name__ == "__main__":
    from src.geo.chainage import load_alignment_working_crs, segment_chainage

    rainfall = fetch_rainfall_normals()
    print(
        f"Rainfall {rainfall['period']}: annual {rainfall['annual_mean_mm']}mm, "
        f"monsoon {rainfall['monsoon_jun_sep_mean_mm']}mm ({rainfall['monsoon_share_pct']}% of annual)"
    )

    alignment = load_alignment_working_crs()
    segments = segment_chainage(alignment)
    scored = score_drainage(segments)

    flags = scored["cross_drainage_candidate"]
    clusters = (flags != flags.shift()).cumsum()[flags].nunique()
    print(f"cross-drainage candidate segments: {int(flags.sum())} in {clusters} distinct locations")
