# Data Dictionary

This document explains the main data fields used in the project.

## Title Information

| Field | What it means |
|---|---|
| title_id | Internal ID used to identify a title in the project |
| tmdb_id | TMDB ID for the title |
| title | Main title used in the project |
| vertical | Category of the title |
| release_date | Original release date |
| release_year | Year the title was released |

## TMDB Data

| Field | What it means |
|---|---|
| tmdb_rating | Average rating on TMDB |
| tmdb_vote_count | Number of votes on TMDB |
| tmdb_popularity | TMDB popularity value |

TMDB popularity is collected for sampling and comparison.

It is not used directly in the Opportunity Score.

## Wikipedia Demand Data

| Field | What it means |
|---|---|
| wikipedia_title | Wikipedia page matched to the title |
| wikipedia_language | Wikipedia language used |
| pageviews | Number of Wikipedia pageviews |
| pageviews_observed_at | Date when the pageview data was collected |

Wikipedia pageviews are used as a demand proxy.

They are not treated as direct Google search volume.

## Audience Data

| Field | What it means |
|---|---|
| imdb_rating | Average IMDb rating |
| imdb_vote_count | Number of IMDb votes |
| anilist_score | AniList score where available |
| rating_observed_at | Date when the rating data was collected |

Rating values will be adjusted where necessary to account for differences in vote counts.

## SERP Data

| Field | What it means |
|---|---|
| query | Search query used for the title |
| serp_position | Position of the result |
| result_url | URL of the result |
| result_domain | Domain of the result |
| publisher_tier | Competition tier assigned to the publisher |
| intent_match | How closely the result matches the search intent |
| result_format | Type of result such as article, listicle, wiki, or thread |
| serp_observed_at | Date when the SERP was collected |

## Competition Metrics

| Field | What it means |
|---|---|
| competition_score | Overall observed SERP competition score |
| ugc_share | Share of results that are user generated content |
| intent_gap | Difference between the search intent and ranking content |
| authority_ceiling | Strength of the strongest publishers appearing in the SERP |
| fandom_flag | Whether the SERP contains multiple Fandom results |

Higher competition score means the SERP appears harder to compete in.

## Opportunity Score

| Field | What it means |
|---|---|
| demand_percentile | Demand compared with other titles in the same vertical |
| quality_percentile | Audience reception compared with other titles in the same vertical |
| competition_percentile | Competition compared with other titles in the same vertical |
| opportunity_score | Final score used to prioritize content opportunities |
| score_observed_at | Date of the scoring run |

All percentile based scores are calculated within each vertical.

This is important because the four verticals have different levels of normal demand and competition.

## Observation Dates

Different sources are collected at different times.

For that reason, each source has its own observation date.

For example:

TMDB: 2026-09-04

Wikipedia: 2026-09-04

IMDb: 2026-09-03

SERP: 2026-08-25

A scoring run will record which observations were used.

The project will not calculate a score when an important input is too old according to the project's staleness rule.

## Missing Data

Missing data will not automatically mean that a title should be removed.

For example, a title may have a Wikipedia page in one language but not another.

Missing values will be recorded and handled explicitly.

The project will report data coverage and missingness by vertical.
