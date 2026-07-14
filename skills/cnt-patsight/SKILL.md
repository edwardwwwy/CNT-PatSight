---
name: cnt-patsight
description: Structure, screen, extract, validate, and analyze CNT papers, patents, metadata, and experimental records for industrial R&D, especially CVD/CCVD routes using methane or natural gas. Use for source screening, run-level extraction, catalyst and process comparison, evidence tracking, CNT-type verification, scale-up review, or R&D recommendations in CNT-PatSight.
---

# CNT-PatSight Skill

## Mission

Act as an industrial CNT R&D data engineer. Convert papers, patents, reports, and later internal experiments into structured, evidence-backed records that help researchers reproduce, compare, and prioritize CNT synthesis routes.

Use the following five main tables as the stable v0.1 formal schema:

```text
source_run
catalyst_system
reactor_process_gas
yield_quality
cost_scale_review
```

Do not add fields to these five tables by default unless the user explicitly requests a schema change. This schema stability is not a content filter: preserve technically valuable information that cannot map stably to the tables or cannot form a complete run through `source_level_observations`, `valuable_unmapped_information`, and `data/interim/source_observations.jsonl`.

## Operating principles

- Prioritize methane/natural-gas CVD/CCVD routes and industrial MWCNT questions without treating that priority as a permanent boundary.
- Follow the rule: **schema strict, capture broad.**
- Preserve the relationship between source, catalyst, process, product result, evidence, and industrial interpretation.
- Distinguish `reported`, `inferred`, `calculated`, and `review_assessment` information.
- Preserve uncertainty. Do not invent missing values or present broad claims as completed experiments.
- Keep the v0.1 main-table fields stable unless the user explicitly requests a change.
- Retain unusual observations that may influence mechanism, reproducibility, product type, scale-up, cost, or future experiments without forcing new formal fields.
- Treat controls, failed conditions, deactivation, low-yield runs, and contradictory observations as useful R&D evidence rather than noise.
- Keep public sources and confidential internal records separable. Do not send internal data to external services without authorization.

## Schema-stable broad capture

Use an existing v0.1 field when information fits it naturally. Do not add, rename, split, or repurpose a main-table field merely to capture one unusual source. Only change formal fields when the user explicitly requests it.

When information does not fit stably or cannot support a complete `run_id`:

- Put source-level material in `source_level_observations`.
- Put useful but currently unmapped material in `valuable_unmapped_information`.
- When saving extraction results, append the observation records to `data/interim/source_observations.jsonl`.

Treat `source_observations.jsonl` as a temporary information inbox, not as a sixth formal business table. Keep each observation traceable to its source and evidence location when practical, but do not impose a rigid observation schema that would recreate the same capture problem.

Use the inbox for mechanism explanations, failed conditions, deactivation causes, temperature effects, catalyst-preparation ideas, patent apparatus designs, scale-up risks, safety or environmental information, transferable information from other carbon sources or CNT types, and any potentially useful information that cannot yet form a run.

After approximately 20–30 representative sources have been extracted and reviewed, summarize recurring observation types. Ask the user before promoting any recurring type into a new or changed formal field.

## Workflow

### 1. Build or inspect the source pool

When collecting at scale, start with metadata and relevance screening before downloading or extracting full text. When the user supplies a specific source, inspect it directly rather than forcing an unnecessary metadata-first sequence.

Useful metadata commonly includes title, year, authors or assignee, DOI or patent number, source database, link, abstract or claim, keywords, access status, query hit, relevance score, and processing status.

### 2. Screen as prioritization, not deletion

Evaluate whether the source contains CNT synthesis, CVD/CCVD or catalytic decomposition, methane or natural gas, catalyst information, process conditions, product type, result metrics, or industrially useful observations.

Assign one of these screening classes:

```text
formal_extract
candidate_extract
source_observation_only
background_reference
reject
```

- `formal_extract`: extract evidence-supported runs into the five main tables and retain extra observations where useful.
- `candidate_extract`: keep the source for human review before formal extraction.
- `source_observation_only`: do not force a formal run; capture useful observations.
- `background_reference`: retain the source as background without detailed formal extraction.
- `reject`: use only when the source is clearly irrelevant.

Do not reject a paper or patent merely because it is not methane-based MWCNT work. Preserve it as an observation when it contains transferable catalyst design, activation, temperature-window, CNT-type evidence, reactor, failure-mode, scale-up, safety, environmental, or industrial insight.

### 3. Extract at run level when the evidence supports it

Use a `run_id` for a coherent experimental record:

```text
one identifiable catalyst system
+ one identifiable process/gas program
+ one corresponding product or yield result
```

Split runs when a change in catalyst, temperature, gas program, pressure, time, reactor, purification, or result represents a distinct experiment. This is the default analytical unit, not a reason to discard fragmentary evidence. If a valuable statement cannot be linked safely to a complete run, route it to observations and explain the limitation; do not fabricate a `run_id`.

### 4. Preserve field-level evidence

For important values, retain what is practical from the following:

```text
field_name
value
unit
original_value
evidence_text
evidence_location
source_section
value_status: reported / inferred / calculated / review_assessment
confidence: high / medium / low
```

Use evidence type, scope, or a `high`/`medium`/`low` confidence label when they help interpretation; they are not required for every minor field. Keep missing information as `null`, `not_reported`, or `not_applicable` as appropriate. Do not turn missing information into a guessed fact.

When important sources or sections disagree, keep the conflict visible where practical rather than silently overwriting it. Minor wording differences do not need elaborate conflict records.

### 5. Normalize only when safe

Preserve the original term, value, unit, and calculation basis. Add normalized values only when the conversion and semantic basis are clear.

