"""Pydantic v2 models for the Federal Register of Legislation (Australia) + au-eli-mcp."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

DATASET_NOTE = (
    "The Federal Register of Legislation (legislation.gov.au) is Australia's official source "
    "of Commonwealth legislation. Australia has no ELI scheme; eli_uri carries the durable "
    "legislation.gov.au URL keyed on the document's own FRLI identifier (see eli_note). "
    "Discover by title (au_search_acts), then fetch the current consolidated text by frli_id. "
    "This MVP covers Acts only; regulations and other instrument types are not yet covered."
)

ELI_NOTE = (
    "Australia has not deployed ELI. eli_uri is the durable legislation.gov.au document URL "
    "(https://www.legislation.gov.au/{frli_id}/latest), keyed on the Federal Register of "
    "Legislation's own persistent identifier (FRLI ID) - never invented."
)


class _Tolerant(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ActSummary(_Tolerant):
    """One Act as returned by ``au_search_acts``."""

    frli_id: str | None = None
    title: str | None = None

    # Citation contract (Art. IV CONSTITUTION).
    eli_uri: str | None = None
    eli_note: str = ELI_NOTE
    human_readable_citation: str | None = None
    source_url: str | None = None


class ActSearchResult(_Tolerant):
    """Result of ``au_search_acts``."""

    query: str
    items: list[ActSummary] = Field(default_factory=list)
    dataset_note: str = DATASET_NOTE


class ActText(_Tolerant):
    """Result of ``au_get_text`` - the current consolidated text of an Act."""

    frli_id: str
    title: str | None = None
    eli_uri: str | None = None
    eli_note: str = ELI_NOTE
    human_readable_citation: str | None = None
    source_url: str | None = None
    content: str | None = None
    byte_size: int | None = None
    truncated: bool = False
    dataset_note: str = DATASET_NOTE
