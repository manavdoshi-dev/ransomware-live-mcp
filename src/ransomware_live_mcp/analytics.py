"""Computed analytics over ransomware.live victim records.

We do the counting here rather than asking the LLM to do it — small Python
aggregations are cheaper, deterministic, and immune to context-window loss
when the victim list is large.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

from .client import RansomwareLiveClient


def _now_year_month() -> tuple[int, int]:
    now = datetime.now(timezone.utc)
    return now.year, now.month


def _victim_date(record: dict[str, Any]) -> datetime | None:
    """Pick the most relevant date field on a victim record."""
    for key in ("attackdate", "discovered", "published"):
        raw = record.get(key)
        if not raw:
            continue
        try:
            # API returns ISO-8601 with offset.
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            continue
    return None


def _in_month(record: dict[str, Any], year: int, month: int) -> bool:
    dt = _victim_date(record)
    return dt is not None and dt.year == year and dt.month == month


def _filter_month(records: Iterable[dict[str, Any]], year: int, month: int) -> list[dict[str, Any]]:
    return [r for r in records if _in_month(r, year, month)]


async def _victims_year(client: RansomwareLiveClient, year: int) -> list[dict[str, Any]]:
    data = await client.get(f"/v2/victims/{year}")
    return data if isinstance(data, list) else []


async def _victims_month(
    client: RansomwareLiveClient, year: int, month: int
) -> list[dict[str, Any]]:
    data = await client.get(f"/v2/victims/{year}/{month}")
    return data if isinstance(data, list) else []


async def top_sector_for_period(
    client: RansomwareLiveClient,
    year: int | None = None,
    month: int | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    cur_y, cur_m = _now_year_month()
    year = year or cur_y
    month = month or cur_m

    records = await _victims_month(client, year, month)
    counts = Counter((r.get("activity") or "Unknown") for r in records)
    ranked = counts.most_common(limit)

    return {
        "year": year,
        "month": month,
        "total_victims": len(records),
        "top_sector": ranked[0][0] if ranked else None,
        "top_sector_count": ranked[0][1] if ranked else 0,
        "ranking": [{"sector": s, "victims": n} for s, n in ranked],
    }


async def top_country_for_period(
    client: RansomwareLiveClient,
    year: int | None = None,
    month: int | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    cur_y, cur_m = _now_year_month()
    year = year or cur_y
    month = month or cur_m

    records = await _victims_month(client, year, month)
    counts = Counter((r.get("country") or "Unknown") for r in records)
    ranked = counts.most_common(limit)

    return {
        "year": year,
        "month": month,
        "total_victims": len(records),
        "top_country": ranked[0][0] if ranked else None,
        "top_country_count": ranked[0][1] if ranked else 0,
        "ranking": [{"country": c, "victims": n} for c, n in ranked],
    }


async def top_groups_for_period(
    client: RansomwareLiveClient,
    year: int | None = None,
    month: int | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    cur_y, cur_m = _now_year_month()
    year = year or cur_y
    month = month or cur_m

    records = await _victims_month(client, year, month)
    counts = Counter((r.get("group") or "Unknown") for r in records)
    ranked = counts.most_common(limit)

    return {
        "year": year,
        "month": month,
        "total_victims": len(records),
        "ranking": [{"group": g, "victims": n} for g, n in ranked],
    }


async def group_activity_timeline(
    client: RansomwareLiveClient,
    name: str,
    year: int | None = None,
) -> dict[str, Any]:
    cur_y, _ = _now_year_month()
    year = year or cur_y

    records = await _victims_year(client, year)
    filtered = [r for r in records if (r.get("group") or "").lower() == name.lower()]

    months = Counter()
    for r in filtered:
        dt = _victim_date(r)
        if dt and dt.year == year:
            months[dt.month] += 1

    return {
        "group": name,
        "year": year,
        "total_victims": len(filtered),
        "by_month": [{"month": m, "victims": months.get(m, 0)} for m in range(1, 13)],
    }
