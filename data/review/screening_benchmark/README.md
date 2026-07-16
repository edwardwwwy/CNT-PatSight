# Screening benchmark review package

- `screening_benchmark.csv`: 120 stratified screening rows plus one current
  source-level deduplication-review row.
- `dedup_audit.csv`: 23 decision-level deduplication audit rows, separated by
  match reason (5 external ID, 15 DOI, 3 conflict review).
- `benchmark_manifest.json`: reproducible seed, population, sample distribution,
  and deduplication audit coverage.
- `benchmark_metrics.json`: weighted screening metrics, R-tier uncertainty,
  reason-specific deduplication metrics, and release gates.

Complete `human_is_target_synthesis`, `human_tier`, `human_extractability`,
`human_reason`, reviewer, and review date in the screening file. Valid
`human_is_target_synthesis` values are `yes`, `no`, and `indeterminate`. Use
`indeterminate` when M-tier metadata is insufficient to support a scientific
decision. Valid `human_extractability` values are `extractable`,
`possibly_extractable`, `source_observation_only`, `background_reference`,
`not_extractable`, and `indeterminate`. `reviewer_notes` is optional. Fill
`possible_duplicate_missed` only when the screening review identifies another
canonical record that may represent the same work.

In `dedup_audit.csv`, complete `human_merge_correct` and `human_relation` for
every row, including conflict-review rows. Valid merge decisions are `yes` and
`no`; relations are `same_work`, `distinct_work`, `version_relation`, and
`indeterminate`. Also fill reviewer and review date. Do not modify automatic
scores, reasons, decisions, or rule versions.

Current deduplication facts:

- fuzzy-title automatic merge groups: 0;
- exact-title automatic merge groups: 0;
- DOI conflict decisions requiring review: 3.

The obsolete 141-row workbook was removed because its metrics mixed screening
and deduplication rows. Rebuild a workbook from the two CSV files only with the
project-approved spreadsheet runtime; do not use the removed workbook for
review.

After review, run:

```powershell
python scripts/screening_benchmark/benchmark.py summarize
```

Only then assess the release thresholds. `benchmark_decision` is the stage gate:

```text
pending_human_review
fail_export_errors_and_revise_rules
pass_freeze_and_start_30_fulltext_pilot
```

Do not revise rules, rescore all works, or start the 30-paper OA pilot while the
decision remains `pending_human_review`.
