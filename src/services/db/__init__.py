"""Database service — re-export session helper for convenience."""

from src.services.db.connection import get_db

__all__ = ["get_db"]
