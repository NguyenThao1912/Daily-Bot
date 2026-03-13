from dataclasses import dataclass, field
from typing import Optional, List, Dict

@dataclass
class JiraTicket:
    key: str
    summary: str
    description: str
    status: str
    issue_type: str
    priority: str
    assignee: Optional[str]
    reporter: Optional[str]
    epic_key: Optional[str]
    epic_name: Optional[str]
    created: str
    updated: str
    labels: List[str] = field(default_factory=list)
    story_points: Optional[float] = None
    sprint: Optional[str] = None
    comment_count: int = 0
    replied_by_devs: List[str] = field(default_factory=list)
    last_dev_reply_by: Optional[str] = None
    has_dev_reply: bool = False
    # Nhãn do AI đánh
    ai_label: Optional[str] = None
    ai_label_reason: Optional[str] = None
    scrum_note: Optional[str] = None

@dataclass
class EpicSummary:
    epic_key: str
    epic_name: str
    tickets: List[JiraTicket] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.tickets)

    @property
    def by_ai_label(self) -> Dict[str, int]:
        result = {}
        for t in self.tickets:
            lbl = t.ai_label or "Chưa phân loại"
            result[lbl] = result.get(lbl, 0) + 1
        return result

    @property
    def by_status(self) -> Dict[str, int]:
        result = {}
        for t in self.tickets:
            result[t.status] = result.get(t.status, 0) + 1
        return result

    @property
    def completion_rate(self) -> float:
        done = sum(1 for t in self.tickets if t.status.lower() in ("done", "closed", "resolved"))
        return round(done / self.total * 100, 1) if self.total else 0.0
