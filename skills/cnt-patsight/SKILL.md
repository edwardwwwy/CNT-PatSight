---
name: cnt-patsight
description: Extract, structure, validate, and review CNT papers, patents, and experimental records for CNT-PatSight. Use for source screening, PDF or full-text extraction, run planning, five-table mapping, catalyst/process/product comparison, CNT-type verification, evidence tracking, source observations, patent examples, and curated CNT R&D data preparation, especially for CVD/CCVD routes.
---

# CNT-PatSight Curated Extraction

## Current Phase

Treat the current phase as **v0.1 curated-paper extraction**.

- Process about 10 high-quality papers manually provided by the user.
- Produce accurate, traceable, database-ready sample records.
- Keep first-pass records at `needs_review` until human verification.
- Use the samples to test the stable five-table schema.
- Do not build bulk pipelines, crawlers, web products, local-model systems, ML predictions, complex schemas, or industrial scoring systems unless explicitly requested.

Optimize for: **extract accurately, preserve evidence, support review**.

## Stable Data Contract

Use only these five formal business tables:

```text
source_run
catalyst_system
reactor_process_gas
yield_quality
cost_scale_review
```

Follow **schema strict, capture broad**:

- Do not add, remove, rename, split, or repurpose formal fields by default.
- Do not create another formal business table by default.
- Preserve useful information outside the five tables in `source_level_observations`, `valuable_unmapped_information`, and `data/interim/source_observations.jsonl`.
- Treat `source_observations.jsonl` as a temporary observation pool, not a sixth business table.
- After 20-30 representative sources, summarize recurring observation types and ask the user before promoting any into the formal schema.

Read [references/schema.md](references/schema.md) when mapping or validating the five tables. Treat it as field vocabulary, not permission to change the schema silently.

## Before Extracting Each Paper

Complete these four steps before filling the five tables.

### 1. Source registration

Establish:

- `source_id`
- `source_type`
- title
- year
- DOI or patent number
- authors or assignee
- document class: paper, patent, or review

### 2. Screening classification

Use exactly one class:

```text
formal_extract
candidate_extract
source_observation_only
background_reference
reject
```

Use `reject` only for clearly irrelevant material. Do not reject a source merely because it is outside methane-MWCNT priority. Preserve transferable catalyst, activation, temperature, atmosphere, failure, CNT-type, reactor, scale-up, safety, or environmental evidence as observations.

### 3. Run plan

List proposed `run_id` values before filling tables. Create one run only when evidence supports:

```text
one identifiable catalyst system
+ one identifiable process/gas program
+ one corresponding product or yield result
= one run_id
```

Split runs when catalyst, temperature, gas composition, gas flow, pressure, time, reactor, purification, or product result changes materially. Do not default to one run per paper and do not fabricate a run from fragmentary discussion.

Represent heating, pretreatment or reduction, growth, and cooling as separate `reactor_process_gas` rows when reported.

### 4. Evidence map

Locate evidence before populating fields. Check:

- abstract
- experimental section
- catalyst preparation
- CNT synthesis procedure
- tables
- figure captions
- results discussion
- conclusion

Keep important fields traceable through `evidence_text`, `evidence_location`, and `source_section` where available. Preserve original terminology, values, units, and formulas before normalization.

## Extraction Stages

### `first_pass_extraction`

- Extract reported facts.
- Add only clear, useful calculations; record the formula and calculated status in the applicable note or evidence record.
- Preserve missing and qualitative states without guessing.
- Route valuable non-run information to observations.
- Keep `extraction_status = needs_review`.
- Store only reported cost, scale, throughput, reuse, safety, emission/waste facts, and missing industrial fields.
- Leave `industrial_value_score`, `reproduction_priority`, `recommended_next_action`, and unsupported `major_cost_driver` null.

### `human_or_review_assessment`

Enter this stage only when the user or a human reviewer explicitly reviews the record.

