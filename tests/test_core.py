"""Unit test suite for Zerodha Long-Term Portfolio Advisor."""

import pytest
import pandas as pd
from advisor.analysis import assess, technical, fundamentals
from advisor.broker import KiteReadOnly, parse_kite_holdings
from advisor.config import Settings
from advisor.engine import run
from advisor.formatters import format_inr
from advisor.portfolio import plan
from advisor.storage import (
    add_purchase, clear_custom_holdings, connect, delete_purchase,
    get_custom_holdings, get_latest_report, get_purchases, monthly_spend,
    save_custom_holdings, save_report, validate_date, validate_symbol
)


# ==============================================================================
# 1. Existing Core Tests (Preserved and Validated)
# ==============================================================================

def test_missing_data_fails_closed():
    assert assess('ABC', [100] * 300)['signal'] == 'REVIEW'


def test_short_history():
    assert not technical([100] * 100)['ready']


def test_budget_no_overspend():
    r = [{'symbol': 'X', 'signal': 'BUY_CANDIDATE', 'score': 99, 'price': 100, 'sector': 'Technology', 'reason': 'test'}]
    p = plan(r, [], 49000, max_stock_weight=1, max_sector_weight=1)
    assert sum(a['estimated_gross'] for a in p['allocations']) <= 1000


def test_monthly_spend(temp_db):
    add_purchase(temp_db, '2026-10-01', 'ABC', 1200)
    add_purchase(temp_db, '2026-09-30', 'ABC', 2000)
    assert monthly_spend(temp_db, '2026-10-22') == 1200


def test_no_order_methods():
    assert not hasattr(KiteReadOnly, 'place_order')
    assert not hasattr(KiteReadOnly, 'modify_order')
    assert not hasattr(KiteReadOnly, 'cancel_order')


def test_sell_signal_on_thesis_break():
    fund_row = pd.Series({
        'symbol': 'BADCO', 'sector': 'Industrials', 'roe': 3.5, 'debt_equity': 2.8,
        'sales_growth': -12.0, 'earnings_growth': -28.0, 'pe': 35.0, 'fair_pe': 20.0,
        'cashflow_positive': 'false'
    })
    prices = [100.0] * 300
    res = assess('BADCO', prices, fund_row)
    assert res['signal'] == 'SELL'
    assert res['action'] == 'SELL'
    assert 'Thesis Break' in res['reason'] or 'Valuation Bubble' in res['reason']


def test_sell_signal_on_valuation_bubble():
    fund_row = pd.Series({
        'symbol': 'BUBBLE', 'sector': 'Technology', 'roe': 22.0, 'debt_equity': 0.1,
        'sales_growth': 15.0, 'earnings_growth': 18.0, 'pe': 95.0, 'fair_pe': 30.0,
        'cashflow_positive': 'true'
    })
    prices = [100.0 + i * 0.5 for i in range(300)]
    res = assess('BUBBLE', prices, fund_row)
    assert res['signal'] == 'SELL'
    assert res['action'] == 'SELL'
    assert res['thesis_status'] == 'VALUATION_BUBBLE'


def test_banking_model_supported():
    fund_row = pd.Series({
        'symbol': 'HDFCBANK', 'sector': 'Banking', 'roe': 17.0, 'debt_equity': 6.5,
        'sales_growth': 18.0, 'earnings_growth': 16.0, 'pe': 18.0, 'fair_pe': 22.0,
        'cashflow_positive': 'true'
    })
    prices = [1500.0 + i * 0.5 for i in range(300)]
    res = assess('HDFCBANK', prices, fund_row)
    assert res['signal'] in ('BUY_CANDIDATE', 'HOLD')
    assert res['action'] in ('BUY', 'HOLD')
    assert res['fundamentals']['ready'] is True


def test_portfolio_plan_with_sells():
    recs = [
        {'symbol': 'BUY1', 'signal': 'BUY_CANDIDATE', 'action': 'BUY', 'score': 88, 'price': 500, 'sector': 'Technology', 'reason': 'Strong buy'},
        {'symbol': 'SELL1', 'signal': 'SELL', 'action': 'SELL', 'score': 35, 'price': 200, 'sector': 'Industrials', 'reason': 'Thesis break', 'thesis_status': 'THESIS_BREAK'}
    ]
    holdings = [
        {'symbol': 'SELL1', 'quantity': 50, 'price': 200, 'average_price': 300, 'sector': 'Industrials'}
    ]
    p = plan(recs, holdings, spent=10000, limit=50000)
    assert len(p['sells']) == 1
    assert p['sells'][0]['symbol'] == 'SELL1'
    assert p['sells'][0]['estimated_proceeds'] == 10000.0
    assert p['potential_freed_capital'] == 10000.0
    assert len(p['allocations']) >= 1


