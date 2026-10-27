"""Zerodha Long-Term Portfolio Advisor Dashboard.

Modular Streamlit frontend architecture with extracted CSS, components, sidebar, and tab modules.
"""

import os
from dotenv import load_dotenv
import streamlit as st

from advisor.config import Settings, environment_file
from advisor.engine import run
from advisor.storage import connect, get_custom_holdings
from ui.components import render_header, render_kpi_cards
from ui.sidebar import render_sidebar
from ui.styles import apply_styles
from ui.tabs.budget import render_budget_tab
from ui.tabs.import_data import render_import_data_tab
from ui.tabs.portfolio import render_portfolio_tab
from ui.tabs.recommendations import render_recommendations_tab
from ui.tabs.research import render_research_tab
from ui.tabs.screener import render_screener_tab
from ui.tabs.strategy import render_strategy_tab

# 1. Streamlit Page Configuration
st.set_page_config(
    page_title="Zerodha Long-Term Advisor",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded",
)

# 2. Inject CSS Theme
apply_styles()

# 3. Environment & Configuration
env_file = environment_file()
if env_file.exists():
    load_dotenv(dotenv_path=env_file, override=True)

curr_api_key = os.getenv('KITE_API_KEY', '').strip()
curr_api_secret = os.getenv('KITE_API_SECRET', '').strip()
curr_access_token = os.getenv('KITE_ACCESS_TOKEN', '').strip()


@st.cache_data(ttl=60)
def check_kite_session(api_key: str, access_token: str):
    """Single unified source of truth for Kite Connect authentication status across entire app."""
    if not api_key or not access_token:
        return {'status': 'unconfigured', 'is_live': False, 'user_name': '', 'user_id': '', 'error': ''}
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        prof = kite.profile()
        return {
            'status': 'connected',
            'is_live': True,
            'user_name': prof.get('user_name', ''),
            'user_id': prof.get('user_id', ''),
            'error': '',
        }
    except Exception as exc:
        return {
            'status': 'expired',
            'is_live': False,
            'user_name': '',
            'user_id': '',
            'error': str(exc),
        }


@st.cache_data(ttl=900)
def load_report():
    """Execute advisory engine and cache result for 15 minutes."""
    return run()


settings = Settings()
kite_session = check_kite_session(curr_api_key, curr_access_token)
is_live = kite_session.get('is_live', False)

db = connect(settings.db)
try:
    custom_saved = get_custom_holdings(db)

    try:
        report = load_report()
    except Exception as exc:
        st.error(f"Cannot initialize portfolio advisor engine: {exc}")
        st.stop()

    summary = report.get('portfolio_summary', {})
    budget = report.get('budget', {})
    holdings = report.get('holdings', [])
    recommendations = report.get('recommendations', [])

    # 4. Render Sidebar
    render_sidebar(report, settings, db, kite_session)

    # 5. Header Title & Top Status Banners
    render_header(report.get('as_of', ''), len(holdings), settings.monthly_limit)

    # Fallback / Demo notification banner
    if settings.mode == 'live' and not report.get('live', False):
        st.warning("⚠️ Live Zerodha Kite Connect session is unavailable or expired. Currently displaying cached portfolio data.")
    elif not is_live and not custom_saved:
        st.markdown(
            """
            <div class="zerodha-connect-banner">
                <div>
                    <span style="font-weight: 700; color: #1D4ED8; font-size: 0.95rem;">⚡ Ready to connect your actual Zerodha portfolio?</span>
                    <span style="color: #1E40AF; font-size: 0.9rem; margin-left: 6px;">
                        You are currently exploring sample demo data. You can connect your live Kite account or drag-and-drop your Zerodha CSV export in the <b>⚡ Zerodha Connect & Import</b> tab below!
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 6. Top Executive Metric Cards
    render_kpi_cards(summary, budget)

    # Important warnings / alerts expander
    if report.get('warnings'):
        with st.expander(f"⚠️ Risk & Concentration Alerts ({len(report['warnings'])})", expanded=False):
            for w in report['warnings']:
                st.markdown(f"- {w}")

    # 7. Main Navigation Tabs
    tabs = st.tabs([
        "📊 Portfolio Overview",
        "🎯 Advisor Recommendations",
        "🔍 Stock Research Studio",
        "💰 Monthly Budget & Plan",
        "⚡ Zerodha Connect & Import",
        "🔭 Discovery Screener",
        "📖 Strategy Framework",
    ])

    with tabs[0]:
        render_portfolio_tab(holdings, summary, settings)

    with tabs[1]:
        render_recommendations_tab(recommendations)

    with tabs[2]:
        render_research_tab(recommendations)

    with tabs[3]:
        render_budget_tab(budget, settings, db)

    with tabs[4]:
        render_import_data_tab(db, kite_session, curr_api_key, curr_api_secret, curr_access_token, env_file)

    with tabs[5]:
        render_screener_tab(recommendations)

    with tabs[6]:
        render_strategy_tab()

finally:
    db.close()
