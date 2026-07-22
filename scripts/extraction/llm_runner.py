"""Provider-neutral LLM runner for evidence-grounded eight-table extraction.

The module is intentionally source-agnostic.  A paper is parsed once by the
rule-based full-text pipeline, then every source follows the same two model
calls and deterministic mapping path:

1. plan experimental runs;
2. extract evidence-valued candidate records;
3. hydrate exact evidence from immutable parser spans;
4. validate and export the fixed eight-table package.

Remote OpenAI-compatible APIs, a local Ollama runtime, and a local llama.cpp
server are supported without putting provider-specific code in paper builders.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.extraction.package import (  # noqa: E402
    build_package,
    build_slotted_package,
)
from scripts.production.staging import (  # noqa: E402
    build_staging_rows,
    evidence_reference_schema,
    export_staging_package,
    hydrate_evidence_from_spans,
    validate_payload,
    validate_rows_with_formal_validator,
)


DEFAULT_SECTION_CSV = (
    ROOT / "cache/parse_exports/paper_text_section.csv"
)
DEFAULT_SPAN_CSV = (
    ROOT / "cache/parse_exports/candidate_experiment_span.csv"
)
DEFAULT_METADATA_DB = (
    ROOT
    / "data/raw/literature/metadata/snapshots/screening_rules_v1.2/literature.sqlite3"
)
DEFAULT_OUTPUT_ROOT = ROOT / "runs/extraction/llm"
FORMAL_SCHEMA_PATH = ROOT / "config/schema.json"
FIELD_DICTIONARY_PATH = ROOT / "config/field_dictionary.csv"
EXTRACTION_SCHEMA_PATH = ROOT / "config/extraction_result_v0.2.schema.json"
RUN_PLAN_SCHEMA_PATH = ROOT / "config/run_plan_v1.schema.json"
UNIT_RULES_PATH = ROOT / "config/extraction_unit_rules_v1.json"

MODEL_BLOCKED_FIELDS = {
    "screening_class",
    "extraction_status",
    "review_status",
    "reviewer",
    "reviewed_at",
    "resolution",
}
ISSUE_FIELDS = (
    "issue_type",
    "target_table",
    "target_record_id",
    "target_field",
    "issue_summary",
    "conflicting_values",
    "severity",
)
COLLECTION_FIELD_DEFS = {
    "run": "source_run",
    "catalyst": "catalyst_system",
    "process": "reactor_process_gas",
    "product": "yield_quality",
    "cost": "cost_scale_review",
}
STRUCTURAL_FIELDS = {
    "source_run": {"run_id", "source_id"},
    "catalyst_system": {"run_id", "catalyst_id"},
    "reactor_process_gas": {"run_id", "process_stage_id"},
    "yield_quality": {"run_id", "product_id"},
    "cost_scale_review": {"run_id"},
}


class StructuredModel(Protocol):
    """Minimal interface shared by remote and local structured-output models."""

    provider_name: str
    model: str

    def generate_json(
        self,
        *,
        schema_name: str,
        output_schema: dict[str, Any],
        system_prompt: str,
        user_payload: dict[str, Any],
    ) -> dict[str, Any]: ...


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _parse_json_content(content: Any) -> dict[str, Any]:
    if isinstance(content, dict):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        content = "".join(parts)
    if not isinstance(content, str):
        raise ValueError("model_response_content_is_not_text_or_object")
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise
        parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("model_response_json_is_not_an_object")
    return parsed


def openai_strict_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Adapt the project schema to the OpenAI strict-output subset.

    The canonical project contracts intentionally allow sparse ``fields``
    objects. OpenAI strict structured output requires every declared property
    to appear, so optional evidence values become required nullable values only
    in the wire schema. The returned payload is still checked against the
    canonical schema after inference.
    """
    result = copy.deepcopy(schema)

    def visit(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                visit(item)
            return
        if not isinstance(node, dict):
            return
        if "oneOf" in node and "anyOf" not in node:
            node["anyOf"] = node.pop("oneOf")
        properties = node.get("properties")
        if isinstance(properties, dict):
            node["required"] = list(properties)
            node["additionalProperties"] = False
        for value in node.values():
            visit(value)

    visit(result)
    return result


@dataclass
class HttpClientBase:
    model: str
    base_url: str
    timeout_seconds: int = 1800
    transport_retries: int = 2
    api_key: str = ""
    provider_name: str = "http"

    def _post(self, endpoint: str, body: dict[str, Any]) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(self.transport_retries + 1):
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=self.timeout_seconds,
                ) as response:
                    result = json.load(response)
                if not isinstance(result, dict):
                    raise ValueError("model_http_response_is_not_an_object")
                return result
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt >= self.transport_retries:
                    break
                time.sleep(min(2**attempt, 4))
        assert last_error is not None
        raise RuntimeError(
            f"{self.provider_name}_request_failed:{type(last_error).__name__}:{last_error}"
        ) from last_error


