# PROJECT MASTER PLAN
## Content Opportunity Intelligence

**Version 1.2 — updated 2026-09-04**
**Status:** Freeze complete. V1 in progress — sample drawn and frozen, daily pipeline live.
**Last session:** 2026-09-04. See §30.1 for exactly where to resume.

> This is the single source of truth. When returning to this project, read §0, then **§30.1 (progress log — what has been done and what is next)**, then §30 for the checklist and §21 for phase context. Do not redesign decisions recorded in §29 unless a genuine methodological problem is identified — and if one is, follow §31.

---

## §0 — The project in 60 seconds

Entertainment websites decide what to write about based on what's popular. But popular is also where all the competition is, so their articles land on page four and nobody reads them.

This project scores 240 titles on **three separate things**: how many people want information about it, how well it was received, and how much has already been written. Combining those finds gaps that popularity alone hides.

It covers four categories — anime, K-drama, animated film, anglophone animation — to test whether they behave differently.

The output is a decision, not a chart: **five titles to write about this month, plus one obvious-looking title to skip, with the data behind each.**

The prediction was written down and timestamped before any data was collected, so it can't be revised after the fact.

---

# PART A — WHAT AND WHY

## §1 — Project overview

**The problem.** Content publishers in entertainment pick topics by popularity. Popularity conflates audience size with competitive saturation, so following it means entering the most crowded queries. A new or mid-sized publisher writing "Attack on Titan ending explained" competes with a dozen established publishers on that exact phrase and loses.

**The insight.** Popularity is three things fused together. Separated, they reveal a fourth state that is invisible when fused: *moderate but rising interest, positive reception, thin existing coverage.*

**Who would use it.** A content strategist or editor at an entertainment publication deciding a monthly editorial calendar. Secondarily, an SEO consultant advising such a publisher.

**The decision it supports.** "Which titles should we produce content about in the next 4–6 weeks, and which query angle for each?"

**Final output.** A ranked, explained list of content opportunities per vertical, plus a defended set of five recommendations and one explicit rejection.

## §2 — Objective and success definition

**Objective:** Build and validate a reproducible prioritisation model that identifies content opportunities not visible in popularity rankings, across four entertainment verticals, using only free data sources.

**The project succeeds if it can answer, with evidence:**

1. Does the Opportunity Score surface titles that popularity ranking misses? (H3)
2. Does the competition rubric agree with human judgment? (§15.3)
3. Do the four verticals show different opportunity distributions? (H1)
4. Would a content strategist act on the five recommendations?

**The project also succeeds if the answer to (1) is no** — provided that is reported clearly. A null result honestly reported is a valid outcome. A null result concealed is a failed project.

**The project fails if:** methodology is changed after seeing results; limitations are omitted; or the deliverable is a dashboard with no decision attached.

## §3 — Research questions and hypotheses

### Pre-registered — frozen 2026-09-03, cannot be changed after seeing data

**H1 — Cross-vertical opportunity gap**

> Among the four verticals, K-drama will show the largest median demand-to-competition gap.

*Measurement.* For each title *i*: `gap_i = demand_level_pct_i − competition_pct_i`, both percentile-ranked within vertical. Vertical statistic = median of `gap_i`, with 95% CI from 10,000 bootstrap resamples.

*Supported if:* K-drama's median gap is highest **and** its CI does not overlap the second-placed vertical's CI.
*Rejected if:* another vertical is highest with separable CIs.
*Inconclusive if:* CIs overlap — reported as "no separable difference," not as support.

*Exclusions fixed in advance:* titles with null pageviews (cannot be demand-ranked); titles with <5 usable SERP results. Both counts reported by vertical.

*Note:* H1 tests demand **level**, not momentum. A result on H1 says nothing about whether the momentum component has value.

**H2 — Demand and reception are weakly related**

> Within each vertical, Spearman correlation between demand level percentile and reception score will be below 0.3.

Reported per vertical with CIs. This is the claim that justifies scoring them separately. If correlation is high, the two components are redundant and that must be stated.

**H3 — The score is not a proxy for popularity**

> Spearman correlation between Opportunity Score rank and TMDB popularity rank will be below 0.7 within each vertical.

*Interpretation is continuous, not pass/fail.* Reported with CIs alongside **top-10 overlap** — how many of the ten highest-scoring titles are also in the ten most popular. Correlation near 1.0 with near-complete overlap means the premise has failed; that becomes the headline finding.

### Not pre-registered

Component weights, shrinkage constant, and SERP aggregation method are tuned against human-labelled difficulty (§15.3), **never against H1–H3 outcomes**. Tuning is frozen before H1–H3 are computed, and computed once.

## §4 — Scope

### Verticals — operational definitions

Each vertical is defined by a reproducible TMDB query, **not** a cultural or industry definition. This is stated in the methodology; no claim is made to capture any canonical definition.

| Vertical | TMDB endpoint | Filters |
|---|---|---|
| `anime` | `/discover/tv` | genre 16, origin JP |
| `kdrama` | `/discover/tv` | origin KR (no genre filter — defined by origin) |
| `animated_film` | `/discover/movie` | genre 16 |
| `anglophone_animation` | `/discover/tv` | genre 16, origin in [US, CA, GB, IE, AU, NZ] |

*Why `anglophone_animation` and not `western_animation`:* an exclusion rule ("not JP/KR/CN") silently admits French, Spanish and Indian animation. An allowlist says exactly what it captures. Continental European animation is out of scope for v1 — a stated boundary, not an oversight.

### Inclusion / exclusion

| Rule | Value |
|---|---|
| Release date | 2015-01-01 to 2026-08-31 (closed window) |
| Minimum votes | TMDB `vote_count >= 100` |
| Adult content | Excluded |
| Wikipedia article | **Not required** — availability is a feature, never a filter |
| Sample | 60 per vertical, 240 total |

### Query types (frozen before collection)

Vertical-specific, because search intent differs by audience:

| Vertical | Query types |
|---|---|
| `anime` | review, ending explained, watch order, characters |
| `kdrama` | review, ending explained, cast, where to watch |
| `animated_film` | review, ending explained, box office, characters |
| `anglophone_animation` | review, best episodes, characters, watch order |

Query string format: `{title_primary} {query_type}`, stored verbatim.

### Geography

English demand primary. Korean and Japanese Wikipedia collected as secondary signals; used descriptively, not in the score for v1.

### Explicitly out of scope

- Live-action non-Korean content
- Paid SERP data; Google SERP specifically
- Commercial use (TMDB free tier is non-commercial only)
- Continental European animation
- Social listening beyond optional Reddit in a later version
- **Any claim that the score predicts traffic**

---

# PART B — DATA

## §5 — Data sources

### 5.1 TMDB — master source

| | |
|---|---|
| **What** | Title metadata, ratings, vote counts, status, popularity, watch providers |
| **Why** | The only source with one consistent schema across all four verticals |
| **Access** | Free Developer key, instant approval. `Bearer` token or `api_key` param |
| **Fields** | `id`, `name`/`title`, `original_name`, `first_air_date`/`release_date`, `origin_country`, `genre_ids`, `vote_average`, `vote_count`, `popularity`, `status`, `external_ids.imdb_id` |
| **Historical?** | **No** — current state only |
| **Cadence** | Daily snapshot |
| **Rate limits** | Old hard limit removed; generous soft limiting. Cache and you won't approach it |
| **Problems** | `popularity` is undocumented and proprietary — stored, never used as a feature |
| **Caching** | Disk cache keyed on endpoint+params hash; TTL 24h for discover, indefinite for static metadata |
| **Missing data** | A title missing from TMDB is not eligible by definition — no missing-data case |
| **Obligation** | Attribution required: *"This product uses the TMDB API but is not endorsed or certified by TMDB."* In dashboard footer and README |

### 5.2 Wikipedia Pageviews — demand

| | |
|---|---|
| **What** | Daily pageviews per article per language |
| **Why** | The **only** input with full historical retrieval. Free, keyless, absolute counts |
| **Access** | `https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/all-access/user/{article}/daily/{start}/{end}` |
| **Fields** | `article`, `timestamp`, `views` |
| **Historical?** | **Yes** — back to 2015 |
| **Cadence** | Daily; backfillable |
| **Rate limits** | Courtesy limit ~200 req/s; set a descriptive `User-Agent` |
| **Problems** | Pageviews ≠ search volume. Redirects and disambiguation pages. Slug changes over time |
| **Caching** | Cache by (slug, lang, date range) |
| **Missing data** | `pageviews = NULL` with `null_reason`. **Never 0.** See §10 |

### 5.3 IMDb non-commercial datasets — second rating

