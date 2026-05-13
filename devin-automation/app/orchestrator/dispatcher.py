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

import httpx

from app.config import settings
from app.db.crud import get_job, update_job_session, update_job_status
from app.db.session import SessionLocal
from app.github.client import post_issue_comment
from app.orchestrator.poller import poll_until_complete
from app.orchestrator.prompt_builder import build_prompt

logger = logging.getLogger(__name__)


async def dispatch_session(job_id: str) -> None:
    """Create a Devin session for *job_id*, poll it, and post results."""
    db = SessionLocal()
    try:
        job = get_job(db, job_id)
        if job is None:
            logger.error("Job %s not found", job_id)
            return

        prompt = build_prompt(job)
        headers = {
            "Authorization": f"Bearer {settings.devin_api_key}",
            "Content-Type": "application/json",
        }
        create_url = (
            f"{settings.devin_api_base}/organizations/{settings.devin_org_id}/sessions"
        )

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                create_url,
                headers=headers,
                json={"prompt": prompt},
                timeout=30,
            )
            resp.raise_for_status()
            session_data = resp.json()

        session_id: str = session_data["session_id"]
        session_url: str = session_data["url"]

        update_job_session(db, job_id, session_id=session_id, session_url=session_url)
        update_job_status(db, job_id, "running")
    finally:
        db.close()

    post_issue_comment(
        repo=job.repo,
        issue_number=job.issue_number,
        body=(f"Devin has picked up this issue. [View session]({session_url})"),
    )

    final_status = await poll_until_complete(session_id, job_id)

    if final_status == "exit":
        post_issue_comment(
            repo=job.repo,
            issue_number=job.issue_number,
            body=(f"Devin completed the task. [View session]({session_url})"),
        )
    else:
        post_issue_comment(
            repo=job.repo,
            issue_number=job.issue_number,
            body=(
                f"Devin session ended with status `{final_status}`. "
                f"[View session]({session_url})"
            ),
        )
