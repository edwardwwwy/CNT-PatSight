#!/usr/bin/env python3
"""Build the thirty-eighth evidence-grounded A-class extraction batch."""

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

BATCH_NUMBER = 38
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_C218734AA7F3AF9E"
PDF_REF = "data/raw/fulltext/pdf/LIT_C218734AA7F3AF9E_e4935d687e31.pdf"

METHOD_SPAN = "SPAN_EE7070461D2605B8AB72"
GAS_SPAN = "SPAN_B19D576CEDD258846390"
YIELD_SPAN = "SPAN_DC0B25A67D388B3605ED"
MORPH_SPAN = "SPAN_4F5EA9F3CCF41E2298A5"
BUNDLE_SPAN = "SPAN_6158503DFBCC0C8467A0"
CHIRAL_SPAN = "SPAN_C2607668E9242C18847A"
TCF_SPAN = "SPAN_5DE19E26B87ADCC46D3D"
TCF_LATE_SPAN = "SPAN_4B79A4D723D85A838995"
CONCLUSION_SPAN = "SPAN_0CF0E4BCFA62000E0283"


def rec(
    metal: str,
    sulfur: int,
    role: str,
    *,
    norm_yield: float | None = None,
    nc_change: str = "",
    diameter: float | None = None,
    igid: float | None = None,
    length: float | None = None,
    individual: float | None = None,
    bundle_count: int | None = None,
    sheet: int | None = None,
    doped_sheet: int | None = None,
    semicon: int | None = None,
    outcome: str,
) -> dict[str, Any]:
    return locals()


RUNS = [
    rec(
        "Fe",
        0,
        "baseline",
        norm_yield=1.0,
        diameter=1.06,
        igid=13,
        length=3.4,
        individual=13,
        bundle_count=9,
        sheet=1512,
        doped_sheet=243,
        semicon=61,
        outcome="baseline Fe-SWCNT film",
    ),
    rec(
        "Fe",
        1,
        "maximum_yield",
        norm_yield=2.5,
        nc_change="+37%",
        diameter=1.26,
        outcome="maximum normalized yield and aerosol number concentration",
    ),
    rec(
        "Fe",
        5,
        "maximum_conductance",
        diameter=1.26,
        igid=19,
        length=4.2,
        individual=21,
        bundle_count=5,
        sheet=469,
        doped_sheet=116,
        semicon=59,
        outcome="maximum pristine sheet conductance and detailed morphology optimum",
    ),
    rec(
        "Fe",
        10,
        "excess_sulfur",
        norm_yield=0.15,
        nc_change="-90%",
        outcome="strong yield and active-particle suppression",
    ),
    rec(
        "Co",
        0,
        "baseline",
        norm_yield=1.0,
        diameter=1.05,
        igid=11,
        individual=11,
        bundle_count=12,
        sheet=1704,
        doped_sheet=274,
        semicon=61,
        outcome="baseline Co-SWCNT film",
    ),
    rec(
        "Co",
        2,
        "maximum_yield",
        norm_yield=2.5,
        nc_change="+34%",
        diameter=1.24,
        outcome="maximum normalized yield and aerosol number concentration",
    ),
    rec(
        "Co",
        8,
        "maximum_conductance",
        diameter=1.24,
        igid=21,
        individual=18,
        bundle_count=5,
        sheet=508,
        doped_sheet=132,
        semicon=66,
        outcome="maximum pristine sheet conductance and detailed morphology optimum",
    ),
    rec(
        "Co",
        10,
        "excess_sulfur",
        norm_yield=0.15,
        nc_change="-90%",
        outcome="strong yield and active-particle suppression",
    ),
]


