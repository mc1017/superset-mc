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

PROMPT_TEMPLATE = """\
You are working on the repository {repo}.

## Task
{issue_title}

## Issue details
{issue_body}

## Instructions
1. Clone the repository if not already available.
2. Understand the issue fully before making any changes.
3. Implement a fix with minimal scope — do not refactor unrelated code.
4. Ensure existing tests still pass.
5. If fixing a dependency, update requirements files and lock files.
6. Open a pull request against the main branch with:
   - A clear title referencing issue #{issue_number}
   - A description explaining what you changed and why
   - Link back to the issue: "Closes #{issue_number}"
7. Post the PR URL as a comment on issue #{issue_number}.

## Constraints
- Do not modify unrelated files.
- Do not bump unrelated dependency versions.
- If you are blocked or unsure, leave a comment on the issue explaining why.

GitHub issue URL: {issue_url}
"""


def build_prompt(job: Job) -> str:
    """Construct the Devin session prompt from a Job row."""
    return PROMPT_TEMPLATE.format(
        repo=job.repo,
        issue_title=job.issue_title,
        issue_body=job.issue_body or "(no body)",
        issue_number=job.issue_number,
        issue_url=job.issue_url,
    )
