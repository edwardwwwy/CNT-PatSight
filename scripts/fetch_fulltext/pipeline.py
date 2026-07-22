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
from pathlib import Path
from typing import Any

from scripts.io_utils import replace_with_retry, unique_part_path, utc_now
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from scripts.collect_metadata.settings import load_dotenv

from .html_inspection import inspect_html
from .models import ArtifactRecord, FetchResult, MetadataRecord, UrlCandidate
from .storage import FulltextStore


QUEUE_RULE_VERSION = "fulltext_queue_v3_legal_fallbacks"
OPEN_ACCESS_STATES = {"open", "gold", "green", "hybrid", "bronze", "diamond"}
PRODUCTION_LANES = {"A": "A", "B": "B", "C": "C", "M": "D"}


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


def request_url(url: str) -> str:
    """Encode spaces/control characters while preserving an already-escaped URL.

    Metadata occasionally contains an otherwise valid legal repository URL
    whose filename has literal spaces.  ``urllib`` rejects such URLs before a
    request is made, so normalize the path/query for transport while retaining
    the original candidate URL in the evidence registry.
    """
    parts = urlsplit(url.strip())
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            quote(parts.path, safe="/%:@!$&'()*+,;=-._~"),
            quote(parts.query, safe="%=&?/:;,+@!$'()*-._~"),
            quote(parts.fragment, safe="%=&?/:;,+@!$'()*-._~"),
        )
    )


