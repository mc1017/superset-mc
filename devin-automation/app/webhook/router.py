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

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.db.crud import create_job
from app.db.session import get_db
from app.orchestrator.dispatcher import dispatch_session
from app.webhook.models import GitHubIssueEvent
from app.webhook.validator import verify_signature

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhook/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, str]:
    """Receive GitHub issue webhook events and dispatch Devin sessions."""
    body = await request.body()
    verify_signature(body, request.headers.get("X-Hub-Signature-256"))

    event_type = request.headers.get("X-GitHub-Event")
    if event_type != "issues":
        return {"status": "ignored", "reason": "not an issue event"}

    payload = await request.json()
    event = GitHubIssueEvent(**payload)

    if event.action != "labeled":
        return {"status": "ignored", "reason": "action is not 'labeled'"}

    if event.label is None or event.label.name != settings.trigger_label:
        return {"status": "ignored", "reason": "label does not match trigger"}

    job = create_job(
        db,
        issue_number=event.issue.number,
        issue_title=event.issue.title,
        issue_url=event.issue.html_url,
        issue_body=event.issue.body or "",
        repo=event.repository.full_name,
    )

    logger.info("Created job %s for issue #%s", job.id, event.issue.number)
    background_tasks.add_task(dispatch_session, job.id)

    return {"status": "accepted", "job_id": str(job.id)}