- Compare routes and results.
- Add reproduction priorities, industrial judgments, cost drivers, or recommendations only with an evidence basis.
- Mark judgments as `review_assessment`.
- Change `extraction_status` to `reviewed` only after the critical-field review described below.

Keep `reported`, `inferred`, `calculated`, and `review_assessment` distinguishable.

## Five-Table Routing

### `source_run`

- Store source and run identity, route classification, extraction status, and concise context.
- Use `data_type = experimental_run` for demonstrated paper experiments; use explicit values such as `patent_example` or `review_context` when appropriate.
- Use a route-specific `target_track`, such as `CH4_CCVD_t-MWCNT`; do not use `priority`.
- Derive `combo_key` from separately retained catalyst, carbon source, reactor, and CNT-type components. Mark it derived/calculated, not reported.

### `catalyst_system`

- Store active metals, support, promoter, precursors, preparation, complexation, drying, thermal decomposition/calcination, reduction, activation, particle evidence, BET/pore data, phases, and dispersion.
- Include every metal central to catalyst function in `active_metals`.
- Keep promoter designation separate from the complete active-metal description.
- Keep catalyst preparation temperatures separate from CNT growth temperatures.

### `reactor_process_gas`

- Store one row per process stage.
- Store reactor, catalyst loading, bed position, temperature, time, pressure, individual gases and flows, ratios, and heating/cooling conditions.
- Prefer `pretreatment` when the source says pretreatment; do not replace it with vague `activation`.
- Put cross-run or discussion-level temperature effects in observations rather than forcing them into run fields.

### `yield_quality`

- Preserve yield identity and definition, CNT identity and evidence, morphology, dimensions, Raman data, TGA/carbon content, residuals, characterization, and post-treatment.
- Keep author-reported CNT type separate from evidence-supported confirmation.
- Do not let boolean-like type fields hide mixed products. Use `partial_mixed` for `is_t_MWCNT` or `is_MWCNT` when the supported type is only one component of a materially mixed product; reserve `yes` for an unambiguous assignment that does not imply a misleading clean success. Repeat the mixture in `CNT_type_evidence` or notes.
- Confirm SWCNT only with suitable evidence such as TEM/HRTEM, Raman RBM, diameter, or wall count.
- Keep TGA carbon content distinct from post-purification application-grade CNT purity.

### `cost_scale_review`

- During first pass, store reported material, scale, cost, throughput, continuous-operation, reuse, safety, emission/waste facts, and missing industrial fields.
- Do not treat an unquantified effect as an absent fact.
- Do not generate recommendations or scores during first pass.
- Separate author-claimed scale from demonstrated experimental scale. When both matter, preserve both in `scale_level_claimed`, for example `author_claimed_large_scale; actual_0.1g_lab_batch`.

In `reactor_process_gas.scale_level`, use a concrete, evidence-backed setup label when reactor size and loading support it, rather than leaving the field empty merely because throughput is unreported. Do not translate a large tube diameter into industrial throughput.

## Field-Level Cautions

### 1. Qualitative evidence versus missing data

Do not leave a field empty when the source provides relevant qualitative evidence but no number. For `catalyst_particle_size_nm`, use an appropriate state when needed:

```text
not_reported
not_applicable
non_uniform_not_quantified
qualitative_only
uncertain
```

For example, when particles are explicitly described as non-uniform or agglomerated without a size value, use `non_uniform_not_quantified`, not an empty cell.

### 2. Active metals versus promoter

Include all core synergistic metals. For Fe-Mo/MgO, Co-Mo/MgO, or Ni-Mo/MgO, include Mo in `active_metals` when the source repeatedly describes bimetallic clusters or interactions. Mo may also appear in `promoter`.

Example:

```text
active_metals = Fe; Mo
promoter = Mo
```

### 3. Acid treatment versus acid complexing

Distinguish:

```text
acid_washing
support_acidification
catalyst_acidification
acid_complexing
```

For citric acid used as a sol-gel complexing agent, use:

```text
acid_treatment_flag = acid_complexing_only
acid_treatment_type = acid_complexing
```

