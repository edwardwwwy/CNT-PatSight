#!/usr/bin/env python3
"""Build the ninth evidence-grounded A-class extraction batch."""
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


BATCH_NUMBER = 9
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_458C915DF011F7D3"


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


def catalyst(
    run_id: str,
    substrate: str,
    mask: str,
    film: str,
) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label=f"nanosphere-lithography Ni dots on {substrate}",
        active_metals="Ni",
        support_material=substrate,
        promoter="not_applicable",
        metal_ratio_original=film,
        metal_ratio_standardized=film,
        precursor_summary="electron-beam-evaporated Ni film",
        preparation_method="nanosphere_lithography_then_e_beam_evaporation",
        preparation_modifier=mask,
        preparation_detail=(
            f"Nanosphere mask applied to {substrate}; {film} Ni deposited by "
            "electron-beam evaporation; spheres removed in CH2Cl2 with "
            "ultrasonication, then substrate rinsed and dried."
        ),
        drying_condition="deionized-water rinse and blown dry",
        calcination_condition="not_applicable",
        reduction_condition="NH3 plasma pre-etch before CNT deposition",
        activation_condition=(
            "NH3 inductive plasma, 8 sccm, approximately 12 Pa, 900 W, "
            "5-15 min"
        ),
        post_preparation_condition="heated/etched Ni islands coalesced to round dots",
        catalyst_particle_size_mean_nm="not_reported",
        catalyst_particle_size_range_nm="not_reported",
        catalyst_particle_size_qualifier="not_reported",
        phase_or_state_summary="Ni islands/dots",
        dispersion_summary="periodic or irregular nanoscale dot pattern",
        deactivation_summary="not_reported",
    )


def stages(
    run_id: str,
    temperature: str,
    duration: str,
    pressure: str,
    carbon: str,
    carbon_flow: str,
    diluent: str,
    diluent_flow: str,
    composition: str,
    program: str,
) -> list[dict[str, str]]:
    setup = (
        "Planar-antenna RF PECVD operated in capacitively coupled mode; "
        "sample stage grounded to confine plasma between stage and quartz window."
    )
    return [
        process_row(
            run_id,
            1,
            "NH3_plasma_catalyst_preetch",
            reactor_type="planar-antenna RF PECVD",
            reactor_material="quartz dielectric window; grounded sample stage",
            reactor_setup_summary=setup,
            temperature_setpoint_C="not_reported",
            holding_time_min="5-15",
            pressure_original="approximately 12 Pa",
            pressure_kPa="",
            cofeed_or_reactive_gas="NH3",
            cofeed_flow_original="8 sccm",
            cofeed_flow_sccm="8",
            total_flow_original="8 sccm",
            total_flow_sccm="8",
            gas_composition_summary="NH3 inductive plasma at 900 W RF power",
            process_note="Catalyst-size optimization before CNT deposition.",
        ),
        process_row(
            run_id,
            2,
            "capacitive_RF_PECVD_CNT_growth",
            reactor_type="planar-antenna RF PECVD",
            reactor_material="quartz dielectric window; grounded sample stage",
            reactor_setup_summary=setup,
            temperature_setpoint_C=temperature,
            temperature_program_summary=program,
            holding_time_min=duration,
            pressure_original=pressure,
            pressure_kPa="",
            carbon_source=carbon,
            carbon_source_flow_original=carbon_flow,
            reducing_gas=diluent if diluent == "H2" else "not_applicable",
            reducing_gas_flow_original=(
                diluent_flow if diluent == "H2" else "not_applicable"
            ),
            inert_gas="not_applicable",
            cofeed_or_reactive_gas=diluent,
            cofeed_flow_original=diluent_flow,
            total_flow_original="not_reported",
            gas_composition_summary=composition,
            process_note="Capacitively coupled plasma; 700 W RF input power.",
        ),
    ]


