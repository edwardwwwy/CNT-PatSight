#!/usr/bin/env python3
"""Build the fourth evidence-grounded A-class extraction batch."""
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


BATCH_NUMBER = 4
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_02606F92F0B40447"


INJECTION = [
    (1, 0, 900, 200, "Ar", 0.65),
    (2, 0, 900, 300, "Ar", 0.21),
    (3, 2, 850, 200, "Ar", 0.21),
    (4, 2, 850, 200, "Ar + 5% H2", 0.47),
    (5, 2, 850, 300, "Ar", 0.07),
    (6, 2, 900, 200, "Ar", 0.06),
    (7, 2, 900, 200, "Ar + 5% H2", 0.27),
    (8, 2, 900, 300, "Ar", 0.97),
    (9, 5, 850, 200, "Ar", 0.85),
    (10, 5, 850, 200, "Ar + 5% H2", 0.38),
    (11, 5, 850, 300, "Ar", 0.05),
    (12, 5, 900, 200, "Ar", 0.74),
    (13, 5, 900, 200, "Ar + 5% H2", 0.53),
    (14, 5, 900, 300, "Ar", 0.76),
    (15, 15, 750, 200, "Ar", 0.05),
    (16, 15, 800, 200, "Ar", 0.05),
    (17, 15, 850, 200, "Ar", 0.26),
    (18, 15, 850, 200, "Ar + 5% H2", 0.38),
    (19, 15, 850, 300, "Ar", 0.03),
    (20, 15, 900, 200, "Ar", 0.66),
    (21, 15, 900, 200, "Ar + 5% H2", 0.58),
    (22, 15, 900, 250, "Ar + 5% H2", 0.26),
    (23, 15, 900, 300, "Ar", 0.40),
    (24, 20, 900, 200, "Ar", 0.78),
    (25, 25, 900, 200, "Ar", 0.71),
]

BUBBLING = [
    (1, 5.1, 0.67, 800, 200, "RT", 60, 0.03),
    (2, 5.1, 0.67, 800, 300, "75 C", 30, 0.01),
    (3, 5.1, 0.67, 850, 200, "40 C", 30, 0.01),
    (4, 10.2, 1.34, 850, 300, "RT", 60, 0.08),
    (5, 10.2, 1.34, 900, 300, "RT", 30, 0.06),
    (6, 10.2, 1.34, 900, 300, "RT", 60, 0.06),
    (7, 10.2, 1.34, 900, 100, "RT", 30, 0.03),
]

COMPOSITION = {
    5: ("40% N-CNT/CNT; 60% amorphous carbon; 0% spheres", "high", "60"),
    11: ("80% N-CNT/CNT; 20% amorphous carbon; 0% spheres", "high", "20"),
    15: ("0% N-CNT/CNT; 100% amorphous carbon; fibres/agglomerates only", "no_CNT", "100"),
    16: ("0% N-CNT/CNT; 100% amorphous carbon; nanopearls/beads", "no_CNT", "100"),
    17: ("80% N-CNT/CNT; 20% amorphous carbon; 0% spheres", "high", "20"),
    18: ("90% N-CNT; 10% amorphous carbon; 0% spheres", "high", "10"),
    19: ("70% N-CNT/CNT; 29% amorphous carbon; 1% spheres", "high", "29"),
    20: ("30% N-CNT/CNT; 70% amorphous carbon; 0% spheres", "medium", "70"),
}

OUTER_DIAMETER = {
    5: ("84", "30"),
    11: ("62", "30"),
    19: ("47", "10"),
}
INNER_DIAMETER = {5: "26", 11: "29", 19: "20"}
BUBBLE_DIAMETER = {
    1: ("49", "20"),
    2: ("58", "10"),
    3: ("74", "10"),
    6: ("46", "20"),
}


def add_observation(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    suffix: str,
    span_id: str,
    summary: str,
) -> str:
    evidence_id = f"EVD_{SOURCE_ID}_OBS_{suffix}"
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
    return evidence_id


