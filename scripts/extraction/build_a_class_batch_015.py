#!/usr/bin/env python3
"""Build the fifteenth evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 15
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "data/interim/extraction_batches" / BATCH_ID
SOURCE_ID = "LIT_A7E485A52DA7BA40"
PDF_NAME = f"{SOURCE_ID}_182bb37c7d0b.pdf"
SUPPLEMENT_NAME = "catalysts-2569843-supplementary.pdf"


def append_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    suffix: str,
    table: str,
    record_id: str,
    fields: str,
    span_id: str,
    summary: str,
    value_status: str = "reported",
) -> None:
    tables["evidence_index"].append(
        evidence_row(
            store,
            SOURCE_ID,
            f"EVD_{run_id}_{suffix}",
            run_id,
            table,
            record_id,
            fields,
            span_id,
            summary,
            value_status=value_status,
        )
    )


def append_pdf_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    suffix: str,
    fields: str,
    *,
    span_id: str,
    page: int,
    evidence_text: str,
    summary: str,
    supplement: bool = False,
    value_status: str = "reported",
) -> None:
    evidence = evidence_row(
        store,
        SOURCE_ID,
        f"EVD_{run_id}_{suffix}",
        run_id,
        "yield_quality",
        f"{run_id}_PROD",
        fields,
        span_id,
        summary,
        value_status=value_status,
    )
    if supplement:
        source_ref = (
            "data/raw/fulltext/supplementary/"
            f"{SOURCE_ID}/catalysts-13-01259-s001/{SUPPLEMENT_NAME}#page={page}"
        )
        source_section = f"Supplementary Figure S{3 if page == 2 else 5}"
        source_locator = f"supplementary PDF page {page}"
    else:
        source_ref = f"data/raw/fulltext/pdf/{PDF_NAME}#page={page}"
        source_section = f"Main-article PDF page {page}"
        source_locator = f"PDF page {page}"
    evidence.update(
        {
            "evidence_type": "pdf_figure_value_transcription",
            "source_section": source_section,
            "source_locator": source_locator,
            "source_object_ref": source_ref,
            "evidence_text": evidence_text,
            "evidence_summary": summary,
            "notes": (
                "Locally stored author/publisher PDF was visually inspected; "
                "values without printed labels are explicitly marked approximate."
            ),
        }
    )
    tables["evidence_index"].append(evidence)


def common_catalyst(run_id: str) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label="Fe2O3/Al2O3 mixed-iron-oxide catalyst",
        active_metals="Fe",
        support_material="Al2O3",
        promoter="not_applicable",
        metal_ratio_original=(
            "author states Fe(II)/Fe(III)=2; reagent amounts are 10/20 mmol"
        ),
        metal_ratio_standardized="unresolved_source_inconsistency",
        precursor_summary=(
            "10 mmol FeCl2 in 20 mL ethanol; 20 mmol FeCl3 in 80 mL "
            "ethylene glycol; 6.6 g Al2O3"
        ),
        preparation_method="sol_gel",
        preparation_modifier="ice-bath equilibration before mixing",
        preparation_detail=(
            "FeCl2/ethanol was heated to boiling; FeCl3/ethylene glycol was "
            "held at 60 C for 5 min. After ice-bath equilibration, both "
            "solutions were mixed with 6.6 g alumina at 60 C for 2 h, "
            "then held at 120 C for about 3 h to gel and heated to 200 C "
            "until a powder formed."
        ),
        drying_condition="integrated 120 C gel formation and 200 C powdering",
        calcination_condition=("N2 100 mNL/min: 300 C for 12 h, then 600 C for 24 h"),
        reduction_condition="not separately reported before CVD",
        activation_condition="thermal treatment under N2",
        post_preparation_condition="fresh Fe2O3/Al2O3 powder",
        catalyst_particle_size_mean_nm="not_reported",
        catalyst_particle_size_range_nm="not_reported",
        catalyst_particle_size_qualifier="not_reported",
        BET_surface_area_m2_g="98",
        pore_volume_cm3_g="0.273",
        phase_or_state_summary=(
            "XRD semi-quantitative composition: 76% Al2O3, 22% Fe2O3 and "
            "1% Fe3O4; atomic absorption: 15 wt.% Fe"
        ),
        dispersion_summary="mixed iron-oxide phases supported on alumina",
        deactivation_summary=(
            "iron can become encapsulated inside carbon and resist acid removal"
        ),
    )


def cvd_process(
    run_id: str,
    carbon_source: str,
    temperature: int,
    *,
    mixture: bool = False,
) -> dict[str, str]:
    return process_row(
        run_id,
        1,
        "single_stage_polyolefin_pyrolysis_CVD",
        reactor_type="vertical three-zone pyrolysis/CVD oven",
        scale_level="lab_batch",
        reactor_material="not_reported",
        reactor_size_summary="not_reported",
        reactor_setup_summary=(
            "Upper crucible held 5 g polymer; lower crucible held 1 g "
            "Fe2O3/Al2O3 catalyst; oven had three temperature-control regions."
        ),
        catalyst_loading_mass_g="1",
        temperature_setpoint_C=str(temperature),
        temperature_program_summary=(
            "One-stage polymer cracking and carbon deposition in the vertical oven"
        ),
        holding_time_min="60",
        heating_rate_C_min="not_reported",
        cooling_condition="not_reported",
        pressure_original="not_reported",
        pressure_kPa="",
        carbon_source=carbon_source,
        carbon_source_flow_original="5 g batch charge",
        reducing_gas="not_applicable",
        inert_gas="N2",
        inert_gas_flow_original="40 mNL/min",
        inert_gas_flow_sccm="40",
        cofeed_or_reactive_gas="polymer pyrolysis vapors generated in situ",
        total_flow_original="40 mNL/min N2; pyrolysis-vapor flow not quantified",
        gas_composition_summary=(
            "N2 carrier with in-situ polyolefin cracking products"
            + ("; MIX feed was LDPE:HDPE:PP = 35:25:40 by mass" if mixture else "")
        ),
        process_note=(
            "The 60 min duration is explicit for the 800 C common protocol; "
            "for the 600 C LDPE run it is retained as a same-protocol inference."
            if temperature == 600
            else "Reported 800 C, 1 h CVD protocol."
        ),
    )


def scale_review(run_id: str, source: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="lab_batch",
        scale_level_claimed="potential_waste_upcycling_route",
        scale_evidence_summary=(
            f"One-stage vertical-reactor experiment using 5 g {source} and "
            "1 g catalyst."
        ),
        reactor_capacity_or_throughput="5 g polymer per reported laboratory run",
        continuous_operation_time_h="not_applicable",
        catalyst_lifetime_or_reuse="not_reported",
        batch_stability="not_reported",
        scale_up_issue=(
            "Validate real mixed/dirty plastic waste, heat and gas mass balance, "
            "catalyst recovery, acid consumption and product consistency."
        ),
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="no currency or energy-cost calculation reported",
        cost_driver_summary=(
            "polymer preprocessing, 800 C furnace duty, nitrogen, supported "
            "iron catalyst and hot sulfuric-acid purification"
        ),
        safety_risk=(
            "hot polymer pyrolysis vapors; nanoparticle exposure; 50% sulfuric "
            "acid reflux at 140 C"
        ),
        emission_or_waste=(
            "unquantified pyrolysis gases/liquids and acidic Fe/Al-containing wash"
        ),
        industrial_readiness_assessment=(
            "proof-of-concept with simulated polyolefin waste; real-waste and "
            "scale validation remain necessary"
        ),
        reproduction_value="high for feedstock-comparison experiments",
        reproduction_priority="high",
        recommended_next_action=(
            "Repeat with real PSW and complete carbon, energy, acid and catalyst balances"
        ),
    )


def build(
    metadata: dict[str, Any],
    store: EvidenceStore,
) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "Five author-synthesized carbon-material runs: LDPE at 600 C "
                "and LDPE, HDPE, PP and simulated mixed polyolefins at 800 C; "
                "CNT synthesis, purification, characterization and CWPO results."
            ),
        )
    )
    tables["source_master"][0]["local_file_path"] = (
        f"data/interim/parsed_text/{SOURCE_ID}/full_text.txt"
    )
    tables["source_master"][0]["notes"] += (
        " Main PDF pages 5 and 9 and official supplementary PDF pages 2 and "
        "4 were visually inspected. Commercial CNT, bare-catalyst and "
        "non-catalytic controls are retained only as contextual comparators."
    )

    configs = [
        {
            "code": "LDPE600",
            "label": "CNM-LDPE-600",
            "source": "LDPE",
            "temperature": 600,
            "yield": "20",
            "yield_status": "reported",
            "mass_loss": "approximately 45",
            "diameter": "",
            "walls": "not_applicable; no CNT formed",
            "morphology": (
                "amorphous carbon and crystalline graphitic shell around Fe; "
                "no filamentous CNT structure"
            ),
            "cnt_reported": "carbon nanomaterial; explicitly not a CNT",
            "cnt_confirmed": "not_applicable",
            "bet": "159",
            "pore": "406",
            "tga": "410 and 550 C mass-loss centers; 28 wt.% ash",
            "amorphous": "approximately 5 wt.% low-temperature amorphous carbon",
            "elemental": (
                "CHNS-O wt.%: C 70.6+/-2.1, H 1.77+/-<0.01, "
                "N 0.07+/-<0.01, S 0.12+/-<0.01, O 4.50+/-0.01; "
                "remaining 23.0 wt.%; Fe 9.7+/-0.0 wt.%"
            ),
            "toc": "33",
            "arm": "70",
            "ph": "approximately 3.4",
            "qn": "50% QN abatement in less than 30 min; >90% within 30-60 min",
        },
        {
            "code": "LDPE800",
            "label": "CNT-LDPE-800",
            "source": "LDPE",
            "temperature": 800,
            "yield": "32",
            "yield_status": "reported",
            "mass_loss": "approximately 56",
            "diameter": "32",
            "diameter_range": "32 +/- 5",
            "walls": "25-27",
            "morphology": "straight-walled hollow CNTs",
            "cnt_reported": "CNTs",
            "cnt_confirmed": "MWCNTs",
            "bet": "235",
            "pore": "594",
            "tga": "600 C mass-loss center; 18 wt.% ash",
            "amorphous": "not detected by TGA/TEM",
            "elemental": (
                "CHNS-O wt.%: C 86.2+/-1.1, H 0.32+/-0.04, "
                "N 0.10+/-0.01, S 0.08+/-0.01, O 0.88+/-0.07; "
                "remaining 12.5 wt.%; Fe 11.3+/-0.2 wt.%"
            ),
            "toc": "73",
            "arm": "77",
            "ph": "approximately 2.8",
            "qn": ">80% QN abatement in less than 30 min; >90% within 30-60 min",
        },
        {
            "code": "HDPE800",
            "label": "CNT-HDPE-800",
            "source": "HDPE",
            "temperature": 800,
            "yield": "approximately 28",
            "yield_status": "approximate",
            "mass_loss": "approximately 56",
            "diameter": "29",
            "diameter_range": "29 +/- 1",
            "walls": "25-27",
            "morphology": "straight-walled hollow CNTs",
            "cnt_reported": "CNTs",
            "cnt_confirmed": "MWCNTs",
            "bet": "189",
            "pore": "456",
            "tga": "598 C mass-loss center; 20 wt.% ash",
            "amorphous": "not detected by TGA/TEM",
            "elemental": (
                "CHNS-O wt.%: C 85.3+/-0.5, H 0.27+/-0.02, "
                "N 0.09+/-<0.01, S 0.14+/-0.01, O 0.83+/-0.03; "
                "remaining 13.4 wt.%; Fe 14.0+/-0.7 wt.%"
            ),
            "toc": "49",
            "arm": "79",
            "ph": "approximately 2.9",
            "qn": ">80% QN abatement in less than 30 min; >90% within 30-60 min",
        },
        {
            "code": "PP800",
            "label": "CNT-PP-800",
            "source": "PP",
            "temperature": 800,
            "yield": "approximately 26",
            "yield_status": "approximate",
            "mass_loss": "approximately 60",
            "diameter": "26",
            "diameter_range": "26 +/- 1",
            "walls": "25-27",
            "morphology": "straight-walled hollow CNTs",
            "cnt_reported": "CNTs",
            "cnt_confirmed": "MWCNTs",
            "bet": "242",
            "pore": "595",
            "tga": "600 C mass-loss center; 18 wt.% ash",
            "amorphous": "not detected by TGA/TEM",
            "elemental": (
                "CHNS-O wt.%: C 84.1+/-2.6, H 0.41+/-0.01, "
                "N 0.11+/-<0.01, S 0.18+/-0.03, O 1.18+/-0.01; "
                "remaining 15.9 wt.%; Fe 11.9+/-0.7 wt.%"
            ),
            "toc": "63",
            "arm": "94",
            "ph": "approximately 2.8",
            "qn": ">80% QN abatement in less than 30 min; >90% within 30-60 min",
        },
        {
            "code": "MIX800",
            "label": "CNT-MIX-800",
            "source": "LDPE:HDPE:PP 35:25:40 by mass",
            "temperature": 800,
            "yield": "approximately 29",
            "yield_status": "approximate",
            "mass_loss": "approximately 57",
            "diameter": "33",
            "diameter_range": "33 +/- 3",
            "walls": "25-27",
            "morphology": (
                "straight-walled hollow CNTs with an observed encapsulated "
                "metal particle"
            ),
            "cnt_reported": "CNTs",
            "cnt_confirmed": "MWCNTs",
            "bet": "194",
            "pore": "496",
            "tga": "587 C mass-loss center; 25 wt.% ash",
            "amorphous": "not detected by TGA/TEM",
            "elemental": (
                "CHNS-O wt.%: C 80.5+/-3.6, H 0.34+/-0.03, "
                "N 0.00+/-<0.01, S 0.36+/-0.09, O 1.83+/-<0.01; "
                "remaining 17.0 wt.%; Fe 14.9+/-0.1 wt.%"
            ),
            "toc": "75",
            "arm": "89",
            "ph": "approximately 2.9",
            "qn": ">80% QN abatement in less than 30 min; >90% within 30-60 min",
        },
    ]

    for config in configs:
        run_id = f"{SOURCE_ID}_{config['code']}"
        is_mix = config["code"] == "MIX800"
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                config["code"],
                config["label"],
                (
                    f"5 g {config['source']} over 1 g Fe2O3/Al2O3 at "
                    f"{config['temperature']} C under 40 mNL/min N2; "
                    f"CVD yield {config['yield']} wt.%."
                ),
                "high" if config["yield_status"] == "reported" else "medium",
            )
        )
        tables["catalyst_system"].append(common_catalyst(run_id))
        tables["reactor_process_gas"].append(
            cvd_process(
                run_id,
                config["source"],
                config["temperature"],
                mixture=is_mix,
            )
        )
        product = yield_row(
            run_id,
            primary_yield_metric="carbon_corrected_CVD_solid_yield",
            yield_original=f"{config['yield']} wt.%",
            yield_definition_original=(
                "recovered-material mass times product elemental-carbon "
                "fraction divided by polymer mass times 85.6 wt.% polymer carbon"
            ),
            yield_calculation_method="author Equation (1), catalyst-blank corrected",
            yield_value_standardized=config["yield"].replace("approximately ", ""),
            yield_unit_standardized="percent",
            yield_standardization_note=(
                "Directly retained author value."
                if config["yield_status"] == "reported"
                else "Approximate value visually read from supplementary Figure S3."
            ),
            secondary_result_summary=(
                f"Acid-purification mass loss {config['mass_loss']}%; "
                f"{config['tga']}; total pore volume {config['pore']} mm3/g. "
                f"{config['elemental']}"
            ),
            CNT_type_reported=config["cnt_reported"],
            CNT_type_confirmed=config["cnt_confirmed"],
            product_mixture_summary=(
                "acid-purified carbon product retaining Fe/Al-containing residue"
            ),
            CNT_type_evidence="TEM morphology and TGA/elemental characterization",
            outer_diameter_mean_nm=config["diameter"],
            outer_diameter_range_nm=config.get("diameter_range", ""),
            wall_number_summary=config["walls"],
            morphology=config["morphology"],
            alignment_or_array="not_reported",
            TGA_carbon_content_wt_percent="",
            purity_basis="air-TGA final ash content; not direct CNT purity",
            residue_summary=(
                config["tga"].split("; ")[-1]
                + "; elemental-analysis remaining and Fe values are in "
                "secondary_result_summary"
            ),
            amorphous_carbon_level=config["amorphous"],
            BET_surface_area_product_m2_g=config["bet"],
            characterization_methods=(
                "TEM; XRD; FTIR; TGA/DTG; N2 adsorption; CHNS-O; "
                "atomic absorption; HPLC; UV-Vis; TOC"
            ),
            post_treatment_or_purification=(
                "50% v/v H2SO4 reflux at 140 C for 3 h; water wash; "
                "dry at 60 C for over 12 h"
            ),
            purification_condition=(
                f"reported purification mass loss {config['mass_loss']}%"
            ),
            application_property_summary=(
                "CWPO: pH0 3.0, QN0 100 mg/L, H2O2 6.2 g/L, catalyst "
                f"2.5 g/L, 80 C. {config['qn']}; TOC removal after 24 h "
                f"{config['toc']}%; ARM removal {config['arm']}%; final pH "
                f"{config['ph']}; Fe leaching <0.05 wt.%."
            ),
        )
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(scale_review(run_id, config["source"]))

        for suffix, table, record, fields, span_id, summary, value_status in [
            (
                "CAT_PREP",
                "catalyst_system",
                f"{run_id}_CAT",
                "record_level",
                "SPAN_B908B9B53C38EDCDA2EA",
                "Sol-gel precursor amounts and staged gel/powder preparation.",
                "reported",
            ),
            (
                "CAT_THERMAL_PROCESS",
                "catalyst_system",
                f"{run_id}_CAT",
                "calcination_condition;activation_condition",
                "SPAN_9D8CAF26D06F9FCC2CCB",
                "Nitrogen thermal-treatment temperatures, durations and flow.",
                "reported",
            ),
            (
                "CAT_PHASE",
                "catalyst_system",
                f"{run_id}_CAT",
                "phase_or_state_summary",
                "SPAN_B1CA4A700DA91B995628",
                "Catalyst phase fractions and Fe content.",
                "reported",
            ),
            (
                "PROCESS",
                "reactor_process_gas",
                f"{run_id}_S01",
                "record_level",
                "SPAN_9D8CAF26D06F9FCC2CCB",
                "Vertical-oven setup, charges, temperature, duration and N2 flow.",
                "inferred" if config["temperature"] == 600 else "reported",
            ),
            (
                "YIELD_DEFINITION",
                "yield_quality",
                f"{run_id}_PROD",
                (
                    "primary_yield_metric;yield_definition_original;"
                    "yield_calculation_method"
                ),
                "SPAN_6A119880FE9F586EE80B",
                "Carbon-corrected yield equation, blank and purification method.",
                "reported",
            ),
            (
                "MORPHOLOGY",
                "yield_quality",
                f"{run_id}_PROD",
                (
                    "CNT_type_reported;CNT_type_confirmed;outer_diameter_mean_nm;"
                    "outer_diameter_range_nm;wall_number_summary;morphology"
                ),
                "SPAN_B2142FA8328EE329518A",
                "TEM-based morphology, wall number and sample-specific diameters.",
                "reported",
            ),
            (
                "BET",
                "yield_quality",
                f"{run_id}_PROD",
                ("BET_surface_area_product_m2_g;secondary_result_summary"),
                "SPAN_6E661E4FE7FBC520DE59",
                "Table 1 sample-specific BET area and total pore volume.",
                "reported",
            ),
            (
                "ELEMENTAL",
                "yield_quality",
                f"{run_id}_PROD",
                "secondary_result_summary;residue_summary",
                "SPAN_F819FC94D03960F0EE27",
                "Table 2 CHNS-O, remaining mass and Fe content.",
                "reported",
            ),
            (
                "CWPO_METHOD",
                "yield_quality",
                f"{run_id}_PROD",
                "application_property_summary",
                "SPAN_8D2F6183B471697387B6",
                "CWPO QN, pH, temperature, peroxide and catalyst conditions.",
                "reported",
            ),
            (
                "CWPO_QN",
                "yield_quality",
                f"{run_id}_PROD",
                "application_property_summary",
                "SPAN_691F79A3702C590F1BE5",
                "QN-abatement timing and the 600 C sample exception.",
                "reported",
            ),
            (
                "CWPO_CONTEXT",
                "yield_quality",
                f"{run_id}_PROD",
                "application_property_summary",
                "SPAN_D0A35097AB79F9B7ADD1",
                "TOC, final-pH and ARM-removal discussion.",
                "reported",
            ),
            (
                "LEACHING",
                "yield_quality",
                f"{run_id}_PROD",
                "application_property_summary",
                "SPAN_35FB5467F47F74B9BA15",
                "Iron leaching below 0.05 wt.% for all catalysts.",
                "reported",
            ),
            (
                "COST",
                "cost_scale_review",
                run_id,
                "record_level",
                "SPAN_1036106673E1F28C7ED7",
                "One-stage proof-of-concept and need for real-waste validation.",
                "review_assessment",
            ),
        ]:
            append_evidence(
                tables,
                store,
                run_id,
                suffix,
                table,
                record,
                fields,
                span_id,
                summary,
                value_status,
            )

        catalyst_texture = evidence_row(
            store,
            SOURCE_ID,
            f"EVD_{run_id}_CAT_TEXTURE",
            run_id,
            "catalyst_system",
            f"{run_id}_CAT",
            "BET_surface_area_m2_g;pore_volume_cm3_g",
            "SPAN_6E661E4FE7FBC520DE59",
            "Table 1 catalyst BET area and standardized pore-volume conversion.",
        )
        catalyst_texture.update(
            {
                "evidence_type": "reported_value_with_unit_standardization",
                "evidence_text": (
                    "Table 1 reports Fe2O3/Al2O3 BET surface area 98 m2/g "
                    "and total pore volume 273 mm3/g; 273 mm3/g equals "
                    "0.273 cm3/g."
                ),
                "evidence_summary": (
                    "Catalyst texture values are retained, with pore volume "
                    "converted from mm3/g to cm3/g."
                ),
                "notes": "Unit conversion only; no scientific-value conversion.",
            }
        )
        tables["evidence_index"].append(catalyst_texture)

        append_pdf_evidence(
            tables,
            store,
            run_id,
            "FIG_S3",
            (
                "yield_original;yield_value_standardized;secondary_result_summary;"
                "purification_condition"
            ),
            span_id="SPAN_E19EF344AA2D5DD4CFBB",
            page=2,
            evidence_text=(
                f"Figure S3 black yield bar for {config['label']}: "
                f"{config['yield']} wt.%; orange purification mass-loss bar: "
                f"{config['mass_loss']}%."
            ),
            summary=(
                "Supplementary Figure S3 supports the sample-specific CVD "
                "yield and purification mass loss."
            ),
            supplement=True,
            value_status=config["yield_status"],
        )
        append_pdf_evidence(
            tables,
            store,
            run_id,
            "FIG3_TGA",
            (
                "TGA_carbon_content_wt_percent;secondary_result_summary;"
                "residue_summary;amorphous_carbon_level"
            ),
            span_id="SPAN_F3FC3FB4C2369F1A6212",
            page=5,
            evidence_text=(
                f"Figure 3 panel for {config['label']} reports {config['tga']}."
            ),
            summary="Main Figure 3 supports sample-specific TGA/DTG values.",
        )
        append_pdf_evidence(
            tables,
            store,
            run_id,
            "FIG6_TOC",
            "application_property_summary",
            span_id="SPAN_5A9CDA0F078E81083197",
            page=9,
            evidence_text=(
                f"Figure 6 printed bar label for {config['label']}: "
                f"{config['toc']}% TOC removal after 24 h."
            ),
            summary="Main Figure 6 supports the sample-specific TOC removal.",
        )
        append_pdf_evidence(
            tables,
            store,
            run_id,
            "FIG_S5",
            "application_property_summary",
            span_id="SPAN_D0A35097AB79F9B7ADD1",
            page=4,
            evidence_text=(
                f"Figure S5 for {config['label']}: final pH {config['ph']} "
                f"(visually read) and printed ARM-removal label {config['arm']}%."
            ),
            summary=(
                "Supplementary Figure S5 supports final pH and sample-specific "
                "ARM removal."
            ),
            supplement=True,
            value_status="approximate",
        )

    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_RATIO_001",
                SOURCE_ID,
                f"{SOURCE_ID}_LDPE800",
                "source_internal_inconsistency",
                "catalyst_system",
                f"{SOURCE_ID}_LDPE800_CAT",
                "metal_ratio_original",
                (
                    "The article states M+2/M+3 = 2, while the reported reagent "
                    "amounts are 10 mmol FeCl2 and 20 mmol FeCl3 (ratio 0.5)."
                ),
                f"EVD_{SOURCE_ID}_LDPE800_CAT_PREP",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_FIGURE_YIELD_001",
                SOURCE_ID,
                f"{SOURCE_ID}_HDPE800",
                "figure_value_transcription",
                "yield_quality",
                f"{SOURCE_ID}_HDPE800_PROD",
                "yield_original",
                (
                    "HDPE, PP and MIX yields and all purification mass losses "
                    "lack printed labels and were visually read from Figure S3; "
                    "treat them as approximate."
                ),
                (
                    f"EVD_{SOURCE_ID}_HDPE800_FIG_S3;"
                    f"EVD_{SOURCE_ID}_PP800_FIG_S3;"
                    f"EVD_{SOURCE_ID}_MIX800_FIG_S3"
                ),
                "medium",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PH_001",
                SOURCE_ID,
                f"{SOURCE_ID}_LDPE600",
                "figure_value_transcription",
                "yield_quality",
                f"{SOURCE_ID}_LDPE600_PROD",
                "application_property_summary",
                (
                    "Final-pH bars in Figure S5b are unlabelled; the five "
                    "sample-specific pH values are approximate visual readings."
                ),
                (
                    f"EVD_{SOURCE_ID}_LDPE600_FIG_S5;"
                    f"EVD_{SOURCE_ID}_LDPE800_FIG_S5;"
                    f"EVD_{SOURCE_ID}_HDPE800_FIG_S5;"
                    f"EVD_{SOURCE_ID}_PP800_FIG_S5;"
                    f"EVD_{SOURCE_ID}_MIX800_FIG_S5"
                ),
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_600_DURATION_001",
                SOURCE_ID,
                f"{SOURCE_ID}_LDPE600",
                "same_protocol_inference",
                "reactor_process_gas",
                f"{SOURCE_ID}_LDPE600_S01",
                "holding_time_min",
                (
                    "The 600 C sentence repeats temperature and N2 flow but not "
                    "duration; 60 min is inferred from the immediately preceding "
                    "common 800 C protocol."
                ),
                f"EVD_{SOURCE_ID}_LDPE600_PROCESS",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_TGA_ELEMENTAL_001",
                SOURCE_ID,
                f"{SOURCE_ID}_MIX800",
                "measurement_basis_difference",
                "yield_quality",
                f"{SOURCE_ID}_MIX800_PROD",
                "residue_summary",
                (
                    "The source states that elemental-analysis remaining mass "
                    "does not match TGA ash because metallic phases oxidize "
                    "during air TGA; values must not be treated as equivalent."
                ),
                (f"EVD_{SOURCE_ID}_MIX800_ELEMENTAL;EVD_{SOURCE_ID}_MIX800_FIG3_TGA"),
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_SCALE_001",
                SOURCE_ID,
                f"{SOURCE_ID}_MIX800",
                "scale_evidence_limit",
                "cost_scale_review",
                f"{SOURCE_ID}_MIX800",
                "industrial_readiness_assessment",
                (
                    "The MIX feed simulates municipal polyolefin composition, "
                    "but the study used clean model polymers rather than real "
                    "mixed/dirty plastic waste."
                ),
                f"EVD_{SOURCE_ID}_MIX800_COST",
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
