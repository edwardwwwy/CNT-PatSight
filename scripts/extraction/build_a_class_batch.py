#!/usr/bin/env python3
"""Build the A-class extraction inventory and the first evidence-grounded batch.

This script makes no external model calls.  The first batch is a manual Codex
transcription from locally parsed full text and candidate spans.  Every output
remains ``needs_review``.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BATCH_ID = "A_CLASS_208_20260716"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
PACKAGE_ROOT = ROOT / "data/interim/eight_table_staging/codex_manual" / BATCH_ID
META_DB = ROOT / "data/raw/metadata/snapshots/screening_rules_v1.2/literature.sqlite3"
FULLTEXT_DB = ROOT / "data/raw/fulltext/fulltext.sqlite3"
CANDIDATE_DB = ROOT / "data/interim/extraction_candidates/extraction_candidates.sqlite3"
SCHEMA_PATH = ROOT / "config/schema.json"
MANUAL_DISPOSITIONS_PATH = BATCH_ROOT / "manual_dispositions.csv"

TABLES = (
    "source_master",
    "source_run",
    "catalyst_system",
    "reactor_process_gas",
    "yield_quality",
    "cost_scale_review",
    "evidence_index",
    "review_issue_log",
)

FIRST_BATCH_IDS = (
    "LIT_0705FD92BBA5C6D2",
    "LIT_B737792873D4A97E",
    "LIT_3D2FAA624663FA97",
    "LIT_6C1D6D8880AEB493",
    "LIT_849AD7FB325763D1",
)


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


SCHEMA = load_schema()


def row(table: str, **values: Any) -> dict[str, str]:
    output = {name: "" for name in SCHEMA["tables"][table]["columns"]}
    for name, value in values.items():
        if name not in output:
            raise KeyError(f"{name!r} is not a {table} field")
        output[name] = "" if value is None else str(value)
    return output


def write_table(path: Path, table: str, rows: list[dict[str, str]]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    with (path / f"{table}.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCHEMA["tables"][table]["columns"])
        writer.writeheader()
        writer.writerows(rows)


def load_metadata() -> dict[str, dict[str, Any]]:
    connection = sqlite3.connect(META_DB)
    connection.row_factory = sqlite3.Row
    result = {
        item["source_id"]: dict(item)
        for item in connection.execute("SELECT * FROM works WHERE priority_tier = 'A'")
    }
    connection.close()
    return result


def load_parse_status() -> dict[str, dict[str, Any]]:
    connection = sqlite3.connect(CANDIDATE_DB)
    connection.row_factory = sqlite3.Row
    result = {
        item["source_id"]: dict(item)
        for item in connection.execute("SELECT * FROM parse_source_status")
    }
    connection.close()
    return result


def load_queue_status() -> dict[str, dict[str, Any]]:
    connection = sqlite3.connect(FULLTEXT_DB)
    connection.row_factory = sqlite3.Row
    result = {
        item["source_id"]: dict(item)
        for item in connection.execute("SELECT * FROM fulltext_acquisition_queue")
    }
    connection.close()
    return result


def load_manual_dispositions() -> dict[str, dict[str, str]]:
    if not MANUAL_DISPOSITIONS_PATH.exists():
        return {}
    with MANUAL_DISPOSITIONS_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return {
            item["source_id"]: item
            for item in csv.DictReader(handle)
            if item.get("source_id")
        }


def existing_manual_source_ids() -> set[str]:
    result: set[str] = set()
    root = ROOT / "data/interim/eight_table_staging/codex_manual"
    if not root.exists():
        return result
    for path in root.rglob("source_master.csv"):
        try:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                first = next(csv.DictReader(handle), None)
            if first and first.get("source_id"):
                result.add(first["source_id"])
        except (OSError, UnicodeError):
            continue
    return result


def has_direct_package(source_id: str) -> bool:
    package = ROOT / "data/interim" / source_id
    return all((package / f"{table}.csv").exists() for table in TABLES)


def build_inventory() -> dict[str, Any]:
    metadata = load_metadata()
    parse_status = load_parse_status()
    queue_status = load_queue_status()
    manual_dispositions = load_manual_dispositions()
    manual_ids = existing_manual_source_ids()
    records: list[dict[str, Any]] = []

    for source_id, work in metadata.items():
        parsed = parse_status.get(source_id, {})
        queued = queue_status.get(source_id, {})
        disposition = manual_dispositions.get(source_id, {})
        if disposition:
            extraction_state = disposition["extraction_state"]
            extraction_reason = disposition.get("reason", "")
        elif source_id in FIRST_BATCH_IDS:
            extraction_state = "batch_001_completed_needs_review"
            extraction_reason = "completed in initial manual batch"
        elif has_direct_package(source_id):
            extraction_state = "existing_curated_package"
            extraction_reason = "pre-existing project-native curated package"
        elif source_id in manual_ids:
            extraction_state = "existing_manual_package_needs_review"
            extraction_reason = "manual eight-table package exists"
        elif parsed.get("candidate_extract_eligible") == 1:
            extraction_state = "ready_for_extraction"
            extraction_reason = "parsed candidate spans await disposition"
        elif parsed.get("parse_status") == "success":
            extraction_state = "parsed_not_extractable"
            extraction_reason = (
                parsed.get("failure_reason")
                or "parser found no extractable CNT-production evidence"
            )
        else:
            extraction_state = "fulltext_or_parse_unavailable"
            extraction_reason = (
                parsed.get("failure_reason")
                or queued.get("failure_reason")
                or "full text or successful parse unavailable"
            )

        records.append(
            {
                "source_id": source_id,
                "title": work.get("title", ""),
                "year": work.get("year", ""),
                "doi": work.get("doi", ""),
                "priority_tier": work.get("priority_tier", ""),
                "metadata_pipeline_status": work.get("pipeline_status", ""),
                "download_status": queued.get("download_status", ""),
                "parse_status": parsed.get("parse_status", ""),
                "parse_quality": parsed.get("parse_quality", ""),
                "candidate_extract_eligible": parsed.get(
                    "candidate_extract_eligible", ""
                ),
                "extracted_char_count": parsed.get("extracted_char_count", ""),
                "candidate_span_count": parsed.get("span_count", ""),
                "extraction_state": extraction_state,
                "extraction_reason": extraction_reason,
            }
        )

    records.sort(
        key=lambda item: (
            {
                "existing_curated_package": 0,
                "existing_manual_package_needs_review": 1,
                "batch_001_completed_needs_review": 2,
                "ready_for_extraction": 3,
                "parsed_not_extractable": 4,
                "fulltext_or_parse_unavailable": 5,
            }[item["extraction_state"]],
            -(int(item["candidate_span_count"] or 0)),
            item["source_id"],
        )
    )
    BATCH_ROOT.mkdir(parents=True, exist_ok=True)
    with (BATCH_ROOT / "manifest.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    state_counts = Counter(item["extraction_state"] for item in records)
    download_counts = Counter(
        item["download_status"] or "not_queued" for item in records
    )
    summary = {
        "batch_id": BATCH_ID,
        "priority_tier": "A",
        "total_sources": len(records),
        "state_counts": dict(sorted(state_counts.items())),
        "download_status_counts": dict(sorted(download_counts.items())),
        "first_batch_source_ids": list(FIRST_BATCH_IDS),
        "automated_model_used": False,
        "status": "in_progress",
    }
    (BATCH_ROOT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


class EvidenceStore:
    def __init__(self) -> None:
        self.connection = sqlite3.connect(CANDIDATE_DB)
        self.connection.row_factory = sqlite3.Row

    def close(self) -> None:
        self.connection.close()

    def span(self, source_id: str, span_id: str) -> dict[str, Any]:
        item = self.connection.execute(
            """
            SELECT s.*, p.section_name_raw, p.section_name_normalized
            FROM candidate_experiment_span AS s
            LEFT JOIN paper_text_section AS p ON p.section_id = s.section_id
            WHERE s.source_id = ? AND s.span_id = ?
            """,
            (source_id, span_id),
        ).fetchone()
        if item is None:
            raise KeyError(f"Missing candidate span {source_id}/{span_id}")
        return dict(item)


def master_row(meta: dict[str, Any], scope: str) -> dict[str, str]:
    return row(
        "source_master",
        source_id=meta["source_id"],
        source_type="paper",
        source_title=meta["title"],
        publication_year=meta["year"],
        authors_or_assignee=meta["authors"],
        publication_venue=meta["journal"],
        doi_or_patent_no=meta["doi"] or "not_reported",
        source_link=meta["source_link"] or "not_reported",
        source_database="local_metadata_snapshot",
        source_language=meta["language"] or "en",
        local_file_path=(f"data/interim/parsed_text/{meta['source_id']}.txt"),
        pdf_status=meta["pdf_status"] or "legal_url_found",
        screening_class="candidate_extract",
        source_section_scope=scope,
        extraction_status="needs_review",
        review_status="pending_human_review",
        notes=(
            f"Codex manual first pass for {BATCH_ID}; locally parsed evidence "
            "only; domain_expert_verified=false."
        ),
    )


def run_row(
    source_id: str, code: str, label: str, summary: str, confidence: str = "high"
) -> dict[str, str]:
    return row(
        "source_run",
        run_id=f"{source_id}_{code}",
        source_id=source_id,
        run_label=label,
        data_type="experimental_run",
        target_track="CNT_production",
        relevance_class="candidate_extract",
        extraction_status="needs_review",
        extraction_confidence=confidence,
        run_summary=summary,
        notes="First-pass structured transcription; human verification required.",
    )


def catalyst_row(run_id: str, **values: Any) -> dict[str, str]:
    defaults = {
        "run_id": run_id,
        "catalyst_id": f"{run_id}_CAT",
        "activation_condition": "not_reported",
        "post_preparation_condition": "fresh catalyst",
        "notes": "CNT dimensions are not mapped to catalyst-particle fields.",
    }
    defaults.update(values)
    return row("catalyst_system", **defaults)


def process_row(
    run_id: str, order: int, stage_type: str, **values: Any
) -> dict[str, str]:
    defaults = {
        "run_id": run_id,
        "process_stage_id": f"{run_id}_S{order:02d}",
        "stage_order": order,
        "stage_type": stage_type,
        "scale_level": "lab_batch",
        "pressure_original": "atmospheric",
        "pressure_kPa": "101.325",
        "process_note": "Reported process stage; first-pass needs_review.",
    }
    defaults.update(values)
    return row("reactor_process_gas", **defaults)


def yield_row(run_id: str, **values: Any) -> dict[str, str]:
    defaults = {
        "run_id": run_id,
        "product_id": f"{run_id}_PROD",
        "CNT_type_confirmed": "not_applicable",
        "yield_standardization_note": "No cross-definition conversion performed.",
        "notes": "Reported identity and basis retained; needs human verification.",
    }
    defaults.update(values)
    return row("yield_quality", **defaults)


def cost_row(run_id: str, **values: Any) -> dict[str, str]:
    defaults = {
        "run_id": run_id,
        "scale_level_demonstrated": "lab_batch",
        "scale_level_claimed": "not_reported",
        "scale_evidence_summary": "Laboratory reactor experiment.",
        "quantitative_cost_reported": "not_reported",
        "quantitative_cost_summary": "not_reported",
        "safety_risk": "not_reported",
        "emission_or_waste": "not_reported",
        "review_note": "No human industrial-readiness assessment entered.",
    }
    defaults.update(values)
    return row("cost_scale_review", **defaults)


def evidence_row(
    store: EvidenceStore,
    source_id: str,
    evidence_id: str,
    run_id: str,
    table: str,
    record_id: str,
    fields: str,
    span_id: str,
    summary: str,
    confidence: str = "high",
    value_status: str = "reported",
) -> dict[str, str]:
    span = store.span(source_id, span_id)
    return row(
        "evidence_index",
        evidence_id=evidence_id,
        source_id=source_id,
        run_id=run_id,
        target_table=table,
        target_record_id=record_id,
        target_fields=fields,
        evidence_type="record_support",
        value_status=value_status,
        source_section=(
            span.get("section_name_raw")
            or span.get("section_name_normalized")
            or "parsed_text"
        ),
        source_locator=span.get("page_range") or "local_span",
        source_object_ref=span_id,
        evidence_text=" ".join(span["text"].split()),
        evidence_summary=summary,
        confidence=confidence,
        linked_issue_id="not_applicable",
        notes="Evidence copied from immutable local candidate span.",
    )


def issue_row(
    issue_id: str,
    source_id: str,
    run_id: str,
    issue_type: str,
    table: str,
    record_id: str,
    field: str,
    summary: str,
    evidence_ids: str,
    severity: str = "medium",
) -> dict[str, str]:
    return row(
        "review_issue_log",
        issue_id=issue_id,
        source_id=source_id,
        run_id=run_id,
        issue_type=issue_type,
        target_table=table,
        target_record_id=record_id,
        target_field=field,
        issue_summary=summary,
        evidence_ids=evidence_ids,
        severity=severity,
        review_status="pending_human_review",
        notes="Resolve before promotion to reviewed/formal data.",
    )


def build_0705(
    meta: dict[str, Any], store: EvidenceStore
) -> dict[str, list[dict[str, str]]]:
    source_id = meta["source_id"]
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            meta,
            "Experimental catalyst preparation; benzene CVD conditions; SEM/Raman results.",
        )
    )
    configs = [
        {
            "code": "R01",
            "label": "Fe@Al2O3 spheres / benzene / 830 C",
            "metal": "Fe",
            "catalyst_label": "Fe@Al2O3 spheres",
            "precursor": "ferrocene in 95% ethanol",
            "method": "impregnation",
            "detail": "Al2O3 spheres impregnated with saturated ferrocene solution in 95% ethanol and dried.",
            "temp": "830",
            "cnt": "CNTs",
            "diameter": "27-135",
            "raman": "0.65",
            "mixture": "CNTs with a small reported amorphous-carbon fraction; helical one-dimensional structures also present.",
            "cat_span": "SPAN_9E136DF8246295B3E41C",
            "result_span": "SPAN_0AD3A6B54B7DE2D888A3",
            "raman_span": "SPAN_2C15C655461F3B67DE8E",
        },
        {
            "code": "R02",
            "label": "Ni/NiO@Al2O3 spheres / benzene / 850 C",
            "metal": "Ni",
            "catalyst_label": "Ni/NiO@Al2O3 spheres",
            "precursor": "nickel nitrate and citric acid",
            "method": "solution combustion after impregnation",
            "detail": "Al2O3 spheres impregnated with nickel nitrate/citric acid solution, dried at 100 C and heat-treated in N2; product reported as 85% Ni and 15% NiO.",
            "temp": "850",
            "cnt": "MWCNTs",
            "diameter": "40-120",
            "raman": "0.78",
            "mixture": "MWCNT product at 850 C; graphene-like carbon frameworks form above 850 C.",
            "cat_span": "SPAN_0872A0C1D6A96817FEE4",
            "result_span": "SPAN_31DE1ED172F2D765DE80",
            "raman_span": "SPAN_2C15C655461F3B67DE8E",
        },
    ]
    for config in configs:
        run_id = f"{source_id}_{config['code']}"
        tables["source_run"].append(
            run_row(
                source_id,
                config["code"],
                config["label"],
                f"{config['catalyst_label']}; benzene carried by N2; {config['temp']} C.",
            )
        )
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                catalyst_label=config["catalyst_label"],
                active_metals=config["metal"],
                support_material="Al2O3 spheres",
                precursor_summary=config["precursor"],
                preparation_method=config["method"],
                preparation_modifier="not_reported",
                preparation_detail=config["detail"],
                drying_condition="reported in catalyst-preparation evidence",
                calcination_condition="not_reported",
                reduction_condition="in situ precursor decomposition during CNT synthesis",
                BET_surface_area_m2_g="248" if config["metal"] == "Fe" else "",
                pore_volume_cm3_g="0.106" if config["metal"] == "Fe" else "",
            )
        )
        tables["reactor_process_gas"].append(
            process_row(
                run_id,
                1,
                "growth",
                reactor_type="vertical CVD fluidised-bed reactor",
                reactor_material="not_reported",
                reactor_setup_summary="N2 passes through a benzene bubbler and carries benzene into the reactor.",
                temperature_setpoint_C=config["temp"],
                temperature_program_summary="Temperature screened from 750 to 860 C; optimum recorded for this catalyst.",
                carbon_source="benzene",
                carbon_source_flow_original="benzene vapour carried by N2",
                inert_gas="N2",
                inert_gas_flow_original="650-700 cm3/min",
                inert_gas_flow_sccm="650-700",
                gas_composition_summary="benzene vapour in nitrogen",
                pressure_original="not_reported",
                pressure_kPa="",
            )
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="not_reported",
                yield_original="not_reported",
                yield_definition_original="not_reported",
                secondary_result_summary=config["mixture"],
                CNT_type_reported=config["cnt"],
                product_mixture_summary=config["mixture"],
                CNT_type_evidence="SEM and Raman evidence.",
                outer_diameter_range_nm=config["diameter"],
                morphology="helical structures reported for Fe run"
                if config["metal"] == "Fe"
                else "multi-walled nanotubes",
                Raman_ratio_type="ID/IG",
                Raman_ratio_value=config["raman"],
                characterization_methods="SEM; Raman spectroscopy",
                amorphous_carbon_level="small"
                if config["metal"] == "Fe"
                else "present/relatively higher defectiveness",
            )
        )
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                reactor_capacity_or_throughput="not_reported",
                cost_driver_summary="not_reported",
            )
        )
        evidence_specs = [
            (
                "CAT",
                "catalyst_system",
                f"{run_id}_CAT",
                "catalyst_label;active_metals;support_material;precursor_summary;preparation_method;BET_surface_area_m2_g;pore_volume_cm3_g"
                if config["metal"] == "Fe"
                else "catalyst_label;active_metals;support_material;precursor_summary;preparation_method",
                config["cat_span"],
                "Catalyst identity, preparation and support properties.",
            ),
            (
                "PROC_GAS",
                "reactor_process_gas",
                f"{run_id}_S01",
                "reactor_type;carbon_source",
                "SPAN_51E68817EA74A7F1E218",
                "Benzene delivery through a nitrogen bubbler.",
            ),
            (
                "PROC_FLOW",
                "reactor_process_gas",
                f"{run_id}_S01",
                "inert_gas;inert_gas_flow_original",
                "SPAN_31DE1ED172F2D765DE80",
                "Reported optimum nitrogen flow range.",
            ),
            (
                "PROC_TEMP",
                "reactor_process_gas",
                f"{run_id}_S01",
                "temperature_setpoint_C",
                config["result_span"],
                "Catalyst-specific optimum synthesis temperature.",
            ),
            (
                "YIELD",
                "yield_quality",
                f"{run_id}_PROD",
                "CNT_type_reported;outer_diameter_range_nm;product_mixture_summary",
                config["result_span"],
                "Product identity, dimensions and mixture description.",
            ),
            (
                "RAMAN",
                "yield_quality",
                f"{run_id}_PROD",
                "Raman_ratio_type;Raman_ratio_value",
                config["raman_span"],
                "Reported ID/IG Raman ratio.",
            ),
            (
                "COST",
                "cost_scale_review",
                run_id,
                "scale_level_demonstrated;reactor_capacity_or_throughput",
                "SPAN_7EFB4625B64E00F02D17",
                "Laboratory vertical CVD apparatus.",
            ),
        ]
        for suffix, table, record_id, fields, span_id, summary in evidence_specs:
            tables["evidence_index"].append(
                evidence_row(
                    store,
                    source_id,
                    f"EVD_{run_id}_{suffix}",
                    run_id,
                    table,
                    record_id,
                    fields,
                    span_id,
                    summary,
                )
            )
    first_run = f"{source_id}_R01"
    tables["review_issue_log"].append(
        issue_row(
            f"{source_id}_ISSUE_REACTOR_001",
            source_id,
            first_run,
            "source_conflict",
            "reactor_process_gas",
            f"{first_run}_S01",
            "reactor_type",
            "The paper calls the system a fluidised-bed reactor, while the experimental figure is labelled a vertical CVD setup; the local text does not quantify fluidisation.",
            f"EVD_{first_run}_PROC_GAS;EVD_{first_run}_COST",
        )
    )
    return tables


def build_b737(
    meta: dict[str, Any], store: EvidenceStore
) -> dict[str, list[dict[str, str]]]:
    source_id = meta["source_id"]
    run_id = f"{source_id}_R01"
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            meta,
            "Catalyst preparation; three-zone CVD process; SEM/Raman product results.",
        )
    )
    tables["source_run"].append(
        run_row(
            source_id,
            "R01",
            "Fe@cenosphere / HDPE waste / 450-to-800 C",
            "HDPE waste pyrolysis vapours converted to CNTs on Fe-impregnated cenospheres in a three-zone reactor.",
        )
    )
    tables["catalyst_system"].append(
        catalyst_row(
            run_id,
            catalyst_label="Fe@P'100/500 cenospheres",
            active_metals="Fe",
            support_material="P'100/500 cenospheres (Si/Al oxide-rich)",
            precursor_summary="100 g/L aqueous iron nitrate nonahydrate",
            preparation_method="impregnation",
            preparation_modifier="drying",
            preparation_detail="10 g cenospheres impregnated with aqueous iron nitrate solution.",
            drying_condition="70 C for 2-3 h until moisture removal",
            calcination_condition="not_reported",
            reduction_condition="in situ iron-nitrate decomposition during synthesis",
        )
    )
    tables["reactor_process_gas"].extend(
        [
            process_row(
                run_id,
                1,
                "feed_generation",
                reactor_type="three-zone CVD reactor",
                reactor_material="quartz tube",
                reactor_size_summary="6 cm inner diameter; 120.7 cm length",
                reactor_setup_summary="4 g HDPE in the first zone; second zone at 700 C; catalyst in third zone.",
                temperature_setpoint_C="450",
                temperature_program_summary="HDPE decomposed at 450 C after screening 450-550 C.",
                holding_time_min="30",
                carbon_source="household HDPE waste pyrolysis vapours",
                inert_gas="N2",
                inert_gas_flow_original="530-540 cm3/min",
                inert_gas_flow_sccm="530-540",
                gas_composition_summary="HDPE pyrolysis products transported by 99.9% N2",
                pressure_original="not_reported",
                pressure_kPa="",
            ),
            process_row(
                run_id,
                2,
                "growth",
                reactor_type="three-zone CVD reactor",
                reactor_material="quartz tube",
                reactor_setup_summary="1 g catalyst in the third zone; intermediate zone at 700 C.",
                catalyst_loading_mass_g="1",
                temperature_setpoint_C="800",
                temperature_program_summary="CNT growth on catalyst at 800 C while HDPE decomposed at 450 C.",
                holding_time_min="30",
                carbon_source="household HDPE waste pyrolysis vapours",
                inert_gas="N2",
                inert_gas_flow_original="530-540 cm3/min",
                inert_gas_flow_sccm="530-540",
                gas_composition_summary="HDPE pyrolysis products transported by 99.9% N2",
                pressure_original="not_reported",
                pressure_kPa="",
            ),
        ]
    )
    tables["yield_quality"].append(
        yield_row(
            run_id,
            primary_yield_metric="not_reported",
            yield_original="not_reported",
            yield_definition_original="not_reported",
            secondary_result_summary="High-quality CNT coating reported; amorphous/turbostratic carbon almost absent.",
            CNT_type_reported="MWCNTs",
            product_mixture_summary="CNT coating on cenospheres; amorphous/turbostratic carbon reported as almost absent.",
            CNT_type_evidence="Raman bands described as characteristic of MWCNTs.",
            outer_diameter_range_nm="16-21",
            morphology="CNT coating on cenosphere surface",
            Raman_ratio_type="ID/IG",
            Raman_ratio_value="0.55",
            amorphous_carbon_level="almost absent",
            characterization_methods="SEM; Raman spectroscopy",
            application_property_summary="CNT-coated cenospheres had a reported water contact angle of 119.3 degrees.",
        )
    )
    tables["cost_scale_review"].append(
        cost_row(
            run_id,
            reactor_capacity_or_throughput="4 g HDPE feed; 1 g catalyst per reported experiment",
            cost_driver_summary="Uses household HDPE waste and power-plant-derived cenospheres; no quantitative cost reported.",
            emission_or_waste="Household HDPE waste used as carbon feed; volatile pyrolysis products generated.",
        )
    )
    evidence_specs = [
        (
            "CAT",
            "catalyst_system",
            f"{run_id}_CAT",
            "catalyst_label;active_metals;support_material;precursor_summary;preparation_method;drying_condition",
            "SPAN_33FEE8BC51CCD4086A9C",
            "Catalyst support, iron-nitrate impregnation and drying.",
        ),
        (
            "PROC1",
            "reactor_process_gas",
            f"{run_id}_S01",
            "reactor_type;reactor_material;reactor_size_summary;temperature_setpoint_C;holding_time_min;carbon_source;inert_gas;inert_gas_flow_original",
            "SPAN_16955D0BF68B2CA873E0",
            "Three-zone process, catalyst loading, temperatures, nitrogen flow and time.",
        ),
        (
            "PROC2",
            "reactor_process_gas",
            f"{run_id}_S02",
            "reactor_type;catalyst_loading_mass_g;temperature_setpoint_C;holding_time_min;carbon_source;inert_gas;inert_gas_flow_original",
            "SPAN_16955D0BF68B2CA873E0",
            "CNT-growth stage in the third reactor zone.",
        ),
        (
            "YIELD",
            "yield_quality",
            f"{run_id}_PROD",
            "CNT_type_reported;outer_diameter_range_nm;Raman_ratio_type;Raman_ratio_value;amorphous_carbon_level",
            "SPAN_4FB97892A109C4D965CA",
            "SEM/Raman product identity, diameter and defect ratio.",
        ),
        (
            "COST",
            "cost_scale_review",
            run_id,
            "scale_level_demonstrated;reactor_capacity_or_throughput;emission_or_waste",
            "SPAN_33FEE8BC51CCD4086A9C",
            "Reported gram-scale feed/catalyst setup and waste-plastic route.",
        ),
    ]
    for suffix, table, record_id, fields, span_id, summary in evidence_specs:
        tables["evidence_index"].append(
            evidence_row(
                store,
                source_id,
                f"EVD_{run_id}_{suffix}",
                run_id,
                table,
                record_id,
                fields,
                span_id,
                summary,
            )
        )
    tables["review_issue_log"].append(
        issue_row(
            f"{source_id}_ISSUE_YIELD_001",
            source_id,
            run_id,
            "critical_data_gap",
            "yield_quality",
            f"{run_id}_PROD",
            "yield_original",
            "The paper gives product morphology and quality but no quantitative CNT yield for the reported optimum run.",
            f"EVD_{run_id}_YIELD",
            "low",
        )
    )
    return tables


def build_3d2(
    meta: dict[str, Any], store: EvidenceStore
) -> dict[str, list[dict[str, str]]]:
    source_id = meta["source_id"]
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            meta,
            "Catalyst precipitation; shared reduction/growth program; Table 1 carbon yields; SEM/TGA purification results.",
        )
    )
    configs = [
        ("R01", "Fe-Ni/gamma-Al2O3", "Fe; Ni", "gamma-Al2O3", "239.1"),
        ("R02", "Fe-Co/gamma-Al2O3", "Fe; Co", "gamma-Al2O3", "263.6"),
        ("R03", "Co-Ni/gamma-Al2O3", "Co; Ni", "gamma-Al2O3", "76.4"),
        ("R04", "Fe-Ni/SiO2", "Fe; Ni", "SiO2 (Kieselgur)", "47.3"),
        ("R05", "Fe-Co/SiO2", "Fe; Co", "SiO2 (Kieselgur)", "61.8"),
        ("R06", "Co-Ni/SiO2", "Co; Ni", "SiO2 (Kieselgur)", "9.1"),
    ]
    for code, label, metals, support, carbon_yield in configs:
        run_id = f"{source_id}_{code}"
        tables["source_run"].append(
            run_row(
                source_id,
                code,
                label,
                f"{label}; ethylene/N2 at 700 C for 1 h; reported carbon yield {carbon_yield}%.",
            )
        )
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                catalyst_label=label,
                active_metals=metals,
                support_material=support,
                metal_ratio_original="equivalent masses of the two metals; total metal loading 5 wt%",
                metal_ratio_standardized="1:1 metal mass ratio; 5 wt% total metal",
                precursor_summary="metal nitrates selected from Fe(NO3)3·9H2O, Co(NO3)2·6H2O and Ni(NO3)2·6H2O",
                preparation_method="precipitation onto support",
                preparation_modifier="ammonia precipitation at pH 8",
                preparation_detail="Metal-nitrate solutions mixed with support for 2 h at room temperature; hydroxides precipitated with ammonia.",
                drying_condition="110 C for 24 h",
                calcination_condition="air at 600 C for 5 h",
                reduction_condition="H2 at 700 C for 2 h before growth",
            )
        )
        tables["reactor_process_gas"].extend(
            [
                process_row(
                    run_id,
                    1,
                    "reduction",
                    reactor_type="horizontal quartz-tube CCVD reactor",
                    reactor_material="quartz",
                    reactor_size_summary="42 mm external diameter; 1 m length",
                    reactor_setup_summary="700 mg catalyst powder in a thin layer in a quartz boat.",
                    catalyst_loading_mass_g="0.7",
                    temperature_setpoint_C="700",
                    holding_time_min="120",
                    reducing_gas="H2",
                    reducing_gas_flow_original="110 mL/min",
                    reducing_gas_flow_sccm="110",
                    total_flow_original="110 mL/min",
                    total_flow_sccm="110",
                ),
                process_row(
                    run_id,
                    2,
                    "growth",
                    reactor_type="horizontal quartz-tube CCVD reactor",
                    reactor_material="quartz",
                    reactor_size_summary="42 mm external diameter; 1 m length",
                    reactor_setup_summary="700 mg reduced catalyst in a quartz boat.",
                    catalyst_loading_mass_g="0.7",
                    temperature_setpoint_C="700",
                    holding_time_min="60",
                    carbon_source="C2H4",
                    carbon_source_flow_original="110 mL/min",
                    carbon_source_flow_sccm="110",
                    inert_gas="N2",
                    inert_gas_flow_original="110 mL/min",
                    inert_gas_flow_sccm="110",
                    total_flow_original="220 mL/min",
                    total_flow_sccm="220",
                    gas_composition_summary="C2H4:N2 = 1:1",
                ),
            ]
        )
        is_feco_alumina = code == "R02"
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="carbon yield relative to reduced catalyst mass",
                yield_original=f"{carbon_yield}%",
                yield_definition_original="100 × (total catalyst plus as-synthesized carbon mass − reduced catalyst mass) / reduced catalyst mass",
                yield_calculation_method="Reported gravimetric formula",
                yield_value_standardized=carbon_yield,
                yield_unit_standardized="% carbon relative to reduced catalyst mass",
                secondary_result_summary="Alumina-supported catalysts produced higher carbon yields than silica-supported counterparts.",
                CNT_type_reported="CNTs",
                product_mixture_summary="As-synthesized carbon-containing product; possible amorphous carbon, graphite nanoparticles and catalyst residue are not excluded by the yield definition.",
                CNT_type_evidence="SEM-based nanotube assignment; authors note SEM cannot conclusively prove tubular structure.",
                outer_diameter_range_nm="20-60",
                morphology="quasi-aligned dense bundles"
                if is_feco_alumina
                else "tangled CNT network",
                alignment_or_array="quasi-aligned bundles"
                if is_feco_alumina
                else "not_reported",
                characterization_methods="SEM; EDS; XRD; DTA/TGA",
                post_treatment_or_purification="liquid oxidation; NaOH then HCl"
                if is_feco_alumina
                else "not_reported",
                purification_condition="1 M NaOH at 80 C for 2 h, water wash, then 1 M HCl; dry at 110 C for 24 h"
                if is_feco_alumina
                else "not_reported",
                notes="Reported carbon yield is not treated as purified CNT purity.",
            )
        )
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                reactor_capacity_or_throughput="700 mg catalyst per reported run",
                cost_driver_summary="not_reported",
            )
        )
        evidence_specs = [
            (
                "CAT",
                "catalyst_system",
                f"{run_id}_CAT",
                "catalyst_label;active_metals;support_material;metal_ratio_original;preparation_method;drying_condition;calcination_condition",
                "SPAN_142155253837FA4E1806",
                "Bimetallic catalyst composition and preparation.",
            ),
            (
                "PROC1",
                "reactor_process_gas",
                f"{run_id}_S01",
                "reactor_type;reactor_size_summary;catalyst_loading_mass_g;temperature_setpoint_C;holding_time_min;reducing_gas;reducing_gas_flow_original;total_flow_original",
                "SPAN_4E8BC4426B8A8195F7EE",
                "Shared hydrogen-reduction program.",
            ),
            (
                "PROC2",
                "reactor_process_gas",
                f"{run_id}_S02",
                "reactor_type;catalyst_loading_mass_g;temperature_setpoint_C;holding_time_min;carbon_source;carbon_source_flow_original;inert_gas;inert_gas_flow_original;total_flow_original",
                "SPAN_4E8BC4426B8A8195F7EE",
                "Shared ethylene/nitrogen CNT-growth program.",
            ),
            (
                "PRESS1",
                "reactor_process_gas",
                f"{run_id}_S01",
                "pressure_original",
                "SPAN_142155253837FA4E1806",
                "Reaction reported at atmospheric pressure.",
            ),
            (
                "PRESS2",
                "reactor_process_gas",
                f"{run_id}_S02",
                "pressure_original",
                "SPAN_142155253837FA4E1806",
                "Reaction reported at atmospheric pressure.",
            ),
            (
                "YIELD",
                "yield_quality",
                f"{run_id}_PROD",
                "primary_yield_metric;yield_original",
                "SPAN_497522478403E7C96D17",
                "Table 1 catalyst-specific carbon yield.",
            ),
            (
                "YIELD_DEF",
                "yield_quality",
                f"{run_id}_PROD",
                "yield_definition_original;yield_calculation_method",
                "SPAN_4E8BC4426B8A8195F7EE",
                "Reported gravimetric carbon-yield formula.",
            ),
            (
                "DIMS",
                "yield_quality",
                f"{run_id}_PROD",
                "CNT_type_reported;outer_diameter_range_nm;product_mixture_summary",
                "SPAN_0AE5072153156983F289",
                "SEM nanotube assignment and reported 20-60 nm diameter range.",
            ),
            (
                "COST",
                "cost_scale_review",
                run_id,
                "scale_level_demonstrated;reactor_capacity_or_throughput",
                "SPAN_4E8BC4426B8A8195F7EE",
                "Laboratory 700 mg catalyst experiment.",
            ),
        ]
        for suffix, table, record_id, fields, span_id, summary in evidence_specs:
            tables["evidence_index"].append(
                evidence_row(
                    store,
                    source_id,
                    f"EVD_{run_id}_{suffix}",
                    run_id,
                    table,
                    record_id,
                    fields,
                    span_id,
                    summary,
                )
            )
        if is_feco_alumina:
            tables["evidence_index"].append(
                evidence_row(
                    store,
                    source_id,
                    f"EVD_{run_id}_PURIFICATION",
                    run_id,
                    "yield_quality",
                    f"{run_id}_PROD",
                    "post_treatment_or_purification;purification_condition;morphology;alignment_or_array",
                    "SPAN_3F724D651503AAD7A449",
                    "Fe-Co/alumina bundle morphology and liquid-oxidation purification.",
                )
            )
    first_run = f"{source_id}_R01"
    tables["review_issue_log"].append(
        issue_row(
            f"{source_id}_ISSUE_DEFINITION_001",
            source_id,
            first_run,
            "definition_ambiguity",
            "yield_quality",
            f"{first_run}_PROD",
            "yield_original",
            "Reported carbon yield includes all accumulated carbon-containing material and must not be treated as purified CNT yield; SEM alone was acknowledged as insufficient to prove tubular identity.",
            f"EVD_{first_run}_YIELD;EVD_{first_run}_YIELD_DEF",
            "high",
        )
    )
    return tables


def build_6c1(
    meta: dict[str, Any], store: EvidenceStore
) -> dict[str, list[dict[str, str]]]:
    source_id = meta["source_id"]
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            meta,
            "Five-stage catalyst/CVD procedure; four ethanol-flow runs; TGA and Raman composition tables.",
        )
    )
    configs = [
        (
            "R01",
            "A-CNTs / 10 sccm ethanol",
            "10",
            "12.1",
            "36.4",
            "31.8",
            "39.0",
            "",
            "",
        ),
        (
            "R02",
            "B-CNTs / 25 sccm ethanol",
            "25",
            "83.7",
            "1.3",
            "9.1",
            "83.4",
            "10",
            "10 ± 2",
        ),
        ("R03", "C-CNTs / 40 sccm ethanol", "40", "36.9", "58.3", "0", "34.7", "", ""),
        ("R04", "D-CNTs / 55 sccm ethanol", "55", "30.2", "65.7", "0", "28.8", "", ""),
    ]
    for (
        code,
        label,
        flow,
        tga_mwcnt,
        amorphous,
        swcnt,
        raman_mwcnt,
        dmean,
        drange,
    ) in configs:
        run_id = f"{source_id}_{code}"
        tables["source_run"].append(
            run_row(
                source_id,
                code,
                label,
                f"Ni/quartz; ethanol {flow} sccm; 750 C for 20 min; TGA MWCNT fraction {tga_mwcnt}%.",
            )
        )
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                catalyst_label="Ni nanoparticles on quartz substrate",
                active_metals="Ni",
                support_material="quartz substrate",
                precursor_summary="50 mmol/L nickel nitrate solution",
                preparation_method="spin coating",
                preparation_modifier="thermal decomposition followed by H2 reduction",
                preparation_detail="Homogeneous nickel-nitrate film spin-coated on quartz and dried.",
                drying_condition="65 C for 2 h",
                calcination_condition="350 C for 30 min at 5 C/min to form NiO",
                reduction_condition="H2 10 sccm plus N2 25 sccm at 450 C for 10 min",
            )
        )
        tables["reactor_process_gas"].extend(
            [
                process_row(
                    run_id,
                    1,
                    "catalyst_decomposition",
                    reactor_type="horizontal tube CVD furnace",
                    reactor_material="not_reported",
                    reactor_setup_summary="Nickel-nitrate-coated quartz substrate in reactor.",
                    temperature_setpoint_C="350",
                    holding_time_min="30",
                    heating_rate_C_min="5",
                    temperature_program_summary="Heat nickel nitrate to 350 C to form NiO.",
                    pressure_original="not_reported",
                    pressure_kPa="",
                ),
                process_row(
                    run_id,
                    2,
                    "reduction",
                    reactor_type="horizontal tube CVD furnace",
                    reactor_setup_summary="NiO-coated quartz substrate.",
                    temperature_setpoint_C="450",
                    holding_time_min="10",
                    reducing_gas="H2",
                    reducing_gas_flow_original="10 sccm",
                    reducing_gas_flow_sccm="10",
                    inert_gas="N2",
                    inert_gas_flow_original="25 sccm",
                    inert_gas_flow_sccm="25",
                    pressure_original="not_reported",
                    pressure_kPa="",
                ),
                process_row(
                    run_id,
                    3,
                    "growth",
                    reactor_type="horizontal tube CVD furnace",
                    reactor_setup_summary="Ethanol bubbler held at 45 C; N2 carried ethanol vapour over Ni/quartz.",
                    temperature_setpoint_C="750",
                    holding_time_min="20",
                    heating_rate_C_min="25",
                    carbon_source="ethanol vapour",
                    carbon_source_flow_original=f"{flow} sccm",
                    carbon_source_flow_sccm=flow,
                    reducing_gas="H2",
                    reducing_gas_flow_original="10 sccm",
                    reducing_gas_flow_sccm="10",
                    inert_gas="N2",
                    inert_gas_flow_original="not_reported",
                    gas_composition_summary="ethanol vapour via N2 bubbler with H2 coflow",
                    pressure_original="not_reported",
                    pressure_kPa="",
                ),
            ]
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="MWCNT fraction in recovered specimen by TGA peak fitting",
                yield_original=f"{tga_mwcnt}% MWCNT by TGA",
                yield_definition_original="MWCNT fraction assigned from Lorentzian fitting of DTGA oxidation regions.",
                yield_calculation_method="Reported Lorentzian peak-area fitting of DTGA",
                yield_value_standardized=tga_mwcnt,
                yield_unit_standardized="wt% MWCNT fraction of specimen",
                secondary_result_summary=f"Amorphous carbon {amorphous}%; SWCNT {swcnt}%; Raman-derived average MWCNT estimate {raman_mwcnt}%.",
                CNT_type_reported="MWCNT-containing product",
                product_mixture_summary=f"MWCNTs plus amorphous carbon ({amorphous}%), SWCNTs ({swcnt}%) and retained Ni/carbons as reported.",
                CNT_type_evidence="TGA phase fitting, Raman estimation and microscopy.",
                outer_diameter_mean_nm=dmean,
                outer_diameter_range_nm=drange,
                morphology="regular and uniform long MWCNTs"
                if code == "R02"
                else "mixed/heterogeneous carbon nanotube product",
                Raman_laser_wavelength_nm="785",
                amorphous_carbon_level=f"{amorphous} wt% by TGA fitting",
                characterization_methods="XRD; SEM; TGA/DTGA; Raman"
                + ("; TEM" if code == "R02" else ""),
                post_treatment_or_purification="0.4 M HCl wash to remove deposits from substrate; deionized-water wash",
                purification_condition="0.4 M HCl at 45 C; dry at 65 C for 1 h",
            )
        )
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                reactor_capacity_or_throughput="quartz-substrate laboratory batch",
                cost_driver_summary="not_reported",
            )
        )
        evidence_specs = [
            (
                "CAT",
                "catalyst_system",
                f"{run_id}_CAT",
                "catalyst_label;active_metals;support_material;precursor_summary;preparation_method",
                "SPAN_FAC07CACA134B58C0AD8",
                "Ni-nitrate coating on quartz and run labels.",
            ),
            (
                "PROC1",
                "reactor_process_gas",
                f"{run_id}_S01",
                "stage_type;temperature_setpoint_C;holding_time_min;heating_rate_C_min",
                "SPAN_676ADBA8492F1993153B",
                "Nickel-nitrate decomposition stage.",
            ),
            (
                "PROC2",
                "reactor_process_gas",
                f"{run_id}_S02",
                "stage_type;temperature_setpoint_C;holding_time_min;reducing_gas;reducing_gas_flow_original;inert_gas;inert_gas_flow_original",
                "SPAN_676ADBA8492F1993153B",
                "Hydrogen reduction stage.",
            ),
            (
                "PROC3_PROGRAM",
                "reactor_process_gas",
                f"{run_id}_S03",
                "stage_type;temperature_setpoint_C;holding_time_min;heating_rate_C_min;carbon_source;reducing_gas",
                "SPAN_D70535410451F3E534AC",
                "Ethanol CNT-growth temperature, time and hydrogen coflow.",
            ),
            (
                "PROC3_FLOW",
                "reactor_process_gas",
                f"{run_id}_S03",
                "carbon_source_flow_original;reducing_gas_flow_original",
                "SPAN_FAC07CACA134B58C0AD8",
                "Run labels, four ethanol flow rates and 10 sccm hydrogen coflow.",
            ),
            (
                "YIELD_DEF",
                "yield_quality",
                f"{run_id}_PROD",
                "primary_yield_metric;yield_definition_original;yield_calculation_method",
                "SPAN_2AE052F27103F186CC6E",
                "DTGA peak assignment and Lorentzian area-fitting definition.",
            ),
            (
                "YIELD_VALUE",
                "yield_quality",
                f"{run_id}_PROD",
                "yield_original;product_mixture_summary",
                "SPAN_0068ADC1513B1DA6B4E9",
                "TGA table MWCNT and co-product fractions.",
            ),
            (
                "RAMAN_METHOD",
                "yield_quality",
                f"{run_id}_PROD",
                "Raman_laser_wavelength_nm",
                "SPAN_089E75DFEB9ED4B2B6A0",
                "Reported 785 nm Raman measurement.",
            ),
            (
                "PURIFICATION",
                "yield_quality",
                f"{run_id}_PROD",
                "post_treatment_or_purification;purification_condition",
                "SPAN_D70535410451F3E534AC",
                "Reported HCl/water recovery and drying procedure.",
            ),
            (
                "COST",
                "cost_scale_review",
                run_id,
                "scale_level_demonstrated;reactor_capacity_or_throughput",
                "SPAN_FAC07CACA134B58C0AD8",
                "Laboratory quartz-substrate CVD setup.",
            ),
        ]
        for suffix, table, record_id, fields, span_id, summary in evidence_specs:
            tables["evidence_index"].append(
                evidence_row(
                    store,
                    source_id,
                    f"EVD_{run_id}_{suffix}",
                    run_id,
                    table,
                    record_id,
                    fields,
                    span_id,
                    summary,
                )
            )
        if code == "R02":
            tables["evidence_index"].append(
                evidence_row(
                    store,
                    source_id,
                    f"EVD_{run_id}_TEM",
                    run_id,
                    "yield_quality",
                    f"{run_id}_PROD",
                    "outer_diameter_mean_nm;outer_diameter_range_nm;morphology",
                    "SPAN_1CBFB98253697D9EFD53",
                    "TEM diameter and long-MWCNT morphology for B-CNTs.",
                )
            )
    first_run = f"{source_id}_R01"
    tables["review_issue_log"].append(
        issue_row(
            f"{source_id}_ISSUE_DEFINITION_001",
            source_id,
            first_run,
            "definition_ambiguity",
            "yield_quality",
            f"{first_run}_PROD",
            "primary_yield_metric",
            "The authors use yield/purity language for fitted MWCNT fraction in recovered specimens; these values are not a mass yield per feed or catalyst.",
            f"EVD_{first_run}_YIELD_DEF;EVD_{first_run}_YIELD_VALUE",
            "high",
        )
    )
    return tables


def build_849(
    meta: dict[str, Any], store: EvidenceStore
) -> dict[str, list[dict[str, str]]]:
    source_id = meta["source_id"]
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            meta,
            "Fe-Mo-MgO preparation; methane/acetylene pressure comparison; TEM/Raman/TGA results.",
        )
    )
    configs = [
        ("R01", "Fe-Mo-MgO / nominal 1 bar", "1 bar", "64"),
        ("R02", "Fe-Mo-MgO / pressure raised to 2 bar", "2 bar after 45 min", "83"),
    ]
    for code, label, pressure, carbon_content in configs:
        run_id = f"{source_id}_{code}"
        tables["source_run"].append(
            run_row(
                source_id,
                code,
                label,
                f"Fe:Mo:MgO 1:8:40; methane then acetylene at 900 C; TGA carbon content {carbon_content}%.",
            )
        )
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                catalyst_label="Fe-Mo-MgO (1:8:40 molar ratio)",
                active_metals="Fe; Mo",
                support_material="MgO",
                promoter="Mo",
                metal_ratio_original="Fe:Mo:MgO = 1:8:40 molar",
                metal_ratio_standardized="Fe:Mo = 1:8; MgO support",
                precursor_summary="Fe(NO3)3·9H2O; (NH4)6Mo7O24·4H2O; MgO",
                preparation_method="impregnation",
                preparation_modifier="NH3-assisted aqueous impregnation",
                preparation_detail="2 g MgO treated with 0.3 wt% NH3 solution, ammonium heptamolybdate and ferric nitrate; stirred sequentially.",
                drying_condition="10 kPa at 90 C for 120 min; ground after drying",
                calcination_condition="none",
                reduction_condition="none before synthesis; methane provides in situ reduction",
                phase_or_state_summary="oxide precursor catalyst; no calcination/reduction pretreatment",
            )
        )
        tables["reactor_process_gas"].extend(
            [
                process_row(
                    run_id,
                    1,
                    "methane_activation_growth",
                    reactor_type="15 mm tubular furnace",
                    reactor_material="not_reported",
                    reactor_setup_summary="Catalyst in quartz boat loaded directly into 900 C hot zone.",
                    temperature_setpoint_C="900",
                    holding_time_min="15",
                    carbon_source="CH4",
                    carbon_source_flow_original="40 cm3/min",
                    carbon_source_flow_sccm="40",
                    inert_gas="Ar",
                    inert_gas_flow_original="100 cm3/min purge",
                    inert_gas_flow_sccm="100",
                    pressure_original="1 bar initially",
                    pressure_kPa="",
                ),
                process_row(
                    run_id,
                    2,
                    "acetylene_growth",
                    reactor_type="15 mm tubular furnace",
                    reactor_setup_summary="CH4 stopped and C2H2 introduced at 900 C.",
                    temperature_setpoint_C="900",
                    holding_time_min="not_reported",
                    carbon_source="C2H2",
                    carbon_source_flow_original="10 cm3/min",
                    carbon_source_flow_sccm="10",
                    pressure_original=pressure,
                    pressure_kPa="",
                    temperature_program_summary="For the high-pressure run, pressure was raised to 2 bar after 45 min and continued for 20 additional min.",
                ),
                process_row(
                    run_id,
                    3,
                    "cooling",
                    reactor_type="15 mm tubular furnace",
                    temperature_setpoint_C="",
                    pressure_original="not_reported",
                    pressure_kPa="",
                    inert_gas="Ar",
                    inert_gas_flow_original="300 cm3/min",
                    inert_gas_flow_sccm="300",
                    cooling_condition="Product removed from hot zone and cooled to room temperature in Ar for about 5 min.",
                ),
            ]
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="TGA carbon content of as-prepared product",
                yield_original=f"approximately {carbon_content}% carbon by TGA",
                yield_definition_original="Carbon fraction of total as-prepared product mass from TGA.",
                yield_calculation_method="Reported TGA mass fraction",
                yield_value_standardized=carbon_content,
                yield_unit_standardized="wt% carbon in as-prepared product",
                secondary_result_summary="Higher pressure increased reported carbon content from about 64% to 83%.",
                CNT_type_reported="few-wall CNTs; some DWCNT/MWCNT and bamboo-like CNTs observed",
                product_mixture_summary="Mostly impurity-free CNTs with small catalyst inclusions; mixed few-wall, double-wall, multi-wall and bamboo-like morphologies.",
                CNT_type_evidence="TEM/HRTEM and RBM Raman evidence.",
                SWCNT_or_few_wall_evidence_summary="RBM peaks and HRTEM support small-diameter few-wall CNTs.",
                RBM_peak_reported="yes",
                outer_diameter_range_nm="2-10 (mostly); some approximately 20 nm",
                wall_number_summary="few-wall dominant; double-wall and multi-wall examples observed",
                morphology="few-wall, closed-tip, bamboo-like and bundled CNTs",
                Raman_ratio_type="IG/ID",
                Raman_ratio_value="approximately 10",
                Raman_laser_wavelength_nm="514",
                TGA_carbon_content_wt_percent=carbon_content,
                amorphous_carbon_level="no amorphous-carbon TGA peak reported",
                characterization_methods="TEM; HRTEM; Raman; TGA/DSC; XRD; Mössbauer; electron diffraction",
            )
        )
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                reactor_capacity_or_throughput="2 g MgO used in catalyst preparation; catalyst charge not reported",
                cost_driver_summary="Authors emphasize no post-preparation calcination or reduction step and shorter catalyst preparation; no quantitative cost reported.",
            )
        )
        evidence_specs = [
            (
                "CAT_RATIO",
                "catalyst_system",
                f"{run_id}_CAT",
                "catalyst_label;active_metals;support_material;metal_ratio_original;precursor_summary;preparation_method",
                "SPAN_60FB137AA299DA43B224",
                "Fe-Mo-MgO identity, 1:8:40 ratio and precursor route.",
            ),
            (
                "CAT_DETAIL",
                "catalyst_system",
                f"{run_id}_CAT",
                "preparation_detail;drying_condition;calcination_condition;reduction_condition",
                "SPAN_9B6E7EA87D8F0A1E6F17",
                "Sequential impregnation, vacuum drying and no-calcination details.",
            ),
            (
                "PROC1",
                "reactor_process_gas",
                f"{run_id}_S01",
                "reactor_type;temperature_setpoint_C;holding_time_min;carbon_source;carbon_source_flow_original;inert_gas;inert_gas_flow_original",
                "SPAN_0FF9E9E489B7A081D57A",
                "Methane stage at 900 C.",
            ),
            (
                "PROC2",
                "reactor_process_gas",
                f"{run_id}_S02",
                "reactor_type;temperature_setpoint_C;carbon_source;carbon_source_flow_original;pressure_original;temperature_program_summary",
                "SPAN_0FF9E9E489B7A081D57A",
                "Acetylene and pressure program.",
            ),
            (
                "PROC3",
                "reactor_process_gas",
                f"{run_id}_S03",
                "stage_type;inert_gas;inert_gas_flow_original;cooling_condition",
                "SPAN_0FF9E9E489B7A081D57A",
                "Argon cooling stage.",
            ),
            (
                "YIELD",
                "yield_quality",
                f"{run_id}_PROD",
                "primary_yield_metric;yield_original;TGA_carbon_content_wt_percent;outer_diameter_range_nm",
                "SPAN_1121D7DE12763E994FEA",
                "Pressure-specific TGA carbon content and CNT diameter.",
            ),
            (
                "RAMAN",
                "yield_quality",
                f"{run_id}_PROD",
                "CNT_type_reported;Raman_ratio_type;Raman_ratio_value;RBM_peak_reported;amorphous_carbon_level",
                "SPAN_57F5C0D97D56A15DA12E",
                "Few-wall identity, IG/ID ratio, RBM and no-amorphous-carbon result.",
            ),
            (
                "RAMAN_LASER",
                "yield_quality",
                f"{run_id}_PROD",
                "Raman_laser_wavelength_nm",
                "SPAN_59DFF056284484520444",
                "Reported 514 nm Raman excitation wavelength.",
            ),
            (
                "PRESSURE1",
                "reactor_process_gas",
                f"{run_id}_S01",
                "pressure_original",
                "SPAN_3BECE6C78B6B41620625",
                "Figure 9 identifies the 1 bar reference synthesis case.",
            ),
            (
                "PRESSURE2",
                "reactor_process_gas",
                f"{run_id}_S02",
                "pressure_original",
                "SPAN_3BECE6C78B6B41620625",
                "Figure 9 identifies the 1 bar and 2 bar synthesis cases.",
            ),
            (
                "COST",
                "cost_scale_review",
                run_id,
                "scale_level_demonstrated;cost_driver_summary",
                "SPAN_1CD4708B4003CDA9E400",
                "Reported simplification by omitting calcination/reduction.",
            ),
        ]
        for suffix, table, record_id, fields, span_id, summary in evidence_specs:
            tables["evidence_index"].append(
                evidence_row(
                    store,
                    source_id,
                    f"EVD_{run_id}_{suffix}",
                    run_id,
                    table,
                    record_id,
                    fields,
                    span_id,
                    summary,
                )
            )
        tables["evidence_index"].append(
            evidence_row(
                store,
                source_id,
                f"EVD_{run_id}_MORPH",
                run_id,
                "yield_quality",
                f"{run_id}_PROD",
                "CNT_type_reported;product_mixture_summary;outer_diameter_range_nm;wall_number_summary;morphology",
                "SPAN_13C536E8DF5FD130BA9F",
                "TEM product purity, dimensions and catalyst inclusions.",
            )
        )
    high_run = f"{source_id}_R02"
    tables["review_issue_log"].append(
        issue_row(
            f"{source_id}_ISSUE_PRESSURE_001",
            source_id,
            high_run,
            "definition_ambiguity",
            "reactor_process_gas",
            f"{high_run}_S02",
            "holding_time_min",
            "The text reports pressure raised after 45 min and continued for 20 min, but does not cleanly separate methane and acetylene durations for the atmospheric reference run.",
            f"EVD_{high_run}_PROC2",
        )
    )
    tables["review_issue_log"].append(
        issue_row(
            f"{source_id}_ISSUE_YIELD_001",
            source_id,
            high_run,
            "definition_ambiguity",
            "yield_quality",
            f"{high_run}_PROD",
            "yield_original",
            "The reported 64% and 83% values are TGA carbon content of total product, not CNT yield per catalyst or carbon-source conversion.",
            f"EVD_{high_run}_YIELD",
            "high",
        )
    )
    return tables


BUILDERS = {
    "LIT_0705FD92BBA5C6D2": build_0705,
    "LIT_B737792873D4A97E": build_b737,
    "LIT_3D2FAA624663FA97": build_3d2,
    "LIT_6C1D6D8880AEB493": build_6c1,
    "LIT_849AD7FB325763D1": build_849,
}


def build_first_batch() -> dict[str, Any]:
    metadata = load_metadata()
    BATCH_ROOT.mkdir(parents=True, exist_ok=True)
    store = EvidenceStore()
    package_metrics: list[dict[str, Any]] = []
    try:
        for source_id in FIRST_BATCH_IDS:
            package = BUILDERS[source_id](metadata[source_id], store)
            out = PACKAGE_ROOT / source_id
            for table in TABLES:
                write_table(out, table, package[table])
            metric = {
                "source_id": source_id,
                "output_path": str(out.relative_to(ROOT)).replace("\\", "/"),
                "row_counts": {table: len(package[table]) for table in TABLES},
                "status": "needs_review",
            }
            (out / "package_metrics.json").write_text(
                json.dumps(metric, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            package_metrics.append(metric)
    finally:
        store.close()
    result = {
        "batch_id": BATCH_ID,
        "automated_model_used": False,
        "packages": package_metrics,
        "total_runs": sum(item["row_counts"]["source_run"] for item in package_metrics),
        "status": "completed_needs_review",
    }
    (BATCH_ROOT / "batch_001_metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    batch = build_first_batch()
    inventory = build_inventory()
    print(
        json.dumps(
            {"inventory": inventory, "first_batch": batch},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
