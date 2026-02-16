"""Slack conversation helpers — channel listing and message history fetching."""

import logging
import time

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)

# Slack API rate limit: ~50 req/min for conversations.history (Tier 3)
# We add a small delay between paginated calls to stay safe.
_PAGE_DELAY_SECONDS = 0.5


def join_channel(client: WebClient, channel_id: str) -> bool:
    """Join a public channel. Returns True if successful or already joined."""
    try:
        client.conversations_join(channel=channel_id)
        logger.info("Bot joined channel %s", channel_id)
        return True
    except SlackApiError as e:
        if e.response.get("error") == "already_in_channel":
            return True
        logger.exception("Failed to join channel %s", channel_id)
        return False


def list_bot_channels(client: WebClient) -> list[dict]:
    """List all public channels the bot has been added to.

    Returns:
        List of {"id": str, "name": str} dicts.
    """
    channels = []
    cursor = None

    while True:
        try:
            resp = client.conversations_list(
                types="public_channel",
                exclude_archived=True,
                limit=200,
                cursor=cursor or "",
            )
        except SlackApiError:
            logger.exception("Failed to list channels")
            break

        for ch in resp.get("channels", []):
            if ch.get("is_member"):
                channels.append({"id": ch["id"], "name": ch["name"]})

        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(_PAGE_DELAY_SECONDS)

    logger.info("Found %d channels bot is a member of", len(channels))
    return channels


def fetch_channel_history(
    client: WebClient,
    channel_id: str,
    decision_maker_id: str,
    oldest: float = 0,
    limit_per_page: int = 200,
) -> list[dict]:
    """Fetch all messages from a channel authored by the decision-maker.

    Paginates through the full history (or from `oldest` timestamp).
    Only includes messages with text content from the decision-maker.

    Args:
        client: Slack WebClient with bot token.
        channel_id: Channel to fetch from.
        decision_maker_id: Slack user ID to filter by.
        oldest: Unix timestamp — only fetch messages after this time. 0 = all history.
        limit_per_page: Messages per API call (max 200).

    Returns:
        List of dicts matching the AI contract format:
        [{"text": str, "channel": str, "ts": str, "thread_ts"?: str}]
    """
    messages = []
    cursor = None

    while True:
        try:
            kwargs = {
                "channel": channel_id,
                "limit": limit_per_page,
            }
            if oldest:
                kwargs["oldest"] = str(oldest)
            if cursor:
                kwargs["cursor"] = cursor

            resp = client.conversations_history(**kwargs)
        except SlackApiError as e:
            if e.response.get("error") == "not_in_channel":
                logger.warning("Bot not in channel %s, skipping", channel_id)
                return messages
            logger.exception("Failed to fetch history for channel %s", channel_id)
            break

        for msg in resp.get("messages", []):
            # Only decision-maker's messages with actual text
            if msg.get("user") != decision_maker_id:
                continue
            if not msg.get("text"):
                continue
            # Skip bot messages and system messages
            if msg.get("subtype"):
                continue

            entry = {
                "text": msg["text"],
                "channel": channel_id,
                "ts": msg["ts"],
            }
            if msg.get("thread_ts") and msg["thread_ts"] != msg["ts"]:
                entry["thread_ts"] = msg["thread_ts"]
            messages.append(entry)

        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(_PAGE_DELAY_SECONDS)

    logger.info(
        "Fetched %d decision-maker messages from channel %s",
        len(messages), channel_id,
    )
    return messages


def fetch_all_workspace_history(
    client: WebClient,
    decision_maker_id: str,
    oldest: float = 0,
) -> tuple[list[dict], int]:
    """Fetch decision-maker messages from all channels the bot is in.

    Args:
        client: Slack WebClient with bot token.
        decision_maker_id: Slack user ID of the decision-maker.
        oldest: Unix timestamp — only fetch messages after this time.

    Returns:
        (messages, channels_processed) — messages in AI contract format, channel count.
    """
    channels = list_bot_channels(client)
    all_messages = []

    for ch in channels:
        logger.info("Fetching history from #%s (%s)", ch["name"], ch["id"])
        msgs = fetch_channel_history(
            client,
            channel_id=ch["id"],
            decision_maker_id=decision_maker_id,
            oldest=oldest,
        )
        all_messages.extend(msgs)

    logger.info(
        "Total: %d decision-maker messages from %d channels",
        len(all_messages), len(channels),
    )
    return all_messages, len(channels)