Do not label it generic acid treatment or acid washing.

### 4. Temperature semantics

Keep drying, catalyst calcination or thermal decomposition, reduction or pretreatment, CNT growth, cooling, author-reported optimum, and patent claim ranges distinct. Do not mix `700 °C for 2 h` catalyst thermal decomposition with `900 °C for 30 min` CNT growth.

### 5. Gas flows

Split reported flows into carbon source, CH4, H2, N2, Ar, other gas, total flow, and `gas_ratio_summary`. Do not retain only total flow when component flows are available. Mark extractor-calculated fractions or ratios as calculated and retain their formula and reported inputs.

### 6. Yield definition

Preserve the current schema equivalents of:

- original yield name/value/unit
- standardized value/unit
- original definition and formula
- standardization note or status

Do not compare or relabel carbon weight gain, g CNT/g catalyst, methane conversion, carbon efficiency, productivity, growth rate, and array height as the same metric.

For carbon weight gain, preserve:

```text
[(w_tot - w_cat) / w_cat] x 100
```

### 7. Raman ratio direction

Treat `IG/ID` and `ID/IG` as inverse quantities. Put reported `IG/ID` only in `Raman_IG_ID`. Calculate a reciprocal only when useful, retain the reported direction, and mark the reciprocal calculated with its formula.

### 8. TGA carbon content

When TGA measures the as-synthesized product, state:

```text
TGA carbon content of as-synthesized product, not post-purification application-grade purity.
```

Do not overstate it as commercial purified-product purity.

### 9. Cost facts versus unquantified cost impact

Record a known material fact even when no cost analysis exists. If Mo is explicitly present, do not use `contains_expensive_metal = not_reported`. Use a statement such as:

```text
Mo present; cost impact not quantified
```

Keep the missing cost analysis in `missing_critical_fields` or an observation.

### 10. First-pass industrial boundary

During first pass, record only reported facts, clear calculated values, missing critical fields, and observations. Do not fill industrial scores, reproduction priority, recommendations, or unsupported major cost drivers.

## Observation Pool

Persist valuable information that does not fit the five tables to:

```text
data/interim/source_observations.jsonl
```

Prefer these `observation_type` values:

```text
mechanism
failure_mode
catalyst_preparation_hint
temperature_effect
scale_up_signal
safety_environment
data_gap
quality_warning
transferable_route
patent_apparatus
other
```

Use this complete structure for every observation, including warnings shown in `source_notes`:

```json
{
  "observation_id": null,
  "source_id": null,
  "related_run_id": null,
  "observation_type": null,
  "topic_tags": [],
  "value_summary": null,
  "original_text": null,
  "evidence_location": null,
  "why_valuable": null,
  "confidence": null,
  "promotion_decision": "not_promoted_yet"
}
```

All keys must be present. `observation_id`, `source_id`, `observation_type`, `evidence_location`, `confidence`, and `promotion_decision` are required and non-null. Use `promotion_decision = not_promoted_yet` by default. Put a short source excerpt in `original_text` when useful wording exists; keep it concise and use null only when no compact source wording is available.

Export every warning and observation to the JSONL pool. Reconcile the per-source IDs and counts between `source_notes` and `data/interim/source_observations.jsonl`; no warning may exist only in the workbook.

Preserve mechanisms, failures, deactivation, catalyst-preparation hints, temperature effects, data gaps, quality warnings, scale-up risks, safety/environmental information, patent apparatus, transferable routes, and valuable information that cannot support a complete run.

## Extraction Status

Keep every Codex first-pass run at:

```text
extraction_status = needs_review
```

Use `reviewed` only after a user or human reviewer verifies:

- run splitting and `run_id`
- catalyst composition, active metals, and preparation
- calcination, thermal decomposition, reduction, or pretreatment
- growth temperature and gas flows
- yield value, unit, and definition
- CNT type and supporting evidence
- diameter and wall number
- Raman ratio direction
- TGA carbon-content meaning
- `evidence_text` and `evidence_location`
- observation export

