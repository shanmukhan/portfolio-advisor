"""Tab 7: Long-Term Compounding Framework & Thesis Rules View."""

import streamlit as st


def render_strategy_tab() -> None:
    """Render Tab 7: Educational philosophy, multi-factor architecture, and decision triggers."""
    st.subheader("Long-Term Compounding Framework & Thesis Rules")

    st.markdown(
        """
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
        """
    )
