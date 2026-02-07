# Slough.ai Testing Strategy

## Testing Environments

### Environment Overview

| Environment | Purpose | Slack Workspace | Database |
|-------------|---------|-----------------|----------|
| **Local/Dev** | Daily coding & testing | Free test workspace | Local Docker |
| **Staging** | Integration testing | Separate free workspace | Cloud (isolated) |
| **Production** | Real customers | Customer workspaces | Cloud (production) |

### Development Workspace Setup

```bash
# 1. Create free Slack workspace (takes 2 minutes)
# Visit: https://slack.com/create

# 2. Create Slack App
# Visit: https://api.slack.com/apps
# Click "Create New App" → "From scratch"

# 3. Install app to test workspace
# Go to "Install App" → "Install to Workspace"
```

### Socket Mode for Local Development

Socket Mode allows local testing without a public URL:

```bash
# 1. Enable Socket Mode in Slack App settings
# Settings → Socket Mode → Enable

# 2. Generate App-Level Token
# Settings → Basic Information → App-Level Tokens
# Create token with connections:write scope

# 3. Use in code
SLACK_APP_TOKEN=xapp-1-... # App-level token
SLACK_BOT_TOKEN=xoxb-...   # Bot token
```

## Testing Pyramid

```
                    ┌───────────┐
                    │    E2E    │  ← Real Slack workspace
                    │  Testing  │    (5-10% of tests)
                  ┌─┴───────────┴─┐
                  │  Integration  │  ← Mocked Slack, real LLM
                  │    Testing    │    (20-30% of tests)
                ┌─┴───────────────┴─┐
                │    Unit Testing    │  ← Pure functions, DB
                │                    │    (60-70% of tests)
                └────────────────────┘
```

## Unit Testing

### Framework: pytest

```python
# tests/unit/test_keywords.py
from src.utils.keywords import detect_high_risk_keywords


def test_detects_contract_keyword():
    result = detect_high_risk_keywords("이 계약 조건 괜찮을까요?")
    assert result["is_high_risk"] is True
    assert "계약" in result["keywords"]


def test_returns_false_for_normal_questions():
    result = detect_high_risk_keywords("다음 미팅 언제죠?")
    assert result["is_high_risk"] is False
```

### What to Unit Test

- Keyword detection logic
- Message formatting utilities
- Rule matching logic
- Database query builders
- Embedding chunking logic

## Integration Testing

### Mocking Slack API

```python
# tests/fixtures/mock_slack.py
from unittest.mock import AsyncMock


def create_mock_slack_client():
    client = AsyncMock()

    client.chat_postMessage.return_value = {"ok": True, "ts": "123.456"}
    client.chat_update.return_value = {"ok": True}

    client.conversations_list.return_value = {
        "ok": True,
        "channels": [{"id": "C123", "name": "general"}],
    }
    client.conversations_history.return_value = {
        "ok": True,
        "messages": [{"text": "Hello", "user": "U123", "ts": "123.456"}],
    }

    client.users_info.return_value = {
        "ok": True,
        "user": {"id": "U123", "name": "testuser"},
    }

    return client
```

### Testing with Real LLM

```python
# tests/integration/test_llm.py
import pytest
from src.services.ai.generation import generate_answer


@pytest.mark.asyncio
async def test_generates_answer_in_korean():
    context = [{"content": "CEO는 버그 수정을 신규 기능보다 우선시합니다."}]
    question = "신규 기능이랑 버그 수정 중에 뭐 먼저 할까요?"

    answer = await generate_answer(question, context)

    assert answer
    assert len(answer) > 10
    # Check it contains Korean characters
    import re
    assert re.search(r"[가-힣]", answer)
```

## E2E Testing

### Manual E2E Test Checklist

