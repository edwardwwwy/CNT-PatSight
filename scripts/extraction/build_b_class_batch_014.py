#!/usr/bin/env python3
"""Transcribe the sixth five-paper B-class batch into all eight tables."""

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
from scripts.extraction.package_io import existing_package_metric

BATCH_ID = "B_CLASS_371_20260719"
REPORT_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
BATCH_NUMBER = 14
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
PACKAGE_ROOT = ROOT / "data/interim/extraction/B"
SOURCE_IDS = (
    "LIT_506EF40D21FFF36D",
    "LIT_52723AF7CCAC0CD4",
    "LIT_57766B564B7B2939",
    "LIT_5C31905295320B91",
    "LIT_60168627B3641616",
)


def make_tables(meta: dict[str, Any], scope: str) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    master = master_row(meta, scope)
    master["local_file_path"] = f"data/interim/parsed_text/by_source/{meta['source_id']}.parsed.json"
    master["notes"] = f"Source-specific transcription for {BATCH_NAME}."
    tables["source_master"].append(master)
    return tables


def ev4(tables: dict[str, list[dict[str, str]]], store: EvidenceStore, sid: str, rid: str, cat: str, proc: str, prod: str, *, review: bool = False) -> None:
    status = "review_assessment" if review else "reported"
    add_evidence(tables, store, sid, rid, "CAT", "catalyst_system", f"{rid}_CAT", "record_level", cat, "Catalyst/material basis.", value_status=status)
    add_evidence(tables, store, sid, rid, "PROC", "reactor_process_gas", f"{rid}_S01", "record_level", proc, "Process or review-scope condition.", value_status=status)
    add_evidence(tables, store, sid, rid, "PRODUCT", "yield_quality", f"{rid}_PROD", "record_level", prod, "Reported product outcome or review conclusion.", value_status=status)
    add_evidence(tables, store, sid, rid, "SCALE", "cost_scale_review", rid, "record_level", proc, "Scale/resource context.", confidence="medium", value_status="review_assessment")


