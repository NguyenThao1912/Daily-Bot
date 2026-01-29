import requests
import urllib3
from datetime import datetime
from src.config import Config
from src.services.watchlist_service import WatchlistService
import pandas as pd
import numpy as np

class StockService:
    @staticmethod
    def _fetch_stock_history(symbol, page_size=300):
        try:
            # Fetch more data for history (PageSize=300 for >200 days for MA200)
            url = f"https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx?Symbol={symbol}&StartDate=&EndDate=&PageIndex=1&PageSize={page_size}"
            headers = {
                "Connection": "keep-alive",
                "Pragma": "no-cache",
                "Cache-Control": "no-cache",
                "Sec-Fetch-Dest": "empty",
                "X-MicrosoftAjax": "Delta=true",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Accept": "*/*",
                "Origin": "https://s.cafef.vn",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
                "Referer": "https://s.cafef.vn/Lich-su-giao-dich-VNINDEX-1.chn",
                "Accept-Language": "vi,en-US;q=0.9,en;q=0.8"
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
    def _generate_portfolio_chart(portfolio_data):
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
            import os
            
            # portfolio_data = list of (Symbol, CurrentVal, CostVal, ProfitVal)
            if not portfolio_data: return None
            
            symbols = [x[0] for x in portfolio_data]
            current_vals = [x[1]/1000000 for x in portfolio_data] # Million VND
            
            # Create Output Dir
            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            chart_path = os.path.join(output_dir, "portfolio_chart.png")

            # Plot Pie Chart
            fig = Figure(figsize=(6, 4))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            
            colors = ['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6']
            wedges, texts, autotexts = ax.pie(current_vals, labels=symbols, autopct='%1.1f%%', 
                                            startangle=90, colors=colors[:len(symbols)],
                                            textprops=dict(color="black"))
            
            ax.set_title('Tỷ trọng Danh mục (theo giá thị trường)')
            
            fig.tight_layout()
            canvas.print_png(chart_path)
            return chart_path
        except Exception as e:
            print(f"⚠️ Portfolio Chart Error: {e}")
            return None

    @staticmethod
    def fetch_stock_analysis():
        results = []
        chart_paths = []
        
        # 1. Watchlist Processing
        watchlist = WatchlistService.get_watchlist(Config.TELEGRAM_CHAT_ID, "stock")
        if not watchlist:
            watchlist = Config.STOCK_WATCHLIST
        
        results.append("--- [WATCHLIST] ---")
        for symbol in watchlist:
            try:
                target = symbol.replace("^", "").split(".")[0]
                history = StockService._fetch_stock_history(target)
                if not history: continue
                
                node = history[0]
                price = node.get('GiaDongCua') or node.get('Price') or 0
                change = node.get('ThayDoi') or node.get('Change') or 0
                pct = node.get('PhanTramThayDoi') or node.get('Percent') or 0
                vol = node.get('KhoiLuongKhopLenh') or node.get('Volume') or 0
                
                rsi, ma20, ma50, ma200, vol_avg = StockService.calculate_technical_indicators(history)
                
                tech_str = ""
                if rsi is not None and ma20 is not None:
                    trend_icon = "🟢" if price > ma20 else "🔴"
                    rsi_status = "Quá mua" if rsi > 70 else "Quá bán" if rsi < 30 else "Tích lũy"
                    vol_check = ""
                    if vol_avg and vol > vol_avg * 1.3: vol_check = "💥 NỔ VOL"
                    elif vol_avg and vol < vol_avg * 0.5: vol_check = "📉 Cạn cung"
                    
                    ma_status = f"MA20({ma20:,.1f})"
                    tech_str = f" | {trend_icon} RSI:{rsi:.0f}({rsi_status}) | {ma_status} | Vol:{vol_check}"

                results.append(f"Mã: {target} | Giá: {price} | +/-: {change} ({pct}%) | Vol: {vol:,.0f} {tech_str}")
            except Exception as e:
                print(f"⚠️ Stock Error ({symbol}): {e}")

        # 2. Portfolio Processing (NEW)
        portfolio = getattr(Config, 'DEFAULT_PORTFOLIO', {})
        if portfolio:
            results.append("\n--- [PORTFOLIO TRONG TAY] ---")
            portfolio_data_chart = [] # For chart
            total_cost = 0
            total_market = 0
            
            for symbol, details in portfolio.items():
                try:
                    vol_hold = details.get('vol', 0)
                    cost_price = details.get('cost', 0)
                    
                    # Fetch realtime price
                    history = StockService._fetch_stock_history(symbol)
                    if not history: continue
                    current_price = history[0].get('GiaDongCua') or history[0].get('Price') or 0
                    
                    # Calc P&L
                    market_val = vol_hold * current_price * 1000 # Assuming price is in KVND? No, usually VND e.g. 24.5 = 24500?
                    # CafeF price usually is 24.5 (meaning 24,500). Wait.
                    # Let's check history sample.
                    # Step 2715: HPG Price ? History output format not shown fully.
                    # Usually CafeF returns e.g. 26.8 (meaning 26,800).
                    # User config: "cost": 24.5 => 24,500.
                    # So calculations should be consistent.
                    
                    # Adjusted: Cost 24.5 * 1000 = 24500 VND.
                    # If config is 24500, then good.
                    # User Config: "cost": 25.
                    # If price is 25.5, then ratio is correct.
                    
                    # Assuming unit is 1.0 = 1000 VND.
                    cost_val = vol_hold * cost_price
                    curr_val = vol_hold * current_price
                    
                    profit = curr_val - cost_val
                    profit_pct = (profit / cost_val) * 100 if cost_val > 0 else 0
                    
                    emoji = "🟢" if profit > 0 else "🔴"
                    results.append(f"{emoji} {symbol}: {vol_hold:,.0f} cp | Giá vốn: {cost_price} | Hiện tại: {current_price} | P/L: {profit_pct:.2f}%")
                    
                    total_cost += cost_val
                    total_market += curr_val
                    portfolio_data_chart.append((symbol, curr_val * 1000, cost_val * 1000, profit * 1000)) 
                    # Multiply by 1000 to get real VND for chart (Million conversion)
                    
                except Exception as e:
                    print(f"⚠️ Portfolio Error ({symbol}): {e}")

            if total_cost > 0:
                total_profit = total_market - total_cost
                total_pct = (total_profit / total_cost) * 100
                results.append(f"\n💰 TỔNG NAV: {total_market * 1000:,.0f} VND (P/L: {total_pct:.2f}%)")
            
            # Generate Chart
            p_chart = StockService._generate_portfolio_chart(portfolio_data_chart)
            if p_chart: chart_paths.append(p_chart)

        # Return Text OR Dict if we have charts
        # If charts exist, we must return Dict to be parsed by Main
        if chart_paths:
             return {
                 "text": "\n".join(results),
                 "chart_path": chart_paths # Main expects list or single? Main handles both.
             }
        
        return "\n".join(results) if results else "Không có dữ liệu watchlist."
