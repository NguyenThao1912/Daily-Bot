import requests
import urllib3
from datetime import datetime
from src.config import Config
from src.services.watchlist_service import WatchlistService

class StockService:
    @staticmethod
    def _fetch_stock_history(symbol, page_size=300):
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # Fetch more data for history (PageSize=300 for >200 days for MA200)
            url = f"https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx?Symbol={symbol}&StartDate=&EndDate=&PageIndex=1&PageSize={page_size}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://cafef.vn/"
            }
            res = requests.get(url, headers=headers, timeout=90, verify=False)
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
            return None, None, None, None, None
            
        # Extract prices and volumes
        prices = []
        volumes = []
        for item in history_data:
            p = item.get('GiaDongCua') or item.get('GiaDieuChinh') or item.get('Price') or 0
            v = item.get('KhoiLuongKhopLenh') or item.get('KhoiLuong') or item.get('Volume') or 0
            prices.append(float(p))
            volumes.append(float(v))
        
        prices.reverse() # Oldest -> Newest
        volumes.reverse()
        
        df = pd.DataFrame({'close': prices, 'volume': volumes})
        
        # Calculate MAs
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma50'] = df['close'].rolling(window=50).mean()
        df['ma200'] = df['close'].rolling(window=200).mean()
        
        # Calculate Volume Avg (20)
        df['vol20'] = df['volume'].rolling(window=20).mean()
        
        # Calculate RSI 14
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        latest_ma20 = df['ma20'].iloc[-1]
        latest_ma50 = df['ma50'].iloc[-1]
        latest_ma200 = df['ma200'].iloc[-1]
        latest_rsi = df['rsi'].iloc[-1]
        latest_vol_avg = df['vol20'].iloc[-1]
        
        return latest_rsi, latest_ma20, latest_ma50, latest_ma200, latest_vol_avg

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
                rsi, ma20, ma50, ma200, vol_avg = StockService.calculate_technical_indicators(history)
                
                tech_str = ""
                if rsi is not None and ma20 is not None:
                    # Determine Trend
                    trend_icon = "🟢" if price > ma20 else "🔴"
                    rsi_status = "Quá mua" if rsi > 70 else "Quá bán" if rsi < 30 else "Tích lũy"
                    
                    # Volume Check
                    vol_check = ""
                    if vol_avg and vol > vol_avg * 1.3: vol_check = "💥 NỔ VOL"
                    elif vol_avg and vol < vol_avg * 0.5: vol_check = "📉 Cạn cung"
                    
                    # MA Status
                    ma_status = f"MA20({ma20:,.1f})"
                    if ma50 and not np.isnan(ma50): ma_status += f" MA50({ma50:,.1f})"
                    if ma200 and not np.isnan(ma200): ma_status += f" MA200({ma200:,.1f})"

                    tech_str = f" | {trend_icon} RSI:{rsi:.0f}({rsi_status}) | {ma_status} | Vol:{vol_check}"

                results.append(
                    f"Mã: {target} | Giá: {price} | +/-: {change} ({pct}%) | Vol: {vol:,.0f} {tech_str}"
                )
            except Exception as e:
                print(f"⚠️ Stock Error ({symbol}): {e}")
        
        return "\n".join(results) if results else "Không có dữ liệu watchlist."
