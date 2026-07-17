#!/usr/bin/env python3
"""Build the twentieth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 20
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_A67692827E9AD9EF"
PDF_REF = "data/raw/fulltext/pdf/LIT_A67692827E9AD9EF_b3037bce977e.pdf"

RECIPE_TEXT = (
    "The precursor solution contained ferrocene at 0.4 wt.% and thiophene "
    "at S/Fe molar ratio 0.3 in 10 mL ethanol. It was injected at 6 uL/min "
    "through a 140 C heating line into a vertical furnace held at 1000 C. "
    "Argon and hydrogen were each 100 sccm, total carrier-gas flow 200 sccm. "
    "The first 30 min of growth were exhausted through an oil trap; subsequent "
    "SWCNT film was collected on a 0.45 um PES membrane at room temperature. "
    "The collection tube was purged with 100 sccm argon when filters were changed."
)

STRUCTURE_TEXT = (
    "TEM measured local SWCNT diameters of 1.54, 1.45 and 1.38 nm, with "
    "average diameter 1.46 nm. The films were connected networks of SWCNT "
    "bundles and EDS mainly detected carbon and iron. Raman used 633.8, 514 "
    "and 785 nm excitation. At 785 nm the pristine ID/IG was 0.11 and RBM "
    "peaks were 112, 150 and 230 cm-1; no D band appeared with 633.8 or 514 nm."
)

TABLE1 = {
    5: {
        "density": "4.6 x 10^21 cm-3",
        "mobility": "4.58 x 10^-2 cm2/Vs",
        "hall": "1.35 x 10^-3 cm3/C",
        "sheet": "370 ohm/square",
        "transmittance": "95%",
        "trans_status": "reported",
    },
    10: {
        "density": "9.5 x 10^21 cm-3",
        "mobility": "3.5 x 10^-2 cm2/Vs",
        "hall": "6.6 x 10^-4 cm3/C",
        "sheet": "234 ohm/square",
        "transmittance": "80%",
        "trans_status": "reported",
    },
    15: {
        "density": "3.5 x 10^22 cm-3",
        "mobility": "3.3 x 10^-2 cm2/Vs",
        "hall": "1.8 x 10^-4 cm3/C",
        "sheet": "79 ohm/square",
        "transmittance": "approximately 72%",
        "trans_status": "figure_digitized_approximate",
    },
    20: {
        "density": "4.7 x 10^22 cm-3",
        "mobility": "3.1 x 10^-2 cm2/Vs",
        "hall": "1.3 x 10^-4 cm3/C",
        "sheet": "51 ohm/square",
        "transmittance": "approximately 64%",
        "trans_status": "figure_digitized_approximate",
    },
    25: {
        "density": "1.3 x 10^23 cm-3",
        "mobility": "2.7 x 10^-2 cm2/Vs",
        "hall": "4.6 x 10^-5 cm3/C",
        "sheet": "21 ohm/square",
        "transmittance": "43%",
        "trans_status": "reported",
    },
}

ACID_CASES = {
    "A": {
        "treatment": "30 min H2SO4 (65 wt.%) treatment plus DI-water rinse",
        "temperature": "not_reported",
        "acid": "H2SO4",
        "concentration": "65 wt.%",
        "rinse": "DI water",
        "density": "7.7 x 10^20 cm-3",
        "mobility": "0.75 cm2/Vs",
        "hall": "8 x 10^-3 cm3/C",
        "sheet": "139 ohm/square",
        "conductivity": "9240 S/m",
        "raman": "",
    },
    "B": {
        "treatment": ("30 min H2SO4 (65 wt.%) treatment at 80 C plus DI-water rinse"),
        "temperature": "80",
        "acid": "H2SO4",
        "concentration": "65 wt.%",
        "rinse": "DI water",
        "density": "3.2 x 10^20 cm-3",
        "mobility": "1.5 cm2/Vs",
        "hall": "2 x 10^-2 cm3/C",
        "sheet": "163 ohm/square",
        "conductivity": "7680 S/m",
        "raman": "0.14",
    },
    "C": {
        "treatment": (
            "30 min H2SO4 (65 wt.%) treatment plus ethanol rinse then DI-water rinse"
        ),
        "temperature": "not_reported",
        "acid": "H2SO4",
        "concentration": "65 wt.%",
        "rinse": "ethanol then DI water",
        "density": "8.4 x 10^21 cm-3",
        "mobility": "0.09 cm2/Vs",
        "hall": "7.7 x 10^-4 cm3/C",
        "sheet": "107 ohm/square",
        "conductivity": "12096 S/m",
        "raman": "",
    },
    "D": {
        "treatment": "30 min H2SO4 (4 M) treatment plus DI-water rinse",
        "temperature": "not_reported",
        "acid": "H2SO4",
        "concentration": "4 M",
        "rinse": "DI water",
        "density": "5 x 10^21 cm-3",
        "mobility": "0.08 cm2/Vs",
        "hall": "1.4 x 10^-3 cm3/C",
        "sheet": "228 ohm/square",
        "conductivity": "6400 S/m",
        "raman": "",
    },
    "E": {
        "treatment": "30 min HCl (4 M) treatment plus DI-water rinse",
        "temperature": "not_reported",
        "acid": "HCl",
        "concentration": "4 M",
        "rinse": "DI water",
        "density": "8.8 x 10^21 cm-3",
        "mobility": "0.1 cm2/Vs",
        "hall": "8.8 x 10^-4 cm3/C",
        "sheet": "115 ohm/square",
        "conductivity": "14060 S/m",
        "raman": "",
    },
    "F": {
        "treatment": "30 min HNO3 (4 M) treatment plus DI-water rinse",
        "temperature": "not_reported",
        "acid": "HNO3",
        "concentration": "4 M",
        "rinse": "DI water",
        "density": "1.2 x 10^22 cm-3",
        "mobility": "0.16 cm2/Vs",
        "hall": "5.8 x 10^-4 cm3/C",
        "sheet": "43 ohm/square",
        "conductivity": "30720 S/m",
        "raman": "0.22",
    },
}


def add_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    suffix: str,
    table: str,
    record_id: str,
    fields: str,
    span_id: str,
    summary: str,
    *,
    value_status: str = "reported",
    confidence: str = "high",
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
            confidence=confidence,
            value_status=value_status,
        )
    )


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
            "source_object_ref": PDF_REF,
            "evidence_text": text,
            "evidence_summary": summary,
            "notes": "Transcribed after visual inspection of the locally stored PDF.",
        }
    )
    tables["evidence_index"].append(item)


def catalyst(run_id: str) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label="in-situ floating Fe catalyst from ferrocene",
        active_metals="Fe",
        support_material="not_applicable_floating_catalyst",
        promoter="thiophene sulfur promoter",
        metal_ratio_original=(
            "ferrocene 0.4 wt.% in ethanol; thiophene S/Fe molar ratio 0.3"
        ),
        metal_ratio_standardized="S/Fe molar ratio 0.3",
        precursor_summary=(
            "ferrocene and thiophene dissolved in 10 mL ethanol precursor solution"
        ),
        preparation_method="in_situ_floating_catalyst_from_solution",
        preparation_modifier="solution injected at 6 uL/min through 140 C line",
        preparation_detail=(
            "Ferrocene-derived Fe catalyst and thiophene promoter entered "
            "continuously with ethanol into the 1000 C furnace."
        ),
        drying_condition="not_applicable",
        calcination_condition="not_applicable",
        reduction_condition="in-situ exposure to 100 sccm H2",
        activation_condition="in-situ ferrocene decomposition at 1000 C",
        post_preparation_condition="continuously generated floating catalyst",
        catalyst_particle_size_mean_nm="not_reported",
        catalyst_particle_size_range_nm="not_reported",
        catalyst_particle_size_qualifier=(
            "CNT diameter is not mapped to catalyst-particle size"
        ),
        phase_or_state_summary=(
            "Fe detected in collected film; active nanoparticle phase not resolved"
        ),
        dispersion_summary="floating aerosol catalyst; particle density not reported",
        deactivation_summary="not_reported",
    )


def growth_stage(
    run_id: str, order: int, duration: int, stage_type: str
) -> dict[str, str]:
    return process_row(
        run_id,
        order,
        stage_type,
        reactor_type="vertical floating-catalyst CVD furnace",
        scale_level="lab_continuous_collection",
        reactor_material="not_reported",
        reactor_size_summary="not_reported",
        reactor_setup_summary=(
            "140 C precursor heating line feeds a 1000 C vertical furnace; "
            "valves direct initial material to an oil trap and later product "
            "to a room-temperature membrane collection tube."
        ),
        temperature_setpoint_C="1000",
        temperature_program_summary=(
            "furnace held at 1000 C; precursor line held at 140 C"
        ),
        holding_time_min=str(duration),
        heating_rate_C_min="not_reported",
        cooling_condition="not_reported",
        pressure_original="not_reported",
        pressure_kPa="",
        carbon_source="ethanol precursor solution",
        carbon_source_flow_original="6 uL/min total precursor solution",
        reducing_gas="H2",
        reducing_gas_flow_original="100 sccm",
        inert_gas="Ar",
        inert_gas_flow_original="100 sccm",
        cofeed_or_reactive_gas=(
            "ferrocene 0.4 wt.% and thiophene at S/Fe 0.3 in ethanol"
        ),
        cofeed_flow_original="included in 6 uL/min precursor-solution feed",
        total_flow_original=(
            "200 sccm carrier gas plus 6 uL/min liquid precursor feed"
        ),
        gas_composition_summary=(
            "100 sccm Ar plus 100 sccm H2 carrying vaporized ethanol, "
            "ferrocene and thiophene"
        ),
        process_note=(
            "Initial 30 min material was exhausted to the oil trap."
            if stage_type == "fccvd_startup_to_waste"
            else (
                f"After startup, clean SWCNT film was collected for {duration} min "
                "on a 0.45 um PES membrane at room temperature."
            )
        ),
    )


def acid_stage(run_id: str, case: str, item: dict[str, str]) -> dict[str, str]:
    return process_row(
        run_id,
        3,
        "post_synthesis_acid_treatment",
        reactor_type="bench liquid-treatment vessel",
        scale_level="lab_batch_post_treatment",
        reactor_material="not_reported",
        reactor_size_summary="not_reported",
        reactor_setup_summary="10 min collected SWCNT membrane film treated with acid",
        temperature_setpoint_C=item["temperature"],
        temperature_program_summary=(
            "held at 80 C throughout treatment"
            if case == "B"
            else "treatment temperature not reported"
        ),
        holding_time_min="30",
        heating_rate_C_min="not_reported",
        cooling_condition="not_reported",
        pressure_original="not_reported",
        pressure_kPa="",
        carbon_source="not_applicable_post_treatment",
        carbon_source_flow_original="not_applicable",
        reducing_gas="not_applicable",
        reducing_gas_flow_original="not_applicable",
        inert_gas="not_applicable",
        inert_gas_flow_original="not_applicable",
        cofeed_or_reactive_gas=f"{item['acid']} acid treatment",
        cofeed_flow_original=item["concentration"],
        total_flow_original="not_applicable_liquid_batch",
        gas_composition_summary="not_applicable_liquid_post_treatment",
        process_note=f"{item['treatment']}; rinse sequence: {item['rinse']}.",
    )


def product(
    run_id: str,
    collection_min: int,
    result: dict[str, str],
    *,
    post_treatment: str = "none",
    raman_ratio: str = "0.11",
) -> dict[str, str]:
    property_summary = (
        f"Hall measurement at 300 K and 0.518 T: carrier density "
        f"{result['density']}; hole mobility {result['mobility']}; "
        f"Hall coefficient {result['hall']}; p-type; sheet resistance "
        f"{result['sheet']}"
    )
    if "conductivity" in result:
        property_summary += f"; conductivity {result['conductivity']}"
    else:
        property_summary += f"; transmittance at 550 nm {result['transmittance']}"
        if collection_min == 25:
            property_summary += "; film thickness approximately 800 nm"
    return yield_row(
        run_id,
        primary_yield_metric="membrane_collection_time_and_thin_film_properties",
        yield_original=f"SWCNT thin film collected for {collection_min} min",
        yield_definition_original=(
            "membrane-collected film after a separate 30 min FCCVD startup-to-waste period"
        ),
        yield_calculation_method="not_applicable_no_mass_yield_reported",
        yield_value_standardized="",
        yield_unit_standardized="",
        yield_standardization_note=(
            "Collection time and film properties retained; no mass-yield conversion."
        ),
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=property_summary,
        CNT_type_reported="SWCNT",
        CNT_type_confirmed="single-wall CNT supported by TEM and RBM Raman modes",
        product_mixture_summary="SWCNT network with Fe detected by EDS",
        CNT_type_evidence="TEM; Raman RBM peaks; diameter near 1.46 nm",
        SWCNT_or_few_wall_evidence_summary=(
            "TEM average diameter 1.46 nm and RBM peaks at 112, 150 and 230 cm-1"
        ),
        RBM_peak_reported="112; 150; 230 cm-1",
        outer_diameter_mean_nm="1.46",
        outer_diameter_range_nm="1.38-1.54",
        inner_diameter_mean_nm="not_reported",
        wall_number_summary="single-walled",
        length_summary="not_reported; aspect ratio described as greater than 1000",
        morphology="connected two-dimensional network of SWCNT bundles",
        alignment_or_array="random thin-film network",
        Raman_ratio_type="ID/IG",
        Raman_ratio_value=raman_ratio or "not_reported_for_this_treatment",
        Raman_laser_wavelength_nm="785" if raman_ratio else "not_reported",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis="not_reported",
        residue_summary="iron detected in deposited film by EDS",
        amorphous_carbon_level="low Raman D band for pristine film",
        BET_surface_area_product_m2_g="",
        characterization_methods="SEM; TEM; EDS; Raman; UV-visible; Hall effect",
        post_treatment_or_purification=post_treatment,
        purification_condition=(
            "not_applicable" if post_treatment == "none" else post_treatment
        ),
        application_property_summary=property_summary,
    )


def cost(run_id: str, acid: bool = False) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="lab_continuous_collection",
        scale_level_claimed="low_cost_process",
        scale_evidence_summary=(
            "Vertical FCCVD used 200 sccm total carrier gas and sequential "
            "membrane changes without stopping the experiment."
        ),
        reactor_capacity_or_throughput="not_reported",
        continuous_operation_time_h="not_reported",
        catalyst_lifetime_or_reuse="continuously supplied ferrocene",
        catalyst_reuse_cycles="not_applicable_continuous_precursor",
        batch_stability=(
            "multiple films collected sequentially; run-to-run statistics not reported"
        ),
        scale_up_issue=(
            "Control aerosol catalyst formation, 1000 C furnace duty, filter "
            "loading and uninterrupted valve/filter exchange."
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary=(
            "Authors call 200 sccm carrier flow low cost; no monetary or mass-yield data."
        ),
        cost_driver_summary=(
            "1000 C furnace, ethanol, ferrocene, thiophene, Ar/H2 and membrane filters"
            + (", plus acid and rinse solvent" if acid else "")
        ),
        safety_risk=(
            "flammable ethanol/H2, toxic ferrocene/thiophene aerosol, hot furnace"
            + (", corrosive concentrated acid" if acid else "")
        ),
        emission_or_waste=(
            "initial 30 min reactor effluent sent to oil trap; unquantified exhaust"
            + (", spent acid and rinse waste" if acid else "")
        ),
        industrial_readiness_assessment=(
            "continuous laboratory film collection demonstrated; production mass absent"
        ),
        reproduction_value="high for conditions; limited for yield economics",
        reproduction_priority="high",
        recommended_next_action=(
            "Report collected mass versus time, ethanol conversion, pressure, "
            "continuous duration, filter capacity and replicate film properties."
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
                "FCCVD synthesis recipe; five pristine collection-time films; "
                "six acid-treatment branches A-F; structural, Raman, optical "
                "and Hall-effect properties."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_fulltext_pdf"
    master["notes"] += (
        " The untreated 10 min sample is Table 2 Case G and is represented "
        "once by the pristine 10 min record."
    )

    pristine_ids: dict[int, str] = {}
    for collection_min, result in TABLE1.items():
        code = f"PRISTINE_{collection_min:02d}MIN"
        run_id = f"{SOURCE_ID}_{code}"
        pristine_ids[collection_min] = run_id
        summary = (
            f"Pristine SWCNT film collected for {collection_min} min after "
            f"30 min startup; {result['density']} carrier density and "
            f"{result['sheet']} sheet resistance."
        )
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                code,
                f"pristine SWCNT film, {collection_min} min collection",
                summary,
            )
        )
        tables["catalyst_system"].append(catalyst(run_id))
        tables["reactor_process_gas"].extend(
            [
                growth_stage(run_id, 1, 30, "fccvd_startup_to_waste"),
                growth_stage(run_id, 2, collection_min, "fccvd_membrane_collection"),
            ]
        )
        tables["yield_quality"].append(product(run_id, collection_min, result))
        tables["cost_scale_review"].append(cost(run_id))

        add_pdf_evidence(
            tables,
            store,
            run_id,
            "RUN",
            "source_run",
            run_id,
            "record_level",
            "SPAN_2532954400F00A0FD1B4",
            5,
            RECIPE_TEXT + f" This record collected product for {collection_min} min.",
            "Startup and collection-time record definition.",
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "CATALYST",
            "catalyst_system",
            f"{run_id}_CAT",
            "record_level",
            "SPAN_6076B4218C19E09B196C",
            5,
            RECIPE_TEXT,
            "Ferrocene/thiophene catalyst precursor composition.",
        )
        for stage in [1, 2]:
            add_pdf_evidence(
                tables,
                store,
                run_id,
                f"PROCESS_{stage}",
                "reactor_process_gas",
                f"{run_id}_S{stage:02d}",
                "record_level",
                "SPAN_2532954400F00A0FD1B4",
                5,
                RECIPE_TEXT
                + f" This record used a {collection_min} min collection interval.",
                "Complete FCCVD startup and collection recipe.",
            )
        table_text = (
            f"Table 1, {collection_min} min: carrier density {result['density']}; "
            f"mobility {result['mobility']}; Hall coefficient {result['hall']}; "
            f"P-type; sheet resistance {result['sheet']}. "
            f"Transmittance at 550 nm was {result['transmittance']}."
        )
        if collection_min == 25:
            table_text += " Film thickness was approximately 800 nm."
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "PRODUCT_TABLE1",
            "yield_quality",
            f"{run_id}_PROD",
            "record_level",
            "SPAN_5147A29A5F024A02AB9B",
            10,
            table_text,
            "Table 1 Hall data and Figure 7 optical property.",
            value_status=result["trans_status"],
            confidence=(
                "medium"
                if result["trans_status"] == "figure_digitized_approximate"
                else "high"
            ),
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "PRODUCT_STRUCTURE",
            "yield_quality",
            f"{run_id}_PROD",
            (
                "CNT_type_reported;CNT_type_confirmed;product_mixture_summary;"
                "CNT_type_evidence;SWCNT_or_few_wall_evidence_summary;"
                "RBM_peak_reported;outer_diameter_mean_nm;outer_diameter_range_nm;"
                "wall_number_summary;length_summary;morphology;alignment_or_array;"
                "Raman_ratio_type;Raman_ratio_value;Raman_laser_wavelength_nm;"
                "residue_summary;amorphous_carbon_level;characterization_methods"
            ),
            "SPAN_B11B4F3E76B2FF7933AA",
            8,
            STRUCTURE_TEXT,
            "Common TEM, EDS and Raman properties of pristine SWCNT film.",
        )
        add_evidence(
            tables,
            store,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            "record_level",
            "SPAN_2CC143C4F4C2116BAF50",
            "Paper identifies the 200 sccm carrier-gas process as low cost.",
            value_status="review_assessment",
        )

    acid_ids: dict[str, str] = {}
    for case, item in ACID_CASES.items():
        code = f"ACID_{case}"
        run_id = f"{SOURCE_ID}_{code}"
        acid_ids[case] = run_id
        summary = (
            f"Table 2 Case {case}: 10 min SWCNT film after {item['treatment']}; "
            f"{item['mobility']} mobility and {item['sheet']} sheet resistance."
        )
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                code,
                f"10 min SWCNT film, acid treatment Case {case}",
                summary,
            )
        )
        tables["catalyst_system"].append(catalyst(run_id))
        tables["reactor_process_gas"].extend(
            [
                growth_stage(run_id, 1, 30, "fccvd_startup_to_waste"),
                growth_stage(run_id, 2, 10, "fccvd_membrane_collection"),
                acid_stage(run_id, case, item),
            ]
        )
        acid_result = dict(item)
        post = item["treatment"]
        tables["yield_quality"].append(
            product(
                run_id,
                10,
                acid_result,
                post_treatment=post,
                raman_ratio=item["raman"],
            )
        )
        tables["cost_scale_review"].append(cost(run_id, acid=True))

        acid_text = (
            f"Table 2 Case {case}: {item['treatment']}. Carrier density "
            f"{item['density']}; hole mobility {item['mobility']}; Hall "
            f"coefficient {item['hall']}; P-type; sheet resistance "
            f"{item['sheet']}; conductivity {item['conductivity']}."
        )
        if item["raman"]:
            acid_text += (
                f" Raman at 785 nm gave ID/IG {item['raman']} for the "
                f"{'sulfuric-acid' if case == 'B' else 'nitric-acid'}-treated film."
            )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "RUN",
            "source_run",
            run_id,
            "record_level",
            "SPAN_367D8FDF7136BCAD298B",
            11,
            RECIPE_TEXT + " " + acid_text,
            "Production and acid-treatment branch definition.",
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "CATALYST",
            "catalyst_system",
            f"{run_id}_CAT",
            "record_level",
            "SPAN_6076B4218C19E09B196C",
            5,
            RECIPE_TEXT,
            "Shared ferrocene/thiophene catalyst recipe.",
        )
        for stage in [1, 2]:
            add_pdf_evidence(
                tables,
                store,
                run_id,
                f"PROCESS_{stage}",
                "reactor_process_gas",
                f"{run_id}_S{stage:02d}",
                "record_level",
                "SPAN_2532954400F00A0FD1B4",
                5,
                RECIPE_TEXT + " This branch used a 10 min collection interval.",
                "Shared FCCVD production process.",
            )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "PROCESS_3",
            "reactor_process_gas",
            f"{run_id}_S03",
            "record_level",
            "SPAN_893E53831769A880855F",
            11,
            acid_text,
            "Case-specific 30 min acid treatment and rinse.",
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "PRODUCT_TABLE2",
            "yield_quality",
            f"{run_id}_PROD",
            "record_level",
            "SPAN_28A0B4CCF59C62176114",
            11,
            acid_text,
            "Table 2 treatment and electrical properties.",
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "PRODUCT_STRUCTURE",
            "yield_quality",
            f"{run_id}_PROD",
            (
                "CNT_type_reported;CNT_type_confirmed;product_mixture_summary;"
                "CNT_type_evidence;SWCNT_or_few_wall_evidence_summary;"
                "RBM_peak_reported;outer_diameter_mean_nm;outer_diameter_range_nm;"
                "wall_number_summary;length_summary;morphology;alignment_or_array;"
                "residue_summary;amorphous_carbon_level;characterization_methods"
            ),
            "SPAN_B11B4F3E76B2FF7933AA",
            8,
            STRUCTURE_TEXT,
            "Shared structure of the starting 10 min SWCNT film.",
        )
        add_evidence(
            tables,
            store,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            "record_level",
            "SPAN_2CC143C4F4C2116BAF50",
            "Low-flow FCCVD plus review assessment of acid-treatment burdens.",
            value_status="review_assessment",
        )

    first_id = pristine_ids[5]
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_001",
                SOURCE_ID,
                first_id,
                "critical_data_gap",
                "yield_quality",
                f"{first_id}_PROD",
                "yield_original",
                (
                    "No collected CNT mass, precursor conversion or mass "
                    "productivity is reported; collection time is not a mass yield."
                ),
                f"EVD_{first_id}_PRODUCT_TABLE1",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_TIME_001",
                SOURCE_ID,
                first_id,
                "definition_boundary",
                "reactor_process_gas",
                f"{first_id}_S01",
                "holding_time_min",
                (
                    "The first 30 min is an FCCVD startup-to-waste period. "
                    "The 5-25 min values are later film-collection intervals "
                    "and must not replace or be added as one growth-time field."
                ),
                f"EVD_{first_id}_PROCESS_1;EVD_{first_id}_PROCESS_2",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_OPTICAL_001",
                SOURCE_ID,
                pristine_ids[15],
                "figure_digitization",
                "yield_quality",
                f"{pristine_ids[15]}_PROD",
                "application_property_summary",
                (
                    "The 15 and 20 min transmittances are visually digitized "
                    "from Figure 7; only the 5 and 25 min endpoints and the "
                    "10 min approximately 80% value are stated in text."
                ),
                (
                    f"EVD_{pristine_ids[15]}_PRODUCT_TABLE1;"
                    f"EVD_{pristine_ids[20]}_PRODUCT_TABLE1"
                ),
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_BRANCH_001",
                SOURCE_ID,
                acid_ids["A"],
                "shared_parent_sample",
                "source_run",
                acid_ids["A"],
                "run_summary",
                (
                    "Cases A-F are post-treatments of the same 10 min "
                    "collection basis; the untreated Case G is represented "
                    "by the pristine 10 min record and is not duplicated."
                ),
                f"EVD_{acid_ids['A']}_RUN",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PRESSURE_001",
                SOURCE_ID,
                first_id,
                "critical_data_gap",
                "reactor_process_gas",
                f"{first_id}_S02",
                "pressure_original",
                "FCCVD operating pressure is not explicitly reported.",
                f"EVD_{first_id}_PROCESS_2",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_RAMAN_001",
                SOURCE_ID,
                acid_ids["A"],
                "sample_mapping",
                "yield_quality",
                f"{acid_ids['A']}_PROD",
                "Raman_ratio_value",
                (
                    "Treatment-specific ID/IG is explicitly available only "
                    "for the selected sulfuric-acid and nitric-acid spectra; "
                    "other acid cases remain not reported."
                ),
                (
                    f"EVD_{acid_ids['B']}_PRODUCT_TABLE2;"
                    f"EVD_{acid_ids['F']}_PRODUCT_TABLE2"
                ),
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
