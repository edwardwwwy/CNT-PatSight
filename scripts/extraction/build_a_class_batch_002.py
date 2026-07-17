#!/usr/bin/env python3
"""Build the second evidence-grounded A-class extraction batch.

The source-specific mappings in this file are authored from locally parsed
full text. Every package remains ``needs_review``.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from scripts.extraction.build_a_class_batch import (
    BATCH_ID,
    PACKAGE_ROOT,
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
    write_table,
    yield_row,
)
from scripts.validation.validate_tables import (
    DEFAULT_DICTIONARY,
    DEFAULT_SCHEMA,
    validate,
)


BATCH_NUMBER = 2
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_IDS = ("LIT_3D8F9EFA937173D0",)


def add_common_process(
    tables: dict[str, list[dict[str, str]]],
    run_id: str,
    calcination_c: int,
) -> None:
    reduction_c = 500 if calcination_c == 500 else 700
    tables["reactor_process_gas"].extend(
        [
            process_row(
                run_id,
                1,
                "reduction",
                reactor_type="stainless-steel fixed-bed continuous-flow micro-reactor",
                reactor_material="stainless steel",
                reactor_size_summary="9.1 mm inner diameter; 30 cm length",
                reactor_setup_summary="Single heating zone; K-type thermocouple axially centered in catalyst bed.",
                catalyst_loading_mass_g="0.3",
                temperature_setpoint_C=str(reduction_c),
                holding_time_min="90",
                pressure_original="atmospheric",
                pressure_kPa="101.325",
                reducing_gas="H2",
                reducing_gas_flow_original="40 mL/min",
                reducing_gas_flow_sccm="40",
                inert_gas="not_reported",
                cofeed_or_reactive_gas="not_applicable",
                gas_composition_summary="H2 reduction",
            ),
            process_row(
                run_id,
                2,
                "methane_decomposition",
                reactor_type="stainless-steel fixed-bed continuous-flow micro-reactor",
                reactor_material="stainless steel",
                reactor_size_summary="9.1 mm inner diameter; 30 cm length",
                reactor_setup_summary="Single heating zone; K-type thermocouple axially centered in catalyst bed.",
                catalyst_loading_mass_g="0.3",
                temperature_setpoint_C="700",
                holding_time_min="360",
                pressure_original="atmospheric",
                pressure_kPa="101.325",
                carbon_source="CH4",
                carbon_source_flow_original="CH4:N2 = 1.5:1; total flow 25 mL/min",
                carbon_source_flow_sccm="15",
                inert_gas="N2",
                inert_gas_flow_original="CH4:N2 = 1.5:1; total flow 25 mL/min",
                inert_gas_flow_sccm="10",
                total_flow_original="25 mL/min",
                total_flow_sccm="25",
                gas_composition_summary="CH4:N2 = 1.5:1",
                GHSV_or_residence_time="5000 mL h-1 gcat-1",
                process_note="Activity followed for up to 6 h on stream; exact figure endpoints require human confirmation.",
            ),
        ]
    )


def build_3d8(
    metadata: dict[str, Any],
    store: EvidenceStore,
) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "Catalyst preparation, calcination, reduction, methane "
                "decomposition, activity, BET, TEM and TGA evidence."
            ),
        )
    )
    tables["source_master"][0]["local_file_path"] = (
        f"data/interim/parsed_text/{source_id}/full_text.txt"
    )

    configurations = [
        {
            "code": "R01",
            "label": "20% Fe/Al2O3 impregnation; calcined 500 C",
            "method": "wet_impregnation",
            "calcination": 500,
            "nickel": 0,
            "bet": "155",
            "result": "steady methane conversion approximately 60% after the first 60 min",
            "conversion": "60",
        },
        {
            "code": "R02",
            "label": "20% Fe/Al2O3 sol-gel; calcined 500 C",
            "method": "sol_gel",
            "calcination": 500,
            "nickel": 0,
            "bet": "208.9",
            "result": "steady methane conversion approximately 50% after the first 60 min",
            "conversion": "50",
        },
        {
            "code": "R03",
            "label": "20% Fe/Al2O3 co-precipitation; calcined 500 C",
            "method": "co_precipitation",
            "calcination": 500,
            "nickel": 0,
            "bet": "237",
            "result": "steady methane conversion approximately 45% after the first 60 min",
            "conversion": "45",
        },
        {
            "code": "R04",
            "label": "20% Fe/Al2O3 impregnation; calcined 800 C",
            "method": "wet_impregnation",
            "calcination": 800,
            "nickel": 0,
            "bet": "95.5",
            "result": "conversion began near 55% and increased to approximately 60%",
            "conversion": "60",
        },
        {
            "code": "R05",
            "label": "20% Fe/Al2O3 sol-gel; calcined 800 C",
            "method": "sol_gel",
            "calcination": 800,
            "nickel": 0,
            "bet": "203.3",
            "result": "lower activity than the corresponding 500 C catalyst and conversion decreased with time on stream",
            "conversion": "",
        },
        {
            "code": "R06",
            "label": "20% Fe/Al2O3 co-precipitation; calcined 800 C",
            "method": "co_precipitation",
            "calcination": 800,
            "nickel": 0,
            "bet": "104.1",
            "result": "lower activity than the corresponding 500 C catalyst and conversion decreased with time on stream",
            "conversion": "",
        },
        {
            "code": "R07",
            "label": "20% Fe-5% Ni/Al2O3 impregnation; calcined 500 C",
            "method": "wet_impregnation",
            "calcination": 500,
            "nickel": 5,
            "bet": "147.7",
        },
        {
            "code": "R08",
            "label": "20% Fe-5% Ni/Al2O3 sol-gel; calcined 500 C",
            "method": "sol_gel",
            "calcination": 500,
            "nickel": 5,
            "bet": "163.1",
        },
        {
            "code": "R09",
            "label": "20% Fe-5% Ni/Al2O3 co-precipitation; calcined 500 C",
            "method": "co_precipitation",
            "calcination": 500,
            "nickel": 5,
            "bet": "215.3",
        },
        {
            "code": "R10",
            "label": "20% Fe-10% Ni/Al2O3 impregnation; calcined 500 C",
            "method": "wet_impregnation",
            "calcination": 500,
            "nickel": 10,
            "bet": "140.6",
        },
        {
            "code": "R11",
            "label": "20% Fe-10% Ni/Al2O3 sol-gel; calcined 500 C",
            "method": "sol_gel",
            "calcination": 500,
            "nickel": 10,
            "bet": "151.2",
        },
        {
            "code": "R12",
            "label": "20% Fe-10% Ni/Al2O3 co-precipitation; calcined 500 C",
            "method": "co_precipitation",
            "calcination": 500,
            "nickel": 10,
            "bet": "248.8",
        },
    ]

    for config in configurations:
        run_id = f"{source_id}_{config['code']}"
        nickel = int(config["nickel"])
        promoted_result = (
            "Ni addition increased methane conversion and hydrogen yield by approximately 10%; "
            "10 wt% Ni was only slightly higher than 5 wt% Ni."
        )
        result = str(config.get("result") or promoted_result)
        tables["source_run"].append(
            run_row(
                source_id,
                str(config["code"]),
                str(config["label"]),
                (
                    f"{config['method']} catalyst, calcined at "
                    f"{config['calcination']} C; {result}."
                ),
                "medium" if nickel or not config.get("conversion") else "high",
            )
        )

        if config["method"] == "wet_impregnation":
            preparation_detail = (
                "Stoichiometric metal-nitrate solution added to alumina with "
                "constant stirring at 85 C; dried at 120 C for about 13 h."
            )
            precursor = "Fe(NO3)3 hydrate; Al2O3 support"
            if nickel:
                precursor += "; Ni(NO3)2 hydrate"
        elif config["method"] == "co_precipitation":
            preparation_detail = (
                "Fe and Al nitrate salts co-precipitated with 10% ammonia to "
                "pH 9 at 80 C; filtered, washed with water and acetone, then "
                "dried at 120 C overnight."
            )
            precursor = "Fe nitrate; Al nitrate; ammonia"
            if nickel:
                precursor += "; Ni nitrate"
        else:
            preparation_detail = (
                "Disperal P2 boehmite dispersed in water with Triton X100; "
                "metal-nitrate solution mixed into the gel, shaped as 2 mm "
                "stripes, dried overnight at room temperature and 12 h at 90 C."
            )
            precursor = "Disperal P2 boehmite; Fe nitrate; Triton X100"
            if nickel:
                precursor += "; Ni nitrate"

        active_metals = "Fe; Ni" if nickel else "Fe"
        catalyst_label = (
            f"20 wt% Fe-{nickel} wt% Ni/Al2O3"
            if nickel
            else "20 wt% Fe/Al2O3"
        )
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                catalyst_label=catalyst_label,
                active_metals=active_metals,
                support_material="Al2O3",
                promoter="Ni" if nickel else "not_applicable",
                metal_ratio_original=(
                    f"20 wt% Fe + {nickel} wt% Ni relative to Al2O3"
                    if nickel
                    else "20 wt% Fe relative to Al2O3"
                ),
                metal_ratio_standardized=(
                    f"Fe:Ni = {20}:{nickel} by reported loading"
                    if nickel
                    else "20 wt% Fe/Al2O3"
                ),
                precursor_summary=precursor,
                preparation_method=str(config["method"]),
                preparation_modifier=(
                    "surfactant_assisted"
                    if config["method"] == "sol_gel"
                    else "not_applicable"
                ),
                preparation_detail=preparation_detail,
                drying_condition=(
                    "120 C for about 13 h"
                    if config["method"] == "wet_impregnation"
                    else (
                        "120 C overnight"
                        if config["method"] == "co_precipitation"
                        else "room temperature overnight; then 90 C for 12 h"
                    )
                ),
                calcination_condition=(
                    f"{config['calcination']} C in air for 3 h"
                ),
                reduction_condition=(
                    f"H2 at {500 if config['calcination'] == 500 else 700} C "
                    "for 90 min; 40 mL/min"
                ),
                BET_surface_area_m2_g=str(config["bet"]),
                phase_or_state_summary=(
                    "Impregnated samples contained more reducible iron oxides; "
                    "sol-gel/co-precipitated samples formed more Fe-Al spinel. "
                    "Ni promotion introduced Ni-Fe oxide/alloy precursor phases."
                ),
                deactivation_summary=(
                    "Ni promotion improved stability by balancing carbon formation, diffusion and precipitation."
                    if nickel
                    else "High-temperature sol-gel and co-precipitated catalysts deactivated with time on stream."
                ),
            )
        )
        add_common_process(tables, run_id, int(config["calcination"]))

        conversion = str(config.get("conversion") or "")
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="methane_conversion",
                yield_original=(
                    f"approximately {conversion}% methane conversion"
                    if conversion
                    else result
                ),
                yield_definition_original=(
                    "CH4 conversion calculated from inlet and outlet methane; "
                    "hydrogen yield calculated from produced H2 relative to methane feed."
                ),
                yield_calculation_method="Reported inlet/outlet gas analysis by online GC-TCD",
                yield_value_standardized=conversion,
                yield_unit_standardized="%" if conversion else "qualitative_only",
                carbon_source_conversion_percent=conversion,
                secondary_result_summary=result,
                CNT_type_reported="carbon nanotubes and carbon nanofibres",
                CNT_type_confirmed="mixed_CNT_CNF",
                product_mixture_summary=(
                    "Source terminology alternates between CNT and carbon nanofibre; "
                    "spent catalyst and deposited filamentous carbon remain mixed."
                ),
                CNT_type_evidence="TEM of spent catalysts; TGA of deposited carbon.",
                outer_diameter_range_nm="16-20" if nickel else "not_reported",
                length_summary=(
                    "Abstract reports 32-34 nm as CNT length; results describe "
                    "carbon nanofibre dimensions near 30 nm. Dimensional label is uncertain."
                ),
                morphology="tip-growth filamentous carbon; metal particle at fibre/tube tip",
                TGA_carbon_content_wt_percent="not_reported",
                purity_basis="not_reported",
                residue_summary="spent Fe or Fe-Ni/Al2O3 catalyst retained with deposited carbon",
                characterization_methods="TEM; TGA; XRD; BET; TPR; online GC-TCD",
            )
        )
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                reactor_capacity_or_throughput="0.3 g catalyst laboratory continuous-flow test",
                continuous_operation_time_h="6",
                catalyst_lifetime_or_reuse="stable up to 6 h on stream according to activity results",
                cost_driver_summary="Fe/Al2O3 base catalyst; Ni addition and H2 reduction add material and gas demand; no quantitative cost reported.",
                safety_risk="CH4 and H2 at 700 C; hot fixed-bed reactor",
                emission_or_waste="Effluent gas analyzed by GC; unreacted methane and deposited spent catalyst/carbon not quantified as waste.",
            )
        )

        catalyst_span = {
            "wet_impregnation": "SPAN_2529A61625E71DEB1184",
            "co_precipitation": "SPAN_3B51E0A5C4A4E241252C",
            "sol_gel": "SPAN_10910CE3EE33818F454E",
        }[str(config["method"])]
        result_span = (
            "SPAN_2621FDD38E6424E6C1B3"
            if nickel
            else "SPAN_B4196FCDA88592E1B97D"
        )
        bet_span = (
            "SPAN_16D47E88B691406CB11E"
            if nickel
            else "SPAN_1E6ED12BFD44E61CA028"
        )
        evidence_specs = [
            (
                "CAT_PREP",
                "catalyst_system",
                f"{run_id}_CAT",
                "precursor_summary;preparation_method;preparation_modifier;preparation_detail;drying_condition;calcination_condition",
                catalyst_span,
                "Catalyst preparation route and thermal treatment.",
            ),
            (
                "CAT_COMPOSITION",
                "catalyst_system",
                f"{run_id}_CAT",
                "catalyst_label;active_metals;support_material;promoter;metal_ratio_original;metal_ratio_standardized",
                (
                    "SPAN_B207697D04401DE82B7E"
                    if nickel
                    else "SPAN_2529A61625E71DEB1184"
                ),
                "Reported Fe loading and, where applicable, Ni loading.",
            ),
            (
                "CAT_BET",
                "catalyst_system",
                f"{run_id}_CAT",
                "BET_surface_area_m2_g;phase_or_state_summary",
                bet_span,
                "Reported BET table and catalyst phase discussion.",
            ),
            (
                "PROC_REDUCTION",
                "reactor_process_gas",
                f"{run_id}_S01",
                "reactor_type;reactor_size_summary;catalyst_loading_mass_g;temperature_setpoint_C;holding_time_min;reducing_gas;reducing_gas_flow_original",
                "SPAN_012941621DFC120E23E0",
                "Reduction temperature, hydrogen flow and duration.",
            ),
            (
                "PROC_REDUCTION_SETUP",
                "reactor_process_gas",
                f"{run_id}_S01",
                "reactor_type;reactor_size_summary;reactor_setup_summary;catalyst_loading_mass_g;pressure_original",
                "SPAN_077A1EE45AF2048345DF",
                "The reduction occurred in the reported fixed-bed reactor using the same 0.3 g catalyst charge.",
            ),
            (
                "PROC_REACTOR",
                "reactor_process_gas",
                f"{run_id}_S02",
                "reactor_type;reactor_size_summary;reactor_setup_summary;catalyst_loading_mass_g;pressure_original;carbon_source;inert_gas;gas_composition_summary",
                "SPAN_077A1EE45AF2048345DF",
                "Fixed-bed reactor, catalyst charge, pressure and methane/nitrogen feed.",
            ),
            (
                "PROC_TEMPERATURE",
                "reactor_process_gas",
                f"{run_id}_S02",
                "temperature_setpoint_C",
                "SPAN_012941621DFC120E23E0",
                "Reported fixed methane-decomposition reaction temperature.",
            ),
            (
                "PROC_FLOW",
                "reactor_process_gas",
                f"{run_id}_S02",
                "carbon_source_flow_original;inert_gas_flow_original;total_flow_original;gas_composition_summary;GHSV_or_residence_time",
                "SPAN_76C3BDC58D29BDC33F90",
                "Figure caption reports methane/nitrogen ratio, total flow and space velocity.",
            ),
            (
                "PROC_DURATION",
                "reactor_process_gas",
                f"{run_id}_S02",
                "holding_time_min;process_note",
                "SPAN_1A6F77DF7AE2BA732637",
                "Activity results followed catalyst stability for six hours on stream.",
            ),
            (
                "YIELD",
                "yield_quality",
                f"{run_id}_PROD",
                "primary_yield_metric;yield_original;yield_definition_original;carbon_source_conversion_percent;secondary_result_summary",
                result_span,
                "Run-series methane conversion and Ni-promotion result.",
            ),
            (
                "PRODUCT",
                "yield_quality",
                f"{run_id}_PROD",
                "CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;outer_diameter_range_nm;length_summary;morphology",
                (
                    "SPAN_1D170D86862DDEE3698C"
                    if nickel
                    else "SPAN_0A5E39D922BB972B728E"
                ),
                "TEM morphology and reported CNT/CNF dimensions.",
            ),
            (
                "PRODUCT_ABSTRACT",
                "yield_quality",
                f"{run_id}_PROD",
                "CNT_type_reported;product_mixture_summary;length_summary;morphology",
                "SPAN_1A6F77DF7AE2BA732637",
                "Abstract-level CNT terminology, dimension and tip-growth statement.",
            ),
            (
                "SCALE",
                "cost_scale_review",
                run_id,
                "scale_level_demonstrated;reactor_capacity_or_throughput",
                "SPAN_077A1EE45AF2048345DF",
                "Laboratory fixed-bed setup and 0.3 g catalyst charge.",
                "high",
                "inferred",
            ),
            (
                "DURATION",
                "cost_scale_review",
                run_id,
                "continuous_operation_time_h;catalyst_lifetime_or_reuse",
                "SPAN_1A6F77DF7AE2BA732637",
                "Reported six-hour on-stream stability.",
            ),
            (
                "COST_SAFETY_ASSESSMENT",
                "cost_scale_review",
                run_id,
                "cost_driver_summary;safety_risk;emission_or_waste",
                "SPAN_077A1EE45AF2048345DF",
                "Review assessment derived from the reported methane, hydrogen, temperature and fixed-bed operating context.",
                "medium",
                "review_assessment",
            ),
        ]
        for spec in evidence_specs:
            suffix, table, record_id, fields, span_id, summary, *options = spec
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
                    *(options or []),
                )
            )

    first_run = f"{source_id}_R01"
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{source_id}_ISSUE_DIMENSION_001",
                source_id,
                first_run,
                "definition_ambiguity",
                "yield_quality",
                f"{first_run}_PROD",
                "length_summary",
                (
                    "The abstract reports CNT length of 32-34 nm, while the "
                    "results describe carbon nanofibre dimensions near 30 nm; "
                    "the dimension and CNT/CNF terminology require source-image review."
                ),
                (
                    f"EVD_{first_run}_PRODUCT;"
                    f"EVD_{first_run}_PRODUCT_ABSTRACT"
                ),
                "high",
            ),
            issue_row(
                f"{source_id}_ISSUE_GRAPH_001",
                source_id,
                first_run,
                "critical_data_gap",
                "yield_quality",
                f"{first_run}_PROD",
                "yield_original",
                (
                    "Several run-specific methane conversion and hydrogen-yield "
                    "values are only graph-readable. Qualitative trends are "
                    "preserved instead of inventing numeric values."
                ),
                f"EVD_{first_run}_YIELD",
            ),
            issue_row(
                f"{source_id}_ISSUE_TGA_001",
                source_id,
                first_run,
                "critical_data_gap",
                "yield_quality",
                f"{first_run}_PROD",
                "TGA_carbon_content_wt_percent",
                (
                    "TGA establishes relative deposited-carbon differences but "
                    "the main parsed text does not provide run-specific weight-loss values."
                ),
                f"EVD_{first_run}_PRODUCT",
            ),
        ]
    )
    return tables


BUILDERS = {"LIT_3D8F9EFA937173D0": build_3d8}


def publish_package(
    source_id: str,
    package: dict[str, list[dict[str, str]]],
) -> dict[str, Any]:
    output_dir = PACKAGE_ROOT / source_id
    if output_dir.exists():
        raise FileExistsError(f"Package already exists: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{source_id}.", dir=output_dir.parent)
    )
    try:
        for table in TABLES:
            write_table(temporary, table, package[table])
        result = validate(temporary, DEFAULT_SCHEMA, DEFAULT_DICTIONARY)
        if result:
            raise RuntimeError(f"Eight-table validation failed for {source_id}")
        shutil.move(str(temporary), str(output_dir))
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {
        "source_id": source_id,
        "output_path": output_dir.relative_to(ROOT).as_posix(),
        "row_counts": {table: len(package[table]) for table in TABLES},
        "status": "needs_review",
    }


def main() -> None:
    metadata = load_metadata()
    store = EvidenceStore()
    metrics: list[dict[str, Any]] = []
    try:
        for source_id in SOURCE_IDS:
            metrics.append(
                publish_package(
                    source_id,
                    BUILDERS[source_id](metadata[source_id], store),
                )
            )
    finally:
        store.close()
    result = {
        "batch_id": BATCH_NAME,
        "sources": metrics,
        "total_runs": sum(
            item["row_counts"]["source_run"] for item in metrics
        ),
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
