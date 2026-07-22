#!/usr/bin/env python3
"""Place every B-class candidate span into an eight-table evidence ledger.

The output is deliberately source-level: one ``source_evidence_ledger`` row
per paper anchors candidate facts without claiming that separately reported
conditions belong to one experimental run.  Each populated fact record has an
immutable candidate-span citation in ``evidence_index.csv``.
"""

from __future__ import annotations

import csv
import contextlib
import io
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from scripts.extraction.batch_common import (
    ROOT,
    TABLES,
    EvidenceStore,
    catalyst_row,
    cost_row,
    evidence_row,
    issue_row,
    load_metadata,
    master_row,
    process_row,
    run_row,
    write_table,
    yield_row,
)
from scripts.validation.validate_tables import DEFAULT_DICTIONARY, DEFAULT_SCHEMA, validate


BATCH_ID = "B_CLASS_371_20260719"
EVIDENCE_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
OUTPUT_ROOT = ROOT / "runs/extraction/B/superseded_evidence" / BATCH_ID

METALS = ("Fe", "Co", "Ni", "Mo", "Cu", "Mn", "Ru", "Pt", "Pd", "Cr", "Au", "Ag", "V", "W")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def metal_tokens(text: str) -> str:
    padded = f" {text} "
    found = [metal for metal in METALS if f" {metal} " in padded]
    return "; ".join(found) or "not_reported"


def add_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    source_id: str,
    run_id: str,
    table: str,
    record_id: str,
    span_id: str,
    summary: str,
) -> str:
    evidence_id = f"EVD_{source_id}_{span_id}"
    tables["evidence_index"].append(
        evidence_row(
            store,
            source_id,
            evidence_id,
            run_id,
            table,
            record_id,
            "record_level",
            span_id,
            summary,
            confidence="medium",
            value_status="reported",
        )
    )
    return evidence_id


def publish(source_id: str, tables: dict[str, list[dict[str, str]]]) -> dict[str, int]:
    destination = OUTPUT_ROOT / source_id
    if destination.exists():
        raise FileExistsError(f"Evidence-ledger package already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{source_id}.", dir=destination.parent))
    try:
        for table in TABLES:
            write_table(temporary, table, tables[table])
        with contextlib.redirect_stdout(io.StringIO()):
            validation_errors = validate(temporary, DEFAULT_SCHEMA, DEFAULT_DICTIONARY)
        if validation_errors:
            raise RuntimeError(f"Eight-table validation failed for {source_id}")
        shutil.move(str(temporary), str(destination))
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {table: len(tables[table]) for table in TABLES}


