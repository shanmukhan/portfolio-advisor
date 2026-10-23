import csv
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import date, timedelta

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PRICES = DATA / "prices"
PRICES.mkdir(parents=True, exist_ok=True)

# 1. Update data/demo_fundamentals.csv with 100% Real Indian Stocks
fundamentals_data = [
    # User's actual portfolio holdings
    {"symbol": "BEL", "sector": "Defense", "roe": 26.5, "debt_equity": 0.0, "sales_growth": 15.2, "earnings_growth": 28.4, "pe": 42.0, "fair_pe": 38.0, "cashflow_positive": "true"},
    {"symbol": "EXIDEIND", "sector": "Industrials", "roe": 11.5, "debt_equity": 0.12, "sales_growth": 11.8, "earnings_growth": 14.0, "pe": 32.0, "fair_pe": 28.0, "cashflow_positive": "true"},
    {"symbol": "GOLDCASE", "sector": "Commodities", "roe": 15.0, "debt_equity": 0.0, "sales_growth": 10.0, "earnings_growth": 10.0, "pe": 18.0, "fair_pe": 18.0, "cashflow_positive": "true"},
    {"symbol": "HDFCBANK", "sector": "Banking", "roe": 16.8, "debt_equity": 6.80, "sales_growth": 18.5, "earnings_growth": 17.2, "pe": 18.2, "fair_pe": 22.5, "cashflow_positive": "true"},
    {"symbol": "MAZDOCK", "sector": "Defense", "roe": 34.2, "debt_equity": 0.0, "sales_growth": 22.5, "earnings_growth": 44.8, "pe": 34.5, "fair_pe": 36.0, "cashflow_positive": "true"},
    {"symbol": "NTPC", "sector": "Energy", "roe": 13.8, "debt_equity": 1.45, "sales_growth": 8.5, "earnings_growth": 12.2, "pe": 16.5, "fair_pe": 17.0, "cashflow_positive": "true"},
    {"symbol": "ONGC", "sector": "Energy", "roe": 14.2, "debt_equity": 0.45, "sales_growth": 9.2, "earnings_growth": 11.5, "pe": 7.5, "fair_pe": 9.0, "cashflow_positive": "true"},
    {"symbol": "SBIN", "sector": "Banking", "roe": 17.5, "debt_equity": 8.50, "sales_growth": 16.2, "earnings_growth": 21.8, "pe": 10.5, "fair_pe": 12.5, "cashflow_positive": "true"},
    {"symbol": "TATACOMM", "sector": "Technology", "roe": 22.4, "debt_equity": 1.65, "sales_growth": 14.2, "earnings_growth": 16.5, "pe": 31.8, "fair_pe": 30.0, "cashflow_positive": "true"},
    {"symbol": "TATASTEEL", "sector": "Metals", "roe": 8.5, "debt_equity": 0.85, "sales_growth": 6.2, "earnings_growth": 7.8, "pe": 24.2, "fair_pe": 18.0, "cashflow_positive": "true"},
    {"symbol": "TMCV", "sector": "Auto", "roe": 20.5, "debt_equity": 0.65, "sales_growth": 15.0, "earnings_growth": 22.5, "pe": 13.8, "fair_pe": 17.0, "cashflow_positive": "true"},
    
    # Real NSE Blue-Chips & Quality Compounders
    {"symbol": "SUNPHARMA", "sector": "Healthcare", "roe": 16.8, "debt_equity": 0.05, "sales_growth": 12.5, "earnings_growth": 16.4, "pe": 35.5, "fair_pe": 38.0, "cashflow_positive": "true"},
    {"symbol": "CIPLA", "sector": "Healthcare", "roe": 15.2, "debt_equity": 0.04, "sales_growth": 10.2, "earnings_growth": 14.0, "pe": 28.0, "fair_pe": 30.0, "cashflow_positive": "true"},
    {"symbol": "INFY", "sector": "Technology", "roe": 31.5, "debt_equity": 0.08, "sales_growth": 10.5, "earnings_growth": 12.8, "pe": 25.4, "fair_pe": 29.0, "cashflow_positive": "true"},
    {"symbol": "TCS", "sector": "Technology", "roe": 48.0, "debt_equity": 0.05, "sales_growth": 9.2, "earnings_growth": 11.4, "pe": 27.8, "fair_pe": 31.0, "cashflow_positive": "true"},
    {"symbol": "HCLTECH", "sector": "Technology", "roe": 23.5, "debt_equity": 0.12, "sales_growth": 9.8, "earnings_growth": 12.5, "pe": 26.5, "fair_pe": 28.0, "cashflow_positive": "true"},
    {"symbol": "WIPRO", "sector": "Technology", "roe": 15.8, "debt_equity": 0.15, "sales_growth": 4.5, "earnings_growth": 6.2, "pe": 22.5, "fair_pe": 24.0, "cashflow_positive": "true"},
    {"symbol": "ICICIBANK", "sector": "Banking", "roe": 18.5, "debt_equity": 6.20, "sales_growth": 21.0, "earnings_growth": 24.5, "pe": 17.5, "fair_pe": 22.0, "cashflow_positive": "true"},
    {"symbol": "RELIANCE", "sector": "Energy", "roe": 10.2, "debt_equity": 0.44, "sales_growth": 11.0, "earnings_growth": 9.8, "pe": 24.8, "fair_pe": 25.5, "cashflow_positive": "true"},
    {"symbol": "ITC", "sector": "Consumer", "roe": 28.5, "debt_equity": 0.01, "sales_growth": 11.2, "earnings_growth": 13.5, "pe": 25.2, "fair_pe": 27.0, "cashflow_positive": "true"},
    {"symbol": "HINDUNILVR", "sector": "Consumer", "roe": 20.4, "debt_equity": 0.02, "sales_growth": 6.5, "earnings_growth": 8.0, "pe": 54.0, "fair_pe": 50.0, "cashflow_positive": "true"},
    {"symbol": "LT", "sector": "Industrials", "roe": 15.8, "debt_equity": 0.88, "sales_growth": 17.5, "earnings_growth": 16.0, "pe": 32.5, "fair_pe": 30.0, "cashflow_positive": "true"},
    {"symbol": "TATAMOTORS", "sector": "Auto", "roe": 22.5, "debt_equity": 0.70, "sales_growth": 19.0, "earnings_growth": 28.0, "pe": 14.5, "fair_pe": 18.5, "cashflow_positive": "true"},
    {"symbol": "TITAN", "sector": "Consumer", "roe": 31.0, "debt_equity": 0.45, "sales_growth": 23.0, "earnings_growth": 20.5, "pe": 82.0, "fair_pe": 65.0, "cashflow_positive": "true"},
    {"symbol": "BHARTIARTL", "sector": "Telecom", "roe": 18.2, "debt_equity": 1.25, "sales_growth": 14.5, "earnings_growth": 22.0, "pe": 42.0, "fair_pe": 45.0, "cashflow_positive": "true"},
    {"symbol": "ASIANPAINT", "sector": "Consumer", "roe": 24.5, "debt_equity": 0.10, "sales_growth": 8.5, "earnings_growth": 11.2, "pe": 52.0, "fair_pe": 55.0, "cashflow_positive": "true"},
    {"symbol": "BAJFINANCE", "sector": "Financial Services", "roe": 21.5, "debt_equity": 3.50, "sales_growth": 26.0, "earnings_growth": 24.0, "pe": 31.0, "fair_pe": 35.0, "cashflow_positive": "true"},
    
    # Real NSE stocks demonstrating Valuation Bubble and Thesis Decay signals
    {"symbol": "NAUKRI", "sector": "Technology", "roe": 6.5, "debt_equity": 0.02, "sales_growth": 12.0, "earnings_growth": 10.0, "pe": 88.0, "fair_pe": 42.0, "cashflow_positive": "true"},
    {"symbol": "YESBANK", "sector": "Banking", "roe": 4.2, "debt_equity": 7.80, "sales_growth": -4.5, "earnings_growth": -18.0, "pe": 38.0, "fair_pe": 16.0, "cashflow_positive": "false"}
]