def add_catalyst(
    tables: dict[str, list[dict[str, str]]],
    run_id: str,
    method: str,
) -> None:
    tables["catalyst_system"].append(
        catalyst_row(
            run_id,
            catalyst_label="iron pentacarbonyl floating catalyst precursor",
            active_metals="Fe",
            support_material="not_applicable",
            promoter="not_applicable",
            metal_ratio_original="Fe(CO)5",
            metal_ratio_standardized="not_applicable",
            precursor_summary="iron pentacarbonyl, Fe(CO)5",
            preparation_method=method,
            preparation_modifier="nitrogen_doped_CNT_synthesis",
            preparation_detail=(
                "Fe(CO)5 introduced with the liquid precursor feed; iron nanoparticles form in situ."
            ),
            drying_condition="not_applicable",
            calcination_condition="not_applicable",
            reduction_condition="not_applicable",
            activation_condition="in_situ_thermal_decomposition",
            post_preparation_condition="floating/in-situ catalyst",
            phase_or_state_summary="Fe catalyst generated in situ from Fe(CO)5",
            deactivation_summary="not_reported",
        )
    )


def injection_product(exp: int, concentration: int, yield_g: float) -> dict[str, str]:
    composition, confidence, amorphous = COMPOSITION.get(
        exp,
        (
            "Recovered carbon product; individual N-CNT fraction not quantified.",
            "not_reported",
            "not_reported",
        ),
    )
    outer_mean, outer_sd = OUTER_DIAMETER.get(
        exp, ("not_reported", "not_reported")
    )
    diameter_note = (
        f" Average outer diameter {outer_mean} ± {outer_sd} nm."
        if outer_mean != "not_reported"
        else ""
    )
    return {
        "primary_yield_metric": "recovered_carbon_product_mass",
        "yield_original": f"{yield_g:g} g recovered carbon soot/product",
        "yield_definition_original": (
            "Carbon soot removed from the reactor and weighed; not a purified N-CNT mass yield."
        ),
        "yield_calculation_method": "gravimetric recovered product mass",
        "yield_value_standardized": f"{yield_g:g}",
        "yield_unit_standardized": "g_recovered_carbon_product",
        "secondary_result_summary": (
            f"Feed contained {concentration}% acetonitrile; {composition}."
            f"{diameter_note}"
        ),
        "CNT_type_reported": "nitrogen-doped CNTs and CNTs",
        "CNT_type_confirmed": (
            "no_CNT_observed"
            if confidence == "no_CNT"
            else (
                "N_CNT_or_CNT_present"
                if confidence == "high"
                else "not_reported"
            )
        ),
        "product_mixture_summary": composition,
        "CNT_type_evidence": "TEM bamboo/corrugated compartment morphology",
        "outer_diameter_mean_nm": outer_mean,
        "outer_diameter_range_nm": "not_reported",
        "inner_diameter_mean_nm": INNER_DIAMETER.get(exp, "not_reported"),
        "wall_number_summary": "multi-walled/bamboo-like N-CNTs",
        "length_summary": "not_reported",
        "morphology": composition,
        "Raman_ratio_type": "not_reported",
        "Raman_ratio_value": "not_reported",
        "Raman_laser_wavelength_nm": "514.5",
        "TGA_carbon_content_wt_percent": "not_reported",
        "purity_basis": "as-recovered mixture before run-specific acid identity was resolved",
        "residue_summary": "TGA discussion reports about 5% FeOx-related residue for selected purified samples.",
        "amorphous_carbon_level": amorphous,
        "characterization_methods": "TEM; Raman spectroscopy; TGA; gravimetry",
        "post_treatment_or_purification": "acid washing for characterized samples",
        "purification_condition": (
            "Either 55% HNO3 or 35% HCl at 80 C for 6 h; wash to about pH 7; dry at 100 C overnight."
        ),
    }


