from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.extraction.package import build_slotted_package
from scripts.production.staging import (
    build_staging_rows,
    constrain_evidence_schema,
    evidence_reference_schema,
    exact_evidence_candidates,
    export_staging_package,
    hydrate_evidence_from_spans,
    validate_payload,
    validate_rows_with_formal_validator,
)
from scripts.production.store import ProductionStore
from scripts.production.workers import pid_alive, reconcile_candidate_queue


ROOT = Path(__file__).resolve().parents[1]


class ProcessLaunchTests(unittest.TestCase):
    def test_current_process_is_detected_as_alive(self) -> None:
        self.assertTrue(pid_alive(os.getpid()))


class EvidenceReferenceTests(unittest.TestCase):
    def test_model_schema_uses_compact_span_reference_marker(self) -> None:
        extraction_schema = json.loads(
            (ROOT / "config/extraction_result_v0.2.schema.json").read_text(
                encoding="utf-8"
            )
        )
        package = {
            "spans": [
                {
                    "span_id": "SPAN_1",
                    "text": "The catalyst was heated to 850 °C for 30 min.",
                }
            ]
        }
        schema = evidence_reference_schema(
            extraction_schema,
            package,
            model_output=True,
        )
        properties = schema["$defs"]["evidence_value"]["properties"]
        self.assertEqual(
            properties["evidence_text"]["const"],
            "__AUTO_FROM_EVIDENCE_SECTION__",
        )
        self.assertEqual(properties["evidence_section"]["enum"], ["SPAN_1"])

    def test_hydration_requires_value_in_model_selected_span(self) -> None:
        package = {
            "spans": [
                {
                    "span_id": "PROCESS",
                    "text": "The catalyst was heated to 850 °C for 30 min.",
                    "page_start": 2,
                },
                {
                    "span_id": "OTHER",
                    "text": "Catalyst preparation used MgO.",
                    "page_start": 1,
                },
            ]
        }
        payload = {
            "process_stage_candidates": [
                {
                    "fields": {
                        "temperature_setpoint_C": {
                            "value_raw": "850 °C",
                            "value_normalized": 850,
                            "unit": "°C",
                            "evidence_text": "__AUTO_FROM_EVIDENCE_SECTION__",
                            "evidence_section": "PROCESS",
                            "evidence_page": None,
                            "confidence": "high",
                            "value_status": "reported",
                        },
                        "holding_time_min": {
                            "value_raw": "30 min",
                            "value_normalized": 30,
                            "unit": "min",
                            "evidence_text": "__AUTO_FROM_EVIDENCE_SECTION__",
                            "evidence_section": "OTHER",
                            "evidence_page": None,
                            "confidence": "high",
                            "value_status": "reported",
                        },
                    }
                }
            ]
        }
        hydrated, failures = hydrate_evidence_from_spans(payload, package)
        temperature = hydrated["process_stage_candidates"][0]["fields"][
            "temperature_setpoint_C"
        ]
        self.assertIn("850 °C", temperature["evidence_text"])
        self.assertEqual(temperature["evidence_page"], 2)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["field"], "holding_time_min")


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

    def test_claim_can_be_limited_to_active_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with ProductionStore(Path(temporary) / "production.sqlite3", ROOT / "config/schema.json") as store:
                store.register_config("OLD", {})
                store.register_config("CURRENT", {})
                store.enqueue("T_OLD", "S_OLD", "a" * 64, "OLD", 1)
                store.enqueue("T_CURRENT", "S_CURRENT", "b" * 64, "CURRENT", 2)
                task = store.claim("worker", "CURRENT")
                self.assertEqual(task["task_id"], "T_CURRENT")
                old = store.connection.execute("SELECT task_status FROM extraction_tasks WHERE task_id='T_OLD'").fetchone()[0]
                self.assertEqual(old, "pending")

    def test_existing_curated_source_is_persistently_excluded_from_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with ProductionStore(Path(temporary) / "production.sqlite3", ROOT / "config/schema.json") as store:
                store.register_config("CFG", {})
                self.assertTrue(store.enqueue("T1", "CURATED", "a" * 64, "CFG", 1))
                self.assertTrue(store.exclude_source(
                "CURATED", "existing_curated_eight_table_package", "data/benchmark/fixtures/six_papers/CURATED",
                ))
                self.assertFalse(store.enqueue("T2", "CURATED", "b" * 64, "CFG", 2))
                self.assertIsNone(store.claim("worker", "CFG"))
                self.assertEqual(store.task_summary("CFG"), {})
                self.assertEqual(
                    store.exclusion_summary(), {"existing_curated_eight_table_package": 1},
                )

    def test_staging_failure_rolls_back_all_tables(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with ProductionStore(Path(temporary) / "production.sqlite3", ROOT / "config/schema.json") as store:
                store.register_config("CFG", {})
                store.enqueue("T1", "S1", "a" * 64, "CFG", 1)
                task = store.claim("worker")
                rows = {name: [] for name in store.schema["tables"]}
                rows["source_master"] = [{"source_id": "S1", "source_type": "paper", "source_title": "T", "publication_year": "2020", "doi_or_patent_no": "not_reported", "screening_class": "candidate_extract", "extraction_status": "needs_review", "review_status": "pending_review"}]
                with self.assertRaises(RuntimeError):
                    store.write_staging(task, "REV", rows, {}, fail_after_table="source_master")
                self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM source_master").fetchone()[0], 0)
                self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM staging_state").fetchone()[0], 0)

    def test_withdraw_staging_keeps_task_history(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with ProductionStore(Path(temporary) / "production.sqlite3", ROOT / "config/schema.json") as store:
                store.register_config("CFG", {})
                store.enqueue("T1", "S1", "a" * 64, "CFG", 1)
                task = store.claim("worker", "CFG")
                rows = {name: [] for name in store.schema["tables"]}
                rows["source_master"] = [{"source_id": "S1"}]
                rows["source_run"] = [{"run_id": "S1_R01", "source_id": "S1"}]
                store.write_staging(task, "REV", rows, {"valid": True})
                deleted = store.withdraw_staging("S1", "existing_curated_eight_table_package")
                self.assertEqual(deleted["source_master"], 1)
                self.assertEqual(deleted["source_run"], 1)
                self.assertEqual(deleted["staging_state"], 1)
                self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM extraction_tasks").fetchone()[0], 1)
                events = [row[0] for row in store.connection.execute("SELECT event_type FROM task_events")]
                self.assertIn("staging_withdrawn", events)
                task_state = store.connection.execute(
                    "SELECT staging_status,superseded_by FROM extraction_tasks WHERE task_id='T1'"
                ).fetchone()
                self.assertEqual(tuple(task_state), ("withdrawn", "existing_curated_eight_table_package"))
                withdrawal = store.connection.execute(
                    "SELECT snapshot_path FROM staging_withdrawals WHERE task_id='T1'"
                ).fetchone()
                self.assertIsNotNone(withdrawal)
                self.assertTrue(Path(withdrawal[0]).is_file())

    def test_completed_inference_can_be_marked_semantically_failed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with ProductionStore(Path(temporary) / "production.sqlite3", ROOT / "config/schema.json") as store:
                store.register_config("CFG", {})
                store.enqueue("T1", "S1", "a" * 64, "CFG", 1)
                task = store.claim("worker", "CFG")
                self.assertIsNotNone(task)
                store.mark_semantic_failure(
                    "T1",
                    superseded_by="existing_curated_eight_table_package",
                    error_codes=["run_split_failure", "entity_type_mismatch"],
                    raw_result_path="raw/attempt_001",
                )
                row = store.connection.execute(
                    """
                    SELECT task_status,extraction_disposition,worker_status,
                           validation_status,staging_status,superseded_by
                    FROM extraction_tasks WHERE task_id='T1'
                    """
                ).fetchone()
                self.assertEqual(
                    tuple(row),
                    (
                        "validation_failed", "reextract_required", "completed",
                        "failed_semantic_validation", "withdrawn",
                        "existing_curated_eight_table_package",
                    ),
                )

    def test_candidate_queue_reconciliation_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config").mkdir()
            shutil.copyfile(ROOT / "config/schema.json", root / "config/schema.json")
            candidate_db = root / "candidate.sqlite3"
            connection = sqlite3.connect(candidate_db)
            connection.execute(
                """CREATE TABLE parse_source_status(
                       source_id TEXT,input_content_hash TEXT,parse_status TEXT,
                       candidate_extract_eligible INTEGER)"""
            )
            connection.executemany(
                "INSERT INTO parse_source_status VALUES (?,?,?,?)",
                [
                    ("ELIGIBLE", "a" * 64, "success", 1),
                    ("REVIEW", "b" * 64, "success", 0),
                    ("FAILED", "c" * 64, "failed", 1),
                ],
            )
            connection.commit()
            connection.close()
            config = {
                "candidate_db": "candidate.sqlite3",
                "production_db": "production.sqlite3",
                "config_snapshot_id": "CFG",
            }
            with ProductionStore(root / "production.sqlite3", root / "config/schema.json") as store:
                store.register_config("CFG", {})
            self.assertEqual(reconcile_candidate_queue(root, config), 1)
            self.assertEqual(reconcile_candidate_queue(root, config), 0)
            with ProductionStore(root / "production.sqlite3", root / "config/schema.json") as store:
                sources = [row[0] for row in store.connection.execute("SELECT source_id FROM extraction_tasks")]
            self.assertEqual(sources, ["ELIGIBLE"])


class ProductionValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.extraction_schema = json.loads((ROOT / "config/extraction_result_v0.2.schema.json").read_text(encoding="utf-8"))
        self.formal_schema = json.loads((ROOT / "config/schema.json").read_text(encoding="utf-8"))
        self.unit_rules = json.loads((ROOT / "config/extraction_unit_rules_v1.json").read_text(encoding="utf-8"))
        self.quote = "Fe catalyst converted methane into carbon nanotubes at 750 °C."
        self.package = {"source_id": "S1", "input_content_hash": "a" * 64, "spans": [{"span_id": "SPAN_1", "text": self.quote}]}

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": "0.2", "source_id": "S1", "input_content_hash": "a" * 64,
            "run_candidates": [{"candidate_run_id": "RUN_CAND_001", "fields": {"run_summary": ev("Fe catalyst converted methane into carbon nanotubes", self.quote)}}],
            "catalyst_candidates": [{"candidate_catalyst_id": "CAT_CAND_001", "candidate_run_id": "RUN_CAND_001", "fields": {"catalyst_label": ev("Fe", self.quote)}}],
            "process_stage_candidates": [{"candidate_stage_id": "STAGE_CAND_001", "candidate_run_id": "RUN_CAND_001", "fields": {
                "stage_type": ev("converted methane into carbon nanotubes", self.quote),
                "temperature_setpoint_C": ev(750, self.quote),
                "carbon_source": ev("methane", self.quote),
            }}],
            "product_candidates": [{"candidate_product_id": "PROD_CAND_001", "candidate_run_id": "RUN_CAND_001", "fields": {"CNT_type_reported": ev("carbon nanotubes", self.quote)}}],
            "cost_scale_candidates": [], "review_issues": [], "extraction_notes": "",
        }

    def test_valid_evidence_value_payload(self) -> None:
        result = validate_payload(self.payload(), self.package, self.extraction_schema, self.formal_schema, self.unit_rules)
        self.assertTrue(result["valid"], result)

    def test_versioned_review_package_exports_exactly_eight_valid_csvs(self) -> None:
        rows = build_staging_rows(
            self.payload(),
            {"title": "Test CNT source", "year": 2020},
            self.formal_schema,
            "REV_TEST",
        )
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary) / "S1" / "REV_TEST"
            first = export_staging_package(
                rows,
                self.formal_schema,
                output_dir,
                ROOT / "config/schema.json",
                ROOT / "config/field_dictionary.csv",
            )
            second = export_staging_package(
                rows,
                self.formal_schema,
                output_dir,
                ROOT / "config/schema.json",
                ROOT / "config/field_dictionary.csv",
            )
            expected = {spec["filename"] for spec in self.formal_schema["tables"].values()}
            self.assertEqual({path.name for path in first}, expected)
            self.assertEqual(first, second)
            self.assertEqual({path.name for path in output_dir.glob("*.csv")}, expected)

    def test_task_schema_allows_only_exact_input_excerpts(self) -> None:
        package = {
            **self.package,
            "source_title": "Exact title",
            "spans": [{"span_id": "SPAN_1", "text": "CNT g rowth was observed at 750 °C. A second exact sentence."}],
        }
        candidates = exact_evidence_candidates(package)
        self.assertIn("CNT g rowth was observed at 750 °C. A second exact sentence.", candidates)
        self.assertFalse(any("CNT growth" in candidate for candidate in candidates))
        constrained = constrain_evidence_schema(self.extraction_schema, package)
        allowed = constrained["$defs"]["evidence_value"]["properties"]["evidence_text"]["enum"]
        self.assertEqual(allowed, candidates)

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

    def test_duplicate_run_candidate_is_hard_failure(self) -> None:
        payload = self.payload()
        payload["run_candidates"].append(json.loads(json.dumps(payload["run_candidates"][0])))
        result = validate_payload(
            payload, self.package, self.extraction_schema, self.formal_schema, self.unit_rules,
        )
        self.assertFalse(result["valid"])
        self.assertIn("duplicate_run_candidate_id", {row["code"] for row in result["errors"]})

    def test_value_must_be_grounded_in_its_own_evidence(self) -> None:
        payload = self.payload()
        payload["catalyst_candidates"][0]["fields"]["catalyst_label"] = ev("Mo", self.quote)
        result = validate_payload(
            payload, self.package, self.extraction_schema, self.formal_schema, self.unit_rules,
        )
        self.assertFalse(result["valid"])
        self.assertIn("evidence_value_not_grounded", {row["code"] for row in result["errors"]})

    def test_multiple_explicit_catalysts_require_multiple_runs(self) -> None:
        package = {
            **self.package,
            "spans": [{
                "span_id": "SPAN_1",
                "text": (
                    "All catalysts are denoted as Fe/MgO, Fe–0.1Mo, Fe–0.5Mo, "
                    "Fe–1Mo, and Mo/MgO, respectively. "
                    + self.quote
                ),
            }],
        }
        result = validate_payload(
            self.payload(), package, self.extraction_schema, self.formal_schema, self.unit_rules,
        )
        self.assertFalse(result["valid"])
        self.assertIn("run_split_failure", {row["code"] for row in result["errors"]})

    def test_cnt_inner_diameter_cannot_enter_catalyst_particle_size(self) -> None:
        quote = "The CNT inner diameter was 6.2 nm."
        package = {
            "source_id": "S1", "input_content_hash": "a" * 64,
            "spans": [{"span_id": "SPAN_1", "text": self.quote + " " + quote}],
        }
        payload = self.payload()
        payload["catalyst_candidates"][0]["fields"]["catalyst_particle_size_mean_nm"] = ev(6.2, quote)
        result = validate_payload(
            payload, package, self.extraction_schema, self.formal_schema, self.unit_rules,
        )
        self.assertFalse(result["valid"])
        self.assertIn("entity_type_mismatch", {row["code"] for row in result["errors"]})

    def test_explicit_core_fact_cannot_be_left_only_in_notes(self) -> None:
        package = {
            **self.package,
            "spans": [{
                "span_id": "SPAN_1",
                "text": self.quote + " 150 mg catalyst was used.",
            }],
        }
        result = validate_payload(
            self.payload(), package, self.extraction_schema, self.formal_schema, self.unit_rules,
        )
        self.assertFalse(result["valid"])
        self.assertIn(
            "missing_core_field_with_explicit_evidence",
            {row["code"] for row in result["errors"]},
        )

    def test_per_run_signal_can_explicitly_mark_figure_only_yield(self) -> None:
        package = {
            **self.package,
            "spans": [{
                "span_id": "SPAN_1",
                "text": (
                    self.quote
                    + " Carbon productivity was 1.03 g gCat.-1 for another catalyst."
                ),
            }],
            "core_evidence_signals": {"yield_original": False},
        }
        result = validate_payload(
            self.payload(),
            package,
            self.extraction_schema,
            self.formal_schema,
            self.unit_rules,
        )
        self.assertNotIn(
            "missing_core_field_with_explicit_evidence",
            {row["code"] for row in result["errors"]},
        )

    def test_slotted_package_preserves_independent_information_categories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            section_path = directory / "sections.csv"
            span_path = directory / "spans.csv"
            section_path.write_text(
                (
                    "source_id,section_id,section_name_normalized,section_name_raw,"
                    "page_start,page_end,text,input_content_hash\n"
                    "S1,SEC1,catalyst_preparation,Experimental,1,1,Title,"
                    + "a" * 64
                    + "\n"
                ),
                encoding="utf-8",
            )
            span_path.write_text(
                (
                    "source_id,span_id,section_id,span_type,text,confidence_rule,"
                    "confidence_score,matched_keywords,page_range,input_content_hash\n"
                    "S1,SP1,SEC1,catalyst,The catalysts were synthesized by "
                    "impregnation.,high,0.9,catalyst,p1,"
                    + "a" * 64
                    + "\n"
                    "S1,SP2,SEC1,process,150 mg catalyst was heated to 850 C "
                    "under pure CH4.,high,0.9,temperature,p1,"
                    + "a" * 64
                    + "\n"
                    "S1,SP3,SEC1,yield,Reported carbon productivity was "
                    "0.40 g gCat.-1 after reaction.,"
                    "high,0.9,productivity,p1,"
                    + "a" * 64
                    + "\n"
                    "S1,SP4,SEC1,characterization,Raman spectroscopy showed "
                    "an ID/IG ratio of 0.30.,high,"
                    "0.9,raman,p1,"
                    + "a" * 64
                    + "\n"
                ),
                encoding="utf-8",
            )
            package = build_slotted_package(
                "S1", section_path, span_path, max_per_slot=2
            )
            self.assertTrue(package["slot_coverage"]["catalyst_preparation"])
            self.assertTrue(package["slot_coverage"]["shared_reaction_conditions"])
            self.assertTrue(package["slot_coverage"]["yield_productivity"])
            self.assertTrue(package["slot_coverage"]["raman"])

    def test_generic_review_placeholder_is_not_written_to_staging(self) -> None:
        payload = self.payload()
        payload["review_issues"] = [{
            "candidate_issue_id": "ISSUE_CAND_001",
            "candidate_run_id": "RUN_CAND_001",
            "fields": {
                "issue_type": ev("needs_review", self.quote),
                "issue_summary": ev("needs_review", self.quote),
            },
        }]
        rows = build_staging_rows(
            payload,
            {"title": "Test CNT source", "year": 2020},
            self.formal_schema,
            "REV_TEST",
        )
        self.assertEqual(rows["review_issue_log"], [])
        validate_rows_with_formal_validator(
            rows,
            self.formal_schema,
            ROOT / "config/schema.json",
            ROOT / "config/field_dictionary.csv",
        )

    def test_real_review_issue_has_linked_evidence(self) -> None:
        payload = self.payload()
        payload["review_issues"] = [{
            "candidate_issue_id": "ISSUE_CAND_001",
            "candidate_run_id": "RUN_CAND_001",
            "fields": {
                "issue_type": ev("run_split_uncertainty", self.quote),
                "issue_summary": ev("Two conditions may represent separate runs", self.quote),
                "target_table": ev("source_run", self.quote),
                "target_record_id": ev("RUN_CAND_001", self.quote),
                "severity": ev("medium", self.quote),
            },
        }]
        rows = build_staging_rows(
            payload,
            {"title": "Test CNT source", "year": 2020},
            self.formal_schema,
            "REV_TEST",
        )
        issue = rows["review_issue_log"][0]
        self.assertEqual(issue["review_status"], "pending_review")
        self.assertIn(issue["evidence_ids"], {row["evidence_id"] for row in rows["evidence_index"]})
        validate_rows_with_formal_validator(
            rows,
            self.formal_schema,
            ROOT / "config/schema.json",
            ROOT / "config/field_dictionary.csv",
        )


if __name__ == "__main__":
    unittest.main()