def summary(x: dict[str, Any]) -> str:
    details = []
    for label, key, unit in [
        ("normalized yield", "norm_yield", "x baseline"),
        ("NC change", "nc_change", ""),
        ("mean diameter", "diameter", "nm"),
        ("IG/ID", "igid", ""),
        ("bundle length", "length", "micrometre"),
        ("individual tubes", "individual", "%"),
        ("tubes/bundle", "bundle_count", ""),
        ("R90 pristine", "sheet", "ohm/sq"),
        ("R90 AuCl3-doped", "doped_sheet", "ohm/sq"),
        ("semiconducting", "semicon", "%"),
    ]:
        if x[key] is not None and x[key] != "":
            details.append(f"{label} {x[key]} {unit}".strip())
    return (
        f"{x['metal']} spark-generated catalyst, H2S {x['sulfur']} ppm, "
        "1050 C vertical FC-CVD with C2H4 0.1 sccm, H2 80 sccm and "
        f"500 sccm total flow: {x['outcome']}; " + "; ".join(details) + "."
    )


def catalyst(x: dict[str, Any], run_id: str) -> dict[str, str]:
    purity = "99.8%" if x["metal"] == "Fe" else "99.95%"
    return catalyst_row(
        run_id,
        catalyst_label=f"spark-generated {x['metal']} aerosol nanoparticles",
        active_metals=x["metal"],
        support_material="unsupported aerosol particles",
        promoter=f"H2S sulfur promoter at {x['sulfur']} ppm",
        metal_ratio_original=f"pure {x['metal']} electrode, {purity}",
        metal_ratio_standardized=f"{x['metal']} with {x['sulfur']} ppm H2S",
        precursor_summary=f"{purity} {x['metal']} rod/tube electrodes",
        preparation_method="spark discharge generator",
        preparation_modifier="2-3 kV evaporation-nucleation-condensation in N2",
        preparation_detail="Rod-to-tube spark discharge; particles carried directly to FC-CVD by N2.",
        drying_condition="not_applicable",
        calcination_condition="not_applicable",
        reduction_condition="80 sccm H2 at 1050 C during growth",
        activation_condition="pre-made particles exposed to ethylene/H2/H2S",
        post_preparation_condition="average mobility size about 3.5 nm; NC about 4.3e6 cm-3",
        catalyst_particle_size_mean_nm="",
        catalyst_particle_size_range_nm="",
        catalyst_particle_size_qualifier="Average catalyst mobility size fixed near 3.5 nm; retained as aerosol context.",
        phase_or_state_summary=f"{x['metal']} aerosol nanoparticles with sulfur-modified surface",
        dispersion_summary="number concentration fixed near 4.3e6 cm-3",
        deactivation_summary="excess H2S reduced active-particle fraction and SWCNT yield",
    )


def process(x: dict[str, Any], run_id: str) -> dict[str, str]:
    h2s_flow = x["sulfur"] / 0.2
    n2 = 420 - h2s_flow
    return process_row(
        run_id,
        1,
        "sulfur_assisted_FC_CVD",
        reactor_type="vertical floating-catalyst CVD reactor",
        scale_level="laboratory_continuous_aerosol",
        reactor_material="not_reported",
        reactor_size_summary="not_reported",
        reactor_setup_summary="spark generator coupled to vertical reactor and membrane filter",
        catalyst_loading_mass_g="",
        temperature_setpoint_C="1050",
        temperature_range_reported_C="1050",
        temperature_program_summary="continuous isothermal aerosol growth",
        holding_time_min="180 min film collection for normalized yield",
        heating_rate_C_min="not_applicable_continuous",
        cooling_condition="as-grown aerosol collected on 13 mm membrane filter",
        pressure_original="not_reported",
        pressure_kPa="",
        carbon_source="C2H4",
        carbon_source_flow_original="0.1 sccm (200 ppm)",
        reducing_gas="H2",
        reducing_gas_flow_original="80 sccm",
        inert_gas="N2",
        inert_gas_flow_original=f"about {n2:g} sccm from spark generator",
        cofeed_or_reactive_gas="0.01 vol% H2S in N2",
        cofeed_flow_original=f"{h2s_flow:g} sccm diluted stream = {x['sulfur']} ppm H2S",
        total_flow_original="500 sccm",
        gas_composition_summary=f"C2H4 0.1, H2 80, H2S {x['sulfur']} ppm, N2 balance",
        process_note="H2S and SDG N2 flows were counter-adjusted to keep total flow/residence time constant.",
    )


