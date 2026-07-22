#!/usr/bin/env python3
"""Build the thirty-fourth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 34
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ID = "LIT_11E2BBB5F0B2D893"
PDF_REF = "data/raw/literature/pdf/LIT_11E2BBB5F0B2D893_921dff6692b3.pdf"

ABSTRACT_SPAN = "SPAN_1AD014F92F7F0BE2A686"
MATERIAL_SPAN = "SPAN_B0DFDAE28064DA47B260"
INK_SPAN = "SPAN_DA164F404EED4E0166CE"
SUPPORT_SPAN = "SPAN_72A81E7AD9C1C9200A4C"
PROCESS_SPAN = "SPAN_13EC686879B12E11BBDF"
CHAR_SPAN = "SPAN_D224614C41E558C27B8B"
WITHDRAWAL_SPAN = "SPAN_7B370E6854504C83B527"
RATIO_SPAN = "SPAN_528D6FB212BC0035D024"
CONCENTRATION_SPAN = "SPAN_7571FA83B1F42E336DA3"
LAYER_SPAN = "SPAN_8FEFD8448713AB451882"
DENSITY_SPAN = "SPAN_FEA0B9542B0EF404C9A0"
GAS_TABLE_SPAN = "SPAN_EFB34346331163F91D65"
NITROGEN_SPAN = "SPAN_A9071F32975647FC422A"
WATER_SPAN = "SPAN_978B1EB5B67B2137EBFA"
TIME_SPAN = "SPAN_BB8DF0DAC685297BDB57"
TIME_LATE_SPAN = "SPAN_F8820784B9E16845C784"
HIGH_INK_TIME_SPAN = "SPAN_A7BDEF0607DBACFBC7A4"
MORPHOLOGY_SPAN = "SPAN_BC5104D1754CD0A5F1C7"
CONCLUSION_SPAN = "SPAN_CA68CA89A5C8314D66D0"


def item(
    code: str,
    series: str,
    *,
    ink_m: float = 0.11,
    ratio: str = "2:3",
    withdrawal: str = "not separately reported",
    n2: int = 50,
    c2h4: int = 70,
    h2: int = 100,
    water: int | None = 30,
    time_min: int = 15,
    height_um: float | None = None,
    height_status: str = "",
    outcome: str,
    confidence: str = "high",
    density: float | None = None,
    charge: float | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "series": series,
        "ink_m": ink_m,
        "ratio": ratio,
        "withdrawal": withdrawal,
        "n2": n2,
        "c2h4": c2h4,
        "h2": h2,
        "water": water,
        "time_min": time_min,
        "height_um": height_um,
        "height_status": height_status,
        "outcome": outcome,
        "confidence": confidence,
        "density": density,
        "charge": charge,
    }


RUNS: list[dict[str, Any]] = [
    item(
        "WITHDRAWAL_50_200_GROUP",
        "withdrawal",
        withdrawal="50-200 mm/min grouped range",
        outcome=(
            "lowest withdrawal speed gave poor height and quality; increasing "
            "withdrawal speed produced higher forests with better orientation"
        ),
        confidence="medium",
    ),
    *[
        item(
            f"RATIO_FECO_{ratio.replace(':', '_')}",
            "ratio",
            ratio=ratio,
            height_um=height,
            height_status=status,
            outcome=outcome,
            confidence=confidence,
        )
        for ratio, height, status, outcome, confidence in [
            ("0:1", None, "", "pure Co salt produced no carbon deposit", "high"),
            (
                "1:3",
                60,
                "reported_approximate",
                "highest forest, almost 60 micrometre",
                "high",
            ),
            (
                "2:3",
                44,
                "visual_estimate",
                "active bimetallic layer; about 44 micrometre in Fig. 2b",
                "medium",
            ),
            (
                "1:1",
                20,
                "reported_approximate",
                "lowest bimetallic result, approximately 20 micrometre in text",
                "high",
            ),
            (
                "3:2",
                42,
                "visual_estimate",
                "active bimetallic layer; about 42 micrometre in Fig. 2b",
                "medium",
            ),
            (
                "3:1",
                47,
                "visual_estimate",
                "active bimetallic layer; about 47 micrometre in Fig. 2b",
                "medium",
            ),
            ("1:0", None, "", "pure Fe salt produced no carbon deposit", "high"),
        ]
    ],
    *[
        item(
            f"INK_{str(conc).replace('.', 'P')}M",
            "concentration",
            ink_m=conc,
            height_um=height,
            height_status=status,
            outcome=outcome,
            confidence=confidence,
            density=density,
            charge=charge,
        )
        for conc, height, status, outcome, confidence, density, charge in [
            (
                0.022,
                None,
                "",
                "lowest ink concentration produced no significant carbon deposit",
                "high",
                None,
                None,
            ),
            (
                0.044,
                0.87,
                "visual_estimate",
                "carbonaceous deposit with only disordered CNTs",
                "medium",
                None,
                2.8,
            ),
            (
                0.066,
                6.66,
                "visual_estimate",
                "well-aligned CNT forest at lower height",
                "medium",
                0.29,
                6.2,
            ),
            (
                0.11,
                15.5,
                "visual_estimate",
                "reference ink identified by the authors as optimum",
                "medium",
                0.35,
                12.5,
            ),
            (
                0.22,
                14.5,
                "visual_estimate",
                "well-aligned CNT forest in the above-threshold plateau",
                "medium",
                0.24,
                10.1,
            ),
            (
                0.44,
                19.5,
                "visual_estimate",
                "well-aligned forest; Fig. 3b appears higher than the stated optimum",
                "medium",
                0.24,
                9.8,
            ),
            (
                0.66,
                12.7,
                "visual_estimate",
                "well-aligned CNT forest in the above-threshold plateau",
                "medium",
                0.28,
                9.6,
            ),
        ]
    ],
]

for varied, values in (
    ("N2", (50, 60, 75)),
    ("C2H4", (70, 95, 120)),
    ("H2", (100, 110, 130)),
):
    for index, value in enumerate(values):
        water_value = (32, 37, 42)[index]
        kwargs = {"n2": 50, "c2h4": 70, "h2": 100}
        kwargs[varied.lower()] = value
        no_water_height = None
        water_height = None
        if varied == "N2":
            no_water_height = (15.0, 24.7, 12.1)[index]
            water_height = (18.2, 16.0, 18.8)[index]
        RUNS.append(
            item(
                f"GAS_{varied}_{value}_NOWATER",
                "gas",
                water=None,
                height_um=no_water_height,
                height_status="visual_estimate" if no_water_height else "",
                outcome=(
                    "without water vapor; lower orientation quality and more defects"
                    + (
                        f"; Fig. 5 height about {no_water_height} micrometre"
                        if no_water_height
                        else ""
                    )
                ),
                confidence="medium",
                **kwargs,
            )
        )
        RUNS.append(
            item(
                f"GAS_{varied}_{value}_WATER_{water_value}",
                "gas",
                water=water_value,
                height_um=water_height,
                height_status="visual_estimate" if water_height else "",
                outcome=(
                    "with water vapor; orientation quality improved"
                    + (
                        f"; Fig. 5 height about {water_height} micrometre"
                        if water_height
                        else ""
                    )
                ),
                confidence="medium",
                **kwargs,
            )
        )

RUNS.extend(
    [
        item(
            f"WATER_{flow}",
            "water",
            water=flow,
            height_um=height,
            height_status=status,
            outcome=outcome,
            confidence=confidence,
        )
        for flow, height, status, outcome, confidence in [
            (
                20,
                7,
                "reported",
                "smallest forest; sinuous CNTs",
                "high",
            ),
            (
                30,
                21.9,
                "reported",
                "highest forest and optimum water-vapor flow",
                "high",
            ),
            (
                40,
                19.8,
                "visual_estimate",
                "well-oriented forest below the 30 cm3/min maximum",
                "medium",
            ),
            (
                50,
                9.2,
                "visual_estimate",
                "forest height decreased as water-assisted degradation increased",
                "medium",
            ),
            (
                60,
                8.1,
                "visual_estimate",
                "forest height remained low at the highest water flow",
                "medium",
            ),
        ]
    ]
)

RUNS.extend(
    [
        item(
            f"TIME_0P11_{time}",
            "time_011",
            time_min=time,
            height_um=height,
            height_status=status,
            outcome=outcome,
            confidence=confidence,
        )
        for time, height, status, outcome, confidence in [
            (
                5,
                6.7,
                "reported",
                "alignment had just started; moderate-height forest",
                "high",
            ),
            (
                10,
                23,
                "visual_estimate",
                "substantially improved length and orderliness",
                "medium",
            ),
            (
                15,
                28,
                "reported",
                "maximum forest height in the 0.11 M time series",
                "high",
            ),
            (
                30,
                17.5,
                "visual_estimate",
                "height declined after the 15 min maximum",
                "medium",
            ),
            (
                60,
                0,
                "reported",
                "complete disappearance of the carbon deposit",
                "high",
            ),
        ]
    ]
)

RUNS.extend(
    [
        item(
            f"TIME_0P66_{time}",
            "time_066",
            ink_m=0.66,
            time_min=time,
            height_um=height,
            height_status=status,
            outcome=outcome,
            confidence=confidence,
        )
        for time, height, status, outcome, confidence in [
            (
                2,
                None,
                "",
                "carbon deposit appeared but no CNTs or ordered fibers were recognized",
                "high",
            ),
            (
                4,
                None,
                "",
                "deposit quality changed but characteristic alignment was absent",
                "high",
            ),
            (
                6,
                12.5,
                "reported",
                "shortest duration producing a well-oriented CNT forest",
                "high",
            ),
            (
                15,
                18.5,
                "reported",
                "well-oriented CNT forest",
                "high",
            ),
        ]
    ]
)


def run_summary(entry: dict[str, Any]) -> str:
    water = (
        "without water vapor"
        if entry["water"] is None
        else f"water vapor {entry['water']} cm3/min"
    )
    height = (
        ""
        if entry["height_um"] is None
        else f"; forest height {entry['height_um']} micrometre"
    )
    return (
        f"Fe:Co {entry['ratio']} ink at {entry['ink_m']} M on oxidized aluminum; "
        f"withdrawal {entry['withdrawal']}; CCVD at 640 C for "
        f"{entry['time_min']} min with C2H4/H2/N2 "
        f"{entry['c2h4']}/{entry['h2']}/{entry['n2']} cm3/min and {water}"
        f"{height}. Outcome: {entry['outcome']}."
    )


def catalyst(entry: dict[str, Any], run_id: str) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label=f"Fe-Co nitrate dip-coated Al, Fe:Co {entry['ratio']}",
        active_metals="Fe; Co",
        support_material="WRS aluminum plate with thermally thickened native alumina",
        promoter="none",
        metal_ratio_original=f"Fe:Co = {entry['ratio']}",
        metal_ratio_standardized=f"Fe:Co = {entry['ratio']}",
        precursor_summary=(
            "Fe(NO3)3·9H2O and Co(NO3)2·6H2O in absolute ethanol; "
            f"total ink concentration {entry['ink_m']} M"
        ),
        preparation_method="dip coating",
        preparation_modifier=(
            "KSV LM dip coater; dipping 200 mm/min; "
            f"withdrawal {entry['withdrawal']}; immersion 5 s"
        ),
        preparation_detail=(
            "Al ultrasonicated in distilled water, sequentially washed with "
            "ethanol and acetone, heated at 400 C for 1 h, flattened, dip "
            "coated with freshly prepared ink, then reheated at 400 C for 1 h."
        ),
        drying_condition="not separately reported before post-dip heating",
        calcination_condition="400 C for 1 h in static oven; 30 C/min heating rate",
        reduction_condition="in situ H2 at 640 C for 5 min",
        activation_condition="hydrogen reduction immediately before ethylene addition",
        post_preparation_condition="3 x 0.4 cm catalyst-coated Al strip in quartz boat",
        catalyst_particle_size_mean_nm="",
        catalyst_particle_size_range_nm="",
        catalyst_particle_size_qualifier=(
            "Particle size could not be determined precisely because of sintering; "
            "native oxide depth 10 nm and average catalyst-layer thickness 20 nm."
        ),
        phase_or_state_summary="Fe-Co oxide/nitrate-derived particles on native alumina",
        dispersion_summary="Al substrate homogeneously covered in blank CCVD controls",
        deactivation_summary=(
            "gradual catalyst inactivation and water-assisted CNT degradation "
            "were proposed for long-duration runs"
        ),
    )


def process_rows(entry: dict[str, Any], run_id: str) -> list[dict[str, str]]:
    total = entry["n2"] + entry["c2h4"] + entry["h2"] + (entry["water"] or 0)
    common = {
        "reactor_type": "horizontal quartz-tube CCVD reactor",
        "scale_level": "laboratory_substrate_CVD",
        "reactor_material": "20 mm diameter quartz tube; quartz boat",
        "reactor_size_summary": "3 x 0.4 cm coated Al strip in 20 mm quartz tube",
        "reactor_setup_summary": "tube inserted into furnace at 640 C under N2",
        "catalyst_loading_mass_g": "",
        "temperature_setpoint_C": "640",
        "temperature_range_reported_C": "640",
        "heating_rate_C_min": "not_reported_for_insertion",
        "pressure_original": "not_reported",
        "pressure_kPa": "",
    }
    return [
        process_row(
            run_id,
            1,
            "hydrogen_reduction",
            **common,
            temperature_program_summary="N2 purge followed by in-situ H2 reduction",
            holding_time_min="5",
            cooling_condition="not_applicable before growth",
            carbon_source="none",
            carbon_source_flow_original="0 cm3/min",
            reducing_gas="H2",
            reducing_gas_flow_original=f"{entry['h2']} cm3/min",
            inert_gas="N2",
            inert_gas_flow_original=f"{entry['n2']} cm3/min",
            cofeed_or_reactive_gas="none",
            cofeed_flow_original="0 cm3/min",
            total_flow_original=f"{entry['n2'] + entry['h2']} cm3/min",
            gas_composition_summary=(f"H2 {entry['h2']} and N2 {entry['n2']} cm3/min"),
            process_note="Typical protocol specifies a 5 min catalyst reduction.",
        ),
        process_row(
            run_id,
            2,
            "ethylene_CCVD_growth",
            **common,
            temperature_program_summary="isothermal ethylene CCVD at 640 C",
            holding_time_min=str(entry["time_min"]),
            cooling_condition=(
                "all gases except N2 off; N2 rinse 2 min, tube removed and "
                "cooled to room temperature under N2"
            ),
            carbon_source="C2H4",
            carbon_source_flow_original=f"{entry['c2h4']} cm3/min",
            reducing_gas="H2",
            reducing_gas_flow_original=f"{entry['h2']} cm3/min",
            inert_gas="N2",
            inert_gas_flow_original=f"{entry['n2']} cm3/min",
            cofeed_or_reactive_gas=(
                "none" if entry["water"] is None else "water vapor"
            ),
            cofeed_flow_original=(
                "0 cm3/min" if entry["water"] is None else f"{entry['water']} cm3/min"
            ),
            total_flow_original=f"{total} cm3/min",
            gas_composition_summary=(
                f"C2H4/H2/N2 = {entry['c2h4']}/{entry['h2']}/{entry['n2']} "
                + (
                    "cm3/min without water"
                    if entry["water"] is None
                    else f"cm3/min plus water {entry['water']} cm3/min"
                )
            ),
            process_note=(
                "Gas flows were varied one factor at a time in the dedicated "
                "gas-feed series."
            ),
        ),
    ]


def product(entry: dict[str, Any], run_id: str) -> dict[str, str]:
    height = entry["height_um"]
    dimensions = entry["series"] == "concentration" and entry["ink_m"] in {
        0.066,
        0.11,
        0.66,
    }
    cnt_positive = not (
        entry["outcome"].startswith("pure ")
        or "no significant carbon" in entry["outcome"]
        or "no CNTs" in entry["outcome"]
        or "complete disappearance" in entry["outcome"]
    )
    secondary = run_summary(entry)
    if entry["density"] is not None:
        secondary += f" Approximate forest density {entry['density']} g/cm3."
    if entry["charge"] is not None:
        secondary += f" Figure-read charge capacity about {entry['charge']} mC/cm2."
    return yield_row(
        run_id,
        primary_yield_metric="CNT_forest_height",
        yield_original=(
            entry["outcome"]
            if height is None
            else f"{height} micrometre CNT forest height"
        ),
        yield_definition_original="35-degree-corrected SEM forest height",
        yield_calculation_method="SEM/ImageJ; some values visually read from plots",
        yield_value_standardized="" if height is None else str(height),
        yield_unit_standardized="micrometre",
        yield_standardization_note=(
            "Figure-read values are approximate and explicitly flagged in evidence."
            if entry["height_status"] == "visual_estimate"
            else "Reported height retained without conversion."
        ),
        CNT_yield_per_catalyst_g_gcat="",
        CNT_productivity_g_gcat_h="",
        carbon_source_conversion_percent="",
        carbon_conversion_to_solid_percent="",
        secondary_result_summary=secondary,
        CNT_type_reported="VACNT forest" if cnt_positive else "no confirmed CNT forest",
        CNT_type_confirmed=(
            "few-wall vertically aligned CNT"
            if dimensions
            else ("CNT_forest" if cnt_positive else "none_or_unconfirmed")
        ),
        product_mixture_summary="CNT forest directly attached to conductive Al substrate",
        CNT_type_evidence="SEM; TEM and Raman for selected concentration samples",
        SWCNT_or_few_wall_evidence_summary=(
            "3-6 walls on average" if dimensions else "not measured for this run"
        ),
        RBM_peak_reported="not_reported",
        outer_diameter_mean_nm="",
        outer_diameter_range_nm="6-10" if dimensions else "",
        inner_diameter_mean_nm="",
        wall_number_summary="3-6 walls on average" if dimensions else "not_reported",
        length_summary=("" if height is None else f"forest height {height} micrometre"),
        morphology=entry["outcome"],
        alignment_or_array=(
            "vertically aligned forest"
            if cnt_positive and "disordered" not in entry["outcome"]
            else entry["outcome"]
        ),
        Raman_ratio_type="IG/ID" if dimensions else "not_reported",
        Raman_ratio_value="1.07 +/- 0.04" if dimensions else "",
        Raman_laser_wavelength_nm="532" if dimensions else "",
        TGA_carbon_content_wt_percent="",
        purified_product_purity_wt_percent="",
        purity_basis="as-grown CNT forest on Al substrate",
        residue_summary="Fe-Co catalyst and Al/native-alumina substrate",
        amorphous_carbon_level=(
            "almost no amorphous carbon on outer CNT surfaces"
            if dimensions
            else "not_quantified"
        ),
        BET_surface_area_product_m2_g="",
        characterization_methods="SEM; TEM; Raman; cyclic voltammetry; weighing",
        post_treatment_or_purification="none",
        purification_condition="not_applicable",
        application_property_summary=(
            ""
            if entry["charge"] is None
            else (
                f"approximate charge capacity {entry['charge']} mC/cm2; "
                "electrical contact between CNTs and Al demonstrated"
            )
        ),
        notes=(
            "Density and charge capacity are approximate plot/table results."
            if entry["series"] == "concentration"
            else "No CNT mass yield or carbon conversion was reported."
        ),
    )


def cost_review(entry: dict[str, Any], run_id: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="laboratory substrate CCVD",
        scale_level_claimed="cheap and easy VACNT production on conductive substrate",
        scale_evidence_summary=run_summary(entry),
        reactor_capacity_or_throughput="single 3 x 0.4 cm Al strip; no mass throughput",
        continuous_operation_time_h=str(entry["time_min"] / 60),
        catalyst_lifetime_or_reuse="not a catalyst-reuse experiment",
        catalyst_reuse_cycles="not_reported",
        batch_stability="not_reported",
        scale_up_issue=(
            "uniform dip coating, Al temperature limit, water control, gas "
            "consumption, substrate handling and absence of mass-yield data"
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="No study-specific cost calculation was reported.",
        cost_driver_summary="metal nitrates, dip coating, 640 C furnace and process gases",
        safety_risk="flammable ethylene/H2 at 640 C; nitrate and solvent handling",
        emission_or_waste="unreacted gases, ethanol/acetone wash and coated Al coupons",
        industrial_readiness_assessment="laboratory parameter study",
        reproduction_value="high",
        reproduction_priority=(
            "high"
            if entry["series"] in {"ratio", "concentration", "water", "time_011"}
            else "medium"
        ),
        recommended_next_action=(
            "report exact replicate matrix, mass CNT yield, gas conversion, "
            "coating uniformity, scale-up throughput and process economics"
        ),
        review_note="Claims of cheap/easy processing are qualitative.",
    )


def result_span(entry: dict[str, Any]) -> tuple[str, int]:
    return {
        "withdrawal": (WITHDRAWAL_SPAN, 3),
        "ratio": (RATIO_SPAN, 4),
        "concentration": (CONCENTRATION_SPAN, 5),
        "gas": (NITROGEN_SPAN if entry["n2"] != 50 else GAS_TABLE_SPAN, 7),
        "water": (WATER_SPAN, 8),
        "time_011": (
            TIME_LATE_SPAN if entry["time_min"] == 60 else TIME_SPAN,
            9,
        ),
        "time_066": (HIGH_INK_TIME_SPAN, 9),
    }[entry["series"]]


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
    evidence = evidence_row(
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
    evidence.update(
        {
            "evidence_type": "pdf_text_and_visual_figure_transcription",
            "source_section": f"PDF page {page}",
            "source_locator": f"PDF page {page}",
            "source_object_ref": PDF_REF,
            "evidence_text": text,
            "evidence_summary": summary,
            "notes": "Text and plot values checked against the local open-access PDF.",
        }
    )
    tables["evidence_index"].append(evidence)


def add_run(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    entry: dict[str, Any],
) -> str:
    run_id = f"{SOURCE_ID}_{entry['code']}"
    summary = run_summary(entry)
    source = run_row(
        SOURCE_ID,
        entry["code"],
        f"{entry['series']} parameter record",
        summary,
        entry["confidence"],
    )
    if entry["series"] == "withdrawal":
        source["data_type"] = "experimental_series_summary"
    tables["source_run"].append(source)
    cat = catalyst(entry, run_id)
    stages = process_rows(entry, run_id)
    prod = product(entry, run_id)
    cost = cost_review(entry, run_id)
    tables["catalyst_system"].append(cat)
    tables["reactor_process_gas"].extend(stages)
    tables["yield_quality"].append(prod)
    tables["cost_scale_review"].append(cost)

    span, page = result_span(entry)
    status = entry["height_status"] or "reported"
    add_evidence(
        tables,
        store,
        run_id,
        "RUN",
        "source_run",
        run_id,
        span,
        page,
        summary,
        "Run/series identity, varied factor and outcome.",
        confidence=entry["confidence"],
        status=status,
    )
    add_evidence(
        tables,
        store,
        run_id,
        "CATALYST",
        "catalyst_system",
        cat["catalyst_id"],
        INK_SPAN,
        2,
        (
            f"{cat['catalyst_label']}; active metals {cat['active_metals']}; "
            f"support {cat['support_material']}; precursor "
            f"{cat['precursor_summary']}; preparation "
            f"{cat['preparation_detail']}; modifier "
            f"{cat['preparation_modifier']}; calcination "
            f"{cat['calcination_condition']}; reduction "
            f"{cat['reduction_condition']}; layer/particle context "
            f"{cat['catalyst_particle_size_qualifier']}"
        ),
        "Catalyst ink, Al pretreatment, dip coating and activation.",
    )
    for stage in stages:
        add_evidence(
            tables,
            store,
            run_id,
            f"PROCESS_{stage['stage_order']}",
            "reactor_process_gas",
            stage["process_stage_id"],
            PROCESS_SPAN,
            3,
            (
                f"Stage {stage['stage_order']} {stage['stage_type']}; reactor "
                f"{stage['reactor_type']}; material {stage['reactor_material']}; "
                f"size {stage['reactor_size_summary']}; temperature "
                f"{stage['temperature_setpoint_C']} C; duration "
                f"{stage['holding_time_min']} min; pressure "
                f"{stage['pressure_original']} / {stage['pressure_kPa']} kPa; "
                f"carbon {stage['carbon_source_flow_original']}; H2 "
                f"{stage['reducing_gas_flow_original']}; N2 "
                f"{stage['inert_gas_flow_original']}; cofeed "
                f"{stage['cofeed_flow_original']}; total "
                f"{stage['total_flow_original']}; composition "
                f"{stage['gas_composition_summary']}; cooling "
                f"{stage['cooling_condition']}"
            ),
            f"Process stage {stage['stage_order']} support.",
        )
    product_span = (
        MORPHOLOGY_SPAN
        if entry["series"] == "concentration" and entry["ink_m"] in {0.066, 0.11, 0.66}
        else span
    )
    add_evidence(
        tables,
        store,
        run_id,
        "PRODUCT",
        "yield_quality",
        prod["product_id"],
        product_span,
        9 if product_span == MORPHOLOGY_SPAN else page,
        (
            f"{summary} Yield {prod['yield_original']}; standardized "
            f"{prod['yield_value_standardized']} {prod['yield_unit_standardized']}; "
            f"type {prod['CNT_type_confirmed']}; diameter "
            f"{prod['outer_diameter_range_nm']} nm; walls "
            f"{prod['wall_number_summary']}; Raman "
            f"{prod['Raman_ratio_type']} {prod['Raman_ratio_value']} at "
            f"{prod['Raman_laser_wavelength_nm']} nm; "
            f"secondary results {prod['secondary_result_summary']}"
        ),
        "Forest height, morphology and selected density/electrochemical data.",
        confidence=entry["confidence"],
        status=status,
    )
    add_evidence(
        tables,
        store,
        run_id,
        "COST",
        "cost_scale_review",
        run_id,
        CONCLUSION_SPAN,
        10,
        (
            "Laboratory 3 x 0.4 cm Al coupon CCVD; no mass throughput or "
            "quantitative cost. The authors call the dip-coating route cheap "
            "and easy; review flags furnace/gas/safety and scale-up needs."
        ),
        "Scale, cost-data gap and safety review.",
        status="review_assessment",
    )
    return run_id


def build(
    metadata: dict[str, Any],
    store: EvidenceStore,
) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "Forty-seven records: one grouped withdrawal-speed screen, "
                "seven Fe:Co ratios, seven ink concentrations, eighteen gas-feed "
                "conditions, five water-flow conditions, five 0.11 M time points "
                "and four 0.66 M time points."
            ),
        )
    )
    master = tables["source_master"][0]
    master["local_file_path"] = PDF_REF
    master["pdf_status"] = "validated_local_open_access_pdf"
    master["notes"] += (
        " Plot-read values are marked approximate. Text/figure discrepancies "
        "for catalyst ratio, ink concentration and Fig. 5 labeling are retained "
        "in the issue log rather than silently resolved."
    )
    run_ids = {entry["code"]: add_run(tables, store, entry) for entry in RUNS}

    withdrawal = run_ids["WITHDRAWAL_50_200_GROUP"]
    ratio_11 = run_ids["RATIO_FECO_1_1"]
    ratio_10 = run_ids["RATIO_FECO_1_0"]
    ink_011 = run_ids["INK_0P11M"]
    ink_044 = run_ids["INK_0P44M"]
    gas_n2_60 = run_ids["GAS_N2_60_NOWATER"]
    gas_c2h4 = run_ids["GAS_C2H4_95_WATER_37"]
    water_30 = run_ids["WATER_30"]
    time_60 = run_ids["TIME_0P11_60"]
    time_066 = run_ids["TIME_0P66_6"]
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_WITHDRAWAL_LEVELS_001",
                SOURCE_ID,
                withdrawal,
                "incomplete_run_matrix",
                "source_run",
                withdrawal,
                "run_summary",
                (
                    "Only the 50-200 mm/min withdrawal range and qualitative "
                    "trend are reported; discrete intermediate speeds and "
                    "individual heights are unavailable."
                ),
                f"EVD_{withdrawal}_RUN",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_RATIO_TEXT_FIGURE_001",
                SOURCE_ID,
                ratio_11,
                "text_figure_discrepancy",
                "yield_quality",
                f"{ratio_11}_PROD",
                "yield_original",
                (
                    "The text reports approximately 20 micrometre for Fe:Co 1:1, "
                    "whereas Fig. 2b visually plots about 31 micrometre. The text "
                    "value is retained as primary."
                ),
                f"EVD_{ratio_11}_RUN;EVD_{ratio_11}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_MONOMETALLIC_FIGURE_001",
                SOURCE_ID,
                ratio_10,
                "text_figure_discrepancy",
                "yield_quality",
                f"{ratio_10}_PROD",
                "yield_original",
                (
                    "The text says pure Fe and pure Co inks produced no carbon "
                    "deposit, but Fig. 2b includes an approximately 10 micrometre "
                    "point labeled Fe:Co 1:0. The explicit text is retained."
                ),
                f"EVD_{ratio_10}_RUN;EVD_{ratio_10}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_INK_OPTIMUM_001",
                SOURCE_ID,
                ink_044,
                "text_figure_discrepancy",
                "yield_quality",
                f"{ink_044}_PROD",
                "yield_original",
                (
                    "The authors call 0.11 M the highest/optimum forest, while "
                    "Fig. 3b visually shows the 0.44 M point near 19.5 micrometre, "
                    "above the 0.11 M point near 15.5 micrometre."
                ),
                f"EVD_{ink_011}_PRODUCT;EVD_{ink_044}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_DENSITY_APPROX_001",
                SOURCE_ID,
                ink_011,
                "measurement_uncertainty",
                "yield_quality",
                f"{ink_011}_PROD",
                "secondary_result_summary",
                (
                    "Forest density was estimated from small mass differences, "
                    "height and area; the authors explicitly call the weighing "
                    "method approximate because forests contain more than 90% air."
                ),
                f"EVD_{ink_011}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_CHARGE_FIGURE_001",
                SOURCE_ID,
                ink_011,
                "figure_read_approximation",
                "yield_quality",
                f"{ink_011}_PROD",
                "application_property_summary",
                (
                    "Charge capacities were visually transcribed from Fig. 4b; "
                    "the plot does not provide printed numeric labels for each point."
                ),
                f"EVD_{ink_011}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_GAS_WATER_MAPPING_001",
                SOURCE_ID,
                gas_c2h4,
                "shared_table_mapping",
                "reactor_process_gas",
                f"{gas_c2h4}_S02",
                "cofeed_flow_original",
                (
                    "Table 1 pairs water flows 32/37/42 cm3/min with increasing "
                    "N2, C2H4 or H2 levels. The paper also says parallel series "
                    "were run with and without water; these are split as separate records."
                ),
                f"EVD_{gas_c2h4}_RUN;EVD_{gas_c2h4}_PROCESS_2",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FIG5_AXIS_CAPTION_001",
                SOURCE_ID,
                gas_n2_60,
                "figure_label_discrepancy",
                "yield_quality",
                f"{gas_n2_60}_PROD",
                "yield_original",
                (
                    "Fig. 5 caption identifies a nitrogen-flow screen, but panel "
                    "g labels the x-axis ethylene/hydrogen. The point-to-condition "
                    "mapping follows panels a-f and the caption."
                ),
                f"EVD_{gas_n2_60}_RUN;EVD_{gas_n2_60}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_GAS_HEIGHT_SCOPE_001",
                SOURCE_ID,
                gas_c2h4,
                "measurement_scope",
                "yield_quality",
                f"{gas_c2h4}_PROD",
                "yield_original",
                (
                    "Numeric heights are published only for the nitrogen-flow "
                    "screen. Ethylene- and hydrogen-flow records retain the "
                    "reported qualitative water/orientation observation."
                ),
                f"EVD_{gas_c2h4}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_TIME_60_EXTRAPLOT_001",
                SOURCE_ID,
                time_60,
                "measurement_scope",
                "yield_quality",
                f"{time_60}_PROD",
                "yield_original",
                (
                    "Complete disappearance at approximately 60 min is stated "
                    "in text; Fig. 7i plots only 5, 10, 15 and 30 min."
                ),
                f"EVD_{time_60}_RUN;EVD_{time_60}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_MORPHOLOGY_SCOPE_001",
                SOURCE_ID,
                ink_011,
                "measurement_scope",
                "yield_quality",
                f"{ink_011}_PROD",
                "outer_diameter_range_nm",
                (
                    "The 6-10 nm diameter, 3-6 walls and IG/ID 1.07 +/- 0.04 "
                    "are demonstrated for representative 0.066, 0.11 and 0.66 M "
                    "samples and are not propagated to every condition."
                ),
                f"EVD_{ink_011}_PRODUCT;EVD_{time_066}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PRESSURE_001",
                SOURCE_ID,
                water_30,
                "critical_data_gap",
                "reactor_process_gas",
                f"{water_30}_S02",
                "pressure_original",
                "CCVD operating pressure was not reported.",
                f"EVD_{water_30}_PROCESS_2",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_NO_MASS_YIELD_001",
                SOURCE_ID,
                water_30,
                "critical_data_gap",
                "yield_quality",
                f"{water_30}_PROD",
                "CNT_yield_per_catalyst_g_gcat",
                (
                    "Forest height, density and electrochemical accessibility "
                    "were measured, but no CNT mass yield, carbon conversion, "
                    "purity or gas balance was reported."
                ),
                f"EVD_{water_30}_PRODUCT",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SCALE_COST_001",
                SOURCE_ID,
                ink_011,
                "scale_limit",
                "cost_scale_review",
                ink_011,
                "quantitative_cost_summary",
                (
                    "The route is described as cheap and easy, but only small "
                    "Al coupons were demonstrated and no cost or throughput "
                    "calculation was supplied."
                ),
                f"EVD_{ink_011}_COST",
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