fund_df = pd.DataFrame(fundamentals_data)
fund_df.to_csv(DATA / "demo_fundamentals.csv", index=False)
print("Updated demo_fundamentals.csv with", len(fund_df), "real Indian stocks")

# 2. Update data/demo_holdings.csv with real Indian stocks
holdings_data = [
    {"symbol": "INFY", "quantity": 30, "price": 1850.0, "average_price": 1520.0, "sector": "Technology"},
    {"symbol": "TCS", "quantity": 15, "price": 4120.0, "average_price": 3650.0, "sector": "Technology"},
    {"symbol": "HDFCBANK", "quantity": 45, "price": 1680.0, "average_price": 1510.0, "sector": "Banking"},
    {"symbol": "RELIANCE", "quantity": 20, "price": 2920.0, "average_price": 2720.0, "sector": "Energy"},
    {"symbol": "ITC", "quantity": 120, "price": 485.0, "average_price": 415.0, "sector": "Consumer"},
    {"symbol": "SUNPHARMA", "quantity": 25, "price": 1820.0, "average_price": 1560.0, "sector": "Healthcare"},
    {"symbol": "TATAMOTORS", "quantity": 35, "price": 980.0, "average_price": 820.0, "sector": "Auto"},
    {"symbol": "LT", "quantity": 12, "price": 3650.0, "average_price": 3200.0, "sector": "Industrials"},
    {"symbol": "ICICIBANK", "quantity": 40, "price": 1260.0, "average_price": 1080.0, "sector": "Banking"},
    {"symbol": "BHARTIARTL", "quantity": 30, "price": 1680.0, "average_price": 1420.0, "sector": "Telecom"},
]
holdings_df = pd.DataFrame(holdings_data)
holdings_df.to_csv(DATA / "demo_holdings.csv", index=False)
print("Updated demo_holdings.csv with", len(holdings_df), "real Indian holdings")

