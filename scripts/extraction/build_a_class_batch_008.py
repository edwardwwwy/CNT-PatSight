#!/usr/bin/env python3
"""Build the eighth evidence-grounded A-class extraction batch."""
from __future__ import annotations

import json
from typing import Any

from scripts.extraction.batch_common import (
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


BATCH_NUMBER = 8
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ID = "LIT_E59DADD0A138DCAC"

TEMPERATURE_RUNS = [
    (740, 0, "0.00"),
    (750, 232, "0.09"),
    (780, 702, "0.26"),
    (800, 810, "0.30"),
    (830, 675, "0.25"),
    (840, 270, "0.10"),
    (850, 0, "0.00"),
]

CONCENTRATION_RUNS = [
    (1000, 243, "0.09", "0.10"),
    (2000, 567, "0.21", "0.21"),
    (3000, 864, "0.32", "0.35"),
    (4000, 1174, "0.43", "0.49"),
    (5000, 1472, "0.55", "0.63"),
    (6000, 1662, "0.62", "0.76"),
]

FLOW_RUNS = [
    (50, 81, "0.03"),
    (100, 267, "0.10"),
    (150, 432, "0.16"),
    (200, 567, "0.21"),
    (250, 643, "0.24"),
    (300, 686, "0.25"),
    (350, 700, "0.26"),
]


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
    confidence: str = "high",
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
            confidence,
            value_status,
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


def common_catalyst(run_id: str) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label="10 mass% Fe/CaCO3",
        active_metals="Fe",
        support_material="CaCO3",
        promoter="not_applicable",
        metal_ratio_original="10 mass% Fe on CaCO3",
        metal_ratio_standardized="10 wt% Fe/CaCO3",
        precursor_summary="iron nitrate; citric acid; ammonia; CaCO3",
        preparation_method="modified_wet_impregnation",
        preparation_modifier="citric-acid complexation; ammonia pH adjustment",
        preparation_detail=(
            "Iron nitrate and citric acid were mixed at approximately 1:1 "
            "molar ratio in deionized water; ammonia was added dropwise to "
            "neutral pH; after 6 h CaCO3 was stirred in to form a dry slurry."
        ),
        drying_condition="slurry left overnight",
        calcination_condition="500 C for 6-12 h in a muffle furnace",
        reduction_condition="H2 present during CNT growth; no separate reduction reported",
        activation_condition="in-situ H2-assisted maintenance of reduced iron",
        post_preparation_condition="calcined supported catalyst",
        phase_or_state_summary="Fe species supported on CaCO3; exact phase not reported",
        dispersion_summary="not_reported",
        deactivation_summary="carbon coverage/poisoning discussed at high CO2 concentration",
    )


def common_process(
    run_id: str,
    temperature_c: int,
    carbon_flow: str,
    gas_summary: str,
) -> list[dict[str, str]]:
    setup = (
        "Vertical quartz/silica tube in an electric furnace; catalyst on quartz "
        "wool; swirled coiled gas mixer, condenser and two product cyclones."
    )
    return [
        process_row(
            run_id,
            1,
            "argon_purge",
            reactor_type="modified swirled floating catalyst CVD reactor",
            reactor_material="quartz or silica",
            reactor_setup_summary=setup,
            catalyst_loading_mass_g="approximately 10",
            pressure_original="not_reported",
            pressure_kPa="",
            inert_gas="Ar",
            inert_gas_flow_original="not_reported",
            gas_composition_summary="argon purge to remove oxygen",
        ),
        process_row(
            run_id,
            2,
            "CO2_H2_CNT_growth",
            reactor_type="modified swirled floating catalyst CVD reactor",
            reactor_material="quartz or silica",
            reactor_setup_summary=setup,
            catalyst_loading_mass_g="approximately 10",
            temperature_setpoint_C=str(temperature_c),
            holding_time_min="45",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source="CO2 (99.99% minimum purity)",
            carbon_source_flow_original=carbon_flow,
            reducing_gas="H2 (95.5% minimum purity)",
            reducing_gas_flow_original="not_reported",
            inert_gas="not_applicable during reported growth mixture",
            cofeed_or_reactive_gas="H2",
            total_flow_original="not_reported",
            gas_composition_summary=gas_summary,
            process_note=(
                "Forty-five-minute production condition; result is the mean "
                "of four replicate runs under similar conditions."
            ),
        ),
    ]


