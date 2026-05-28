"""Quick CLI demo — exercises the analytics functions without going through MCP.

    python examples/cli_demo.py top-sector
    python examples/cli_demo.py top-country 2026 4
    python examples/cli_demo.py timeline lockbit3
"""

from __future__ import annotations

import asyncio
import json
import sys

from ransomware_live_mcp.analytics import (
    group_activity_timeline,
    top_country_for_period,
    top_groups_for_period,
    top_sector_for_period,
)
from ransomware_live_mcp.client import RansomwareLiveClient


async def main(argv: list[str]) -> None:
    if not argv:
        print(__doc__)
        return

    cmd, *rest = argv
    async with RansomwareLiveClient() as client:
        if cmd == "top-sector":
            year = int(rest[0]) if len(rest) > 0 else None
            month = int(rest[1]) if len(rest) > 1 else None
            result = await top_sector_for_period(client, year=year, month=month)
        elif cmd == "top-country":
            year = int(rest[0]) if len(rest) > 0 else None
            month = int(rest[1]) if len(rest) > 1 else None
            result = await top_country_for_period(client, year=year, month=month)
        elif cmd == "top-groups":
            year = int(rest[0]) if len(rest) > 0 else None
            month = int(rest[1]) if len(rest) > 1 else None
            result = await top_groups_for_period(client, year=year, month=month)
        elif cmd == "timeline":
            name = rest[0]
            year = int(rest[1]) if len(rest) > 1 else None
            result = await group_activity_timeline(client, name=name, year=year)
        else:
            print(f"unknown command: {cmd}")
            print(__doc__)
            return

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
