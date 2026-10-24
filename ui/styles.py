"""Global CSS themes and layout styles for Zerodha Portfolio Advisor."""

import streamlit as st

APP_CSS = """
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
"""


def apply_styles() -> None:
    """Inject application global CSS into current Streamlit session."""
    st.markdown(APP_CSS, unsafe_allow_html=True)
