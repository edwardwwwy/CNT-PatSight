#!/usr/bin/env python3
"""Build the seventh evidence-grounded A-class extraction batch."""
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


BATCH_NUMBER = 7
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ID = "LIT_F64EACA2D669B320"

PRECURSOR_RUNS = [
    ("Ethylbenzene", "954 ± 175", "38.2 ± 8.5", "10 ± 1.3", "45.1", "24.3", "0.327", "597", "640", "654", "58", "1.8"),
    ("Isopropylbenzene", "699 ± 159", "27.4 ± 6.6", "10.2 ± 0.8", "58.8", "26.6", "0.290", "610", "650", "673", "63", "2.8"),
    ("Toluene", "591 ± 141", "21.2 ± 5.9", "11.15 ± 0.6", "38.3", "13.4", "0.290", "575", "622", "644", "69", "5.9"),
    ("m-Xylene", "531 ± 42", "20.8 ± 3.6", "10.2 ± 1.6", "40.4", "20.4", "0.286", "581", "616", "630", "49", "3.3"),
    ("n-Butylbenzene", "466 ± 54", "16.6 ± 2.4", "11.19 ± 1", "57.0", "26.8", "0.322", "573", "615", "638", "64", "3.0"),
    ("Benzene", "403 ± 51", "16.6 ± 2.2", "9.7 ± 0.4", "47.5", "22.2", "0.292", "581", "621", "632", "51", "4.4"),
    ("Methylcyclohexane", "392 ± 183", "50.6 ± 23.8", "3.1 ± 0.1", "43.1", "20.8", "0.345", "607", "649", "672", "66", "1.1"),
    ("n-Heptane", "392 ± 263", "14.3 ± 9.6", "10.95 ± 0.5", "33.5", "17.2", "0.414", "562", "606", "630", "68", "4.1"),
    ("1,2,4-Trimethylbenzene", "309 ± 78", "13.2 ± 3.3", "9.35 ± 0.2", "52.1", "22.6", "0.307", "558", "594", "624", "66", "4.3"),
    ("n-Pentane", "302 ± 196", "<1", "~250", "40.3", "18.3", "0.349", "595", "641", "665", "70", "1.3"),
    ("Cyclohexane", "204 ± 11", "6.5 ± 0.8", "12.45 ± 1.3", "47.4", "23.5", "0.384", "583", "633", "663", "80", "5.0"),
    ("n-Hexane", "131 ± 59", "<1", "~100", "39.2", "14.7", "0.401", "555", "606", "637", "82", "7.5"),
    ("Cyclohexanone", "125 ± 49", "9.6 ± 3.8", "5.2 ± 0", "48.0", "25.6", "0.429", "548", "585", "608", "60", "5.6"),
    ("Diethylbenzene", "60 ± 37", "1.9 ± 1.2", "12.9 ± 2.9", "57.5", "21.4", "0.309", "570", "608", "624", "55", "3.7"),
    ("n-Propylbenzene", "57 ± 21", "2.1 ± 0.8", "10.9 ± 0.8", "37.4", "12.2", "0.542", "512", "574", "620", "108", "10.9"),
]

FERROCENE_LEVELS = (1, 3, 5, 7, 9, 11, 13, 15)

CATALYST_SOURCE_RUNS = [
    ("Fe", "5 wt.% ferrocene", "ferrocene", "Fe-only comparison control"),
    (
        "Fe; Ni",
        "4.89 wt.% ferrocene + 0.11 wt.% nickelocene",
        "ferrocene; nickelocene",
        "Ni addition did not improve MWCNT yield or quality",
    ),
    (
        "Fe; Co",
        "4.89 wt.% ferrocene + 0.11 wt.% cobaltocene",
        "ferrocene; cobaltocene",
        "Co addition did not improve MWCNT yield or quality",
    ),
]

