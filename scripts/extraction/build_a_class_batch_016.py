#!/usr/bin/env python3
"""Build the sixteenth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 16
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_F5C517498209ABBA"
HTML_NAME = f"{SOURCE_ID}_7f13c21ac393.html"


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


def append_figure_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    suffix: str,
    fields: str,
    span_id: str,
    figure_number: int,
    text: str,
    summary: str,
    value_status: str = "reported",
) -> None:
    evidence = evidence_row(
        store,
        SOURCE_ID,
        f"EVD_{run_id}_{suffix}",
        run_id,
        "yield_quality",
        f"{run_id}_PROD",
        fields,
        span_id,
        summary,
        value_status=value_status,
    )
    evidence.update(
        {
            "evidence_type": "html_figure_value_transcription",
            "source_section": f"Figure {figure_number}",
            "source_locator": f"PMC HTML Figure {figure_number}",
            "source_object_ref": (
                "data/raw/fulltext/supplementary/"
                f"{SOURCE_ID}/figure-{figure_number:02d}.jpg"
            ),
            "evidence_text": text,
            "evidence_summary": summary,
            "notes": (
                "The image linked from the locally stored PMC full text was "
                "downloaded and visually inspected."
            ),
        }
    )
    tables["evidence_index"].append(evidence)


def steel_catalyst(run_id: str, oxidized: bool = True) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label=(
            "air-oxidized SS 316 reactor-wall self-catalyst"
            if oxidized
            else "pristine non-oxidized SS 316 reactor-wall control"
        ),
        active_metals="Fe; Ni",
        support_material="SS 316 reactor wall",
        promoter="not_applicable",
        metal_ratio_original="Fe balance; Ni 10-14 wt.%; Cr 16-18 wt.%",
        metal_ratio_standardized="not_applicable",
        precursor_summary=(
            "SS 316: C 0.08, Mn 2.00, P 0.045, S 0.030, Si 0.75, "
            "Cr 16-18, Ni 10-14, Mo 2-3, N 0.10 wt.%; Fe balance"
        ),
        preparation_method=(
            "reactor_wall_air_oxidation_and_brushing"
            if oxidized
            else "as_received_reactor_wall"
        ),
        preparation_modifier=(
            "static air at 900 C for 1 h, cool, then nylon-brush surface"
            if oxidized
            else "no oxidation pretreatment"
        ),
        preparation_detail=(
            "Before each CVD run the second-stage SS 316 tube was oxidized "
            "at 900 C for 1 h at atmospheric pressure to remove carbon "
            "residue and expose/activate Fe and Ni."
            if oxidized
            else (
                "The non-oxidized control retained a Cr-dominated surface, "
                "which suppressed MWCNT formation."
            )
        ),
        drying_condition="not_applicable",
        calcination_condition=(
            "static air, 900 C, 60 min, atmospheric pressure"
            if oxidized
            else "not_applicable"
        ),
        reduction_condition="in-situ exposure to polypropylene pyrolysis vapors",
        activation_condition=(
            "oxidation removes/redistributes protective Cr surface layer"
            if oxidized
            else "not activated"
        ),
        post_preparation_condition=(
            "oxidized/brushed reactor wall"
            if oxidized
            else "pristine Cr-rich reactor wall"
        ),
        catalyst_particle_size_mean_nm="not_reported",
        catalyst_particle_size_range_nm="not_reported",
        catalyst_particle_size_qualifier=(
            "metal particles were observed at CNT tips and inside tubes"
        ),
        phase_or_state_summary=(
            "oxidized surface contained nickel iron oxide and iron chromium oxide"
            if oxidized
            else "pristine fcc austenite with Cr-dominated surface"
        ),
        dispersion_summary=(
            "Fe became exposed after oxidation; Ni grain-boundary distribution changed"
            if oxidized
            else "Cr extensively covered the pristine surface"
        ),
        deactivation_summary=(
            "carbon residue was removed by repeated pre-run oxidation; "
            "long-term reactor-wall consumption not quantified"
        ),
    )


def two_stage_process(run_id: str, temperature: int) -> dict[str, str]:
    return process_row(
        run_id,
        1,
        "two_stage_polypropylene_pyrolysis_CVD",
        reactor_type="two-stage SS 316 metal-tube CVD furnace",
        scale_level="lab_batch",
        reactor_material="SS 316",
        reactor_size_summary="not_reported",
        reactor_setup_summary=(
            "Washed/dried waste PP centrifuge tube pieces in first oven; "
            "self-catalytic SS 316 growth surface in second oven."
        ),
        catalyst_loading_mass_g="not_applicable_reactor_wall",
        temperature_setpoint_C=str(temperature),
        temperature_program_summary=(
            "Flush Ar 10 min; heat second stage at 10 C/min under 100 sccm "
            f"Ar to {temperature} C; then heat first stage at 10 C/min to "
            "500 C to generate propylene."
        ),
        holding_time_min="120",
        heating_rate_C_min="10",
        cooling_condition="furnace cooled before soot scraping",
        pressure_original="atmospheric",
        pressure_kPa="101.325",
        carbon_source="washed waste polypropylene centrifuge tubes",
        carbon_source_flow_original=(
            "typically 1-2 g, chopped into 0.5 cm x 8 cm pieces"
        ),
        reducing_gas="not_applicable",
        inert_gas="Ar",
        inert_gas_flow_original="100 sccm",
        inert_gas_flow_sccm="100",
        cofeed_or_reactive_gas="propylene generated in first stage at 500 C",
        total_flow_original="100 sccm Ar plus unquantified PP pyrolysis vapors",
        gas_composition_summary=(
            "Ar carrier; PP decomposed predominantly to propylene"
        ),
        process_note=(
            "After 2 h, black product was recovered by scraping the tube wall."
        ),
    )


def scale_review(run_id: str, oxidized: bool) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="lab_batch",
        scale_level_claimed="potential_low_cost_plastic_waste_upcycling",
        scale_evidence_summary=(
            "Two-stage flow reactor converted 1-2 g waste PP per run; "
            + (
                "the reactor wall supplied the catalyst without an added powder."
                if oxidized
                else "non-oxidized wall served as a low-yield control."
            )
        ),
        reactor_capacity_or_throughput="typically 1-2 g waste PP over 2 h",
        continuous_operation_time_h="not_reported",
        catalyst_lifetime_or_reuse=(
            "same SS 316 tube re-oxidized before runs; lifetime not quantified"
        ),
        batch_stability="temperature series reported; replicate dispersion absent",
        scale_up_issue=(
            "Reactor-wall metal dusting consumes/pits steel and presents "
            "mechanical-integrity and contamination risks."
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="no currency, energy or reactor-life cost reported",
        cost_driver_summary=(
            "two-furnace heating, argon, SS 316 wall renewal and nitric-acid purification"
        ),
        safety_risk=(
            "intentional metal dusting, hot propylene/pyrolysis gas, concentrated "
            "nitric acid reflux and nanoparticle exposure"
        ),
        emission_or_waste=(
            "unquantified pyrolysis off-gas and metal-containing nitric-acid wash"
        ),
        industrial_readiness_assessment=(
            "laboratory proof-of-principle; pressure-vessel integrity and "
            "reactor-wall loss require engineering validation"
        ),
        reproduction_value="high for temperature and pretreatment comparison",
        reproduction_priority="high",
        recommended_next_action=(
            "Measure reactor-wall mass loss, gas/carbon balance, metal carryover "
            "and repeated-run mechanical integrity."
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
                "Six oxidized-SS316 temperature-series runs at 600-1100 C "
                "and one non-oxidized 900 C reactor-wall control."
            ),
        )
    )
    tables["source_master"][0]["local_file_path"] = (
        f"data/interim/parsed_text/{SOURCE_ID}/full_text.txt"
    )
    tables["source_master"][0]["pdf_status"] = "validated_html_fulltext"
    tables["source_master"][0]["notes"] += (
        " Local PMC HTML and downloaded Figures 6, 8 and 9 were inspected. "
        "The attempted PMC PDF response was not a valid PDF and is not used."
    )

    configs = [
        {
            "code": "OX600",
            "label": "W-MWCNT-600",
            "temperature": 600,
            "yield": "0.6",
            "inner": "8",
            "outer": "28",
            "id_ig": "approximately 0.87",
            "i2d_ig": "approximately 0.35",
            "morphology": ("mixture of MWCNTs, CNFs, amorphous carbon and impurities"),
            "amorphous": "present; minor low-temperature TGA oxidation step",
            "tga": (
                "two oxidation regions at 300-400 C and 450-650 C; "
                "main oxidation near 500 C"
            ),
        },
        {
            "code": "OX700",
            "label": "W-MWCNT-700",
            "temperature": 700,
            "yield": "15",
            "inner": "9",
            "outer": "30",
            "id_ig": "approximately 0.76",
            "i2d_ig": "approximately 0.55",
            "morphology": "MWCNT product with reduced amorphous-carbon fraction",
            "amorphous": "small amount present",
            "tga": "small amorphous-carbon contribution; CNT oxidation above 500 C",
        },
        {
            "code": "OX800",
            "label": "W-MWCNT-800",
            "temperature": 800,
            "yield": "22.5",
            "inner": "9",
            "outer": "33",
            "id_ig": "approximately 0.56",
            "i2d_ig": "approximately 0.61",
            "morphology": "MWCNTs; amorphous-carbon formation not observed by SEM",
            "amorphous": "not observed",
            "tga": "highly graphitic carbon; oxidation above 500 C",
        },
        {
            "code": "OX900",
            "label": "W-MWCNT-900",
            "temperature": 900,
            "yield": "42.4",
            "inner": "10",
            "outer": "35",
            "outer_range": "20-35",
            "id_ig": "0.48",
            "i2d_ig": "approximately 0.60",
            "morphology": (
                "thick mat of graphitic hollow MWCNTs; metal at tips and "
                "inside tubes; interwall distance 0.35 nm"
            ),
            "amorphous": "not observed",
            "tga": "highly graphitic carbon; oxidation above 500 C",
        },
        {
            "code": "OX1000",
            "label": "W-MWCNT-1000",
            "temperature": 1000,
            "yield": "31.4",
            "inner": "9",
            "outer": "28",
            "id_ig": "approximately 0.63",
            "i2d_ig": "approximately 0.58",
            "morphology": "graphitic hollow MWCNTs similar to the 900 C product",
            "amorphous": "not observed",
            "tga": "highly graphitic carbon; oxidation shifted to higher temperature",
        },
        {
            "code": "OX1100",
            "label": "W-MWCNT-1100",
            "temperature": 1100,
            "yield": "35",
            "inner": "8",
            "outer": "32",
            "id_ig": "approximately 0.58",
            "i2d_ig": "approximately 0.53",
            "morphology": (
                "graphitic hollow MWCNTs; XRD also detected iron carbide "
                "and nickel iron oxide"
            ),
            "amorphous": "not observed",
            "tga": "highest-temperature oxidation profile in the series",
        },
    ]

    for config in configs:
        run_id = f"{SOURCE_ID}_{config['code']}"
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                config["code"],
                config["label"],
                (
                    f"Waste PP two-stage CVD on oxidized SS 316 at "
                    f"{config['temperature']} C for 2 h; corrected MWCNT "
                    f"yield {config['yield']}%."
                ),
                "high",
            )
        )
        tables["catalyst_system"].append(steel_catalyst(run_id))
        tables["reactor_process_gas"].append(
            two_stage_process(run_id, config["temperature"])
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="TGA_corrected_MWCNT_yield_from_waste_PP",
                yield_original=f"{config['yield']} wt.%",
                yield_definition_original=(
                    "TGA carbon fraction multiplied by gross metal-containing "
                    "CVD product yield, divided by 100"
                ),
                yield_calculation_method="author Equations (1) and (2)",
                yield_value_standardized=config["yield"],
                yield_unit_standardized="percent",
                secondary_result_summary=config["tga"],
                CNT_type_reported="W-MWCNTs",
                CNT_type_confirmed="MWCNTs",
                product_mixture_summary=config["morphology"],
                CNT_type_evidence="SEM/TEM hollow multiwall morphology",
                outer_diameter_mean_nm=config["outer"],
                outer_diameter_range_nm=config.get("outer_range", ""),
                inner_diameter_mean_nm=config["inner"],
                wall_number_summary="multi-walled; exact wall count not reported",
                length_summary="not_reported",
                morphology=config["morphology"],
                alignment_or_array="non-aligned fibrous mat",
                Raman_ratio_type="ID/IG; I2D/IG",
                Raman_ratio_value=f"{config['id_ig']}; {config['i2d_ig']}",
                Raman_laser_wavelength_nm="514.5",
                purity_basis="TGA used in corrected-yield equation",
                residue_summary="metal catalyst particles observed in/at CNTs",
                amorphous_carbon_level=config["amorphous"],
                characterization_methods="SEM; TEM; Raman; XRD; TGA; EPMA-WDS",
                post_treatment_or_purification=(
                    "400 mg product refluxed with 50 mL concentrated nitric "
                    "acid at 120 C for 4 h; filtered and washed to pH 5-7"
                ),
                purification_condition="concentrated nitric acid reflux",
            )
        )
        tables["cost_scale_review"].append(scale_review(run_id, True))

        for suffix, table, record, fields, span_id, summary in [
            (
                "CAT_COMPOSITION",
                "catalyst_system",
                f"{run_id}_CAT",
                "record_level",
                "SPAN_9D81D387A8C6DFD3BBCB",
                "SS 316 elemental composition.",
            ),
            (
                "CAT_PRETREATMENT",
                "catalyst_system",
                f"{run_id}_CAT",
                "record_level",
                "SPAN_46DFCD36236A755609FD",
                "Static-air oxidation, cooling and nylon brushing.",
            ),
            (
                "CAT_REUSE",
                "catalyst_system",
                f"{run_id}_CAT",
                "calcination_condition;activation_condition",
                "SPAN_F11BDAD854161B6ED897",
                "Pre-run oxidation condition and purpose.",
            ),
            (
                "PROCESS",
                "reactor_process_gas",
                f"{run_id}_S01",
                "record_level",
                "SPAN_9F7C76D4C49E25992658",
                "Two-stage heating, Ar flow, temperatures and 2 h hold.",
            ),
            (
                "FEED",
                "reactor_process_gas",
                f"{run_id}_S01",
                "carbon_source;carbon_source_flow_original",
                "SPAN_D7BEB75FF2497466576D",
                "Waste-PP preparation, dimensions and typical mass.",
            ),
            (
                "DIAMETER",
                "yield_quality",
                f"{run_id}_PROD",
                "inner_diameter_mean_nm;outer_diameter_mean_nm",
                "SPAN_A22FEA1985EDA011F7A9",
                "Table 2 inner and outer diameters for all temperatures.",
            ),
            (
                "MORPHOLOGY",
                "yield_quality",
                f"{run_id}_PROD",
                "record_level",
                (
                    "SPAN_C7C39C7FD2C87340E4B9"
                    if config["temperature"] >= 900
                    else "SPAN_B06A00E4A1B2C6D2304A"
                ),
                "Temperature-dependent carbon morphology.",
            ),
            (
                "TGA",
                "yield_quality",
                f"{run_id}_PROD",
                "secondary_result_summary;amorphous_carbon_level",
                "SPAN_CB0316F7E959E68D55C8",
                "TGA oxidation behavior and amorphous-carbon trend.",
            ),
            (
                "PURIFICATION",
                "yield_quality",
                f"{run_id}_PROD",
                "post_treatment_or_purification;purification_condition",
                "SPAN_52B32FC2DCD775E1BC96",
                "Nitric-acid purification mass, volume, temperature and duration.",
            ),
            (
                "RAMAN_METHOD",
                "yield_quality",
                f"{run_id}_PROD",
                "Raman_ratio_type;Raman_laser_wavelength_nm",
                "SPAN_5973FFD56E794DD1ED97",
                "Raman laser wavelength and measurement setup.",
            ),
            (
                "COST",
                "cost_scale_review",
                run_id,
                "record_level",
                "SPAN_9F7C76D4C49E25992658",
                "Laboratory two-stage batch scale.",
            ),
        ]:
            append_evidence(
                tables,
                store,
                run_id,
                suffix,
                table,
                record,
                fields,
                span_id,
                summary,
                "review_assessment" if table == "cost_scale_review" else "reported",
            )

        append_figure_evidence(
            tables,
            store,
            run_id,
            "FIG6_YIELD",
            "yield_original;yield_value_standardized",
            "SPAN_D515A06B371C07E28442",
            6,
            (
                f"Figure 6 prints {config['yield']}% above the "
                f"{config['temperature']} C bar."
            ),
            "Figure 6 supports the sample-specific corrected MWCNT yield.",
        )
        append_figure_evidence(
            tables,
            store,
            run_id,
            "FIG8_RAMAN",
            "Raman_ratio_type;Raman_ratio_value",
            "SPAN_ECC7157691C1EE51B72D",
            8,
            (
                f"Figure 8b at {config['temperature']} C: ID/IG "
                f"{config['id_ig']}; I2D/IG {config['i2d_ig']}."
            ),
            "Figure 8b supports the temperature-specific Raman ratios.",
            ("reported" if config["temperature"] == 900 else "approximate"),
        )
        append_figure_evidence(
            tables,
            store,
            run_id,
            "FIG9_TGA",
            "secondary_result_summary;amorphous_carbon_level",
            "SPAN_CB0316F7E959E68D55C8",
            9,
            f"Figure 9 profile for {config['label']}: {config['tga']}.",
            "Figure 9 supports the qualitative TGA profile.",
            "qualitative",
        )

    control_id = f"{SOURCE_ID}_RAW900"
    tables["source_run"].append(
        run_row(
            SOURCE_ID,
            "RAW900",
            "non-oxidized SS316 / waste PP / 900 C control",
            (
                "At 900 C the pristine Cr-covered tube produced filled CNFs "
                "and amorphous carbon at approximately 2.3 wt.% yield."
            ),
            "high",
        )
    )
    tables["source_run"][-1]["data_type"] = "experimental_control"
    tables["catalyst_system"].append(steel_catalyst(control_id, False))
    tables["reactor_process_gas"].append(two_stage_process(control_id, 900))
    tables["yield_quality"].append(
        yield_row(
            control_id,
            primary_yield_metric="reported_CNF_product_yield",
            yield_original="approximately 2.3 wt.%",
            yield_definition_original="carbon product relative to waste PP feed",
            yield_calculation_method="reported approximate value",
            yield_value_standardized="2.3",
            yield_unit_standardized="percent",
            secondary_result_summary=(
                "Cr-dominated pristine surface gave poor carbon-fiber yield."
            ),
            CNT_type_reported="carbon nanofibers",
            CNT_type_confirmed="not_applicable",
            product_mixture_summary="large filled CNFs with amorphous carbon",
            CNT_type_evidence="TEM found no hollow structure",
            outer_diameter_mean_nm="50",
            length_summary="5-8 micrometers",
            morphology="filled CNFs; soot/spheres/amorphous carbon also expected",
            alignment_or_array="not_reported",
            characterization_methods="SEM; TEM; EPMA-WDS; XRD",
            post_treatment_or_purification="not separately reported for control",
            purification_condition="not_reported",
        )
    )
    tables["cost_scale_review"].append(scale_review(control_id, False))
    for suffix, table, record, fields, span_id, summary, status in [
        (
            "CAT_COMPOSITION",
            "catalyst_system",
            f"{control_id}_CAT",
            "record_level",
            "SPAN_9D81D387A8C6DFD3BBCB",
            "SS 316 elemental composition.",
            "reported",
        ),
        (
            "PROCESS",
            "reactor_process_gas",
            f"{control_id}_S01",
            "record_level",
            "SPAN_9F7C76D4C49E25992658",
            "Common two-stage process used for the 900 C comparison.",
            "inferred",
        ),
        (
            "FEED",
            "reactor_process_gas",
            f"{control_id}_S01",
            "carbon_source;carbon_source_flow_original",
            "SPAN_D7BEB75FF2497466576D",
            "Waste-PP preparation, dimensions and typical mass.",
            "reported",
        ),
        (
            "OUTCOME",
            "yield_quality",
            f"{control_id}_PROD",
            "record_level",
            "SPAN_D6C52BCDB3A943D10182",
            "Non-oxidized 900 C CNF morphology, dimensions and yield.",
            "reported",
        ),
        (
            "COST",
            "cost_scale_review",
            control_id,
            "record_level",
            "SPAN_D6C52BCDB3A943D10182",
            "Low-yield consequence of omitting reactor oxidation.",
            "review_assessment",
        ),
    ]:
        append_evidence(
            tables,
            store,
            control_id,
            suffix,
            table,
            record,
            fields,
            span_id,
            summary,
            status,
        )

    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_1000_YIELD_001",
                SOURCE_ID,
                f"{SOURCE_ID}_OX1000",
                "source_internal_inconsistency",
                "yield_quality",
                f"{SOURCE_ID}_OX1000_PROD",
                "yield_original",
                (
                    "Figure 6 prints 31.4%, while the results text states "
                    "31.3% for the 1000 C product; the figure value is retained."
                ),
                (
                    f"EVD_{SOURCE_ID}_OX1000_FIG6_YIELD;"
                    f"EVD_{SOURCE_ID}_OX1000_YIELD_TEXT"
                ),
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_RAMAN_001",
                SOURCE_ID,
                f"{SOURCE_ID}_OX600",
                "figure_value_transcription",
                "yield_quality",
                f"{SOURCE_ID}_OX600_PROD",
                "Raman_ratio_value",
                (
                    "Except for the explicitly reported 900 C ID/IG=0.48, "
                    "temperature-specific ID/IG and I2D/IG values were visually "
                    "read from Figure 8b and are approximate."
                ),
                (
                    f"EVD_{SOURCE_ID}_OX600_FIG8_RAMAN;"
                    f"EVD_{SOURCE_ID}_OX700_FIG8_RAMAN;"
                    f"EVD_{SOURCE_ID}_OX800_FIG8_RAMAN;"
                    f"EVD_{SOURCE_ID}_OX1000_FIG8_RAMAN;"
                    f"EVD_{SOURCE_ID}_OX1100_FIG8_RAMAN"
                ),
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_LENGTH_001",
                SOURCE_ID,
                f"{SOURCE_ID}_OX900",
                "critical_data_gap",
                "yield_quality",
                f"{SOURCE_ID}_OX900_PROD",
                "length_summary",
                (
                    "Table 2 is captioned as diameter and length, but the "
                    "available table contains only inner and outer diameters."
                ),
                f"EVD_{SOURCE_ID}_OX900_DIAMETER",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CONTROL_PROTOCOL_001",
                SOURCE_ID,
                control_id,
                "same_protocol_inference",
                "reactor_process_gas",
                f"{control_id}_S01",
                "record_level",
                (
                    "The non-oxidized 900 C comparison reports its outcome but "
                    "does not restate every common flow/heating parameter; those "
                    "are inherited from the stated temperature-series protocol."
                ),
                f"EVD_{control_id}_PROCESS;EVD_{control_id}_OUTCOME",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_REACTOR_SAFETY_001",
                SOURCE_ID,
                f"{SOURCE_ID}_OX900",
                "scale_safety_limit",
                "cost_scale_review",
                f"{SOURCE_ID}_OX900",
                "safety_risk",
                (
                    "The method intentionally exploits metal dusting of the "
                    "reactor wall; reactor-wall mass loss and mechanical life "
                    "were not quantified."
                ),
                f"EVD_{SOURCE_ID}_OX900_COST",
                "high",
            ),
        ]
    )

    # Ground the explicitly reported text values used in issue comparison.
    append_evidence(
        tables,
        store,
        f"{SOURCE_ID}_OX1000",
        "YIELD_TEXT",
        "yield_quality",
        f"{SOURCE_ID}_OX1000_PROD",
        "yield_original",
        "SPAN_BC789FC46FBEA407AF17",
        "Results text reports 31.3% at 1000 C, differing from Figure 6.",
    )
    append_evidence(
        tables,
        store,
        f"{SOURCE_ID}_OX900",
        "RAMAN_EXACT",
        "yield_quality",
        f"{SOURCE_ID}_OX900_PROD",
        "Raman_ratio_value",
        "SPAN_65A49A3207339ADE24AE",
        "The 900 C ID/IG value of 0.48 is explicitly reported.",
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