def bubble_product(exp: int, yield_g: float) -> dict[str, str]:
    description = {
        2: "N-CNTs with substantial amorphous material after bubbling solution at 75 C.",
        3: "N-CNT sample with the highest observed tube abundance; corrugated compartments.",
        7: "Very few N-CNTs at 100 mL/min carrier flow.",
    }.get(
        exp,
        "N-CNTs with corrugated compartments and generally little amorphous carbon.",
    )
    mean, sd = BUBBLE_DIAMETER.get(exp, ("not_reported", "not_reported"))
    diameter_note = (
        f" Average outer diameter {mean} ± {sd} nm."
        if mean != "not_reported"
        else ""
    )
    return {
        "primary_yield_metric": "recovered_carbon_product_mass",
        "yield_original": f"{yield_g:g} g recovered carbon product",
        "yield_definition_original": (
            "Total recovered bubbling-method carbon product; not purified N-CNT-only yield."
        ),
        "yield_calculation_method": "gravimetric recovered product mass",
        "yield_value_standardized": f"{yield_g:g}",
        "yield_unit_standardized": "g_recovered_carbon_product",
        "secondary_result_summary": f"{description}{diameter_note}",
        "CNT_type_reported": "nitrogen-doped CNTs",
        "CNT_type_confirmed": "N_CNT_present",
        "product_mixture_summary": description,
        "CNT_type_evidence": "TEM",
        "outer_diameter_mean_nm": mean,
        "outer_diameter_range_nm": "not_reported",
        "wall_number_summary": "corrugated/bamboo-like compartments",
        "length_summary": "not_reported",
        "morphology": description,
        "Raman_ratio_type": "not_reported",
        "Raman_ratio_value": "not_reported",
        "Raman_laser_wavelength_nm": "not_reported",
        "TGA_carbon_content_wt_percent": "not_reported",
        "purity_basis": "as-recovered product",
        "residue_summary": "not_reported",
        "amorphous_carbon_level": (
            "high"
            if exp == 2
            else ("low" if exp != 7 else "not_reported")
        ),
        "characterization_methods": "TEM; gravimetry",
        "post_treatment_or_purification": "not_reported",
        "purification_condition": "not_reported",
    }


