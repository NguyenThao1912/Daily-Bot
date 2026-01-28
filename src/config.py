import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Core
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # External APIs
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    WEATHER_LOCATION = os.getenv("WEATHER_LOCATION", "Hanoi")

    # Agents Specific Keys (Defaults to Main Key)
    GEMINI_KEYS = {
        "finance": os.getenv("GEMINI_FINANCE_KEY", GEMINI_API_KEY),
        "weather": os.getenv("GEMINI_WEATHER_KEY", GEMINI_API_KEY),
        "events": os.getenv("GEMINI_EVENT_KEY", GEMINI_API_KEY),
        "crypto": os.getenv("GEMINI_CRYPTO_KEY", GEMINI_API_KEY),
        "news": os.getenv("GEMINI_NEWS_KEY", GEMINI_API_KEY),
        "tech": os.getenv("GEMINI_TECH_KEY", GEMINI_API_KEY),
        "trends": os.getenv("GEMINI_TRENDS_KEY", GEMINI_API_KEY),
    }

    # Paths
    PROMPT_BASE = os.path.join(os.path.dirname(__file__), "../prompts/base.txt")
    PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "../prompts/agents")
    PROMPT_USER = os.path.join(os.path.dirname(__file__), "../prompts/user_context.txt")
