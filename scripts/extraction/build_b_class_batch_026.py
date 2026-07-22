#!/usr/bin/env python3
"""Transcribe the final two-paper B-class candidate batch."""
from __future__ import annotations

import json
from typing import Callable

from scripts.extraction.batch_common import (
    ROOT, TABLES, EvidenceStore, catalyst_row, cost_row, issue_row,
    load_metadata, master_row, process_row, run_row, yield_row,
)
from scripts.extraction.build_b_class_batch_001 import add_evidence, publish_package
from scripts.extraction.package_io import existing_package_metric

BATCH_ID = "B_CLASS_371_20260719"
REPORT_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
BATCH_NUMBER = 26
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
PACKAGE_ROOT = ROOT / "data/interim/extraction/B"
SOURCE_IDS = ("LIT_F2D0EAEF6124778C", "LIT_F5C87E84F498DD3B")


def base(meta, scope):
    tables = {name: [] for name in TABLES}
    item = master_row(meta, scope)
    item["local_file_path"] = f"data/interim/parsed_text/by_source/{meta['source_id']}.parsed.json"
    item["notes"] = f"Source-specific transcription for {BATCH_NAME}."
    tables["source_master"].append(item)
    return tables


def evidence(tables, store, sid, rid, cat_span, proc_span, product_span, scale_span=None):
    add_evidence(tables, store, sid, rid, "CAT", "catalyst_system", f"{rid}_CAT", "record_level", cat_span, "Catalyst/support evidence.")
    add_evidence(tables, store, sid, rid, "PROC", "reactor_process_gas", f"{rid}_S01", "record_level", proc_span, "Process-condition evidence.")
    add_evidence(tables, store, sid, rid, "PROD", "yield_quality", f"{rid}_PROD", "record_level", product_span, "Product and performance evidence.")
    add_evidence(tables, store, sid, rid, "SCALE", "cost_scale_review", rid, "record_level", scale_span or proc_span, "Scale/safety basis.", confidence="medium", value_status="review_assessment")


def build_plasma_review(meta, store):
    sid = meta["source_id"]
    tables = base(meta, "Review of plasma-assisted CNT synthesis and modification; represented as literature synthesis, not an author experiment.")
    rid = f"{sid}_REVIEW"
    item = run_row(sid, "REVIEW", "PECVD CNT synthesis review", "Reviews low-temperature synthesis, ion bombardment, plasma-sheath alignment and plasma modification of CNTs.", "high")
    item["data_type"] = "literature_review"
    tables["source_run"].append(item)
    tables["catalyst_system"].append(catalyst_row(
        rid, catalyst_label="reviewed transition-metal nanoparticle catalysts",
        active_metals="Fe; Co; Ni and combinations", support_material="conductive and insulating substrates; multiple literature supports",
        preparation_method="literature_review", preparation_detail="Review compares catalyst-support design across reported PECVD routes.",
        deactivation_summary="catalyst poisoning and amorphous-carbon formation identified as growth-termination mechanisms",
    ))
    tables["reactor_process_gas"].append(process_row(
        rid, 1, "literature_review", reactor_type="reviewed DC, RF and microwave PECVD reactors",
        temperature_setpoint_C="multiple literature conditions, including approximately 400-500 C low-temperature regimes",
        carbon_source="multiple hydrocarbon feeds", cofeed_or_reactive_gas="H2 and/or NH3 in reviewed routes",
        process_note="Review discusses plasma power, sheath voltage, pressure, ion flux, electric/magnetic fields and CNT modification; no unique author growth recipe.",
    ))
    tables["yield_quality"].append(yield_row(
        rid, primary_yield_metric="review conclusions", yield_original="PECVD enables free-standing individual vertically aligned CNTs and lower-temperature growth, with crystallinity/ion-damage trade-offs",
        yield_definition_original="literature synthesis; no author mass yield",
        secondary_result_summary="Minimizing ion bombardment through sheath-voltage and pressure control is important for high-quality SWCNT growth.",
        CNT_type_reported="SWCNT, MWCNT and carbon nanofibres", CNT_type_confirmed="review_only",
        product_mixture_summary="not_applicable", CNT_type_evidence="reviewed Raman/TEM literature",
        alignment_or_array="plasma-sheath-guided vertical or field-directed growth",
        characterization_methods="literature review and plasma modelling",
        application_property_summary="microelectronics integration, field emitters, sensors, composites and hybrid materials",
    ))
    tables["cost_scale_review"].append(cost_row(
        rid, scale_level_demonstrated="review", scale_level_claimed="microelectronics-compatible and potentially scalable PECVD",
        scale_evidence_summary="Review notes compatibility with established integrated-circuit plasma-processing infrastructure.",
        cost_driver_summary="vacuum/plasma reactor, power supply, catalyst preparation and thermal budget",
        safety_risk="plasma/high voltage, flammable/reactive gases, metal nanoparticles and CNT exposure",
        emission_or_waste="hydrocarbon/ammonia plasma exhaust and catalyst-bearing substrates",
    ))
    evidence(tables, store, sid, rid, "SPAN_664961CBF2F173AB0456", "SPAN_FF7DD871099CC112082E", "SPAN_2FE1367496D551511FC7", "SPAN_5446A008C850DF0470A0")
    tables["review_issue_log"].append(issue_row(
        f"{sid}_ISSUE_SCOPE", sid, rid, "source_scope", "source_run", rid, "data_type",
        "Review article; tabulated recipes and outcomes belong to cited studies and are not author-performed runs.", f"EVD_{rid}_PROC", "high",
    ))
    return tables