UPSCALE_RUNS = [
    (1, "small", 800, 15, "1.0", "10.0", "0.95", "43.2", "45.1", "24.3", "25.5", "40.0", "56.1", "310", "0.327", "0.582", "597", "640", "654", "58", "1.85"),
    (2, "small", 800, 30, "1.0", "10.0", "1.92", "38.4", "33.6", "16.1", "24.3", "30.4", "38.9", "670", "0.325", "0.595", "593", "626", "645", "52", "2.16"),
    (3, "small", 800, 45, "1.0", "10.0", "2.41", "32.1", "35.2", "22.2", "21.6", "29.2", "41.0", "1050", "0.352", "0.569", "601", "630", "646", "45", "1.71"),
    (4, "small", 800, 60, "1.0", "10.0", "2.44", "24.4", "37.2", "22.3", "19.6", "31.9", "53.4", "1350", "0.410", "0.561", "574", "600", "615", "41", "2.90"),
    (5, "small", 800, 120, "1.0", "10.0", "4.42", "22.1", "76.0", "37.8", "41.6", "72.4", "106.5", "1550", "0.384", "0.552", "586", "622", "655", "69", "2.42"),
    (6, "small", 800, 120, "2.5", "27.4", "4.95", "9.0", "39.7", "26.9", "19.8", "29.3", "55.4", "1400", "0.484", "0.512", "552", "577", "596", "44", "5.87"),
    (7, "small", 850, 120, "1.0", "10.0", "2.54", "12.7", "39.9", "20.9", "21.9", "39.5", "49.9", "2280", "0.318", "0.599", "574", "613", "661", "88", "2.93"),
    (8, "small", 850, 120, "2.5", "27.4", "5.48", "10.0", "84.9", "42.6", "50.2", "84.5", "106.7", "2450", "0.289", "0.551", "571", "595", "618", "47", "3.61"),
    (9, "large", 800, 120, "1.0", "12.0", "21.1", "87.9", "44.3", "25.4", "26.2", "36.9", "54.6", "1190", "0.368", "0.500", "615", "646", "663", "48", "1.29"),
    (10, "large", 850, 120, "1.0", "12.0", "5.6", "23.3", "48.2", "24.9", "28.0", "42.6", "63.2", "1430", "0.385", "0.421", "610", "641", "658", "48", "1.37"),
    (11, "large", 850, 120, "2.5", "32.9", "6.8", "10.3", "35.7", "16.1", "25.0", "32.0", "40.4", "1430", "0.315", "0.529", "595", "626", "653", "58", "1.83"),
    (12, "large", 850, 120, "2 × 2.5", "54.8", "28", "26", "43.6", "21.8", "29.0", "38.1", "56.4", "860", "0.519", "0.481", "574", "608", "645", "70", "2.25"),
    (13, "large", 850, 240, "2 × 1.0", "20.0", "25", "31", "33.2", "15.2", "21.8", "30.4", "39.3", "2680", "0.310", "0.561", "592", "616", "641", "49", "2.02"),
]


def add_observation(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    suffix: str,
    span_id: str,
    summary: str,
) -> str:
    evidence_id = f"EVD_{SOURCE_ID}_OBS_{suffix}"
    evidence = evidence_row(
        store,
        SOURCE_ID,
        evidence_id,
        "not_applicable",
        "source_master",
        SOURCE_ID,
        "source_section_scope",
        span_id,
        summary,
    )
    evidence["evidence_type"] = "source_observation"
    tables["evidence_index"].append(evidence)
    return evidence_id


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
        )
    )


def floating_catalyst(
    run_id: str,
    active_metals: str,
    ratio: str,
    precursors: str,
) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label=f"floating catalyst from {precursors}",
        active_metals=active_metals,
        support_material="not_applicable",
        promoter="not_applicable",
        metal_ratio_original=ratio,
        metal_ratio_standardized=ratio,
        precursor_summary=precursors,
        preparation_method="aerosol_assisted_in_situ_floating_catalyst",
        preparation_modifier="metallocene dissolved in liquid carbon source",
        preparation_detail=(
            "Liquid precursor/metallocene solution aerosolized by a "
            "piezo-driven generator; catalyst nanoparticles formed in situ."
        ),
        drying_condition="not_applicable",
        calcination_condition="not_applicable",
        reduction_condition="in-situ metallocene decomposition",
        activation_condition="in-situ metallocene decomposition",
        post_preparation_condition="floating/in-situ catalyst",
        phase_or_state_summary="iron or mixed-metal nanoparticles formed in situ",
        dispersion_summary="aerosol/floating catalyst",
        deactivation_summary="not_reported",
    )


