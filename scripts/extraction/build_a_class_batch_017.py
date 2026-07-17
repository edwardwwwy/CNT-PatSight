#!/usr/bin/env python3
"""Build the seventeenth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 17
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_79F908D3DA4AE6F8"


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


def catalyst(run_id: str) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label="in-situ Fe from ferrocene on porous silicon",
        active_metals="Fe",
        support_material="porous silicon (PSi)",
        promoter="not_applicable",
        metal_ratio_original="not_reported",
        metal_ratio_standardized="not_applicable",
        precursor_summary="ferrocene mixed with camphor oil",
        preparation_method="in_situ_ferrocene_decomposition",
        preparation_modifier="first-furnace vaporization/pyrolysis",
        preparation_detail=(
            "Camphor oil and ferrocene were introduced together; ferrocene "
            "decomposed in the first furnace to form the Fe catalyst, which "
            "was transported toward the porous-silicon substrate."
        ),
        drying_condition="not_applicable",
        calcination_condition="not_applicable",
        reduction_condition="not separately reported",
        activation_condition="in-situ at 180 C precursor-zone treatment",
        post_preparation_condition="fresh floating/deposited Fe during CVD",
        catalyst_particle_size_mean_nm="not_reported",
        catalyst_particle_size_range_nm="not_reported",
        catalyst_particle_size_qualifier=(
            "CNT diameters are not mapped as catalyst-particle sizes"
        ),
        phase_or_state_summary="ferrocene-derived Fe; exact phase not reported",
        dispersion_summary="deposited on selectively doped porous silicon",
        deactivation_summary="not_reported",
    )


def main_cost(run_id: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="lab_batch",
        scale_level_claimed="potential_renewable_precursor_route",
        scale_evidence_summary=(
            "One-hour horizontal two-furnace CVD on a porous-silicon substrate."
        ),
        reactor_capacity_or_throughput="not_reported",
        continuous_operation_time_h="1",
        catalyst_lifetime_or_reuse="not_reported",
        batch_stability="single flow-program result; replicate statistics absent",
        scale_up_issue=(
            "Control camphor/ferrocene delivery, extreme diameter broadening, "
            "PSi substrate cost and uniformity over larger areas."
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="no mass yield, feed quantity or cost reported",
        cost_driver_summary=(
            "camphor oil, ferrocene, porous-silicon fabrication, argon and furnace duty"
        ),
        safety_risk=(
            "flammable camphor vapor, ferrocene/iron nanoparticles and hot exhaust"
        ),
        emission_or_waste="unquantified amorphous carbon and CVD exhaust",
        industrial_readiness_assessment=(
            "laboratory morphology-control demonstration; mass productivity absent"
        ),
        reproduction_value="medium until exact deposition temperature and feed ratio are given",
        reproduction_priority="medium",
        recommended_next_action=(
            "Report exact growth temperature, camphor/ferrocene feed, CNT mass "
            "yield and layer-resolved diameter distributions."
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
                "One sequential 600-to-400-to-200 sccm flow-program CVD run "
                "forming a three-layer MVCNT array, plus a fixed-flow Raman comparator."
            ),
        )
    )
    tables["source_master"][0]["local_file_path"] = (
        f"data/interim/parsed_text/{SOURCE_ID}/full_text.txt"
    )
    tables["source_master"][0]["pdf_status"] = "validated_html_fulltext"
    tables["source_master"][0]["notes"] += (
        " The three diameters belong to sequential layers in one product, "
        "not to three independently reported synthesis batches."
    )

    run_id = f"{SOURCE_ID}_FLOW_PROGRAM"
    tables["source_run"].append(
        run_row(
            SOURCE_ID,
            "FLOW_PROGRAM",
            "sequential 600/400/200 sccm Ar multilayer-MVCNT growth",
            (
                "Camphor oil/ferrocene CVD on PSi with a one-hour decreasing-Ar "
                "program produced vertically aligned layers near 30 nm, 75 nm "
                "and up to 1 micrometer diameter."
            ),
            "medium",
        )
    )
    tables["catalyst_system"].append(catalyst(run_id))
    tables["reactor_process_gas"].extend(
        [
            process_row(
                run_id,
                1,
                "precursor_vaporization_and_catalyst_generation",
                reactor_type="horizontal two-furnace quartz-tube CVD",
                scale_level="lab_batch",
                reactor_material="quartz tube",
                reactor_size_summary="not_reported",
                reactor_setup_summary=(
                    "Camphor oil/ferrocene at the inlet in the first furnace; "
                    "porous-silicon substrate in the second furnace."
                ),
                temperature_setpoint_C="180",
                temperature_program_summary="heat and hold precursor zone at 180 C",
                holding_time_min="30",
                pressure_original="1 bar",
                pressure_kPa="100",
                carbon_source="camphor oil",
                carbon_source_flow_original="amount and pump rate not reported",
                reducing_gas="not_applicable",
                inert_gas="Ar",
                cofeed_or_reactive_gas="ferrocene",
                cofeed_flow_original="amount and camphor/ferrocene ratio not reported",
                gas_composition_summary="camphor and ferrocene vapor transported in Ar",
                process_note=(
                    "The source describes the 180 C treatment as complete "
                    "precursor/catalyst pyrolysis."
                ),
            ),
            process_row(
                run_id,
                2,
                "sequential_flow_CVD_growth",
                reactor_type="horizontal two-furnace quartz-tube CVD",
                scale_level="lab_batch",
                reactor_material="quartz tube",
                reactor_size_summary="not_reported",
                reactor_setup_summary="PSi substrate in the second furnace",
                temperature_range_reported_C="750-850",
                temperature_program_summary=(
                    "Exact deposition setpoint not stated; described as optimal "
                    "within 750-850 C."
                ),
                holding_time_min="60",
                cooling_condition="slow cool to room temperature under Ar",
                pressure_original="1 bar",
                pressure_kPa="100",
                carbon_source="camphor oil vapor",
                reducing_gas="not_applicable",
                inert_gas="Ar",
                inert_gas_flow_original=(
                    "600 sccm initially; after 10 min decrease to 400 sccm; "
                    "after 20 min decrease to 200 sccm until 60 min"
                ),
                cofeed_or_reactive_gas="ferrocene-derived Fe aerosol",
                total_flow_original="Ar schedule 600 -> 400 -> 200 sccm",
                gas_composition_summary=(
                    "Sequential Ar flow program changed transport/diffusion "
                    "while carbon source was consumed."
                ),
                process_note=(
                    "The wording does not clarify whether 'after 20 min' is "
                    "elapsed time or an additional 20-min interval."
                ),
            ),
        ]
    )
    tables["yield_quality"].append(
        yield_row(
            run_id,
            primary_yield_metric="layer_resolved_CNT_diameter_outcome",
            yield_original="mass yield not reported",
            yield_definition_original="not_reported",
            yield_calculation_method="not_applicable",
            yield_value_standardized="",
            yield_unit_standardized="not_applicable",
            secondary_result_summary=(
                "FTIR bands: 3424, 2928, 1699 and 1540 cm-1; D and G Raman "
                "peaks at 1348 and 1577 cm-1."
            ),
            CNT_type_reported="multilayer vertical carbon nanotubes (MVCNTs)",
            CNT_type_confirmed="multiwall CNTs by FESEM/Raman/FTIR",
            product_mixture_summary=(
                "three sequential vertically aligned CNT layers with strongly "
                "different diameter distributions"
            ),
            CNT_type_evidence="long straight multiwall tubes in FESEM",
            outer_diameter_range_nm=(
                "about 30 nm first layer; about 75 nm central layer; "
                "up to 1000 nm final layer"
            ),
            length_summary="long tubes; numerical length not reported",
            morphology="well-aligned, straight, three-layer heterostructured array",
            alignment_or_array="vertically aligned MVCNT array on PSi",
            Raman_ratio_type="ID/IG",
            Raman_ratio_value="approximately 1.12",
            Raman_laser_wavelength_nm="514.5",
            purity_basis="not_reported",
            amorphous_carbon_level="not quantified",
            characterization_methods="FESEM; Raman; FTIR; H2-TPD",
            post_treatment_or_purification="none reported",
            purification_condition="not_applicable",
            application_property_summary=(
                "H2-TPD: degas at 100 C, expose to H2 at 760 Torr, cool to "
                "approximately 190 K during evacuation; near-ambient hydrogen "
                "adsorption capacity reported as approximately 2x a single-layer "
                "CNT comparator, without absolute capacity."
            ),
        )
    )
    tables["cost_scale_review"].append(main_cost(run_id))

    for suffix, table, record, fields, span_id, summary, status in [
        (
            "CATALYST",
            "catalyst_system",
            f"{run_id}_CAT",
            "record_level",
            "SPAN_376631171D96DBA61927",
            "Camphor/ferrocene introduction and in-situ Fe formation.",
            "reported",
        ),
        (
            "PROCESS_PRECURSOR",
            "reactor_process_gas",
            f"{run_id}_S01",
            "record_level",
            "SPAN_376631171D96DBA61927",
            "First-furnace temperature, duration and second-furnace range.",
            "reported",
        ),
        (
            "PROCESS_FLOW",
            "reactor_process_gas",
            f"{run_id}_S02",
            "record_level",
            "SPAN_0BE959FBCCADE14776A6",
            "Pressure, complete Ar schedule, duration and cooling.",
            "reported",
        ),
        (
            "MORPHOLOGY",
            "yield_quality",
            f"{run_id}_PROD",
            "CNT_type_reported;CNT_type_confirmed;morphology;alignment_or_array",
            "SPAN_229E64C5B82C25CFAAC7",
            "Vertically aligned morphology and flow-dependent thickening.",
            "reported",
        ),
        (
            "DIAMETERS",
            "yield_quality",
            f"{run_id}_PROD",
            "outer_diameter_range_nm;product_mixture_summary",
            "SPAN_A05C66A0B0A128F3DC28",
            "Layer-specific 30 nm, 75 nm and up-to-1-micrometer diameters.",
            "reported",
        ),
        (
            "RAMAN",
            "yield_quality",
            f"{run_id}_PROD",
            "Raman_ratio_type;Raman_ratio_value",
            "SPAN_0EF2B62483D9F11B9101",
            "D/G peaks and approximate ID/IG ratio.",
            "reported",
        ),
        (
            "CHAR_METHOD",
            "yield_quality",
            f"{run_id}_PROD",
            "Raman_laser_wavelength_nm;characterization_methods",
            "SPAN_0BE959FBCCADE14776A6",
            "Raman wavelength and characterization instruments.",
            "reported",
        ),
        (
            "FTIR",
            "yield_quality",
            f"{run_id}_PROD",
            "secondary_result_summary",
            "SPAN_19C813FF0F45E60EE1B0",
            "Table 1 FTIR band values and assignments.",
            "reported",
        ),
        (
            "APPLICATION",
            "yield_quality",
            f"{run_id}_PROD",
            "application_property_summary",
            "SPAN_16E95D68F2B4084DAD84",
            "Hydrogen TPD conditions and relative-capacity claim.",
            "reported",
        ),
        (
            "COST",
            "cost_scale_review",
            run_id,
            "record_level",
            "SPAN_0BE959FBCCADE14776A6",
            "One-hour laboratory flow-program scale.",
            "review_assessment",
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
            status,
        )

    diameter_conversion = evidence_row(
        store,
        SOURCE_ID,
        f"EVD_{run_id}_DIAMETER_CONVERSION",
        run_id,
        "yield_quality",
        f"{run_id}_PROD",
        "outer_diameter_range_nm",
        "SPAN_A05C66A0B0A128F3DC28",
        "Final-layer micrometer diameter standardized to nanometers.",
    )
    diameter_conversion.update(
        {
            "evidence_type": "reported_value_with_unit_standardization",
            "evidence_text": (
                "The final layer is reported as up to 1 micrometer diameter; "
                "1 micrometer equals 1000 nanometers."
            ),
            "evidence_summary": (
                "The reported 1 micrometer maximum is standardized as 1000 nm."
            ),
            "notes": "Unit conversion only.",
        }
    )
    tables["evidence_index"].append(diameter_conversion)

    comparator_id = f"{SOURCE_ID}_FIXED_FLOW"
    tables["source_run"].append(
        run_row(
            SOURCE_ID,
            "FIXED_FLOW",
            "fixed-flow CNT Raman comparator",
            (
                "A fixed-flow CNT product was compared by Raman and had "
                "approximately the same ID/IG ratio (1.12), but its synthesis "
                "flow and run details were not reported."
            ),
            "low",
        )
    )
    tables["source_run"][-1]["data_type"] = "experimental_control"
    tables["catalyst_system"].append(catalyst(comparator_id))
    tables["reactor_process_gas"].append(
        process_row(
            comparator_id,
            1,
            "fixed_flow_CVD_comparator",
            reactor_type="horizontal quartz-tube CVD",
            scale_level="lab_batch",
            reactor_material="quartz tube",
            reactor_size_summary="not_reported",
            reactor_setup_summary="porous-silicon substrate",
            temperature_range_reported_C="not separately reported",
            holding_time_min="not_reported",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source="camphor oil",
            reducing_gas="not_applicable",
            inert_gas="Ar",
            inert_gas_flow_original="fixed value not reported",
            cofeed_or_reactive_gas="ferrocene",
            gas_composition_summary="fixed-flow comparator; details absent",
            process_note="Only its Raman comparison is reported.",
        )
    )
    tables["yield_quality"].append(
        yield_row(
            comparator_id,
            primary_yield_metric="Raman_quality_comparator_only",
            yield_original="not_reported",
            yield_definition_original="not_reported",
            yield_calculation_method="not_applicable",
            yield_value_standardized="",
            yield_unit_standardized="not_applicable",
            secondary_result_summary="fixed-flow comparator details not reported",
            CNT_type_reported="CNTs grown under a unique/fixed flow rate",
            CNT_type_confirmed="not separately characterized",
            product_mixture_summary="not_reported",
            CNT_type_evidence="Raman comparison only",
            morphology="not separately reported",
            alignment_or_array="not separately reported",
            Raman_ratio_type="ID/IG",
            Raman_ratio_value="approximately 1.12",
            Raman_laser_wavelength_nm="514.5",
            characterization_methods="Raman",
            post_treatment_or_purification="not_reported",
            purification_condition="not_reported",
        )
    )
    tables["cost_scale_review"].append(main_cost(comparator_id))
    tables["cost_scale_review"][-1].update(
        {
            "scale_evidence_summary": "Fixed-flow comparator mentioned only in Raman discussion.",
            "reactor_capacity_or_throughput": "not_reported",
            "continuous_operation_time_h": "not_reported",
            "reproduction_value": "low until fixed-flow condition is disclosed",
            "reproduction_priority": "low",
        }
    )
    for suffix, table, record, fields, span_id, summary, status in [
        (
            "CATALYST",
            "catalyst_system",
            f"{comparator_id}_CAT",
            "record_level",
            "SPAN_376631171D96DBA61927",
            "Common camphor/ferrocene catalyst system.",
            "inferred",
        ),
        (
            "PROCESS",
            "reactor_process_gas",
            f"{comparator_id}_S01",
            "record_level",
            "SPAN_0EF2B62483D9F11B9101",
            "Source identifies a fixed-flow comparator but omits its flow.",
            "not_reported",
        ),
        (
            "RAMAN",
            "yield_quality",
            f"{comparator_id}_PROD",
            "record_level",
            "SPAN_0EF2B62483D9F11B9101",
            "Fixed-flow comparator ID/IG approximately 1.12.",
            "reported",
        ),
        (
            "CHAR_METHOD",
            "yield_quality",
            f"{comparator_id}_PROD",
            "Raman_laser_wavelength_nm;characterization_methods",
            "SPAN_0BE959FBCCADE14776A6",
            "Common Raman wavelength.",
            "inferred",
        ),
        (
            "COST",
            "cost_scale_review",
            comparator_id,
            "record_level",
            "SPAN_0EF2B62483D9F11B9101",
            "Comparator is insufficiently documented for reproduction.",
            "review_assessment",
        ),
    ]:
        append_evidence(
            tables,
            store,
            comparator_id,
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
                f"{SOURCE_ID}_ISSUE_TEMP_001",
                SOURCE_ID,
                run_id,
                "critical_data_gap",
                "reactor_process_gas",
                f"{run_id}_S02",
                "temperature_setpoint_C",
                (
                    "The deposition temperature is described only as an "
                    "optimal range of 750-850 C; no exact setpoint is reported."
                ),
                f"EVD_{run_id}_PROCESS_PRECURSOR",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FEED_001",
                SOURCE_ID,
                run_id,
                "critical_data_gap",
                "catalyst_system",
                f"{run_id}_CAT",
                "precursor_summary",
                (
                    "Camphor-oil mass/flow, ferrocene amount and their ratio "
                    "are not reported."
                ),
                f"EVD_{run_id}_CATALYST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FLOW_TIMING_001",
                SOURCE_ID,
                run_id,
                "timeline_ambiguity",
                "reactor_process_gas",
                f"{run_id}_S02",
                "inert_gas_flow_original",
                (
                    "The phrase 'then, after 20 min' may mean 20 min elapsed "
                    "or 20 additional minutes; the raw schedule wording is retained."
                ),
                f"EVD_{run_id}_PROCESS_FLOW",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_DIAMETER_001",
                SOURCE_ID,
                run_id,
                "reported_value_requires_confirmation",
                "yield_quality",
                f"{run_id}_PROD",
                "outer_diameter_range_nm",
                (
                    "The final layer is reported as reaching 1 micrometer "
                    "diameter, unusually large for CNTs; retain as author report."
                ),
                f"EVD_{run_id}_DIAMETERS",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_001",
                SOURCE_ID,
                run_id,
                "critical_data_gap",
                "yield_quality",
                f"{run_id}_PROD",
                "yield_original",
                "No CNT mass yield, productivity or carbon conversion is reported.",
                f"EVD_{run_id}_MORPHOLOGY",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_H2_001",
                SOURCE_ID,
                run_id,
                "relative_only_application_result",
                "yield_quality",
                f"{run_id}_PROD",
                "application_property_summary",
                (
                    "Hydrogen storage is reported only as approximately 2x "
                    "the single-layer comparator; absolute capacity and units "
                    "are absent."
                ),
                f"EVD_{run_id}_APPLICATION",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FIXED_FLOW_001",
                SOURCE_ID,
                comparator_id,
                "critical_data_gap",
                "reactor_process_gas",
                f"{comparator_id}_S01",
                "inert_gas_flow_original",
                (
                    "The fixed-flow comparator's flow, temperature, duration "
                    "and product morphology are not separately reported."
                ),
                f"EVD_{comparator_id}_PROCESS;EVD_{comparator_id}_RAMAN",
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
    output = BATCH_ROOT / f"batch_{BATCH_NUMBER:03d}_metrics.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
