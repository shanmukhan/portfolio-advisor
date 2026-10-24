"""Sidebar navigation, account status, glanceable metrics, and quick trade entry."""

from datetime import date, datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo
import streamlit as st

from advisor.config import Settings
from advisor.formatters import format_inr
from advisor.storage import add_purchase, clear_custom_holdings, get_custom_holdings, monthly_spend

IST = ZoneInfo('Asia/Kolkata')


def render_sidebar(
    report: Dict[str, Any],
    settings: Settings,
    db: Any,
    kite_session: Dict[str, Any],
) -> None:
    """Render the full left sidebar navigation, account widget, metrics, and actions."""
    summary = report.get('portfolio_summary', {})
    holdings = report.get('holdings', [])

    with st.sidebar:
        # A. Brand & Logo Header
        st.markdown(
            """
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
            """,
            unsafe_allow_html=True,
        )

        # B. Account Connection Status Widget
        custom_saved = get_custom_holdings(db)

        if kite_session.get('status') == 'connected':
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
        elif kite_session.get('status') == 'expired':
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

        st.markdown(
            f"""
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
            """,
            unsafe_allow_html=True,
        )

        # C. Refresh Button
        if st.button("Refresh Signals & Portfolio", key="refresh_portfolio_btn", icon=":material/refresh:", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        # D. Portfolio Snapshot Mini-Card
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

        st.markdown(
            f"""
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
            """,
            unsafe_allow_html=True,
        )

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

        st.markdown(
            f"""
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
            """,
            unsafe_allow_html=True,
        )

        # F. Collapsible Quick Trade Logger
        with st.expander("📝 Record Executed Trade", expanded=False):
            st.caption(f"Record manual or offline purchases to deduct against your {limit_fmt} monthly budget.")
            with st.form("quick_record_form"):
                trade_date = st.date_input("Trade Date", date.today())
                trade_sym = st.text_input("NSE Symbol", placeholder="e.g. INFY, HDFCBANK").strip().upper()
                trade_amt = st.number_input("Gross Consideration (₹)", min_value=0.0, step=1000.0, format="%.2f")
                submitted = st.form_submit_button("Record Purchase", use_container_width=True)
                if submitted:
                    if not trade_sym or trade_amt <= 0:
                        st.error("Please enter a valid symbol and positive amount.")
                    else:
                        try:
                            add_purchase(db, trade_date.isoformat(), trade_sym, trade_amt)
                            st.success(f"Recorded ₹{trade_amt:,.0f} for {trade_sym}")
                            st.cache_data.clear()
                            st.rerun()
                        except ValueError as err:
                            st.error(f"Validation error: {err}")

        # G. Reset Action
        if custom_saved:
            st.markdown("<div style='height: 2px;'></div>", unsafe_allow_html=True)
            if st.button("🗑️ Reset to Demo Portfolio", use_container_width=True):
                clear_custom_holdings(db)
                st.cache_data.clear()
                st.success("Reset to demo portfolio!")
                st.rerun()

        st.markdown(
            """
            <div class="sidebar-security-footer">
                <div style="display: flex; align-items: center; justify-content: center; gap: 6px; color: #94A3B8; font-size: 0.72rem;">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                    </svg>
                    <span>Read-Only Kite Access • Client Isolated</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
