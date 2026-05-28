"""Unit tests for the analytics aggregation — uses fake records, no network."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ransomware_live_mcp import analytics


class FakeClient:
    def __init__(self, records: list[dict]) -> None:
        self._records = records

    async def get(self, path: str):
        return self._records


@pytest.fixture
def records() -> list[dict]:
    return [
        {"group": "lockbit3", "activity": "Healthcare", "country": "US",
         "attackdate": "2026-05-10T00:00:00+00:00"},
        {"group": "lockbit3", "activity": "Healthcare", "country": "GB",
         "attackdate": "2026-05-12T00:00:00+00:00"},
        {"group": "alphv", "activity": "Manufacturing", "country": "US",
         "attackdate": "2026-05-15T00:00:00+00:00"},
        {"group": "lockbit3", "activity": "Legal Services", "country": "US",
         "attackdate": "2026-04-01T00:00:00+00:00"},  # different month
    ]


@pytest.mark.asyncio
async def test_top_sector(records: list[dict]) -> None:
    client = FakeClient(records)
    out = await analytics.top_sector_for_period(client, year=2026, month=5)
    assert out["total_victims"] == 3
    assert out["top_sector"] == "Healthcare"
    assert out["top_sector_count"] == 2


@pytest.mark.asyncio
async def test_top_country(records: list[dict]) -> None:
    client = FakeClient(records)
    out = await analytics.top_country_for_period(client, year=2026, month=5)
    assert out["top_country"] == "US"
    assert out["top_country_count"] == 2


@pytest.mark.asyncio
async def test_top_groups(records: list[dict]) -> None:
    client = FakeClient(records)
    out = await analytics.top_groups_for_period(client, year=2026, month=5)
    assert out["ranking"][0] == {"group": "lockbit3", "victims": 2}


@pytest.mark.asyncio
async def test_group_timeline(records: list[dict]) -> None:
    client = FakeClient(records)
    out = await analytics.group_activity_timeline(client, name="lockbit3", year=2026)
    by_month = {row["month"]: row["victims"] for row in out["by_month"]}
    assert by_month[4] == 1
    assert by_month[5] == 2
    assert out["total_victims"] == 3
