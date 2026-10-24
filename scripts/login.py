"""Zerodha Kite Connect interactive login & portfolio sync assistant.
Exchanges request_token for access_token, writes to .env, and pulls actual live holdings.
"""
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv, set_key
from kiteconnect import KiteConnect
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / '.env'

def get_or_prompt(value, prompt_msg, default=''):
    if value:
        return value.strip()
    val = input(f"{prompt_msg} [{default}]: " if default else f"{prompt_msg}: ").strip()
    return val if val else default

def main():
    load_dotenv(ENV_PATH)
    parser = argparse.ArgumentParser(description="Zerodha Kite Connect Login & Portfolio Fetcher")
    parser.add_argument("--api-key", help="Kite Connect API Key")
    parser.add_argument("--api-secret", help="Kite Connect API Secret")
    parser.add_argument("--request-token", help="Request Token from login redirect URL")
    parser.add_argument("--access-token", help="Direct access token if already generated today")
    args = parser.parse_args()

    api_key = args.api_key or os.getenv("KITE_API_KEY", "")
    api_secret = args.api_secret or os.getenv("KITE_API_SECRET", "")
    access_token = args.access_token or os.getenv("KITE_ACCESS_TOKEN", "")

    print("\n" + "="*60)
    print("🔐 ZERODHA KITE CONNECT PORTFOLIO CONNECTOR")
    print("="*60)

    if not api_key:
        api_key = get_or_prompt("", "Enter your Kite Connect API Key")
    if not api_key:
        print("❌ Error: API Key is required.")
        sys.exit(1)

    kite = KiteConnect(api_key=api_key)

    # If access token is provided or already in .env, test it
    if access_token:
        print(f"\nTesting existing access token for API Key: {api_key[:4]}***")
        kite.set_access_token(access_token)
        try:
            profile = kite.profile()
            print(f"✅ Authenticated successfully as: {profile.get('user_name')} ({profile.get('user_id')})")
            fetch_and_save_holdings(kite)
            update_env(api_key, api_secret, access_token)
            return
        except Exception as e:
            print(f"⚠️ Existing access token is invalid or expired ({e}). Proceeding to new login session...")

    # Needs new login session
    if not api_secret:
        api_secret = get_or_prompt("", "Enter your Kite Connect API Secret")
    if not api_secret:
        print("❌ Error: API Secret is required to generate a session.")
        sys.exit(1)

    login_url = kite.login_url()
    print("\n👉 STEP 1: Open the following Zerodha Kite Login URL in your browser:")
    print("-" * 60)
    print(login_url)
    print("-" * 60)
    print("\nAfter logging in with your Zerodha User ID, Password & 2FA/TOTP,")
    print("your browser will redirect to a URL like:")
    print("  https://127.0.0.1:8501/?request_token=XXXXXX&action=login&status=success")
    print("Copy the 'request_token' parameter value from the URL.\n")

    request_token = args.request_token
    if not request_token:
        request_token = get_or_prompt("", "Paste the request_token from your browser URL")

    if not request_token:
        print("❌ Error: request_token is required.")
        sys.exit(1)

    print("\nExchanging request_token for Kite session access_token...")
    try:
        data = kite.generate_session(request_token, api_secret=api_secret)
        new_token = data["access_token"]
        kite.set_access_token(new_token)
        profile = kite.profile()
        print(f"✅ Connected to Zerodha! Logged in as: {profile.get('user_name')} ({profile.get('user_id')})")
        update_env(api_key, api_secret, new_token)
        fetch_and_save_holdings(kite)
    except Exception as e:
        print(f"❌ Failed to generate Kite session: {e}")
        sys.exit(1)

def update_env(api_key, api_secret, access_token):
    if not ENV_PATH.exists():
        ENV_PATH.write_text("")
    set_key(str(ENV_PATH), "ADVISOR_MODE", "live")
    set_key(str(ENV_PATH), "KITE_API_KEY", api_key)
    if api_secret:
        set_key(str(ENV_PATH), "KITE_API_SECRET", api_secret)
    set_key(str(ENV_PATH), "KITE_ACCESS_TOKEN", access_token)
    print("💾 Saved live credentials to .env (ADVISOR_MODE=live)")

def fetch_and_save_holdings(kite):
    print("\n📦 Fetching actual portfolio holdings from Zerodha...")
    try:
        raw_holdings = kite.holdings()
        print(f"Retrieved {len(raw_holdings)} holdings from Zerodha.")
        if not raw_holdings:
            print("Notice: Your Zerodha account currently has 0 stock holdings.")
            return

        # Standardized holdings parsing
        sys.path.insert(0, str(ROOT))
        from advisor.broker import parse_kite_holdings
        from advisor.storage import connect, save_custom_holdings
        from advisor.config import Settings

        db_records = parse_kite_holdings(raw_holdings)

        records = []
        for r in db_records:
            sym = r['symbol']
            qty = r['quantity']
            avg_p = r['average_price']
            ltp = r['price']
            pnl = (ltp - avg_p) * qty
            pnl_pct = (pnl / (avg_p * qty) * 100.0) if avg_p * qty > 0 else 0.0
            records.append({
                'Symbol': sym,
                'Quantity': qty,
                'Avg Cost (₹)': avg_p,
                'LTP (₹)': ltp,
                'Cur Value (₹)': round(qty * ltp, 2),
                'P&L (₹)': round(pnl, 2),
                'Return (%)': round(pnl_pct, 2)
            })

        df = pd.DataFrame(records)
        print("\n" + "="*70)
        print("📈 ACTUAL ZERODHA HOLDINGS:")
        print("="*70)
        print(df.to_string(index=False))
        print("="*70)

        # Save to database
        db = connect(Settings().db)
        try:
            save_custom_holdings(db, db_records)
            print("✅ Stored actual portfolio in local database. Streamlit dashboard is now live-synced!")
            print("Run 'streamlit run app.py' or refresh the dashboard to view your live advice!")
        finally:
            db.close()
    except Exception as e:
        print(f"❌ Error fetching holdings: {e}")

if __name__ == "__main__":
    main()
