# Slough.ai Setup Guide

## Prerequisites

- Python 3.12+ installed
- Docker & Docker Compose (for local development)
- Slack workspace (free tier works)
- OpenAI API key

## Quick Start

### 1. Clone and Install

```bash
cd slough-ai

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (creates venv automatically)
uv sync
```

### 2. Set Up Local Database

```bash
# Start PostgreSQL (with pgvector) and Redis
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 3. Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Name: "Slough.ai" (or your preferred name)
5. Select your development workspace

### 4. Configure Slack App

#### Enable Socket Mode (for local development)
1. Go to **Settings -> Socket Mode**
2. Toggle **Enable Socket Mode** ON
3. Create App-Level Token with `connections:write` scope
4. Copy the `xapp-` token

#### Set OAuth Scopes
1. Go to **OAuth & Permissions**
2. Add Bot Token Scopes (see SLACK-API.md for full list)
3. Add User Token Scopes (see SLACK-API.md for full list)

#### Enable Events
1. Go to **Event Subscriptions**
2. Toggle **Enable Events** ON
3. Subscribe to bot events: `message.im`, `app_uninstalled`

#### Create Slash Commands
1. Go to **Slash Commands**
2. Create commands: `/slough-rule`, `/slough-ingest`, `/slough-stats`, `/slough-help`

#### Enable Interactivity
1. Go to **Interactivity & Shortcuts**
2. Toggle **Interactivity** ON

### 5. Install App to Workspace

1. Go to **Install App**
2. Click "Install to Workspace"
3. Authorize the app
4. Copy Bot Token (`xoxb-...`) and User Token (`xoxp-...`)

### 6. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit with your values
nano .env
```

```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-level-token  # Socket Mode only
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_CLIENT_ID=your-client-id
SLACK_CLIENT_SECRET=your-client-secret

# Database (PostgreSQL + pgvector)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/slough

# Redis
REDIS_URL=redis://localhost:6379

# LLM & Embeddings
OPENAI_API_KEY=sk-your-key

# App Configuration
LOG_LEVEL=DEBUG
SERVICE_TYPE=web
```

### 7. Run Migrations

```bash
uv run alembic upgrade head
```

### 8. Start Development Server

```bash
# Terminal 1: App (Socket Mode)
PYTHONPATH=. uv run python src/app.py

# Terminal 2: Celery Worker
PYTHONPATH=. uv run celery -A src.worker worker --loglevel=info --concurrency=2

# Terminal 3: Celery Beat (scheduler)
PYTHONPATH=. uv run celery -A src.worker beat --loglevel=info
```

### 9. Test the Bot

1. Open Slack
2. Find your bot in Apps
3. Send a DM: "Hello"
4. Bot should respond

## Docker Compose Configuration

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: slough
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
```

Note: Use `pgvector/pgvector:pg16` image instead of vanilla PostgreSQL to get pgvector extension pre-installed.

## Production Deployment (AWS)

### AWS Resources

| Service | AWS Resource | Purpose |
|---------|-------------|---------|
| Compute | ECS Fargate | 3 services (app, worker, beat) |
| Database | RDS PostgreSQL | Data + pgvector embeddings |
| Cache/Queue | ElastiCache Redis | Celery + persona cache |
| Load Balancer | ALB | HTTP routing |
| CDN/HTTPS | CloudFront | HTTPS termination for Slack |
| Container Registry | ECR | Docker image storage |
| Logging | CloudWatch | Centralized logs |
| CI/CD | GitHub Actions | Auto-deploy on push to main |

### Deployment

Deployment is automated via GitHub Actions. Push to `main` branch triggers:
1. Build Docker image
2. Push to ECR
3. Update ECS services

### Slack App URLs (Production)

Set these in your Slack app settings:

- **Install URL:** `https://{cloudfront-domain}/slack/install`
- **OAuth Redirect:** `https://{cloudfront-domain}/slack/oauth_redirect`
- **Event Subscriptions URL:** `https://{cloudfront-domain}/slack/events`
- **Interactivity Request URL:** `https://{cloudfront-domain}/slack/events`

Important: Users must install via the `/slack/install` URL (not the Slack API site button) for OAuth to work properly.

## Verifying Setup

### Check Database Connection

```bash
# Connect to PostgreSQL
docker exec -it slough-postgres psql -U postgres -d slough

# Verify pgvector extension
SELECT * FROM pg_extension WHERE extname = 'vector';

# List tables
\dt
```

### Check Slack Connection

```python
# scripts/test_slack.py
import os
from slack_bolt import App
from dotenv import load_dotenv

load_dotenv()

app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)

result = app.client.auth_test()
print(f"Bot user: {result['user']}")
print("Bolt app connected successfully!")
```

### Check LLM Connection

```python
# scripts/test_llm.py
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o",
    max_tokens=100,
    messages=[{"role": "user", "content": "안녕하세요"}],
)
print(f"Response: {response.choices[0].message.content}")
```

## Troubleshooting

### "Invalid token" Error
- Check that tokens don't have extra whitespace
- Verify tokens match the correct environment
- Reinstall app to workspace if needed

### Socket Mode Connection Issues
- Ensure `SLACK_APP_TOKEN` starts with `xapp-`
- Check that Socket Mode is enabled in app settings
- Verify network connectivity

### Database Connection Failed
- Check Docker containers are running: `docker-compose ps`
- Verify `DATABASE_URL` format is correct
- Try connecting manually with psql

### pgvector Extension Missing
- Use `pgvector/pgvector:pg16` Docker image
- Or run: `CREATE EXTENSION IF NOT EXISTS vector;`

### Embeddings Failing
- Verify `OPENAI_API_KEY` is valid
- Check API quota/billing status
- Test with smaller input first

## Next Steps

After setup is complete:

1. Read [ARCHITECTURE.md](./ARCHITECTURE.md) for system design
2. Follow [ROADMAP.md](./ROADMAP.md) for development phases
3. Reference [MVP-SPEC.md](./MVP-SPEC.md) for feature requirements
4. Use [TESTING.md](./TESTING.md) for testing strategies
