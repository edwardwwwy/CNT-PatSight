from __future__ import annotations

import csv
import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from scripts.io_utils import atomic_write_json, replace_with_retry
from scripts.fetch_fulltext.html_inspection import inspect_html
from scripts.fetch_fulltext.models import ArtifactRecord, FetchResult, MetadataRecord
from scripts.fetch_fulltext.pipeline import FulltextPipeline, sniff_type
from scripts.fetch_fulltext.storage import FulltextStore
from scripts.parse_fulltext.extractor import (
    PARSER_VERSION,
    build_candidate_spans,
    detect_heading,
    label_scientific_reports_frontmatter,
    normalize_section_name,
    segment_pages,
    assess_parse_quality,
)
from scripts.parse_fulltext.models import PageText, TextSection
from scripts.parse_fulltext.pipeline import ParsePipeline
from scripts.parse_fulltext.storage import CandidateStore


NOW = "2026-01-01T00:00:00Z"


class AtomicPublishTests(unittest.TestCase):
    def test_atomic_json_uses_unique_temporary_file_and_cleans_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "state.json"
            atomic_write_json(target, {"status": "ready"})
            self.assertEqual(
                json.loads(target.read_text(encoding="utf-8")),
                {"status": "ready"},
            )
            self.assertEqual(list(Path(directory).glob("*.part")), [])

    def test_transient_windows_replace_lock_is_retried(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory) / "value.csv.part"
            target = Path(directory) / "value.csv"
            temporary.write_text("new", encoding="utf-8")
            target.write_text("old", encoding="utf-8")
            real_replace = os.replace
            attempts = 0

            def transient_replace(source: Path, destination: Path) -> None:
                nonlocal attempts
                attempts += 1
                if attempts < 3:
                    raise PermissionError(13, "transient reader lock")
                real_replace(source, destination)

            with patch("scripts.io_utils.os.replace", side_effect=transient_replace):
                replace_with_retry(temporary, target, attempts=4)
            self.assertEqual(target.read_text(encoding="utf-8"), "new")
            self.assertEqual(attempts, 3)


class HtmlInspectionTests(unittest.TestCase):
    def test_fulltext_html_and_pdf_link_detection(self) -> None:
        body = (
            "<html><head><meta name='citation_pdf_url' content='/paper.pdf'></head><body><article>"
            "<h1>Paper</h1><h2>Abstract</h2><p>" + "carbon nanotube " * 400 + "</p>"
            "<h2>Introduction</h2><p>intro</p><h2>Experimental</h2><p>methods</p>"
            "<h2>Results and Discussion</h2><p>results</p><h2>References</h2><p>refs</p>"
            "</article></body></html>"
        ).encode()
        result = inspect_html(body, "https://example.test/article", "text/html; charset=utf-8")
        self.assertTrue(result.is_likely_fulltext)
        self.assertEqual(result.pdf_links, ["https://example.test/paper.pdf"])

    def test_landing_page_is_not_fulltext(self) -> None:
        result = inspect_html(b"<html><body><h1>Paper title</h1><p>Abstract only.</p></body></html>", "https://example.test")
        self.assertFalse(result.is_likely_fulltext)

    def test_content_sniffing(self) -> None:
        self.assertEqual(sniff_type(b"%PDF-1.7\n", "application/octet-stream"), "pdf")
        self.assertEqual(sniff_type(b"<!doctype html><html>", "text/plain"), "html")


