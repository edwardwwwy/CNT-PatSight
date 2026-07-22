#!/usr/bin/env python3
"""Apply source-first semantic guardrails to one B-class redo package."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.validation.validate_tables import (
    DEFAULT_DICTIONARY,
    DEFAULT_REVIEW_POLICY,
    DEFAULT_SCHEMA,
    validate as validate_base,
)


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config/b_class_redo_policy_v1.json"
NULLS = {"", "not_reported", "not_applicable"}
FACT_TABLES = (
    "catalyst_system",
    "reactor_process_gas",
    "yield_quality",
    "cost_scale_review",
)
IDENTITY_OR_STRUCTURAL_FIELDS = {
    "catalyst_system": {"run_id", "catalyst_id", "notes"},
    "reactor_process_gas": {
        "run_id",
        "process_stage_id",
        "stage_order",
        "process_note",
    },
    "yield_quality": {
        "run_id",
        "product_id",
        "yield_standardization_note",
        "notes",
    },
    "cost_scale_review": {"run_id", "review_note"},
}
NUMERIC_LITERAL = re.compile(
    r"^\s*[~≈]?\s*-?\d+(?:\.\d+)?"
    r"(?:\s*(?:-|–|—|to)\s*[~≈]?\s*-?\d+(?:\.\d+)?)?\s*$",
    re.IGNORECASE,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def target_id(table: str, row: dict[str, str]) -> str:
    if table == "catalyst_system":
        return row["catalyst_id"]
    if table == "reactor_process_gas":
        return row["process_stage_id"]
    if table == "yield_quality":
        return row["product_id"]
    if table == "cost_scale_review":
        return row["run_id"]
    raise KeyError(table)


def split_fields(value: str) -> set[str]:
    return {item.strip() for item in value.split(";") if item.strip()}


def normalized(value: str) -> str:
    return (
        value.lower()
        .replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("°", "")
        .replace(" ", "")
        .replace(",", "")
    )


def numeric_tokens(value: str) -> list[str]:
    return re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", value.replace(",", ""))


def evidence_for_field(
    evidence: list[dict[str, str]], table: str, record_id: str, field: str
) -> list[dict[str, str]]:
    return [
        item
        for item in evidence
        if item["target_table"] == table
        and item["target_record_id"] == record_id
        and (
            item["target_fields"] == "record_level"
            or field in split_fields(item["target_fields"])
        )
    ]


def validate_redo(package: Path, policy: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    tables = {
        table: read_csv(package / f"{table}.csv")
        for table in (
            "source_master",
            "source_run",
            *FACT_TABLES,
            "evidence_index",
            "review_issue_log",
        )
    }
    evidence = tables["evidence_index"]
    allowed_status = set(policy["allowed_value_statuses"])

    review_path = package / "source_review.json"
    if not review_path.is_file():
        errors.append(
            {"code": "missing_source_review", "detail": "source_review.json is required"}
        )
        review: dict[str, Any] = {}
    else:
        review = json.loads(review_path.read_text(encoding="utf-8"))
        if review.get("old_b_facts_used") is not False:
            errors.append(
                {
                    "code": "legacy_fact_contamination",
                    "detail": "old_b_facts_used must be false",
                }
            )
        campaign = review.get("campaign_reconciliation", {})
        reported = campaign.get("result_linked_campaigns_in_paper")
        extracted = campaign.get("extracted_runs")
        if reported is None or extracted is None:
            errors.append(
                {
                    "code": "missing_campaign_reconciliation",
                    "detail": "result-linked and extracted campaign counts are required",
                }
            )
        elif int(extracted) != len(tables["source_run"]):
            errors.append(
                {
                    "code": "campaign_run_count_mismatch",
                    "detail": f"source_review extracted_runs={extracted}, source_run={len(tables['source_run'])}",
                }
            )
        if tables["source_master"]:
            local_path = tables["source_master"][0].get("local_file_path", "")
            source_path = Path(local_path)
            if not source_path.is_absolute():
                source_path = ROOT / source_path
            if not source_path.is_file():
                errors.append(
                    {
                        "code": "missing_local_source",
                        "detail": str(source_path),
                    }
                )
            if source_path.suffix.lower() == ".pdf":
                visual = review.get("pdf_visual_review", {})
                if visual.get("completed") is not True or not visual.get("pages_checked"):
                    errors.append(
                        {
                            "code": "missing_pdf_visual_review",
                            "detail": "PDF packages require checked pages and completion flag",
                        }
                    )

    for row_number, item in enumerate(evidence, start=2):
        status = item.get("value_status", "")
        if status not in allowed_status:
            errors.append(
                {
                    "code": "invalid_value_status",
                    "detail": f"evidence_index:{row_number} value_status={status!r}",
                }
            )
        if status == "review_assessment" and item.get("target_table") != "cost_scale_review":
            errors.append(
                {
                    "code": "review_assessment_on_fact_field",
                    "detail": f"evidence_index:{row_number} targets {item.get('target_table')}",
                }
            )
        if not item.get("source_locator") or not item.get("source_object_ref"):
            errors.append(
                {
                    "code": "weak_evidence_locator",
                    "detail": f"evidence_index:{row_number} lacks locator/object reference",
                }
            )

    numeric_columns = policy["numeric_columns"]
    for table, fields in numeric_columns.items():
        for row in tables[table]:
            for field in fields:
                value = row.get(field, "").strip()
                if value in NULLS:
                    continue
                if not NUMERIC_LITERAL.fullmatch(value):
                    errors.append(
                        {
                            "code": "non_numeric_value_in_numeric_field",
                            "detail": f"{table}.{field}={value!r}",
                        }
                    )

    for table in FACT_TABLES:
        for row in tables[table]:
            record = target_id(table, row)
            for field, value in row.items():
                value = value.strip()
                if field in IDENTITY_OR_STRUCTURAL_FIELDS[table] or value in NULLS:
                    continue
                applicable = evidence_for_field(evidence, table, record, field)
                if not applicable:
                    errors.append(
                        {
                            "code": "field_without_evidence",
                            "detail": f"{table}.{field}={value!r} at {record}",
                        }
                    )
                    continue
                tokens = numeric_tokens(value)
                reported_evidence = [
                    item for item in applicable if item["value_status"] == "reported"
                ]
                if tokens and reported_evidence:
                    joined = normalized(
                        " ".join(item["evidence_text"] for item in reported_evidence)
                    )
                    missing = [token for token in tokens if normalized(token) not in joined]
                    if missing:
                        errors.append(
                            {
                                "code": "reported_numeric_token_not_grounded",
                                "detail": f"{table}.{field}={value!r}; missing {missing}",
                            }
                        )

    for field, forbidden_values in policy["forbidden_defaults"].items():
        table, column = field.split(".", 1)
        for row in tables[table]:
            value = row.get(column, "").strip()
            if value not in forbidden_values:
                continue
            record = target_id(table, row)
            applicable = evidence_for_field(evidence, table, record, column)
            reported_text = normalized(
                " ".join(
                    item["evidence_text"]
                    for item in applicable
                    if item["value_status"] in {"reported", "normalized"}
                )
            )
            if column == "pressure_original":
                grounded = "atmospheric" in reported_text
            elif column == "pressure_kPa":
                grounded = bool(applicable) and (
                    "101.325" in reported_text
                    or "1atm" in reported_text
                    or "atmospheric" in reported_text
                )
            else:
                grounded = normalized(value) in reported_text
            if not grounded:
                errors.append(
                    {
                        "code": "unsupported_forbidden_default",
                        "detail": f"{field}={value!r} at {record}",
                    }
                )

    run_ids = {row["run_id"] for row in tables["source_run"]}
    for table in ("catalyst_system", "yield_quality", "cost_scale_review"):
        counts = {run_id: 0 for run_id in run_ids}
        for row in tables[table]:
            if row["run_id"] in counts:
                counts[row["run_id"]] += 1
        bad = {run_id: count for run_id, count in counts.items() if count != 1}
        if bad:
            errors.append(
                {
                    "code": "one_row_per_run_failure",
                    "detail": f"{table}: {bad}",
                }
            )

    return {
        "package": package.as_posix(),
        "source_id": tables["source_master"][0]["source_id"] if tables["source_master"] else "",
        "run_count": len(tables["source_run"]),
        "evidence_count": len(evidence),
        "errors": errors,
        "warnings": warnings,
        "passed": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    package = args.package.resolve()
    base_status = validate_base(
        package,
        DEFAULT_SCHEMA,
        DEFAULT_DICTIONARY,
        DEFAULT_REVIEW_POLICY,
    )
    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    report = validate_redo(package, policy)
    report["base_validator_passed"] = base_status == 0
    report["passed"] = report["passed"] and base_status == 0
    if args.write_report:
        (package / "redo_validation.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
