#!/usr/bin/env python3
"""Build the twenty-third evidence-grounded A-class extraction batch."""

from __future__ import annotations

import json
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


BATCH_NUMBER = 23
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_5D2B63B0DDC58EBA"
PDF_REF = "data/raw/fulltext/pdf/LIT_5D2B63B0DDC58EBA_semantic_scholar.pdf"
PMC_XML_REF = "data/raw/fulltext/supplementary/LIT_5D2B63B0DDC58EBA/PMC10385283.xml"
FIGURE_ROOT = "data/raw/fulltext/supplementary/LIT_5D2B63B0DDC58EBA/PMC10385283_files"
FIG4_REF = f"{FIGURE_ROOT}/micromachines-14-01288-g004.jpg"
FIG6_REF = f"{FIGURE_ROOT}/micromachines-14-01288-g006.jpg"

CATALYST_SYNTHESIS = (
    "Cobalt polymolybdate was prepared from 3.4 g ammonium "
    "heptamolybdate tetrahydrate and 11.3 g cobalt acetate "
    "tetrahydrate in 250 mL water plus 50 mL acetic acid, with 0.6 g "
    "hydrazine sulfate; the solution was stirred 10 min and heated at "
    "67 C for 3 days. In the deposition route, a Co-polymolybdate "
    "suspension was mixed with MgO and evaporated at 60 C. In the "
    "combustion route, magnesium nitrate, Co polymolybdate and ammonium "
    "heptamolybdate were dissolved in citric acid and thermally shocked "
    "in a 540 C muffle furnace."
)

REACTOR_RECIPE = (
    "A stainless-steel reactor casing contained a removable quartz tube "
    "30 mm in diameter and 1 m long. Catalyst powder on a ceramic boat "
    "was held in the cold zone while the evacuated reactor was filled "
    "with H2 and heated to 1000 C. The boat was moved to the hot zone, "
    "reduced in 150 mL/min H2 for 10 min, exposed to constant CH4/H2 "
    "flows for 30 min, and finally purged with 150 mL/min H2 for 10 min."
)

PURIFICATION_RECIPE = (
    "The black carbon product was stirred in concentrated HCl for 4-6 h, "
    "filtered, repeatedly washed with distilled water, and dried at "
    "100 C for 6-12 h."
)

# Figure 4b contains eleven plotted positions A-K. The printed caption lists
# only six Raman spectra and omits several x-axis conditions from the yield
# graph. Values below are visually digitized from the published PDF. H and J
# are unlabeled intermediate positions but have explicit x-axis ticks.
FIG4_SERIES = [
    {"point": "A", "ch4": 50, "h2": 0, "yield": 5200},
    {"point": "B", "ch4": 50, "h2": 50, "yield": 4500},
    {"point": "C", "ch4": 100, "h2": 0, "yield": 9300},
    {"point": "D", "ch4": 100, "h2": 50, "yield": 4900},
    {"point": "E", "ch4": 150, "h2": 0, "yield": 7300},
    {"point": "F", "ch4": 150, "h2": 50, "yield": 4600},
    {"point": "H", "ch4": 100, "h2": 100, "yield": 7300},
    {"point": "G", "ch4": 200, "h2": 0, "yield": 10100},
    {"point": "I", "ch4": 150, "h2": 150, "yield": 3000},
    {"point": "J", "ch4": 200, "h2": 100, "yield": 6500},
    {"point": "K", "ch4": 300, "h2": 0, "yield": 9800},
]

FIG6_SERIES = [
    {"point": "A", "ch4": 50, "h2": 0, "yield": 8200},
    {"point": "B", "ch4": 50, "h2": 50, "yield": 7500},
    {"point": "C", "ch4": 100, "h2": 0, "yield": 11200},
    {"point": "D", "ch4": 100, "h2": 50, "yield": 8000},
    {"point": "E", "ch4": 150, "h2": 0, "yield": 20500},
    {"point": "F", "ch4": 200, "h2": 0, "yield": 9500},
    {"point": "G", "ch4": 300, "h2": 0, "yield": 16500},
]