def cost(run_id: str, throughput: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="lab_batch",
        scale_level_claimed="scale_up_potential",
        scale_evidence_summary=(
            "Substrate-based planar RF PECVD with nanosphere-lithography Ni "
            "patterning; the author describes NSL as simple and large-area capable."
        ),
        reactor_capacity_or_throughput=throughput,
        continuous_operation_time_h="not_applicable",
        catalyst_lifetime_or_reuse="not_reported",
        batch_stability="single representative deposition condition",
        scale_up_issue=(
            "Uniform large-area catalyst patterning, plasma uniformity, "
            "substrate throughput and gas utilization require scale-up work."
        ),
        cost_driver_summary=(
            "Ni evaporation, nanosphere masks, RF power, vacuum, substrate "
            "heating and reactive gases; no quantitative cost reported."
        ),
        safety_risk=(
            "Acetylene or methane with hydrogen/ammonia under RF plasma and "
            "vacuum; solvent and nanoparticle handling."
        ),
        emission_or_waste=(
            "Unreacted hydrocarbon/ammonia or hydrogen exhaust and spent "
            "nanosphere/solvent materials; quantities not reported."
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
                "Doctoral dissertation Chapter 4 CNT catalyst patterning, "
                "RF-PECVD conditions and CNT morphology/characterization. "
                "Carbon-nanosheet experiments are excluded from production runs."
            ),
        )
    )
    tables["source_master"][0]["local_file_path"] = (
        f"data/interim/parsed_text/{SOURCE_ID}/full_text.txt"
    )
    tables["source_master"][0]["notes"] += (
        " PDF pages 93-95 were visually checked to resolve OCR-split values "
        "for the typical, aligned and methane/H2 CNT depositions."
    )

    configs = [
        {
            "code": "R01",
            "label": "typical random MWCNT; C2H2/NH3 capacitive RF PECVD",
            "summary": (
                "Approximately 700 C, 1 Torr, 700 W and 20 min; random "
                "20-50 nm MWCNTs several micrometers long."
            ),
            "substrate": "Si",
            "mask": "419 nm self-assembled polystyrene nanospheres",
            "film": "10-30 nm Ni film",
            "temperature": "approximately 700",
            "duration": "20",
            "pressure": "approximately 1 Torr",
            "carbon": "C2H2",
            "carbon_flow": "15 sccm",
            "diluent": "NH3",
            "diluent_flow": "60 sccm",
            "composition": "20% C2H2 in NH3; 15 sccm C2H2 and 60 sccm NH3",
            "program": "700 W RF power; grounded sample stage",
            "yield": yield_row(
                f"{SOURCE_ID}_R01",
                primary_yield_metric="qualitative_CNT_deposition",
                yield_original="randomly oriented CNT deposition; mass yield not reported",
                yield_definition_original="morphology and presence by SEM/HRTEM",
                yield_calculation_method="qualitative microscopy characterization",
                yield_value_standardized="not_reported",
                yield_unit_standardized="not_applicable",
                secondary_result_summary=(
                    "Spaghetti-like CNTs, typically 20-50 nm in diameter and "
                    "several micrometers long; base-growth mechanism."
                ),
                CNT_type_reported="carbon nanotubes",
                CNT_type_confirmed="MWCNTs",
                product_mixture_summary=(
                    "Hollow multi-walled nanotubes; defects observed by Raman."
                ),
                CNT_type_evidence="HRTEM parallel graphene layers and hollow center.",
                outer_diameter_range_nm="20-50",
                wall_number_summary="multi-walled",
                length_summary="several micrometers",
                morphology="spaghetti-like hollow nanotubes",
                alignment_or_array="randomly oriented",
                Raman_ratio_type="not_reported",
                Raman_ratio_value="not_reported",
                Raman_laser_wavelength_nm="514",
                amorphous_carbon_level="defective-carbon D band present; not quantified",
                characterization_methods="SEM; HRTEM; Raman spectroscopy",
                post_treatment_or_purification="none reported",
                purification_condition="not_applicable",
            ),
            "process_span": "SPAN_FDB299AEC289B3F94DF5",
            "quality_span": "SPAN_E7235AC8F1D00DEFB055",
        },
        {
            "code": "R02",
            "label": "aligned CNT array; C2H2/NH3 on Ni/SiO2/Si",
            "summary": (
                "680 C, 1 Torr, 700 W, +50 V and 12 min; vertically aligned "
                "approximately 50 nm CNT arrays by tip growth."
            ),
            "substrate": "365 nm SiO2-coated Si",
            "mask": "400 nm non-self-assembled silica nanospheres",
            "film": "Ni dot pattern; film thickness not repeated",
            "temperature": "680",
            "duration": "12",
            "pressure": "1 Torr",
            "carbon": "C2H2",
            "carbon_flow": "not_reported",
            "diluent": "NH3",
            "diluent_flow": "not_reported",
            "composition": "20% C2H2 in NH3",
            "program": "700 W RF power; +50 V DC bias",
            "yield": yield_row(
                f"{SOURCE_ID}_R02",
                primary_yield_metric="qualitative_aligned_CNT_deposition",
                yield_original="vertically aligned CNT array; mass yield not reported",
                yield_definition_original="alignment and morphology by SEM",
                yield_calculation_method="qualitative microscopy characterization",
                yield_value_standardized="not_reported",
                yield_unit_standardized="not_applicable",
                secondary_result_summary=(
                    "Approximately 50 nm CNT diameter; Ni at tube top supports "
                    "tip-growth mechanism."
                ),
                CNT_type_reported="vertically aligned carbon nanotubes",
                CNT_type_confirmed="not_applicable",
                product_mixture_summary="Aligned CNT array; wall count not reported.",
                CNT_type_evidence="SEM alignment and catalyst position.",
                outer_diameter_mean_nm="approximately 50",
                outer_diameter_range_nm="not_reported",
                wall_number_summary="not_reported",
                morphology="vertically aligned nanotubes",
                alignment_or_array="vertically aligned array",
                characterization_methods="SEM",
                post_treatment_or_purification="none reported",
                purification_condition="not_applicable",
            ),
            "process_span": "SPAN_747B1CCBA6021A4138CF",
            "quality_span": "SPAN_A57EFCB1FB32490555A9",
        },
        {
            "code": "R03",
            "label": "sparse CNT/CNF; CH4/H2 capacitive RF PECVD",
            "summary": (
                "680 C, 1 Torr, 700 W and 5 min using 20% CH4/H2; very few "
                "one-dimensional nanotube structures observed."
            ),
            "substrate": "Ni-patterned substrate; exact substrate not repeated",
            "mask": "nanosphere-lithography pattern; exact mask not repeated",
            "film": "Ni film thickness not repeated",
            "temperature": "680",
            "duration": "5",
            "pressure": "1 Torr",
            "carbon": "CH4",
            "carbon_flow": "not_reported",
            "diluent": "H2",
            "diluent_flow": "not_reported",
            "composition": "20% CH4 in H2",
            "program": "700 W RF power; other conditions as typical CNT deposition",
            "yield": yield_row(
                f"{SOURCE_ID}_R03",
                primary_yield_metric="qualitative_sparse_CNT_deposition",
                yield_original="very few nanotubes observed; mass yield not reported",
                yield_definition_original="qualitative abundance by SEM",
                yield_calculation_method="qualitative microscopy characterization",
                yield_value_standardized="not_reported",
                yield_unit_standardized="not_applicable",
                secondary_result_summary="Very few one-dimensional CNT structures observed.",
                CNT_type_reported="CNTs; carbon nanofibers",
                CNT_type_confirmed="not_applicable",
                product_mixture_summary=(
                    "Source alternates between CNT and carbon-nanofiber "
                    "terminology for the CH4/H2 product."
                ),
                CNT_type_evidence="SEM only; wall count not reported.",
                wall_number_summary="not_reported",
                morphology="sparse one-dimensional nanotube/fiber structures",
                alignment_or_array="not_reported",
                characterization_methods="SEM",
                post_treatment_or_purification="none reported",
                purification_condition="not_applicable",
            ),
            "process_span": "SPAN_A57EFCB1FB32490555A9",
            "quality_span": "SPAN_C474EF300F8B8E46C242",
        },
    ]

    for config in configs:
        code = str(config["code"])
        run_id = f"{SOURCE_ID}_{code}"
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                code,
                str(config["label"]),
                str(config["summary"]),
                "high" if code != "R03" else "medium",
            )
        )
        tables["catalyst_system"].append(
            catalyst(
                run_id,
                str(config["substrate"]),
                str(config["mask"]),
                str(config["film"]),
            )
        )
        tables["reactor_process_gas"].extend(
            stages(
                run_id,
                str(config["temperature"]),
                str(config["duration"]),
                str(config["pressure"]),
                str(config["carbon"]),
                str(config["carbon_flow"]),
                str(config["diluent"]),
                str(config["diluent_flow"]),
                str(config["composition"]),
                str(config["program"]),
            )
        )
        tables["yield_quality"].append(config["yield"])
        tables["cost_scale_review"].append(
            cost(run_id, f"{config['duration']}-min substrate deposition")
        )

        append_evidence(
            tables,
            store,
            run_id,
            "CAT_PATTERN",
            "catalyst_system",
            f"{run_id}_CAT",
            "record_level",
            "SPAN_EE0723AA025BB59C4775",
            "Nanosphere materials and Ni-patterning substrate context.",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "CAT_FILM",
            "catalyst_system",
            f"{run_id}_CAT",
            "precursor_summary;preparation_method;preparation_detail;"
            "drying_condition;post_preparation_condition;"
            "metal_ratio_original;metal_ratio_standardized",
            "SPAN_A7620A84C299ABD3CFEF",
            "Ni evaporation, sphere removal, rinse and catalyst-dot preparation.",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "PREETCH",
            "reactor_process_gas",
            f"{run_id}_S01",
            "record_level",
            "SPAN_FDB299AEC289B3F94DF5",
            "Common NH3 plasma catalyst pre-etch and capacitive reactor setup.",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "PROCESS",
            "reactor_process_gas",
            f"{run_id}_S02",
            "record_level",
            str(config["process_span"]),
            "Run-specific RF-PECVD growth condition.",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "QUALITY",
            "yield_quality",
            f"{run_id}_PROD",
            "record_level",
            str(config["quality_span"]),
            "Run-specific morphology and CNT identity evidence.",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            "record_level",
            str(config["process_span"]),
            "Review assessment from the reported RF-PECVD condition.",
            "review_assessment",
        )
        if code == "R01":
            append_evidence(
                tables,
                store,
                run_id,
                "RAMAN",
                "yield_quality",
                f"{run_id}_PROD",
                "Raman_laser_wavelength_nm;amorphous_carbon_level;"
                "characterization_methods",
                "SPAN_E7235AC8F1D00DEFB055",
                "Typical-CNT Raman wavelength and D/G peak interpretation.",
            )
        if code == "R02":
            append_evidence(
                tables,
                store,
                run_id,
                "ALIGN",
                "yield_quality",
                f"{run_id}_PROD",
                "secondary_result_summary;outer_diameter_mean_nm;morphology;"
                "alignment_or_array",
                "SPAN_747B1CCBA6021A4138CF",
                "Aligned-array diameter and tip-growth evidence.",
            )

    device = add_observation(
        tables,
        store,
        "CNT_DEVICE",
        "SPAN_39869ADADFCB007E8644",
        (
            "A distinct back-gated CNT field-emission device used patterned "
            "W/Ni and a post-growth buffered-HF dip. It is retained as an "
            "application observation rather than an additional synthesis run."
        ),
    )
    cns = add_observation(
        tables,
        store,
        "CNS_EXCLUDED",
        "SPAN_EC2D61CED6CC2A8BAD1E",
        (
            "The dissertation contains extensive catalyst-free carbon-nanosheet "
            "experiments in inductively coupled plasma. CNS conditions are out "
            "of the CNT-production target and are not represented as runs."
        ),
    )

    r01 = f"{SOURCE_ID}_R01"
    r03 = f"{SOURCE_ID}_R03"
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_PDF_OCR_001",
                SOURCE_ID,
                r01,
                "definition_ambiguity",
                "reactor_process_gas",
                f"{r01}_S02",
                "holding_time_min",
                (
                    "Parsed text split the typical-condition values across "
                    "lines. PDF page 93 was visually checked and confirms "
                    "20 min, 20% C2H2, 15 sccm C2H2 and 60 sccm NH3."
                ),
                f"EVD_{r01}_PROCESS",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_001",
                SOURCE_ID,
                r01,
                "critical_data_gap",
                "yield_quality",
                f"{r01}_PROD",
                "yield_original",
                (
                    "The CNT chapter reports morphology and abundance but no "
                    "product mass, catalyst-normalized yield or carbon conversion."
                ),
                f"EVD_{r01}_QUALITY",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_NOMENCLATURE_001",
                SOURCE_ID,
                r03,
                "CNT_type_uncertainty",
                "yield_quality",
                f"{r03}_PROD",
                "CNT_type_reported",
                (
                    "The CH4/H2 product is called carbon nanofibers in one "
                    "sentence and CNTs/nanotube structures in the next; SEM "
                    "does not establish wall count."
                ),
                f"EVD_{r03}_QUALITY",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CATALYST_CONTEXT_001",
                SOURCE_ID,
                r03,
                "critical_data_gap",
                "catalyst_system",
                f"{r03}_CAT",
                "catalyst_label",
                (
                    "The CH4/H2 condition says other parameters match typical "
                    "CNT deposition but does not repeat the exact substrate, "
                    "mask or Ni-film thickness."
                ),
                f"EVD_{r03}_CAT_PATTERN;EVD_{r03}_PROCESS",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SCOPE_001",
                SOURCE_ID,
                "not_applicable",
                "definition_ambiguity",
                "source_master",
                SOURCE_ID,
                "source_section_scope",
                (
                    "Catalyst-free carbon nanosheets dominate later chapters "
                    "but are outside the CNT-production target. Device processing "
                    "is also kept separate from synthesis runs."
                ),
                f"{cns};{device}",
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
