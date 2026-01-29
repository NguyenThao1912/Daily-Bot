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
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception as e:
            print(f"⚠️ Raw Interest Fetch Error: {e}")
            return None

    @staticmethod
    def _fetch_raw_exchange_rates():
        try:
            # CafeF Exchange Rates
            now = datetime.now()
            date_str = now.strftime("%d/%m/%Y")
            url = f"https://cafef.vn/du-lieu//ajax/exchangerate/ajaxratecurrency.ashx?time={date_str}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://cafef.vn/"
            }
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception as e:
            print(f"⚠️ Raw Exchange Fetch Error: {e}")
            return None

    @staticmethod
    def _generate_rate_chart(rates_data):
        try:
            import matplotlib.pyplot as plt
            
            # Extract data
            banks = []
            values = []
            
            # Sort by rate desc: (BankCode, RateFloat)
            sorted_rates = sorted(rates_data, key=lambda x: x[1], reverse=True)
            
            for bank, rate in sorted_rates:
                banks.append(bank)
                values.append(rate)
            
            # Create Output Dir
            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            chart_path = os.path.join(output_dir, "interest_rate_chart.png")

            # Plot properties
            plt.figure(figsize=(10, 5))
            bars = plt.bar(banks, values, color='#4CAF50') # Green theme
            plt.ylabel('Lãi suất 12 Tháng (%)')
            plt.title('Lãi suất Tiết kiệm Ngân hàng (12M)')
            plt.ylim(0, max(values) + 1)
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height}%',
                        ha='center', va='bottom', fontweight='bold')

            plt.tight_layout()
            plt.savefig(chart_path)
            plt.close()
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
                             if r12 and r12 != 'N/A':
                                chart_data.append((code, float(r12)))
                         except: pass
                 
                 int_text = "\n".join(lines)
                 chart_path = BankingService._generate_rate_chart(chart_data)
             except Exception as e:
                 print(f"Rate process error: {e}")
                 int_text = "Lỗi xử lý lãi suất."
        
        text = f"--- [TỶ GIÁ & LÃI SUẤT] ---\n{ex_text}\n\nLãi suất 12M các NH lớn:\n{int_text}"
        return {"text": text, "chart_path": chart_path}
