---
name: cnt-patsight
description: Extract, normalize, validate, and review CNT papers, patents, and experimental records for CNT-PatSight. Use for source registration, screening, PDF/full-text extraction, run planning, eight-table mapping, catalyst/process/product comparison, CNT-type verification, centralized evidence indexing, conflict review, field-dictionary maintenance, and curated CVD/CCVD CNT R&D data preparation.
---

# CNT-PatSight Curated Extraction

## Operating Goal

Build a traceable database that remains usable from the current curated sample through several hundred papers and patents.

- Optimize for accuracy, auditability, stable joins, and low schema sparsity.
- Keep first-pass records at `needs_review` until a human checks critical fields.
- Do not build crawlers, dashboards, ML predictions, or industrial scoring systems unless requested.
- Generate `ml_runs_clean.csv` later from reviewed normalized tables; never maintain it manually.

Read [references/schema.md](references/schema.md) before table mapping, migration, validation, or field changes.

## Stable Eight-Table Contract

Maintain exactly these source tables:

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

Maintain `config/field_dictionary.csv` as the machine-readable field contract. Treat it as documentation, not a ninth business table.

Use the tables as follows:

- `source_master`: one row per paper, patent, review, or internal source.
- `source_run`: one row per defensible experimental run or patent example.
- `catalyst_system`: catalyst composition, preparation, texture, state, and deactivation facts.
- `reactor_process_gas`: one row per process stage, including role-based gas fields.
- `yield_quality`: primary yield identity, normalized results, CNT identity, morphology, Raman/TGA, purification, and application properties.
- `cost_scale_review`: reported scale/cost/stability/safety facts plus later human industrial assessments.
- `evidence_index`: all source locations, excerpts, calculated/inferred status, and target-field links.
- `review_issue_log`: only actual conflicts, ambiguities, missing critical evidence, or human-review decisions.

Do not store source title, DOI, authors, year, or venue in `source_run`. Do not store `evidence_text`, evidence location, or confidence in the five run-fact tables. Do not create placeholder issue rows for clean records.

## Field Admission Rule

Apply **schema strict, capture broad**.

Add a dedicated column only when at least one condition holds:

1. It is an identifier, foreign key, status, or essential interpretation field.
2. It is likely to be populated across a substantial share of the target paper/patent corpus.
3. It is conditionally common within a major source class or route and has stable semantics.
4. It may be less frequent but is critical for CNT identity, safety, scale-up, reproducibility, or industrial review.

Do not add a column merely because one current paper reports it. Do not delete a field merely because the current six papers omit it. Evaluate expected use across several hundred papers and patents.

Prefer a stable summary field when detail is valuable but heterogeneous or rarely quantified. Examples:

- use `quantitative_cost_summary`, not separate per-kg columns for every gas and energy input;
- use `application_property_summary`, not dedicated conductivity, viscosity, and density columns unless corpus evidence later justifies promotion;
- use role-based gas fields plus `gas_composition_summary`, not one permanent pair of columns for every possible molecule;
- use `Raman_ratio_type` with `Raman_ratio_value`, not two competing ratio-direction columns.

Route source-specific detail to `evidence_index`. Route unresolved conflicts and critical gaps to `review_issue_log`. Propose formal schema changes only after checking recurrence across representative papers and patents and update the field dictionary at the same time.

## Per-Source Workflow

Complete these steps in order.

### 1. Register the source

Create one `source_master` row with stable `source_id`, source type, title, year, identifier, authors or assignee, venue, link, local file, screening class, and review states.

Use one screening class:

```text
formal_extract
candidate_extract
source_observation_only
background_reference
reject
```

Do not reject useful catalyst, process, failure, CNT-type, scale, safety, or environmental evidence merely because the route is outside the current methane-MWCNT priority.

### 2. Plan runs

Create one `run_id` only when evidence supports:

```text
one identifiable catalyst system
+ one identifiable process/gas program
+ one corresponding product or result
= one run
```

Split materially different catalysts, temperatures, gas programs, times, pressures, reactors, purification conditions, or results. Do not default to one run per source and do not fabricate a run from discussion fragments.

Represent heating, pretreatment/reduction, growth, and cooling as separate `reactor_process_gas` rows when reported.

### 3. Build an evidence map

Check the abstract, experimental section, catalyst preparation, synthesis procedure, tables, figure captions, results, conclusion, supplementary material, patent examples, and claims.

Create evidence rows that point from `evidence_index` to the affected table, record, and fields. Preserve original values, units, formulas, and terminology before normalization. Mark each row as `reported`, `calculated`, `inferred`, or `review_assessment` through `value_status`.

### 4. Populate facts

Populate the five run-fact tables without duplicating source metadata or evidence locations. Preserve meaningful qualitative states such as:

```text
not_reported
not_applicable
non_uniform_not_quantified
qualitative_only
uncertain
```

Do not replace a reported qualitative fact with an empty cell.

### 5. Register review issues

Create a `review_issue_log` row when evidence is internally conflicting, definitions are ambiguous, run splitting is uncertain, a critical value is missing, or a human decision is required.

