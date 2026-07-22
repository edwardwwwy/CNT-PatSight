#!/usr/bin/env python3
"""Validate the canonical CNT-PatSight data lifecycle and one-file packages."""

from __future__ import annotations

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

TOP_LEVEL = {"raw", "interim", "processed", "benchmark", "audit"}
RAW = {"literature", "api_responses"}
LITERATURE = {"pdf", "html", "metadata", "supplements"}
INTERIM = {"parsed_text", "extraction", "evidence", "review_queue"}
PROCESSED = {"eight_tables", "analysis", "snapshots"}
BENCHMARK = {"gold", "fixtures", "templates", "results"}
AUDIT = {"samples", "issues", "summaries"}
EIGHT_TABLES = {
    "source_master.csv",
    "source_run.csv",
    "catalyst_system.csv",
    "reactor_process_gas.csv",
    "yield_quality.csv",
    "cost_scale_review.csv",
    "evidence_index.csv",
    "review_issue_log.csv",
}
ANALYSIS_FILES = {"run_level_dataset.csv", "process_comparison.csv", "data_quality_summary.csv"}
TEMPLATE_FILES = EIGHT_TABLES | {"cnt_patsight_collection_template.xlsx"}


def directories(path: Path) -> set[str]:
    return {item.name for item in path.iterdir() if item.is_dir()} if path.exists() else set()


def check_exact(errors: list[str], path: Path, expected: set[str]) -> None:
    actual = directories(path)
    if actual != expected:
        if actual - expected:
            errors.append(f"{path.relative_to(ROOT)} has extra folders: {sorted(actual - expected)}")
        if expected - actual:
            errors.append(f"{path.relative_to(ROOT)} is missing folders: {sorted(expected - actual)}")


def check_files(errors: list[str], path: Path, required: set[str], *, exact_csv: bool = False) -> None:
    actual = {item.name for item in path.iterdir() if item.is_file()} if path.exists() else set()
    if required - actual:
        errors.append(f"{path.relative_to(ROOT)} is missing files: {sorted(required - actual)}")
    if exact_csv:
        csv_files = {name for name in actual if name.lower().endswith(".csv")}
        if csv_files != required:
            errors.append(f"{path.relative_to(ROOT)} must contain only the canonical eight CSV files")


def validate_extractions(errors: list[str]) -> None:
    root = DATA / "interim/extraction"
    check_exact(errors, root, {"A", "B", "C"})
    seen: set[str] = set()
    expected_tables = {name.removesuffix(".csv") for name in EIGHT_TABLES}
    for tier in "ABC":
        for path in (root / tier).glob("*"):
            if not path.is_file() or not path.name.endswith(".extraction.json"):
                errors.append(f"unexpected extraction artifact: {path.relative_to(ROOT)}")
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                errors.append(f"invalid extraction JSON {path.relative_to(ROOT)}: {exc}")
                continue
            source_id = str(payload.get("source_id") or "")
            if path.name != f"{source_id}.extraction.json":
                errors.append(f"source_id/filename mismatch: {path.relative_to(ROOT)}")
            if source_id in seen:
                errors.append(f"source_id appears in more than one tier: {source_id}")
            seen.add(source_id)
            if payload.get("relevance_tier") != tier:
                errors.append(f"tier mismatch: {path.relative_to(ROOT)}")
            if set(payload.get("tables", {})) != expected_tables:
                errors.append(f"invalid eight-table payload: {path.relative_to(ROOT)}")


def validate_parsed_text(errors: list[str]) -> None:
    root = DATA / "interim/parsed_text"
    check_exact(errors, root, {"by_source"})
    for path in (root / "by_source").glob("*"):
        if not path.is_file() or not path.name.endswith(".parsed.json"):
            errors.append(f"unexpected parsed-text artifact: {path.relative_to(ROOT)}")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"invalid parsed JSON {path.relative_to(ROOT)}: {exc}")
            continue
        if path.name != f"{payload.get('source_id', '')}.parsed.json":
            errors.append(f"parsed source_id/filename mismatch: {path.relative_to(ROOT)}")


def main() -> int:
    errors: list[str] = []
    check_exact(errors, DATA, TOP_LEVEL)
    check_exact(errors, DATA / "raw", RAW)
    check_exact(errors, DATA / "raw/literature", LITERATURE)
    check_exact(errors, DATA / "raw/literature/metadata", {"snapshots", "fulltext_registry"})
    check_exact(errors, DATA / "interim", INTERIM)
    check_exact(errors, DATA / "processed", PROCESSED)
    check_exact(errors, DATA / "benchmark", BENCHMARK)
    check_exact(errors, DATA / "audit", AUDIT)

    validate_parsed_text(errors)
    validate_extractions(errors)
    check_exact(errors, DATA / "interim/review_queue", set())
    check_files(errors, DATA / "processed/eight_tables", EIGHT_TABLES, exact_csv=True)
    check_files(errors, DATA / "processed/analysis", ANALYSIS_FILES)
    check_files(errors, DATA / "benchmark/templates", TEMPLATE_FILES)

    six_samples = DATA / "benchmark/fixtures/six_papers"
    if not six_samples.is_dir() or len(directories(six_samples)) != 6:
        errors.append("data/benchmark/fixtures/six_papers must contain exactly 6 sample packages")
    if "templates" in directories(DATA / "benchmark/fixtures"):
        errors.append("benchmark templates must live in data/benchmark/templates, not fixtures/templates")

    loose = [item.name for item in DATA.iterdir() if item.is_file() and item.name != "README.md"]
    if loose:
        errors.append(f"data/ has loose files: {sorted(loose)}")
    for required_dir in (ROOT / "reports", ROOT / "scripts", ROOT / "src", ROOT / "tests"):
        if not required_dir.is_dir():
            errors.append(f"missing top-level folder: {required_dir.name}")

    company_dir = os.environ.get("CNT_COMPANY_DATA_DIR", "").strip()
    if company_dir:
        candidate = Path(company_dir).expanduser().resolve()
        if candidate == ROOT.resolve() or ROOT.resolve() in candidate.parents:
            errors.append("CNT_COMPANY_DATA_DIR must point outside the public repository")

    if errors:
        print("Data layout validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Data layout validation passed: raw, interim, processed, benchmark, audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
