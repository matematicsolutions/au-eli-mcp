"""Element 9 of the MateMatic MCP canon: this connector declares its own coverage.

Knowledge about what a corpus does NOT hold is useless while it lives only as prose
in the server instructions - the model has to remember it and choose to relay it, and
an agent has no way to ask. Here it is callable.

Every gap below is grounded in this connector's own source and tool surface. The list
is deliberately never empty: no legal corpus is complete, so an empty gap list would
mean "nobody checked", not "there are no gaps".
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _CoverageBase(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class CoverageFamily(_CoverageBase):
    """One data family this connector exposes."""

    name: str = Field(description="Data family, e.g. 'Federal legislation'.")
    tool: str = Field(description="Tool or tools that reach this family.")
    source: str = Field(description="Official source the data comes from.")
    captured_at: str | None = Field(
        default=None,
        description="Date this family was last captured (ISO). None when queried live.",
    )
    live: bool = Field(default=True, description="True when queried live instead of from a snapshot.")


class CoverageGap(_CoverageBase):
    """A known, named hole in this connector's coverage - plus the way around it."""

    id: str = Field(description="Stable gap identifier.")
    family: str = Field(description="Which family the gap belongs to.")
    missing: str = Field(description="What is NOT available through this connector.")
    fallback: str = Field(description="Where to go instead.")


class Coverage(_CoverageBase):
    """What this connector covers, how it is sourced, and what it does not cover."""

    status: Literal["ok", "degraded", "failed"] = "ok"
    as_of_note: str = Field(description="States what the dates mean, and what they do not promise.")
    families: list[CoverageFamily] = Field(default_factory=list)
    known_gaps: list[CoverageGap] = Field(
        default_factory=list,
        description="Never empty. An empty list would mean 'not checked', not 'no gaps'.",
    )


SOURCE = 'legislation.gov.au (Federal Register of Legislation)'

AS_OF_NOTE = (
    "Data is queried live against the source, so there is no local snapshot date. Any date "
    "on a record states when the source published it - not that this connector verified the "
    "text is still in force today."
)

_FAMILIES: list[dict] = [{'name': 'Commonwealth Acts', 'tool': 'au_search_acts / au_get_text'}]

_GAPS: list[dict] = [{'id': 'AU-001', 'family': 'Commonwealth Acts', 'missing': 'Regulations, legislative instruments and other instrument types are not covered - this connector exposes Acts only.', 'fallback': 'Use the Federal Register of Legislation web search for instruments.'}, {'id': 'AU-002', 'family': 'Commonwealth Acts', 'missing': 'Repealed and historical versions are not covered; only the current (latest) text of an Act is served.', 'fallback': 'Use the point-in-time view on legislation.gov.au.'}, {'id': 'AU-003', 'family': 'Commonwealth Acts', 'missing': 'State and territory legislation is out of scope - this is Commonwealth law only.', 'fallback': 'Use the relevant state or territory legislation portal.'}]


def build_coverage() -> Coverage:
    """Assemble the declared coverage for this connector."""
    return Coverage(
        status="ok",
        as_of_note=AS_OF_NOTE,
        families=[CoverageFamily(source=SOURCE, live=True, **f) for f in _FAMILIES],
        known_gaps=[CoverageGap(**g) for g in _GAPS],
    )
