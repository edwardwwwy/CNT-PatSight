from __future__ import annotations

import csv
import hashlib
import json
import re
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.validation.validate_tables import validate as validate_eight_tables


COLLECTION_TO_TABLE = {
    "run_candidates": "source_run",
    "catalyst_candidates": "catalyst_system",
    "process_stage_candidates": "reactor_process_gas",
    "product_candidates": "yield_quality",
    "cost_scale_candidates": "cost_scale_review",
}

STRUCTURAL_FIELDS = {
    "source_master": {"source_id"},
    "source_run": {"run_id", "source_id"},
    "catalyst_system": {"run_id", "catalyst_id"},
    "reactor_process_gas": {"run_id", "process_stage_id"},
    "yield_quality": {"run_id", "product_id"},
    "cost_scale_review": {"run_id"},
    "evidence_index": {"evidence_id", "source_id", "run_id"},
    "review_issue_log": {"issue_id", "source_id", "run_id"},
}


def normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip().casefold()


def allowed_field_map(formal_schema: dict[str, Any]) -> dict[str, list[str]]:
    return {
        table: [c for c in spec["columns"] if c not in STRUCTURAL_FIELDS.get(table, set())]
        for table, spec in formal_schema["tables"].items()
        if table not in {"evidence_index", "review_issue_log", "source_master"}
    }


def package_with_contract(package: dict[str, Any], formal_schema: dict[str, Any]) -> dict[str, Any]:
    # Field names are constrained by the active JSON Schema generated from the
    # formal contract. Repeating the complete field map in every prompt consumed
    # several thousand context tokens without adding any validation strength.
    return dict(package)


