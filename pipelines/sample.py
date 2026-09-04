"""Draw the stratified sample of 240 (§8).

Procedure, from the frozen eligible population:
  - assign popularity_tercile within vertical
  - cross with year_bucket to give 12 cells per vertical
  - draw target_per_cell from each with a fixed seed
  - on shortfall, take all available and redistribute the deficit
    proportionally across cells with headroom, capped at max_per_cell

Determinism notes:

  Each cell is drawn with its own RNG, seeded from a hash of the global
  seed plus the cell's identity. A single global RNG consumed in sequence
  would work too, but then a shortfall in one cell shifts the random
  stream for every cell after it -- so an unrelated change to the
  population would silently redraw the whole sample. Per-cell seeding
  keeps each cell's draw independent and reproducible in isolation.

  Ties in popularity are broken by tmdb_id so tercile boundaries never
  depend on the order rows happen to sit in the parquet.

Run:
    python -m pipelines.sample --dry-run
    python -m pipelines.sample
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from src.collect.tmdb import load_sampling_config

FROZEN_DIR = Path("data/frozen")


def latest_population(frozen_dir: Path = FROZEN_DIR) -> Path:
    candidates = sorted(frozen_dir.glob("eligible_population_*.parquet"))
    if not candidates:
        raise FileNotFoundError(
            "No eligible population snapshot found. Run "
            "python -m pipelines.bootstrap_population first."
        )
    return candidates[-1]


def cell_rng(seed: int, vertical: str, bucket: str, tercile: int) -> np.random.Generator:
    """A deterministic RNG unique to one cell."""
    key = f"{seed}|{vertical}|{bucket}|{tercile}".encode("utf-8")
    digest = hashlib.sha256(key).digest()[:8]
    return np.random.default_rng(int.from_bytes(digest, "big"))


def assign_terciles(frame: pd.DataFrame, groups: int) -> pd.Series:
    """Split a vertical into equal-sized popularity groups, 1 = least popular.

    Rank-based rather than value-based (qcut), because popularity is heavily
    skewed and clustered; equal-width value bins would leave groups empty.
    """
    ordered = frame.sort_values(["popularity", "tmdb_id"], kind="mergesort")
    n = len(ordered)
    positions = np.arange(n)
    tercile = (positions * groups // n) + 1
    return pd.Series(tercile, index=ordered.index).astype(int)


def allocate(available: dict, target: int, max_per_cell: int) -> tuple[dict, list[dict]]:
    """Allocate draws across cells, redistributing shortfalls proportionally.

    Returns (allocation, log) where log records every redistribution.
    """
    allocation = {cell: min(target, n) for cell, n in available.items()}
    log: list[dict] = []

    deficit = sum(target - allocation[cell] for cell in available)
    if deficit == 0:
        return allocation, log

    short_cells = [c for c in available if allocation[c] < target]

    while deficit > 0:
        headroom = {
            cell: min(available[cell], max_per_cell) - allocation[cell]
            for cell in available
        }
        eligible = {c: h for c, h in headroom.items() if h > 0}
        if not eligible:
            log.append(
                {
                    "from_cells": ",".join(sorted(short_cells)),
                    "deficit_remaining": deficit,
                    "to_cell": None,
                    "amount": 0,
                    "note": "no headroom left; vertical under target",
                }
            )
            break

        # Weight by eligible population, not by headroom, per §8 step 8.
        weights = {c: available[c] for c in eligible}
        total_weight = sum(weights.values())

        # Largest-remainder apportionment keeps this deterministic.
        exact = {c: deficit * weights[c] / total_weight for c in eligible}
        floor = {c: int(np.floor(v)) for c, v in exact.items()}
        remainder = deficit - sum(floor.values())
        by_remainder = sorted(
            eligible, key=lambda c: (-(exact[c] - floor[c]), c)
        )
        for cell in by_remainder[:remainder]:
            floor[cell] += 1

        moved_any = False
        for cell in sorted(eligible):
            amount = min(floor[cell], headroom[cell])
            if amount <= 0:
                continue
            allocation[cell] += amount
            deficit -= amount
            moved_any = True
            log.append(
                {
                    "from_cells": ",".join(sorted(short_cells)),
                    "deficit_remaining": deficit,
                    "to_cell": cell,
                    "amount": amount,
                    "note": "proportional redistribution",
                }
            )

        if not moved_any:
            break

    return allocation, log


def sample_vertical(
    frame: pd.DataFrame, vertical: str, cfg: dict
) -> tuple[pd.DataFrame, list[dict]]:
    seed = cfg["seed"]
    groups = cfg["popularity_groups"]
    target = cfg.get("target_per_cell", 5)
    max_per_cell = cfg.get("max_per_cell", 8)
    buckets = list(cfg["release_year_buckets"])

    frame = frame.copy()
    frame["popularity_tercile"] = assign_terciles(frame, groups)

    cells = {
        f"{bucket}|{tercile}": frame[
            (frame["year_bucket"] == bucket) & (frame["popularity_tercile"] == tercile)
        ]
        for bucket in buckets
        for tercile in range(1, groups + 1)
    }
    available = {cell: len(sub) for cell, sub in cells.items()}

    allocation, log = allocate(available, target, max_per_cell)
    for entry in log:
        entry["vertical"] = vertical

    drawn = []
    for cell, sub in cells.items():
        n = allocation[cell]
        if n == 0:
            continue
        bucket, tercile = cell.split("|")
        rng = cell_rng(seed, vertical, bucket, int(tercile))
        # Sort before drawing so the candidate order is fixed regardless of
        # how the parquet happens to be ordered.
        ordered = sub.sort_values("tmdb_id", kind="mergesort")
        picks = rng.choice(len(ordered), size=n, replace=False)
        drawn.append(ordered.iloc[np.sort(picks)])

    sample = pd.concat(drawn, ignore_index=True)
    sample = sample.sort_values(
        ["year_bucket", "popularity_tercile", "tmdb_id"], kind="mergesort"
    ).reset_index(drop=True)
    sample["title_id"] = [f"{vertical}_{i + 1:03d}" for i in range(len(sample))]
    return sample, log


def draw_sample(population: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    order = cfg.get("vertical_precedence") or list(cfg["verticals"])
    samples, logs = [], []

    for vertical in order:
        subset = population[population["vertical"] == vertical]
        sample, log = sample_vertical(subset, vertical, cfg)
        samples.append(sample)
        logs.extend(log)

    combined = pd.concat(samples, ignore_index=True)
    combined["sampled_at"] = date.today().isoformat()

    columns = [
        "title_id",
        "vertical",
        "tmdb_id",
        "tmdb_endpoint",
        "title_primary",
        "title_native",
        "release_date",
        "year_bucket",
        "popularity_tercile",
        "popularity",
        "vote_average",
        "vote_count",
        "sampled_at",
    ]
    return combined[columns], pd.DataFrame(logs)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--population", type=Path, default=None)
    args = parser.parse_args()

    cfg = load_sampling_config()
    path = args.population or latest_population()
    population = pd.read_parquet(path)
    print(f"population: {path} ({len(population)} rows)")

    sample, redistribution = draw_sample(population, cfg)

    order = cfg.get("vertical_precedence") or list(cfg["verticals"])
    target_total = cfg["titles_per_vertical"]

    print("\nsample drawn:")
    for vertical in order:
        subset = sample[sample["vertical"] == vertical]
        flag = "" if len(subset) == target_total else "  << under target"
        print(f"  {vertical:<22} {len(subset):>3}{flag}")
    print(f"  {'TOTAL':<22} {len(sample):>3}")

    print("\ncell occupancy (bucket x tercile):")
    for vertical in order:
        subset = sample[sample["vertical"] == vertical]
        counts = (
            subset.groupby(["year_bucket", "popularity_tercile"])
            .size()
            .reindex(
                pd.MultiIndex.from_product(
                    [list(cfg["release_year_buckets"]), range(1, cfg["popularity_groups"] + 1)],
                    names=["year_bucket", "popularity_tercile"],
                ),
                fill_value=0,
            )
        )
        print(f"  {vertical}: {list(counts.values)}")

    if len(redistribution):
        print(f"\nredistributions: {len(redistribution)}")
        for _, row in redistribution.iterrows():
            print(
                f"  {row['vertical']}: +{row['amount']} to {row['to_cell']} "
                f"({row['note']})"
            )
    else:
        print("\nredistributions: none — every cell filled at target")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    sample_path = FROZEN_DIR / "sample_240_v1.csv"
    log_path = FROZEN_DIR / "sample_240_v1_redistribution_log.csv"

    if sample_path.exists():
        print(f"\n{sample_path} exists. Frozen files are never overwritten (§20).")
        return 1

    sample.to_csv(sample_path, index=False)
    redistribution.to_csv(log_path, index=False)
    print(f"\nwrote {sample_path}")
    print(f"wrote {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())