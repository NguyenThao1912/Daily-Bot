import asyncio
import logging
import os
import sys
from datetime import datetime

# Thêm root dự án vào sys.path để import được src
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.core.config import Config
from src.services.jira import run_daily_jira_report

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("JiraStandaloneRunner")

async def main():
    project_key = os.getenv("JIRA_DEFAULT_PROJECT", "PROJ")
    
    logger.info(f"🚦 Bắt đầu chạy JIRA Report riêng biệt: {project_key}")
    
    try:
        result = await run_daily_jira_report(
            project_key=project_key,
            send_telegram=True,
            send_slack=True, # Bật nếu có config
            export_excel=True
        )
        
        if result.get("errors"):
            logger.error(f"❌ Có lỗi khi gửi báo cáo: {result['errors']}")
        else:
            logger.info("✅ Hoàn thành JIRA Report thành công!")
            
    except Exception as e:
        logger.error(f"💥 Lỗi hệ thống khi chạy JIRA: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Dừng bởi người dùng.")
    except Exception as e:
        logger.error(f"❌ Lỗi: {e}")
        sys.exit(1)
