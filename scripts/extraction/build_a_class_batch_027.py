#!/usr/bin/env python3
"""Build the twenty-seventh evidence-grounded A-class extraction batch."""

from __future__ import annotations

import json
from typing import Any

from scripts.extraction.batch_common import (
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


BATCH_NUMBER = 27
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ID = "LIT_11B9044BBBEDF0FD"
PDF_REF = "data/raw/literature/pdf/LIT_11B9044BBBEDF0FD_mdpi.pdf"

CATALYST_SPAN = "SPAN_9D417DBEACAC347A1AF0"
PROCESS_SPAN = "SPAN_2110CA8B98874D6A2290"
XRD_SPAN = "SPAN_8C48EC83DDB6F47DE988"
RAMAN_SPAN = "SPAN_006FCDC9C18363E34136"
BET_SPAN = "SPAN_60686BBC2741365873B0"
TEM_SPAN = "SPAN_05D78377EBD54192BDDA"
TGA_SPAN = "SPAN_FA8D1CC4A0327C7D20CB"
ELECTRO_SPAN = "SPAN_234FCA810298F7A6FA0B"

SAMPLES: list[dict[str, Any]] = [
    {
        "name": "HNi10-600",
        "ni": 10,
        "temperature": 600,
        "raman": "",
        "bet": "",
        "pore_volume": "",
        "pore_diameter": "",
        "loss1_range": "",
        "loss1": "",
        "loss2_range": "",
        "loss2": "",
        "electro_area": "",
        "roughness": "",
        "negative": True,
    },
    {
        "name": "HNi10-700",
        "ni": 10,
        "temperature": 700,
        "raman": 1.19,
        "bet": 13,
        "pore_volume": 0.084,
        "pore_diameter": 260,
        "loss1_range": "350-373",
        "loss1": 13.11,
        "loss2_range": "537-576",
        "loss2": 14.06,
        "electro_area": "0.168 +/- 0.031",
        "roughness": 2.37,
    },
    {
        "name": "HNi10-750",
        "ni": 10,
        "temperature": 750,
        "raman": 1.22,
        "bet": 12,
        "pore_volume": 0.078,
        "pore_diameter": 250,
        "loss1_range": "330-423",
        "loss1": 2.73,
        "loss2_range": "537-655",
        "loss2": 15.26,
        "electro_area": "0.334 +/- 0.053",
        "roughness": 4.73,
    },
    {
        "name": "HNi10-800",
        "ni": 10,
        "temperature": 800,
        "raman": 1.30,
        "bet": 10,
        "pore_volume": 0.069,
        "pore_diameter": 290,
        "loss1_range": "200-477",
        "loss1": 18.35,
        "loss2_range": "573-708",
        "loss2": 15.78,
        "electro_area": "0.380 +/- 0.051",
        "roughness": 5.37,
        "k0": "1.1 x 10^-2 cm/s",
    },
    {
        "name": "HNi10-850",
        "ni": 10,
        "temperature": 850,
        "raman": 1.19,
        "bet": 6,
        "pore_volume": 0.051,
        "pore_diameter": 340,
        "loss1_range": "300-452",
        "loss1": 2.98,
        "loss2_range": "540-600",
        "loss2": 11.47,
        "electro_area": "0.277 +/- 0.050",
        "roughness": 3.93,
    },
    {
        "name": "HNi10-900",
        "ni": 10,
        "temperature": 900,
        "raman": 1.16,
        "bet": 7,
        "pore_volume": 0.063,
        "pore_diameter": 360,
        "loss1_range": "357-381",
        "loss1": 13.90,
        "loss2_range": "549-609",
        "loss2": 26.77,
        "electro_area": "0.188 +/- 0.026",
        "roughness": 2.66,
    },
    {
        "name": "HNi5-800",
        "ni": 5,
        "temperature": 800,
        "raman": 1.17,
        "bet": 8,
        "pore_volume": 0.067,
        "pore_diameter": 330,
        "loss1_range": "345-369",
        "loss1": 17.24,
        "loss2_range": "537-579",
        "loss2": 8.68,
        "electro_area": "",
        "roughness": "",
    },
    {
        "name": "HNi15-800",
        "ni": 15,
        "temperature": 800,
        "raman": 1.22,
        "bet": 11,
        "pore_volume": 0.069,
        "pore_diameter": 240,
        "loss1_range": "349-376",
        "loss1": 8.43,
        "loss2_range": "540-581",
        "loss2": 5.76,
        "electro_area": "",
        "roughness": "",
        "loss3": "4.534 wt% at 684-700 C",
    },
    {
        "name": "HNi20-800",
        "ni": 20,
        "temperature": 800,
        "raman": 1.22,
        "bet": 8,
        "pore_volume": 0.070,
        "pore_diameter": 370,
        "loss1_range": "342-367",
        "loss1": 13.46,
        "loss2_range": "523-568",
        "loss2": 8.83,
        "electro_area": "",
        "roughness": "",
    },
]


def sample_summary(item: dict[str, Any]) -> str:
    if item.get("negative"):
        return (
            "Ni/CaO 10 wt% at 600 C was included in the reported 600-900 C "
            "temperature screen, but the authors state that at least 700 C "
            "was required for an XRD CNT peak. No BET, TGA, Raman, microscopy "
            "or electrochemical values were reported for the 600 C product."
        )
    parts = [
        f"{item['name']} CQN: Ni/CaO {item['ni']} wt%, CVD at {item['temperature']} C",
        f"Raman IG/ID {item['raman']}",
        f"BET {item['bet']} m2/g",
        f"pore volume {item['pore_volume']} cm3/g",
        f"BJH pore diameter {item['pore_diameter']} A",
        (
            f"TGA loss 1 {item['loss1']} wt% at {item['loss1_range']} C "
            "(assigned by the paper to amorphous carbon)"
        ),
        (
            f"TGA loss 2 {item['loss2']} wt% at {item['loss2_range']} C "
            "(assigned by the paper to CNT oxidation)"
        ),
    ]
    if item["electro_area"]:
        parts.extend(
            [
                f"SPCE electroactive area {item['electro_area']} cm2",
                f"roughness factor {item['roughness']}",
            ]
        )
    if item.get("k0"):
        parts.append(f"heterogeneous electron-transfer rate constant {item['k0']}")
    if item.get("loss3"):
        parts.append(f"third stable-carbon/graphitic-soot loss {item['loss3']}")
    if item["name"] == "HNi10-800":
        parts.append(
            "highest graphitization, electroactive area and average CV peak current"
        )
    if item["name"] == "HNi15-800":
        parts.append("highest XRD CNT (002) intensity and highest BET at 800 C")
    if item["name"] == "HNi10-900":
        parts.append(
            "highest temperature-series XRD intensity but additional peaks "
            "and the largest CNT-associated TGA loss"
        )
    return "; ".join(parts) + "."


def catalyst(run_id: str, ni: int) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label=f"Ni/CaO catalyst, nominal {ni} wt% Ni",
        active_metals="Ni",
        support_material="CaO quicklime derived from local carbonate stones",
        promoter="none reported",
        metal_ratio_original=f"{ni} wt% Ni nitrate salt loading for Ni/CaO preparation",
        metal_ratio_standardized=f"{ni} wt% Ni nominal",
        precursor_summary="nickel(II) nitrate hexahydrate; carbonate-stone-derived CaO",
        preparation_method="aqueous impregnation followed by evaporative drying",
        preparation_modifier="CaO support calcined from carbonate stone",
        preparation_detail=(
            "Crushed carbonate stone calcined at 1000 C for 5 h, ground and "
            "sieved to 90 um. Ni nitrate was dissolved in 40 mL water, CaO "
            "added directly, stirred at 70 +/- 10 C to evaporate solvent, "
            "oven-dried at 70 +/- 10 C overnight and re-sieved to 90 um."
        ),
        drying_condition="70 +/- 10 C overnight",
        calcination_condition="carbonate stone at 1000 C for 5 h",
        reduction_condition="not_reported",
        activation_condition="in-situ heating under N2 before n-hexane introduction",
        post_preparation_condition="stored in sample bottle; sieved to 90 um",
        catalyst_particle_size_mean_nm="",
        catalyst_particle_size_range_nm="",
        catalyst_particle_size_qualifier=(
            "No quantitative catalyst-particle distribution; spherical Ni/support "
            "particles remained outside, at tips, and sometimes inside CNTs."
        ),
        phase_or_state_summary="Ni-containing particles on CaO; residual CaO and Ni in CQN",
        dispersion_summary="qualitative only; high Ni can aggregate into larger clusters",
        deactivation_summary="not_reported",
    )


