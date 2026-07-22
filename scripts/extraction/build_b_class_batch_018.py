#!/usr/bin/env python3
"""Transcribe the tenth five-paper B-class batch into complete eight-table packages."""
from __future__ import annotations

import json
from typing import Callable

from scripts.extraction.batch_common import (
    ROOT, TABLES, EvidenceStore, catalyst_row, cost_row, issue_row,
    load_metadata, master_row, process_row, run_row, yield_row,
)
from scripts.extraction.build_b_class_batch_001 import add_evidence, publish_package
from scripts.extraction.package_io import existing_package_metric

BATCH_ID = "B_CLASS_371_20260719"
REPORT_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
BATCH_NUMBER = 18
BATCH_NAME = f"{BATCH_ID}_MANUAL_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/B/batches" / BATCH_ID
PACKAGE_ROOT = ROOT / "data/interim/extraction/B"
SOURCE_IDS = (
    "LIT_920AD764C13FB11B", "LIT_954C0D690A6F7711", "LIT_960D4EBE5F445BFD",
    "LIT_9A6884F1BCF7D6CC", "LIT_9B4BCF02D1067EA7",
)


def base(m, scope):
    t = {name: [] for name in TABLES}
    row = master_row(m, scope)
    row["local_file_path"] = f"data/interim/parsed_text/by_source/{m['source_id']}.parsed.json"
    row["notes"] = f"Source-specific transcription for {BATCH_NAME}."
    t["source_master"].append(row)
    return t


def ev(t, store, sid, rid, cat, proc, prod, *, review=False):
    add_evidence(t, store, sid, rid, "CAT", "catalyst_system", f"{rid}_CAT", "record_level", cat, "Catalyst/material evidence.")
    add_evidence(t, store, sid, rid, "PROC", "reactor_process_gas", f"{rid}_S01", "record_level", proc, "Process evidence.")
    add_evidence(t, store, sid, rid, "PRODUCT", "yield_quality", f"{rid}_PROD", "record_level", prod, "Outcome evidence.")
    add_evidence(t, store, sid, rid, "SCALE", "cost_scale_review", rid, "record_level", proc, "Scale and resource context.", confidence="medium", value_status="review_assessment" if review else "author_reported")


