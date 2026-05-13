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

from app.db.models import Job
from app.orchestrator.prompt_builder import build_prompt


def test_build_prompt_includes_issue_details() -> None:
    job = Job(
        id="test-uuid",
        issue_number=99,
        issue_title="Add dark mode",
        issue_body="We need dark mode support.",
        issue_url="https://github.com/org/repo/issues/99",
        repo="org/repo",
    )
    prompt = build_prompt(job)

    assert "Add dark mode" in prompt
    assert "We need dark mode support." in prompt
    assert "#99" in prompt
    assert "org/repo" in prompt
    assert "https://github.com/org/repo/issues/99" in prompt


def test_build_prompt_handles_empty_body() -> None:
    job = Job(
        id="test-uuid",
        issue_number=1,
        issue_title="Empty body issue",
        issue_body=None,
        issue_url="https://github.com/org/repo/issues/1",
        repo="org/repo",
    )
    prompt = build_prompt(job)
    assert "(no body)" in prompt
