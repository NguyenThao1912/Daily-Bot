import asyncio
import itertools
import logging
import os
import re
from datetime import datetime
from typing import Optional, Any, Dict

from src.core.config import Config
from src.services.jira.analyzer import run_jira_analysis
from src.services.jira.excel_reporter import export_excel_report
from src.services.jira.notifier import TelegramNotifier, SlackNotifier

logger = logging.getLogger(__name__)

async def run_daily_jira_report(
    project_key: str,
    llm_client=None,
    send_telegram: bool = True,
    send_slack: bool = False,
    export_excel: bool = True,
) -> Dict[str, Any]:
    """
    Pipeline đầy đủ:
    1. Fetch tickets từ Jira Cloud
    2. AI đánh nhãn từng ticket (Scrum Master mode)
    3. Build báo cáo thống kê theo Epic
    4. Export Excel
    5. Gửi Telegram / Slack
    """
    if llm_client is None:
        llm_client = _default_llm_client()

    # ── 1. Phân tích ──
    logger.info(f"🚀 Bắt đầu Jira Daily Report cho project: {project_key}")
    tickets, report = await run_jira_analysis(project_key, llm_client)

    # ── 2. Export Excel ──
    excel_path = None
    if export_excel:
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        excel_path = f"output/jira_{project_key}_{ts}.xlsx"
        export_excel_report(tickets, report, excel_path)
        logger.info(f"📊 Excel saved: {excel_path}")

    # ── 3. Gửi notifications ──
    errors = []

    if send_telegram and os.getenv("TELEGRAM_BOT_TOKEN"):
        try:
            notifier = TelegramNotifier()
            await notifier.send_report(report, excel_path)
        except Exception as e:
            errors.append(f"Telegram: {e}")
            logger.error(f"❌ Telegram error: {e}")

    if send_slack and os.getenv("SLACK_WEBHOOK_URL"):
        try:
            notifier = SlackNotifier()
            await notifier.send_report(report, excel_path)
        except Exception as e:
            errors.append(f"Slack: {e}")
            logger.error(f"❌ Slack error: {e}")

    return {"report": report, "excel_path": excel_path, "errors": errors}

def _default_llm_client():
    """
    LLM client mặc định — gọi Gemini tùy theo env.
    """
    import aiohttp

    key_candidates = [
        Config.JIRA_GEMINI_API_KEY or "",
        Config.JIRA_GEMINI_API_KEY_2 or "",
        Config.GEMINI_KEYS.get("finance") or "",
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
        gemini_model = Config.JIRA_GEMINI_MODEL

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
            "Cần JIRA_GEMINI_API_KEY hoặc JIRA_GEMINI_API_KEY_2 hoặc GEMINI_FINANCE_KEY hoặc GEMINI_API_KEY trong .env"
        )

    return call
