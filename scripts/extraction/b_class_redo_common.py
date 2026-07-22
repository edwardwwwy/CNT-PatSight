"""Safe helpers for the source-first B-class re-extraction.

Unlike ``batch_common``, this module supplies no scientific defaults.  In
particular it never assumes atmospheric pressure, laboratory scale, a fresh
catalyst, or a successful CNT product.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REDO_ID = "B_CLASS_REDO_20260720"
REDO_ROOT = (
    ROOT / "runs/extraction/B/redo" / REDO_ID
)
META_DB = (
    ROOT
    / "data/raw/literature/metadata/snapshots/screening_rules_v1.2/literature.sqlite3"
)
FULLTEXT_DB = ROOT / "data/raw/literature/metadata/fulltext_registry/fulltext.sqlite3"
CANDIDATE_DB = (
    ROOT
    / "cache/databases/extraction_candidates.sqlite3"
)
SCHEMA_PATH = ROOT / "config/schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
TABLES = tuple(SCHEMA["tables"])

MANIFEST_COLUMNS = [
    "source_id",
    "title",
    "publication_year",
    "doi",
    "source_format",
    "local_source_path",
    "content_hash",
    "parse_status",
    "section_count",
    "span_count",
    "shard",
    "redo_status",
    "package_path",
    "reviewer",
    "reviewed_at",
    "blocking_reason",
]


@dataclass(frozen=True)
class SourceContext:
    source_id: str
    metadata: dict[str, Any]
    fulltext: dict[str, Any]
    parse: dict[str, Any]
    local_source_path: str

    @property
    def shard(self) -> int:
        digest = hashlib.sha256(self.source_id.encode("utf-8")).hexdigest()
        return int(digest, 16) % 4


def schema_row(table: str, **values: Any) -> dict[str, str]:
    """Return a schema-complete row without adding scientific facts."""
    if table not in SCHEMA["tables"]:
        raise KeyError(f"Unknown table: {table}")
    output = {name: "" for name in SCHEMA["tables"][table]["columns"]}
    unknown = sorted(set(values) - set(output))
    if unknown:
        raise KeyError(f"Unknown {table} field(s): {', '.join(unknown)}")
    for name, value in values.items():
        output[name] = "" if value is None else str(value)
    return output


def _resolve_local_path(stored_path: str, source_id: str) -> str:
    candidates: list[Path] = []
    if stored_path:
        stored = Path(stored_path)
        candidates.append(stored if stored.is_absolute() else ROOT / stored)
        normalized = stored_path.replace("\\", "/")
        migrations = {
            "data/raw/fulltext/pdf/": "data/raw/literature/pdf/",
            "data/raw/fulltext/html/": "data/raw/literature/html/",
            "data/raw/papers/": "data/raw/literature/pdf/",
        }
        for old, new in migrations.items():
            if normalized.startswith(old):
                candidates.append(ROOT / (new + normalized.removeprefix(old)))
        basename = Path(normalized).name
        if basename:
            candidates.extend(
                (ROOT / "data/raw/literature").glob(f"**/{basename}")
            )
    candidates.extend(
        (ROOT / "data/raw/literature/pdf").glob(f"**/{source_id}*.pdf")
    )
    candidates.extend(
        (ROOT / "data/raw/literature/html").glob(f"**/{source_id}*.html")
    )
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved.relative_to(ROOT).as_posix()
    return ""


def load_available_sources() -> list[SourceContext]:
    """Load the frozen B-tier sources with successful local parsing."""
    with sqlite3.connect(META_DB) as connection:
        connection.row_factory = sqlite3.Row
        metadata = {
            row["source_id"]: dict(row)
            for row in connection.execute(
                "SELECT * FROM works WHERE priority_tier='B' ORDER BY source_id"
            )
        }
    with sqlite3.connect(FULLTEXT_DB) as connection:
        connection.row_factory = sqlite3.Row
        fulltext = {
            row["source_id"]: dict(row)
            for row in connection.execute(
                """
                SELECT * FROM fulltext_source
                WHERE is_primary=1 AND fetch_status='success'
                  AND content_scope='fulltext'
                ORDER BY source_id
                """
            )
        }
    with sqlite3.connect(CANDIDATE_DB) as connection:
        connection.row_factory = sqlite3.Row
        parsed = {
            row["source_id"]: dict(row)
            for row in connection.execute(
                "SELECT * FROM parse_source_status WHERE parse_status='success'"
            )
        }

    output: list[SourceContext] = []
    for source_id, meta in metadata.items():
        parse = parsed.get(source_id)
        artifact = fulltext.get(source_id)
        if parse is None or artifact is None:
            continue
        local_path = _resolve_local_path(artifact.get("local_path", ""), source_id)
        if not local_path:
            raise FileNotFoundError(
                f"Parsed source has no resolvable local artifact: {source_id}"
            )
        output.append(
            SourceContext(
                source_id=source_id,
                metadata=meta,
                fulltext=artifact,
                parse=parse,
                local_source_path=local_path,
            )
        )
    return output


def load_span(source_id: str, span_id: str) -> dict[str, Any]:
    with sqlite3.connect(CANDIDATE_DB) as connection:
        connection.row_factory = sqlite3.Row
        item = connection.execute(
            """
            SELECT s.*, p.section_name_raw, p.section_name_normalized,
                   p.page_start AS section_page_start,
                   p.page_end AS section_page_end
            FROM candidate_experiment_span AS s
            LEFT JOIN paper_text_section AS p ON p.section_id=s.section_id
            WHERE s.source_id=? AND s.span_id=?
            """,
            (source_id, span_id),
        ).fetchone()
    if item is None:
        raise KeyError(f"Unknown evidence span: {source_id}/{span_id}")
    return dict(item)


def source_master_row(context: SourceContext, scope: str) -> dict[str, str]:
    meta = context.metadata
    return schema_row(
        "source_master",
        source_id=context.source_id,
        source_type="paper",
        source_title=meta.get("title", ""),
        publication_year=meta.get("year", ""),
        authors_or_assignee=meta.get("authors", ""),
        publication_venue=meta.get("journal", ""),
        doi_or_patent_no=meta.get("doi") or "not_reported",
        source_link=meta.get("source_link") or "not_reported",
        source_database="local_metadata_snapshot",
        source_language=meta.get("language") or "en",
        local_file_path=context.local_source_path,
        pdf_status=(
            "local_fulltext_available"
            if context.fulltext.get("fulltext_type") in {"pdf", "local_pdf"}
            else "local_html_fulltext_available"
        ),
        screening_class="candidate_extract",
        source_section_scope=scope,
        extraction_status="needs_review",
        review_status="pending_review",
        notes=(
            f"Source-first B-class redo {REDO_ID}; source content hash "
            f"{context.parse.get('input_content_hash', '')}; old B facts not used."
        ),
    )


def source_run_row(
    source_id: str,
    code: str,
    label: str,
    summary: str,
    *,
    data_type: str = "experimental_run",
    target_track: str = "CNT_production",
    confidence: str = "high",
) -> dict[str, str]:
    run_id = f"{source_id}_{code}"
    return schema_row(
        "source_run",
        run_id=run_id,
        source_id=source_id,
        run_label=label,
        data_type=data_type,
        target_track=target_track,
        relevance_class="candidate_extract",
        extraction_status="needs_review",
        extraction_confidence=confidence,
        run_summary=summary,
        notes="Source-first redo; independent supervisory review pending.",
    )


def catalyst_row(run_id: str, **values: Any) -> dict[str, str]:
    return schema_row(
        "catalyst_system",
        run_id=run_id,
        catalyst_id=f"{run_id}_CAT",
        **values,
    )


def process_row(
    run_id: str, stage_order: int, stage_type: str, **values: Any
) -> dict[str, str]:
    return schema_row(
        "reactor_process_gas",
        run_id=run_id,
        process_stage_id=f"{run_id}_S{stage_order:02d}",
        stage_order=stage_order,
        stage_type=stage_type,
        **values,
    )


def yield_row(run_id: str, **values: Any) -> dict[str, str]:
    return schema_row(
        "yield_quality",
        run_id=run_id,
        product_id=f"{run_id}_PROD",
        **values,
    )


def cost_row(run_id: str, **values: Any) -> dict[str, str]:
    return schema_row("cost_scale_review", run_id=run_id, **values)


def evidence_row(
    source_id: str,
    evidence_id: str,
    run_id: str,
    target_table: str,
    target_record_id: str,
    target_fields: str,
    span_id: str,
    summary: str,
    *,
    value_status: str = "reported",
    confidence: str = "high",
    linked_issue_id: str = "not_applicable",
) -> dict[str, str]:
    span = load_span(source_id, span_id)
    page_range = str(span.get("page_range") or "").strip()
    if not page_range:
        start = span.get("section_page_start")
        end = span.get("section_page_end")
        if start is not None:
            page_range = f"p{start}" if end in {None, start} else f"p{start}-p{end}"
    locator = page_range or f"section:{span['section_id']}"
    return schema_row(
        "evidence_index",
        evidence_id=evidence_id,
        source_id=source_id,
        run_id=run_id,
        target_table=target_table,
        target_record_id=target_record_id,
        target_fields=target_fields,
        evidence_type="record_support",
        value_status=value_status,
        source_section=(
            span.get("section_name_raw")
            or span.get("section_name_normalized")
            or "parsed_text"
        ),
        source_locator=locator,
        source_object_ref=span_id,
        evidence_text=" ".join(str(span["text"]).split()),
        evidence_summary=summary,
        confidence=confidence,
        linked_issue_id=linked_issue_id,
        notes="Evidence hydrated from immutable parsed span; PDF figure/table checked separately when applicable.",
    )


def issue_row(
    issue_id: str,
    source_id: str,
    run_id: str,
    issue_type: str,
    target_table: str,
    target_record_id: str,
    target_field: str,
    summary: str,
    *,
    evidence_ids: str,
    severity: str = "medium",
    conflicting_values: str = "",
) -> dict[str, str]:
    return schema_row(
        "review_issue_log",
        issue_id=issue_id,
        source_id=source_id,
        run_id=run_id,
        issue_type=issue_type,
        target_table=target_table,
        target_record_id=target_record_id,
        target_field=target_field,
        issue_summary=summary,
        conflicting_values=conflicting_values,
        evidence_ids=evidence_ids,
        severity=severity,
        review_status="pending_review",
        notes="Resolve during supervisory evidence review before formalization.",
    )


def write_package(
    package_dir: Path, tables: dict[str, list[dict[str, str]]]
) -> None:
    unknown = sorted(set(tables) - set(TABLES))
    if unknown:
        raise KeyError(f"Unknown table(s): {', '.join(unknown)}")
    package_dir.mkdir(parents=True, exist_ok=True)
    for table in TABLES:
        rows = tables.get(table, [])
        path = package_dir / SCHEMA["tables"][table]["filename"]
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=SCHEMA["tables"][table]["columns"],
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)


def write_shard_manifest(shard: int, *, replace: bool = False) -> Path:
    if shard not in range(4):
        raise ValueError("shard must be 0, 1, 2, or 3")
    shard_root = REDO_ROOT / "shards" / f"{shard:02d}"
    shard_root.mkdir(parents=True, exist_ok=True)
    path = shard_root / "shard_manifest.csv"
    if path.exists() and not replace:
        raise FileExistsError(f"Manifest exists: {path}")
    contexts = [item for item in load_available_sources() if item.shard == shard]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=MANIFEST_COLUMNS, lineterminator="\n"
        )
        writer.writeheader()
        for item in contexts:
            writer.writerow(
                {
                    "source_id": item.source_id,
                    "title": item.metadata.get("title", ""),
                    "publication_year": item.metadata.get("year", ""),
                    "doi": item.metadata.get("doi", ""),
                    "source_format": item.fulltext.get("fulltext_type", ""),
                    "local_source_path": item.local_source_path,
                    "content_hash": item.parse.get("input_content_hash", ""),
                    "parse_status": item.parse.get("parse_status", ""),
                    "section_count": item.parse.get("section_count", ""),
                    "span_count": item.parse.get("span_count", ""),
                    "shard": f"{shard:02d}",
                    "redo_status": "pending",
                    "package_path": "",
                    "reviewer": "",
                    "reviewed_at": "",
                    "blocking_reason": "",
                }
            )
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init-shard", type=int, choices=range(4))
    parser.add_argument("--replace-manifest", action="store_true")
    parser.add_argument("--inventory", action="store_true")
    args = parser.parse_args()
    contexts = load_available_sources()
    if len(contexts) != 139:
        raise RuntimeError(
            f"Frozen available-source count changed: expected 139, found {len(contexts)}"
        )
    if args.inventory:
        counts = {str(shard): sum(item.shard == shard for item in contexts) for shard in range(4)}
        print(json.dumps({"available_sources": len(contexts), "shards": counts}, indent=2))
    if args.init_shard is not None:
        print(write_shard_manifest(args.init_shard, replace=args.replace_manifest))
    if not args.inventory and args.init_shard is None:
        parser.error("choose --inventory or --init-shard")


if __name__ == "__main__":
    main()
