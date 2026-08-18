"""Project-wide constants — CRS, disclaimer, and constraint weights.

See CLAUDE.md invariants 3 (projection) and 6 (uncertainty is a column).
"""

WORKING_CRS = 32643
"""EPSG:32643 — WGS84 / UTM zone 43N. All spatial analysis happens here."""

STORAGE_CRS = 4326
"""EPSG:4326 — storage and serving only. Convert explicitly at boundaries."""

DISCLAIMER = (
    "Screening-grade, not design-grade. Built on open data for constraint "
    "triage. All findings require verification against field survey."
)

CONSTRAINT_WEIGHTS: dict[str, float | None] = {
    "railway_crossing": None,
    "metro_interface": None,
    "existing_elevated_structure": None,
    "major_arterial_crossing": None,
    "restricted_military_area": None,
    "entry_exit_feasibility": None,
    "curve_severity": None,
    "eht_line_crossing": None,
    "dam_check_structure": None,
    "land_availability": None,
    "habitation_proximity": None,
    "hydraulic_sensitivity": None,
}
"""Empty by design — Session 7 ships the equal-weight defaults per pack §5."""

CHAINAGE_STEP_M = 100
"""Segment length in metres. chainage_m is the primary key (invariant 5)."""
