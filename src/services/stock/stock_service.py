import requests
import urllib3
from datetime import datetime
from src.config import Config
from src.services.watchlist_service import WatchlistService

class StockService:
    @staticmethod
    def _fetch_stock_history(symbol, page_size=60):
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # Fetch more data for history (PageSize=60 for ~3 months of trading days to be safe for MA20/RSI14)
            url = f"https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx?Symbol={symbol}&StartDate=&EndDate=&PageIndex=1&PageSize={page_size}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://cafef.vn/"
            }
            res = requests.get(url, headers=headers, timeout=10, verify=False)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, dict):
                    inner = data.get("Data", [])
                    if isinstance(inner, dict): inner = inner.get("Data", [])
                    if isinstance(inner, list) and len(inner) > 0:
                        return inner
            return []
        except Exception as e:
            print(f"⚠️ CafeF History Error ({symbol}): {e}")
            return []

    @staticmethod
    def calculate_technical_indicators(history_data):
        import pandas as pd
        import numpy as np
        
        if not history_data or len(history_data) < 30:
            return None, None

        # Extract prices (reverse to have Oldest -> Newest for Pandas)
        prices = []
        for item in history_data:
            p = item.get('GiaDongCua') or item.get('GiaDieuChinh') or item.get('Price') or 0
            prices.append(float(p))
        
        prices.reverse() # CafeF returns Newest first
        
        df = pd.DataFrame({'close': prices})
        
        # Calculate MA20
        df['ma20'] = df['close'].rolling(window=20).mean()
        
        # Calculate RSI 14
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        # Create 'wilder' smoothing/EMA style if preferred, but simple rolling is okay for approximation
        # Let's use Wilder's Smoothing for more accuracy if possible, but standard rolling is often sufficient for snapshot
        # For simplicity and speed without complex recursion:
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Get latest values
        latest_ma = df['ma20'].iloc[-1]
        latest_rsi = df['rsi'].iloc[-1]
        
        return latest_rsi, latest_ma

    @staticmethod
    def fetch_stock_analysis():
        results = []
        # Fetch from DB if available, fallback to Config
        watchlist = WatchlistService.get_watchlist(Config.TELEGRAM_CHAT_ID, "stock")
        if not watchlist:
            watchlist = Config.STOCK_WATCHLIST
            
        for symbol in watchlist:
            try:
                # Handle symbol cleanup
                target = symbol.replace("^", "").split(".")[0] 
                
                # Fetch History (includes latest)
                history = StockService._fetch_stock_history(target)
                
                if not history:
                    print(f"⚠️ No data for {target}")
                    continue

                node = history[0] # Latest
                
                # Extract Data
                price = node.get('GiaDongCua') or node.get('GiaDieuChinh') or node.get('Price') or node.get('price') or 0
                change = node.get('ThayDoi') or node.get('Change') or node.get('change') or 0
                pct = node.get('PhanTramThayDoi') or node.get('Percent') or node.get('volPercent') or 0
                vol = node.get('KhoiLuongKhopLenh') or node.get('KhoiLuong') or node.get('Volume') or 0
                
                # Tech Indicators
                rsi, ma20 = StockService.calculate_technical_indicators(history)
                
                tech_str = ""
                if rsi is not None and ma20 is not None:
                    # Determine Trend
                    trend_icon = "🟢" if price > ma20 else "🔴"
                    rsi_status = "Quá mua" if rsi > 70 else "Quá bán" if rsi < 30 else "Tích lũy"
                    tech_str = f" | {trend_icon} RSI: {rsi:.1f} ({rsi_status}), MA20: {ma20:,.1f}"

                results.append(
                    f"Mã: {target} | Giá: {price} | +/-: {change} ({pct}%) | Vol: {vol:,.0f}{tech_str}"
                )
            except Exception as e:
                print(f"⚠️ Stock Error ({symbol}): {e}")
        
        return "\n".join(results) if results else "Không có dữ liệu watchlist."
