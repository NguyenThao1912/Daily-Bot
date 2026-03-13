import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
    GEMINI_FINANCE_KEY = os.getenv("GEMINI_FINANCE_KEY")
