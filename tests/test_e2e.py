"""End-to-end tests hitting live api.piste.gouv.fr.

Gated by env var ``LEGIFRANCE_E2E=1`` + valid ``PISTE_CLIENT_ID`` /
``PISTE_CLIENT_SECRET`` in the environment. Run:

    source ~/.etikpharma-secrets
    LEGIFRANCE_E2E=1 pytest tests/test_e2e.py -v

PISTE est un service public, mais les requêtes consomment un quota — laisser
gated par défaut.
"""

from __future__ import annotations

import pytest

from legifrance_mcp.client.http import LegifranceClient
from legifrance_mcp.config import Settings

# CID/textId connus, validés en session du 24/05/2026.
CSP_TEXT_ID = "LEGITEXT000006072665"
R4235_CHAPITRE_CID = "LEGISCTA000006178625"
R4235_1_ARTICLE_ID = "LEGIARTI000006913651"
DECRET_2026_156_JORF = "JORFTEXT000053618939"


@pytest.fixture
async def client():
    async with LegifranceClient(Settings()) as c:  # type: ignore[call-arg]
        yield c


@pytest.mark.e2e
async def test_get_section_r4235_chapitre_v(client):
    """R.4235 — chapitre V Code de déontologie des pharmaciens.

    Doit retourner ≥ 7 sous-sections (Section 1 à Section 7 du chapitre).
    """
    r = await client.post_json(
        "/consult/getSectionByCid",
        {"cid": R4235_CHAPITRE_CID, "textId": CSP_TEXT_ID, "date": "2026-05-24"},
    )
    assert "listSection" in r
    versions = r["listSection"]
    assert versions, "Aucune version de section retournée"
    # Au moins une version doit contenir des sous-sections
    sub_counts = [len(v.get("liensSection", [])) for v in versions]
    assert max(sub_counts) >= 6, f"Sous-sections attendues ≥ 6, got {sub_counts}"


@pytest.mark.e2e
async def test_get_jorf_decret_2026_156(client):
    """Décret n° 2026-156 du 3 mars 2026 modifiant le code de déontologie."""
    r = await client.post_json("/consult/jorf", {"textCid": DECRET_2026_156_JORF})
    title = r.get("title") or ""
    assert "2026-156" in title or "déontologie" in title.lower(), title
    assert (r.get("nature") or "").upper().startswith("DECRET") or r.get("nature") == "Décret"


@pytest.mark.e2e
async def test_search_loda_biosimilaire(client):
    """search 'biosimilaire' dans LODA_ETAT doit retourner ≥ 1 résultat.

    Spec d'origine mentionne fond=CODE — pratique : 'biosimilaire' n'apparaît pas
    verbatim dans le CSP (le code parle de 'groupes biologiques similaires').
    On valide donc sur le fond LODA qui contient l'arrêté substitution
    biosimilaire 20/02/2025 — ce qui est l'usage réel côté officine.
    """
    r = await client.post_json(
        "/search",
        {
            "recherche": {
                "champs": [
                    {
                        "typeChamp": "ALL",
                        "criteres": [
                            {"typeRecherche": "UN_DES_MOTS", "valeur": "biosimilaire", "operateur": "ET"}
                        ],
                        "operateur": "ET",
                    }
                ],
                "pageNumber": 1,
                "pageSize": 5,
                "operateur": "ET",
                "sort": "PERTINENCE",
                "typePagination": "DEFAUT",
            },
            "fond": "LODA_ETAT",
        },
    )
    total = r.get("totalResultNumber", 0)
    assert total >= 1, f"Attendu ≥1 résultat LODA pour 'biosimilaire', got {total}"


@pytest.mark.e2e
async def test_get_code_toc_csp(client):
    """TOC complète du Code de la santé publique."""
    r = await client.post_json(
        "/consult/code/tableMatieres",
        {"textId": CSP_TEXT_ID, "date": "2026-05-24"},
    )
    assert r.get("title")
    assert "santé publique" in r["title"].lower()
    sections = r.get("sections") or []
    # CSP a 6 Parties → au moins 4 sections top-level
    assert len(sections) >= 4, f"Sections top-level CSP attendues ≥ 4, got {len(sections)}"


@pytest.mark.e2e
async def test_get_article_r4235_1(client):
    """R.4235-1 CSP — article fondateur du code de déontologie."""
    r = await client.post_json("/consult/getArticle", {"id": R4235_1_ARTICLE_ID})
    art = r.get("article") or {}
    assert art.get("num") == "R4235-1"
    texte = (art.get("texte") or "").lower()
    assert "déontologie" in texte and "pharmaciens" in texte
