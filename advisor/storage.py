import sqlite3
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

IST = ZoneInfo('Asia/Kolkata')
SYMBOL_REGEX = re.compile(r'^[A-Z0-9&_\.\-]{1,25}$')

def validate_symbol(symbol: str) -> str:
    """Validate and normalize a stock ticker symbol.

    Args:
        symbol: Raw stock ticker symbol (e.g., 'INFY', 'M&M').

    Returns:
        Stripped, uppercase normalized symbol string.

    Raises:
        ValueError: If symbol is empty or contains invalid characters.
    """
    if not isinstance(symbol, str):
        raise ValueError(f"Symbol must be a string, got {type(symbol).__name__}")
    clean = symbol.strip().upper()
    if not clean or not SYMBOL_REGEX.match(clean):
        raise ValueError(
            f"Invalid symbol: '{symbol}'. Must be 1-25 characters containing uppercase alphanumeric, &, _, ., or -."
        )
    return clean

def validate_date(date_str: str) -> str:
    """Validate that date_str is a valid ISO date format (YYYY-MM-DD).

    Args:
        date_str: ISO date string to validate.

    Returns:
        Validated date string.

    Raises:
        ValueError: If format is invalid or date does not exist.
    """
    if not isinstance(date_str, str):
        raise ValueError(f"Date must be a string, got {type(date_str).__name__}")
    clean = date_str.strip()
    try:
        datetime.strptime(clean, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD.")
    return clean

def connect(path: str) -> sqlite3.Connection:
    """Connect to SQLite database and ensure required tables are created.

    Args:
        path: File path to SQLite database.

    Returns:
        Configured sqlite3.Connection instance with sqlite3.Row factory.
    """
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute('''CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_date TEXT NOT NULL,
        symbol TEXT NOT NULL,
        gross_amount REAL NOT NULL CHECK(gross_amount >= 0),
        source TEXT NOT NULL,
        unique_key TEXT UNIQUE
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS reports (
        run_date TEXT PRIMARY KEY,
        report_json TEXT NOT NULL
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS custom_holdings (
        symbol TEXT PRIMARY KEY,
        quantity REAL NOT NULL CHECK(quantity >= 0),
        average_price REAL NOT NULL,
        price REAL,
        sector TEXT,
        updated_at TEXT
    )''')
    db.commit()
    return db

def add_purchase(
    db: sqlite3.Connection,
    date: str,
    symbol: str,
    gross_amount: float,
    source: str = 'manual',
    unique_key: Optional[str] = None
) -> None:
    """Record a purchase transaction in the database.

    Args:
        db: SQLite database connection.
        date: Purchase date in YYYY-MM-DD format.
        symbol: Stock ticker symbol.
        gross_amount: Gross transaction amount in INR (>= 0).
        source: Origin of purchase ('manual', 'zerodha', etc.).
        unique_key: Optional deduplication key.

    Raises:
        ValueError: If validation fails for symbol, date, or amount.
    """
    valid_symbol = validate_symbol(symbol)
    valid_date = validate_date(date)
    if gross_amount < 0:
        raise ValueError('Purchase amount cannot be negative')
    db.execute(
        'INSERT OR IGNORE INTO purchases(trade_date, symbol, gross_amount, source, unique_key) VALUES(?,?,?,?,?)',
        (valid_date, valid_symbol, float(gross_amount), source, unique_key)
    )
    db.commit()

def get_purchases(db: sqlite3.Connection, month: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve purchases, optionally filtered by YYYY-MM month prefix.

    Args:
        db: SQLite database connection.
        month: Optional month string in YYYY-MM format.

    Returns:
        List of purchase dictionaries ordered descending by trade date.
    """
    if month:
        cur = db.execute(
            'SELECT id, trade_date, symbol, gross_amount, source FROM purchases WHERE substr(trade_date,1,7)=? ORDER BY trade_date DESC, id DESC',
            (month,)
        )
    else:
        cur = db.execute(
            'SELECT id, trade_date, symbol, gross_amount, source FROM purchases ORDER BY trade_date DESC, id DESC'
        )
    return [dict(row) for row in cur.fetchall()]

def delete_purchase(db: sqlite3.Connection, purchase_id: int) -> None:
    """Delete a purchase record by ID.

    Args:
        db: SQLite database connection.
        purchase_id: Primary key of purchase to delete.
    """
    db.execute('DELETE FROM purchases WHERE id=?', (purchase_id,))
    db.commit()

def monthly_spend(db: sqlite3.Connection, date: Optional[str] = None) -> float:
    """Calculate cumulative spending for the month of the specified date.

    Args:
        db: SQLite database connection.
        date: Reference date string (YYYY-MM-DD). Defaults to today in IST.

    Returns:
        Total gross spend amount in INR for the month.
    """
    date = date or datetime.now(IST).date().isoformat()
    month = date[:7]
    res = db.execute('SELECT COALESCE(SUM(gross_amount), 0) FROM purchases WHERE substr(trade_date,1,7)=?', (month,)).fetchone()[0]
    return float(res)

def save_report(db: sqlite3.Connection, date: str, report: Dict[str, Any]) -> None:
    """Persist an advisor analysis report JSON for historical lookup.

    Args:
        db: SQLite database connection.
        date: Run date key (YYYY-MM-DD).
        report: Dict containing report data.
    """
    valid_date = validate_date(date)
    db.execute('INSERT OR REPLACE INTO reports VALUES(?,?)', (valid_date, json.dumps(report, default=str)))
    db.commit()

def get_latest_report(db: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    """Fetch the most recently stored advisor report.

    Args:
        db: SQLite database connection.

    Returns:
        Deserialized report dictionary, or None if no reports exist.
    """
    row = db.execute('SELECT report_json FROM reports ORDER BY run_date DESC LIMIT 1').fetchone()
    if row:
        return json.loads(row[0])
    return None

def save_custom_holdings(db: sqlite3.Connection, holdings_list: List[Dict[str, Any]]) -> None:
    """Overwrite custom holdings table with the provided list of positions.

    Args:
        db: SQLite database connection.
        holdings_list: List of position dicts containing symbol, quantity, etc.
    """
    now = datetime.now(IST).isoformat()
    db.execute('DELETE FROM custom_holdings')
    for h in holdings_list:
        clean_sym = validate_symbol(h['symbol'])
        db.execute(
            'INSERT OR REPLACE INTO custom_holdings(symbol, quantity, average_price, price, sector, updated_at) VALUES(?,?,?,?,?,?)',
            (clean_sym, float(h['quantity']), float(h.get('average_price') or h.get('price', 0)), float(h.get('price', 0)), h.get('sector', 'Unknown'), now)
        )
    db.commit()

def get_custom_holdings(db: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Retrieve all current custom holdings.

    Args:
        db: SQLite database connection.

    Returns:
        List of position dictionaries.
    """
    cur = db.execute('SELECT symbol, quantity, average_price, price, sector FROM custom_holdings')
    rows = cur.fetchall()
    return [dict(r) for r in rows]

def clear_custom_holdings(db: sqlite3.Connection) -> None:
    """Delete all records from the custom holdings table.

    Args:
        db: SQLite database connection.
    """
    db.execute('DELETE FROM custom_holdings')
    db.commit()
