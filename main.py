import os
import asyncio
from datetime import datetime
from telegram import Bot
from supabase import create_client

from src.config import Config
from src.orchestrator import Orchestrator, CategoryAgent
from src.services.finance.crypto_service import CryptoService
from src.services.finance.market_service import MarketService
from src.services.finance.banking_service import BankingService
from src.services.stock.stock_service import StockService
from src.services.social.news_service import NewsService
from src.services.weather.weather_service import WeatherService
from src.services.subscription_service import SubscriptionService

async def save_reminders(alerts):
    if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
        print("⚠️ Supabase config missing.")
        return

    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    for alert in alerts:
        try:
            # Parse time HH:MM
            deal_time = datetime.strptime(alert['time'], "%H:%M")
            now = datetime.now()
            # Remind 1 hour before
            remind_dt = now.replace(hour=deal_time.hour, minute=deal_time.minute, second=0, microsecond=0)
            
            # Simple logic: if event is passed for today, ignore (or could set for tomorrow)
            if remind_dt < now: 
                 print(f"⚠️ Event {alert['title']} has passed today.")
                 continue

            supabase.table("reminders").insert({
                "title": alert["title"],
                "remind_at": remind_dt.isoformat(),
                "status": "pending"
            }).execute()
            print(f"✅ Saved reminder: {alert['title']} at {alert['time']}")
        except Exception as e:
            print(f"❌ Failed to save reminder: {e}")

