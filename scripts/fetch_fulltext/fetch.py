from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.fetch_fulltext.pipeline import FulltextPipeline, print_summary
from scripts.fetch_fulltext.storage import FulltextStore


ROOT = Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch and register legal/local full text without modifying the eight-table data contract.")
    parser.add_argument("--metadata-db", type=Path, default=ROOT / "data/raw/literature/metadata/literature.sqlite3")
    parser.add_argument("--fulltext-db", type=Path, default=ROOT / "data/raw/literature/metadata/fulltext_registry/fulltext.sqlite3")
    parser.add_argument("--pdf-dir", type=Path, default=ROOT / "data/raw/literature/pdf")
    parser.add_argument("--html-dir", type=Path, default=ROOT / "data/raw/literature/html")
    parser.add_argument("--reports-dir", type=Path, default=ROOT / "runs/fulltext")
    parser.add_argument("--source-csv", type=Path, default=ROOT / "data/raw/literature/metadata/fulltext_registry/fulltext_source.csv")
    parser.add_argument("--coverage-csv", type=Path, default=ROOT / "data/raw/literature/metadata/fulltext_registry/fulltext_coverage.csv")
    parser.add_argument("--queue-csv", type=Path, default=ROOT / "data/raw/literature/metadata/fulltext_registry/fulltext_acquisition_queue.csv")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument(
        "--verified-candidates-csv",
        type=Path,
        default=ROOT / "data/raw/literature/metadata/fulltext_registry/verified_oa_candidates.csv",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--source-id", action="append")
    run.add_argument("--limit", type=int)
    run.add_argument("--force", action="store_true")
    run.add_argument("--no-unpaywall", action="store_true")
    run.add_argument("--max-candidates-per-source", type=int, default=10)
    run.add_argument("--max-attempts", type=int, default=3)
    run.add_argument(
        "--all-metadata",
        action="store_true",
        help="Diagnostic override: bypass the A/B acquisition queue.",
    )
    queue = subparsers.add_parser("queue")
    queue.add_argument("--reset-terminal", action="store_true")
    queue.add_argument("--max-attempts", type=int, default=3)
    subparsers.add_parser("report")
    subparsers.add_parser("export")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pipeline = FulltextPipeline(
        ROOT,
        args.metadata_db.resolve(),
        args.fulltext_db.resolve(),
        args.pdf_dir.resolve(),
        args.html_dir.resolve(),
        args.reports_dir.resolve(),
        args.source_csv.resolve(),
        args.coverage_csv.resolve(),
        args.env_file.resolve(),
        force=getattr(args, "force", False),
        use_unpaywall=not getattr(args, "no_unpaywall", False),
        max_candidates_per_source=max(1, getattr(args, "max_candidates_per_source", 10)),
        queue_csv=args.queue_csv.resolve(),
        max_queue_attempts=max(1, getattr(args, "max_attempts", 3)),
        verified_candidates_csv=args.verified_candidates_csv.resolve(),
    )
    if args.command == "queue":
        summary = pipeline.build_queue(reset_terminal=args.reset_terminal)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if args.command == "run":
        summary = pipeline.run(args.source_id, args.limit, from_queue=not args.all_metadata)
        print_summary(summary)
        return 0 if summary.get("status") == "complete" else 1
    records = pipeline.load_metadata()
    with FulltextStore(args.fulltext_db.resolve()) as store:
        if args.command == "export":
            source_rows, coverage_rows = store.export(records, args.source_csv.resolve(), args.coverage_csv.resolve())
            queue_rows = store.export_queue(args.queue_csv.resolve())
            print(f"fulltext_source_rows: {source_rows}")
            print(f"coverage_rows: {coverage_rows}")
            print(f"queue_rows: {queue_rows}")
            return 0
        report = store.latest_run()
        if not report:
            print("No fulltext run found.", file=sys.stderr)
            return 1
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
