#!/usr/bin/env python3
"""Transcribe the second five-paper B-class batch into eight-table packages."""

from __future__ import annotations

import json
from typing import Any, Callable

from scripts.extraction.batch_common import (
    ROOT,
    TABLES,
    EvidenceStore,
    catalyst_row,
    cost_row,
    issue_row,
    load_metadata,
    master_row,
    process_row,
    run_row,
    yield_row,
)
from scripts.extraction.build_b_class_batch_001 import add_evidence, publish_package


BATCH_ID = "B_CLASS_371_20260719"
REPORT_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
BATCH_NUMBER = 10
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
SOURCE_IDS = (
    "LIT_1E15BC8013D45B19",
    "LIT_2220A162F1244DB9",
    "LIT_25D339F1DCC67CED",
    "LIT_26E8CF0B49DA2722",
    "LIT_2771CADE088A800B",
)


def new_tables(metadata: dict[str, Any], scope: str) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    master = master_row(metadata, scope)
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{metadata['source_id']}.parsed.json"
    master["notes"] = f"Source-specific transcription for {BATCH_NAME}; physical run boundaries follow the printed experimental matrix."
    tables["source_master"].append(master)
    return tables


def add_standard_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    source_id: str,
    run_id: str,
    catalyst_span: str,
    process_span: str,
    product_span: str,
    scale_span: str | None = None,
) -> None:
    add_evidence(tables, store, source_id, run_id, "CAT", "catalyst_system", f"{run_id}_CAT", "record_level", catalyst_span, "Catalyst identity, support and preparation.")
    add_evidence(tables, store, source_id, run_id, "PROC", "reactor_process_gas", f"{run_id}_S01", "record_level", process_span, "Reported CNT-production reactor condition.")
    add_evidence(tables, store, source_id, run_id, "PRODUCT", "yield_quality", f"{run_id}_PROD", "record_level", product_span, "Reported carbon/CNT outcome and characterization.")
    add_evidence(tables, store, source_id, run_id, "SCALE", "cost_scale_review", run_id, "record_level", scale_span or process_span, "Laboratory scale and material/energy context.", confidence="medium", value_status="review_assessment")


