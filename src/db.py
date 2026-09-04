"""DuckDB warehouse: connection and schema.

The schema is §7 of the master plan, transcribed with its constraints
enforced by the database rather than by convention. Several §24 quality
checks are structural here -- duplicate title_id, position outside 1-10,
a rating outside 0-10 and a duplicate (title, query_type, position, date)
all fail at write time instead of being found in a later audit.

Two rules from §7 that the schema encodes deliberately:
  - pageviews is NULLABLE. NULL means unknown demand, never zero demand.
  - opportunity.score is NULLABLE. Any null component yields a null score.

The warehouse is rebuildable and gitignored. If deleting it loses
information, something that should be committed isn't (§6).
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb

WAREHOUSE_PATH = Path(os.getenv("WAREHOUSE_PATH", "data/warehouse.duckdb"))
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))

DATA_SUBDIRS = ("raw", "frozen", "snapshots", "outputs")

SCHEMA_SQL = """
-- One row per sampled title. Stable; written once at bootstrap.
CREATE TABLE IF NOT EXISTS titles (
    title_id           VARCHAR PRIMARY KEY,
    vertical           VARCHAR NOT NULL,
    tmdb_id            INTEGER NOT NULL UNIQUE,
    tmdb_endpoint      VARCHAR NOT NULL CHECK (tmdb_endpoint IN ('tv', 'movie')),
    imdb_id            VARCHAR,
    anilist_id         INTEGER,
    wiki_slug_en       VARCHAR,
    wiki_slug_ko       VARCHAR,
    wiki_slug_ja       VARCHAR,
    title_primary      VARCHAR NOT NULL,
    title_native       VARCHAR,
    release_date       DATE    NOT NULL,
    year_bucket        VARCHAR NOT NULL,
    popularity_tercile INTEGER NOT NULL CHECK (popularity_tercile BETWEEN 1 AND 3),
    resolution_method  VARCHAR NOT NULL,
    sampled_at         DATE    NOT NULL
);

-- Daily, append-only. popularity is stored as an H3 benchmark, never a feature.
CREATE TABLE IF NOT EXISTS tmdb_snapshot (
    title_id      VARCHAR   NOT NULL,
    observed_at   DATE      NOT NULL,
    collected_at  TIMESTAMP NOT NULL,
    vote_average  DOUBLE    NOT NULL CHECK (vote_average BETWEEN 0 AND 10),
    vote_count    INTEGER   NOT NULL,
    popularity    DOUBLE    NOT NULL,
    status        VARCHAR   NOT NULL,
    PRIMARY KEY (title_id, observed_at)
);

-- pageviews is nullable by design. NULL != 0 (§10).
CREATE TABLE IF NOT EXISTS pageviews_daily (
    title_id     VARCHAR NOT NULL,
    date         DATE    NOT NULL,
    collected_at DATE    NOT NULL,
    lang         VARCHAR NOT NULL CHECK (lang IN ('en', 'ko', 'ja')),
    pageviews    INTEGER,
    null_reason  VARCHAR CHECK (
        null_reason IN ('no_article', 'api_error', 'slug_unresolved')
    ),
    PRIMARY KEY (title_id, date, lang)
);

CREATE TABLE IF NOT EXISTS ratings_snapshot (
    title_id     VARCHAR NOT NULL,
    source       VARCHAR NOT NULL CHECK (source IN ('tmdb', 'imdb')),
    observed_at  DATE    NOT NULL,
    score_raw    DOUBLE  NOT NULL CHECK (score_raw BETWEEN 0 AND 10),
    vote_count   INTEGER NOT NULL,
    score_shrunk DOUBLE  CHECK (score_shrunk BETWEEN 0 AND 10),
    PRIMARY KEY (title_id, source, observed_at)
);

-- One row per SERP result. The PK is §24's duplicate check.
CREATE TABLE IF NOT EXISTS serp_results (
    title_id       VARCHAR NOT NULL,
    query_type     VARCHAR NOT NULL,
    query_string   VARCHAR NOT NULL,
    observed_at    DATE    NOT NULL,
    position       INTEGER NOT NULL CHECK (position BETWEEN 1 AND 10),
    domain         VARCHAR NOT NULL,
    result_title   VARCHAR NOT NULL,
    publisher_tier INTEGER NOT NULL CHECK (publisher_tier BETWEEN 0 AND 5),
    tier_matched   BOOLEAN NOT NULL,
    intent_match   INTEGER NOT NULL CHECK (intent_match BETWEEN 0 AND 3),
    format_score   INTEGER NOT NULL CHECK (format_score BETWEEN 0 AND 2),
    rubric_version INTEGER NOT NULL,
    PRIMARY KEY (title_id, query_type, position, observed_at)
);

