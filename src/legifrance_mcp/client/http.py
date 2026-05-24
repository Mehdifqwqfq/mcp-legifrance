"""Async HTTP client for Légifrance via PISTE — OAuth2 bearer + JSON POST.

All Légifrance endpoints (lf-engine-app/*) are POST with a JSON body.
Token comes from :class:`PisteTokenProvider`; on 401 we refresh once and retry.
"""

from __future__ import annotations

import logging
import time
from types import TracebackType
from typing import Any

import httpx

from legifrance_mcp.client.auth import PisteTokenProvider
from legifrance_mcp.client.errors import (
    LegifranceAuthError,
    LegifranceError,
    LegifranceNotFoundError,
    LegifranceRateLimitError,
)
from legifrance_mcp.config import Settings

logger = logging.getLogger(__name__)


class LegifranceClient:
    """Async client wrapping the Légifrance API (DILA / PISTE)."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._http = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.request_timeout, connect=10.0),
            follow_redirects=False,
        )
        self._tokens = PisteTokenProvider(settings, self._http)

    async def __aenter__(self) -> "LegifranceClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self._http.aclose()

    async def post_json(
        self,
        path: str,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        """POST ``body`` as JSON to ``{base}{path}`` and return the parsed JSON.

        Refreshes the PISTE token once on 401 before failing.
        """
        url = self._settings.legifrance_base_url.rstrip("/") + path
        for attempt in (0, 1):
            token = await self._tokens.get_token(force_refresh=bool(attempt))
            start = time.monotonic()
            logger.info("→ POST %s (attempt %d)", path, attempt + 1)
            try:
                response = await self._http.post(
                    url,
                    json=body,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "User-Agent": self._settings.user_agent,
                    },
                )
            except httpx.HTTPError as exc:
                raise LegifranceError(
                    f"Échec réseau Légifrance: {exc}", url=url
                ) from exc

            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.info("← %d (%dms) %s", response.status_code, elapsed_ms, path)

            if response.status_code == 401 and attempt == 0:
                logger.info("401 — refresh PISTE token et retry")
                continue

            self._raise_for_status(response, url)
            try:
                return response.json()
            except ValueError as exc:
                raise LegifranceError(
                    f"Réponse Légifrance non-JSON: {exc}",
                    status_code=response.status_code,
                    url=url,
                    body=response.text[:500],
                ) from exc

        raise LegifranceAuthError(
            "Auth PISTE échoue après refresh.",
            status_code=401,
            url=url,
        )

    @staticmethod
    def _raise_for_status(response: httpx.Response, url: str) -> None:
        if response.is_success:
            return
        status = response.status_code
        body = response.text[:500]
        if status in (401, 403):
            raise LegifranceAuthError(
                "Auth PISTE refusée.",
                status_code=status,
                url=url,
                body=body,
            )
        if status == 404:
            raise LegifranceNotFoundError(
                "CID/endpoint introuvable.",
                status_code=status,
                url=url,
                body=body,
            )
        if status == 429:
            raise LegifranceRateLimitError(
                "Quota PISTE atteint.",
                status_code=status,
                url=url,
                body=body,
            )
        raise LegifranceError(
            f"Réponse HTTP {status} inattendue.",
            status_code=status,
            url=url,
            body=body,
        )
