from typing import Any, Dict, List, Optional, TypedDict


class ServicePayload(TypedDict, total=False):
    text: str
    chart_path: Optional[str] | List[str]
    summary: Dict[str, Any]
    signals: Dict[str, Any]


class NewsEntry(TypedDict, total=False):
    title: str
    link: str
    pub_date: str
    source: str


class StockSnapshot(TypedDict, total=False):
    symbol: str
    date: str
    close: Optional[float]
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    volume: int
    change: Optional[float]
    pct_change: Optional[float]
    rsi: Optional[float]
    ma20: Optional[float]
    ma50: Optional[float]
    ma200: Optional[float]
    avg_volume: Optional[float]
    volume_ratio: Optional[float]
    distance_ma20: Optional[float]
    distance_ma50: Optional[float]
    strength: str


class CategoryResult(TypedDict):
    category: str
    content: str


class ReportContext(TypedDict):
    data_map: Dict[str, Any]
    upcoming_holidays: List[Dict[str, Any]]
