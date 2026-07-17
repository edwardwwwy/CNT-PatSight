#!/usr/bin/env python3
"""Build the twenty-first evidence-grounded A-class extraction batch."""

from __future__ import annotations

import json
from itertools import product as factorial
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


BATCH_NUMBER = 21
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_3BDCD8F9895BE659"
PDF_REF = "data/raw/fulltext/pdf/LIT_3BDCD8F9895BE659_ad8a37d0aa53.pdf"

BASE_RECIPE = (
    "Co or Fe films 0.3 nm thick were evaporated onto either 100 nm SiO2 "
    "or 30 nm Al2O3 on Si. Pre-oxidized films were exposed at room "
    "temperature to 2 x 10^-5 Torr O2 for 250 s. Catalysts were annealed "
    "at 700 C in approximately 1 x 10^-8 Torr vacuum. CNT growth used "
    "2 Torr ethanol at 700 C for 5 min. A 0.5 mm graphite hot filament, "
    "when enabled, was held at 1500 C approximately 8 mm from the sample."
)

PHASE = {
    ("Fe", "SiO2", "as_deposited", "off"): (
        "After 20 s ethanol exposure, Fe was mostly oxidized with only a "
        "very small metallic Fe fraction."
    ),
    ("Fe", "SiO2", "as_deposited", "on"): (
        "After 20 s ethanol exposure, Fe partly oxidized but retained a "
        "much larger metallic Fe fraction than with the filament off."
    ),
    ("Fe", "SiO2", "oxidized", "off"): (
        "After 20 s ethanol exposure, pre-oxidized Fe remained fully oxidized."
    ),
    ("Fe", "SiO2", "oxidized", "on"): (
        "After 20 s ethanol exposure, pre-oxidized Fe partly reduced and "
        "showed a small metallic Fe peak at 706.7 eV."
    ),
    ("Fe", "Al2O3", "as_deposited", "off"): (
        "After 5 s ethanol exposure, metallic Fe partly oxidized, less "
        "strongly than the corresponding Fe/SiO2 condition."
    ),
    ("Fe", "Al2O3", "as_deposited", "on"): (
        "Carbon obscured the 5 s XPS signal; at less than 0.5 s Fe remained "
        "fully metallic while graphitic carbon formation had commenced."
    ),
    ("Fe", "Al2O3", "oxidized", "off"): (
        "After 5 s ethanol exposure, pre-oxidized Fe partly reduced and "
        "showed a small metallic Fe peak."
    ),
    ("Fe", "Al2O3", "oxidized", "on"): (
        "After 5 s ethanol exposure, pre-oxidized Fe reduced further and "
        "showed a strong metallic Fe peak at 706.7 eV."
    ),
    ("Co", "SiO2", "as_deposited", "off"): (
        "After 20 s ethanol exposure, as-deposited Co remained metallic."
    ),
    ("Co", "SiO2", "as_deposited", "on"): (
        "After 20 s ethanol exposure, as-deposited Co remained metallic."
    ),
    ("Co", "SiO2", "oxidized", "off"): (
        "After 20 s ethanol exposure, oxidized Co reduced mostly to metallic "
        "Co with only a very small Co2+ fraction."
    ),
    ("Co", "SiO2", "oxidized", "on"): (
        "After 20 s ethanol exposure, oxidized Co reduced mostly to metallic "
        "Co with only a very small Co2+ fraction."
    ),
    ("Co", "Al2O3", "as_deposited", "off"): (
        "After 5 s ethanol exposure, as-deposited Co remained metallic."
    ),
    ("Co", "Al2O3", "as_deposited", "on"): (
        "After 5 s ethanol exposure, as-deposited Co remained metallic."
    ),
    ("Co", "Al2O3", "oxidized", "off"): (
        "After 5 s ethanol exposure, oxidized Co reduced mostly to metallic "
        "Co with only a very small Co2+ fraction."
    ),
    ("Co", "Al2O3", "oxidized", "on"): (
        "After 5 s ethanol exposure, oxidized Co reduced mostly to metallic "
        "Co with only a very small Co2+ fraction."
    ),
}