def common_cost(run_id: str, throughput: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="lab_batch",
        scale_level_claimed="scale_up_potential",
        scale_evidence_summary=(
            "Approximately 10 g supported catalyst in a modified vertical "
            "SFCCVD laboratory reactor; large-scale CVD potential is discussed."
        ),
        reactor_capacity_or_throughput=throughput,
        continuous_operation_time_h="0.75",
        catalyst_lifetime_or_reuse="not_reported",
        batch_stability="reported value is the mean of four replicate runs",
        scale_up_issue=(
            "CO2/H2 delivery, heat demand, catalyst deactivation, product "
            "collection and acid purification require scale-up assessment."
        ),
        cost_driver_summary=(
            "Iron nitrate, CaCO3, citric acid, ammonia, CO2, H2, argon, "
            "furnace energy, cyclones and nitric-acid purification; no "
            "quantitative production cost reported."
        ),
        safety_risk=(
            "Hydrogen with high-temperature equipment; nitric acid at 120 C; "
            "airborne or residual CNT exposure requires controls."
        ),
        emission_or_waste=(
            "CO/CO2 process off-gas and nitric-acid/wash-water waste; exact "
            "amounts and gas conversion were not reported."
        ),
    )


def common_yield(
    run_id: str,
    mass_mg: int,
    rate_mg_s: str,
    representative_800: bool = False,
    simulated_rate: str = "",
) -> dict[str, str]:
    if mass_mg == 0:
        cnt_reported = "no CNT product"
        confirmed = "not_applicable"
        mixture = "No CNTs were collected under the reported condition."
    elif representative_800:
        cnt_reported = "CNTs"
        confirmed = "MWCNTs"
        mixture = (
            "Hollow CNT product; absence of Raman RBM supports multi-walled "
            "identity for the representative 800 C sample."
        )
    else:
        cnt_reported = "CNTs"
        confirmed = "not_applicable"
        mixture = (
            "CNT product reported; source-level MWCNT identification was not "
            "mapped to this individual condition."
        )

    secondary = f"Actual production rate {rate_mg_s} mg/s."
    if simulated_rate:
        secondary += f" Simulated production rate {simulated_rate} mg/s."

    return yield_row(
        run_id,
        primary_yield_metric="CNT_product_mass_per_45_min_batch",
        yield_original=(
            f"{mass_mg} mg CNTs collected; actual production rate "
            f"{rate_mg_s} mg/s"
        ),
        yield_definition_original=(
            "Weight of CNTs produced during 45 minutes; mean of four "
            "replicate runs under similar experimental conditions."
        ),
        yield_calculation_method="reported gravimetric product mass and rate",
        yield_value_standardized=str(mass_mg),
        yield_unit_standardized="mg per 45-min batch",
        yield_standardization_note=(
            "Reported batch mass retained without catalyst or feed normalization."
        ),
        secondary_result_summary=secondary,
        CNT_type_reported=cnt_reported,
        CNT_type_confirmed=confirmed,
        product_mixture_summary=mixture,
        CNT_type_evidence=(
            "TEM hollow morphology and absence of Raman RBM at 800 C."
            if representative_800
            else "Run-specific CNT wall count not reported."
        ),
        wall_number_summary="multi-walled" if representative_800 else "not_reported",
        morphology=(
            "hollow tubular structures"
            if representative_800
            else ("no product" if mass_mg == 0 else "not_reported")
        ),
        Raman_ratio_type="ID/IG" if representative_800 else "not_reported",
        Raman_ratio_value="0.71" if representative_800 else "not_reported",
        RBM_peak_reported="absent" if representative_800 else "not_reported",
        purity_basis="as-produced product; exact collected-mass basis unclear",
        residue_summary="not_reported",
        amorphous_carbon_level=(
            "D-band present; not quantitatively separated"
            if representative_800
            else "not_reported"
        ),
        characterization_methods=(
            "TEM; Raman spectroscopy" if representative_800 else "not_reported"
        ),
        post_treatment_or_purification=(
            "General method: 10% nitric acid purification; table mass appears "
            "to describe produced/crude CNTs."
        ),
        purification_condition=(
            "10% nitric acid, gentle vortexing for 2.5 h at 120 C; filter, "
            "wash to pH 7 and dry at 80 C overnight."
        ),
    )