@dataclass
class OpenAICompatibleClient(HttpClientBase):
    """Remote API using the standard strict json_schema response format."""

    provider_name: str = "api"
    schema_mode: str = "strict"

    def request_body(
        self,
        *,
        schema_name: str,
        output_schema: dict[str, Any],
        system_prompt: str,
        user_payload: dict[str, Any],
    ) -> dict[str, Any]:
        if self.schema_mode == "strict":
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": openai_strict_schema(output_schema),
                },
            }
            model_payload = user_payload
        elif self.schema_mode == "json-object":
            response_format = {"type": "json_object"}
            model_payload = {
                "instructions": user_payload,
                "output_schema": output_schema,
            }
        else:
            raise ValueError(f"unsupported_api_schema_mode:{self.schema_mode}")
        return {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(model_payload, ensure_ascii=False),
                },
            ],
            "response_format": response_format,
        }

    def generate_json(
        self,
        *,
        schema_name: str,
        output_schema: dict[str, Any],
        system_prompt: str,
        user_payload: dict[str, Any],
    ) -> dict[str, Any]:
        body = self.request_body(
            schema_name=schema_name,
            output_schema=output_schema,
            system_prompt=system_prompt,
            user_payload=user_payload,
        )
        endpoint = self.base_url.rstrip("/") + "/chat/completions"
        result = self._post(endpoint, body)
        return _parse_json_content(result["choices"][0]["message"]["content"])


@dataclass
class LlamaCppClient(OpenAICompatibleClient):
    """Local llama.cpp server using its schema response_format dialect."""

    provider_name: str = "llama-cpp"
    schema_mode: str = "strict"

    def request_body(
        self,
        *,
        schema_name: str,
        output_schema: dict[str, Any],
        system_prompt: str,
        user_payload: dict[str, Any],
    ) -> dict[str, Any]:
        body = super().request_body(
            schema_name=schema_name,
            output_schema=output_schema,
            system_prompt=system_prompt,
            user_payload=user_payload,
        )
        body["response_format"] = {
            "type": "json_schema",
            "schema": output_schema,
        }
        return body


@dataclass
class OllamaClient(HttpClientBase):
    """Local Ollama /api/chat client with native JSON Schema output."""

    provider_name: str = "ollama"

    def request_body(
        self,
        *,
        schema_name: str,
        output_schema: dict[str, Any],
        system_prompt: str,
        user_payload: dict[str, Any],
    ) -> dict[str, Any]:
        del schema_name
        return {
            "model": self.model,
            "stream": False,
            "format": output_schema,
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(user_payload, ensure_ascii=False),
                },
            ],
        }

    def generate_json(
        self,
        *,
        schema_name: str,
        output_schema: dict[str, Any],
        system_prompt: str,
        user_payload: dict[str, Any],
    ) -> dict[str, Any]:
        body = self.request_body(
            schema_name=schema_name,
            output_schema=output_schema,
            system_prompt=system_prompt,
            user_payload=user_payload,
        )
        endpoint = self.base_url.rstrip("/") + "/api/chat"
        result = self._post(endpoint, body)
        return _parse_json_content(result["message"]["content"])


