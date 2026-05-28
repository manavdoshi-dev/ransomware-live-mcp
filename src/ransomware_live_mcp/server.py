"""MCP server exposing ransomware.live v2 endpoints + computed analytics.

The thin-wrapper tools mirror the upstream endpoints one-for-one. The analytics
tools combine those calls and do the aggregation in-process so the LLM doesn't
have to count records itself — which is the kind of thing it's bad at.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from .analytics import (
    group_activity_timeline,
    top_country_for_period,
    top_groups_for_period,
    top_sector_for_period,
)
from .client import RansomwareLiveClient, RansomwareLiveError

log = logging.getLogger(__name__)

mcp = FastMCP("ransomware-live")
_client: RansomwareLiveClient | None = None


def _get_client() -> RansomwareLiveClient:
    global _client
    if _client is None:
        _client = RansomwareLiveClient()
    return _client


# ---------- thin endpoint wrappers ----------

@mcp.tool()
async def recent_victims() -> Any:
    """Return the most recent ransomware victims posted on leak sites.

    Each record includes group, victim domain, country, sector ("activity"),
    discovery and attack timestamps, and a short description.
    """
    return await _get_client().get("/v2/recentvictims")


@mcp.tool()
async def recent_cyberattacks() -> Any:
    """Return recently reported cyberattacks (broader than just leak-site posts)."""
    return await _get_client().get("/v2/recentcyberattacks")


@mcp.tool()
async def list_groups() -> Any:
    """List all tracked ransomware threat-actor groups (names + metadata)."""
    return await _get_client().get("/v2/groups")


@mcp.tool()
async def group_details(name: str) -> Any:
    """Return profile information for a single ransomware group.

    Args:
        name: Group identifier as used by ransomware.live (e.g. "lockbit3", "alphv").
    """
    return await _get_client().get(f"/v2/group/{name}")


@mcp.tool()
async def group_victims(name: str) -> Any:
    """Return all known victims attributed to a specific ransomware group."""
    return await _get_client().get(f"/v2/groupvictims/{name}")


@mcp.tool()
async def country_victims(country_code: str) -> Any:
    """Return victims located in a country.

    Args:
        country_code: ISO 3166-1 alpha-2 code (e.g. "US", "GB", "FR").
    """
    return await _get_client().get(f"/v2/countryvictims/{country_code.upper()}")


@mcp.tool()
async def sector_victims(sector: str, country_code: str | None = None) -> Any:
    """Return victims in a given industry sector, optionally filtered by country.

    Args:
        sector: Sector name as used by ransomware.live (e.g. "Healthcare").
        country_code: Optional ISO 3166-1 alpha-2 code to narrow the result.
    """
    if country_code:
        return await _get_client().get(
            f"/v2/sectorvictims/{sector}/{country_code.upper()}"
        )
    return await _get_client().get(f"/v2/sectorvictims/{sector}")


@mcp.tool()
async def list_sectors() -> Any:
    """List every industry sector tracked by ransomware.live."""
    return await _get_client().get("/v2/sectors")


@mcp.tool()
async def victims_in_year(year: int) -> Any:
    """Return all victims posted in a given calendar year."""
    return await _get_client().get(f"/v2/victims/{year}")


@mcp.tool()
async def victims_in_month(year: int, month: int) -> Any:
    """Return victims posted in a specific month of a year.

    Args:
        year: Calendar year, e.g. 2026.
        month: Month 1-12.
    """
    return await _get_client().get(f"/v2/victims/{year}/{month}")


@mcp.tool()
async def search_victims(keyword: str) -> Any:
    """Full-text search across the victim database (domain, description, etc.)."""
    return await _get_client().get(f"/v2/searchvictims/{keyword}")


@mcp.tool()
async def country_cyberattacks(country_code: str) -> Any:
    """Return reported cyberattacks against entities in a country (broader than leak posts)."""
    return await _get_client().get(f"/v2/countrycyberattacks/{country_code.upper()}")


@mcp.tool()
async def all_cyberattacks() -> Any:
    """Return the full corpus of tracked cyberattacks."""
    return await _get_client().get("/v2/allcyberattacks")


@mcp.tool()
async def country_certs(country_code: str) -> Any:
    """Return national CERT/CSIRT contact info for a country (useful for incident escalation)."""
    return await _get_client().get(f"/v2/certs/{country_code.upper()}")


@mcp.tool()
async def api_info() -> Any:
    """Return ransomware.live API version and metadata."""
    return await _get_client().get("/v2/info")


@mcp.tool()
async def fetch_endpoint(path: str) -> Any:
    """Escape hatch — fetch any v2 endpoint path directly.

    Use when no dedicated tool exists for an endpoint. The path must start with
    "/v2/" and contain no query string. Example: "/v2/iocs/lockbit3".
    """
    if not path.startswith("/v2/"):
        raise RansomwareLiveError("path must start with /v2/")
    if "?" in path:
        raise RansomwareLiveError("query strings are not supported")
    return await _get_client().get(path)


# ---------- analytics tools ----------

@mcp.tool()
async def top_sector_this_month(year: int | None = None, month: int | None = None) -> dict[str, Any]:
    """Industry sector with the most ransomware victims this month (or a given month).

    Args:
        year: Calendar year (defaults to current year UTC).
        month: Month 1-12 (defaults to current month UTC).
    """
    return await top_sector_for_period(_get_client(), year=year, month=month)


@mcp.tool()
async def top_country_this_month(year: int | None = None, month: int | None = None) -> dict[str, Any]:
    """Country with the most ransomware victims this month (or a given month)."""
    return await top_country_for_period(_get_client(), year=year, month=month)


@mcp.tool()
async def top_groups_this_month(
    limit: int = 10, year: int | None = None, month: int | None = None
) -> dict[str, Any]:
    """Most active ransomware groups by victim count for the period."""
    return await top_groups_for_period(_get_client(), limit=limit, year=year, month=month)


@mcp.tool()
async def group_timeline(name: str, year: int | None = None) -> dict[str, Any]:
    """Monthly victim count for a specific group across a year.

    Args:
        name: Group identifier.
        year: Calendar year (defaults to current year UTC).
    """
    return await group_activity_timeline(_get_client(), name=name, year=year)


def run() -> None:
    """Run the server over stdio (default MCP transport for desktop clients)."""
    logging.basicConfig(level=logging.INFO)
    mcp.run()
