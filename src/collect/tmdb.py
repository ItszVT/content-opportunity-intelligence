"""TMDB client and eligible-population collector.

TMDB is the master source (§6): every title enters the dataset here and no
other source may introduce one.

All eligibility rules are read from config/sampling.yaml. Nothing about the
sample is hardcoded in this file, so the frozen config remains the single
source of truth and cannot silently drift from the code.

Two pagination hazards this handles explicitly:

  1. Sorting /discover by popularity is unstable. Popularity shifts while
     you page, so titles duplicate across pages and others are never seen.
     We sort by release date instead and still dedupe on tmdb_id, because
     even a date sort has ties.

  2. /discover stops at page 500. If a vertical exceeds that, the snapshot
     is silently truncated, so we raise rather than freeze a partial
     population.

Run:
    python -m src.collect.tmdb anime --max-pages 2
    python -m src.collect.tmdb all
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator, Optional

import requests
import yaml
from dotenv import load_dotenv

from src.collect.cache import TTL_24H, DiskCache

load_dotenv()

API_ROOT = "https://api.themoviedb.org/3"
SAMPLING_CONFIG = Path("config/sampling.yaml")
MAX_DISCOVER_PAGES = 500  # TMDB hard limit
PAGE_SLEEP_SECONDS = 0.25


class TMDBAuthError(RuntimeError):
    pass


class PopulationTruncatedError(RuntimeError):
    """Raised when a vertical exceeds TMDB's 500-page discover ceiling."""


def load_sampling_config(path: Path = SAMPLING_CONFIG) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