OUTCOME = {
    ("Fe", "SiO2", "as_deposited", "off"): (
        "CNT mat",
        "thin entangled CNT mat; lower yield than filament-on condition",
    ),
    ("Fe", "SiO2", "as_deposited", "on"): (
        "small SWCNT forest",
        "small vertically aligned SWCNT forest",
    ),
    ("Fe", "SiO2", "oxidized", "off"): (
        "no CNT growth",
        "no observable CNT growth by SEM",
    ),
    ("Fe", "SiO2", "oxidized", "on"): (
        "CNT mat",
        "entangled CNT mat after partial catalyst reduction",
    ),
    ("Fe", "Al2O3", "as_deposited", "off"): (
        "CNT mat",
        "entangled CNT mat; higher activity than corresponding SiO2 condition",
    ),
    ("Fe", "Al2O3", "as_deposited", "on"): (
        "strongest SWCNT forest",
        "dense vertically aligned SWCNT forest; strongest growth in the matrix",
    ),
    ("Fe", "Al2O3", "oxidized", "off"): (
        "CNT mat",
        "entangled CNT mat despite partial reduction to metallic Fe",
    ),
    ("Fe", "Al2O3", "oxidized", "on"): (
        "CNT mat",
        "entangled CNT mat; did not form a SWCNT forest despite strong Fe0 peak",
    ),
    ("Co", "SiO2", "as_deposited", "off"): (
        "CNT mat",
        "entangled CNT mat; more active than pre-oxidized Co",
    ),
    ("Co", "SiO2", "as_deposited", "on"): (
        "aligned CNT forest",
        "vertically aligned CNT forest near the micrometer scale",
    ),
    ("Co", "SiO2", "oxidized", "off"): (
        "sparse CNT layer",
        "very low-yield thin CNT layer",
    ),
    ("Co", "SiO2", "oxidized", "on"): (
        "CNT mat",
        "higher-yield CNT mat than the filament-off oxidized condition",
    ),
    ("Co", "Al2O3", "as_deposited", "off"): (
        "CNT mat",
        "dense CNT mat; higher yield than corresponding SiO2 condition",
    ),
    ("Co", "Al2O3", "as_deposited", "on"): (
        "aligned CNT forest",
        "dense vertically aligned CNT forest; Fe/Al2O3 forest was factor 2 taller",
    ),
    ("Co", "Al2O3", "oxidized", "off"): (
        "CNT mat",
        "CNT mat; higher yield than corresponding SiO2 condition",
    ),
    ("Co", "Al2O3", "oxidized", "on"): (
        "aligned CNT forest",
        "vertically aligned CNT forest after reduction of oxidized Co",
    ),
}


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


def page_and_span(metal: str, support: str) -> tuple[int, str]:
    if metal == "Fe" and support == "SiO2":
        return 6, "SPAN_BF97138F72197A25F3B8"
    if metal == "Fe" and support == "Al2O3":
        return 7, "SPAN_BF97138F72197A25F3B8"
    if metal == "Co" and support == "SiO2":
        return 8, "SPAN_C366DD594A37C8669CF0"
    return 9, "SPAN_CDF3C22F41AB7C7AEE2D"


def catalyst(
    run_id: str,
    metal: str,
    support: str,
    state: str,
    filament: str,
) -> dict[str, str]:
    support_detail = "100 nm SiO2 on Si" if support == "SiO2" else "30 nm Al2O3 on Si"
    oxidation = (
        "none; used as-deposited metallic film"
        if state == "as_deposited"
        else "2 x 10^-5 Torr O2 for 250 s at room temperature"
    )
    return catalyst_row(
        run_id,
        catalyst_label=f"0.3 nm {metal} thin film on {support}",
        active_metals=metal,
        support_material=support_detail,
        promoter="not_applicable",
        metal_ratio_original=f"{metal} 0.3 nm; support {support_detail}",
        metal_ratio_standardized="not_applicable_thickness_stack",
        precursor_summary=f"elemental {metal} evaporated thin film",
        preparation_method="physical_vapor_deposition",
        preparation_modifier=(
            "as-deposited"
            if state == "as_deposited"
            else "pre-oxidized before anneal and growth"
        ),
        preparation_detail=(
            f"0.3 nm {metal} film evaporated onto {support_detail}; "
            f"oxidation condition: {oxidation}."
        ),
        drying_condition="not_applicable",
        calcination_condition="not_applicable",
        reduction_condition=(
            "700 C vacuum anneal followed by ethanol exposure"
            + (" with 1500 C hot filament" if filament == "on" else "")
        ),
        activation_condition="annealed at 700 C in approximately 1 x 10^-8 Torr",
        post_preparation_condition=PHASE[(metal, support, state, filament)],
        catalyst_particle_size_mean_nm="not_reported",
        catalyst_particle_size_range_nm="not_reported",
        catalyst_particle_size_qualifier=(
            "film thickness is not catalyst-particle diameter"
        ),
        phase_or_state_summary=PHASE[(metal, support, state, filament)],
        dispersion_summary="nominally continuous evaporated ultrathin catalyst film",
        deactivation_summary=(
            "Fe activity tracks retained metallic fraction; pre-oxidation also "
            "changes morphology. Co remains mostly metallic but oxidized Co is less active."
        ),
    )