def add_run_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    table_span: str,
    trend_span: str,
    yield_summary: str,
    representative_800: bool = False,
    simulated: bool = False,
) -> None:
    specs = [
        (
            "CAT",
            "catalyst_system",
            f"{run_id}_CAT",
            "record_level",
            "SPAN_C6619B774FEDF06283B3",
            "Ten-mass-percent Fe/CaCO3 catalyst preparation.",
            "reported",
        ),
        (
            "SETUP",
            "reactor_process_gas",
            f"{run_id}_S01",
            "reactor_type;reactor_material;reactor_setup_summary;"
            "catalyst_loading_mass_g",
            "SPAN_F4F67553E2820BEC010A",
            "Modified SFCCVD setup and approximate catalyst charge.",
            "reported",
        ),
        (
            "SETUP_GROWTH",
            "reactor_process_gas",
            f"{run_id}_S02",
            "reactor_type;reactor_material;reactor_setup_summary;"
            "catalyst_loading_mass_g",
            "SPAN_F4F67553E2820BEC010A",
            "Modified SFCCVD growth setup and approximate catalyst charge.",
            "reported",
        ),
        (
            "GAS",
            "reactor_process_gas",
            f"{run_id}_S02",
            "carbon_source;reducing_gas;temperature_setpoint_C",
            "SPAN_DF13EC90522CE3B95811",
            "Argon purge and UHP CO2/H2 growth-gas description.",
            "reported",
        ),
        (
            "PROC_TABLE",
            "reactor_process_gas",
            f"{run_id}_S02",
            "temperature_setpoint_C;holding_time_min;"
            "carbon_source_flow_original;gas_composition_summary",
            table_span,
            "Appendix table condition linked to the run-specific growth stage.",
            "reported",
        ),
        (
            "YIELD",
            "yield_quality",
            f"{run_id}_PROD",
            "primary_yield_metric;yield_original;yield_definition_original;"
            "yield_value_standardized;yield_unit_standardized;"
            "secondary_result_summary",
            table_span,
            yield_summary,
            "reported",
        ),
        (
            "TREND",
            "yield_quality",
            f"{run_id}_PROD",
            "secondary_result_summary",
            trend_span,
            "Narrative interpretation of the experimental series.",
            "reported",
        ),
        (
            "PURIFICATION",
            "yield_quality",
            f"{run_id}_PROD",
            "post_treatment_or_purification;purification_condition;"
            "purity_basis",
            "SPAN_DF13EC90522CE3B95811",
            "General nitric-acid purification procedure.",
            "reported",
        ),
        (
            "COST",
            "cost_scale_review",
            run_id,
            "record_level",
            "SPAN_F4F67553E2820BEC010A",
            "Review assessment from reported laboratory setup and materials.",
            "review_assessment",
        ),
    ]
    for suffix, table, record_id, fields, span, summary, status in specs:
        append_evidence(
            tables,
            store,
            run_id,
            suffix,
            table,
            record_id,
            fields,
            span,
            summary,
            value_status=status,
        )
    if representative_800:
        append_evidence(
            tables,
            store,
            run_id,
            "TEM",
            "yield_quality",
            f"{run_id}_PROD",
            "CNT_type_reported;CNT_type_confirmed;CNT_type_evidence;"
            "wall_number_summary;morphology",
            "SPAN_09379E9BBA4C7E3EDCEA",
            "Representative 800 C TEM shows hollow CNT structures.",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "RAMAN",
            "yield_quality",
            f"{run_id}_PROD",
            "CNT_type_confirmed;CNT_type_evidence;wall_number_summary;"
            "Raman_ratio_type;Raman_ratio_value;RBM_peak_reported;"
            "amorphous_carbon_level;characterization_methods",
            "SPAN_48527CF0AC6FC847A1C6",
            "Representative 800 C Raman peaks, absent RBM and ID/IG 0.71.",
        )
    if simulated:
        append_evidence(
            tables,
            store,
            run_id,
            "SIMULATED",
            "yield_quality",
            f"{run_id}_PROD",
            "secondary_result_summary",
            table_span,
            "Appendix table reports a simulated production rate separately.",
            value_status="calculated",
        )


