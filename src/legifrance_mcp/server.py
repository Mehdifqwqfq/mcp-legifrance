"""FastMCP server entry point — wires settings, client, and tools."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from legifrance_mcp.client.http import LegifranceClient
from legifrance_mcp.config import Settings
from legifrance_mcp.logging_setup import setup_logging
from legifrance_mcp.tools import register_all

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Initialise settings + HTTP client; tear down on shutdown."""
    settings = Settings()  # type: ignore[call-arg]
    setup_logging(settings.log_level)
    logger.info(
        "legifrance_mcp starting up (base=%s)",
        settings.legifrance_base_url,
    )

    async with LegifranceClient(settings) as client:
        try:
            yield {"client": client, "settings": settings}
        finally:
            logger.info("legifrance_mcp shutting down")


mcp = FastMCP("legifrance_mcp", lifespan=lifespan)
register_all(mcp)


def main() -> None:
    """Entry point used by `python -m legifrance_mcp` and the console script."""
    mcp.run()


if __name__ == "__main__":
    main()