def process(
    run_id: str,
    metal: str,
    support: str,
    state: str,
    filament: str,
) -> dict[str, str]:
    return process_row(
        run_id,
        1,
        "hot_filament_ethanol_CVD_growth",
        reactor_type="interconnected ultrahigh-vacuum CVD chamber",
        scale_level="lab_thin_film_screen",
        reactor_material="not_reported",
        reactor_size_summary="not_reported",
        reactor_setup_summary=(
            f"0.3 nm {metal}/{support} sample; "
            f"{'pre-oxidized' if state == 'oxidized' else 'as-deposited'}; "
            f"hot filament {filament}."
        ),
        temperature_setpoint_C="700",
        temperature_program_summary=(
            "vacuum anneal and growth at 700 C; hot filament 1500 C when enabled"
        ),
        holding_time_min="5",
        heating_rate_C_min="not_reported",
        cooling_condition="not_reported",
        pressure_original="2 Torr ethanol",
        pressure_kPa="",
        carbon_source="ethanol vapor",
        carbon_source_flow_original="not_reported",
        reducing_gas=(
            "H2 and reducing fragments generated by hot-filament ethanol decomposition"
            if filament == "on"
            else "not_separately_fed"
        ),
        reducing_gas_flow_original="not_reported",
        inert_gas="not_reported",
        inert_gas_flow_original="not_reported",
        cofeed_or_reactive_gas="activated ethanol fragments"
        if filament == "on"
        else "none",
        cofeed_flow_original="not_reported",
        total_flow_original="not_reported",
        gas_composition_summary=(
            "2 Torr ethanol exposed to a 1500 C graphite filament 8 mm from sample"
            if filament == "on"
            else "2 Torr unactivated ethanol; hot filament off"
        ),
        process_note=(
            "Companion XPS used a short 20 s exposure on SiO2 or 5 s on Al2O3; "
            "the production/SEM comparison used 5 min growth."
        ),
    )


