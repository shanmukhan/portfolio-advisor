"""Allowlisted Kite reads only. No order or position mutation methods exposed."""

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def parse_kite_holdings(raw_holdings: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Parse raw Zerodha Kite Connect holdings into standardized portfolio holding dictionaries.

    Filters out positions with non-positive quantities and maps keys to:
    - symbol: uppercase NSE trading symbol
    - quantity: float share count (> 0)
    - average_price: float average purchase price / cost basis
    - price: float latest traded price (LTP)
    - sector: string sector classification ('Unknown' default)

    Args:
        raw_holdings: Iterable of dict-like holding records from Kite Connect.

    Returns:
        List of standardized holding dictionaries.
    """
    if not raw_holdings:
        return []

    parsed: List[Dict[str, Any]] = []
    for r in raw_holdings:
        try:
            qty = float(r.get('quantity', 0))
        except (ValueError, TypeError):
            continue

        if qty <= 0:
            continue

        sym = r.get('tradingsymbol') or r.get('symbol', '')
        if not sym:
            continue

        try:
            avg_p = float(r.get('average_price') or r.get('last_price') or 0.0)
        except (ValueError, TypeError):
            avg_p = 0.0

        try:
            ltp = float(r.get('last_price') or avg_p or 0.0)
        except (ValueError, TypeError):
            ltp = avg_p

        parsed.append({
            'symbol': str(sym).strip().upper(),
            'quantity': qty,
            'average_price': avg_p,
            'price': ltp,
            'sector': r.get('sector', 'Unknown')
        })
    return parsed


class KiteReadOnly:
    """Read-only client wrapper for Zerodha Kite Connect.

    Exposes read endpoints (holdings, profile, instruments, historical, ltp, trades)
    while strictly disallowing any order or fund placement operations.
    """

    def __init__(self, api_key: Optional[str] = None, access_token: Optional[str] = None) -> None:
        try:
            from kiteconnect import KiteConnect
        except ImportError as exc:
            logger.error("kiteconnect package not installed")
            raise RuntimeError(
                "kiteconnect is not installed. Run 'pip install kiteconnect' to use live Kite mode."
            ) from exc

        key = api_key or os.getenv('KITE_API_KEY', '')
        token = access_token or os.getenv('KITE_ACCESS_TOKEN', '')
        if not key or not token:
            raise RuntimeError('Set KITE_API_KEY and KITE_ACCESS_TOKEN in .env or via settings')

        self._kite = KiteConnect(api_key=key)
        self._kite.set_access_token(token)

    def holdings(self) -> List[Dict[str, Any]]:
        """Fetch current portfolio holdings from Kite."""
        return self._kite.holdings()

    def profile(self) -> Dict[str, Any]:
        """Fetch user profile information from Kite."""
        return self._kite.profile()

    def instruments(self) -> List[Dict[str, Any]]:
        """Fetch active NSE equity instruments from Kite."""
        return self._kite.instruments('NSE')

    def historical(self, token: int, start: Any, end: Any) -> List[Dict[str, Any]]:
        """Fetch daily historical price candles for an instrument token."""
        return self._kite.historical_data(token, start, end, 'day')

    def ltp(self, keys: List[str]) -> Dict[str, Any]:
        """Fetch last traded prices for instrument keys."""
        return self._kite.ltp(keys)

    def trades(self) -> List[Dict[str, Any]]:
        """Fetch executed trades for the day."""
        return self._kite.trades()