def constrain_run_plan_schema(
    schema: dict[str, Any],
    package: dict[str, Any],
) -> dict[str, Any]:
    """Restrict all planning evidence references to immutable input span IDs."""
    result = copy.deepcopy(schema)
    span_ids = [
        str(span.get("span_id", "")).strip()
        for span in package.get("spans", [])
        if str(span.get("span_id", "")).strip()
    ]
    if not span_ids:
        raise ValueError("no_run_plan_evidence_spans")
    enum_items = {"type": "string", "enum": span_ids}
    run_properties = result["$defs"]["run"]["properties"]
    run_properties["catalyst_evidence_span_ids"]["items"] = copy.deepcopy(
        enum_items
    )
    run_properties["result_evidence_span_ids"]["items"] = copy.deepcopy(
        enum_items
    )
    shared = result["$defs"]["shared_condition"]["properties"]
    shared["evidence_span_id"] = copy.deepcopy(enum_items)
    return result


def model_field_map(formal_schema: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for table, structural in STRUCTURAL_FIELDS.items():
        columns = formal_schema["tables"][table]["columns"]
        result[table] = [
            field
            for field in columns
            if field not in structural and field not in MODEL_BLOCKED_FIELDS
        ]
    return result


def constrain_extraction_field_schema(
    schema: dict[str, Any],
    formal_schema: dict[str, Any],
) -> dict[str, Any]:
    """Make candidate field names closed and table-specific for model output."""
    result = copy.deepcopy(schema)
    allowed = model_field_map(formal_schema)
    evidence_or_null = {
        "oneOf": [
            {"$ref": "#/$defs/evidence_value"},
            {"type": "null"},
        ]
    }
    for definition, table in COLLECTION_FIELD_DEFS.items():
        name = f"{definition}_fields"
        result["$defs"][name] = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                field: copy.deepcopy(evidence_or_null)
                for field in allowed[table]
            },
        }
        result["$defs"][definition]["properties"]["fields"] = {
            "$ref": f"#/$defs/{name}"
        }
    result["$defs"]["issue_fields"] = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            field: copy.deepcopy(evidence_or_null) for field in ISSUE_FIELDS
        },
    }
    result["$defs"]["issue"]["properties"]["fields"] = {
        "$ref": "#/$defs/issue_fields"
    }
    result["$defs"].pop("fields", None)
    return result


def _json_schema_messages(
    instance: dict[str, Any],
    schema: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "code": "json_schema",
            "message": (
                f"{'/'.join(map(str, error.path))}: {error.message}"
            ),
        }
        for error in Draft202012Validator(schema).iter_errors(instance)
    ]


def validate_run_plan(
    plan: dict[str, Any],
    package: dict[str, Any],
    schema: dict[str, Any],
) -> list[dict[str, str]]:
    errors = _json_schema_messages(plan, schema)
    if plan.get("source_id") != package.get("source_id"):
        errors.append({"code": "source_id_mismatch", "message": "run plan"})
    if plan.get("input_content_hash") != package.get("input_content_hash"):
        errors.append({"code": "content_hash_mismatch", "message": "run plan"})
    runs = plan.get("runs", [])
    if not isinstance(runs, list) or not runs:
        errors.append({"code": "empty_run_plan", "message": "no planned runs"})
        return errors
    ids = [str(row.get("planned_run_id", "")) for row in runs if isinstance(row, dict)]
    if len(ids) != len(set(ids)):
        errors.append({"code": "duplicate_planned_run_id", "message": str(ids)})
    return errors


def validate_plan_alignment(
    payload: dict[str, Any],
    run_plan: dict[str, Any],
) -> list[dict[str, str]]:
    planned = run_plan.get("runs", [])
    expected = [f"RUN_CAND_{index:03d}" for index in range(1, len(planned) + 1)]
    actual = [
        str(row.get("candidate_run_id", ""))
        for row in payload.get("run_candidates", [])
        if isinstance(row, dict)
    ]
    if actual != expected:
        return [
            {
                "code": "run_plan_alignment",
                "message": f"expected={expected}; actual={actual}",
            }
        ]
    return []


class AttemptStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, phase: str, attempt: int, name: str, value: Any) -> Path:
        directory = self.root / phase / f"attempt_{attempt:02d}"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{name}.json"
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return path


def _run_id_mapping(run_plan: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "planned_run_id": str(run.get("planned_run_id", "")),
            "candidate_run_id": f"RUN_CAND_{index:03d}",
            "catalyst_label": str(run.get("catalyst_label", "")),
        }
        for index, run in enumerate(run_plan.get("runs", []), start=1)
    ]


def plan_runs(
    model: StructuredModel,
    package: dict[str, Any],
    run_plan_schema: dict[str, Any],
    attempts: AttemptStore,
    max_repairs: int,
) -> dict[str, Any]:
    schema = constrain_run_plan_schema(run_plan_schema, package)
    repair: dict[str, Any] | None = None
    for attempt in range(1, max_repairs + 2):
        user_payload: dict[str, Any] = {
            "task": "Identify every independent CNT synthesis experimental run.",
            "source_id": package["source_id"],
            "input_content_hash": package["input_content_hash"],
            "rules": [
                "Use only supplied spans and their exact span_id values.",
                "Split different catalyst formulations, temperatures, gas programs, times, controls, or result identities when they represent separate experiments.",
                "Keep conditions shared by all runs in shared_conditions.",
                "Do not invent an unreported run, value, unit, or relationship.",
                "Preserve ambiguous boundaries in planning_notes rather than guessing.",
            ],
            "candidate_package": package,
        }
        if repair is not None:
            user_payload["repair"] = repair
        attempts.write("plan", attempt, "request", user_payload)
        try:
            result = model.generate_json(
                schema_name="cnt_run_plan",
                output_schema=schema,
                system_prompt=(
                    "You plan run boundaries in CNT synthesis papers. Return only "
                    "schema-valid JSON. Evidence span IDs must come from the input."
                ),
                user_payload=user_payload,
            )
            attempts.write("plan", attempt, "response", result)
            errors = validate_run_plan(result, package, schema)
        except Exception as exc:  # provider or malformed JSON is repairable
            result = {}
            errors = [
                {
                    "code": "generation_error",
                    "message": f"{type(exc).__name__}:{exc}",
                }
            ]
        attempts.write("plan", attempt, "validation", {"errors": errors})
        if not errors:
            return result
        repair = {
            "instruction": "Repair the previous response without changing supported facts.",
            "previous_response": result,
            "validation_errors": errors,
        }
    raise RuntimeError("run_plan_failed_after_repairs")