def product_row(
    run_id: str,
    metal: str,
    support: str,
    state: str,
    filament: str,
) -> dict[str, str]:
    label, detail = OUTCOME[(metal, support, state, filament)]
    forest = "forest" in label
    no_growth = label == "no CNT growth"
    return yield_row(
        run_id,
        primary_yield_metric="qualitative_SEM_CNT_growth_after_5_min",
        yield_original=label,
        yield_definition_original="SEM morphology after 5 min exposure to 2 Torr ethanol",
        yield_calculation_method="qualitative_visual_comparison",
        yield_value_standardized="",
        yield_unit_standardized="",
        yield_standardization_note=(
            "No mass yield reported; qualitative SEM outcome retained."
        ),
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=detail,
        CNT_type_reported=(
            "no_product"
            if no_growth
            else ("SWCNT forest" if forest else "CNT mat or layer")
        ),
        CNT_type_confirmed=(
            "not_applicable_no_growth"
            if no_growth
            else (
                "SWCNT confirmed by TEM for strongest Fe/Al2O3 forest"
                if (metal, support, state, filament)
                == ("Fe", "Al2O3", "as_deposited", "on")
                else "not_separately_confirmed_for_this_condition"
            )
        ),
        product_mixture_summary="not_reported"
        if no_growth
        else "CNT film on catalyst/support",
        CNT_type_evidence=(
            "SEM no-growth observation"
            if no_growth
            else "SEM morphology; TEM insert for strongest Fe/Al2O3 forest"
        ),
        SWCNT_or_few_wall_evidence_summary=(
            "TEM image supports SWCNT identity"
            if (metal, support, state, filament)
            == ("Fe", "Al2O3", "as_deposited", "on")
            else "not_reported_for_individual_condition"
        ),
        RBM_peak_reported="not_reported",
        outer_diameter_mean_nm="not_reported",
        outer_diameter_range_nm="not_reported",
        inner_diameter_mean_nm="not_reported",
        wall_number_summary="not_reported",
        length_summary=(
            "Fe/Al2O3 as-deposited filament-on forest was factor 2 taller "
            "than corresponding Co forest"
            if (metal, support, state, filament)
            in {
                ("Fe", "Al2O3", "as_deposited", "on"),
                ("Co", "Al2O3", "as_deposited", "on"),
            }
            else "not_quantified"
        ),
        morphology=detail,
        alignment_or_array=(
            "vertically aligned forest"
            if forest
            else ("not_applicable_no_growth" if no_growth else "entangled mat or layer")
        ),
        Raman_ratio_type="not_reported",
        Raman_ratio_value="not_reported",
        Raman_laser_wavelength_nm="not_reported",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis="not_reported",
        residue_summary="not_reported",
        amorphous_carbon_level=(
            "ethanol selected partly because it suppresses soot formation"
        ),
        BET_surface_area_product_m2_g="",
        characterization_methods="SEM; XPS; TEM for strongest forest",
        post_treatment_or_purification="none",
        purification_condition="not_applicable",
        application_property_summary="catalyst-state/growth-correlation study",
    )


