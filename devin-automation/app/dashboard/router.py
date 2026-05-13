# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.crud import list_jobs
from app.db.models import Job
from app.db.session import get_db

router = APIRouter()

STATUS_COLORS: dict[str, str] = {
    "pending": "#6c757d",
    "running": "#0d6efd",
    "exit": "#198754",
    "error": "#dc3545",
    "suspended": "#ffc107",
}


def _metric(value: str, label: str, color: str = "") -> str:
    style = f' style="color:{color}"' if color else ""
    return (
        f'<div class="metric">'
        f'<div class="value"{style}>{value}</div>'
        f'<div class="label">{label}</div>'
        f"</div>"
    )


def _build_row(j: Job) -> str:
    color = STATUS_COLORS.get(str(j.status), "#333")
    sid = j.devin_session_id or "\u2014"
    session_link = (
        f'<a href="{j.devin_session_url}" target="_blank">{sid}</a>'
        if j.devin_session_url
        else "\u2014"
    )
    pr_link = f'<a href="{j.pr_url}" target="_blank">PR</a>' if j.pr_url else "\u2014"
    created = j.created_at.strftime("%Y-%m-%d %H:%M") if j.created_at else "\u2014"
    title = j.issue_title or "\u2014"
    return (
        f"<tr>"
        f"<td>{j.issue_number}</td>"
        f'<td><a href="{j.issue_url}"'
        f' target="_blank">{title}</a></td>'
        f'<td style="color:{color};font-weight:600">'
        f"{j.status}</td>"
        f"<td>{session_link}</td>"
        f"<td>{pr_link}</td>"
        f"<td>{created}</td>"
        f"</tr>"
    )


_CSS = """\
body{font-family:system-ui,sans-serif;margin:2rem;background:#f8f9fa}
h1{margin-bottom:.5rem}
.metrics{display:flex;gap:1.5rem;margin-bottom:1.5rem}
.metric{background:#fff;border-radius:8px;padding:1rem 1.5rem;
  box-shadow:0 1px 3px rgba(0,0,0,.1);text-align:center}
.metric .value{font-size:2rem;font-weight:700}
.metric .label{font-size:.85rem;color:#6c757d}
table{width:100%;border-collapse:collapse;background:#fff;
  border-radius:8px;overflow:hidden;
  box-shadow:0 1px 3px rgba(0,0,0,.1)}
th,td{padding:.75rem 1rem;text-align:left;
  border-bottom:1px solid #dee2e6}
th{background:#343a40;color:#fff}
a{color:#0d6efd;text-decoration:none}
a:hover{text-decoration:underline}"""

_EMPTY_ROW = (
    "<tr><td colspan='6' style='text-align:center;color:#6c757d'>No jobs yet</td></tr>"
)

_THEAD = (
    "<thead><tr>"
    "<th>#</th><th>Issue</th><th>Status</th>"
    "<th>Session</th><th>PR</th><th>Created</th>"
    "</tr></thead>"
)


def _build_html(
    jobs: list[Job],
    total: int,
    success: int,
    failed: int,
    running: int,
    avg_mins: int,
) -> str:
    rows = "".join(_build_row(j) for j in jobs)
    rate = round(success / total * 100) if total else 0

    metrics = (
        _metric(str(total), "Total Jobs")
        + _metric(f"{rate}%", "Success Rate", "#198754")
        + _metric(str(failed), "Failed", "#dc3545")
        + _metric(str(running), "Running", "#0d6efd")
        + _metric(f"{avg_mins}m", "Avg Time-to-PR")
    )

    tbody = rows if rows else _EMPTY_ROW

    return (
        "<!DOCTYPE html>"
        '<html lang="en"><head>'
        '<meta charset="utf-8"/>'
        '<meta name="viewport"'
        ' content="width=device-width,initial-scale=1"/>'
        "<title>Devin Automation Dashboard</title>"
        f"<style>{_CSS}</style>"
        "</head><body>"
        "<h1>Devin Automation Dashboard</h1>"
        f'<div class="metrics">{metrics}</div>'
        f"<table>{_THEAD}<tbody>{tbody}</tbody></table>"
        "</body></html>"
    )


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    db: Session = Depends(get_db),  # noqa: B008
) -> str:
    """Render a simple HTML dashboard of automation jobs."""
    jobs = list_jobs(db)

    total = len(jobs)
    success = sum(1 for j in jobs if j.status == "exit")
    failed = sum(1 for j in jobs if j.status in ("error", "suspended"))
    running = sum(1 for j in jobs if j.status == "running")

    durations = [
        int(
            (j.finished_at - j.started_at).total_seconds(),
        )
        // 60
        for j in jobs
        if j.status == "exit" and j.started_at and j.finished_at
    ]
    avg_mins = round(sum(durations) / len(durations)) if durations else 0

    return _build_html(jobs, total, success, failed, running, avg_mins)
