from __future__ import annotations

import json
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

from .clients import (
    CrossrefClient,
    JsonHttpClient,
    OpenAlexClient,
    RawArchive,
    SemanticScholarClient,
    UnpaywallClient,
)
from .models import SourceBatch
from .scoring import RelevanceScorer, ScreeningRules
from .settings import Credentials, Paths, SearchSettings
from .storage import MetadataStore
from .utils import json_dumps, utc_now


class CollectionPipeline:
    def __init__(self, paths: Paths, settings: SearchSettings, credentials: Credentials):
        self.paths = paths
        self.settings = settings
        self.credentials = credentials
        self.rules = ScreeningRules.from_file(paths.screening_rules_file)
        self.scorer = RelevanceScorer(self.rules)

    def _clients(self, run_id: str) -> dict[str, Any]:
        archive = RawArchive(self.paths.raw_responses, self.paths.root, run_id)
        http = JsonHttpClient(
            archive,
            timeout_seconds=self.credentials.timeout_seconds,
            max_retries=self.credentials.max_retries,
        )
        email = self.credentials.crossref_email or self.credentials.unpaywall_email
        user_agent = f"CNT-PatSight/0.1 metadata-collector ({email or 'contact-not-configured'})"
        return {
            "openalex": OpenAlexClient(http, self.credentials.openalex_api_key, user_agent),
            "semantic_scholar": SemanticScholarClient(
                http, self.credentials.semantic_scholar_api_key, user_agent
            ),
            "crossref": CrossrefClient(
                http, self.credentials.crossref_email, user_agent, self.settings.crossref_interval
            ),
            "unpaywall": UnpaywallClient(
                http, self.credentials.unpaywall_email, user_agent, self.settings.unpaywall_interval
            ),
        }

    def run(self) -> dict[str, Any]:
        run_id = self._run_id()
        run_config = {
            "queries": self.settings.queries,
            "max_results_per_query": self.settings.max_results_per_query,
            "max_enrich_records": self.settings.max_enrich_records,
            "title_similarity_threshold": self.settings.title_similarity_threshold,
            "title_review_threshold": self.settings.title_review_threshold,
            "title_min_length": self.settings.title_min_length,
            "screening_rule_version": self.rules.screening_rule_version,
            "dedup_rule_version": self.rules.dedup_rule_version,
            "enabled_sources": self.settings.enabled_sources,
        }
        clients = self._clients(run_id)
        api_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"requests": 0, "returned": 0, "errors": 0, "skipped_reason": ""}
        )
        inserted: set[str] = set()
        updated_existing: set[str] = set()
        enriched_new: set[str] = set()
        touched: set[str] = set()
        exact_dedup_events = 0
        fuzzy_dedup_events = 0
        dedup_review_events = 0
        unchanged_events = 0
        normalized_records = 0
        query_report: list[dict[str, Any]] = []
        status = "complete"
        error_message = ""

        with MetadataStore(
            self.paths.database,
            self.settings.title_similarity_threshold,
            self.settings.title_review_threshold,
            self.settings.title_min_length,
            self.rules.dedup_rule_version,
        ) as store:
            store.start_run(run_id, run_config)
            try:
                imported = store.import_legacy_csv(self.paths.master_csv, run_id, self.scorer)
                openalex = clients["openalex"]
                for query in self.settings.queries:
                    query_id = query["query_id"]
                    query_text = query["query"]
                    if "openalex" not in self.settings.enabled_sources:
                        batch = SourceBatch(skipped_reason="disabled by config")
                    else:
                        batch = openalex.search(query_id, query_text, self.settings.max_results_per_query)
                    self._record_responses(store, run_id, batch, api_stats)
                    counters = self._apply_batch(
                        store, run_id, batch, inserted, updated_existing, enriched_new, touched
                    )
                    normalized_records += counters["normalized"]
                    exact_dedup_events += counters["exact"]
                    fuzzy_dedup_events += counters["fuzzy"]
                    dedup_review_events += counters["review"]
                    unchanged_events += counters["unchanged"]
                    query_errors = [response.error for response in batch.responses if response.error]
                    query_status = "skipped" if batch.skipped_reason else ("error" if query_errors else "ok")
                    store.record_query(
                        run_id,
                        query_id,
                        query_text,
                        self.settings.max_results_per_query,
                        batch.api_total,
                        len(batch.records),
                        len(batch.responses),
                        query_status,
                        batch.skipped_reason or " | ".join(query_errors),
                    )
                    query_report.append(
                        {
                            "query_id": query_id,
                            "query": query_text,
                            "api_total": batch.api_total,
                            "returned": len(batch.records),
                            "requests": len(batch.responses),
                            "status": query_status,
                            "error": batch.skipped_reason or " | ".join(query_errors),
                        }
                    )

                dois = store.list_dois(touched, self.settings.max_enrich_records)
                enrichment_order = ["semantic_scholar", "crossref", "unpaywall"]
                for source_name in enrichment_order:
                    if source_name not in self.settings.enabled_sources:
                        batch = SourceBatch(skipped_reason="disabled by config")
                    elif not dois:
                        batch = SourceBatch(skipped_reason="no DOI available for enrichment")
                    else:
                        batch = clients[source_name].enrich(dois)
                    self._record_responses(store, run_id, batch, api_stats, source_name)
                    counters = self._apply_batch(
                        store, run_id, batch, inserted, updated_existing, enriched_new, touched
                    )
                    normalized_records += counters["normalized"]
                    exact_dedup_events += counters["exact"]
                    fuzzy_dedup_events += counters["fuzzy"]
                    dedup_review_events += counters["review"]
                    unchanged_events += counters["unchanged"]

                errors = sum(int(values["errors"]) for values in api_stats.values())
                credential_skips = [
                    source
                    for source, values in api_stats.items()
                    if values.get("skipped_reason")
                    and values["skipped_reason"] not in {"disabled by config", "no DOI available for enrichment"}
                ]
                if errors or credential_skips:
                    status = "partial" if touched else "failed"
                elif not touched:
                    status = "failed"
                    error_message = "No works were collected. Check credentials, source configuration, and API responses."
                run_slice = store.summarize_ids(touched)
                exported = store.export_csv(self.paths.master_csv)
                summary = {
                    "run_id": run_id,
                    "status": status,
                    "queries": query_report,
                    "api": dict(api_stats),
                    "legacy_records_imported": imported,
                    "normalized_source_records": normalized_records,
                    "inserted_works": len(inserted),
                    "updated_existing_works": len(updated_existing),
                    "enriched_new_works": len(enriched_new),
                    "exact_dedup_merge_events": exact_dedup_events,
                    "fuzzy_dedup_merge_events": fuzzy_dedup_events,
                    "dedup_review_events": dedup_review_events,
                    "unchanged_merge_events": unchanged_events,
                    "run_works": run_slice["works"],
                    "relevance_distribution": run_slice["relevance_distribution"],
                    "priority_tier_distribution": run_slice["priority_tier_distribution"],
                    "document_type_distribution": run_slice["document_type_distribution"],
                    "dedup_status_distribution": run_slice["dedup_status_distribution"],
                    "dedup_review_candidates": run_slice["dedup_review_candidates"],
                    "pdf_links": run_slice["pdf_links"],
                    "html_links": run_slice["html_links"],
                    "credential_or_access_skips": credential_skips,
                    "database_total_works": store.count_works(),
                    **store.dedup_corpus_summary(),
                    "csv_exported_rows": exported,
                    "database_path": self._display_path(self.paths.database),
                    "master_csv_path": self._display_path(self.paths.master_csv),
                    "raw_response_directory": self._display_path(self.paths.raw_responses / run_id),
                    "completed_at": utc_now(),
                }
                store.finish_run(run_id, status, summary, error_message)
                self._write_report(run_id, summary)
                return summary
            except Exception as exc:
                status = "failed"
                error_message = f"{type(exc).__name__}: {exc}"
                failure_summary = {
                    "run_id": run_id,
                    "status": status,
                    "queries": query_report,
                    "api": dict(api_stats),
                    "error": error_message,
                    "completed_at": utc_now(),
                }
                store.finish_run(run_id, status, failure_summary, error_message)
                self._write_report(run_id, failure_summary)
                raise

    def enrich(self, source_names: list[str], max_records: int) -> dict[str, Any]:
        """Enrich already collected DOI records without repeating discovery."""

        run_id = self._run_id()
        clients = self._clients(run_id)
        run_config = {
            "mode": "enrich_only",
            "sources": source_names,
            "max_records_per_source": max_records,
            "screening_rule_version": self.rules.screening_rule_version,
            "dedup_rule_version": self.rules.dedup_rule_version,
        }
        api_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"requests": 0, "returned": 0, "errors": 0, "skipped_reason": ""}
        )
        inserted: set[str] = set()
        updated_existing: set[str] = set()
        enriched_new: set[str] = set()
        touched: set[str] = set()
        candidate_counts: dict[str, int] = {}
        normalized_records = 0
        exact_dedup_events = 0
        fuzzy_dedup_events = 0
        dedup_review_events = 0
        unchanged_events = 0
        status = "complete"
        error_message = ""

        with MetadataStore(
            self.paths.database,
            self.settings.title_similarity_threshold,
            self.settings.title_review_threshold,
            self.settings.title_min_length,
            self.rules.dedup_rule_version,
        ) as store:
            store.start_run(run_id, run_config)
            try:
                for source_name in source_names:
                    dois = store.list_dois_missing_source(source_name, max_records)
                    candidate_counts[source_name] = len(dois)
                    if not dois:
                        batch = SourceBatch(skipped_reason="no pending DOI available for enrichment")
                    else:
                        batch = clients[source_name].enrich(dois)
                    self._record_responses(store, run_id, batch, api_stats, source_name)
                    counters = self._apply_batch(
                        store, run_id, batch, inserted, updated_existing, enriched_new, touched
                    )
                    normalized_records += counters["normalized"]
                    exact_dedup_events += counters["exact"]
                    fuzzy_dedup_events += counters["fuzzy"]
                    dedup_review_events += counters["review"]
                    unchanged_events += counters["unchanged"]

                errors = sum(int(values["errors"]) for values in api_stats.values())
                if errors:
                    status = "partial" if touched else "failed"
                run_slice = store.summarize_ids(touched)
                exported = store.export_csv(self.paths.master_csv)
                summary = {
                    "run_id": run_id,
                    "status": status,
                    "mode": "enrich_only",
                    "queries": [],
                    "enrichment_candidates": candidate_counts,
                    "api": dict(api_stats),
                    "normalized_source_records": normalized_records,
                    "inserted_works": len(inserted),
                    "updated_existing_works": len(updated_existing),
                    "enriched_new_works": len(enriched_new),
                    "exact_dedup_merge_events": exact_dedup_events,
                    "fuzzy_dedup_merge_events": fuzzy_dedup_events,
                    "dedup_review_events": dedup_review_events,
                    "unchanged_merge_events": unchanged_events,
                    "run_works": run_slice["works"],
                    "relevance_distribution": run_slice["relevance_distribution"],
                    "priority_tier_distribution": run_slice["priority_tier_distribution"],
                    "document_type_distribution": run_slice["document_type_distribution"],
                    "dedup_status_distribution": run_slice["dedup_status_distribution"],
                    "dedup_review_candidates": run_slice["dedup_review_candidates"],
                    "pdf_links": run_slice["pdf_links"],
                    "html_links": run_slice["html_links"],
                    "database_total_works": store.count_works(),
                    **store.dedup_corpus_summary(),
                    "csv_exported_rows": exported,
                    "database_path": self._display_path(self.paths.database),
                    "master_csv_path": self._display_path(self.paths.master_csv),
                    "raw_response_directory": self._display_path(
                        self.paths.raw_responses / run_id
                    ),
                    "completed_at": utc_now(),
                }
                store.finish_run(run_id, status, summary, error_message)
                self._write_report(run_id, summary)
                return summary
            except Exception as exc:
                error_message = f"{type(exc).__name__}: {exc}"
                failure_summary = {
                    "run_id": run_id,
                    "status": "failed",
                    "mode": "enrich_only",
                    "enrichment_candidates": candidate_counts,
                    "api": dict(api_stats),
                    "error": error_message,
                    "completed_at": utc_now(),
                }
                store.finish_run(run_id, "failed", failure_summary, error_message)
                self._write_report(run_id, failure_summary)
                raise

    @staticmethod
    def _record_responses(
        store: MetadataStore,
        run_id: str,
        batch: SourceBatch,
        api_stats: dict[str, dict[str, Any]],
        source_name: str = "openalex",
    ) -> None:
        if batch.skipped_reason:
            api_stats[source_name]["skipped_reason"] = batch.skipped_reason
        for response in batch.responses:
            store.record_response(run_id, response)
            stats = api_stats[response.source_api]
            stats["requests"] += 1
            stats["returned"] += response.returned_count
            if response.error:
                stats["errors"] += 1

    def _apply_batch(
        self,
        store: MetadataStore,
        run_id: str,
        batch: SourceBatch,
        inserted: set[str],
        updated_existing: set[str],
        enriched_new: set[str],
        touched: set[str],
    ) -> dict[str, int]:
        counters = {"normalized": 0, "exact": 0, "fuzzy": 0, "review": 0, "unchanged": 0}
        for work, raw_path in batch.records:
            result = store.upsert_work(work, run_id, raw_path, self.scorer)
            counters["normalized"] += 1
            touched.add(result.source_id)
            if result.action == "inserted":
                inserted.add(result.source_id)
            elif result.action == "updated":
                if result.source_id in inserted:
                    enriched_new.add(result.source_id)
                else:
                    updated_existing.add(result.source_id)
            else:
                counters["unchanged"] += 1
            if result.match_type in {"external_id", "doi", "title_exact"}:
                counters["exact"] += 1
            elif result.match_type == "title_fuzzy":
                counters["fuzzy"] += 1
            elif result.match_type in {"possible_duplicate", "doi_conflict_review"}:
                counters["review"] += 1
        return counters

    def _write_report(self, run_id: str, summary: dict[str, Any]) -> None:
        self.paths.run_reports.mkdir(parents=True, exist_ok=True)
        content = json.dumps(summary, ensure_ascii=False, indent=2)
        (self.paths.run_reports / f"{run_id}.json").write_text(content, encoding="utf-8")
        (self.paths.run_reports / "latest.json").write_text(content, encoding="utf-8")

    def _display_path(self, path: Path) -> str:
        try:
            return path.relative_to(self.paths.root).as_posix()
        except ValueError:
            return str(path)

    @staticmethod
    def _run_id() -> str:
        stamp = utc_now().replace("-", "").replace(":", "").replace("Z", "Z")
        return f"RUN_{stamp}_{uuid.uuid4().hex[:6]}"