def product(x: dict[str, Any], run_id: str) -> dict[str, str]:
    sec = summary(x)
    return yield_row(
        run_id,
        primary_yield_metric="normalized_SWNCT_film_yield",
        yield_original=(
            "not numerically reported"
            if x["norm_yield"] is None
            else f"{x['norm_yield']} times 0-ppm baseline"
        ),
        yield_definition_original="Beer-Lambert-normalized film thickness after fixed 3 h collection",
        yield_calculation_method="550 nm transmittance of film on 13 mm filter",
        yield_value_standardized=""
        if x["norm_yield"] is None
        else str(x["norm_yield"]),
        yield_unit_standardized="relative_to_0_ppm_baseline",
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=sec,
        CNT_type_reported="SWCNT",
        CNT_type_confirmed="SWCNT",
        product_mixture_summary="SWCNT thin film with Fe or Co catalyst residue",
        CNT_type_evidence="OAS; Raman RBM; HR-TEM; electron diffraction",
        SWCNT_or_few_wall_evidence_summary="single-walled; chirality spans zig-zag to armchair",
        RBM_peak_reported="reported with 488, 514 and 633 nm excitation",
        outer_diameter_mean_nm="" if x["diameter"] is None else str(x["diameter"]),
        outer_diameter_range_nm="",
        inner_diameter_mean_nm="",
        wall_number_summary="single-walled",
        length_summary=""
        if x["length"] is None
        else f"average bundle length {x['length']} micrometre",
        morphology=x["outcome"],
        alignment_or_array="thin-film bundle network",
        Raman_ratio_type="IG/ID" if x["igid"] is not None else "not_reported",
        Raman_ratio_value="" if x["igid"] is None else str(x["igid"]),
        Raman_laser_wavelength_nm="488; 514; 633",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis="as-grown film",
        residue_summary=f"{x['metal']} catalyst residue; sulfur not quantitatively assigned per run",
        amorphous_carbon_level="quality improved at optimized sulfur; not mass-quantified",
        BET_surface_area_product_m2_g="",
        characterization_methods="UV-Vis-NIR; Raman; SEM; HR-TEM; ED; DMA; XPS; four-probe",
        post_treatment_or_purification="dry press-transfer; optional AuCl3 doping",
        purification_condition="16 mM AuCl3 in acetonitrile, washed and N2-dried for doped films",
        application_property_summary=(
            ""
            if x["sheet"] is None
            else f"R90 pristine {x['sheet']} ohm/sq; doped {x['doped_sheet']} ohm/sq at 90% T550"
        ),
        notes=(
            f"NC change {x['nc_change']}; individual-tube fraction {x['individual']}%; "
            f"average bundle count {x['bundle_count']}; semiconducting fraction {x['semicon']}%."
        ),
    )


def cost_review(x: dict[str, Any], run_id: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="laboratory continuous FC-CVD",
        scale_level_claimed="continuous scalable single-step TCF production",
        scale_evidence_summary=summary(x),
        reactor_capacity_or_throughput="500 sccm total; 3 h film collection on 13 mm filter",
        continuous_operation_time_h="3",
        catalyst_lifetime_or_reuse="continuous spark generation",
        catalyst_reuse_cycles="not_applicable",
        batch_stability="not_reported",
        scale_up_issue="spark-generator throughput, H2S control, film area, collection and doping",
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="No study-specific cost analysis.",
        cost_driver_summary="1050 C heat, high-purity gases, electrodes and AuCl3 doping",
        safety_risk="toxic H2S; flammable H2/ethylene; high voltage and temperature",
        emission_or_waste="H2S-containing offgas and dopant solvent waste",
        industrial_readiness_assessment="laboratory continuous TCF demonstration",
        reproduction_value="high",
        reproduction_priority="high",
        recommended_next_action="report absolute mass yield, sulfur balance, long-run stability and scale economics",
        review_note="Normalized optical yield is not mass productivity.",
    )


def result_span(x: dict[str, Any]) -> str:
    if x["role"] in {"maximum_yield", "excess_sulfur"}:
        return YIELD_SPAN
    if x["role"] == "maximum_conductance":
        return MORPH_SPAN
    return TCF_SPAN


