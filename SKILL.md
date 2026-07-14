---
name: cnt-patsight
summary: Collect, screen, extract, validate, and analyze CVD/CCVD CNT literature and patent data for methane/natural-gas MWCNT industrial optimization.
---

# CNT-PatSight Skill

Use this skill when working on CNT-PatSight tasks involving CVD/CCVD carbon nanotube papers, patents, metadata, PDF text, structured extraction, database validation, or industrial R&D recommendations.

## 1. Mission

Act as an industrial CNT R&D data engineer.

The goal is not to summarize papers casually. The goal is to convert public papers, patents, and later internal experiments into structured, evidence-backed data that can help a CNT R&D team reproduce, compare, and prioritize methane/natural-gas CVD routes for MWCNT production.

The core output is a five-table database:

```text
source_run
catalyst_system
reactor_process_gas
yield_quality
cost_scale_review
```

## 2. Scope filter

Prioritize:

```text
CVD / CCVD / catalytic decomposition / catalytic pyrolysis
+ CNT, especially MWCNT
+ CH4 / methane / natural gas
+ catalyst formulation, support, promoter
+ CVD conditions
+ yield / quality / cost / scale-up
```

Deprioritize or reject:

```text
application-only CNT papers with no synthesis conditions
SWCNT-only mechanism work unless useful as comparison
arc discharge / laser ablation / CO2 electrolysis routes
graphene / carbon black / carbon fiber unless clearly connected to CNT-CVD
broad patent claims without concrete examples
```

## 3. Standard workflow

### Step A — Metadata candidate pool

Collect metadata first. Do not start with full PDF extraction.

Candidate metadata should include:

```text
doc_id
source_db
source_type
title
year
authors_or_assignee
journal_or_patent_office
doi
patent_number
link
abstract_or_claim
keywords
is_open_access
oa_url
cited_by_count
query_hit
relevance_score
status
```

Common data sources:

```text
OpenAlex
Crossref
Semantic Scholar
CORE
Web of Science export
Scopus export
CNKI / Wanfang / VIP export
Google Patents / Lens / EPO OPS / CNIPA
```

### Step B — Seven-question screening

Classify each document before full extraction:

```text
1. CNT related?
2. CVD / CCVD / catalytic decomposition / catalytic pyrolysis?
3. CH4 / methane / natural gas involved?
4. MWCNT or likely MWCNT?
5. Catalyst information present?
6. Process conditions present?
7. At least one result metric present?
```

Classification:

```text
A_formal_extract = extract to five-table database
B_candidate = keep but do not fully extract yet
C_reject = exclude from v1
```

Formal extraction minimum:

```text
CVD/CCVD/catalytic-decomposition CNT
+ catalyst information
+ process condition
+ at least one result metric
+ can form a run_id
```

For v1, prefer high-quality records over quantity.

### Step C — Run-level extraction

Never assume one paper equals one record.

A `run_id` is:

```text
one explicit catalyst system
+ one explicit reactor/process/gas condition
+ one corresponding yield/product-quality result
= one experimental record
```

Split into multiple `run_id` values if catalyst, support, promoter, temperature, gas flow, pressure, reaction time, reactor, purification, or result changes.

Examples:

```text
Fe/MgO      -> run 1
Fe-Mo/MgO   -> run 2
Co/MgO      -> run 3
Co-Mo/MgO   -> run 4
Ni/MgO      -> run 5
```

Temperature series also splits:

```text
Fe-Mo/MgO at 750 C -> run 1
Fe-Mo/MgO at 800 C -> run 2
Fe-Mo/MgO at 850 C -> run 3
```

### Step D — Evidence-backed field extraction

For every critical field, preserve:

```text
field_name
value
unit
source_text
evidence_location
source_section
extraction_method: explicit / inferred / calculated
confidence: high / medium / low
```

Critical fields include:

