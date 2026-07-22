from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from scripts.extraction.llm_runner import (
    AttemptStore,
    LlamaCppClient,
    OllamaClient,
    OpenAICompatibleClient,
    build_model_package,
    constrain_extraction_field_schema,
    extract_candidates,
    openai_strict_schema,
    plan_runs,
    read_json,
)


ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = "__AUTO_FROM_EVIDENCE_SECTION__"


class SequenceModel:
    provider_name = "test"
    model = "sequence-model"

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.requests: list[dict[str, Any]] = []

    def generate_json(self, **request: Any) -> dict[str, Any]:
        self.requests.append(request)
        return self.responses.pop(0)


def evidence(raw: str, normalized: str) -> dict[str, Any]:
    return {
        "value_raw": raw,
        "value_normalized": normalized,
        "unit": None,
        "evidence_text": PLACEHOLDER,
        "evidence_section": "SPAN_1",
        "evidence_page": None,
        "confidence": "high",
        "value_status": "reported",
    }


def valid_plan() -> dict[str, Any]:
    return {
        "schema_version": "run_plan_v1",
        "source_id": "S1",
        "input_content_hash": "a" * 64,
        "runs": [
            {
                "planned_run_id": "PLAN_RUN_001",
                "catalyst_label": "Ni",
                "aliases": [],
                "role": "experimental",
                "catalyst_evidence_span_ids": ["SPAN_1"],
                "result_evidence_span_ids": ["SPAN_1"],
            }
        ],
        "shared_conditions": {},
        "planning_notes": "One explicitly described run.",
    }


class ProviderRequestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "optional": {
                    "oneOf": [{"type": "string"}, {"type": "null"}]
                }
            },
        }

    def request(self, client: Any) -> dict[str, Any]:
        return client.request_body(
            schema_name="test_schema",
            output_schema=self.schema,
            system_prompt="Return JSON.",
            user_payload={"source_id": "S1"},
        )

    def test_api_strict_mode_adapts_optional_schema(self) -> None:
        body = self.request(
            OpenAICompatibleClient(model="m", base_url="https://example.test/v1")
        )
        wire_schema = body["response_format"]["json_schema"]["schema"]
        self.assertEqual(body["response_format"]["type"], "json_schema")
        self.assertEqual(wire_schema["required"], ["optional"])
        self.assertIn("anyOf", wire_schema["properties"]["optional"])
        self.assertNotIn("oneOf", wire_schema["properties"]["optional"])

    def test_api_json_object_mode_embeds_canonical_schema(self) -> None:
        body = self.request(
            OpenAICompatibleClient(
                model="m",
                base_url="https://example.test/v1",
                schema_mode="json-object",
            )
        )
        user_message = json.loads(body["messages"][1]["content"])
        self.assertEqual(body["response_format"], {"type": "json_object"})
        self.assertEqual(user_message["output_schema"], self.schema)

    def test_local_clients_use_their_native_schema_protocols(self) -> None:
        ollama = self.request(
            OllamaClient(model="qwen", base_url="http://127.0.0.1:11434")
        )
        llama_cpp = self.request(
            LlamaCppClient(model="qwen", base_url="http://127.0.0.1:8080/v1")
        )
        self.assertEqual(ollama["format"], self.schema)
        self.assertFalse(ollama["stream"])
        self.assertEqual(
            llama_cpp["response_format"],
            {"type": "json_schema", "schema": self.schema},
        )


