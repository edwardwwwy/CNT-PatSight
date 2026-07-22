#!/usr/bin/env python3
"""Build the twenty-second evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 22
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ID = "LIT_010B9BF252F13139"
PDF_REF = "data/raw/literature/pdf/LIT_010B9BF252F13139_42df7ef02687.pdf"
SI_REF = "data/raw/literature/supplements/LIT_010B9BF252F13139/nn4c15449_si_001.pdf"

COMMON_RECIPE = (
    "FCCVD reactor: 700 mm alumina tube, 40 mm internal diameter and 5 mm "
    "wall, externally heated. Total injected precursor/catalyst/hydrogen "
    "flow was 0.8 slpm. Methane was the carbon source. Ferrocene vapor was "
    "supplied by 0.015 slpm H2 through three 150 mL copper-lined chambers, "
    "each containing 30 g ferrocene at 80 C. Thiophene vapor was supplied "
    "by 0.01 slpm H2 through a diffuser immersed in 200 mL thiophene at "
    "1 C. Before each experiment the reactor was purged with 1.5 slpm Ar "
    "for 20 min and 1.5 slpm H2 for 20 min; the ferrocene container was "
    "then purged with 30 sccm H2 for 45 min."
)

SAMPLING_RECIPE = (
    "A 50 sccm sample was extracted on the reactor centreline through a "
    "1.5 mm-ID alumina tube. The sampled aerosol was quenched with 5 slpm "
    "N2; a 1 slpm diluted portion was analyzed by CPMA/CPC/electrometer, "
    "and a 2 slpm portion was collected on a TEM grid for 2-20 min."
)

# Figure S1. Values are visually transcribed; precursor fractions were changed
# together, so these are coupled screening conditions rather than a one-factor
# methane series.
AEROGEL_SCREEN = [
    {
        "code": "SCREEN_M53",
        "methane": "5.3",
        "ferrocene": "0.0014",
        "thiophene": "0.038",
        "aerogel": "not present",
        "filter": "visible CNTs present",
    },
    {
        "code": "SCREEN_M58",
        "methane": "5.8",
        "ferrocene": "0.0021",
        "thiophene": "0.045",
        "aerogel": "present",
        "filter": "visible CNTs present",
    },
    {
        "code": "SCREEN_M64",
        "methane": "6.35",
        "ferrocene": "0.0029",
        "thiophene": "0.054",
        "aerogel": "present",
        "filter": "not present",
    },
    {
        "code": "SCREEN_M74",
        "methane": "7.35",
        "ferrocene": "0.0045",
        "thiophene": "0.069",
        "aerogel": "present",
        "filter": "not present",
    },
    {
        "code": "SCREEN_M93",
        "methane": "9.3",
        "ferrocene": "0.0075",
        "thiophene": "0.098",
        "aerogel": "present",
        "filter": "not present",
    },
]

# Figure 6b, visually digitized from the published high-resolution figure.
MASS_RATE = {
    275: ("0.05", "1470"),
    280: ("0.06", "1480"),
    285: ("0.08", "1490"),
    290: ("0.13", "1498"),
    295: ("0.17", "1500"),
    300: ("0.40", "1501"),
    305: ("0.64", "1505"),
    310: ("0.82", "1509"),
    315: ("1.00", "1513"),
    320: ("0.71", "1516"),
    325: ("0.41", "1518"),
}

AXIAL_POSITIONS = [
    250,
    275,
    280,
    285,
    290,
    295,
    300,
    305,
    310,
    315,
    320,
    325,
    330,
    400,
    500,
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
            "notes": "Transcribed after visual inspection of the locally stored PDF.",
        }
    )
    tables["evidence_index"].append(item)


def catalyst(
    run_id: str,
    *,
    methane_fraction: str = "5.3",
    ferrocene_fraction: str = "0.0014",
    thiophene_fraction: str = "0.038",
    position: int | None = None,
) -> dict[str, str]:
    fraction_text = (
        f"relative-to-H2 mole fractions: methane approximately "
        f"{methane_fraction}%, ferrocene approximately {ferrocene_fraction}%, "
        f"thiophene approximately {thiophene_fraction}%"
    )
    position_note = ""
    if position == 250:
        position_note = (
            "Only catalyst nanoparticles were observed on the TEM grid at X=250 mm; "
            "less than 4% lay in the diameter range observed at CNT tips."
        )
    elif position == 300:
        position_note = (
            "At X=300 mm, 82% of catalyst nanoparticles lay in the diameter "
            "range observed for particles at CNT tips."
        )
    elif position == 400:
        position_note = (
            "At X=400 mm, 92% of catalyst nanoparticles lay in the diameter "
            "range observed for particles at CNT tips."
        )
    elif position is not None:
        position_note = (
            "Catalyst nanoparticle mass decreased and its distribution narrowed "
            "with increasing axial position."
        )
    return catalyst_row(
        run_id,
        catalyst_label="in-situ floating Fe catalyst from ferrocene vapor",
        active_metals="Fe",
        support_material="not_applicable_floating_catalyst",
        promoter="thiophene-derived sulfur promoter",
        metal_ratio_original=fraction_text,
        metal_ratio_standardized="not_reported_as_atomic_Fe_to_S_ratio",
        precursor_summary=(
            "ferrocene vapor in H2 plus thiophene vapor in H2; methane carbon source"
        ),
        preparation_method="in_situ_floating_catalyst_vapor_generation",
        preparation_modifier=(
            "ferrocene held at 80 C in three powder chambers; thiophene held at 1 C"
        ),
        preparation_detail=COMMON_RECIPE,
        drying_condition="not_applicable",
        calcination_condition="not_applicable",
        reduction_condition="continuous H2 carrier during in-situ particle formation",
        activation_condition="thermal ferrocene decomposition in rising-temperature zone",
        post_preparation_condition=position_note
        or "continuously generated aerosol catalyst",
        catalyst_particle_size_mean_nm="not_reported",
        catalyst_particle_size_range_nm="not_reported",
        catalyst_particle_size_qualifier=(
            "Figure 7 gives position-dependent distributions; fractions in the "
            "CNT-tip size range are retained in phase/state summary."
        ),
        phase_or_state_summary=position_note or fraction_text,
        dispersion_summary="aerosolized individual particles and particle agglomerates",
        deactivation_summary=(
            "CNT nucleation/growth depends on evolving catalyst size, population "
            "and sulfur state; these were not reduced to a single lifetime metric."
        ),
    )


def precondition_stage(run_id: str) -> dict[str, str]:
    return process_row(
        run_id,
        1,
        "reactor_preheat_and_purge",
        reactor_type="horizontal floating-catalyst CVD tube reactor",
        scale_level="lab_continuous_aerosol_reactor",
        reactor_material="alumina",
        reactor_size_summary="700 mm length; 40 mm ID; 5 mm wall thickness",
        reactor_setup_summary="externally heated alumina tube in Vecstar VTF7 furnace",
        temperature_setpoint_C="not_reported",
        temperature_program_summary=(
            "heated under 1.5 slpm air; then Ar purge 20 min, H2 purge 20 min "
            "and ferrocene-container H2 purge 45 min"
        ),
        holding_time_min="20 min Ar + 20 min H2 + 45 min ferrocene purge",
        heating_rate_C_min="not_reported",
        cooling_condition="not_applicable_before_growth",
        pressure_original="near atmospheric; exact pressure not reported",
        pressure_kPa="",
        carbon_source="none during purge",
        carbon_source_flow_original="not_applicable",
        reducing_gas="H2",
        reducing_gas_flow_original="1.5 slpm for 20 min; 30 sccm through ferrocene for 45 min",
        inert_gas="Ar",
        inert_gas_flow_original="1.5 slpm for 20 min",
        cofeed_or_reactive_gas="air during furnace heat-up",
        cofeed_flow_original="1.5 slpm",
        total_flow_original="stage dependent",
        gas_composition_summary="air heat-up followed by Ar and H2 purge sequence",
        process_note=COMMON_RECIPE,
    )


def growth_stage(
    run_id: str,
    *,
    methane_fraction: str,
    ferrocene_fraction: str,
    thiophene_fraction: str,
    duration: str,
    position: int | None = None,
) -> dict[str, str]:
    location = (
        f"centreline sample extracted at X={position} mm"
        if position is not None
        else "whole-reactor aerogel/filter screening"
    )
    return process_row(
        run_id,
        2,
        "fccvd_growth_and_aerosol_sampling",
        reactor_type="horizontal floating-catalyst CVD tube reactor",
        scale_level="lab_continuous_aerosol_reactor",
        reactor_material="alumina",
        reactor_size_summary="700 mm length; 40 mm ID; 5 mm wall thickness",
        reactor_setup_summary=f"{location}; {SAMPLING_RECIPE}",
        temperature_setpoint_C=(
            MASS_RATE[position][1] if position in MASS_RATE else "not_reported"
        ),
        temperature_program_summary=(
            "reactants traverse a measured rising then falling axial temperature profile"
        ),
        holding_time_min=duration,
        heating_rate_C_min="not_applicable_steady_profile",
        cooling_condition="sampled flow quenched immediately with 5 slpm N2",
        pressure_original="near atmospheric; exact pressure not reported",
        pressure_kPa="",
        carbon_source="methane",
        carbon_source_flow_original=(
            f"approximately {methane_fraction} mol% relative to H2; "
            "volumetric methane flow not separately reported"
        ),
        reducing_gas="H2",
        reducing_gas_flow_original=(
            "balance of 0.8 slpm total injected flow; includes 0.015 slpm "
            "through ferrocene and 0.01 slpm through thiophene"
        ),
        inert_gas="none in reactor growth feed",
        inert_gas_flow_original="not_applicable",
        cofeed_or_reactive_gas=(
            f"ferrocene approximately {ferrocene_fraction} mol% and thiophene "
            f"approximately {thiophene_fraction} mol%, each relative to H2"
        ),
        cofeed_flow_original=(
            "ferrocene carrier 0.015 slpm H2; thiophene carrier 0.01 slpm H2"
        ),
        total_flow_original="0.8 slpm precursors, catalyst and hydrogen",
        gas_composition_summary=(
            f"CH4/H2/ferrocene/thiophene; approximate relative-to-H2 mole "
            f"fractions {methane_fraction}%/{ferrocene_fraction}%/"
            f"{thiophene_fraction}%"
        ),
        process_note=(
            f"{COMMON_RECIPE} {SAMPLING_RECIPE} Growth/sampling location: {location}."
        ),
    )


def aerogel_product(run_id: str, item: dict[str, str]) -> dict[str, str]:
    outcome = (
        f"CNT aerogel in reactor: {item['aerogel']}; downstream filter: "
        f"{item['filter']}"
    )
    return yield_row(
        run_id,
        primary_yield_metric="qualitative_aerogel_and_downstream_filter_presence",
        yield_original=outcome,
        yield_definition_original=(
            "visual observation after 15 min precursor injection; SEM confirmed CNTs"
        ),
        yield_calculation_method="qualitative_visual_and_SEM_classification",
        yield_value_standardized="",
        yield_unit_standardized="",
        yield_standardization_note="No mass yield or concentration conversion.",
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=outcome,
        CNT_type_reported="CNT",
        CNT_type_confirmed="CNT confirmed by SEM",
        product_mixture_summary="CNT aerogel and/or CNT-coated exhaust filter",
        CNT_type_evidence="optical observation and SEM",
        SWCNT_or_few_wall_evidence_summary="not_reported_for_screening_series",
        RBM_peak_reported="not_reported",
        outer_diameter_mean_nm="not_reported",
        outer_diameter_range_nm="not_reported",
        inner_diameter_mean_nm="not_reported",
        wall_number_summary="not_reported",
        length_summary="not_reported_for_screening_series",
        morphology=outcome,
        alignment_or_array="aerogel network or dispersed exhaust deposit",
        Raman_ratio_type="not_reported",
        Raman_ratio_value="not_reported",
        Raman_laser_wavelength_nm="not_reported",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis="not_reported",
        residue_summary="not_reported",
        amorphous_carbon_level="not_reported",
        BET_surface_area_product_m2_g="",
        characterization_methods="optical observation; SEM",
        post_treatment_or_purification="none",
        purification_condition="not_applicable",
        application_property_summary="aerogel-formation boundary screen",
    )


def axial_product(run_id: str, position: int) -> dict[str, str]:
    rate = MASS_RATE.get(position)
    primary = (
        f"normalized mass production rate Mdot/MdotMax approximately {rate[0]}"
        if rate
        else "position-specific aerosol/TEM characterization"
    )
    details: list[str] = []
    cnt_type = "CNT-containing aerosol"
    morphology = "not_reported_for_this_position"
    length = "not_reported_for_this_position"
    wall = "not_reported_for_this_position"

    if position == 250:
        cnt_type = "no CNT observed on TEM grid; catalyst nanoparticles only"
        morphology = "isolated and agglomerated catalyst nanoparticles"
        details.append("Only catalyst nanoparticles observed by TEM.")
    if position >= 300:
        details.append("CPMA spectra peak between approximately 0.1 and 0.2 fg.")
    if position in {300, 400, 500}:
        cnt_type = "few-wall CNT-containing aerosol"
        morphology = (
            "isolated CNTs, linear bundles and branched CNT clusters with "
            "adhered catalyst nanoparticles"
        )
        wall = "typically 2-4 walls; CNTs longer than 8.5 um had 3 walls"
        details.append(
            "Mean calculated CNT-bundle density 1170 kg/m3; CNT inner diameter "
            "0.5-5.5 nm and outer diameter 1-7 nm across the three TEM positions."
        )
    if position == 300:
        length = (
            "0.1-54 um overall; number median approximately 3.5 um at X=300 mm; "
            "longest measured CNT exceeded 50 um"
        )
        details.extend(
            [
                "CNTs longer than 25 um account for more than half the CNT mass at X=300 mm.",
                "Between X=280 and 300 mm, aerosol mass increased 57% over about 0.18 s.",
                "Lower-bound mass-weighted CNT growth-rate mean and mode approximately 250 um/s.",
            ]
        )
    elif position == 500:
        length = (
            "number median approximately 0.95 um; distribution shorter than X=300 mm"
        )
        details.append(
            "Median CNT length decreased by more than factor 3 from X=300 mm."
        )
    elif position == 400:
        length = (
            "individual CNT paths measured within bundles/clusters; no median reported"
        )
    if position == 330:
        details.append(
            "The 320-330 mm particle-production increase was 8-76% below "
            "the preceding 310-320 mm interval for masses 0.05-0.5 fg."
        )
    if rate:
        details.append(
            f"Figure 6b: normalized mass production approximately {rate[0]} "
            f"at approximately {rate[1]} K."
        )

    return yield_row(
        run_id,
        primary_yield_metric=(
            "normalized_axial_mass_production_rate"
            if rate
            else "position_specific_aerosol_and_TEM_result"
        ),
        yield_original=primary,
        yield_definition_original=(
            "mass spectra integrated at each X; mass change divided by calculated "
            "inter-position residence time and normalized by the maximum"
            if rate
            else "reported aerosol/TEM observation at the stated axial position"
        ),
        yield_calculation_method=(
            "figure_digitized_normalized_rate"
            if rate
            else "direct CPMA/CPC/electrometer and TEM characterization"
        ),
        yield_value_standardized=rate[0] if rate else "",
        yield_unit_standardized="dimensionless_ratio" if rate else "",
        yield_standardization_note=(
            "Figure 6b value is approximate and normalized; it is not an absolute mass yield."
            if rate
            else "No absolute mass yield assigned."
        ),
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=" ".join(details) or primary,
        CNT_type_reported=cnt_type,
        CNT_type_confirmed=(
            "few-wall CNT by TEM"
            if position in {300, 400, 500}
            else "not_separately_confirmed_for_this_position"
        ),
        product_mixture_summary=(
            "CNTs/CNT bundles/CNT clusters plus adhered Fe nanoparticles"
            if position in {300, 400, 500}
            else "position-specific aerosol particles"
        ),
        CNT_type_evidence="TEM and aerosol mass analysis",
        SWCNT_or_few_wall_evidence_summary=wall,
        RBM_peak_reported="not_reported",
        outer_diameter_mean_nm="not_reported_as_single_mean",
        outer_diameter_range_nm=("1-7" if position in {300, 400, 500} else ""),
        inner_diameter_mean_nm="not_reported_as_single_mean",
        wall_number_summary=wall,
        length_summary=length,
        morphology=morphology,
        alignment_or_array="aerosolized isolated, bundled or clustered CNTs",
        Raman_ratio_type="not_reported",
        Raman_ratio_value="not_reported",
        Raman_laser_wavelength_nm="not_reported",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis="not_reported",
        residue_summary="adhered Fe-containing catalyst nanoparticles",
        amorphous_carbon_level="not_reported",
        BET_surface_area_product_m2_g="",
        characterization_methods="CPMA; CPC; electrometer; TEM; CFD residence-time model",
        post_treatment_or_purification="none",
        purification_condition="not_applicable",
        application_property_summary="in-situ FCCVD growth-kinetics characterization",
    )


def cost(run_id: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="lab_continuous_aerosol_reactor",
        scale_level_claimed="relevant_to_continuous_FCCVD_scale_up",
        scale_evidence_summary=(
            "Continuous precursor delivery and centreline aerosol extraction were "
            "demonstrated in a 700 mm, 40 mm-ID reactor."
        ),
        reactor_capacity_or_throughput="0.8 slpm injected growth flow; CNT mass throughput not reported",
        continuous_operation_time_h="not_reported_for_axial_measurement_series",
        catalyst_lifetime_or_reuse="continuously generated from ferrocene vapor",
        catalyst_reuse_cycles="not_applicable_floating_catalyst",
        batch_stability="replicate and long-duration stability not reported",
        scale_up_issue=(
            "Control catalyst size/sulfur distribution, CNT nucleation, axial "
            "temperature and agglomeration while avoiding probe/filter artifacts."
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="No monetary cost or absolute CNT production mass reported.",
        cost_driver_summary=(
            "high-temperature furnace, H2, methane, ferrocene, thiophene, "
            "N2 quench and aerosol instrumentation"
        ),
        safety_risk=(
            "flammable H2/methane, toxic ferrocene/thiophene, high temperature "
            "and respirable CNT/metal aerosol"
        ),
        emission_or_waste="unquantified CNT/iron aerosol and combustible reactor exhaust",
        industrial_readiness_assessment=(
            "high-value mechanistic in-situ study; production economics remain unquantified"
        ),
        reproduction_value="high for reactor and sampling method; medium for exact precursor vapor concentration",
        reproduction_priority="high",
        recommended_next_action=(
            "Report absolute CNT mass flow, methane conversion, pressure, vapor "
            "concentrations, replicates and long-duration material balance."
        ),
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
                "Five-condition coupled precursor/aerogel boundary screen; "
                "fifteen axial FCCVD sampling positions; CPMA particle spectra, "
                "normalized mass-production profile, catalyst-size evolution, "
                "CNT diameter/wall/length distributions, agglomeration and growth rate."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_fulltext_pdf_with_supporting_information"
    master["notes"] += f" Supporting information retained at {SI_REF}."

    screen_ids: list[str] = []
    for item in AEROGEL_SCREEN:
        run_id = f"{SOURCE_ID}_{item['code']}"
        screen_ids.append(run_id)
        summary = (
            f"Coupled precursor screen: CH4 {item['methane']}%, ferrocene "
            f"{item['ferrocene']}%, thiophene {item['thiophene']}% relative "
            f"to H2 for 15 min; aerogel {item['aerogel']}, filter {item['filter']}."
        )
        tables["source_run"].append(
            run_row(SOURCE_ID, item["code"], summary, summary, "medium")
        )
        tables["catalyst_system"].append(
            catalyst(
                run_id,
                methane_fraction=item["methane"],
                ferrocene_fraction=item["ferrocene"],
                thiophene_fraction=item["thiophene"],
            )
        )
        tables["reactor_process_gas"].extend(
            [
                precondition_stage(run_id),
                growth_stage(
                    run_id,
                    methane_fraction=item["methane"],
                    ferrocene_fraction=item["ferrocene"],
                    thiophene_fraction=item["thiophene"],
                    duration="15",
                ),
            ]
        )
        tables["yield_quality"].append(aerogel_product(run_id, item))
        tables["cost_scale_review"].append(cost(run_id))

        screen_text = (
            "Figure S1 visually transcribed coupled precursor condition: "
            f"methane {item['methane']}%, ferrocene {item['ferrocene']}%, "
            f"thiophene {item['thiophene']}% relative to H2; 15 min injection; "
            f"aerogel {item['aerogel']}; downstream filter {item['filter']}."
        )
        for suffix, table, record, fields in [
            ("RUN", "source_run", run_id, "record_level"),
            ("CATALYST", "catalyst_system", f"{run_id}_CAT", "record_level"),
            ("PRODUCT", "yield_quality", f"{run_id}_PROD", "record_level"),
        ]:
            add_pdf_evidence(
                tables,
                store,
                run_id,
                suffix,
                table,
                record,
                fields,
                "SPAN_24E61C29F2904B549D2B",
                3,
                screen_text,
                "Supporting-information aerogel boundary screen.",
                object_ref=SI_REF,
                value_status="figure_digitized_approximate",
                confidence="medium",
            )
        for order, span in [
            (1, "SPAN_FAC9B0EEF1BEB9CFFC24"),
            (2, "SPAN_341D53F98DB9C8800F1F"),
        ]:
            add_pdf_evidence(
                tables,
                store,
                run_id,
                f"PROCESS_{order}",
                "reactor_process_gas",
                f"{run_id}_S{order:02d}",
                "record_level",
                span,
                11,
                COMMON_RECIPE + " " + screen_text,
                "Shared preconditioning and 15 min screening process.",
                value_status=(
                    "figure_digitized_approximate" if order == 2 else "reported"
                ),
                confidence="medium" if order == 2 else "high",
            )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            "record_level",
            "SPAN_341D53F98DB9C8800F1F",
            11,
            COMMON_RECIPE,
            "Process-intensity facts and unreported economic metrics.",
            value_status="review_assessment",
        )

    axial_ids: dict[int, str] = {}
    for position in AXIAL_POSITIONS:
        code = f"AXIAL_X{position:03d}"
        run_id = f"{SOURCE_ID}_{code}"
        axial_ids[position] = run_id
        summary = f"Shared low-precursor FCCVD condition sampled at X={position} mm."
        if position in MASS_RATE:
            rate, temp = MASS_RATE[position]
            summary += (
                f" Figure 6b normalized mass-production rate approximately "
                f"{rate} at approximately {temp} K."
            )
        tables["source_run"].append(
            run_row(SOURCE_ID, code, f"axial sample X={position} mm", summary, "high")
        )
        tables["catalyst_system"].append(catalyst(run_id, position=position))
        tables["reactor_process_gas"].extend(
            [
                precondition_stage(run_id),
                growth_stage(
                    run_id,
                    methane_fraction="5.3",
                    ferrocene_fraction="0.0014",
                    thiophene_fraction="0.038",
                    duration="not_reported_for_axial_series",
                    position=position,
                ),
            ]
        )
        tables["yield_quality"].append(axial_product(run_id, position))
        tables["cost_scale_review"].append(cost(run_id))

        add_pdf_evidence(
            tables,
            store,
            run_id,
            "RUN",
            "source_run",
            run_id,
            "record_level",
            "SPAN_C3D60BCAEEBEC384E67F",
            3,
            COMMON_RECIPE + f" Axial sample position X={position} mm.",
            "Axial sampling record under the shared low-precursor condition.",
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "CATALYST",
            "catalyst_system",
            f"{run_id}_CAT",
            "record_level",
            "SPAN_BE310AC99B8C5E4BDBD6",
            5,
            COMMON_RECIPE
            + (
                " Adopted low-precursor relative-to-H2 mole fractions: "
                "methane approximately 5.3%, ferrocene approximately "
                "0.0014%, thiophene approximately 0.038%."
            )
            + (
                f" Catalyst-size population and CNT-tip-size overlap evaluated "
                f"at X={position} mm where reported."
            ),
            "Floating catalyst recipe and axial catalyst evolution.",
        )
        for order, span in [
            (1, "SPAN_FAC9B0EEF1BEB9CFFC24"),
            (2, "SPAN_341D53F98DB9C8800F1F"),
        ]:
            local_figure = ""
            if order == 2 and position in MASS_RATE:
                rate, temperature = MASS_RATE[position]
                local_figure = (
                    f" Figure 6b visual transcription at X={position} mm: "
                    f"temperature approximately {temperature} K and normalized "
                    f"mass-production rate approximately {rate}."
                )
            add_pdf_evidence(
                tables,
                store,
                run_id,
                f"PROCESS_{order}",
                "reactor_process_gas",
                f"{run_id}_S{order:02d}",
                "record_level",
                span,
                11,
                COMMON_RECIPE
                + " "
                + SAMPLING_RECIPE
                + (
                    " Adopted low-precursor relative-to-H2 mole fractions: "
                    "methane approximately 5.3%, ferrocene approximately "
                    "0.0014%, thiophene approximately 0.038%."
                )
                + f" Axial sample position X={position} mm."
                + local_figure,
                "Shared preconditioning, FCCVD feed and aerosol sampling method.",
            )

        product_span = "SPAN_CDD2A145DB4A6987B710"
        product_text = (
            f"Axial sample X={position} mm. "
            + tables["yield_quality"][-1]["secondary_result_summary"]
        )
        status = "reported"
        confidence = "high"
        if position in MASS_RATE:
            product_span = "SPAN_0A04C643185EB905C1A6"
            status = "figure_digitized_approximate"
            confidence = "medium"
        if position in {300, 400, 500}:
            product_span = (
                "SPAN_EB1A1FAF5494DD4B0D51"
                if position in {300, 500}
                else "SPAN_BE310AC99B8C5E4BDBD6"
            )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "PRODUCT",
            "yield_quality",
            f"{run_id}_PROD",
            "record_level",
            product_span,
            8 if position in {300, 400, 500} else 9,
            product_text,
            "Position-specific aerosol, mass-production or TEM result.",
            value_status=status,
            confidence=confidence,
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            "record_level",
            "SPAN_341D53F98DB9C8800F1F",
            11,
            COMMON_RECIPE,
            "Process-intensity facts and industrial data gaps.",
            value_status="review_assessment",
        )

    reference_id = axial_ids[300]
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_NORMALIZED_YIELD_001",
                SOURCE_ID,
                reference_id,
                "definition_boundary",
                "yield_quality",
                f"{reference_id}_PROD",
                "yield_value_standardized",
                (
                    "Figure 6b reports Mdot/MdotMax, not absolute CNT mass, "
                    "space-time yield, carbon conversion or catalyst productivity."
                ),
                f"EVD_{reference_id}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FIGURE_DIGITIZATION_001",
                SOURCE_ID,
                axial_ids[275],
                "figure_digitization",
                "yield_quality",
                f"{axial_ids[275]}_PROD",
                "yield_original",
                (
                    "The eleven normalized mass-production rates and local "
                    "temperatures were visually digitized from Figure 6b."
                ),
                ";".join(f"EVD_{axial_ids[x]}_PRODUCT" for x in MASS_RATE),
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_AXIAL_MAPPING_001",
                SOURCE_ID,
                reference_id,
                "shared_parent_condition",
                "source_run",
                reference_id,
                "run_summary",
                (
                    "The fifteen axial records are measurements from one shared "
                    "low-precursor FCCVD recipe, not fifteen independent synthesis recipes."
                ),
                f"EVD_{reference_id}_RUN",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SCREEN_CONFOUNDING_001",
                SOURCE_ID,
                screen_ids[0],
                "coupled_variable_screen",
                "reactor_process_gas",
                f"{screen_ids[0]}_S02",
                "gas_composition_summary",
                (
                    "Methane, ferrocene and thiophene fractions were reduced "
                    "together in Figure S1; the aerogel transition cannot be "
                    "attributed to methane alone."
                ),
                f"EVD_{screen_ids[0]}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SCREEN_DIGITIZATION_001",
                SOURCE_ID,
                screen_ids[0],
                "figure_digitization",
                "catalyst_system",
                f"{screen_ids[0]}_CAT",
                "metal_ratio_original",
                (
                    "Figure S1 precursor mole fractions are visual "
                    "transcriptions and are retained as approximate values."
                ),
                ";".join(f"EVD_{run_id}_CATALYST" for run_id in screen_ids),
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_METHANE_FLOW_001",
                SOURCE_ID,
                reference_id,
                "critical_data_gap",
                "reactor_process_gas",
                f"{reference_id}_S02",
                "carbon_source_flow_original",
                (
                    "Methane mole fraction and 0.8 slpm total feed are given, "
                    "but an unambiguous separate methane volumetric flow is not reported."
                ),
                f"EVD_{reference_id}_PROCESS_2",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_DURATION_001",
                SOURCE_ID,
                reference_id,
                "critical_data_gap",
                "reactor_process_gas",
                f"{reference_id}_S02",
                "holding_time_min",
                (
                    "The 15 min duration applies to the aerogel-boundary screen; "
                    "the duration of the main axial measurement campaign is not reported."
                ),
                f"EVD_{reference_id}_PROCESS_2",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_LENGTH_LOWER_BOUND_001",
                SOURCE_ID,
                reference_id,
                "measurement_lower_bound",
                "yield_quality",
                f"{reference_id}_PROD",
                "length_summary",
                (
                    "Long CNT paths become ambiguous inside clusters; the reported "
                    "maximum length and derived growth rate are conservative lower bounds."
                ),
                f"EVD_{reference_id}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CPC_LARGE_PARTICLE_001",
                SOURCE_ID,
                axial_ids[500],
                "instrument_limit",
                "yield_quality",
                f"{axial_ids[500]}_PROD",
                "secondary_result_summary",
                (
                    "For masses much greater than 1 fg, CPC counts can greatly "
                    "overstate true high-aspect-ratio CNT-particle number concentration."
                ),
                f"EVD_{axial_ids[500]}_PRODUCT",
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
