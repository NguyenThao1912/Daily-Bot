import io
import zipfile

from src.services.stock.stock_service import StockService


def build_cophieu68_zip(content: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("amibroker_all_data.txt", content)
    return buffer.getvalue()


def test_repair_cophieu68_header_stuck_to_first_row():
    content = (
        "<Ticker>,<DTYYYYMMDD>,<Open>,<High>,<Low>,<Close>,<Volume>"
        "FPT,20260319,77.7,77.8,76.6,76.8,11602900\n"
        "HPG,20260319,26.5,26.9,26.4,26.7,36837300\n"
    )
    repaired = StockService._repair_cophieu68_content(content)

    assert repaired.startswith("<Ticker>,<DTYYYYMMDD>,<Open>,<High>,<Low>,<Close>,<Volume>\nFPT,20260319")


def test_process_zip_data_parses_rows_when_header_is_stuck():
    content = (
        "<Ticker>,<DTYYYYMMDD>,<Open>,<High>,<Low>,<Close>,<Volume>"
        "FPT,20260319,77.7,77.8,76.6,76.8,11602900\n"
        "HPG,20260319,26.5,26.9,26.4,26.7,36837300\n"
    )
    zip_bytes = build_cophieu68_zip(content)

    rows = StockService.process_zip_data(zip_bytes)

    assert len(rows) == 2
    assert rows[0]["Ticker"] == "FPT"
    assert rows[0]["Date"] == "2026-03-19"
    assert rows[1]["Ticker"] == "HPG"


def test_process_zip_data_ignores_zero_date_rows_after_normalization():
    content = (
        "<Ticker>,<DTYYYYMMDD>,<Open>,<High>,<Low>,<Close>,<Volume>\n"
        "FPT,00000000,3.6,3.6,3.5,3.5,1887400\n"
        "FPT,20260319,77.7,77.8,76.6,76.8,11602900\n"
    )
    zip_bytes = build_cophieu68_zip(content)

    rows = StockService.process_zip_data(zip_bytes)

    assert len(rows) == 1
    assert rows[0]["Ticker"] == "FPT"
    assert rows[0]["Date"] == "2026-03-19"
