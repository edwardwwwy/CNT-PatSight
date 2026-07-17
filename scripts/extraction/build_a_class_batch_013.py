#!/usr/bin/env python3
"""Build the thirteenth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 13
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_427378A0096D943B"


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
            value_status=value_status,
        )
    )


def append_r2r_pdf_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
) -> None:
    evidence = evidence_row(
        store,
        SOURCE_ID,
        f"EVD_{run_id}_R2R_PDF",
        run_id,
        "reactor_process_gas",
        f"{run_id}_S01",
        "record_level",
        "SPAN_FC98756598372D52FE31",
        "Industrial roll-to-roll condition visually checked in the PDF.",
    )
    evidence.update(
        {
            "evidence_type": "pdf_text_and_figure_annotation",
            "source_section": "Section 3.3 and Figure 7",
            "source_locator": "PDF page 15",
            "source_object_ref": (
                f"data/raw/fulltext/pdf/{SOURCE_ID}_f8e072dd7343.pdf#page=15"
            ),
            "evidence_text": (
                "Continuous 30 cm-wide roll-to-roll pilot line; 615 C; "
                "60 min growth; VACNT height above 200 micrometers; "
                "Figure 7 caption reports rolling speed 1 m/h."
            ),
            "evidence_summary": (
                "PDF page 15 confirms the industrial pilot dimensions, "
                "temperature, duration, height and rolling speed."
            ),
            "notes": "Locally stored PDF was visually inspected.",
        }
    )
    tables["evidence_index"].append(evidence)
    cost_evidence = evidence.copy()
    cost_evidence.update(
        {
            "evidence_id": f"EVD_{run_id}_R2R_COST_PDF",
            "target_table": "cost_scale_review",
            "target_record_id": run_id,
            "target_fields": ("scale_evidence_summary;reactor_capacity_or_throughput"),
            "evidence_summary": (
                "PDF page 15 confirms the continuous pilot-line width and "
                "rolling throughput used in the scale review."
            ),
        }
    )
    tables["evidence_index"].append(cost_evidence)
    yield_evidence = evidence.copy()
    yield_evidence.update(
        {
            "evidence_id": f"EVD_{run_id}_R2R_YIELD_PDF",
            "target_table": "yield_quality",
            "target_record_id": f"{run_id}_PROD",
            "target_fields": "yield_original;length_summary",
            "evidence_summary": (
                "PDF page 15 confirms that the industrial pilot produced a "
                "VACNT carpet above 200 micrometers."
            ),
        }
    )
    tables["evidence_index"].append(yield_evidence)


def append_baseline_scan_pdf_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    *,
    inferred_from_same_conditions: bool = False,
) -> None:
    evidence = evidence_row(
        store,
        SOURCE_ID,
        f"EVD_{run_id}_580C_20MIN_PDF",
        run_id,
        "reactor_process_gas",
        f"{run_id}_S01",
        "temperature_setpoint_C;holding_time_min",
        "SPAN_011736A753EE93D6A9B4",
        "Baseline/Fe-C scan temperature and duration checked in the PDF.",
        value_status=("inferred" if inferred_from_same_conditions else "reported"),
    )
    condition_text = (
        "The acetylene baseline kept all other conditions similar to the "
        "preceding 580 C, 20 min toluene/ferrocene baseline."
        if inferred_from_same_conditions
        else (
            "The baseline text and Figure 1 caption report synthesis at "
            "580 C for 20 min."
        )
    )
    evidence.update(
        {
            "evidence_type": (
                "pdf_text_and_explicit_same-condition_inference"
                if inferred_from_same_conditions
                else "pdf_text_and_figure_caption"
            ),
            "source_section": "Section 3.1.1 and Figure 1",
            "source_locator": "PDF page 5",
            "source_object_ref": (
                f"data/raw/fulltext/pdf/{SOURCE_ID}_f8e072dd7343.pdf#page=5"
            ),
            "evidence_text": condition_text,
            "evidence_summary": ("PDF page 5 grounds the 580 C and 20 min condition."),
            "notes": "Locally stored PDF was visually inspected.",
        }
    )
    tables["evidence_index"].append(evidence)


def append_optimized_pdf_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
) -> None:
    evidence = evidence_row(
        store,
        SOURCE_ID,
        f"EVD_{run_id}_OPTIMIZED_PDF",
        run_id,
        "yield_quality",
        f"{run_id}_PROD",
        "yield_original;length_summary;TGA_carbon_content_wt_percent",
        "SPAN_02592EE5B003FE69CB8E",
        "Optimized carpet thickness and purity visually checked in the PDF.",
    )
    evidence.update(
        {
            "evidence_type": "pdf_text_and_figure_annotation",
            "source_section": "Sections 3.1.1-3.1.2 and Figure 2",
            "source_locator": "PDF page 6",
            "source_object_ref": (
                f"data/raw/fulltext/pdf/{SOURCE_ID}_f8e072dd7343.pdf#page=6"
            ),
            "evidence_text": (
                "At 580 C and 20 min the VACNT carpet reaches 50 "
                "micrometers. At 615 C it exceeds 80 micrometers with a "
                "growth rate of 4 micrometers/min. Optimized CNT carbon "
                "purity is 99.4% by TGA under air."
            ),
            "evidence_summary": (
                "PDF page 6 confirms the optimized carpet heights, the "
                "615 C growth rate and 99.4% TGA carbon purity."
            ),
            "notes": "Locally stored PDF was visually inspected.",
        }
    )
    tables["evidence_index"].append(evidence)


def catalyst(run_id: str) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label=(
            "in-situ Fe nanoparticles from ferrocene aerosol on aluminium foil"
        ),
        active_metals="Fe",
        support_material="commercial aluminium foil",
        promoter="not_applicable",
        metal_ratio_original=(
            "Fe/C mass ratio in precursor varied; run-specific category is "
            "recorded in the process note where reported"
        ),
        metal_ratio_standardized="not_applicable",
        precursor_summary="ferrocene dissolved in toluene and aerosol-injected",
        preparation_method="floating_catalyst_aerosol_injection",
        preparation_modifier=(
            "Al foil acetone-cleaned; no other substrate pretreatment"
        ),
        preparation_detail=(
            "Ferrocene/toluene aerosol carried by Ar/H2; Fe nanoparticles "
            "nucleate in the gas phase and deposit at the Al/VACNT interface."
        ),
        drying_condition="not_applicable",
        calcination_condition="not_applicable",
        reduction_condition="H2 present in carrier gas",
        activation_condition="in-situ ferrocene decomposition during CCVD",
        post_preparation_condition="continuously refreshed floating Fe catalyst",
        catalyst_particle_size_mean_nm="not_reported",
        catalyst_particle_size_range_nm="not_reported",
        catalyst_particle_size_qualifier="not mapped from CNT dimensions",
        phase_or_state_summary="iron-based nanoparticles",
        dispersion_summary="gas-phase nucleation and delivery to Al surface",
        deactivation_summary=(
            "growth saturation attributed to disorganized-carbon-induced "
            "catalyst deactivation at long duration"
        ),
    )


def process(
    run_id: str,
    stage_type: str,
    temperature: str,
    duration: str,
    carbon: str,
    note: str,
    scale: str = "lab_batch",
    use_study_ranges: bool = False,
) -> dict[str, str]:
    if use_study_ranges:
        reducing_flow = "10-20% concentration range in optimized study"
        total_flow = "100-333 sccm study-wide range"
        composition = (
            "C2H2 and H2 each studied in a 10-20% concentration range; "
            "Fe/C ratio kept below 2 wt%."
        )
    else:
        reducing_flow = "not_reported"
        total_flow = "not_reported"
        composition = (
            "Ar/H2 carried the ferrocene/toluene aerosol and acetylene was "
            "added; exact run-level fractions were not reported."
        )
    return process_row(
        run_id,
        1,
        stage_type,
        reactor_type=(
            "continuous roll-to-roll aerosol-assisted CCVD pilot line"
            if scale == "industrial_pilot"
            else "aerosol-assisted atmospheric-pressure CCVD furnace"
        ),
        scale_level=scale,
        reactor_material="not_reported",
        reactor_size_summary=(
            "30 cm-wide continuous foil path"
            if scale == "industrial_pilot"
            else "1 cm Al discs in reactor isothermal zone"
        ),
        reactor_setup_summary=(
            "Ferrocene/toluene aerosol injected and carried by Ar/H2; "
            "acetylene added as reactive carbon precursor."
        ),
        temperature_setpoint_C=temperature,
        temperature_program_summary="isothermal low-temperature CCVD",
        holding_time_min=duration,
        pressure_original="atmospheric",
        pressure_kPa="101.325",
        carbon_source=carbon,
        carbon_source_flow_original="not individually reported",
        reducing_gas="H2",
        reducing_gas_flow_original=reducing_flow,
        inert_gas="Ar",
        inert_gas_flow_original="not individually reported",
        cofeed_or_reactive_gas="ferrocene/toluene aerosol",
        cofeed_flow_original="not individually reported",
        total_flow_original=total_flow,
        gas_composition_summary=composition,
        process_note=note,
    )


def qualitative_yield(
    run_id: str,
    outcome: str,
    detail: str,
    morphology: str,
    alignment: str,
    confirmed_type: str = "MWCNTs",
) -> dict[str, str]:
    return yield_row(
        run_id,
        primary_yield_metric="qualitative_VACNT_growth_outcome",
        yield_original=outcome,
        yield_definition_original="SEM-observed carpet formation and morphology",
        yield_calculation_method="qualitative microscopy observation",
        yield_value_standardized="",
        yield_unit_standardized="not_applicable",
        secondary_result_summary=detail,
        CNT_type_reported="carbon nanotubes",
        CNT_type_confirmed=confirmed_type,
        product_mixture_summary=detail,
        CNT_type_evidence="TEM/HRTEM and reported multiwall structure.",
        wall_number_summary="multi-walled; exact count not mapped for this run",
        length_summary=detail,
        morphology=morphology,
        alignment_or_array=alignment,
        Raman_ratio_type="not_reported",
        Raman_ratio_value="not_reported",
        purity_basis="not_reported",
        residue_summary="not_reported",
        amorphous_carbon_level="not_reported",
        characterization_methods="SEM; TEM/HRTEM where applicable",
        post_treatment_or_purification="none reported",
        purification_condition="not_applicable",
    )


def optimized_yield(
    run_id: str,
    temperature: int,
    height: str,
    growth_rate: str,
    outer: str,
    inner: str,
    id_i2d: str,
    density: str,
) -> dict[str, str]:
    return yield_row(
        run_id,
        primary_yield_metric="VACNT_carpet_growth_rate",
        yield_original=(
            f"{growth_rate} micrometers/min mean growth rate; "
            f"approximately {height} micrometers carpet height"
        ),
        yield_definition_original="carpet thickness divided by synthesis duration",
        yield_calculation_method="SEM cross-section thickness/time",
        yield_value_standardized=growth_rate,
        yield_unit_standardized="micrometers/min",
        secondary_result_summary=(
            f"At {temperature} C: mean outer diameter {outer} nm; "
            f"inner diameter {inner} nm; density {density}; "
            f"Raman ID/I2D {id_i2d}."
        ),
        CNT_type_reported="vertically aligned carbon nanotubes",
        CNT_type_confirmed="MWCNTs",
        product_mixture_summary="clean dense VACNT carpet with few by-products",
        CNT_type_evidence="HRTEM showed 7-9 graphene walls.",
        outer_diameter_mean_nm=outer,
        inner_diameter_mean_nm=inner,
        wall_number_summary="7-9 graphene walls",
        length_summary=f"approximately {height} micrometers carpet height",
        morphology="clean narrow-diameter MWCNTs",
        alignment_or_array="well-aligned VACNT forest",
        Raman_ratio_type="ID/IG; supplementary ID/I2D quality comparison",
        Raman_ratio_value="approximately 1.3",
        Raman_laser_wavelength_nm="532",
        TGA_carbon_content_wt_percent="99.4",
        purity_basis="air TGA carbon content",
        residue_summary="very few nanoparticles or encapsulated Fe nanowires",
        amorphous_carbon_level="almost none observed by HRTEM",
        characterization_methods="SEM; TEM; HRTEM; Raman; TGA",
        post_treatment_or_purification="none reported",
        purification_condition="not_applicable",
    )


def table1_yield(
    run_id: str,
    sample: dict[str, str],
) -> dict[str, str]:
    return yield_row(
        run_id,
        primary_yield_metric="reported_VACNT_sample_mass",
        yield_original=f"{sample['mass']} mg VACNT sample mass",
        yield_definition_original="mass listed for VACNT/Al electrode sample",
        yield_calculation_method="reported sample mass; method not repeated",
        yield_value_standardized="",
        yield_unit_standardized="not_applicable",
        secondary_result_summary=(
            f"Height {sample['height']} micrometers; mean diameter "
            f"{sample['diameter']} nm; density {sample['density']} x10^10 "
            f"CNT/cm2; developed surface {sample['surface']} m2."
        ),
        CNT_type_reported="vertically aligned carbon nanotubes",
        CNT_type_confirmed="MWCNTs",
        product_mixture_summary="VACNT carpet on aluminium",
        CNT_type_evidence="Produced under the optimized MWCNT forest process.",
        outer_diameter_mean_nm=sample["diameter"],
        wall_number_summary="multi-walled; run-specific count not reported",
        length_summary=f"{sample['height']} micrometers carpet height",
        morphology="dense VACNT carpet",
        alignment_or_array="vertically aligned forest",
        Raman_ratio_type="not separately reported for P sample",
        Raman_ratio_value="not_reported",
        purity_basis="not separately reported for P sample",
        residue_summary="not_reported",
        amorphous_carbon_level="not separately reported",
        characterization_methods="SEM; electrochemical characterization",
        post_treatment_or_purification="none reported",
        purification_condition="not_applicable",
        application_property_summary=(
            f"Gravimetric capacitance {sample['cm']} F/g; electrode "
            f"capacitance {sample['cap']} mF; developed surface "
            f"{sample['surface']} m2."
        ),
    )


def model_yield(
    run_id: str,
    hmax: str,
    rate: str,
    lifetime: str,
) -> dict[str, str]:
    return yield_row(
        run_id,
        primary_yield_metric="exponential_model_initial_growth_rate",
        yield_original=(
            f"fitted hmax {hmax} micrometers; initial growth rate "
            f"{rate} micrometers/min; catalyst lifetime {lifetime} min"
        ),
        yield_definition_original=(
            "Exponential self-deactivation model fit to VACNT height-time data"
        ),
        yield_calculation_method="model fit to experimental synthesis series",
        yield_value_standardized=rate,
        yield_unit_standardized="micrometers/min",
        yield_standardization_note="Thesis-style model result retained as reported.",
        secondary_result_summary=(
            f"Maximum fitted height {hmax} micrometers; fitted catalyst "
            f"lifetime {lifetime} min."
        ),
        CNT_type_reported="vertically aligned carbon nanotubes",
        CNT_type_confirmed="MWCNTs",
        product_mixture_summary="VACNT forest series",
        CNT_type_evidence="Common process characterization.",
        wall_number_summary="7-9 for optimized process; not separately fit",
        length_summary=f"fitted maximum height {hmax} micrometers",
        morphology="VACNT carpet",
        alignment_or_array="vertically aligned forest",
        characterization_methods="SEM height-time series; exponential modeling",
        post_treatment_or_purification="none reported",
        purification_condition="not_applicable",
    )


def cost(run_id: str, scale: str = "lab_batch") -> dict[str, str]:
    pilot = scale == "industrial_pilot"
    return cost_row(
        run_id,
        scale_level_demonstrated=scale,
        scale_level_claimed=(
            "industrial_roll_to_roll" if pilot else "roll_to_roll_compatible"
        ),
        scale_evidence_summary=(
            "Continuous 30 cm-wide pilot roll-to-roll line at 1 m/h."
            if pilot
            else "Atmospheric single-step process on commercial Al foil."
        ),
        reactor_capacity_or_throughput=(
            "30 cm foil width; 1 m/h rolling speed"
            if pilot
            else "1 cm Al-disc laboratory substrates"
        ),
        continuous_operation_time_h="not_reported",
        catalyst_lifetime_or_reuse=(
            "Fitted lifetime varies with temperature/injection sequence; "
            "run-specific value in yield table where available."
        ),
        batch_stability="long-duration growth shows height saturation",
        scale_up_issue=(
            "Control Fe/C ratio, suppress disorganized carbon, maintain "
            "precursor injection and catalyst refreshment across foil width."
        ),
        cost_driver_summary=(
            "Ferrocene/toluene aerosol, acetylene, H2/Ar, furnace duty, "
            "commercial Al foil and roll-to-roll gas distribution."
        ),
        safety_risk=(
            "Acetylene and hydrogen at elevated temperature; ferrocene/toluene "
            "aerosol; CNT nanoparticle exposure."
        ),
        emission_or_waste=(
            "Hydrocarbon/solvent exhaust and disorganized-carbon deposits; "
            "quantities not reported."
        ),
        industrial_readiness_assessment=(
            "Pilot roll-to-roll transfer demonstrated."
            if pilot
            else "Laboratory process with demonstrated pilot transfer."
        ),
        reproduction_value="high after resolving exact gas recipes",
        reproduction_priority="high",
        recommended_next_action=(
            "Obtain supplementary exact flow/injection recipes and replicate "
            "mass/energy balances at pilot scale."
        ),
    )


TABLE1 = [
    {
        "code": "P1",
        "height": "99",
        "mass": "0.42",
        "diameter": "8.1",
        "density": "5.9",
        "surface": "0.117",
        "cm": "47",
        "cap": "19.7",
    },
    {
        "code": "P2",
        "height": "96",
        "mass": "0.45",
        "diameter": "8.1",
        "density": "6.6",
        "surface": "0.126",
        "cm": "32",
        "cap": "14.4",
    },
    {
        "code": "P3",
        "height": "49",
        "mass": "0.57",
        "diameter": "8.3",
        "density": "15.7",
        "surface": "0.158",
        "cm": "47",
        "cap": "26.8",
    },
    {
        "code": "P4",
        "height": "65",
        "mass": "0.81",
        "diameter": "10.6",
        "density": "10.6",
        "surface": "0.181",
        "cm": "35",
        "cap": "28.4",
    },
    {
        "code": "P5",
        "height": "53.5",
        "mass": "0.79",
        "diameter": "8.7",
        "density": "18.2",
        "surface": "0.209",
        "cm": "38",
        "cap": "30.0",
    },
    {
        "code": "P6",
        "height": "56",
        "mass": "0.84",
        "diameter": "8.7",
        "density": "18.5",
        "surface": "0.223",
        "cm": "40",
        "cap": "33.6",
    },
    {
        "code": "P7",
        "height": "125",
        "mass": "1.28",
        "diameter": "11.1",
        "density": "7.7",
        "surface": "0.263",
        "cm": "30",
        "cap": "38.4",
    },
]

MODELS = [
    {
        "code": "M580S",
        "temperature": "580",
        "label": "single injection",
        "hmax": "65",
        "rate": "3.8",
        "lifetime": "17",
    },
    {
        "code": "M615S",
        "temperature": "615",
        "label": "single injection",
        "hmax": "121",
        "rate": "8.3",
        "lifetime": "15",
    },
    {
        "code": "M580Q",
        "temperature": "580",
        "label": "sequential injection",
        "hmax": "100",
        "rate": "3.0",
        "lifetime": "33",
    },
    {
        "code": "M615Q",
        "temperature": "615",
        "label": "sequential injection",
        "hmax": "215",
        "rate": "6.0",
        "lifetime": "36",
    },
]


def add_run(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    code: str,
    label: str,
    summary: str,
    process_row_value: dict[str, str],
    yield_row_value: dict[str, str],
    process_span: str,
    yield_span: str,
    *,
    data_type: str = "experimental_run",
    scale: str = "lab_batch",
    yield_status: str = "reported",
) -> None:
    run_id = f"{SOURCE_ID}_{code}"
    source_run = run_row(SOURCE_ID, code, label, summary, "medium")
    source_run["data_type"] = data_type
    tables["source_run"].append(source_run)
    tables["catalyst_system"].append(catalyst(run_id))
    tables["reactor_process_gas"].append(process_row_value)
    tables["yield_quality"].append(yield_row_value)
    tables["cost_scale_review"].append(cost(run_id, scale))
    append_evidence(
        tables,
        store,
        run_id,
        "CATALYST",
        "catalyst_system",
        f"{run_id}_CAT",
        "record_level",
        "SPAN_AA5CD464CF654455999A",
        "Common ferrocene/toluene floating-catalyst method and Al substrate.",
    )
    append_evidence(
        tables,
        store,
        run_id,
        "PROCESS",
        "reactor_process_gas",
        f"{run_id}_S01",
        "record_level",
        process_span,
        f"Process condition for {label}.",
    )
    append_evidence(
        tables,
        store,
        run_id,
        "YIELD",
        "yield_quality",
        f"{run_id}_PROD",
        "record_level",
        yield_span,
        f"VACNT outcome for {label}.",
        yield_status,
    )
    append_evidence(
        tables,
        store,
        run_id,
        "COST_REVIEW",
        "cost_scale_review",
        run_id,
        "record_level",
        (
            "SPAN_FC98756598372D52FE31"
            if scale == "industrial_pilot"
            else "SPAN_AA5CD464CF654455999A"
        ),
        "Scale/cost/safety review from the reported apparatus.",
        "review_assessment",
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
                "Atmospheric aerosol-assisted floating-catalyst CCVD on Al: "
                "baseline/Fe-C scans, optimized 580/615 C products, P1-P7 "
                "electrode samples, fitted single/sequential injection series, "
                "reduced-acetylene sequence and industrial R2R demonstration."
            ),
        )
    )
    tables["source_master"][0]["local_file_path"] = (
        f"data/interim/parsed_text/{SOURCE_ID}/full_text.txt"
    )
    tables["source_master"][0]["notes"] += (
        " PDF page 15 was visually checked for the 30 cm-wide pilot-line "
        "condition and Figure 7 rolling speed."
    )

    baselines = [
        (
            "B01",
            "toluene/ferrocene baseline",
            "580",
            "20",
            "toluene",
            "Only a thin 1 micrometer carpet of entangled CNTs.",
            "1 micrometer entangled CNT carpet",
            "entangled nanotubes",
            "not vertically aligned",
        ),
        (
            "B02",
            "initial acetylene baseline",
            "580",
            "20",
            "C2H2",
            "VACNT could not be observed before parameter optimization.",
            "No observable VACNT carpet on Al discs.",
            "no VACNT carpet",
            "not_applicable",
        ),
    ]
    for code, label, temp, duration, carbon, outcome, detail, morph, align in baselines:
        run_id = f"{SOURCE_ID}_{code}"
        add_run(
            tables,
            store,
            code,
            label,
            outcome,
            process(
                run_id,
                "baseline_aerosol_assisted_CCVD",
                temp,
                duration,
                carbon,
                "Pre-optimization baseline; exact gas recipe not repeated.",
            ),
            qualitative_yield(run_id, outcome, detail, morph, align),
            "SPAN_AA53942229E136ACCBA5",
            "SPAN_AA53942229E136ACCBA5",
        )
        if code == "B02":
            tables["yield_quality"][-1]["CNT_type_confirmed"] = "not_applicable"
            tables["yield_quality"][-1]["CNT_type_evidence"] = (
                "No observable VACNT product in this baseline."
            )
        append_baseline_scan_pdf_evidence(
            tables,
            store,
            run_id,
            inferred_from_same_conditions=code == "B02",
        )

    scans = [
        (
            "F01",
            ">4 wt%",
            "growth definitely disrupted",
            "disrupted carbon deposit",
            "not aligned",
            "SPAN_318E8C4AF638E8920A94",
        ),
        (
            "F02",
            "2-4 wt%",
            "VACNT with overgrown CNT bundles at carpet top",
            "VACNT with bundle overgrowth",
            "vertically aligned with overgrowth",
            "SPAN_318E8C4AF638E8920A94",
        ),
        (
            "F03",
            "<2 wt%",
            "very clean VACNT carpet without overgrown material",
            "clean VACNT carpet",
            "vertically aligned forest",
            "SPAN_011736A753EE93D6A9B4",
        ),
    ]
    for code, ratio, outcome, morph, align, span in scans:
        run_id = f"{SOURCE_ID}_{code}"
        add_run(
            tables,
            store,
            code,
            f"580 C Fe/C scan; ratio {ratio}",
            outcome,
            process(
                run_id,
                "Fe_C_ratio_scan",
                "580",
                "20",
                "C2H2",
                f"Fe/C precursor mass-ratio category {ratio}.",
            ),
            qualitative_yield(run_id, outcome, outcome, morph, align),
            span,
            span,
        )
        append_baseline_scan_pdf_evidence(tables, store, run_id)

    optimized = [
        (
            "O580",
            580,
            "50",
            "2.5",
            "8.7",
            "4.0",
            "6.94",
            "approximately 2 x10^11 CNT/cm2",
        ),
        (
            "O615",
            615,
            ">80",
            "4",
            "10.6",
            "5.1",
            "4.25",
            "approximately 1 x10^11 CNT/cm2",
        ),
    ]
    for code, temp, height, rate, outer, inner, id_i2d, density in optimized:
        run_id = f"{SOURCE_ID}_{code}"
        add_run(
            tables,
            store,
            code,
            f"optimized low-Fe/C VACNT at {temp} C",
            f"Clean aligned MWCNT carpet; mean growth rate {rate} micrometers/min.",
            process(
                run_id,
                "optimized_aerosol_assisted_CCVD",
                str(temp),
                "20",
                "C2H2",
                (
                    "Low Fe/C <2 wt%; total flow and C2H2/H2 values are "
                    "reported only as study-wide ranges."
                ),
                use_study_ranges=True,
            ),
            optimized_yield(
                run_id,
                temp,
                height,
                rate,
                outer,
                inner,
                id_i2d,
                density,
            ),
            "SPAN_4117A3D386BB903AD597",
            "SPAN_6617A867C1F6D97DBE8B",
        )
        growth_span = (
            "SPAN_305DE17DDE69C41FECB1"
            if code == "O580"
            else "SPAN_D0555750EF080363466C"
        )
        append_evidence(
            tables,
            store,
            run_id,
            "GROWTH",
            "yield_quality",
            f"{run_id}_PROD",
            (
                "yield_original;yield_value_standardized;"
                "yield_unit_standardized;length_summary"
            ),
            growth_span,
            f"Reported {temp} C VACNT growth-rate and thickness trend.",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "PURITY",
            "yield_quality",
            f"{run_id}_PROD",
            "TGA_carbon_content_wt_percent;purity_basis",
            "SPAN_8B2FC7057A95A8AFE8CE",
            "Results-section TGA carbon purity for optimized samples.",
        )
        append_optimized_pdf_evidence(tables, store, run_id)
        append_evidence(
            tables,
            store,
            run_id,
            "RAMAN",
            "yield_quality",
            f"{run_id}_PROD",
            "Raman_ratio_type;Raman_ratio_value",
            "SPAN_301A01228643E8A8148A",
            "Optimized 580/615 C Raman quality comparison.",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "RAMAN_METHOD",
            "yield_quality",
            f"{run_id}_PROD",
            "Raman_laser_wavelength_nm",
            "SPAN_BBCF2AED5133AA1442AB",
            "Reported 532 nm Raman excitation wavelength.",
        )
        if code == "O615":
            append_evidence(
                tables,
                store,
                run_id,
                "PURITY_RATE",
                "yield_quality",
                f"{run_id}_PROD",
                "yield_original;TGA_carbon_content_wt_percent;amorphous_carbon_level",
                "SPAN_0814133E8A571AF7D8A6",
                "Conclusion summary of 615 C rate, purity and morphology.",
            )

    for sample in TABLE1:
        code = sample["code"]
        run_id = f"{SOURCE_ID}_{code}"
        add_run(
            tables,
            store,
            code,
            f"Table 1 VACNT/Al electrode sample {code}",
            (
                f"Reported mass {sample['mass']} mg, height "
                f"{sample['height']} micrometers and diameter "
                f"{sample['diameter']} nm."
            ),
            process(
                run_id,
                "optimized_CCVD_product_sample_conditions_not_mapped",
                "not_reported",
                "not_reported",
                "C2H2",
                (
                    "P1-P7 were made by varying synthesis temperature and "
                    "duration, but Table 1 does not map exact settings to IDs."
                ),
            ),
            table1_yield(run_id, sample),
            "SPAN_201A3DED8872DAE8D844",
            "SPAN_579B955E8B48AD176C46",
            data_type="experimental_product_sample",
        )

    for item in MODELS:
        code = item["code"]
        run_id = f"{SOURCE_ID}_{code}"
        add_run(
            tables,
            store,
            code,
            f"{item['label']} fitted series at {item['temperature']} C",
            (
                f"Exponential-model fit: rate {item['rate']} micrometers/min, "
                f"lifetime {item['lifetime']} min, hmax {item['hmax']} micrometers."
            ),
            process(
                run_id,
                "experimental_series_exponential_model_fit",
                item["temperature"],
                "not_reported",
                "C2H2",
                f"{item['label']} experimental height-time series.",
            ),
            model_yield(
                run_id,
                item["hmax"],
                item["rate"],
                item["lifetime"],
            ),
            "SPAN_EF974DACDB79A6AF22DA",
            "SPAN_AB380F5587DD72A10B30",
            data_type="experimental_series_model_fit",
            yield_status="calculated",
        )

    reduced_id = f"{SOURCE_ID}_RED615"
    add_run(
        tables,
        store,
        "RED615",
        "615 C sequential run with acetylene flow divided by three",
        "Twenty minutes standard feed plus 60 minutes at one-third C2H2 flow.",
        process(
            reduced_id,
            "two_stage_reduced_acetylene_sequential_CCVD",
            "615",
            "80",
            "C2H2",
            "20 min standard conditions then 60 min at one-third C2H2 flow.",
        ),
        qualitative_yield(
            reduced_id,
            "180 micrometer mean height versus 112 micrometers for standard 80-min run",
            "Reduced acetylene suppressed disorganized interfacial carbon.",
            "thick VACNT mat with reduced disorganized carbon",
            "vertically aligned forest",
        ),
        "SPAN_30BB009D8318355875F0",
        "SPAN_71468A65C70CB83A113A",
    )

    r2r_id = f"{SOURCE_ID}_R2R"
    add_run(
        tables,
        store,
        "R2R",
        "continuous 30 cm roll-to-roll pilot VACNT production",
        "At 615 C for 60 min, VACNT height exceeded 200 micrometers.",
        process(
            r2r_id,
            "continuous_roll_to_roll_CCVD",
            "615",
            "60",
            "C2H2",
            "30 cm-wide pilot foil path at 1 m/h rolling speed.",
            "industrial_pilot",
        ),
        qualitative_yield(
            r2r_id,
            "VACNT carpet height above 200 micrometers",
            "Nanotube diameter/structure similar to laboratory products.",
            "industrial-scale VACNT carpet",
            "vertically aligned forest",
        ),
        "SPAN_FC98756598372D52FE31",
        "SPAN_82A5834307C2A9FC48E3",
        scale="industrial_pilot",
    )
    append_r2r_pdf_evidence(tables, store, r2r_id)

    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_GAS_RECIPE_001",
                SOURCE_ID,
                f"{SOURCE_ID}_O580",
                "critical_data_gap",
                "reactor_process_gas",
                f"{SOURCE_ID}_O580_S01",
                "gas_composition_summary",
                (
                    "The main article gives only study-wide ranges "
                    "(100-333 sccm total flow and 10-20% C2H2/H2); exact "
                    "run-level recipes appear to require supplementary data."
                ),
                f"EVD_{SOURCE_ID}_O580_PROCESS",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_P_MAPPING_001",
                SOURCE_ID,
                f"{SOURCE_ID}_P1",
                "run_split_uncertainty",
                "reactor_process_gas",
                f"{SOURCE_ID}_P1_S01",
                "temperature_setpoint_C",
                (
                    "P1-P7 are distinct named VACNT/Al samples with complete "
                    "product rows, but Table 1 does not map each sample to its "
                    "synthesis temperature and duration."
                ),
                f"EVD_{SOURCE_ID}_P1_PROCESS;EVD_{SOURCE_ID}_P1_YIELD",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_DUPLICATION_001",
                SOURCE_ID,
                f"{SOURCE_ID}_P1",
                "run_overlap_uncertainty",
                "source_run",
                f"{SOURCE_ID}_P1",
                "run_summary",
                (
                    "P1-P7 may overlap the optimized temperature/duration "
                    "series represented elsewhere. They are retained because "
                    "the source presents them as distinct named samples."
                ),
                f"EVD_{SOURCE_ID}_P1_YIELD",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_MODEL_001",
                SOURCE_ID,
                f"{SOURCE_ID}_M580S",
                "definition_ambiguity",
                "yield_quality",
                f"{SOURCE_ID}_M580S_PROD",
                "yield_original",
                (
                    "M580S/M615S/M580Q/M615Q are fitted summaries of "
                    "experimental series, not single physical synthesis runs."
                ),
                f"EVD_{SOURCE_ID}_M580S_YIELD",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PURITY_001",
                SOURCE_ID,
                f"{SOURCE_ID}_O615",
                "source_conflict",
                "yield_quality",
                f"{SOURCE_ID}_O615_PROD",
                "TGA_carbon_content_wt_percent",
                (
                    "The results text reports 99.4% C purity for optimized "
                    "samples, whereas the conclusion states 99.5 wt% at 615 C. "
                    "The structured field retains the direct results value 99.4."
                ),
                f"EVD_{SOURCE_ID}_O615_YIELD;EVD_{SOURCE_ID}_O615_PURITY_RATE",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_BASELINE_OCR_001",
                SOURCE_ID,
                f"{SOURCE_ID}_B01",
                "definition_ambiguity",
                "source_run",
                f"{SOURCE_ID}_B01",
                "run_summary",
                (
                    "The duplicated PDF text around the toluene-to-acetylene "
                    "baseline comparison is heavily interleaved. The two "
                    "negative/baseline outcomes are retained with medium confidence."
                ),
                f"EVD_{SOURCE_ID}_B01_YIELD;EVD_{SOURCE_ID}_B02_YIELD",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_001",
                SOURCE_ID,
                f"{SOURCE_ID}_O615",
                "critical_data_gap",
                "yield_quality",
                f"{SOURCE_ID}_O615_PROD",
                "yield_original",
                (
                    "The article reports carpet height/rate and P-sample mass "
                    "but not feed-carbon conversion or catalyst-normalized CNT yield."
                ),
                f"EVD_{SOURCE_ID}_O615_YIELD",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_R2R_PDF_001",
                SOURCE_ID,
                r2r_id,
                "figure_value_transcription",
                "reactor_process_gas",
                f"{r2r_id}_S01",
                "reactor_size_summary",
                (
                    "R2R width, speed and >200 micrometer carpet height were "
                    "visually checked on PDF page 15 and remain pending "
                    "independent evidence review."
                ),
                f"EVD_{r2r_id}_R2R_PDF",
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
