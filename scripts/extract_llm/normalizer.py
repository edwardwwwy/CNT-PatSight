from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any


ARRAY_KEYS = {
    "run_candidates": "candidate_run_id",
    "catalyst_candidates": "candidate_catalyst_id",
    "process_stage_candidates": "candidate_stage_id",
    "product_candidates": "candidate_product_id",
    "cost_scale_candidates": "candidate_cost_scale_id",
    "source_observations": "candidate_observation_id",
    "review_issues": "candidate_issue_id",
}

TARGET_ALIASES = {
    "catalyst_candidate": "catalyst",
    "process_stage_candidate": "process_stage",
    "product_candidate": "product",
    "cost_scale_candidate": "cost_scale",
    "run_candidate": "run",
    "source_observation": "source_observation",
}

FIELD_ALIASES = {
    "product_characterization.CNT_type": "CNT_type_reported",
    "product_characterization.diameter": "outer_diameter_range_nm",
    "product_characterization.wall_number": "wall_number_summary",
    "product_characterization.morphology": "morphology",
    "product_characterization.yield": "yield_original",
    "product_characterization.purity": "product_mixture_summary",
    "product_characterization.raman_analysis": "Raman_ratio_type",
    "product_characterization.tga_analysis": "TGA_carbon_content_wt_percent",
}

STAGE_TYPE_ALIASES = {
    "preparation": "other",
    "catalyst_preparation": "other",
    "growth": "cnt_growth",
    "cnt growth": "cnt_growth",
    "catalytic_growth": "cnt_growth",
    # Hydrogen treatment after growth is not necessarily reduction or
    # purification. Keep the reported detail in process_note and avoid
    # inventing a more specific controlled stage.
    "catalytic_hydrogenation": "other",
}

OBSERVATION_TYPE_ALIASES = {
    "catalyst_preparation": "preparation_hint",
    "catalyst_characterization": "other",
    "cnt_growth": "transferable_route",
    "product_characterization": "other",
    "yield": "other",
    "conversion": "other",
    "diameter": "other",
    "morphology": "other",
    "purity": "other",
}

VALUE_STATUS_ALIASES = {
    "measured": "reported",
    "observed": "reported",
    "direct": "reported",
    "derived": "calculated",
    "estimated": "inferred",
}

YIELD_METRIC_ALIASES = {
    "carbon weight gain": "carbon_weight_gain_percent",
    "carbon_weight_gain": "carbon_weight_gain_percent",
    "g-cnts/g-catalyst": "CNT_yield_per_catalyst",
    "cnt_yield_per_catalyst_g_gcat": "CNT_yield_per_catalyst",
}

PURITY_BASIS_ALIASES = {
    # "TGA analysis" alone does not establish whether the sample was
    # as-synthesized or purified, so retain the ambiguity for review.
    "tga analysis": "author_unspecified",
}


def _schema_properties(schema_path: Path) -> dict[str, set[str]]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return {
        key: set(value["items"]["properties"])
        for key, value in schema["properties"].items()
        if isinstance(value, dict) and value.get("type") == "array" and "items" in value and "properties" in value["items"]
    }


def _first_run_id(payload: dict[str, Any]) -> str | None:
    runs = payload.get("run_candidates", [])
    return runs[0].get("candidate_run_id") if runs else None


def _map_target_field(value: str, target_type: str) -> str:
    if value in FIELD_ALIASES:
        return FIELD_ALIASES[value]
    if "." in value:
        tail = value.split(".")[-1]
        if tail in {"CNT_type", "diameter", "wall_number", "morphology", "yield", "purity"}:
            return FIELD_ALIASES.get(f"product_characterization.{tail}", "run_summary")
        return tail
    if value in {"run_candidates", "catalyst_candidates", "process_stage_candidates", "product_candidates", "cost_scale_candidates"}:
        return {"run_candidates": "run_summary", "catalyst_candidates": "catalyst_label", "process_stage_candidates": "process_note", "product_candidates": "yield_original", "cost_scale_candidates": "scale_evidence_summary"}[value]
    return value


def _referenced_spans(spans: list[dict[str, Any]], span_ids: list[str]) -> list[dict[str, Any]]:
    requested = set(span_ids)
    return [
        span for span in spans
        if requested.intersection({str(span.get("span_id", "")), *map(str, span.get("duplicate_span_ids", []))})
    ]


def _quote_tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if len(token) >= 3}


