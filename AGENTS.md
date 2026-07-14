# CNT-PatSight Agent Operating Rules

## Current Phase

Current phase: **v0.1 curated-paper extraction**.

- The user will manually provide about 10 high-quality papers.
- Extract each paper carefully into traceable, structured `needs_review` sample data.
- Use these samples to test whether the stable five-table schema is sufficient.
- Optimize for accuracy, auditability, and database readiness rather than record count.

Do not expand the project into a platform. Unless the user explicitly requests it, do not build crawlers, web apps, dashboards, local-model pipelines, bulk-processing systems, machine-learning predictions, complex schemas, or industrial scoring systems.

## Required Project Guidance

Before screening, PDF extraction, `run_id` planning, field mapping, table validation, CNT-type verification, catalyst/process comparison, or R&D review, read:

```text
skills/cnt-patsight/SKILL.md
```

For five-table field mapping or validation, also read:

```text
skills/cnt-patsight/references/schema.md
```

Do not load the detailed schema reference for unrelated repository maintenance.

## Stable v0.1 Schema

Use only these five formal business tables:

- `source_run`
- `catalyst_system`
- `reactor_process_gas`
- `yield_quality`
- `cost_scale_review`

Follow **schema strict, capture broad**:

- Do not add, remove, rename, split, or repurpose formal fields by default.
- Do not add another formal business table by default.
- Put valuable information that does not fit cleanly into `source_level_observations`, `valuable_unmapped_information`, and `data/interim/source_observations.jsonl`.
- Treat `source_observations.jsonl` as a temporary observation pool, not a sixth formal table.
- Report recurring schema gaps after 20-30 representative sources; ask the user before promoting them into the formal schema.

## Per-Paper Sequence

Complete these steps before filling the five tables:

1. **Source registration**: establish `source_id`, source type, title, year, DOI or patent number, authors or assignee, and whether the source is a paper, patent, or review.
2. **Screening classification**: use only `formal_extract`, `candidate_extract`, `source_observation_only`, `background_reference`, or `reject`. Do not reject useful catalyst, temperature, atmosphere, failure, CNT-type, reactor, scale-up, safety, or environmental evidence merely because the route is outside the current methane-MWCNT priority.
3. **Run plan**: list proposed `run_id` values before filling tables. One run requires one identifiable catalyst system, one identifiable process/gas program, and one corresponding product or yield result. Split materially different catalysts, temperatures, gas programs, times, reactors, purification conditions, or results.
4. **Evidence map**: locate evidence in the abstract, experimental section, catalyst preparation, CNT synthesis, tables, figure captions, results discussion, and conclusion. Important values must remain traceable through `evidence_text`, `evidence_location`, and the source section where available.

Do not default to one run per paper and do not fabricate a run from fragmentary discussion.

## Extraction Status Boundary

After Codex first-pass extraction, keep `source_run.extraction_status = needs_review`.

Change it to `reviewed` only after the user or a human reviewer checks the important fields, including run splitting, catalyst composition and preparation, catalyst thermal treatment, growth temperature, gas flow, yield value and definition, CNT type, diameter or wall number, Raman direction, TGA meaning, evidence locations, and observation export.

## First-Pass Guardrails

- Keep `reported`, `inferred`, `calculated`, and `review_assessment` distinguishable.
- Keep true absence as `null`, `not_reported`, or `not_applicable`.
- When qualitative evidence exists without a number, preserve a meaningful status such as `non_uniform_not_quantified`, `qualitative_only`, or `uncertain`; do not turn it into an empty cell.
- Include all core synergistic metals in `active_metals`; for repeatedly described Fe-Mo bimetallic catalysts, use `Fe; Mo` even if Mo is also a promoter.
- Distinguish `acid_washing`, `support_acidification`, `catalyst_acidification`, and `acid_complexing`. Citric-acid sol-gel complexation is `acid_complexing_only`, not generic acid treatment.
- Keep drying, catalyst calcination or thermal decomposition, reduction or pretreatment, CNT growth, and cooling temperatures separate.
- Split CH4, H2, N2, Ar, other gas, and total flow when reported. Mark extractor-calculated fractions or ratios as calculated with the formula.
- Preserve the reported yield name, value, unit, definition, and standardization status. Never relabel carbon weight gain as methane conversion, carbon efficiency, productivity, growth rate, or array height.
- Keep `Raman_IG_ID` and `Raman_ID_IG` in the correct direction. Mark a calculated reciprocal explicitly.
- Treat TGA carbon content of an as-synthesized product as distinct from post-purification application-grade purity.
- Do not let a boolean-like CNT field turn a mixed product into a clean success. Use `partial_mixed` for `is_t_MWCNT` or `is_MWCNT` when that type is supported only as one component of a mixed product, and state the mixture explicitly in type evidence or notes. Reserve `yes` for an unambiguous positive assignment that does not conceal a material mixed-product caveat.
- Record an explicit material fact even when its cost effect is unquantified. For example, use `Mo present; cost impact not quantified` rather than `not_reported` when Mo presence is known but no cost analysis is given.
- Keep author scale wording separate from demonstrated experimental scale. Preserve both in `scale_level_claimed` when necessary, and populate `reactor_process_gas.scale_level` from concrete reactor/loading evidence when the source supports a defensible label.
- During first pass, leave `industrial_value_score`, `reproduction_priority`, `recommended_next_action`, and unsupported `major_cost_driver` null.

