import os
import aiohttp
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def _progress_bar(pct: float, length: int = 8) -> str:
    filled = round(pct / 100 * length)
    return "█" * filled + "░" * (length - filled)

def format_telegram_message(report: Dict[str, Any]) -> str:
    """Tạo message Telegram với Markdown v2"""
    p = report
    alerts = p.get("scrum_alerts", {})
    lbl = p.get("label_summary", {})
    now = p.get("generated_at", datetime.now().strftime("%Y-%m-%d %H:%M"))

    total = p["total_tickets"] or 1
    bug_pct = round(lbl.get("bug", 0) / total * 100)

    lines = [
        f"📊 *JIRA DAILY REPORT — {p['project']}*",
        f"🕐 {now}\n",
        f"📦 *Tổng quan:*",
        f"  • Tổng tickets: `{p['total_tickets']}`",
        f"  • Số Epics: `{p['epics_count']}`\n",
        f"🏷 *Phân loại AI:*",
        f"  🐛 Bug: `{lbl.get('bug', 0)}` ({bug_pct}%)",
        f"  📋 Request Feature: `{lbl.get('request_feature', 0)}`",
        f"  ✨ New Feature: `{lbl.get('new_feature', 0)}`",
        f"  🔄 In Progress: `{lbl.get('in_progress', 0)}`",
        f"  ❓ Chưa phân loại: `{lbl.get('Chưa phân loại', 0)}`\n",
    ]

    epics = p.get("epics", {})
    if epics:
        lines.append("📌 *Tiến độ Epic:*")
        for ek, edata in list(epics.items())[:5]:
            bar = _progress_bar(edata["completion_rate"])
            lines.append(f"  `{ek}` {edata['name'][:25]}")
            lines.append(f"    {bar} {edata['completion_rate']}% ({edata['total']} tickets)")
        lines.append("")

    has_alert = any([
        alerts.get("overdue_count", 0),
        alerts.get("blocked_count", 0),
        alerts.get("no_assignee_count", 0),
    ])
    if has_alert:
        lines.append("🚨 *Cảnh báo Scrum Master:*")
        if alerts.get("overdue_count"):
            keys = ", ".join(f"`{k}`" for k in alerts.get("overdue_keys", [])[:5])
            lines.append(f"  ⏰ Overdue: {alerts['overdue_count']} tickets → {keys}")
        if alerts.get("blocked_count"):
            keys = ", ".join(f"`{k}`" for k in alerts.get("blocked_keys", [])[:5])
            lines.append(f"  🔴 Blocked: {alerts['blocked_count']} tickets → {keys}")
        if alerts.get("no_assignee_count"):
            lines.append(f"  👤 Chưa assign: {alerts['no_assignee_count']} tickets")
        lines.append("")

    lines.append("📎 _Xem báo cáo chi tiết trong file Excel đính kèm_")
    return "\n".join(lines)

