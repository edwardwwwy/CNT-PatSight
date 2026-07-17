#!/usr/bin/env python3
"""Build the eighteenth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 18
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_7D549B9B7575FB0C"
PDF_REF = "data/raw/fulltext/pdf/LIT_7D549B9B7575FB0C_895a8f2f9800.pdf"


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


def append_pdf_evidence(
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
    value_status: str = "reported",
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
            "notes": (
                "Transcribed after visual inspection of the locally stored "
                "author manuscript PDF; candidate span supplies immutable linkage."
            ),
        }
    )
    tables["evidence_index"].append(item)


def no_catalyst(run_id: str) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label="no added catalyst (catalyst-free FFD)",
        active_metals="not_applicable",
        support_material="not_applicable",
        promoter="not_applicable",
        metal_ratio_original="not_applicable",
        metal_ratio_standardized="not_applicable",
        precursor_summary="not_applicable",
        preparation_method="not_applicable_catalyst_free",
        preparation_modifier="not_applicable",
        preparation_detail=(
            "The authors explicitly report flame-fragment deposition without "
            "using a catalyst."
        ),
        drying_condition="not_applicable",
        calcination_condition="not_applicable",
        reduction_condition="not_applicable",
        activation_condition="not_applicable",
        post_preparation_condition="not_applicable",
        catalyst_particle_size_mean_nm="not_applicable",
        catalyst_particle_size_range_nm="not_applicable",
        catalyst_particle_size_qualifier="not_applicable",
        phase_or_state_summary="not_applicable",
        dispersion_summary="not_applicable",
        deactivation_summary="not_applicable",
    )


def synthesis_stage(run_id: str) -> dict[str, str]:
    return process_row(
        run_id,
        1,
        "flame_fragments_deposition_synthesis",
        reactor_type="homemade flame-fragments-deposition chamber",
        scale_level="lab_batch",
        reactor_material="two stainless-steel boxes",
        reactor_size_summary=(
            "inner box 41 x 38 x 25 cm3; outer box 50 x 47 x 38 cm3; "
            "three 1.5 cm inlet tubes; nine collection positions"
        ),
        reactor_setup_summary=(
            "LPG, oxygen and nitrogen fed through separate stainless inlets; "
            "crucibles at the cold upper lid collected flame fragments."
        ),
        temperature_setpoint_C="160",
        temperature_program_summary="low-temperature FFD synthesis at 160 C",
        holding_time_min="not_reported",
        cooling_condition="not_reported",
        pressure_original="not_reported",
        pressure_kPa="",
        carbon_source="Iraqi liquefied petroleum gas (LPG)",
        carbon_source_flow_original="not_reported",
        reducing_gas="not_applicable",
        inert_gas="N2",
        inert_gas_flow_original="not_reported",
        cofeed_or_reactive_gas="O2",
        cofeed_flow_original="not_reported",
        total_flow_original="not_reported",
        gas_composition_summary=(
            "LPG carbon source with oxygen combustion feed and nitrogen gas; "
            "all flow rates controlled by external gauges but not disclosed."
        ),
        process_note=(
            "The current paper describes the chamber but refers to prior work "
            "for the detailed synthesis method."
        ),
    )


def common_cost(run_id: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="lab_batch",
        scale_level_claimed="potential_low_cost_catalyst_free_route",
        scale_evidence_summary=(
            "Homemade nine-position FFD chamber operated at 160 C, followed "
            "by bench purification where applicable."
        ),
        reactor_capacity_or_throughput="not_reported",
        continuous_operation_time_h="not_reported",
        catalyst_lifetime_or_reuse="not_applicable_catalyst_free",
        batch_stability="single study; replicate statistics absent",
        scale_up_issue=(
            "Control LPG combustion, flame uniformity and nine-position "
            "collection while containing PAH-rich soot and solvent operations."
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary=(
            "No CNT mass yield, gas consumption, solvent recovery or cost is reported."
        ),
        cost_driver_summary=(
            "LPG, oxygen/nitrogen, H2O2 and acetone, sonication, refrigeration "
            "and optional 275 C calcination"
        ),
        safety_risk=(
            "flammable LPG/acetone, oxygen-supported flame, concentrated H2O2, "
            "PAH-containing soot and hot calcination"
        ),
        emission_or_waste=(
            "unquantified combustion exhaust, amorphous carbon/PAH residues "
            "and aqueous/acetone purification waste"
        ),
        industrial_readiness_assessment=(
            "laboratory purification communication; production productivity absent"
        ),
        reproduction_value=(
            "medium for purification; low for synthesis until gas flows and time are disclosed"
        ),
        reproduction_priority="medium",
        recommended_next_action=(
            "Report LPG/O2/N2 flows, deposition duration, crude and recovered "
            "mass yields, solvent recovery and replicate purity."
        ),
    )


def add_common_author_records(
    tables: dict[str, list[dict[str, str]]],
    source_id: str,
    code: str,
    label: str,
    summary: str,
    confidence: str,
) -> str:
    run_id = f"{source_id}_{code}"
    tables["source_run"].append(run_row(source_id, code, label, summary, confidence))
    tables["catalyst_system"].append(no_catalyst(run_id))
    tables["reactor_process_gas"].append(synthesis_stage(run_id))
    tables["cost_scale_review"].append(common_cost(run_id))
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
                "Catalyst-free LPG flame-fragment synthesis baseline; crude, "
                "H2O2-only and sequential H2O2/acetone branches; commercial "
                "Aldrich MWNT characterization control."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_fulltext_pdf"
    master["notes"] += (
        " Purification branches begin from the same 100 mg as-prepared "
        "material basis and must not be summed as independent synthesis yields."
    )

    crude_id = add_common_author_records(
        tables,
        SOURCE_ID,
        "CRUDE_FFD",
        "as-prepared catalyst-free LPG FFD product",
        (
            "Crude flame-deposited material collected at 160 C contained a "
            "minimal CNT fraction with bundles wrapped by unconverted carbon "
            "and heavy LPG-derived oily/PAH material."
        ),
        "medium",
    )
    tables["yield_quality"].append(
        yield_row(
            crude_id,
            primary_yield_metric="crude_CNT_presence_and_impurity_profile",
            yield_original="mass yield not reported",
            yield_definition_original="not_reported",
            yield_calculation_method="not_applicable",
            yield_value_standardized="",
            yield_unit_standardized="not_applicable",
            secondary_result_summary=(
                "XRD impurity peaks before sequential purification: 14.78, "
                "29.47, 31.86 and 49.38 degrees 2theta."
            ),
            CNT_type_reported="multi-walled carbon nanotubes (MWCNTs)",
            CNT_type_confirmed="CNT filaments observed by AFM/TEM",
            product_mixture_summary=(
                "bundled carbon filaments with minimal CNT fraction, "
                "unconverted/amorphous carbon, carbon nanoparticles and "
                "LPG-derived heavy oil/PAH"
            ),
            CNT_type_evidence="AFM/TEM before purification",
            length_summary="not_reported before purification",
            morphology="bundled/agglomerated filaments wrapped by unconverted carbon",
            alignment_or_array="not_reported",
            purity_basis="qualitative AFM/TEM/XRD",
            residue_summary="unconverted carbon and aluminum-associated XRD peaks",
            amorphous_carbon_level="high qualitative impurity burden",
            characterization_methods="AFM; TEM; XRD",
            post_treatment_or_purification="none",
            purification_condition="not_applicable",
        )
    )

    h2o2_id = add_common_author_records(
        tables,
        SOURCE_ID,
        "H2O2",
        "FFD CNTs purified with H2O2 only",
        (
            "A 100 mg aliquot was sonicated in 50 mL of 30 wt.% H2O2, "
            "cold-aged, heated, washed and dried; TGA still showed organic "
            "and PAH-related losses."
        ),
        "high",
    )
    tables["reactor_process_gas"].extend(
        [
            process_row(
                h2o2_id,
                2,
                "H2O2_sonication_and_cold_aging",
                reactor_type="ultrasonic water bath and refrigerator",
                scale_level="lab_batch",
                reactor_material="not_reported",
                reactor_size_summary="50 mL H2O2 treatment volume",
                reactor_setup_summary="100 mg as-prepared CNTs in 30 wt.% H2O2",
                catalyst_loading_mass_g="0.1",
                temperature_program_summary=(
                    "sonicate at room temperature, then hold at 4 C"
                ),
                holding_time_min="1440",
                pressure_original="atmospheric",
                pressure_kPa="101.325",
                carbon_source="not_applicable_post_treatment",
                reducing_gas="not_applicable",
                inert_gas="not_applicable",
                cofeed_or_reactive_gas="30 wt.% H2O2",
                cofeed_flow_original="50 mL batch charge",
                total_flow_original="not_applicable",
                gas_composition_summary="not_applicable liquid purification",
                process_note=("Ultrasonic water bath for 1 h followed by 24 h at 4 C."),
            ),
            process_row(
                h2o2_id,
                3,
                "H2O2_decomposition_wash_and_dry",
                reactor_type="heated liquid-treatment and drying setup",
                scale_level="lab_batch",
                reactor_material="not_reported",
                reactor_size_summary="not_reported",
                reactor_setup_summary="treated CNT/H2O2 suspension",
                temperature_setpoint_C="50",
                temperature_program_summary=(
                    "warm to room temperature then gradually heat to 50 C "
                    "until H2O2 is destroyed; DI-water wash; dry at 80 C"
                ),
                holding_time_min="240",
                pressure_original="atmospheric",
                pressure_kPa="101.325",
                carbon_source="not_applicable_post_treatment",
                reducing_gas="not_applicable",
                inert_gas="not_applicable",
                cofeed_or_reactive_gas="deionized water wash",
                total_flow_original="not_applicable",
                gas_composition_summary="not_applicable liquid/solid post-treatment",
                process_note="The 4 h duration applies to drying at 80 C.",
            ),
        ]
    )
    tables["yield_quality"].append(
        yield_row(
            h2o2_id,
            primary_yield_metric="TGA_impurity_mass_loss_profile",
            yield_original="recovered mass yield not reported",
            yield_definition_original="not_reported",
            yield_calculation_method="not_applicable",
            yield_value_standardized="",
            yield_unit_standardized="not_applicable",
            secondary_result_summary=(
                "TGA under N2: about 4.3% loss below 400 C and 13.4% loss "
                "from 400-800 C."
            ),
            CNT_type_reported="multi-walled carbon nanotubes",
            CNT_type_confirmed="not separately imaged in the H2O2-only branch",
            product_mixture_summary=(
                "CNT-containing product retaining heavy organic material, "
                "amorphous carbon and traces of PAH"
            ),
            CNT_type_evidence="common synthesized CNT batch; TGA branch comparison",
            morphology="tubular bundles; H2O2 alone failed to decompose oil material",
            alignment_or_array="not_reported",
            TGA_carbon_content_wt_percent="not explicitly calculated",
            purified_product_purity_wt_percent="not_reported",
            purity_basis="semi-quantitative TGA under nitrogen",
            residue_summary=("4.3% low-temperature loss plus 13.4% 400-800 C loss"),
            amorphous_carbon_level="residual; associated with 13.4% TGA region",
            characterization_methods="AFM; TGA",
            post_treatment_or_purification="H2O2 oxidation",
            purification_condition=(
                "100 mg CNT; 50 mL 30 wt.% H2O2; sonicate 1 h; 4 C for "
                "24 h; heat to 50 C; wash; dry 80 C for 4 h"
            ),
        )
    )

    sequential_id = add_common_author_records(
        tables,
        SOURCE_ID,
        "H2O2_ACETONE",
        "FFD CNTs sequentially purified with H2O2 and acetone",
        (
            "The H2O2-treated and dried sample was additionally sonicated "
            "in acetone, centrifuged and calcined, producing individual tubular "
            "MWCNTs and an 84.53% TGA-estimated CNT ratio."
        ),
        "high",
    )
    tables["reactor_process_gas"].extend(
        [
            process_row(
                sequential_id,
                2,
                "H2O2_sonication_and_cold_aging",
                reactor_type="ultrasonic water bath and refrigerator",
                scale_level="lab_batch",
                reactor_material="not_reported",
                reactor_size_summary="50 mL H2O2 treatment volume",
                reactor_setup_summary="100 mg as-prepared CNTs in 30 wt.% H2O2",
                catalyst_loading_mass_g="0.1",
                temperature_program_summary=(
                    "sonicate at room temperature, then hold at 4 C"
                ),
                holding_time_min="1440",
                pressure_original="atmospheric",
                pressure_kPa="101.325",
                carbon_source="not_applicable_post_treatment",
                reducing_gas="not_applicable",
                inert_gas="not_applicable",
                cofeed_or_reactive_gas="30 wt.% H2O2",
                cofeed_flow_original="50 mL batch charge",
                total_flow_original="not_applicable",
                gas_composition_summary="not_applicable liquid purification",
                process_note=("Ultrasonic water bath for 1 h followed by 24 h at 4 C."),
            ),
            process_row(
                sequential_id,
                3,
                "H2O2_decomposition_wash_and_dry",
                reactor_type="heated liquid-treatment and drying setup",
                scale_level="lab_batch",
                reactor_material="not_reported",
                reactor_size_summary="not_reported",
                reactor_setup_summary="treated CNT/H2O2 suspension",
                temperature_setpoint_C="50",
                temperature_program_summary=(
                    "warm to room temperature then gradually heat to 50 C "
                    "until H2O2 is destroyed; DI-water wash; dry at 80 C"
                ),
                holding_time_min="240",
                pressure_original="atmospheric",
                pressure_kPa="101.325",
                carbon_source="not_applicable_post_treatment",
                reducing_gas="not_applicable",
                inert_gas="not_applicable",
                cofeed_or_reactive_gas="deionized water wash",
                total_flow_original="not_applicable",
                gas_composition_summary="not_applicable liquid/solid post-treatment",
                process_note="The 4 h duration applies to drying at 80 C.",
            ),
            process_row(
                sequential_id,
                4,
                "acetone_sonication_and_centrifugation",
                reactor_type="separation funnel/sonicator/centrifuge",
                scale_level="lab_batch",
                reactor_material="not_reported",
                reactor_size_summary="15 mL acetone batch",
                reactor_setup_summary="dried H2O2-treated CNTs dispersed in acetone",
                temperature_program_summary="acetone treatment temperature not reported",
                holding_time_min="15",
                pressure_original="atmospheric",
                pressure_kPa="101.325",
                carbon_source="not_applicable_post_treatment",
                reducing_gas="not_applicable",
                inert_gas="not_applicable",
                cofeed_or_reactive_gas="acetone",
                cofeed_flow_original="15 mL batch charge",
                total_flow_original="not_applicable",
                gas_composition_summary="not_applicable liquid purification",
                process_note="Sonicate 15 min, then centrifuge 15 min.",
            ),
            process_row(
                sequential_id,
                5,
                "post_purification_calcination",
                reactor_type="calcination furnace",
                scale_level="lab_batch",
                reactor_material="not_reported",
                reactor_size_summary="not_reported",
                reactor_setup_summary="separated acetone-treated CNTs",
                temperature_setpoint_C="275",
                temperature_program_summary="calcine at 275 C",
                holding_time_min="120",
                pressure_original="not_reported",
                pressure_kPa="",
                carbon_source="not_applicable_post_treatment",
                reducing_gas="not_applicable",
                inert_gas="not_reported",
                cofeed_or_reactive_gas="not_reported",
                total_flow_original="not_reported",
                gas_composition_summary="calcination atmosphere not reported",
                process_note="Final calcination after acetone separation.",
            ),
        ]
    )
    tables["yield_quality"].append(
        yield_row(
            sequential_id,
            primary_yield_metric="TGA_estimated_CNT_ratio",
            yield_original="84.53% CNT ratio by TGA",
            yield_definition_original=(
                "author-reported ratio of CNTs after heating to 800 C"
            ),
            yield_calculation_method="100 wt.% minus reported total 15.47 wt.% loss",
            yield_value_standardized="84.53",
            yield_unit_standardized="wt_percent",
            secondary_result_summary=(
                "TGA: 1.8% loss up to 400 C; principal loss begins at "
                "390 C and equals 14.03%; total loss to 800 C is 15.47 wt.%."
            ),
            CNT_type_reported="multi-walled carbon nanotubes (MWCNTs)",
            CNT_type_confirmed="tubular multiwall graphitic CNTs by AFM/TEM/XRD",
            product_mixture_summary=(
                "purified CNTs with strongly reduced unconverted carbon and "
                "oil/PAH impurities; thin amorphous film remains"
            ),
            CNT_type_evidence=(
                "AFM tubular morphology, TEM graphitic lattice and XRD carbon peaks"
            ),
            wall_number_summary="multi-walled; numerical wall count not reported",
            length_summary="0.8-2.1 micrometers",
            morphology="individual/small-bundle tubular filaments",
            alignment_or_array="not_reported",
            TGA_carbon_content_wt_percent="84.53",
            purified_product_purity_wt_percent="84.53",
            purity_basis="semi-quantitative TGA under nitrogen",
            residue_summary="15.47 wt.% total mass loss to 800 C",
            amorphous_carbon_level="thin amorphous film observed by HRTEM",
            characterization_methods="AFM; TEM/HRTEM; XRD; TGA",
            post_treatment_or_purification="sequential H2O2 oxidation and acetone washing",
            purification_condition=(
                "common H2O2 route; then 15 mL acetone, sonicate 15 min, "
                "centrifuge 15 min and calcine at 275 C for 2 h"
            ),
            application_property_summary=(
                "Graphitic interplanar spacing 0.35 nm; XRD peaks at "
                "26.56 and 44.16 degrees 2theta."
            ),
        )
    )

    reference_id = f"{SOURCE_ID}_ALDRICH_REF"
    tables["source_run"].append(
        run_row(
            SOURCE_ID,
            "ALDRICH_REF",
            "commercial Aldrich MWNT characterization reference",
            (
                "Commercial 95% MWNTs with 5.5 nm mode diameter were used "
                "as an XRD/TGA comparison, not synthesized by the authors."
            ),
            "high",
        )
    )
    tables["source_run"][-1].update(
        {
            "data_type": "experimental_reference",
            "target_track": "characterization_control",
            "relevance_class": "contextual_control",
        }
    )
    tables["catalyst_system"].append(
        catalyst_row(
            reference_id,
            catalyst_label="not_applicable_commercial_product",
            active_metals="not_reported",
            support_material="not_reported",
            promoter="not_reported",
            metal_ratio_original="not_reported",
            metal_ratio_standardized="not_applicable",
            precursor_summary="not_reported",
            preparation_method="not_reported_commercial_reference",
            preparation_modifier="not_reported",
            preparation_detail="Commercial Aldrich MWNT synthesis was not described.",
            drying_condition="not_reported",
            calcination_condition="not_reported",
            reduction_condition="not_reported",
            activation_condition="not_reported",
            post_preparation_condition="used without further purification",
            catalyst_particle_size_mean_nm="not_reported",
            catalyst_particle_size_range_nm="not_reported",
            catalyst_particle_size_qualifier="not_applicable",
            phase_or_state_summary="not_reported",
            dispersion_summary="not_reported",
            deactivation_summary="not_reported",
        )
    )
    tables["reactor_process_gas"].append(
        process_row(
            reference_id,
            1,
            "commercial_reference_material",
            reactor_type="not_applicable_commercial_reference",
            scale_level="commercial_reference",
            reactor_material="not_reported",
            reactor_size_summary="not_reported",
            reactor_setup_summary="MWNTs purchased from Aldrich",
            temperature_program_summary="not_applicable",
            holding_time_min="not_reported",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source="not_reported",
            reducing_gas="not_reported",
            inert_gas="not_reported",
            cofeed_or_reactive_gas="not_reported",
            total_flow_original="not_reported",
            gas_composition_summary="not_reported",
            process_note="The authors did not produce this comparator.",
        )
    )
    tables["yield_quality"].append(
        yield_row(
            reference_id,
            primary_yield_metric="commercial_purity_and_TGA_reference",
            yield_original="commercial purity 95%",
            yield_definition_original="supplier-reported purity",
            yield_calculation_method="not_applicable",
            yield_value_standardized="95",
            yield_unit_standardized="wt_percent_supplier_claim",
            secondary_result_summary=(
                "TGA under N2: about 1.43% loss from 200-400 C and "
                "8.97% loss above 400 C."
            ),
            CNT_type_reported="standard MWNTs",
            CNT_type_confirmed="commercial MWNT XRD/TGA reference",
            product_mixture_summary="commercial material; residual amorphous fraction by TGA",
            CNT_type_evidence="supplier identity and carbon XRD peaks",
            outer_diameter_mean_nm="5.5",
            outer_diameter_range_nm="not_reported",
            morphology="not separately imaged",
            alignment_or_array="not_reported",
            purified_product_purity_wt_percent="95",
            purity_basis="supplier-reported purity",
            residue_summary="8.97% high-temperature loss attributed to leftover amorphous material",
            amorphous_carbon_level="about 8.97% TGA loss above 400 C",
            characterization_methods="XRD; TGA",
            post_treatment_or_purification="used without further purification",
            purification_condition="not_applicable",
        )
    )
    tables["cost_scale_review"].append(
        cost_row(
            reference_id,
            scale_level_demonstrated="commercial_reference",
            scale_level_claimed="not_applicable",
            scale_evidence_summary="Purchased Aldrich comparison material.",
            reactor_capacity_or_throughput="not_applicable",
            continuous_operation_time_h="not_applicable",
            catalyst_lifetime_or_reuse="not_reported",
            batch_stability="not_reported",
            scale_up_issue="outside source scope",
            quantitative_cost_reported="not_reported",
            quantitative_cost_summary="purchase price not reported",
            cost_driver_summary="commercial MWNT purchase",
            safety_risk="nanopowder handling",
            emission_or_waste="not_reported",
            industrial_readiness_assessment="commercial characterization control only",
            reproduction_value="not_applicable for author synthesis",
            reproduction_priority="low",
            recommended_next_action="Do not count as author production.",
        )
    )

    author_runs = [crude_id, h2o2_id, sequential_id]
    for run_id in author_runs:
        append_evidence(
            tables,
            store,
            run_id,
            "CATALYST",
            "catalyst_system",
            f"{run_id}_CAT",
            "record_level",
            "SPAN_4051834B110A45B68711",
            "Abstract explicitly states catalyst-free LPG FFD synthesis at 160 C.",
        )
        append_pdf_evidence(
            tables,
            store,
            run_id,
            "SYNTHESIS",
            "reactor_process_gas",
            f"{run_id}_S01",
            "record_level",
            "SPAN_323976E18D9B9BD9155B",
            4,
            (
                "FFD in a homemade chamber of two stainless steel boxes; "
                "inner box 41 x 38 x 25 cm3, outer box 50 x 47 x 38 cm3; "
                "LPG, oxygen and nitrogen through three 1.5 cm inlet tubes; "
                "nine crucible collection positions. Abstract reports 160 C."
            ),
            "Homemade chamber geometry, gas identities and 160 C synthesis.",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            "record_level",
            "SPAN_A3276D1D5F84081AB770",
            "Authors claim an environmentally friendly and less expensive purification.",
            value_status="review_assessment",
        )

    append_pdf_evidence(
        tables,
        store,
        crude_id,
        "PRODUCT",
        "yield_quality",
        f"{crude_id}_PROD",
        "record_level",
        "SPAN_1D1D6797D9F6FC7FC22B",
        5,
        (
            "Before treatment, AFM shows bundles or quaffs of carbon filaments "
            "with a minimal CNT fraction, aggregations and heavy oil material; "
            "TEM shows unconverted carbon wrapping CNT bundles."
        ),
        "Crude-product CNT presence and impurity profile.",
    )
    append_evidence(
        tables,
        store,
        crude_id,
        "XRD",
        "yield_quality",
        f"{crude_id}_PROD",
        "secondary_result_summary;residue_summary",
        "SPAN_AA9DFC7DC55E596F579E",
        "Four pre-purification impurity peaks and their assignments.",
    )

    for run_id in [h2o2_id, sequential_id]:
        append_pdf_evidence(
            tables,
            store,
            run_id,
            "H2O2_STAGE_1",
            "reactor_process_gas",
            f"{run_id}_S02",
            "record_level",
            "SPAN_A3A1CAF420A76F6269D4",
            4,
            (
                "100 mg as-prepared CNTs dispersed in 50 mL H2O2 with an "
                "ultrasonic water bath for one hour, then held at 4 C for 24 h."
            ),
            "H2O2 charge, sonication and cold-aging conditions.",
        )
        append_pdf_evidence(
            tables,
            store,
            run_id,
            "H2O2_STAGE_2",
            "reactor_process_gas",
            f"{run_id}_S03",
            "record_level",
            "SPAN_A0F1D02FA08FED67DF06",
            4,
            (
                "Allow to reach room temperature, heat gradually to 50 C "
                "until H2O2 is destroyed, wash with DI water and dry at "
                "80 C for 4 h."
            ),
            "H2O2 decomposition, washing and drying conditions.",
        )

    append_evidence(
        tables,
        store,
        h2o2_id,
        "PRODUCT",
        "yield_quality",
        f"{h2o2_id}_PROD",
        "record_level",
        "SPAN_8352E7A3AB27D099E18E",
        "H2O2-only TGA losses and residual impurity assignments.",
    )

    append_pdf_evidence(
        tables,
        store,
        sequential_id,
        "ACETONE",
        "reactor_process_gas",
        f"{sequential_id}_S04",
        "record_level",
        "SPAN_A0F1D02FA08FED67DF06",
        4,
        (
            "Dried sample dispersed in 15 mL acetone, sonicated for 15 min "
            "and centrifuged for 15 min."
        ),
        "Acetone charge, sonication and centrifugation.",
    )
    append_pdf_evidence(
        tables,
        store,
        sequential_id,
        "CALCINATION",
        "reactor_process_gas",
        f"{sequential_id}_S05",
        "record_level",
        "SPAN_A0F1D02FA08FED67DF06",
        4,
        "The separated CNTs were calcined at 275 C for 2 h.",
        "Final calcination temperature and duration.",
    )
    append_pdf_evidence(
        tables,
        store,
        sequential_id,
        "MORPHOLOGY",
        "yield_quality",
        f"{sequential_id}_PROD",
        "length_summary;morphology;CNT_type_confirmed",
        "SPAN_1D1D6797D9F6FC7FC22B",
        5,
        (
            "Sequential H2O2/acetone treatment gives tubular CNT structures "
            "with length 0.8-2.1 micrometers; TEM shows impurities removed "
            "and CNTs visualized as single filaments."
        ),
        "Purified-product length and morphology.",
    )
    append_pdf_evidence(
        tables,
        store,
        sequential_id,
        "STRUCTURE",
        "yield_quality",
        f"{sequential_id}_PROD",
        "application_property_summary;amorphous_carbon_level",
        "SPAN_AA9DFC7DC55E596F579E",
        6,
        (
            "HRTEM reports graphite lattice interplanar spacing 0.35 nm, "
            "high outer-wall crystallinity and a thin amorphous film; "
            "purified XRD peaks occur at 26.56 and 44.16 degrees 2theta."
        ),
        "HRTEM spacing, crystallinity and XRD peaks.",
    )
    append_evidence(
        tables,
        store,
        sequential_id,
        "TGA",
        "yield_quality",
        f"{sequential_id}_PROD",
        (
            "yield_original;yield_value_standardized;secondary_result_summary;"
            "TGA_carbon_content_wt_percent;purified_product_purity_wt_percent;"
            "residue_summary"
        ),
        "SPAN_8352E7A3AB27D099E18E",
        "Sequential-product TGA losses and author-reported 84.53% CNT ratio.",
    )

    append_evidence(
        tables,
        store,
        reference_id,
        "MATERIAL",
        "catalyst_system",
        f"{reference_id}_CAT",
        "record_level",
        "SPAN_6353F61036111BFECEF9",
        "Commercial Aldrich MWNTs were used without further purification.",
    )
    append_evidence(
        tables,
        store,
        reference_id,
        "PROCESS",
        "reactor_process_gas",
        f"{reference_id}_S01",
        "record_level",
        "SPAN_6353F61036111BFECEF9",
        "The material was purchased; no author synthesis process applies.",
        value_status="not_applicable",
    )
    append_evidence(
        tables,
        store,
        reference_id,
        "PRODUCT",
        "yield_quality",
        f"{reference_id}_PROD",
        (
            "yield_original;yield_value_standardized;outer_diameter_mean_nm;"
            "purified_product_purity_wt_percent"
        ),
        "SPAN_6353F61036111BFECEF9",
        "Supplier purity and mode diameter of the Aldrich MWNT reference.",
    )
    append_evidence(
        tables,
        store,
        reference_id,
        "TGA",
        "yield_quality",
        f"{reference_id}_PROD",
        "secondary_result_summary;residue_summary;amorphous_carbon_level",
        "SPAN_B7D54B3F0D54BF069870",
        "Aldrich reference TGA losses under nitrogen.",
    )
    append_evidence(
        tables,
        store,
        reference_id,
        "COST",
        "cost_scale_review",
        reference_id,
        "record_level",
        "SPAN_6353F61036111BFECEF9",
        "Commercial reference only; purchase price is absent.",
        value_status="review_assessment",
    )

    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_SYNTHESIS_001",
                SOURCE_ID,
                crude_id,
                "critical_data_gap",
                "reactor_process_gas",
                f"{crude_id}_S01",
                "carbon_source_flow_original",
                (
                    "LPG/O2/N2 flow rates, deposition duration and pressure "
                    "are not reported in this paper; detailed synthesis is "
                    "referred to earlier work."
                ),
                f"EVD_{crude_id}_SYNTHESIS",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_001",
                SOURCE_ID,
                crude_id,
                "critical_data_gap",
                "yield_quality",
                f"{crude_id}_PROD",
                "yield_original",
                "No crude CNT mass yield, LPG conversion or productivity is reported.",
                f"EVD_{crude_id}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_OVERLAP_001",
                SOURCE_ID,
                sequential_id,
                "shared_batch_branching",
                "source_run",
                sequential_id,
                "run_summary",
                (
                    "Crude, H2O2-only and sequential records are treatment "
                    "branches from the same as-prepared CNT basis, not additive "
                    "independent synthesis yields."
                ),
                (f"EVD_{h2o2_id}_H2O2_STAGE_1;EVD_{sequential_id}_H2O2_STAGE_1"),
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_H2O2_PURITY_001",
                SOURCE_ID,
                h2o2_id,
                "reported_value_not_derived",
                "yield_quality",
                f"{h2o2_id}_PROD",
                "purified_product_purity_wt_percent",
                (
                    "The H2O2-only branch reports 4.3% and 13.4% TGA regions "
                    "but does not state a total CNT purity; no purity is derived."
                ),
                f"EVD_{h2o2_id}_PRODUCT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_TGA_001",
                SOURCE_ID,
                sequential_id,
                "method_limit",
                "yield_quality",
                f"{sequential_id}_PROD",
                "purified_product_purity_wt_percent",
                (
                    "The source itself describes TGA CNT fraction estimation "
                    "as semi-quantitative rather than a precise quantitative technique."
                ),
                f"EVD_{sequential_id}_TGA",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_RECOVERY_001",
                SOURCE_ID,
                sequential_id,
                "critical_data_gap",
                "yield_quality",
                f"{sequential_id}_PROD",
                "yield_original",
                (
                    "The 84.53% value is a TGA-estimated composition, not "
                    "recovered product mass yield; purification recovery is absent."
                ),
                f"EVD_{sequential_id}_TGA",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_ALUMINUM_001",
                SOURCE_ID,
                crude_id,
                "source_interpretation_ambiguity",
                "yield_quality",
                f"{crude_id}_PROD",
                "residue_summary",
                (
                    "The source assigns two XRD impurity peaks to aluminum "
                    "used as a precipitation support, although the FFD synthesis "
                    "section does not clearly define that support."
                ),
                f"EVD_{crude_id}_XRD",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_REFERENCE_001",
                SOURCE_ID,
                reference_id,
                "non_author_synthesis_control",
                "source_run",
                reference_id,
                "data_type",
                (
                    "The Aldrich record is a commercial characterization "
                    "control and must not be counted as author CNT production."
                ),
                f"EVD_{reference_id}_MATERIAL",
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
