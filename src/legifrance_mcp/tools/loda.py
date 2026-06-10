"""Tool: consult_loda — POST /consult/lawDecree (texte LODA consolidé)."""

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


class ConsultLodaInput(StrictBase):
    text_id: str = Field(
        ...,
        description=(
            "Identifiant LEGITEXT du texte LODA (loi/décret/arrêté consolidé). "
            "Note : ``/consult/lawDecree`` exige un LEGITEXT (pas un JORFTEXT)."
        ),
        examples=["LEGITEXT000025056888"],
    )
    date: str | None = Field(
        default=None,
        description="Date d'application YYYY-MM-DD (obligatoire côté API — défaut : aujourd'hui).",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="consult_loda",
        annotations={
            "title": "Texte LODA consolidé (loi/décret/arrêté hors code)",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def consult_loda(params: ConsultLodaInput, ctx: Context) -> str:
        """Renvoie un texte LODA consolidé à une date donnée.

        L'API attend un LEGITEXT (et non un JORFTEXT). Renvoie titre, nature,
        état, période de vigueur, articles et sections rattachés.
        """
        client: LegifranceClient = ctx.request_context.lifespan_context["client"]
        iso = params.date or date.today().isoformat()
        body = {"textId": params.text_id, "date": iso}
        try:
            data = await client.post_json("/consult/lawDecree", body)
        except LegifranceError as exc:
            return format_error_for_agent(exc)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2, ensure_ascii=False)

        return _format_md(data, date_iso=iso)


def _format_md(data: dict, *, date_iso: str) -> str:
    title = data.get("title") or "(texte LODA sans titre)"
    nature = data.get("nature") or "?"
    etat = data.get("etat") or "?"
    nor = data.get("nor") or "—"
    text_num = data.get("textNumber") or "—"
    start = ms_to_iso(data.get("dateDebutVersion")) or "?"
    end = ms_to_iso(data.get("dateFinVersion")) or "—"

    lines = [
        f"### {title}",
        f"**Nature** : {nature} · **NOR** : {nor} · **N° texte** : {text_num}",
        f"**État** : {etat} · **Version** : {start} → {end}",
        f"**Date interrogée** : {date_iso}",
    ]

    sections = data.get("sections") or []
    articles = data.get("articles") or []
    if articles:
        lines += ["", f"#### Articles rattachés au texte ({len(articles)})"]
        for a in articles[:30]:
            num = a.get("num") or "?"
            a_id = a.get("id") or a.get("cid") or "?"
            lines.append(f"- **Art. {num}** · `{a_id}`")
    if sections:
        lines += ["", f"#### Sections ({len(sections)})"]
        for s in sections[:30]:
            s_title = s.get("title") or s.get("titre") or "(section)"
            s_cid = s.get("cid") or s.get("id") or ""
            lines.append(f"- {s_title} `{s_cid}`")

    return "\n".join(lines)
