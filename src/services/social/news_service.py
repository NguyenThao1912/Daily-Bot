import requests
import os
from src.config import Config

class NewsService:
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
    def fetch_news(news_type="general", limit=20):
        data = NewsService._fetch_from_worker("/news", params={"type": news_type, "limit": limit})
        if not data or 'data' not in data:
            return "Không lấy được tin tức."
        
        top_news = [f"- [{entry['title']}]({entry['link']})" for entry in data['data']]
        return "\n".join(top_news)

    @staticmethod
    def _generate_trend_chart(trends_data):
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
            
            # Simple data extraction
            titles = []
            traffic = []
            
            # Limit to top 15 for chart
            chart_data = trends_data[:15]
            
            for t in chart_data: 
                titles.append(t['title'][:25] + "...") # Slightly longer title
                # Parse traffic string "20.000+" -> 20000
                tf_str = t['traffic'].replace('.', '').replace(',', '').replace('+', '')
                try: traffic.append(int(tf_str))
                except: traffic.append(0)
            
            # Create Output Dir
            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            chart_path = os.path.join(output_dir, "trend_chart.png")

            # Dynamic Height: Base 2 + 0.5 per item. For 15 items -> ~9.5 inch height
            fig_height = max(6, len(chart_data) * 0.5 + 2)
            
            # Plot properties (OO)
            fig = Figure(figsize=(10, fig_height))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            
            bars = ax.barh(titles, traffic, color='#3498db') # Blue
            ax.set_xlabel('Lượt tìm kiếm')
            ax.set_title(f'Top {len(chart_data)} Google Trends Vietnam')
            ax.invert_yaxis() # Top trend at top
            
            # Add value labels
            for bar in bars:
                width = bar.get_width()
                ax.text(width, bar.get_y() + bar.get_height()/2, f'{int(width):,}', 
                         ha='left', va='center', fontweight='bold')

            fig.tight_layout()
            canvas.print_png(chart_path)
            return chart_path
        except Exception as e:
            print(f"⚠️ Trend Chart Error: {e}")
            return None

    @staticmethod
    def fetch_trends(limit=15):
        data = NewsService._fetch_from_worker("/trends", params={"limit": limit})
        if not data or 'data' not in data:
            return {"text": "Không lấy được Google Trends.", "chart_path": None}
        
        trends_list = data['data']
        trends_text = []
        for entry in trends_list:
            trends_text.append(f"- {entry['title']} ({entry['traffic']} lượt tìm): {entry['link']}")
        
        chart_path = NewsService._generate_trend_chart(trends_list)
        
        return {
            "text": "\n".join(trends_text),
            "chart_path": chart_path
        }
