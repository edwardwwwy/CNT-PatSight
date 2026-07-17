#!/usr/bin/env python3
"""Build the twenty-eighth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 28
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_F9ED79E1CCABED15"
PDF_REF = "data/raw/fulltext/pdf/LIT_F9ED79E1CCABED15_38282a4fbd1e.pdf"

METHOD_SPAN = "SPAN_D2744CCF7CD22B58395F"
GC_SPAN = "SPAN_D13537E889A047A7D617"
PRETREAT_SPAN = "SPAN_E290136541A00A7F368C"
YIELD_SPAN = "SPAN_CF9F869B1ED5C184203F"
QUALITY_SPAN = "SPAN_4DD35BCF39E5083AB0F1"
DIAMETER_SPAN = "SPAN_47911D38B77BB479EB89"

GC_CONTROLS = [
    {
        "code": "GC_FERROCENE_300C",
        "temperature": 300,
        "ch4": 1.12,
        "h2": 3.30,
        "summary": (
            "Preliminary GC-TCD ferrocene-decomposition test at 300 C: "
            "CH4 1.12 wt% and H2 3.30 wt%; unknown chromatogram components "
            "were attributed to cyclopentadiene and other impurities."
        ),
    },
    {
        "code": "GC_FERROCENE_400C",
        "temperature": 400,
        "ch4": 2.39,
        "h2": 10.26,
        "summary": (
            "Preliminary GC-TCD ferrocene-decomposition test at 400 C: "
            "CH4 2.39 wt% and H2 10.26 wt%. A 0-30 min GC series reported "
            "CH4 values 7.6, 13.6, 8.7, 19.9, 14.3, 8.3 and 7.2 and H2 "
            "values 1.1, 3.5, 4.1, 6.8, 5.7, 2.7 and 3.8 at 0, 5, 10, "
            "15, 20, 25 and 30 min; both decreased after 20 min."
        ),
    },
]

SYNTHESIS_RUNS = [
    {
        "code": "VAP300_OXIDIZED",
        "vaporizer": 300,
        "treated": True,
        "mass": 0.97,
        "yield": 24.25,
    },
    {
        "code": "VAP300_UNTREATED",
        "vaporizer": 300,
        "treated": False,
        "mass": 0.68,
        "yield": 17.02,
    },
    {
        "code": "VAP400_OXIDIZED",
        "vaporizer": 400,
        "treated": True,
        "mass": 2.15,
        "yield": 53.69,
    },
    {
        "code": "VAP400_UNTREATED",
        "vaporizer": 400,
        "treated": False,
        "mass": 0.84,
        "yield": 21.00,
    },
]


def catalyst(run_id: str, treated: bool | None) -> dict[str, str]:
    if treated is None:
        treatment = (
            "GC-TCD decomposition calibration; substrate treatment not applicable"
        )
    elif treated:
        treatment = (
            "316 stainless steel oxidatively heat-treated in air for 20 min; "
            "treatment temperature not reported"
        )
    else:
        treatment = "316 stainless steel used without oxidative heat treatment"
    return catalyst_row(
        run_id,
        catalyst_label="ferrocene-derived Fe plus Fe-bearing stainless steel 316 substrate",
        active_metals="Fe from ferrocene and stainless steel 316",
        support_material="horizontal stainless steel type 316 structured gauze substrate",
        promoter="surface oxygen/radical-O after oxidative treatment"
        if treated
        else "none",
        metal_ratio_original="reported overall Fe/C ratio 0.469 for the study",
        metal_ratio_standardized="Fe/C = 0.469 reported study-level ratio",
        precursor_summary="4 g ferrocene, Fe(C5H5)2, serving as carbon source and catalyst",
        preparation_method="ferrocene vaporization with optional oxidative substrate activation",
        preparation_modifier=treatment,
        preparation_detail=(
            "Horizontal SS316 substrate contact area 37.68 cm2 in the effective "
            "zone of reactor 2. Oxidation removes/passivates the Cr2O3 layer "
            "and exposes Fe-containing catalytic surface according to the authors."
        ),
        drying_condition="not_applicable",
        calcination_condition=(
            "oxidative heat treatment in air for 20 min; temperature not reported"
            if treated
            else "not_applicable"
        ),
        reduction_condition="not_reported",
        activation_condition=treatment,
        post_preparation_condition="placed horizontally in reactor 2 at 850 C",
        catalyst_particle_size_mean_nm="",
        catalyst_particle_size_range_nm="",
        catalyst_particle_size_qualifier=(
            "No catalyst-particle distribution; Fe3C cores and agglomerated Fe "
            "particles were associated with carbon onions and broad CNT diameters."
        ),
        phase_or_state_summary="Fe, Fe3C, Fe3O4 and Fe2O3 detected in/with CNT product",
        dispersion_summary="qualitative; oxidative treatment increased reactive surface",
        deactivation_summary="catalyst saturation/shooting discussed as a termination mechanism",
    )


def gc_process(run_id: str, temperature: int) -> list[dict[str, str]]:
    return [
        process_row(
            run_id,
            1,
            "ferrocene_decomposition_gc_calibration",
            reactor_type="vertical structured gauze reactor with double furnace",
            scale_level="lab_preliminary_calibration",
            reactor_material="quartz tube",
            reactor_size_summary="reported total height 737 cm and diameter 3 cm",
            reactor_setup_summary="furnace 1 vaporizer; furnace 2 substrate zone; cyclone; GC-TCD outlet",
            catalyst_loading_mass_g="4",
            temperature_setpoint_C=str(temperature),
            temperature_range_reported_C=str(temperature),
            temperature_program_summary=f"ferrocene vaporizer furnace at {temperature} C",
            holding_time_min="0-30 GC sampling series; production duration selected as 20",
            heating_rate_C_min="not_reported",
            cooling_condition="not_reported for GC calibration",
            pressure_original="atmospheric",
            pressure_kPa="101.325",
            carbon_source="ferrocene",
            carbon_source_flow_original="4 g batch charge",
            reducing_gas="H2 generated in situ",
            reducing_gas_flow_original="not controlled externally",
            inert_gas="Ar",
            inert_gas_flow_original="150 cm3/min",
            cofeed_or_reactive_gas="none",
            cofeed_flow_original="not_applicable",
            total_flow_original="150 cm3/min Ar plus ferrocene decomposition products",
            gas_composition_summary="Fe, CH4, H2, cyclopentadiene and unidentified impurities",
            process_note="GC-TCD used to select vaporizer temperature and 20 min duration.",
        )
    ]


def synthesis_process(
    run_id: str, vaporizer: int, treated: bool
) -> list[dict[str, str]]:
    stages: list[dict[str, str]] = []
    if treated:
        stages.append(
            process_row(
                run_id,
                1,
                "oxidative_substrate_activation",
                reactor_type="oxidative heat-treatment apparatus; not reported",
                scale_level="lab_substrate_pretreatment",
                reactor_material="not_reported",
                reactor_size_summary="horizontal SS316 substrate area 37.68 cm2",
                reactor_setup_summary="stainless steel type 316 exposed to air",
                catalyst_loading_mass_g="not_applicable",
                temperature_setpoint_C="not_reported",
                temperature_program_summary="oxidative heat treatment for 20 min",
                holding_time_min="20",
                heating_rate_C_min="not_reported",
                cooling_condition="not_reported",
                pressure_original="atmospheric",
                pressure_kPa="101.325",
                carbon_source="none",
                reducing_gas="none",
                inert_gas="none",
                cofeed_or_reactive_gas="air/O2",
                cofeed_flow_original="not_reported",
                total_flow_original="not_reported",
                gas_composition_summary="oxidative atmosphere; air mentioned",
                process_note=(
                    "Treatment intended to remove Cr2O3/passivation and produce "
                    "an approximately 35 nm optimum roughness cited from prior work."
                ),
            )
        )
    order = len(stages) + 1
    stages.append(
        process_row(
            run_id,
            order,
            "dual_furnace_floating_catalyst_cvd",
            reactor_type="vertical structured gauze reactor with double furnace",
            scale_level="lab_batch_structured_substrate",
            reactor_material="quartz tube",
            reactor_size_summary="reported total height 737 cm and diameter 3 cm",
            reactor_setup_summary=(
                "furnace 1 ferrocene vaporizer; furnace 2 horizontal SS316 "
                "substrate zone; downstream cyclone"
            ),
            catalyst_loading_mass_g="4",
            temperature_setpoint_C="850",
            temperature_range_reported_C=f"vaporizer {vaporizer}; substrate 850",
            temperature_program_summary=(
                f"furnace 1 at {vaporizer} C and furnace 2 at 850 C for 20 min"
            ),
            holding_time_min="20",
            heating_rate_C_min="not_reported",
            cooling_condition="not_reported",
            pressure_original="atmospheric",
            pressure_kPa="101.325",
            carbon_source="ferrocene and its hydrocarbon decomposition products",
            carbon_source_flow_original="4 g ferrocene batch charge",
            reducing_gas="H2 generated by ferrocene decomposition",
            reducing_gas_flow_original="not externally metered",
            inert_gas="Ar",
            inert_gas_flow_original="150 cm3/min",
            cofeed_or_reactive_gas="none",
            cofeed_flow_original="not_applicable",
            total_flow_original="150 cm3/min Ar plus vaporized/decomposed ferrocene",
            gas_composition_summary=(
                f"Ar carrier; furnace-1 decomposition at {vaporizer} C produces "
                "Fe, CH4, H2 and cyclopentadiene"
            ),
            process_note="Horizontal substrate contact area 37.68 cm2.",
        )
    )
    return stages


def gc_product(run_id: str, item: dict[str, Any]) -> dict[str, str]:
    return yield_row(
        run_id,
        primary_yield_metric="GC_TCD_decomposition_gas_composition",
        yield_original=f"CH4 {item['ch4']} wt%; H2 {item['h2']} wt%",
        yield_definition_original=item["summary"],
        yield_calculation_method="GC-TCD outlet-gas analysis",
        yield_value_standardized="",
        yield_unit_standardized="",
        yield_standardization_note="Preliminary gas calibration, not a CNT-yield experiment.",
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=item["summary"],
        CNT_type_reported="not_applicable calibration",
        CNT_type_confirmed="not_applicable",
        product_mixture_summary="gas-phase ferrocene decomposition products",
        CNT_type_evidence="not_applicable",
        SWCNT_or_few_wall_evidence_summary="not_applicable",
        RBM_peak_reported="not_applicable",
        outer_diameter_mean_nm="",
        outer_diameter_range_nm="",
        inner_diameter_mean_nm="",
        wall_number_summary="not_applicable",
        length_summary="not_applicable",
        morphology="not_applicable",
        alignment_or_array="not_applicable",
        Raman_ratio_type="not_applicable",
        Raman_ratio_value="",
        Raman_laser_wavelength_nm="",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis="not_applicable",
        residue_summary="unidentified GC peaks",
        amorphous_carbon_level="not_applicable",
        BET_surface_area_product_m2_g="",
        characterization_methods="GC-TCD",
        post_treatment_or_purification="none",
        purification_condition="not_applicable",
        application_property_summary="selected 400 C vaporizer and 20 min production duration",
        notes="Mechanistic/preliminary calibration retained separately from CNT runs.",
    )


def synthesis_summary(item: dict[str, Any]) -> str:
    treated = item["treated"]
    sem_range = "76-122.7 nm" if treated else "94.6-110.5 nm"
    xrd_size = "9.64 nm" if treated else "12.63 nm"
    edx = "C/O/Fe = 73.7/8.17/16.48 wt%" if treated else "C/O/Fe = 59.96/4.03/34.57 wt%"
    return (
        f"Horizontal SS316, ferrocene vaporizer {item['vaporizer']} C, "
        f"{'with' if treated else 'without'} 20 min oxidative treatment: "
        f"CNT mass {item['mass']} g from 4 g ferrocene and reported yield "
        f"{item['yield']}%. Treatment-level SEM apparent tube-width range "
        f"{sem_range}; XRD Scherrer mean crystallite/particle size {xrd_size}; "
        f"EDX {edx}. Product was low-quality MWCNT mixed with amorphous "
        "carbon, hexagonal graphite, Fe3C, Fe3O4 and Fe2O3."
    )


def synthesis_product(run_id: str, item: dict[str, Any]) -> dict[str, str]:
    treated = item["treated"]
    summary = synthesis_summary(item)
    return yield_row(
        run_id,
        primary_yield_metric="CNT_mass_per_ferrocene_charge_percent",
        yield_original=f"{item['mass']} g CNT; {item['yield']}%",
        yield_definition_original="collected CNT mass divided by 4 g ferrocene charge x 100%",
        yield_calculation_method=f"{item['mass']} g / 4 g x 100%",
        yield_value_standardized=str(item["yield"]),
        yield_unit_standardized="%",
        yield_standardization_note=(
            "This is product mass relative to total ferrocene charge, not carbon-"
            "atom conversion and not yield per catalyst mass."
        ),
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=summary,
        CNT_type_reported="CNT",
        CNT_type_confirmed="low-quality MWCNT",
        product_mixture_summary=(
            "MWCNT, abundant amorphous carbon, hexagonal graphite, carbon "
            "onions, Fe3C, Fe3O4 and Fe2O3"
        ),
        CNT_type_evidence="SEM and XRD peaks at 26 and 43 degrees",
        SWCNT_or_few_wall_evidence_summary="XRD peak at 43 degrees assigned to MWCNT",
        RBM_peak_reported="not_reported",
        outer_diameter_mean_nm="",
        outer_diameter_range_nm=(
            "SEM apparent width 76-122.7"
            if treated
            else "SEM apparent width 94.6-110.5"
        ),
        inner_diameter_mean_nm="",
        wall_number_summary="multi-walled; exact wall count not reported",
        length_summary="not_quantified",
        morphology="buckled, curved, tangled/agglomerated tubes; carbon onions",
        alignment_or_array="non-aligned tangled CNT",
        Raman_ratio_type="not_reported",
        Raman_ratio_value="",
        Raman_laser_wavelength_nm="",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis="unpurified product; XRD/SEM/EDX",
        residue_summary="Fe3C, Fe3O4, Fe2O3 and hexagonal graphite",
        amorphous_carbon_level=(
            "lower than untreated by XRD/SEM, but still high"
            if treated
            else "highest amorphous-carbon XRD peak among treatment comparison"
        ),
        BET_surface_area_product_m2_g="",
        characterization_methods="SEM; XRD; EDX",
        post_treatment_or_purification="none reported",
        purification_condition="none",
        application_property_summary="",
        notes=(
            "Scherrer sizes (~9.64/~12.63 nm) are retained in the summary as "
            "crystallite/particle values and not normalized as SEM tube diameter."
        ),
    )


def scale_review(run_id: str, summary: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="laboratory vertical structured-substrate batch",
        scale_level_claimed="reactor modification intended to reduce carbon loss and blockage",
        scale_evidence_summary=summary,
        reactor_capacity_or_throughput="4 g ferrocene per 20 min run; CNT mass up to 2.15 g",
        continuous_operation_time_h="0.333",
        catalyst_lifetime_or_reuse="not_reported",
        catalyst_reuse_cycles="not_reported",
        batch_stability="not_reported",
        scale_up_issue=(
            "reactor dimension/unit ambiguity, high impurity content, carbon loss, "
            "ferrocene utilization and substrate/catalyst fouling"
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="No monetary cost or measured energy consumption.",
        cost_driver_summary="ferrocene, Ar, two furnaces at 300/400 and 850 C, SS316 substrate",
        safety_risk="flammable decomposition gases, ferrocene/iron aerosol, high temperature",
        emission_or_waste="CH4, H2, cyclopentadiene, unidentified gases and iron/carbon solids",
        industrial_readiness_assessment="small batch proof-of-concept with high impurity burden",
        reproduction_value="medium",
        reproduction_priority="medium",
        recommended_next_action=(
            "clarify reactor dimensions, pretreatment temperature, yield collection "
            "boundary, carbon balance, repeatability and purified CNT mass"
        ),
        review_note="Calculated heat-capacity values are design estimates, not metered energy use.",
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
            "evidence_type": "pdf_visual_transcription",
            "source_section": f"PDF page {page}",
            "source_locator": f"PDF page {page}",
            "source_object_ref": PDF_REF,
            "evidence_text": text,
            "evidence_summary": summary,
            "notes": "Transcribed after visual inspection of the local open-access PDF.",
        }
    )
    tables["evidence_index"].append(item)


def build(
    metadata: dict[str, Any],
    store: EvidenceStore,
) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "Six records: two preliminary ferrocene-decomposition GC-TCD "
                "calibrations at 300/400 C and four 2x2 CNT syntheses varying "
                "vaporizer temperature and oxidative SS316 treatment."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_open_access_pdf"
    master["notes"] += (
        " Tables 2-7 and Figures 1-4 were visually checked. Gas-decomposition "
        "calibrations are kept separate from collected-CNT runs."
    )

    for item in GC_CONTROLS:
        run_id = f"{SOURCE_ID}_{item['code']}"
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                item["code"],
                f"Ferrocene GC-TCD calibration at {item['temperature']} C",
                item["summary"],
                "high",
            )
        )
        tables["catalyst_system"].append(catalyst(run_id, None))
        run_stages = gc_process(run_id, item["temperature"])
        tables["reactor_process_gas"].extend(run_stages)
        tables["yield_quality"].append(gc_product(run_id, item))
        tables["cost_scale_review"].append(scale_review(run_id, item["summary"]))

        common_text = (
            f"Ferrocene charge 4 g; vaporizer {item['temperature']} C; "
            f"Ar 150 cm3/min; atmospheric pressure 101.325 kPa. {item['summary']}"
        )
        add_evidence(
            tables,
            store,
            run_id,
            "RUN",
            "source_run",
            run_id,
            GC_SPAN,
            3,
            common_text,
            "Preliminary decomposition-calibration identity and result.",
        )
        add_evidence(
            tables,
            store,
            run_id,
            "CATALYST",
            "catalyst_system",
            f"{run_id}_CAT",
            METHOD_SPAN,
            2,
            common_text + " Reported study-level Fe/C ratio 0.469.",
            "Ferrocene/Fe catalyst and reactor-substrate context.",
        )
        add_evidence(
            tables,
            store,
            run_id,
            "PROCESS_1",
            "reactor_process_gas",
            f"{run_id}_S01",
            GC_SPAN,
            3,
            common_text + " Reactor reported height 737 cm and diameter 3 cm; "
            "GC samples covered 0-30 min and production duration selected as 20 min.",
            "GC calibration process.",
        )
        add_evidence(
            tables,
            store,
            run_id,
            "PRODUCT",
            "yield_quality",
            f"{run_id}_PROD",
            GC_SPAN,
            3,
            common_text,
            "GC-TCD methane/hydrogen composition.",
        )
        add_evidence(
            tables,
            store,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            METHOD_SPAN,
            2,
            common_text + " Reactor 1/2 design heat capacities were 2.762/3.133 kJ/s; "
            "these were calculated, not metered. No cost was reported.",
            "Scale and energy-design context.",
            status="review_assessment",
        )

    synthesis_ids: list[str] = []
    for item in SYNTHESIS_RUNS:
        run_id = f"{SOURCE_ID}_{item['code']}"
        synthesis_ids.append(run_id)
        summary = synthesis_summary(item)
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                item["code"],
                (
                    f"{item['vaporizer']} C vaporizer, "
                    f"{'oxidized' if item['treated'] else 'untreated'} SS316"
                ),
                summary,
                "high",
            )
        )
        tables["catalyst_system"].append(catalyst(run_id, item["treated"]))
        run_stages = synthesis_process(run_id, item["vaporizer"], item["treated"])
        tables["reactor_process_gas"].extend(run_stages)
        tables["yield_quality"].append(synthesis_product(run_id, item))
        tables["cost_scale_review"].append(scale_review(run_id, summary))

        add_evidence(
            tables,
            store,
            run_id,
            "RUN",
            "source_run",
            run_id,
            YIELD_SPAN,
            4,
            summary,
            "2x2 synthesis-condition identity and collected product.",
        )
        add_evidence(
            tables,
            store,
            run_id,
            "CATALYST",
            "catalyst_system",
            f"{run_id}_CAT",
            PRETREAT_SPAN,
            3,
            (
                f"{summary} Ferrocene 4 g acted as carbon source and Fe catalyst; "
                "horizontal SS316 area 37.68 cm2; study-level Fe/C ratio 0.469."
            ),
            "Ferrocene-derived Fe and SS316 catalytic substrate.",
        )
        for stage in run_stages:
            add_evidence(
                tables,
                store,
                run_id,
                f"PROCESS_{stage['stage_order']}",
                "reactor_process_gas",
                stage["process_stage_id"],
                PRETREAT_SPAN
                if stage["stage_type"].startswith("oxidative")
                else METHOD_SPAN,
                3 if stage["stage_type"].startswith("oxidative") else 2,
                (
                    f"Stage {stage['stage_order']} {stage['stage_type']}: "
                    f"temperature {stage['temperature_setpoint_C']} C; "
                    f"temperature range {stage['temperature_range_reported_C']} C; "
                    f"duration {stage['holding_time_min']} min; pressure "
                    f"{stage['pressure_original']} / {stage['pressure_kPa']} kPa; "
                    f"charge {stage['catalyst_loading_mass_g']} g; "
                    f"Ar {stage['inert_gas_flow_original']}; total flow "
                    f"{stage['total_flow_original']}; reactor "
                    f"{stage['reactor_size_summary']}; gas "
                    f"{stage['gas_composition_summary']}."
                ),
                f"Process stage {stage['stage_order']} support.",
            )
        add_evidence(
            tables,
            store,
            run_id,
            "PRODUCT",
            "yield_quality",
            f"{run_id}_PROD",
            YIELD_SPAN,
            4,
            summary,
            "Collected mass, ferrocene-basis yield, diameter and EDX result.",
        )
        add_evidence(
            tables,
            store,
            run_id,
            "PRODUCT_QUALITY",
            "yield_quality",
            f"{run_id}_PROD",
            QUALITY_SPAN,
            5,
            (
                f"{summary} XRD showed CNT peaks at 26 and 43 degrees, "
                "hexagonal graphite at 43.7 degrees, amorphous carbon, Fe3C, "
                "Fe3O4 and Fe2O3."
            ),
            "CNT identity and impurity phases.",
        )
        add_evidence(
            tables,
            store,
            run_id,
            "PRODUCT_DIAMETER",
            "yield_quality",
            f"{run_id}_PROD",
            DIAMETER_SPAN,
            5,
            (
                "Treatment-level XRD Scherrer size 9.64 nm and untreated "
                "size 12.63 nm; SEM apparent tube widths were 76-122.7 nm "
                "for treated and 94.6-110.5 nm for untreated substrate."
            ),
            "Measurement-definition-specific size values.",
            status="reported_mixed_diameter_definitions",
        )
        add_evidence(
            tables,
            store,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            YIELD_SPAN,
            4,
            (
                f"{summary} The 20 min run used 4 g ferrocene and yielded "
                f"{item['mass']} g product. No cost, repeatability, measured "
                "energy or catalyst reuse was reported."
            ),
            "Scale, material intensity and missing economics.",
            status="review_assessment",
        )

    ref = f"{SOURCE_ID}_VAP400_OXIDIZED"
    untreated = f"{SOURCE_ID}_VAP400_UNTREATED"
    gc_ref = f"{SOURCE_ID}_GC_FERROCENE_400C"
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_BASIS_001",
                SOURCE_ID,
                ref,
                "yield_definition",
                "yield_quality",
                f"{ref}_PROD",
                "yield_value_standardized",
                (
                    "Reported yield is collected CNT-labeled product mass divided "
                    "by the 4 g total ferrocene charge. It is not elemental-carbon "
                    "conversion and includes impurity-rich unpurified product."
                ),
                f"EVD_{ref}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_DIAMETER_001",
                SOURCE_ID,
                ref,
                "dimension_semantics",
                "yield_quality",
                f"{ref}_PROD",
                "outer_diameter_range_nm",
                (
                    "SEM apparent tube widths are tens to >100 nm, whereas XRD "
                    "Scherrer values are ~9.64/~12.63 nm crystallite/particle "
                    "sizes. These are retained separately and not averaged."
                ),
                f"EVD_{ref}_PRODUCT_DIAMETER;EVD_{untreated}_PRODUCT_DIAMETER",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PRETREAT_TEMP_001",
                SOURCE_ID,
                ref,
                "critical_data_gap",
                "reactor_process_gas",
                f"{ref}_S01",
                "temperature_setpoint_C",
                (
                    "Oxidative pretreatment duration (20 min) and air exposure "
                    "are reported, but the treatment temperature is not given."
                ),
                f"EVD_{ref}_PROCESS_1",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_REACTOR_SIZE_001",
                SOURCE_ID,
                ref,
                "reported_unit_ambiguity",
                "reactor_process_gas",
                f"{ref}_S02",
                "reactor_size_summary",
                (
                    "The paper reports a quartz reactor height of 737 cm and "
                    "diameter 3 cm; the unusually large height may be a unit "
                    "or decimal error, so it is preserved verbatim."
                ),
                f"EVD_{ref}_PROCESS_2",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_GC_TIME_SERIES_001",
                SOURCE_ID,
                gc_ref,
                "grouped_time_series",
                "yield_quality",
                f"{gc_ref}_PROD",
                "secondary_result_summary",
                (
                    "The 0-30 min methane/hydrogen GC series is a reactor "
                    "calibration, not seven independent CNT synthesis runs."
                ),
                f"EVD_{gc_ref}_PRODUCT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_EDX_SCOPE_001",
                SOURCE_ID,
                ref,
                "measurement_scope",
                "yield_quality",
                f"{ref}_PROD",
                "secondary_result_summary",
                (
                    "EDX C/O/Fe values are reported by treatment status without "
                    "separate values for 300 and 400 C vaporizer conditions, so "
                    "the same treatment-level values contextualize both runs."
                ),
                f"EVD_{ref}_PRODUCT;EVD_{SOURCE_ID}_VAP300_OXIDIZED_PRODUCT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_IMPURITIES_001",
                SOURCE_ID,
                ref,
                "product_mixture",
                "yield_quality",
                f"{ref}_PROD",
                "product_mixture_summary",
                (
                    "The collected material contains high amorphous carbon and "
                    "multiple Fe/graphite impurity phases; no purified CNT mass "
                    "or purity fraction is reported."
                ),
                f"EVD_{ref}_PRODUCT_QUALITY",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_ENERGY_001",
                SOURCE_ID,
                ref,
                "derived_design_value",
                "cost_scale_review",
                ref,
                "quantitative_cost_summary",
                (
                    "Reactor heat figures 2.762 and 3.133 kJ/s and a stated "
                    "1.892 kJ/s requirement are design calculations with decimal/"
                    "unit ambiguity, not measured energy consumption."
                ),
                f"EVD_{gc_ref}_COST",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_REPLICATES_001",
                SOURCE_ID,
                ref,
                "critical_data_gap",
                "cost_scale_review",
                ref,
                "batch_stability",
                (
                    "No replicate counts, error bars or run-to-run variability "
                    "are reported for the 2x2 yield comparison."
                ),
                f"EVD_{ref}_COST",
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
