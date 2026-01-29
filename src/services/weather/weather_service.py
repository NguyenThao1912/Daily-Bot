import requests
import json
import os
from src.config import Config

class WeatherService:
    @staticmethod
    def _fetch_from_worker(path, params=None):
        try:
            url = f"{Config.WORKER_HOST.rstrip('/')}{path}"
            res = requests.get(url, params=params, timeout=20)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"⚠️ Worker Error ({path}): {e}")
            return None

    @staticmethod
    def _generate_weather_chart(weather_data):
        try:
            import matplotlib.pyplot as plt
            # Extract hourly data
            hours = weather_data['forecast']['forecastday'][0]['hour']
            times = [h['time'].split(' ')[1] for h in hours] # HH:MM
            temps = [h['temp_c'] for h in hours]
            
            # Create Output Dir
            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            chart_path = os.path.join(output_dir, "weather_chart.png")

            # Plotting
            plt.figure(figsize=(10, 5))
            plt.plot(times, temps, marker='o', linestyle='-', color='orange', label='Nhiệt độ (°C)')
            
            # Labeling
            date_str = weather_data['forecast']['forecastday'][0]['date']
            location_name = weather_data['location']['name']
            plt.title(f"Dự báo nhiệt độ {location_name} ngày {date_str}")
            plt.xlabel("Thời gian (Giờ)")
            plt.ylabel("Nhiệt độ (°C)")
            plt.xticks(rotation=45)
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.legend()
            plt.tight_layout()
            
            plt.savefig(chart_path)
            plt.close()
            return chart_path
        except Exception as e:
            print(f"⚠️ Chart Error: {e}")
            return None

    @staticmethod
    def fetch_weather():
        data = WeatherService._fetch_from_worker("/weather", params={"location": Config.WEATHER_LOCATION})
        if not data or 'data' in data.get('error', {}): 
            return "Lỗi lấy thời tiết từ worker."
        
        weather = data.get('data')
        if not weather or 'current' not in weather:
            return "Không lấy được dữ liệu thời tiết chi tiết."

        loc = weather['location']['name']
        curr = weather['current']
        forecast_data = weather['forecast']['forecastday'][0]['day']
        astro = weather['forecast']['forecastday'][0]['astro']
        
        # 1. Human Readable Summary
        summary = (
            f"📍 {loc}: {curr['condition']['text']}, {curr['temp_c']}°C (Cảm giác {curr['feelslike_c']}°C).\n"
            f"💨 Gió: {curr['wind_kph']}km/h {curr['wind_dir']}. UV: {curr['uv']}. Độ ẩm: {curr['humidity']}%.\n"
            f"🌬️ AQI (US-EPA): {curr['air_quality']['us-epa-index']}.\n"
            f"📅 Dự báo hôm nay: {forecast_data['condition']['text']}. Max: {forecast_data['maxtemp_c']}°C, Min: {forecast_data['mintemp_c']}°C.\n"
            f"🌅 Bình minh: {astro['sunrise']} | 🌇 Hoàng hôn: {astro['sunset']}\n"
        )
        
        # 2. Raw JSON for AI
        raw_json_str = json.dumps(weather, ensure_ascii=False)
        
        # 3. Generate Chart
        chart_path = WeatherService._generate_weather_chart(weather)
        
        return {
            "text": f"{summary}\n--- [RAW WEATHER DATA FOR AI] ---\n{raw_json_str}",
            "chart_path": chart_path
        }
