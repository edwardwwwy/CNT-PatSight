#!/usr/bin/env python3
"""Publish one navigable dataset for every parseable B-class source.

This is a delivery-layer organizer.  It does not promote parser candidate
spans to formal experiments: each of the 139 parsed sources receives the same
eight-table package layout, while only source-backed, reconstructable runs are
present in the formal fact tables.  Candidate-span observations, measurements,
and entities are made searchable in a clearly labelled evidence layer.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sqlite3
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from scripts.extraction.batch_common import ROOT, SCHEMA, TABLES, write_table
from scripts.extraction.package_io import read_extraction_package


BATCH_ID = "B_CLASS_371_20260719"
EVIDENCE_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
STRUCTURED_ROOT = EVIDENCE_ROOT / "structured_evidence"
PACKAGE_ROOT = ROOT / "data/interim/extraction/B"
METADATA_DB = ROOT / "data/raw/literature/metadata/literature.sqlite3"
OUTPUT = ROOT / "runs/extraction/B/releases/B_CLASS_139_20260720"

CATALOG_COLUMNS = (
    "source_id",
    "title",
    "year",
    "doi",
    "publication_venue",
    "source_type",
    "parse_status",
    "download_status",
    "package_kind",
    "formal_run_count",
    "atomic_observation_count",
    "measurement_count",
    "entity_count",
    "source_package_path",
    "primary_search_path",
    "data_interpretation",
)

FIELD_INDEX_COLUMNS = (
    "source_id",
    "record_kind",
    "record_id",
    "value_origin",
    "canonical_table",
    "canonical_field",
    "value_raw",
    "value_normalized",
    "unit",
    "qualifier_or_context",
    "value_status",
    "confidence",
    "evidence_span_id",
    "source_locator",
    "data_path",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, columns: Iterable[str], rows: Iterable[dict[str, Any]]) -> None:
    names = list(columns)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: "" if row.get(name) is None else row.get(name) for name in names})


def actual_packages() -> dict[str, Path]:
    packages: dict[str, Path] = {}
    for package in sorted(PACKAGE_ROOT.glob("*.extraction.json")):
        rows = read_extraction_package(package)["tables"]["source_master"]
        if len(rows) != 1 or not rows[0].get("source_id"):
            raise ValueError(f"Invalid actual eight-table package: {package}")
        source_id = rows[0]["source_id"]
        if source_id in packages:
            raise ValueError(f"Duplicate actual source package: {source_id}")
        packages[source_id] = package
    return packages


def load_metadata() -> dict[str, dict[str, Any]]:
    with sqlite3.connect(METADATA_DB) as connection:
        connection.row_factory = sqlite3.Row
        return {
            str(row["source_id"]): dict(row)
            for row in connection.execute("SELECT * FROM works WHERE priority_tier = 'B'")
        }


def empty_source_master(meta: dict[str, Any], manifest: dict[str, str]) -> dict[str, str]:
    state = manifest["extraction_state"]
    source_id = str(meta["source_id"])
    if state == "parsed_not_extractable":
        screening_class = "parsed_not_extractable"
        scope = "Parsed full text; no source-level CNT-production evidence suitable for a formal run package."
    else:
        screening_class = "candidate_extract"
        scope = "Parsed full text; source-span evidence is published in the evidence layer before formal run reconstruction."
    return {
        "source_id": source_id,
        "source_type": str(meta.get("source_type") or "paper"),
        "source_title": str(meta.get("title") or source_id),
        "publication_year": str(meta.get("year") or "not_reported"),
        "authors_or_assignee": str(meta.get("authors") or "not_reported"),
        "publication_venue": str(meta.get("journal") or "not_reported"),
        "doi_or_patent_no": str(meta.get("doi") or "not_reported"),
        "source_link": str(meta.get("source_link") or "not_reported"),
        "source_database": "local_metadata_registry",
        "source_language": str(meta.get("language") or "not_reported"),
        "local_file_path": "registered_locally; see catalog/source_catalog.csv",
        "pdf_status": str(manifest.get("download_status") or "validated"),
        "screening_class": screening_class,
        "source_section_scope": scope,
        "extraction_status": "needs_review",
        "review_status": "pending_review",
        "notes": (
            "No formal source_run is emitted until a reviewer confirms run boundaries. "
            "Candidate-span values remain searchable in evidence/ and catalog/field_index.csv."
        ),
    }


def package_row_counts(package: Path) -> dict[str, int]:
    tables = read_extraction_package(package)["tables"]
    return {table: len(tables[table]) for table in TABLES}


def write_source_packages(
    temporary: Path,
    parseable: list[dict[str, str]],
    metadata: dict[str, dict[str, Any]],
    packages: dict[str, Path],
) -> dict[str, dict[str, int]]:
    root = temporary / "source_packages"
    root.mkdir()
    counts: dict[str, dict[str, int]] = {}
    for manifest in parseable:
        source_id = manifest["source_id"]
        destination = root / source_id
        destination.mkdir()
        if source_id in packages:
            package_tables = read_extraction_package(packages[source_id])["tables"]
            for table in TABLES:
                write_table(destination, table, package_tables[table])
            counts[source_id] = {table: len(package_tables[table]) for table in TABLES}
            continue
        master = empty_source_master(metadata[source_id], manifest)
        for table in TABLES:
            rows = [master] if table == "source_master" else []
            write_table(destination, table, rows)
        counts[source_id] = {table: (1 if table == "source_master" else 0) for table in TABLES}
    return counts


def write_combined_eight_tables(temporary: Path, parseable: list[dict[str, str]]) -> dict[str, int]:
    source_root = temporary / "source_packages"
    destination = temporary / "eight_tables"
    destination.mkdir()
    counts: dict[str, int] = {}
    for table in TABLES:
        rows: list[dict[str, str]] = []
        for manifest in parseable:
            rows.extend(read_csv(source_root / manifest["source_id"] / f"{table}.csv"))
        write_csv(destination / f"{table}.csv", SCHEMA["tables"][table]["columns"], rows)
        counts[table] = len(rows)
    return counts


def copy_evidence_layer(temporary: Path) -> tuple[dict[str, list[dict[str, str]]], dict[str, int]]:
    destination = temporary / "evidence"
    destination.mkdir()
    files = ("atomic_observations.csv", "measurements.csv", "entities.csv", "source_summary.csv")
    rows: dict[str, list[dict[str, str]]] = {}
    counts: dict[str, int] = {}
    for name in files:
        source = STRUCTURED_ROOT / name
        if not source.is_file():
            raise FileNotFoundError(f"Missing structured-evidence file: {source}")
        shutil.copy2(source, destination / name)
        rows[name] = read_csv(source)
        counts[name.removesuffix(".csv")] = len(rows[name])
    return rows, counts


def formal_field_rows(temporary: Path, parseable: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    ignored = {"source_id", "run_id", "evidence_id", "issue_id", "product_id", "catalyst_id", "process_stage_id"}
    for manifest in parseable:
        source_id = manifest["source_id"]
        package = temporary / "source_packages" / source_id
        for table in TABLES:
            for record in read_csv(package / f"{table}.csv"):
                identity = SCHEMA["tables"][table]["row_identity"]
                record_id = "|".join(record.get(field, "") for field in identity)
                for field, value in record.items():
                    if field in ignored or not value or value in {"not_reported", "not_applicable"}:
                        continue
                    rows.append(
                        {
                            "source_id": source_id,
                            "record_kind": table,
                            "record_id": record_id,
                            "value_origin": "formal_eight_table",
                            "canonical_table": table,
                            "canonical_field": field,
                            "value_raw": value,
                            "value_normalized": value,
                            "unit": "",
                            "qualifier_or_context": "",
                            "value_status": "needs_review",
                            "confidence": "",
                            "evidence_span_id": "",
                            "source_locator": "",
                            "data_path": f"source_packages/{source_id}/{table}.csv",
                        }
                    )
    return rows


def evidence_field_rows(evidence: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    layouts = {
        "atomic_observations.csv": ("atomic_observation", "observation_id", "qualifier"),
        "measurements.csv": ("measurement", "measurement_id", "context"),
        "entities.csv": ("entity", "entity_id", ""),
    }
    for filename, (kind, record_column, context_column) in layouts.items():
        for record in evidence[filename]:
            rows.append(
                {
                    "source_id": record["source_id"],
                    "record_kind": kind,
                    "record_id": record[record_column],
                    "value_origin": "candidate_source_span",
                    "canonical_table": record.get("canonical_table", ""),
                    "canonical_field": record.get("canonical_field", ""),
                    "value_raw": record.get("value_raw", ""),
                    "value_normalized": record.get("value_normalized", ""),
                    "unit": record.get("unit", ""),
                    "qualifier_or_context": record.get(context_column, "") if context_column else "",
                    "value_status": record.get("value_status", ""),
                    "confidence": record.get("confidence", ""),
                    "evidence_span_id": record.get("span_id", ""),
                    "source_locator": record.get("page_range", ""),
                    "data_path": f"evidence/{filename}",
                }
            )
    return rows


def build_catalog(
    parseable: list[dict[str, str]],
    metadata: dict[str, dict[str, Any]],
    packages: dict[str, Path],
    package_counts: dict[str, dict[str, int]],
    evidence_rows: dict[str, list[dict[str, str]]],
    evidence_ledger_ids: set[str],
) -> list[dict[str, str]]:
    evidence_summary = {row["source_id"]: row for row in evidence_rows["source_summary.csv"]}
    catalog: list[dict[str, str]] = []
    for manifest in parseable:
        source_id = manifest["source_id"]
        meta = metadata[source_id]
        actual = source_id in packages
        summary = evidence_summary.get(source_id, {})
        if source_id in evidence_ledger_ids:
            package_kind = "evidence_ledger_eight_table"
            interpretation = "Every candidate span is formally represented as a source-level ledger record; it must not be interpreted as a reconstructed experimental run."
            primary = f"source_packages/{source_id}/"
        elif actual:
            package_kind = "formal_eight_table"
            interpretation = "Formal rows are source-backed first-pass transcriptions; inspect evidence_index.csv before reuse."
            primary = f"source_packages/{source_id}/"
        elif manifest["extraction_state"] == "parsed_not_extractable":
            package_kind = "parsed_no_extractable_run"
            interpretation = "The text parsed successfully but no CNT-production evidence justified a formal run row."
            primary = f"source_packages/{source_id}/source_master.csv"
        else:
            package_kind = "candidate_evidence_only"
            interpretation = "All extracted source-span observations are searchable in evidence/; no run boundary has been asserted."
            primary = "catalog/field_index.csv"
        catalog.append(
            {
                "source_id": source_id,
                "title": str(meta.get("title") or manifest.get("title", "")),
                "year": str(meta.get("year") or manifest.get("year", "")),
                "doi": str(meta.get("doi") or manifest.get("doi", "")),
                "publication_venue": str(meta.get("journal") or ""),
                "source_type": str(meta.get("source_type") or "paper"),
                "parse_status": manifest["parse_status"],
                "download_status": manifest.get("download_status", ""),
                "package_kind": package_kind,
                "formal_run_count": str(package_counts[source_id]["source_run"]),
                "atomic_observation_count": summary.get("atomic_evidence_count", "0"),
                "measurement_count": summary.get("measurement_count", "0"),
                "entity_count": summary.get("entity_count", "0"),
                "source_package_path": f"source_packages/{source_id}/",
                "primary_search_path": primary,
                "data_interpretation": interpretation,
            }
        )
    return catalog


def write_readme(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(
        """# B 类可解析来源数据集（139 篇）