def add_pdf_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    suffix: str,
    table: str,
    record_id: str,
    fields: str,
    span_id: str,
    page: int,
    text: str,
    summary: str,
    *,
    object_ref: str = PDF_REF,
    value_status: str = "reported",
    confidence: str = "high",
) -> None:
    item = evidence_row(
        store,
        SOURCE_ID,
        f"EVD_{run_id}_{suffix}",
        run_id,
        table,
        record_id,
        fields,
        span_id,
        summary,
        confidence=confidence,
        value_status=value_status,
    )
    item.update(
        {
            "evidence_type": "pdf_visual_transcription",
            "source_section": f"PDF page {page}",
            "source_locator": f"PDF page {page}",
            "source_object_ref": object_ref,
            "evidence_text": text,
            "evidence_summary": summary,
            "notes": (
                "Transcribed from the locally stored article PDF or its "
                "primary PMC figure asset."
            ),
        }
    )
    tables["evidence_index"].append(item)


def catalyst(run_id: str, series: str) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label=(
            f"{series} Co-polymolybdate/MgO catalyst; numbered identity "
            "is contradictory in the article"
        ),
        active_metals="Co; Mo",
        support_material="MgO",
        promoter="not_reported",
        metal_ratio_original="not_reported",
        metal_ratio_standardized="not_reported",
        precursor_summary=(
            "cobalt polymolybdate plus MgO; exact assignment of deposition "
            "versus combustion route to this figure series is unresolved"
        ),
        preparation_method="identity_unresolved_deposition_or_combustion",
        preparation_modifier=(
            "article alternately assigns catalyst 1 and catalyst 2 to the "
            "deposition and combustion routes"
        ),
        preparation_detail=CATALYST_SYNTHESIS,
        drying_condition=(
            "deposition route: evaporated at 60 C; combustion-route drying "
            "not separately reported"
        ),
        calcination_condition="combustion route: thermal shock at 540 C",
        reduction_condition="150 mL/min H2 at 1000 C for 10 min before growth",
        activation_condition=(
            "reported for deposited Co-polymolybdate/MgO: 700 C for 11 min, "
            "then cool to room temperature"
        ),
        post_preparation_condition=(
            "powder evenly distributed on a ceramic boat before CCVD"
        ),
        catalyst_particle_size_mean_nm="",
        catalyst_particle_size_range_nm="not_reported",
        catalyst_particle_size_qualifier=(
            "average size reported for MoO3/CoMoO4 particles formed by "
            "decomposition of deposited Co-polymolybdate/MgO"
        ),
        phase_or_state_summary=(
            "activation reported to form MoO3 and CoMoO4; subsequent H2 "
            "treatment described as reduction to metallic particles"
        ),
        dispersion_summary="Co-polymolybdate distributed on MgO support",
        deactivation_summary="not_reported",
        notes=(
            "Catalyst numbering and route assignment require human resolution; "
            "the figure-series identity is preserved without forced remapping."
        ),
    )


