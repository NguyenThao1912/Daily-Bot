import asyncio
import logging
import sys
import os

# Thêm directory hiện tại vào sys.path để import src
sys.path.append(os.getcwd())

from src.services.stock.runner import run_daily_stock_report
from dotenv import load_dotenv

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def main():
    load_dotenv()
    try:
        results = await run_daily_stock_report(send_telegram=True)
        # print(f"Results: {results}")
    except Exception as e:
        logger.error(f"Lỗi khi chạy Stock Report: {e}")

if __name__ == "__main__":
    asyncio.run(main())
