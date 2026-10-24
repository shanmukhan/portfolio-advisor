"""Tab 1: Portfolio Composition & Performance View."""

from typing import Any, Dict, List
import pandas as pd
import streamlit as st

from advisor.charts import (
    plot_holdings_pnl,
    plot_holdings_treemap,
    plot_portfolio_allocation,
    plot_sector_exposure_chart,
)
from advisor.config import Settings
from advisor.formatters import format_inr


def render_portfolio_tab(
    holdings: List[Dict[str, Any]],
    summary: Dict[str, Any],
    settings: Settings,
) -> None:
    """Render Tab 1: Portfolio composition, charts, holdings table, and diagnostics."""
    st.subheader("Portfolio Composition & Performance")

    # Visual View Selector
    c_col1, c_col2 = st.columns([3, 2])
    with c_col1:
        st.caption("Visual asset allocation, sector risk concentration, and unrealized return heatmap.")
    with c_col2:
        overview_mode = st.radio(
            "Visualization Perspective:",
            ["🗺️ Market Heatmap & Treemap", "🍩 Stock Allocation & Sector Cap (25%)", "📊 Profit & Loss Ranking"],
            horizontal=True,
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
                'Score': lambda x: f"{x:.1f}" if pd.notnull(x) and x is not None else "Pending",
            }).map(
                lambda val: 'color: #059669; font-weight: bold;' if str(val).startswith('+')
                else ('color: #DC2626; font-weight: bold;' if str(val).startswith('-') else ''),
                subset=['Return (%)'],
            ),
            use_container_width=True,
            hide_index=True,
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
