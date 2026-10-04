"""Central configuration. Every value can be overridden with an environment variable (see .env.example)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]          # backend/
REPO_ROOT = BASE_DIR.parent                              # skillpulse-india/

# --- Data location -----------------------------------------------------------------------
# The prototype reads local DEMO files. To use real data later, add a source adapter in
# app/services/ingestion.py and point it at the official file / API (see data_sources.json).
DATA_DIR = Path(os.getenv("SKILLPULSE_DATA_DIR") or REPO_ROOT / "data")

# --- Database ----------------------------------------------------------------------------
# Default: SQLite file (zero setup, works on Windows). For PostgreSQL/PostGIS set DATABASE_URL
# to a postgresql+psycopg2:// URL and install sqlalchemy + psycopg2-binary (see app/db.py).
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{(BASE_DIR / 'skillpulse.db').as_posix()}"


def _f(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


class Settings:
    """Configurable thresholds. gap_ratio = (forecast demand - training capacity) / forecast demand."""

    shortage_threshold = _f("SHORTAGE_THRESHOLD", 0.10)    # gap_ratio > this  -> SHORTAGE
    surplus_threshold = _f("SURPLUS_THRESHOLD", -0.10)     # gap_ratio < this  -> SURPLUS
    ew_low_max = _f("EW_LOW_MAX", 0.10)                    # early warning: <= this -> LOW
    ew_growing_max = _f("EW_GROWING_MAX", 0.25)            # <= this -> GROWING, above -> CRITICAL (prototype class)
    capacity_growth_pct = _f("CAPACITY_GROWTH_PCT", 0.0)   # assumed yearly capacity growth in forecast years
    transition_min_fit = _f("TRANSITION_MIN_FIT", 40.0)    # min fit score to count as a transition opportunity
    nearby_radius_km = _f("NEARBY_RADIUS_KM", 300.0)       # search radius for surplus capacity
    min_balancing_seats = _f("MIN_BALANCING_SEATS", 50.0)
    industry_growing_cagr = _f("INDUSTRY_GROWING_CAGR", 0.08)
    industry_declining_cagr = _f("INDUSTRY_DECLINING_CAGR", -0.03)
    forecast_years = (2027, 2028)
    history_years = (2023, 2024, 2025, 2026)
    base_year = 2026


settings = Settings()

DEMO_LABEL = "Prototype/Demo Data — Not official statistics"
