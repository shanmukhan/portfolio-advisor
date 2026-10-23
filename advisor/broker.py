"""Allowlisted Kite reads only. No order or position mutation methods exposed."""
import os

class KiteReadOnly:
    def __init__(self, api_key=None, access_token=None):
        from dotenv import load_dotenv
        load_dotenv(override=True)
        from kiteconnect import KiteConnect
        key = api_key or os.getenv('KITE_API_KEY', '')
        token = access_token or os.getenv('KITE_ACCESS_TOKEN', '')
        if not key or not token:
            raise RuntimeError('Set KITE_API_KEY and KITE_ACCESS_TOKEN in .env or via settings')
        self._kite = KiteConnect(api_key=key)
        self._kite.set_access_token(token)

    def holdings(self):
        return self._kite.holdings()

    def profile(self):
        return self._kite.profile()

    def instruments(self):
        return self._kite.instruments('NSE')

    def historical(self, token, start, end):
        return self._kite.historical_data(token, start, end, 'day')

    def ltp(self, keys):
        return self._kite.ltp(keys)

    def trades(self):
        return self._kite.trades()
