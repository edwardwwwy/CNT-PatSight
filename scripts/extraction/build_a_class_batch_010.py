#!/usr/bin/env python3
"""Build the tenth evidence-grounded A-class extraction batch."""
from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

from scripts.extraction.build_a_class_batch import (
    BATCH_ID,
    ROOT,
    TABLES,
    EvidenceStore,
    catalyst_row,
    cost_row,
    evidence_row,
    issue_row,
    load_metadata,
    master_row,
    process_row,
    run_row,
    yield_row,
)
from scripts.extraction.build_a_class_batch_002 import publish_package


BATCH_NUMBER = 10
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_4BDFD588A5A5F5AA"
TABLES_PATH = (
    ROOT / f"data/interim/parsed_text/{SOURCE_ID}/tables.json"
)

REACTOR_SPANS = {
    82: "SPAN_702727879343154F1754",
    83: "SPAN_34B83B7CFCD0CE598918",
    84: "SPAN_1E2C2D74E1CE03FF69A8",
    85: "SPAN_5689B2FEAB9047F361D5",
    86: "SPAN_0E9DC4CF2B3AB935A6C7",
}
GAS_SPANS = {
    87: "SPAN_405AEC0F65B1E9C34F14",
    88: "SPAN_DE08E08B446B17A46660",
    89: "SPAN_A704DC4C51EC498C51F5",
    90: "SPAN_90450AF297550D366F3B",
    91: "SPAN_5C98C07097CB5EC03EBD",
}
SUCCESS_SPANS = {
    92: "SPAN_923F2AAC0DA3DC6FA2C2",
    93: "SPAN_25382920698E99991656",
    94: "SPAN_46CE5668A940C46D34C2",
}
FAILURE_SPANS = {
    95: "SPAN_7892AC895388B2C9B779",
    96: "SPAN_99EE44F9EB4F279162EA",
    97: "SPAN_3FC8B58A17E3018D7573",
}