| | |
|---|---|
| **What** | `title.ratings.tsv.gz`, `title.basics.tsv.gz` |
| **Why** | Independent second rating; covers animation and film better than anime-specific sources |
| **Access** | Direct download, no key |
| **Fields** | `tconst`, `averageRating`, `numVotes`, `titleType`, `startYear` |
| **Historical?** | No — current state only |
| **Cadence** | Weekly download |
| **Problems** | Large files; join depends on TMDB providing `imdb_id` |
| **Caching** | Download, filter to sample `tconst`s, discard the rest |
| **Missing data** | `imdb_id` null → reception computed from TMDB alone, flagged |

### 5.4 AniList — anime enrichment only

| | |
|---|---|
| **What** | Season, studio, format, independent score |
| **Why** | Anime-specific context TMDB lacks |
| **Access** | GraphQL, free, no key |
| **Historical?** | No |
| **Cadence** | Weekly |
| **Rate limits** | ~90 req/min |
| **Problems** | Matching to TMDB is fuzzy — romaji vs. English vs. native |
| **Missing data** | Enrichment only; absence never blocks a score |

### 5.5 `ddgs` metasearch — competition

| | |
|---|---|
| **What** | Top 10 organic results per query: title, URL, snippet |
| **Why** | The only genuinely free keyless SERP source |
| **Access** | `pip install ddgs` |
| **Historical?** | **No — no SERP archive exists anywhere.** This drives the entire validation design |
| **Cadence** | Fortnightly (rate-limited). This is the staleness bottleneck |
| **Rate limits** | Aggressive throttling. 3–5s jittered sleep; expect 5–10% failures needing retry |
| **Problems** | It is a scraper, not an API. **Not Google** — results differ. Called "observed SERP competition" throughout |
| **Caching** | Cache by query string hash + date. Never re-fetch within a collection window |
| **Missing data** | <5 results → excluded from H1, flagged |

### 5.6 Google Trends (pytrends) — validation only

Used on a 40–50 title subset to establish that Wikipedia pageviews correlate with search interest. **Never a scoring input.** Unofficial, breaks periodically, requires anchor-term normalisation if used comparatively.

## §6 — Data architecture

### Master source

**TMDB is the master.** Every title enters the dataset via TMDB and receives an internal `title_id`. All other sources attach to that ID. No source other than TMDB can introduce a title.

### Flow

```
TMDB /discover  →  eligible population snapshot (frozen, committed)
                        ↓  stratified sample, fixed seed
                   sample_240 (frozen, committed)
                        ↓  entity resolution
                   title_map  ──┬── wiki_slug (en/ko/ja)
                                ├── imdb_id
                                └── anilist_id
                        ↓
   ┌────────────┬──────────────┬──────────────┬─────────────┐
   │ tmdb       │ pageviews    │ ratings      │ serp        │
   │ snapshot   │ daily        │ snapshot     │ results     │
   │ (daily)    │ (daily)      │ (weekly)     │ (fortnightly)│
   └────────────┴──────────────┴──────────────┴─────────────┘
                        ↓  each carries its own observation date
                   feature tables (demand / reception / competition)
                        ↓  within-vertical percentile
                   opportunity score  →  recommendations
```

### Dataset layers — strictly separated

| Layer | Path | Committed? | Description |
|---|---|---|---|
| **Raw** | `data/raw/` | No | Exact API responses, cached, never edited |
| **Frozen** | `data/frozen/` | **Yes** | Population snapshot, sample list, title_map. Never overwritten |
| **Snapshots** | `data/snapshots/` | **Yes** | Dated parquet, append-only, the time series |
| **Warehouse** | `data/warehouse.duckdb` | No | Rebuilt from frozen + snapshots by a single command |
| **Outputs** | `data/outputs/` | Yes | Scored results per run, dated |

**Rule:** the warehouse must be fully reconstructible from committed files. If deleting it loses information, something committed is missing.

## §7 — Data schema

Field flags: **F** = model feature · **B** = benchmark/sampling only · **D** = descriptive

### `titles` — one row per sampled title, stable

| Field | Type | Source | Null? | Flag | Meaning |
|---|---|---|---|---|---|
| `title_id` | str | internal | No | — | PK, `{vertical}_{nnn}` |
| `vertical` | cat | internal | No | F | One of four |
| `tmdb_id` | int | TMDB | No | — | |
| `tmdb_endpoint` | str | TMDB | No | — | `tv` or `movie` |
| `imdb_id` | str | TMDB | Yes | — | `tconst` |
| `anilist_id` | int | AniList | Yes | — | Anime only |
| `wiki_slug_en` | str | resolution | Yes | — | Null = no article |
| `wiki_slug_ko` | str | resolution | Yes | — | |
| `wiki_slug_ja` | str | resolution | Yes | — | |
| `title_primary` | str | TMDB | No | — | Display + query construction |
| `title_native` | str | TMDB | Yes | D | |
| `release_date` | date | TMDB | No | B | |
| `year_bucket` | cat | derived | No | B | Sampling stratum |
| `popularity_tercile` | int | derived | No | B | Stratum, fixed at draw |
| `resolution_method` | cat | internal | No | D | `auto`/`manual`/`unresolved` |
| `sampled_at` | date | internal | No | — | |

### `tmdb_snapshot` — daily, append-only

| Field | Type | Null? | Flag | Meaning |
|---|---|---|---|---|
| `title_id` | str | No | — | |
| `observed_at` | date | No | — | |
| `collected_at` | timestamp | No | — | When the request ran |
| `vote_average` | float | No | F | 0–10 |
| `vote_count` | int | No | F | Delta = audience **activity** proxy |
| `popularity` | float | No | **B** | Benchmark for H3 only. Never a feature |
| `status` | cat | No | F | Segmentation variable |

### `pageviews_daily`

| Field | Type | Null? | Flag | Meaning |
|---|---|---|---|---|
| `title_id` | str | No | — | |
| `date` | date | No | — | `data_as_of` |
| `collected_at` | date | No | — | |
| `lang` | cat | No | — | en/ko/ja |
| `pageviews` | int | **Yes** | F | **NULL ≠ 0** |
| `null_reason` | cat | Yes | D | `no_article`/`api_error`/`slug_unresolved` |

### `ratings_snapshot`

| Field | Type | Null? | Flag |
|---|---|---|---|
| `title_id` | str | No | — |
| `source` | cat | No | — |
| `observed_at` | date | No | — |
| `score_raw` | float | No | F |
| `vote_count` | int | No | F |
| `score_shrunk` | float | No | F |

### `serp_results` — one row per result

| Field | Type | Null? | Flag |
|---|---|---|---|
| `title_id` | str | No | — |
| `query_type` | cat | No | — |
| `query_string` | str | No | D |
| `observed_at` | date | No | — |
| `position` | int | No | F |
| `domain` | str | No | F |
| `result_title` | str | No | D |
| `publisher_tier` | int | No | F |
| `tier_matched` | bool | No | D |
| `intent_match` | int | No | F |
| `format_score` | int | No | F |
| `rubric_version` | int | No | D |

### `competition` — per title × query_type

`title_id`, `query_type`, `observed_at`, `score` (0–100), `ugc_share`, `intent_gap`, `publisher_ceiling`, `n_results`

### `opportunity` — the output

| Field | Type | Null? | Meaning |
|---|---|---|---|
| `title_id` | str | No | |
| `computed_at` | date | No | |
| `observed_at_tmdb` | date | No | ← date vector |
| `observed_at_wiki` | date | No | |
| `observed_at_serp` | date | No | |
| `observed_at_imdb` | date | Yes | |
| `max_staleness_days` | int | No | Scoring aborts above tolerance |
| `demand_level_pct` | float | Yes | |
| `demand_momentum_pct` | float | Yes | |
| `reception_pct` | float | No | |
| `competition_pct` | float | Yes | |
| `score` | float | **Yes** | Null if any component null |
| `is_partial` | bool | No | True → excluded from rankings |
| `rationale` | str | No | Generated sentence |
| `weights_version` | int | No | |

### Non-negotiable rules

1. `NULL` never becomes `0`
2. Any null component → null score, `is_partial = True`
3. `popularity` stored, never a feature (H3 tests against it)
4. Every score records its full date vector
5. Scoring aborts if `max_staleness_days` > tolerance

## §8 — Sampling methodology

**Frozen 2026-09-03. Seed `20260903`.**

**Procedure:**

1. Query TMDB `/discover` per vertical with §4 filters, paginating fully.
2. Apply eligibility: release window, `vote_count >= 100`, not adult.
3. **Save the complete eligible population** to `data/frozen/eligible_population_{date}.parquet` and commit. *The seed alone does not guarantee reproducibility — TMDB's data changes.*
4. Assign `year_bucket`: [2015–2017], [2018–2020], [2021–2023], [2024–2026].
5. Assign `popularity_tercile` within vertical: split into 3 by TMDB popularity.
6. 4 buckets × 3 terciles = **12 cells**, target **5 per cell** = 60.
7. Random sample within each cell using the fixed seed.
8. **Shortfall:** if a cell has <5 eligible, take all, then redistribute the deficit **proportionally across remaining cells weighted by eligible count**, capped at `max_per_cell = 8`. Log every redistribution (cell, deficit, destination).
9. Save `data/frozen/sample_240_v1.csv` and commit.