def extract_candidates(
    model: StructuredModel,
    package: dict[str, Any],
    run_plan: dict[str, Any],
    extraction_schema: dict[str, Any],
    formal_schema: dict[str, Any],
    unit_rules: dict[str, Any],
    attempts: AttemptStore,
    max_repairs: int,
) -> dict[str, Any]:
    package_with_plan = copy.deepcopy(package)
    package_with_plan["run_plan"] = run_plan
    strict_schema = constrain_extraction_field_schema(
        extraction_schema,
        formal_schema,
    )
    generation_schema = evidence_reference_schema(
        strict_schema,
        package_with_plan,
        model_output=True,
    )
    validation_schema = evidence_reference_schema(
        strict_schema,
        package_with_plan,
        model_output=False,
    )
    repair: dict[str, Any] | None = None
    for attempt in range(1, max_repairs + 2):
        user_payload: dict[str, Any] = {
            "task": "Extract evidence-valued candidates for the fixed CNT eight-table schema.",
            "source_id": package["source_id"],
            "input_content_hash": package["input_content_hash"],
            "run_plan": run_plan,
            "run_id_mapping": _run_id_mapping(run_plan),
            "allowed_fields": model_field_map(formal_schema),
            "issue_fields": list(ISSUE_FIELDS),
            "rules": [
                "Follow run_id_mapping exactly and keep run_candidates in that order.",
                "Every run needs at least one catalyst, process, and product candidate.",
                "Expand a shared condition into each applicable run using the same supporting span.",
                "For every non-null fact, value_raw must be an exact expression found in the selected evidence_section span.",
                "Use value_normalized only for controlled labels or unit normalization.",
                "Keep reported, calculated, and inferred value_status distinct.",
                "Omit or set null for unreported fields; never fabricate evidence for not_reported.",
                "Do not equate incompatible yield definitions or catalyst and CNT particle dimensions.",
                "Record real conflicts and critical gaps in review_issues with evidence.",
            ],
            "candidate_package": package,
        }
        if repair is not None:
            user_payload["repair"] = repair
        attempts.write("extract", attempt, "request", user_payload)
        raw: dict[str, Any] = {}
        try:
            raw = model.generate_json(
                schema_name="cnt_eight_table_candidates",
                output_schema=generation_schema,
                system_prompt=(
                    "You extract run-level CNT synthesis facts from supplied evidence. "
                    "Return only schema-valid JSON. Never use outside knowledge."
                ),
                user_payload=user_payload,
            )
            attempts.write("extract", attempt, "response", raw)
            errors = _json_schema_messages(raw, generation_schema)
            if not errors:
                hydrated, hydration_failures = hydrate_evidence_from_spans(
                    raw,
                    package_with_plan,
                )
                errors.extend(
                    {
                        "code": "evidence_hydration",
                        "message": canonical_json(item),
                    }
                    for item in hydration_failures
                )
                errors.extend(validate_plan_alignment(hydrated, run_plan))
                if not errors:
                    report = validate_payload(
                        hydrated,
                        package_with_plan,
                        validation_schema,
                        formal_schema,
                        unit_rules,
                    )
                    errors.extend(report["errors"])
                if not errors:
                    attempts.write("extract", attempt, "hydrated", hydrated)
                    attempts.write(
                        "extract",
                        attempt,
                        "validation",
                        {"valid": True, "errors": []},
                    )
                    return hydrated
        except Exception as exc:
            errors = [
                {
                    "code": "generation_error",
                    "message": f"{type(exc).__name__}:{exc}",
                }
            ]
        attempts.write(
            "extract",
            attempt,
            "validation",
            {"valid": False, "errors": errors},
        )
        repair = {
            "instruction": (
                "Repair only the listed structural or evidence errors. Do not "
                "change a scientific value unless the cited span supports it."
            ),
            "previous_response": raw,
            "validation_errors": errors,
        }
    raise RuntimeError("candidate_extraction_failed_after_repairs")


def load_metadata(
    source_id: str,
    package: dict[str, Any],
    metadata_json: Path | None,
    metadata_db: Path,
) -> dict[str, Any]:
    if metadata_json is not None:
        value = read_json(metadata_json)
        if source_id in value and isinstance(value[source_id], dict):
            return dict(value[source_id])
        if value.get("source_id") in {None, source_id}:
            return value
        raise ValueError("metadata_json_source_id_mismatch")
    if metadata_db.is_file():
        with sqlite3.connect(metadata_db) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM works WHERE source_id=?",
                (source_id,),
            ).fetchone()
        if row is not None:
            return dict(row)
    return {
        "source_id": source_id,
        "source_type": "paper",
        "title": package.get("source_title") or source_id,
        "year": "not_reported",
        "language": "not_reported",
        "local_file_path": f"data/interim/parsed_text/by_source/{source_id}.parsed.json",
        "pdf_status": "available",
    }


def revision_id(
    source_id: str,
    content_hash: str,
    provider: str,
    model: str,
) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(
        f"{source_id}|{content_hash}|{provider}|{model}".encode("utf-8")
    ).hexdigest()[:8].upper()
    return f"REV_{timestamp}_{digest}"