def extracted_rows(
    items: list[dict[str, Any]],
    page_start: int,
    page_end: int,
    expected_columns: int,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in items:
        match = re.search(
            r"Extracted table p(\d+)", item["section_name_raw"]
        )
        if not match:
            continue
        page = int(match.group(1))
        if not page_start <= page <= page_end:
            continue
        current = ""
        for line in item["text"].splitlines():
            if re.match(r"^\d+\t", line):
                if current:
                    columns = current.split("\t")
                    columns += [""] * (expected_columns - len(columns))
                    output.append({"page": page, "columns": columns})
                current = line
            elif current:
                current += " " + line
        if current:
            columns = current.split("\t")
            columns += [""] * (expected_columns - len(columns))
            output.append({"page": page, "columns": columns})
    return output


def load_compiled_data() -> tuple[
    dict[int, dict[str, Any]],
    dict[int, dict[str, Any]],
    list[dict[str, Any]],
]:
    items = json.loads(TABLES_PATH.read_text(encoding="utf-8"))
    reactors: dict[int, dict[str, Any]] = {}
    for item in extracted_rows(items, 82, 86, 5):
        order, catalyst, geometry, dimensions, reactor_type = item["columns"][:5]
        reactors[int(order)] = {
            "page": item["page"],
            "catalyst": catalyst.strip(),
            "geometry": geometry.strip(),
            "dimensions": dimensions.strip(),
            "reactor_type": reactor_type.strip(),
        }

    gases: dict[int, dict[str, Any]] = {}
    for item in extracted_rows(items, 87, 91, 8):
        (
            order,
            carbon,
            other_gases,
            temperature,
            carbon_flow,
            other_flow,
            terminal_length,
            synthesis_time,
        ) = item["columns"][:8]
        gases[int(order)] = {
            "page": item["page"],
            "carbon": carbon.strip().lower(),
            "other_gases": other_gases.strip(),
            "temperature": temperature.strip(),
            "carbon_flow": carbon_flow.strip(),
            "other_flow": other_flow.strip(),
            "terminal_length": terminal_length.strip(),
            "synthesis_time": synthesis_time.strip(),
        }

    conditions: list[dict[str, Any]] = []
    for status, start, end, expected in (
        ("successful", 92, 94, 13),
        ("unsuccessful", 95, 97, 12),
    ):
        for item in extracted_rows(items, start, end, expected):
            columns = item["columns"]
            record = {
                "status": status,
                "page": item["page"],
                "order": int(columns[0]),
                "carbon": columns[1].strip().lower(),
                "temperature": columns[2].strip(),
                "qc": columns[3].strip(),
                "qh": columns[4].strip(),
                "qt": columns[5].strip(),
                "volume": columns[6].strip(),
                "residence_time": columns[7].strip(),
                "growth_rate": columns[8].strip(),
                "cc": columns[9].strip(),
                "ch": columns[10].strip(),
                "ratio": columns[11].strip(),
                "growth_rate_duplicate": (
                    columns[12].strip() if expected == 13 else ""
                ),
            }
            if record["growth_rate_duplicate"]:
                record["growth_rate"] = record["growth_rate_duplicate"]
            conditions.append(record)
    return reactors, gases, conditions


def active_metals(label: str) -> str:
    if "stainless steel" in label.lower():
        return "stainless steel; composition not resolved"
    tokens = re.findall(
        r"(?<![A-Za-z])(Fe|Co|Ni|Mo|Cu|Au|Pd|Pt|Mn|W|Ti|Cr|La)(?![a-z])",
        label,
    )
    unique = list(dict.fromkeys(tokens))
    return "; ".join(unique) if unique else "not_reported"


def support_material(label: str) -> str:
    supports = []
    for token in (
        "Al2O3",
        "CaCO3",
        "MgO",
        "NaY",
        "AC",
        "CAs",
        "Mt",
        "SiO2",
    ):
        if token.lower() in label.lower():
            supports.append(token)
    return "; ".join(supports) if supports else "not_reported"


def gas_fields(
    other_gases: str,
    qh: str,
) -> dict[str, str]:
    inert = [
        gas for gas in ("Ar", "N2", "He") if gas.lower() in other_gases.lower()
    ]
    reactive = [
        gas
        for gas in ("CO2", "O2", "H2O", "NH3")
        if gas.lower() in other_gases.lower()
    ]
    try:
        has_hydrogen = float(qh or 0) > 0
    except ValueError:
        has_hydrogen = "h2" in other_gases.lower()
    return {
        "reducing_gas": "H2" if has_hydrogen else "not_applicable",
        "reducing_gas_flow_original": (
            f"{qh} sccm" if has_hydrogen and qh else "not_reported"
        ),
        "reducing_gas_flow_sccm": qh if has_hydrogen else "",
        "inert_gas": "; ".join(inert) if inert else "not_reported",
        "cofeed_or_reactive_gas": (
            "; ".join(reactive) if reactive else "not_applicable"
        ),
    }


def append_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    suffix: str,
    table: str,
    record_id: str,
    fields: str,
    span_id: str,
    summary: str,
    value_status: str = "reported",
) -> None:
    tables["evidence_index"].append(
        evidence_row(
            store,
            SOURCE_ID,
            f"EVD_{run_id}_{suffix}",
            run_id,
            table,
            record_id,
            fields,
            span_id,
            summary,
            value_status=value_status,
        )
    )


def add_observation(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    suffix: str,
    span_id: str,
    summary: str,
) -> str:
    evidence_id = f"EVD_{SOURCE_ID}_OBS_{suffix}"
    evidence = evidence_row(
        store,
        SOURCE_ID,
        evidence_id,
        "not_applicable",
        "source_master",
        SOURCE_ID,
        "source_section_scope",
        span_id,
        summary,
    )
    evidence["evidence_type"] = "source_observation"
    tables["evidence_index"].append(evidence)
    return evidence_id


