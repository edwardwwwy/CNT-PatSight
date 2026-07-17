#!/usr/bin/env python3
"""Build the third evidence-grounded A-class extraction batch."""
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


BATCH_NUMBER = 3
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_A590E23A531DD9BE"


CONFIGURATIONS = [
    {
        "code": "R01",
        "mode": "CH4",
        "catalyst": "LaNi5",
        "temperature": 650,
        "product": "CNTs and CNFs; one measured CNT had 60 nm outer diameter",
        "product_span": "SPAN_0628A510A3AD00165589",
        "outer_mean": "60",
        "raman": "D band 1360 cm-1; G band 1600 cm-1",
    },
    {
        "code": "R02",
        "mode": "CH4",
        "catalyst": "LaNi5",
        "temperature": 750,
        "product": "well-defined MWCNTs with low amorphous carbon",
        "product_span": "SPAN_5CF8695CC84A88A96952",
        "outer_range": "16.6-26.3",
        "raman": "D band 1352 cm-1; G band 1585 cm-1; G' band 2701 cm-1",
        "outlet": "13.65% H2; 28.02% unknown; 58.33% CH4",
    },
    {
        "code": "R03",
        "mode": "CH4",
        "catalyst": "LaNi5",
        "temperature": 850,
        "product": "well-defined MWCNTs with low amorphous carbon",
        "product_span": "SPAN_5CF8695CC84A88A96952",
        "outer_mean": "75.2",
        "raman": "D band 1354 cm-1; G band 1591 cm-1; G' band 2714 cm-1",
        "outlet": "17.52% H2; 15.02% unknown; 67.46% CH4",
    },
    {
        "code": "R04",
        "mode": "CO2",
        "catalyst": "LaNi5",
        "temperature": 650,
        "product": "MWCNTs, helical/straight CNFs and amorphous carbon",
        "product_span": "SPAN_D48802A6B2C09E4981FA",
        "raman": "D band 1352 cm-1; G band 1593 cm-1; G' band 2710 cm-1",
        "outlet": "5.33% O2; 2.02% CO; 92.65% CO2",
    },
    {
        "code": "R05",
        "mode": "CO2",
        "catalyst": "LaNi5",
        "temperature": 700,
        "product": "overlapping CNTs and CNFs with amorphous/graphitic particles",
        "product_span": "SPAN_D48802A6B2C09E4981FA",
        "raman": "D band 1360 cm-1; G band 1603 cm-1; G' band 2698 cm-1",
    },
    {
        "code": "R06",
        "mode": "CO2",
        "catalyst": "LaNi5",
        "temperature": 750,
        "product": "predominantly CNFs; CNTs were few",
        "product_span": "SPAN_F85287ED5E3C917DB959",
        "outer_mean": "72.5",
        "raman": "D band 1356 cm-1; G band 1591 cm-1; G' band 2701 cm-1",
        "outlet": "0.06% O2; 12.03% CO; 87.91% CO2",
    },
    {
        "code": "R07",
        "mode": "CO2",
        "catalyst": "LaNi5",
        "temperature": 850,
        "product": "CNFs with more distinct, longer graphitic structure",
        "product_span": "SPAN_F85287ED5E3C917DB959",
        "outer_mean": "217.5",
        "raman": "D band 1350 cm-1; G band 1591 cm-1; G' band 2685 cm-1",
    },
    {
        "code": "R08",
        "mode": "CO2",
        "catalyst": "mischmetal_nickel",
        "temperature": 800,
        "product": "hollow CNFs; relatively catalyst-free fibres, up to about 3.6 micrometres",
        "product_span": "SPAN_CA4BBBBEE5A4B0FCA9DC",
        "raman": "D-band intensity exceeded G-band intensity, indicating structural defects",
    },
    {
        "code": "R09",
        "mode": "CO2",
        "catalyst": "Pt_Al2O3",
        "temperature": 750,
        "product": "CNFs and possible CNTs; one CNF about 1.44 micrometres long",
        "product_span": "SPAN_CA4BBBBEE5A4B0FCA9DC",
        "raman": "Raman spectrum supported carbon nanostructure formation; ratio not reported",
    },
    {
        "code": "R10",
        "mode": "dry",
        "catalyst": "LaNi5",
        "temperature": 750,
        "product": "MWCNTs, including disordered tubes",
        "product_span": "SPAN_4136F93E47917DACFD62",
        "raman": "D band 1358 cm-1; G band 1593 cm-1; G' band 2710 cm-1",
        "outlet": "10.27% H2; 11.3% CO; 35.59% CH4; 42.84% CO2",
    },
    {
        "code": "R11",
        "mode": "dry",
        "catalyst": "LaNi5",
        "temperature": 850,
        "product": "CNT signal confirmed by Raman; morphology less defined at higher temperature",
        "product_span": "SPAN_D0E3E885EE67AC6C9FA9",
        "raman": "D band 1360 cm-1; G band 1601 cm-1",
        "outlet": "11.66% H2; 5.83% CO; 34.51% CH4; 48% CO2",
    },
    {
        "code": "R12",
        "mode": "dry",
        "catalyst": "LaNi5",
        "temperature": 950,
        "product": "CNTs not observed by TEM and Raman pattern did not support CNT formation",
        "product_span": "SPAN_BE5DE9A5CF018D516227",
        "raman": "non-CNT Raman pattern; peak ratio not reported",
    },
    {
        "code": "R13",
        "mode": "dry",
        "catalyst": "mischmetal_nickel",
        "temperature": 750,
        "product": "network of MWCNTs with better wall structure than LaNi5",
        "product_span": "SPAN_2415E66964846AF48B8F",
        "raman": "D band 1358 cm-1; G band 1599 cm-1; G' band 2710 cm-1",
        "outlet": "14.18% H2; 9.67% CO; 8.97% CH4; 67.18% CO2",
    },
    {
        "code": "R14",
        "mode": "dry",
        "catalyst": "mischmetal_nickel",
        "temperature": 850,
        "product": "CNTs, incompletely formed CNTs, filamentous carbon and amorphous carbon",
        "product_span": "SPAN_2415E66964846AF48B8F",
        "raman": "D band 1352 cm-1; G band 1589 cm-1; G' band 2705 cm-1",
    },
    {
        "code": "R15",
        "mode": "dry",
        "catalyst": "mischmetal_nickel",
        "temperature": 950,
        "product": "few MWCNTs; carbon deposition was small",
        "product_span": "SPAN_6126117ABF724B5FEA6F",
        "raman": "not_reported",
        "outlet": "49.51% H2; 25.21% CO; 8.61% CH4; 16.67% CO2",
    },
]


