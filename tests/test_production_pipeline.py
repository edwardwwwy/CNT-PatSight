from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.production.staging import collapse_identical_candidate_duplicates, validate_payload
from scripts.production.store import ProductionStore


ROOT = Path(__file__).resolve().parents[1]


def ev(value: object, quote: str) -> dict[str, object]:
    return {
        "value_raw": value, "value_normalized": value, "unit": None,
        "evidence_text": quote, "evidence_section": "Experimental", "evidence_page": 1,
        "confidence": "high", "value_status": "reported",
    }


class ProductionStoreTests(unittest.TestCase):
    def test_enqueue_is_idempotent_and_claim_is_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with ProductionStore(Path(temporary) / "production.sqlite3", ROOT / "config/schema.json") as store:
                store.register_config("CFG", {})
                self.assertTrue(store.enqueue("T1", "S1", "a" * 64, "CFG", 1))
                self.assertFalse(store.enqueue("T2", "S1", "a" * 64, "CFG", 1))
                claimed = store.claim("worker-1")
                self.assertEqual(claimed["task_id"], "T1")
                self.assertIsNone(store.claim("worker-2"))

    def test_staging_failure_rolls_back_all_tables(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with ProductionStore(Path(temporary) / "production.sqlite3", ROOT / "config/schema.json") as store:
                store.register_config("CFG", {})
                store.enqueue("T1", "S1", "a" * 64, "CFG", 1)
                task = store.claim("worker")
                rows = {name: [] for name in store.schema["tables"]}
                rows["source_master"] = [{"source_id": "S1", "source_type": "paper", "source_title": "T", "publication_year": "2020", "doi_or_patent_no": "not_reported", "screening_class": "candidate_extract", "extraction_status": "needs_review", "review_status": "pending_human_review"}]
                with self.assertRaises(RuntimeError):
                    store.write_staging(task, "REV", rows, {}, fail_after_table="source_master")
                self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM source_master").fetchone()[0], 0)
                self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM staging_state").fetchone()[0], 0)


class ProductionValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.extraction_schema = json.loads((ROOT / "config/llm_extraction_v0.2.schema.json").read_text(encoding="utf-8"))
        self.formal_schema = json.loads((ROOT / "config/schema.json").read_text(encoding="utf-8"))
        self.unit_rules = json.loads((ROOT / "config/llm_unit_rules_v1.json").read_text(encoding="utf-8"))
        self.quote = "Fe catalyst converted methane into carbon nanotubes at 750 °C."
        self.package = {"source_id": "S1", "input_content_hash": "a" * 64, "spans": [{"span_id": "SPAN_1", "text": self.quote}]}

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": "0.2", "source_id": "S1", "input_content_hash": "a" * 64,
            "run_candidates": [{"candidate_run_id": "RUN_CAND_001", "fields": {"run_summary": ev("run", self.quote)}}],
            "catalyst_candidates": [{"candidate_catalyst_id": "CAT_CAND_001", "candidate_run_id": "RUN_CAND_001", "fields": {"catalyst_label": ev("Fe", self.quote)}}],
            "process_stage_candidates": [{"candidate_stage_id": "STAGE_CAND_001", "candidate_run_id": "RUN_CAND_001", "fields": {"stage_type": ev("cnt_growth", self.quote), "temperature_setpoint_C": ev(750, self.quote)}}],
            "product_candidates": [{"candidate_product_id": "PROD_CAND_001", "candidate_run_id": "RUN_CAND_001", "fields": {"CNT_type_reported": ev("CNT", self.quote)}}],
            "cost_scale_candidates": [], "review_issues": [], "extraction_notes": "",
        }

    def test_valid_evidence_value_payload(self) -> None:
        result = validate_payload(self.payload(), self.package, self.extraction_schema, self.formal_schema, self.unit_rules)
        self.assertTrue(result["valid"], result)

    def test_paraphrased_evidence_is_rejected(self) -> None:
        payload = self.payload()
        payload["product_candidates"][0]["fields"]["CNT_type_reported"]["evidence_text"] = "A paraphrase that is absent from the source."
        result = validate_payload(payload, self.package, self.extraction_schema, self.formal_schema, self.unit_rules)
        self.assertFalse(result["valid"])
        self.assertIn("evidence_not_in_input", {row["code"] for row in result["errors"]})

    def test_incomplete_run_is_rejected(self) -> None:
        payload = self.payload()
        payload["product_candidates"] = []
        result = validate_payload(payload, self.package, self.extraction_schema, self.formal_schema, self.unit_rules)
        self.assertFalse(result["valid"])
        self.assertIn("incomplete_run_linkage", {row["code"] for row in result["errors"]})

    def test_only_identical_candidate_duplicates_are_collapsed(self) -> None:
        payload = self.payload()
        payload["run_candidates"].append(json.loads(json.dumps(payload["run_candidates"][0])))
        normalized, collapsed = collapse_identical_candidate_duplicates(payload)
        self.assertEqual(len(normalized["run_candidates"]), 1)
        self.assertEqual(collapsed[0]["candidate_id"], "RUN_CAND_001")

        divergent = self.payload()
        duplicate = json.loads(json.dumps(divergent["run_candidates"][0]))
        duplicate["fields"]["run_summary"] = ev("different", self.quote)
        divergent["run_candidates"].append(duplicate)
        normalized, collapsed = collapse_identical_candidate_duplicates(divergent)
        self.assertEqual(len(normalized["run_candidates"]), 2)
        self.assertEqual(collapsed, [])


if __name__ == "__main__":
    unittest.main()
