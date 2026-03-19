import logging
import os
from datetime import datetime
from typing import Dict, Any, List

from src.services.stock.stock_service import StockService
from src.services.stock.prompts import STOCK_MARKET_SUMMARY_PROMPT
from src.services.stock.notifier import TelegramNotifier
from src.services.stock.llm_utils import _default_llm_client

logger = logging.getLogger(__name__)

VN30_TICKERS = [
    "ACB", "SHB", "DGC", "BID", "CTG", "FPT", "GAS", "HPG", "MBB", "MSN", 
    "MWG", "SSI", "STB", "VCB", "VIC", "VNM", "SAB", "VIB", "VJC", "PLX", 
    "VPB", "LPB", "VRE", "HDB", "BCM", "VHM", "GVR", "TPB", "TCB", "SSB"
]

async def run_daily_stock_report(
    send_telegram: bool = True,
    llm_client=None
) -> Dict[str, Any]:
    """
    Pipeline chính cho VN30.
    """
    if llm_client is None:
        llm_client = _default_llm_client()

    service = StockService()
    logger.info("🚀 Bắt đầu Stock Daily Report (VN30 Focus)")
    
    # 1. Fetch data
    alert = await service.check_alerts()
    if alert:
        status = {"status": "alert", "message": alert}
    else:
        data_bytes = await service.download_eod_data()
        if not data_bytes or len(data_bytes) < 1024:
            status = {"status": "fail", "message": "Dữ liệu chưa có sẵn"}
        else:
            all_records = service.process_zip_data(data_bytes)
            vn30_records = [
                r for r in all_records 
                if r.get("Ticker", "").upper() in VN30_TICKERS
            ]
            status = {
                "status": "success",
                "message": "Dữ liệu VN30 đã sẵn sàng",
                "total_records": len(all_records),
                "vn30_count": len(vn30_records),
                "data": vn30_records
            }

    # 2. AI Summary
    ai_summary = ""
    if status["status"] == "success" and status.get("data"):
        try:
            market_text = "\n".join([str(r) for r in status["data"]])
            prompt = STOCK_MARKET_SUMMARY_PROMPT.format(market_data=market_text)
            
            logger.info("🤖 Đang tạo bản tin AI...")
            ai_summary = await llm_client(prompt)
            status["ai_summary"] = ai_summary
        except Exception as e:
            logger.error(f"❌ Lỗi AI summary: {e}")
            status["ai_error"] = str(e)

    # 3. Notification
    if send_telegram:
        try:
            notifier = TelegramNotifier()
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            if status["status"] == "alert":
                msg = f"📩 *THÔNG BÁO TỪ COPHIEU68.VN*\n\n🕐 {now}\n\n⚠️ {status['message']}"
            elif status["status"] == "success":
                msg = f"📊 *STOCK REPORT (VN30) — {now}*\n\n"
                if ai_summary:
                    msg += f"🤖 *NHẬN ĐỊNH AI:*\n{ai_summary}"
                else:
                    msg += f"✅ Đã cập nhật {status['vn30_count']} mã VN30"
            else:
                msg = f"❌ *STOCK DATA ERROR — {now}*\n\n⚠️ {status['message']}"
            
            await notifier.send_message(msg)
        except Exception as e:
            logger.error(f"❌ Lỗi gửi Telegram: {e}")

    return status
