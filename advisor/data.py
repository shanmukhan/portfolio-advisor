"""Data ingestion layer for Zerodha Portfolio Advisor.

Provides demo data from local CSVs or live data from Zerodha Kite Connect.
"""

import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from .broker import KiteReadOnly, parse_kite_holdings

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'


def demo() -> Tuple[List[Dict[str, Any]], pd.DataFrame, Dict[str, List[float]], bool]:
    """Load cached sample portfolio, fundamental metrics, and synthetic price series.

    Returns:
        Tuple of (holdings, fundamentals_df, prices_dict, is_live_flag=False).
    """
    holdings_path = DATA / 'demo_holdings.csv'
    holdings = pd.read_csv(holdings_path).to_dict('records') if holdings_path.exists() else []

    funds_path = DATA / 'demo_fundamentals.csv'
    funds = pd.read_csv(funds_path) if funds_path.exists() else pd.DataFrame(columns=['symbol'])

    # Collect symbols from holdings, fundamentals, and universe
    all_syms = set(funds.symbol.dropna()) | {h['symbol'] for h in holdings}
    univ_file = DATA / 'universe.csv'
    if univ_file.exists():
        all_syms |= set(pd.read_csv(univ_file).symbol.dropna())

    prices: Dict[str, List[float]] = {}
    for sym in all_syms:
        p = DATA / 'prices' / f'{sym}.csv'
        if p.exists():
            try:
                prices[sym] = pd.read_csv(p)['close'].tolist()
            except Exception as e:
                logger.warning("Error loading price for %s: %s", sym, e)

    return holdings, funds, prices, False


def live() -> Tuple[List[Dict[str, Any]], pd.DataFrame, Dict[str, List[float]], bool]:
    """Fetch live holdings and price history via Zerodha Kite Connect.

    Falls back to local demo/cache if session is expired or unavailable.

    Returns:
        Tuple of (holdings, fundamentals_df, prices_dict, is_live_flag).
    """
    try:
        broker = KiteReadOnly()
        raw = broker.holdings()
        holdings = parse_kite_holdings(raw)
    except Exception as exc:
        logger.warning(
            "Kite Connect session expired or unavailable (%s). Falling back to cached data.",
            exc,
        )
        h_demo, f_demo, p_demo, _ = demo()
        return h_demo, f_demo, p_demo, False

    # Fallback to demo_fundamentals if fundamentals.csv is not present
    funds_path = DATA / 'fundamentals.csv'
    if not funds_path.exists():
        funds_path = DATA / 'demo_fundamentals.csv'
    funds = pd.read_csv(funds_path) if funds_path.exists() else pd.DataFrame(columns=['symbol'])

    # Explicit curated universe; never scan all NSE instruments without rate limiting
    univ_path = DATA / 'universe.csv'
    universe = (
        pd.read_csv(univ_path).symbol.dropna().astype(str).tolist()
        if univ_path.exists()
        else []
    )
    symbols = sorted(set(universe + [h['symbol'] for h in holdings]))

    instruments = {
        x['tradingsymbol']: x['instrument_token']
        for x in broker.instruments()
        if x.get('segment') == 'NSE'
    }
    end = date.today()
    start = end - timedelta(days=550)

    import time
    prices: Dict[str, List[float]] = {}
    for sym in symbols:
        token = instruments.get(sym)
        if not token:
            # Fallback to cached prices in data/prices if available
            p = DATA / 'prices' / f'{sym}.csv'
            if p.exists():
                try:
                    prices[sym] = pd.read_csv(p)['close'].tolist()
                except Exception as e:
                    logger.warning("Error loading cached price for %s: %s", sym, e)
            continue
        try:
            candles = broker.historical(token, start, end)
            p_list = [c['close'] for c in candles]
            if len(p_list) >= 252:
                prices[sym] = p_list
            else:
                # If broker returned less than required history, fallback to local cache
                p = DATA / 'prices' / f'{sym}.csv'
                if p.exists():
                    prices[sym] = pd.read_csv(p)['close'].tolist()
                elif p_list:
                    prices[sym] = p_list
        except Exception as exc:
            logger.warning("Price history unavailable from broker for %s: %s", sym, exc)
            # Fallback to local price file if present
            p = DATA / 'prices' / f'{sym}.csv'
            if p.exists():
                try:
                    prices[sym] = pd.read_csv(p)['close'].tolist()
                except Exception as e:
                    logger.warning("Error loading fallback price for %s: %s", sym, e)
        time.sleep(0.38)

    return holdings, funds, prices, True


def check_fundamentals_staleness(days_threshold: int = 90) -> Optional[str]:
    """Check if the active fundamentals CSV file has not been modified in > days_threshold days.

    Args:
        days_threshold: Maximum acceptable data age in days (default 90).

    Returns:
        Staleness warning message string if outdated, else None.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo
    ist = ZoneInfo('Asia/Kolkata')

    funds_path = DATA / 'fundamentals.csv'
    if not funds_path.exists():
        funds_path = DATA / 'demo_fundamentals.csv'
    if not funds_path.exists():
        return "No fundamental data CSV found in data directory."

    mtime = datetime.fromtimestamp(funds_path.stat().st_mtime, tz=ist)
    age_days = (datetime.now(ist) - mtime).days
    if age_days > days_threshold:
        return (
            f"Fundamental metrics are {age_days} days old (last updated: {mtime.strftime('%Y-%m-%d')}). "
            f"Multiples (P/E, ROE) should be refreshed with recent quarterly filings."
        )
    return None
