import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = Path(__file__).resolve().parents[2]

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

    # JIRA
    JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
    JIRA_EMAIL = os.getenv("JIRA_EMAIL")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
    JIRA_DEFAULT_PROJECT = os.getenv("JIRA_DEFAULT_PROJECT", "PROJ")
    JIRA_TELEGRAM_CHAT_ID = os.getenv("JIRA_TELEGRAM_CHAT_ID")
    JIRA_GEMINI_API_KEY = os.getenv("JIRA_GEMINI_API_KEY")
    JIRA_GEMINI_API_KEY_2 = os.getenv("JIRA_GEMINI_API_KEY_2")
    JIRA_GEMINI_MODEL = os.getenv("JIRA_GEMINI_MODEL", "gemini-2.5-flash")
    JIRA_FOCUS_EPIC_KEYS = [
        key.strip()
        for key in os.getenv("JIRA_FOCUS_EPIC_KEYS", "").split(",")
        if key.strip()
    ]

    # Default Portfolio (Hardcoded for now as requested)
    # Format: {"Symbol": {"vol": float, "cost": float}}
    DEFAULT_PORTFOLIO = {
        
    }
    # Helper to handle empty strings as None
    @staticmethod
    def _get_key(key, default):
        val = os.getenv(key)
        if val and val.strip(): return val
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
    PROMPT_BASE = str(BASE_DIR / "prompts" / "base.txt")
    PROMPTS_DIR = str(BASE_DIR / "prompts" / "agents")
