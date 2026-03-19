import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    @staticmethod
    def _get_env(key, default=None):
        val = os.getenv(key)
        if val and val.strip():
            return val.strip()
        return default

    # Core
    TELEGRAM_BOT_TOKEN = _get_env.__func__("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = _get_env.__func__("TELEGRAM_CHAT_ID")
    GEMINI_API_KEY = _get_env.__func__("GEMINI_API_KEY")
    WORKER_HOST = _get_env.__func__("WORKER_HOST", "http://localhost:8787")

    # External APIs
    WEATHER_API_KEY = _get_env.__func__("WEATHER_API_KEY")
    WEATHER_LOCATION = _get_env.__func__("WEATHER_LOCATION", "Hanoi")
    STOCK_WATCHLIST = _get_env.__func__(
        "STOCK_WATCHLIST",
        "FPT.VN,HPG.VN,VHM.VN,VCB.VN,MBB.VN,ACB.VN,TCB.VN,VIC.VN,^VNINDEX",
    ).split(",")

    # Default Portfolio (Hardcoded for now as requested)
    # Format: {"Symbol": {"vol": float, "cost": float}}
    DEFAULT_PORTFOLIO = {
        
    }
    # Helper to handle empty strings as None
    @staticmethod
    def _get_key(key, default):
        val = os.getenv(key)
        if val and val.strip():
            return val.strip()
        return default

    # Agents Specific Keys (Defaults to Main Key)
    GEMINI_KEYS = {
        "finance": _get_key.__func__("GEMINI_FINANCE_KEY", GEMINI_API_KEY),
        "weather": _get_key.__func__("GEMINI_WEATHER_KEY", GEMINI_API_KEY),
        "news": _get_key.__func__("GEMINI_NEWS_KEY", GEMINI_API_KEY),
        "tech": _get_key.__func__("GEMINI_TECH_KEY", GEMINI_API_KEY),
        "trends": _get_key.__func__("GEMINI_TRENDS_KEY", GEMINI_API_KEY),
        "calendar": _get_key.__func__("GEMINI_CALENDAR_KEY", GEMINI_API_KEY),
    }

    # Paths
    PROMPT_BASE = os.path.join(os.path.dirname(__file__), "../prompts/base.txt")
    PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "../prompts/agents")