def build_source(meta: dict[str, Any], spans: list[dict[str, str]], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = str(meta["source_id"])
    run_id = f"{source_id}_EVIDENCE_LEDGER"
    tables = {table: [] for table in TABLES}
    master = master_row(
        meta,
        "Every parser-selected candidate span is entered as a source-level evidence ledger record; experimental run boundaries are intentionally not inferred.",
    )
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{source_id}.parsed.json"
    master["notes"] = "Eight-table evidence ledger; values are source-span scoped and must not be combined as one experimental condition."
    tables["source_master"].append(master)
    tables["source_run"].append(
        run_row(
            source_id,
            "EVIDENCE_LEDGER",
            "Source-level candidate evidence ledger",
            f"{len(spans)} candidate spans retained without asserting experimental run boundaries.",
            confidence="low",
        )
    )
    tables["source_run"][0]["data_type"] = "source_evidence_ledger"
    tables["source_run"][0]["notes"] = "Not an experimental run; this row only anchors independently reported source-span records."

    catalyst_spans = [row for row in spans if row["span_type"] == "catalyst"]
    process_spans = [row for row in spans if row["span_type"] in {"process", "gas"}]
    quality_spans = [row for row in spans if row["span_type"] in {"yield", "characterization", "purification"}]
    scale_spans = [row for row in spans if row["span_type"] == "scale_safety"]
    issue_evidence = ""
    issue_target: tuple[str, str] | None = None

    for index, span in enumerate(catalyst_spans, start=1):
        catalyst_id = f"{run_id}_CAT_{index:03d}"
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                catalyst_id=catalyst_id,
                catalyst_label="candidate catalyst evidence; see linked source span",
                active_metals=metal_tokens(span["text"]),
                support_material="not_reported",
                preparation_method="source_span_evidence",
                preparation_detail="Candidate span retained verbatim in evidence_index; not assigned to a reconstructed run.",
                notes="Source-level evidence record, not a catalyst formulation assertion across the paper.",
            )
        )
        evidence_id = add_evidence(tables, store, source_id, run_id, "catalyst_system", catalyst_id, span["span_id"], "Candidate catalyst/preparation evidence.")
        if issue_target is None:
            issue_target, issue_evidence = ("catalyst_system", catalyst_id), evidence_id

    for order, span in enumerate(process_spans, start=1):
        stage_id = f"{run_id}_S{order:03d}"
        tables["reactor_process_gas"].append(
            process_row(
                run_id,
                order,
                "source_span_evidence",
                process_stage_id=stage_id,
                reactor_type="source_span_evidence",
                scale_level="not_reported",
                pressure_original="not_reported",
                pressure_kPa="",
                process_note="Candidate process/gas span retained as evidence; it is not joined to other source conditions.",
            )
        )
        evidence_id = add_evidence(tables, store, source_id, run_id, "reactor_process_gas", stage_id, span["span_id"], "Candidate process or gas evidence.")
        if issue_target is None:
            issue_target, issue_evidence = ("reactor_process_gas", stage_id), evidence_id

    for index, span in enumerate(quality_spans, start=1):
        product_id = f"{run_id}_PROD_{index:03d}"
        tables["yield_quality"].append(
            yield_row(
                run_id,
                product_id=product_id,
                primary_yield_metric="source-span candidate product/yield/quality evidence",
                yield_original="not_reported",
                yield_definition_original="not_reported",
                secondary_result_summary="Candidate span retained verbatim in evidence_index; it is not assigned to a reconstructed run.",
                CNT_type_reported="not_reported",
                CNT_type_confirmed="not_applicable",
                CNT_type_evidence="Source-span candidate evidence; see linked evidence_index record.",
                characterization_methods="not_reported",
                notes="Source-level evidence record; query catalog/field_index.csv for span-derived values.",
            )
        )
        evidence_id = add_evidence(tables, store, source_id, run_id, "yield_quality", product_id, span["span_id"], "Candidate yield, characterization, or purification evidence.")
        if issue_target is None:
            issue_target, issue_evidence = ("yield_quality", product_id), evidence_id

    if scale_spans:
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                scale_level_demonstrated="not_reported",
                scale_evidence_summary="Source-span scale/safety evidence is retained in evidence_index; no source-wide scale claim is inferred.",
                cost_driver_summary="not_reported",
                safety_risk="not_reported",
                emission_or_waste="not_reported",
                review_note="One row anchors multiple independently reported source-span scale/safety records.",
            )
        )
        for span in scale_spans:
            evidence_id = add_evidence(tables, store, source_id, run_id, "cost_scale_review", run_id, span["span_id"], "Candidate scale or safety evidence.")
            if issue_target is None:
                issue_target, issue_evidence = ("cost_scale_review", run_id), evidence_id

    if issue_target is not None:
        table, record_id = issue_target
        target_field = "record_level"
        tables["review_issue_log"].append(
            issue_row(
                f"{source_id}_ISSUE_RUN_BOUNDARY_001",
                source_id,
                run_id,
                "critical_data_gap",
                table,
                record_id,
                target_field,
                "Source spans are formalized as independent ledger records. Experimental run boundaries were not recoverable without manual source-level reconciliation.",
                issue_evidence,
                "high",
            )
        )
    return tables


def main() -> None:
    manifest = read_csv(EVIDENCE_ROOT / "manifest.csv")
    source_ids = [row["source_id"] for row in manifest if row["extraction_state"] == "candidate_evidence_exported_needs_review"]
    span_rows = read_csv(EVIDENCE_ROOT / "candidate_evidence.csv")
    grouped: dict[str, list[dict[str, str]]] = {source_id: [] for source_id in source_ids}
    for span in span_rows:
        grouped[span["source_id"]].append(span)
    if any(not grouped[source_id] for source_id in source_ids):
        raise ValueError("Candidate source without spans")
    metadata = load_metadata("B")
    metrics: dict[str, dict[str, int]] = {}
    store = EvidenceStore()
    try:
        for source_id in source_ids:
            metrics[source_id] = publish(source_id, build_source(metadata[source_id], grouped[source_id], store))
    finally:
        store.close()
    result = {
        "source_count": len(source_ids),
        "candidate_span_count": len(span_rows),
        "row_counts": {table: sum(item[table] for item in metrics.values()) for table in TABLES},
        "status": "evidence_ledger_needs_run_boundary_review",
    }
    (OUTPUT_ROOT / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
