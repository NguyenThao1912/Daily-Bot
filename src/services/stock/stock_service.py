import requests
import urllib3
from datetime import datetime
from src.config import Config
from src.services.watchlist_service import WatchlistService

class StockService:
    @staticmethod
    def _fetch_cafef_stock_snapshot(symbol):
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # User provided: https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx?Symbol=...
            url = f"https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx?Symbol={symbol}&StartDate=&EndDate=&PageIndex=1&PageSize=20"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://cafef.vn/"
            }
            res = requests.get(url, headers=headers, timeout=10, verify=False)
            if res.status_code == 200:
                data = res.json()
                # Structure: {"Data": { "Data": [ { "GiaDongCua": ... } ] } } 
                # OR: {"Data": [ ... ]}
                # Let's handle generic wrapper
                
                if isinstance(data, dict):
                    # Try to drill down to list of items
                    inner = data.get("Data", [])
                    if isinstance(inner, dict):
                         inner = inner.get("Data", []) # Sometimes Data.Data
                    
                    if isinstance(inner, list) and len(inner) > 0:
                        return inner[0] # Latest item
                
                return data
            return None
        except Exception as e:
            print(f"⚠️ CafeF Stock Snapshot Error ({symbol}): {e}")
            return None

    @staticmethod
    def fetch_stock_analysis():
        results = []
        # Fetch from DB if available, fallback to Config
        watchlist = WatchlistService.get_watchlist(Config.TELEGRAM_CHAT_ID, "stock")
        if not watchlist:
            watchlist = Config.STOCK_WATCHLIST
            
        for symbol in watchlist:
            try:
                # Handle symbol cleanup (Daily-Bot's config or user input might have suffixes)
                target = symbol.replace("^", "").split(".")[0] 
                
                # Special mapping for CafeF: VNINDEX -> VNI
                if target.upper() in ["VNINDEX", "VN-INDEX"]:
                    target = "VNI"
                
                node = StockService._fetch_cafef_stock_snapshot(target)
                if not node:
                    print(f"⚠️ No data for {target}")
                    continue

                # Extract Data
                # PriceHistory keys are usually: GiaDongCua, ThayDoi, PhanTramThayDoi, KhoiLuongKhopLenh
                price = node.get('GiaDongCua') or node.get('GiaDieuChinh') or node.get('Price') or node.get('price') or 0
                change = node.get('ThayDoi') or node.get('Change') or node.get('change') or 0
                pct = node.get('PhanTramThayDoi') or node.get('Percent') or node.get('volPercent') or 0
                vol = node.get('KhoiLuongKhopLenh') or node.get('KhoiLuong') or node.get('Volume') or 0
                
                # If still 0, debug
                if price == 0:
                     print(f"DEBUG {target} RAW: {str(node)[:200]}")

                results.append(
                    f"Mã: {target} | Giá: {price} | +/-: {change} ({pct}%) | Vol: {vol:,.0f}"
                )
            except Exception as e:
                print(f"⚠️ Stock Error ({symbol}): {e}")
        
        return "\n".join(results) if results else "Không có dữ liệu watchlist."
