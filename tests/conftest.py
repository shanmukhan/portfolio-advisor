"""Shared pytest fixtures and test data factories for Zerodha Portfolio Advisor."""

import pandas as pd
import pytest
from advisor.storage import connect


@pytest.fixture
def temp_db(tmp_path):
    """Provide a temporary clean SQLite database connection."""
    db_file = tmp_path / "test_advisor.sqlite3"
    db = connect(str(db_file))
    yield db
    db.close()


@pytest.fixture
def healthy_fund_row():
    """Fundamental metrics for a high-quality compounder."""
    return pd.Series({
        'symbol': 'QUALITYCO',
        'sector': 'Technology',
        'roe': 28.5,
        'debt_equity': 0.05,
        'sales_growth': 16.0,
        'earnings_growth': 20.0,
        'pe': 25.0,
        'fair_pe': 30.0,
        'cashflow_positive': 'true'
    })


@pytest.fixture
def bubble_fund_row():
    """Fundamental metrics for a valuation bubble stock."""
    return pd.Series({
        'symbol': 'BUBBLECO',
        'sector': 'Consumer',
        'roe': 20.0,
        'debt_equity': 0.1,
        'sales_growth': 12.0,
        'earnings_growth': 14.0,
        'pe': 98.0,
        'fair_pe': 32.0,
        'cashflow_positive': 'true'
    })


@pytest.fixture
def deteriorating_fund_row():
    """Fundamental metrics for a thesis break stock."""
    return pd.Series({
        'symbol': 'BROKENCO',
        'sector': 'Industrials',
        'roe': 2.0,
        'debt_equity': 3.2,
        'sales_growth': -15.0,
        'earnings_growth': -35.0,
        'pe': 45.0,
        'fair_pe': 18.0,
        'cashflow_positive': 'false'
    })


@pytest.fixture
def uptrend_prices():
    """300 days of ascending prices representing strong uptrend."""
    base = 100.0
    return [base + (i * 0.8) for i in range(300)]


@pytest.fixture
def downtrend_prices():
    """300 days of descending prices representing severe breakdown."""
    base = 400.0
    return [max(10.0, base - (i * 1.0)) for i in range(300)]
