#!/usr/bin/env python3
"""Run batch-level semantic guardrails over A-class eight-table packages."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BATCH_ID = "A_CLASS_208_20260716"
PACKAGE_ROOT = (
    ROOT / "data/interim/eight_table_staging/codex_manual" / BATCH_ID
)
REPORT_PATH = (
    ROOT / "data/interim/extraction_batches" / BATCH_ID / "semantic_audit.json"
)
NULLS = {"", "not_reported", "not_applicable"}
NUMERIC_GROUNDED_FIELDS = {
    "catalyst_system": {
        "metal_ratio_original",
        "BET_surface_area_m2_g",
        "pore_diameter_nm",
        "pore_volume_cm3_g",
    },
    "reactor_process_gas": {
        "catalyst_loading_mass_g",
        "temperature_setpoint_C",
        "holding_time_min",
        "heating_rate_C_min",
        "carbon_source_flow_original",
        "reducing_gas_flow_original",
        "inert_gas_flow_original",
        "cofeed_flow_original",
        "total_flow_original",
        "pressure_original",
    },
    "yield_quality": {
        "yield_original",
        "outer_diameter_mean_nm",
        "outer_diameter_range_nm",
        "inner_diameter_mean_nm",
        "Raman_ratio_value",
        "Raman_laser_wavelength_nm",
        "TGA_carbon_content_wt_percent",
        "purified_product_purity_wt_percent",
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def record_id(table: str, item: dict[str, str]) -> str:
    if table == "catalyst_system":
        return item["catalyst_id"]
    if table == "reactor_process_gas":
        return item["process_stage_id"]
    if table == "yield_quality":
        return item["product_id"]
    if table == "cost_scale_review":
        return item["run_id"]
    raise KeyError(table)


def numeric_tokens(value: str) -> list[str]:
    return re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", value.replace(",", ""))


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


def token_is_grounded(
    field: str, value: str, token: str, evidence_text: str
) -> bool:
    if normalized(token) in evidence_text:
        return True
    number = float(token)
    if field == "holding_time_min" and number % 60 == 0:
        hours = number / 60
        number_words = {
            1: "one",
            2: "two",
            3: "three",
            4: "four",
            5: "five",
            6: "six",
            7: "seven",
            8: "eight",
            9: "nine",
            10: "ten",
            12: "twelve",
            24: "twentyfour",
        }
        hour_forms = {
            normalized(f"{hours:g} h"),
            normalized(f"{hours:g} hour"),
            normalized(f"{hours:g} hours"),
        }
        if hours.is_integer() and int(hours) in number_words:
            word = number_words[int(hours)]
            hour_forms.update({f"{word}hour", f"{word}hours"})
        if any(form in evidence_text for form in hour_forms):
            return True
    if field == "catalyst_loading_mass_g":
        milligrams = number * 1000
        if normalized(f"{milligrams:g} mg") in evidence_text:
            return True
    return False


def main() -> None:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    global_run_ids: list[str] = []
    package_summaries: list[dict[str, object]] = []

    for package in sorted(path for path in PACKAGE_ROOT.iterdir() if path.is_dir()):
        tables = {
            name: read_csv(package / f"{name}.csv")
            for name in (
                "source_run",
                "catalyst_system",
                "reactor_process_gas",
                "yield_quality",
                "cost_scale_review",
                "evidence_index",
            )
        }
        run_ids = [item["run_id"] for item in tables["source_run"]]
        global_run_ids.extend(run_ids)
        if len(run_ids) != len(set(run_ids)):
            errors.append(
                {
                    "source_id": package.name,
                    "error_code": "duplicate_run_candidate_id",
                    "detail": "Duplicate run_id within source package.",
                }
            )
        for table in ("catalyst_system", "yield_quality", "cost_scale_review"):
            table_runs = [item["run_id"] for item in tables[table]]
            if Counter(table_runs) != Counter(run_ids):
                errors.append(
                    {
                        "source_id": package.name,
                        "error_code": "run_split_failure",
                        "detail": f"{table} does not have exactly one row per run.",
                    }
                )

        evidence_by_target: dict[tuple[str, str], list[dict[str, str]]] = {}
        for item in tables["evidence_index"]:
            evidence_by_target.setdefault(
                (item["target_table"], item["target_record_id"]), []
            ).append(item)

        for table, fields in NUMERIC_GROUNDED_FIELDS.items():
            for item in tables[table]:
                target = record_id(table, item)
                evidence = evidence_by_target.get((table, target), [])
                for field in fields:
                    value = item.get(field, "").strip()
                    if value in NULLS:
                        continue
                    tokens = numeric_tokens(value)
                    if not tokens:
                        continue
                    applicable = [
                        entry
                        for entry in evidence
                        if entry["target_fields"] == "record_level"
                        or field in {
                            part.strip()
                            for part in entry["target_fields"].split(";")
                        }
                    ]
                    if not applicable:
                        errors.append(
                            {
                                "source_id": package.name,
                                "error_code": "evidence_value_not_grounded",
                                "detail": f"{table}.{field}={value!r} has no field-linked evidence.",
                            }
                        )
                        continue
                    evidence_text = normalized(
                        " ".join(entry["evidence_text"] for entry in applicable)
                    )
                    missing = [
                        token
                        for token in tokens
                        if not token_is_grounded(
                            field, value, token, evidence_text
                        )
                    ]
                    if missing:
                        errors.append(
                            {
                                "source_id": package.name,
                                "error_code": "evidence_value_not_grounded",
                                "detail": (
                                    f"{table}.{field}={value!r} numeric token(s) "
                                    f"{missing} absent from linked evidence."
                                ),
                            }
                        )

        for item in tables["catalyst_system"]:
            if (
                item["catalyst_particle_size_mean_nm"] not in NULLS
                or item["catalyst_particle_size_range_nm"] not in NULLS
            ):
                warnings.append(
                    {
                        "source_id": package.name,
                        "warning_code": "catalyst_particle_size_requires_context_review",
                        "detail": item["run_id"],
                    }
                )

        package_summaries.append(
            {
                "source_id": package.name,
                "run_count": len(run_ids),
                "evidence_count": len(tables["evidence_index"]),
            }
        )

    duplicates = [
        run_id for run_id, count in Counter(global_run_ids).items() if count > 1
    ]
    if duplicates:
        errors.append(
            {
                "source_id": "batch",
                "error_code": "duplicate_run_candidate_id",
                "detail": ";".join(duplicates),
            }
        )

    report = {
        "batch_id": BATCH_ID,
        "package_count": len(package_summaries),
        "run_count": len(global_run_ids),
        "duplicate_run_id_count": len(duplicates),
        "packages": package_summaries,
        "errors": errors,
        "warnings": warnings,
        "status": "passed" if not errors else "failed",
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
