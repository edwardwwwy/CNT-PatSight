#!/usr/bin/env python3
"""Transcribe the seventh five-paper B-class batch into eight-table packages."""

from __future__ import annotations

import json
from typing import Any, Callable

from scripts.extraction.batch_common import ROOT, TABLES, EvidenceStore, catalyst_row, cost_row, issue_row, load_metadata, master_row, process_row, run_row, yield_row
from scripts.extraction.build_b_class_batch_001 import add_evidence, publish_package

BATCH_ID = "B_CLASS_371_20260719"
REPORT_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
BATCH_NUMBER = 15
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
SOURCE_IDS = ("LIT_6048271303BD7143", "LIT_60EA741AF22F1B37", "LIT_65C8BD1BF4B591DD", "LIT_66DB00E917C24EAC", "LIT_68B8A2A5415EBF90")


def make_tables(meta: dict[str, Any], scope: str) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    master = master_row(meta, scope)
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{meta['source_id']}.parsed.json"
    master["notes"] = f"Source-specific transcription for {BATCH_NAME}."
    tables["source_master"].append(master)
    return tables


def ev4(tables: dict[str, list[dict[str, str]]], store: EvidenceStore, sid: str, rid: str, cat: str, proc: str, prod: str, review: bool = False) -> None:
    status = "review_assessment" if review else "reported"
    add_evidence(tables, store, sid, rid, "CAT", "catalyst_system", f"{rid}_CAT", "record_level", cat, "Catalyst/material basis.", value_status=status)
    add_evidence(tables, store, sid, rid, "PROC", "reactor_process_gas", f"{rid}_S01", "record_level", proc, "Process condition or model definition.", value_status=status)
    add_evidence(tables, store, sid, rid, "PRODUCT", "yield_quality", f"{rid}_PROD", "record_level", prod, "Reported product/result.", value_status=status)
    add_evidence(tables, store, sid, rid, "SCALE", "cost_scale_review", rid, "record_level", proc, "Scale/resource context.", confidence="medium", value_status="review_assessment")


