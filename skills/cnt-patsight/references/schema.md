# CNT-PatSight eight-table schema

This reference defines the normalized source schema for several hundred CNT papers and patents. `config/schema.json` is authoritative for file names and column order; `config/field_dictionary.csv` is authoritative for field semantics and population expectations.

## Contents

- [Relationships](#relationships)
- [Sparsity policy](#sparsity-policy)
- [`source_master`](#source_master)
- [`source_run`](#source_run)
- [`catalyst_system`](#catalyst_system)
- [`reactor_process_gas`](#reactor_process_gas)
- [`yield_quality`](#yield_quality)
- [`cost_scale_review`](#cost_scale_review)
- [`evidence_index`](#evidence_index)
- [`review_issue_log`](#review_issue_log)
- [Derived and optional artifacts](#derived-and-optional-artifacts)
- [Field-change protocol](#field-change-protocol)

## Relationships

```text
source_master 1 ── n source_run
source_run    1 ── n catalyst_system
source_run    1 ── n reactor_process_gas
source_run    1 ── n yield_quality
source_run    1 ── 1 cost_scale_review

evidence_index   n ── 1 source_master
evidence_index   n ── 0..1 source_run
evidence_index   n ── 1 target record in any factual table
review_issue_log n ── 1 source_master
review_issue_log n ── 0..1 source_run
review_issue_log n ── n evidence_index through evidence_ids
```

Use `source_id` as the stable source key and `run_id` as the stable experimental key. Do not use a directory path, DOI fragment, title, or row number as a relational key.

## Sparsity policy

Evaluate fields against the expected several-hundred-source corpus, not only the current sample.

Keep a dedicated field when it is:

- required for identity, joins, status, or interpretation;
- common across the full corpus;
- conditionally common within a major source class such as catalyst papers, reactor papers, scale studies, or patents;
- less frequent but consistently defined and critical for CNT identity, reproducibility, safety, scale, or industrial review.

Use a summary field or long evidence row when the information is heterogeneous, source-specific, or rarely quantified. A table may have conditionally empty fields; avoid families of narrow fields that remain empty for nearly every source.

Examples:

- Retain BET, pore, catalyst lifetime, GHSV, length, residue, purification, and throughput fields because they are expected to recur in substantial source classes and materially affect interpretation.
- Consolidate per-kg CH4, H2, inert gas, electricity, and waste costs into `quantitative_cost_summary` because explicit normalized cost accounting is rare and definitions vary.
- Consolidate conductivity, viscosity, density, and similar application tests into `application_property_summary` until recurrence justifies a stable dedicated field.
- Represent gas roles generically and preserve the complete mixture in `gas_composition_summary`.
- Represent Raman direction with one type/value pair.

Record `not_reported`, `not_applicable`, or a meaningful qualitative state when needed for interpretation. Do not fill reviewer-assessment fields during first-pass extraction.

## `source_master`

Purpose: store source metadata once, independent of run count.

Identity: `source_id`.

```text
source_id
source_type
source_title
publication_year
authors_or_assignee
publication_venue
doi_or_patent_no
source_link
source_database
source_language
local_file_path
pdf_status
screening_class
source_section_scope
extraction_status
review_status
notes
```

Use `source_type` values such as `paper`, `patent`, `review`, or `internal_record`. Use `doi_or_patent_no` as the principal published identifier without creating separate paper-only and patent-only identity columns.

## `source_run`

Purpose: identify and classify a defensible run or patent example without repeating source metadata.

Identity: `run_id`.

Foreign key: `source_id -> source_master.source_id`.

```text
run_id
source_id
run_label
data_type
target_track
relevance_class
extraction_status
extraction_confidence
run_summary
notes
```

Recommended `data_type` values include `experimental_run`, `patent_example`, and `review_context`. Use a route-specific `target_track`, for example `CH4_CCVD_t-MWCNT`.

Do not store catalyst keys, reactor type, CNT type, or a manually maintained `combo_key` here. Generate cross-table feature keys later in `ml_runs_clean.csv`.

## `catalyst_system`

Purpose: store catalyst composition, preparation, structure, and deactivation facts.

Identity: `run_id + catalyst_id`.

Foreign key: `run_id -> source_run.run_id`.

```text
run_id
catalyst_id
catalyst_label
active_metals
support_material
promoter
metal_ratio_original
metal_ratio_standardized
precursor_summary
preparation_method
preparation_modifier
preparation_detail
drying_condition
calcination_condition
reduction_condition
activation_condition
post_preparation_condition
catalyst_particle_size_mean_nm
catalyst_particle_size_range_nm
catalyst_particle_size_qualifier
BET_surface_area_m2_g
pore_diameter_nm
pore_volume_cm3_g
phase_or_state_summary
dispersion_summary
deactivation_summary
notes
```

Use `preparation_modifier` for stable categories such as:

```text
acid_washing
support_acidification
catalyst_acidification
acid_complexing
alkali_assisted
surfactant_assisted
chelating_agent
not_applicable
other
```

Put reagent, concentration, ratio, pH, or one-off preparation detail in `preparation_detail` rather than creating a column for each possible modifier.

For catalyst particles:

- put a reported mean in `catalyst_particle_size_mean_nm`;
- put a reported range in `catalyst_particle_size_range_nm`;
- use `catalyst_particle_size_qualifier` for `reported_numeric`, `non_uniform_not_quantified`, `qualitative_only`, `uncertain`, or `not_reported`.

## `reactor_process_gas`

Purpose: store one row per process stage with reactor, temperature, time, pressure, and gas program.

Identity: `run_id + process_stage_id`.

Foreign key: `run_id -> source_run.run_id`.

```text
run_id
process_stage_id
stage_order
stage_type
reactor_type
scale_level
reactor_material
reactor_size_summary
reactor_setup_summary
catalyst_loading_mass_g
temperature_setpoint_C
temperature_range_reported_C
temperature_program_summary
holding_time_min
heating_rate_C_min
cooling_condition
pressure_original
pressure_kPa
carbon_source
carbon_source_flow_original
carbon_source_flow_sccm
reducing_gas
reducing_gas_flow_original
reducing_gas_flow_sccm
inert_gas
inert_gas_flow_original
inert_gas_flow_sccm
cofeed_or_reactive_gas
cofeed_flow_original
cofeed_flow_sccm
total_flow_original
total_flow_sccm
gas_composition_summary
GHSV_or_residence_time
process_note
```

Use role-based gas fields so the schema works for methane, other hydrocarbons, alcohols, CO, natural gas, and biogas without adding permanent columns for every molecule.

- Carbon source: the principal CNT carbon precursor.
- Reducing gas: H2 or another reducing species used for catalyst state control.
- Inert gas: Ar, N2, He, or another carrier/inert species.
- Cofeed/reactive gas: CO2, O2, steam, NH3, or another non-primary reactive component.

When multiple gases share a role, preserve all components and ratios in `gas_composition_summary`. Keep original and standardized flow values distinguishable and link calculated standardizations to evidence.

## `yield_quality`

Purpose: preserve yield identity, normalized results, CNT/product identity, morphology, quality, purification, and application properties.

Identity: `run_id + product_id`.

Foreign key: `run_id -> source_run.run_id`.

```text
run_id
product_id
primary_yield_metric
yield_original
yield_definition_original
yield_calculation_method
yield_value_standardized
yield_unit_standardized
yield_standardization_note
CNT_yield_per_catalyst_g_gcat
CNT_productivity_g_gcat_h
carbon_source_conversion_percent
carbon_conversion_to_solid_percent
secondary_result_summary
CNT_type_reported
CNT_type_confirmed
product_mixture_summary
CNT_type_evidence
SWCNT_or_few_wall_evidence_summary
RBM_peak_reported
outer_diameter_mean_nm
outer_diameter_range_nm
inner_diameter_mean_nm
wall_number_summary
length_summary
morphology
alignment_or_array
Raman_ratio_type
Raman_ratio_value
Raman_laser_wavelength_nm
TGA_carbon_content_wt_percent
purified_product_purity_wt_percent
purity_basis
residue_summary
amorphous_carbon_level
BET_surface_area_product_m2_g
characterization_methods
post_treatment_or_purification
purification_condition
application_property_summary
notes
```

Keep `primary_yield_metric` explicit. Examples include:

```text
carbon_weight_gain_percent
CNT_yield_per_catalyst
CNT_productivity
carbon_conversion_to_solid
methane_conversion
CNT_array_height
reported_yield_other
```

Do not compare or relabel unlike metrics. Use `secondary_result_summary` when a source reports additional metrics that do not justify another stable column.

Use one reported Raman direction in `Raman_ratio_type` (`ID/IG` or `IG/ID`) and its matching value in `Raman_ratio_value`. Record a calculated reciprocal as calculated evidence, not as a second reported direction.

Use `product_mixture_summary` for amorphous carbon, fibers, graphitic particles, multiple CNT classes, or other material mixtures. A mixed product must not be represented as an unqualified clean CNT success.

Use `purity_basis` to distinguish at least:

```text
as_synthesized_TGA_carbon_content
post_purification_product_purity
ash_or_residue_basis
author_unspecified
not_reported
```

## `cost_scale_review`

Purpose: store reported scale, stability, cost, safety, and emission facts and later human industrial assessments.

Identity: `run_id`.

Foreign key: `run_id -> source_run.run_id`.

```text
run_id
scale_level_demonstrated
scale_level_claimed
scale_evidence_summary
reactor_capacity_or_throughput
continuous_operation_time_h
catalyst_lifetime_or_reuse
catalyst_reuse_cycles
batch_stability
scale_up_issue
quantitative_cost_reported
quantitative_cost_summary
cost_driver_summary
safety_risk
emission_or_waste
industrial_readiness_assessment
reproduction_value
reproduction_priority
industrial_value_score
recommended_next_action
review_note
```

Keep demonstrated scale separate from author wording. A large-diameter tube with 0.1 g catalyst is a laboratory batch unless actual throughput supports a stronger label.

Use `quantitative_cost_summary` for the uncommon cases with actual normalized costs or consumption. Use `cost_driver_summary` for reported or human-reviewed material, energy, purification, and waste drivers without maintaining many mostly empty cost columns.

Leave the assessment fields empty during first pass unless a human explicitly performs the review.

## `evidence_index`

Purpose: centralize traceability and remove location/excerpt repetition from factual tables.

Identity: `evidence_id`.

Foreign keys: `source_id -> source_master.source_id`; optional `run_id -> source_run.run_id`.

```text
evidence_id
source_id
run_id
target_table
target_record_id
target_fields
evidence_type
value_status
source_section
source_locator
source_object_ref
evidence_text
evidence_summary
confidence
linked_issue_id
notes
```

Use `target_table`, `target_record_id`, and `target_fields` to point from evidence to facts. `target_fields` may contain a semicolon-separated set when one excerpt supports a compact group of fields.

Recommended `evidence_type` values:

```text
record_support
direct_quote
table_value
figure_interpretation
patent_example
patent_claim
source_observation
calculation
```

Recommended `value_status` values:

```text
reported
calculated
inferred
review_assessment
```

Use `source_locator` for page or paragraph location, `source_section` for the named section, and `source_object_ref` for table, figure, equation, example, claim, or supplement identifiers.

## `review_issue_log`

Purpose: manage conflicts, ambiguities, critical missing evidence, and human resolution without overwriting source facts.

Identity: `issue_id`.

Foreign keys: `source_id -> source_master.source_id`; optional `run_id -> source_run.run_id`.

```text
issue_id
source_id
run_id
issue_type
target_table
target_record_id
target_field
issue_summary
conflicting_values
evidence_ids
severity
review_status
reviewer
reviewed_at
resolution
notes
```

Create rows only for real issues. Recommended `issue_type` values:

```text
source_conflict
definition_ambiguity
run_split_uncertainty
CNT_type_uncertainty
calculation_check
critical_data_gap
quality_warning
schema_mapping_question
```

Recommended `review_status` values:

```text
open
in_review
resolved
wont_fix
```

Link all supporting `evidence_id` values. Keep conflicting alternatives visible until resolution.

## Derived and optional artifacts

`ml_runs_clean.csv` is a later, automatically generated wide table. It may derive:

- catalyst keys and composition encodings;
- carbon-source/reactor/CNT-type combination keys;
- one-hot CNT labels;
- normalized gas features;
- selected yield/productivity targets;
- review-complete training filters.

Never edit it as a source of truth.

`field_dictionary.csv` documents every formal field, data type, unit, expected population, null policy, and inclusion rationale. It is required for schema governance but is not a business table.

## Field-change protocol

Before adding, deleting, renaming, or splitting a field:

1. Review expected occurrence across papers and patents, not only the current sources.
2. Decide whether the concept is corpus-common, class-conditionally common, rare but critical, or source-specific.
3. Reuse a stable summary or evidence row for source-specific detail.
4. Check migration impact on all eight tables, validators, workbooks, and derived-data builders.
5. Update `config/schema.json`, `config/field_dictionary.csv`, this reference, and validation tests together.
6. Ask the user before changing the formal contract after reviewed data exists.
