# Slack API Reference for Slough.ai

## Required OAuth Scopes

### User Token Scopes (Decision-maker grants during install)

These scopes allow the bot to access the decision-maker's data for learning:

| Scope | Purpose |
|-------|---------|
| `channels:history` | Read messages in public channels decision-maker is in |
| `channels:read` | List public channels decision-maker has access to |
| `groups:history` | Read messages in private channels decision-maker is in |
| `groups:read` | List private channels decision-maker has access to |
| `im:history` | Read decision-maker's direct messages |
| `im:read` | List decision-maker's DM conversations |
| `mpim:history` | Read group DMs decision-maker is in |
| `users:read` | Get user info for context |

### Bot Token Scopes

These scopes allow the bot to interact with users:

| Scope | Purpose |
|-------|---------|
| `chat:write` | Send messages to users |
| `im:history` | Read messages in bot DMs |
| `im:read` | Access bot DM list |
| `im:write` | Open DM channels with users |
| `commands` | Handle slash commands |
| `users:read` | Get user information |

## Slack Events

### Events to Subscribe

| Event | Trigger | Usage |
|-------|---------|-------|
| `message.im` | User sends DM to bot | Handle employee questions |

### Event Payload Example

```python
# message.im event
{
    "type": "message",
    "channel": "D1234567890",       # DM channel ID
    "user": "U1234567890",          # User who sent message
    "text": "버그 수정 먼저 할까요?",
    "ts": "1234567890.123456",
    "channel_type": "im",
    "event_ts": "1234567890.123456"
}
```

## API Methods Used

### conversations.list

List all conversations the user has access to.

```python
result = client.conversations_list(
    token=user_token,  # decision-maker's user token
    types="public_channel,private_channel,im,mpim",
    limit=200,
    cursor=next_cursor  # For pagination
)

# Response
{
    "channels": [
        {
            "id": "C1234567890",
            "name": "general",
            "is_channel": True,
            "is_member": True
        }
    ],
    "response_metadata": {
        "next_cursor": "dXNlcjpVMDYxTkZUVDI="
    }
}
```

### conversations.history

Fetch message history from a channel.

```python
result = client.conversations_history(
    token=user_token,
    channel=channel_id,
    limit=200,
    cursor=next_cursor,
    oldest="0",       # From beginning
    inclusive=True
)

# Response
{
    "messages": [
        {
            "type": "message",
            "user": "U1234567890",
            "text": "버그 수정을 먼저 하세요",
            "ts": "1234567890.123456",
            "thread_ts": "1234567890.123456"  # If in thread
        }
    ],
    "has_more": True,
    "response_metadata": {
        "next_cursor": "bmV4dF90czoxMjM0NTY3ODkw"
    }
}
```

### conversations.replies

Fetch thread replies.

```python
result = client.conversations_replies(
    token=user_token,
    channel=channel_id,
    ts=thread_ts,
    limit=200
)
```

### chat.postMessage

Send a message to a user or channel.

```python
result = client.chat_postMessage(
    token=bot_token,
    channel=user_id,       # User ID for DM
    text="Fallback text",
    blocks=[
        # Block Kit blocks
    ]
)

# Response
{
    "ok": True,
    "channel": "D1234567890",
    "ts": "1234567890.123456",
    "message": { ... }
}
```

### chat.update

Update an existing message.

```python
result = client.chat_update(
    token=bot_token,
    channel=channel_id,
    ts=message_ts,
    text="Updated text",
    blocks=[...]
)
```

### users.info

Get user information.

```python
result = client.users_info(
    token=bot_token,
    user=user_id
)

# Response
{
    "user": {
        "id": "U1234567890",
        "name": "johndoe",
        "real_name": "John Doe",
        "profile": {
            "display_name": "John"
        }
    }
}
```

### views.open

Open a modal for user input.

```python
result = client.views_open(
    token=bot_token,
    trigger_id=trigger_id,  # From interaction payload
    view={
        "type": "modal",
        "callback_id": "edit_answer_modal",
        "title": {"type": "plain_text", "text": "답변 수정"},
        "submit": {"type": "plain_text", "text": "저장"},
        "blocks": [...]
    }
)
```

