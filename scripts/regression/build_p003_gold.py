#!/usr/bin/env python3
"""Build the P003 five-run gold regression package without touching curated data."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID = "P003_Pan_2025_FeMo_MgO_Methane_CNT"
BASE_DIR = ROOT / "data" / "benchmark" / "samples" / "six_papers" / SOURCE_ID
OUTPUT_DIR = (
    ROOT
    / "data"
    / "benchmark"
    / "gold"
    / "regression"
    / "gold"
    / SOURCE_ID
)
TABLES = (
    "source_master",
    "source_run",
    "catalyst_system",
    "reactor_process_gas",
    "yield_quality",
    "cost_scale_review",
    "evidence_index",
    "review_issue_log",
)

RUNS = {
    "P003_FE": {
        "label": "Fe/MgO",
        "active_metals": "Fe",
        "promoter": "not_applicable",
        "ratio": "Fe:MgO = 0.03 mol/mol",
        "precursors": "Fe(NO3)3·9H2O",
        "graphitic": "15%",
        "yield": "0.16 g gCat^-1 in 30 min",
        "type": "mixed SWCNT/DWCNT",
        "inner_mean": "6.2",
        "diameter_summary": "inner diameter 3-10 nm; mean 6.2 nm",
        "raman": "not_reported",
        "product": "SWCNTs and DWCNTs; randomly entangled CNT product",
    },
    "P003_FE_MO01": {
        "label": "Fe-0.1Mo/MgO",
        "active_metals": "Fe; Mo",
        "promoter": "Mo",
        "ratio": "Fe:MgO = 0.03 mol/mol; Mo:Fe = 0.1 mol/mol",
        "precursors": "Fe(NO3)3·9H2O; (NH4)6Mo7O24·4H2O",
        "graphitic": "59.9%",
        "yield": "0.40 g gCat^-1 in 30 min",
        "type": "SWCNT-dominant",
        "inner_mean": "7.9",
        "diameter_summary": "inner diameter 3-15 nm; mean 7.9 nm",
        "raman": "0.0",
        "product": "large number of SWCNTs in erect or lying-down orientations",
    },
    "P003_FE_MO05": {
        "label": "Fe-0.5Mo/MgO",
        "active_metals": "Fe; Mo",
        "promoter": "Mo",
        "ratio": "Fe:MgO = 0.03 mol/mol; Mo:Fe = 0.5 mol/mol",
        "precursors": "Fe(NO3)3·9H2O; (NH4)6Mo7O24·4H2O",
        "graphitic": ">95%",
        "yield": "not_reported",
        "type": "MWCNT-dominant",
        "inner_mean": "13.6",
        "diameter_summary": "mean inner diameter 13.6 nm",
        "raman": "0.30",
        "product": "MWCNT-dominant product",
    },
    "P003_FE_MO1": {
        "label": "Fe-1Mo/MgO",
        "active_metals": "Fe; Mo",
        "promoter": "Mo",
        "ratio": "Fe:MgO = 0.03 mol/mol; Mo:Fe = 1 mol/mol",
        "precursors": "Fe(NO3)3·9H2O; (NH4)6Mo7O24·4H2O",
        "graphitic": "96.2%",
        "yield": "1.03 g gCat^-1 in 30 min",
        "type": "MWCNT-dominant",
        "inner_mean": "15.7",
        "diameter_summary": "mean inner diameter 15.7 nm",
        "raman": "0.35",
        "product": "MWCNT-dominant product",
    },
    "P003_MO": {
        "label": "Mo/MgO",
        "active_metals": "Mo",
        "promoter": "not_applicable",
        "ratio": "Mo:MgO = 0.03 mol/mol",
        "precursors": "(NH4)6Mo7O24·4H2O",
        "graphitic": "38.8%",
        "yield": "0.08 g gCat^-1 in 30 min",
        "type": "no_CNT_graphite",
        "inner_mean": "not_reported",
        "diameter_summary": "not_applicable",
        "raman": "1.37",
        "product": "graphitic layers/graphene flakes; no CNT formation",
    },
}


def read_table(table: str) -> tuple[list[str], list[dict[str, str]]]:
    path = BASE_DIR / f"{table}.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_table(
    table: str, fieldnames: list[str], rows: list[dict[str, str]]
) -> None:
    path = OUTPUT_DIR / f"{table}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_source_master(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    row = dict(rows[0])
    row.update(
        {
            "screening_class": "candidate_extract",
            "source_section_scope": (
                "Experimental 2.2-2.4; Results 3.1-3.4; Figs. 1-3; "
                "supplement references S3-S8"
            ),
            "extraction_status": "needs_review",
            "review_status": "pending_review",
            "notes": (
                "Codex-authored five-run gold regression case; "
                "domain_expert_verified=false; not formal_extract."
            ),
        }
    )
    return [row]


def build_source_run(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_id = {row["run_id"]: dict(row) for row in rows}
    output = []
    for run_id, spec in RUNS.items():
        row = by_id[run_id]
        row.update(
            {
                "run_label": spec["label"],
                "relevance_class": "candidate_extract",
                "extraction_status": "needs_review",
                "extraction_confidence": "high",
                "run_summary": (
                    f"{spec['label']}; shared CH4 pyrolysis conditions at 850 °C "
                    f"for 30 min; product: {spec['product']}."
                ),
                "notes": (
                    "Fe-0.5Mo exact carbon productivity is figure-only and was "
                    "not digitized."
                    if run_id == "P003_FE_MO05"
                    else "not_reported"
                ),
            }
        )
        output.append(row)
    return output


def build_catalysts(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_id = {row["run_id"]: dict(row) for row in rows}
    output = []
    for run_id, spec in RUNS.items():
        row = by_id[run_id]
        row.update(
            {
                "catalyst_label": spec["label"],
                "active_metals": spec["active_metals"],
                "support_material": "MgO",
                "promoter": spec["promoter"],
                "metal_ratio_original": spec["ratio"],
                "precursor_summary": spec["precursors"],
                "preparation_method": (
                    "impregnation followed by hydrothermal treatment"
                ),
                "preparation_modifier": "not_applicable",
                "preparation_detail": (
                    "MgO and metal precursor dissolved separately in deionized "
                    "water, mixed, sonicated for 10 min, hydrothermally treated "
                    "at 200 °C for 2 h, cooled, dried, and crushed."
                ),
                "drying_condition": "100-120 °C after hydrothermal treatment",
                "calcination_condition": "not_reported",
                "reduction_condition": (
                    "no separate reduction reported; catalyst heated in He "
                    "before CH4 introduction"
                ),
                "activation_condition": "not_reported",
                "post_preparation_condition": "crushed into powder",
                "catalyst_particle_size_mean_nm": "not_reported",
                "catalyst_particle_size_range_nm": "not_reported",
                "catalyst_particle_size_qualifier": "not_reported",
                "phase_or_state_summary": (
                    "fresh catalyst nanosheet morphology; no distinct metal "
                    "particles observed by fresh-catalyst EDS mapping"
                ),
                "dispersion_summary": (
                    "Fe and Mo were uniformly dispersed on Mg(OH)2 in fresh "
                    "catalysts; high Mo loading caused spent-particle coarsening"
                ),
                "deactivation_summary": (
                    "Fe-1Mo remained active beyond 1 h"
                    if run_id == "P003_FE_MO1"
                    else "not_reported"
                ),
                "notes": (
                    f"Reported graphitic-carbon fraction: {spec['graphitic']}; "
                    "kept separate from CNT purity."
                ),
            }
        )
        output.append(row)
    return output


def build_process(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_key = {(row["run_id"], row["stage_type"]): dict(row) for row in rows}
    output = []
    for run_id in RUNS:
        for stage_order, stage_type in enumerate(("heating", "growth", "cooling"), 1):
            row = by_key[(run_id, stage_type)]
            row.update(
                {
                    "stage_order": str(stage_order),
                    "reactor_type": "horizontal quartz tube",
                    "scale_level": "lab_batch",
                    "reactor_material": "quartz",
                    "reactor_size_summary": "not_reported",
                    "reactor_setup_summary": "150 mg catalyst on a porcelain boat",
                    "catalyst_loading_mass_g": "0.15",
                    "pressure_original": "not_reported",
                    "pressure_kPa": "not_reported",
                }
            )
            if stage_type == "heating":
                row.update(
                    {
                        "temperature_setpoint_C": "850",
                        "temperature_program_summary": (
                            "heated to 850 °C at 10 °C/min in He"
                        ),
                        "holding_time_min": "not_reported",
                        "heating_rate_C_min": "10",
                        "cooling_condition": "not_applicable",
                        "carbon_source": "not_applicable",
                        "carbon_source_flow_original": "not_reported",
                        "carbon_source_flow_sccm": "not_reported",
                        "inert_gas": "He",
                        "gas_composition_summary": "He heating atmosphere",
                        "process_note": "shared heating stage",
                    }
                )
            elif stage_type == "growth":
                row.update(
                    {
                        "temperature_setpoint_C": "850",
                        "temperature_program_summary": (
                            "held at 850 °C while pure CH4 was introduced"
                        ),
                        "holding_time_min": "30",
                        "heating_rate_C_min": "not_applicable",
                        "cooling_condition": "not_applicable",
                        "carbon_source": "CH4",
                        "carbon_source_flow_original": "20 mL/min",
                        "carbon_source_flow_sccm": "20",
                        "inert_gas": "not_applicable",
                        "gas_composition_summary": "pure CH4",
                        "total_flow_original": "20 mL/min",
                        "total_flow_sccm": "20",
                        "process_note": "shared CNT growth stage",
                    }
                )
            else:
                row.update(
                    {
                        "temperature_setpoint_C": "not_reported",
                        "temperature_program_summary": "not_reported",
                        "holding_time_min": "not_reported",
                        "heating_rate_C_min": "not_applicable",
                        "cooling_condition": "cooled in He",
                        "carbon_source": "not_applicable",
                        "carbon_source_flow_original": "not_reported",
                        "carbon_source_flow_sccm": "not_reported",
                        "inert_gas": "He",
                        "gas_composition_summary": "He cooling atmosphere",
                        "process_note": "shared cooling stage",
                    }
                )
            output.append(row)
    return output


def build_yields(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_id = {row["run_id"]: dict(row) for row in rows}
    output = []
    for run_id, spec in RUNS.items():
        row = by_id[run_id]
        is_mo_control = run_id == "P003_MO"
        is_fe = run_id == "P003_FE"
        row.update(
            {
                "primary_yield_metric": "reported_yield_other",
                "yield_original": spec["yield"],
                "yield_definition_original": (
                    "TGA-derived total deposited carbon mass per residual "
                    "catalyst mass after 30 min"
                ),
                "yield_calculation_method": (
                    "[weight loss]/[residual weight]"
                ),
                "yield_value_standardized": "not_reported",
                "yield_unit_standardized": "not_reported",
                "yield_standardization_note": (
                    "Reported carbon productivity; not isolated CNT yield, "
                    "methane conversion, or carbon efficiency."
                ),
                "CNT_yield_per_catalyst_g_gcat": "not_reported",
                "CNT_productivity_g_gcat_h": "not_reported",
                "secondary_result_summary": (
                    f"Graphitic-carbon fraction: {spec['graphitic']} "
                    "(TGA thermal-stability classification; not CNT purity)."
                ),
                "CNT_type_reported": spec["type"],
                "CNT_type_confirmed": spec["type"],
                "product_mixture_summary": spec["product"],
                "CNT_type_evidence": (
                    f"{spec['product']}; {spec['diameter_summary']}."
                ),
                "SWCNT_or_few_wall_evidence_summary": (
                    f"{spec['product']}; {spec['diameter_summary']}."
                    if run_id in {"P003_FE", "P003_FE_MO01"}
                    else "not_applicable"
                ),
                "inner_diameter_mean_nm": spec["inner_mean"],
                "morphology": (
                    "graphite/graphene flakes"
                    if is_mo_control
                    else spec["product"]
                ),
                "alignment_or_array": (
                    "not_applicable"
                    if is_mo_control
                    else (
                        "randomly entangled"
                        if is_fe
                        else (
                            "mixed erect and lying-down orientations"
                            if run_id == "P003_FE_MO01"
                            else "not_reported"
                        )
                    )
                ),
                "Raman_ratio_type": (
                    "not_reported" if spec["raman"] == "not_reported" else "ID/IG"
                ),
                "Raman_ratio_value": spec["raman"],
                "Raman_laser_wavelength_nm": "532",
                "TGA_carbon_content_wt_percent": "not_reported",
                "purified_product_purity_wt_percent": "not_reported",
                "purity_basis": "not_reported",
                "characterization_methods": (
                    "(S)TEM; TGA; Raman (532 nm); XRD; N2 adsorption"
                ),
                "post_treatment_or_purification": (
                    "HCl dissolution used only for separated-CNT diameter "
                    "analysis"
                    if is_fe
                    else "not_reported"
                ),
                "purification_condition": "not_reported",
                "notes": (
                    "Exact carbon productivity appears only in Fig. 2f and is "
                    "not digitized; graphitic fraction is not product purity."
                    if run_id == "P003_FE_MO05"
                    else (
                        f"Graphitic-carbon fraction {spec['graphitic']} is not "
                        "post-purification CNT purity."
                    )
                ),
            }
        )
        output.append(row)
    return output


def build_cost_scale(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_id = {row["run_id"]: dict(row) for row in rows}
    output = []
    for run_id in RUNS:
        row = by_id[run_id]
        row.update(
            {
                "scale_level_demonstrated": "lab_batch",
                "scale_level_claimed": "not_reported",
                "scale_evidence_summary": (
                    "150 mg catalyst in a horizontal quartz-tube laboratory "
                    "experiment"
                ),
                "reactor_capacity_or_throughput": "not_reported",
                "continuous_operation_time_h": (
                    ">1" if run_id == "P003_FE_MO1" else "not_reported"
                ),
                "catalyst_lifetime_or_reuse": (
                    "remained active beyond 1 hour"
                    if run_id == "P003_FE_MO1"
                    else (
                        "carbon productivity plateaued within 30 min"
                        if run_id in {"P003_FE", "P003_FE_MO01"}
                        else "not_reported"
                    )
                ),
                "catalyst_reuse_cycles": "not_reported",
                "batch_stability": "not_reported",
                "scale_up_issue": "not_reported",
                "quantitative_cost_reported": "no",
                "quantitative_cost_summary": "not_reported",
                "cost_driver_summary": "not_reported",
                "safety_risk": "not_reported",
                "emission_or_waste": "not_reported",
                "industrial_readiness_assessment": "",
                "reproduction_value": "",
                "reproduction_priority": "",
                "industrial_value_score": "",
                "recommended_next_action": "",
                "review_note": (
                    "Automated/LLM regression gold; industrial assessment "
                    "fields intentionally left empty pending independent evidence review."
                ),
            }
        )
        output.append(row)
    return output


def evidence_row(
    number: int,
    run_id: str,
    target_table: str,
    target_record_id: str,
    target_fields: str,
    section: str,
    locator: str,
    text: str,
    summary: str,
    *,
    evidence_type: str = "record_support",
    value_status: str = "reported",
    confidence: str = "high",
    linked_issue_id: str = "not_applicable",
    notes: str = "not_reported",
) -> dict[str, str]:
    return {
        "evidence_id": f"EVID_P003_GOLD_{number:04d}",
        "source_id": SOURCE_ID,
        "run_id": run_id,
        "target_table": target_table,
        "target_record_id": target_record_id,
        "target_fields": target_fields,
        "evidence_type": evidence_type,
        "value_status": value_status,
        "source_section": section,
        "source_locator": locator,
        "source_object_ref": "data/raw/literature/pdf/local_papers/d4cp04231j.pdf",
        "evidence_text": text,
        "evidence_summary": summary,
        "confidence": confidence,
        "linked_issue_id": linked_issue_id,
        "notes": notes,
    }


def build_evidence() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    number = 0

    prep_text = (
        "The catalysts are synthesized by impregnation and hydrothermal "
        "treatment. Commercial MgO powder and metal precursor were dissolved "
        "in deionized water respectively and mixed. The suspension was then "
        "sonicated for 10 min. Afterwards, hydrothermal treatment was "
        "performed at 200 °C in an autoclave for 2 h. After cooling down to "
        "room temperature, the suspension was dried at 100-120 °C, and the "
        "residual solid was crushed into powder."
    )
    ratio_texts = {
        "P003_FE": (
            "Regarding the fraction of Fe/MgO and Fe-Mo/MgO, Fe content were "
            "0.03 mol mol-1 MgO."
        ),
        "P003_FE_MO01": (
            "Mo as the second metal in Fe-Mo/MgO, the contents were 0.1, 0.5 "
            "and 1 mol mol-1 Fe, respectively."
        ),
        "P003_FE_MO05": (
            "Mo as the second metal in Fe-Mo/MgO, the contents were 0.1, 0.5 "
            "and 1 mol mol-1 Fe, respectively."
        ),
        "P003_FE_MO1": (
            "Mo as the second metal in Fe-Mo/MgO, the contents were 0.1, 0.5 "
            "and 1 mol mol-1 Fe, respectively."
        ),
        "P003_MO": "In Mo/MgO, Mo content was 0.03 mol mol-1 MgO.",
    }
    process_text = (
        "The experiments were performed in a horizontal quartz tube. 150 mg "
        "fresh catalyst was put on a porcelain boat and heated up to 850 °C "
        "with 10 °C min-1 rate in Helium. Then, temperature was kept at 850 °C "
        "for 30 min meanwhile pure CH4 with 20 mL min-1 flow rate was "
        "introduced. After reaction, the reactor was cooled down in Helium "
        "atmosphere."
    )
    yield_texts = {
        "P003_FE": (
            "Fe/MgO exhibits a carbon productivity of 0.16 g gCat.-1. Both "
            "SW- and DW-CNTs were clearly identified. The inner diameters were "
            "predominantly distributed between 3-10 nm, with an average inner "
            "diameter of 6.2 nm."
        ),
        "P003_FE_MO01": (
            "In Fe-0.1Mo, specifically, the carbon productivity reached "
            "0.40 g gCat.-1. A large number of SWCNTs were observed. The inner "
            "diameters mainly ranged from 3-15 nm, with an average diameter of "
            "7.9 nm. An ID/IG ratio of 0.0 was observed on Fe-0.1Mo."
        ),
        "P003_FE_MO05": (
            "The carbon productivity is illustrated in Fig. 2f (red column). "
            "MWCNTs dominated on the products of Fe-0.5Mo and Fe-1Mo "
            "catalysts, whose average inner diameters were enlarged to "
            "13.6 nm and 15.7 nm, respectively. The ID/IG ratios for "
            "Fe-0.5Mo and Fe-1Mo were 0.30 and 0.35, respectively."
        ),
        "P003_FE_MO1": (
            "The carbon productivity reached the maximum, 1.03 g gCat.-1, on "
            "Fe-1Mo. MWCNTs dominated on the products of Fe-0.5Mo and Fe-1Mo "
            "catalysts, whose average inner diameters were enlarged to "
            "13.6 nm and 15.7 nm, respectively. The ID/IG ratios for "
            "Fe-0.5Mo and Fe-1Mo were 0.30 and 0.35, respectively."
        ),
        "P003_MO": (
            "The Mo/MgO catalyst alone displays negligible carbon "
            "productivity (0.08 g gCat.-1). Mo/MgO exhibited graphitic layers "
            "with an interlayer spacing of 0.48 nm, while no evidence of CNT "
            "formation was observed. On Mo/MgO, the carbon product has an "
            "ID/IG ratio of 1.37."
        ),
    }
    graphitic_texts = {
        "P003_FE": "In the Fe/MgO system, graphitic carbon constituted only 15% of the total carbon species.",
        "P003_FE_MO01": "The proportion of graphitic carbon rose to 59.9% (Fe-0.1Mo).",
        "P003_FE_MO05": "In Fe-0.5Mo and Fe-1Mo catalysts, graphitic carbon selectivity exceeded 95%.",
        "P003_FE_MO1": "The proportion of graphitic carbon reached a maximum of 96.2% (Fe-1Mo).",
        "P003_MO": "The Mo/MgO system exhibited intermediate graphitic carbon content (38.8%).",
    }

    for run_id, spec in RUNS.items():
        number += 1
        rows.append(
            evidence_row(
                number,
                run_id,
                "catalyst_system",
                f"{run_id}_CAT",
                "record_level",
                "Experimental 2.2 Catalyst preparation",
                "p. 18303, section 2.2",
                f"{prep_text} {ratio_texts[run_id]}",
                (
                    f"{spec['label']} composition and shared impregnation/"
                    "hydrothermal preparation."
                ),
            )
        )
        for stage_type, suffix in (
            ("heating", "HEAT"),
            ("growth", "GROWTH"),
            ("cooling", "COOL"),
        ):
            number += 1
            rows.append(
                evidence_row(
                    number,
                    run_id,
                    "reactor_process_gas",
                    f"{run_id}_{suffix}",
                    "record_level",
                    "Experimental 2.3 Catalytic pyrolysis of CH4",
                    "p. 18303, section 2.3",
                    process_text,
                    f"Shared {stage_type} conditions for {spec['label']}.",
                )
            )
        number += 1
        issue_link = (
            "ISS_P003_GOLD_001"
            if run_id == "P003_FE_MO05"
            else "not_applicable"
        )
        rows.append(
            evidence_row(
                number,
                run_id,
                "yield_quality",
                f"{run_id}_PRODUCT",
                "record_level",
                "Results 3.2 Evaluation of carbon products",
                "pp. 18305-18306, section 3.2; Fig. 2f",
                f"{yield_texts[run_id]} {graphitic_texts[run_id]}",
                (
                    f"{spec['label']} productivity/product identity, CNT "
                    "diameter, Raman ratio, and graphitic fraction."
                ),
                linked_issue_id=issue_link,
                notes=(
                    "Exact Fe-0.5Mo productivity is shown graphically in Fig. "
                    "2f but is not stated numerically in the article text."
                    if run_id == "P003_FE_MO05"
                    else "not_reported"
                ),
            )
        )
        number += 1
        lifetime_text = (
            "Fe-1Mo demonstrated sustained activity, with carbon productivity "
            "increasing from 15 to 60 minutes."
            if run_id == "P003_FE_MO1"
            else (
                "Both Fe/MgO and Fe-0.1Mo exhibited rapid deactivation, with "
                "carbon productivities plateauing within 30 minutes."
                if run_id in {"P003_FE", "P003_FE_MO01"}
                else "No quantitative scale or cost analysis was reported."
            )
        )
        rows.append(
            evidence_row(
                number,
                run_id,
                "cost_scale_review",
                run_id,
                "record_level",
                "Experimental 2.3; Results 3.4",
                "p. 18303 section 2.3; p. 18307 section 3.4",
                f"{process_text} {lifetime_text}",
                (
                    f"Laboratory 150 mg quartz-tube scale for {spec['label']}; "
                    "lifetime included where explicitly reported."
                ),
            )
        )

    number += 1
    rows.append(
        evidence_row(
            number,
            "not_applicable",
            "source_master",
            SOURCE_ID,
            "notes",
            "Results 3.4 Discussion of the mechanism",
            "p. 18307, section 3.4",
            (
                "Continuous incorporation of Mo promotes the coarsening of "
                "Fe-Mo nanoparticles. Consequently, the dominant CNT structure "
                "shifts from single- and double-walled to multi-walled, while "
                "the mean CNT diameter increases from 6.2 nm to 15.7 nm."
            ),
            "Mo-loading mechanism and CNT-type transition source observation.",
            evidence_type="source_observation",
        )
    )
    return rows


def build_review_issues() -> list[dict[str, str]]:
    return [
        {
            "issue_id": "ISS_P003_GOLD_001",
            "source_id": SOURCE_ID,
            "run_id": "P003_FE_MO05",
            "issue_type": "critical_data_gap",
            "target_table": "yield_quality",
            "target_record_id": "P003_FE_MO05_PRODUCT",
            "target_field": "yield_original",
            "issue_summary": (
                "Fe-0.5Mo carbon productivity is shown in Fig. 2f but is not "
                "reported as an exact numeric value in article text."
            ),
            "conflicting_values": "not_applicable",
            "evidence_ids": "EVID_P003_GOLD_0017",
            "severity": "medium",
            "review_status": "pending_review",
            "reviewer": "not_assigned",
            "reviewed_at": "not_applicable",
            "resolution": "pending_review",
            "notes": (
                "Keep yield_original=not_reported unless the figure or underlying "
                "supplementary/raw data is independently digitized and reviewed."
            ),
        }
    ]


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    loaded = {table: read_table(table) for table in TABLES}
    builders = {
        "source_master": build_source_master,
        "source_run": build_source_run,
        "catalyst_system": build_catalysts,
        "reactor_process_gas": build_process,
        "yield_quality": build_yields,
        "cost_scale_review": build_cost_scale,
        "evidence_index": lambda _rows: build_evidence(),
        "review_issue_log": lambda _rows: build_review_issues(),
    }
    for table in TABLES:
        fieldnames, rows = loaded[table]
        write_table(table, fieldnames, builders[table](rows))
    print(OUTPUT_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
