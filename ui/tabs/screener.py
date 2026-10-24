"""Tab 6: Discovery Screener & Risk/Momentum Matrix View."""

from typing import Any, Dict, List
import pandas as pd
import streamlit as st

from advisor.charts import plot_risk_return


def render_screener_tab(recommendations: List[Dict[str, Any]]) -> None:
    """Render Tab 6: Watchlist screener and risk-return matrix for unowned stocks."""
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
                'Score': lambda x: f"{x:.1f}" if pd.notnull(x) and x is not None else "Pending",
            }),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")
        st.subheader("Risk vs. Momentum Matrix")
        st.plotly_chart(plot_risk_return(recommendations), use_container_width=True)
    else:
        st.info("All tracked universe stocks are currently owned in your portfolio.")