def build_buffer_layers(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    sid = meta["source_id"]
    tables = make_tables(meta, "Four exact 650 C oxide-buffer comparisons plus two explicitly reported 550-700 C growth-rate series summaries.")
    exact = (
        ("AL2O3_T650", "ALD Al2O3", "thickest and densest VACNT array; mostly triple-walled"),
        ("TIO2_T650", "ALD TiO2", "relatively thin, low-density VACNT array; more than four walls"),
        ("ZNO_T650", "ALD ZnO", "almost no VACNT growth; detected tubes were multi-walled/more than four walls"),
        ("SIO2_T650", "thermally oxidized SiO2", "relatively thin VACNT array; more than four walls"),
    )
    for code, buffer_name, outcome in exact:
        rid = f"{sid}_{code}"
        tables["source_run"].append(run_row(sid, code, f"1 nm Fe on {buffer_name}; 650 C acetylene CVD", outcome))
        tables["catalyst_system"].append(catalyst_row(rid, catalyst_label=f"1 nm Fe / 20 nm {buffer_name}", active_metals="Fe", support_material=f"20 nm {buffer_name} on Si", metal_ratio_original="1 nm Fe film on 20 nm oxide", precursor_summary="electron-beam evaporated Fe; ALD oxide or thermal SiO2", preparation_method="ALD/thermal oxidation followed by electron-beam Fe evaporation", preparation_detail="Al2O3, TiO2 and ZnO deposited by ALD at 200 C using TMA, TDMAT and DEZ respectively with H2O; SiO2 thermally oxidized.", activation_condition="600 C H2 anneal for 3 min at 700 sccm"))
        tables["reactor_process_gas"].append(process_row(rid, 1, "thermal_CVD", reactor_type="AIXTRON Black Magic II commercial CVD system", temperature_setpoint_C="650", holding_time_min="30", carbon_source="C2H2", carbon_source_flow_original="100 sccm", carbon_source_flow_sccm="100", reducing_gas="H2", reducing_gas_flow_original="700 sccm", reducing_gas_flow_sccm="700", total_flow_original="800 sccm", total_flow_sccm="800", gas_composition_summary="C2H2 100 sccm + H2 700 sccm after 600 C H2 catalyst anneal"))
        tables["yield_quality"].append(yield_row(rid, primary_yield_metric="VACNT array morphology", yield_original=outcome, yield_definition_original="Cross-sectional SEM/TEM/Raman buffer-layer comparison; no mass yield reported.", secondary_result_summary=outcome, CNT_type_reported="vertically aligned carbon nanotubes", CNT_type_confirmed="MWCNT", product_mixture_summary=outcome, CNT_type_evidence="SEM, TEM and absence of RBM in Raman", morphology=outcome, alignment_or_array="vertically aligned array; nearly absent for ZnO", Raman_ratio_type="ID/IG", Raman_ratio_value="near or above 1; plot spectra only", characterization_methods="FESEM; TEM; Raman (632.8 nm)"))
        tables["cost_scale_review"].append(cost_row(rid, scale_evidence_summary="Laboratory thin-film substrate CVD run.", cost_driver_summary="ALD or thermal oxide, e-beam Fe, 650 C CVD and 700 sccm hydrogen.", safety_risk="Hydrogen/acetylene at high temperature; pyrophoric/volatile ALD precursors during buffer preparation.", emission_or_waste="CVD exhaust and oxide/Fe-coated Si substrates."))
        ev4(tables, store, sid, rid, "SPAN_3182AB668CE5EE6E7391", "SPAN_7FC38A2C42DC2A94A0C5", "SPAN_AE6D7741A0FDC02587BE")

    for code, buffer_name, trend in (
        ("AL2O3_TSERIES", "ALD Al2O3", "growth rate first increased then decreased across 550-700 C; it continued to increase above 600 C before its later decline"),
        ("SIO2_TSERIES", "thermally oxidized SiO2", "growth rate first increased then decreased across 550-700 C and decreased above 600 C"),
    ):
        rid = f"{sid}_{code}"
        rr = run_row(sid, code, f"1 nm Fe on {buffer_name}; 550-700 C temperature series", trend, confidence="medium")
        rr["data_type"] = "experimental_series_summary"
        tables["source_run"].append(rr)
        tables["catalyst_system"].append(catalyst_row(rid, catalyst_label=f"1 nm Fe / 20 nm {buffer_name}", active_metals="Fe", support_material=f"20 nm {buffer_name} on Si", metal_ratio_original="1 nm Fe film on 20 nm oxide", preparation_method="oxide formation plus electron-beam Fe evaporation", activation_condition="600 C H2 anneal for 3 min at 700 sccm"))
        tables["reactor_process_gas"].append(process_row(rid, 1, "thermal_CVD_temperature_series", reactor_type="AIXTRON Black Magic II", temperature_setpoint_C="550-700", holding_time_min="30 per condition", carbon_source="C2H2", carbon_source_flow_original="100 sccm", carbon_source_flow_sccm="100", reducing_gas="H2", reducing_gas_flow_original="700 sccm", reducing_gas_flow_sccm="700", total_flow_original="800 sccm", total_flow_sccm="800", process_note="Series endpoints/range reported; individual growth-rate values are plot-only and were not digitized."))
        tables["yield_quality"].append(yield_row(rid, primary_yield_metric="VACNT growth-rate trend", yield_original=trend, yield_definition_original="Figure 6 trend; exact plotted rates not tabulated.", secondary_result_summary=trend, CNT_type_reported="VACNT", CNT_type_confirmed="MWCNT", product_mixture_summary="vertically aligned MWCNT array", CNT_type_evidence="SEM/TEM/Raman", morphology="VACNT array", characterization_methods="cross-sectional SEM; TEM; Raman"))
        tables["cost_scale_review"].append(cost_row(rid, scale_evidence_summary="Laboratory thin-film temperature series.", cost_driver_summary="ALD/thermal oxide, e-beam Fe, hydrogen/acetylene and 550-700 C furnace.", safety_risk="Hydrogen/acetylene at high temperature.", emission_or_waste="CVD exhaust and coated Si coupons."))
        ev4(tables, store, sid, rid, "SPAN_3182AB668CE5EE6E7391", "SPAN_7FC38A2C42DC2A94A0C5", "SPAN_06F56E46A7DE04F21CA0")
        tables["review_issue_log"].append(issue_row(f"{rid}_ISSUE_PLOT", sid, rid, "plot_only_value", "yield_quality", f"{rid}_PROD", "yield_original", "The paper reports the growth-rate curve graphically; this row preserves only the stated trend and does not invent point values.", f"EVD_{rid}_PRODUCT", "medium"))
    return tables


def build_cvd_review(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    sid = meta["source_id"]
    tables = make_tables(meta, "Review-chapter synthesis only; no author-generated CNT experiment is represented.")
    code = "REVIEW_CVD_LANDSCAPE"
    rid = f"{sid}_{code}"
    rr = run_row(sid, code, "Review synthesis of catalytic CVD CNT production", "Chapter reviews carbon-source, catalyst and substrate effects; it does not report an author-run experiment.", confidence="medium")
    rr["data_type"] = "literature_review"
    rr["target_track"] = "CNT_production_review"
    tables["source_run"].append(rr)
    tables["catalyst_system"].append(catalyst_row(rid, catalyst_label="reviewed transition-metal catalyst systems", active_metals="Fe; Co; Ni and other systems discussed", support_material="multiple reviewed supports/substrates", precursor_summary="multiple literature systems", preparation_method="not_applicable_review_synthesis", phase_or_state_summary="no single source-specific catalyst recipe"))
    tables["reactor_process_gas"].append(process_row(rid, 1, "literature_review_synthesis", reactor_type="multiple CVD configurations reviewed", temperature_setpoint_C="500-1200 (generic CVD comparison range)", holding_time_min="not_applicable", carbon_source="multiple reviewed carbon sources", pressure_original="multiple literature conditions", pressure_kPa="", process_note="Review-level comparison, not an experimental run by the chapter authors."))
    tables["yield_quality"].append(yield_row(rid, primary_yield_metric="generic reviewed CVD yield range", yield_original="60-90% in broad method-comparison table", yield_definition_original="Review table aggregate; basis and comparability across cited studies are not established.", secondary_result_summary="CVD described as simple, lower-cost and promising for large-scale control relative to other synthesis methods.", CNT_type_reported="SWCNT and MWCNT across reviewed literature", CNT_type_confirmed="not_applicable_review", product_mixture_summary="multiple reviewed CNT products", CNT_type_evidence="review narrative/tables", characterization_methods="not_applicable_review"))
    tables["cost_scale_review"].append(cost_row(rid, scale_evidence_summary="Review claims broad large-scale prospects; no author-demonstrated reactor scale.", scale_level_claimed="potential_large_scale", cost_driver_summary="Carbon source, catalyst and substrate are identified as key controls; no quantitative source-specific cost model.", safety_risk="Varies across reviewed CVD systems.", emission_or_waste="Varies across reviewed systems."))
    ev4(tables, store, sid, rid, "SPAN_FB9196CB0DB253CEE8A3", "SPAN_FB9196CB0DB253CEE8A3", "SPAN_FB9196CB0DB253CEE8A3", review=True)
    tables["review_issue_log"].append(issue_row(f"{sid}_ISSUE_SCOPE_001", sid, rid, "secondary_source", "source_run", rid, "data_type", "This source is a review chapter. No cited literature condition is promoted to an author-generated experimental run.", f"EVD_{rid}_PROC", "high"))
    tables["review_issue_log"].append(issue_row(f"{sid}_ISSUE_YIELD_001", sid, rid, "definition_ambiguity", "yield_quality", f"{rid}_PROD", "yield_original", "The 60-90% CVD range is a broad review-table comparison with no uniform yield basis.", f"EVD_{rid}_PRODUCT", "high"))
    return tables


def build_fe3o4_size(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    sid = meta["source_id"]
    tables = make_tables(meta, "Four matched Fe3O4 nanoparticle-size catalyst runs grown under one explicit CVD recipe.")
    records = (
        ("NP3P0", "3:3", "3.0", "VACNTs formed but tilted with top defects; poorer alignment than the 3.5 nm catalyst"),
        ("NP3P5", "4.5:3", "3.5", "dense, uniform-height, defect-free vertically aligned MWCNT array; best alignment"),
        ("NP4P1", "6:3", "4.1", "VACNTs formed but tilted with top defects; wall count/diameter increased relative to smaller catalyst"),
        ("NP6P0", "7.5:3", "6.0", "less-dense VACNTs with tilted/defective alignment and increased outer diameter/wall count"),
    )
    for code, ratio, size, outcome in records:
        rid = f"{sid}_{code}"
        tables["source_run"].append(run_row(sid, code, f"{size} nm Fe3O4 nanoparticles on Si", outcome))
        tables["catalyst_system"].append(catalyst_row(rid, catalyst_label=f"{size} nm Fe3O4 nanoparticles drop-dried on Si", active_metals="Fe", support_material="cleaned HF-treated Si(100)", metal_ratio_original=f"OA:OAm molar ratio {ratio}", precursor_summary="1 mmol Fe(acac)3, 5 mmol 1,2-hexadecanediol, variable OA, 3 mmol oleylamine, 10 mL phenyl ether", preparation_method="thermal decomposition then drop-drying", preparation_detail=f"Refluxed 30 min under N2, ethanol-washed/centrifuged, redispersed in hexane; OA:OAm {ratio} produced mean Fe3O4 size {size} nm; one drop placed on Si.", calcination_condition="773 K (about 500 C) for 30 min during ramp", catalyst_particle_size_mean_nm=size, catalyst_particle_size_qualifier="mean HRTEM size", phase_or_state_summary="single-crystal FCC Fe3O4 nanoparticles"))
        tables["reactor_process_gas"].append(process_row(rid, 1, "thermal_CVD", reactor_type="horizontal electric tubular furnace with quartz boat", reactor_setup_summary="Ramp from room temperature at 5 K/min; calcine at 773 K for 30 min; hold at 973 K about 15 min before growth.", temperature_setpoint_C="699.85", holding_time_min="30 growth after about 15 min temperature hold", carbon_source="C2H2", carbon_source_flow_original="10 sccm", carbon_source_flow_sccm="10", reducing_gas="H2", reducing_gas_flow_original="80 sccm during 400 sccm ramp; about 40 sccm after total reduced to 200 sccm assuming retained 4:1 Ar/H2 ratio", reducing_gas_flow_sccm="40", inert_gas="Ar", inert_gas_flow_original="320 sccm during ramp; about 160 sccm during growth assuming retained 4:1 ratio", inert_gas_flow_sccm="160", total_flow_original="400 sccm Ar/H2 (4:1) ramp, then 200 sccm Ar/H2 plus 10 sccm C2H2", total_flow_sccm="210", gas_composition_summary="Ar/H2 4:1; absolute component growth flows inferred from reported 200 sccm total and retained ratio"))
        tables["yield_quality"].append(yield_row(rid, primary_yield_metric="VACNT alignment/morphology", yield_original=outcome, yield_definition_original="SEM/TEM qualitative comparison; no mass yield and no exact CNT-diameter values tabulated.", secondary_result_summary=outcome, CNT_type_reported="vertically aligned carbon nanotubes", CNT_type_confirmed="MWCNT", product_mixture_summary="VACNT array", CNT_type_evidence="FESEM, HRTEM and Raman", morphology=outcome, alignment_or_array="best uniform vertical alignment" if size == "3.5" else "tilted/defective vertical array", characterization_methods="FESEM; HRTEM; Raman (1064 nm)"))
        tables["cost_scale_review"].append(cost_row(rid, scale_evidence_summary="Laboratory 1 cm x 1 cm Si coupon in tube furnace.", cost_driver_summary="Monodisperse Fe3O4 wet synthesis, Si cleaning/HF, 700 C furnace and Ar/H2/C2H2.", safety_risk="HF and piranha wafer cleaning; hydrogen/acetylene at high temperature; nanoparticle handling.", emission_or_waste="Organic solvent/surfactant wash waste, acidic wafer-cleaning waste and CVD exhaust."))
        ev4(tables, store, sid, rid, "SPAN_31998EB6E101D6AB7004", "SPAN_0629148292C98C0E9B22", "SPAN_968275B016FA8ECD3DDA")
    tables["review_issue_log"].append(issue_row(f"{sid}_ISSUE_FLOW_001", sid, f"{sid}_NP3P5", "derived_value", "reactor_process_gas", f"{sid}_NP3P5_S01", "reducing_gas_flow_sccm", "Growth-stage Ar and H2 component flows are calculated from the stated 200 sccm Ar/H2 total assuming the reported 4:1 ratio remains in force.", f"EVD_{sid}_NP3P5_PROC", "medium"))
    return tables


def build_composite_review(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    sid = meta["source_id"]
    tables = make_tables(meta, "Review-chapter synthesis of CNT-composite processing; no author-generated CNT growth run.")
    code = "REVIEW_COMPOSITE_PROCESSING"
    rid = f"{sid}_{code}"
    rr = run_row(sid, code, "Review synthesis of CNT-polymer composite processing", "Reviews CNT dispersion, polymer compounding and structural-health-monitoring composites; CNT synthesis is not reported by the chapter authors.", confidence="medium")
    rr["data_type"] = "literature_review"
    rr["target_track"] = "CNT_composite_review"
    tables["source_run"].append(rr)
    tables["catalyst_system"].append(catalyst_row(rid, catalyst_label="pre-existing CNT filler in reviewed polymer composites", active_metals="not_applicable", support_material="thermoset/thermoplastic matrices and fibre composites", precursor_summary="SWCNT or MWCNT filler from cited studies", preparation_method="multiple reviewed dispersion/compounding routes", phase_or_state_summary="no source-specific CNT catalyst or growth recipe"))
    tables["reactor_process_gas"].append(process_row(rid, 1, "literature_review_composite_processing", reactor_type="multiple reviewed solution, sonication, three-roll milling and melt-compounding routes", temperature_setpoint_C="not_applicable_review", holding_time_min="not_applicable_review", carbon_source="pre-existing CNT filler", pressure_original="not_applicable_review", pressure_kPa="", process_note="Review synthesis; a cited typical multiscale-hybrid route uses three-roll-mill resin dispersion then vacuum-assisted resin-transfer moulding."))
    tables["yield_quality"].append(yield_row(rid, primary_yield_metric="reviewed composite-property/application outcomes", yield_original="not_comparable_across_reviewed_studies", yield_definition_original="No author-generated material yield.", secondary_result_summary="CNT networks reviewed for electrical conductivity, strain sensing and structural-health monitoring.", CNT_type_reported="SWCNT and MWCNT inputs", CNT_type_confirmed="not_applicable_review", product_mixture_summary="CNT-polymer and multiscale hybrid composites", CNT_type_evidence="review narrative", morphology="dispersed/percolated CNT networks in polymer matrices", characterization_methods="multiple cited studies; not a single author experiment", application_property_summary="electrical conductivity, piezoresistive sensing and damage monitoring"))
    tables["cost_scale_review"].append(cost_row(rid, scale_evidence_summary="Review discusses lab and industry-relevant processing, but demonstrates no author-run scale.", scale_level_claimed="industry_relevant_processing_review", cost_driver_summary="CNT filler, dispersion energy/equipment, polymer processing and fibre-composite moulding.", safety_risk="CNT powder exposure, solvents/resins and high-shear processing vary by reviewed route.", emission_or_waste="Composite/solvent waste varies across cited routes."))
    ev4(tables, store, sid, rid, "SPAN_03A78028CBDA0585608E", "SPAN_270EE8F98AB3903A4637", "SPAN_9D2D4C63A79F50CEE8C4", review=True)
    tables["review_issue_log"].append(issue_row(f"{sid}_ISSUE_SCOPE_001", sid, rid, "secondary_source", "source_run", rid, "data_type", "This is a review chapter; it contains no author-generated CNT synthesis run. The eight-table package records only the review-level composite-processing scope.", f"EVD_{rid}_PROC", "high"))
    return tables


def build_vpe(meta: dict[str, Any], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    sid = meta["source_id"]
    tables = make_tables(meta, "Six explicitly demonstrated chirality/feed/substrate VPE combinations plus two reported ethanol-flow optimization series summaries.")
    records = (
        ("76_ETOH_QTZ", "(7,6)", "ethanol", "quartz", "34.5 +/- 17.7 micrometres average length after cloning versus 0.34 +/- 0.15 micrometres seeds; about 0.9 nm diameter"),
        ("76_CH4_QTZ", "(7,6)", "methane", "quartz", "long horizontally aligned cloned (7,6) SWCNTs"),
        ("65_CH4_QTZ", "(6,5)", "methane", "quartz", "long horizontally aligned cloned semiconducting (6,5) SWCNTs"),
        ("65_ETOH_QTZ", "(6,5)", "ethanol", "quartz", "long horizontally aligned cloned semiconducting (6,5) SWCNTs"),
        ("77_CH4_QTZ", "(7,7)", "methane", "quartz", "cloned metallic armchair (7,7) SWCNTs aligned to quartz crystal orientation"),
        ("77_CH4_SIO2", "(7,7)", "methane", "Si/SiO2", "randomly oriented cloned metallic armchair (7,7) SWCNTs"),
    )
    for code, chirality, feed, substrate, outcome in records:
        rid = f"{sid}_{code}"
        tables["source_run"].append(run_row(sid, code, f"Metal-free {chirality} SWCNT VPE; {feed}; {substrate}", outcome))
        tables["catalyst_system"].append(catalyst_row(rid, catalyst_label=f"DNA-purified chirality-pure {chirality} SWCNT seed; no metal catalyst", active_metals="none", support_material=substrate, metal_ratio_original="metal-catalyst-free", precursor_summary=f"about 0.5 mg/mL purified {chirality} SWCNT seed solution", preparation_method="DNA chromatography, drop deposition and end activation", preparation_detail="Seed solution drop-deposited and incubated 30 min to 1 week, gently rinsed and dried.", activation_condition="air 200 C 30 min; then 400 C under 300 sccm H2; 100 sccm Ar through room-temperature water bubbler for 3 min", phase_or_state_summary="open/activated SWCNT seed ends"))
        if feed == "ethanol":
            gas = dict(carbon_source="ethanol vapour", carbon_source_flow_original="160 sccm Ar through ethanol bubbler at 0 C", carbon_source_flow_sccm="not_convertible_from_bubbler_flow", reducing_gas="H2", reducing_gas_flow_original="300 sccm", reducing_gas_flow_sccm="300", inert_gas="Ar carrier", inert_gas_flow_original="160 sccm through ethanol bubbler", inert_gas_flow_sccm="160", total_flow_original="460 sccm gas-carrier total plus ethanol vapour", total_flow_sccm="460")
        else:
            gas = dict(carbon_source="CH4", carbon_source_flow_original="2000 sccm", carbon_source_flow_sccm="2000", reducing_gas="H2", reducing_gas_flow_original="300 sccm", reducing_gas_flow_sccm="300", total_flow_original="2300 sccm", total_flow_sccm="2300")
        tables["reactor_process_gas"].append(process_row(rid, 1, "metal_free_vapour_phase_epitaxy", reactor_type="2.54 cm (1 inch) tube furnace", temperature_setpoint_C="900", holding_time_min="15", gas_composition_summary=f"{feed} feed with hydrogen after seed air/H2/water-vapour activation", **gas))
        length = "34.5 +/- 17.7 micrometres" if code == "76_ETOH_QTZ" else "tens of micrometres/qualitative long tubes"
        tables["yield_quality"].append(yield_row(rid, primary_yield_metric="chirality-preserving SWCNT elongation", yield_original=outcome, yield_definition_original="AFM/SEM/Raman outcome; no mass yield.", secondary_result_summary=outcome, CNT_type_reported=f"{chirality} SWCNT", CNT_type_confirmed=f"{chirality} SWCNT", product_mixture_summary="cloned SWCNT from purified seed", CNT_type_evidence="AFM/SEM and chirality-specific Raman RBM; electrical measurement for (7,6)/(6,5)", outer_diameter_range_nm="about 0.9" if chirality == "(7,6)" else "not_reported", length_summary=length, morphology="horizontal aligned on quartz; random on Si/SiO2", alignment_or_array="quartz-crystal aligned" if substrate == "quartz" else "random", RBM_peak_reported="265 cm-1 for (7,6); 249 cm-1 for (7,7); chirality-specific assignment", characterization_methods="AFM; SEM; Raman 633/532 nm; individual-device electrical measurement"))
        tables["cost_scale_review"].append(cost_row(rid, scale_evidence_summary="Laboratory substrate-based seeded VPE in 1-inch tube furnace.", cost_driver_summary="DNA-purified chirality seeds, 900 C furnace, high gas flow and substrate/device processing.", safety_risk="Hydrogen/methane or ethanol vapour at high temperature; nanoparticle/nanotube handling.", emission_or_waste="Hydrocarbon VPE exhaust, etched seed loss and processed substrates."))
        ev4(tables, store, sid, rid, "SPAN_B51C0D5D5B7182EE8D99", "SPAN_0FF17C0FED0ECE9FE084", "SPAN_352FCE10EB2B0DB0530A")

    for code, label, h2, ar, outcome in (
        ("ETOH_H2_SERIES", "ethanol VPE H2-flow series (200-400 sccm; Ar 160 sccm)", "200-400", "160", "highest cloned-SWCNT density at H2 300 sccm and Ar 160 sccm"),
        ("ETOH_AR_SERIES", "ethanol-carrier series (Ar 200-108 sccm; H2 250 sccm)", "250", "200-108", "highest cloned-SWCNT density at H2 250 sccm and Ar 128 sccm; optimum H2/Ar ratio about 2"),
    ):
        rid = f"{sid}_{code}"
        rr = run_row(sid, code, label, outcome, confidence="medium")
        rr["data_type"] = "experimental_series_summary"
        tables["source_run"].append(rr)
        tables["catalyst_system"].append(catalyst_row(rid, catalyst_label="matched purified SWCNT seed samples; no metal catalyst", active_metals="none", support_material="growth substrate", metal_ratio_original="metal-catalyst-free", precursor_summary="ten samples with similar nanotube-seed density", preparation_method="DNA purification, drop deposition and air/H2/water activation", activation_condition="air 200 C 30 min; H2 at 400 C; water-vapour treatment 3 min"))
        tables["reactor_process_gas"].append(process_row(rid, 1, "metal_free_vapour_phase_epitaxy_series", reactor_type="1-inch tube furnace", temperature_setpoint_C="900", holding_time_min="15 per condition", carbon_source="ethanol vapour", carbon_source_flow_original=f"Ar carrier {ar} sccm through 0 C ethanol bubbler", carbon_source_flow_sccm="not_convertible_from_bubbler_flow", reducing_gas="H2", reducing_gas_flow_original=f"{h2} sccm", reducing_gas_flow_sccm=h2, inert_gas="Ar carrier", inert_gas_flow_original=f"{ar} sccm", inert_gas_flow_sccm=ar, total_flow_original="series; ethanol vapour addition not quantified", total_flow_sccm="", process_note="Series summary; individual SEM-derived density values are not tabulated."))
        tables["yield_quality"].append(yield_row(rid, primary_yield_metric="relative cloned-SWCNT density", yield_original=outcome, yield_definition_original="SEM comparison of series; exact density values not reported.", secondary_result_summary=outcome, CNT_type_reported="cloned SWCNT", CNT_type_confirmed="SWCNT", product_mixture_summary="seed-elongated SWCNT", CNT_type_evidence="SEM", morphology="long cloned nanotubes", characterization_methods="SEM"))
        tables["cost_scale_review"].append(cost_row(rid, scale_evidence_summary="Ten matched laboratory substrate samples in optimization series.", cost_driver_summary="Purified seeds, 900 C VPE, hydrogen and ethanol-carrier flow.", safety_risk="Hydrogen/ethanol at high temperature.", emission_or_waste="VPE exhaust and substrate samples."))
        ev4(tables, store, sid, rid, "SPAN_B51C0D5D5B7182EE8D99", "SPAN_0FF17C0FED0ECE9FE084", "SPAN_37F87B18E0493A28BCF7")
        tables["review_issue_log"].append(issue_row(f"{rid}_ISSUE_SERIES", sid, rid, "plot_only_value", "yield_quality", f"{rid}_PROD", "yield_original", "Only the reported optimum/trend is retained because per-condition nanotube densities are not tabulated.", f"EVD_{rid}_PRODUCT", "medium"))
    return tables


BUILDERS: dict[str, Callable[[dict[str, Any], EvidenceStore], dict[str, list[dict[str, str]]]]] = {
    "LIT_506EF40D21FFF36D": build_buffer_layers,
    "LIT_52723AF7CCAC0CD4": build_cvd_review,
    "LIT_57766B564B7B2939": build_fe3o4_size,
    "LIT_5C31905295320B91": build_composite_review,
    "LIT_60168627B3641616": build_vpe,
}


def main() -> None:
    metadata = load_metadata("B")
    store = EvidenceStore()
    metrics: list[dict[str, Any]] = []
    try:
        for sid in SOURCE_IDS:
            metric = existing_package_metric(sid, "B")
            if metric is None:
                metrics.append(publish_package(sid, BUILDERS[sid](metadata[sid], store)))
            else:
                metrics.append(metric)
    finally:
        store.close()
    result = {"batch_id": BATCH_NAME, "sources": metrics, "total_runs": sum(x["row_counts"]["source_run"] for x in metrics), "status": "completed_needs_review"}
    (REPORT_ROOT / "manual_batch_014_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
