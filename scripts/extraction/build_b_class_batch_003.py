#!/usr/bin/env python3
"""Manually transcribe Fe/Si biased-hydrogen-plasma methane-CNT cases."""

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
BATCH_NUMBER = 3
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data" / "interim" / "candidate_extracts" / "B_class" / "batches" / BATCH_ID
SOURCE_ID = "LIT_5925FB1BAD7692D5"


def build_source(
    metadata: dict[str, Any], store: EvidenceStore
) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    tables = {name: [] for name in TABLES}
    master = master_row(
        metadata,
        "Untreated Fe/Si control and 5, 10, 20 and 30 min biased-hydrogen-plasma treatment cases.",
    )
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{source_id}.parsed.json"
    master["notes"] = (
        f"Manual first-pass transcription for {BATCH_NAME}; endpoint values printed in text are retained, "
        "while graph-only intermediate points are not digitized."
    )
    tables["source_master"].append(master)

    records = (
        ("UNTREATED", "Fe/Si without biased H2 plasma treatment", "0", "83% methane conversion", "not_reported", "not_reported", "Main deposited carbon formed particles; MWCNT growth was associated with plasma-treated cases."),
        ("H2P_5MIN", "Fe/Si after 5 min biased H2 plasma", "5", "93% methane conversion", "83% hydrogen yield", "not_reported", "Maximum printed methane conversion and hydrogen yield endpoint."),
        ("H2P_10MIN", "Fe/Si after 10 min biased H2 plasma", "10", "not_reported", "not_reported", "MWCNT height 30.7 nm", "Vertically grown MWCNT morphology; maximum printed height."),
        ("H2P_20MIN", "Fe/Si after 20 min biased H2 plasma", "20", "not_reported", "not_reported", "22.0 g carbon/g catalyst", "Maximum deposited-carbon endpoint; MWCNT diameter reached 22.5 nm in the printed discussion."),
        ("H2P_30MIN", "Fe/Si after 30 min biased H2 plasma", "30", "not_reported", "not_reported", "MWCNT diameter 9.8 nm", "Smallest printed MWCNT diameter endpoint."),
    )
    for code, label, treatment_minutes, methane_conversion, hydrogen_yield, product_metric, summary in records:
        run_id = f"{source_id}_{code}"
        tables["source_run"].append(run_row(source_id, code, label, summary))
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                catalyst_label="10 nm Fe film on Si wafer",
                active_metals="Fe",
                support_material="10 mm x 10 mm silicon wafer",
                precursor_summary="RF-sputtered Fe film",
                preparation_method="RF_sputtering",
                preparation_detail="Fe deposited onto Si using RF sputtering at 20 W; deposited Fe thickness 10 nm.",
                activation_condition=(
                    f"Biased H2 plasma for {treatment_minutes} min at -150 V, 550 C and 500 W."
                    if treatment_minutes != "0" else "not_applicable; untreated Fe/Si control"
                ),
                post_preparation_condition="used for microwave plasma methane decomposition",
            )
        )
        stage_order = 1
        if treatment_minutes != "0":
            tables["reactor_process_gas"].append(
                process_row(
                    run_id,
                    stage_order,
                    "biased_H2_plasma_activation",
                    reactor_type="low-pressure flow-type microwave remote-plasma reactor",
                    reactor_setup_summary="ULVAC CN-CVD-100R with catalyst 650 mm from waveguide.",
                    temperature_setpoint_C="550",
                    holding_time_min=treatment_minutes,
                    pressure_original="180 Pa initial",
                    pressure_kPa="0.18",
                    reducing_gas="H2",
                    reducing_gas_flow_original="80 mL/min",
                    reducing_gas_flow_sccm="80",
                    gas_composition_summary="H2 plasma; 500 W microwave; -150 V bias",
                )
            )
            stage_order += 1
        tables["reactor_process_gas"].append(
            process_row(
                run_id,
                stage_order,
                "microwave_methane_decomposition",
                reactor_type="low-pressure flow-type microwave remote-plasma reactor",
                reactor_setup_summary="ULVAC CN-CVD-100R with catalyst 650 mm from waveguide.",
                temperature_setpoint_C="600",
                holding_time_min="30",
                pressure_original="254 Pa initial",
                pressure_kPa="0.254",
                carbon_source="CH4",
                carbon_source_flow_original="CH4:H2 = 1:4 molar; total 100 mL/min",
                reducing_gas="H2",
                reducing_gas_flow_original="CH4:H2 = 1:4 molar; total 100 mL/min",
                total_flow_original="100 mL/min",
                total_flow_sccm="100",
                gas_composition_summary="CH4:H2 = 1:4; 500 W microwave; non-biased heating to 600 C",
            )
        )
        product_is_mwcnt = treatment_minutes != "0"
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="source-reported methane conversion / hydrogen yield / deposited carbon endpoint",
                yield_original="; ".join(value for value in (methane_conversion, hydrogen_yield, product_metric) if value != "not_reported") or "not_reported",
                yield_definition_original=(
                    "Methane conversion and hydrogen distribution are calculated from gas chromatography; "
                    "carbon yield is deposited-carbon mass divided by Fe/Si catalyst mass."
                ),
                carbon_source_conversion_percent=("93" if treatment_minutes == "5" else "83" if treatment_minutes == "0" else ""),
                secondary_result_summary=summary,
                CNT_type_reported=("MWCNT" if product_is_mwcnt else "not_reported"),
                CNT_type_confirmed=("MWCNT" if product_is_mwcnt else "not_applicable"),
                product_mixture_summary=("Vertically grown MWCNT-containing deposited carbon." if product_is_mwcnt else "Particle-like deposited carbon in untreated Fe/Si control."),
                CNT_type_evidence=("SEM and TEM; parallel graphite layers reported." if product_is_mwcnt else "not_reported"),
                outer_diameter_mean_nm=("22.5" if treatment_minutes == "20" else "9.8" if treatment_minutes == "30" else "not_reported"),
                length_summary=("maximum height 30.7 nm" if treatment_minutes == "10" else "not_reported"),
                morphology=("vertical MWCNT growth" if product_is_mwcnt else "particle-like deposited carbon"),
                characterization_methods="gas chromatography; SEM; TEM",
            )
        )
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                scale_evidence_summary="Laboratory microwave remote-plasma experiment on a 10 mm x 10 mm Fe/Si wafer.",
                cost_driver_summary="Microwave energy, H2 plasma activation, methane/hydrogen feed and RF-sputtered Fe/Si substrate.",
                safety_risk="Microwave plasma, low-pressure equipment and flammable H2/CH4 feeds.",
                emission_or_waste="Hydrocarbon/plasma off-gas and spent Fe/Si wafer; no quantitative source emission inventory.",
            )
        )
        add_evidence(
            tables, store, source_id, run_id, "CAT", "catalyst_system", f"{run_id}_CAT",
            "catalyst_label;active_metals;support_material;preparation_method;preparation_detail;activation_condition",
            "SPAN_0F6EEBF57265881FF4AA", "Fe/Si preparation and biased-hydrogen-plasma activation conditions."
        )
        if treatment_minutes != "0":
            add_evidence(
                tables, store, source_id, run_id, "ACT", "reactor_process_gas", f"{run_id}_S01",
                "stage_type;reactor_type;temperature_setpoint_C;holding_time_min;pressure_original;reducing_gas;reducing_gas_flow_original;gas_composition_summary",
                "SPAN_0F6EEBF57265881FF4AA", "Biased H2 plasma treatment setting."
            )
        reaction_stage = f"{run_id}_S{stage_order:02d}"
        add_evidence(
            tables, store, source_id, run_id, "PROC", "reactor_process_gas", reaction_stage,
            "stage_type;reactor_type;temperature_setpoint_C;holding_time_min;pressure_original;carbon_source;carbon_source_flow_original;reducing_gas;total_flow_original;gas_composition_summary",
            "SPAN_0F6EEBF57265881FF4AA", "Microwave methane/hydrogen reaction condition."
        )
        result_span = "SPAN_03AE1D6A21491DF0A6F6" if treatment_minutes == "0" else "SPAN_B5EE96DE36C0CB022C0E" if treatment_minutes == "5" else "SPAN_074064D05AFB87CF8699" if treatment_minutes in {"10", "30"} else "SPAN_7ED707B28E0CFEEDFA63"
        add_evidence(
            tables, store, source_id, run_id, "PRODUCT", "yield_quality", f"{run_id}_PROD",
            "primary_yield_metric;yield_original;yield_definition_original;carbon_source_conversion_percent;secondary_result_summary;CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;outer_diameter_mean_nm;length_summary;morphology",
            result_span, "Printed endpoint for the selected plasma-treatment case."
        )
        add_evidence(
            tables, store, source_id, run_id, "SCALE", "cost_scale_review", run_id,
            "scale_level_demonstrated;scale_evidence_summary;cost_driver_summary;safety_risk;emission_or_waste",
            "SPAN_0F6EEBF57265881FF4AA", "Laboratory microwave-plasma apparatus context.", "medium", "inferred"
        )

    first_run = f"{source_id}_UNTREATED"
    tables["review_issue_log"].extend(
        (
            issue_row(
                f"{source_id}_ISSUE_GRAPHS_001", source_id, first_run,
                "critical_data_gap", "yield_quality", f"{first_run}_PROD", "yield_original",
                "Intermediate treatment-time values are shown in figures; only endpoints explicitly printed in text or abstract are transcribed.",
                f"EVD_{first_run}_PRODUCT", "high",
            ),
            issue_row(
                f"{source_id}_ISSUE_CARBON_001", source_id, f"{source_id}_H2P_20MIN",
                "source_conflict", "yield_quality", f"{source_id}_H2P_20MIN_PROD", "yield_original",
                "The abstract assigns the maximum 22 g/gcat deposited-carbon value to 20 min, whereas one OCR-derived reference fragment says 10 min. The abstract-supported 20 min value is retained and this conflict remains open.",
                f"EVD_{source_id}_H2P_20MIN_PRODUCT", "high",
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
    (REPORT_ROOT / "manual_batch_003_metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
