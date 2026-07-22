#!/usr/bin/env python3
"""Transcribe five B-class CNT growth or CNT-functionalization papers."""

from __future__ import annotations

import json
from typing import Any, Callable

from scripts.extraction.batch_common import ROOT, TABLES, EvidenceStore, catalyst_row, cost_row, issue_row, load_metadata, master_row, process_row, run_row, yield_row
from scripts.extraction.build_b_class_batch_001 import add_evidence, publish_package

BATCH_ID = "B_CLASS_371_20260719"
REPORT_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
BATCH_NUMBER = 13
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
SOURCE_IDS = ("LIT_4421747A539A3C4E", "LIT_4596780F2CFEE553", "LIT_4B17E877536A6E0E", "LIT_4B3D3C5CD3B8D731", "LIT_4DC70416A368D5D9")


def make_tables(meta: dict[str, Any], scope: str) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    master = master_row(meta, scope)
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{meta['source_id']}.parsed.json"
    master["notes"] = f"Source-specific transcription for {BATCH_NAME}."
    tables["source_master"].append(master)
    return tables


def ev4(tables: dict[str, list[dict[str, str]]], store: EvidenceStore, sid: str, rid: str, cat: str, proc: str, prod: str) -> None:
    add_evidence(tables, store, sid, rid, "CAT", "catalyst_system", f"{rid}_CAT", "record_level", cat, "Catalyst or functional material preparation.")
    add_evidence(tables, store, sid, rid, "PROC", "reactor_process_gas", f"{rid}_S01", "record_level", proc, "Reported process condition.")
    add_evidence(tables, store, sid, rid, "PRODUCT", "yield_quality", f"{rid}_PROD", "record_level", prod, "Reported CNT/material outcome.")
    add_evidence(tables, store, sid, rid, "SCALE", "cost_scale_review", rid, "record_level", proc, "Laboratory scale/resource context.", confidence="medium", value_status="review_assessment")


