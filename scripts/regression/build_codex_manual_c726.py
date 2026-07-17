#!/usr/bin/env python3
"""Build the first Codex-manual eight-table package for the five-paper pilot.

This file deliberately contains no external-model invocation. It records only
facts read from the local P003-like candidate spans for C726; unresolved
secondary parameter series remain in review_issue_log.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.extraction.package import build_slotted_package

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID = "LIT_C726D1011E035C35"
OUT = ROOT / "data/interim/eight_table_staging/codex_manual/C726_NiMo_MgO_biogas"
TEMPLATE = ROOT / "data/interim/P003_Pan_2025_FeMo_MgO_Methane_CNT"
TABLES = (
    "source_master",
    "source_run",
    "catalyst_system",
    "reactor_process_gas",
    "yield_quality",
    "cost_scale_review",
    "evidence_index",
    "review_issue_log",
)

RATIO_RUNS = [
    ("R01", "NiMo(1:0.1)/MgO", "1:0.1", "0.09", "6.15", "7.84", "81.32", "92.63", "88.52", "99.59", "3.59", "30", "10–40", "6.53", "1.51"),
    ("R02", "NiMo(1:0.5)/MgO", "1:0.5", "0.37", "26.97", "26.94", "97.55", "98.80", "96.53", "99.32", "2.71", "27.88", "15–50", "6.09", ""),
    ("R03", "NiMo(1:1)/MgO", "1:1", "0.30", "20.16", "22.81", "97.34", "98.73", "98.04", "99.60", "3.72", "24.89", "15–30", "4.37", ""),
    ("R04", "NiMo(1:1.5)/MgO", "1:1.5", "0.30", "21.34", "23.31", "97.04", "98.60", "98.19", "99.73", "3.11", "24.40", "10–40", "5.62", ""),
    ("R05", "NiMo(1:2)/MgO", "1:2", "0.27", "19.31", "21.35", "97.64", "98.84", "98.19", "99.81", "3.22", "25.63", "15–35", "4.82", ""),
    ("R06", "NiMo(1:4)/MgO", "1:4", "0.24", "16.51", "19.21", "97.31", "98.75", "98.23", "99.65", "3.18", "26.91", "10–40", "4.76", "2.12"),
]
LOADING_RUNS = [
    ("R07", "1%wtNiMo/MgO", "1 wt%", "", "", "", "", "84.98", "59.1", "93.8", "2.02", "", "", "", ""),
    ("R08", "10%wtNiMo/MgO", "10 wt%", "0.2958", "13.54", "22.83", "96.06", "98.05", "94.2", "99.1", "2.24", "", "", "", ""),
    ("R09", "30%wtNiMo/MgO", "30 wt%", "0.3688", "26.97", "26.94", "98.39", "98.80", "96.5", "99.3", "2.71", "27.88", "15–50", "6.09", "1.10"),
    ("R10", "50%wtNiMo/MgO", "50 wt%", "0.2480", "11.46", "19.87", "97.49", "98.80", "96.6", "99.2", "2.36", "38.49", "15–70", "10.08", "2.39"),
    ("R11", "70%wtNiMo/MgO", "70 wt%", "0.2014", "15.27", "16.77", "97.29", "98.70", "96.3", "99.6", "5.37", "36.53", "20–60", "7.94", "2.20"),
]


def read_headers(table: str) -> list[str]:
    with (TEMPLATE / f"{table}.csv").open(encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f))


def row(table: str, **values: str) -> dict[str, str]:
    result = {key: "" for key in read_headers(table)}
    result.update({key: str(value) for key, value in values.items() if value is not None})
    return result


SPAN_MAP: dict[str, dict] = {}


def evidence(eid: str, run_id: str, table: str, record_id: str, fields: str, span_id: str) -> dict[str, str]:
    span = SPAN_MAP[span_id]
    return row(
        "evidence_index",
        evidence_id=eid,
        source_id=SOURCE_ID,
        run_id=run_id,
        target_table=table,
        target_record_id=record_id,
        target_fields=fields.replace("|", ";"),
        evidence_type="reported_text_or_table",
        value_status="reported",
        source_section="Experimental/Results",
        source_locator=span.get("page_range") or span.get("page_start") or "local_span",
        source_object_ref=span_id,
        evidence_text=span["text"],
        evidence_summary=f"Local parsed span {span_id} supports {fields}.",
        confidence="medium",
        linked_issue_id="not_applicable",
        notes="Codex manual first pass; needs_review.",
    )


def main() -> int:
    started = time.perf_counter()
    package = build_slotted_package(
        SOURCE_ID,
        ROOT / "data/interim/extraction_candidates/paper_text_section.csv",
        ROOT / "data/interim/extraction_candidates/candidate_experiment_span.csv",
    )
    global SPAN_MAP
    SPAN_MAP = {span["span_id"]: span for span in package["spans"]}
    prep = "SPAN_C92B40830625CB953D17"
    process = "SPAN_3FCFDDF9A328CC764588"
    result = "SPAN_C5E5DF3CF18B83824977"
    dims = "SPAN_379F4F2ECEABC977F6D8"
    table_dims = "SPAN_1A4D691234D939312FB4"
    raman = "SPAN_924C4024EA304B92B965"
    loading_result = "SPAN_F6AE1F81A695C6AEFCF1"
    scale = "SPAN_60CCE5157908C94C8E6F"

    runs = RATIO_RUNS + LOADING_RUNS
    source_master = [row("source_master", source_id=SOURCE_ID, source_type="paper", source_title="Dual function NiMo/MgO catalyst for biogas valorization to syngas and carbon nanotubes", publication_year="2025", authors_or_assignee="Pichawee Aieamsam-Aung; Narissara Simma; Sornsawan Juntala; Atthapon Srifa; Wanida Koo-Amornpattana; Prasert Reubroycharoen; Phorndranrat Suchamalawong; Choji Fukuhara; Sakhon Ratchahat", publication_venue="Scientific Reports", doi_or_patent_no="10.1038/s41598-025-99439-1", source_link="https://doi.org/10.1038/s41598-025-99439-1", source_database="local_metadata_snapshot", source_language="en", local_file_path="data/raw/fulltext/text/LIT_C726D1011E035C35.txt", pdf_status="legal_url_found", screening_class="candidate_extract", source_section_scope="Experimental catalyst preparation and main ratio/loading series; secondary temperature/flow/biogas-ratio/stability series flagged for review", extraction_status="needs_review", review_status="pending_review", notes="Codex first-pass extraction; independent evidence review required.")]

    source_run = []
    catalysts = []
    processes = []
    yields = []
    costs = []
    evidences = []
    for code, label, ratio, y, ypct, purity, syngas_y, syngas_p, ch4, co2, h2co, diameter, diameter_range, sd, raman_value in runs:
        rid = f"C726_{code}"
        source_run.append(row("source_run", run_id=rid, source_id=SOURCE_ID, run_label=label, data_type="experimental_run", target_track="CNT_production", relevance_class="candidate_extract", extraction_status="needs_review", extraction_confidence="medium", run_summary=f"{label}; main biogas CNT/syngas series at 900 °C for 1 h.", notes="Secondary parameter series not split in this first pass; see review_issue_log."))
        catalysts.append(row("catalyst_system", run_id=rid, catalyst_id=f"{rid}_CAT", catalyst_label=label, active_metals="Ni; Mo", support_material="MgO", promoter="Mo", metal_ratio_original=f"Ni:Mo = {ratio}", metal_ratio_standardized=ratio, precursor_summary="Ni(II) nitrate hexahydrate; ammonium heptamolybdate tetrahydrate", preparation_method="wetness impregnation", preparation_modifier="calcination", preparation_detail="Precursors dissolved in water, dropped into MgO, stirred, evaporated on hotplate; calcined 500 °C for 3 h.", drying_condition="hotplate evaporation to dried powder", calcination_condition="500 °C for 3 h", reduction_condition="H2 activation at 900 °C for 30 min", activation_condition="H2, 75 mL/min, 900 °C, 30 min", post_preparation_condition="fresh catalyst powder", catalyst_particle_size_mean_nm="", catalyst_particle_size_range_nm="", catalyst_particle_size_qualifier="", phase_or_state_summary="NiMo/MgO catalyst; metal loading series for R07-R11.", dispersion_summary="Not separately quantified in first pass.", deactivation_summary="", notes="CNT diameters are kept in yield_quality, never catalyst particle-size fields."))
        for order, stage in enumerate(("activation", "growth", "cooling"), 1):
            processes.append(row("reactor_process_gas", run_id=rid, process_stage_id=f"{rid}_S{order:02d}", stage_order=str(order), stage_type=stage, reactor_type="fixed-bed horizontal quartz tube", scale_level="lab_batch", reactor_material="quartz", reactor_size_summary="horizontal tube: 26 mm i.d.; 1100 mm length", reactor_setup_summary="1 g catalyst powder loaded in quartz boat at reactor center", catalyst_loading_mass_g="1", temperature_setpoint_C="900", temperature_program_summary="900 °C", holding_time_min="30" if stage == "activation" else ("60" if stage == "growth" else ""), heating_rate_C_min="", cooling_condition="He to room temperature" if stage == "cooling" else "", pressure_original="", pressure_kPa="", carbon_source="biogas (40 vol% CO2; 60 vol% CH4)" if stage == "growth" else "", carbon_source_flow_original="75 mL/min" if stage == "growth" else "", carbon_source_flow_sccm="75" if stage == "growth" else "", reducing_gas="H2" if stage == "activation" else "", reducing_gas_flow_original="75 mL/min" if stage == "activation" else "", reducing_gas_flow_sccm="75" if stage == "activation" else "", inert_gas="He" if stage == "cooling" else "", inert_gas_flow_original="", inert_gas_flow_sccm="", cofeed_or_reactive_gas="", cofeed_flow_original="", cofeed_flow_sccm="", total_flow_original="75 mL/min" if stage in {"activation", "growth"} else "", total_flow_sccm="75" if stage in {"activation", "growth"} else "", gas_composition_summary="H2 activation" if stage == "activation" else ("40 vol% CO2 + 60 vol% CH4" if stage == "growth" else "He cooling"), GHSV_or_residence_time="4500 mL/gcat·h" if stage == "growth" else "", process_note="Shared condition copied to this run; first-pass needs_review."))
        yields.append(row("yield_quality", run_id=rid, product_id=f"{rid}_PROD", primary_yield_metric="CNT mass productivity/yield", yield_original=f"{y} gCNT/gCat" if y else "not_reported", yield_definition_original="CNT yield and purity reported as average over 1 h; 1% loading has no detectable CNT yield", yield_calculation_method="Reported source table", yield_value_standardized=y, yield_unit_standardized="g/gcat" if y else "not_applicable", yield_standardization_note="", CNT_yield_per_catalyst_g_gcat=y, CNT_productivity_g_gcat_h="", carbon_source_conversion_percent=ch4, carbon_conversion_to_solid_percent="", secondary_result_summary=f"CNT yield {ypct}% ; CNT purity {purity}% ; syngas yield {syngas_y}% ; syngas purity {syngas_p}% ; CH4 conversion {ch4}% ; CO2 conversion {co2}% ; H2/CO {h2co}.", CNT_type_reported="MWCNTs" if y else "no detectable CNTs reported", CNT_type_confirmed="MWCNTs" if y else "not_applicable", product_mixture_summary="MWCNT carbon product with syngas co-production" if y else "No detectable CNTs in 1% loading result.", CNT_type_evidence="TEM/morphology table for ratio series and 30/50/70 wt% loading series." if y else "Table 6 reports dashes for CNT yield/purity.", SWCNT_or_few_wall_evidence_summary="", RBM_peak_reported="", outer_diameter_mean_nm="", outer_diameter_range_nm="", inner_diameter_mean_nm="", wall_number_summary="multi-walled" if y else "", length_summary="", morphology=f"CNT diameter mean {diameter} nm; range {diameter_range}; SD {sd} nm" if diameter else "", alignment_or_array="", Raman_ratio_type="IG/ID" if raman_value else "", Raman_ratio_value=raman_value, Raman_laser_wavelength_nm="532", TGA_carbon_content_wt_percent="", purified_product_purity_wt_percent=purity, purity_basis="reported CNT purity" if purity else "", residue_summary="", amorphous_carbon_level="", BET_surface_area_product_m2_g="", characterization_methods="TEM; FE-SEM; Raman; TGA; XRD" if y else "TGA/production table", post_treatment_or_purification="", purification_condition="", application_property_summary="", notes="Graphitic/TGA observations remain separate from CNT purity."))
        costs.append(row("cost_scale_review", run_id=rid, scale_level_demonstrated="lab_batch", scale_level_claimed="industrial-scale potential mentioned by authors", scale_evidence_summary="1 g catalyst laboratory fixed-bed series", reactor_capacity_or_throughput="75 mL/min biogas; 4500 mL/gcat·h", continuous_operation_time_h="1", catalyst_lifetime_or_reuse="", catalyst_reuse_cycles="", batch_stability="", scale_up_issue="", quantitative_cost_reported="not_reported", quantitative_cost_summary="not_reported", cost_driver_summary="Ni/Mo loading and biogas process; no cost calculation extracted", safety_risk="H2 and combustible biogas; review needed", emission_or_waste="CO2/CH4 conversion process; review needed", industrial_readiness_assessment="", reproduction_value="", reproduction_priority="", industrial_value_score="", recommended_next_action="", review_note="First pass; independent evidence review required."))
        evidences.extend([
            evidence(f"EVD_{rid}_CAT", rid, "catalyst_system", f"{rid}_CAT", "catalyst_label|active_metals|support_material|metal_ratio_original|preparation_method", prep),
            evidence(f"EVD_{rid}_PROC_S01", rid, "reactor_process_gas", f"{rid}_S01", "record_level", process),
            evidence(f"EVD_{rid}_PROC_S02", rid, "reactor_process_gas", f"{rid}_S02", "record_level", process),
            evidence(f"EVD_{rid}_PROC_S03", rid, "reactor_process_gas", f"{rid}_S03", "record_level", process),
            evidence(f"EVD_{rid}_YIELD", rid, "yield_quality", f"{rid}_PROD", "record_level", result if code.startswith("R0") else loading_result),
            evidence(f"EVD_{rid}_COST", rid, "cost_scale_review", rid, "record_level", scale),
        ])
        if diameter:
            evidences.append(evidence(f"EVD_{rid}_DIMS", rid, "yield_quality", f"{rid}_PROD", "morphology|CNT_type_reported", dims if code.startswith("R0") else table_dims))
        if raman_value:
            evidences.append(evidence(f"EVD_{rid}_RAMAN", rid, "yield_quality", f"{rid}_PROD", "Raman_ratio_type|Raman_ratio_value", raman))

    issue_id = "C726_ISSUE_SCOPE_001"
    issues = [row("review_issue_log", issue_id=issue_id, source_id=SOURCE_ID, run_id="C726_R09", issue_type="critical_data_gap", target_table="source_run", target_record_id="C726_R09", target_field="record_level", issue_summary="First pass covers the main Ni:Mo ratio and metal-loading series but does not yet split the secondary temperature, flow-rate, biogas-composition, and 100 h stability series.", conflicting_values="", evidence_ids="EVD_C726_R09_YIELD", severity="medium", review_status="pending_review", reviewer="", reviewed_at="", resolution="", notes="Resolve during independent evidence review before formalization.")]

    OUT.mkdir(parents=True, exist_ok=True)
    for name, values in {
        "source_master": source_master,
        "source_run": source_run,
        "catalyst_system": catalysts,
        "reactor_process_gas": processes,
        "yield_quality": yields,
        "cost_scale_review": costs,
        "evidence_index": evidences,
        "review_issue_log": issues,
    }.items():
        with (OUT / f"{name}.csv").open("w", encoding="utf-8-sig", newline="") as f:
            fields = read_headers(name)
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(values)
    metrics = {
        "source_id": SOURCE_ID,
        "batch_id": "CODEX_MANUAL_5_20260716",
        "input_selected_chars": package["selection_stats"]["selected_text_chars"],
        "input_candidate_spans": len(package["spans"]),
        "estimated_input_tokens_chars_div_4": round(package["selection_stats"]["selected_text_chars"] / 4),
        "output_fact_rows": {"source_run": len(source_run), "catalyst_system": len(catalysts), "reactor_process_gas": len(processes), "yield_quality": len(yields), "cost_scale_review": len(costs), "evidence_index": len(evidences), "review_issue_log": len(issues)},
        "elapsed_generation_seconds": round(time.perf_counter() - started, 3),
        "status": "needs_review",
        "notes": "Token figure is an estimate from selected package chars; Codex internal generation-token telemetry is not exposed by the desktop runtime.",
    }
    (OUT / "codex_manual_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
