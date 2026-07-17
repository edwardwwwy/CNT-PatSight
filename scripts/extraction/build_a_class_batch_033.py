#!/usr/bin/env python3
"""Build the thirty-third evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 33
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_42CA430104DA72AA"
PDF_REF = "data/raw/fulltext/pdf/LIT_42CA430104DA72AA_66eb0daffee5.pdf"

ABSTRACT_SPAN = "SPAN_D254B065AE1BCB00197B"
PREP_SPAN = "SPAN_D6F355EB876B414BA4CF"
ACETYLENE_REACTOR_SPAN = "SPAN_F71383C43778F341946A"
ACETYLENE_PROTOCOL_SPAN = "SPAN_06BBF652F0348357649E"
PARAMETER_RANGE_SPAN = "SPAN_014994D01A579291C37B"
TEMPERATURE_SPAN = "SPAN_ADD7CA265EC1A644C5DE"
REDUCTION_SPAN = "SPAN_A1802F27D5B6B779985D"
TIME_SPAN = "SPAN_8ED231A4EF56B61F526E"
TIME_LATE_SPAN = "SPAN_AB1C200DF8ECE6B94B9C"
GAS_SPAN = "SPAN_0FF397650A647BD64EE0"
DIMENSION_SPAN = "SPAN_0698360E64FC159B3593"
CO_REACTOR_SPAN = "SPAN_274BA9D97FBDF8AC50A8"
CO_PROTOCOL_SPAN = "SPAN_9A3C9EF3866A6FA0FAFF"


RUNS: list[dict[str, Any]] = [
    {
        "code": "NI_C2H2_TEMP_650",
        "metal": "Ni",
        "precursor": "C2H2",
        "temp": 650,
        "reduction": 5,
        "growth": 10,
        "outcome": "practically no secondary nanotubes",
        "series": "temperature",
    },
    {
        "code": "NI_C2H2_TEMP_700",
        "metal": "Ni",
        "precursor": "C2H2",
        "temp": 700,
        "reduction": 5,
        "growth": 10,
        "outcome": "secondary growth occurred but was inferior to 750 C",
        "series": "temperature",
    },
    {
        "code": "NI_C2H2_TEMP_800",
        "metal": "Ni",
        "precursor": "C2H2",
        "temp": 800,
        "reduction": 5,
        "growth": 10,
        "outcome": "secondary growth occurred but was inferior to 750 C",
        "series": "temperature",
    },
    {
        "code": "NI_C2H2_REDUCTION_2P5",
        "metal": "Ni",
        "precursor": "C2H2",
        "temp": 750,
        "reduction": 2.5,
        "growth": 10,
        "outcome": "poor activation; reduction too short to form good catalyst particles",
        "series": "reduction",
    },
    {
        "code": "NI_C2H2_REDUCTION_7P5",
        "metal": "Ni",
        "precursor": "C2H2",
        "temp": 750,
        "reduction": 7.5,
        "growth": 10,
        "outcome": (
            "some locally good activation but very short tubes; many sites "
            "inactive and covered by amorphous carbon"
        ),
        "series": "reduction",
    },
    {
        "code": "NI_C2H2_GROWTH_2P5",
        "metal": "Ni",
        "precursor": "C2H2",
        "temp": 750,
        "reduction": 5,
        "growth": 2.5,
        "outcome": "growth barely begun; very little VGCF activation",
        "series": "growth_time",
    },
    {
        "code": "NI_C2H2_GROWTH_5",
        "metal": "Ni",
        "precursor": "C2H2",
        "temp": 750,
        "reduction": 5,
        "growth": 5,
        "outcome": "significant activation but secondary tubes remained short",
        "series": "growth_time",
    },
    {
        "code": "NI_C2H2_GROWTH_10_OPTIMUM",
        "metal": "Ni",
        "precursor": "C2H2",
        "temp": 750,
        "reduction": 5,
        "growth": 10,
        "outcome": "high activation and good MWCNT coverage on untreated VGCFs",
        "series": "optimum",
    },
    {
        "code": "NI_C2H2_GROWTH_15",
        "metal": "Ni",
        "precursor": "C2H2",
        "temp": 750,
        "reduction": 5,
        "growth": 15,
        "outcome": "activation significantly higher than after 10 min",
        "series": "growth_time",
    },
    {
        "code": "NI_C2H2_GROWTH_20",
        "metal": "Ni",
        "precursor": "C2H2",
        "temp": 750,
        "reduction": 5,
        "growth": 20,
        "outcome": (
            "no clear activation difference versus 15 min; MWCNT outer diameter "
            "12.5 +/- 1.7 nm, inner diameter 5.2 +/- 2.0 nm and 10-20 walls"
        ),
        "series": "growth_time",
    },
    {
        "code": "NI_C2H2_GAS_SCREEN_GROUP",
        "metal": "Ni",
        "precursor": "C2H2",
        "temp": 750,
        "reduction": 5,
        "growth": 10,
        "outcome": (
            "grouped gas-composition screen; gas effect was less important "
            "within tested ranges and optimum was C2H2/H2/Ar = 30/200/420 mL/min"
        ),
        "series": "gas_screen_group",
    },
    *[
        {
            "code": f"FE_C2H2_TEMP_{temp}",
            "metal": "Fe",
            "precursor": "C2H2",
            "temp": temp,
            "reduction": 5,
            "growth": 10,
            "outcome": (
                "Fe inactive for secondary CNT growth on untreated VGCFs"
                + (
                    "; about 300 micrometre CNT forest grew on adjacent SiO2"
                    if temp == 800
                    else ""
                )
            ),
            "series": "fe_acetylene",
        }
        for temp in (700, 750, 800)
    ],
    {
        "code": "FE_CO_GROWTH_30",
        "metal": "Fe",
        "precursor": "CO",
        "temp": 890,
        "reduction": 5,
        "growth": 30,
        "outcome": (
            "no hierarchical secondary CNT growth; 72 inactive Fe particles "
            "measured, 13.5 +/- 2.7 nm on VGCFs and 6.4 +/- 1.4 nm on grid"
        ),
        "series": "fe_co",
    },
    {
        "code": "FE_CO_GROWTH_120",
        "metal": "Fe",
        "precursor": "CO",
        "temp": 890,
        "reduction": 5,
        "growth": 120,
        "outcome": "prolonging synthesis to 2 h produced no significant improvement",
        "series": "fe_co",
    },
]


def is_co(item: dict[str, Any]) -> bool:
    return item["precursor"] == "CO"


def gas_summary(item: dict[str, Any]) -> str:
    if item["series"] == "gas_screen_group":
        return (
            "C2H2 10-50 mL/min, H2 0/130/200 mL/min and Ar "
            "0/270/420/700 mL/min were varied; optimum 30/200/420 mL/min."
        )
    if is_co(item):
        return "growth CO 400 mL/min, H2 200 mL/min and CO2 8 mL/min."
    return "optimum C2H2 30, H2 200 and Ar 420 mL/min; total 650 mL/min."


def run_summary(item: dict[str, Any]) -> str:
    return (
        f"{item['metal']}-sputtered untreated Showa Denko VGCF, "
        f"{item['precursor']} CVD at {item['temp']} C; reduction "
        f"{item['reduction']} min and growth {item['growth']} min. "
        f"{gas_summary(item)} Outcome: {item['outcome']}."
    )


def catalyst(item: dict[str, Any], run_id: str) -> dict[str, str]:
    particle_context = (
        "For the 5 min reduction Ni sample, 24 particles averaged "
        "9.5 +/- 1.9 nm on VGCF and 5.5 +/- 1.3 nm on the grid."
        if item["metal"] == "Ni"
        else (
            "For the 890 C CO/30 min sample, 72 inactive Fe particles "
            "averaged 13.5 +/- 2.7 nm on VGCF and 6.4 +/- 1.4 nm on the grid."
            if is_co(item) and item["growth"] == 30
            else "No run-specific Fe particle distribution reported."
        )
    )
    return catalyst_row(
        run_id,
        catalyst_label=f"sputtered {item['metal']} on Showa Denko VGCF/SiO2",
        active_metals=item["metal"],
        support_material=(
            "untreated highly crystalline Showa Denko vapor-grown carbon "
            "fibers on SiO2/Si"
        ),
        promoter="none",
        metal_ratio_original="sputtering current 20 mA for 15 s",
        metal_ratio_standardized="loading not reported; 20 mA x 15 s sputter",
        precursor_summary=f"pure {item['metal']} sputtering target",
        preparation_method="magnetron sputtering",
        preparation_modifier="AGAR Auto Sputter Coater 108A",
        preparation_detail=(
            "VGCFs about 150 nm diameter dispersed in 1,2-dichloroethane at "
            "0.5-1.5 mg/mL and drop-dried on about 0.5 cm2 SiO2/Si; catalyst "
            "sputtered at 20 mA for 15 s."
        ),
        drying_condition="drop-dried; exact duration not reported",
        calcination_condition="not_applicable",
        reduction_condition=(
            f"in situ at {item['temp']} C for {item['reduction']} min in "
            "H2/Ar atmosphere"
        ),
        activation_condition="hydrogen reduction immediately before growth",
        post_preparation_condition="untreated VGCF support; no acid pretreatment",
        catalyst_particle_size_mean_nm="",
        catalyst_particle_size_range_nm="",
        catalyst_particle_size_qualifier=particle_context,
        phase_or_state_summary=(
            f"{item['metal']} nanoparticles on crystalline carbon-fiber surface"
        ),
        dispersion_summary=particle_context,
        deactivation_summary=(
            "Fe was inactive; possible coalescence/iron carbide poisoning. "
            "Over-reduced Ni had inactive sites and amorphous-carbon coverage."
        ),
    )


def process_rows(item: dict[str, Any], run_id: str) -> list[dict[str, str]]:
    if is_co(item):
        reactor = "vertical laminar-flow CVD reactor"
        material = "2.2 cm ID ceramic tube; 6 mm stainless-steel sample rod"
        size = "2.2 cm tube ID inside 44 cm furnace"
        reduction_comp = "H2 200 mL/min and Ar 400 mL/min"
        growth_total = "608 mL/min"
        carbon_flow = "400 mL/min"
        inert = "none after Ar replaced by CO"
        inert_flow = "0 mL/min during growth"
    else:
        reactor = "horizontal hot-wall CVD reactor"
        material = "40 cm quartz tube, 1.2 cm ID, inside 3.0 cm ID ceramic tube"
        size = "34 cm furnace; about 0.5 cm2 supported sample"
        reduction_comp = "H2/Ar; optimum H2 200 and Ar 420 mL/min"
        growth_total = (
            "tested grouped ranges"
            if item["series"] == "gas_screen_group"
            else "650 mL/min"
        )
        carbon_flow = (
            "10-50 mL/min screen"
            if item["series"] == "gas_screen_group"
            else "30 mL/min"
        )
        inert = "Ar"
        inert_flow = (
            "0/270/420/700 mL/min screen"
            if item["series"] == "gas_screen_group"
            else "420 mL/min"
        )
    return [
        process_row(
            run_id,
            1,
            "hydrogen_reduction",
            reactor_type=reactor,
            scale_level="laboratory_substrate_CVD",
            reactor_material=material,
            reactor_size_summary=size,
            reactor_setup_summary="sample inserted into calibrated hot zone",
            catalyst_loading_mass_g="",
            temperature_setpoint_C=str(item["temp"]),
            temperature_range_reported_C=str(item["temp"]),
            temperature_program_summary="in situ catalyst reduction at growth temperature",
            holding_time_min=str(item["reduction"]),
            heating_rate_C_min="not_reported",
            cooling_condition="not_applicable before growth",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source="none",
            reducing_gas="H2",
            reducing_gas_flow_original=(
                "200 mL/min"
                if is_co(item) or item["series"] != "gas_screen_group"
                else "0/130/200 mL/min screen"
            ),
            inert_gas="Ar",
            inert_gas_flow_original=("400 mL/min" if is_co(item) else inert_flow),
            cofeed_or_reactive_gas="none",
            total_flow_original=reduction_comp,
            gas_composition_summary=reduction_comp,
            process_note="Catalyst metal was sputtered before in-situ reduction.",
        ),
        process_row(
            run_id,
            2,
            "CVD_secondary_CNT_growth",
            reactor_type=reactor,
            scale_level="laboratory_substrate_CVD",
            reactor_material=material,
            reactor_size_summary=size,
            reactor_setup_summary=(
                "VGCF-coated substrate or TEM grid located in reactor hot zone"
            ),
            catalyst_loading_mass_g="",
            temperature_setpoint_C=str(item["temp"]),
            temperature_range_reported_C=str(item["temp"]),
            temperature_program_summary=f"isothermal {item['precursor']} CVD",
            holding_time_min=str(item["growth"]),
            heating_rate_C_min="not_reported",
            cooling_condition=(
                "C2H2/H2 stopped; Ar increased to 700 mL/min for about "
                "1.5 h until below 200 C"
                if not is_co(item)
                else "not_reported"
            ),
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source=item["precursor"],
            carbon_source_flow_original=carbon_flow,
            reducing_gas="H2",
            reducing_gas_flow_original=(
                "200 mL/min"
                if item["series"] != "gas_screen_group"
                else "0/130/200 mL/min screen"
            ),
            inert_gas=inert,
            inert_gas_flow_original=inert_flow,
            cofeed_or_reactive_gas="CO2" if is_co(item) else "none",
            cofeed_flow_original="8 mL/min" if is_co(item) else "0 mL/min",
            total_flow_original=growth_total,
            gas_composition_summary=gas_summary(item),
            process_note=(
                "Gas composition is a grouped screen, not one physical mixture."
                if item["series"] == "gas_screen_group"
                else "Mass-flow-controlled gas delivery."
            ),
        ),
    ]


def product(item: dict[str, Any], run_id: str) -> dict[str, str]:
    positive = item["metal"] == "Ni" and item["temp"] != 650
    exact_dimensions = item["code"] == "NI_C2H2_GROWTH_20"
    forest = item["code"] == "FE_C2H2_TEMP_800"
    return yield_row(
        run_id,
        primary_yield_metric="SEM_visual_activation_and_coverage",
        yield_original=item["outcome"],
        yield_definition_original=(
            "visual SEM estimate of secondary-tube density and length"
        ),
        yield_calculation_method="qualitative SEM/TEM comparison",
        yield_value_standardized="",
        yield_unit_standardized="qualitative",
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=run_summary(item),
        CNT_type_reported=(
            "MWCNT"
            if positive
            else ("CNT forest on adjacent SiO2 only" if forest else "no CNT on VGCF")
        ),
        CNT_type_confirmed=(
            "MWCNT"
            if positive
            else ("support-dependent CNT control" if forest else "none_on_VGCF")
        ),
        product_mixture_summary=(
            "secondary MWCNTs anchored to primary VGCFs"
            if positive
            else "catalyst-coated VGCF without hierarchical secondary CNTs"
        ),
        CNT_type_evidence="SEM and TEM",
        SWCNT_or_few_wall_evidence_summary=(
            "10-20 walls in the 20 min Ni/C2H2 sample"
            if exact_dimensions
            else "not quantified for this run"
        ),
        RBM_peak_reported="not_reported",
        outer_diameter_mean_nm="12.5" if exact_dimensions else "",
        outer_diameter_range_nm="",
        inner_diameter_mean_nm="5.2" if exact_dimensions else "",
        wall_number_summary="10-20 walls" if exact_dimensions else "not_reported",
        length_summary=(
            "about 300 micrometre forest on adjacent SiO2"
            if forest
            else "qualitative short/coverage comparison"
        ),
        morphology=item["outcome"],
        alignment_or_array=(
            "forest on adjacent SiO2, not on VGCF" if forest else "not quantified"
        ),
        Raman_ratio_type="not_reported",
        Raman_ratio_value="",
        Raman_laser_wavelength_nm="",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis="as-grown hierarchical substrate material",
        residue_summary=f"{item['metal']} catalyst on VGCF/SiO2",
        amorphous_carbon_level=(
            "many sites covered after 7.5 min reduction"
            if item["reduction"] == 7.5
            else "not_quantified"
        ),
        BET_surface_area_product_m2_g="",
        characterization_methods="SEM; TEM",
        post_treatment_or_purification="none",
        purification_condition="not_applicable",
        application_property_summary=(
            "candidate fuel-cell/supercapacitor support, sensor or reinforcement; "
            "no application test"
        ),
        notes=(
            "Diameter and wall-count statistics belong only to the explicitly "
            "characterized 20 min Ni/C2H2 sample."
        ),
    )


def cost_review(item: dict[str, Any], run_id: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="laboratory substrate CVD",
        scale_level_claimed="simple route on industrial VGCF feedstock",
        scale_evidence_summary=run_summary(item),
        reactor_capacity_or_throughput=(
            "about 0.5 cm2 substrate; no product-mass throughput"
        ),
        continuous_operation_time_h="",
        catalyst_lifetime_or_reuse="not_reported",
        catalyst_reuse_cycles="not_reported",
        batch_stability="not_reported",
        scale_up_issue=(
            "sputter uniformity on powder, incomplete Fe activation, gas use, "
            "substrate handling and absence of mass-yield data"
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="not_reported",
        cost_driver_summary="VGCF feedstock, sputtering, furnace heat and process gases",
        safety_risk=(
            "flammable acetylene/H2 at high temperature; toxic CO; DCE solvent"
        ),
        emission_or_waste="unreacted gases and catalyst-coated carbon substrate",
        industrial_readiness_assessment="laboratory morphology demonstration",
        reproduction_value="high",
        reproduction_priority=(
            "high" if item["series"] in {"optimum", "growth_time"} else "medium"
        ),
        recommended_next_action=(
            "report full run matrix, absolute CNT mass yield, electrical/mechanical "
            "performance, powder-scale catalyst uniformity and continuous safety"
        ),
        review_note="Industrial-scale VGCF input does not make the secondary CVD process industrial.",
    )


def result_span(item: dict[str, Any]) -> str:
    return {
        "temperature": TEMPERATURE_SPAN,
        "reduction": REDUCTION_SPAN,
        "growth_time": TIME_SPAN if item["growth"] <= 5 else TIME_LATE_SPAN,
        "optimum": TIME_LATE_SPAN,
        "gas_screen_group": GAS_SPAN,
        "fe_acetylene": DIMENSION_SPAN,
        "fe_co": REDUCTION_SPAN,
    }[item["series"]]


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
            "evidence_type": "pdf_text_and_visual_figure_transcription",
            "source_section": f"PDF page {page}",
            "source_locator": f"PDF page {page}",
            "source_object_ref": PDF_REF,
            "evidence_text": text,
            "evidence_summary": summary,
            "notes": "Values checked against the local open-access PDF.",
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
    confidence = (
        "medium"
        if item["series"] in {"temperature", "gas_screen_group", "fe_co"}
        and item["code"] not in {"NI_C2H2_TEMP_650", "FE_CO_GROWTH_30"}
        else "high"
    )
    source = run_row(
        SOURCE_ID,
        item["code"],
        f"{item['metal']}/{item['precursor']} {item['series']}",
        summary,
        confidence,
    )
    if item["series"] == "gas_screen_group":
        source["data_type"] = "experimental_series_summary"
    tables["source_run"].append(source)
    cat = catalyst(item, run_id)
    tables["catalyst_system"].append(cat)
    stages = process_rows(item, run_id)
    tables["reactor_process_gas"].extend(stages)
    prod = product(item, run_id)
    tables["yield_quality"].append(prod)
    cost = cost_review(item, run_id)
    tables["cost_scale_review"].append(cost)

    span = result_span(item)
    page = 3 if item["series"] != "fe_co" else 4
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
        "Run/series identity, condition and qualitative outcome.",
        confidence=confidence,
    )
    add_evidence(
        tables,
        store,
        run_id,
        "CATALYST",
        "catalyst_system",
        cat["catalyst_id"],
        PREP_SPAN,
        5,
        (
            f"{cat['catalyst_label']}; active metal {cat['active_metals']}; "
            f"support {cat['support_material']}; sputtering "
            f"{cat['metal_ratio_original']}; preparation "
            f"{cat['preparation_detail']}; reduction "
            f"{cat['reduction_condition']}; particle context "
            f"{cat['catalyst_particle_size_qualifier']}"
        ),
        "VGCF support, sputtering and catalyst-particle context.",
    )
    for stage in stages:
        stage_span = (
            CO_PROTOCOL_SPAN
            if is_co(item)
            else (
                ACETYLENE_REACTOR_SPAN
                if stage["stage_order"] == "1"
                else ACETYLENE_PROTOCOL_SPAN
            )
        )
        stage_page = 6 if is_co(item) else 5
        stage_text = (
            f"Stage {stage['stage_order']} {stage['stage_type']}; reactor "
            f"{stage['reactor_type']}; material {stage['reactor_material']}; "
            f"size {stage['reactor_size_summary']}; temperature "
            f"{stage['temperature_setpoint_C']} C; duration "
            f"{stage['holding_time_min']} min; pressure "
            f"{stage['pressure_original']} / {stage['pressure_kPa']} kPa; "
            f"carbon source {stage['carbon_source']} at "
            f"{stage['carbon_source_flow_original']}; H2 "
            f"{stage['reducing_gas_flow_original']}; inert "
            f"{stage['inert_gas_flow_original']}; cofeed "
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
            stage_span,
            stage_page,
            stage_text,
            f"Process stage {stage['stage_order']} support.",
        )
    product_span = (
        DIMENSION_SPAN
        if item["code"] in {"NI_C2H2_GROWTH_20", "FE_C2H2_TEMP_800"}
        else span
    )
    add_evidence(
        tables,
        store,
        run_id,
        "PRODUCT",
        "yield_quality",
        prod["product_id"],
        product_span,
        4,
        (
            f"{summary} Product {prod['CNT_type_confirmed']}; outer diameter "
            f"{prod['outer_diameter_mean_nm']} nm; inner diameter "
            f"{prod['inner_diameter_mean_nm']} nm; walls "
            f"{prod['wall_number_summary']}; length {prod['length_summary']}."
        ),
        "SEM/TEM activation, morphology and dimensions.",
        confidence=confidence,
    )
    add_evidence(
        tables,
        store,
        run_id,
        "COST",
        "cost_scale_review",
        run_id,
        ABSTRACT_SPAN,
        2,
        (
            f"Laboratory substrate CVD using about 0.5 cm2 support and "
            f"{gas_summary(item)} No product-mass throughput or quantitative "
            "cost was reported; hazards include hot flammable/toxic gases and DCE."
        ),
        "Scale, cost-data gap and safety review.",
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
                "Sixteen records: ten distinct Ni/C2H2 condition observations, "
                "one grouped gas-composition screen, three Fe/C2H2 temperature "
                "runs and two Fe/CO duration runs."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_open_access_pdf"
    master["notes"] += (
        " Literature-only Table 1 was excluded. Nominally overlapping optimum, "
        "reduction and growth-time observations were merged where appropriate."
    )

    run_ids = {item["code"]: add_run(tables, store, item) for item in RUNS}
    opt = run_ids["NI_C2H2_GROWTH_10_OPTIMUM"]
    ni20 = run_ids["NI_C2H2_GROWTH_20"]
    gas = run_ids["NI_C2H2_GAS_SCREEN_GROUP"]
    fe800 = run_ids["FE_C2H2_TEMP_800"]
    feco = run_ids["FE_CO_GROWTH_30"]
    fe120 = run_ids["FE_CO_GROWTH_120"]
    temp700 = run_ids["NI_C2H2_TEMP_700"]
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_MATRIX_INCOMPLETE_001",
                SOURCE_ID,
                gas,
                "incomplete_run_matrix",
                "source_run",
                gas,
                "run_summary",
                (
                    "The paper lists tested ranges/levels but does not publish "
                    "the full cross-product of gas-flow combinations. The gas "
                    "screen is therefore one grouped series record."
                ),
                f"EVD_{gas}_RUN;EVD_{gas}_PROCESS_2",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_BASELINE_INFERENCE_001",
                SOURCE_ID,
                temp700,
                "shared_baseline_inference",
                "reactor_process_gas",
                f"{temp700}_S02",
                "gas_composition_summary",
                (
                    "The temperature and reduction screens are described around "
                    "the successful condition but individual gas mixtures are not "
                    "restated for every sample; the reported optimum mixture is "
                    "used as the nominal shared baseline."
                ),
                f"EVD_{temp700}_RUN;EVD_{temp700}_PROCESS_2",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_QUALITATIVE_YIELD_001",
                SOURCE_ID,
                opt,
                "qualitative_metric",
                "yield_quality",
                f"{opt}_PROD",
                "yield_original",
                (
                    "Activation is explicitly defined as visual SEM estimation "
                    "of secondary-tube density and length; no mass yield or "
                    "numeric activation scale was reported."
                ),
                f"EVD_{opt}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_DIMENSION_SCOPE_001",
                SOURCE_ID,
                ni20,
                "measurement_scope",
                "yield_quality",
                f"{ni20}_PROD",
                "outer_diameter_mean_nm",
                (
                    "The 12.5 +/- 1.7 nm outer diameter, 5.2 +/- 2.0 nm inner "
                    "diameter and 10-20 walls were measured for the 20 min "
                    "Ni/C2H2 sample and are not assigned to other runs."
                ),
                f"EVD_{ni20}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PARTICLE_SCOPE_001",
                SOURCE_ID,
                opt,
                "catalyst_particle_scope",
                "catalyst_system",
                f"{opt}_CAT",
                "catalyst_particle_size_qualifier",
                (
                    "Ni particle statistics came from 24 particles in a 5 min "
                    "reduction sample; Fe statistics came from 72 inactive "
                    "particles in the 890 C, 30 min CO experiment."
                ),
                f"EVD_{opt}_CATALYST;EVD_{feco}_CATALYST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SUPPORT_DEPENDENCE_001",
                SOURCE_ID,
                fe800,
                "support_dependent_outcome",
                "yield_quality",
                f"{fe800}_PROD",
                "CNT_type_confirmed",
                (
                    "At 800 C Fe/C2H2 was inactive on untreated VGCFs while "
                    "an approximately 300 micrometre CNT forest grew on adjacent "
                    "SiO2, proving the reactor condition itself supported growth."
                ),
                f"EVD_{fe800}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FE_CO_DURATION_001",
                SOURCE_ID,
                fe120,
                "duration_censoring",
                "yield_quality",
                f"{fe120}_PROD",
                "yield_original",
                (
                    "The paper states that extending Fe experiments up to 2 h "
                    "gave no significant improvement; it does not provide a "
                    "separate micrograph or particle statistics for the 120 min run."
                ),
                f"EVD_{fe120}_RUN;EVD_{fe120}_PRODUCT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PRESSURE_001",
                SOURCE_ID,
                opt,
                "critical_data_gap",
                "reactor_process_gas",
                f"{opt}_S02",
                "pressure_original",
                "Operating pressure was not reported for either reactor.",
                f"EVD_{opt}_PROCESS_2",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_NO_PERFORMANCE_TEST_001",
                SOURCE_ID,
                opt,
                "application_gap",
                "cost_scale_review",
                opt,
                "industrial_readiness_assessment",
                (
                    "Fuel-cell, supercapacitor, sensor and reinforcement uses "
                    "are proposed applications; no electrical, electrochemical "
                    "or mechanical performance test was performed."
                ),
                f"EVD_{opt}_COST",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SCALE_001",
                SOURCE_ID,
                opt,
                "scale_limit",
                "cost_scale_review",
                opt,
                "reactor_capacity_or_throughput",
                (
                    "The primary VGCF material was industrially manufactured, "
                    "but the demonstrated secondary CNT process used about "
                    "0.5 cm2 laboratory substrates and no mass throughput."
                ),
                f"EVD_{opt}_COST",
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
    output = BATCH_ROOT / f"batch_{BATCH_NUMBER:03d}_metrics.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
