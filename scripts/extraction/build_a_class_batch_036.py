#!/usr/bin/env python3
"""Build the thirty-sixth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 36
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ID = "LIT_58B091070B8AC565"
PDF_REF = "data/raw/literature/pdf/LIT_58B091070B8AC565_0788779913fa.pdf"

ABSTRACT_SPAN = "SPAN_D6ACF23A1E624A1A6A13"
PREP_SPAN = "SPAN_42360495DB363F0EEADE"
PROCESS_SPAN = "SPAN_A0857AB1D14F65F687E9"
TEMP_SPAN = "SPAN_C9B66946082783E041E9"
FLOW_SPAN = "SPAN_05F72D8BCBA8EAA2B684"
TIME_SPAN = "SPAN_BCF9CC35DAA85BC67D9F"
CHAR_SPAN = "SPAN_5AD5BB41A59051854490"

RUNS: list[dict[str, Any]] = [
    {
        "code": "TEMP_800",
        "series": "temperature",
        "temp": 800,
        "flow": 140,
        "time": 25,
        "diameter": "15-28",
        "outcome": "twisted and entangled MWCNTs; diameter tracks catalyst size",
    },
    {
        "code": "BASELINE_900_140_25",
        "series": "shared_baseline",
        "temp": 900,
        "flow": 140,
        "time": 25,
        "diameter": "25-40",
        "outcome": "central condition shared by all three one-factor screens",
    },
    {
        "code": "TEMP_1000",
        "series": "temperature",
        "temp": 1000,
        "flow": 140,
        "time": 25,
        "diameter": "28-53",
        "outcome": "largest diameters; catalyst sintering/agglomeration increased",
    },
    {
        "code": "FLOW_100",
        "series": "flow",
        "temp": 900,
        "flow": 100,
        "time": 25,
        "diameter": "14-22",
        "outcome": "lowest acetylene flow and smallest flow-series diameters",
    },
    {
        "code": "FLOW_180",
        "series": "flow",
        "temp": 900,
        "flow": 180,
        "time": 25,
        "diameter": "25-52",
        "outcome": "largest flow-series range with amorphous carbon on sidewalls",
    },
    {
        "code": "TIME_15",
        "series": "time",
        "temp": 900,
        "flow": 140,
        "time": 15,
        "diameter": "20-50",
        "outcome": "broad diameter range; 25% TGA weight loss and lower crystallinity",
    },
    {
        "code": "TIME_35",
        "series": "time",
        "temp": 900,
        "flow": 140,
        "time": 35,
        "diameter": "10-30",
        "outcome": "predominantly smaller, well-aligned and more crystalline MWCNTs; 2% TGA weight loss",
    },
]


def summary(item: dict[str, Any]) -> str:
    return (
        f"NiO/Al2O3-catalyzed atmospheric quartz-tube CVD at {item['temp']} C, "
        f"acetylene {item['flow']} mL/min for {item['time']} min, with 10 mg "
        f"catalyst and 100 mL/min Ar purge/carrier. MWCNT diameter range "
        f"{item['diameter']} nm. {item['outcome']}."
    )


def catalyst(run_id: str) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label="NiO supported on fumed Al2O3 nanoparticles",
        active_metals="Ni",
        support_material="fumed Al2O3 nanoparticles",
        promoter="none",
        metal_ratio_original="0.245 g Ni(NO3)2·6H2O per 1 g Al2O3",
        metal_ratio_standardized="reported precursor mass ratio retained",
        precursor_summary="Ni(NO3)2·6H2O in 30 mL methanol",
        preparation_method="wet impregnation",
        preparation_modifier="magnetic stirring and rotary evaporation",
        preparation_detail=(
            "1 g fumed alumina impregnated with 0.245 g nickel nitrate "
            "hexahydrate in 30 mL methanol for 1 h at room temperature; "
            "solvent removed by rotary evaporation; powder heated and ground."
        ),
        drying_condition="150 C overnight",
        calcination_condition="no separate calcination reported",
        reduction_condition="no separate H2 reduction; acetylene CVD directly applied",
        activation_condition="in-situ thermal activation in acetylene at reaction temperature",
        post_preparation_condition="fine NiO/Al2O3 powder; 10 mg per run",
        catalyst_particle_size_mean_nm="",
        catalyst_particle_size_range_nm="",
        catalyst_particle_size_qualifier=(
            "approximately 15-30 nm spherical particles; some agglomerated before CVD"
        ),
        phase_or_state_summary="spherical NiO particles on alumina",
        dispersion_summary="partly agglomerated pristine catalyst",
        deactivation_summary="high acetylene flow covered catalyst with amorphous carbon",
    )


def process(item: dict[str, Any], run_id: str) -> dict[str, str]:
    return process_row(
        run_id,
        1,
        "acetylene_thermal_CVD",
        reactor_type="horizontal thermal CVD quartz-tube reactor",
        scale_level="laboratory_batch",
        reactor_material="quartz tube",
        reactor_size_summary="70 mm diameter and 300 mm length",
        reactor_setup_summary="10 mg catalyst at center of hot zone",
        catalyst_loading_mass_g="0.01",
        temperature_setpoint_C=str(item["temp"]),
        temperature_range_reported_C=str(item["temp"]),
        temperature_program_summary=(
            "Ar heat-up to setpoint; Ar stopped and acetylene introduced; "
            "acetylene replaced with Ar for cooling"
        ),
        holding_time_min=str(item["time"]),
        heating_rate_C_min="not_reported",
        cooling_condition="cooled to room temperature under 100 mL/min Ar",
        pressure_original="atmospheric pressure",
        pressure_kPa="101.325",
        carbon_source="C2H2",
        carbon_source_flow_original=f"{item['flow']} mL/min",
        reducing_gas="none separately added",
        reducing_gas_flow_original="0 mL/min",
        inert_gas="Ar",
        inert_gas_flow_original="100 mL/min during heat-up and cooling",
        cofeed_or_reactive_gas="none",
        cofeed_flow_original="0 mL/min",
        total_flow_original=f"{item['flow']} mL/min during growth",
        gas_composition_summary="pure acetylene during growth; Ar before and after",
        process_note="One-factor-at-a-time design over temperature, flow and time.",
    )


def product(item: dict[str, Any], run_id: str) -> dict[str, str]:
    char15 = item["code"] == "TIME_15"
    char35 = item["code"] == "TIME_35"
    return yield_row(
        run_id,
        primary_yield_metric="MWCNT_outer_diameter_range",
        yield_original=f"{item['diameter']} nm diameter range",
        yield_definition_original="FESEM/ImageJ MWCNT diameter distribution",
        yield_calculation_method="diameters measured from FESEM images with ImageJ",
        yield_value_standardized="",
        yield_unit_standardized="nm_range",
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=summary(item),
        CNT_type_reported="MWCNT",
        CNT_type_confirmed="MWCNT",
        product_mixture_summary="MWCNTs plus catalyst/amorphous carbon before purification",
        CNT_type_evidence="FESEM; HRTEM; Raman; TGA/DTA",
        SWCNT_or_few_wall_evidence_summary="multi-walled; wall count not quantified",
        RBM_peak_reported="680 cm-1 near-RBM feature" if char35 else "not_reported",
        outer_diameter_mean_nm="",
        outer_diameter_range_nm=item["diameter"],
        inner_diameter_mean_nm="",
        wall_number_summary="multi-walled; exact count not reported",
        length_summary="not_reported",
        morphology=item["outcome"],
        alignment_or_array=(
            "well-aligned bundles" if char35 else "twisted/entangled or bundled"
        ),
        Raman_ratio_type="ID/IG" if char15 or char35 else "not_reported",
        Raman_ratio_value="qualitatively lower at 35 min than 15 min"
        if char15 or char35
        else "",
        Raman_laser_wavelength_nm="",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis="purified by nitric acid, sonication and filtration",
        residue_summary=(
            "TGA weight loss 25%"
            if char15
            else ("TGA weight loss 2%" if char35 else "not quantified")
        ),
        amorphous_carbon_level=(
            "higher; oxidation near 150 C and 25% weight loss"
            if char15
            else (
                "low; 2% weight loss and oxidation feature near 300 C"
                if char35
                else "condition-dependent"
            )
        ),
        BET_surface_area_product_m2_g="",
        characterization_methods="FESEM; HRTEM; Raman; TGA/DTA",
        post_treatment_or_purification=(
            "concentrated HNO3 stirring 3 h; ethanol suspension, sonication "
            "10 min, ceramic-crucible filtration and furnace drying"
        ),
        purification_condition="room-temperature acid treatment followed by filtration",
        application_property_summary="controlled-diameter reinforcement material",
        notes="No mass yield, carbon conversion or numeric mean diameter table was reported.",
    )


def cost_review(item: dict[str, Any], run_id: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="laboratory quartz-tube batch CVD",
        scale_level_claimed="simple economical CVD route; no pilot scale",
        scale_evidence_summary=summary(item),
        reactor_capacity_or_throughput="10 mg catalyst per run; product mass not reported",
        continuous_operation_time_h=str(item["time"] / 60),
        catalyst_lifetime_or_reuse="not_reported",
        catalyst_reuse_cycles="not_reported",
        batch_stability="not_reported",
        scale_up_issue="diameter uniformity, catalyst sintering, amorphous carbon and acid purification",
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="No study-specific cost calculation.",
        cost_driver_summary="900 C-class furnace, acetylene, Ni salt and nitric-acid purification",
        safety_risk="flammable acetylene; concentrated HNO3; hot quartz reactor",
        emission_or_waste="acidic Ni-containing waste and amorphous carbon",
        industrial_readiness_assessment="laboratory parameter screening",
        reproduction_value="high",
        reproduction_priority="high",
        recommended_next_action="report replicates, mean/SD, mass yield, gas conversion and purification recovery",
        review_note="Affordable/large-scale statements are general CVD context.",
    )


def span_for(item: dict[str, Any]) -> tuple[str, int]:
    return {
        "temperature": (TEMP_SPAN, 5),
        "flow": (FLOW_SPAN, 5),
        "time": (TIME_SPAN, 7),
        "shared_baseline": (TEMP_SPAN, 5),
    }[item["series"]]


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
            "evidence_type": "pdf_text_transcription",
            "source_section": f"PDF page {page}",
            "source_locator": f"PDF page {page}",
            "source_object_ref": PDF_REF,
            "evidence_text": text,
            "evidence_summary": summary_text,
            "notes": "Values transcribed from the local open-access PDF.",
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
        run_row(SOURCE_ID, item["code"], item["series"], run_summary, "high")
    )
    cat = catalyst(run_id)
    stage = process(item, run_id)
    prod = product(item, run_id)
    cost = cost_review(item, run_id)
    tables["catalyst_system"].append(cat)
    tables["reactor_process_gas"].append(stage)
    tables["yield_quality"].append(prod)
    tables["cost_scale_review"].append(cost)
    span, page = span_for(item)

    add_evidence(
        tables,
        store,
        run_id,
        "RUN",
        "source_run",
        run_id,
        span,
        page,
        run_summary,
        "Run condition and diameter range.",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "CATALYST",
        "catalyst_system",
        cat["catalyst_id"],
        PREP_SPAN,
        3,
        (
            f"{cat['catalyst_label']}; ratio {cat['metal_ratio_original']}; "
            f"preparation {cat['preparation_detail']}; drying "
            f"{cat['drying_condition']}; particle qualifier "
            f"{cat['catalyst_particle_size_qualifier']}"
        ),
        "NiO/Al2O3 preparation and particle size.",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "PROCESS",
        "reactor_process_gas",
        stage["process_stage_id"],
        PROCESS_SPAN,
        4,
        (
            f"Quartz reactor {stage['reactor_size_summary']}; catalyst "
            f"{stage['catalyst_loading_mass_g']} g; temperature "
            f"{stage['temperature_setpoint_C']} C; duration "
            f"{stage['holding_time_min']} min; pressure "
            f"{stage['pressure_original']} / {stage['pressure_kPa']} kPa; "
            f"acetylene {stage['carbon_source_flow_original']}; Ar "
            f"{stage['inert_gas_flow_original']}; total "
            f"{stage['total_flow_original']}; cooling {stage['cooling_condition']}"
        ),
        "CVD reactor, feed and timing.",
    )
    add_evidence(
        tables,
        store,
        run_id,
        "PRODUCT",
        "yield_quality",
        prod["product_id"],
        CHAR_SPAN if item["series"] == "time" else span,
        9 if item["series"] == "time" else page,
        (
            f"MWCNT diameter range {prod['outer_diameter_range_nm']} nm; "
            f"morphology {prod['morphology']}; alignment "
            f"{prod['alignment_or_array']}; RBM {prod['RBM_peak_reported']}; "
            f"Raman {prod['Raman_ratio_type']} {prod['Raman_ratio_value']}; "
            f"residue {prod['residue_summary']}; amorphous carbon "
            f"{prod['amorphous_carbon_level']}; purification "
            f"{prod['post_treatment_or_purification']}."
        ),
        "Diameter, morphology, Raman/TGA and purification.",
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
            f"Laboratory 10 mg catalyst run for {item['time']} min; no product "
            "mass or cost. Acetylene and concentrated HNO3 drive safety/waste."
        ),
        "Scale, cost-data gap and safety review.",
        status="review_assessment",
    )
    return run_id


def build(
    metadata: dict[str, Any], store: EvidenceStore
) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "Seven unique physical conditions after merging the shared "
                "900 C, 140 mL/min, 25 min baseline across three one-factor screens."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_open_access_pdf"
    master["notes"] += " The central condition was not triplicated."
    run_ids = {item["code"]: add_run(tables, store, item) for item in RUNS}
    baseline = run_ids["BASELINE_900_140_25"]
    time15 = run_ids["TIME_15"]
    time35 = run_ids["TIME_35"]
    flow180 = run_ids["FLOW_180"]
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_BASELINE_MERGE_001",
                SOURCE_ID,
                baseline,
                "duplicate_condition_merge",
                "source_run",
                baseline,
                "run_summary",
                "The same 900 C/140 mL-min/25 min condition anchors all three screens and is represented once.",
                f"EVD_{baseline}_RUN",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_NO_MEAN_TABLE_001",
                SOURCE_ID,
                baseline,
                "critical_data_gap",
                "yield_quality",
                f"{baseline}_PROD",
                "outer_diameter_mean_nm",
                "Mean diameters appear only in plots; the text provides diameter ranges, which are retained without visual interpolation.",
                f"EVD_{baseline}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_REPLICATES_001",
                SOURCE_ID,
                baseline,
                "critical_data_gap",
                "source_run",
                baseline,
                "run_summary",
                "Replicate count, sample count per diameter distribution and statistical uncertainty are not reported.",
                f"EVD_{baseline}_RUN",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_TGA_METRIC_001",
                SOURCE_ID,
                time15,
                "metric_definition",
                "yield_quality",
                f"{time15}_PROD",
                "residue_summary",
                "The reported 25% and 2% TGA weight losses are retained as stated and are not converted into purity without a complete temperature-resolved mass balance.",
                f"EVD_{time15}_PRODUCT;EVD_{time35}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_RBM_ASSIGNMENT_001",
                SOURCE_ID,
                time35,
                "characterization_interpretation",
                "yield_quality",
                f"{time35}_PROD",
                "RBM_peak_reported",
                "The authors describe a 680 cm-1 peak as near RBM despite assigning the product as MWCNT; the interpretation is retained verbatim.",
                f"EVD_{time35}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_HIGH_FLOW_CARBON_001",
                SOURCE_ID,
                flow180,
                "product_mixture",
                "yield_quality",
                f"{flow180}_PROD",
                "amorphous_carbon_level",
                "At 180 mL/min acetylene, amorphous carbon coated CNT sidewalls; no quantitative fraction was reported.",
                f"EVD_{flow180}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_NO_YIELD_001",
                SOURCE_ID,
                time35,
                "critical_data_gap",
                "yield_quality",
                f"{time35}_PROD",
                "CNT_yield_per_catalyst_g_gcat",
                "No CNT mass yield, carbon conversion, recovered mass after purification or gas balance was reported.",
                f"EVD_{time35}_PRODUCT",
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
    (REPORT_ROOT / f"batch_{BATCH_NUMBER:03d}_metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
