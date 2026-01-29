import os
import matplotlib
matplotlib.use('Agg') # Force non-interactive backend to prevent recursion/thread errors
import asyncio
import shutil
import pytz
from datetime import datetime, timedelta
from telegram import Bot
from supabase import create_client

# --- PROJECT IMPORTS ---
from src.config import Config
from src.orchestrator import Orchestrator, CategoryAgent
from src.services.finance.crypto_service import CryptoService
from src.services.finance.market_service import MarketService
from src.services.finance.banking_service import BankingService
from src.services.stock.stock_service import StockService
from src.services.social.news_service import NewsService
from src.services.weather.weather_service import WeatherService
from src.services.subscription_service import SubscriptionService

# --- HELPER FUNCTIONS ---

def get_safe_data(service_res):
    """Safely extracts text and chart_path from service response to avoid crashes."""
    if isinstance(service_res, dict):
        return service_res.get("text", "Dữ liệu không khả dụng"), service_res.get("chart_path", None)
    return str(service_res), None

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

async def save_reminders(alerts):
    """Saves alerts to Supabase, correcting for Timezone and Reminder Logic."""
    if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
        print("⚠️ Supabase config missing. Skipping reminders.")
        return

    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    # DEFINING TIMEZONE (Vietnam)
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    now = datetime.now(vn_tz)
    
    for alert in alerts:
        try:
            # Parse time HH:MM (naive)
            deal_time = datetime.strptime(alert['time'], "%H:%M")
            
            # Create timezone-aware datetime for TODAY
            event_dt = now.replace(
                hour=deal_time.hour, 
                minute=deal_time.minute, 
                second=0, 
                microsecond=0
            )
            
            # Logic: Remind 1 hour before the event
            remind_dt = event_dt - timedelta(hours=1)
            
            # If the calculated reminder time has already passed today
            if remind_dt < now: 
                 print(f"⚠️ Reminder for {alert['title']} at {remind_dt.strftime('%H:%M')} has passed. Skipping.")
                 continue

            supabase.table("reminders").insert({
                "title": alert["title"],
                "remind_at": remind_dt.isoformat(), # ISO format with TZ info
                "status": "pending"
            }).execute()
            print(f"✅ Saved reminder: {alert['title']} for {remind_dt.strftime('%H:%M')}")

        except Exception as e:
            print(f"❌ Failed to save reminder '{alert.get('title', 'Unknown')}': {e}")

# --- MAIN FLOW ---

