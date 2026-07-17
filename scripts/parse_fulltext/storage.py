from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

from scripts.io_utils import replace_with_retry, unique_part_path

from .models import CandidateSpan, TextSection


SECTION_COLUMNS = [
    "section_id", "source_id", "input_fulltext_id", "input_content_hash",
    "section_name_raw", "section_name_normalized", "section_order", "text",
    "page_start", "page_end", "extractor", "needs_review",
]

SPAN_COLUMNS = [
    "source_id", "span_id", "input_fulltext_id", "section_id", "span_type", "text",
    "confidence_rule", "confidence_score", "matched_keywords", "page_range", "needs_review",
]

STATUS_COLUMNS = [
    "source_id", "input_fulltext_id", "input_content_hash", "parser_version", "parse_status",
    "failure_reason", "parse_quality", "page_count", "extracted_char_count", "table_count",
    "reference_section_detected", "experimental_section_detected", "ocr_required",
    "fulltext_relevance_status", "candidate_extract_eligible", "promotion_reason",
    "section_count", "span_count", "warnings_json", "raw_text_path", "parsed_text_path",
    "created_at", "updated_at",
]

OCR_QUEUE_COLUMNS = [
    "source_id", "input_fulltext_id", "input_content_hash", "parse_quality",
    "page_count", "extracted_char_count", "ocr_required", "parser_version",
    "failure_reason", "created_at", "updated_at",
]


class CandidateStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode = WAL")
        self._create_schema()

    def __enter__(self) -> "CandidateStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.connection.close()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS parse_runs (
                run_id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                config_json TEXT NOT NULL,
                summary_json TEXT NOT NULL DEFAULT '{}',
                error_message TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS parse_source_status (
                source_id TEXT PRIMARY KEY,
                input_fulltext_id TEXT NOT NULL DEFAULT '',
                input_content_hash TEXT NOT NULL DEFAULT '',
                parser_version TEXT NOT NULL,
                parse_status TEXT NOT NULL CHECK(parse_status IN ('success','failed','skipped')),
                failure_reason TEXT NOT NULL DEFAULT '',
                parse_quality TEXT NOT NULL DEFAULT 'metadata_only',
                page_count INTEGER NOT NULL DEFAULT 0,
                extracted_char_count INTEGER NOT NULL DEFAULT 0,
                table_count INTEGER NOT NULL DEFAULT 0,
                reference_section_detected INTEGER NOT NULL DEFAULT 0,
                experimental_section_detected INTEGER NOT NULL DEFAULT 0,
                ocr_required INTEGER NOT NULL DEFAULT 0,
                fulltext_relevance_status TEXT NOT NULL DEFAULT 'needs_fulltext_review',
                candidate_extract_eligible INTEGER NOT NULL DEFAULT 0,
                promotion_reason TEXT NOT NULL DEFAULT '',
                section_count INTEGER NOT NULL DEFAULT 0,
                span_count INTEGER NOT NULL DEFAULT 0,
                warnings_json TEXT NOT NULL DEFAULT '[]',
                raw_text_path TEXT NOT NULL DEFAULT '',
                parsed_text_path TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS paper_text_section (
                section_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                input_fulltext_id TEXT NOT NULL,
                input_content_hash TEXT NOT NULL,
                section_name_raw TEXT NOT NULL,
                section_name_normalized TEXT NOT NULL,
                section_order INTEGER NOT NULL,
                text TEXT NOT NULL,
                page_start INTEGER,
                page_end INTEGER,
                extractor TEXT NOT NULL,
                needs_review INTEGER NOT NULL DEFAULT 1
            );
            CREATE INDEX IF NOT EXISTS idx_section_source_order ON paper_text_section(source_id,section_order);
            CREATE INDEX IF NOT EXISTS idx_section_normalized ON paper_text_section(section_name_normalized);

            CREATE TABLE IF NOT EXISTS candidate_experiment_span (
                span_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                input_fulltext_id TEXT NOT NULL,
                section_id TEXT NOT NULL,
                span_type TEXT NOT NULL,
                text TEXT NOT NULL,
                confidence_rule TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                matched_keywords TEXT NOT NULL,
                page_range TEXT NOT NULL DEFAULT '',
                needs_review INTEGER NOT NULL DEFAULT 1
            );
            CREATE INDEX IF NOT EXISTS idx_span_source_type ON candidate_experiment_span(source_id,span_type);
            CREATE INDEX IF NOT EXISTS idx_span_confidence ON candidate_experiment_span(confidence_score DESC);
            """
        )
        additions = {
            "parse_quality": "TEXT NOT NULL DEFAULT 'metadata_only'",
            "page_count": "INTEGER NOT NULL DEFAULT 0",
            "extracted_char_count": "INTEGER NOT NULL DEFAULT 0",
            "table_count": "INTEGER NOT NULL DEFAULT 0",
            "reference_section_detected": "INTEGER NOT NULL DEFAULT 0",
            "experimental_section_detected": "INTEGER NOT NULL DEFAULT 0",
            "ocr_required": "INTEGER NOT NULL DEFAULT 0",
            "fulltext_relevance_status": "TEXT NOT NULL DEFAULT 'needs_fulltext_review'",
            "candidate_extract_eligible": "INTEGER NOT NULL DEFAULT 0",
            "promotion_reason": "TEXT NOT NULL DEFAULT ''",
        }
        existing = {str(row[1]) for row in self.connection.execute("PRAGMA table_info(parse_source_status)")}
        for name, definition in additions.items():
            if name not in existing:
                self.connection.execute(f"ALTER TABLE parse_source_status ADD COLUMN {name} {definition}")
        self.connection.commit()

    def start_run(self, run_id: str, started_at: str, config: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT INTO parse_runs(run_id,started_at,status,config_json) VALUES (?,?,'running',?)",
            (run_id, started_at, json.dumps(config, ensure_ascii=False, sort_keys=True)),
        )
        self.connection.commit()

    def finish_run(self, run_id: str, completed_at: str, status: str, summary: dict[str, Any], error: str = "") -> None:
        self.connection.execute(
            "UPDATE parse_runs SET completed_at=?,status=?,summary_json=?,error_message=? WHERE run_id=?",
            (completed_at, status, json.dumps(summary, ensure_ascii=False, sort_keys=True), error, run_id),
        )
        self.connection.commit()

    def is_cached(self, source_id: str, content_hash: str, parser_version: str) -> bool:
        row = self.connection.execute(
            "SELECT parse_status,input_content_hash,parser_version FROM parse_source_status WHERE source_id=?",
            (source_id,),
        ).fetchone()
        return bool(row and row["parse_status"] == "success" and row["input_content_hash"] == content_hash and row["parser_version"] == parser_version)

    def replace_source(
        self,
        source_id: str,
        fulltext_id: str,
        content_hash: str,
        parser_version: str,
        sections: list[TextSection],
        spans: list[CandidateSpan],
        warnings: list[str],
        raw_text_path: str,
        parsed_text_path: str,
        now: str,
        *,
        parse_quality: str,
        page_count: int,
        extracted_char_count: int,
        table_count: int,
        reference_section_detected: int,
        experimental_section_detected: int,
        ocr_required: int,
        fulltext_relevance_status: str,
        candidate_extract_eligible: int,
        promotion_reason: str,
    ) -> None:
        created_row = self.connection.execute(
            "SELECT created_at FROM parse_source_status WHERE source_id=?", (source_id,)
        ).fetchone()
        created_at = str(created_row[0]) if created_row else now
        with self.connection:
            self.connection.execute("DELETE FROM candidate_experiment_span WHERE source_id=?", (source_id,))
            self.connection.execute("DELETE FROM paper_text_section WHERE source_id=?", (source_id,))
            self.connection.executemany(
                f"INSERT INTO paper_text_section({','.join(SECTION_COLUMNS)}) VALUES ({','.join('?' for _ in SECTION_COLUMNS)})",
                [[getattr(section, column) for column in SECTION_COLUMNS] for section in sections],
            )
            self.connection.executemany(
                f"INSERT INTO candidate_experiment_span({','.join(SPAN_COLUMNS)}) VALUES ({','.join('?' for _ in SPAN_COLUMNS)})",
                [[getattr(span, column) for column in SPAN_COLUMNS] for span in spans],
            )
            self.connection.execute(
                """
                INSERT INTO parse_source_status(
                    source_id,input_fulltext_id,input_content_hash,parser_version,parse_status,
                    failure_reason,parse_quality,page_count,extracted_char_count,table_count,
                    reference_section_detected,experimental_section_detected,ocr_required,
                    fulltext_relevance_status,candidate_extract_eligible,promotion_reason,
                    section_count,span_count,warnings_json,raw_text_path,parsed_text_path,
                    created_at,updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(source_id) DO UPDATE SET
                    input_fulltext_id=excluded.input_fulltext_id,
                    input_content_hash=excluded.input_content_hash,
                    parser_version=excluded.parser_version,
                    parse_status=excluded.parse_status,
                    failure_reason=excluded.failure_reason,
                    parse_quality=excluded.parse_quality,
                    page_count=excluded.page_count,
                    extracted_char_count=excluded.extracted_char_count,
                    table_count=excluded.table_count,
                    reference_section_detected=excluded.reference_section_detected,
                    experimental_section_detected=excluded.experimental_section_detected,
                    ocr_required=excluded.ocr_required,
                    fulltext_relevance_status=excluded.fulltext_relevance_status,
                    candidate_extract_eligible=excluded.candidate_extract_eligible,
                    promotion_reason=excluded.promotion_reason,
                    section_count=excluded.section_count,
                    span_count=excluded.span_count,
                    warnings_json=excluded.warnings_json,
                    raw_text_path=excluded.raw_text_path,
                    parsed_text_path=excluded.parsed_text_path,
                    updated_at=excluded.updated_at
                """,
                (
                    source_id, fulltext_id, content_hash, parser_version, "success", "",
                    parse_quality, page_count, extracted_char_count, table_count,
                    reference_section_detected, experimental_section_detected, ocr_required,
                    fulltext_relevance_status, candidate_extract_eligible, promotion_reason,
                    len(sections), len(spans), json.dumps(warnings, ensure_ascii=False),
                    raw_text_path, parsed_text_path, created_at, now,
                ),
            )

    def mark_status(
        self,
        source_id: str,
        parser_version: str,
        status: str,
        reason: str,
        now: str,
        fulltext_id: str = "",
        content_hash: str = "",
        warnings: list[str] | None = None,
        parse_quality: str = "unreadable",
        ocr_required: int = 0,
    ) -> None:
        existing = self.connection.execute(
            "SELECT created_at FROM parse_source_status WHERE source_id=?", (source_id,)
        ).fetchone()
        created_at = str(existing[0]) if existing else now
        with self.connection:
            self.connection.execute("DELETE FROM candidate_experiment_span WHERE source_id=?", (source_id,))
            self.connection.execute("DELETE FROM paper_text_section WHERE source_id=?", (source_id,))
            self.connection.execute(
                """
            INSERT INTO parse_source_status(
                source_id,input_fulltext_id,input_content_hash,parser_version,parse_status,
                failure_reason,parse_quality,page_count,extracted_char_count,table_count,
                reference_section_detected,experimental_section_detected,ocr_required,
                fulltext_relevance_status,candidate_extract_eligible,promotion_reason,
                section_count,span_count,warnings_json,raw_text_path,parsed_text_path,
                created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(source_id) DO UPDATE SET
                input_fulltext_id=excluded.input_fulltext_id,
                input_content_hash=excluded.input_content_hash,
                parser_version=excluded.parser_version,
                parse_status=excluded.parse_status,
                failure_reason=excluded.failure_reason,
                parse_quality=excluded.parse_quality,
                page_count=excluded.page_count,
                extracted_char_count=excluded.extracted_char_count,
                table_count=excluded.table_count,
                reference_section_detected=excluded.reference_section_detected,
                experimental_section_detected=excluded.experimental_section_detected,
                ocr_required=excluded.ocr_required,
                fulltext_relevance_status=excluded.fulltext_relevance_status,
                candidate_extract_eligible=excluded.candidate_extract_eligible,
                promotion_reason=excluded.promotion_reason,
                section_count=excluded.section_count,
                span_count=excluded.span_count,
                warnings_json=excluded.warnings_json,
                raw_text_path=excluded.raw_text_path,
                parsed_text_path=excluded.parsed_text_path,
                updated_at=excluded.updated_at
            """,
                (
                    source_id, fulltext_id, content_hash, parser_version, status, reason,
                    parse_quality, 0, 0, 0, 0, 0, ocr_required,
                    "needs_fulltext_review", 0, f"parse_status_{status}:{reason}",
                    0, 0, json.dumps(warnings or [], ensure_ascii=False), "", "", created_at, now,
                ),
            )

    def export(self, section_csv: Path, span_csv: Path, status_csv: Path) -> tuple[int, int, int]:
        section_csv.parent.mkdir(parents=True, exist_ok=True)
        sections = self.connection.execute("SELECT * FROM paper_text_section ORDER BY source_id,section_order").fetchall()
        spans = self.connection.execute("SELECT * FROM candidate_experiment_span ORDER BY source_id,confidence_score DESC,span_type,span_id").fetchall()
        statuses = self.connection.execute("SELECT * FROM parse_source_status ORDER BY source_id").fetchall()
        self._write_rows(section_csv, SECTION_COLUMNS, sections)
        self._write_rows(span_csv, SPAN_COLUMNS, spans)
        self._write_rows(status_csv, STATUS_COLUMNS, statuses)
        return len(sections), len(spans), len(statuses)

    def export_ocr_queue(self, path: Path) -> int:
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = self.connection.execute(
            "SELECT * FROM parse_source_status WHERE ocr_required=1 AND parse_quality='scanned' ORDER BY source_id"
        ).fetchall()
        self._write_rows(path, OCR_QUEUE_COLUMNS, rows)
        return len(rows)

    @staticmethod
    def _write_rows(path: Path, columns: list[str], rows: list[sqlite3.Row]) -> None:
        temporary = unique_part_path(path)
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow({column: row[column] if row[column] is not None else "" for column in columns})
        replace_with_retry(temporary, path)

    def summary(self) -> dict[str, Any]:
        status_counts = {
            str(row["parse_status"]): int(row["count"])
            for row in self.connection.execute("SELECT parse_status,COUNT(*) AS count FROM parse_source_status GROUP BY parse_status")
        }
        section_counts = {
            str(row["section_name_normalized"]): int(row["count"])
            for row in self.connection.execute("SELECT section_name_normalized,COUNT(*) AS count FROM paper_text_section GROUP BY section_name_normalized")
        }
        span_counts = {
            str(row["span_type"]): int(row["count"])
            for row in self.connection.execute("SELECT span_type,COUNT(*) AS count FROM candidate_experiment_span GROUP BY span_type")
        }
        quality_counts = {
            str(row["parse_quality"]): int(row["count"])
            for row in self.connection.execute("SELECT parse_quality,COUNT(*) AS count FROM parse_source_status GROUP BY parse_quality")
        }
        relevance_counts = {
            str(row["fulltext_relevance_status"]): int(row["count"])
            for row in self.connection.execute("SELECT fulltext_relevance_status,COUNT(*) AS count FROM parse_source_status GROUP BY fulltext_relevance_status")
        }
        return {
            "parse_status_distribution": status_counts,
            "section_type_distribution": section_counts,
            "span_type_distribution": span_counts,
            "parse_quality_distribution": quality_counts,
            "fulltext_relevance_distribution": relevance_counts,
            "candidate_extract_eligible_sources": relevance_counts.get("candidate_extract", 0),
            "section_rows": sum(section_counts.values()),
            "span_rows": sum(span_counts.values()),
        }

    def latest_run(self) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT * FROM parse_runs ORDER BY started_at DESC LIMIT 1").fetchone()
        if not row:
            return None
        data = dict(row)
        data["config"] = json.loads(data.pop("config_json"))
        data["summary"] = json.loads(data.pop("summary_json"))
        return data