def format_slack_blocks(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Tạo Slack Block Kit message"""
    p = report
    alerts = p.get("scrum_alerts", {})
    lbl = p.get("label_summary", {})
    total = p["total_tickets"] or 1

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"📊 Jira Report — {p['project']}", "emoji": True}
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"🕐 {p.get('generated_at')}  |  {p['total_tickets']} tickets  |  {p['epics_count']} epics"}]
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*🐛 Bug*\n{lbl.get('bug', 0)} ({round(lbl.get('bug',0)/total*100)}%)"},
                {"type": "mrkdwn", "text": f"*📋 Request Feature*\n{lbl.get('request_feature', 0)}"},
                {"type": "mrkdwn", "text": f"*✨ New Feature*\n{lbl.get('new_feature', 0)}"},
                {"type": "mrkdwn", "text": f"*🔄 In Progress*\n{lbl.get('in_progress', 0)}"},
            ]
        },
        {"type": "divider"},
    ]

    epics = p.get("epics", {})
    if epics:
        epic_text = "*📌 Tiến độ Epic:*\n"
        for ek, edata in list(epics.items())[:5]:
            bar = _progress_bar(edata["completion_rate"])
            epic_text += f"`{ek}` {edata['name'][:25]}  {bar} *{edata['completion_rate']}%*\n"
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": epic_text}})

    has_alert = alerts.get("overdue_count") or alerts.get("blocked_count") or alerts.get("no_assignee_count")
    if has_alert:
        alert_parts = []
        if alerts.get("overdue_count"):
            alert_parts.append(f"⏰ *Overdue:* {alerts['overdue_count']} tickets")
        if alerts.get("blocked_count"):
            alert_parts.append(f"🔴 *Blocked:* {alerts['blocked_count']} tickets")
        if alerts.get("no_assignee_count"):
            alert_parts.append(f"👤 *Chưa assign:* {alerts['no_assignee_count']} tickets")

        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "🚨 *Scrum Alerts:*\n" + "\n".join(alert_parts)}
        })

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": "📎 File Excel đính kèm bên dưới"}]
    })
    return blocks

class TelegramNotifier:
    def __init__(self):
        self.token   = os.getenv("TELEGRAM_BOT_TOKEN", "")
        # Prioritize JIRA_TELEGRAM_CHAT_ID, fallback to TELEGRAM_CHAT_ID
        self.chat_id = os.getenv("JIRA_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID", "")
        
        if not self.token or not self.chat_id:
            raise ValueError("Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID/JIRA_TELEGRAM_CHAT_ID")
        self.api = f"https://api.telegram.org/bot{self.token}"

    async def send_message(self, text: str):
        async with aiohttp.ClientSession() as s:
            resp = await s.post(f"{self.api}/sendMessage", json={
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            })
            body = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"Telegram sendMessage lỗi {resp.status}: {body}")

    async def send_document(self, file_path: str, caption: str = ""):
        async with aiohttp.ClientSession() as s:
            with open(file_path, "rb") as f:
                data = aiohttp.FormData()
                data.add_field("chat_id", self.chat_id)
                data.add_field("caption", caption)
                data.add_field("document", f, filename=os.path.basename(file_path),
                               content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                resp = await s.post(f"{self.api}/sendDocument", data=data)
                body = await resp.text()
                if resp.status != 200:
                    raise RuntimeError(f"Telegram sendDocument lỗi {resp.status}: {body}")

    async def send_report(self, report: Dict[str, Any], excel_path: Optional[str] = None):
        msg = format_telegram_message(report)
        await self.send_message(msg)
        if excel_path and os.path.exists(excel_path):
            await self.send_document(excel_path, caption=f"📊 Chi tiết — {report['project']}")
        logger.info("✅ Đã gửi báo cáo qua Telegram")

class SlackNotifier:
    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        self.token       = os.getenv("SLACK_BOT_TOKEN", "")
        self.channel     = os.getenv("SLACK_CHANNEL", "#daily-bot")

    async def send_blocks(self, blocks: List[Dict[str, Any]], text: str = "Jira Report"):
        if not self.webhook_url:
            raise ValueError("Thiếu SLACK_WEBHOOK_URL")
        async with aiohttp.ClientSession() as s:
            resp = await s.post(self.webhook_url, json={"text": text, "blocks": blocks})
            body = await resp.text()
            if resp.status >= 400:
                raise RuntimeError(f"Slack webhook lỗi {resp.status}: {body}")

    async def send_file(self, file_path: str, title: str = "Jira Excel Report"):
        if not self.token:
            logger.warning("Không có SLACK_BOT_TOKEN, bỏ qua upload file")
            return
        async with aiohttp.ClientSession() as s:
            with open(file_path, "rb") as f:
                data = aiohttp.FormData()
                data.add_field("token", self.token)
                data.add_field("channels", self.channel)
                data.add_field("title", title)
                data.add_field("file", f, filename=os.path.basename(file_path))
                resp = await s.post("https://slack.com/api/files.upload", data=data)
                payload = await resp.json(content_type=None)
                if resp.status >= 400 or not payload.get("ok", False):
                    raise RuntimeError(f"Slack file upload lỗi {resp.status}: {payload}")

    async def send_report(self, report: Dict[str, Any], excel_path: Optional[str] = None):
        blocks = format_slack_blocks(report)
        await self.send_blocks(blocks)
        if excel_path and os.path.exists(excel_path):
            await self.send_file(excel_path, title=f"Jira Report — {report['project']}")
        logger.info("✅ Đã gửi báo cáo qua Slack")