def _exact_excerpt_for_paraphrase(quote: str, spans: list[dict[str, Any]]) -> str:
    quote_tokens = _quote_tokens(quote)
    candidates: list[tuple[int, int, str]] = []
    for span in spans:
        text = str(span.get("text", "")).strip()
        if not text:
            continue
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]
        for sentence in sentences:
            overlap = len(quote_tokens.intersection(_quote_tokens(sentence)))
            candidates.append((overlap, -len(sentence), sentence))
    if not candidates:
        return ""
    overlap, _, excerpt = max(candidates)
    if overlap:
        return excerpt
    return min((str(span.get("text", "")).strip() for span in spans if str(span.get("text", "")).strip()), key=len)


def _normalize_quote(
    quote: str,
    spans: list[dict[str, Any]],
    span_ids: list[str],
) -> tuple[str, str | None]:
    if not quote:
        return quote, None
    normalized_quote = " ".join(quote.split()).lower()
    referenced = _referenced_spans(spans, span_ids) or spans
    normalized_spans = [" ".join(str(span.get("text", "")).split()) for span in referenced]
    if any(normalized_quote in span.lower() for span in normalized_spans):
        return quote, None
    for fragment in quote.split("..."):
        fragment = " ".join(fragment.split()).strip()
        if len(fragment) >= 24 and any(fragment.lower() in span.lower() for span in normalized_spans):
            return fragment, "quote_ellipsis_repaired"
    excerpt = _exact_excerpt_for_paraphrase(quote, referenced)
    if excerpt:
        return excerpt, "quote_paraphrase_replaced"
    return quote, None


def _normalize_controlled_value(
    row: dict[str, Any],
    field: str,
    aliases: dict[str, str],
    issues: list[dict[str, Any]],
) -> None:
    value = row.get(field)
    if not isinstance(value, str):
        return
    mapped = aliases.get(value.strip().lower())
    if mapped and mapped != value:
        row[field] = mapped
        issues.append({
            "code": "enum_alias_normalized",
            "message": f"{field} {value} mapped to {mapped}",
        })


