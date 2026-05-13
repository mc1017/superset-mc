# Devin Automation

Event-driven automation system that connects GitHub issues to Devin AI sessions.
When a GitHub issue receives the `devin-ready` label, the system automatically:

1. Creates a Devin session with a prompt built from the issue
2. Posts a "picked up" comment on the issue with a session link
3. Polls the Devin API until the session completes
4. Posts the final outcome back to the issue

A built-in `/dashboard` route provides a live HTML view of all jobs.

## Architecture

```
GitHub Issue (labeled "devin-ready")
        │
        ▼
  POST /webhook/github  ──► HMAC validation
        │
        ▼
  Create Job (SQLite)
        │
        ▼
  Background task:
    ├── Build prompt from issue
    ├── POST Devin API → create session
    ├── Comment on issue ("picked up")
    ├── Poll GET /sessions/{id} until terminal
    └── Comment on issue (result)
```

## Quick Start

```bash
# Clone and configure
cp .env.example .env
# Edit .env with your credentials

# Run with Docker
docker compose up --build

# Or run locally
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Configuration

| Variable | Description |
|---|---|
| `DEVIN_API_KEY` | Devin service user API key (starts with `cog_`) |
| `DEVIN_ORG_ID` | Devin organization ID |
| `GITHUB_WEBHOOK_SECRET` | Secret for HMAC webhook validation |
| `GITHUB_TOKEN` | GitHub PAT for posting issue comments |

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/webhook/github` | Receives GitHub webhook events |
| `GET`  | `/dashboard` | HTML dashboard with job metrics |
| `GET`  | `/health` | Health check |

## GitHub Webhook Setup

1. In your repo: **Settings → Webhooks → Add webhook**
2. Payload URL: `https://your-server:8000/webhook/github`
3. Content type: `application/json`
4. Secret: your `GITHUB_WEBHOOK_SECRET`
5. Events: select **Issues** only

Create a `devin-ready` label in your repo. Apply it to any issue to trigger automation.

## Devin API Credentials

1. Go to Devin org **Settings → Service users → Create service user**
2. Choose the **Member** role
3. Click **Generate API key** (starts with `cog_`, shown once)
4. Copy the org ID from the same page

## Running Tests

```bash
pip install -r requirements.txt pytest
cd devin-automation
pytest -v
```

## Dashboard

Visit `http://localhost:8000/dashboard` to see:
- Total jobs, success rate, failure count, running count
- Average time-to-PR for successful jobs
- Table of recent jobs with status, session links, and PR links
