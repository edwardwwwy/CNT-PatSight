#!/usr/bin/env python3
"""Consolidate canonical A extraction packages into a disposable run artifact."""

from __future__ import annotations

import csv
import json
import shutil
import tempfile
from pathlib import Path

from scripts.extraction.build_a_class_batch import BATCH_ID, ROOT, TABLES
from scripts.extraction.package_io import read_extraction_package


PACKAGE_ROOT = ROOT / "data/interim/extraction/A"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
OUTPUT = BATCH_ROOT / "consolidated_eight_tables"


def main() -> None:
    packages = [
        read_extraction_package(path)
        for path in sorted(PACKAGE_ROOT.glob("*.extraction.json"))
    ]
    if not packages:
        raise FileNotFoundError(f"No A extraction packages found under {PACKAGE_ROOT}")
    BATCH_ROOT.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".a_class_consolidated.", dir=BATCH_ROOT))
    counts: dict[str, int] = {}
    try:
        for table in TABLES:
            rows = [row for package in packages for row in package["tables"][table]]
            columns = list(json.loads((ROOT / "config/schema.json").read_text(encoding="utf-8"))["tables"][table]["columns"])
            with (temporary / f"{table}.csv").open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
                writer.writeheader()
                writer.writerows(rows)
            counts[table] = len(rows)

        source_ids = [package["source_id"] for package in packages]
        run_ids = [row["run_id"] for package in packages for row in package["tables"]["source_run"]]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Duplicate source_id in A extraction packages")
        if len(run_ids) != len(set(run_ids)):
            raise ValueError("Duplicate run_id in consolidated output")
        summary = {
            "batch_id": BATCH_ID,
            "package_count": len(packages),
            "source_count": len(source_ids),
            "run_count": len(run_ids),
            "row_counts": counts,
            "canonical_package_root": PACKAGE_ROOT.relative_to(ROOT).as_posix(),
            "artifact_class": "rebuildable_run_output",
        }
        (temporary / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
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