def compiled_catalyst(
    run_id: str,
    raw_label: str,
) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label=raw_label or "not_reported",
        active_metals=active_metals(raw_label),
        support_material=support_material(raw_label),
        promoter="not_reported",
        metal_ratio_original="not_reported",
        metal_ratio_standardized="not_reported",
        precursor_summary="not_reported in compilation",
        preparation_method="not_reported in compilation",
        preparation_modifier="not_reported",
        preparation_detail="not_reported",
        drying_condition="not_reported",
        calcination_condition="not_reported",
        reduction_condition="not_reported",
        activation_condition="not_reported",
        post_preparation_condition="literature-compiled catalyst identity only",
        phase_or_state_summary="not_reported",
        dispersion_summary="not_reported",
        deactivation_summary="not_reported",
        notes=(
            "Secondary-source catalyst label transcribed from thesis Table 8; "
            "preparation and exact composition require the cited primary paper."
        ),
    )


def compiled_process(
    run_id: str,
    condition: dict[str, Any],
    reactor: dict[str, Any],
    gas: dict[str, Any],
) -> dict[str, str]:
    gas_values = gas_fields(gas["other_gases"], condition["qh"])
    volume = condition["volume"]
    dimensions = reactor["dimensions"] or "not_reported"
    size_summary = dimensions
    if volume:
        size_summary += f"; thesis-calculated V={volume} cm3"
    carbon = condition["carbon"] or gas["carbon"]
    return process_row(
        run_id,
        1,
        "secondary_literature_compiled_CVD_condition",
        reactor_type=(
            f"{reactor['reactor_type']}; {reactor['geometry']}".strip("; ")
            or "not_reported"
        ),
        reactor_material="not_reported",
        reactor_size_summary=size_summary,
        reactor_setup_summary=(
            "Reactor and gas condition compiled from cited primary literature; "
            "not an experiment performed in this thesis."
        ),
        catalyst_loading_mass_g="not_reported",
        temperature_setpoint_C=condition["temperature"] or "not_reported",
        temperature_program_summary=(
            f"Raw Table 9 temperature entry: {gas['temperature'] or 'not_reported'}"
        ),
        holding_time_min=gas["synthesis_time"] or "not_reported",
        pressure_original="not_reported",
        pressure_kPa="",
        carbon_source=carbon,
        carbon_source_flow_original=(
            f"{condition['qc']} sccm"
            if condition["qc"]
            else gas["carbon_flow"] or "not_reported"
        ),
        carbon_source_flow_sccm=condition["qc"],
        reducing_gas=gas_values["reducing_gas"],
        reducing_gas_flow_original=gas_values["reducing_gas_flow_original"],
        reducing_gas_flow_sccm=gas_values["reducing_gas_flow_sccm"],
        inert_gas=gas_values["inert_gas"],
        inert_gas_flow_original="not_separately_reported in processed table",
        cofeed_or_reactive_gas=gas_values["cofeed_or_reactive_gas"],
        cofeed_flow_original=gas["other_flow"] or "not_reported",
        total_flow_original=(
            f"{condition['qt']} sccm; thesis-calculated"
            if condition["qt"]
            else "not_reported"
        ),
        total_flow_sccm=condition["qt"],
        gas_composition_summary=(
            f"Raw other gases: {gas['other_gases'] or 'not_reported'}; "
            f"Cc={condition['cc'] or 'not_reported'} mol/cm3; "
            f"Ch={condition['ch'] or 'not_reported'} mol/cm3; "
            f"Ch/Cc={condition['ratio'] or 'not_reported'}."
        ),
        GHSV_or_residence_time=(
            f"{condition['residence_time']} min residence time"
            if condition["residence_time"]
            else "not_reported"
        ),
        process_note=(
            f"Thesis classification: {condition['status']}; original compiled "
            f"order {condition['order']}."
        ),
    )


