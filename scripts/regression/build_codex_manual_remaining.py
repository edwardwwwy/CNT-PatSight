#!/usr/bin/env python3
"""Build Codex-manual first-pass packages for the other four local papers.

No external model call is made here. Values are transcribed from the
local candidate spans and deliberately remain needs_review.
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
TEMPLATE = ROOT / "data/interim/P003_Pan_2025_FeMo_MgO_Methane_CNT"
SPAN_CSV = ROOT / "data/interim/extraction_candidates/candidate_experiment_span.csv"
SECTION_CSV = ROOT / "data/interim/extraction_candidates/paper_text_section.csv"

TABLES = ("source_master", "source_run", "catalyst_system", "reactor_process_gas", "yield_quality", "cost_scale_review", "evidence_index", "review_issue_log")

SOURCES = {
    "LIT_15F49C3012600D0B": {
        "folder": "15F_waste_PP_NiFeCo_Al2O3", "title": "Monometallic and Bimetallic Ni, Fe, and Co Catalysts to Produce Carbon Nanotubes from Pyrolysis-Catalysis of Waste Polypropylene", "year": "2026", "venue": "Waste and Biomass Valorization", "doi": "10.1007/s12649-026-03645-5", "authors": "Mohammed A. Farji; Paul T. Williams", "prep": "SPAN_F3402D2A974CC7FA388E", "process": "SPAN_F3402D2A974CC7FA388E", "result": "SPAN_4F6BF8178C49C617A7BD", "dims": "SPAN_0C990F7CFEDAA96DA6BD", "runs": [
            ("R01", "Ni/Al2O3", "Ni", "10 wt% Ni", "285", "mg/gplastic", "Ni/Al2O3 produced about 285 mg carbon deposit per g plastic", "14.66", "7.5-39.33", "23"),
            ("R02", "Fe/Al2O3", "Fe", "10 wt% Fe", "285", "mg/gplastic", "Fe/Al2O3 produced about 285 mg carbon deposit per g plastic", "13.50", "4.04-29.7", "17"),
            ("R03", "Co/Al2O3", "Co", "10 wt% Co", "184.6", "mg/gplastic", "Co/Al2O3 produced 184.6 mg carbon deposit per g plastic", "11.75", "3.99-20.12", "17"),
            ("R04", "Ni-Fe/Al2O3", "Ni; Fe", "5 wt% Ni + 5 wt% Fe", "420.7", "mg/gplastic", "Ni-Fe/Al2O3 produced 420.7 mg carbon deposit per g plastic", "11.87", "6.6-23.97", "18"),
            ("R05", "Ni-Co/Al2O3", "Ni; Co", "5 wt% Ni + 5 wt% Co", "212", "mg/gplastic", "Ni-Co/Al2O3 produced about 212 mg carbon deposit per g plastic", "14.61", "5.4-30.3", "26"),
        ], "issue": "Main five catalyst comparison extracted; steam/feed details and any additional operating-condition series require human review."
    },
    "LIT_4C5EB40B8CD80C4F": {
        "folder": "4C5_CoCu_CDC_methane", "title": "Selective synthesis of carbon nanotubes by catalytic decomposition of methane using Co-Cu/cellulose derived carbon catalysts: A comprehensive kinetic study", "year": "2021", "venue": "Chemical Engineering Journal", "doi": "10.1016/j.cej.2020.126103", "authors": "W. Henao; F. Cazaña; P. Tarifa; E. Romeo; N. Latorre; V. Sebastian; J.J. Delgado; A. Monzón", "prep": "SPAN_583D5474533DC92C67C1", "process": "SPAN_4FFB5C99F9E153B79A1E", "result": "SPAN_6BAEFA12666A4DA87B1D", "dims": "SPAN_4474257BA98D0EBC3799", "runs": [
            ("R01", "Co-Cu/CDC optimum CNT condition", "Co; Cu", "nominal 5% Co + 1.35% Cu; Co/Cu=4", "0.29", "gC/gcat·h", "Best reported CNT productivity 0.29 gC/gcat·h at 750 °C, 28.6% CH4:14.3% H2:57.1% N2; ID/IG=1.10", "", "", ""),
        ], "issue": "Temperature (650-950 °C), gas-composition, and long-operation series are represented by the optimum run only; split review required before promotion."
    },
    "LIT_401BD476DB8344E9": {
        "folder": "401_NiCuCoCu_ArDC_methane", "title": "Hydrogen and CNT Production by Methane Cracking Using Ni-Cu and Co-Cu Catalysts Supported on Argan-Derived Carbon", "year": "2022", "venue": "ChemEngineering", "doi": "10.3390/chemengineering6040047", "authors": "Fernando Cazaña; Zainab Afailal; Miguel González-Martín; José Luis Sánchez; Nieves Latorre; Eva Romeo; Jesús Arauzo; Antonio Monzón", "prep": "SPAN_88B8D800ED82282D12A5", "process": "SPAN_0A1D044C50BFE4F4EB28", "result": "SPAN_06B0520BF795CB3017BF", "dims": "SPAN_94FCB4497285CF5A28AA", "runs": [
            ("R01", "Ni-Cu/ArDC", "Ni; Cu", "nominal 5% Ni + 1.35% Cu; Ni/Cu=4", "3.7", "gC/gmetal", "Ni-Cu/ArDC at 900 °C and CH4:H2=2 produced 3.7 gC/gmetal after 2 h; H2 productivity 0.61 g/gmetal·h", "", "", ""),
            ("R02", "Co-Cu/ArDC", "Co; Cu", "nominal 5% Co + 1.35% Cu; Co/Cu=4", "1.4", "gC/gmetal", "Co-Cu/ArDC produced 1.4 gC/gmetal; best CNT selectivity is around 800 °C", "", "", ""),
        ], "issue": "Temperature and CH4:H2 ratio series are summarized by representative catalyst runs; full run split and CNT-versus-graphitic product assignment require review."
    },
    "LIT_9B43B350883D2B6F": {
        "folder": "9B43_corn_cob_char_NiMo_PP", "title": "Corn Cob Char as Catalyst Support for Developing Carbon Nanotubes from Waste Polypropylene Plastics: Comparison of Activation Techniques", "year": "2022", "venue": "Polymers", "doi": "10.3390/polym14142898", "authors": "Helen U. Modekwe; Kapil Moothi; Michael O. Daramola; Messai A. Mamo", "prep": "SPAN_1D2CB083D2525CF6AD40", "process": "SPAN_8C9B834A88E7C6B80B09", "result": "SPAN_CDAA16BFFFF41BD1238C", "dims": "SPAN_7F575AEB5F019E2A7D09", "runs": [
            ("R01", "NiMo/AC0", "Ni; Mo", "10 wt% Ni; Ni:Mo=5:1; non-activated char", "430", "mg/gcat", "Table 4 reports 430 mg CNTs/g catalyst and IG/ID=1.09 for CNT0", "", "12-36", ""),
            ("R02", "NiMo/ACX", "Ni; Mo", "10 wt% Ni; Ni:Mo=5:1; KOH-treated char", "470", "mg/gcat", "Table 4 reports 470 mg CNTs/g catalyst and IG/ID=1.08 for CNTX", "", "10-40", ""),
            ("R03", "NiMo/ACT", "Ni; Mo", "10 wt% Ni; Ni:Mo=5:1; steam-activated char", "70", "mg/gcat", "Table 4 reports 70 mg CNTs/g catalyst and IG/ID=1.44 for CNTT", "", "10-30", ""),
        ], "issue": "The table gives three activation-condition runs; catalyst text, purification basis, and mixed amorphous/metal residue content need human review."
    },
}

def headers(table: str) -> list[str]:
    with (TEMPLATE / f"{table}.csv").open(encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f))

def mkrow(table: str, **values: str) -> dict[str, str]:
    out = {k: "" for k in headers(table)}
    out.update({k: str(v) for k, v in values.items() if v is not None})
    return out

def make_package(source_id: str, cfg: dict) -> dict:
    started = time.perf_counter()
    pkg = build_slotted_package(source_id, SECTION_CSV, SPAN_CSV)
    spans = {s["span_id"]: s for s in pkg["spans"]}
    outdir = ROOT / "data/interim/eight_table_staging/codex_manual" / cfg["folder"]
    def ev(eid: str, rid: str, table: str, record: str, fields: str, sid: str) -> dict[str, str]:
        s = spans[sid]
        return mkrow("evidence_index", evidence_id=eid, source_id=source_id, run_id=rid, target_table=table, target_record_id=record, target_fields=fields.replace("|", ";"), evidence_type="reported_text_or_table", value_status="reported", source_section="Experimental/Results", source_locator=s.get("page_range") or s.get("page_start") or "local_span", source_object_ref=sid, evidence_text=s["text"], evidence_summary=f"Local parsed span {sid} supports {fields}.", confidence="medium", linked_issue_id="not_applicable", notes="Codex manual first pass; needs_review.")
    master = [mkrow("source_master", source_id=source_id, source_type="paper", source_title=cfg["title"], publication_year=cfg["year"], authors_or_assignee=cfg["authors"], publication_venue=cfg["venue"], doi_or_patent_no=cfg["doi"], source_link=f"https://doi.org/{cfg['doi']}", source_database="local_metadata_snapshot", source_language="en", local_file_path=f"data/raw/fulltext/text/{source_id}.txt", pdf_status="legal_url_found", screening_class="candidate_extract", source_section_scope="Main catalyst comparison/optimum series transcribed from local candidate spans; secondary series flagged", extraction_status="needs_review", review_status="pending_human_review", notes="Codex manual extraction; no external model inference; domain_expert_verified=false.")]
    runs, cats, procs, yqs, costs, evs = [], [], [], [], [], []
    for code, label, metals, ratio, y, yunit, summary, dmean, drange, walls in cfg["runs"]:
        rid = f"{source_id}_{code}"
        runs.append(mkrow("source_run", run_id=rid, source_id=source_id, run_label=label, data_type="experimental_run", target_track="CNT_production", relevance_class="candidate_extract", extraction_status="needs_review", extraction_confidence="medium", run_summary=summary, notes="Secondary operating-condition series not fully split; see review_issue_log."))
        cats.append(mkrow("catalyst_system", run_id=rid, catalyst_id=f"{rid}_CAT", catalyst_label=label, active_metals=metals, support_material="γ-Al2O3" if source_id.startswith("LIT_15") else ("cellulose-derived carbon" if source_id.startswith("LIT_4C5") else ("Argan-derived carbon" if source_id.startswith("LIT_401") else "corn-cob-derived activated char")), promoter="Cu" if "Cu" in metals else ("Mo" if "Mo" in metals else ""), metal_ratio_original=ratio, metal_ratio_standardized=ratio, precursor_summary="Reported nitrate precursors; see catalyst-preparation evidence.", preparation_method="incipient wetness impregnation" if source_id != "LIT_9B43B350883D2B6F" else "impregnation", preparation_modifier="calcination/thermal decomposition", preparation_detail="See linked preparation span; no ungrounded particle-size assignment.", drying_condition="reported in preparation span", calcination_condition="reported in preparation span", reduction_condition="reported in preparation span", activation_condition="not_reported", post_preparation_condition="fresh catalyst", catalyst_particle_size_mean_nm="", catalyst_particle_size_range_nm="", catalyst_particle_size_qualifier="", BET_surface_area_m2_g="", pore_diameter_nm="", pore_volume_cm3_g="", phase_or_state_summary="", dispersion_summary="", deactivation_summary="", notes="CNT dimensions remain in yield_quality, never catalyst particle-size fields."))
        for order, stage in enumerate(("activation", "growth", "cooling"), 1):
            if source_id.startswith("LIT_15"):
                temp, hold, carbon, flow, reductant = "800", "180", "waste polypropylene pyrolysis vapour", "not_reported", "5 vol% H2/95 vol% N2"
            elif source_id.startswith("LIT_4C5"):
                temp, hold, carbon, flow, reductant = "750", "120", "CH4", "700 mL/min", "H2/N2 feed"
            elif source_id.startswith("LIT_401"):
                temp, hold, carbon, flow, reductant = ("900" if code == "R01" else "800"), "120", "CH4", "700 mL/min", "H2/N2 feed"
            else:
                temp, hold, carbon, flow, reductant = "700", "30", "waste polypropylene", "120 mL/min", "5 vol% H2/95 vol% Ar"
            procs.append(mkrow("reactor_process_gas", run_id=rid, process_stage_id=f"{rid}_S{order:02d}", stage_order=str(order), stage_type=stage, reactor_type="fixed-bed quartz tube" if source_id != "LIT_4C5" else "quartz thermobalance fixed-bed differential reactor", scale_level="lab_batch", reactor_material="quartz", reactor_size_summary="reported in linked process span", reactor_setup_summary="catalyst loaded in reactor; see process evidence", catalyst_loading_mass_g="1" if source_id in {"LIT_15F49C3012600D0B", "LIT_9B43B350883D2B6F"} else "0.025", temperature_setpoint_C=temp, temperature_program_summary=f"{temp} °C representative condition", holding_time_min=hold if stage != "cooling" else "", heating_rate_C_min="10" if source_id != "LIT_4C5EB40B8CD80C4F" else "10", cooling_condition="inert gas to room temperature" if stage == "cooling" else "", pressure_original="atmospheric" if source_id != "LIT_15F49C3012600D0B" else "", pressure_kPa="101.325" if source_id != "LIT_15F49C3012600D0B" else "", carbon_source=carbon if stage == "growth" else "", carbon_source_flow_original=flow if stage == "growth" else "", carbon_source_flow_sccm="700" if flow == "700 mL/min" else ("120" if flow == "120 mL/min" else ""), reducing_gas=reductant if stage == "activation" else "", reducing_gas_flow_original="not_reported", reducing_gas_flow_sccm="", inert_gas="N2" if stage == "cooling" else "", inert_gas_flow_original="", inert_gas_flow_sccm="", cofeed_or_reactive_gas="", cofeed_flow_original="", cofeed_flow_sccm="", total_flow_original=flow if stage in {"activation", "growth"} else "", total_flow_sccm="700" if flow == "700 mL/min" else ("120" if flow == "120 mL/min" else ""), gas_composition_summary="see linked source span", GHSV_or_residence_time="", process_note="Representative shared condition; needs_review."))
        ctype = "MWCNTs" if not source_id.startswith("LIT_4C5") else "CNTs; morphology varies with conditions"
        yqs.append(mkrow("yield_quality", run_id=rid, product_id=f"{rid}_PROD", primary_yield_metric="CNT carbon yield/productivity", yield_original=f"{y} {yunit}", yield_definition_original="Reported carbon/CNT yield or productivity; exact normalization retained in original expression.", yield_calculation_method="Reported source table/text", yield_value_standardized="", yield_unit_standardized=yunit, yield_standardization_note="No cross-unit conversion performed in first pass.", CNT_yield_per_catalyst_g_gcat="", CNT_productivity_g_gcat_h=y if "gC/gcat" in yunit else "", carbon_source_conversion_percent="", carbon_conversion_to_solid_percent="", secondary_result_summary=summary, CNT_type_reported=ctype, CNT_type_confirmed="not_applicable", product_mixture_summary="Carbon nanomaterial/CNT product; product selectivity may vary by condition.", CNT_type_evidence="Linked TEM/Raman/result evidence.", SWCNT_or_few_wall_evidence_summary="", RBM_peak_reported="", outer_diameter_mean_nm=dmean, outer_diameter_range_nm=drange, inner_diameter_mean_nm="", wall_number_summary=walls, length_summary="", morphology="", alignment_or_array="", Raman_ratio_type="IG/ID" if source_id.startswith("LIT_9B43") else "", Raman_ratio_value=("1.09" if code == "R01" and source_id.startswith("LIT_9B43") else ("1.08" if code == "R02" and source_id.startswith("LIT_9B43") else ("1.44" if code == "R03" and source_id.startswith("LIT_9B43") else ""))), Raman_laser_wavelength_nm="532" if source_id != "LIT_4C5EB40B8CD80C4F" else "488", TGA_carbon_content_wt_percent="", purified_product_purity_wt_percent="", purity_basis="", residue_summary="", amorphous_carbon_level="", BET_surface_area_product_m2_g="", characterization_methods="TEM; Raman; TGA/XRD where reported", post_treatment_or_purification="", purification_condition="", application_property_summary="", notes="Do not equate carbon deposition with purified CNT purity."))
        costs.append(mkrow("cost_scale_review", run_id=rid, scale_level_demonstrated="lab_batch", scale_level_claimed="not_reported", scale_evidence_summary="Laboratory catalyst experiment", reactor_capacity_or_throughput="not_reported", continuous_operation_time_h="", catalyst_lifetime_or_reuse="", catalyst_reuse_cycles="", batch_stability="", scale_up_issue="", quantitative_cost_reported="not_reported", quantitative_cost_summary="not_reported", cost_driver_summary="No quantitative cost calculation extracted.", safety_risk="Combustible gases/pyrolysis vapours; review needed", emission_or_waste="Waste plastic or methane feed; review needed", industrial_readiness_assessment="", reproduction_value="", reproduction_priority="", industrial_value_score="", recommended_next_action="", review_note="Automated first-pass; human review required."))
        evs.extend([ev(f"EVD_{rid}_CAT", rid, "catalyst_system", f"{rid}_CAT", "catalyst_label|active_metals|support_material|metal_ratio_original|preparation_method", cfg["prep"]), ev(f"EVD_{rid}_YIELD", rid, "yield_quality", f"{rid}_PROD", "record_level", cfg["result"]), ev(f"EVD_{rid}_COST", rid, "cost_scale_review", rid, "record_level", cfg["result"])])
        for order in (1, 2, 3):
            evs.append(ev(f"EVD_{rid}_PROC_S{order:02d}", rid, "reactor_process_gas", f"{rid}_S{order:02d}", "record_level", cfg["process"]))
        if dmean:
            evs.append(ev(f"EVD_{rid}_DIMS", rid, "yield_quality", f"{rid}_PROD", "outer_diameter_mean_nm|outer_diameter_range_nm|wall_number_summary", cfg["dims"]))
    issue_id = f"{source_id}_ISSUE_SCOPE_001"
    issues = [mkrow("review_issue_log", issue_id=issue_id, source_id=source_id, run_id=f"{source_id}_R01", issue_type="run_split_uncertainty", target_table="source_run", target_record_id=f"{source_id}_R01", target_field="record_level", issue_summary=cfg["issue"], conflicting_values="", evidence_ids=f"EVD_{source_id}_R01_YIELD", severity="medium", review_status="pending_human_review", reviewer="", reviewed_at="", resolution="", notes="Do not promote until human checks run split and evidence assignment.")]
    outdir.mkdir(parents=True, exist_ok=True)
    for table, vals in zip(TABLES, (master, runs, cats, procs, yqs, costs, evs, issues)):
        with (outdir / f"{table}.csv").open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers(table))
            writer.writeheader()
            writer.writerows(vals)
    metrics = {"source_id": source_id, "batch_id": "CODEX_MANUAL_5_20260716", "input_selected_chars": pkg["selection_stats"]["selected_text_chars"], "input_candidate_spans": len(pkg["spans"]), "estimated_input_tokens_chars_div_4": round(pkg["selection_stats"]["selected_text_chars"] / 4), "output_fact_rows": {"source_run": len(runs), "catalyst_system": len(cats), "reactor_process_gas": len(procs), "yield_quality": len(yqs), "cost_scale_review": len(costs), "evidence_index": len(evs), "review_issue_log": len(issues)}, "elapsed_generation_seconds": round(time.perf_counter() - started, 3), "status": "needs_review", "notes": "Input tokens are estimated selected chars/4; Codex internal generation-token telemetry is not exposed by desktop runtime."}
    (outdir / "codex_manual_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metrics

if __name__ == "__main__":
    all_metrics = [make_package(sid, cfg) for sid, cfg in SOURCES.items()]
    print(json.dumps(all_metrics, ensure_ascii=False))
