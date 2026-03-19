import aiohttp
import zipfile
import io
import csv
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

import requests

from src.config import Config

logger = logging.getLogger(__name__)

STOCK_CHECK_URL = "https://www.cophieu68.vn/download/_amibroker.php?type=check"
STOCK_DOWNLOAD_URL = "https://www.cophieu68.vn/download/_amibroker.php?type=all"

class StockService:
    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        raw = (symbol or "").strip().upper()
        if raw.startswith("^"):
            return raw
        return raw.replace(".VN", "").replace(".HOSE", "").replace(".HNX", "").replace(".UPCOM", "")

    @staticmethod
    def _parse_float(value: Any) -> Optional[float]:
        try:
            if value is None or value == "":
                return None
            return float(str(value).replace(",", ""))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_int(value: Any) -> int:
        try:
            if value is None or value == "":
                return 0
            return int(float(str(value).replace(",", "")))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _parse_date(value: str) -> Optional[datetime]:
        for fmt in ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(str(value).strip(), fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _sort_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(
            records,
            key=lambda row: StockService._parse_date(row.get("Date", "")) or datetime.min,
        )

    @staticmethod
    async def check_alerts() -> Optional[str]:
        """
        Kiểm tra thông báo mới từ cophieu68.vn (type=check)
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(STOCK_CHECK_URL) as response:
                    text = await response.text()
                    if text.strip() and "error" not in text.lower():
                        return text.strip()
            except Exception as e:
                logger.error(f"Error checking stock alerts: {e}")
        return None

    @staticmethod
    async def download_eod_data() -> Optional[bytes]:
        """
        Tải dữ liệu EOD (zip) từ cophieu68.vn (type=all)
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(STOCK_DOWNLOAD_URL) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.error(f"Failed to download stock data: HTTP {response.status}")
            except Exception as e:
                logger.error(f"Error downloading stock data: {e}")
        return None

    @staticmethod
    def process_zip_data(zip_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Giải nén và parse dữ liệu CSV từ zip bytes
        """
        results = []
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                file_names = z.namelist()
                if not file_names:
                    logger.error("Zip file is empty")
                    return []
                
                csv_filename = file_names[0]
                with z.open(csv_filename) as f:
                    content = f.read().decode('utf-8')
                    # Format cophieu68 chuẩn: Ticker,Date,Open,High,Low,Close,Volume
                    lines = content.strip().split('\n')
                    if not lines:
                        return []
                    
                    first_line = lines[0].lower()
                    if 'ticker' in first_line or 'symbol' in first_line:
                        reader = csv.DictReader(io.StringIO(content))
                    else:
                        fieldnames = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                        reader = csv.DictReader(io.StringIO(content), fieldnames=fieldnames)
                    
                    for row in reader:
                        results.append(row)
        except Exception as e:
            logger.error(f"Error processing stock zip/csv: {e}")
        return results

    @staticmethod
    def _download_eod_data_sync() -> Optional[bytes]:
        try:
            response = requests.get(STOCK_DOWNLOAD_URL, timeout=60)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Error downloading stock data synchronously: {e}")
            return None

    @staticmethod
    def _fetch_all_records_sync() -> List[Dict[str, Any]]:
        zip_bytes = StockService._download_eod_data_sync()
        if not zip_bytes:
            return []
        return StockService.process_zip_data(zip_bytes)

    @staticmethod
    def _group_records_by_symbol(records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for row in records:
            symbol = StockService._normalize_symbol(row.get("Ticker", ""))
            if not symbol or symbol.startswith("^"):
                continue
            grouped.setdefault(symbol, []).append(row)
        return {symbol: StockService._sort_records(items) for symbol, items in grouped.items()}

    @staticmethod
    def _build_snapshot(symbol: str, records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        ordered = StockService._sort_records(records)
        if not ordered:
            return None

        latest = ordered[-1]
        previous = ordered[-2] if len(ordered) > 1 else None
        close_price = StockService._parse_float(latest.get("Close"))
        open_price = StockService._parse_float(latest.get("Open"))
        high_price = StockService._parse_float(latest.get("High"))
        low_price = StockService._parse_float(latest.get("Low"))
        volume = StockService._parse_int(latest.get("Volume"))
        previous_close = StockService._parse_float(previous.get("Close")) if previous else None

        change = None
        pct_change = None
        if close_price is not None and previous_close not in (None, 0):
            change = close_price - previous_close
            pct_change = (change / previous_close) * 100

        rsi, ma20, ma50, ma200, avg_volume = StockService.calculate_technical_indicators(ordered)

        return {
            "symbol": symbol,
            "date": latest.get("Date", ""),
            "close": close_price,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "volume": volume,
            "change": change,
            "pct_change": pct_change,
            "rsi": rsi,
            "ma20": ma20,
            "ma50": ma50,
            "ma200": ma200,
            "avg_volume": avg_volume,
        }

    @staticmethod
    def calculate_technical_indicators(records: List[Dict[str, Any]]) -> tuple[Optional[float], Optional[float], Optional[float], Optional[float], Optional[float]]:
        closes = [StockService._parse_float(r.get("Close")) for r in records]
        closes = [c for c in closes if c is not None]
        volumes = [StockService._parse_int(r.get("Volume")) for r in records]
        volumes = [v for v in volumes if v > 0]

        def sma(values: List[float], period: int) -> Optional[float]:
            if len(values) < period:
                return None
            return sum(values[-period:]) / period

        rsi = None
        if len(closes) >= 15:
            gains: List[float] = []
            losses: List[float] = []
            for idx in range(len(closes) - 14, len(closes)):
                diff = closes[idx] - closes[idx - 1]
                gains.append(max(diff, 0))
                losses.append(abs(min(diff, 0)))
            avg_gain = sum(gains) / 14
            avg_loss = sum(losses) / 14
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

        return (
            rsi,
            sma(closes, 20),
            sma(closes, 50),
            sma(closes, 200),
            sma([float(v) for v in volumes], 20),
        )

    @staticmethod
    def _generate_watchlist_chart(snapshots: List[Dict[str, Any]]) -> Optional[str]:
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

            chart_data = [item for item in snapshots if item.get("pct_change") is not None]
            if not chart_data:
                return None

            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            chart_path = os.path.join(output_dir, "stock_watchlist_chart.png")
            symbols = [item["symbol"] for item in chart_data]
            pct_changes = [item["pct_change"] for item in chart_data]
            colors = ["#16a34a" if value >= 0 else "#dc2626" for value in pct_changes]

            fig = Figure(figsize=(12, 6))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            bars = ax.bar(symbols, pct_changes, color=colors)
            ax.set_title("Bien dong watchlist tu du lieu cophieu68")
            ax.set_ylabel("% thay doi")
            ax.axhline(0, color="#111827", linewidth=0.8)
            ax.grid(True, axis="y", linestyle="--", alpha=0.4)

            for bar, value in zip(bars, pct_changes):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    value,
                    f"{value:+.2f}%",
                    ha="center",
                    va="bottom" if value >= 0 else "top",
                    fontsize=9,
                )

            fig.tight_layout()
            canvas.print_png(chart_path)
            return chart_path
        except Exception as e:
            logger.error(f"Error generating stock chart: {e}")
            return None

    @staticmethod
    def fetch_stock_analysis() -> Dict[str, Any]:
        all_records = StockService._fetch_all_records_sync()
        if not all_records:
            return {
                "text": "Khong lay duoc du lieu co phieu tu cophieu68.",
                "chart_path": None,
            }

        grouped_records = StockService._group_records_by_symbol(all_records)
        watchlist = [
            StockService._normalize_symbol(symbol)
            for symbol in Config.STOCK_WATCHLIST
            if StockService._normalize_symbol(symbol) and not StockService._normalize_symbol(symbol).startswith("^")
        ]

        snapshots: List[Dict[str, Any]] = []
        missing_symbols: List[str] = []
        for symbol in watchlist:
            symbol_records = grouped_records.get(symbol)
            if not symbol_records:
                missing_symbols.append(symbol)
                continue

            snapshot = StockService._build_snapshot(symbol, symbol_records)
            if snapshot:
                snapshots.append(snapshot)

        if not snapshots:
            return {
                "text": "Co du lieu cophieu68 nhung khong tim thay ma nao trong watchlist.",
                "chart_path": None,
            }

        lines = [
            "DU LIEU WATCHLIST TU COPHIEU68:",
            f"Ngay giao dich gan nhat: {snapshots[0]['date']}",
        ]
        for item in snapshots:
            close_text = f"{item['close']:.2f}" if item.get("close") is not None else "N/A"
            change_text = f"{item['change']:+.2f}" if item.get("change") is not None else "N/A"
            pct_text = f"{item['pct_change']:+.2f}%" if item.get("pct_change") is not None else "N/A"
            rsi_text = f"{item['rsi']:.1f}" if item.get("rsi") is not None else "N/A"
            volume_text = f"{item['volume']:,}" if item.get("volume") else "0"
            ma20_text = f"{item['ma20']:.2f}" if item.get("ma20") is not None else "N/A"
            ma50_text = f"{item['ma50']:.2f}" if item.get("ma50") is not None else "N/A"
            lines.append(
                f"- {item['symbol']}: Close {close_text} | Change {change_text} ({pct_text}) | "
                f"RSI {rsi_text} | MA20 {ma20_text} | MA50 {ma50_text} | Volume {volume_text}"
            )

        if missing_symbols:
            lines.append("Ma khong tim thay trong goi du lieu: " + ", ".join(sorted(set(missing_symbols))))

        chart_path = StockService._generate_watchlist_chart(snapshots)
        return {
            "text": "\n".join(lines),
            "chart_path": chart_path,
        }
