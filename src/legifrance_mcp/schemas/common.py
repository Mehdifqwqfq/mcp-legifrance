"""Shared pydantic schemas + response format enum + ms→ISO helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict


class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"


class StrictBase(BaseModel):
    """Reject unknown fields — early failure beats silently dropping params."""

    model_config = ConfigDict(extra="forbid")


def ms_to_iso(ms: int | float | None) -> str | None:
    """Convert a Légifrance timestamp (Unix ms, UTC) to ISO ``YYYY-MM-DD``.

    Légifrance returns ``9223372036854775807`` (Long.MAX_VALUE) for "no end
    date" — collapse it to None so downstream Markdown stays clean.
    """
    if ms is None:
        return None
    try:
        n = int(ms)
    except (TypeError, ValueError):
        return None
    if n <= 0 or n >= 9_000_000_000_000:  # ~year 2255, sentinel
        return None
    return datetime.fromtimestamp(n / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
