import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import os
import textwrap
from dotenv import set_key

from advisor.engine import run
from advisor.formatters import format_inr
from advisor.storage import (
    connect, add_purchase, monthly_spend, get_purchases,
    delete_purchase, save_custom_holdings, get_custom_holdings, clear_custom_holdings
)
from advisor.config import Settings
from advisor.charts import (
    plot_portfolio_allocation, plot_holdings_pnl,
    plot_stock_price_history, plot_factor_radar,
    plot_risk_return, plot_budget_gauge,
    plot_holdings_treemap, plot_sector_exposure_chart,
    plot_capital_flow
)

IST = ZoneInfo('Asia/Kolkata')

# 1. Streamlit Page Configuration
st.set_page_config(
    page_title="Zerodha Long-Term Advisor",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# 2. Modern Institutional Financial Light Theme (Plus Jakarta Sans + JetBrains Mono)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* Global Typography & Light Canvas */
    html, body, [class*="css"], .stApp {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }

    /* Tabular Numerals for Financial Data & Prices */
    .tabular-nums, .metric-value, .stat-mono {
        font-family: 'JetBrains Mono', monospace !important;
        font-variant-numeric: tabular-nums !important;
    }

    /* Top navbar brand bar */
    .top-brand-bar {
        background-color: #FFFFFF;
        border-bottom: 1px solid #E2E8F0;
        padding: 14px 28px;
        margin: -6rem -4rem 1.8rem -4rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }

    /* Live and Sync Pulse animations */
    .live-pulse {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10B981;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
        animation: pulse-green 2s infinite;
        flex-shrink: 0;
    }
    @keyframes pulse-green {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    .blue-pulse {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #2563EB;
        box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.7);
        animation: pulse-blue 2s infinite;
        flex-shrink: 0;
    }
    @keyframes pulse-blue {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 5px rgba(37, 99, 235, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(37, 99, 235, 0); }
    }
    .amber-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #F59E0B;
        flex-shrink: 0;
    }

    /* Left Menu Bar (Sidebar) Institutional Financial Styling */
    [data-testid="stSidebar"] {
        background-color: #FAFCFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.25rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.65rem !important;
    }
    [data-testid="stSidebar"] hr {
        margin: 0.5rem 0 !important;
        border-color: #F1F5F9 !important;
    }

    /* Sidebar Brand Header */
    .sidebar-brand-wrapper {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 4px 10px 4px;
        border-bottom: 1px solid #EDF2F7;
        margin-bottom: 2px;
    }
    .sidebar-kite-icon {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 3px 8px rgba(37, 99, 235, 0.28);
        flex-shrink: 0;
    }
    .sidebar-brand-title {
        font-weight: 800;
        font-size: 1.10rem;
        color: #0F172A;
        letter-spacing: -0.02em;
        line-height: 1.15;
    }
    .sidebar-brand-sub {
        font-size: 0.70rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 2px;
    }

    /* Sidebar Status Card */
    .sidebar-status-card {
        border-radius: 10px;
        padding: 10px 12px;
        margin-bottom: 2px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.02);
        transition: all 0.15s ease;
    }
    .sidebar-env-badge {
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 9999px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* Sidebar KPI Snapshot Card */
    .sidebar-kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 12px 14px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
        position: relative;
        overflow: hidden;
    }
    .sidebar-kpi-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #2563EB, #60A5FA);
    }
    .sidebar-kpi-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.68rem;
        font-weight: 700;
        color: #64748B;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .sidebar-kpi-val {
        font-size: 1.35rem;
        font-weight: 700;
        color: #0F172A;
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
        font-variant-numeric: tabular-nums !important;
        letter-spacing: -0.02em;
        margin-top: 3px;
        line-height: 1.2;
    }
    .sidebar-pnl-pill {
        font-size: 0.72rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 6px;
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
        font-variant-numeric: tabular-nums !important;
        display: inline-flex;
        align-items: center;
        gap: 3px;
    }
    .pnl-pill-profit {
        background: #ECFDF5;
        color: #059669;
        border: 1px solid #A7F3D0;
    }
    .pnl-pill-loss {
        background: #FEF2F2;
        color: #DC2626;
        border: 1px solid #FECACA;
    }
    .sidebar-kpi-signals-row {
        display: flex;
        gap: 5px;
        margin-top: 9px;
        padding-top: 8px;
        border-top: 1px dashed #E2E8F0;
    }
    .sidebar-sig-badge {
        flex: 1;
        text-align: center;
        font-size: 0.68rem;
        padding: 3px 4px;
        border-radius: 6px;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
    }
    .sig-buy { background: #F0FDF4; color: #166534; border: 1px solid #DCFCE7; }
    .sig-hold { background: #FFFBEB; color: #92400E; border: 1px solid #FEF3C7; }
    .sig-sell { background: #FEF2F2; color: #991B1B; border: 1px solid #FEE2E2; }
    .sig-dot-buy { width: 5px; height: 5px; border-radius: 50%; background: #16A34A; }
    .sig-dot-hold { width: 5px; height: 5px; border-radius: 50%; background: #D97706; }
    .sig-dot-sell { width: 5px; height: 5px; border-radius: 50%; background: #DC2626; }

    /* Sidebar Monthly Budget Card */
    .sidebar-budget-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 12px 14px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
        position: relative;
        overflow: hidden;
    }
    .sidebar-budget-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #7C3AED, #A78BFA);
    }
    .sidebar-budget-track {
        width: 100%;
        height: 7px;
        background: #F1F5F9;
        border-radius: 9999px;
        overflow: hidden;
    }
    .sidebar-budget-bar {
        height: 100%;
        border-radius: 9999px;
        transition: width 0.3s ease;
    }

    /* Sidebar Form and Expander styling */
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.02) !important;
        overflow: hidden;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] details {
        border: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary {
        font-weight: 600 !important;
        font-size: 0.84rem !important;
        color: #1E293B !important;
        padding: 10px 12px !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
        color: #2563EB !important;
    }
    [data-testid="stSidebar"] .stTextInput input, 
    [data-testid="stSidebar"] .stNumberInput input, 
    [data-testid="stSidebar"] .stDateInput input {
        border-radius: 6px !important;
        border: 1px solid #CBD5E1 !important;
        font-size: 0.82rem !important;
        padding: 6px 10px !important;
        background-color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] .stTextInput input:focus, 
    [data-testid="stSidebar"] .stNumberInput input:focus, 
    [data-testid="stSidebar"] .stDateInput input:focus {
        border-color: #2563EB !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15) !important;
    }

    /* Sidebar Buttons */
    [data-testid="stSidebar"] .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.84rem !important;
        padding: 8px 14px !important;
        transition: all 0.15s ease !important;
    }

    /* Soothing, Harmonious Refresh Action Button */
    [data-testid="stSidebar"] .st-key-refresh_portfolio_btn button {
        background: #EFF6FF !important;
        color: #1D4ED8 !important;
        border: 1px solid #BFDBFE !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.84rem !important;
        padding: 8px 16px !important;
        box-shadow: 0 1px 2px rgba(37, 99, 235, 0.05) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 8px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    [data-testid="stSidebar"] .st-key-refresh_portfolio_btn button:hover {
        background: #DBEAFE !important;
        color: #1E40AF !important;
        border-color: #93C5FD !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.12) !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="stSidebar"] .st-key-refresh_portfolio_btn button:active {
        transform: translateY(0) !important;
        background: #BFDBFE !important;
    }
    [data-testid="stSidebar"] .st-key-refresh_portfolio_btn button [data-testid="stIconMaterial"] {
        color: #1D4ED8 !important;
        font-size: 1.15rem !important;
        display: inline-flex !important;
        align-items: center !important;
        transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), color 0.2s ease !important;
    }
    [data-testid="stSidebar"] .st-key-refresh_portfolio_btn button:hover [data-testid="stIconMaterial"] {
        color: #1E40AF !important;
        transform: rotate(180deg) !important;
    }

    [data-testid="stSidebar"] .stButton>button:not([kind="primary"]) {
        background: #F8FAFC !important;
        color: #64748B !important;
        border: 1px solid #E2E8F0 !important;
    }
    [data-testid="stSidebar"] .stButton>button:not([kind="primary"]):hover {
        background: #FEE2E2 !important;
        color: #DC2626 !important;
        border-color: #FECACA !important;
    }

    /* Sidebar Security Footer */
    .sidebar-security-footer {
        padding: 10px 4px 2px 4px;
        text-align: center;
        border-top: 1px solid #EDF2F7;
        margin-top: 6px;
    }

    /* Modern Metric KPI Cards with Top Gradient Accent */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.04);
        position: relative;
        overflow: hidden;
        transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #CBD5E1;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04);
    }
    .metric-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3.5px;
        background: linear-gradient(90deg, #2563EB, #60A5FA);
    }
    .metric-card-profit::before {
        background: linear-gradient(90deg, #059669, #34D399) !important;
    }
    .metric-card-loss::before {
        background: linear-gradient(90deg, #DC2626, #F87171) !important;
    }
    .metric-card-budget::before {
        background: linear-gradient(90deg, #7C3AED, #A78BFA) !important;
    }
    .metric-card-signals::before {
        background: linear-gradient(90deg, #0284C7, #38BDF8) !important;
    }
    .metric-title {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748B;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.2;
        letter-spacing: -0.02em;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .metric-sub {
        font-size: 0.85rem;
        margin-top: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
        font-weight: 500;
    }

    /* Modern Recommendation Cards */
    .rec-card-buy, .rec-card-hold, .rec-card-sell {
        background: #FFFFFF;
        border-top: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        border-bottom: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .rec-card-buy:hover, .rec-card-hold:hover, .rec-card-sell:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 24px -6px rgba(15, 23, 42, 0.09);
    }
    .rec-card-buy { border-left: 5px solid #059669; }
    .rec-card-hold { border-left: 5px solid #D97706; }
    .rec-card-sell { border-left: 5px solid #DC2626; }

    /* Semantic Signal Badges */
    .badge-buy {
        background: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.78rem;
        letter-spacing: 0.02em;
        display: inline-flex;
        align-items: center;
    }
    .badge-hold {
        background: #FFFBEB;
        color: #92400E;
        border: 1px solid #FDE68A;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.78rem;
        letter-spacing: 0.02em;
        display: inline-flex;
        align-items: center;
    }
    .badge-sell {
        background: #FEF2F2;
        color: #991B1B;
        border: 1px solid #FECACA;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.78rem;
        letter-spacing: 0.02em;
        display: inline-flex;
        align-items: center;
    }
    .badge-review {
        background: #F0F9FF;
        color: #075985;
        border: 1px solid #BAE6FD;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.78rem;
        letter-spacing: 0.02em;
        display: inline-flex;
        align-items: center;
    }

    /* High-contrast, sleek navigation tabs */
    button[data-baseweb="tab"] {
        background: transparent !important;
        color: #64748B !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 10px 18px !important;
        border-radius: 8px !important;
        margin-right: 6px !important;
        transition: all 0.15s ease !important;
        border: 1px solid transparent !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #2563EB !important;
        background: #F1F5F9 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #2563EB !important;
        background: #EFF6FF !important;
        border: 1px solid #BFDBFE !important;
        font-weight: 700 !important;
    }

    /* Primary buttons */
    .stButton>button[kind="primary"] {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 8px 18px !important;
        box-shadow: 0 1px 2px rgba(37, 99, 235, 0.2) !important;
        transition: all 0.15s ease !important;
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #1D4ED8 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }

    /* Clean banners */
    .zerodha-connect-banner {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 10px;
        padding: 16px 22px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 1px 2px rgba(37, 99, 235, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# 3. Environment & Engine Run (Executed before sidebar for live metrics)
env_file = Path(__file__).resolve().parent / '.env'
from dotenv import load_dotenv, set_key
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
            'error': ''
        }
    except Exception as exc:
        return {
            'status': 'expired',
            'is_live': False,
            'user_name': '',
            'user_id': '',
            'error': str(exc)
        }

kite_session = check_kite_session(curr_api_key, curr_access_token)
is_live = kite_session.get('is_live', False)
settings = Settings()
db = connect(settings.db)
custom_saved = get_custom_holdings(db)

@st.cache_data(ttl=900)
def load_report():
    return run()

try:
    report = load_report()
except Exception as exc:
    st.error(f"Cannot initialize portfolio advisor engine: {exc}")
    st.stop()

summary = report.get('portfolio_summary', {})
budget = report.get('budget', {})
holdings = report.get('holdings', [])
recommendations = report.get('recommendations', [])

# 4. Institutional Left Navigation Bar (Sidebar)
with st.sidebar:
    # A. Brand & Logo Header
    st.markdown("""
    <div class="sidebar-brand-wrapper">
        <div class="sidebar-kite-icon">
            <svg width="22" height="22" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M16 4L5 16L16 28L27 16L16 4Z" fill="#FFFFFF"/>
                <path d="M16 9.5L10 16L16 22.5L22 16L16 9.5Z" fill="#2563EB"/>
                <circle cx="16" cy="16" r="2.2" fill="#FFFFFF"/>
            </svg>
        </div>
        <div>
            <div class="sidebar-brand-title">ZERODHA <span style="color: #2563EB; font-weight: 500;">KITE</span></div>
            <div class="sidebar-brand-sub">Portfolio Advisor • v2.4</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # B. Account Connection Status Widget (Unified with Import Tab)
    custom_saved = get_custom_holdings(db)
    
    if kite_session['status'] == 'connected':
        status_title = "Kite Connect: Live Sync"
        user_info = f" · {kite_session['user_id']}" if kite_session.get('user_id') else ""
        status_sub = f"Authenticated{user_info} • Real-Time Stream"
        status_dot_class = "live-pulse"
        badge_text = "LIVE"
        card_bg = "#F0FDF4"
        card_border = "#BBF7D0"
        title_color = "#15803D"
        badge_bg = "#DCFCE7"
        badge_color = "#166534"
    elif kite_session['status'] == 'expired':
        status_title = "Kite: Session Expired"
        status_sub = "Token invalid • Re-login on Import tab"
        status_dot_class = "amber-dot"
        badge_text = "EXPIRED"
        card_bg = "#FFFBEB"
        card_border = "#FDE68A"
        title_color = "#B45309"
        badge_bg = "#FEF3C7"
        badge_color = "#92400E"
    elif custom_saved and len(custom_saved) > 0:
        status_title = "Zerodha Portfolio Active"
        status_sub = f"{len(custom_saved)} holdings imported & tracking"
        status_dot_class = "blue-pulse"
        badge_text = "SYNCED"
        card_bg = "#EFF6FF"
        card_border = "#BFDBFE"
        title_color = "#1D4ED8"
        badge_bg = "#DBEAFE"
        badge_color = "#1E40AF"
    else:
        status_title = "Simulation Demo Mode"
        status_sub = "Curated Indian benchmark stocks"
        status_dot_class = "amber-dot"
        badge_text = "DEMO"
        card_bg = "#FFFBEB"
        card_border = "#FDE68A"
        title_color = "#B45309"
        badge_bg = "#FEF3C7"
        badge_color = "#92400E"

    st.markdown(f"""
    <div class="sidebar-status-card" style="background: {card_bg}; border: 1px solid {card_border};">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 7px;">
                <span class="{status_dot_class}"></span>
                <span style="font-weight: 700; color: {title_color}; font-size: 0.82rem;">{status_title}</span>
            </div>
            <span class="sidebar-env-badge" style="background: {badge_bg}; color: {badge_color};">{badge_text}</span>
        </div>
        <div style="font-size: 0.72rem; color: #64748B; margin-top: 3px; padding-left: 15px;">{status_sub}</div>
    </div>
    """, unsafe_allow_html=True)

    # C. Soothing Refresh Action with Harmonious Matching Icon
    if st.button("Refresh Signals & Portfolio", key="refresh_portfolio_btn", icon=":material/refresh:", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # D. Portfolio Snapshot Mini-Card (Glanceable Summary)
    total_mkt = summary.get('total_market_value', 0.0)
    total_pnl = summary.get('total_unrealized_pnl', 0.0)
    total_pnl_pct = summary.get('total_pnl_percent', 0.0)
    holdings_cnt = summary.get('holdings_count', len(holdings))
    buy_cnt = summary.get('buy_count', 0)
    hold_cnt = summary.get('hold_count', 0)
    sell_cnt = summary.get('sell_count', 0) + summary.get('review_count', 0)

    is_pnl_pos = total_pnl >= 0
    pnl_sign = "+" if is_pnl_pos else ""
    pnl_pill_cls = "pnl-pill-profit" if is_pnl_pos else "pnl-pill-loss"

    total_mkt_fmt = format_inr(total_mkt)
    total_pnl_fmt = format_inr(total_pnl, show_plus=True)

    st.markdown(f"""
    <div class="sidebar-kpi-card">
        <div class="sidebar-kpi-header">
            <span>Portfolio Snapshot</span>
            <span style="background: #F1F5F9; color: #475569; padding: 2px 6px; border-radius: 4px;">{holdings_cnt} STOCKS</span>
        </div>
        <div class="sidebar-kpi-val">{total_mkt_fmt}</div>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 6px;">
            <span class="sidebar-pnl-pill {pnl_pill_cls}">
                {total_pnl_fmt} ({pnl_sign}{total_pnl_pct:.2f}%)
            </span>
            <span style="font-size: 0.72rem; color: #64748B; font-weight: 500;">Unrealized P&L</span>
        </div>
        <div class="sidebar-kpi-signals-row">
            <div class="sidebar-sig-badge sig-buy" title="Buy Candidates">
                <span class="sig-dot-buy"></span> <strong>{buy_cnt}</strong> Buy
            </div>
            <div class="sidebar-sig-badge sig-hold" title="Hold Positions">
                <span class="sig-dot-hold"></span> <strong>{hold_cnt}</strong> Hold
            </div>
            <div class="sidebar-sig-badge sig-sell" title="Review / Trim Triggers">
                <span class="sig-dot-sell"></span> <strong>{sell_cnt}</strong> Review
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # E. Monthly SIP Gross Budget Card
    today_str = datetime.now(IST).date().isoformat()
    spent_month = monthly_spend(db, today_str)
    rem_budget = max(0.0, settings.monthly_limit - spent_month)
    pct_spent = (spent_month / settings.monthly_limit * 100) if settings.monthly_limit > 0 else 0
    pct_clamped = min(100.0, max(0.0, pct_spent))

    limit_fmt = format_inr(settings.monthly_limit)
    spent_fmt = format_inr(spent_month)
    rem_budget_fmt = format_inr(rem_budget)

    if pct_spent < 50:
        budget_bar_bg = "linear-gradient(90deg, #10B981, #059669)"
        budget_tag = "✅ High budget headroom for buys"
    elif pct_spent < 85:
        budget_bar_bg = "linear-gradient(90deg, #F59E0B, #D97706)"
        budget_tag = "⚠️ Budget halfway deployed"
    else:
        budget_bar_bg = "linear-gradient(90deg, #EF4444, #DC2626)"
        budget_tag = "🛑 Near monthly budget cap"

    st.markdown(f"""
    <div class="sidebar-budget-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 0.70rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">
                Monthly SIP Budget
            </span>
            <span style="font-size: 0.72rem; font-weight: 700; color: #7C3AED; font-family: 'Plus Jakarta Sans', sans-serif; font-variant-numeric: tabular-nums;">
                {limit_fmt} CAP
            </span>
        </div>
        <div style="margin-top: 8px;">
            <div class="sidebar-budget-track">
                <div class="sidebar-budget-bar" style="width: {pct_clamped}%; background: {budget_bar_bg};"></div>
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 8px; font-size: 0.74rem;">
            <div>
                <span style="color: #64748B;">Spent:</span>
                <strong style="color: #0F172A; font-family: 'Plus Jakarta Sans', sans-serif; font-variant-numeric: tabular-nums; margin-left: 2px;">{spent_fmt}</strong>
            </div>
            <div>
                <span style="color: #64748B;">Available:</span>
                <strong style="color: #059669; font-family: 'Plus Jakarta Sans', sans-serif; font-variant-numeric: tabular-nums; margin-left: 2px;">{rem_budget_fmt}</strong>
            </div>
        </div>
        <div style="margin-top: 7px; font-size: 0.69rem; color: #475569; background: #F8FAFC; padding: 4px 8px; border-radius: 4px; text-align: center; border: 1px solid #F1F5F9;">
            {budget_tag}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # F. Collapsible Quick Trade Logger (Keeps left bar clean & uncluttered)
    with st.expander("📝 Record Executed Trade", expanded=False):
        st.caption("Record manual or offline purchases to deduct against your ₹50k monthly budget.")
        with st.form("quick_record_form"):
            trade_date = st.date_input("Trade Date", date.today())
            trade_sym = st.text_input("NSE Symbol", placeholder="e.g. INFY, HDFCBANK").strip().upper()
            trade_amt = st.number_input("Gross Consideration (₹)", min_value=0.0, step=1000.0, format="%.2f")
            submitted = st.form_submit_button("Record Purchase", use_container_width=True)
            if submitted:
                if not trade_sym or trade_amt <= 0:
                    st.error("Please enter a valid symbol and positive amount.")
                else:
                    add_purchase(db, trade_date.isoformat(), trade_sym, trade_amt)
                    st.success(f"Recorded ₹{trade_amt:,.0f} for {trade_sym}")
                    st.cache_data.clear()
                    st.rerun()

    # G. Secondary Actions / Footer
    if custom_saved:
        st.markdown("<div style='height: 2px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Reset to Demo Portfolio", use_container_width=True):
            clear_custom_holdings(db)
            st.cache_data.clear()
            st.success("Reset to demo portfolio!")
            st.rerun()

    st.markdown("""
    <div class="sidebar-security-footer">
        <div style="display: flex; align-items: center; justify-content: center; gap: 6px; color: #94A3B8; font-size: 0.72rem;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            <span>Read-Only Kite Access • Client Isolated</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 5. Header Title & Top Status Banners
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.markdown("""
    <h1 style="color: #0F172A; font-weight: 800; font-size: 2.1rem; margin-bottom: 2px;">
        Zerodha Long-Term Portfolio Advisor
    </h1>
    <p style="color: #64748B; font-size: 0.92rem; margin-top: 0;">
        Institutional Long-Term Equity Decision Support · Buy, Sell & Hold Signals · ₹50,000 Gross Monthly Budget Framework
    </p>
    """, unsafe_allow_html=True)

with header_col2:
    st.markdown(
        f"""
        <div style="text-align: right; padding-top: 14px;">
            <span style="background: #FFFFFF; border: 1px solid #E2E8F0; padding: 7px 14px; border-radius: 8px; font-size: 0.85rem; color: #334155; font-weight: 500;">
                📅 <b>{report['as_of']}</b> (IST) · <b>{len(holdings)} Stocks</b>
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

# Prominent Notice Banner if not on live Kite account
if not is_live and not custom_saved:
    st.markdown("""
    <div class="zerodha-connect-banner">
        <div>
            <span style="font-weight: 700; color: #1D4ED8; font-size: 0.95rem;">⚡ Ready to connect your actual Zerodha portfolio?</span>
            <span style="color: #1E40AF; font-size: 0.9rem; margin-left: 6px;">
                You are currently exploring sample demo data. You can connect your live Kite account or drag-and-drop your Zerodha CSV export in the <b>⚡ Zerodha Connect & Import</b> tab below!
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 6. Executive Metric Cards (Light Theme)
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_market = summary.get('total_market_value', 0.0)
total_invested = summary.get('total_invested_value', 0.0)
total_pnl = summary.get('total_unrealized_pnl', 0.0)
total_pnl_pct = summary.get('total_pnl_percent', 0.0)
pnl_color = "#059669" if total_pnl >= 0 else "#DC2626"
pnl_sign = "+" if total_pnl >= 0 else ""
pnl_card_class = "metric-card metric-card-profit" if total_pnl >= 0 else "metric-card metric-card-loss"

with kpi1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">💼 Portfolio Market Value</div>
        <div class="metric-value">{format_inr(total_market)}</div>
        <div class="metric-sub" style="color: #64748B;">
            Invested Capital: <b style="color: #334155;">{format_inr(total_invested)}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="{pnl_card_class}">
        <div class="metric-title">📈 Total Unrealized Return</div>
        <div class="metric-value" style="color: {pnl_color};">{format_inr(total_pnl, show_plus=True)}</div>
        <div class="metric-sub" style="color: {pnl_color}; font-weight: 700;">
            {pnl_sign}{total_pnl_pct:.2f}% Overall Return
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    spent = budget.get('spent', 0.0)
    limit = budget.get('monthly_limit', 50000.0)
    avail = max(0.0, limit - spent)
    st.markdown(f"""
    <div class="metric-card metric-card-budget">
        <div class="metric-title">💳 Gross Monthly Budget</div>
        <div class="metric-value">{format_inr(avail)}</div>
        <div class="metric-sub" style="color: #64748B;">
            Spent: <b style="color: #334155;">{format_inr(spent)}</b> of {format_inr(limit)} limit
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    bc = summary.get('buy_count', 0)
    hc = summary.get('hold_count', 0)
    sc = summary.get('sell_count', 0)
    rc = summary.get('review_count', 0)
    st.markdown(f"""
    <div class="metric-card metric-card-signals">
        <div class="metric-title">🎯 Advisory Decisions</div>
        <div class="metric-value" style="font-size: 1.55rem; display: flex; gap: 8px; align-items: center;">
            <span style="color:#059669;">{bc} BUY</span>
            <span style="color:#CBD5E1; font-weight:300;">|</span>
            <span style="color:#D97706;">{hc} HOLD</span>
            <span style="color:#CBD5E1; font-weight:300;">|</span>
            <span style="color:#DC2626;">{sc} SELL</span>
        </div>
        <div class="metric-sub" style="color: #64748B;">
            {rc} pending data · 100% quantitative signals
        </div>
    </div>
    """, unsafe_allow_html=True)

# Important warnings/alerts bar
if report.get('warnings'):
    with st.expander(f"⚠️ Risk & Concentration Alerts ({len(report['warnings'])})", expanded=False):
        for w in report['warnings']:
            st.markdown(f"- {w}")

# 7. Main Navigation Tabs (High Visibility & Clear Order)
tabs = st.tabs([
    "📊 Portfolio Overview",
    "🎯 Advisor Recommendations",
    "🔍 Stock Research Studio",
    "💰 Monthly Budget & Plan",
    "⚡ Zerodha Connect & Import",
    "🔭 Discovery Screener",
    "📖 Strategy Framework"
])

# ==========================================
# TAB 1: PORTFOLIO OVERVIEW
# ==========================================
with tabs[0]:
    st.subheader("Portfolio Composition & Performance")
    
    # Visual View Selector
    c_col1, c_col2 = st.columns([3, 2])
    with c_col1:
        st.caption("Visual asset allocation, sector risk concentration, and unrealized return heatmap.")
    with c_col2:
        overview_mode = st.radio(
            "Visualization Perspective:",
            ["🗺️ Market Heatmap & Treemap", "🍩 Stock Allocation & Sector Cap (25%)", "📊 Profit & Loss Ranking"],
            horizontal=True
        )

    if "Heatmap" in overview_mode:
        st.plotly_chart(plot_holdings_treemap(holdings), use_container_width=True)
    elif "Stock Allocation" in overview_mode:
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.plotly_chart(plot_portfolio_allocation(holdings), use_container_width=True)
        with col_chart2:
            st.plotly_chart(plot_sector_exposure_chart(holdings, settings.max_sector_weight), use_container_width=True)
    else:
        col_pnl1, col_pnl2 = st.columns([3, 2])
        with col_pnl1:
            st.plotly_chart(plot_holdings_pnl(holdings), use_container_width=True)
        with col_pnl2:
            st.plotly_chart(plot_sector_exposure_chart(holdings, settings.max_sector_weight), use_container_width=True)

    st.subheader("Holdings Detail & Real-Time Signals")
    if holdings:
        hdf = pd.DataFrame(holdings)
        display_cols = ['symbol', 'sector', 'quantity', 'average_price', 'price', 'market_value', 'unrealized_pnl', 'pnl_percent', 'weight', 'action', 'score']
        avail_cols = [c for c in display_cols if c in hdf.columns]
        
        table_df = hdf[avail_cols].copy()
        table_df.columns = [
            'Symbol', 'Sector', 'Quantity', 'Avg Cost (₹)', 'LTP (₹)',
            'Cur Value (₹)', 'Unrealized P&L (₹)', 'Return (%)', 'Weight (%)', 'Signal', 'Score'
        ]
        
        # Color formatted display
        st.dataframe(
            table_df.style.format({
                'Quantity': lambda x: f"{x:,.0f}" if pd.notnull(x) and x is not None else "-",
                'Avg Cost (₹)': lambda x: format_inr(x, decimals=2) if pd.notnull(x) and x is not None else "-",
                'LTP (₹)': lambda x: format_inr(x, decimals=2) if pd.notnull(x) and x is not None else "-",
                'Cur Value (₹)': lambda x: format_inr(x, decimals=2) if pd.notnull(x) and x is not None else "-",
                'Unrealized P&L (₹)': lambda x: format_inr(x, decimals=2, show_plus=True) if pd.notnull(x) and x is not None else "-",
                'Return (%)': lambda x: f"{x:+.2f}%" if pd.notnull(x) and x is not None else "-",
                'Weight (%)': lambda x: f"{x:.2f}%" if pd.notnull(x) and x is not None else "-",
                'Score': lambda x: f"{x:.1f}" if pd.notnull(x) and x is not None else "Pending"
            }).map(
                lambda val: 'color: #059669; font-weight: bold;' if str(val).startswith('+')
                else ('color: #DC2626; font-weight: bold;' if str(val).startswith('-') else ''),
                subset=['Return (%)']
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No holdings in portfolio yet. Connect to Zerodha or upload your CSV in the '⚡ Zerodha Connect & Import' tab.")

    st.markdown("---")
    st.subheader("Portfolio Diagnostics & Health Metrics")
    diag1, diag2, diag3, diag4 = st.columns(4)
    avg_qs = summary.get('average_quality_score')
    diag1.metric("Weighted Quality Score", f"{avg_qs:.1f} / 100" if avg_qs is not None else "N/A")
    w_pe = summary.get('weighted_pe')
    diag2.metric("Weighted Portfolio P/E", f"{w_pe:.1f}x" if w_pe is not None else "N/A")
    w_roe = summary.get('weighted_roe')
    diag3.metric("Weighted Portfolio ROE", f"{w_roe:.1f}%" if w_roe is not None else "N/A")
    max_stock = max((h.get('weight', 0.0) for h in holdings), default=0.0)
    diag4.metric("Largest Stock Concentration", f"{max_stock:.1f}%", help="Guideline: Keep below 10% for individual stocks")

# ==========================================
# TAB 2: ADVISOR RECOMMENDATIONS
# ==========================================
with tabs[1]:
    st.subheader("Actionable Long-Term Recommendations")
    st.caption("Institutional research signals synthesized across Quality, Valuation, Trend, and Growth metrics. Includes thesis-break sell protection.")

    owned_recs = [r for r in recommendations if r.get('owned')]
    
    # Filter and Sort controls
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([3, 2, 1])
    with ctrl_col1:
        filter_choice = st.radio(
            "Filter by Action:",
            ["All Holdings", "🟢 BUY Candidates", "🟡 HOLD Positions", "🔴 SELL / Profit-Taking"],
            horizontal=True
        )
    with ctrl_col2:
        sort_choice = st.selectbox(
            "Sort by Score / Priority:",
            [
                "Highest Score (Best Quality First)",
                "Lowest Score (Underperformers First)",
                "Highest Portfolio Weight (%)",
                "Highest Unrealized Return (%)",
                "Lowest Unrealized Return (%)",
                "Symbol (A-Z)"
            ],
            index=0
        )
    with ctrl_col3:
        view_mode = st.radio("View Layout:", ["Cards", "Table"], horizontal=True)

    if filter_choice == "🟢 BUY Candidates":
        filtered_recs = [r for r in owned_recs if r['action'] == 'BUY']
    elif filter_choice == "🟡 HOLD Positions":
        filtered_recs = [r for r in owned_recs if r['action'] == 'HOLD']
    elif filter_choice == "🔴 SELL / Profit-Taking":
        filtered_recs = [r for r in owned_recs if r['action'] == 'SELL']
    else:
        filtered_recs = list(owned_recs)

    # Sort based on selected option (safe against None scores)
    if "Highest Score" in sort_choice:
        filtered_recs = sorted(filtered_recs, key=lambda x: (x.get('score') is not None, x.get('score') or 0.0), reverse=True)
    elif "Lowest Score" in sort_choice:
        filtered_recs = sorted(filtered_recs, key=lambda x: (x.get('score') is None, x.get('score') if x.get('score') is not None else 999.0))
    elif "Highest Portfolio Weight" in sort_choice:
        filtered_recs = sorted(filtered_recs, key=lambda x: x.get('weight') or 0.0, reverse=True)
    elif "Highest Unrealized Return" in sort_choice:
        filtered_recs = sorted(filtered_recs, key=lambda x: x.get('pnl_percent') or 0.0, reverse=True)
    elif "Lowest Unrealized Return" in sort_choice:
        filtered_recs = sorted(filtered_recs, key=lambda x: x.get('pnl_percent') or 0.0)
    elif "Symbol" in sort_choice:
        filtered_recs = sorted(filtered_recs, key=lambda x: x.get('symbol', ''))

    st.caption(f"Showing **{len(filtered_recs)}** holdings · Sorted by: **{sort_choice}**")

    if not filtered_recs:
        st.info(f"No holdings match the filter: {filter_choice}")

    if view_mode == "Table" and filtered_recs:
        rec_table_df = pd.DataFrame([
            {
                'Symbol': r['symbol'],
                'Sector': r.get('sector', 'Unknown'),
                'Score': r.get('score'),
                'Signal': r.get('action_label', r['action']),
                'LTP (₹)': r.get('price'),
                'Return (%)': r.get('pnl_percent'),
                'Weight (%)': r.get('weight'),
                'Rationale': r.get('reason', '')
            }
            for r in filtered_recs
        ])
        st.dataframe(
            rec_table_df.style.format({
                'Score': lambda x: f"{x:.1f}" if pd.notnull(x) and x is not None else "Pending",
                'LTP (₹)': lambda x: format_inr(x, decimals=2) if pd.notnull(x) and x is not None else "-",
                'Return (%)': lambda x: f"{x:+.2f}%" if pd.notnull(x) and x is not None else "-",
                'Weight (%)': lambda x: f"{x:.2f}%" if pd.notnull(x) and x is not None else "-"
            }).map(
                lambda val: 'color: #059669; font-weight: bold;' if str(val).startswith('+')
                else ('color: #DC2626; font-weight: bold;' if str(val).startswith('-') else ''),
                subset=['Return (%)']
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        for r in filtered_recs:
            sym = r['symbol']
            act = r['action']
            act_label = r.get('action_label', act)
            score = r.get('score')
            score_display = f"{score:.1f}/100" if score is not None else "Pending Data"
            score_pct = float(score) if score is not None else 0.0
            reason = r.get('reason') or 'Under review'
            price = r.get('price') if r.get('price') is not None else 0.0
            pnl = r.get('unrealized_pnl') if r.get('unrealized_pnl') is not None else 0.0
            pnl_pct = r.get('pnl_percent') if r.get('pnl_percent') is not None else 0.0
            weight = r.get('weight') if r.get('weight') is not None else 0.0
            sec = r.get('sector') or 'Unknown'
            sma200 = r.get('sma200')
            
            card_class = f"rec-card-{act.lower()}"
            badge_class = f"badge-{act.lower()}"
            pnl_color = '#059669' if pnl >= 0 else '#DC2626'
            price_str = format_inr(price, decimals=2)
            pnl_str = format_inr(pnl, decimals=2, show_plus=True)
            
            score_color = '#059669' if score is not None and score >= 75 else ('#D97706' if score is not None and score >= 55 else '#DC2626')

            if sma200 and price:
                sma_diff = (price / sma200 - 1) * 100
                if sma_diff >= 0:
                    trend_tag = f"<span style='background:#ECFDF5; color:#065F46; border:1px solid #A7F3D0; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:600;'>📈 +{sma_diff:.1f}% vs 200 DMA</span>"
                else:
                    trend_tag = f"<span style='background:#FEF2F2; color:#991B1B; border:1px solid #FECACA; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:600;'>📉 {sma_diff:.1f}% vs 200 DMA</span>"
            else:
                trend_tag = ""

            card_html = textwrap.dedent(f"""
            <div class="{card_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                        <span style="font-size: 1.35rem; font-weight: 800; color: #0F172A; letter-spacing: -0.01em;">{sym}</span>
                        <span style="background: #F1F5F9; color: #475569; font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: 6px;">{sec}</span>
                        <span class="{badge_class}">{act_label}</span>
                        {trend_tag}
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 0.75rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; margin-right: 6px;">Quality Score:</span>
                        <span style="font-size: 1.3rem; font-weight: 800; color: {score_color}; font-family: 'Plus Jakarta Sans', sans-serif; font-variant-numeric: tabular-nums;">{score_display}</span>
                    </div>
                </div>
                <div style="background: #F1F5F9; border-radius: 9999px; height: 5px; width: 100%; overflow: hidden; margin-bottom: 12px;">
                    <div style="background: {score_color}; height: 100%; width: {score_pct}%; border-radius: 9999px;"></div>
                </div>
                <div style="display: flex; gap: 24px; font-size: 0.88rem; color: #64748B; margin-bottom: 10px; flex-wrap: wrap;">
                    <span>Current Price: <b style="color: #0F172A; font-family: 'Plus Jakarta Sans', sans-serif; font-variant-numeric: tabular-nums;">{price_str}</b></span>
                    <span>Unrealized Return: <b style="color: {pnl_color}; font-family: 'Plus Jakarta Sans', sans-serif; font-variant-numeric: tabular-nums;">{pnl_str} ({pnl_pct:+.1f}%)</b></span>
                    <span>Portfolio Weight: <b style="color: #0F172A; font-family: 'Plus Jakarta Sans', sans-serif; font-variant-numeric: tabular-nums;">{weight:.1f}%</b></span>
                </div>
                <div style="background: #F8FAFC; border-radius: 8px; padding: 10px 14px; border: 1px solid #F1F5F9;">
                    <p style="margin: 0; color: #334155; font-size: 0.9rem; line-height: 1.5;">
                        <b style="color: #0F172A;">Investment Rationale:</b> {reason}
                    </p>
                </div>
            </div>
            """).strip()
            st.markdown(card_html, unsafe_allow_html=True)

# ==========================================
# TAB 3: STOCK RESEARCH STUDIO
# ==========================================
with tabs[2]:
    st.subheader("Deep-Dive Stock Research Studio")
    
    all_sym_list = sorted(list({r['symbol'] for r in recommendations}))
    if all_sym_list:
        selected_stock = st.selectbox("Select Stock to Inspect:", all_sym_list, index=0)
        stock_rec = next((r for r in recommendations if r['symbol'] == selected_stock), None)
        
        if stock_rec:
            # Top stock banner
            s_col1, s_col2, s_col3, s_col4 = st.columns(4)
            s_price = stock_rec.get('price') if stock_rec.get('price') is not None else 0.0
            s_act = stock_rec.get('action') or 'REVIEW'
            s_score = stock_rec.get('score')
            s_score_str = f"{s_score:.1f} / 100" if s_score is not None else "Pending Data"
            s_sma200 = stock_rec.get('sma200')
            sma_str = format_inr(s_sma200, decimals=2) if s_sma200 is not None else "N/A"
            sma_delta = f"{((s_price/s_sma200-1)*100):+.1f}% vs 200 DMA" if s_sma200 and s_price and s_sma200 > 0 else None
            
            s_col1.metric("Current Market Price", format_inr(s_price, decimals=2))
            s_col2.metric("Recommendation", stock_rec.get('action_label', s_act), help=stock_rec.get('reason'))
            s_col3.metric("Composite Quality Score", s_score_str)
            s_col4.metric("200-Day SMA Trend", sma_str, delta=sma_delta)

            # 52-Week Range Bar Widget
            p_file = Path("data/prices") / f"{selected_stock}.csv"
            if p_file.exists():
                pdf_hist = pd.read_csv(p_file)
                if 'close' in pdf_hist.columns and len(pdf_hist) > 0:
                    c_window = pdf_hist['close'].tail(252)
                    low_52w = float(c_window.min())
                    high_52w = float(c_window.max())
                else:
                    low_52w, high_52w = s_price * 0.8, s_price * 1.2
            else:
                low_52w, high_52w = s_price * 0.8, s_price * 1.2

            range_span = max(0.01, high_52w - low_52w)
            pos_pct = max(0.0, min(100.0, ((s_price - low_52w) / range_span) * 100.0))

            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px 22px; margin: 16px 0; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 0.8rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">52-Week Range Spectrum</span>
                    <span style="font-size: 0.85rem; font-weight: 700; color: #0F172A; font-family: 'Plus Jakarta Sans', sans-serif; font-variant-numeric: tabular-nums;">
                        LTP: {format_inr(s_price, decimals=2)} ({pos_pct:.1f}% of Range)
                    </span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; color: #64748B; margin-bottom: 6px;">
                    <span>52W Low: <b style="color: #0F172A; font-family: 'Plus Jakarta Sans', sans-serif; font-variant-numeric: tabular-nums;">{format_inr(low_52w, decimals=2)}</b></span>
                    <span>52W High: <b style="color: #0F172A; font-family: 'Plus Jakarta Sans', sans-serif; font-variant-numeric: tabular-nums;">{format_inr(high_52w, decimals=2)}</b></span>
                </div>
                <div style="background: #F1F5F9; border-radius: 9999px; height: 10px; width: 100%; position: relative; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #DC2626 0%, #D97706 50%, #059669 100%); height: 100%; width: 100%; opacity: 0.85;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #94A3B8; margin-top: 5px;">
                    <span>{((s_price/low_52w-1)*100):+.1f}% above 52W low</span>
                    <span>{((s_price/high_52w-1)*100):+.1f}% vs 52W high</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")
            # Charts row: Price Action + Radar Factor Scorecard
            c_left, c_right = st.columns([3, 2])
            with c_left:
                price_fig = plot_stock_price_history(selected_stock)
                if price_fig:
                    st.plotly_chart(price_fig, use_container_width=True)
                else:
                    st.info(f"Price chart data currently unavailable for {selected_stock}.")
            with c_right:
                scores_dict = stock_rec.get('scores', {})
                st.plotly_chart(plot_factor_radar(scores_dict), use_container_width=True)

            # Fundamentals Grid
            funds_info = stock_rec.get('fundamentals', {})
            st.subheader(f"Fundamental Scorecard — {selected_stock}")
            
            f1, f2, f3, f4, f5 = st.columns(5)
            f_pe = funds_info.get('pe')
            f_fair = funds_info.get('fair_pe')
            pe_delta = f"{((f_pe/f_fair-1)*100):+.1f}% vs Fair" if f_fair and f_pe and f_fair > 0 else None
            
            f1.metric("P/E Ratio", f"{f_pe:.1f}x" if f_pe is not None else "N/A", delta=pe_delta, delta_color="inverse")
            f2.metric("Fair Value P/E", f"{f_fair:.1f}x" if f_fair is not None else "N/A")
            f3.metric("Return on Equity (ROE)", f"{funds_info.get('roe'):.1f}%" if funds_info.get('roe') is not None else "N/A")
            f4.metric("Debt-to-Equity", f"{funds_info.get('debt_equity'):.2f}" if funds_info.get('debt_equity') is not None else "N/A")
            f5.metric("Earnings Growth", f"{funds_info.get('earnings_growth'):+.1f}%" if funds_info.get('earnings_growth') is not None else "N/A")

            # Thesis & Risk Narrative
            st.markdown("### 📝 Long-Term Thesis & Risk Diagnostics")
            t_box1, t_box2 = st.columns(2)
            with t_box1:
                sales_g = funds_info.get('sales_growth')
                sales_str = f"{sales_g:+.1f}%" if sales_g is not None else "N/A"
                st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
                    <h5 style="color: #0369A1; margin-top: 0; font-weight: 700;">📈 Investment Drivers</h5>
                    <p style="font-size: 0.9rem; margin-bottom: 5px; color: #334155;">• <b>Sector:</b> {stock_rec.get('sector') or 'Unknown'}</p>
                    <p style="font-size: 0.9rem; margin-bottom: 5px; color: #334155;">• <b>Long-term Trend:</b> {stock_rec.get('regime', 'N/A')}</p>
                    <p style="font-size: 0.9rem; margin-bottom: 5px; color: #334155;">• <b>Operating Cash Flow:</b> {'✅ Positive' if funds_info.get('cashflow_positive') else ('❌ Negative' if funds_info.get('cashflow_positive') is False else 'Pending Data')}</p>
                    <p style="font-size: 0.9rem; margin-bottom: 0; color: #334155;">• <b>Sales Growth YoY:</b> {sales_str}</p>
                </div>
                """, unsafe_allow_html=True)
            with t_box2:
                dd_val = stock_rec.get('drawdown_52w')
                dd_str = f"{dd_val*100:.1f}%" if dd_val is not None else "N/A"
                ret6_val = stock_rec.get('return_6m')
                ret6_str = f"{ret6_val*100:+.1f}%" if ret6_val is not None else "N/A"
                mult_str = f"{f_pe/f_fair:.2f}x of fair price" if f_pe and f_fair and f_fair > 0 else "N/A"
                st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
                    <h5 style="color: #D97706; margin-top: 0; font-weight: 700;">⚠️ Risk Factors & Thesis Check</h5>
                    <p style="font-size: 0.9rem; margin-bottom: 5px; color: #334155;">• <b>52-Week Drawdown:</b> {dd_str}</p>
                    <p style="font-size: 0.9rem; margin-bottom: 5px; color: #334155;">• <b>6-Month Return:</b> {ret6_str}</p>
                    <p style="font-size: 0.9rem; margin-bottom: 5px; color: #334155;">• <b>Valuation Multiplier:</b> {mult_str}</p>
                    <p style="font-size: 0.9rem; margin-bottom: 0; color: #334155;">• <b>Thesis Status:</b> {stock_rec.get('thesis_status') or 'Under Review'}</p>
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# TAB 4: MONTHLY BUDGET & PLAN
# ==========================================
with tabs[3]:
    st.subheader("Monthly Purchase Budget & Rebalancing Execution Plan")
    st.caption("Systematic ₹50,000 monthly capital deployment framework ensuring strict diversification and risk management.")

    b_col1, b_col2 = st.columns([1, 2])
    with b_col1:
        st.plotly_chart(plot_budget_gauge(budget.get('spent', 0.0), budget.get('monthly_limit', 50000.0)), use_container_width=True)
    with b_col2:
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 18px; margin-top: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
            <h4 style="margin-top:0; color: #0284C7;">Execution Principles:</h4>
            <p style="font-size:0.9rem; margin-bottom: 6px; color: #334155;">• <b>Budget Cap:</b> ₹50,000 gross consideration per IST calendar month.</p>
            <p style="font-size:0.9rem; margin-bottom: 6px; color: #334155;">• <b>Stock Cap:</b> Max 10% target weight per individual stock.</p>
            <p style="font-size:0.9rem; margin-bottom: 6px; color: #334155;">• <b>Sector Cap:</b> Max 25% target weight per sector.</p>
            <p style="font-size:0.9rem; margin-bottom: 0; color: #334155;">• <b>Capital Recycling:</b> Proceeds liberated from SELL recommendations can supplement deployment into top BUY compounders.</p>
        </div>
        """, unsafe_allow_html=True)

    # Visual capital flow waterfall bar chart
    st.plotly_chart(plot_capital_flow(budget), use_container_width=True)

    st.markdown("---")
    
    # 1. Recommended Buys Plan
    st.subheader("🟢 Proposed Buy Allocations (Within ₹50k Budget)")
    buys_list = budget.get('allocations', [])
    if buys_list:
        bdf = pd.DataFrame(buys_list)
        bdf_display = bdf[['symbol', 'sector', 'quantity', 'price', 'estimated_gross', 'action_label', 'reason']].copy()
        bdf_display.columns = ['Symbol', 'Sector', 'Shares to Buy', 'Indicative Price (₹)', 'Gross Investment (₹)', 'Action', 'Rationale']
        st.dataframe(
            bdf_display.style.format({
                'Shares to Buy': '{:,.0f}',
                'Indicative Price (₹)': lambda x: format_inr(x, decimals=2),
                'Gross Investment (₹)': lambda x: format_inr(x, decimals=2)
            }),
            use_container_width=True,
            hide_index=True
        )
        total_buy_spend = sum(b['estimated_gross'] for b in buys_list)
        st.success(f"Total Proposed Buys: **{format_inr(total_buy_spend, decimals=2)}** · Remaining Unallocated: **{format_inr(budget.get('unallocated', 0), decimals=2)}**")
    else:
        st.info("No new buy allocations proposed this month. Budget is either fully deployed or candidates exceed risk headroom.")

    # 2. Recommended Sells Plan
    st.markdown("---")
    st.subheader("🔴 Capital Harvesting — Recommended Sells & Trims")
    sells_list = budget.get('sells', [])
    if sells_list:
        sdf = pd.DataFrame(sells_list)
        sdf_display = sdf[['symbol', 'sector', 'quantity_held', 'quantity_to_sell', 'price', 'estimated_proceeds', 'unrealized_pnl', 'pnl_percent', 'action_label', 'reason']].copy()
        sdf_display.columns = ['Symbol', 'Sector', 'Qty Held', 'Qty to Sell', 'LTP (₹)', 'Est. Proceeds (₹)', 'Unrealized P&L (₹)', 'P&L (%)', 'Action', 'Exit Rationale']
        st.dataframe(
            sdf_display.style.format({
                'Qty Held': '{:,.0f}',
                'Qty to Sell': '{:,.0f}',
                'LTP (₹)': lambda x: format_inr(x, decimals=2),
                'Est. Proceeds (₹)': lambda x: format_inr(x, decimals=2),
                'Unrealized P&L (₹)': lambda x: format_inr(x, decimals=2, show_plus=True),
                'P&L (%)': '{:+.1f}%'
            }),
            use_container_width=True,
            hide_index=True
        )
        total_proceeds = sum(s['estimated_proceeds'] for s in sells_list)
        st.warning(f"Executing these recommended sales would liberate **{format_inr(total_proceeds, decimals=2)}** in gross capital for redeployment.")
    else:
        st.info("No holdings currently meet sell or profit-taking triggers.")

    # 3. Monthly Purchases Ledger Table
    st.markdown("---")
    st.subheader("📋 Executed Purchases Ledger (Current Month)")
    purchases = get_purchases(db, today_str[:7])
    if purchases:
        pdf = pd.DataFrame(purchases)
        pdf_display = pdf[['id', 'trade_date', 'symbol', 'gross_amount', 'source']].copy()
        pdf_display.columns = ['ID', 'Date', 'Symbol', 'Gross Amount (₹)', 'Source']
        st.dataframe(
            pdf_display.style.format({'Gross Amount (₹)': lambda x: format_inr(x, decimals=2)}),
            use_container_width=True,
            hide_index=True
        )
        
        # Delete purchase option
        p_ids = [p['id'] for p in purchases]
        del_col1, del_col2 = st.columns([2, 1])
        with del_col1:
            sel_del = st.selectbox("Delete mistake or duplicate entry:", p_ids, format_func=lambda x: f"ID {x} — {next(p['symbol'] for p in purchases if p['id']==x)} ({format_inr(next(p['gross_amount'] for p in purchases if p['id']==x))})")
        with del_col2:
            st.write("")
            st.write("")
            if st.button("Delete Entry", type="secondary"):
                delete_purchase(db, sel_del)
                st.success(f"Deleted purchase entry ID {sel_del}")
                st.cache_data.clear()
                st.rerun()
    else:
        st.info("No executed purchases recorded yet this month.")

# ==========================================
# TAB 5: ZERODHA CONNECT & IMPORT (PROMINENT!)
# ==========================================
with tabs[4]:
    st.markdown("""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 20px 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <h2 style="color: #0F172A; margin: 0 0 6px 0; font-size: 1.5rem; font-weight: 700;">
            ⚡ Zerodha Account Connection & Portfolio Import
        </h2>
        <p style="color: #64748B; margin: 0; font-size: 0.95rem;">
            Load your real stock holdings into the advisor using either <b>Direct Zerodha Kite API</b> or <b>1-Click CSV Upload</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    method_choice = st.radio(
        "Choose Connection Method:",
        ["Option 1: Connect via Zerodha Kite Connect API (Live Sync)", "Option 2: Upload Zerodha Holdings CSV (1-Click, No API needed)", "Option 3: Manually Add / Edit Stock Holdings"],
        horizontal=True
    )

    if "Option 1" in method_choice:
        st.markdown("### 🔌 Live Zerodha Kite Connect Integration")
        st.caption("Pull live holdings, average purchase costs, and real-time market LTP directly from your Zerodha account.")

        from kiteconnect import KiteConnect

        # Check if request_token in URL query parameters
        url_req_token = st.query_params.get("request_token", "")

        kc_col1, kc_col2 = st.columns(2)
        with kc_col1:
            st.markdown("#### Step 1: Your Kite API Credentials")
            kc_api_key = st.text_input("Kite API Key", value=curr_api_key, type="password", help="From developer console at developers.kite.trade").strip()
            kc_api_secret = st.text_input("Kite API Secret", value=curr_api_secret, type="password", help="API Secret corresponding to your API Key").strip()

            if kc_api_key:
                login_link = f"https://kite.zerodha.com/connect/login?v=3&api_key={kc_api_key}"
                st.markdown(f"""
                <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 14px; margin-top: 10px;">
                    <p style="margin:0; font-size: 0.9rem; color: #1E40AF;"><b>Log in to Zerodha:</b></p>
                    <a href="{login_link}" target="_blank" style="color: #2563EB; font-weight: bold; font-size: 1rem; text-decoration: underline;">
                        👉 Click here to Open Zerodha Kite Login Page
                    </a>
                    <p style="margin: 8px 0 0 0; font-size: 0.82rem; color: #64748B;">
                        After logging in with your Zerodha User ID, password & TOTP, copy the <code>request_token</code> from the redirected browser URL.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Enter your Kite API Key above to generate your unique login link.")

        with kc_col2:
            st.markdown("#### Step 2: Authenticate & Pull Real Holdings")
            kc_req_token = st.text_input("Request Token (from redirect URL)", value=url_req_token).strip()
            kc_acc_token = st.text_input("Or Direct Access Token (if already generated today)", value=curr_access_token, type="password").strip()

            st.write("")
            btn_connect = st.button("🚀 Connect to Zerodha & Fetch Actual Portfolio", type="primary", use_container_width=True)

            if btn_connect:
                if not kc_api_key:
                    st.error("Please enter your Kite API Key.")
                else:
                    try:
                        kite = KiteConnect(api_key=kc_api_key)
                        final_token = None

                        if kc_req_token:
                            if not kc_api_secret:
                                st.error("API Secret is required to exchange a request token.")
                            else:
                                with st.spinner("Exchanging token and connecting to Zerodha..."):
                                    session_data = kite.generate_session(kc_req_token, api_secret=kc_api_secret)
                                    final_token = session_data["access_token"]
                        elif kc_acc_token:
                            final_token = kc_acc_token

                        if final_token:
                            kite.set_access_token(final_token)
                            profile = kite.profile()
                            user_name = profile.get("user_name", "User")
                            user_id = profile.get("user_id", "")
                            st.success(f"Connected as **{user_name}** ({user_id})!")

                            raw_h = kite.holdings()
                            if not raw_h:
                                st.warning("Connected successfully, but your Zerodha account has 0 stock holdings.")
                            else:
                                parsed_records = []
                                for r in raw_h:
                                    sym = r.get('tradingsymbol')
                                    qty = float(r.get('quantity', 0))
                                    if qty <= 0:
                                        continue
                                    avg_p = float(r.get('average_price') or r.get('last_price') or 0.0)
                                    ltp = float(r.get('last_price') or avg_p)
                                    parsed_records.append({
                                        'symbol': sym,
                                        'quantity': qty,
                                        'average_price': avg_p,
                                        'price': ltp,
                                        'sector': 'Unknown'
                                    })

                                save_custom_holdings(db, parsed_records)
                                st.success(f"🎉 Successfully imported {len(parsed_records)} live holdings from your Zerodha account!")

                            # Save to .env and environment
                            if not env_file.exists():
                                env_file.write_text("")
                            set_key(str(env_file), "ADVISOR_MODE", "live")
                            set_key(str(env_file), "KITE_API_KEY", kc_api_key)
                            if kc_api_secret:
                                set_key(str(env_file), "KITE_API_SECRET", kc_api_secret)
                            set_key(str(env_file), "KITE_ACCESS_TOKEN", final_token)

                            os.environ["ADVISOR_MODE"] = "live"
                            os.environ["KITE_API_KEY"] = kc_api_key
                            if kc_api_secret:
                                os.environ["KITE_API_SECRET"] = kc_api_secret
                            os.environ["KITE_ACCESS_TOKEN"] = final_token
                            load_dotenv(dotenv_path=env_file, override=True)

                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Please provide either a Request Token or an Access Token.")
                    except Exception as e:
                        st.error(f"Zerodha Kite connection error: {e}")

        st.markdown("---")
        status_col1, status_col2 = st.columns([2, 1])
        with status_col1:
            if kite_session['status'] == 'connected':
                user_info = f" · Account: **{kite_session['user_name']}** ({kite_session['user_id']})" if kite_session.get('user_name') else ""
                st.success(f"🟢 **Kite Status: CONNECTED & LIVE**{user_info}")
            elif kite_session['status'] == 'expired':
                st.warning(f"🟡 **Kite Status: TOKEN EXPIRED OR INACTIVE** ({kite_session['error']}). Please re-authenticate above.")
            else:
                st.info("⚪ **Kite Status: NOT CONFIGURED**. (Using Demo Mode / Uploaded CSV)")

        with status_col2:
            if kite_session['status'] == 'connected':
                if st.button("🔄 Sync Live Holdings Now", key="sync_live_holdings_btn", use_container_width=True):
                    try:
                        k_test = KiteConnect(api_key=curr_api_key)
                        k_test.set_access_token(curr_access_token)
                        raw_h = k_test.holdings()
                        parsed_records = [
                            {
                                'symbol': r.get('tradingsymbol'),
                                'quantity': float(r.get('quantity', 0)),
                                'average_price': float(r.get('average_price') or r.get('last_price') or 0.0),
                                'price': float(r.get('last_price') or r.get('average_price') or 0.0),
                                'sector': 'Unknown'
                            }
                            for r in raw_h if float(r.get('quantity', 0)) > 0
                        ]
                        save_custom_holdings(db, parsed_records)
                        st.success(f"Synced {len(parsed_records)} live holdings from Zerodha!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Sync error: {e}")
            elif kite_session['status'] == 'expired':
                st.caption("⚠️ Please re-authenticate above with a valid token to enable live syncing.")

    elif "Option 2" in method_choice:
        st.markdown("### 📤 Upload Zerodha Holdings CSV (1-Click, No API key needed)")
        st.markdown("""
        **How to export your CSV in 10 seconds:**
        1. Open **[Zerodha Console](https://console.zerodha.com)** or **Kite Web**.
        2. Go to **Portfolio > Holdings**.
        3. Click **Download CSV**.
        4. Upload the file below:
        """)
        
        uploaded_file = st.file_uploader("Upload your Zerodha Holdings CSV", type=['csv'])
        if uploaded_file is not None:
            try:
                raw_df = pd.read_csv(uploaded_file)
                st.write("Detected Columns:", list(raw_df.columns))
                
                renames = {}
                for col in raw_df.columns:
                    c_lower = col.strip().lower()
                    if 'instrument' in c_lower or 'symbol' in c_lower or 'stock' in c_lower:
                        renames[col] = 'symbol'
                    elif 'qty' in c_lower or 'quantity' in c_lower:
                        renames[col] = 'quantity'
                    elif 'avg' in c_lower or 'cost' in c_lower:
                        renames[col] = 'average_price'
                    elif 'ltp' in c_lower or 'last' in c_lower or 'price' in c_lower:
                        renames[col] = 'price'
                    elif 'sector' in c_lower:
                        renames[col] = 'sector'
                        
                parsed_df = raw_df.rename(columns=renames)
                if 'symbol' in parsed_df and 'quantity' in parsed_df:
                    parsed_df['quantity'] = pd.to_numeric(parsed_df['quantity'], errors='coerce').fillna(0)
                    parsed_df = parsed_df[parsed_df['quantity'] > 0]
                    if 'average_price' not in parsed_df:
                        parsed_df['average_price'] = parsed_df.get('price', 0.0)
                    if 'sector' not in parsed_df:
                        parsed_df['sector'] = 'Unknown'
                        
                    st.write("Preview Parsed Holdings:")
                    st.dataframe(parsed_df[['symbol', 'quantity', 'average_price', 'sector']].head(8), use_container_width=True)
                    
                    if st.button("Apply Uploaded Zerodha Portfolio", type="primary"):
                        holdings_records = parsed_df.to_dict('records')
                        save_custom_holdings(db, holdings_records)
                        st.success(f"🎉 Successfully applied {len(holdings_records)} holdings from Zerodha CSV!")
                        st.cache_data.clear()
                        st.rerun()
                else:
                    st.error("Could not find 'Instrument' / 'symbol' and 'Qty' in the uploaded file.")
            except Exception as e:
                st.error(f"Error parsing uploaded CSV: {e}")

    else:
        st.markdown("### ✍️ Add / Edit Stock Holding Manually")
        with st.form("manual_holding_form"):
            man_sym = st.text_input("NSE Symbol (e.g. INFY, TCS, RELIANCE)").strip().upper()
            man_qty = st.number_input("Shares Owned", min_value=1, step=1, value=10)
            man_avg = st.number_input("Average Purchase Price (₹)", min_value=1.0, step=10.0, value=1500.0)
            man_sec = st.selectbox("Sector", ["Technology", "Banking", "Consumer", "Energy", "Industrials", "Auto", "Healthcare", "Unknown"])
            man_submit = st.form_submit_button("Add / Update Holding", type="primary")
            if man_submit:
                if not man_sym:
                    st.error("Please enter a valid stock symbol.")
                else:
                    curr_h = get_custom_holdings(db)
                    curr_dict = {h['symbol']: h for h in curr_h}
                    curr_dict[man_sym] = {
                        'symbol': man_sym,
                        'quantity': man_qty,
                        'average_price': man_avg,
                        'price': man_avg,
                        'sector': man_sec
                    }
                    save_custom_holdings(db, list(curr_dict.values()))
                    st.success(f"Added {man_sym} to holdings!")
                    st.cache_data.clear()
                    st.rerun()

# ==========================================
# TAB 6: DISCOVERY SCREENER
# ==========================================
with tabs[5]:
    st.subheader("Discovery Screener — Watchlist & New Opportunities")
    st.caption("Screen curated NSE equities not currently in your portfolio to identify high-conviction candidates for your monthly budget.")

    unowned_recs = [r for r in recommendations if not r.get('owned')]
    
    if unowned_recs:
        udf = pd.DataFrame(unowned_recs)
        
        # Sector filter
        sec_options = ["All Sectors"] + sorted(list(set(udf['sector'])))
        selected_sec = st.selectbox("Filter by Sector:", sec_options)
        
        if selected_sec != "All Sectors":
            udf = udf[udf['sector'] == selected_sec]

        udf = udf.sort_values('score', ascending=False)

        disc_table = udf[['symbol', 'sector', 'price', 'score', 'action', 'action_label', 'reason']].copy()
        disc_table.columns = ['Symbol', 'Sector', 'LTP (₹)', 'Score', 'Signal', 'Action', 'Investment Thesis']

        st.dataframe(
            disc_table.style.format({
                'LTP (₹)': lambda x: f"₹{x:,.2f}" if pd.notnull(x) and x is not None else "-",
                'Score': lambda x: f"{x:.1f}" if pd.notnull(x) and x is not None else "Pending"
            }),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.subheader("Risk vs. Momentum Matrix")
        st.plotly_chart(plot_risk_return(recommendations), use_container_width=True)
    else:
        st.info("All tracked universe stocks are currently owned in your portfolio.")

# ==========================================
# TAB 7: STRATEGY FRAMEWORK
# ==========================================
with tabs[6]:
    st.subheader("Long-Term Compounding Framework & Thesis Rules")
    
    st.markdown("""
    ### 🎯 Core Philosophy: Long-Term Horizon vs Intraday Trading
    Intraday trading suffers from high frictional drag: brokerage fees, STT, exchange turnover taxes, bid-ask spreads, and emotional burnout.
    This advisor is specifically engineered for **multi-year compounding** (1–5+ years horizon), focusing on businesses with high return on capital and reasonable valuations.

    ---

    ### ⚖️ Multi-Factor Evaluation Architecture (0–100 Score)
    Every stock is evaluated continuously across five distinct quantitative pillars:
    
    1. **Business Quality (35% Weight)**:
       - **Return on Equity (ROE)**: High ROE (target > 15–20%) indicates strong economic moat and pricing power.
       - **Financial Leverage**: Low Debt/Equity (< 0.8) for non-financials protects solvency across economic downturns.
       - **Operating Cash Flow**: Net operating cash flow must back reported GAAP profits.
       - **Financial Sector Model**: Banking and NBFC institutions use asset quality, ROA, and credit growth instead of traditional leverage.

    2. **Valuation Margin of Safety (25% Weight)**:
       - **Price-to-Earnings (P/E) vs. Fair P/E**: Discounts to fair historical multiples provide safety; multiples over 1.7x trigger profit-booking.

    3. **Long-Term Trend & Momentum (15% Weight)**:
       - **200-Day Simple Moving Average (200 DMA)**: The primary anchor of institutional long-term uptrends.
       - **50-Day Moving Average & 52-Week Range**: Identifies healthy consolidation vs structural trend breakdowns.

    4. **Growth Stability (15% Weight)**:
       - Combined sales growth and earnings growth YoY stability.

    5. **Diversification & Neutral Risk (10% Weight)**:
       - Systemic buffer to avoid single-factor bias.

    ---

    ### 🚦 Explicit Decision Triggers
    - **🟢 BUY / ACCUMULATE (Score >= 75–80)**:
      High quality compounder trading at fair/attractive price above 200 DMA. Deploy monthly budget incrementally.
    - **🟡 HOLD (Score 55–74)**:
      Business fundamentals remain robust. Valuation is fair. Let profits compound uninterrupted.
    - **🔴 SELL / PROFIT-TAKING (Valuation Bubble)**:
      P/E >= 1.7x Fair P/E. Lock in accumulated gains (e.g. trim 50%) before multiple contraction erodes returns.
    - **🔴 SELL / EXIT (Fundamental Thesis Break)**:
      Earnings contraction (< -10%), surging debt, or negative cash flow. Eliminate value traps immediately.
    """)
