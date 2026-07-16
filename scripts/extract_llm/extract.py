from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.extract_llm.runner import (
    DEFAULT_MODEL,
    DEFAULT_PROMPT,
    DEFAULT_REVIEW_DIR,
    DEFAULT_SCHEMA,
    DEFAULT_SECTION_CSV,
    DEFAULT_SPAN_CSV,
    DEFAULT_STAGE_DIR,
    LlmExtractionRunner,
    read_json,
    utc_now,
    write_json,
)
from scripts.extract_llm.validator import validate_payload


ROOT = Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Qwen staging extraction from CNT candidate spans; never writes the formal eight tables.")
    parser.add_argument("--model", type=Path, default=ROOT / DEFAULT_MODEL)
    parser.add_argument("--schema", type=Path, default=ROOT / DEFAULT_SCHEMA)
    parser.add_argument("--prompt", type=Path, default=ROOT / DEFAULT_PROMPT)
    parser.add_argument("--section-csv", type=Path, default=ROOT / DEFAULT_SECTION_CSV)
    parser.add_argument("--span-csv", type=Path, default=ROOT / DEFAULT_SPAN_CSV)
    parser.add_argument("--stage-dir", type=Path, default=ROOT / DEFAULT_STAGE_DIR)
    parser.add_argument("--review-dir", type=Path, default=ROOT / DEFAULT_REVIEW_DIR)
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--device", default="Vulkan0")
    parser.add_argument("--context-size", type=int, default=16384)
    parser.add_argument("--max-tokens", type=int, default=7500)
    parser.add_argument("--max-chars", type=int, default=10000)
    parser.add_argument("--max-spans", type=int, default=80)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--source-id", action="append")
    parser.add_argument("--sample-set", type=Path, default=ROOT / "config/llm_sample_set.json")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare")
    run = subparsers.add_parser("run")
    run.add_argument("--force", action="store_true")
    pipeline = subparsers.add_parser("pipeline")
    pipeline.add_argument("--force", action="store_true")
    validate = subparsers.add_parser("validate")
    validate.add_argument("--source-id", action="append")
    subparsers.add_parser("review")
    return parser


def source_ids(args: argparse.Namespace) -> list[str]:
    if args.source_id:
        return list(dict.fromkeys(args.source_id))
    sample = read_json(args.sample_set)
    return list(sample["source_ids"])


def runner_from_args(args: argparse.Namespace) -> LlmExtractionRunner:
    return LlmExtractionRunner(
        ROOT,
        args.model,
        args.schema,
        args.prompt,
        args.section_csv,
        args.span_csv,
        args.stage_dir,
        args.review_dir,
        args.runtime,
        args.device,
        args.context_size,
        args.max_tokens,
        args.max_chars,
        args.max_spans,
        args.timeout_seconds,
    )


def write_review_exports(runner: LlmExtractionRunner, source_filter: list[str] | None = None) -> dict[str, int]:
    runner.review_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    issues: list[dict[str, object]] = []
    latest_by_source: dict[str, tuple[float, Path]] = {}
    for report_path in sorted(runner.report_dir.glob("*.json")):
        if report_path.name == "latest.json":
            continue
        report = read_json(report_path)
        source_id = report.get("source_id")
        if not source_id or (source_filter and source_id not in source_filter):
            continue
        current = latest_by_source.get(source_id)
        if current is None or report_path.stat().st_mtime > current[0]:
            latest_by_source[source_id] = (report_path.stat().st_mtime, report_path)
    # Keep historical reports on disk for traceability, but expose only the
    # latest attempt per source in the active human-review queue.
    for source_id in sorted(latest_by_source):
        report = read_json(latest_by_source[source_id][1])
        validation = report.get("validation", {})
        rows.append({
            "source_id": report.get("source_id", ""),
            "request_hash": report.get("request_hash", ""),
            "extraction_status": report.get("status", ""),
            "review_status": "open",
            "error_count": validation.get("error_count", ""),
            "warning_count": validation.get("warning_count", ""),
            "run_count": validation.get("counts", {}).get("run_candidates", ""),
            "catalyst_count": validation.get("counts", {}).get("catalyst_candidates", ""),
            "process_stage_count": validation.get("counts", {}).get("process_stage_candidates", ""),
            "product_count": validation.get("counts", {}).get("product_candidates", ""),
            "evidence_claim_count": validation.get("counts", {}).get("evidence_claims", ""),
            "evidence_field_coverage": validation.get("evidence_field_coverage", {}).get("ratio", ""),
            "reviewer": "",
            "reviewed_at": "",
            "notes": "First-pass Qwen staging output; not formal eight-table data.",
        })
        for issue in validation.get("issues", []):
            issues.append({
                "source_id": report.get("source_id", ""),
                "request_hash": report.get("request_hash", ""),
                "review_status": "open",
                **issue,
            })
    queue_path = runner.review_dir / "review_queue.csv"
    issue_path = runner.review_dir / "validation_issues.csv"
    queue_fields = list(rows[0].keys()) if rows else ["source_id", "request_hash", "extraction_status", "review_status"]
    issue_fields = sorted({key for row in issues for key in row}) if issues else ["source_id", "request_hash", "review_status", "code", "message", "severity"]
    for path, data, fields in ((queue_path, rows, queue_fields), (issue_path, issues, issue_fields)):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)
    write_json(runner.review_dir / "latest.json", {"generated_at": utc_now(), "queue_rows": len(rows), "issue_rows": len(issues), "queue_path": str(queue_path.relative_to(ROOT)), "issue_path": str(issue_path.relative_to(ROOT))})
    return {"queue_rows": len(rows), "issue_rows": len(issues)}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runner = runner_from_args(args)
    selected = source_ids(args)
    if args.command == "prepare":
        for source_id in selected:
            prepared = runner.prepare(source_id)
            print(f"prepared {source_id}: {prepared['request_hash']} spans={prepared['package']['selection_stats']['selected_spans']}")
        return 0
    if args.command == "run":
        summary = runner.run(selected, force=args.force)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if summary["status"] == "complete" else 1
    if args.command == "pipeline":
        summary = runner.run(selected, force=args.force)
        exports = write_review_exports(runner, selected)
        print(json.dumps({"run": summary, "review_exports": exports}, ensure_ascii=False, indent=2))
        return 0 if summary["status"] == "complete" else 1
    if args.command == "validate":
        failures = 0
        for source_id in selected:
            matches = sorted(runner.validated_dir.glob(f"{source_id}__*.json"))
            if not matches:
                print(f"missing validated JSON: {source_id}", file=sys.stderr)
                failures += 1
                continue
            package = runner.package(source_id)
            payload = read_json(matches[-1])
            from scripts.extract_llm.normalizer import normalize_payload
            normalized, normalization_issues = normalize_payload(payload, package, runner.schema_path)
            write_json(matches[-1], normalized)
            result = validate_payload(normalized, package, runner.schema_path)
            for issue in normalization_issues:
                result["issues"].append({**issue, "severity": "warning"})
            result["warning_count"] += len(normalization_issues)
            result["normalization_issue_count"] = len(normalization_issues)
            result["normalization_issues"] = normalization_issues
            report_path = runner.report_dir / f"{matches[-1].stem}.json"
            if report_path.exists():
                report = read_json(report_path)
                report["status"] = "validated_needs_review" if result["valid"] else "validation_failed"
                report["validation"] = result
                write_json(report_path, report)
            print(source_id, json.dumps(result, ensure_ascii=False))
            failures += int(not result["valid"])
        return 0 if failures == 0 else 1
    exports = write_review_exports(runner, selected)
    print(json.dumps(exports, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
