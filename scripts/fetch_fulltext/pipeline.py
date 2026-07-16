from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import sqlite3
import time
import uuid
from collections import deque
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from scripts.collect_metadata.settings import load_dotenv

from .html_inspection import inspect_html
from .models import ArtifactRecord, FetchResult, MetadataRecord, UrlCandidate
from .storage import FulltextStore


QUEUE_RULE_VERSION = "fulltext_queue_v1"
OPEN_ACCESS_STATES = {"open", "gold", "green", "hybrid", "bronze", "diamond"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sniff_type(content: bytes, media_type: str) -> str:
    leading = content[:1024].lstrip().lower()
    if content.startswith(b"%PDF-"):
        return "pdf"
    if b"application/pdf" in media_type.lower().encode("ascii", errors="ignore") and b"%pdf-" in leading:
        return "pdf"
    if leading.startswith((b"<!doctype html", b"<html", b"<?xml")) or b"text/html" in media_type.lower().encode("ascii", errors="ignore"):
        return "html"
    return "unknown"


class Downloader:
    RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}

    def __init__(self, user_agent: str, timeout: int = 30, retries: int = 3, max_bytes: int = 50 * 1024 * 1024):
        self.user_agent = user_agent
        self.timeout = timeout
        self.retries = retries
        self.max_bytes = max_bytes

    def fetch(self, url: str) -> FetchResult:
        if urlsplit(url).scheme not in {"http", "https"}:
            return FetchResult(url, url, 0, "", b"", "unsupported_url_scheme")
        last = FetchResult(url, url, 0, "", b"", "request_not_attempted")
        for attempt in range(1, self.retries + 1):
            try:
                request = Request(
                    url,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "application/pdf,text/html,application/xhtml+xml;q=0.9,*/*;q=0.2",
                    },
                )
                with urlopen(request, timeout=self.timeout) as response:
                    status = int(response.status)
                    media_type = response.headers.get("Content-Type", "")
                    content_length = response.headers.get("Content-Length")
                    if content_length and int(content_length) > self.max_bytes:
                        return FetchResult(url, response.geturl(), status, media_type, b"", "content_length_exceeds_limit")
                    chunks: list[bytes] = []
                    total = 0
                    while True:
                        chunk = response.read(min(1024 * 1024, self.max_bytes - total + 1))
                        if not chunk:
                            break
                        chunks.append(chunk)
                        total += len(chunk)
                        if total > self.max_bytes:
                            return FetchResult(url, response.geturl(), status, media_type, b"", "download_exceeds_limit")
                    return FetchResult(url, response.geturl(), status, media_type, b"".join(chunks), "")
            except HTTPError as exc:
                status = int(exc.code)
                last = FetchResult(url, exc.geturl(), status, exc.headers.get("Content-Type", "") if exc.headers else "", b"", f"http_{status}")
                if status not in self.RETRY_STATUS or attempt >= self.retries:
                    return last
                retry_after = exc.headers.get("Retry-After", "") if exc.headers else ""
                try:
                    delay = min(30.0, float(retry_after))
                except ValueError:
                    delay = min(10.0, 2 ** (attempt - 1) + random.random())
                time.sleep(delay)
            except (URLError, TimeoutError, OSError, ValueError) as exc:
                last = FetchResult(url, url, 0, "", b"", f"{type(exc).__name__}:{exc}")
                if attempt < self.retries:
                    time.sleep(min(10.0, 2 ** (attempt - 1) + random.random()))
        return last