def build_model_package(
    *,
    source_id: str,
    section_csv: Path,
    span_csv: Path,
    max_per_slot: int,
    max_total_chars: int,
) -> dict[str, Any]:
    """Blend slot coverage with broad parser ranking for source-agnostic input.

    Slot retrieval protects known scientific categories, while the broad pass
    keeps papers with unfamiliar terminology from disappearing merely because
    they did not match one of the retrieval patterns. Neither pass creates a
    scientific fact; both select immutable parser spans for the model.
    """
    slot_budget = max(1000, int(max_total_chars * 0.7))
    slotted = build_slotted_package(
        source_id=source_id,
        section_csv=section_csv,
        span_csv=span_csv,
        max_per_slot=max_per_slot,
        max_total_chars=slot_budget,
    )
    broad = build_package(
        source_id=source_id,
        section_csv=section_csv,
        span_csv=span_csv,
        max_chars=max_total_chars,
        max_spans=max(32, max_per_slot * 12),
    )
    selected: list[dict[str, Any]] = []
    selected_by_id: dict[str, dict[str, Any]] = {}
    used_chars = 0
    for source in (slotted.get("spans", []), broad.get("spans", [])):
        for span in source:
            span_id = str(span.get("span_id", ""))
            if not span_id:
                continue
            if span_id in selected_by_id:
                existing = selected_by_id[span_id]
                existing["slots"] = sorted(
                    set(existing.get("slots", []))
                    | set(span.get("slots", []))
                )
                continue
            text_length = len(str(span.get("text", "")))
            if selected and used_chars + text_length > max_total_chars:
                continue
            item = copy.deepcopy(span)
            item["slots"] = sorted(item.get("slots", []))
            selected.append(item)
            selected_by_id[span_id] = item
            used_chars += text_length
    if not selected:
        raise ValueError(f"no_candidate_spans_for_source:{source_id}")
    return {
        "package_version": "candidate_package_llm_v1",
        "source_id": source_id,
        "source_title": broad.get("source_title", source_id),
        "input_content_hash": broad["input_content_hash"],
        "sections": broad.get("sections", []),
        "spans": selected,
        "slot_coverage": slotted.get("slot_coverage", {}),
        "selection_stats": {
            "strategy": "slotted_then_broad",
            "selected_spans": len(selected),
            "selected_text_chars": used_chars,
            "max_total_chars": max_total_chars,
        },
    }