def build_wafer(m, store):
    sid = m["source_id"]
    t = base(m, "Two wafer-scale aligned-SWCNT routes distinguished by catalyst-patterning polymer and pretreatment.")
    routes = (
        ("PHOTO", "FeCl3/Shipley 1827 photolithography", "5 mmol/L FeCl3 in methanol doped into Shipley 1827 positive photoresist; 20 micrometre lines", "O2 plasma 15 min or air calcination 700 C for 5 min", "~10 SWCNT/micrometre; most >200 micrometres and some ~1 mm; mean diameter ~1.1 nm", "10"),
        ("PVP", "FeCl3/PVP microcontact printing", "10 mmol/L FeCl3 plus 20-40 mmol/L PVP ink printed with PDMS stamp for 2 min", "H2/Ar 220/1000 sccm reduction for 5-15 min", "2-5 SWCNT/micrometre, locally ~10; lower/nonuniform density and slight curvature", "2-5"),
    )
    for code, label, prep, activation, outcome, density in routes:
        rid = f"{sid}_{code}"
        t["source_run"].append(run_row(sid, code, label, outcome))
        t["catalyst_system"].append(catalyst_row(
            rid, catalyst_label=label, active_metals="Fe", support_material="ST-cut single-crystal quartz wafer",
            precursor_summary=prep, preparation_method="photolithography" if code == "PHOTO" else "PDMS microcontact printing",
            preparation_detail=prep, activation_condition=activation, catalyst_particle_size_mean_nm="~6" if code == "PHOTO" else "not_reported",
            catalyst_particle_size_qualifier="FeOx nanoparticles after polymer removal/reduction",
        ))
        t["reactor_process_gas"].append(process_row(
            rid, 1, "methane_CVD", reactor_type="horizontal 3-inch-diameter tube furnace", temperature_setpoint_C="920",
            holding_time_min="30", carbon_source="CH4", carbon_source_flow_original="1100 sccm", carbon_source_flow_sccm="1100",
            reducing_gas="H2", reducing_gas_flow_original="220 sccm", reducing_gas_flow_sccm="220", inert_gas="Ar",
            inert_gas_flow_original="1500 sccm during heating/cooling", inert_gas_flow_sccm="1500",
            total_flow_original="1320 sccm during growth", total_flow_sccm="1320", gas_composition_summary="CH4/H2 1100/220 sccm after Ar heat-up",
            process_note=activation,
        ))
        t["yield_quality"].append(yield_row(
            rid, primary_yield_metric="aligned SWCNT array density", yield_original=f"{density} SWCNT/micrometre",
            yield_definition_original="AFM/SEM line density; no mass yield", secondary_result_summary=outcome,
            CNT_type_reported="single-walled carbon nanotubes", CNT_type_confirmed="SWCNT", product_mixture_summary="clean aligned SWCNT arrays",
            CNT_type_evidence="RBM Raman plus AFM", outer_diameter_mean_nm="~1.1" if code == "PHOTO" else "not_reported",
            length_summary=">200 micrometres for most; up to ~1 mm" if code == "PHOTO" else "not_reported",
            morphology="straight aligned arrays" if code == "PHOTO" else "aligned arrays with slight curvature",
            alignment_or_array="quartz-directed wafer-scale alignment", characterization_methods="SEM; AFM; Raman 633 nm",
        ))
        t["cost_scale_review"].append(cost_row(
            rid, scale_evidence_summary="Catalyst patterns demonstrated over 25 x 40 mm quartz wafers.",
            cost_driver_summary="Quartz annealing, polymer lithography/printing, Ar/H2/CH4 and 920 C furnace.",
            safety_risk="Hydrogen/methane at 920 C; FeCl3 and oxygen-plasma handling.",
            emission_or_waste="CVD exhaust, photoresist/PVP residues and patterned quartz substrates.",
        ))
        ev(t, store, sid, rid, "SPAN_40CC499A1098DD4D7715", "SPAN_1B2B457423FC2F98E2A3", "SPAN_06ECA4CBED4F8598E521")
    return t