def process_stages(run_id: str, ch4: int, h2: int) -> list[dict[str, str]]:
    return [
        process_row(
            run_id,
            1,
            "catalyst_thermal_activation",
            reactor_type="muffle furnace",
            scale_level="lab_batch",
            reactor_material="not_reported",
            reactor_size_summary="not_reported",
            reactor_setup_summary=(
                "Co-polymolybdate/MgO powder thermally decomposed before CCVD"
            ),
            catalyst_loading_mass_g="not_reported",
            temperature_setpoint_C="700",
            temperature_program_summary="hold 11 min, then cool to room temperature",
            holding_time_min="11",
            heating_rate_C_min="not_reported",
            cooling_condition="cooled to room temperature",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source="none",
            reducing_gas="none",
            inert_gas="not_reported",
            gas_composition_summary="atmosphere not reported",
            process_note=(
                "Reported to form MoO3 and CoMoO4 particles averaging 5 nm; "
                "explicitly described for deposited Co-polymolybdate/MgO."
            ),
        ),
        process_row(
            run_id,
            2,
            "hydrogen_reduction",
            reactor_type="horizontal tubular CCVD reactor",
            scale_level="lab_batch",
            reactor_material="30 mm diameter, 1 m long removable quartz tube",
            reactor_size_summary="30 mm diameter x 1 m",
            reactor_setup_summary=REACTOR_RECIPE,
            catalyst_loading_mass_g="not_reported",
            temperature_setpoint_C="1000",
            temperature_program_summary="constant-temperature hot zone",
            holding_time_min="10",
            heating_rate_C_min="not_reported",
            cooling_condition="not_applicable_before_growth",
            pressure_original="evacuated, then filled with H2; growth pressure not reported",
            pressure_kPa="",
            carbon_source="none",
            reducing_gas="H2",
            reducing_gas_flow_original="150 mL/min",
            reducing_gas_flow_sccm="150",
            inert_gas="none",
            total_flow_original="150 mL/min",
            total_flow_sccm="150",
            gas_composition_summary="100% H2",
            process_note="Catalyst boat moved into the 1000 C hot zone for reduction.",
        ),
        process_row(
            run_id,
            3,
            "ccvd_growth",
            reactor_type="horizontal tubular CCVD reactor",
            scale_level="lab_batch",
            reactor_material="30 mm diameter, 1 m long removable quartz tube",
            reactor_size_summary="30 mm diameter x 1 m",
            reactor_setup_summary=REACTOR_RECIPE,
            catalyst_loading_mass_g="not_reported",
            temperature_setpoint_C="1000",
            temperature_program_summary="constant-temperature profile",
            holding_time_min="30",
            heating_rate_C_min="not_reported",
            cooling_condition="not_reported",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source="CH4",
            carbon_source_flow_original=f"{ch4} mL/min",
            carbon_source_flow_sccm=str(ch4),
            reducing_gas="H2" if h2 else "none",
            reducing_gas_flow_original=f"{h2} mL/min" if h2 else "0 mL/min",
            reducing_gas_flow_sccm=str(h2),
            inert_gas="none",
            total_flow_original=f"{ch4 + h2} mL/min",
            total_flow_sccm=str(ch4 + h2),
            gas_composition_summary=f"CH4/H2 = {ch4}/{h2} mL/min",
            process_note=(
                "Black carbon outgrowth formed on the ceramic boat; flow "
                "condition is read from the corresponding published figure."
            ),
        ),
        process_row(
            run_id,
            4,
            "post_growth_hydrogen_purge",
            reactor_type="horizontal tubular CCVD reactor",
            scale_level="lab_batch",
            reactor_material="quartz tube",
            reactor_size_summary="30 mm diameter x 1 m",
            reactor_setup_summary=REACTOR_RECIPE,
            temperature_setpoint_C="1000",
            temperature_program_summary="final purge after growth",
            holding_time_min="10",
            heating_rate_C_min="not_applicable",
            cooling_condition="not_reported after purge",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source="none",
            reducing_gas="H2",
            reducing_gas_flow_original="150 mL/min",
            reducing_gas_flow_sccm="150",
            inert_gas="none",
            total_flow_original="150 mL/min",
            total_flow_sccm="150",
            gas_composition_summary="100% H2",
            process_note="Final H2 purge reported for every synthesis.",
        ),
        process_row(
            run_id,
            5,
            "acid_purification",
            reactor_type="bench liquid-treatment vessel",
            scale_level="lab_batch_post_treatment",
            reactor_material="not_reported",
            reactor_size_summary="not_reported",
            reactor_setup_summary=PURIFICATION_RECIPE,
            temperature_setpoint_C="not_reported",
            temperature_program_summary="stirred at unreported temperature",
            holding_time_min="240-360",
            heating_rate_C_min="not_applicable",
            cooling_condition="not_applicable",
            pressure_original="atmospheric",
            pressure_kPa="101.325",
            carbon_source="none",
            reducing_gas="none",
            inert_gas="none",
            cofeed_or_reactive_gas="concentrated HCl",
            cofeed_flow_original="not_reported",
            gas_composition_summary="not_applicable_liquid_treatment",
            process_note=(
                "Concentrated-HCl stirring removed catalyst particles and MgO; "
                "product was then filtered and repeatedly water-washed."
            ),
        ),
        process_row(
            run_id,
            6,
            "product_drying",
            reactor_type="desiccator or drying vessel",
            scale_level="lab_batch_post_treatment",
            reactor_material="not_reported",
            reactor_size_summary="not_reported",
            reactor_setup_summary=PURIFICATION_RECIPE,
            temperature_setpoint_C="100",
            temperature_program_summary="dry at 100 C",
            holding_time_min="360-720",
            heating_rate_C_min="not_reported",
            cooling_condition="not_reported",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source="none",
            reducing_gas="none",
            inert_gas="not_reported",
            gas_composition_summary="drying atmosphere not reported",
            process_note="Purified CNT product dried for 6-12 h.",
        ),
    ]


