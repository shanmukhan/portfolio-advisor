from datetime import datetime
from zoneinfo import ZoneInfo
from .analysis import assess
from .portfolio import plan
from .storage import connect, monthly_spend, save_report, get_custom_holdings
from .config import Settings
from .data import demo, live

IST = ZoneInfo('Asia/Kolkata')

def run(settings=None, save=True, custom_holdings=None):
    settings = settings or Settings()
    if settings.mode not in ('demo', 'live'):
        raise ValueError('ADVISOR_MODE must be demo or live')
    
    db = connect(settings.db)
    
    # 1. Determine holdings & market data source
    holdings_raw, funds, prices, is_live = (live() if settings.mode == 'live' else demo())
    
    # Use custom holdings if provided explicitly or saved in database
    if custom_holdings is not None:
        holdings_source = custom_holdings
    else:
        db_custom = get_custom_holdings(db)
        if db_custom and len(db_custom) > 0:
            holdings_source = db_custom
        else:
            holdings_source = holdings_raw

    # Build fund lookup
    funds_by_sym = {}
    if 'symbol' in funds:
        for _, row in funds.iterrows():
            funds_by_sym[str(row['symbol']).upper()] = row

    # 2. Enrich holdings with latest prices, sectors, and P&L calculations
    holdings = []
    for h in holdings_source:
        sym = str(h['symbol']).upper()
        qty = float(h.get('quantity', 0))
        if qty <= 0:
            continue
            
        fund_row = funds_by_sym.get(sym)
        sector = h.get('sector')
        if not sector or sector == 'Unknown':
            sector = str(fund_row['sector']) if fund_row is not None and 'sector' in fund_row else 'Unknown'
            
        # Get latest market price from price series or holding record
        if sym in prices and len(prices[sym]) > 0:
            market_price = float(prices[sym][-1])
        else:
            market_price = float(h.get('price') or h.get('average_price') or 0.0)
            
        avg_price = float(h.get('average_price') or h.get('price') or market_price)
        
        market_val = round(qty * market_price, 2)
        invested_val = round(qty * avg_price, 2)
        pnl = round(market_val - invested_val, 2)
        pnl_pct = round((market_val / invested_val - 1.0) * 100.0, 2) if invested_val > 0 else 0.0
        
        holdings.append({
            'symbol': sym,
            'quantity': qty,
            'average_price': avg_price,
            'price': market_price,
            'market_value': market_val,
            'invested_value': invested_val,
            'unrealized_pnl': pnl,
            'pnl_percent': pnl_pct,
            'sector': sector
        })

    # Total portfolio values
    total_market_value = sum(h['market_value'] for h in holdings)
    total_invested_value = sum(h['invested_value'] for h in holdings)
    total_pnl = round(total_market_value - total_invested_value, 2)
    total_pnl_pct = round((total_market_value / total_invested_value - 1.0) * 100.0, 2) if total_invested_value > 0 else 0.0

    # Add weights to holdings
    for h in holdings:
        h['weight'] = round((h['market_value'] / total_market_value * 100.0), 2) if total_market_value > 0 else 0.0

    # 3. Assess all symbols (holdings + universe)
    holdings_symbols = {h['symbol'] for h in holdings}
    all_symbols = sorted(set(prices) | holdings_symbols | set(funds_by_sym.keys()))
    
    results = []
    holding_lookup = {h['symbol']: h for h in holdings}

    for sym in all_symbols:
        fund_row = funds_by_sym.get(sym)
        sym_prices = prices.get(sym, [])
        result = assess(sym, sym_prices, fund_row)
        
        # Sector resolution
        if fund_row is not None and 'sector' in fund_row:
            result['sector'] = str(fund_row['sector'])
        elif sym in holding_lookup:
            result['sector'] = holding_lookup[sym].get('sector', 'Unknown')
        else:
            result['sector'] = 'Unknown'
            
        result['owned'] = sym in holdings_symbols
        if result['owned']:
            h_info = holding_lookup[sym]
            result['quantity_owned'] = h_info['quantity']
            result['average_price'] = h_info['average_price']
            result['market_value'] = h_info['market_value']
            result['unrealized_pnl'] = h_info['unrealized_pnl']
            result['pnl_percent'] = h_info['pnl_percent']
            result['weight'] = h_info['weight']
            # update holding with recommendation signal
            h_info['signal'] = result['signal']
            h_info['action'] = result['action']
            h_info['action_label'] = result.get('action_label', result['signal'])
            h_info['score'] = result.get('score')
        else:
            result['quantity_owned'] = 0
            result['market_value'] = 0.0
            result['unrealized_pnl'] = 0.0
            result['pnl_percent'] = 0.0
            result['weight'] = 0.0
            
        results.append(result)

    # 4. Portfolio Summary & Health Diagnostics
    owned_recs = [r for r in results if r['owned']]
    buy_count = sum(1 for r in owned_recs if r['action'] == 'BUY')
    hold_count = sum(1 for r in owned_recs if r['action'] == 'HOLD')
    sell_count = sum(1 for r in owned_recs if r['action'] == 'SELL')
    review_count = sum(1 for r in owned_recs if r['action'] == 'REVIEW')

    # Sector Breakdown
    sector_values = {}
    for h in holdings:
        sec = h['sector']
        sector_values[sec] = sector_values.get(sec, 0.0) + h['market_value']
        
    sector_breakdown = []
    for sec, val in sorted(sector_values.items(), key=lambda x: x[1], reverse=True):
        pct = round((val / total_market_value * 100.0), 2) if total_market_value > 0 else 0.0
        sector_breakdown.append({
            'sector': sec,
            'market_value': round(val, 2),
            'weight_percent': pct,
            'exceeds_limit': pct > (settings.max_sector_weight * 100.0)
        })

    # Weighted Quality & Valuation Multiples
    weighted_score = 0.0
    weighted_pe = 0.0
    weighted_roe = 0.0
    valid_weight = 0.0
    for r in owned_recs:
        w = r['weight']
        if r.get('score') is not None:
            weighted_score += r['score'] * w
            valid_weight += w
        f = r.get('fundamentals', {})
        if f.get('ready'):
            weighted_pe += f.get('pe', 0) * (w / 100.0)
            weighted_roe += f.get('roe', 0) * (w / 100.0)
            
    avg_quality_score = round(weighted_score / valid_weight, 1) if valid_weight > 0 else 0.0

    # Concentration and risk warnings
    concentration_warnings = []
    for h in holdings:
        if h['weight'] > (settings.max_stock_weight * 100.0):
            concentration_warnings.append(f"Stock concentration alert: {h['symbol']} represents {h['weight']:.1f}% of portfolio (max guideline: {settings.max_stock_weight*100:.0f}%).")
            
    for s_info in sector_breakdown:
        if s_info['exceeds_limit']:
            concentration_warnings.append(f"Sector concentration alert: {s_info['sector']} represents {s_info['weight_percent']:.1f}% of portfolio (max guideline: {settings.max_sector_weight*100:.0f}%).")

    today = datetime.now(IST).date().isoformat()
    spent = monthly_spend(db, today)
    proposal = plan(results, holdings, spent, settings.monthly_limit, settings.max_stock_weight, settings.max_sector_weight)

    portfolio_summary = {
        'total_market_value': total_market_value,
        'total_invested_value': total_invested_value,
        'total_unrealized_pnl': total_pnl,
        'total_pnl_percent': total_pnl_pct,
        'holdings_count': len(holdings),
        'buy_count': buy_count,
        'hold_count': hold_count,
        'sell_count': sell_count,
        'review_count': review_count,
        'sector_breakdown': sector_breakdown,
        'average_quality_score': avg_quality_score,
        'weighted_pe': round(weighted_pe, 1),
        'weighted_roe': round(weighted_roe, 1),
        'concentration_warnings': concentration_warnings
    }

    warnings = [
        'Recommendations are research hypotheses, not financial advice. No orders can be placed.',
        'Live purchase ledger must be reconciled manually; a zero ledger does NOT mean zero real purchases.',
        'Fundamental CSV values must be independently sourced, timestamped, and reviewed.'
    ] + concentration_warnings

    report = {
        'as_of': today,
        'mode': settings.mode,
        'live': is_live,
        'holdings': holdings,
        'recommendations': results,
        'budget': proposal,
        'portfolio_summary': portfolio_summary,
        'warnings': warnings
    }

    if save:
        save_report(db, today, report)
    db.close()
    return report