async def main():
    # 1. Setup & Checks
    if not Config.TELEGRAM_BOT_TOKEN:
        print("❌ Missing TELEGRAM_BOT_TOKEN. Check .env or Secrets.")
        return

    bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
    orchestrator = Orchestrator(bot)
    
    # Load Base Prompt
    try:
        with open(Config.PROMPT_BASE, "r", encoding="utf-8") as f:
            base_prompt = f.read()
    except FileNotFoundError:
        print(f"❌ Base prompt not found at {Config.PROMPT_BASE}")
        return

    # 2. Register Agents
    agents_map = {
        "weather": "WEATHER & TRAFFIC",
        "finance": "FINANCE",
        "news": "DAILY NEWS",
        "trends": "GOOGLE TRENDS & VIRAL",
        "tech": "TECHNOLOGY & AI"
    }

    for name in agents_map.keys():
        api_key = Config.GEMINI_KEYS.get(name)
        if api_key:
            prompt_path = os.path.join(Config.PROMPTS_DIR, f"{name}.txt")
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    specific_prompt = f.read()
            except FileNotFoundError:
                print(f"⚠️ Specific prompt missing for {name}, using base only.")
                specific_prompt = ""
            
            full_prompt = f"{base_prompt}\n\n{specific_prompt}"
            orchestrator.add_agent(CategoryAgent(name, api_key, full_prompt))
        else:
            print(f"⚠️ No API Key for agent: {name}")

    # 3. Fetch Data (Safe Mode)
    print("⏳ Fetching real-time data...")

    # Fetching with safe extraction
    # Fetching with safe extraction
    weather_text, weather_chart = get_safe_data(WeatherService.fetch_weather())
    
    # Market now returns Dict with chart_path as LIST
    market_text, market_charts = get_safe_data(MarketService.fetch_market())
    
    banking_text, banking_chart = get_safe_data(BankingService.fetch_banking_rates())
    stock_text = str(StockService.fetch_stock_analysis())
    crypto_text = str(CryptoService.fetch_crypto())
    
    # News & Trends
    news_text = NewsService.fetch_news("general")
    tech_news = NewsService.fetch_news("tech")
    trends_text, trends_chart = get_safe_data(NewsService.fetch_trends())

    # Compile Data Map
    data_map = {
        "finance": (
            f"--- [MARKET OVERVIEW] ---\n{market_text}\n"
            f"--- [STOCK WATCHLIST] ---\n{stock_text}\n"
            f"--- [BANKING] ---\n{banking_text}\n"
            f"--- [CRYPTO] ---\n{crypto_text}"
        ),
        "weather": weather_text,
        "events": "Họp đối tác lúc 10:30, Deadline báo cáo quý lúc 17:00.",
        "tech": tech_news,
        "news": news_text,
        "trends": trends_text,
        # Hidden fields for internal use/charts
        "weather_chart": weather_chart,
        "trends_chart": trends_chart,
        "finance_market_charts": market_charts,
        "finance_banking_chart": banking_chart
    }

    # Fetch Supabase CRM Data
    if Config.SUPABASE_URL and Config.SUPABASE_KEY and Config.TELEGRAM_CHAT_ID:
        try:
             supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
             sub_service = SubscriptionService(supabase)
             bills_data = sub_service.get_upcoming_bills(Config.TELEGRAM_CHAT_ID)
             
             # Append bills to finance section
             data_map["finance"] += f"\n\n--- [PERSONAL FINANCE] ---\n{bills_data}"
        except Exception as e:
             print(f"⚠️ CRM Data fetch failed: {e}")

    # 4. AI Analysis
    user_context = "User Context: General User interested in Finance, Tech, and Trends."
    print("🚀 AI Analysis in progress...")
    
    try:
        results = await orchestrator.run_all(user_context, data_map)
    except Exception as e:
        print(f"❌ Orchestrator Error: {e}")
        return

    # 5. Send Report
    if Config.TELEGRAM_CHAT_ID:
        # Header
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        now_str = datetime.now(vn_tz).strftime('%d/%m/%Y %H:%M')
        header = (
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌅 *BẢN TIN CHIẾN LƯỢC MỚI*\n"
            f"📅 _Cập nhật lúc: {now_str}_\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        await bot.send_message(chat_id=Config.TELEGRAM_CHAT_ID, text=header, parse_mode='Markdown')

        # Prepare Data for PDF
        # Aggregate Finance Charts
        finance_charts = []
        m_charts = data_map.get("finance_market_charts")
        if m_charts:
            if isinstance(m_charts, list): finance_charts.extend(m_charts)
            else: finance_charts.append(m_charts)
        
        b_chart = data_map.get("finance_banking_chart")
        if b_chart:
            finance_charts.append(b_chart)

        chart_source_map = {
            "weather": data_map["weather_chart"],
            "trends": data_map["trends_chart"],
            "finance": finance_charts
        }

        # Generate PDF
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
        else:
            print("❌ Failed to generate PDF. Sending fallback text.")
            # Fallback: Send raw text if PDF fails
            full_report = "\n\n".join([r["content"] for r in results])
            await send_smart_chunked_message(bot, Config.TELEGRAM_CHAT_ID, full_report, parse_mode='HTML')

    else:
        print("⚠️ No TELEGRAM_CHAT_ID found. Report generated but not sent.")

    # 6. Save Reminders (Alerts found by AI)
    if orchestrator.alerts:
        print(f"🔔 Found {len(orchestrator.alerts)} alerts. Saving...")
        await save_reminders(orchestrator.alerts)

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