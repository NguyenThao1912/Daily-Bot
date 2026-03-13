
import sys
import os

# Add src to path if needed (depending on how you run this)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

try:
    print("🔍 Testing JIRA Service imports...")
    from src.services.jira import run_daily_jira_report, JiraClient, JiraTicket, EpicSummary
    from src.services.jira.analyzer import run_jira_analysis
    from src.services.jira.notifier import TelegramNotifier, SlackNotifier
    from src.services.jira.excel_reporter import export_excel_report
    from src.services.jira.prompts import TICKET_LABELING_PROMPT, SPRINT_SUMMARY_PROMPT, SPRINT_HEALTH_PROMPT
    
    print("✅ All modules imported successfully!")
    
    # Simple check for constants
    if "Senior Scrum Master" in TICKET_LABELING_PROMPT:
        print("✅ Prompts loaded correctly.")
        
    print("🎉 Verification passed!")

except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ An error occurred: {e}")
    sys.exit(1)
