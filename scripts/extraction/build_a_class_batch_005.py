#!/usr/bin/env python3
"""Build the fifth evidence-grounded A-class extraction batch."""
from __future__ import annotations

import json
from typing import Any

from scripts.extraction.build_a_class_batch import (
    BATCH_ID,
    ROOT,
    TABLES,
    EvidenceStore,
    catalyst_row,
    cost_row,
    evidence_row,
    issue_row,
    load_metadata,
    master_row,
    process_row,
    run_row,
    yield_row,
)
from scripts.extraction.build_a_class_batch_002 import publish_package


BATCH_NUMBER = 5
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_4C9F9F626FE8A7BC"

# The same CNT31-03-09 sample appears in all three one-factor tables. It is
# represented once here so that one physical sample cannot become three runs.
RUNS = [
    ("CNT28-02-09", 750, 50, 3.3, "temperature"),
    ("CNT05-02-09", 800, 50, 3.3, "temperature"),
    ("CNT25-03-09", 850, 50, 3.3, "temperature"),
    ("CNT18-02-09", 900, 50, 3.3, "temperature"),
    ("CNT23-02-09", 950, 50, 3.3, "temperature"),
    ("CNT23-03-09", 1000, 50, 3.3, "temperature"),
    ("CNT31-03-09", 900, 50, 3.3, "shared_baseline"),
    ("CNT07-04-09", 900, 50, 3.3, "temperature"),
    ("CNT09-05-09", 900, 10, 3.3, "flow"),
    ("CNT12-05-09", 900, 20, 3.3, "flow"),
    ("CNT13-05-09", 900, 30, 3.3, "flow"),
    ("CNT19-05-09", 900, 40, 3.3, "flow"),
    ("CNT21-05-09", 900, 80, 3.3, "flow"),
    ("CNT20-05-09", 900, 100, 3.3, "flow"),
    ("CNT05-05-09", 900, 50, 0.0, "catalyst"),
    ("CNT04-05-09", 900, 50, 1.0, "catalyst"),
    ("CNT01-05-09", 900, 50, 2.0, "catalyst"),
    ("CNT06-05-09", 900, 50, 4.0, "catalyst"),
    ("CNT07-05-09", 900, 50, 5.0, "catalyst"),
]


def add_observation(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    suffix: str,
    span_id: str,
    summary: str,
) -> str:
    evidence_id = f"EVD_{SOURCE_ID}_OBS_{suffix}"
    item = evidence_row(
        store,
        SOURCE_ID,
        evidence_id,
        "not_applicable",
        "source_master",
        SOURCE_ID,
        "source_section_scope",
        span_id,
        summary,
    )
    item["evidence_type"] = "source_observation"
    tables["evidence_index"].append(item)
    return evidence_id


def condition_span(group: str) -> str:
    if group in {"temperature", "shared_baseline"}:
        return "SPAN_1935D9E1AA918D44E224"
    if group == "flow":
        return "SPAN_96E33E26CF5F9D596542"
    return "SPAN_D0BFB93FB4D7F8791172"


