"""Tab 2: Advisor Recommendations View."""

from typing import Any, Dict, List
import pandas as pd
import streamlit as st

from advisor.formatters import format_inr
from ui.components import render_recommendation_card


def render_recommendations_tab(recommendations: List[Dict[str, Any]]) -> None:
    """Render Tab 2: Filterable and sortable recommendation cards or table."""
    st.subheader("Actionable Long-Term Recommendations")
    st.caption("Institutional research signals synthesized across Quality, Valuation, Trend, and Growth metrics. Includes thesis-break sell protection.")

    owned_recs = [r for r in recommendations if r.get('owned')]

    # Filter and Sort controls
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([3, 2, 1])
    with ctrl_col1:
        filter_choice = st.radio(
            "Filter by Action:",
            ["All Holdings", "🟢 BUY Candidates", "🟡 HOLD Positions", "🔴 SELL / Profit-Taking"],
            horizontal=True,
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
                "Symbol (A-Z)",
            ],
            index=0,
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
                'Rationale': r.get('reason', ''),
            }
            for r in filtered_recs
        ])
        st.dataframe(
            rec_table_df.style.format({
                'Score': lambda x: f"{x:.1f}" if pd.notnull(x) and x is not None else "Pending",
                'LTP (₹)': lambda x: format_inr(x, decimals=2) if pd.notnull(x) and x is not None else "-",
                'Return (%)': lambda x: f"{x:+.2f}%" if pd.notnull(x) and x is not None else "-",
                'Weight (%)': lambda x: f"{x:.2f}%" if pd.notnull(x) and x is not None else "-",
            }).map(
                lambda val: 'color: #059669; font-weight: bold;' if str(val).startswith('+')
                else ('color: #DC2626; font-weight: bold;' if str(val).startswith('-') else ''),
                subset=['Return (%)'],
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        for r in filtered_recs:
            render_recommendation_card(r)
