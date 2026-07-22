#!/usr/bin/env python3
"""Continuously acquire, parse, and package all C-tier papers in batches of five.

The generated eight-table packages are conservative source-level evidence
ledgers.  Candidate spans are never combined into reconstructed experimental
runs.  Sources without lawful/parseable full text still receive a complete
eight-file package whose status ledger explains the blocking condition.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.extraction.batch_common import (
    ROOT,
    TABLES,
    EvidenceStore,
    catalyst_row,
    cost_row,
    evidence_row,
    issue_row,
    process_row,
    row,
    run_row,
    write_table,
    yield_row,
)
from scripts.extraction.package_io import read_extraction_package, write_extraction_package
from scripts.validation.validate_tables import DEFAULT_DICTIONARY, DEFAULT_SCHEMA, validate


BATCH_ID = "C_CLASS_450_20260720"
BATCH_SIZE = 5
SOURCE_ROOT = ROOT / "data/raw/literature"
PIPELINE_ROOT = ROOT / "data/interim"
CLASS_ROOT = PIPELINE_ROOT / "extraction/C"
META_DB = SOURCE_ROOT / "metadata/literature.sqlite3"
PDF_ROOT = SOURCE_ROOT / "pdf"
FULLTEXT_ROOT = SOURCE_ROOT / "html"
FULLTEXT_DB = SOURCE_ROOT / "metadata/fulltext_registry/fulltext.sqlite3"
CANDIDATE_ROOT = ROOT / "cache/exports"
CANDIDATE_DB = ROOT / "cache/databases/extraction_candidates.sqlite3"
PARSED_TEXT_ROOT = ROOT / "data/interim/parsed_text/by_source"
RAW_TEXT_ROOT = PARSED_TEXT_ROOT
BATCH_ROOT = ROOT / "runs/extraction/C/batches" / BATCH_ID
PACKAGE_ROOT = CLASS_ROOT
COMPLETE_ROOT = ROOT / "runs/extraction/C/coverage/C_CLASS_COMPLETE_20260720"
REPORT_ROOT = BATCH_ROOT
METALS = ("Fe", "Co", "Ni", "Mo", "Cu", "Mn", "Ru", "Pt", "Pd", "Cr", "Au", "Ag", "V", "W")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, columns: Iterable[str], rows: Iterable[dict[str, Any]]) -> None:
    names = list(columns)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="raise")
        writer.writeheader()
        for item in rows:
            writer.writerow({name: "" if item.get(name) is None else item.get(name) for name in names})


def source_rows() -> list[dict[str, Any]]:
    with sqlite3.connect(META_DB) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("ATTACH DATABASE ? AS fulltext", (str(FULLTEXT_DB),))
        connection.execute("ATTACH DATABASE ? AS candidate", (str(CANDIDATE_DB),))
        return [
            dict(item)
            for item in connection.execute(
                """
                SELECT w.*, q.download_status, q.fulltext_status,
                       q.acquisition_status, q.failure_reason AS fulltext_failure_reason,
                       q.local_path AS acquired_local_path,
                       p.parse_status, p.parse_quality, p.candidate_extract_eligible,
                       p.span_count, p.failure_reason AS parse_failure_reason
                FROM works AS w
                LEFT JOIN fulltext.fulltext_acquisition_queue AS q USING (source_id)
                LEFT JOIN candidate.parse_source_status AS p USING (source_id)
                WHERE w.priority_tier = 'C'
                ORDER BY q.queue_priority, w.source_id
                """
            )
        ]


def refresh_source(source_id: str) -> dict[str, Any]:
    return next(item for item in source_rows() if item["source_id"] == source_id)


def candidate_spans(source_id: str) -> list[dict[str, Any]]:
    with sqlite3.connect(CANDIDATE_DB) as connection:
        connection.row_factory = sqlite3.Row
        return [
            dict(item)
            for item in connection.execute(
                """
                SELECT s.*, p.section_name_raw, p.section_name_normalized
                FROM candidate_experiment_span AS s
                LEFT JOIN paper_text_section AS p ON p.section_id = s.section_id
                WHERE s.source_id = ?
                ORDER BY s.page_range, s.span_id
                """,
                (source_id,),
            )
        ]


class CClassEvidenceStore:
    def __init__(self) -> None:
        self.connection = sqlite3.connect(CANDIDATE_DB)
        self.connection.row_factory = sqlite3.Row

    def close(self) -> None:
        self.connection.close()

    def span(self, source_id: str, span_id: str) -> dict[str, Any]:
        item = self.connection.execute(
            """
            SELECT s.*, p.section_name_raw, p.section_name_normalized
            FROM candidate_experiment_span AS s
            LEFT JOIN paper_text_section AS p ON p.section_id = s.section_id
            WHERE s.source_id = ? AND s.span_id = ?
            """,
            (source_id, span_id),
        ).fetchone()
        if item is None:
            raise KeyError(f"Missing candidate span {source_id}/{span_id}")
        return dict(item)


def master(meta: dict[str, Any], scope: str, state: str) -> dict[str, str]:
    local_path = f"data/interim/parsed_text/by_source/{meta['source_id']}.parsed.json"
    return row(
        "source_master",
        source_id=meta["source_id"],
        source_type=meta.get("source_type") or "paper",
        source_title=meta.get("title") or meta["source_id"],
        publication_year=meta.get("year") or "not_reported",
        authors_or_assignee=meta.get("authors") or "not_reported",
        publication_venue=meta.get("journal") or "not_reported",
        doi_or_patent_no=meta.get("doi") or "not_reported",
        source_link=meta.get("source_link") or "not_reported",
        source_database="local_metadata_registry",
        source_language=meta.get("language") or "not_reported",
        local_file_path=local_path,
        pdf_status=meta.get("download_status") or meta.get("pdf_status") or "not_available",
        screening_class=state,
        source_section_scope=scope,
        extraction_status="needs_review",
        review_status="pending_review",
        notes=f"Automated conservative C-tier package for {BATCH_ID}; domain_expert_verified=false.",
    )


def metal_tokens(text: str) -> str:
    padded = f" {text} "
    found = [metal for metal in METALS if f" {metal} " in padded]
    return "; ".join(found) or "not_reported"


def add_evidence(
    tables: dict[str, list[dict[str, str]]], store: EvidenceStore, source_id: str,
    run_id: str, table: str, record_id: str, span_id: str, summary: str,
) -> str:
    evidence_id = f"EVD_{source_id}_{span_id}"
    tables["evidence_index"].append(
        evidence_row(
            store, source_id, evidence_id, run_id, table, record_id,
            "record_level", span_id, summary, confidence="medium", value_status="reported",
        )
    )
    return evidence_id


def evidence_ledger(meta: dict[str, Any], spans: list[dict[str, Any]], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = str(meta["source_id"])
    run_id = f"{source_id}_EVIDENCE_LEDGER"
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master(
            meta,
            "Every parser-selected candidate span is retained independently; experimental run boundaries are not inferred.",
            "candidate_evidence_ledger",
        )
    )
    anchor = run_row(
        source_id, "EVIDENCE_LEDGER", "Source-level candidate evidence ledger",
        f"{len(spans)} candidate spans retained without asserting experimental run boundaries.", "low",
    )
    anchor["data_type"] = "source_evidence_ledger"
    anchor["notes"] = "Not an experimental run; this row anchors independently reported source-span records."
    tables["source_run"].append(anchor)

    first_evidence = "not_applicable"
    first_target = ("source_run", run_id)
    catalyst_spans = [item for item in spans if item["span_type"] == "catalyst"]
    process_spans = [item for item in spans if item["span_type"] in {"process", "gas"}]
    quality_spans = [item for item in spans if item["span_type"] in {"yield", "characterization", "purification"}]
    scale_spans = [item for item in spans if item["span_type"] == "scale_safety"]

    for index, span in enumerate(catalyst_spans, start=1):
        record_id = f"{run_id}_CAT_{index:03d}"
        tables["catalyst_system"].append(
            catalyst_row(
                run_id, catalyst_id=record_id,
                catalyst_label="candidate catalyst evidence; see linked source span",
                active_metals=metal_tokens(span["text"]), support_material="not_reported",
                preparation_method="source_span_evidence",
                preparation_detail="Candidate span retained verbatim; not assigned to a reconstructed run.",
                notes="Source-level evidence record, not a paper-wide catalyst assertion.",
            )
        )
        evidence_id = add_evidence(tables, store, source_id, run_id, "catalyst_system", record_id, span["span_id"], "Candidate catalyst/preparation evidence.")
        if first_evidence == "not_applicable":
            first_evidence, first_target = evidence_id, ("catalyst_system", record_id)

    for order, span in enumerate(process_spans, start=1):
        record_id = f"{run_id}_S{order:03d}"
        tables["reactor_process_gas"].append(
            process_row(
                run_id, order, "source_span_evidence", process_stage_id=record_id,
                reactor_type="source_span_evidence", scale_level="not_reported",
                pressure_original="not_reported", pressure_kPa="",
                process_note="Candidate process/gas span retained independently; no cross-span condition join.",
            )
        )
        evidence_id = add_evidence(tables, store, source_id, run_id, "reactor_process_gas", record_id, span["span_id"], "Candidate process or gas evidence.")
        if first_evidence == "not_applicable":
            first_evidence, first_target = evidence_id, ("reactor_process_gas", record_id)

    for index, span in enumerate(quality_spans, start=1):
        record_id = f"{run_id}_PROD_{index:03d}"
        tables["yield_quality"].append(
            yield_row(
                run_id, product_id=record_id,
                primary_yield_metric="source-span candidate product/yield/quality evidence",
                yield_original="not_reported", yield_definition_original="not_reported",
                secondary_result_summary="Candidate span retained verbatim; not assigned to a reconstructed run.",
                CNT_type_reported="not_reported", CNT_type_confirmed="not_applicable",
                CNT_type_evidence="Source-span candidate evidence; see evidence_index.",
                characterization_methods="not_reported",
                notes="Source-level evidence record; values remain needs_review.",
            )
        )
        evidence_id = add_evidence(tables, store, source_id, run_id, "yield_quality", record_id, span["span_id"], "Candidate yield, characterization, or purification evidence.")
        if first_evidence == "not_applicable":
            first_evidence, first_target = evidence_id, ("yield_quality", record_id)

    if scale_spans:
        tables["cost_scale_review"].append(
            cost_row(
                run_id, scale_level_demonstrated="not_reported",
                scale_evidence_summary="Source-span scale/safety evidence retained independently.",
                cost_driver_summary="not_reported", safety_risk="not_reported",
                emission_or_waste="not_reported",
                review_note="One source-level row anchors independently reported scale/safety spans.",
            )
        )
        for span in scale_spans:
            evidence_id = add_evidence(tables, store, source_id, run_id, "cost_scale_review", run_id, span["span_id"], "Candidate scale or safety evidence.")
            if first_evidence == "not_applicable":
                first_evidence, first_target = evidence_id, ("cost_scale_review", run_id)

    target_table, target_id = first_target
    tables["review_issue_log"].append(
        issue_row(
            f"{source_id}_ISSUE_RUN_BOUNDARY_001", source_id, run_id,
            "critical_data_gap", target_table, target_id, "record_level",
            "Candidate spans are independent evidence records; experimental run boundaries require source-level review.",
            first_evidence, "high",
        )
    )
    return tables


def status_ledger(meta: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    source_id = str(meta["source_id"])
    run_id = f"{source_id}_SOURCE_STATUS"
    parsed = meta.get("parse_status") == "success"
    if parsed:
        state = "parsed_not_extractable"
        reason = meta.get("parse_failure_reason") or "Parsed text contains no candidate CNT-production span."
        scope = "Full text parsed; no source-level evidence justified a candidate experimental record."
    else:
        state = "fulltext_or_parse_unavailable"
        reason = meta.get("parse_failure_reason") or meta.get("fulltext_failure_reason") or "Lawful full text or successful parse unavailable."
        scope = "Metadata retained; structured scientific facts are not inferred without lawful parseable source text."
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(master(meta, scope, state))
    anchor = run_row(source_id, "SOURCE_STATUS", "Source processing status", reason, "low")
    anchor["data_type"] = "source_status_ledger"
    anchor["relevance_class"] = state
    anchor["notes"] = "Administrative coverage row only; not an experimental run."
    tables["source_run"].append(anchor)
    status_evidence_id = f"EVD_{source_id}_SOURCE_STATUS"
    tables["evidence_index"].append(
        row(
            "evidence_index",
            evidence_id=status_evidence_id,
            source_id=source_id,
            run_id=run_id,
            target_table="source_run",
            target_record_id=run_id,
            target_fields="data_type; run_summary",
            evidence_type="processing_status",
            value_status="not_reported",
            source_section="metadata_and_local_processing_registry",
            source_locator="fulltext_acquisition_queue; parse_source_status",
            source_object_ref="not_applicable",
            evidence_text="",
            evidence_summary=reason,
            confidence="high",
            linked_issue_id=f"{source_id}_ISSUE_SOURCE_001",
            notes="Administrative provenance only; not scientific source evidence.",
        )
    )
    tables["review_issue_log"].append(
        issue_row(
            f"{source_id}_ISSUE_SOURCE_001", source_id, run_id,
            "critical_data_gap", "source_run", run_id, "data_type",
            reason, status_evidence_id, "high" if not parsed else "medium",
        )
    )
    return tables


def publish(source_id: str, tables: dict[str, list[dict[str, str]]]) -> dict[str, int]:
    write_extraction_package(
        source_id,
        "C",
        tables,
        extraction_status="needs_review",
        replace=True,
    )
    return {table: len(tables[table]) for table in TABLES}


def run_command(arguments: list[str]) -> int:
    completed = subprocess.run([sys.executable, *arguments], cwd=ROOT, check=False)
    return completed.returncode


def fetch_command(command: str) -> list[str]:
    return [
        "scripts/fetch_fulltext/fetch.py",
        "--metadata-db", str(META_DB),
        "--fulltext-db", str(FULLTEXT_DB),
        "--pdf-dir", str(PDF_ROOT),
        "--html-dir", str(FULLTEXT_ROOT),
        "--reports-dir", str(ROOT / "runs/fulltext"),
        "--source-csv", str(SOURCE_ROOT / "metadata/fulltext_registry/fulltext_source.csv"),
        "--coverage-csv", str(SOURCE_ROOT / "metadata/fulltext_registry/fulltext_coverage.csv"),
        "--queue-csv", str(SOURCE_ROOT / "metadata/fulltext_registry/fulltext_acquisition_queue.csv"),
        "--verified-candidates-csv", str(SOURCE_ROOT / "metadata/fulltext_registry/verified_oa_candidates.csv"),
        command,
    ]


def parse_command(command: str) -> list[str]:
    return [
        "scripts/parse_fulltext/parse.py",
        "--metadata-db", str(META_DB),
        "--fulltext-db", str(FULLTEXT_DB),
        "--candidate-db", str(CANDIDATE_DB),
        "--raw-text-dir", str(RAW_TEXT_ROOT),
        "--parsed-text-dir", str(PARSED_TEXT_ROOT),
        "--section-csv", str(CANDIDATE_ROOT / "paper_text_section.csv"),
        "--span-csv", str(CANDIDATE_ROOT / "candidate_experiment_span.csv"),
        "--status-csv", str(CANDIDATE_ROOT / "parse_source_status.csv"),
        "--ocr-queue-csv", str(CANDIDATE_ROOT / "ocr_queue.csv"),
        "--reports-dir", str(CANDIDATE_ROOT / "reports"),
        command,
    ]


def acquire_and_parse(
    batch: list[dict[str, Any]], skip_acquire: bool, max_candidates_per_source: int,
) -> list[dict[str, Any]]:
    source_ids = [str(item["source_id"]) for item in batch]
    if not skip_acquire:
        pending = [
            str(item["source_id"])
            for item in batch
            if item.get("download_status") in {None, "", "queued", "downloading", "failed_retryable"}
        ]
        if pending:
            command = fetch_command("run") + [
                "--max-candidates-per-source", str(max_candidates_per_source),
            ]
            for source_id in pending:
                command.extend(["--source-id", source_id])
            run_command(command)

    refreshed = [refresh_source(source_id) for source_id in source_ids]
    parse_ids = [
        str(item["source_id"])
        for item in refreshed
        if item.get("download_status") in {"validated", "downloaded", "local_existing"}
        and item.get("parse_status") != "success"
    ]
    if parse_ids:
        command = parse_command("run")
        for source_id in parse_ids:
            command.extend(["--source-id", source_id])
        run_command(command)
    return [refresh_source(source_id) for source_id in source_ids]


def write_batch_metrics(batch_number: int, source_metrics: dict[str, dict[str, Any]]) -> None:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {
        "batch_id": BATCH_ID,
        "batch_number": batch_number,
        "batch_size": len(source_metrics),
        "source_ids": list(source_metrics),
        "sources": source_metrics,
        "completed_at": utc_now(),
    }
    (REPORT_ROOT / f"automatic_batch_{batch_number:03d}_metrics.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def consolidate(sources: list[dict[str, Any]]) -> dict[str, Any]:
    COMPLETE_ROOT.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".c_class_complete.", dir=COMPLETE_ROOT.parent))
    try:
        tables_root = temporary / "eight_tables"
        tables_root.mkdir()
        combined_counts: dict[str, int] = {}
        for table in TABLES:
            rows: list[dict[str, str]] = []
            for meta in sources:
                payload = read_extraction_package(
                    PACKAGE_ROOT / f"{meta['source_id']}.extraction.json"
                )
                rows.extend(payload["tables"][table])
            columns = list(row(table).keys())
            write_csv(tables_root / f"{table}.csv", columns, rows)
            combined_counts[table] = len(rows)

        coverage: list[dict[str, Any]] = []
        for index, meta in enumerate(sources, start=1):
            source_id = str(meta["source_id"])
            payload = read_extraction_package(
                PACKAGE_ROOT / f"{source_id}.extraction.json"
            )
            master_rows = payload["tables"]["source_master"]
            coverage.append(
                {
                    "source_id": source_id,
                    "title": meta.get("title") or "",
                    "priority_tier": "C",
                    "batch_number": ((index - 1) // BATCH_SIZE) + 1,
                    "download_status": meta.get("download_status") or "not_queued",
                    "parse_status": meta.get("parse_status") or "not_parsed",
                    "package_state": master_rows[0]["screening_class"],
                    "candidate_span_count": meta.get("span_count") or 0,
                    "package_path": str(PACKAGE_ROOT / f"{source_id}.extraction.json"),
                }
            )
        write_csv(temporary / "source_coverage.csv", coverage[0].keys(), coverage)
        state_counts = Counter(item["package_state"] for item in coverage)
        summary = {
            "batch_id": BATCH_ID,
            "source_count": len(sources),
            "batch_size": BATCH_SIZE,
            "batch_count": (len(sources) + BATCH_SIZE - 1) // BATCH_SIZE,
            "package_state_counts": dict(sorted(state_counts.items())),
            "eight_table_row_counts": combined_counts,
            "completed_at": utc_now(),
            "status": "complete_eight_table_packages_with_explicit_evidence_scope",
        }
        if COMPLETE_ROOT.exists():
            shutil.rmtree(COMPLETE_ROOT)
        shutil.move(str(temporary), str(COMPLETE_ROOT))
        REPORT_ROOT.mkdir(parents=True, exist_ok=True)
        (REPORT_ROOT / "consolidated_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return summary
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process every C-tier source in uninterrupted batches of five.")
    parser.add_argument("--skip-acquire", action="store_true", help="Package current local state without remote acquisition.")
    parser.add_argument("--start-batch", type=int, default=1, help="One-based batch checkpoint to resume from.")
    parser.add_argument("--max-batches", type=int, help="Diagnostic cap; omit for complete processing.")
    parser.add_argument("--max-candidates-per-source", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sources = source_rows()
    if len(sources) != 450:
        raise ValueError(f"Expected 450 C-tier sources, found {len(sources)}")
    all_batches = [sources[index:index + BATCH_SIZE] for index in range(0, len(sources), BATCH_SIZE)]
    start_index = max(0, args.start_batch - 1)
    batches = list(enumerate(all_batches[start_index:], start=start_index + 1))
    if args.max_batches is not None:
        batches = batches[: max(0, args.max_batches)]
    store = CClassEvidenceStore()
    try:
        for batch_number, batch in batches:
            print(f"C batch {batch_number:03d}/{(len(sources) + 4) // 5:03d} start: " + ", ".join(str(item["source_id"]) for item in batch), flush=True)
            refreshed = acquire_and_parse(
                batch, args.skip_acquire, max(1, args.max_candidates_per_source),
            )
            source_metrics: dict[str, dict[str, Any]] = {}
            for meta in refreshed:
                source_id = str(meta["source_id"])
                spans = candidate_spans(source_id) if meta.get("parse_status") == "success" else []
                tables = evidence_ledger(meta, spans, store) if spans else status_ledger(meta)
                counts = publish(source_id, tables)
                source_metrics[source_id] = {
                    "download_status": meta.get("download_status") or "not_queued",
                    "parse_status": meta.get("parse_status") or "not_parsed",
                    "candidate_span_count": len(spans),
                    "package_state": tables["source_master"][0]["screening_class"],
                    "row_counts": counts,
                }
            write_batch_metrics(batch_number, source_metrics)
            print(f"C batch {batch_number:03d} complete", flush=True)
    finally:
        store.close()

    if batches and batches[-1][0] == len(all_batches):
        run_command(fetch_command("export"))
        run_command(parse_command("export"))
        summary = consolidate(source_rows())
        print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