class Downloader:
    RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}

    def __init__(self, user_agent: str, timeout: int = 30, retries: int = 3, max_bytes: int = 50 * 1024 * 1024):
        self.user_agent = user_agent
        self.timeout = timeout
        self.retries = retries
        self.max_bytes = max_bytes

    def fetch(self, url: str) -> FetchResult:
        try:
            transport_url = request_url(url)
        except ValueError as exc:
            return FetchResult(url, url, 0, "", b"", f"invalid_url:{exc}")
        if urlsplit(transport_url).scheme not in {"http", "https"}:
            return FetchResult(url, url, 0, "", b"", "unsupported_url_scheme")
        last = FetchResult(url, url, 0, "", b"", "request_not_attempted")
        for attempt in range(1, self.retries + 1):
            try:
                request = Request(
                    transport_url,
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
        self.downloader = Downloader(f"CNT-LitSight/0.2 fulltext-fetcher ({contact})")
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.html_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def load_metadata(self, source_ids: list[str] | None = None, limit: int | None = None) -> list[MetadataRecord]:
        with closing(sqlite3.connect(self.metadata_db)) as connection:
            connection.row_factory = sqlite3.Row
            columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(works)")}
            tables = {str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}

            def field(name: str, fallback: str = "''") -> str:
                return name if name in columns else f"{fallback} AS {name}"

            select_fields = [
                field("source_id"), field("doi"), field("title"), field("abstract"),
                field("source_link"),
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
                (
                    "COALESCE((SELECT GROUP_CONCAT(DISTINCT source_api) FROM work_source_records s "
                    "WHERE s.source_id=works.source_id),'') AS source_providers"
                    if "work_source_records" in tables else "'' AS source_providers"
                ),
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
            records = [MetadataRecord(**dict(row)) for row in connection.execute(sql, params).fetchall()]
            if records and "work_source_records" in tables:
                by_source: dict[str, list[dict[str, str]]] = {record.source_id: [] for record in records}
                placeholders = ",".join("?" for _ in records)
                provider_rows = connection.execute(
                    f"""
                    SELECT source_id,source_api,source_url,source_database,normalized_json
                    FROM work_source_records
                    WHERE source_id IN ({placeholders})
                    ORDER BY source_id,source_api,external_id
                    """,
                    [record.source_id for record in records],
                ).fetchall()
                for provider_row in provider_rows:
                    by_source[str(provider_row["source_id"])].append(
                        {
                            "source_api": str(provider_row["source_api"]),
                            "source_url": str(provider_row["source_url"]),
                            "source_database": str(provider_row["source_database"]),
                            "normalized_json": str(provider_row["normalized_json"]),
                        }
                    )
                for record in records:
                    record.provider_records_json = json.dumps(
                        by_source[record.source_id],
                        ensure_ascii=False,
                        sort_keys=True,
                    )
            return records

    def build_queue(self, *, reset_terminal: bool = False) -> dict[str, Any]:
        all_records = self.load_metadata()
        records: list[MetadataRecord] = []
        deferred_metadata_pending = 0
        for record in all_records:
            if record.priority_tier not in PRODUCTION_LANES:
                continue
            if record.priority_tier == "M" and not self._metadata_enrichment_complete(record):
                deferred_metadata_pending += 1
                continue
            records.append(record)
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
            production_lane = PRODUCTION_LANES[record.priority_tier]
            lane_rank = {"A": 0, "B": 1, "C": 2, "D": 3}[production_lane]
            enrichment_status = (
                "completed_no_abstract_fulltext_gate"
                if record.priority_tier == "M" else "not_required_frozen_screening"
            )
            if record.pdf_path:
                format_rank = 0
                preferred_format = "local_pdf"
                candidate_url = ""
                url_source = "metadata.pdf_path"
                access_type = "local_existing"
                reason = "existing_local_pdf"
            elif is_oa and record.pdf_url:
                format_rank = 1
                preferred_format = "pdf"
                candidate_url = record.pdf_url
                url_source = pdf_source
                access_type = "legal_oa"
                reason = f"tier_{record.priority_tier}_oa_pdf"
            elif is_oa and record.html_url:
                format_rank = 2
                preferred_format = "html"
                candidate_url = record.html_url
                url_source = html_source
                access_type = "legal_oa"
                reason = f"tier_{record.priority_tier}_oa_html"
            else:
                format_rank = 3
                preferred_format = "landing_page"
                candidate_url = record.html_url or (f"https://doi.org/{record.doi}" if record.doi else "")
                url_source = html_source if record.html_url else "doi_resolver"
                access_type = "landing_page_only"
                reason = f"tier_{record.priority_tier}_no_direct_oa_fulltext"
            sort_key = (
                lane_rank,
                format_rank,
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
                        "priority_reason": f"lane_{production_lane}:{reason}",
                        "production_lane": production_lane,
                        "metadata_enrichment_status": enrichment_status,
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
                    "production_lane": plan["production_lane"],
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
                    "fulltext_status": "pending",
                    "acquisition_status": "queued",
                    "publisher_url": self._publisher_url(record),
                    "manual_access_url": "",
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
            "production_lane_counts": {
                lane: sum(1 for row in queue_rows if row["production_lane"] == lane)
                for lane in ("A", "B", "C", "D")
            },
            "deferred_metadata_pending": deferred_metadata_pending,
        }

    @staticmethod
    def _metadata_enrichment_complete(record: MetadataRecord) -> bool:
        providers = {item.strip() for item in record.source_providers.split(",") if item.strip()}
        # Semantic Scholar may legitimately return no record. OpenAlex,
        # Crossref and Unpaywall coverage plus DOI identity is the deterministic
        # completion gate before an M record enters production lane D.
        return bool(record.doi) and {"openalex", "crossref", "unpaywall"}.issubset(providers)

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
                        acquisition_step=1,
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
                    fulltext_status="available",
                    acquisition_status="local_existing",
                    publisher_url=self._publisher_url(record),
                    manual_access_url=self._manual_access_url(record),
                )
                store.refresh_primary(record.source_id)
                return
            store.upsert_artifact(
                self._failed_record(
                    record,
                    "local_pdf",
                    "",
                    record.pdf_path,
                    "local_pdf_invalid_signature_or_missing",
                    "metadata.pdf_path",
                    now,
                    acquisition_step=1,
                )
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
                    fulltext_status="available",
                    acquisition_status="reused_verified_fulltext",
                    publisher_url=self._publisher_url(record),
                    manual_access_url=self._manual_access_url(record),
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
                    self._failed_record(
                        record,
                        candidate.expected_type,
                        normalized_url,
                        "",
                        result.error,
                        candidate.url_source,
                        now,
                        result.status_code,
                        result.media_type,
                        acquisition_step=candidate.acquisition_step,
                        version_type=candidate.version_type,
                        version_relation=candidate.version_relation,
                        related_source_id=candidate.related_source_id,
                    )
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
                        acquisition_step=candidate.acquisition_step,
                        version_type=candidate.version_type,
                        version_relation=candidate.version_relation,
                        related_source_id=candidate.related_source_id,
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
                    fulltext_status="available",
                    acquisition_status="acquired_legal_fulltext",
                    publisher_url=self._publisher_url(record),
                    manual_access_url=self._manual_access_url(record),
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
                                candidate.acquisition_step,
                                candidate.version_type,
                                candidate.version_relation,
                                candidate.related_source_id,
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
                            acquisition_step=candidate.acquisition_step,
                            version_type=candidate.version_type,
                            version_relation=candidate.version_relation,
                            related_source_id=candidate.related_source_id,
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
                        fulltext_status="available",
                        acquisition_status="acquired_legal_fulltext",
                        publisher_url=self._publisher_url(record),
                        manual_access_url=self._manual_access_url(record),
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
                            candidate.acquisition_step,
                            candidate.version_type,
                            candidate.version_relation,
                            candidate.related_source_id,
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
                self._failed_record(
                    record,
                    candidate.expected_type,
                    normalized_url,
                    "",
                    "unsupported_or_unrecognized_content",
                    candidate.url_source,
                    now,
                    result.status_code,
                    result.media_type,
                    acquisition_step=candidate.acquisition_step,
                    version_type=candidate.version_type,
                    version_relation=candidate.version_relation,
                    related_source_id=candidate.related_source_id,
                )
            )
            counters["failed_attempts"] += 1
            last_failure_status = "not_pdf"
            last_failure_reason = "unsupported_or_unrecognized_content"
            last_http_status = result.status_code
            last_content_type = result.media_type
            last_resolved_url = result.final_url
        store.refresh_primary(record.source_id)
        if not store.successful_artifacts(record.source_id):
            legal_search_exhausted = not queue
            terminal = legal_search_exhausted
            terminal_download_status = (
                last_failure_status
                if last_failure_status in {"blocked", "paywalled", "not_found", "not_pdf"}
                else "failed_final"
            )
            store.update_queue_status(
                record.source_id,
                terminal_download_status if terminal else "failed_retryable",
                utc_now(),
                http_status=last_http_status,
                content_type=last_content_type,
                resolved_url=last_resolved_url,
                failure_reason="no_legal_fulltext_found" if terminal else last_failure_reason,
                fulltext_status="unavailable_legally" if terminal else "pending",
                acquisition_status="manual_access_required" if terminal else "retry_pending",
                publisher_url=self._publisher_url(record),
                manual_access_url=self._manual_access_url(record),
            )
            store.record_event(
                run_id,
                record.source_id,
                "source_coverage",
                "failed",
                utc_now(),
                detail=(
                    "no_legal_fulltext_found; manual_access_required"
                    if terminal
                    else "legal_fulltext_search_retry_pending"
                ),
            )
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
        provider_records = self._provider_records(record)

        # Step 2: Unpaywall OA PDF/HTML, including every licensed location.
        candidates.extend(self._provider_candidates(provider_records, {"unpaywall"}, 2))
        if record.pdf_url and is_oa and "unpaywall" in str(field_sources.get("pdf_url") or "").lower():
            candidates.append(
                UrlCandidate(record.pdf_url, "pdf", "metadata.unpaywall.pdf_url", "legal_oa", acquisition_step=2)
            )
        if record.html_url and is_oa and "unpaywall" in str(field_sources.get("html_url") or "").lower():
            candidates.append(
                UrlCandidate(record.html_url, "html", "metadata.unpaywall.html_url", "legal_oa", acquisition_step=2)
            )
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
                                2,
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
                                2,
                            )
                        )

        # Step 3: OpenAlex and Semantic Scholar open-full-text locations.
        candidates.extend(self._provider_candidates(provider_records, {"openalex", "semantic_scholar"}, 3))
        pdf_field_source = str(field_sources.get("pdf_url") or "metadata.pdf_url")
        html_field_source = str(field_sources.get("html_url") or "metadata.html_url")
        if record.pdf_url and is_oa and "unpaywall" not in pdf_field_source.lower():
            candidates.append(
                UrlCandidate(
                    record.pdf_url,
                    "pdf",
                    pdf_field_source,
                    "legal_oa",
                    acquisition_step=3 if any(name in pdf_field_source.lower() for name in ("openalex", "semantic")) else 4,
                )
            )

        # Step 4: official publisher/DOI page. A landing page is never treated
        # as a PDF; only signature-validated PDF or scholarly full-text HTML is saved.
        if record.doi:
            candidates.append(
                UrlCandidate(
                    f"https://doi.org/{record.doi}",
                    "html",
                    "doi_resolver.publisher_check",
                    "publisher_page_check",
                    acquisition_step=4,
                )
            )
        if record.source_link and record.source_link != f"https://doi.org/{record.doi}":
            candidates.append(
                UrlCandidate(
                    record.source_link,
                    "html",
                    "metadata.source_link.publisher_check",
                    "publisher_page_check",
                    acquisition_step=4,
                )
            )
        if record.html_url:
            candidates.append(
                UrlCandidate(
                    record.html_url,
                    "html",
                    html_field_source,
                    "legal_oa" if is_oa else "publisher_page_check",
                    acquisition_step=3 if is_oa and any(name in html_field_source.lower() for name in ("openalex", "semantic")) else 4,
                )
            )

        # Steps 5-6: explicitly verified official/institutional repositories,
        # author pages, and linked preprint/accepted-manuscript versions.
        candidates.extend(self.verified_candidates.get(record.source_id, []))
        output: list[UrlCandidate] = []
        seen: set[str] = set()
        attempt_count = (
            store.queue_attempt_count(record.source_id)[0]
            if hasattr(store, "queue_attempt_count")
            else 0
        )
        exhausted_urls = (
            set()
            if self.force or attempt_count == 0 or not hasattr(store, "exhausted_candidate_urls")
            else store.exhausted_candidate_urls(record.source_id)
        )
        for candidate in sorted(candidates, key=lambda item: (item.acquisition_step, 0 if item.expected_type == "pdf" else 1)):
            if candidate.url and candidate.url not in seen and candidate.url not in exhausted_urls:
                seen.add(candidate.url)
                output.append(candidate)
        return output

    @staticmethod
    def _provider_records(record: MetadataRecord) -> list[dict[str, Any]]:
        try:
            raw_records = json.loads(record.provider_records_json or "[]")
        except json.JSONDecodeError:
            return []
        return [item for item in raw_records if isinstance(item, dict)]

    @staticmethod
    def _provider_candidates(
        provider_records: list[dict[str, Any]],
        providers: set[str],
        acquisition_step: int,
    ) -> list[UrlCandidate]:
        candidates: list[UrlCandidate] = []
        for provider_record in provider_records:
            source_api = str(provider_record.get("source_api") or "").strip().lower()
            if source_api not in providers:
                continue
            try:
                normalized = json.loads(str(provider_record.get("normalized_json") or "{}"))
            except json.JSONDecodeError:
                continue
            if not isinstance(normalized, dict):
                continue
            oa_status = str(normalized.get("open_access_status") or "unknown").strip().lower()
            if oa_status not in OPEN_ACCESS_STATES:
                continue
            pdf_url = str(normalized.get("pdf_url") or "").strip()
            html_url = str(normalized.get("html_url") or "").strip()
            if pdf_url:
                candidates.append(
                    UrlCandidate(
                        pdf_url,
                        "pdf",
                        f"{source_api}.normalized.pdf_url",
                        "legal_oa",
                        acquisition_step=acquisition_step,
                    )
                )
            if html_url:
                candidates.append(
                    UrlCandidate(
                        html_url,
                        "html",
                        f"{source_api}.normalized.html_url",
                        "legal_oa",
                        acquisition_step=acquisition_step,
                    )
                )
        return candidates

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
                version_type = str(row.get("version_type") or "published").strip().lower()
                version_relation = str(row.get("version_relation") or "same_record").strip().lower()
                related_source_id = str(row.get("related_source_id") or "").strip()
                permitted_version_relations = {
                    "published": {"same_record", "published_version"},
                    "accepted_manuscript": {"accepted_manuscript_of"},
                    "author_manuscript": {"author_manuscript_of"},
                    "preprint": {"preprint_of"},
                }
                if (
                    not source_id
                    or not url
                    or fulltext_type not in {"pdf", "html"}
                    or access_type != "legal_oa"
                    or verification_status != "verified"
                    or version_type not in permitted_version_relations
                    or version_relation not in permitted_version_relations[version_type]
                ):
                    continue
                try:
                    configured_step = int(str(row.get("acquisition_step") or "0"))
                except ValueError:
                    configured_step = 0
                acquisition_step = configured_step or (
                    6 if version_type in {"preprint", "accepted_manuscript", "author_manuscript"} else 5
                )
                output.setdefault(source_id, []).append(
                    UrlCandidate(
                        url,
                        fulltext_type,
                        str(row.get("url_source") or "verified_oa_candidates"),
                        "legal_oa",
                        str(row.get("license") or ""),
                        acquisition_step,
                        version_type,
                        version_relation,
                        related_source_id,
                    )
                )
        return output

    @staticmethod
    def _publisher_url(record: MetadataRecord) -> str:
        if record.doi:
            return f"https://doi.org/{record.doi}"
        return record.source_link or record.html_url

    @classmethod
    def _manual_access_url(cls, record: MetadataRecord) -> str:
        return cls._publisher_url(record)

    def _save_content(self, store: FulltextStore, source_id: str, content: bytes, extension: str) -> tuple[str, str, bool]:
        content_hash = sha256_bytes(content)
        existing = store.successful_path_for_hash(content_hash)
        if existing and self._resolve(existing).exists():
            return existing, content_hash, True
        directory = self.pdf_dir if extension == "pdf" else self.html_dir
        path = directory / f"{source_id}.{extension}"
        if path.exists():
            if sha256_file(path) == content_hash:
                return self._rel(path), content_hash, True
            raise FileExistsError(
                f"canonical source file already has different content; archive it before replacement: {path}"
            )
        temp_path = unique_part_path(path)
        temp_path.write_bytes(content)
        if sha256_file(temp_path) != content_hash:
            temp_path.unlink(missing_ok=True)
            raise OSError("content_hash_mismatch_after_write")
        replace_with_retry(temp_path, path)
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
        acquisition_step: int = 0,
        version_type: str = "published",
        version_relation: str = "same_record",
        related_source_id: str = "",
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
            acquisition_step=acquisition_step,
            version_type=version_type,
            version_relation=version_relation,
            related_source_id=related_source_id,
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
