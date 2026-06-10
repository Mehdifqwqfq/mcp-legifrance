"""Tool: get_code_toc — POST /consult/code/tableMatieres."""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context
from pydantic import Field

from legifrance_mcp.client.errors import LegifranceError, format_error_for_agent
from legifrance_mcp.schemas.common import ResponseFormat, StrictBase, ms_to_iso

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from legifrance_mcp.client.http import LegifranceClient

logger = logging.getLogger(__name__)


class GetCodeTocInput(StrictBase):
    text_id: str = Field(
        ...,
        description=(
            "Identifiant Légifrance du code (LEGITEXT…). Ex: "
            "'LEGITEXT000006072665' = Code de la santé publique, "
            "'LEGITEXT000006073189' = Code de la sécurité sociale."
        ),
        examples=["LEGITEXT000006072665"],
    )
    date: str | None = Field(
        default=None,
        description="Date d'application YYYY-MM-DD (défaut : aujourd'hui).",
    )
    max_depth: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Profondeur max d'arborescence rendue en markdown (par défaut 3).",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="get_code_toc",
        annotations={
            "title": "Table des matières d'un code consolidé Légifrance",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def get_code_toc(params: GetCodeTocInput, ctx: Context) -> str:
        """Renvoie la table des matières d'un code consolidé (CSP, CSS, CT…).

        Sortie markdown : arborescence Livre / Titre / Chapitre / Section avec
        les CID de section pour pouvoir appeler ``get_section`` ensuite.
        """
        client: LegifranceClient = ctx.request_context.lifespan_context["client"]
        iso = params.date or date.today().isoformat()
        body = {"textId": params.text_id, "date": iso}
        try:
            data = await client.post_json("/consult/code/tableMatieres", body)
        except LegifranceError as exc:
            return format_error_for_agent(exc)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2, ensure_ascii=False)

        return _format_md(data, max_depth=params.max_depth, date_iso=iso)


def _format_md(data: dict, *, max_depth: int, date_iso: str) -> str:
    lines = [
        f"### {data.get('title') or '(code sans titre)'}",
        f"**Date** : {date_iso} · **CID** : `{data.get('cid')}` · "
        f"**NOR** : {data.get('nor') or '—'}",
        "",
    ]
    sections = data.get("sections") or []
    articles = data.get("articles") or []
    if not sections and not articles:
        lines.append("_(table des matières vide à cette date — vérifier text_id)_")
        return "\n".join(lines)

    _render_sections(sections, lines, level=1, max_depth=max_depth)
    if articles:
        lines.append(f"\n_+ {len(articles)} article(s) rattaché(s) directement au texte_")
    return "\n".join(lines)


def _render_sections(
    sections: list[dict],
    lines: list[str],
    *,
    level: int,
    max_depth: int,
) -> None:
    if level > max_depth:
        return
    prefix = "#" * min(level + 3, 6)  # h4, h5, h6
    for s in sections:
        title = s.get("title") or s.get("titre") or "(section)"
        cid = s.get("cid") or s.get("id")
        etat = s.get("etat") or ""
        start = ms_to_iso(s.get("dateDebut")) or ""
        meta = []
        if etat:
            meta.append(etat)
        if start:
            meta.append(f"depuis {start}")
        meta_str = f" _( {' · '.join(meta)} )_" if meta else ""
        lines.append(f"{prefix} {title}{meta_str}")
        if cid:
            lines.append(f"`{cid}`")
        nested = s.get("sections") or []
        nested_articles = s.get("articles") or []
        if nested_articles:
            lines.append(f"_({len(nested_articles)} article(s))_")
        if nested:
            _render_sections(nested, lines, level=level + 1, max_depth=max_depth)