## Block Kit Components

### Answer Message Structure

```python
import json

answer_blocks = [
    # Answer text
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "버그 수정 B를 먼저 진행하세요.\n\n이유:\n1. 현재 고객 불만이 접수된 상태입니다.\n2. 신규 기능은 다음 스프린트에 포함해도 일정에 문제 없습니다."
        }
    },

    # Divider
    {"type": "divider"},

    # Disclaimer
    {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "⚠️ AI가 생성한 응답입니다. 오류가 있을 수 있습니다."
            }
        ]
    },

    # Review request button
    {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "🔍 검토 요청", "emoji": True},
                "action_id": "request_review",
                "value": json.dumps({"questionId": "Q123", "messageTs": "123.456"})
            }
        ]
    }
]
```

### Decision-Maker Review Request Message

```python
review_request_blocks = [
    # Header
    {
        "type": "header",
        "text": {"type": "plain_text", "text": "🔔 검토 요청", "emoji": True}
    },

    # Requester info
    {
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": "<@U1234567890>님이 검토를 요청했습니다"}
        ]
    },

    # Original question
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*❓ 질문:*\n신규 기능 A와 버그 수정 B 중에 뭘 먼저 해야 할까요?"
        }
    },

    # AI answer
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": '*🤖 AI 응답:*\n"버그 수정 B를 먼저 진행하세요. 이유: 1. 현재 고객 불만이 접수된 상태..."'
        }
    },

    # Feedback buttons
    {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "✅ 문제 없음", "emoji": True},
                "style": "primary",
                "action_id": "feedback_approved",
                "value": "Q123"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "❌ 틀림", "emoji": True},
                "style": "danger",
                "action_id": "feedback_rejected",
                "value": "Q123"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "✏️ 직접 수정", "emoji": True},
                "action_id": "feedback_edit",
                "value": "Q123"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "⚠️ 판단 시 주의 필요", "emoji": True},
                "action_id": "feedback_caution",
                "value": "Q123"
            }
        ]
    }
]
```

### Edit Answer Modal

```python
import json

edit_modal = {
    "type": "modal",
    "callback_id": "edit_answer_submit",
    "private_metadata": json.dumps({"questionId": "Q123", "askerId": "U123"}),
    "title": {"type": "plain_text", "text": "답변 수정"},
    "submit": {"type": "plain_text", "text": "저장"},
    "close": {"type": "plain_text", "text": "취소"},
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*원본 질문:*\n신규 기능 A와 버그 수정 B 중에 뭘 먼저 해야 할까요?"
            }
        },
        {
            "type": "input",
            "block_id": "corrected_answer_block",
            "element": {
                "type": "plain_text_input",
                "action_id": "corrected_answer_input",
                "multiline": True,
                "initial_value": "버그 수정 B를 먼저 진행하세요..."
            },
            "label": {"type": "plain_text", "text": "수정된 답변"}
        }
    ]
}
```

## Slash Command Handling

### /rule Command

```python
import re

@app.command("/rule")
async def handle_rule_command(ack, command, respond, client):
    await ack()

    text = command["text"].strip()
    parts = text.split(" ", 1)
    action = parts[0] if parts else ""
    args = parts[1] if len(parts) > 1 else ""

    if action == "add":
        # Parse rule content (remove quotes)
        rule_content = re.sub(r'^"(.*)"$', r"\1", args)
        # Save to database
        await save_rule(command["team_id"], command["user_id"], rule_content)
        await respond(text=f'✅ 법칙이 추가되었습니다: "{rule_content}"')

    elif action == "list":
        rules = await get_rules(command["team_id"])
        rule_text = "\n".join(
            f'[ID: {r["id"]}]: "{r["rule_text"]}"' for r in rules
        )
        await respond(
            text=(
                f"📜 현재 적용 중인 법칙 목록입니다.\n\n{rule_text}\n\n"
                "(삭제하시려면 /rule delete [ID]를 입력하세요)"
            )
        )

    elif action == "delete":
        rule_id = int(args)
        await delete_rule(command["team_id"], rule_id)
        await respond(text=f"✅ 법칙 ID {rule_id}이(가) 삭제되었습니다.")

    else:
        await respond(
            text='사용법:\n• /rule add "법칙 내용"\n• /rule list\n• /rule delete [ID]'
        )
```

