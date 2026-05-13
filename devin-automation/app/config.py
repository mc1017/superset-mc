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

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    devin_api_key: str = os.getenv("DEVIN_API_KEY", "")
    devin_org_id: str = os.getenv("DEVIN_ORG_ID", "")
    github_webhook_secret: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    github_token: str = os.getenv("GITHUB_TOKEN", "")

    devin_api_base: str = "https://api.devin.ai/v3"
    trigger_label: str = "devin-ready"
    poll_interval_seconds: int = 15

    database_url: str = (
        f"sqlite:///{Path(__file__).resolve().parent.parent / 'data' / 'jobs.db'}"
    )

    class Config:
        env_file = ".env"


settings = Settings()