def stages(run_id: str, item: dict[str, Any]) -> list[dict[str, str]]:
    composition_series = item["temperature"] == 800
    return [
        process_row(
            run_id,
            1,
            "quicklime_support_preparation",
            reactor_type="high-temperature calcination furnace",
            scale_level="lab_batch",
            reactor_material="not_reported",
            reactor_size_summary="not_reported",
            reactor_setup_summary="crushed local carbonate stones",
            catalyst_loading_mass_g="not_reported",
            temperature_setpoint_C="1000",
            temperature_program_summary="calcination at 1000 C",
            holding_time_min="300",
            heating_rate_C_min="not_reported",
            cooling_condition="not_reported",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source="carbonate stone precursor",
            reducing_gas="none",
            inert_gas="not_reported",
            cofeed_or_reactive_gas="air atmosphere not explicitly stated",
            gas_composition_summary="calcination atmosphere not reported",
            process_note="Ground after calcination and sieved through 90 um mesh.",
        ),
        process_row(
            run_id,
            2,
            "nickel_impregnation_and_drying",
            reactor_type="heated stirred impregnation vessel and drying oven",
            scale_level="lab_batch",
            reactor_material="not_reported",
            reactor_size_summary="40 mL distilled-water preparation",
            reactor_setup_summary=f"nominal {item['ni']} wt% Ni nitrate on CaO",
            catalyst_loading_mass_g="not_reported",
            temperature_setpoint_C="70 +/- 10",
            temperature_program_summary="heated stirring to evaporate water; oven dry overnight",
            holding_time_min="overnight drying; exact hours not reported",
            heating_rate_C_min="not_applicable",
            cooling_condition="not_reported",
            pressure_original="atmospheric",
            pressure_kPa="101.325",
            carbon_source="none",
            reducing_gas="none",
            inert_gas="none",
            cofeed_or_reactive_gas="nickel(II) nitrate hexahydrate in distilled water",
            cofeed_flow_original=f"{item['ni']} wt% nominal Ni salt; 40 mL water",
            total_flow_original="not_applicable",
            gas_composition_summary="not_applicable",
            process_note="Dried solid was sieved through 90 um mesh.",
        ),
        process_row(
            run_id,
            3,
            "n_hexane_cvd",
            reactor_type="horizontal atmospheric-pressure CVD furnace",
            scale_level="lab_batch",
            reactor_material="quartz tube with alumina catalyst boat",
            reactor_size_summary="quartz tube OD 25 mm x ID 20 mm x length 1000 mm",
            reactor_setup_summary="approximately 1 +/- 0.005 g catalyst in alumina boat",
            catalyst_loading_mass_g="1 +/- 0.005",
            temperature_setpoint_C=str(item["temperature"]),
            temperature_program_summary=(
                f"heat under N2 to {item['temperature']} C, introduce hexane, "
                "then furnace-off cooling under N2"
            ),
            holding_time_min="30" if composition_series else "not_reported",
            heating_rate_C_min="not_reported",
            cooling_condition="furnace off; cool to room temperature under N2",
            pressure_original="atmospheric",
            pressure_kPa="101.325",
            carbon_source="n-hexane",
            carbon_source_flow_original=(
                "N2 carrier passed over liquid n-hexane; liquid amount and "
                "hexane vapor delivery rate not reported"
            ),
            reducing_gas="none",
            reducing_gas_flow_original="not_applicable",
            inert_gas="N2",
            inert_gas_flow_original="100 mL/min",
            cofeed_or_reactive_gas="none",
            cofeed_flow_original="not_applicable",
            total_flow_original="100 mL/min N2 before/around hexane saturation",
            gas_composition_summary="N2 carrier saturated by passage over n-hexane",
            process_note=(
                "Thirty minutes is explicitly reported for the 800 C "
                "composition series; duration is not restated for other temperatures."
            ),
        ),
    ]