async def main():
    # 1. Setup Agents
    if not Config.TELEGRAM_BOT_TOKEN:
        print("❌ Missing TELEGRAM_BOT_TOKEN. Please check your .env file or GitHub Secrets!")
        return

    bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
    orchestrator = Orchestrator(bot)
    
    try:
        with open(Config.PROMPT_BASE, "r", encoding="utf-8") as f:
            base_prompt = f.read()
    except FileNotFoundError:
        print(f"❌ Base prompt not found at {Config.PROMPT_BASE}")
        return

    # Register Agents using Config
    agents_map = {
        "finance": "FINANCE",
        "weather": "WEATHER & TRAFFIC",
        "events": "EVENTS & SCHEDULE",
        "tech": "TECHNOLOGY & AI",
        "trends": "GOOGLE TRENDS & VIRAL",
        "news": "DAILY NEWS"
    }

    for name in agents_map.keys():
        api_key = Config.GEMINI_KEYS.get(name)
        if api_key:
            # Load specific prompt
            prompt_path = os.path.join(Config.PROMPTS_DIR, f"{name}.txt")
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    specific_prompt = f.read()
            except FileNotFoundError:
                print(f"⚠️ Specific prompt not found for {name}, using base only.")
                specific_prompt = ""
            
            full_prompt = f"{base_prompt}\n\n{specific_prompt}"
            orchestrator.add_agent(CategoryAgent(name, api_key, full_prompt))
        else:
            print(f"⚠️ No API key required/found for agent: {name}")

    # 2. Fetch Data
    print("⏳ Fetching real-time data...")
    
    # Weather
    weather_res = WeatherService.fetch_weather()
    weather_text = weather_res["text"] if isinstance(weather_res, dict) else weather_res
    weather_chart = weather_res.get("chart_path") if isinstance(weather_res, dict) else None
    
    # Market (CafeF)
    market_text = MarketService.fetch_market()
    
    # Banking (CafeF)
    banking_res = BankingService.fetch_banking_rates()
    banking_text = banking_res["text"]
    banking_chart = banking_res["chart_path"]
    
    # Stock (CafeF)
    stock_text = StockService.fetch_stock_analysis()
    
    # Crypto
    crypto_text = CryptoService.fetch_crypto()
    
    # News & Trends
    news_text = NewsService.fetch_news("general")
    tech_news = NewsService.fetch_news("tech")
    trends_res = NewsService.fetch_trends()
    trends_text = trends_res["text"]
    trends_chart = trends_res["chart_path"]

    data_map = {
        "finance": (
            f"--- [MARKET OVERVIEW] ---\n{market_text}\n"
            f"--- [STOCK WATCHLIST] ---\n{stock_text}\n"
            f"--- [BANKING] ---\n{banking_text}\n"
            f"--- [CRYPTO] ---\n{crypto_text}"
        ),
        "weather": weather_text,
        "weather_chart": weather_chart,
        "events": "Họp đối tác lúc 10:30, Deadline báo cáo quý lúc 17:00.", # Placeholder
        "tech": tech_news,
        "news": news_text,
        "trends": trends_text,
        "trends_chart": trends_chart,
        "rates_chart": banking_chart
    }

    # Fetch CRM Data if DB connected
    if Config.SUPABASE_URL and Config.SUPABASE_KEY and Config.TELEGRAM_CHAT_ID:
        try:
             supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
             
             # Subscription Data (Merge into Finance)
             sub_service = SubscriptionService(supabase)
             bills_data = sub_service.get_upcoming_bills(Config.TELEGRAM_CHAT_ID)
             if "finance" in data_map:
                 data_map["finance"] += f"\n\n--- [MICRO FINANCE DATA] ---\n{bills_data}"
             else:
                 data_map["finance"] = f"Dữ liệu vĩ mô: Không có.\n\n--- [MICRO FINANCE DATA] ---\n{bills_data}"

        except Exception as e:
             print(f"⚠️ Sub Data fetch failed: {e}")
    else:
        pass

    try:
        # Use simple default context or minimal info
        user_context = "User Context: General User interested in Finance, Tech, and Trends."

    except Exception:
        user_context = "User Context: General."

    # 3. Execute AI Pipeline
    print("🚀 AI Analysis in progress...")
    results = await orchestrator.run_all(user_context, data_map)
    
    # 4. Send Report
    if Config.TELEGRAM_CHAT_ID:
        # Start message (Separator)
        now_str = datetime.now().strftime('%d/%m/%Y %H:%M')
        header = (
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌅 *BẢN TIN CHIẾN LƯỢC MỚI*\n"
            f"📅 _Cập nhật lúc: {now_str}_\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        try:
            await bot.send_message(chat_id=Config.TELEGRAM_CHAT_ID, text=header, parse_mode='Markdown')
        except Exception as e:
            print(f"⚠️ Header Send Error: {e}")
            # Fallback plain text
            await bot.send_message(chat_id=Config.TELEGRAM_CHAT_ID, text=header.replace('*', '').replace('_', ''))

        # Map charts to categories
        chart_map = {
            "weather": data_map.get("weather_chart"),
            "trends": data_map.get("trends_chart"),
            "finance": data_map.get("rates_chart")
        }

        # 1. Accumulate Content
        full_report_parts = []
        charts_to_send = []

        for res in results:
            category = res["category"]
            content = res["content"]
            full_report_parts.append(content)
            
            # Check for chart
            c_path = chart_map.get(category)
            if c_path and os.path.exists(c_path) and os.path.getsize(c_path) > 0:
                charts_to_send.append((category, c_path))

        full_report = "\n\n".join(full_report_parts)

        # 2. Send Full Text Report (Chunked)
        try:
            if len(full_report) > 4000:
                # Split by newline to avoid breaking words if possible, or simple chunking
                # Simple chunking for safety:
                for chunk in [full_report[i:i+4000] for i in range(0, len(full_report), 4000)]:
                     await bot.send_message(chat_id=Config.TELEGRAM_CHAT_ID, text=chunk, parse_mode='Markdown')
            else:
                await bot.send_message(chat_id=Config.TELEGRAM_CHAT_ID, text=full_report, parse_mode='Markdown')
        except Exception as e_md:
            print(f"⚠️ Report Send Error (Markdown): {e_md} -> Fallback plain text")
            # Last resort fallback
            if len(full_report) > 4000:
                 for chunk in [full_report[i:i+4000] for i in range(0, len(full_report), 4000)]:
                     await bot.send_message(chat_id=Config.TELEGRAM_CHAT_ID, text=chunk)
            else:
                 await bot.send_message(chat_id=Config.TELEGRAM_CHAT_ID, text=full_report)

        # 3. Send Charts (After report)
        for cat, path in charts_to_send:
            try:
                caption = f"📊 Biểu đồ {cat.capitalize()}"
                with open(path, 'rb') as photo:
                    await bot.send_photo(chat_id=Config.TELEGRAM_CHAT_ID, photo=photo, caption=caption)
            except Exception as e:
                print(f"⚠️ Chart Send Error ({cat}): {e}")
    else:
        print("⚠️ No TELEGRAM_CHAT_ID, skipping send.")
    
    # 5. Process Alerts
    if orchestrator.alerts:
        print(f"🔔 Found {len(orchestrator.alerts)} alerts. Saving...")
        await save_reminders(orchestrator.alerts)
    
    print("✅ Done!")
    
    # 6. Cleanup Output Folder
    try:
        if os.path.exists("output"):
            import shutil
            shutil.rmtree("output")
            print("🧹 Cleaned up 'output' folder.")
    except Exception as e:
        print(f"⚠️ Cleanup Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
