#!/usr/bin/env python3
"""Manually transcribe polyethylene-waste/cenosphere CNT experiments.

The paper reports three condition/result pairs in its results figures.  The
prepared Ni-only catalyst is not emitted because the source gives no matching
experimental result for it.
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
BATCH_NUMBER = 4
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data" / "interim" / "candidate_extracts" / "B_class" / "batches" / BATCH_ID
SOURCE_ID = "LIT_004FAE25B3DA5255"


def build_source(
    metadata: dict[str, Any], store: EvidenceStore
) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    tables = {name: [] for name in TABLES}
    master = master_row(
        metadata,
        (
            "Ni/Co-cenosphere at 400 C, Co-cenosphere at 450 C, and "
            "Ni/Co-cenosphere at 450 C polyethylene-decomposition cases."
        ),
    )
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{source_id}.parsed.json"
    master["notes"] = (
        f"Manual first-pass transcription for {BATCH_NAME}; the Ni-only catalyst "
        "preparation is not emitted because no corresponding result is reported."
    )
    tables["source_master"].append(master)

    records = (
        (
            "NICO_PE400",
            "Ni/Co-cenosphere; polyethylene at 400 C",
            "Ni; Co",
            "nickel nitrate and cobalt nitrate mixture",
            "400",
            "carbon nanomaterial of amorphous structure; temperature insufficient for CNT synthesis",
            "not_reported",
            "not_applicable",
            "not_reported",
        ),
        (
            "CO_PE450",
            "Co-cenosphere; polyethylene at 450 C",
            "Co",
            "cobalt nitrate",
            "450",
            "mainly amorphous carbon with a small number of CNTs",
            "CNT",
            "confirmed",
            "60-70",
        ),
        (
            "NICO_PE450",
            "Ni/Co-cenosphere; polyethylene at 450 C",
            "Ni; Co",
            "nickel nitrate and cobalt nitrate mixture",
            "450",
            "CNT-coated cenospheres with small amorphous inclusions and about 300 nm carbon fibres",
            "CNT",
            "confirmed",
            "40-100",
        ),
    )

    for code, label, metals, precursor, pyrolysis_temp, result, cnt_type, confirmed, diameter in records:
        run_id = f"{source_id}_{code}"
        tables["source_run"].append(run_row(source_id, code, label, result))
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                catalyst_label=f"{metals.replace('; ', '/')}-impregnated cenospheres",
                active_metals=metals,
                support_material=(
                    "P100/500 cenospheres (100-500 micrometre; mainly SiO2 and Al2O3)"
                ),
                metal_ratio_original="100 g/L aqueous nitrate impregnation solution; metal ratio not reported",
                precursor_summary=precursor,
                preparation_method="aqueous impregnation",
                preparation_detail=(
                    "10 g cenospheres impregnated with the nitrate solution and dried "
                    "at 70 C for 2-3 h until moisture removal."
                ),
                drying_condition="70 C for 2-3 h",
                activation_condition="nitrates decomposed in situ to Ni and/or Co during synthesis",
            )
        )
        tables["reactor_process_gas"].extend(
            (
                process_row(
                    run_id,
                    1,
                    "polyethylene_pyrolysis",
                    reactor_type="three-zone furnace with 6 cm ID, 120.7 cm quartz reactor",
                    reactor_setup_summary="4 g polyethylene waste in a first-zone quartz cuvette.",
                    catalyst_loading_mass_g="1-2",
                    temperature_setpoint_C=pyrolysis_temp,
                    holding_time_min="30",
                    carbon_source="polyethylene waste",
                    carbon_source_flow_original="4 g batch; pyrolysis products transported downstream",
                    inert_gas="N2",
                    inert_gas_flow_original="540 cm3/min",
                    inert_gas_flow_sccm="540",
                    gas_composition_summary="polyethylene pyrolysis products in N2",
                ),
                process_row(
                    run_id,
                    2,
                    "CNT_growth",
                    reactor_type="three-zone furnace with 6 cm ID, 120.7 cm quartz reactor",
                    reactor_setup_summary=(
                        "Second zone at 700 C and catalyst-containing third zone at 800 C."
                    ),
                    catalyst_loading_mass_g="1-2",
                    temperature_setpoint_C="800",
                    holding_time_min="30",
                    carbon_source="polyethylene pyrolysis products",
                    inert_gas="N2",
                    inert_gas_flow_original="540 cm3/min",
                    inert_gas_flow_sccm="540",
                    gas_composition_summary="polyethylene-derived vapour transported by N2; intermediate zone 700 C",
                ),
            )
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="qualitative SEM product assessment",
                yield_original="not_reported",
                yield_definition_original="No gravimetric or conversion yield reported.",
                secondary_result_summary=result,
                product_mixture_summary=result,
                CNT_type_reported=cnt_type,
                CNT_type_confirmed=confirmed,
                CNT_type_evidence=(
                    "SEM morphology reported as carbon nanotubes."
                    if cnt_type == "CNT"
                    else "SEM showed amorphous carbon and the authors reported no nanotube synthesis."
                ),
                outer_diameter_range_nm=diameter,
                morphology=result,
                characterization_methods="SEM",
            )
        )
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                scale_evidence_summary="Laboratory three-zone quartz-reactor experiment using 4 g waste polyethylene.",
                cost_driver_summary="Furnace heating, nitrate-impregnated cenospheres and nitrogen transport gas.",
                safety_risk="Hot polymer pyrolysis vapour and nickel/cobalt compounds.",
                emission_or_waste="Polyethylene-derived vapour/off-gas and mixed amorphous-carbon deposits; not quantified.",
            )
        )

        catalyst_id = f"{run_id}_CAT"
        product_id = f"{run_id}_PROD"
        add_evidence(
            tables,
            store,
            source_id,
            run_id,
            "CAT",
            "catalyst_system",
            catalyst_id,
            "catalyst_label;active_metals;support_material;metal_ratio_original;precursor_summary;preparation_method;preparation_detail;drying_condition;activation_condition",
            "SPAN_5DA851F670109BE760A7",
            "Cenosphere composition, nitrate impregnation and drying procedure.",
        )
        for order, suffix in ((1, "PYR"), (2, "GROWTH")):
            add_evidence(
                tables,
                store,
                source_id,
                run_id,
                suffix,
                "reactor_process_gas",
                f"{run_id}_S{order:02d}",
                "record_level",
                "SPAN_47B8457A36D358A7BEEA" if order == 1 else "SPAN_6FB7A31C8488C3FEF9F2",
                "Polyethylene first-zone and downstream CNT-growth conditions.",
            )

        result_span = "SPAN_54A686627B56E31002E0" if code == "NICO_PE450" else "SPAN_06EA1D53C0FC99E7DE1B"
        add_evidence(
            tables,
            store,
            source_id,
            run_id,
            "PRODUCT",
            "yield_quality",
            product_id,
            "secondary_result_summary;product_mixture_summary;CNT_type_reported;CNT_type_confirmed;CNT_type_evidence;outer_diameter_range_nm;morphology;characterization_methods",
            result_span,
            "Condition-specific SEM result and CNT-diameter evidence.",
        )
        add_evidence(
            tables,
            store,
            source_id,
            run_id,
            "SCALE",
            "cost_scale_review",
            run_id,
            "scale_level_demonstrated;scale_evidence_summary;cost_driver_summary;safety_risk;emission_or_waste",
            "SPAN_47B8457A36D358A7BEEA",
            "Laboratory batch mass, furnace and waste-polyethylene context.",
        )

        issue_id = f"{source_id}_ISSUE_{code}_001"
        tables["review_issue_log"].append(
            issue_row(
                issue_id,
                source_id,
                run_id,
                "limited_quantitative_result",
                "yield_quality",
                product_id,
                "yield_original",
                (
                    "The source identifies this condition/result pair by figure and text but reports "
                    "no mass yield; retain the product assessment without inventing a yield."
                ),
                f"EVD_{run_id}_PRODUCT",
                "low",
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
    result = {
        "batch_id": BATCH_NAME,
        "sources": [metric],
        "total_runs": metric["row_counts"]["source_run"],
        "status": "completed_needs_review",
    }
    (REPORT_ROOT / "manual_batch_004_metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