def test_storage_custom_holdings(temp_db):
    custom = [
        {'symbol': 'INFY', 'quantity': 25, 'average_price': 1500.0, 'price': 1850.0, 'sector': 'Technology'},
        {'symbol': 'TCS', 'quantity': 10, 'average_price': 3500.0, 'price': 4000.0, 'sector': 'Technology'}
    ]
    save_custom_holdings(temp_db, custom)
    loaded = get_custom_holdings(temp_db)
    assert len(loaded) == 2
    assert {x['symbol'] for x in loaded} == {'INFY', 'TCS'}


def test_indian_currency_formatting():
    assert format_inr(1191318) == '₹11,91,318'
    assert format_inr(-141659) == '-₹1,41,659'
    assert format_inr(50000) == '₹50,000'
    assert format_inr(968.3, decimals=2) == '₹968.30'
    assert format_inr(10000000) == '₹1,00,00,000'
    assert format_inr(141659, show_plus=True) == '+₹1,41,659'
    assert format_inr(1191318, include_symbol=False) == '11,91,318'


def test_settings_dynamic_mode(monkeypatch):
    monkeypatch.setenv('ADVISOR_MODE', 'demo')
    s1 = Settings()
    assert s1.mode == 'demo'
    monkeypatch.setenv('ADVISOR_MODE', 'live')
    s2 = Settings()
    assert s2.mode == 'live'


def test_stock_price_history_chart_layout():
    from advisor.charts import plot_stock_price_history
    fig = plot_stock_price_history('BEL')
    assert fig is not None
    assert 0.0 <= fig.layout.title.y <= 1.0
    assert fig.layout.legend.y is not None


# ==============================================================================
# 2. Input Validation Tests (Symbol & Date)
# ==============================================================================

def test_validate_symbol_valid():
    assert validate_symbol('infy') == 'INFY'
    assert validate_symbol('  TCS  ') == 'TCS'
    assert validate_symbol('M&M') == 'M&M'
    assert validate_symbol('BAJAJ-AUTO') == 'BAJAJ-AUTO'
    assert validate_symbol('L_T') == 'L_T'


def test_validate_symbol_invalid():
    with pytest.raises(ValueError):
        validate_symbol('')
    with pytest.raises(ValueError):
        validate_symbol('   ')
    with pytest.raises(ValueError):
        validate_symbol('INVALID SYMBOL WITH SPACES')
    with pytest.raises(ValueError):
        validate_symbol('VERY_LONG_SYMBOL_EXCEEDING_TWENTY_FIVE_CHARS')
    with pytest.raises(ValueError):
        validate_symbol(123)  # type: ignore


def test_validate_date_valid():
    assert validate_date('2026-10-24') == '2026-10-24'
    assert validate_date('2025-01-01') == '2025-01-01'


def test_validate_date_invalid():
    with pytest.raises(ValueError):
        validate_date('2026/10/24')
    with pytest.raises(ValueError):
        validate_date('24-10-2026')
    with pytest.raises(ValueError):
        validate_date('2026-02-31')  # Nonexistent date
    with pytest.raises(ValueError):
        validate_date('not-a-date')


# ==============================================================================
# 3. Technical Indicator Regimes
# ==============================================================================

def test_technical_strong_uptrend(uptrend_prices):
    res = technical(uptrend_prices)
    assert res['ready'] is True
    assert res['regime'] == 'STRONG_UPTREND'
    assert res['score'] >= 75
    assert res['last'] > res['sma50'] >= res['sma200']


def test_technical_severe_breakdown(downtrend_prices):
    res = technical(downtrend_prices)
    assert res['ready'] is True
    assert res['regime'] == 'SEVERE_BREAKDOWN'
    assert res['score'] <= 50


def test_technical_uptrend_regime():
    # Last is above sma200, but sma50 is not >= sma200
    prices = [200.0] * 200 + [100.0] * 50 + [210.0] * 50
    res = technical(prices)
    assert res['ready'] is True
    assert res['regime'] in ('UPTREND', 'STRONG_UPTREND')


def test_technical_downtrend_regime():
    # Price below 200 SMA, but not severe enough for SEVERE_BREAKDOWN
    prices = [100.0] * 250 + [90.0] * 50
    res = technical(prices)
    assert res['ready'] is True
    assert res['regime'] in ('DOWNTREND', 'SEVERE_BREAKDOWN')


# ==============================================================================
# 4. Direct Fundamental Analysis & Assess Signals
# ==============================================================================

