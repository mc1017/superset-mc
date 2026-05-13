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

import asyncio
import logging

import httpx

from app.config import settings
from app.db.crud import update_job_status
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

TERMINAL_STATUSES = {"exit", "error", "suspended"}


async def poll_until_complete(session_id: str, job_id: str) -> str:
    """Poll the Devin API until the session reaches a terminal status.

    Returns the final status string.
    """
    headers = {"Authorization": f"Bearer {settings.devin_api_key}"}
    url = (
        f"{settings.devin_api_base}/organizations/{settings.devin_org_id}"
        f"/sessions/{session_id}"
    )

    async with httpx.AsyncClient() as client:
        while True:
            try:
                resp = await client.get(url, headers=headers, timeout=15)
                resp.raise_for_status()
                status: str = resp.json()["status"]
            except httpx.HTTPError:
                logger.exception("Error polling session %s", session_id)
                await asyncio.sleep(settings.poll_interval_seconds)
                continue

            db = SessionLocal()
            try:
                update_job_status(db, job_id, status)
            finally:
                db.close()

            if status in TERMINAL_STATUSES:
                logger.info(
                    "Session %s reached terminal status: %s", session_id, status
                )
                return status

            await asyncio.sleep(settings.poll_interval_seconds)
