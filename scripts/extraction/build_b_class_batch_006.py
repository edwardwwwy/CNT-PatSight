#!/usr/bin/env python3
"""Transcribe the unique steel-slag/CNT CVD optimization conditions."""

from __future__ import annotations

import json
from typing import Any

from scripts.extraction.batch_common import (
    ROOT, TABLES, EvidenceStore, catalyst_row, cost_row, issue_row,
    load_metadata, master_row, process_row, run_row, yield_row,
)
from scripts.extraction.build_b_class_batch_001 import add_evidence, publish_package

BATCH_ID = "B_CLASS_371_20260719"
REPORT_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
BATCH_NUMBER = 6
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
SOURCE_ID = "LIT_0B337E3E2AB8B340"


def build_source(metadata: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    tables = {name: [] for name in TABLES}
    master = master_row(
        metadata,
        "Nine unique physical conditions from the time, temperature and acetylene-flow SS@CNT optimization series; the shared 45 min/600 C/200 sccm condition is emitted once.",
    )
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{source_id}.parsed.json"
    master["notes"] = f"Manual first-pass transcription for {BATCH_NAME}; adsorption tests are summarized only as an end-use result on the optimum synthesis run."
    tables["source_master"].append(master)

    # code, time, temperature, acetylene, carbon yield, diameter, Raman ID/IG,
    # BET area, series condition span, numeric table span, morphology span
    records = (
        ("T15", "15", "600", "200", "13", "10.3", "1.38", "36.75", "SPAN_25DC7A01C484BCF54E6E", "SPAN_F42939DE8F6544386F06", "SPAN_DA9C03CFCAD63CE26862"),
        ("T30", "30", "600", "200", "23", "12.8", "", "43.19", "SPAN_25DC7A01C484BCF54E6E", "SPAN_F42939DE8F6544386F06", "SPAN_DA9C03CFCAD63CE26862"),
        ("OPT_T45_600_F200", "45", "600", "200", "36", "17.5", "", "49.85", "SPAN_25DC7A01C484BCF54E6E", "SPAN_F42939DE8F6544386F06", "SPAN_DA9C03CFCAD63CE26862"),
        ("T60", "60", "600", "200", "39", "21.3", "1.19", "43.07", "SPAN_25DC7A01C484BCF54E6E", "SPAN_F42939DE8F6544386F06", "SPAN_DA9C03CFCAD63CE26862"),
        ("TEMP500", "45", "500", "200", "4.5", "8.4", "1.37", "15.89", "SPAN_6DA373DB939FC398012F", "SPAN_190183443D94E451608D", "SPAN_D12DF0249ACA02B4F41B"),
        ("TEMP700", "45", "700", "200", "17", "22.6", "", "15.74", "SPAN_6DA373DB939FC398012F", "SPAN_190183443D94E451608D", "SPAN_D12DF0249ACA02B4F41B"),
        ("TEMP800", "45", "800", "200", "15", "31.4", "1.13", "11.07", "SPAN_6DA373DB939FC398012F", "SPAN_190183443D94E451608D", "SPAN_D12DF0249ACA02B4F41B"),
        ("FLOW100", "45", "600", "100", "17", "7", "", "25.63", "SPAN_F25BCDD2ED74036F0981", "SPAN_B029D07CD41727CE6AA7", "SPAN_973D2C12054E25520C7C"),
        ("FLOW300", "45", "600", "300", "38", "41", "", "37.92", "SPAN_F25BCDD2ED74036F0981", "SPAN_B029D07CD41727CE6AA7", "SPAN_973D2C12054E25520C7C"),
    )

    for code, time_min, temp_c, c2h2, carbon_yield, diameter, raman, bet, condition_span, table_span, morphology_span in records:
        run_id = f"{source_id}_{code}"
        summary = (
            f"Steel-slag CVD at {temp_c} C for {time_min} min with H2/C2H2/N2 "
            f"400/{c2h2}/800 sccm; {carbon_yield} wt% carbon mass gain and about {diameter} nm CNT diameter."
        )
        if code == "OPT_T45_600_F200":
            summary += " Highest reported aspect ratio; this shared condition is the authors' selected optimum."
        tables["source_run"].append(run_row(source_id, code, f"SS@CNT {code}", summary))
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                catalyst_label="untreated steel slag intrinsic Fe-oxide catalyst/substrate",
                active_metals="Fe",
                support_material="steel slag",
                metal_ratio_original="33.98 wt% Fe2O3 in steel slag by XRF",
                precursor_summary="10 g well-ground as-received steel slag",
                preparation_method="no catalyst pretreatment",
                preparation_detail="Steel slag was ground, loaded directly into a porcelain boat and used without added catalyst.",
                activation_condition="heated under 200 sccm N2 to synthesis temperature",
            )
        )
        tables["reactor_process_gas"].append(
            process_row(
                run_id,
                1,
                "acetylene_CVD",
                reactor_type="horizontal tube furnace with 80 mm quartz tube and 200 mm heating zone",
                reactor_setup_summary="10 g steel slag in a porcelain boat in the furnace heating zone.",
                catalyst_loading_mass_g="10",
                temperature_setpoint_C=temp_c,
                holding_time_min=time_min,
                carbon_source="C2H2",
                carbon_source_flow_original=f"{c2h2} sccm",
                carbon_source_flow_sccm=c2h2,
                reducing_gas="H2",
                reducing_gas_flow_original="400 sccm",
                reducing_gas_flow_sccm="400",
                inert_gas="N2",
                inert_gas_flow_original="800 sccm during growth; 200 sccm heat-up; 800 sccm cool-down",
                inert_gas_flow_sccm="800",
                total_flow_original=f"{400 + int(c2h2) + 800} sccm during growth",
                total_flow_sccm=str(400 + int(c2h2) + 800),
                gas_composition_summary=f"H2/C2H2/N2 = 400/{c2h2}/800 sccm",
            )
        )
        secondary = f"Approximate CNT diameter {diameter} nm; product BET area {bet} m2/g."
        if code == "OPT_T45_600_F200":
            secondary += " Optimum composite later adsorbed up to 427.26 mg/g Pb(II) and 132.79 mg/g Cu(II)."
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="carbon mass gain relative to raw steel slag",
                yield_original=f"{carbon_yield} wt% carbon",
                yield_definition_original="100 x (total synthetic product mass - raw steel slag mass) / raw steel slag mass; includes CNT and amorphous carbon.",
                secondary_result_summary=secondary,
                product_mixture_summary="CNTs plus amorphous carbon on steel-slag particles",
                CNT_type_reported="CNT",
                CNT_type_confirmed="CNT",
                CNT_type_evidence="SEM/TEM tubular morphology; no wall-count class assigned in the source.",
                outer_diameter_mean_nm=diameter,
                Raman_ratio_type="ID/IG" if raman else "not_reported",
                Raman_ratio_value=raman or "not_reported",
                TGA_carbon_content_wt_percent=carbon_yield,
                morphology="CNTs coiled around steel-slag particles; condition-dependent amorphous carbon and aspect ratio",
                characterization_methods="TGA; Raman; SEM; TEM; BET",
                notes="BET value is retained in secondary_result_summary because the yield_quality schema has no product-surface-area field.",
            )
        )
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                scale_evidence_summary="Laboratory CVD batch using 10 g untreated steel-industry slag.",
                cost_driver_summary="Tube-furnace heating and H2/C2H2/N2 supply; no separately prepared catalyst.",
                safety_risk="Flammable acetylene and hydrogen at elevated temperature.",
                emission_or_waste="CVD off-gas and carbon-containing steel-slag composite; no quantitative inventory.",
                review_note="Waste-derived catalyst/support is a reported material advantage; industrial readiness is not inferred.",
            )
        )

        add_evidence(tables, store, source_id, run_id, "CAT", "catalyst_system", f"{run_id}_CAT", "record_level", "SPAN_96FCC722892137AF83DE", "Steel-slag composition, including 33.98 wt% Fe2O3.")
        add_evidence(tables, store, source_id, run_id, "METHOD", "reactor_process_gas", f"{run_id}_S01", "record_level", "SPAN_3727488900176A1DA7F6", "CVD reactor, slag mass and gas-handling method.")
        add_evidence(tables, store, source_id, run_id, "CONDITION", "reactor_process_gas", f"{run_id}_S01", "temperature_setpoint_C;holding_time_min;carbon_source_flow_original;gas_composition_summary", condition_span, "Series-specific physical synthesis condition.")
        add_evidence(tables, store, source_id, run_id, "YIELD", "yield_quality", f"{run_id}_PROD", "yield_original;yield_definition_original;TGA_carbon_content_wt_percent", table_span, "Condition-specific carbon-yield table.")
        add_evidence(tables, store, source_id, run_id, "MORPH", "yield_quality", f"{run_id}_PROD", "secondary_result_summary;product_mixture_summary;CNT_type_reported;CNT_type_confirmed;outer_diameter_mean_nm;Raman_ratio_type;Raman_ratio_value;morphology;characterization_methods", morphology_span, "Series-specific Raman, SEM and TEM results.")
        add_evidence(tables, store, source_id, run_id, "SCALE", "cost_scale_review", run_id, "record_level", "SPAN_3727488900176A1DA7F6", "Laboratory batch mass, reactor and gas-use evidence.")

        if code == "OPT_T45_600_F200":
            add_evidence(tables, store, source_id, run_id, "ADSORB", "yield_quality", f"{run_id}_PROD", "secondary_result_summary", "SPAN_66850A8998735536F672", "Optimum SS@CNT composite adsorption result.")
        tables["review_issue_log"].append(
            issue_row(
                f"{source_id}_ISSUE_{code}_001",
                source_id,
                run_id,
                "yield_basis",
                "yield_quality",
                f"{run_id}_PROD",
                "yield_original",
                "Reported carbon mass gain includes CNTs and amorphous carbon and must not be interpreted as purified CNT yield.",
                f"EVD_{run_id}_YIELD",
                "medium",
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
    (REPORT_ROOT / "manual_batch_006_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
