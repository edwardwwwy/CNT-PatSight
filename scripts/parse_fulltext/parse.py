from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.parse_fulltext.pipeline import ParsePipeline, print_summary
from scripts.parse_fulltext.storage import CandidateStore


ROOT = Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract reviewable sections and CNT experiment candidate spans from registered full text.")
    parser.add_argument("--metadata-db", type=Path, default=ROOT / "data/raw/literature/metadata/literature.sqlite3")
    parser.add_argument("--fulltext-db", type=Path, default=ROOT / "data/raw/literature/metadata/fulltext_registry/fulltext.sqlite3")
    parser.add_argument("--candidate-db", type=Path, default=ROOT / "cache/databases/extraction_candidates.sqlite3")
    parser.add_argument("--raw-text-dir", type=Path, default=ROOT / "data/interim/parsed_text/by_source", help=argparse.SUPPRESS)
    parser.add_argument("--parsed-text-dir", type=Path, default=ROOT / "data/interim/parsed_text/by_source")
    parser.add_argument("--section-csv", type=Path, default=ROOT / "cache/exports/paper_text_section.csv")
    parser.add_argument("--span-csv", type=Path, default=ROOT / "cache/exports/candidate_experiment_span.csv")
    parser.add_argument("--status-csv", type=Path, default=ROOT / "cache/exports/parse_source_status.csv")
    parser.add_argument("--ocr-queue-csv", type=Path, default=ROOT / "cache/exports/ocr_queue.csv")
    parser.add_argument("--reports-dir", type=Path, default=ROOT / "runs/parse")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--source-id", action="append")
    run.add_argument("--limit", type=int)
    run.add_argument("--force", action="store_true")
    subparsers.add_parser("report")
    subparsers.add_parser("export")
    return parser


def pipeline_from_args(args: argparse.Namespace) -> ParsePipeline:
    return ParsePipeline(
        ROOT,
        args.metadata_db.resolve(),
        args.fulltext_db.resolve(),
        args.candidate_db.resolve(),
        args.raw_text_dir.resolve(),
        args.parsed_text_dir.resolve(),
        args.section_csv.resolve(),
        args.span_csv.resolve(),
        args.status_csv.resolve(),
        args.reports_dir.resolve(),
        force=getattr(args, "force", False),
        ocr_queue_csv=args.ocr_queue_csv.resolve(),
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pipeline = pipeline_from_args(args)
    if args.command == "run":
        summary = pipeline.run(args.source_id, args.limit)
        print_summary(summary)
        return 0 if summary.get("status") in {"complete", "partial"} else 1
    with CandidateStore(args.candidate_db.resolve()) as store:
        if args.command == "export":
            counts = store.export(args.section_csv.resolve(), args.span_csv.resolve(), args.status_csv.resolve())
            ocr_count = store.export_ocr_queue(args.ocr_queue_csv.resolve())
            print(f"section_rows={counts[0]}, span_rows={counts[1]}, status_rows={counts[2]}")
            print(f"ocr_queue_rows={ocr_count}")
            return 0
        report = store.latest_run()
        if not report:
            print("No parse run found.", file=sys.stderr)
            return 1
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