def product(run_id: str, item: dict[str, Any]) -> dict[str, str]:
    summary = sample_summary(item)
    negative = item.get("negative", False)
    return yield_row(
        run_id,
        primary_yield_metric=(
            "negative_CNT_formation_control"
            if negative
            else "TGA_CNT_associated_weight_loss"
        ),
        yield_original=(
            "no XRD CNT peak below 700 C"
            if negative
            else f"{item['loss2']} wt% loss at {item['loss2_range']} C"
        ),
        yield_definition_original=(
            "Paper-assigned second TGA loss due to CNT oxidation; it is a "
            "composition indicator, not a synthesis mass yield."
            if not negative
            else summary
        ),
        yield_calculation_method="TGA from room temperature to 1000 C at 5 C/min",
        yield_value_standardized="" if negative else str(item["loss2"]),
        yield_unit_standardized="" if negative else "wt%",
        yield_standardization_note=(
            "Retained as CNT-associated fraction of the unpurified CQN; "
            "not converted to CNT yield per catalyst or carbon conversion."
        ),
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=summary,
        CNT_type_reported="CNT-quicklime nanocomposite"
        if not negative
        else "no CNT confirmed",
        CNT_type_confirmed=(
            "predominantly MWCNT with possible SWCNT co-presence"
            if not negative
            else "not confirmed at 600 C"
        ),
        product_mixture_summary=(
            "CNTs, carbon nanofibers, amorphous carbon, possible nanospheres/"
            "nanoonions, residual Ni catalyst and CaO support"
            if not negative
            else "600 C CVD product not further characterized"
        ),
        CNT_type_evidence=(
            "XRD; Raman; FESEM; TEM" if not negative else "absence of CNT XRD peak"
        ),
        SWCNT_or_few_wall_evidence_summary=(
            "Raman band near 200 cm^-1 was interpreted as MWCNT with possible SWCNT."
            if not negative
            else "not_applicable"
        ),
        RBM_peak_reported="possible low-wavenumber band"
        if not negative
        else "not_reported",
        outer_diameter_mean_nm="",
        outer_diameter_range_nm="not_quantified; visibly variable",
        inner_diameter_mean_nm="",
        wall_number_summary=(
            "multi-walled with possible single-walled co-presence"
            if not negative
            else "not_reported"
        ),
        length_summary="not_quantified",
        morphology=(
            "tubular CNTs and carbon nanofibers; some chain-like segments"
            if not negative
            else "not_reported"
        ),
        alignment_or_array="non-aligned powder nanocomposite",
        Raman_ratio_type="IG/ID",
        Raman_ratio_value="" if negative else str(item["raman"]),
        Raman_laser_wavelength_nm="532" if not negative else "not_reported",
        TGA_carbon_content_wt_percent="" if negative else str(item["loss2"]),
        purified_product_purity_wt_percent="",
        purity_basis="unpurified composite; TGA loss assignments by authors",
        residue_summary="substantial CaO support and residual/encapsulated Ni catalyst",
        amorphous_carbon_level=(
            "not_reported"
            if negative
            else f"{item['loss1']} wt% TGA loss at {item['loss1_range']} C"
        ),
        BET_surface_area_product_m2_g="" if negative else str(item["bet"]),
        characterization_methods="XRD; Raman; BET/BJH; FESEM; TEM; TGA; CV",
        post_treatment_or_purification="ground and stored; no purification",
        purification_condition="none",
        application_property_summary=(
            "not tested"
            if negative
            else (
                f"SPCE electroactive area {item['electro_area']} cm2; "
                f"roughness {item['roughness']}"
                if item["electro_area"]
                else "CV response reported qualitatively; no electroactive-area table value"
            )
            + (f"; k0 {item['k0']}" if item.get("k0") else "")
        ),
        notes=(
            "TGA fractions do not sum to total CNT yield because CaO/Ni residue "
            "and other carbon species remain in the nanocomposite."
        ),
    )


