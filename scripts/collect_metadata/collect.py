from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.collect_metadata.pipeline import CollectionPipeline, print_summary
from scripts.collect_metadata.scoring import RelevanceScorer, ScreeningRules
from scripts.collect_metadata.settings import Credentials, Paths, ROOT, SearchSettings
from scripts.collect_metadata.storage import MetadataStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect, normalize, deduplicate, and persist CNT literature metadata."
    )
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "literature_search.json")
    parser.add_argument("--screening-rules", type=Path, default=ROOT / "config" / "screening_rules.json")
    parser.add_argument("--database", type=Path, default=ROOT / "data" / "raw" / "literature" / "metadata" / "literature.sqlite3")
    parser.add_argument("--master-csv", type=Path, default=ROOT / "data" / "raw" / "literature" / "metadata" / "literature_master.csv")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data/raw/api_responses")
    parser.add_argument("--reports-dir", type=Path, default=ROOT / "runs/metadata")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run OpenAlex discovery and configured DOI enrichment sources.")
    run.add_argument("--query", action="append", help="Override configured queries; may be repeated.")
    run.add_argument("--max-results-per-query", type=int)
    run.add_argument("--max-enrich-records", type=int)
    run.add_argument(
        "--sources",
        help="Comma-separated source list: openalex,semantic_scholar,crossref,unpaywall",
    )
    run.add_argument(
        "--query-id",
        action="append",
        help="Run only selected configured query_id values; may be repeated.",
    )

    enrich = subparsers.add_parser(
        "enrich",
        help="Resume DOI enrichment without repeating OpenAlex discovery.",
    )
    enrich.add_argument(
        "--sources",
        help="Comma-separated enrichment sources: semantic_scholar,crossref,unpaywall",
    )
    enrich.add_argument("--max-records", type=int, help="Maximum pending DOI records per source.")

    subparsers.add_parser("doctor", help="Check configuration and credential presence without showing secrets.")
    subparsers.add_parser("export", help="Rebuild the normalized CSV export from SQLite.")
    subparsers.add_parser("rescore", help="Recompute document type, screening scores, tiers, and rule snapshots.")
    report = subparsers.add_parser("report", help="Print the latest or a selected stored run report.")
    report.add_argument("--run-id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = Paths(
        root=ROOT,
        env_file=args.env_file.resolve(),
        config_file=args.config.resolve(),
        screening_rules_file=args.screening_rules.resolve(),
        database=args.database.resolve(),
        master_csv=args.master_csv.resolve(),
        raw_responses=args.raw_dir.resolve(),
        run_reports=args.reports_dir.resolve(),
    )
    credentials = Credentials.from_env(paths.env_file)
    if args.command == "doctor":
        print(f"env_file: {paths.env_file}")
        print(f"env_file_exists: {paths.env_file.exists()}")
        for name, available in credentials.availability().items():
            print(f"{name}: {'configured' if available else 'missing'}")
        print(f"config_file: {paths.config_file}")
        print(f"config_file_exists: {paths.config_file.exists()}")
        print(f"screening_rules_file: {paths.screening_rules_file}")
        print(f"screening_rules_file_exists: {paths.screening_rules_file.exists()}")
        return 0 if credentials.openalex_api_key and paths.config_file.exists() and paths.screening_rules_file.exists() else 2

    settings = SearchSettings.from_file(paths.config_file)
    rules = ScreeningRules.from_file(paths.screening_rules_file)
    settings.title_similarity_threshold = rules.dedup_auto_merge_threshold
    settings.title_review_threshold = rules.dedup_review_threshold
    settings.title_min_length = rules.title_min_length
    if args.command == "run":
        if args.query:
            settings.queries = [
                {"query_id": f"cli_query_{index:02d}", "query": query}
                for index, query in enumerate(args.query, start=1)
            ]
        elif args.query_id:
            requested = set(args.query_id)
            available_query_ids = {item["query_id"] for item in settings.queries}
            unknown = sorted(requested - available_query_ids)
            if unknown:
                print(f"Unknown query_id values: {', '.join(unknown)}", file=sys.stderr)
                return 2
            settings.queries = [item for item in settings.queries if item["query_id"] in requested]
        if args.max_results_per_query is not None:
            settings.max_results_per_query = max(1, args.max_results_per_query)
        if args.max_enrich_records is not None:
            settings.max_enrich_records = max(0, args.max_enrich_records)
        if args.sources:
            settings.enabled_sources = [item.strip() for item in args.sources.split(",") if item.strip()]
        summary = CollectionPipeline(paths, settings, credentials).run()
        print_summary(summary)
        return 0 if summary.get("status") in {"complete", "partial"} else 1

    if args.command == "enrich":
        sources = (
            [item.strip() for item in args.sources.split(",") if item.strip()]
            if args.sources
            else ["semantic_scholar", "crossref", "unpaywall"]
        )
        invalid = sorted(set(sources) - {"semantic_scholar", "crossref", "unpaywall"})
        if invalid:
            print(f"Invalid enrichment sources: {', '.join(invalid)}", file=sys.stderr)
            return 2
        max_records = settings.max_enrich_records if args.max_records is None else max(0, args.max_records)
        summary = CollectionPipeline(paths, settings, credentials).enrich(sources, max_records)
        print_summary(summary)
        return 0 if summary.get("status") in {"complete", "partial"} else 1

    with MetadataStore(
        paths.database,
        settings.title_similarity_threshold,
        settings.title_review_threshold,
        settings.title_min_length,
        rules.dedup_rule_version,
    ) as store:
        if args.command == "rescore":
            count = store.rescore_all(RelevanceScorer(rules))
            exported = store.export_csv(paths.master_csv)
            print(f"rescored_rows: {count}")
            print(f"exported_rows: {exported}")
            print(f"screening_rule_version: {rules.screening_rule_version}")
            print(f"dedup_rule_version: {rules.dedup_rule_version}")
            return 0
        if args.command == "export":
            count = store.export_csv(paths.master_csv)
            print(f"exported_rows: {count}")
            print(f"master_csv: {paths.master_csv}")
            print(json.dumps(store.dedup_corpus_summary(), ensure_ascii=False, sort_keys=True))
            return 0
        report = store.latest_report(args.run_id)
        if report is None:
            print("No collection run was found.", file=sys.stderr)
            return 1
        report.update(store.dedup_corpus_summary())
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
