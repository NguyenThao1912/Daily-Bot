import aiohttp
import zipfile
import io
import csv
import logging
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

import requests

from src.constants import VN30_TICKERS
from src.config import Config
from src.types import StockSnapshot

logger = logging.getLogger(__name__)

STOCK_CHECK_URL = "https://www.cophieu68.vn/download/_amibroker.php?type=check"
STOCK_DOWNLOAD_URL = "https://www.cophieu68.vn/download/_amibroker.php?type=all"

class StockService:
    FIELD_ALIASES = {
        "ticker": "Ticker",
        "symbol": "Ticker",
        "<ticker>": "Ticker",
        "date": "Date",
        "<dtyyyymmdd>": "Date",
        "open": "Open",
        "<open>": "Open",
        "high": "High",
        "<high>": "High",
        "low": "Low",
        "<low>": "Low",
        "close": "Close",
        "<close>": "Close",
        "volume": "Volume",
        "<volume>": "Volume",
    }

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

                for file_name in file_names:
                    if file_name.endswith("/") or "__MACOSX" in file_name:
                        continue

                    with z.open(file_name) as f:
                        raw_bytes = f.read()
                        content = None
                        for encoding in ("utf-8-sig", "utf-8", "latin-1"):
                            try:
                                content = raw_bytes.decode(encoding)
                                break
                            except UnicodeDecodeError:
                                continue

                        if not content:
                            logger.warning(f"Skip undecodable file in zip: {file_name}")
                            continue

                        lines = [line for line in content.strip().splitlines() if line.strip()]
                        if not lines:
                            continue

                        reader = StockService._build_csv_reader(content)
                        file_rows = 0
                        for row in reader:
                            normalized_row = StockService._normalize_record(row)
                            if not normalized_row.get("Ticker") or not normalized_row.get("Date"):
                                continue
                            results.append(normalized_row)
                            file_rows += 1

                        logger.info(f"Processed {file_rows} rows from {file_name}")
        except Exception as e:
            logger.error(f"Error processing stock zip/csv: {e}")
        return results

    @staticmethod
    def _build_csv_reader(content: str):
        content = StockService._repair_cophieu68_content(content)
        first_line = content.strip().splitlines()[0].lower()
        if "ticker" in first_line or "symbol" in first_line or "<ticker>" in first_line:
            return csv.DictReader(io.StringIO(content))

        fieldnames = ["Ticker", "Date", "Open", "High", "Low", "Close", "Volume"]
        return csv.DictReader(io.StringIO(content), fieldnames=fieldnames)

    @staticmethod
    def _repair_cophieu68_content(content: str) -> str:
        header = "<Ticker>,<DTYYYYMMDD>,<Open>,<High>,<Low>,<Close>,<Volume>"
        if content.startswith(header) and not content.startswith(header + "\n"):
            repaired = re.sub(
                r"^(<Ticker>,<DTYYYYMMDD>,<Open>,<High>,<Low>,<Close>,<Volume>)([A-Za-z0-9._-]+,)",
                r"\1\n\2",
                content,
                count=1,
            )
            return repaired
        return content

    @staticmethod
    def _normalize_record(row: Dict[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {}
        for key, value in row.items():
            clean_key = (key or "").strip()
            canonical_key = StockService.FIELD_ALIASES.get(clean_key.lower(), clean_key)
            normalized[canonical_key] = value.strip() if isinstance(value, str) else value

        if normalized.get("Date"):
            raw_date = str(normalized["Date"]).strip()
            if raw_date in {"00000000", "0", ""}:
                normalized["Date"] = ""
            parsed = StockService._parse_date(raw_date)
            if parsed:
                normalized["Date"] = parsed.strftime("%Y-%m-%d")

        if normalized.get("Ticker"):
            normalized["Ticker"] = StockService._normalize_symbol(str(normalized["Ticker"]))

        return normalized

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
            symbol = StockService._normalize_symbol(
                row.get("Ticker") or row.get("Symbol") or row.get("<Ticker>") or ""
            )
            if not symbol or symbol.startswith("^"):
                continue
            grouped.setdefault(symbol, []).append(row)
        return {symbol: StockService._sort_records(items) for symbol, items in grouped.items()}

    @staticmethod
    def _build_snapshot(symbol: str, records: List[Dict[str, Any]]) -> Optional[StockSnapshot]:
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
        volume_ratio = (volume / avg_volume) if avg_volume not in (None, 0) else None
        distance_ma20 = ((close_price - ma20) / ma20 * 100) if close_price is not None and ma20 not in (None, 0) else None
        distance_ma50 = ((close_price - ma50) / ma50 * 100) if close_price is not None and ma50 not in (None, 0) else None

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
            "volume_ratio": volume_ratio,
            "distance_ma20": distance_ma20,
            "distance_ma50": distance_ma50,
            "strength": StockService._classify_strength(
                close_price=close_price,
                pct_change=pct_change,
                rsi=rsi,
                volume_ratio=volume_ratio,
                distance_ma20=distance_ma20,
                distance_ma50=distance_ma50,
            ),
        }

    @staticmethod
    def _classify_strength(
        close_price: Optional[float],
        pct_change: Optional[float],
        rsi: Optional[float],
        volume_ratio: Optional[float],
        distance_ma20: Optional[float],
        distance_ma50: Optional[float],
    ) -> str:
        score = 0
        if close_price is None:
            return "neutral"
        if pct_change is not None:
            if pct_change >= 1.5:
                score += 2
            elif pct_change <= -1.5:
                score -= 2
        if volume_ratio is not None:
            if volume_ratio >= 1.5:
                score += 1
            elif volume_ratio < 0.8:
                score -= 1
        if distance_ma20 is not None:
            score += 1 if distance_ma20 > 0 else -1
        if distance_ma50 is not None:
            score += 1 if distance_ma50 > 0 else -1
        if rsi is not None:
            if rsi >= 70:
                score -= 1
            elif rsi >= 55:
                score += 1
            elif rsi <= 35:
                score -= 1

        if score >= 3:
            return "strong"
        if score <= -2:
            return "weak"
        return "neutral"

    @staticmethod
    def _build_short_term_note(item: StockSnapshot) -> str:
        notes = []
        if item.get("pct_change") is not None and item["pct_change"] > 0:
            notes.append("gia dang giu xung luc tang")
        if item.get("volume_ratio") is not None and item["volume_ratio"] >= 1.2:
            notes.append("dong tien vao tot")
        if item.get("distance_ma20") is not None and item["distance_ma20"] > 0:
            notes.append("dang nam tren MA20")
        if item.get("rsi") is not None and 45 <= item["rsi"] <= 68:
            notes.append("RSI con du dia")
        return ", ".join(notes[:3]) if notes else "theo doi them"

    @staticmethod
    def _round_metric(value: Optional[float], digits: int = 2) -> Optional[float]:
        if value is None:
            return None
        return round(value, digits)

    @staticmethod
    def _is_short_term_candidate(item: StockSnapshot) -> bool:
        pct_change = item.get("pct_change")
        volume_ratio = item.get("volume_ratio")
        rsi = item.get("rsi")
        distance_ma20 = item.get("distance_ma20")
        distance_ma50 = item.get("distance_ma50")

        if pct_change is None or volume_ratio is None or rsi is None:
            return False

        return (
            pct_change >= 0.5
            and volume_ratio >= 1.1
            and 45 <= rsi <= 68
            and (distance_ma20 is None or distance_ma20 >= 0)
            and (distance_ma50 is None or distance_ma50 >= -2)
        )

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
    def _generate_vn30_chart(snapshots: List[Dict[str, Any]]) -> Optional[str]:
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

            chart_data = [item for item in snapshots if item.get("pct_change") is not None]
            if not chart_data:
                return None

            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            chart_path = os.path.join(output_dir, "stock_vn30_chart.png")
            symbols = [item["symbol"] for item in chart_data]
            pct_changes = [item["pct_change"] for item in chart_data]
            colors = ["#16a34a" if value >= 0 else "#dc2626" for value in pct_changes]

            fig = Figure(figsize=(12, 6))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            bars = ax.bar(symbols, pct_changes, color=colors)
            ax.set_title("Bien dong VN30 tu du lieu cophieu68")
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
        target_symbols = [symbol for symbol in VN30_TICKERS if symbol]
        logger.info(
            "cophieu68 vn30 matching: records=%s symbols=%s vn30=%s",
            len(all_records),
            len(grouped_records),
            ",".join(target_symbols),
        )

        snapshots: List[StockSnapshot] = []
        missing_symbols: List[str] = []
        for symbol in target_symbols:
            symbol_records = grouped_records.get(symbol)
            if not symbol_records:
                missing_symbols.append(symbol)
                continue

            snapshot = StockService._build_snapshot(symbol, symbol_records)
            if snapshot:
                snapshots.append(snapshot)

        if not snapshots:
            available_sample = ", ".join(sorted(list(grouped_records.keys()))[:20]) if grouped_records else "none"
            return {
                "text": (
                    "Co du lieu cophieu68 nhung khong tim thay ma nao trong VN30. "
                    f"Mau ma tim thay: {available_sample}"
                ),
                "chart_path": None,
            }

        snapshots.sort(
            key=lambda item: (
                item.get("pct_change") is not None,
                item.get("pct_change") or -9999,
                item.get("volume_ratio") or -9999,
            ),
            reverse=True,
        )
        top_gainers = sorted(
            [item for item in snapshots if item.get("pct_change") is not None],
            key=lambda item: (item["pct_change"], item.get("volume_ratio") or 0),
            reverse=True,
        )[:5]
        top_losers = sorted(
            [item for item in snapshots if item.get("pct_change") is not None],
            key=lambda item: (item["pct_change"], -(item.get("volume_ratio") or 0)),
        )[:5]
        top_volume = sorted(
            [item for item in snapshots if item.get("volume_ratio") is not None],
            key=lambda item: (item["volume_ratio"], item.get("pct_change") or 0),
            reverse=True,
        )[:5]
        short_term_candidates = sorted(
            [item for item in snapshots if StockService._is_short_term_candidate(item)],
            key=lambda item: (
                item.get("strength") == "strong",
                item.get("volume_ratio") or 0,
                item.get("pct_change") or 0,
            ),
            reverse=True,
        )[:6]

        advancers = sum(1 for item in snapshots if (item.get("pct_change") or 0) > 0)
        decliners = sum(1 for item in snapshots if (item.get("pct_change") or 0) < 0)
        above_ma20 = sum(1 for item in snapshots if (item.get("distance_ma20") or -999) >= 0)
        above_ma50 = sum(1 for item in snapshots if (item.get("distance_ma50") or -999) >= 0)
        strong_count = sum(1 for item in snapshots if item.get("strength") == "strong")
        weak_count = sum(1 for item in snapshots if item.get("strength") == "weak")
        avg_rsi_values = [item["rsi"] for item in snapshots if item.get("rsi") is not None]
        avg_volume_values = [item["volume_ratio"] for item in snapshots if item.get("volume_ratio") is not None]
        breadth_ratio = (advancers / len(snapshots)) if snapshots else 0
        avg_rsi = (sum(avg_rsi_values) / len(avg_rsi_values)) if avg_rsi_values else None
        avg_volume_ratio = (sum(avg_volume_values) / len(avg_volume_values)) if avg_volume_values else None

        regime = "can_bang"
        if breadth_ratio >= 0.6 and strong_count >= weak_count + 4:
            regime = "broad_strength"
        elif breadth_ratio <= 0.4 and weak_count >= strong_count + 3:
            regime = "broad_weakness"
        elif breadth_ratio >= 0.5 and avg_volume_ratio is not None and avg_volume_ratio < 1:
            regime = "fragile_market"
        elif strong_count > 0 and weak_count > 0:
            regime = "selective_rebound"

        coverage = round(len(snapshots) / len(target_symbols), 2) if target_symbols else 0
        confidence_score = 0.35
        confidence_score += 0.25 * coverage
        confidence_score += 0.15 if len(avg_rsi_values) >= 20 else 0
        confidence_score += 0.15 if len(avg_volume_values) >= 20 else 0
        confidence_score += 0.10 if len(top_gainers) >= 5 and len(top_losers) >= 5 else 0
        confidence_score = min(round(confidence_score, 2), 1.0)

        if confidence_score >= 0.8:
            confidence = "high"
        elif confidence_score >= 0.6:
            confidence = "medium"
        else:
            confidence = "low"

        rows = []
        for item in snapshots:
            close_text = f"{item['close']:.2f}" if item.get("close") is not None else "N/A"
            pct_text = f"{item['pct_change']:+.2f}%" if item.get("pct_change") is not None else "N/A"
            rsi_text = f"{item['rsi']:.1f}" if item.get("rsi") is not None else "N/A"
            volume_text = f"{item['volume']:,}" if item.get("volume") else "0"
            ma20_text = f"{item['ma20']:.2f}" if item.get("ma20") is not None else "N/A"
            ma50_text = f"{item['ma50']:.2f}" if item.get("ma50") is not None else "N/A"
            vol_ratio_text = f"{item['volume_ratio']:.2f}x" if item.get("volume_ratio") is not None else "N/A"
            dist_ma20_text = f"{item['distance_ma20']:+.2f}%" if item.get("distance_ma20") is not None else "N/A"
            dist_ma50_text = f"{item['distance_ma50']:+.2f}%" if item.get("distance_ma50") is not None else "N/A"
            rows.append(
                "<tr>"
                f"<td><b>{item['symbol']}</b></td>"
                f"<td>{close_text}</td>"
                f"<td>{pct_text}</td>"
                f"<td>{rsi_text}</td>"
                f"<td>{ma20_text}</td>"
                f"<td>{ma50_text}</td>"
                f"<td>{vol_ratio_text}</td>"
                f"<td>{dist_ma20_text}</td>"
                f"<td>{dist_ma50_text}</td>"
                f"<td>{item['strength']}</td>"
                "</tr>"
            )

        lines = [
            "DU LIEU VN30 TU COPHIEU68:",
            f"Ngay giao dich gan nhat: {snapshots[0]['date']}",
            "BANG TOAN CANH VN30:",
            "<table>",
            "<tr><th>Ma</th><th>Close</th><th>% Change</th><th>RSI</th><th>MA20</th><th>MA50</th><th>VolRatio</th><th>DistMA20</th><th>DistMA50</th><th>Strength</th></tr>",
            *rows,
            "</table>",
        ]

        if top_gainers:
            lines.append("<div><b>TOP TANG</b></div>")
            lines.append("<ul>")
            for item in top_gainers:
                rsi_text = f"{item['rsi']:.1f}" if item.get("rsi") is not None else "N/A"
                lines.append(
                    f"<li><b>{item['symbol']}</b>: {item['pct_change']:+.2f}% | RSI {rsi_text}</li>"
                )
            lines.append("</ul>")

        if top_losers:
            lines.append("<div><b>TOP GIAM</b></div>")
            lines.append("<ul>")
            for item in top_losers:
                rsi_text = f"{item['rsi']:.1f}" if item.get("rsi") is not None else "N/A"
                lines.append(f"<li><b>{item['symbol']}</b>: {item['pct_change']:+.2f}% | RSI {rsi_text}</li>")
            lines.append("</ul>")

        if top_volume:
            lines.append("<div><b>TOP VOLUME</b></div>")
            lines.append("<ul>")
            for item in top_volume:
                vol_ratio_text = f"{item['volume_ratio']:.2f}x" if item.get("volume_ratio") is not None else "N/A"
                volume_text = f"{item['volume']:,}" if item.get("volume") else "0"
                lines.append(
                    f"<li><b>{item['symbol']}</b>: Volume {volume_text} | VolRatio {vol_ratio_text} | Strength {item['strength']}</li>"
                )
            lines.append("</ul>")

        if short_term_candidates:
            lines.extend([
                "<div><b>UNG VIEN MUA NGAN HAN</b></div>",
                "<div>Luu y: day la bang ung vien ky thuat de theo doi cho luot song ngan han, khong phai khuyen nghi mua chac chan.</div>",
                "<table>",
                "<tr><th>Ma</th><th>% Change</th><th>RSI</th><th>VolRatio</th><th>DistMA20</th><th>Strength</th><th>Ly do theo doi</th></tr>",
            ])
            for item in short_term_candidates:
                pct_text = f"{item['pct_change']:+.2f}%" if item.get("pct_change") is not None else "N/A"
                rsi_text = f"{item['rsi']:.1f}" if item.get("rsi") is not None else "N/A"
                vol_ratio_text = f"{item['volume_ratio']:.2f}x" if item.get("volume_ratio") is not None else "N/A"
                dist_ma20_text = f"{item['distance_ma20']:+.2f}%" if item.get("distance_ma20") is not None else "N/A"
                note_text = StockService._build_short_term_note(item)
                lines.append(
                    "<tr>"
                    f"<td><b>{item['symbol']}</b></td>"
                    f"<td>{pct_text}</td>"
                    f"<td>{rsi_text}</td>"
                    f"<td>{vol_ratio_text}</td>"
                    f"<td>{dist_ma20_text}</td>"
                    f"<td>{item['strength']}</td>"
                    f"<td>{note_text}</td>"
                    "</tr>"
                )
            lines.append("</table>")

        if missing_symbols:
            lines.append("Ma VN30 khong tim thay trong goi du lieu: " + ", ".join(sorted(set(missing_symbols))))

        chart_path = StockService._generate_vn30_chart(snapshots)
        summary = {
            "as_of": snapshots[0]["date"],
            "coverage_ratio": coverage,
            "advancers": advancers,
            "decliners": decliners,
            "above_ma20": above_ma20,
            "above_ma50": above_ma50,
            "strong_count": strong_count,
            "weak_count": weak_count,
            "avg_rsi": StockService._round_metric(avg_rsi, 1),
            "avg_volume_ratio": StockService._round_metric(avg_volume_ratio),
            "regime": regime,
            "confidence": confidence,
            "confidence_score": confidence_score,
            "top_gainers": [item["symbol"] for item in top_gainers],
            "top_losers": [item["symbol"] for item in top_losers],
            "top_volume": [item["symbol"] for item in top_volume],
            "missing_symbols": sorted(set(missing_symbols)),
        }
        signals = {
            "breadth_positive": breadth_ratio >= 0.55,
            "breadth_negative": breadth_ratio <= 0.45,
            "momentum_supportive": bool(avg_volume_ratio is not None and avg_volume_ratio >= 1.0 and avg_rsi is not None and avg_rsi >= 50),
            "market_pressure": bool(avg_rsi is not None and avg_rsi < 45 and weak_count >= strong_count),
        }
        return {
            "text": "\n".join(lines),
            "chart_path": chart_path,
            "summary": summary,
            "signals": signals,
        }
