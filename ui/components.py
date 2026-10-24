"""Reusable UI HTML component builders with automatic HTML sanitization."""

import html
import textwrap
from typing import Any, Dict, Optional
import streamlit as st

from advisor.formatters import format_inr


def escape_html(val: Any) -> str:
    """Sanitize and escape user or external data to prevent XSS in HTML blocks."""
    if val is None:
        return ""
    return html.escape(str(val))


def render_header(as_of: str, holdings_count: int, monthly_limit: float = 50000.0) -> None:
    """Render top page title and status header."""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f"""
            <h1 style="color: #0F172A; font-weight: 800; font-size: 2.1rem; margin-bottom: 2px;">
                Zerodha Long-Term Portfolio Advisor
            </h1>
            <p style="color: #64748B; font-size: 0.92rem; margin-top: 0;">
                Institutional Long-Term Equity Decision Support · Buy, Sell & Hold Signals · {format_inr(monthly_limit)} Gross Monthly Budget Framework
            </p>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        clean_as_of = escape_html(as_of)
        st.markdown(
            f"""
            <div style="text-align: right; padding-top: 14px;">
                <span style="background: #FFFFFF; border: 1px solid #E2E8F0; padding: 7px 14px; border-radius: 8px; font-size: 0.85rem; color: #334155; font-weight: 500;">
                    📅 <b>{clean_as_of}</b> (IST) · <b>{holdings_count} Stocks</b>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_kpi_cards(summary: Dict[str, Any], budget: Dict[str, Any]) -> None:
    """Render top 4 executive KPI metric cards."""
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    total_market = summary.get('total_market_value', 0.0)
    total_invested = summary.get('total_invested_value', 0.0)
    total_pnl = summary.get('total_unrealized_pnl', 0.0)
    total_pnl_pct = summary.get('total_pnl_percent', 0.0)
    pnl_color = "#059669" if total_pnl >= 0 else "#DC2626"
    pnl_sign = "+" if total_pnl >= 0 else ""
    pnl_card_class = "metric-card metric-card-profit" if total_pnl >= 0 else "metric-card metric-card-loss"

    with kpi1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">💼 Portfolio Market Value</div>
                <div class="metric-value">{format_inr(total_market)}</div>
                <div class="metric-sub" style="color: #64748B;">
                    Invested Capital: <b style="color: #334155;">{format_inr(total_invested)}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi2:
        st.markdown(
            f"""
            <div class="{pnl_card_class}">
                <div class="metric-title">📈 Total Unrealized Return</div>
                <div class="metric-value" style="color: {pnl_color};">{format_inr(total_pnl, show_plus=True)}</div>
                <div class="metric-sub" style="color: {pnl_color}; font-weight: 700;">
                    {pnl_sign}{total_pnl_pct:.2f}% Overall Return
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi3:
        spent = budget.get('spent', 0.0)
        limit = budget.get('monthly_limit', 50000.0)
        avail = max(0.0, limit - spent)
        st.markdown(
            f"""
            <div class="metric-card metric-card-budget">
                <div class="metric-title">💳 Gross Monthly Budget</div>
                <div class="metric-value">{format_inr(avail)}</div>
                <div class="metric-sub" style="color: #64748B;">
                    Spent: <b style="color: #334155;">{format_inr(spent)}</b> of {format_inr(limit)} limit
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi4:
        bc = summary.get('buy_count', 0)
        hc = summary.get('hold_count', 0)
        sc = summary.get('sell_count', 0)
        rc = summary.get('review_count', 0)
        st.markdown(
            f"""
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
            """,
            unsafe_allow_html=True,
        )


def render_recommendation_card(r: Dict[str, Any]) -> None:
    """Render a sanitized recommendation card for a stock."""
    sym = escape_html(r['symbol'])
    act = escape_html(r['action'])
    act_label = escape_html(r.get('action_label', act))
    sec = escape_html(r.get('sector') or 'Unknown')
    reason = escape_html(r.get('reason') or 'Under review')

    score = r.get('score')
    score_display = f"{score:.1f}/100" if score is not None else "Pending Data"
    score_pct = float(score) if score is not None else 0.0

    price = float(r.get('price', 0.0) or 0.0)
    pnl = float(r.get('unrealized_pnl', 0.0) or 0.0)
    pnl_pct = float(r.get('pnl_percent', 0.0) or 0.0)
    weight = float(r.get('weight', 0.0) or 0.0)
    sma200 = r.get('sma200')

    card_class = f"rec-card-{r['action'].lower()}"
    badge_class = f"badge-{r['action'].lower()}"
    pnl_color = '#059669' if pnl >= 0 else '#DC2626'
    price_str = format_inr(price, decimals=2)
    pnl_str = format_inr(pnl, decimals=2, show_plus=True)

    score_color = (
        '#059669' if score is not None and score >= 75
        else ('#D97706' if score is not None and score >= 55 else '#DC2626')
    )

    if sma200 and price:
        sma_diff = (price / float(sma200) - 1) * 100
        if sma_diff >= 0:
            trend_tag = (
                f"<span style='background:#ECFDF5; color:#065F46; border:1px solid #A7F3D0; "
                f"padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:600;'>"
                f"📈 +{sma_diff:.1f}% vs 200 DMA</span>"
            )
        else:
            trend_tag = (
                f"<span style='background:#FEF2F2; color:#991B1B; border:1px solid #FECACA; "
                f"padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:600;'>"
                f"📉 {sma_diff:.1f}% vs 200 DMA</span>"
            )
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
