# ransomware-live-mcp

A [Model Context Protocol](https://modelcontextprotocol.io) server that lets
Claude (and any other MCP client) answer questions like:

> *"Which industry got hit most by ransomware this month?"*
> *"How active has LockBit been this year, month by month?"*
> *"List every UK victim posted in the last week."*

It wraps the public [ransomware.live v2 API](https://www.ransomware.live/api)
and adds a few computed analytics tools so the LLM doesn't have to count
records itself.

## What's inside

**Thin wrappers** (one tool per upstream endpoint):

- `recent_victims`, `recent_cyberattacks`
- `list_groups`, `group_details`, `group_victims`
- `country_victims`, `sector_victims`, `yearly_victims`
- `search_victims`
- `fetch_endpoint` — escape hatch for any other `/v2/...` path

**Computed analytics** (aggregation done in Python, not the LLM):

- `top_sector_this_month` — leading industry by victim count
- `top_country_this_month` — leading country
- `top_groups_this_month` — most active threat actors
- `group_timeline` — monthly victim count for a named group

## Install

Requires Python 3.10+.

```bash
git clone <this repo>
cd ransomware-live-mcp
pip install -e .
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install -e .
```

## Use it from Claude Desktop

Add this to your Claude Desktop config
(`%APPDATA%\Claude\claude_desktop_config.json` on Windows,
`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "ransomware-live": {
      "command": "ransomware-live-mcp"
    }
  }
}
```

A `uvx`-based variant is in [`examples/claude_desktop_config.json`](examples/claude_desktop_config.json).

Restart Claude Desktop. You should see the tools light up in the 🔌 menu.

## Try it from the CLI

```bash
python examples/cli_demo.py top-sector
python examples/cli_demo.py top-country 2026 4
python examples/cli_demo.py timeline lockbit3
```

## Run the tests

```bash
pip install -e ".[dev]"
pytest
```

## Notes on the upstream API

- ransomware.live v2 is free and unauthenticated but rate-limited to roughly
  **1 request per minute per endpoint**.
- This server caches responses in-process for 60s, so a Claude session that
  asks several questions about the same period only hits the API once.
- A "PRO" tier with an API key exists at `api-pro.ransomware.live` — not used
  here, but the client class is small enough to extend if you need it.

## License

MIT.
