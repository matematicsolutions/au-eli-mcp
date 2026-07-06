# Discovery: Federal Register of Legislation (legislation.gov.au) - Australia

Date: 2026-07-06. **Status: CLOSED** for a search+fetch+cite MVP (confirmed by live probing).

## Context: New Zealand was probed alongside Australia and ruled out

`legislation.govt.nz` returned **HTTP 202 with an empty body** on both `/robots.txt` and the
homepage, from a plain `httpx`/browser-UA request - a bot-challenge pattern (the server accepts
the request but returns nothing, typical of a WAF/challenge service that needs real browser JS
execution to pass). This is the same fragility class as Thailand's WAF-blocked SPA in this
session: not fixable with a header change, needs either browser automation or a human decision
to invest in that. New Zealand was not pursued further in this session.

## Base properties (CONFIRMED live 2026-07-06)

- **Base URL:** `https://www.legislation.gov.au`
- **Authentication:** none (public portal).
- **Format:** Angular application with **server-side rendering** - unlike a typical SPA, the
  initial HTML response already contains the real search results and legislative text, not
  just an app shell (confirmed: an `ng-version` marker is present alongside genuine body text
  matching the requested document).
- **`robots.txt`**: permissive - only `/assets/` is disallowed, with a 10-second
  `Crawl-delay` and a `Sitemap` directive (the sitemap itself is a small placeholder covering
  only static top-level pages, not a full act catalog - not used for discovery here).
- **Identifier:** Australia has no ELI. Documents carry a **FRLI ID** (Federal Register of
  Legislation Identifier, e.g. `C2004A00042`) - a genuine, government-assigned persistent
  identifier, a stronger foundation for `eli_uri` than an ad-hoc viewer URL alone.

## Endpoints (CONFIRMED)

| Endpoint | Notes |
|---|---|
| `GET /search/title({query})/collection(act)` | server-rendered search results; each result `<a href="/{frli_id}/latest">{title}</a>` gives both the FRLI ID and the title as the link itself - no separate metadata call needed |
| `GET /{frli_id}/{version}/text` | the full text of a document; `version` is `latest` (current consolidated) or `asmade` (as originally made) - this MVP always uses `latest` |

Verified live: `/search/title(privacy)/collection(act)` returned real FRLI IDs
(`C1956A00041`, `C2004A00042`, ...) each as the visible text of its own result link;
`/C2004A00042/latest/text` returned a 75 KB page whose `<title>` correctly named the requested
Act and whose `#textTab` container held genuine section text (confirmed: the phrase "land
rights" appeared 5 times in a land-rights amendment Act, not template boilerplate).

## What was NOT found

- **No genuine `/api/*` REST endpoint.** A guessed `/api/search` path returned the Angular app
  shell (HTML, not JSON) - it is a client-side route matched by the Angular router, not a
  backend API, despite the URL's name.
- **No full-catalog sitemap.** `sitemap.xml` is a short, manually-curated placeholder, not a
  crawlable index of every Act.

## Fields used (for the citation contract)

- FRLI ID (from a search result `href`) -> the durable identifier ->
  `eli_uri = https://www.legislation.gov.au/{frli_id}/latest`.
- The Act title (search result link text, or the page `<title>` minus the
  " - Federal Register of Legislation" suffix) -> `human_readable_citation`.
- Same legislation.gov.au URL -> `source_url`.
- The `#textTab` container on a document page -> `au_get_text` (parsed with the same tolerant
  HTML tree builder as `sg-eli-mcp`, `html_tree.py` - stdlib only, no lxml/bs4 dependency).

## Citation contract (Article IV) - CLOSED for AU

- `eli_uri` = the legislation.gov.au document URL, keyed on the FRLI ID (no native ELI;
  documented via `eli_note`).
- `human_readable_citation` = the Act title, taken verbatim from the source.
- `source_url` = the same legislation.gov.au document URL.

## Tool mapping - search+fetch+cite MVP

| Tool | Endpoint |
|---|---|
| `au_search_acts` | `/search/title({query})/collection(act)` |
| `au_get_text` | `/{frli_id}/latest/text` (`#textTab` container flattened to text, truncated ~300k chars) |

**Deferred:** regulations and other instrument types, historical (`asmade`) versions, case law
(a separate portal).

## Decision: BUILD

Keyless, permissive `robots.txt`, genuinely server-rendered (not a client-only shell), and a
real government-assigned persistent identifier to build the citation contract on.
