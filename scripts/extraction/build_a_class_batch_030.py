#!/usr/bin/env python3
"""Build the thirtieth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 30
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ID = "LIT_169EACB657CC8523"
PDF_REF = "data/raw/literature/pdf/LIT_169EACB657CC8523_b8b0f725610b.pdf"

PREP_SPAN = "SPAN_55A3DEEA68849C59652C"
FLOW_SPAN = "SPAN_D7010E0CD1576482E28F"
CONCENTRATION_SPAN = "SPAN_8AB4F30EDD268ACB5000"
HYDROGEN_SPAN = "SPAN_320AF22FDB033B8B07EB"
LOADING_SPAN = "SPAN_DD2C8804A7AB048F5440"
OPTIMUM_SPAN = "SPAN_8122C6B6789B60103C95"
CNT_SPAN = "SPAN_7911155E27BEE09322BC"
COST_SPAN = "SPAN_AA430D3BBCD8B6F0C933"


FLOW_RUNS = [
    {
        "code": "FLOW_84",
        "series": "flow",
        "ni": 10,
        "granule": 500,
        "flow": 84,
        "inlet_velocity": 0.036,
        "particle_velocity": 0.00028,
        "catalyst_mass": 10.3,
        "rate": 0.83,
        "rate_weight": 0.00011,
        "rate_surface": 0.019,
        "effective_rate": 0.0049,
        "kc": 0.0045,
        "kr": 14.67,
    },
    {
        "code": "FLOW_120",
        "series": "flow",
        "ni": 10,
        "granule": 500,
        "flow": 120,
        "inlet_velocity": 0.051,
        "particle_velocity": 0.00040,
        "catalyst_mass": 10.3,
        "rate": 0.95,
        "rate_weight": 0.00013,
        "rate_surface": 0.022,
        "effective_rate": 0.0056,
        "kc": 0.0054,
        "kr": 16.61,
    },
    {
        "code": "FLOW_180",
        "series": "flow",
        "ni": 10,
        "granule": 500,
        "flow": 180,
        "inlet_velocity": 0.077,
        "particle_velocity": 0.00066,
        "catalyst_mass": 10.2,
        "rate": 1.07,
        "rate_weight": 0.00015,
        "rate_surface": 0.025,
        "effective_rate": 0.0064,
        "kc": 0.0069,
        "kr": 18.12,
    },
    {
        "code": "FLOW_240",
        "series": "flow",
        "ni": 10,
        "granule": 500,
        "flow": 240,
        "inlet_velocity": 0.103,
        "particle_velocity": 0.00093,
        "catalyst_mass": 10.1,
        "rate": 1.15,
        "rate_weight": 0.00016,
        "rate_surface": 0.027,
        "effective_rate": 0.0069,
        "kc": 0.0083,
        "kr": 18.15,
    },
]


PARTICLE_RUNS = [
    {
        "code": f"PARTICLE_{diameter}_FLOW_{flow}",
        "series": "particle",
        "ni": 10,
        "granule": diameter,
        "flow": flow,
        "rate": rate,
    }
    for diameter, rates in [
        (300, {120: 0.85, 180: 0.91, 240: 0.98}),
        (725, {120: 0.95, 180: 1.07, 240: 1.15}),
        (1000, {120: 0.68, 180: 0.84, 240: 0.97}),
    ]
    for flow, rate in rates.items()
]


CONCENTRATION_RUNS = [
    {
        "code": "NG_N2_90_10",
        "series": "concentration",
        "ni": 10,
        "granule": 725,
        "flow": 120,
        "ng": 90,
        "n2": 10,
        "rate_surface": 0.0075,
        "bulk": 13.3,
        "kr_mass_transfer": 0.00066,
        "keff": 0.00058,
        "bulk_from_rate": 12.7,
    },
    {
        "code": "NG_N2_70_30",
        "series": "concentration",
        "ni": 10,
        "granule": 725,
        "flow": 120,
        "ng": 70,
        "n2": 30,
        "rate_surface": 0.0069,
        "bulk": 10.4,
        "kr_mass_transfer": 0.00066,
        "keff": 0.00058,
        "bulk_from_rate": 11.7,
    },
    {
        "code": "NG_N2_50_50",
        "series": "concentration",
        "ni": 10,
        "granule": 725,
        "flow": 120,
        "ng": 50,
        "n2": 50,
        "rate_surface": 0.0053,
        "bulk": 7.4,
        "kr_mass_transfer": 0.00066,
        "keff": 0.00058,
        "bulk_from_rate": 9.1,
    },
]


HYDROGEN_RUNS = [
    {
        "code": "NG_H2_100_0",
        "series": "hydrogen",
        "ni": 5,
        "granule": 725,
        "flow": 120,
        "ng": 100,
        "h2": 0,
        "rate": 0.65,
        "deactivation": 81,
    },
    {
        "code": "NG_H2_95_5",
        "series": "hydrogen",
        "ni": 5,
        "granule": 725,
        "flow": 120,
        "ng": 95,
        "h2": 5,
        "rate": 0.41,
        "deactivation": 300,
        "censored": True,
    },
    {
        "code": "NG_H2_90_10",
        "series": "hydrogen",
        "ni": 5,
        "granule": 725,
        "flow": 120,
        "ng": 90,
        "h2": 10,
        "rate": 0.08,
        "deactivation": 20,
    },
]


LOADING_RUNS = [
    {
        "code": "NI_LOADING_5",
        "series": "loading",
        "ni": 5,
        "granule": 725,
        "flow": 120,
        "carbon_mass": 13,
        "duration": 154,
        "rate": 0.088,
        "diameter": "15-30",
    },
    {
        "code": "NI_LOADING_10",
        "series": "loading",
        "ni": 10,
        "granule": 725,
        "flow": 120,
        "carbon_mass": 62,
        "duration": 285,
        "rate": 0.12,
    },
    {
        "code": "NI_LOADING_15",
        "series": "loading",
        "ni": 15,
        "granule": 725,
        "flow": 120,
        "carbon_mass": 143,
        "duration": 445,
        "rate": 0.124,
    },
]


OPTIMUM_RUN = {
    "code": "NI_LOADING_12P5_VALIDATION",
    "series": "optimum",
    "ni": 12.5,
    "granule": 725,
    "flow": 120,
    "rate": 0.125,
}


ALL_RUNS = [
    *FLOW_RUNS,
    *PARTICLE_RUNS,
    *CONCENTRATION_RUNS,
    *HYDROGEN_RUNS,
    *LOADING_RUNS,
    OPTIMUM_RUN,
]


def run_summary(item: dict[str, Any]) -> str:
    series = item["series"]
    common = (
        f"{item['ni']} wt% Ni/gamma-Al2O3, catalyst granule diameter "
        f"{item['granule']} micrometre, 550 C and {item['flow']} mL/min total gas."
    )
    if series == "flow":
        return (
            f"Natural-gas flow screen: {common} Inlet velocity "
            f"{item['inlet_velocity']} m/s, velocity around particle "
            f"{item['particle_velocity']} m/s, initial catalyst "
            f"{item['catalyst_mass']} mg, TGA carbon rate {item['rate']} mg/min, "
            f"weight-basis rate {item['rate_weight']} mol/s/gcat, surface-basis "
            f"rate {item['rate_surface']} mol/s/m2, effective specific rate "
            f"{item['effective_rate']} m/s, kc {item['kc']} m/s and kr "
            f"{item['kr']} s-1."
        )
    if series == "particle":
        return (
            f"Catalyst-granule screen: {common} TGA carbon-deposition rate "
            f"{item['rate']} mg/min. The 725 micrometre granule gave the "
            "maximum rates and was selected for later experiments."
        )
    if series == "concentration":
        return (
            f"Natural-gas/N2 concentration screen: {common} Gas was "
            f"{item['ng']} vol% natural gas and {item['n2']} vol% N2. "
            f"Surface-basis rate {item['rate_surface']} mol/s/m2, measured bulk "
            f"concentration {item['bulk']} mol/m3, kr {item['kr_mass_transfer']} "
            f"m/s, keff {item['keff']} m/s and rate-derived bulk concentration "
            f"{item['bulk_from_rate']} mol/m3 supported a first-order model."
        )
    if series == "hydrogen":
        qualifier = (
            "without deactivation during the 300 min test"
            if item.get("censored")
            else "to complete deactivation"
        )
        return (
            f"Hydrogen-cofeed screen: {common} Feed was {item['ng']} vol% "
            f"natural gas and {item['h2']} vol% H2. Instant rate "
            f"{item['rate']} mg/min and {item['deactivation']} min {qualifier}."
        )
    if series == "loading":
        return (
            f"Nickel-loading screen: {common} Carbon deposited "
            f"{item['carbon_mass']} mg over {item['duration']} min; carbon "
            f"formation rate {item['rate']} mgC/min/mgNi."
            + (
                f" TEM/SEM CNT diameter was {item['diameter']} nm, with hollow "
                "and solid dense tubes."
                if item.get("diameter")
                else ""
            )
        )
    return (
        f"Experimental optimum validation: {common} Carbon formation rate "
        f"{item['rate']} mgC/min/mgNi, similar to 15 wt% but with lower Ni cost."
    )


def catalyst(item: dict[str, Any], run_id: str) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label=f"{item['ni']} wt% Ni/gamma-Al2O3",
        active_metals="Ni",
        support_material="gamma-Al2O3 nanopowder",
        promoter="none",
        metal_ratio_original=f"{item['ni']} wt% Ni/Al2O3",
        metal_ratio_standardized=f"Ni loading = {item['ni']} wt%",
        precursor_summary="Ni(NO3)2.6H2O in methanol plus gamma-Al2O3",
        preparation_method="wet impregnation",
        preparation_modifier="closed-vessel stirring followed by open-atmosphere drying",
        preparation_detail=(
            "Nickel nitrate dissolved in methanol; alumina added at the "
            "required ratio; stirred at 90 C for 2 h."
        ),
        drying_condition="90 C in open atmosphere; duration not reported",
        calcination_condition="650 C in air for 1 h inside TGA",
        reduction_condition="in situ at 550 C for 90 min in 5% H2/95% N2",
        activation_condition="reduced immediately before natural-gas decomposition",
        post_preparation_condition="used in quartz flat-bottom TGA sample holder",
        catalyst_particle_size_mean_nm="",
        catalyst_particle_size_range_nm="",
        catalyst_particle_size_qualifier=(
            f"Screened catalyst granule diameter {item['granule']} micrometre; "
            "this is not the nanoscale Ni active-particle diameter"
        ),
        phase_or_state_summary="reduced Ni on gamma-Al2O3",
        dispersion_summary=(
            "not measured; authors caution that high Ni loading can lower dispersion"
        ),
        deactivation_summary=(
            "carbon coverage reduces free Ni surface; deactivation time depends "
            "on flow, gas composition and Ni loading"
        ),
    )


def process_rows(item: dict[str, Any], run_id: str) -> list[dict[str, str]]:
    ng = item.get("ng", 100)
    h2 = item.get("h2", 0)
    n2 = item.get("n2", 0)
    if item["series"] == "hydrogen":
        gas_summary = f"natural gas {ng} vol%; H2 {h2} vol%"
    elif item["series"] == "concentration":
        gas_summary = f"natural gas {ng} vol%; N2 {n2} vol%"
    else:
        gas_summary = "natural gas; composition not reported, methane dominant"
    duration = item.get("duration", item.get("deactivation", "not_reported"))
    return [
        process_row(
            run_id,
            1,
            "air_calcination",
            reactor_type="Thermax 500 thermogravimetric analyzer",
            scale_level="laboratory_TGA",
            reactor_material="quartz flat-bottom sample holder",
            reactor_size_summary="microbalance sample; exact volume not reported",
            reactor_setup_summary="calcination performed inside the TGA",
            catalyst_loading_mass_g="",
            temperature_setpoint_C="650",
            temperature_range_reported_C="650",
            temperature_program_summary="air calcination",
            holding_time_min="60",
            heating_rate_C_min="not_reported",
            cooling_condition="not_reported",
            pressure_original="1 atmosphere",
            pressure_kPa="101.325",
            carbon_source="none",
            reducing_gas="none",
            inert_gas="none",
            cofeed_or_reactive_gas="air",
            cofeed_flow_original="not_reported",
            total_flow_original="not_reported",
            gas_composition_summary="air",
            process_note="Calcined catalyst remained in the TGA for in-situ reduction.",
        ),
        process_row(
            run_id,
            2,
            "hydrogen_reduction",
            reactor_type="Thermax 500 thermogravimetric analyzer",
            scale_level="laboratory_TGA",
            reactor_material="quartz flat-bottom sample holder",
            reactor_size_summary="microbalance sample; exact volume not reported",
            reactor_setup_summary="in-situ reduction at reaction temperature",
            catalyst_loading_mass_g="",
            temperature_setpoint_C="550",
            temperature_range_reported_C="550",
            temperature_program_summary="5% H2/95% N2 reduction",
            holding_time_min="90",
            heating_rate_C_min="not_reported",
            cooling_condition="not_applicable before reaction",
            pressure_original="1 atmosphere",
            pressure_kPa="101.325",
            carbon_source="none",
            reducing_gas="H2",
            reducing_gas_flow_original="5 vol%",
            inert_gas="N2",
            inert_gas_flow_original="95 vol%",
            cofeed_or_reactive_gas="none",
            total_flow_original="not_reported",
            gas_composition_summary="5% H2 and 95% N2",
            process_note="Reduction lasted 90 min immediately before reaction.",
        ),
        process_row(
            run_id,
            3,
            "natural_gas_catalytic_decomposition",
            reactor_type="Thermax 500 thermogravimetric analyzer",
            scale_level="laboratory_TGA",
            reactor_material="quartz flat-bottom sample holder",
            reactor_size_summary="microbalance sample; exact volume not reported",
            reactor_setup_summary=(
                f"{item['granule']} micrometre catalyst granule in TGA sample holder"
            ),
            catalyst_loading_mass_g=(
                str(item["catalyst_mass"] / 1000) if item.get("catalyst_mass") else ""
            ),
            temperature_setpoint_C="550",
            temperature_range_reported_C="550",
            temperature_program_summary="isothermal natural-gas decomposition",
            holding_time_min=str(duration),
            heating_rate_C_min="not_applicable after reduction",
            cooling_condition="not_reported",
            pressure_original="1 atmosphere",
            pressure_kPa="101.325",
            carbon_source="natural gas; methane used for conversion definition",
            carbon_source_flow_original=f"{item['flow']} mL/min",
            reducing_gas="H2" if h2 else "none externally added",
            reducing_gas_flow_original=f"{h2} vol%" if h2 else "0 vol%",
            inert_gas="N2" if n2 else "none externally added",
            inert_gas_flow_original=f"{n2} vol%" if n2 else "0 vol%",
            cofeed_or_reactive_gas="none",
            cofeed_flow_original="not_applicable",
            total_flow_original=f"{item['flow']} mL/min",
            gas_composition_summary=gas_summary,
            process_note=(
                "TGA mass increase was assigned to carbon deposition; time zero "
                "was when natural gas began flowing."
            ),
        ),
    ]


def product(item: dict[str, Any], run_id: str) -> dict[str, str]:
    summary = run_summary(item)
    series = item["series"]
    rate = item.get("rate_surface", item.get("rate"))
    if series == "concentration":
        unit = "mol/s/m2"
    elif series in {"loading", "optimum"}:
        unit = "mg_C/min/mg_Ni"
    else:
        unit = "mg_C/min"
    diameter = item.get("diameter", "")
    return yield_row(
        run_id,
        primary_yield_metric="initial_or_specific_carbon_deposition_rate",
        yield_original=f"{rate} {unit}",
        yield_definition_original=(
            "TGA mass increase assigned to deposited carbon; normalization "
            "depends on the experimental series"
        ),
        yield_calculation_method=(
            "fresh-catalyst initial TGA rate or rate normalized by Ni/external area"
        ),
        yield_value_standardized=str(rate),
        yield_unit_standardized=unit,
        yield_standardization_note=(
            "Rates with different denominators are not directly pooled."
        ),
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=summary,
        CNT_type_reported="carbon nanotubes",
        CNT_type_confirmed=("hollow and solid CNT" if item.get("ni") == 5 else "CNT"),
        product_mixture_summary="CNT/carbon deposit plus spent Ni/Al2O3 catalyst",
        CNT_type_evidence="TEM and SEM; TGA mass gain",
        SWCNT_or_few_wall_evidence_summary="wall count not consistently assigned",
        RBM_peak_reported="not_reported",
        outer_diameter_mean_nm="",
        outer_diameter_range_nm=diameter,
        inner_diameter_mean_nm="",
        wall_number_summary="hollow and solid dense tubes; exact wall count not reported",
        length_summary="not_quantified",
        morphology="dense CNT network; hollow and solid channels observed for 5 wt% Ni",
        alignment_or_array="non-aligned network",
        Raman_ratio_type="not_reported",
        Raman_ratio_value="",
        Raman_laser_wavelength_nm="",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis="unpurified TGA carbon/catalyst product",
        residue_summary="Ni/Al2O3 catalyst",
        amorphous_carbon_level="not_quantified",
        BET_surface_area_product_m2_g="",
        characterization_methods="TGA; TEM; SEM; CFD-derived velocity/rate analysis",
        post_treatment_or_purification="none reported",
        purification_condition="not_reported",
        application_property_summary="hydrogen co-production; no application test",
        notes=(
            "CNT diameter 15-30 nm was explicitly characterized using the "
            "5 wt% Ni catalyst and is not propagated to every run."
            if diameter
            else "No run-specific CNT diameter was reported."
        ),
    )


def cost_review(item: dict[str, Any], run_id: str) -> dict[str, str]:
    representative = item["series"] == "optimum"
    return cost_row(
        run_id,
        scale_level_demonstrated="laboratory TGA microbalance",
        scale_level_claimed="pilot-scale testing recommended; process not commercial",
        scale_evidence_summary=run_summary(item),
        reactor_capacity_or_throughput=(
            f"{item['flow']} mL/min gas; catalyst sample about 10 mg in flow screen"
        ),
        continuous_operation_time_h="",
        catalyst_lifetime_or_reuse=(
            f"{item['deactivation']} min"
            if item.get("deactivation") and not item.get("censored")
            else (
                "active through 300 min test"
                if item.get("censored")
                else "condition-dependent; not a reuse test"
            )
        ),
        catalyst_reuse_cycles="not_reported",
        batch_stability="not_reported",
        scale_up_issue=(
            "external mass-transfer control, catalyst deactivation, Ni dispersion, "
            "product separation and absence of pilot data"
        ),
        quantitative_cost_reported=(
            "modeled maximum profit 0.0021 USD/min excluding CNT value"
            if representative
            else "study-level optimization model"
        ),
        quantitative_cost_summary=(
            "Economic model predicted 30 wt% Ni optimum; natural gas "
            "0.0043 USD/min, N2 0.0013 USD/min, power 0.0022 USD/min, "
            "Ni(NO3)2 128 USD/kg, Al2O3 80 USD/kg and H2 2.2 USD/kg."
            if representative
            else "No run-specific measured cost."
        ),
        cost_driver_summary="nickel loading, alumina, natural gas, N2, power and H2 value",
        safety_risk="flammable natural gas/H2 at 550 C; Ni nitrate and Ni exposure",
        emission_or_waste="solid carbon/CNT with spent Ni/Al2O3; CO-free H2 claimed",
        industrial_readiness_assessment="laboratory kinetic study; no pilot reactor",
        reproduction_value="high",
        reproduction_priority="high" if representative else "medium",
        recommended_next_action=(
            "validate intrinsic kinetics without external mass-transfer limitation, "
            "measure CNT purity/yield, Ni dispersion, gas conversion and pilot economics"
        ),
        review_note=(
            "Experimental activity optimum is 12.5 wt% Ni; 30 wt% is an "
            "economic-model optimum and excludes CNT market value."
        ),
    )


def add_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    suffix: str,
    table: str,
    record_id: str,
    span_id: str,
    page: int,
    text: str,
    summary: str,
    *,
    confidence: str = "high",
    status: str = "reported",
) -> None:
    item = evidence_row(
        store,
        SOURCE_ID,
        f"EVD_{run_id}_{suffix}",
        run_id,
        table,
        record_id,
        "record_level",
        span_id,
        summary,
        confidence=confidence,
        value_status=status,
    )
    item.update(
        {
            "evidence_type": "pdf_text_and_visual_table_transcription",
            "source_section": f"PDF page {page}",
            "source_locator": f"PDF page {page}",
            "source_object_ref": PDF_REF,
            "evidence_text": text,
            "evidence_summary": summary,
            "notes": "Values visually checked against the local publisher PDF.",
        }
    )
    tables["evidence_index"].append(item)


def source_span_and_page(item: dict[str, Any]) -> tuple[str, int]:
    return {
        "flow": (FLOW_SPAN, 4),
        "particle": (FLOW_SPAN, 4),
        "concentration": (CONCENTRATION_SPAN, 7),
        "hydrogen": (HYDROGEN_SPAN, 7),
        "loading": (LOADING_SPAN, 7),
        "optimum": (OPTIMUM_SPAN, 10),
    }[item["series"]]


def add_run(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    item: dict[str, Any],
) -> str:
    run_id = f"{SOURCE_ID}_{item['code']}"
    summary = run_summary(item)
    span, page = source_span_and_page(item)
    tables["source_run"].append(
        run_row(
            SOURCE_ID,
            item["code"],
            f"{item['series']} series: {item['ni']} wt% Ni, {item['flow']} mL/min",
            summary,
            "high",
        )
    )
    cat = catalyst(item, run_id)
    tables["catalyst_system"].append(cat)
    stages = process_rows(item, run_id)
    tables["reactor_process_gas"].extend(stages)
    prod = product(item, run_id)
    tables["yield_quality"].append(prod)
    cost = cost_review(item, run_id)
    tables["cost_scale_review"].append(cost)

    add_evidence(
        tables,
        store,
        run_id,
        "RUN",
        "source_run",
        run_id,
        span,
        page,
        summary,
        "Run identity and reported result.",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "CATALYST",
        "catalyst_system",
        f"{run_id}_CAT",
        PREP_SPAN,
        3,
        (
            f"{item['ni']} wt% Ni/Al2O3; Ni(NO3)2.6H2O in methanol on "
            f"gamma-Al2O3; stirred at 90 C for 2 h, dried at 90 C, "
            "calcined at 650 C in air for 1 h, and reduced at 550 C for "
            f"90 min in 5% H2/95% N2. Catalyst granule diameter "
            f"{item['granule']} micrometre; not nanoscale Ni-particle diameter."
        ),
        "Catalyst composition, preparation and granule-size context.",
    )
    for stage in stages:
        stage_text = (
            f"Stage {stage['stage_order']} {stage['stage_type']}; reactor "
            f"{stage['reactor_type']}; material {stage['reactor_material']}; "
            f"size {stage['reactor_size_summary']}; setup "
            f"{stage['reactor_setup_summary']}; catalyst loading "
            f"{stage['catalyst_loading_mass_g']} g; temperature "
            f"{stage['temperature_setpoint_C']} C; range "
            f"{stage['temperature_range_reported_C']} C; program "
            f"{stage['temperature_program_summary']}; duration "
            f"{stage['holding_time_min']} min; pressure "
            f"{stage['pressure_original']} / {stage['pressure_kPa']} kPa; "
            f"carbon source {stage['carbon_source']} at "
            f"{stage['carbon_source_flow_original']}; H2 "
            f"{stage['reducing_gas_flow_original']}; N2 "
            f"{stage['inert_gas_flow_original']}; total flow "
            f"{stage['total_flow_original']}; composition "
            f"{stage['gas_composition_summary']}; note {stage['process_note']}"
        )
        add_evidence(
            tables,
            store,
            run_id,
            f"PROCESS_{stage['stage_order']}",
            "reactor_process_gas",
            stage["process_stage_id"],
            PREP_SPAN if stage["stage_order"] != "3" else span,
            3 if stage["stage_order"] != "3" else page,
            stage_text,
            f"Process stage {stage['stage_order']} support.",
        )
    add_evidence(
        tables,
        store,
        run_id,
        "PRODUCT",
        "yield_quality",
        f"{run_id}_PROD",
        CNT_SPAN if item.get("diameter") else span,
        10 if item.get("diameter") else page,
        (
            f"{summary} Standardized primary value "
            f"{prod['yield_value_standardized']} "
            f"{prod['yield_unit_standardized']}; CNT diameter "
            f"{prod['outer_diameter_range_nm']} nm."
        ),
        "Carbon-deposition rate and CNT product result.",
    )
    cost_text = (
        f"Laboratory TGA at 550 C and {item['flow']} mL/min; catalyst "
        f"granule {item['granule']} micrometre; process not commercial and "
        "pilot-scale work recommended."
    )
    if item["series"] == "optimum":
        cost_text += (
            " Experimental optimum 12.5 wt% Ni; modeled economic optimum "
            "30 wt% Ni; maximum profit 0.0021 USD/min excluding CNT value. "
            "Natural gas 0.0043 USD/min, N2 0.0013 USD/min, power "
            "0.0022 USD/min, Ni(NO3)2 128 USD/kg, Al2O3 80 USD/kg and "
            "H2 price 2.2 USD/kg."
        )
    elif item.get("censored"):
        cost_text += " Catalyst remained active through the 300 min test."
    elif item.get("deactivation"):
        cost_text += f" Complete deactivation time {item['deactivation']} min."
    add_evidence(
        tables,
        store,
        run_id,
        "COST",
        "cost_scale_review",
        run_id,
        COST_SPAN if item["series"] == "optimum" else span,
        9 if item["series"] == "optimum" else page,
        cost_text,
        "Scale, lifetime and economics context.",
        status="review_assessment",
    )
    return run_id


def build(
    metadata: dict[str, Any],
    store: EvidenceStore,
) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "Twenty-three records: four gas-flow runs, nine catalyst-granule "
                "runs, three natural-gas/N2 runs, three natural-gas/H2 runs, "
                "three measured Ni-loading runs and one 12.5 wt% optimum validation."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_publisher_pdf"
    master["notes"] += (
        " Tables 1-8 and TEM/SEM Figs. 8-10 were visually checked. Derived "
        "kinetic-model alternatives are retained in summaries/issues, not "
        "duplicated as synthesis runs."
    )

    run_ids = {item["code"]: add_run(tables, store, item) for item in ALL_RUNS}
    flow120 = run_ids["FLOW_120"]
    particle725 = run_ids["PARTICLE_725_FLOW_120"]
    ng90 = run_ids["NG_N2_90_10"]
    h2five = run_ids["NG_H2_95_5"]
    loading5 = run_ids["NI_LOADING_5"]
    loading15 = run_ids["NI_LOADING_15"]
    optimum = run_ids["NI_LOADING_12P5_VALIDATION"]
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_RATE_DENOMINATOR_001",
                SOURCE_ID,
                flow120,
                "metric_denominator",
                "yield_quality",
                f"{flow120}_PROD",
                "yield_unit_standardized",
                (
                    "The paper reports total TGA mg/min, mol/s/gcat, mol/s/m2 "
                    "and mgC/min/mgNi in different experimental series. These "
                    "are preserved with their original denominators and not pooled."
                ),
                f"EVD_{flow120}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_GRANULE_SIZE_001",
                SOURCE_ID,
                particle725,
                "dimension_semantics",
                "catalyst_system",
                f"{particle725}_CAT",
                "catalyst_particle_size_qualifier",
                (
                    "The 300, 725 and 1000 micrometre values are catalyst "
                    "granule diameters used for mass-transfer screening, not "
                    "nanoscale Ni active-particle sizes or CNT diameters."
                ),
                f"EVD_{particle725}_CATALYST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CNT_DIAMETER_SCOPE_001",
                SOURCE_ID,
                loading5,
                "measurement_scope",
                "yield_quality",
                f"{loading5}_PROD",
                "outer_diameter_range_nm",
                (
                    "The 15-30 nm CNT diameter was characterized using 5 wt% "
                    "Ni/Al2O3 and is not automatically assigned to other loadings."
                ),
                f"EVD_{loading5}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_TGA_MASS_001",
                SOURCE_ID,
                flow120,
                "measurement_assumption",
                "yield_quality",
                f"{flow120}_PROD",
                "yield_definition_original",
                (
                    "All TGA weight increase during natural-gas flow was assumed "
                    "to be carbon deposition; no independent run-level carbon "
                    "purity correction was reported."
                ),
                f"EVD_{flow120}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FIRST_HALF_ORDER_001",
                SOURCE_ID,
                ng90,
                "derived_model_alternative",
                "yield_quality",
                f"{ng90}_PROD",
                "secondary_result_summary",
                (
                    "Tables 5 and 6 apply first-order and half-order calculations "
                    "to the same three experiments. The authors select first "
                    "order; the alternative is not treated as new runs."
                ),
                f"EVD_{ng90}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_H2_CENSOR_001",
                SOURCE_ID,
                h2five,
                "right_censored_lifetime",
                "cost_scale_review",
                h2five,
                "catalyst_lifetime_or_reuse",
                (
                    "At 5 vol% H2 the catalyst was still active after 300 min, "
                    "so 300 min is a lower bound rather than a complete "
                    "deactivation time."
                ),
                f"EVD_{h2five}_COST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_OPTIMUM_SCOPE_001",
                SOURCE_ID,
                optimum,
                "optimization_objective",
                "cost_scale_review",
                optimum,
                "review_note",
                (
                    "12.5 wt% Ni maximizes the interpolated experimental carbon "
                    "rate, whereas 30 wt% maximizes the paper's economic objective. "
                    "They are different optimization targets."
                ),
                f"EVD_{optimum}_COST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_MODEL_EXTRAPOLATION_001",
                SOURCE_ID,
                optimum,
                "model_extrapolation",
                "cost_scale_review",
                optimum,
                "quantitative_cost_summary",
                (
                    "The 30 wt% economic optimum lies outside the measured "
                    "5, 10 and 15 wt% catalyst set and is constrained by an "
                    "assumed wet-impregnation upper limit."
                ),
                f"EVD_{optimum}_COST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_COST_EXCLUDES_CNT_001",
                SOURCE_ID,
                optimum,
                "cost_boundary",
                "cost_scale_review",
                optimum,
                "quantitative_cost_reported",
                (
                    "The maximum modeled profit of 0.0021 USD/min explicitly "
                    "excludes any market value for the produced CNTs."
                ),
                f"EVD_{optimum}_COST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_NG_COMPOSITION_001",
                SOURCE_ID,
                loading15,
                "critical_data_gap",
                "reactor_process_gas",
                f"{loading15}_S03",
                "gas_composition_summary",
                (
                    "Natural gas is described as methane-dominant, but its full "
                    "component analysis is not reported; methane is used for "
                    "conversion equations."
                ),
                f"EVD_{loading15}_PROCESS_3",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SERIES_OVERLAP_001",
                SOURCE_ID,
                flow120,
                "experimental_series_overlap",
                "source_run",
                flow120,
                "run_summary",
                (
                    "Some nominal conditions recur across flow, granule and "
                    "loading tables, but the records represent distinct screening "
                    "series with different reported metrics and sample definitions."
                ),
                f"EVD_{flow120}_RUN;EVD_{particle725}_RUN",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SCALE_001",
                SOURCE_ID,
                optimum,
                "scale_limit",
                "cost_scale_review",
                optimum,
                "industrial_readiness_assessment",
                (
                    "The demonstrated reactor is a TGA microbalance with roughly "
                    "10 mg catalyst in the flow screen; no continuous or pilot "
                    "CNT collection was demonstrated."
                ),
                f"EVD_{optimum}_COST",
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
    output = REPORT_ROOT / f"batch_{BATCH_NUMBER:03d}_metrics.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