*Why terciles not deciles:* 10 deciles × 4 buckets = 40 cells for 60 titles. Most cells would be empty or singletons. 12 cells at 5 each holds.

*Why proportional redistribution:* dumping deficit into the largest cell concentrates the sample in one release period and defeats stratification.

## §9 — Entity resolution

**Order matters — each step uses IDs from the previous.**

**Step 1 — IMDb.** TMDB `/external_ids` returns `imdb_id` directly. Near-100% for film, lower for TV. No fuzzy matching needed.

**Step 2 — Wikipedia (English).** In order, stopping at first success:
1. Wikidata via TMDB external IDs where available
2. Wikipedia search API on `title_primary` + release year, accept exact title match
3. Search on `title_primary` alone, accept if the article's Wikidata entity has an instance-of matching TV series / film / anime
4. Otherwise → `manual_review`

Reject disambiguation pages. Follow redirects and store the **canonical** slug.

**Step 3 — Wikipedia (ko/ja).** Via Wikidata sitelinks from the resolved English entity. If no English article, attempt direct search. Null is acceptable and expected.

**Step 4 — AniList (anime only).** GraphQL search on `title_primary`, then `title_native`. Accept if release year matches ±1 and normalised title similarity ≥ 0.85. Otherwise manual.

**Ambiguity handling.** Anything not auto-resolved goes to `data/frozen/manual_review.csv` with candidates listed. Resolved by hand, committed, never re-run automatically.

**Known hard cases:** season splits (TMDB "Season 2" vs. separate Wikipedia articles for each cour); anime with different English/romaji titles; K-dramas with multiple romanisations; films sharing a title with a TV series.

**Report:** auto-match rate per source **per vertical**. The variation is itself a finding — expect Wikipedia coverage to differ materially by vertical, which speaks directly to §10.

---

# PART C — METHODOLOGY

## §10 — Demand

### Two distinct quantities

| Quantity | Definition | Used in |
|---|---|---|
| **Demand level** | Mean daily English pageviews over trailing 90 days | H1, Opportunity Score |
| **Demand momentum** | `(mean last 90d − mean prior 90d) / mean prior 90d` | Opportunity Score, historical validation |

Momentum requires 180 days of history. Titles released <180 days ago get `demand_momentum = NULL` and a partial score.

### Language handling

English is the scoring signal. Korean and Japanese are collected and reported descriptively (a K-drama with high `ko` and low `en` pageviews is domestically strong but internationally undiscovered — interesting, but not in the v1 score).

### Missing data — the critical rule

`pageviews = NULL`, never `0`. No Wikipedia article means *unknown demand*, not *no demand*.

**Why this matters more than it looks:** titles without Wikipedia articles are disproportionately newer, smaller, and less internationally known — **exactly the population the project's thesis identifies as likely opportunities.** Coding them as zero, or dropping them, would systematically remove the findings from the dataset.

Handling: partial score on available components, `is_partial = True`, displayed in a separate dashboard panel, excluded from rankings and from H1.

### Fallback: audience activity

For titles without pageviews, `vote_count` delta between TMDB snapshots gives a coarse signal.

**Named "audience activity," not demand.** Rising vote counts mean people are *engaging* — voting requires an account and deliberate action. Most people who watch or search a title never rate it. It is displayed as a labelled secondary indicator, **never substituted into `demand_level_pct`**, and titles using it remain `is_partial = True`.

## §11 — Audience reception

Named *reception*, not *quality* — ratings measure how an audience responded, which a passionate niche fandom can inflate.

### Bayesian shrinkage

For each source *s* and title *i* in vertical *v*:

```
score_shrunk = (n_i / (n_i + m_v)) * R_i  +  (m_v / (n_i + m_v)) * C_v
```

Where:
- `R_i` = raw rating, `n_i` = vote count
- `C_v` = **vertical** mean rating (not global — everything else is within-vertical)
- `m_v` = shrinkage constant = **median vote count within vertical**

*Why median vote count:* a title with typical vote volume is pulled halfway to the vertical mean; a title with 10× the median barely moves; one with a tenth moves most of the way. Principled and defensible without tuning.

`m_v` is configurable and reported under sensitivity analysis (§17).

### Composite reception score

```
reception_raw = mean(score_shrunk_tmdb, score_shrunk_imdb)     # both on 0–10
```

If `imdb_id` is null, TMDB alone, flagged `single_source = True`.

**Cross-source agreement:** `|score_shrunk_tmdb − score_shrunk_imdb|`. Titles with disagreement > 1.0 are flagged and reported — a data-quality signal, not a score penalty.

`reception_pct` = percentile rank of `reception_raw` within vertical.

## §12 — Observed SERP competition

Named **observed** throughout: results come from a metasearch proxy, not Google.

### Collection

For each title, for each of its 4 vertical-specific query types: query `{title_primary} {query_type}`, retrieve top 10, sleep 3–5s jittered, cache by query hash + date. Retry failures once after 60s.

### Per-result score (0–10)

```
result_score = publisher_tier + intent_match + format_score
```

**`publisher_tier` (0–5)** — from `config/publisher_tiers.yaml` v1, frozen before collection:

| Band | Definition |
|---|---|
| 5 | Major established editorial publisher |
| 4 | Strong specialist publisher |
| 3 | Established niche publisher / high-traffic blog |
| 2 | Database, reference, or high-authority wiki |
| 1 | UGC, forum, video platform |
| 0 | Low authority or irrelevant |

Unmatched domains default to **3** (conservative — assumes competition exists). `tier_matched = False` logged for audit.

*Renamed from "authority":* this is an assigned tier, not a measured domain authority metric.

*Fandom decision (made in advance):* Fandom is reference content but carries authority far beyond a typical wiki and often holds 3+ top-10 slots in animation verticals. Scoring it tier 1 would systematically understate competition there. Assigned **tier 2**; SERPs with 3+ Fandom results flagged.

**`intent_match` (0–3)** — does the result actually answer *this* query?

| Score | Condition |
|---|---|
| 3 | Query modifier appears in result title (exact or close variant) |
| 2 | Semantic equivalent present ("finale breakdown" for "ending explained") |
| 1 | Title mentions the show but not the intent |
| 0 | Neither |

*This is the axis result-count metrics cannot see.* A tier-5 publisher ranking with a generic page (intent 1) is a materially weaker competitor than a tier-3 site with a purpose-built article (intent 3).

**`format_score` (0–2)** — 2 = dedicated article · 1 = listicle/roundup · 0 = wiki, database, thread, video. Inferred from domain and title patterns.

### Aggregation to a query-level score

Position weight: `w_p = 1 / log2(p + 1)` for p = 1..10.

```
comp_raw  = Σ (result_score_p × w_p)
comp_max  = 10 × Σ w_p
score     = 100 × comp_raw / comp_max
```

**0–100, higher = harder to enter.**

### Reported sub-metrics

- **`ugc_share`** — proportion of top 10 at tier 1
- **`intent_gap`** — proportion with `intent_match ≤ 1`
- **`publisher_ceiling`** — max tier in top 3

These are shown as chips beside each title because they're individually interpretable in a way the composite isn't.

### Aggregation across query types — tested, not assumed

Three candidates:

| Method | Rationale |
|---|---|
| **Minimum** | One viable entry point justifies coverage |
| **Median** | Typical difficulty across angles |
| **Weighted mean** | Weighted by query type's expected search volume |

Each is compared against the human-labelled difficulty ratings (§15.3); the best-aligned is adopted and the comparison reported.

**Constraint stated explicitly:** with no historical SERPs, these cannot be tested against future traffic — only against human judgment. The minimum could overstate opportunity if the one easy angle has negligible search volume, and this limitation is documented.

Whichever wins, the **winning query type is surfaced** in the recommendation: "write the ending explainer, not the review."

## §13 — Opportunity Score

### Formula

All inputs percentile-ranked **within vertical**, 0–100:

```
opportunity_score =
      w_level    × demand_level_pct
    + w_momentum × demand_momentum_pct
    + w_reception× reception_pct
    + w_comp     × (100 − competition_pct)
```

Note `(100 − competition_pct)`: high competition reduces opportunity.

Weights sum to 1. Defaults in `config/weights.yaml`:

| Weight | Default | Rationale |
|---|---|---|
| `w_level` | 0.25 | Audience must exist |
| `w_momentum` | 0.25 | Direction matters as much as size |
| `w_reception` | 0.20 | Necessary but least differentiating |
| `w_comp` | 0.30 | The signal others don't have |

**Decision required — but recommended:** these defaults are a judgment call. Recommended approach: keep them, and let §17 sensitivity analysis demonstrate how much they matter rather than pretending they were derived.

