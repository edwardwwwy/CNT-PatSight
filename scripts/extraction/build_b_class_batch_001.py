#!/usr/bin/env python3
"""Manually transcribe the first evidence-reviewed B-class paper.

This batch deliberately preserves the published one-hour methane-decomposition
matrix as separate runs.  A later three-hour morphology case is kept separate
instead of attaching its TEM result to every one-hour mass-increase result.
"""

from __future__ import annotations

import json
from typing import Any

from scripts.extraction.batch_common import (
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
from scripts.extraction.package_io import write_extraction_package


BATCH_ID = "B_CLASS_371_20260719"
REPORT_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
BATCH_NUMBER = 1
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = REPORT_ROOT
PACKAGE_ROOT = ROOT / "data/interim/extraction/B"
SOURCE_ID = "LIT_2A2F8594DBA4A040"


def add_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    source_id: str,
    run_id: str,
    suffix: str,
    table: str,
    record_id: str,
    fields: str,
    span_id: str,
    summary: str,
    confidence: str = "high",
    value_status: str = "reported",
) -> None:
    tables["evidence_index"].append(
        evidence_row(
            store,
            source_id,
            f"EVD_{run_id}_{suffix}",
            run_id,
            table,
            record_id,
            fields,
            span_id,
            summary,
            confidence,
            value_status,
        )
    )


