import requests
import os
import urllib3
from datetime import datetime
from src.config import Config

class BankingService:
    @staticmethod
    def _fetch_raw_interest_rates():
        try:
            # CafeF Interest Rates
            url = "https://cafefnew.mediacdn.vn/Images/Uploaded/DuLieuDownload/Liveboard/all_banks_interest_rates.json"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://cafef.vn/"
            }
            res = requests.get(url, headers=headers, timeout=90)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception as e:
            print(f"⚠️ Raw Interest Fetch Error: {e}")
            return None

    @staticmethod
    def _fetch_raw_exchange_rates():
        try:
            from datetime import timedelta
            # Try Today, then Yesterday (if today is early morning and no data)
            now = datetime.now()
            dates_to_try = [now, now - timedelta(days=1)]
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://cafef.vn/"
            }

            for d in dates_to_try:
                date_str = d.strftime("%d/%m/%Y")
                url = f"https://cafef.vn/du-lieu/ajax/exchangerate/ajaxratecurrency.ashx?time={date_str}"
                
                try:
                    res = requests.get(url, headers=headers, timeout=90)
                    if res.status_code == 200:
                        data = res.json()
                        if data and isinstance(data, list) and len(data) > 0:
                            return data
                except:
                    continue
            
            return None
        except Exception as e:
            print(f"⚠️ Raw Exchange Fetch Error: {e}")
            return None

    @staticmethod
    def _generate_rate_chart(chart_data):
        """
        chart_data: List of tuples (BankCode, Rate6M, Rate12M)
        """
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
            import numpy as np
            
            # Extract data
            banks = [x[0] for x in chart_data]
            rates_6m = [x[1] for x in chart_data]
            rates_12m = [x[2] for x in chart_data]
            
            # Setup Grouped Bar
            x = np.arange(len(banks))
            width = 0.35
            
            # Create Output Dir
            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            chart_path = os.path.join(output_dir, "interest_rate_chart.png")

            # Plotting OO
            fig = Figure(figsize=(12, 6))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            
            rects1 = ax.bar(x - width/2, rates_6m, width, label='6 Tháng', color='#3498db')
            rects2 = ax.bar(x + width/2, rates_12m, width, label='12 Tháng', color='#2ecc71')

            ax.set_ylabel('Lãi suất (%)')
            ax.set_title('So sánh Lãi suất Tiết kiệm (6M vs 12M)')
            ax.set_xticks(x)
            ax.set_xticklabels(banks)
            ax.legend()
            ax.grid(True, axis='y', linestyle='--', alpha=0.5)
            
            # Add labels
            def autolabel(rects):
                for rect in rects:
                    height = rect.get_height()
                    ax.annotate(f'{height}%',
                                xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 3),  # 3 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom', fontsize=8)

            autolabel(rects1)
            autolabel(rects2)

            fig.tight_layout()
            canvas.print_png(chart_path)
            return chart_path
        except Exception as e:
            print(f"⚠️ Rate Chart Error: {e}")
            return None


    @staticmethod
    def fetch_banking_rates():
        # Exchange Rates
        rates = BankingService._fetch_raw_exchange_rates()
        ex_text = "N/A"
        if rates:
            try:
                # Find VCB row
                vcb = next((item for item in rates if item.get('BankCode') == 'VCB'), None)
                if vcb:
                    usd = next((r for r in rates if r.get('BankCode') == 'VCB' and r.get('CurrencyCode') == 'USD'), None)
                    eur = next((r for r in rates if r.get('BankCode') == 'VCB' and r.get('CurrencyCode') == 'EUR'), None)
                    
                    ex_text = ""
                    if usd: ex_text += f"USD/VND (VCB): Mua {usd['BuyTransfer']} - Bán {usd['Sell']}\n"
                    if eur: ex_text += f"EUR/VND (VCB): Mua {eur['BuyTransfer']} - Bán {eur['Sell']}"
                else:
                    # Fallback
                    usd = next((r for r in rates if r.get('CurrencyCode') == 'USD'), None)
                    if usd: ex_text = f"USD/VND ({usd['BankCode']}): Mua {usd['BuyTransfer']} - Bán {usd['Sell']}"
            except:
                ex_text = "Lỗi xử lý tỷ giá."
        
        # Interest Rates
        rates_data = BankingService._fetch_raw_interest_rates()
        int_text = "N/A"
        chart_path = None
        
        if rates_data and 'Data' in rates_data:
             chart_data = []
             try:
                 rates = rates_data['Data']
                 # Get Big 4 + key private
                 # Symbols in JSON: VCB, BID, CTG, AGB, TCB, MBB, VPB
                 targets = ["VCB", "BID", "CTG", "AGB", "TCB", "MBB", "VPB"] 
                 lines = []
                 for bank in rates:
                     code = bank.get('symbol')
                     if code in targets:
                         # Interest Rates is a list of dicts: [{'deposit': 6, 'value': 4.5}, ...]
                         ir_list = bank.get('interestRates', [])
                         
                         def get_rate(term):
                             found = next((item for item in ir_list if item.get('deposit') == term), None)
                             return found.get('value') if found else 'N/A'

                         r12 = get_rate(12)
                         r6 = get_rate(6)
                         
                         lines.append(f"{code}: 6M({r6}%) - 12M({r12}%)")
                         
                         try: 
                             r12_val = float(r12) if r12 != 'N/A' else 0
                             r6_val = float(r6) if r6 != 'N/A' else 0
                             if r12_val > 0:
                                chart_data.append((code, r6_val, r12_val))
                         except: pass
                 
                 int_text = "\n".join(lines)
                 chart_path = BankingService._generate_rate_chart(chart_data)
             except Exception as e:
                 print(f"Rate process error: {e}")
                 int_text = "Lỗi xử lý lãi suất."
        
        text = f"--- [TỶ GIÁ & LÃI SUẤT] ---\n{ex_text}\n\nLãi suất 12M các NH lớn:\n{int_text}"
        return {"text": text, "chart_path": chart_path}
