#!/usr/bin/env python3
"""Transcribe a five-paper B-class batch covering SWCNT, DWCNT and FB-CVD studies."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from scripts.extraction.batch_common import ROOT, TABLES, EvidenceStore, catalyst_row, cost_row, issue_row, load_metadata, master_row, process_row, run_row, yield_row
from scripts.extraction.build_b_class_batch_001 import add_evidence, publish_package
from scripts.extraction.package_io import existing_package_metric

BATCH_ID = "B_CLASS_371_20260719"
REPORT_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
BATCH_NUMBER = 12
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
PACKAGE_ROOT = ROOT / "data/interim/extraction/B"
SOURCE_IDS = ("LIT_345CEADD3D2F160E", "LIT_35577E37A51DAB17", "LIT_3DE18AF24FC0FE98", "LIT_409E04302856FA93", "LIT_436402DA7A57D194")


def make_tables(meta: dict[str, Any], scope: str) -> dict[str, list[dict[str, str]]]:
    out = {name: [] for name in TABLES}
    master = master_row(meta, scope)
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{meta['source_id']}.parsed.json"
    master["notes"] = f"Source-specific transcription for {BATCH_NAME}."
    out["source_master"].append(master)
    return out


def evidence(tables: dict[str, list[dict[str, str]]], store: EvidenceStore, source_id: str, run_id: str, cat: str, proc: str, prod: str, extra_process: bool = False) -> None:
    add_evidence(tables, store, source_id, run_id, "CAT", "catalyst_system", f"{run_id}_CAT", "record_level", cat, "Catalyst composition and preparation.")
    add_evidence(tables, store, source_id, run_id, "PROC", "reactor_process_gas", f"{run_id}_S01", "record_level", proc, "CNT-growth condition.")
    if extra_process:
        add_evidence(tables, store, source_id, run_id, "PROC2", "reactor_process_gas", f"{run_id}_S02", "record_level", proc, "Second reported process stage.")
    add_evidence(tables, store, source_id, run_id, "PRODUCT", "yield_quality", f"{run_id}_PROD", "record_level", prod, "Product outcome and characterization.")
    add_evidence(tables, store, source_id, run_id, "SCALE", "cost_scale_review", run_id, "record_level", proc, "Scale and process-resource context.", confidence="medium", value_status="review_assessment")


def build_tpcvd(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = meta["source_id"]
    tables = make_tables(meta, "Normal constant-temperature SWCNT growth and explicit 0/30/60/90/120-cycle tandem-plate temperature-perturbation conditions.")
    records = (
        ("NORMAL_850", "normal CVD at 850 C for 15 min", "normal", "15", "baseline broad chirality distribution; aligned SWCNT array"),
        ("TPCVD_000", "TPCVD protocol with 0 perturbation cycles", "0", "10", "aligned SWCNT control within cycle series"),
        ("TPCVD_030", "TPCVD with 30 perturbation cycles", "30", "13", "small-helix-angle population increased; length/density began to decrease"),
        ("TPCVD_060", "TPCVD with 60 perturbation cycles", "60", "16", "further small-helix-angle enrichment with reduced length/density"),
        ("TPCVD_090", "optimized TPCVD with 90 perturbation cycles", "90", "19", "72% helix angle below 10 degrees; (15,2) selectivity at least 21%; aligned SWCNT"),
        ("TPCVD_120", "TPCVD with 120 perturbation cycles", "120", "22", "no further enrichment beyond 90 cycles; additional catalyst deactivation"),
    )
    for code, label, cycles, total_growth, outcome in records:
        run_id = f"{source_id}_{code}"
        tables["source_run"].append(run_row(source_id, code, label, outcome))
        tables["catalyst_system"].append(catalyst_row(run_id, catalyst_label="Fe catalyst stripe on ST-cut quartz", active_metals="Fe", support_material="annealed ST-cut quartz", metal_ratio_original="0.05 mM Fe(OH)3/ethanol colloid", precursor_summary="Fe(OH)3/ethanol colloid", preparation_method="colloid deposition and needle-patterned stripe", preparation_detail="Quartz annealed 900 C in air 8 h and cooled to 300 C over 10 h; catalyst stripe drawn after needle dipping.", calcination_condition="sample heated in air to 850 C over 20 min before gas treatment"))
        if cycles == "normal":
            program = "constant 850 C for 15 min after H2 treatment"
        else:
            program = f"5 min pregrowth at 850 C; {cycles} cycles between 880 and 820 C (1 s move + 5 s stabilization per cycle); 5 min postgrowth at 850 C"
        tables["reactor_process_gas"].append(process_row(run_id, 1, "tandem_plate_CVD" if cycles != "normal" else "thermal_CVD", reactor_type="1-inch quartz-tube furnace with movable furnace/sample position", temperature_setpoint_C="850", temperature_range_reported_C="820-880" if cycles != "normal" and cycles != "0" else "", temperature_program_summary=program, holding_time_min=total_growth, carbon_source="ethanol vapour", carbon_source_flow_original="30 sccm Ar through ethanol bubbler", inert_gas="Ar", inert_gas_flow_original="30 sccm through ethanol bubbler during growth", reducing_gas="H2", reducing_gas_flow_original="300 sccm for 5 min before growth", gas_composition_summary="ethanol carried by 30 sccm Ar after 300 sccm H2 pretreatment"))
        tables["yield_quality"].append(yield_row(run_id, primary_yield_metric="SWCNT chirality distribution and array outcome", yield_original=outcome, yield_definition_original="Raman/TEM/SEM tube-count statistics; no mass yield.", secondary_result_summary=outcome, CNT_type_reported="single-walled carbon nanotubes", CNT_type_confirmed="SWCNT", product_mixture_summary="horizontally aligned SWCNT array with cycle-dependent chirality distribution", CNT_type_evidence="RBM Raman mapping, TEM and SEM.", SWCNT_or_few_wall_evidence_summary="SWCNT chiralities assigned by RBM Raman/TEM.", outer_diameter_mean_nm="about 0.8 Raman/simulation-matched subset" if code == "TPCVD_090" else "", morphology="well-aligned SWCNT array", alignment_or_array="horizontally aligned array on quartz", Raman_ratio_type="chirality/RBM population", Raman_ratio_value="72% helix angle <10 degrees; >=21% (15,2)" if code == "TPCVD_090" else "not_reported", characterization_methods="SEM; AFM; TEM; Raman mapping"))
        tables["cost_scale_review"].append(cost_row(run_id, scale_evidence_summary="Laboratory quartz-substrate SWCNT CVD.", cost_driver_summary="Movable furnace, 820-880 C cycling, ethanol, H2/Ar and patterned Fe colloid.", safety_risk="Ethanol vapour and hydrogen at high temperature.", emission_or_waste="CVD exhaust and catalyst-coated quartz; not quantified."))
        evidence(tables, store, source_id, run_id, "SPAN_43111CC0CABF9268236B", "SPAN_43111CC0CABF9268236B", "SPAN_BF9A75F5149DAB6BA58C" if code == "TPCVD_090" else "SPAN_37B14FC27F945EFE62B5")
    tables["review_issue_log"].append(issue_row(f"{source_id}_ISSUE_TREND_001", source_id, f"{source_id}_TPCVD_030", "qualitative_series", "yield_quality", f"{source_id}_TPCVD_030_PROD", "yield_original", "Only the 90-cycle condition has explicit chirality percentages; other cycle points retain the reported trend and are not assigned invented numeric selectivity.", f"EVD_{source_id}_TPCVD_030_PRODUCT", "medium"))
    return tables


def build_combinatorial(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = meta["source_id"]
    tables = make_tables(meta, "Seven optimized/summary catalyst conditions from the combinatorial thickness-by-methane maps; continuous maps are not expanded into fabricated grid points.")
    records = (
        ("FE_070", "Fe optimum", "Fe", "0.7 nm nominal Fe at maximum", "70", "4-6 tubes/micrometre; broad 35-85% CH4 growth window"),
        ("CO_065", "Co optimum", "Co", "optimized gradient-film region", "65", "4-6 tubes/micrometre; narrower CH4 window"),
        ("NI_OPT", "Ni optimized thin-film region", "Ni", "below 0.6 nm", "not_reported", "about 1 tube/micrometre"),
        ("CU_080", "Cu optimum", "Cu", "optimized gradient-film region", "80", "about 1 tube/micrometre"),
        ("MO_070", "Mo no-growth condition", "Mo", "optimized gradient-film map", "70", "no nanotube growth"),
        ("FECO_075_080", "Fe-Co high-density region", "Fe; Co", "overlapping sufficient Fe and Co thicknesses", "75-80", "7-9 tubes/micrometre"),
        ("COCU_070", "Co-Cu high-density region", "Co; Cu", "overlapping optimized Co and Cu thicknesses", "70", "8-10 tubes/micrometre; relatively short"),
    )
    for code, label, metals, thickness, methane, outcome in records:
        run_id = f"{source_id}_{code}"
        has_cnt = not outcome.startswith("no")
        tables["source_run"].append(run_row(source_id, code, label, outcome))
        tables["catalyst_system"].append(catalyst_row(run_id, catalyst_label=f"combinatorial {metals.replace('; ', '-')} film on r-plane sapphire", active_metals=metals, support_material="r-plane sapphire, miscut <0.3 degrees", metal_ratio_original=thickness, precursor_summary="elemental RF sputter target(s)", preparation_method="combinatorial RF magnetron sputtering through slit mask", preparation_detail="10 micrometre catalyst stripes at 300 micrometre spacing; gradual film thickness; second mask rotated 90 degrees for binary catalysts.", activation_condition="900 C in 100 sccm H2 for 5 min"))
        ch4_flow = "not_reported" if methane == "not_reported" else f"{methane}% of 380 sccm total CH4/H2"
        tables["reactor_process_gas"].append(process_row(run_id, 1, "thermal_CVD", reactor_type="26 mm ID quartz tube", temperature_setpoint_C="900", holding_time_min="15", carbon_source="CH4", carbon_source_flow_original=ch4_flow, reducing_gas="H2", total_flow_original="380 sccm CH4/H2", total_flow_sccm="380", gas_composition_summary=f"CH4 concentration {methane}% of CH4+H2 at 380 sccm total; 5 min H2 reduction before growth", cooling_condition="cooled in 300 sccm Ar"))
        tables["yield_quality"].append(yield_row(run_id, primary_yield_metric="horizontally aligned SWCNT line density", yield_original=outcome, yield_definition_original="Direct SEM count per micrometre width; not gravimetric yield.", secondary_result_summary=outcome, CNT_type_reported="single-walled carbon nanotubes" if has_cnt else "no nanotube growth", CNT_type_confirmed="SWCNT" if has_cnt else "not_applicable", product_mixture_summary=outcome, CNT_type_evidence="Raman RBM and SEM line counting" if has_cnt else "SEM no-growth observation", SWCNT_or_few_wall_evidence_summary="clear RBM peaks at 100-200 cm-1 for representative products" if has_cnt else "", morphology="horizontally aligned SWCNT" if has_cnt else "no CNT", alignment_or_array="aligned along sapphire atomic rows" if has_cnt else "not_applicable", characterization_methods="SEM; AFM; Raman"))
        tables["cost_scale_review"].append(cost_row(run_id, scale_evidence_summary="Laboratory 10 x 10 mm patterned sapphire combinatorial sample.", cost_driver_summary="Photolithography, RF sputtering, 900 C CH4/H2 CVD and sapphire.", safety_risk="Methane/hydrogen at 900 C, plasma cleaning and solvent/photoresist handling.", emission_or_waste="CVD exhaust, photoresist/acetone waste and sputtered-metal substrate."))
        product_span = "SPAN_E1C7E19C2398FDCDE86C" if code == "COCU_070" else "SPAN_8A58D14C0A54860C7CE0" if code == "FECO_075_080" else "SPAN_033C6565BB6600915135"
        evidence(tables, store, source_id, run_id, "SPAN_6BB448B246A8539EF483", "SPAN_0707D9506D116051796D", product_span)
    tables["review_issue_log"].append(issue_row(f"{source_id}_ISSUE_MAP_001", source_id, f"{source_id}_FE_070", "series_granularity", "source_run", f"{source_id}_FE_070", "run_summary", "Continuous catalyst-thickness/methane maps are represented by printed optima and explicit no-growth/summary conditions, not by synthetic grid points.", f"EVD_{source_id}_FE_070_PRODUCT", "medium"))
    return tables


def build_water_fccvd(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = meta["source_id"]
    tables = make_tables(meta, "Three otherwise matched continuous FCCVD runs with 0, 1 or 2 mL DI water added to one 10 mL catalyst-solution syringe.")
    records = (
        ("CNT0", "0", "MWCNT-dominant; 19-23 nm", "19-23", "7.25", "18.57", "10.55"),
        ("CNT1", "1", "DWCNTs emerge with some >10-wall MWCNT", "not_reported", "7.96", "22.86", "not_reported"),
        ("CNT2", "2", "great majority DWCNT; 10-15 nm", "10-15", "10.23", "23.89", "10.54"),
    )
    for code, water, morphology, diameter, raman, tga_residue, initial_fe in records:
        run_id = f"{source_id}_{code}"
        tables["source_run"].append(run_row(source_id, code, f"water-assisted FCCVD catalyst solution with {water} mL DI water", morphology))
        tables["catalyst_system"].append(catalyst_row(run_id, catalyst_label="floating Fe/S catalyst", active_metals="Fe", promoter="S from thiophene; water oxidizer", support_material="unsupported floating catalyst", metal_ratio_original=f"Fe:S molar ratio 1:3; {water} mL DI water per standard catalyst solution", precursor_summary="ferrocene, thiophene, acetone and DI water", preparation_method="premixed liquid floating-catalyst feed", preparation_detail=f"Standard feed used Fe:S=1:3 and {water} mL DI water; one 10 mL syringe consumed per collection.", phase_or_state_summary="S-coated Fe nanoparticles formed in situ; water removes amorphous carbon coating"))
        tables["reactor_process_gas"].append(process_row(run_id, 1, "water_assisted_floating_catalyst_CVD", reactor_type="closed-end alumina tube, 56 mm ID x 60 mm OD x 1000 mm", temperature_setpoint_C="1250", holding_time_min="not_reported; one 10 mL syringe consumed", carbon_source="acetone", carbon_source_flow_original="catalyst solution injection 5-?5 mL/h (upper digit corrupted in parsed source)", reducing_gas="H2", reducing_gas_flow_original="50-?00 sccm (upper digit corrupted in parsed source)", inert_gas="Ar", inert_gas_flow_original="700-?200 sccm (upper digit corrupted in parsed source)", gas_composition_summary="ferrocene/thiophene/acetone/water solution injected into flowing Ar/H2", process_note="CNT sock continuously collected on rotating Teflon-covered mandrel; exact upper flow digits require source-image review."))
        tables["yield_quality"].append(yield_row(run_id, primary_yield_metric="continuously collected CNT sock outcome", yield_original="one 10 mL catalyst-solution syringe per matched collection; CNT mass not reported", yield_definition_original="Matched feed-volume collection, not a mass yield.", secondary_result_summary=morphology, CNT_type_reported="DWCNT/MWCNT mixture", CNT_type_confirmed="DWCNT-dominant" if code == "CNT2" else "MWCNT-dominant" if code == "CNT0" else "mixed DWCNT/MWCNT", product_mixture_summary=f"{morphology}; catalyst residue and residual amorphous carbon present", CNT_type_evidence="HRTEM wall count; TGA/DTG and Raman", outer_diameter_range_nm=diameter, morphology="long entangled bundle network, slightly aligned by rotating collection spindle", alignment_or_array="partial collection-direction alignment", Raman_ratio_type="IG/ID", Raman_ratio_value=raman, Raman_laser_wavelength_nm="785", TGA_carbon_content_wt_percent=str(round(100-float(tga_residue), 2)), purity_basis=f"100 minus {tga_residue} wt.% residue at 800 C in air; includes all oxidized carbon, not purified CNT-only fraction", residue_summary=f"{tga_residue} wt.% at 800 C; initial EDS Fe {initial_fe} wt.%" if initial_fe != "not_reported" else f"{tga_residue} wt.% at 800 C", amorphous_carbon_level="decreases with added water; not separately quantified", characterization_methods="SEM/EDS; HRTEM; TGA/DTG; Raman"))
        tables["cost_scale_review"].append(cost_row(run_id, scale_evidence_summary="Continuous laboratory FCCVD sock collection from one 10 mL syringe.", reactor_capacity_or_throughput="continuous collection; liquid feed rate printed with OCR-corrupted upper bound", cost_driver_summary="1250 C furnace, ferrocene, thiophene, acetone, Ar/H2 and rotating collection.", safety_risk="Hydrogen/acetone at 1250 C; oxygen-containing exhaust controlled by one-way gas shield.", emission_or_waste="Ar/H2/oxygen-containing exhaust and Fe/S-containing CNT residue."))
        product_span = "SPAN_3CE20146892D37B1638D" if code != "CNT1" else "SPAN_9F4D1591DAA8C173AE83"
        evidence(tables, store, source_id, run_id, "SPAN_59ED11378A47754E8AFA", "SPAN_59ED11378A47754E8AFA", product_span)
    tables["review_issue_log"].extend((
        issue_row(f"{source_id}_ISSUE_FLOW_001", source_id, f"{source_id}_CNT0", "ocr_gap", "reactor_process_gas", f"{source_id}_CNT0_S01", "record_level", "Upper digits in the printed Ar, H2 and liquid-injection ranges are corrupted in the local text; values are not guessed.", f"EVD_{source_id}_CNT0_PROC", "high"),
        issue_row(f"{source_id}_ISSUE_PURITY_001", source_id, f"{source_id}_CNT2", "definition_ambiguity", "yield_quality", f"{source_id}_CNT2_PROD", "TGA_carbon_content_wt_percent", "TGA carbon fraction includes all oxidized carbon species and is not a purified DWCNT purity or synthesis yield.", f"EVD_{source_id}_CNT2_PRODUCT", "medium"),
    ))
    return tables


def build_vacnt_optimization(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = meta["source_id"]
    tables = make_tables(meta, "Printed catalyst-treatment endpoints at fixed 800 C growth plus three 820 C Raman characterization conditions; non-tabulated temperature curves are not digitized.")
    endpoint_records = (
        ("FE1_TR500_G800", "1", "500", "800", "1308", "not_reported"),
        ("FE1_TR800_G800", "1", "800", "800", "844", "not_reported"),
        ("FE3_TR500_G800", "3", "500", "800", "1598", "not_reported"),
        ("FE3_TR800_G800", "3", "800", "800", "1202", "not_reported"),
        ("FE5_TR500_G800", "5", "500", "800", "1117", "not_reported"),
        ("FE5_TR800_G800", "5", "800", "800", "1003", "not_reported"),
        ("FE1_G820_RAMAN", "1", "not_reported", "820", "not_reported", "0.5943"),
        ("FE3_G820_RAMAN", "3", "not_reported", "820", "not_reported", "0.5282"),
        ("FE5_G820_RAMAN", "5", "not_reported", "820", "not_reported", "0.4882"),
    )
    for code, fe_nm, treatment, growth, height, raman in endpoint_records:
        run_id = f"{source_id}_{code}"
        summary = f"{fe_nm} nm Fe; catalyst treatment {treatment} C; growth {growth} C; forest height {height} micrometres; ID/IG {raman}."
        tables["source_run"].append(run_row(source_id, code, f"{fe_nm} nm Fe VACNT condition", summary))
        tables["catalyst_system"].append(catalyst_row(run_id, catalyst_label=f"{fe_nm} nm Fe / 10 nm Al2O3 / 300 nm SiO2 / Si(100)", active_metals="Fe", support_material="10 nm Al2O3 on 300 nm SiO2/Si", metal_ratio_original=f"{fe_nm} nm Fe film; 10 nm Al2O3 support", precursor_summary="high-purity Fe and Al2O3 e-beam evaporation targets", preparation_method="e-beam evaporation", preparation_detail="Al2O3 deposited 0.3-0.5 nm/s, Fe 0.1-0.2 nm/s at 1e-6 Torr.", activation_condition=f"40/10 sccm H2/Ar for 5 min at {treatment} C" if treatment != "not_reported" else "40/10 sccm H2/Ar for 5 min; temperature not reported for Raman-only condition"))
        tables["reactor_process_gas"].append(process_row(run_id, 1, "catalyst_reduction", reactor_type="22 mm ID horizontal quartz tube; 300 mm hot zone", temperature_setpoint_C=treatment, holding_time_min="5", reducing_gas="H2", reducing_gas_flow_original="40 sccm", reducing_gas_flow_sccm="40", inert_gas="Ar", inert_gas_flow_original="10 sccm", inert_gas_flow_sccm="10", total_flow_original="50 sccm", total_flow_sccm="50"))
        tables["reactor_process_gas"].append(process_row(run_id, 2, "thermal_CVD", reactor_type="22 mm ID horizontal quartz tube; 300 mm hot zone", temperature_setpoint_C=growth, holding_time_min="30", carbon_source="C2H4", carbon_source_flow_original="10 sccm", carbon_source_flow_sccm="10", reducing_gas="H2", reducing_gas_flow_original="40 sccm", reducing_gas_flow_sccm="40", inert_gas="Ar", inert_gas_flow_original="10 sccm", inert_gas_flow_sccm="10", total_flow_original="60 sccm", total_flow_sccm="60", cooling_condition="rapid cooling under 300 sccm Ar"))
        tables["yield_quality"].append(yield_row(run_id, primary_yield_metric="VACNT forest height", yield_original=f"{height} micrometres" if height != "not_reported" else "not_reported; Raman characterization condition", yield_definition_original="SEM forest height after 30 min growth.", CNT_type_reported="vertically aligned multi-walled CNT", CNT_type_confirmed="MWCNT", product_mixture_summary="millimetre-class VACNT forest" if height != "not_reported" else "VACNT forest", CNT_type_evidence="Raman D/G/G' bands; source identifies MWCNT forests.", length_summary=f"{height} micrometres" if height != "not_reported" else "not_reported", morphology="vertically aligned forest", alignment_or_array="VACNT forest", Raman_ratio_type="ID/IG" if raman != "not_reported" else "not_reported", Raman_ratio_value=raman, Raman_laser_wavelength_nm="532", characterization_methods="SEM; Raman"))
        tables["cost_scale_review"].append(cost_row(run_id, scale_evidence_summary="Laboratory 7 x 7 mm substrate CVD.", cost_driver_summary="E-beam thin films, 500-840 C H2 treatment/CVD and ethylene/Ar gas.", safety_risk="Hydrogen/ethylene at high temperature.", emission_or_waste="CVD exhaust and coated Si substrate."))
        evidence(tables, store, source_id, run_id, "SPAN_AB2A4182EB3318DB6EE3", "SPAN_0E0827411D1930465625", "SPAN_2EB1A0FDC0D24340589B" if raman != "not_reported" else "SPAN_756588EEA6E7D2440D04", extra_process=True)
    tables["review_issue_log"].append(issue_row(f"{source_id}_ISSUE_CURVE_001", source_id, f"{source_id}_FE1_TR500_G800", "plot_only_data", "source_run", f"{source_id}_FE1_TR500_G800", "run_summary", "Only table values and stated endpoints/optima are transcribed; intermediate treatment/growth-temperature points visible only in plots are not digitized.", f"EVD_{source_id}_FE1_TR500_G800_PRODUCT", "medium"))
    return tables


def build_fluidized_bed(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = meta["source_id"]
    tables = make_tables(meta, "Nine author-generated Fe/Al2O3 MWCNT fluidized-bed runs: six temperatures in the 2.5 cm reactor and three larger-reactor scale-up runs. Literature-review Table 1 and Ni/GNF runs are excluded from CNT production.")
    records = (
        ("R25_T500", "2.5", "60", "0.5", "500", "60", "160", "120", "0.28", "0.56", "7.8", "small FB temperature series"),
        ("R25_T550", "2.5", "60", "0.5", "550", "60", "160", "120", "0.55", "1.10", "15.3", "small FB temperature series"),
        ("R25_T600", "2.5", "60", "0.5", "600", "60", "160", "120", "0.95", "1.90", "26.4", "small FB temperature series"),
        ("R25_T650", "2.5", "60", "0.5", "650", "60", "160", "120", "1.35", "2.70", "37.6", "small FB optimum"),
        ("R25_T700", "2.5", "60", "0.5", "700", "60", "160", "120", "1.28", "2.55", "35.5", "small FB temperature series"),
        ("R25_T750", "2.5", "60", "0.5", "750", "60", "160", "120", "1.23", "2.46", "34.2", "small FB temperature series"),
        ("R53_RUN1", "5.3", "120", "20", "650", "405", "685", "1200", "40.4", "2.02", "83.2", "partial bed agglomeration"),
        ("R160_RUN1", "16", "120", "200", "650", "11300", "6500", "3800", "535", "2.70", "39.5", "pilot reproducibility run 1; no agglomeration"),
        ("R160_RUN2", "16", "120", "200", "650", "11300", "6500", "3800", "551", "2.75", "40.7", "pilot reproducibility run 2; no agglomeration"),
    )
    for code, diameter, minutes, catalyst_mass, temp, ethylene, n2, h2, cnt_mass, productivity, conversion, note in records:
        run_id = f"{source_id}_{code}"
        tables["source_run"].append(run_row(source_id, code, f"{diameter} cm FB-CVD at {temp} C", f"Produced {cnt_mass} g MWCNT; {productivity} gC/gcat; ethylene conversion {conversion}%; {note}."))
        tables["catalyst_system"].append(catalyst_row(run_id, catalyst_label="9.6 wt.% Fe/Al2O3", active_metals="Fe", support_material="Al2O3 powder (204 m2/g; dv50 301 micrometres)", metal_ratio_original="9.6 wt.% Fe by ICP", precursor_summary="iron pentacarbonyl and water vapour", preparation_method="fluidized-bed organometallic CVD deposition", preparation_detail="Fe(CO)5 evaporated at 50 C and decomposed with water vapour on fluidized alumina at 220 C/50 Torr using N2."))
        tables["reactor_process_gas"].append(process_row(run_id, 1, "fluidized_bed_CVD", reactor_type=f"vertical {diameter} cm ID fluidized-bed CVD reactor", reactor_setup_summary=f"{catalyst_mass} g Fe/Al2O3; fluidized under N2/H2 during heat-up, then ethylene introduced at constant total flow.", catalyst_loading_mass_g=catalyst_mass, temperature_setpoint_C=temp, holding_time_min=minutes, carbon_source="C2H4", carbon_source_flow_original=f"{ethylene} sccm", carbon_source_flow_sccm=ethylene, reducing_gas="H2", reducing_gas_flow_original=f"{h2} sccm", reducing_gas_flow_sccm=h2, inert_gas="N2", inert_gas_flow_original=f"{n2} sccm", inert_gas_flow_sccm=n2, total_flow_original=f"{float(ethylene)+float(n2)+float(h2):g} sccm", total_flow_sccm=f"{float(ethylene)+float(n2)+float(h2):g}"))
        tables["yield_quality"].append(yield_row(run_id, primary_yield_metric="as-produced MWCNT mass and catalyst productivity", yield_original=f"{cnt_mass} g CNT; {productivity} gC/gcat; {conversion}% C2H4 conversion", yield_definition_original="Weighed carbon deposit characterized as selectively produced MWCNT; productivity is grams carbon per gram initial catalyst.", CNT_yield_per_catalyst_g_gcat=productivity, CNT_productivity_g_gcat_h=str(round(float(productivity)/(float(minutes)/60), 4)), carbon_source_conversion_percent=conversion, secondary_result_summary=note, CNT_type_reported="multi-walled carbon nanotubes", CNT_type_confirmed="MWCNT", product_mixture_summary="MWCNT/catalyst composite powder before acid purification", CNT_type_evidence="TEM, SEM, TGA and Raman; scale-up product reported completely selective.", morphology="globular MWCNT mass around exploding catalyst grains", characterization_methods="gravimetry; TGA; SEM; TEM; Raman", post_treatment_or_purification="H2SO4 wash", purification_condition="acid wash to remove catalyst"))
        level = "pilot_scale" if diameter == "16" else "bench_scale" if diameter == "5.3" else "lab_batch"
        tables["cost_scale_review"].append(cost_row(run_id, scale_level_demonstrated=level, scale_evidence_summary=f"{diameter} cm ID FB-CVD with {catalyst_mass} g catalyst and {cnt_mass} g CNT in {minutes} min.", reactor_capacity_or_throughput=f"{cnt_mass} g per {minutes} min; {round(float(cnt_mass)/(float(minutes)/60), 2)} g/h observed", continuous_operation_time_h=str(float(minutes)/60), batch_stability="duplicate pilot runs 535 and 551 g" if diameter == "16" else note, scale_up_issue="partial agglomeration" if diameter == "5.3" else "no agglomeration reported" if diameter == "16" else "wall effects and local agglomeration at high productivity", cost_driver_summary="Fe/Al2O3 catalyst, 650 C fluidized bed, high ethylene/H2/N2 flows and acid purification.", safety_risk="Large hot flows of ethylene/hydrogen and iron-carbonyl catalyst preparation.", emission_or_waste="Bag-filter fines, reactor off-gas and Fe-containing sulfuric-acid wash waste."))
        evidence(tables, store, source_id, run_id, "SPAN_20990C8C2C83C65BB56F", "SPAN_13DF52CB1777CFFB2C77", "SPAN_4A36CC2D650D8FDBEF78")
    tables["review_issue_log"].append(issue_row(f"{source_id}_ISSUE_SCOPE_001", source_id, f"{source_id}_R25_T650", "source_scope", "source_run", f"{source_id}_R25_T650", "run_summary", "Review Table 1 and the Ni/Al2O3 graphite-nanofibre series are excluded; only author-generated Fe/Al2O3 MWCNT runs enter the CNT eight tables.", f"EVD_{source_id}_R25_T650_PRODUCT", "low"))
    return tables


BUILDERS: dict[str, Callable[[dict[str, Any], EvidenceStore], dict[str, list[dict[str, str]]]]] = {
    "LIT_345CEADD3D2F160E": build_tpcvd,
    "LIT_35577E37A51DAB17": build_combinatorial,
    "LIT_3DE18AF24FC0FE98": build_water_fccvd,
    "LIT_409E04302856FA93": build_vacnt_optimization,
    "LIT_436402DA7A57D194": build_fluidized_bed,
}


def main() -> None:
    metadata = load_metadata("B")
    store = EvidenceStore()
    metrics: list[dict[str, Any]] = []
    try:
        for source_id in SOURCE_IDS:
            metric = existing_package_metric(source_id, "B")
            if metric is None:
                metrics.append(publish_package(source_id, BUILDERS[source_id](metadata[source_id], store)))
            else:
                metrics.append(metric)
    finally:
        store.close()
    result = {"batch_id": BATCH_NAME, "sources": metrics, "total_runs": sum(x["row_counts"]["source_run"] for x in metrics), "status": "completed_needs_review"}
    (REPORT_ROOT / "manual_batch_012_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
