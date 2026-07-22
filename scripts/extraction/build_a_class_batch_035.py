#!/usr/bin/env python3
"""Build the thirty-fifth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 35
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ID = "LIT_89DB5AF57D638DC8"
PDF_REF = "data/raw/literature/pdf/LIT_89DB5AF57D638DC8_08cf7fdc4cb8.pdf"

ABSTRACT_SPAN = "SPAN_17272EA434369103872C"
RESULT_SPAN = "SPAN_9529A5EDFA52DF34033A"
YIELD_SPAN = "SPAN_2EC06E01BBC0AF42F2C4"
CHAR_SPAN = "SPAN_8D292917B3230A668239"
IMPURITY_SPAN = "SPAN_D40239D2918BEE646D85"
DISCUSSION_SPAN = "SPAN_705BA18D24F9A2071D1E"
MATERIAL_SPAN = "SPAN_2FB86F93ABE0F62D5564"
METHOD_SPAN = "SPAN_1778471BF502D2E914F7"
RAMAN_SPAN = "SPAN_F0B63E349254629772A5"

RUNS: list[dict[str, Any]] = [
    {
        "code": "ALUMINA_TUBE",
        "tube": "alumina",
        "composition": "Al2O3",
        "linear_density": 0.35,
        "raman": 0.3,
        "g_peak": 1583,
        "residual": 8.5,
        "outcome": "stable continuous spinning but lowest carbon-to-fiber conversion",
    },
    {
        "code": "ALUMINA_MULLITE_INSERT",
        "tube": "alumina reactor with concentric mullite inner tube",
        "composition": "Al2O3 outer tube plus mullite insert",
        "linear_density": 0.43,
        "raman": 0.4,
        "g_peak": 1584,
        "residual": 7.4,
        "outcome": "intermediate carbon-to-fiber conversion",
    },
    {
        "code": "MULLITE_TUBE",
        "tube": "mullite",
        "composition": "62.6% Al2O3, 35.2% SiO2 and 2.2% other components",
        "linear_density": 0.60,
        "raman": 0.3,
        "g_peak": 1583,
        "residual": 4.0,
        "outcome": "highest carbon-to-fiber conversion and darkest CNT aerogel",
    },
]


def summary(item: dict[str, Any]) -> str:
    return (
        f"Direct-spinning floating-catalyst CVD in a {item['tube']} reactor at "
        f"1250 C under H2, using purified ferrocene, thiophene and liquid carbon "
        f"source; fiber winding 5 m/min. Linear density {item['linear_density']} "
        f"g/km; ID/IG {item['raman']}; G peak {item['g_peak']} cm-1; "
        f"residual catalyst about {item['residual']} wt%. {item['outcome']}."
    )


def catalyst(item: dict[str, Any], run_id: str) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label="floating Fe catalyst with sulfur promoter",
        active_metals="Fe",
        support_material="unsupported floating nanoparticles in H2",
        promoter="S from thiophene",
        metal_ratio_original=(
            "ferrocene:thiophene:carbon-source formulations ranged from "
            "0.8:1.5:97.7 to 0.8:0.2:99.0"
        ),
        metal_ratio_standardized="exact formulation for tube comparison not disclosed",
        precursor_summary=(
            "98% ferrocene purified by sublimation/recrystallization; "
            ">=99% thiophene; >99% 1-butanol/toluene"
        ),
        preparation_method="in-situ floating-catalyst nanoparticle formation",
        preparation_modifier=f"{item['tube']} reactor wall assists hydrocarbon cracking",
        preparation_detail=(
            "Ferrocene, thiophene and liquid carbon precursor were injected "
            "into a vertical 1250 C H2 reactor; long CNTs formed an aerogel "
            "that was continuously drawn onto a winder."
        ),
        drying_condition="not_applicable",
        calcination_condition="not_applicable",
        reduction_condition="formed and maintained under H2 at 1250 C",
        activation_condition="thermal ferrocene decomposition in H2",
        post_preparation_condition="continuous gas-phase formation during spinning",
        catalyst_particle_size_mean_nm="",
        catalyst_particle_size_range_nm="",
        catalyst_particle_size_qualifier=(
            "Discussion uses a representative Fe radius of 4.5 nm and Fe feed "
            "below 3 microgram/s; these are model inputs, not run measurements."
        ),
        phase_or_state_summary="S-coated floating Fe nanoparticles",
        dispersion_summary="extremely dilute floating Fe-particle population",
        deactivation_summary="not quantified; Fe residue remains in as-spun fiber",
    )


def stages(item: dict[str, Any], run_id: str) -> list[dict[str, str]]:
    return [
        process_row(
            run_id,
            1,
            "floating_catalyst_CNT_growth_and_direct_spinning",
            reactor_type="vertical tubular FC-CVD direct-spinning reactor",
            scale_level="laboratory_continuous_fiber_spinning",
            reactor_material=item["composition"],
            reactor_size_summary="reactor radius 3.5 cm used in mechanism estimate",
            reactor_setup_summary=(
                f"{item['tube']}; aerogel drawn continuously from reactor onto winder"
            ),
            catalyst_loading_mass_g="",
            temperature_setpoint_C="1250",
            temperature_range_reported_C="1250",
            temperature_program_summary="continuous high-temperature FC-CVD",
            holding_time_min="continuous; fibers spun for hours",
            heating_rate_C_min="not_reported",
            cooling_condition="not_reported",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source="1-butanol; toluene also tested in broader comparison",
            carbon_source_flow_original="not_reported",
            reducing_gas="H2",
            reducing_gas_flow_original="not_reported",
            inert_gas="N2 at reactor exit for safety, not part of reaction",
            inert_gas_flow_original="not_reported",
            cofeed_or_reactive_gas="ferrocene vapor and thiophene promoter",
            cofeed_flow_original="not_reported",
            total_flow_original="not_reported",
            gas_composition_summary=(
                "H2 atmosphere with ferrocene, thiophene and liquid carbon source"
            ),
            process_note="Fiber take-up speed was 5 m/min for the reported density comparison.",
        )
    ]


def product(item: dict[str, Any], run_id: str) -> dict[str, str]:
    return yield_row(
        run_id,
        primary_yield_metric="CNT_fiber_linear_mass_density",
        yield_original=f"{item['linear_density']} g/km at 5 m/min spinning rate",
        yield_definition_original="mass per unit length of continuously wound CNT fiber",
        yield_calculation_method="fiber linear-density measurement",
        yield_value_standardized=str(item["linear_density"]),
        yield_unit_standardized="g/km",
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=summary(item),
        CNT_type_reported="few-layer MWCNT fiber",
        CNT_type_confirmed="few-layer MWCNT fiber",
        product_mixture_summary="continuous porous CNT fiber with residual Fe catalyst",
        CNT_type_evidence="Raman; SEM; TEM; TGA",
        SWCNT_or_few_wall_evidence_summary="predominantly 3-5 walls",
        RBM_peak_reported="not_reported_for_this_few-layer_MWCNT_comparison",
        outer_diameter_mean_nm="",
        outer_diameter_range_nm="",
        inner_diameter_mean_nm="",
        wall_number_summary="predominantly 3-5 walls",
        length_summary="individual CNTs about 1 mm; continuous macroscopic fiber",
        morphology="highly graphitic bundled CNT aerogel/fiber",
        alignment_or_array="CNTs assembled and wound as macroscopic fiber",
        Raman_ratio_type="ID/IG",
        Raman_ratio_value=str(item["raman"]),
        Raman_laser_wavelength_nm="532",
        TGA_carbon_content_wt_percent=str(100 - item["residual"]),
        purified_product_purity_wt_percent="",
        purity_basis="as-spun fiber; TGA-derived complement of residual catalyst",
        residue_summary=(
            f"about {item['residual']} wt% residual catalyst; occasional "
            "SiO2/SiC reactor-tube fragments in long-collected samples"
        ),
        amorphous_carbon_level="similar low poorly graphitized fraction below 400 C",
        BET_surface_area_product_m2_g="",
        characterization_methods="Raman; TGA; SEM; TEM; EDS; XPS; WAXS",
        post_treatment_or_purification="none for primary as-spun samples",
        purification_condition="not_applicable",
        application_property_summary="continuous macroscopic CNT fiber production",
        notes="Tube composition changed yield but not CNT type or graphitization.",
    )


def cost_review(item: dict[str, Any], run_id: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="continuous laboratory fiber spinning",
        scale_level_claimed="laboratory >10 km/day and industrial scaled-up facilities",
        scale_evidence_summary=summary(item),
        reactor_capacity_or_throughput=(
            f"5 m/min fiber take-up; {item['linear_density']} g/km linear density"
        ),
        continuous_operation_time_h="continuous for hours",
        catalyst_lifetime_or_reuse="continuous precursor injection",
        catalyst_reuse_cycles="not_applicable",
        batch_stability="stable continuous spinning",
        scale_up_issue=(
            "reactor-tube degradation, Si-containing contamination, precursor "
            "conversion, tube aging and H2/high-temperature safety"
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="No study-specific cost calculation.",
        cost_driver_summary="1250 C heat duty, H2, ferrocene/thiophene and ceramic tube",
        safety_risk="H2 and volatile organics at 1250 C; N2 added at exit for safety",
        emission_or_waste="unconverted/cracked hydrocarbons and ceramic fragments",
        industrial_readiness_assessment="continuous process demonstrated; purity issue remains",
        reproduction_value="high",
        reproduction_priority="high",
        recommended_next_action=(
            "report absolute precursor/H2 flows, carbon balance, tube lifetime, "
            "impurity frequency and scaled energy/cost"
        ),
        review_note="Scale claims are contextual; exact industrial throughput is not reported here.",
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
    summary_text: str,
    *,
    status: str = "reported",
) -> None:
    evidence = evidence_row(
        store,
        SOURCE_ID,
        f"EVD_{run_id}_{suffix}",
        run_id,
        table,
        record_id,
        "record_level",
        span_id,
        summary_text,
        confidence="high",
        value_status=status,
    )
    evidence.update(
        {
            "evidence_type": "pdf_text_and_visual_figure_transcription",
            "source_section": f"PDF page {page}",
            "source_locator": f"PDF page {page}",
            "source_object_ref": PDF_REF,
            "evidence_text": text,
            "evidence_summary": summary_text,
            "notes": "PDF text and rendered figures were cross-checked.",
        }
    )
    tables["evidence_index"].append(evidence)


def add_run(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    item: dict[str, Any],
) -> str:
    run_id = f"{SOURCE_ID}_{item['code']}"
    run_summary = summary(item)
    tables["source_run"].append(
        run_row(SOURCE_ID, item["code"], item["tube"], run_summary, "high")
    )
    cat = catalyst(item, run_id)
    process = stages(item, run_id)[0]
    prod = product(item, run_id)
    cost = cost_review(item, run_id)
    tables["catalyst_system"].append(cat)
    tables["reactor_process_gas"].append(process)
    tables["yield_quality"].append(prod)
    tables["cost_scale_review"].append(cost)

    add_evidence(
        tables,
        store,
        run_id,
        "RUN",
        "source_run",
        run_id,
        YIELD_SPAN,
        3,
        run_summary,
        "Reactor-tube comparison, fiber density and quality.",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "CATALYST",
        "catalyst_system",
        cat["catalyst_id"],
        MATERIAL_SPAN,
        8,
        (
            f"{cat['catalyst_label']}; active {cat['active_metals']}; promoter "
            f"{cat['promoter']}; precursors {cat['precursor_summary']}; "
            f"formulation context {cat['metal_ratio_original']}; formation "
            f"{cat['preparation_detail']}; size context "
            f"{cat['catalyst_particle_size_qualifier']}"
        ),
        "Floating Fe/S catalyst and precursor preparation.",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "PROCESS",
        "reactor_process_gas",
        process["process_stage_id"],
        METHOD_SPAN,
        8,
        (
            f"Reactor {process['reactor_type']}; material "
            f"{process['reactor_material']}; radius/size "
            f"{process['reactor_size_summary']}; temperature "
            f"{process['temperature_setpoint_C']} C; duration "
            f"{process['holding_time_min']}; pressure "
            f"{process['pressure_original']} / {process['pressure_kPa']} kPa; "
            f"carbon source {process['carbon_source']} at "
            f"{process['carbon_source_flow_original']}; H2 "
            f"{process['reducing_gas_flow_original']}; N2 "
            f"{process['inert_gas_flow_original']}; cofeed "
            f"{process['cofeed_flow_original']}; composition "
            f"{process['gas_composition_summary']}; note {process['process_note']}"
        ),
        "Direct-spinning FC-CVD process.",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "PRODUCT",
        "yield_quality",
        prod["product_id"],
        CHAR_SPAN,
        4,
        (
            f"Linear density {prod['yield_original']}; standardized "
            f"{prod['yield_value_standardized']} {prod['yield_unit_standardized']}; "
            f"CNT type {prod['CNT_type_confirmed']}; walls "
            f"{prod['wall_number_summary']}; Raman ID/IG "
            f"{prod['Raman_ratio_value']} at 532 nm; G peak "
            f"{item['g_peak']} cm-1; residual catalyst {item['residual']} wt%; "
            f"TGA carbon complement {prod['TGA_carbon_content_wt_percent']} wt%; "
            f"length {prod['length_summary']}."
        ),
        "Fiber yield, Raman/TEM morphology and TGA residue.",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "IMPURITY",
        "yield_quality",
        prod["product_id"],
        IMPURITY_SPAN,
        5,
        (
            "Occasional Si-containing impurities were found in long-collected "
            "fibers from heavily used tubes; SiO2 and SiC were assigned and "
            "interpreted as detached reactor-tube fragments."
        ),
        "Reactor-tube impurity context.",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "COST",
        "cost_scale_review",
        run_id,
        ABSTRACT_SPAN,
        1,
        (
            f"Continuous fibers spun at 5 m/min with linear density "
            f"{item['linear_density']} g/km; process can run for hours. No "
            "study-specific cost; high-temperature H2 and tube degradation "
            "are scale and safety issues."
        ),
        "Continuous scale, cost-data gap and safety review.",
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
                "Three directly comparable reactor configurations: alumina, "
                "alumina with a concentric mullite insert, and mullite."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_open_access_pdf"
    master["notes"] += (
        " Page-render review was used to resolve the TGA-residue ordering. "
        "Broader SWCNT/MWCNT and butanol/toluene observations lack a complete "
        "condition matrix and are retained as contextual evidence."
    )
    run_ids = {item["code"]: add_run(tables, store, item) for item in RUNS}
    alumina = run_ids["ALUMINA_TUBE"]
    mixed = run_ids["ALUMINA_MULLITE_INSERT"]
    mullite = run_ids["MULLITE_TUBE"]
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_FORMULATION_001",
                SOURCE_ID,
                mullite,
                "critical_data_gap",
                "catalyst_system",
                f"{mullite}_CAT",
                "metal_ratio_standardized",
                (
                    "The methods give a precursor-composition range used to "
                    "tune wall number, but do not identify the exact ferrocene/"
                    "thiophene/carbon-source formulation for the three tube runs."
                ),
                f"EVD_{mullite}_CATALYST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FLOW_PRESSURE_001",
                SOURCE_ID,
                mullite,
                "critical_data_gap",
                "reactor_process_gas",
                f"{mullite}_S01",
                "carbon_source_flow_original",
                (
                    "Absolute liquid-precursor, H2 and exit-N2 flow rates and "
                    "operating pressure are not reported in the main paper."
                ),
                f"EVD_{mullite}_PROCESS",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_RESIDUE_ORDER_001",
                SOURCE_ID,
                alumina,
                "text_figure_discrepancy",
                "yield_quality",
                f"{alumina}_PROD",
                "residue_summary",
                (
                    "The sentence listing 8.5/7.4/4.0% names the tubes in an "
                    "order inconsistent with Fig. 4b and its caption. Values "
                    "are mapped as alumina 8.5%, mixed 7.4%, mullite 4.0% "
                    "following the plotted residual levels and yield logic."
                ),
                (f"EVD_{alumina}_PRODUCT;EVD_{mixed}_PRODUCT;EVD_{mullite}_PRODUCT"),
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CARBON_BALANCE_001",
                SOURCE_ID,
                mullite,
                "metric_definition",
                "yield_quality",
                f"{mullite}_PROD",
                "yield_original",
                (
                    "Fiber linear density is used as the reported reaction-yield "
                    "proxy; no complete injected-carbon conversion or carbon "
                    "mass balance is provided."
                ),
                f"EVD_{mullite}_RUN;EVD_{mullite}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_IMPURITY_FREQUENCY_001",
                SOURCE_ID,
                mullite,
                "impurity_scope",
                "yield_quality",
                f"{mullite}_PROD",
                "residue_summary",
                (
                    "SiO2/SiC fragments were scarce and mainly detected after "
                    "long collection (>30 min) in heavily used tubes; no "
                    "frequency or mass fraction was quantified."
                ),
                f"EVD_{mullite}_IMPURITY",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_TUBE_AGE_001",
                SOURCE_ID,
                mullite,
                "time_dependent_reactor_effect",
                "cost_scale_review",
                mullite,
                "scale_up_issue",
                (
                    "Months of reducing-atmosphere use roughened/amorphized "
                    "mullite and may change reaction yield, but tube age was "
                    "not controlled as an explicit experimental variable."
                ),
                f"EVD_{mullite}_COST",
                "high",
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
