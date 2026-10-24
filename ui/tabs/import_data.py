"""Tab 5: Zerodha Account Connection & Portfolio Import View."""

import os
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv, set_key
import pandas as pd
import streamlit as st

from advisor.broker import parse_kite_holdings
from advisor.storage import get_custom_holdings, save_custom_holdings, validate_symbol


def get_available_sectors() -> list:
    """Retrieve dynamic list of sectors from fundamentals data."""
    funds_path = Path(__file__).resolve().parent.parent.parent / "data" / "demo_fundamentals.csv"
    if funds_path.exists():
        try:
            sectors = sorted(list(set(pd.read_csv(funds_path)['sector'].dropna().astype(str).str.strip().tolist())))
            if "Unknown" not in sectors:
                sectors.append("Unknown")
            return sectors
        except Exception:
            pass
    return ["Auto", "Banking", "Commodities", "Consumer", "Defense", "Energy", "Financial Services", "Healthcare", "Industrials", "Metals", "Technology", "Telecom", "Unknown"]


def render_import_data_tab(
    db: Any,
    kite_session: Dict[str, Any],
    curr_api_key: str,
    curr_api_secret: str,
    curr_access_token: str,
    env_file: Path,
) -> None:
    """Render Tab 5: Connect Zerodha Kite API, upload CSV, or manual holdings entry."""
    st.markdown(
        """
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 20px 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <h2 style="color: #0F172A; margin: 0 0 6px 0; font-size: 1.5rem; font-weight: 700;">
                ⚡ Zerodha Account Connection & Portfolio Import
            </h2>
            <p style="color: #64748B; margin: 0; font-size: 0.95rem;">
                Load your real stock holdings into the advisor using either <b>Direct Zerodha Kite API</b> or <b>1-Click CSV Upload</b>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    method_choice = st.radio(
        "Choose Connection Method:",
        ["Option 1: Connect via Zerodha Kite Connect API (Live Sync)", "Option 2: Upload Zerodha Holdings CSV (1-Click, No API needed)", "Option 3: Manually Add / Edit Stock Holdings"],
        horizontal=True,
    )

    if "Option 1" in method_choice:
        st.markdown("### 🔌 Live Zerodha Kite Connect Integration")
        st.caption("Pull live holdings, average purchase costs, and real-time market LTP directly from your Zerodha account.")

        try:
            from kiteconnect import KiteConnect
        except ImportError:
            st.error("⚠️ The `kiteconnect` library is not installed in this environment. Run `pip install kiteconnect` to enable live Kite API integration.")
            return

        # Check if request_token in URL query parameters
        url_req_token = st.query_params.get("request_token", "")

        kc_col1, kc_col2 = st.columns(2)
        with kc_col1:
            st.markdown("#### Step 1: Your Kite API Credentials")
            kc_api_key = st.text_input("Kite API Key", value=curr_api_key, type="password", help="From developer console at developers.kite.trade").strip()
            kc_api_secret = st.text_input("Kite API Secret", value=curr_api_secret, type="password", help="API Secret corresponding to your API Key").strip()

            if kc_api_key:
                login_link = f"https://kite.zerodha.com/connect/login?v=3&api_key={kc_api_key}"
                st.markdown(
                    f"""
                    <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 14px; margin-top: 10px;">
                        <p style="margin:0; font-size: 0.9rem; color: #1E40AF;"><b>Log in to Zerodha:</b></p>
                        <a href="{login_link}" target="_blank" style="color: #2563EB; font-weight: bold; font-size: 1rem; text-decoration: underline;">
                            👉 Click here to Open Zerodha Kite Login Page
                        </a>
                        <p style="margin: 8px 0 0 0; font-size: 0.82rem; color: #64748B;">
                            After logging in with your Zerodha User ID, password & TOTP, copy the <code>request_token</code> from the redirected browser URL.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
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
                                parsed_records = parse_kite_holdings(raw_h)
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
            if kite_session.get('status') == 'connected':
                user_info = f" · Account: **{kite_session['user_name']}** ({kite_session['user_id']})" if kite_session.get('user_name') else ""
                st.success(f"🟢 **Kite Status: CONNECTED & LIVE**{user_info}")
            elif kite_session.get('status') == 'expired':
                st.warning(f"🟡 **Kite Status: TOKEN EXPIRED OR INACTIVE** ({kite_session['error']}). Please re-authenticate above.")
            else:
                st.info("⚪ **Kite Status: NOT CONFIGURED**. (Using Demo Mode / Uploaded CSV)")

        with status_col2:
            if kite_session.get('status') == 'connected':
                if st.button("🔄 Sync Live Holdings Now", key="sync_live_holdings_btn", use_container_width=True):
                    try:
                        k_test = KiteConnect(api_key=curr_api_key)
                        k_test.set_access_token(curr_access_token)
                        raw_h = k_test.holdings()
                        parsed_records = parse_kite_holdings(raw_h)
                        save_custom_holdings(db, parsed_records)
                        st.success(f"Synced {len(parsed_records)} live holdings from Zerodha!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Sync error: {e}")
            elif kite_session.get('status') == 'expired':
                st.caption("⚠️ Please re-authenticate above with a valid token to enable live syncing.")

    elif "Option 2" in method_choice:
        st.markdown("### 📤 Upload Zerodha Holdings CSV (1-Click, No API key needed)")
        st.markdown(
            """
            **How to export your CSV in 10 seconds:**
            1. Open **[Zerodha Console](https://console.zerodha.com)** or **Kite Web**.
            2. Go to **Portfolio > Holdings**.
            3. Click **Download CSV**.
            4. Upload the file below:
            """
        )

        uploaded_file = st.file_uploader("Upload your Zerodha Holdings CSV", type=['csv'])
        if uploaded_file is not None:
            try:
                raw_df = pd.read_csv(uploaded_file)
                st.write("Detected Columns:", list(raw_df.columns))

                renames = {}
                for col in raw_df.columns:
                    c_lower = str(col).strip().lower()
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
        available_sectors = get_available_sectors()
        with st.form("manual_holding_form"):
            man_sym = st.text_input("NSE Symbol (e.g. INFY, TCS, RELIANCE)").strip().upper()
            man_qty = st.number_input("Shares Owned", min_value=1, step=1, value=10)
            man_avg = st.number_input("Average Purchase Price (₹)", min_value=1.0, step=10.0, value=1500.0)
            man_sec = st.selectbox("Sector", available_sectors)
            man_submit = st.form_submit_button("Add / Update Holding", type="primary")
            if man_submit:
                if not man_sym:
                    st.error("Please enter a valid stock symbol.")
                else:
                    try:
                        clean_sym = validate_symbol(man_sym)
                        curr_h = get_custom_holdings(db)
                        curr_dict = {h['symbol']: h for h in curr_h}
                        curr_dict[clean_sym] = {
                            'symbol': clean_sym,
                            'quantity': man_qty,
                            'average_price': man_avg,
                            'price': man_avg,
                            'sector': man_sec,
                        }
                        save_custom_holdings(db, list(curr_dict.values()))
                        st.success(f"Added {clean_sym} to holdings!")
                        st.cache_data.clear()
                        st.rerun()
                    except ValueError as err:
                        st.error(f"Invalid symbol: {err}")
