"""Federal Register of Legislation (Australia) parsing + citation helpers.

legislation.gov.au is an Angular app with server-side rendering: search results and act text
are both present in the initial HTML response. Each document carries a stable **FRLI ID**
(Federal Register of Legislation Identifier, e.g. ``C2004A00042``) - a genuine, government-
assigned persistent identifier, used here as the durable "no native ELI" substitute. Parsed
with the same tolerant tree builder as ``sg-eli-mcp`` (``html_tree.py``, stdlib only).

Citation contract:
- ``eli_uri``: the durable legislation.gov.au document URL, keyed on the FRLI ID
  (``https://www.legislation.gov.au/{frli_id}/latest``). NEVER invented.
- ``human_readable_citation``: the Act title, taken verbatim from the search result link text
  or the page's ``<title>``.
- ``source_url``: the same legislation.gov.au document URL.
"""

from __future__ import annotations

import re
from typing import Any

from . import html_tree

BASE_URL = "https://www.legislation.gov.au"
_TITLE_SUFFIX_RE = re.compile(r"\s*-\s*Federal Register of Legislation\s*$", re.IGNORECASE)
_RESULT_HREF_RE = re.compile(r"^/([A-Za-z]\d{4}[A-Za-z]\d+)/(latest|asmade)$")


def doc_url(frli_id: str, version: str = "latest") -> str:
    return f"{BASE_URL}/{frli_id}/{version}"


def parse_search_results(html_text: str) -> list[dict[str, Any]]:
    """Parse a ``/search/title(...)/collection(act)`` page into ``[{frli_id, title}, ...]``."""
    root = html_tree.parse(html_text)
    seen: dict[str, str] = {}
    for link in _iter_links(root):
        href = (link.get("attr") or {}).get("href", "")
        m = _RESULT_HREF_RE.match(href)
        if not m:
            continue
        frli_id = m.group(1)
        title = html_tree.text_of(link).strip()
        if frli_id and title and frli_id not in seen:
            seen[frli_id] = title
    return [{"frli_id": frli_id, "title": title} for frli_id, title in seen.items()]


def _iter_links(node: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(node, dict):
        if node.get("tag") == "a":
            out.append(node)
        for child in node.get("children") or []:
            out.extend(_iter_links(child))
    elif isinstance(node, list):
        for child in node:
            out.extend(_iter_links(child))
    return out


def _page_title(root: dict[str, Any]) -> str | None:
    for node in _iter_tags(root, "title"):
        text = html_tree.text_of(node).strip()
        if text:
            return _TITLE_SUFFIX_RE.sub("", text).strip()
    return None


def _iter_tags(node: Any, tag: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(node, dict):
        if node.get("tag") == tag:
            out.append(node)
        for child in node.get("children") or []:
            out.extend(_iter_tags(child, tag))
    elif isinstance(node, list):
        for child in node:
            out.extend(_iter_tags(child, tag))
    return out


def build_summary(frli_id: str, html_text: str, version: str = "latest") -> dict[str, Any]:
    """Build the citation contract from a fetched ``/{frli_id}/{version}/text`` page."""
    root = html_tree.parse(html_text)
    title = _page_title(root)
    url = doc_url(frli_id, version)
    return {
        "frli_id": frli_id,
        "title": title,
        "human_readable_citation": title,
        "eli_uri": url,
        "source_url": url,
    }


def extract_text(html_text: str) -> str | None:
    """Extract the legislative text from the ``#textTab`` container on a document page."""
    root = html_tree.parse(html_text)
    container = html_tree.find_by_id(root, "textTab")
    if container is None:
        return None
    text = html_tree.text_of(container).strip()
    return text or None