class FulltextStoreTests(unittest.TestCase):
    def test_missing_doi_is_normalized_for_artifact_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fulltext.sqlite3"
            with FulltextStore(path) as store:
                record = ArtifactRecord(
                    "S0", None, "No DOI", "pdf", "https://x/no-doi.pdf", "", "failed",
                    "http_404", "", 0, "", 404, "test", "unknown", "", NOW, NOW, NOW,
                )
                fulltext_id = store.upsert_artifact(record)
                row = store.connection.execute(
                    "SELECT doi FROM fulltext_source WHERE fulltext_id=?", (fulltext_id,)
                ).fetchone()
                self.assertEqual(row["doi"], "")

    def test_success_is_not_downgraded_by_later_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fulltext.sqlite3"
            with FulltextStore(path) as store:
                success = ArtifactRecord("S1", "10/x", "Title", "pdf", "https://x/p.pdf", "x.pdf", "success", "", "abc", 3, "application/pdf", 200, "test", "fulltext", "ok", NOW, NOW, NOW)
                failure = ArtifactRecord("S1", "10/x", "Title", "pdf", "https://x/p.pdf", "", "failed", "http_500", "", 0, "", 500, "test", "unknown", "", NOW, NOW, NOW)
                fulltext_id = store.upsert_artifact(success)
                store.upsert_artifact(failure)
                row = store.connection.execute("SELECT * FROM fulltext_source WHERE fulltext_id=?", (fulltext_id,)).fetchone()
                self.assertEqual(row["fetch_status"], "success")
                self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM fulltext_source").fetchone()[0], 1)

    def test_coverage_has_one_row_per_metadata_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with FulltextStore(root / "db.sqlite3") as store:
                records = [MetadataRecord("S1", "10/x", "One"), MetadataRecord("S2", "10/y", "Two")]
                store.export(records, root / "source.csv", root / "coverage.csv")
                with (root / "coverage.csv").open(encoding="utf-8-sig", newline="") as handle:
                    self.assertEqual(len(list(csv.DictReader(handle))), 2)

    def test_queue_sync_supports_abcd_production_lanes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with FulltextStore(root / "fulltext.sqlite3") as store:
                now = NOW
                rows = []
                for index, (tier, lane) in enumerate((("A", "A"), ("B", "B"), ("C", "C"), ("M", "D")), start=1):
                    rows.append(
                        {
                            "queue_id": f"Q{index}", "source_id": f"S{index}", "work_id": f"S{index}",
                            "title": f"Title {index}", "doi": None if index == 1 else "", "priority_tier": tier,
                            "production_lane": lane,
                            "queue_priority": index, "preferred_format": "landing_page",
                            "candidate_url": "", "url_source": "", "access_type": "landing_page_only",
                            "rule_version": "v1", "created_at": now, "updated_at": now,
                        }
                    )
                self.assertEqual(store.sync_queue(rows), 4)
                self.assertEqual(store.queued_source_ids(), ["S1", "S2", "S3", "S4"])
                self.assertEqual(
                    store.connection.execute(
                        "SELECT doi FROM fulltext_acquisition_queue WHERE source_id='S1'"
                    ).fetchone()[0],
                    "",
                )

    def test_legacy_ab_queue_is_migrated_without_losing_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.sqlite3"
            connection = sqlite3.connect(path)
            connection.execute(
                """CREATE TABLE fulltext_acquisition_queue(
                       queue_id TEXT PRIMARY KEY,source_id TEXT UNIQUE,work_id TEXT,title TEXT,
                       doi TEXT DEFAULT '',priority_tier TEXT CHECK(priority_tier IN ('A','B')),
                       queue_priority INTEGER,preferred_format TEXT,download_status TEXT DEFAULT 'queued',
                       max_attempts INTEGER DEFAULT 3,rule_version TEXT,created_at TEXT,updated_at TEXT)"""
            )
            connection.execute(
                "INSERT INTO fulltext_acquisition_queue VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("Q1", "S1", "S1", "Title", "", "B", 1, "pdf", "validated", 3, "v1", NOW, NOW),
            )
            connection.commit()
            connection.close()
            with FulltextStore(path) as store:
                row = store.connection.execute(
                    "SELECT priority_tier,production_lane,download_status FROM fulltext_acquisition_queue"
                ).fetchone()
                self.assertEqual(tuple(row), ("B", "B", "validated"))

    def test_retry_pending_remains_claimable_and_terminal_reset_clears_control_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fulltext.sqlite3"
            row = {
                "queue_id": "Q1",
                "source_id": "S1",
                "work_id": "S1",
                "title": "Title",
                "doi": "10/test",
                "priority_tier": "A",
                "production_lane": "A",
                "queue_priority": 1,
                "preferred_format": "landing_page",
                "candidate_url": "https://doi.org/10/test",
                "url_source": "doi_resolver",
                "access_type": "publisher_page_check",
                "rule_version": "v1",
                "created_at": NOW,
                "updated_at": NOW,
                "max_attempts": 1,
            }
            with FulltextStore(path) as store:
                store.sync_queue([row])
                store.connection.execute(
                    """
                    UPDATE fulltext_acquisition_queue
                    SET download_status='failed_retryable',attempt_count=1,
                        fulltext_status='pending',acquisition_status='retry_pending'
                    WHERE source_id='S1'
                    """
                )
                store.connection.commit()
                self.assertEqual(store.queued_source_ids(), ["S1"])
                store.connection.execute(
                    """
                    UPDATE fulltext_acquisition_queue
                    SET download_status='not_found',fulltext_status='unavailable_legally',
                        acquisition_status='manual_access_required',
                        failure_reason='no_legal_fulltext_found'
                    WHERE source_id='S1'
                    """
                )
                store.connection.commit()
                store.sync_queue([{**row, "reset_terminal": True, "updated_at": "2026-01-02T00:00:00Z"}])
                reset = store.connection.execute(
                    """
                    SELECT download_status,fulltext_status,acquisition_status,failure_reason,attempt_count
                    FROM fulltext_acquisition_queue WHERE source_id='S1'
                    """
                ).fetchone()
                self.assertEqual(tuple(reset), ("queued", "pending", "queued", "", 0))

    def test_new_queue_rule_reopens_legacy_terminal_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fulltext.sqlite3"
            row = {
                "queue_id": "Q1",
                "source_id": "S1",
                "work_id": "S1",
                "title": "Title",
                "doi": "10/test",
                "priority_tier": "A",
                "production_lane": "A",
                "queue_priority": 1,
                "preferred_format": "landing_page",
                "candidate_url": "https://doi.org/10/test",
                "url_source": "doi_resolver",
                "access_type": "publisher_page_check",
                "rule_version": "legacy_rule",
                "created_at": NOW,
                "updated_at": NOW,
            }
            with FulltextStore(path) as store:
                store.sync_queue([row])
                store.connection.execute(
                    """
                    UPDATE fulltext_acquisition_queue
                    SET download_status='paywalled',fulltext_status='unavailable',
                        acquisition_status='legacy_terminal',
                        failure_reason='html_landing_page_not_fulltext',attempt_count=3
                    WHERE source_id='S1'
                    """
                )
                store.connection.commit()
                store.sync_queue([{**row, "rule_version": "new_legal_fallback_rule"}])
                reset = store.connection.execute(
                    """
                    SELECT download_status,fulltext_status,acquisition_status,
                           failure_reason,attempt_count,rule_version
                    FROM fulltext_acquisition_queue WHERE source_id='S1'
                    """
                ).fetchone()
                self.assertEqual(
                    tuple(reset),
                    (
                        "queued",
                        "pending",
                        "queued",
                        "",
                        0,
                        "new_legal_fallback_rule",
                    ),
                )


