#!/usr/bin/env python3
"""Transcribe four ferrocene/ruthenocene floating-CVD CNT materials."""

from __future__ import annotations

import json
from typing import Any

from scripts.extraction.batch_common import ROOT, TABLES, EvidenceStore, catalyst_row, cost_row, issue_row, load_metadata, master_row, process_row, run_row, yield_row
from scripts.extraction.build_b_class_batch_001 import add_evidence, publish_package

BATCH_ID = "B_CLASS_371_20260719"
REPORT_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
BATCH_NUMBER = 8
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
SOURCE_ID = "LIT_1D9479E2BC5CDCEF"


def build_source(metadata: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    tables = {name: [] for name in TABLES}
    master = master_row(metadata, "Fe@CNT, Fe@NCNT and two directly Ru/Fe-co-doped NCNT floating-CVD syntheses; post-synthesis Ru impregnation and methanation tests are outside the CNT-production run set.")
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{source_id}.parsed.json"
    master["notes"] = f"Manual first-pass CNT-production transcription for {BATCH_NAME}."
    tables["source_master"].append(master)
    records = (
        ("FECNT", "Fe@CNT", "1.0 g ferrocene", "toluene", "Fe", "CNT", "not_reported", "0.19", "ordered CNT bundles"),
        ("FENCNT", "Fe@NCNT", "1.0 g ferrocene", "acetonitrile", "Fe", "nitrogen-doped CNT", "about 1.5 g raw product per 40 mL injection", "0.90", "highly aligned nitrogen-doped CNT bundles"),
        ("RUFE_005_095", "Ru,Fe@NCNT-0.05/0.95", "0.05 g ruthenocene plus 0.95 g ferrocene", "acetonitrile", "Ru; Fe", "Ru/Fe-decorated nitrogen-doped CNT", "not_reported", "not_reported", "highly aligned tight-packed bundles, indistinguishable from Fe@NCNT by SEM"),
        ("RUFE_020_100", "Ru,Fe@NCNT-0.2/1.0", "0.20 g ruthenocene plus 1.0 g ferrocene", "acetonitrile", "Ru; Fe", "Ru/Fe-decorated nitrogen-doped CNT", "not_reported", "1.02", "less-aligned, curled nanotubes with large Ru-Fe nanoparticles disrupting growth"),
    )
    for code, label, precursor, solvent, metals, cnt_type, raw_yield, raman, morphology in records:
        run_id = f"{source_id}_{code}"
        summary = f"Floating CVD at 790 C for 4 h from {precursor} in {solvent}; {morphology}."
        tables["source_run"].append(run_row(source_id, code, label, summary))
        tables["catalyst_system"].append(catalyst_row(
            run_id, catalyst_label=f"in-situ {metals.replace('; ', '/')}-nanoparticle CNT-growth catalyst", active_metals=metals,
            support_material="unsupported floating catalyst; particles become embedded in CNT walls", metal_ratio_original=precursor,
            precursor_summary=precursor, preparation_method="in-situ organometallic precursor decomposition",
            preparation_detail=f"Organometallic precursor dissolved in 50 mL {solvent}; precursor solution fed directly into the CVD reactor.",
            activation_condition="decomposition under flowing H2 during CVD", post_preparation_condition="catalyst particles retained in/as-grown CNT product",
        ))
        tables["reactor_process_gas"].append(process_row(
            run_id, 1, "floating_catalyst_CVD", reactor_type="25 mm ID x 28 mm OD x 122 cm quartz tube in tubular furnace",
            reactor_setup_summary=f"40 mL {solvent} precursor solution injected at 10 mL/h.", temperature_setpoint_C="790", holding_time_min="240",
            carbon_source=solvent, carbon_source_flow_original="precursor solution 10 mL/h; 40 mL injected",
            reducing_gas="H2", reducing_gas_flow_original="50 sccm", reducing_gas_flow_sccm="50",
            inert_gas="Ar", inert_gas_flow_original="400 sccm", inert_gas_flow_sccm="400", total_flow_original="450 sccm gas plus precursor vapour", total_flow_sccm="450",
            gas_composition_summary=f"{solvent} precursor vapour in 50 sccm H2 and 400 sccm Ar",
        ))
        tables["yield_quality"].append(yield_row(
            run_id, primary_yield_metric="raw as-grown CNT/catalyst product", yield_original=raw_yield,
            yield_definition_original=("Typical raw Fe@NCNT catalyst/product recovered from one 40 mL precursor injection." if code == "FENCNT" else "not_reported"),
            secondary_result_summary=morphology, product_mixture_summary=f"{cnt_type} containing embedded {metals} nanoparticles",
            CNT_type_reported=cnt_type, CNT_type_confirmed=cnt_type, CNT_type_evidence="SEM/TEM morphology; Raman and EDX/XPS used for composition.",
            Raman_ratio_type="ID/IG" if raman != "not_reported" else "not_reported", Raman_ratio_value=raman,
            morphology=morphology, characterization_methods="Raman; SEM; FESEM; TEM; EDX; XPS; XRD",
        ))
        tables["cost_scale_review"].append(cost_row(
            run_id, scale_evidence_summary="Laboratory floating-CVD batch; standard 40 mL injection produced about 1.5 g Fe@NCNT and a stock of about 10 g was prepared over repeated batches.",
            cost_driver_summary=f"790 C furnace, {precursor}, {solvent}, hydrogen and argon.", safety_risk="Flammable solvent vapour and hydrogen at high temperature; organometallic Fe/Ru precursor exposure.",
            emission_or_waste="CVD off-gas and metal-containing raw CNT product; not quantitatively inventoried.",
        ))
        add_evidence(tables, store, source_id, run_id, "CAT", "catalyst_system", f"{run_id}_CAT", "record_level", "SPAN_0DE0252671702A0C467D", "Ferrocene-based in-situ CNT catalyst and floating-CVD method.")
        add_evidence(tables, store, source_id, run_id, "PROC", "reactor_process_gas", f"{run_id}_S01", "record_level", "SPAN_0DE0252671702A0C467D", "Precursor concentration, injection, reactor temperature, time and H2/Ar flows.")
        if code.startswith("RUFE"):
            add_evidence(tables, store, source_id, run_id, "RATIO", "catalyst_system", f"{run_id}_CAT", "metal_ratio_original;precursor_summary;preparation_detail", "SPAN_33B9BD747105647D4D19", "CVD co-doping precursor ratios.")
        result_span = "SPAN_9C4BF2FB0AFBC5F2E503" if code in {"FECNT", "FENCNT"} else "SPAN_A5522DA4B582C1855F38"
        add_evidence(tables, store, source_id, run_id, "PRODUCT", "yield_quality", f"{run_id}_PROD", "record_level", result_span, "CNT identity, Raman disorder and morphology.")
        add_evidence(tables, store, source_id, run_id, "SCALE", "cost_scale_review", run_id, "record_level", "SPAN_35C0434DB059A9B601A7", "Per-injection yield and repeated-batch stock context.")
        tables["review_issue_log"].append(issue_row(
            f"{source_id}_ISSUE_{code}_001", source_id, run_id, "product_basis", "yield_quality", f"{run_id}_PROD", "yield_original",
            "The only printed mass is raw Fe@NCNT catalyst/product; it is not a purified CNT yield and is not transferred to the other precursor variants.", f"EVD_{run_id}_PRODUCT; EVD_{run_id}_SCALE", "low",
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
    (REPORT_ROOT / "manual_batch_008_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