### Missing components

| Missing | Result |
|---|---|
| `demand_level` (no Wikipedia) | `score = NULL`, `is_partial = True` |
| `demand_momentum` (<180d history) | `score = NULL`, `is_partial = True` |
| `competition` (<5 results) | `score = NULL`, `is_partial = True` |
| `imdb` rating | Score computed, `single_source = True` |

**Partial-score titles are never imputed and never ranked against complete ones.** They appear in a dedicated dashboard panel with what *is* known, so a strategist can still act on them with eyes open.

### Staleness guard

```python
staleness = max(computed_at - d for d in observation_dates if d is not None)
if staleness.days > STALENESS_TOLERANCE_DAYS:
    raise StaleInputError(...)
```

**Decision required — recommended: 21 days.** Rationale: SERP refresh is fortnightly, so 21 allows one missed cycle before refusing. Configurable in `config/settings.yaml`.

### Rationale text

Each score generates a sentence for the Explorer, e.g.:

> "Not among the most popular titles in its vertical (popularity percentile 38), but demand is growing (+68% over 90 days), reception is strong (8.4 shrunk), and the 'ending explained' SERP is 40% forum content with no dedicated article in the top 5. Best entry angle: ending explained."

## §14 — Observation dates and snapshots

### Why separate dates per source

Sources refresh at different cadences: TMDB daily, Wikipedia daily (backfillable), IMDb weekly, SERP fortnightly. **A single `snapshot_date` per row will eventually be a lie** — you would build a "September score" from September ratings and August SERPs and record it as one measurement. That is precisely the leakage the project claims to avoid.

### Three distinct timestamps

| Field | Meaning | Example |
|---|---|---|
| `collected_at` | When our code ran the request | 2026-09-03 03:14 UTC |
| `data_as_of` | The date the value describes | 2026-09-01 (pageviews for Sept 1) |
| `observed_at` | The date the source's state was observed | 2026-09-03 |

For point-in-time sources (Wikipedia) `data_as_of` is the meaningful one. For current-state sources (TMDB, IMDb, SERP) `observed_at` is, and `data_as_of` is undefined — you cannot know when the rating "became" that value.

### Snapshot record

Every scoring run stores the full vector, not a single date:

```json
{
  "title_id": "kdrama_017",
  "computed_at": "2026-09-03",
  "observed_at": {
    "tmdb": "2026-09-03",
    "wikipedia": "2026-09-02",
    "serp": "2026-08-19",
    "imdb": "2026-09-01"
  },
  "max_staleness_days": 15,
  "weights_version": 1,
  "rubric_version": 1
}
```

This makes the leakage claim **enforceable in code**, not merely asserted in a document.

---

# PART D — VALIDATION

## §15 — Validation plan

### 15.1 Historical demand validation

**Testing:** does demand momentum have predictive value?
**Data:** Wikipedia pageviews only — the sole input with full history.
**Procedure:** pick a cutoff (e.g. 2026-03-01). Compute momentum using only data ≤ cutoff. Measure demand level change over the following 90 days. Correlate.
**Metric:** Spearman correlation with CI, per vertical.
**Strong result:** positive correlation with CI excluding zero.
**Weak result:** momentum is noise; the `w_momentum` component is unjustified and must be reported as such.
**Cannot claim:** that the *full Opportunity Score* is validated. Only the demand component is tested here.

### 15.2 Prospective validation

**Testing:** do high-scoring titles subsequently outperform?
**Procedure:** freeze scores and recommendations at project start with a timestamp, commit them, wait 8–10 weeks, measure subsequent demand change for top quartile vs. bottom quartile.
**Metric:** difference in median demand growth, with bootstrap CI.
**Strong result:** top quartile grows measurably more.
**Weak result:** reported plainly. The score may still be useful as a prioritisation tool without being predictive — but that must be stated, not implied.
**Cannot claim:** traffic prediction. Demand growth ≠ article performance.

### 15.3 SERP rubric validation

**Testing:** does the automated competition score agree with human judgment?
**Data:** 40 SERPs, stratified 10 per vertical, hand-labelled 1–5 on "how hard to break into" **before** viewing automated scores.
**Metric:** Spearman with **confidence interval and sample size**, interpreted continuously — not passed/failed against a threshold. (Target ~0.6 as an expectation, not a gate.)
**Also used for:** selecting the aggregation method (§12).
**Cannot claim:** population-level estimates. This validates the rubric, not the dataset.

### 15.4 Sensitivity analysis

See §17.

### 15.5 Cross-source agreement

**Testing:** are the inputs internally consistent?
- TMDB vs. IMDb shrunk ratings — correlation and mean absolute difference
- Wikipedia pageviews vs. Google Trends on 40–50 titles — correlation
**Weak result on Trends:** the demand proxy is questionable and this must be prominent in limitations, not buried.

## §16 — Backtest and leakage

### What can and cannot be reconstructed

| Input | Historical? | Consequence |
|---|---|---|
| Wikipedia pageviews | **Yes** | Can be validated historically |
| TMDB rating / vote count | No | Cannot |
| TMDB popularity | No | Cannot |
| IMDb rating | No | Cannot |
| SERP results | **No archive exists** | Cannot |

**Therefore a full historical backtest of the Opportunity Score is impossible.** Not difficult — impossible. Two of three components have no historical record.

### Rules

1. **Never invent historical values.** Do not use today's rating as a proxy for a past rating.
2. **Never compute a historical Opportunity Score.** Only the demand component is backtestable.
3. Any historical analysis filters on `data_as_of <= cutoff`, enforced in code, not by care.

### Prospective validation set

1. On freeze date, compute scores for all complete-data titles.
2. Write `data/frozen/prospective_set_{date}.csv`: `title_id`, `score`, `quartile`, all component percentiles, full date vector.
3. **Commit it.** It must never be recomputed or overwritten.
4. Daily snapshots continue.
5. At +8 to +10 weeks, measure demand change against the frozen list.

**This is why the daily pipeline is V1, not V4.** Ratings, vote counts and SERPs have no archive — an unrecorded day is gone permanently.

## §17 — Sensitivity analysis

**Weights.** Re-run scoring under:
- Defaults (0.25 / 0.25 / 0.20 / 0.30)
- Competition-heavy (0.20 / 0.20 / 0.10 / 0.50)
- Demand-heavy (0.40 / 0.30 / 0.15 / 0.15)
- Equal (0.25 each)
- Competition removed (0.35 / 0.35 / 0.30 / 0.00)

**Shrinkage.** `m_v` at 0.5×, 1×, 2× median vote count.

**Aggregation.** Minimum / median / weighted mean.

**Reported per configuration:**
- Top-10 membership overlap with default (count out of 10)
- Spearman between the configuration's ranking and default
- Whether each of the five recommendations survives

**Interpretation:** if recommendations survive most configurations, they're robust. If they change completely, the weights are doing the work and that must be the headline caveat — not a footnote.

## §18 — Limitations

### From data availability

1. **No historical backtest possible.** Two of three components have no archive.
2. **Pageviews are a proxy, not search volume.** Bookmarks, links, internal navigation. Correlation with Trends is measured and reported.
3. **SERP source is not Google.** A free metasearch aggregator. Similar for informational queries, differs on freshness-sensitive ones.
4. **240 titles** supports within-vertical percentile scoring and distributional comparison, not fine-grained modelling.
5. **Wikipedia coverage is uneven** across verticals; partial-score rates will differ and are reported.
6. **IMDb linkage is incomplete** for some TV titles.

### From methodology

7. **Publisher tier is assigned, not measured.** A documented judgment call anchored with examples.
8. **Weights are a judgment call.** Sensitivity analysis quantifies how much that matters; it does not eliminate it.
9. **Percentile scores are not comparable across verticals.** 85 in anime ≠ 85 in K-drama. Only distributions are compared.
10. **Rating platforms skew** young, online, English-speaking. `ko`/`ja` pageviews partly offset; do not eliminate.
11. **Airing status confounds** demand and competition. Analysis segmented by status.
12. **Vertical definitions are database rules,** not cultural definitions.
13. **Not a traffic prediction.** Realised performance also depends on domain authority, backlinks, timing and content quality — none modelled.
14. **Intent match is inferred from titles,** not page content, because the free SERP source returns no page bodies.

Both lists appear in the methodology document **and** in a dashboard "Limitations" section.

---

# PART E — IMPLEMENTATION

## §19 — Repository structure

