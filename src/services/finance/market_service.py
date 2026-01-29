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
    def _generate_leader_chart(leaders_data):
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
            import numpy as np
            
            # Data typically: [{'Symbol': 'VCB', 'ContributionPoint': 1.5}, ...]
            # We need to find the correct key for point
            data = []
            for item in leaders_data:
                sym = item.get('Symbol') or item.get('StockCode')
                # Try common keys for contribution
                point = item.get('ContributionPoint') or item.get('Point') or item.get('Value') or 0
                if sym and point != 0:
                    data.append((sym, float(point)))
            
            # Sort by point desc
            data.sort(key=lambda x: x[1])
            
            if not data: return None

            symbols = [x[0] for x in data]
            values = [x[1] for x in data]
            colors = ['#2ecc71' if v > 0 else '#e74c3c' for v in values]
            
            # Create Output Dir
            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            chart_path = os.path.join(output_dir, "market_leader_chart.png")

            # Plotting (OO Interface)
            fig = Figure(figsize=(10, 6))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            
            bars = ax.barh(symbols, values, color=colors)
            
            ax.set_title('Top Cổ Phiếu Ảnh Hưởng Đến VN-Index')
            ax.set_xlabel('Điểm đóng góp')
            ax.axvline(x=0, color='black', linewidth=0.8)
            ax.grid(True, axis='x', linestyle='--', alpha=0.5)
            
            # Value Labels
            for bar in bars:
                width = bar.get_width()
                label_x_pos = width if width > 0 else width
                align = 'left' if width > 0 else 'right'
                offset = 5 if width > 0 else -5
                
                ax.text(label_x_pos + (offset/100), bar.get_y() + bar.get_height()/2, 
                         f'{width:+.2f}', 
                         va='center', ha=align, fontsize=9, fontweight='bold')

            fig.tight_layout()
            canvas.print_png(chart_path)
            return chart_path

        except Exception as e:
            print(f"⚠️ Leader Chart Error: {e}")
            return None

        except Exception as e:
            print(f"⚠️ Leader Chart Error: {e}")
            return None

    @staticmethod
    def _fetch_cafef_leaders():
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            url = "https://msh-appdata.cafef.vn/rest-api/api/v1/MarketLeaderGroup?centerId=1&take=10"
            headers = {
               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                  "Referer": "https://cafef.vn/",
                  "Origin": "https://cafef.vn",
                  "Host": "msh-appdata.cafef.vn",
                  "Accept": "application/json, text/plain, */*",
                  "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
                  "Connection": "keep-alive",
                  "Sec-Fetch-Dest": "empty",
                  "Sec-Fetch-Mode": "cors",
                  "Sec-Fetch-Site": "same-site"
            }
            
            res = requests.get(url, headers=headers, timeout=10, verify=False)
            
            if res.status_code != 200:
                  print(f"Lỗi HTTP: {res.status_code}")
                  # print(res.text[:200]) # Optional debug
                  return None

            if res.status_code == 200:
                return res.json()
            return None
        except Exception as e:
             print(f"⚠️ CafeF Leader Error: {e}")
             return None

    @staticmethod
    def _fetch_cafef_foreign_flow():
        try:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            headers = {
               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
               "Referer": "https://cafef.vn/"
            }
            
            # Fetch Buy
            url_buy = "https://cafef.vn/du-lieu/ajax/mobile/smart/ajaxkhoingoai.ashx?type=buy"
            res_buy = requests.get(url_buy, headers=headers, timeout=10, verify=False)
            buy_data = res_buy.json() if res_buy.status_code == 200 else []
            
            # Fetch Sell
            url_sell = "https://cafef.vn/du-lieu/ajax/mobile/smart/ajaxkhoingoai.ashx?type=sell"
            res_sell = requests.get(url_sell, headers=headers, timeout=10, verify=False)
            sell_data = res_sell.json() if res_sell.status_code == 200 else []

            # Process Data: Calculate Net Flow (Buy - Sell)
            # Structure assumed: list of dicts with 'Symbol' and 'Value' (Volume or Value?) - usually Volume or Value. 
            # Let's inspect keys if possible. Assuming 'Symbol' and 'Value' based on typical endpoints.
            
            # Helper to map symbol -> value
            def map_data(data_list):
                d = {}
                if not isinstance(data_list, list): return d
                for item in data_list:
                    sym = item.get('Symbol') or item.get('StockCode')
                    val = item.get('Value') or item.get('Volume') or 0 # Ensure we get something
                    if sym: d[sym] = float(val)
                return d

            buy_map = map_data(buy_data)
            sell_map = map_data(sell_data)
            
            # Merge keys
            all_syms = set(buy_map.keys()) | set(sell_map.keys())
            
            net_flow = [] # (Symbol, NetValue)
            for sym in all_syms:
                b = buy_map.get(sym, 0)
                s = sell_map.get(sym, 0)
                net = b - s
                if net != 0:
                    net_flow.append((sym, net))
            
            # Sort by absolute net value? Or separate Buy/Sell?
            # Typically users want Top Net Buy and Top Net Sell.
            net_flow.sort(key=lambda x: x[1], reverse=True) # Descending for Buy
            
            top_buy = net_flow[:5]
            top_sell = net_flow[-5:] # Smallest (most negative) for Sell
            top_sell.sort(key=lambda x: x[1]) # Sort ascending (most negative first)
            
            return top_buy, top_sell, buy_data, sell_data

        except Exception as e:
            print(f"⚠️ Foreign Flow Error: {e}")
            return [], [], [], []

    @staticmethod
    def fetch_market():
        lines = []
        
        # 0. Foreign Flow (NEW)
        top_buy, top_sell, raw_buy, raw_sell = MarketService._fetch_cafef_foreign_flow()
        if top_buy or top_sell:
            lines.append("[KHỐI NGOẠI (HOSE)]")
            
            if top_buy:
                lines.append("Mua ròng mạnh:")
                for sym, val in top_buy:
                    if val > 0:
                        lines.append(f"+ {sym}: {val:,.0f}")
            
            if top_sell:
                lines.append("Bán ròng mạnh:")
                for sym, val in top_sell:
                    if val < 0: # Should be negative
                        lines.append(f"- {sym}: {val:,.0f}")
            lines.append("")

        # 1. Commodities (Hang Hoa)
        comm_data = MarketService._fetch_cafef_commodities()
        if comm_data and comm_data.get('Success') and 'Data' in comm_data:
            comm_list = comm_data['Data']
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
             for item in leaders:
                 sym = item.get('Symbol') or item.get('StockCode')
                 if sym: l_strs.append(sym)
             if l_strs:
                 lines.append(", ".join(l_strs))
        
        return "\n\n[MARKET DATA - CafeF]:\n" + "\n".join(lines)
