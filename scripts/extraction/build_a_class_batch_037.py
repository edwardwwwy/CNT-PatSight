#!/usr/bin/env python3
"""Build the thirty-seventh evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 37
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ID = "LIT_665FCAE5A73EA1BB"
HTML_REF = "data/raw/literature/html/LIT_665FCAE5A73EA1BB.html"

ABSTRACT_SPAN = "SPAN_B48B7001A0FAFD14878B"
METHOD_SPAN = "SPAN_4E7704077A262E5720A9"
ETHYLENE_SPAN = "SPAN_19E5304B39106B072DF3"
HYDROGEN_SCAN_SPAN = "SPAN_0067855E4C9CB4BDBE26"
REGIME_SPAN = "SPAN_A56CCE6A25BB3BE503E8"
OPTIMAL_SPAN = "SPAN_0D0AA86996E54B9D7ACA"
CONCLUSION_SPAN = "SPAN_882B25BED117D7973C58"

RUNS: list[dict[str, Any]] = [
    {
        "code": "C2H4_1000_OPTIMUM_0P24",
        "series": "ethylene",
        "temp": 1000,
        "ethylene": "0.24 vol%",
        "hydrogen": "0 vol%",
        "yield": "1.05 cm2/L",
        "outcome": "near-maximum yield and minimum R90 about 65 kOhm/sq",
    },
    {
        "code": "C2H4_1000_PYROLYSIS_THRESHOLD_0P40",
        "series": "ethylene",
        "temp": 1000,
        "ethylene": "0.40 vol%",
        "hydrogen": "0 vol%",
        "yield": "qualitative threshold",
        "outcome": "gas-phase self-pyrolysis appeared above this ethylene level",
    },
    {
        "code": "C2H4_900_TRANSFER_BOUNDARY_1P0",
        "series": "ethylene",
        "temp": 900,
        "ethylene": "1.0 vol%",
        "hydrogen": "0 vol%",
        "yield": "qualitative boundary",
        "outcome": "higher ethylene boundary before film quality/transfer failure",
    },
    {
        "code": "C2H4_1000_H2_24_EXPANDED_WINDOW",
        "series": "ethylene_hydrogen",
        "temp": 1000,
        "ethylene": "up to 0.5 vol%",
        "hydrogen": "24 vol%",
        "yield": "qualitative expanded window",
        "outcome": "high-quality SWCNT synthesis sustained by pyrolysis suppression",
    },
    {
        "code": "H2_900_PROMOTION_0_3P6_GROUP",
        "series": "hydrogen_regime",
        "temp": 900,
        "ethylene": "0.4 vol%",
        "hydrogen": "0.0-3.6 vol%",
        "yield": "increasing trend",
        "outcome": "surface cleaning/activation promotion; yield, quality and length improved",
    },
    {
        "code": "H2_900_ETCHING_GT_4P6_GROUP",
        "series": "hydrogen_regime",
        "temp": 900,
        "ethylene": "0.4 vol%",
        "hydrogen": ">4.6 vol%",
        "yield": "decreasing trend",
        "outcome": "surface poisoning/SWCNT etching; yield fell and R90 rose",
    },
    {
        "code": "H2_1000_PYROLYSIS_LT_3P6_GROUP",
        "series": "hydrogen_regime",
        "temp": 1000,
        "ethylene": "0.4 vol%",
        "hydrogen": "<3.6 vol%",
        "yield": "suppressed trend",
        "outcome": "regime I: ethylene pyrolysis suppressed; cleaner, longer and higher-quality SWCNTs",
    },
    {
        "code": "H2_1000_PROMOTION_4P6_23_GROUP",
        "series": "hydrogen_regime",
        "temp": 1000,
        "ethylene": "0.4 vol%",
        "hydrogen": "4.6-23.0 vol%",
        "yield": "increasing trend",
        "outcome": "regime II: catalyst-surface cleaning/activation promotion",
    },
    {
        "code": "H2_1000_ETCHING_GT_27_GROUP",
        "series": "hydrogen_regime",
        "temp": 1000,
        "ethylene": "0.4 vol%",
        "hydrogen": ">27 vol%",
        "yield": "decreasing trend",
        "outcome": "regime III: reversible surface poisoning/SWCNT etching",
    },
]


def summary(item: dict[str, Any]) -> str:
    return (
        f"Aerosol FC-CVD at {item['temp']} C with ethylene {item['ethylene']}, "
        f"H2 {item['hydrogen']}, ferrocene vapor nominally 0.28 Pa and total "
        f"flow 2.5 L/min. Yield/result: {item['yield']}; {item['outcome']}."
    )


def catalyst(run_id: str) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label="floating Fe catalyst from ferrocene",
        active_metals="Fe",
        support_material="unsupported aerosol nanoparticles",
        promoter="H2 as process promoter/etchant; CO2 available in setup but not assigned to these runs",
        metal_ratio_original="ferrocene partial pressure nominally 0.28 Pa",
        metal_ratio_standardized="0.28 Pa ferrocene vapor",
        precursor_summary="98% ferrocene carried by 99.999% N2",
        preparation_method="in-situ ferrocene decomposition in aerosol CVD",
        preparation_modifier="extreme dilution of catalyst particles",
        preparation_detail=(
            "N2 transferred ferrocene vapor from a cartridge through an injector "
            "near the hot zone, where Fe aerosol catalyst formed before/during growth."
        ),
        drying_condition="not_applicable",
        calcination_condition="not_applicable",
        reduction_condition="H2 concentration varied as the experimental factor",
        activation_condition="thermal ferrocene decomposition and H2-dependent surface cleaning",
        post_preparation_condition="continuous floating aerosol catalyst",
        catalyst_particle_size_mean_nm="",
        catalyst_particle_size_range_nm="",
        catalyst_particle_size_qualifier="No direct run-resolved catalyst diameter was reported.",
        phase_or_state_summary="floating Fe-based catalyst particles",
        dispersion_summary="extremely dilute aerosol catalyst",
        deactivation_summary="carbon coverage at low cleaning and H2 poisoning/etching at high concentration",
    )


def process(item: dict[str, Any], run_id: str) -> dict[str, str]:
    return process_row(
        run_id,
        1,
        "ethylene_aerosol_FC_CVD",
        reactor_type="three-zone tubular aerosol CVD reactor",
        scale_level="laboratory_continuous_aerosol",
        reactor_material="glass tube",
        reactor_size_summary="51 mm ID, 1300 mm length and about 550 mm isothermal hot zone",
        reactor_setup_summary="ferrocene/N2 injector near hot zone; downstream membrane filter",
        catalyst_loading_mass_g="",
        temperature_setpoint_C=str(item["temp"]),
        temperature_range_reported_C=str(item["temp"]),
        temperature_program_summary="continuous isothermal aerosol synthesis",
        holding_time_min="about 1.5 min collection; residence time not separately reported",
        heating_rate_C_min="not_applicable_continuous",
        cooling_condition="product aerosol filtered downstream",
        pressure_original="not_reported",
        pressure_kPa="",
        carbon_source="C2H4",
        carbon_source_flow_original=item["ethylene"],
        reducing_gas="H2",
        reducing_gas_flow_original=item["hydrogen"],
        inert_gas="N2",
        inert_gas_flow_original="balance to 2.5 L/min total flow",
        cofeed_or_reactive_gas="ferrocene vapor",
        cofeed_flow_original="0.28 Pa nominal partial pressure",
        total_flow_original="2.5 L/min",
        gas_composition_summary=(
            f"C2H4 {item['ethylene']}; H2 {item['hydrogen']}; N2 balance; "
            "ferrocene aerosol precursor"
        ),
        process_note="Total flow remained constant while gas fractions were varied.",
    )


def product(item: dict[str, Any], run_id: str) -> dict[str, str]:
    numeric = item["code"] == "C2H4_1000_OPTIMUM_0P24"
    return yield_row(
        run_id,
        primary_yield_metric="SWCNT_film_area_at_90_percent_transmittance_per_feed_volume",
        yield_original=item["yield"],
        yield_definition_original=(
            "film collection area at 90% transmittance per liter of flow"
        ),
        yield_calculation_method="Beer-Lambert conversion from 550 nm film transmittance",
        yield_value_standardized="1.05" if numeric else "",
        yield_unit_standardized="cm2/L" if numeric else "qualitative_trend",
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=summary(item),
        CNT_type_reported="SWCNT",
        CNT_type_confirmed="SWCNT",
        product_mixture_summary="randomly oriented SWCNT bundles collected as thin film",
        CNT_type_evidence="UV-Vis-NIR van Hove transitions; Raman RBM; TEM",
        SWCNT_or_few_wall_evidence_summary="SWCNT confirmed; diameter did not change across H2 scan",
        RBM_peak_reported="reported in supplementary Raman spectra",
        outer_diameter_mean_nm="",
        outer_diameter_range_nm="",
        inner_diameter_mean_nm="",
        wall_number_summary="single-walled",
        length_summary=(
            "hydrogen-dependent geometric mean bundle length; exact plot values not text-reported"
        ),
        morphology=item["outcome"],
        alignment_or_array="randomly oriented thin-film network",
        Raman_ratio_type="IG/ID",
        Raman_ratio_value="trend reported; exact point value not text-reported",
        Raman_laser_wavelength_nm="532",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis="as-collected aerosol SWCNT film",
        residue_summary="Fe catalyst and pyrolytic/polyaromatic carbon not quantitatively separated",
        amorphous_carbon_level="reduced in H2 pyrolysis-suppression regime",
        BET_surface_area_product_m2_g="",
        characterization_methods="UV-Vis-NIR; Raman; SEM; TEM; DMA; four-probe resistance",
        post_treatment_or_purification="dry transfer from filter to glass",
        purification_condition="no solution purification",
        application_property_summary=(
            "equivalent sheet resistance R90 tracked transparent-electrode performance"
        ),
        notes="Grouped regime records preserve reported boundaries without inventing plot points.",
    )


def cost_review(item: dict[str, Any], run_id: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="laboratory continuous aerosol CVD",
        scale_level_claimed="thin-film production for transparent electrodes",
        scale_evidence_summary=summary(item),
        reactor_capacity_or_throughput="2.5 L/min total flow; about 1.5 min collection",
        continuous_operation_time_h="not_reported",
        catalyst_lifetime_or_reuse="continuous floating catalyst",
        catalyst_reuse_cycles="not_applicable",
        batch_stability="not_reported",
        scale_up_issue="gas dilution, pyrolysis control, collection area and film uniformity",
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="No study-specific cost calculation.",
        cost_driver_summary="900-1000 C heat, high-purity gases and ferrocene",
        safety_risk="flammable H2/ethylene at high temperature; ferrocene aerosol",
        emission_or_waste="pyrolytic aerosol and spent membrane filters",
        industrial_readiness_assessment="laboratory continuous parameter study",
        reproduction_value="high",
        reproduction_priority="high",
        recommended_next_action="publish full point-level dataset, residence time, carbon balance and scale economics",
        review_note="Yield is an optical film-area metric, not mass productivity.",
    )


def span_for(item: dict[str, Any]) -> str:
    if item["series"] in {"ethylene", "ethylene_hydrogen"}:
        return ETHYLENE_SPAN
    if "PROMOTION" in item["code"]:
        return OPTIMAL_SPAN
    return REGIME_SPAN


def add_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    suffix: str,
    table: str,
    record_id: str,
    span_id: str,
    text: str,
    summary_text: str,
    *,
    status: str = "reported",
) -> None:
    evidence = evidence_row(
        store,
        SOURCE_ID,
        f"EVD_{run_id}_{suffix}",
        run_id,
        table,
        record_id,
        "record_level",
        span_id,
        summary_text,
        confidence="high",
        value_status=status,
    )
    evidence.update(
        {
            "evidence_type": "official_open_access_html_transcription",
            "source_section": "official article HTML",
            "source_locator": "official article HTML",
            "source_object_ref": HTML_REF,
            "evidence_text": text,
            "evidence_summary": summary_text,
            "notes": "Official open-access HTML retained locally.",
        }
    )
    tables["evidence_index"].append(evidence)


def add_run(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    item: dict[str, Any],
) -> str:
    run_id = f"{SOURCE_ID}_{item['code']}"
    run_summary = summary(item)
    source = run_row(SOURCE_ID, item["code"], item["series"], run_summary, "high")
    if item["series"] == "hydrogen_regime":
        source["data_type"] = "experimental_series_summary"
    tables["source_run"].append(source)
    cat = catalyst(run_id)
    stage = process(item, run_id)
    prod = product(item, run_id)
    cost = cost_review(item, run_id)
    tables["catalyst_system"].append(cat)
    tables["reactor_process_gas"].append(stage)
    tables["yield_quality"].append(prod)
    tables["cost_scale_review"].append(cost)
    span = span_for(item)

    add_evidence(
        tables,
        store,
        run_id,
        "RUN",
        "source_run",
        run_id,
        span,
        run_summary,
        "Condition or reported H2 regime.",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "CATALYST",
        "catalyst_system",
        cat["catalyst_id"],
        METHOD_SPAN,
        (
            f"{cat['catalyst_label']}; active {cat['active_metals']}; precursor "
            f"{cat['precursor_summary']}; ferrocene basis "
            f"{cat['metal_ratio_original']}; preparation "
            f"{cat['preparation_detail']}; reduction/activation "
            f"{cat['reduction_condition']}; deactivation "
            f"{cat['deactivation_summary']}."
        ),
        "Floating Fe catalyst and H2-dependent surface state.",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "PROCESS",
        "reactor_process_gas",
        stage["process_stage_id"],
        METHOD_SPAN,
        (
            f"Glass reactor {stage['reactor_size_summary']}; temperature "
            f"{stage['temperature_setpoint_C']} C; collection "
            f"{stage['holding_time_min']}; pressure {stage['pressure_original']} / "
            f"{stage['pressure_kPa']} kPa; ethylene "
            f"{stage['carbon_source_flow_original']}; H2 "
            f"{stage['reducing_gas_flow_original']}; N2 "
            f"{stage['inert_gas_flow_original']}; ferrocene "
            f"{stage['cofeed_flow_original']}; total {stage['total_flow_original']}."
        ),
        "Aerosol CVD reactor and gas conditions.",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "PRODUCT",
        "yield_quality",
        prod["product_id"],
        span,
        (
            f"Yield/result {prod['yield_original']}; standardized "
            f"{prod['yield_value_standardized']} {prod['yield_unit_standardized']}; "
            f"type {prod['CNT_type_confirmed']}; wall "
            f"{prod['wall_number_summary']}; Raman {prod['Raman_ratio_type']} "
            f"{prod['Raman_ratio_value']} at 532 nm; length "
            f"{prod['length_summary']}; morphology {prod['morphology']}; "
            f"application {prod['application_property_summary']}."
        ),
        "Yield trend, SWCNT identity, quality and film performance.",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "COST",
        "cost_scale_review",
        run_id,
        CONCLUSION_SPAN,
        (
            "Continuous 2.5 L/min aerosol process with short filter collection; "
            "no cost or carbon balance. High-temperature flammable gases are "
            "the main safety concern."
        ),
        "Scale, cost-data gap and safety review.",
        status="review_assessment",
    )
    return run_id


def build(
    metadata: dict[str, Any], store: EvidenceStore
) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "Nine records: four explicit ethylene/H2 boundary conditions "
                "and five grouped hydrogen-mechanism regimes across 900 and 1000 C."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = HTML_REF
    master["pdf_status"] = "official_open_access_HTML"
    master["notes"] += (
        " Grouped regime boundaries are retained without visually estimating every plotted point."
    )
    run_ids = {item["code"]: add_run(tables, store, item) for item in RUNS}
    optimum = run_ids["C2H4_1000_OPTIMUM_0P24"]
    scan900 = run_ids["H2_900_PROMOTION_0_3P6_GROUP"]
    scan1000 = run_ids["H2_1000_PROMOTION_4P6_23_GROUP"]
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_GROUPED_SCAN_001",
                SOURCE_ID,
                scan1000,
                "incomplete_run_matrix",
                "source_run",
                scan1000,
                "run_summary",
                "The article plots multiple H2 concentrations but text-extracted point values are unavailable; exact reported regime boundaries are represented as grouped series.",
                f"EVD_{scan900}_RUN;EVD_{scan1000}_RUN",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FERROCENE_PRESSURE_001",
                SOURCE_ID,
                optimum,
                "text_figure_discrepancy",
                "catalyst_system",
                f"{optimum}_CAT",
                "metal_ratio_original",
                "Methods state ferrocene partial pressure 0.28 Pa for all experiments, while a later figure caption states 0.18 Pa. The methods value is retained as nominal.",
                f"EVD_{optimum}_CATALYST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_H2_BOUNDARY_GAPS_001",
                SOURCE_ID,
                scan1000,
                "regime_boundary_gap",
                "reactor_process_gas",
                f"{scan1000}_S01",
                "reducing_gas_flow_original",
                "Reported regime boundaries leave transition gaps at 3.6-4.6 vol% and 23-27 vol% H2; no regime is assigned inside those gaps.",
                f"EVD_{scan1000}_PROCESS",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_DEFINITION_001",
                SOURCE_ID,
                optimum,
                "metric_definition",
                "yield_quality",
                f"{optimum}_PROD",
                "yield_original",
                "Yield is optical film area at 90% transmittance per liter, not CNT mass or carbon conversion.",
                f"EVD_{optimum}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_NO_POINT_METRICS_001",
                SOURCE_ID,
                scan900,
                "critical_data_gap",
                "yield_quality",
                f"{scan900}_PROD",
                "Raman_ratio_value",
                "Exact point-level IG/ID, R90, bundle length and yield values for the H2 scans are not reported in article text and were not visually interpolated.",
                f"EVD_{scan900}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PRESSURE_RESIDENCE_001",
                SOURCE_ID,
                scan1000,
                "critical_data_gap",
                "reactor_process_gas",
                f"{scan1000}_S01",
                "pressure_original",
                "Operating pressure and numeric gas residence time are not reported.",
                f"EVD_{scan1000}_PROCESS",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_NO_MASS_BALANCE_001",
                SOURCE_ID,
                optimum,
                "critical_data_gap",
                "yield_quality",
                f"{optimum}_PROD",
                "CNT_yield_per_catalyst_g_gcat",
                "No CNT mass yield, catalyst-normalized productivity, carbon conversion or purity balance was reported.",
                f"EVD_{optimum}_PRODUCT",
                "high",
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
    (REPORT_ROOT / f"batch_{BATCH_NUMBER:03d}_metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