```
content-opportunity-intelligence/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
│
├── config/
│   ├── settings.yaml            # staleness tolerance, cadences, paths
│   ├── sampling.yaml            # FROZEN v1
│   ├── publisher_tiers.yaml     # FROZEN v1
│   ├── query_types.yaml         # FROZEN v1
│   └── weights.yaml             # versioned, tunable
│
├── docs/
│   ├── preregistration.md       # FROZEN — never edited, only appended
│   ├── data_dictionary.md
│   ├── methodology.md
│   ├── findings.md
│   ├── recommendations.md
│   └── decision_log.md
│
├── src/
│   ├── collect/
│   │   ├── cache.py
│   │   ├── tmdb.py
│   │   ├── wikipedia.py
│   │   ├── imdb_dumps.py
│   │   ├── anilist.py
│   │   ├── serp.py
│   │   └── trends.py
│   ├── resolve/
│   │   ├── entity_resolution.py
│   │   └── manual_review.py
│   ├── transform/
│   │   ├── demand.py
│   │   ├── reception.py
│   │   └── competition.py
│   ├── score/
│   │   ├── normalize.py
│   │   ├── opportunity.py
│   │   ├── staleness.py
│   │   ├── rationale.py
│   │   └── sensitivity.py
│   ├── analysis/
│   │   ├── hypotheses.py        # H1, H2, H3
│   │   └── validation.py
│   ├── db.py
│   └── utils.py
│
├── pipelines/
│   ├── bootstrap.py             # one-time: population → sample → resolution
│   ├── daily.py                 # TMDB + Wikipedia snapshot
│   ├── fortnightly_serp.py
│   ├── weekly_ratings.py
│   └── score.py
│
├── data/
│   ├── raw/                     # GITIGNORED
│   ├── frozen/                  # COMMITTED, never overwritten
│   ├── snapshots/               # COMMITTED, append-only
│   ├── outputs/                 # COMMITTED, dated
│   └── warehouse.duckdb         # GITIGNORED
│
├── tests/
│   ├── test_sampling.py
│   ├── test_competition.py
│   ├── test_opportunity.py
│   ├── test_staleness.py
│   └── test_data_quality.py
│
├── notebooks/
│   ├── 01_resolution_review.ipynb
│   ├── 02_rubric_validation.ipynb
│   ├── 03_hypotheses.ipynb
│   └── 04_sensitivity.ipynb
│
├── dashboard/
│   ├── Home.py
│   ├── pages/
│   └── components/
│
└── .github/workflows/
    ├── daily.yml
    ├── weekly.yml
    └── tests.yml
```

**Never committed:** `.env`, `data/raw/`, `data/warehouse.duckdb`, `__pycache__`, `.ipynb_checkpoints`.

**Never overwritten:** anything in `data/frozen/`, `docs/preregistration.md`, frozen configs. Changes create a v2 file.

## §20 — Git strategy

### Commit order for the first session — order is the point

| # | Commit | Why this order |
|---|---|---|
| 1 | Empty repo + README stub | Establishes the timeline |
| 2 | `docs/preregistration.md` | **Alone**, so the timestamp is unambiguous |
| 3 | `config/sampling.yaml` | Before any data is seen |
| 4 | `config/publisher_tiers.yaml` + `query_types.yaml` | Before any SERP is seen |
| 5 | `docs/data_dictionary.md` | |
| 6 | `.gitignore` + `.env.example` | Before the real key exists anywhere |

Only then does collection code appear.

### Versioned vs. immutable

| Type | Rule |
|---|---|
| `preregistration.md` | **Immutable.** Amendments appended below original, never edited |
| Frozen configs | **Immutable.** Changes create `_v2` file; v1 stays |
| `weights.yaml` | Versioned; every score records `weights_version` |
| `data/frozen/*` | **Immutable.** New draws create new dated files |
| `data/snapshots/*` | Append-only. Never edited retroactively |
| `data/outputs/*` | Dated; old runs retained |

### Commit messages

Prefix with the phase: `[freeze]`, `[collect]`, `[resolve]`, `[score]`, `[validate]`, `[dash]`, `[docs]`. Makes the history legible to a reviewer skimming it.

## §21 — Build phases

### V1 — Working pipeline and score

**Goal:** a complete, honest end-to-end run on real data.

**Tasks:** freeze commits · TMDB collector + cache · eligible population snapshot · sampling · entity resolution (Wikipedia only) · Wikipedia collector · **daily GitHub Action live** · SERP collector + rubric · demand and competition transforms · reception from TMDB only · Opportunity Score with staleness guard · minimal Streamlit dashboard.

**Output:** scored 240 titles, dashboard, daily snapshots accumulating.

**Done when:** `pipelines/score.py` runs end-to-end and produces a ranked list per vertical, partial scores separated, and the daily Action has run green three days consecutively.

**Do NOT yet:** AniList, IMDb, sensitivity analysis, hypothesis testing, dashboard polish.

### V2 — Enrichment and reception quality

**Goal:** a defensible reception component.

**Tasks:** IMDb dumps · IMDb resolution · Bayesian shrinkage · cross-source agreement · AniList enrichment · `ko`/`ja` pageviews · rationale text generation.

**Done when:** reception uses both sources with shrinkage, disagreements are flagged, and coverage rates are reported per vertical.

**Do NOT yet:** touch weights based on what the results look like.

### V3 — Validation

**Goal:** evidence the model does what it claims.

**Tasks:** freeze the prospective set and commit · hand-label 40 SERPs · rubric validation · aggregation selection · historical demand validation · sensitivity analysis · Trends cross-check.

**Done when:** every §15 exercise has a reported result, including any that came out weak.

**Do NOT yet:** compute H1/H2/H3. Tuning must be frozen first.

### V4 — Findings and delivery

**Goal:** the portfolio artifact.

**Tasks:** freeze weights and aggregation · compute H1/H2/H3 **once** · findings document · five recommendations plus one rejection · methodology document · dashboard completion · README.

**Done when:** §32 checklist passes.

## §22 — First week plan (part-time)

| Day | Time | Work |
|---|---|---|
| **1** | 2h | Repo. Commits 1–6 per §20. Get TMDB key, into `.env`. **No code.** |
| **2** | 2h | `cache.py` + `tmdb.py`. Pull one vertical's eligible population, verify field shapes against §7. |
| **3** | 2h | All four verticals. Save + commit `eligible_population_{date}.parquet`. Inspect counts per cell — **do not look at title names or ratings.** |
| **4** | 1.5h | `pipelines/daily.py` + `.github/workflows/daily.yml`. **Get it green.** This is the highest-value hour of the week. |
| **5** | 2h | Sampling with fixed seed. Draw 240. Commit `sample_240_v1.csv`. Log redistributions. |
| **6** | 3h | Entity resolution: Wikipedia English. Expect 15–20% to manual review. |
| **7** | 2h | Manual review queue. Commit `title_map`. Start `wikipedia.py`. |

**End of week you have:** frozen methodology, frozen sample, resolved titles, and a pipeline that has been collecting for four days.

## §23 — Implementation order and dependencies

```
1.  db.py + cache.py          → no dependencies
2.  tmdb.py                   → needs cache
3.  bootstrap: population     → needs tmdb
4.  sampling.py               → needs population + sampling.yaml
5.  daily.py + Action         → needs tmdb, sample   ← EARLY, deliberately
6.  entity_resolution.py      → needs sample
7.  wikipedia.py              → needs title_map
8.  demand.py                 → needs pageviews (90d minimum)
9.  serp.py                   → needs sample + query_types.yaml
10. competition.py            → needs serp + publisher_tiers.yaml
11. imdb_dumps.py             → needs title_map
12. reception.py              → needs ratings snapshots
13. normalize.py              → needs all feature tables
14. staleness.py              → needs date vectors
15. opportunity.py            → needs normalize + staleness + weights.yaml
16. rationale.py              → needs opportunity
17. dashboard                 → needs opportunity
18. validation.py             → needs everything + time elapsed
19. hypotheses.py             → needs frozen tuning     ← LAST
```

**Step 5 is deliberately out of logical order.** The pipeline goes live before it is needed, because prospective data cannot be backfilled.

**Step 19 is last and runs once.**

## §24 — Testing strategy

### Unit tests

| Test | Asserts |
|---|---|
| `test_sampling` | Fixed seed reproduces identical sample; cell allocation sums to 60; redistribution respects `max_per_cell` |
| `test_competition` | Position weights descend; perfect SERP = 100, empty = 0; unmatched domain gets default tier |
| `test_opportunity` | Score in [0,100]; any null component → null score + `is_partial`; weights sum to 1 |
| `test_staleness` | Raises above tolerance; handles null IMDb date without crashing |
| `test_reception` | Shrinkage moves low-vote titles toward vertical mean; high-vote titles barely move |

### Data quality checks — run every pipeline execution, fail loudly

