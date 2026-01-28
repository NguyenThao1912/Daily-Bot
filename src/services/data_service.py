import os
import requests
import feedparser
import yfinance as yf

class DataService:
    @staticmethod
    def fetch_crypto():
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd"
            res = requests.get(url).json()
            return (
                f"BTC: {res['bitcoin']['usd']}$ (Link: https://www.coingecko.com/en/coins/bitcoin), "
                f"ETH: {res['ethereum']['usd']}$, SOL: {res['solana']['usd']}$."
            )
        except Exception:
            return "Không lấy được dữ liệu Crypto."

    @staticmethod
    def fetch_news():
        try:
            feed = feedparser.parse("https://vnexpress.net/rss/tin-moi-nhat.rss")
            top_news = [f"- [{entry.title}]({entry.link})" for entry in feed.entries[:3]]
            return "\n".join(top_news)
        except Exception:
            return "Không lấy được tin tức RSS."

    @staticmethod
    def fetch_market():
        try:
            tickers = yf.Tickers("^VNINDEX GC=F SI=F CL=F HPG.VN")
            
            def get_price(ticker):
                try: return ticker.fast_info['lastPrice']
                except: return 0

            return (
                f"\n\n[REAL-TIME MARKET]:\n"
                f"- VN-Index: {get_price(tickers.tickers['^VNINDEX']):.2f}\n"
                f"- Gold (World): {get_price(tickers.tickers['GC=F']):.2f} USD/oz\n"
                f"- Silver: {get_price(tickers.tickers['SI=F']):.2f} USD/oz\n"
                f"- Oil (WTI): {get_price(tickers.tickers['CL=F']):.2f} USD/barrel\n"
                f"- Steel (HPG Proxy): {get_price(tickers.tickers['HPG.VN']):.0f} VND"
            )
        except Exception as e:
            return f"\n\n[REAL-TIME ERROR]: Market data error ({str(e)})"

    @staticmethod
    def fetch_weather():
        from src.config import Config
        api_key = Config.WEATHER_API_KEY
        if not api_key:
            return " (Chưa cấu hình WEATHER_API_KEY)"
            
        try:
            url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={Config.WEATHER_LOCATION}&days=1&aqi=yes&alerts=yes"
            res = requests.get(url).json()
            
            curr = res['current']
            loc = res['location']['name']
            
            info = (
                f"Tại {loc}: {curr['condition']['text']}, Nhiệt độ {curr['temp_c']}°C. "
                f"UV: {curr['uv']}. Độ ẩm: {curr['humidity']}%. "
                f"AQI (US-EPA): {curr['air_quality']['us-epa-index']}."
            )
            
            if 'alerts' in res and res['alerts']['alert']:
                alerts = " | ".join([a['event'] for a in res['alerts']['alert']])
                info += f" [CẢNH BÁO]: {alerts}"
                
            return info
        except Exception as e:
            return f"Lỗi lấy thời tiết: {str(e)}"

    @staticmethod
    def get_macro_data():
        import pandas_datareader.data as web
        import datetime
        try:
            # 3. Lấy VN-Index
            from vnstock import Vnstock
            stock = Vnstock().stock(symbol="VNINDEX", source='VCI')
            df = stock.quote.history(start="2024-01-01", end=str(datetime.date.today()), resolution="1D")
            
            if not df.empty:
                vnindex_now = df['close'].iloc[-1]
                vnindex_change = df['close'].iloc[-1] - df['close'].iloc[-2]
            else:
                 vnindex_now, vnindex_change = 0, 0
        except Exception:
             vnindex_now, vnindex_change = 0, 0

        return {
            "DXY": f"{dxy_now:.2f} ({dxy_change:+.2f}%)",
            "Yield_Curve": spread_now,
            "VNIndex": f"{vnindex_now:.2f} ({vnindex_change:+.2f} điểm)"
        }

    @staticmethod
    def fetch_trends():
        try:
            # Google Trends RSS for Vietnam
            url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=VN"
            feed = feedparser.parse(url)
            trends = []
            for entry in feed.entries[:5]:
                # feedparser maps <ht:approx_traffic> to ht_approx_traffic
                traffic = getattr(entry, 'ht_approx_traffic', 'N/A')
                trends.append(f"- {entry.title} ({traffic} lượt tìm): {entry.link}")
            return "\n".join(trends)
        except Exception:
            return "Không lấy được Google Trends."

    @staticmethod
    async def get_all_data():
        macro = DataService.get_macro_data()
        return {
            "finance": (
                f"MACRO DATA:\n- DXY: {macro['DXY']}\n- US10Y-US2Y: {macro['Yield_Curve']}\n- VN-Index: {macro['VNIndex']}\n"
                "FPT: 135.2 (+0.5%), HPG: 25.4 (-1.2%), Vàng SJC: 89tr." + 
                DataService.fetch_market()
            ),
            "weather": DataService.fetch_weather(),
            "events": "Họp đối tác lúc 10:30, Deadline báo cáo quý lúc 17:00.",
            "tech": DataService.fetch_tech(),
            "news": DataService.fetch_news(),
            "trends": DataService.fetch_trends()
        }

    @staticmethod
    def fetch_tech():
        try:
            # VNExpress Số Hóa RSS
            feed = feedparser.parse("https://vnexpress.net/rss/so-hoa.rss")
            news = []
            for entry in feed.entries[:3]:
                news.append(f"- [{entry.title}]({entry.link})")
            return "\n".join(news)
        except Exception:
            return "Không lấy được tin công nghệ."