## Observation Pool

Route useful non-run or non-schema information to `data/interim/source_observations.jsonl`, including mechanism, failure or deactivation, catalyst-preparation hints, temperature effects, data gaps, quality warnings, scale-up signals, safety/environmental information, patent apparatus, transferable routes, and information that cannot yet support a complete `run_id`.

Every observation, including every warning displayed in `source_notes`, must use the complete observation structure. All observation keys must be present; `observation_id`, `source_id`, `observation_type`, `evidence_location`, `confidence`, and `promotion_decision` must not be null. Use `promotion_decision = not_promoted_yet` unless a reviewed decision says otherwise. Add a short source excerpt to `original_text` whenever concise wording is available; use null only when the source does not provide a useful compact excerpt.

Export warnings and other observations to `data/interim/source_observations.jsonl`. For each source, reconcile the JSONL observation count and IDs against the observation rows in the review workbook so that `source_notes` is not a workbook-only holding area.

## File Routing

- Original public PDFs: `data/raw/papers/` or the matching raw-source folder.
- Per-source extraction JSON, five CSVs, and one review workbook: `data/interim/<source_id>/`.
- Cross-source observation pool: `data/interim/source_observations.jsonl`.
- Human-reviewed and approved data: `data/processed/`.
- Do not create redundant version directories unless the user requests versioned outputs.
- Do not place canonical collected research data only in `outputs/`.
- Keep public and confidential internal data separable; treat internal data as sensitive.

## Completion Checks

Before reporting a paper extraction complete:

- Validate schema column names, order, and `run_id` relationships across all five tables.
- Confirm `data_type` and route-specific `target_track`; do not use vague values such as `priority`.
- Check active metals, catalyst preparation, particle size or qualitative particle evidence, BET and pore data.
- Check all temperature stages, individual gas flows, time, pressure, catalyst mass, calculated-value labels, and discussion-level observations.
- Check yield definition, CNT-type evidence, dimensions, Raman direction, TGA meaning, post-treatment, and residual-metal gaps.
- Check that cost/scale rows contain reported facts and missing fields, not premature recommendations.
- Check that valuable source notes were exported to the observation pool without creating new formal fields.
- Check that every warning and observation is fully structured, exported to JSONL, and count-reconciled by `source_id`.
- Check that mixed CNT products use `partial_mixed` rather than a misleading clean `yes`, and that author-claimed scale is separated from actual batch evidence.
- Keep all first-pass runs at `needs_review`.

Run:

```text
python scripts/validation/validate_tables.py <data_directory>
```

Do not claim completion while validation errors remain.

## P001 Regression Focus

Use Dubey et al. 2012 as a compact regression case. Preserve three runs (`SG-1`, `SG-2`, `SG-3`), Fe-Mo/MgO chemistry, stage-separated catalyst treatment and CNT growth, gas flows, carbon-weight-gain definition, Raman direction, TGA caveat, `needs_review` status, unquantified Mo cost impact, and mechanism/failure/scale observations. SG-1 must not appear as a clean CNT-type success: use `partial_mixed` for its t-MWCNT/MWCNT flags and retain the carbon-fiber mixture warning. Preserve `scale_level_claimed = author_claimed_large_scale; actual_0.1g_lab_batch` and use `scale_level = lab_batch_large_diameter_tube` for its supported process-stage scale. Detailed expected values are in the project Skill.
