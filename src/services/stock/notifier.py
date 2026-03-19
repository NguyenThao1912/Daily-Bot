import os
import aiohttp
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.token   = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        
        if not self.token or not self.chat_id:
            raise ValueError("Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID trong .env")
        self.api = f"https://api.telegram.org/bot{self.token}"

    async def send_message(self, text: str):
        async with aiohttp.ClientSession() as s:
            resp = await s.post(f"{self.api}/sendMessage", json={
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            })
            body = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"Telegram sendMessage lỗi {resp.status}: {body}")

    async def send_document(self, file_path: str, caption: str = ""):
        async with aiohttp.ClientSession() as s:
            with open(file_path, "rb") as f:
                data = aiohttp.FormData()
                data.add_field("chat_id", self.chat_id)
                data.add_field("caption", caption)
                data.add_field("document", f, filename=os.path.basename(file_path))
                resp = await s.post(f"{self.api}/sendDocument", data=data)
                body = await resp.text()
                if resp.status != 200:
                    raise RuntimeError(f"Telegram sendDocument lỗi {resp.status}: {body}")
