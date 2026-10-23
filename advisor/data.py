from pathlib import Path
import pandas as pd
from datetime import date, timedelta
from .broker import KiteReadOnly

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'

def demo():
    holdings = pd.read_csv(DATA / 'demo_holdings.csv').to_dict('records')
    funds_path = DATA / 'demo_fundamentals.csv'
    funds = pd.read_csv(funds_path) if funds_path.exists() else pd.DataFrame(columns=['symbol'])
    
    # Collect symbols from holdings, fundamentals, and universe
    all_syms = set(funds.symbol.dropna()) | {h['symbol'] for h in holdings}
    univ_file = DATA / 'universe.csv'
    if univ_file.exists():
        all_syms |= set(pd.read_csv(univ_file).symbol.dropna())

    prices = {}
    for sym in all_syms:
        p = DATA / 'prices' / f'{sym}.csv'
        if p.exists():
            try:
                prices[sym] = pd.read_csv(p)['close'].tolist()
            except Exception as e:
                print(f"Error loading price for {sym}: {e}")
                
    return holdings, funds, prices, False

def live():
    try:
        broker = KiteReadOnly()
        raw = broker.holdings()
        
        # In live Zerodha Kite holdings, average_price is cost, last_price is LTP
        holdings = [
            {
                'symbol': r['tradingsymbol'],
                'quantity': r['quantity'],
                'average_price': float(r.get('average_price') or r.get('last_price') or 0.0),
                'price': float(r.get('last_price') or r.get('average_price') or 0.0),
                'sector': 'Unknown'
            }
            for r in raw if r.get('quantity', 0) > 0
        ]
    except Exception as exc:
        print(f"Kite Connect session expired or unavailable ({exc}). Falling back to cached data.")
        h_demo, f_demo, p_demo, _ = demo()
        return h_demo, f_demo, p_demo, False
    
    # Fallback to demo_fundamentals if fundamentals.csv is not present
    funds_path = DATA / 'fundamentals.csv'
    if not funds_path.exists():
        funds_path = DATA / 'demo_fundamentals.csv'
    funds = pd.read_csv(funds_path) if funds_path.exists() else pd.DataFrame(columns=['symbol'])
    
    # Explicit curated universe; never scan all NSE instruments without rate limiting
    univ_path = DATA / 'universe.csv'
    universe = pd.read_csv(univ_path).symbol.dropna().astype(str).tolist() if univ_path.exists() else []
    symbols = sorted(set(universe + [h['symbol'] for h in holdings]))
    
    instruments = {x['tradingsymbol']: x['instrument_token'] for x in broker.instruments() if x.get('segment') == 'NSE'}
    end = date.today()
    start = end - timedelta(days=550)
    
    import time
    prices = {}
    for sym in symbols:
        token = instruments.get(sym)
        if not token:
            # Fallback to cached prices in data/prices if available
            p = DATA / 'prices' / f'{sym}.csv'
            if p.exists():
                prices[sym] = pd.read_csv(p)['close'].tolist()
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
            print(f'Price history unavailable for {sym}: {exc}')
            # fallback to local price file if present
            p = DATA / 'prices' / f'{sym}.csv'
            if p.exists():
                prices[sym] = pd.read_csv(p)['close'].tolist()
        time.sleep(0.38)
        
    return holdings, funds, prices, True
