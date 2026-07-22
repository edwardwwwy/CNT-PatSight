#!/usr/bin/env python3
"""Build the twelfth evidence-grounded A-class extraction batch."""

from __future__ import annotations

import json
from typing import Any

from scripts.extraction.batch_common import (
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


BATCH_NUMBER = 12
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ID = "LIT_71A4E4C2BB4AEDD8"


def append_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    suffix: str,
    table: str,
    record_id: str,
    fields: str,
    span_id: str,
    summary: str,
    value_status: str = "reported",
) -> None:
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
            value_status=value_status,
        )
    )


def build(
    metadata: dict[str, Any],
    store: EvidenceStore,
) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "Fe-Ni/activated-carbon catalyst preparation; acetylene CVD "
                "production of MWCNTs; acid/alkali surface modification and "
                "adsorbent morphology/BET/application characterization."
            ),
        )
    )
    tables["source_master"][0]["local_file_path"] = (
        f"data/interim/parsed_text/by_source/{SOURCE_ID}.parsed.json"
    )

    run_id = f"{SOURCE_ID}_R01"
    tables["source_run"].append(
        run_row(
            SOURCE_ID,
            "R01",
            ("Fe-Ni/activated-carbon catalyst; acetylene CVD at 973 K for 30 min"),
            (
                "Five grams of Fe-Ni/AC catalyst in a 90 mm quartz-tube "
                "horizontal furnace; 100 mL/min acetylene and 250 mL/min "
                "argon produced compact upright-forest MWCNTs."
            ),
            "medium",
        )
    )
    tables["source_run"][0]["notes"] = (
        "The paper says the MWCNT methodology follows previous study 45; "
        "primary attribution and reuse of characterization figures require review."
    )

    tables["catalyst_system"].append(
        catalyst_row(
            run_id,
            catalyst_label="Fe-Ni on Jacobi activated carbon",
            active_metals="Fe; Ni",
            support_material="Jacobi activated carbon",
            promoter="not_applicable",
            metal_ratio_original=(
                "Fe(NO3)3·9H2O and Ni(NO3)2·6H2O each supplied as 0.25 M; "
                "solution volumes not reported"
            ),
            metal_ratio_standardized="not_reported",
            precursor_summary=(
                "5 g activated carbon in 50 mL distilled water with "
                "0.25 M Fe and Ni nitrate solutions"
            ),
            preparation_method="aqueous_impregnation_dry_heat_treatment",
            preparation_modifier="crushed and sieved through 200 micrometer sieve",
            preparation_detail=(
                "Stir slurry 20 min; dry at 373 K for 12 h; cool, crush "
                "and sieve; heat at 673 K for 6 h to remove nitrates/moisture."
            ),
            drying_condition="373 K for 12 h",
            calcination_condition="673 K for 6 h; atmosphere not reported",
            reduction_condition="acetylene exposure at 973 K during CVD",
            activation_condition=(
                "The paper describes acetylene as promoting surface cleaning, "
                "carburization, reduction and active-site formation."
            ),
            post_preparation_condition="Fe-Ni/AC powder",
            catalyst_particle_size_mean_nm="not_reported",
            catalyst_particle_size_range_nm="not_reported",
            catalyst_particle_size_qualifier="not_reported",
            phase_or_state_summary="not_reported",
            dispersion_summary="impregnated Fe/Ni salts on activated carbon",
            deactivation_summary="not_reported",
        )
    )

    setup = (
        "Horizontal CVD tube furnace; 5 g catalyst in a ceramic boat inside "
        "a 90 mm diameter quartz tube."
    )
    tables["reactor_process_gas"].extend(
        [
            process_row(
                run_id,
                1,
                "argon_purge_and_heat",
                reactor_type="horizontal tube CVD furnace",
                reactor_material="quartz tube; ceramic boat",
                reactor_size_summary="90 mm tube diameter",
                reactor_setup_summary=setup,
                catalyst_loading_mass_g="5",
                temperature_setpoint_C="not_reported",
                temperature_program_summary=(
                    "Heat at 10 C/min under 30 mL/min Ar until the "
                    "reported CVD temperature of 973 K."
                ),
                holding_time_min="not_reported",
                heating_rate_C_min="10",
                pressure_original="not_reported",
                pressure_kPa="",
                carbon_source="not_applicable",
                reducing_gas="not_applicable",
                inert_gas="Ar",
                inert_gas_flow_original="30 mL/min",
                total_flow_original="30 mL/min",
                gas_composition_summary="Ar purge/heating atmosphere",
            ),
            process_row(
                run_id,
                2,
                "acetylene_CVD_MWCNT_growth",
                reactor_type="horizontal tube CVD furnace",
                reactor_material="quartz tube; ceramic boat",
                reactor_size_summary="90 mm tube diameter",
                reactor_setup_summary=setup,
                catalyst_loading_mass_g="5",
                temperature_setpoint_C="not_reported",
                temperature_program_summary=(
                    "Isothermal reaction at 973 K; Celsius conversion not "
                    "entered because the source reports Kelvin."
                ),
                holding_time_min="30",
                pressure_original="not_reported",
                pressure_kPa="",
                carbon_source="C2H2",
                carbon_source_flow_original="100 mL/min",
                reducing_gas="not_applicable",
                inert_gas="Ar",
                inert_gas_flow_original="250 mL/min",
                total_flow_original=(
                    "not_reported; component flows retained separately"
                ),
                gas_composition_summary=("C2H2 100 mL/min with Ar 250 mL/min at 973 K"),
                process_note=(
                    "The methods section describes this exposure partly as "
                    "catalyst activation; the conclusion identifies the process "
                    "as CVD synthesis of MWCNTs."
                ),
            ),
            process_row(
                run_id,
                3,
                "cooling_and_argon_purge",
                reactor_type="horizontal tube CVD furnace",
                reactor_material="quartz tube; ceramic boat",
                reactor_size_summary="90 mm tube diameter",
                reactor_setup_summary=setup,
                temperature_setpoint_C="not_reported",
                temperature_program_summary="cool furnace to room temperature",
                holding_time_min="not_reported",
                cooling_condition=(
                    "Acetylene stopped; reactor purged with 20 mL/min Ar"
                ),
                pressure_original="not_reported",
                pressure_kPa="",
                carbon_source="not_applicable",
                reducing_gas="not_applicable",
                inert_gas="Ar",
                inert_gas_flow_original="20 mL/min",
                total_flow_original="20 mL/min",
                gas_composition_summary="Ar post-reaction purge",
            ),
        ]
    )

    tables["yield_quality"].append(
        yield_row(
            run_id,
            primary_yield_metric="qualitative_MWCNT_production",
            yield_original=("MWCNTs produced by CVD; product mass yield not reported"),
            yield_definition_original=(
                "CNT identity and morphology by FESEM; BET/FTIR/EDS used "
                "for pristine and modified adsorbent characterization."
            ),
            yield_calculation_method="qualitative characterization",
            yield_value_standardized="",
            yield_unit_standardized="not_applicable",
            secondary_result_summary=(
                "Pristine MWCNT BET surface area 240 m2/g; modified material "
                "11 m2/g. FESEM showed highly compact upright-forest structures."
            ),
            CNT_type_reported="multi-walled carbon nanotubes",
            CNT_type_confirmed="not_applicable",
            product_mixture_summary="not reported beyond MWCNT identity",
            CNT_type_evidence=(
                "Author-reported MWCNT identity and upright-forest FESEM "
                "morphology; wall count/diameter not quantified."
            ),
            wall_number_summary="multi-walled; exact wall count not reported",
            length_summary=("acid-treated MWCNTs appeared shorter; no absolute length"),
            morphology="highly compact upright forests perpendicular to substrate",
            alignment_or_array="upright forest-like structures",
            Raman_ratio_type="not_reported",
            Raman_ratio_value="not_reported",
            purity_basis="not_reported",
            residue_summary="not_reported",
            amorphous_carbon_level="not_reported",
            BET_surface_area_product_m2_g="240",
            characterization_methods="FESEM; BET N2 sorption; FTIR; EDS",
            post_treatment_or_purification=(
                "Disperse 0.5 g MWCNT in 100 mL dichloromethane; sonicate "
                "0.5 h at 328 K; stir 5 min; add 30 mL HCl and 30 mL HNO3; "
                "stir 1 h at 333 K; neutralize near pH 7 with 1 g NaOH in "
                "100 mL water; dry at 353 K for 24 h."
            ),
            purification_condition=(
                "acid functionalization followed by NaOH neutralization/drying"
            ),
            application_property_summary=(
                "Modified MWCNT CO2 adsorption reached 424.08 mg/g at "
                "25 C and 10 bar; application result, not CNT-production yield."
            ),
        )
    )

    tables["cost_scale_review"].append(
        cost_row(
            run_id,
            scale_level_demonstrated="lab_batch",
            scale_level_claimed="adsorbent_scale_up_potential",
            scale_evidence_summary=(
                "Five-gram catalyst charge in a 90 mm horizontal CVD tube; "
                "subsequent adsorption modeling discusses scale-up."
            ),
            reactor_capacity_or_throughput="5 g catalyst charge; product mass NR",
            continuous_operation_time_h="not_applicable",
            catalyst_lifetime_or_reuse="not reported for CNT synthesis",
            batch_stability="single CVD condition; replicate count not reported",
            scale_up_issue=(
                "Missing CNT mass yield, catalyst conversion, diameter/purity "
                "statistics and reproducibility limit production assessment."
            ),
            cost_driver_summary=(
                "Activated carbon, Fe/Ni nitrates, 973 K furnace duty, "
                "acetylene/argon and multi-step solvent/acid treatment."
            ),
            safety_risk=(
                "Acetylene at high temperature; Fe/Ni salts; dichloromethane; "
                "concentrated HCl/HNO3 and NaOH."
            ),
            emission_or_waste=(
                "Hydrocarbon exhaust, nitrate-containing catalyst preparation "
                "waste and halogenated/acidic liquid waste; not quantified."
            ),
            industrial_readiness_assessment=(
                "Adsorbent application demonstrated, but CNT production data "
                "are insufficient for manufacturing readiness."
            ),
            reproduction_value="medium; procedure has attribution ambiguities",
            reproduction_priority="medium",
            recommended_next_action=(
                "Resolve study 45, verify whether CVD/product data are primary, "
                "and measure CNT mass balance and structural distributions."
            ),
        )
    )

    append_evidence(
        tables,
        store,
        run_id,
        "CAT_IMPREGNATION",
        "catalyst_system",
        f"{run_id}_CAT",
        "precursor_summary;metal_ratio_original;preparation_method;"
        "preparation_modifier;preparation_detail;drying_condition;"
        "calcination_condition",
        "SPAN_4AAE9E4FB4714FAD8959",
        "Fe/Ni nitrate impregnation, drying, sieving and heat treatment.",
    )
    append_evidence(
        tables,
        store,
        run_id,
        "PURGE_HEAT",
        "reactor_process_gas",
        f"{run_id}_S01",
        "record_level",
        "SPAN_B02BAB1381C1036D49C6",
        "Catalyst charge, 90 mm quartz tube, Ar purge and heating rate.",
    )
    append_evidence(
        tables,
        store,
        run_id,
        "GROWTH",
        "reactor_process_gas",
        f"{run_id}_S02",
        "record_level",
        "SPAN_B98E8931E95E919AC9B5",
        "Reported 973 K acetylene/argon exposure and 30-min duration.",
    )
    append_evidence(
        tables,
        store,
        run_id,
        "COOL_PURGE",
        "reactor_process_gas",
        f"{run_id}_S03",
        "record_level",
        "SPAN_9E3A4F0883E2F7FCE94A",
        "Post-reaction cooling, acetylene stop and purge context.",
    )
    append_evidence(
        tables,
        store,
        run_id,
        "PRODUCT_ID",
        "yield_quality",
        f"{run_id}_PROD",
        "yield_original;CNT_type_reported;CNT_type_evidence",
        "SPAN_3172B367891BD7599C0C",
        "Paper conclusion identifies Fe-Ni/AC CVD synthesis of MWCNTs.",
    )
    append_evidence(
        tables,
        store,
        run_id,
        "BET",
        "yield_quality",
        f"{run_id}_PROD",
        "secondary_result_summary;BET_surface_area_product_m2_g",
        "SPAN_BDC64D942CE04C8DF96A",
        "Pristine and modified MWCNT BET surface areas.",
    )
    append_evidence(
        tables,
        store,
        run_id,
        "MORPHOLOGY",
        "yield_quality",
        f"{run_id}_PROD",
        "morphology;alignment_or_array;length_summary;characterization_methods",
        "SPAN_977EEDB52395C769D79A",
        "FESEM upright-forest morphology and acid-treatment observations.",
    )
    append_evidence(
        tables,
        store,
        run_id,
        "POST_TREATMENT",
        "yield_quality",
        f"{run_id}_PROD",
        "post_treatment_or_purification;purification_condition",
        "SPAN_20D821073C7077AE11CF",
        "Acid/alkali modification, neutralization and final drying.",
    )
    append_evidence(
        tables,
        store,
        run_id,
        "APPLICATION",
        "yield_quality",
        f"{run_id}_PROD",
        "application_property_summary",
        "SPAN_2D81293A947E760638FE",
        "Modified-MWCNT CO2 adsorption capacity and conditions.",
    )
    append_evidence(
        tables,
        store,
        run_id,
        "COST_REVIEW",
        "cost_scale_review",
        run_id,
        "record_level",
        "SPAN_B02BAB1381C1036D49C6",
        "Scale/cost/safety review from the reported batch apparatus.",
        "review_assessment",
    )

    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_ATTRIBUTION_001",
                SOURCE_ID,
                run_id,
                "primary_source_attribution_uncertainty",
                "source_run",
                run_id,
                "run_summary",
                (
                    "The methods say MWCNT synthesis followed previous study "
                    "45, and several characterization figures also cite 45. "
                    "It is unclear which production/characterization data are "
                    "new in this article versus reused."
                ),
                f"EVD_{run_id}_PRODUCT_ID;EVD_{run_id}_MORPHOLOGY",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_001",
                SOURCE_ID,
                run_id,
                "critical_data_gap",
                "yield_quality",
                f"{run_id}_PROD",
                "yield_original",
                (
                    "No CNT product mass, carbon conversion, catalyst-normalized "
                    "yield, diameter distribution, Raman ratio or TGA purity is "
                    "reported for the CVD production condition."
                ),
                f"EVD_{run_id}_PRODUCT_ID",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PROCESS_ROLE_001",
                SOURCE_ID,
                run_id,
                "definition_ambiguity",
                "reactor_process_gas",
                f"{run_id}_S02",
                "stage_type",
                (
                    "The detailed methods describe the acetylene exposure as "
                    "activation of Fe-Ni/AC, whereas the abstract/conclusion "
                    "identify CVD production of MWCNTs. It is represented as "
                    "the production stage pending source clarification."
                ),
                f"EVD_{run_id}_GROWTH;EVD_{run_id}_PRODUCT_ID",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_POST_TREATMENT_001",
                SOURCE_ID,
                run_id,
                "definition_ambiguity",
                "yield_quality",
                f"{run_id}_PROD",
                "post_treatment_or_purification",
                (
                    "The acid-treatment paragraph switches between MWCNT and "
                    "catalyst-sample terminology. The sequence is retained as "
                    "MWCNT modification because the surrounding text and FESEM "
                    "comparison describe pristine versus modified MWCNTs."
                ),
                f"EVD_{run_id}_POST_TREATMENT;EVD_{run_id}_MORPHOLOGY",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PRESSURE_001",
                SOURCE_ID,
                run_id,
                "critical_data_gap",
                "reactor_process_gas",
                f"{run_id}_S02",
                "pressure_original",
                "CVD operating pressure is not reported.",
                f"EVD_{run_id}_GROWTH",
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
    output = REPORT_ROOT / f"batch_{BATCH_NUMBER:03d}_metrics.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