def add_injection_run(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    item: tuple[int, int, int, int, str, float],
) -> None:
    exp, concentration, temperature, flow, carrier, yield_g = item
    run_id = f"{SOURCE_ID}_R{exp:02d}"
    tables["source_run"].append(
        run_row(
            SOURCE_ID,
            f"R{exp:02d}",
            (
                f"injection experiment {exp}; {concentration}% CH3CN; "
                f"{temperature} C; {flow} mL/min {carrier}"
            ),
            (
                f"Fe(CO)5/toluene/acetonitrile injection at {temperature} C "
                f"under {carrier}; recovered product {yield_g:g} g."
            ),
            "high",
        )
    )
    add_catalyst(tables, run_id, "floating_catalyst_injection_CVD")
    hydrogen = "H2" if "H2" in carrier else "not_applicable"
    tables["reactor_process_gas"].extend(
        [
            process_row(
                run_id,
                1,
                "injection_CVD_growth",
                reactor_type="horizontal quartz-tube CVD reactor",
                reactor_material="quartz",
                reactor_size_summary="32 cm diameter/width notation by 1 m length; source wording requires review",
                reactor_setup_summary="Water-cooled quartz liquid-delivery system feeding the hot zone.",
                catalyst_loading_mass_g="not_applicable",
                temperature_setpoint_C=str(temperature),
                holding_time_min="20-25",
                pressure_original="atmospheric",
                pressure_kPa="101.325",
                carbon_source="toluene",
                carbon_source_flow_original="liquid precursor solution injected at 0.80 mL/min",
                reducing_gas=hydrogen,
                reducing_gas_flow_original=(
                    f"5% H2 in {flow} mL/min carrier"
                    if hydrogen == "H2"
                    else "not_applicable"
                ),
                inert_gas="Ar",
                inert_gas_flow_original=f"{flow} mL/min carrier",
                inert_gas_flow_sccm=str(flow),
                cofeed_or_reactive_gas="acetonitrile",
                cofeed_flow_original=f"{concentration}% of liquid precursor feed",
                total_flow_original=f"{flow} mL/min carrier gas",
                total_flow_sccm=str(flow),
                gas_composition_summary=carrier,
                process_note=(
                    "Fe(CO)5 held near 1.3 mL; experiments marked 'a' used a 10 mL solution."
                    if exp in {5, 6, 11, 19}
                    else "Fe(CO)5 held near 1.3 mL; liquid composition varied by CH3CN percentage."
                ),
            ),
            process_row(
                run_id,
                2,
                "argon_cooling",
                reactor_type="horizontal quartz-tube CVD reactor",
                reactor_material="quartz",
                pressure_original="atmospheric",
                pressure_kPa="101.325",
                cooling_condition="cooled to room temperature under Ar",
                inert_gas="Ar",
                inert_gas_flow_original="approximately 50 mL/min",
                inert_gas_flow_sccm="50",
                gas_composition_summary="Ar cooling purge",
            ),
        ]
    )
    tables["yield_quality"].append(
        yield_row(run_id, **injection_product(exp, concentration, yield_g))
    )
    tables["cost_scale_review"].append(
        cost_row(
            run_id,
            reactor_capacity_or_throughput=(
                f"{yield_g:g} g recovered product from a 20-25 min laboratory run"
            ),
            continuous_operation_time_h="not_applicable",
            catalyst_lifetime_or_reuse="not_reported",
            batch_stability="single laboratory batch",
            scale_up_issue="Injector blockage from Fe(CO)5 decomposition was reported.",
            cost_driver_summary="Fe(CO)5, toluene, acetonitrile and optional acid purification; no quantitative cost.",
            safety_risk="not_reported",
            emission_or_waste="Acid wash and iron-containing residue for characterized samples.",
        )
    )
    table_span = (
        "SPAN_EA059F232277B18C56AB"
        if exp <= 17
        else "SPAN_F6A619141DE1D67D659E"
    )
    specs = [
        (
            "CAT",
            "catalyst_system",
            f"{run_id}_CAT",
            "catalyst_label;active_metals;metal_ratio_original;precursor_summary;preparation_method;preparation_detail;activation_condition",
            "SPAN_30104D36DD0C6B4D83A5",
            "Fe(CO)5 liquid precursor and injection procedure.",
        ),
        (
            "GROWTH_PROCEDURE",
            "reactor_process_gas",
            f"{run_id}_S01",
            "reactor_type;reactor_material;reactor_size_summary;reactor_setup_summary;holding_time_min;pressure_original;carbon_source;carbon_source_flow_original;cofeed_or_reactive_gas",
            "SPAN_39EE783EBE188727B2F7",
            "Typical injection-CVD apparatus, liquid rate, pressure and duration.",
        ),
        (
            "GROWTH_CONDITION",
            "reactor_process_gas",
            f"{run_id}_S01",
            "temperature_setpoint_C;reducing_gas;reducing_gas_flow_original;inert_gas;inert_gas_flow_original;cofeed_flow_original;total_flow_original;gas_composition_summary",
            table_span,
            "Experiment-specific CH3CN concentration, temperature, carrier and flow.",
        ),
        (
            "COOLING",
            "reactor_process_gas",
            f"{run_id}_S02",
            "pressure_original;cooling_condition;inert_gas;inert_gas_flow_original;gas_composition_summary",
            "SPAN_39EE783EBE188727B2F7",
            "Post-reaction argon cooling conditions.",
        ),
        (
            "YIELD",
            "yield_quality",
            f"{run_id}_PROD",
            "primary_yield_metric;yield_original;yield_definition_original;yield_calculation_method;yield_value_standardized;yield_unit_standardized",
            table_span,
            "Experiment-specific recovered carbon-product mass.",
        ),
        (
            "PURIFICATION",
            "yield_quality",
            f"{run_id}_PROD",
            "purity_basis;residue_summary;post_treatment_or_purification;purification_condition",
            "SPAN_BDC0DA0183B38A898401",
            "Acid purification alternatives and thermal/washing sequence.",
        ),
        (
            "RAMAN_METHOD",
            "yield_quality",
            f"{run_id}_PROD",
            "Raman_laser_wavelength_nm;characterization_methods",
            "SPAN_AE9DA1756EA2EF3666D4",
            "Raman excitation wavelength and TEM/TGA/Raman methods.",
        ),
        (
            "SCALE",
            "cost_scale_review",
            run_id,
            "scale_level_demonstrated;reactor_capacity_or_throughput;batch_stability;scale_up_issue;cost_driver_summary;emission_or_waste",
            "SPAN_30104D36DD0C6B4D83A5",
            "Laboratory injection batch and material handling context.",
        ),
    ]
    detail_span = None
    if exp in {5, 11, 19}:
        detail_span = "SPAN_FC105575ACEDEA8AF94F"
    if exp in {15, 16, 17, 20}:
        detail_span = "SPAN_5FD577658A9ADC67DFE4"
    if exp in {17, 18}:
        detail_span = "SPAN_4D56FF0F5BFA2B5ED5F6"
    if detail_span:
        specs.append(
            (
                "PRODUCT_DETAIL",
                "yield_quality",
                f"{run_id}_PROD",
                "secondary_result_summary;CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;morphology;amorphous_carbon_level",
                detail_span,
                "TEM-derived product composition for this comparison run.",
            )
        )
    if exp in OUTER_DIAMETER:
        specs.extend(
            [
                (
                    "OUTER",
                    "yield_quality",
                    f"{run_id}_PROD",
                    "outer_diameter_mean_nm;outer_diameter_range_nm",
                    "SPAN_B985454C7C180A257C9E",
                    "Concentration-series average outer diameter.",
                ),
                (
                    "INNER",
                    "yield_quality",
                    f"{run_id}_PROD",
                    "inner_diameter_mean_nm",
                    "SPAN_FAD8A8AC82AC99E06C8D",
                    "Concentration-series average inner diameter.",
                ),
            ]
        )
    for suffix, table, record_id, fields, span_id, summary in specs:
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


