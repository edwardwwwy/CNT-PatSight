#!/usr/bin/env python3
"""Build the fourteenth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 14
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_0682357008FA0412"


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


def append_contact_angle_pdf_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    collector: str,
    angle: str,
) -> None:
    evidence = evidence_row(
        store,
        SOURCE_ID,
        f"EVD_{run_id}_CONTACT_ANGLE_PDF",
        run_id,
        "yield_quality",
        f"{run_id}_PROD",
        "application_property_summary",
        "SPAN_36C7686196D68B282130",
        "Collector-specific water contact angle visually checked in Figure 9.",
    )
    evidence.update(
        {
            "evidence_type": "pdf_figure_value_transcription",
            "source_section": "Application of VACNTs; Figure 9d",
            "source_locator": "PDF page 15",
            "source_object_ref": (
                f"data/raw/fulltext/pdf/{SOURCE_ID}_dc85e16355b1.pdf#page=15"
            ),
            "evidence_text": (
                f"Figure 9d reports a water contact angle of {angle} degrees "
                f"for CNTs on the {collector} collector."
            ),
            "evidence_summary": (
                f"PDF Figure 9d confirms the {collector} contact angle."
            ),
            "notes": "Locally stored PDF was visually inspected.",
        }
    )
    tables["evidence_index"].append(evidence)


def floating_catalyst(
    run_id: str,
    collector: str,
    ratio: str,
) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label="in-situ floating Fe species from ferrocene",
        active_metals="Fe",
        support_material=collector,
        promoter="not_applicable",
        metal_ratio_original=ratio,
        metal_ratio_standardized="not_applicable",
        precursor_summary="pre-mixed camphor carbon source and ferrocene catalyst",
        preparation_method="single_stage_floating_catalyst_in_situ_pyrolysis",
        preparation_modifier=(
            "precursor container placed in the ceramic-tube preheat zone"
        ),
        preparation_detail=(
            "Ferrocene and camphor were mixed in a ceramic container; "
            "ferrocene decomposed in the inlet/preheat region and Fe species "
            "were transported by nitrogen to collector surfaces."
        ),
        drying_condition="not_applicable",
        calcination_condition="not_applicable",
        reduction_condition="not separately reported",
        activation_condition="in-situ ferrocene pyrolysis under N2",
        post_preparation_condition="continuously generated floating catalyst",
        catalyst_particle_size_mean_nm="not_reported",
        catalyst_particle_size_range_nm="not_reported",
        catalyst_particle_size_qualifier=(
            "CNT-embedded Fe dimensions are not mapped as active catalyst size"
        ),
        phase_or_state_summary=(
            "Fe, Fe3C and oxidized iron species identified after synthesis"
        ),
        dispersion_summary=(
            "small floating Fe species deposited more uniformly on alumina "
            "than on smooth Si or bare Cu"
        ),
        deactivation_summary=("graphitic encapsulation can reduce catalytic activity"),
    )


def ss_process(
    run_id: str,
    collector: str,
) -> dict[str, str]:
    return process_row(
        run_id,
        1,
        "single_stage_floating_catalyst_CVD_growth",
        reactor_type="single-zone SS-FCCVD tube furnace",
        scale_level="gram_scale_batch",
        reactor_material="alumina ceramic tube",
        reactor_size_summary=(
            "75 mm inner diameter; 1000 mm tube length; "
            "300 mm constant-temperature zone"
        ),
        reactor_setup_summary=(
            f"Camphor/ferrocene source 15 cm from the tube inlet; {collector} "
            "collector in the 850 C reaction zone."
        ),
        temperature_setpoint_C="850",
        temperature_program_summary=(
            "Heat at 10 C/min to 850 C; preheat-zone gradient 21 C/cm; "
            "nitrogen purge maintained through cooling."
        ),
        holding_time_min="60",
        heating_rate_C_min="10",
        pressure_original="atmospheric",
        pressure_kPa="101.325",
        carbon_source="camphor",
        carbon_source_flow_original="17 g feed for the reported production batch",
        reducing_gas="not_applicable",
        inert_gas="N2",
        inert_gas_flow_original="400 sccm",
        cofeed_or_reactive_gas="ferrocene vapor",
        cofeed_flow_original="camphor/ferrocene mass ratio 20:1",
        total_flow_original="400 sccm N2; precursor vapor contribution not reported",
        gas_composition_summary=(
            "20:1 camphor/ferrocene mixture transported in high-purity N2"
        ),
        process_note=(
            "Products were collected separately from the silicon wafer, "
            "copper plate, ceramic boat and alumina-tube inner wall; "
            "estimated gas residence time was approximately 52 s."
        ),
    )


def product_cost(
    run_id: str,
    collector: str,
    scale: str = "gram_scale_batch",
) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated=scale,
        scale_level_claimed="scalable_mass_production",
        scale_evidence_summary=(
            "Single-zone floating-catalyst process uses reactor and collector "
            f"surfaces directly; this record concerns {collector}."
        ),
        reactor_capacity_or_throughput="shared SS-FCCVD production batch",
        continuous_operation_time_h="not_reported",
        catalyst_lifetime_or_reuse="not_reported",
        batch_stability="temperature profile reported to stabilize before growth",
        scale_up_issue=(
            "Control precursor evaporation, Fe coalescence, collector geometry "
            "and deposition uniformity across the reaction zone."
        ),
        cost_driver_summary=(
            "Camphor, ferrocene, high-purity nitrogen and single-zone furnace duty"
        ),
        safety_risk=(
            "Ferrocene/camphor vapor and hot carbon/iron nanoparticle exposure"
        ),
        emission_or_waste=(
            "Unreacted or condensed precursor and hydrocarbon pyrolysis exhaust; "
            "quantities not reported"
        ),
        industrial_readiness_assessment=(
            "Gram-scale batch demonstrated; mass-production suitability claimed"
        ),
        reproduction_value="high after clarifying collector-specific mass yield",
        reproduction_priority="high",
        recommended_next_action=(
            "Repeat with collector-resolved mass balance and precursor utilization"
        ),
    )


def add_ss_record(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    code: str,
    label: str,
    summary: str,
    collector: str,
    product: dict[str, str],
    result_span: str,
    *,
    data_type: str = "experimental_product_sample",
) -> str:
    run_id = f"{SOURCE_ID}_{code}"
    source_run = run_row(SOURCE_ID, code, label, summary, "medium")
    source_run["data_type"] = data_type
    tables["source_run"].append(source_run)
    tables["catalyst_system"].append(
        floating_catalyst(run_id, collector, "camphor/ferrocene 20:1 by mass")
    )
    tables["reactor_process_gas"].append(ss_process(run_id, collector))
    tables["yield_quality"].append(product)
    tables["cost_scale_review"].append(product_cost(run_id, collector))

    append_evidence(
        tables,
        store,
        run_id,
        "CATALYST",
        "catalyst_system",
        f"{run_id}_CAT",
        "record_level",
        "SPAN_8334AEBF8CCEC0CD60CB",
        "Camphor/ferrocene ratio and in-tube precursor placement.",
    )
    for suffix, span_id, summary_text in [
        (
            "PROCESS_REACTOR",
            "SPAN_32066AB2595A8BB7CE42",
            "Alumina reactor dimensions and 850 C constant-temperature zone.",
        ),
        (
            "PROCESS_FLOW",
            "SPAN_07CFF09581748D597BBD",
            "Nitrogen flow, residence time and temperature-profile stabilization.",
        ),
        (
            "PROCESS_GROWTH",
            "SPAN_696F3D45F75A9978EF0B",
            "One-hour growth, nitrogen flow, cooling and collector list.",
        ),
        (
            "PROCESS_DETAIL",
            "SPAN_53AE3F11A01E0B0A0F05",
            "Heating rate, atmospheric pressure and tested collector substrates.",
        ),
        (
            "PROCESS_PRECURSOR",
            "SPAN_8334AEBF8CCEC0CD60CB",
            "Precursor ratio and 15 cm source position.",
        ),
        (
            "PROCESS_FEED",
            "SPAN_F33586BE7DA62FE933FC",
            "Reported 17 g camphor feed for the shared production batch.",
        ),
    ]:
        append_evidence(
            tables,
            store,
            run_id,
            suffix,
            "reactor_process_gas",
            f"{run_id}_S01",
            "record_level",
            span_id,
            summary_text,
        )
    append_evidence(
        tables,
        store,
        run_id,
        "YIELD",
        "yield_quality",
        f"{run_id}_PROD",
        "record_level",
        result_span,
        f"Collector-specific outcome for {label}.",
    )
    append_evidence(
        tables,
        store,
        run_id,
        "COST",
        "cost_scale_review",
        run_id,
        "record_level",
        "SPAN_633A7F2A9210E053D992",
        "Scalability and mass-production claim for SS-FCCVD.",
        "review_assessment",
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
                "Author experiments separated into an external-heater Si "
                "baseline, an overall SS-FCCVD production batch, four "
                "collector-specific co-products and two ceramic-plate "
                "precursor-ratio conditions."
            ),
        )
    )
    tables["source_master"][0]["local_file_path"] = (
        f"data/interim/parsed_text/{SOURCE_ID}/full_text.txt"
    )
    tables["source_master"][0]["notes"] += (
        " PDF pages 4, 8, 9, 15 and 16 were visually inspected for the "
        "process, Table 1, microscopy, contact-angle and adsorption values."
    )

    baseline_id = f"{SOURCE_ID}_EXT_SI"
    tables["source_run"].append(
        run_row(
            SOURCE_ID,
            "EXT_SI",
            "external-heater camphor/ferrocene CVD on Si(100)",
            (
                "Pre-SS-FCCVD baseline at 850 C produced low-yield, "
                "randomly oriented approximately 80 nm CNTs and no VACNT forest."
            ),
            "medium",
        )
    )
    tables["catalyst_system"].append(
        floating_catalyst(
            baseline_id,
            "non-thermally oxidized Si(100)",
            "camphor/ferrocene ratio not reported for this baseline",
        )
    )
    tables["reactor_process_gas"].append(
        process_row(
            baseline_id,
            1,
            "external_heater_camphor_ferrocene_CVD",
            reactor_type="single-stage CVD with external precursor heater",
            reactor_material="not_reported",
            reactor_size_summary="not_reported",
            reactor_setup_summary=(
                "External heater vaporized camphor/ferrocene; vapors condensed "
                "in the connecting copper tube before reaching the Si substrate."
            ),
            temperature_setpoint_C="850",
            holding_time_min="not_reported",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source="camphor",
            reducing_gas="not_applicable",
            inert_gas="not_reported",
            gas_composition_summary="not_reported",
            process_note="Preliminary system abandoned because of precursor loss.",
        )
    )
    tables["yield_quality"].append(
        yield_row(
            baseline_id,
            primary_yield_metric="qualitative_CNT_growth_outcome",
            yield_original="low yield; no observable VACNT forest",
            yield_definition_original="SEM-observed alignment and relative yield",
            yield_calculation_method="qualitative microscopy observation",
            yield_value_standardized="",
            yield_unit_standardized="not_applicable",
            secondary_result_summary=(
                "Randomly oriented, bent and loosely packed CNTs with "
                "approximately 80 nm average diameter."
            ),
            CNT_type_reported="carbon nanotubes",
            CNT_type_confirmed="MWCNTs not specifically confirmed for baseline",
            product_mixture_summary="low-carbon-content random CNT agglomerates",
            CNT_type_evidence="SEM morphology only",
            outer_diameter_mean_nm="80",
            morphology="combed-yarn and bird's-nest agglomerates",
            alignment_or_array="randomly oriented; no VACNT array",
            amorphous_carbon_level="not_reported",
            characterization_methods="SEM",
            post_treatment_or_purification="none reported",
            purification_condition="not_applicable",
        )
    )
    tables["cost_scale_review"].append(
        product_cost(baseline_id, "Si(100)", "lab_batch")
    )
    append_evidence(
        tables,
        store,
        baseline_id,
        "CATALYST",
        "catalyst_system",
        f"{baseline_id}_CAT",
        "record_level",
        "SPAN_767102B5ADE73EDFAABE",
        "External-heater camphor/ferrocene baseline on Si.",
    )
    append_evidence(
        tables,
        store,
        baseline_id,
        "PROCESS",
        "reactor_process_gas",
        f"{baseline_id}_S01",
        "record_level",
        "SPAN_767102B5ADE73EDFAABE",
        "External-heater baseline at 850 C.",
    )
    append_evidence(
        tables,
        store,
        baseline_id,
        "PROCESS_FAILURE",
        "reactor_process_gas",
        f"{baseline_id}_S01",
        "reactor_setup_summary;process_note",
        "SPAN_8334AEBF8CCEC0CD60CB",
        "Condensation and unreacted-precursor problem in the earlier setup.",
    )
    append_evidence(
        tables,
        store,
        baseline_id,
        "YIELD",
        "yield_quality",
        f"{baseline_id}_PROD",
        "record_level",
        "SPAN_767102B5ADE73EDFAABE",
        "Low-yield random 80 nm CNT morphology and absence of VACNTs.",
    )
    append_evidence(
        tables,
        store,
        baseline_id,
        "COST",
        "cost_scale_review",
        baseline_id,
        "record_level",
        "SPAN_8334AEBF8CCEC0CD60CB",
        "Precursor-loss limitation of the external-heater setup.",
        "review_assessment",
    )

    batch_id = add_ss_record(
        tables,
        store,
        "SS_BATCH",
        "overall 20:1 SS-FCCVD production batch",
        (
            "One-hour 850 C run using 17 g camphor produced approximately "
            "10 g VACNT-containing product at reported productivity near 60%."
        ),
        "alumina tube, ceramic boat, Si and Cu collectors",
        yield_row(
            f"{SOURCE_ID}_SS_BATCH",
            primary_yield_metric="reported_total_VACNT_product_mass",
            yield_original=(
                "approximately 10 g VACNT product from 17 g camphor; "
                "reported productivity approximately 60%"
            ),
            yield_definition_original=(
                "reported product mass relative to camphor feed; "
                "collector allocation not provided"
            ),
            yield_calculation_method="reported approximate batch productivity",
            yield_value_standardized="60",
            yield_unit_standardized="percent",
            secondary_result_summary=(
                "Products were collected separately from four collector locations."
            ),
            CNT_type_reported="vertically aligned carbon nanotubes",
            CNT_type_confirmed="VA-MWCNTs with Fe-containing co-product",
            product_mixture_summary=(
                "collector-dependent VACNT, random CNT and amorphous/graphitic "
                "carbon products"
            ),
            CNT_type_evidence="SEM/TEM/XRD/Raman/TGA characterization",
            morphology="collector-dependent",
            alignment_or_array="VACNT on alumina; random or poor growth on Si/Cu",
            purity_basis="collector-resolved purity not reported",
            residue_summary="iron-containing CNT product",
            characterization_methods="SEM; TEM; XRD; Raman; FTIR; XPS; TGA; BET",
            post_treatment_or_purification="none reported before characterization",
            purification_condition="not_applicable",
            application_property_summary=(
                "Fe/CNT BET area 62.438 m2/g; mean pore diameter 8.84 nm; "
                "pore volume 0.138 cc/g; Cr(VI) adsorption 0.206 +/- "
                "0.007 mmol/m2 at pH 5, R2 0.97; Langmuir surface coverage "
                "0.828 micromol/m2."
            ),
        ),
        "SPAN_F33586BE7DA62FE933FC",
        data_type="experimental_batch_summary",
    )
    append_evidence(
        tables,
        store,
        batch_id,
        "APPLICATION",
        "yield_quality",
        f"{batch_id}_PROD",
        "application_property_summary",
        "SPAN_8F0AB7C8019DD472932F",
        "Cr(VI) adsorption, pore diameter, pore volume and surface coverage.",
    )
    append_evidence(
        tables,
        store,
        batch_id,
        "BET",
        "yield_quality",
        f"{batch_id}_PROD",
        "application_property_summary",
        "SPAN_4EF999DB9FC4CCB687D7",
        "BET area and preliminary maximum-adsorption conditions.",
    )
    tables["cost_scale_review"][-1].update(
        {
            "reactor_capacity_or_throughput": (
                "approximately 10 g product from 17 g camphor in a 1 h run"
            ),
            "quantitative_cost_reported": "not_reported",
            "quantitative_cost_summary": (
                "No currency cost; reported batch productivity approximately 60%"
            ),
        }
    )
    append_evidence(
        tables,
        store,
        batch_id,
        "COST_THROUGHPUT",
        "cost_scale_review",
        batch_id,
        "reactor_capacity_or_throughput;quantitative_cost_summary",
        "SPAN_F33586BE7DA62FE933FC",
        "Reported batch feed, product mass and approximate productivity.",
        "review_assessment",
    )

    tube_id = add_ss_record(
        tables,
        store,
        "AL_TUBE",
        "VACNT product on alumina ceramic tube inner wall",
        (
            "Ordered VA-MWCNTs approximately 1.0 mm long and 50 nm outer "
            "diameter; Table 1 reports a 16 micrometers/min growth rate."
        ),
        "concave alumina ceramic tube inner wall",
        yield_row(
            f"{SOURCE_ID}_AL_TUBE",
            primary_yield_metric="VACNT_growth_rate",
            yield_original=("16 micrometers/min; approximately 1.0 mm VACNT length"),
            yield_definition_original="Table 1 growth rate and reported length",
            yield_calculation_method="reported value",
            yield_value_standardized="16",
            yield_unit_standardized="micrometers/min",
            secondary_result_summary=(
                "Outer diameter about 50 nm; inner diameter about 10 nm; "
                "approximately 15 graphitic walls; ID/IG 0.81 and ID/I2D 0.83."
            ),
            CNT_type_reported="VACNTs",
            CNT_type_confirmed="VA-MWCNTs",
            product_mixture_summary=(
                "well-aligned MWCNTs with carbon-encapsulated and surface Fe"
            ),
            CNT_type_evidence="TEM identifies multiwall hollow tubes",
            outer_diameter_mean_nm="50",
            inner_diameter_mean_nm="10",
            wall_number_summary="approximately 15 concentric graphitic layers",
            length_summary="approximately 1.0 mm",
            morphology="smooth bundled VA-MWCNTs",
            alignment_or_array="well-aligned forest on concave tube wall",
            Raman_ratio_type="ID/IG; ID/I2D",
            Raman_ratio_value="0.81; 0.83",
            Raman_laser_wavelength_nm="780",
            TGA_carbon_content_wt_percent="approximately 95",
            purity_basis="air TGA residual-mass interpretation",
            residue_summary=(
                "4.986% low residual mass attributed to embedded iron "
                "nanoparticles; initial 1.301% loss from oxygenated groups"
            ),
            amorphous_carbon_level="low",
            characterization_methods="SEM; TEM; XRD; Raman; FTIR; XPS; TGA",
            post_treatment_or_purification="none reported",
            purification_condition="not_applicable",
            application_property_summary="water contact angle 154 degrees",
        ),
        "SPAN_F33586BE7DA62FE933FC",
    )
    for suffix, fields, span_id, summary_text in [
        (
            "TABLE1_RATE",
            (
                "yield_original;yield_value_standardized;"
                "yield_unit_standardized;length_summary"
            ),
            "SPAN_1EF1BF8F13BF1E5904B2",
            "Table 1 reports the 16 micrometers/min rate and 1.0 mm length.",
        ),
        (
            "TEM",
            (
                "CNT_type_confirmed;inner_diameter_mean_nm;"
                "wall_number_summary;product_mixture_summary"
            ),
            "SPAN_68659F1389AE89178DBC",
            "TEM identity, inner diameter, graphitic walls and encapsulated Fe.",
        ),
        (
            "RAMAN",
            "Raman_ratio_type;Raman_ratio_value",
            "SPAN_A912BEFCFB4447169662",
            "Reported ID/IG and ID/I2D ratios.",
        ),
        (
            "RAMAN_METHOD",
            "Raman_laser_wavelength_nm",
            "SPAN_8334AEBF8CCEC0CD60CB",
            "Reported 780 nm Raman excitation wavelength.",
        ),
        (
            "TGA_LOSS",
            "residue_summary;amorphous_carbon_level",
            "SPAN_8E32688D5035DEE5917C",
            "Initial TGA mass loss and low amorphous-carbon interpretation.",
        ),
        (
            "TGA_PURITY",
            "TGA_carbon_content_wt_percent;purity_basis;residue_summary",
            "SPAN_8A00FEC5E1658593FCE7",
            "Residual mass and approximately 95% carbon purity.",
        ),
    ]:
        append_evidence(
            tables,
            store,
            tube_id,
            suffix,
            "yield_quality",
            f"{tube_id}_PROD",
            fields,
            span_id,
            summary_text,
        )
    append_contact_angle_pdf_evidence(
        tables,
        store,
        tube_id,
        "alumina ceramic tube",
        "154",
    )

    boat_id = add_ss_record(
        tables,
        store,
        "AL_BOAT",
        "VACNT product on alumina ceramic boat",
        (
            "Perpendicular flow over the boat produced approximately 1.2 mm "
            "VACNTs of about 60 nm diameter at 20 micrometers/min."
        ),
        "alumina ceramic boat",
        yield_row(
            f"{SOURCE_ID}_AL_BOAT",
            primary_yield_metric="VACNT_growth_rate",
            yield_original=("20 micrometers/min; approximately 1.2 mm VACNT length"),
            yield_definition_original="Table 1 growth rate and reported length",
            yield_calculation_method="reported value",
            yield_value_standardized="20",
            yield_unit_standardized="micrometers/min",
            secondary_result_summary="approximately 60 nm CNT diameter",
            CNT_type_reported="VACNTs",
            CNT_type_confirmed="VA-MWCNTs",
            product_mixture_summary="long bundled VACNT forest with low impurities",
            CNT_type_evidence="SEM/TEM characterization of alumina products",
            outer_diameter_mean_nm="60",
            wall_number_summary="multi-walled; boat-specific count not reported",
            length_summary="approximately 1.2 mm",
            morphology="bundled forest-like VACNTs",
            alignment_or_array="vertically aligned forest",
            purity_basis="low impurities stated; collector-specific TGA not mapped",
            residue_summary="not_reported",
            amorphous_carbon_level="low impurities reported",
            characterization_methods="SEM; TEM",
            post_treatment_or_purification="none reported",
            purification_condition="not_applicable",
            application_property_summary="water contact angle 149 degrees",
        ),
        "SPAN_F33586BE7DA62FE933FC",
    )
    append_contact_angle_pdf_evidence(
        tables,
        store,
        boat_id,
        "alumina ceramic boat",
        "149",
    )

    silicon_id = add_ss_record(
        tables,
        store,
        "SS_SI",
        "SS-FCCVD product on Si(100) plate",
        "Smooth Si supported random, non-uniform CNT clusters rather than VACNTs.",
        "non-thermally oxidized Si(100) plate",
        yield_row(
            f"{SOURCE_ID}_SS_SI",
            primary_yield_metric="qualitative_collector_growth_outcome",
            yield_original="random non-uniform CNT growth; no aligned forest",
            yield_definition_original="SEM morphology by collector",
            yield_calculation_method="qualitative microscopy observation",
            yield_value_standardized="",
            yield_unit_standardized="not_applicable",
            secondary_result_summary=(
                "Larger Fe particles and clustered, lower-roughness CNT deposit."
            ),
            CNT_type_reported="CNTs",
            CNT_type_confirmed="not further classified",
            product_mixture_summary="random CNT clusters",
            CNT_type_evidence="SEM",
            morphology="non-uniform clustered CNTs",
            alignment_or_array="randomly oriented",
            characterization_methods="SEM; contact-angle imaging",
            post_treatment_or_purification="none reported",
            purification_condition="not_applicable",
            application_property_summary="water contact angle 82 degrees",
        ),
        "SPAN_7BABC85F5E3164699A2F",
    )
    append_contact_angle_pdf_evidence(
        tables,
        store,
        silicon_id,
        "silicon plate",
        "82",
    )

    add_ss_record(
        tables,
        store,
        "SS_CU",
        "SS-FCCVD product on bare Cu(111) plate",
        "Bare copper produced a brittle amorphous/graphitic carbon carpet.",
        "bare Cu(111) plate",
        yield_row(
            f"{SOURCE_ID}_SS_CU",
            primary_yield_metric="qualitative_collector_growth_outcome",
            yield_original="brittle amorphous and graphitic carbon carpet",
            yield_definition_original="observed collector deposit",
            yield_calculation_method="qualitative microscopy observation",
            yield_value_standardized="",
            yield_unit_standardized="not_applicable",
            secondary_result_summary=(
                "Insufficient active catalyst was attributed to Fe diffusion "
                "into bare copper."
            ),
            CNT_type_reported="carbon structures",
            CNT_type_confirmed="not_applicable",
            product_mixture_summary="amorphous and graphitic carbon",
            CNT_type_evidence="No successful CNT assignment for bare Cu",
            morphology="brittle carbon carpet",
            alignment_or_array="not_applicable",
            amorphous_carbon_level="high/mixed with graphitic carbon",
            characterization_methods="SEM",
            post_treatment_or_purification="none reported",
            purification_condition="not_applicable",
        ),
        "SPAN_D4C6165DC117E8A19AFA",
    )

    for code, ratio in [("PLATE20", "20:1"), ("PLATE15_2", "15:2")]:
        run_id = f"{SOURCE_ID}_{code}"
        source_run = run_row(
            SOURCE_ID,
            code,
            f"4 x 4 cm ceramic plate; camphor/ferrocene {ratio}",
            (
                "Additional ceramic-plate SS-FCCVD ratio condition; exact "
                "collector-specific yield and property values are not mapped "
                "in the main article."
            ),
            "low",
        )
        source_run["data_type"] = "experimental_condition_unmapped_outcome"
        tables["source_run"].append(source_run)
        tables["catalyst_system"].append(
            floating_catalyst(
                run_id,
                "4 x 4 cm alumina ceramic plate",
                f"camphor/ferrocene {ratio} by mass",
            )
        )
        tables["reactor_process_gas"].append(
            process_row(
                run_id,
                1,
                "ceramic_plate_ratio_optimization",
                reactor_type="single-stage SS-FCCVD",
                reactor_material="alumina ceramic tube",
                reactor_size_summary="4 x 4 cm ceramic plate collector",
                reactor_setup_summary="plate positioned perpendicular to gas flow",
                temperature_setpoint_C="not_reported",
                holding_time_min="not_reported",
                pressure_original="not_reported",
                pressure_kPa="",
                carbon_source="camphor",
                reducing_gas="not_applicable",
                inert_gas="N2",
                cofeed_or_reactive_gas="ferrocene vapor",
                cofeed_flow_original=f"camphor/ferrocene mass ratio {ratio}",
                gas_composition_summary=(
                    "additional ratio test; other exact settings not repeated"
                ),
                process_note=(
                    "Main text says the ratios were tested but points to "
                    "supplementary comparison for detailed effects."
                ),
            )
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="condition_tested_without_mapped_outcome",
                yield_original="not_reported",
                yield_definition_original="not_reported",
                yield_calculation_method="not_applicable",
                yield_value_standardized="",
                yield_unit_standardized="not_applicable",
                secondary_result_summary=(
                    "Growth, quality, length and hydrophobicity were compared, "
                    "but exact values by ratio are absent from the main article."
                ),
                CNT_type_reported="VACNTs",
                CNT_type_confirmed="not separately confirmed by ratio",
                product_mixture_summary="not_reported",
                CNT_type_evidence="condition reported without mapped product row",
                morphology="not_reported",
                alignment_or_array="not_reported",
                characterization_methods="not separately mapped",
                post_treatment_or_purification="none reported",
                purification_condition="not_applicable",
            )
        )
        tables["cost_scale_review"].append(
            product_cost(run_id, "4 x 4 cm ceramic plate", "lab_batch")
        )
        tables["cost_scale_review"][-1]["reactor_capacity_or_throughput"] = (
            "4 x 4 cm ceramic plate collector"
        )
        append_evidence(
            tables,
            store,
            run_id,
            "CATALYST",
            "catalyst_system",
            f"{run_id}_CAT",
            "record_level",
            "SPAN_D7410DBBEE6D069E8BFA",
            "Ceramic-plate dimensions and tested precursor ratios.",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "PROCESS",
            "reactor_process_gas",
            f"{run_id}_S01",
            "record_level",
            "SPAN_D7410DBBEE6D069E8BFA",
            "Ceramic-plate ratio-test condition.",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "YIELD",
            "yield_quality",
            f"{run_id}_PROD",
            "record_level",
            "SPAN_D7410DBBEE6D069E8BFA",
            "The main article confirms a comparison but omits mapped outcomes.",
            "not_reported",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            "record_level",
            "SPAN_D7410DBBEE6D069E8BFA",
            "Laboratory 4 x 4 cm plate scale.",
            "review_assessment",
        )

    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_OVERLAP_001",
                SOURCE_ID,
                batch_id,
                "run_overlap_uncertainty",
                "source_run",
                batch_id,
                "run_summary",
                (
                    "SS_BATCH is the overall production event; AL_TUBE, AL_BOAT, "
                    "SS_SI and SS_CU are collector-specific co-products from "
                    "the same event and must not be summed as independent batches."
                ),
                f"EVD_{batch_id}_PROCESS_GROWTH",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_ATTRIBUTION_001",
                SOURCE_ID,
                batch_id,
                "definition_ambiguity",
                "yield_quality",
                f"{batch_id}_PROD",
                "yield_original",
                (
                    "The approximately 10 g product and approximately 60% "
                    "productivity are reported for the experiment overall, "
                    "without mass allocation among the four collectors."
                ),
                f"EVD_{batch_id}_YIELD",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PLATE_OUTCOME_001",
                SOURCE_ID,
                f"{SOURCE_ID}_PLATE20",
                "critical_data_gap",
                "yield_quality",
                f"{SOURCE_ID}_PLATE20_PROD",
                "yield_original",
                (
                    "The main article reports 20:1 and 15:2 ceramic-plate tests "
                    "but does not provide ratio-specific product values; the "
                    "relevant supplementary figures were unavailable locally."
                ),
                (f"EVD_{SOURCE_ID}_PLATE20_YIELD;EVD_{SOURCE_ID}_PLATE15_2_YIELD"),
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CONTACT_001",
                SOURCE_ID,
                tube_id,
                "figure_value_transcription",
                "yield_quality",
                f"{tube_id}_PROD",
                "application_property_summary",
                (
                    "Collector-specific contact angles 82, 149 and 154 degrees "
                    "were transcribed from Figure 9d and need independent review."
                ),
                (
                    f"EVD_{silicon_id}_CONTACT_ANGLE_PDF;"
                    f"EVD_{boat_id}_CONTACT_ANGLE_PDF;"
                    f"EVD_{tube_id}_CONTACT_ANGLE_PDF"
                ),
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_APPLICATION_ATTRIBUTION_001",
                SOURCE_ID,
                batch_id,
                "run_split_uncertainty",
                "yield_quality",
                f"{batch_id}_PROD",
                "application_property_summary",
                (
                    "Cr(VI) adsorption and BET results are reported for the "
                    "Fe/CNT material but are not mapped to a specific collector; "
                    "they are retained at overall-batch level."
                ),
                f"EVD_{batch_id}_APPLICATION;EVD_{batch_id}_BET",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_BASELINE_001",
                SOURCE_ID,
                baseline_id,
                "critical_data_gap",
                "reactor_process_gas",
                f"{baseline_id}_S01",
                "holding_time_min",
                (
                    "The external-heater Si baseline reports 850 C and product "
                    "morphology but not a complete run-level gas recipe, "
                    "precursor ratio or duration."
                ),
                (f"EVD_{baseline_id}_PROCESS;EVD_{baseline_id}_PROCESS_FAILURE"),
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_RAMAN_001",
                SOURCE_ID,
                tube_id,
                "definition_ambiguity",
                "yield_quality",
                f"{tube_id}_PROD",
                "Raman_ratio_value",
                (
                    "The reported D-band overlaps hematite features; the source "
                    "itself warns this can inflate apparent carbon disorder."
                ),
                f"EVD_{tube_id}_RAMAN",
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