def catalyst_values(config: dict[str, Any]) -> dict[str, str]:
    catalyst = config["catalyst"]
    if catalyst == "LaNi5":
        return {
            "catalyst_label": "lanthanum nickel alloy (LaNi5)",
            "active_metals": "La; Ni",
            "support_material": "not_applicable",
            "promoter": "not_applicable",
            "metal_ratio_original": "LaNi5 formula",
            "metal_ratio_standardized": "La:Ni = 1:5",
            "phase_or_state_summary": "intermetallic lanthanum-nickel alloy",
        }
    if catalyst == "mischmetal_nickel":
        return {
            "catalyst_label": "mischmetal nickel alloy",
            "active_metals": "Ni; Ce; La; Nd",
            "support_material": "not_applicable",
            "promoter": "not_applicable",
            "metal_ratio_original": "not_reported",
            "metal_ratio_standardized": "not_reported",
            "phase_or_state_summary": (
                "Nickel alloy containing rare-earth constituents; EDS identified Ce, La and Nd."
            ),
        }
    return {
        "catalyst_label": "1 wt% Pt on alumina powder",
        "active_metals": "Pt",
        "support_material": "Al2O3",
        "promoter": "not_applicable",
        "metal_ratio_original": "1 wt% Pt on alumina",
        "metal_ratio_standardized": "1 wt% Pt/Al2O3",
        "phase_or_state_summary": "supported noble-metal catalyst powder",
    }


