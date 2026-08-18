import geopandas as gpd
import pytest
from shapely.geometry import Point

from src.geo.validation import CRSError, require_working_crs


@require_working_crs
def _dummy_analysis(gdf):
    return len(gdf)


def test_analysis_function_requires_working_crs():
    valid = gpd.GeoDataFrame(geometry=[Point(0, 0)], crs="EPSG:32643")
    assert _dummy_analysis(valid) == 1

    invalid = gpd.GeoDataFrame(geometry=[Point(0, 0)], crs="EPSG:4326")
    with pytest.raises(CRSError):
        _dummy_analysis(invalid)
