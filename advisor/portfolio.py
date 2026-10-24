"""Portfolio rebalancing and monthly SIP allocation planner.

Enforces monthly budget constraints, position sizing limits, and sector concentration caps.
"""

from typing import Any, Dict, List, Optional


def plan(
    recommendations: List[Dict[str, Any]],
    holdings: List[Dict[str, Any]],
    spent: float,
    limit: float = 50000.0,
    max_stock_weight: float = 0.10,
    max_sector_weight: float = 0.25,
    planned: float = 0.0,
) -> Dict[str, Any]:
    """Conservative sizing and allocation planner for both BUYS and SELLS.

    Respects monthly budget limit, single-stock weight limits (default 10%),
    and sector concentration caps (default 25%). Generates prioritized BUY
    allocations and disciplined SELL harvesting recommendations.

    Args:
        recommendations: Evaluated stock recommendations with scores and signals.
        holdings: Current portfolio holding records.
        spent: Gross capital already spent during the current calendar month.
        limit: Configured monthly investment budget ceiling.
        max_stock_weight: Maximum allowed portfolio weight per stock (0.0 - 1.0).
        max_sector_weight: Maximum allowed portfolio weight per sector (0.0 - 1.0).
        planned: Additional committed capital for current cycle.

    Returns:
        Dict containing buy 'allocations', sell 'sells', 'potential_freed_capital',
        'unallocated' cash, and tracking metrics.
    """
    remaining = max(0.0, float(limit) - float(spent) - float(planned))

    # Track holdings values and quantities
    values = {x['symbol']: float(x.get('quantity', 0)) * float(x.get('price', 0)) for x in holdings}
    sectors = {x['symbol']: x.get('sector', 'Unknown') for x in holdings}
    total = sum(values.values())

    # 1. Plan BUY allocations within available monthly budget
    allocations: List[Dict[str, Any]] = []
    for r in sorted(recommendations, key=lambda x: x.get('score') or -1, reverse=True):
        if r.get('signal') not in ('BUY_CANDIDATE', 'BUY') or not r.get('price') or r['price'] <= 0:
            continue
        symbol = r['symbol']
        price = float(r['price'])
        sector = r.get('sector', 'Unknown')
        if sector == 'Unknown':
            continue

        current = values.get(symbol, 0.0)
        sector_value = sum(v for sym, v in values.items() if sectors.get(sym) == sector)

        # Sizing limits based on post-purchase projected base
        projected_base = total + remaining
        stock_headroom = max(0.0, projected_base * max_stock_weight - current)
        sector_headroom = max(0.0, projected_base * max_sector_weight - sector_value)
        target = min(remaining, stock_headroom, sector_headroom, 10000.0)
        qty = int(target // price)
        if qty <= 0:
            continue

        amount = round(qty * price, 2)
        allocations.append({
            'symbol': symbol,
            'quantity': qty,
            'price': price,
            'estimated_gross': amount,
            'reason': r['reason'],
            'action': 'BUY',
            'action_label': r.get('action_label', 'Accumulate'),
            'sector': sector,
            'score': r.get('score'),
        })
        remaining = round(remaining - amount, 2)
        values[symbol] = current + amount
        sectors[symbol] = sector

    # 2. Plan SELL / TRIM recommendations for owned holdings
    sells: List[Dict[str, Any]] = []
    rec_by_sym = {r['symbol']: r for r in recommendations}
    for h in holdings:
        sym = h['symbol']
        r = rec_by_sym.get(sym)
        if not r or r.get('signal') not in ('SELL', 'SELL_CANDIDATE'):
            continue

        qty_held = int(h.get('quantity', 0))
        if qty_held <= 0:
            continue

        price = float(r.get('price') or h.get('price', 0))
        avg_cost = float(h.get('average_price') or h.get('price', 0))
        thesis_status = r.get('thesis_status', 'THESIS_BREAK')

        # If valuation bubble with massive gain: recommend Trim 50% or Exit 100%
        if thesis_status == 'VALUATION_BUBBLE':
            sell_qty = max(1, qty_held // 2) if qty_held > 1 else qty_held
            sell_label = 'Trim 50% / Profit Booking' if sell_qty < qty_held else 'Sell / Profit Booking'
        else:
            sell_qty = qty_held
            sell_label = 'Exit 100% / Thesis Break'

        proceeds = round(sell_qty * price, 2)
        gain_loss = round((price - avg_cost) * sell_qty, 2)
        gain_loss_pct = round(((price / avg_cost) - 1) * 100, 1) if avg_cost > 0 else 0.0

        sells.append({
            'symbol': sym,
            'quantity_held': qty_held,
            'quantity_to_sell': sell_qty,
            'price': price,
            'average_price': avg_cost,
            'estimated_proceeds': proceeds,
            'unrealized_pnl': gain_loss,
            'pnl_percent': gain_loss_pct,
            'action': 'SELL',
            'action_label': sell_label,
            'reason': r['reason'],
            'thesis_status': thesis_status,
            'sector': h.get('sector', r.get('sector', 'Unknown')),
        })

    potential_freed_capital = round(sum(s['estimated_proceeds'] for s in sells), 2)

    return {
        'allocations': allocations,
        'sells': sells,
        'potential_freed_capital': potential_freed_capital,
        'unallocated': remaining,
        'spent': spent,
        'monthly_limit': limit,
        'note': 'Indicative sizes only; actual fills, fees and manual trades must be reconciled.',
    }
