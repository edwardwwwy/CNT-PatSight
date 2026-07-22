#!/usr/bin/env python3
"""Transcribe the seventeenth five-paper B-class batch."""
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
BATCH_NUMBER = 25
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
PACKAGE_ROOT = ROOT / "data/interim/extraction/B"
SOURCE_IDS = (
    "LIT_E9BE1E06A502226C", "LIT_E9E787428CFD3649",
    "LIT_EC90CFDB47F2377F", "LIT_ED1D628BC55C93F4",
    "LIT_F27CA92832125F8A",
)


def base(meta, scope):
    tables = {name: [] for name in TABLES}
    item = master_row(meta, scope)
    item["local_file_path"] = f"data/interim/parsed_text/by_source/{meta['source_id']}.parsed.json"
    item["notes"] = f"Source-specific transcription for {BATCH_NAME}."
    tables["source_master"].append(item)
    return tables


def evidence(tables, store, sid, rid, cat_span, proc_span, product_span, scale_span=None):
    add_evidence(tables, store, sid, rid, "CAT", "catalyst_system", f"{rid}_CAT", "record_level", cat_span, "Catalyst and substrate evidence.")
    add_evidence(tables, store, sid, rid, "PROC", "reactor_process_gas", f"{rid}_S01", "record_level", proc_span, "Process-condition evidence.")
    add_evidence(tables, store, sid, rid, "PROD", "yield_quality", f"{rid}_PROD", "record_level", product_span, "Product and quality evidence.")
    add_evidence(tables, store, sid, rid, "SCALE", "cost_scale_review", rid, "record_level", scale_span or proc_span, "Scale, cost, safety, or waste basis.", confidence="medium", value_status="review_assessment")


def build_desktop(meta, store):
    sid = meta["source_id"]
    tables = base(meta, "Three annealing-time demonstrations in an automated desktop atmospheric-pressure CVD system.")
    outcomes = {
        5: "densest and best-aligned CNT forest among the three annealing times",
        10: "intermediate CNT forest density/alignment",
        20: "lower-density and less-aligned CNT forest than shorter annealing times",
    }
    for minutes, outcome in outcomes.items():
        rid = f"{sid}_A{minutes}"
        tables["source_run"].append(run_row(sid, f"A{minutes}", f"desktop CVD, {minutes} min catalyst anneal", outcome))
        tables["catalyst_system"].append(catalyst_row(
            rid, catalyst_label="1 nm Fe on 10 nm Al2O3", active_metals="Fe",
            support_material="10 nm Al2O3 on 300 nm SiO2/Si",
            metal_ratio_original="Fe 1 nm; Al2O3 10 nm",
            preparation_method="thin-film deposition followed by H2 annealing",
            preparation_detail=f"Catalyst annealing time varied to {minutes} min before C2H4 growth.",
        ))
        tables["reactor_process_gas"].append(process_row(
            rid, 1, "APCVD", reactor_type="automated desktop 1-inch tube furnace",
            temperature_setpoint_C="approximately 800", holding_time_min=str(minutes),
            carbon_source="C2H4", cofeed_or_reactive_gas="H2",
            inert_gas="Ar", process_note="Ar purge; Ar/H2 heat-up and catalyst anneal; C2H4 growth; Ar cool-down. Exact standard-recipe gas flows and growth time are figure-only in the parsed source.",
        ))
        tables["yield_quality"].append(yield_row(
            rid, primary_yield_metric="CNT forest density and alignment",
            yield_original=outcome, yield_definition_original="SEM comparison; no mass yield",
            secondary_result_summary="Average CNT diameter about 10 nm; interspacing on the order of tens to hundreds of nanometres; forest height controllable up to millimetre scale.",
            CNT_type_reported="carbon nanotube forest", CNT_type_confirmed="CNT forest",
            product_mixture_summary="as-grown patterned CNT forest", CNT_type_evidence="SEM",
            outer_diameter_mean_nm="approximately 10", alignment_or_array="vertically aligned forest",
            characterization_methods="SEM; optical photography",
        ))
        tables["cost_scale_review"].append(cost_row(
            rid, scale_level_demonstrated="desktop laboratory CVD",
            scale_level_claimed="compact programmable CNT growth platform",
            scale_evidence_summary="System volume reported as about 15% of a commercial CVD system.",
            quantitative_cost_reported="yes",
            quantitative_cost_summary="Approximate build cost US$12,500 versus about US$55,000 commercial system; authors report 78% saving.",
            cost_driver_summary="tube furnace, four MFC channels, controls and LabVIEW automation",
            safety_risk="C2H4/H2 flammable gases, hot furnace and CNT exposure",
            emission_or_waste="hydrocarbon/H2 exhaust and spent catalyst-coated wafers",
        ))
        evidence(tables, store, sid, rid, "SPAN_0677BA784C53BAE60718", "SPAN_0579BE504BBA55BED208", "SPAN_3EBCA6A65B047601C347", "SPAN_AFA15D04709F57AA24B3")
    tables["review_issue_log"].append(issue_row(
        f"{sid}_ISSUE_FIGURE", sid, f"{sid}_A5", "figure_only_value",
        "reactor_process_gas", f"{sid}_A5_S01", "process_note",
        "Exact standard-recipe flow rates and growth duration are embedded in a figure and were not transcribed from the parsed text.",
        f"EVD_{sid}_A5_PROC", "medium",
    ))
    return tables


