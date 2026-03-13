import asyncio
from datetime import datetime, timezone
from telegram import Bot
from supabase import create_client, Client
from src.core.config import Config

async def run_worker():
    if not all([Config.SUPABASE_URL, Config.SUPABASE_KEY, Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHAT_ID]):
        print("❌ Thiếu cấu hình môi trường (Supabase hoặc Telegram).")
        return

    supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)

    # 1. Query pending reminders that should be sent now
    now = datetime.now(timezone.utc).isoformat()
    
    try:
        response = supabase.table("reminders")\
            .select("*")\
            .eq("status", "pending")\
            .lte("remind_at", now)\
            .execute()

        pending_reminders = response.data
    except Exception as e:
        print(f"❌ Lỗi truy vấn Supabase: {str(e)}")
        return

    if not pending_reminders:
        print(f"[{datetime.now()}] Không có lời nhắc nào cần gửi.")
        return

    print(f"🔔 Đang xử lý {len(pending_reminders)} lời nhắc...")

    for reminder in pending_reminders:
        try:
            # 2. Send Telegram message
            message = f"⏰ *NHẮC HẸN SĂN DEAL (Còn 1 tiếng)*\n\n"
            message += f"🔥 *Nội dung:* {reminder['title']}\n"
            message += f"👉 Kiểm tra ngay Shopee/Uniqlo/ShopeeFood để không bỏ lỡ!"
            
            await bot.send_message(chat_id=Config.TELEGRAM_CHAT_ID, text=message, parse_mode='Markdown')

            # 3. Update status to 'sent'
            supabase.table("reminders")\
                .update({"status": "sent"})\
                .eq("id", reminder["id"])\
                .execute()
            
            print(f"✅ Đã gửi: {reminder['title']}")
        except Exception as e:
            print(f"❌ Lỗi khi gửi lời nhắc {reminder['id']}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_worker())
