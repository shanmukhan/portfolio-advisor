"""Configuration settings and environment variable bindings for Portfolio Advisor."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv(override=True)


@dataclass(frozen=True)
class Settings:
    """Immutable application settings with environment variable defaults.

    Attributes:
        mode: Operational mode ('demo' or 'live'). Defaults to ADVISOR_MODE env var or 'demo'.
        db: SQLite database file path. Defaults to ADVISOR_DB env var or 'advisor.sqlite3'.
        monthly_limit: Monthly capital deployment ceiling in INR. Defaults to 50,000.
        max_stock_weight: Maximum portfolio allocation cap for any single stock (0.0 to 1.0).
        max_sector_weight: Maximum portfolio allocation cap for any single sector (0.0 to 1.0).
        min_history_days: Minimum daily price bars required to evaluate technical trend.
        buy_threshold: Composite score threshold (0-100) required for a BUY recommendation.
        review_threshold: Minimum composite score required to avoid an UNDERPERFORMER sell flag.
    """

    mode: Optional[str] = None
    db: Optional[str] = None
    monthly_limit: float = 50000.0
    max_stock_weight: float = 0.10
    max_sector_weight: float = 0.25
    min_history_days: int = 252
    buy_threshold: float = 80.0
    review_threshold: float = 60.0

    def __post_init__(self) -> None:
        """Resolve environment variable defaults for mode and db."""
        if self.mode is None:
            object.__setattr__(self, 'mode', os.getenv('ADVISOR_MODE', 'demo'))
        if self.db is None:
            object.__setattr__(self, 'db', os.getenv('ADVISOR_DB', 'advisor.sqlite3'))