def product(
    run_id: str,
    series: str,
    point: str,
    ch4: int,
    h2: int,
    yield_value: int,
) -> dict[str, str]:
    raman = ""
    morphology = "not individually reported"
    diameter_mean = ""
    diameter_range = ""
    wall_summary = ""
    cnt_type = "CNT mixture"
    swcnt_evidence = ""
    rbm = ""
    amorphous = "not individually reported"
    application = ""
    secondary = (
        f"{series} point {point}; approximate figure yield {yield_value} wt.%; "
        f"CH4/H2 {ch4}/{h2} mL/min."
    )

    if series == "FIG4":
        cnt_type = "DWCNT and MWCNT mixture at the characterized 200/0 condition"
        if ch4 == 200 and h2 == 0:
            raman = "0.5"
            morphology = "balls and bundles of DWCNTs with individual MWCNTs"
            diameter_mean = "5"
            diameter_range = "2-5"
            wall_summary = "bilayer CNT bundles plus individual multiwall CNTs"
            amorphous = "reported absent in the characterized sample"
        elif ch4 == 300 and h2 == 0:
            raman = "1.6"
            morphology = "thick and defective CNTs"
            wall_summary = "increased thick multiwall fraction"
        secondary += (
            " Text reports the 200 mL/min CH4 condition as low-defect and "
            "the 300 mL/min condition as the highest-defect condition."
        )
    else:
        cnt_type = "SWCNT, DWCNT, triple-wall CNT and MWCNT mixture"
        swcnt_evidence = (
            "RBM peaks were observed for all Figure 6 spectra, interpreted "
            "as single- and double-wall CNT formation."
        )
        rbm = "present in all Figure 6 samples; positions not tabulated"
        if ch4 == 50 and h2 == 50:
            raman = "0.2"
        elif ch4 == 150 and h2 == 0:
            raman = "0.5"
            application = (
                "Reported as the highest specific-capacitance sample over "
                "the tested potential-sweep-rate range."
            )
        elif ch4 == 300 and h2 == 0:
            raman = "0.8"
            wall_summary = (
                "highest defect ratio in the 0.2-0.8 series; fewer bilayer "
                "CNTs and more large-diameter MWCNTs"
            )
        if ch4 == 200 and h2 == 0:
            morphology = (
                "highly dispersed thin CNTs including DWCNT, triple-wall CNT and MWCNT"
            )
            diameter_mean = "3;5;7"
            diameter_range = "up to 14"
            wall_summary = (
                "average outer diameters reported as 3, 5 and 7 nm for "
                "double-, triple- and multiwall populations; MWCNT up to 14 nm"
            )
        secondary += " Figure 6 text reports ID/IG values spanning 0.2-0.8."

    return yield_row(
        run_id,
        primary_yield_metric="CNT_yield_wt_percent_from_figure",
        yield_original=f"approximately {yield_value} wt.% (visual digitization)",
        yield_definition_original=(
            "Figure y-axis: Yield of carbon nanotubes, wt.%; denominator and "
            "calculation basis are not defined"
        ),
        yield_calculation_method="visual_digitization_of_published_line_graph",
        yield_value_standardized="",
        yield_unit_standardized="",
        yield_standardization_note=(
            "No conversion to g/g catalyst because the wt.% denominator and "
            "catalyst charge are not reported."
        ),
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=secondary,
        CNT_type_reported=cnt_type,
        CNT_type_confirmed="mixed-wall CNT product supported by TEM and Raman",
        product_mixture_summary=(
            "purified CNT mixture; exact wall-number distribution was only "
            "characterized for selected conditions"
        ),
        CNT_type_evidence="TEM; Raman D/G bands; RBM where reported",
        SWCNT_or_few_wall_evidence_summary=swcnt_evidence,
        RBM_peak_reported=rbm,
        outer_diameter_mean_nm=diameter_mean,
        outer_diameter_range_nm=diameter_range,
        inner_diameter_mean_nm="not_reported",
        wall_number_summary=wall_summary,
        length_summary="not_reported",
        morphology=morphology,
        alignment_or_array="not_reported",
        Raman_ratio_type="ID/IG",
        Raman_ratio_value=raman,
        Raman_laser_wavelength_nm="not_reported",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis="not_reported",
        residue_summary="catalyst and MgO removed by concentrated-HCl treatment",
        amorphous_carbon_level=amorphous,
        BET_surface_area_product_m2_g="",
        characterization_methods="TEM; Raman spectroscopy; gravimetric yield",
        post_treatment_or_purification="concentrated-HCl purification and water wash",
        purification_condition=PURIFICATION_RECIPE,
        application_property_summary=application,
        notes=(
            "Yield is approximate visual transcription. Catalyst numbering, "
            "series identity and selected-condition morphology require review."
        ),
    )