def build_metal_review(meta, store):
    sid = meta["source_id"]
    tables = base(meta, "Review of CNT-forest growth on flexible metal substrates; literature synthesis is represented without fabricating an author experiment.")
    rid = f"{sid}_REVIEW"
    item = run_row(sid, "REVIEW", "flexible-metal-substrate CNT-forest review", "Reviews barriers, catalysts, pretreatments, CVD routes, scale-up challenges and applications.", "high")
    item["data_type"] = "literature_review"
    tables["source_run"].append(item)
    tables["catalyst_system"].append(catalyst_row(
        rid, catalyst_label="reviewed Fe/Co/Ni and catalyst-free metal-substrate systems",
        active_metals="Fe; Co; Ni; substrate-derived metals", support_material="flexible metal foils and meshes with oxide/diffusion barriers",
        preparation_method="literature_review", preparation_detail="Review covers deposited catalyst stacks and substrate pretreatments including oxidation/reduction, plasma, polishing and related routes.",
    ))
    tables["reactor_process_gas"].append(process_row(
        rid, 1, "literature_review", reactor_type="reviewed thermal and plasma CVD configurations",
        temperature_setpoint_C="multiple literature conditions", carbon_source="multiple literature carbon sources",
        process_note="No single author-performed CNT growth run is reported by this review.",
    ))
    tables["yield_quality"].append(yield_row(
        rid, primary_yield_metric="review conclusions", yield_original="substrate pretreatment generally improves carbon yield, uniformity and growth efficiency",
        yield_definition_original="literature synthesis rather than author measurement",
        secondary_result_summary="Thicker and more uniform barriers are often required on rough metal substrates to suppress interdiffusion and catalyst poisoning.",
        CNT_type_reported="vertically aligned carbon nanotube forests", CNT_type_confirmed="review_only",
        product_mixture_summary="not_applicable", CNT_type_evidence="reviewed literature", characterization_methods="literature review",
        application_property_summary="flexible, conductive and scalable metal-supported CNT forest applications",
    ))
    tables["cost_scale_review"].append(cost_row(
        rid, scale_level_demonstrated="review", scale_level_claimed="scalable flexible-substrate manufacturing",
        scale_evidence_summary="Review evaluates flexible metal substrates and manufacturing challenges.",
        cost_driver_summary="barrier/catalyst deposition, metal pretreatment, thermal budget and continuous processing",
        safety_risk="route-dependent high temperature, reactive gases, metal catalysts and CNT exposure",
        emission_or_waste="route-dependent CVD exhaust and metal/catalyst process waste",
    ))
    evidence(tables, store, sid, rid, "SPAN_00574F8FD00BA0FC2835", "SPAN_C0E835C3F837E3EBF227", "SPAN_6A747C78847502130A39", "SPAN_2FD69F9B3DB6B1803EBD")
    tables["review_issue_log"].append(issue_row(
        f"{sid}_ISSUE_SCOPE", sid, rid, "source_scope", "source_run", rid, "data_type",
        "Review article: conditions and outcomes aggregate cited studies and are not an author experimental run.", f"EVD_{rid}_PROC", "high",
    ))
    return tables


