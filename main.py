import os
import matplotlib
matplotlib.use('Agg') # Force non-interactive backend to prevent recursion/thread errors
import asyncio
import shutil
import pytz
from datetime import datetime
from typing import Any, Dict, Tuple
from telegram import Bot

# --- PROJECT IMPORTS ---
from src.constants import AGENT_LABELS
from src.config import Config
from src.orchestrator import Orchestrator, CategoryAgent
from src.services.finance.crypto_service import CryptoService
from src.services.finance.market_service import MarketService
from src.services.finance.banking_service import BankingService
from src.services.stock.stock_service import StockService
from src.services.social.news_service import NewsService
from src.services.weather.weather_service import WeatherService
from src.services.calendar.lunar_service import LunarService
from src.types import ReportContext, ServicePayload

# --- HELPER FUNCTIONS ---

def get_safe_data(service_res: Any) -> Tuple[str, Any]:
    """Safely extracts text and chart_path from service response to avoid crashes."""
    if isinstance(service_res, dict):
        return service_res.get("text", "Dữ liệu không khả dụng"), service_res.get("chart_path", None)
    return str(service_res), None


def load_base_prompt() -> str | None:
    try:
        with open(Config.PROMPT_BASE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Base prompt not found at {Config.PROMPT_BASE}")
        return None


def build_agent_prompt(base_prompt: str, agent_name: str) -> str:
    prompt_path = os.path.join(Config.PROMPTS_DIR, f"{agent_name}.txt")
    prompt_folder_path = os.path.join(Config.PROMPTS_DIR, agent_name, "prompt.txt")

    specific_prompt = ""
    if os.path.exists(prompt_path):
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                specific_prompt = f.read()
        except Exception as e:
            print(f"⚠️ Read error for {agent_name}.txt: {e}")
    elif os.path.exists(prompt_folder_path):
        try:
            with open(prompt_folder_path, "r", encoding="utf-8") as f:
                specific_prompt = f.read()
        except Exception as e:
            print(f"⚠️ Read error for {agent_name}/prompt.txt: {e}")
    else:
        print(f"⚠️ Specific prompt missing for {agent_name}, using base only.")

    return f"{base_prompt}\n\n{specific_prompt}"


def format_news_entries(entries: list[dict[str, str]], empty_message: str) -> str:
    if not entries:
        return empty_message
    return "\n".join(
        f"- [{entry.get('title', 'Untitled')}]({entry.get('link', '')})"
        for entry in entries
        if entry.get("title") and entry.get("link")
    ) or empty_message


def register_agents(orchestrator: Orchestrator, base_prompt: str) -> None:
    for name in AGENT_LABELS.keys():
        api_key = Config.GEMINI_KEYS.get(name)
        if api_key:
            full_prompt = build_agent_prompt(base_prompt, name)
            orchestrator.add_agent(CategoryAgent(name, api_key, full_prompt))
        else:
            print(f"⚠️ No API Key for agent: {name}")


def fetch_report_context() -> ReportContext:
    print("⏳ Fetching real-time data...")

    weather_text, weather_chart = get_safe_data(WeatherService.fetch_weather())
    market_text, market_charts = get_safe_data(MarketService.fetch_market())
    banking_text, banking_chart = get_safe_data(BankingService.fetch_banking_rates())
    stock_text, stock_charts = get_safe_data(StockService.fetch_stock_analysis())
    crypto_text = str(CryptoService.fetch_crypto())

    general_news_entries = NewsService.fetch_news_entries("general")
    featured_news_entries = NewsService.fetch_news_entries("featured")
    business_news_entries = NewsService.fetch_news_entries("business")
    tech_news_entries = NewsService.fetch_news_entries("tech")
    vn30_impact_entries = NewsService.fetch_vn30_impact_news()

    news_text = format_news_entries(general_news_entries, "Không lấy được tin tức.")
    featured_news = format_news_entries(featured_news_entries, "Không lấy được tin nổi bật.")
    business_news = format_news_entries(business_news_entries, "Không lấy được tin kinh doanh.")
    tech_news = format_news_entries(tech_news_entries, "Không lấy được tin công nghệ.")
    vn30_impact_news = format_news_entries(
        vn30_impact_entries,
        "Chưa ghi nhận tin rõ ràng có thể ảnh hưởng dài hạn đến VN30 từ feed hiện tại.",
    )
    trends_text, trends_chart = get_safe_data(NewsService.fetch_trends())

    calendar_text = str(LunarService.get_date_info())
    upcoming_holidays = LunarService.get_upcoming_holidays()

    data_map = {
        "finance": (
            f"--- [MARKET OVERVIEW] ---\n{market_text}\n"
            f"--- [VN30 STOCKS] ---\n{stock_text}\n"
            f"--- [VN30 IMPACT NEWS] ---\n{vn30_impact_news}\n"
            f"--- [BANKING] ---\n{banking_text}\n"
            f"--- [CRYPTO] ---\n{crypto_text}\n"
            f"--- [MACRO & POLITICS] ---\n{news_text}\n"
            f"--- [BUSINESS NEWS] ---\n{business_news}"
        ),
        "weather": weather_text,
        "events": "Họp đối tác lúc 10:30, Deadline báo cáo quý lúc 17:00.",
        "tech": tech_news,
        "news": f"{news_text}\n\n--- [TIN NỔI BẬT] ---\n{featured_news}",
        "trends": trends_text,
        "calendar": calendar_text,
        "weather_chart": weather_chart,
        "trends_chart": trends_chart,
        "finance_market_charts": market_charts,
        "finance_banking_chart": banking_chart,
        "finance_stock_charts": stock_charts
    }

    print_data_load_status(data_map, stock_text, stock_charts)
    return {"data_map": data_map, "upcoming_holidays": upcoming_holidays}


def print_data_load_status(data_map: Dict[str, Any], stock_text: str, stock_charts: Any) -> None:
    print("\n📊 --- DATA LOAD STATUS ---")
    for k, v in data_map.items():
        if isinstance(v, str):
            print(f"✅ Loaded [{k}]: {len(v)} chars")
        elif isinstance(v, list):
            print(f"✅ Loaded [{k}]: {len(v)} items")
        elif v:
            print(f"✅ Loaded [{k}]: available")
        else:
            print(f"⚠️ Loaded [{k}]: empty")

    stock_preview = stock_text[:220].replace("\n", " ")
    print(f"✅ Loaded [finance_stock_text]: {len(stock_text)} chars")
    print(f"🔎 [finance_stock_preview]: {stock_preview}...")
    if isinstance(stock_charts, list):
        print(f"✅ Loaded [finance_stock_charts]: {len(stock_charts)} items")
    elif stock_charts:
        print("✅ Loaded [finance_stock_charts]: available")
    else:
        print("⚠️ Loaded [finance_stock_charts]: empty")
    print("----------------------------------\n")


def build_user_context() -> str:
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    now_str_short = datetime.now(vn_tz).strftime('%d/%m/%Y')
    return f"User Context: General User interested in Finance, Tech, and Trends.\nTODAY'S DATE: {now_str_short}"


async def send_report(bot: Bot, results, data_map: Dict[str, Any], upcoming_holidays) -> None:
    if not Config.TELEGRAM_CHAT_ID:
        print("⚠️ No TELEGRAM_CHAT_ID found. Report generated but not sent.")
        return

    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    now_str = datetime.now(vn_tz).strftime('%d/%m/%Y %H:%M')
    header = (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌅 *BẢN TIN CHIẾN LƯỢC MỚI*\n"
        f"📅 _Cập nhật lúc: {now_str}_\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await bot.send_message(chat_id=Config.TELEGRAM_CHAT_ID, text=header, parse_mode='Markdown')

    finance_charts = []
    m_charts = data_map.get("finance_market_charts")
    if m_charts:
        if isinstance(m_charts, list):
            finance_charts.extend(m_charts)
        else:
            finance_charts.append(m_charts)

    b_chart = data_map.get("finance_banking_chart")
    if b_chart:
        finance_charts.append(b_chart)

    s_charts = data_map.get("finance_stock_charts")
    if s_charts:
        if isinstance(s_charts, list):
            finance_charts.extend(s_charts)
        else:
            finance_charts.append(s_charts)

    chart_source_map = {
        "weather": data_map["weather_chart"],
        "trends": data_map["trends_chart"],
        "finance": finance_charts
    }

    print("📄 Generating PDF Report...")
    from src.services.report.pdf_service import PDFService
    pdf_path = PDFService.generate_report(results, chart_source_map)

    if pdf_path and os.path.exists(pdf_path):
        await bot.send_document(
            chat_id=Config.TELEGRAM_CHAT_ID,
            document=open(pdf_path, 'rb'),
            caption=f"📄 Bản tin Chiến lược Ngày {now_str}",
            parse_mode='HTML'
        )
        print("✅ PDF Report sent successfully!")
        await send_event_notifications(bot, Config.TELEGRAM_CHAT_ID, upcoming_holidays)
    else:
        print("❌ Failed to generate PDF. Sending fallback text.")
        full_report = "\n\n".join([r["content"] for r in results])
        await send_smart_chunked_message(bot, Config.TELEGRAM_CHAT_ID, full_report, parse_mode='HTML')

async def send_smart_chunked_message(bot, chat_id, text, parse_mode='Markdown'):
    """Splits long messages and handles Markdown errors gracefully."""
    max_length = 4096
    
    # Split text into chunks
    chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]

    for chunk in chunks:
        try:
            # Try sending with formatted mode (Markdown/HTML)
            await bot.send_message(chat_id=chat_id, text=chunk, parse_mode=parse_mode)
        except Exception as e:
            print(f"⚠️ Formatting Error ({parse_mode}): {e}. Sending plain text fallback.")
            try:
                # Fallback: Send without formatting
                await bot.send_message(chat_id=chat_id, text=chunk)
            except Exception as e_plain:
                 print(f"❌ Failed to send message chunk: {e_plain}")

async def send_event_notifications(bot, chat_id, upcoming_holidays):
    """Send a prominent Telegram message with upcoming lunar holidays."""
    if not upcoming_holidays:
        return
    
    # Filter for holidays within the next 7 days
    near_holidays = [h for h in upcoming_holidays if h.get('days_until', 0) <= 7]
    
    if not near_holidays:
        return

    # Format holidays message
    event_msg = "🔔 *SỰ KIỆN SẮP TỚI:*\n\n"
    
    for holiday in near_holidays:
        name = holiday.get('name', '')
        days = holiday.get('days_until', 0)
        date = holiday.get('date', '')
        days_text = f"Còn {days} ngày" if days > 0 else "Hôm nay"
        event_msg += f"• *{name}* - {days_text} ({date})\n"
    
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=event_msg,
            parse_mode='Markdown'
        )
        print("✅ Lunar holiday notifications sent!")
    except Exception as e:
        print(f"⚠️ Failed to send holiday notifications: {e}")

# --- MAIN FLOW ---

async def main():
    if not Config.TELEGRAM_BOT_TOKEN:
        print("❌ Missing TELEGRAM_BOT_TOKEN. Check .env or Secrets.")
        return

    bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
    orchestrator = Orchestrator(bot)

    base_prompt = load_base_prompt()
    if not base_prompt:
        return

    register_agents(orchestrator, base_prompt)
    context = fetch_report_context()
    data_map = context["data_map"]
    upcoming_holidays = context["upcoming_holidays"]
    user_context = build_user_context()
    print("🚀 AI Analysis in progress...")
    
    try:
        results = await orchestrator.run_all(user_context, data_map)
    except Exception as e:
        print(f"❌ Orchestrator Error: {e}")
        return

    await send_report(bot, results, data_map, upcoming_holidays)

    print("✅ Process Completed!")

    # 7. Cleanup
    try:
        if os.path.exists("output"):
            shutil.rmtree("output")
            print("🧹 Cleaned up 'output' folder.")
    except Exception as e:
        print(f"⚠️ Cleanup Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        print("🛑 Force Exit.")
        import sys
        sys.exit(0)
