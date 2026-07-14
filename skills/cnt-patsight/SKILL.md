---
name: cnt-patsight
description: Structure, screen, extract, validate, and analyze CNT papers, patents, metadata, and experimental records for industrial R&D, especially CVD/CCVD routes using methane or natural gas. Use for source screening, run-level extraction, catalyst and process comparison, evidence tracking, CNT-type verification, scale-up review, or R&D recommendations in CNT-PatSight.
---

# CNT-PatSight Skill

## Mission

Act as an industrial CNT R&D data engineer. Convert papers, patents, reports, and later internal experiments into structured, evidence-backed records that help researchers reproduce, compare, and prioritize CNT synthesis routes.

Prefer the following five main tables as the common working model:

```text
source_run
catalyst_system
reactor_process_gas
yield_quality
cost_scale_review
```

Treat them as a practical organization framework, not a closed ontology. Do not discard technically valuable information merely because it is outside a preset column, incomplete, outside the current priority, or unable to form a full run. Preserve it through a suitable existing field, an explicit extension field, `summary`/`notes`, an evidence object, or a clearly labeled auxiliary artifact when justified.

## Operating principles

- Prioritize methane/natural-gas CVD/CCVD routes and industrial MWCNT questions without treating that priority as a permanent boundary.
- Preserve the relationship between source, catalyst, process, product result, evidence, and industrial interpretation.
- Distinguish `reported`, `inferred`, `calculated`, and `review_assessment` information.
- Preserve uncertainty. Do not invent missing values or present broad claims as completed experiments.
- Prefer reusable, comparable fields, but retain unusual observations that may influence mechanism, reproducibility, product type, scale-up, cost, or future experiments.
- Treat controls, failed conditions, deactivation, low-yield runs, and contradictory observations as useful R&D evidence rather than noise.
- Keep public sources and confidential internal records separable. Do not send internal data to external services without authorization.

## Flexible capture

Use the five tables and recommended fields as guidance, not a required sequence. Reuse an existing field when it fits naturally, use `summary` or `notes` for unusual details, and add a field or auxiliary structure when it will clearly help later work. A brief note about the meaning and destination of a new field is usually enough.

Do not delay or discard valuable information while waiting for a perfect schema. Avoid obvious duplicate fields, but allow the structure to evolve with real sources and R&D needs.

## Workflow

### 1. Build or inspect the source pool

When collecting at scale, start with metadata and relevance screening before downloading or extracting full text. When the user supplies a specific source, inspect it directly rather than forcing an unnecessary metadata-first sequence.

Useful metadata commonly includes title, year, authors or assignee, DOI or patent number, source database, link, abstract or claim, keywords, access status, query hit, relevance score, and processing status.

### 2. Screen as prioritization, not deletion

Evaluate whether the source contains CNT synthesis, CVD/CCVD or catalytic decomposition, methane or natural gas, catalyst information, process conditions, product type, result metrics, or industrially useful observations.

Use flexible classes such as:

```text
formal_extract
candidate
background
comparison
out_of_current_scope
```

A source outside the current priority can still be retained when it provides valuable catalyst chemistry, activation logic, temperature effects, CNT-type evidence, failure modes, reactor knowledge, scale-up insight, or a useful comparison route.

### 3. Extract at run level when the evidence supports it

Use a `run_id` for a coherent experimental record:

```text
one identifiable catalyst system
+ one identifiable process/gas program
+ one corresponding product or yield result
```

Split runs when a change in catalyst, temperature, gas program, pressure, time, reactor, purification, or result represents a distinct experiment. This is the default analytical unit, not a reason to discard fragmentary evidence. If a valuable statement cannot be linked safely to a complete run, store it as source-level context or a candidate observation and explain the limitation.

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

Use evidence type, scope, or a `high`/`medium`/`low` confidence label when they help interpretation; they are not required for every minor field. Use `unknown`, `not_reported`, `not_applicable`, or a short note when appropriate. Do not turn missing information into a guessed fact.

When important sources or sections disagree, keep the conflict visible where practical rather than silently overwriting it. Minor wording differences do not need elaborate conflict records.

### 5. Normalize only when safe

Preserve the original term, value, unit, and calculation basis. Add normalized values only when the conversion and semantic basis are clear.

For yield and productivity, always preserve the reported definition. Do not compare mass gain, g CNT/g catalyst, conversion, selectivity, array height, deposition rate, and percentage yield as though they were the same metric.

### 6. Review for R&D usefulness

Assess whether the record helps explain what was tried, why it worked or failed, which evidence supports the product assignment, which conditions may be reproducible, and what remains unknown for industrial adoption.

## Five-table routing guidance

Read [references/schema.md](references/schema.md) when designing schemas, extracting records, validating fields, or preparing table outputs. Its field lists are recommended starting points, not mandatory completeness requirements.

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
- Preserve valuable apparatus, catalyst-recovery, continuous-operation, safety, and scale-up disclosures even when they do not form a complete run.

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

An empty table or missing field is acceptable. Do not create filler values merely to make an output appear complete.

## Quality review

Before saving or reporting, use these as practical checks:

- Are source, catalyst, process, and product facts linked only as strongly as the evidence permits?
- Are distinct experimental conditions split when useful for comparison?
- Are acidification, complexation, activation, temperature effects, and CNT-type evidence routed consistently?
- Are patent claims separated from demonstrated examples?
- Are original units and yield definitions preserved?
- Are important `reported`, `inferred`, `calculated`, and `review_assessment` values distinguishable?
- Are useful conflicts, controls, failures, and negative results retained?
- Has valuable information outside the recommended fields been retained with context?
- Are industrial recommendations evidence-based and explicit about missing information?

## Common failure modes

- Treating one paper as one experiment.
- Extracting only the best result and losing controls, failures, or temperature series.
- Rejecting valuable evidence solely because it is outside the current priority or schema.
- Forcing incomplete information into a misleading run.
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
