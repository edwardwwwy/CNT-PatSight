# Recommended five-table schema

Use these fields as a starting vocabulary. They are neither mandatory for every record nor exhaustive. Add a clearly named field, summary, note, or evidence object when a valuable source does not fit cleanly.

## Contents

- [`source_run`](#source_run)
- [`catalyst_system`](#catalyst_system)
- [`reactor_process_gas`](#reactor_process_gas)
- [`yield_quality`](#yield_quality)
- [`cost_scale_review`](#cost_scale_review)
- [Flexible field priority](#flexible-field-priority)
- [Field extension protocol](#field-extension-protocol)

## `source_run`

Purpose: identify the source and run, classify the route, and support aggregation.

```text
source_id
run_id
source_type
source_title
year
authors_or_assignee
doi_or_patent_no
source_link
source_database
source_section
data_type
run_label
target_track
catalyst_key
combo_key
relevance_class
relevance_score
extraction_status
extraction_confidence
run_summary
notes
```

Suggested derived key:

```text
combo_key = catalyst_key + carbon_source + reactor_type + CNT_type
```

Store each component independently. Record how the key was generated and update it when a component is corrected.

## `catalyst_system`

Purpose: describe catalyst composition, preparation, acidification/complexation/activation, structure, and stability.

```text
run_id
catalyst_id
catalyst_label
catalyst_key
active_metals
support_material
promoter
metal_ratio_original
metal_ratio_standardized
precursor_summary
preparation_method
acid_or_complexing_summary
acid_treatment_flag
acid_treatment_type
acid_treatment_purpose
complexing_agent
complexing_ratio_original
solution_pH
washing_condition
drying_condition
calcination_condition
reduction_condition
activation_summary
crushing_or_sieving_condition
catalyst_particle_size_nm
BET_surface_area_m2_g
pore_diameter_nm
pore_volume_cm3_g
phase_or_state_summary
dispersion_summary
expected_CNT_type_bias
catalyst_lifetime_or_reuse
deactivation_reason
catalyst_assessment
evidence_text
evidence_location
confidence
notes
```

Useful acid-treatment categories include:

```text
support_acidification
catalyst_acidification
acid_complexing
other_acid_assisted_preparation
```

Do not force detailed acid fields when only a short statement is available; retain the original statement in `acid_or_complexing_summary`.

## `reactor_process_gas`

Purpose: describe each process stage and support process-window and temperature-effect analysis.

```text
run_id
process_stage_id
stage_order
stage_type
reactor_type
scale_level
reactor_material
reactor_size_summary
catalyst_loading_mass
catalyst_bed_position
temperature_sensor_position
start_temperature_C
temperature_setpoint_C
temperature_actual_C
temperature_range_reported_C
reported_suitable_temperature
reported_optimal_temperature
reported_failed_temperature
temperature_effect_summary
holding_time_min
heating_rate_C_min
cooling_condition
pressure_original
pressure_kPa
carbon_source
CH4_flow_original
CH4_flow_sccm
natural_gas_flow_original
natural_gas_flow_sccm
natural_gas_composition
H2_flow_original
H2_flow_sccm
N2_flow_original
N2_flow_sccm
Ar_flow_original
Ar_flow_sccm
other_gas_flow_original
other_gas_flow_sccm
total_flow_original
total_flow_sccm
gas_ratio_summary
CH4_volume_fraction_percent
GHSV_or_residence_time
process_note
evidence_text
evidence_location
confidence
```

Keep these concepts separate:

- `temperature_setpoint_C`: the temperature used in this run;
- `temperature_range_reported_C`: a source-reported range, with evidence type such as example, claim, or review;
- `reported_optimal_temperature`: the authors' stated or experimentally supported optimum;
- `temperature_effect_summary`: the observed influence on yield, purity, morphology, CNT type, sintering, or unwanted carbon.

## `yield_quality`

Purpose: preserve yield definitions, product identity, CNT-type evidence, quality, and post-treatment.

```text
run_id
product_id
catalyst_mass_before_g
product_mass_raw_g
product_mass_after_purification_g
yield_original
yield_definition_original
yield_calculation_method
yield_value_standardized
yield_unit_standardized
yield_standardization_note
CNT_yield_per_catalyst_g_gcat
CNT_productivity_g_gcat_h
space_time_yield_kg_m3_h
methane_conversion_percent
carbon_efficiency_percent
carbon_conversion_to_solid_percent
CNT_selectivity_in_solid_carbon_percent
CNT_type_reported
CNT_type_confirmed
is_SWCNT
is_DWCNT
is_t_MWCNT
is_MWCNT
CNT_type_evidence
SWCNT_evidence_summary
RBM_peak_reported
outer_diameter_mean_nm
outer_diameter_range_nm
inner_diameter_mean_nm
inner_diameter_or_wall_number
wall_number_mean
length_summary
length_mean_um
aspect_ratio
morphology
alignment_or_array
Raman_ID_IG
Raman_IG_ID
Raman_laser_wavelength_nm
purity_wt_percent
ash_content_wt_percent
metal_residue_wt_percent
amorphous_carbon_level
BET_surface_area_product_m2_g
tap_density_g_cm3
bulk_density_g_cm3
conductivity
slurry_viscosity
characterization_methods
post_treatment_or_purification
purification_condition
application_related_properties
image_or_figure_ref
evidence_text
evidence_location
confidence
notes
```

For SWCNT assessment, distinguish an author claim from evidence such as TEM/HRTEM, Raman RBM, diameter distribution, and wall count. Use an uncertain or unknown status when the evidence is insufficient.

## `cost_scale_review`

Purpose: combine reported industrial facts with transparent review judgments and next actions.

```text
run_id
quantitative_cost_reported
methane_consumption_per_kg_CNT
natural_gas_consumption_per_kg_CNT
H2_consumption_per_kg_CNT
N2_or_Ar_consumption_per_kg_CNT
electricity_consumption_per_kg_CNT
catalyst_cost_signal
purification_cost_signal
waste_treatment_signal
total_variable_cost_per_kg_CNT
continuous_operation_time_h
catalyst_reuse_cycles
batch_success_rate_percent
batch_stability
scale_signal_reported
scale_level_claimed
scale_up_issue
safety_risk
emission_or_waste
contains_expensive_metal
needs_H2
needs_acid_washing
major_cost_driver
reported_best_condition_summary
reviewed_suitable_condition
reproduction_value
reproduction_priority
industrial_value_score
recommended_next_action
missing_critical_fields
review_note
evidence_text
evidence_location
confidence
```

Treat reported best conditions, reviewer-selected suitable conditions, reproduction recommendations, and industrial judgments as different concepts. Explain the basis and missing evidence for every nontrivial assessment.

## Flexible field priority

Use priority as an extraction aid, not an exclusion rule:

- Core: fields needed to identify and interpret a run when available.
- Enrichment: fields that improve mechanism, comparison, or industrial analysis.
- Opportunistic: rare but valuable fields captured only when explicitly reported.

A missing core field can reduce confidence without automatically invalidating a valuable record. A rare field can still deserve preservation when it changes the R&D interpretation.

## Field extension protocol

Add fields when they make useful information easier to retain or compare. Reuse an existing field when the meaning is close, use `summary` or `notes` for one-off details, and keep unresolved information in `valuable_unmapped_information` when useful.

For a field likely to be reused, briefly note its meaning, destination table, and unit or value style. This is guidance rather than an approval process. Keep materially conflicting values visible when they affect interpretation.
