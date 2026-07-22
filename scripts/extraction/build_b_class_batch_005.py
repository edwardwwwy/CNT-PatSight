#!/usr/bin/env python3
"""Transcribe the six first-principles CNT catalyst models as eight tables."""

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
BATCH_NUMBER = 5
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
SOURCE_ID = "LIT_04A53D0FAD58D6F5"


def build_source(metadata: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    tables = {name: [] for name in TABLES}
    master = master_row(
        metadata,
        "First-principles Ni, Pd, Pt, Cu, Ag and Au CNT-growth catalyst models; no physical synthesis run is claimed.",
    )
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{source_id}.parsed.json"
    master["notes"] = f"Manual computational-model transcription for {BATCH_NAME}."
    tables["source_master"].append(master)

    models = (
        ("NI", "Ni", "0.39 eV calculated C-adatom diffusion barrier on Ni(111); armchair preference ratio about 5 at 900 C.", "SPAN_80B514EEB368E4BA46FD"),
        ("PD", "Pd", "Calculated carbon binding, surface/subsurface diffusion and armchair-versus-zigzag edge stability for Pd.", "SPAN_0C142B488D4FD01181FC"),
        ("PT", "Pt", "Calculated carbon binding and diffusion; concerted C-dimer barrier reaches about 0.70 eV for Pt.", "SPAN_A37486F670F04E28EB40"),
        ("CU", "Cu", "0.07 eV calculated C-adatom surface-diffusion barrier and armchair preference ratio about 130 at 900 C; identified as the strongest modeled chirality-selective candidate.", "SPAN_2FA3B1D2451433D34BB9"),
        ("AG", "Ag", "0.20 eV calculated C-adatom barrier and 0.43 eV concerted C-dimer barrier on Ag.", "SPAN_5136698638DF23FB3717"),
        ("AU", "Au", "Calculated surface, subsurface and bulk monoatomic-carbon barriers lie in the 0.52-0.64 eV range.", "SPAN_0EB8BA7BBD9581E27993"),
    )
    for code, metal, summary, result_span in models:
        run_id = f"{source_id}_{code}_DFT"
        run = run_row(source_id, f"{code}_DFT", f"{metal} catalyst first-principles model", summary, confidence="medium")
        run["data_type"] = "computational_model_record"
        run["target_track"] = "CNT_growth_modeling"
        tables["source_run"].append(run)
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                catalyst_label=f"fcc {metal} nanoparticle surface model",
                active_metals=metal,
                support_material="not_applicable",
                metal_ratio_original=f"pure {metal}",
                precursor_summary="not_applicable; computational catalyst model",
                preparation_method="not_applicable",
                preparation_detail="Periodic fcc-metal (111) slab and bulk models; a (311) stepped surface represented (100) step edges.",
                activation_condition="not_applicable",
                post_preparation_condition="not_applicable",
            )
        )
        tables["reactor_process_gas"].append(
            process_row(
                run_id,
                1,
                "first_principles_modeling",
                reactor_type="not_applicable; density-functional-theory model",
                reactor_setup_summary=(
                    "Quantum ESPRESSO/PWSCF PBE ultrasoft-pseudopotential calculation; "
                    "three-layer p(3x3) slabs and 3x3x3 bulk supercells."
                ),
                scale_level="computational",
                temperature_setpoint_C="not_applicable",
                holding_time_min="not_applicable",
                carbon_source="monoatomic and diatomic carbon derived conceptually from CH4, C2H4, C2H2 or ethanol",
                pressure_original="not_applicable",
                pressure_kPa="",
                process_note="Calculated binding, diffusion and CNT-edge energetics; not a physical reactor run.",
            )
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="calculated catalyst/CNT-growth energetic indicators",
                yield_original="not_applicable; no physical CNT yield",
                yield_definition_original="First-principles binding energies, activation barriers and thermodynamic chirality preference.",
                secondary_result_summary=summary,
                product_mixture_summary="not_applicable; no product synthesized",
                CNT_type_reported="modeled armchair-like and zigzag-like CNT edges",
                CNT_type_confirmed="not_applicable",
                CNT_type_evidence="Computational edge-fragment energetics only.",
                characterization_methods="density functional theory; nudged elastic band calculation",
            )
        )
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                scale_level_demonstrated="computational",
                scale_evidence_summary="Atomistic model; no laboratory or production scale demonstrated.",
                cost_driver_summary="computational resources",
                safety_risk="not_applicable",
                emission_or_waste="not_applicable",
            )
        )
        add_evidence(tables, store, source_id, run_id, "CAT", "catalyst_system", f"{run_id}_CAT", "catalyst_label;active_metals;support_material;preparation_detail", "SPAN_7A1C2F130FE171C9E3A9", "Six modeled late-transition and coinage-metal catalysts.")
        add_evidence(tables, store, source_id, run_id, "MODEL", "reactor_process_gas", f"{run_id}_S01", "record_level", "SPAN_D5030CAE570CB7E24685", "Periodic slab/bulk first-principles model setup.")
        add_evidence(tables, store, source_id, run_id, "RESULT", "yield_quality", f"{run_id}_PROD", "record_level", result_span, f"{metal}-specific calculated growth indicator.", confidence="medium", value_status="calculated")
        add_evidence(tables, store, source_id, run_id, "SCALE", "cost_scale_review", run_id, "record_level", "SPAN_1638490BB0C91169704A", "The source scope is explicitly first-principles modeling rather than a physical scale demonstration.", confidence="medium", value_status="review_assessment")
        tables["review_issue_log"].append(
            issue_row(
                f"{source_id}_ISSUE_{code}_001",
                source_id,
                run_id,
                "graph_only_values",
                "yield_quality",
                f"{run_id}_PROD",
                "secondary_result_summary",
                "Most metal-specific energies are graph-only; only values explicitly printed in narrative text are transcribed.",
                f"EVD_{run_id}_RESULT",
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
    result = {"batch_id": BATCH_NAME, "sources": [metric], "total_runs": metric["row_counts"]["source_run"], "status": "completed_needs_review"}
    (REPORT_ROOT / "manual_batch_005_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