- Link the relevant `evidence_id` values.
- Keep `review_status = open` until reviewed.
- Record the resolution without overwriting the source-reported alternatives.
- Do not use the issue table as a general observation dump.

## Domain Guardrails

### Catalyst

- Include every metal central to catalyst function in `active_metals`; Fe-Mo means `Fe; Mo` even when Mo is also a promoter.
- Distinguish acid washing, support/catalyst acidification, acid complexing, and other preparation modifiers.
- Record citric-acid sol-gel use as `acid_complexing`, not generic acid treatment.
- Keep drying, calcination/thermal decomposition, reduction, activation, and CNT growth conditions separate.
- Preserve particle-size ranges and qualitative states separately; do not force non-uniform particles into a numeric mean.
- Retain BET, pore, phase, dispersion, lifetime, and deactivation evidence when reported; these are conditionally common and analytically valuable even if absent in the current sample.

### Reactor, process, and gas

- Use one row per process stage.
- Preserve reactor type/material/size, catalyst loading, temperature, time, pressure, heating/cooling, and GHSV/residence time when reported.
- Map gases by role: carbon source, reducing gas, inert gas, and cofeed/reactive gas. Preserve the complete original mixture in `gas_composition_summary`.
- Keep original and standardized flows. Mark calculated flows and ratios explicitly in evidence.
- Put discussion-only temperature trends in evidence unless they define a run or a review issue.

### Yield and quality

- Preserve the primary metric name, original value/unit expression, definition, formula, normalized value/unit, and normalization note.
- Do not relabel carbon weight gain, g CNT/g catalyst, productivity, conversion, carbon efficiency, growth rate, or array height as equivalent metrics.
- Keep normalized CNT yield/productivity and carbon-source conversion fields because they recur across major CNT synthesis and reforming source classes, even when not present in every paper.
- Keep author-reported and evidence-confirmed CNT type separate.
- State mixed products in `product_mixture_summary`; do not turn a partial MWCNT/t-MWCNT component into a clean success.
- Confirm SWCNT/few-wall assignments with suitable TEM/HRTEM, RBM, diameter, or wall-count evidence.
- Store Raman direction in `Raman_ratio_type` and the matching value in `Raman_ratio_value`.
- Keep as-synthesized TGA carbon content separate from post-purification product purity.
- Retain length, residue, BET-product, purification, and application-property summaries when reported; avoid one column per rare application test.

### Cost, scale, and review

- Separate demonstrated scale from author-claimed scale.
- Preserve throughput/capacity, continuous duration, catalyst lifetime/reuse, batch stability, scale-up problems, safety, and emissions when reported.
- Use a compact quantitative cost summary; do not create mostly empty dedicated columns for every possible gas, feedstock, utility, and waste stream.
- During first pass, leave industrial readiness, reproduction priority, industrial score, and recommended action unfilled unless a human explicitly assesses them.
- Keep known facts visible even when cost impact is unquantified; the catalyst and process tables supply material and gas facts for later automated derivation.

## Status Boundary

Keep Codex first-pass `source_master.extraction_status` and every `source_run.extraction_status` at `needs_review`.

Change to `reviewed` only after a human verifies:

- source identity and run splitting;
- catalyst composition/preparation and thermal treatment;
- reactor stages, temperature, pressure, gases, flows, time, and loading;
- yield identity, value, unit, definition, and calculations;
- CNT type, mixture caveats, dimensions, Raman direction, TGA meaning, and purification;
- evidence links and all open review issues.

## Completion Checks

Before reporting extraction complete:

1. Validate all eight CSV files, column order, identities, and foreign keys.
2. Confirm every catalyst, process-stage, yield, and cost/scale record has linked evidence.
3. Confirm each issue links to existing evidence and retains unresolved alternatives.
4. Confirm source metadata exists only once in `source_master`.
5. Confirm no evidence-location columns remain in the five run-fact tables.
6. Confirm all first-pass runs remain `needs_review`.
7. Run `python scripts/validation/validate_tables.py <data_directory>` and fix every error.

## P001 Regression Case

For Dubey et al. 2012, preserve:

- three runs: SG-1, SG-2, and SG-3;
- Fe-Mo/MgO with `active_metals = Fe; Mo`;
- citric acid as `preparation_modifier = acid_complexing`;
- catalyst decomposition at 700 °C for 2 h separately from CNT growth at 900 °C for 30 min;
- 0.1 g loading and separate heating, pretreatment, growth, and cooling stages;
- 73%, 452%, and 370% as carbon weight gain;
- Raman values 3.6, 4.7, and 3.1 with `Raman_ratio_type = IG/ID`;
- 43%, 85%, and 82% as as-synthesized TGA carbon content, not application-grade purity;
- SG-1 mixed t-MWCNT/MWCNT/carbon-fiber warning in `product_mixture_summary`;
- author-claimed large scale separately from the demonstrated 0.1 g laboratory batch;
- Mo shielding, air-decomposition failure, Ar/H2 dispersion improvement, scale claim, and high-Mo interpretation as evidence rows;
- all conflicts and critical gaps as linked open review issues.

## Response Style

- Explain results in Chinese.
- Use English `snake_case` for fields and controlled values.
- Emphasize evidence quality, uncertainty, and review state over record count.