def build_co_graphene(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    sid = meta["source_id"]
    tables = make_tables(meta, "Four acetylene-CVD temperatures over matched 0.02 g Co3O4/RGO precursor.")
    records = (("G400", "400", "0.033", "1.7", "23.9"), ("G450", "450", "0.055", "2.8", "21.2"), ("G500", "500", "0.075", "3.8", "18.6"), ("G550", "550", "0.1893", "9.5", "10.9"))
    for code, temp, mass, ratio, magnetization in records:
        rid = f"{sid}_{code}"
        tables["source_run"].append(run_row(sid, code, f"Co3O4/RGO acetylene CVD at {temp} C", f"Collected {mass} g Co@CNT-graphene hybrid from 0.02 g precursor; product/catalyst mass ratio about {ratio}."))
        tables["catalyst_system"].append(catalyst_row(rid, catalyst_label="commercial Co3O4/reduced graphene oxide", active_metals="Co", support_material="reduced graphene oxide", metal_ratio_original="0.02 g Co3O4/RGO precursor per run", precursor_summary="Co3O4/RGO", preparation_method="commercial precursor dispersed on ceramic plate", preparation_detail="0.02 g precursor spread on ceramic plate; Co3O4 reduced in situ to Co nanoparticles during acetylene exposure.", phase_or_state_summary="Co nanoparticles encapsulated in/at CNT tips on graphene"))
        tables["reactor_process_gas"].append(process_row(rid, 1, "thermal_CVD", reactor_type="quartz-tube furnace with ceramic plate", temperature_setpoint_C=temp, holding_time_min="120", carbon_source="C2H2", carbon_source_flow_original="not_reported", inert_gas="Ar during heat-up and cooling", gas_composition_summary="acetylene at atmospheric pressure; argon heat-up/cooling; absolute flows not reported"))
        tables["yield_quality"].append(yield_row(rid, primary_yield_metric="total Co@CNT-graphene hybrid mass per precursor mass", yield_original=f"{mass} g product; product/precursor ratio {ratio}", yield_definition_original="Total collected hybrid mass divided by 0.02 g Co3O4/RGO precursor; includes graphene and Co, not CNT-only yield.", yield_value_standardized=ratio, yield_unit_standardized="g hybrid/g precursor", secondary_result_summary=f"CNT content increased with temperature; saturation magnetization {magnetization} emu/g.", CNT_type_reported="carbon nanotubes", CNT_type_confirmed="CNT", product_mixture_summary="ternary Co@CNTs-graphene hybrid", CNT_type_evidence="SEM/TEM and Raman/XRD", morphology="CNTs grown from Co nanoparticles on graphene; tip-growth assignment", Raman_laser_wavelength_nm="514.5", characterization_methods="XRD; Raman; TEM; FE-SEM; FTIR; AFM; magnetometry", application_property_summary=f"saturation magnetization {magnetization} emu/g; microwave absorption characterized"))
        tables["cost_scale_review"].append(cost_row(rid, scale_evidence_summary="Laboratory 0.02 g catalyst-precursor CVD batch.", reactor_capacity_or_throughput=f"{mass} g hybrid after 2 h", cost_driver_summary="Co3O4/RGO precursor, 400-550 C furnace, acetylene and argon.", safety_risk="Acetylene at high temperature; cobalt-containing nanopowder.", emission_or_waste="CVD exhaust and cobalt-containing hybrid/residue."))
        ev4(tables, store, sid, rid, "SPAN_52768DF77E508D3F12D1", "SPAN_52768DF77E508D3F12D1", "SPAN_41293DD81F6BE300A30C")
    tables["review_issue_log"].append(issue_row(f"{sid}_ISSUE_YIELD_001", sid, f"{sid}_G550", "definition_ambiguity", "yield_quality", f"{sid}_G550_PROD", "yield_original", "The product/precursor ratio is total ternary-hybrid mass gain and cannot be interpreted as CNT-only yield.", f"EVD_{sid}_G550_PRODUCT", "high"))
    return tables


def build_dot_pecvd(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    sid = meta["source_id"]
    tables = make_tables(meta, "Three exact C2H2 fractions (15, 20, 25%) at fixed total flow in dc PECVD on 100 nm Ni catalyst dots.")
    records = (("C2H2_15", "15", "hollow VACNT; 60-80 nm diameter"), ("C2H2_20", "20", "intermediate VACNT morphology between hollow tube and fibre-like product"), ("C2H2_25", "25", "bamboo-like/fibre-like VACNT; top 70-80 nm, bottom 100-150 nm; length 3.5 micrometres"))
    for code, fraction, outcome in records:
        rid = f"{sid}_{code}"
        tables["source_run"].append(run_row(sid, code, f"100 nm Ni-dot dc PECVD; C2H2 fraction {fraction}%", outcome))
        tables["catalyst_system"].append(catalyst_row(rid, catalyst_label="100 nm Ni dot array on Cr/Si", active_metals="Ni", support_material="Cr diffusion barrier on Si", metal_ratio_original="100 nm lateral catalyst dots; Ni/Cr film thicknesses not reported", precursor_summary="sputtered Ni and Cr films", preparation_method="RF magnetron sputtering plus e-beam lithography/lift-off", preparation_detail="Cr diffusion barrier and Ni catalyst deposited on Si; 100 nm dot array patterned by electron-beam lithography; 10 micrometre pitch.", activation_condition="NH3 pretreatment at 700 C for 5 min"))
        c2h2 = 150 * float(fraction) / 100
        nh3 = 150 - c2h2
        tables["reactor_process_gas"].append(process_row(rid, 1, "dc_PECVD", reactor_type="cylindrical quartz tube with parallel-diode electrodes about 5 mm apart", temperature_setpoint_C="700", holding_time_min="15", pressure_original="400 Pa", pressure_kPa="0.4", carbon_source="C2H2", carbon_source_flow_original=f"{fraction}% of 150 sccm total", carbon_source_flow_sccm=f"{c2h2:g}", reducing_gas="NH3", reducing_gas_flow_original=f"{100-float(fraction):g}% of 150 sccm total", reducing_gas_flow_sccm=f"{nh3:g}", total_flow_original="150 sccm", total_flow_sccm="150", gas_composition_summary=f"C2H2/NH3 total 150 sccm; applied sample voltage -650 V"))
        tables["yield_quality"].append(yield_row(rid, primary_yield_metric="single-dot VACNT morphology", yield_original=outcome, yield_definition_original="SEM/TEM morphology; no mass yield.", secondary_result_summary=outcome, CNT_type_reported="vertically aligned carbon nanotube", CNT_type_confirmed="MWCNT/bamboo-like CNT" if fraction == "25" else "MWCNT", product_mixture_summary=outcome, CNT_type_evidence="SEM and TEM; catalyst particle at tip", outer_diameter_range_nm="60-80" if fraction == "15" else "70-150" if fraction == "25" else "not_reported", length_summary="3.5 micrometres" if fraction == "25" else "not_reported", morphology=outcome, alignment_or_array="one vertical emitter per 100 nm catalyst dot", characterization_methods="FE-SEM; TEM; optical emission spectroscopy; field emission"))
        tables["cost_scale_review"].append(cost_row(rid, scale_evidence_summary="Laboratory lithographic Si-chip emitter array.", cost_driver_summary="E-beam lithography, Ni/Cr sputtering, 700 C dc plasma and C2H2/NH3.", safety_risk="Acetylene/ammonia, high voltage and hot vacuum/plasma reactor.", emission_or_waste="PECVD exhaust and lithography/metal-film waste."))
        ev4(tables, store, sid, rid, "SPAN_21DAF422DB4C050A962C", "SPAN_21DAF422DB4C050A962C", "SPAN_00CF87177BB50889B1B4")
    return tables


def build_wire_substrates(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    sid = meta["source_id"]
    tables = make_tables(meta, "Eight matched Fe/Al2O3 CVD substrate runs: seven 25 micrometre metal wires and one 7 micrometre carbon fibre.")
    records = (
        ("NB", "niobium wire", "short, dense and aligned MWCNT coating", True),
        ("TA", "tantalum wire", "longer, more randomly oriented MWCNT than Nb", True),
        ("CF", "T650-35 carbon fibre", "longer, more randomly oriented MWCNT than Nb", True),
        ("MO", "molybdenum wire", "sparse/large carbon nanotube structures", True),
        ("W", "tungsten wire", "less-dense large CNT structures", True),
        ("SS", "stainless-steel wire", "less-dense large CNT structures", True),
        ("TI", "titanium wire", "less-dense large CNT structures", True),
        ("PD", "palladium wire", "large-diameter amorphous carbon; not CNT", False),
    )
    for code, substrate, outcome, has_cnt in records:
        rid = f"{sid}_{code}"
        diameter = "7 micrometres" if code == "CF" else "25 micrometres"
        tables["source_run"].append(run_row(sid, code, f"Fe/Al2O3 on {substrate}", outcome))
        tables["catalyst_system"].append(catalyst_row(rid, catalyst_label=f"1 nm Fe / 30 nm Al2O3 on {substrate}", active_metals="Fe", support_material=f"30 nm Al2O3 buffer on {diameter} {substrate}", metal_ratio_original="1 nm Fe film; 30 nm Al2O3", precursor_summary="e-beam evaporated Fe and Al2O3", preparation_method="electron-beam physical vapour deposition", preparation_detail="Line-of-sight coating deposited on one side, producing a half-coated cylindrical substrate.", activation_condition="700 C under 2000 sccm Ar + 200 sccm H2 for 10 min"))
        tables["reactor_process_gas"].append(process_row(rid, 1, "thermal_CVD", reactor_type="quartz-tube CVD reactor", temperature_setpoint_C="700", holding_time_min="5", carbon_source="C2H4", carbon_source_flow_original="10 sccm", carbon_source_flow_sccm="10", reducing_gas="H2", reducing_gas_flow_original="200 sccm", reducing_gas_flow_sccm="200", inert_gas="Ar", inert_gas_flow_original="2000 sccm", inert_gas_flow_sccm="2000", total_flow_original="2210 sccm during growth", total_flow_sccm="2210", gas_composition_summary="10 min Ar/H2 activation then 5 min ethylene growth"))
        tables["yield_quality"].append(yield_row(rid, primary_yield_metric="carbon coating morphology", yield_original=outcome, yield_definition_original="SEM/Raman qualitative substrate comparison; no mass yield.", secondary_result_summary=outcome, CNT_type_reported="multi-walled carbon nanotubes" if has_cnt else "amorphous carbon, not CNT", CNT_type_confirmed="MWCNT" if has_cnt else "not_applicable", product_mixture_summary=outcome, CNT_type_evidence="SEM and Raman" if has_cnt else "SEM morphology assigned amorphous carbon", morphology=outcome, alignment_or_array="aligned array" if code == "NB" else "mixed/random" if has_cnt else "not_applicable", characterization_methods="SEM; Raman; electrochemical characterization"))
        tables["cost_scale_review"].append(cost_row(rid, scale_evidence_summary="Laboratory micro-wire/fibre CVD electrode.", cost_driver_summary="E-beam Fe/Al2O3 coating, 700 C reactor and high Ar/H2 flow.", safety_risk="Hydrogen/ethylene at 700 C and metal-wire handling.", emission_or_waste="CVD exhaust and coated wire/fibre."))
        prod_span = "SPAN_A9D1899618D2BAD220B2" if code in {"MO", "W", "SS", "TI", "PD"} else "SPAN_4C0947BC304500EF383C"
        ev4(tables, store, sid, rid, "SPAN_5E30C49E507420DE6F5C", "SPAN_3B576713C0FBD4A20F07", prod_span)
    tables["review_issue_log"].append(issue_row(f"{sid}_ISSUE_PD_001", sid, f"{sid}_PD", "negative_control", "yield_quality", f"{sid}_PD_PROD", "CNT_type_confirmed", "The Pd condition produced amorphous carbon rather than CNT and is retained as an explicit negative substrate outcome.", f"EVD_{sid}_PD_PRODUCT", "low"))
    return tables


def build_remote_plasma(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    sid = meta["source_id"]
    tables = make_tables(meta, "Three plasma-power points at 775 C and eight 200 W temperature points; the shared 775 C/200 W condition is deduplicated.")
    records = [
        ("P000_T775", "0", "775", "52.2 wt.% SWCNT; 47.8 wt.% amorphous/defective carbon", "not_reported"),
        ("P200_T775", "200", "775", "59.5 wt.% SWCNT; 40.5 wt.% amorphous/defective carbon; optimum; (7,5)+(8,4) >50% semiconducting species", "30.1% (7,5); 20.2% (8,4)"),
        ("P250_T775", "250", "775", "37.6 wt.% SWCNT; 53.2 wt.% amorphous/defective; 4.2 wt.% MWCNT; 5.0 wt.% graphite", "not_reported"),
        ("P200_T625", "200", "625", "few SWCNT; low purity", "not_reported"),
        ("P200_T675", "200", "675", "SWCNT; small-diameter species present", "18.9% (7,3); 24.9% (6,5); 10.7% (7,5); 9.5% (8,4); 5.7% (7,6)"),
        ("P200_T725", "200", "725", "SWCNT; (6,5) dominant", "12.6% (7,3); 25.8% (6,5); 14.9% (7,5); 10.6% (8,4); 6.2% (7,6)"),
        ("P200_T750", "200", "750", "maximum purity/minimum amorphous-carbon region", "5.5% (7,3); 24.0% (6,5); 20.8% (7,5); 17.0% (8,4); 7.9% (7,6)"),
        ("P200_T800", "200", "800", "larger-diameter SWCNT distribution", "10.4% (6,5); 26.6% (7,5); 21.7% (8,4); 13.4% (7,6)"),
        ("P200_T825", "200", "825", "larger-diameter SWCNT distribution", "6.4% (6,5); 24.6% (7,5); 23.4% (8,4); 16.1% (7,6)"),
        ("P200_T875", "200", "875", "few SWCNT; weak RBM/resonant absorption", "not_reported"),
    ]
    for code, power, temp, outcome, chirality in records:
        rid = f"{sid}_{code}"
        tables["source_run"].append(run_row(sid, code, f"Co-MCM-41 ethanol RPE-CVD; {power} W; {temp} C", outcome))
        tables["catalyst_system"].append(catalyst_row(rid, catalyst_label="1 wt.% Co-MCM-41", active_metals="Co", support_material="MCM-41 mesoporous silica", metal_ratio_original="1 wt.% Co", preparation_method="literature Co incorporation into MCM-41; source-specific recipe referenced", calcination_condition="air at 500 C", reduction_condition="80 sccm atmospheric H2, room temperature to 500 C at 10 C/min", BET_surface_area_m2_g=">1000", pore_diameter_nm="narrow distribution FWHM <0.2 nm", phase_or_state_summary="isolated/incorporated Co species; major TPR reduction peak above 800 C"))
        tables["reactor_process_gas"].append(process_row(rid, 1, "remote_plasma_ethanol_CVD", reactor_type="2-inch quartz-tube furnace with 13.56 MHz remote ICP source 21 cm upstream", catalyst_loading_mass_g="0.08", temperature_setpoint_C=temp, holding_time_min="30", pressure_original="ethanol reservoir 2 mbar; reactor evacuated to 0.1 mbar before plasma", pressure_kPa="", carbon_source="ethanol vapour", carbon_source_flow_original="evaporated from 2 mbar reservoir; absolute flow not reported", inert_gas="Ar purge/cooling", cofeed_or_reactive_gas=f"remote ICP {power} W", gas_composition_summary=f"ethanol remote plasma at {power} W; catalyst 21 cm downstream"))
        swcnt_fraction = "59.5" if code == "P200_T775" else "52.2" if code == "P000_T775" else "37.6" if code == "P250_T775" else ""
        tables["yield_quality"].append(yield_row(rid, primary_yield_metric="carbon composition/chirality outcome", yield_original=outcome, yield_definition_original="DTG-deconvoluted carbon fractions for 0/200/250 W at 775 C; PL relative abundance for temperature series.", TGA_carbon_content_wt_percent=swcnt_fraction, purity_basis="SWCNT fraction of carbon deposit by DTG deconvolution" if swcnt_fraction else "PL/Raman/absorption qualitative or chirality-relative result", secondary_result_summary=f"{outcome}; chirality: {chirality}", CNT_type_reported="single-walled carbon nanotubes", CNT_type_confirmed="SWCNT", product_mixture_summary=outcome, CNT_type_evidence="RBM/split-G Raman, UV-vis-NIR, PL and TGA/DTG", SWCNT_or_few_wall_evidence_summary="RBM 100-400 cm-1 and PL-assigned (n,m) species", RBM_peak_reported="yes; weak at 625/875 C", morphology="SWCNT bundles on powder catalyst", Raman_ratio_type="ID/IG trend", Raman_ratio_value="minimum near 200 W / around 750 C; exact plot values not tabulated", characterization_methods="SEM; Raman; UV-vis-NIR; PL; TGA/DTG"))
        tables["cost_scale_review"].append(cost_row(rid, scale_evidence_summary="Laboratory 80 mg catalyst RPE-CVD batch, repeated at least three times.", cost_driver_summary="Mesoporous Co catalyst, vacuum, 13.56 MHz plasma, ethanol and 625-875 C furnace.", safety_risk="Ethanol vapour, hydrogen reduction, RF plasma and vacuum.", emission_or_waste="Carbon/silica/cobalt powder and reactor exhaust; acid purification mentioned for analysis."))
        prod_span = "SPAN_47D38947F26A1A40653D" if temp == "775" else "SPAN_3A0EF257D76A3BE79F0D"
        ev4(tables, store, sid, rid, "SPAN_60D030D0E9D8BE321E37", "SPAN_60D030D0E9D8BE321E37", prod_span)
    tables["review_issue_log"].append(issue_row(f"{sid}_ISSUE_PURITY_001", sid, f"{sid}_P200_T775", "definition_ambiguity", "yield_quality", f"{sid}_P200_T775_PROD", "TGA_carbon_content_wt_percent", "The 59.5 wt.% value is the SWCNT share of recovered carbon by DTG deconvolution, not SWCNT yield per catalyst or ethanol conversion.", f"EVD_{sid}_P200_T775_PRODUCT", "high"))
    return tables


def build_zno_coating(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    sid = meta["source_id"]
    tables = make_tables(meta, "One ZnO-coating/post-processing experiment on pre-obtained functionalized MWCNT; the source does not report CNT synthesis.")
    rid = f"{sid}_ZNO_MWCNT_COPRECIP"
    run = run_row(sid, "ZNO_MWCNT_COPRECIP", "ZnO-coated functionalized MWCNT by co-precipitation", "Pre-obtained MWCNTs were coated with ZnO nanoparticles for dye photodegradation; no CNT-growth recipe is reported.", confidence="medium")
    run["data_type"] = "experimental_post_processing"
    run["target_track"] = "CNT_functionalization"
    tables["source_run"].append(run)
    tables["catalyst_system"].append(catalyst_row(rid, catalyst_label="ZnO-coated functionalized MWCNT photocatalyst", active_metals="Zn", support_material="pre-obtained functionalized MWCNT", precursor_summary="Zn(NO3)2·6H2O and NaOH", preparation_method="aqueous co-precipitation coating", preparation_detail="Functionalized MWCNT dispersed by 30 min sonication; zinc nitrate in 20 mL DI water added dropwise; NaOH added to pH 10; stirred 1 h, aged overnight, washed and filtered.", drying_condition="70 C", calcination_condition="350 C; duration not reported", post_preparation_condition="ZnO nanoparticle-coated MWCNT"))
    tables["reactor_process_gas"].append(process_row(rid, 1, "aqueous_co_precipitation_functionalization", reactor_type="heated-plate stirred aqueous vessel", reactor_setup_summary="MWCNT dispersion sonicated 30 min; Zn nitrate added dropwise; NaOH precipitated Zn(OH)2 at pH 10.", temperature_setpoint_C="room/unspecified heated-plate temperature; dry 70; calcine 350", holding_time_min="60 stirring plus overnight aging", carbon_source="pre-existing functionalized MWCNT (not synthesized in this source)", pressure_original="atmospheric", pressure_kPa="101.325", process_note="CNT post-processing/material synthesis, not CNT growth."))
    tables["yield_quality"].append(yield_row(rid, primary_yield_metric="ZnO-coated MWCNT photocatalyst formation", yield_original="not_reported", yield_definition_original="No product mass, CNT yield or coating yield reported.", secondary_result_summary="ZnO nanoparticles deposited on MWCNT for UV/visible methyl-orange degradation.", CNT_type_reported="pre-obtained multi-walled carbon nanotubes", CNT_type_confirmed="MWCNT input material; synthesis unmapped", product_mixture_summary="ZnO-coated functionalized MWCNT nanocomposite", CNT_type_evidence="The source uses pre-obtained MWNT; it does not establish their growth conditions.", morphology="ZnO nanoparticle-coated MWCNT", characterization_methods="XRD; FTIR; diffuse reflectance; SEM-EDX; photocatalysis", post_treatment_or_purification="ZnO aqueous co-precipitation coating", purification_condition="washed with distilled water until nitrate removal, filtered, dried 70 C, calcined 350 C", application_property_summary="methyl-orange photodegradation under 280 nm UV and 480 nm visible light"))
    tables["cost_scale_review"].append(cost_row(rid, scale_evidence_summary="Laboratory 20 mL aqueous coating batch; product/feed masses not reported.", cost_driver_summary="Functionalized MWCNT, zinc nitrate, NaOH, sonication and 350 C calcination.", safety_risk="Caustic NaOH, zinc salts, nanopowder and UV exposure.", emission_or_waste="Nitrate-containing wash water and Zn/MWCNT solids."))
    ev4(tables, store, sid, rid, "SPAN_0EF750CA1B70CFCA9443", "SPAN_5E508256FDC6C862BA27", "SPAN_659B3D72F6CE1FDE9295")
    tables["review_issue_log"].append(issue_row(f"{sid}_ISSUE_SCOPE_001", sid, rid, "critical_data_gap", "reactor_process_gas", f"{rid}_S01", "carbon_source", "This paper functionalizes pre-obtained MWCNT and contains no source-specific CNT growth condition; the run is explicitly typed as post-processing.", f"EVD_{rid}_PROC", "high"))
    return tables


BUILDERS: dict[str, Callable[[dict[str, Any], EvidenceStore], dict[str, list[dict[str, str]]]]] = {
    "LIT_4421747A539A3C4E": build_co_graphene,
    "LIT_4596780F2CFEE553": build_dot_pecvd,
    "LIT_4B17E877536A6E0E": build_wire_substrates,
    "LIT_4B3D3C5CD3B8D731": build_remote_plasma,
    "LIT_4DC70416A368D5D9": build_zno_coating,
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
    (REPORT_ROOT / "manual_batch_013_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
