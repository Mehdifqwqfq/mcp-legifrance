"""PISTE OAuth2 client_credentials — in-memory token cache with auto refresh."""

from __future__ import annotations

import asyncio
import logging
import time

import httpx

from legifrance_mcp.client.errors import LegifranceAuthError, LegifranceError
from legifrance_mcp.config import Settings

logger = logging.getLogger(__name__)

# Refresh slightly before expiry to avoid racing the server clock.
_REFRESH_MARGIN_S = 60.0


class PisteTokenProvider:
    """Async-safe token cache for the PISTE OAuth2 client_credentials flow.

    PISTE returns an opaque access_token with ``expires_in`` (typically 3600s).
    We cache it in memory and refresh on demand — single in-flight refresh
    guaranteed by ``self._refresh_lock``.
    """

    def __init__(self, settings: Settings, http_client: httpx.AsyncClient):
        self._settings = settings
        self._http = http_client
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._refresh_lock = asyncio.Lock()

    async def get_token(self, *, force_refresh: bool = False) -> str:
        """Return a valid bearer token, refreshing if expired or forced."""
        now = time.monotonic()
        if (
            not force_refresh
            and self._token is not None
            and now < self._expires_at - _REFRESH_MARGIN_S
        ):
            return self._token

        async with self._refresh_lock:
            now = time.monotonic()
            if (
                not force_refresh
                and self._token is not None
                and now < self._expires_at - _REFRESH_MARGIN_S
            ):
                return self._token
            await self._refresh()
            assert self._token is not None
            return self._token

    async def _refresh(self) -> None:
        logger.info("PISTE OAuth → refreshing token (scope=%s)", self._settings.piste_token_scope)
        data = {
            "grant_type": "client_credentials",
            "client_id": self._settings.piste_client_id,
            "client_secret": self._settings.piste_client_secret,
            "scope": self._settings.piste_token_scope,
        }
        start = time.monotonic()
        try:
            response = await self._http.post(
                self._settings.piste_token_url,
                data=data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "User-Agent": self._settings.user_agent,
                },
            )
        except httpx.HTTPError as exc:
            raise LegifranceError(
                f"Échec réseau auth PISTE: {exc}",
                url=self._settings.piste_token_url,
            ) from exc

        if response.status_code != 200:
            raise LegifranceAuthError(
                "PISTE refuse l'authentification.",
                status_code=response.status_code,
                url=self._settings.piste_token_url,
                body=response.text,
            )

        payload = response.json()
        token = payload.get("access_token")
        expires_in = float(payload.get("expires_in", 3600))
        if not token:
            raise LegifranceAuthError(
                "Réponse PISTE sans access_token.",
                status_code=response.status_code,
                url=self._settings.piste_token_url,
                body=response.text,
            )

        self._token = token
        self._expires_at = time.monotonic() + expires_in
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "PISTE token OK (%dms, expires_in=%ds, scope=%s)",
            elapsed_ms,
            int(expires_in),
            payload.get("scope", "?"),
        )