def build_sic_composite(m, store):
    sid = m["source_id"]
    t = base(m, "One VACNT growth run with a second, explicitly linked LPCVD a-SiC infiltration stage.")
    rid = f"{sid}_VACNT_SIC"
    r = run_row(sid, "VACNT_SIC", "Fe/Al2O3 VACNT followed by a-SiC infiltration", "96.3 micrometre VACNT at 5 min; porous array converted to SiC-CNT composite")
    r["target_track"] = "CNT_composite_device"
    t["source_run"].append(r)
    t["catalyst_system"].append(catalyst_row(
        rid, catalyst_label="2 nm Fe / 20 nm Al2O3", active_metals="Fe", support_material="20 nm Al2O3 on SiO2/Si",
        metal_ratio_original="2 nm Fe over 20 nm Al2O3", preparation_method="electron-beam evaporation",
        preparation_detail="Al2O3 evaporated before Fe to enhance Fe-particle nucleation density", activation_condition="H2 at 500 C for 3 min",
    ))
    t["reactor_process_gas"].append(process_row(
        rid, 1, "VACNT_CVD", reactor_type="Aixtron Blackmagic CVD", temperature_setpoint_C="600", holding_time_min="5",
        pressure_original="80 mbar", pressure_kPa="8", carbon_source="C2H2", carbon_source_flow_original="50 sccm", carbon_source_flow_sccm="50",
        reducing_gas="H2", reducing_gas_flow_original="700 sccm", reducing_gas_flow_sccm="700", total_flow_original="750 sccm", total_flow_sccm="750",
        gas_composition_summary="H2/C2H2 700/50 sccm after 500 C H2 activation",
    ))
    t["reactor_process_gas"].append(process_row(
        rid, 2, "a_SiC_LPCVD_infiltration", reactor_type="low-pressure CVD", temperature_setpoint_C="760",
        pressure_original="1 mbar", pressure_kPa="0.1", carbon_source="C2H2", carbon_source_flow_original="21.75 sccm", carbon_source_flow_sccm="21.75",
        cofeed_or_reactive_gas="SiH2Cl2 3.25 sccm", reducing_gas="H2 dilution", gas_composition_summary="SiH2Cl2/C2H2 diluted in H2",
        process_note="a-SiC deposition rate about 0.25 nm/min; device flow later used a 90 nm coating.",
    ))
    t["yield_quality"].append(yield_row(
        rid, primary_yield_metric="VACNT height and composite formation", yield_original="96.3 micrometres after 5 min; a-SiC infiltration ~0.25 nm/min",
        yield_definition_original="SEM height and coating-rate outcome; no mass yield", secondary_result_summary="Highest array height 96.3 micrometres; LPCVD thickened fibers and produced dense SiC-CNT composite.",
        CNT_type_reported="vertically aligned carbon nanotube array", CNT_type_confirmed="VACNT", product_mixture_summary="a-SiC-infiltrated VACNT composite",
        CNT_type_evidence="cross-sectional and surface SEM", length_summary="96.3 micrometres", morphology="porous vertical CNT template filled with a-SiC",
        alignment_or_array="vertical array", characterization_methods="SEM; electrical resistance versus temperature; mechanical/device characterization",
    ))
    t["cost_scale_review"].append(cost_row(
        rid, scale_evidence_summary="Wafer-process-compatible catalyst, VACNT growth and LPCVD infiltration; demonstrated on 4-inch wafer device flow.",
        cost_driver_summary="Electron-beam catalyst evaporation, Aixtron CVD, long low-rate LPCVD a-SiC coating and lithographic micromachining.",
        safety_risk="Hydrogen/acetylene and dichlorosilane at high temperature; HF/HBr appear in downstream device processing.",
        emission_or_waste="CVD/LPCVD exhaust and semiconductor-process etchants/resists.",
    ))
    ev(t, store, sid, rid, "SPAN_6A215D63A1860F3E2DC0", "SPAN_7ECCC368F1B8D91695D7", "SPAN_A3E00CC79B82532E1F87")
    add_evidence(t, store, sid, rid, "PROC_S02", "reactor_process_gas", f"{rid}_S02", "record_level", "SPAN_A3E00CC79B82532E1F87", "a-SiC LPCVD infiltration evidence.")
    return t


