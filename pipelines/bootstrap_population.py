"""Freeze the eligible population snapshot (§8 steps 1-3).

Fetches every vertical from TMDB, resolves cross-vertical overlap by
precedence, and writes a dated parquet to data/frozen/ along with a
manifest.

Why this file is committed to data/frozen/: the seed alone does not make
the sample reproducible, because TMDB's underlying data changes daily. A
reviewer re-running the sampler months from now must draw from the same
population we drew from, which means that population has to be a committed
artifact rather than a live query (§8 step 3).

Run:
    python -m pipelines.bootstrap_population
    python -m pipelines.bootstrap_population --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from src.collect.tmdb import (
    TMDBClient,
    fetch_eligible_population,
    load_sampling_config,
    year_bucket_counts,
)

FROZEN_DIR = Path("data/frozen")


def assign_year_bucket(release_date: str, cfg: dict) -> str | None:
    year = int(release_date[:4])
    for label, span in cfg["release_year_buckets"].items():
        if span["start"] <= year <= span["end"]:
            return label
    return None


def apply_precedence(
    populations: dict[str, list[dict]], order: list[str]
) -> tuple[dict[str, list[dict]], list[dict]]:
    """Assign each tmdb_id to the first vertical in `order` that claims it.

    Returns (assigned, reassignments) where reassignments records every
    title that was dropped from a later vertical, so the decision is
    auditable rather than invisible.
    """
    claimed: dict[int, str] = {}
    assigned: dict[str, list[dict]] = {v: [] for v in order}
    reassignments: list[dict] = []

    for vertical in order:
        for record in populations.get(vertical, []):
            tmdb_id = record["tmdb_id"]
            if tmdb_id in claimed:
                reassignments.append(
                    {
                        "tmdb_id": tmdb_id,
                        "kept_in": claimed[tmdb_id],
                        "removed_from": vertical,
                        "origin_country": record["origin_country"],
                    }
                )
                continue
            claimed[tmdb_id] = vertical
            assigned[vertical].append(record)

    return assigned, reassignments


def config_fingerprint(path: Path) -> str:
    """Hash of the config that produced this snapshot."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run", action="store_true", help="report counts, write nothing"
    )
    args = parser.parse_args()

    cfg = load_sampling_config()
    order = cfg.get("vertical_precedence") or list(cfg["verticals"])

    missing = set(cfg["verticals"]) ^ set(order)
    if missing:
        print(f"vertical_precedence does not match verticals: {sorted(missing)}")
        return 1

    client = TMDBClient()
    populations: dict[str, list[dict]] = {}
    fetch_stats: dict[str, dict] = {}

    for vertical in order:
        records, stats = fetch_eligible_population(vertical, client=client, cfg=cfg)
        populations[vertical] = records
        fetch_stats[vertical] = stats
        print(f"{vertical:<22} fetched {len(records):>5}")

    assigned, reassignments = apply_precedence(populations, order)

    print(f"\nprecedence order: {' > '.join(order)}")
    if reassignments:
        print(f"overlap resolved: {len(reassignments)} titles reassigned")
        for vertical in order:
            n = sum(1 for r in reassignments if r["removed_from"] == vertical)
            if n:
                print(f"  removed from {vertical:<22} {n}")
    else:
        print("overlap resolved: none found")

    rows = []
    snapshot_date = date.today().isoformat()
    collected_at = datetime.now(timezone.utc).isoformat()

    for vertical in order:
        for record in assigned[vertical]:
            rows.append(
                {
                    **record,
                    "year_bucket": assign_year_bucket(record["release_date"], cfg),
                    "snapshot_date": snapshot_date,
                    "collected_at": collected_at,
                }
            )

    frame = pd.DataFrame(rows)

    print("\nfinal population, by vertical and year bucket:")
    for vertical in order:
        records = assigned[vertical]
        counts = year_bucket_counts(records, cfg)
        counts.pop("_outside_buckets", None)
        spread = "  ".join(f"{label}:{n}" for label, n in counts.items())
        print(f"  {vertical:<22} {len(records):>5}   {spread}")

    # Every cell needs enough titles to fill its quota; flag thin ones now.
    target = cfg.get("target_per_cell", 5)
    groups = cfg["popularity_groups"]
    print(f"\nthin-bucket check (target {target}/cell x {groups} terciles):")
    any_thin = False
    for vertical in order:
        counts = year_bucket_counts(assigned[vertical], cfg)
        counts.pop("_outside_buckets", None)
        for label, n in counts.items():
            if n < target * groups:
                print(f"  {vertical} / {label}: {n} titles, needs {target * groups}")
                any_thin = True
    if not any_thin:
        print("  none — every bucket can fill its cells")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    FROZEN_DIR.mkdir(parents=True, exist_ok=True)
    parquet_path = FROZEN_DIR / f"eligible_population_{snapshot_date}.parquet"
    manifest_path = FROZEN_DIR / f"eligible_population_{snapshot_date}.manifest.json"

    if parquet_path.exists():
        print(f"\n{parquet_path} already exists. Frozen files are never")
        print("overwritten (§20). Delete it deliberately if you must redraw.")
        return 1

    frame.to_parquet(parquet_path, index=False)

    manifest = {
        "snapshot_date": snapshot_date,
        "collected_at": collected_at,
        "sampling_config_sha256_16": config_fingerprint(Path("config/sampling.yaml")),
        "precedence_order": order,
        "total_titles": len(frame),
        "by_vertical": {v: len(assigned[v]) for v in order},
        "fetch_stats": fetch_stats,
        "reassignments": reassignments,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"\nwrote {parquet_path}  ({len(frame)} rows)")
    print(f"wrote {manifest_path}")
    print("\nCommit both. They are frozen artifacts and must never be edited.")
    return 0


if __name__ == "__main__":
    sys.exit(main())