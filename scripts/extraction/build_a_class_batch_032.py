#!/usr/bin/env python3
"""Build the thirty-second evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 32
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_CC1837EDE2344C3D"
HTML_REF = f"data/interim/parsed_text/{SOURCE_ID}.txt"
XML_REF = f"data/raw/fulltext/supplementary/{SOURCE_ID}/PMC9057708.xml"
SI_REF = f"data/raw/fulltext/supplementary/{SOURCE_ID}/RA-010-D0RA07440C-s001.pdf"
SI_RENDER_REF = f"data/raw/fulltext/supplementary/{SOURCE_ID}/rendered/si-14.png"

PREP_SPAN = "SPAN_3D8C3EE03FC1EDA64140"
PROCESS_SPAN = "SPAN_9E6925641D9BFB66CECB"
PROPERTY_SPAN = "SPAN_815AB7A934EBD0B3768F"
HYDROGEN_SPAN = "SPAN_3AFD1985AB7A879B102E"
CONVERSION_SPAN = "SPAN_665282B3156713386CDA"
LONG_SPAN = "SPAN_BBC7E4969219D5FF1DBC"
DEACTIVATION_SPAN = "SPAN_B50B5D413AA000E4E179"
MORPHOLOGY_SPAN = "SPAN_4DCC49CFBBF955B4E453"
CONCLUSION_SPAN = "SPAN_80E702652CC9847073A6"
ECONOMICS_SPAN = "SPAN_6D87C665F52E282BFBB9"


CATALYSTS = {
    "RU_ZSM5": {
        "label": "3 wt% Ru/ZSM-5",
        "active": "Ru",
        "support": "ZSM-5, SiO2/Al2O3 = 23:1",
        "ratio": "3 wt% Ru",
        "prep": (
            "Incipient wet impregnation with Ru(NO)NO3 solution; air drying "
            "at 110 C for 12 h between additions; air calcination at 500 C "
            "for 5 h."
        ),
        "reduction_temp": 500,
        "reduction_min": 300,
        "bet": "297",
        "pore_volume": "0.27",
        "pore_size": "3.65",
        "size_note": (
            "Ru chemisorption crystallite size 44.64 +/- 1.31 nm and "
            "dispersion 2.94 +/- 0.08%; retained as Ru crystallite context."
        ),
        "state": "Ru species reduced on crystalline ZSM-5",
        "deactivation": "CNT growth on outer zeolite surface can block access",
        "cnt": "CNT",
        "morphology": "CNTs confirmed by SEM/TEM",
    },
    "ZSM5": {
        "label": "commercial ZSM-5",
        "active": "none intentionally added",
        "support": "ZSM-5, SiO2/Al2O3 = 23:1",
        "ratio": "no Ru",
        "prep": "Commercial Alfa Aesar ZSM-5 used as received.",
        "reduction_temp": "",
        "reduction_min": "",
        "bet": "363",
        "pore_volume": "0.32",
        "pore_size": "3.56",
        "size_note": "No active-metal particle size reported.",
        "state": "crystalline ZSM-5 containing native/trace active sites",
        "deactivation": "CNT growth on outer zeolite surface can block access",
        "cnt": "CNT",
        "morphology": "CNTs confirmed by SEM/TEM",
    },
    "RU_AC": {
        "label": "3 wt% Ru/activated carbon",
        "active": "Ru",
        "support": "commercial activated carbon",
        "ratio": "3 wt% Ru",
        "prep": (
            "Incipient wet impregnation with Ru(NO)NO3 solution; air drying "
            "at 110 C for 12 h between additions; N2 calcination at 500 C "
            "for 5 h in a fixed bed."
        ),
        "reduction_temp": 600,
        "reduction_min": 300,
        "bet": "693",
        "pore_volume": "0.65",
        "pore_size": "1.88",
        "size_note": (
            "Ru chemisorption crystallite size 42.46 +/- 0.50 nm and "
            "dispersion 3.16 +/- 0.04%; retained as Ru crystallite context."
        ),
        "state": "reduced Ru on amorphous activated carbon",
        "deactivation": (
            "weak Ru-support interaction, Ru detachment, carbon coverage and "
            "pore blocking caused continuous deactivation"
        ),
        "cnt": "CNT",
        "morphology": "Ru addition changed AC product from turbostratic carbon to CNTs",
    },
    "AC": {
        "label": "commercial activated carbon",
        "active": "none intentionally added",
        "support": "activated carbon",
        "ratio": "no Ru",
        "prep": "Commercial Alfa Aesar activated carbon used as received.",
        "reduction_temp": 700,
        "reduction_min": 30,
        "bet": "776",
        "pore_volume": "0.75",
        "pore_size": "1.89",
        "size_note": "No active-metal particle size reported.",
        "state": "amorphous activated carbon",
        "deactivation": "carbon deposition and pore-mouth blocking",
        "cnt": "turbostratic_carbon",
        "morphology": "turbostratic carbon; no CNT assignment",
    },
    "AB": {
        "label": "KOH-activated Douglas-fir biochar",
        "active": "native alkali/alkaline-earth ash species",
        "support": "Douglas-fir biochar carbon",
        "ratio": "3 g KOH per 1 g biochar during activation",
        "prep": (
            "Douglas-fir fast-pyrolysis biochar; KOH activation at 3:1 "
            "KOH/biochar. Dried 105 C for 12 h, held 400 C for 1 h then "
            "800 C for 2 h under N2, washed with 0.1 M HCl/DI water to pH 7, "
            "dried 105 C for 12 h and ball-milled at 400 rpm for 2 h."
        ),
        "reduction_temp": 700,
        "reduction_min": 30,
        "bet": "3256",
        "pore_volume": "1.78",
        "pore_size": "1.10",
        "size_note": (
            "No active-particle diameter reported; ash 3.9 +/- 0.3 wt% and "
            "82% microporous structure were reported."
        ),
        "state": "high-surface-area microporous activated biochar with ash species",
        "deactivation": (
            "initial rapid decline then stable conversion; CNT autocatalysis "
            "and remaining surface area proposed to extend life"
        ),
        "cnt": "CNT",
        "morphology": "CNTs confirmed by SEM/TEM",
    },
    "HB": {
        "label": "heat-treated Douglas-fir biochar",
        "active": "native ash species",
        "support": "Douglas-fir biochar carbon",
        "ratio": "no added metal",
        "prep": (
            "Douglas-fir fast-pyrolysis biochar heat-treated at 800 C for "
            "2 h under 0.3 L/min N2 with 5 C/min ramp, cooled under N2 and "
            "ball-milled at 400 rpm for 2 h."
        ),
        "reduction_temp": 700,
        "reduction_min": 30,
        "bet": "109",
        "pore_volume": "0.09",
        "pore_size": "1.64",
        "size_note": (
            "No active-particle diameter reported; ash content 7.6 +/- 0.3 wt%."
        ),
        "state": "heat-treated amorphous/turbostratic biochar with ash species",
        "deactivation": "low surface area and carbon deposition",
        "cnt": "no_CNT_observed",
        "morphology": "tube-like SEM appearance but no CNT observed by TEM",
    },
}


SHORT_01 = [
    ("RU_ZSM5", 40, 0.14),
    ("ZSM5", 21, 0.07),
    ("RU_AC", 73, 0.26),
    ("AC", 51, 0.18),
    ("AB", 69, 0.23),
    ("HB", 41, 0.14),
]

SHORT_04 = [
    ("RU_ZSM5", 26, 0.32),
    ("ZSM5", 9, 0.12),
    ("RU_AC", 62, 0.76),
    ("AC", 35, 0.45),
    ("AB", 59, 0.72),
    ("HB", 29, 0.35),
]

RUNS: list[dict[str, Any]] = [
    *[
        {
            "code": f"{key}_WHSV_0P1_8H",
            "catalyst": key,
            "whsv": 0.1,
            "duration_h": 8,
            "conversion": conversion,
            "hydrogen": hydrogen,
            "visual": False,
            "morphology_scope": True,
        }
        for key, conversion, hydrogen in SHORT_01
    ],
    {
        "code": "BLANK_WHSV_0P1_8H",
        "catalyst": "BLANK",
        "whsv": 0.1,
        "duration_h": 8,
        "conversion": "2-3",
        "hydrogen": "",
        "visual": False,
        "morphology_scope": False,
    },
    *[
        {
            "code": f"{key}_WHSV_0P4_8H",
            "catalyst": key,
            "whsv": 0.4,
            "duration_h": 8,
            "conversion": conversion,
            "hydrogen": hydrogen,
            "visual": True,
            "morphology_scope": False,
        }
        for key, conversion, hydrogen in SHORT_04
    ],
    {
        "code": "RU_AC_WHSV_0P1_60H",
        "catalyst": "RU_AC",
        "whsv": 0.1,
        "duration_h": 60,
        "conversion": 21,
        "hydrogen": "",
        "visual": False,
        "morphology_scope": True,
    },
    {
        "code": "AB_WHSV_0P1_60H",
        "catalyst": "AB",
        "whsv": 0.1,
        "duration_h": 60,
        "conversion": 51,
        "hydrogen": "",
        "visual": False,
        "morphology_scope": True,
    },
]


def run_summary(item: dict[str, Any]) -> str:
    if item["catalyst"] == "BLANK":
        return (
            "Empty Inconel-reactor control at 800 C, atmospheric pressure, "
            "50% CH4/50% N2 and nominal 0.1 WHSV for 8 h; methane conversion "
            "was 2-3%, attributed to Ni/Fe reactor components."
        )
    cat = CATALYSTS[item["catalyst"]]
    qualifier = "figure-read approximate" if item["visual"] else "reported"
    hydrogen = (
        f", H2 production {item['hydrogen']} mmol/min" if item["hydrogen"] != "" else ""
    )
    return (
        f"{cat['label']} at 800 C, atmospheric pressure, 50% CH4/50% N2, "
        f"{item['whsv']} WHSV for {item['duration_h']} h: methane conversion "
        f"{item['conversion']}%{hydrogen} ({qualifier} endpoint)."
    )


def catalyst(item: dict[str, Any], run_id: str) -> dict[str, str]:
    if item["catalyst"] == "BLANK":
        return catalyst_row(
            run_id,
            catalyst_label="empty-reactor control",
            active_metals="Ni and Fe reactor-wall components, unintentionally active",
            support_material="Inconel reactor wall",
            promoter="none",
            metal_ratio_original="not_applicable",
            metal_ratio_standardized="not_applicable",
            precursor_summary="none",
            preparation_method="none",
            preparation_modifier="empty reactor",
            preparation_detail="No catalyst charge was placed in the reactor.",
            drying_condition="not_applicable",
            calcination_condition="not_applicable",
            reduction_condition="not_applicable",
            activation_condition="not_applicable",
            post_preparation_condition="empty Inconel tube",
            catalyst_particle_size_mean_nm="",
            catalyst_particle_size_range_nm="",
            catalyst_particle_size_qualifier="not_applicable",
            phase_or_state_summary="Inconel reactor containing Ni and Fe",
            dispersion_summary="not_applicable",
            deactivation_summary="not assessed",
        )
    cat = CATALYSTS[item["catalyst"]]
    reduction = (
        f"{cat['reduction_temp']} C for {cat['reduction_min']} min in 10 mL/min H2"
        if cat["reduction_temp"] != ""
        else "no reduction condition reported for bare ZSM-5"
    )
    return catalyst_row(
        run_id,
        catalyst_label=cat["label"],
        active_metals=cat["active"],
        support_material=cat["support"],
        promoter="none",
        metal_ratio_original=cat["ratio"],
        metal_ratio_standardized=cat["ratio"],
        precursor_summary=(
            "Ru(NO)NO3 in 1.5 w/v% Ru solution"
            if item["catalyst"].startswith("RU_")
            else "commercial material or Douglas-fir biochar"
        ),
        preparation_method=(
            "incipient wet impregnation"
            if item["catalyst"].startswith("RU_")
            else (
                "KOH chemical activation"
                if item["catalyst"] == "AB"
                else (
                    "thermal treatment"
                    if item["catalyst"] == "HB"
                    else "commercial material"
                )
            )
        ),
        preparation_modifier="supplementary-method transcription",
        preparation_detail=cat["prep"],
        drying_condition=(
            "110 C for 12 h in air"
            if item["catalyst"].startswith("RU_")
            else (
                "105 C for 12 h after washing"
                if item["catalyst"] == "AB"
                else "not_applicable_or_not_reported"
            )
        ),
        calcination_condition=(
            "500 C for 5 h in air"
            if item["catalyst"] == "RU_ZSM5"
            else (
                "500 C for 5 h under N2"
                if item["catalyst"] == "RU_AC"
                else "not_applicable"
            )
        ),
        reduction_condition=reduction,
        activation_condition=reduction,
        post_preparation_condition="fresh catalyst placed in fixed bed",
        BET_surface_area_m2_g=cat["bet"],
        pore_diameter_nm=cat["pore_size"],
        pore_volume_cm3_g=cat["pore_volume"],
        catalyst_particle_size_mean_nm="",
        catalyst_particle_size_range_nm="",
        catalyst_particle_size_qualifier=cat["size_note"],
        phase_or_state_summary=cat["state"],
        dispersion_summary=cat["size_note"],
        deactivation_summary=cat["deactivation"],
    )


def process_rows(item: dict[str, Any], run_id: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if item["catalyst"] != "BLANK":
        cat = CATALYSTS[item["catalyst"]]
        if cat["reduction_temp"] != "":
            rows.append(
                process_row(
                    run_id,
                    1,
                    "hydrogen_reduction",
                    reactor_type="top-feed Inconel fixed-bed reactor",
                    scale_level="laboratory_fixed_bed",
                    reactor_material="Inconel",
                    reactor_size_summary=("12.7 mm OD, 9.53 mm ID and 533.5 mm length"),
                    reactor_setup_summary="electrically heated top-feed fixed bed",
                    catalyst_loading_mass_g="",
                    temperature_setpoint_C=str(cat["reduction_temp"]),
                    temperature_range_reported_C=str(cat["reduction_temp"]),
                    temperature_program_summary="in situ H2 reduction before reaction",
                    holding_time_min=str(cat["reduction_min"]),
                    heating_rate_C_min="not_reported",
                    cooling_condition="not_applicable before reaction",
                    pressure_original="atmospheric",
                    pressure_kPa="101.325",
                    carbon_source="none",
                    reducing_gas="H2",
                    reducing_gas_flow_original="10 mL/min",
                    inert_gas="none",
                    cofeed_or_reactive_gas="none",
                    total_flow_original="10 mL/min",
                    gas_composition_summary="pure H2 reduction",
                    process_note="Reduction temperature depended on catalyst identity.",
                )
            )
    order = len(rows) + 1
    rows.append(
        process_row(
            run_id,
            order,
            "thermocatalytic_methane_decomposition",
            reactor_type="top-feed Inconel fixed-bed reactor",
            scale_level="laboratory_fixed_bed",
            reactor_material="Inconel",
            reactor_size_summary="12.7 mm OD, 9.53 mm ID and 533.5 mm length",
            reactor_setup_summary=(
                "electric heater, cooled heat exchanger and Agilent 3000A micro-GC"
            ),
            catalyst_loading_mass_g="",
            temperature_setpoint_C="800",
            temperature_range_reported_C="800",
            temperature_program_summary="isothermal methane decomposition",
            holding_time_min=str(item["duration_h"] * 60),
            heating_rate_C_min="not_reported",
            cooling_condition="not_reported",
            pressure_original="atmospheric pressure",
            pressure_kPa="101.325",
            carbon_source="CH4",
            carbon_source_flow_original="50 vol%",
            reducing_gas="none externally added during reaction",
            reducing_gas_flow_original="0 vol%",
            inert_gas="N2",
            inert_gas_flow_original="50 vol%",
            cofeed_or_reactive_gas="none",
            cofeed_flow_original="0 vol%",
            total_flow_original=f"{item['whsv']} h-1 WHSV",
            gas_composition_summary="50 vol% CH4 and 50 vol% N2",
            process_note=(
                "Product gas sampled every 30 min; first reported product "
                "composition after 2 h because of line residence delay."
            ),
        )
    )
    return rows


def product(item: dict[str, Any], run_id: str) -> dict[str, str]:
    blank = item["catalyst"] == "BLANK"
    cat = None if blank else CATALYSTS[item["catalyst"]]
    if blank or item["visual"]:
        standardized = ""
    else:
        standardized = str(item["conversion"])
    morphology = (
        "not characterized for this exact run"
        if not item["morphology_scope"] or blank
        else cat["morphology"]
    )
    cnt_type = (
        "not_characterized" if not item["morphology_scope"] or blank else cat["cnt"]
    )
    hydrogen = (
        f"H2 production {item['hydrogen']} mmol/min; " if item["hydrogen"] != "" else ""
    )
    return yield_row(
        run_id,
        primary_yield_metric="methane_conversion_at_endpoint",
        yield_original=f"{item['conversion']}% methane conversion",
        yield_definition_original=(
            "inlet/outlet CH4 flow from N2 internal-balance calculation"
        ),
        yield_calculation_method=(
            "micro-GC composition with total outlet flow calculated by N2 balance"
        ),
        yield_value_standardized=standardized,
        yield_unit_standardized="percent_CH4_conversion",
        yield_standardization_note=(
            "0.4 WHSV values are visual endpoint estimates and are not "
            "placed in the standardized numeric field."
            if item["visual"]
            else "Endpoint retained without cross-condition conversion."
        ),
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent=str(item["conversion"]),
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=(
            f"{run_summary(item)} {hydrogen}Carbon morphology: {morphology} "
            + (
                "Hydrogen yield was reported above 90% for all six catalysts "
                "at 0.1 WHSV."
                if item["whsv"] == 0.1 and item["duration_h"] == 8 and not blank
                else ""
            )
        ),
        CNT_type_reported=cnt_type,
        CNT_type_confirmed=cnt_type,
        product_mixture_summary="H2-rich gas plus deposited solid carbon",
        CNT_type_evidence=(
            "SEM and TEM of specified spent-catalyst samples"
            if item["morphology_scope"] and not blank
            else "not characterized for this exact condition"
        ),
        SWCNT_or_few_wall_evidence_summary="wall count not reported",
        RBM_peak_reported="not_reported",
        outer_diameter_mean_nm="",
        outer_diameter_range_nm="",
        inner_diameter_mean_nm="",
        wall_number_summary="not_reported",
        length_summary="not_reported",
        morphology=morphology,
        alignment_or_array="not_reported",
        Raman_ratio_type="not_reported",
        Raman_ratio_value="",
        Raman_laser_wavelength_nm="",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis="unpurified spent catalyst/carbon",
        residue_summary="spent carbon catalyst or zeolite plus deposited carbon",
        amorphous_carbon_level="not_quantified",
        BET_surface_area_product_m2_g=(
            "746"
            if item["code"] == "AB_WHSV_0P1_60H"
            else ("1893" if item["code"] == "AB_WHSV_0P1_8H" else "")
        ),
        characterization_methods="micro-GC; SEM; TEM; BET; XRD; TPR",
        post_treatment_or_purification="none reported",
        purification_condition="not_reported",
        application_property_summary="co-production of COx-free hydrogen and carbon",
        notes=(
            "Visual estimates are approximate."
            if item["visual"]
            else "No CNT mass yield, diameter distribution or purity was reported."
        ),
    )


def cost_review(item: dict[str, Any], run_id: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="laboratory fixed bed",
        scale_level_claimed="potential hydrogen-production catalyst; no pilot run",
        scale_evidence_summary=run_summary(item),
        reactor_capacity_or_throughput=(
            f"{item['whsv']} h-1 WHSV; catalyst mass and absolute feed flow not reported"
        ),
        continuous_operation_time_h=str(item["duration_h"]),
        catalyst_lifetime_or_reuse=(
            "active through 60 h with 51% conversion"
            if item["code"] == "AB_WHSV_0P1_60H"
            else (
                "continuous deactivation to 21% conversion at 60 h"
                if item["code"] == "RU_AC_WHSV_0P1_60H"
                else "not a reuse test"
            )
        ),
        catalyst_reuse_cycles="not_reported",
        batch_stability="not_reported",
        scale_up_issue=(
            "carbon removal/regeneration, pore blocking, catalyst mass/feed "
            "basis, reactor-wall activity and CNT separation"
        ),
        quantitative_cost_reported="not_reported_for_this_study",
        quantitative_cost_summary=(
            "Only literature background estimates were cited; no study-specific "
            "capital, operating or catalyst cost model was performed."
        ),
        cost_driver_summary="Ru loading, biochar activation, 800 C heat duty and gas feed",
        safety_risk="flammable CH4/H2 at 800 C; Ru compounds, KOH and HCl handling",
        emission_or_waste="solid carbon/spent catalyst; no direct COx in ideal TCD",
        industrial_readiness_assessment="laboratory catalyst screening",
        reproduction_value="high",
        reproduction_priority=(
            "high" if item["catalyst"] in {"AB", "RU_AC"} else "medium"
        ),
        recommended_next_action=(
            "report catalyst mass and absolute flows, quantify CNT/carbon yield, "
            "regeneration, sulfur tolerance and process energy/economics"
        ),
        review_note="Background cost and energy figures are not experimental run data.",
    )


def add_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    suffix: str,
    table: str,
    record_id: str,
    span_id: str,
    text: str,
    summary: str,
    *,
    source_ref: str = XML_REF,
    locator: str = "official Europe PMC full text",
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
            "evidence_type": "official_fulltext_or_supplement_transcription",
            "source_section": locator,
            "source_locator": locator,
            "source_object_ref": source_ref,
            "evidence_text": text,
            "evidence_summary": summary,
            "notes": "Main text and supplementary information were locally retained.",
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
    confidence = "medium" if item["visual"] else "high"
    tables["source_run"].append(
        run_row(
            SOURCE_ID,
            item["code"],
            (
                "empty-reactor control"
                if item["catalyst"] == "BLANK"
                else CATALYSTS[item["catalyst"]]["label"]
            ),
            summary,
            confidence,
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

    result_span = LONG_SPAN if item["duration_h"] == 60 else CONVERSION_SPAN
    result_ref = SI_REF if item["visual"] else XML_REF
    result_locator = (
        "ESI page 14, Fig. S10"
        if item["visual"]
        else "official Europe PMC results text"
    )
    add_evidence(
        tables,
        store,
        run_id,
        "RUN",
        "source_run",
        run_id,
        result_span,
        summary,
        "Run identity, endpoint and condition.",
        source_ref=result_ref,
        locator=result_locator,
        confidence=confidence,
        status="visual_estimate" if item["visual"] else "reported",
    )

    cat_text = (
        "Empty Inconel reactor; no catalyst charge. Ni and Fe reactor "
        "components were proposed to cause 2-3% methane conversion."
        if item["catalyst"] == "BLANK"
        else (
            f"{cat['catalyst_label']}; active {cat['active_metals']}; support "
            f"{cat['support_material']}; ratio {cat['metal_ratio_original']}; "
            f"preparation {cat['preparation_detail']}; drying "
            f"{cat['drying_condition']}; calcination "
            f"{cat['calcination_condition']}; reduction "
            f"{cat['reduction_condition']}; BET {cat['BET_surface_area_m2_g']} "
            f"m2/g; pore volume {cat['pore_volume_cm3_g']} cm3/g; average pore "
            f"size {cat['pore_diameter_nm']} nm; size context "
            f"{cat['catalyst_particle_size_qualifier']}"
        )
    )
    add_evidence(
        tables,
        store,
        run_id,
        "CATALYST",
        "catalyst_system",
        cat["catalyst_id"],
        PREP_SPAN if item["catalyst"] != "BLANK" else CONVERSION_SPAN,
        cat_text,
        "Catalyst preparation, properties and activation.",
        source_ref=SI_REF if item["catalyst"] != "BLANK" else XML_REF,
        locator=(
            "ESI catalyst preparation and main Table 3"
            if item["catalyst"] != "BLANK"
            else "official Europe PMC results text"
        ),
    )
    for stage in stages:
        stage_text = (
            f"Stage {stage['stage_order']} {stage['stage_type']}; reactor "
            f"{stage['reactor_type']}; material {stage['reactor_material']}; "
            f"size {stage['reactor_size_summary']}; catalyst mass "
            f"{stage['catalyst_loading_mass_g']} g; temperature "
            f"{stage['temperature_setpoint_C']} C; duration "
            f"{stage['holding_time_min']} min; pressure "
            f"{stage['pressure_original']} / {stage['pressure_kPa']} kPa; "
            f"carbon source {stage['carbon_source']} at "
            f"{stage['carbon_source_flow_original']}; H2 "
            f"{stage['reducing_gas_flow_original']}; N2 "
            f"{stage['inert_gas_flow_original']}; total/basis "
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
            PROCESS_SPAN,
            stage_text,
            f"Process stage {stage['stage_order']} support.",
        )
    product_span = (
        MORPHOLOGY_SPAN
        if item["morphology_scope"] and item["catalyst"] != "BLANK"
        else result_span
    )
    add_evidence(
        tables,
        store,
        run_id,
        "PRODUCT",
        "yield_quality",
        prod["product_id"],
        product_span,
        (
            f"{summary} Yield original {prod['yield_original']}; standardized "
            f"value {prod['yield_value_standardized']} "
            f"{prod['yield_unit_standardized']}; conversion field "
            f"{prod['carbon_source_conversion_percent']}%; product "
            f"{prod['CNT_type_confirmed']}; morphology {prod['morphology']}; "
            f"spent-product BET {prod['BET_surface_area_product_m2_g']} m2/g."
        ),
        "Methane conversion, hydrogen production and carbon morphology.",
        source_ref=result_ref,
        locator=result_locator,
        confidence=confidence,
        status="visual_estimate" if item["visual"] else "reported",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "COST",
        "cost_scale_review",
        run_id,
        ECONOMICS_SPAN,
        (
            f"Laboratory Inconel fixed-bed run for {item['duration_h']} h at "
            f"{item['whsv']} h-1 WHSV; catalyst mass and absolute feed flow "
            "not reported. No study-specific cost model; scale-up issues include "
            "800 C heat duty, carbon removal, regeneration and gas safety."
        ),
        "Scale, lifetime, cost-data gap and safety review.",
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
                "Fifteen records: six catalyst endpoints at 0.1 WHSV/8 h, "
                "one empty-reactor control, six visually transcribed endpoints "
                "at 0.4 WHSV/8 h, and two dedicated 60 h stability runs."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = XML_REF
    master["pdf_status"] = "official_Europe_PMC_XML_plus_validated_ESI_PDF"
    master["notes"] += (
        " Europe PMC full-text XML, the 693 kB ESI PDF and rendered ESI page "
        "14 were retained. Fig. S10 endpoints are explicitly marked approximate."
    )

    run_ids = {item["code"]: add_run(tables, store, item) for item in RUNS}
    ab_short = run_ids["AB_WHSV_0P1_8H"]
    ab_long = run_ids["AB_WHSV_0P1_60H"]
    ruac_long = run_ids["RU_AC_WHSV_0P1_60H"]
    blank = run_ids["BLANK_WHSV_0P1_8H"]
    ab_04 = run_ids["AB_WHSV_0P4_8H"]
    ac_short = run_ids["AC_WHSV_0P1_8H"]
    hb_short = run_ids["HB_WHSV_0P1_8H"]
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_FIGURE_READ_001",
                SOURCE_ID,
                ab_04,
                "figure_read_approximation",
                "yield_quality",
                f"{ab_04}_PROD",
                "yield_original",
                (
                    "All six 0.4 WHSV 8 h conversion and H2-production endpoints "
                    "were visually read from ESI Fig. S10 and are approximate."
                ),
                f"EVD_{ab_04}_RUN;EVD_{ab_04}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_MORPHOLOGY_SCOPE_001",
                SOURCE_ID,
                ac_short,
                "measurement_scope",
                "yield_quality",
                f"{ac_short}_PROD",
                "CNT_type_confirmed",
                (
                    "SEM/TEM morphology is tied to the spent samples identified "
                    "in Figs. 8-9 at 0.1 WHSV: four 8 h samples and the 60 h "
                    "Ru-AC/AB samples. It is not propagated to 0.4 WHSV runs."
                ),
                f"EVD_{ac_short}_PRODUCT;EVD_{ruac_long}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_HB_SEM_TEM_001",
                SOURCE_ID,
                hb_short,
                "characterization_discrepancy",
                "yield_quality",
                f"{hb_short}_PROD",
                "morphology",
                (
                    "HB showed a tube-like SEM appearance similar to Ru-AC, "
                    "but no CNTs could be observed in TEM; it is coded as no "
                    "CNT observed rather than confirmed CNT."
                ),
                f"EVD_{hb_short}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_BLANK_REACTOR_001",
                SOURCE_ID,
                blank,
                "reactor_background_activity",
                "catalyst_system",
                f"{blank}_CAT",
                "active_metals",
                (
                    "The empty Inconel reactor converted about 2-3% methane at "
                    "800 C; the authors attribute this to Ni and Fe in the reactor."
                ),
                f"EVD_{blank}_CATALYST;EVD_{blank}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_NO_CARBON_YIELD_001",
                SOURCE_ID,
                ab_short,
                "critical_data_gap",
                "yield_quality",
                f"{ab_short}_PROD",
                "CNT_yield_per_catalyst_g_gcat",
                (
                    "The study reports gas conversion/H2 production and carbon "
                    "identity, but no mass yield, CNT fraction, dimensions, "
                    "purity or solid-carbon balance."
                ),
                f"EVD_{ab_short}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_H2_METRIC_001",
                SOURCE_ID,
                ab_short,
                "metric_definition",
                "yield_quality",
                f"{ab_short}_PROD",
                "secondary_result_summary",
                (
                    "The paper separately reports H2 production rate in mmol/min "
                    "and H2 yield above 90%; these are not interchangeable metrics."
                ),
                f"EVD_{ab_short}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_WHSV_BASIS_001",
                SOURCE_ID,
                ab_short,
                "critical_data_gap",
                "reactor_process_gas",
                f"{ab_short}_S02",
                "total_flow_original",
                (
                    "WHSV is reported, but catalyst mass and absolute CH4/N2 "
                    "feed flow for the reaction runs are not reported in the "
                    "main text or ESI."
                ),
                f"EVD_{ab_short}_PROCESS_2",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_RUN_SPLIT_001",
                SOURCE_ID,
                ab_long,
                "experimental_run_boundary",
                "source_run",
                ab_long,
                "run_summary",
                (
                    "The 60 h AB and Ru-AC stability tests were dedicated "
                    "long-duration experiments selected after the six-catalyst "
                    "8 h screen, so they are represented as separate runs."
                ),
                f"EVD_{ab_long}_RUN;EVD_{ruac_long}_RUN",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_AB_BET_001",
                SOURCE_ID,
                ab_long,
                "time_dependent_catalyst_property",
                "yield_quality",
                f"{ab_long}_PROD",
                "BET_surface_area_product_m2_g",
                (
                    "AB BET area fell from 3256 m2/g fresh to 1893 m2/g after "
                    "8 h and 746 m2/g after 60 h; these are spent-product values "
                    "and are not fresh-catalyst duplicates."
                ),
                f"EVD_{ab_long}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_COST_BOUNDARY_001",
                SOURCE_ID,
                ab_long,
                "cost_boundary",
                "cost_scale_review",
                ab_long,
                "quantitative_cost_summary",
                (
                    "Hydrogen selling-price and energy-demand values in the "
                    "introduction are cited literature background, not a cost "
                    "analysis of the six catalysts tested here."
                ),
                f"EVD_{ab_long}_COST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_DEACTIVATION_001",
                SOURCE_ID,
                ruac_long,
                "deactivation_interpretation",
                "cost_scale_review",
                ruac_long,
                "catalyst_lifetime_or_reuse",
                (
                    "Ru-AC conversion declined continuously to 21% at 60 h, "
                    "whereas AB declined rapidly for about 10 h then remained "
                    "comparatively stable at 51% by 60 h."
                ),
                f"EVD_{ruac_long}_RUN;EVD_{ab_long}_RUN",
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
