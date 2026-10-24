"""Command Line Interface for Zerodha Portfolio Advisor."""

import argparse
import json
import sys
from typing import Optional

from .config import Settings
from .engine import run
from .storage import add_purchase, connect


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="advisor",
        description="Zerodha Long-Term Portfolio Advisor CLI — Read-only guidance and budget tracking",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        title="Commands",
        description="Available commands",
    )

    # Subcommand: report
    report_parser = subparsers.add_parser(
        "report",
        help="Generate full advisory report as formatted JSON",
    )
    report_parser.add_argument(
        "--compact",
        action="store_true",
        help="Output compact single-line JSON instead of indented",
    )

    # Subcommand: record-buy
    buy_parser = subparsers.add_parser(
        "record-buy",
        help="Manually record gross executed purchase for monthly budget tracking",
    )
    buy_parser.add_argument(
        "--date",
        required=True,
        help="Trade date in ISO format (YYYY-MM-DD)",
    )
    buy_parser.add_argument(
        "--symbol",
        required=True,
        help="NSE stock symbol (e.g. INFY, HDFCBANK)",
    )
    buy_parser.add_argument(
        "--amount",
        type=float,
        required=True,
        help="Gross purchase amount in INR",
    )

    return parser.parse_args(args)


def main(args: Optional[list] = None) -> int:
    """Main CLI entrypoint."""
    parsed = parse_args(args)

    if parsed.command == "record-buy":
        try:
            settings = Settings()
            db = connect(settings.db)
            try:
                add_purchase(db, parsed.date, parsed.symbol, parsed.amount)
                print(f"✅ Recorded purchase: ₹{parsed.amount:,.2f} for {parsed.symbol.upper()} on {parsed.date}")
            finally:
                db.close()
            return 0
        except ValueError as val_err:
            print(f"❌ Validation error: {val_err}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"❌ Error recording purchase: {exc}", file=sys.stderr)
            return 1

    # Default to report command
    try:
        report_data = run()
        indent = None if getattr(parsed, "compact", False) else 2
        print(json.dumps(report_data, indent=indent, default=str))
        return 0
    except Exception as exc:
        print(f"❌ Error generating report: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
