#!/usr/bin/env python3
"""Build the nineteenth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 19
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ID = "LIT_A4E38E9C51ED6D44"
PDF_REF = "data/raw/literature/pdf/LIT_A4E38E9C51ED6D44_60e6076ddec8.pdf"
SI_REF = (
        "data/raw/literature/supplements/LIT_A4E38E9C51ED6D44/"
    "1-s2.0-S0008622319306591-mmc1.pdf"
)
ATM_RECIPE_EVIDENCE_TEXT = (
    "Supplementary Table S1/procedure: reset at 875 C with 100 sccm air "
    "for 30 min. Pump down 15 min to 1 Torr and He-fill twice; heat from "
    "25 to 775 C in 10 min with 100 sccm He and 400 sccm H2. Carbon "
    "preload uses 100 sccm C2H4 for 3 min, then 0 sccm C2H4 for 7 min; "
    "reference uses 0 sccm C2H4. Total flow is 600 sccm during preload "
    "and 500 sccm otherwise. Anneal 10 min at 775 C with 100 sccm He "
    "and 400 sccm H2, total 500 sccm. Withdraw and cool 2 min; the "
    "carbon-source-off interval is 18 min including a 16 min switch using "
    "486 sccm He, 100 sccm H2 and 14 sccm wet He "
    "(about 370 ppm H2O), then add 100 sccm C2H4 for 7 min with "
    "386 sccm dry He plus 14 sccm wet He; total 600 sccm. Growth at "
    "775 C uses 100 sccm C2H4, 100 sccm H2 and 386 sccm dry plus "
    "14 sccm wet He for the first 3 min, then 400 sccm dry He; growth "
    "time varied from 1 to 40 min. Cool 5 min with 100 sccm C2H4, "
    "100 sccm H2 and 400 sccm He, total 600 sccm, then purge 5 min "
    "with 1000 sccm He; combined cooling/purge time 10 min."
)
LP_RECIPE_EVIDENCE_TEXT = (
    "Low-pressure SWCNT procedure: calcine in air at 400 C for 20 min; "
    "use the reference or carbon-preload concept at 775 C and about "
    "400 Torr during a 10 min anneal; carbon preload uses 100 sccm "
    "C2H4 for 3 min and reference uses 0. Growth is 5 min at 775 C and about "
    "100 Torr with 100 sccm C2H4, 800 sccm dry He and 200 sccm wet He "
    "containing 100 ppm H2O, total 1100 sccm."
)


def add_evidence(
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


def add_pdf_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    suffix: str,
    table: str,
    record_id: str,
    fields: str,
    span_id: str,
    page: str,
    text: str,
    summary: str,
    *,
    source_ref: str = PDF_REF,
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
            "source_object_ref": source_ref,
            "evidence_text": text,
            "evidence_summary": summary,
            "notes": "Transcribed after visual inspection of the locally stored PDF.",
        }
    )
    tables["evidence_index"].append(item)


def thin_film_catalyst(
    run_id: str,
    substrate: str = "thermally oxidized Si(100) wafer",
) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label="1 nm Fe / 10 nm Al2O3 supported thin film",
        active_metals="Fe",
        support_material=f"10 nm Al2O3 on {substrate}",
        promoter="trace carbon preload where applicable",
        metal_ratio_original="Al2O3 10 nm; Fe 1 nm",
        metal_ratio_standardized="not_applicable_thickness_stack",
        precursor_summary="sputtered Al2O3 followed by sputtered Fe",
        preparation_method="sequential_sputter_deposition",
        preparation_modifier="air-exposed Fe film; optional carbon-assisted dewetting",
        preparation_detail=(
            f"Al2O3 (10 nm) followed by Fe (1 nm) sputtered on {substrate}."
        ),
        drying_condition="not_applicable",
        calcination_condition="not_applicable unless low-pressure SWCNT run",
        reduction_condition="H2-containing anneal at growth-system temperature",
        activation_condition="dewetting into Fe nanoparticles",
        post_preparation_condition="used immediately after prescribed reactor sequence",
        catalyst_particle_size_mean_nm="not_reported",
        catalyst_particle_size_range_nm="not_reported",
        catalyst_particle_size_qualifier="annealed-particle distributions are separate controls",
        phase_or_state_summary=(
            "air-oxidized Fe film reduced/dewetted; carbon preload may promote "
            "metallic Fe and graphitic encapsulation"
        ),
        dispersion_summary="supported thin film becomes a nanoparticle population",
        deactivation_summary="density decay and self-termination during forest growth",
    )


def common_cost(run_id: str, scale_summary: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="lab_batch",
        scale_level_claimed="potential_scalable_high_density_forest_process",
        scale_evidence_summary=scale_summary,
        reactor_capacity_or_throughput="4 x 8 mm substrate for mass-density series",
        continuous_operation_time_h="not_applicable_batch_sequence",
        catalyst_lifetime_or_reuse="single growth; lifetime inferred from height-time curve",
        batch_stability="replicate/measurement errors shown for selected forest points",
        scale_up_issue=(
            "Maintain transient wall-derived carbon exposure, rapid substrate "
            "transfer, moisture control and uniform thin-film catalyst activation."
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="No material, energy or equipment cost is reported.",
        cost_driver_summary=(
            "sputtered Fe/Al2O3, high-purity gases, quartz hot-wall reactor, "
            "vacuum/purge cycles and rapid-transfer hardware"
        ),
        safety_risk=(
            "flammable H2/C2H4, hot quartz furnace, air oxidation at 875 C "
            "and vacuum-pressure transitions"
        ),
        emission_or_waste="hydrocarbon/VOC effluent and tube-wall carbon deposits",
        industrial_readiness_assessment=(
            "mechanistically supported laboratory process with improved density; "
            "wafer-scale uniformity and gas utilization not demonstrated here"
        ),
        reproduction_value="high because the supplementary recipe is explicit",
        reproduction_priority="high",
        recommended_next_action=(
            "Validate on larger substrates with online wall-carbon/VOC monitoring, "
            "replicated mass yield and carbon-conversion accounting."
        ),
    )


def add_run(
    tables: dict[str, list[dict[str, str]]],
    code: str,
    label: str,
    summary: str,
    confidence: str = "high",
    *,
    data_type: str = "experimental_run",
    target_track: str = "CNT_production",
) -> str:
    run_id = f"{SOURCE_ID}_{code}"
    tables["source_run"].append(run_row(SOURCE_ID, code, label, summary, confidence))
    tables["source_run"][-1].update(
        {"data_type": data_type, "target_track": target_track}
    )
    return run_id


def atmospheric_stages(run_id: str, preload: bool) -> list[dict[str, str]]:
    preload_text = (
        "100 sccm C2H4 added for 3 min, then shut off for 7 min"
        if preload
        else "no C2H4 during the corresponding 10 min reference preparation"
    )
    return [
        process_row(
            run_id,
            1,
            "reactor_reset",
            reactor_type="1 inch hot-wall quartz-tube CVD",
            scale_level="lab_batch",
            reactor_material="quartz tube",
            reactor_size_summary="1 inch diameter; single-zone furnace",
            reactor_setup_summary="tube oxidized before each run to reset aging",
            temperature_setpoint_C="875",
            temperature_program_summary="heat tube at 875 C in air",
            holding_time_min="30",
            pressure_original="atmospheric",
            pressure_kPa="101.325",
            carbon_source="residual wall carbon removed",
            reducing_gas="not_applicable",
            inert_gas="not_applicable",
            cofeed_or_reactive_gas="air",
            cofeed_flow_original="100 sccm",
            total_flow_original="100 sccm",
            gas_composition_summary="air oxidation reset",
            process_note="Performed before each atmospheric run.",
        ),
        process_row(
            run_id,
            2,
            "pump_fill_heat_and_preload",
            reactor_type="rapid-transfer hot-wall quartz-tube CVD",
            scale_level="lab_batch",
            reactor_material="quartz tube",
            reactor_size_summary="1 inch diameter",
            reactor_setup_summary="sample outside hot zone on quartz boat",
            temperature_setpoint_C="775",
            temperature_program_summary=(
                "pump to 1 Torr and He-fill twice; heat from 25 to 775 C "
                f"in 10 min; {preload_text}"
            ),
            holding_time_min="10 min heat plus 3 min preload window plus 7 min preparation",
            pressure_original="atmospheric after pump/fill conditioning",
            pressure_kPa="101.325",
            carbon_source="C2H4" if preload else "not_applicable_before_growth",
            carbon_source_flow_original="100 sccm for 3 min" if preload else "0 sccm",
            reducing_gas="H2",
            reducing_gas_flow_original="400 sccm",
            inert_gas="He",
            inert_gas_flow_original="100 sccm",
            cofeed_or_reactive_gas="not_applicable",
            total_flow_original=(
                "600 sccm during 3 min preload; 500 sccm otherwise"
                if preload
                else "500 sccm"
            ),
            gas_composition_summary=(
                "He/H2/C2H4 carbon preload followed by He/H2"
                if preload
                else "He/H2 reference preparation"
            ),
            process_note="Carbon preload conditions the empty hot zone/tube wall.",
        ),
        process_row(
            run_id,
            3,
            "catalyst_anneal_dewetting",
            reactor_type="rapid-transfer hot-wall quartz-tube CVD",
            scale_level="lab_batch",
            reactor_material="quartz tube",
            reactor_size_summary="sample 7 cm downstream from furnace center",
            reactor_setup_summary="sample moved into reaction zone",
            temperature_setpoint_C="775",
            temperature_program_summary="anneal/dewet Fe film at 775 C",
            holding_time_min="10",
            pressure_original="atmospheric",
            pressure_kPa="101.325",
            carbon_source="wall-derived trace species" if preload else "not_applicable",
            reducing_gas="H2",
            reducing_gas_flow_original="400 sccm",
            inert_gas="He",
            inert_gas_flow_original="100 sccm",
            cofeed_or_reactive_gas="not_applicable",
            total_flow_original="500 sccm",
            gas_composition_summary="H2/He; no supplied C2H4",
            process_note="Expected catalyst reduction and nanoparticle formation.",
        ),
        process_row(
            run_id,
            4,
            "growth_atmosphere_preparation",
            reactor_type="rapid-transfer hot-wall quartz-tube CVD",
            scale_level="lab_batch",
            reactor_material="quartz tube",
            reactor_size_summary="sample withdrawn during gas switching",
            reactor_setup_summary="2 min cooling then establish wet growth gas",
            temperature_setpoint_C="775",
            temperature_program_summary="hot zone remains at 775 C",
            holding_time_min="2 min cooling plus 16 min switch plus 7 min C2H4 establishment",
            pressure_original="atmospheric",
            pressure_kPa="101.325",
            carbon_source="C2H4",
            carbon_source_flow_original="0 sccm for 18 min then 100 sccm for 7 min",
            reducing_gas="H2",
            reducing_gas_flow_original="400 sccm for 2 min then 100 sccm",
            inert_gas="He",
            inert_gas_flow_original=(
                "100 sccm for 2 min; 486 sccm for 16 min; "
                "386 sccm dry plus 14 sccm wet He for 7 min"
            ),
            cofeed_or_reactive_gas="H2O in He",
            cofeed_flow_original="14 sccm wet He, approximately 370 ppm H2O",
            total_flow_original="600 sccm after growth mixture is established",
            gas_composition_summary="C2H4/H2/He with controlled moisture",
            process_note="The sample remains outside the hot zone during switching.",
        ),
        process_row(
            run_id,
            5,
            "CNT_forest_growth_time_series",
            reactor_type="rapid-transfer hot-wall quartz-tube CVD",
            scale_level="lab_batch",
            reactor_material="quartz tube",
            reactor_size_summary="4 x 8 mm catalyst substrate for density series",
            reactor_setup_summary="sample returned to reaction zone",
            temperature_setpoint_C="775",
            temperature_program_summary="isothermal CNT forest growth",
            holding_time_min="varied from 1 to 40 min across the series",
            pressure_original="atmospheric",
            pressure_kPa="101.325",
            carbon_source="C2H4",
            carbon_source_flow_original="100 sccm",
            reducing_gas="H2",
            reducing_gas_flow_original="100 sccm",
            inert_gas="He",
            inert_gas_flow_original=(
                "386 sccm dry plus 14 sccm wet He for first 3 min; "
                "400 sccm dry He thereafter"
            ),
            cofeed_or_reactive_gas="H2O for first 3 min",
            cofeed_flow_original="approximately 370 ppm H2O for first 3 min",
            total_flow_original="600 sccm",
            gas_composition_summary="C2H4/H2/He; transient water cofeed",
            process_note="Growth duration was the principal time-series variable.",
        ),
        process_row(
            run_id,
            6,
            "rapid_cooling_and_purge",
            reactor_type="rapid-transfer hot-wall quartz-tube CVD",
            scale_level="lab_batch",
            reactor_material="quartz tube",
            reactor_size_summary="not_applicable",
            reactor_setup_summary="furnace opened and sample withdrawn",
            temperature_program_summary="rapid cool; unseal below 100 C",
            holding_time_min="10",
            pressure_original="atmospheric",
            pressure_kPa="101.325",
            carbon_source="C2H4 during first 5 min cooling",
            carbon_source_flow_original="100 sccm for 5 min then 0",
            reducing_gas="H2",
            reducing_gas_flow_original="100 sccm for 5 min then 0",
            inert_gas="He",
            inert_gas_flow_original="400 sccm for 5 min then 1000 sccm",
            cofeed_or_reactive_gas="not_applicable",
            total_flow_original="600 sccm then 1000 sccm",
            gas_composition_summary="growth gas during fast cooling, then He purge",
            process_note="C2H4 during cooling improves forest adhesion.",
        ),
    ]


def build(
    metadata: dict[str, Any],
    store: EvidenceStore,
) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "Atmospheric reference/preload growth-time series; annealed "
                "catalyst controls; ETEM validation; preload-duration and "
                "sequence controls; low-pressure SWCNT reference/preload."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_main_and_supplementary_pdf"
    master["notes"] += (
        f" Supplementary recipe stored at {SI_REF}. Main plotted series are "
        "represented as experimental-series records rather than falsely "
        "assigning every figure marker an exact independent-run value."
    )

    ref_id = add_run(
        tables,
        "AP_REF_TS",
        "atmospheric reference forest growth-time series",
        (
            "Fe/Al2O3 few-wall CNT forests grown without supplied carbon "
            "during catalyst preparation; height stalls near 1 mm and density "
            "is lower than the carbon-preload series."
        ),
        data_type="experimental_series",
    )
    preload_id = add_run(
        tables,
        "AP_PRELOAD_TS",
        "atmospheric 3 min carbon-preload growth-time series",
        (
            "A 3 min C2H4 tube-conditioning step before Fe dewetting yields "
            "higher-density few-wall CNT forests and extends growth lifetime."
        ),
        data_type="experimental_series",
    )
    for run_id, preload in [(ref_id, False), (preload_id, True)]:
        tables["catalyst_system"].append(thin_film_catalyst(run_id))
        tables["reactor_process_gas"].extend(atmospheric_stages(run_id, preload))
        tables["cost_scale_review"].append(
            common_cost(
                run_id,
                "Atmospheric 1 inch hot-wall CVD on 4 x 8 mm substrates.",
            )
        )

    tables["yield_quality"].append(
        yield_row(
            ref_id,
            primary_yield_metric="forest_height_and_bulk_mass_density_time_series",
            yield_original="3 min bulk mass density 17 ± 10 microgram/mm3",
            yield_definition_original="forest mass divided by substrate area and SEM height",
            yield_calculation_method="mass balance / (4 x 8 mm substrate area x forest height)",
            yield_value_standardized="",
            yield_unit_standardized="microgram_per_mm3",
            secondary_result_summary=(
                "Height is approximately linear through 10 min then stalls "
                "near 1 mm; 10 min density 13 ± 3 microgram/mm3. "
                "SAXS local-mass fits: 5 min, rho=13 exp(-0.0016z); "
                "20 min, rho=8.3 exp(-0.0013z), with z in micrometers."
            ),
            CNT_type_reported="few-walled CNT forest",
            CNT_type_confirmed="vertically aligned few-wall CNTs by SEM/TEM/SAXS",
            product_mixture_summary="CNT forest with amorphous carbon fraction",
            CNT_type_evidence="SEM/TEM forest morphology and SAXS wall model",
            outer_diameter_range_nm="approximately 4.8-5.25",
            wall_number_summary=(
                "5 min approximately 2.45-2.65 walls; "
                "20 min approximately 2.8-3.1 walls"
            ),
            length_summary="forest height saturates near 1000 micrometers",
            morphology="vertically aligned CNT forest",
            alignment_or_array="dense vertical forest",
            TGA_carbon_content_wt_percent="74.2",
            purified_product_purity_wt_percent="74.2",
            purity_basis="TGA CNT fraction for 20 min forest",
            residue_summary="22.3 wt.% amorphous carbon by TGA",
            amorphous_carbon_level="22.3 wt.% for 20 min sample",
            characterization_methods="mass balance; SEM; TEM; TGA; SAXS",
            post_treatment_or_purification="none",
            purification_condition="not_applicable",
            application_property_summary=(
                "SAXS 5 min peak CNT number density 3.6 x 10^9 CNT/cm2; "
                "inner/outer diameter ratio fixed near 0.65 for 5 min and "
                "0.60 for 20 min fits."
            ),
        )
    )
    tables["yield_quality"].append(
        yield_row(
            preload_id,
            primary_yield_metric="forest_height_and_bulk_mass_density_time_series",
            yield_original="3 min bulk mass density 70 ± 12 microgram/mm3",
            yield_definition_original="forest mass divided by substrate area and SEM height",
            yield_calculation_method="mass balance / (4 x 8 mm substrate area x forest height)",
            yield_value_standardized="",
            yield_unit_standardized="microgram_per_mm3",
            secondary_result_summary=(
                "Height remains approximately linear through 10 min and "
                "saturates near 2.3 mm after about 25 min; 10 min density "
                "35 ± 3 microgram/mm3. SAXS 5 min local-mass fit: "
                "rho=160 exp(-0.0024z), z in micrometers."
            ),
            CNT_type_reported="few-walled CNT forest",
            CNT_type_confirmed="vertically aligned few-wall CNTs by SEM/TEM/SAXS",
            product_mixture_summary="higher-density CNT forest with amorphous carbon fraction",
            CNT_type_evidence="SEM/TEM forest morphology and SAXS wall model",
            outer_diameter_range_nm="approximately 5.9-6.3",
            wall_number_summary="approximately 4.1-4.4 walls for 5 min forest",
            length_summary="forest height saturates near 2300 micrometers",
            morphology="high-density vertically aligned CNT forest",
            alignment_or_array="dense vertical forest",
            TGA_carbon_content_wt_percent="78",
            purified_product_purity_wt_percent="78",
            purity_basis="TGA CNT fraction for 20 min forest",
            residue_summary="20.3 wt.% amorphous carbon by TGA",
            amorphous_carbon_level="20.3 wt.% for 20 min sample",
            characterization_methods="mass balance; SEM; TEM; TGA; SAXS",
            post_treatment_or_purification="none",
            purification_condition="not_applicable",
            application_property_summary=(
                "SAXS 5 min peak CNT number density 2.9 x 10^10 CNT/cm2; "
                "inner/outer diameter ratio fixed near 0.525. Peak local "
                "mass density is more than 10-fold above the comparison."
            ),
        )
    )

    anneal_ids: list[tuple[str, bool]] = []
    for code, preload, label in [
        ("ANNEAL_REF", False, "reference annealed catalyst control"),
        ("ANNEAL_PRELOAD", True, "carbon-preload annealed catalyst control"),
    ]:
        run_id = add_run(
            tables,
            code,
            label,
            "Catalyst was withdrawn after annealing/dewetting and before intended CNT growth.",
            data_type="experimental_control",
            target_track="catalyst_development",
        )
        anneal_ids.append((run_id, preload))
        catalyst = thin_film_catalyst(run_id)
        catalyst.update(
            {
                "catalyst_particle_size_range_nm": "not_reported",
                "dispersion_summary": (
                    "AFM particle density 3.6 x 10^11 cm-2; TEM density "
                    "2.63 x 10^11 cm-2; smaller-diameter-biased distribution"
                    if preload
                    else "AFM particle density 3.0 x 10^11 cm-2; TEM density "
                    "1.16 x 10^11 cm-2; less completely defined particles"
                ),
                "phase_or_state_summary": (
                    "graphitic carbon remains after Ar cleaning; graphitic "
                    "layers and occasional short CNTs on particles"
                    if preload
                    else "weak residual carbon signal; incomplete reduction/dewetting"
                ),
            }
        )
        tables["catalyst_system"].append(catalyst)
        stages = atmospheric_stages(run_id, preload)[:3]
        tables["reactor_process_gas"].extend(stages)
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="annealed_catalyst_morphology_control",
                yield_original="not_applicable_no_intended_growth",
                yield_definition_original="not_applicable",
                yield_calculation_method="not_applicable",
                yield_value_standardized="",
                yield_unit_standardized="not_applicable",
                secondary_result_summary=(
                    "Carbon preload increased catalyst-particle density and "
                    "biased the TEM histogram toward smaller diameters."
                ),
                CNT_type_reported=(
                    "occasional very short CNTs on preload catalyst"
                    if preload
                    else "not_applicable"
                ),
                CNT_type_confirmed="not_applicable_catalyst_control",
                product_mixture_summary="annealed catalyst substrate",
                CNT_type_evidence="TEM catalyst characterization",
                morphology="Fe nanoparticle population after annealing",
                alignment_or_array="not_applicable",
                characterization_methods="AFM; TEM; Raman; XPS",
                post_treatment_or_purification="not_applicable",
                purification_condition="not_applicable",
            )
        )
        tables["cost_scale_review"].append(
            common_cost(run_id, "Annealing-only catalyst-control substrate.")
        )

    etem_ids: list[tuple[str, bool]] = []
    for code, preload, outcome in [
        ("ETEM_REF", False, "very few CNTs nucleated"),
        ("ETEM_PRELOAD", True, "high-density CNT growth"),
    ]:
        run_id = add_run(
            tables,
            code,
            "ETEM carbon-preload validation"
            if preload
            else "ETEM reference validation",
            (f"Low-pressure in-situ ETEM growth on Fe/Al2O3/Si3N4: {outcome}."),
            data_type="experimental_control",
        )
        etem_ids.append((run_id, preload))
        tables["catalyst_system"].append(
            thin_film_catalyst(run_id, "10 nm Si3N4 TEM window")
        )
        tables["reactor_process_gas"].extend(
            [
                process_row(
                    run_id,
                    1,
                    "ETEM_cleaning",
                    reactor_type="FEI Titan 80-300 ETEM",
                    scale_level="in_situ_microscopy",
                    reactor_material="ETEM chamber and heating holder",
                    reactor_size_summary="TEM-grid experiment",
                    reactor_setup_summary="chamber and holder plasma cleaned",
                    temperature_program_summary="room-temperature O2 plasma cleaning",
                    holding_time_min="40",
                    pressure_original="not_reported",
                    pressure_kPa="",
                    carbon_source="not_applicable",
                    reducing_gas="not_applicable",
                    inert_gas="not_applicable",
                    cofeed_or_reactive_gas="O2 plasma",
                    total_flow_original="not_reported",
                    gas_composition_summary="30 min chamber plus 10 min holder cleaning",
                    process_note="Cleaning precedes each ETEM experiment.",
                ),
                process_row(
                    run_id,
                    2,
                    "ETEM_heat_and_anneal",
                    reactor_type="FEI Titan 80-300 ETEM",
                    scale_level="in_situ_microscopy",
                    reactor_material="ETEM chamber",
                    reactor_size_summary="TEM-grid experiment",
                    reactor_setup_summary="Fe/Al2O3-coated Si3N4 grid",
                    temperature_setpoint_C="650",
                    temperature_program_summary="heat to 650 C and anneal",
                    holding_time_min="15",
                    pressure_original=(
                        "40 mTorr H2 plus 0.4 mTorr C2H2" if preload else "40 mTorr H2"
                    ),
                    pressure_kPa="",
                    carbon_source="C2H2" if preload else "not_applicable",
                    carbon_source_flow_original=(
                        "0.4 mTorr partial pressure" if preload else "0"
                    ),
                    reducing_gas="H2",
                    reducing_gas_flow_original="40 mTorr partial pressure",
                    inert_gas="not_applicable",
                    cofeed_or_reactive_gas="not_applicable",
                    total_flow_original="pressure-controlled, flow not reported",
                    gas_composition_summary=(
                        "trace C2H2/H2 preload" if preload else "H2 reference"
                    ),
                    process_note="Trace C2H2 is present before growth only in preload case.",
                ),
                process_row(
                    run_id,
                    3,
                    "ETEM_CNT_growth",
                    reactor_type="FEI Titan 80-300 ETEM",
                    scale_level="in_situ_microscopy",
                    reactor_material="ETEM chamber",
                    reactor_size_summary="TEM-grid experiment",
                    reactor_setup_summary="same field after catalyst annealing",
                    temperature_setpoint_C="650",
                    temperature_program_summary="isothermal growth",
                    holding_time_min="not_reported",
                    pressure_original="10 mTorr C2H2 added to H2",
                    pressure_kPa="",
                    carbon_source="C2H2",
                    carbon_source_flow_original="10 mTorr partial pressure",
                    reducing_gas="H2",
                    reducing_gas_flow_original="40 mTorr partial pressure",
                    inert_gas="not_applicable",
                    cofeed_or_reactive_gas="not_applicable",
                    total_flow_original="50 mTorr nominal combined pressure",
                    gas_composition_summary="C2H2/H2",
                    process_note="Growth time is not stated.",
                ),
            ]
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="qualitative_CNT_nucleation_density",
                yield_original=outcome,
                yield_definition_original="ETEM image comparison",
                yield_calculation_method="qualitative",
                yield_value_standardized="",
                yield_unit_standardized="qualitative",
                secondary_result_summary=outcome,
                CNT_type_reported="CNTs",
                CNT_type_confirmed="CNTs observed in ETEM",
                product_mixture_summary="CNTs and catalyst particles on TEM grid",
                CNT_type_evidence="in-situ ETEM",
                morphology="high-density network" if preload else "very sparse CNTs",
                alignment_or_array="not_applicable_TEM_grid",
                characterization_methods="ETEM",
                post_treatment_or_purification="none",
                purification_condition="not_applicable",
            )
        )
        tables["cost_scale_review"].append(
            common_cost(run_id, "In-situ TEM-grid validation; not a production scale.")
        )

    duration_id = add_run(
        tables,
        "PRELOAD_DURATION",
        "carbon-preload duration series at 10 min CNT growth",
        (
            "Tube C2H4 exposure was varied from no preload to 1800 s; density "
            "increased by 18 s and did not improve further, while height was similar."
        ),
        data_type="experimental_series",
    )
    tables["catalyst_system"].append(thin_film_catalyst(duration_id))
    tables["reactor_process_gas"].extend(atmospheric_stages(duration_id, True))
    tables["reactor_process_gas"][len(tables["reactor_process_gas"]) - 5][
        "holding_time_min"
    ] = "preload duration varied: 0, 5, 18, 180 and 1800 s"
    tables["yield_quality"].append(
        yield_row(
            duration_id,
            primary_yield_metric="preload_duration_vs_forest_density",
            yield_original=(
                "10 min volumetric density approximately 17, 14, 34, 37 and "
                "34 microgram/mm3 at 0, 5, 18, 180 and 1800 s preload"
            ),
            yield_definition_original="Figure 6 graph-digitized volumetric density",
            yield_calculation_method="manual visual transcription from Figure 6",
            yield_value_standardized="",
            yield_unit_standardized="microgram_per_mm3",
            secondary_result_summary=(
                "Forest heights are approximately 1200, 1000, 1100, 1000 "
                "and 950 micrometers for the same preload-time sequence."
            ),
            CNT_type_reported="few-walled CNT forest",
            CNT_type_confirmed="vertically aligned CNT forest",
            product_mixture_summary="CNT forest",
            CNT_type_evidence="Figure 6 forest height/density comparison",
            length_summary="approximately 950-1200 micrometer forest height",
            morphology="vertically aligned forest",
            alignment_or_array="vertical forest",
            characterization_methods="mass balance; SEM",
            post_treatment_or_purification="none",
            purification_condition="not_applicable",
        )
    )
    tables["cost_scale_review"].append(
        common_cost(duration_id, "Five-condition preload-duration laboratory series.")
    )

    modified_ids: list[tuple[str, str]] = []
    modified_configs = [
        (
            "MODIFIED_1",
            "tube preloaded empty, cooled/purged/reheated, then reference growth",
            "preload density enhancement nullified; low-density curve",
        ),
        (
            "MODIFIED_2",
            "system pumped and purged between preload and catalyst anneal",
            "low-density curve; catalyst outside hot zone did not retain benefit",
        ),
        (
            "MODIFIED_3",
            "catalyst annealed under preload, then cooled/exposed before growth",
            "high-density curve retained; annealing exposure caused lasting change",
        ),
    ]
    for code, sequence, outcome in modified_configs:
        run_id = add_run(
            tables,
            code,
            code.replace("_", " ").lower(),
            f"{sequence}; {outcome}.",
            "medium",
            data_type="experimental_control",
        )
        modified_ids.append((run_id, outcome))
        tables["catalyst_system"].append(thin_film_catalyst(run_id))
        tables["reactor_process_gas"].append(
            process_row(
                run_id,
                1,
                "modified_carbon_preload_sequence",
                reactor_type="rapid-transfer hot-wall quartz-tube CVD",
                scale_level="lab_batch",
                reactor_material="quartz tube",
                reactor_size_summary="1 inch diameter",
                reactor_setup_summary=sequence,
                temperature_setpoint_C="775",
                temperature_program_summary="modified ordering around 3 min preload/anneal",
                holding_time_min="growth duration not explicitly restated",
                pressure_original="atmospheric",
                pressure_kPa="101.325",
                carbon_source="C2H4",
                carbon_source_flow_original="100 sccm during 3 min preload and growth",
                reducing_gas="H2",
                reducing_gas_flow_original="recipe-based; 400 sccm during anneal",
                inert_gas="He",
                inert_gas_flow_original="recipe-based",
                cofeed_or_reactive_gas="H2O during initial growth",
                total_flow_original="recipe-based",
                gas_composition_summary="standard recipe gases with sequence interruption",
                process_note=sequence,
            )
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="local_mass_density_profile_control",
                yield_original=outcome,
                yield_definition_original="Figure 7 SAXS local-density curve",
                yield_calculation_method="qualitative/graphical comparison",
                yield_value_standardized="",
                yield_unit_standardized="qualitative",
                secondary_result_summary=(
                    "Figure 7 preserves the full density-vs-height profile; "
                    "individual plotted points are not asserted as exact values."
                ),
                CNT_type_reported="CNT forest",
                CNT_type_confirmed="vertically aligned CNT forest",
                product_mixture_summary="CNT forest",
                CNT_type_evidence="SAXS local density profile",
                morphology="vertically aligned forest",
                alignment_or_array="vertical forest",
                characterization_methods="SAXS",
                post_treatment_or_purification="none",
                purification_condition="not_applicable",
            )
        )
        tables["cost_scale_review"].append(
            common_cost(run_id, "Modified sequence mechanism-control experiment.")
        )

    lp_ids: list[tuple[str, bool]] = []
    for code, preload, height, ratio in [
        ("LP_SWCNT_REF", False, "26.1", "4.5"),
        ("LP_SWCNT_PRELOAD", True, "80.2", "8.6"),
    ]:
        run_id = add_run(
            tables,
            code,
            "low-pressure SWCNT carbon-preload"
            if preload
            else "low-pressure SWCNT reference",
            (
                f"Five-minute low-pressure SWCNT forest: height {height} "
                f"micrometers and middle-sidewall G/D ratio {ratio}."
            ),
        )
        lp_ids.append((run_id, preload))
        catalyst = thin_film_catalyst(run_id)
        catalyst["calcination_condition"] = "air at 400 C for 20 min"
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].extend(
            [
                process_row(
                    run_id,
                    1,
                    "catalyst_calcination",
                    reactor_type="low-pressure hot-wall CVD system",
                    scale_level="lab_batch",
                    reactor_material="not_reported",
                    reactor_size_summary="separate low-pressure system",
                    reactor_setup_summary="Fe/Al2O3-coated Si substrate",
                    temperature_setpoint_C="400",
                    temperature_program_summary="calcine catalyst substrate in air",
                    holding_time_min="20",
                    pressure_original="air; pressure not reported",
                    pressure_kPa="",
                    carbon_source="not_applicable",
                    reducing_gas="not_applicable",
                    inert_gas="not_applicable",
                    cofeed_or_reactive_gas="air",
                    total_flow_original="not_reported",
                    gas_composition_summary="air calcination",
                    process_note="Additional step unique to low-pressure SWCNT synthesis.",
                ),
                process_row(
                    run_id,
                    2,
                    "low_pressure_anneal_and_optional_preload",
                    reactor_type="low-pressure hot-wall CVD",
                    scale_level="lab_batch",
                    reactor_material="not_reported",
                    reactor_size_summary="separate low-pressure system",
                    reactor_setup_summary="reference/preload recipe with pressure modification",
                    temperature_setpoint_C="775",
                    temperature_program_summary=(
                        "same reference/preload concept; exact low-pressure "
                        "preload timing otherwise follows main recipe"
                    ),
                    holding_time_min="10",
                    pressure_original="approximately 400 Torr during annealing",
                    pressure_kPa="",
                    carbon_source="trace C2H4 preload" if preload else "not_applicable",
                    carbon_source_flow_original=(
                        "100 sccm during preload" if preload else "0 during preload"
                    ),
                    reducing_gas="H2",
                    reducing_gas_flow_original="recipe-based; exact low-pressure flow not restated",
                    inert_gas="He",
                    inert_gas_flow_original="recipe-based",
                    cofeed_or_reactive_gas="not_applicable",
                    total_flow_original="not_reported for anneal",
                    gas_composition_summary=(
                        "carbon-preload anneal" if preload else "reference anneal"
                    ),
                    process_note="Annealing pressure is approximately 400 Torr.",
                ),
                process_row(
                    run_id,
                    3,
                    "low_pressure_SWCNT_growth",
                    reactor_type="low-pressure hot-wall CVD",
                    scale_level="lab_batch",
                    reactor_material="not_reported",
                    reactor_size_summary="separate low-pressure system",
                    reactor_setup_summary="SWCNT forest growth",
                    temperature_setpoint_C="775",
                    temperature_program_summary="isothermal low-pressure growth",
                    holding_time_min="5",
                    pressure_original="approximately 100 Torr",
                    pressure_kPa="",
                    carbon_source="C2H4",
                    carbon_source_flow_original="100 sccm",
                    reducing_gas="not_reported in stated growth mixture",
                    inert_gas="He",
                    inert_gas_flow_original="800 sccm dry plus 200 sccm wet He",
                    cofeed_or_reactive_gas="H2O",
                    cofeed_flow_original="200 sccm wet He containing 100 ppm H2O",
                    total_flow_original="1100 sccm",
                    gas_composition_summary="C2H4/He/wet He",
                    process_note="Lower C2H4 partial pressure supports SWCNT growth.",
                ),
            ]
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="SWCNT_forest_height",
                yield_original=f"{height} micrometer forest height at 5 min",
                yield_definition_original="SEM forest height",
                yield_calculation_method="direct SEM measurement",
                yield_value_standardized="",
                yield_unit_standardized="micrometer_forest_height",
                secondary_result_summary=(
                    "Carbon preload increases height and improves Raman crystallinity."
                ),
                CNT_type_reported="forest containing single-walled CNTs",
                CNT_type_confirmed="SWCNTs by RBM Raman features and TEM",
                product_mixture_summary="SWCNT-containing forest",
                CNT_type_evidence="RBM peaks and exemplary TEM",
                SWCNT_or_few_wall_evidence_summary=(
                    "RBM peaks; preload shifts prominence toward higher frequencies"
                ),
                RBM_peak_reported="yes",
                length_summary=f"{height} micrometer forest height",
                morphology="vertically aligned SWCNT-containing forest",
                alignment_or_array="vertical forest",
                Raman_ratio_type="G/D",
                Raman_ratio_value=ratio,
                Raman_laser_wavelength_nm="532",
                characterization_methods="SEM; TEM; Raman",
                post_treatment_or_purification="none",
                purification_condition="not_applicable",
            )
        )
        tables["cost_scale_review"].append(
            common_cost(run_id, "Separate low-pressure SWCNT hot-wall CVD experiment.")
        )

    all_runs = [
        ref_id,
        preload_id,
        *(item[0] for item in anneal_ids),
        *(item[0] for item in etem_ids),
        duration_id,
        *(item[0] for item in modified_ids),
        *(item[0] for item in lp_ids),
    ]
    for run_id in all_runs:
        add_evidence(
            tables,
            store,
            run_id,
            "CATALYST",
            "catalyst_system",
            f"{run_id}_CAT",
            "record_level",
            "SPAN_39910C58537EE9FA3455",
            "Common sputtered 10 nm Al2O3 / 1 nm Fe catalyst stack.",
        )
        add_evidence(
            tables,
            store,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            "record_level",
            "SPAN_0A4EDEF496BD03DAA15E",
            "Laboratory high-density forest process and scalability motivation.",
            value_status="review_assessment",
        )

    for run_id, preload in [(ref_id, False), (preload_id, True)]:
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "RECIPE",
            "reactor_process_gas",
            f"{run_id}_S01",
            "record_level",
            "SPAN_39910C58537EE9FA3455",
            "SI pages 2-4",
            ATM_RECIPE_EVIDENCE_TEXT,
            "Complete atmospheric recipe sequence.",
            source_ref=SI_REF,
        )
        for stage in range(2, 7):
            add_pdf_evidence(
                tables,
                store,
                run_id,
                f"STAGE_{stage}",
                "reactor_process_gas",
                f"{run_id}_S{stage:02d}",
                "record_level",
                "SPAN_39910C58537EE9FA3455",
                "SI pages 2-4",
                ATM_RECIPE_EVIDENCE_TEXT,
                f"Supplementary recipe support for process stage {stage}.",
                source_ref=SI_REF,
            )

    add_evidence(
        tables,
        store,
        ref_id,
        "RESULT",
        "yield_quality",
        f"{ref_id}_PROD",
        (
            "yield_original;TGA_carbon_content_wt_percent;"
            "purified_product_purity_wt_percent"
        ),
        "SPAN_1D93ACC01488E990CCE1",
        "Reference 3 min density and Figure 2 series context.",
    )
    add_pdf_evidence(
        tables,
        store,
        ref_id,
        "SAXS_SHAPE",
        "yield_quality",
        f"{ref_id}_PROD",
        "outer_diameter_range_nm;wall_number_summary;application_property_summary",
        "SPAN_AE4226C8E93232379DC1",
        "SI page 9",
        (
            "Figure S2: reference 5 min outer diameter about 4.8-5.15 nm, "
            "2.45-2.65 walls, c=0.65; reference 20 min diameter about "
            "4.8-5.25 nm, 2.8-3.1 walls, c=0.60."
        ),
        "Reference SAXS diameter/wall ranges.",
        source_ref=SI_REF,
        value_status="figure_digitized_approximate",
        confidence="medium",
    )
    add_pdf_evidence(
        tables,
        store,
        ref_id,
        "TGA",
        "yield_quality",
        f"{ref_id}_PROD",
        "TGA_carbon_content_wt_percent;purified_product_purity_wt_percent",
        "SPAN_1B59631BB2EF7FB41846",
        "SI page 8",
        "Reference 20 min forest: 74.2% CNT and 22.3% amorphous carbon.",
        "Reference TGA composition.",
        source_ref=SI_REF,
    )
    add_evidence(
        tables,
        store,
        preload_id,
        "RESULT",
        "yield_quality",
        f"{preload_id}_PROD",
        (
            "yield_original;TGA_carbon_content_wt_percent;"
            "purified_product_purity_wt_percent"
        ),
        "SPAN_1B59631BB2EF7FB41846",
        "Preload density and TGA composition.",
    )
    add_pdf_evidence(
        tables,
        store,
        preload_id,
        "DENSITY_3MIN",
        "yield_quality",
        f"{preload_id}_PROD",
        "yield_original",
        "SPAN_1D93ACC01488E990CCE1",
        "main PDF page 6",
        (
            "At 3 min growth, carbon-preload bulk mass density is "
            "70 ± 12 microgram/mm3; reference is 17 ± 10 microgram/mm3."
        ),
        "Explicit three-minute bulk-density comparison.",
    )
    add_pdf_evidence(
        tables,
        store,
        preload_id,
        "SAXS_SHAPE",
        "yield_quality",
        f"{preload_id}_PROD",
        "outer_diameter_range_nm;wall_number_summary;application_property_summary",
        "SPAN_AE4226C8E93232379DC1",
        "SI page 9",
        (
            "Figure S2: carbon-preload 5 min outer diameter about 5.9-6.3 nm, "
            "4.1-4.4 walls and fixed inner/outer diameter ratio c=0.525."
        ),
        "Preload SAXS diameter/wall ranges.",
        source_ref=SI_REF,
        value_status="figure_digitized_approximate",
        confidence="medium",
    )

    for run_id, preload in anneal_ids:
        for stage in [1, 2]:
            add_pdf_evidence(
                tables,
                store,
                run_id,
                f"PROCESS_{stage}",
                "reactor_process_gas",
                f"{run_id}_S{stage:02d}",
                "record_level",
                "SPAN_66BE27A0D8209CCB5851" if preload else "SPAN_39910C58537EE9FA3455",
                "SI pages 2-4",
                ATM_RECIPE_EVIDENCE_TEXT,
                "Pre-anneal control sequence.",
                source_ref=SI_REF,
            )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "PROCESS",
            "reactor_process_gas",
            f"{run_id}_S03",
            "record_level",
            "SPAN_66BE27A0D8209CCB5851" if preload else "SPAN_39910C58537EE9FA3455",
            "SI pages 2-4",
            ATM_RECIPE_EVIDENCE_TEXT,
            "Annealing/dewetting control condition.",
            source_ref=SI_REF,
        )
        add_evidence(
            tables,
            store,
            run_id,
            "CAT_RESULT",
            "catalyst_system",
            f"{run_id}_CAT",
            "catalyst_particle_size_range_nm;dispersion_summary;phase_or_state_summary",
            "SPAN_5606D7A5ED10D62C50D5" if preload else "SPAN_B103F6C9384417C9FB45",
            "AFM/TEM particle densities and catalyst morphology.",
        )
        add_evidence(
            tables,
            store,
            run_id,
            "PRODUCT",
            "yield_quality",
            f"{run_id}_PROD",
            "record_level",
            "SPAN_91AA56894D5EEA5465F5",
            "Annealed catalyst was a pre-growth morphology control.",
        )

    for run_id, preload in etem_ids:
        for stage in range(1, 4):
            add_evidence(
                tables,
                store,
                run_id,
                f"PROCESS_{stage}",
                "reactor_process_gas",
                f"{run_id}_S{stage:02d}",
                "record_level",
                "SPAN_093E04444FEB8344F235",
                "ETEM cleaning, annealing and C2H2 growth conditions.",
            )
        add_evidence(
            tables,
            store,
            run_id,
            "PRODUCT",
            "yield_quality",
            f"{run_id}_PROD",
            "record_level",
            "SPAN_093E04444FEB8344F235",
            "Very sparse reference versus high-density preload ETEM CNT growth.",
        )

    add_pdf_evidence(
        tables,
        store,
        duration_id,
        "PROCESS",
        "reactor_process_gas",
        f"{duration_id}_S02",
        "record_level",
        "SPAN_BD8FD48802453402B9F9",
        "main PDF page 8",
        (
            ATM_RECIPE_EVIDENCE_TEXT
            + " Preload duration series: 0, 5, 18, 180 and 1800 s; "
            "otherwise the standard recipe and 10 min CNT growth."
        ),
        "Preload-duration conditions.",
    )
    add_pdf_evidence(
        tables,
        store,
        duration_id,
        "RESULT",
        "yield_quality",
        f"{duration_id}_PROD",
        "record_level",
        "SPAN_BD8FD48802453402B9F9",
        "main PDF page 8",
        (
            "Figure 6 approximate transcription: density 17, 14, 34, 37, "
            "34 microgram/mm3 and height 1200, 1000, 1100, 1000, 950 "
            "micrometers at preload times 0, 5, 18, 180, 1800 s."
        ),
        "Graph-digitized preload-duration series.",
        value_status="figure_digitized_approximate",
        confidence="medium",
    )
    for stage in [1, 3, 4, 5, 6]:
        add_pdf_evidence(
            tables,
            store,
            duration_id,
            f"STAGE_{stage}",
            "reactor_process_gas",
            f"{duration_id}_S{stage:02d}",
            "record_level",
            "SPAN_39910C58537EE9FA3455",
            "SI pages 2-4",
            ATM_RECIPE_EVIDENCE_TEXT,
            "Standard-stage support.",
            source_ref=SI_REF,
        )

    for index, (run_id, _) in enumerate(modified_ids, start=1):
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "PROCESS",
            "reactor_process_gas",
            f"{run_id}_S01",
            "record_level",
            "SPAN_CFBFFEB67F213B491B23" if index == 1 else "SPAN_46F81587B4EF378AE681",
            "main PDF page 9 and SI pages 2-4",
            (
                ATM_RECIPE_EVIDENCE_TEXT
                + f" Modified preload {index} changes the ordering/purge "
                "around the standard 3 min preload and anneal."
            ),
            f"Modified preload {index} sequence and interpretation.",
            source_ref=SI_REF,
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "RESULT",
            "yield_quality",
            f"{run_id}_PROD",
            "record_level",
            "SPAN_46F81587B4EF378AE681",
            "main PDF page 9",
            (
                "Figure 7 local mass-density curves: modified 1 and 2 are "
                "low-density, while modified 3 retains a substantially higher "
                "profile after catalyst exposure during annealing."
            ),
            f"Modified preload {index} density-profile outcome.",
            value_status="figure_comparison",
        )

    for run_id, preload in lp_ids:
        for stage in range(1, 4):
            add_pdf_evidence(
                tables,
                store,
                run_id,
                f"PROCESS_{stage}",
                "reactor_process_gas",
                f"{run_id}_S{stage:02d}",
                "record_level",
                "SPAN_8A211B0EA2D52D083524",
                "main PDF page 4",
                LP_RECIPE_EVIDENCE_TEXT,
                "Low-pressure calcination, pressure and growth-gas conditions.",
            )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "PRODUCT",
            "yield_quality",
            f"{run_id}_PROD",
            "yield_original;Raman_ratio_value;Raman_laser_wavelength_nm",
            "SPAN_D2B7CACD5F084172714A",
            "main PDF page 10",
            (
                "Five-minute low-pressure SWCNT forest: "
                + (
                    "80.2 micrometers and G/D 8.6 with carbon preload."
                    if preload
                    else "26.1 micrometers and G/D 4.5 for reference."
                )
                + " Raman characterization used a 532 nm laser."
            ),
            "Low-pressure SWCNT height and Raman quality.",
        )

    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_SERIES_001",
                SOURCE_ID,
                ref_id,
                "series_aggregation",
                "source_run",
                ref_id,
                "run_summary",
                (
                    "Figure 2 contains multiple growth-time specimens. They "
                    "are retained as one experimental-series record because "
                    "many marker values are graphical rather than tabulated."
                ),
                f"EVD_{ref_id}_RESULT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_DIGITIZATION_001",
                SOURCE_ID,
                duration_id,
                "figure_digitization_uncertainty",
                "yield_quality",
                f"{duration_id}_PROD",
                "yield_original",
                (
                    "Figure 6 density/height values are approximate manual "
                    "visual transcriptions; the text only establishes the "
                    "18 s threshold and invariance through 1800 s."
                ),
                f"EVD_{duration_id}_RESULT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SAXS_001",
                SOURCE_ID,
                preload_id,
                "model_fit_uncertainty",
                "yield_quality",
                f"{preload_id}_PROD",
                "outer_diameter_range_nm",
                (
                    "Supplementary Figure S2 notes point-to-point fitting "
                    "inconsistencies; diameter, wall number and c values are "
                    "model-dependent and graph-digitized."
                ),
                f"EVD_{preload_id}_SAXS_SHAPE",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_MASS_DENSITY_001",
                SOURCE_ID,
                preload_id,
                "definition_scope",
                "yield_quality",
                f"{preload_id}_PROD",
                "yield_original",
                (
                    "Bulk forest mass density includes CNT and amorphous "
                    "carbon and was not corrected by TGA purity because the "
                    "spatial impurity distribution was unknown."
                ),
                f"EVD_{preload_id}_RESULT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CARBON_CONVERSION_001",
                SOURCE_ID,
                preload_id,
                "critical_data_gap",
                "yield_quality",
                f"{preload_id}_PROD",
                "carbon_source_conversion_percent",
                (
                    "No ethylene conversion, total carbon balance or CNT "
                    "productivity per feed amount is reported."
                ),
                f"EVD_{preload_id}_RESULT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_ETEM_TIME_001",
                SOURCE_ID,
                etem_ids[1][0],
                "critical_data_gap",
                "reactor_process_gas",
                f"{etem_ids[1][0]}_S03",
                "holding_time_min",
                "ETEM CNT-growth duration is not reported.",
                f"EVD_{etem_ids[1][0]}_PROCESS_3",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_MODIFIED_001",
                SOURCE_ID,
                modified_ids[0][0],
                "graph_only_result",
                "yield_quality",
                f"{modified_ids[0][0]}_PROD",
                "yield_original",
                (
                    "Modified-preload results are local-density curves without "
                    "tabulated point values; qualitative curve classification "
                    "is retained instead of invented exact measurements."
                ),
                f"EVD_{modified_ids[0][0]}_RESULT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_LP_ANNEAL_001",
                SOURCE_ID,
                lp_ids[1][0],
                "partial_recipe_inheritance",
                "reactor_process_gas",
                f"{lp_ids[1][0]}_S02",
                "reducing_gas_flow_original",
                (
                    "The low-pressure section states modifications to the main "
                    "recipe but does not separately restate all anneal/preload "
                    "gas flows."
                ),
                f"EVD_{lp_ids[1][0]}_PROCESS_2",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_GAS_001",
                SOURCE_ID,
                preload_id,
                "effluent_context_not_yield",
                "reactor_process_gas",
                f"{preload_id}_S03",
                "process_note",
                (
                    "Figure 8 VOC concentrations diagnose wall-carbon transfer "
                    "but are not a feed conversion or emission-rate measurement."
                ),
                f"EVD_{preload_id}_STAGE_3",
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
