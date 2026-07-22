#!/usr/bin/env python3
"""Validate a source package or the combined formal CNT-PatSight eight tables."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = PROJECT_ROOT / "config" / "schema.json"
DEFAULT_DICTIONARY = PROJECT_ROOT / "config" / "field_dictionary.csv"
DEFAULT_REVIEW_POLICY = PROJECT_ROOT / "config" / "review_policy.json"
NULL_SENTINELS = {"", "not_applicable", "not_reported"}
FACT_TABLES = {
    "source_master",
    "source_run",
    "catalyst_system",
    "reactor_process_gas",
    "yield_quality",
    "cost_scale_review",
}
EVIDENCE_REQUIRED_TABLES = {
    "catalyst_system",
    "reactor_process_gas",
    "yield_quality",
    "cost_scale_review",
}
DICTIONARY_COLUMNS = [
    "table_name",
    "field_name",
    "description_cn",
    "data_type",
    "unit",
    "required_level",
    "population_expectation",
    "controlled_values_or_format",
    "null_policy",
    "inclusion_rationale",
]


def read_schema(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = list(reader.fieldnames or [])
        rows = []
        for row in reader:
            cleaned = {
                key: (value or "").strip()
                for key, value in row.items()
                if key is not None
            }
            if any(cleaned.values()):
                rows.append(cleaned)
    return headers, rows


def split_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def build_target_keys(
    table_name: str, rows: list[dict[str, str]]
) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for row in rows:
        if table_name == "source_master":
            keys.add(("not_applicable", row.get("source_id", "")))
        elif table_name in {"source_run", "cost_scale_review"}:
            run_id = row.get("run_id", "")
            keys.add((run_id, run_id))
        elif table_name == "catalyst_system":
            keys.add((row.get("run_id", ""), row.get("catalyst_id", "")))
        elif table_name == "reactor_process_gas":
            keys.add((row.get("run_id", ""), row.get("process_stage_id", "")))
        elif table_name == "yield_quality":
            keys.add((row.get("run_id", ""), row.get("product_id", "")))
    return keys


def validate_dictionary(
    schema: dict, dictionary_path: Path, errors: list[str]
) -> None:
    if not dictionary_path.is_file():
        errors.append(f"字段字典缺失: {dictionary_path}")
        return

    headers, rows = read_csv(dictionary_path)
    if headers != DICTIONARY_COLUMNS:
        errors.append("field_dictionary.csv 字段或字段顺序不符合约定")
        return

    pairs = [(row.get("table_name", ""), row.get("field_name", "")) for row in rows]
    for pair, count in Counter(pairs).items():
        if count > 1:
            errors.append(f"字段字典重复定义: {pair[0]}.{pair[1]}")

    expected = {
        (table_name, field_name)
        for table_name, spec in schema["tables"].items()
        for field_name in spec["columns"]
    }
    actual = set(pairs)
    for table_name, field_name in sorted(expected - actual):
        errors.append(f"字段字典缺少: {table_name}.{field_name}")
    for table_name, field_name in sorted(actual - expected):
        errors.append(f"字段字典存在未登记字段: {table_name}.{field_name}")

    allowed_population = {
        "always",
        "common",
        "class_conditional_common",
        "rare_but_critical",
        "review_stage_only",
    }
    for row_number, row in enumerate(rows, start=2):
        if not row.get("description_cn"):
            errors.append(f"field_dictionary:{row_number}: description_cn 为空")
        if row.get("population_expectation") not in allowed_population:
            errors.append(
                f"field_dictionary:{row_number}: population_expectation 非法"
            )
        if not row.get("inclusion_rationale"):
            errors.append(f"field_dictionary:{row_number}: inclusion_rationale 为空")


def validate(
    data_dir: Path,
    schema_path: Path,
    dictionary_path: Path,
    review_policy_path: Path = DEFAULT_REVIEW_POLICY,
    *,
    combined: bool = False,
) -> int:
    schema = read_schema(schema_path)
    review_policy = read_schema(review_policy_path)
    errors: list[str] = []
    warnings: list[str] = []
    loaded: dict[str, list[dict[str, str]]] = {}

    validate_dictionary(schema, dictionary_path, errors)

    for table_name, spec in schema["tables"].items():
        expected = spec["columns"]
        undeclared_required = [
            field for field in spec.get("required_fields", []) if field not in expected
        ]
        if undeclared_required:
            errors.append(
                f"{table_name}: required_fields 含未定义字段 "
                + ", ".join(undeclared_required)
            )

        path = data_dir / spec["filename"]
        if not path.is_file():
            errors.append(f"{table_name}: 缺少文件 {path.name}")
            continue

        headers, rows = read_csv(path)
        loaded[table_name] = rows
        if headers != expected:
            missing = [field for field in expected if field not in headers]
            extra = [field for field in headers if field not in expected]
            if missing:
                errors.append(f"{table_name}: 缺少字段 {', '.join(missing)}")
            if extra:
                errors.append(f"{table_name}: 未登记字段 {', '.join(extra)}")
            if not missing and not extra:
                errors.append(f"{table_name}: 字段顺序与 schema 不一致")

        identity = spec["row_identity"]
        identity_values: list[tuple[str, ...]] = []
        for row_number, row in enumerate(rows, start=2):
            identity_key = tuple(row.get(field, "") for field in identity)
            if not all(identity_key):
                errors.append(
                    f"{table_name}:{row_number}: 行标识不完整 ({', '.join(identity)})"
                )
            else:
                identity_values.append(identity_key)

            for field in spec.get("required_fields", []):
                if not row.get(field, ""):
                    errors.append(f"{table_name}:{row_number}: 必填字段 {field} 为空")

        for key, count in Counter(identity_values).items():
            if count > 1:
                errors.append(f"{table_name}: 重复行标识 {key}")

    # Generic foreign keys declared in the schema.
    for table_name, spec in schema["tables"].items():
        rows = loaded.get(table_name, [])
        for foreign_key in spec.get("foreign_keys", []):
            ref_table, ref_column = foreign_key["references"].split(".", 1)
            reference_values = {
                row.get(ref_column, "") for row in loaded.get(ref_table, [])
            }
            for row_number, row in enumerate(rows, start=2):
                value = row.get(foreign_key["column"], "")
                if value in NULL_SENTINELS and foreign_key.get("nullable"):
                    continue
                if value not in reference_values:
                    errors.append(
                        f"{table_name}:{row_number}: {foreign_key['column']}={value!r} "
                        f"在 {foreign_key['references']} 中不存在"
                    )

    source_master_rows = loaded.get("source_master", [])
    if not combined and len(source_master_rows) != 1:
        errors.append(
            f"source_master: 单篇复核包应有且仅有 1 行，当前为 {len(source_master_rows)} 行"
        )

    source_ids = {row.get("source_id", "") for row in source_master_rows}
    run_source_ids = {row.get("source_id", "") for row in loaded.get("source_run", [])}
    if source_ids and run_source_ids - source_ids:
        errors.append("source_run: 存在不属于本 source_master 的 source_id")

    first_pass_review_status = review_policy["first_pass"]["review_status"]
    formalization = review_policy["formalization"]
    formal_review_status = formalization["review_status"]
    legacy_review_statuses = set(review_policy.get("legacy_review_statuses", []))
    allowed_review_statuses = {
        first_pass_review_status,
        "in_review",
        formal_review_status,
        *legacy_review_statuses,
    }
    blocking_issue_severities = set(formalization["blocking_issue_severities"])
    formal_source_ids: set[str] = set()
    master_extraction_statuses: dict[str, str] = {}

    for row_number, row in enumerate(source_master_rows, start=2):
        extraction_status = row.get("extraction_status", "")
        review_status = row.get("review_status", "")
        source_id = row.get("source_id", "")
        master_extraction_statuses[source_id] = extraction_status
        if extraction_status not in {"needs_review", "reviewed"}:
            errors.append(
                f"source_master:{row_number}: extraction_status={extraction_status!r} 非法"
            )
        if review_status not in allowed_review_statuses:
            errors.append(
                f"source_master:{row_number}: review_status={review_status!r} 非法"
            )
        if review_status in legacy_review_statuses:
            warnings.append(
                f"source_master:{row_number}: review_status={review_status!r} 为历史值；新数据使用 {first_pass_review_status!r}"
            )
        if (extraction_status == "reviewed") != (review_status == formal_review_status):
            errors.append(
                f"source_master:{row_number}: extraction_status 与 review_status 的 reviewed 状态不一致"
            )
        if (
            row.get("screening_class") == formalization["screening_class"]
            and extraction_status == formalization["extraction_status"]
            and review_status == formal_review_status
        ):
            formal_source_ids.add(source_id)

    for row_number, row in enumerate(loaded.get("source_run", []), start=2):
        status = row.get("extraction_status", "")
        if status not in {"needs_review", "reviewed"}:
            errors.append(f"source_run:{row_number}: extraction_status={status!r} 非法")
        source_id = row.get("source_id", "")
        master_status = master_extraction_statuses.get(source_id, "")
        if master_status and status != master_status:
            errors.append(
                f"source_run:{row_number}: extraction_status={status!r} 与 source_master 不一致"
            )

    # Evidence target validation and row-level evidence coverage.
    target_keys = {
        table_name: build_target_keys(table_name, loaded.get(table_name, []))
        for table_name in FACT_TABLES
    }
    evidence_rows = loaded.get("evidence_index", [])
    evidence_ids = {row.get("evidence_id", "") for row in evidence_rows}
    covered: set[tuple[str, str, str]] = set()
    for row_number, row in enumerate(evidence_rows, start=2):
        target_table = row.get("target_table", "")
        if target_table not in FACT_TABLES:
            errors.append(
                f"evidence_index:{row_number}: target_table={target_table!r} 不是事实表"
            )
            continue
        run_id = row.get("run_id", "") or "not_applicable"
        target_record_id = row.get("target_record_id", "")
        if (run_id, target_record_id) not in target_keys[target_table]:
            errors.append(
                f"evidence_index:{row_number}: 目标记录不存在 "
                f"({target_table}, {run_id}, {target_record_id})"
            )
        target_fields = split_ids(row.get("target_fields", ""))
        if target_fields != ["record_level"]:
            unknown_fields = [
                field
                for field in target_fields
                if field not in schema["tables"][target_table]["columns"]
            ]
            if unknown_fields:
                errors.append(
                    f"evidence_index:{row_number}: target_fields 不属于 {target_table}: "
                    + ", ".join(unknown_fields)
                )
        covered.add((target_table, run_id, target_record_id))

    for table_name in EVIDENCE_REQUIRED_TABLES:
        for run_id, target_record_id in target_keys[table_name]:
            if (table_name, run_id, target_record_id) not in covered:
                errors.append(
                    f"{table_name}: 记录 ({run_id}, {target_record_id}) 缺少 evidence_index"
                )

    issue_rows = loaded.get("review_issue_log", [])
    issue_ids = {row.get("issue_id", "") for row in issue_rows}
    allowed_issue_status = allowed_review_statuses
    for row_number, row in enumerate(issue_rows, start=2):
        review_status = row.get("review_status", "")
        if review_status not in allowed_issue_status:
            errors.append(f"review_issue_log:{row_number}: review_status 非法")
        if review_status in legacy_review_statuses:
            warnings.append(
                f"review_issue_log:{row_number}: review_status={review_status!r} 为历史值；新数据使用 {first_pass_review_status!r}"
            )
        if review_status == formal_review_status:
            for field in ("reviewer", "reviewed_at", "resolution"):
                if row.get(field, "") in NULL_SENTINELS:
                    errors.append(
                        f"review_issue_log:{row_number}: reviewed 问题缺少 {field}"
                    )
        if row.get("source_id", "") in formal_source_ids and review_status != formal_review_status:
            if row.get("severity", "") in blocking_issue_severities:
                errors.append(
                    f"review_issue_log:{row_number}: formal 数据仍有未关闭的 {row.get('severity')} 问题"
                )
            else:
                warnings.append(
                    f"review_issue_log:{row_number}: formal 数据保留未关闭的非阻断问题"
                )
        target_table = row.get("target_table", "")
        target_run_id = row.get("run_id", "") or "not_applicable"
        target_record_id = row.get("target_record_id", "")
        if target_table not in FACT_TABLES:
            errors.append(
                f"review_issue_log:{row_number}: target_table={target_table!r} 不是事实表"
            )
        elif (target_run_id, target_record_id) not in target_keys[target_table]:
            errors.append(
                f"review_issue_log:{row_number}: 目标记录不存在 "
                f"({target_table}, {target_run_id}, {target_record_id})"
            )
        target_field = row.get("target_field", "")
        if (
            target_table in FACT_TABLES
            and target_field != "record_level"
            and target_field not in schema["tables"][target_table]["columns"]
        ):
            errors.append(
                f"review_issue_log:{row_number}: target_field={target_field!r} "
                f"不属于 {target_table}"
            )
        for evidence_id in split_ids(row.get("evidence_ids", "")):
            if evidence_id not in evidence_ids:
                errors.append(
                    f"review_issue_log:{row_number}: evidence_id={evidence_id!r} 不存在"
                )

    for row_number, row in enumerate(evidence_rows, start=2):
        linked_issue_id = row.get("linked_issue_id", "")
        if linked_issue_id not in NULL_SENTINELS and linked_issue_id not in issue_ids:
            errors.append(
                f"evidence_index:{row_number}: linked_issue_id={linked_issue_id!r} 不存在"
            )

    print(f"Schema: {schema_path}")
    print(f"Data:   {data_dir}")
    for table_name in schema["tables"]:
        print(f"  {table_name}: {len(loaded.get(table_name, []))} 行")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print(f"校验失败：{len(errors)} 个错误，{len(warnings)} 个提示。")
        return 1
    print(f"校验通过：0 个错误，{len(warnings)} 个提示。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path, help="包含八张 CSV 的单篇来源目录")
    parser.add_argument(
        "--schema", type=Path, default=DEFAULT_SCHEMA, help="schema.json 路径"
    )
    parser.add_argument(
        "--dictionary",
        type=Path,
        default=DEFAULT_DICTIONARY,
        help="field_dictionary.csv 路径",
    )
    parser.add_argument(
        "--review-policy",
        type=Path,
        default=DEFAULT_REVIEW_POLICY,
        help="review_policy.json 路径",
    )
    parser.add_argument(
        "--combined",
        action="store_true",
        help="validate the multi-source formal dataset instead of a one-source package",
    )
    args = parser.parse_args()
    return validate(
        args.data_dir.resolve(),
        args.schema.resolve(),
        args.dictionary.resolve(),
        args.review_policy.resolve(),
        combined=args.combined,
    )


if __name__ == "__main__":
    sys.exit(main())
