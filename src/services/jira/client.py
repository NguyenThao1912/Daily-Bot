import os
import aiohttp
import logging
import base64
from typing import Any
from .models import JiraTicket

logger = logging.getLogger(__name__)

class JiraClient:
    """Client gọi Jira Cloud REST API v3"""

    def __init__(self):
        self.base_url = os.getenv("JIRA_BASE_URL", "").rstrip("/")  # vd: https://yourteam.atlassian.net
        self.email    = os.getenv("JIRA_EMAIL", "")
        self.api_token= os.getenv("JIRA_API_TOKEN", "")

        if not all([self.base_url, self.email, self.api_token]):
            raise ValueError("Thiếu biến môi trường: JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN")

        cred = base64.b64encode(f"{self.email}:{self.api_token}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {cred}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _get(self, path: str, params: dict = None) -> dict:
        url = f"{self.base_url}/rest/api/3{path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"Jira API lỗi {resp.status}: {text}")
                return await resp.json()

    async def fetch_tickets(
        self,
        project_key: str,
        max_results: int = 200,
        focus_epic_keys: list[str] | None = None,
    ) -> list[JiraTicket]:
        """Lấy toàn bộ ticket trong project (có phân trang)"""
        tickets = []
        start = 0
        page_size = 50

        jql = self._build_jql(project_key, focus_epic_keys)
        fields = "summary,description,status,issuetype,priority,assignee,reporter,created,updated,labels,comment,story_points,customfield_10016,customfield_10014,customfield_10020,parent"

        while True:
            data = await self._get("/search/jql", params={
                "jql": jql,
                "startAt": start,
                "maxResults": min(page_size, max_results - len(tickets)),
                "fields": fields,
            })

            issues = data.get("issues", [])
            if not issues:
                break

            for issue in issues:
                try:
                    tickets.append(self._parse_ticket(issue))
                except Exception as exc:
                    logger.warning("Bỏ qua ticket %s do parse lỗi: %s", issue.get("key", "?"), exc)

            start += len(issues)
            if start >= data.get("total", 0) or len(tickets) >= max_results:
                break

        if focus_epic_keys:
            focus_set = set(focus_epic_keys)
            tickets = [
                ticket
                for ticket in tickets
                if ticket.key in focus_set or ticket.epic_key in focus_set
            ]

        logger.info(f"Lấy được {len(tickets)} ticket từ project {project_key}")
        return tickets

    def _build_jql(self, project_key: str, focus_epic_keys: list[str] | None = None) -> str:
        if not focus_epic_keys:
            return f'project = "{project_key}" ORDER BY created DESC'

        quoted_keys = ", ".join(f'"{key}"' for key in focus_epic_keys)
        return (
            f'project = "{project_key}" AND ('
            f'issuekey in ({quoted_keys}) OR '
            f'parentEpic in ({quoted_keys})'
            f") ORDER BY updated DESC"
        )

    def _parse_ticket(self, issue: dict) -> JiraTicket:
        f = issue.get("fields", {})

        # Epic link (Cloud dùng customfield_10014 hoặc parent)
        epic_key, epic_name = None, None
        parent = f.get("parent")
        if parent and parent.get("fields", {}).get("issuetype", {}).get("name") == "Epic":
            epic_key = parent.get("key")
            epic_name = parent.get("fields", {}).get("summary")
        epic_key = epic_key or f.get("customfield_10014")

        # Story points
        sp = f.get("customfield_10016") or f.get("story_points")

        # Sprint
        sprint_name = self._extract_sprint_name(f.get("customfield_10020"))

        # Description (Jira Cloud trả về Atlassian Document Format)
        desc = self._extract_description(f.get("description"))
        reporter_name = f.get("reporter", {}).get("displayName") if f.get("reporter") else None
        assignee_name = f.get("assignee", {}).get("displayName") if f.get("assignee") else None
        comment_summary = self._extract_comment_summary(
            f.get("comment"),
            reporter_name=reporter_name,
            assignee_name=assignee_name,
        )

        return JiraTicket(
            key=issue["key"],
            summary=f.get("summary", ""),
            description=desc,
            status=f.get("status", {}).get("name", ""),
            issue_type=f.get("issuetype", {}).get("name", ""),
            priority=f.get("priority", {}).get("name", "") if f.get("priority") else "",
            assignee=assignee_name,
            reporter=reporter_name,
            epic_key=epic_key,
            epic_name=epic_name,
            created=f.get("created", ""),
            updated=f.get("updated", ""),
            labels=f.get("labels", []),
            story_points=self._parse_story_points(sp),
            sprint=sprint_name,
            comment_count=comment_summary["comment_count"],
            replied_by_devs=comment_summary["replied_by_devs"],
            last_dev_reply_by=comment_summary["last_dev_reply_by"],
            has_dev_reply=comment_summary["has_dev_reply"],
        )

    def _parse_story_points(self, value: Any) -> float | None:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            logger.warning("Không parse được story points: %r", value)
            return None

    def _extract_sprint_name(self, sprint_field: Any) -> str | None:
        if not sprint_field:
            return None
        if isinstance(sprint_field, list):
            for item in reversed(sprint_field):
                if isinstance(item, dict) and item.get("name"):
                    return item["name"]
                if isinstance(item, str):
                    parsed = self._extract_name_from_legacy_sprint(item)
                    if parsed:
                        return parsed
            return None
        if isinstance(sprint_field, dict):
            return sprint_field.get("name")
        if isinstance(sprint_field, str):
            return self._extract_name_from_legacy_sprint(sprint_field) or sprint_field
        return None

    def _extract_name_from_legacy_sprint(self, raw_value: str) -> str | None:
        marker = "name="
        if marker not in raw_value:
            return None
        start = raw_value.find(marker) + len(marker)
        end = raw_value.find(",", start)
        return raw_value[start:end] if end != -1 else raw_value[start:]

    def _extract_description(self, desc_field) -> str:
        """Chuyển Atlassian Document Format → plain text"""
        if not desc_field:
            return ""
        if isinstance(desc_field, str):
            return desc_field
        # ADF format
        texts = []
        def walk(node):
            if isinstance(node, dict):
                if node.get("type") == "text":
                    texts.append(node.get("text", ""))
                for child in node.get("content", []):
                    walk(child)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
        walk(desc_field)
        return " ".join(texts).strip()

    def _extract_comment_summary(
        self,
        comment_field: Any,
        reporter_name: str | None,
        assignee_name: str | None,
    ) -> dict[str, Any]:
        comments = []
        if isinstance(comment_field, dict):
            comments = comment_field.get("comments", []) or []
        elif isinstance(comment_field, list):
            comments = comment_field

        reporter_normalized = (reporter_name or "").strip().lower()
        assignee_normalized = (assignee_name or "").strip().lower()
        dev_repliers: list[str] = []
        last_dev_reply_by: str | None = None

        for comment in comments:
            author_name = (
                comment.get("author", {}).get("displayName")
                if isinstance(comment, dict)
                else None
            )
            if not author_name:
                continue
            normalized = author_name.strip().lower()
            is_dev_reply = False
            if assignee_normalized and normalized == assignee_normalized:
                is_dev_reply = True
            elif reporter_normalized and normalized != reporter_normalized:
                is_dev_reply = True
            elif reporter_normalized == "" and normalized:
                is_dev_reply = True

            if is_dev_reply:
                if author_name not in dev_repliers:
                    dev_repliers.append(author_name)
                last_dev_reply_by = author_name

        return {
            "comment_count": len(comments),
            "replied_by_devs": dev_repliers,
            "last_dev_reply_by": last_dev_reply_by,
            "has_dev_reply": bool(dev_repliers),
        }
