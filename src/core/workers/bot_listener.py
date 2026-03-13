from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from src.core.config import Config
from src.services.weather.weather_service import WeatherService
from src.services.finance.crypto_service import CryptoService

# --- Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /start"""
    await update.message.reply_text(
        "👋 Chào Sếp! Tôi là Morning Strategist Bot.\n\n"
        "Các lệnh hỗ trợ:\n"
        "/weather - Xem thời tiết hiện tại\n"
        "/crypto - Check nhanh giá BTC/ETH\n"
        "/help - Xem hướng dẫn này"
    )

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /weather -> Gọi DataService lấy thời tiết ngay lập tức"""
    msg = await update.message.reply_text("⏳ Đang check thời tiết...")
    w_info = WeatherService.fetch_weather()
    if isinstance(w_info, dict):
        w_text = w_info.get("text", "Lỗi lấy thời tiết")
    else:
        w_text = str(w_info)
    # Edit message để cập nhật kết quả
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id, text=w_text)

async def crypto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /crypto"""
    msg = await update.message.reply_text("⏳ Đang check giá Coin...")
    c_info = CryptoService.fetch_crypto()
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=msg.message_id, text=c_info)

# --- Main Listener ---

if __name__ == '__main__':
    if not Config.TELEGRAM_BOT_TOKEN:
        print("❌ Thiếu TELEGRAM_BOT_TOKEN")
        exit(1)

    print("🤖 Bot đang khởi động...")
    app = ApplicationBuilder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # Đăng ký lệnh
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', start_command))
    app.add_handler(CommandHandler('weather', weather_command))
    app.add_handler(CommandHandler('crypto', crypto_command))

    print("✅ Bot đang lắng nghe lệnh... (Polling Mode)")
    app.run_polling()
