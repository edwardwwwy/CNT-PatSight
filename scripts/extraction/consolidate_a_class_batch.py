#!/usr/bin/env python3
"""Consolidate all available A-class eight-table packages into eight CSV files."""

from __future__ import annotations

import csv
import json
import shutil
import tempfile
from pathlib import Path

from scripts.extraction.build_a_class_batch import BATCH_ID, ROOT, TABLES

PACKAGE_ROOT = ROOT / "data/interim/eight_table_staging/codex_manual" / BATCH_ID
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
OUTPUT = BATCH_ROOT / "consolidated_eight_tables"
MANIFEST = BATCH_ROOT / "manifest.csv"


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def package_dirs() -> list[Path]:
    directories = sorted(item for item in PACKAGE_ROOT.iterdir() if item.is_dir())
    with MANIFEST.open(encoding="utf-8-sig", newline="") as handle:
        for item in csv.DictReader(handle):
            if item["extraction_state"] == "existing_curated_package":
                directories.append(ROOT / "data/interim" / item["source_id"])
    return directories


def main() -> None:
    packages = package_dirs()
    temporary = Path(tempfile.mkdtemp(prefix=".a_class_consolidated.", dir=BATCH_ROOT))
    counts: dict[str, int] = {}
    try:
        for table in TABLES:
            header: list[str] | None = None
            rows: list[dict[str, str]] = []
            for package in packages:
                current_header, current_rows = read_rows(package / f"{table}.csv")
                if header is None:
                    header = current_header
                elif current_header != header:
                    raise ValueError(f"Header mismatch: {package}/{table}.csv")
                rows.extend(current_rows)
            with (temporary / f"{table}.csv").open(
                "w", encoding="utf-8-sig", newline=""
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=header or [])
                writer.writeheader()
                writer.writerows(rows)
            counts[table] = len(rows)

        source_ids = {
            row["source_id"]
            for _, rows in [read_rows(temporary / "source_master.csv")]
            for row in rows
        }
        _, runs = read_rows(temporary / "source_run.csv")
        run_ids = [row["run_id"] for row in runs]
        if len(run_ids) != len(set(run_ids)):
            raise ValueError("Duplicate run_id in consolidated output")

        summary = {
            "batch_id": BATCH_ID,
            "package_count": len(packages),
            "source_count": len(source_ids),
            "run_count": len(run_ids),
            "row_counts": counts,
            "manual_package_root": PACKAGE_ROOT.relative_to(ROOT).as_posix(),
            "includes_existing_curated_packages": True,
        }
        (temporary / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if OUTPUT.exists():
            raise FileExistsError(f"Output already exists: {OUTPUT}")
        shutil.move(str(temporary), str(OUTPUT))
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


if __name__ == "__main__":
    main()
