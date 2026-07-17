from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import shutil
import tempfile
import unicodedata
import uuid
from contextlib import redirect_stdout
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

EVIDENCE_CONSTRAINT_VERSION = "exact_input_excerpt_enum_v1"
EVIDENCE_REFERENCE_PLACEHOLDER = "__AUTO_FROM_EVIDENCE_SECTION__"

ALLOWED_ISSUE_TYPES = {
    "source_conflict",
    "definition_ambiguity",
    "run_split_uncertainty",
    "CNT_type_uncertainty",
    "calculation_check",
    "critical_data_gap",
    "quality_warning",
    "schema_mapping_question",
}
GENERIC_ISSUE_TEXT = {
    "",
    "needs review",
    "needs_review",
    "not reported",
    "not_reported",
    "unknown",
    "n/a",
}
PLACEHOLDER_VALUES = {
    "",
    "not reported",
    "not_reported",
    "not specified",
    "not_specified",
    "unknown",
    "n/a",
    "none",
    "null",
}
CATALYST_LABEL_PATTERN = re.compile(
    r"\b(?:Fe|Mo|Ni|Co|Cu|Mn|Cr|W|Ru|Rh|Pd|Pt|Al)"
    r"(?:[-–—−]\d+(?:\.\d+)?(?:Fe|Mo|Ni|Co|Cu|Mn|Cr|W|Ru|Rh|Pd|Pt))?"
    r"(?:/[A-Za-z][A-Za-z0-9()\-]*)?\b",
    re.IGNORECASE,
)
CORE_SIGNAL_RULES = {
    "catalyst_loading_mass_g": (
        re.compile(r"\b150\s*mg\b", re.IGNORECASE),
        "process_stage_candidates",
    ),
    "temperature_setpoint_C": (
        re.compile(r"\b850\s*(?:°\s*C|1C|C)\b", re.IGNORECASE),
        "process_stage_candidates",
    ),
    "heating_rate_C_min": (
        re.compile(r"\b10\s*(?:°\s*C|1C|C)\s*min", re.IGNORECASE),
        "process_stage_candidates",
    ),
    "holding_time_min": (
        re.compile(r"\b30\s*min", re.IGNORECASE),
        "process_stage_candidates",
    ),
    "carbon_source": (
        re.compile(r"\b(?:pure\s+)?CH\s*4\b|\bmethane\b", re.IGNORECASE),
        "process_stage_candidates",
    ),
    "carbon_source_flow_original": (
        re.compile(r"\b20\s*mL\s*min", re.IGNORECASE),
        "process_stage_candidates",
    ),
}


class FormalStagingValidationError(ValueError):
    """A deterministic eight-table mapping failure that must not be retried."""

    def __init__(self, report: str):
        super().__init__("formal_eight_table_validator_failed")
        self.report = report

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


def normalized_scientific_text(value: str) -> str:
    """Normalize typography without changing scientific identity."""
    text = unicodedata.normalize("NFKC", value)
    text = re.sub(r"[‐‑‒–—−]", "-", text)
    text = text.replace("℃", "°C")
    text = re.sub(r"\s+", " ", text).strip().casefold()
    return text


def _is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, list):
        return not value or all(_is_placeholder(item) for item in value)
    return normalized_scientific_text(str(value)) in PLACEHOLDER_VALUES


def _numeric_tokens(value: str) -> list[str]:
    return re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?", value)


def evidence_value_is_grounded(evidence: dict[str, Any]) -> bool:
    """Require value_raw to be present in its own evidence excerpt.

    Controlled/normalized mappings belong in value_normalized. value_raw must
    remain a source expression, primitive, or list of source expressions.
    """
    quote = normalized_scientific_text(str(evidence.get("evidence_text", "")))
    raw = evidence.get("value_raw")
    if not quote or _is_placeholder(raw):
        return False
    values = raw if isinstance(raw, list) else [raw]
    for item in values:
        item_text = normalized_scientific_text(str(item))
        if item_text and item_text in quote:
            continue
        numbers = _numeric_tokens(item_text)
        if numbers and all(re.search(rf"(?<!\d){re.escape(number)}(?!\d)", quote) for number in numbers):
            continue
        return False
    return True


