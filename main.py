import asyncio
import os
import shutil
from datetime import datetime, timedelta
from typing import Any, Callable

import matplotlib
import pytz
from supabase import create_client
from telegram import Bot

from src.core.config import Config
from src.core.orchestrator import CategoryAgent, Orchestrator
from src.services.calendar import LunarService
from src.services.finance.banking_service import BankingService
from src.services.finance.crypto_service import CryptoService
from src.services.finance.market_service import MarketService
from src.services.social import NewsService
from src.services.stock.stock_service import StockService
from src.services.subscription import SubscriptionService
from src.services.weather import WeatherService

os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.getcwd(), ".matplotlib"))
matplotlib.use("Agg")

FetchFn = Callable[[], Any]
VIETNAM_TZ = pytz.timezone("Asia/Ho_Chi_Minh")
AGENT_NAMES = ("weather", "calendar", "finance", "news", "trends", "tech")


def get_safe_data(service_res: Any) -> tuple[str, Any]:
    """Safely extracts text and chart_path from service response to avoid crashes."""
    if isinstance(service_res, dict):
        return service_res.get("text", "Dữ liệu không khả dụng"), service_res.get("chart_path")
    return str(service_res), None


def load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def load_agent_prompt(agent_name: str, base_prompt: str) -> str:
    prompt_candidates = (
        os.path.join(Config.PROMPTS_DIR, f"{agent_name}.txt"),
        os.path.join(Config.PROMPTS_DIR, agent_name, "prompt.txt"),
    )

    specific_prompt = ""
    for prompt_path in prompt_candidates:
        if not os.path.exists(prompt_path):
            continue
        try:
            specific_prompt = load_prompt(prompt_path)
            break
        except Exception as exc:
            print(f"⚠️ Read error for {agent_name} prompt ({prompt_path}): {exc}")
    else:
        print(f"⚠️ Specific prompt missing for {agent_name}, using base only.")

    return f"{base_prompt}\n\n{specific_prompt}" if specific_prompt else base_prompt


def register_agents(orchestrator: Orchestrator, base_prompt: str) -> None:
    for agent_name in AGENT_NAMES:
        api_key = Config.GEMINI_KEYS.get(agent_name)
        if not api_key:
            print(f"⚠️ No API Key for agent: {agent_name}")
            continue
        orchestrator.add_agent(
            CategoryAgent(agent_name, api_key, load_agent_prompt(agent_name, base_prompt))
        )


async def run_blocking_fetch(label: str, fetch_fn: FetchFn) -> Any:
    try:
        return await asyncio.to_thread(fetch_fn)
    except Exception as exc:
        print(f"⚠️ Fetch failed for {label}: {exc}")
        return None


async def fetch_runtime_data() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    print("⏳ Fetching real-time data...")

    fetch_jobs: dict[str, FetchFn] = {
        "weather": WeatherService.fetch_weather,
        "market": MarketService.fetch_market,
        "banking": BankingService.fetch_banking_rates,
        "stock": StockService.fetch_stock_analysis,
        "crypto": CryptoService.fetch_crypto,
        "news_general": lambda: NewsService.fetch_news("general"),
        "news_featured": lambda: NewsService.fetch_news("featured"),
        "news_business": lambda: NewsService.fetch_news("business"),
        "news_tech": lambda: NewsService.fetch_news("tech"),
        "trends": NewsService.fetch_trends,
        "calendar_info": LunarService.get_date_info,
        "upcoming_holidays": LunarService.get_upcoming_holidays,
    }

    results = await asyncio.gather(
        *(run_blocking_fetch(label, fetch_fn) for label, fetch_fn in fetch_jobs.items())
    )
    fetched = dict(zip(fetch_jobs.keys(), results, strict=True))

    weather_text, weather_chart = get_safe_data(fetched["weather"])
    market_text, market_charts = get_safe_data(fetched["market"])
    banking_text, banking_chart = get_safe_data(fetched["banking"])
    stock_text, stock_charts = get_safe_data(fetched["stock"])
    trends_text, trends_chart = get_safe_data(fetched["trends"])

    data_map = {
        "finance": (
            f"--- [MARKET OVERVIEW] ---\n{market_text}\n"
            f"--- [STOCK WATCHLIST] ---\n{stock_text}\n"
            f"--- [BANKING] ---\n{banking_text}\n"
            f"--- [CRYPTO] ---\n{fetched['crypto']}\n"
            f"--- [MACRO & POLITICS] ---\n{fetched['news_general']}\n"
            f"--- [BUSINESS NEWS] ---\n{fetched['news_business']}"
        ),
        "weather": weather_text,
        "events": "Họp đối tác lúc 10:30, Deadline báo cáo quý lúc 17:00.",
        "tech": str(fetched["news_tech"]),
        "news": f"{fetched['news_general']}\n\n--- [TIN NỔI BẬT] ---\n{fetched['news_featured']}",
        "trends": trends_text,
        "calendar": str(fetched["calendar_info"]),
        "weather_chart": weather_chart,
        "trends_chart": trends_chart,
        "finance_market_charts": market_charts,
        "finance_banking_chart": banking_chart,
        "finance_stock_charts": stock_charts,
    }

    upcoming_holidays = fetched["upcoming_holidays"]
    if not isinstance(upcoming_holidays, list):
        upcoming_holidays = []

    print("\n📊 --- DATA LOAD STATUS ---")
    for key, value in data_map.items():
        if isinstance(value, str):
            print(f"✅ Loaded [{key}]: {len(value)} chars")
        elif isinstance(value, list):
            print(f"✅ Loaded [{key}]: {len(value)} items")
    print("----------------------------------\n")

    return data_map, upcoming_holidays


