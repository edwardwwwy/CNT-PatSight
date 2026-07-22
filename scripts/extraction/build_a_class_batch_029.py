#!/usr/bin/env python3
"""Build the twenty-ninth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 29
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ID = "LIT_6B3D416B1699661A"
PDF_REF = "data/raw/literature/pdf/LIT_6B3D416B1699661A_9514e4d34e96.pdf"
SI_REF = (
        "data/raw/literature/supplements/LIT_6B3D416B1699661A/"
    "41467_2026_69501_MOESM1_ESM.pdf"
)
SOURCE_DATA_REF = (
        "data/raw/literature/supplements/LIT_6B3D416B1699661A/"
    "41467_2026_69501_MOESM4_ESM.xlsx"
)

METHOD_SPAN = "SPAN_A02BED083CAC4B62D3B9"
LEACH_SPAN = "SPAN_F4370CE907C92FB98201"
PET_EFFECT_SPAN = "SPAN_4A559A79F9DAC21C2B2F"
RATIO_RESULT_SPAN = "SPAN_28DC540CB17B2911590C"
GAS_TGA_SPAN = "SPAN_4E6D694260DD05088E81"
HEAT_SPAN = "SPAN_B83C8C4AC53DD8647C1C"
CONDUCTIVITY_SPAN = "SPAN_590AA359F4DA52EDBB52"
UNIVERSAL_SPAN = "SPAN_8F2C7B817E24883C3E2F"
LCA_SPAN = "SPAN_9D0739E83CD5FB9EDA05"
COST_SPAN = "SPAN_1F9DFFD3A4A452D83F07"


RATIO_RUNS = [
    {
        "code": "NCM811_HDPE_550_R1_30_0",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:30:0",
        "temperature": 550,
        "pet": 0,
        "li": 81.4,
        "summary": (
            "No-PET control at NCM811/PE/PET 1:30:0, 550 C for 5 h. "
            "The product was a carbon-coated 10-15 micrometre structure, "
            "with catalyst deactivation and Li leaching efficiency 81.4%."
        ),
        "cnt": False,
    },
    {
        "code": "NCM811_HDPE_550_R1_30_0P5",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:30:0.5",
        "temperature": 550,
        "pet": 0.5,
        "summary": (
            "Intermediate PET-addition condition at NCM811/PE/PET "
            "1:30:0.5, 550 C for 5 h; SEM was reported in Supplementary "
            "Fig. 5, but no numeric CNT conversion was assigned."
        ),
        "cnt": True,
    },
    {
        "code": "NCM811_HDPE_550_R1_3_1",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:3:1",
        "temperature": 550,
        "pet": 1,
        "summary": (
            "NCM811/PE/PET 1:3:1 at 550 C for 5 h; SEM documents the "
            "ratio-screening product, with no exact carbon conversion reported."
        ),
        "cnt": True,
    },
    {
        "code": "NCM811_HDPE_550_R1_10_1",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:10:1",
        "temperature": 550,
        "pet": 1,
        "summary": (
            "NCM811/PE/PET 1:10:1 at 550 C for 5 h; SEM documents the "
            "ratio-screening product, with no exact carbon conversion reported."
        ),
        "cnt": True,
    },
    {
        "code": "NCM811_HDPE_550_R1_20_1",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:20:1",
        "temperature": 550,
        "pet": 1,
        "summary": (
            "NCM811/PE/PET 1:20:1 at 550 C for 5 h; SEM documents the "
            "ratio-screening product, with no exact carbon conversion reported."
        ),
        "cnt": True,
    },
    {
        "code": "NCM811_HDPE_550_R1_30_1",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:30:1",
        "temperature": 550,
        "pet": 1,
        "li": 99.9,
        "carbon": 33,
        "char": 8,
        "gas": 59,
        "mwc_ratio": 1437,
        "summary": (
            "Optimal NCM811/PE/PET 1:30:1 condition at 550 C for 5 h: "
            "Li leaching 99.9%, CNT carbon conversion 33%, char 8%, gas "
            "59%, and MWCNT/NiCo mass ratio 1437%. PET-containing product "
            "weight loss before 400 C was 0.6%."
        ),
        "cnt": True,
        "tga_pre400": 0.6,
        "unheated_rl": "-10.00+/-0.18 dB at 4.62+/-0.02 mm",
        "unheated_eab": "0.11+/-0.15 GHz at 4.57+/-0 mm",
        "conductivity": 3.3049,
        "resistivity": 0.30257,
    },
    {
        "code": "NCM811_HDPE_550_R1_40_1",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:40:1",
        "temperature": 550,
        "pet": 1,
        "summary": (
            "NCM811/PE/PET 1:40:1 at 550 C for 5 h; SEM documents the "
            "ratio-screening product, with no exact carbon conversion reported."
        ),
        "cnt": True,
    },
    {
        "code": "NCM811_HDPE_500_R1_3_1",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:3:1",
        "temperature": 500,
        "pet": 1,
        "summary": (
            "NCM811/PE/PET 1:3:1 at 500 C for 5 h; XRD showed NiCo alloy "
            "and carbon, and the Li-leaching bars were approximately 99-100%."
        ),
        "cnt": True,
    },
    {
        "code": "NCM811_HDPE_500_R1_10_1",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:10:1",
        "temperature": 500,
        "pet": 1,
        "summary": (
            "NCM811/PE/PET 1:10:1 at 500 C for 5 h; XRD showed NiCo alloy "
            "and carbon, and the Li-leaching bars were approximately 99-100%."
        ),
        "cnt": True,
    },
    {
        "code": "NCM811_HDPE_500_R1_20_1",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:20:1",
        "temperature": 500,
        "pet": 1,
        "summary": (
            "NCM811/PE/PET 1:20:1 at 500 C for 5 h; XRD showed NiCo alloy "
            "and carbon, and the Li-leaching bars were approximately 99-100%."
        ),
        "cnt": True,
    },
    {
        "code": "NCM811_HDPE_500_R1_40_1",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:40:1",
        "temperature": 500,
        "pet": 1,
        "summary": (
            "NCM811/PE/PET 1:40:1 at 500 C for 5 h; XRD showed NiCo alloy "
            "and carbon, and the Li-leaching bars were approximately 94-96%."
        ),
        "cnt": True,
    },
]


UNIVERSAL_RUNS = [
    {
        "code": "NCM811_LDPE_550_R1_30_1",
        "cathode": "NCM811",
        "plastic": "LDPE",
        "carbon": 29,
        "char": 8,
        "gas": 63,
        "mwc_ratio": 1251,
        "li": 95.5,
        "li_error": 0.22053,
        "particle_mean": 44.04,
        "particle_sd": 17.74,
    },
    {
        "code": "NCM811_PP_550_R1_30_1",
        "cathode": "NCM811",
        "plastic": "PP",
        "carbon": 23,
        "char": 13,
        "gas": 64,
        "mwc_ratio": 995,
        "li": 88.8,
        "li_error": 1.09187,
        "particle_mean": 36.91,
        "particle_sd": 17.43,
    },
    {
        "code": "NCM811_PC_550_R1_30_1",
        "cathode": "NCM811",
        "plastic": "PC",
        "carbon": 36,
        "char": 43,
        "gas": 21,
        "mwc_ratio": 1353,
        "li": 99.8,
        "li_error": 0.43403,
        "particle_mean": 65.46,
        "particle_sd": 26.95,
    },
    {
        "code": "NCM811_PS_550_R1_30_1",
        "cathode": "NCM811",
        "plastic": "PS",
        "carbon": 25,
        "char": 14,
        "gas": 61,
        "mwc_ratio": 1144,
        "li": 91.6,
        "li_error": 0.67579,
        "particle_mean": 54.49,
        "particle_sd": 26.13,
    },
    {
        "code": "NCM622_HDPE_550_R1_30_1",
        "cathode": "NCM622",
        "plastic": "HDPE/PE",
        "carbon": 21,
        "char": 8,
        "gas": 71,
        "mwc_ratio": 884,
    },
    {
        "code": "NCM622_LDPE_550_R1_30_1",
        "cathode": "NCM622",
        "plastic": "LDPE",
        "carbon": 22,
        "char": 9,
        "gas": 70,
        "mwc_ratio": 934,
        "li": 99.1,
        "li_error": 1.39886,
        "particle_mean": 33.61,
        "particle_sd": 9.12,
    },
    {
        "code": "NCM622_PP_550_R1_30_1",
        "cathode": "NCM622",
        "plastic": "PP",
        "carbon": 24,
        "char": 5,
        "gas": 72,
        "mwc_ratio": 1017,
        "li": 100.8,
        "li_error": 0.61156,
        "particle_mean": 52.99,
        "particle_sd": 15.61,
    },
    {
        "code": "NCM622_PC_550_R1_30_1",
        "cathode": "NCM622",
        "plastic": "PC",
        "carbon": 24,
        "char": 51,
        "gas": 25,
        "mwc_ratio": 915,
        "li": 100.7,
        "li_error": 1.20491,
        "particle_mean": 32.05,
        "particle_sd": 7.39,
    },
    {
        "code": "NCM622_PS_550_R1_30_1",
        "cathode": "NCM622",
        "plastic": "PS",
        "carbon": 26,
        "char": 7,
        "gas": 67,
        "mwc_ratio": 1186,
        "li": 100.7,
        "li_error": 0.40769,
        "particle_mean": 47.13,
        "particle_sd": 15.74,
    },
]


HEAT_RUNS = [
    {
        "code": "NCM811_HDPE_R1_30_1_CALC500",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:30:1",
        "calcination": 500,
        "ms": 56.65,
        "hc": 193.1,
        "mr": 11.8,
        "rl": "-26.00+/-1.34 dB at 5.00+/-0 mm",
        "eab": "3.77+/-0.13 GHz at 2.30+/-0.01 mm",
    },
    {
        "code": "NCM811_HDPE_R1_30_1_CALC600",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:30:1",
        "calcination": 600,
        "ms": 43.42,
        "hc": 203.2,
        "mr": 6.06,
        "rl": "-64.99+/-2.08 dB at 2.84+/-0.07 mm",
        "eab": "5.11+/-0.07 GHz at 2.22+/-0.01 mm",
    },
    {
        "code": "NCM811_HDPE_R1_30_1_CALC700",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:30:1",
        "calcination": 700,
        "ms": 40.63,
        "hc": 354.2,
        "mr": 6.76,
        "rl": "-57.34+/-3.18 dB at 1.80+/-0.17 mm",
        "eab": "5.08+/-0.15 GHz at 1.95+/-0.02 mm",
    },
    {
        "code": "NCM811_HDPE_R1_30_1_CALC800",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:30:1",
        "calcination": 800,
        "ms": 34.20,
        "hc": 90.4,
        "mr": 4.87,
        "rl": "-67.22+/-4.15 dB at 3.41+/-0.06 mm",
        "eab": "5.41+/-0.15 GHz at 2.20+/-0.07 mm",
        "raman": 1.27,
        "conductivity": 11.282,
        "resistivity": 0.088629,
    },
    {
        "code": "NCM811_HDPE_R1_30_1_CALC900",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:30:1",
        "calcination": 900,
        "ms": 33.04,
        "hc": 144.1,
        "mr": 2.31,
        "rl": "-49.73+/-2.35 dB at 1.59+/-0.02 mm",
        "eab": "4.64+/-0.20 GHz at 1.88+/-0.04 mm",
    },
    {
        "code": "NCM622_HDPE_R1_30_1_CALC800",
        "cathode": "NCM622",
        "plastic": "HDPE/PE",
        "ratio": "1:30:1",
        "calcination": 800,
        "rl": "-58.81+/-2.67 dB at 1.94+/-0.04 mm",
        "eab": "7.02+/-0.02 GHz at 2.43+/-0.01 mm",
        "conductivity": 8.3096,
        "resistivity": 0.12034,
        "diameter": "80-100",
    },
    {
        "code": "NCM811_HDPE_R1_3_1_CALC800",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:3:1",
        "calcination": 800,
        "rl": "-7.48+/-0.02 dB at 5.00+/-0 mm",
        "eab": "0 GHz",
    },
    {
        "code": "NCM811_HDPE_R1_10_1_CALC800",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:10:1",
        "calcination": 800,
        "rl": "-13.12+/-0.39 dB at 1.67+/-0.02 mm",
        "eab": "3.75+/-0.30 GHz at 1.87+/-0.03 mm",
    },
    {
        "code": "NCM811_HDPE_R1_20_1_CALC800",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:20:1",
        "calcination": 800,
        "rl": "-18.92+/-0.83 dB at 1.73+/-0.02 mm",
        "eab": "5.07+/-0.11 GHz at 2.04+/-0.02 mm",
    },
    {
        "code": "NCM811_HDPE_R1_40_1_CALC800",
        "cathode": "NCM811",
        "plastic": "HDPE/PE",
        "ratio": "1:40:1",
        "calcination": 800,
        "rl": "-11.33+/-0.28 dB at 5.00+/-0 mm",
        "eab": "0.79+/-0.21 GHz at 4.94+/-0.08 mm",
    },
]


def alloy_label(cathode: str) -> str:
    return "(Ni8Co1)MnO" if cathode == "NCM811" else "(Ni6Co2)MnO"


def catalyst_summary(item: dict[str, Any]) -> str:
    cathode = item["cathode"]
    formula = (
        "LiNi0.8Co0.1Mn0.1O2 with Ni:Co 8:1"
        if cathode == "NCM811"
        else "LiNi0.6Co0.2Mn0.2O2 with Ni:Co 6:2"
    )
    text = (
        f"{cathode} ({formula}) was placed on stainless steel. Plastic/PET "
        "pyrolysis gas reduced the cathode to NiCo alloy plus MnO, while "
        "Li2CO3 acted as a particle-growth template."
    )
    if "particle_mean" in item:
        text += (
            f" SEM NiCo-alloy particle size was {item['particle_mean']} "
            f"+/- {item['particle_sd']} nm."
        )
    elif item.get("ratio") == "1:30:1" and item.get("cathode") == "NCM811":
        text += " The NiCo particles were reported below 100 nm."
    return text


def catalyst(item: dict[str, Any], run_id: str) -> dict[str, str]:
    cathode = item["cathode"]
    formula = "LiNi0.8Co0.1Mn0.1O2" if cathode == "NCM811" else "LiNi0.6Co0.2Mn0.2O2"
    particle_qualifier = (
        f"SEM semi-quantitative NiCo-alloy size "
        f"{item['particle_mean']} +/- {item['particle_sd']} nm; not CNT diameter"
        if "particle_mean" in item
        else (
            "Optimized system reports NiCo particles below 100 nm; "
            "not standardized because this is a catalyst-particle statement"
            if item.get("ratio") == "1:30:1"
            else "No run-specific catalyst-particle distribution reported"
        )
    )
    return catalyst_row(
        run_id,
        catalyst_label=f"spent {cathode}-derived NiCo/MnO catalyst in CNT composite",
        active_metals="Ni-Co alloy",
        support_material="MnO with transient Li2CO3 template; stainless-steel holder",
        promoter="PET-derived CO/CO2 etching gas and Li2CO3 particle-size template",
        metal_ratio_original=(
            "NCM Ni:Co = 8:1" if cathode == "NCM811" else "NCM Ni:Co = 6:2"
        ),
        metal_ratio_standardized=("Ni/Co = 8" if cathode == "NCM811" else "Ni/Co = 3"),
        precursor_summary=f"commercial {cathode}, {formula}, used as received",
        preparation_method="in-situ carbothermal/pyrolysis-gas reduction",
        preparation_modifier="PET-assisted etching and Li2CO3-templated size control",
        preparation_detail=(
            "Cathode on stainless steel above the mixed plastic/PET bed in a "
            "50 mL steel reactor."
        ),
        drying_condition="vacuum dried at 60 C for 24 h after water leaching",
        calcination_condition=(
            f"{item['calcination']} C for 1 h in Ar"
            if item.get("calcination")
            else "not_applicable before optional downstream heat treatment"
        ),
        reduction_condition=(
            f"plastic/PET pyrolysis gas at {item.get('temperature', 550)} C for 5 h"
        ),
        activation_condition="in-situ formation of nanoscale NiCo alloy",
        post_preparation_condition="80 mL water leach at 25 C for 1 h",
        catalyst_particle_size_mean_nm="",
        catalyst_particle_size_range_nm="",
        catalyst_particle_size_qualifier=particle_qualifier,
        phase_or_state_summary=f"{alloy_label(cathode)} with CNT and Li2CO3 before leaching",
        dispersion_summary="NiCo nanoparticles distributed on/in CNT product",
        deactivation_summary=(
            "Without PET, fast carbon deposition coated and deactivated the alloy; "
            "PET-derived CO/CO2 suppressed amorphous-carbon accumulation."
        ),
    )


def process_rows(item: dict[str, Any], run_id: str) -> list[dict[str, str]]:
    temperature = int(item.get("temperature", 550))
    ratio = item.get("ratio", "1:30:1")
    rows = [
        process_row(
            run_id,
            1,
            "sealed_batch_co_pyrolysis",
            reactor_type="steel batch reactor heated in muffle furnace",
            scale_level="laboratory_batch",
            reactor_material="steel",
            reactor_size_summary="50 mL",
            reactor_setup_summary=(
                "cathode on stainless steel above bottom mixed-plastic/PET bed"
            ),
            catalyst_loading_mass_g="not_reported",
            temperature_setpoint_C=str(temperature),
            temperature_range_reported_C=str(temperature),
            temperature_program_summary=f"heated at 5 C/min to {temperature} C",
            holding_time_min="300",
            heating_rate_C_min="5",
            cooling_condition="not_reported",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source=f"{item['plastic']} plus PET",
            carbon_source_flow_original=f"batch cathode/plastic/PET mass ratio {ratio}",
            reducing_gas="plastic pyrolysis gas generated in situ",
            reducing_gas_flow_original="not_applicable batch generation",
            inert_gas="not_reported for co-pyrolysis",
            inert_gas_flow_original="not_reported",
            cofeed_or_reactive_gas="PET-derived CO and CO2",
            cofeed_flow_original="not separately metered",
            total_flow_original="not_applicable sealed/batch reactor",
            gas_composition_summary=(
                "with NCM: CH4 80-90%, H2 7-8%, CO2 about 0.5%; "
                "PET gas CO2 22.8% and CO 8.33%"
            ),
            process_note=(
                "Methods allowed 0.5-4 g plastic and 0-0.1 g PET; the "
                "run-specific mass ratio is retained without inferring absolute mass."
            ),
        ),
        process_row(
            run_id,
            2,
            "water_leaching_and_filtration",
            reactor_type="100 mL beaker and membrane filtration",
            scale_level="laboratory_workup",
            reactor_material="glass beaker; hydrophilic membrane",
            reactor_size_summary="100 mL beaker; 90 mm membrane; 0.45 micrometre pore",
            reactor_setup_summary="80 mL deionized water with stirring",
            catalyst_loading_mass_g="not_applicable",
            temperature_setpoint_C="25",
            temperature_range_reported_C="25",
            temperature_program_summary="isothermal water leach",
            holding_time_min="60",
            heating_rate_C_min="not_applicable",
            cooling_condition="not_applicable",
            pressure_original="atmospheric",
            pressure_kPa="101.325",
            carbon_source="none",
            reducing_gas="none",
            inert_gas="none",
            cofeed_or_reactive_gas="80 mL deionized water",
            cofeed_flow_original="batch",
            total_flow_original="not_applicable",
            gas_composition_summary="not_applicable",
            process_note="Filtrate collected in a 100 mL volumetric flask.",
        ),
        process_row(
            run_id,
            3,
            "vacuum_drying",
            reactor_type="vacuum dryer",
            scale_level="laboratory_workup",
            reactor_material="not_reported",
            reactor_size_summary="not_reported",
            reactor_setup_summary="solid product after membrane filtration",
            catalyst_loading_mass_g="not_applicable",
            temperature_setpoint_C="60",
            temperature_range_reported_C="60",
            temperature_program_summary="vacuum drying",
            holding_time_min="1440",
            heating_rate_C_min="not_reported",
            cooling_condition="not_reported",
            pressure_original="vacuum; level not reported",
            pressure_kPa="",
            carbon_source="none",
            reducing_gas="none",
            inert_gas="none",
            cofeed_or_reactive_gas="none",
            total_flow_original="not_applicable",
            gas_composition_summary="vacuum",
            process_note="Dried solid retained as NiCo/MnO/CNT composite.",
        ),
    ]
    if item.get("calcination"):
        rows.append(
            process_row(
                run_id,
                4,
                "argon_heat_treatment",
                reactor_type="heat-treatment furnace",
                scale_level="laboratory_post_treatment",
                reactor_material="not_reported",
                reactor_size_summary="not_reported",
                reactor_setup_summary="water-leached and vacuum-dried composite",
                catalyst_loading_mass_g="not_applicable",
                temperature_setpoint_C=str(item["calcination"]),
                temperature_range_reported_C=str(item["calcination"]),
                temperature_program_summary=(
                    f"calcined at {item['calcination']} C for 1 h in Ar"
                ),
                holding_time_min="60",
                heating_rate_C_min="not_reported",
                cooling_condition="not_reported",
                pressure_original="not_reported",
                pressure_kPa="",
                carbon_source="none",
                reducing_gas="none",
                inert_gas="Ar",
                inert_gas_flow_original="not_reported",
                cofeed_or_reactive_gas="none",
                total_flow_original="not_reported",
                gas_composition_summary="Ar",
                process_note="Heat treatment removed surface amorphous carbon.",
            )
        )
    return rows


def synthesis_summary(item: dict[str, Any]) -> str:
    if "summary" in item:
        return item["summary"]
    text = (
        f"{item['cathode']}/{item['plastic']}/PET at 1:30:1, 550 C for 5 h: "
        f"CNT carbon conversion {item['carbon']}%, char {item['char']}%, "
        f"gas {item['gas']}%, and MWCNT/NiCo mass ratio "
        f"{item['mwc_ratio']}% ({item['mwc_ratio'] / 100:g} g/g NiCo)."
    )
    if "li" in item:
        text += (
            f" Li leaching was {item['li']}% +/- {item['li_error']}% "
            "from the Source Data."
        )
    if "particle_mean" in item:
        text += (
            f" NiCo-alloy SEM size was {item['particle_mean']} +/- "
            f"{item['particle_sd']} nm."
        )
    return text


def heat_summary(item: dict[str, Any]) -> str:
    text = (
        f"{item['cathode']}/{item['plastic']}/PET {item['ratio']} was "
        f"co-pyrolyzed at 550 C for 5 h, water leached, vacuum dried at "
        f"60 C for 24 h, and calcined at {item['calcination']} C for 1 h "
        f"in Ar. Average RLmin was {item['rl']}; average EAB was {item['eab']}."
    )
    if "ms" in item:
        text += (
            f" Ms {item['ms']} emu/g, Hc {item['hc']} Oe, and Mr {item['mr']} emu/g."
        )
    if "raman" in item:
        text += f" Raman ID/IG was {item['raman']}."
    if "conductivity" in item:
        text += (
            f" Conductivity {item['conductivity']} S/cm and resistivity "
            f"{item['resistivity']} ohm m."
        )
    if "diameter" in item:
        text += f" CNT diameter was about {item['diameter']} nm."
    return text


def product_row(item: dict[str, Any], run_id: str) -> dict[str, str]:
    is_heat = "calcination" in item
    summary = heat_summary(item) if is_heat else synthesis_summary(item)
    carbon = item.get("carbon")
    mwc_ratio = item.get("mwc_ratio")
    cnt = item.get("cnt", True)
    return yield_row(
        run_id,
        primary_yield_metric=(
            "post_treatment_microwave_performance"
            if is_heat
            else (
                "carbon_conversion_to_CNT_percent"
                if carbon is not None
                else "reported_product_outcome"
            )
        ),
        yield_original=(
            f"CNT carbon conversion {carbon}%"
            if carbon is not None
            else ("not quantified" if cnt else "no selective CNT yield")
        ),
        yield_definition_original=(
            "carbon in final CNT product divided by carbon in binary plastics x 100%"
            if carbon is not None
            else "No standardized mass yield reported for this condition."
        ),
        yield_calculation_method=(
            "Supplementary Text S2 carbon-balance definition"
            if carbon is not None
            else "not_reported"
        ),
        yield_value_standardized=str(carbon) if carbon is not None else "",
        yield_unit_standardized="%" if carbon is not None else "",
        yield_standardization_note=(
            "CNT-specific carbon conversion; char and gas are separate carbon fates."
            if carbon is not None
            else "Condition retained without inventing a numeric yield."
        ),
        CNT_yield_per_catalyst_g_gcat=(
            str(mwc_ratio / 100) if mwc_ratio is not None else ""
        ),
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent=(str(carbon) if carbon is not None else ""),
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=summary,
        CNT_type_reported="MWCNT" if cnt else "no selective CNT",
        CNT_type_confirmed="MWCNT" if cnt else "carbon-coated/deactivated product",
        product_mixture_summary=(
            f"{alloy_label(item['cathode'])}/MWCNT composite with residual char"
            if cnt
            else "carbon-coated transition-metal oxide/alloy product"
        ),
        CNT_type_evidence=(
            "SEM/TEM plus XRD carbon (002) peak"
            if cnt
            else "SEM carbon-coated 10-15 micrometre structure"
        ),
        SWCNT_or_few_wall_evidence_summary="multi-walled; not SWCNT",
        RBM_peak_reported="not_reported",
        outer_diameter_mean_nm="",
        outer_diameter_range_nm=item.get("diameter", ""),
        inner_diameter_mean_nm="",
        wall_number_summary="multi-walled; exact wall count not reported",
        length_summary=(
            "shorter for NCM622 than NCM811; not quantified"
            if item["cathode"] == "NCM622"
            else "broad distribution; not quantified"
        ),
        morphology=(
            "bent and entangled CNT; NiCo anchored within or at tube ends"
            if cnt
            else "10-15 micrometre carbon-coated structure"
        ),
        alignment_or_array="entangled/non-aligned" if cnt else "not_applicable",
        Raman_ratio_type="ID/IG" if item.get("raman") else "not_reported",
        Raman_ratio_value=str(item.get("raman", "")),
        Raman_laser_wavelength_nm="532" if item.get("raman") else "",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis=(
            "water-leached composite; no purified isolated-CNT fraction"
            if cnt
            else "not_applicable"
        ),
        residue_summary="NiCo alloy and MnO; char varies with plastic",
        amorphous_carbon_level=(
            "reduced after PET addition and further reduced after heat treatment"
            if cnt
            else "high; catalyst covered/deactivated"
        ),
        BET_surface_area_product_m2_g="",
        characterization_methods="SEM; TEM; XRD; Raman; TG; AAS; VNA as applicable",
        post_treatment_or_purification=(
            f"water leach, vacuum drying, then {item['calcination']} C Ar treatment"
            if is_heat
            else "water leach and vacuum drying"
        ),
        purification_condition=(
            f"80 mL water at 25 C for 1 h; 60 C vacuum dry 24 h; "
            f"{item['calcination']} C Ar 1 h"
            if is_heat
            else "80 mL water at 25 C for 1 h; 60 C vacuum dry 24 h"
        ),
        application_property_summary=(
            summary
            if is_heat
            else (
                f"Unheated RL/EAB {item['unheated_rl']}; {item['unheated_eab']}; "
                f"conductivity {item['conductivity']} S/cm; resistivity "
                f"{item['resistivity']} ohm m."
                if item.get("unheated_rl")
                else ""
            )
        ),
        notes=(
            "MWCNT/NiCo percentage is converted to g/g NiCo only; it is not "
            "yield per total composite or initial cathode mass."
            if mwc_ratio is not None
            else "No missing numeric outcome was inferred from image appearance."
        ),
    )


def cost_review(item: dict[str, Any], run_id: str) -> dict[str, str]:
    representative = item.get("code") == "NCM811_HDPE_550_R1_30_1"
    return cost_row(
        run_id,
        scale_level_demonstrated="laboratory 50 mL batch reactor",
        scale_level_claimed=(
            "modeled plant processing 20000 tonnes/year spent NCM811"
            if representative
            else "universality/condition screen; no scale demonstration"
        ),
        scale_evidence_summary=(
            "Methods used 0.5-4 g plastic and 0-0.1 g PET per batch; "
            "experiments were independently repeated three times where stated."
        ),
        reactor_capacity_or_throughput="0.5-4 g plastic; 0-0.1 g PET per batch",
        continuous_operation_time_h="",
        catalyst_lifetime_or_reuse="not_reported",
        catalyst_reuse_cycles="not_reported",
        batch_stability="three independent measurements/images where stated",
        scale_up_issue=(
            "batch heat transfer, mixed-waste variability, gas management, "
            "NiCo particle control, char separation and product-quality consistency"
        ),
        quantitative_cost_reported=(
            "modeled upcycling profit 1497.89 USD/kg"
            if representative
            else "study-level modeled economics only"
        ),
        quantitative_cost_summary=(
            "EverBatt case: product revenue 1500 USD/kg, materials cost "
            "1.53 USD/kg, total modeled profit 1497.89 USD/kg."
            if representative
            else "No run-specific measured cost."
        ),
        cost_driver_summary=(
            "NCM cathode, plastic/PET, 550 C for 5 h, water workup, "
            "60 C drying and optional 500-900 C Ar heat treatment"
        ),
        safety_risk="sealed hot plastic pyrolysis gas, CH4/H2/CO, metal-containing solids",
        emission_or_waste=(
            "modeled upcycling GWP100 0.883 kg CO2-eq per kg spent NCM811; "
            "foreground GHG 876 g CO2-eq/kg in the EverBatt comparison"
            if representative
            else "plastic pyrolysis gas, char, leachate and metal-containing solids"
        ),
        industrial_readiness_assessment=(
            "laboratory batch evidence plus modeled, not demonstrated, industrial case"
        ),
        reproduction_value="high",
        reproduction_priority="high" if representative else "medium",
        recommended_next_action=(
            "report absolute cathode mass, complete carbon balance, isolated CNT "
            "purity/yield, gas flow/pressure, batch variability and pilot operation"
        ),
        review_note=(
            "LCA and profit are scenario-model outputs, not measured economics "
            "from the 50 mL laboratory reactor."
        ),
    )


def add_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    suffix: str,
    table: str,
    record_id: str,
    span_id: str,
    locator: str,
    text: str,
    summary: str,
    *,
    object_ref: str = PDF_REF,
    evidence_type: str = "pdf_text_and_visual_transcription",
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
            "evidence_type": evidence_type,
            "source_section": locator,
            "source_locator": locator,
            "source_object_ref": object_ref,
            "evidence_text": text,
            "evidence_summary": summary,
            "notes": "Main PDF, official SI, and official Source Data were cross-checked.",
        }
    )
    tables["evidence_index"].append(item)


def add_run(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    item: dict[str, Any],
) -> str:
    run_id = f"{SOURCE_ID}_{item['code']}"
    summary = heat_summary(item) if "calcination" in item else synthesis_summary(item)
    tables["source_run"].append(
        run_row(
            SOURCE_ID,
            item["code"],
            (
                f"{item['cathode']} {item['plastic']} {item.get('ratio', '1:30:1')} "
                f"{item.get('temperature', 550)} C"
                + (
                    f" plus {item['calcination']} C Ar treatment"
                    if item.get("calcination")
                    else ""
                )
            ),
            summary,
            "high",
        )
    )
    cat = catalyst(item, run_id)
    tables["catalyst_system"].append(cat)
    stages = process_rows(item, run_id)
    tables["reactor_process_gas"].extend(stages)
    product = product_row(item, run_id)
    tables["yield_quality"].append(product)
    cost = cost_review(item, run_id)
    tables["cost_scale_review"].append(cost)

    add_evidence(
        tables,
        store,
        run_id,
        "RUN",
        "source_run",
        run_id,
        HEAT_SPAN if item.get("calcination") else UNIVERSAL_SPAN,
        "Main PDF results and official SI condition captions",
        summary,
        "Run identity and principal result.",
    )
    cat_text = catalyst_summary(item)
    add_evidence(
        tables,
        store,
        run_id,
        "CATALYST",
        "catalyst_system",
        f"{run_id}_CAT",
        METHOD_SPAN,
        "Main PDF Methods and SI Fig. 38",
        (
            f"{cat_text} Cathode on stainless steel in a 50 mL reactor; "
            "vacuum dried at 60 C for 24 h after 80 mL water leaching at "
            f"25 C for 1 h. Calcination condition: "
            f"{item.get('calcination', 'not applicable')} C; "
            f"reduction {item.get('temperature', 550)} C for 5 h."
        ),
        "In-situ NCM-derived catalyst identity, preparation and particle size.",
    )
    for stage in stages:
        if stage["stage_order"] == "1":
            span = METHOD_SPAN
            locator = "Main PDF Methods: recovery of spent LIB cathodes"
        elif stage["stage_order"] == "2":
            span = LEACH_SPAN
            locator = "Main PDF Methods: water leaching and filtration"
        elif stage["stage_order"] == "3":
            span = LEACH_SPAN
            locator = "Main PDF Methods: vacuum drying"
        else:
            span = HEAT_SPAN
            locator = "Main PDF Results and SI heat-treatment series"
        stage_text = (
            f"Stage {stage['stage_order']} {stage['stage_type']}; reactor "
            f"{stage['reactor_type']}; size {stage['reactor_size_summary']}; "
            f"setup {stage['reactor_setup_summary']}; temperature "
            f"{stage['temperature_setpoint_C']} C; range "
            f"{stage['temperature_range_reported_C']} C; program "
            f"{stage['temperature_program_summary']}; duration "
            f"{stage['holding_time_min']} min; heating rate "
            f"{stage['heating_rate_C_min']} C/min; pressure "
            f"{stage['pressure_original']} {stage['pressure_kPa']} kPa; "
            f"carbon source {stage['carbon_source']}; source amount "
            f"{stage['carbon_source_flow_original']}; inert gas "
            f"{stage['inert_gas']} {stage['inert_gas_flow_original']}; "
            f"reactive cofeed {stage['cofeed_or_reactive_gas']} "
            f"{stage['cofeed_flow_original']}; total flow "
            f"{stage['total_flow_original']}; gas "
            f"{stage['gas_composition_summary']}; note {stage['process_note']}"
        )
        add_evidence(
            tables,
            store,
            run_id,
            f"PROCESS_{stage['stage_order']}",
            "reactor_process_gas",
            stage["process_stage_id"],
            span,
            locator,
            stage_text,
            f"Process stage {stage['stage_order']} support.",
        )
    add_evidence(
        tables,
        store,
        run_id,
        "PRODUCT",
        "yield_quality",
        f"{run_id}_PROD",
        HEAT_SPAN if item.get("calcination") else UNIVERSAL_SPAN,
        (
            "SI Tables 1-2 and main Fig. 2"
            if item.get("calcination")
            else "Main results, SI Figs. 5-7 and 39-47"
        ),
        (
            f"{summary} Product fields: carbon conversion "
            f"{item.get('carbon', 'not quantified')}%; MWCNT/NiCo "
            f"{item.get('mwc_ratio', 'not quantified')}%; diameter "
            f"{item.get('diameter', 'not quantified')} nm; Raman ID/IG "
            f"{item.get('raman', 'not reported')}; Raman laser "
            f"{532 if item.get('raman') else 'not reported'} nm."
        ),
        "Yield, product identity, quality and application result.",
    )
    if item in UNIVERSAL_RUNS:
        source_text = (
            f"Official Source Data Fig.5b for {item['cathode']} {item['plastic']}: "
            f"Li leaching {item.get('li', 'not individually reported')}% "
            f"+/- {item.get('li_error', 'not reported')}%. SI Fig.47: CNT "
            f"{item['carbon']}%, char {item['char']}%, gas {item['gas']}%, "
            f"MWCNT/NiCo {item['mwc_ratio']}% or {item['mwc_ratio'] / 100:g} g/g."
        )
        add_evidence(
            tables,
            store,
            run_id,
            "PRODUCT_SOURCE_DATA",
            "yield_quality",
            f"{run_id}_PROD",
            UNIVERSAL_SPAN,
            "Official Source Data sheet Fig.5b and SI page 53",
            source_text,
            "Source-data leaching result and visually transcribed carbon balance.",
            object_ref=SOURCE_DATA_REF,
            evidence_type="official_source_data_xlsx_plus_si_visual_transcription",
        )
    if item.get("code") == "NCM811_HDPE_550_R1_30_1":
        add_evidence(
            tables,
            store,
            run_id,
            "PRODUCT_OPTIMUM",
            "yield_quality",
            f"{run_id}_PROD",
            RATIO_RESULT_SPAN,
            "Main Fig. 1 and SI Figs. 11/47; SI Table 2",
            (
                f"{summary} Unheated microwave result "
                f"{item['unheated_rl']} and {item['unheated_eab']}; "
                f"conductivity {item['conductivity']} S/cm and resistivity "
                f"{item['resistivity']} ohm m."
            ),
            "Optimized unheated product and carbon-balance result.",
        )
    cost_text = (
        "Laboratory method: 50 mL reactor, 0.5-4 g plastic and 0-0.1 g PET, "
        "550 C for 5 h, 80 mL water at 25 C for 1 h, 60 C drying for 24 h. "
        "Three independent measurements/images were reported where stated."
    )
    if item.get("code") == "NCM811_HDPE_550_R1_30_1":
        cost_text += (
            " Modeled plant capacity 20000 tonnes/year; EverBatt product "
            "revenue 1500 USD/kg, materials cost 1.53 USD/kg, profit "
            "1497.89 USD/kg; modeled GWP100 0.883 kg CO2-eq/kg spent "
            "NCM811 and foreground GHG 876 g CO2-eq/kg."
        )
    add_evidence(
        tables,
        store,
        run_id,
        "COST",
        "cost_scale_review",
        run_id,
        COST_SPAN if item.get("code") == "NCM811_HDPE_550_R1_30_1" else METHOD_SPAN,
        "Main Methods, LCA/EverBatt results and SI Tables 5-8",
        cost_text,
        "Laboratory scale and modeled economics/environment context.",
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
                "Thirty records: eleven NCM811 PE/PET ratio-temperature "
                "screening conditions, nine additional cathode/plastic "
                "universality conditions, and ten downstream Ar heat-treatment "
                "conditions. Official SI and Source Data were inspected."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_pdf_plus_official_si_and_source_data"
    master["notes"] += (
        " Official 64-page SI and Source Data XLSX were downloaded from the "
        "publisher. Raw spectra/maps are retained as source files; the eight "
        "tables capture condition-level synthesis and reported outcomes."
    )

    run_ids: dict[str, str] = {}
    for item in [*RATIO_RUNS, *UNIVERSAL_RUNS, *HEAT_RUNS]:
        run_ids[item["code"]] = add_run(tables, store, item)

    optimal = run_ids["NCM811_HDPE_550_R1_30_1"]
    ncm622_800 = run_ids["NCM622_HDPE_R1_30_1_CALC800"]
    ncm622_pp = run_ids["NCM622_PP_550_R1_30_1"]
    ratio500 = run_ids["NCM811_HDPE_500_R1_40_1"]
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_CARBON_CONVERSION_001",
                SOURCE_ID,
                optimal,
                "yield_definition",
                "yield_quality",
                f"{optimal}_PROD",
                "carbon_source_conversion_percent",
                (
                    "Carbon conversion is CCNT divided by carbon in the binary "
                    "plastics. It is not total solid yield, cathode conversion "
                    "or isolated purified-CNT yield."
                ),
                f"EVD_{optimal}_PRODUCT_OPTIMUM",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_MWCNT_NICO_001",
                SOURCE_ID,
                optimal,
                "denominator_scope",
                "yield_quality",
                f"{optimal}_PROD",
                "CNT_yield_per_catalyst_g_gcat",
                (
                    "The reported 1437% value is MWCNT mass relative to NiCo "
                    "mass calculated from NCM, not relative to total NCM, MnO, "
                    "Li2CO3 or composite mass."
                ),
                f"EVD_{optimal}_PRODUCT_OPTIMUM",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PE_HDPE_001",
                SOURCE_ID,
                optimal,
                "source_label_inconsistency",
                "reactor_process_gas",
                f"{optimal}_S01",
                "carbon_source",
                (
                    "Methods and ratio-screening figures use PE, whereas "
                    "Supplementary Fig. 47 labels the corresponding plastic "
                    "HDPE. The extraction preserves the combined label HDPE/PE."
                ),
                f"EVD_{optimal}_PROCESS_1;EVD_{optimal}_PRODUCT_OPTIMUM",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_MICROWAVE_LABEL_001",
                SOURCE_ID,
                ncm622_800,
                "cross_source_discrepancy",
                "yield_quality",
                f"{ncm622_800}_PROD",
                "application_property_summary",
                (
                    "Main-text sample labels for the 7.01 GHz and 5.22 GHz "
                    "examples conflict with SI Table 2. The structured record "
                    "uses SI Table 2 replicate-average labels and retains the "
                    "main-text discrepancy here."
                ),
                f"EVD_{ncm622_800}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PARTICLE_DIAMETER_001",
                SOURCE_ID,
                ncm622_pp,
                "dimension_semantics",
                "catalyst_system",
                f"{ncm622_pp}_CAT",
                "catalyst_particle_size_qualifier",
                (
                    "Supplementary Fig. 38 values are NiCo-alloy particle sizes "
                    "from SEM, not CNT outer diameters. The 80-100 nm CNT "
                    "diameter applies specifically to the calcined NCM622 product."
                ),
                f"EVD_{ncm622_pp}_CATALYST;EVD_{ncm622_800}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_LEACH_OVER100_001",
                SOURCE_ID,
                ncm622_pp,
                "reported_measurement_over_100",
                "yield_quality",
                f"{ncm622_pp}_PROD",
                "secondary_result_summary",
                (
                    "Official Source Data reports some Li leaching means above "
                    "100% (100.8% and 100.7%). Values are preserved with errors "
                    "and not clipped."
                ),
                f"EVD_{ncm622_pp}_PRODUCT_SOURCE_DATA",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_500C_APPROX_001",
                SOURCE_ID,
                ratio500,
                "visual_approximation",
                "yield_quality",
                f"{ratio500}_PROD",
                "secondary_result_summary",
                (
                    "The 500 C ratio-screen leaching bars are only visually "
                    "readable from Supplementary Fig. 6; approximate ranges are "
                    "retained in summaries and not standardized as exact yields."
                ),
                f"EVD_{ratio500}_PRODUCT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CARBON_PARTITION_001",
                SOURCE_ID,
                optimal,
                "pdf_visual_transcription",
                "yield_quality",
                f"{optimal}_PROD",
                "secondary_result_summary",
                (
                    "CNT/char/gas fractions and MWCNT/NiCo ratios were visually "
                    "transcribed from Supplementary Fig. 47 because they are not "
                    "included as a worksheet in the official Source Data XLSX."
                ),
                f"EVD_{optimal}_PRODUCT_OPTIMUM",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_COST_MODEL_001",
                SOURCE_ID,
                optimal,
                "modeled_not_measured",
                "cost_scale_review",
                optimal,
                "quantitative_cost_summary",
                (
                    "The 1497.89 USD/kg profit, 20000 tonne/year capacity and "
                    "LCA emissions are EverBatt/OpenLCA scenario outputs, not "
                    "measured pilot-plant results."
                ),
                f"EVD_{optimal}_COST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_ABSOLUTE_MASS_001",
                SOURCE_ID,
                optimal,
                "critical_data_gap",
                "reactor_process_gas",
                f"{optimal}_S01",
                "catalyst_loading_mass_g",
                (
                    "The methods give screening ranges of 0.5-4 g plastic and "
                    "0-0.1 g PET but do not state the absolute NCM mass for each "
                    "ratio condition; only mass ratios are structured."
                ),
                f"EVD_{optimal}_PROCESS_1",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_REPLICATES_001",
                SOURCE_ID,
                optimal,
                "replicate_grouping",
                "source_run",
                optimal,
                "run_summary",
                (
                    "Repeated SEM or microwave measurements validate one "
                    "condition and are not expanded into independent synthesis "
                    "runs. Reported averages and errors remain within the run."
                ),
                f"EVD_{optimal}_RUN",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_RAW_SOURCE_DATA_001",
                SOURCE_ID,
                optimal,
                "raw_series_retention",
                "yield_quality",
                f"{optimal}_PROD",
                "application_property_summary",
                (
                    "The official XLSX contains raw XRD, Raman, permittivity, "
                    "reflection-loss and thermal curves. These are retained as "
                    "source files rather than expanded into thousands of run rows."
                ),
                f"EVD_{optimal}_PRODUCT_OPTIMUM",
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