def normalize_payload(payload: dict[str, Any], package: dict[str, Any], schema_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    properties = _schema_properties(schema_path)
    normalized: dict[str, Any] = {
        "schema_version": "0.1",
        "source_id": package["source_id"],
        "source_title": package["source_title"],
        "input_content_hash": package["input_content_hash"],
        "extraction_scope": "candidate_spans_only",
        "run_candidates": [],
        "catalyst_candidates": [],
        "process_stage_candidates": [],
        "product_candidates": [],
        "cost_scale_candidates": [],
        "source_observations": [],
        "evidence_claims": [],
        "review_issues": [],
        "extraction_notes": str(payload.get("extraction_notes", "")),
    }
    issues: list[dict[str, Any]] = []
    run_id = _first_run_id(payload)
    for key, id_field in ARRAY_KEYS.items():
        if key == "review_issues":
            continue
        for index, original in enumerate(payload.get(key, []) if isinstance(payload.get(key, []), list) else [], start=1):
            row = copy.deepcopy(original)
            if key == "process_stage_candidates":
                row.setdefault("stage_order", index)
                _normalize_controlled_value(row, "stage_type", STAGE_TYPE_ALIASES, issues)
            if key == "product_candidates":
                if isinstance(row.get("CNT_type_confirmed"), bool):
                    row["CNT_type_confirmed"] = row.get("CNT_type_reported") if row.get("CNT_type_confirmed") else None
                _normalize_controlled_value(row, "primary_yield_metric", YIELD_METRIC_ALIASES, issues)
                if (
                    row.get("primary_yield_metric") == "CNT_yield_per_catalyst"
                    and "/h" in str(row.get("yield_unit_standardized", "")).lower()
                ):
                    row["primary_yield_metric"] = "CNT_productivity"
                    issues.append({
                        "code": "yield_metric_unit_normalized",
                        "message": "hour-normalized CNT_yield_per_catalyst mapped to CNT_productivity",
                    })
                _normalize_controlled_value(row, "purity_basis", PURITY_BASIS_ALIASES, issues)
            if key == "cost_scale_candidates" and row.get("quantitative_cost_reported") is None:
                row["quantitative_cost_reported"] = False
                issues.append({"code": "null_boolean_defaulted", "message": "quantitative_cost_reported null mapped to false"})
            if key in {"catalyst_candidates", "process_stage_candidates", "product_candidates", "cost_scale_candidates"}:
                if not row.get("candidate_run_id") and run_id:
                    row["candidate_run_id"] = run_id
                    issues.append({"code": "run_reference_defaulted", "message": f"{key} row {index} linked to first candidate run"})
            target_properties = properties[key]
            cleaned = {field: row[field] for field in target_properties if field in row}
            cleaned.setdefault(id_field, f"{id_field.replace('candidate_', '').upper()}_CAND_{index:03d}")
            if key == "run_candidates":
                cleaned.setdefault("evidence_span_ids", row.get("evidence_span_ids", []))
            elif key in {"catalyst_candidates", "process_stage_candidates", "product_candidates", "cost_scale_candidates"}:
                cleaned.setdefault("candidate_run_id", run_id or "RUN_CAND_001")
                cleaned.setdefault("confidence", float(row.get("confidence", 0.4) or 0.4))
                cleaned.setdefault("evidence_span_ids", row.get("evidence_span_ids", []))
            elif key == "source_observations":
                _normalize_controlled_value(cleaned, "observation_type", OBSERVATION_TYPE_ALIASES, issues)
                _normalize_controlled_value(cleaned, "value_status", VALUE_STATUS_ALIASES, issues)
            normalized[key].append(cleaned)

    known_ids = {row.get("span_id") for row in package.get("spans", [])}
    for index, original in enumerate(payload.get("evidence_claims", []) if isinstance(payload.get("evidence_claims", []), list) else [], start=1):
        claim = dict(original)
        target_type = TARGET_ALIASES.get(claim.get("target_type"), claim.get("target_type"))
        target_id = claim.get("target_id") or claim.get("target_value")
        if not target_type:
            field = str(claim.get("target_field", ""))
            target_type = next((alias for token, alias in (("catalyst", "catalyst"), ("process", "process_stage"), ("product", "product"), ("scale", "cost_scale"), ("run", "run")) if token in field), "run")
        target_fields = claim.get("target_fields")
        if not target_fields:
            target_fields = [_map_target_field(str(claim.get("target_field", "run_summary")), target_type)]
        span_ids = claim.get("span_ids", claim.get("evidence_span_ids", []))
        quote, repair_code = _normalize_quote(
            str(claim.get("evidence_quote", claim.get("quote", ""))),
            package.get("spans", []),
            span_ids,
        )
        if repair_code:
            issues.append({
                "code": repair_code,
                "message": f"Claim CLM_{index:03d} quote replaced with an exact referenced-span excerpt",
            })
        value_status = claim.get("value_status", "reported")
        if isinstance(value_status, str) and value_status.strip().lower() in VALUE_STATUS_ALIASES:
            mapped = VALUE_STATUS_ALIASES[value_status.strip().lower()]
            issues.append({
                "code": "enum_alias_normalized",
                "message": f"value_status {value_status} mapped to {mapped}",
            })
            value_status = mapped
        normalized["evidence_claims"].append({
            "claim_id": f"CLM_{index:03d}",
            "target_type": target_type,
            "target_id": target_id or "",
            "target_fields": target_fields,
            "span_ids": span_ids,
            "evidence_quote": quote,
            "value_status": value_status,
            "confidence": float(claim.get("confidence", 0.4) or 0.4),
            "notes": str(claim.get("notes", "")),
        })

    issue_aliases = {"critical_gap": "critical_data_gap", "uncertainty": "definition_ambiguity"}
    for index, original in enumerate(payload.get("review_issues", []) if isinstance(payload.get("review_issues", []), list) else [], start=1):
        issue = dict(original)
        normalized["review_issues"].append({
            "candidate_issue_id": f"ISSUE_CAND_{index:03d}",
            "candidate_run_id": issue.get("candidate_run_id"),
            "issue_type": issue_aliases.get(issue.get("issue_type"), issue.get("issue_type", "quality_warning")),
            "target_type": TARGET_ALIASES.get(issue.get("target_type"), issue.get("target_type", "source")),
            "target_id": issue.get("target_id"),
            "target_field": issue.get("target_field", ""),
            "issue_summary": issue.get("issue_summary", ""),
            "conflicting_values": issue.get("conflicting_values") or [],
            "evidence_span_ids": issue.get("evidence_span_ids", []),
            "severity": issue.get("severity", "medium"),
            "review_status": "open",
        })
    for row in normalized["review_issues"]:
        if row["issue_type"] == "critical_data_gap":
            issues.append({"code": "critical_gap_preserved", "message": row["issue_summary"], "severity": "warning"})
    return normalized, issues