def evidence_reference_schema(
    extraction_schema: dict[str, Any],
    package: dict[str, Any],
    *,
    model_output: bool,
) -> dict[str, Any]:
    """Constrain evidence by span identity without asking the model to copy it.

    In model-output mode, ``evidence_text`` is a short fixed marker. After
    inference, :func:`hydrate_evidence_from_spans` replaces the marker with an
    exact source excerpt selected deterministically from ``evidence_section``.
    Validation mode accepts that hydrated excerpt while retaining the same
    closed set of input span IDs.
    """
    result = json.loads(json.dumps(extraction_schema, ensure_ascii=False))
    span_ids = [
        str(span.get("span_id", "")).strip()
        for span in package.get("spans", [])
        if str(span.get("span_id", "")).strip()
    ]
    if not span_ids:
        raise ValueError("no_evidence_span_ids")
    properties = result["$defs"]["evidence_value"]["properties"]
    properties["evidence_section"] = {
        "type": "string",
        "enum": span_ids,
    }
    if model_output:
        properties["evidence_text"] = {
            "const": EVIDENCE_REFERENCE_PLACEHOLDER,
        }
    else:
        properties["evidence_text"] = {
            "type": "string",
            "minLength": 1,
        }
    return result


def _exact_supporting_excerpt(text: str, evidence: dict[str, Any]) -> str | None:
    """Return the shortest exact source window that supports ``value_raw``."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    candidates: list[str] = []
    candidates.extend(lines)
    for width in (2, 3, 4, 6):
        candidates.extend(
            "\n".join(lines[index : index + width])
            for index in range(0, max(0, len(lines) - width + 1))
        )
    candidates.extend(
        part.strip()
        for part in re.split(r"\n\s*\n|(?<=[.!?])\s+(?=[A-Z0-9])", text)
        if part.strip()
    )
    candidates.append(text.strip())
    seen: set[str] = set()
    for candidate in sorted(candidates, key=len):
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        probe = dict(evidence)
        probe["evidence_text"] = candidate
        if evidence_value_is_grounded(probe):
            return candidate
    return None


def hydrate_evidence_from_spans(
    payload: dict[str, Any],
    package: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Hydrate model span references into exact, value-supporting excerpts.

    This transformation never supplies or changes a scientific value. It only
    resolves a model-selected span ID to an exact substring of that span.
    Unresolvable references retain the marker so semantic validation fails.
    """
    result = json.loads(json.dumps(payload, ensure_ascii=False))
    spans = {
        str(span.get("span_id", "")): span
        for span in package.get("spans", [])
        if str(span.get("span_id", ""))
    }
    failures: list[dict[str, str]] = []
    collections = (
        "run_candidates",
        "catalyst_candidates",
        "process_stage_candidates",
        "product_candidates",
        "cost_scale_candidates",
    )
    for collection in collections:
        for row_index, row in enumerate(result.get(collection, [])):
            for field, evidence in row.get("fields", {}).items():
                if not isinstance(evidence, dict):
                    continue
                span_id = str(evidence.get("evidence_section", ""))
                span = spans.get(span_id)
                excerpt = (
                    _exact_supporting_excerpt(str(span.get("text", "")), evidence)
                    if span
                    else None
                )
                if excerpt is None:
                    failures.append(
                        {
                            "collection": collection,
                            "row_index": str(row_index),
                            "field": field,
                            "evidence_section": span_id,
                            "reason": (
                                "unknown_evidence_section"
                                if span is None
                                else "value_raw_not_found_in_selected_span"
                            ),
                        }
                    )
                    continue
                evidence["evidence_text"] = excerpt
                page = (
                    span.get("page_start")
                    or span.get("page_range")
                    or span.get("page_end")
                )
                if page not in (None, ""):
                    evidence["evidence_page"] = page
    return result, failures