def build_hfcvd_supports(meta, store):
    sid = meta["source_id"]
    tables = base(meta, "Five support/catalyst-stack HFCVD experiments transcribed from Table 1, with matching field-emission data retained where reported.")
    cases = (
        ("SI", "Fe 3 nm", "Si(100) with native ~2 nm oxide", "no Al buffer", 500, 750, "180-200", "20-22", "Bare-Si FE table separately uses Fe 1 nm: 0.67 V/um turn-on, 1.52 V/um for 1 mA, beta 3976."),
        ("ALSI", "Fe 3 nm", "Al 10 nm / Si(100)", "Al 10 nm", 500, 750, "850-1150", "95-125", "0.57 V/um turn-on, 1.46 V/um for 1 mA, field enhancement 4635."),
        ("ALSS", "Fe 4 nm", "Al 30 nm / stainless steel", "Al 30 nm", 450, 700, "95-120", "10-13", "0.65 V/um turn-on, 1.61 V/um for 1 mA, field enhancement 3852."),
        ("ALTI", "Fe 4 nm", "Al 40 nm / titanium", "Al 40 nm", 450, 700, "85-120", "9-13", "Field-emission value not separately listed in Table 2."),
        ("ALCU", "Fe 4 nm", "Al 50 nm / copper", "Al 50 nm", 450, 700, "105-150", "11-16", "Field-emission value not separately listed in Table 2."),
    )
    for code, fe, support, barrier, pretreat, growth_temp, length, rate, fe_result in cases:
        rid = f"{sid}_{code}"
        outcome = f"VACNT length {length} um; growth rate {rate} um/min. {fe_result}"
        tables["source_run"].append(run_row(sid, code, f"{fe} on {support}", outcome))
        tables["catalyst_system"].append(catalyst_row(
            rid, catalyst_label=f"{fe} / {barrier}", active_metals="Fe", support_material=support,
            metal_ratio_original=f"{fe}; {barrier}", preparation_method="sequential Ar sputtering followed by air annealing",
            preparation_detail=f"Metal foil, where applicable, ultrasonically cleaned in acetone and isopropanol for 15 min each; catalyst stack annealed in air at {pretreat} C for 10 min.",
            calcination_condition=f"air, {pretreat} C, 10 min", catalyst_particle_size_range_nm="approximately 10-20 for optimized Fe/Al/Si stack",
            phase_or_state_summary="air-annealed high-density Fe nanoparticles; Al acts as diffusion barrier/support",
        ))
        tables["reactor_process_gas"].append(process_row(
            rid, 1, "HFCVD", reactor_type="hot-filament CVD with tungsten filaments",
            reactor_setup_summary="substrate rapidly inserted about 17 mm beneath tungsten filament",
            temperature_setpoint_C=str(growth_temp), holding_time_min="9", pressure_original="30 Torr", pressure_kPa="3.9997",
            carbon_source="CH4", carbon_source_flow_original="20 sccm", carbon_source_flow_sccm="20",
            reducing_gas="H2", reducing_gas_flow_original="30 sccm", reducing_gas_flow_sccm="30",
            total_flow_original="50 sccm", total_flow_sccm="50",
            temperature_program_summary=f"tungsten filament 2200-2500 C; substrate growth maintained near {growth_temp} C",
            process_note="Common 9 min HFCVD run using 30 Torr CH4/H2 feed.",
        ))
        tables["yield_quality"].append(yield_row(
            rid, primary_yield_metric="VACNT length and effective growth rate", yield_original=f"{length} um length; {rate} um/min",
            yield_definition_original="Table 1 cross-sectional SEM length divided by 9 min growth time",
            secondary_result_summary=fe_result, CNT_type_reported="vertically aligned carbon nanotubes", CNT_type_confirmed="multiwall VACNT",
            product_mixture_summary="as-grown high-purity VACNT carpet; quantitative purity not shown",
            CNT_type_evidence="SEM; TGA and Raman stated, data not shown", outer_diameter_mean_nm="approximately 15",
            outer_diameter_range_nm="approximately 12-18", morphology="dense vertically aligned forest",
            alignment_or_array="vertically aligned array", characterization_methods="SEM; TGA; Raman; field-emission I-V/Fowler-Nordheim analysis",
            application_property_summary=fe_result,
        ))
        tables["cost_scale_review"].append(cost_row(
            rid, scale_level_demonstrated="laboratory substrate/cathode",
            scale_level_claimed="field-electron-emitter support architecture",
            scale_evidence_summary="VACNT cathodes with 2 mm diameter were repeatedly field-emission tested.",
            cost_driver_summary="sputtered Fe/Al films, foil/substrate preparation, tungsten-filament power and vacuum gases",
            safety_risk="CH4/H2, 2200-2500 C filament, vacuum/high voltage, metal nanoparticles and CNT exposure",
            emission_or_waste="CVD exhaust, solvent cleaning waste and Fe/Al-coated substrates",
        ))
        evidence(tables, store, sid, rid, "SPAN_7116B0244AB341667006", "SPAN_0C5909F89EA471ED4D96", "SPAN_19D41F1BBD0E64F24107", "SPAN_52E7AB9F42AECE928B14")
    tables["review_issue_log"].append(issue_row(
        f"{sid}_ISSUE_SI_FE", sid, f"{sid}_SI", "condition_mismatch", "yield_quality", f"{sid}_SI_PROD", "application_property_summary",
        "Table 1 uses Fe 3 nm/Si for growth, while Table 2 field-emission data use Fe 1 nm/Si; values are retained as a separately labelled comparison rather than asserted as the same run.",
        f"EVD_{sid}_SI_PROD", "high",
    ))
    tables["review_issue_log"].append(issue_row(
        f"{sid}_ISSUE_TI_LENGTH", sid, f"{sid}_ALTI", "source_internal_conflict", "yield_quality", f"{sid}_ALTI_PROD", "yield_original",
        "Table 1 reports 85-120 um for Fe 4 nm/Al 40 nm/Ti, while the conclusion states about 180 um; Table 1 values are used and the conflict is flagged.",
        f"EVD_{sid}_ALTI_PROD", "high",
    ))
    return tables


BUILDERS: dict[str, Callable] = {
    "LIT_F2D0EAEF6124778C": build_plasma_review,
    "LIT_F5C87E84F498DD3B": build_hfcvd_supports,
}


def main():
    metadata = load_metadata("B")
    store = EvidenceStore()
    metrics = []
    try:
        for sid in SOURCE_IDS:
            metric = existing_package_metric(sid, "B")
            if metric is None:
                metrics.append(publish_package(sid, BUILDERS[sid](metadata[sid], store)))
            else:
                metrics.append(metric)
    finally:
        store.close()
    result = {"batch_id": BATCH_NAME, "sources": metrics, "total_runs": sum(x["row_counts"]["source_run"] for x in metrics), "status": "completed_needs_review"}
    (REPORT_ROOT / "manual_batch_026_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
