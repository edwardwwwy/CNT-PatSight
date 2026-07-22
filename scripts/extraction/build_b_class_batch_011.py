#!/usr/bin/env python3
"""Transcribe five B-class CVD papers into source-specific eight-table packages."""

from __future__ import annotations

import json
from typing import Any, Callable

from scripts.extraction.batch_common import ROOT, TABLES, EvidenceStore, catalyst_row, cost_row, issue_row, load_metadata, master_row, process_row, run_row, yield_row
from scripts.extraction.build_b_class_batch_001 import add_evidence, publish_package

BATCH_ID = "B_CLASS_371_20260719"
REPORT_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
BATCH_NUMBER = 11
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
SOURCE_IDS = (
    "LIT_29053831AED49C65",
    "LIT_2AF904451035F138",
    "LIT_2CBAB1EE4362DD19",
    "LIT_308D1442E521B6DD",
    "LIT_34447B54D64C4FF1",
)


def make_tables(meta: dict[str, Any], scope: str) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    master = master_row(meta, scope)
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{meta['source_id']}.parsed.json"
    master["notes"] = f"Source-specific first-pass transcription for {BATCH_NAME}."
    tables["source_master"].append(master)
    return tables


def evidence4(tables: dict[str, list[dict[str, str]]], store: EvidenceStore, source_id: str, run_id: str, cat: str, proc: str, prod: str) -> None:
    add_evidence(tables, store, source_id, run_id, "CAT", "catalyst_system", f"{run_id}_CAT", "record_level", cat, "Catalyst preparation and identity.")
    add_evidence(tables, store, source_id, run_id, "PROC", "reactor_process_gas", f"{run_id}_S01", "record_level", proc, "Reported CNT-growth condition.")
    add_evidence(tables, store, source_id, run_id, "PRODUCT", "yield_quality", f"{run_id}_PROD", "record_level", prod, "Reported CNT outcome and characterization.")
    add_evidence(tables, store, source_id, run_id, "SCALE", "cost_scale_review", run_id, "record_level", proc, "Laboratory apparatus and process context.", confidence="medium", value_status="review_assessment")


