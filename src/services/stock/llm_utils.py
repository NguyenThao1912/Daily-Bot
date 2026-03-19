import os
import aiohttp
import asyncio
import re
import itertools
import logging
from src.config import Config

logger = logging.getLogger(__name__)

def _default_llm_client():
    """
    LLM client mặc định sử dụng Gemini.
    Được tách từ dịch vụ JIRA cũ để đảm bảo tính độc lập.
    """
    # Lấy danh sách API keys từ Config hoặc Env
    key_candidates = [
        os.getenv("JIRA_GEMINI_API_KEY", ""),
        os.getenv("JIRA_GEMINI_API_KEY_2", ""),
        getattr(Config, "GEMINI_FINANCE_KEY", ""),
        os.getenv("GEMINI_API_KEY", ""),
    ]
    gemini_keys = list(dict.fromkeys(key for key in key_candidates if key))
    gemini_key_cycle = itertools.cycle(gemini_keys) if gemini_keys else None

    async def _parse_error_response(resp: aiohttp.ClientResponse) -> str:
        body = await resp.text()
        return f"HTTP {resp.status}: {body}"

    def _retry_delay_seconds(error_text: str) -> float:
        match = re.search(r"retry in ([0-9]+(?:\.[0-9]+)?)s", error_text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return 5.0

    async def call(prompt: str) -> str:
        gemini_model = os.getenv("JIRA_GEMINI_MODEL", "gemini-2.5-flash")

        if gemini_key_cycle:
            last_error = None
            for attempt in range(len(gemini_keys) * 2):
                gemini_api_key = next(gemini_key_cycle)
                timeout = aiohttp.ClientTimeout(total=45)
                async with aiohttp.ClientSession(timeout=timeout) as s:
                    resp = await s.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_api_key}",
                        json={"contents": [{"parts": [{"text": prompt}]}]},
                    )
                    if resp.status != 200:
                        error_text = await _parse_error_response(resp)
                        last_error = RuntimeError(f"Gemini lỗi: {error_text}")
                        if resp.status == 429 and attempt < (len(gemini_keys) * 2) - 1:
                            await asyncio.sleep(_retry_delay_seconds(error_text))
                            continue
                        raise last_error
                    data = await resp.json()
                    candidates = data.get("candidates") or []
                    if not candidates:
                        raise RuntimeError(f"Gemini trả response không hợp lệ: {data}")
                    return data["candidates"][0]["content"]["parts"][0]["text"]

            if last_error is not None:
                raise last_error

        raise ValueError(
            "Cần cấu hình ít nhất một GEMINI_API_KEY trong .env"
        )

    return call
