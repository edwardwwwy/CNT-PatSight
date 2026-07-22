#!/usr/bin/env python3
"""Export the complete reviewable evidence set for screened B-tier sources.

The screening tier is deliberately kept separate from the formal eight-table
layer.  This exporter copies every parser candidate span for each locally
available, B-tier, ``candidate_extract_eligible`` source, with its section
locator and metadata.  It does *not* invent run boundaries or promote any
candidate evidence to a formal experimental fact.

The resulting batch makes the entire B-class corpus auditable in one place:

* ``manifest.csv`` covers all screened B-tier sources;
* ``candidate_evidence.csv`` contains every available candidate span for the
  sources the parser considers eligible for evidence review;
* ``sections.csv`` retains the complete parsed section map for those sources;
* ``ready_for_evidence_review.csv`` and ``unavailable_fulltext.csv`` provide
  the actionable and blocked queues without silently dropping records.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sqlite3
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[2]
BATCH_ID = "B_CLASS_371_20260719"
BATCH_ROOT = ROOT / "runs" / "extraction" / "B" / "batches" / BATCH_ID
META_DB = ROOT / "data" / "raw" / "literature" / "metadata" / "literature.sqlite3"
FULLTEXT_DB = ROOT / "data" / "raw" / "literature" / "metadata" / "fulltext_registry" / "fulltext.sqlite3"
CANDIDATE_DB = (
    ROOT / "cache" / "databases" / "extraction_candidates.sqlite3"
)
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


def _read_rows(connection: sqlite3.Connection, query: str, values: Sequence[Any] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(query, values)]


def _write_csv(path: Path, rows: Iterable[dict[str, Any]], headers: Sequence[str] | None = None) -> int:
    materialized = list(rows)
    if headers is None:
        headers = list(materialized[0]) if materialized else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="raise")
        writer.writeheader()
        for row in materialized:
            writer.writerow({key: "" if row.get(key) is None else row.get(key) for key in headers})
    return len(materialized)


def _has_direct_package(source_id: str) -> bool:
    package = ROOT / "data" / "benchmark" / "fixtures" / "six_papers" / source_id
    return all((package / f"{table}.csv").is_file() for table in TABLES)


def _manual_package_ids() -> set[str]:
    root = ROOT / "data" / "interim" / "extraction" / "B"
    return {path.name.removesuffix(".extraction.json") for path in root.glob("*.extraction.json")}


def _load_manifest_rows() -> list[dict[str, Any]]:
    with sqlite3.connect(META_DB) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("ATTACH DATABASE ? AS fulltext", (str(FULLTEXT_DB),))
        connection.execute("ATTACH DATABASE ? AS candidate", (str(CANDIDATE_DB),))
        rows = _read_rows(
            connection,
            """
            SELECT
                w.source_id,
                w.title,
                w.year,
                w.doi,
                w.priority_tier,
                w.pipeline_status AS metadata_pipeline_status,
                q.download_status,
                q.failure_reason AS fulltext_failure_reason,
                p.parse_status,
                p.parse_quality,
                p.candidate_extract_eligible,
                p.extracted_char_count,
                p.span_count AS candidate_span_count,
                p.failure_reason AS parse_failure_reason
            FROM works AS w
            LEFT JOIN fulltext.fulltext_acquisition_queue AS q USING (source_id)
            LEFT JOIN candidate.parse_source_status AS p USING (source_id)
            WHERE w.priority_tier = 'B'
            ORDER BY w.source_id
            """,
        )
    manual_ids = _manual_package_ids()
    for row in rows:
        source_id = str(row["source_id"])
        if _has_direct_package(source_id):
            state = "existing_curated_package"
            reason = "Existing project-native eight-table package."
        elif source_id in manual_ids:
            state = "existing_manual_package_needs_review"
            reason = "Existing manually transcribed eight-table package."
        elif row["candidate_extract_eligible"] == 1:
            state = "candidate_evidence_exported_needs_review"
            reason = "All locally parsed candidate evidence is exported in this B-class batch."
        elif row["parse_status"] == "success":
            state = "parsed_not_extractable"
            reason = row["parse_failure_reason"] or (
                "Parser found no source-level CNT-production evidence suitable for a run-level package."
            )
        else:
            state = "fulltext_or_parse_unavailable"
            reason = (
                row["parse_failure_reason"]
                or row["fulltext_failure_reason"]
                or "Legal full text or successful parse unavailable."
            )
        row["extraction_state"] = state
        row["extraction_reason"] = reason
    return rows


def _load_evidence_rows(source_ids: Sequence[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not source_ids:
        return [], []
    placeholders = ",".join("?" for _ in source_ids)
    with sqlite3.connect(CANDIDATE_DB) as connection:
        connection.row_factory = sqlite3.Row
        sections = _read_rows(
            connection,
            f"""
            SELECT *
            FROM paper_text_section
            WHERE source_id IN ({placeholders})
            ORDER BY source_id, section_order, section_id
            """,
            source_ids,
        )
        spans = _read_rows(
            connection,
            f"""
            SELECT
                s.*,
                p.section_name_raw,
                p.section_name_normalized,
                p.page_start AS section_page_start,
                p.page_end AS section_page_end
            FROM candidate_experiment_span AS s
            LEFT JOIN paper_text_section AS p ON p.section_id = s.section_id
            WHERE s.source_id IN ({placeholders})
            ORDER BY s.source_id, s.page_range, s.span_id
            """,
            source_ids,
        )
    return sections, spans


def export_batch(replace: bool = False) -> dict[str, Any]:
    """Create an immutable, complete B-tier evidence batch and return its metrics."""
    if BATCH_ROOT.exists() and not replace:
        raise FileExistsError(f"B-class batch already exists: {BATCH_ROOT}; pass --replace to refresh it")

    manifest = _load_manifest_rows()
    ready = [
        row
        for row in manifest
        if row["extraction_state"] == "candidate_evidence_exported_needs_review"
    ]
    ready_ids = [str(row["source_id"]) for row in ready]
    sections, spans = _load_evidence_rows(ready_ids)
    span_source_ids = {str(row["source_id"]) for row in spans}
    missing_spans = sorted(set(ready_ids) - span_source_ids)
    if missing_spans:
        raise ValueError("Eligible B sources without candidate spans: " + ";".join(missing_spans))

    BATCH_ROOT.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".b_class_evidence.", dir=BATCH_ROOT.parent))
    try:
        manifest_headers = list(manifest[0]) if manifest else []
        row_counts = {
            "manifest": _write_csv(temporary / "manifest.csv", manifest, manifest_headers),
            "ready_for_evidence_review": _write_csv(
                temporary / "ready_for_evidence_review.csv", ready, manifest_headers
            ),
            "unavailable_fulltext": _write_csv(
                temporary / "unavailable_fulltext.csv",
                [
                    row
                    for row in manifest
                    if row["extraction_state"] == "fulltext_or_parse_unavailable"
                ],
                manifest_headers,
            ),
            "parsed_not_extractable": _write_csv(
                temporary / "parsed_not_extractable.csv",
                [row for row in manifest if row["extraction_state"] == "parsed_not_extractable"],
                manifest_headers,
            ),
            "sections": _write_csv(
                temporary / "sections.csv",
                sections,
                list(sections[0]) if sections else [],
            ),
            "candidate_evidence": _write_csv(
                temporary / "candidate_evidence.csv",
                spans,
                list(spans[0]) if spans else [],
            ),
        }
        summary = {
            "batch_id": BATCH_ID,
            "priority_tier": "B",
            "total_sources": len(manifest),
            "state_counts": dict(sorted(Counter(str(row["extraction_state"]) for row in manifest).items())),
            "download_status_counts": dict(
                sorted(Counter(str(row["download_status"] or "not_queued") for row in manifest).items())
            ),
            "candidate_evidence_source_count": len(ready_ids),
            "candidate_evidence_span_count": len(spans),
            "parsed_section_count": len(sections),
            "row_counts": row_counts,
            "evidence_status": "candidate_evidence_only_needs_independent_review",
            "formal_fact_rows_created": 0,
            "automated_model_used": False,
            "coverage_note": (
                "All candidate spans available in the local parser registry for eligible B-tier sources "
                "are exported. Sources without lawful full text remain explicitly listed rather than inferred."
            ),
        }
        (temporary / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        if BATCH_ROOT.exists():
            shutil.rmtree(BATCH_ROOT)
        shutil.move(str(temporary), str(BATCH_ROOT))
        return summary
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the complete B-class evidence registry.")
    parser.add_argument("--replace", action="store_true", help="Refresh the existing derived export.")
    args = parser.parse_args()
    print(json.dumps(export_batch(args.replace), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