def build(
    metadata: dict[str, Any],
    store: EvidenceStore,
) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "Doctoral dissertation Chapter 3 methods, Chapter 4 CNT "
                "production analysis, Appendix B production tables, and "
                "source-level wastewater/safety observations."
            ),
        )
    )
    tables["source_master"][0]["local_file_path"] = (
        f"data/interim/parsed_text/by_source/{SOURCE_ID}.parsed.json"
    )
    tables["source_master"][0]["notes"] += (
        " Source document is a doctoral dissertation; downstream wastewater "
        "experiments are not represented as CNT-production runs."
    )

    for index, (temperature, mass, rate) in enumerate(
        TEMPERATURE_RUNS, start=1
    ):
        code = f"T{index:02d}"
        run_id = f"{SOURCE_ID}_{code}"
        representative = temperature == 800
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                code,
                f"temperature series: {temperature} C; CO2 400 mL/min; 45 min",
                (
                    f"Mean of four replicate SFCCVD runs; {mass} mg CNTs and "
                    f"{rate} mg/s production rate."
                ),
            )
        )
        tables["catalyst_system"].append(common_catalyst(run_id))
        tables["reactor_process_gas"].extend(
            common_process(
                run_id,
                temperature,
                "400 mL/min",
                "CO2/H2 reaction mixture; CO2 flow 400 mL/min; H2 flow not reported",
            )
        )
        tables["yield_quality"].append(
            common_yield(run_id, mass, rate, representative)
        )
        tables["cost_scale_review"].append(
            common_cost(run_id, f"{mass} mg CNTs per 45-min batch")
        )
        add_run_evidence(
            tables,
            store,
            run_id,
            "SPAN_58283BFF530005B2BD28",
            "SPAN_33B03226824C98A7514F",
            "Appendix B1 temperature-specific mass and production rate.",
            representative,
        )

    for index, (concentration, mass, actual, simulated) in enumerate(
        CONCENTRATION_RUNS, start=1
    ):
        code = f"C{index:02d}"
        run_id = f"{SOURCE_ID}_{code}"
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                code,
                f"CO2 concentration series: {concentration} ppm; 800 C; 45 min",
                (
                    f"Mean of four replicate SFCCVD runs; {mass} mg CNTs, "
                    f"{actual} mg/s actual and {simulated} mg/s simulated rate."
                ),
            )
        )
        tables["catalyst_system"].append(common_catalyst(run_id))
        tables["reactor_process_gas"].extend(
            common_process(
                run_id,
                800,
                "not_reported",
                (
                    f"CO2/H2 reaction mixture; CO2 concentration "
                    f"{concentration} ppm; total and component flows not reported"
                ),
            )
        )
        tables["yield_quality"].append(
            common_yield(run_id, mass, actual, simulated_rate=simulated)
        )
        tables["cost_scale_review"].append(
            common_cost(run_id, f"{mass} mg CNTs per 45-min batch")
        )
        add_run_evidence(
            tables,
            store,
            run_id,
            "SPAN_58283BFF530005B2BD28",
            "SPAN_2F5E50779789DDFA6B73",
            "Appendix B2 concentration-specific mass, actual and simulated rate.",
            simulated=True,
        )

    for index, (flow, mass, rate) in enumerate(FLOW_RUNS, start=1):
        code = f"F{index:02d}"
        run_id = f"{SOURCE_ID}_{code}"
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                code,
                f"CO2 flow series: {flow} mL/min; 800 C; 45 min",
                (
                    f"Mean of four replicate SFCCVD runs; {mass} mg CNTs and "
                    f"{rate} mg/s production rate."
                ),
            )
        )
        tables["catalyst_system"].append(common_catalyst(run_id))
        tables["reactor_process_gas"].extend(
            common_process(
                run_id,
                800,
                f"{flow} mL/min",
                (
                    f"CO2/H2 reaction mixture; CO2 flow {flow} mL/min; "
                    "H2 flow not reported"
                ),
            )
        )
        tables["yield_quality"].append(common_yield(run_id, mass, rate))
        tables["cost_scale_review"].append(
            common_cost(run_id, f"{mass} mg CNTs per 45-min batch")
        )
        add_run_evidence(
            tables,
            store,
            run_id,
            "SPAN_A6B3607CD6BED6097493",
            "SPAN_B962A36212D63C98E3D7",
            "Appendix B3 flow-specific mass and production rate.",
        )

    downstream = add_observation(
        tables,
        store,
        "DOWNSTREAM_WASTEWATER",
        "SPAN_4CF65822FFAD753613DD",
        (
            "Downstream brewery-wastewater tests reported 96.0% COD removal "
            "and 5 NTU residual turbidity for the best CNT-containing treatment "
            "scheme; these tests are not CNT-production runs."
        ),
    )
    health = add_observation(
        tables,
        store,
        "HEALTH_RISK",
        "SPAN_50E5D4B033F84E53D7EF",
        (
            "The dissertation reviews possible residual-CNT health effects "
            "including cancer, granulomas, inflammation and fibrosis."
        ),
    )
    hydrogen = add_observation(
        tables,
        store,
        "HYDROGEN_ROLE",
        "SPAN_DAD14D18DEA0BC99CA8F",
        (
            "Hydrogen is described as helping maintain reduced iron and "
            "alleviate carbon poisoning, but its run-specific flow is absent."
        ),
    )

    t04 = f"{SOURCE_ID}_T04"
    c01 = f"{SOURCE_ID}_C01"
    f07 = f"{SOURCE_ID}_F07"
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_MASS_BASIS_001",
                SOURCE_ID,
                t04,
                "definition_ambiguity",
                "yield_quality",
                f"{t04}_PROD",
                "purity_basis",
                (
                    "Appendix B calls the value weight of CNTs produced, while "
                    "the methods separately describe nitric-acid purification. "
                    "Whether table masses are crude or purified is unclear."
                ),
                f"EVD_{t04}_YIELD;EVD_{t04}_PURIFICATION",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CONCENTRATION_001",
                SOURCE_ID,
                c01,
                "critical_data_gap",
                "reactor_process_gas",
                f"{c01}_S02",
                "gas_composition_summary",
                (
                    "The CO2 concentration series reports ppm values but not "
                    "the ppm basis, total flow, H2 flow or balance gas."
                ),
                f"EVD_{c01}_YIELD;{hydrogen}",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_TREND_001",
                SOURCE_ID,
                f07,
                "definition_ambiguity",
                "yield_quality",
                f"{f07}_PROD",
                "secondary_result_summary",
                (
                    "Measured total mass and actual rate still increase through "
                    "350 mL/min and 6000 ppm, while the narrative says high flow "
                    "or concentration reduces production. This appears to refer "
                    "to marginal rate per feed or an extrapolated regime."
                ),
                (
                    f"EVD_{f07}_YIELD;EVD_{f07}_TREND;"
                    f"EVD_{SOURCE_ID}_C06_YIELD;"
                    f"EVD_{SOURCE_ID}_C06_TREND"
                ),
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CHARACTERIZATION_001",
                SOURCE_ID,
                t04,
                "CNT_type_uncertainty",
                "yield_quality",
                f"{t04}_PROD",
                "CNT_type_confirmed",
                (
                    "TEM/Raman are reported for a representative 800 C product "
                    "without a complete gas-condition label. MWCNT confirmation "
                    "is attached only to the closest 800 C, 400 mL/min run and "
                    "must not be generalized across the other 800 C series."
                ),
                f"EVD_{t04}_TEM;EVD_{t04}_RAMAN",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_LOADING_REPLICATES_001",
                SOURCE_ID,
                t04,
                "definition_ambiguity",
                "reactor_process_gas",
                f"{t04}_S02",
                "catalyst_loading_mass_g",
                (
                    "Catalyst loading is approximately 10 g and Appendix values "
                    "are averages of four replicate runs; replicate-level raw "
                    "measurements and exact catalyst masses are unavailable."
                ),
                f"EVD_{t04}_SETUP;EVD_{t04}_YIELD",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_DOWNSTREAM_001",
                SOURCE_ID,
                "not_applicable",
                "definition_ambiguity",
                "source_master",
                SOURCE_ID,
                "source_section_scope",
                (
                    "Nitric-acid purification of produced CNTs and concentrated "
                    "HCl functionalisation for wastewater use are distinct. "
                    "Downstream performance and health evidence are observations, "
                    "not additional CNT-production runs."
                ),
                f"{downstream};{health}",
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
    output = REPORT_ROOT / f"batch_{BATCH_NUMBER:03d}_metrics.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