```text
carbon_source
CNT_type
catalyst active metal
support
promoter
precursor
preparation method
calcination condition
reduction condition
reactor type
temperature
reaction time
CH4/H2/N2 flow
pressure
yield
CH4 conversion
CNT diameter
CNT length
Raman ID/IG
purity
ash content
metal residue
purification method
continuous operation time
cost fields
```

Do not fill missing fields by guesswork.

Allowed values for missing/uncertain data:

```text
unknown
not_reported
not_applicable
inferred_low_confidence
calculated_from_reported_values
```

### Step E — Standardization and validation

Normalize only when safe.

Use normalized units:

```text
temperature -> C
time -> min
flow -> sccm, with original preserved
pressure -> kPa, with original preserved
diameter -> nm
length -> um
yield -> preserve original; standardize only when definition is clear
Raman -> ID/IG
purity/ash/residue -> wt% or ppm as reported
```

Yield rule:

Always keep original yield fields:

```text
yield_original
yield_original_unit
yield_calculation_method
```

Only fill standardized yield if the basis is clear:

```text
yield_value_standardized
yield_unit_standardized
yield_standardization_note
```

Do not compare incompatible yield definitions directly.

## 4. Table schemas

### 4.1 `source_run`

```text
run_id
source_id
source_type
source_title
year
authors_or_assignee
doi_or_patent_no
source_link
source_database
run_label
data_type
target_product
carbon_source_main
relevance_class
relevance_score
extraction_confidence
status
run_summary
notes
```

### 4.2 `catalyst_system`

```text
run_id
catalyst_id
active_metal
metal_ratio_original
Fe_wt_percent
Ni_wt_percent
Co_wt_percent
Mo_wt_percent
support_material
promoter
precursor
preparation_method
precipitant
complexing_agent
drying_condition
calcination_condition
reduction_condition
crushing_or_sieving
catalyst_particle_size_nm
BET_surface_area_m2_g
catalyst_lifetime_h
deactivation_reason
```

### 4.3 `reactor_process_gas`

Use one row per stage if possible.

```text
run_id
program_stage_id
stage_order
stage_type
reactor_type
scale_level
reactor_material
reactor_inner_diameter
heating_zone_length
catalyst_loading_mass_g
catalyst_bed_position
temperature_sensor_position
start_temperature_C
target_temperature_C
actual_temperature_C
heating_rate_C_min
holding_time_min
cooling_rate_C_min
pressure_original
pressure_kPa
CH4_flow_original
CH4_flow_sccm
natural_gas_flow_original
H2_flow_original
H2_flow_sccm
N2_flow_original
N2_flow_sccm
Ar_flow_original
Ar_flow_sccm
total_flow_original
total_flow_sccm
CH4_volume_fraction_percent
CH4_H2_ratio
CH4_N2_ratio
natural_gas_composition
GHSV_h_1
residence_time_s
process_note
```

### 4.4 `yield_quality`

```text
run_id
product_id
catalyst_mass_before_g
product_mass_raw_g
product_mass_after_purification_g
yield_original
yield_value_standardized
yield_unit_standardized
CNT_yield_per_catalyst_g_gcat
CNT_productivity_g_gcat_h
space_time_yield_kg_m3_h
CH4_conversion_percent
carbon_conversion_to_solid_percent
CNT_selectivity_in_solid_carbon_percent
amorphous_carbon_fraction_wt_percent
catalyst_residue_fraction_wt_percent
CNT_type_confirmed
purity_wt_percent
outer_diameter_mean_nm
outer_diameter_range_nm
inner_diameter_mean_nm
wall_number_mean
length_mean_um
aspect_ratio
morphology
Raman_ID_IG
Raman_laser_wavelength_nm
ash_content_wt_percent
Fe_residue
Ni_residue
Co_residue
BET_surface_area_product_m2_g
tap_density_g_cm3
bulk_density_g_cm3
conductivity
slurry_viscosity
battery_or_slurry_relevance
characterization_methods
purification_method
purification_condition
mass_loss_after_purification_percent
image_or_figure_ref
```

