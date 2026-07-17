#!/usr/bin/env python3
"""Build the thirty-first evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 31
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_6A5D5568EBD1E558"
PDF_REF = "data/raw/fulltext/pdf/LIT_6A5D5568EBD1E558_df369881dc50.pdf"

CATALYST_SPAN = "SPAN_12FC34035713175370E7"
TVA_SPAN = "SPAN_9E2D2FB39196405407CA"
PROTOCOL_SPAN = "SPAN_B17EC482D886F808EC5C"
RESULT_SPAN = "SPAN_00CF3CC57DC64A9C1819"
OPTI_SPAN = "SPAN_3CB79F050156630139FA"
ABSTRACT_SPAN = "SPAN_B567E30CC2EE3459360A"
MODEL_SPAN = "SPAN_F53EC05E56D60005DAD5"
CONCLUSION_SPAN = "SPAN_4A42E669D518B9E4D61C"


TAGUCHI_RUNS = [
    {
        "code": "E1",
        "temp_k": 973,
        "temp_c": 700,
        "h2": 10,
        "ch4": 10,
        "o2": 0,
        "pressure": 10,
        "power": 342.82,
        "h_atom": 0.041,
        "outcome": "no or few nanotubes",
    },
    {
        "code": "E2",
        "temp_k": 1123,
        "temp_c": 850,
        "h2": 10,
        "ch4": 10,
        "o2": 0,
        "pressure": 10,
        "power": 342.82,
        "h_atom": 0.039,
        "outcome": "long spiral or helical nanotubes; best Taguchi combination",
    },
    {
        "code": "E3",
        "temp_k": 973,
        "temp_c": 700,
        "h2": 10,
        "ch4": 10,
        "o2": 0,
        "pressure": 40,
        "power": 814.54,
        "h_atom": 0.061,
        "outcome": "no or few nanotubes; strong substrate etching",
    },
    {
        "code": "E4",
        "temp_k": 1123,
        "temp_c": 850,
        "h2": 10,
        "ch4": 10,
        "o2": 0,
        "pressure": 40,
        "power": 814.54,
        "h_atom": 0.059,
        "outcome": "shorter nanotubes at a run-dependent density",
    },
    {
        "code": "E5",
        "temp_k": 973,
        "temp_c": 700,
        "h2": 100,
        "ch4": 10,
        "o2": 0,
        "pressure": 10,
        "power": 342.82,
        "h_atom": 0.046,
        "outcome": "no or few nanotubes",
    },
    {
        "code": "E6",
        "temp_k": 1123,
        "temp_c": 850,
        "h2": 100,
        "ch4": 10,
        "o2": 0,
        "pressure": 10,
        "power": 342.82,
        "h_atom": 0.043,
        "outcome": "shorter nanotubes at a run-dependent density",
    },
    {
        "code": "E7",
        "temp_k": 973,
        "temp_c": 700,
        "h2": 100,
        "ch4": 10,
        "o2": 0,
        "pressure": 40,
        "power": 814.54,
        "h_atom": 0.054,
        "outcome": "no or few nanotubes; inferred from the four 700 C runs",
    },
    {
        "code": "E8",
        "temp_k": 1123,
        "temp_c": 850,
        "h2": 100,
        "ch4": 10,
        "o2": 0,
        "pressure": 40,
        "power": 814.54,
        "h_atom": 0.051,
        "outcome": "shorter nanotubes at a run-dependent density",
    },
]

OPTI_RUN = {
    "code": "OPTI",
    "temp_k": 1123,
    "temp_c": 850,
    "h2": 90,
    "ch4": 10,
    "o2": 1,
    "pressure": 10,
    "power": 342.82,
    "outcome": (
        "regular full-surface MWCNT coverage; about 40 nm outer diameter, "
        "1 micrometre length and top-growth morphology"
    ),
}

MODEL_RUNS = [
    {
        "code": "CFD_OPTI_BASELINE",
        "temp_k": 1123,
        "temp_c": 850,
        "h2": 90,
        "ch4": 10,
        "o2": 0,
        "pressure": 10,
        "power": "",
        "outcome": (
            "calculated CNT growth rate 8.3 micrometre/h at site density "
            "5.0e-10 mol/cm2; plasma maximum 2163 K about 17 mm above substrate"
        ),
        "model_kind": "baseline",
    },
    {
        "code": "CFD_TEMPERATURE_SWEEP",
        "temp_k": "873-1273",
        "temp_c": "600-1000",
        "h2": 90,
        "ch4": 10,
        "o2": 0,
        "pressure": 10,
        "power": "",
        "outcome": (
            "calculated CNT growth rate increased from 0.5 to 45 micrometre/h "
            "over 873-1273 K; fitted activation energy 1.2 kJ/mol"
        ),
        "model_kind": "temperature_sweep",
    },
]

ALL_RUNS = [*TAGUCHI_RUNS, OPTI_RUN, *MODEL_RUNS]


def is_model(item: dict[str, Any]) -> bool:
    return "model_kind" in item


def run_summary(item: dict[str, Any]) -> str:
    if is_model(item):
        return (
            "Nonphysical 2D axisymmetric steady laminar ANSYS Fluent 12 record; "
            f"10 vol% CH4/90 vol% H2, 10 mbar. {item['outcome']}."
        )
    oxygen = f", O2 {item['o2']} sccm" if item["o2"] else ""
    atom = (
        f" Figure-derived 0D H-atom mole fraction approximately {item['h_atom']}."
        if "h_atom" in item
        else ""
    )
    return (
        f"PECVD {item['code']}: Ni/Si with a 1 nm Ni film; "
        f"{item['temp_k']} K ({item['temp_c']} C), H2 {item['h2']} sccm, "
        f"CH4 {item['ch4']} sccm{oxygen}, {item['pressure']} mbar and "
        f"{item['power']} W microwave input. After 20 min growth: "
        f"{item['outcome']}.{atom}"
    )


def catalyst(item: dict[str, Any], run_id: str) -> dict[str, str]:
    anneal = (
        f"{item['temp_k']} K ({item['temp_c']} C) vacuum anneal for 20 min"
        if not is_model(item)
        else "catalyst surface represented by fitted site-density boundary condition"
    )
    return catalyst_row(
        run_id,
        catalyst_label="TVA-deposited 1 nm Ni film on Si wafer",
        active_metals="Ni",
        support_material="Si wafer",
        promoter="O2 growth cofeed" if item.get("o2") else "none",
        metal_ratio_original="1 nm Ni film thickness on Si",
        metal_ratio_standardized="Ni film thickness = 1 nm",
        precursor_summary="pure Ni anode evaporated into TVA plasma",
        preparation_method="thermionic vacuum arc physical vapor deposition",
        preparation_modifier="quartz-balance endpoint control",
        preparation_detail=(
            "Residual pressure 3e-6 torr; TVA filament 60 A at 20 V AC; "
            "anode-voltage ramp about 1000 V/min; deposition stopped at 1 nm."
        ),
        drying_condition="not_applicable",
        calcination_condition="not_applicable",
        reduction_condition=(
            "pure H2 plasma for 10 min after vacuum annealing"
            if not is_model(item)
            else "not_applicable_to_simulation"
        ),
        activation_condition=anneal,
        post_preparation_condition=(
            "18-20 s deposition at about 0.05 nm/s followed by 120 min "
            "high-vacuum cooling"
        ),
        catalyst_particle_size_mean_nm="",
        catalyst_particle_size_range_nm="",
        catalyst_particle_size_qualifier=(
            "The 1 nm value is deposited film thickness. AFM RMS roughness "
            "changed from 1.864 to 3.485 nm after 850 C annealing/H2 treatment; "
            "neither value is a catalyst-particle diameter."
        ),
        phase_or_state_summary="annealed/agglomerated Ni clusters on Si",
        dispersion_summary="individual Ni clusters agglomerated during annealing",
        deactivation_summary="not quantified; oxygen was tested to enhance activity",
    )


def physical_process_rows(item: dict[str, Any], run_id: str) -> list[dict[str, str]]:
    pressure_kpa = str(item["pressure"] / 10)
    common = {
        "reactor_type": "microwave PECVD silica bell jar",
        "scale_level": "laboratory_substrate",
        "reactor_material": "10 cm diameter silica bell jar; molybdenum boat",
        "reactor_size_summary": "10 cm bell-jar diameter; plasma-zone radius 2.5 cm",
        "reactor_setup_summary": (
            "1.2 kW, 2.45 GHz microwave generator; substrate electrically "
            "heated and monitored by optical pyrometer"
        ),
        "catalyst_loading_mass_g": "",
        "temperature_setpoint_C": str(item["temp_c"]),
        "temperature_range_reported_C": str(item["temp_c"]),
        "heating_rate_C_min": "not_reported",
        "cooling_condition": "not_reported",
        "pressure_original": f"{item['pressure']} mbar",
        "pressure_kPa": pressure_kpa,
    }
    return [
        process_row(
            run_id,
            1,
            "vacuum_thermal_annealing",
            **common,
            temperature_program_summary=f"anneal at {item['temp_k']} K in vacuum",
            holding_time_min="20",
            carbon_source="none",
            reducing_gas="none",
            inert_gas="vacuum",
            cofeed_or_reactive_gas="none",
            total_flow_original="not_applicable",
            gas_composition_summary="vacuum annealing",
            process_note="Continuous 1 nm Ni film agglomerated into catalytic clusters.",
        ),
        process_row(
            run_id,
            2,
            "hydrogen_plasma_treatment",
            **common,
            temperature_program_summary="pure-H2 microwave-plasma catalyst treatment",
            holding_time_min="10",
            carbon_source="none",
            reducing_gas="H2",
            reducing_gas_flow_original=f"{item['h2']} sccm",
            inert_gas="none",
            cofeed_or_reactive_gas="none",
            total_flow_original=f"{item['h2']} sccm",
            gas_composition_summary=f"pure H2 at {item['h2']} sccm",
            process_note=f"Microwave input {item['power']} W.",
        ),
        process_row(
            run_id,
            3,
            "microwave_PECVD_CNT_growth",
            **common,
            temperature_program_summary="isothermal plasma-enhanced CNT growth",
            holding_time_min="20",
            carbon_source="CH4",
            carbon_source_flow_original=f"{item['ch4']} sccm",
            reducing_gas="H2",
            reducing_gas_flow_original=f"{item['h2']} sccm",
            inert_gas="none",
            cofeed_or_reactive_gas="O2" if item["o2"] else "none",
            cofeed_flow_original=(f"{item['o2']} sccm" if item["o2"] else "0 sccm"),
            total_flow_original=f"{item['h2'] + item['ch4'] + item['o2']} sccm",
            gas_composition_summary=(
                f"H2 {item['h2']} sccm; CH4 {item['ch4']} sccm; O2 {item['o2']} sccm"
            ),
            process_note=(
                f"Microwave input {item['power']} W; pressure and power were "
                "coupled to hold plasma volume constant."
            ),
        ),
    ]


def model_process_rows(item: dict[str, Any], run_id: str) -> list[dict[str, str]]:
    return [
        process_row(
            run_id,
            1,
            "CFD_simulation",
            reactor_type="2D axisymmetric model of microwave PECVD bell jar",
            scale_level="computational_model",
            reactor_material="modeled quartz enclosure and substrate holder",
            reactor_size_summary="geometry matched experimental reactor",
            reactor_setup_summary=(
                "ANSYS Fluent 12; steady laminar LTE neutral-species finite-rate model"
            ),
            catalyst_loading_mass_g="",
            temperature_setpoint_C=("850" if item["model_kind"] == "baseline" else ""),
            temperature_range_reported_C=str(item["temp_c"]),
            temperature_program_summary=(
                f"substrate-temperature condition {item['temp_k']} K; wall 400 K"
            ),
            holding_time_min="not_applicable",
            heating_rate_C_min="not_applicable",
            cooling_condition="not_applicable",
            pressure_original="10 mbar",
            pressure_kPa="1",
            carbon_source="CH4",
            carbon_source_flow_original="10 vol%",
            reducing_gas="H2",
            reducing_gas_flow_original="90 vol%",
            inert_gas="none",
            cofeed_or_reactive_gas="none",
            cofeed_flow_original="0 vol%",
            total_flow_original="inlet velocity 0.1326 m/s",
            gas_composition_summary="10 vol% CH4 and 90 vol% H2 at 298 K inlet",
            process_note=(
                "Wall 400 K; plasma heat source 0.634e7 W/m3; surface site "
                "density 5.0e-10 mol/cm2 for the baseline calculation."
            ),
        )
    ]


def product(item: dict[str, Any], run_id: str) -> dict[str, str]:
    if is_model(item):
        baseline = item["model_kind"] == "baseline"
        return yield_row(
            run_id,
            primary_yield_metric="calculated_CNT_growth_rate",
            yield_original=(
                "8.3 micrometre/h"
                if baseline
                else "0.5-45 micrometre/h over 873-1273 K"
            ),
            yield_definition_original="surface-model CNT axial growth rate",
            yield_calculation_method=(
                "CFD gas/surface chemistry with fitted surface site density"
            ),
            yield_value_standardized="8.3" if baseline else "",
            yield_unit_standardized="micrometre/h",
            secondary_result_summary=run_summary(item),
            CNT_type_reported="MWCNT model",
            CNT_type_confirmed="not_applicable_to_simulation",
            product_mixture_summary="not_applicable_to_simulation",
            CNT_type_evidence="model calibrated against experimental deposition rate",
            SWCNT_or_few_wall_evidence_summary="not_applicable",
            RBM_peak_reported="not_applicable",
            outer_diameter_mean_nm="",
            outer_diameter_range_nm="",
            inner_diameter_mean_nm="",
            wall_number_summary="not simulated",
            length_summary="calculated axial growth rate only",
            morphology="not simulated",
            alignment_or_array="not simulated",
            Raman_ratio_type="not_applicable",
            Raman_ratio_value="",
            Raman_laser_wavelength_nm="",
            TGA_carbon_content_wt_percent="",
            purified_product_purity_wt_percent="",
            purity_basis="not_applicable",
            residue_summary="not_applicable",
            amorphous_carbon_level="not simulated",
            BET_surface_area_product_m2_g="",
            characterization_methods="ANSYS Fluent 12 CFD and surface kinetics",
            post_treatment_or_purification="not_applicable",
            purification_condition="not_applicable",
            application_property_summary="model interpretation only",
            notes="This record is a grouped calculation, not a physical synthesis run.",
        )

    positive = item["code"] in {"E2", "E4", "E6", "E8", "OPTI"}
    optimum = item["code"] == "OPTI"
    return yield_row(
        run_id,
        primary_yield_metric="SEM_CNT_growth_outcome",
        yield_original=item["outcome"],
        yield_definition_original="qualitative SEM outcome after 20 min PECVD",
        yield_calculation_method="direct SEM observation; no mass yield reported",
        yield_value_standardized="",
        yield_unit_standardized="qualitative",
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=run_summary(item),
        CNT_type_reported="multi-walled carbon nanotubes" if optimum else "nanotubes",
        CNT_type_confirmed="MWCNT"
        if optimum
        else ("CNT" if positive else "none_or_few"),
        product_mixture_summary="CNTs on Ni-covered Si substrate",
        CNT_type_evidence="SEM; catalyst-at-tip morphology for OPTI",
        SWCNT_or_few_wall_evidence_summary="wall number only assigned as MWCNT for OPTI",
        RBM_peak_reported="not_reported",
        outer_diameter_mean_nm="40" if optimum else "",
        outer_diameter_range_nm="",
        inner_diameter_mean_nm="",
        wall_number_summary="multi-walled for OPTI; otherwise not quantified",
        length_summary="about 1 micrometre" if optimum else "qualitative only",
        morphology=(
            "regular coverage; catalyst particle at tube top; top-growth"
            if optimum
            else item["outcome"]
        ),
        alignment_or_array="dense regular substrate coverage"
        if optimum
        else "not quantified",
        Raman_ratio_type="not_reported",
        Raman_ratio_value="",
        Raman_laser_wavelength_nm="",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis="as-grown substrate-bound product",
        residue_summary="Ni catalyst remains at CNT tip for OPTI",
        amorphous_carbon_level="not_quantified",
        BET_surface_area_product_m2_g="",
        characterization_methods="SEM; AFM for catalyst-surface context",
        post_treatment_or_purification="none reported",
        purification_condition="not_reported",
        application_property_summary="no application test",
        notes="No physical run-specific mass yield or carbon conversion was reported.",
    )


def cost_review(item: dict[str, Any], run_id: str) -> dict[str, str]:
    model = is_model(item)
    return cost_row(
        run_id,
        scale_level_demonstrated=(
            "computational model" if model else "laboratory substrate PECVD"
        ),
        scale_level_claimed="large-area uniform coverage discussed; no pilot scale",
        scale_evidence_summary=run_summary(item),
        reactor_capacity_or_throughput=(
            "10 cm diameter bell jar; substrate-scale batch"
            if not model
            else "not_applicable_to_simulation"
        ),
        continuous_operation_time_h="",
        catalyst_lifetime_or_reuse="not_reported",
        catalyst_reuse_cycles="not_reported",
        batch_stability="not_reported",
        scale_up_issue=(
            "microwave-plasma uniformity, substrate area, Ni-film control, "
            "flammable gas handling and absence of mass-productivity data"
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="not_reported",
        cost_driver_summary="microwave power, vacuum/TVA deposition and process gases",
        safety_risk=(
            "microwave plasma, high voltage, hot substrate and flammable H2/CH4; "
            "OPTI also combines H2 and O2"
        ),
        emission_or_waste="unreacted CH4/H2 and deposited carbon; no balance reported",
        industrial_readiness_assessment=(
            "preliminary computational study"
            if model
            else "laboratory thin-film PECVD demonstration"
        ),
        reproduction_value="high",
        reproduction_priority="high" if item["code"] in {"E2", "OPTI"} else "medium",
        recommended_next_action=(
            "measure run-specific CNT mass yield, conversion, wall count, "
            "alignment, catalyst-particle distribution and scale uniformity"
        ),
        review_note=(
            "Simulation records must not be pooled with physical synthesis runs."
            if model
            else "Pressure and microwave power were intentionally coupled."
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
            "notes": "Values checked against the local publisher PDF and rendered pages.",
        }
    )
    tables["evidence_index"].append(item)


def add_run(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    item: dict[str, Any],
) -> str:
    run_id = f"{SOURCE_ID}_{item['code']}"
    summary = run_summary(item)
    source = run_row(
        SOURCE_ID,
        item["code"],
        f"{'CFD model' if is_model(item) else 'PECVD experiment'} {item['code']}",
        summary,
        "medium" if is_model(item) or item["code"] == "E7" else "high",
    )
    if is_model(item):
        source["data_type"] = "computational_model_record"
        source["target_track"] = "CNT_growth_modeling"
    tables["source_run"].append(source)
    cat = catalyst(item, run_id)
    tables["catalyst_system"].append(cat)
    stages = (
        model_process_rows(item, run_id)
        if is_model(item)
        else physical_process_rows(item, run_id)
    )
    tables["reactor_process_gas"].extend(stages)
    prod = product(item, run_id)
    tables["yield_quality"].append(prod)
    cost = cost_review(item, run_id)
    tables["cost_scale_review"].append(cost)

    run_span = (
        MODEL_SPAN
        if is_model(item)
        else (OPTI_SPAN if item["code"] == "OPTI" else RESULT_SPAN)
    )
    run_page = 12 if is_model(item) else (10 if item["code"] == "OPTI" else 9)
    add_evidence(
        tables,
        store,
        run_id,
        "RUN",
        "source_run",
        run_id,
        run_span,
        run_page,
        summary,
        "Run identity, conditions and result.",
        confidence=source["extraction_confidence"],
    )
    add_evidence(
        tables,
        store,
        run_id,
        "CATALYST",
        "catalyst_system",
        cat["catalyst_id"],
        TVA_SPAN,
        2,
        (
            "Ni/Si catalyst: 1 nm Ni film deposited by TVA at residual pressure "
            "3e-6 torr; filament 60 A and 20 V AC; anode ramp about 1000 V/min; "
            "18-20 s deposition at about 0.05 nm/s; 120 min high-vacuum cooling. "
            f"Activation context: {cat['activation_condition']}. AFM RMS roughness "
            "1.864 nm before and 3.485 nm after 850 C treatment; these are not "
            "catalyst-particle diameters."
        ),
        "Catalyst deposition, activation and dimension semantics.",
    )
    for stage in stages:
        page = 12 if is_model(item) else 3
        span = MODEL_SPAN if is_model(item) else PROTOCOL_SPAN
        stage_text = (
            f"Stage {stage['stage_order']} {stage['stage_type']}; reactor "
            f"{stage['reactor_type']}; material {stage['reactor_material']}; "
            f"size {stage['reactor_size_summary']}; setup "
            f"{stage['reactor_setup_summary']}; temperature "
            f"{stage['temperature_setpoint_C']} C; range "
            f"{stage['temperature_range_reported_C']} C; program "
            f"{stage['temperature_program_summary']}; duration "
            f"{stage['holding_time_min']} min; pressure "
            f"{stage['pressure_original']} / {stage['pressure_kPa']} kPa; "
            f"carbon source {stage['carbon_source']} at "
            f"{stage['carbon_source_flow_original']}; H2 "
            f"{stage['reducing_gas_flow_original']}; cofeed "
            f"{stage['cofeed_flow_original']}; total "
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
            span,
            page,
            stage_text,
            f"Process/model stage {stage['stage_order']} support.",
        )
    product_span = (
        MODEL_SPAN
        if is_model(item)
        else (OPTI_SPAN if item["code"] == "OPTI" else RESULT_SPAN)
    )
    product_page = 12 if is_model(item) else (10 if item["code"] == "OPTI" else 9)
    add_evidence(
        tables,
        store,
        run_id,
        "PRODUCT",
        "yield_quality",
        prod["product_id"],
        product_span,
        product_page,
        (
            f"{summary} Yield original: {prod['yield_original']}; standardized "
            f"value {prod['yield_value_standardized']} "
            f"{prod['yield_unit_standardized']}; outer diameter "
            f"{prod['outer_diameter_mean_nm']} nm; length "
            f"{prod['length_summary']}."
        ),
        "Experimental morphology or modeled growth-rate result.",
        confidence="medium" if is_model(item) or item["code"] == "E7" else "high",
        status="calculated" if is_model(item) else "reported",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "COST",
        "cost_scale_review",
        run_id,
        ABSTRACT_SPAN if not is_model(item) else MODEL_SPAN,
        1 if not is_model(item) else 12,
        (
            f"Scale assessment for {item['code']}: {cost['scale_evidence_summary']} "
            f"Demonstrated scale {cost['scale_level_demonstrated']}; reactor "
            f"capacity {cost['reactor_capacity_or_throughput']}; no quantitative "
            "cost or mass-throughput study; hazards include microwave plasma, "
            "high voltage, hot substrate and flammable gases."
        ),
        "Scale, cost-data gap and safety context.",
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
                "Eleven records: eight Taguchi PECVD experiments, one oxygen-added "
                "OPTI experiment, one baseline CFD calculation and one grouped "
                "CFD substrate-temperature sweep."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_publisher_pdf"
    master["notes"] += (
        " Tables 1, 4 and 5 and Figs. 4-7 were visually checked. Computational "
        "records are explicitly separated from physical synthesis runs."
    )

    run_ids = {item["code"]: add_run(tables, store, item) for item in ALL_RUNS}
    e2 = run_ids["E2"]
    e3 = run_ids["E3"]
    e7 = run_ids["E7"]
    opti = run_ids["OPTI"]
    model = run_ids["CFD_OPTI_BASELINE"]
    sweep = run_ids["CFD_TEMPERATURE_SWEEP"]
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_DUPLICATED_E5_001",
                SOURCE_ID,
                e7,
                "source_typographical_error",
                "yield_quality",
                f"{e7}_PROD",
                "yield_original",
                (
                    "The results text lists the four 700 C samples as E1, E3, "
                    "E5 and E5. Table 1 shows E7 is the remaining 700 C run, so "
                    "the no/few-CNT outcome is assigned to E7 as an explicit inference."
                ),
                f"EVD_{e7}_RUN;EVD_{e7}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_H_ATOM_APPROX_001",
                SOURCE_ID,
                e2,
                "figure_read_approximation",
                "source_run",
                e2,
                "run_summary",
                (
                    "H-atom mole fractions for E1-E8 were visually approximated "
                    "from Fig. 5 and are 0D model calculations, not measured gas data."
                ),
                f"EVD_{e2}_RUN",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_COUPLED_FACTORS_001",
                SOURCE_ID,
                e3,
                "confounded_design_factors",
                "reactor_process_gas",
                f"{e3}_S03",
                "process_note",
                (
                    "Pressure and microwave input power changed together to "
                    "maintain plasma volume, so their independent effects cannot "
                    "be separated from this Taguchi design."
                ),
                f"EVD_{e3}_PROCESS_3",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_OPTI_SAFETY_001",
                SOURCE_ID,
                opti,
                "safety_driven_condition_change",
                "reactor_process_gas",
                f"{opti}_S03",
                "gas_composition_summary",
                (
                    "The O2 controller lower limit was 1 sccm. H2 was raised "
                    "from 10 to 90 sccm to avoid the H2/O2 explosion-limit regime."
                ),
                f"EVD_{opti}_RUN;EVD_{opti}_PROCESS_3",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SIZE_SEMANTICS_001",
                SOURCE_ID,
                opti,
                "dimension_semantics",
                "catalyst_system",
                f"{opti}_CAT",
                "catalyst_particle_size_qualifier",
                (
                    "The reported 1 nm is Ni film thickness and the 1.864/3.485 nm "
                    "values are AFM RMS roughness; no catalyst-particle diameter "
                    "distribution was reported."
                ),
                f"EVD_{opti}_CATALYST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_MODEL_SEPARATION_001",
                SOURCE_ID,
                model,
                "model_experiment_boundary",
                "source_run",
                model,
                "data_type",
                (
                    "The CFD baseline and temperature sweep are calculation "
                    "records and must not be counted as physical CNT syntheses."
                ),
                f"EVD_{model}_RUN;EVD_{sweep}_RUN",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_REACTION_COUNT_001",
                SOURCE_ID,
                model,
                "internal_source_discrepancy",
                "yield_quality",
                f"{model}_PROD",
                "notes",
                (
                    "The abstract states 17 surface reactions, while the surface-"
                    "chemistry section states 18 heterogeneous reactions."
                ),
                f"EVD_{model}_RUN",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SITE_DENSITY_001",
                SOURCE_ID,
                model,
                "fitted_model_parameter",
                "yield_quality",
                f"{model}_PROD",
                "yield_calculation_method",
                (
                    "Surface site density 5.0e-10 mol/cm2 was adjusted to "
                    "reproduce experimental deposition-rate values and was not "
                    "independently measured."
                ),
                f"EVD_{model}_PROCESS_1;EVD_{model}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_NO_PHYSICAL_YIELD_001",
                SOURCE_ID,
                e2,
                "critical_data_gap",
                "yield_quality",
                f"{e2}_PROD",
                "yield_value_standardized",
                (
                    "The physical E1-E8 and OPTI experiments report SEM morphology "
                    "but no run-specific CNT mass yield, carbon conversion or "
                    "measured axial growth rate."
                ),
                f"EVD_{e2}_PRODUCT;EVD_{opti}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_POWER_ROUNDING_001",
                SOURCE_ID,
                opti,
                "rounding_discrepancy",
                "reactor_process_gas",
                f"{opti}_S03",
                "process_note",
                (
                    "The abstract rounds optimized microwave power to 342 W; "
                    "Table 4 reports 342.82 W, which is retained as the exact value."
                ),
                f"EVD_{opti}_RUN;EVD_{opti}_PROCESS_3",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_TEMPERATURE_CONVERSION_001",
                SOURCE_ID,
                e2,
                "reported_unit_pair",
                "reactor_process_gas",
                f"{e2}_S03",
                "temperature_setpoint_C",
                (
                    "Table 1 reports 973 and 1123 K, while the results discuss "
                    "700 and 850 C. Both reported representations are retained."
                ),
                f"EVD_{e2}_RUN;EVD_{e2}_PROCESS_3",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CHARACTERIZATION_GAPS_001",
                SOURCE_ID,
                opti,
                "critical_data_gap",
                "yield_quality",
                f"{opti}_PROD",
                "wall_number_summary",
                (
                    "OPTI is identified as MWCNT by SEM description, but exact "
                    "wall count, alignment metric, diameter distribution, Raman "
                    "quality and product purity were not reported."
                ),
                f"EVD_{opti}_PRODUCT",
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
