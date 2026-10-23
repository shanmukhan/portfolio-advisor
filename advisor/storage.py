import sqlite3
import json
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo('Asia/Kolkata')

def connect(path):
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

def add_purchase(db, date, symbol, gross_amount, source='manual', unique_key=None):
    if gross_amount < 0:
        raise ValueError('Purchase amount cannot be negative')
    db.execute(
        'INSERT OR IGNORE INTO purchases(trade_date, symbol, gross_amount, source, unique_key) VALUES(?,?,?,?,?)',
        (date, symbol.strip().upper(), float(gross_amount), source, unique_key)
    )
    db.commit()

def get_purchases(db, month=None):
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

def delete_purchase(db, purchase_id):
    db.execute('DELETE FROM purchases WHERE id=?', (purchase_id,))
    db.commit()

def monthly_spend(db, date=None):
    date = date or datetime.now(IST).date().isoformat()
    month = date[:7]
    res = db.execute('SELECT COALESCE(SUM(gross_amount), 0) FROM purchases WHERE substr(trade_date,1,7)=?', (month,)).fetchone()[0]
    return float(res)

def save_report(db, date, report):
    db.execute('INSERT OR REPLACE INTO reports VALUES(?,?)', (date, json.dumps(report, default=str)))
    db.commit()

def get_latest_report(db):
    row = db.execute('SELECT report_json FROM reports ORDER BY run_date DESC LIMIT 1').fetchone()
    if row:
        return json.loads(row[0])
    return None

def save_custom_holdings(db, holdings_list):
    now = datetime.now(IST).isoformat()
    db.execute('DELETE FROM custom_holdings')
    for h in holdings_list:
        db.execute(
            'INSERT OR REPLACE INTO custom_holdings(symbol, quantity, average_price, price, sector, updated_at) VALUES(?,?,?,?,?,?)',
            (h['symbol'].upper(), float(h['quantity']), float(h.get('average_price') or h.get('price', 0)), float(h.get('price', 0)), h.get('sector', 'Unknown'), now)
        )
    db.commit()

def get_custom_holdings(db):
    cur = db.execute('SELECT symbol, quantity, average_price, price, sector FROM custom_holdings')
    rows = cur.fetchall()
    return [dict(r) for r in rows]

def clear_custom_holdings(db):
    db.execute('DELETE FROM custom_holdings')
    db.commit()
