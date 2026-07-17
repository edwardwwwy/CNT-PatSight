#!/usr/bin/env python3
"""Build the twenty-fourth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 24
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_6731BD3F12EC3922"
PDF_REF = "data/raw/fulltext/pdf/LIT_6731BD3F12EC3922_c5205b472274.pdf"

COMMON_RECIPE = (
    "Aerosol-assisted one-step CCVD at atmospheric pressure and 615 C. "
    "Ferrocene, at a reported selectable concentration of 0.25-2.5 wt.% "
    "in toluene, was injected through an engine injection system. Ar/H2 "
    "carrier contained 10 vol.% H2; C2H2 and optional CO2 contents were "
    "varied while Ar was reduced to keep total flow constant. The aerosol "
    "passed through a 250 C evaporator before a horizontal quartz reactor. "
    "Ten 10 mm Al discs on a quartz holder were used in every synthesis, "
    "then cooled to room temperature under Ar/H2."
)

SUBSTRATES = {
    "LG": {
        "label": "low-grade Al foil",
        "purity": "99.99%",
        "thickness": "95 um",
        "roughness": "400 +/- 100 nm",
    },
    "HG": {
        "label": "high-grade polished/smoother Al foil",
        "purity": "99.99%",
        "thickness": "130 um",
        "roughness": "50 +/- 10 nm",
    },
}


def key(substrate: str, c2h2: float, co2: float, duration: int) -> tuple:
    return substrate, float(c2h2), float(co2), duration


CONDITIONS: dict[tuple, dict[str, Any]] = {}


def add_condition(
    substrate: str,
    c2h2: float,
    co2: float,
    duration: int,
    height: float,
    figure: int,
    page: int,
    span: str,
    *,
    height_note: str = "",
) -> None:
    item_key = key(substrate, c2h2, co2, duration)
    if item_key in CONDITIONS:
        previous = CONDITIONS[item_key]
        if abs(float(previous["height"]) - height) >= 10:
            previous["height_note"] = (
                f"{previous.get('height_note', '')} Figure {previous['figure']} "
                f"reads approximately {previous['height']} um and Figure "
                f"{figure} approximately {height} um for the same nominal "
                "condition."
            ).strip()
            previous["height"] = round((float(previous["height"]) + height) / 2)
            previous["height_original"] = (
                f"approximately {min(float(previous['height_values'][0]), height):g}-"
                f"{max(float(previous['height_values'][0]), height):g} um across figures"
            )
            previous["height_values"].append(height)
        return
    CONDITIONS[item_key] = {
        "substrate": substrate,
        "c2h2": float(c2h2),
        "co2": float(co2),
        "duration": duration,
        "height": height,
        "height_original": f"approximately {height:g} um",
        "height_values": [height],
        "height_note": height_note,
        "figure": figure,
        "page": page,
        "span": span,
    }


# Figure 1: long syntheses without CO2, visually digitized.
FIG1 = {
    (1.5, "LG"): [110, 145, 260, 430, 520, 500, 390],
    (1.5, "HG"): [100, 185, 355, 475, 660, 665, 620],
    (5.0, "LG"): [80, 150, 255, 390, 430, 390, 310],
    (5.0, "HG"): [85, 170, 320, 350, 520, 490, 420],
}
for (acetylene, substrate), heights in FIG1.items():
    for duration, height in zip([20, 40, 80, 120, 160, 200, 240], heights, strict=True):
        add_condition(
            substrate,
            acetylene,
            0,
            duration,
            height,
            1,
            4,
            "SPAN_7F74EC5EB463F5336554",
        )

# Figure 3: 80 min CO2-content screen, visually digitized.
FIG3_15 = {
    "LG": {0: 150, 1.5: 160, 15: 140, 75: 120},
    "HG": {0: 160, 1.5: 150, 15: 125, 75: 150},
}
for substrate, points in FIG3_15.items():
    for co2, height in points.items():
        add_condition(
            substrate,
            15,
            co2,
            80,
            height,
            3,
            6,
            "SPAN_34DCC40D178AF1856737",
        )

FIG3_1P5 = {
    "LG": {0: 260, 1.5: 360, 4.5: 240, 7.5: 195, 15: 235, 45: 70},
    "HG": {0: 340, 1.5: 450, 4.5: 275, 7.5: 180, 15: 295, 45: 150},
}
for substrate, points in FIG3_1P5.items():
    for co2, height in points.items():
        add_condition(
            substrate,
            1.5,
            co2,
            80,
            height,
            3,
            6,
            "SPAN_2C5DE6CAADF2E35F4783",
        )

# Figure 4: long equimolar C2H2/CO2 syntheses, visually digitized.
FIG4 = {
    "LG": {40: 110, 80: 320, 160: 440, 240: 585, 320: 655},
    "HG": {40: 110, 80: 390, 160: 525, 240: 765, 320: 800},
}
for substrate, points in FIG4.items():
    for duration, height in points.items():
        add_condition(
            substrate,
            1.5,
            1.5,
            duration,
            height,
            4,
            7,
            "SPAN_3D3D4E0A0328942379D2",
        )

# Figure 7: areal mass loading and carpet bulk mass density, visually digitized.
DENSITY = {
    key("LG", 1.5, 0, 20): (0.5, 45),
    key("LG", 1.5, 0, 40): (0.8, 55),
    key("LG", 1.5, 0, 80): (1.4, 60),
    key("LG", 1.5, 0, 120): (2.4, 55),
    key("LG", 1.5, 0, 160): (3.6, 75),
    key("LG", 1.5, 0, 200): (3.5, 70),
    key("LG", 1.5, 0, 240): (4.0, 110),
    key("LG", 1.5, 1.5, 40): (0.2, 20),
    key("LG", 1.5, 1.5, 80): (2.2, 65),
    key("LG", 1.5, 1.5, 160): (3.7, 85),
    key("LG", 1.5, 1.5, 240): (9.0, 150),
    key("LG", 1.5, 1.5, 320): (13.5, 208),
    key("HG", 1.5, 0, 20): (0.4, 48),
    key("HG", 1.5, 0, 40): (1.4, 72),
    key("HG", 1.5, 0, 80): (2.2, 66),
    key("HG", 1.5, 0, 160): (5.9, 80),
    key("HG", 1.5, 0, 240): (4.9, 85),
    key("HG", 1.5, 1.5, 40): (0.3, 35),
    key("HG", 1.5, 1.5, 80): (1.7, 50),
    key("HG", 1.5, 1.5, 160): (3.8, 72),
    key("HG", 1.5, 1.5, 240): (8.1, 112),
    key("HG", 1.5, 1.5, 320): (9.7, 120),
}

# Figure 5: mean external/internal CNT diameters, visually digitized.
DIAMETER = {
    key("LG", 1.5, 0, 20): (6.3, 3.8),
    key("LG", 1.5, 0, 80): (7.6, 4.5),
    key("LG", 1.5, 0, 160): (6.6, 4.3),
    key("LG", 1.5, 0, 240): (7.4, 4.8),
    key("HG", 1.5, 0, 80): (7.3, 4.0),
    key("HG", 1.5, 0, 160): (7.7, 4.7),
    key("HG", 1.5, 1.5, 40): (8.6, 5.5),
    key("HG", 1.5, 1.5, 80): (8.3, 5.3),
    key("HG", 1.5, 1.5, 160): (9.8, 5.1),
    key("HG", 1.5, 1.5, 240): (9.4, 5.3),
    key("HG", 1.5, 1.5, 320): (10.5, 6.5),
}

# Figure 6b: Raman D-band FWHM on top and at the carpet center.
RAMAN_FWHM = {
    key("HG", 1.5, 0, 40): (111, 91),
    key("HG", 1.5, 0, 80): (109, 88),
    key("HG", 1.5, 0, 160): (106, 101),
    key("HG", 1.5, 0, 240): (95, 70),
    key("HG", 1.5, 1.5, 40): (108, 88),
    key("HG", 1.5, 1.5, 80): (106, 98),
    key("HG", 1.5, 1.5, 160): (107, 74),
    key("HG", 1.5, 1.5, 240): (108, 81),
    key("HG", 1.5, 1.5, 320): (102, 64),
}

GROWTH_MODEL = {
    "LG": {
        "maximum_height_um": 870,
        "time_constant_min": 227,
        "initial_rate_um_min": 3.8,
        "r_squared": 0.974,
    },
    "HG": {
        "maximum_height_um": 896,
        "time_constant_min": 141,
        "initial_rate_um_min": 6.2,
        "r_squared": 0.972,
    },
}


def fmt(value: float) -> str:
    return f"{value:g}"


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
    value_status: str = "reported",
    confidence: str = "high",
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


def catalyst(run_id: str, substrate: str) -> dict[str, str]:
    sub = SUBSTRATES[substrate]
    return catalyst_row(
        run_id,
        catalyst_label=(f"in-situ Fe aerosol catalyst deposited on {sub['label']}"),
        active_metals="Fe",
        support_material="native alumina-covered Al foil growth substrate",
        promoter="CO2 when present is a gas-phase growth promoter/oxidant",
        metal_ratio_original="not_reported",
        metal_ratio_standardized="not_reported",
        precursor_summary="ferrocene dissolved in toluene",
        preparation_method="continuous_in_situ_ferrocene_aerosol_decomposition",
        preparation_modifier=(
            f"{sub['label']}; {sub['purity']} Al; {sub['thickness']}; "
            f"surface roughness {sub['roughness']}"
        ),
        preparation_detail=(
            "Ferrocene/toluene aerosol evaporated at 250 C, decomposed at "
            "615 C, and continuously renewed Fe nanoparticles migrated to "
            "the Al substrate. Substrates were cleaned with acetone and ethanol."
        ),
        drying_condition="not_applicable",
        calcination_condition="not_applicable",
        reduction_condition="10 vol.% H2 carrier during growth",
        activation_condition="in-situ ferrocene decomposition at 615 C",
        post_preparation_condition="continuously refreshed during one-step CCVD",
        catalyst_particle_size_mean_nm="",
        catalyst_particle_size_range_nm="not_reported",
        catalyst_particle_size_qualifier=(
            "No obvious particle-size increase at the CNT/Al interface with CO2."
        ),
        phase_or_state_summary=(
            "Fe nanoparticles form in the gas phase and on the native alumina "
            "surface; no iron diffusion through native alumina was observed."
        ),
        dispersion_summary="continuous aerosol nucleation and migration to substrate",
        deactivation_summary=(
            "growth degradation after about 160 min without CO2; CO2 postpones termination"
        ),
    )


def growth_process(run_id: str, item: dict[str, Any]) -> list[dict[str, str]]:
    c2h2 = fmt(item["c2h2"])
    co2 = fmt(item["co2"])
    duration = str(item["duration"])
    gas = (
        f"C2H2 {c2h2} vol.%; CO2 {co2} vol.%; H2 10 vol.%; "
        "balance Ar; absolute total flow not reported"
    )
    return [
        process_row(
            run_id,
            1,
            "aerosol_evaporation_and_feed",
            reactor_type="aerosol-assisted one-step CCVD feed system",
            scale_level="lab_multi_substrate_batch",
            reactor_material="heated evaporator upstream of quartz reactor",
            reactor_size_summary="not_reported",
            reactor_setup_summary=COMMON_RECIPE,
            catalyst_loading_mass_g="not_reported_continuous_ferrocene_feed",
            temperature_setpoint_C="250",
            temperature_program_summary="ferrocene/toluene aerosol evaporated at 250 C",
            holding_time_min=duration,
            heating_rate_C_min="not_reported",
            cooling_condition="not_applicable_feed_stage",
            pressure_original="atmospheric",
            pressure_kPa="101.325",
            carbon_source="toluene carrier solvent; C2H2 supplied separately",
            carbon_source_flow_original=(
                "ferrocene concentration 0.25-2.5 wt.% in toluene; "
                "exact run concentration and liquid flow not reported"
            ),
            reducing_gas="H2",
            reducing_gas_flow_original="10 vol.% of gas mixture",
            inert_gas="Ar",
            inert_gas_flow_original="balance adjusted when CO2 was added",
            cofeed_or_reactive_gas="ferrocene/toluene aerosol",
            cofeed_flow_original="not_reported",
            total_flow_original="constant across CO2 substitutions; absolute value not reported",
            gas_composition_summary=gas,
            process_note=(f"Aerosol feed continued for the {duration} min synthesis."),
        ),
        process_row(
            run_id,
            2,
            "vacnt_growth",
            reactor_type="horizontal quartz aerosol-assisted CCVD reactor",
            scale_level="lab_multi_substrate_batch",
            reactor_material="quartz",
            reactor_size_summary="not_reported",
            reactor_setup_summary=(
                "Ten 10 mm Al discs P1-P10 on a quartz holder in the "
                "isothermal zone of a Carbolite TZF 12/38/400 furnace."
            ),
            catalyst_loading_mass_g="not_reported_continuous_ferrocene_feed",
            temperature_setpoint_C="615",
            temperature_program_summary="isothermal growth at 615 C",
            holding_time_min=duration,
            heating_rate_C_min="not_reported",
            cooling_condition="subsequently cooled to room temperature under Ar/H2",
            pressure_original="atmospheric",
            pressure_kPa="101.325",
            carbon_source="C2H2",
            carbon_source_flow_original=f"{c2h2} vol.%",
            reducing_gas="H2",
            reducing_gas_flow_original="10 vol.%",
            inert_gas="Ar",
            inert_gas_flow_original="balance gas",
            cofeed_or_reactive_gas="CO2" if item["co2"] else "none",
            cofeed_flow_original=f"{co2} vol.%",
            total_flow_original="constant but absolute flow not reported",
            gas_composition_summary=gas,
            process_note=(
                f"{SUBSTRATES[item['substrate']]['label']}; synthesis "
                f"duration {duration} min."
            ),
        ),
        process_row(
            run_id,
            3,
            "reactor_cooling",
            reactor_type="horizontal quartz CCVD reactor",
            scale_level="lab_multi_substrate_batch",
            reactor_material="quartz",
            reactor_size_summary="not_reported",
            reactor_setup_summary=COMMON_RECIPE,
            temperature_setpoint_C="room_temperature",
            temperature_program_summary="cool from 615 C to room temperature",
            holding_time_min="not_reported",
            heating_rate_C_min="not_applicable",
            cooling_condition="under Ar and H2 flow",
            pressure_original="atmospheric",
            pressure_kPa="101.325",
            carbon_source="none",
            reducing_gas="H2",
            reducing_gas_flow_original="part of Ar/H2 cooling flow; absolute value not reported",
            inert_gas="Ar",
            inert_gas_flow_original="part of Ar/H2 cooling flow; absolute value not reported",
            cofeed_or_reactive_gas="none",
            total_flow_original="not_reported",
            gas_composition_summary="Ar/H2",
            process_note="Samples collected only after cooling to room temperature.",
        ),
    ]


def product(run_id: str, item: dict[str, Any]) -> dict[str, str]:
    item_key = key(item["substrate"], item["c2h2"], item["co2"], item["duration"])
    secondary = [
        (
            f"VACNT carpet thickness {item['height_original']}; visual "
            f"digitization from Figure {item['figure']}."
        )
    ]
    if item.get("height_note"):
        secondary.append(item["height_note"])

    areal = ""
    bulk = ""
    if item_key in DENSITY:
        areal_value, bulk_value = DENSITY[item_key]
        areal = fmt(areal_value)
        bulk = fmt(bulk_value)
        secondary.append(
            f"Figure 7 areal loading approximately {areal} mg/cm2 and "
            f"carpet mass density approximately {bulk} mg/cm3."
        )

    outer = ""
    inner = ""
    if item_key in DIAMETER:
        outer_value, inner_value = DIAMETER[item_key]
        outer = fmt(outer_value)
        inner = fmt(inner_value)
        secondary.append(
            f"Figure 5 mean outer/inner diameters approximately {outer}/{inner} nm."
        )

    if item_key in RAMAN_FWHM:
        top, lateral = RAMAN_FWHM[item_key]
        secondary.append(
            f"Figure 6 D-band FWHM approximately {top} cm-1 at the top "
            f"and {lateral} cm-1 in lateral center view."
        )

    substrate = item["substrate"]
    co2 = item["co2"]
    duration = item["duration"]
    if item["c2h2"] == 1.5 and co2 == 1.5:
        model = GROWTH_MODEL[substrate]
        secondary.append(
            "Table 1 exponential-growth fit for this substrate/condition "
            f"series: maximum height {model['maximum_height_um']} um, "
            f"time constant {model['time_constant_min']} min, initial rate "
            f"{model['initial_rate_um_min']} um/min and R2 "
            f"{model['r_squared']}."
        )
    morphology = "vertically aligned CNT carpet"
    amorphous = "few disorganized carbon nanostructures reported"
    if duration > 160 and not co2:
        morphology += (
            "; thickness saturation/degradation, brittle bundles and fluffy top"
        )
        if substrate == "LG":
            morphology += "; disordered carbon at the CNT/substrate interface"
            amorphous = "heavy disordered-carbon morphology at the interface"
    elif substrate == "HG":
        morphology += "; comparatively clean and well organized"

    wall_summary = (
        "approximately 6-8 walls with CO2"
        if co2 and item["c2h2"] == 1.5
        else "approximately 4-6 walls without CO2 for characterized 1.5 vol.% C2H2 samples"
    )
    return yield_row(
        run_id,
        primary_yield_metric="VACNT_carpet_thickness",
        yield_original=item["height_original"],
        yield_definition_original=(
            "mean cross-sectional carpet thickness from five SEM locations"
        ),
        yield_calculation_method="SEM cross-section; graph value visually digitized",
        yield_value_standardized=fmt(item["height"]),
        yield_unit_standardized="um",
        yield_standardization_note=(
            "Thickness retained as the paper's production metric; no mass-yield conversion."
        ),
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=" ".join(secondary),
        CNT_type_reported="VACNT carpet",
        CNT_type_confirmed="few-wall/multiwall vertically aligned CNT carpet",
        product_mixture_summary=(
            "VACNT carpet; degradation can add disordered carbon at long "
            "duration, especially on rough LG Al without CO2"
        ),
        CNT_type_evidence="SEM cross-section; TEM; Raman",
        SWCNT_or_few_wall_evidence_summary=wall_summary,
        RBM_peak_reported="not_reported",
        outer_diameter_mean_nm=outer,
        outer_diameter_range_nm="not_reported",
        inner_diameter_mean_nm=inner,
        wall_number_summary=wall_summary,
        length_summary=f"carpet thickness {item['height_original']}",
        morphology=morphology,
        alignment_or_array="vertically aligned carpet",
        Raman_ratio_type="ID/I2D",
        Raman_ratio_value="",
        Raman_laser_wavelength_nm="532",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis=(
            "prior TGA cited iron content below 2 wt.%; current TEM found "
            "no visible Fe nanoparticles inside or outside CNTs"
        ),
        residue_summary="iron contribution to weighed mass treated as negligible",
        amorphous_carbon_level=amorphous,
        BET_surface_area_product_m2_g="",
        characterization_methods="SEM; TEM; STEM-EDX; Raman; gravimetry",
        post_treatment_or_purification="none",
        purification_condition="not_applicable_as-grown_carpet",
        application_property_summary=(
            f"Figure 7 areal loading {areal} mg/cm2; bulk carpet density {bulk} mg/cm3"
            if areal
            else ""
        ),
        notes=(
            "Graph-derived values are approximate; plotted uncertainty bars "
            "are not converted into exact numeric standard deviations."
        ),
    )


def cost(run_id: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="lab_multi_substrate_batch",
        scale_level_claimed="large_scale_compatible_one_step_process",
        scale_evidence_summary=(
            "Atmospheric one-step aerosol CCVD processed ten 10 mm Al discs "
            "simultaneously and continuously renewed catalyst precursor."
        ),
        reactor_capacity_or_throughput="ten 10 mm Al discs per synthesis",
        continuous_operation_time_h="up to 5.33 h",
        catalyst_lifetime_or_reuse=(
            "continuous ferrocene supply renews catalyst; no discrete reuse cycle"
        ),
        catalyst_reuse_cycles="not_applicable_continuous_precursor",
        batch_stability=(
            "ten discs weighed per synthesis; thickness measured at five locations; "
            "plotted error bars reported but exact values unavailable"
        ),
        scale_up_issue=(
            "Control long-duration aerosol delivery, CO2/C2H2 composition, "
            "substrate roughness, catalyst renewal and exhaust oxidation chemistry."
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary=(
            "Moderate 615 C temperature and atmospheric operation are scale "
            "advantages; no monetary or energy-per-mass analysis."
        ),
        cost_driver_summary=(
            "615 C furnace for up to 320 min, ferrocene/toluene aerosol, "
            "C2H2, H2, Ar, CO2 and high-grade Al foil"
        ),
        safety_risk=(
            "flammable C2H2/H2/toluene; ferrocene aerosol; CO formation from "
            "oxidative dehydrogenation; hot quartz furnace"
        ),
        emission_or_waste=(
            "unquantified hydrocarbon/CO exhaust; no wet purification waste"
        ),
        industrial_readiness_assessment=(
            "promising laboratory multi-substrate process, but absolute flow, "
            "mass productivity and long-run reproducibility are missing"
        ),
        reproduction_value="high for composition/time/temperature matrix",
        reproduction_priority="high",
        recommended_next_action=(
            "Report absolute gas and aerosol flow, exact ferrocene concentration, "
            "collected CNT mass rate, energy use and replicate raw data."
        ),
        review_note="Scale assessment remains provisional without throughput normalization.",
    )


CONTROL_RUNS = [
    {
        "code": "CONTROL_COLD_160_C2H2_ANNEAL_80",
        "label": "cold 160 min LG-Al carpet, 80 min C2H2 anneal",
        "summary": (
            "LG-Al VACNT carpet grown 160 min without CO2, cooled, then "
            "annealed at 615 C for 80 min in Ar/H2 with 1.5 vol.% C2H2; "
            "no further degradation or mass change."
        ),
        "span": "SPAN_A850C43C24B9FF6EE13A",
        "page": 10,
    },
    {
        "code": "CONTROL_COLD_240_ARH2_ANNEAL",
        "label": "cold degraded 240 min carpet, Ar/H2 anneal",
        "summary": (
            "Previously degraded 240 min carpet was cooled and reintroduced "
            "for 40-160 min annealing at 615 C in Ar/H2; no additional "
            "degradation or mass change."
        ),
        "span": "SPAN_4E424416C44D6ADF4989",
        "page": 8,
    },
    {
        "code": "CONTROL_COLD_DEGRADED_FE_REEXPOSURE",
        "label": "cold degraded carpet re-exposed with ferrocene",
        "summary": (
            "A cooled degraded carpet was re-exposed to standard growth gas "
            "with ferrocene; a new carpet grew underneath while the old carpet "
            "did not degrade further, supporting base growth."
        ),
        "span": "SPAN_B737B74775A9DE5FD15A",
        "page": 9,
    },
    {
        "code": "CONTROL_HOT_240_STOP_FE_160",
        "label": "240 min hot growth, ferrocene stopped after 160 min",
        "summary": (
            "During a 240 min synthesis, ferrocene injection was stopped at "
            "160 min; final thickness matched a standard degraded 240 min "
            "carpet, so continued ferrocene did not control degradation onset."
        ),
        "span": "SPAN_6C89AC2B3BB8BC635D9A",
        "page": 9,
    },
]


def build(
    metadata: dict[str, Any],
    store: EvidenceStore,
) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "54 unique VACNT growth conditions across substrate grade, "
                "C2H2, CO2 and duration; four degradation-control branches; "
                "thickness, density, diameter, wall-number and Raman results."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_fulltext_pdf"
    master["notes"] += (
        " Supplementary Tables S1-S4 are cited but were not included in the "
        "open HAL PDF; the publisher states data are available on request."
    )

    run_ids: list[str] = []
    for item_key in sorted(
        CONDITIONS,
        key=lambda x: (x[0], x[1], x[2], x[3]),
    ):
        item = CONDITIONS[item_key]
        substrate = item["substrate"]
        c2h2 = fmt(item["c2h2"])
        co2 = fmt(item["co2"])
        duration = item["duration"]
        code = (
            f"{substrate}_C2H2_{c2h2.replace('.', 'P')}_"
            f"CO2_{co2.replace('.', 'P')}_{duration:03d}MIN"
        )
        run_id = f"{SOURCE_ID}_{code}"
        run_ids.append(run_id)
        summary = (
            f"{SUBSTRATES[substrate]['label']}, C2H2 {c2h2} vol.%, "
            f"CO2 {co2} vol.%, 615 C for {duration} min: VACNT carpet "
            f"{item['height_original']}."
        )
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                code,
                (f"{substrate} Al, C2H2/CO2 {c2h2}/{co2} vol.%, {duration} min"),
                summary,
                "medium",
            )
        )
        tables["catalyst_system"].append(catalyst(run_id, substrate))
        tables["reactor_process_gas"].extend(growth_process(run_id, item))
        tables["yield_quality"].append(product(run_id, item))
        tables["cost_scale_review"].append(cost(run_id))

        condition_text = (
            f"{COMMON_RECIPE} This record used {SUBSTRATES[substrate]['label']} "
            f"with surface roughness {SUBSTRATES[substrate]['roughness']}, "
            f"C2H2 {c2h2} vol.%, CO2 {co2} vol.%, 10 vol.% H2, "
            f"615 C, atmospheric pressure, and duration {duration} min."
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "RUN",
            "source_run",
            run_id,
            "record_level",
            item["span"],
            item["page"],
            condition_text + f" VACNT thickness {item['height_original']}.",
            "Growth-condition identity and carpet thickness.",
            value_status="mixed_reported_and_visually_digitized",
            confidence="medium",
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "CATALYST",
            "catalyst_system",
            f"{run_id}_CAT",
            "record_level",
            "SPAN_7B91A7A600809079D3CA",
            3,
            condition_text
            + " Ferrocene concentration was selectable from 0.25 to 2.5 wt.%.",
            "Continuous ferrocene-derived Fe catalyst and substrate condition.",
        )
        process_texts = [
            (
                1,
                "SPAN_C4BB3586851EE13C51E5",
                3,
                (
                    f"Ferrocene/toluene aerosol was evaporated at 250 C for "
                    f"the {duration} min synthesis; pressure 101.325 kPa "
                    "(atmospheric). " + condition_text
                ),
            ),
            (
                2,
                "SPAN_39E038FA07016861366E",
                3,
                condition_text,
            ),
            (
                3,
                "SPAN_CB3C7C29F24D75544497",
                3,
                (
                    "After growth at 615 C, the reactor was cooled from "
                    "615 C to room temperature under Ar/H2 at atmospheric "
                    "pressure, 101.325 kPa; cooling duration was not reported."
                ),
            ),
        ]
        for stage, span, page, text in process_texts:
            add_pdf_evidence(
                tables,
                store,
                run_id,
                f"PROCESS_{stage}",
                "reactor_process_gas",
                f"{run_id}_S{stage:02d}",
                "record_level",
                span,
                page,
                text,
                f"Process stage {stage} support.",
            )

        product_text = (
            f"Figure {item['figure']}: {SUBSTRATES[substrate]['label']}, "
            f"C2H2 {c2h2} vol.%, CO2 {co2} vol.%, duration {duration} min, "
            f"VACNT thickness {item['height_original']}; standardized "
            f"thickness {fmt(item['height'])} um. Raman wavelength 532 nm."
        )
        if item_key in DENSITY:
            areal, bulk = DENSITY[item_key]
            product_text += (
                f" Figure 7 areal loading {fmt(areal)} mg/cm2 and mass "
                f"density {fmt(bulk)} mg/cm3."
            )
        if item_key in DIAMETER:
            outer, inner = DIAMETER[item_key]
            product_text += (
                f" Figure 5 mean outer diameter {fmt(outer)} nm and mean "
                f"inner diameter {fmt(inner)} nm."
            )
        if item_key in RAMAN_FWHM:
            top, lateral = RAMAN_FWHM[item_key]
            product_text += (
                f" Figure 6 D-band FWHM {top} cm-1 at the top and "
                f"{lateral} cm-1 at the lateral center."
            )
        if item["c2h2"] == 1.5 and item["co2"] == 1.5:
            model = GROWTH_MODEL[substrate]
            product_text += (
                " Table 1 exponential-growth fit for this condition series: "
                f"maximum height {model['maximum_height_um']} um, time "
                f"constant {model['time_constant_min']} min, initial rate "
                f"{model['initial_rate_um_min']} um/min and R2 "
                f"{model['r_squared']}."
            )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "PRODUCT",
            "yield_quality",
            f"{run_id}_PROD",
            "record_level",
            item["span"],
            item["page"],
            product_text,
            "Thickness and condition-linked structural/density properties.",
            value_status="mixed_reported_and_visually_digitized",
            confidence="medium",
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            "record_level",
            "SPAN_144A932982D06645C52D",
            11,
            (
                f"{condition_text} Ten 10 mm discs were processed; longest "
                "demonstrated operation was 320 min, 5.33 h. No normalized "
                "throughput, monetary cost or energy use was reported."
            ),
            "Scale evidence, process intensity and industrial data gaps.",
            value_status="review_assessment",
        )

    for control in CONTROL_RUNS:
        run_id = f"{SOURCE_ID}_{control['code']}"
        run_ids.append(run_id)
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                control["code"],
                control["label"],
                control["summary"],
                "medium",
            )
        )
        tables["catalyst_system"].append(catalyst(run_id, "LG"))
        tables["reactor_process_gas"].extend(
            [
                process_row(
                    run_id,
                    1,
                    "preexisting_vacnt_growth",
                    reactor_type="horizontal quartz aerosol-assisted CCVD reactor",
                    scale_level="lab_mechanistic_control",
                    reactor_material="quartz",
                    reactor_setup_summary=COMMON_RECIPE,
                    temperature_setpoint_C="615",
                    temperature_program_summary="initial VACNT growth at 615 C",
                    holding_time_min=(
                        "240"
                        if "240" in control["code"]
                        else "160"
                        if "160" in control["code"]
                        else "not_reported"
                    ),
                    pressure_original="atmospheric",
                    pressure_kPa="101.325",
                    carbon_source="C2H2",
                    carbon_source_flow_original="1.5 vol.%",
                    reducing_gas="H2",
                    reducing_gas_flow_original="10 vol.%",
                    inert_gas="Ar",
                    gas_composition_summary="1.5 vol.% C2H2; 10 vol.% H2; balance Ar",
                    process_note="Initial growth used the standard no-CO2 condition.",
                ),
                process_row(
                    run_id,
                    2,
                    "degradation_mechanism_control",
                    reactor_type="horizontal quartz aerosol-assisted CCVD reactor",
                    scale_level="lab_mechanistic_control",
                    reactor_material="quartz",
                    reactor_setup_summary=control["summary"],
                    temperature_setpoint_C="615",
                    temperature_program_summary="control exposure at 615 C",
                    holding_time_min=(
                        "80"
                        if control["code"] == "CONTROL_COLD_160_C2H2_ANNEAL_80"
                        else "40-160"
                        if "ARH2" in control["code"]
                        else "80"
                        if "REEXPOSURE" in control["code"]
                        else "80"
                    ),
                    pressure_original="atmospheric",
                    pressure_kPa="101.325",
                    carbon_source=("none" if "ARH2" in control["code"] else "C2H2"),
                    carbon_source_flow_original=(
                        "0 vol.%" if "ARH2" in control["code"] else "1.5 vol.%"
                    ),
                    reducing_gas="H2",
                    reducing_gas_flow_original="10 vol.%",
                    inert_gas="Ar",
                    cofeed_or_reactive_gas=(
                        "ferrocene aerosol"
                        if "FE_" in control["code"]
                        or "FE_REEXPOSURE" in control["code"]
                        else "none"
                    ),
                    gas_composition_summary=control["summary"],
                    process_note=control["summary"],
                ),
            ]
        )
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="qualitative_degradation_control",
                yield_original="no additional degradation or control-specific outcome",
                yield_definition_original=control["summary"],
                yield_calculation_method="SEM morphology and before/after mass comparison",
                yield_value_standardized="",
                yield_unit_standardized="",
                yield_standardization_note="Qualitative mechanistic control; no new mass yield.",
                secondary_result_summary=control["summary"],
                CNT_type_reported="VACNT carpet",
                CNT_type_confirmed="vertically aligned CNT carpet",
                product_mixture_summary="pre-existing and/or newly grown VACNT carpet",
                CNT_type_evidence="SEM cross-section",
                wall_number_summary="not_measured_for_control",
                length_summary="not separately quantified",
                morphology="control-specific result retained in secondary summary",
                alignment_or_array="vertically aligned carpet",
                Raman_ratio_type="not_reported_for_control",
                Raman_laser_wavelength_nm="not_reported_for_control",
                residue_summary="not_reported",
                amorphous_carbon_level="no new mass-forming impurity during cold anneal",
                characterization_methods="SEM; gravimetry",
                post_treatment_or_purification="post-growth thermal/control exposure",
                purification_condition="not_applicable",
            )
        )
        tables["cost_scale_review"].append(cost(run_id))
        evidence_text = (
            f"{control['summary']} Initial/control temperatures 615 C; "
            "atmospheric pressure 101.325 kPa. The standard initial growth "
            "feed contained 1.5 vol.% C2H2 and 10 vol.% H2; control stages "
            "using standard growth gas retained the same gas composition."
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "RUN",
            "source_run",
            run_id,
            "record_level",
            control["span"],
            control["page"],
            evidence_text,
            "Mechanistic-control identity and outcome.",
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "CATALYST",
            "catalyst_system",
            f"{run_id}_CAT",
            "record_level",
            control["span"],
            control["page"],
            evidence_text + " Ferrocene-derived Fe was the catalyst precursor.",
            "Catalyst context for degradation control.",
        )
        for stage in [1, 2]:
            add_pdf_evidence(
                tables,
                store,
                run_id,
                f"PROCESS_{stage}",
                "reactor_process_gas",
                f"{run_id}_S{stage:02d}",
                "record_level",
                control["span"],
                control["page"],
                evidence_text
                + (
                    " Initial growth duration was 240 min."
                    if "240" in control["code"]
                    else " Initial growth duration was 160 min."
                    if "160" in control["code"]
                    else ""
                )
                + (
                    " Control duration was 40-160 min."
                    if "ARH2" in control["code"]
                    else " Control duration was 80 min."
                ),
                f"Control process stage {stage}.",
            )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "PRODUCT",
            "yield_quality",
            f"{run_id}_PROD",
            "record_level",
            control["span"],
            control["page"],
            evidence_text,
            "Qualitative degradation-control outcome.",
            value_status="qualitative_control",
        )
        add_pdf_evidence(
            tables,
            store,
            run_id,
            "COST",
            "cost_scale_review",
            run_id,
            "record_level",
            control["span"],
            control["page"],
            evidence_text + " No cost or throughput normalization was reported.",
            "Control-process scale and data gaps.",
            value_status="review_assessment",
        )

    reference_id = run_ids[0]
    eq_lg = f"{SOURCE_ID}_LG_C2H2_1P5_CO2_1P5_080MIN"
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_DIGITIZATION_001",
                SOURCE_ID,
                reference_id,
                "figure_digitization",
                "yield_quality",
                f"{reference_id}_PROD",
                "yield_original",
                (
                    "Thickness, density, diameter and Raman FWHM point values "
                    "were visually digitized from figures; raw numeric tables "
                    "and exact plotted uncertainties are unavailable."
                ),
                f"EVD_{reference_id}_PRODUCT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SUPPLEMENT_001",
                SOURCE_ID,
                reference_id,
                "missing_supplementary_data",
                "yield_quality",
                f"{reference_id}_PROD",
                "secondary_result_summary",
                (
                    "Supplementary Tables S1-S4 are cited for Raman fits, "
                    "additional microscopy and literature data, but were not "
                    "included in the open HAL deposit; publisher data statement "
                    "says data are available on request."
                ),
                f"EVD_{reference_id}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FERROCENE_001",
                SOURCE_ID,
                reference_id,
                "critical_data_gap",
                "catalyst_system",
                f"{reference_id}_CAT",
                "precursor_summary",
                (
                    "The method gives a selectable ferrocene range of 0.25-2.5 "
                    "wt.% but not the exact concentration used for each plotted run."
                ),
                f"EVD_{reference_id}_CATALYST",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FLOW_001",
                SOURCE_ID,
                reference_id,
                "critical_data_gap",
                "reactor_process_gas",
                f"{reference_id}_S02",
                "total_flow_original",
                (
                    "Gas compositions are reported as volume percentages and "
                    "total flow was held constant, but the absolute total and "
                    "aerosol liquid flow rates are not reported."
                ),
                f"EVD_{reference_id}_PROCESS_1;EVD_{reference_id}_PROCESS_2",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FIG3_FIG4_001",
                SOURCE_ID,
                eq_lg,
                "figure_value_discrepancy",
                "yield_quality",
                f"{eq_lg}_PROD",
                "yield_original",
                (
                    "The nominal 80 min, 1.5 vol.% C2H2/1.5 vol.% CO2 "
                    "condition reads differently in Figures 3 and 4 "
                    "(about 360 vs 320 um on LG Al and 450 vs 390 um on HG Al); "
                    "the package retains a range/mean and flags the discrepancy."
                ),
                f"EVD_{eq_lg}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_BASIS_001",
                SOURCE_ID,
                reference_id,
                "yield_definition",
                "yield_quality",
                f"{reference_id}_PROD",
                "primary_yield_metric",
                (
                    "Carpet thickness is the primary production metric; no CNT "
                    "mass yield per catalyst, carbon conversion or productivity "
                    "is reported."
                ),
                f"EVD_{reference_id}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_DENSITY_CONTAMINATION_001",
                SOURCE_ID,
                f"{SOURCE_ID}_LG_C2H2_1P5_CO2_0_240MIN",
                "measurement_interference",
                "yield_quality",
                f"{SOURCE_ID}_LG_C2H2_1P5_CO2_0_240MIN_PROD",
                "application_property_summary",
                (
                    "For degraded long-duration LG-Al samples without CO2, "
                    "areal and bulk density can include dense disordered carbon "
                    "at the interface rather than only VACNT mass."
                ),
                f"EVD_{SOURCE_ID}_LG_C2H2_1P5_CO2_0_240MIN_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_IRON_BASIS_001",
                SOURCE_ID,
                reference_id,
                "evidence_scope",
                "yield_quality",
                f"{reference_id}_PROD",
                "purity_basis",
                (
                    "Iron below 2 wt.% is cited from the authors' previous TGA "
                    "work, not measured by TGA for every present run; current "
                    "TEM/STEM-EDX provides qualitative support."
                ),
                f"EVD_{reference_id}_PRODUCT",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_REPLICATES_001",
                SOURCE_ID,
                reference_id,
                "uncertainty_transcription",
                "cost_scale_review",
                reference_id,
                "batch_stability",
                (
                    "Ten discs and five SEM thickness locations provide "
                    "within-run replication, but exact pointwise error-bar "
                    "values were not available for transcription."
                ),
                f"EVD_{reference_id}_COST",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CONTROL_AGGREGATION_001",
                SOURCE_ID,
                f"{SOURCE_ID}_CONTROL_COLD_240_ARH2_ANNEAL",
                "grouped_control",
                "source_run",
                f"{SOURCE_ID}_CONTROL_COLD_240_ARH2_ANNEAL",
                "run_summary",
                (
                    "The paper summarizes multiple cold-carpet anneals over "
                    "40-160 min without listing every individual combination; "
                    "the grouped control record preserves only explicitly "
                    "reported ranges and qualitative outcomes."
                ),
                f"EVD_{SOURCE_ID}_CONTROL_COLD_240_ARH2_ANNEAL_RUN",
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