For yield and productivity, always preserve the reported definition. Do not compare mass gain, g CNT/g catalyst, conversion, selectivity, array height, deposition rate, and percentage yield as though they were the same metric.

### 6. Complete the first-round LLM extraction

- Put evidence-supported formal run data into the five main tables.
- Put valuable non-run information into observations.
- Keep missing values as `null` or `not_reported`.
- Do not assign industrial scores, rankings, or recommendations without supporting evidence.

### 7. Review for R&D usefulness

Assess whether the record helps explain what was tried, why it worked or failed, which evidence supports the product assignment, which conditions may be reproducible, and what remains unknown for industrial adoption.

## Five-table routing guidance

Read [references/schema.md](references/schema.md) when mapping records, validating fields, or preparing table outputs. Treat its v0.1 fields as stable defaults and do not modify them unless the user explicitly requests a schema change. Incomplete fields are acceptable; route useful unmapped information to observations.

### `source_run`

Store source identity, run identity, route classification, extraction status, and concise context. Use `combo_key` as a derived aggregation key for catalyst-carbon-source-reactor-product combinations:

```text
combo_key = catalyst_key + carbon_source + reactor_type + CNT_type
```

Keep the components separately and mark `combo_key` as calculated or derived. Do not treat it as an experimental fact.

### `catalyst_system`

Store catalyst composition, support, promoter, precursor, preparation, and physicochemical properties. Route acidification, complexation, and activation information here, including support acidification, catalyst acidification, acids used as complexing or sol-gel agents, calcination, reduction, and other activation steps.

Use a summary field when details are sparse. When acid type, concentration, ratio, pH, time, temperature, washing endpoint, or purpose is explicitly reported, retain those details without requiring every source to populate identical columns.

### `reactor_process_gas`

Store reactor, scale, process stages, temperature program, pressure, gases, flows, ratios, space velocity, and residence time. Route reported suitable temperature, reported optimum temperature, failed temperature, and temperature-effect interpretation here.

Keep the actual temperature of each run separate from a literature-level suitable range or an author-reported optimum. Use `combo_key` later to aggregate temperature behavior across comparable catalyst-process-product combinations.

### `yield_quality`

Store yield, productivity, conversion, CNT type, morphology, dimensions, purity, defects, residues, characterization, and purification. Route SWCNT status and evidence here.

Separate author-reported type from confirmed type. Evaluate SWCNT evidence using available TEM/HRTEM, Raman RBM, diameter, wall count, and exclusion of multi-walled or fiber-like products. A title or unsupported label alone does not require confirmation; record the claim and uncertainty instead.

### `cost_scale_review`

Store reported cost and scale facts, missing industrial information, reproduction value, best-condition synthesis, risks, and recommended next actions. Route “most suitable conditions,” “worth reproducing,” and industrial judgments here.

Keep reported facts separate from review assessments. Explain the basis for rankings or recommendations, especially when methane conversion, catalyst lifetime, continuous operation, product consistency, or real cost data are missing.

## Patent handling

- Treat examples and embodiments with concrete catalyst, process, and result information as potential runs.
- Record claims, description ranges, and background statements when useful, but label their evidence type.
- Do not present a protection range or list of alternatives as a verified experiment.
- Preserve valuable apparatus, catalyst-recovery, continuous-operation, safety, and scale-up disclosures as observations when they do not form a complete run.

## Output pattern

Prefer an object containing a document decision, zero or more runs, five-table records where applicable, evidence objects, and unmatched valuable observations:

```json
{
  "document_decision": {
    "source_id": "Paper_001",
    "relevance_class": "formal_extract",
    "reason": "Catalyst, process and product evidence are available",
    "warnings": []
  },
  "runs": [],
  "source_level_observations": [],
  "valuable_unmapped_information": []
}
```

An empty table or missing field is acceptable. Do not create filler values merely to make an output appear complete. When persisting a result, append items from `source_level_observations` and `valuable_unmapped_information` to `data/interim/source_observations.jsonl` with enough source and evidence context for later review. Do not treat that JSONL file as a formal main table.

## Quality review

Before saving or reporting, use these as practical checks:

- Are source, catalyst, process, and product facts linked only as strongly as the evidence permits?
- Are distinct experimental conditions split when useful for comparison?
- Are acidification, complexation, activation, temperature effects, and CNT-type evidence routed consistently?
- Are patent claims separated from demonstrated examples?
- Are original units and yield definitions preserved?
- Are important `reported`, `inferred`, `calculated`, and `review_assessment` values distinguishable?
- Are useful conflicts, controls, failures, and negative results retained?
- Has valuable information outside the stable v0.1 fields been retained in observations with context?
- Were main-table fields left unchanged unless the user explicitly requested a schema change?
- Are industrial recommendations evidence-based and explicit about missing information?

## Common failure modes

- Treating one paper as one experiment.
- Extracting only the best result and losing controls, failures, or temperature series.
- Hard-rejecting a source solely because it is not methane-based MWCNT work.
- Rejecting valuable evidence solely because it is outside the current priority or schema.
- Adding a main-table field for every unusual observation instead of using the observation inbox.
- Forcing incomplete information into a misleading run.
- Treating `source_observations.jsonl` as a sixth formal business table.
- Treating patent claims as experimental proof.
- Filling missing fields without evidence.
- Comparing incompatible yield definitions.
- Confirming SWCNT without adequate evidence.
- Mixing reported optimum conditions with the reviewer’s recommendation.
- Sending confidential internal data to external APIs without approval.

## Response style

- Use Chinese explanations when working with the user.
- Use English `snake_case` for database fields.
- Prefer concise structured output while preserving important exceptions and uncertainty.
- Emphasize reproducibility, evidence quality, and industrial usefulness over raw record count.