def build_waste_plastic(meta, store):
    sid = meta["source_id"]
    tables = base(meta, "Four conditioning-catalyst loadings in two-stage HDPE pyrolysis/CVD using a common Ni/AAO template catalyst.")
    for amount, carbon_yield, outcome in (
        (0.0, "4", "lowest carbon deposition and broadest CNT diameter distribution"),
        (0.2, "not_reported", "conditioning catalyst increased CNT carbon deposition and improved diameter uniformity"),
        (0.5, "not_reported", "further increase in CNT carbon deposition and diameter uniformity"),
        (1.0, "9", "highest carbon deposition and most uniform CNT diameter distribution"),
    ):
        code = str(amount).replace(".", "P")
        rid = f"{sid}_COND{code}G"
        tables["source_run"].append(run_row(sid, f"COND{code}G", f"{amount:g} g conditioning catalyst", outcome))
        tables["catalyst_system"].append(catalyst_row(
            rid, catalyst_label="Ni/AAO template catalyst plus Ni/Al2O3 conditioning catalyst",
            active_metals="Ni", support_material="anodic aluminium oxide (AAO) growth template; Al2O3 conditioning support",
            metal_ratio_original="10 wt% Ni on Al2O3 conditioning catalyst; Ni/AAO prepared from 0.1 M Ni nitrate",
            precursor_summary="Ni(NO3)2 aqueous impregnation",
            preparation_method="wet impregnation, drying and calcination",
            preparation_detail=f"Ni/AAO dried 100 C for 24 h and calcined 700 C at 10 C/min for 3 h; conditioning catalyst charge {amount:g} g.",
        ))
        tables["reactor_process_gas"].append(process_row(
            rid, 1, "two_stage_pyrolysis_CVD", reactor_type="two-stage fixed-bed reactor",
            temperature_setpoint_C="500 pyrolysis; 700 catalytic CNT stage", carbon_source="2 mm waste HDPE particles",
            inert_gas="N2", inert_gas_flow_original="100 mL/min", inert_gas_flow_sccm="100",
            process_note="HDPE pyrolysis vapour passes through the Ni/Al2O3 conditioning catalyst and then the Ni/AAO template catalyst.",
        ))
        tables["yield_quality"].append(yield_row(
            rid, primary_yield_metric="TGA carbon deposition on catalyst",
            yield_original=(f"{carbon_yield} wt% carbon" if carbon_yield != "not_reported" else "intermediate value shown graphically but not text-reported"),
            yield_value_standardized=carbon_yield,
            yield_unit_standardized=("wt.% carbon per recovered catalyst/product" if carbon_yield != "not_reported" else "not_reported"),
            yield_definition_original="TGA weight loss attributed to deposited carbon",
            secondary_result_summary=outcome, CNT_type_reported="carbon nanotubes", CNT_type_confirmed="CNT",
            product_mixture_summary="CNT/carbon deposited on Ni/AAO", CNT_type_evidence="SEM, TEM and TGA",
            morphology="template-directed nanotubes with loading-dependent diameter uniformity",
            characterization_methods="SEM; TEM; TGA; XRD",
        ))
        tables["cost_scale_review"].append(cost_row(
            rid, scale_level_demonstrated="laboratory two-stage batch",
            scale_level_claimed="waste-plastic valorisation",
            scale_evidence_summary="Waste HDPE converted in a two-stage reactor with template and conditioning catalysts.",
            cost_driver_summary="AAO template, Ni catalysts, two heated stages and inert gas",
            safety_risk="flammable pyrolysis vapours, hot reactor, Ni compounds and CNT exposure",
            emission_or_waste="plastic pyrolysis off-gas and spent Ni/AAO/Ni-Al2O3 solids",
        ))
        evidence(tables, store, sid, rid, "SPAN_793E1118A7099595DEDB", "SPAN_95221B14CFF4922B9C60", "SPAN_587B67C9130A026396C4", "SPAN_C27FCD4A492C8DCE5D14")
        if carbon_yield == "not_reported":
            tables["review_issue_log"].append(issue_row(
                f"{rid}_ISSUE_YIELD", sid, rid, "figure_only_value", "yield_quality", f"{rid}_PROD", "yield_value_standardized",
                "Intermediate TGA carbon yield is plotted but not explicitly stated in parsed text; no value interpolated.", f"EVD_{rid}_PROD", "medium",
            ))
    return tables