## After Extraction Checklist

### `source_run`

- Check that the paper was not incorrectly reduced to one run.
- Check unique `run_id` values and cross-table relationships.
- Check explicit `data_type` and route-specific `target_track`.
- Check that `combo_key` is derived/calculated.
- Keep first-pass status at `needs_review`.

### `catalyst_system`

- Check all bimetallic active metals and promoter separation.
- Check acid washing, acidification, and complexing distinctions.
- Check quantitative particle size or qualitative particle evidence.
- Reconcile BET area, pore size, and pore volume with the source table.

### `reactor_process_gas`

- Check catalyst-treatment and CNT-growth temperatures separately.
- Check pretreatment/reduction, growth, and cooling stages.
- Check individual CH4, H2, N2, Ar, and other-gas flows.
- Check calculated-value labels and formulas.
- Keep discussion-level temperature effects in observations when not run facts.

### `yield_quality`

- Check original yield definition and metric identity.
- Check CNT-type evidence and avoid title-only SWCNT confirmation.
- Check that mixed products use `partial_mixed`, not a clean-success `yes`, in boolean-like CNT-type fields.
- Check Raman direction.
- Check that TGA carbon content is not presented as application-grade purity.

### `cost_scale_review`

- Keep reported facts separate from missing industrial information.
- Do not generate premature recommendations or scores.
- Keep `review_assessment` separate from reported facts.
- Do not turn unquantified cost impact into absence of a known material.

### Observations

- Export every warning and valuable source note to `source_observations.jsonl`.
- Check every observation for complete keys and required non-null identity, type, evidence, confidence, and promotion fields.
- Reconcile per-source observation IDs and counts between `source_notes` and JSONL.
- Add short `original_text` excerpts where the source provides concise wording.
- Give mechanism, failure, data-gap, quality, and scale signals evidence locations.
- Do not create formal fields merely to store one-off observations.

Run `scripts/validation/validate_tables.py` when CSV tables are produced. Do not report completion while validation errors remain.

## P001-Style Regression Example

For Dubey et al. 2012, verify these typical failure points:

- Produce three runs: `SG-1`, `SG-2`, and `SG-3`.
- Use `data_type = experimental_run`, `target_track = CH4_CCVD_t-MWCNT`, and `extraction_status = needs_review`.
- Use SG-1 `catalyst_particle_size_nm = non_uniform_not_quantified`; use SG-2/SG-3 `3-6`.
- Use Fe-Mo/MgO `active_metals = Fe; Mo`.
- Treat citric acid as `acid_complexing`, not acid washing.
- Keep `700 °C for 2 h` catalyst thermal decomposition separate from `900 °C for 30 min` CNT growth.
- Preserve 0.1 g catalyst loading and separate heating, pretreatment, growth, and cooling rows.
- Preserve 73%, 452%, and 370% as carbon weight gain, not methane conversion.
- Put reported values 3.6, 4.7, and 3.1 in `Raman_IG_ID`, not `Raman_ID_IG`.
- Label 43%, 85%, and 82% as as-synthesized TGA carbon content, not application-grade purity.
- Use SG-1 `is_t_MWCNT = partial_mixed` and `is_MWCNT = partial_mixed`; retain the t-MWCNT/MWCNT/carbon-fiber caveat in evidence or notes.
- Use `contains_expensive_metal = Mo present; cost impact not quantified`.
- Use `scale_level_claimed = author_claimed_large_scale; actual_0.1g_lab_batch` and process-stage `scale_level = lab_batch_large_diameter_tube`.
- Structure and export all five source warnings as observations with IDs, source, type, evidence location, confidence, and short original text where available.
- Export Mo shielding, air-decomposition failure, Ar/H2 dispersion improvement, scale-up claim, and high-Mo interpretation as observations.

## Response Style

- Explain results in Chinese.
- Use English `snake_case` for fields and controlled values.
- Prefer concise, structured reporting.
- Emphasize evidence quality, uncertainty, and review status over record count.
