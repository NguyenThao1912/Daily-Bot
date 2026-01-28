import asyncio
from datetime import datetime
from telegram import Bot
from supabase import create_client

from src.config import Config
from src.orchestrator import Orchestrator, CategoryAgent
from src.services.data_service import DataService
from src.services.user_service import UserService
from src.services.crm_service import CRMService
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
    data_map = await DataService.get_all_data()

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
    report = await orchestrator.run_all(user_context, data_map)
    
    # 4. Send Report
    if Config.TELEGRAM_CHAT_ID:
        await bot.send_message(chat_id=Config.TELEGRAM_CHAT_ID, text=report, parse_mode='Markdown')
    else:
        print("⚠️ No TELEGRAM_CHAT_ID, skipping send.")
    
    # 5. Process Alerts
    if orchestrator.alerts:
        print(f"🔔 Found {len(orchestrator.alerts)} alerts. Saving...")
        await save_reminders(orchestrator.alerts)
    
    print("✅ Done!")

if __name__ == "__main__":
    asyncio.run(main())