def collapse_identical_candidate_duplicates(payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Collapse byte-equivalent repeated candidates without changing facts.

    The untouched model payload remains stored in the attempt directory. A
    repeated ID with different content is deliberately retained so validation
    rejects the ambiguity.
    """
    result = json.loads(json.dumps(payload, ensure_ascii=False))
    collapsed: list[dict[str, str]] = []
    collections = {
        "run_candidates": "candidate_run_id",
        "catalyst_candidates": "candidate_catalyst_id",
        "process_stage_candidates": "candidate_stage_id",
        "product_candidates": "candidate_product_id",
        "cost_scale_candidates": "candidate_cost_scale_id",
        "review_issues": "candidate_issue_id",
    }
    for collection, id_field in collections.items():
        seen: dict[str, str] = {}
        kept: list[Any] = []
        for row in result.get(collection, []):
            row_id = str(row.get(id_field, "")) if isinstance(row, dict) else ""
            encoded = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if row_id and seen.get(row_id) == encoded:
                collapsed.append({"collection": collection, "candidate_id": row_id})
                continue
            seen.setdefault(row_id, encoded)
            kept.append(row)
        if collection in result:
            result[collection] = kept
    return result, collapsed


def validate_payload(
    payload: dict[str, Any],
    package: dict[str, Any],
    extraction_schema: dict[str, Any],
    formal_schema: dict[str, Any],
    unit_rules: dict[str, Any],
) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    for error in Draft202012Validator(extraction_schema).iter_errors(payload):
        errors.append({"code": "json_schema", "message": f"{'/'.join(map(str,error.path))}: {error.message}"})
    if payload.get("source_id") != package.get("source_id"):
        errors.append({"code": "source_id_mismatch", "message": "source_id differs from input package"})
    if payload.get("input_content_hash") != package.get("input_content_hash"):
        errors.append({"code": "content_hash_mismatch", "message": "input_content_hash differs from input package"})

    span_text = normalized_text("\n".join(str(s.get("text", "")) for s in package.get("spans", [])))
    allowed = allowed_field_map(formal_schema)
    run_ids = {r.get("candidate_run_id") for r in payload.get("run_candidates", [])}
    linked = {run_id: {"catalyst": 0, "process": 0, "product": 0} for run_id in run_ids}
    ids_seen: set[str] = set()

    collections = [
        ("run_candidates", "candidate_run_id", "source_run"),
        ("catalyst_candidates", "candidate_catalyst_id", "catalyst_system"),
        ("process_stage_candidates", "candidate_stage_id", "reactor_process_gas"),
        ("product_candidates", "candidate_product_id", "yield_quality"),
        ("cost_scale_candidates", "candidate_cost_scale_id", "cost_scale_review"),
    ]
    for collection, id_field, table in collections:
        for row in payload.get(collection, []):
            row_id = str(row.get(id_field, ""))
            if row_id in ids_seen:
                errors.append({"code": "duplicate_candidate_id", "message": row_id})
            ids_seen.add(row_id)
            run_id = row.get("candidate_run_id") if collection != "run_candidates" else row_id
            if run_id not in run_ids:
                errors.append({"code": "unknown_candidate_run", "message": f"{row_id}->{run_id}"})
            if run_id in linked:
                if table == "catalyst_system": linked[run_id]["catalyst"] += 1
                if table == "reactor_process_gas": linked[run_id]["process"] += 1
                if table == "yield_quality": linked[run_id]["product"] += 1
            fields = row.get("fields", {})
            if table in {"catalyst_system", "reactor_process_gas", "yield_quality", "cost_scale_review"} and not any(v is not None for v in fields.values()):
                errors.append({"code": "empty_fact_record", "message": f"{table}:{row_id}"})
            for field, evidence in fields.items():
                if field not in allowed.get(table, []):
                    errors.append({"code": "unknown_formal_field", "message": f"{table}.{field}"})
                    continue
                if evidence is None:
                    continue
                quote = normalized_text(str(evidence.get("evidence_text", "")))
                if not quote or quote not in span_text:
                    errors.append({"code": "evidence_not_in_input", "message": f"{table}.{field}"})
                _check_bounds(field, evidence, unit_rules, warnings)
                _check_unit(field, evidence, unit_rules, warnings)
    for run_id, counts in linked.items():
        missing = [name for name, count in counts.items() if not count]
        if missing:
            errors.append({"code": "incomplete_run_linkage", "message": f"{run_id}:{','.join(missing)}"})
    return {
        "valid": not errors,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "run_count": len(run_ids),
    }


def _number(evidence: dict[str, Any]) -> float | None:
    value = evidence.get("value_normalized")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _check_bounds(field: str, evidence: dict[str, Any], rules: dict[str, Any], warnings: list[dict[str, str]]) -> None:
    value = _number(evidence)
    if value is None:
        return
    key = None
    if "temperature" in field and field.endswith("_C"): key = "temperature_C"
    elif "pressure" in field and field.endswith("_kPa"): key = "pressure_kPa"
    elif "flow" in field and field.endswith("_sccm"): key = "flow_sccm"
    elif field in {"holding_time_min", "continuous_operation_time_h"}: key = "time_min"
    elif field.endswith("_percent") and not any(token in field.lower() for token in ("yield", "weight_gain")): key = "ordinary_percent"
    if key and key in rules.get("bounds", {}):
        low, high = rules["bounds"][key]
        comparable = value * 60 if field == "continuous_operation_time_h" else value
        if comparable < low or comparable > high:
            warnings.append({"code": "plausibility_range", "message": f"{field}={value}"})


def _check_unit(field: str, evidence: dict[str, Any], rules: dict[str, Any], warnings: list[dict[str, str]]) -> None:
    unit = evidence.get("unit")
    if unit in {None, "", "not_applicable"}:
        return
    groups = rules.get("conversions", {})
    expected = None
    if field.endswith("_C"): expected = "temperature"
    elif field.endswith("_kPa"): expected = "pressure"
    elif field.endswith("_min") or field.endswith("_h"): expected = "time"
    elif field.endswith("_g"): expected = "mass"
    elif field.endswith("_nm"): expected = "length"
    elif field.endswith("_sccm"): expected = "standard_flow"
    if expected and str(unit) not in groups.get(expected, []):
        warnings.append({"code": "unit_requires_review", "message": f"{field}:{unit}"})


def build_staging_rows(
    payload: dict[str, Any],
    metadata: dict[str, Any],
    formal_schema: dict[str, Any],
    revision_id: str,
) -> dict[str, list[dict[str, Any]]]:
    source_id = payload["source_id"]
    token = hashlib.sha256(source_id.encode("utf-8")).hexdigest()[:10].upper()
    rows: dict[str, list[dict[str, Any]]] = {name: [] for name in formal_schema["tables"]}
    rows["source_master"].append({
        "source_id": source_id,
        "source_type": metadata.get("source_type") or "paper",
        "source_title": metadata.get("title") or source_id,
        "publication_year": metadata.get("year") or "not_reported",
        "authors_or_assignee": metadata.get("authors") or metadata.get("authors_or_assignee") or "",
        "publication_venue": metadata.get("journal") or "",
        "doi_or_patent_no": metadata.get("doi") or metadata.get("doi_or_patent_no") or "",
        "source_link": metadata.get("source_link") or "",
        "source_database": metadata.get("source_database") or "metadata_snapshot_v1.2",
        "source_language": metadata.get("language") or "not_reported",
        "local_file_path": metadata.get("local_file_path") or "",
        "pdf_status": metadata.get("pdf_status") or "available",
        "screening_class": "candidate_extract",
        "source_section_scope": "parsed_candidate_spans",
        "extraction_status": "needs_review",
        "review_status": "pending_human_review",
        "notes": f"Qwen staging revision {revision_id}; domain_expert_verified=false",
    })
    run_map: dict[str, str] = {}
    target_ids: dict[tuple[str, str], tuple[str, str]] = {}
    evidence_counter = 0

    for index, candidate in enumerate(payload.get("run_candidates", []), start=1):
        candidate_id = candidate["candidate_run_id"]
        run_id = f"STG_{token}_R{index:03d}"
        run_map[candidate_id] = run_id
        row = {
            "run_id": run_id, "source_id": source_id,
            "run_label": candidate_id, "data_type": "experimental_run",
            "target_track": "CNT_CVD_candidate", "relevance_class": "candidate_extract",
            "extraction_status": "needs_review", "extraction_confidence": "needs_review",
            "notes": f"staging:{revision_id}",
        }
        _apply_fields(row, candidate.get("fields", {}))
        rows["source_run"].append(row)
        target_ids[("source_run", candidate_id)] = (run_id, run_id)

    collections = [
        ("catalyst_candidates", "catalyst_system", "candidate_catalyst_id", "catalyst_id", "CAT"),
        ("process_stage_candidates", "reactor_process_gas", "candidate_stage_id", "process_stage_id", "STAGE"),
        ("product_candidates", "yield_quality", "candidate_product_id", "product_id", "PROD"),
        ("cost_scale_candidates", "cost_scale_review", "candidate_cost_scale_id", None, "SCALE"),
    ]
    evidence_specs: list[tuple[str, str, str, str, dict[str, Any]]] = []
    for collection, table, candidate_key, identity_field, prefix in collections:
        for index, candidate in enumerate(payload.get(collection, []), start=1):
            run_id = run_map[candidate["candidate_run_id"]]
            record_id = run_id if identity_field is None else f"{prefix}_{index:03d}"
            row = {"run_id": run_id}
            if identity_field:
                row[identity_field] = record_id
            if table == "reactor_process_gas":
                row.setdefault("stage_order", str(index))
            _apply_fields(row, candidate.get("fields", {}))
            rows[table].append(row)
            target_ids[(table, candidate[candidate_key])] = (run_id, record_id)
            for field, evidence in candidate.get("fields", {}).items():
                if evidence is not None:
                    evidence_specs.append((table, run_id, record_id, field, evidence))

    for table, run_id, record_id, field, evidence in evidence_specs:
        evidence_counter += 1
        rows["evidence_index"].append({
            "evidence_id": f"EVID_{token}_{evidence_counter:04d}",
            "source_id": source_id,
            "run_id": run_id,
            "target_table": table,
            "target_record_id": record_id,
            "target_fields": field,
            "evidence_type": "record_support",
            "value_status": evidence.get("value_status") or "reported",
            "source_section": evidence.get("evidence_section") or "not_reported",
            "source_locator": f"page {evidence.get('evidence_page')}" if evidence.get("evidence_page") is not None else "not_reported",
            "source_object_ref": "",
            "evidence_text": evidence.get("evidence_text") or "",
            "evidence_summary": str(evidence.get("value_raw") or ""),
            "confidence": evidence.get("confidence") or "low",
            "linked_issue_id": "",
            "notes": f"raw={json.dumps(evidence.get('value_raw'), ensure_ascii=False)}; unit={evidence.get('unit')}",
        })

    for index, candidate in enumerate(payload.get("review_issues", []), start=1):
        fields = {k: _value(v) for k, v in candidate.get("fields", {}).items() if v is not None}
        candidate_run = candidate.get("candidate_run_id")
        run_id = run_map.get(candidate_run, "")
        target_table = str(fields.get("target_table") or "source_run")
        target_record_id = str(fields.get("target_record_id") or run_id)
        rows["review_issue_log"].append({
            "issue_id": f"ISSUE_{token}_{index:03d}", "source_id": source_id, "run_id": run_id,
            "issue_type": fields.get("issue_type") or "quality_warning",
            "target_table": target_table, "target_record_id": target_record_id,
            "target_field": fields.get("target_field") or "record_level",
            "issue_summary": fields.get("issue_summary") or "Qwen extraction requires human review",
            "conflicting_values": fields.get("conflicting_values") or "",
            "evidence_ids": "", "severity": fields.get("severity") or "medium",
            "review_status": "open", "reviewer": "", "reviewed_at": "", "resolution": "",
            "notes": "domain_expert_verified=false",
        })
    # The formal contract requires interpretive fields to be explicit. These
    # sentinels mean the source did not report the value; they are not model
    # facts and never receive fabricated evidence.
    for table, spec in formal_schema["tables"].items():
        for row in rows[table]:
            for field in spec.get("required_fields", []):
                if row.get(field) is None or row.get(field) == "":
                    row[field] = "not_reported"
    return rows


def _value(evidence: dict[str, Any]) -> Any:
    value = evidence.get("value_normalized")
    return evidence.get("value_raw") if value is None else value


def _apply_fields(row: dict[str, Any], fields: dict[str, Any]) -> None:
    for field, evidence in fields.items():
        if evidence is not None:
            row[field] = _value(evidence)


def validate_rows_with_formal_validator(
    rows_by_table: dict[str, list[dict[str, Any]]],
    formal_schema: dict[str, Any],
    schema_path: Path,
    dictionary_path: Path,
) -> None:
    with tempfile.TemporaryDirectory(prefix="cnt_patsight_staging_") as temporary:
        directory = Path(temporary)
        for table, spec in formal_schema["tables"].items():
            path = directory / spec["filename"]
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=spec["columns"], extrasaction="ignore", lineterminator="\n")
                writer.writeheader()
                for row in rows_by_table.get(table, []):
                    writer.writerow({column: _csv_cell(row.get(column, "")) for column in spec["columns"]})
        if validate_eight_tables(directory, schema_path, dictionary_path) != 0:
            raise ValueError("formal_eight_table_validator_failed")


def _csv_cell(value: Any) -> str:
    if value is None: return ""
    if isinstance(value, list): return "; ".join(map(str, value))
    if isinstance(value, dict): return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, bool): return "1" if value else "0"
    return str(value)
