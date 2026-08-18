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

IRC_86_2018_MIN_RADIUS_M: dict[int, dict[str, int]] = {
    # Table 8.2, IRC:86-2018 §8.3 — see data/SOURCES.md for the citation.
    # Do not edit these values without updating the table's page reference.
    20: {"se_7pct": 15, "se_4pct": 20},
    30: {"se_7pct": 30, "se_4pct": 40},
    40: {"se_7pct": 60, "se_4pct": 70},
    50: {"se_7pct": 90, "se_4pct": 105},
    60: {"se_7pct": 130, "se_4pct": 150},
    70: {"se_7pct": 175, "se_4pct": 200},
    80: {"se_7pct": 230, "se_4pct": 265},
}
"""Minimum horizontal curve radius by design speed (km/h). The pack scopes
this project's speed band at 60-80 km/h urban. The 4% super-elevation column
is used (see doc §8.2.1: "on urban sections with frequent intersections, it
will be desirable to limit the super elevation to 4 per cent")."""