def cost(run_id: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="lab_thin_film_screen",
        scale_level_claimed="not_reported",
        scale_evidence_summary=(
            "Five-minute catalyst-screening growth in a vacuum-connected CVD/XPS system."
        ),
        reactor_capacity_or_throughput="not_reported",
        continuous_operation_time_h="not_reported",
        catalyst_lifetime_or_reuse="not_reported",
        catalyst_reuse_cycles="not_reported",
        batch_stability="single qualitative SEM comparison",
        scale_up_issue=(
            "Maintain metal state, support interaction and local ethanol activation "
            "uniformly over larger substrates."
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="No CNT mass, conversion, throughput or cost reported.",
        cost_driver_summary="700 C CVD, 1500 C filament, ethanol and vacuum handling",
        safety_risk="flammable ethanol vapor, hot graphite filament and nanoparticle films",
        emission_or_waste="unquantified ethanol decomposition exhaust",
        industrial_readiness_assessment="mechanistic laboratory catalyst screen",
        reproduction_value="high for qualitative catalyst ranking; low for productivity",
        reproduction_priority="high",
        recommended_next_action=(
            "Measure catalyst-resolved CNT mass, forest height, carbon conversion "
            "and replicate variability for all 16 conditions."
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
                "Sixteen-condition 0.3 nm Fe/Co x SiO2/Al2O3 x "
                "as-deposited/oxidized x hot-filament off/on ethanol-CVD matrix; "
                "short-time XPS catalyst states and 5 min SEM growth outcomes."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_fulltext_pdf"

    run_ids: dict[tuple[str, str, str, str], str] = {}
    for metal, support, state, filament in factorial(
        ["Fe", "Co"],
        ["SiO2", "Al2O3"],
        ["as_deposited", "oxidized"],
        ["off", "on"],
    ):
        key = (metal, support, state, filament)
        state_code = "AD" if state == "as_deposited" else "OX"
        code = f"{metal}_{support}_{state_code}_HF_{filament.upper()}"
        run_id = f"{SOURCE_ID}_{code}"
        run_ids[key] = run_id
        outcome, detail = OUTCOME[key]
        summary = (
            f"0.3 nm {metal}/{support}, {state.replace('_', '-')}, "
            f"hot filament {filament}, 700 C and 2 Torr ethanol for 5 min: "
            f"{outcome}."
        )
        tables["source_run"].append(run_row(SOURCE_ID, code, summary, summary, "high"))
        tables["catalyst_system"].append(
            catalyst(run_id, metal, support, state, filament)
        )
        tables["reactor_process_gas"].append(
            process(run_id, metal, support, state, filament)
        )
        tables["yield_quality"].append(
            product_row(run_id, metal, support, state, filament)
        )
        tables["cost_scale_review"].append(cost(run_id))

        page, span = page_and_span(metal, support)
        evidence_text = (
            BASE_RECIPE
            + " "
            + PHASE[key]
            + f" Five-minute SEM outcome: {outcome}; {detail}."
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "RUN",
            "source_run",
            run_id,
            "record_level",
            span,
            page,
            evidence_text,
            "Condition identity and qualitative growth outcome.",
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "CATALYST",
            "catalyst_system",
            f"{run_id}_CAT",
            "record_level",
            span,
            page,
            evidence_text,
            "Catalyst preparation, support and XPS phase state.",
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "PROCESS",
            "reactor_process_gas",
            f"{run_id}_S01",
            "record_level",
            "SPAN_0CCAD30284C1E3B52C4D",
            4,
            BASE_RECIPE,
            "Shared ethanol-CVD growth recipe.",
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "PRODUCT",
            "yield_quality",
            f"{run_id}_PROD",
            "record_level",
            span,
            page,
            evidence_text,
            "SEM morphology and XPS/growth correlation.",
            value_status="qualitative_figure_comparison",
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            "record_level",
            "SPAN_C6D6887256921A517A85",
            9,
            (
                BASE_RECIPE + " The paper reports a mechanistic catalyst screen but no "
                "CNT mass, conversion, throughput, catalyst lifetime or cost."
            ),
            "Process-intensity facts and industrial data gaps.",
            value_status="review_assessment",
        )

    reference_id = run_ids[("Fe", "Al2O3", "as_deposited", "on")]
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_001",
                SOURCE_ID,
                reference_id,
                "critical_data_gap",
                "yield_quality",
                f"{reference_id}_PROD",
                "yield_original",
                (
                    "All production outcomes are qualitative SEM comparisons; "
                    "no CNT mass yield, conversion or absolute forest height table is reported."
                ),
                f"EVD_{reference_id}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_XPS_TIME_001",
                SOURCE_ID,
                reference_id,
                "companion_diagnostic",
                "catalyst_system",
                f"{reference_id}_CAT",
                "phase_or_state_summary",
                (
                    "XPS phase states use 20 s SiO2 or 5 s Al2O3 ethanol "
                    "exposures, while SEM production outcomes use 5 min growth."
                ),
                f"EVD_{reference_id}_CATALYST;EVD_{reference_id}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FIGURE_001",
                SOURCE_ID,
                reference_id,
                "figure_comparison",
                "yield_quality",
                f"{reference_id}_PROD",
                "morphology",
                (
                    "Forest/mat/layer labels are faithful qualitative readings "
                    "of Figures 3, 5, 7 and 8; image scale bars were not converted "
                    "into unreported numeric heights."
                ),
                f"EVD_{reference_id}_PRODUCT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_THIN_FILM_001",
                SOURCE_ID,
                reference_id,
                "scope_boundary",
                "source_run",
                reference_id,
                "run_summary",
                (
                    "Additional 0.02 nm pre-growth XPS controls probe "
                    "metal-support interaction but do not report CNT-growth "
                    "outcomes; the production matrix uses the stated 0.3 nm films."
                ),
                f"EVD_{reference_id}_CATALYST",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CO_STATE_001",
                SOURCE_ID,
                run_ids[("Co", "SiO2", "oxidized", "off")],
                "mechanistic_interpretation",
                "catalyst_system",
                f"{run_ids[('Co', 'SiO2', 'oxidized', 'off')]}_CAT",
                "deactivation_summary",
                (
                    "Oxidized Co becomes mostly metallic during ethanol "
                    "exposure but remains less active than initially metallic "
                    "Co, indicating morphology/history effects beyond oxidation state."
                ),
                f"EVD_{run_ids[('Co', 'SiO2', 'oxidized', 'off')]}_CATALYST",
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
