#!/usr/bin/env python3
"""Build a disposable B-class coverage bundle from canonical source packages."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import tempfile
from pathlib import Path

from scripts.extraction.batch_common import ROOT, SCHEMA, TABLES, load_metadata
from scripts.extraction.package_io import read_extraction_package


PACKAGE_ROOT = ROOT / "data/interim/extraction/B"
OUTPUT = ROOT / "runs/extraction/B/deliveries/B_CLASS_COMPLETE_20260720"


def write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def build_coverage(packages: dict[str, dict]) -> tuple[list[str], list[dict[str, str]]]:
    metadata = load_metadata("B")
    header = [
        "source_id", "title", "year", "doi", "priority_tier",
        "coverage_state", "eight_table_included", "package_path",
        "disposition", "constraint",
    ]
    rows: list[dict[str, str]] = []
    for source_id, meta in sorted(metadata.items()):
        package = packages.get(source_id)
        included = "yes" if package else "no"
        rows.append({
            "source_id": source_id,
            "title": str(meta.get("title") or ""),
            "year": str(meta.get("year") or ""),
            "doi": str(meta.get("doi") or ""),
            "priority_tier": "B",
            "coverage_state": "canonical_extraction_package" if package else "not_packaged",
            "eight_table_included": included,
            "package_path": (
                f"data/interim/extraction/B/{source_id}.extraction.json" if package else ""
            ),
            "disposition": (
                "Included from the canonical one-file extraction package."
                if package else
                "No experimental row is emitted until source-backed run boundaries are reconstructed."
            ),
            "constraint": "Independent review remains required." if package else "No canonical extraction package.",
        })
    return header, rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a rebuildable B-class delivery bundle in runs/.")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output.resolve()
    expected_parent = (ROOT / "runs/extraction/B/deliveries").resolve()
    if output.parent != expected_parent or not output.name.startswith("B_CLASS_COMPLETE_"):
        raise ValueError(f"Refusing output outside the B-class run area: {output}")
    if output.exists() and not args.replace:
        raise FileExistsError(f"Output already exists: {output}; pass --replace to refresh it")

    package_list = [
        read_extraction_package(path)
        for path in sorted(PACKAGE_ROOT.glob("*.extraction.json"))
    ]
    packages = {package["source_id"]: package for package in package_list}
    if len(packages) != len(package_list):
        raise ValueError("Duplicate B source package detected")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".b_class_complete.", dir=output.parent))
    try:
        tables_root = temporary / "eight_tables"
        tables_root.mkdir()
        counts: dict[str, int] = {}
        for table in TABLES:
            rows = [row for package in package_list for row in package["tables"][table]]
            write_csv(tables_root / f"{table}.csv", list(SCHEMA["tables"][table]["columns"]), rows)
            counts[table] = len(rows)

        coverage_header, coverage_rows = build_coverage(packages)
        write_csv(temporary / "source_coverage.csv", coverage_header, coverage_rows)
        summary = {
            "delivery": "B-class rebuildable coverage bundle",
            "priority_tier": "B",
            "registered_source_count": len(coverage_rows),
            "extraction_source_count": len(packages),
            "eight_table_run_count": counts["source_run"],
            "eight_table_row_counts": counts,
            "artifact_class": "rebuildable_run_output",
            "canonical_input": PACKAGE_ROOT.relative_to(ROOT).as_posix(),
        }
        (temporary / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        if output.exists():
            shutil.rmtree(output)
        shutil.move(str(temporary), str(output))
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


if __name__ == "__main__":
    main()