def scale_review(run_id: str, item: dict[str, Any]) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="laboratory powder batch",
        scale_level_claimed="potential economical natural-support route",
        scale_evidence_summary=(
            f"Approximately 1 +/- 0.005 g of {item['ni']} wt% Ni/CaO catalyst "
            "was processed in a 25/20/1000 mm quartz tube."
        ),
        reactor_capacity_or_throughput="approximately 1 g catalyst charge; product mass not reported",
        continuous_operation_time_h="not_reported",
        catalyst_lifetime_or_reuse="not_reported",
        catalyst_reuse_cycles="not_reported",
        batch_stability="not_reported",
        scale_up_issue=(
            "hexane vapor delivery is unquantified; natural stone composition, "
            "Ni dispersion, residual support and product heterogeneity require control"
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="Natural carbonate stone is described as economical, without cost data.",
        cost_driver_summary=(
            "1000 C/5 h support calcination, Ni nitrate, overnight drying, "
            "600-900 C CVD, N2 and unquantified n-hexane"
        ),
        safety_risk=(
            "flammable n-hexane vapor, nickel salts, high-temperature furnace "
            "and nanopowder exposure"
        ),
        emission_or_waste="unquantified hydrocarbon exhaust; Ni/CaO-containing solid residue",
        industrial_readiness_assessment=(
            "proof-of-concept batch composite; yield, purity and throughput are unreported"
        ),
        reproduction_value="medium-high",
        reproduction_priority="medium",
        recommended_next_action=(
            "report hexane delivery rate, run duration for every temperature, "
            "product mass, carbon conversion, Ni dispersion and purified CNT fraction"
        ),
        review_note="Economical-support claim is qualitative.",
    )