def build_review(m, store):
    sid = m["source_id"]
    t = base(m, "Review-level catalyst taxonomy covering conventional metals, poor metals, ceramics/semiconductors and catalyst-free CNT formation; no author experiment reconstructed.")
    rid = f"{sid}_REVIEW"
    r = run_row(sid, "REVIEW", "review of CNT synthesis with and without catalyst particles", "Literature synthesis: catalyst identity is broad and CNT growth is not unique to transition metals", "medium")
    r["data_type"] = "literature_review"
    r["target_track"] = "catalyst_scope_review"
    t["source_run"].append(r)
    t["catalyst_system"].append(catalyst_row(
        rid, catalyst_label="literature catalyst taxonomy", active_metals="Fe; Co; Ni; noble/poor metals and nonmetals discussed",
        support_material="various oxides, ceramics, semiconductors and carbonaceous particles", precursor_summary="Review includes conventional transition metals, Au and other poor metals, SiC-derived routes and nano-diamond particles.",
        preparation_method="literature_review", phase_or_state_summary="nanoparticle catalysis and catalyst-free/high-temperature formation mechanisms",
    ))
    t["reactor_process_gas"].append(process_row(
        rid, 1, "literature_review", reactor_type="multiple CVD/annealing/arc-related systems across cited literature",
        temperature_setpoint_C="source-dependent; SiC annealing discussed above 1500", carbon_source="hydrocarbons, alcohols, solid carbon and SiC-derived carbon",
        process_note="No single author-run recipe is reported because this source is a review.",
    ))
    t["yield_quality"].append(yield_row(
        rid, primary_yield_metric="review conclusion", yield_original="CNT synthesis reported with transition metals, poor/noble metals, ceramics/semiconductors, nano-diamond and catalyst-free routes",
        yield_definition_original="Qualitative literature synthesis; not an experimental yield.", secondary_result_summary="Catalytic behavior depends strongly on nanoscale state and support interactions; catalyst-free formation can occur under high-energy/high-temperature conditions.",
        CNT_type_reported="SWCNT and MWCNT across cited literature", CNT_type_confirmed="review_only", product_mixture_summary="not_applicable",
        CNT_type_evidence="reviewed TEM/Raman and synthesis literature", characterization_methods="literature review",
    ))
    t["cost_scale_review"].append(cost_row(
        rid, scale_evidence_summary="Review compares laboratory synthesis families rather than one scale demonstration.",
        cost_driver_summary="Catalyst composition/support, high-temperature energy and carbon-feed/reaction route are the main cross-study drivers.",
        safety_risk="Route-dependent high temperatures, flammable feeds, nanoparticle catalysts and arc/laser hazards.",
        emission_or_waste="Route-dependent CVD exhaust, soot and spent supported catalysts.",
    ))
    ev(t, store, sid, rid, "SPAN_A238FCB0BDBCD8EB8E89", "SPAN_832ACF80FA5987F00951", "SPAN_A238FCB0BDBCD8EB8E89", review=True)
    t["review_issue_log"].append(issue_row(f"{sid}_ISSUE_REVIEW", sid, rid, "source_scope", "source_run", rid, "data_type", "Review article: the row summarizes cited-literature scope and must not be interpreted as an author-generated synthesis run.", f"EVD_{rid}_CAT", "high"))
    return t