class FulltextPipeline:
    def __init__(
        self,
        root: Path,
        metadata_db: Path,
        fulltext_db: Path,
        pdf_dir: Path,
        html_dir: Path,
        reports_dir: Path,
        source_csv: Path,
        coverage_csv: Path,
        env_file: Path,
        *,
        force: bool = False,
        use_unpaywall: bool = True,
        max_candidates_per_source: int = 10,
        queue_csv: Path | None = None,
        max_queue_attempts: int = 3,
        verified_candidates_csv: Path | None = None,
    ):
        self.root = root
        self.metadata_db = metadata_db
        self.fulltext_db = fulltext_db
        self.pdf_dir = pdf_dir
        self.html_dir = html_dir
        self.reports_dir = reports_dir
        self.source_csv = source_csv
        self.coverage_csv = coverage_csv
        self.force = force
        self.use_unpaywall = use_unpaywall
        self.max_candidates_per_source = max_candidates_per_source
        self.queue_csv = queue_csv or fulltext_db.parent / "fulltext_acquisition_queue.csv"
        self.max_queue_attempts = max(1, max_queue_attempts)
        self.verified_candidates_csv = verified_candidates_csv or fulltext_db.parent / "verified_oa_candidates.csv"
        self.verified_candidates = self._load_verified_candidates(self.verified_candidates_csv)
        load_dotenv(env_file)
        self.email = os.environ.get("UNPAYWALL_EMAIL", "").strip()
        contact = self.email or "contact-not-configured"
        self.downloader = Downloader(f"CNT-PatSight/0.2 fulltext-fetcher ({contact})")
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.html_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def load_metadata(self, source_ids: list[str] | None = None, limit: int | None = None) -> list[MetadataRecord]:
        with closing(sqlite3.connect(self.metadata_db)) as connection:
            connection.row_factory = sqlite3.Row
            columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(works)")}

            def field(name: str, fallback: str = "''") -> str:
                return name if name in columns else f"{fallback} AS {name}"

            select_fields = [
                field("source_id"), field("doi"), field("title"), field("abstract"),
                field("pdf_url"), field("html_url"), field("pdf_path"),
                field("priority_tier"), field("topic_relevance_score", "0"),
                (
                    "metadata_evidence_likelihood_score AS evidence_likelihood_score"
                    if "metadata_evidence_likelihood_score" in columns
                    else "0 AS evidence_likelihood_score"
                ),
                field("access_score", "0"), field("citation_count", "0"),
                field("open_access_status", "'unknown'"), field("field_sources_json", "'{}'"),
                field("screening_rule_version"),
            ]
            sql = f"SELECT {','.join(select_fields)} FROM works"
            params: list[Any] = []
            if source_ids:
                placeholders = ",".join("?" for _ in source_ids)
                sql += f" WHERE source_id IN ({placeholders})"
                params.extend(source_ids)
            sql += " ORDER BY source_id"
            if limit is not None:
                sql += " LIMIT ?"
                params.append(limit)
            return [MetadataRecord(**dict(row)) for row in connection.execute(sql, params).fetchall()]

    def build_queue(self, *, reset_terminal: bool = False) -> dict[str, Any]:
        records = [record for record in self.load_metadata() if record.priority_tier in {"A", "B"}]
        planned: list[tuple[tuple[Any, ...], MetadataRecord, dict[str, Any]]] = []
        now = utc_now()
        for record in records:
            try:
                field_sources = json.loads(record.field_sources_json or "{}")
            except json.JSONDecodeError:
                field_sources = {}
            is_oa = record.open_access_status.strip().lower() in OPEN_ACCESS_STATES
            pdf_source = str(field_sources.get("pdf_url") or "metadata.pdf_url")
            html_source = str(field_sources.get("html_url") or "metadata.html_url")
            if record.pdf_path:
                bucket = 0
                preferred_format = "local_pdf"
                candidate_url = ""
                url_source = "metadata.pdf_path"
                access_type = "local_existing"
                reason = "existing_local_pdf"
            elif is_oa and record.pdf_url:
                bucket = 1 if record.priority_tier == "A" else 3
                preferred_format = "pdf"
                candidate_url = record.pdf_url
                url_source = pdf_source
                access_type = "legal_oa"
                reason = f"tier_{record.priority_tier}_oa_pdf"
            elif is_oa and record.html_url:
                bucket = 2 if record.priority_tier == "A" else 4
                preferred_format = "html"
                candidate_url = record.html_url
                url_source = html_source
                access_type = "legal_oa"
                reason = f"tier_{record.priority_tier}_oa_html"
            else:
                bucket = 5 if record.priority_tier == "A" else 6
                preferred_format = "landing_page"
                candidate_url = record.html_url or (f"https://doi.org/{record.doi}" if record.doi else "")
                url_source = html_source if record.html_url else "doi_resolver"
                access_type = "landing_page_only"
                reason = f"tier_{record.priority_tier}_no_direct_oa_fulltext"
            sort_key = (
                bucket,
                -float(record.topic_relevance_score or 0),
                -float(record.evidence_likelihood_score or 0),
                -int(record.citation_count or 0),
                record.source_id,
            )
            planned.append(
                (
                    sort_key,
                    record,
                    {
                        "preferred_format": preferred_format,
                        "candidate_url": candidate_url,
                        "url_source": url_source,
                        "access_type": access_type,
                        "priority_reason": reason,
                    },
                )
            )
        queue_rows: list[dict[str, Any]] = []
        for priority, (_, record, plan) in enumerate(sorted(planned, key=lambda item: item[0]), start=1):
            queue_rows.append(
                {
                    "queue_id": "FQ_" + hashlib.sha256(record.source_id.encode("utf-8")).hexdigest()[:20].upper(),
                    "source_id": record.source_id,
                    "work_id": record.source_id,
                    "title": record.title,
                    "doi": record.doi,
                    "priority_tier": record.priority_tier,
                    "queue_priority": priority,
                    "topic_relevance_score": record.topic_relevance_score,
                    "evidence_likelihood_score": record.evidence_likelihood_score,
                    "citation_count": record.citation_count,
                    "license": "",
                    "download_status": "queued",
                    "max_attempts": self.max_queue_attempts,
                    "rule_version": QUEUE_RULE_VERSION,
                    "created_at": now,
                    "updated_at": now,
                    "reset_terminal": reset_terminal,
                    **plan,
                }
            )
        with FulltextStore(self.fulltext_db) as store:
            count = store.sync_queue(queue_rows)
            exported = store.export_queue(self.queue_csv)
            summary = store.queue_summary()
        return {
            **summary,
            "synced_rows": count,
            "exported_rows": exported,
            "queue_rule_version": QUEUE_RULE_VERSION,
            "queue_csv_path": self._rel(self.queue_csv),
        }

    def run(
        self,
        source_ids: list[str] | None = None,
        limit: int | None = None,
        *,
        from_queue: bool = False,
    ) -> dict[str, Any]:
        queue_plan: dict[str, Any] = {}
        if from_queue:
            queue_plan = self.build_queue()
            with FulltextStore(self.fulltext_db) as queue_store:
                queued_ids = queue_store.queued_source_ids(None, self.force)
            if source_ids:
                requested = set(source_ids)
                queued_ids = [source_id for source_id in queued_ids if source_id in requested]
            if limit is not None:
                queued_ids = queued_ids[:limit]
            loaded = {record.source_id: record for record in self.load_metadata(queued_ids)}
            records = [loaded[source_id] for source_id in queued_ids if source_id in loaded]
        else:
            records = self.load_metadata(source_ids, limit)
        run_id = f"FT_{utc_now().replace('-','').replace(':','')}_{uuid.uuid4().hex[:6]}"
        counters = {
            "network_requests": 0,
            "cache_hits": 0,
            "local_pdf_reused": 0,
            "downloaded_pdf": 0,
            "downloaded_html": 0,
            "failed_attempts": 0,
        }
        with FulltextStore(self.fulltext_db) as store:
            store.start_run(
                run_id,
                utc_now(),
                {
                    "source_ids": source_ids or [],
                    "limit": limit,
                    "force": self.force,
                    "use_unpaywall": self.use_unpaywall,
                    "max_candidates_per_source": self.max_candidates_per_source,
                    "from_queue": from_queue,
                    "queue_rule_version": QUEUE_RULE_VERSION,
                },
            )
            try:
                for record in records:
                    self._process_record(store, run_id, record, counters)
                if from_queue:
                    queue_ids = store.all_queue_source_ids()
                    all_loaded = {record.source_id: record for record in self.load_metadata(queue_ids)}
                    export_records = [all_loaded[source_id] for source_id in queue_ids if source_id in all_loaded]
                else:
                    export_records = records
                source_rows, coverage_rows = store.export(export_records, self.source_csv, self.coverage_csv)
                coverage = store.coverage_summary(records)
                summary = {
                    "run_id": run_id,
                    "status": "complete",
                    **counters,
                    **coverage,
                    "fulltext_source_rows": source_rows,
                    "coverage_rows": coverage_rows,
                    "database_path": self._rel(self.fulltext_db),
                    "source_csv_path": self._rel(self.source_csv),
                    "coverage_csv_path": self._rel(self.coverage_csv),
                    "queue_csv_path": self._rel(self.queue_csv),
                    "queue_plan": queue_plan,
                    **store.queue_summary(),
                    "completed_at": utc_now(),
                }
                store.export_queue(self.queue_csv)
                store.finish_run(run_id, utc_now(), "complete", summary)
                self._write_report(run_id, summary)
                return summary
            except Exception as exc:
                summary = {"run_id": run_id, "status": "failed", **counters, "error": f"{type(exc).__name__}:{exc}"}
                store.finish_run(run_id, utc_now(), "failed", summary, summary["error"])
                self._write_report(run_id, summary)
                raise

    def _process_record(self, store: FulltextStore, run_id: str, record: MetadataRecord, counters: dict[str, int]) -> None:
        now = utc_now()
        local_path = self._resolve(record.pdf_path)
        if record.pdf_path:
            local_prefix = b""
            if local_path.exists() and local_path.is_file():
                with local_path.open("rb") as handle:
                    local_prefix = handle.read(4096)
            if local_prefix and sniff_type(local_prefix, "application/pdf") == "pdf":
                content_hash = sha256_file(local_path)
                store.upsert_artifact(
                    ArtifactRecord(
                        source_id=record.source_id,
                        doi=record.doi,
                        title=record.title,
                        fulltext_type="local_pdf",
                        fulltext_url="",
                        local_path=self._rel(local_path),
                        fetch_status="success",
                        failure_reason="",
                        content_hash=content_hash,
                        content_bytes=local_path.stat().st_size,
                        media_type="application/pdf",
                        http_status=None,
                        url_source="metadata.pdf_path",
                        content_scope="fulltext",
                        validation_note="existing local PDF registered without copying or modification",
                        created_at=now,
                        updated_at=now,
                        last_checked_at=now,
                    )
                )
                store.record_event(run_id, record.source_id, "register_local_pdf", "success", now, detail=self._rel(local_path))
                counters["local_pdf_reused"] += 1
                store.update_queue_status(
                    record.source_id,
                    "local_existing",
                    now,
                    content_type="application/pdf",
                    local_path=self._rel(local_path),
                    file_size=local_path.stat().st_size,
                    sha256=content_hash,
                    url_source="metadata.pdf_path",
                    access_type="local_existing",
                )
                store.refresh_primary(record.source_id)
                return
            store.upsert_artifact(
                self._failed_record(record, "local_pdf", "", record.pdf_path, "local_pdf_invalid_signature_or_missing", "metadata.pdf_path", now)
            )
            reason = "local_pdf_invalid_signature_or_missing"
            store.record_event(run_id, record.source_id, "register_local_pdf", "failed", now, detail=reason)
            counters["failed_attempts"] += 1

        cached = store.successful_artifacts(record.source_id)
        if cached and not self.force:
            valid = False
            for row in cached:
                path = self._resolve(str(row["local_path"]))
                if path.exists() and sha256_file(path) == row["content_hash"]:
                    valid = True
                    break
            if valid:
                store.record_event(run_id, record.source_id, "reuse_cached_fulltext", "success", now, detail=str(cached[0]["local_path"]))
                counters["cache_hits"] += 1
                primary = cached[0]
                store.update_queue_status(
                    record.source_id,
                    "validated",
                    now,
                    http_status=primary["http_status"],
                    content_type=str(primary["media_type"]),
                    resolved_url=str(primary["fulltext_url"]),
                    local_path=str(primary["local_path"]),
                    file_size=int(primary["content_bytes"]),
                    sha256=str(primary["content_hash"]),
                    url_source=str(primary["url_source"]),
                )
                store.refresh_primary(record.source_id)
                return

        candidates = self._candidates(record, store, run_id)
        store.mark_queue_attempt(record.source_id, now)
        attempt_count, max_attempts = store.queue_attempt_count(record.source_id)
        queue: deque[UrlCandidate] = deque(candidates)
        seen: set[str] = set()
        processed = 0
        pdf_success = False
        last_failure_status = "not_found" if not candidates else "failed_retryable"
        last_failure_reason = "no_legal_oa_or_landing_candidate" if not candidates else "no_successful_fulltext_candidate"
        last_http_status: int | None = None
        last_content_type = ""
        last_resolved_url = ""
        while queue and processed < self.max_candidates_per_source:
            candidate = queue.popleft()
            normalized_url = candidate.url.strip()
            if not normalized_url or normalized_url in seen:
                continue
            seen.add(normalized_url)
            processed += 1
            counters["network_requests"] += 1
            result = self.downloader.fetch(normalized_url)
            now = utc_now()
            store.record_event(
                run_id,
                record.source_id,
                "download_candidate",
                "failed" if result.error else "success",
                now,
                url=normalized_url,
                detail=result.error or f"http={result.status_code}; media_type={result.media_type}; bytes={len(result.body)}",
            )
            if result.error:
                store.upsert_artifact(
                    self._failed_record(record, candidate.expected_type, normalized_url, "", result.error, candidate.url_source, now, result.status_code, result.media_type)
                )
                counters["failed_attempts"] += 1
                last_http_status = result.status_code
                last_content_type = result.media_type
                last_resolved_url = result.final_url
                last_failure_reason = result.error
                if result.status_code in {401, 403}:
                    last_failure_status = "blocked"
                elif result.status_code in {404, 410}:
                    last_failure_status = "not_found"
                elif attempt_count >= max_attempts:
                    last_failure_status = "failed_final"
                else:
                    last_failure_status = "failed_retryable"
                continue
            actual_type = sniff_type(result.body, result.media_type)
            if actual_type == "pdf":
                local, content_hash, reused = self._save_content(store, record.source_id, result.body, "pdf")
                store.upsert_artifact(
                    ArtifactRecord(
                        source_id=record.source_id,
                        doi=record.doi,
                        title=record.title,
                        fulltext_type="pdf",
                        fulltext_url=result.final_url,
                        local_path=local,
                        fetch_status="success",
                        failure_reason="",
                        content_hash=content_hash,
                        content_bytes=len(result.body),
                        media_type=result.media_type or "application/pdf",
                        http_status=result.status_code,
                        url_source=candidate.url_source,
                        content_scope="fulltext",
                        validation_note=f"PDF signature validated; requested_url={normalized_url}; deduplicated_by_hash={reused}",
                        created_at=now,
                        updated_at=now,
                        last_checked_at=now,
                    )
                )
                counters["downloaded_pdf"] += 0 if reused else 1
                store.update_queue_status(
                    record.source_id,
                    "validated",
                    now,
                    http_status=result.status_code,
                    content_type=result.media_type or "application/pdf",
                    resolved_url=result.final_url,
                    local_path=local,
                    file_size=len(result.body),
                    sha256=content_hash,
                    url_source=candidate.url_source,
                    access_type=candidate.access_type,
                    license=candidate.license,
                )
                pdf_success = True
                break
            if actual_type == "html":
                inspection = inspect_html(result.body, result.final_url, result.media_type)
                for link in reversed(inspection.pdf_links):
                    if link not in seen:
                        queue.appendleft(
                            UrlCandidate(
                                link,
                                "pdf",
                                f"{candidate.url_source}:html_discovery",
                                candidate.access_type,
                                candidate.license,
                            )
                        )
                if inspection.is_likely_fulltext:
                    local, content_hash, reused = self._save_content(store, record.source_id, result.body, "html")
                    store.upsert_artifact(
                        ArtifactRecord(
                            source_id=record.source_id,
                            doi=record.doi,
                            title=record.title,
                            fulltext_type="html",
                            fulltext_url=result.final_url,
                            local_path=local,
                            fetch_status="success",
                            failure_reason="",
                            content_hash=content_hash,
                            content_bytes=len(result.body),
                            media_type=result.media_type or "text/html",
                            http_status=result.status_code,
                            url_source=candidate.url_source,
                            content_scope="fulltext",
                            validation_note=inspection.validation_note + f"; requested_url={normalized_url}; deduplicated_by_hash={reused}",
                            created_at=now,
                            updated_at=now,
                            last_checked_at=now,
                        )
                    )
                    counters["downloaded_html"] += 0 if reused else 1
                    store.update_queue_status(
                        record.source_id,
                        "validated",
                        now,
                        http_status=result.status_code,
                        content_type=result.media_type or "text/html",
                        resolved_url=result.final_url,
                        local_path=local,
                        file_size=len(result.body),
                        sha256=content_hash,
                        url_source=candidate.url_source,
                        access_type=(
                            candidate.access_type
                            if candidate.access_type == "legal_oa"
                            else "public_fulltext_license_unknown"
                        ),
                        license=candidate.license,
                    )
                else:
                    store.upsert_artifact(
                        self._failed_record(
                            record,
                            candidate.expected_type,
                            normalized_url,
                            "",
                            "html_landing_page_not_fulltext",
                            candidate.url_source,
                            now,
                            result.status_code,
                            result.media_type,
                            inspection.validation_note,
                            "landing_page",
                        )
                    )
                    counters["failed_attempts"] += 1
                    if candidate.expected_type == "pdf":
                        last_failure_status = "not_pdf"
                        last_failure_reason = "expected_pdf_received_html_landing_page"
                    else:
                        last_failure_status = "paywalled"
                        last_failure_reason = "html_landing_page_not_fulltext"
                    last_http_status = result.status_code
                    last_content_type = result.media_type
                    last_resolved_url = result.final_url
                continue
            store.upsert_artifact(
                self._failed_record(record, candidate.expected_type, normalized_url, "", "unsupported_or_unrecognized_content", candidate.url_source, now, result.status_code, result.media_type)
            )
            counters["failed_attempts"] += 1
            last_failure_status = "not_pdf"
            last_failure_reason = "unsupported_or_unrecognized_content"
            last_http_status = result.status_code
            last_content_type = result.media_type
            last_resolved_url = result.final_url
        store.refresh_primary(record.source_id)
        if not store.successful_artifacts(record.source_id):
            store.update_queue_status(
                record.source_id,
                last_failure_status,
                utc_now(),
                http_status=last_http_status,
                content_type=last_content_type,
                resolved_url=last_resolved_url,
                failure_reason=last_failure_reason,
            )
            store.record_event(run_id, record.source_id, "source_coverage", "failed", utc_now(), detail="no_successful_fulltext_candidate")
        elif pdf_success:
            store.record_event(run_id, record.source_id, "source_coverage", "success", utc_now(), detail="pdf")
        else:
            store.record_event(run_id, record.source_id, "source_coverage", "success", utc_now(), detail="html")

    def _candidates(self, record: MetadataRecord, store: FulltextStore, run_id: str) -> list[UrlCandidate]:
        candidates: list[UrlCandidate] = []
        is_oa = record.open_access_status.strip().lower() in OPEN_ACCESS_STATES
        try:
            field_sources = json.loads(record.field_sources_json or "{}")
        except json.JSONDecodeError:
            field_sources = {}
        if record.pdf_url and is_oa:
            candidates.append(
                UrlCandidate(
                    record.pdf_url,
                    "pdf",
                    str(field_sources.get("pdf_url") or "metadata.pdf_url"),
                    "legal_oa",
                )
            )
        candidates.extend(self.verified_candidates.get(record.source_id, []))
        if self.use_unpaywall and self.email and record.doi:
            api_url = f"https://api.unpaywall.org/v2/{quote(record.doi, safe='/')}?email={quote(self.email)}"
            result = self.downloader.fetch(api_url)
            store.record_event(
                run_id,
                record.source_id,
                "unpaywall_lookup",
                "failed" if result.error else "success",
                utc_now(),
                url="https://api.unpaywall.org/v2/<doi>?email=<redacted>",
                detail=result.error or f"http={result.status_code}",
            )
            if not result.error:
                try:
                    payload = json.loads(result.body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    payload = {}
                best = payload.get("best_oa_location") if isinstance(payload, dict) and isinstance(payload.get("best_oa_location"), dict) else {}
                raw_locations = payload.get("oa_locations", []) if isinstance(payload, dict) else []
                locations: list[tuple[str, dict[str, Any]]] = []
                if best:
                    locations.append(("unpaywall.best_oa_location", best))
                if isinstance(raw_locations, list):
                    locations.extend(
                        (f"unpaywall.oa_locations[{index}]", location)
                        for index, location in enumerate(raw_locations)
                        if isinstance(location, dict)
                    )
                # Try every explicitly licensed OA PDF before any landing page.
                # The nominal "best" location is often bot-blocked while an
                # institutional repository copy in oa_locations remains usable.
                for source, location in locations:
                    if location.get("url_for_pdf"):
                        candidates.append(
                            UrlCandidate(
                                str(location["url_for_pdf"]),
                                "pdf",
                                source,
                                "legal_oa",
                                str(location.get("license") or ""),
                            )
                        )
                for source, location in locations:
                    landing = location.get("url_for_landing_page") or location.get("url")
                    if landing:
                        candidates.append(
                            UrlCandidate(
                                str(landing),
                                "html",
                                source,
                                "legal_oa",
                                str(location.get("license") or ""),
                            )
                        )
        if record.html_url and is_oa:
            candidates.append(
                UrlCandidate(
                    record.html_url,
                    "html",
                    str(field_sources.get("html_url") or "metadata.html_url"),
                    "legal_oa",
                )
            )
        if record.doi:
            candidates.append(UrlCandidate(f"https://doi.org/{record.doi}", "html", "doi_resolver", "landing_page_only"))
        if record.html_url and not is_oa:
            candidates.append(UrlCandidate(record.html_url, "html", str(field_sources.get("html_url") or "metadata.html_url"), "landing_page_only"))
        output: list[UrlCandidate] = []
        seen: set[str] = set()
        for candidate in candidates:
            if candidate.url and candidate.url not in seen:
                seen.add(candidate.url)
                output.append(candidate)
        return output

    @staticmethod
    def _load_verified_candidates(path: Path) -> dict[str, list[UrlCandidate]]:
        output: dict[str, list[UrlCandidate]] = {}
        if not path.exists():
            return output
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                source_id = str(row.get("source_id") or "").strip()
                url = str(row.get("fulltext_url") or "").strip()
                fulltext_type = str(row.get("fulltext_type") or "").strip().lower()
                access_type = str(row.get("access_type") or "").strip().lower()
                verification_status = str(row.get("verification_status") or "").strip().lower()
                if (
                    not source_id
                    or not url
                    or fulltext_type not in {"pdf", "html"}
                    or access_type != "legal_oa"
                    or verification_status != "verified"
                ):
                    continue
                output.setdefault(source_id, []).append(
                    UrlCandidate(
                        url,
                        fulltext_type,
                        str(row.get("url_source") or "verified_oa_candidates"),
                        "legal_oa",
                        str(row.get("license") or ""),
                    )
                )
        return output

    def _save_content(self, store: FulltextStore, source_id: str, content: bytes, extension: str) -> tuple[str, str, bool]:
        content_hash = sha256_bytes(content)
        existing = store.successful_path_for_hash(content_hash)
        if existing and self._resolve(existing).exists():
            return existing, content_hash, True
        directory = self.pdf_dir if extension == "pdf" else self.html_dir
        path = directory / f"{source_id}_{content_hash[:12]}.{extension}"
        if path.exists():
            return self._rel(path), content_hash, True
        temp_path = path.with_suffix(path.suffix + ".part")
        temp_path.write_bytes(content)
        if sha256_file(temp_path) != content_hash:
            temp_path.unlink(missing_ok=True)
            raise OSError("content_hash_mismatch_after_write")
        temp_path.replace(path)
        return self._rel(path), content_hash, False

    def _failed_record(
        self,
        record: MetadataRecord,
        fulltext_type: str,
        url: str,
        local_path: str,
        reason: str,
        url_source: str,
        now: str,
        http_status: int | None = None,
        media_type: str = "",
        validation_note: str = "",
        content_scope: str = "unknown",
    ) -> ArtifactRecord:
        return ArtifactRecord(
            source_id=record.source_id,
            doi=record.doi,
            title=record.title,
            fulltext_type=fulltext_type if fulltext_type in {"pdf", "html", "local_pdf"} else "html",
            fulltext_url=url,
            local_path=local_path,
            fetch_status="failed" if reason != "html_landing_page_not_fulltext" else "skipped",
            failure_reason=reason,
            content_hash="",
            content_bytes=0,
            media_type=media_type,
            http_status=http_status,
            url_source=url_source,
            content_scope=content_scope,
            validation_note=validation_note,
            created_at=now,
            updated_at=now,
            last_checked_at=now,
        )

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
        "coverage: "
        f"available={summary.get('available_sources',0)}/{summary.get('metadata_total',0)}, "
        f"unavailable={summary.get('unavailable_sources',0)}"
    )
    print(f"primary_types: {json.dumps(summary.get('primary_type_distribution',{}), ensure_ascii=False, sort_keys=True)}")
    print(
        "actions: "
        f"local_pdf_reused={summary.get('local_pdf_reused',0)}, cache_hits={summary.get('cache_hits',0)}, "
        f"network_requests={summary.get('network_requests',0)}, downloaded_pdf={summary.get('downloaded_pdf',0)}, "
        f"downloaded_html={summary.get('downloaded_html',0)}, failed_attempts={summary.get('failed_attempts',0)}"
    )
    for item in summary.get("unavailable_detail", []):
        print(f"  unavailable {item['source_id']}: {item['reason']}")
    print(f"coverage_csv: {summary.get('coverage_csv_path','')}")
