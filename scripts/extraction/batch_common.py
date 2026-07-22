"""Shared schema, storage, and row helpers for curated extraction batches.

Batch files contain source-specific research facts.  Keeping infrastructure in
this module prevents those data-heavy builders from depending on batch 001.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BATCH_ID = "A_CLASS_208_20260716"
PACKAGE_ROOT = ROOT / "data/interim/extraction/A"
META_DB = ROOT / "data/raw/literature/metadata/snapshots/screening_rules_v1.2/literature.sqlite3"
FULLTEXT_DB = ROOT / "data/raw/literature/metadata/fulltext_registry/fulltext.sqlite3"
CANDIDATE_DB = ROOT / "cache/databases/extraction_candidates.sqlite3"
SCHEMA_PATH = ROOT / "config/schema.json"

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


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


SCHEMA = load_schema()


def row(table: str, **values: Any) -> dict[str, str]:
    output = {name: "" for name in SCHEMA["tables"][table]["columns"]}
    for name, value in values.items():
        if name not in output:
            raise KeyError(f"{name!r} is not a {table} field")
        output[name] = "" if value is None else str(value)
    return output


def write_table(path: Path, table: str, rows: list[dict[str, str]]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    with (path / f"{table}.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=SCHEMA["tables"][table]["columns"],
        )
        writer.writeheader()
        writer.writerows(rows)


def load_metadata(priority_tier: str = "A") -> dict[str, dict[str, Any]]:
    """Load canonical metadata for a single screened priority tier.

    Existing A-class batch builders retain the default.  Manual B-class review
    builders pass ``"B"`` explicitly so their evidence packages cannot
    accidentally draw source metadata from the A-tier queue.
    """
    with sqlite3.connect(META_DB) as connection:
        connection.row_factory = sqlite3.Row
        return {
            item["source_id"]: dict(item)
            for item in connection.execute(
                "SELECT * FROM works WHERE priority_tier = ?",
                (priority_tier,),
            )
        }


class EvidenceStore:
    def __init__(self) -> None:
        self.connection = sqlite3.connect(CANDIDATE_DB)
        self.connection.row_factory = sqlite3.Row

    def close(self) -> None:
        self.connection.close()

    def span(self, source_id: str, span_id: str) -> dict[str, Any]:
        item = self.connection.execute(
            """
            SELECT s.*, p.section_name_raw, p.section_name_normalized
            FROM candidate_experiment_span AS s
            LEFT JOIN paper_text_section AS p ON p.section_id = s.section_id
            WHERE s.source_id = ? AND s.span_id = ?
            """,
            (source_id, span_id),
        ).fetchone()
        if item is None:
            raise KeyError(f"Missing candidate span {source_id}/{span_id}")
        return dict(item)


def master_row(meta: dict[str, Any], scope: str) -> dict[str, str]:
    return row(
        "source_master",
        source_id=meta["source_id"],
        source_type="paper",
        source_title=meta["title"],
        publication_year=meta["year"],
        authors_or_assignee=meta["authors"],
        publication_venue=meta["journal"],
        doi_or_patent_no=meta["doi"] or "not_reported",
        source_link=meta["source_link"] or "not_reported",
        source_database="local_metadata_snapshot",
        source_language=meta["language"] or "en",
        local_file_path=f"data/interim/parsed_text/by_source/{meta['source_id']}.parsed.json",
        pdf_status=meta["pdf_status"] or "legal_url_found",
        screening_class="candidate_extract",
        source_section_scope=scope,
        extraction_status="needs_review",
        review_status="pending_review",
        notes=(
            f"Codex manual first pass for {BATCH_ID}; locally parsed evidence "
            "only; domain_expert_verified=false."
        ),
    )


def run_row(
    source_id: str,
    code: str,
    label: str,
    summary: str,
    confidence: str = "high",
) -> dict[str, str]:
    return row(
        "source_run",
        run_id=f"{source_id}_{code}",
        source_id=source_id,
        run_label=label,
        data_type="experimental_run",
        target_track="CNT_production",
        relevance_class="candidate_extract",
        extraction_status="needs_review",
        extraction_confidence=confidence,
        run_summary=summary,
        notes=(
            "First-pass structured transcription; "
            "independent evidence review required."
        ),
    )


def catalyst_row(run_id: str, **values: Any) -> dict[str, str]:
    defaults = {
        "run_id": run_id,
        "catalyst_id": f"{run_id}_CAT",
        "activation_condition": "not_reported",
        "post_preparation_condition": "fresh catalyst",
        "notes": "CNT dimensions are not mapped to catalyst-particle fields.",
    }
    defaults.update(values)
    return row("catalyst_system", **defaults)


def process_row(
    run_id: str,
    order: int,
    stage_type: str,
    **values: Any,
) -> dict[str, str]:
    defaults = {
        "run_id": run_id,
        "process_stage_id": f"{run_id}_S{order:02d}",
        "stage_order": order,
        "stage_type": stage_type,
        "scale_level": "lab_batch",
        "pressure_original": "atmospheric",
        "pressure_kPa": "101.325",
        "process_note": "Reported process stage; first-pass needs_review.",
    }
    defaults.update(values)
    return row("reactor_process_gas", **defaults)


def yield_row(run_id: str, **values: Any) -> dict[str, str]:
    defaults = {
        "run_id": run_id,
        "product_id": f"{run_id}_PROD",
        "CNT_type_confirmed": "not_applicable",
        "yield_standardization_note": "No cross-definition conversion performed.",
        "notes": (
            "Reported identity and basis retained; "
            "needs independent evidence review."
        ),
    }
    defaults.update(values)
    return row("yield_quality", **defaults)


def cost_row(run_id: str, **values: Any) -> dict[str, str]:
    defaults = {
        "run_id": run_id,
        "scale_level_demonstrated": "lab_batch",
        "scale_level_claimed": "not_reported",
        "scale_evidence_summary": "Laboratory reactor experiment.",
        "quantitative_cost_reported": "not_reported",
        "quantitative_cost_summary": "not_reported",
        "safety_risk": "not_reported",
        "emission_or_waste": "not_reported",
        "review_note": "No review-stage industrial-readiness assessment entered.",
    }
    defaults.update(values)
    return row("cost_scale_review", **defaults)


def evidence_row(
    store: EvidenceStore,
    source_id: str,
    evidence_id: str,
    run_id: str,
    table: str,
    record_id: str,
    fields: str,
    span_id: str,
    summary: str,
    confidence: str = "high",
    value_status: str = "reported",
) -> dict[str, str]:
    span = store.span(source_id, span_id)
    return row(
        "evidence_index",
        evidence_id=evidence_id,
        source_id=source_id,
        run_id=run_id,
        target_table=table,
        target_record_id=record_id,
        target_fields=fields,
        evidence_type="record_support",
        value_status=value_status,
        source_section=(
            span.get("section_name_raw")
            or span.get("section_name_normalized")
            or "parsed_text"
        ),
        source_locator=span.get("page_range") or "local_span",
        source_object_ref=span_id,
        evidence_text=" ".join(span["text"].split()),
        evidence_summary=summary,
        confidence=confidence,
        linked_issue_id="not_applicable",
        notes="Evidence copied from immutable local candidate span.",
    )


def issue_row(
    issue_id: str,
    source_id: str,
    run_id: str,
    issue_type: str,
    table: str,
    record_id: str,
    field: str,
    summary: str,
    evidence_ids: str,
    severity: str = "medium",
) -> dict[str, str]:
    return row(
        "review_issue_log",
        issue_id=issue_id,
        source_id=source_id,
        run_id=run_id,
        issue_type=issue_type,
        target_table=table,
        target_record_id=record_id,
        target_field=field,
        issue_summary=summary,
        evidence_ids=evidence_ids,
        severity=severity,
        review_status="pending_review",
        notes="Resolve in the independent evidence pass before formalization.",
    )
