import asyncio
import logging
import json
from datetime import datetime
from typing import List, Dict, Tuple, Any
from src.core.config import Config
from .models import JiraTicket, EpicSummary
from .prompts import TICKET_LABELING_PROMPT
from .client import JiraClient

logger = logging.getLogger(__name__)

DONE_STATUSES = {"done", "closed", "resolved"}
STALE_AGE_DAYS = 3
LABEL_BATCH_SIZE = 10


def _parse_ticket_date(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _is_stale(ticket: JiraTicket, now: datetime) -> bool:
    if ticket.status.lower() in DONE_STATUSES:
        return False

    updated_at = _parse_ticket_date(ticket.updated)
    created_at = _parse_ticket_date(ticket.created)
    reference = updated_at or created_at
    if reference is None:
        return False

    age_days = (now.date() - reference.date()).days
    return age_days >= STALE_AGE_DAYS


def _normalize_ai_reason(reason: str) -> str:
    cleaned = (reason or "").strip()
    if not cleaned:
        return "AI chưa cung cấp lý do phân loại."
    return cleaned


def _localize_ai_error(error: Exception | str) -> str:
    text = str(error).strip()
    lowered = text.lower()

    if "429" in lowered or "resource_exhausted" in lowered or "quota exceeded" in lowered:
        return "AI tạm vượt quota hoặc giới hạn tốc độ. Hãy chạy lại sau ít phút."
    if "404" in lowered and "model" in lowered:
        return "Model AI hiện tại không khả dụng hoặc cấu hình sai."
    if "timeout" in lowered:
        return "AI phản hồi quá lâu nên hệ thống đã bỏ qua ticket này."
    if "json" in lowered or "response không phải list" in lowered:
        return "AI trả về sai định dạng nên chưa thể phân loại ticket này."
    if "http" in lowered:
        return "AI trả về lỗi kết nối hoặc lỗi dịch vụ. Hãy thử lại sau."
    return "AI chưa phân loại được ticket này do lỗi xử lý nội bộ."

async def label_tickets_with_ai(tickets: List[JiraTicket], llm_client) -> List[JiraTicket]:
    """
    Đánh nhãn AI cho danh sách ticket.
    llm_client: async function nhận prompt → trả về string JSON
    """
    async def label_batch(batch: List[JiraTicket]) -> List[JiraTicket]:
        ticket_blocks = []
        for ticket in batch:
            ticket_blocks.append(
                TICKET_LABELING_PROMPT.format(
                    key=ticket.key,
                    issue_type=ticket.issue_type,
                    summary=ticket.summary,
                    description=ticket.description[:800] if ticket.description else "(không có)",
                    status=ticket.status,
                    labels=", ".join(ticket.labels) if ticket.labels else "(không có)",
                    priority=ticket.priority,
                    reporter=ticket.reporter or "(không có)",
                )
            )

        prompt = (
            "Bạn sẽ phân loại NHIỀU ticket Jira trong một lần.\n"
            "Với mỗi ticket bên dưới, hãy trả về đúng 1 object JSON trong một array JSON thuần.\n"
            "Mỗi object phải có các field: key, label, reason, confidence, scrum_note.\n"
            "Trường reason phải viết bằng tiếng Việt rõ ràng, không pha tiếng Anh trừ tên status bắt buộc.\n"
            "Không dùng markdown, không dùng giải thích ngoài JSON.\n\n"
            + "\n\n===== TICKET =====\n\n".join(ticket_blocks)
        )

        try:
            raw = await llm_client(prompt)
            start = raw.find("[")
            end = raw.rfind("]") + 1
            parsed = json.loads(raw[start:end])
            if not isinstance(parsed, list):
                raise ValueError(f"AI response không phải list JSON: {parsed}")

            by_key = {
                str(item.get("key", "")).strip(): item
                for item in parsed
                if isinstance(item, dict) and item.get("key")
            }

            for ticket in batch:
                data = by_key.get(ticket.key)
                if not data:
                    ticket.ai_label = "Chưa phân loại"
                    ticket.ai_label_reason = "AI không trả kết quả cho ticket này."
                    ticket.scrum_note = None
                    continue
                ticket.ai_label = data.get("label", "Chưa phân loại")
                ticket.ai_label_reason = _normalize_ai_reason(data.get("reason", ""))
                ticket.scrum_note = data.get("scrum_note", "") or None
        except Exception as e:
            logger.warning(
                "Không label được batch tickets %s: %s",
                ", ".join(ticket.key for ticket in batch),
                e,
            )
            for ticket in batch:
                ticket.ai_label = "Chưa phân loại"
                ticket.ai_label_reason = _localize_ai_error(e)
                ticket.scrum_note = None
        return batch

    batches = [
        tickets[index : index + LABEL_BATCH_SIZE]
        for index in range(0, len(tickets), LABEL_BATCH_SIZE)
    ]

    semaphore = asyncio.Semaphore(1)

    async def bounded(batch: List[JiraTicket]) -> List[JiraTicket]:
        async with semaphore:
            return await label_batch(batch)

    labeled_batches = await asyncio.gather(*(bounded(batch) for batch in batches))
    return [ticket for batch in labeled_batches for ticket in batch]

def build_epic_summaries(tickets: List[JiraTicket]) -> Dict[str, EpicSummary]:
    """Nhóm ticket theo Epic"""
    epics: Dict[str, EpicSummary] = {}
    no_epic_key = "NO_EPIC"

    for ticket in tickets:
        key = ticket.epic_key or no_epic_key
        name = ticket.epic_name or "Không thuộc Epic"
        if key not in epics:
            epics[key] = EpicSummary(epic_key=key, epic_name=name)
        epics[key].tickets.append(ticket)

    return epics

def build_scrum_master_report(epics: Dict[str, EpicSummary], project_key: str) -> Dict[str, Any]:
    """Tổng hợp báo cáo Scrum Master"""
    all_tickets = [t for e in epics.values() for t in e.tickets]
    now = datetime.now()

    stale_tickets = [
        t for t in all_tickets
        if _is_stale(t, now)
    ]

    blocked_tickets = [
        t for t in all_tickets
        if (
            "block" in " ".join(t.labels).lower()
            or t.status.lower() == "blocked"
            or (t.scrum_note or "").upper() == "BLOCKED"
        )
    ]

    no_assignee = [t for t in all_tickets if not t.assignee]

    return {
        "project": project_key,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_tickets": len(all_tickets),
        "epics_count": len(epics),
        "label_summary": {
            lbl: sum(1 for t in all_tickets if t.ai_label == lbl)
            for lbl in ("bug", "request_feature", "new_feature", "in_progress", "Chưa phân loại")
        },
        "status_summary": {
            s: sum(1 for t in all_tickets if t.status == s)
            for s in set(t.status for t in all_tickets)
        },
        "epics": {k: {
            "name": v.epic_name,
            "total": v.total,
            "completion_rate": v.completion_rate,
            "by_label": v.by_ai_label,
            "by_status": v.by_status,
        } for k, v in epics.items()},
        "scrum_alerts": {
            "stale_count": len(stale_tickets),
            "blocked_count": len(blocked_tickets),
            "no_assignee_count": len(no_assignee),
            "stale_keys": [t.key for t in stale_tickets[:10]],
            "blocked_keys": [t.key for t in blocked_tickets[:10]],
        }
    }

async def run_jira_analysis(project_key: str, llm_client) -> Tuple[List[JiraTicket], Dict[str, Any]]:
    """
    Pipeline chính:
    1. Lấy tickets từ Jira
    2. Đánh nhãn bằng AI
    3. Build report
    """
    client = JiraClient()

    logger.info(f"🔍 Đang lấy tickets từ project {project_key}...")
    tickets = await client.fetch_tickets(
        project_key,
        focus_epic_keys=Config.JIRA_FOCUS_EPIC_KEYS,
    )

    logger.info(f"🤖 Đang đánh nhãn {len(tickets)} tickets...")
    tickets = await label_tickets_with_ai(tickets, llm_client)

    epics = build_epic_summaries(tickets)
    report = build_scrum_master_report(epics, project_key)

    logger.info(f"✅ Hoàn thành phân tích: {report['total_tickets']} tickets, {report['epics_count']} epics")
    return tickets, report