def compiled_yield(
    run_id: str,
    condition: dict[str, Any],
    gas: dict[str, Any],
) -> dict[str, str]:
    growth = condition["growth_rate"]
    successful = condition["status"] == "successful"
    if growth:
        original = (
            f"{growth} micrometers/min thesis-calculated CNT growth rate; "
            f"classified {condition['status']}"
        )
        standardized = growth if successful else ""
        unit = "micrometers/min" if successful else "not_applicable"
    else:
        original = (
            f"condition classified {condition['status']}; "
            "growth rate not available"
        )
        standardized = ""
        unit = "not_applicable"
    terminal = gas["terminal_length"] or "not_reported"
    synthesis_time = gas["synthesis_time"] or "not_reported"
    return yield_row(
        run_id,
        primary_yield_metric=(
            "thesis_calculated_CNT_linear_growth_rate"
            if successful
            else "author_classified_unsuccessful_condition"
        ),
        yield_original=original,
        yield_definition_original=(
            "Successful means CNT products were clearly observed in the cited "
            "paper; growth rate was calculated as terminal CNT length or height "
            "divided by synthesis time."
        ),
        yield_calculation_method=(
            "Secondary-source calculation from compiled terminal length/height "
            "and synthesis time."
        ),
        yield_value_standardized=standardized,
        yield_unit_standardized=unit,
        yield_standardization_note=(
            "The thesis calculation is retained; it is not a mass yield or "
            "carbon conversion."
        ),
        secondary_result_summary=(
            f"Raw terminal CNT length/height {terminal} micrometers; raw "
            f"synthesis time {synthesis_time} min; classification "
            f"{condition['status']}."
        ),
        CNT_type_reported="CNTs",
        CNT_type_confirmed="not_applicable",
        product_mixture_summary="not_reported in compilation",
        CNT_type_evidence=(
            "Compilation used clear observation of CNT products as the "
            "success criterion; run-specific characterization was not transcribed."
        ),
        wall_number_summary="not_reported",
        morphology="not_reported",
        alignment_or_array="terminal length/height may describe arrays; not resolved",
        Raman_ratio_type="not_reported",
        Raman_ratio_value="not_reported",
        purity_basis="not_reported",
        residue_summary="not_reported",
        amorphous_carbon_level="not_reported",
        characterization_methods="not_reported in compilation",
        post_treatment_or_purification="not_reported",
        purification_condition="not_reported",
        notes=(
            "Secondary literature compilation; consult the cited primary "
            "article before formal promotion."
        ),
    )


def compiled_cost(run_id: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="secondary_literature_compilation",
        scale_level_claimed="not_reported",
        scale_evidence_summary=(
            "The thesis compares published cylindrical CVD conditions for "
            "energy, material and life-cycle implications."
        ),
        reactor_capacity_or_throughput="not_reported",
        continuous_operation_time_h="not_applicable",
        catalyst_lifetime_or_reuse="not_reported",
        batch_stability="not_reported",
        scale_up_issue=(
            "Cross-paper heterogeneity, missing reactor dimensions and assumed "
            "heated lengths limit direct industrial comparison."
        ),
        cost_driver_summary=(
            "Synthesis temperature, hydrocarbon/hydrogen flow, total flow and "
            "residence time were treated as energy/material drivers."
        ),
        safety_risk=(
            "Hydrocarbon and hydrogen feeds at elevated temperature; "
            "run-specific controls are unavailable in the compilation."
        ),
        emission_or_waste=(
            "Short residence time may waste feed; high residence time may "
            "accumulate byproducts according to the thesis discussion."
        ),
        industrial_readiness_assessment=(
            "Useful for comparative screening, not sufficient for process design."
        ),
        reproduction_value="medium; requires primary-paper verification",
        reproduction_priority="medium",
        recommended_next_action=(
            "Resolve the original cited paper and verify the compiled condition."
        ),
    )