def test_fundamentals_direct(healthy_fund_row):
    f = fundamentals(healthy_fund_row)
    assert f['ready'] is True
    assert f['quality'] >= 60
    assert f['valuation'] >= 50
    assert f['is_thesis_break'] is False
    assert f['is_valuation_bubble'] is False


def test_fundamentals_missing_fields():
    incomplete = pd.Series({'symbol': 'XYZ', 'pe': 20.0})
    f = fundamentals(incomplete)
    assert f['ready'] is False


def test_assess_hold_signal(uptrend_prices):
    # Steady company with good quality, fair valuation, not a runaway buy
    fund_row = pd.Series({
        'symbol': 'STEADY', 'sector': 'Consumer', 'roe': 16.0, 'debt_equity': 0.3,
        'sales_growth': 8.0, 'earnings_growth': 10.0, 'pe': 28.0, 'fair_pe': 28.0,
        'cashflow_positive': 'true'
    })
    res = assess('STEADY', uptrend_prices, fund_row)
    assert res['signal'] in ('HOLD', 'BUY_CANDIDATE')
    assert res['action'] in ('HOLD', 'BUY')


def test_assess_underperformer(uptrend_prices):
    # Mediocre company with poor quality and low score
    fund_row = pd.Series({
        'symbol': 'MEDIOCRE', 'sector': 'Metals', 'roe': 7.0, 'debt_equity': 1.2,
        'sales_growth': 1.0, 'earnings_growth': 2.0, 'pe': 40.0, 'fair_pe': 15.0,
        'cashflow_positive': 'true'
    })
    res = assess('MEDIOCRE', uptrend_prices, fund_row)
    assert res['signal'] == 'SELL'
    assert res['action'] == 'SELL'
    assert res['thesis_status'] in ('UNDERPERFORMER', 'VALUATION_BUBBLE')


# ==============================================================================
# 5. Core Engine run() Tests
# ==============================================================================

def test_engine_run_demo(temp_db, monkeypatch):
    monkeypatch.setenv('ADVISOR_MODE', 'demo')
    monkeypatch.setattr('advisor.config.Settings.db', None)
    settings = Settings(mode='demo', db=temp_db.execute("PRAGMA database_list").fetchall()[0][2])

    report = run(settings=settings, save=True)
    assert 'as_of' in report
    assert report['mode'] == 'demo'
    assert 'holdings' in report
    assert 'recommendations' in report
    assert 'budget' in report
    assert 'portfolio_summary' in report
    assert 'warnings' in report

    # Verify report was saved in database
    latest = get_latest_report(temp_db)
    assert latest is not None
    assert latest['as_of'] == report['as_of']


def test_engine_run_invalid_mode():
    settings = Settings(mode='invalid_mode')
    with pytest.raises(ValueError, match='ADVISOR_MODE must be demo or live'):
        run(settings=settings)


# ==============================================================================
# 6. Storage CRUD & Edge Cases
# ==============================================================================

def test_storage_delete_purchase(temp_db):
    add_purchase(temp_db, '2026-10-15', 'TCS', 5000.0)
    purchases = get_purchases(temp_db)
    assert len(purchases) == 1
    p_id = purchases[0]['id']

    delete_purchase(temp_db, p_id)
    assert len(get_purchases(temp_db)) == 0


def test_storage_negative_purchase_rejected(temp_db):
    with pytest.raises(ValueError, match='Purchase amount cannot be negative'):
        add_purchase(temp_db, '2026-10-15', 'TCS', -500.0)


def test_storage_save_and_get_latest_report(temp_db):
    report_data = {'status': 'ok', 'score': 95}
    save_report(temp_db, '2026-10-24', report_data)

    retrieved = get_latest_report(temp_db)
    assert retrieved == report_data


def test_storage_clear_custom_holdings(temp_db):
    save_custom_holdings(temp_db, [{'symbol': 'INFY', 'quantity': 10, 'average_price': 1500, 'price': 1800, 'sector': 'Technology'}])
    assert len(get_custom_holdings(temp_db)) == 1

    clear_custom_holdings(temp_db)
    assert len(get_custom_holdings(temp_db)) == 0


# ==============================================================================
# 7. Portfolio Planner Limits & Sizing
# ==============================================================================