def build_ddm(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    sid = meta["source_id"]
    tables = make_tables(meta, "Six matched spray-pyrolysis catalyst screening runs for methane decomposition; detailed CNT metrics retained only where measured.")
    records = (
        ("NI_AL", "Ni/Al2O3", "Ni", "Al2O3", "Ni 40 wt.%; Al2O3 60 wt.%", "800", "600", "3.13", "15.6", "CNT, 30-40 nm; longer/more crystalline; ID/IG 1.25; about 9 g/gcat final"),
        ("NICU_MG", "Ni-Cu/MgO", "Ni; Cu", "MgO", "Ni 50 wt.%; Cu 5 wt.%; MgO 45 wt.%", "500", "650", "5.37", "9.0", "CNT, 30-40 nm; ID/IG 1.63; about 16 g/gcat final; <2.2 wt.% residue after acid purification"),
        ("COMO_MG", "Co-Mo/MgO", "Co; Mo", "MgO", "Co 3 wt.%; Mo 17 wt.%; MgO 80 wt.%", "800", "700", "0.31", "", "carbon deposit; CNT-specific morphology not resolved for this screening row"),
        ("NI_SI", "Ni/SiO2", "Ni", "SiO2", "Ni 10 wt.%; SiO2 90 wt.%", "400", "550", "0", "", "no carbon yield in the three-hour screening run"),
        ("FE_AL", "Fe/Al2O3", "Fe", "Al2O3", "Fe 29 wt.%; Al2O3 71 wt.%", "750", "700", "0.26", "", "low carbon deposit; CNT-specific morphology not resolved for this screening row"),
        ("NI_MG", "Ni/MgO", "Ni", "MgO", "Ni 71 wt.%; MgO 29 wt.%", "500", "670", "0.12", "", "low carbon deposit; CNT-specific morphology not resolved for this screening row"),
    )
    for code, label, metals, support, comp, calc, temp, hourly, particle, outcome in records:
        rid = f"{sid}_{code}"
        total = float(hourly) * 3
        tables["source_run"].append(run_row(sid, code, f"{label} methane decomposition at {temp} C", f"Three-hour carbon productivity {hourly} g/gcat/h ({total:g} g/gcat cumulative by table basis); {outcome}."))
        tables["catalyst_system"].append(catalyst_row(rid, catalyst_label=label, active_metals=metals, support_material=support, metal_ratio_original=comp, precursor_summary="metal nitrates (plus ammonium molybdate/TEOS where applicable), P123, ethanol, water and HNO3", preparation_method="spray-pyrolysis-assisted one-pot EISA", preparation_detail="P123 precursor solution aerosolized by 1.7 MHz ultrasonic nebulizer into 700 C quartz tube under 10 L/min N2; bag-filter collection at 100-130 C.", calcination_condition=f"air at {calc} C", reduction_condition=f"4% H2/Ar, 400 sccm, 2 h at catalyst-specific reduction temperature", catalyst_particle_size_mean_nm=particle, catalyst_particle_size_qualifier="XRD Scherrer Ni crystallite size" if particle else "not_reported"))
        tables["reactor_process_gas"].append(process_row(rid, 1, "direct_methane_decomposition", reactor_type="three-inch-ID horizontal quartz tube furnace; ceramic boat", catalyst_loading_mass_g="0.2", temperature_setpoint_C=temp, holding_time_min="180", carbon_source="CH4", carbon_source_flow_original="200 mL/min", carbon_source_flow_sccm="200", inert_gas="N2", inert_gas_flow_original="200 mL/min", inert_gas_flow_sccm="200", total_flow_original="400 mL/min", total_flow_sccm="400", GHSV_or_residence_time="120 L gcat-1 h-1", gas_composition_summary="50% CH4/N2 after 4% H2/Ar reduction and one-hour N2 ramp purge"))
        confirmed = "CNT" if code in {"NI_AL", "NICU_MG"} else "not_applicable" if hourly == "0" else "carbon_deposit_unresolved"
        tables["yield_quality"].append(yield_row(rid, primary_yield_metric="three-hour carbon productivity", yield_original=f"{hourly} g carbon gcat-1 h-1 for 3 h; cumulative {total:g} g/gcat", yield_definition_original="Table 1 carbon weight gain normalized by catalyst mass and reaction time.", yield_value_standardized=hourly, yield_unit_standardized="g carbon/gcat/h", CNT_yield_per_catalyst_g_gcat=f"{total:g}", CNT_productivity_g_gcat_h=hourly, secondary_result_summary=outcome, CNT_type_reported="CNT" if confirmed == "CNT" else "carbon product", CNT_type_confirmed=confirmed, product_mixture_summary=outcome, CNT_type_evidence="TEM/Raman/TGA for selected Ni catalysts" if confirmed == "CNT" else "screening carbon weight only", outer_diameter_range_nm="30-40" if confirmed == "CNT" else "", morphology="base-growth CNT" if confirmed == "CNT" else outcome, Raman_ratio_type="ID/IG" if code in {"NI_AL", "NICU_MG"} else "", Raman_ratio_value="1.25" if code == "NI_AL" else "1.63" if code == "NICU_MG" else "", characterization_methods="gravimetry; TEM; Raman; TGA; XRD"))
        tables["cost_scale_review"].append(cost_row(rid, scale_evidence_summary="Laboratory 0.2 g catalyst, three-hour methane-decomposition run.", reactor_capacity_or_throughput=f"{total:g} g carbon per g catalyst over 3 h", cost_driver_summary="Spray pyrolysis/EISA catalyst, 4% H2 reduction, 550-700 C reaction and methane/nitrogen.", safety_risk="Methane/hydrogen at high temperature; nitrate/acid catalyst preparation.", emission_or_waste="Hydrogen-containing DDM exhaust and spent supported catalyst; HCl purification for selected CNTs."))
        ev4(tables, store, sid, rid, "SPAN_3CB3C6F7DFEFCD02BAA7", "SPAN_33FF0B0400AF474B309E", "SPAN_195320981F7F272FD2A0")
    tables["review_issue_log"].append(issue_row(f"{sid}_ISSUE_PRODUCT_001", sid, f"{sid}_COMO_MG", "critical_data_gap", "yield_quality", f"{sid}_COMO_MG_PROD", "CNT_type_confirmed", "Table 1 quantifies total carbon for all six catalysts, but source-specific CNT morphology is deeply characterized only for Ni/Al2O3 and Ni-Cu/MgO.", f"EVD_{sid}_COMO_MG_PRODUCT", "high"))
    return tables


def build_lca(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    sid = meta["source_id"]
    tables = make_tables(meta, "Two ex-ante modeled CNT-production scenarios at the common functional unit of 100 t/y, 90%-purity MWCNT; no author laboratory run.")
    records = (
        ("MODEL_MSCC_ET", "molten-salt CO2 capture/electrochemical transformation", "brass cathode; Inconel 718 anode", "BaCO3/Na2CO3 molten electrolyte", "770", "CO2", "MSCC-ET showed lower climate-change, non-renewable-energy and ozone-depletion impacts; MEA capture integration mitigates about 716.6 t CO2-eq per 100 t MWCNT"),
        ("MODEL_CCVD", "inclined mobile-bed catalytic CVD", "Ni-Mo", "MgO", "not_reported_in_article_model_summary", "natural gas", "CCVD outperformed MSCC-ET in several non-climate impact categories; selected process yields 5-20 nm MWCNT at modeled 90% purity"),
    )
    for code, route, metals, support, temp, feed, outcome in records:
        rid = f"{sid}_{code}"
        rr = run_row(sid, code, f"Ex-ante LCA: {route}", outcome, confidence="medium")
        rr["data_type"] = "modeled_process_scenario"
        rr["target_track"] = "CNT_production_LCA"
        tables["source_run"].append(rr)
        tables["catalyst_system"].append(catalyst_row(rid, catalyst_label=metals, active_metals=metals, support_material=support, precursor_summary="literature-derived/process-model material inventory", preparation_method="modeled upstream supply", phase_or_state_summary="scenario input; not synthesized by article authors"))
        tables["reactor_process_gas"].append(process_row(rid, 1, "modeled_CNT_process", reactor_type=route, temperature_setpoint_C=temp, holding_time_min="modeled continuous annual production", carbon_source=feed, pressure_original="scenario-specific/not fully reported in main text", pressure_kPa="", process_note="Ex-ante cradle-to-gate model scaled to 100 t MWCNT/year at 90% product purity; not an experimental run."))
        tables["yield_quality"].append(yield_row(rid, primary_yield_metric="modeled functional-unit product", yield_original="100 t/y MWCNT product at 90% purity", yield_definition_original="Common ex-ante LCA functional unit; remaining 10% is cathode or spent-catalyst residue.", secondary_result_summary=outcome, CNT_type_reported="multi-walled carbon nanotubes", CNT_type_confirmed="modeled MWCNT product", product_mixture_summary="90% MWCNT, 10% residual electrode/catalyst particles", CNT_type_evidence="selected literature technology and process modeling", outer_diameter_range_nm="5-20", characterization_methods="ex-ante LCA/process modeling"))
        tables["cost_scale_review"].append(cost_row(rid, scale_level_demonstrated="modeled_industrial_scale", scale_level_claimed="100_t_per_year", scale_evidence_summary="Cradle-to-gate ex-ante model with functional unit 100 t MWCNT/year at 90% purity.", reactor_capacity_or_throughput="100 t MWCNT/year functional unit", quantitative_cost_reported="relative feed-cost statement only" if code == "MODEL_CCVD" else "not_reported", quantitative_cost_summary="Natural gas stated 99.9% cheaper per tonne than ethylene" if code == "MODEL_CCVD" else "No direct monetary cost; environmental inventory modeled.", cost_driver_summary="Electricity and electrode/electrolyte materials" if code == "MODEL_MSCC_ET" else "Natural gas, Ni-Mo/MgO, thermal reactor and five-step purification", safety_risk="High-temperature molten salt/electrolysis" if code == "MODEL_MSCC_ET" else "Natural gas at elevated temperature and acid purification", emission_or_waste=outcome))
        evidence = "SPAN_1FE39C505037B7A2E5D5" if code == "MODEL_MSCC_ET" else "SPAN_1CF331213290373402E6"
        ev4(tables, store, sid, rid, evidence, evidence, "SPAN_17203E89D42DBE8A51C9", review=True)
    tables["review_issue_log"].append(issue_row(f"{sid}_ISSUE_MODEL_001", sid, f"{sid}_MODEL_MSCC_ET", "modeled_not_experimental", "source_run", f"{sid}_MODEL_MSCC_ET", "data_type", "Both rows are ex-ante scaled scenarios assembled from literature, expert input and modeling; they are not author-generated CNT synthesis experiments.", f"EVD_{sid}_MODEL_MSCC_ET_PROC;EVD_{sid}_MODEL_CCVD_PROC", "high"))
    return tables


def build_semiconducting(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    sid = meta["source_id"]
    tables = make_tables(meta, "Main partially carbon-coated Co catalyst, exposed-Co control, and a larger-exposed-area reduction series summary.")
    records = (
        ("PARTIAL_CO", "partially carbon-coated Co nanoparticles", "500 C H2 5 min then 700 C 5 min", "experimental_run", "mean SWCNT diameter 1.7 nm; >95% semiconducting by stated result (98-99% by Raman/absorption; 96% by electron diffraction); about 10 micrometre length"),
        ("EXPOSED_CO", "fully exposed Co nanoparticles", "air 750 C 5 min removes carbon coating", "experimental_control", "broad RBM distribution containing both semiconducting and metallic SWCNTs"),
        ("EXPOSURE_SERIES", "partially coated Co with larger exposed area", "H2 reduction changed to 700 C 10 min and 800 C 10 min", "experimental_series_summary", "mean SWCNT diameter 2.1 nm and semiconducting content >96% for the reported tuned samples"),
    )
    for code, label, treatment, dtype, outcome in records:
        rid = f"{sid}_{code}"
        rr = run_row(sid, code, label, outcome, confidence="medium" if dtype.endswith("summary") else "high")
        rr["data_type"] = dtype
        tables["source_run"].append(rr)
        tables["catalyst_system"].append(catalyst_row(rid, catalyst_label=label, active_metals="Co", support_material="Si/300 nm SiO2 patterned by PS-b-P4VP nanodomains", precursor_summary="0.25 wt.% PS-b-P4VP and 1 mmol/L K3[Co(CN)6]", preparation_method="block-copolymer self-assembly/metal-complex adsorption/plasma and H2 reduction", preparation_detail="PS-b-P4VP spin-coated at 5000 rpm for 2 min, solvent-vapour annealed, immersed in K3[Co(CN)6] 3 min, dried 60 C 20 min and air-plasma treated 10 min.", reduction_condition=treatment, catalyst_particle_size_mean_nm="3.1 for main partially coated catalyst", catalyst_particle_size_qualifier="TEM mean; >90% in 2.5-4.5 nm for main catalyst", phase_or_state_summary=label))
        tables["reactor_process_gas"].append(process_row(rid, 1, "ethanol_CVD", reactor_type="25 mm diameter quartz tube in horizontal furnace", temperature_setpoint_C="700", holding_time_min="10-25", carbon_source="ethanol vapour", carbon_source_flow_original="75 sccm Ar through ethanol bubbler at 35 C", carbon_source_flow_sccm="not_convertible_from_bubbler_flow", reducing_gas="H2", reducing_gas_flow_original="200 sccm", reducing_gas_flow_sccm="200", inert_gas="Ar carrier", inert_gas_flow_original="75 sccm through ethanol bubbler", inert_gas_flow_sccm="75", total_flow_original="275 sccm carrier/reducing gas plus ethanol vapour", total_flow_sccm="275", gas_composition_summary="ethanol carried by 75 sccm Ar with 200 sccm H2"))
        tables["yield_quality"].append(yield_row(rid, primary_yield_metric="SWCNT diameter/electronic-type distribution", yield_original=outcome, yield_definition_original="TEM/Raman/UV-vis-NIR/electron-diffraction characterization; no mass yield.", secondary_result_summary=outcome, CNT_type_reported="single-wall carbon nanotubes", CNT_type_confirmed="SWCNT", product_mixture_summary=outcome, CNT_type_evidence="TEM, Raman RBM, UV-vis-NIR and electron diffraction", outer_diameter_range_nm="1.7 mean" if code == "PARTIAL_CO" else "2.1 mean" if code == "EXPOSURE_SERIES" else "broad/not_tabulated", length_summary="about 10 micrometres for main sample", morphology="isolated straight SWCNTs randomly dispersed on substrate", Raman_ratio_type="RBM/electronic-type assignment", Raman_ratio_value="narrow around 141 cm-1 for main; broad for exposed control", characterization_methods="AFM; SEM; TEM; Raman; UV-vis-NIR; electron diffraction; TFT testing"))
        tables["cost_scale_review"].append(cost_row(rid, scale_evidence_summary="Laboratory patterned Si/SiO2 substrate CVD.", cost_driver_summary="Block-copolymer nanolithography, cobalt complex, plasma treatment, 700 C ethanol/H2 CVD.", safety_risk="Hydrogen/ethanol at 700 C; cyanometallate precursor and plasma.", emission_or_waste="Organic-solvent/polymer waste, cobalt-containing substrate and CVD exhaust."))
        ev4(tables, store, sid, rid, "SPAN_245794DED2503EF9072B", "SPAN_35998E3DF954E6DC5A5B", "SPAN_7A17878DDC01492C98C7" if code == "EXPOSURE_SERIES" else "SPAN_09B09D95F0CB8BC7C5DA")
    tables["review_issue_log"].append(issue_row(f"{sid}_ISSUE_SERIES_001", sid, f"{sid}_EXPOSURE_SERIES", "series_aggregation", "source_run", f"{sid}_EXPOSURE_SERIES", "run_summary", "The 700 C and 800 C reduction variants are described together with one aggregate 2.1 nm/>96% outcome, so they remain one series-summary row.", f"EVD_{sid}_EXPOSURE_SERIES_PRODUCT", "medium"))
    return tables


def build_plastic_composites(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    sid = meta["source_id"]
    tables = make_tables(meta, "Six explicitly named CNT feed/treatment states fabricated as 2 wt.% epoxy composites; CNT-growth conditions referenced to prior work are not invented.")
    records = (
        ("CCNT", "commercial pristine CNT", "commercial as received", "clean, well-dispersed commercial CNT reference"),
        ("PCNT", "waste-polypropylene-derived CNT", "as-produced in prior two-stage Fe-CVD work", "intertwined/rough CNT with amorphous carbon, carbon fibres and Fe/Al2O3 residue"),
        ("P_CCNT", "HNO3-purified commercial CNT", "1 g CNT in 150 mL 20 wt.% HNO3, 40 C, 24 h", "purified/shortened commercial CNT"),
        ("P_PCNT", "HNO3-purified plastic-derived CNT", "1 g CNT in 150 mL 20 wt.% HNO3, 40 C, 24 h", "purified/shortened plastic-derived CNT; substantial encapsulated/support residue remains"),
        ("M_CCNT", "mixed-acid carboxylated commercial CNT", "0.5 g purified CNT in 80 mL H2SO4/HNO3 3:1; sonicate 5 h", "carboxyl-functionalized commercial CNT"),
        ("M_PCNT", "mixed-acid carboxylated plastic-derived CNT", "0.5 g purified CNT in 80 mL H2SO4/HNO3 3:1; sonicate 5 h", "carboxyl-functionalized plastic-derived CNT; at 2 wt.% epoxy: Young's modulus 3776.9 MPa, tensile strength 37.3 MPa, fracture strain 6.32%, fracture strength 111.7 MPa"),
    )
    for code, label, treatment, outcome in records:
        rid = f"{sid}_{code}_EP2"
        rr = run_row(sid, f"{code}_EP2", f"2 wt.% {label} in epoxy", outcome, confidence="medium" if code != "M_PCNT" else "high")
        rr["data_type"] = "experimental_post_processing"
        rr["target_track"] = "CNT_composite_fabrication"
        tables["source_run"].append(rr)
        origin = "commercial CNT" if "CCNT" in code else "waste-PP-derived CNT from prior-work two-stage fixed-bed Fe catalyst route"
        tables["catalyst_system"].append(catalyst_row(rid, catalyst_label=label, active_metals="not_applicable; residual Fe reported for pCNT", support_material="E51 epoxy resin", precursor_summary=origin, preparation_method="CNT purification/functionalization followed by epoxy dispersion", preparation_detail=treatment, post_preparation_condition="2 wt.% CNT manually blended, sonicated 4 h at 500 W/40 kHz, EP:amine curing agent 6:1, degassed 25 min", phase_or_state_summary="CNT-filled cured epoxy composite"))
        tables["reactor_process_gas"].append(process_row(rid, 1, "CNT_epoxy_composite_fabrication", reactor_type="ultrasonic dispersion, vacuum degassing and air oven curing", temperature_setpoint_C="25 to 120 ramp over 1 h; hold 120", holding_time_min="240 curing after 240 min sonication and 25 min degassing", carbon_source=origin, pressure_original="vacuum degassing then air-pressure cure", pressure_kPa="", process_note=f"CNT treatment: {treatment}; composite contains 2 wt.% named CNT state."))
        tables["yield_quality"].append(yield_row(rid, primary_yield_metric="epoxy-composite mechanical performance", yield_original=outcome, yield_definition_original="Mechanical comparison at 2 wt.% CNT loading; exact values retained where text reports them.", secondary_result_summary=outcome, CNT_type_reported="CNT", CNT_type_confirmed="CNT input material", product_mixture_summary="2 wt.% CNT in cured E51 epoxy/amine matrix", CNT_type_evidence="TEM/Raman/TGA/FTIR/XPS on CNT input and mechanical/SEM composite testing", outer_diameter_range_nm="few to tens for pCNT; commercial 10-20", length_summary="pCNT at least 20 micrometres; commercial 10-30 micrometres", morphology=outcome, characterization_methods="TEM; TGA; Raman 532 nm; FTIR; XPS; tensile/flexural testing; fracture SEM", post_treatment_or_purification=treatment, application_property_summary=outcome))
        tables["cost_scale_review"].append(cost_row(rid, scale_evidence_summary="Laboratory 2 wt.% CNT/epoxy coupon fabrication; tests repeated three times.", cost_driver_summary="CNT feed, nitric/sulfuric acid treatment where applicable, 4 h high-power sonication and 4 h oven cure.", safety_risk="Concentrated HNO3/H2SO4, CNT aerosol, high-power sonication and epoxy/amine exposure.", emission_or_waste="Acid wash water, CNT/metal residue and thermoset composite waste."))
        cat_span = "SPAN_35CC2459A15D4E4367A4" if code in {"CCNT", "PCNT"} else "SPAN_B24BBB20D034DF2797DA"
        ev4(tables, store, sid, rid, cat_span, "SPAN_4343085580C3F1B72FF8", "SPAN_0F45D4E80B6B0572E238")
    tables["review_issue_log"].append(issue_row(f"{sid}_ISSUE_GROWTH_001", sid, f"{sid}_PCNT_EP2", "critical_data_gap", "reactor_process_gas", f"{sid}_PCNT_EP2_S01", "carbon_source", "The pCNT growth recipe is only referenced to prior work; this package records the source's actual purification/functionalization/composite experiments and does not reconstruct missing CVD conditions.", f"EVD_{sid}_PCNT_EP2_CAT", "high"))
    return tables


def build_integrated(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    sid = meta["source_id"]
    tables = make_tables(meta, "One explicitly reported patterned-island methane-CVD SWCNT growth and device-fabrication run.")
    code = "PATTERNED_FEMO_CH4"
    rid = f"{sid}_{code}"
    tables["source_run"].append(run_row(sid, code, "Fe-Mo/alumina patterned-island methane CVD", "Predominantly individual low-defect SWCNTs bridging patterned catalyst islands; small amount of >5 nm SWCNT ropes."))
    tables["catalyst_system"].append(catalyst_row(rid, catalyst_label="Fe-Mo/alumina nanoparticle ink on patterned islands", active_metals="Fe; Mo", support_material="15 mg alumina nanoparticles on SiO2/Si", metal_ratio_original="0.05 mmol Fe(NO3)3.9H2O; 0.015 mmol Mo2(acac)2; 15 mg alumina", precursor_summary="Fe nitrate, molybdenum acetylacetonate and alumina in 15 mL methanol", preparation_method="24 h stirring, 1 h sonication and patterned PMMA deposition/liftoff", preparation_detail="Catalyst deposited in 5 x 5 micrometre lithographic islands."))
    tables["reactor_process_gas"].append(process_row(rid, 1, "methane_CVD", reactor_type="1-inch-diameter tube furnace", temperature_setpoint_C="900", holding_time_min="10", carbon_source="CH4", carbon_source_flow_original="5000 cm3/min", carbon_source_flow_sccm="5000", total_flow_original="5000 cm3/min methane; carrier/reducing gases not reported", total_flow_sccm="5000", gas_composition_summary="methane flow; other gases/pressure not reported"))
    tables["yield_quality"].append(yield_row(rid, primary_yield_metric="patterned SWCNT bridge formation", yield_original="predominantly individual SWCNTs with few structural defects; small amount of SWCNT ropes >5 nm", yield_definition_original="SEM/AFM morphology; no mass yield.", secondary_result_summary="Individual SWCNT lengths 0.3-10 micrometres controlled by catalyst-island separation; two-terminal resistance as low as 20 kohm at low temperature.", CNT_type_reported="single-walled carbon nanotubes", CNT_type_confirmed="SWCNT", product_mixture_summary="individual SWCNT plus minor ropes", CNT_type_evidence="SEM and AFM; electrical transport", outer_diameter_range_nm="individual SWCNT; ropes >5 nm", length_summary="0.3-10 micrometres", morphology="individual tubes bridging patterned islands", characterization_methods="SEM; AFM; electrical transport"))
    tables["cost_scale_review"].append(cost_row(rid, scale_evidence_summary="Laboratory lithographically patterned device substrate.", cost_driver_summary="Multiple EBL steps, Fe-Mo/alumina ink, 900 C furnace and 5000 sccm methane.", safety_risk="High methane flow at 900 C; methanol and nanocatalyst handling.", emission_or_waste="Methane CVD exhaust, solvent/lithography waste and metal-coated substrates."))
    ev4(tables, store, sid, rid, "SPAN_07C9913A6FE495403BAA", "SPAN_07C9913A6FE495403BAA", "SPAN_07C9913A6FE495403BAA")
    return tables


BUILDERS: dict[str, Callable[[dict[str, Any], EvidenceStore], dict[str, list[dict[str, str]]]]] = {
    "LIT_6048271303BD7143": build_ddm,
    "LIT_60EA741AF22F1B37": build_lca,
    "LIT_65C8BD1BF4B591DD": build_semiconducting,
    "LIT_66DB00E917C24EAC": build_plastic_composites,
    "LIT_68B8A2A5415EBF90": build_integrated,
}


def main() -> None:
    metadata = load_metadata("B")
    store = EvidenceStore()
    metrics: list[dict[str, Any]] = []
    try:
        for sid in SOURCE_IDS:
            metrics.append(publish_package(sid, BUILDERS[sid](metadata[sid], store)))
    finally:
        store.close()
    result = {"batch_id": BATCH_NAME, "sources": metrics, "total_runs": sum(x["row_counts"]["source_run"] for x in metrics), "status": "completed_needs_review"}
    (REPORT_ROOT / "manual_batch_015_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