def add_ev(
    tables,
    store,
    run_id,
    suffix,
    table,
    record_id,
    span,
    text,
    summary_text,
    status="reported",
):
    e = evidence_row(
        store,
        SOURCE_ID,
        f"EVD_{run_id}_{suffix}",
        run_id,
        table,
        record_id,
        "record_level",
        span,
        summary_text,
        confidence="high",
        value_status=status,
    )
    e.update(
        {
            "evidence_type": "pdf_text_transcription",
            "source_section": "accepted-manuscript PDF",
            "source_locator": "accepted-manuscript PDF",
            "source_object_ref": PDF_REF,
            "evidence_text": text,
            "evidence_summary": summary_text,
            "notes": "Values checked against the local accepted-manuscript PDF.",
        }
    )
    tables["evidence_index"].append(e)


def add_run(tables, store, x):
    run_id = f"{SOURCE_ID}_{x['metal'].upper()}_H2S_{x['sulfur']}_{x['role'].upper()}"
    s = summary(x)
    tables["source_run"].append(
        run_row(
            SOURCE_ID,
            run_id.removeprefix(f"{SOURCE_ID}_"),
            f"{x['metal']} {x['sulfur']} ppm H2S",
            s,
            "high",
        )
    )
    cat, stage, prod, cost = (
        catalyst(x, run_id),
        process(x, run_id),
        product(x, run_id),
        cost_review(x, run_id),
    )
    tables["catalyst_system"].append(cat)
    tables["reactor_process_gas"].append(stage)
    tables["yield_quality"].append(prod)
    tables["cost_scale_review"].append(cost)
    span = result_span(x)
    add_ev(
        tables,
        store,
        run_id,
        "RUN",
        "source_run",
        run_id,
        span,
        s,
        "Run identity and sulfur-dependent result.",
    )
    add_ev(
        tables,
        store,
        run_id,
        "CATALYST",
        "catalyst_system",
        cat["catalyst_id"],
        METHOD_SPAN,
        f"{cat['catalyst_label']}; active {cat['active_metals']}; promoter {cat['promoter']}; precursor {cat['precursor_summary']}; preparation {cat['preparation_detail']}; aerosol context {cat['post_preparation_condition']}.",
        "Spark-generated catalyst and sulfur promoter.",
    )
    add_ev(
        tables,
        store,
        run_id,
        "PROCESS",
        "reactor_process_gas",
        stage["process_stage_id"],
        GAS_SPAN,
        f"Temperature 1050 C; time {stage['holding_time_min']}; pressure {stage['pressure_original']} / {stage['pressure_kPa']} kPa; C2H4 0.1 sccm (200 ppm); H2 80 sccm; N2 {stage['inert_gas_flow_original']}; H2S {stage['cofeed_flow_original']}; total 500 sccm.",
        "FC-CVD gas and collection conditions.",
    )
    add_ev(
        tables,
        store,
        run_id,
        "PRODUCT",
        "yield_quality",
        prod["product_id"],
        span,
        f"{s} Yield {prod['yield_original']}; diameter {prod['outer_diameter_mean_nm']} nm; Raman IG/ID {prod['Raman_ratio_value']} with 488, 514 and 633 nm lasers; length {prod['length_summary']}; application {prod['application_property_summary']}; notes {prod['notes']}.",
        "Yield, morphology, chirality and TCF performance.",
    )
    add_ev(
        tables,
        store,
        run_id,
        "BUNDLE",
        "yield_quality",
        prod["product_id"],
        BUNDLE_SPAN,
        f"Individual fraction {x['individual']}%; average tubes per bundle {x['bundle_count']}; bundle length {x['length']} micrometre; diameter {x['diameter']} nm; semiconducting fraction {x['semicon']}%.",
        "Bundle and electron-diffraction statistics.",
    )
    add_ev(
        tables,
        store,
        run_id,
        "COST",
        "cost_scale_review",
        run_id,
        CONCLUSION_SPAN,
        "Continuous 500 sccm laboratory process; no cost or mass balance. H2S, H2/ethylene, high voltage and AuCl3/acetonitrile require controls.",
        "Scale, cost-data gap and safety review.",
        "review_assessment",
    )
    return run_id


