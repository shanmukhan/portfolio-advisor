"""Technical and multi-factor fundamental analysis engine for equity securities.

Supports standard corporate and specialized Indian banking/NBFC evaluation models.
"""

from typing import Any, Dict, List, Optional, Sequence
import numpy as np
import pandas as pd

REQUIRED_FUNDAMENTALS = {
    'symbol',
    'sector',
    'roe',
    'debt_equity',
    'sales_growth',
    'earnings_growth',
    'pe',
    'fair_pe',
    'cashflow_positive',
}


def technical(prices: Sequence[float]) -> Dict[str, Any]:
    """Compute technical trend indicators and market regimes over daily close prices.

    Requires at least 252 valid positive daily closing prices. Evaluates 200-day SMA,
    50-day SMA, 6-month and 1-year returns, 52-week highs/lows, and maximum drawdown.

    Args:
        prices: Sequence of daily closing prices ordered chronologically.

    Returns:
        Dict containing indicator metrics, trend regime ('STRONG_UPTREND', 'UPTREND',
        'DOWNTREND', 'SEVERE_BREAKDOWN'), and composite technical score (0-100).
    """
    s = pd.Series(prices, dtype=float).dropna()
    if len(s) < 252 or (s <= 0).any():
        return {'ready': False, 'reason': 'Need at least 252 valid daily closes'}

    last = float(s.iloc[-1])
    sma200 = float(s.tail(200).mean())
    sma50 = float(s.tail(50).mean()) if len(s) >= 50 else sma200
    ret126 = float(last / s.iloc[-127] - 1)
    ret252 = float(last / s.iloc[-252] - 1) if len(s) >= 252 else ret126
    high = float(s.tail(252).max())
    low = float(s.tail(252).min())
    drawdown = float(last / high - 1)

    # Technical trend regime
    if last >= sma50 >= sma200:
        regime = "STRONG_UPTREND"
    elif last >= sma200:
        regime = "UPTREND"
    elif last < 0.82 * sma200 or drawdown < -0.35:
        regime = "SEVERE_BREAKDOWN"
    else:
        regime = "DOWNTREND"

    score = float(
        np.clip(
            50
            + 25 * (last > sma200)
            + 15 * (ret126 > 0)
            + 10 * (drawdown > -0.20)
            - 20 * (drawdown < -0.35),
            0,
            100,
        )
    )

    return {
        'ready': True,
        'last': last,
        'sma200': sma200,
        'sma50': sma50,
        'high_52w': high,
        'low_52w': low,
        'return_6m': ret126,
        'return_1y': ret252,
        'drawdown_52w': drawdown,
        'regime': regime,
        'score': score,
    }


