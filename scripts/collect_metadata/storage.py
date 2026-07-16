from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

from .models import ApiResponse, MatchDecision, NormalizedWork, UpsertResult
from .scoring import DEDUP_RULE_VERSION, RelevanceScorer
from .utils import json_dumps, normalize_doi, normalize_title, stable_source_id, utc_now


CSV_COLUMNS = [
    "source_id",
    "source_type",
    "document_type",
    "title",
    "doi_or_patent_no",
    "abstract",
    "authors_or_assignee",
    "year",
    "journal",
    "publisher",
    "publication_date",
    "citation_count",
    "source_link",
    "open_access_status",
    "pdf_url",
    "html_url",
    "source_database",
    "source_api_ids",
    "collection_time",
    "last_updated_at",
    "relevance_score",
    "relevance_band",
    "relevance_reasons",
    "topic_relevance_score",
    "metadata_evidence_likelihood_score",
    "access_score",
    "priority_tier",
    "needs_fulltext_check",
    "pipeline_status",
    "topic_positive_reasons",
    "topic_negative_reasons",
    "evidence_reasons",
    "priority_tier_reason",
    "screening_rule_version",
    "dedup_rule_version",
    "scored_at",
    "source_snapshot_id",
    "dedup_status",
    "dedup_reasons",
    "conflict_reasons",
    "screening_class",
    "language",
    "pdf_status",
    "pdf_path",
    "extraction_status",
    "review_status",
    "notes",
]


FIELD_PRIORITY: dict[str, dict[str, int]] = {
    "document_type": {"manual_registry": 100, "crossref": 50, "openalex": 40, "semantic_scholar": 35, "unpaywall": 30},
    "title": {"manual_registry": 100, "crossref": 50, "openalex": 40, "semantic_scholar": 30, "unpaywall": 20},
    "doi": {"manual_registry": 100, "crossref": 50, "openalex": 40, "semantic_scholar": 40, "unpaywall": 40},
    "abstract": {"manual_registry": 100, "semantic_scholar": 50, "openalex": 40, "crossref": 30},
    "authors": {"manual_registry": 100, "crossref": 50, "openalex": 40, "semantic_scholar": 30, "unpaywall": 20},
    "year": {"manual_registry": 100, "crossref": 50, "openalex": 40, "semantic_scholar": 30, "unpaywall": 20},
    "journal": {"manual_registry": 100, "crossref": 50, "openalex": 40, "semantic_scholar": 30, "unpaywall": 20},
    "publisher": {"manual_registry": 100, "crossref": 50, "unpaywall": 40, "openalex": 30},
    "publication_date": {"crossref": 50, "openalex": 40, "semantic_scholar": 30},
    "citation_count": {"semantic_scholar": 50, "openalex": 40, "crossref": 30},
    "source_link": {"manual_registry": 100, "crossref": 50, "semantic_scholar": 40, "openalex": 30, "unpaywall": 20},
    "open_access_status": {"unpaywall": 50, "semantic_scholar": 40, "openalex": 30, "crossref": 20},
    "pdf_url": {"unpaywall": 50, "semantic_scholar": 40, "openalex": 30, "crossref": 20},
    "html_url": {"unpaywall": 50, "semantic_scholar": 40, "openalex": 30, "crossref": 20},
    "language": {"openalex": 50, "crossref": 30},
    "screening_class": {"manual_registry": 100},
    "pdf_status": {"manual_registry": 100},
    "pdf_path": {"manual_registry": 100},
    "extraction_status": {"manual_registry": 100},
    "review_status": {"manual_registry": 100},
    "notes": {"manual_registry": 100},
}


WORK_VALUE_FIELDS = [
    "title",
    "document_type",
    "doi",
    "abstract",
    "authors",
    "year",
    "journal",
    "publisher",
    "publication_date",
    "citation_count",
    "source_link",
    "open_access_status",
    "pdf_url",
    "html_url",
    "language",
    "screening_class",
    "pdf_status",
    "pdf_path",
    "extraction_status",
    "review_status",
    "notes",
]