def product_values(config: dict[str, Any]) -> dict[str, str]:
    product = str(config["product"])
    if "not observed" in product:
        reported = "no CNT"
        confirmed = "no_CNT_observed"
    elif "CNF" in product and "CNT" not in product:
        reported = "CNF"
        confirmed = "CNF"
    elif "possible CNT" in product or "few" in product.lower():
        reported = "MWCNT and CNF"
        confirmed = "uncertain_or_sparse_MWCNT"
    elif "CNF" in product:
        reported = "MWCNT and CNF"
        confirmed = "mixed_MWCNT_CNF"
    else:
        reported = "MWCNT"
        confirmed = "MWCNT"
    outlet = str(config.get("outlet") or "")
    return {
        "primary_yield_metric": (
            "outlet_gas_composition_and_product_identity"
            if outlet
            else "product_identity"
        ),
        "yield_original": (
            f"Outlet gas composition: {outlet}; product: {product}"
            if outlet
            else product
        ),
        "yield_definition_original": (
            "GC outlet composition percentages; not a CNT mass yield or feed conversion."
            if outlet
            else "Qualitative TEM/Raman product identity; no mass yield reported."
        ),
        "yield_calculation_method": (
            "Exit-gas GC composition and TEM/Raman characterization"
            if outlet
            else "TEM/Raman characterization"
        ),
        "yield_value_standardized": "not_reported",
        "yield_unit_standardized": "not_applicable",
        "secondary_result_summary": str(config["raman"]),
        "CNT_type_reported": reported,
        "CNT_type_confirmed": confirmed,
        "product_mixture_summary": product,
        "CNT_type_evidence": "TEM/HMTEM and Raman spectroscopy",
        "outer_diameter_mean_nm": str(config.get("outer_mean") or "not_reported"),
        "outer_diameter_range_nm": str(config.get("outer_range") or "not_reported"),
        "wall_number_summary": (
            "multiple concentric walls reported"
            if "MWCNT" in reported
            else "not_reported"
        ),
        "length_summary": (
            "several hundred nanometres to several micrometres"
            if config["mode"] == "CH4"
            else (
                "up to about 3.6 micrometres"
                if config["code"] == "R08"
                else (
                    "about 1.44 micrometres for one CNF"
                    if config["code"] == "R09"
                    else "not_reported"
                )
            )
        ),
        "morphology": product,
        "Raman_ratio_type": "not_reported",
        "Raman_ratio_value": "not_reported",
        "Raman_laser_wavelength_nm": "514.5",
        "amorphous_carbon_level": (
            "low"
            if config["mode"] == "CH4"
            else (
                "present"
                if config["code"] in {"R04", "R05", "R14"}
                else "not_reported"
            )
        ),
        "characterization_methods": "TEM; HMTEM; Raman spectroscopy; GC",
    }


