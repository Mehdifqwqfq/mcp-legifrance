"""Unit tests — no network. Validate helpers + schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from legifrance_mcp.schemas.common import ms_to_iso
from legifrance_mcp.tools.get_article import GetArticleInput, _strip_html
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
