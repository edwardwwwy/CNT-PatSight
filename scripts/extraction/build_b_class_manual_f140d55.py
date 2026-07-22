#!/usr/bin/env python3
"""Source-specific reconstruction of the reported standard wafer-scale SWCNT case."""

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
BATCH_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
SOURCE_ID = "LIT_F140D55ED8245E17"


def build_source(metadata: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    run_id = f"{source_id}_STANDARD_80MBAR"
    tables = {name: [] for name in TABLES}
    master = master_row(
        metadata,
        "Reported 80 mbar/800 C standard-recipe wafer-scale SWCNT forest; graph-only parametric values are excluded.",
    )
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{source_id}.parsed.json"
    master["notes"] = "Source-specific first-pass reconstruction from printed methods and narrative results; needs independent review."
    tables["source_master"].append(master)
    tables["source_run"].append(
        run_row(
            source_id,
            "STANDARD_80MBAR",
            "Standard 80 mbar / 800 C wafer-scale SWCNT forest",
            "Baseline cold-wall CVD recipe; only a single named standard condition is represented, not the graph-only scan points.",
        )
    )
    tables["catalyst_system"].append(
        catalyst_row(
            run_id,
            catalyst_label="Al2O3/Mo/Fe thin-film catalyst on Si wafer",
            active_metals="Mo; Fe",
            support_material="Si wafer with Al2O3 underlayer",
            metal_ratio_original="400 Å / 0.5 Å / 5.5 Å Al2O3/Mo/Fe",
            precursor_summary="e-beam-evaporated Al2O3/Mo/Fe thin-film stack",
            preparation_method="e_beam_evaporation",
            preparation_detail="400 Å Al2O3, 0.5 Å Mo and 5.5 Å Fe deposited on Si wafer by e-beam evaporation.",
            activation_condition="Annealed 2 min at 800 C and 80 mbar under Ar/H2 400/700 sccm; 100–200 ppm H2O introduced through an Ar water-bubbler stream.",
            post_preparation_condition="Immediately used for cold-wall CVD growth.",
        )
    )
    tables["reactor_process_gas"].extend(
        (
            process_row(
                run_id, 1, "catalyst_annealing",
                reactor_type="AIXTRON Black Magic cold-wall shower-head CVD furnace",
                reactor_setup_summary="Graphite heating stage and quartz showerhead; accommodates up to 6-inch wafers.",
                temperature_setpoint_C="800", holding_time_min="2",
                pressure_original="80 mbar", pressure_kPa="8",
                inert_gas="Ar", inert_gas_flow_original="400 sccm", inert_gas_flow_sccm="400",
                reducing_gas="H2", reducing_gas_flow_original="700 sccm", reducing_gas_flow_sccm="700",
                gas_composition_summary="Ar/H2 400/700 sccm; 100–200 ppm H2O vapor.",
            ),
            process_row(
                run_id, 2, "CNT_growth",
                reactor_type="AIXTRON Black Magic cold-wall shower-head CVD furnace",
                reactor_setup_summary="Temperature and pressure maintained from annealing; only growth-step variables were changed in scans.",
                temperature_setpoint_C="800", holding_time_min="not_reported",
                pressure_original="80 mbar", pressure_kPa="8",
                carbon_source="C2H2", carbon_source_flow_original="4 sccm", carbon_source_flow_sccm="4",
                inert_gas="Ar", inert_gas_flow_original="400 sccm", inert_gas_flow_sccm="400",
                reducing_gas="H2", reducing_gas_flow_original="700 sccm", reducing_gas_flow_sccm="700",
                gas_composition_summary="Ar/H2/C2H2 400/700/4 sccm with 100–200 ppm H2O vapor.",
            ),
        )
    )
    tables["yield_quality"].append(
        yield_row(
            run_id,
            primary_yield_metric="CNT forest mass was determined gravimetrically; printed standard-case mass is not reported.",
            yield_original="not_reported",
            yield_definition_original="CNT forest mass calculated from pre- and post-growth wafer weighing; 0.1 mg microbalance resolution.",
            secondary_result_summary="Reported standard forests were >96% SWCNT with ~2 nm average diameter, 5 nm maximum diameter and ~1×10^12 CNT/cm2 areal number density.",
            CNT_type_reported="SWCNT",
            CNT_type_confirmed="SWCNT",
            product_mixture_summary=">96% SWCNT reported for the same setup and carbon source at 80 mbar.",
            CNT_type_evidence="TEM diameter distribution plus stated SWCNT composition.",
            outer_diameter_mean_nm="2", outer_diameter_range_nm="maximum reported diameter 5 nm",
            morphology="vertically aligned CNT forest", characterization_methods="gravimetry; TEM; Raman; TGA",
        )
    )
    tables["cost_scale_review"].append(
        cost_row(
            run_id,
            scale_level_demonstrated="pilot",
            scale_level_claimed="wafer-scale; catalyst area scanned from 1 to 180 cm2",
            scale_evidence_summary="CVD furnace accommodates up to 6-inch wafers; the study reports a 1–180 cm2 catalyst-area scan.",
            cost_driver_summary="Wafer substrate, e-beam deposition, 800 C heating, high H2/Ar flow, acetylene and water-vapor control.",
            safety_risk="Flammable H2 and C2H2 at elevated temperature and reduced pressure.",
            emission_or_waste="Hydrocarbon/hydrogen off-gas and used catalyst wafers; no quantified emission inventory.",
        )
    )
    for suffix, table, record_id, fields, span_id, summary in (
        ("CAT", "catalyst_system", f"{run_id}_CAT", "catalyst_label;active_metals;support_material;metal_ratio_original;preparation_method;preparation_detail;activation_condition", "SPAN_6DC4C158638E27C4C291", "Thin-film catalyst stack and standard annealing conditions."),
        ("ANNEAL", "reactor_process_gas", f"{run_id}_S01", "stage_type;reactor_type;temperature_setpoint_C;holding_time_min;pressure_original;inert_gas;reducing_gas;gas_composition_summary", "SPAN_6DC4C158638E27C4C291", "Named standard annealing step."),
        ("GROWTH", "reactor_process_gas", f"{run_id}_S02", "stage_type;temperature_setpoint_C;pressure_original;carbon_source;carbon_source_flow_original;inert_gas;reducing_gas;gas_composition_summary", "SPAN_CBCA0D478FEA4A2C26C9", "Named standard growth composition."),
        ("PRODUCT", "yield_quality", f"{run_id}_PROD", "primary_yield_metric;yield_definition_original;secondary_result_summary;CNT_type_reported;CNT_type_confirmed;product_mixture_summary;outer_diameter_mean_nm;outer_diameter_range_nm;morphology", "SPAN_CBCA0D478FEA4A2C26C9", "Printed SWCNT composition, diameter and density for the named standard recipe."),
        ("SCALE", "cost_scale_review", run_id, "scale_level_demonstrated;scale_level_claimed;scale_evidence_summary;cost_driver_summary;safety_risk", "SPAN_278B487A1A70B75DE8CB", "Reported catalyst-area and process-window scale context."),
    ):
        add_evidence(tables, store, source_id, run_id, suffix, table, record_id, fields, span_id, summary)
    tables["review_issue_log"].extend(
        (
            issue_row(f"{source_id}_ISSUE_TIME_001", source_id, run_id, "critical_data_gap", "reactor_process_gas", f"{run_id}_S02", "holding_time_min", "The printed standard recipe does not provide a baseline growth duration; no duration is inferred.", f"EVD_{run_id}_GROWTH", "high"),
            issue_row(f"{source_id}_ISSUE_SCAN_001", source_id, run_id, "critical_data_gap", "yield_quality", f"{run_id}_PROD", "yield_original", "The study reports extensive parametric scans, but their plotted numerical points are not transcribed without source-table values or controlled digitization.", f"EVD_{run_id}_PRODUCT", "medium"),
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
    (REPORT_ROOT / "manual_f140d55_metrics.json").write_text(json.dumps({"source": metric, "status": "completed_needs_review"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metric, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