class MetadataStore:
    def __init__(
        self,
        path: Path,
        similarity_threshold: float = 0.97,
        review_threshold: float = 0.92,
        title_min_length: int = 30,
        dedup_rule_version: str = DEDUP_RULE_VERSION,
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.similarity_threshold = similarity_threshold
        self.review_threshold = review_threshold
        self.title_min_length = title_min_length
        self.dedup_rule_version = dedup_rule_version
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self._create_schema()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "MetadataStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS collection_runs (
                run_id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                config_json TEXT NOT NULL,
                summary_json TEXT NOT NULL DEFAULT '{}',
                error_message TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS works (
                source_id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL DEFAULT 'paper',
                document_type TEXT NOT NULL DEFAULT 'unknown',
                title TEXT NOT NULL,
                title_normalized TEXT NOT NULL,
                doi TEXT,
                abstract TEXT NOT NULL DEFAULT '',
                authors TEXT NOT NULL DEFAULT '',
                year INTEGER,
                journal TEXT NOT NULL DEFAULT '',
                publisher TEXT NOT NULL DEFAULT '',
                publication_date TEXT NOT NULL DEFAULT '',
                citation_count INTEGER,
                source_link TEXT NOT NULL DEFAULT '',
                open_access_status TEXT NOT NULL DEFAULT 'unknown',
                pdf_url TEXT NOT NULL DEFAULT '',
                html_url TEXT NOT NULL DEFAULT '',
                language TEXT NOT NULL DEFAULT '',
                primary_source_api TEXT NOT NULL,
                source_databases_json TEXT NOT NULL DEFAULT '[]',
                source_api_ids_json TEXT NOT NULL DEFAULT '{}',
                field_sources_json TEXT NOT NULL DEFAULT '{}',
                first_collected_at TEXT NOT NULL,
                last_collected_at TEXT NOT NULL,
                relevance_score REAL NOT NULL DEFAULT 0,
                relevance_band TEXT NOT NULL DEFAULT 'low',
                relevance_reasons_json TEXT NOT NULL DEFAULT '[]',
                topic_relevance_score REAL NOT NULL DEFAULT 0,
                metadata_evidence_likelihood_score REAL NOT NULL DEFAULT 0,
                access_score REAL NOT NULL DEFAULT 0,
                priority_tier TEXT NOT NULL DEFAULT 'M',
                needs_fulltext_check INTEGER NOT NULL DEFAULT 1,
                pipeline_status TEXT NOT NULL DEFAULT 'screened_candidate',
                topic_positive_reasons_json TEXT NOT NULL DEFAULT '[]',
                topic_negative_reasons_json TEXT NOT NULL DEFAULT '[]',
                evidence_reasons_json TEXT NOT NULL DEFAULT '[]',
                priority_tier_reason TEXT NOT NULL DEFAULT '',
                screening_rule_version TEXT NOT NULL DEFAULT '',
                dedup_rule_version TEXT NOT NULL DEFAULT '',
                scored_at TEXT NOT NULL DEFAULT '',
                source_snapshot_id TEXT NOT NULL DEFAULT '',
                dedup_status TEXT NOT NULL DEFAULT 'unique',
                dedup_reasons_json TEXT NOT NULL DEFAULT '[]',
                conflict_reasons_json TEXT NOT NULL DEFAULT '[]',
                screening_class TEXT NOT NULL DEFAULT 'background_reference',
                pdf_status TEXT NOT NULL DEFAULT '',
                pdf_path TEXT NOT NULL DEFAULT '',
                extraction_status TEXT NOT NULL DEFAULT 'needs_review',
                review_status TEXT NOT NULL DEFAULT 'pending_human_review',
                notes TEXT NOT NULL DEFAULT '',
                created_run_id TEXT NOT NULL,
                updated_run_id TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_works_doi
                ON works(doi) WHERE doi IS NOT NULL AND doi <> '';
            CREATE INDEX IF NOT EXISTS idx_works_title_normalized ON works(title_normalized);
            CREATE INDEX IF NOT EXISTS idx_works_year ON works(year);
            CREATE INDEX IF NOT EXISTS idx_works_relevance ON works(relevance_band, relevance_score DESC);

            CREATE TABLE IF NOT EXISTS work_source_records (
                source_api TEXT NOT NULL,
                external_id TEXT NOT NULL,
                source_id TEXT NOT NULL REFERENCES works(source_id),
                source_database TEXT NOT NULL DEFAULT '',
                source_url TEXT NOT NULL DEFAULT '',
                raw_path TEXT NOT NULL DEFAULT '',
                normalized_json TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                first_seen_run_id TEXT NOT NULL,
                last_seen_run_id TEXT NOT NULL,
                PRIMARY KEY (source_api, external_id)
            );
            CREATE INDEX IF NOT EXISTS idx_work_source_records_source_id ON work_source_records(source_id);

            CREATE TABLE IF NOT EXISTS api_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL REFERENCES collection_runs(run_id),
                source_api TEXT NOT NULL,
                request_kind TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                returned_count INTEGER NOT NULL DEFAULT 0,
                raw_path TEXT NOT NULL DEFAULT '',
                collected_at TEXT NOT NULL,
                error TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS run_queries (
                run_id TEXT NOT NULL REFERENCES collection_runs(run_id),
                query_id TEXT NOT NULL,
                query_text TEXT NOT NULL,
                requested_limit INTEGER NOT NULL,
                api_total INTEGER,
                returned_count INTEGER NOT NULL,
                request_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                error TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (run_id, query_id)
            );

            CREATE TABLE IF NOT EXISTS dedup_decision_log (
                decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL REFERENCES collection_runs(run_id),
                incoming_source_api TEXT NOT NULL,
                incoming_external_id TEXT NOT NULL DEFAULT '',
                incoming_doi TEXT NOT NULL DEFAULT '',
                incoming_title TEXT NOT NULL DEFAULT '',
                resolved_source_id TEXT NOT NULL DEFAULT '',
                related_source_id TEXT NOT NULL DEFAULT '',
                decision TEXT NOT NULL,
                match_type TEXT NOT NULL,
                similarity REAL,
                dedup_reasons_json TEXT NOT NULL DEFAULT '[]',
                conflict_reasons_json TEXT NOT NULL DEFAULT '[]',
                dedup_rule_version TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_dedup_decision_run ON dedup_decision_log(run_id);
            CREATE INDEX IF NOT EXISTS idx_dedup_decision_review ON dedup_decision_log(decision, match_type);
            """
        )
        work_columns = {
            str(row["name"])
            for row in self.connection.execute("PRAGMA table_info(works)").fetchall()
        }
        work_additions = {
            "document_type": "TEXT NOT NULL DEFAULT 'unknown'",
            "topic_relevance_score": "REAL NOT NULL DEFAULT 0",
            "metadata_evidence_likelihood_score": "REAL NOT NULL DEFAULT 0",
            "access_score": "REAL NOT NULL DEFAULT 0",
            "priority_tier": "TEXT NOT NULL DEFAULT 'M'",
            "needs_fulltext_check": "INTEGER NOT NULL DEFAULT 1",
            "pipeline_status": "TEXT NOT NULL DEFAULT 'screened_candidate'",
            "topic_positive_reasons_json": "TEXT NOT NULL DEFAULT '[]'",
            "topic_negative_reasons_json": "TEXT NOT NULL DEFAULT '[]'",
            "evidence_reasons_json": "TEXT NOT NULL DEFAULT '[]'",
            "priority_tier_reason": "TEXT NOT NULL DEFAULT ''",
            "screening_rule_version": "TEXT NOT NULL DEFAULT ''",
            "dedup_rule_version": "TEXT NOT NULL DEFAULT ''",
            "scored_at": "TEXT NOT NULL DEFAULT ''",
            "source_snapshot_id": "TEXT NOT NULL DEFAULT ''",
            "dedup_status": "TEXT NOT NULL DEFAULT 'unique'",
            "dedup_reasons_json": "TEXT NOT NULL DEFAULT '[]'",
            "conflict_reasons_json": "TEXT NOT NULL DEFAULT '[]'",
        }
        for name, definition in work_additions.items():
            if name not in work_columns:
                self.connection.execute(f"ALTER TABLE works ADD COLUMN {name} {definition}")
        source_columns = {
            str(row["name"])
            for row in self.connection.execute("PRAGMA table_info(work_source_records)").fetchall()
        }
        if "source_database" not in source_columns:
            self.connection.execute(
                "ALTER TABLE work_source_records ADD COLUMN source_database TEXT NOT NULL DEFAULT ''"
            )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_works_priority ON works(priority_tier, topic_relevance_score DESC)"
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_works_document_type ON works(document_type)"
        )
        self.connection.commit()

    def start_run(self, run_id: str, config: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT INTO collection_runs(run_id, started_at, status, config_json) VALUES (?, ?, 'running', ?)",
            (run_id, utc_now(), json_dumps(config)),
        )
        self.connection.commit()

    def finish_run(self, run_id: str, status: str, summary: dict[str, Any], error_message: str = "") -> None:
        self.connection.execute(
            "UPDATE collection_runs SET completed_at = ?, status = ?, summary_json = ?, error_message = ? WHERE run_id = ?",
            (utc_now(), status, json_dumps(summary), error_message, run_id),
        )
        self.connection.commit()

    def record_response(self, run_id: str, response: ApiResponse) -> None:
        self.connection.execute(
            """
            INSERT INTO api_requests(
                run_id, source_api, request_kind, status_code, returned_count,
                raw_path, collected_at, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                response.source_api,
                response.request_kind,
                response.status_code,
                response.returned_count,
                response.raw_path,
                response.collected_at,
                response.error,
            ),
        )
        self.connection.commit()

    def record_query(
        self,
        run_id: str,
        query_id: str,
        query_text: str,
        requested_limit: int,
        api_total: int | None,
        returned_count: int,
        request_count: int,
        status: str,
        error: str = "",
    ) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO run_queries(
                run_id, query_id, query_text, requested_limit, api_total,
                returned_count, request_count, status, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, query_id, query_text, requested_limit, api_total, returned_count, request_count, status, error),
        )
        self.connection.commit()

    def count_works(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM works").fetchone()[0])

    def dedup_corpus_summary(self) -> dict[str, int]:
        raw_source_record_count = int(
            self.connection.execute("SELECT COUNT(*) FROM work_source_records").fetchone()[0]
        )
        group_row = self.connection.execute(
            """
            SELECT COUNT(*) AS merge_group_count,
                   COALESCE(SUM(source_count - 1), 0) AS merged_source_record_count
            FROM (
                SELECT source_id,COUNT(*) AS source_count
                FROM work_source_records
                GROUP BY source_id
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()
        possible_duplicate_count = int(
            self.connection.execute(
                "SELECT COUNT(*) FROM works WHERE dedup_status='needs_review'"
            ).fetchone()[0]
        )
        return {
            "raw_source_record_count": raw_source_record_count,
            "canonical_work_count": self.count_works(),
            "merge_group_count": int(group_row[0]),
            "merged_source_record_count": int(group_row[1]),
            "possible_duplicate_count": possible_duplicate_count,
        }

    def import_legacy_csv(self, path: Path, run_id: str, scorer: RelevanceScorer) -> int:
        if self.count_works() or not path.exists() or path.stat().st_size == 0:
            return 0
        count = 0
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                title = (row.get("title") or row.get("source_title") or "").strip()
                if not title:
                    continue
                source_id = (row.get("source_id") or "").strip()
                is_manual = bool(source_id and not source_id.startswith("LIT_"))
                source_api = "manual_registry" if is_manual else "csv_restore"
                work = NormalizedWork(
                    source_api=source_api,
                    external_id=source_id or row.get("doi_or_patent_no") or title,
                    manual_source_id=source_id,
                    title=title,
                    source_type=(row.get("source_type") or "paper").strip(),
                    document_type=(row.get("document_type") or "").strip(),
                    source_database=(row.get("source_database") or "manual_registry").strip(),
                    doi=normalize_doi(row.get("doi_or_patent_no") or row.get("doi")),
                    abstract=(row.get("abstract") or "").strip(),
                    authors=self._split_authors(row.get("authors_or_assignee") or row.get("authors") or ""),
                    year=self._to_int(row.get("year") or row.get("publication_year")),
                    journal=(row.get("journal") or row.get("publication_venue") or row.get("venue") or "").strip(),
                    publisher=(row.get("publisher") or "").strip(),
                    publication_date=(row.get("publication_date") or "").strip(),
                    citation_count=self._to_int(row.get("citation_count")),
                    source_url=(row.get("source_link") or row.get("source_url") or "").strip(),
                    open_access_status=(row.get("open_access_status") or "unknown").strip(),
                    pdf_url=(row.get("pdf_url") or "").strip(),
                    html_url=(row.get("html_url") or "").strip(),
                    language=(row.get("language") or "").strip(),
                    collected_at=(row.get("collection_time") or utc_now()).strip(),
                    screening_class=(row.get("screening_class") or "").strip(),
                    pdf_status=(row.get("pdf_status") or "").strip(),
                    pdf_path=(row.get("pdf_path") or row.get("local_file_path") or "").strip(),
                    extraction_status=(row.get("extraction_status") or "needs_review").strip(),
                    review_status=(row.get("review_status") or "pending_human_review").strip(),
                    notes=(row.get("notes") or "").strip(),
                )
                self.upsert_work(work, run_id, "", scorer)
                count += 1
        return count

    def upsert_work(
        self,
        work: NormalizedWork,
        run_id: str,
        raw_path: str,
        scorer: RelevanceScorer,
    ) -> UpsertResult:
        work.doi = normalize_doi(work.doi)
        work.title = " ".join(work.title.split())
        if not work.document_type or work.document_type == "unknown":
            work.document_type = scorer.classify_document_type(work.title, work.source_type, work.document_type)
        title_normalized = normalize_title(work.title)
        if not work.collected_at:
            work.collected_at = utc_now()
        decision = self._find_match(work, title_normalized)
        source_id = decision.source_id
        if not title_normalized and source_id:
            existing_title = self.connection.execute(
                "SELECT title FROM works WHERE source_id = ?", (source_id,)
            ).fetchone()
            work.title = str(existing_title[0])
            title_normalized = normalize_title(work.title)
        if not title_normalized:
            raise ValueError("Cannot store an unmatched work without a title")
        if source_id is None:
            source_id = work.manual_source_id or stable_source_id(work.doi, work.title, work.year)
            if self.connection.execute("SELECT 1 FROM works WHERE source_id = ?", (source_id,)).fetchone():
                source_id = stable_source_id("", f"{work.title}|{work.external_id}", work.year)
            self._insert_work(source_id, work, title_normalized, run_id, scorer)
            dedup_status = "needs_review" if decision.decision == "review_required" else "unique"
            self.connection.execute(
                "UPDATE works SET dedup_status = ?, dedup_reasons_json = ?, conflict_reasons_json = ?, dedup_rule_version = ? WHERE source_id = ?",
                (
                    dedup_status,
                    json_dumps(decision.dedup_reasons),
                    json_dumps(decision.conflict_reasons),
                    self.dedup_rule_version,
                    source_id,
                ),
            )
            self._upsert_source_record(source_id, work, raw_path, run_id)
            self._refresh_source_provenance(source_id)
            self._log_dedup_decision(run_id, work, source_id, decision)
            self.connection.commit()
            return UpsertResult(
                source_id=source_id,
                action="inserted",
                match_type=decision.match_type,
                changed_fields=[],
                dedup_status=dedup_status,
                similarity=decision.similarity,
                related_source_id=decision.related_source_id,
                dedup_reasons=decision.dedup_reasons,
                conflict_reasons=decision.conflict_reasons,
            )

        row = dict(self.connection.execute("SELECT * FROM works WHERE source_id = ?", (source_id,)).fetchone())
        changed = self._merge_values(row, work)
        row["title_normalized"] = normalize_title(row["title"])
        row["last_collected_at"] = max(row["last_collected_at"], work.collected_at)
        row["updated_run_id"] = run_id
        score = self._score_row(row, scorer)
        field_sources = json.loads(row["field_sources_json"] or "{}")
        self._apply_score(row, score)
        if field_sources.get("screening_class") != "manual_registry":
            if row["screening_class"] != score.screening_class:
                changed.append("screening_class")
            row["screening_class"] = score.screening_class
        elif row.get("screening_class"):
            row["pipeline_status"] = row["screening_class"]
        row["dedup_status"] = "auto_merged"
        row["dedup_reasons_json"] = json_dumps(decision.dedup_reasons)
        row["conflict_reasons_json"] = json_dumps(decision.conflict_reasons)
        row["dedup_rule_version"] = self.dedup_rule_version
        if not row["pdf_status"] and row["pdf_url"]:
            row["pdf_status"] = "legal_url_found"
            changed.append("pdf_status")
        self._update_work_row(row)
        source_record_changed = self._upsert_source_record(source_id, work, raw_path, run_id)
        self._refresh_source_provenance(source_id)
        self._log_dedup_decision(run_id, work, source_id, decision)
        self.connection.commit()
        if source_record_changed and "source_provenance" not in changed:
            changed.append("source_provenance")
        return UpsertResult(
            source_id=source_id,
            action="updated" if changed else "unchanged",
            match_type=decision.match_type,
            changed_fields=sorted(set(changed)),
            dedup_status="auto_merged",
            similarity=decision.similarity,
            related_source_id=decision.related_source_id,
            dedup_reasons=decision.dedup_reasons,
            conflict_reasons=decision.conflict_reasons,
        )

    def _find_match(self, work: NormalizedWork, title_normalized: str) -> MatchDecision:
        if work.external_id:
            row = self.connection.execute(
                "SELECT r.source_id, w.doi FROM work_source_records r JOIN works w ON w.source_id = r.source_id WHERE r.source_api = ? AND r.external_id = ?",
                (work.source_api, work.external_id),
            ).fetchone()
            if row:
                conflicts = ["external_id_same_but_doi_changed"] if self._conflicting_dois(work.doi, row["doi"]) else []
                return MatchDecision(
                    source_id=str(row["source_id"]),
                    match_type="external_id",
                    decision="auto_merge",
                    similarity=1.0,
                    dedup_reasons=["same_provider_external_id"],
                    conflict_reasons=conflicts,
                )
        if work.doi:
            row = self.connection.execute("SELECT source_id FROM works WHERE doi = ?", (work.doi,)).fetchone()
            if row:
                return MatchDecision(
                    source_id=str(row[0]),
                    match_type="doi",
                    decision="auto_merge",
                    similarity=1.0,
                    dedup_reasons=["normalized_doi_exact"],
                )
        exact_rows = self.connection.execute(
            "SELECT source_id, title_normalized, year, doi, document_type, authors, journal FROM works WHERE title_normalized = ?",
            (title_normalized,),
        ).fetchall()
        review_candidate: MatchDecision | None = None
        for row in exact_rows:
            evaluated = self._evaluate_title_candidate(work, title_normalized, row, 1.0, "title_exact")
            if evaluated.decision == "auto_merge":
                return evaluated
            review_candidate = evaluated
        if len(title_normalized) < self.title_min_length:
            return review_candidate or MatchDecision(
                None, "new", "new", dedup_reasons=["short_title_no_fuzzy_match"]
            )
        if work.year:
            candidates = self.connection.execute(
                "SELECT source_id, title_normalized, year, doi, document_type, authors, journal FROM works WHERE year IS NULL OR year BETWEEN ? AND ?",
                (work.year - 1, work.year + 1),
            ).fetchall()
        else:
            candidates = self.connection.execute(
                "SELECT source_id, title_normalized, year, doi, document_type, authors, journal FROM works"
            ).fetchall()
        best_auto: MatchDecision | None = None
        best_review = review_candidate
        for candidate in candidates:
            if str(candidate["title_normalized"]) == title_normalized:
                continue
            similarity = self._title_similarity(title_normalized, candidate["title_normalized"])
            if similarity < self.review_threshold:
                continue
            evaluated = self._evaluate_title_candidate(work, title_normalized, candidate, similarity, "title_fuzzy")
            if evaluated.decision == "auto_merge" and (
                best_auto is None or (evaluated.similarity or 0) > (best_auto.similarity or 0)
            ):
                best_auto = evaluated
            elif evaluated.decision == "review_required" and (
                best_review is None or (evaluated.similarity or 0) > (best_review.similarity or 0)
            ):
                best_review = evaluated
        return best_auto or best_review or MatchDecision(
            None, "new", "new", dedup_reasons=["no_duplicate_candidate"]
        )

    def _evaluate_title_candidate(
        self,
        work: NormalizedWork,
        title_normalized: str,
        candidate: sqlite3.Row,
        similarity: float,
        match_type: str,
    ) -> MatchDecision:
        related_id = str(candidate["source_id"])
        conflicts: list[str] = []
        reasons = [f"title_similarity:{similarity:.4f}"]
        if self._conflicting_dois(work.doi, candidate["doi"]):
            conflicts.append("doi_conflict_review")
        if len(title_normalized) < self.title_min_length:
            conflicts.append("short_title_review")
        if not self._years_compatible(work.year, candidate["year"]):
            conflicts.append("publication_year_conflict")
        if not self._document_types_compatible(work.document_type, candidate["document_type"]):
            conflicts.append("document_type_or_version_relation_review")
        author_match, venue_match = self._author_or_venue_match(work, candidate)
        if author_match:
            reasons.append("first_author_match")
        if venue_match:
            reasons.append("venue_match")
        if not (author_match or venue_match):
            conflicts.append("missing_first_author_or_venue_confirmation")
        if similarity >= self.similarity_threshold and not conflicts:
            reasons.append("conservative_title_auto_merge")
            return MatchDecision(related_id, match_type, "auto_merge", similarity, related_id, reasons, [])
        return MatchDecision(
            source_id=None,
            match_type="doi_conflict_review" if "doi_conflict_review" in conflicts else "possible_duplicate",
            decision="review_required",
            similarity=similarity,
            related_source_id=related_id,
            dedup_reasons=reasons,
            conflict_reasons=conflicts,
        )

    def _insert_work(
        self,
        source_id: str,
        work: NormalizedWork,
        title_normalized: str,
        run_id: str,
        scorer: RelevanceScorer,
    ) -> None:
        score = scorer.score(
            work.title,
            work.abstract,
            source_type=work.source_type,
            raw_document_type=work.document_type,
            doi=work.doi,
            pdf_url=work.pdf_url,
            html_url=work.html_url,
            pdf_path=work.pdf_path,
        )
        is_manual = work.source_api == "manual_registry"
        screening_class = work.screening_class if is_manual and work.screening_class else score.screening_class
        pdf_status = work.pdf_status or ("legal_url_found" if work.pdf_url else "not_checked")
        values = self._incoming_values(work)
        field_sources = {
            key: work.source_api
            for key, value in values.items()
            if not self._is_empty(value)
            and not (key == "open_access_status" and str(value).lower() == "unknown")
        }
        row: dict[str, Any] = {
            "source_id": source_id,
            "source_type": work.source_type or "paper",
            "document_type": score.document_type,
            "title": work.title,
            "title_normalized": title_normalized,
            "doi": work.doi or None,
            "abstract": work.abstract,
            "authors": "; ".join(work.authors),
            "year": work.year,
            "journal": work.journal,
            "publisher": work.publisher,
            "publication_date": work.publication_date,
            "citation_count": work.citation_count,
            "source_link": work.source_url,
            "open_access_status": work.open_access_status or "unknown",
            "pdf_url": work.pdf_url,
            "html_url": work.html_url,
            "language": work.language,
            "primary_source_api": work.source_api,
            "source_databases_json": "[]",
            "source_api_ids_json": "{}",
            "field_sources_json": json_dumps(field_sources),
            "first_collected_at": work.collected_at,
            "last_collected_at": work.collected_at,
            "screening_class": screening_class,
            "pdf_status": pdf_status,
            "pdf_path": work.pdf_path,
            "extraction_status": work.extraction_status or "needs_review",
            "review_status": work.review_status or "pending_human_review",
            "notes": work.notes,
            "created_run_id": run_id,
            "updated_run_id": run_id,
            "dedup_status": "unique",
            "dedup_reasons_json": "[]",
            "conflict_reasons_json": "[]",
            "dedup_rule_version": self.dedup_rule_version,
        }
        self._apply_score(row, score)
        if is_manual and work.screening_class:
            row["pipeline_status"] = work.screening_class
        columns = list(row)
        self.connection.execute(
            f"INSERT INTO works({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
            [row[column] for column in columns],
        )

    def _merge_values(self, row: dict[str, Any], work: NormalizedWork) -> list[str]:
        incoming = self._incoming_values(work)
        field_sources = json.loads(row["field_sources_json"] or "{}")
        changed: list[str] = []
        for field in WORK_VALUE_FIELDS:
            new_value = incoming[field]
            old_value = row.get(field)
            if field == "open_access_status" and str(new_value).lower() == "unknown":
                continue
            if self._is_empty(new_value):
                continue
            if field == "doi" and old_value and normalize_doi(old_value) != normalize_doi(new_value):
                continue
            current_source = field_sources.get(field, row.get("primary_source_api", ""))
            should_replace = self._is_empty(old_value) or (
                field == "open_access_status" and str(old_value).lower() == "unknown"
            )
            if not should_replace and new_value != old_value:
                new_priority = self._priority(work.source_api, field)
                old_priority = self._priority(current_source, field)
                should_replace = new_priority >= old_priority
                if field == "abstract" and len(str(new_value)) > len(str(old_value)) * 1.25:
                    should_replace = new_priority + 10 >= old_priority
            if should_replace and new_value != old_value:
                row[field] = new_value
                field_sources[field] = work.source_api
                changed.append(field)
        row["field_sources_json"] = json_dumps(field_sources)
        return changed

    def _update_work_row(self, row: dict[str, Any]) -> None:
        update_fields = [
            "document_type", "title", "title_normalized", "doi", "abstract", "authors", "year", "journal",
            "publisher", "publication_date", "citation_count", "source_link",
            "open_access_status", "pdf_url", "html_url", "language", "field_sources_json",
            "last_collected_at", "relevance_score", "relevance_band", "relevance_reasons_json",
            "topic_relevance_score", "metadata_evidence_likelihood_score", "access_score",
            "priority_tier", "needs_fulltext_check", "pipeline_status",
            "topic_positive_reasons_json", "topic_negative_reasons_json", "evidence_reasons_json",
            "priority_tier_reason", "screening_rule_version", "dedup_rule_version", "scored_at",
            "source_snapshot_id", "dedup_status", "dedup_reasons_json", "conflict_reasons_json",
            "screening_class", "pdf_status", "pdf_path", "extraction_status", "review_status",
            "notes", "updated_run_id",
        ]
        sql = "UPDATE works SET " + ", ".join(f"{field} = ?" for field in update_fields) + " WHERE source_id = ?"
        self.connection.execute(sql, [row[field] for field in update_fields] + [row["source_id"]])

    def _score_row(self, row: dict[str, Any], scorer: RelevanceScorer):
        return scorer.score(
            str(row.get("title", "")),
            str(row.get("abstract", "")),
            source_type=str(row.get("source_type", "paper")),
            raw_document_type=str(row.get("document_type", "")),
            doi=str(row.get("doi") or ""),
            pdf_url=str(row.get("pdf_url", "")),
            html_url=str(row.get("html_url", "")),
            pdf_path=str(row.get("pdf_path", "")),
        )

    def _apply_score(self, row: dict[str, Any], score: Any) -> None:
        row["document_type"] = score.document_type
        row["relevance_score"] = score.score
        row["relevance_band"] = score.band
        row["relevance_reasons_json"] = json_dumps(score.reasons)
        row["topic_relevance_score"] = score.topic_relevance_score
        row["metadata_evidence_likelihood_score"] = score.metadata_evidence_likelihood_score
        row["access_score"] = score.access_score
        row["priority_tier"] = score.priority_tier
        row["needs_fulltext_check"] = int(score.needs_fulltext_check)
        row["pipeline_status"] = score.pipeline_status
        row["topic_positive_reasons_json"] = json_dumps(score.topic_positive_reasons)
        row["topic_negative_reasons_json"] = json_dumps(score.topic_negative_reasons)
        row["evidence_reasons_json"] = json_dumps(score.evidence_reasons)
        row["priority_tier_reason"] = score.priority_tier_reason
        row["screening_rule_version"] = score.screening_rule_version
        row["dedup_rule_version"] = self.dedup_rule_version
        row["scored_at"] = score.scored_at
        row["source_snapshot_id"] = self._snapshot_id(row)

    @staticmethod
    def _snapshot_id(row: dict[str, Any]) -> str:
        fields = (
            "source_type", "document_type", "title", "doi", "abstract", "authors", "year",
            "journal", "publisher", "publication_date", "pdf_url", "html_url",
        )
        payload = {field: row.get(field) for field in fields}
        return "SNAP_" + hashlib.sha256(json_dumps(payload).encode("utf-8")).hexdigest()[:20].upper()

    def _log_dedup_decision(
        self,
        run_id: str,
        work: NormalizedWork,
        resolved_source_id: str,
        decision: MatchDecision,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO dedup_decision_log(
                run_id, incoming_source_api, incoming_external_id, incoming_doi, incoming_title,
                resolved_source_id, related_source_id, decision, match_type, similarity,
                dedup_reasons_json, conflict_reasons_json, dedup_rule_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id, work.source_api, work.external_id, work.doi, work.title,
                resolved_source_id, decision.related_source_id, decision.decision, decision.match_type,
                decision.similarity, json_dumps(decision.dedup_reasons),
                json_dumps(decision.conflict_reasons), self.dedup_rule_version, utc_now(),
            ),
        )

    def rescore_all(self, scorer: RelevanceScorer) -> int:
        rows = [dict(row) for row in self.connection.execute("SELECT * FROM works").fetchall()]
        for row in rows:
            score = self._score_row(row, scorer)
            self._apply_score(row, score)
            field_sources = json.loads(row.get("field_sources_json") or "{}")
            if field_sources.get("screening_class") != "manual_registry":
                row["screening_class"] = score.screening_class
            elif row.get("screening_class"):
                row["pipeline_status"] = row["screening_class"]
            self._update_work_row(row)
        self.connection.commit()
        return len(rows)

    def _upsert_source_record(self, source_id: str, work: NormalizedWork, raw_path: str, run_id: str) -> bool:
        external_id = work.external_id or work.doi or stable_source_id("", work.title, work.year)
        existing = self.connection.execute(
            "SELECT source_id, normalized_json, raw_path FROM work_source_records WHERE source_api = ? AND external_id = ?",
            (work.source_api, external_id),
        ).fetchone()
        normalized = work.to_dict()
        normalized.pop("collected_at", None)
        normalized_json = json_dumps(normalized)
        if existing:
            try:
                previous_normalized = json.loads(existing["normalized_json"])
            except json.JSONDecodeError:
                previous_normalized = {}
            previous_normalized.setdefault("source_database", "")
            changed = (
                existing["source_id"] != source_id
                or json_dumps(previous_normalized) != normalized_json
            )
            self.connection.execute(
                """
                UPDATE work_source_records SET source_id = ?, source_database = ?, source_url = ?, raw_path = ?,
                    normalized_json = ?, last_seen_at = ?, last_seen_run_id = ?
                WHERE source_api = ? AND external_id = ?
                """,
                (
                    source_id, work.source_database or work.source_api, work.source_url,
                    raw_path or existing["raw_path"], normalized_json,
                    work.collected_at, run_id, work.source_api, external_id,
                ),
            )
            return changed
        self.connection.execute(
            """
            INSERT INTO work_source_records(
                source_api, external_id, source_id, source_database, source_url, raw_path, normalized_json,
                first_seen_at, last_seen_at, first_seen_run_id, last_seen_run_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                work.source_api, external_id, source_id, work.source_database or work.source_api,
                work.source_url, raw_path, normalized_json,
                work.collected_at, work.collected_at, run_id, run_id,
            ),
        )
        return True

    def _refresh_source_provenance(self, source_id: str) -> None:
        rows = self.connection.execute(
            "SELECT source_api, external_id, source_database FROM work_source_records WHERE source_id = ? ORDER BY source_api, external_id",
            (source_id,),
        ).fetchall()
        databases: list[str] = []
        api_ids: dict[str, list[str]] = {}
        for row in rows:
            api = str(row["source_api"])
            labels = str(row["source_database"] or api).split(";")
            for label in labels:
                label = label.strip()
                if label and label not in databases:
                    databases.append(label)
            api_ids.setdefault(api, []).append(str(row["external_id"]))
        self.connection.execute(
            "UPDATE works SET source_databases_json = ?, source_api_ids_json = ? WHERE source_id = ?",
            (json_dumps(databases), json_dumps(api_ids), source_id),
        )

    def list_dois(self, source_ids: Iterable[str], limit: int) -> list[str]:
        ids = list(dict.fromkeys(source_ids))
        if not ids or limit <= 0:
            return []
        placeholders = ",".join("?" for _ in ids)
        rows = self.connection.execute(
            f"SELECT doi FROM works WHERE source_id IN ({placeholders}) AND doi IS NOT NULL AND doi <> '' AND priority_tier IN ('A','B','M') ORDER BY topic_relevance_score DESC, access_score DESC LIMIT ?",
            [*ids, limit],
        ).fetchall()
        return [str(row[0]) for row in rows]

    def list_dois_missing_source(self, source_api: str, limit: int) -> list[str]:
        """Return prioritized DOIs not yet archived from one enrichment source.

        This makes enrichment safely resumable: a repeated command only selects
        records for which that provider has not produced a normalized source
        record yet. Failed API requests remain eligible for a later retry.
        """

        if limit <= 0:
            return []
        rows = self.connection.execute(
            """
            SELECT w.doi
            FROM works AS w
            WHERE w.doi IS NOT NULL
              AND w.doi <> ''
              AND w.priority_tier IN ('A', 'B', 'M')
              AND NOT EXISTS (
                  SELECT 1
                  FROM work_source_records AS source_record
                  WHERE source_record.source_id = w.source_id
                    AND source_record.source_api = ?
              )
            ORDER BY
                w.topic_relevance_score DESC,
                w.metadata_evidence_likelihood_score DESC,
                w.access_score DESC,
                w.citation_count DESC,
                w.source_id
            LIMIT ?
            """,
            (source_api, limit),
        ).fetchall()
        return [str(row[0]) for row in rows]

    def export_csv(self, path: Path) -> int:
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = self.connection.execute(
            "SELECT * FROM works ORDER BY relevance_score DESC, year DESC, title"
        ).fetchall()
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                item = dict(row)
                writer.writerow(
                    {
                        "source_id": item["source_id"],
                        "source_type": item["source_type"],
                        "document_type": item["document_type"],
                        "title": item["title"],
                        "doi_or_patent_no": item["doi"] or "",
                        "abstract": item["abstract"],
                        "authors_or_assignee": item["authors"],
                        "year": item["year"] or "",
                        "journal": item["journal"],
                        "publisher": item["publisher"],
                        "publication_date": item["publication_date"],
                        "citation_count": "" if item["citation_count"] is None else item["citation_count"],
                        "source_link": item["source_link"],
                        "open_access_status": item["open_access_status"],
                        "pdf_url": item["pdf_url"],
                        "html_url": item["html_url"],
                        "source_database": "; ".join(json.loads(item["source_databases_json"])),
                        "source_api_ids": item["source_api_ids_json"],
                        "collection_time": item["first_collected_at"],
                        "last_updated_at": item["last_collected_at"],
                        "relevance_score": item["relevance_score"],
                        "relevance_band": item["relevance_band"],
                        "relevance_reasons": "; ".join(json.loads(item["relevance_reasons_json"])),
                        "topic_relevance_score": item["topic_relevance_score"],
                        "metadata_evidence_likelihood_score": item["metadata_evidence_likelihood_score"],
                        "access_score": item["access_score"],
                        "priority_tier": item["priority_tier"],
                        "needs_fulltext_check": bool(item["needs_fulltext_check"]),
                        "pipeline_status": item["pipeline_status"],
                        "topic_positive_reasons": "; ".join(json.loads(item["topic_positive_reasons_json"])),
                        "topic_negative_reasons": "; ".join(json.loads(item["topic_negative_reasons_json"])),
                        "evidence_reasons": "; ".join(json.loads(item["evidence_reasons_json"])),
                        "priority_tier_reason": item["priority_tier_reason"],
                        "screening_rule_version": item["screening_rule_version"],
                        "dedup_rule_version": item["dedup_rule_version"],
                        "scored_at": item["scored_at"],
                        "source_snapshot_id": item["source_snapshot_id"],
                        "dedup_status": item["dedup_status"],
                        "dedup_reasons": "; ".join(json.loads(item["dedup_reasons_json"])),
                        "conflict_reasons": "; ".join(json.loads(item["conflict_reasons_json"])),
                        "screening_class": item["screening_class"],
                        "language": item["language"],
                        "pdf_status": item["pdf_status"],
                        "pdf_path": item["pdf_path"],
                        "extraction_status": item["extraction_status"],
                        "review_status": item["review_status"],
                        "notes": item["notes"],
                    }
                )
        return len(rows)

    def summarize_ids(self, source_ids: Iterable[str]) -> dict[str, Any]:
        ids = list(dict.fromkeys(source_ids))
        if not ids:
            return {
                "works": 0, "relevance_distribution": {}, "priority_tier_distribution": {},
                "document_type_distribution": {}, "dedup_status_distribution": {},
                "pdf_links": 0, "html_links": 0, "dedup_review_candidates": 0,
            }
        placeholders = ",".join("?" for _ in ids)
        rows = self.connection.execute(
            f"SELECT relevance_band, COUNT(*) AS count FROM works WHERE source_id IN ({placeholders}) GROUP BY relevance_band",
            ids,
        ).fetchall()
        tier_rows = self.connection.execute(
            f"SELECT priority_tier, COUNT(*) AS count FROM works WHERE source_id IN ({placeholders}) GROUP BY priority_tier",
            ids,
        ).fetchall()
        type_rows = self.connection.execute(
            f"SELECT document_type, COUNT(*) AS count FROM works WHERE source_id IN ({placeholders}) GROUP BY document_type",
            ids,
        ).fetchall()
        dedup_rows = self.connection.execute(
            f"SELECT dedup_status, COUNT(*) AS count FROM works WHERE source_id IN ({placeholders}) GROUP BY dedup_status",
            ids,
        ).fetchall()
        link_row = self.connection.execute(
            f"""
            SELECT COUNT(*) AS works,
                SUM(CASE WHEN pdf_url <> '' THEN 1 ELSE 0 END) AS pdf_links,
                SUM(CASE WHEN html_url <> '' THEN 1 ELSE 0 END) AS html_links,
                SUM(CASE WHEN dedup_status = 'needs_review' THEN 1 ELSE 0 END) AS dedup_review_candidates
            FROM works WHERE source_id IN ({placeholders})
            """,
            ids,
        ).fetchone()
        return {
            "works": int(link_row["works"] or 0),
            "relevance_distribution": {str(row["relevance_band"]): int(row["count"]) for row in rows},
            "priority_tier_distribution": {str(row["priority_tier"]): int(row["count"]) for row in tier_rows},
            "document_type_distribution": {str(row["document_type"]): int(row["count"]) for row in type_rows},
            "dedup_status_distribution": {str(row["dedup_status"]): int(row["count"]) for row in dedup_rows},
            "pdf_links": int(link_row["pdf_links"] or 0),
            "html_links": int(link_row["html_links"] or 0),
            "dedup_review_candidates": int(link_row["dedup_review_candidates"] or 0),
        }

    def latest_report(self, run_id: str | None = None) -> dict[str, Any] | None:
        if run_id:
            row = self.connection.execute("SELECT * FROM collection_runs WHERE run_id = ?", (run_id,)).fetchone()
        else:
            row = self.connection.execute("SELECT * FROM collection_runs ORDER BY started_at DESC LIMIT 1").fetchone()
        if not row:
            return None
        result = dict(row)
        result["config"] = json.loads(result.pop("config_json"))
        result["summary"] = json.loads(result.pop("summary_json"))
        result["queries"] = [
            dict(item)
            for item in self.connection.execute(
                "SELECT * FROM run_queries WHERE run_id = ? ORDER BY query_id", (result["run_id"],)
            ).fetchall()
        ]
        return result

    @staticmethod
    def _incoming_values(work: NormalizedWork) -> dict[str, Any]:
        return {
            "title": work.title,
            "document_type": work.document_type,
            "doi": work.doi or None,
            "abstract": work.abstract,
            "authors": "; ".join(work.authors),
            "year": work.year,
            "journal": work.journal,
            "publisher": work.publisher,
            "publication_date": work.publication_date,
            "citation_count": work.citation_count,
            "source_link": work.source_url,
            "open_access_status": work.open_access_status,
            "pdf_url": work.pdf_url,
            "html_url": work.html_url,
            "language": work.language,
            "screening_class": work.screening_class,
            "pdf_status": work.pdf_status,
            "pdf_path": work.pdf_path,
            "extraction_status": work.extraction_status,
            "review_status": work.review_status,
            "notes": work.notes,
        }

    @staticmethod
    def _priority(source_api: str, field: str) -> int:
        if source_api == "csv_restore":
            return 15
        return FIELD_PRIORITY.get(field, {}).get(source_api, 10)

    @staticmethod
    def _is_empty(value: Any) -> bool:
        return value is None or value == "" or value == []

    @staticmethod
    def _years_compatible(left: int | None, right: int | None) -> bool:
        return left is None or right is None or abs(int(left) - int(right)) <= 1

    @staticmethod
    def _conflicting_dois(left: str, right: str | None) -> bool:
        return bool(left and right and normalize_doi(left) != normalize_doi(right))

    @staticmethod
    def _title_similarity(left: str, right: str) -> float:
        sequence = SequenceMatcher(None, left, right).ratio()
        left_tokens, right_tokens = set(left.split()), set(right.split())
        union = left_tokens | right_tokens
        jaccard = len(left_tokens & right_tokens) / len(union) if union else 0.0
        token_sort = SequenceMatcher(None, " ".join(sorted(left_tokens)), " ".join(sorted(right_tokens))).ratio()
        return 0.7 * max(sequence, token_sort) + 0.3 * jaccard

    @staticmethod
    def _document_types_compatible(left: str, right: str) -> bool:
        left = (left or "unknown").strip().lower()
        right = (right or "unknown").strip().lower()
        return left == right or left in {"", "unknown"} or right in {"", "unknown"}

    @staticmethod
    def _author_or_venue_match(work: NormalizedWork, candidate: sqlite3.Row) -> tuple[bool, bool]:
        incoming_author = normalize_title(work.authors[0].split()[-1]) if work.authors and work.authors[0].split() else ""
        stored_authors = str(candidate["authors"] or "").split(";", 1)[0].strip().split()
        stored_author = normalize_title(stored_authors[-1]) if stored_authors else ""
        author_match = bool(incoming_author and stored_author and incoming_author == stored_author)
        incoming_venue = normalize_title(work.journal)
        stored_venue = normalize_title(candidate["journal"])
        venue_match = bool(incoming_venue and stored_venue and incoming_venue == stored_venue)
        return author_match, venue_match

    @staticmethod
    def _split_authors(value: str) -> list[str]:
        separator = ";" if ";" in value else "|"
        return [item.strip() for item in value.split(separator) if item.strip()]

    @staticmethod
    def _to_int(value: Any) -> int | None:
        try:
            return int(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None
