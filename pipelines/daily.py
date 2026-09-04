"""Daily TMDB snapshot for the frozen 240 (§14, §24).

This is the highest-value automation in the project and the reason the
pipeline goes live before it is strictly needed (§23 step 5). TMDB ratings,
vote counts and popularity have no historical archive: a day that isn't
recorded is gone permanently, and the prospective validation in §15.2
depends on this series existing.

Design points:

  observed_at and collected_at are separate fields. observed_at is the date
  the source's state was observed; collected_at is when our code ran. They
  differ whenever a run spans midnight UTC or is re-run later, and §14 is
  explicit that collapsing them eventually records a lie.

  The cache key includes observed_at, so a re-run on the same day is free
  but a run on a new day can never be served yesterday's response. A plain
  24h TTL would blur that boundary.

  Quality checks fail the process with a non-zero exit. A cron that breaks
  silently is worse than no cron, because you go on trusting a series that
  stopped updating.

Currently TMDB only. Wikipedia pageviews join this pipeline once entity
resolution has produced a title_map.

Run:
    python -m pipelines.daily --dry-run
    python -m pipelines.daily
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from src.collect.cache import TTL_NEVER
from src.collect.tmdb import TMDBClient

FROZEN_SAMPLE = Path("data/frozen/sample_240_v1.csv")
SNAPSHOT_DIR = Path("data/snapshots")
REQUEST_SLEEP_SECONDS = 0.1
ROW_COUNT_TOLERANCE = 0.10


class QualityCheckFailure(RuntimeError):
    pass


def fetch_title_state(
    client: TMDBClient, tmdb_id: int, endpoint: str, observed_at: str
) -> dict:
    """Current state for one title. observed_at is part of the cache key."""
    path = f"/{endpoint}/{tmdb_id}"
    key = {"endpoint": path, "params": {"language": "en-US"}, "observed_at": observed_at}

    hit = client.cache.get(key, ttl=TTL_NEVER)
    if hit is not None:
        return hit

    for attempt in (1, 2):
        try:
            response = client.session.get(
                f"https://api.themoviedb.org/3{path}",
                params={"language": "en-US"},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            client.cache.set(key, payload)
            return payload
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(5)

    raise RuntimeError("unreachable")


def collect(sample: pd.DataFrame, client: TMDBClient) -> tuple[pd.DataFrame, list[dict]]:
    observed_at = datetime.now(timezone.utc).date().isoformat()
    collected_at = datetime.now(timezone.utc).isoformat()

    rows, failures = [], []

    for _, title in sample.iterrows():
        try:
            payload = fetch_title_state(
                client, int(title["tmdb_id"]), title["tmdb_endpoint"], observed_at
            )
        except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
            failures.append({"title_id": title["title_id"], "error": str(exc)})
            continue

        rows.append(
            {
                "title_id": title["title_id"],
                "observed_at": observed_at,
                "collected_at": collected_at,
                "vote_average": payload.get("vote_average"),
                "vote_count": payload.get("vote_count"),
                "popularity": payload.get("popularity"),
                "status": payload.get("status"),
            }
        )
        time.sleep(REQUEST_SLEEP_SECONDS)

    return pd.DataFrame(rows), failures


def previous_snapshot(snapshot_dir: Path, exclude: str) -> pd.DataFrame | None:
    paths = sorted(
        p for p in snapshot_dir.glob("tmdb_snapshot_*.parquet") if exclude not in p.name
    )
    return pd.read_parquet(paths[-1]) if paths else None


def run_quality_checks(
    frame: pd.DataFrame, sample: pd.DataFrame, failures: list[dict], previous: pd.DataFrame | None
) -> list[str]:
    """Return a list of failure messages. Empty means everything passed."""
    errors, warnings = [], []

    if frame.empty:
        return ["snapshot is empty"]

    if frame["title_id"].duplicated().any():
        errors.append("duplicate title_id in snapshot")

    unknown = set(frame["title_id"]) - set(sample["title_id"])
    if unknown:
        errors.append(f"{len(unknown)} title_id values not present in the frozen sample")

    bad_ratings = frame[~frame["vote_average"].between(0, 10)]
    if len(bad_ratings):
        errors.append(f"{len(bad_ratings)} rows with vote_average outside 0-10")

    if frame["observed_at"].max() > date.today().isoformat():
        errors.append("observed_at is in the future")

    if frame[["vote_count", "popularity", "status"]].isna().any().any():
        errors.append("null in a NOT NULL column (vote_count / popularity / status)")

    # A silent partial collection is the failure mode this guards against.
    if previous is not None:
        change = abs(len(frame) - len(previous)) / len(previous)
        if change > ROW_COUNT_TOLERANCE:
            errors.append(
                f"row count moved {change:.1%} from the previous snapshot "
                f"({len(previous)} -> {len(frame)}); tolerance is "
                f"{ROW_COUNT_TOLERANCE:.0%}"
            )

        merged = frame.merge(
            previous[["title_id", "vote_count"]],
            on="title_id",
            suffixes=("", "_prev"),
            how="inner",
        )
        dropped = merged[merged["vote_count"] < merged["vote_count_prev"]]
        if len(dropped):
            warnings.append(
                f"{len(dropped)} titles show a falling vote_count "
                "(possible source correction)"
            )

    if failures:
        share = len(failures) / (len(frame) + len(failures))
        message = f"{len(failures)} titles failed to collect ({share:.1%})"
        (errors if share > ROW_COUNT_TOLERANCE else warnings).append(message)

    for warning in warnings:
        print(f"  WARN  {warning}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="collect only N titles")
    args = parser.parse_args()

    if not FROZEN_SAMPLE.exists():
        print(f"{FROZEN_SAMPLE} not found. Run python -m pipelines.sample first.")
        return 1

    sample = pd.read_csv(FROZEN_SAMPLE)
    if args.limit:
        sample = sample.head(args.limit)

    print(f"collecting {len(sample)} titles...")
    client = TMDBClient()
    frame, failures = collect(sample, client)

    observed_at = frame["observed_at"].iloc[0] if len(frame) else date.today().isoformat()
    print(f"collected {len(frame)} rows, {len(failures)} failures, observed_at={observed_at}")

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    previous = previous_snapshot(SNAPSHOT_DIR, exclude=observed_at)

    print("quality checks:")
    errors = run_quality_checks(frame, sample, failures, previous)
    if errors:
        for error in errors:
            print(f"  FAIL  {error}")
        for failure in failures[:5]:
            print(f"        {failure['title_id']}: {failure['error'][:90]}")
        return 1
    print("  all passed")

    if args.dry_run:
        print("--dry-run: nothing written")
        return 0

    path = SNAPSHOT_DIR / f"tmdb_snapshot_{observed_at}.parquet"
    if path.exists():
        print(f"{path} already exists; snapshots are append-only, not rewritten.")
        return 0

    frame.to_parquet(path, index=False)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())