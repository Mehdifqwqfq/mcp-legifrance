"""Tool: get_article_by_num — POST /consult/getArticleWithIdAndNum.

Retrouve un article par son NUMÉRO dans un code (ex: R5132-36 du CSP). Ni
``get_section`` (ses ``liensArticle`` n'ont pas de numéro) ni la recherche plein
texte ne le permettent.

⚠️ Casse de l'endpoint : ``getArticleWithIdAndNum`` (A majuscule) répond 200,
``getArticleWithIdandNum`` répond 403 — mesuré le 2026-09-29.

⚠️ L'endpoint IGNORE un champ ``date`` dans le corps (mesuré le 2026-09-29 :
``date: 2015-01-01`` renvoie quand même la version de 2022). Il renvoie
toujours la version EN VIGUEUR, avec la liste ``articleVersions``. Le paramètre
``date`` est donc résolu ici : on choisit la version dont la période couvre la
date, puis on la relit via ``/consult/getArticle``.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date as date_cls
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context
from pydantic import Field

from legifrance_mcp.client.errors import LegifranceError, format_error_for_agent
from legifrance_mcp.schemas.common import ResponseFormat, StrictBase, ms_to_iso
from legifrance_mcp.tools.get_article import format_article_lines

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from legifrance_mcp.client.http import LegifranceClient

logger = logging.getLogger(__name__)

# "R.5132-36", "r 5132-36" → "R5132-36" : l'API ne connaît que la forme sans point
# (mesuré : "R.5132-36" renvoie article=null).
_NUM_PREFIX_RE = re.compile(r"^([A-Za-z]{1,2})\.?\s*(?=\d)")


def normalize_num(num: str) -> str:
    num = num.strip()
    return _NUM_PREFIX_RE.sub(lambda m: m.group(1).upper(), num, count=1)


class GetArticleByNumInput(StrictBase):
    text_id: str = Field(
        ...,
        description=(
            "LEGITEXT… du code. CSP = 'LEGITEXT000006072665', Code du travail = "
            "'LEGITEXT000006072050', CSS = 'LEGITEXT000006073189'."
        ),
        examples=["LEGITEXT000006072665"],
    )
    num: str = Field(
        ...,
        description="Numéro de l'article, ex: 'R5132-36' (le point après la lettre est toléré).",
        examples=["R5132-36"],
    )
    date: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description=("Date d'application YYYY-MM-DD. Absente = version en vigueur aujourd'hui."),
    )
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


def pick_version(versions: list[dict], iso: str) -> dict | None:
    """Version dont [dateDebut, dateFin[ contient la date ``iso`` (minuit UTC)."""
    d = date_cls.fromisoformat(iso)
    ms = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)
    for v in versions:
        start, end = v.get("dateDebut"), v.get("dateFin")
        if start is None or end is None:
            continue
        if int(start) <= ms < int(end):
            return v
    return None


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="get_article_by_num",
        annotations={
            "title": "Article d'un code Légifrance par son numéro",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def get_article_by_num(params: GetArticleByNumInput, ctx: Context) -> str:
        """Renvoie un article d'un code à partir de son numéro (ex: R5132-36 CSP).

        Affiche l'id de la version EN VIGUEUR (ou de la version à ``date``),
        le CID (1re version, stable), l'état, la période, le texte et le NOTA,
        ainsi que la liste des versions connues.
        """
        client: LegifranceClient = ctx.request_context.lifespan_context["client"]
        num = normalize_num(params.num)
        body = {"id": params.text_id, "num": num}
        try:
            data = await client.post_json("/consult/getArticleWithIdAndNum", body)
        except LegifranceError as exc:
            return format_error_for_agent(exc)

        art = data.get("article") or {}
        if not art:
            if params.response_format == ResponseFormat.JSON:
                return json.dumps(data, indent=2, ensure_ascii=False)
            return f"_(aucun article « {num} » dans {params.text_id})_"

        dated: dict | None = None
        if params.date:
            version = pick_version(art.get("articleVersions") or [], params.date)
            if version is None:
                return (
                    f"_(l'article {num} n'avait aucune version en vigueur le "
                    f"{params.date})_\n\n" + _versions_md(art)
                )
            if version.get("id") != art.get("id"):
                try:
                    dated = await client.post_json("/consult/getArticle", {"id": version["id"]})
                except LegifranceError as exc:
                    return format_error_for_agent(exc)

        if params.response_format == ResponseFormat.JSON:
            out = {"en_vigueur": data}
            if dated is not None:
                out["a_la_date"] = dated
            return json.dumps(out, indent=2, ensure_ascii=False)

        return _format_md(art, dated=(dated or {}).get("article"), date_iso=params.date)


def _format_md(art: dict, *, dated: dict | None, date_iso: str | None) -> str:
    shown = dated or art
    code = ((art.get("context") or {}).get("titreTxt") or [{}])[0]
    lines = format_article_lines(shown)
    head = [f"**Id version en vigueur** : `{art.get('id') or '?'}`"]
    if date_iso:
        head.insert(0, f"**Date interrogée** : {date_iso} → version `{shown.get('id') or '?'}`")
    if code.get("id"):
        head.append(f"**Code** : {code.get('titre') or '?'} (`{code['id']}`)")
    lines[1:1] = head
    lines += ["", _versions_md(art)]
    return "\n".join(lines)


def _versions_md(art: dict) -> str:
    versions = art.get("articleVersions") or []
    if not versions:
        return "_(liste des versions non fournie)_"
    rows = ["**Versions**"]
    for v in versions:
        start = ms_to_iso(v.get("dateDebut")) or "?"
        end = ms_to_iso(v.get("dateFin")) or "—"
        rows.append(f"- `{v.get('id')}` · {v.get('etat') or '?'} · {start} → {end}")
    return "\n".join(rows)