def build(
    metadata: dict[str, Any],
    store: EvidenceStore,
) -> dict[str, list[dict[str, str]]]:
    reactors, gases, conditions = load_compiled_data()
    if len(reactors) != 108 or len(gases) != 108:
        raise RuntimeError("Expected 108 Table 8 and Table 9 source-order rows")
    status_counts = Counter(item["status"] for item in conditions)
    if status_counts != Counter({"successful": 74, "unsuccessful": 52}):
        raise RuntimeError(f"Unexpected Table 10/11 counts: {status_counts}")

    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "Master's thesis secondary literature compilation: Tables 8-9 "
                "contain 108 source-order reactor/gas records; Tables 10-11 "
                "contain 74 successful and 52 unsuccessful expanded conditions."
            ),
        )
    )
    tables["source_master"][0]["local_file_path"] = (
        f"data/interim/parsed_text/{SOURCE_ID}/full_text.txt"
    )
    tables["source_master"][0]["notes"] += (
        " All source_run rows are secondary literature-compiled conditions, "
        "not experiments conducted by the thesis author."
    )

    for sequence, condition in enumerate(conditions, start=1):
        status_code = "S" if condition["status"] == "successful" else "U"
        code = f"{status_code}{sequence:03d}"
        run_id = f"{SOURCE_ID}_{code}"
        order = condition["order"]
        reactor = reactors[order]
        gas = gases[order]
        row = run_row(
            SOURCE_ID,
            code,
            (
                f"{condition['status']} compiled condition; source order "
                f"{order}; {condition['carbon']} at "
                f"{condition['temperature']} C"
            ),
            (
                f"Secondary literature condition: Qc {condition['qc'] or 'NR'} "
                f"sccm, Qh {condition['qh'] or 'NR'} sccm, Qt "
                f"{condition['qt'] or 'NR'} sccm, growth rate "
                f"{condition['growth_rate'] or 'NR'} micrometers/min."
            ),
            "medium",
        )
        row["data_type"] = "secondary_literature_compiled_condition"
        row["notes"] = (
            f"Original compilation order {order}; thesis Table 10/11 "
            "condition; primary-paper verification required."
        )
        tables["source_run"].append(row)
        tables["catalyst_system"].append(
            compiled_catalyst(run_id, reactor["catalyst"])
        )
        tables["reactor_process_gas"].append(
            compiled_process(run_id, condition, reactor, gas)
        )
        tables["yield_quality"].append(compiled_yield(run_id, condition, gas))
        tables["cost_scale_review"].append(compiled_cost(run_id))

        reactor_span = REACTOR_SPANS[reactor["page"]]
        gas_span = GAS_SPANS[gas["page"]]
        processed_span = (
            SUCCESS_SPANS[condition["page"]]
            if condition["status"] == "successful"
            else FAILURE_SPANS[condition["page"]]
        )
        append_evidence(
            tables,
            store,
            run_id,
            "CATALYST",
            "catalyst_system",
            f"{run_id}_CAT",
            "record_level",
            reactor_span,
            f"Table 8 catalyst identity for original order {order}.",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "REACTOR",
            "reactor_process_gas",
            f"{run_id}_S01",
            "reactor_type;reactor_size_summary",
            reactor_span,
            f"Table 8 reactor geometry and dimensions for order {order}.",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "RAW_GAS",
            "reactor_process_gas",
            f"{run_id}_S01",
            "temperature_program_summary;holding_time_min;carbon_source;"
            "carbon_source_flow_original;reducing_gas;inert_gas;"
            "cofeed_or_reactive_gas;cofeed_flow_original;"
            "gas_composition_summary",
            gas_span,
            f"Table 9 raw gas, temperature, length and time for order {order}.",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "CALCULATED_PROCESS",
            "reactor_process_gas",
            f"{run_id}_S01",
            "temperature_setpoint_C;reactor_size_summary;"
            "carbon_source_flow_original;carbon_source_flow_sccm;"
            "reducing_gas_flow_original;reducing_gas_flow_sccm;"
            "total_flow_original;total_flow_sccm;"
            "gas_composition_summary;GHSV_or_residence_time;process_note",
            processed_span,
            (
                f"Table 10/11 processed parameters for compiled "
                f"{condition['status']} condition."
            ),
            "calculated",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "OUTCOME",
            "yield_quality",
            f"{run_id}_PROD",
            "record_level",
            processed_span,
            (
                f"Table 10/11 growth-rate values and {condition['status']} "
                "classification."
            ),
            "calculated",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "COST_REVIEW",
            "cost_scale_review",
            run_id,
            "record_level",
            "SPAN_22635E21DD354225AF1C",
            "Review assessment based on the thesis compilation method.",
            "review_assessment",
        )

    method = add_observation(
        tables,
        store,
        "METHOD",
        "SPAN_22635E21DD354225AF1C",
        (
            "The thesis selected published cylindrical CVD experiments using "
            "methane, ethylene or acetylene and defined successful experiments "
            "as those where CNT products were clearly observed."
        ),
    )
    calculation = add_observation(
        tables,
        store,
        "CALCULATION",
        "SPAN_9BC3E737EE6A7D2ED5E6",
        (
            "Residence time, concentrations and growth rate were normalized or "
            "calculated across papers; missing heated lengths could be filled "
            "using furnace-manufacturer standard parameters."
        ),
    )
    conclusion = add_observation(
        tables,
        store,
        "CONCLUSION",
        "SPAN_88D20C70CD896232C66C",
        (
            "The thesis concludes methane has the highest average successful "
            "temperature, followed by ethylene and acetylene, and discusses an "
            "optimum residence-time tradeoff for material and energy use."
        ),
    )

    first_run = f"{SOURCE_ID}_S001"
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_SECONDARY_001",
                SOURCE_ID,
                first_run,
                "definition_ambiguity",
                "source_run",
                first_run,
                "data_type",
                (
                    "All 126 rows are secondary literature-compiled conditions. "
                    "They must not be treated as experiments performed by the "
                    "thesis author or as primary evidence without resolving the "
                    "cited paper."
                ),
                method,
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SUCCESS_001",
                SOURCE_ID,
                first_run,
                "definition_ambiguity",
                "yield_quality",
                f"{first_run}_PROD",
                "yield_definition_original",
                (
                    "Successful means CNT products were clearly observed "
                    "according to the cited authors; product purity, wall count "
                    "and quantitative quality thresholds were not standardized."
                ),
                method,
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CALCULATION_001",
                SOURCE_ID,
                first_run,
                "definition_ambiguity",
                "reactor_process_gas",
                f"{first_run}_S01",
                "GHSV_or_residence_time",
                (
                    "Reactor volume, total flow, residence time, gas "
                    "concentrations and growth rate can be thesis-derived rather "
                    "than directly reported in the primary paper."
                ),
                calculation,
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_ASSUMPTION_001",
                SOURCE_ID,
                first_run,
                "critical_data_gap",
                "reactor_process_gas",
                f"{first_run}_S01",
                "reactor_size_summary",
                (
                    "Where heated length was unavailable, the thesis could "
                    "assume 30.48 cm from a common furnace model. Individual "
                    "rows do not identify which dimensions were assumed."
                ),
                calculation,
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CATALYST_001",
                SOURCE_ID,
                f"{SOURCE_ID}_S002",
                "critical_data_gap",
                "catalyst_system",
                f"{SOURCE_ID}_S002_CAT",
                "catalyst_label",
                (
                    "Some Table 8 order rows combine multiple alternative "
                    "catalyst labels. They are retained verbatim rather than "
                    "split into unsupported run-specific catalyst assignments."
                ),
                f"EVD_{SOURCE_ID}_S002_CATALYST",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_EXPANSION_001",
                SOURCE_ID,
                first_run,
                "run_split_uncertainty",
                "source_run",
                first_run,
                "run_summary",
                (
                    "Tables 10 and 11 expand 108 original-order records into "
                    "126 temperature/status conditions. Repeated order numbers "
                    "are retained as distinct compiled conditions."
                ),
                f"{method};{calculation}",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_OUTLIER_001",
                SOURCE_ID,
                f"{SOURCE_ID}_S001",
                "critical_data_gap",
                "reactor_process_gas",
                f"{SOURCE_ID}_S001_S01",
                "temperature_program_summary",
                (
                    "The compilation contains apparent transcription or range "
                    "anomalies, including parenthetical selected temperatures "
                    "outside printed ranges. Values are retained verbatim and "
                    "require primary-paper checks."
                ),
                f"EVD_{SOURCE_ID}_S001_RAW_GAS;{conclusion}",
            ),
        ]
    )
    return tables


def main() -> None:
    metadata = load_metadata()
    store = EvidenceStore()
    try:
        metric = publish_package(SOURCE_ID, build(metadata[SOURCE_ID], store))
    finally:
        store.close()
    result = {
        "batch_id": BATCH_NAME,
        "sources": [metric],
        "total_runs": metric["row_counts"]["source_run"],
        "status": "completed_needs_review",
    }
    output = BATCH_ROOT / f"batch_{BATCH_NUMBER:03d}_metrics.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
