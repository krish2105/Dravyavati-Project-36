"""Building footprint ingest — Session 5 (constraints 10-11).

Substitutes OSM `building=*` footprints for Google Open Buildings v3 (the
pack's named source in §4). v3's public mirrors are organised into ~13-14 GB
S2-level-4 cells; even the spatially-indexed FlatGeobuf form did not resolve
a bbox-filtered remote read over our corridor within this session's time
budget. See data/SOURCES.md for the full reasoning — this is a documented
deviation, not a silent swap.
"""

from src.ingest.osm import CORRIDOR_BBOX, fetch_cached


def fetch_buildings(bbox: tuple[float, float, float, float] = CORRIDOR_BBOX) -> dict:
    south, west, north, east = bbox
    query = f"""
    [out:json][timeout:120];
    ( way["building"]({south},{west},{north},{east}); );
    out geom;
    """
    return fetch_cached("osm_buildings_raw", query)


if __name__ == "__main__":
    data = fetch_buildings()
    print(f"buildings: {len(data['elements'])} elements")
