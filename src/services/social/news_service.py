import os
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List

import requests

from src.constants import (
    GOOGLE_NEWS_EXCLUDED_KEYWORDS,
    GOOGLE_NEWS_PRIORITY_KEYWORDS,
    GOOGLE_NEWS_QUERIES,
    VN30_COMPANY_ALIASES,
    VN30_IMPACT_KEYWORDS,
)
from src.config import Config
from src.types import NewsEntry

class NewsService:
    GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
    GOOGLE_NEWS_TOP_URL = "https://news.google.com/rss"

    @staticmethod
    def _sanitize_chart_label(value: str, fallback: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            return fallback

        # DejaVu Sans in CI does not cover Hangul well; strip those glyphs from chart labels
        # so trend chart rendering stays quiet and deterministic.
        filtered = "".join(
            ch for ch in cleaned
            if not (0x1100 <= ord(ch) <= 0x11FF or 0x3130 <= ord(ch) <= 0x318F or 0xAC00 <= ord(ch) <= 0xD7AF)
        ).strip()
        if not filtered:
            return fallback
        return filtered

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
        entries = NewsService.fetch_news_entries(news_type, limit)
        if not entries:
            return "Không lấy được tin tức."

        top_news = [f"- [{entry['title']}]({entry['link']})" for entry in entries]
        return "\n".join(top_news)

    @staticmethod
    def fetch_news_entries(news_type="general", limit=20) -> List[NewsEntry]:
        return NewsService._fetch_google_news(news_type, limit)

    @staticmethod
    def fetch_vn30_impact_news(limit=8) -> List[NewsEntry]:
        candidate_entries: List[NewsEntry] = []
        for news_type in ("general", "featured", "business"):
            candidate_entries.extend(NewsService.fetch_news_entries(news_type, limit=limit))

        ranked = NewsService._rank_vn30_impact_entries(candidate_entries, limit)
        return [entry for _, entry in ranked[:limit]]

    @staticmethod
    def _build_google_news_url(query: str, limit: int) -> str:
        params = {
            "q": query,
            "hl": "vi",
            "gl": "VN",
            "ceid": "VN:vi",
        }
        base_url = f"{NewsService.GOOGLE_NEWS_RSS_URL}?{urllib.parse.urlencode(params)}"
        return f"{base_url}&num={limit}"

    @staticmethod
    def _fetch_google_news(news_type="general", limit=20) -> List[NewsEntry]:
        try:
            queries = GOOGLE_NEWS_QUERIES.get(news_type, GOOGLE_NEWS_QUERIES["general"])
            per_query_limit = max(limit, 10)
            merged_entries: List[NewsEntry] = []

            for query in queries:
                url = NewsService._build_google_news_url(query, per_query_limit)
                response = requests.get(url, timeout=20)
                response.raise_for_status()

                root = ET.fromstring(response.content)
                items = root.findall(".//item")
                for item in items:
                    title = (item.findtext("title") or "").strip()
                    link = (item.findtext("link") or "").strip()
                    if not title or not link:
                        continue

                    entry = {
                        "title": title,
                        "link": link,
                        "pub_date": (item.findtext("pubDate") or "").strip(),
                        "source": (item.findtext("source") or "").strip(),
                    }
                    if NewsService._is_relevant_entry(entry, news_type):
                        merged_entries.append(entry)

            entries = NewsService._rank_and_dedupe_entries(merged_entries, news_type, limit)

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
    def _normalize_text(value: str) -> str:
        return " ".join((value or "").lower().split())

    @staticmethod
    def _is_relevant_entry(entry: NewsEntry, news_type: str) -> bool:
        title = NewsService._normalize_text(entry.get("title", ""))
        source = NewsService._normalize_text(entry.get("source", ""))
        text = f"{title} {source}"

        if any(keyword in text for keyword in GOOGLE_NEWS_EXCLUDED_KEYWORDS):
            return False

        if news_type == "tech":
            return any(keyword in text for keyword in GOOGLE_NEWS_PRIORITY_KEYWORDS["tech"])

        return True

    @staticmethod
    def _score_entry(entry: NewsEntry, news_type: str) -> int:
        title = NewsService._normalize_text(entry.get("title", ""))
        source = NewsService._normalize_text(entry.get("source", ""))
        text = f"{title} {source}"
        score = 0

        for keyword in GOOGLE_NEWS_PRIORITY_KEYWORDS.get(news_type, []):
            if keyword.lower() in text:
                score += 3 if keyword.lower() in title else 1

        if any(token in title for token in ["viet nam", "vietnam"]):
            score += 2
        if source:
            score += 1
        return score

    @staticmethod
    def _rank_and_dedupe_entries(
        entries: List[NewsEntry],
        news_type: str,
        limit: int,
    ) -> List[NewsEntry]:
        ranked: list[tuple[int, NewsEntry]] = []
        seen_keys = set()

        for entry in entries:
            title = (entry.get("title") or "").strip()
            link = (entry.get("link") or "").strip()
            title_key = NewsService._normalize_text(title)
            link_key = link.split("?")[0]
            dedupe_key = (title_key, link_key)
            if not title_key or not link_key or dedupe_key in seen_keys:
                continue

            seen_keys.add(dedupe_key)
            ranked.append((NewsService._score_entry(entry, news_type), entry))

        ranked.sort(
            key=lambda item: (
                -item[0],
                NewsService._normalize_text(item[1].get("pub_date", "")),
            ),
        )
        return [entry for _, entry in ranked[:limit]]

    @staticmethod
    def _fetch_google_top_news(limit=20) -> List[NewsEntry]:
        try:
            params = {"hl": "vi", "gl": "VN", "ceid": "VN:vi"}
            url = f"{NewsService.GOOGLE_NEWS_TOP_URL}?{urllib.parse.urlencode(params)}"
            response = requests.get(url, timeout=20)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            entries: List[NewsEntry] = []
            for item in root.findall(".//item")[: max(limit * 2, 20)]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if not title or not link:
                    continue
                entry = {
                    "title": title,
                    "link": link,
                    "pub_date": (item.findtext("pubDate") or "").strip(),
                    "source": (item.findtext("source") or "").strip(),
                }
                if NewsService._is_relevant_entry(entry, "general"):
                    entries.append(entry)
            return NewsService._rank_and_dedupe_entries(entries, "general", limit)
        except Exception as e:
            print(f"⚠️ Google Top News Error: {e}")
            return []

    @staticmethod
    def _score_vn30_impact_entry(entry: NewsEntry) -> int:
        title = NewsService._normalize_text(entry.get("title", ""))
        source = NewsService._normalize_text(entry.get("source", ""))
        text = f"{title} {source}"
        score = 0

        for keyword in VN30_IMPACT_KEYWORDS:
            if keyword.lower() in text:
                score += 4 if keyword.lower() in title else 2

        matched_symbols = 0
        for symbol, aliases in VN30_COMPANY_ALIASES.items():
            if any(alias in text for alias in aliases):
                matched_symbols += 1
                score += 6
                if symbol.lower() in title:
                    score += 2

        if any(token in title for token in ["viet nam", "vietnam"]):
            score += 2
        return score + min(matched_symbols, 3)

    @staticmethod
    def _rank_vn30_impact_entries(
        entries: List[NewsEntry],
        limit: int,
    ) -> List[tuple[int, NewsEntry]]:
        ranked: list[tuple[int, NewsEntry]] = []
        seen_titles = set()

        for entry in entries:
            title = (entry.get("title") or "").strip()
            normalized_title = NewsService._normalize_text(title)
            if not normalized_title or normalized_title in seen_titles:
                continue

            score = NewsService._score_vn30_impact_entry(entry)
            if score <= 0:
                continue

            seen_titles.add(normalized_title)
            ranked.append((score, entry))

        ranked.sort(
            key=lambda item: (
                -item[0],
                NewsService._normalize_text(item[1].get("pub_date", "")),
            ),
        )
        return ranked

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
            
            for idx, t in enumerate(chart_data, start=1):
                raw_title = t.get('title', '')
                safe_title = NewsService._sanitize_chart_label(raw_title, f"Trend {idx}")
                if len(safe_title) > 25:
                    safe_title = safe_title[:25] + "..."
                titles.append(safe_title)
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
