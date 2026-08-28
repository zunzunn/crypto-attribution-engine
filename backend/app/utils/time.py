"""Timezone helpers that keep datetimes consistent across the app.

Policy: the canonical Pydantic schema carries timezone-aware datetimes;
the ORM columns store true UTC (naive) to behave identically on PostgreSQL
and SQLite.
"""

from __future__ import annotations

from datetime import datetime, timezone


def as_aware_utc(dt: datetime | None) -> datetime | None:
    """Return the datetime normalized to timezone-aware UTC (``tzinfo`` set)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def as_naive_utc(dt: datetime | None) -> datetime | None:
    """Return the datetime as naive UTC (strip tzinfo) for storage."""
    if dt is None:
        return None
    aware = dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
    return aware.astimezone(timezone.utc).replace(tzinfo=None)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)