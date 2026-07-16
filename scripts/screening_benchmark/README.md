# Screening benchmark

This module creates a reproducible, stratified human-review sample from the
metadata registry. It does not change automatic tiers or any formal table.

```powershell
python scripts/screening_benchmark/benchmark.py generate
python scripts/screening_benchmark/benchmark.py summarize
```

The screening file contains the fixed A/B/C/M/R stratified sample plus any
source-level `needs_review` row. The separate deduplication file contains:

- 5 sampled external-ID merge groups;
- 15 sampled exact-DOI merge groups;
- every exact-title and fuzzy-title automatic merge group;
- every `review_required` conflict decision.

Rerunning preserves screening review fields by `source_id` and deduplication
review fields by `decision_id`.

The screening review contract is now frozen at:

```text
human_is_target_synthesis
human_tier
human_extractability
human_reason
reviewer_notes
error_type
possible_duplicate_missed
reviewer
reviewed_at
```

Use `yes`, `no`, or `indeterminate` in `human_is_target_synthesis`. In
particular, an M-tier record that cannot be judged from available metadata
should remain `indeterminate`, not be forced into a correct/incorrect label.
Controlled `human_extractability` values are `extractable`,
`possibly_extractable`, `source_observation_only`, `background_reference`,
`not_extractable`, and `indeterminate`.

The A+B recall estimate uses the original stratum weight `N_h / n_h`. Release
metrics stay null until all rows in their required strata are reviewed. R-tier
zero-error results also report the rule-of-three upper bound and still require
an additional 50-75 boundary-focused R review before the rules can be called
stable.

Automatic merge results are reported separately for external ID, DOI, exact
title, and fuzzy title. A zero fuzzy-title population is reported as not
applicable, rather than being treated as evidence of a zero error rate.

The automatic release decision requires complete independent review and checks
A precision, weighted A+B recall, R false-kill rate and count, external-ID
merges, DOI merges, and DOI-conflict decisions. It does not start any download.
