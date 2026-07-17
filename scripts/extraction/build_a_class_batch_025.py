#!/usr/bin/env python3
"""Build the twenty-fifth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 25
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_8761E4F08EA23163"
PDF_REF = "data/raw/fulltext/pdf/LIT_8761E4F08EA23163_ccacb4452e54.pdf"


def stage(
    order: int,
    stage_type: str,
    evidence: str,
    **values: Any,
) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "order": order,
        "stage_type": stage_type,
        "evidence": evidence,
        "reactor_type": "laboratory CVD or preparation apparatus; configuration not reported",
        "scale_level": "lab_batch",
        "reactor_material": "not_reported",
        "reactor_size_summary": "not_reported",
        "reactor_setup_summary": "not_reported",
        "catalyst_loading_mass_g": "not_reported",
        "temperature_setpoint_C": "not_reported",
        "temperature_range_reported_C": "not_reported",
        "temperature_program_summary": "not_reported",
        "holding_time_min": "not_reported",
        "heating_rate_C_min": "not_reported",
        "cooling_condition": "not_reported",
        "pressure_original": "not_reported",
        "pressure_kPa": "",
        "carbon_source": "not_reported",
        "carbon_source_flow_original": "not_reported",
        "reducing_gas": "not_reported",
        "reducing_gas_flow_original": "not_reported",
        "inert_gas": "not_reported",
        "inert_gas_flow_original": "not_reported",
        "cofeed_or_reactive_gas": "not_reported",
        "cofeed_flow_original": "not_reported",
        "total_flow_original": "not_reported",
        "gas_composition_summary": "not_reported",
        "GHSV_or_residence_time": "not_reported",
        "process_note": evidence,
    }
    defaults.update(values)
    return defaults


def common_product(
    *,
    metric: str,
    yield_original: str,
    summary: str,
    cnt_type: str,
    morphology: str,
    characterization: str,
    raman_summary: str,
    outer_range: str = "",
    laser: str = "",
    post_treatment: str = "none reported",
    purification: str = "not_reported",
) -> dict[str, str]:
    return {
        "primary_yield_metric": metric,
        "yield_original": yield_original,
        "yield_definition_original": summary,
        "yield_calculation_method": "SEM/TEM/Raman qualitative assessment unless otherwise stated",
        "yield_value_standardized": "",
        "yield_unit_standardized": "",
        "yield_standardization_note": (
            "No mass yield or conversion was reported; dimensional and "
            "qualitative outcomes are retained without cross-definition conversion."
        ),
        "CNT_yield_per_catalyst_g_gcat": "",
        "CNT_productivity_g_gcat_h": "",
        "carbon_source_conversion_percent": "",
        "carbon_conversion_to_solid_percent": "",
        "secondary_result_summary": summary,
        "CNT_type_reported": cnt_type,
        "CNT_type_confirmed": cnt_type,
        "product_mixture_summary": summary,
        "CNT_type_evidence": characterization,
        "SWCNT_or_few_wall_evidence_summary": raman_summary,
        "RBM_peak_reported": "reported" if "RBM" in raman_summary else "not_reported",
        "outer_diameter_mean_nm": "",
        "outer_diameter_range_nm": outer_range,
        "inner_diameter_mean_nm": "",
        "wall_number_summary": cnt_type,
        "length_summary": summary,
        "morphology": morphology,
        "alignment_or_array": "not_reported",
        "Raman_ratio_type": "not_reported",
        "Raman_ratio_value": "",
        "Raman_laser_wavelength_nm": laser,
        "TGA_carbon_content_wt_percent": "",
        "purified_product_purity_wt_percent": "",
        "purity_basis": raman_summary,
        "residue_summary": "not quantitatively reported",
        "amorphous_carbon_level": (
            "qualitative only; retained in secondary result summary"
        ),
        "BET_surface_area_product_m2_g": "",
        "characterization_methods": characterization,
        "post_treatment_or_purification": post_treatment,
        "purification_condition": purification,
        "application_property_summary": "",
        "notes": (
            "This review-style chapter reports morphology and Raman quality "
            "but no gravimetric CNT yield, conversion, or productivity."
        ),
    }


def common_cost(run_id: str, route: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="lab_substrate_experiment",
        scale_level_claimed="not_reported",
        scale_evidence_summary=(
            f"Laboratory substrate-based {route}; no batch mass, throughput, "
            "energy intensity, or scale-up demonstration was reported."
        ),
        reactor_capacity_or_throughput="not_reported",
        continuous_operation_time_h="not_reported",
        catalyst_lifetime_or_reuse="not_reported",
        catalyst_reuse_cycles="not_reported",
        batch_stability="not_reported",
        scale_up_issue=(
            "Nanoparticle preparation uniformity, thermal stability, substrate "
            "coverage, gas delivery and CNT density reproducibility."
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="No monetary or normalized energy data reported.",
        cost_driver_summary=(
            "Ion implantation or colloid preparation, high-temperature H2 "
            "pretreatment, CH4/H2 CVD, lithographic-grade substrates and microscopy."
        ),
        safety_risk=(
            "flammable H2/CH4, high-temperature processing, HF exposure, "
            "ion implantation and oxidizing/plasma treatments where applicable"
        ),
        emission_or_waste=(
            "unquantified CVD exhaust; HF-containing waste and organic/metal "
            "precursor waste for applicable routes"
        ),
        industrial_readiness_assessment=(
            "mechanistic laboratory evidence only; mass productivity and "
            "large-area reproducibility are unreported"
        ),
        reproduction_value="high for catalyst-structure comparison",
        reproduction_priority="medium",
        recommended_next_action=(
            "Report exact gas flows, pressure, growth duration, CNT area density, "
            "replicates, collected mass and catalyst stability."
        ),
        review_note="Industrial assessment is evidence-limited and provisional.",
    )


def run_specs() -> list[dict[str, Any]]:
    return [
        {
            "code": "FIG1_C_IMPLANTED_GE_STRUCTURAL_REORGANIZATION",
            "label": "C-implanted Ge sample, catalyst-free structural reorganization",
            "summary": (
                "Self-assembled MWNTs and an early-stage DWNT were observed on "
                "a carbon-implanted Ge nanoparticle sample; no catalyst particle "
                "was detected at nanotube ends."
            ),
            "confidence": "medium",
            "span": "SPAN_37F89912233944A4F513",
            "page": 3,
            "catalyst": {
                "catalyst_label": "no external graphitization catalyst detected",
                "active_metals": "none detected at CNT ends",
                "support_material": "carbon-implanted Ge nanoparticle sample",
                "promoter": "none reported",
                "metal_ratio_original": "not_applicable",
                "metal_ratio_standardized": "not_applicable",
                "precursor_summary": "pre-existing amorphous carbon deposits",
                "preparation_method": "carbon implantation; exact implant conditions not restated",
                "preparation_modifier": "Ge nanoparticle substrate",
                "preparation_detail": (
                    "Carbon deposits reorganized into nanotubes at elevated "
                    "temperature; the exact annealing program was not reported."
                ),
                "drying_condition": "not_reported",
                "calcination_condition": "not_reported",
                "reduction_condition": "not_reported",
                "activation_condition": "elevated-temperature structural reorganization",
                "post_preparation_condition": "TEM sample scraped onto holey-carbon grid",
                "catalyst_particle_size_mean_nm": "",
                "catalyst_particle_size_range_nm": "",
                "catalyst_particle_size_qualifier": (
                    "No catalyst particle was detected at either nanotube end."
                ),
                "phase_or_state_summary": "amorphous carbon deposits on Ge nanoparticle sample",
                "dispersion_summary": "not_reported",
                "deactivation_summary": "not_applicable",
            },
            "stages": [
                stage(
                    1,
                    "non_cvd_structural_reorganization",
                    (
                        "Carbon nanostructures on a carbon-implanted Ge "
                        "nanoparticle sample formed by structural reorganization "
                        "of nearby amorphous carbon at elevated temperature; "
                        "the exact temperature, time, gas and pressure were not reported."
                    ),
                    reactor_type="annealing apparatus; not reported",
                    carbon_source="pre-deposited amorphous carbon",
                    process_note=(
                        "The chapter explicitly states that this route is not "
                        "strictly classed as CVD."
                    ),
                )
            ],
            "product": common_product(
                metric="qualitative_CNT_identity",
                yield_original="MWNTs and one early-stage DWNT observed",
                summary=(
                    "Small MWNTs and a DWNT in early growth were observed; no "
                    "catalyst was detected, graphitization was good, and few "
                    "impurities such as amorphous carbon were present."
                ),
                cnt_type="MWNT and DWNT",
                morphology="small self-assembled nanotubes",
                characterization="TEM",
                raman_summary="No Raman result reported for this figure.",
            ),
            "product_evidence": (
                "Figure 1 shows small MWNTs and a DWNT in the early stages of "
                "growth on a carbon-implanted Ge nanoparticle sample. No "
                "catalyst particle was detected at the nanotube ends; both "
                "structures had good graphitization and few amorphous-carbon impurities."
            ),
            "route": "non-CVD structural-reorganization control",
        },
        {
            "code": "AU_SIO2_PRETREAT_SCREEN_850_1050",
            "label": "Au/SiO2 pretreatment-temperature screen",
            "summary": (
                "Colloidal Au nanoparticles on 300 nm SiO2/Si were H2 "
                "pretreated for 10 min over 850-1050 C, then exposed to "
                "CH4/H2 at 850 C; the highest CNT area density occurred after "
                "1000 C pretreatment."
            ),
            "confidence": "medium",
            "span": "SPAN_1045E0900AA545305981",
            "page": 5,
            "catalyst": {
                "catalyst_label": "colloidal Au nanoparticles on SiO2/Si",
                "active_metals": "Au",
                "support_material": "300 nm SiO2-capped Si",
                "promoter": "none reported",
                "metal_ratio_original": "not_reported",
                "metal_ratio_standardized": "not_reported",
                "precursor_summary": "colloidal gold nanoparticles",
                "preparation_method": "spin coating",
                "preparation_modifier": "H2 pretreatment temperature screen",
                "preparation_detail": (
                    "As-deposited particles were approximately 1.4 nm in "
                    "diameter with density 2500 +/- 790 particles/um2 and "
                    "interparticle separation 20 +/- 3 nm. Density fell to "
                    "420 particles/um2 after 900 C and 290 particles/um2 "
                    "after 1000 C pretreatment."
                ),
                "drying_condition": "not_reported",
                "calcination_condition": "not_applicable",
                "reduction_condition": "H2 for 10 min at 850-1050 C",
                "activation_condition": "H2 pretreatment",
                "post_preparation_condition": "immediately followed by CH4/H2 growth",
                "catalyst_particle_size_mean_nm": "",
                "catalyst_particle_size_range_nm": "",
                "catalyst_particle_size_qualifier": (
                    "As-deposited diameter approximately 1.4 nm; distribution "
                    "broadened and modal height decreased as pretreatment temperature rose."
                ),
                "phase_or_state_summary": (
                    "Au nanoparticle loss/coalescence was attributed to "
                    "evaporation, diffusion into the substrate, ripening and migration."
                ),
                "dispersion_summary": (
                    "Initial density 2500 +/- 790 particles/um2; 420 at "
                    "900 C; 290 at 1000 C; initial separation 20 +/- 3 nm."
                ),
                "deactivation_summary": (
                    "High pretreatment temperature reduced Au particle density."
                ),
            },
            "stages": [
                stage(
                    1,
                    "catalyst_deposition",
                    (
                        "Colloidal Au nanoparticles were spin coated on a "
                        "Si substrate capped with 300 nm SiO2. The as-deposited "
                        "particles were approximately 1.4 nm with density "
                        "2500 +/- 790 particles/um2 and separation 20 +/- 3 nm."
                    ),
                    reactor_type="spin coater",
                    reactor_setup_summary="300 nm SiO2-capped Si substrate",
                    cofeed_or_reactive_gas="colloidal Au suspension",
                ),
                stage(
                    2,
                    "hydrogen_pretreatment_screen",
                    (
                        "Samples were pretreated in H2 for 10 min at "
                        "temperatures ranging from 850 to 1050 C. Particle "
                        "density was 420 particles/um2 after 900 C and "
                        "290 particles/um2 after 1000 C."
                    ),
                    temperature_setpoint_C="850-1050",
                    temperature_range_reported_C="850-1050",
                    temperature_program_summary="H2 pretreatment-temperature screen",
                    holding_time_min="10",
                    reducing_gas="H2",
                    gas_composition_summary="H2; flow and pressure not reported",
                ),
                stage(
                    3,
                    "cnt_growth",
                    (
                        "After pretreatment, CNT growth was performed in a "
                        "CH4/H2 mixture at 850 C. Growth time, gas flows and "
                        "pressure were not reported in the chapter."
                    ),
                    temperature_setpoint_C="850",
                    temperature_program_summary="isothermal CNT growth at 850 C",
                    carbon_source="CH4",
                    reducing_gas="H2",
                    gas_composition_summary="CH4/H2; composition and flows not reported",
                ),
            ],
            "product": common_product(
                metric="qualitative_CNT_area_density",
                yield_original="highest CNT area density after 1000 C pretreatment",
                summary=(
                    "The pretreatment screen produced predominantly SWNTs; "
                    "the highest CNT area density occurred after 1000 C H2 "
                    "pretreatment. Raman showed an RBM feature."
                ),
                cnt_type="predominantly SWNT",
                morphology="substrate-supported CNT network",
                characterization="SEM; AFM; Raman",
                raman_summary=(
                    "RBM feature confirmed predominantly SWNTs; Raman "
                    "excitation wavelength was 632.8 nm."
                ),
                laser="632.8",
            ),
            "product_evidence": (
                "Au samples pretreated from 850 to 1050 C were grown at "
                "850 C in CH4/H2. The highest CNT area density followed "
                "1000 C pretreatment. Raman excitation was 632.8 nm and "
                "the RBM feature indicated predominantly SWNTs."
            ),
            "route": "Au nanoparticle CVD screen",
        },
        {
            "code": "CU_SIO2_900C",
            "label": "Cu/SiO2 catalyst, 900 C CH4/H2 growth",
            "summary": (
                "Cu nanoparticles made from 1 mM Cu(NO3)2/isopropanol and "
                "decomposed in air at 400 C were H2 pretreated for 10 min "
                "at 900 C and used for CH4/H2 growth at 900 C."
            ),
            "confidence": "high",
            "span": "SPAN_0E3ACF66C5120005EF5F",
            "page": 6,
            "catalyst": {
                "catalyst_label": "Cu nanoparticles on SiO2",
                "active_metals": "Cu",
                "support_material": "SiO2",
                "promoter": "none reported",
                "metal_ratio_original": "not_reported",
                "metal_ratio_standardized": "not_reported",
                "precursor_summary": "1 mM Cu(NO3)2 in isopropanol",
                "preparation_method": "solution deposition and thermal decomposition in air",
                "preparation_modifier": "400 C decomposition; 900 C H2 pretreatment",
                "preparation_detail": (
                    "Mean particle size 1.5 +/- 0.4 nm and particle density "
                    "350 +/- 50 particles/um2 by AFM."
                ),
                "drying_condition": "not_reported",
                "calcination_condition": "air at 400 C",
                "reduction_condition": "H2 for 10 min at 900 C",
                "activation_condition": "H2 pretreatment",
                "post_preparation_condition": "CH4/H2 CNT growth at 900 C",
                "catalyst_particle_size_mean_nm": "",
                "catalyst_particle_size_range_nm": "",
                "catalyst_particle_size_qualifier": "1.5 +/- 0.4 nm mean +/- standard deviation",
                "phase_or_state_summary": "Cu nanoparticles from decomposed Cu nitrate",
                "dispersion_summary": "350 +/- 50 particles/um2",
                "deactivation_summary": "not_reported",
            },
            "stages": [
                stage(
                    1,
                    "catalyst_thermal_decomposition",
                    (
                        "Cu nanoparticles were formed by thermal decomposition "
                        "of Cu(NO3)2 in air at 400 C after deposition from a "
                        "1 mM isopropanol solution on SiO2."
                    ),
                    reactor_type="air thermal-treatment apparatus; not reported",
                    reactor_setup_summary="Cu(NO3)2 deposited on SiO2",
                    temperature_setpoint_C="400",
                    temperature_program_summary="thermal decomposition in air at 400 C",
                    cofeed_or_reactive_gas="air",
                    gas_composition_summary="air",
                ),
                stage(
                    2,
                    "hydrogen_pretreatment",
                    "The Cu catalyst was pretreated in H2 for 10 min at 900 C.",
                    temperature_setpoint_C="900",
                    temperature_program_summary="H2 pretreatment at 900 C",
                    holding_time_min="10",
                    reducing_gas="H2",
                    gas_composition_summary="H2; flow and pressure not reported",
                ),
                stage(
                    3,
                    "cnt_growth",
                    (
                        "CNT growth followed at the same 900 C temperature in "
                        "a CH4/H2 mixture. Duration, flows and pressure were not reported."
                    ),
                    temperature_setpoint_C="900",
                    temperature_program_summary="CH4/H2 CNT growth at 900 C",
                    carbon_source="CH4",
                    reducing_gas="H2",
                    gas_composition_summary="CH4/H2; composition and flows not reported",
                ),
            ],
            "product": common_product(
                metric="qualitative_CNT_quality",
                yield_original="predominantly high-quality SWNTs",
                summary=(
                    "Raman spectroscopy identified the carbon products as "
                    "predominantly high-quality SWNTs. A metallic-SWNT "
                    "preference reported elsewhere was not detected in this "
                    "experiment, but only one laser line and a small sample were used."
                ),
                cnt_type="predominantly SWNT",
                morphology="substrate-supported CNT network",
                characterization="SEM; AFM; Raman",
                raman_summary="Raman identified predominantly high-quality SWNTs.",
            ),
            "product_evidence": (
                "Cu nanoparticles had mean size 1.5 +/- 0.4 nm and density "
                "350 +/- 50 particles/um2. After 10 min H2 pretreatment at "
                "900 C and CH4/H2 growth at 900 C, Raman showed predominantly "
                "high-quality SWNTs."
            ),
            "route": "Cu nanoparticle CVD",
        },
        {
            "code": "SIGE_ISLANDS_C_IMPLANTED",
            "label": "C-implanted Si0.7Ge0.3 islands",
            "summary": (
                "A 50 nm Si0.7Ge0.3 layer on Si(001) formed 20-50 nm-high "
                "islands, received a 30 keV, 3 x 10^16 cm-2 C implant, "
                "wet preparation, 900 C Ar/H2 pretreatment and 850 C CH4/H2 growth."
            ),
            "confidence": "high",
            "span": "SPAN_020702E3AB3F65A990B6",
            "page": 8,
            "catalyst": {
                "catalyst_label": "Ge-rich clusters formed from C-implanted SiGe islands",
                "active_metals": "Ge-rich semiconductor clusters",
                "support_material": "Si0.7Ge0.3 islands on Si(001)",
                "promoter": "carbon implantation",
                "metal_ratio_original": "Si0.7Ge0.3",
                "metal_ratio_standardized": "Si:Ge=0.7:0.3",
                "precursor_summary": "50 nm Si0.7Ge0.3 CVD layer",
                "preparation_method": "CVD island formation, C implantation, wet oxidation and reduction",
                "preparation_modifier": "30 keV C implant at 3 x 10^16 cm-2",
                "preparation_detail": (
                    "Islands were 20-50 nm high; buffered HF removed native "
                    "oxide, 30% H2O2 chemically oxidized the surface, and "
                    "900 C Ar/H2 pretreatment formed nanoscale Ge-rich clusters."
                ),
                "drying_condition": "not_reported",
                "calcination_condition": "not_applicable",
                "reduction_condition": "Ar/H2 for 10 min at 900 C",
                "activation_condition": "chemical oxidation followed by reducing anneal",
                "post_preparation_condition": "CH4/H2 CNT growth at 850 C",
                "catalyst_particle_size_mean_nm": "",
                "catalyst_particle_size_range_nm": "",
                "catalyst_particle_size_qualifier": (
                    "Parent SiGe islands were 20-50 nm high; active Ge-rich "
                    "cluster dimensions were not quantified."
                ),
                "phase_or_state_summary": (
                    "Wet SiGe oxide was reduced preferentially at Ge-O bonds, "
                    "nucleating nanoscale Ge-rich clusters."
                ),
                "dispersion_summary": "not_quantified",
                "deactivation_summary": "not_reported",
            },
            "stages": [
                stage(
                    1,
                    "sige_island_formation",
                    (
                        "A 50 nm Si0.7Ge0.3 layer was deposited by CVD on "
                        "Si(001) after a thin Si buffer; stress produced islands "
                        "20-50 nm high."
                    ),
                    reactor_setup_summary="Si0.7Ge0.3 CVD layer on Si(001)",
                    process_note="Layer thickness 50 nm; island height 20-50 nm.",
                ),
                stage(
                    2,
                    "carbon_ion_implantation",
                    (
                        "The SiGe islands were implanted with carbon ions at "
                        "30 keV and dose 3 x 10^16 cm-2."
                    ),
                    reactor_type="ion implanter",
                    cofeed_or_reactive_gas="C ions",
                    process_note="C implant energy 30 keV; dose 3 x 10^16 cm-2.",
                ),
                stage(
                    3,
                    "wet_surface_preparation",
                    (
                        "Buffered HF removed native oxide, followed by chemical "
                        "oxidation in 30% H2O2 at room temperature."
                    ),
                    reactor_type="wet-chemical treatment",
                    temperature_setpoint_C="room_temperature",
                    cofeed_or_reactive_gas="30% H2O2 aqueous solution after buffered HF",
                    cofeed_flow_original="30 wt.% H2O2 solution",
                    gas_composition_summary="not_applicable_wet_treatment",
                ),
                stage(
                    4,
                    "hydrogen_pretreatment",
                    "Pretreatment used Ar/H2 for 10 min at 900 C.",
                    temperature_setpoint_C="900",
                    temperature_program_summary="reducing pretreatment at 900 C",
                    holding_time_min="10",
                    reducing_gas="H2",
                    inert_gas="Ar",
                    gas_composition_summary="Ar/H2; composition and flows not reported",
                ),
                stage(
                    5,
                    "cnt_growth",
                    (
                        "CNT growth used CH4/H2 at 850 C; duration, gas flows "
                        "and pressure were not reported."
                    ),
                    temperature_setpoint_C="850",
                    temperature_program_summary="CH4/H2 CNT growth at 850 C",
                    carbon_source="CH4",
                    reducing_gas="H2",
                    gas_composition_summary="CH4/H2; composition and flows not reported",
                ),
                stage(
                    6,
                    "post_growth_hf_vapor_etch",
                    (
                        "A post-growth HF vapour etch removed approximately "
                        "20 nm-diameter, 1 um-long SiOx nanowires while CNTs remained."
                    ),
                    reactor_type="HF vapour etch apparatus",
                    cofeed_or_reactive_gas="HF vapour",
                    process_note="Selective removal of SiOx nanowire byproduct.",
                ),
            ],
            "product": common_product(
                metric="CNT_length_and_identity",
                yield_original="approximately 5 um-long, less-than-10 nm fibres",
                summary=(
                    "The growth step produced straight thin fibres less than "
                    "10 nm in diameter and approximately 5 um long; Raman "
                    "confirmed SWNTs and no D band near 1350 cm-1 was detected. "
                    "Pretreatment also formed approximately 20 nm-diameter, "
                    "1 um-long SiOx nanowires removable by HF vapour."
                ),
                cnt_type="SWNT",
                morphology="straight thin fibres",
                characterization="SEM; TEM; Raman; photoluminescence",
                raman_summary="RBM and G band present; D band near 1350 cm-1 absent.",
                post_treatment="HF vapour etch removed SiOx nanowires",
                purification="HF vapour etch; duration not reported",
            ),
            "product_evidence": (
                "C-implanted SiGe islands produced straight fibres less than "
                "10 nm in diameter and approximately 5 um long. Raman RBM/G "
                "features confirmed SWNTs, and the D band near 1350 cm-1 "
                "was absent. HF vapour removed 20 nm-diameter, 1 um-long "
                "SiOx nanowires while CNTs remained."
            ),
            "route": "C-implanted SiGe semiconductor-catalyst CVD",
        },
        {
            "code": "GE_SK_DOTS_C_IMPLANTED",
            "label": "C-implanted Ge Stranski-Krastanow dots",
            "summary": (
                "Ge Stranski-Krastanow dots were C implanted, HF cleaned, "
                "oxidized with 30% H2O2, pretreated in Ar/H2 for 10 min at "
                "900 C and used for CH4/H2 growth at 850 C."
            ),
            "confidence": "high",
            "span": "SPAN_2341EC296CCDFA163332",
            "page": 10,
            "catalyst": {
                "catalyst_label": "Ge-rich clusters from C-implanted Ge SK dots",
                "active_metals": "Ge semiconductor clusters",
                "support_material": "Ge Stranski-Krastanow dots on thin Si buffer/Si",
                "promoter": "carbon implantation",
                "metal_ratio_original": "not_reported",
                "metal_ratio_standardized": "not_reported",
                "precursor_summary": "CVD-deposited Ge Stranski-Krastanow dots",
                "preparation_method": "CVD dot formation, C implantation, wet oxidation and reduction",
                "preparation_modifier": "30 keV C implant at 3 x 10^16 cm-2",
                "preparation_detail": (
                    "Parent dots were cones 20-250 nm in diameter and 10-25 nm "
                    "high; buffered HF, 30% H2O2 and 900 C Ar/H2 treatment "
                    "generated Ge-enriched clusters."
                ),
                "drying_condition": "not_reported",
                "calcination_condition": "not_applicable",
                "reduction_condition": "Ar/H2 for 10 min at 900 C",
                "activation_condition": "chemical oxidation followed by reducing anneal",
                "post_preparation_condition": "CH4/H2 CNT growth at 850 C",
                "catalyst_particle_size_mean_nm": "",
                "catalyst_particle_size_range_nm": "",
                "catalyst_particle_size_qualifier": (
                    "Parent dots 20-250 nm diameter and 10-25 nm height; "
                    "active cluster size not quantified."
                ),
                "phase_or_state_summary": "Ge-enriched clusters within non-reducible matrix",
                "dispersion_summary": "not_quantified",
                "deactivation_summary": "not_reported",
            },
            "stages": [
                stage(
                    1,
                    "ge_dot_cvd_formation",
                    (
                        "CVD deposition of Ge on a thin Si buffer formed "
                        "conical Stranski-Krastanow dots 20-250 nm in diameter "
                        "and 10-25 nm high."
                    ),
                    reactor_setup_summary="Ge CVD deposition on thin Si buffer layer",
                ),
                stage(
                    2,
                    "carbon_ion_implantation",
                    (
                        "Ge dots were implanted with C ions at 30 keV and "
                        "dose 3 x 10^16 cm-2."
                    ),
                    reactor_type="ion implanter",
                    cofeed_or_reactive_gas="C ions",
                    process_note="C implant energy 30 keV; dose 3 x 10^16 cm-2.",
                ),
                stage(
                    3,
                    "wet_surface_preparation",
                    (
                        "Buffered HF removed native oxide, followed by chemical "
                        "oxidation in 30% H2O2 at room temperature."
                    ),
                    reactor_type="wet-chemical treatment",
                    temperature_setpoint_C="room_temperature",
                    cofeed_or_reactive_gas="30% H2O2 aqueous solution after buffered HF",
                    cofeed_flow_original="30 wt.% H2O2 solution",
                    gas_composition_summary="not_applicable_wet_treatment",
                ),
                stage(
                    4,
                    "hydrogen_pretreatment",
                    "Pretreatment used Ar/H2 for 10 min at 900 C.",
                    temperature_setpoint_C="900",
                    temperature_program_summary="reducing pretreatment at 900 C",
                    holding_time_min="10",
                    reducing_gas="H2",
                    inert_gas="Ar",
                    gas_composition_summary="Ar/H2; composition and flows not reported",
                ),
                stage(
                    5,
                    "cnt_growth",
                    (
                        "CNT growth used CH4/H2 at 850 C; duration, gas flows "
                        "and pressure were not reported."
                    ),
                    temperature_setpoint_C="850",
                    temperature_program_summary="CH4/H2 CNT growth at 850 C",
                    carbon_source="CH4",
                    reducing_gas="H2",
                    gas_composition_summary="CH4/H2; composition and flows not reported",
                ),
            ],
            "product": common_product(
                metric="CNT_diameter_and_identity",
                yield_original="SWNT diameter range 1.6-2.1 nm",
                summary=(
                    "TEM showed a SWNT bundle. Raman RBM and tangential G "
                    "features indicated SWNT diameters of 1.6-2.1 nm; the "
                    "D band was not detected, indicating high quality."
                ),
                cnt_type="SWNT",
                morphology="SWNT bundle",
                characterization="TEM; Raman",
                raman_summary="RBM and G band present; D band absent.",
                outer_range="1.6-2.1",
            ),
            "product_evidence": (
                "C-implanted Ge Stranski-Krastanow dots yielded a SWNT "
                "bundle. Raman RBM/G features indicated CNT diameters "
                "1.6-2.1 nm, and the disorder-induced D band was absent."
            ),
            "route": "C-implanted Ge-dot semiconductor-catalyst CVD",
        },
        {
            "code": "GE_ION_IMPLANT_NO_C",
            "label": "Ge ion-implanted nanoparticles without C implant",
            "summary": (
                "Ge nanoparticles made by 20 keV, 5 x 10^15 cm-2 implantation "
                "into 30 nm SiO2, 600 C N2 anneal for 40 min and HF exposure "
                "were used for CNT growth without a subsequent C implant."
            ),
            "confidence": "medium",
            "span": "SPAN_7EE984BC50F9FBD95347",
            "page": 11,
            "catalyst": {
                "catalyst_label": "Ge nanoparticles fabricated by ion implantation",
                "active_metals": "Ge semiconductor nanoparticles",
                "support_material": "30 nm thermally oxidized SiO2 layer",
                "promoter": "none",
                "metal_ratio_original": "not_reported",
                "metal_ratio_standardized": "not_reported",
                "precursor_summary": "20 keV Ge ion implant at 5 x 10^15 cm-2",
                "preparation_method": "Ge implantation, N2 anneal and HF vapour etch",
                "preparation_modifier": "no subsequent C implant",
                "preparation_detail": (
                    "Annealed at 600 C for 40 min in N2. Exposed particles "
                    "had density 460 +/- 30 particles/um2 and modal height 1.8 nm."
                ),
                "drying_condition": "not_reported",
                "calcination_condition": "600 C for 40 min in N2",
                "reduction_condition": "not_reported",
                "activation_condition": "HF vapour exposure of implanted Ge nanocrystals",
                "post_preparation_condition": "CNT growth; exact recipe not restated",
                "catalyst_particle_size_mean_nm": "",
                "catalyst_particle_size_range_nm": "",
                "catalyst_particle_size_qualifier": "modal height 1.8 nm",
                "phase_or_state_summary": "implanted/annealed Ge nanocrystals",
                "dispersion_summary": "460 +/- 30 particles/um2",
                "deactivation_summary": (
                    "Particle density decreased strongly as pretreatment "
                    "temperature increased; exact series values were not reported."
                ),
            },
            "stages": [
                stage(
                    1,
                    "ge_ion_implantation",
                    (
                        "Ge was implanted at 20 keV and dose 5 x 10^15 cm-2 "
                        "into a 30 nm thermally oxidized SiO2 layer."
                    ),
                    reactor_type="ion implanter",
                    cofeed_or_reactive_gas="Ge ions",
                    process_note=("Ge implant 20 keV, 5 x 10^15 cm-2 into 30 nm SiO2."),
                ),
                stage(
                    2,
                    "nanocrystal_annealing",
                    "The implanted layer was annealed at 600 C for 40 min in N2.",
                    temperature_setpoint_C="600",
                    temperature_program_summary="Ge nanocrystal anneal at 600 C",
                    holding_time_min="40",
                    inert_gas="N2",
                    gas_composition_summary="N2; flow and pressure not reported",
                ),
                stage(
                    3,
                    "hf_vapor_etch",
                    "HF vapour removed SiO2 and exposed the Ge nanoparticles.",
                    reactor_type="HF vapour etch apparatus",
                    cofeed_or_reactive_gas="HF vapour",
                ),
                stage(
                    4,
                    "cnt_growth_not_restanted",
                    (
                        "The chapter reports CNT growth from the exposed Ge "
                        "nanoparticles but does not restate the exact growth "
                        "temperature, time, gas composition, flow or pressure."
                    ),
                    reactor_type="CNT CVD reactor; configuration not reported",
                    process_note="Exact CNT growth recipe not restated in this chapter section.",
                ),
            ],
            "product": common_product(
                metric="qualitative_CNT_area_density",
                yield_original="good CNT area density; no numeric density reported",
                summary=(
                    "SEM showed a good CNT area density. Raman RBM confirmed "
                    "SWNTs, while a small D band near 1320 cm-1 indicated "
                    "some nanotube disorder."
                ),
                cnt_type="SWNT",
                morphology="substrate-supported CNT network",
                characterization="AFM; SEM; Raman",
                raman_summary="RBM present; small D band near 1320 cm-1.",
            ),
            "product_evidence": (
                "Without C implantation, Ge nanoparticles had density "
                "460 +/- 30 particles/um2 and modal height 1.8 nm. CNT "
                "growth gave good area density; Raman RBM showed SWNTs, "
                "with a small D band near 1320 cm-1."
            ),
            "route": "Ge-ion-implant semiconductor-catalyst CVD",
        },
        {
            "code": "GE_ION_IMPLANT_WITH_C",
            "label": "Ge ion-implanted nanoparticles with C implant",
            "summary": (
                "Ge nanoparticles made by implantation/annealing/HF were "
                "subsequently implanted with C at 30 keV and 3 x 10^16 cm-2 "
                "before CNT growth."
            ),
            "confidence": "medium",
            "span": "SPAN_F3199BAEE797C8922555",
            "page": 12,
            "catalyst": {
                "catalyst_label": "C-implanted Ge nanoparticles fabricated by ion implantation",
                "active_metals": "Ge-C semiconductor nanoparticles",
                "support_material": "30 nm thermally oxidized SiO2 layer",
                "promoter": "C implantation",
                "metal_ratio_original": "not_reported",
                "metal_ratio_standardized": "not_reported",
                "precursor_summary": (
                    "20 keV Ge implant at 5 x 10^15 cm-2 plus 30 keV C "
                    "implant at 3 x 10^16 cm-2"
                ),
                "preparation_method": "Ge implantation, N2 anneal, HF etch and C implantation",
                "preparation_modifier": "C implantation stabilized the pretreatment window",
                "preparation_detail": (
                    "After C implantation, particle density was 70 +/- 18 "
                    "particles/um2 and modal height 0.7 nm, with a narrower distribution."
                ),
                "drying_condition": "not_reported",
                "calcination_condition": "600 C for 40 min in N2 before C implantation",
                "reduction_condition": "not_reported",
                "activation_condition": "C implantation after Ge nanocrystal exposure",
                "post_preparation_condition": "CNT growth; exact recipe not restated",
                "catalyst_particle_size_mean_nm": "",
                "catalyst_particle_size_range_nm": "",
                "catalyst_particle_size_qualifier": "modal height 0.7 nm after C implantation",
                "phase_or_state_summary": "possible Ge1-yCy alloy; not directly confirmed",
                "dispersion_summary": "70 +/- 18 particles/um2 after C implantation",
                "deactivation_summary": (
                    "Only a small particle-density decrease occurred with "
                    "increasing pretreatment temperature; exact series values were unreported."
                ),
            },
            "stages": [
                stage(
                    1,
                    "ge_ion_implantation",
                    (
                        "Ge was implanted at 20 keV and dose 5 x 10^15 cm-2 "
                        "into a 30 nm thermally oxidized SiO2 layer."
                    ),
                    reactor_type="ion implanter",
                    cofeed_or_reactive_gas="Ge ions",
                    process_note=("Ge implant 20 keV, 5 x 10^15 cm-2 into 30 nm SiO2."),
                ),
                stage(
                    2,
                    "nanocrystal_annealing",
                    "The implanted layer was annealed at 600 C for 40 min in N2.",
                    temperature_setpoint_C="600",
                    temperature_program_summary="Ge nanocrystal anneal at 600 C",
                    holding_time_min="40",
                    inert_gas="N2",
                    gas_composition_summary="N2; flow and pressure not reported",
                ),
                stage(
                    3,
                    "hf_vapor_etch",
                    "HF vapour removed SiO2 and exposed the Ge nanoparticles.",
                    reactor_type="HF vapour etch apparatus",
                    cofeed_or_reactive_gas="HF vapour",
                ),
                stage(
                    4,
                    "carbon_ion_implantation",
                    (
                        "Selected samples received a C implant at 30 keV and "
                        "dose 3 x 10^16 cm-2, reducing particle density to "
                        "70 +/- 18 particles/um2 and modal height to 0.7 nm."
                    ),
                    reactor_type="ion implanter",
                    cofeed_or_reactive_gas="C ions",
                    process_note="C implant energy 30 keV; dose 3 x 10^16 cm-2.",
                ),
                stage(
                    5,
                    "cnt_growth_not_restanted",
                    (
                        "The chapter reports CNT growth from C-implanted Ge "
                        "nanoparticles but does not restate the exact growth "
                        "temperature, time, gas composition, flow or pressure."
                    ),
                    reactor_type="CNT CVD reactor; configuration not reported",
                    process_note="Exact CNT growth recipe not restated in this chapter section.",
                ),
            ],
            "product": common_product(
                metric="qualitative_CNT_area_density",
                yield_original="good CNT area density; wider successful temperature window",
                summary=(
                    "At the optimum condition, C implantation gave no "
                    "statistically significant CNT area-density benefit, but "
                    "successful growth occurred over a wider temperature range. "
                    "Raman RBM confirmed SWNTs and no D band was observed."
                ),
                cnt_type="high-quality SWNT",
                morphology="substrate-supported CNT network",
                characterization="AFM; SEM; Raman",
                raman_summary="RBM present; D band absent after C implantation.",
            ),
            "product_evidence": (
                "C implantation reduced Ge particle density to 70 +/- 18 "
                "particles/um2 and modal height to 0.7 nm. CNT area density "
                "at the optimum was not statistically better than without C, "
                "but the successful temperature window was wider. Raman RBM "
                "showed SWNTs and no D band was observed."
            ),
            "route": "C-implanted Ge-ion-implant semiconductor-catalyst CVD",
        },
        {
            "code": "COLLOIDAL_GE_SIO2_PRETREAT_SCREEN",
            "label": "Colloidal Ge/SiO2 pretreatment screen",
            "summary": (
                "Inverse-micelle Ge nanoparticles spin coated from a 1 mM "
                "solution onto SiO2 were O2-plasma cleaned, H2 pretreated for "
                "10 min over 850-1050 C and used for CH4/H2 growth at 850 C."
            ),
            "confidence": "medium",
            "span": "SPAN_714A05B971B215DEAA6F",
            "page": 13,
            "catalyst": {
                "catalyst_label": "colloidal Ge nanoparticles on SiO2",
                "active_metals": "Ge semiconductor nanoparticles",
                "support_material": "SiO2",
                "promoter": "organic cap stabilized particles during furnace ramp",
                "metal_ratio_original": "not_reported",
                "metal_ratio_standardized": "not_reported",
                "precursor_summary": "Ge[N(SiCH3)2]2 inverse-micelle-derived colloid",
                "preparation_method": "hot injection, precipitation, redispersion and spin coating",
                "preparation_modifier": "100 W O2 plasma for 30 min",
                "preparation_detail": (
                    "50 mg precursor in 7 mL trioctylamine was injected at "
                    "340 C into 1 g molten HDA, then processed with toluene, "
                    "methanol and trioctylamine. The deposited particles were "
                    "1.5 +/- 0.4 nm with density 430 +/- 60 particles/um2."
                ),
                "drying_condition": "not_reported",
                "calcination_condition": "100 W O2 plasma for 30 min",
                "reduction_condition": "H2 for 10 min at 850-1050 C",
                "activation_condition": "O2 plasma clean followed by H2 pretreatment",
                "post_preparation_condition": "CH4/H2 CNT growth at 850 C",
                "catalyst_particle_size_mean_nm": "",
                "catalyst_particle_size_range_nm": "",
                "catalyst_particle_size_qualifier": "mean 1.5 +/- 0.4 nm",
                "phase_or_state_summary": (
                    "Colloidal Ge nanocrystals with organic cap removed/reduced "
                    "during plasma and high-temperature treatment."
                ),
                "dispersion_summary": "430 +/- 60 particles/um2 after spin coating",
                "deactivation_summary": (
                    "No statistically significant particle-density loss with "
                    "increasing pretreatment temperature; particle size rose slightly."
                ),
            },
            "stages": [
                stage(
                    1,
                    "colloidal_ge_synthesis",
                    (
                        "50 mg Ge[N(SiCH3)2]2 precursor in 7 mL "
                        "trioctylamine was injected at 340 C into 1 g molten "
                        "hexadecylamine. Residue was redissolved in toluene, "
                        "reprecipitated with methanol and suspended in trioctylamine."
                    ),
                    reactor_type="hot-injection colloid synthesis vessel",
                    catalyst_loading_mass_g="0.05",
                    temperature_setpoint_C="340",
                    temperature_program_summary="hot injection into molten HDA at 340 C",
                    cofeed_or_reactive_gas="trioctylamine; hexadecylamine; toluene; methanol",
                ),
                stage(
                    2,
                    "spin_coating",
                    (
                        "Colloidal Ge nanoparticles were deposited on SiO2 "
                        "by spin coating a 1 mM solution. The layer had mean "
                        "particle size 1.5 +/- 0.4 nm and density "
                        "430 +/- 60 particles/um2."
                    ),
                    reactor_type="spin coater",
                    reactor_setup_summary="SiO2 support",
                    cofeed_or_reactive_gas="1 mM colloidal Ge solution",
                ),
                stage(
                    3,
                    "oxygen_plasma_clean",
                    (
                        "The spin-coated sample was cleaned in a 100 W O2 "
                        "plasma for 30 min to remove organic residue."
                    ),
                    reactor_type="O2 plasma cleaner",
                    holding_time_min="30",
                    cofeed_or_reactive_gas="O2 plasma",
                    process_note="O2 plasma power 100 W; duration 30 min.",
                ),
                stage(
                    4,
                    "hydrogen_pretreatment_screen",
                    (
                        "Samples were H2 pretreated for 10 min at temperatures "
                        "from 850 to 1050 C; the highest CNT area density followed "
                        "900 C pretreatment."
                    ),
                    temperature_setpoint_C="850-1050",
                    temperature_range_reported_C="850-1050",
                    temperature_program_summary="H2 pretreatment-temperature screen",
                    holding_time_min="10",
                    reducing_gas="H2",
                    gas_composition_summary="H2; flow and pressure not reported",
                ),
                stage(
                    5,
                    "cnt_growth",
                    (
                        "CNT growth used CH4/H2 at 850 C. Duration, gas "
                        "composition, flows and pressure were not reported."
                    ),
                    temperature_setpoint_C="850",
                    temperature_program_summary="CH4/H2 CNT growth at 850 C",
                    carbon_source="CH4",
                    reducing_gas="H2",
                    gas_composition_summary="CH4/H2; composition and flows not reported",
                ),
            ],
            "product": common_product(
                metric="qualitative_CNT_area_density",
                yield_original="highest CNT area density after 900 C pretreatment",
                summary=(
                    "The highest CNT area density on SiO2 followed 900 C "
                    "pretreatment. CNT area density changed little from "
                    "900 to 1000 C, and Raman showed predominantly high-quality SWNTs."
                ),
                cnt_type="predominantly high-quality SWNT",
                morphology="substrate-supported CNT network",
                characterization="AFM; SEM; Raman",
                raman_summary=(
                    "Raman showed an RBM near 138 cm-1 in the representative "
                    "spectrum and predominantly high-quality SWNTs."
                ),
            ),
            "product_evidence": (
                "Colloidal Ge particles were 1.5 +/- 0.4 nm with density "
                "430 +/- 60 particles/um2. H2 pretreatment ranged 850-1050 C; "
                "the highest CNT area density occurred at 900 C and changed "
                "little from 900 to 1000 C. CH4/H2 growth was at 850 C. "
                "Raman showed predominantly high-quality SWNTs and a "
                "representative RBM near 138 cm-1."
            ),
            "route": "colloidal Ge semiconductor-catalyst CVD screen",
        },
        {
            "code": "COLLOIDAL_GE_SAPPHIRE_900C",
            "label": "Colloidal Ge on sapphire, 900 C pretreatment",
            "summary": (
                "Colloidal Ge nanoparticles on sapphire were O2-plasma "
                "cleaned, H2 pretreated for 10 min at 900 C and used for "
                "CH4/H2 CNT growth at 850 C."
            ),
            "confidence": "high",
            "span": "SPAN_8C04D4CA17626275E967",
            "page": 14,
            "catalyst": {
                "catalyst_label": "colloidal Ge nanoparticles on sapphire",
                "active_metals": "Ge semiconductor nanoparticles",
                "support_material": "sapphire (Al2O3)",
                "promoter": "Al2O3 support interface for graphite formation",
                "metal_ratio_original": "not_reported",
                "metal_ratio_standardized": "not_reported",
                "precursor_summary": "Ge[N(SiCH3)2]2 inverse-micelle-derived colloid",
                "preparation_method": "hot injection, precipitation, redispersion and spin coating",
                "preparation_modifier": "100 W O2 plasma for 30 min",
                "preparation_detail": (
                    "The same colloidal synthesis produced mean 1.5 +/- 0.4 nm "
                    "particles and 430 +/- 60 particles/um2 on the characterized "
                    "spin-coated layer; support-specific particle statistics "
                    "for sapphire were not separately reported."
                ),
                "drying_condition": "not_reported",
                "calcination_condition": "100 W O2 plasma for 30 min",
                "reduction_condition": "H2 for 10 min at 900 C",
                "activation_condition": "O2 plasma clean followed by H2 pretreatment",
                "post_preparation_condition": "CH4/H2 CNT growth at 850 C",
                "catalyst_particle_size_mean_nm": "",
                "catalyst_particle_size_range_nm": "",
                "catalyst_particle_size_qualifier": (
                    "Colloid mean 1.5 +/- 0.4 nm; sapphire-specific size not separated."
                ),
                "phase_or_state_summary": "colloidal Ge nanocrystals on Al2O3",
                "dispersion_summary": (
                    "Colloid layer density 430 +/- 60 particles/um2; "
                    "sapphire-specific value not separately reported."
                ),
                "deactivation_summary": "not_reported",
            },
            "stages": [
                stage(
                    1,
                    "colloidal_ge_synthesis",
                    (
                        "50 mg Ge[N(SiCH3)2]2 precursor in 7 mL "
                        "trioctylamine was injected at 340 C into 1 g molten "
                        "hexadecylamine, followed by toluene/methanol workup."
                    ),
                    reactor_type="hot-injection colloid synthesis vessel",
                    catalyst_loading_mass_g="0.05",
                    temperature_setpoint_C="340",
                    temperature_program_summary="hot injection into molten HDA at 340 C",
                    cofeed_or_reactive_gas="trioctylamine; hexadecylamine; toluene; methanol",
                ),
                stage(
                    2,
                    "spin_coating",
                    (
                        "Colloidal Ge nanoparticles were deposited on sapphire "
                        "by spin coating a 1 mM solution; the chapter does not "
                        "report separate sapphire particle statistics."
                    ),
                    reactor_type="spin coater",
                    reactor_setup_summary="sapphire (Al2O3) support",
                    cofeed_or_reactive_gas="1 mM colloidal Ge solution",
                ),
                stage(
                    3,
                    "oxygen_plasma_clean",
                    (
                        "The spin-coated sample was cleaned in a 100 W O2 "
                        "plasma for 30 min."
                    ),
                    reactor_type="O2 plasma cleaner",
                    holding_time_min="30",
                    cofeed_or_reactive_gas="O2 plasma",
                    process_note="O2 plasma power 100 W; duration 30 min.",
                ),
                stage(
                    4,
                    "hydrogen_pretreatment",
                    "The sapphire-supported sample was H2 pretreated for 10 min at 900 C.",
                    temperature_setpoint_C="900",
                    temperature_program_summary="H2 pretreatment at 900 C",
                    holding_time_min="10",
                    reducing_gas="H2",
                    gas_composition_summary="H2; flow and pressure not reported",
                ),
                stage(
                    5,
                    "cnt_growth",
                    (
                        "CNT growth used CH4/H2 at 850 C. Duration, gas "
                        "composition, flows and pressure were not reported."
                    ),
                    temperature_setpoint_C="850",
                    temperature_program_summary="CH4/H2 CNT growth at 850 C",
                    carbon_source="CH4",
                    reducing_gas="H2",
                    gas_composition_summary="CH4/H2; composition and flows not reported",
                ),
            ],
            "product": common_product(
                metric="qualitative_CNT_area_density",
                yield_original="slightly higher uniformity and CNT area density than SiO2",
                summary=(
                    "At the 900 C pretreatment/850 C growth condition, "
                    "sapphire gave slightly higher CNT uniformity and area "
                    "density than SiO2. The products were predominantly "
                    "high-quality SWNTs."
                ),
                cnt_type="predominantly high-quality SWNT",
                morphology="more uniform substrate-supported CNT network",
                characterization="SEM; Raman",
                raman_summary="Representative colloidal-Ge Raman showed RBM and SWNT identity.",
            ),
            "product_evidence": (
                "Colloidal Ge on sapphire was pretreated in H2 for 10 min "
                "at 900 C and grown in CH4/H2 at 850 C. Sapphire showed "
                "slightly higher CNT uniformity and area density than SiO2; "
                "the products were predominantly high-quality SWNTs."
            ),
            "route": "colloidal Ge/sapphire semiconductor-catalyst CVD",
        },
    ]


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
    confidence: str = "high",
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
            "notes": "Transcribed after visual inspection of the local open-access PDF.",
        }
    )
    tables["evidence_index"].append(item)


def build(
    metadata: dict[str, Any],
    store: EvidenceStore,
) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    specs = run_specs()
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "Nine author-presented experimental datasets from Figures 1-9: "
                "one non-CVD structural-reorganization control, Au and Cu "
                "nanoparticle CVD, SiGe and Ge-dot routes, paired Ge-ion-implant "
                "conditions, and colloidal-Ge experiments on SiO2 and sapphire."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_fulltext_pdf"
    master["notes"] += (
        " The document is a review-style book chapter that re-presents several "
        "experiments from the authors' earlier publications. External literature "
        "examples were not converted into primary-source run records."
    )

    for spec in specs:
        run_id = f"{SOURCE_ID}_{spec['code']}"
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                spec["code"],
                spec["label"],
                spec["summary"],
                spec["confidence"],
            )
        )
        tables["catalyst_system"].append(catalyst_row(run_id, **spec["catalyst"]))

        for process in spec["stages"]:
            values = {
                key: value
                for key, value in process.items()
                if key not in {"order", "stage_type", "evidence"}
            }
            tables["reactor_process_gas"].append(
                process_row(
                    run_id,
                    process["order"],
                    process["stage_type"],
                    **values,
                )
            )

        tables["yield_quality"].append(yield_row(run_id, **spec["product"]))
        tables["cost_scale_review"].append(common_cost(run_id, spec["route"]))

        add_pdf_evidence(
            tables,
            store,
            run_id,
            "RUN",
            "source_run",
            run_id,
            "record_level",
            spec["span"],
            spec["page"],
            spec["summary"],
            "Experimental run identity and condition grouping.",
            confidence=spec["confidence"],
            value_status="reported_or_grouped_as_stated",
        )
        catalyst_text = (
            spec["summary"]
            + " "
            + spec["catalyst"]["preparation_detail"]
            + " "
            + spec["catalyst"]["catalyst_particle_size_qualifier"]
            + " "
            + spec["catalyst"]["dispersion_summary"]
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "CATALYST",
            "catalyst_system",
            f"{run_id}_CAT",
            "record_level",
            spec["span"],
            spec["page"],
            catalyst_text,
            "Catalyst identity, preparation, morphology and support.",
            confidence=spec["confidence"],
        )
        for process in spec["stages"]:
            add_pdf_evidence(
                tables,
                store,
                run_id,
                f"PROCESS_{process['order']}",
                "reactor_process_gas",
                f"{run_id}_S{process['order']:02d}",
                "record_level",
                spec["span"],
                spec["page"],
                process["evidence"],
                f"Process stage {process['order']} support.",
                confidence=spec["confidence"],
            )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "PRODUCT",
            "yield_quality",
            f"{run_id}_PROD",
            "record_level",
            spec["span"],
            spec["page"],
            spec["product_evidence"],
            "CNT identity, dimensions, morphology and Raman quality.",
            confidence=spec["confidence"],
            value_status="reported_qualitative_or_dimensional",
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            "record_level",
            spec["span"],
            spec["page"],
            (
                spec["summary"]
                + " This was a laboratory substrate experiment; no batch mass, "
                "throughput, energy intensity, monetary cost, catalyst reuse or "
                "large-area reproducibility data were reported."
            ),
            "Scale evidence and industrial data gaps.",
            confidence=spec["confidence"],
            value_status="review_assessment",
        )

    first = f"{SOURCE_ID}_{specs[0]['code']}"
    au = f"{SOURCE_ID}_AU_SIO2_PRETREAT_SCREEN_850_1050"
    ion = f"{SOURCE_ID}_GE_ION_IMPLANT_NO_C"
    colloid = f"{SOURCE_ID}_COLLOIDAL_GE_SIO2_PRETREAT_SCREEN"
    sapphire = f"{SOURCE_ID}_COLLOIDAL_GE_SAPPHIRE_900C"
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_REVIEW_ATTRIBUTION_001",
                SOURCE_ID,
                au,
                "secondary_source_attribution",
                "source_run",
                au,
                "run_summary",
                (
                    "This is a review-style book chapter that re-presents "
                    "experiments also described in the authors' earlier papers. "
                    "Values are attributed to this chapter's figures/text and "
                    "should not be treated as independent replicate publications."
                ),
                f"EVD_{au}_RUN",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_AU_GROUPING_001",
                SOURCE_ID,
                au,
                "grouped_condition_series",
                "source_run",
                au,
                "run_summary",
                (
                    "The Au pretreatment study is reported only as a range "
                    "850-1050 C, with explicit catalyst densities at 900 and "
                    "1000 C and the optimum at 1000 C. Unlisted intermediate "
                    "conditions were not invented as separate runs."
                ),
                f"EVD_{au}_PROCESS_2;EVD_{au}_PRODUCT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_COLLOID_GROUPING_001",
                SOURCE_ID,
                colloid,
                "grouped_condition_series",
                "source_run",
                colloid,
                "run_summary",
                (
                    "The colloidal-Ge pretreatment study is reported as "
                    "850-1050 C with an optimum at 900 C and little CNT-density "
                    "change from 900 to 1000 C; exact results for every "
                    "temperature were not tabulated."
                ),
                f"EVD_{colloid}_PROCESS_4;EVD_{colloid}_PRODUCT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_ION_GROWTH_RECIPE_001",
                SOURCE_ID,
                ion,
                "critical_data_gap",
                "reactor_process_gas",
                f"{ion}_S04",
                "temperature_setpoint_C",
                (
                    "The Ge-ion-implant section reports catalyst fabrication "
                    "and CNT outcomes but does not restate exact CNT growth "
                    "temperature, duration, gases, flows or pressure."
                ),
                f"EVD_{ion}_PROCESS_4",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_001",
                SOURCE_ID,
                colloid,
                "critical_data_gap",
                "yield_quality",
                f"{colloid}_PROD",
                "yield_value_standardized",
                (
                    "CNT area density is described comparatively as highest, "
                    "good, wider-window or slightly higher, but no numeric CNT "
                    "count density, mass yield, conversion or productivity is reported."
                ),
                f"EVD_{colloid}_PRODUCT;EVD_{sapphire}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FLOW_TIME_PRESSURE_001",
                SOURCE_ID,
                au,
                "critical_data_gap",
                "reactor_process_gas",
                f"{au}_S03",
                "total_flow_original",
                (
                    "Across the CVD experiments, CH4/H2 composition, absolute "
                    "flows, growth duration and pressure are generally not reported."
                ),
                f"EVD_{au}_PROCESS_3",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_RAMAN_QUANT_001",
                SOURCE_ID,
                au,
                "critical_data_gap",
                "yield_quality",
                f"{au}_PROD",
                "Raman_ratio_value",
                (
                    "Raman spectra establish RBM/G/D-band presence or absence, "
                    "but quantitative ID/IG ratios and systematic peak-fit values "
                    "are not reported."
                ),
                f"EVD_{au}_PRODUCT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_EXTERNAL_LITERATURE_001",
                SOURCE_ID,
                "not_applicable",
                "scope_boundary",
                "source_master",
                SOURCE_ID,
                "source_section_scope",
                (
                    "Ceramic-catalyst and other literature examples cited in "
                    "the review were not decomposed into runs because they are "
                    "secondary summaries without complete primary experimental details."
                ),
                f"EVD_{first}_RUN",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_NON_CVD_CONTROL_001",
                SOURCE_ID,
                first,
                "route_scope_exception",
                "source_run",
                first,
                "run_summary",
                (
                    "Figure 1 is explicitly described as not strictly CVD. It "
                    "is retained as a mechanistic structural-reorganization "
                    "control rather than merged with CVD growth runs."
                ),
                f"EVD_{first}_PROCESS_1",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CATALYST_DIMENSIONS_001",
                SOURCE_ID,
                au,
                "dimension_semantics",
                "catalyst_system",
                f"{au}_CAT",
                "catalyst_particle_size_qualifier",
                (
                    "AFM reports particle height/diameter distributions, parent "
                    "island dimensions and number densities. These are retained "
                    "in qualifiers rather than normalized into a single catalyst "
                    "particle-size field across unlike preparation routes."
                ),
                f"EVD_{au}_CATALYST",
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
