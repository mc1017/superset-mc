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

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Job


def create_job(
    db: Session,
    *,
    issue_number: int,
    issue_title: str,
    issue_url: str,
    issue_body: str,
    repo: str,
) -> Job:
    """Insert a new pending job row."""
    job = Job(
        issue_number=issue_number,
        issue_title=issue_title,
        issue_url=issue_url,
        issue_body=issue_body,
        repo=repo,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str) -> Job | None:
    """Fetch a job by its UUID primary key."""
    return db.query(Job).filter(Job.id == job_id).first()


def update_job_session(
    db: Session,
    job_id: str,
    *,
    session_id: str,
    session_url: str,
) -> None:
    """Persist the Devin session ID and URL on a job."""
    job = get_job(db, job_id)
    if job is None:
        return
    job.devin_session_id = session_id
    job.devin_session_url = session_url
    job.started_at = datetime.now(timezone.utc)
    db.commit()


def update_job_status(
    db: Session,
    job_id: str,
    status: str,
    *,
    error_message: str | None = None,
    pr_url: str | None = None,
) -> None:
    """Update job status and optionally set terminal fields."""
    job = get_job(db, job_id)
    if job is None:
        return
    job.status = status
    if error_message is not None:
        job.error_message = error_message
    if pr_url is not None:
        job.pr_url = pr_url
    if status in ("exit", "error", "suspended"):
        job.finished_at = datetime.now(timezone.utc)
    db.commit()


def list_jobs(db: Session, *, limit: int = 50) -> list[Job]:
    """Return the most recent jobs ordered by creation time descending."""
    return db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()