# 3. Update data/universe.csv (All Real NSE symbols)
universe_symbols = sorted(list({f["symbol"] for f in fundamentals_data}))
univ_df = pd.DataFrame({"symbol": universe_symbols})
univ_df.to_csv(DATA / "universe.csv", index=False)
print("Updated universe.csv with", len(univ_df), "real NSE symbols")

# 4. Generate price histories for stocks missing in data/prices/
end_date = date(2026, 10, 22)
dates = []
curr = end_date
while len(dates) < 320:
    if curr.weekday() < 5: # Mon-Fri
        dates.append(curr.isoformat())
    curr -= timedelta(days=1)
dates.reverse()

target_prices = {
    "BEL": (372.50, 0.42, 0.018),
    "EXIDEIND": (465.0, 0.22, 0.019),
    "GOLDCASE": (18.40, 0.12, 0.008),
    "HDFCBANK": (1680.0, 0.18, 0.014),
    "MAZDOCK": (4450.0, 0.65, 0.024),
    "NTPC": (388.0, 0.28, 0.016),
    "ONGC": (285.0, 0.25, 0.019),
    "SBIN": (968.30, 0.28, 0.016),
    "TATACOMM": (1880.0, 0.15, 0.018),
    "TATASTEEL": (148.50, 0.12, 0.017),
    "TMCV": (118.0, 0.22, 0.020),
    "SUNPHARMA": (1820.0, 0.28, 0.014),
    "CIPLA": (1540.0, 0.22, 0.013),
    "INFY": (1850.0, 0.25, 0.015),
    "TCS": (4120.0, 0.20, 0.012),
    "HCLTECH": (1780.0, 0.26, 0.015),
    "WIPRO": (480.0, 0.12, 0.016),
    "ICICIBANK": (1260.0, 0.28, 0.015),
    "RELIANCE": (2920.0, 0.12, 0.016),
    "ITC": (485.0, 0.18, 0.011),
    "HINDUNILVR": (2540.0, 0.05, 0.013),
    "LT": (3650.0, 0.22, 0.017),
    "TATAMOTORS": (980.0, 0.35, 0.022),
    "TITAN": (3450.0, 0.10, 0.016),
    "BHARTIARTL": (1680.0, 0.32, 0.016),
    "ASIANPAINT": (2920.0, 0.08, 0.015),
    "BAJFINANCE": (7150.0, 0.22, 0.018),
    "NAUKRI": (7450.0, 0.85, 0.032), # Bubble valuation example
    "YESBANK": (19.50, -0.38, 0.026), # Thesis decay example
}

np.random.seed(42)

for sym, (target_last, drift_1y, vol) in target_prices.items():
    p_file = PRICES / f"{sym}.csv"
    n = len(dates)
    daily_drift = drift_1y / 252.0
    returns = np.random.normal(daily_drift, vol, n)
    raw_path = np.exp(np.cumsum(returns))
    scaled_close = target_last * (raw_path / raw_path[-1])
    
    opens = []
    highs = []
    lows = []
    closes = []
    volumes = []
    
    for i in range(n):
        c = float(scaled_close[i])
        spread = c * np.random.uniform(0.005, 0.018)
        o = c + np.random.uniform(-spread*0.5, spread*0.5)
        h = max(o, c) + abs(np.random.normal(0, spread*0.5))
        l = min(o, c) - abs(np.random.normal(0, spread*0.5))
        v = int(np.random.lognormal(12.5, 0.8))
        
        opens.append(round(o, 2))
        highs.append(round(h, 2))
        lows.append(round(l, 2))
        closes.append(round(c, 2))
        volumes.append(max(1000, v))
        
    df_p = pd.DataFrame({
        "date": dates,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes
    })
    df_p.to_csv(p_file, index=False)

print(f"Successfully generated historical price series for all {len(target_prices)} real Indian stocks!")