class SafeAcquisitionRegressionTests(unittest.TestCase):
    class StubDownloader:
        def __init__(self, responses: dict[str, FetchResult]):
            self.responses = responses

        def fetch(self, url: str) -> FetchResult:
            return self.responses[url]

    class EventStore:
        def record_event(self, *args: object, **kwargs: object) -> None:
            return None

    def test_unpaywall_all_oa_locations_are_candidates_with_pdfs_first(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pipeline = FulltextPipeline(
                root, root / "metadata.sqlite3", root / "fulltext.sqlite3",
                root / "pdf", root / "html", root / "reports", root / "source.csv",
                root / "coverage.csv", root / ".env", use_unpaywall=True,
            )
            pipeline.email = "reviewer@example.test"
            api_url = "https://api.unpaywall.org/v2/10/test?email=reviewer%40example.test"
            payload = {
                "best_oa_location": {
                    "url_for_pdf": "https://blocked.test/paper.pdf",
                    "url_for_landing_page": "https://blocked.test/paper",
                    "license": "cc-by",
                },
                "oa_locations": [
                    {
                        "url_for_pdf": "https://repository.test/paper.pdf",
                        "url_for_landing_page": "https://repository.test/item",
                        "license": "cc-by-nc",
                    }
                ],
            }
            pipeline.downloader = self.StubDownloader(
                {api_url: FetchResult(api_url, api_url, 200, "application/json", json.dumps(payload).encode())}
            )
            candidates = pipeline._candidates(
                MetadataRecord("S1", "10/test", "Title", open_access_status="gold"),
                self.EventStore(),
                "RUN1",
            )
            urls = [candidate.url for candidate in candidates]
            self.assertIn("https://repository.test/paper.pdf", urls)
            self.assertLess(
                urls.index("https://repository.test/paper.pdf"),
                urls.index("https://blocked.test/paper"),
            )

    def test_only_verified_legal_oa_candidate_rows_are_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_csv = root / "verified.csv"
            candidate_csv.write_text(
                "source_id,fulltext_url,fulltext_type,url_source,access_type,license,verification_status\n"
                "S1,https://repository.test/paper.pdf,pdf,institutional_repository,legal_oa,cc-by,verified\n"
                "S1,https://invalid.test/paper.pdf,pdf,manual,unknown,,verified\n"
                "S1,https://unchecked.test/paper.pdf,pdf,manual,legal_oa,,pending\n",
                encoding="utf-8",
            )
            pipeline = FulltextPipeline(
                root, root / "metadata.sqlite3", root / "fulltext.sqlite3",
                root / "pdf", root / "html", root / "reports", root / "source.csv",
                root / "coverage.csv", root / ".env", use_unpaywall=False,
                verified_candidates_csv=candidate_csv,
            )
            urls = [
                candidate.url
                for candidate in pipeline._candidates(
                    MetadataRecord("S1", "", "Title", open_access_status="gold"),
                    self.EventStore(),
                    "RUN1",
                )
            ]
            self.assertEqual(urls, ["https://repository.test/paper.pdf"])

    def test_legal_candidates_follow_required_source_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_csv = root / "verified.csv"
            candidate_csv.write_text(
                "source_id,fulltext_url,fulltext_type,url_source,access_type,license,"
                "verification_status,acquisition_step,version_type,version_relation,related_source_id\n"
                "S1,https://repository.test/paper.pdf,pdf,HAL,legal_oa,,verified,5,"
                "published,same_record,\n",
                encoding="utf-8",
            )
            pipeline = FulltextPipeline(
                root, root / "metadata.sqlite3", root / "fulltext.sqlite3",
                root / "pdf", root / "html", root / "reports", root / "source.csv",
                root / "coverage.csv", root / ".env", use_unpaywall=False,
                verified_candidates_csv=candidate_csv,
            )
            provider_records = [
                {
                    "source_api": "unpaywall",
                    "normalized_json": json.dumps(
                        {
                            "open_access_status": "gold",
                            "pdf_url": "https://unpaywall.test/paper.pdf",
                        }
                    ),
                },
                {
                    "source_api": "openalex",
                    "normalized_json": json.dumps(
                        {
                            "open_access_status": "green",
                            "pdf_url": "https://openalex.test/paper.pdf",
                        }
                    ),
                },
                {
                    "source_api": "semantic_scholar",
                    "normalized_json": json.dumps(
                        {
                            "open_access_status": "open",
                            "pdf_url": "https://semanticscholar.test/paper.pdf",
                        }
                    ),
                },
            ]
            candidates = pipeline._candidates(
                MetadataRecord(
                    "S1",
                    "10/test",
                    "Title",
                    source_link="https://publisher.test/article",
                    provider_records_json=json.dumps(provider_records),
                ),
                self.EventStore(),
                "RUN1",
            )
            self.assertEqual(
                [(candidate.acquisition_step, candidate.url) for candidate in candidates],
                [
                    (2, "https://unpaywall.test/paper.pdf"),
                    (3, "https://openalex.test/paper.pdf"),
                    (3, "https://semanticscholar.test/paper.pdf"),
                    (4, "https://doi.org/10/test"),
                    (4, "https://publisher.test/article"),
                    (5, "https://repository.test/paper.pdf"),
                ],
            )

    def test_unrelated_preprint_without_explicit_version_relation_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_csv = root / "verified.csv"
            candidate_csv.write_text(
                "source_id,fulltext_url,fulltext_type,url_source,access_type,license,"
                "verification_status,version_type,version_relation,related_source_id\n"
                "S1,https://preprint.test/unsafe.pdf,pdf,ChemRxiv,legal_oa,,verified,"
                "preprint,same_record,\n"
                "S1,https://preprint.test/linked.pdf,pdf,ChemRxiv,legal_oa,,verified,"
                "preprint,preprint_of,S1_PREPRINT\n",
                encoding="utf-8",
            )
            pipeline = FulltextPipeline(
                root, root / "metadata.sqlite3", root / "fulltext.sqlite3",
                root / "pdf", root / "html", root / "reports", root / "source.csv",
                root / "coverage.csv", root / ".env", use_unpaywall=False,
                verified_candidates_csv=candidate_csv,
            )
            candidates = pipeline._candidates(
                MetadataRecord("S1", "", "Title"),
                self.EventStore(),
                "RUN1",
            )
            self.assertEqual([candidate.url for candidate in candidates], ["https://preprint.test/linked.pdf"])
            self.assertEqual(candidates[0].version_relation, "preprint_of")
            self.assertEqual(candidates[0].related_source_id, "S1_PREPRINT")

    def _metadata_db(self, root: Path, rows: list[tuple[str, str]]) -> Path:
        db = root / "metadata.sqlite3"
        with closing(sqlite3.connect(db)) as connection:
            connection.execute(
                """
                CREATE TABLE works(
                    source_id TEXT,title TEXT,abstract TEXT,doi TEXT,pdf_url TEXT,html_url TEXT,pdf_path TEXT,
                    priority_tier TEXT,topic_relevance_score REAL,metadata_evidence_likelihood_score REAL,
                    access_score REAL,citation_count INTEGER,open_access_status TEXT,
                    field_sources_json TEXT,screening_rule_version TEXT
                )
                """
            )
            for source_id, url in rows:
                connection.execute(
                    "INSERT INTO works VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (source_id, f"CNT synthesis {source_id}", "", "", url, "", "", "A", 9, 4, 3, 10, "gold", '{"pdf_url":"unpaywall"}', "v1"),
                )
            connection.commit()
        return db

    def _pipeline(self, root: Path, metadata: Path) -> FulltextPipeline:
        return FulltextPipeline(
            root, metadata, root / "fulltext.sqlite3", root / "pdf", root / "html", root / "reports",
            root / "source.csv", root / "coverage.csv", root / ".env", use_unpaywall=False,
            queue_csv=root / "queue.csv",
        )

    def test_valid_oa_pdf_is_validated_and_duplicate_content_is_reused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            urls = [("S1", "https://example.test/one.pdf"), ("S2", "https://example.test/two.pdf")]
            metadata = self._metadata_db(root, urls)
            content = b"%PDF-1.7\nshared body\n%%EOF"
            pipeline = self._pipeline(root, metadata)
            pipeline.downloader = self.StubDownloader(
                {
                    url: FetchResult(url, url, 200, "application/pdf", content)
                    for _, url in urls
                }
            )
            summary = pipeline.run(from_queue=True)
            self.assertEqual(summary["downloaded_pdf"], 1)
            self.assertEqual(len(list((root / "pdf").glob("*.pdf"))), 1)
            with FulltextStore(root / "fulltext.sqlite3") as store:
                paths = {row[0] for row in store.connection.execute("SELECT local_path FROM fulltext_source WHERE fetch_status='success'")}
                self.assertEqual(len(paths), 1)
                statuses = {row[0] for row in store.connection.execute("SELECT download_status FROM fulltext_acquisition_queue")}
                self.assertEqual(statuses, {"validated"})

    def test_html_fake_pdf_and_404_have_explicit_terminal_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            urls = [("S1", "https://example.test/fake.pdf"), ("S2", "https://example.test/missing.pdf")]
            metadata = self._metadata_db(root, urls)
            pipeline = self._pipeline(root, metadata)
            pipeline.downloader = self.StubDownloader(
                {
                    urls[0][1]: FetchResult(urls[0][1], urls[0][1], 200, "application/pdf", b"<html>not a PDF</html>"),
                    urls[1][1]: FetchResult(urls[1][1], urls[1][1], 404, "text/html", b"", "http_404"),
                }
            )
            pipeline.run(from_queue=True)
            with FulltextStore(root / "fulltext.sqlite3") as store:
                statuses = {
                    row["source_id"]: row["download_status"]
                    for row in store.connection.execute("SELECT source_id,download_status FROM fulltext_acquisition_queue")
                }
                self.assertEqual(statuses, {"S1": "not_pdf", "S2": "not_found"})
                terminal = {
                    row["source_id"]: (
                        row["fulltext_status"],
                        row["acquisition_status"],
                        row["failure_reason"],
                        row["manual_access_url"],
                    )
                    for row in store.connection.execute(
                        """
                        SELECT source_id,fulltext_status,acquisition_status,failure_reason,manual_access_url
                        FROM fulltext_acquisition_queue
                        """
                    )
                }
                self.assertEqual(
                    terminal,
                    {
                        "S1": (
                            "unavailable_legally",
                            "manual_access_required",
                            "no_legal_fulltext_found",
                            "",
                        ),
                        "S2": (
                            "unavailable_legally",
                            "manual_access_required",
                            "no_legal_fulltext_found",
                            "",
                        ),
                    },
                )
                failure_steps = {
                    row["source_id"]: int(row["acquisition_step"])
                    for row in store.connection.execute(
                        """
                        SELECT source_id,acquisition_step
                        FROM fulltext_source
                        WHERE fetch_status IN ('failed','skipped')
                        """
                    )
                }
                self.assertEqual(failure_steps, {"S1": 2, "S2": 2})

    def test_candidate_limit_does_not_prematurely_mark_manual_access(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            metadata = self._metadata_db(root, [("S1", "https://example.test/blocked.pdf")])
            with closing(sqlite3.connect(metadata)) as connection:
                connection.execute("UPDATE works SET doi='10/test' WHERE source_id='S1'")
                connection.commit()
            pipeline = FulltextPipeline(
                root, metadata, root / "fulltext.sqlite3", root / "pdf", root / "html",
                root / "reports", root / "source.csv", root / "coverage.csv", root / ".env",
                use_unpaywall=False, queue_csv=root / "queue.csv", max_candidates_per_source=1,
            )
            pipeline.downloader = self.StubDownloader(
                {
                    "https://example.test/blocked.pdf": FetchResult(
                        "https://example.test/blocked.pdf",
                        "https://example.test/blocked.pdf",
                        403,
                        "text/html",
                        b"",
                        "http_403",
                    ),
                    "https://doi.org/10/test": FetchResult(
                        "https://doi.org/10/test",
                        "https://publisher.test/article",
                        404,
                        "text/html",
                        b"",
                        "http_404",
                    ),
                }
            )
            pipeline.run(from_queue=True)
            with FulltextStore(root / "fulltext.sqlite3") as store:
                row = store.connection.execute(
                    """
                    SELECT download_status,fulltext_status,acquisition_status,failure_reason
                    FROM fulltext_acquisition_queue WHERE source_id='S1'
                    """
                ).fetchone()
                self.assertEqual(
                    tuple(row),
                    ("failed_retryable", "pending", "retry_pending", "http_403"),
                )
            pipeline.run(from_queue=True)
            with FulltextStore(root / "fulltext.sqlite3") as store:
                row = store.connection.execute(
                    """
                    SELECT download_status,fulltext_status,acquisition_status,failure_reason,manual_access_url
                    FROM fulltext_acquisition_queue WHERE source_id='S1'
                    """
                ).fetchone()
                self.assertEqual(
                    tuple(row),
                    (
                        "not_found",
                        "unavailable_legally",
                        "manual_access_required",
                        "no_legal_fulltext_found",
                        "https://doi.org/10/test",
                    ),
                )

    def test_blank_pdf_is_classified_scanned_and_requires_ocr(self) -> None:
        quality, ocr_required = assess_parse_quality("pdf", 8, 120, 0, False)
        self.assertEqual(quality, "scanned")
        self.assertEqual(ocr_required, 1)


class ExtractionRuleTests(unittest.TestCase):
    def test_section_normalization(self) -> None:
        self.assertEqual(normalize_section_name("2.2 Catalyst preparation"), "catalyst_preparation")
        self.assertEqual(
            normalize_section_name("2.1 Preparation and characterization of Fe-Mo/MgO catalysts"),
            "catalyst_preparation",
        )
        self.assertEqual(normalize_section_name("2.2 Synthesis and characterization of CNTs"), "cvd_growth")
        self.assertEqual(normalize_section_name("Materials and Methods"), "methods")
        self.assertEqual(detect_heading("3. Experimental procedure")[1], "experimental")
        self.assertEqual(detect_heading("Article Info Abstract")[1], "abstract")
        self.assertIsNone(detect_heading("results"))

    def test_sections_and_candidate_spans_are_reviewable(self) -> None:
        pages = [
            PageText(
                1,
                "Abstract\nMethane CVD was studied.\n1. Experimental\n"
                "Fe/MgO catalyst was calcined at 700 °C for 2 h. Methane at 100 sccm and H2 at 50 sccm flowed through a quartz reactor.\n"
                "2. Characterization\nTEM and Raman ID/IG were used. The CNT yield was 3.2 g/g catalyst.",
            )
        ]
        sections = segment_pages("S1", "FT1", "hash", "Title", "", pages, [], "test")
        spans = build_candidate_spans(sections)
        types = {span.span_type for span in spans}
        self.assertTrue({"catalyst", "process", "gas", "yield", "characterization"}.issubset(types))
        self.assertTrue(all(section.needs_review == 1 for section in sections))
        self.assertTrue(all(span.needs_review == 1 for span in spans))

    def test_repeated_text_in_distinct_sections_has_distinct_span_ids(self) -> None:
        text = "Fe catalyst methane growth at 750 C for 30 min produced CNT yield of 3 g/g catalyst."
        sections = [
            TextSection("SEC_A", "S1", "FT1", "hash", "Experimental", "experimental", 1, text, 1, 1, "test"),
            TextSection("SEC_B", "S1", "FT1", "hash", "Table 1", "tables", 2, text, 2, 2, "test"),
        ]
        spans = build_candidate_spans(sections)
        self.assertGreater(len(spans), 1)
        self.assertEqual(len({span.span_id for span in spans}), len(spans))

    def test_wrapped_numbered_headings_are_joined(self) -> None:
        pages = [
            PageText(
                2,
                "2. Experimental section\n"
                "2.1. Preparation and characterization of Fe-Mo/\n"
                "MgO catalysts\nCatalyst preparation details.\n"
                "2.2. Synthesis and characterization of CNTs\nGrowth details.",
            )
        ]
        sections = segment_pages("S1", "FT1", "hash", "Title", "", pages, [], "test")
        normalized = [section.section_name_normalized for section in sections]
        self.assertIn("catalyst_preparation", normalized)
        self.assertIn("cvd_growth", normalized)

    def test_scientific_reports_unlabelled_abstract_is_marked(self) -> None:
        class FakePage:
            def extract_text_lines(self, return_chars: bool = False):
                texts = [
                    "www.nature.com/scientificreports",
                    "OPEN Paper title",
                    "Title continued",
                    "First Author & Corresponding Author*",
                    "Abstract sentence one.",
                    "Abstract sentence two.",
                    "Abstract sentence three.",
                    "Abstract sentence four.",
                    "Abstract sentence five.",
                    "Introduction sentence.",
                    "More body text.",
                    "Affiliation text.",
                ]
                rows = []
                top = 240.0
                for index, text in enumerate(texts):
                    if index == 9:
                        top += 20.0
                    rows.append({"text": text, "top": top, "bottom": top + 9.0})
                    top += 11.0
                return rows

        text = "www.nature.com/scientificreports\nOPEN Paper title\nFirst Author & Corresponding Author*"
        labeled, applied = label_scientific_reports_frontmatter(FakePage(), text)
        self.assertTrue(applied)
        self.assertIn("\nAbstract\nAbstract sentence one.", labeled)
        self.assertIn("\nIntroduction\nIntroduction sentence.", labeled)


class PipelineIntegrationTests(unittest.TestCase):
    def _metadata_db(self, root: Path, pdf_path: str = "") -> Path:
        db = root / "metadata.sqlite3"
        with closing(sqlite3.connect(db)) as connection:
            connection.execute(
                "CREATE TABLE works(source_id TEXT,title TEXT,abstract TEXT,doi TEXT,pdf_url TEXT,html_url TEXT,pdf_path TEXT)"
            )
            connection.execute(
                "INSERT INTO works VALUES (?,?,?,?,?,?,?)",
                ("S1", "Methane CVD CNT paper", "Abstract", "10/test", "", "", pdf_path),
            )
            connection.commit()
        return db

    def test_local_pdf_is_registered_without_copying(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            local = root / "original.pdf"
            local.write_bytes(b"%PDF-1.4\noriginal")
            metadata = self._metadata_db(root, "original.pdf")
            pipeline = FulltextPipeline(
                root, metadata, root / "fulltext.sqlite3", root / "pdf", root / "html", root / "reports",
                root / "source.csv", root / "coverage.csv", root / ".env", use_unpaywall=False,
            )
            first = pipeline.run()
            second = pipeline.run()
            self.assertEqual(first["available_sources"], 1)
            self.assertEqual(second["local_pdf_reused"], 1)
            self.assertEqual(local.read_bytes(), b"%PDF-1.4\noriginal")
            self.assertEqual(list((root / "pdf").glob("*.pdf")), [])

    def test_html_parse_pipeline_and_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            metadata = self._metadata_db(root)
            html = root / "paper.html"
            html.write_text(
                "<html><body><h2>Experimental</h2><p>Fe catalyst was calcined at 700 °C. Methane flow was 100 sccm in a CVD reactor.</p>"
                "<h2>Characterization</h2><p>TEM and Raman were used and CNT yield was 2 g/g catalyst.</p></body></html>",
                encoding="utf-8",
            )
            with FulltextStore(root / "fulltext.sqlite3") as store:
                record = ArtifactRecord("S1", "10/test", "Methane CVD CNT paper", "html", "https://example.test", "paper.html", "success", "", "hash", html.stat().st_size, "text/html", 200, "test", "fulltext", "", NOW, NOW, NOW, 1)
                store.upsert_artifact(record)
                store.refresh_primary("S1")
            pipeline = ParsePipeline(
                root, metadata, root / "fulltext.sqlite3", root / "candidate.sqlite3",
                root / "raw_text", root / "parsed_text", root / "sections.csv", root / "spans.csv",
                root / "status.csv", root / "parse_reports",
            )
            first = pipeline.run()
            second = pipeline.run()
            self.assertEqual(first["parsed_sources"], 1)
            self.assertGreater(first["span_rows"], 0)
            self.assertEqual(second["cache_hits"], 1)
            package = root / "parsed_text" / "S1.parsed.json"
            payload = json.loads(package.read_text(encoding="utf-8"))
            self.assertEqual(payload["source_id"], "S1")
            self.assertIn("full_text", payload)
            self.assertIn("sections", payload)
            parse_report = payload["parse_report"]
            self.assertEqual(parse_report["source_id"], "S1")
            self.assertEqual(parse_report["parser_version"], PARSER_VERSION)
            with CandidateStore(root / "candidate.sqlite3") as store:
                self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM parse_source_status").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
