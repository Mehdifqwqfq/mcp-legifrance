"""Tool: get_jorf — POST /consult/jorf (texte du Journal Officiel)."""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context
from pydantic import Field

from legifrance_mcp.client.errors import LegifranceError, format_error_for_agent
from legifrance_mcp.schemas.common import ResponseFormat, StrictBase, ms_to_iso

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]+")


def _clean(text: str | None) -> str:
    if not text:
        return ""
    text = _TAG_RE.sub(" ", text)
    text = text.replace("&nbsp;", " ").replace("&#13;", "")
    text = _WS_RE.sub(" ", text)
    return " ".join(line.strip() for line in text.splitlines() if line.strip())

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from legifrance_mcp.client.http import LegifranceClient

logger = logging.getLogger(__name__)


class GetJorfInput(StrictBase):
    text_cid: str = Field(
        ...,
        description=(
            "CID du texte JORF (JORFTEXT…). Ex: 'JORFTEXT000053618939' = "
            "Décret n° 2026-156 du 3 mars 2026 modifiant le code de déontologie des pharmaciens."
        ),
        examples=["JORFTEXT000053618939"],
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="get_jorf",
        annotations={
            "title": "Texte JORF (décret, arrêté, loi) par CID",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def get_jorf(params: GetJorfInput, ctx: Context) -> str:
        """Récupère un texte publié au Journal Officiel par son CID JORFTEXT.

        Renvoie : titre, nature (décret/arrêté/loi/…), N° NOR, date du texte,
        état de vigueur, signataires, et la liste des sections (avec articles
        cibles si dérefencés par l'API).
        """
        client: LegifranceClient = ctx.request_context.lifespan_context["client"]
        body = {"textCid": params.text_cid}
        try:
            data = await client.post_json("/consult/jorf", body)
        except LegifranceError as exc:
            return format_error_for_agent(exc)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2, ensure_ascii=False)

        return _format_md(data)


def _format_md(data: dict) -> str:
    title = data.get("title") or "(texte JORF sans titre)"
    nature = data.get("nature") or "?"
    nor = data.get("nor") or "—"
    text_num = data.get("textNumber") or "—"
    etat = data.get("etat") or "?"
    date_texte = ms_to_iso(data.get("dateTexte")) or "?"
    date_pub = ms_to_iso(data.get("dateParution")) or "?"
    signers = _clean(data.get("signers"))

    lines = [
        f"### {title}",
        f"**Nature** : {nature} · **NOR** : {nor} · **N° texte** : {text_num}",
        f"**Date du texte** : {date_texte} · **Parution JORF** : {date_pub}",
        f"**État** : {etat}",
    ]
    if signers:
        lines.append(f"**Signataires** : {signers}")

    sections = data.get("sections") or []
    if sections:
        lines.append("")
        lines.append(f"#### Sections ({len(sections)})")
        for s in sections[:30]:
            s_title = s.get("title") or s.get("titre") or "(section)"
            s_cid = s.get("cid") or s.get("id") or ""
            lines.append(f"- {s_title} `{s_cid}`")

    return "\n".join(lines)