def run_llm_extraction(
    *,
    source_id: str,
    model: StructuredModel,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    revision: str | None = None,
    metadata_json: Path | None = None,
    metadata_db: Path = DEFAULT_METADATA_DB,
    section_csv: Path = DEFAULT_SECTION_CSV,
    span_csv: Path = DEFAULT_SPAN_CSV,
    max_repairs: int = 2,
    max_per_slot: int = 4,
    max_total_chars: int = 32000,
) -> list[Path]:
    package = build_model_package(
        source_id=source_id,
        section_csv=section_csv,
        span_csv=span_csv,
        max_per_slot=max_per_slot,
        max_total_chars=max_total_chars,
    )
    formal_schema = read_json(FORMAL_SCHEMA_PATH)
    extraction_schema = read_json(EXTRACTION_SCHEMA_PATH)
    run_plan_schema = read_json(RUN_PLAN_SCHEMA_PATH)
    unit_rules = read_json(UNIT_RULES_PATH)
    metadata = load_metadata(source_id, package, metadata_json, metadata_db)
    current_revision = revision or revision_id(
        source_id,
        package["input_content_hash"],
        model.provider_name,
        model.model,
    )
    output_dir = output_root / source_id / current_revision
    attempt_root = output_dir.with_name(output_dir.name + "_attempts")
    attempts = AttemptStore(attempt_root)
    attempts.write("input", 1, "package", package)
    attempts.write("input", 1, "metadata", metadata)

    run_plan = plan_runs(
        model,
        package,
        run_plan_schema,
        attempts,
        max_repairs,
    )
    payload = extract_candidates(
        model,
        package,
        run_plan,
        extraction_schema,
        formal_schema,
        unit_rules,
        attempts,
        max_repairs,
    )
    rows = build_staging_rows(
        payload,
        metadata,
        formal_schema,
        current_revision,
    )
    validate_rows_with_formal_validator(
        rows,
        formal_schema,
        FORMAL_SCHEMA_PATH,
        FIELD_DICTIONARY_PATH,
    )
    paths = export_staging_package(
        rows,
        formal_schema,
        output_dir,
        FORMAL_SCHEMA_PATH,
        FIELD_DICTIONARY_PATH,
    )
    manifest = {
        "source_id": source_id,
        "revision_id": current_revision,
        "provider": model.provider_name,
        "model": model.model,
        "input_content_hash": package["input_content_hash"],
        "run_count": len(run_plan.get("runs", [])),
        "output_files": [path.name for path in paths],
        "attempt_log": attempt_root.relative_to(ROOT).as_posix()
        if attempt_root.is_relative_to(ROOT)
        else str(attempt_root),
        "status": "needs_review",
    }
    (output_dir / "llm_extraction_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths


def build_model(args: argparse.Namespace) -> StructuredModel:
    model = args.model or os.environ.get("LLM_MODEL", "")
    if not model:
        raise ValueError("model_required_use_--model_or_LLM_MODEL")
    if args.provider == "ollama":
        return OllamaClient(
            model=model,
            base_url=args.base_url or "http://127.0.0.1:11434",
            timeout_seconds=args.timeout_seconds,
            transport_retries=args.transport_retries,
        )
    if args.provider == "llama-cpp":
        return LlamaCppClient(
            model=model,
            base_url=args.base_url or "http://127.0.0.1:8080/v1",
            timeout_seconds=args.timeout_seconds,
            transport_retries=args.transport_retries,
            api_key="",
        )
    base_url = args.base_url or os.environ.get("LLM_API_BASE_URL", "")
    if not base_url:
        raise ValueError("api_base_url_required")
    api_key = os.environ.get(args.api_key_env, "") if args.api_key_env else ""
    return OpenAICompatibleClient(
        model=model,
        base_url=base_url,
        api_key=api_key,
        timeout_seconds=args.timeout_seconds,
        transport_retries=args.transport_retries,
        schema_mode=args.api_schema_mode,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Plan runs with an LLM, extract evidence-valued facts, and export "
            "one validated CNT-LitSight eight-table package."
        )
    )
    parser.add_argument("--source-id", required=True)
    parser.add_argument(
        "--provider",
        choices=("api", "ollama", "llama-cpp"),
        required=True,
    )
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--api-key-env", default="LLM_API_KEY")
    parser.add_argument(
        "--api-schema-mode",
        choices=("strict", "json-object"),
        default="strict",
        help=(
            "Use strict json_schema when supported; json-object embeds the "
            "schema in the prompt for older OpenAI-compatible services."
        ),
    )
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--revision-id")
    parser.add_argument("--metadata-json", type=Path)
    parser.add_argument("--metadata-db", type=Path, default=DEFAULT_METADATA_DB)
    parser.add_argument("--section-csv", type=Path, default=DEFAULT_SECTION_CSV)
    parser.add_argument("--span-csv", type=Path, default=DEFAULT_SPAN_CSV)
    parser.add_argument("--max-repairs", type=int, default=2)
    parser.add_argument("--max-per-slot", type=int, default=4)
    parser.add_argument("--max-total-chars", type=int, default=32000)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--transport-retries", type=int, default=2)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    model = build_model(args)
    paths = run_llm_extraction(
        source_id=args.source_id,
        model=model,
        output_root=args.output_root.resolve(),
        revision=args.revision_id,
        metadata_json=args.metadata_json.resolve() if args.metadata_json else None,
        metadata_db=args.metadata_db.resolve(),
        section_csv=args.section_csv.resolve(),
        span_csv=args.span_csv.resolve(),
        max_repairs=max(0, args.max_repairs),
        max_per_slot=max(1, args.max_per_slot),
        max_total_chars=max(1000, args.max_total_chars),
    )
    print(paths[0].parent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
