"""Shared pytest fixtures + E2E gating."""

from __future__ import annotations

import os

import pytest


def pytest_collection_modifyitems(config, items):
    """Skip E2E tests unless LEGIFRANCE_E2E=1 — live tests hit api.piste.gouv.fr."""
    if os.environ.get("LEGIFRANCE_E2E") == "1":
        return
    skip = pytest.mark.skip(
        reason="set LEGIFRANCE_E2E=1 + PISTE_CLIENT_ID/SECRET to run live PISTE tests"
    )
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip)
