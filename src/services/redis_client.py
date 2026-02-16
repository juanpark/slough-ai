"""Redis Multi-DB client manager and cache helpers.

Ported from SloughAI's ``redis_client.py``, adapted for slough-ai's
config and DB access patterns.

DB layout:
  - DB0: Celery Broker (task queue)
  - DB1: Celery Backend (task results)
  - DB2: Dedup keys + Rule cache
"""

import logging
from typing import Optional

import redis

from src.config import settings

logger = logging.getLogger(__name__)


# ── Singleton Manager ─────────────────────────────────────────────────

class RedisManager:
    """Lazy-initialized Redis multi-DB client manager."""

    _broker_client: Optional[redis.Redis] = None
    _backend_client: Optional[redis.Redis] = None
    _cache_client: Optional[redis.Redis] = None

    @classmethod
    def get_broker(cls) -> redis.Redis:
        """DB0: Celery Broker."""
        if cls._broker_client is None:
            cls._broker_client = redis.from_url(
                settings.redis_broker_url,
                decode_responses=True,
            )
        return cls._broker_client

    @classmethod
    def get_backend(cls) -> redis.Redis:
        """DB1: Celery Backend."""
        if cls._backend_client is None:
            cls._backend_client = redis.from_url(
                settings.redis_backend_url,
                decode_responses=True,
            )
        return cls._backend_client

    @classmethod
    def get_cache(cls) -> redis.Redis:
        """DB2: Dedup + Rule Cache."""
        if cls._cache_client is None:
            cls._cache_client = redis.from_url(
                settings.redis_cache_url,
                decode_responses=True,
            )
        return cls._cache_client


# ── Dedup Helper ──────────────────────────────────────────────────────

def is_duplicate_event(event_id: str) -> bool:
    """Check if a Slack event has already been processed.

    Uses Redis SETNX with a TTL to prevent processing the same event twice
    (Slack retries on timeouts).

    Returns:
        True  → duplicate (already seen)
        False → new event
    """
    cache = RedisManager.get_cache()
    key = f"dedup:{event_id}"

    is_new = cache.setnx(key, "1")
    if is_new:
        cache.expire(key, settings.dedup_ttl_seconds)
        return False  # New event

    return True  # Duplicate


# ── Rule Cache Helpers ────────────────────────────────────────────────

def get_cached_rule(keyword: str) -> Optional[str]:
    """Look up a cached rule by keyword."""
    cache = RedisManager.get_cache()
    return cache.get(f"rule:{keyword}")


def set_cached_rule(keyword: str, rule_text: str, ttl: int = 3600) -> None:
    """Cache a rule with a TTL (default 1 hour)."""
    cache = RedisManager.get_cache()
    cache.setex(f"rule:{keyword}", ttl, rule_text)


def get_all_rules() -> dict:
    """Return all cached rules as {keyword: rule_text}."""
    cache = RedisManager.get_cache()
    keys = cache.keys("rule:*")

    rules: dict[str, str] = {}
    for key in keys:
        keyword = key.replace("rule:", "", 1)
        val = cache.get(key)
        if val:
            rules[keyword] = val
    return rules


def sync_rules_from_db() -> int:
    """Sync active rules from PostgreSQL → Redis cache.

    Clears existing rule:* keys and replaces with current DB state.
    Returns the number of rules synced.
    """
    from src.services.db import get_db
    from src.services.db.rules import get_active_rules

    cache = RedisManager.get_cache()

    # Clear existing
    for key in cache.keys("rule:*"):
        cache.delete(key)

    # Fetch from DB and cache
    count = 0
    try:
        with get_db() as db:
            # get_active_rules needs a workspace_id, but for global sync
            # we iterate all workspaces. For now, cache all rules.
            from src.services.db.models import Rule
            from sqlalchemy import select

            rules = db.execute(
                select(Rule).where(Rule.is_active == True)  # noqa: E712
            ).scalars().all()

            for rule in rules:
                cache.set(f"rule:{rule.rule_text[:50]}", rule.rule_text)
                count += 1
    except Exception:
        logger.exception("Failed to sync rules from DB to Redis")

    logger.info("Synced %d rules from DB to Redis", count)
    return count
