import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Core
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    WORKER_HOST = os.getenv("WORKER_HOST", "http://localhost:8787")

    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # External APIs
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    WEATHER_LOCATION = os.getenv("WEATHER_LOCATION", "Hanoi")
    STOCK_WATCHLIST = os.getenv("STOCK_WATCHLIST", "FPT.VN,HPG.VN,VHM.VN,VCB.VN,MBB.VN,ACB.VN,TCB.VN,VIC.VN,^VNINDEX").split(",")

    # Default Portfolio (Hardcoded for now as requested)
    # Format: {"Symbol": {"vol": float, "cost": float}}
    DEFAULT_PORTFOLIO = {
        "ACB": {"vol": 7200, "cost": 25}, # Example: 7200 shares @ 24.5   
    }
    # Agents Specific Keys (Defaults to Main Key)
    GEMINI_KEYS = {
        "finance": os.getenv("GEMINI_FINANCE_KEY", GEMINI_API_KEY),
        "weather": os.getenv("GEMINI_WEATHER_KEY", GEMINI_API_KEY),
        "events": os.getenv("GEMINI_EVENT_KEY", GEMINI_API_KEY),
        "news": os.getenv("GEMINI_NEWS_KEY", GEMINI_API_KEY),
        "tech": os.getenv("GEMINI_TECH_KEY", GEMINI_API_KEY),
        "trends": os.getenv("GEMINI_TRENDS_KEY", GEMINI_API_KEY),
        "calendar": os.getenv("GEMINI_CALENDAR_KEY", GEMINI_API_KEY),
    }

    # Paths
    PROMPT_BASE = os.path.join(os.path.dirname(__file__), "../prompts/base.txt")
    PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "../prompts/agents")
