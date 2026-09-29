"""Tool: get_article — POST /consult/getArticle."""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context
from pydantic import Field

from legifrance_mcp.client.errors import LegifranceError, format_error_for_agent
from legifrance_mcp.schemas.common import ResponseFormat, StrictBase, ms_to_iso

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from legifrance_mcp.client.http import LegifranceClient

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str | None) -> str:
    if not text:
        return ""
    return _TAG_RE.sub("", text).replace("&nbsp;", " ").replace("&#13;", "\n").strip()


class GetArticleInput(StrictBase):
    article_id: str = Field(
        ...,
        description=("Identifiant article (LEGIARTI…). Ex: 'LEGIARTI000006913651' = R.4235-1 CSP."),
        examples=["LEGIARTI000006913651"],
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="get_article",
        annotations={
            "title": "Article unique Légifrance par identifiant",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def get_article(params: GetArticleInput, ctx: Context) -> str:
        """Renvoie le verbatim d'un article par son identifiant LEGIARTI.

        Inclut le numéro (ex: R.4235-1), le texte intégral nettoyé du HTML,
        la période de vigueur et le NOTA s'il y en a.
        """
        client: LegifranceClient = ctx.request_context.lifespan_context["client"]
        body = {"id": params.article_id}
        try:
            data = await client.post_json("/consult/getArticle", body)
        except LegifranceError as exc:
            return format_error_for_agent(exc)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2, ensure_ascii=False)

        return _format_md(data)


def _format_md(data: dict) -> str:
    art = data.get("article") or {}
    if not art:
        return "_(article introuvable)_"
    lines = format_article_lines(art)
    if data.get("dereferenced"):
        lines.insert(1, "⚠️ L'API signale cet article comme **déréférencé** (`dereferenced: true`).")
    return "\n".join(lines)


def format_article_lines(art: dict) -> list[str]:
    """Rendu Markdown commun à ``get_article`` et ``get_article_by_num``.

    ``id`` = la VERSION précise de l'article (change à chaque modification) ;
    ``cid`` = l'identifiant de sa 1re version, stable dans le temps. Les deux
    sont affichés : n'afficher que le CID laissait croire que l'id demandé
    avait été remplacé.
    """
    num = art.get("num") or "?"
    version_id = art.get("id") or "?"
    cid = art.get("cid") or version_id
    etat = art.get("etat") or "?"
    start = ms_to_iso(art.get("dateDebut")) or "?"
    end = ms_to_iso(art.get("dateFin")) or "—"
    texte = _strip_html(art.get("texte"))
    nota = _strip_html(art.get("nota"))

    lines = [
        f"### Article {num}",
        f"**Id version** : `{version_id}` · **CID** : `{cid}`",
        f"**État** : {etat} · **Période** : {start} → {end}",
        "",
        texte or "_(texte vide)_",
    ]
    if nota:
        lines += ["", "**NOTA**", nota]
    return lines