def build_ru_hfcvd(meta, store):
    sid = meta["source_id"]
    tables = base(meta, "Three substrate temperatures in hot-filament CVD from a Ru-porphyrin self-assembled catalyst system.")
    for temp, outcome, ratio in (
        (800, "weak/limited SWCNT growth relative to higher temperatures", "not_reported"),
        (900, "dense high-quality SWCNT growth", "<0.09"),
        (1000, "straighter and more aligned SWCNTs but greater disorder and larger diameters", "approximately 0.2"),
    ):
        rid = f"{sid}_T{temp}"
        tables["source_run"].append(run_row(sid, f"T{temp}", f"Ru-SAM HFCVD at {temp} C", outcome))
        tables["catalyst_system"].append(catalyst_row(
            rid, catalyst_label="Ru tetraphenylporphyrin self-assembled monolayer catalyst",
            active_metals="Ru", support_material="pyridine-functionalized silicon oxide",
            precursor_summary="RuTPP immobilized on a pyridine-terminated silane SAM",
            preparation_method="molecular self-assembly", preparation_detail="Silane SAM thickness about 1.2 nm; Ru porphyrin coordinated to the functionalized surface.",
            phase_or_state_summary="surface-bound molecular Ru catalyst precursor",
        ))
        tables["reactor_process_gas"].append(process_row(
            rid, 1, "HFCVD", reactor_type="dual tungsten-filament hot-filament CVD",
            temperature_setpoint_C=str(temp), holding_time_min="30", pressure_original="90 mbar", pressure_kPa="9",
            carbon_source="CH4", gas_composition_summary="CH4 relative concentration 10% in H2",
            cofeed_or_reactive_gas="H2", process_note="H2 activation 5 min; H filament about 1900 C at 160 W. CH4 filament about 1700 C at 120 W during 30 min growth.",
        ))
        tables["yield_quality"].append(yield_row(
            rid, primary_yield_metric="SWCNT surface growth and Raman disorder ratio",
            yield_original=f"{outcome}; Raman ID/IG {ratio}", yield_definition_original="microscopy/Raman comparison; no mass yield",
            secondary_result_summary=outcome, CNT_type_reported="single-walled carbon nanotubes", CNT_type_confirmed="SWCNT",
            product_mixture_summary="surface-grown SWCNTs", CNT_type_evidence="Raman RBM/G-band and microscopy",
            alignment_or_array=("increased straightness/alignment" if temp == 1000 else "surface network"),
            characterization_methods="AFM; SEM; Raman spectroscopy; ellipsometry",
        ))
        tables["cost_scale_review"].append(cost_row(
            rid, scale_level_demonstrated="laboratory substrate growth",
            scale_evidence_summary="Molecular-catalyst HFCVD on functionalized oxide substrates.",
            cost_driver_summary="surface functionalization, Ru porphyrin, tungsten filaments and high substrate temperature",
            safety_risk="hydrogen/methane, hot filaments, Ru compounds and CNT exposure",
            emission_or_waste="CH4/H2 exhaust and Ru/silane-bearing substrate-processing waste",
        ))
        evidence(tables, store, sid, rid, "SPAN_026DE49B573C0425026F", "SPAN_A7E55265313387858970", "SPAN_151378D6306543221A0B")
    return tables


