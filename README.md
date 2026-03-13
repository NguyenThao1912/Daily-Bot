# Daily-Bot Jira Reporting

Nhánh `jira-reporting` chỉ giữ lại phần code phục vụ báo cáo Jira.

Entry point:

- `run_jira.py`

Thành phần chính:

- `src/core/config.py`
- `src/services/jira/`
- `.github/workflows/jira_run.yml`

Chạy local:

```bash
uv sync
uv run python run_jira.py
```
