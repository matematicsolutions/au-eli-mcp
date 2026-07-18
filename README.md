# au-eli-mcp

<!-- mcp-name: io.github.matematicsolutions/au-eli-mcp -->

An MCP server for Australia's **Federal Register of Legislation** (`legislation.gov.au`), the
official source of Commonwealth legislation. It searches, fetches, and cites Acts, with a
verifiable citation on every response.

Part of the MateMatic `eu-legal-mcp` production line, extended into Asia-Pacific alongside
`jp-eli-mcp`, `sg-eli-mcp` and `my-eli-mcp`. Same citation contract (a stable identifier + a
human-readable citation + a source URL), adapted for a jurisdiction with no ELI.

> **Scope.** This MVP covers Acts only (`collection(act)`); regulations and other legislative
> instrument types are not yet covered. Discovery is by title (`au_search_acts`); fetch the
> current consolidated text with `au_get_text` (truncated for very large Acts). Every response
> carries a `dataset_note`.
>
> **Licence.** Federal Register of Legislation content is official public information
> published by the Australian government. This connector relays it with attribution and a
> `source_url`.

## The tools

| Tool | What it does |
|---|---|
| `au_search_acts` | Search Commonwealth Acts by (partial) title. |
| `au_get_text` | The current consolidated text of an Act (truncated at ~300,000 characters). |

Every response carries the contract: `eli_uri` (Australia has no ELI - this is the durable
legislation.gov.au URL keyed on the document's own FRLI identifier, e.g.
`https://www.legislation.gov.au/C2004A00042/latest`, see `eli_note`), `human_readable_citation`
(the Act title), and `source_url`.

## Install

Not yet on PyPI - install from source until the first release ships:

```bash
git clone https://github.com/matematicsolutions/au-eli-mcp
cd au-eli-mcp
pip install -e .
```

Once released, this will be `uvx au-eli-mcp`.

Configuration via env:

- `AU_ELI_BASE_URL` - default `https://www.legislation.gov.au`
- `AU_ELI_CACHE_DIR` - default `~/.matematic/cache/au-eli`
- `AU_ELI_AUDIT_DIR` - default `~/.matematic/audit`

No API key. legislation.gov.au is keyless.

### Configure (Claude Code / any MCP client)

```json
{
  "mcpServers": {
    "au-eli-mcp": { "command": "au-eli-mcp" }
  }
}
```

### Windows 11 with Smart App Control

Smart App Control blocks unsigned executables, which covers `uvx.exe`, `pip.exe`
and the `au-eli-mcp.exe` launcher that pip writes at install time. The `python.exe` and
`py.exe` from the python.org installer are signed by the Python Software
Foundation, so running the module through the interpreter works:

```bash
python -m pip install au-eli-mcp
python -m au_eli_mcp
```

`pip.exe` is blocked for the same reason, so install with `python -m pip`, not
`pip install`. If `python` is not on PATH, use the Windows launcher: `py -3 -m au_eli_mcp`.

```json
{ "mcpServers": { "au-eli-mcp": { "command": "python", "args": ["-m", "au_eli_mcp"] } } }
```

Do not turn Smart App Control off to work around this - it cannot be re-enabled
without reinstalling Windows.

## Governance

- **Public data only** - read-only against legislation.gov.au; no client data leaves the machine.
- **Robots-compliant** - `robots.txt` allows crawling (only `/assets/` is disallowed); this
  connector caches aggressively rather than hitting the site repeatedly.
- **Audit log** - every tool call appends one JSON line to `~/.matematic/audit/au-eli-mcp.jsonl`.
- **Vendor-neutral** - talks only to `legislation.gov.au`; no LLM provider, no telemetry.
- **Verifiable citations** - every response is independently checkable via `source_url`.

See `CONSTITUTION.md` and `DISCOVERY.md`.

## Tests

```bash
pip install -e ".[dev]"
pytest tests/test_instructions_drift.py -v   # offline
pytest tests/test_smoke.py -v                # hits live legislation.gov.au
```

## Licence

Apache-2.0. © Matematic Solutions / Wieslaw Mazur.