def add_observation(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    evidence_id: str,
    span_id: str,
    summary: str,
) -> None:
    item = evidence_row(
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
    item["evidence_type"] = "source_observation"
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
                "Thesis experimental chapters: supplied catalysts, CCVD conditions, "
                "TEM/HMTEM, Raman, GC, kinetics and scale/cost observations."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = (
        f"data/interim/parsed_text/{SOURCE_ID}/full_text.txt"
    )
    master["notes"] += " Source document is a university thesis."

    for config in CONFIGURATIONS:
        run_id = f"{SOURCE_ID}_{config['code']}"
        mode = str(config["mode"])
        catalyst = str(config["catalyst"])
        temperature = int(config["temperature"])
        catalyst_label = catalyst_values(config)["catalyst_label"]
        feed_label = {
            "CH4": "CH4 decomposition",
            "CO2": "CO2 decomposition",
            "dry": "CH4/CO2 dry reforming",
        }[mode]
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                str(config["code"]),
                f"{catalyst_label}; {feed_label}; {temperature} C",
                f"{feed_label} over {catalyst_label} at {temperature} C; {config['product']}.",
                "medium",
            )
        )
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                **catalyst_values(config),
                precursor_summary="commercial catalyst used as supplied",
                preparation_method="commercial_as_received",
                preparation_modifier="not_applicable",
                preparation_detail="Used as supplied by Sigma-Aldrich without further pretreatment.",
                drying_condition="not_applicable",
                calcination_condition="not_applicable",
                reduction_condition="not_applicable",
                activation_condition="not_applicable",
                post_preparation_condition="as_received",
                deactivation_summary=(
                    "High-temperature dry-reforming samples showed limited carbon deposition."
                    if mode == "dry"
                    else "not_reported"
                ),
            )
        )

        loading = "2.5" if catalyst == "Pt_Al2O3" else "10"
        reactor_material = "mullite" if mode != "dry" else "quartz"
        reactor_size = (
            "50 mm inner diameter; 1050 mm length"
            if mode != "dry"
            else "50 mm inner diameter; 1000 mm length"
        )
        setup = (
            "Catalyst on quartz wool, 28 cm from tube bottom, in a vertical electric furnace."
            if mode != "dry"
            else "Catalyst on a 40-90 micrometre quartz frit at the centre of a vertical tube."
        )
        tables["reactor_process_gas"].append(
            process_row(
                run_id,
                1,
                "argon_purge",
                reactor_type="vertical CCVD tube reactor",
                reactor_material=reactor_material,
                reactor_size_summary=reactor_size,
                reactor_setup_summary=setup,
                catalyst_loading_mass_g="not_reported",
                pressure_original="not_reported",
                pressure_kPa="not_reported",
                inert_gas="Ar",
                inert_gas_flow_original="not_reported",
                gas_composition_summary="Argon purge before experimental run.",
            )
        )
        growth = {
            "reactor_type": "vertical CCVD tube reactor",
            "reactor_material": reactor_material,
            "reactor_size_summary": reactor_size,
            "reactor_setup_summary": setup,
            "catalyst_loading_mass_g": loading,
            "temperature_setpoint_C": str(temperature),
            "holding_time_min": "60",
            "pressure_original": "not_reported",
            "pressure_kPa": "not_reported",
            "inert_gas": "not_applicable",
            "reducing_gas": "not_applicable",
            "GHSV_or_residence_time": "not_reported",
        }
        if mode == "CH4":
            growth.update(
                carbon_source="CH4",
                carbon_source_flow_original="487 mL/min",
                carbon_source_flow_sccm="487",
                cofeed_or_reactive_gas="not_applicable",
                total_flow_original="487 mL/min",
                total_flow_sccm="487",
                gas_composition_summary="UHP CH4 feed",
            )
        elif mode == "CO2":
            growth.update(
                carbon_source="CO2",
                carbon_source_flow_original="487 mL/min",
                carbon_source_flow_sccm="487",
                cofeed_or_reactive_gas="not_applicable",
                total_flow_original="487 mL/min",
                total_flow_sccm="487",
                gas_composition_summary="UHP CO2 feed",
            )
        else:
            growth.update(
                carbon_source="CH4",
                carbon_source_flow_original="CH4 487 mL/min",
                carbon_source_flow_sccm="487",
                cofeed_or_reactive_gas="CO2",
                cofeed_flow_original="CO2 487 mL/min",
                cofeed_flow_sccm="487",
                total_flow_original="CH4 487 + CO2 487 mL/min",
                total_flow_sccm="974",
                gas_composition_summary="Equal-flow UHP CH4 and CO2",
            )
        tables["reactor_process_gas"].append(
            process_row(run_id, 2, "CCVD_growth", **growth)
        )
        tables["yield_quality"].append(yield_row(run_id, **product_values(config)))

        scale_issue = (
            "High reaction temperature and satisfactory CO2 conversion were identified as scale-up cost concerns."
            if mode in {"CO2", "dry"}
            else "not_reported"
        )
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                reactor_capacity_or_throughput=f"{loading} g catalyst; 60 min laboratory run",
                continuous_operation_time_h="1",
                catalyst_lifetime_or_reuse="not_reported",
                scale_up_issue=scale_issue,
                cost_driver_summary=(
                    "Noble-metal Pt cost may negate the economic benefit of using CO2."
                    if catalyst == "Pt_Al2O3"
                    else "No quantitative catalyst or operating cost reported."
                ),
                safety_risk="High-temperature operation; gas-specific safety details not quantified.",
                emission_or_waste="Exit gas characterized by GC; carbon remained mixed with catalyst.",
            )
        )

        table_span = "SPAN_5A610C4B74CF8BFC0064"
        setup_span = (
            "SPAN_BA94862594EBAF556715"
            if mode == "dry"
            else "SPAN_F689D7BE4646B0DD71CE"
        )
        evidence_specs = [
            (
                "CAT_ID",
                "catalyst_system",
                f"{run_id}_CAT",
                "catalyst_label;active_metals;support_material;promoter;metal_ratio_original;metal_ratio_standardized",
                table_span,
                "Table 3.1 identifies catalyst and experimental condition.",
            ),
            (
                "CAT_USE",
                "catalyst_system",
                f"{run_id}_CAT",
                "precursor_summary;preparation_method;preparation_detail;post_preparation_condition",
                "SPAN_F689D7BE4646B0DD71CE",
                "Commercial catalysts were used as supplied without pretreatment.",
            ),
            (
                "PURGE",
                "reactor_process_gas",
                f"{run_id}_S01",
                "reactor_type;reactor_material;reactor_size_summary;reactor_setup_summary;inert_gas;gas_composition_summary",
                "SPAN_F689D7BE4646B0DD71CE",
                "Vertical reactor setup and pre-run argon purge.",
            ),
            (
                "GROWTH_SETUP",
                "reactor_process_gas",
                f"{run_id}_S02",
                "reactor_type;reactor_material;reactor_size_summary;reactor_setup_summary",
                setup_span,
                "Reported CCVD reactor configuration.",
            ),
            (
                "GROWTH_LOADING",
                "reactor_process_gas",
                f"{run_id}_S02",
                "catalyst_loading_mass_g",
                (
                    table_span
                    if catalyst == "Pt_Al2O3"
                    else "SPAN_F689D7BE4646B0DD71CE"
                ),
                "Reported catalyst charge.",
            ),
            (
                "GROWTH_CONDITION",
                "reactor_process_gas",
                f"{run_id}_S02",
                "temperature_setpoint_C;holding_time_min;carbon_source;carbon_source_flow_original;cofeed_or_reactive_gas;cofeed_flow_original;total_flow_original;gas_composition_summary",
                table_span,
                "Table 3.1 reports temperature, catalyst, feed flows and 60-minute duration.",
            ),
            (
                "PRODUCT",
                "yield_quality",
                f"{run_id}_PROD",
                "yield_original;secondary_result_summary;CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;outer_diameter_mean_nm;outer_diameter_range_nm;wall_number_summary;length_summary;morphology;amorphous_carbon_level",
                str(config["product_span"]),
                "TEM/HMTEM or Raman evidence for the run-specific carbon product.",
            ),
            (
                "RAMAN_METHOD",
                "yield_quality",
                f"{run_id}_PROD",
                "Raman_laser_wavelength_nm;characterization_methods",
                "SPAN_5EAC947BF67F12DFCA39",
                "Raman excitation wavelength and analytical method.",
            ),
            (
                "SCALE",
                "cost_scale_review",
                run_id,
                "scale_level_demonstrated;reactor_capacity_or_throughput;continuous_operation_time_h",
                table_span,
                "Laboratory catalyst charge and run duration.",
            ),
        ]
        if config.get("outlet"):
            evidence_specs.append(
                (
                    "OUTLET",
                    "yield_quality",
                    f"{run_id}_PROD",
                    "primary_yield_metric;yield_original;yield_definition_original;yield_calculation_method",
                    "SPAN_0A7C025742C55E0A8B9B",
                    "Table 4.1 reports outlet-gas percentages and carbon-product identity.",
                )
            )
        if catalyst == "mischmetal_nickel":
            evidence_specs.append(
                (
                    "MISCHMETAL",
                    "catalyst_system",
                    f"{run_id}_CAT",
                    "active_metals;phase_or_state_summary;deactivation_summary",
                    "SPAN_0E0978489B7C59D82203",
                    "EDS and discussion identify Ce, La and Nd and limited coking.",
                )
            )
        if catalyst == "Pt_Al2O3":
            evidence_specs.append(
                (
                    "PT_COST",
                    "cost_scale_review",
                    run_id,
                    "scale_up_issue;cost_driver_summary",
                    "SPAN_9B9174710A95F33B8930",
                    "The source explicitly flags the high cost of the Pt catalyst.",
                )
            )
        elif mode in {"CO2", "dry"}:
            evidence_specs.append(
                (
                    "SCALE_COST",
                    "cost_scale_review",
                    run_id,
                    "scale_up_issue;cost_driver_summary",
                    "SPAN_86263446FAE67016FE03",
                    "The thesis flags industrial cost for satisfactory CO2 conversion.",
                )
            )
        for suffix, table, record_id, fields, span_id, summary in evidence_specs:
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

    add_observation(
        tables,
        store,
        f"EVD_{SOURCE_ID}_OBS_KINETIC_MATRIX",
        "SPAN_BA94862594EBAF556715",
        (
            "Kinetic matrix varied one dry-reforming feed from 154 to 927 mL/min "
            "at fixed 308 mL/min counterpart and 750, 800 and 850 C."
        ),
    )
    add_observation(
        tables,
        store,
        f"EVD_{SOURCE_ID}_OBS_ACTIVATION_ENERGY",
        "SPAN_9AB3E883623C9CA1A36D",
        (
            "Apparent activation energies: CH4 consumption 41.7, CO2 consumption "
            "47.5, H2 production 54.5 and CO production 47.5 kJ/mol."
        ),
    )
    add_observation(
        tables,
        store,
        f"EVD_{SOURCE_ID}_OBS_INDUSTRIAL_COST",
        "SPAN_86263446FAE67016FE03",
        "Industrial operation may be costly when targeting satisfactory CO2 conversion.",
    )

    first_run = f"{SOURCE_ID}_R01"
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_TABLE_COLUMNS_001",
                SOURCE_ID,
                first_run,
                "run_split_uncertainty",
                "reactor_process_gas",
                f"{first_run}_S02",
                "carbon_source_flow_original",
                (
                    "Plain-text extraction of Table 3.1 loses blank CO2/CH4 cells. "
                    "Single-gas assignments were reconstructed from chapter headings "
                    "and run-specific results and require PDF-table verification."
                ),
                f"EVD_{first_run}_GROWTH_CONDITION",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_OUTLET_BASIS_001",
                SOURCE_ID,
                f"{SOURCE_ID}_R02",
                "definition_ambiguity",
                "yield_quality",
                f"{SOURCE_ID}_R02_PROD",
                "yield_original",
                (
                    "Table 4.1 percentages are outlet-gas composition, not feed "
                    "conversion, CNT yield or carbon efficiency; no conversion was inferred."
                ),
                f"EVD_{SOURCE_ID}_R02_OUTLET",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_KINETIC_RUNS_001",
                SOURCE_ID,
                f"{SOURCE_ID}_R10",
                "run_split_uncertainty",
                "source_run",
                f"{SOURCE_ID}_R10",
                "run_summary",
                (
                    "The 24-condition kinetic flow matrix has gas-rate results but no "
                    "condition-specific CNT product mapping, so it remains a source "
                    "observation rather than fabricated CNT production runs."
                ),
                f"EVD_{SOURCE_ID}_OBS_KINETIC_MATRIX",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CATALYST_LABEL_001",
                SOURCE_ID,
                f"{SOURCE_ID}_R09",
                "critical_data_gap",
                "source_run",
                f"{SOURCE_ID}_R09",
                "run_summary",
                (
                    "Table 3.1 also contains a 750 C condition transcribed as "
                    "'Ni (2.5g) & LaO5 (2.5g)' without a corresponding product result; "
                    "it was not promoted to a run and requires PDF image review."
                ),
                f"EVD_{SOURCE_ID}_R09_GROWTH_CONDITION",
            ),
        ]
    )
    return tables


def main() -> None:
    metadata = load_metadata()
    store = EvidenceStore()
    try:
        metric = publish_package(
            SOURCE_ID,
            build(metadata[SOURCE_ID], store),
        )
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