def detect_catalyst_labels(package: dict[str, Any]) -> list[str]:
    """Extract explicit compared catalyst labels from planning text."""
    planned = package.get("run_plan", {}).get("runs", [])
    if planned:
        labels = [str(row.get("catalyst_label", "")).strip() for row in planned]
        return [label for label in labels if label]
    signaled = package.get("structure_signals", {}).get("catalyst_labels", [])
    if signaled:
        return [str(label) for label in signaled if str(label).strip()]
    text = "\n".join(str(span.get("text", "")) for span in package.get("spans", []))
    match = re.search(
        r"all catalysts are denoted as(?P<body>.{0,700}?)respectively",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return []
    labels: list[str] = []
    for label in CATALYST_LABEL_PATTERN.findall(match.group("body")):
        normalized = re.sub(r"[–—−]", "-", label)
        if normalized.casefold() not in {item.casefold() for item in labels}:
            labels.append(normalized)
    return labels


def _populated_field(rows: list[dict[str, Any]], field: str) -> bool:
    return any(
        field in row.get("fields", {})
        and row["fields"].get(field) is not None
        and not _is_placeholder(row["fields"][field].get("value_raw"))
        for row in rows
    )


def _semantic_entity_errors(table: str, field: str, evidence: dict[str, Any]) -> list[dict[str, str]]:
    raw = normalized_scientific_text(str(evidence.get("value_raw", "")))
    quote = normalized_scientific_text(str(evidence.get("evidence_text", "")))
    combined = f"{raw} {quote}"
    errors: list[dict[str, str]] = []
    if field.startswith("catalyst_particle_size"):
        if any(token in combined for token in ("inner diameter", "outer diameter", "cnt diameter", "nanotube diameter")):
            errors.append({
                "code": "entity_type_mismatch",
                "message": f"{table}.{field}:CNT dimension assigned to catalyst particle size",
            })
        elif not any(token in combined for token in ("catalyst particle", "metal particle", "nanoparticle", "iron oxide particle")):
            errors.append({
                "code": "entity_type_mismatch",
                "message": f"{table}.{field}:missing catalyst-particle context",
            })
    if field in {
        "inner_diameter_mean_nm", "inner_diameter_range_nm",
        "outer_diameter_mean_nm", "outer_diameter_range_nm",
    } and not any(token in combined for token in ("cnt", "nanotube", "inner diameter", "outer diameter")):
        errors.append({
            "code": "entity_type_mismatch",
            "message": f"{table}.{field}:missing CNT-dimension context",
        })
    if field in {"Raman_ratio_type", "Raman_ratio_value"} and not any(
        token in combined for token in ("id/ig", "ig/id", "d band", "g band", "raman")
    ):
        errors.append({
            "code": "entity_type_mismatch",
            "message": f"{table}.{field}:missing Raman-ratio context",
        })
    if field in {"purified_product_purity_wt_percent", "TGA_carbon_content_wt_percent"} and any(
        token in combined for token in ("graphitic carbon", "graphitization", "graphitic carbon selectivity")
    ):
        errors.append({
            "code": "entity_type_mismatch",
            "message": f"{table}.{field}:graphitic-carbon fraction is not CNT purity",
        })
    if field.startswith("yield_") and any(token in combined for token in ("id/ig", "ig/id")):
        errors.append({
            "code": "entity_type_mismatch",
            "message": f"{table}.{field}:Raman ratio assigned to yield",
        })
    return errors


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


def _exact_excerpt_chunks(text: str, max_chars: int = 520) -> list[str]:
    """Split source text without changing any source character inside chunks."""
    chunks: list[str] = []
    cursor = 0
    while cursor < len(text):
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text):
            break
        end = min(len(text), cursor + max_chars)
        if end < len(text):
            floor = cursor + max(80, max_chars // 2)
            candidates = [
                text.rfind(". ", floor, end), text.rfind("; ", floor, end),
                text.rfind(": ", floor, end), text.rfind(" ", floor, end),
            ]
            split = max(candidates)
            if split >= floor:
                end = split + (1 if text[split] in ".;:" else 0)
        chunk = text[cursor:end].strip()
        if chunk:
            chunks.append(chunk)
        cursor = end
    return chunks


def exact_evidence_candidates(package: dict[str, Any]) -> list[str]:
    """Return deterministic exact excerpts eligible for evidence_text."""
    candidates: list[str] = []
    title = str(package.get("source_title", "")).strip()
    if title:
        candidates.append(title)
    for span in package.get("spans", []):
        candidates.extend(_exact_excerpt_chunks(str(span.get("text", ""))))
    return list(dict.fromkeys(candidates))


def constrain_evidence_schema(extraction_schema: dict[str, Any], package: dict[str, Any]) -> dict[str, Any]:
    """Constrain model evidence to verbatim excerpts from this input package."""
    result = json.loads(json.dumps(extraction_schema, ensure_ascii=False))
    candidates = exact_evidence_candidates(package)
    if not candidates:
        raise ValueError("no_exact_evidence_candidates")
    result["$defs"]["evidence_value"]["properties"]["evidence_text"] = {
        "type": "string", "enum": candidates,
    }
    return result


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

    source_text = "\n".join([
        str(package.get("source_title", "")),
        *(str(s.get("text", "")) for s in package.get("spans", [])),
    ])
    span_text = normalized_text(source_text)
    allowed = allowed_field_map(formal_schema)
    run_candidates = payload.get("run_candidates", [])
    run_id_list = [str(row.get("candidate_run_id", "")) for row in run_candidates]
    duplicate_run_ids = sorted({
        run_id for run_id in run_id_list if run_id and run_id_list.count(run_id) > 1
    })
    for run_id in duplicate_run_ids:
        errors.append({"code": "duplicate_run_candidate_id", "message": run_id})
    run_ids = set(run_id_list)
    expected_labels = detect_catalyst_labels(package)
    if len(expected_labels) > len(run_ids):
        errors.append({
            "code": "run_split_failure",
            "message": (
                f"explicit_catalyst_labels={len(expected_labels)} output_runs={len(run_ids)} "
                f"labels={json.dumps(expected_labels, ensure_ascii=False)}"
            ),
        })
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
                if not (collection == "run_candidates" and row_id in duplicate_run_ids):
                    errors.append({"code": "duplicate_candidate_id", "message": row_id})
            ids_seen.add(row_id)
            run_id = row.get("candidate_run_id") if collection != "run_candidates" else row_id
            if run_id not in run_ids:
                errors.append({"code": "unknown_candidate_run", "message": f"{row_id}->{run_id}"})
            if run_id in linked:
                if table == "catalyst_system":
                    linked[run_id]["catalyst"] += 1
                if table == "reactor_process_gas":
                    linked[run_id]["process"] += 1
                if table == "yield_quality":
                    linked[run_id]["product"] += 1
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
                if not evidence_value_is_grounded(evidence):
                    errors.append({
                        "code": "evidence_value_not_grounded",
                        "message": f"{table}.{field}",
                    })
                errors.extend(_semantic_entity_errors(table, field, evidence))
                _check_bounds(field, evidence, unit_rules, warnings)
                _check_unit(field, evidence, unit_rules, warnings)
    for run_id, counts in linked.items():
        missing = [name for name, count in counts.items() if not count]
        if missing:
            errors.append({"code": "incomplete_run_linkage", "message": f"{run_id}:{','.join(missing)}"})

    process_rows = payload.get("process_stage_candidates", [])
    normalized_source = normalized_scientific_text(source_text)
    explicit_signals = dict(package.get("core_evidence_signals", {}))
    for field, (pattern, collection) in CORE_SIGNAL_RULES.items():
        signaled = (
            bool(explicit_signals[field])
            if field in explicit_signals
            else bool(pattern.search(normalized_source))
        )
        if signaled and collection == "process_stage_candidates" and not _populated_field(process_rows, field):
            errors.append({
                "code": "missing_core_field_with_explicit_evidence",
                "message": f"reactor_process_gas.{field}",
            })
    explicit_yield = (
        bool(explicit_signals["yield_original"])
        if "yield_original" in explicit_signals
        else bool(
            re.search(
                r"\b(?:carbon\s+productivity|yield)\b.{0,100}\b\d+(?:\.\d+)?\s*g\s*g",
                normalized_source,
                re.IGNORECASE | re.DOTALL,
            )
        )
    )
    if explicit_yield and not _populated_field(payload.get("product_candidates", []), "yield_original"):
        errors.append({
            "code": "missing_core_field_with_explicit_evidence",
            "message": "yield_quality.yield_original",
        })

    # Keep diagnostics stable and non-redundant for queue state and regression reports.
    errors = list({
        (row["code"], row["message"]): row
        for row in errors
    }.values())
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
    if "temperature" in field and field.endswith("_C"):
        key = "temperature_C"
    elif "pressure" in field and field.endswith("_kPa"):
        key = "pressure_kPa"
    elif "flow" in field and field.endswith("_sccm"):
        key = "flow_sccm"
    elif field in {"holding_time_min", "continuous_operation_time_h"}:
        key = "time_min"
    elif field.endswith("_percent") and not any(
        token in field.lower() for token in ("yield", "weight_gain")
    ):
        key = "ordinary_percent"
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
    if field.endswith("_C"):
        expected = "temperature"
    elif field.endswith("_kPa"):
        expected = "pressure"
    elif field.endswith("_min") or field.endswith("_h"):
        expected = "time"
    elif field.endswith("_g"):
        expected = "mass"
    elif field.endswith("_nm"):
        expected = "length"
    elif field.endswith("_sccm"):
        expected = "standard_flow"
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
        "notes": f"First-pass staging revision {revision_id}; domain_expert_verified=false",
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

    issue_counter = 0
    for candidate in payload.get("review_issues", []):
        fields = {k: _value(v) for k, v in candidate.get("fields", {}).items() if v is not None}
        issue_type_raw = str(fields.get("issue_type") or "").strip()
        issue_summary = str(fields.get("issue_summary") or "").strip()
        if normalized_text(issue_summary) in GENERIC_ISSUE_TEXT:
            # First-pass status is already represented by extraction_status.
            # Do not create a business issue row from a generic placeholder.
            continue
        issue_type = issue_type_raw if issue_type_raw in ALLOWED_ISSUE_TYPES else "quality_warning"
        candidate_run = candidate.get("candidate_run_id")
        run_id = run_map.get(candidate_run, "")
        default_table = "source_run" if run_id else "source_master"
        target_table = str(fields.get("target_table") or default_table)
        if target_table not in formal_schema["tables"] or target_table in {"evidence_index", "review_issue_log"}:
            target_table = default_table
        supplied_target = str(fields.get("target_record_id") or "")
        mapped_target = target_ids.get((target_table, supplied_target))
        if mapped_target:
            run_id, target_record_id = mapped_target
        elif target_table == "source_master":
            run_id, target_record_id = "", source_id
        else:
            target_record_id = run_id
        target_field = str(fields.get("target_field") or "record_level")
        if target_field != "record_level" and target_field not in formal_schema["tables"][target_table]["columns"]:
            target_field = "record_level"
        severity = str(fields.get("severity") or "medium")
        if severity not in {"low", "medium", "high", "critical"}:
            severity = "medium"
        issue_counter += 1
        issue_id = f"ISSUE_{token}_{issue_counter:03d}"
        issue_evidence = candidate.get("fields", {}).get("issue_summary")
        if issue_evidence is None:
            issue_evidence = next((value for value in candidate.get("fields", {}).values() if value is not None), None)
        evidence_ids = ""
        if issue_evidence is not None:
            evidence_counter += 1
            evidence_id = f"EVID_{token}_{evidence_counter:04d}"
            evidence_ids = evidence_id
            rows["evidence_index"].append({
                "evidence_id": evidence_id,
                "source_id": source_id,
                "run_id": run_id,
                "target_table": target_table,
                "target_record_id": target_record_id,
                "target_fields": target_field,
                "evidence_type": "review_issue_support",
                "value_status": issue_evidence.get("value_status") or "reported",
                "source_section": issue_evidence.get("evidence_section") or "not_reported",
                "source_locator": f"page {issue_evidence.get('evidence_page')}" if issue_evidence.get("evidence_page") is not None else "not_reported",
                "source_object_ref": "",
                "evidence_text": issue_evidence.get("evidence_text") or "",
                "evidence_summary": str(issue_evidence.get("value_raw") or issue_summary),
                "confidence": issue_evidence.get("confidence") or "low",
                "linked_issue_id": issue_id,
                "notes": "First-pass review issue evidence; domain_expert_verified=false",
            })
        if not evidence_ids:
            # The formal contract requires every real issue to link to evidence.
            # A model issue without evidence is invalid, not a placeholder row.
            continue
        rows["review_issue_log"].append({
            "issue_id": issue_id, "source_id": source_id, "run_id": run_id,
            "issue_type": issue_type,
            "target_table": target_table, "target_record_id": target_record_id,
            "target_field": target_field,
            "issue_summary": issue_summary,
            "conflicting_values": fields.get("conflicting_values") or "",
            "evidence_ids": evidence_ids, "severity": severity,
            "review_status": "pending_human_review", "reviewer": "", "reviewed_at": "", "resolution": "",
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
        _write_staging_csvs(directory, rows_by_table, formal_schema)
        return_code, report = _formal_validation_report(directory, schema_path, dictionary_path)
        if return_code != 0:
            raise FormalStagingValidationError(report)


def export_staging_package(
    rows_by_table: dict[str, list[dict[str, Any]]],
    formal_schema: dict[str, Any],
    output_dir: Path,
    schema_path: Path,
    dictionary_path: Path,
) -> list[Path]:
    """Publish one immutable, versioned eight-CSV review package."""
    if output_dir.exists():
        return_code, report = _formal_validation_report(output_dir, schema_path, dictionary_path)
        if return_code != 0:
            raise FormalStagingValidationError(report)
        return [output_dir / spec["filename"] for spec in formal_schema["tables"].values()]
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_dir.with_name(output_dir.name + f".part-{uuid.uuid4().hex[:8]}")
    temporary.mkdir(parents=False, exist_ok=False)
    try:
        _write_staging_csvs(temporary, rows_by_table, formal_schema)
        return_code, report = _formal_validation_report(temporary, schema_path, dictionary_path)
        if return_code != 0:
            raise FormalStagingValidationError(report)
        os.replace(temporary, output_dir)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return [output_dir / spec["filename"] for spec in formal_schema["tables"].values()]


def _write_staging_csvs(
    directory: Path,
    rows_by_table: dict[str, list[dict[str, Any]]],
    formal_schema: dict[str, Any],
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for table, spec in formal_schema["tables"].items():
        path = directory / spec["filename"]
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=spec["columns"], extrasaction="ignore", lineterminator="\n"
            )
            writer.writeheader()
            for row in rows_by_table.get(table, []):
                writer.writerow({column: _csv_cell(row.get(column, "")) for column in spec["columns"]})


def _formal_validation_report(
    directory: Path,
    schema_path: Path,
    dictionary_path: Path,
) -> tuple[int, str]:
    output = io.StringIO()
    with redirect_stdout(output):
        return_code = validate_eight_tables(directory, schema_path, dictionary_path)
    return return_code, output.getvalue()


def _csv_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(map(str, value))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)