async def enrich_finance_data(data_map: dict[str, Any]) -> None:
    if not (Config.SUPABASE_URL and Config.SUPABASE_KEY and Config.TELEGRAM_CHAT_ID):
        return

    try:
        supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        sub_service = SubscriptionService(supabase)
        bills_data = await asyncio.to_thread(
            sub_service.get_upcoming_bills,
            Config.TELEGRAM_CHAT_ID,
        )
        data_map["finance"] += f"\n\n--- [PERSONAL FINANCE] ---\n{bills_data}"
    except Exception as exc:
        print(f"⚠️ CRM Data fetch failed: {exc}")


def collect_finance_charts(data_map: dict[str, Any]) -> list[str]:
    finance_charts: list[str] = []
    for value in (
        data_map.get("finance_market_charts"),
        data_map.get("finance_banking_chart"),
        data_map.get("finance_stock_charts"),
    ):
        if not value:
            continue
        if isinstance(value, list):
            finance_charts.extend(value)
        else:
            finance_charts.append(value)
    return finance_charts


async def send_smart_chunked_message(
    bot: Bot,
    chat_id: str,
    text: str,
    parse_mode: str = "Markdown",
) -> None:
    """Splits long messages and handles Markdown errors gracefully."""
    max_length = 4096
    chunks = [text[i : i + max_length] for i in range(0, len(text), max_length)]

    for chunk in chunks:
        try:
            await bot.send_message(chat_id=chat_id, text=chunk, parse_mode=parse_mode)
        except Exception as exc:
            print(f"⚠️ Formatting Error ({parse_mode}): {exc}. Sending plain text fallback.")
            try:
                await bot.send_message(chat_id=chat_id, text=chunk)
            except Exception as plain_exc:
                print(f"❌ Failed to send message chunk: {plain_exc}")


async def send_event_notifications(
    bot: Bot,
    chat_id: str,
    upcoming_holidays: list[dict[str, Any]],
) -> None:
    """Send a prominent Telegram message with upcoming lunar holidays."""
    if not upcoming_holidays:
        return

    near_holidays = [holiday for holiday in upcoming_holidays if holiday.get("days_until", 0) <= 7]
    if not near_holidays:
        return

    event_msg = "🔔 *SỰ KIỆN SẮP TỚI:*\n\n"
    for holiday in near_holidays:
        name = holiday.get("name", "")
        days = holiday.get("days_until", 0)
        date = holiday.get("date", "")
        days_text = f"Còn {days} ngày" if days > 0 else "Hôm nay"
        event_msg += f"• *{name}* - {days_text} ({date})\n"

    try:
        await bot.send_message(chat_id=chat_id, text=event_msg, parse_mode="Markdown")
        print("✅ Lunar holiday notifications sent!")
    except Exception as exc:
        print(f"⚠️ Failed to send holiday notifications: {exc}")