def add_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    suffix: str,
    table: str,
    record_id: str,
    span_id: str,
    page: int,
    text: str,
    summary: str,
    *,
    confidence: str = "high",
    status: str = "reported",
) -> None:
    item = evidence_row(
        store,
        SOURCE_ID,
        f"EVD_{run_id}_{suffix}",
        run_id,
        table,
        record_id,
        "record_level",
        span_id,
        summary,
        confidence=confidence,
        value_status=status,
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
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "Nine conditions: one 600 C negative control, five Ni/CaO "
                "10 wt% temperature-series products at 700-900 C, and three "
                "additional 5/15/20 wt% Ni composition conditions at 800 C."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_open_access_pdf"
    master["notes"] += (
        " The open-access publisher-formatted PDF was obtained through a "
        "public scholarly PDF mirror after direct MDPI CDN access was denied. "
        "Tables 1-3 and Figures 1-12 were visually checked."
    )

    run_ids: list[str] = []
    for item in SAMPLES:
        code = item["name"].replace("-", "_").upper()
        run_id = f"{SOURCE_ID}_{code}"
        run_ids.append(run_id)
        summary = sample_summary(item)
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                code,
                item["name"],
                summary,
                "high" if not item.get("negative") else "medium",
            )
        )
        tables["catalyst_system"].append(catalyst(run_id, item["ni"]))
        run_stages = stages(run_id, item)
        tables["reactor_process_gas"].extend(run_stages)
        tables["yield_quality"].append(product(run_id, item))
        tables["cost_scale_review"].append(scale_review(run_id, item))

        add_evidence(
            tables,
            store,
            run_id,
            "RUN",
            "source_run",
            run_id,
            XRD_SPAN,
            5,
            summary,
            "Sample identity, temperature/composition condition and outcome.",
            confidence="medium" if item.get("negative") else "high",
            status="reported_or_negative_control",
        )
        add_evidence(
            tables,
            store,
            run_id,
            "CATALYST",
            "catalyst_system",
            f"{run_id}_CAT",
            CATALYST_SPAN,
            3,
            (
                f"{item['name']}: nominal Ni loading {item['ni']} wt%. "
                "Carbonate stone was calcined at 1000 C for 5 h and sieved "
                "to 90 um. Ni nitrate was dissolved in 40 mL water, stirred "
                "at 70 +/- 10 C, dried at 70 +/- 10 C overnight and re-sieved "
                "to 90 um. Catalyst particle size was not quantified."
            ),
            "Ni/CaO catalyst identity and preparation.",
        )
        for stage in run_stages:
            add_evidence(
                tables,
                store,
                run_id,
                f"PROCESS_{stage['stage_order']}",
                "reactor_process_gas",
                stage["process_stage_id"],
                CATALYST_SPAN if stage["stage_order"] < "3" else PROCESS_SPAN,
                3,
                (
                    f"Stage {stage['stage_order']} {stage['stage_type']}: "
                    f"temperature {stage['temperature_setpoint_C']} C; "
                    f"duration {stage['holding_time_min']} min; pressure "
                    f"{stage['pressure_original']}; catalyst charge "
                    f"{stage['catalyst_loading_mass_g']} g; reactor "
                    f"{stage['reactor_size_summary']}; carbon source "
                    f"{stage['carbon_source']} at {stage['carbon_source_flow_original']}; "
                    f"N2/inert flow {stage['inert_gas_flow_original']}; "
                    f"cofeed {stage['cofeed_flow_original']}; "
                    f"total flow {stage['total_flow_original']}; cooling "
                    f"{stage['cooling_condition']}."
                ),
                f"Process stage {stage['stage_order']} support.",
            )

        if item.get("negative"):
            result_text = summary
            result_span = XRD_SPAN
            result_page = 5
        else:
            result_text = (
                summary
                + " TEM showed tubular CNTs, residual spherical catalyst/support "
                "particles at tube exteriors and tips, and sometimes filled tubes. "
                "FESEM also showed carbon nanofibers and possible nanospheres/"
                "nanoonions. Raman used 532 nm excitation."
            )
            result_span = TGA_SPAN
            result_page = 11
        add_evidence(
            tables,
            store,
            run_id,
            "PRODUCT",
            "yield_quality",
            f"{run_id}_PROD",
            result_span,
            result_page,
            result_text,
            "TGA composition, Raman, porosity, morphology and application outcome.",
            confidence="medium" if item.get("negative") else "high",
            status="reported_composite_property_not_mass_yield",
        )
        if not item.get("negative"):
            add_evidence(
                tables,
                store,
                run_id,
                "PRODUCT_RAMAN",
                "yield_quality",
                f"{run_id}_PROD",
                RAMAN_SPAN,
                6,
                (
                    f"{item['name']} Raman IG/ID {item['raman']} from Figure 3; "
                    "laser wavelength 532 nm."
                ),
                "Raman graphitization ratio visually transcribed from labeled bars.",
                status="pdf_labeled_figure_value",
            )
            add_evidence(
                tables,
                store,
                run_id,
                "PRODUCT_BET",
                "yield_quality",
                f"{run_id}_PROD",
                BET_SPAN,
                7,
                (
                    f"{item['name']}: BET {item['bet']} m2/g, pore volume "
                    f"{item['pore_volume']} cm3/g, BJH average pore diameter "
                    f"{item['pore_diameter']} A."
                ),
                "BET and BJH table values.",
            )
            if item["electro_area"]:
                add_evidence(
                    tables,
                    store,
                    run_id,
                    "PRODUCT_ELECTRO",
                    "yield_quality",
                    f"{run_id}_PROD",
                    ELECTRO_SPAN,
                    13,
                    (
                        f"{item['name']}: SPCE geometrical area 0.0707 cm2, "
                        f"electroactive area {item['electro_area']} cm2, "
                        f"roughness factor {item['roughness']}."
                        + (
                            f" Heterogeneous electron-transfer k0 {item['k0']}."
                            if item.get("k0")
                            else ""
                        )
                    ),
                    "SPCE electroactive-area and kinetic performance.",
                    status="reported_application_property",
                )
        add_evidence(
            tables,
            store,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            PROCESS_SPAN,
            3,
            (
                f"{summary} Approximately 1 +/- 0.005 g catalyst was charged "
                "to a 25/20/1000 mm quartz tube. No product mass, energy, "
                "throughput-normalized cost or catalyst reuse was reported."
            ),
            "Scale evidence and industrial data gaps.",
            status="review_assessment",
        )

    ref = f"{SOURCE_ID}_HNI10_800"
    negative = f"{SOURCE_ID}_HNI10_600"
    composition_ref = f"{SOURCE_ID}_HNI5_800"
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_DEFINITION_001",
                SOURCE_ID,
                ref,
                "yield_definition",
                "yield_quality",
                f"{ref}_PROD",
                "primary_yield_metric",
                (
                    "The second TGA loss is assigned to CNT oxidation and is "
                    "retained as a product-composition indicator, not as synthesis "
                    "yield, catalyst productivity or carbon conversion."
                ),
                f"EVD_{ref}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_600_CONTROL_001",
                SOURCE_ID,
                negative,
                "negative_control_data_gap",
                "yield_quality",
                f"{negative}_PROD",
                "secondary_result_summary",
                (
                    "The study states that the screen covered 600-900 C and "
                    "that at least 700 C was needed for a CNT XRD peak, but "
                    "does not present a separate 600 C spectrum or table row."
                ),
                f"EVD_{negative}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_DURATION_001",
                SOURCE_ID,
                negative,
                "critical_data_gap",
                "reactor_process_gas",
                f"{negative}_S03",
                "holding_time_min",
                (
                    "A 30 min holding time is explicit for the 800 C catalyst-"
                    "composition series, but the duration is not restated for "
                    "the 600-900 C temperature series."
                ),
                f"EVD_{negative}_PROCESS_3;EVD_{composition_ref}_PROCESS_3",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_HEXANE_FLOW_001",
                SOURCE_ID,
                ref,
                "critical_data_gap",
                "reactor_process_gas",
                f"{ref}_S03",
                "carbon_source_flow_original",
                (
                    "N2 was passed over liquid n-hexane, but hexane amount, "
                    "bubbler temperature, vapor concentration and carbon feed "
                    "rate were not reported."
                ),
                f"EVD_{ref}_PROCESS_3",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PRODUCT_MIXTURE_001",
                SOURCE_ID,
                ref,
                "product_mixture",
                "yield_quality",
                f"{ref}_PROD",
                "product_mixture_summary",
                (
                    "The unpurified CQN contains CNTs, carbon nanofibers, "
                    "amorphous/other carbon, CaO and residual or encapsulated "
                    "Ni; CNT-only purity and diameter distributions were not quantified."
                ),
                f"EVD_{ref}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_RAMAN_LABEL_001",
                SOURCE_ID,
                ref,
                "figure_transcription",
                "yield_quality",
                f"{ref}_PROD",
                "Raman_ratio_value",
                (
                    "IG/ID values were transcribed from numeric labels above "
                    "Figure 3 bars; plotted error-bar magnitudes were not digitized."
                ),
                f"EVD_{ref}_PRODUCT_RAMAN",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_ELECTRO_SCOPE_001",
                SOURCE_ID,
                ref,
                "application_scope",
                "yield_quality",
                f"{ref}_PROD",
                "application_property_summary",
                (
                    "Exact electroactive areas were tabulated only for the "
                    "HNi10 temperature series. Composition-series CV outcomes "
                    "remain qualitative except HNi10-800 kinetic data."
                ),
                f"EVD_{ref}_PRODUCT_ELECTRO",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_TGA_ASSIGNMENT_001",
                SOURCE_ID,
                ref,
                "measurement_interpretation",
                "yield_quality",
                f"{ref}_PROD",
                "TGA_carbon_content_wt_percent",
                (
                    "TGA loss 1 and loss 2 are assigned by the authors to "
                    "amorphous carbon and CNT oxidation, respectively; overlapping "
                    "carbon species and incomplete oxidation separation may remain."
                ),
                f"EVD_{ref}_PRODUCT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_COST_001",
                SOURCE_ID,
                ref,
                "critical_data_gap",
                "cost_scale_review",
                ref,
                "quantitative_cost_summary",
                (
                    "The carbonate-stone support is described as natural, "
                    "available and economical, but no cost, energy, product "
                    "mass, throughput or reuse data are reported."
                ),
                f"EVD_{ref}_COST",
                "high",
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
    output = REPORT_ROOT / f"batch_{BATCH_NUMBER:03d}_metrics.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
