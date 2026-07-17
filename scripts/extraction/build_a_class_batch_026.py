#!/usr/bin/env python3
"""Build the twenty-sixth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 26
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_BA29B44179EB3783"
PDF_REF = "data/raw/fulltext/pdf/LIT_BA29B44179EB3783_414357a3b135.pdf"
SI_REF = (
    "data/raw/fulltext/supplementary/LIT_BA29B44179EB3783/S0008622319312588_mmc1.pdf"
)

METHOD_SPAN = "SPAN_5C6098B25CDF8BF45F66"
WATER_SPAN = "SPAN_72A84EB117FAFF5924C2"
SI_SPAN = "SPAN_34A01A8D471020D3F8D4"

FEMO_SERIES = [
    (1, 2.35, 95.2, 2.4, 0.023, 1.76, 12.0),
    (2, 2.19, 96.5, 2.9, 0.021, 1.43, 18.0),
    (3, 2.43, 98.0, 3.2, 0.025, 1.45, 19.0),
    (4, 2.37, 98.7, 3.7, 0.028, 1.42, 17.0),
    (5, 2.30, 100.0, 3.8, 0.025, 1.29, 20.0),
]

FE_SERIES = [
    (1, 3.12, 100.0, 8.0, 0.024, 0.40, 10.0),
    (2, 3.55, 98.0, 12.0, 0.022, 0.22, 7.5),
    (3, 3.48, 74.0, 12.5, 0.025, 0.20, 6.5),
    (4, 3.58, 82.0, 13.0, 0.020, 0.154, 4.0),
    (5, 3.50, 87.0, 13.5, 0.020, 0.16, 8.0),
]

FLOW_SERIES = [
    (4, 14.2, 2.46, 1.45),
    (9, 15.5, 2.22, 1.32),
    (16, 17.8, 2.23, 1.70),
]


def catalyst(run_id: str, catalyst_type: str) -> dict[str, str]:
    femo = catalyst_type == "Fe/Mo"
    return catalyst_row(
        run_id,
        catalyst_label=(
            "Fe/Mo/Al2O3 multilayer thin film on Si(100)"
            if femo
            else "Fe/Al2O3 multilayer thin film on Si(100)"
        ),
        active_metals="Fe; Mo" if femo else "Fe",
        support_material="400 A Al2O3 on Si(100)",
        promoter="Mo interlayer" if femo else "none",
        metal_ratio_original="Fe/Mo = 5.5/0.5 A nominal" if femo else "Mo omitted",
        metal_ratio_standardized="Fe:Mo = 11:1 nominal thickness ratio"
        if femo
        else "Fe only",
        precursor_summary="elemental Fe and Mo evaporation sources; Al2O3 support layer",
        preparation_method="sequential electron-beam evaporation without breaking vacuum",
        preparation_modifier="base pressure <= 1.6 x 10^-6 mbar",
        preparation_detail=(
            "Nominal Fe/Mo/Al2O3 thickness 5.5/0.5/400 A; RBS measured "
            "5.0 +/- 0.4 A Fe and 0.4 +/- 0.3 A Mo."
            if femo
            else "Fe-only comparison retained the Fe/Al2O3 architecture with Mo omitted."
        ),
        drying_condition="not_applicable",
        calcination_condition="not_applicable",
        reduction_condition="H2/Ar anneal at 800 C for 2 min",
        activation_condition="standard 800 C reducing anneal",
        post_preparation_condition="immediately followed by low-pressure CVD",
        catalyst_particle_size_mean_nm="",
        catalyst_particle_size_range_nm="",
        catalyst_particle_size_qualifier=(
            "Annealed Fe/Mo particles 4.1 +/- 1.0 nm, n=461, on a "
            "10 nm Al2O3 TEM membrane; not one-to-one with the growth wafer."
            if femo
            else "Annealed Fe particles 5.4 +/- 1.3 nm, n=167, on a "
            "10 nm Al2O3 TEM membrane; not one-to-one with the growth wafer."
        ),
        phase_or_state_summary=(
            "Fe/Mo particles were smaller, more numerous and better defined after annealing."
            if femo
            else "Fe-only particles were larger and less clearly defined after annealing."
        ),
        dispersion_summary=(
            "TEM-resolved particle density 1.1 x 10^12 cm^-2, a lower bound."
            if femo
            else "TEM-resolved particle density 4.0 x 10^11 cm^-2, a lower bound."
        ),
        deactivation_summary="abrupt self-termination at approximately 210 min",
    )


def process(
    run_id: str,
    catalyst_type: str,
    *,
    duration: str = "13",
    acetylene: str = "4",
    wet_ar: str | None = None,
    top_heater: str | None = None,
    note: str = "",
) -> list[dict[str, str]]:
    if wet_ar is None:
        wet_ar = "20" if catalyst_type == "Fe/Mo" else "80"
    if top_heater is None:
        top_heater = "700 C" if catalyst_type == "Fe/Mo" else "not required"
    dry_ar = (
        f"{400 - int(wet_ar)} sccm"
        if wet_ar.isdigit() and int(wet_ar) <= 400
        else "varied to retain 400 sccm total Ar"
    )
    return [
        process_row(
            run_id,
            1,
            "catalyst_deposition",
            reactor_type="electron-beam evaporation system",
            scale_level="wafer_scale_batch",
            reactor_material="vacuum deposition chamber",
            reactor_size_summary="supports Si wafers up to 6 in.",
            reactor_setup_summary="sequential Fe/Mo/Al2O3 or Fe/Al2O3 deposition",
            catalyst_loading_mass_g="not_reported",
            temperature_setpoint_C="not_reported",
            temperature_program_summary="room-temperature thin-film deposition",
            holding_time_min="not_reported",
            heating_rate_C_min="not_applicable",
            cooling_condition="not_applicable",
            pressure_original="base pressure <= 1.6 x 10^-6 mbar",
            pressure_kPa="<= 1.6 x 10^-7",
            carbon_source="none",
            reducing_gas="none",
            inert_gas="none",
            cofeed_or_reactive_gas="Fe; Mo where applicable; Al2O3",
            gas_composition_summary="vacuum deposition",
            process_note="Layers deposited without breaking vacuum.",
        ),
        process_row(
            run_id,
            2,
            "pumpdown_ramp_and_reducing_anneal",
            reactor_type="AIXTRON Black Magic Pro 6 in. cold-wall low-pressure CVD",
            scale_level="wafer_scale_batch",
            reactor_material="cold-wall chamber with local heater and showerhead",
            reactor_size_summary="6 in. tool; 4- and 6-in. wafers demonstrated",
            reactor_setup_summary=(
                f"bottom heater 800 C; top heater {top_heater}; gas showerhead"
            ),
            catalyst_loading_mass_g="not_reported",
            temperature_setpoint_C="800",
            temperature_range_reported_C="room temperature to 800",
            temperature_program_summary="ramp 200-300 C/min to 800 C, then hold 2 min",
            holding_time_min="2",
            heating_rate_C_min="200-300",
            cooling_condition="not_reported for growth wafers",
            pressure_original="pump below 0.2 mbar, then anneal at 80 mbar",
            pressure_kPa="8",
            carbon_source="none",
            reducing_gas="H2",
            reducing_gas_flow_original="700 sccm",
            inert_gas="Ar",
            inert_gas_flow_original="200 sccm",
            cofeed_or_reactive_gas="none",
            total_flow_original="900 sccm",
            gas_composition_summary="H2/Ar = 700/200 sccm at 80 mbar",
            process_note="Chamber pumped below 0.2 mbar before recipe start.",
        ),
        process_row(
            run_id,
            3,
            "swcnt_forest_growth",
            reactor_type="AIXTRON Black Magic Pro 6 in. cold-wall low-pressure CVD",
            scale_level="wafer_scale_batch",
            reactor_material="cold-wall chamber with local heater and showerhead",
            reactor_size_summary="4- and 6-in. Si wafers",
            reactor_setup_summary=(
                f"bottom heater 800 C; top heater {top_heater}; water bubbler"
            ),
            catalyst_loading_mass_g="not_reported",
            temperature_setpoint_C="800",
            temperature_program_summary="isothermal growth after reducing anneal",
            holding_time_min=duration,
            heating_rate_C_min="not_applicable",
            cooling_condition="not_reported",
            pressure_original="80 mbar",
            pressure_kPa="8",
            carbon_source="C2H2",
            carbon_source_flow_original=f"{acetylene} sccm",
            reducing_gas="H2",
            reducing_gas_flow_original="700 sccm",
            inert_gas="Ar",
            inert_gas_flow_original=f"{dry_ar} dry plus {wet_ar} sccm through H2O bubbler",
            cofeed_or_reactive_gas="H2O vapor",
            cofeed_flow_original=(
                f"{wet_ar} sccm Ar through water bubbler; "
                "~170-1500 ppmv over the full x range"
            ),
            total_flow_original=f"{1100 + int(acetylene) if acetylene.isdigit() else 'varied'} sccm",
            gas_composition_summary=(
                f"C2H2/H2/Ar = {acetylene}/700/400 sccm total Ar; "
                f"{wet_ar} sccm Ar passed through H2O bubbler"
            ),
            process_note=note or "Standard wafer-scale forest growth condition.",
        ),
    ]


def product(
    run_id: str,
    *,
    metric: str,
    original: str,
    value: str = "",
    unit: str = "",
    summary: str,
    diameter: str = "",
    raman: str = "",
    purity: str = "",
    conversion: str = "",
    amorphous: str = "approximately 5% for standard 13 min Fe/Mo forest",
) -> dict[str, str]:
    return yield_row(
        run_id,
        primary_yield_metric=metric,
        yield_original=original,
        yield_definition_original=summary,
        yield_calculation_method=(
            "SEM height/witness bands, gravimetric or RBS mass, TEM, Raman and SAXS; "
            "figure-only point values are visually digitized"
        ),
        yield_value_standardized=value,
        yield_unit_standardized=unit,
        yield_standardization_note=(
            "Standardized only when a single run-level value is available; "
            "series-level values remain in the result summary."
        ),
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent=conversion,
        carbon_conversion_to_solid_percent=conversion,
        secondary_result_summary=summary,
        CNT_type_reported="vertically aligned SWCNT forest",
        CNT_type_confirmed="predominantly single-walled CNT forest",
        product_mixture_summary=(
            "SWCNT forest with a minor double-/triple-walled fraction and "
            "low-order carbon quantified where available"
        ),
        CNT_type_evidence="HRTEM; Raman RBM/G/D; SAXS absence of graphitic (002) peak",
        SWCNT_or_few_wall_evidence_summary=(
            f"SW purity {purity}."
            if purity
            else "Predominantly SWCNT by TEM/Raman/SAXS."
        ),
        RBM_peak_reported="reported",
        outer_diameter_mean_nm=diameter,
        outer_diameter_range_nm="",
        inner_diameter_mean_nm="",
        wall_number_summary="predominantly single-walled; minor double/triple walls",
        length_summary=original,
        morphology="vertically aligned wafer-scale forest",
        alignment_or_array="vertically aligned forest",
        Raman_ratio_type="integrated G/D",
        Raman_ratio_value=raman,
        Raman_laser_wavelength_nm="633",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis="TEM wall count; Raman; SAXS; TGA lower-order-carbon assessment",
        residue_summary="catalyst/substrate not included as harvested free product",
        amorphous_carbon_level=amorphous,
        BET_surface_area_product_m2_g="",
        characterization_methods="SEM; HRTEM; Raman; SAXS; RBS; gravimetry; TGA",
        post_treatment_or_purification="none before characterization except method-specific sampling",
        purification_condition="not_applicable",
        application_property_summary="wafer-scale structural uniformity and carbon efficiency",
        notes="Approximate graph readings are explicitly flagged in the issue log.",
    )


def scale_review(run_id: str, summary: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="full 4-in. and 6-in. Si wafer batch growth",
        scale_level_claimed="transferable toward larger-area and roll-to-roll synthesis",
        scale_evidence_summary=summary,
        reactor_capacity_or_throughput="one full wafer up to 6 in.; mass throughput not reported",
        continuous_operation_time_h="3.5 maximum demonstrated growth duration",
        catalyst_lifetime_or_reuse="abrupt self-termination at approximately 210 min",
        catalyst_reuse_cycles="not_applicable thin-film catalyst consumed with wafer",
        batch_stability="five sequential 4-in. runs for both Fe/Mo and Fe",
        scale_up_issue=(
            "carbon delivery did not scale proportionally with substrate area; "
            "thermal gradient, water concentration and showerhead distribution require control"
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="No monetary cost or energy intensity was reported.",
        cost_driver_summary=(
            "electron-beam catalyst deposition, H2, low-pressure pumping, "
            "800 C heating, acetylene and wafer substrates"
        ),
        safety_risk="flammable H2/C2H2, hot surfaces, vacuum equipment and pressurized gases",
        emission_or_waste="unquantified C2H2/H2/Ar exhaust and single-use catalyst-coated wafers",
        industrial_readiness_assessment=(
            "strong wafer-scale batch demonstration; continuous manufacture not demonstrated"
        ),
        reproduction_value="high",
        reproduction_priority="high",
        recommended_next_action=(
            "publish raw run-level mass/height maps, exact water ppm, flow residence "
            "time, energy use and throughput-normalized economics"
        ),
        review_note="Resource efficiency is quantified by carbon conversion, not cost.",
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
    supplement: bool = False,
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
            "evidence_type": (
                "supplementary_pdf_visual_transcription"
                if supplement
                else "pdf_visual_transcription"
            ),
            "source_section": f"{'SI ' if supplement else ''}PDF page {page}",
            "source_locator": f"{'SI ' if supplement else ''}PDF page {page}",
            "source_object_ref": SI_REF if supplement else PDF_REF,
            "evidence_text": text,
            "evidence_summary": summary,
            "notes": (
                "Transcribed after visual inspection of the local supplementary PDF."
                if supplement
                else "Transcribed after visual inspection of the local full-text PDF."
            ),
        }
    )
    tables["evidence_index"].append(item)


def add_run(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    *,
    code: str,
    label: str,
    run_summary: str,
    catalyst_type: str,
    stages: list[dict[str, str]],
    result: dict[str, str],
    span: str,
    page: int,
    result_text: str,
    supplement: bool = False,
    confidence: str = "high",
) -> str:
    run_id = f"{SOURCE_ID}_{code}"
    tables["source_run"].append(
        run_row(SOURCE_ID, code, label, run_summary, confidence)
    )
    tables["catalyst_system"].append(catalyst(run_id, catalyst_type))
    tables["reactor_process_gas"].extend(stages)
    tables["yield_quality"].append(result)
    tables["cost_scale_review"].append(scale_review(run_id, run_summary))

    add_evidence(
        tables,
        store,
        run_id,
        "RUN",
        "source_run",
        run_id,
        span,
        page,
        run_summary,
        "Run identity and experimental grouping.",
        supplement=supplement,
        confidence=confidence,
        status="reported_or_grouped_as_stated",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "CATALYST",
        "catalyst_system",
        f"{run_id}_CAT",
        METHOD_SPAN,
        30,
        run_summary
        + " "
        + (
            "Nominal Fe/Mo/Al2O3 thickness was 5.5/0.5/400 A. "
            "Fe/Mo particles were 4.1 +/- 1.0 nm at 1.1 x 10^12 cm^-2."
            if catalyst_type == "Fe/Mo"
            else "The Fe-only film omitted Mo. Fe particles were "
            "5.4 +/- 1.3 nm at 4.0 x 10^11 cm^-2."
        ),
        "Catalyst film, annealing and particle-characterization context.",
    )
    for stage in stages:
        add_evidence(
            tables,
            store,
            run_id,
            f"PROCESS_{stage['stage_order']}",
            "reactor_process_gas",
            stage["process_stage_id"],
            METHOD_SPAN if stage["stage_order"] < "3" else WATER_SPAN,
            30,
            (
                f"Stage {stage['stage_order']}: {stage['stage_type']}; "
                f"temperature {stage['temperature_setpoint_C']} C; "
                f"pressure {stage['pressure_original']}; "
                f"duration {stage['holding_time_min']} min; "
                f"heating rate {stage['heating_rate_C_min']} C/min; "
                f"gas {stage['gas_composition_summary']}; "
                f"inert flow {stage['inert_gas_flow_original']}; "
                f"cofeed {stage['cofeed_flow_original']}; "
                f"total flow {stage['total_flow_original']}."
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
        span,
        page,
        result_text + " Raman excitation wavelength 633 nm.",
        "Yield, kinetics, structure and quality outcome.",
        supplement=supplement,
        confidence=confidence,
        status="mixed_reported_and_visually_digitized",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "COST",
        "cost_scale_review",
        run_id,
        "SPAN_1D4AA2A453372414B120",
        24,
        run_summary
        + " Full wafers up to 6 in. were demonstrated; cost and energy were not reported.",
        "Scale evidence and industrial data gaps.",
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
                "Nineteen run records covering five Fe/Mo and five Fe sequential "
                "wafer growths, two long self-termination experiments, three "
                "acetylene-flow conditions, and grouped water, top-heater and "
                "uniformity controls from the article and its Supporting Information."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_fulltext_pdf_with_supplement"
    master["notes"] += (
        " The publisher Supporting Information was acquired from the Elsevier "
        "content CDN and visually checked. Wafer maps from Figures 3-4 and "
        "Figures S4-S8 are attached to Fe/Mo sequential Run 1 because they "
        "characterize the same physical growth."
    )

    run_ids: list[str] = []
    for number, diameter, purity, height_rate, mass_rate, density, gd in FEMO_SERIES:
        mapping = ""
        if number == 1:
            mapping = (
                " Full-wafer mapping of this same sample found SAXS diameter "
                "2.07 +/- 0.07 nm (range 1.88-2.21, CV 0.03), RBS-derived "
                "number density 2.26 +/- 0.27 x 10^12 cm^-2 (range 1.77-3.17, "
                "CV 0.12), center/edge TEM diameters 2.15 +/- 0.86 and "
                "2.06 +/- 0.89 nm, Raman-map height 31.7 +/- 3.5 um versus "
                "optical 35.1 +/- 1.8 um, and G/D up to approximately 15 "
                "at the center. Raman mapping used a 6.5 x 6.5 cm area, "
                "500 um steps and 17,161 points. RBM maps showed increasing "
                "small-diameter abundance toward the edge. SAXS-TEM fit was "
                "dSAXS=1.12*dTEM+0.34 (R2=0.97); RBS-balance slope 0.98 "
                "(R2=0.99). Standard-growth amorphous carbon was 5%."
            )
        summary = (
            f"Sequential Fe/Mo 4-in. wafer run {number}: visually digitized "
            f"diameter {diameter} nm, SW purity {purity}%, height kinetics "
            f"{height_rate} um/min, mass kinetics {mass_rate} mg/cm2/min, "
            f"number density {density} x 10^12 cm^-2 and G/D {gd}.{mapping}"
        )
        run_id = f"{SOURCE_ID}_FEMO_SEQ_{number:02d}"
        run_ids.append(
            add_run(
                tables,
                store,
                code=f"FEMO_SEQ_{number:02d}",
                label=f"Fe/Mo sequential 4-in. wafer growth run {number}",
                run_summary=summary,
                catalyst_type="Fe/Mo",
                stages=process(run_id, "Fe/Mo"),
                result=product(
                    run_id,
                    metric="forest_height_kinetics",
                    original=f"approximately {height_rate} um/min",
                    value=str(height_rate),
                    unit="um/min",
                    summary=summary,
                    diameter=str(diameter),
                    raman=str(gd),
                    purity=str(purity),
                ),
                span="SPAN_31507B431901330D9853",
                page=9,
                result_text=summary,
                confidence="medium",
            )
        )

    for number, diameter, purity, height_rate, mass_rate, density, gd in FE_SERIES:
        summary = (
            f"Sequential Fe-only 4-in. wafer run {number}: Figure S3 visually "
            f"digitized diameter {diameter} nm, SW purity {purity}%, height "
            f"kinetics {height_rate} um/min, mass kinetics {mass_rate} mg/cm2/min, "
            f"number density {density} x 10^12 cm^-2 and G/D {gd}. The SI "
            "reports overall G/D 4-10, diameter 3.12-3.58 nm, purity as low "
            "as 74%, density variation of 60% with a minimum 1.54 x 10^11 "
            "cm^-2, and average height kinetics 11.7 um/min."
        )
        run_id = f"{SOURCE_ID}_FE_SEQ_{number:02d}"
        run_ids.append(
            add_run(
                tables,
                store,
                code=f"FE_SEQ_{number:02d}",
                label=f"Fe-only sequential 4-in. wafer growth run {number}",
                run_summary=summary,
                catalyst_type="Fe",
                stages=process(run_id, "Fe"),
                result=product(
                    run_id,
                    metric="forest_height_kinetics",
                    original=f"approximately {height_rate} um/min",
                    value=str(height_rate),
                    unit="um/min",
                    summary=summary,
                    diameter=str(diameter),
                    raman=str(gd),
                    purity=str(purity),
                    amorphous="not separately quantified for Fe-only series",
                ),
                span=SI_SPAN,
                page=4,
                result_text=summary,
                supplement=True,
                confidence="medium",
            )
        )

    for catalyst_type, height in [("Fe", 1700), ("Fe/Mo", 800)]:
        code = f"{catalyst_type.replace('/', '')}_TERMINATION_210MIN".upper()
        run_id = f"{SOURCE_ID}_{code}"
        summary = (
            f"{catalyst_type} 4-in. wafer long-growth experiment self-terminated "
            f"abruptly at 210 min with terminal forest height {height / 1000:g} mm "
            "and mass incorporation approximately 0.16 mg/cm2/min. Witness "
            "bands were made by switching C2H2 on 10 min and off 1 min. "
            + (
                "TGA of the long Fe/Mo forest measured 6.5% amorphous carbon."
                if catalyst_type == "Fe/Mo"
                else "Long-run Fe amorphous-carbon fraction was not separately reported."
            )
        )
        run_ids.append(
            add_run(
                tables,
                store,
                code=code,
                label=f"{catalyst_type} full self-termination growth",
                run_summary=summary,
                catalyst_type=catalyst_type,
                stages=process(
                    run_id,
                    catalyst_type,
                    duration="210",
                    note="C2H2 cyclically switched on 10 min and off 1 min for witness bands.",
                ),
                result=product(
                    run_id,
                    metric="terminal_forest_height",
                    original=f"{height / 1000:g} mm at 210 min",
                    value=str(height),
                    unit="um",
                    summary=summary,
                    amorphous=(
                        "6.5% by TGA"
                        if catalyst_type == "Fe/Mo"
                        else "not separately quantified"
                    ),
                ),
                span="SPAN_4212B5CC31F8F905249E",
                page=22,
                result_text=summary,
            )
        )

    for flow, gd, diameter, density in FLOW_SERIES:
        code = f"FEMO_FLOW_{flow:02d}SCCM"
        run_id = f"{SOURCE_ID}_{code}"
        summary = (
            f"Fe/Mo wafer-scale C2H2-flow condition at {flow} sccm, with "
            f"Figure S16 visually digitized G/D approximately {gd}, diameter "
            f"{diameter} nm and density {density} x 10^12 cm^-2. Across 4, 9 "
            "and 16 sccm, mass kinetics increased proportionally while diameter, "
            "graphitization and density changed little. Growth times were 3-15 "
            "min. Mean carbon conversion across the three flows was 47.1 +/- "
            "1.7% on 4-in. wafers and 64.3 +/- 4.5% on 6-in. wafers; catalyst-"
            "normalized values were 1.24 +/- 0.04 and 0.80 +/- 0.05 x 10^6 "
            "% g-catalyst^-1, respectively."
        )
        run_ids.append(
            add_run(
                tables,
                store,
                code=code,
                label=f"Fe/Mo C2H2 flow series, {flow} sccm",
                run_summary=summary,
                catalyst_type="Fe/Mo",
                stages=process(
                    run_id,
                    "Fe/Mo",
                    duration="3-15",
                    acetylene=str(flow),
                    note="Grouped flow condition from 4- and 6-in. wafer experiments.",
                ),
                result=product(
                    run_id,
                    metric="flow_condition_structural_response",
                    original=f"C2H2 {flow} sccm; 3-15 min growths",
                    summary=summary,
                    diameter=str(diameter),
                    raman=str(gd),
                ),
                span="SPAN_4663275B3F31B383BF1C",
                page=24,
                result_text=summary,
                supplement=True,
                confidence="medium",
            )
        )

    for catalyst_type, count, wet in [("Fe", 36, "0-400"), ("Fe/Mo", 11, "0-400")]:
        code = f"{catalyst_type.replace('/', '')}_WATER_SCREEN".upper()
        run_id = f"{SOURCE_ID}_{code}"
        summary = (
            f"Grouped {catalyst_type} H2O concentration screen on 4-in. wafers "
            f"(n={count} with water; the no-water reproducibility set contained "
            "n=57 total experiments). Coverage was scored qualitatively Q1-Q5. "
            "The main text identifies an optimal approximately 120-250 ppmv "
            "window; bubbler conditions across the study generated roughly "
            "170-1500 ppmv. Individual point values were not numerically tabulated."
        )
        run_ids.append(
            add_run(
                tables,
                store,
                code=code,
                label=f"{catalyst_type} water-vapor coverage screen",
                run_summary=summary,
                catalyst_type=catalyst_type,
                stages=process(
                    run_id,
                    catalyst_type,
                    duration="13",
                    wet_ar=wet,
                    note="Grouped H2O screen; qualitative Q1-Q5 wafer coverage.",
                ),
                result=product(
                    run_id,
                    metric="qualitative_wafer_coverage_Q1_Q5",
                    original="optimal H2O approximately 120-250 ppmv",
                    summary=summary,
                    amorphous="not measured for each water-screen experiment",
                ),
                span=SI_SPAN,
                page=2,
                result_text=summary,
                supplement=True,
                confidence="medium",
            )
        )

    code = "FEMO_TOP_HEATER_SCREEN"
    run_id = f"{SOURCE_ID}_{code}"
    summary = (
        "Grouped Fe/Mo top-heater screen at bottom-heater 800 C and 20 sccm "
        "wet Ar compared top heater off with 700 C. Figure S2 reports sample "
        "sizes n=54, 33, 6 and 3 for all-run/after-first-run groupings. Top "
        "heating improved wafer coverage, while mass kinetics remained near "
        "0.02-0.03 mg/cm2/min without a clear enhancement."
    )
    run_ids.append(
        add_run(
            tables,
            store,
            code=code,
            label="Fe/Mo top-heater coverage and mass-kinetics screen",
            run_summary=summary,
            catalyst_type="Fe/Mo",
            stages=process(
                run_id,
                "Fe/Mo",
                top_heater="off versus 700 C",
                note="Grouped top-heater comparison with 20 sccm wet Ar.",
            ),
            result=product(
                run_id,
                metric="top_heater_coverage_response",
                original="top heater off versus 700 C",
                summary=summary,
                amorphous="not measured for each top-heater experiment",
            ),
            span=SI_SPAN,
            page=3,
            result_text=summary,
            supplement=True,
            confidence="medium",
        )
    )

    code = "FEMO_UNIFORMITY_WITNESS_CONTROL"
    run_id = f"{SOURCE_ID}_{code}"
    summary = (
        "Grouped Fe/Mo uniform versus unsuccessful/non-uniform 4-in. wafer "
        "witness-band comparison. C2H2 was pulsed on 1 min and off 1 min for "
        "30 min. In the non-uniform case, early termination began at the center "
        "and edge growth accelerated; the uniform case showed similar center "
        "and edge height trajectories. Figure-only curves were not digitized "
        "into invented exact time-series points."
    )
    run_ids.append(
        add_run(
            tables,
            store,
            code=code,
            label="Fe/Mo center-edge uniformity witness-band control",
            run_summary=summary,
            catalyst_type="Fe/Mo",
            stages=process(
                run_id,
                "Fe/Mo",
                duration="30",
                note="C2H2 pulsed 1 min on and 1 min off; center and edge compared.",
            ),
            result=product(
                run_id,
                metric="center_edge_height_kinetics",
                original="uniform versus non-uniform 30 min pulse experiment",
                summary=summary,
                amorphous="not quantified for uniformity control",
            ),
            span="SPAN_E47E05C6D76EC80C9A24",
            page=15,
            result_text=summary,
            supplement=True,
            confidence="medium",
        )
    )

    reference = run_ids[0]
    fe_reference = f"{SOURCE_ID}_FE_SEQ_01"
    flow_reference = f"{SOURCE_ID}_FEMO_FLOW_04SCCM"
    long_reference = f"{SOURCE_ID}_FEMO_TERMINATION_210MIN"
    water_reference = f"{SOURCE_ID}_FEMO_WATER_SCREEN"
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_DIGITIZATION_001",
                SOURCE_ID,
                reference,
                "figure_digitization",
                "yield_quality",
                f"{reference}_PROD",
                "secondary_result_summary",
                (
                    "Run-specific Figure 2, Figure S3 and Figure S16 point values "
                    "were visually digitized; exact raw values and individual "
                    "error bars were unavailable."
                ),
                f"EVD_{reference}_PRODUCT;EVD_{fe_reference}_PRODUCT;"
                f"EVD_{flow_reference}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_MAP_IDENTITY_001",
                SOURCE_ID,
                reference,
                "sample_identity_merge",
                "yield_quality",
                f"{reference}_PROD",
                "secondary_result_summary",
                (
                    "Figures 3-4 and Figures S4-S8 characterize sequential Fe/Mo "
                    "Run 1 and are merged into that run rather than counted as "
                    "additional synthesis experiments."
                ),
                f"EVD_{reference}_PRODUCT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FE_RECIPE_001",
                SOURCE_ID,
                fe_reference,
                "inferred_condition",
                "catalyst_system",
                f"{fe_reference}_CAT",
                "preparation_detail",
                (
                    "The Fe-only comparison is described as Fe/Al2O3 without Mo; "
                    "the package treats it as the nominal Fe architecture with "
                    "Mo omitted, but the SI does not restate every deposition detail."
                ),
                f"EVD_{fe_reference}_CATALYST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FLOW_GROUPING_001",
                SOURCE_ID,
                flow_reference,
                "grouped_condition_series",
                "source_run",
                flow_reference,
                "run_summary",
                (
                    "Flow records group results by 4, 9 and 16 sccm across 4- "
                    "and 6-in. wafers. Size-level mean conversions are not "
                    "assigned as exact replicate values to individual growths."
                ),
                f"EVD_{flow_reference}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_WATER_GROUPING_001",
                SOURCE_ID,
                water_reference,
                "grouped_condition_series",
                "source_run",
                water_reference,
                "run_summary",
                (
                    "The H2O screen contains 57 no-water, 36 Fe-water and 11 "
                    "Fe/Mo-water experiments, but only grouped Q1-Q5 plot data "
                    "are available; individual runs were not invented."
                ),
                f"EVD_{water_reference}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_TOP_HEATER_GROUPING_001",
                SOURCE_ID,
                f"{SOURCE_ID}_FEMO_TOP_HEATER_SCREEN",
                "grouped_condition_series",
                "source_run",
                f"{SOURCE_ID}_FEMO_TOP_HEATER_SCREEN",
                "run_summary",
                (
                    "Top-heater statistics use overlapping all-run and after-"
                    "first-run groupings with different sample sizes; these are "
                    "retained as one grouped control."
                ),
                f"EVD_{SOURCE_ID}_FEMO_TOP_HEATER_SCREEN_PRODUCT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CATALYST_PARTICLE_SCOPE_001",
                SOURCE_ID,
                reference,
                "measurement_scope",
                "catalyst_system",
                f"{reference}_CAT",
                "catalyst_particle_size_qualifier",
                (
                    "Catalyst particles were measured after annealing on 10 nm "
                    "Al2O3-coated TEM membranes, whereas growth wafers used "
                    "40 nm Al2O3; particle statistics are contextual, not direct "
                    "run-level wafer measurements."
                ),
                f"EVD_{reference}_CATALYST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_LONG_TGA_SCOPE_001",
                SOURCE_ID,
                long_reference,
                "measurement_scope",
                "yield_quality",
                f"{long_reference}_PROD",
                "amorphous_carbon_level",
                (
                    "The 6.5% amorphous-carbon TGA value applies to the long "
                    "Fe/Mo forest; the corresponding long Fe value was not reported."
                ),
                f"EVD_{long_reference}_PRODUCT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_COST_001",
                SOURCE_ID,
                reference,
                "critical_data_gap",
                "cost_scale_review",
                reference,
                "quantitative_cost_summary",
                (
                    "Despite unusually detailed conversion and wafer-scale data, "
                    "energy use, monetary cost, gas utilization beyond carbon, "
                    "and mass throughput are not reported."
                ),
                f"EVD_{reference}_COST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_MODEL_SCOPE_001",
                SOURCE_ID,
                flow_reference,
                "derived_model",
                "yield_quality",
                f"{flow_reference}_PROD",
                "secondary_result_summary",
                (
                    "The paper's density-height analytical model, power-law "
                    "N=3.6x10^13 d^-3.7 (R2=0.78), close-packing extrapolation "
                    "and SSA=1315 m2/g are retained in evidence/summary context "
                    "rather than represented as additional experimental runs."
                ),
                f"EVD_{flow_reference}_PRODUCT",
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