def build_ferrocene(m, store):
    sid = m["source_id"]
    t = base(m, "Four directly compared floating-catalyst precursors under otherwise common FC-CVD conditions.")
    recs = (
        ("FER", "ferrocene", "18.31", "1.1-4.8", "0.9-1.6", "2-10; mostly <7", "79", "mostly SWCNT; baseline precursor"),
        ("ACF", "acetylferrocene", "74.43", "1.5-6", "1.0-2.25", "3.59-19.04; mean 7.72", "90", "highest crystallinity; SWCNT with increased FWCNT fraction"),
        ("FCM", "ferrocenemethanol", "23.06", "1.5-5.1", "1.0-2.3", "5-38; mean 18.97", "90", "mostly SWCNT; OH group suppresses oxidation/carbon contamination"),
        ("DAF", "1,1'-diacetylferrocene", "47.12", "1.5-3.6", "1.0-1.7", "11-40; mostly 17-24", "not_reported", "mostly SWCNT but tube yield significantly lower; tube-like carbon laminates present"),
    )
    for code, precursor, igid, tem_range, rbm_range, particle, purity, outcome in recs:
        rid = f"{sid}_{code}"
        t["source_run"].append(run_row(sid, code, precursor, outcome))
        mean = "7.72" if code == "ACF" else "18.97" if code == "FCM" else "not_reported"
        prange = particle.split(";")[0]
        t["catalyst_system"].append(catalyst_row(
            rid, catalyst_label=f"{precursor}/thiophene floating catalyst", active_metals="Fe", support_material="floating/no solid support",
            metal_ratio_original="organometallic precursor:thiophene = 1 mol/mol", precursor_summary=f"{precursor}, thiophene and acetone stock solution",
            preparation_method="liquid injection FC-CVD", catalyst_particle_size_mean_nm=mean,
            catalyst_particle_size_range_nm=prange, catalyst_particle_size_qualifier=particle,
        ))
        t["reactor_process_gas"].append(process_row(
            rid, 1, "floating_catalyst_CVD", reactor_type="hot-zone FC-CVD reactor with outstream aerogel collection",
            temperature_setpoint_C="1200", carbon_source="acetone", carbon_source_flow_original="stock solution 12 mL/h",
            reducing_gas="H2 carrier", cofeed_or_reactive_gas="thiophene promoter at 1:1 molar ratio to organometallic precursor",
            gas_composition_summary="acetone/organometallic/thiophene injected at 12 mL/h in hydrogen",
        ))
        t["yield_quality"].append(yield_row(
            rid, primary_yield_metric="CNT purity/crystallinity", yield_original=(f"{purity}% purity; IG/ID {igid}" if purity != "not_reported" else f"purity not individually reported; IG/ID {igid}"),
            yield_definition_original="TGA residual-mass-derived purity and Raman IG/ID; no mass production yield", secondary_result_summary=outcome,
            CNT_type_reported="SWCNT/few-walled CNT", CNT_type_confirmed="predominantly SWCNT", product_mixture_summary=outcome,
            CNT_type_evidence="TEM, Raman RBM and TGA", outer_diameter_range_nm=tem_range,
            morphology=f"TEM diameter {tem_range} nm; RBM-derived diameter {rbm_range} nm", Raman_ratio_type="IG/ID", Raman_ratio_value=igid,
            TGA_carbon_content_wt_percent=purity, purity_basis="100 minus TGA residual mass" if purity != "not_reported" else "not individually quantified",
            characterization_methods="TEM; SEM; Raman 514 nm; XPS; XRD; TG-DSC; TGA",
        ))
        t["cost_scale_review"].append(cost_row(
            rid, scale_evidence_summary="Continuous liquid injection at 12 mL/h with outstream aerogel collection; laboratory direct-spinning-relevant FC-CVD.",
            cost_driver_summary="Specialty ferrocene derivative, thiophene/acetone, hydrogen and 1200 C reactor energy.",
            safety_risk="Hydrogen, volatile acetone/thiophene and organometallic precursor at 1200 C; CNT aerogel exposure.",
            emission_or_waste="Organic/ sulfur-containing FC-CVD exhaust and Fe-containing CNT residue.",
        ))
        ev(t, store, sid, rid, "SPAN_21E293577CCC44C49EA3", "SPAN_21E293577CCC44C49EA3", "SPAN_B292AD4850E22F7C7F78" if code != "FCM" else "SPAN_97C92F565C771645267D")
    return t