def build_source(
    metadata: dict[str, Any], store: EvidenceStore
) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    tables = {name: [] for name in TABLES}
    master = master_row(
        metadata,
        (
            "Ni/CeZrO2 one-hour methane-decomposition matrix; a distinct "
            "three-hour CNT morphology case; and a Ni-MgO reference case."
        ),
    )
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{source_id}.parsed.json"
    master["notes"] = (
        f"Manual first-pass transcription for {BATCH_NAME}; all values remain "
        "needs_review and are linked to immutable local candidate spans."
    )
    tables["source_master"].append(master)

    matrix = (
        ("UNRED_02_7000", "unreduced; 2 vol.% CH4/Ar; GHSV 7000 h-1", "unreduced", "2", "7000", "2.1", "1.1"),
        ("UNRED_02_13000", "unreduced; 2 vol.% CH4/Ar; GHSV 13000 h-1", "unreduced", "2", "13000", "2.5", "1.3"),
        ("UNRED_10_7000", "unreduced; 10 vol.% CH4/Ar; GHSV 7000 h-1", "unreduced", "10", "7000", "8.3", "4.5"),
        ("UNRED_10_13000", "unreduced; 10 vol.% CH4/Ar; GHSV 13000 h-1", "unreduced", "10", "13000", "7.9", "4.2"),
        ("RED_02_7000", "pre-reduced; 2 vol.% CH4/Ar; GHSV 7000 h-1", "pre-reduced", "2", "7000", "3.6", "1.9"),
        ("RED_02_13000", "pre-reduced; 2 vol.% CH4/Ar; GHSV 13000 h-1", "pre-reduced", "2", "13000", "3.1", "1.7"),
        ("RED_10_7000", "pre-reduced; 10 vol.% CH4/Ar; GHSV 7000 h-1", "pre-reduced", "10", "7000", "9.0", "4.8"),
        ("RED_10_13000", "pre-reduced; 10 vol.% CH4/Ar; GHSV 13000 h-1", "pre-reduced", "10", "13000", "8.8", "4.7"),
    )
    for code, label, pretreatment, methane_percent, ghsv, mass_increase, carbon_ratio in matrix:
        run_id = f"{source_id}_{code}"
        tables["source_run"].append(
            run_row(
                source_id,
                code,
                label,
                (
                    "One-hour Ni/CeZrO2 methane-decomposition matrix entry; "
                    f"mass increase {mass_increase}% and C/Ni {carbon_ratio} mol/mol."
                ),
            )
        )
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                catalyst_label="10 wt.% Ni/CeZrO2 pellets",
                active_metals="Ni",
                support_material="CeZrO2 (68% Ce; 32% Zr) pellet",
                metal_ratio_original="10 wt.% nominal Ni",
                precursor_summary="Ni(NO3)2·6H2O aqueous solution",
                preparation_method="impregnation",
                preparation_detail=(
                    "CeZrO2 pellets containing 2 wt.% graphite were impregnated; "
                    "dried overnight at room temperature then 120 C for 12 h; "
                    "calcined 700 C for 5 h."
                ),
                drying_condition="room temperature overnight; 120 C for 12 h",
                calcination_condition="700 C for 5 h",
                reduction_condition=(
                    "5 vol.% H2/Ar at 700 C for 2 h"
                    if pretreatment == "pre-reduced"
                    else "not_applicable; unreduced test"
                ),
                BET_surface_area_m2_g="110",
            )
        )
        stage_order = 1
        if pretreatment == "pre-reduced":
            tables["reactor_process_gas"].append(
                process_row(
                    run_id,
                    stage_order,
                    "pre_reduction",
                    reactor_type="1.2 cm diameter quartz flow reactor",
                    temperature_setpoint_C="700",
                    holding_time_min="120",
                    reducing_gas="H2",
                    reducing_gas_flow_original="5 vol.% H2/Ar",
                    inert_gas="Ar",
                    gas_composition_summary="5 vol.% H2/Ar",
                    pressure_original="not_reported",
                    pressure_kPa="",
                )
            )
            stage_order += 1
        tables["reactor_process_gas"].append(
            process_row(
                run_id,
                stage_order,
                "methane_decomposition",
                reactor_type="1.2 cm diameter quartz flow reactor",
                temperature_setpoint_C="700",
                holding_time_min="60",
                carbon_source="CH4",
                carbon_source_flow_original=f"{methane_percent} vol.% CH4/Ar",
                inert_gas="Ar",
                gas_composition_summary=f"{methane_percent} vol.% CH4/Ar; GHSV {ghsv} h-1",
                GHSV_or_residence_time=f"{ghsv} h-1",
                pressure_original="not_reported",
                pressure_kPa="",
            )
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="catalyst mass increase after methane-decomposition test",
                yield_original=f"Δm = {mass_increase}% ; C/Ni = {carbon_ratio} mol/mol",
                yield_definition_original=(
                    "Table 1 reports increase in Ni/CeZrO2 mass after a 1 h CH4 decomposition test; "
                    "the source also reports deposited carbon per Ni mol."
                ),
                secondary_result_summary="CNT morphology was not assigned to this one-hour matrix entry.",
                CNT_type_reported="not_reported",
                CNT_type_confirmed="not_applicable",
                CNT_type_evidence="not_reported",
                characterization_methods="TGA reported separately for selected conditions",
            )
        )
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                scale_evidence_summary="Laboratory quartz flow-reactor matrix.",
                cost_driver_summary="Ni catalyst preparation, reactor heating and CH4/Ar supply; no source-specific cost calculation.",
                safety_risk="Hot methane-containing gas stream and hydrogen pretreatment where applicable.",
                emission_or_waste="Carbon deposits and reactor off-gas were generated; no quantitative source emission inventory.",
            )
        )
        add_evidence(
            tables, store, source_id, run_id, "CAT", "catalyst_system", f"{run_id}_CAT",
            "catalyst_label;active_metals;support_material;metal_ratio_original;preparation_method;preparation_detail;drying_condition;calcination_condition",
            "SPAN_316743AB3E3D6D06400D", "Ni/CeZrO2 pellet composition, impregnation, drying and calcination."
        )
        if pretreatment == "pre-reduced":
            add_evidence(
                tables, store, source_id, run_id, "RED", "reactor_process_gas", f"{run_id}_S01",
                "stage_type;temperature_setpoint_C;holding_time_min;reducing_gas;reducing_gas_flow_original",
                "SPAN_BA49E74DA993BB792505", "Published H2/Ar pre-reduction condition."
            )
        growth_stage = f"{run_id}_S{stage_order:02d}"
        add_evidence(
            tables, store, source_id, run_id, "PROC", "reactor_process_gas", growth_stage,
            "stage_type;reactor_type;temperature_setpoint_C;holding_time_min;carbon_source;carbon_source_flow_original;inert_gas;GHSV_or_residence_time",
            "SPAN_BA49E74DA993BB792505", "Published CH4 decomposition test configuration."
        )
        add_evidence(
            tables, store, source_id, run_id, "RESULT", "yield_quality", f"{run_id}_PROD",
            "primary_yield_metric;yield_original;yield_definition_original",
            "SPAN_05D42DB2689B3FB4D44F", "Table 1 mass-increase and C/Ni matrix values."
        )
        add_evidence(
            tables, store, source_id, run_id, "SCALE", "cost_scale_review", run_id,
            "scale_level_demonstrated;scale_evidence_summary;cost_driver_summary;safety_risk",
            "SPAN_97196FF415B136F70F56", "Quartz reactor and laboratory catalyst-testing context.", "medium", "inferred"
        )

    morphology_run = f"{source_id}_MORPH_10_7000_3H"
    tables["source_run"].append(
        run_row(
            source_id,
            "MORPH_10_7000_3H",
            "Ni/CeZrO2; 10 vol.% CH4/Ar; GHSV 7000 h-1; 3 h morphology case",
            "TEM-confirmed filamentous MWCNT product observed after a distinct three-hour test.",
        )
    )
    tables["catalyst_system"].append(
        catalyst_row(
            morphology_run,
            catalyst_label="10 wt.% Ni/CeZrO2 pellets",
            active_metals="Ni",
            support_material="CeZrO2 (68% Ce; 32% Zr) pellet",
            metal_ratio_original="10 wt.% nominal Ni",
            precursor_summary="Ni(NO3)2·6H2O aqueous solution",
            preparation_method="impregnation",
            preparation_detail="Same Ni/CeZrO2 preparation reported for the methane-decomposition matrix.",
            drying_condition="room temperature overnight; 120 C for 12 h",
            calcination_condition="700 C for 5 h",
            reduction_condition="not_reported for this morphology case",
        )
    )
    tables["reactor_process_gas"].append(
        process_row(
            morphology_run,
            1,
            "methane_decomposition",
            reactor_type="1.2 cm diameter quartz flow reactor",
            temperature_setpoint_C="700",
            holding_time_min="180",
            carbon_source="CH4",
            carbon_source_flow_original="10 vol.% CH4/Ar",
            inert_gas="Ar",
            gas_composition_summary="10 vol.% CH4/Ar; GHSV 7000 h-1",
            GHSV_or_residence_time="7000 h-1",
            pressure_original="not_reported",
            pressure_kPa="",
        )
    )
    tables["yield_quality"].append(
        yield_row(
            morphology_run,
            primary_yield_metric="not_reported",
            yield_original="not_reported",
            yield_definition_original="not_reported",
            secondary_result_summary="Filamentous carbon deposits; TEM confirmed parallel graphene layers characteristic of CNTs.",
            CNT_type_reported="multiwall CNT",
            CNT_type_confirmed="MWCNT",
            product_mixture_summary="Filamentous carbon deposits on some Ni/CeZrO2 grains; MWCNTs identified by TEM.",
            CNT_type_evidence="TEM evidence of parallel graphene layers.",
            outer_diameter_range_nm="up to 64",
            morphology="filamentous CNTs of varied curvature and length",
            characterization_methods="SEM; TEM",
        )
    )
    tables["cost_scale_review"].append(
        cost_row(
            morphology_run,
            scale_evidence_summary="Laboratory quartz flow-reactor morphology experiment.",
            cost_driver_summary="Ni/CeZrO2 preparation, 700 C reactor heating and CH4/Ar supply.",
            safety_risk="Hot methane-containing gas stream.",
            emission_or_waste="Carbon deposits and reactor off-gas; no quantitative source emission inventory.",
        )
    )
    for suffix, table, record_id, fields, span_id, summary in (
        ("CAT", "catalyst_system", f"{morphology_run}_CAT", "catalyst_label;active_metals;support_material;metal_ratio_original;preparation_method", "SPAN_316743AB3E3D6D06400D", "Ni/CeZrO2 catalyst preparation."),
        ("PROC", "reactor_process_gas", f"{morphology_run}_S01", "stage_type;reactor_type;temperature_setpoint_C;holding_time_min;carbon_source;carbon_source_flow_original;inert_gas;GHSV_or_residence_time", "SPAN_0CC8038B9EE83EE9E783", "Three-hour CH4 decomposition condition."),
        ("PRODUCT", "yield_quality", f"{morphology_run}_PROD", "CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;outer_diameter_range_nm;morphology", "SPAN_19E4281021A7A40DE008", "SEM/TEM identity and MWCNT outer-diameter evidence."),
        ("SCALE", "cost_scale_review", morphology_run, "scale_level_demonstrated;scale_evidence_summary;cost_driver_summary;safety_risk", "SPAN_97196FF415B136F70F56", "Laboratory reactor context."),
    ):
        add_evidence(tables, store, source_id, morphology_run, suffix, table, record_id, fields, span_id, summary)

    reference_run = f"{source_id}_NIMGO_10_7000_1H"
    tables["source_run"].append(
        run_row(
            source_id,
            "NIMGO_10_7000_1H",
            "Ni-MgO reference; 10 vol.% CH4/Ar; GHSV 7000 h-1; 1 h",
            "Reference catalyst with 79% deposited carbon and 8.9 mol C/mol Ni by TGA.",
        )
    )
    tables["catalyst_system"].append(
        catalyst_row(
            reference_run,
            catalyst_label="Ni-MgO reference catalyst",
            active_metals="Ni",
            support_material="MgO",
            metal_ratio_original="43 wt.% Ni",
            precursor_summary="nickel nitrate; magnesium nitrate; citric acid",
            preparation_method="sol_gel",
            preparation_detail="Ni-MgO reference made by sol-gel, then dried and calcined 700 C for 5 h.",
            drying_condition="120 C overnight",
            calcination_condition="700 C for 5 h",
        )
    )
    tables["reactor_process_gas"].append(
        process_row(
            reference_run,
            1,
            "methane_decomposition",
            reactor_type="1.2 cm diameter quartz flow reactor",
            temperature_setpoint_C="700",
            holding_time_min="60",
            carbon_source="CH4",
            carbon_source_flow_original="10 vol.% CH4/Ar",
            inert_gas="Ar",
            gas_composition_summary="10 vol.% CH4/Ar; GHSV 7000 h-1",
            GHSV_or_residence_time="7000 h-1",
            pressure_original="not_reported",
            pressure_kPa="",
        )
    )
    tables["yield_quality"].append(
        yield_row(
            reference_run,
            primary_yield_metric="deposited carbon content by TGA",
            yield_original="79% carbon content; 8.9 mol C/mol Ni",
            yield_definition_original="TGA carbon content after a 1 h methane-decomposition test; not CNT yield per catalyst.",
            TGA_carbon_content_wt_percent="79",
            secondary_result_summary="Deposited carbon was mostly structural according to the DTG peak near 715 C.",
            CNT_type_reported="not_reported",
            CNT_type_confirmed="not_applicable",
            CNT_type_evidence="not_reported",
            characterization_methods="TGA; DTG; XRD",
        )
    )
    tables["cost_scale_review"].append(
        cost_row(
            reference_run,
            scale_evidence_summary="Laboratory reference-catalyst experiment.",
            cost_driver_summary="Ni/MgO preparation, 700 C heating and CH4/Ar supply.",
            safety_risk="Hot methane-containing gas stream.",
            emission_or_waste="Carbon deposits and reactor off-gas; no quantitative source emission inventory.",
        )
    )
    for suffix, table, record_id, fields, span_id, summary in (
        ("CAT", "catalyst_system", f"{reference_run}_CAT", "catalyst_label;active_metals;support_material;metal_ratio_original;preparation_method;calcination_condition", "SPAN_97196FF415B136F70F56", "Ni-MgO reference preparation and loading."),
        ("PROC", "reactor_process_gas", f"{reference_run}_S01", "stage_type;reactor_type;temperature_setpoint_C;holding_time_min;carbon_source;carbon_source_flow_original;inert_gas;GHSV_or_residence_time", "SPAN_2C152BE9703EF1F933C9", "Reference CH4 decomposition condition."),
        ("RESULT", "yield_quality", f"{reference_run}_PROD", "primary_yield_metric;yield_original;yield_definition_original;TGA_carbon_content_wt_percent;secondary_result_summary", "SPAN_2C152BE9703EF1F933C9", "TGA carbon-content and C/Ni result."),
        ("SCALE", "cost_scale_review", reference_run, "scale_level_demonstrated;scale_evidence_summary;cost_driver_summary;safety_risk", "SPAN_97196FF415B136F70F56", "Laboratory reactor context."),
    ):
        add_evidence(tables, store, source_id, reference_run, suffix, table, record_id, fields, span_id, summary)

    first_run = f"{source_id}_UNRED_02_7000"
    tables["review_issue_log"].extend(
        (
            issue_row(
                f"{source_id}_ISSUE_MASS_001", source_id, first_run,
                "definition_ambiguity", "yield_quality", f"{first_run}_PROD", "yield_original",
                "Table 1 reports Δm (%) and C/Ni (mol/mol); these values are deposited-carbon indicators, not directly comparable CNT yield metrics.",
                f"EVD_{first_run}_RESULT", "high",
            ),
            issue_row(
                f"{source_id}_ISSUE_PRODUCT_001", source_id, first_run,
                "critical_data_gap", "yield_quality", f"{first_run}_PROD", "CNT_type_reported",
                "The source does not assign CNT morphology to each one-hour matrix condition; the distinct three-hour TEM case is retained as a separate run.",
                f"EVD_{first_run}_RESULT;EVD_{morphology_run}_PRODUCT", "high",
            ),
            issue_row(
                f"{source_id}_ISSUE_FLOW_001", source_id, first_run,
                "critical_data_gap", "reactor_process_gas", f"{first_run}_S01", "carbon_source_flow_sccm",
                "The reported methane concentration and GHSV do not identify an absolute gas flow for the matrix rows.",
                f"EVD_{first_run}_PROC", "medium",
            ),
        )
    )
    return tables


def publish_package(source_id: str, package: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    output_path = write_extraction_package(
        source_id,
        "B",
        package,
        extraction_status="needs_review",
    )
    return {
        "source_id": source_id,
        "output_path": output_path.relative_to(ROOT).as_posix(),
        "row_counts": {table: len(package[table]) for table in TABLES},
        "status": "needs_review",
    }


def main() -> None:
    metadata = load_metadata("B")
    store = EvidenceStore()
    try:
        metric = publish_package(SOURCE_ID, build_source(metadata[SOURCE_ID], store))
    finally:
        store.close()
    result = {"batch_id": BATCH_NAME, "sources": [metric], "total_runs": metric["row_counts"]["source_run"], "status": "completed_needs_review"}
    (REPORT_ROOT / "manual_batch_001_metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
