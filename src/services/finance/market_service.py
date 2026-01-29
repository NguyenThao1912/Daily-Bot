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
    def _generate_foreign_flow_chart(net_flow_data):
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
            
            # net_flow_data is list of (Symbol, NetValue)
            # Filter top 5 buy and top 5 sell (already sorted in fetch logic, but let's ensure)
            # data comes in as full list? No, fetch_market gets top_buy and top_sell.
            # Let's align the interface. We'll accept (top_buy, top_sell).
            
            top_buy, top_sell = net_flow_data
            
            # Combine for chart: Top Sell (negative) ... Top Buy (positive)
            # to make a diverging bar chart
            
            # Prepare data
            chart_data = [] # (Symbol, Value)
            # Add Top Sell first (so they appear at bottom or left?)
            # Barh: Y axis is categories. 
            # We want Buy on top, Sell on bottom? Or diverging?
            # Let's put Top Buy on top, Top Sell on bottom.
            
            # Sort Top Buy desc (biggest first)
            # Sort Top Sell desc (most negative first - currently they are passed as such?)
            
            combined = top_buy + top_sell # [(Sym, Val), ...]
            combined.sort(key=lambda x: x[1]) # Sort by value asc (Negative -> Positive)
            
            symbols = [x[0] for x in combined]
            values = [x[1] / 1_000_000_000 for x in combined] # Convert to Billion VND
            
            colors = ['#2ecc71' if v > 0 else '#e74c3c' for v in values]
            
            # Plot
            fig = Figure(figsize=(10, 6))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            
            bars = ax.barh(symbols, values, color=colors)
            
            ax.set_title('Top Khối Ngoại Mua/Bán Ròng (Tỷ VNĐ)')
            ax.set_xlabel('Giá trị ròng (Tỷ VNĐ)')
            ax.axvline(x=0, color='black', linewidth=0.8)
            ax.grid(True, axis='x', linestyle='--', alpha=0.5)
            
            # Labels
            for bar in bars:
                width = bar.get_width()
                label_x_pos = width
                align = 'left' if width > 0 else 'right'
                offset = 2 if width > 0 else -2
                
                ax.text(label_x_pos + (offset/100 * abs(width)), bar.get_y() + bar.get_height()/2, 
                         f'{width:,.1f}', 
                         va='center', ha=align, fontsize=9, fontweight='bold')

            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            chart_path = os.path.join(output_dir, "foreign_flow_chart.png")
            
            fig.tight_layout()
            canvas.print_png(chart_path)
            return chart_path
        except Exception as e:
            print(f"⚠️ Foreign Flow Chart Error: {e}")
            return None

    @staticmethod
    def _generate_commodities_chart(comm_data):
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
            
            # comm_data is list of dicts: {'goods': 'Gold', 'changePercent': 0.5, ...}
            # Filter top items (e.g. Gold, Oil, Bitcoin, etc.) or just top 10 by importance?
            # Let's take first 8 items as they are usually ranked by importance
            items = comm_data[:8]
            
            names = [x.get('goods', 'N/A') for x in items]
            changes = []
            for x in items:
                try:
                    c = float(x.get('changePercent', 0))
                except:
                    c = 0
                changes.append(c)

            # Colors
            colors = ['#2ecc71' if c >= 0 else '#e74c3c' for c in changes]
            
            # Plot
            fig = Figure(figsize=(8, 5))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            
            bars = ax.barh(names, changes, color=colors)
            ax.set_title('Biến động Hàng Hóa (%)')
            ax.set_xlabel('% Thay đổi')
            ax.axvline(x=0, color='black', linewidth=0.8)
            ax.grid(True, axis='x', linestyle='--', alpha=0.5)
            ax.invert_yaxis()
            
            for bar in bars:
                width = bar.get_width()
                label_x_pos = width
                align = 'left' if width > 0 else 'right'
                offset = 0.1 if width > 0 else -0.1
                ax.text(label_x_pos + offset, bar.get_y() + bar.get_height()/2, 
                        f'{width:+.2f}%', va='center', ha=align, fontsize=9, fontweight='bold')

            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            chart_path = os.path.join(output_dir, "commodities_chart.png")
            
            fig.tight_layout()
            canvas.print_png(chart_path)
            return chart_path
        except Exception as e:
            print(f"⚠️ Commodities Chart Error: {e}")
            return None

    @staticmethod
    def _generate_global_chart(global_data):
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
            
            # global_data is list of dicts.
            # Names can be long. Let's pick Key Indices: Dow Jones, Nasdaq, S&P 500, Nikkei 225, Shanghai, Hang Seng, FTSE 100, DAX
            # Filter by known keywords or just take top 8
            
            # Simple approach: Top 8 from list
            items = global_data[:8]
            
            names = []
            changes = []
            for x in items:
                n = x.get('Symbol') or x.get('Name') or 'N/A'
                # Shorten names
                n = n.replace('COMPOSITE', '').replace('INDEX', '').strip()
                names.append(n)
                
                # Change percent might be string "0.5%" or float
                try:
                    ch_raw = x.get('ChangePercent') or x.get('PercentChange') or 0
                    if isinstance(ch_raw, str):
                        ch_raw = ch_raw.replace('%', '')
                    changes.append(float(ch_raw))
                except:
                    changes.append(0)

            colors = ['#2ecc71' if c >= 0 else '#e74c3c' for c in changes]
            
            fig = Figure(figsize=(8, 5))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            
            bars = ax.barh(names, changes, color=colors)
            ax.set_title('Chỉ số Thế giới (%)')
            ax.set_xlabel('% Thay đổi')
            ax.axvline(x=0, color='black', linewidth=0.8)
            ax.grid(True, axis='x', linestyle='--', alpha=0.5)
            ax.invert_yaxis()
            
            for bar in bars:
                width = bar.get_width()
                label_x_pos = width
                align = 'left' if width > 0 else 'right'
                offset = 0.05 if width > 0 else -0.05
                ax.text(label_x_pos + offset, bar.get_y() + bar.get_height()/2, 
                        f'{width:+.2f}%', va='center', ha=align, fontsize=9, fontweight='bold')

            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            chart_path = os.path.join(output_dir, "global_chart.png")
            
            fig.tight_layout()
            canvas.print_png(chart_path)
            return chart_path
        except Exception as e:
            print(f"⚠️ Global Chart Error: {e}")
            return None

    @staticmethod
    def fetch_market():
        lines = []
        chart_paths = []

        # 0. Foreign Flow (NEW)
        top_buy, top_sell, raw_buy, raw_sell = MarketService._fetch_cafef_foreign_flow()
        if top_buy or top_sell:
            lines.append("[KHỐI NGOẠI (HOSE)]")
            
            # Generate Foreign Flow Chart
            ff_chart = MarketService._generate_foreign_flow_chart((top_buy, top_sell))
            if ff_chart: chart_paths.append(ff_chart)

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
            
            # Generate Chart
            c_chart = MarketService._generate_commodities_chart(comm_list)
            if c_chart: chart_paths.append(c_chart)

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
                
                # Generate Chart
                g_chart = MarketService._generate_global_chart(gl_data)
                if g_chart: chart_paths.append(g_chart)

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
             
             # Generate Leader Chart
             leader_chart = MarketService._generate_leader_chart(leaders)
             if leader_chart: chart_paths.append(leader_chart)
             
             for item in leaders:
                 sym = item.get('Symbol') or item.get('StockCode')
                 if sym: l_strs.append(sym)
             if l_strs:
                 lines.append(", ".join(l_strs))
        
        return {
            "text": "\n\n[MARKET DATA - CafeF]:\n" + "\n".join(lines),
            "chart_path": chart_paths # Dict key expects 'chart_path' but we pass a list here. 
            # Note: get_safe_data in main.py will extract this. 
            # We'll need to handle list in main.py if get_safe_data expects single.
            # Actually get_safe_data just gets the value. So list is fine.
        }
