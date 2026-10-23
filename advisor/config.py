import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv(override=True)

@dataclass(frozen=True)
class Settings:
    mode: str = None
    db: str = None
    monthly_limit: float = 50000.0
    max_stock_weight: float = 0.10
    max_sector_weight: float = 0.25
    min_history_days: int = 252
    buy_threshold: float = 80
    review_threshold: float = 60

    def __post_init__(self):
        if self.mode is None:
            object.__setattr__(self, 'mode', os.getenv('ADVISOR_MODE', 'demo'))
        if self.db is None:
            object.__setattr__(self, 'db', os.getenv('ADVISOR_DB', 'advisor.sqlite3'))