def fundamentals(row: Optional[pd.Series]) -> Dict[str, Any]:
    """Evaluate fundamental quality, growth, valuation, and balance sheet health.

    Supports dedicated banking leverage models for Banking/NBFC sectors, and standard
    debt penalty models for non-financial corporations. Detects thesis breaks and bubbles.

    Args:
        row: Pandas Series containing required fundamental metrics.

    Returns:
        Dict with readiness flag, factor subscores (quality, growth, valuation, health),
        and thesis break / valuation bubble warnings.
    """
    if row is None or not REQUIRED_FUNDAMENTALS.issubset(set(row.index)):
        return {'ready': False, 'reason': 'Missing fundamental fields'}
    try:
        roe = float(row['roe'])
        debt = float(row['debt_equity'])
        sales = float(row['sales_growth'])
        earnings = float(row['earnings_growth'])
        pe = float(row['pe'])
        fair = float(row['fair_pe'])
        cash = str(row['cashflow_positive']).strip().lower() in ('true', '1', 'yes')
        if not np.isfinite([roe, debt, sales, earnings, pe, fair]).all() or pe <= 0 or fair <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return {'ready': False, 'reason': 'Invalid fundamental fields'}

    sector = str(row['sector']).strip()
    is_financial = sector.lower() in ('banking', 'nbfc', 'financials', 'insurance')

    thesis_breaks: List[str] = []

    if is_financial:
        # Dedicated model for Indian Banks & NBFCs:
        # Leverage of deposits/borrowings is normal, so do not penalize D/E.
        # High ROE (14-20% is stellar for banks), steady loan/earnings growth, fair valuation
        quality = np.clip(35 + min(roe, 25) * 2.2 + (15 if cash else 0), 0, 100)
        growth = np.clip(50 + sales * 0.8 + earnings * 0.8, 0, 100)
        valuation = np.clip(50 + (fair / pe - 1) * 50, 0, 100)
        health = np.clip(50 + min(roe, 20) * 2.0 + (10 if earnings > 0 else -20), 0, 100)

        # Financial sector thesis breaks:
        if pe / fair >= 1.7:
            thesis_breaks.append(f"Valuation bubble (P/E {pe:.1f} is {pe/fair:.1f}x fair P/E {fair:.1f})")
        if earnings < -15 and sales < -5:
            thesis_breaks.append(f"Earnings contraction ({earnings:.1f}% earnings growth, {sales:.1f}% sales growth)")
        if roe < 8.0:
            thesis_breaks.append(f"Low capital return (Bank ROE fell to {roe:.1f}%)")
    else:
        # Standard corporate model:
        quality = np.clip(30 + min(roe, 25) * 1.5 + (20 if cash else 0) - max(debt - 1, 0) * 20, 0, 100)
        growth = np.clip(50 + sales * 0.8 + earnings * 0.8, 0, 100)
        valuation = np.clip(50 + (fair / pe - 1) * 50, 0, 100)
        health = np.clip(60 - max(debt - 1, 0) * 30 + (20 if cash else -20), 0, 100)

        # Corporate thesis breaks:
        if pe / fair >= 1.7:
            thesis_breaks.append(f"Valuation bubble (P/E {pe:.1f} is {pe/fair:.1f}x fair P/E {fair:.1f})")
        if earnings < -12 and sales < -5:
            thesis_breaks.append(f"Severe earnings decay ({earnings:.1f}% earnings growth, {sales:.1f}% sales growth)")
        if debt > 1.8 and not cash:
            thesis_breaks.append(f"Debt distress (D/E {debt:.2f} with negative cash flow)")
        elif debt > 2.5:
            thesis_breaks.append(f"Extreme leverage (D/E {debt:.2f} exceeds safety threshold)")
        if roe < 6.0:
            thesis_breaks.append(f"ROE collapse ({roe:.1f}% below cost of capital)")

    is_valuation_bubble = (pe / fair >= 1.7) or (pe > 60 and pe / fair >= 1.45)
    is_thesis_break = len(thesis_breaks) > 0
    thesis_break_reason = "; ".join(thesis_breaks) if is_thesis_break else None

    return {
        'ready': True,
        'quality': float(quality),
        'growth': float(growth),
        'valuation': float(valuation),
        'health': float(health),
        'is_financial': is_financial,
        'is_valuation_bubble': is_valuation_bubble,
        'is_thesis_break': is_thesis_break,
        'thesis_break_reason': thesis_break_reason,
        'roe': roe,
        'debt_equity': debt,
        'sales_growth': sales,
        'earnings_growth': earnings,
        'pe': pe,
        'fair_pe': fair,
        'cashflow_positive': cash,
    }


