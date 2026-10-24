"""Tab 3: Stock Research Studio View."""

from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
import streamlit as st

from advisor.charts import plot_factor_radar, plot_stock_price_history
from advisor.formatters import format_inr
from ui.components import escape_html


def render_research_tab(recommendations: List[Dict[str, Any]]) -> None:
    """Render Tab 3: Deep dive stock research, candlestick charts, and factor radar."""
    st.subheader("Deep-Dive Stock Research Studio")

    all_sym_list = sorted(list({r['symbol'] for r in recommendations}))
    if not all_sym_list:
        st.info("No stocks available in recommendation universe.")
        return

    selected_stock = st.selectbox("Select Stock to Inspect:", all_sym_list, index=0)
    stock_rec = next((r for r in recommendations if r['symbol'] == selected_stock), None)

    if not stock_rec:
        return

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
        try:
            pdf_hist = pd.read_csv(p_file)
            if 'close' in pdf_hist.columns and len(pdf_hist) > 0:
                c_window = pdf_hist['close'].tail(252)
                low_52w = float(c_window.min())
                high_52w = float(c_window.max())
            else:
                low_52w, high_52w = s_price * 0.8, s_price * 1.2
        except Exception:
            low_52w, high_52w = s_price * 0.8, s_price * 1.2
    else:
        low_52w, high_52w = s_price * 0.8, s_price * 1.2

    range_span = max(0.01, high_52w - low_52w)
    pos_pct = max(0.0, min(100.0, ((s_price - low_52w) / range_span) * 100.0))

    st.markdown(
        f"""
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
        """,
        unsafe_allow_html=True,
    )

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
    st.subheader(f"Fundamental Scorecard — {escape_html(selected_stock)}")

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
        sec_name = escape_html(stock_rec.get('sector') or 'Unknown')
        regime_name = escape_html(stock_rec.get('regime', 'N/A'))
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
                <h5 style="color: #0369A1; margin-top: 0; font-weight: 700;">📈 Investment Drivers</h5>
                <p style="font-size: 0.9rem; margin-bottom: 5px; color: #334155;">• <b>Sector:</b> {sec_name}</p>
                <p style="font-size: 0.9rem; margin-bottom: 5px; color: #334155;">• <b>Long-term Trend:</b> {regime_name}</p>
                <p style="font-size: 0.9rem; margin-bottom: 5px; color: #334155;">• <b>Operating Cash Flow:</b> {'✅ Positive' if funds_info.get('cashflow_positive') else ('❌ Negative' if funds_info.get('cashflow_positive') is False else 'Pending Data')}</p>
                <p style="font-size: 0.9rem; margin-bottom: 0; color: #334155;">• <b>Sales Growth YoY:</b> {sales_str}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with t_box2:
        dd_val = stock_rec.get('drawdown_52w')
        dd_str = f"{dd_val*100:.1f}%" if dd_val is not None else "N/A"
        ret6_val = stock_rec.get('return_6m')
        ret6_str = f"{ret6_val*100:+.1f}%" if ret6_val is not None else "N/A"
        mult_str = f"{f_pe/f_fair:.2f}x of fair price" if f_pe and f_fair and f_fair > 0 else "N/A"
        status_name = escape_html(stock_rec.get('thesis_status') or 'Under Review')
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
                <h5 style="color: #D97706; margin-top: 0; font-weight: 700;">⚠️ Risk Factors & Thesis Check</h5>
                <p style="font-size: 0.9rem; margin-bottom: 5px; color: #334155;">• <b>52-Week Drawdown:</b> {dd_str}</p>
                <p style="font-size: 0.9rem; margin-bottom: 5px; color: #334155;">• <b>6-Month Return:</b> {ret6_str}</p>
                <p style="font-size: 0.9rem; margin-bottom: 5px; color: #334155;">• <b>Valuation Multiplier:</b> {mult_str}</p>
                <p style="font-size: 0.9rem; margin-bottom: 0; color: #334155;">• <b>Thesis Status:</b> {status_name}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
