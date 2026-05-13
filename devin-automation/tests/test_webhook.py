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

import hashlib
import hmac
from unittest.mock import patch

from app.db.models import Job
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _make_payload(
    action: str = "labeled",
    label_name: str = "devin-ready",
) -> dict[str, object]:
    return {
        "action": action,
        "label": {"name": label_name},
        "issue": {
            "number": 42,
            "title": "Fix the widget",
            "body": "The widget is broken.",
            "html_url": "https://github.com/test-org/test-repo/issues/42",
        },
        "repository": {"full_name": "test-org/test-repo"},
    }


def _sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_webhook_ignores_non_issue_events(client: TestClient) -> None:
    resp = client.post(
        "/webhook/github",
        json=_make_payload(),
        headers={"X-GitHub-Event": "push"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


def test_webhook_ignores_wrong_action(client: TestClient) -> None:
    resp = client.post(
        "/webhook/github",
        json=_make_payload(action="opened"),
        headers={"X-GitHub-Event": "issues"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


def test_webhook_ignores_wrong_label(client: TestClient) -> None:
    resp = client.post(
        "/webhook/github",
        json=_make_payload(label_name="bug"),
        headers={"X-GitHub-Event": "issues"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"


@patch("app.webhook.router.dispatch_session")
def test_webhook_accepts_matching_event(
    mock_dispatch: object,
    client: TestClient,
    db_session: Session,
) -> None:
    resp = client.post(
        "/webhook/github",
        json=_make_payload(),
        headers={"X-GitHub-Event": "issues"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "accepted"
    assert "job_id" in data

    job = db_session.query(Job).first()
    assert job is not None
    assert job.issue_number == 42
    assert job.status == "pending"


def test_webhook_rejects_invalid_signature(client: TestClient) -> None:
    with patch("app.webhook.validator.settings") as mock_settings:
        mock_settings.github_webhook_secret = "real-secret"  # noqa: S105

        resp = client.post(
            "/webhook/github",
            json=_make_payload(),
            headers={
                "X-GitHub-Event": "issues",
                "X-Hub-Signature-256": "sha256=invalid",
            },
        )
        assert resp.status_code == 403