class SchemaAndPipelineTests(unittest.TestCase):
    def test_model_field_schema_is_closed_and_blocks_workflow_fields(self) -> None:
        extraction = read_json(ROOT / "config/extraction_result_v0.2.schema.json")
        formal = read_json(ROOT / "config/schema.json")
        constrained = constrain_extraction_field_schema(extraction, formal)
        run_fields = constrained["$defs"]["run_fields"]
        self.assertFalse(run_fields["additionalProperties"])
        self.assertIn("run_label", run_fields["properties"])
        self.assertNotIn("extraction_status", run_fields["properties"])
        self.assertNotIn("fields", constrained["$defs"])

    def test_openai_adapter_does_not_mutate_canonical_schema(self) -> None:
        canonical = {
            "type": "object",
            "properties": {"x": {"type": ["string", "null"]}},
        }
        adapted = openai_strict_schema(canonical)
        self.assertNotIn("required", canonical)
        self.assertEqual(adapted["required"], ["x"])

    def test_planning_repairs_an_invalid_span_reference(self) -> None:
        package = {
            "source_id": "S1",
            "input_content_hash": "a" * 64,
            "spans": [{"span_id": "SPAN_1", "text": "supported text"}],
        }
        bad = valid_plan()
        bad["runs"][0]["result_evidence_span_ids"] = ["NOT_IN_INPUT"]
        model = SequenceModel([bad, valid_plan()])
        with tempfile.TemporaryDirectory() as temporary:
            result = plan_runs(
                model,
                package,
                read_json(ROOT / "config/run_plan_v1.schema.json"),
                AttemptStore(Path(temporary)),
                max_repairs=1,
            )
        self.assertEqual(result, valid_plan())
        repair = model.requests[1]["user_payload"]["repair"]
        self.assertTrue(repair["validation_errors"])

    def test_extraction_is_evidence_hydrated_and_contract_valid(self) -> None:
        package = {
            "source_id": "S1",
            "source_title": "Example source",
            "input_content_hash": "a" * 64,
            "spans": [
                {
                    "span_id": "SPAN_1",
                    "text": (
                        "Run one used Ni in a fixed bed and produced MWCNT at "
                        "lab scale."
                    ),
                    "page_start": 2,
                }
            ],
        }
        payload = {
            "schema_version": "0.2",
            "source_id": "S1",
            "input_content_hash": "a" * 64,
            "run_candidates": [
                {
                    "candidate_run_id": "RUN_CAND_001",
                    "fields": {"run_label": evidence("Run one", "Run one")},
                }
            ],
            "catalyst_candidates": [
                {
                    "candidate_catalyst_id": "CAT_CAND_001",
                    "candidate_run_id": "RUN_CAND_001",
                    "fields": {"catalyst_label": evidence("Ni", "Ni")},
                }
            ],
            "process_stage_candidates": [
                {
                    "candidate_stage_id": "STAGE_CAND_001",
                    "candidate_run_id": "RUN_CAND_001",
                    "fields": {"reactor_type": evidence("fixed bed", "fixed_bed")},
                }
            ],
            "product_candidates": [
                {
                    "candidate_product_id": "PROD_CAND_001",
                    "candidate_run_id": "RUN_CAND_001",
                    "fields": {"CNT_type_reported": evidence("MWCNT", "MWCNT")},
                }
            ],
            "cost_scale_candidates": [
                {
                    "candidate_cost_scale_id": "SCALE_CAND_001",
                    "candidate_run_id": "RUN_CAND_001",
                    "fields": {
                        "scale_level_demonstrated": evidence("lab", "lab")
                    },
                }
            ],
            "review_issues": [],
            "extraction_notes": "Test extraction.",
        }
        model = SequenceModel([payload])
        with tempfile.TemporaryDirectory() as temporary:
            hydrated = extract_candidates(
                model,
                package,
                valid_plan(),
                read_json(ROOT / "config/extraction_result_v0.2.schema.json"),
                read_json(ROOT / "config/schema.json"),
                read_json(ROOT / "config/extraction_unit_rules_v1.json"),
                AttemptStore(Path(temporary)),
                max_repairs=0,
            )
        value = hydrated["process_stage_candidates"][0]["fields"]["reactor_type"]
        self.assertIn("fixed bed", value["evidence_text"])
        self.assertEqual(value["evidence_page"], 2)

    def test_broad_retrieval_keeps_unfamiliar_paper_wording(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            section_csv = root / "sections.csv"
            span_csv = root / "spans.csv"
            with section_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "source_id",
                        "section_id",
                        "section_name_normalized",
                        "section_name_raw",
                        "page_start",
                        "page_end",
                        "text",
                        "input_content_hash",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "source_id": "S1",
                        "section_id": "SEC_1",
                        "section_name_normalized": "experimental",
                        "section_name_raw": "Procedure",
                        "page_start": "1",
                        "page_end": "1",
                        "text": "Example title",
                        "input_content_hash": "b" * 64,
                    }
                )
            with span_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "source_id",
                        "span_id",
                        "section_id",
                        "span_type",
                        "text",
                        "confidence_rule",
                        "confidence_score",
                        "matched_keywords",
                        "page_range",
                        "input_content_hash",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "source_id": "S1",
                        "span_id": "UNFAMILIAR_1",
                        "section_id": "SEC_1",
                        "span_type": "other",
                        "text": (
                            "An unconventional protocol named sample Zeta was "
                            "executed under the stated apparatus configuration."
                        ),
                        "confidence_rule": "test",
                        "confidence_score": "0.9",
                        "matched_keywords": "",
                        "page_range": "1",
                        "input_content_hash": "b" * 64,
                    }
                )
            package = build_model_package(
                source_id="S1",
                section_csv=section_csv,
                span_csv=span_csv,
                max_per_slot=2,
                max_total_chars=2000,
            )
        self.assertEqual(package["spans"][0]["span_id"], "UNFAMILIAR_1")
        self.assertEqual(
            package["selection_stats"]["strategy"],
            "slotted_then_broad",
        )


if __name__ == "__main__":
    unittest.main()
