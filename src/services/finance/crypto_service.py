import requests
from src.config import Config

class CryptoService:
    @staticmethod
    def _fetch_from_worker(path, params=None):
        try:
            url = f"{Config.WORKER_HOST.rstrip('/')}{path}"
            res = requests.get(url, params=params, timeout=20)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"⚠️ Worker Error ({path}): {e}")
            return None

    @staticmethod
    def fetch_crypto():
        data = CryptoService._fetch_from_worker("/crypto")
        if not data or 'data' not in data:
            return "Không lấy được dữ liệu Crypto."
        
        res = data['data']
        try:
            return (
                f"BTC: {res['bitcoin']['usd']}$ (Link: https://www.coingecko.com/en/coins/bitcoin), "
                f"ETH: {res['ethereum']['usd']}$, SOL: {res['solana']['usd']}$."
            )
        except:
            return str(res)