这是 `data/` 中唯一面向检索和使用的 B 类交付入口。不要从 `raw/`、`interim/` 或历史批次目录查找最终数据。

## 从哪里开始

1. 按题名、DOI、年份或 `source_id` 找论文：`catalog/source_catalog.csv`。
2. 按催化剂、气源、温度、产率或 CNT 特征找值：`catalog/field_index.csv`。
3. 查看单篇固定八表：`source_packages/<source_id>/`。
4. 跨来源分析已确认的实验行：`eight_tables/` 中的八张合并 CSV。
5. 回到原文证据定位：`evidence/atomic_observations.csv`、`measurements.csv`、`entities.csv`，使用 `source_id` + `evidence_span_id`。

## 数据状态必须区分

- `formal_eight_table`：存在已重建的实验运行；所有值仍为第一轮 `needs_review`，但已链接到该包的 `evidence_index.csv`。
- `evidence_ledger_eight_table`：全文中的候选证据已全部进入八表，并逐条链接原始跨度；`source_evidence_ledger` 仅是来源级锚点，绝不是把跨段信息拼成的实验运行。
- `parsed_no_extractable_run`：全文可解析，但没有足以构造 CNT 生产实验行的来源证据。

每个 139 篇来源都有相同的 8 个 CSV 文件。`parsed_no_extractable_run` 的正式事实表为空；这表示“没有可合法、可追溯的正式运行”，不是遗漏。可检索的来源证据在 `evidence/` 与 `catalog/field_index.csv`。

