import pandas as pd
from advisor.analysis import assess, technical, fundamentals
from advisor.portfolio import plan
from advisor.storage import connect, add_purchase, monthly_spend, save_custom_holdings, get_custom_holdings

def test_missing_data_fails_closed():
    assert assess('ABC', [100] * 300)['signal'] == 'REVIEW'

def test_short_history():
    assert not technical([100] * 100)['ready']

def test_budget_no_overspend():
    r = [{'symbol': 'X', 'signal': 'BUY_CANDIDATE', 'score': 99, 'price': 100, 'sector': 'Technology', 'reason': 'test'}]
    p = plan(r, [], 49000, max_stock_weight=1, max_sector_weight=1)
    assert sum(a['estimated_gross'] for a in p['allocations']) <= 1000

def test_monthly_spend(tmp_path):
    db = connect(str(tmp_path / 'test.db'))
    add_purchase(db, '2026-10-01', 'ABC', 1200)
    add_purchase(db, '2026-09-30', 'ABC', 2000)
    assert monthly_spend(db, '2026-10-22') == 1200
    db.close()

def test_no_order_methods():
    from advisor.broker import KiteReadOnly
    assert not hasattr(KiteReadOnly, 'place_order')
    assert not hasattr(KiteReadOnly, 'modify_order')
    assert not hasattr(KiteReadOnly, 'cancel_order')

def test_sell_signal_on_thesis_break():
    # Deteriorating company with high debt, negative earnings, negative cashflow
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
    # Healthy company but trading at 3x fair PE
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
    # Bank with normal financial leverage (e.g. D/E 6.5) and good ROE
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

def test_storage_custom_holdings(tmp_path):
    db = connect(str(tmp_path / 'custom.db'))
    custom = [
        {'symbol': 'INFY', 'quantity': 25, 'average_price': 1500.0, 'price': 1850.0, 'sector': 'Technology'},
        {'symbol': 'TCS', 'quantity': 10, 'average_price': 3500.0, 'price': 4000.0, 'sector': 'Technology'}
    ]
    save_custom_holdings(db, custom)
    loaded = get_custom_holdings(db)
    assert len(loaded) == 2
    assert {x['symbol'] for x in loaded} == {'INFY', 'TCS'}
    db.close()

def test_indian_currency_formatting():
    from advisor.formatters import format_inr
    assert format_inr(1191318) == '₹11,91,318'
    assert format_inr(-141659) == '-₹1,41,659'
    assert format_inr(50000) == '₹50,000'
    assert format_inr(968.3, decimals=2) == '₹968.30'
    assert format_inr(10000000) == '₹1,00,00,000'
    assert format_inr(141659, show_plus=True) == '+₹1,41,659'
    assert format_inr(1191318, include_symbol=False) == '11,91,318'

def test_settings_dynamic_mode(monkeypatch):
    from advisor.config import Settings
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


