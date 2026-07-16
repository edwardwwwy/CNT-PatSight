from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ID_FIELDS = {
    "candidate_run_id", "candidate_catalyst_id", "candidate_stage_id", "candidate_product_id",
    "candidate_cost_scale_id", "candidate_observation_id", "candidate_issue_id", "claim_id",
}
META_FIELDS = ID_FIELDS | {"candidate_run_id", "confidence", "evidence_span_ids", "candidate_issue_id", "review_status"}

RECORD_SPECS = {
    "run": ("run_candidates", "candidate_run_id"),
    "catalyst": ("catalyst_candidates", "candidate_catalyst_id"),
    "process_stage": ("process_stage_candidates", "candidate_stage_id"),
    "product": ("product_candidates", "candidate_product_id"),
    "cost_scale": ("cost_scale_candidates", "candidate_cost_scale_id"),
    "source_observation": ("source_observations", "candidate_observation_id"),
    "review_issue": ("review_issues", "candidate_issue_id"),
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _add(issues: list[dict[str, Any]], code: str, message: str, severity: str = "error", **context: Any) -> None:
    issues.append({"code": code, "message": message, "severity": severity, **context})


def _schema_errors(payload: dict[str, Any], schema_path: Path) -> list[dict[str, Any]]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return [{"code": "missing_jsonschema", "message": "Install requirements-llm.txt before validating JSON", "severity": "error"}]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    return [
        {"code": "schema_error", "message": error.message, "severity": "error", "path": list(error.absolute_path)}
        for error in sorted(validator.iter_errors(payload), key=lambda error: list(error.absolute_path))
    ]


def validate_payload(
    payload: dict[str, Any],
    package: dict[str, Any],
    schema_path: Path,
) -> dict[str, Any]:
    issues = _schema_errors(payload, schema_path)
    if payload.get("source_id") != package.get("source_id"):
        _add(issues, "source_id_mismatch", "Payload source_id does not match the candidate package")
    if payload.get("input_content_hash") != package.get("input_content_hash"):
        _add(issues, "content_hash_mismatch", "Payload input_content_hash does not match the candidate package")

    known_span_ids: set[str] = set()
    for span in package.get("spans", []):
        known_span_ids.add(span.get("span_id", ""))
        known_span_ids.update(span.get("duplicate_span_ids", []))
    records: dict[str, dict[str, dict[str, Any]]] = {}
    for record_type, (key, id_field) in RECORD_SPECS.items():
        records[record_type] = {}
        for record in payload.get(key, []) if isinstance(payload.get(key, []), list) else []:
            record_id = record.get(id_field)
            if record_id in records[record_type]:
                _add(issues, "duplicate_candidate_id", f"Duplicate {record_type} ID {record_id}", record_type=record_type, record_id=record_id)
            records[record_type][record_id] = record

    run_ids = set(records["run"])
    for record_type in ("catalyst", "process_stage", "product", "cost_scale"):
        for record in records[record_type].values():
            run_id = record.get("candidate_run_id")
            if run_id not in run_ids:
                _add(issues, "unknown_run_reference", f"{record_type} record references unknown run {run_id}", record_type=record_type, record_id=record.get("candidate_run_id"))

    claim_by_target: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for claim in payload.get("evidence_claims", []) if isinstance(payload.get("evidence_claims", []), list) else []:
        target_type = claim.get("target_type")
        target_id = claim.get("target_id")
        claim_by_target.setdefault((target_type, target_id), []).append(claim)
        if target_type not in RECORD_SPECS:
            _add(issues, "unknown_claim_target_type", f"Unknown claim target type {target_type}")
            continue
        if target_id not in records[target_type]:
            _add(issues, "unknown_claim_target", f"Claim points to unknown {target_type} record {target_id}", claim_id=claim.get("claim_id"))
        span_ids = claim.get("span_ids", [])
        if not span_ids:
            _add(issues, "claim_without_evidence", f"Claim {claim.get('claim_id')} has no span IDs", claim_id=claim.get("claim_id"))
        unknown = [span_id for span_id in span_ids if span_id not in known_span_ids]
        if unknown:
            _add(issues, "unknown_span_id", f"Claim references spans not present in the package: {unknown}", claim_id=claim.get("claim_id"))
        quote = _norm(str(claim.get("evidence_quote", "")))
        referenced = [span for span in package.get("spans", []) if any(span_id in span.get("duplicate_span_ids", []) for span_id in span_ids)]
        if quote and referenced and not any(quote in _norm(span.get("text", "")) for span in referenced):
            _add(issues, "quote_not_in_span", f"Evidence quote for {claim.get('claim_id')} is not an exact normalized substring of a referenced span", claim_id=claim.get("claim_id"))
        target_record = records[target_type].get(target_id)
        if target_record is not None:
            unknown_fields = [field for field in claim.get("target_fields", []) if field not in target_record]
            if unknown_fields:
                _add(issues, "unknown_target_field", f"Claim {claim.get('claim_id')} names fields absent from target record: {unknown_fields}", claim_id=claim.get("claim_id"))

    fact_field_count = 0
    covered_field_count = 0
    for record_type, rows in records.items():
        if record_type in {"source_observation", "review_issue"}:
            continue
        for record_id, record in rows.items():
            claims = claim_by_target.get((record_type, record_id), [])
            record_span_ids = record.get("evidence_span_ids", []) if isinstance(record, dict) else []
            unknown_record_spans = [span_id for span_id in record_span_ids if span_id not in known_span_ids]
            if unknown_record_spans:
                _add(issues, "unknown_record_span_id", f"{record_type} record {record_id} references unknown spans: {unknown_record_spans}", record_type=record_type, record_id=record_id)
            if not claims and not record_span_ids:
                _add(issues, "record_without_evidence", f"{record_type} record {record_id} has no evidence claim", record_type=record_type, record_id=record_id)
            covered = {field for claim in claims for field in claim.get("target_fields", [])}
            for field, value in record.items():
                if field in META_FIELDS or field in {"candidate_run_id", "active_metals", "characterization_methods"}:
                    if field in {"active_metals", "characterization_methods"} and value:
                        fact_field_count += 1
                        covered_field_count += int(field in covered)
                    continue
                populated = value is not None and value != "" and value != [] and value is not False
                if not populated:
                    continue
                fact_field_count += 1
                if field in covered:
                    covered_field_count += 1
                else:
                    _add(issues, "fact_without_field_evidence", f"{record_type} {record_id} field {field} has a value but no target field evidence claim", "warning" if record_span_ids else "error", record_type=record_type, record_id=record_id, field=field)

    for issue in payload.get("review_issues", []) if isinstance(payload.get("review_issues", []), list) else []:
        if issue.get("review_status") != "open":
            _add(issues, "review_issue_not_open", f"Review issue {issue.get('candidate_issue_id')} must remain open", record_id=issue.get("candidate_issue_id"))
        unknown = [span_id for span_id in issue.get("evidence_span_ids", []) if span_id not in known_span_ids]
        if unknown:
            _add(issues, "unknown_issue_span_id", f"Review issue references unknown spans: {unknown}", record_id=issue.get("candidate_issue_id"))

    errors = sum(issue.get("severity") == "error" for issue in issues)
    warnings = sum(issue.get("severity") == "warning" for issue in issues)
    return {
        "valid": errors == 0,
        "status": "schema_valid_needs_review" if errors == 0 else "invalid",
        "error_count": errors,
        "warning_count": warnings,
        "issues": issues,
        "counts": {key: len(payload.get(key, [])) for key in ("run_candidates", "catalyst_candidates", "process_stage_candidates", "product_candidates", "cost_scale_candidates", "source_observations", "evidence_claims", "review_issues")},
        "evidence_field_coverage": {
            "populated_fact_fields": fact_field_count,
            "covered_fact_fields": covered_field_count,
            "ratio": (covered_field_count / fact_field_count) if fact_field_count else 1.0,
        },
    }