def common_process(
    run_id: str,
    carbon_source: str,
    temperature: int,
    time_min: int,
    argon_flow: str,
    precursor_rate: str,
    reactor: str = "small",
) -> dict[str, str]:
    if reactor == "large":
        reactor_size = "120 cm length; 9.5 cm inner diameter; 8.5 L"
        reactor_type = "large three-zone horizontal AACVD tube furnace"
    else:
        reactor_size = "60-80 cm heated/tube length; 2.1 cm inner diameter; 0.2 L"
        reactor_type = "single-zone horizontal AACVD tube furnace"
    return process_row(
        run_id,
        1,
        "AACVD_growth",
        reactor_type=reactor_type,
        reactor_material="quartz",
        reactor_size_summary=reactor_size,
        reactor_setup_summary=(
            "Piezo-driven aerosol generator feeding a horizontal quartz-tube "
            "furnace; acetone bubbler captured soot and other exhaust products."
        ),
        catalyst_loading_mass_g="not_applicable",
        temperature_setpoint_C=str(temperature),
        temperature_program_summary="reactor stabilized before aerosol injection",
        holding_time_min=str(time_min),
        cooling_condition="cooled under argon flow",
        pressure_original="not_reported",
        pressure_kPa="not_reported",
        carbon_source=carbon_source,
        carbon_source_flow_original=(
            f"{precursor_rate} g/hr precursor consumption"
            if precursor_rate
            else "not_reported"
        ),
        inert_gas="Ar",
        inert_gas_flow_original=f"{argon_flow} L/min",
        cofeed_or_reactive_gas="not_applicable",
        total_flow_original=f"{argon_flow} L/min Ar",
        gas_composition_summary=(
            f"{carbon_source} aerosol/metallocene precursor carried by Ar"
        ),
    )