def build(
    metadata: dict[str, Any],
    store: EvidenceStore,
) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "Thesis experimental chapters: camphor/ferrocene CVD, temperature, "
                "argon-flow and catalyst-concentration series, TGA, Raman, FTIR and EM."
            ),
        )
    )
    tables["source_master"][0]["local_file_path"] = (
        f"data/interim/parsed_text/{SOURCE_ID}/full_text.txt"
    )
    tables["source_master"][0]["notes"] += " Source document is a university thesis."

    for index, (sample_id, temperature, flow, catalyst_pct, group) in enumerate(
        RUNS, start=1
    ):
        run_id = f"{SOURCE_ID}_R{index:02d}"
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                f"R{index:02d}",
                (
                    f"{sample_id}; {temperature} C; {flow} sccm Ar; "
                    f"{catalyst_pct:g}% ferrocene"
                ),
                (
                    f"Camphor/ferrocene CVD sample {sample_id} on Si and quartz "
                    f"substrates at {temperature} C and {flow} sccm Ar."
                ),
                "high",
            )
        )
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                catalyst_label=(
                    f"{catalyst_pct:g}% ferrocene in camphor source mixture"
                ),
                active_metals="Fe" if catalyst_pct else "not_applicable",
                support_material="not_applicable",
                promoter="not_applicable",
                metal_ratio_original=(
                    f"{catalyst_pct:g}% ferrocene; ferrocene:camphor "
                    f"{catalyst_pct:g}:100"
                ),
                metal_ratio_standardized=(
                    f"{catalyst_pct:g} wt/relative-% ferrocene in source mixture"
                ),
                precursor_summary="ferrocene (C10H10Fe)",
                preparation_method="floating_catalyst_solid_vapour_CVD",
                preparation_modifier="camphor_ferrocene_mixture",
                preparation_detail=(
                    "Camphor/ferrocene source mixture was heated separately; Fe from "
                    "ferrocene decomposition formed catalyst particles in situ."
                ),
                drying_condition="not_applicable",
                calcination_condition="not_applicable",
                reduction_condition="not_applicable",
                activation_condition="in_situ_ferrocene_decomposition",
                post_preparation_condition="floating/in-situ catalyst",
                phase_or_state_summary=(
                    "No Fe catalyst precursor"
                    if catalyst_pct == 0
                    else "in-situ iron nanoparticles/clusters"
                ),
                deactivation_summary="not_reported",
            )
        )
        setup = (
            "115 cm long, 5 cm diameter quartz tube; Si and quartz substrates "
            "on alumina boat at furnace centre; 3-4 g source mixture about 30 cm away."
        )
        tables["reactor_process_gas"].extend(
            [
                process_row(
                    run_id,
                    1,
                    "argon_purge",
                    reactor_type="horizontal quartz-tube CVD furnace",
                    reactor_material="quartz",
                    reactor_size_summary="115 cm length; 5 cm diameter",
                    reactor_setup_summary=setup,
                    catalyst_loading_mass_g="not_reported",
                    holding_time_min="30",
                    pressure_original="not_reported",
                    pressure_kPa="not_reported",
                    inert_gas="Ar",
                    inert_gas_flow_original="500 sccm",
                    inert_gas_flow_sccm="500",
                    gas_composition_summary="Ar purge",
                ),
                process_row(
                    run_id,
                    2,
                    "camphor_ferrocene_CVD_growth",
                    reactor_type="horizontal quartz-tube CVD furnace",
                    reactor_material="quartz",
                    reactor_size_summary="115 cm length; 5 cm diameter",
                    reactor_setup_summary=setup,
                    catalyst_loading_mass_g="not_reported",
                    temperature_setpoint_C=str(temperature),
                    temperature_program_summary=(
                        "Camphor/ferrocene source heated to approximately 200 C "
                        "before vapour transport to the growth zone."
                    ),
                    holding_time_min="5-15",
                    pressure_original="not_reported",
                    pressure_kPa="not_reported",
                    carbon_source="camphor; ferrocene",
                    carbon_source_flow_original=(
                        f"solid source vapour carried by {flow} sccm Ar"
                    ),
                    inert_gas="Ar",
                    inert_gas_flow_original=f"{flow} sccm",
                    inert_gas_flow_sccm=str(flow),
                    cofeed_or_reactive_gas="not_applicable",
                    total_flow_original=f"{flow} sccm Ar",
                    total_flow_sccm=str(flow),
                    gas_composition_summary=(
                        f"Ar carrier; {catalyst_pct:g}% ferrocene in camphor source"
                    ),
                ),
                process_row(
                    run_id,
                    3,
                    "argon_cooling",
                    reactor_type="horizontal quartz-tube CVD furnace",
                    reactor_material="quartz",
                    pressure_original="not_reported",
                    pressure_kPa="not_reported",
                    cooling_condition="furnace cooled to room temperature under Ar",
                    inert_gas="Ar",
                    inert_gas_flow_original="not_reported",
                    gas_composition_summary="Ar cooling atmosphere",
                ),
            ]
        )
        zero_catalyst = catalyst_pct == 0
        best = (
            temperature == 800
            or flow == 80
            or catalyst_pct in {1, 4}
        )
        product = (
            "Predominantly graphitic/black carbon; broad D and high G Raman peaks."
            if zero_catalyst
            else (
                "CNTs observed; this condition was among the one-factor quality optima."
                if best
                else "CNTs observed, with condition-dependent quality, quantity and deposition position."
            )
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="qualitative_CNT_presence_and_quality",
                yield_original="qualitative only; no run-specific mass yield reported",
                yield_definition_original=(
                    "CNT presence/relative quality from TGA, Raman and microscopy; "
                    "the thesis does not provide a run-specific mass yield table."
                ),
                yield_calculation_method="qualitative cross-characterization",
                yield_value_standardized="not_reported",
                yield_unit_standardized="not_applicable",
                secondary_result_summary=product,
                CNT_type_reported="CNTs and CNFs",
                CNT_type_confirmed=(
                    "uncertain_graphitic_carbon"
                    if zero_catalyst
                    else "CNT_or_CNF_present"
                ),
                product_mixture_summary=product,
                CNT_type_evidence="TEM/SEM, Raman and TGA",
                wall_number_summary="not_reported",
                length_summary="not_reported",
                morphology=(
                    "thin hair-like structures; bridges; thick CNT mats; other carbon products"
                ),
                Raman_ratio_type="ID/IG",
                Raman_ratio_value="not_reported",
                Raman_laser_wavelength_nm="633",
                TGA_carbon_content_wt_percent="not_reported",
                purity_basis="as-collected powder scratched from quartz tube",
                residue_summary=(
                    "Iron-oxide residual mass varied with growth condition."
                    if not zero_catalyst
                    else "0% catalyst sample showed graphitic/black-carbon behavior."
                ),
                amorphous_carbon_level=(
                    "high"
                    if zero_catalyst or flow <= 20
                    else "condition_dependent"
                ),
                characterization_methods="TGA; Raman; FTIR; TEM; SEM",
                post_treatment_or_purification="none reported",
                purification_condition="not_applicable",
            )
        )
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                reactor_capacity_or_throughput="3-4 g solid source mixture; 5-15 min laboratory growth",
                continuous_operation_time_h="not_applicable",
                catalyst_lifetime_or_reuse="not_reported",
                batch_stability="single laboratory deposition",
                scale_up_issue=(
                    "Camphor and ferrocene evaporated unevenly; source heating and positioning limited repeatability."
                ),
                cost_driver_summary="Simple camphor/ferrocene CVD setup; no quantitative cost reported.",
                safety_risk="not_reported",
                emission_or_waste="Undeposited or unpyrolyzed material collected through an oil bubbler.",
            )
        )

        cond_span = condition_span(group)
        evidence_specs = [
            (
                "CAT",
                "catalyst_system",
                f"{run_id}_CAT",
                "catalyst_label;active_metals;metal_ratio_original;metal_ratio_standardized;precursor_summary;preparation_method;preparation_detail;activation_condition;phase_or_state_summary",
                "SPAN_8840215AC2B6E4090337",
                "Camphor/ferrocene source, mass and in-situ iron catalyst.",
            ),
            (
                "CAT_CONDITION",
                "catalyst_system",
                f"{run_id}_CAT",
                "catalyst_label;active_metals;metal_ratio_original;metal_ratio_standardized",
                cond_span,
                "Sample-specific ferrocene concentration.",
            ),
            (
                "PURGE",
                "reactor_process_gas",
                f"{run_id}_S01",
                "reactor_type;reactor_material;reactor_size_summary;reactor_setup_summary;holding_time_min;inert_gas;inert_gas_flow_original;gas_composition_summary",
                "SPAN_7E0020F6862458A65132",
                "CVD setup and 500 sccm, 30-minute argon purge.",
            ),
            (
                "GROWTH_COMMON",
                "reactor_process_gas",
                f"{run_id}_S02",
                "reactor_type;reactor_material;reactor_size_summary;reactor_setup_summary;temperature_program_summary;holding_time_min;carbon_source",
                "SPAN_7E0020F6862458A65132",
                "Common source heating, vapour transport and 5-15 minute growth procedure.",
            ),
            (
                "GROWTH_CONDITION",
                "reactor_process_gas",
                f"{run_id}_S02",
                "temperature_setpoint_C;carbon_source_flow_original;inert_gas;inert_gas_flow_original;total_flow_original;gas_composition_summary",
                cond_span,
                "Sample-specific temperature, argon flow and ferrocene concentration.",
            ),
            (
                "COOLING",
                "reactor_process_gas",
                f"{run_id}_S03",
                "cooling_condition;inert_gas;gas_composition_summary",
                "SPAN_863351E2A804E2F004C3",
                "Furnace cooling to room temperature under argon.",
            ),
            (
                "PRODUCT",
                "yield_quality",
                f"{run_id}_PROD",
                "primary_yield_metric;yield_original;yield_definition_original;secondary_result_summary;CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;morphology;amorphous_carbon_level;purity_basis;residue_summary",
                (
                    "SPAN_E2D61EEFB86C41500C3F"
                    if zero_catalyst
                    else "SPAN_DB85E491B537024015E6"
                ),
                "Condition-series CNT/carbon identity and qualitative quality evidence.",
            ),
            (
                "RAMAN_METHOD",
                "yield_quality",
                f"{run_id}_PROD",
                "Raman_ratio_type;Raman_laser_wavelength_nm;characterization_methods",
                "SPAN_A184DD9289CEE038E63B",
                "Raman wavelength and characterization methods.",
            ),
            (
                "SCALE",
                "cost_scale_review",
                run_id,
                "scale_level_demonstrated;reactor_capacity_or_throughput;batch_stability;scale_up_issue;cost_driver_summary;emission_or_waste",
                "SPAN_8840215AC2B6E4090337",
                "Laboratory source mass and setup limitations.",
            ),
        ]
        for suffix, table, record_id, fields, span_id, summary in evidence_specs:
            tables["evidence_index"].append(
                evidence_row(
                    store,
                    SOURCE_ID,
                    f"EVD_{run_id}_{suffix}",
                    run_id,
                    table,
                    record_id,
                    fields,
                    span_id,
                    summary,
                )
            )

    observations = {
        "OPTIMA": add_observation(
            tables,
            store,
            "OPTIMA",
            "SPAN_155714349100C14C037A",
            (
                "One-factor optima were 800 C growth temperature, 80 sccm Ar "
                "and 4% catalyst concentration; these were not one combined run."
            ),
        ),
        "FLOW": add_observation(
            tables,
            store,
            "FLOW",
            "SPAN_4E2349E9EFDE67E65DB1",
            (
                "Higher argon flow reduced amorphous-carbon accumulation but "
                "decreased product yield; Raman quality generally improved with flow."
            ),
        ),
        "CATALYST": add_observation(
            tables,
            store,
            "CATALYST",
            "SPAN_E2D61EEFB86C41500C3F",
            (
                "The 0% ferrocene sample behaved as graphitic/black carbon, while "
                "1% and 4% gave minimum ID/IG and favorable TGA indicators."
            ),
        ),
    }
    first_run = f"{SOURCE_ID}_R01"
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_DUPLICATE_SAMPLE_001",
                SOURCE_ID,
                f"{SOURCE_ID}_R07",
                "run_split_uncertainty",
                "source_run",
                f"{SOURCE_ID}_R07",
                "run_summary",
                (
                    "CNT31-03-09 appears in the temperature, flow and catalyst tables. "
                    "It is represented once as a shared baseline, reducing 21 table rows "
                    "to 19 unique physical samples."
                ),
                f"EVD_{SOURCE_ID}_R07_GROWTH_CONDITION",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_001",
                SOURCE_ID,
                first_run,
                "critical_data_gap",
                "yield_quality",
                f"{first_run}_PROD",
                "yield_original",
                (
                    "The source discusses relative yield trends but does not provide "
                    "run-specific recovered CNT mass or a yield definition table."
                ),
                f"EVD_{first_run}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_OPTIMUM_001",
                SOURCE_ID,
                f"{SOURCE_ID}_R02",
                "definition_ambiguity",
                "source_run",
                f"{SOURCE_ID}_R02",
                "run_summary",
                (
                    "The abstract lists 800 C, 80 sccm and 4% as separate one-factor "
                    "optima. No experiment combining all three conditions is reported."
                ),
                observations["OPTIMA"],
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_ZERO_CATALYST_001",
                SOURCE_ID,
                f"{SOURCE_ID}_R15",
                "source_conflict",
                "yield_quality",
                f"{SOURCE_ID}_R15_PROD",
                "CNT_type_confirmed",
                (
                    "The general results say CNTs were seen under all growth conditions, "
                    "but the 0% catalyst discussion identifies graphitic/black carbon. "
                    "The zero-catalyst product requires image-level verification."
                ),
                observations["CATALYST"],
                "high",
            ),
        ]
    )
    return tables


def main() -> None:
    metadata = load_metadata()
    store = EvidenceStore()
    try:
        metric = publish_package(SOURCE_ID, build(metadata[SOURCE_ID], store))
    finally:
        store.close()
    result = {
        "batch_id": BATCH_NAME,
        "sources": [metric],
        "total_runs": metric["row_counts"]["source_run"],
        "status": "completed_needs_review",
    }
    output = BATCH_ROOT / f"batch_{BATCH_NUMBER:03d}_metrics.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
