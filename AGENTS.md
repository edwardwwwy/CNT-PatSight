# CNT-PatSight Agent Operating Rules

## Current Phase

Current phase: **curated-paper and patent extraction with eight-table normalization**.

- Extract manually supplied sources into traceable `needs_review` data.
- Keep the design usable for several hundred papers and patents.
- Optimize for accuracy, auditability, stable joins, and controlled sparsity.
- Do not build crawlers, web apps, dashboards, ML predictions, or industrial scoring systems unless requested.

## Required Guidance

Before screening, PDF extraction, run planning, field mapping, validation, CNT-type verification, catalyst/process comparison, or R&D review, read:

```text
skills/cnt-patsight/SKILL.md
```

For table mapping or validation, also read:

```text
skills/cnt-patsight/references/schema.md
```

## Stable Data Contract

Maintain these eight source tables:

```text
source_master
source_run
catalyst_system
reactor_process_gas
yield_quality
cost_scale_review
evidence_index
review_issue_log
```

- Maintain `config/field_dictionary.csv` as the machine-readable field contract.
- Generate `ml_runs_clean.csv` later; never maintain it manually.
- Do not add, remove, rename, split, or repurpose formal fields silently.
- Evaluate field usefulness across several hundred papers and patents, not only the current sample.
- Keep common and class-conditionally common fields; retain rarer fields when they are critical for identity, reproducibility, safety, scale, or industrial review.
- Put heterogeneous or one-off detail in summary fields and `evidence_index` rather than creating mostly empty column families.

## Per-Source Sequence

Complete these steps in order:

1. Register one `source_master` row with stable source metadata and screening status.
2. Classify with `formal_extract`, `candidate_extract`, `source_observation_only`, `background_reference`, or `reject`.
3. List proposed `run_id` values before filling tables. One run requires one identifiable catalyst system, one process/gas program, and one corresponding product/result.
4. Build an evidence map from experimental sections, catalyst preparation, synthesis procedure, tables, figures, results, conclusions, supplements, patent examples, and claims.
5. Populate run facts without repeating source metadata or evidence locations.
6. Create review issues only for actual conflicts, ambiguities, critical gaps, or required human decisions.

Split materially different catalysts, temperatures, gas programs, times, pressures, reactors, purification conditions, or results. Do not fabricate runs from discussion fragments.

## Extraction Status Boundary

Keep `source_master.extraction_status = needs_review` and every first-pass `source_run.extraction_status = needs_review`.

Change to `reviewed` only after a human checks run splitting, catalyst composition/preparation, catalyst thermal treatment, growth stages, pressure, gases/flows, yield identity and definition, CNT type and mixture caveats, dimensions, Raman direction, TGA meaning, purification, evidence links, and open review issues.

## First-Pass Guardrails

- Keep `reported`, `calculated`, `inferred`, and `review_assessment` distinguishable in `evidence_index.value_status`.
- Use `not_reported`, `not_applicable`, or a meaningful qualitative state when interpretation requires it.
- Include all synergistic metals in `active_metals`; Fe-Mo means `Fe; Mo` even if Mo is also a promoter.
- Distinguish acid washing, support/catalyst acidification, and acid complexing through `preparation_modifier` and `preparation_detail`.
- Keep drying, calcination/thermal decomposition, reduction, activation, CNT growth, and cooling conditions separate.
- Preserve original gas programs and map gases by role: carbon source, reducing gas, inert gas, and cofeed/reactive gas.
- Preserve yield name, value/unit expression, definition, formula, normalized value/unit, and normalization status. Never equate carbon weight gain, g/gcat, productivity, conversion, carbon efficiency, growth rate, and array height.
- Use `Raman_ratio_type` with its matching `Raman_ratio_value`; mark calculated reciprocals as calculated evidence.
- Keep as-synthesized TGA carbon content separate from post-purification product purity.
- State mixed products in `product_mixture_summary`; do not represent a mixed CNT/fiber/amorphous product as a clean success.
- Keep demonstrated scale separate from author claims.
- During first pass, leave industrial readiness, reproduction priority, industrial score, and recommended action empty unless a human explicitly assesses them.

## Evidence and Review

- Give every catalyst, process-stage, yield, and cost/scale row at least one `evidence_index` record.
- Use `target_table`, `target_record_id`, and `target_fields` to link evidence to facts.
- Keep source location, section, table/figure/claim reference, excerpt, summary, status, and confidence in the evidence table rather than the fact tables.
- Store mechanisms, failures, preparation hints, temperature effects, scale signals, safety/environment facts, and transferable-route notes as `source_observation` evidence when they are not direct run fields.
- Create `review_issue_log` rows for source conflicts, definition ambiguity, run-split uncertainty, CNT-type uncertainty, calculation checks, critical data gaps, and quality warnings.
- Link review issues to existing evidence IDs and preserve competing reported values until resolution.
- Do not create placeholder issue rows for records without issues.

## File Routing

- Original public PDFs: `data/raw/papers/` or the matching raw-source folder.
- Per-source first-pass package: eight CSVs plus `extraction_workbook.xlsx` in `data/interim/<source_id>/`.
- Global field contract: `config/field_dictionary.csv`.
- Human-reviewed cross-source data: `data/processed/`.
- Public and confidential internal data must remain separable.

Do not keep a separate observation JSONL after its contents have been migrated to `evidence_index` and `review_issue_log`.

## Completion Checks

- Validate exact filenames, column order, row identities, and foreign keys across all eight tables.
- Confirm source metadata is not repeated in `source_run`.
- Confirm no evidence-location columns remain in the five run-fact tables.
- Confirm every catalyst/process/yield/cost row has linked evidence.
- Confirm every review issue links to valid evidence and has a review state.
- Check catalyst composition, particle state, BET/pore data, thermal treatment, all process stages, pressure, gases/flows, time, loading, yield definitions, CNT identity, dimensions, Raman direction, TGA basis, purification, scale, lifetime/reuse, safety, and unresolved conflicts.
- Keep all first-pass runs at `needs_review`.

Run:

```text
python scripts/validation/validate_tables.py <data_directory>
```

Do not claim completion while validation errors remain.

## P001 Regression Focus

For Dubey et al. 2012 preserve three runs, Fe-Mo/MgO chemistry, citric acid as `acid_complexing`, stage-separated catalyst treatment and CNT growth, all gas flows, carbon-weight-gain identity, reported `IG/ID` direction, TGA basis, SG-1 mixed-product warning, unquantified Mo cost implications as evidence, and author-claimed versus demonstrated scale. Keep all records at `needs_review` until human verification.