def cost(run_id: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="lab_batch",
        scale_level_claimed="not_reported",
        scale_evidence_summary=(
            "A 30 mm diameter, 1 m quartz-tube CCVD reactor was operated for "
            "30 min growth at 1000 C."
        ),
        reactor_capacity_or_throughput="not_reported",
        continuous_operation_time_h="not_reported",
        catalyst_lifetime_or_reuse="not_reported",
        catalyst_reuse_cycles="not_reported",
        batch_stability="single plotted values; replicate statistics not reported",
        scale_up_issue=(
            "Resolve catalyst identity and yield basis; quantify catalyst "
            "charge, methane conversion, productivity, gas utilization, acid "
            "consumption and reproducibility."
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="No monetary or normalized production-cost data.",
        cost_driver_summary=(
            "1000 C furnace duty, H2/CH4 gas, Co/Mo precursors, MgO, "
            "concentrated HCl, water washing and long drying"
        ),
        safety_risk=(
            "flammable H2/CH4 at 1000 C; Co/Mo compounds; hydrazine sulfate; "
            "concentrated HCl; high-temperature combustion preparation"
        ),
        emission_or_waste=(
            "unquantified CCVD exhaust plus Co/Mo/Mg-containing acidic wash waste"
        ),
        industrial_readiness_assessment=(
            "laboratory condition screen only; missing defined yield basis, "
            "conversion, throughput and catalyst-life data"
        ),
        reproduction_value="medium",
        reproduction_priority="high",
        recommended_next_action=(
            "Repeat the full CH4/H2 matrix with unambiguous catalyst labels, "
            "mass balances, replicate error bars and normalized productivity."
        ),
        review_note="Industrial review is provisional because reported yield basis is unclear.",
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
                "Two Co-polymolybdate/MgO catalyst-series condition screens; "
                "18 CH4/H2 growth conditions; catalyst preparation, activation, "
                "CCVD, purification, Raman/TEM/yield and selected electrode results."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_fulltext_pdf"
    master["notes"] += (
        f" Primary PMC XML retained at {PMC_XML_REF}. Figure-series labels "
        "are used because catalyst numbering is internally contradictory."
    )

    runs: list[tuple[str, dict[str, int | str]]] = [
        ("FIG4", item) for item in FIG4_SERIES
    ] + [("FIG6", item) for item in FIG6_SERIES]

    first_ids: dict[str, str] = {}
    for series, item in runs:
        ch4 = int(item["ch4"])
        h2 = int(item["h2"])
        point = str(item["point"])
        yield_value = int(item["yield"])
        code = f"{series}_{point}_CH4_{ch4}_H2_{h2}"
        run_id = f"{SOURCE_ID}_{code}"
        first_ids.setdefault(series, run_id)
        summary = (
            f"{series} point {point}: Co-polymolybdate/MgO CCVD at 1000 C "
            f"for 30 min with CH4/H2 {ch4}/{h2} mL/min; approximate CNT "
            f"yield {yield_value} wt.%."
        )
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                code,
                f"{series} point {point}, CH4/H2 {ch4}/{h2} mL/min",
                summary,
                "medium",
            )
        )
        tables["catalyst_system"].append(catalyst(run_id, series))
        tables["reactor_process_gas"].extend(process_stages(run_id, ch4, h2))
        tables["yield_quality"].append(
            product(run_id, series, point, ch4, h2, yield_value)
        )
        tables["cost_scale_review"].append(cost(run_id))

        figure_ref = FIG4_REF if series == "FIG4" else FIG6_REF
        figure_page = 9 if series == "FIG4" else 11
        figure_span = (
            "SPAN_2AB62835D1A6A9A21E6F"
            if series == "FIG4"
            else "SPAN_4CA307F0BC64276C7141"
        )
        result_span = (
            "SPAN_A010E3B0A2B3654B45C8"
            if series == "FIG4"
            else "SPAN_948740E81F656D8CA49F"
        )

        add_pdf_evidence(
            tables,
            store,
            run_id,
            "RUN",
            "source_run",
            run_id,
            "record_level",
            figure_span,
            figure_page,
            (
                f"Published {series} graph point {point}: CH4/H2 "
                f"{ch4}/{h2} mL/min; visually digitized CNT yield "
                f"approximately {yield_value} wt.%."
            ),
            "Condition identity and graph-derived yield.",
            object_ref=figure_ref,
            value_status="visually_digitized",
            confidence="medium",
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "CATALYST",
            "catalyst_system",
            f"{run_id}_CAT",
            "record_level",
            "SPAN_377009B102AC4899DE83",
            6,
            CATALYST_SYNTHESIS,
            "Catalyst precursor preparation and the two reported preparation routes.",
        )

        process_evidence = [
            (
                1,
                "SPAN_6DF45AEC558EE1BF02BB",
                7,
                "Thermal activation at 700 C for 11 min and 5 nm MoO3/CoMoO4.",
            ),
            (
                2,
                "SPAN_80ECE84F2D136A0DFEF6",
                8,
                REACTOR_RECIPE,
            ),
            (
                3,
                figure_span,
                figure_page,
                (
                    f"{REACTOR_RECIPE} This record used CH4/H2 {ch4}/{h2} "
                    f"mL/min, total flow {ch4 + h2} mL/min."
                ),
            ),
            (
                4,
                "SPAN_EC5B6255BAC1C9DF54E7",
                8,
                "Final 150 mL/min H2 purge at 1000 C for 10 min.",
            ),
            (
                5,
                "SPAN_EC5B6255BAC1C9DF54E7",
                8,
                PURIFICATION_RECIPE
                + " The 4-6 h acid treatment corresponds to 240-360 min.",
            ),
            (
                6,
                "SPAN_EC5B6255BAC1C9DF54E7",
                8,
                PURIFICATION_RECIPE,
            ),
        ]
        for stage, span, page, text in process_evidence:
            add_pdf_evidence(
                tables,
                store,
                run_id,
                f"PROCESS_{stage}",
                "reactor_process_gas",
                f"{run_id}_S{stage:02d}",
                "record_level",
                span,
                page,
                text,
                f"Process stage {stage} support.",
            )

        product_text = (
            f"{series} point {point}, CH4/H2 {ch4}/{h2} mL/min: "
            f"approximate CNT yield {yield_value} wt.% from the published "
            "graph. "
        )
        if series == "FIG4":
            product_text += (
                "The text reports ID/IG 0.5 at 200 mL/min CH4 and 1.6 at "
                "300 mL/min CH4."
            )
            if ch4 == 200 and h2 == 0:
                product_text += (
                    " TEM reports DWCNT outer diameters 2-5 nm and individual "
                    "MWCNTs with average diameter 5 nm."
                )
        else:
            product_text += (
                "The text reports ID/IG spanning 0.2-0.8, with 0.2 at "
                "50/50, 0.5 at 150/0 and the maximum at 300/0."
            )
            if ch4 == 200 and h2 == 0:
                product_text += (
                    " TEM reports double-, triple- and multiwall populations "
                    "with average outer diameters 3, 5 and 7 nm, plus MWCNTs "
                    "up to 14 nm."
                )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "PRODUCT",
            "yield_quality",
            f"{run_id}_PROD",
            "record_level",
            result_span,
            figure_page,
            product_text,
            "Graph yield, Raman trend and selected morphology.",
            object_ref=figure_ref,
            value_status="mixed_reported_and_visually_digitized",
            confidence="medium",
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            "record_level",
            "SPAN_80ECE84F2D136A0DFEF6",
            8,
            REACTOR_RECIPE + " " + PURIFICATION_RECIPE,
            "Process-intensity facts and industrial data gaps.",
            value_status="review_assessment",
        )

    fig4_id = first_ids["FIG4"]
    fig6_id = first_ids["FIG6"]
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_CATALYST_NUMBERING_001",
                SOURCE_ID,
                fig4_id,
                "source_contradiction",
                "catalyst_system",
                f"{fig4_id}_CAT",
                "preparation_method",
                (
                    "The objectives/conclusions assign deposition to catalyst 1 "
                    "and combustion to catalyst 2; Materials and Methods reverses "
                    "that assignment, while the thermal-shock paragraph itself "
                    "calls the combustion powder catalyst 1."
                ),
                f"EVD_{fig4_id}_CATALYST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SERIES_IDENTITY_001",
                SOURCE_ID,
                fig6_id,
                "source_contradiction",
                "source_run",
                fig6_id,
                "run_label",
                (
                    "Figures 3-6 and their surrounding text repeatedly label "
                    "both distinct result series as catalyst 1 or catalyst 2. "
                    "Records therefore preserve Figure 4/Figure 6 series identity."
                ),
                f"EVD_{fig4_id}_RUN;EVD_{fig6_id}_RUN",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FIG4_CONDITIONS_001",
                SOURCE_ID,
                fig4_id,
                "caption_graph_mismatch",
                "source_run",
                fig4_id,
                "run_summary",
                (
                    "Figure 4 caption enumerates six Raman spectra, but the yield "
                    "graph has eleven A-K positions and additional CH4/H2 ticks. "
                    "All eleven graph positions are retained; H and J are unlabeled "
                    "intermediate points read from explicit x-axis ticks."
                ),
                f"EVD_{fig4_id}_RUN",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_DIGITIZATION_001",
                SOURCE_ID,
                fig4_id,
                "figure_digitization",
                "yield_quality",
                f"{fig4_id}_PROD",
                "yield_original",
                (
                    "All CNT-yield values are approximate visual readings from "
                    "line graphs without error bars or underlying numeric tables."
                ),
                f"EVD_{fig4_id}_PRODUCT;EVD_{fig6_id}_PRODUCT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_BASIS_001",
                SOURCE_ID,
                fig6_id,
                "critical_data_gap",
                "yield_quality",
                f"{fig6_id}_PROD",
                "yield_definition_original",
                (
                    "The figure axis is labeled yield of carbon nanotubes, wt.%, "
                    "but the denominator and calculation are not defined. Values "
                    "exceed 100%, so no conversion to g/g catalyst was performed."
                ),
                f"EVD_{fig6_id}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_MORPHOLOGY_IDENTITY_001",
                SOURCE_ID,
                fig4_id,
                "source_contradiction",
                "yield_quality",
                f"{fig4_id}_PROD",
                "morphology",
                (
                    "Figure 3 caption assigns the 200 mL/min sample to catalyst 1 "
                    "while the adjacent text assigns it to catalyst 2; Figure 5 "
                    "and its narrative also conflict. Morphology is attached to "
                    "the adjacent figure series, not a resolved catalyst route."
                ),
                f"EVD_{fig4_id}_PRODUCT;EVD_{fig6_id}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_APPLICATION_IDENTITY_001",
                SOURCE_ID,
                fig6_id,
                "source_contradiction",
                "yield_quality",
                f"{fig6_id}_PROD",
                "application_property_summary",
                (
                    "The electrochemical comparison sentence states catalyst 1 "
                    "twice while reporting surface areas of 379 and 285 m2/g; "
                    "the higher-capacitance route cannot be assigned safely."
                ),
                f"EVD_{fig6_id}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_LOADING_PRESSURE_001",
                SOURCE_ID,
                fig4_id,
                "critical_data_gap",
                "reactor_process_gas",
                f"{fig4_id}_S03",
                "catalyst_loading_mass_g",
                (
                    "Catalyst charge/loading and actual growth pressure are not "
                    "reported, preventing normalized productivity or residence-time "
                    "calculation."
                ),
                f"EVD_{fig4_id}_PROCESS_2;EVD_{fig4_id}_PROCESS_3",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_REPLICATES_001",
                SOURCE_ID,
                fig6_id,
                "critical_data_gap",
                "cost_scale_review",
                fig6_id,
                "batch_stability",
                "No replicate count, uncertainty or run-to-run variability is reported.",
                f"EVD_{fig6_id}_COST",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SCOPE_001",
                SOURCE_ID,
                fig6_id,
                "scope_boundary",
                "source_run",
                fig6_id,
                "run_summary",
                (
                    "The paper also reports porous-carbon synthesis, hybrid "
                    "mixing and battery/supercapacitor testing. Those non-CNT "
                    "production branches are outside the CNT_production target "
                    "track; selected application findings are retained only as "
                    "product-property summaries."
                ),
                f"EVD_{fig6_id}_PRODUCT",
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
