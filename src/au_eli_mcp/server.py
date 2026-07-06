"""FastMCP entry point - Australia Federal Register of Legislation tools.

Run:

    python -m au_eli_mcp.server

Configuration via env:

- ``AU_ELI_CACHE_DIR`` (default ``~/.matematic/cache/au-eli``)
- ``AU_ELI_AUDIT_DIR`` (default ``~/.matematic/audit``)
- ``AU_ELI_BASE_URL`` (default ``https://www.legislation.gov.au``)
"""

from __future__ import annotations

import os

import httpx
from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .audit import AuditLogger, hash_input, timer
from .citations import build_summary, extract_text, parse_search_results
from .client import DEFAULT_BASE_URL, FrliClient
from .models import ActSearchResult, ActSummary, ActText

_MAX_FULL_TEXT_CHARS = 300_000

INSTRUCTIONS = """\
This MCP server exposes Australia's Federal Register of Legislation (legislation.gov.au), the official source of Commonwealth legislation. Australia has no ELI scheme; every response carries a stable `eli_uri` (the durable legislation.gov.au URL, keyed on the document's own FRLI identifier), a `human_readable_citation` (the Act title) and a `source_url`. See `eli_note` on every response for the honest explanation.

## Scope (MVP)

This MVP covers **Acts only** (`collection(act)`). Regulations and other instrument types are not yet covered - relay the `dataset_note`.

## Call order

1. `au_search_acts` - find Acts by (partial) title. Returns `frli_id` for each match (e.g. `C2004A00042` for the Aboriginal Affairs (Arrangements with the States) Act 1973).
2. `au_get_text` - the current consolidated text of an Act by `frli_id`. Large Acts are truncated at roughly 300,000 characters.

## Hard constraints

- **No native ELI** - Australia has not deployed ELI. `eli_uri` is the legislation.gov.au document URL, never invented; see `eli_note`.
- **Acts only in this MVP** - regulations, legislative instruments, and repealed/historical versions are not covered; only the current (`latest`) text of an Act.
- **Every response has `human_readable_citation` + `source_url`** - cite both to the user.
- **No modification of official text** - returned verbatim from legislation.gov.au.
- **Audit log JSONL** - every tool call appends to `~/.matematic/audit/au-eli-mcp.jsonl`.

## Error iteration

Tools return a structured error with a `[code]` prefix:
- `invalid_arg` - a parameter is missing, empty, or out of range.
- `not_found` - no Act matches that `frli_id`, or no search results were found.
- `upstream_error` - a legislation.gov.au error (HTTP, timeout, malformed HTML). Retry once before surfacing.

## Response style

- Cite Acts as `human_readable_citation` with the legislation.gov.au URL: "Aboriginal Affairs (Arrangements with the States) Act 1973, https://www.legislation.gov.au/C2004A00042/latest".
- NEVER invent an `frli_id`, `eli_uri` or title - take each from the tool output.
"""


class ToolError(Exception):
    """Structured error for au-eli MCP tools - visible to the LLM with a [code] prefix."""

    VALID_CODES = frozenset({"invalid_arg", "not_found", "upstream_error"})

    def __init__(self, code: str, message: str):
        if code not in self.VALID_CODES:
            raise ValueError(f"Unknown ToolError code: {code}. Valid: {sorted(self.VALID_CODES)}")
        self.code = code
        super().__init__(f"[{code}] {message}")


READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    idempotentHint=True,
    destructiveHint=False,
    openWorldHint=True,
)

mcp: FastMCP = FastMCP(name="au-eli-mcp", instructions=INSTRUCTIONS)


def _base_url() -> str:
    return os.environ.get("AU_ELI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _audit() -> AuditLogger:
    return AuditLogger()


def _map_upstream(exc: Exception) -> Exception:
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 404:
        return ToolError("not_found", "No Act found on legislation.gov.au for that frli_id.")
    if isinstance(exc, (httpx.HTTPStatusError, httpx.TransportError, httpx.TimeoutException)):
        return ToolError("upstream_error", f"legislation.gov.au error: {type(exc).__name__}: {exc}")
    return exc


# ---------------------------------------------------------------------------
# au_search_acts
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def au_search_acts(title: str) -> ActSearchResult:
    """Search Commonwealth Acts by (partial) title.

    Args:
        title: e.g. ``"privacy"`` or ``"Aboriginal Affairs"``.

    Returns:
        ``ActSearchResult`` with ``items: list[ActSummary]``, each carrying the citation contract.
    """
    audit = _audit()
    if not title.strip():
        raise ToolError("invalid_arg", "title must not be empty.")
    input_hash = hash_input({"title": title})

    with timer() as t:
        try:
            async with FrliClient(base_url=_base_url()) as client:
                html = await client.search_by_title(title)
        except Exception as exc:
            audit.log(tool="au_search_acts", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    rows = parse_search_results(html)
    items = [
        ActSummary.model_validate(
            {
                "frli_id": row["frli_id"],
                "title": row["title"],
                "human_readable_citation": row["title"],
                "eli_uri": f"https://www.legislation.gov.au/{row['frli_id']}/latest",
                "source_url": f"https://www.legislation.gov.au/{row['frli_id']}/latest",
            }
        )
        for row in rows
    ]
    result = ActSearchResult(query=title, items=items)
    audit.log(tool="au_search_acts", input_hash=input_hash, output_count_or_size=len(items),
              duration_ms=t.duration_ms, status="ok")
    return result


# ---------------------------------------------------------------------------
# au_get_text
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def au_get_text(frli_id: str) -> ActText:
    """Fetch the current consolidated text of an Act by its FRLI identifier.

    Args:
        frli_id: e.g. ``"C2004A00042"``.

    Returns:
        ``ActText`` with ``eli_uri``, ``human_readable_citation``, ``source_url``, ``content``
        and ``truncated`` (True if the text was cut at ~300,000 characters).
    """
    audit = _audit()
    if not frli_id.strip():
        raise ToolError("invalid_arg", "frli_id must not be empty.")
    input_hash = hash_input({"frli_id": frli_id})

    with timer() as t:
        try:
            async with FrliClient(base_url=_base_url()) as client:
                html = await client.get_text(frli_id)
        except Exception as exc:
            audit.log(tool="au_get_text", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    full_text = extract_text(html)
    if not full_text:
        raise ToolError("not_found", f"No text found for frli_id={frli_id!r}.")
    truncated = len(full_text) > _MAX_FULL_TEXT_CHARS
    content = full_text[:_MAX_FULL_TEXT_CHARS] if truncated else full_text

    meta = build_summary(frli_id, html)
    result = ActText(
        frli_id=frli_id,
        title=meta.get("title"),
        eli_uri=meta.get("eli_uri"),
        human_readable_citation=meta.get("human_readable_citation"),
        source_url=meta.get("source_url"),
        content=content,
        byte_size=len(content.encode("utf-8")),
        truncated=truncated,
    )
    audit.log(tool="au_get_text", input_hash=input_hash, output_count_or_size=result.byte_size or 0,
              duration_ms=t.duration_ms, status="ok")
    return result


def main() -> None:
    """Run the MCP server over stdio (default for Claude Code)."""
    mcp.run()


if __name__ == "__main__":
    main()