def build_vacnt(metadata: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    tables = new_tables(metadata, "One water-assisted CVD VACNT growth run; subsequent rolling, peeling and drying are retained as post-processing rather than new CNT-growth runs.")
    run_id = f"{source_id}_VACNT_815C_10MIN"
    tables["source_run"].append(run_row(source_id, "VACNT_815C_10MIN", "Fe/Al2O3/Si water-assisted CVD VACNT array", "Ethylene water-assisted CVD at 815 C for 10 min produced an approximately 1 mm tall VACNT array, later rolled into an aligned membrane."))
    tables["catalyst_system"].append(catalyst_row(
        run_id,
        catalyst_label="Fe(1.4 nm)/Al2O3(40 nm)/Si thin-film catalyst",
        active_metals="Fe",
        support_material="40 nm Al2O3 on Si",
        metal_ratio_original="1.4 nm Fe film on 40 nm Al2O3 film",
        precursor_summary="predeposited Fe/Al2O3 thin films",
        preparation_method="thin-film catalyst stack; deposition method not reported in extracted text",
        preparation_detail="Fe(1.4 nm)/Al2O3(40 nm)/Si catalyst substrate used for VACNT growth.",
        catalyst_particle_size_qualifier="nominal Fe film thickness, not particle diameter",
    ))
    tables["reactor_process_gas"].append(process_row(
        run_id, 1, "water_assisted_CVD",
        reactor_type="thermal CVD reactor",
        reactor_setup_summary="VACNT growth on Fe/Al2O3/Si substrate.",
        temperature_setpoint_C="815",
        holding_time_min="10",
        carbon_source="ethylene",
        carbon_source_flow_original="100 sccm",
        carbon_source_flow_sccm="100",
        reducing_gas="H2",
        inert_gas="Ar",
        total_flow_original="650 sccm Ar/H2 carrier plus 100 sccm ethylene",
        total_flow_sccm="750",
        cofeed_or_reactive_gas="water vapor",
        cofeed_flow_original="100-200 ppm",
        gas_composition_summary="100 sccm C2H4 with Ar/H2 carrier gas (650 sccm total carrier) and 100-200 ppm water vapor",
    ))
    tables["reactor_process_gas"].append(process_row(
        run_id, 2, "mechanical_membrane_fabrication",
        reactor_type="two-glass-slide rolling apparatus",
        reactor_setup_summary="As-grown array pushed over and repeatedly rolled/stacked into a dense aligned membrane; peeled by DI-water sonication.",
        temperature_setpoint_C="not_applicable",
        holding_time_min="not_reported",
        carbon_source="not_applicable",
        pressure_original="ambient",
        pressure_kPa="101.325",
        process_note="Post-growth membrane fabrication, not a second CNT synthesis run; vacuum dried at 60 C for 4 h.",
    ))
    tables["yield_quality"].append(yield_row(
        run_id,
        primary_yield_metric="VACNT array formation",
        yield_original="approximately 1 mm array height; no mass yield reported",
        yield_definition_original="As-grown vertical array height before rolling.",
        secondary_result_summary="Rolled membrane thickness about 120 micrometres, pore size about 10 nm and CNT areal density about 1e11 cm-2.",
        CNT_type_reported="vertically aligned carbon nanotubes",
        CNT_type_confirmed="few-wall CNT",
        product_mixture_summary="High-purity aligned CNT array/membrane; no metal catalyst particles observed by TEM.",
        CNT_type_evidence="TEM showed typical outer diameter about 5 nm and approximately three graphitic walls.",
        SWCNT_or_few_wall_evidence_summary="Approximately three graphitic walls by TEM.",
        outer_diameter_mean_nm="5",
        wall_number_summary="about 3 graphitic walls",
        length_summary="array height about 1 mm before rolling",
        morphology="vertically aligned array; mechanically densified aligned membrane",
        alignment_or_array="vertically aligned array; rolled aligned membrane",
        Raman_ratio_type="IG/ID",
        Raman_ratio_value="12.3",
        amorphous_carbon_level="not quantified; source describes high purity",
        characterization_methods="SEM; TEM; Raman; membrane transport testing",
        post_treatment_or_purification="mechanical rolling; DI-water sonication release; vacuum drying",
        purification_condition="vacuum dried at 60 C for 4 h after peeling",
    ))
    tables["cost_scale_review"].append(cost_row(
        run_id,
        scale_evidence_summary="Laboratory substrate-scale VACNT array and membrane fabrication.",
        cost_driver_summary="815 C furnace, ethylene, hydrogen/argon, water dosing and Fe/Al2O3/Si substrate.",
        safety_risk="Flammable ethylene/hydrogen at high temperature.",
        emission_or_waste="CVD off-gas and substrate/membrane trimming; not quantified.",
    ))
    add_standard_evidence(tables, store, source_id, run_id, "SPAN_1DEA67D0F6963C33DD13", "SPAN_1DEA67D0F6963C33DD13", "SPAN_0E22A6656532D9AF4FC2")
    add_evidence(tables, store, source_id, run_id, "POST", "reactor_process_gas", f"{run_id}_S02", "record_level", "SPAN_0976AD8F3FF68F1BC1D6", "Rolling, peeling and vacuum-drying post-process.")
    tables["review_issue_log"].append(issue_row(
        f"{source_id}_ISSUE_YIELD_001", source_id, run_id, "critical_data_gap", "yield_quality", f"{run_id}_PROD", "yield_original",
        "The source reports array and membrane dimensions but no CNT mass yield; membrane thickness after rolling must not be treated as as-grown array height.", f"EVD_{run_id}_PRODUCT", "medium",
    ))
    return tables


def build_flame(metadata: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    tables = new_tables(metadata, "Acid-dipping and flame-height physical series with the shared 165 s/6 mm optimum deduplicated, plus one explicitly separated computational model record.")

    def add_physical(code: str, label: str, acid_s: str, hab_mm: str, outcome: str, product_span: str) -> None:
        run_id = f"{source_id}_{code}"
        has_cnt = outcome.startswith("CNT")
        tables["source_run"].append(run_row(source_id, code, label, f"Methane co-flow diffusion-flame exposure for 10 min at {hab_mm} mm HAB after {acid_s} s nitric-acid pretreatment: {outcome}."))
        tables["catalyst_system"].append(catalyst_row(
            run_id,
            catalyst_label="oxidized pure Ni wire" if acid_s != "0" else "untreated pure Ni wire",
            active_metals="Ni",
            support_material="self-supported Ni wire",
            precursor_summary="0.4 mm diameter, 50 mm long pure Ni wire",
            preparation_method="solvent/water sonication followed by nitric-acid oxidation" if acid_s != "0" else "solvent/water sonication; no acid oxidation",
            preparation_detail=f"Ten wires per 30 mL bath; acetone sonication 15 min, DI-water sonication 15 min; 65% HNO3 dip {acid_s} s.",
            activation_condition=f"65% HNO3 dip for {acid_s} s" if acid_s != "0" else "no nitric-acid pretreatment",
            phase_or_state_summary="Ni oxide nanoparticles formed on the wire after acid pretreatment/flame exposure" if acid_s != "0" else "suitable Ni oxide nanoparticles absent",
        ))
        tables["reactor_process_gas"].append(process_row(
            run_id, 1, "flame_CVD",
            reactor_type="18 mm ID methane co-flow diffusion-flame burner",
            reactor_setup_summary=f"Ni wire/50 mm square #40 stainless-steel mesh positioned at {hab_mm} mm height above burner; atmospheric visible flame about 100 mm high.",
            reactor_size_summary="18 mm methane tube concentric with 24 mm co-flow tube",
            holding_time_min="10",
            carbon_source="CH4",
            carbon_source_flow_original="0.48 slpm",
            carbon_source_flow_sccm="480",
            inert_gas="N2",
            cofeed_or_reactive_gas="O2",
            total_flow_original="4 slpm N2/O2 co-flow at 3:1 plus 0.48 slpm CH4",
            total_flow_sccm="4480",
            gas_composition_summary="0.48 slpm pure methane; 4 slpm outer N2/O2 co-flow at 3:1",
            GHSV_or_residence_time=f"wire sampling height {hab_mm} mm HAB",
        ))
        tables["yield_quality"].append(yield_row(
            run_id,
            primary_yield_metric="CNT growth-region outcome",
            yield_original=outcome,
            yield_definition_original="Observed axial length/presence of CNT deposit on the sampled wire; not a gravimetric yield.",
            CNT_type_reported="multiwall CNT" if has_cnt else "no CNT observed",
            CNT_type_confirmed="MWCNT" if has_cnt else "not_applicable",
            product_mixture_summary=outcome,
            CNT_type_evidence="SEM/TEM; sampled CNTs were multiwalled with Ni-oxide tip particles." if has_cnt else "SEM observation reported no CNT.",
            outer_diameter_mean_nm="25" if has_cnt else "",
            outer_diameter_range_nm="9-27" if has_cnt else "",
            wall_number_summary="multiwalled" if has_cnt else "",
            morphology="curly, entangled and randomly oriented" if has_cnt else outcome,
            characterization_methods="SEM; TEM; EDX" if has_cnt else "SEM",
        ))
        tables["cost_scale_review"].append(cost_row(
            run_id,
            scale_evidence_summary="Laboratory wire-sampling flame synthesis.",
            cost_driver_summary="Methane flame, N2/O2 co-flow, Ni wire and concentrated nitric acid.",
            safety_risk="Open methane flame and 65% nitric acid; hot metal substrate.",
            emission_or_waste="Combustion exhaust, soot at high HAB and spent nitric-acid bath; not quantified.",
        ))
        add_standard_evidence(tables, store, source_id, run_id, "SPAN_203BB77D6C849A7AD03D", "SPAN_203BB77D6C849A7AD03D", product_span)

    acid_series = (
        ("ACID_000_HAB6", "untreated Ni wire; HAB 6 mm", "0", "6", "no CNT observed", "SPAN_0F86D2693517DA48EF08"),
        ("ACID_075_HAB6", "75 s acid dip; HAB 6 mm", "75", "6", "no CNT observed (<90 s)", "SPAN_13398CB945C0EAEBD2A2"),
        ("ACID_090_HAB6", "90 s acid dip; HAB 6 mm", "90", "6", "CNT present; minimal growth region", "SPAN_13398CB945C0EAEBD2A2"),
        ("ACID_165_HAB6", "165 s acid dip; HAB 6 mm optimum", "165", "6", "CNT present; maximum growth region about 4 mm", "SPAN_13398CB945C0EAEBD2A2"),
        ("ACID_210_HAB6", "210 s acid dip; HAB 6 mm", "210", "6", "CNT present; minimal growth region", "SPAN_13398CB945C0EAEBD2A2"),
        ("ACID_260_HAB6", "260 s acid dip; HAB 6 mm", "260", "6", "no observable CNT deposit", "SPAN_2DA783D1F1361BD303B7"),
    )
    for args in acid_series:
        add_physical(*args)
    hab_series = (
        ("ACID165_HAB1", "165 s acid dip; HAB 1 mm", "165", "1", "no dark CNT spot", "SPAN_3C14B1160444A0E181F6"),
        ("ACID165_HAB3", "165 s acid dip; HAB 3 mm", "165", "3", "no dark CNT spot", "SPAN_3C14B1160444A0E181F6"),
        ("ACID165_HAB4", "165 s acid dip; HAB 4 mm", "165", "4", "CNT present; growth region about 2 mm", "SPAN_3C14B1160444A0E181F6"),
        ("ACID165_HAB5", "165 s acid dip; HAB 5 mm", "165", "5", "CNT present; growth region about 3 mm", "SPAN_680A5CBC885E23EACE4E"),
        ("ACID165_HAB7", "165 s acid dip; HAB 7 mm", "165", "7", "soot deposit; no CNT", "SPAN_680A5CBC885E23EACE4E"),
        ("ACID165_HAB10", "165 s acid dip; HAB 10 mm", "165", "10", "soot deposit; no CNT", "SPAN_680A5CBC885E23EACE4E"),
    )
    for args in hab_series:
        add_physical(*args)

    model_id = f"{source_id}_CFD_CNT_GROWTH_MODEL"
    model_run = run_row(source_id, "CFD_CNT_GROWTH_MODEL", "CFD/ODE methane-flame CNT growth model", "OpenFOAM flame fields coupled to a CNT growth-rate/length model predicted the high-growth region near 7 mm HAB but did not reproduce no-growth/soot regions.", confidence="medium")
    model_run["data_type"] = "computational_model_record"
    model_run["target_track"] = "CNT_growth_modeling"
    tables["source_run"].append(model_run)
    tables["catalyst_system"].append(catalyst_row(model_id, catalyst_label="modelled Ni/NiO particle catalyst", active_metals="Ni", support_material="Ni wire boundary", preparation_method="computational representation of acid-oxidized Ni wire", phase_or_state_summary="NiO growth sites represented through model inputs"))
    tables["reactor_process_gas"].append(process_row(model_id, 1, "CFD_multiscale_model", reactor_type="axisymmetric methane co-flow diffusion-flame domain", reactor_setup_summary="OpenFOAM CFD temperature/species fields supplied to CNT growth ODE model.", holding_time_min="10", carbon_source="CH4", carbon_source_flow_original="0.48 slpm experimental boundary", inert_gas="N2", cofeed_or_reactive_gas="O2", gas_composition_summary="Experimental methane/N2/O2 boundary conditions", GHSV_or_residence_time="predicted along HAB"))
    tables["yield_quality"].append(yield_row(model_id, primary_yield_metric="predicted CNT growth-rate/length profile", yield_original="maximum predicted near 7 mm HAB", yield_definition_original="Model output, not a physical yield.", secondary_result_summary="Reasonable growth-region agreement, but the model predicted growth where experiments gave no growth or soot.", CNT_type_reported="modelled CNT", CNT_type_confirmed="not_applicable", product_mixture_summary="computational output", CNT_type_evidence="not_applicable", characterization_methods="OpenFOAM CFD coupled to multiscale CNT growth equations"))
    tables["cost_scale_review"].append(cost_row(model_id, scale_evidence_summary="Computational record calibrated against a laboratory flame.", cost_driver_summary="CFD/ODE computation and experimental boundary data.", safety_risk="not_applicable to model record", emission_or_waste="not_applicable to model record"))
    add_standard_evidence(tables, store, source_id, model_id, "SPAN_12DBE7C63E6AA2A00878", "SPAN_12DBE7C63E6AA2A00878", "SPAN_AB1DD8F3513AB9B676E9")
    tables["review_issue_log"].extend((
        issue_row(f"{source_id}_ISSUE_ACID_001", source_id, f"{source_id}_ACID_260_HAB6", "source_inconsistency", "yield_quality", f"{source_id}_ACID_260_HAB6_PROD", "yield_original", "Narrative thresholds are inconsistent (beyond 210 s versus more than 260 s); 260 s is retained as the explicit no-growth endpoint stated in the conclusion.", f"EVD_{source_id}_ACID_260_HAB6_PRODUCT", "medium"),
        issue_row(f"{source_id}_ISSUE_MODEL_001", source_id, model_id, "model_scope", "yield_quality", f"{model_id}_PROD", "secondary_result_summary", "The model excludes soot chemistry and cannot reproduce the experimental no-growth/soot regions; its prediction must not be merged with physical run outcomes.", f"EVD_{model_id}_PRODUCT", "high"),
    ))
    return tables


def build_sphere(metadata: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    tables = new_tables(metadata, "Four unique HDPE two-stage pyrolysis/CVD runs: the 1.0 mol/L Ni-precursor temperature series and the 0.1 mol/L comparison at 800 C.")
    records = (
        ("NI10_600", "1.0/sphere; 600 C", "1.0", "600", "no CNT observed; mainly amorphous carbon", "not_reported", "not_reported", "not_reported"),
        ("NI10_700", "1.0/sphere; 700 C", "1.0", "700", "CNT observed; small/disordered", "1.0", "1.2", "not_reported"),
        ("NI10_800", "1.0/sphere; 800 C", "1.0", "800", "abundant aligned/uniform CNT", "7.5", "1.0", "55.2 +/- 7.9"),
        ("NI01_800", "0.1/sphere; 800 C", "0.1", "800", "filamentous carbon mostly CNT", "6.2", "1.0", "40.2 +/- 8.6"),
    )
    for code, label, concentration, temp, outcome, cnt_yield, amorphous, diameter in records:
        run_id = f"{source_id}_{code}"
        has_cnt = cnt_yield != "not_reported" or temp != "600"
        tables["source_run"].append(run_row(source_id, code, label, f"1 g HDPE pyrolysed at 500 C; vapours contacted {concentration}/sphere Ni-alumina at {temp} C for a 60 min total experiment. {outcome}."))
        tables["catalyst_system"].append(catalyst_row(
            run_id, catalyst_label=f"{concentration}/sphere Ni on spherical Al2O3", active_metals="Ni", support_material="spherical Al2O3",
            metal_ratio_original=f"prepared to saturation with {concentration} mol/L Ni(NO3)2 solution; final Ni wt.% not reported",
            precursor_summary="Ni(NO3)2 aqueous solution", preparation_method="incipient/saturation impregnation by dropwise addition",
            preparation_detail="Alumina spheres dried 100 C for 24 h; nickel nitrate solution added dropwise to saturation; wet catalyst dried 100 C for 24 h.",
            drying_condition="100 C for 24 h before and after impregnation", calcination_condition="air, 750 C, 2 C/min, 3 h",
        ))
        tables["reactor_process_gas"].append(process_row(run_id, 1, "plastic_pyrolysis", reactor_type="two-stage fixed-bed reactor", reactor_setup_summary="1 g HDPE in first stage; catalytic sphere bed in second stage.", temperature_setpoint_C="500", holding_time_min="not separately reported", carbon_source="HDPE", carbon_source_flow_original="1 g batch", inert_gas="N2", inert_gas_flow_original="100 mL/min", inert_gas_flow_sccm="100", total_flow_original="100 mL/min N2 plus HDPE vapour", process_note="First-stage plastic pyrolysis."))
        tables["reactor_process_gas"].append(process_row(run_id, 2, "catalytic_CVD", reactor_type="second stage of two-stage fixed-bed reactor", temperature_setpoint_C=temp, holding_time_min="60 total reaction time", carbon_source="HDPE pyrolysis vapours", inert_gas="N2", inert_gas_flow_original="100 mL/min", inert_gas_flow_sccm="100", total_flow_original="100 mL/min N2 plus pyrolysis vapours", process_note="Second-stage catalytic carbon deposition; 60 min is reported for the total reaction."))
        tables["yield_quality"].append(yield_row(
            run_id, primary_yield_metric="TPO-separated filamentous carbon assigned to CNT", yield_original=(f"{cnt_yield} wt.% CNT; {amorphous} wt.% amorphous carbon" if cnt_yield != "not_reported" else outcome),
            yield_definition_original="TPO carbon fractions relative to plastic feed; oxidation below about 550 C assigned amorphous carbon and higher-temperature filamentous fraction checked by SEM/TEM.",
            yield_value_standardized=cnt_yield if cnt_yield != "not_reported" else "", yield_unit_standardized="wt.% of HDPE feed" if cnt_yield != "not_reported" else "",
            secondary_result_summary=outcome, CNT_type_reported="CNT" if has_cnt else "no CNT observed", CNT_type_confirmed="CNT" if has_cnt else "not_applicable",
            product_mixture_summary=f"{outcome}; amorphous carbon {amorphous} wt.%" if amorphous != "not_reported" else outcome,
            CNT_type_evidence="SEM/TEM and TPO fractionation" if has_cnt else "SEM found no CNT at 600 C.",
            outer_diameter_mean_nm=diameter.split(" +/- ")[0] if "+/-" in diameter else "", outer_diameter_range_nm=diameter if "+/-" in diameter else "",
            morphology=outcome, amorphous_carbon_level=f"{amorphous} wt.% of plastic feed by TPO" if amorphous != "not_reported" else "qualitatively dominant; exact fraction not reported",
            characterization_methods="SEM; TEM; TGA-TPO; DTG-TPO; ImageJ diameter analysis",
        ))
        tables["cost_scale_review"].append(cost_row(run_id, scale_evidence_summary="Laboratory 1 g HDPE batch in a two-stage fixed-bed reactor.", cost_driver_summary="750 C catalyst calcination, 500 C pyrolysis, 600-800 C catalyst stage and nitrogen.", safety_risk="Hot plastic pyrolysis vapours and flammable decomposition gases.", emission_or_waste="Oil/gas coproducts, amorphous carbon and spent Ni/alumina catalyst; not fully inventoried."))
        add_evidence(tables, store, source_id, run_id, "CAT", "catalyst_system", f"{run_id}_CAT", "record_level", "SPAN_258000F0C6E098447EEE", "Spherical-alumina Ni catalyst preparation.")
        add_evidence(tables, store, source_id, run_id, "PYR", "reactor_process_gas", f"{run_id}_S01", "record_level", "SPAN_1ACE9202638D76A15660", "Two-stage HDPE process, temperature, nitrogen and time.")
        add_evidence(tables, store, source_id, run_id, "CVD", "reactor_process_gas", f"{run_id}_S02", "record_level", "SPAN_1ACE9202638D76A15660", "Second-stage catalytic temperature series.")
        product_span = "SPAN_1F1963DFD768CB2E865C" if temp == "600" else "SPAN_4C0C57952777DFD87A2D" if concentration == "1.0" else "SPAN_2C0554AA16A7D86515B0"
        add_evidence(tables, store, source_id, run_id, "PRODUCT", "yield_quality", f"{run_id}_PROD", "record_level", product_span, "SEM/TEM/TPO CNT outcome and carbon fractions.")
        add_evidence(tables, store, source_id, run_id, "SCALE", "cost_scale_review", run_id, "record_level", "SPAN_1ACE9202638D76A15660", "Laboratory 1 g two-stage batch.", confidence="medium", value_status="review_assessment")
    tables["review_issue_log"].append(issue_row(f"{source_id}_ISSUE_TPO_001", source_id, f"{source_id}_NI10_700", "definition_ambiguity", "yield_quality", f"{source_id}_NI10_700_PROD", "yield_original", "TPO separates amorphous and thermally stable filamentous carbon; CNT assignment is supported by microscopy, but the values are not purified CNT product yields.", f"EVD_{source_id}_NI10_700_PRODUCT", "medium"))
    return tables


def build_pp_foam(metadata: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    tables = new_tables(metadata, "Five unique Ni-foam WPP runs from two intersecting series: CVD temperature at 5 C/min and pyrolysis heating rate at 700 C.")
    records = (
        ("HR05_CVD600", "5 C/min; CVD 600 C", "5", "600", "43.12", "55", "1.09"),
        ("HR05_CVD700", "5 C/min; CVD 700 C", "5", "700", "39.34", "30", "0.98"),
        ("HR05_CVD800", "5 C/min; CVD 800 C", "5", "800", "35.67", "26", "0.879"),
        ("HR10_CVD700", "10 C/min; CVD 700 C", "10", "700", "23.12", "74", "1.06"),
        ("HR20_CVD700", "20 C/min; CVD 700 C", "20", "700", "11.02", "145", "1.072"),
    )
    for code, label, rate, cvd_temp, carbon_yield, diameter, raman in records:
        run_id = f"{source_id}_{code}"
        tables["source_run"].append(run_row(source_id, code, label, f"5 g waste PP pyrolysed to 500 C at {rate} C/min and held 30 min; uncondensed vapours contacted 0.15 g activated Ni foam at {cvd_temp} C. Carbon deposit {carbon_yield}% of Ni-foam mass."))
        tables["catalyst_system"].append(catalyst_row(
            run_id, catalyst_label="commercial nickel foam", active_metals="Ni", support_material="self-supported porous Ni foam", preparation_method="commercial foam oxidation and reduction",
            preparation_detail="0.15 g Ni foam used in each experiment.", calcination_condition="oxidized in static air at 500 C for 30 min",
            reduction_condition="600 C for 1 h under 100 mL/min H2/N2; mixture composition not recoverable from parsed line",
            phase_or_state_summary="three-dimensional porous metallic Ni foam after activation",
        ))
        tables["reactor_process_gas"].append(process_row(run_id, 1, "plastic_pyrolysis", reactor_type="80 cm x 4 cm ID stainless-steel horizontal tube reactor", reactor_setup_summary="First stage of double-stage pyrolysis-condenser-catalytic reactor; charged with 5 g WPP.", temperature_setpoint_C="500", temperature_program_summary=f"heated to 500 C at {rate} C/min and held 30 min", holding_time_min="30", heating_rate_C_min=rate, carbon_source="waste polypropylene", carbon_source_flow_original="5 g batch", inert_gas="N2", inert_gas_flow_original="60 mL/min", inert_gas_flow_sccm="60", total_flow_original="60 mL/min N2 plus WPP vapours"))
        tables["reactor_process_gas"].append(process_row(run_id, 2, "catalytic_CVD", reactor_type="80 cm x 4 cm ID stainless-steel horizontal tube reactor", reactor_setup_summary="Second stage containing 0.15 g Ni foam; condensable liquid removed between stages.", catalyst_loading_mass_g="0.15", temperature_setpoint_C=cvd_temp, holding_time_min="30 (coupled to first-stage hold)", carbon_source="uncondensed WPP pyrolysis gases", inert_gas="N2", inert_gas_flow_original="60 mL/min", inert_gas_flow_sccm="60", total_flow_original="60 mL/min N2 plus uncondensed pyrolysis gases"))
        tables["yield_quality"].append(yield_row(
            run_id, primary_yield_metric="carbon deposited relative to initial Ni-foam mass", yield_original=f"{carbon_yield}% carbon yield",
            yield_definition_original="(mass of catalyst plus deposited carbon after CVD - initial Ni-foam mass) / initial Ni-foam mass x 100; total deposited carbon, described/characterized as CNT-rich product.",
            CNT_yield_per_catalyst_g_gcat=str(round(float(carbon_yield) / 100, 4)),
            secondary_result_summary=f"MWCNT mean diameter {diameter} nm; ID/IG {raman}.", CNT_type_reported="multiwall carbon nanotubes", CNT_type_confirmed="MWCNT",
            product_mixture_summary="CNT-rich carbon deposit on nickel foam; total carbon yield is not a purified CNT fraction.", CNT_type_evidence="SEM/TEM morphology and graphitic (002) XRD peak.",
            outer_diameter_mean_nm=diameter, wall_number_summary="multiwalled", morphology="CNTs on three-dimensional Ni foam; diameter becomes narrower with lower heating rate/higher CVD temperature",
            Raman_ratio_type="ID/IG", Raman_ratio_value=raman, characterization_methods="SEM; TEM; XRD; Raman; gravimetry",
        ))
        tables["cost_scale_review"].append(cost_row(run_id, scale_evidence_summary="Laboratory 5 g WPP two-stage batch with 0.15 g Ni foam.", reactor_capacity_or_throughput="5 g WPP per batch", cost_driver_summary="500 C pyrolysis, 600-800 C catalytic stage, Ni foam and nitrogen/hydrogen activation gas.", safety_risk="Hot WPP pyrolysis gases; hydrogen activation; combustible gas products.", emission_or_waste="Pyrolysis oil, char, non-condensable gas and carbon-coated Ni foam; product splits reported for pyrolysis but no full emissions inventory."))
        add_evidence(tables, store, source_id, run_id, "CAT", "catalyst_system", f"{run_id}_CAT", "record_level", "SPAN_14AF377211D069F30583", "Ni-foam mass and activation.")
        add_evidence(tables, store, source_id, run_id, "PYR", "reactor_process_gas", f"{run_id}_S01", "record_level", "SPAN_6CDCB2A7E061034C7990", "WPP charge, heating rates, reactor and nitrogen flow.")
        add_evidence(tables, store, source_id, run_id, "CVD", "reactor_process_gas", f"{run_id}_S02", "record_level", "SPAN_1573F84E05FCC094079A", "Second-stage CVD temperature and 30 min hold context.")
        product_span = "SPAN_26272C61E0D13F906168" if rate == "5" else "SPAN_501A4BA48E785AA3F02B"
        add_evidence(tables, store, source_id, run_id, "PRODUCT", "yield_quality", f"{run_id}_PROD", "record_level", product_span, "Carbon yield, diameter and Raman ratio.")
        add_evidence(tables, store, source_id, run_id, "SCALE", "cost_scale_review", run_id, "record_level", "SPAN_6CDCB2A7E061034C7990", "Five-gram laboratory batch context.", confidence="medium", value_status="review_assessment")
    tables["review_issue_log"].extend((
        issue_row(f"{source_id}_ISSUE_BASIS_001", source_id, f"{source_id}_HR05_CVD700", "definition_ambiguity", "yield_quality", f"{source_id}_HR05_CVD700_PROD", "yield_original", "The reported percentage is total mass gain relative to Ni-foam mass, not purified CNT yield relative to plastic feed.", f"EVD_{source_id}_HR05_CVD700_PRODUCT", "high"),
        issue_row(f"{source_id}_ISSUE_REDUCTION_001", source_id, f"{source_id}_HR05_CVD700", "critical_data_gap", "catalyst_system", f"{source_id}_HR05_CVD700_CAT", "reduction_condition", "Parsed text preserves the total H2/N2 flow but loses the printed mixture percentage at the page break; no composition is inferred.", f"EVD_{source_id}_HR05_CVD700_CAT", "medium"),
    ))
    return tables


def build_mixed_plastic(metadata: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = metadata["source_id"]
    tables = new_tables(metadata, "Four physical runs differing only by porous support for a 10 wt.% Ni-Fe (1:3 molar) catalyst in two-stage post-consumer mixed-plastic pyrolysis-catalysis.")
    records = (
        ("ZSM5", "Ni-Fe/ZSM5", "ZSM-5", "38", "254.83", "0.248", "50.00", "18-25", "moderate; thin amorphous layer on some CNTs", "not_reported"),
        ("MCM41", "Ni-Fe/MCM41", "MCM-41", "25", "478.80", "0.539", "55.60", "about 24", "highest purity; almost no noticeable amorphous carbon", "0.51"),
        ("NKF5", "Ni-Fe/NKF5", "NKF-5", "25", "255.09", "0.123", "36.60", "about 12 and about 22", "moderate purity; bimodal diameter", "not_reported"),
        ("BETA", "Ni-Fe/Beta", "H-Beta", "38", "318.21", "0.215", "47.00", "12-25 overall source range", "lowest quality/uniformity; more amorphous carbon", "not_reported"),
    )
    for code, label, support, si_al, bet, pore_vol, carbon_yield, diameter, quality, raman in records:
        run_id = f"{source_id}_{code}"
        tables["source_run"].append(run_row(source_id, code, label, f"1 g mixed post-consumer plastics pyrolysed at 500 C and vapours catalysed over 0.5 g {label} at 800 C; total carbon deposition {carbon_yield} wt.% of plastic feed."))
        tables["catalyst_system"].append(catalyst_row(
            run_id, catalyst_label=f"10 wt.% Ni-Fe/{support}", active_metals="Ni; Fe", support_material=support,
            metal_ratio_original=f"Ni:Fe molar ratio 1:3; total metal loading 10 wt.%; support SiO2:Al2O3 molar ratio {si_al}", metal_ratio_standardized="Ni:Fe=1:3 mol/mol",
            precursor_summary="Ni(NO3)2 hydrate and Fe(NO3)3 hydrate in ethanol", preparation_method="wet impregnation",
            preparation_detail="Support pre-calcined 550 C for 6 h; nitrates dissolved in ethanol at 50 C, support added, stirred 4 h and dried overnight at 100 C.",
            drying_condition="100 C overnight", calcination_condition="air, 800 C, 10 C/min, 3 h", reduction_condition="no ex-situ reduction; in-situ reduction by product H2",
            BET_surface_area_m2_g=bet, pore_volume_cm3_g=pore_vol, phase_or_state_summary="Ni-Fe oxides before reaction; Fe-Ni alloy particles identified after reaction",
        ))
        tables["reactor_process_gas"].append(process_row(run_id, 1, "plastic_pyrolysis", reactor_type="two-stage quartz fixed-bed reactor", reactor_setup_summary="1 g mixed waste plastic in a quartz crucible in the first stage.", temperature_setpoint_C="500", temperature_program_summary="heated to 500 C at 30 C/min and held 15 min", holding_time_min="15", heating_rate_C_min="30", carbon_source="post-consumer mixed plastics (40% HDPE, 35% LDPE, 20% PP, 5% PS)", carbon_source_flow_original="1 g batch", inert_gas="N2", inert_gas_flow_original="100 mL/min", inert_gas_flow_sccm="100", total_flow_original="100 mL/min N2 plus plastic vapours"))
        tables["reactor_process_gas"].append(process_row(run_id, 2, "catalytic_CVD", reactor_type="second stage of two-stage quartz fixed-bed reactor", reactor_setup_summary=f"0.5 g {label} in porous quartz crucible.", catalyst_loading_mass_g="0.5", temperature_setpoint_C="800", holding_time_min="15 (coupled to pyrolysis hold)", carbon_source="mixed-plastic pyrolysis vapours", inert_gas="N2", inert_gas_flow_original="100 mL/min", inert_gas_flow_sccm="100", total_flow_original="100 mL/min N2 plus pyrolysis vapours"))
        tables["yield_quality"].append(yield_row(
            run_id, primary_yield_metric="total catalyst carbon deposition relative to plastic feed", yield_original=f"{carbon_yield} wt.% carbon deposition",
            yield_definition_original="Mass difference between fresh and spent catalyst divided by plastic feed mass; total deposited carbon, not purified CNT yield.",
            yield_value_standardized=carbon_yield, yield_unit_standardized="wt.% of mixed-plastic feed", secondary_result_summary=f"Deposits dominated by MWCNT; {quality}.",
            CNT_type_reported="multi-walled carbon nanotubes", CNT_type_confirmed="MWCNT", product_mixture_summary=f"MWCNT-dominated filamentous carbon with support-dependent amorphous carbon; {quality}.",
            CNT_type_evidence="SEM and HRTEM showed dense entangled filamentous carbon dominated by MWCNT with some bamboo-like knots.", outer_diameter_mean_nm="24" if code == "MCM41" else "",
            outer_diameter_range_nm=diameter, wall_number_summary="MCM41 example about 20 graphitic layers; other supports not numerically assigned", length_summary="up to a few micrometres",
            morphology="dense entangled MWCNT; some complete/incomplete bamboo-like knots", Raman_ratio_type="ID/IG" if raman != "not_reported" else "not_reported", Raman_ratio_value=raman,
            amorphous_carbon_level=quality, characterization_methods="TPO; SEM; HRTEM; HAADF-EDXS; XRD; Raman",
        ))
        tables["cost_scale_review"].append(cost_row(run_id, scale_evidence_summary="Laboratory 1 g mixed-plastic batch with 0.5 g catalyst.", reactor_capacity_or_throughput="1 g plastic per batch", cost_driver_summary="Porous zeolite support, Ni/Fe nitrates, 800 C calcination/catalysis and nitrogen.", safety_risk="Hot mixed-plastic pyrolysis vapours and combustible hydrogen/hydrocarbon product gas.", emission_or_waste="Oil, fuel gas and carbon-coated spent catalyst; mixed-plastic additives include oxygen/sulphur impurities."))
        add_evidence(tables, store, source_id, run_id, "CAT", "catalyst_system", f"{run_id}_CAT", "record_level", "SPAN_550CE0188349B240D7B0", "Ni-Fe ratio, loading, support and preparation.")
        add_evidence(tables, store, source_id, run_id, "PYR", "reactor_process_gas", f"{run_id}_S01", "record_level", "SPAN_2FA9467BD6B551E779CA", "Two-stage reactor, feed, catalyst, temperatures and nitrogen flow.")
        add_evidence(tables, store, source_id, run_id, "CVD", "reactor_process_gas", f"{run_id}_S02", "record_level", "SPAN_2FA9467BD6B551E779CA", "Second-stage 800 C catalytic condition.")
        add_evidence(tables, store, source_id, run_id, "YIELD", "yield_quality", f"{run_id}_PROD", "primary_yield_metric;yield_original;yield_definition_original", "SPAN_18B89D3EA835A13AEC64", "Support-resolved carbon deposition values and definition.")
        product_span = "SPAN_94C17CC58B0A63318D9C" if code != "MCM41" else "SPAN_59C531FC6497E4B58BF6"
        add_evidence(tables, store, source_id, run_id, "PRODUCT", "yield_quality", f"{run_id}_PROD", "CNT_type_reported;CNT_type_confirmed;outer_diameter_range_nm;morphology;Raman_ratio_value", product_span, "MWCNT morphology, diameter and support-dependent quality.")
        add_evidence(tables, store, source_id, run_id, "SCALE", "cost_scale_review", run_id, "record_level", "SPAN_2FA9467BD6B551E779CA", "One-gram laboratory batch context.", confidence="medium", value_status="review_assessment")
    tables["review_issue_log"].append(issue_row(f"{source_id}_ISSUE_BASIS_001", source_id, f"{source_id}_MCM41", "definition_ambiguity", "yield_quality", f"{source_id}_MCM41_PROD", "yield_original", "Carbon-deposition wt.% is total carbon mass gain relative to plastic feed; microscopy shows MWCNT dominance but the number is not a purified CNT fraction.", f"EVD_{source_id}_MCM41_YIELD;EVD_{source_id}_MCM41_PRODUCT", "high"))
    return tables


BUILDERS: dict[str, Callable[[dict[str, Any], EvidenceStore], dict[str, list[dict[str, str]]]]] = {
    "LIT_1E15BC8013D45B19": build_vacnt,
    "LIT_2220A162F1244DB9": build_flame,
    "LIT_25D339F1DCC67CED": build_sphere,
    "LIT_26E8CF0B49DA2722": build_pp_foam,
    "LIT_2771CADE088A800B": build_mixed_plastic,
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
    result = {
        "batch_id": BATCH_NAME,
        "sources": metrics,
        "total_runs": sum(item["row_counts"]["source_run"] for item in metrics),
        "status": "completed_needs_review",
    }
    (REPORT_ROOT / "manual_batch_010_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