## 规模

```text
parseable_sources: {parseable_sources}
formal_sources: {formal_sources}
formal_runs: {formal_runs}
evidence_ledger_sources: {evidence_ledger_sources}
evidence_ledger_records: {evidence_ledger_records}
candidate_observations: {candidate_observations}
measurements: {measurements}
entities: {entities}
```
""".format(**manifest),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a clear B-class 139-source data directory.")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--replace", action="store_true", help="Replace the existing generated dataset.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output.resolve()
    release_root = (ROOT / "runs/extraction/B/releases").resolve()
    if output.parent != release_root or not output.name.startswith("B_CLASS_139_"):
        raise ValueError(f"Refusing output outside the B-class run area: {output}")
    if output.exists() and not args.replace:
        raise FileExistsError(f"Output already exists: {output}; pass --replace to refresh it")
    output.parent.mkdir(parents=True, exist_ok=True)

    manifest = read_csv(EVIDENCE_ROOT / "manifest.csv")
    parseable = [row for row in manifest if row.get("parse_status") == "success"]
    if len(parseable) != 139:
        raise ValueError(f"Expected 139 parseable B sources, found {len(parseable)}")
    metadata = load_metadata()
    missing_metadata = sorted({row["source_id"] for row in parseable} - set(metadata))
    if missing_metadata:
        raise ValueError("Parseable sources missing metadata: " + ";".join(missing_metadata))
    packages = actual_packages()
    unknown_packages = sorted(set(packages) - {row["source_id"] for row in parseable})
    if unknown_packages:
        raise ValueError("Actual packages are not parseable B sources: " + ";".join(unknown_packages))

    evidence_ledger_ids: set[str] = set()
    temporary = Path(tempfile.mkdtemp(prefix=".b_class_139.", dir=output.parent))
    try:
        package_counts = write_source_packages(temporary, parseable, metadata, packages)
        combined_counts = write_combined_eight_tables(temporary, parseable)
        evidence, evidence_counts = copy_evidence_layer(temporary)
        catalog_root = temporary / "catalog"
        catalog_root.mkdir()
        catalog = build_catalog(parseable, metadata, packages, package_counts, evidence, evidence_ledger_ids)
        write_csv(catalog_root / "source_catalog.csv", CATALOG_COLUMNS, catalog)
        write_csv(catalog_root / "b_class_coverage.csv", list(manifest[0]), manifest)
        field_rows = formal_field_rows(temporary, parseable) + evidence_field_rows(evidence)
        field_rows.sort(
            key=lambda row: (
                row["source_id"], row["canonical_table"], row["canonical_field"], row["record_kind"], row["record_id"]
            )
        )
        write_csv(catalog_root / "field_index.csv", FIELD_INDEX_COLUMNS, field_rows)
        package_kind_counts = Counter(row["package_kind"] for row in catalog)
        release_manifest = {
            "dataset": "B-class parseable-source delivery",
            "parseable_sources": len(parseable),
            "formal_sources": len(packages) - len(evidence_ledger_ids),
            "formal_runs": sum(
                package_counts[source_id]["source_run"]
                for source_id in packages
                if source_id not in evidence_ledger_ids
            ),
            "evidence_ledger_sources": len(evidence_ledger_ids),
            "evidence_ledger_records": len(evidence_ledger_ids),
            "candidate_observations": evidence_counts["atomic_observations"],
            "measurements": evidence_counts["measurements"],
            "entities": evidence_counts["entities"],
            "package_kind_counts": dict(sorted(package_kind_counts.items())),
            "eight_table_row_counts": combined_counts,
            "field_index_rows": len(field_rows),
            "source_package_layout": "Every parseable source has eight schema CSV files under source_packages/.",
            "formalization_policy": "Candidate source-span evidence is never converted to a reconstructed experimental run before its run boundary is confirmed.",
        }
        (temporary / "MANIFEST.json").write_text(
            json.dumps(release_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        write_readme(temporary / "README.md", release_manifest)
        if output.exists():
            shutil.rmtree(output)
        shutil.move(str(temporary), str(output))
        print(json.dumps(release_manifest, ensure_ascii=False, indent=2))
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


if __name__ == "__main__":
    main()
