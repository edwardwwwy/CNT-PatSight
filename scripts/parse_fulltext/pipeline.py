from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from contextlib import closing
from pathlib import Path
from typing import Any

from scripts.io_utils import replace_with_retry, unique_part_path, utc_now

from .extractor import PARSER_VERSION, extract_document
from .storage import CandidateStore


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ParsePipeline:
    def __init__(
        self,
        root: Path,
        metadata_db: Path,
        fulltext_db: Path,
        candidate_db: Path,
        raw_text_dir: Path,
        parsed_text_dir: Path,
        section_csv: Path,
        span_csv: Path,
        status_csv: Path,
        reports_dir: Path,
        *,
        force: bool = False,
        ocr_queue_csv: Path | None = None,
    ):
        self.root = root
        self.metadata_db = metadata_db
        self.fulltext_db = fulltext_db
        self.candidate_db = candidate_db
        self.raw_text_dir = raw_text_dir
        self.parsed_text_dir = parsed_text_dir
        self.section_csv = section_csv
        self.span_csv = span_csv
        self.status_csv = status_csv
        self.reports_dir = reports_dir
        self.force = force
        self.ocr_queue_csv = ocr_queue_csv or status_csv.parent / "ocr_queue.csv"
        for directory in (parsed_text_dir, section_csv.parent, reports_dir):
            directory.mkdir(parents=True, exist_ok=True)

    def run(self, source_ids: list[str] | None = None, limit: int | None = None) -> dict[str, Any]:
        metadata = self._load_metadata(source_ids, limit)
        primary = self._load_primary()
        run_id = f"PARSE_{utc_now().replace('-','').replace(':','')}_{uuid.uuid4().hex[:6]}"
        counters = {"parsed_sources": 0, "cache_hits": 0, "skipped_no_fulltext": 0, "failed_sources": 0}
        with CandidateStore(self.candidate_db) as store:
            store.start_run(run_id, utc_now(), {"source_ids": source_ids or [], "limit": limit, "force": self.force, "parser_version": PARSER_VERSION})
            try:
                for record in metadata:
                    source_id = record["source_id"]
                    artifact = primary.get(source_id)
                    now = utc_now()
                    if not artifact:
                        store.mark_status(
                            source_id,
                            PARSER_VERSION,
                            "skipped",
                            "no_available_fulltext",
                            now,
                            parse_quality="metadata_only",
                        )
                        counters["skipped_no_fulltext"] += 1
                        continue
                    path = self._resolve(artifact["local_path"])
                    if not path.exists():
                        store.mark_status(source_id, PARSER_VERSION, "failed", "registered_fulltext_file_missing", now, artifact["fulltext_id"], artifact["content_hash"])
                        counters["failed_sources"] += 1
                        continue
                    actual_hash = sha256_file(path)
                    parsed_text_path = self.parsed_text_dir / f"{source_id}.parsed.json"
                    if (
                        not self.force
                        and store.is_cached(source_id, actual_hash, PARSER_VERSION)
                        and parsed_text_path.exists()
                    ):
                        counters["cache_hits"] += 1
                        continue
                    warnings: list[str] = []
                    if actual_hash != artifact["content_hash"]:
                        warnings.append("content_hash_changed_after_fulltext_registration")
                    try:
                        output = extract_document(
                            path,
                            artifact["fulltext_type"],
                            source_id,
                            artifact["fulltext_id"],
                            actual_hash,
                            record["title"],
                            record["abstract"],
                        )
                    except Exception as exc:
                        store.mark_status(
                            source_id,
                            PARSER_VERSION,
                            "failed",
                            f"{type(exc).__name__}:{exc}",
                            now,
                            artifact["fulltext_id"],
                            actual_hash,
                            warnings,
                        )
                        counters["failed_sources"] += 1
                        continue
                    warnings.extend(output.warnings)
                    self._write_source_file(
                        parsed_text_path,
                        record,
                        artifact,
                        actual_hash,
                        output,
                        now,
                    )
                    store.replace_source(
                        source_id,
                        artifact["fulltext_id"],
                        actual_hash,
                        PARSER_VERSION,
                        output.sections,
                        output.spans,
                        warnings,
                        self._rel(parsed_text_path),
                        self._rel(parsed_text_path),
                        now,
                        parse_quality=output.parse_quality,
                        page_count=output.page_count,
                        extracted_char_count=output.extracted_char_count,
                        table_count=output.table_count,
                        reference_section_detected=output.reference_section_detected,
                        experimental_section_detected=output.experimental_section_detected,
                        ocr_required=output.ocr_required,
                        fulltext_relevance_status=output.fulltext_relevance_status,
                        candidate_extract_eligible=output.candidate_extract_eligible,
                        promotion_reason=output.promotion_reason,
                    )
                    counters["parsed_sources"] += 1
                section_rows, span_rows, status_rows = store.export(self.section_csv, self.span_csv, self.status_csv)
                ocr_queue_rows = store.export_ocr_queue(self.ocr_queue_csv)
                aggregate = store.summary()
                status = "partial" if counters["failed_sources"] else "complete"
                summary = {
                    "run_id": run_id,
                    "status": status,
                    "metadata_sources": len(metadata),
                    **counters,
                    **aggregate,
                    "section_csv_path": self._rel(self.section_csv),
                    "span_csv_path": self._rel(self.span_csv),
                    "status_csv_path": self._rel(self.status_csv),
                    "candidate_database_path": self._rel(self.candidate_db),
                    "ocr_queue_csv_path": self._rel(self.ocr_queue_csv),
                    "ocr_queue_rows": ocr_queue_rows,
                    "exported_section_rows": section_rows,
                    "exported_span_rows": span_rows,
                    "exported_status_rows": status_rows,
                    "completed_at": utc_now(),
                }
                store.finish_run(run_id, utc_now(), status, summary)
                self._write_report(run_id, summary)
                return summary
            except Exception as exc:
                summary = {"run_id": run_id, "status": "failed", **counters, "error": f"{type(exc).__name__}:{exc}"}
                store.finish_run(run_id, utc_now(), "failed", summary, summary["error"])
                self._write_report(run_id, summary)
                raise

    def _load_metadata(self, source_ids: list[str] | None, limit: int | None) -> list[dict[str, Any]]:
        with closing(sqlite3.connect(self.metadata_db)) as connection:
            connection.row_factory = sqlite3.Row
            sql = "SELECT source_id,title,abstract,doi FROM works"
            params: list[Any] = []
            if source_ids:
                placeholders = ",".join("?" for _ in source_ids)
                sql += f" WHERE source_id IN ({placeholders})"
                params.extend(source_ids)
            sql += " ORDER BY source_id"
            if limit is not None:
                sql += " LIMIT ?"
                params.append(limit)
            return [dict(row) for row in connection.execute(sql, params)]

    def _load_primary(self) -> dict[str, dict[str, Any]]:
        with closing(sqlite3.connect(self.fulltext_db)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT * FROM fulltext_source WHERE is_primary=1 AND fetch_status='success' AND content_scope='fulltext'"
            ).fetchall()
            return {str(row["source_id"]): dict(row) for row in rows}

    @staticmethod
    def _write_if_changed(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_text(encoding="utf-8", errors="replace") == content:
            return
        temp = unique_part_path(path)
        temp.write_text(content, encoding="utf-8")
        replace_with_retry(temp, path)

    def _write_json_if_changed(self, path: Path, value: Any) -> None:
        self._write_if_changed(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")

    def _write_source_file(
        self,
        path: Path,
        metadata: dict[str, Any],
        artifact: dict[str, Any],
        actual_hash: str,
        output: Any,
        parsed_at: str,
    ) -> None:
        """Write the only parsed-text artifact retained for a source."""
        section_rows = [
            {
                "section_id": section.section_id,
                "section_name_raw": section.section_name_raw,
                "section_name_normalized": section.section_name_normalized,
                "section_order": section.section_order,
                "text": section.text,
                "page_start": section.page_start,
                "page_end": section.page_end,
                "extractor": section.extractor,
                "needs_review": bool(section.needs_review),
            }
            for section in output.sections
        ]
        payload = {
            "source_id": metadata["source_id"],
            "full_text": output.raw_text,
            "sections": section_rows,
            "tables": [
                row for row in section_rows if row["section_name_normalized"] == "tables"
            ],
            "figure_captions": [
                row
                for row in section_rows
                if row["section_name_normalized"] == "figure_captions"
            ],
            "document_metadata": {
                "source_id": metadata["source_id"],
                "doi": metadata.get("doi") or "",
                "title": metadata.get("title") or "",
                "abstract": metadata.get("abstract") or "",
                "input_fulltext_id": artifact["fulltext_id"],
                "input_fulltext_type": artifact["fulltext_type"],
                "input_fulltext_url": artifact.get("fulltext_url") or "",
                "input_local_path": artifact.get("local_path") or "",
                "source_file_sha256": actual_hash,
                "parser_version": PARSER_VERSION,
                "parsed_at": parsed_at,
            },
            "parse_report": {
                "source_id": metadata["source_id"],
                "parser_version": PARSER_VERSION,
                "parse_quality": output.parse_quality,
                "page_count": output.page_count,
                "extracted_char_count": output.extracted_char_count,
                "table_count": output.table_count,
                "reference_section_detected": bool(output.reference_section_detected),
                "experimental_section_detected": bool(output.experimental_section_detected),
                "ocr_required": bool(output.ocr_required),
                "automatic_fulltext_relevance_status": output.fulltext_relevance_status,
                "automatic_candidate_extract_eligible": bool(output.candidate_extract_eligible),
                "promotion_reason": output.promotion_reason,
                "warnings": output.warnings,
                "section_count": len(output.sections),
                "candidate_span_count": len(output.spans),
                "parsed_at": parsed_at,
            },
        }
        self._write_json_if_changed(path, payload)

    def _write_report(self, run_id: str, summary: dict[str, Any]) -> None:
        content = json.dumps(summary, ensure_ascii=False, indent=2)
        (self.reports_dir / f"{run_id}.json").write_text(content, encoding="utf-8")
        (self.reports_dir / "latest.json").write_text(content, encoding="utf-8")

    def _resolve(self, path: str) -> Path:
        candidate = Path(path)
        return candidate if candidate.is_absolute() else self.root / candidate

    def _rel(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return str(path.resolve())


def print_summary(summary: dict[str, Any]) -> None:
    print(f"run_id: {summary.get('run_id','')}")
    print(f"status: {summary.get('status','')}")
    print(
        "sources: "
        f"parsed={summary.get('parsed_sources',0)}, cache_hits={summary.get('cache_hits',0)}, "
        f"skipped_no_fulltext={summary.get('skipped_no_fulltext',0)}, failed={summary.get('failed_sources',0)}"
    )
    print(f"sections: {summary.get('section_rows',0)} {json.dumps(summary.get('section_type_distribution',{}), ensure_ascii=False, sort_keys=True)}")
    print(f"candidate_spans: {summary.get('span_rows',0)} {json.dumps(summary.get('span_type_distribution',{}), ensure_ascii=False, sort_keys=True)}")
    print(f"section_csv: {summary.get('section_csv_path','')}")
    print(f"span_csv: {summary.get('span_csv_path','')}")
