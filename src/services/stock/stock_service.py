import os
import aiohttp
import zipfile
import io
import csv
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

STOCK_CHECK_URL = "https://www.cophieu68.vn/download/_amibroker.php?type=check"
STOCK_DOWNLOAD_URL = "https://www.cophieu68.vn/download/_amibroker.php?type=all"

class StockService:
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