CREATE TABLE IF NOT EXISTS competition (
    title_id          VARCHAR NOT NULL,
    query_type        VARCHAR NOT NULL,
    observed_at       DATE    NOT NULL,
    score             DOUBLE  NOT NULL CHECK (score BETWEEN 0 AND 100),
    ugc_share         DOUBLE  NOT NULL CHECK (ugc_share BETWEEN 0 AND 1),
    intent_gap        DOUBLE  NOT NULL CHECK (intent_gap BETWEEN 0 AND 1),
    publisher_ceiling INTEGER NOT NULL CHECK (publisher_ceiling BETWEEN 0 AND 5),
    n_results         INTEGER NOT NULL,
    PRIMARY KEY (title_id, query_type, observed_at)
);

-- The output. Every score carries its full date vector (§14).
CREATE TABLE IF NOT EXISTS opportunity (
    title_id           VARCHAR NOT NULL,
    computed_at        DATE    NOT NULL,
    observed_at_tmdb   DATE    NOT NULL,
    observed_at_wiki   DATE    NOT NULL,
    observed_at_serp   DATE    NOT NULL,
    observed_at_imdb   DATE,
    max_staleness_days INTEGER NOT NULL,
    demand_level_pct   DOUBLE  CHECK (demand_level_pct BETWEEN 0 AND 100),
    demand_momentum_pct DOUBLE CHECK (demand_momentum_pct BETWEEN 0 AND 100),
    reception_pct      DOUBLE  NOT NULL CHECK (reception_pct BETWEEN 0 AND 100),
    competition_pct    DOUBLE  CHECK (competition_pct BETWEEN 0 AND 100),
    score              DOUBLE  CHECK (score BETWEEN 0 AND 100),
    is_partial         BOOLEAN NOT NULL,
    rationale          VARCHAR NOT NULL,
    weights_version    INTEGER NOT NULL,
    PRIMARY KEY (title_id, computed_at, weights_version)
);
"""

TABLES = (
    "titles",
    "tmdb_snapshot",
    "pageviews_daily",
    "ratings_snapshot",
    "serp_results",
    "competition",
    "opportunity",
)


def ensure_dirs() -> None:
    """Create the data/ layout described in §6."""
    for sub in DATA_SUBDIRS:
        (DATA_DIR / sub).mkdir(parents=True, exist_ok=True)


def connect(path: Path | str | None = None, read_only: bool = False):
    """Open the warehouse. Creates it if absent."""
    target = Path(path) if path else WAREHOUSE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(target), read_only=read_only)


def init_schema(con) -> None:
    """Apply the schema. Idempotent -- safe to run on every pipeline start."""
    con.execute(SCHEMA_SQL)


def table_counts(con) -> dict[str, int]:
    return {
        t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLES
    }


if __name__ == "__main__":
    ensure_dirs()
    con = connect()
    init_schema(con)

    counts = table_counts(con)
    print(f"warehouse: {WAREHOUSE_PATH}")
    for table, n in counts.items():
        print(f"  {table:<18} {n:>6} rows")

    # Confirm the NULL != 0 rule is actually permitted by the schema, and
    # that the position guard actually bites.
    con.execute(
        "INSERT INTO pageviews_daily VALUES "
        "('_t', DATE '2026-01-01', DATE '2026-01-01', 'en', NULL, 'no_article')"
    )
    assert con.execute(
        "SELECT pageviews IS NULL FROM pageviews_daily WHERE title_id = '_t'"
    ).fetchone()[0]
    con.execute("DELETE FROM pageviews_daily WHERE title_id = '_t'")

    try:
        con.execute(
            "INSERT INTO serp_results VALUES "
            "('_t','review','x',DATE '2026-01-01',99,'d.com','t',3,true,2,1,1)"
        )
    except duckdb.ConstraintException:
        pass
    else:
        raise AssertionError("position check constraint did not fire")

    con.close()
    print("db.py: schema applied, constraints verified")