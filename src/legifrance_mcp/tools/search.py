"""Tool: search_legifrance — POST /search across LODA/CODE/JORF/JURI/ALL."""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context
from pydantic import Field

from legifrance_mcp.client.errors import LegifranceError, format_error_for_agent
from legifrance_mcp.schemas.common import ResponseFormat, StrictBase

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from legifrance_mcp.client.http import LegifranceClient

logger = logging.getLogger(__name__)

# Friendly fond name → Légifrance fond constant.
# CODE_DATE = code consolidé à une date donnée (le plus utile pour pharmaciens).
# CODE_ETAT = code dans son état actuel.
# LODA_ETAT = lois/décrets/arrêtés (LODA) — pour textes non codifiés.
# JORF = textes publiés au Journal Officiel.
# JURI = jurisprudence.
# ALL = recherche tous fonds (utile en exploratoire).
_FOND_MAP: dict[str, str] = {
    "code": "CODE_DATE",
    "code_date": "CODE_DATE",
    "code_etat": "CODE_ETAT",
    "loda": "LODA_ETAT",
    "loda_etat": "LODA_ETAT",
    "jorf": "JORF",
    "juri": "JURI",
    "all": "ALL",
    "tout": "ALL",
}


class SearchLegifranceInput(StrictBase):
    query: str = Field(
        min_length=2,
        description="Texte à rechercher (mots-clés, expression).",
    )
    fond: str = Field(
        default="all",
        description=(
            "Fond Légifrance : 'code' (= CODE_DATE, code consolidé à une date), "
            "'code_etat' (état actuel), 'loda' (lois/décrets/arrêtés non codifiés), "
            "'jorf' (Journal Officiel), 'juri' (jurisprudence), 'all' (tous fonds)."
        ),
    )
    date: str | None = Field(
        default=None,
        description=(
            "Date d'application au format YYYY-MM-DD. **Obligatoire pour fond='code'** "
            "(CODE_DATE) — sinon 0 résultat. Défaut : date du jour si fond='code'."
        ),
    )
    code_name: str | None = Field(
        default=None,
        description=(
            "Restreint la recherche à un code précis (ex: 'Code de la santé publique'). "
            "N'a d'effet que sur fond='code' / 'code_etat'."
        ),
    )
    page_size: int = Field(default=10, ge=1, le=50)
    page_number: int = Field(default=1, ge=1)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


def register(mcp: "FastMCP") -> None:
    @mcp.tool(
        name="search_legifrance",
        annotations={
            "title": "Rechercher dans Légifrance (codes, JORF, LODA, jurisprudence)",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def search_legifrance(params: SearchLegifranceInput, ctx: Context) -> str:
        """Recherche full-text via l'API Légifrance.

        Pour le pharmacien officinal, le cas central c'est ``fond='code'`` avec
        ``code_name='Code de la santé publique'`` et la date du jour — on récupère
        la version en vigueur des articles qui matchent.

        Pour les textes JORF (décrets, arrêtés non codifiés) utiliser ``fond='loda'``
        ou ``fond='jorf'``.

        Renvoie ``totalResultNumber`` + jusqu'à ``page_size`` résultats avec
        titre, CID, état (VIGUEUR / ABROGE / MODIFIE), date, nature.
        """
        client: LegifranceClient = ctx.request_context.lifespan_context["client"]

        fond_key = (params.fond or "all").lower()
        fond = _FOND_MAP.get(fond_key, fond_key.upper())

        criteres = [
            {
                "typeRecherche": "UN_DES_MOTS",
                "valeur": params.query,
                "operateur": "ET",
            }
        ]
        recherche: dict = {
            "champs": [
                {"typeChamp": "ALL", "criteres": criteres, "operateur": "ET"}
            ],
            "pageNumber": params.page_number,
            "pageSize": params.page_size,
            "operateur": "ET",
            "sort": "PERTINENCE",
            "typePagination": "DEFAUT",
        }

        filtres: list[dict] = []
        if params.code_name:
            filtres.append({"facette": "NOM_CODE", "valeurs": [params.code_name]})

        if fond == "CODE_DATE":
            iso = params.date or date.today().isoformat()
            try:
                ts_ms = int(
                    date.fromisoformat(iso).strftime("%s")
                ) * 1000
            except ValueError:
                return f"Erreur Légifrance: date invalide '{iso}' (attendu YYYY-MM-DD)."
            filtres.append({"facette": "DATE_VERSION", "singleDate": ts_ms})

        if filtres:
            recherche["filtres"] = filtres

        body = {"recherche": recherche, "fond": fond}

        try:
            data = await client.post_json("/search", body)
        except LegifranceError as exc:
            return format_error_for_agent(exc)

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2, ensure_ascii=False)

        return _format_md(data, query=params.query, fond=fond)


def _format_md(data: dict, *, query: str, fond: str) -> str:
    total = data.get("totalResultNumber", 0)
    results = data.get("results") or []
    lines = [
        f"### Recherche Légifrance — `{fond}` : *{query}*",
        f"**Total** : {total} résultat(s) · affichés : {len(results)}",
        "",
    ]
    if not results:
        lines.append("_(aucun résultat — affiner la requête, vérifier le fond et la date)_")
        return "\n".join(lines)

    for i, r in enumerate(results, 1):
        titles = r.get("titles") or []
        # L'API renvoie souvent en titles[0..n] des sections (title=None) puis le
        # texte parent. On prend la 1re entrée avec un titre non vide.
        head = next((t for t in titles if t.get("title")), titles[0] if titles else {})
        title = head.get("title") or "(sans titre)"
        cid = head.get("cid")
        legal = head.get("legalStatus") or r.get("etat") or "?"
        nature = head.get("nature") or r.get("nature") or "?"
        start = (head.get("startDate") or "")[:10]
        lines.append(f"**{i}. {title}**")
        meta = [f"📜 {nature}", f"🏛 {legal}"]
        if start:
            meta.append(f"📅 {start}")
        if cid:
            meta.append(f"`{cid}`")
        lines.append(" · ".join(meta))
        snippet = (r.get("text") or "").strip()
        if snippet:
            lines.append("> " + snippet.replace("\n", " ")[:400])
        lines.append("")

    return "\n".join(lines)
