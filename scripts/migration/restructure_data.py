#!/usr/bin/env python3
"""Migrate ``data/`` to the raw/interim/processed/benchmark/audit lifecycle.

The migration is intentionally phased and idempotent:

1. ``inventory`` hashes the pre-migration files and writes the manifest/baseline.
2. ``migrate`` only copies, converts, or externalizes; it never deletes sources.
3. ``verify`` checks raw PDFs, the formal eight tables, extraction packages,
   parsed-text cardinality, and the private company copy.
4. ``archive`` creates an external ZIP from the inventory and records its SHA-256.
5. ``cleanup`` is refused unless both verification and archive checks pass.
6. ``cleanup-private-company`` separately removes only the three named legacy
   directories after validating the canonical private tree and archive hash.

Run ``all`` to execute the safe phases through archive.  Cleanup remains an
explicit command so that a failed project/benchmark test can never be hidden by
deleting the legacy inputs first.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import mimetypes
import os
import re
import shutil
import sqlite3
import stat
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
AUDIT_SUMMARIES = DATA / "audit" / "summaries"
MANIFEST = AUDIT_SUMMARIES / "migration_manifest.csv"
BASELINE = AUDIT_SUMMARIES / "migration_baseline.json"
VERIFY_REPORT = AUDIT_SUMMARIES / "migration_verification.json"
ARCHIVE_DIR = Path(os.environ.get("CNT_ARCHIVE_DIR", r"E:\CNT-LitSight-archive"))
ARCHIVE_STEM = "20260720_pre_restructure"
PRIVATE_COMPANY = Path(
    os.environ.get(
        "CNT_COMPANY_DATA_DIR",
        str(ROOT.parent / "CNT-LitSight-private" / "company"),
    )
)

TABLES = (
    "source_master",
    "source_run",
    "catalyst_system",
    "reactor_process_gas",
    "yield_quality",
    "cost_scale_review",
    "evidence_index",
    "review_issue_log",
)

AGGREGATES = {
    "A": DATA
    / "interim/candidate_extracts/A_class/batches/A_CLASS_208_20260716/consolidated_eight_tables",
    "B": DATA / "processed/eight_tables",
    "C": DATA
    / "interim/candidate_extracts/C_class/delivery_candidates/C_CLASS_COMPLETE_20260720/eight_tables",
}

LEGACY_ROOTS = (
    DATA / "company",
    DATA / "review",
    DATA / "interim/candidate_extracts",
    DATA / "interim/parsed_text/fulltext",
    DATA / "interim/parsed_text/sections",
    DATA / "interim/screening",
    DATA / "interim/review_queue/archive_pre_restructure_20260720",
    DATA / "interim/review_queue/extraction",
    DATA / "interim/review_queue/extraction_control",
    DATA / "interim/review_queue/fulltext_pilot_v1",
    DATA / "interim/review_queue/runtime",
    DATA / "raw/literature/fulltext",
    DATA / "raw/literature/metadata/api_responses",
    DATA / "raw/literature/metadata/run_reports",
    DATA / "benchmark/samples",
    DATA / "benchmark/fixtures/templates",
    DATA / "benchmark/results/archive_interim",
    DATA / "benchmark/results/screening_benchmark/history",
    DATA / "processed/analysis/release_support",
    ROOT / "reports/pipeline_runs",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, columns: Iterable[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    names = list(columns)
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in names})
    temporary.replace(path)


def copy_verified(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and sha256_file(source) == sha256_file(target):
        return
    temporary = target.with_suffix(target.suffix + ".part")
    shutil.copy2(source, temporary)
    if sha256_file(source) != sha256_file(temporary):
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"copy checksum mismatch: {source} -> {target}")
    temporary.replace(target)


def formal_baseline() -> dict[str, Any]:
    root = DATA / "processed/eight_tables"
    result: dict[str, Any] = {"row_counts": {}, "columns": {}}
    for table in TABLES:
        path = root / f"{table}.csv"
        rows = read_csv(path)
        result["row_counts"][table] = len(rows)
        result["columns"][table] = list(rows[0]) if rows else []
    masters = read_csv(root / "source_master.csv")
    runs = read_csv(root / "source_run.csv")
    result["source_ids"] = sorted({row.get("source_id", "") for row in masters if row.get("source_id")})
    result["run_ids"] = sorted({row.get("run_id", "") for row in runs if row.get("run_id")})
    return result


def source_id_from_name(path: Path) -> str:
    match = re.match(r"^(LIT_[0-9A-Fa-f]{16})(?:_|$)", path.stem)
    if match:
        return match.group(1).upper()
    match = re.match(r"^(P\d{3})(?:_|$)", path.stem)
    return match.group(1) if match else path.stem


def private_company_target(relative: Path) -> Path:
    """Map the former public company tree into the shallow private tree."""

    parts = relative.parts
    if not parts:
        return PRIVATE_COMPANY
    if parts[0] == "catalog":
        return PRIVATE_COMPANY / parts[-1]
    if parts[0] == "internal_lab":
        return PRIVATE_COMPANY / f"internal_lab_{parts[-1]}"
    if parts[0] == "review" and len(parts) > 1 and parts[1] == "source_packages":
        package_parts = parts[2:]
        if "eight_tables" in package_parts:
            return PRIVATE_COMPANY / "eight_tables" / parts[-1]
        if parts[-1].lower() == "readme.md":
            return PRIVATE_COMPANY / "source_package_README.md"
        return PRIVATE_COMPANY / parts[-1]
    if parts[0] == "review":
        return PRIVATE_COMPANY / parts[-1]
    if parts[0] == "raw":
        return PRIVATE_COMPANY / "raw" / parts[-1]
    return PRIVATE_COMPANY / parts[-1]


def classify(path: Path) -> tuple[str, str]:
    value = rel(path)
    posix = value.replace("\\", "/")
    if posix.startswith("data/company/"):
        return "externalize_private", str(
            private_company_target(Path(posix).relative_to("data/company"))
        )
    if posix.startswith("data/interim/parsed_text/"):
        return "convert_parsed_json", "data/interim/parsed_text/by_source/{source_id}.parsed.json"
    if posix.startswith("data/interim/candidate_extracts/"):
        if "/renders/" in f"/{posix}/" or posix.startswith("data/interim/candidate_extracts/renders/"):
            return "copy_cache", f"cache/renders/{Path(posix).name}"
        return "convert_or_archive_extraction", "data/interim/extraction/{tier}/{source_id}.extraction.json"
    if posix.startswith("data/interim/review_queue/archive_pre_restructure_20260720/"):
        return "archive_external", str(ARCHIVE_DIR / f"{ARCHIVE_STEM}.zip")
    if posix.startswith("data/review/"):
        return "copy_audit", posix.replace("data/review/", "data/audit/samples/", 1)
    if posix.startswith("data/benchmark/samples/"):
        return "copy_fixture", posix.replace("data/benchmark/samples/", "data/benchmark/fixtures/", 1)
    if posix.startswith("data/benchmark/results/archive_interim/") or "/screening_benchmark/history/" in posix:
        return "archive_external", str(ARCHIVE_DIR / f"{ARCHIVE_STEM}.zip")
    if posix.startswith("data/raw/literature/metadata/api_responses/"):
        return "compress_jsonl_gz", "data/raw/api_responses/{provider}/{batch}.jsonl.gz"
    if posix.startswith("data/raw/literature/metadata/run_reports/"):
        return "copy_run", posix.replace("data/raw/literature/metadata/run_reports/", "runs/metadata/", 1)
    if posix.startswith("data/raw/literature/fulltext/reports/"):
        return "copy_run", posix.replace("data/raw/literature/fulltext/reports/", "runs/fulltext/", 1)
    if posix.startswith("data/raw/literature/fulltext/supplementary/"):
        if any(part.lower().startswith("rendered") for part in path.parts):
            return "copy_cache", f"cache/renders/supplements/{path.name}"
        return "copy_raw_supplement", posix.replace(
            "data/raw/literature/fulltext/supplementary/", "data/raw/literature/supplements/", 1
        )
    if posix.startswith("data/raw/literature/fulltext/") and path.suffix.lower() in {".html", ".xml"}:
        return "copy_raw_html", f"data/raw/literature/html/{source_id_from_name(path)}{path.suffix.lower()}"
    if posix.startswith("data/raw/literature/fulltext/"):
        return "copy_fulltext_registry", f"data/raw/literature/metadata/fulltext_registry/{path.name}"
    if posix.startswith("data/raw/literature/pdf/") and path.suffix.lower() == ".pdf":
        return "copy_canonical_pdf", f"data/raw/literature/pdf/{source_id_from_name(path)}.pdf"
    if posix.startswith("reports/pipeline_runs/"):
        return "copy_run", posix.replace("reports/pipeline_runs/", "runs/pipeline/", 1)
    return "retain", posix


def inventory() -> dict[str, Any]:
    AUDIT_SUMMARIES.mkdir(parents=True, exist_ok=True)
    excluded = {MANIFEST.resolve(), BASELINE.resolve(), VERIFY_REPORT.resolve()}
    roots = [DATA, ROOT / "reports/pipeline_runs"]
    files: list[Path] = []
    for scan_root in roots:
        if scan_root.exists():
            files.extend(path for path in scan_root.rglob("*") if path.is_file() and path.resolve() not in excluded)
    files = sorted(dict.fromkeys(path.resolve() for path in files), key=lambda item: rel(item))
    rows: list[dict[str, Any]] = []
    for index, path in enumerate(files, start=1):
        action, new_path = classify(path)
        rows.append(
            {
                "old_path": rel(path),
                "new_path": new_path,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "action": action,
                "status": "planned" if action != "retain" else "retained",
            }
        )
        if index % 1000 == 0:
            print(f"inventory_hashed={index}", flush=True)
    write_csv(
        MANIFEST,
        ("old_path", "new_path", "size_bytes", "sha256", "action", "status"),
        rows,
    )
    parsed_old = DATA / "interim/parsed_text"
    parsed_ids = {
        item.name
        for root in (parsed_old / "fulltext", parsed_old / "sections")
        if root.exists()
        for item in root.iterdir()
        if item.name.lower() != "readme.md"
    }
    parsed_ids = {Path(name).stem for name in parsed_ids}
    baseline = {
        "created_at": utc_now(),
        "inventory_file_count": len(rows),
        "inventory_bytes": sum(int(row["size_bytes"]) for row in rows),
        "raw_pdf_count": len(list((DATA / "raw").rglob("*.pdf"))),
        "parsed_source_count": len(parsed_ids),
        "formal_eight_tables": formal_baseline(),
        "private_company_dir": str(PRIVATE_COMPANY.resolve()),
        "archive_dir": str(ARCHIVE_DIR.resolve()),
    }
    write_json(BASELINE, baseline)
    print(json.dumps(baseline, ensure_ascii=False, indent=2))
    return baseline


def ensure_structure() -> None:
    directories = (
        "data/raw/literature/pdf",
        "data/raw/literature/html",
        "data/raw/literature/metadata",
        "data/raw/literature/supplements",
        "data/raw/api_responses/openalex",
        "data/raw/api_responses/semantic_scholar",
        "data/raw/api_responses/crossref",
        "data/raw/api_responses/unpaywall",
        "data/interim/parsed_text/by_source",
        "data/interim/extraction/A",
        "data/interim/extraction/B",
        "data/interim/extraction/C",
        "data/interim/evidence",
        "data/interim/review_queue",
        "data/processed/eight_tables",
        "data/processed/analysis",
        "data/processed/snapshots",
        "data/benchmark/gold",
        "data/benchmark/fixtures",
        "data/benchmark/templates",
        "data/benchmark/results",
        "data/audit/samples",
        "data/audit/issues",
        "data/audit/summaries",
        "runs",
        "cache/renders",
        "reports",
    )
    for directory in directories:
        (ROOT / directory).mkdir(parents=True, exist_ok=True)


def local_paper_mapping() -> dict[str, str]:
    mapping: dict[str, str] = {}
    root = DATA / "benchmark/samples/six_papers"
    if not root.exists():
        root = DATA / "benchmark/fixtures/six_papers"
    for package in root.glob("P*"):
        masters = read_csv(package / "source_master.csv")
        if not masters:
            continue
        old_name = Path(masters[0].get("local_file_path", "")).name
        if old_name:
            mapping[old_name] = masters[0]["source_id"]
    return mapping


def migrate_raw() -> None:
    pdf_root = DATA / "raw/literature/pdf"
    local_mapping = local_paper_mapping()
    original_pdfs = list(pdf_root.rglob("*.pdf")) if pdf_root.exists() else []
    for source in original_pdfs:
        if source.parent == pdf_root and re.fullmatch(r"(?:LIT_[0-9A-F]{16}|P.+)\.pdf", source.name):
            continue
        source_id = local_mapping.get(source.name, source_id_from_name(source))
        copy_verified(source, pdf_root / f"{source_id}.pdf")

    legacy = DATA / "raw/literature/fulltext"
    if legacy.exists():
        html_candidates: dict[tuple[str, str], list[Path]] = defaultdict(list)
        for source in legacy.rglob("*"):
            if not source.is_file() or "supplementary" in source.parts or "reports" in source.parts:
                continue
            if source.suffix.lower() in {".html", ".xml"}:
                html_candidates[(source_id_from_name(source), source.suffix.lower())].append(source)
        for (source_id, suffix), candidates in sorted(html_candidates.items()):
            source = sorted(candidates, key=lambda item: (item.stat().st_size, str(item)), reverse=True)[0]
            copy_verified(source, DATA / f"raw/literature/html/{source_id}{suffix}")

        supplements = legacy / "supplementary"
        if supplements.exists():
            for source in supplements.rglob("*"):
                if not source.is_file():
                    continue
                relative = source.relative_to(supplements)
                if any(part.lower().startswith("rendered") for part in relative.parts):
                    target = ROOT / "cache/renders/supplements" / relative
                else:
                    target = DATA / "raw/literature/supplements" / relative
                copy_verified(source, target)

        registry = DATA / "raw/literature/metadata/fulltext_registry"
        for source in legacy.iterdir():
            if source.is_file() and source.suffix.lower() not in {".html", ".xml", ".md"}:
                copy_verified(source, registry / source.name)

        registry_db = registry / "fulltext.sqlite3"
        if registry_db.exists():
            with sqlite3.connect(registry_db) as connection:
                table_names = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
                for table in ("fulltext_source", "fulltext_acquisition_queue"):
                    if table not in table_names:
                        continue
                    columns = {
                        row[1] for row in connection.execute(f"PRAGMA table_info({table})")
                    }
                    if not {"source_id", "local_path"}.issubset(columns):
                        continue
                    rows = connection.execute(
                        f"SELECT rowid,source_id,local_path FROM {table} WHERE local_path != ''"
                    ).fetchall()
                    for rowid, source_id, local_path in rows:
                        suffix = Path(str(local_path)).suffix.lower()
                        if suffix == ".pdf":
                            candidate = DATA / f"raw/literature/pdf/{source_id}.pdf"
                        elif suffix in {".html", ".xml"}:
                            candidate = DATA / f"raw/literature/html/{source_id}{suffix}"
                        else:
                            continue
                        if not candidate.exists():
                            artifact_id = source_id_from_name(Path(str(local_path)))
                            if suffix == ".pdf":
                                candidate = DATA / f"raw/literature/pdf/{artifact_id}.pdf"
                            else:
                                candidate = DATA / f"raw/literature/html/{artifact_id}{suffix}"
                        if candidate.exists():
                            connection.execute(
                                f"UPDATE {table} SET local_path=? WHERE rowid=?",
                                (rel(candidate), rowid),
                            )
                connection.commit()

        reports = legacy / "reports"
        if reports.exists():
            for source in reports.rglob("*"):
                if source.is_file():
                    copy_verified(source, ROOT / "runs/fulltext" / source.relative_to(reports))

    api_root = DATA / "raw/literature/metadata/api_responses"
    if api_root.exists():
        for batch in sorted(path for path in api_root.iterdir() if path.is_dir()):
            for provider in sorted(path for path in batch.iterdir() if path.is_dir()):
                source_files = sorted(path for path in provider.rglob("*") if path.is_file())
                if not source_files:
                    continue
                target = DATA / "raw/api_responses" / provider.name / f"{batch.name}.jsonl.gz"
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_suffix(target.suffix + ".part")
                with gzip.open(temporary, "wt", encoding="utf-8", newline="\n") as handle:
                    for source in source_files:
                        try:
                            payload: Any = json.loads(source.read_text(encoding="utf-8-sig"))
                        except (UnicodeError, json.JSONDecodeError):
                            payload = {"raw_text": source.read_text(encoding="utf-8", errors="replace")}
                        handle.write(
                            json.dumps(
                                {"source_path": rel(source), "sha256": sha256_file(source), "payload": payload},
                                ensure_ascii=False,
                                separators=(",", ":"),
                            )
                            + "\n"
                        )
                temporary.replace(target)

    run_reports = DATA / "raw/literature/metadata/run_reports"
    if run_reports.exists():
        for source in run_reports.rglob("*"):
            if source.is_file():
                copy_verified(source, ROOT / "runs/metadata" / source.relative_to(run_reports))

    pipeline_reports = ROOT / "reports/pipeline_runs"
    if pipeline_reports.exists():
        for source in pipeline_reports.rglob("*"):
            if source.is_file():
                copy_verified(source, ROOT / "runs/pipeline" / source.relative_to(pipeline_reports))


def migrate_parsed_text() -> int:
    old = DATA / "interim/parsed_text"
    fulltext_root = old / "fulltext"
    sections_root = old / "sections"
    identifiers: set[str] = set()
    for root in (fulltext_root, sections_root):
        if not root.exists():
            continue
        identifiers.update(path.stem for path in root.glob("*.txt"))
        identifiers.update(path.name for path in root.iterdir() if path.is_dir())
    output_root = old / "by_source"
    for source_id in sorted(identifiers):
        package = sections_root / source_id
        full_text_path = package / "full_text.txt"
        if not full_text_path.exists():
            full_text_path = fulltext_root / f"{source_id}.txt"
        if not full_text_path.exists():
            full_text_path = sections_root / f"{source_id}.txt"
        payload: dict[str, Any] = {
            "source_id": source_id,
            "full_text": full_text_path.read_text(encoding="utf-8", errors="replace") if full_text_path.exists() else "",
            "sections": [],
        }
        if package.is_dir():
            for name, key in (
                ("document_metadata.json", "document_metadata"),
                ("sections.json", "sections"),
                ("figures_captions.json", "figure_captions"),
                ("tables.json", "tables"),
                ("parse_report.json", "parse_report"),
            ):
                path = package / name
                if path.exists():
                    payload[key] = json.loads(path.read_text(encoding="utf-8-sig"))
        write_json(output_root / f"{source_id}.parsed.json", payload)
    return len(identifiers)


def load_tables(root: Path) -> dict[str, list[dict[str, str]]]:
    return {table: read_csv(root / f"{table}.csv") for table in TABLES}


def split_tables(tables: dict[str, list[dict[str, str]]]) -> dict[str, dict[str, list[dict[str, str]]]]:
    source_ids = [row["source_id"] for row in tables["source_master"] if row.get("source_id")]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("duplicate source_id in aggregate source_master")
    run_to_source = {
        row["run_id"]: row["source_id"]
        for row in tables["source_run"]
        if row.get("run_id") and row.get("source_id")
    }
    output: dict[str, dict[str, list[dict[str, str]]]] = {}
    for source_id in source_ids:
        run_ids = {run_id for run_id, owner in run_to_source.items() if owner == source_id}
        package: dict[str, list[dict[str, str]]] = {}
        for table, rows in tables.items():
            selected = [
                row
                for row in rows
                if row.get("source_id") == source_id
                or (row.get("run_id") and row.get("run_id") in run_ids)
            ]
            package[table] = selected
        output[source_id] = package
    return output


def canonical_source_path(source_id: str) -> str:
    """Return the preferred canonical local artifact for a source."""

    parsed = DATA / f"interim/parsed_text/by_source/{source_id}.parsed.json"
    if parsed.is_file():
        return rel(parsed)
    pdf = DATA / f"raw/literature/pdf/{source_id}.pdf"
    if pdf.is_file():
        return rel(pdf)
    for suffix in (".html", ".xml"):
        document = DATA / f"raw/literature/html/{source_id}{suffix}"
        if document.is_file():
            return rel(document)
    return ""


def normalize_source_master_paths(rows: list[dict[str, str]]) -> None:
    for row in rows:
        source_id = row.get("source_id", "")
        canonical = canonical_source_path(source_id) if source_id else ""
        if canonical:
            row["local_file_path"] = canonical


def normalize_formal_source_paths() -> None:
    path = DATA / "processed/eight_tables/source_master.csv"
    rows = read_csv(path)
    if not rows:
        return
    columns = list(rows[0])
    normalize_source_master_paths(rows)
    write_csv(path, columns, rows)


def rebuild_process_comparison() -> None:
    """Build the requested process-level comparison from the formal run view."""

    source = DATA / "processed/analysis/run_level_dataset.csv"
    rows = read_csv(source)
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (
            row.get("reactor_type") or "not_reported",
            row.get("carbon_source") or "not_reported",
        )
        groups[key].append(row)
    output = []
    for (reactor_type, carbon_source), members in sorted(groups.items()):
        yields: list[float] = []
        for member in members:
            raw = (member.get("max_CNT_yield_g_gcat") or "").strip()
            try:
                value = float(raw)
            except ValueError:
                continue
            if value > 0:
                yields.append(value)
        output.append(
            {
                "reactor_type": reactor_type,
                "carbon_source": carbon_source,
                "run_count": len(members),
                "source_count": len({item.get("source_id", "") for item in members}),
                "runs_with_quantitative_yield": len(yields),
                "mean_max_CNT_yield_g_gcat": f"{sum(yields) / len(yields):.6g}" if yields else "",
                "max_CNT_yield_g_gcat": f"{max(yields):.6g}" if yields else "",
            }
        )
    write_csv(
        DATA / "processed/analysis/process_comparison.csv",
        (
            "reactor_type",
            "carbon_source",
            "run_count",
            "source_count",
            "runs_with_quantitative_yield",
            "mean_max_CNT_yield_g_gcat",
            "max_CNT_yield_g_gcat",
        ),
        output,
    )


def migrate_extractions() -> dict[str, Any]:
    output: dict[str, Any] = {"tiers": {}, "total_sources": 0}
    seen: set[str] = set()
    for tier, aggregate in AGGREGATES.items():
        tables = load_tables(aggregate)
        packages = split_tables(tables)
        overlap = seen.intersection(packages)
        if overlap:
            raise ValueError(f"source_id occurs in multiple relevance tiers: {sorted(overlap)[:10]}")
        seen.update(packages)
        input_counts = {table: len(rows) for table, rows in tables.items()}
        output_counts = {table: 0 for table in TABLES}
        for source_id, package in packages.items():
            normalize_source_master_paths(package["source_master"])
            for table in TABLES:
                output_counts[table] += len(package[table])
            master = package["source_master"][0] if package["source_master"] else {}
            payload = {
                "source_id": source_id,
                "relevance_tier": tier,
                "extraction_status": master.get("extraction_status") or "candidate_extract",
                "tables": package,
            }
            write_json(DATA / f"interim/extraction/{tier}/{source_id}.extraction.json", payload)
        if input_counts != output_counts:
            raise RuntimeError(f"{tier} extraction row mismatch: {input_counts} != {output_counts}")
        output["tiers"][tier] = {
            "source_count": len(packages),
            "input_row_counts": input_counts,
            "output_row_counts": output_counts,
            "input_root": rel(aggregate),
        }
    output["total_sources"] = len(seen)
    write_csv(
        DATA / "interim/extraction_manifest.csv",
        ("source_id", "relevance_tier", "path", "sha256"),
        (
            {
                "source_id": path.name.removesuffix(".extraction.json"),
                "relevance_tier": path.parent.name,
                "path": rel(path),
                "sha256": sha256_file(path),
            }
            for tier in "ABC"
            for path in sorted((DATA / f"interim/extraction/{tier}").glob("*.extraction.json"))
        ),
    )
    return output


def migrate_evidence_and_queue() -> None:
    candidate_csv = DATA / "interim/candidate_extracts/candidates/candidate_experiment_span.csv"
    target = DATA / "interim/evidence/evidence_candidates.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".part")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for row in read_csv(candidate_csv):
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporary.replace(target)

    control_db = DATA / "interim/review_queue/extraction_control/extraction.sqlite3"
    pending: list[dict[str, Any]] = []
    resolved: list[dict[str, Any]] = []
    if control_db.exists():
        with sqlite3.connect(control_db) as connection:
            connection.row_factory = sqlite3.Row
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "extraction_tasks" in tables:
                for row in connection.execute("SELECT * FROM extraction_tasks ORDER BY source_id,task_id"):
                    item = dict(row)
                    if item.get("task_status") in {"pending", "running", "interrupted"}:
                        pending.append(item)
                    else:
                        resolved.append(item)
    for name, rows in (("pending.jsonl", pending), ("resolved.jsonl", resolved)):
        path = DATA / "interim/review_queue" / name
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def migrate_benchmark_and_audit() -> None:
    samples = DATA / "benchmark/samples"
    fixtures = DATA / "benchmark/fixtures"
    if samples.exists():
        for source in samples.rglob("*"):
            if source.is_file():
                relative = source.relative_to(samples)
                if relative.parts and relative.parts[0] == "templates":
                    target = DATA / "benchmark/templates" / Path(*relative.parts[1:])
                else:
                    target = fixtures / relative
                copy_verified(source, target)
    misplaced_templates = fixtures / "templates"
    if misplaced_templates.exists():
        for source in misplaced_templates.rglob("*"):
            if source.is_file():
                copy_verified(
                    source,
                    DATA / "benchmark/templates" / source.relative_to(misplaced_templates),
                )
    review = DATA / "review"
    if review.exists():
        for source in review.rglob("*"):
            if source.is_file():
                copy_verified(source, DATA / "audit/samples" / source.relative_to(review))
    demo = fixtures / "company_demo_anonymized.json"
    write_json(
        demo,
        {
            "source_id": "COMP_DEMO_001",
            "company_id": "ANONYMIZED_COMPANY",
            "confidential": False,
            "relevance_tier": "company_demo",
            "tables": {table: [] for table in TABLES},
            "notes": "Synthetic fixture only; contains no company source values.",
        },
    )


def migrate_company() -> int:
    source_root = DATA / "company"
    if not source_root.exists():
        return 0
    count = 0
    for source in source_root.rglob("*"):
        if source.is_file():
            copy_verified(source, private_company_target(source.relative_to(source_root)))
            count += 1

    formal_root = PRIVATE_COMPANY / "eight_tables"
    masters = read_csv(formal_root / "source_master.csv")
    if masters:
        master_columns = list(masters[0])
        for row in masters:
            local_path = row.get("local_file_path", "").replace("\\", "/")
            if local_path.startswith("data/company/"):
                row["local_file_path"] = local_path.removeprefix("data/company/")
        write_csv(formal_root / "source_master.csv", master_columns, masters)

        all_rows = {table: read_csv(formal_root / f"{table}.csv") for table in TABLES}
        for master in masters:
            source_id = master.get("source_id", "")
            if not source_id:
                continue
            run_ids = {
                row.get("run_id", "")
                for row in all_rows["source_run"]
                if row.get("source_id") == source_id
            }
            tables: dict[str, list[dict[str, str]]] = {}
            for table, rows in all_rows.items():
                if table == "source_master":
                    selected = [row for row in rows if row.get("source_id") == source_id]
                elif table == "source_run" or any("source_id" in row for row in rows):
                    selected = [row for row in rows if row.get("source_id") == source_id]
                elif any("run_id" in row for row in rows):
                    selected = [row for row in rows if row.get("run_id") in run_ids]
                else:
                    selected = rows if len(masters) == 1 else []
                tables[table] = selected
            write_json(
                PRIVATE_COMPANY / f"{source_id}.extraction.json",
                {
                    "source_id": source_id,
                    "relevance_tier": "company_data",
                    "confidential": True,
                    "tables": tables,
                    "generated_at": utc_now(),
                },
            )
    return count


def write_source_manifest() -> None:
    root = DATA / "raw"
    manifest = root / "source_manifest.csv"
    legacy_prefixes = (
        DATA / "raw/literature/fulltext",
        DATA / "raw/literature/metadata/api_responses",
        DATA / "raw/literature/metadata/run_reports",
    )
    files = []
    for path in root.rglob("*"):
        if not path.is_file() or path == manifest:
            continue
        if any(prefix == path or prefix in path.parents for prefix in legacy_prefixes):
            continue
        if (
            path.parent == DATA / "raw/literature/pdf"
            and re.fullmatch(r"LIT_[0-9A-F]{16}_.+\.pdf", path.name)
        ):
            continue
        if DATA / "raw/literature/pdf/local_papers" in path.parents:
            continue
        files.append(path)
    rows = []
    for path in sorted(files):
        rows.append(
            {
                "path": rel(path),
                "source_id": source_id_from_name(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "media_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            }
        )
    write_csv(manifest, ("path", "source_id", "size_bytes", "sha256", "media_type"), rows)


def update_manifest_status() -> None:
    rows = read_csv(MANIFEST)
    for row in rows:
        action = row["action"]
        if action == "retain":
            row["status"] = "retained"
        elif action == "externalize_private":
            target = Path(row["new_path"])
            row["status"] = "copied_verified" if target.exists() else "group_converted"
        else:
            row["status"] = "group_converted"
    write_csv(MANIFEST, ("old_path", "new_path", "size_bytes", "sha256", "action", "status"), rows)


def migrate() -> dict[str, Any]:
    if not MANIFEST.exists() or not BASELINE.exists():
        raise RuntimeError("run inventory before migrate")
    ensure_structure()
    migrate_raw()
    parsed_count = migrate_parsed_text()
    normalize_formal_source_paths()
    rebuild_process_comparison()
    extraction = migrate_extractions()
    migrate_evidence_and_queue()
    migrate_benchmark_and_audit()
    company_count = migrate_company()
    write_source_manifest()
    update_manifest_status()
    result = {
        "migrated_at": utc_now(),
        "parsed_sources": parsed_count,
        "extraction": extraction,
        "private_company_files": company_count,
        "legacy_files_deleted": 0,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def extraction_counts() -> tuple[dict[str, dict[str, int]], set[str]]:
    counts: dict[str, dict[str, int]] = {}
    source_ids: set[str] = set()
    for tier in "ABC":
        tier_counts = {table: 0 for table in TABLES}
        for path in sorted((DATA / f"interim/extraction/{tier}").glob("*.extraction.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            source_id = payload.get("source_id", "")
            if not source_id or source_id in source_ids or payload.get("relevance_tier") != tier:
                raise ValueError(f"invalid or duplicate extraction package: {path}")
            source_ids.add(source_id)
            for table in TABLES:
                tier_counts[table] += len(payload.get("tables", {}).get(table, []))
        counts[tier] = tier_counts
    return counts, source_ids


def verify_private_company(company_rows: list[dict[str, str]]) -> dict[str, Any]:
    """Verify the canonical private tree, not byte-identical derived outputs."""

    errors: list[str] = []
    root = PRIVATE_COMPANY.resolve()
    public_root = ROOT.resolve()
    if root == public_root or public_root in root.parents:
        errors.append("private_root_inside_public_repository")

    for directory in ("raw", "eight_tables", "scripts"):
        if not (root / directory).is_dir():
            errors.append(f"missing_directory:{directory}")
    for legacy in ("interim", "processed", "catalog", "internal_lab", "review"):
        if (root / legacy).exists():
            errors.append(f"legacy_directory_present:{legacy}")

    preserved_rows = [
        row
        for row in company_rows
        if "/raw/" in row["old_path"].replace("\\", "/")
        or row["old_path"].lower().endswith(".xlsx")
    ]
    preserved_errors: list[str] = []
    for row in preserved_rows:
        old_relative = Path(row["old_path"].replace("\\", "/")).relative_to("data/company")
        target = private_company_target(old_relative)
        if (
            not target.is_file()
            or target.stat().st_size != int(row["size_bytes"])
            or sha256_file(target) != row["sha256"]
        ):
            preserved_errors.append(row["old_path"])
    if preserved_errors:
        errors.append("preserved_private_sources_invalid")

    formal_root = root / "eight_tables"
    csv_names = {path.stem for path in formal_root.glob("*.csv")}
    if csv_names != set(TABLES):
        errors.append("formal_eight_table_set_invalid")
    formal_rows = {table: read_csv(formal_root / f"{table}.csv") for table in TABLES}
    formal_counts = {table: len(rows) for table, rows in formal_rows.items()}
    if not formal_rows["source_master"] or not formal_rows["source_run"]:
        errors.append("formal_company_tables_empty")

    extraction_files = sorted(root.glob("*.extraction.json"))
    extraction_counts = {table: 0 for table in TABLES}
    extraction_source_ids: set[str] = set()
    for path in extraction_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            errors.append(f"invalid_extraction_json:{path.name}")
            continue
        if payload.get("relevance_tier") != "company_data" or payload.get("confidential") is not True:
            errors.append(f"invalid_extraction_attributes:{path.name}")
        source_id = payload.get("source_id", "")
        if not source_id or source_id in extraction_source_ids:
            errors.append(f"invalid_extraction_source:{path.name}")
        extraction_source_ids.add(source_id)
        tables = payload.get("tables", {})
        if set(tables) != set(TABLES):
            errors.append(f"invalid_extraction_table_set:{path.name}")
            continue
        for table in TABLES:
            extraction_counts[table] += len(tables[table])
    formal_source_ids = {
        row.get("source_id", "") for row in formal_rows["source_master"] if row.get("source_id")
    }
    if not extraction_files:
        errors.append("company_extraction_missing")
    if extraction_source_ids != formal_source_ids:
        errors.append("company_extraction_source_set_mismatch")
    if extraction_counts != formal_counts:
        errors.append("company_extraction_row_counts_mismatch")

    for name in ("company_master.csv", "company_source_catalog.csv"):
        if not read_csv(root / name):
            errors.append(f"missing_or_empty_catalog:{name}")

    return {
        "expected_inventory_files": len(company_rows),
        "preserved_source_files": len(preserved_rows),
        "preserved_source_errors": preserved_errors,
        "formal_row_counts": formal_counts,
        "extraction_files": len(extraction_files),
        "extraction_row_counts": extraction_counts,
        "errors": errors,
    }


def verify() -> dict[str, Any]:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    checks: dict[str, Any] = {}
    failures: list[str] = []

    target_pdfs = [
        path
        for path in (DATA / "raw/literature/pdf").glob("*.pdf")
        if re.fullmatch(r"LIT_[0-9A-F]{16}\.pdf", path.name)
        or re.match(r"P\d{3}_.+\.pdf$", path.name)
    ] + list((DATA / "raw/literature/supplements").rglob("*.pdf"))
    checks["raw_pdf_count"] = {"before": baseline["raw_pdf_count"], "after": len(target_pdfs)}
    if len(target_pdfs) < baseline["raw_pdf_count"]:
        failures.append("raw_pdf_count_decreased")

    current_formal = formal_baseline()
    expected_formal = baseline["formal_eight_tables"]
    checks["formal_eight_tables"] = current_formal
    if current_formal != expected_formal:
        failures.append("formal_eight_tables_changed")

    counts, source_ids = extraction_counts()
    if all(root.is_dir() for root in AGGREGATES.values()):
        expected_counts = {
            tier: {table: len(read_csv(root / f"{table}.csv")) for table in TABLES}
            for tier, root in AGGREGATES.items()
        }
    elif VERIFY_REPORT.is_file():
        previous = json.loads(VERIFY_REPORT.read_text(encoding="utf-8"))
        expected_counts = previous.get("checks", {}).get("extraction_row_counts", {})
    else:
        expected_counts = {}
    checks["extraction_row_counts"] = counts
    checks["extraction_source_count"] = len(source_ids)
    if counts != expected_counts:
        failures.append("extraction_row_counts_changed")

    parsed_files = list((DATA / "interim/parsed_text/by_source").glob("*.parsed.json"))
    checks["parsed_source_count"] = {
        "before": baseline["parsed_source_count"],
        "after": len(parsed_files),
    }
    if len(parsed_files) != baseline["parsed_source_count"]:
        failures.append("parsed_source_count_changed")

    company_rows = [row for row in read_csv(MANIFEST) if row["action"] == "externalize_private"]
    company_check = verify_private_company(company_rows)
    checks["private_company"] = company_check
    if company_check["errors"]:
        failures.append("private_company_layout_invalid")

    manifest_rows = read_csv(DATA / "raw/source_manifest.csv")
    checks["raw_source_manifest_rows"] = len(manifest_rows)
    if not manifest_rows:
        failures.append("raw_source_manifest_empty")

    report = {
        "verified_at": utc_now(),
        "valid": not failures,
        "failures": failures,
        "checks": checks,
    }
    write_json(VERIFY_REPORT, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def pre_migration_source_master_bytes() -> bytes:
    """Recreate the inventoried formal source master before path normalization."""

    master_path = DATA / "processed/eight_tables/source_master.csv"
    rows = read_csv(master_path)
    if not rows:
        raise RuntimeError("formal source_master.csv is empty")
    columns = list(rows[0])
    run_sources = {
        row["source_id"]
        for row in read_csv(DATA / "processed/eight_tables/source_run.csv")
        if row.get("source_id")
    }
    fixture_rows = read_csv(
        DATA / "benchmark/fixtures/six_papers/P001_Dubey_2012_FeMo_MgO_tMWCNT/source_master.csv"
    )
    fixture_path = fixture_rows[0]["local_file_path"] if fixture_rows else ""
    for row in rows:
        source_id = row["source_id"]
        if source_id not in run_sources:
            row["local_file_path"] = "registered_locally; see catalog/source_catalog.csv"
        elif source_id == "P001_Dubey_2012_FeMo_MgO_tMWCNT":
            row["local_file_path"] = fixture_path
        else:
            row["local_file_path"] = f"data/interim/parsed_text/sections/{source_id}/full_text.txt"
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode("utf-8-sig")


def archive() -> dict[str, Any]:
    if not MANIFEST.exists():
        raise RuntimeError("run inventory before archive")
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = ARCHIVE_DIR / f"{ARCHIVE_STEM}.zip"
    external_manifest = ARCHIVE_DIR / f"{ARCHIVE_STEM}_manifest.csv"
    checksum_path = ARCHIVE_DIR / f"{ARCHIVE_STEM}.sha256"
    rows = read_csv(MANIFEST)
    archived_rows: list[dict[str, Any]] = []
    temporary = archive_path.with_suffix(".zip.part")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as bundle:
        for index, row in enumerate(rows, start=1):
            source = ROOT / row["old_path"]
            if not source.is_file():
                raise FileNotFoundError(f"inventory source disappeared before archive: {source}")
            current_hash = sha256_file(source)
            expected_hash = row["sha256"]
            archive_status = "verified_pre_migration_bytes"
            archive_size = source.stat().st_size
            archive_hash = current_hash
            if current_hash == expected_hash:
                bundle.write(source, arcname=row["old_path"])
            elif row["old_path"] == "data/processed/eight_tables/source_master.csv":
                payload = pre_migration_source_master_bytes()
                archive_size = len(payload)
                archive_hash = hashlib.sha256(payload).hexdigest()
                if archive_size != int(row["size_bytes"]) or archive_hash != expected_hash:
                    raise RuntimeError("could not reconstruct the inventoried formal source_master.csv")
                bundle.writestr(row["old_path"], payload)
                archive_status = "reconstructed_pre_migration_bytes"
            elif row["old_path"] in {
                "data/README.md",
                "data/raw/README.md",
                "data/interim/README.md",
                "data/processed/README.md",
                "data/benchmark/README.md",
            }:
                bundle.write(source, arcname=row["old_path"])
                archive_status = "post_inventory_documentation"
            else:
                raise RuntimeError(f"inventory source changed before archive: {source}")
            archived_rows.append(
                {
                    **row,
                    "archive_size_bytes": archive_size,
                    "archive_sha256": archive_hash,
                    "archive_status": archive_status,
                }
            )
            if index % 1000 == 0:
                print(f"archive_files={index}", flush=True)
    temporary.replace(archive_path)
    write_csv(
        external_manifest,
        (
            "old_path",
            "new_path",
            "size_bytes",
            "sha256",
            "action",
            "status",
            "archive_size_bytes",
            "archive_sha256",
            "archive_status",
        ),
        archived_rows,
    )
    checksum = sha256_file(archive_path)
    checksum_path.write_text(f"{checksum}  {archive_path.name}\n", encoding="ascii")
    result = {
        "archive": str(archive_path.resolve()),
        "manifest": str(external_manifest.resolve()),
        "checksum_file": str(checksum_path.resolve()),
        "sha256": checksum,
        "size_bytes": archive_path.stat().st_size,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def archive_valid() -> bool:
    archive_path = ARCHIVE_DIR / f"{ARCHIVE_STEM}.zip"
    checksum_path = ARCHIVE_DIR / f"{ARCHIVE_STEM}.sha256"
    if not archive_path.is_file() or not checksum_path.is_file():
        return False
    expected = checksum_path.read_text(encoding="ascii").split()[0]
    return sha256_file(archive_path) == expected


def remove_tree_checked(path: Path) -> int:
    resolved = path.resolve()
    allowed = (DATA.resolve(), (ROOT / "reports/pipeline_runs").resolve())
    if not any(resolved == base or base in resolved.parents for base in allowed):
        raise RuntimeError(f"refusing cleanup outside allowed roots: {resolved}")
    if not path.exists():
        return 0
    count = len(list(path.rglob("*"))) if path.is_dir() else 1
    if path.is_dir():
        def remove_readonly(function: Any, target: str, _error: Any) -> None:
            os.chmod(target, stat.S_IWRITE)
            function(target)

        shutil.rmtree(path, onexc=remove_readonly)
    else:
        os.chmod(path, stat.S_IWRITE)
        path.unlink()
    return count


def cleanup_private_company() -> dict[str, Any]:
    """Remove only verified legacy copies from the external private company root."""

    company_rows = [row for row in read_csv(MANIFEST) if row["action"] == "externalize_private"]
    check = verify_private_company(company_rows)
    blocking_errors = [
        error for error in check["errors"] if not error.startswith("legacy_directory_present:")
    ]
    if blocking_errors:
        raise RuntimeError(f"private cleanup refused: {blocking_errors}")
    if not archive_valid():
        raise RuntimeError("private cleanup refused: external archive or SHA-256 is invalid")

    root = PRIVATE_COMPANY.resolve()
    allowed_names = {"interim", "processed", "catalog", "internal_lab", "review"}
    removed = 0
    for name in sorted(allowed_names):
        target = (root / name).resolve()
        if target.parent != root or target.name not in allowed_names:
            raise RuntimeError(f"refusing private cleanup target: {target}")
        if not target.exists():
            continue
        removed += len(list(target.rglob("*"))) + 1

        def remove_readonly(function: Any, item: str, _error: Any) -> None:
            os.chmod(item, stat.S_IWRITE)
            function(item)

        shutil.rmtree(target, onexc=remove_readonly)

    result = {
        "cleaned_at": utc_now(),
        "private_root": str(root),
        "removed_entries": removed,
        "removed_legacy_roots": sorted(allowed_names),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def cleanup() -> dict[str, Any]:
    report = verify()
    if not report["valid"]:
        raise RuntimeError("cleanup refused: migration verification failed")
    if not archive_valid():
        raise RuntimeError("cleanup refused: external archive or SHA-256 is invalid")
    removed = 0
    for legacy in LEGACY_ROOTS:
        removed += remove_tree_checked(legacy)
    for row in read_csv(MANIFEST):
        if row["action"] != "copy_canonical_pdf" or row["old_path"] == row["new_path"]:
            continue
        old_pdf = ROOT / row["old_path"]
        if old_pdf.is_file():
            removed += remove_tree_checked(old_pdf)
    local_papers = DATA / "raw/literature/pdf/local_papers"
    if local_papers.exists() and not any(local_papers.iterdir()):
        local_papers.rmdir()
    patents = DATA / "raw/patents"
    if patents.exists() and not any(path.is_file() and path.suffix.lower() != ".md" for path in patents.rglob("*")):
        removed += remove_tree_checked(patents)
    rows = read_csv(MANIFEST)
    for row in rows:
        row["status"] = (
            "retained" if (ROOT / row["old_path"]).is_file() else "archived_and_removed"
        )
    write_csv(MANIFEST, ("old_path", "new_path", "size_bytes", "sha256", "action", "status"), rows)
    write_source_manifest()
    result = {"cleaned_at": utc_now(), "removed_entries": removed, "archive": str(ARCHIVE_DIR)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "inventory",
            "migrate",
            "verify",
            "archive",
            "cleanup",
            "cleanup-private-company",
            "all",
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "inventory":
        inventory()
    elif args.command == "migrate":
        migrate()
    elif args.command == "verify":
        return 0 if verify()["valid"] else 1
    elif args.command == "archive":
        archive()
    elif args.command == "cleanup":
        cleanup()
    elif args.command == "cleanup-private-company":
        cleanup_private_company()
    else:
        inventory()
        migrate()
        if not verify()["valid"]:
            return 1
        archive()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
