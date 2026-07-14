#!/usr/bin/env python3
"""Validate CNT-PatSight five-table CSV collections against config/schema.json."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA = PROJECT_ROOT / "config" / "schema.json"


def read_schema(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        rows = [
            {key: (value or "").strip() for key, value in row.items() if key is not None}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]
    return headers, rows


def validate(data_dir: Path, schema_path: Path) -> int:
    schema = read_schema(schema_path)
    errors: list[str] = []
    warnings: list[str] = []
    loaded: dict[str, list[dict[str, str]]] = {}

    for table_name, spec in schema["tables"].items():
        expected = spec["columns"]
        recommended_fields = spec.get("v1_recommended_fields", [])
        unknown_recommended = [column for column in recommended_fields if column not in expected]
        if unknown_recommended:
            errors.append(
                f"{table_name}: v1_recommended_fields 包含未定义字段 {', '.join(unknown_recommended)}"
            )
        if len(recommended_fields) != len(set(recommended_fields)):
            errors.append(f"{table_name}: v1_recommended_fields 存在重复字段")

        path = data_dir / spec["filename"]
        if not path.is_file():
            errors.append(f"{table_name}: 缺少文件 {path}")
            continue

        headers, rows = read_csv(path)
        if headers != expected:
            missing = [column for column in expected if column not in headers]
            extra = [column for column in headers if column not in expected]
            if missing:
                errors.append(f"{table_name}: 缺少字段 {', '.join(missing)}")
            if extra:
                errors.append(f"{table_name}: 未登记字段 {', '.join(extra)}")
            if not missing and not extra:
                errors.append(f"{table_name}: 字段顺序与 schema 不一致")

        loaded[table_name] = rows
        identity = spec["row_identity"]
        keys: list[tuple[str, ...]] = []
        for row_number, row in enumerate(rows, start=2):
            key = tuple(row.get(column, "") for column in identity)
            if not all(key):
                warnings.append(
                    f"{table_name}:{row_number}: 行标识不完整 ({', '.join(identity)})"
                )
            else:
                keys.append(key)
        duplicates = [key for key, count in Counter(keys).items() if count > 1]
        for key in duplicates:
            errors.append(f"{table_name}: 重复行标识 {key}")

    source_ids = {
        row.get("run_id", "")
        for row in loaded.get("source_run", [])
        if row.get("run_id", "")
    }
    for table_name, rows in loaded.items():
        if table_name == "source_run":
            continue
        for row_number, row in enumerate(rows, start=2):
            run_id = row.get("run_id", "")
            if run_id and run_id not in source_ids:
                errors.append(
                    f"{table_name}:{row_number}: run_id={run_id!r} 在 source_run 中不存在"
                )

    print(f"Schema: {schema_path}")
    print(f"Data:   {data_dir}")
    for table_name in schema["tables"]:
        print(f"  {table_name}: {len(loaded.get(table_name, []))} 条数据行")
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
    parser.add_argument("data_dir", type=Path, help="包含五张 CSV 的目录")
    parser.add_argument(
        "--schema", type=Path, default=DEFAULT_SCHEMA, help="schema.json 路径"
    )
    args = parser.parse_args()
    return validate(args.data_dir.resolve(), args.schema.resolve())


if __name__ == "__main__":
    sys.exit(main())
