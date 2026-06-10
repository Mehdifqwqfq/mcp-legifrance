"""MCP tool registration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register_all(mcp: FastMCP) -> None:
    """Register every tool module on the given FastMCP instance."""
    from legifrance_mcp.tools import (  # noqa: PLC0415
        get_article,
        get_code_toc,
        get_jorf,
        get_section,
        loda,
        search,
    )

    search.register(mcp)
    get_code_toc.register(mcp)
    get_section.register(mcp)
    get_article.register(mcp)
    get_jorf.register(mcp)
    loda.register(mcp)