async def save_reminders(alerts: list[dict[str, str]]) -> None:
    """Saves alerts to Supabase, correcting for Timezone and Reminder Logic."""
    if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
        print("⚠️ Supabase config missing. Skipping reminders.")
        return

    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    now = datetime.now(VIETNAM_TZ)

    for alert in alerts:
        try:
            deal_time = datetime.strptime(alert["time"], "%H:%M")
            event_dt = now.replace(
                hour=deal_time.hour,
                minute=deal_time.minute,
                second=0,
                microsecond=0,
            )
            remind_dt = event_dt - timedelta(hours=1)

            if remind_dt < now:
                print(
                    f"⚠️ Reminder for {alert['title']} at {remind_dt.strftime('%H:%M')} has passed. Skipping."
                )
                continue

            await asyncio.to_thread(
                lambda: supabase.table("reminders")
                .insert(
                    {
                        "title": alert["title"],
                        "remind_at": remind_dt.isoformat(),
                        "status": "pending",
                    }
                )
                .execute()
            )
            print(f"✅ Saved reminder: {alert['title']} for {remind_dt.strftime('%H:%M')}")
        except Exception as exc:
            print(f"❌ Failed to save reminder '{alert.get('title', 'Unknown')}': {exc}")


async def send_report(
    bot: Bot,
    results: list[dict[str, str]],
    data_map: dict[str, Any],
    upcoming_holidays: list[dict[str, Any]],
) -> None:
    if not Config.TELEGRAM_CHAT_ID:
        print("⚠️ No TELEGRAM_CHAT_ID found. Report generated but not sent.")
        return

    now_str = datetime.now(VIETNAM_TZ).strftime("%d/%m/%Y %H:%M")
    header = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌅 *BẢN TIN CHIẾN LƯỢC MỚI*\n"
        f"📅 _Cập nhật lúc: {now_str}_\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await bot.send_message(chat_id=Config.TELEGRAM_CHAT_ID, text=header, parse_mode="Markdown")

    chart_source_map = {
        "weather": data_map["weather_chart"],
        "trends": data_map["trends_chart"],
        "finance": collect_finance_charts(data_map),
    }

    print("📄 Generating PDF Report...")
    from src.services.report.pdf_service import PDFService

    pdf_path = await asyncio.to_thread(PDFService.generate_report, results, chart_source_map)
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as document:
            await bot.send_document(
                chat_id=Config.TELEGRAM_CHAT_ID,
                document=document,
                caption=f"📄 Bản tin Chiến lược Ngày {now_str}",
                parse_mode="HTML",
            )
        print("✅ PDF Report sent successfully!")
        await send_event_notifications(bot, Config.TELEGRAM_CHAT_ID, upcoming_holidays)
        return

    print("❌ Failed to generate PDF. Sending fallback text.")
    full_report = "\n\n".join(result["content"] for result in results)
    await send_smart_chunked_message(bot, Config.TELEGRAM_CHAT_ID, full_report, parse_mode="HTML")


def cleanup_output() -> None:
    try:
        if os.path.exists("output"):
            shutil.rmtree("output")
            print("🧹 Cleaned up 'output' folder.")
    except Exception as exc:
        print(f"⚠️ Cleanup Error: {exc}")


async def main() -> None:
    if not Config.TELEGRAM_BOT_TOKEN:
        print("❌ Missing TELEGRAM_BOT_TOKEN. Check .env or Secrets.")
        return

    bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
    orchestrator = Orchestrator(bot)

    try:
        base_prompt = load_prompt(Config.PROMPT_BASE)
    except FileNotFoundError:
        print(f"❌ Base prompt not found at {Config.PROMPT_BASE}")
        return

    register_agents(orchestrator, base_prompt)

    data_map, upcoming_holidays = await fetch_runtime_data()
    await enrich_finance_data(data_map)

    now_str_short = datetime.now(VIETNAM_TZ).strftime("%d/%m/%Y")
    user_context = (
        "User Context: General User interested in Finance, Tech, and Trends.\n"
        f"TODAY'S DATE: {now_str_short}"
    )
    print("🚀 AI Analysis in progress...")

    try:
        results = await orchestrator.run_all(user_context, data_map)
    except Exception as exc:
        print(f"❌ Orchestrator Error: {exc}")
        return

    await send_report(bot, results, data_map, upcoming_holidays)

    if orchestrator.alerts:
        print(f"🔔 Found {len(orchestrator.alerts)} alerts. Saving...")
        await save_reminders(orchestrator.alerts)

    print("✅ Process Completed!")
    cleanup_output()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        print("🛑 Force Exit.")
