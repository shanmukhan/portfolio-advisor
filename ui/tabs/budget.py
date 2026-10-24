"""Tab 4: Monthly Budget & Rebalancing Execution Plan View."""

from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st

from advisor.charts import plot_budget_gauge, plot_capital_flow
from advisor.config import Settings
from advisor.formatters import format_inr
from advisor.storage import delete_purchase, get_purchases

IST = ZoneInfo('Asia/Kolkata')


def render_budget_tab(
    budget: Dict[str, Any],
    settings: Settings,
    db: Any,
) -> None:
    """Render Tab 4: Monthly budget tracking, allocations, sells, and purchases ledger."""
    limit_fmt = format_inr(settings.monthly_limit)
    st.subheader("Monthly Purchase Budget & Rebalancing Execution Plan")
    st.caption(f"Systematic {limit_fmt} monthly capital deployment framework ensuring strict diversification and risk management.")

    b_col1, b_col2 = st.columns([1, 2])
    with b_col1:
        st.plotly_chart(
            plot_budget_gauge(budget.get('spent', 0.0), budget.get('monthly_limit', settings.monthly_limit)),
            use_container_width=True,
        )
    with b_col2:
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 18px; margin-top: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                <h4 style="margin-top:0; color: #0284C7;">Execution Principles:</h4>
                <p style="font-size:0.9rem; margin-bottom: 6px; color: #334155;">• <b>Budget Cap:</b> {limit_fmt} gross consideration per IST calendar month.</p>
                <p style="font-size:0.9rem; margin-bottom: 6px; color: #334155;">• <b>Stock Cap:</b> Max {settings.max_stock_weight*100:.0f}% target weight per individual stock.</p>
                <p style="font-size:0.9rem; margin-bottom: 6px; color: #334155;">• <b>Sector Cap:</b> Max {settings.max_sector_weight*100:.0f}% target weight per sector.</p>
                <p style="font-size:0.9rem; margin-bottom: 0; color: #334155;">• <b>Capital Recycling:</b> Proceeds liberated from SELL recommendations can supplement deployment into top BUY compounders.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Visual capital flow waterfall bar chart
    st.plotly_chart(plot_capital_flow(budget), use_container_width=True)

    st.markdown("---")

    # 1. Recommended Buys Plan
    st.subheader(f"🟢 Proposed Buy Allocations (Within {limit_fmt} Budget)")
    buys_list = budget.get('allocations', [])
    if buys_list:
        bdf = pd.DataFrame(buys_list)
        bdf_display = bdf[['symbol', 'sector', 'quantity', 'price', 'estimated_gross', 'action_label', 'reason']].copy()
        bdf_display.columns = ['Symbol', 'Sector', 'Shares to Buy', 'Indicative Price (₹)', 'Gross Investment (₹)', 'Action', 'Rationale']
        st.dataframe(
            bdf_display.style.format({
                'Shares to Buy': '{:,.0f}',
                'Indicative Price (₹)': lambda x: format_inr(x, decimals=2),
                'Gross Investment (₹)': lambda x: format_inr(x, decimals=2),
            }),
            use_container_width=True,
            hide_index=True,
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
                'P&L (%)': '{:+.1f}%',
            }),
            use_container_width=True,
            hide_index=True,
        )
        total_proceeds = sum(s['estimated_proceeds'] for s in sells_list)
        st.warning(f"Executing these recommended sales would liberate **{format_inr(total_proceeds, decimals=2)}** in gross capital for redeployment.")
    else:
        st.info("No holdings currently meet sell or profit-taking triggers.")

    # 3. Monthly Purchases Ledger Table
    st.markdown("---")
    st.subheader("📋 Executed Purchases Ledger (Current Month)")
    today_str = datetime.now(IST).date().isoformat()
    purchases = get_purchases(db, today_str[:7])
    if purchases:
        pdf = pd.DataFrame(purchases)
        pdf_display = pdf[['id', 'trade_date', 'symbol', 'gross_amount', 'source']].copy()
        pdf_display.columns = ['ID', 'Date', 'Symbol', 'Gross Amount (₹)', 'Source']
        st.dataframe(
            pdf_display.style.format({'Gross Amount (₹)': lambda x: format_inr(x, decimals=2)}),
            use_container_width=True,
            hide_index=True,
        )

        # Delete purchase option
        p_ids = [p['id'] for p in purchases]
        del_col1, del_col2 = st.columns([2, 1])
        with del_col1:
            sel_del = st.selectbox(
                "Delete mistake or duplicate entry:",
                p_ids,
                format_func=lambda x: f"ID {x} — {next(p['symbol'] for p in purchases if p['id']==x)} ({format_inr(next(p['gross_amount'] for p in purchases if p['id']==x))})",
            )
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
