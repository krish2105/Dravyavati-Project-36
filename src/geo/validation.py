"""CRS guard for analysis functions — see CLAUDE.md invariant 3.

Any function that does spatial analysis (distance, area, buffering, curvature)
must operate in the working CRS. Wrap it with @require_working_crs so a
mis-projected GeoDataFrame fails loudly instead of producing silently wrong
numbers.
"""

import functools

from src.constants import WORKING_CRS


class CRSError(ValueError):
    """Raised when a GeoDataFrame isn't in the required working CRS."""


def require_working_crs(func):
    @functools.wraps(func)
    def wrapper(gdf, *args, **kwargs):
        crs = getattr(gdf, "crs", None)
        epsg = crs.to_epsg() if crs is not None else None
        if epsg != WORKING_CRS:
            raise CRSError(
                f"{func.__name__} requires EPSG:{WORKING_CRS}, got {crs!r}"
            )
        return func(gdf, *args, **kwargs)

    return wrapper
