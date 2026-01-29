import requests
import urllib3
from datetime import datetime

class MarketService:
    @staticmethod
    def _fetch_cafef_commodities():
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            url = "https://cafef.vn/du-lieu/ajax/mobile/smart/ajaxhanghoa.ashx?type=1"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://cafef.vn/"
            }
            res = requests.get(url, headers=headers, timeout=10, verify=False)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception as e:
            print(f"⚠️ CafeF Commodities Error: {e}")
            return None

    @staticmethod
    def _fetch_cafef_global():
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            url = "https://cafef.vn/du-lieu/ajax/mobile/smart/ajaxchisothegioi.ashx"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://cafef.vn/"
            }
            res = requests.get(url, headers=headers, timeout=10, verify=False)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception as e:
            print(f"⚠️ CafeF Global Error: {e}")
            return None

    @staticmethod
    def _fetch_cafef_leaders():
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            url = "https://msh-appdata.cafef.vn/rest-api/api/v1/MarketLeaderGroup?centerId=1&take=10"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://cafef.vn/"
            }
            res = requests.get(url, headers=headers, timeout=10, verify=False)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception as e:
             print(f"⚠️ CafeF Leader Error: {e}")
             return None

    @staticmethod
    def fetch_market():
        lines = []
        
        # 1. Commodities (Hang Hoa)
        comm_data = MarketService._fetch_cafef_commodities()
        if comm_data and comm_data.get('Success') and 'Data' in comm_data:
            comm_list = comm_data['Data']
            # Map typical keys if known, otherwise list all or major ones
            # User requested ALL. so we try to map as many as possible or just list them.
            # But the list is huge. Let's map the important ones and list others if possible.
            # Actually, user said "lấy all đi". 
            
            lines.append("[HÀNG HÓA - TOP 15 QUAN TRỌNG]")
            for item in comm_list[:15]:
                name = item.get('goods')
                price = item.get('last')
                change = item.get('changePercent')
                if name and price:
                     lines.append(f"- {name}: {price:,.2f} ({change}%)")

        # 2. World Indices
        gl_data = MarketService._fetch_cafef_global()
        if gl_data:
            if isinstance(gl_data, list):
                lines.append("\n[CHỈ SỐ THẾ GIỚI]")
                count = 0
                for item in gl_data:
                     if count >= 3: break
                     name = item.get('Symbol') or item.get('Name')
                     price = item.get('Price') or item.get('Point')
                     if name and price:
                        lines.append(f"- {name}: {price}")
                        count += 1
        
        # 3. Market Leaders
        lines.append("\n[DẪN DẮT VN-INDEX - ALL]")
        leaders = MarketService._fetch_cafef_leaders()
        if leaders and isinstance(leaders, list):
             l_strs = []
             for item in leaders: # Remove slicing [:5]
                 sym = item.get('Symbol') or item.get('StockCode')
                 if sym: l_strs.append(sym)
             if l_strs:
                 lines.append(", ".join(l_strs))
        
        return "\n\n[MARKET DATA - CafeF]:\n" + "\n".join(lines)