def build_pecvd_wire(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = meta["source_id"]
    tables = make_tables(meta, "Explicit PECVD temperature, pressure/wire-diameter and plasma/bias cases; phase-diagram ranges are not expanded into unprinted grid points.")

    records = (
        # code, metal, wire um, K, C2H2 Torr, plasma, bias, outcome
        ("CO30_RT_P02", "Co", "30", "room_temperature", "0.2", "dc_glow", "-500 V", "no CNT"),
        ("CO30_750_P02", "Co", "30", "750", "0.2", "dc_glow", "-500 V", "dense aligned CNT; 20-130 nm diameter; about 5 micrometres long"),
        ("CO30_1200_P02", "Co", "30", "1200", "0.2", "dc_glow", "-500 V", "no CNT"),
        ("NI10_750_P005", "Ni", "10", "750", "0.05", "dc_glow", "-500 V", "no CNT below 0.1 Torr C2H2"),
        ("NI10_750_P01", "Ni", "10", "750", "0.1", "dc_glow", "-500 V", "densely distributed aligned CNT"),
        ("NI10_750_P03", "Ni", "10", "750", "0.3", "dc_glow", "-500 V", "aligned CNT; average length up to 6 micrometres"),
        ("NI10_750_P04", "Ni", "10", "750", "0.4", "dc_glow", "-500 V", "lengthened CNT aggregated into conical bundles"),
        ("NI30_750_P08", "Ni", "30", "750", "0.8", "dc_glow", "-500 V", "aligned CNT"),
        ("CO10_750_P01", "Co", "10", "750", "0.1", "dc_glow", "-500 V", "aligned CNT below 0.2 Torr"),
        ("CO10_750_P02", "Co", "10", "750", "0.2", "dc_glow", "-500 V", "conical CNT bundles"),
        ("CO10_750_P08", "Co", "10", "750", "0.8", "dc_glow", "-500 V", "stalactite-like CNT structures"),
        ("CO30_750_THERM_P02", "Co", "30", "750", "0.2", "none", "resistive heating only", "sparse randomly configured CNT; some helical or looped"),
        ("CO30_750_THERM_P08", "Co", "30", "750", "0.8", "none", "resistive heating only", "higher site density of lengthened random CNT; never well aligned"),
        ("CO30_750_INV_P02", "Co", "30", "750", "0.2", "inverse_dc_glow", "+500 V", "no CNT"),
    )
    for code, metal, wire, temp, acetylene_p, plasma, bias, outcome in records:
        run_id = f"{source_id}_{code}"
        has_cnt = not outcome.startswith("no CNT")
        tables["source_run"].append(run_row(source_id, code, f"{metal}/{wire} um W wire; {temp} K; C2H2 {acetylene_p} Torr; {plasma}", outcome))
        tables["catalyst_system"].append(catalyst_row(run_id, catalyst_label=f"approximately 80 nm {metal} film on W wire", active_metals=metal, support_material=f"{wire} micrometre diameter W wire", metal_ratio_original=f"approximately 80 nm {metal} film", precursor_summary=f"{metal} disk sputter target", preparation_method="Ar+ sputter deposition", preparation_detail="Catalyst film deposited on W wire by Ar+ sputtering the disk electrode at 0.1 Torr."))
        tables["reactor_process_gas"].append(process_row(run_id, 1, "dc_PECVD" if plasma != "none" else "thermal_CVD_control", reactor_type="dc PECVD chamber with resistively heated W-wire sample about 10 mm from disk electrode", temperature_setpoint_C=str(round((float(temp) - 273.15), 2)) if temp != "room_temperature" else "room_temperature", holding_time_min="20", pressure_original=f"C2H2 {acetylene_p} Torr; NH3 {2*float(acetylene_p):g} Torr", pressure_kPa="", carbon_source="C2H2", carbon_source_flow_original=f"partial pressure {acetylene_p} Torr", reducing_gas="NH3", reducing_gas_flow_original=f"partial pressure {2*float(acetylene_p):g} Torr", gas_composition_summary=f"C2H2:NH3 partial-pressure ratio 1:2; sample bias {bias}; plasma mode {plasma}", process_note="Pressure is represented by acetylene partial pressure; no absolute gas flow reported."))
        tables["yield_quality"].append(yield_row(run_id, primary_yield_metric="CNT growth/morphology outcome", yield_original=outcome, yield_definition_original="SEM/TEM morphology outcome; no gravimetric yield.", secondary_result_summary=outcome, CNT_type_reported="CNT" if has_cnt else "no CNT", CNT_type_confirmed="CNT" if has_cnt else "not_applicable", product_mixture_summary=outcome, CNT_type_evidence="SEM; TEM for representative Co and Ni products" if has_cnt else "SEM no-growth observation", outer_diameter_range_nm="20-130" if code == "CO30_750_P02" else "", length_summary="about 5 micrometres" if code == "CO30_750_P02" else "up to 6 micrometres" if code == "NI10_750_P03" else "", morphology=outcome, alignment_or_array="aligned" if "aligned" in outcome and "never" not in outcome else "not aligned" if has_cnt else "not_applicable", characterization_methods="SEM; TEM; electron diffraction" if has_cnt else "SEM"))
        tables["cost_scale_review"].append(cost_row(run_id, scale_evidence_summary="Laboratory W-wire dc PECVD condition.", cost_driver_summary="Vacuum chamber, resistive wire heating, dc plasma, acetylene/ammonia and sputtered Co or Ni film.", safety_risk="Acetylene/ammonia gases, high voltage and hot wire under vacuum.", emission_or_waste="PECVD exhaust and metal-coated W wire; not quantified."))
        prod_span = "SPAN_1EFC3A46AC67421B280F" if code.startswith("CO30_") and "THERM" not in code and "INV" not in code else "SPAN_824BF56271D7EDDD63EA" if code.startswith(("NI", "CO10")) else "SPAN_A22435120E937D0DE04C"
        evidence4(tables, store, source_id, run_id, "SPAN_7131E928D0E32AD7D59D", "SPAN_7131E928D0E32AD7D59D", prod_span)
    tables["review_issue_log"].append(issue_row(f"{source_id}_ISSUE_PHASE_001", source_id, f"{source_id}_NI10_750_P01", "granularity_limit", "source_run", f"{source_id}_NI10_750_P01", "run_summary", "Only exact conditions and explicit boundary examples are materialized. Curves/demarcation lines in the phase diagram are not converted into invented point runs.", f"EVD_{source_id}_NI10_750_P01_PRODUCT", "medium"))
    return tables


def build_temperature_vacnt(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = meta["source_id"]
    tables = make_tables(meta, "Four PECVD temperature points at otherwise fixed Ni/Cr/Si catalyst, gas, pressure and time.")
    records = (
        ("T650", "650", "25 +/- 3", "65 +/- 5", "not_reported", "vertical array with disoriented CNTs"),
        ("T700", "700", "25 +/- 4", "66 +/- 5", "0.92", "vertically aligned MWCNT; disoriented CNTs removed"),
        ("T750", "750", "44 +/- 3", "80 +/- 9", "0.88", "vertically aligned MWCNT; lowest reported defect ratio; some individual 70 +/- 3 nm x 350 +/- 10 nm CNTs"),
        ("T800", "800", "51 +/- 6", "100 +/- 12", "0.90", "graphenated vertically aligned MWCNT; some individual 52 +/- 2 nm x 600 +/- 14 nm CNTs"),
    )
    for code, temp, diameter, height, raman, morphology in records:
        run_id = f"{source_id}_{code}"
        tables["source_run"].append(run_row(source_id, code, f"Ni(10 nm)/Cr(20 nm)/Si PECVD at {temp} C", morphology))
        tables["catalyst_system"].append(catalyst_row(run_id, catalyst_label="10 nm Ni / 20 nm Cr / Si(100)", active_metals="Ni", support_material="20 nm Cr buffer layer on Si(100)", metal_ratio_original="10 nm Ni catalytic film; 20 nm Cr buffer", precursor_summary="Ni and Cr sputter targets", preparation_method="magnetron sputtering", preparation_detail="Cr buffer and Ni catalytic films formed on Si(100) by magnetron sputtering."))
        tables["reactor_process_gas"].append(process_row(run_id, 1, "PECVD", reactor_type="NANOFAB NTK-9 PECVD module", temperature_setpoint_C=temp, holding_time_min="20", pressure_original="4.5 Torr", pressure_kPa="0.59995", carbon_source="C2H2", carbon_source_flow_original="70 sccm", carbon_source_flow_sccm="70", reducing_gas="NH3", reducing_gas_flow_original="210 sccm", reducing_gas_flow_sccm="210", total_flow_original="280 sccm", total_flow_sccm="280", gas_composition_summary="70 sccm acetylene and 210 sccm ammonia at 4.5 Torr"))
        tables["yield_quality"].append(yield_row(run_id, primary_yield_metric="VACNT geometric outcome", yield_original=f"mean diameter {diameter} nm; reported array/CNT height {height} nm", yield_definition_original="SEM statistical dimensions; the source labels the second dimension as height.", secondary_result_summary=morphology, CNT_type_reported="vertically aligned carbon nanotubes", CNT_type_confirmed="MWCNT", product_mixture_summary=morphology, CNT_type_evidence="D/G Raman modes and absence of RBM in all samples indicate multiwall CNT.", outer_diameter_mean_nm=diameter.split(" +/- ")[0], outer_diameter_range_nm=diameter, wall_number_summary="multiwalled", length_summary=f"reported height {height} nm", morphology=morphology, alignment_or_array="vertically aligned array", Raman_ratio_type="ID/IG" if raman != "not_reported" else "not_reported", Raman_ratio_value=raman, RBM_peak_reported="absent", characterization_methods="SEM; Raman"))
        tables["cost_scale_review"].append(cost_row(run_id, scale_evidence_summary="Laboratory Si-wafer PECVD sample.", cost_driver_summary="650-800 C PECVD, acetylene/ammonia, vacuum and sputtered Ni/Cr films.", safety_risk="Acetylene/ammonia and plasma/vacuum operation.", emission_or_waste="PECVD exhaust and coated Si wafer; not quantified."))
        evidence4(tables, store, source_id, run_id, "SPAN_365F3A0E561CD0EC7671", "SPAN_365F3A0E561CD0EC7671", "SPAN_4127CBDACE2C54254D43")
    tables["review_issue_log"].append(issue_row(f"{source_id}_ISSUE_HEIGHT_001", source_id, f"{source_id}_T750", "unit_or_definition_check", "yield_quality", f"{source_id}_T750_PROD", "length_summary", "The paper repeatedly reports VACNT height in nm (80-100 nm) while mentioning individual CNTs up to 350-600 nm; values are preserved exactly and require source-image confirmation.", f"EVD_{source_id}_T750_PRODUCT", "medium"))
    return tables


def build_aerogel(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = meta["source_id"]
    tables = make_tables(meta, "One C13-methane tracing run, three carbon-source axial-collection series summaries and two counter-flow methane exposure outcomes.")

    def add_run(code: str, label: str, reactor: str, furnace: str, carbon: str, carbon_feed: str, h2: str, outcome: str, data_type: str, span: str) -> None:
        run_id = f"{source_id}_{code}"
        run = run_row(source_id, code, label, outcome)
        run["data_type"] = data_type
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst_row(run_id, catalyst_label="floating Fe/S catalyst from ferrocene and thiophene", active_metals="Fe", promoter="S from thiophene", support_material="unsupported floating catalyst", precursor_summary="ferrocene and thiophene vapours", preparation_method="in-situ floating-catalyst nucleation", preparation_detail="Ferrocene sublimed into H2 and thiophene bubbled into H2; catalyst droplets form, evaporate and re-nucleate along reactor temperature profile.", phase_or_state_summary="small liquid Fe/S catalyst droplets downstream of the hottest zone"))
        tables["reactor_process_gas"].append(process_row(run_id, 1, "floating_catalyst_CVD", reactor_type=reactor, temperature_setpoint_C=furnace, holding_time_min="8 carbon-source feed" if code == "C13_TRACE" else "4-30 reagent-supply window" if code.startswith("AXIAL") else "not_reported", carbon_source=carbon, carbon_source_flow_original=carbon_feed, reducing_gas="H2", reducing_gas_flow_original=h2, inert_gas="Ar during cooling", gas_composition_summary=f"{carbon}; floating ferrocene/thiophene in H2", process_note="Aerogel formation varies axially with the non-isothermal reactor temperature profile."))
        tables["yield_quality"].append(yield_row(run_id, primary_yield_metric="CNT aerogel formation outcome", yield_original=outcome, yield_definition_original="Aerogel filament or axial filter-mass outcome; no single source-normalized CNT yield reported.", secondary_result_summary=outcome, CNT_type_reported="CNT aerogel", CNT_type_confirmed="CNT", product_mixture_summary="CNT aerogel with source/position-dependent graphitic impurities", CNT_type_evidence="Raman and SEM; continuous aerogel filament collected where formation occurred.", morphology="spinnable CNT aerogel/web" if "no aerogel" not in outcome else "no aerogel", characterization_methods="Raman; SEM; axial gravimetric filter collection"))
        tables["cost_scale_review"].append(cost_row(run_id, scale_evidence_summary="Lab-scale horizontal continuous-feed aerogel reactor.", cost_driver_summary="1200-1300 C furnace, hydrogen, ferrocene, thiophene and carbon feed.", safety_risk="Hydrogen and hydrocarbon feed at very high temperature; organometallic/sulphur precursors.", emission_or_waste="Hot reactor exhaust, Fe/S-containing soot/aerogel and purge gas; not quantitatively inventoried."))
        evidence4(tables, store, source_id, run_id, span, span, span)

    add_run("C13_TRACE", "13CH4 isotope-tracing CNT aerogel", "46 mm ID x 700 mm quartz tube", "1200", "13CH4", "40 sccm after 8 min catalyst feed", "0.5 slpm bulk H2 plus 40 sccm ferrocene-H2 and 10 sccm thiophene-H2", "intact aerogel filament; about 95% of CNT carbon derived from methane", "experimental_run", "SPAN_4FF71EFAB3480EFEBBC2")
    for code, carbon, flow in (("AXIAL_CH4", "CH4", "120 sccm"), ("AXIAL_ETHANOL", "ethanol", "8 mL/h"), ("AXIAL_TOLUENE", "toluene", "2.5 mL/h")):
        add_run(code, f"axial aerogel quantification with {carbon}", "40 mm ID x 700 mm alumina tube", "1300", carbon, flow, "1.4 slpm bulk H2 plus 100 sccm ferrocene-H2 and 100 sccm thiophene-H2", "similar S-shaped axial CNT mass profile; bulk formation mainly downstream as gas cools from about 1200 to 950 C", "experimental_series_summary", "SPAN_42BCA9967AA03251EE74")
    add_run("COUNTER_CH4_900", "counter-flow CH4 delivered only to about 900 C re-nucleation zone", "quartz reactor with adjustable alumina counter-flow tube", "hot-zone setpoint from C13-like protocol", "CH4", "20-70 sccm counter-flow", "front-fed ferrocene/thiophene in bulk H2", "no aerogel formed when methane was not exposed to the hottest zone", "experimental_run", "SPAN_15175EA3A8B2A2D82E5B")
    add_run("COUNTER_CH4_GT1000", "counter-flow CH4 extended into >1000 C hot zone", "quartz reactor with adjustable alumina counter-flow tube", ">1000 exposure before re-nucleation zone", "CH4", "20-70 sccm counter-flow", "front-fed ferrocene/thiophene in bulk H2", "CNT aerogel formed after methane reached the hot zone; product contained many graphitic impurities", "experimental_run", "SPAN_15175EA3A8B2A2D82E5B")
    tables["review_issue_log"].extend((
        issue_row(f"{source_id}_ISSUE_AXIAL_001", source_id, f"{source_id}_AXIAL_CH4", "series_granularity", "source_run", f"{source_id}_AXIAL_CH4", "data_type", "The paper plots multiple filter positions without tabulated numeric masses; each carbon-source curve is retained as a series summary rather than invented point values.", f"EVD_{source_id}_AXIAL_CH4_PRODUCT", "medium"),
        issue_row(f"{source_id}_ISSUE_COUNTER_001", source_id, f"{source_id}_COUNTER_CH4_GT1000", "condition_range", "reactor_process_gas", f"{source_id}_COUNTER_CH4_GT1000_S01", "temperature_setpoint_C", "Counter-flow methane threshold is reported qualitatively as exposure above 1000 C; exact tube position/temperature for the positive case is not tabulated.", f"EVD_{source_id}_COUNTER_CH4_GT1000_PROC", "medium"),
    ))
    return tables


def build_fe_alumina(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = meta["source_id"]
    tables = make_tables(meta, "One physical CCVD growth run on Fe-doped alpha-alumina ceramic; the H2-only sample is catalyst characterization, not a CNT-production run.")
    run_id = f"{source_id}_FE_ALUMINA_1000C"
    tables["source_run"].append(run_row(source_id, "FE_ALUMINA_1000C", "Fe-doped alpha-Al2O3 ceramic; H2/CH4 CCVD at 1000 C", "Organized high-quality CNTs grew along ceramic steps/kinks, with random CNTs bridging grains elsewhere; overall yield was relatively low."))
    tables["catalyst_system"].append(catalyst_row(run_id, catalyst_label="in-situ Fe nanoparticles from alpha-Al1.8Fe0.2O3 solid-solution ceramic", active_metals="Fe", support_material="polycrystalline Fe-doped alpha-Al2O3 ceramic", metal_ratio_original="alpha-Al1.8Fe0.2O3 powder", precursor_summary="Fe-doped alumina solid-solution powder", preparation_method="combustion synthesis, tape casting and sintering; selective in-situ reduction", preparation_detail="Tape cast, dried 30 min ambient, laminated 45 MPa/70 C/10 min, organics removed 450 C/2 h, sintered 1400-1600 C/2 h in air.", calcination_condition="ceramic sintering 1400-1600 C for 2 h in air", reduction_condition="in-situ in 82 mol% H2 / 18 mol% CH4 while heating to 1000 C", catalyst_particle_size_range_nm="25-30 before carbon exposure for most particles", dispersion_summary="homogeneous over surface and preferentially localized at nanometre-scale steps and kinks"))
    tables["reactor_process_gas"].append(process_row(run_id, 1, "CCVD", reactor_type="CCVD chamber; ceramic substrate in alumina boat", temperature_setpoint_C="1000", temperature_program_summary="heated and cooled at 5 C/min; no dwell at 1000 C", holding_time_min="0", heating_rate_C_min="5", cooling_condition="5 C/min", carbon_source="CH4", carbon_source_flow_original="18 mol% of H2/CH4 mixture", reducing_gas="H2", reducing_gas_flow_original="82 mol% of H2/CH4 mixture", gas_composition_summary="82 mol% H2, 18 mol% CH4; absolute flow not reported"))
    tables["yield_quality"].append(yield_row(run_id, primary_yield_metric="CNT formation and organization", yield_original="relatively low CNT yield; no mass reported", yield_definition_original="Qualitative SEM assessment relative to the number of catalytic nanoparticles.", secondary_result_summary="CNTs organized along steps/kinks; random CNTs bridged grains elsewhere.", CNT_type_reported="CNT including a few-wall/single-wall fraction", CNT_type_confirmed="SWCNT/few-wall CNT evidence present", product_mixture_summary="high-quality organized CNTs with low undesired carbon phase content", CNT_type_evidence="RBM peaks and split G band indicate at least some few-wall and single-wall CNTs.", SWCNT_or_few_wall_evidence_summary="RBM peaks at 115, 120, 132.7, 168.7 and 177.7 cm-1; Raman-derived resonant diameter 1.26-1.95 nm.", RBM_peak_reported="yes", outer_diameter_range_nm="1.26-1.95 Raman-resonant subset", morphology="organized along ceramic steps/kinks; random bridging between grains", alignment_or_array="topographically organized, not a vertically aligned forest", Raman_ratio_type="ID/IG", Raman_ratio_value="0.18", Raman_laser_wavelength_nm="632.82", amorphous_carbon_level="low undesired carbon phases inferred from low ID/IG", characterization_methods="FEG-SEM; Raman"))
    tables["cost_scale_review"].append(cost_row(run_id, scale_evidence_summary="Laboratory ceramic coupon CCVD experiment.", cost_driver_summary="Tape-cast Fe-doped alumina ceramic, 1400-1600 C sintering and 1000 C H2/CH4 CCVD.", safety_risk="Hydrogen/methane at 1000 C and high-temperature ceramic processing.", emission_or_waste="Organic binder burnout and CCVD off-gas; not quantified."))
    evidence4(tables, store, source_id, run_id, "SPAN_1F8C08E96E38E6B8EB0A", "SPAN_1F8C08E96E38E6B8EB0A", "SPAN_018BBA1939B85F9A91A8")
    tables["review_issue_log"].append(issue_row(f"{source_id}_ISSUE_DIAM_001", source_id, run_id, "measurement_scope", "yield_quality", f"{run_id}_PROD", "outer_diameter_range_nm", "The 1.26-1.95 nm range is calculated from resonant RBM peaks and describes only the Raman-visible subset, not the full CNT diameter distribution.", f"EVD_{run_id}_PRODUCT", "medium"))
    return tables


def build_membrane_vacnt(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = meta["source_id"]
    tables = make_tables(meta, "One water-assisted VACNT growth run; parylene infiltration, annealing, plasma opening and HF release are post-growth membrane fabrication stages.")
    run_id = f"{source_id}_VACNT_815C_10S"
    tables["source_run"].append(run_row(source_id, "VACNT_815C_10S", "Fe/Al2O3/Si water-assisted CVD VACNT forest", "A 10 s water-assisted ethylene CVD produced an 8-10 micrometre forest of aligned few-wall CNTs, later embedded in parylene."))
    tables["catalyst_system"].append(catalyst_row(run_id, catalyst_label="1.4 nm Fe / approximately 40 nm Al2O3 / Si(100)", active_metals="Fe", support_material="Al2O3 bilayer support on Si(100)", metal_ratio_original="1.4 nm Fe and approximately 40 nm Al2O3 films", precursor_summary="evaporated Fe/Al2O3 bilayer films", preparation_method="film evaporation", preparation_detail="Al2O3/Fe bilayer films evaporated on Si(100).", catalyst_particle_size_qualifier="film thicknesses, not nanoparticle sizes"))
    tables["reactor_process_gas"].append(process_row(run_id, 1, "water_assisted_CVD", reactor_type="thermal CVD reactor", temperature_setpoint_C="815", holding_time_min="0.1667", carbon_source="ethylene", carbon_source_flow_original="100 sccm", carbon_source_flow_sccm="100", reducing_gas="H2", inert_gas="Ar", total_flow_original="600 sccm Ar/H2 carrier plus 100 sccm ethylene", total_flow_sccm="700", cofeed_or_reactive_gas="water vapour", cofeed_flow_original="100-200 ppm", gas_composition_summary="100 sccm ethylene, 600 sccm total Ar/H2 carrier and 100-200 ppm water vapour", process_note="Growth duration reported as 10 seconds."))
    tables["reactor_process_gas"].append(process_row(run_id, 2, "composite_membrane_fabrication", reactor_type="low-pressure parylene CVD plus thermal/plasma post-processing", reactor_setup_summary="Parylene infiltrated at 0.1 Torr/room temperature to 10 micrometre film, annealed 375 C 1 h in Ar, Ar/O2 plasma etched, then 50% HF released from Si.", temperature_setpoint_C="room_temperature; anneal 375", holding_time_min="parylene about 500 min at 1.2 micrometre/h; anneal 60 min; top plasma 90 min; backside plasma 5 min", pressure_original="0.1 Torr during parylene CVD", pressure_kPa="0.013332", carbon_source="para-xylene monomer for parylene matrix, not CNT growth", cofeed_or_reactive_gas="Ar/O2 plasma with 71.4% O2", process_note="Post-growth membrane fabrication, not a new CNT synthesis run."))
    tables["yield_quality"].append(yield_row(run_id, primary_yield_metric="VACNT forest formation", yield_original="8-10 micrometre forest height; no mass yield", yield_definition_original="As-grown forest height after a 10 s growth.", secondary_result_summary="Typical CNT diameter about 7 nm, three graphitic walls and IG/ID about 2.8; no measurable TGA residue above 750 C in air.", CNT_type_reported="vertically aligned carbon nanotubes", CNT_type_confirmed="few-wall CNT", product_mixture_summary="high-purity VACNT forest subsequently embedded in parylene", CNT_type_evidence="HRTEM showed approximately three walls; TGA showed no measurable residue.", SWCNT_or_few_wall_evidence_summary="three graphitic walls by HRTEM", outer_diameter_mean_nm="7", wall_number_summary="3", length_summary="forest height 8-10 micrometres", morphology="highly aligned continuous VACNT forest", alignment_or_array="vertically aligned forest", Raman_ratio_type="IG/ID", Raman_ratio_value="2.8", TGA_carbon_content_wt_percent="approximately 100 (no measurable residue; not a calibrated purity number)", purity_basis="TGA no measurable residue after heating above 750 C in air", characterization_methods="SEM; HRTEM; TGA; Raman", post_treatment_or_purification="parylene infiltration, 375 C Ar anneal, Ar/O2 plasma tip opening and 50% HF substrate release", purification_condition="not a CNT purification; membrane fabrication sequence"))
    tables["cost_scale_review"].append(cost_row(run_id, scale_evidence_summary="Laboratory Si-wafer VACNT/composite membrane.", cost_driver_summary="815 C CVD, ethylene/H2/Ar/water, parylene deposition, 375 C anneal, 95 min plasma etching and HF release.", safety_risk="Flammable CVD gases, oxidative plasma and concentrated HF.", emission_or_waste="CVD/parylene exhaust, etched polymer and HF-containing Si waste; not quantified."))
    evidence4(tables, store, source_id, run_id, "SPAN_443C3D4B6824DA3C0756", "SPAN_443C3D4B6824DA3C0756", "SPAN_2F256E6823930D621965")
    add_evidence(tables, store, source_id, run_id, "POST", "reactor_process_gas", f"{run_id}_S02", "record_level", "SPAN_0319B303BC98065DC79C", "Parylene/anneal/plasma/HF membrane fabrication and Raman retention.")
    tables["review_issue_log"].append(issue_row(f"{source_id}_ISSUE_TGA_001", source_id, run_id, "measurement_limit", "yield_quality", f"{run_id}_PROD", "TGA_carbon_content_wt_percent", "No measurable TGA residue supports high purity but does not justify a more precise numerical purity than approximately 100%; it is not a mass yield.", f"EVD_{run_id}_PRODUCT", "medium"))
    return tables


BUILDERS: dict[str, Callable[[dict[str, Any], EvidenceStore], dict[str, list[dict[str, str]]]]] = {
    "LIT_29053831AED49C65": build_pecvd_wire,
    "LIT_2AF904451035F138": build_temperature_vacnt,
    "LIT_2CBAB1EE4362DD19": build_aerogel,
    "LIT_308D1442E521B6DD": build_fe_alumina,
    "LIT_34447B54D64C4FF1": build_membrane_vacnt,
}


def main() -> None:
    metadata = load_metadata("B")
    store = EvidenceStore()
    metrics: list[dict[str, Any]] = []
    try:
        for source_id in SOURCE_IDS:
            metrics.append(publish_package(source_id, BUILDERS[source_id](metadata[source_id], store)))
    finally:
        store.close()
    result = {"batch_id": BATCH_NAME, "sources": metrics, "total_runs": sum(item["row_counts"]["source_run"] for item in metrics), "status": "completed_needs_review"}
    (REPORT_ROOT / "manual_batch_011_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
