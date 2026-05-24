"""Typed exceptions for the Legifrance (PISTE) client."""

from __future__ import annotations


class LegifranceError(Exception):
    """Base error from the Legifrance client."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        url: str | None = None,
        body: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.url = url
        self.body = body


class LegifranceAuthError(LegifranceError):
    """401 / 403 — token expired, scope missing, or app revoked."""


class LegifranceNotFoundError(LegifranceError):
    """404 — endpoint or CID/textId unknown."""


class LegifranceRateLimitError(LegifranceError):
    """429 — PISTE quota hit."""


def format_error_for_agent(exc: LegifranceError) -> str:
    """Render a typed error as an actionable message for the LLM agent."""
    parts = [f"Erreur Légifrance: {exc.message}"]
    if exc.status_code:
        parts.append(f"HTTP {exc.status_code}")
    if exc.url:
        parts.append(f"URL: {exc.url}")
    if isinstance(exc, LegifranceAuthError):
        parts.append(
            "→ Auth PISTE refusée. Vérifier PISTE_CLIENT_ID/SECRET dans "
            "~/.etikpharma-secrets et que l'app PISTE est bien souscrite à "
            "l'API Légifrance v2.4.2."
        )
    elif isinstance(exc, LegifranceNotFoundError):
        parts.append("→ CID/textId inconnu côté Légifrance. Vérifier l'identifiant.")
    elif isinstance(exc, LegifranceRateLimitError):
        parts.append("→ Quota PISTE atteint. Réessayer dans quelques secondes.")
    if exc.body:
        parts.append(f"Body: {exc.body[:300]}")
    return " | ".join(parts)