def build_como(m, store):
    sid = m["source_id"]
    t = base(m, "All 16 temperature/H2 combinations in Table 1 and all 12 pretreatment/growth-atmosphere combinations in Table 2.")
    catalyst = dict(
        catalyst_label="Co-Mo/MgO gel-combustion catalyst", active_metals="Co; Mo", support_material="MgO",
        metal_ratio_original="Co:Mo:MgO = 0.5:0.25:10 molar; 1.06 wt% Co and 0.86 wt% Mo",
        precursor_summary="Co(NO3)2·6H2O, (NH4)5Mo7O24·4H2O, Mg(NO3)2·6H2O and sorbitol",
        preparation_method="gel combustion", preparation_detail="dry 100 C 3 h; flash calcine 550 C 30 min; grind and sieve 75-250 micrometres",
    )
    table1 = (
        (850,50,"16.4","1.85","825"),(850,100,"16.2","1.57","816"),(850,150,"27.5","3.53","678"),(850,200,"7.8","2.63","795"),
        (900,50,"8.6","1.56","1501"),(900,100,"7.6","3.18","1094"),(900,150,"8.4","5.89","1024"),(900,200,"5.8","6.11","1093"),
        (950,50,"8.2","5.64","722"),(950,100,"6.7","4.64","635"),(950,150,"8.2","5.70","489"),(950,200,"2.3","7.01","1526"),
        (1000,50,"3.5","3.25","779"),(1000,100,"3.9","5.57","397"),(1000,150,"not_reported","5.87","339"),(1000,200,"3.1","13.63","292"),
    )
    for temp, h2, amorph, igid, yld in table1:
        code = f"T{temp}_H{h2}"
        rid = f"{sid}_{code}"
        outcome = f"CNT yield {yld}%; amorphous carbon {amorph}%; IG/ID {igid}"
        t["source_run"].append(run_row(sid, code, f"{temp} C, H2 {h2} sccm", outcome))
        t["catalyst_system"].append(catalyst_row(rid, **catalyst))
        t["reactor_process_gas"].append(process_row(
            rid, 1, "thermal_CVD", reactor_type="1-inch quartz tube at atmospheric pressure", temperature_setpoint_C=str(temp), holding_time_min="40",
            pressure_original="atmospheric", pressure_kPa="101.325", carbon_source="CH4", carbon_source_flow_original="50 sccm", carbon_source_flow_sccm="50",
            reducing_gas="H2", reducing_gas_flow_original=f"{h2} sccm", reducing_gas_flow_sccm=str(h2),
            gas_composition_summary=f"CH4 50 sccm + H2 {h2} sccm after H2 pretreatment at 850 C for 1 h",
            process_note="15 mg catalyst; 5 C/min ramp; same H2 flow used for pretreatment and growth as tabulated.",
        ))
        t["yield_quality"].append(yield_row(
            rid, primary_yield_metric="CNT gravimetric yield", yield_original=f"{yld}%", yield_value_standardized=yld, yield_unit_standardized="wt.% relative to catalyst",
            yield_definition_original="[(product mass - catalyst mass)/catalyst mass] x 100 after subtracting TGA-derived amorphous carbon",
            secondary_result_summary=outcome, CNT_type_reported="carbon nanotubes; SWCNT RBM at higher H2 flow", CNT_type_confirmed="CNT",
            product_mixture_summary=f"CNT with {amorph}% amorphous carbon", CNT_type_evidence="SEM; TGA; Raman; TEM",
            Raman_ratio_type="IG/ID", Raman_ratio_value=igid, TGA_carbon_content_wt_percent=(str(100-float(amorph)) if amorph != "not_reported" else "not_reported"),
            purity_basis="100 minus TGA amorphous-carbon percentage", characterization_methods="SEM; TGA; Raman; TEM",
        ))
        t["cost_scale_review"].append(cost_row(
            rid, scale_evidence_summary="15 mg catalyst atmospheric tube-CVD screening run.", cost_driver_summary="Co/Mo salts, MgO support, 40 min at high temperature, CH4 and H2.",
            safety_risk="Hydrogen/methane at 850-1000 C; cobalt/nickel-like transition-metal nanoparticle and CNT exposure.",
            emission_or_waste="Methane/H2 CVD exhaust and MgO/Co/Mo-containing CNT product.",
        ))
        ev(t, store, sid, rid, "SPAN_11E47F81090B2AC29C0D", "SPAN_11E47F81090B2AC29C0D", "SPAN_3D30EF9DFEC2ED73250A")

    pretreatments = (
        ("H200", "H2 200 sccm", "200", "0"),
        ("AR200", "Ar 200 sccm", "0", "200"),
        ("H10AR190", "H2 10 + Ar 190 sccm", "10", "190"),
        ("AR_HEAT_H", "Ar heat-up then H2 200 sccm at 850 C for 1 h; switch to Ar", "200", "200"),
    )
    atmos = (
        ("H2", "50", "200", "0", (("2.8","292"),("7.9","93"),("3.2","243"),("6.7","67"))),
        ("MIX", "20", "20", "210", (("4.4","140"),("6.9","41"),("5.9","174"),("6.3","68"))),
        ("AR", "40", "0", "210", (("3.1","349"),("2.0","172"),("2.1","237"),("1.9","368"))),
    )
    for acode, ch4, gh2, gar, outcomes in atmos:
        for idx, (pcode, plabel, ph2, par) in enumerate(pretreatments):
            amorph, yld = outcomes[idx]
            code = f"ATM_{pcode}_{acode}"
            rid = f"{sid}_{code}"
            outcome = f"CNT yield {yld}%; amorphous carbon {amorph}%"
            t["source_run"].append(run_row(sid, code, f"{plabel}; {acode} growth", outcome))
            t["catalyst_system"].append(catalyst_row(rid, **catalyst))
            t["reactor_process_gas"].append(process_row(
                rid, 1, "thermal_CVD_atmosphere_comparison", reactor_type="1-inch quartz tube at atmospheric pressure",
                temperature_setpoint_C="1000", holding_time_min="40", pressure_original="atmospheric", pressure_kPa="101.325",
                carbon_source="CH4", carbon_source_flow_original=f"{ch4} sccm", carbon_source_flow_sccm=ch4,
                reducing_gas="H2", reducing_gas_flow_original=f"growth {gh2} sccm; pretreatment {ph2} sccm", reducing_gas_flow_sccm=gh2,
                inert_gas="Ar", inert_gas_flow_original=f"growth {gar} sccm; pretreatment {par} sccm", inert_gas_flow_sccm=gar,
                total_flow_original="250 sccm during growth; 200 sccm during pretreatment", total_flow_sccm="250",
                gas_composition_summary=f"pretreatment {plabel}; growth CH4/H2/Ar {ch4}/{gh2}/{gar} sccm",
            ))
            t["yield_quality"].append(yield_row(
                rid, primary_yield_metric="CNT gravimetric yield", yield_original=f"{yld}%", yield_value_standardized=yld, yield_unit_standardized="wt.% relative to catalyst",
                yield_definition_original="[(product mass - catalyst mass)/catalyst mass] x 100 after subtracting TGA-derived amorphous carbon",
                secondary_result_summary=outcome, CNT_type_reported="predominantly SWCNT under best H2 condition; larger diameter under Ar growth",
                CNT_type_confirmed="CNT", product_mixture_summary=f"CNT with {amorph}% amorphous carbon", CNT_type_evidence="SEM; TEM; Raman; TGA",
                TGA_carbon_content_wt_percent=str(100-float(amorph)), purity_basis="100 minus TGA amorphous-carbon percentage", characterization_methods="SEM; TGA; Raman; TEM",
            ))
            t["cost_scale_review"].append(cost_row(
                rid, scale_evidence_summary="15 mg catalyst atmospheric tube-CVD atmosphere-comparison run.",
                cost_driver_summary="Co/Mo salts, MgO, 1000 C furnace, 40 min duration and H2/Ar/CH4 consumption.",
                safety_risk="Hydrogen/methane at 1000 C; Co/Mo and CNT powders.", emission_or_waste="CVD exhaust and metal/MgO-containing CNT residue.",
            ))
            ev(t, store, sid, rid, "SPAN_11E47F81090B2AC29C0D", "SPAN_7368722E250E670D5C16", "SPAN_7368722E250E670D5C16")
    return t


BUILDERS: dict[str, Callable] = {
    "LIT_920AD764C13FB11B": build_wafer,
    "LIT_954C0D690A6F7711": build_sic_composite,
    "LIT_960D4EBE5F445BFD": build_review,
    "LIT_9A6884F1BCF7D6CC": build_ferrocene,
    "LIT_9B4BCF02D1067EA7": build_como,
}


def main():
    metadata = load_metadata("B")
    store = EvidenceStore()
    metrics = []
    try:
        for sid in SOURCE_IDS:
            metric = existing_package_metric(sid, "B")
            if metric is None:
                metrics.append(publish_package(sid, BUILDERS[sid](metadata[sid], store)))
            else:
                metrics.append(metric)
    finally:
        store.close()
    result = {
        "batch_id": BATCH_NAME, "sources": metrics,
        "total_runs": sum(x["row_counts"]["source_run"] for x in metrics),
        "status": "completed_needs_review",
    }
    (REPORT_ROOT / "manual_batch_018_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