class TMDBClient:
    """Thin, cached TMDB wrapper.

    The bearer token is sent as a header and is never part of the cache key,
    so it cannot reach a filename or a cached payload on disk.
    """

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.getenv("TMDB_BEARER_TOKEN")
        if not self.token:
            raise TMDBAuthError(
                "TMDB_BEARER_TOKEN is not set. Copy .env.example to .env and "
                "paste your TMDB API Read Access Token."
            )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
            }
        )
        self.cache = DiskCache("tmdb")

    def get(
        self, endpoint: str, params: dict, ttl: Optional[int] = TTL_24H
    ) -> dict:
        key = {"endpoint": endpoint, "params": params}
        hit = self.cache.get(key, ttl=ttl)
        if hit is not None:
            return hit

        response = self.session.get(f"{API_ROOT}{endpoint}", params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        self.cache.set(key, payload)
        return payload

    def discover_pages(self, endpoint: str, params: dict, max_pages: Optional[int] = None) -> Iterator[dict]:
        """Yield every /discover page, warning loudly if truncated."""
        page = 1
        total_pages = None

        while True:
            page_params = dict(params, page=page)
            payload = self.get(f"/discover/{endpoint}", page_params)

            if total_pages is None:
                total_pages = payload.get("total_pages", 1)
                total_results = payload.get("total_results", 0)
                if total_pages > MAX_DISCOVER_PAGES and max_pages is None:
                    raise PopulationTruncatedError(
                        f"{endpoint} query spans {total_pages} pages "
                        f"({total_results} results); TMDB serves only "
                        f"{MAX_DISCOVER_PAGES}. Narrow the filters before "
                        "freezing a population snapshot."
                    )

            yield payload

            limit = min(total_pages, max_pages or total_pages, MAX_DISCOVER_PAGES)
            if page >= limit:
                break
            page += 1
            time.sleep(PAGE_SLEEP_SECONDS)


def build_discover_params(vertical_cfg: dict, cfg: dict) -> dict:
    """Translate sampling.yaml into TMDB /discover query parameters."""
    endpoint = vertical_cfg["endpoint"]
    is_tv = endpoint == "tv"

    date_field = "first_air_date" if is_tv else "primary_release_date"
    sort_field = "first_air_date" if is_tv else "primary_release_date"

    params: dict[str, Any] = {
        "language": "en-US",
        "include_adult": str(bool(cfg.get("include_adult", False))).lower(),
        "vote_count.gte": cfg["min_vote_count"],
        f"{date_field}.gte": cfg["release_date_min"],
        f"{date_field}.lte": cfg["release_date_max"],
        # Stable ordering: popularity reorders itself mid-pagination.
        "sort_by": f"{sort_field}.desc",
    }

    if vertical_cfg.get("genres"):
        params["with_genres"] = ",".join(str(g) for g in vertical_cfg["genres"])

    if vertical_cfg.get("origin_country"):
        # Pipe = OR in TMDB's query grammar.
        params["with_origin_country"] = "|".join(vertical_cfg["origin_country"])

    return params


def normalise_result(raw: dict, endpoint: str, vertical: str) -> dict:
    """Map a TMDB result onto the §7 `titles` field names."""
    is_tv = endpoint == "tv"
    return {
        "vertical": vertical,
        "tmdb_id": raw["id"],
        "tmdb_endpoint": endpoint,
        "title_primary": raw["name"] if is_tv else raw["title"],
        "title_native": raw.get("original_name") if is_tv else raw.get("original_title"),
        "release_date": raw.get("first_air_date") if is_tv else raw.get("release_date"),
        "origin_country": raw.get("origin_country") or [],
        "genre_ids": raw.get("genre_ids") or [],
        "vote_average": raw.get("vote_average"),
        "vote_count": raw.get("vote_count"),
        "popularity": raw.get("popularity"),
    }


def is_eligible(record: dict, vertical_cfg: dict, cfg: dict) -> tuple[bool, str]:
    """Re-check eligibility client-side.

    The API filters already do this, but a silent parameter change or a TMDB
    behaviour change would otherwise pass unnoticed into a frozen snapshot.
    Returns (eligible, reason_if_not).
    """
    if not record["release_date"]:
        return False, "no_release_date"

    try:
        released = datetime.strptime(record["release_date"], "%Y-%m-%d").date()
    except ValueError:
        return False, "unparseable_release_date"

    lo = datetime.strptime(cfg["release_date_min"], "%Y-%m-%d").date()
    hi = datetime.strptime(cfg["release_date_max"], "%Y-%m-%d").date()
    if not (lo <= released <= hi):
        return False, "outside_release_window"

    if (record["vote_count"] or 0) < cfg["min_vote_count"]:
        return False, "below_min_vote_count"

    required_genres = vertical_cfg.get("genres") or []
    if required_genres and not set(required_genres) & set(record["genre_ids"]):
        return False, "genre_mismatch"

    allowed = vertical_cfg.get("origin_country")
    if allowed and not set(allowed) & set(record["origin_country"]):
        return False, "origin_mismatch"

    return True, ""


def fetch_eligible_population(
    vertical: str,
    client: Optional[TMDBClient] = None,
    cfg: Optional[dict] = None,
    max_pages: Optional[int] = None,
) -> tuple[list[dict], dict]:
    """Return (records, stats) for one vertical. Deduped on tmdb_id."""
    cfg = cfg or load_sampling_config()
    vertical_cfg = cfg["verticals"][vertical]
    client = client or TMDBClient()

    endpoint = vertical_cfg["endpoint"]
    params = build_discover_params(vertical_cfg, cfg)

    seen: dict[int, dict] = {}
    stats = {"pages": 0, "raw_results": 0, "duplicates": 0, "rejected": {}}

    for payload in client.discover_pages(endpoint, params, max_pages=max_pages):
        stats["pages"] += 1
        for raw in payload.get("results", []):
            stats["raw_results"] += 1
            record = normalise_result(raw, endpoint, vertical)

            ok, reason = is_eligible(record, vertical_cfg, cfg)
            if not ok:
                stats["rejected"][reason] = stats["rejected"].get(reason, 0) + 1
                continue

            if record["tmdb_id"] in seen:
                stats["duplicates"] += 1
                continue

            seen[record["tmdb_id"]] = record

    return list(seen.values()), stats


def year_bucket_counts(records: list[dict], cfg: dict) -> dict[str, int]:
    """Count records per year bucket. Counts only -- never titles (§22 day 3)."""
    counts = {label: 0 for label in cfg["release_year_buckets"]}
    counts["_outside_buckets"] = 0

    for record in records:
        year = int(record["release_date"][:4])
        for label, span in cfg["release_year_buckets"].items():
            if span["start"] <= year <= span["end"]:
                counts[label] += 1
                break
        else:
            counts["_outside_buckets"] += 1

    return counts


def _report(vertical: str, records: list[dict], stats: dict, cfg: dict) -> None:
    print(f"\n=== {vertical} ===")
    print(f"  pages fetched      {stats['pages']}")
    print(f"  raw results        {stats['raw_results']}")
    print(f"  duplicates dropped {stats['duplicates']}")
    print(f"  eligible (unique)  {len(records)}")

    if stats["rejected"]:
        print("  rejected:")
        for reason, n in sorted(stats["rejected"].items()):
            print(f"    {reason:<26} {n}")

    print("  by year bucket:")
    for label, n in year_bucket_counts(records, cfg).items():
        print(f"    {label:<26} {n}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull a TMDB eligible population.")
    parser.add_argument("vertical", help="a vertical name, or 'all'")
    parser.add_argument("--max-pages", type=int, default=None)
    args = parser.parse_args()

    cfg = load_sampling_config()
    client = TMDBClient()

    verticals = list(cfg["verticals"]) if args.vertical == "all" else [args.vertical]
    if args.vertical != "all" and args.vertical not in cfg["verticals"]:
        print(f"unknown vertical {args.vertical!r}; known: {list(cfg['verticals'])}")
        return 1

    by_vertical: dict[str, set[int]] = {}

    for vertical in verticals:
        records, stats = fetch_eligible_population(
            vertical, client=client, cfg=cfg, max_pages=args.max_pages
        )
        _report(vertical, records, stats, cfg)
        by_vertical[vertical] = {r["tmdb_id"] for r in records}

        if records:
            sample = records[0]
            missing = [k for k, v in sample.items() if v is None]
            if missing:
                print(f"  null fields in first record: {missing}")

    # A title with origin_country ['JP','US'] satisfies both the anime and the
    # anglophone allowlist. Report it rather than resolve it silently -- the
    # rule belongs in the plan, not buried in a collector.
    names = list(by_vertical)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            overlap = by_vertical[a] & by_vertical[b]
            if overlap:
                print(f"\n!! {len(overlap)} titles appear in both {a} and {b}")
                print("   Decide and log a rule before freezing the snapshot.")

    print("\nNote: counts only, by design. Do not inspect titles yet (§22).")
    return 0


if __name__ == "__main__":
    sys.exit(main())