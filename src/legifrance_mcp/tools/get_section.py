"""Tool: get_section — POST /consult/getSectionByCid."""

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


class GetSectionInput(StrictBase):
    cid: str = Field(
        ...,
        description=(
            "CID Légifrance de la section (LEGISCTA…). Ex: "
            "'LEGISCTA000006178625' = chapitre V (Code de déontologie des pharmaciens)."
        ),
        examples=["LEGISCTA000006178625"],
    )
    text_id: str = Field(
        ...,
        description="LEGITEXT… du code conteneur (ex: 'LEGITEXT000006072665' = CSP).",
        examples=["LEGITEXT000006072665"],
    )
    date: str | None = Field(
        default=None,
        description="Date d'application YYYY-MM-DD (défaut : aujourd'hui).",
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


def register(mcp: "FastMCP") -> None:
    @mcp.tool(
        name="get_section",
        annotations={
            "title": "Section d'un code consolidé Légifrance (sous-sections + articles)",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def get_section(params: GetSectionInput, ctx: Context) -> str:
        """Renvoie une section d'un code à une date donnée.

        ``getSectionByCid`` retourne une **liste de versions** (``listSection``)
        — on garde par défaut la version en VIGUEUR à la date demandée, et on
        liste les autres versions (MODIFIE/ABROGE) en pied de réponse.

        Chaque section contient ses sous-sections (``liensSection``) avec leurs
        CID pour récursion, et ses articles (``liensArticle``) avec leur numéro.
        """
        client: LegifranceClient = ctx.request_context.lifespan_context["client"]
        iso = params.date or date.today().isoformat()
        body = {"cid": params.cid, "textId": params.text_id, "date": iso}
        try:
            data = await client.post_json("/consult/getSectionByCid", body)
        except LegifranceError as exc:
            return format_error_for_agent(exc)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2, ensure_ascii=False)

        return _format_md(data, date_iso=iso)


def _derive_etat(version: dict) -> str:
    """Derive VIGUEUR/MODIFIE from dateFin sentinel when etat is missing.

    Légifrance ne renvoie pas toujours ``etat`` sur les versions de section ;
    quand dateFin = Long.MAX_VALUE (≈ pas de fin), c'est la version en vigueur.
    """
    declared = (version.get("etat") or "").upper()
    if declared:
        return declared
    return "VIGUEUR" if ms_to_iso(version.get("dateFin")) is None else "MODIFIE"


def _format_md(data: dict, *, date_iso: str) -> str:
    versions = data.get("listSection") or []
    if not versions:
        return f"_(aucune section retournée pour la date {date_iso})_"

    # Pick the version in VIGUEUR if any, otherwise the first.
    current = next((v for v in versions if _derive_etat(v) == "VIGUEUR"), None)
    primary = current or versions[0]
    others = [v for v in versions if v is not primary]

    lines = []
    title = primary.get("titre") or "(section)"
    cid = primary.get("cid") or "?"
    etat = _derive_etat(primary)
    start = ms_to_iso(primary.get("dateDebut")) or "?"
    end = ms_to_iso(primary.get("dateFin")) or "—"
    lines.append(f"### {title}")
    lines.append(f"**CID** : `{cid}` · **État** : {etat} · **Période** : {start} → {end}")
    lines.append(f"**Date interrogée** : {date_iso}")
    lines.append("")

    sub_sections = primary.get("liensSection") or []
    if sub_sections:
        lines.append(f"#### Sous-sections ({len(sub_sections)})")
        for s in sub_sections:
            s_title = s.get("titre") or "(section)"
            s_cid = s.get("cid") or s.get("id") or "?"
            s_etat = s.get("etat") or ""
            s_start = ms_to_iso(s.get("dateDebut")) or ""
            meta = []
            if s_etat:
                meta.append(s_etat)
            if s_start:
                meta.append(f"depuis {s_start}")
            meta_str = f" _( {' · '.join(meta)} )_" if meta else ""
            lines.append(f"- **{s_title}**{meta_str}")
            lines.append(f"  `{s_cid}`")
        lines.append("")

    articles = primary.get("liensArticle") or []
    if articles:
        lines.append(f"#### Articles ({len(articles)})")
        for a in articles:
            num = a.get("num") or "?"
            a_id = a.get("id") or a.get("cid") or "?"
            a_etat = a.get("etat") or ""
            lines.append(f"- **Art. {num}** · `{a_id}` _({a_etat})_")
        lines.append("")

    if others:
        lines.append(f"#### Autres versions de cette section ({len(others)})")
        for v in others:
            v_etat = _derive_etat(v)
            v_start = ms_to_iso(v.get("dateDebut")) or "?"
            v_end = ms_to_iso(v.get("dateFin")) or "—"
            lines.append(f"- {v_etat} : {v_start} → {v_end}")

    return "\n".join(lines)