### 4.5 `cost_scale_review`

```text
run_id
continuous_operation_time_h
batch_success_rate_percent
catalyst_reuse_cycles
methane_consumption_per_kg_CNT
natural_gas_consumption_per_kg_CNT
H2_consumption_per_kg_CNT
N2_consumption_per_kg_CNT
electricity_consumption_per_kg_CNT
catalyst_cost_per_kg_CNT
purification_cost_per_kg_CNT
waste_treatment_cost_per_kg_CNT
total_variable_cost_per_kg_CNT
contains_expensive_metal
needs_H2
needs_acid_washing
process_complexity_score
scale_up_potential_score
battery_slurry_relevance_score
industrial_value_score
ML_value_score
patent_risk
safety_risk
emission_or_waste
scale_up_issue
missing_critical_fields
internal_trial_status
recommended_next_action
review_note
```

## 5. Patent extraction rules

Handle patent sections differently:

```text
examples / embodiments -> can become run_id if concrete
claims -> protection scope only
background -> context only
description ranges -> candidate info, not real experiment
```

Do not convert a claim such as:

```text
Fe, Co, Ni or Mo catalyst; 500-1100 C; hydrocarbon gas
```

into an experimental record. Only concrete embodiments/examples with specific catalyst, process, and result can become formal `run_id` rows.

## 6. Extraction output template

When extracting from a paper or patent, return a structured object like:

```json
{
  "document_decision": {
    "source_id": "Paper_001",
    "relevance_class": "A_formal_extract",
    "reason": "CH4-CVD CNT paper with catalyst, process and yield data",
    "warnings": []
  },
  "runs": [
    {
      "run_id": "Paper_001_run_001",
      "source_run": {},
      "catalyst_system": {},
      "reactor_process_gas": [],
      "yield_quality": {},
      "cost_scale_review": {},
      "evidence": [
        {
          "field_name": "target_temperature_C",
          "value": 850,
          "unit": "C",
          "source_text": "The reaction was conducted at 850 C.",
          "evidence_location": "page 4, experimental section",
          "extraction_method": "explicit",
          "confidence": "high"
        }
      ]
    }
  ]
}
```

## 7. Quality checklist

Before saving or reporting data, check:

```text
[ ] Is the record within CNT-PatSight v1 scope?
[ ] Can it form one or more clear run_id values?
[ ] Are source, catalyst, process, and result linked by the same run_id?
[ ] Are critical values backed by evidence?
[ ] Are patent claims separated from examples?
[ ] Are original units preserved?
[ ] Are normalized units safe and documented?
[ ] Is yield definition preserved?
[ ] Are inferred/calculated values marked as such?
[ ] Is the record useful for reproducing or industrially evaluating a CNT synthesis route?
```

## 8. Recommended first milestone

For v0.1, do not chase volume.

Target:

```text
10 high-relevance papers/patents
20-40 run_id records
5-table Excel/CSV database
field_definitions.md
extraction_rules.md
2-3 basic charts
3-page preliminary report
```

Only after the v0.1 loop is validated, expand metadata collection and extraction.

## 9. Common mistakes to avoid

```text
- Treating one paper as one record.
- Extracting only the best result and ignoring controls or failed/low-yield runs.
- Treating patent claims as experiments.
- Filling missing fields without evidence.
- Mixing original yield and standardized yield.
- Comparing yields with incompatible definitions.
- Prioritizing dashboards before data quality.
- Sending confidential internal data to external APIs without approval.
```

## 10. Response style for this skill

When producing guidance or extraction results:

- Prefer concise, structured tables.
- Use Chinese explanations when working with the user.
- Use English snake_case for database columns.
- Always distinguish `reported`, `inferred`, and `calculated` values.
- Emphasize reproducibility and industrial usefulness over academic completeness.
