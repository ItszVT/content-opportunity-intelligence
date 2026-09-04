# Decision log

Decisions 1–18 are recorded in the project master plan (§29). This file
continues the log from that point and is the live record from here on.

| # | Decision | Reason | Date | Alternative | Why rejected | Changeable? |
|---|---|---|---|---|---|---|
| 19 | Corrected `sampling.yaml` to match §4 | Transcription errors: missing `release_date_max`, missing IE in the anglophone allowlist, missing adult exclusion, missing `max_per_cell` | 2026-09-04 | Create `sampling_v2.yaml` | No data had been collected at the time of the fix, so there were no results to fit the method to. A v2 superseding a v1 that was never used would obscure the history rather than clarify it | No — frozen for real now |
| 20 | Cross-vertical overlap resolved by first-match precedence: anime > kdrama > animated_film > anglophone_animation | 6 titles satisfied both the anime and anglophone_animation filters (co-productions with multiple origin countries). Unresolved, they would be sampled twice, appear in two within-vertical percentile ranks, and contaminate H1's cross-vertical comparison | 2026-09-04 | (a) Drop ambiguous titles from both verticals; (b) allow duplicates | (a) deletes internationally co-produced titles, precisely the population the thesis targets; (b) breaks H1's assumption that verticals are distinct populations. Precedence is deterministic, reproducible, and reaches §4's stated intent for the anglophone allowlist without reintroducing an exclusion rule | No — frozen before the population snapshot |