def build(metadata, store):
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            metadata,
            "Eight records: Fe and Co baselines, maximum-yield sulfur levels, maximum-conductance levels, and 10 ppm excess-sulfur endpoints.",
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_accepted_manuscript_pdf"
    ids = {(x["metal"], x["sulfur"]): add_run(tables, store, x) for x in RUNS}
    fe0, fe1, fe5, fe10 = (
        ids[("Fe", 0)],
        ids[("Fe", 1)],
        ids[("Fe", 5)],
        ids[("Fe", 10)],
    )
    co0, co2, co8, co10 = (
        ids[("Co", 0)],
        ids[("Co", 2)],
        ids[("Co", 8)],
        ids[("Co", 10)],
    )
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_NORMALIZED_001",
                SOURCE_ID,
                fe1,
                "metric_definition",
                "yield_quality",
                f"{fe1}_PROD",
                "yield_original",
                "Yield is normalized from optical film transmittance relative to 0 ppm H2S, not a mass yield.",
                f"EVD_{fe1}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_OPTIMA_DIFFER_001",
                SOURCE_ID,
                fe5,
                "multiple_optima",
                "source_run",
                fe5,
                "run_summary",
                "Maximum yield occurs at Fe 1 ppm/Co 2 ppm, while maximum sheet conductance occurs at Fe 5 ppm/Co 8 ppm; these are distinct physical runs.",
                f"EVD_{fe1}_RUN;EVD_{co2}_RUN;EVD_{fe5}_RUN;EVD_{co8}_RUN",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CO_LENGTH_001",
                SOURCE_ID,
                co8,
                "measurement_scope",
                "yield_quality",
                f"{co8}_PROD",
                "length_summary",
                "The paper says Co bundle length showed a similar 25% improvement but does not print the two absolute Co length means.",
                f"EVD_{co8}_BUNDLE",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_10PPM_SHARED_001",
                SOURCE_ID,
                fe10,
                "shared_summary_value",
                "yield_quality",
                f"{fe10}_PROD",
                "yield_original",
                "At 10 ppm, yield about 15% of baseline and NC about 90% lower are stated jointly for both catalysts; separate Fe/Co exact values are not printed.",
                f"EVD_{fe10}_PRODUCT;EVD_{co10}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CHIRALITY_001",
                SOURCE_ID,
                fe5,
                "interpretation_limit",
                "yield_quality",
                f"{fe5}_PROD",
                "SWCNT_or_few_wall_evidence_summary",
                "Sulfur shifted diameter distributions but did not provide effective chirality control; distributions remained broad from zig-zag to armchair.",
                f"EVD_{fe5}_PRODUCT;EVD_{co8}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_NO_MASS_YIELD_001",
                SOURCE_ID,
                co8,
                "critical_data_gap",
                "yield_quality",
                f"{co8}_PROD",
                "CNT_yield_per_catalyst_g_gcat",
                "No CNT mass yield, catalyst-normalized productivity, carbon conversion or sulfur mass balance was reported.",
                f"EVD_{co8}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PRESSURE_001",
                SOURCE_ID,
                fe0,
                "critical_data_gap",
                "reactor_process_gas",
                f"{fe0}_S01",
                "pressure_original",
                "FC-CVD operating pressure and reactor dimensions were not reported in the main manuscript.",
                f"EVD_{fe0}_PROCESS",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_DOPING_BOUNDARY_001",
                SOURCE_ID,
                co0,
                "post_treatment_scope",
                "yield_quality",
                f"{co0}_PROD",
                "application_property_summary",
                "AuCl3-doped sheet resistance is a post-treated application result and is kept separate from pristine-film R90.",
                f"EVD_{co0}_PRODUCT",
                "high",
            ),
        ]
    )
    return tables


def main():
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
    (BATCH_ROOT / f"batch_{BATCH_NUMBER:03d}_metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
