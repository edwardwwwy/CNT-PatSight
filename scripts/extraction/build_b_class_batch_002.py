#!/usr/bin/env python3
"""Manually transcribe B-class HDPE/Ni-on-ceramic CNT experiments."""

from __future__ import annotations

import json
from typing import Any

from scripts.extraction.batch_common import (
    ROOT,
    TABLES,
    EvidenceStore,
    catalyst_row,
    cost_row,
    issue_row,
    load_metadata,
    master_row,
    process_row,
    run_row,
    yield_row,
)
from scripts.extraction.build_b_class_batch_001 import add_evidence, publish_package


BATCH_ID = "B_CLASS_371_20260719"
REPORT_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
BATCH_NUMBER = 2
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data" / "interim" / "candidate_extracts" / "B_class" / "batches" / BATCH_ID
SOURCE_ID = "LIT_F131336078B20564"


def build_source(
    metadata: dict[str, Any], store: EvidenceStore
) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    tables = {name: [] for name in TABLES}
    master = master_row(
        metadata,
        (
            "0.5 mol L-1 Ni/ceramic temperature series and 0.1, 1.0 and "
            "2.0 mol L-1 Ni/ceramic comparisons at 700 C."
        ),
    )
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{source_id}.parsed.json"
    master["notes"] = (
        f"Manual first-pass transcription for {BATCH_NAME}; values remain needs_review "
        "and the unavailable Table 2 cells are not inferred."
    )
    tables["source_master"].append(master)

    records = (
        ("NI0P5_T600", "0.5 mol L-1 Ni/ceramic; 600 C", "0.5", "0.125", "600", "7.2 wt.% filamentous carbon", "21.2", "CNT diameter reported around 10 nm by SEM; 21.2 ± 5.6 nm TEM value reported for the first temperature-series image."),
        ("NI0P5_T700", "0.5 mol L-1 Ni/ceramic; 700 C", "0.5", "0.125", "700", "not_reported", "16.9", "Optimal temperature; abundant filamentous carbon and 16.9 ± 4.3 nm CNT diameter reported by TEM."),
        ("NI0P5_T800", "0.5 mol L-1 Ni/ceramic; 800 C", "0.5", "0.125", "800", "1.2 wt.% filamentous carbon", "", "Only a few filamentous carbons were observed and CNTs were difficult to find by TEM."),
        ("NI0P1_T700", "0.1 mol L-1 Ni/ceramic; 700 C", "0.1", "0.025", "700", "3.1 wt.% CNT/filamentous carbon", "15.7", "Lowest Ni-loading comparison; sparse filamentous carbon and 15.7 ± 3.6 nm mean CNT diameter."),
        ("NI1P0_T700", "1.0 mol L-1 Ni/ceramic; 700 C", "1.0", "0.251", "700", "9.4 wt.% CNT/filamentous carbon", "", "Highest reported CNT/filamentous-carbon production in the Ni-loading comparison."),
        ("NI2P0_T700", "2.0 mol L-1 Ni/ceramic; 700 C", "2.0", "0.508", "700", "not_reported", "24.9", "Highest Ni-loading comparison; 24.9 ± 2.3 nm mean CNT diameter."),
    )
    for code, label, concentration, precursor_mass, temperature, yield_value, diameter, result in records:
        run_id = f"{source_id}_{code}"
        tables["source_run"].append(
            run_row(source_id, code, label, result)
        )
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                catalyst_label=f"{concentration} mol L-1 Ni/Al2O3 ceramic membrane",
                active_metals="Ni",
                support_material="Al2O3 ceramic membrane (1 mm thick; 30 mm diameter)",
                metal_ratio_original=f"{concentration} mol L-1 Ni(NO3)2·6H2O precursor solution",
                precursor_summary=f"{precursor_mass} g Ni(NO3)2·6H2O in 5 mL ethanol",
                preparation_method="incipient wetness impregnation by precursor drop-loading",
                preparation_detail=(
                    "Precursor solution drop-loaded onto a ~1.32 g ceramic membrane; "
                    "dried at 100 C for 24 h, then calcined in air at 800 C for 3 h "
                    "with a 10 C/min ramp."
                ),
                drying_condition="100 C for 24 h",
                calcination_condition="800 C in air for 3 h; 10 C/min",
                BET_surface_area_m2_g="below 10",
                catalyst_particle_size_mean_nm=(
                    "11.4" if concentration == "0.1" else "35.2" if concentration == "2.0" else "not_reported"
                ),
                catalyst_particle_size_qualifier=(
                    "± 2.4 nm" if concentration == "0.1" else "± 3.5 nm" if concentration == "2.0" else "not_reported"
                ),
            )
        )
        tables["reactor_process_gas"].extend(
            (
                process_row(
                    run_id,
                    1,
                    "HDPE_pyrolysis",
                    reactor_type="two-stage catalytic thermal-chemical conversion reactor",
                    reactor_setup_summary="Plastic-pyrolysis first stage followed by catalytic gasification/CNT-growth second stage.",
                    catalyst_loading_mass_g="1.32",
                    temperature_setpoint_C="500",
                    holding_time_min="60",
                    carbon_source="HDPE",
                    carbon_source_flow_original="about 1 g HDPE per experiment; pyrolysis vapour feeds second stage",
                    inert_gas="N2",
                    inert_gas_flow_original="100 mL/min",
                    inert_gas_flow_sccm="100",
                    gas_composition_summary="HDPE pyrolysis under N2 carrier gas",
                    pressure_original="not_reported",
                    pressure_kPa="",
                ),
                process_row(
                    run_id,
                    2,
                    "catalytic_CNT_growth",
                    reactor_type="two-stage catalytic thermal-chemical conversion reactor",
                    reactor_setup_summary="Second-stage Ni/ceramic catalytic gasification/CNT-growth zone.",
                    catalyst_loading_mass_g="1.32",
                    temperature_setpoint_C=temperature,
                    holding_time_min="60",
                    carbon_source="HDPE pyrolysis vapour",
                    inert_gas="N2",
                    inert_gas_flow_original="100 mL/min",
                    inert_gas_flow_sccm="100",
                    gas_composition_summary="Pyrolysis vapour transported by N2 carrier gas",
                    cooling_condition="cooled to room temperature under continuous N2 at 100 mL/min",
                    pressure_original="not_reported",
                    pressure_kPa="",
                ),
            )
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="TGA-TPO filamentous-carbon fraction (treated as CNT proxy by source)",
                yield_original=yield_value,
                yield_definition_original=(
                    "Source separates amorphous carbon below 550 C oxidation and filamentous carbon "
                    "above 550 C oxidation, and treats the latter as a CNT proxy."
                ),
                secondary_result_summary=result,
                CNT_type_reported=("CNT" if temperature != "800" else "not_reported"),
                CNT_type_confirmed=("not_applicable" if temperature == "800" else "CNT"),
                product_mixture_summary=(
                    "Filamentous carbon; source treats the high-temperature TPO fraction as CNT proxy."
                    if temperature != "800" else "Few filamentous carbons; CNTs difficult to identify by TEM."
                ),
                CNT_type_evidence=("SEM; TEM; TGA-TPO" if temperature != "800" else "TEM found CNTs difficult to identify."),
                outer_diameter_mean_nm=diameter or "not_reported",
                outer_diameter_range_nm=("around 10" if code == "NI0P5_T600" else "not_reported"),
                characterization_methods="SEM; TEM; TGA-TPO; DTG-TPO; XRD",
                amorphous_carbon_level=("reported separately by TGA-TPO" if temperature != "800" else "predominant relative to scarce CNT-like product"),
            )
        )
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                scale_evidence_summary="Laboratory two-stage HDPE pyrolysis/catalytic-growth experiment.",
                cost_driver_summary="Ceramic membrane, nickel precursor, 500-800 C heating, nitrogen carrier gas and waste-HDPE handling.",
                safety_risk="Hot plastic pyrolysis vapours and reactor surfaces; gaseous pyrolysis products require controlled venting.",
                emission_or_waste="Spent Ni/ceramic catalyst, carbon deposits and plastic-pyrolysis off-gas; no quantitative source emission inventory.",
            )
        )
        add_evidence(
            tables, store, source_id, run_id, "CAT", "catalyst_system", f"{run_id}_CAT",
            "catalyst_label;active_metals;support_material;metal_ratio_original;precursor_summary;preparation_method;preparation_detail;drying_condition;calcination_condition;BET_surface_area_m2_g",
            "SPAN_ADD6C1E785225D105702", "Ni/ceramic precursor masses, loading labels, drying and calcination."
        )
        add_evidence(
            tables, store, source_id, run_id, "PROC1", "reactor_process_gas", f"{run_id}_S01",
            "stage_type;reactor_type;reactor_setup_summary;temperature_setpoint_C;holding_time_min;carbon_source;inert_gas;inert_gas_flow_original",
            "SPAN_9A3949BD5D3EFF39B177", "Two-stage HDPE-pyrolysis and catalytic-growth procedure."
        )
        add_evidence(
            tables, store, source_id, run_id, "PROC2", "reactor_process_gas", f"{run_id}_S02",
            "stage_type;temperature_setpoint_C;holding_time_min;carbon_source;inert_gas;inert_gas_flow_original;cooling_condition",
            "SPAN_9A3949BD5D3EFF39B177", "Second-stage temperature series and nitrogen flow/cooling condition."
        )
        result_span = "SPAN_919250D4F5E2417B1F93" if code in {"NI0P1_T700", "NI1P0_T700", "NI2P0_T700"} else "SPAN_5F7F41957DCFCD5D12B7"
        add_evidence(
            tables, store, source_id, run_id, "PRODUCT", "yield_quality", f"{run_id}_PROD",
            "primary_yield_metric;yield_original;yield_definition_original;secondary_result_summary;CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;outer_diameter_mean_nm;outer_diameter_range_nm;characterization_methods",
            result_span, "Source-reported CNT/filamentous-carbon production and morphology trend."
        )
        add_evidence(
            tables, store, source_id, run_id, "SCALE", "cost_scale_review", run_id,
            "scale_level_demonstrated;scale_evidence_summary;cost_driver_summary;safety_risk;emission_or_waste",
            "SPAN_9A3949BD5D3EFF39B177", "Laboratory two-stage reactor context.", "medium", "inferred"
        )

    first_run = f"{source_id}_NI0P5_T600"
    tables["review_issue_log"].extend(
        (
            issue_row(
                f"{source_id}_ISSUE_TABLE_001", source_id, first_run,
                "critical_data_gap", "yield_quality", f"{first_run}_PROD", "yield_original",
                "The parsed local text describes Table 2 but does not preserve every table cell; only values printed in surrounding prose are transcribed.",
                f"EVD_{first_run}_PRODUCT", "high",
            ),
            issue_row(
                f"{source_id}_ISSUE_PROXY_001", source_id, first_run,
                "definition_ambiguity", "yield_quality", f"{first_run}_PROD", "primary_yield_metric",
                "The source defines filamentous carbon by TPO oxidation above 550 C and assumes it represents CNTs; this is retained as a source-specific proxy rather than normalized CNT yield.",
                f"EVD_{first_run}_PRODUCT", "high",
            ),
            issue_row(
                f"{source_id}_ISSUE_DURATION_001", source_id, first_run,
                "definition_ambiguity", "reactor_process_gas", f"{first_run}_S01", "holding_time_min",
                "The article states total reaction time of 60 min without separately reporting first- and second-stage residence durations; both stage rows retain the shared total time and require review.",
                f"EVD_{first_run}_PROC1;EVD_{first_run}_PROC2",
            ),
        )
    )
    return tables


def main() -> None:
    metadata = load_metadata("B")
    store = EvidenceStore()
    try:
        metric = publish_package(SOURCE_ID, build_source(metadata[SOURCE_ID], store))
    finally:
        store.close()
    result = {"batch_id": BATCH_NAME, "sources": [metric], "total_runs": metric["row_counts"]["source_run"], "status": "completed_needs_review"}
    (REPORT_ROOT / "manual_batch_002_metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