| Check | Rule |
|---|---|
| Duplicate `title_id` | Zero tolerance |
| Duplicate `tmdb_id` | Zero tolerance |
| Missing `title_id` in any table | Must be in `titles` |
| `pageviews == 0` | **Flag every instance.** A true zero is possible but rare; verify it isn't a coerced null |
| Null without `null_reason` | Fail |
| Rating outside 0–10 | Fail |
| `vote_count` decreasing between snapshots | Warn — possible source correction |
| `position` outside 1–10 | Fail |
| Duplicate (title, query_type, position, date) | Fail |
| SERP with <5 results | Warn + flag |
| Score outside 0–100 | Fail |
| `observed_at` in the future | Fail |
| Snapshot gap > 2 days | Warn — the Action may have failed silently |

### Pipeline checks

Daily Action asserts row count within ±10% of prior run and posts a failure notification. A silently broken cron is worse than no cron, because you'll trust data you don't have.

## §25 — Dashboard specification

Streamlit. **Every chart must answer a stated question or be removed.**

### Home — Overview
Top 10 opportunities per vertical (tabbed). Each row: title, score, four component chips, best query angle. Sidebar: the date vector and staleness for the current run. A prominent one-line statement that this is a prioritisation tool, not a traffic prediction.
*Answers:* "What should I write about?"
*Charts: none.* A table is correct here.

### Demand
Pageview time series for selected titles. Level vs. momentum scatter, quadrant-labelled.
*Answers:* "Who is rising, and who is merely large?"
*Charts:* one line chart, one scatter.

### Reception
Shrunk vs. raw rating scatter showing shrinkage effect. TMDB vs. IMDb agreement scatter with disagreements highlighted.
*Answers:* "Are ratings trustworthy for this title?"
*Charts:* two scatters. No rating histograms — they answer nothing actionable.

### Competition
Per title: competition score, UGC share, intent gap, publisher ceiling. Expandable top-10 SERP with each result's tier/intent/format. Fandom-heavy SERPs flagged.
*Answers:* "Why is this hard or easy, and which angle is open?"
*Charts:* none. The SERP table *is* the visualisation.

### Title Explorer
Single title, full profile, all components, generated rationale, full date vector.
*Answers:* "Why did this score what it scored?"

### Incomplete Data
Partial-score titles with what is known and what is missing. Coverage rate by vertical.
*Answers:* "What am I not seeing, and why?"
*This page exists to make missing data visible rather than convenient to ignore.*

### Recommendations
The five picks, the one rejection, the reasoning, the date they were frozen, and — once elapsed — the prospective validation result.
*Answers:* "What was decided, and was it right?"

### Limitations
Both lists from §18, in full.

## §26 — Final research outputs

**README** — 60-second summary, screenshot, what it does, how to run it, data sources with attribution, honest limitations summary, link to methodology.

**`methodology.md`** — §4–§14 in full, plus both limitation lists. Written for a skeptical reader.

**`findings.md`** — H1/H2/H3 results with CIs, cross-vertical comparison, all validation results including weak ones, sensitivity results. Structured as: question, method, result, interpretation, what cannot be concluded.

**`recommendations.md`** — five picks with per-title evidence and best query angle; one rejection with reasoning; the frozen date; prospective outcome when available.

**Dashboard** — per §25, publicly hosted.

**Repository** — clean history showing the freeze-before-collect sequence.

## §27 — Portfolio presentation

**Title:** Content Opportunity Intelligence — a cross-vertical content prioritisation model

**One line:** Built and validated a reproducible model scoring 240 entertainment titles on demand, reception and SERP competition to identify content opportunities that popularity ranking misses.

**Skills demonstrated:** Python · API integration (4 sources) · entity resolution · statistical adjustment (Bayesian shrinkage) · hypothesis pre-registration · missing-data handling · point-in-time data integrity · metric design and human validation · sensitivity analysis · DuckDB · Streamlit · CI automation · SEO domain expertise

**Resume bullets:**

- Designed and validated a composite prioritisation model across 240 titles and 4 content verticals, integrating 4 free data sources with reproducible stratified sampling
- Pre-registered hypotheses and scoring rules in version control before data collection, and reported results against them including where predictions were rejected
- Identified that two of three model inputs had no historical archive, and redesigned validation from retrospective backtest to a frozen prospective design to eliminate leakage
- Built a SERP competition metric scoring publisher tier, query-intent match and result format, validated against 40 hand-labelled result sets
- Automated daily point-in-time snapshots via GitHub Actions, enforcing per-source observation dates and a staleness guard that blocks scoring on stale inputs

**60–90 second explanation:**

> "Entertainment sites pick topics by popularity, but popularity is also where all the competition is — so their articles land on page four. I built a model that scores titles on three separate things: how many people want information, how well it was received, and how much has already been written. Separating them exposes gaps popularity hides.
>
> I ran it across anime, K-drama, animated film and anglophone animation to test whether those behave differently, and I committed my prediction to git before collecting any data so I couldn't revise it afterwards.
>
> The most interesting problem was validation. I planned to backtest six months. Then I checked what was actually retrievable and found that ratings and search results have no historical archive — only Wikipedia does. So a full backtest was impossible, and attempting one would have leaked future information. I redesigned it as a frozen prospective test and started daily snapshots immediately, because that data can't be backfilled.
>
> The output is a decision: five titles to cover, one popular title to skip, and the evidence for each."

## §28 — Interview defense

**Sampling**
- *Why 240?* SERP throughput on free tools, plus within-vertical percentile scoring needs a coherent cohort more than a large one. State the constraint, don't dress it up.
- *Why terciles?* 40 cells for 60 titles gives singletons. 12 cells at 5 holds.
- *How do I know you didn't cherry-pick?* Fixed seed and eligible-population snapshot both committed. Reproduce it yourself.
- *Why 2015?* Wikipedia pageviews API begins then. A data constraint, stated.

**Missing data**
- *Why not impute pageviews?* Imputing would place a fabricated value on precisely the population the thesis targets. Partial scores make the gap visible instead.
- *Doesn't excluding them bias results?* Yes — which is why they're reported separately with coverage rates by vertical, rather than silently dropped.

**Shrinkage**
- *Why median vote count as prior strength?* Typical-volume titles pull halfway to the mean; it's principled without tuning. Sensitivity-tested at 0.5× and 2×.
- *Why vertical mean not global?* Everything else is within-vertical; a global prior would import cross-vertical rating differences into the score.

**Percentiles**
- *Why not z-scores?* Distributions aren't normal — popularity is heavily skewed. Percentiles are robust and directly interpretable.
- *Can I compare 85 in anime to 85 in K-drama?* No, and the dashboard says so. Only distributions are compared.

**SERP scoring**
- *Isn't the rubric subjective?* Yes, and it's frozen and versioned before collection, anchored with examples, and validated against 40 hand labels with a reported correlation.
- *Why is Fandom tier 2?* Documented in advance: reference content with atypical authority. Scoring it tier 1 would understate competition in animation verticals.
- *Why does intent match matter?* A major publisher ranking on brand authority with a generic page is beatable; a purpose-built article is not. Result counts can't see the difference.

**Weights**
- *Where did they come from?* Judgment. Sensitivity analysis quantifies how much that matters and reports whether recommendations survive alternative weightings.
- *Isn't that circular?* Tuning is against human-labelled difficulty, never against hypothesis outcomes, and is frozen before hypotheses are computed.

**Leakage**
- *How do you prevent it?* Per-source observation dates, a stored date vector per score, and a staleness guard that raises rather than computing. Enforced in code.
- *Why no backtest?* Two of three inputs have no historical archive. Not hard — impossible. Attempting one would require inventing past values.

**Validation**
- *Isn't 8 weeks short?* Yes. It detects direction, not magnitude, and the writeup says so.
- *What if the prospective test fails?* It's reported. The score may still be useful as prioritisation without being predictive, but the distinction is stated.

**Correlation vs. causation**
- *Does a high score cause traffic?* No claim is made. It's a prioritisation heuristic; realised traffic depends on domain authority, backlinks, timing and quality, none of which are modelled.

**Data source choices**
- *Why Wikipedia over Trends?* Absolute counts, full history, keyless, works identically across verticals. Trends is relative within query batches and unofficial. Trends is used to validate the proxy.
- *Isn't Wikipedia a poor demand proxy?* It's a proxy, named as one, with correlation to Trends measured and reported.
- *Why not Google SERPs?* Cost. The project is free-tier by design. Called "observed" competition throughout, with the difference stated.
- *Why four verticals?* To test whether the demand/competition relationship is structural or vertical-specific.

**Failure modes** — *why might this be wrong?*
- The score might just re-derive popularity — explicitly tested as H3 and reported either way
- Metasearch results may diverge from Google more than assumed
- The minimum-aggregation rule may overstate opportunity when the easy angle has low volume
- Intent match is inferred from result titles, not page content
- Eight weeks may be too short to detect anything

*Having this list ready is stronger than defending the project as flawless.*

## §29 — Decision log

