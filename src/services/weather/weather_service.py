import requests
import json
import os
from src.core.config import Config

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
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
            
            # Extract hourly data
            hours = weather_data['forecast']['forecastday'][0]['hour']
            times = [h['time'].split(' ')[1] for h in hours] # HH:MM
            temps = [h.get('temp_c', 0) for h in hours]
            humidities = [h.get('humidity', 0) for h in hours]
            
            # Create Output Dir
            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            chart_path = os.path.join(output_dir, "weather_chart.png")

            # Plotting Combo Chart OO
            fig = Figure(figsize=(12, 6))
            canvas = FigureCanvas(fig)
            ax1 = fig.add_subplot(111)

            # Temp on Left (Ax1)
            color_temp = '#e74c3c' # Red
            ax1.set_xlabel('Giờ')
            ax1.set_ylabel('Nhiệt độ (°C)', color=color_temp, fontweight='bold')
            ax1.plot(times, temps, color=color_temp, marker='o', linewidth=2.5, label='Nhiệt độ', markersize=6)
            ax1.tick_params(axis='y', labelcolor=color_temp)
            ax1.grid(True, linestyle='--', alpha=0.5)

            # Humidity on Right (Ax2)
            ax2 = ax1.twinx()
            color_hum = '#3498db' # Blue
            ax2.set_ylabel('Độ ẩm (%)', color=color_hum, fontweight='bold')
            ax2.plot(times, humidities, color=color_hum, marker='s', linewidth=2, label='Độ ẩm', linestyle='--', markersize=5)
            ax2.tick_params(axis='y', labelcolor=color_hum)
            
            # Combined Legend
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True, shadow=True)
            
            # Title
            date_str = weather_data['forecast']['forecastday'][0]['date']
            location_name = weather_data['location']['name']
            ax1.set_title(f"Biểu đồ Nhiệt độ & Độ ẩm - {location_name} ({date_str})", fontsize=14, fontweight='bold', pad=20)
            
            fig.tight_layout()
            canvas.print_png(chart_path)
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