def add_bubbling_run(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    item: tuple[int, float, float, int, int, str, int, float],
) -> None:
    exp, acn_ml, feco_ml, temperature, flow, solution_temp, time_min, yield_g = item
    code = 25 + exp
    run_id = f"{SOURCE_ID}_R{code:02d}"
    tables["source_run"].append(
        run_row(
            SOURCE_ID,
            f"R{code:02d}",
            (
                f"bubbling experiment {exp}; {temperature} C; {flow} mL/min Ar; "
                f"solution {solution_temp}; {time_min} min"
            ),
            (
                f"Ar bubbling through {acn_ml:g} mL acetonitrile and {feco_ml:g} mL "
                f"Fe(CO)5; recovered product {yield_g:g} g."
            ),
            "high",
        )
    )
    add_catalyst(tables, run_id, "floating_catalyst_bubbling_CVD")
    tables["reactor_process_gas"].append(
        process_row(
            run_id,
            1,
            "bubbling_CVD_growth",
            reactor_type="CVD reactor; bubbling precursor delivery",
            reactor_material="quartz (same study apparatus; exact reuse requires review)",
            reactor_setup_summary="Ar bubbled through mixed Fe(CO)5/acetonitrile solution.",
            catalyst_loading_mass_g="not_applicable",
            temperature_setpoint_C=str(temperature),
            temperature_program_summary=f"precursor solution temperature {solution_temp}",
            holding_time_min=str(time_min),
            pressure_original="not_reported",
            pressure_kPa="not_reported",
            carbon_source="acetonitrile/carbonyl precursor system",
            carbon_source_flow_original="not_reported",
            reducing_gas="not_applicable",
            inert_gas="Ar",
            inert_gas_flow_original=f"{flow} mL/min",
            inert_gas_flow_sccm=str(flow),
            cofeed_or_reactive_gas="Fe(CO)5 catalyst precursor",
            cofeed_flow_original=f"{feco_ml:g} mL Fe(CO)5 with {acn_ml:g} mL CH3CN",
            total_flow_original=f"{flow} mL/min Ar",
            total_flow_sccm=str(flow),
            gas_composition_summary="Ar carrier through precursor solution",
        )
    )
    tables["yield_quality"].append(yield_row(run_id, **bubble_product(exp, yield_g)))
    tables["cost_scale_review"].append(
        cost_row(
            run_id,
            reactor_capacity_or_throughput=(
                f"{yield_g:g} g recovered product from {time_min} min bubbling run"
            ),
            continuous_operation_time_h="not_applicable",
            catalyst_lifetime_or_reuse="not_reported",
            batch_stability="single laboratory batch",
            scale_up_issue="Bubbling improved product quality but gave low mass yield and limited precursor-delivery control.",
            cost_driver_summary="Fe(CO)5/acetonitrile precursor and heated bubbling solution; no quantitative cost.",
            safety_risk="not_reported",
            emission_or_waste="not_reported",
        )
    )
    specs = [
        (
            "CAT",
            "catalyst_system",
            f"{run_id}_CAT",
            "catalyst_label;active_metals;metal_ratio_original;precursor_summary;preparation_method;preparation_detail;activation_condition",
            "SPAN_8FFF210844B60E98BB6A",
            "Bubbling table identifies Fe(CO)5 and acetonitrile quantities.",
        ),
        (
            "PROCESS",
            "reactor_process_gas",
            f"{run_id}_S01",
            "reactor_type;reactor_material;reactor_setup_summary;temperature_setpoint_C;temperature_program_summary;holding_time_min;carbon_source;inert_gas;inert_gas_flow_original;cofeed_or_reactive_gas;cofeed_flow_original;total_flow_original;gas_composition_summary",
            "SPAN_8FFF210844B60E98BB6A",
            "Experiment-specific bubbling conditions.",
        ),
        (
            "YIELD",
            "yield_quality",
            f"{run_id}_PROD",
            "primary_yield_metric;yield_original;yield_definition_original;yield_calculation_method;yield_value_standardized;yield_unit_standardized",
            "SPAN_5AF279C610EBDD728589",
            "Experiment-specific recovered bubbling-product mass.",
        ),
        (
            "PRODUCT",
            "yield_quality",
            f"{run_id}_PROD",
            "secondary_result_summary;CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;wall_number_summary;morphology;amorphous_carbon_level;characterization_methods",
            "SPAN_8268BF53C27AC6911D53",
            "TEM comparison of bubbling-method products.",
        ),
        (
            "SCALE",
            "cost_scale_review",
            run_id,
            "scale_level_demonstrated;reactor_capacity_or_throughput;batch_stability;scale_up_issue;cost_driver_summary",
            "SPAN_BBAEA9C5AD177FAC30F0",
            "Bubbling yield and scale-up limitations.",
        ),
    ]
    if exp in BUBBLE_DIAMETER:
        specs.append(
            (
                "OUTER",
                "yield_quality",
                f"{run_id}_PROD",
                "outer_diameter_mean_nm;outer_diameter_range_nm",
                "SPAN_BA6FA883D3B6084D4A30",
                "Bubbling-run average outer diameter.",
            )
        )
    for suffix, table, record_id, fields, span_id, summary in specs:
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