def print_summary(summary: dict[str, Any]) -> None:
    print(f"run_id: {summary.get('run_id', '')}")
    print(f"status: {summary.get('status', '')}")
    print("queries:")
    for query in summary.get("queries", []):
        print(
            f"  - {query['query_id']}: returned={query['returned']}, "
            f"api_total={query.get('api_total')}, status={query['status']} | {query['query']}"
        )
    print("api_returns:")
    for source, values in summary.get("api", {}).items():
        suffix = f", skipped={values['skipped_reason']}" if values.get("skipped_reason") else ""
        print(
            f"  - {source}: requests={values.get('requests', 0)}, "
            f"returned={values.get('returned', 0)}, errors={values.get('errors', 0)}{suffix}"
        )
    print(
        "database: "
        f"inserted={summary.get('inserted_works', 0)}, "
        f"updated_existing={summary.get('updated_existing_works', 0)}, "
        f"enriched_new={summary.get('enriched_new_works', 0)}, "
        f"total={summary.get('database_total_works', 0)}"
    )
    print(
        "dedup: "
        f"exact_merges={summary.get('exact_dedup_merge_events', 0)}, "
        f"fuzzy_merges={summary.get('fuzzy_dedup_merge_events', 0)}, "
        f"review_required={summary.get('dedup_review_events', 0)}, "
        f"unchanged_merges={summary.get('unchanged_merge_events', 0)}"
    )
    print(
        "dedup_corpus: "
        f"raw_source_records={summary.get('raw_source_record_count', 0)}, "
        f"canonical_works={summary.get('canonical_work_count', summary.get('database_total_works', 0))}, "
        f"merge_groups={summary.get('merge_group_count', 0)}, "
        f"merged_extra_source_records={summary.get('merged_source_record_count', 0)}, "
        f"possible_duplicates={summary.get('possible_duplicate_count', 0)}"
    )
    print(f"relevance_distribution: {json_dumps(summary.get('relevance_distribution', {}))}")
    print(f"priority_tier_distribution: {json_dumps(summary.get('priority_tier_distribution', {}))}")
    print(f"document_type_distribution: {json_dumps(summary.get('document_type_distribution', {}))}")
    print(f"links: pdf={summary.get('pdf_links', 0)}, html={summary.get('html_links', 0)}")
    print(f"master_csv: {summary.get('master_csv_path', '')}")
    print(f"raw_responses: {summary.get('raw_response_directory', '')}")
