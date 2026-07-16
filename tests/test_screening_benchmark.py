from __future__ import annotations

import csv
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from scripts.screening_benchmark.benchmark import summarize


class ScreeningBenchmarkMetricTests(unittest.TestCase):
    def test_weighted_recall_indeterminate_and_dedup_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            database = root / "benchmark.sqlite3"
            screening_csv = root / "screening.csv"
            dedup_csv = root / "dedup.csv"
            output_json = root / "metrics.json"
            manifest_json = root / "manifest.json"
            errors_csv = root / "errors.csv"

            with closing(sqlite3.connect(database)) as connection:
                connection.execute(
                    "CREATE TABLE works(source_id TEXT PRIMARY KEY, priority_tier TEXT NOT NULL)"
                )
                for tier, count in {"A": 10, "B": 20, "C": 30, "M": 40, "R": 50}.items():
                    connection.executemany(
                        "INSERT INTO works(source_id,priority_tier) VALUES(?,?)",
                        [(f"{tier}_{index}", tier) for index in range(count)],
                    )
                connection.execute(
                    """
                    CREATE TABLE dedup_decision_log(
                        decision TEXT NOT NULL,
                        match_type TEXT NOT NULL,
                        resolved_source_id TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    "INSERT INTO dedup_decision_log VALUES('auto_merge','title_fuzzy','F_1')"
                )
                connection.commit()

            labels = {
                "A": ["include", "include"],
                "B": ["include", "exclude"],
                "C": ["exclude", "exclude"],
                "M": ["indeterminate", "exclude"],
                "R": ["include", "exclude"],
            }
            with screening_csv.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "source_id", "sample_stratum", "auto_tier", "human_is_target_synthesis",
                        "human_tier", "human_extractability", "human_reason",
                        "error_type", "reviewer", "reviewed_at",
                    ],
                )
                writer.writeheader()
                for tier, tier_labels in labels.items():
                    for index, label in enumerate(tier_labels):
                        writer.writerow({
                            "source_id": f"{tier}_{index}",
                            "sample_stratum": tier,
                            "auto_tier": tier,
                            "human_is_target_synthesis": label,
                            "human_tier": tier,
                            "human_extractability": "indeterminate" if label == "indeterminate" else "extractable",
                            "human_reason": "test review",
                            "error_type": "",
                            "reviewer": "tester",
                            "reviewed_at": "2026-07-16",
                        })

            with dedup_csv.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "decision", "match_type", "human_merge_correct",
                        "human_relation", "reviewer", "reviewed_at",
                    ],
                )
                writer.writeheader()
                writer.writerow({
                    "decision": "auto_merge",
                    "match_type": "title_fuzzy",
                    "human_merge_correct": "no",
                    "human_relation": "distinct_work",
                    "reviewer": "tester",
                    "reviewed_at": "2026-07-16",
                })

            manifest_json.write_text(
                json.dumps({
                    "benchmark_version": "test_design",
                    "tier_population": {"A": 10, "B": 20, "C": 30, "M": 40, "R": 50},
                }),
                encoding="utf-8",
            )

            summary = summarize(
                screening_csv, dedup_csv, database, manifest_json, output_json, errors_csv
            )

            self.assertEqual(summary["A_precision"], 1.0)
            self.assertEqual(summary["AB_target_recall_weighted_estimate"], 0.4444)
            self.assertEqual(summary["R_false_kill_rate"], 0.5)
            self.assertIsNone(summary["R_rule_of_three_95pct_upper_if_zero"])
            self.assertEqual(summary["AB_obvious_non_target_rate"], 0.3333)
            self.assertEqual(summary["M_indeterminate_rate"], 0.5)
            self.assertEqual(
                summary["diagnostic_gates"]["title_fuzzy_false_merge_eq_0"], "fail"
            )
            self.assertEqual(summary["benchmark_decision"], "fail_export_errors_and_revise_rules")
            self.assertEqual(
                json.loads(output_json.read_text(encoding="utf-8"))["review_completion"], 1.0
            )


if __name__ == "__main__":
    unittest.main()
