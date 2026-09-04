"""Sampling tests (§24).

The reproducibility claim in §32 -- "fixed seed reproduces the identical
240" -- is only meaningful if something checks it. That is this file.
"""

from __future__ import annotations

import pandas as pd
import pytest

from pipelines.sample import allocate, assign_terciles, draw_sample
from src.collect.tmdb import load_sampling_config


@pytest.fixture(scope="module")
def cfg() -> dict:
    return load_sampling_config()


def _population(cfg: dict, per_cell: int = 20) -> pd.DataFrame:
    """A synthetic population with plenty in every cell."""
    rows = []
    tmdb_id = 1
    for vertical, vcfg in cfg["verticals"].items():
        for bucket, span in cfg["release_year_buckets"].items():
            for i in range(per_cell * cfg["popularity_groups"]):
                rows.append(
                    {
                        "vertical": vertical,
                        "tmdb_id": tmdb_id,
                        "tmdb_endpoint": vcfg["endpoint"],
                        "title_primary": f"title {tmdb_id}",
                        "title_native": None,
                        "release_date": f"{span['start']}-06-01",
                        "year_bucket": bucket,
                        "popularity": float(i),
                        "vote_average": 7.0,
                        "vote_count": 500,
                    }
                )
                tmdb_id += 1
    return pd.DataFrame(rows)


def test_fixed_seed_reproduces_identical_sample(cfg):
    population = _population(cfg)
    first, _ = draw_sample(population, cfg)
    second, _ = draw_sample(population, cfg)
    pd.testing.assert_frame_equal(first, second)


def test_row_order_does_not_change_the_draw(cfg):
    """Shuffling the population must not change which titles are drawn."""
    population = _population(cfg)
    shuffled = population.sample(frac=1.0, random_state=99).reset_index(drop=True)

    a, _ = draw_sample(population, cfg)
    b, _ = draw_sample(shuffled, cfg)
    assert set(a["tmdb_id"]) == set(b["tmdb_id"])


def test_sample_size_per_vertical(cfg):
    population = _population(cfg)
    sample, _ = draw_sample(population, cfg)

    assert len(sample) == cfg["titles_per_vertical"] * len(cfg["verticals"])
    for vertical in cfg["verticals"]:
        subset = sample[sample["vertical"] == vertical]
        assert len(subset) == cfg["titles_per_vertical"]


def test_title_ids_are_unique(cfg):
    population = _population(cfg)
    sample, _ = draw_sample(population, cfg)
    assert sample["title_id"].is_unique
    assert sample["tmdb_id"].is_unique


def test_terciles_are_balanced(cfg):
    population = _population(cfg)
    subset = population[population["vertical"] == "anime"].copy()
    terciles = assign_terciles(subset, cfg["popularity_groups"])

    counts = terciles.value_counts()
    assert set(counts.index) == set(range(1, cfg["popularity_groups"] + 1))
    assert counts.max() - counts.min() <= 1


def test_allocation_sums_to_target_when_supply_is_ample():
    available = {f"cell_{i}": 50 for i in range(12)}
    allocation, log = allocate(available, target=5, max_per_cell=8)

    assert sum(allocation.values()) == 60
    assert log == []


def test_shortfall_is_redistributed_and_logged():
    available = {f"cell_{i}": 50 for i in range(12)}
    available["cell_0"] = 2  # 3 short of target

    allocation, log = allocate(available, target=5, max_per_cell=8)

    assert allocation["cell_0"] == 2
    assert sum(allocation.values()) == 60
    assert log, "a redistribution must be logged"
    assert sum(entry["amount"] for entry in log) == 3


def test_max_per_cell_is_respected():
    available = {f"cell_{i}": 50 for i in range(12)}
    available["cell_0"] = 0
    available["cell_1"] = 0
    available["cell_2"] = 0

    allocation, _ = allocate(available, target=5, max_per_cell=8)

    assert max(allocation.values()) <= 8


def test_under_target_is_reported_not_silently_accepted():
    """When supply genuinely cannot meet 60, the cap holds and it's logged."""
    available = {f"cell_{i}": 1 for i in range(12)}
    allocation, log = allocate(available, target=5, max_per_cell=8)

    assert sum(allocation.values()) == 12
    assert any(entry["to_cell"] is None for entry in log)