# Review and formalization policy

CNT-LitSight separates first-pass extraction from formalization without requiring a separate owner review for every source. A designated evidence-review agent, including Codex, may promote a package to the formal data layer after completing an independent second pass and satisfying the gates below.

## State model

| Stage | `screening_class` | `extraction_status` | `review_status` |
|---|---|---|---|
| First-pass package | `candidate_extract` or provisional `formal_extract` | `needs_review` | `pending_review` |
| Review in progress | unchanged | `needs_review` | `in_review` |
| Formal package | `formal_extract` | `reviewed` | `reviewed` |

`pending_human_review` is accepted only as a legacy value in existing packages. New output uses `pending_review`.

## What the review agent must check

1. Confirm the source identity, DOI or patent number, accessible source, and relevant experimental scope.
2. Rebuild or verify run boundaries so each run has one identifiable catalyst system, process/gas program, and corresponding result.
3. Check catalyst composition and preparation, all process stages, pressure, gases and flows, time, yield identity, CNT type, dimensions, Raman direction, TGA basis, purification, and scale claims against the cited evidence.
4. Preserve `reported`, `calculated`, `inferred`, and `review_assessment` as distinct value states.
5. Confirm units and yield definitions without equating incompatible metrics.
6. Validate all primary/foreign keys, target records, evidence links, issue links, and required fields.
7. Resolve every blocking review issue and record `reviewer`, `reviewed_at`, and `resolution`.
8. Run `python scripts/validation/validate_tables.py <package>` and require zero errors.

## Formalization rule

The review agent may set the package to formal when:

- `source_master.screening_class = formal_extract`;
- `source_master.extraction_status = reviewed`;
- `source_master.review_status = reviewed`;
- every `source_run.extraction_status = reviewed`;
- all high- or critical-severity issues are `reviewed` with a recorded resolution;
- evidence and schema validation pass with zero errors.

A source does not need to be complete to be formal. The following are non-blocking when represented faithfully:

- optional values that the source does not report;
- negative or low-yield runs;
- source conflicts retained as competing reported values;
- low-confidence optional facts omitted rather than guessed;
- open low- or medium-severity improvement notes that do not change run identity or core conclusions.

## When owner input is required

Escalate only when the review agent cannot safely decide without changing the user's intent or authority:

- source identity or run boundaries remain irreconcilably ambiguous;
- a conflict would materially change the primary catalyst, process, yield, or CNT identity;
- company confidentiality, personal data, licensing, or redistribution rights are unclear;
- a business preference, industrial priority, or risk tolerance must be chosen rather than extracted from evidence;
- required source content is unavailable.

The owner is not a routine approval gate. If none of these conditions applies and validation passes, the agent-reviewed package is formal.
