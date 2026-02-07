# Slough.ai - Decision-Maker Persona Slack Bot

> Slack 대화로 의사결정자의 사고를 학습하는 AI - learns from a decision-maker's Slack conversation history and provides persona-based answers to employees.

## Problem & Solution

**Problem:**
- Decision-makers are bombarded with repetitive questions on Slack
- Most questions have already been answered before with the same logic
- Decision-maker's reasoning patterns exist in Slack but aren't reusable
- Operations stall while waiting for approval/direction

**Solution:**
- Learn from the decision-maker's entire Slack conversation history
- Provide instant persona-based answers to employees via DM
- Maintain feedback loop for continuous improvement
- Rules take precedence over learned patterns for explicit control

## Project Structure

```
slough-ai/
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md      # System architecture
│   ├── MVP-SPEC.md          # Feature specifications
│   ├── TESTING.md           # Testing strategy
│   ├── COSTS.md             # Cost analysis
│   ├── ROADMAP.md           # Development timeline
│   ├── SETUP.md             # Setup instructions
│   └── SLACK-API.md         # Slack API details
├── src/
│   ├── app.py               # Slack Bolt app entry
│   ├── config.py            # Environment config (pydantic-settings)
│   ├── handlers/            # Event & action handlers
│   ├── services/            # Business logic
│   └── utils/               # Utilities
├── tests/                   # Test files
├── scripts/                 # Setup & maintenance scripts
├── CLAUDE.md                # Instructions for Claude CLI
└── README.md                # This file
```

## Quick Start

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env

# Start in development mode (Socket Mode)
python src/app.py
```

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System design & data flow |
| [MVP Spec](docs/MVP-SPEC.md) | Feature requirements |
| [Testing](docs/TESTING.md) | Testing strategy & environments |
| [Costs](docs/COSTS.md) | Development & production costs |
| [Roadmap](docs/ROADMAP.md) | Week-by-week development plan |
| [Setup](docs/SETUP.md) | Detailed setup instructions |
| [Slack API](docs/SLACK-API.md) | Slack scopes & API reference |

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** Slack Bolt for Python
- **Web Framework:** FastAPI
- **Database:** PostgreSQL
- **Vector DB:** Pinecone Serverless
- **LLM:** OpenAI GPT-4o
- **Embeddings:** OpenAI text-embedding-3-small
- **Queue:** Celery + Redis

## Ideal Customer Profile

- Teams with heavy Slack usage and rich conversation history
- Organizations with clear decision-making frameworks from leadership
- Startups requiring thought-alignment between executives and staff
- Organizations where operational delays from approval bottlenecks are costly

## Not Suitable For

- Very large organizations
- Low-Slack-usage teams
- Environments requiring legal/financial AI liability

## License

Private - All rights reserved