## Rate Limits

### Important Limits

| API Method | Tier | Limit |
|------------|------|-------|
| chat.postMessage | Tier 3 | 50+ per minute |
| conversations.history | Tier 3 | 50+ per minute |
| conversations.list | Tier 2 | 20+ per minute |
| users.info | Tier 4 | 100+ per minute |

### Handling Rate Limits

```python
from slack_sdk import WebClient
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler

client = WebClient(token=token)

# Add the built-in rate limit retry handler
rate_limit_handler = RateLimitErrorRetryHandler(max_retry_count=3)
client.retry_handlers.append(rate_limit_handler)
```

## Error Handling

### Common Error Codes

| Error | Cause | Solution |
|-------|-------|----------|
| `invalid_auth` | Bad token | Check token is correct |
| `channel_not_found` | Invalid channel ID | Verify channel exists |
| `not_in_channel` | Bot not in channel | Invite bot to channel |
| `ratelimited` | Too many requests | Implement backoff |
| `user_not_found` | Invalid user ID | Verify user exists |

### Error Handler Pattern

```python
from slack_bolt import App
from slack_sdk.errors import SlackApiError

app = App(token=bot_token, signing_secret=signing_secret)

@app.error
async def global_error_handler(error, body, logger):
    if isinstance(error, SlackApiError):
        logger.error(f"Slack API error: {error.response['error']}")
        # Handle specific error codes
        if error.response["error"] == "ratelimited":
            # Wait and retry
            pass
    else:
        logger.error(f"Unexpected error: {error}")
```

## Webhook Signature Verification

When using HTTP mode (not Socket Mode):

```python
from slack_bolt import App
import os

# Bolt for Python handles signature verification automatically
# when you provide the signing secret
app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"]
)

# All incoming requests are verified against the signing secret
# before being dispatched to handlers. No additional setup needed.
```

## OAuth Flow Implementation

```python
import os
from slack_bolt import App
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore

app = App(
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    oauth_settings=OAuthSettings(
        client_id=os.environ["SLACK_CLIENT_ID"],
        client_secret=os.environ["SLACK_CLIENT_SECRET"],
        scopes=[
            "chat:write", "im:history", "im:read",
            "im:write", "commands", "users:read"
        ],
        user_scopes=[
            "channels:history", "channels:read",
            "groups:history", "groups:read",
            "im:history", "im:read", "mpim:history",
            "users:read"
        ],
        installation_store=FileInstallationStore(),
        state_store=FileOAuthStateStore(expiration_seconds=600),
    )
)

# For custom post-install logic, use the callback
from slack_bolt.oauth.callback_options import CallbackOptions, SuccessArgs, FailureArgs
from slack_bolt.response import BoltResponse


async def success_callback(success_args: SuccessArgs) -> BoltResponse:
    installation = success_args.installation
    # Save tokens to database
    await save_workspace(
        team_id=installation.team_id,
        team_name=installation.team_name,
        bot_token=installation.bot_token,
        user_token=installation.user_token,
        ceo_user_id=installation.user_id,
    )
    return BoltResponse(status=302, headers={"Location": "/install-success"})


async def failure_callback(failure_args: FailureArgs) -> BoltResponse:
    return BoltResponse(
        status=failure_args.suggested_status_code,
        body=failure_args.reason,
    )
```

## Useful Resources

- [Slack Bolt for Python Documentation](https://slack.dev/bolt-python/concepts)
- [Slack SDK for Python (slack_sdk)](https://slack.dev/python-slack-sdk/)
- [Slack API Methods](https://api.slack.com/methods)
- [Block Kit Builder](https://app.slack.com/block-kit-builder)
- [Slack Events API](https://api.slack.com/events-api)
- [OAuth Flow Guide](https://api.slack.com/authentication/oauth-v2)
