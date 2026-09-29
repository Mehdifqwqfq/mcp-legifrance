"""Unit tests — no network. Validate helpers + schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from legifrance_mcp.schemas.common import ms_to_iso
from legifrance_mcp.tools.get_article import GetArticleInput, _format_md, _strip_html
from legifrance_mcp.tools.get_article_by_num import (
    GetArticleByNumInput,
    normalize_num,
    pick_version,
)
from legifrance_mcp.tools.get_article_by_num import _format_md as _format_by_num_md
from legifrance_mcp.tools.get_section import GetSectionInput
from legifrance_mcp.tools.search import SearchLegifranceInput


class TestMsToIso:
    def test_valid_timestamp(self):
        # 06/03/2026 00:00 UTC = 1772755200000
        assert ms_to_iso(1772755200000) == "2026-03-06"

    def test_sentinel_max_long_returns_none(self):
        assert ms_to_iso(9223372036854775807) is None

    def test_none(self):
        assert ms_to_iso(None) is None

    def test_zero(self):
        assert ms_to_iso(0) is None

    def test_bogus_string(self):
        assert ms_to_iso("not-a-number") is None


class TestStripHtml:
    def test_strips_tags_and_entities(self):
        assert _strip_html("<p>Hello&nbsp;<b>world</b></p>") == "Hello world"

    def test_keeps_text_only(self):
        assert _strip_html("plain") == "plain"

    def test_none(self):
        assert _strip_html(None) == ""

    def test_cr_entity(self):
        assert "\n" in _strip_html("a&#13;b")


class TestSchemas:
    def test_search_rejects_extra_field(self):
        with pytest.raises(ValidationError):
            SearchLegifranceInput(query="x", surprise=True)  # type: ignore[call-arg]

    def test_search_default_fond(self):
        m = SearchLegifranceInput(query="déontologie")
        assert m.fond == "all"
        assert m.page_size == 10

    def test_get_section_requires_cid_and_text_id(self):
        with pytest.raises(ValidationError):
            GetSectionInput(cid="LEGISCTA000006178625")  # type: ignore[call-arg]

    def test_get_article_min(self):
        m = GetArticleInput(article_id="LEGIARTI000006913651")
        assert m.article_id.startswith("LEGIARTI")


# Versions réelles de R5132-36 CSP, relevées le 2026-09-29.
_R5132_36_VERSIONS = [
    {
        "id": "LEGIARTI000006915590",
        "etat": "MODIFIE",
        "dateDebut": 1091923200000,
        "dateFin": 1170806400000,
    },
    {
        "id": "LEGIARTI000006915591",
        "etat": "MODIFIE",
        "dateDebut": 1170806400000,
        "dateFin": 1270080000000,
    },
    {
        "id": "LEGIARTI000022061148",
        "etat": "MODIFIE",
        "dateDebut": 1270080000000,
        "dateFin": 1335830400000,
    },
    {
        "id": "LEGIARTI000025787571",
        "etat": "MODIFIE",
        "dateDebut": 1335830400000,
        "dateFin": 1643932800000,
    },
    {
        "id": "LEGIARTI000045117816",
        "etat": "VIGUEUR",
        "dateDebut": 1643932800000,
        "dateFin": 32472144000000,
    },
]


class TestGetArticleByNum:
    def test_normalize_num(self):
        assert normalize_num("R5132-36") == "R5132-36"
        assert normalize_num("R.5132-36") == "R5132-36"
        assert normalize_num(" r. 5132-36 ") == "R5132-36"
        assert normalize_num("LO.141") == "LO141"
        assert normalize_num("Annexe 1") == "Annexe 1"

    def test_schema_rejects_bad_date(self):
        with pytest.raises(ValidationError):
            GetArticleByNumInput(text_id="LEGITEXT000006072665", num="R5132-36", date="01/01/2015")

    def test_pick_version(self):
        assert pick_version(_R5132_36_VERSIONS, "2015-01-01")["id"] == "LEGIARTI000025787571"
        assert pick_version(_R5132_36_VERSIONS, "2026-09-29")["id"] == "LEGIARTI000045117816"
        # borne : dateDebut incluse (2022-02-04)
        assert pick_version(_R5132_36_VERSIONS, "2022-02-04")["id"] == "LEGIARTI000045117816"
        assert pick_version(_R5132_36_VERSIONS, "2000-01-01") is None

    def test_format_shows_version_in_force(self):
        art = {
            "id": "LEGIARTI000045117816",
            "cid": "LEGIARTI000006915590",
            "num": "R5132-36",
            "etat": "VIGUEUR",
            "dateDebut": 1643932800000,
            "dateFin": 32472144000000,
            "texte": "<p>Texte</p>",
            "articleVersions": _R5132_36_VERSIONS,
            "context": {
                "titreTxt": [{"id": "LEGITEXT000006072665", "titre": "Code de la santé publique"}]
            },
        }
        md = _format_by_num_md(art, dated=None, date_iso=None)
        assert "**Id version en vigueur** : `LEGIARTI000045117816`" in md
        assert "**CID** : `LEGIARTI000006915590`" in md
        assert "`LEGITEXT000006072665`" in md
        assert "Texte" in md

    def test_format_dated_version(self):
        art = {
            "id": "LEGIARTI000045117816",
            "cid": "LEGIARTI000006915590",
            "num": "R5132-36",
            "articleVersions": _R5132_36_VERSIONS,
        }
        dated = {
            "id": "LEGIARTI000025787571",
            "cid": "LEGIARTI000006915590",
            "num": "R5132-36",
            "etat": "MODIFIE",
            "texte": "ancien",
        }
        md = _format_by_num_md(art, dated=dated, date_iso="2015-01-01")
        assert "version `LEGIARTI000025787571`" in md
        assert "**Id version** : `LEGIARTI000025787571`" in md
        assert "**Id version en vigueur** : `LEGIARTI000045117816`" in md


class TestGetArticleFormat:
    def test_shows_queried_version_id_and_cid(self):
        md = _format_md(
            {
                "article": {
                    "id": "LEGIARTI000006915590",
                    "cid": "LEGIARTI000006915590",
                    "num": "R5132-36",
                    "etat": "MODIFIE",
                    "texte": "x",
                }
            }
        )
        assert "**Id version** : `LEGIARTI000006915590`" in md
        md = _format_md(
            {
                "article": {
                    "id": "LEGIARTI000045117816",
                    "cid": "LEGIARTI000006915590",
                    "num": "R5132-36",
                    "texte": "x",
                }
            }
        )
        assert "**Id version** : `LEGIARTI000045117816` · **CID** : `LEGIARTI000006915590`" in md
