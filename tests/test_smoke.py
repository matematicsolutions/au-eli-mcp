"""Smoke tests - require internet, hit the live legislation.gov.au site.

Run manually:

    pytest tests/test_smoke.py -v
"""

from __future__ import annotations

import pytest

from au_eli_mcp.server import au_get_text, au_search_acts

# Aboriginal Affairs (Arrangements with the States) Act 1973.
FRLI_ID = "C2004A00042"


@pytest.mark.asyncio
async def test_smoke_search_acts() -> None:
    result = await au_search_acts("Aboriginal Affairs")
    assert len(result.items) > 0, "expected at least one match"
    assert any(item.frli_id == FRLI_ID for item in result.items), (
        f"expected {FRLI_ID} among matches: {[i.frli_id for i in result.items]}"
    )
    for item in result.items:
        assert item.eli_uri is not None and "legislation.gov.au" in item.eli_uri
        assert item.human_readable_citation is not None


@pytest.mark.asyncio
async def test_smoke_get_text() -> None:
    text = await au_get_text(FRLI_ID)
    assert text.content is not None and len(text.content) > 0
    assert text.eli_uri == f"https://www.legislation.gov.au/{FRLI_ID}/latest"
    assert text.byte_size and text.byte_size > 0
