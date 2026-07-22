"""Read, validate, and atomically write one-file extraction packages."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.extraction.batch_common import ROOT, TABLES, write_table
from scripts.validation.validate_tables import (
    DEFAULT_DICTIONARY,
    DEFAULT_SCHEMA,
    validate,
)


TableRows = Mapping[str, Sequence[Mapping[str, Any]]]


def extraction_path(source_id: str, relevance_tier: str) -> Path:
    tier = relevance_tier.upper()
    if tier not in {"A", "B", "C"}:
        raise ValueError(f"unsupported relevance tier: {relevance_tier}")
    return ROOT / "data/interim/extraction" / tier / f"{source_id}.extraction.json"


def validate_extraction_tables(tables: TableRows) -> None:
    """Run the existing eight-table validator without persisting eight CSVs."""

    missing = set(TABLES) - set(tables)
    extra = set(tables) - set(TABLES)
    if missing or extra:
        raise ValueError(f"invalid table set: missing={sorted(missing)} extra={sorted(extra)}")
    with tempfile.TemporaryDirectory(prefix="cnt_litsight_extract_validate_") as directory:
        root = Path(directory)
        for table in TABLES:
            write_table(root, table, [dict(row) for row in tables[table]])
        errors = validate(root, DEFAULT_SCHEMA, DEFAULT_DICTIONARY)
        if errors:
            raise RuntimeError(f"eight-table validation failed with {errors} error(s)")


def write_extraction_package(
    source_id: str,
    relevance_tier: str,
    tables: TableRows,
    *,
    extraction_status: str = "candidate_extract",
    replace: bool = False,
    validate_rows: bool = True,
) -> Path:
    """Write exactly one atomic JSON package for a source."""

    destination = extraction_path(source_id, relevance_tier)
    if destination.exists() and not replace:
        raise FileExistsError(f"extraction package already exists: {destination}")
    normalized = {table: [dict(row) for row in tables[table]] for table in TABLES}
    if validate_rows:
        validate_extraction_tables(normalized)
    payload = {
        "source_id": source_id,
        "relevance_tier": relevance_tier.upper(),
        "extraction_status": extraction_status,
        "tables": normalized,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)
    return destination


def read_extraction_package(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if path.name != f"{payload.get('source_id', '')}.extraction.json":
        raise ValueError(f"source_id/filename mismatch: {path}")
    if set(payload.get("tables", {})) != set(TABLES):
        raise ValueError(f"invalid table set: {path}")
    return payload


def existing_package_metric(
    source_id: str,
    relevance_tier: str,
    *,
    status: str = "needs_review",
) -> dict[str, Any] | None:
    """Return batch metrics for an existing one-file package, if present."""

    path = extraction_path(source_id, relevance_tier)
    if not path.exists():
        return None
    payload = read_extraction_package(path)
    tables = payload["tables"]
    return {
        "source_id": source_id,
        "output_path": path.relative_to(ROOT).as_posix(),
        "row_counts": {table: len(tables[table]) for table in TABLES},
        "status": payload.get("extraction_status", status),
    }
