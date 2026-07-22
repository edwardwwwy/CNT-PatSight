#!/usr/bin/env python3
"""Transcribe the thesis's collaborator-grown CNT-forest electrode outcome."""

from __future__ import annotations

import json
from typing import Any

from scripts.extraction.batch_common import ROOT, TABLES, EvidenceStore, catalyst_row, cost_row, issue_row, load_metadata, master_row, process_row, run_row, yield_row
from scripts.extraction.build_b_class_batch_001 import add_evidence, publish_package

BATCH_ID = "B_CLASS_371_20260719"
REPORT_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
BATCH_NUMBER = 9
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
SOURCE_ID = "LIT_1DE84982FB5B0C57"


def build_source(metadata: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    run_id = f"{source_id}_CNT_FOREST_GOLD"
    tables = {name: [] for name in TABLES}
    master = master_row(metadata, "Collaborator-grown vertically aligned CNT forest directly on a gold electrode; exact collaborator recipe is not printed in the thesis.")
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{source_id}.parsed.json"
    master["notes"] = f"Source-specific first-pass transcription for {BATCH_NAME}; generic literature CVD conditions in the methodology chapter are not copied into the physical run."
    tables["source_master"].append(master)
    run = run_row(source_id, "CNT_FOREST_GOLD", "CNT forest grown directly on gold electrode", "Vertically aligned CNT forest was physically grown on a gold electrode on fused silica or silicon; the gold underlayer retarded growth and required a longer, unreported CVD time.", confidence="low")
    run["data_type"] = "experimental_condition_unmapped_outcome"
    tables["source_run"].append(run)
    tables["catalyst_system"].append(catalyst_row(
        run_id, catalyst_label="CNT-growth catalyst film; composition not specified for the collaborator run", active_metals="not_reported",
        support_material="gold electrode on fused silica or silicon wafer", metal_ratio_original="not_reported", precursor_summary="not_reported",
        preparation_method="catalyst film on substrate; exact deposition not reported", preparation_detail="CNT forest synthesized directly on the gold electrode by collaborators.",
        activation_condition="not_reported", post_preparation_condition="CNT forest used directly as an electrochemical working electrode",
    ))
    tables["reactor_process_gas"].append(process_row(
        run_id, 1, "thermal_CVD", reactor_type="not_reported", reactor_setup_summary="CNT forest grown directly on a gold electrode supported by fused silica or silicon.",
        scale_level="lab_batch", temperature_setpoint_C="not_reported", holding_time_min="not_reported", carbon_source="not_reported for the collaborator run",
        pressure_original="not_reported", pressure_kPa="", process_note="The thesis states that CVD time was increased to compensate for growth retardation by gold but does not print the exact recipe.",
    ))
    tables["yield_quality"].append(yield_row(
        run_id, primary_yield_metric="CNT forest formation on electrode", yield_original="not_reported", yield_definition_original="No mass yield or forest height reported for the synthesis run.",
        secondary_result_summary="Vertically aligned CNT forest obtained; preliminary comparison found less forest height on gold than on a catalyst-coated silicon wafer.",
        product_mixture_summary="CNT forest electrode", CNT_type_reported="vertically aligned CNT forest", CNT_type_confirmed="CNT forest",
        CNT_type_evidence="Source reports direct CVD growth and subsequent electrode use; no wall-count classification assigned.", morphology="vertically aligned CNT forest on gold electrode",
        characterization_methods="SEM stated for CNT-forest characterization; later electrochemical testing",
    ))
    tables["cost_scale_review"].append(cost_row(
        run_id, scale_evidence_summary="Laboratory electrode-scale collaborator synthesis.", cost_driver_summary="Gold electrode, catalyst film and thermal CVD; exact gas and energy use not reported.",
        safety_risk="Thermal CVD hazards; exact precursor and gas inventory not reported.", emission_or_waste="not_reported",
    ))
    add_evidence(tables, store, source_id, run_id, "CAT", "catalyst_system", f"{run_id}_CAT", "record_level", "SPAN_3BE3472DB4F56923CC36", "Gold-electrode substrate and unspecified CNT catalyst context.", confidence="medium")
    add_evidence(tables, store, source_id, run_id, "PROC", "reactor_process_gas", f"{run_id}_S01", "record_level", "SPAN_71E2C072D99EB9DB84F2", "Thermal-CVD outcome and unreported longer growth time on gold.", confidence="medium")
    add_evidence(tables, store, source_id, run_id, "PRODUCT", "yield_quality", f"{run_id}_PROD", "record_level", "SPAN_6B3D7965C8A044801580", "Vertically aligned CNT forest and reduced height on gold.", confidence="medium")
    add_evidence(tables, store, source_id, run_id, "SCALE", "cost_scale_review", run_id, "record_level", "SPAN_71E2C072D99EB9DB84F2", "Electrode/substrate-scale synthesis context.", confidence="low", value_status="review_assessment")
    tables["review_issue_log"].append(issue_row(
        f"{source_id}_ISSUE_RECIPE_001", source_id, run_id, "critical_data_gap", "reactor_process_gas", f"{run_id}_S01", "record_level",
        "The physical CNT forest is source-confirmed, but catalyst composition, exact gas recipe, temperature and time were performed by collaborators and are not printed; generic literature values are deliberately excluded.",
        f"EVD_{run_id}_PROC", "high",
    ))
    return tables


def main() -> None:
    metadata = load_metadata("B")
    store = EvidenceStore()
    try:
        metric = publish_package(SOURCE_ID, build_source(metadata[SOURCE_ID], store))
    finally:
        store.close()
    result = {"batch_id": BATCH_NAME, "sources": [metric], "total_runs": metric["row_counts"]["source_run"], "status": "completed_needs_review"}
    (REPORT_ROOT / "manual_batch_009_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
