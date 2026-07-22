#!/usr/bin/env python3
"""Transcribe the PP/Fe-Mn-Al2O3 catalyst series as five physical runs."""

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
BATCH_NUMBER = 7
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
SOURCE_ID = "LIT_0C298FD36DDDBFF2"


def build_source(metadata: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    tables = {name: [] for name in TABLES}
    master = master_row(metadata, "Complete 0, 1, 5 and 10 wt% Mn/10 wt% Fe-Al2O3 series plus the 10 wt% Mn/no-Fe physical control.")
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{source_id}.parsed.json"
    master["notes"] = f"Manual first-pass transcription for {BATCH_NAME}; plotted TPO values are retained with their stated filamentous-carbon-as-CNT assumption."
    tables["source_master"].append(master)

    # code, Mn wt%, Fe wt%, filamentous yield, amorphous yield, CNT share,
    # fresh Fe2O3 crystallite, outer diameter, Raman ID/IG
    records = (
        ("10MN0FE", "10", "0", "0", "0", "0", "not_applicable", "not_reported", "not_reported"),
        ("0MN10FE", "0", "10", "23.41", "2.54", "90.2", "107.1", "15-60", "0.60"),
        ("1MN10FE", "1", "10", "23.05", "2.38", "90.6", "14.0", "15-60", "not_reported"),
        ("5MN10FE", "5", "10", "29.36", "3.62", "89.0", "8.4", "30-115", "not_reported"),
        ("10MN10FE", "10", "10", "32.89", "8.69", "79.1", "30.3", "30-115", "0.40"),
    )
    for code, mn, fe, filament, amorphous, share, crystallite, diameter, raman in records:
        run_id = f"{source_id}_{code}"
        total = float(filament) + float(amorphous)
        active = "Mn" if fe == "0" else "Fe" if mn == "0" else "Fe; Mn"
        summary = (
            f"2 g PP over 0.5 g {code}/Al2O3 in the two-stage reactor; "
            + ("no carbon deposition detected." if fe == "0" else f"{filament} wt% filamentous carbon (assumed CNT) and {amorphous} wt% amorphous carbon by TPO.")
        )
        tables["source_run"].append(run_row(source_id, code, code, summary))
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                catalyst_label=f"{mn} wt% Mn/{fe} wt% Fe on Al2O3",
                active_metals=active,
                support_material="Al2O3 powder, approximately 10 micrometre",
                metal_ratio_original=f"{mn} wt% Mn; {fe} wt% Fe",
                precursor_summary="Mn(NO3)2 hydrate and/or Fe(NO3)3·9H2O",
                preparation_method="wet impregnation",
                preparation_detail="Nitrates dissolved in 100 mL water, stirred 0.5 h; Al2O3 added and stirred about 1 h; water evaporated at 90 C.",
                drying_condition="105 C overnight",
                calcination_condition="500 C in air for 3 h; 10 C/min ramp",
                catalyst_particle_size_mean_nm=crystallite,
                catalyst_particle_size_qualifier=("fresh alpha-Fe2O3 XRD crystallite size; not a direct particle-size measurement" if fe != "0" else "not_applicable"),
            )
        )
        tables["reactor_process_gas"].extend((
            process_row(
                run_id, 1, "PP_pyrolysis",
                reactor_type="two-stage quartz-tube pyrolysis/catalysis system",
                reactor_setup_summary="2 g recycled PP pellet in first-stage aluminium boat.",
                temperature_setpoint_C="500", holding_time_min="about 60",
                heating_rate_C_min="10 from 200 to 500 C; initial 40 C/min to 200 C",
                carbon_source="recycled polypropylene", carbon_source_flow_original="2 g batch",
                inert_gas="N2", inert_gas_flow_original="100 mL/min", inert_gas_flow_sccm="100",
            ),
            process_row(
                run_id, 2, "catalytic_CNT_growth",
                reactor_type="two-stage quartz-tube pyrolysis/catalysis system",
                reactor_setup_summary="0.5 g catalyst on about 30 mg quartz wool in second stage; condensable vapour removed upstream.",
                catalyst_loading_mass_g="0.5", temperature_setpoint_C="800", holding_time_min="about 60",
                heating_rate_C_min="40", carbon_source="non-condensed PP pyrolysis vapour",
                inert_gas="N2", inert_gas_flow_original="100 mL/min", inert_gas_flow_sccm="100",
            ),
        ))
        if fe == "0":
            cnt_type, confirmed, mixture, yield_value, yield_def = (
                "not_reported", "not_applicable", "No carbon detected by TPO.", "0 wt% carbon", "No TPO weight loss; control inactive for carbon formation."
            )
        else:
            cnt_type, confirmed = "CNT", "CNT"
            mixture = f"{filament} wt% filamentous carbon and {amorphous} wt% amorphous carbon; filamentous share {share}%."
            yield_value = f"{filament} wt% filamentous carbon; {amorphous} wt% amorphous carbon; {total:.2f} wt% total carbon"
            yield_def = "TPO mass loss relative to reacted catalyst; carbon oxidizing above 600 C was classified as filamentous carbon and assumed to be CNT."
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="TPO-derived filamentous and amorphous carbon yield",
                yield_original=yield_value,
                yield_definition_original=yield_def,
                secondary_result_summary=("No carbon formed without Fe." if fe == "0" else f"CNT outer diameter {diameter} nm; tip-growth morphology; fresh-catalyst Fe2O3 crystallite {crystallite} nm."),
                product_mixture_summary=mixture,
                CNT_type_reported=cnt_type,
                CNT_type_confirmed=confirmed,
                CNT_type_evidence=("not_applicable" if fe == "0" else "TEM filamentous/tubular morphology with catalyst particles at CNT tips."),
                outer_diameter_range_nm=diameter,
                Raman_ratio_type="ID/IG" if raman != "not_reported" else "not_reported",
                Raman_ratio_value=raman,
                TGA_carbon_content_wt_percent=(f"{total:.2f}" if fe != "0" else "0"),
                morphology=("no carbon deposit" if fe == "0" else "filamentous CNTs with tip-located metal particles; Mn-dependent diameter and homogeneity"),
                characterization_methods="TPO/TGA; XRD; SEM; TEM; Raman",
            )
        )
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                scale_evidence_summary="Laboratory two-stage run using 2 g recycled PP and 0.5 g catalyst.",
                cost_driver_summary="Wet-impregnated Fe/Mn catalyst, two heated zones and nitrogen supply.",
                safety_risk="Hot plastic-pyrolysis vapours and nitrate-derived Fe/Mn catalyst powders.",
                emission_or_waste="Condensed PP products, non-condensed gas and carbon-containing spent catalyst; not quantitatively inventoried.",
            )
        )
        add_evidence(tables, store, source_id, run_id, "CATPREP", "catalyst_system", f"{run_id}_CAT", "record_level", "SPAN_ABCABAADA18CF02AAD66", "Catalyst wet-impregnation, drying and calcination.")
        if fe != "0":
            add_evidence(tables, store, source_id, run_id, "CATSIZE", "catalyst_system", f"{run_id}_CAT", "catalyst_particle_size_mean_nm;catalyst_particle_size_qualifier", "SPAN_23E99AB200807972A38A", "Fresh-catalyst Fe2O3 XRD crystallite-size series.")
        for order, suffix in ((1, "PYR"), (2, "GROWTH")):
            add_evidence(tables, store, source_id, run_id, suffix, "reactor_process_gas", f"{run_id}_S{order:02d}", "record_level", "SPAN_A87B445D47ECB9DA530C", "Two-stage PP pyrolysis and catalytic-growth conditions.")
        result_span = "SPAN_ACE0183BD17BE1E25857" if fe == "0" else "SPAN_10F204CCD1E8A178C1C5"
        add_evidence(tables, store, source_id, run_id, "YIELD", "yield_quality", f"{run_id}_PROD", "yield_original;yield_definition_original;product_mixture_summary;TGA_carbon_content_wt_percent", result_span, "TPO-derived carbon yields and phase shares.", value_status="calculated")
        if fe != "0":
            add_evidence(tables, store, source_id, run_id, "MORPH", "yield_quality", f"{run_id}_PROD", "secondary_result_summary;CNT_type_reported;CNT_type_confirmed;CNT_type_evidence;outer_diameter_range_nm;morphology", "SPAN_2861FDB57F7717E81315", "TEM CNT morphology and diameter ranges.")
            if raman != "not_reported":
                add_evidence(tables, store, source_id, run_id, "RAMAN", "yield_quality", f"{run_id}_PROD", "Raman_ratio_type;Raman_ratio_value", "SPAN_03213ECEA33FD21ED8C8", "Narrative Raman ID/IG endpoints.")
        add_evidence(tables, store, source_id, run_id, "SCALE", "cost_scale_review", run_id, "record_level", "SPAN_A87B445D47ECB9DA530C", "Laboratory feed and catalyst quantities.")
        tables["review_issue_log"].append(issue_row(
            f"{source_id}_ISSUE_{code}_001", source_id, run_id, "yield_basis", "yield_quality", f"{run_id}_PROD", "yield_original",
            "The source assumes carbon oxidizing above 600 C is CNT; preserve this classification without treating it as purified CNT mass.", f"EVD_{run_id}_YIELD", "medium",
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
    (REPORT_ROOT / "manual_batch_007_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