def test_portfolio_plan_sector_cap_enforcement():
    # When sector is already at or above cap (25%), no further buys in that sector
    recs = [
        {'symbol': 'TECH1', 'signal': 'BUY_CANDIDATE', 'score': 95, 'price': 500, 'sector': 'Technology', 'reason': 'Strong buy'},
        {'symbol': 'HEALTH1', 'signal': 'BUY_CANDIDATE', 'score': 85, 'price': 500, 'sector': 'Healthcare', 'reason': 'Good buy'}
    ]
    # Existing portfolio: Technology is 50,000 out of 60,000 (>25%)
    holdings = [
        {'symbol': 'TECH_OLD', 'quantity': 100, 'price': 500, 'average_price': 400, 'sector': 'Technology'},
        {'symbol': 'AUTO_OLD', 'quantity': 20, 'price': 500, 'average_price': 400, 'sector': 'Auto'}
    ]
    p = plan(recs, holdings, spent=0, limit=20000, max_stock_weight=0.15, max_sector_weight=0.25)
    # TECH1 should receive 0 allocation because Technology sector headroom is 0
    symbols_bought = [a['symbol'] for a in p['allocations']]
    assert 'TECH1' not in symbols_bought


def test_portfolio_plan_stock_cap_enforcement():
    recs = [
        {'symbol': 'INFY', 'signal': 'BUY_CANDIDATE', 'score': 95, 'price': 1000, 'sector': 'Technology', 'reason': 'Strong buy'}
    ]
    # INFY already 10,000 in a 20,000 portfolio (50% > 10% max)
    holdings = [
        {'symbol': 'INFY', 'quantity': 10, 'price': 1000, 'average_price': 900, 'sector': 'Technology'},
        {'symbol': 'OTHER', 'quantity': 10, 'price': 1000, 'average_price': 900, 'sector': 'Consumer'}
    ]
    p = plan(recs, holdings, spent=0, limit=10000, max_stock_weight=0.10)
    assert len(p['allocations']) == 0


def test_portfolio_plan_empty_inputs():
    p = plan([], [], spent=50000, limit=50000)
    assert p['allocations'] == []
    assert p['sells'] == []
    assert p['unallocated'] == 0.0


# ==============================================================================
# 8. Broker Adapter & Parsing
# ==============================================================================

def test_parse_kite_holdings_filtering_and_mapping():
    raw = [
        {'tradingsymbol': 'INFY', 'quantity': 25, 'average_price': 1500.5, 'last_price': 1850.0},
        {'tradingsymbol': 'TCS', 'quantity': 0, 'average_price': 3500.0, 'last_price': 4000.0},  # 0 quantity should be filtered
        {'tradingsymbol': 'WIPRO', 'quantity': -5, 'average_price': 450.0, 'last_price': 480.0}, # Negative qty filtered
        {'tradingsymbol': 'RELIANCE', 'quantity': 10, 'average_price': 0.0, 'last_price': 2900.0}  # Falls back to LTP
    ]
    parsed = parse_kite_holdings(raw)
    assert len(parsed) == 2
    assert parsed[0]['symbol'] == 'INFY'
    assert parsed[0]['quantity'] == 25.0
    assert parsed[0]['average_price'] == 1500.5
    assert parsed[0]['price'] == 1850.0
    assert parsed[0]['sector'] == 'Unknown'

    assert parsed[1]['symbol'] == 'RELIANCE'
    assert parsed[1]['average_price'] == 2900.0  # Fallback to last_price


def test_parse_kite_holdings_empty():
    assert parse_kite_holdings([]) == []
    assert parse_kite_holdings(None) == []


# ==============================================================================
# 9. Formatters Edge Cases
# ==============================================================================

def test_format_inr_edge_cases():
    assert format_inr(None) == '-'
    assert format_inr(float('nan')) == '-'
    assert format_inr(0) == '₹0'
    assert format_inr(0, decimals=2) == '₹0.00'
    assert format_inr(-0.5, decimals=2) == '-₹0.50'
    assert format_inr('invalid') == 'invalid'


# ==============================================================================
# 10. CLI Integration Test
# ==============================================================================

def test_cli_record_buy_and_report(tmp_path, monkeypatch):
    from advisor.cli import main
    db_path = str(tmp_path / "cli_test.sqlite3")
    monkeypatch.setenv('ADVISOR_DB', db_path)
    monkeypatch.setenv('ADVISOR_MODE', 'demo')

    # Test record-buy command
    exit_code = main(['record-buy', '--date', '2026-10-24', '--symbol', 'INFY', '--amount', '5000.0'])
    assert exit_code == 0

    # Verify db record was written
    test_db = connect(db_path)
    try:
        purchases = get_purchases(test_db)
        assert len(purchases) == 1
        assert purchases[0]['symbol'] == 'INFY'
        assert purchases[0]['gross_amount'] == 5000.0
    finally:
        test_db.close()

    # Test report command
    exit_code_report = main(['report', '--compact'])
    assert exit_code_report == 0