| # | Decision | Reason | Date | Alternative | Why rejected | Changeable? |
|---|---|---|---|---|---|---|
| 1 | Wikipedia pageviews as primary demand | Absolute, historical, keyless, cross-vertical | 09-03 | Google Trends | Relative within batches; unofficial; no reliable history | No — foundational |
| 2 | TMDB as master source | Only unified schema across 4 verticals | 09-03 | Per-vertical sources | Four schemas, no comparability | No |
| 3 | Wikipedia **not** an inclusion criterion | Would drop newer/smaller titles — the target population | 09-03 | Require it | Removes the findings from the dataset | No |
| 4 | `NULL` ≠ `0` for pageviews | Missing ≠ absent | 09-03 | Impute 0 | Fabricates data on the target population | No |
| 5 | 240 titles, 60/vertical | SERP throughput; cohort coherence | 09-03 | 1000+ | Not feasible free; doesn't improve percentile scoring | Yes, upward later |
| 6 | Terciles not deciles | 40 cells for 60 titles gives singletons | 09-03 | Deciles | Empty cells | Yes |
| 7 | Proportional shortfall redistribution | Preserves stratification | 09-03 | To largest cell | Concentrates sample in one period | Yes |
| 8 | `anglophone_animation` allowlist | Exclusion rule didn't define "Western" | 09-03 | Exclude JP/KR/CN | Silently admits FR/ES/IN | Yes — could add EU in v2 |
| 9 | No full historical backtest | Two of three inputs have no archive | 09-03 | Reconstruct with current values | Leakage | No |
| 10 | Daily pipeline in V1 | Enables prospective validation; can't backfill | 09-03 | V4 | Loses irrecoverable data | No |
| 11 | Per-source observation dates | Single date would mix September ratings with August SERPs | 09-03 | One `snapshot_date` | Silent leakage | No |
| 12 | `vote_count` delta = *activity*, not demand | Voting requires deliberate engagement | 09-03 | Call it demand | Easily challenged, and wrong | No |
| 13 | Fandom at tier 2 | Reference content with atypical authority | 09-03 | Tier 1 | Understates competition in animation | Yes, via rubric v2 |
| 14 | Shrinkage to vertical mean, `m` = median votes | Consistent with within-vertical scoring | 09-03 | Global mean | Imports cross-vertical differences | Yes, sensitivity-tested |
| 15 | Aggregation tested, not assumed | Minimum may overstate opportunity | 09-03 | Fix minimum | Unjustified | Resolved in V3 |
| 16 | H3 continuous, not pass/fail | 0.82 has no principled cutoff | 09-03 | Second threshold | Arbitrary | No |
| 17 | Weights: 0.25/0.25/0.20/0.30 | Competition is the differentiating signal | 09-03 | Equal | Under-weights the novel component | Yes — sensitivity-tested |
| 18 | Staleness tolerance 21 days | One missed fortnightly SERP cycle | 09-03 | 7 / 30 | 7 too strict for SERP cadence; 30 permits real staleness | Yes |
| 19 | Corrected `sampling.yaml` in place to match §4 | Transcription errors: no `release_date_max`, no IE in the anglophone allowlist, no adult exclusion, no `max_per_cell` | 09-04 | Create `sampling_v2.yaml` | No data collected at the time, so there were no results to fit the method to. A v2 superseding a v1 that was never used obscures the history | No — frozen for real now |
| 20 | Cross-vertical overlap resolved by first-match precedence (`anime` > `kdrama` > `animated_film` > `anglophone_animation`) | 6 titles satisfied both `anime` and `anglophone_animation`. Unresolved they would be sampled twice, appear in two within-vertical percentile ranks, and contaminate H1 | 09-04 | (a) drop ambiguous titles from both; (b) allow duplicates | (a) deletes internationally co-produced titles, precisely the target population; (b) breaks H1's assumption that verticals are distinct. Precedence is deterministic and reaches §4's stated intent without reintroducing an exclusion rule | No — frozen before the population snapshot |

## §30 — Status tracker

Legend: ☐ not started · ◐ in progress · ☑ complete · ⚠ blocked · ? needs review

**Freeze** — complete 2026-09-04
- ☑ Repo created — `github.com/ItszVT/content-opportunity-intelligence`
- ☑ `preregistration.md` committed
- ☑ `sampling.yaml` committed (corrected 09-04, decision 19)
- ☑ `publisher_tiers.yaml` + `query_types.yaml` committed
- ☑ `data_dictionary.md` committed
- ☑ TMDB key obtained, `.env` gitignored, `.env.example` committed
- ☑ `requirements.txt`, `pytest.ini` committed

**V1**
- ☑ `cache.py` / `db.py`
- ☑ `tmdb.py`
- ☑ Eligible population snapshot committed
- ☑ Sampling, `sample_240_v1.csv` committed
- ◐ **Daily Action green** — pipeline written, first snapshot collected manually; needs three consecutive automated green runs
- ☐ Entity resolution (Wikipedia), match rate reported ← **NEXT**
- ☐ `wikipedia.py`
- ☐ `serp.py`, first full collection
- ☐ `competition.py`
- ☐ `demand.py`
- ☐ `opportunity.py` + staleness guard
- ☐ Minimal dashboard

**V2**
- ☐ IMDb dumps + resolution
- ☐ Bayesian shrinkage
- ☐ Cross-source agreement
- ☐ AniList enrichment
- ☐ `ko`/`ja` pageviews
- ☐ Rationale generation

**V3**
- ☐ Prospective set frozen and committed
- ☐ 40 SERPs hand-labelled
- ☐ Rubric validation reported
- ☐ Aggregation method selected
- ☐ Historical demand validation
- ☐ Sensitivity analysis
- ☐ Trends cross-check

**V4**
- ☐ Weights frozen
- ☐ H1 / H2 / H3 computed **once**
- ☐ `findings.md`
- ☐ `recommendations.md` (5 + 1 rejection)
- ☐ `methodology.md`
- ☐ Dashboard complete
- ☐ README
- ☐ Prospective result added (+8–10 weeks)

## §30.1 — Progress log

> Read this section to resume. It records what exists, what it produced, and the next action.

### Environment

| | |
|---|---|
| **Repo** | `github.com/ItszVT/content-opportunity-intelligence` |
| **Working environment** | GitHub Codespaces, Python 3.12.1 |
| **Rule** | Work in Codespaces only. Editing via the GitHub web editor while a Codespace is open caused a diverged history and a file/directory conflict on 09-04 |
| **Secrets** | `TMDB_BEARER_TOKEN` in local `.env` (gitignored) and as a GitHub Actions repository secret. API Read Access Token, not the short API key — it travels in a header, never a URL |
| **Tests** | `pytest -v` from repo root. `pytest.ini` sets `pythonpath = .` |

### Session 1 — 2026-09-04

**Freeze completed.** Commit order followed §20: preregistration alone first, then configs, then `data_dictionary.md`, then `.gitignore` + `.env.example`. Verifiable in the git log — the timestamp sequence is the evidence that methodology preceded data.

**Two methodology corrections, both before any data was collected** (decisions 19 and 20 in `docs/decision_log.md`):

1. `sampling.yaml` had drifted from §4 during transcription — missing `release_date_max` (the open window would have made the population unreproducible), missing `IE` from the anglophone allowlist, missing the adult exclusion and `max_per_cell`. Corrected in place rather than versioned to v2, because zero data existed and a v2 superseding an unused v1 obscures rather than clarifies.
2. Cross-vertical overlap was undefined in §4. Six titles satisfied both `anime` and `anglophone_animation` (co-productions with multiple `origin_country` values). Resolved by **first-match precedence**, order declared explicitly in `sampling.yaml` as `vertical_precedence`.

**Note:** seed is `20260904`, not the `20260903` written in §8. Frozen on the 4th. The value is arbitrary; only its fixity matters.

### Code written

| File | Purpose | Verified by |
|---|---|---|
| `src/collect/cache.py` | Namespaced disk cache, SHA-256 key. Refuses key material containing credential-like names, so a token can never reach a filename | self-test in `__main__` |
| `src/db.py` | DuckDB schema for all seven §7 tables. Several §24 checks are structural — `pageviews` nullable while its row-mates are `NOT NULL`; `position` constrained 1–10 | self-test asserts the NULL rule holds and a constraint actually fires |
| `src/collect/tmdb.py` | TMDB client + eligible population fetch. Reads every rule from `sampling.yaml`; nothing hardcoded | ran against all four verticals |
| `pipelines/bootstrap_population.py` | Applies precedence, freezes the population, writes a manifest | dry-run then real run |
| `pipelines/sample.py` | §8 stratified draw, per-cell RNG, proportional redistribution | 9 tests in `tests/test_sampling.py` |
| `pipelines/daily.py` | Daily TMDB snapshot with §24 quality checks; non-zero exit on failure | 240/240 collected, 0 failures |
| `.github/workflows/daily.yml` | Scheduled 03:17 UTC + manual dispatch. Pinned to `actions/checkout@v5` and `actions/setup-python@v6` | manual dispatch run green, no annotations |