def build(
    metadata: dict[str, Any],
    store: EvidenceStore,
) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "Thesis experimental chapter: 25 injection-CVD runs, seven "
                "bubbling-CVD runs, purification, TEM, TGA and Raman comparisons."
            ),
        )
    )
    tables["source_master"][0]["local_file_path"] = (
        f"data/interim/parsed_text/{SOURCE_ID}/full_text.txt"
    )
    tables["source_master"][0]["notes"] += " Source document is a university thesis."

    for item in INJECTION:
        add_injection_run(tables, store, item)
    for item in BUBBLING:
        add_bubbling_run(tables, store, item)

    observations = [
        (
            "CONCENTRATION_COMPOSITION",
            "SPAN_FC105575ACEDEA8AF94F",
            "At 850 C and 300 mL/min, 2%, 5% and 15% CH3CN samples contained 40%, 80% and 70% N-CNT/CNT respectively.",
        ),
        (
            "BAMBOO_DISTANCE",
            "SPAN_658A8E7E4E126B0AFB95",
            "At 900 C and 200 mL/min, average bamboo-compartment spacing decreased from 28±8 to 22±10 to 9±8 nm for 2%, 5% and 15% CH3CN.",
        ),
        (
            "TGA",
            "SPAN_C6FA1EA272A61380DC83",
            "Selected 0%, 5%, 15% and 25% CH3CN samples decomposed at 741, 641, 693 and 572 C; selected purified samples retained about 5% FeOx-related residue.",
        ),
        (
            "RAMAN",
            "SPAN_0C554A00E093F9C5BD4C",
            "ID/IG ratios for 2%, 5%, 15%, 20% and 25% CH3CN samples were 0.84±0.05, 0.79±0.05, 0.75±0.05, 0.75±0.05 and 0.92±0.05.",
        ),
        (
            "TEMPERATURE",
            "SPAN_5FD577658A9ADC67DFE4",
            "For the 15% concentration series, 750 and 800 C produced no tubes, while 850 and 900 C produced N-CNT/CNT fractions of 80% and 30%.",
        ),
        (
            "COMPARTMENT_CONFLICT",
            "SPAN_18009FA1C92E157A152C",
            "A separate temperature table reports 15% CH3CN bamboo spacing of 6 nm at 850 C and 5 nm at 900 C.",
        ),
    ]
    observation_ids = {
        suffix: add_observation(tables, store, suffix, span, summary)
        for suffix, span, summary in observations
    }

    first_run = f"{SOURCE_ID}_R01"
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_BASIS_001",
                SOURCE_ID,
                first_run,
                "definition_ambiguity",
                "yield_quality",
                f"{first_run}_PROD",
                "yield_original",
                (
                    "Table 3.2 and Table 3.14 yield values are total recovered carbon "
                    "product/soot masses, not purified N-CNT yield or g/gcat."
                ),
                f"EVD_{first_run}_YIELD",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_ACID_IDENTITY_001",
                SOURCE_ID,
                first_run,
                "critical_data_gap",
                "yield_quality",
                f"{first_run}_PROD",
                "purification_condition",
                (
                    "The thesis states either HNO3 or HCl purification but does not "
                    "identify the acid used for each injection run."
                ),
                f"EVD_{first_run}_PURIFICATION",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CHARACTERIZATION_MAPPING_001",
                SOURCE_ID,
                f"{SOURCE_ID}_R05",
                "run_split_uncertainty",
                "yield_quality",
                f"{SOURCE_ID}_R05_PROD",
                "secondary_result_summary",
                (
                    "TGA and Raman tables are concentration-level comparisons without "
                    "complete run identifiers; values are retained as source observations "
                    "rather than silently assigned to every matching run."
                ),
                (
                    f"{observation_ids['TGA']};"
                    f"{observation_ids['RAMAN']}"
                ),
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_TABLE39_OCR_001",
                SOURCE_ID,
                f"{SOURCE_ID}_R15",
                "source_conflict",
                "yield_quality",
                f"{SOURCE_ID}_R15_PROD",
                "product_mixture_summary",
                (
                    "Parsed Table 3.9 displays '2%' CH3CN, but the narrative explicitly "
                    "maps the four temperature runs to Table 3.2 entries 15, 16, 17 and "
                    "20, all of which are 15%; PDF image verification is required."
                ),
                observation_ids["TEMPERATURE"],
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_BAMBOO_DISTANCE_001",
                SOURCE_ID,
                f"{SOURCE_ID}_R20",
                "source_conflict",
                "yield_quality",
                f"{SOURCE_ID}_R20_PROD",
                "length_summary",
                (
                    "The 15%/900 C bamboo spacing is 9±8 nm in the concentration table "
                    "but 5 nm in the separate temperature table; both are preserved as "
                    "source observations pending context review."
                ),
                (
                    f"{observation_ids['BAMBOO_DISTANCE']};"
                    f"{observation_ids['COMPARTMENT_CONFLICT']}"
                ),
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_BUBBLE_CARBON_SOURCE_001",
                SOURCE_ID,
                f"{SOURCE_ID}_R26",
                "definition_ambiguity",
                "reactor_process_gas",
                f"{SOURCE_ID}_R26_S01",
                "carbon_source",
                (
                    "The bubbling method omits toluene and uses Fe(CO)5/acetonitrile; "
                    "the exact carbon contribution of acetonitrile versus carbonyl "
                    "precursor is not resolved."
                ),
                f"EVD_{SOURCE_ID}_R26_PROCESS",
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