def assess(
    symbol: str,
    prices: Sequence[float],
    fund_row: Optional[pd.Series] = None,
) -> Dict[str, Any]:
    """Generate comprehensive investment assessment and recommendation signal for a stock.

    Combines technical and fundamental factor models to classify stock into signals:
    - 'BUY_CANDIDATE': High quality compounder with attractive or fair valuation
    - 'HOLD': Steady compounding position with thesis intact
    - 'SELL': Thesis break, valuation bubble, severe trend breakdown, or underperformance
    - 'REVIEW': Incomplete price history (<252 days) or missing fundamental fields

    Args:
        symbol: Stock trading symbol (e.g. 'INFY').
        prices: Chronological sequence of historical daily closing prices.
        fund_row: Optional Pandas Series containing fundamental ratios.

    Returns:
        Dict containing action ('BUY', 'HOLD', 'SELL', 'REVIEW'), composite score,
        subscores, rationale, and underlying indicator readings.
    """
    t = technical(prices)
    f = fundamentals(fund_row)
    if not t['ready'] or not f['ready']:
        reasons = [x['reason'] for x in (t, f) if not x['ready']]
        return {
            'symbol': symbol,
            'signal': 'REVIEW',
            'action': 'REVIEW',
            'action_label': 'Under Review',
            'score': None,
            'scores': {'quality': 0, 'valuation': 0, 'growth': 0, 'technical': 0, 'health': 0},
            'reason': '; '.join(reasons) if reasons else 'Data incomplete',
            'price': t.get('last'),
            'sma200': t.get('sma200'),
            'thesis_status': 'UNCONFIRMED',
        }

    # Standard weighting: Quality 35%, Valuation 25%, Technical 15%, Growth 15%, Neutral 10%
    score = round(
        0.35 * f['quality']
        + 0.25 * f['valuation']
        + 0.15 * t['score']
        + 0.15 * f['growth']
        + 0.10 * 50,
        1,
    )

    # 1. Fundamental Thesis Break: Declining earnings, debt distress, or ROE collapse -> Exit 100%
    if f.get('is_thesis_break') and (
        f.get('debt_equity', 0) > 1.8
        or f.get('earnings_growth', 0) < -10
        or not f.get('cashflow_positive', True)
    ):
        signal = 'SELL'
        action = 'SELL'
        action_label = 'Exit / Thesis Break'
        thesis_status = 'THESIS_BREAK'
        reason = (
            f"Thesis Break: {f.get('thesis_break_reason')}. Core long-term investment hypothesis invalidated."
        )

    # 2. Valuation Euphoria Bubble: Sell / Profit Booking -> Trim
    elif f.get('is_valuation_bubble') or f['valuation'] <= 20:
        signal = 'SELL'
        action = 'SELL'
        action_label = 'Take Profit / Trim'
        thesis_status = 'VALUATION_BUBBLE'
        reason = (
            f"Valuation Bubble: P/E {f['pe']:.1f} is {f['pe']/f['fair_pe']:.1f}x Fair P/E ({f['fair_pe']:.1f}). "
            f"Extreme multiple expansion poses severe downside risk. Take profits / trim."
        )

    # 3. Severe Long-Term Trend Breakdown with Weak Fundamentals
    elif t.get('regime') == 'SEVERE_BREAKDOWN' and (score < 55 or f['quality'] < 50):
        signal = 'SELL'
        action = 'SELL'
        action_label = 'Cut Loss / Capital Protection'
        thesis_status = 'TREND_BREAKDOWN'
        drawdown_pct = abs(t.get('drawdown_52w', 0)) * 100
        reason = (
            f"Severe Breakdown: Price is {drawdown_pct:.1f}% below 52W high and below 200 SMA with weak fundamentals "
            f"({f['quality']:.0f}/100). Capital protection stop triggered."
        )

    # 4. Low Composite Underperformer: Sell
    elif score < 50:
        signal = 'SELL'
        action = 'SELL'
        action_label = 'Reallocate / Exit'
        thesis_status = 'UNDERPERFORMER'
        reason = (
            f"Low Composite Score ({score:.1f}/100): Weak fundamental quality ({f['quality']:.0f}) and trend "
            f"({t['score']:.0f}). Reallocate capital to higher-conviction opportunities."
        )

    # 5. BUY_CANDIDATE: Strong compounder at fair or attractive price
    elif score >= 80 or (
        score >= 75
        and f['valuation'] >= 55
        and f['quality'] >= 60
        and t['last'] >= t['sma200']
    ):
        signal = 'BUY_CANDIDATE'
        action = 'BUY'
        action_label = 'Accumulate'
        thesis_status = 'STRONG_COMPOUNDER'
        reason = (
            f"Quality {f['quality']:.0f}, valuation {f['valuation']:.0f}, growth {f['growth']:.0f}, trend {t['score']:.0f}; "
            f"Strong long-term compounder candidate."
        )

    # 6. HOLD: Fundamentals intact, steady compounding
    else:
        signal = 'HOLD'
        action = 'HOLD'
        action_label = 'Hold & Compound'
        thesis_status = 'STEADY_HOLD'
        reason = (
            f"Quality {f['quality']:.0f}, valuation {f['valuation']:.0f}, growth {f['growth']:.0f}, trend {t['score']:.0f}; "
            f"Thesis intact, fair valuation. Hold for compounding."
        )

    return {
        'symbol': symbol,
        'signal': signal,
        'action': action,
        'action_label': action_label,
        'score': score,
        'scores': {
            'quality': f['quality'],
            'valuation': f['valuation'],
            'growth': f['growth'],
            'technical': t['score'],
            'health': f.get('health', 60),
        },
        'reason': reason,
        'thesis_status': thesis_status,
        'price': t['last'],
        'sma200': t['sma200'],
        'sma50': t.get('sma50'),
        'high_52w': t.get('high_52w'),
        'low_52w': t.get('low_52w'),
        'return_6m': t.get('return_6m'),
        'return_1y': t.get('return_1y'),
        'drawdown_52w': t.get('drawdown_52w'),
        'regime': t.get('regime'),
        'fundamentals': f,
    }
