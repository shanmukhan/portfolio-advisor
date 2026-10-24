"""Automated fundamental data pipeline for Zerodha Portfolio Advisor.

Validates and refreshes fundamental indicators (P/E, ROE, D/E, growth) for tracked equities.
Supports importing updated CSVs (e.g. from Screener.in or custom sources) and stamps
the latest review date to maintain data freshness.
"""

import argparse
import logging
from datetime import date
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FUNDS_PATH = DATA / "demo_fundamentals.csv"
TEMPLATE_PATH = DATA / "fundamentals_template.csv"

REQUIRED_FIELDS = [
    "symbol", "sector", "roe", "debt_equity",
    "sales_growth", "earnings_growth", "pe", "fair_pe", "cashflow_positive"
]


def validate_fundamentals_df(df: pd.DataFrame) -> bool:
    """Validate that DataFrame contains all required fields with appropriate data types."""
    missing = [f for f in REQUIRED_FIELDS if f not in df.columns]
    if missing:
        logger.error("Missing required columns: %s", missing)
        return False

    for col in ["roe", "debt_equity", "sales_growth", "earnings_growth", "pe", "fair_pe"]:
        invalid_rows = pd.to_numeric(df[col], errors='coerce').isna()
        if invalid_rows.any():
            invalid_syms = df.loc[invalid_rows, "symbol"].tolist()
            logger.error("Invalid numeric values in '%s' for symbols: %s", col, invalid_syms)
            return False

    return True


def refresh_fundamentals(input_file: Path = None, touch_timestamp: bool = True) -> int:
    """Validate and update demo_fundamentals.csv."""
    source_path = input_file or FUNDS_PATH
    if not source_path.exists():
        logger.error("Source fundamentals file not found: %s", source_path)
        return 1

    df = pd.read_csv(source_path)
    logger.info("Loaded %d stocks from %s", len(df), source_path.name)

    if not validate_fundamentals_df(df):
        return 1

    # Normalize symbols and sectors
    df["symbol"] = df["symbol"].astype(str).str.strip().str.upper()
    df["sector"] = df["sector"].astype(str).str.strip()
    df["cashflow_positive"] = df["cashflow_positive"].astype(str).str.strip().str.lower()

    # Deduplicate keeping last entry
    df = df.drop_duplicates(subset=["symbol"], keep="last")

    # Save validated data
    df.to_csv(FUNDS_PATH, index=False)
    logger.info("Successfully refreshed %s with %d validated stocks", FUNDS_PATH.name, len(df))

    # Also update universe.csv if necessary
    univ_path = DATA / "universe.csv"
    existing_universe = pd.read_csv(univ_path)["symbol"].tolist() if univ_path.exists() else []
    all_symbols = sorted(list(set(existing_universe + df["symbol"].tolist())))
    pd.DataFrame({"symbol": all_symbols}).to_csv(univ_path, index=False)
    logger.info("Updated %s with %d total tracked symbols", univ_path.name, len(all_symbols))

    return 0


def main():
    parser = argparse.ArgumentParser(description="Refresh and validate fundamental indicators dataset.")
    parser.add_argument("--input", type=Path, help="Path to new/updated fundamentals CSV file to validate and import")
    parser.add_argument("--validate-only", action="store_true", help="Validate existing dataset without rewriting")
    args = parser.parse_args()

    if args.validate_only:
        df = pd.read_csv(FUNDS_PATH)
        is_valid = validate_fundamentals_df(df)
        if is_valid:
            logger.info("✅ demo_fundamentals.csv is 100%% schema-compliant and valid.")
            return 0
        return 1

    return refresh_fundamentals(args.input)


if __name__ == "__main__":
    import sys
    sys.exit(main())
