# Constitution of au-eli-mcp

Version: 0.1.0
Date: 2026-07-06
Licence: Apache-2.0

`au-eli-mcp` is an MCP server for Australia's Federal Register of Legislation
(`legislation.gov.au`). It searches, fetches, and cites Commonwealth Acts as parsed
server-rendered HTML. Regulations, other instrument types, and case law are out of scope for
this MVP.

The 4 principles below are inherited from the `eu-legal-mcp` line Constitution (Article IV),
adapted for a jurisdiction without ELI.

---

## Art. 1. Public data only

The Federal Register of Legislation is the official, public source of Commonwealth
legislation, published by the Australian government. The server is read-only against
legislation.gov.au and sends nothing beyond the requested title or FRLI identifier.

## Art. 2. Mandatory audit log

Every tool call MUST append one JSON line to `~/.matematic/audit/au-eli-mcp.jsonl`
(ts / tool / input_hash SHA-256 / output_count_or_size / duration_ms / status). Inability to
write = the tool returns an error, it does not silently skip.

## Art. 3. Vendor neutrality

No tool hardcodes an LLM provider, assumes a model, or adds commercial telemetry. The server
talks only to `legislation.gov.au` and the local filesystem. Authentication: none; own backoff
+ cache.

## Art. 4. A durable identifier and a human-readable citation are mandatory

Every response MUST carry three fields:
- `eli_uri`: Australia has no ELI. This is the durable legislation.gov.au document URL
  (`https://www.legislation.gov.au/{frli_id}/latest`), keyed on the Federal Register of
  Legislation's own persistent identifier (FRLI ID) - never invented. `eli_note` on every
  response says so explicitly.
- `human_readable_citation`: the Act title, taken verbatim from the source (search result link
  text or page `<title>`).
- `source_url`: the same legislation.gov.au document URL.

---

## Open points

1. **Acts only** - regulations and other Federal Register instrument types (legislative
   instruments, notifiable instruments) are not covered by this MVP.
2. **Current text only** - `au_get_text` always fetches the `latest` (current consolidated)
   version; historical (`asmade`, point-in-time) versions are not yet exposed as a parameter.
3. **Crawl-delay** - `robots.txt` requests a 10-second crawl delay. This connector relies on
   aggressive caching rather than an enforced in-process sleep between requests, consistent
   with `sg-eli-mcp`'s handling of its own robots.txt constraints; a future revision could add
   an explicit rate limiter if usage patterns warrant it.

## Ewolucja konstytucji

Changes to art. 1-4 follow SEMVER + an entry in `CHANGELOG.md` + a `pyproject.toml` bump.

First version: 2026-07-06. Author: Wieslaw Mazur / MateMatic.
