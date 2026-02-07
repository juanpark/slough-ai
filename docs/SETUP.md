# Slough.ai Setup Guide

## Prerequisites

- Python 3.10+ installed
- Docker & Docker Compose (for local development)
- Slack workspace (free tier works)
- OpenAI API key

## Quick Start

### 1. Clone and Install

```bash
cd slough-ai

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up Local Database

```bash
# Start PostgreSQL and Redis
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

#### Enable Socket Mode
1. Go to **Settings → Socket Mode**
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
3. Subscribe to bot events: `message.im`

#### Create Slash Command
1. Go to **Slash Commands**
2. Create `/rule` command
3. Set request URL (will be handled via Socket Mode)

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
SLACK_APP_TOKEN=xapp-your-app-level-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_CLIENT_ID=your-client-id
SLACK_CLIENT_SECRET=your-client-secret

# Database
DATABASE_URL=postgres://postgres:postgres@localhost:5432/slough

# Redis
REDIS_URL=redis://localhost:6379

# LLM & Embeddings
OPENAI_API_KEY=sk-your-key

# Vector DB
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=slough-contexts

# App Configuration
LOG_LEVEL=DEBUG
```

### 7. Run Migrations

```bash
alembic upgrade head
```

### 8. Start Development Server

```bash
python src/app.py
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
    image: postgres:16-alpine
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

## Project Structure Setup

```bash
# Create directory structure
mkdir -p src/{handlers/{events,actions,commands,views},services/{slack,ai,db,ingestion,scheduler},utils}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p scripts

# Create initial files
touch src/app.py
touch src/config.py
touch src/handlers/events/message.py
touch src/handlers/actions/review_request.py
touch src/handlers/actions/feedback.py
touch src/handlers/commands/rule.py
touch src/handlers/views/edit_answer.py
touch src/services/slack/messages.py
touch src/services/slack/conversations.py
touch src/services/ai/__init__.py
touch src/services/ai/embeddings.py
touch src/services/ai/generation.py
touch src/services/ai/vector_search.py
touch src/services/db/connection.py
touch src/services/db/models.py
touch src/utils/blocks.py
touch src/utils/keywords.py
touch src/utils/logger.py
```

## Requirements (requirements.txt)

```txt
# Slack
slack-bolt>=1.18.0
slack-sdk>=3.27.0

# Web framework
fastapi>=0.110.0
uvicorn>=0.27.0

# LLM & Embeddings
openai>=1.12.0

# Vector DB
pinecone-client>=3.1.0

# Database
sqlalchemy>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0
psycopg2-binary>=2.9.0

# Queue
celery>=5.3.0
redis>=5.0.0

# Config & Utils
pydantic-settings>=2.1.0
structlog>=24.1.0
python-dotenv>=1.0.0

# Dev
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

## Slack App Manifest (Alternative Setup)

Instead of manual configuration, you can use an app manifest:

```yaml
display_information:
  name: Slough.ai
  description: Decision-Maker Persona AI Assistant
  background_color: "#2c2d30"

features:
  bot_user:
    display_name: Slough.ai
    always_online: true
  slash_commands:
    - command: /rule
      description: Manage decision-maker rules
      usage_hint: "add/list/delete [rule]"

oauth_config:
  scopes:
    user:
      - channels:history
      - channels:read
      - groups:history
      - groups:read
      - im:history
      - im:read
      - mpim:history
      - users:read
    bot:
      - chat:write
      - im:history
      - im:read
      - im:write
      - commands
      - users:read

settings:
  event_subscriptions:
    bot_events:
      - message.im
  interactivity:
    is_enabled: true
  org_deploy_enabled: false
  socket_mode_enabled: true
  token_rotation_enabled: false
```

## Verifying Setup

### Check Database Connection

```bash
# Connect to PostgreSQL
docker exec -it slough-postgres psql -U postgres -d slough

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

### Check Pinecone Connection

```python
# scripts/test_pinecone.py
import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index(os.environ["PINECONE_INDEX_NAME"])

stats = index.describe_index_stats()
print(f"Pinecone index stats: {stats}")
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