def build_cf_filaments(meta, store):
    sid = meta["source_id"]
    tables = base(meta, "Three CF-cloth CCVD conditions separating ferrocene-precoated filament growth from direct CNT growth.")
    cases = (
        ("COAT1H", True, 60, "straight MWCNT filaments, 15-25 micrometres diameter and >200 micrometres length"),
        ("COAT2H", True, 120, "coiled/helical MWCNT filaments with similar 15-25 micrometre diameter"),
        ("RAW2H", False, 120, "MWCNT coverage without filament formation"),
    )
    for code, coated, duration, outcome in cases:
        rid = f"{sid}_{code}"
        tables["source_run"].append(run_row(sid, code, f"{'ferrocene-coated' if coated else 'as-received'} CF cloth, {duration // 60} h", outcome))
        tables["catalyst_system"].append(catalyst_row(
            rid, catalyst_label="ferrocene-derived Fe particles",
            active_metals="Fe", support_material="2-D woven carbon-fibre cloth",
            metal_ratio_original="8 wt% ferrocene/toluene pre-soak" if coated else "no catalyst pre-coating",
            precursor_summary="ferrocene in toluene; injected solution concentration 0.077 g/mL",
            preparation_method="solution pre-soak and in-situ ferrocene injection" if coated else "in-situ ferrocene injection only",
            preparation_detail="Pre-soaked cloth dried under vacuum at 80 C for 4 h before growth." if coated else "As-received cloth placed directly in reactor.",
        ))
        tables["reactor_process_gas"].append(process_row(
            rid, 1, "CCVD", reactor_type="horizontal furnace catalytic CVD",
            temperature_setpoint_C="750", holding_time_min=str(duration), carbon_source="toluene",
            gas_composition_summary="ferrocene/toluene solution, 0.077 g/mL, vaporized at 200 C",
            inert_gas="Ar", process_note="Ar carries vaporized ferrocene-toluene into the 750 C reaction zone.",
        ))
        tables["yield_quality"].append(yield_row(
            rid, primary_yield_metric="MWCNT filament morphology", yield_original=outcome,
            yield_definition_original="SEM/TEM morphology; no mass yield",
            secondary_result_summary=outcome, CNT_type_reported="multiwalled carbon nanotubes", CNT_type_confirmed="MWCNT",
            product_mixture_summary="dense MWCNTs with a few growth catalyst particles",
            CNT_type_evidence="TEM-resolved multiwalled structure", morphology=outcome,
            alignment_or_array="macroscopic filament assembly" if coated else "CNT coating without filaments",
            characterization_methods="optical microscopy; SEM; TEM",
        ))
        tables["cost_scale_review"].append(cost_row(
            rid, scale_level_demonstrated="laboratory carbon-cloth coupon",
            scale_level_claimed="reinforcement architecture for CNT-polymer composites",
            scale_evidence_summary="Direct growth on woven carbon-fibre cloth; one-hour coated route sufficient for straight filaments.",
            cost_driver_summary="carbon cloth, ferrocene/toluene feed, furnace heat and inert gas",
            safety_risk="flammable/toxic toluene, ferrocene aerosol, hot furnace and CNT exposure",
            emission_or_waste="organic/CVD exhaust and Fe-containing carbon-cloth residues",
        ))
        evidence(tables, store, sid, rid, "SPAN_1DCFB53E509025DCB2BA", "SPAN_8C197DBBF233D60135BA", "SPAN_052F2B74E5C2A96937C3", "SPAN_4D795EE4DE006E5F6539")
    return tables


BUILDERS: dict[str, Callable] = {
    "LIT_E9BE1E06A502226C": build_desktop,
    "LIT_E9E787428CFD3649": build_metal_review,
    "LIT_EC90CFDB47F2377F": build_waste_plastic,
    "LIT_ED1D628BC55C93F4": build_ru_hfcvd,
    "LIT_F27CA92832125F8A": build_cf_filaments,
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
    (REPORT_ROOT / "manual_batch_025_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