Two pagination hazards are handled explicitly in `tmdb.py` and are worth not re-discovering: `/discover` sorted by popularity reorders itself mid-pagination (so results duplicate and others are never seen — we sort by release date and dedupe on `tmdb_id` anyway), and `/discover` stops at page 500 (so the collector raises rather than freezing a silently truncated population).

`pipelines/sample.py` seeds each cell's RNG from a hash of the global seed plus the cell's identity, rather than consuming one global stream in order. With a single stream, a shortfall in one cell shifts the draw for every cell after it — so an unrelated population change would silently redraw the whole sample.

### Frozen artifacts — committed, never to be edited

```
data/frozen/eligible_population_2026-09-04.parquet          1,502 rows
data/frozen/eligible_population_2026-09-04.manifest.json    includes sampling.yaml SHA
data/frozen/sample_240_v1.csv                               240 titles
data/frozen/sample_240_v1_redistribution_log.csv            3 redistributions
data/snapshots/tmdb_snapshot_2026-09-04.parquet             240 rows, day 1
```

The manifest records the SHA-256 of `sampling.yaml`. A reviewer can prove which config produced the population, and any later edit becomes detectable rather than a matter of trust.

### Results

**Eligible population, after precedence:**

| Vertical | Eligible | 2015–17 | 2018–20 | 2021–23 | 2024–26 |
|---|---|---|---|---|---|
| `anime` | 363 | 96 | 129 | 102 | 36 |
| `kdrama` | 224 | 40 | 54 | 83 | 47 |
| `animated_film` | 751 | 225 | 217 | 214 | 95 |
| `anglophone_animation` | 164 | 21 | 54 | 58 | 31 |

`animated_film` is 4.5× `anglophone_animation`. Expected — films accumulate and the allowlist is narrow. Irrelevant to scoring, which is within-vertical throughout.

**Sample: 240 drawn, 60 per vertical, every vertical at target.** Three cells fell short and were redistributed:

| Vertical | Short cell | Drawn | Deficit went to |
|---|---|---|---|
| `animated_film` | 2024-2026 / tercile 1 | 3 | 2015-2017/T1, 2018-2020/T1 |
| `anglophone_animation` | 2015-2017 / tercile 1 | 4 | 2021-2023/T1 |

Both shortfalls sit in **tercile 1** — the least popular slice. This is structural, not chance: recent releases skew toward higher popularity, so the least-popular third of a thin year bucket is the smallest cell in the design. Worth a paragraph in `methodology.md`, since a reviewer will ask why the redistribution rule fired.

### Known follow-ups

- **Cosmetic:** `pipelines/sample.py` prints `np.int64(5)` in cell occupancy. Change `list(counts.values)` to `counts.tolist()`.
- **Before V1 ends:** pin `requirements.txt` to exact versions (currently `>=`). §32 requires a fresh clone to rebuild identically. Do not use `pip freeze` — it captured all 105 Codespaces packages when tried on 09-04. Write the seven project dependencies by hand with their resolved versions.
- **Daily Action:** needs three consecutive green automated runs before §30 can be ticked. The manual run does not exercise the commit-and-push path, since that day's snapshot already existed locally.

### Workflow maintenance

The first manual run raised a Node 20 deprecation warning. Bumped `actions/checkout@v4 → v5` and `actions/setup-python@v5 → v6`, both of which ship Node 24 builds with unchanged input APIs. This was not cosmetic: **GitHub removes Node 20 from the runners on 2026-09-16**, and a workflow that dies then would open an unbackfillable gap in the series.

The general rule for this project: anything that could silently stop the cron gets fixed immediately, because §15.2's prospective validation needs an unbroken 8–10 week series and no day can be recovered after the fact.

Failure notifications should be enabled at GitHub → Settings → Notifications → Actions → failed workflows only. Without them a broken cron is invisible until someone happens to look.

### Verify at the start of the next session

1. **The 03:17 UTC run fired.** Look for a commit from `github-actions[bot]` and a second file in `data/snapshots/`. This is the first run to exercise the commit-and-push path.
2. **Row count held at 240** in the new snapshot, and the ±10% check passed against day one.
3. If either failed, fix before writing new code — a gap compounds daily.

### Next action

**Entity resolution, English Wikipedia** (§9 step 2, §23 step 6) → `src/resolve/entity_resolution.py`.

Resolution order matters and is fixed in §9: Wikidata via TMDB external IDs, then Wikipedia search on `title_primary` + year, then search on title alone with an instance-of check, then manual review. Reject disambiguation pages; follow redirects and store the canonical slug. Expect 15–20% to land in `data/frozen/manual_review.csv`.

Report auto-match rate **per vertical**. The variation is itself a finding — uneven Wikipedia coverage across verticals is exactly what §10 and limitation 5 are about, and it determines the partial-score rate.

Then `wikipedia.py`, then add pageviews to `pipelines/daily.py`.

## §31 — Rules for changing methodology

**Never silently change anything frozen.**

### Permitted without amendment
- Bug fixes that make code match documented methodology
- Performance and refactoring
- Adding tests, docs, dashboard elements

### Requires a logged amendment
Anything altering what is measured or how. Procedure:

1. Add a row to §29 with the date, reason, and what it supersedes
2. Create a **new versioned file** (`publisher_tiers_v2.yaml`). Never edit v1
3. Record the version in every affected output (`rubric_version`, `weights_version`)
4. Note in `methodology.md` which results used which version
5. If it affects a pre-registered hypothesis, append to `preregistration.md` **below** the original text, never edit it

### Forbidden
- Changing H1/H2/H3 or their operationalisation after seeing results
- Re-drawing the sample because the current one looks uninteresting
- Adjusting publisher tiers after seeing which domains dominate
- Tuning weights against hypothesis outcomes
- Deleting or overwriting anything in `data/frozen/`

### The test
> If a reviewer saw this change alongside the results, would it look like a fix or like fitting the method to the answer?

If the second, don't make it. If it must be made, document it so thoroughly that the reasoning is auditable.

## §32 — Definition of done

The project is portfolio-ready when **all** of the following are true:

**Reproducibility**
- ☐ Fresh clone + `.env` + one command rebuilds the warehouse
- ☐ Fixed seed reproduces the identical 240
- ☐ Eligible population snapshot committed
- ☐ All frozen configs committed and unedited

**Data integrity**
- ☐ All §24 quality checks pass
- ☐ Zero `pageviews == 0` that are actually coerced nulls
- ☐ Every score carries a complete date vector
- ☐ Staleness guard demonstrably triggers when tested
- ☐ Partial scores separated from rankings everywhere

**Methodology**
- ☐ Pre-registration committed **before** first data commit (verifiable in log)
- ☐ Match rates reported per source per vertical
- ☐ Rubric validated with correlation, CI and n
- ☐ Aggregation method selected on evidence, with comparison reported
- ☐ Sensitivity analysis reported
- ☐ Both limitation lists in methodology and dashboard

**Findings**
- ☐ H1, H2, H3 computed once, after tuning frozen
- ☐ Results reported as pre-registered, **including rejections**
- ☐ Weak or null validation results reported, not omitted
- ☐ No claim of traffic prediction anywhere

**Deliverables**
- ☐ Dashboard live, all 8 pages
- ☐ Five recommendations plus one defended rejection
- ☐ Prospective set frozen; result added at +8–10 weeks
- ☐ README, methodology, findings, recommendations complete
- ☐ TMDB attribution in footer and README
- ☐ Decision log current

**The final test**
- ☐ A skeptical senior analyst could read the repo and understand every methodological choice without asking you
- ☐ You can answer every §28 question without hedging
- ☐ Nothing in the project claims more than the data supports

---

## The first five things to do

1. **Create the repo and commit the pre-registration alone.** The timestamp is the point.
2. **Commit `sampling.yaml`, then `publisher_tiers.yaml` + `query_types.yaml`, then `data_dictionary.md`** — separate commits, in that order.
3. **Get the TMDB Developer key.** Into `.env`, with `.gitignore` committed in the same change.
4. **Write `cache.py` and `tmdb.py`.** Pull one vertical, verify fields match §7.
5. **Get the daily GitHub Action running,** even before the sample exists. It can pull the eligible population daily until it has something better to do.

## What NOT to do yet

- **Do not open a notebook and explore.** Charts on an unfrozen sample will anchor your intuitions before your rules exist, and every later decision gets quietly shaped by what you saw.
- **Do not build the dashboard.** It's the fun part and it's last for a reason.
- **Do not look at title names, ratings, or which shows made the sample** beyond verifying the code works. Check cell counts, not contents.
- **Do not touch AniList, IMDb, or Trends.** V2 and V3.
- **Do not adjust the weights.** They're sensitivity-tested later, not tuned now.
- **Do not run any hypothesis test.** V4, once, after tuning is frozen.