def common_cost(
    run_id: str,
    throughput: str,
    reactor: str = "small",
) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="lab_batch",
        scale_level_claimed="scale_up_potential",
        scale_evidence_summary=(
            "Large 8.5 L reactor with large-area substrates"
            if reactor == "large"
            else "Small laboratory AACVD reactor"
        ),
        reactor_capacity_or_throughput=throughput,
        continuous_operation_time_h="not_applicable",
        catalyst_lifetime_or_reuse="not_applicable; floating catalyst consumed",
        batch_stability="single reported batch/condition or replicate mean",
        scale_up_issue=(
            "Batch heating/cooling, precursor utilization, catalyst residue "
            "and exhaust/by-product management."
        ),
        cost_driver_summary=(
            "Liquid hydrocarbon, metallocene, argon, furnace energy and "
            "exhaust handling; no full quantitative cost model."
        ),
        safety_risk=(
            "Flammable hydrocarbons/metallocenes at high temperature; substrate "
            "cleaning elsewhere used hydrofluoric acid."
        ),
        emission_or_waste=(
            "Soot and hydrocarbon by-products captured in an acetone bubbler; "
            "benzene/toluene by-products identified."
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
                "Doctoral dissertation experimental chapters: reactor mapping, "
                "15-carbon-source comparison, ferrocene concentration series, "
                "mixed-metallocene comparison, online gas analysis and 13-run "
                "AACVD scale-up matrix."
            ),
        )
    )
    tables["source_master"][0]["local_file_path"] = (
        f"data/interim/parsed_text/by_source/{SOURCE_ID}.parsed.json"
    )
    tables["source_master"][0]["notes"] += " Source document is a doctoral dissertation."

    # Fifteen carbon-source comparison runs (Table 6).
    for index, item in enumerate(PRECURSOR_RUNS, start=1):
        (
            carbon,
            mass_mg,
            conversion,
            consumption,
            diameter,
            diameter_sd,
            raman,
            t20,
            t50,
            t70,
            t_delta,
            iron,
        ) = item
        code = f"P{index:02d}"
        run_id = f"{SOURCE_ID}_{code}"
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                code,
                f"{carbon} + 5 wt.% ferrocene / 800 C / 15 min",
                (
                    f"AACVD carbon-source comparison; {mass_mg} mg MWCNTs, "
                    f"{conversion}% precursor conversion, mean OD {diameter} nm."
                ),
            )
        )
        tables["catalyst_system"].append(
            floating_catalyst(run_id, "Fe", "5 wt.% ferrocene", "ferrocene")
        )
        tables["reactor_process_gas"].append(
            common_process(
                run_id, carbon, 800, 15, "1.000", consumption, "small"
            )
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="precursor_conversion_to_MWCNT_product",
                yield_original=f"{conversion}% precursor conversion yield",
                yield_definition_original=(
                    "mass of synthesized MWCNTs divided by mass of consumed precursor"
                ),
                yield_calculation_method="reported gravimetric definition",
                yield_value_standardized=conversion if "<" not in conversion else "not_reported",
                yield_unit_standardized="percent",
                yield_standardization_note="Reported precursor conversion; no redefinition.",
                secondary_result_summary=(
                    f"Total MWCNT mass {mass_mg} mg; precursor consumption "
                    f"{consumption} g/hr; TGA T20/T50/T70 = "
                    f"{t20}/{t50}/{t70} C; T70-T20 = {t_delta} C."
                ),
                CNT_type_reported="MWCNTs",
                CNT_type_confirmed="MWCNTs",
                product_mixture_summary=(
                    f"MWCNTs with {iron} wt.% reported residual iron-based catalyst."
                ),
                CNT_type_evidence="TEM and Raman characterization.",
                outer_diameter_mean_nm=diameter,
                outer_diameter_range_nm=f"mean {diameter} ± {diameter_sd}",
                wall_number_summary="multi-walled",
                morphology="MWCNT carpet/batch; carbon-source-dependent morphology",
                alignment_or_array="vertically aligned carpets reported for efficient precursors",
                Raman_ratio_type="ID/IG",
                Raman_ratio_value=raman,
                purity_basis="as-synthesized product; residual catalyst by TGA/XRD method",
                residue_summary=f"{iron} wt.% residual iron-based catalyst",
                amorphous_carbon_level="not_reported",
                characterization_methods="SEM; TEM; Raman; TGA; XRD",
                post_treatment_or_purification="none reported",
                purification_condition="not_applicable",
            )
        )
        tables["cost_scale_review"].append(
            common_cost(
                run_id,
                (
                    f"{mass_mg} mg MWCNTs in 15 min; "
                    f"{consumption} g/hr precursor consumption"
                ),
            )
        )
        evidence_specs = [
            ("CAT", "catalyst_system", f"{run_id}_CAT", "record_level", "SPAN_15314A1789BCACB175AE", "Five-weight-percent ferrocene floating-catalyst recipe."),
            ("PROC", "reactor_process_gas", f"{run_id}_S01", "reactor_type;reactor_material;reactor_size_summary;temperature_setpoint_C;holding_time_min;cooling_condition;carbon_source;inert_gas;inert_gas_flow_original;total_flow_original", "SPAN_70DF8D5AE367868F1E80", "AACVD reactor, temperature and argon carrier."),
            ("PROC_TIME", "reactor_process_gas", f"{run_id}_S01", "holding_time_min;cooling_condition", "SPAN_92AF98B31AB4B1E65AC8", "Fifteen-minute aerosol injection and argon cooling."),
            ("PROC_RATE", "reactor_process_gas", f"{run_id}_S01", "carbon_source_flow_original", "SPAN_829900287C4041DF92B4", "Carbon-source-specific precursor consumption rate."),
            ("YIELD", "yield_quality", f"{run_id}_PROD", "record_level", "SPAN_829900287C4041DF92B4", "Table 6 mass, conversion, diameter, Raman, TGA and residue data."),
            ("COST", "cost_scale_review", run_id, "record_level", "SPAN_829900287C4041DF92B4", "Reported batch mass and precursor-use evidence."),
            ("WASTE", "cost_scale_review", run_id, "safety_risk;emission_or_waste;scale_up_issue", "SPAN_747B1BC33B21F97A4128", "Acetone-bubbler exhaust capture and spatial reactor setup."),
        ]
        for spec in evidence_specs:
            append_evidence(tables, store, run_id, *spec)

    # Ferrocene concentration series. Exact graph-only values are deliberately not digitized.
    for index, level in enumerate(FERROCENE_LEVELS, start=1):
        code = f"F{index:02d}"
        run_id = f"{SOURCE_ID}_{code}"
        if level == 1:
            result = "MWCNTs formed but were randomly oriented rather than a clean aligned carpet."
        elif level == 15:
            result = "Vertically aligned MWCNT carpet; mean OD exceeded 70 nm."
        elif level >= 11:
            result = "Vertically aligned MWCNT carpet with micron-scale iron-particle agglomerates."
        else:
            result = "Clean vertically aligned MWCNT carpet; diameter generally within the 30-60 nm series range."
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                code,
                f"toluene + {level} wt.% ferrocene / 800 C / 15 min",
                f"Ferrocene-concentration series; {result}",
                "medium",
            )
        )
        tables["catalyst_system"].append(
            floating_catalyst(
                run_id, "Fe", f"{level} wt.% ferrocene", "ferrocene"
            )
        )
        tables["reactor_process_gas"].append(
            common_process(run_id, "toluene", 800, 15, "1.000", "", "small")
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="qualitative_yield_and_morphology",
                yield_original="exact value shown graphically; not digitized",
                yield_definition_original=(
                    "MWCNT mass/precursor behavior compared across ferrocene concentrations"
                ),
                yield_calculation_method="qualitative transcription from text and figures",
                yield_value_standardized="not_reported",
                yield_unit_standardized="not_applicable",
                secondary_result_summary=result,
                CNT_type_reported="MWCNTs",
                CNT_type_confirmed="MWCNTs",
                product_mixture_summary=(
                    result
                    + (
                        " Residual catalyst increased at higher ferrocene concentration."
                        if level >= 9
                        else ""
                    )
                ),
                CNT_type_evidence="TEM gallery and text.",
                outer_diameter_range_nm=(
                    ">70" if level == 15 else "30-60 (series-level range)"
                ),
                wall_number_summary="multi-walled",
                morphology="MWCNTs",
                alignment_or_array=(
                    "randomly oriented" if level == 1 else "vertically aligned carpet"
                ),
                Raman_ratio_type="ID/IG",
                Raman_ratio_value="not_reported",
                purity_basis="as-synthesized",
                residue_summary=(
                    "micron-scale iron agglomerates visible"
                    if level >= 11
                    else "qualitative residual iron trend only"
                ),
                amorphous_carbon_level="not_reported",
                characterization_methods="SEM; TEM; Raman; TGA",
                post_treatment_or_purification="none reported",
                purification_condition="not_applicable",
            )
        )
        tables["cost_scale_review"].append(
            common_cost(
                run_id,
                "15 min laboratory AACVD batch; exact product mass graph-only",
            )
        )
        evidence_specs = [
            ("CAT", "catalyst_system", f"{run_id}_CAT", "record_level", "SPAN_B61AB05D8A04B36EAE66", "Ferrocene concentration series conditions."),
            ("PROC", "reactor_process_gas", f"{run_id}_S01", "record_level", "SPAN_92AF98B31AB4B1E65AC8", "Common 800 C, 15-minute AACVD process."),
            ("YIELD_TREND", "yield_quality", f"{run_id}_PROD", "primary_yield_metric;yield_original;yield_definition_original;secondary_result_summary;residue_summary", "SPAN_29C37169C86901815F9E", "Yield, oxidation-resistance and residual-catalyst trends."),
            ("MORPH", "yield_quality", f"{run_id}_PROD", "CNT_type_reported;CNT_type_confirmed;outer_diameter_range_nm;wall_number_summary;morphology;alignment_or_array;product_mixture_summary", "SPAN_54AF44E04AC5FF612ACC", "Concentration-specific morphology and diameter range."),
            ("COST", "cost_scale_review", run_id, "record_level", "SPAN_4A226B74787124A1F47E", "Metallocene cost/solubility and large-scale implications."),
        ]
        for spec in evidence_specs:
            append_evidence(tables, store, run_id, *spec)

    # Catalyst-source comparison.
    for index, (metals, ratio, precursor, result) in enumerate(
        CATALYST_SOURCE_RUNS, start=1
    ):
        code = f"M{index:02d}"
        run_id = f"{SOURCE_ID}_{code}"
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                code,
                f"toluene + {ratio} / 800 C / 15 min",
                f"Catalyst-source comparison; {result}.",
                "medium",
            )
        )
        tables["catalyst_system"].append(
            floating_catalyst(run_id, metals, ratio, precursor)
        )
        tables["reactor_process_gas"].append(
            common_process(run_id, "toluene", 800, 15, "1.000", "", "small")
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="qualitative_catalyst_source_comparison",
                yield_original="exact mass/yield not reported in text",
                yield_definition_original="relative MWCNT yield and quality",
                yield_calculation_method="qualitative comparison",
                yield_value_standardized="not_reported",
                yield_unit_standardized="not_applicable",
                secondary_result_summary=result,
                CNT_type_reported="MWCNTs",
                CNT_type_confirmed="MWCNTs",
                product_mixture_summary="MWCNT product; exact impurity level not reported.",
                CNT_type_evidence="MWCNT catalyst-source comparison.",
                wall_number_summary="multi-walled",
                morphology="MWCNTs",
                Raman_ratio_type="not_reported",
                Raman_ratio_value="not_reported",
                purity_basis="not_reported",
                residue_summary="not_reported",
                amorphous_carbon_level="not_reported",
                characterization_methods="SEM; TEM; Raman; TGA",
                post_treatment_or_purification="none reported",
                purification_condition="not_applicable",
            )
        )
        tables["cost_scale_review"].append(
            common_cost(
                run_id,
                "15 min laboratory AACVD catalyst-source comparison",
            )
        )
        evidence_specs = [
            ("CAT", "catalyst_system", f"{run_id}_CAT", "record_level", "SPAN_B61AB05D8A04B36EAE66", "Metallocene catalyst-source composition."),
            ("PROC", "reactor_process_gas", f"{run_id}_S01", "record_level", "SPAN_92AF98B31AB4B1E65AC8", "Common AACVD process."),
            ("YIELD", "yield_quality", f"{run_id}_PROD", "record_level", "SPAN_4A226B74787124A1F47E", "Nickelocene/cobaltocene did not improve yield or quality."),
            ("COST", "cost_scale_review", run_id, "record_level", "SPAN_4A226B74787124A1F47E", "Low solubility and higher cost of Ni/Co metallocenes."),
        ]
        for spec in evidence_specs:
            append_evidence(tables, store, run_id, *spec)

    # Thirteen scale-up matrix runs (Tables 11-13).
    for item in UPSCALE_RUNS:
        (
            sample,
            reactor,
            temperature,
            time_min,
            argon,
            precursor_rate,
            mass_g,
            conversion,
            diameter,
            diameter_sd,
            q1,
            median,
            q3,
            carpet_um,
            raman,
            raman_gprime,
            t20,
            t50,
            t70,
            t_delta,
            residue,
        ) = item
        code = f"U{sample:02d}"
        run_id = f"{SOURCE_ID}_{code}"
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                code,
                (
                    f"scale-up sample {sample}; {reactor} reactor; "
                    f"{temperature} C; {time_min} min; {argon} L/min Ar"
                ),
                (
                    f"Ethylbenzene/5 wt.% ferrocene AACVD; {mass_g} g MWCNTs, "
                    f"{conversion}% conversion, {carpet_um} micrometer maximum carpet."
                ),
            )
        )
        tables["catalyst_system"].append(
            floating_catalyst(run_id, "Fe", "5 wt.% ferrocene", "ferrocene")
        )
        tables["reactor_process_gas"].append(
            common_process(
                run_id,
                "ethylbenzene",
                temperature,
                time_min,
                argon,
                precursor_rate,
                reactor,
            )
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="precursor_conversion_to_MWCNT_product",
                yield_original=f"{conversion}% precursor conversion yield",
                yield_definition_original=(
                    "mass of synthesized MWCNTs divided by mass of consumed precursor"
                ),
                yield_calculation_method="reported gravimetric definition",
                yield_value_standardized=conversion,
                yield_unit_standardized="percent",
                yield_standardization_note="Reported conversion retained.",
                secondary_result_summary=(
                    f"Total mass {mass_g} g; OD {diameter} ± {diameter_sd} nm; "
                    f"OD quartiles {q1}/{median}/{q3} nm; TGA T20/T50/T70 "
                    f"{t20}/{t50}/{t70} C and T70-T20 {t_delta} C."
                ),
                CNT_type_reported="vertically aligned MWCNTs",
                CNT_type_confirmed="MWCNTs",
                product_mixture_summary=(
                    f"As-synthesized MWCNT carpet with {residue} wt.% "
                    "residual catalyst."
                ),
                CNT_type_evidence="SEM/TEM/Raman/TGA characterization.",
                outer_diameter_mean_nm=diameter,
                outer_diameter_range_nm=f"mean {diameter} ± {diameter_sd}",
                wall_number_summary="multi-walled",
                length_summary=f"maximum carpet thickness {carpet_um} micrometers",
                morphology="straight/vertically aligned MWCNT carpet",
                alignment_or_array="vertically aligned carpet",
                Raman_ratio_type="ID/IG",
                Raman_ratio_value=raman,
                purity_basis="as-synthesized; TGA residual catalyst",
                residue_summary=(
                    f"{residue} wt.% residual catalyst; IG'/IG = {raman_gprime}"
                ),
                amorphous_carbon_level="condition-dependent; not separately quantified",
                characterization_methods="OM; SEM; TEM; Raman; TGA; XRD",
                post_treatment_or_purification="none reported",
                purification_condition="not_applicable",
            )
        )
        throughput = (
            f"{mass_g} g MWCNTs in {time_min} min; {precursor_rate} g/hr precursor; "
            + ("8.5 L reactor" if reactor == "large" else "0.2 L reactor")
        )
        tables["cost_scale_review"].append(
            common_cost(run_id, throughput, reactor)
        )
        evidence_specs = [
            ("CAT", "catalyst_system", f"{run_id}_CAT", "record_level", "SPAN_65EE7F51BEE1AD946BAB", "Ethylbenzene/5 wt.% ferrocene scale-up recipe."),
            ("PROC", "reactor_process_gas", f"{run_id}_S01", "record_level", "SPAN_5C2E33338F6544D80629", "Table 11 reactor, temperature, time, flow and precursor rate."),
            ("YIELD", "yield_quality", f"{run_id}_PROD", "primary_yield_metric;yield_original;yield_definition_original;yield_value_standardized;yield_unit_standardized;secondary_result_summary;outer_diameter_mean_nm;outer_diameter_range_nm;length_summary;alignment_or_array", "SPAN_4B94ADAC191204D99593", "Table 12 mass, conversion and morphology."),
            ("QUALITY", "yield_quality", f"{run_id}_PROD", "Raman_ratio_type;Raman_ratio_value;purity_basis;residue_summary;characterization_methods", "SPAN_F3EB1BA2DDEDF0607823", "Table 13 Raman, TGA and residual catalyst."),
            ("COST", "cost_scale_review", run_id, "record_level", "SPAN_92851443FBFA0EC96BB1", "Reactor capacity, precursor throughput and large-wafer setup."),
        ]
        for spec in evidence_specs:
            append_evidence(tables, store, run_id, *spec)

    zero_control = add_observation(
        tables,
        store,
        "ZERO_FERROCENE_CONTROL",
        "SPAN_B61AB05D8A04B36EAE66",
        (
            "A 0 wt.% ferrocene/toluene condition was used for gas-analysis "
            "control, but no corresponding characterized MWCNT product was "
            "reported; it is not represented as a formal CNT production run."
        ),
    )
    mapping = add_observation(
        tables,
        store,
        "REACTOR_MAPPING",
        "SPAN_747B1BC33B21F97A4128",
        (
            "One 800 C toluene/5 wt.% ferrocene batch was spatially mapped "
            "across thirteen substrates from -55 to 595 mm. These positions are "
            "within one physical run, not thirteen independent runs."
        ),
    )
    scale = add_observation(
        tables,
        store,
        "SCALE_UP_CONCLUSION",
        "SPAN_3FF64F05097F2D3C87C6",
        (
            "The larger reactor produced continuous 9 × 10 cm, millimeter-thick "
            "MWCNT carpets; synthesis rate and conversion improved about fivefold "
            "and twofold, respectively, with benzene/toluene by-products proposed "
            "for recycling."
        ),
    )
    gas = add_observation(
        tables,
        store,
        "GAS_ANALYSIS",
        "SPAN_FDFDCDC6C1E803E62431",
        (
            "Online mass spectrometry mapped thermocatalytic cracking fragments "
            "for all fifteen hydrocarbons; gas conversion did not consistently "
            "predict MWCNT yield."
        ),
    )

    first_run = f"{SOURCE_ID}_P01"
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_GRAPH_ONLY_001",
                SOURCE_ID,
                f"{SOURCE_ID}_F01",
                "critical_data_gap",
                "yield_quality",
                f"{SOURCE_ID}_F01_PROD",
                "yield_original",
                (
                    "Exact mass, diameter, Raman and TGA values for the ferrocene "
                    "concentration series are plotted in Figure 33 but not tabulated "
                    "in parsed text. No graph digitization was performed."
                ),
                f"EVD_{SOURCE_ID}_F01_YIELD_TREND",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SPATIAL_001",
                SOURCE_ID,
                f"{SOURCE_ID}_P03",
                "run_split_uncertainty",
                "source_run",
                f"{SOURCE_ID}_P03",
                "run_summary",
                (
                    "The reactor-mapping experiment has thirteen spatial product "
                    "positions but one shared synthesis program. Positions are kept "
                    "as evidence observations rather than independent runs."
                ),
                mapping,
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_ZERO_CONTROL_001",
                SOURCE_ID,
                f"{SOURCE_ID}_F01",
                "critical_data_gap",
                "source_run",
                f"{SOURCE_ID}_F01",
                "run_summary",
                (
                    "The 0 wt.% ferrocene condition is a gas-analysis control "
                    "without a characterized CNT product and is excluded from "
                    "formal source_run rows."
                ),
                zero_control,
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_REPEAT_CONDITIONS_001",
                SOURCE_ID,
                first_run,
                "run_split_uncertainty",
                "source_run",
                first_run,
                "run_summary",
                (
                    "Nominally similar 800 C/15 min ethylbenzene or toluene "
                    "conditions appear in different dissertation chapters and "
                    "comparison series. They are retained as distinct batches "
                    "because their reported results and experimental objectives differ."
                ),
                f"EVD_{first_run}_YIELD;{mapping}",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CATALYST_SOURCE_001",
                SOURCE_ID,
                f"{SOURCE_ID}_M02",
                "critical_data_gap",
                "yield_quality",
                f"{SOURCE_ID}_M02_PROD",
                "yield_original",
                (
                    "The text reports no improvement from nickelocene/cobaltocene "
                    "but does not tabulate exact product mass or quality values."
                ),
                f"EVD_{SOURCE_ID}_M02_YIELD",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CNT_MIXTURE_001",
                SOURCE_ID,
                f"{SOURCE_ID}_P03",
                "CNT_type_uncertainty",
                "yield_quality",
                f"{SOURCE_ID}_P03_PROD",
                "CNT_type_confirmed",
                (
                    "MWCNTs dominate, but SWCNTs/DWCNTs and fullerene-like "
                    "nanobud structures were observed near the reactor exhaust. "
                    "Spatial product identity requires independent evidence review."
                ),
                mapping,
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SCALE_CLAIM_001",
                SOURCE_ID,
                f"{SOURCE_ID}_U12",
                "definition_ambiguity",
                "cost_scale_review",
                f"{SOURCE_ID}_U12",
                "scale_level_claimed",
                (
                    "The dissertation demonstrates an 8.5 L laboratory reactor "
                    "and large carpets, while industrial/continuous production "
                    "remains a proposed future configuration."
                ),
                scale,
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_GAS_YIELD_001",
                SOURCE_ID,
                first_run,
                "definition_ambiguity",
                "yield_quality",
                f"{first_run}_PROD",
                "yield_definition_original",
                (
                    "Thermocatalytic gas cracking intensity is mechanistic "
                    "evidence and must not be substituted for precursor conversion "
                    "yield or MWCNT mass."
                ),
                gas,
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
