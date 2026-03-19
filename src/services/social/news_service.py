import os
import urllib.parse
import xml.etree.ElementTree as ET

import requests

from src.config import Config

class NewsService:
    GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
    GOOGLE_NEWS_TOP_URL = "https://news.google.com/rss"
    NEWS_QUERIES = {
        "general": "Vietnam OR world news when:1d",
        "featured": "Vietnam headlines OR breaking news when:1d",
        "business": "Vietnam business OR economy OR market when:1d",
        "tech": "AI OR technology OR startup OR software when:1d",
    }

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
        entries = NewsService._fetch_google_news(news_type, limit)
        if not entries:
            return "Không lấy được tin tức."

        top_news = [f"- [{entry['title']}]({entry['link']})" for entry in entries]
        return "\n".join(top_news)

    @staticmethod
    def _build_google_news_url(news_type: str, limit: int) -> str:
        query = NewsService.NEWS_QUERIES.get(news_type, NewsService.NEWS_QUERIES["general"])
        params = {
            "q": query,
            "hl": "vi",
            "gl": "VN",
            "ceid": "VN:vi",
        }
        base_url = f"{NewsService.GOOGLE_NEWS_RSS_URL}?{urllib.parse.urlencode(params)}"
        return f"{base_url}&num={limit}"

    @staticmethod
    def _fetch_google_news(news_type="general", limit=20):
        try:
            url = NewsService._build_google_news_url(news_type, limit)
            response = requests.get(url, timeout=20)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            items = root.findall(".//item")
            entries = []
            seen_links = set()

            for item in items:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if not title or not link or link in seen_links:
                    continue

                seen_links.add(link)
                entries.append({
                    "title": title,
                    "link": link,
                    "pub_date": (item.findtext("pubDate") or "").strip(),
                    "source": (item.findtext("source") or "").strip(),
                })
                if len(entries) >= limit:
                    break

            if entries:
                return entries

            if news_type in {"general", "featured"}:
                return NewsService._fetch_google_top_news(limit)
            return []
        except Exception as e:
            print(f"⚠️ Google News Error ({news_type}): {e}")
            if news_type in {"general", "featured"}:
                return NewsService._fetch_google_top_news(limit)
            return []

    @staticmethod
    def _fetch_google_top_news(limit=20):
        try:
            params = {"hl": "vi", "gl": "VN", "ceid": "VN:vi"}
            url = f"{NewsService.GOOGLE_NEWS_TOP_URL}?{urllib.parse.urlencode(params)}"
            response = requests.get(url, timeout=20)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            entries = []
            for item in root.findall(".//item")[:limit]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if not title or not link:
                    continue
                entries.append({"title": title, "link": link})
            return entries
        except Exception as e:
            print(f"⚠️ Google Top News Error: {e}")
            return []

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
    def fetch_trends(limit=30):
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
