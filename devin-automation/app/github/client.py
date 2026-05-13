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

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


def post_issue_comment(repo: str, issue_number: int, body: str) -> None:
    """Post a comment on a GitHub issue.

    Args:
        repo: Repository full name, e.g. ``"owner/repo"``.
        issue_number: The issue number to comment on.
        body: Markdown body of the comment.
    """
    url = f"{GITHUB_API}/repos/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        resp = httpx.post(url, headers=headers, json={"body": body}, timeout=15)
        resp.raise_for_status()
        logger.info("Posted comment on %s#%s", repo, issue_number)
    except httpx.HTTPError:
        logger.exception("Failed to post comment on %s#%s", repo, issue_number)
