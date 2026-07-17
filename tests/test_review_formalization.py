from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.validation.validate_tables import validate


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "config/schema.json"
DICTIONARY_PATH = ROOT / "config/field_dictionary.csv"
REVIEW_POLICY_PATH = ROOT / "config/review_policy.json"


class ReviewFormalizationTests(unittest.TestCase):
    def _write_package(
        self,
        directory: Path,
        *,
        formal: bool,
        issue_status: str | None = None,
    ) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        extraction_status = "reviewed" if formal else "needs_review"
        review_status = "reviewed" if formal else "pending_review"
        rows = {
            "source_master": [
                {
                    "source_id": "S1",
                    "source_type": "paper",
                    "source_title": "Formalization test source",
                    "publication_year": "2025",
                    "doi_or_patent_no": "10.0000/example",
                    "screening_class": (
                        "formal_extract" if formal else "candidate_extract"
                    ),
                    "extraction_status": extraction_status,
                    "review_status": review_status,
                }
            ],
            "source_run": [
                {
                    "run_id": "R1",
                    "source_id": "S1",
                    "run_label": "Run 1",
                    "data_type": "experimental",
                    "target_track": "CNT",
                    "relevance_class": "A",
                    "extraction_status": extraction_status,
                    "extraction_confidence": "high",
                }
            ],
            "catalyst_system": [
                {
                    "run_id": "R1",
                    "catalyst_id": "C1",
                    "catalyst_label": "Ni/Al2O3",
                    "active_metals": "Ni",
                    "support_material": "Al2O3",
                    "preparation_method": "impregnation",
                }
            ],
            "reactor_process_gas": [
                {
                    "run_id": "R1",
                    "process_stage_id": "ST1",
                    "stage_order": "1",
                    "stage_type": "growth",
                    "reactor_type": "fixed_bed",
                }
            ],
            "yield_quality": [
                {
                    "run_id": "R1",
                    "product_id": "P1",
                    "primary_yield_metric": "mass_yield",
                    "yield_original": "10 wt%",
                    "yield_definition_original": "product/feed",
                    "CNT_type_reported": "MWCNT",
                    "CNT_type_confirmed": "MWCNT",
                    "CNT_type_evidence": "TEM",
                }
            ],
            "cost_scale_review": [
                {
                    "run_id": "R1",
                    "scale_level_demonstrated": "lab",
                    "scale_level_claimed": "lab",
                    "quantitative_cost_reported": "no",
                }
            ],
            "evidence_index": [
                {
                    "evidence_id": f"E{index}",
                    "source_id": "S1",
                    "run_id": "R1",
                    "target_table": table_name,
                    "target_record_id": record_id,
                    "target_fields": "record_level",
                    "evidence_type": "direct_quote",
                    "value_status": "reported",
                    "source_locator": "page 1",
                    "evidence_summary": "Verified against the source.",
                    "confidence": "high",
                }
                for index, (table_name, record_id) in enumerate(
                    (
                        ("catalyst_system", "C1"),
                        ("reactor_process_gas", "ST1"),
                        ("yield_quality", "P1"),
                        ("cost_scale_review", "R1"),
                    ),
                    start=1,
                )
            ],
            "review_issue_log": [],
        }

        if issue_status is not None:
            issue = {
                "issue_id": "I1",
                "source_id": "S1",
                "run_id": "R1",
                "issue_type": "evidence_gap",
                "target_table": "catalyst_system",
                "target_record_id": "C1",
                "target_field": "active_metals",
                "issue_summary": "Check the catalyst identity.",
                "evidence_ids": "E1",
                "severity": "high",
                "review_status": issue_status,
            }
            if issue_status == "reviewed":
                issue.update(
                    {
                        "reviewer": "codex",
                        "reviewed_at": "2026-07-17T00:00:00Z",
                        "resolution": "Confirmed directly against the cited evidence.",
                    }
                )
            rows["review_issue_log"] = [issue]

        for table_name, spec in schema["tables"].items():
            with (directory / spec["filename"]).open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=spec["columns"])
                writer.writeheader()
                writer.writerows(rows[table_name])

    def _validate(self, *, formal: bool, issue_status: str | None = None) -> int:
        with tempfile.TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir)
            self._write_package(
                package_dir,
                formal=formal,
                issue_status=issue_status,
            )
            with redirect_stdout(io.StringIO()):
                return validate(
                    package_dir,
                    SCHEMA_PATH,
                    DICTIONARY_PATH,
                    REVIEW_POLICY_PATH,
                )

    def test_new_first_pass_uses_pending_review(self) -> None:
        self.assertEqual(self._validate(formal=False), 0)

    def test_unresolved_high_issue_blocks_formalization(self) -> None:
        self.assertEqual(
            self._validate(formal=True, issue_status="pending_review"),
            1,
        )

    def test_agent_reviewed_issue_allows_formalization(self) -> None:
        self.assertEqual(self._validate(formal=True, issue_status="reviewed"), 0)


if __name__ == "__main__":
    unittest.main()