```markdown
## Onboarding Flow
- [ ] CEO can install bot via OAuth
- [ ] Bot requests correct permissions
- [ ] Data ingestion starts after install
- [ ] Welcome message sent to CEO after completion

## Q&A Flow
- [ ] Employee can send DM to bot
- [ ] Bot responds within 10 seconds
- [ ] Response includes disclaimer
- [ ] Response includes [검토 요청] button

## Feedback Flow
- [ ] [검토 요청] button works
- [ ] CEO receives notification
- [ ] [✅ 문제 없음] sends confirmation to employee
- [ ] [❌ 틀림] sends rejection message
- [ ] [✏️ 직접 수정] opens modal
- [ ] Corrected answer delivered to employee
- [ ] [⚠️ 판단 시 주의 필요] sends caution message

## Rule System
- [ ] /rule add works
- [ ] /rule list shows rules
- [ ] /rule delete removes rule
- [ ] Rules are applied in answer generation

## Safety
- [ ] High-risk keywords trigger warning
- [ ] Disclaimer always present

## Weekly Reminder
- [ ] Report generates correctly
- [ ] Sent at scheduled time
- [ ] Stats are accurate
```

### Automated E2E with Playwright (Optional)

```python
# tests/e2e/test_slack_web.py
# Note: Requires Slack web client automation - complex setup

import pytest
from playwright.async_api import async_playwright


@pytest.mark.asyncio
async def test_employee_can_ask_question_via_dm():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Login to Slack web
        await page.goto("https://your-workspace.slack.com")
        # ... login steps

        # Open bot DM
        await page.click("text=Slough.ai")

        # Send message
        await page.fill('[data-qa="message_input"]', "버그 수정 먼저 할까요?")
        await page.press('[data-qa="message_input"]', "Enter")

        # Wait for response
        await page.wait_for_selector(
            "text=AI가 생성한 응답입니다", timeout=15000
        )

        await browser.close()
```

## Test Data

### Seed Data for Testing

```python
# tests/fixtures/seed_data.py

mock_ceo_messages = [
    {
        "text": "버그 수정은 항상 신규 기능보다 우선입니다. 고객 불만이 쌓이면 안 됩니다.",
        "channel": "C123",
        "ts": "1704067200.000001",
    },
    {
        "text": "100만원 이상 지출은 반드시 저한테 확인 받으세요.",
        "channel": "C123",
        "ts": "1704067200.000002",
    },
    # ... more messages
]

mock_questions = [
    "신규 기능 A랑 버그 수정 B 중에 뭐 먼저?",
    "300만원짜리 장비 구매해도 될까요?",
    "이 계약 조건 괜찮을까요?",
]
```

## Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit

# Integration tests only
pytest tests/integration

# With coverage
pytest --cov=src --cov-report=html

# Watch mode (requires pytest-watch)
ptw

# Verbose output
pytest -v
```

## CI/CD Testing

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: slough_test
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - run: pip install -r requirements.txt
      - run: pytest tests/unit

      - name: Integration tests
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/slough_test
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: pytest tests/integration
```

## Performance Testing

### Response Time Benchmarks

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Message receipt → Processing start | < 500ms | Slack event latency |
| RAG retrieval | < 1s | Vector search time |
| LLM generation | < 8s | OpenAI API response |
| Total response time | < 10s | End-to-end |

### Load Testing (Future)

```python
# Simple load test with locust
# locustfile.py
from locust import HttpUser, task, between


class SlackEventUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def send_message_event(self):
        self.client.post("/slack/events", json={
            # ... event payload
        })
```

## Debugging Tips

### Enable Verbose Logging

```bash
# Development
LOG_LEVEL=DEBUG python src/app.py
```

### Slack Event Inspection

```python
# Add middleware to log all events
@app.middleware
async def log_events(logger, body, next):
    import json
    logger.debug(f"Event received: {json.dumps(body, indent=2, ensure_ascii=False)}")
    await next()
```

### Test LLM Prompts Independently

```python
# scripts/test_prompt.py
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Test prompt here..."}],
)

print(response.choices[0].message.content)
```
