#!/usr/bin/env python3
"""Source-specific builders for supervised B-class redo shard 00.

Every source function is authored from the local paper and immutable parsed
evidence.  The module intentionally contains no generic fact templates.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from scripts.extraction.b_class_redo_common import (
    REDO_ID,
    REDO_ROOT,
    SourceContext,
    catalyst_row,
    cost_row,
    evidence_row,
    issue_row,
    load_available_sources,
    process_row,
    source_master_row,
    source_run_row,
    write_package,
    yield_row,
)


SHARD = 0
SHARD_ROOT = REDO_ROOT / "shards" / f"{SHARD:02d}"
MANIFEST = SHARD_ROOT / "shard_manifest.csv"


def contexts() -> dict[str, SourceContext]:
    return {
        item.source_id: item
        for item in load_available_sources()
        if item.shard == SHARD
    }


def update_manifest(
    source_id: str,
    status: str,
    *,
    package_path: str = "",
    blocking_reason: str = "",
) -> None:
    with MANIFEST.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    found = False
    for item in rows:
        if item["source_id"] != source_id:
            continue
        item["redo_status"] = status
        item["package_path"] = package_path
        item["blocking_reason"] = blocking_reason
        found = True
    if not found:
        raise KeyError(f"Source is not in shard manifest: {source_id}")
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_review(package: Path, payload: dict[str, Any]) -> None:
    (package / "source_review.json").write_text(
        json.dumps(
            {
                "redo_id": REDO_ID,
                "protocol": "docs/b_class_redo_protocol_v1.md",
                "old_b_facts_used": False,
                **payload,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def mark_non_extractable(
    context: SourceContext,
    *,
    reason: str,
    evidence_sections: list[str],
    pdf_pages_checked: list[int],
) -> Path:
    package = SHARD_ROOT / context.source_id
    package.mkdir(parents=True, exist_ok=True)
    is_pdf = context.local_source_path.lower().endswith(".pdf")
    write_review(
        package,
        {
            "source_id": context.source_id,
            "review_status": "non_extractable",
            "reviewer": "Codex",
            "source_identity_checked": True,
            "disposition": "non_extractable",
            "disposition_reason": reason,
            "evidence_sections_checked": evidence_sections,
            "campaign_reconciliation": {
                "result_linked_campaigns_in_paper": 0,
                "extracted_runs": 0,
                "negative_runs_preserved": 0,
            },
            "pdf_visual_review": (
                {
                    "completed": True,
                    "pages_checked": pdf_pages_checked,
                    "objects_checked": ["article abstract", "main text", "conclusions"],
                }
                if is_pdf
                else {
                    "completed": False,
                    "pages_checked": [],
                    "not_applicable_reason": "Local source is HTML rather than PDF.",
                }
            ),
            "html_source_review": (
                {"completed": True, "sections_checked": evidence_sections}
                if not is_pdf
                else {"completed": False, "not_applicable_reason": "Local source is PDF."}
            ),
        },
    )
    update_manifest(
        context.source_id,
        "non_extractable",
        package_path=package.relative_to(REDO_ROOT).as_posix(),
        blocking_reason=reason,
    )
    return package


def build_lit_004fae25(context: SourceContext) -> Path:
    """Smagulova et al. 2019, polymer-waste three-zone CVD."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    runs = [
        {
            "code": "NICO_PYRO400",
            "label": "Ni/Co-cenosphere, polyethylene pyrolysis at 400 C",
            "summary": (
                "Three-zone polyethylene-waste CVD with mixed Ni/Co nitrate "
                "on cenospheres; the 400 C feed-pyrolysis condition produced "
                "amorphous carbon and no observed nanotubes."
            ),
            "metals": "Ni; Co",
            "catalyst_label": "mixed Ni/Co nitrate-impregnated cenospheres",
            "precursor": "aqueous nickel nitrate and cobalt nitrate mixture, 100 g/L",
            "pyrolysis_C": "400",
            "outcome": "amorphous carbon; 400 C was insufficient for nanotube synthesis",
            "cnt_type": "not_reported",
            "mixture": "amorphous carbon material on cenosphere surface",
            "diameter": "",
            "morphology": "amorphous structure coating cenospheres",
            "amorphous": "dominant",
            "result_span": "SPAN_06EA1D53C0FC99E7DE1B",
            "temperature_span": "SPAN_06EA1D53C0FC99E7DE1B",
            "result_summary": "SEM shows amorphous carbon on Ni/Co cenospheres at 400 C and no nanotubes.",
        },
        {
            "code": "CO_PYRO450",
            "label": "Co-cenosphere, polyethylene pyrolysis at 450 C",
            "summary": (
                "Three-zone polyethylene-waste CVD with cobalt nitrate on "
                "cenospheres; at 450 C feed pyrolysis the product remained "
                "mainly amorphous with a small number of 60-70 nm CNTs."
            ),
            "metals": "Co",
            "catalyst_label": "cobalt nitrate-impregnated cenospheres",
            "precursor": "aqueous cobalt nitrate, 100 g/L",
            "pyrolysis_C": "450",
            "outcome": "small number of CNTs in a mainly amorphous carbon product",
            "cnt_type": "carbon nanotubes; wall number not reported",
            "mixture": "mainly amorphous carbon with a small number of CNTs",
            "diameter": "60-70",
            "morphology": "carbon-coated cenospheres with sparse CNTs",
            "amorphous": "dominant",
            "result_span": "SPAN_06EA1D53C0FC99E7DE1B",
            "temperature_span": "SPAN_06EA1D53C0FC99E7DE1B",
            "result_summary": "SEM at 450 C on Co cenospheres shows mainly amorphous carbon and sparse 60-70 nm CNTs.",
        },
        {
            "code": "NICO_PYRO450",
            "label": "Ni/Co-cenosphere, polyethylene pyrolysis at 450 C",
            "summary": (
                "Best reported three-zone polyethylene-waste CVD condition: "
                "mixed Ni/Co nitrate on cenospheres with 450 C feed pyrolysis, "
                "forming 40-100 nm CNTs with minor amorphous inclusions."
            ),
            "metals": "Ni; Co",
            "catalyst_label": "mixed Ni/Co nitrate-impregnated cenospheres",
            "precursor": "aqueous nickel nitrate and cobalt nitrate mixture, 100 g/L",
            "pyrolysis_C": "450",
            "outcome": "CNT-coated cenospheres; best reported catalytic activity",
            "cnt_type": "carbon nanotubes; wall number not reported",
            "mixture": "CNTs with small amorphous inclusions and approximately 300 nm carbon fibres",
            "diameter": "40-100",
            "morphology": "CNT coating on cenosphere surface; separate one-dimensional fibres about 300 nm",
            "amorphous": "minor inclusions",
            "result_span": "SPAN_54A686627B56E31002E0",
            "temperature_span": "SPAN_06EA1D53C0FC99E7DE1B",
            "result_summary": "SEM shows 40-100 nm CNTs, minor amorphous material, and separate approximately 300 nm fibres.",
        },
    ]

    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [
            source_master_row(
                context,
                "Experimental methods and all three result-linked catalyst/pyrolysis campaigns in Figures 2-4.",
            )
        ],
        "source_run": [],
        "catalyst_system": [],
        "reactor_process_gas": [],
        "yield_quality": [],
        "cost_scale_review": [],
        "evidence_index": [],
        "review_issue_log": [],
    }

    scope_evidence_id = f"{source_id}_EV_SCOPE"
    scope_issue_id = f"{source_id}_ISSUE_UNLINKED_NI"
    tables["evidence_index"].append(
        evidence_row(
            source_id,
            scope_evidence_id,
            "not_applicable",
            "source_master",
            source_id,
            "source_section_scope",
            "SPAN_5DA851F670109BE760A7",
            "The methods list Ni, Co, and mixed Ni/Co preparations, while the result section links outcomes only to three campaigns.",
            linked_issue_id=scope_issue_id,
        )
    )
    tables["review_issue_log"].append(
        issue_row(
            scope_issue_id,
            source_id,
            "not_applicable",
            "reported_recipe_without_linked_result",
            "source_master",
            source_id,
            "source_section_scope",
            "A nickel-only catalyst preparation is mentioned, but no nickel-only result is linked in the paper; no nickel-only run was fabricated.",
            evidence_ids=scope_evidence_id,
            severity="low",
        )
    )

    for index, item in enumerate(runs, start=1):
        run = source_run_row(
            source_id,
            item["code"],
            item["label"],
            item["summary"],
        )
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label=item["catalyst_label"],
            active_metals=item["metals"],
            support_material=(
                "cenospheres: hollow 100-500 micrometre aluminosilicate spheres"
            ),
            metal_ratio_original=(
                "nitrate solution concentration 100 g/L; Ni:Co ratio not reported"
                if item["metals"] == "Ni; Co"
                else "cobalt nitrate solution concentration 100 g/L"
            ),
            precursor_summary=item["precursor"],
            preparation_method="aqueous impregnation",
            preparation_detail="10 g cenospheres impregnated with the nitrate solution",
            drying_condition="70 C for 2-3 h until moisture removal",
            phase_or_state_summary=(
                "nickel/cobalt nitrates decompose during synthesis to form Ni/Co"
                if item["metals"] == "Ni; Co"
                else "cobalt nitrate decomposes during synthesis to form Co"
            ),
            notes="Cenosphere dimensions are support dimensions, not catalyst-particle size.",
        )
        stages = [
            process_row(
                run_id,
                1,
                "polyethylene_waste_pyrolysis",
                reactor_type="three-zone quartz reactor",
                reactor_size_summary="6 cm inner diameter; 120.7 cm length",
                reactor_setup_summary="zone 1 contains a quartz cuvette with compacted polyethylene waste",
                temperature_setpoint_C=item["pyrolysis_C"],
                carbon_source="cleaned and compacted polyethylene bag waste",
                carbon_source_flow_original="4 g charge",
                inert_gas="N2 transport through the three-zone reactor",
                inert_gas_flow_original="540 cm3/min",
                temperature_program_summary="zone 1 feed-pyrolysis temperature",
                process_note="No reaction pressure was reported.",
            ),
            process_row(
                run_id,
                2,
                "secondary_hot_zone",
                reactor_type="three-zone quartz reactor",
                reactor_size_summary="6 cm inner diameter; 120.7 cm length",
                temperature_setpoint_C="700",
                inert_gas="N2 transport gas",
                inert_gas_flow_original="540 cm3/min",
                process_note="Intermediate hot zone; pressure not reported.",
            ),
            process_row(
                run_id,
                3,
                "catalytic_deposition",
                reactor_type="three-zone quartz reactor",
                reactor_size_summary="6 cm inner diameter; 120.7 cm length",
                reactor_setup_summary="zone 3 contains a quartz cuvette with the supported catalyst",
                catalyst_loading_mass_g="1-2",
                temperature_setpoint_C="800",
                holding_time_min="30",
                carbon_source="products of polyethylene thermal decomposition",
                inert_gas="N2 transport gas",
                inert_gas_flow_original="540 cm3/min",
                process_note="Catalytic deposition zone; pressure not reported.",
            ),
        ]
        product = yield_row(
            run_id,
            primary_yield_metric="qualitative carbon-product outcome",
            yield_original=item["outcome"],
            yield_definition_original="SEM-observed product identity and relative abundance; no mass yield reported",
            yield_standardization_note="No quantitative yield reported and no cross-definition conversion performed.",
            secondary_result_summary=item["outcome"],
            CNT_type_reported=item["cnt_type"],
            CNT_type_confirmed="not_reported",
            product_mixture_summary=item["mixture"],
            CNT_type_evidence="SEM morphology only; wall number not established",
            outer_diameter_range_nm=item["diameter"],
            morphology=item["morphology"],
            amorphous_carbon_level=item["amorphous"],
            characterization_methods="SEM",
            notes="The approximately 300 nm fibres in the Ni/Co 450 C product are not entered as CNT diameter.",
        )
        cost = cost_row(
            run_id,
            scale_level_demonstrated="not_reported",
            scale_level_claimed="not_reported",
            scale_evidence_summary="Reported batch charge sizes only; scale class not assigned.",
            reactor_capacity_or_throughput="4 g polyethylene charge; 1-2 g catalyst charge per experiment",
            quantitative_cost_reported="not_reported",
            quantitative_cost_summary="not_reported",
            review_note="No industrial-readiness score inferred from the conference paper.",
        )
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].extend(stages)
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)

        ev_prefix = f"{source_id}_EV_{index:02d}"
        tables["evidence_index"].append(
            evidence_row(
                source_id,
                f"{ev_prefix}_CAT",
                run_id,
                "catalyst_system",
                catalyst["catalyst_id"],
                "catalyst_label;active_metals;support_material;metal_ratio_original;precursor_summary;preparation_method;preparation_detail;drying_condition;phase_or_state_summary",
                "SPAN_5DA851F670109BE760A7",
                "Cenosphere composition/dimensions and nitrate impregnation/drying method.",
            )
        )
        for stage in stages:
            stage_code = stage["process_stage_id"].rsplit("_", 1)[-1]
            tables["evidence_index"].append(
                evidence_row(
                    source_id,
                    f"{ev_prefix}_{stage_code}_APP",
                    run_id,
                    "reactor_process_gas",
                    stage["process_stage_id"],
                    "stage_type;reactor_type;reactor_size_summary",
                    "SPAN_DFC671428FF337A466CD",
                    "The experimental section identifies the three-zone quartz reactor and its 6 cm by 120.7 cm dimensions.",
                )
            )
            if stage_code == "S01":
                tables["evidence_index"].extend(
                    [
                        evidence_row(
                            source_id,
                            f"{ev_prefix}_{stage_code}_FEED",
                            run_id,
                            "reactor_process_gas",
                            stage["process_stage_id"],
                            "reactor_setup_summary;carbon_source;carbon_source_flow_original;temperature_program_summary",
                            "SPAN_47B8457A36D358A7BEEA",
                            "Zone 1 contains a 4 g polyethylene charge and is operated over the reported 400-450 C study range.",
                        ),
                        evidence_row(
                            source_id,
                            f"{ev_prefix}_{stage_code}_TEMP",
                            run_id,
                            "reactor_process_gas",
                            stage["process_stage_id"],
                            "temperature_setpoint_C",
                            item["temperature_span"],
                            "The result figure/text links this catalyst campaign to the exact polyethylene decomposition temperature.",
                        ),
                        evidence_row(
                            source_id,
                            f"{ev_prefix}_{stage_code}_GAS",
                            run_id,
                            "reactor_process_gas",
                            stage["process_stage_id"],
                            "inert_gas;inert_gas_flow_original",
                            "SPAN_6FB7A31C8488C3FEF9F2",
                            "Nitrogen at 540 cm3/min is the reported transport gas for synthesis.",
                        ),
                    ]
                )
            elif stage_code == "S02":
                tables["evidence_index"].append(
                    evidence_row(
                        source_id,
                        f"{ev_prefix}_{stage_code}_COND",
                        run_id,
                        "reactor_process_gas",
                        stage["process_stage_id"],
                        "temperature_setpoint_C;inert_gas;inert_gas_flow_original",
                        "SPAN_6FB7A31C8488C3FEF9F2",
                        "The second zone is 700 C with nitrogen transport at 540 cm3/min.",
                    )
                )
            else:
                tables["evidence_index"].extend(
                    [
                        evidence_row(
                            source_id,
                            f"{ev_prefix}_{stage_code}_COND",
                            run_id,
                            "reactor_process_gas",
                            stage["process_stage_id"],
                            "reactor_setup_summary;catalyst_loading_mass_g;temperature_setpoint_C;holding_time_min;inert_gas;inert_gas_flow_original",
                            "SPAN_6FB7A31C8488C3FEF9F2",
                            "The third-zone catalyst charge is 1-2 g at 800 C; nitrogen flow is 540 cm3/min and synthesis time is 30 min.",
                        ),
                        evidence_row(
                            source_id,
                            f"{ev_prefix}_{stage_code}_CARBON",
                            run_id,
                            "reactor_process_gas",
                            stage["process_stage_id"],
                            "carbon_source",
                            "SPAN_47B8457A36D358A7BEEA",
                            "CNT synthesis uses products generated by thermal destruction of the polyethylene charge.",
                        ),
                    ]
                )
        tables["evidence_index"].append(
            evidence_row(
                source_id,
                f"{ev_prefix}_PROD",
                run_id,
                "yield_quality",
                product["product_id"],
                "primary_yield_metric;yield_original;yield_definition_original;secondary_result_summary;CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;outer_diameter_range_nm;morphology;amorphous_carbon_level;characterization_methods",
                item["result_span"],
                item["result_summary"],
            )
        )
        tables["evidence_index"].append(
            evidence_row(
                source_id,
                f"{ev_prefix}_SCALE",
                run_id,
                "cost_scale_review",
                run_id,
                "scale_level_demonstrated;scale_level_claimed;scale_evidence_summary;reactor_capacity_or_throughput;quantitative_cost_reported;quantitative_cost_summary;review_note",
                "SPAN_6FB7A31C8488C3FEF9F2",
                "Only the experimental charge sizes are reported; no scale or cost claim is made.",
            )
        )

    write_package(package, tables)
    write_review(
        package,
        {
            "source_id": source_id,
            "review_status": "extracted_needs_supervisory_review",
            "reviewer": "Codex",
            "source_identity_checked": True,
            "campaign_reconciliation": {
                "result_linked_campaigns_in_paper": 3,
                "extracted_runs": 3,
                "negative_runs_preserved": 1,
                "unlinked_recipe_note": "Nickel-only catalyst preparation is mentioned but has no linked result; it was not emitted as a run."
            },
            "pdf_visual_review": {
                "completed": True,
                "pages_checked": [1, 2, 3, 4],
                "objects_checked": ["Figure 1", "Figure 2", "Figure 3", "Figure 4"]
            },
            "pressure_policy_check": "No pressure value emitted because the paper does not report one.",
            "cross_run_inheritance_check": "Each product outcome and CNT diameter is restricted to its figure-linked catalyst/temperature run.",
        },
    )
    update_manifest(
        source_id,
        "extracted_needs_supervisory_review",
        package_path=package.relative_to(REDO_ROOT).as_posix(),
    )
    return package


def build_lit_1e15bc80(context: SourceContext) -> Path:
    """Zhang et al. 2015, water-assisted VACNT membrane."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    run = source_run_row(
        source_id,
        "WACVD_MEMBRANE",
        "815 C water-assisted VACNT growth and rolled membrane",
        (
            "Fe(1.4 nm)/Al2O3(40 nm)/Si water-assisted ethylene CVD at "
            "815 C for 10 min, followed by mechanical rolling, ultrasonic "
            "release, and vacuum drying to form a dense aligned CNT membrane."
        ),
    )
    run_id = run["run_id"]
    catalyst = catalyst_row(
        run_id,
        catalyst_label="Fe(1.4 nm)/Al2O3(40 nm)/Si catalyst stack",
        active_metals="Fe",
        support_material="40 nm Al2O3 on Si",
        metal_ratio_original="Fe film thickness 1.4 nm; Al2O3 layer thickness 40 nm",
        precursor_summary="not_reported",
        preparation_method="not_reported",
        notes="Reported layer thicknesses are not treated as catalyst-particle diameters.",
    )
    growth = process_row(
        run_id,
        1,
        "water_assisted_ethylene_CVD",
        reactor_type="not_reported",
        reactor_setup_summary="water-assisted CVD; a portion of Ar passes through a water bubbler",
        temperature_setpoint_C="815",
        holding_time_min="10",
        carbon_source="high-purity ethylene (99.99%)",
        carbon_source_flow_original="100 sccm",
        carbon_source_flow_sccm="100",
        reducing_gas="H2 (99.999%)",
        inert_gas="Ar (99.999%)",
        cofeed_or_reactive_gas="water vapor, 100-200 ppm",
        total_flow_original="650 sccm Ar/H2 carrier gas",
        total_flow_sccm="650",
        process_note="Individual Ar and H2 flows and reaction pressure were not reported.",
    )
    membrane = process_row(
        run_id,
        2,
        "mechanical_membrane_fabrication",
        reactor_type="not_applicable",
        reactor_setup_summary="glass-slide-guided rolling/shear pressing of the as-grown VACNT array",
        temperature_setpoint_C="60",
        holding_time_min="240",
        cooling_condition="vacuum drying at 60 C",
        cofeed_or_reactive_gas="deionized water during ultrasonic release from the Si substrate",
        process_note="After rolling, the aligned layer was ultrasonically peeled in DI water and vacuum-dried for 4 h.",
    )
    product = yield_row(
        run_id,
        primary_yield_metric="VACNT array height",
        yield_original="as-grown VACNT array about 1 mm tall",
        yield_definition_original="cross-sectional SEM array height; not a mass yield",
        yield_standardization_note="Array height retained as reported; no conversion to mass yield.",
        secondary_result_summary="rolled freestanding membrane pore size 10 nm and thickness approximately 120 micrometre",
        CNT_type_reported="few-walled CNT; typical nanotube about 3 graphitic walls",
        CNT_type_confirmed="few-walled CNT",
        product_mixture_summary="high-purity CNT membrane; no metal catalyst observed by TEM",
        CNT_type_evidence="HRTEM of a representative nanotube shows about 3 graphitic walls",
        inner_diameter_mean_nm="5",
        wall_number_summary="about 3 graphitic walls for the representative CNT",
        length_summary="as-grown vertically aligned array about 1 mm tall; rolled membrane about 120 micrometre thick",
        morphology="dense freestanding CNT membrane produced by rolling a vertically aligned forest",
        alignment_or_array="vertically aligned as grown; remains aligned after directional rolling",
        Raman_ratio_type="I_G/I_D",
        Raman_ratio_value="12.3",
        purity_basis="TEM qualitative observation: no metal catalyst observed",
        characterization_methods="SEM; HRTEM; Raman spectroscopy",
        post_treatment_or_purification="mechanical rolling; ultrasonic release in DI water; vacuum drying",
        purification_condition="vacuum drying at 60 C for 4 h",
        application_property_summary=(
            "Membrane pore size 10 nm, thickness ~120 micrometre, CNT areal density ~1e11 cm-2, "
            "area 7.065e-2 cm2. Liquid permeability at 1 atm (ml min-1 cm-2): "
            "water 3.23 +/- 0.05, ethanol 0.507, hexane 1.00, kerosene 0.10."
        ),
        notes=(
            "The body text calls the representative 5 nm value a CNT diameter, "
            "whereas the Figure 1 caption calls it an inner diameter; the value is "
            "stored as inner diameter and the ambiguity is logged."
        ),
    )
    cost = cost_row(
        run_id,
        scale_level_demonstrated="not_reported",
        scale_level_claimed="not_reported",
        scale_evidence_summary="Individual Si-substrate array and 7.065e-2 cm2 membrane test specimen; no production scale claimed.",
        quantitative_cost_reported="not_reported",
        quantitative_cost_summary="not_reported",
        review_note="Membrane specimen size is not interpreted as reactor scale or throughput.",
    )
    issue_id = f"{source_id}_ISSUE_DIAMETER_BASIS"
    ev_cat = f"{source_id}_EV_CAT"
    ev_growth_main = f"{source_id}_EV_GROWTH_MAIN"
    ev_growth_water = f"{source_id}_EV_GROWTH_WATER"
    ev_membrane_main = f"{source_id}_EV_MEMBRANE_MAIN"
    ev_membrane_time = f"{source_id}_EV_MEMBRANE_TIME"
    ev_product_structure = f"{source_id}_EV_PRODUCT_STRUCTURE"
    ev_product_figure = f"{source_id}_EV_PRODUCT_FIGURE"
    ev_product_raman = f"{source_id}_EV_PRODUCT_RAMAN"
    ev_product_membrane = f"{source_id}_EV_PRODUCT_MEMBRANE"
    ev_product_transport = f"{source_id}_EV_PRODUCT_TRANSPORT"
    ev_scale = f"{source_id}_EV_SCALE"
    evidence = [
        evidence_row(
            source_id,
            ev_cat,
            run_id,
            "catalyst_system",
            catalyst["catalyst_id"],
            "catalyst_label;active_metals;support_material;metal_ratio_original;precursor_summary;preparation_method",
            "SPAN_1DEA67D0F6963C33DD13",
            "The methods specify the Fe(1.4 nm)/Al2O3(40 nm)/Si catalyst stack.",
        ),
        evidence_row(
            source_id,
            ev_growth_main,
            run_id,
            "reactor_process_gas",
            growth["process_stage_id"],
            "stage_type;reactor_setup_summary;temperature_setpoint_C;carbon_source;carbon_source_flow_original;carbon_source_flow_sccm;reducing_gas;inert_gas;total_flow_original;total_flow_sccm",
            "SPAN_1DEA67D0F6963C33DD13",
            "Water-assisted CVD uses 99.99% ethylene at 100 sccm, Ar/H2 carrier at 650 sccm total, and 815 C.",
        ),
        evidence_row(
            source_id,
            ev_growth_water,
            run_id,
            "reactor_process_gas",
            growth["process_stage_id"],
            "holding_time_min;cofeed_or_reactive_gas",
            "SPAN_6E38354E7712318E0BAB",
            "The typical array is grown under 100-200 ppm water for 10 min.",
        ),
        evidence_row(
            source_id,
            ev_membrane_main,
            run_id,
            "reactor_process_gas",
            membrane["process_stage_id"],
            "stage_type;reactor_setup_summary;temperature_setpoint_C;cooling_condition;cofeed_or_reactive_gas",
            "SPAN_2F043F3587419975AFB0",
            "The rolled membrane is ultrasonically released in DI water and vacuum-dried at 60 C.",
        ),
        evidence_row(
            source_id,
            ev_membrane_time,
            run_id,
            "reactor_process_gas",
            membrane["process_stage_id"],
            "holding_time_min",
            "SPAN_2F043F3587419975AFB0",
            "The paper reports 4 h vacuum drying; 240 min is a unit normalization.",
            value_status="normalized",
        ),
        evidence_row(
            source_id,
            ev_product_structure,
            run_id,
            "yield_quality",
            product["product_id"],
            "CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;inner_diameter_mean_nm;wall_number_summary;morphology;alignment_or_array;purity_basis;characterization_methods",
            "SPAN_1DEA67D0F6963C33DD13",
            "HRTEM reports a representative approximately 5 nm CNT with about 3 walls and no observed metal; SEM shows alignment.",
            linked_issue_id=issue_id,
        ),
        evidence_row(
            source_id,
            ev_product_figure,
            run_id,
            "yield_quality",
            product["product_id"],
            "primary_yield_metric;yield_original;yield_definition_original;secondary_result_summary;inner_diameter_mean_nm;length_summary;morphology;alignment_or_array;post_treatment_or_purification;purification_condition",
            "SPAN_2F043F3587419975AFB0",
            "Figure 1 documents the 1 mm array, representative 5 nm inner diameter, rolling, alignment, and drying.",
            linked_issue_id=issue_id,
        ),
        evidence_row(
            source_id,
            ev_product_raman,
            run_id,
            "yield_quality",
            product["product_id"],
            "Raman_ratio_type;Raman_ratio_value;post_treatment_or_purification",
            "SPAN_6E38354E7712318E0BAB",
            "As-synthesized CNTs have I_G/I_D 12.3; rolling and ultrasonic release are described.",
        ),
        evidence_row(
            source_id,
            ev_product_membrane,
            run_id,
            "yield_quality",
            product["product_id"],
            "secondary_result_summary;length_summary;application_property_summary",
            "SPAN_BB62260092536C69B5CD",
            "Table 1 reports 10 nm pore size, approximately 120 micrometre thickness, about 1e11 cm-2 areal density, and 7.065e-2 cm2 area.",
        ),
        evidence_row(
            source_id,
            ev_product_transport,
            run_id,
            "yield_quality",
            product["product_id"],
            "application_property_summary",
            "SPAN_FE4BD931DF8C78769C10",
            "Table 2 reports liquid permeabilities at 1 atm, including water 3.23 +/- 0.05, ethanol 0.507, hexane 1.00, and kerosene 0.10.",
        ),
        evidence_row(
            source_id,
            ev_scale,
            run_id,
            "cost_scale_review",
            run_id,
            "scale_level_demonstrated;scale_level_claimed;scale_evidence_summary;quantitative_cost_reported;quantitative_cost_summary",
            "SPAN_BB62260092536C69B5CD",
            "The paper reports only a small membrane specimen and makes no production-scale or cost claim.",
            value_status="review_assessment",
        ),
    ]
    issue = issue_row(
        issue_id,
        source_id,
        run_id,
        "ambiguous_diameter_basis",
        "yield_quality",
        product["product_id"],
        "inner_diameter_mean_nm",
        "The results prose calls the representative value a CNT diameter, while the Figure 1 caption calls it an inner diameter; stored as inner diameter with the ambiguity retained.",
        evidence_ids=f"{ev_product_structure};{ev_product_figure}",
        severity="medium",
        conflicting_values="body: diameter about 5 nm; Figure 1 caption: inner diameter about 5 nm",
    )
    tables = {
        "source_master": [
            source_master_row(
                context,
                "Water-assisted VACNT growth, mechanical membrane fabrication, structure characterization, and printed membrane transport parameters.",
            )
        ],
        "source_run": [run],
        "catalyst_system": [catalyst],
        "reactor_process_gas": [growth, membrane],
        "yield_quality": [product],
        "cost_scale_review": [cost],
        "evidence_index": evidence,
        "review_issue_log": [issue],
    }
    write_package(package, tables)
    write_review(
        package,
        {
            "source_id": source_id,
            "review_status": "extracted_needs_supervisory_review",
            "reviewer": "Codex",
            "source_identity_checked": True,
            "campaign_reconciliation": {
                "result_linked_campaigns_in_paper": 1,
                "extracted_runs": 1,
                "negative_runs_preserved": 0,
                "application_tests": "Gas/liquid transport results remain application properties of the single membrane campaign, not synthetic run duplicates.",
            },
            "pdf_visual_review": {
                "completed": True,
                "pages_checked": [2, 3, 6, 7],
                "objects_checked": ["Methods", "Figure 1", "Table 1", "Table 2", "Figure 4"],
            },
            "pressure_policy_check": "Growth pressure is not reported and is left empty; transport-test pressures are not assigned to CVD growth.",
            "cross_run_inheritance_check": "Only one explicitly reported growth campaign is emitted.",
        },
    )
    update_manifest(
        source_id,
        "extracted_needs_supervisory_review",
        package_path=package.relative_to(REDO_ROOT).as_posix(),
    )
    return package


def build_lit_2220a162(context: SourceContext) -> Path:
    """Hamzah et al. 2019, complete flame/HNO3/HAB experimental matrix."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    acid_figure_mm: dict[int, float | None] = {
        15: None,
        30: None,
        45: None,
        60: None,
        75: None,
        90: 0.5,
        105: 1.0,
        120: 1.5,
        135: 2.5,
        150: 3.5,
        165: 4.0,
        180: 3.0,
        195: 2.0,
        210: 0.5,
        225: None,
        240: None,
    }
    hab_figure_mm: dict[int, float | None] = {
        1: None,
        2: None,
        3: None,
        4: 2.0,
        5: 3.0,
        7: None,
        8: None,
        9: None,
        10: None,
    }
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [
            source_master_row(
                context,
                "Experimental apparatus, full 15 s acid-dipping series in Figure 4, full 1-10 mm HAB series in Figure 5, microscopy, and the conflicting abstract/conclusion range statement.",
            )
        ],
        "source_run": [],
        "catalyst_system": [],
        "reactor_process_gas": [],
        "yield_quality": [],
        "cost_scale_review": [],
        "evidence_index": [],
        "review_issue_log": [],
    }

    conflict_issue = f"{source_id}_ISSUE_ACID_WINDOW"
    conflict_results_ev = f"{source_id}_EV_ACID_WINDOW_RESULTS"
    conflict_conclusion_ev = f"{source_id}_EV_ACID_WINDOW_CONCLUSION"
    tables["evidence_index"].extend(
        [
            evidence_row(
                source_id,
                conflict_results_ev,
                "not_applicable",
                "source_master",
                source_id,
                "source_section_scope",
                "SPAN_13398CB945C0EAEBD2A2",
                "The Results section states CNT production from 90 through 210 s and no observable deposit beyond 210 s.",
                linked_issue_id=conflict_issue,
            ),
            evidence_row(
                source_id,
                conflict_conclusion_ev,
                "not_applicable",
                "source_master",
                source_id,
                "source_section_scope",
                "SPAN_2DA783D1F1361BD303B7",
                "The conclusion instead states that CNTs cease only after more than 260 s; the abstract likewise describes 90-260 s as favorable.",
                linked_issue_id=conflict_issue,
            ),
        ]
    )
    tables["review_issue_log"].append(
        issue_row(
            conflict_issue,
            source_id,
            "not_applicable",
            "internal_range_conflict",
            "source_master",
            source_id,
            "source_section_scope",
            "The experimental Results/Figure 4 window (90-210 s) conflicts with the abstract/conclusion wording (90-260 s). Run outcomes follow Results/Figure 4, while both statements remain visible.",
            evidence_ids=f"{conflict_results_ev};{conflict_conclusion_ev}",
            severity="high",
            conflicting_values="Results/Fig. 4: CNT at 90-210 s and none beyond 210 s; abstract/conclusion: favorable through 260 s and none after 260 s",
        )
    )

    def add_common_rows(
        *,
        code: str,
        label: str,
        summary: str,
        acid_s: int,
        hab_mm: int | None,
        exposure_min: int | None,
        outcome: str,
        yield_text: str,
        result_span: str,
        result_status: str,
        cnt_type_reported: str,
        cnt_type_confirmed: str,
        cnt_evidence: str,
        product_extra: dict[str, str] | None = None,
        result_issue: str = "not_applicable",
    ) -> None:
        run = source_run_row(
            source_id,
            code,
            label,
            summary,
            data_type="experimental_condition",
            confidence="medium" if result_issue != "not_applicable" else "high",
        )
        run_id = run["run_id"]
        if acid_s == 0:
            catalyst = catalyst_row(
                run_id,
                catalyst_label="untreated pure nickel catalyst wire",
                active_metals="Ni",
                support_material="self-supported 0.4 mm diameter x 50 mm pure nickel wire",
                preparation_method="acetone/water cleaning; no nitric-acid pretreatment",
                preparation_detail="no nitric-acid dip (0 s)",
                catalyst_particle_size_qualifier="post-flame particles larger than 100 nm",
                phase_or_state_summary="pure nickel wire with oversized nickel particles after flame exposure",
            )
        else:
            catalyst = catalyst_row(
                run_id,
                catalyst_label="nitric-acid-oxidized pure nickel catalyst wire",
                active_metals="Ni",
                support_material="self-supported 0.4 mm diameter x 50 mm pure nickel wire",
                preparation_method="acetone/water cleaning followed by nitric-acid oxidation",
                preparation_modifier="65% laboratory-grade HNO3; fresh 30 mL solution per 10 wires",
                preparation_detail=f"acid-dip duration {acid_s} s",
                phase_or_state_summary=(
                    "nickel oxide nanoparticles identified after flame exposure"
                    if acid_s == 165 and hab_mm == 6
                    else "not_reported"
                ),
            )
        setup = (
            f"impact-flow sampling with catalyst positioned at HAB {hab_mm} mm"
            if hab_mm is not None
            else "impact-flow sampling; HAB for the untreated-wire observation was not reported"
        )
        process = process_row(
            run_id,
            1,
            "methane_diffusion_flame_exposure",
            reactor_type="methane co-flow diffusion-flame burner",
            reactor_material="stainless-steel concentric burner tubes",
            reactor_size_summary="18 mm ID methane tube inside a 24 mm co-flow tube",
            reactor_setup_summary=setup,
            holding_time_min=str(exposure_min) if exposure_min is not None else "",
            pressure_original="atmospheric",
            pressure_kPa="101.325",
            carbon_source="99.9% methane",
            carbon_source_flow_original="0.48 slpm",
            carbon_source_flow_sccm="480",
            cofeed_or_reactive_gas="99.9% nitrogen and 99.9% oxygen",
            cofeed_flow_original="4 slpm total",
            cofeed_flow_sccm="4000",
            gas_composition_summary="N2:O2 = 3:1",
            process_note="Impact-flow wire/mesh sampling; reaction temperature at each HAB was measured but no numerical synthesis temperature was reported.",
        )
        product_values: dict[str, str] = {
            "primary_yield_metric": "CNT-covered growth-region length on catalyst wire",
            "yield_original": yield_text,
            "yield_definition_original": "Dark SEM-confirmed CNT-covered region; sporadic grey edge regions excluded",
            "secondary_result_summary": outcome,
            "CNT_type_reported": cnt_type_reported,
            "CNT_type_confirmed": cnt_type_confirmed,
            "product_mixture_summary": outcome,
            "CNT_type_evidence": cnt_evidence,
            "characterization_methods": "FESEM; EDX; TEM for the optimum sample" if acid_s == 165 and hab_mm == 6 else "FESEM",
        }
        if product_extra:
            product_values.update(product_extra)
        product = yield_row(run_id, **product_values)
        cost = cost_row(
            run_id,
            scale_level_demonstrated="not_reported",
            scale_level_claimed="not_reported",
            quantitative_cost_reported="not_reported",
        )
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].append(process)
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)

        ev = f"{source_id}_EV_{code}"
        cat_common_fields = "catalyst_label;active_metals;support_material;preparation_method"
        tables["evidence_index"].append(
            evidence_row(
                source_id,
                f"{ev}_CAT_COMMON",
                run_id,
                "catalyst_system",
                catalyst["catalyst_id"],
                cat_common_fields,
                "SPAN_1FA45C7BBF7B01225CB5",
                "Pure 0.4 mm x 50 mm nickel wires were solvent-cleaned and used as the catalyst substrate.",
            )
        )
        if acid_s == 0:
            tables["evidence_index"].append(
                evidence_row(
                    source_id,
                    f"{ev}_CAT_ZERO",
                    run_id,
                    "catalyst_system",
                    catalyst["catalyst_id"],
                    "preparation_method;preparation_detail;catalyst_particle_size_qualifier;phase_or_state_summary",
                    "SPAN_F4362747281F8C61E011",
                    "The untreated flame-exposed wire did not form CNTs and had nickel particles larger than 100 nm.",
                )
            )
        else:
            tables["evidence_index"].extend(
                [
                    evidence_row(
                        source_id,
                        f"{ev}_CAT_REAGENT",
                        run_id,
                        "catalyst_system",
                        catalyst["catalyst_id"],
                        "preparation_method;preparation_modifier",
                        "SPAN_1FA45C7BBF7B01225CB5",
                        "The wire treatment used 65% nitric acid with a fresh 30 mL portion per ten wires.",
                    ),
                    evidence_row(
                        source_id,
                        f"{ev}_CAT_TIME",
                        run_id,
                        "catalyst_system",
                        catalyst["catalyst_id"],
                        "preparation_detail",
                        "SPAN_13398CB945C0EAEBD2A2",
                        f"Figure 4 and its 15 s series identify the acid-dip point at {acid_s} s.",
                        value_status="figure_digitized",
                        confidence="medium",
                        linked_issue_id=result_issue,
                    ),
                ]
            )
            if catalyst["phase_or_state_summary"] != "not_reported":
                tables["evidence_index"].append(
                    evidence_row(
                        source_id,
                        f"{ev}_CAT_PHASE",
                        run_id,
                        "catalyst_system",
                        catalyst["catalyst_id"],
                        "phase_or_state_summary",
                        "SPAN_DB04921B74A7A02003C5",
                        "EDX identifies the end-cap catalyst nanoparticles of the optimum sample as nickel oxides.",
                    )
                )
        tables["evidence_index"].extend(
            [
                evidence_row(
                    source_id,
                    f"{ev}_PROC_BURNER",
                    run_id,
                    "reactor_process_gas",
                    process["process_stage_id"],
                    "stage_type;reactor_type;reactor_material;reactor_size_summary;carbon_source;carbon_source_flow_original;cofeed_or_reactive_gas;cofeed_flow_original;gas_composition_summary;pressure_original;process_note",
                    "SPAN_203BB77D6C849A7AD03D",
                    "The apparatus uses 0.48 slpm methane in an 18 mm tube, a 4 slpm N2/O2 3:1 co-flow in a 24 mm tube, and atmospheric pressure.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_PROC_CH4_NORM",
                    run_id,
                    "reactor_process_gas",
                    process["process_stage_id"],
                    "carbon_source_flow_sccm",
                    "SPAN_203BB77D6C849A7AD03D",
                    "0.48 standard litre per minute is normalized to 480 sccm.",
                    value_status="normalized",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_PROC_COFLOW_NORM",
                    run_id,
                    "reactor_process_gas",
                    process["process_stage_id"],
                    "cofeed_flow_sccm",
                    "SPAN_203BB77D6C849A7AD03D",
                    "4 standard litres per minute is normalized to 4000 sccm.",
                    value_status="normalized",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_PROC_PRESS_NORM",
                    run_id,
                    "reactor_process_gas",
                    process["process_stage_id"],
                    "pressure_kPa",
                    "SPAN_203BB77D6C849A7AD03D",
                    "Reported atmospheric pressure is normalized to 101.325 kPa.",
                    value_status="normalized",
                ),
            ]
        )
        if hab_mm is not None:
            tables["evidence_index"].append(
                evidence_row(
                    source_id,
                    f"{ev}_PROC_HAB",
                    run_id,
                    "reactor_process_gas",
                    process["process_stage_id"],
                    "reactor_setup_summary",
                    "SPAN_3C14B1160444A0E181F6" if code.startswith("HAB_") else "SPAN_13398CB945C0EAEBD2A2",
                    f"The plotted experimental matrix places this wire at HAB {hab_mm} mm.",
                    value_status="figure_digitized",
                    confidence="medium",
                )
            )
        else:
            tables["evidence_index"].append(
                evidence_row(
                    source_id,
                    f"{ev}_PROC_SETUP",
                    run_id,
                    "reactor_process_gas",
                    process["process_stage_id"],
                    "reactor_setup_summary",
                    "SPAN_F4362747281F8C61E011",
                    "An untreated nickel wire was flame-exposed, but its HAB is not stated.",
                )
            )
        if exposure_min is not None:
            tables["evidence_index"].append(
                evidence_row(
                    source_id,
                    f"{ev}_PROC_TIME",
                    run_id,
                    "reactor_process_gas",
                    process["process_stage_id"],
                    "holding_time_min",
                    "SPAN_13398CB945C0EAEBD2A2" if not code.startswith("HAB_") else "SPAN_3C14B1160444A0E181F6",
                    "The experimental series fixes flame exposure at 10 minutes.",
                )
            )
        product_fields = (
            "primary_yield_metric;yield_original;yield_definition_original;secondary_result_summary;"
            "CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;characterization_methods"
        )
        tables["evidence_index"].append(
            evidence_row(
                source_id,
                f"{ev}_PRODUCT",
                run_id,
                "yield_quality",
                product["product_id"],
                product_fields,
                result_span,
                outcome,
                value_status=result_status,
                confidence="medium" if result_status == "figure_digitized" else "high",
                linked_issue_id=result_issue,
            )
        )
        tables["evidence_index"].append(
            evidence_row(
                source_id,
                f"{ev}_COST",
                run_id,
                "cost_scale_review",
                run_id,
                "record_level",
                "SPAN_203BB77D6C849A7AD03D",
                "The paper demonstrates individual catalyst-wire flame experiments and reports no quantitative production cost or scale class.",
                value_status="review_assessment",
            )
        )
        if product_extra:
            extra_fields = ";".join(product_extra)
            tables["evidence_index"].extend(
                [
                    evidence_row(
                        source_id,
                        f"{ev}_MORPH_SEM",
                        run_id,
                        "yield_quality",
                        product["product_id"],
                        "outer_diameter_mean_nm;outer_diameter_range_nm;morphology",
                        "SPAN_D39304CD7EC8DD676271",
                        "SEM gives 9-27 nm curly, randomly oriented CNTs in the central growth region.",
                    ),
                    evidence_row(
                        source_id,
                        f"{ev}_MORPH_TEM",
                        run_id,
                        "yield_quality",
                        product["product_id"],
                        "CNT_type_reported;CNT_type_confirmed;CNT_type_evidence;outer_diameter_mean_nm;wall_number_summary;morphology;characterization_methods",
                        "SPAN_DB04921B74A7A02003C5",
                        "TEM confirms hollow multiwalled CNTs, about 25 nm average diameter, 0.3 nm lattice spacing, and tip growth with a nickel-oxide end particle.",
                    ),
                ]
            )

    add_common_rows(
        code="NO_ACID",
        label="Untreated nickel wire exposed to methane flame",
        summary="Control observation using a flame-exposed pure nickel wire without nitric-acid pretreatment; no CNT formation was observed.",
        acid_s=0,
        hab_mm=None,
        exposure_min=None,
        outcome="No CNT formation; post-flame nickel particles larger than 100 nm inhibited nanotube inception.",
        yield_text="no CNT observed",
        result_span="SPAN_F4362747281F8C61E011",
        result_status="reported",
        cnt_type_reported="no CNT observed",
        cnt_type_confirmed="no CNT observed",
        cnt_evidence="FESEM observation of the untreated flame-exposed wire",
    )

    for acid_s, length_mm in acid_figure_mm.items():
        conflicted = acid_s in {225, 240}
        if length_mm is None:
            outcome = (
                "No observable CNT deposit in Results/Figure 4; this conflicts with the broader abstract/conclusion range wording."
                if conflicted
                else "No CNT produced in Results/Figure 4."
            )
            yield_text = "no observable CNT deposit"
            cnt_reported = "no CNT observed in Results/Figure 4"
            cnt_confirmed = "no CNT observed by FESEM"
            cnt_evidence = "Results text and Figure 4 absence of a CNT growth-region bar"
        else:
            outcome = f"CNT-covered wire region approximately {length_mm:g} mm long by digitization of Figure 4."
            yield_text = f"approximately {length_mm:g} mm (digitized from Figure 4)"
            cnt_reported = "CNT"
            cnt_confirmed = "CNT observed by FESEM"
            cnt_evidence = "SEM-defined dark CNT-covered wire region in the acid-duration series"
        extra: dict[str, str] | None = None
        if acid_s == 165:
            extra = {
                "CNT_type_reported": "multiwalled CNT",
                "CNT_type_confirmed": "MWCNT confirmed by TEM",
                "CNT_type_evidence": "TEM hollow multiwall structure and approximately 0.3 nm lattice spacing",
                "outer_diameter_mean_nm": "25",
                "outer_diameter_range_nm": "9-27",
                "wall_number_summary": "multiwalled; wall count not reported",
                "morphology": "hollow, curly and entangled CNTs with random growth; tip-growth end caps",
            }
        add_common_rows(
            code=f"ACID_{acid_s:03d}",
            label=f"Acid-duration series: {acid_s} s HNO3, HAB 6 mm",
            summary=f"Methane-flame exposure for 10 min at HAB 6 mm after {acid_s} s nitric-acid pretreatment; {outcome}",
            acid_s=acid_s,
            hab_mm=6,
            exposure_min=10,
            outcome=outcome,
            yield_text=yield_text,
            result_span="SPAN_13398CB945C0EAEBD2A2",
            result_status="figure_digitized" if length_mm is not None else "reported",
            cnt_type_reported=cnt_reported,
            cnt_type_confirmed=cnt_confirmed,
            cnt_evidence=cnt_evidence,
            product_extra=extra,
            result_issue=conflict_issue if conflicted else "not_applicable",
        )

    for hab_mm, length_mm in hab_figure_mm.items():
        if hab_mm <= 3:
            outcome = "No dark CNT deposit was observed on the wire."
            yield_text = "no CNT deposit observed"
            cnt_reported = "no CNT observed"
            cnt_confirmed = "no CNT observed by FESEM"
            cnt_evidence = "Figure 5 series and Results description"
            span = "SPAN_3C14B1160444A0E181F6"
            status = "reported"
        elif hab_mm in {4, 5}:
            outcome = f"CNT-covered wire region {length_mm:g} mm long."
            yield_text = f"{length_mm:g} mm CNT growth region"
            cnt_reported = "CNT"
            cnt_confirmed = "CNT observed by FESEM"
            cnt_evidence = "SEM-defined dark CNT-covered region in the HAB series"
            span = "SPAN_3C14B1160444A0E181F6"
            status = "reported"
        else:
            outcome = "No CNT; thick soot deposit was observed."
            yield_text = "no CNT; soot deposit"
            cnt_reported = "no CNT observed; soot formed"
            cnt_confirmed = "no CNT observed by FESEM"
            cnt_evidence = "Results description of thick soot from HAB 7 through 10 mm"
            span = "SPAN_9A074CBA565AA78189B2"
            status = "reported"
        add_common_rows(
            code=f"HAB_{hab_mm:02d}",
            label=f"HAB series: {hab_mm} mm, 165 s HNO3",
            summary=f"Methane-flame exposure for 10 min at HAB {hab_mm} mm after 165 s nitric-acid pretreatment; {outcome}",
            acid_s=165,
            hab_mm=hab_mm,
            exposure_min=10,
            outcome=outcome,
            yield_text=yield_text,
            result_span=span,
            result_status=status,
            cnt_type_reported=cnt_reported,
            cnt_type_confirmed=cnt_confirmed,
            cnt_evidence=cnt_evidence,
        )

    write_package(package, tables)
    write_review(
        package,
        {
            "source_id": source_id,
            "review_status": "extracted_needs_supervisory_review",
            "reviewer": "Codex",
            "source_identity_checked": True,
            "campaign_reconciliation": {
                "result_linked_campaigns_in_paper": 26,
                "extracted_runs": 26,
                "negative_runs_preserved": 15,
                "matrix_note": "One untreated-wire control; sixteen 15 s acid-duration points from 15-240 s at HAB 6 mm; nine additional HAB points after excluding the duplicate HAB 6/165 s condition.",
            },
            "pdf_visual_review": {
                "completed": True,
                "pages_checked": [3, 4, 5, 6, 7],
                "objects_checked": ["Figure 1 apparatus", "Figures 2-3 microscopy", "Figure 4 acid-duration bars", "Figure 5 HAB bars", "Figure 6 catalyst surfaces", "conclusion"],
            },
            "figure_digitization": {
                "completed": True,
                "figures": [4, 5],
                "policy": "Approximate bar heights are labelled figure_digitized; text-explicit 4/5/6 mm HAB values remain reported.",
            },
            "pressure_policy_check": "Atmospheric pressure is explicitly reported; 101.325 kPa is stored only as a normalized value with separate evidence.",
            "cross_run_inheritance_check": "MWCNT structure and 9-27/25 nm morphology are assigned only to the 165 s/HAB 6 mm sample analyzed by SEM/TEM.",
            "internal_conflict_preserved": "Results/Figure 4 gives 90-210 s, whereas abstract/conclusion gives 90-260 s; no reconciliation was invented.",
        },
    )
    update_manifest(
        source_id,
        "extracted_needs_supervisory_review",
        package_path=package.relative_to(REDO_ROOT).as_posix(),
    )
    return package


def build_lit_26e8cf0b(context: SourceContext) -> Path:
    """Eldahshory et al. 2023, five unique WPP/Ni-foam result campaigns."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    runs = [
        {"code": "HR05_CVD600", "hr": 5, "cvd": 600, "yield": 43.12, "diameter": 55, "raman": 1.09, "series": "temperature"},
        {"code": "HR05_CVD700", "hr": 5, "cvd": 700, "yield": 39.34, "diameter": 30, "raman": 0.98, "series": "overlap"},
        {"code": "HR05_CVD800", "hr": 5, "cvd": 800, "yield": 35.67, "diameter": 26, "raman": 0.879, "series": "temperature"},
        {"code": "HR10_CVD700", "hr": 10, "cvd": 700, "yield": 23.12, "diameter": 74, "raman": 1.06, "series": "heating_rate"},
        {"code": "HR20_CVD700", "hr": 20, "cvd": 700, "yield": 11.02, "diameter": 145, "raman": 1.072, "series": "heating_rate"},
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [
            source_master_row(
                context,
                "Methods and the two intersecting one-factor result series: CVD temperature at 5 C/min and WPP heating rate at 700 C.",
            )
        ],
        "source_run": [],
        "catalyst_system": [],
        "reactor_process_gas": [],
        "yield_quality": [],
        "cost_scale_review": [],
        "evidence_index": [],
        "review_issue_log": [],
    }
    yield_issue = f"{source_id}_ISSUE_YIELD_BASIS"
    unlinked_issue = f"{source_id}_ISSUE_FIG3_UNLINKED"
    ev_formula = f"{source_id}_EV_YIELD_FORMULA"
    ev_unlinked = f"{source_id}_EV_FIG3_UNLINKED"
    tables["evidence_index"].extend(
        [
            evidence_row(
                source_id,
                ev_formula,
                "not_applicable",
                "source_master",
                source_id,
                "source_section_scope",
                "SPAN_3914F1F792F6710B4978",
                "The paper labels the metric carbon/CNT yield, but Equation 1 is total post-CVD mass gain divided by initial Ni-foam mass.",
                linked_issue_id=yield_issue,
            ),
            evidence_row(
                source_id,
                ev_unlinked,
                "not_applicable",
                "source_master",
                source_id,
                "source_section_scope",
                "SPAN_170C39FA6116F3DB6B8C",
                "Figure 3 reports a separate 11.61-22.5 nm/2.35 nm-wall observation without identifying its HR/CVD condition.",
                linked_issue_id=unlinked_issue,
            ),
        ]
    )
    tables["review_issue_log"].extend(
        [
            issue_row(
                yield_issue,
                source_id,
                "not_applicable",
                "yield_definition_scope",
                "source_master",
                source_id,
                "source_section_scope",
                "The reported percentage is a catalyst mass-gain metric for total deposited carbon, although the prose and Figure 5 call it CNT yield. It is not converted to plastic-carbon conversion or pure-CNT yield.",
                evidence_ids=ev_formula,
                severity="medium",
                conflicting_values="label: CNT/carbon yield; formula: (post-CVD catalyst plus deposit minus initial catalyst)/initial catalyst",
            ),
            issue_row(
                unlinked_issue,
                source_id,
                "not_applicable",
                "result_without_run_locator",
                "source_master",
                source_id,
                "source_section_scope",
                "The Figure 3 diameter and wall-thickness values are not linked to a unique experimental condition and therefore are not copied into any run.",
                evidence_ids=ev_unlinked,
                severity="low",
            ),
        ]
    )

    for index, item in enumerate(runs, start=1):
        run = source_run_row(
            source_id,
            item["code"],
            f"WPP heating {item['hr']} C/min; CVD {item['cvd']} C",
            f"Two-stage WPP pyrolysis/catalysis with 5 g WPP and Ni foam; carbon-deposit yield {item['yield']}% of initial catalyst mass, mean MWCNT diameter {item['diameter']} nm, and Raman I_D/I_G {item['raman']}.",
            data_type="experimental_condition",
        )
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label="commercial nickel foam",
            active_metals="Ni",
            support_material="self-supported three-dimensional nickel foam",
            preparation_method="air oxidation followed by hydrogen/nitrogen reduction",
            preparation_modifier="H2:N2 = 40:60 during reduction",
            preparation_detail="0.15 g nickel foam used in every experiment",
            calcination_condition="500 C in static air for 30 min",
            reduction_condition="600 C for 1 h at 100 mL/min H2/N2",
            phase_or_state_summary="metallic Ni reflections remained after CNT deposition",
        )
        pyrolysis = process_row(
            run_id,
            1,
            "waste_polypropylene_pyrolysis",
            reactor_type="two-stage horizontal fixed-bed tube system",
            reactor_material="stainless steel",
            reactor_size_summary="pyrolysis tube 80 cm long and 4 cm inner diameter",
            reactor_setup_summary="pyrolysis reactor followed by a room-temperature condenser and catalytic reactor",
            temperature_setpoint_C="500",
            heating_rate_C_min=str(item["hr"]),
            holding_time_min="30",
            carbon_source="washed, dried, shredded waste polypropylene screened to 500 micrometres",
            carbon_source_flow_original="5 g WPP charge",
            inert_gas="N2",
            inert_gas_flow_original="60 mL/min",
            process_note="The catalytic reactor was heated before the WPP pyrolysis ramp; pressure was not reported.",
        )
        deposition = process_row(
            run_id,
            2,
            "catalytic_carbon_deposition",
            reactor_type="two-stage horizontal fixed-bed tube system",
            reactor_material="stainless steel",
            reactor_size_summary="catalytic tube 80 cm long and 4 cm inner diameter",
            reactor_setup_summary="uncondensed WPP pyrolysis gases pass from the condenser over nickel foam",
            catalyst_loading_mass_g="0.15",
            temperature_setpoint_C=str(item["cvd"]),
            carbon_source="uncondensed gases from 500 C WPP pyrolysis",
            inert_gas="N2",
            inert_gas_flow_original="60 mL/min",
            cooling_condition="both reactors cooled to room temperature while N2 continued to flow",
            process_note="CVD pressure and an independently timed deposition duration were not reported.",
        )
        product = yield_row(
            run_id,
            primary_yield_metric="carbon-deposit mass gain relative to initial Ni-foam mass",
            yield_original=f"{item['yield']}%",
            yield_definition_original="(post-CVD mass of catalyst plus deposited carbon - initial Ni-foam mass) / initial Ni-foam mass x 100",
            yield_value_standardized=str(item["yield"]),
            yield_unit_standardized="percent of initial Ni-foam mass",
            yield_standardization_note="Value retained on the paper's catalyst-mass-gain basis; not treated as plastic conversion or pure-CNT mass yield.",
            secondary_result_summary="MWCNTs deposited on the three-dimensional nickel-foam surface",
            CNT_type_reported="multiwall carbon nanotubes",
            CNT_type_confirmed="MWCNT confirmed by TEM",
            product_mixture_summary="carbon deposit identified as MWCNTs; non-CNT fraction not quantified",
            CNT_type_evidence="TEM and XRD/Raman characterization",
            outer_diameter_mean_nm=str(item["diameter"]),
            morphology="entangled multiwall nanotubes on nickel foam",
            Raman_ratio_type="I_D/I_G",
            Raman_ratio_value=str(item["raman"]),
            purity_basis="no quantitative purity measurement; 2D-band intensity is not converted to purity",
            characterization_methods="SEM; TEM; XRD; Raman",
            notes="Condition-unlinked Figure 3 dimensions were deliberately not inherited into this run.",
        )
        cost = cost_row(
            run_id,
            scale_level_demonstrated="not_reported",
            scale_level_claimed="not_reported",
            quantitative_cost_reported="not_reported",
        )
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].extend([pyrolysis, deposition])
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        ev = f"{source_id}_EV_{index:02d}"
        tables["evidence_index"].extend(
            [
                evidence_row(
                    source_id,
                    f"{ev}_CAT_BASE",
                    run_id,
                    "catalyst_system",
                    catalyst["catalyst_id"],
                    "catalyst_label;active_metals;support_material;preparation_method;preparation_detail;calcination_condition;reduction_condition",
                    "SPAN_4AD86E43849E90A78626",
                    "All experiments use 0.15 g commercial Ni foam oxidized at 500 C for 30 min and reduced at 600 C for 1 h in 100 mL/min H2/N2.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_CAT_RATIO",
                    run_id,
                    "catalyst_system",
                    catalyst["catalyst_id"],
                    "preparation_modifier",
                    "SPAN_C9C821AC22F0A143A228",
                    "The reduction mixture is reported as H2:N2 40:60.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_CAT_PHASE",
                    run_id,
                    "catalyst_system",
                    catalyst["catalyst_id"],
                    "phase_or_state_summary",
                    "SPAN_CAA7C7D81CDAA9211723",
                    "XRD shows metallic Ni reflections in the CNT-bearing samples.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_PYR_APP",
                    run_id,
                    "reactor_process_gas",
                    pyrolysis["process_stage_id"],
                    "stage_type;reactor_type;reactor_material;reactor_size_summary;reactor_setup_summary;inert_gas;inert_gas_flow_original;process_note",
                    "SPAN_5F4ACF44D5EC7EE88DCD",
                    "The two 80 cm x 4 cm stainless-steel tube reactors operate under 60 mL/min N2 with an intermediate condenser.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_PYR_COND",
                    run_id,
                    "reactor_process_gas",
                    pyrolysis["process_stage_id"],
                    "temperature_setpoint_C;heating_rate_C_min;carbon_source;carbon_source_flow_original",
                    "SPAN_6CDCB2A7E061034C7990",
                    f"The 5 g WPP charge is heated to 500 C at the series rate of {item['hr']} C/min.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_PYR_TIME",
                    run_id,
                    "reactor_process_gas",
                    pyrolysis["process_stage_id"],
                    "holding_time_min",
                    "SPAN_A24CE2EF28FA6E986FF3",
                    "WPP is held at 500 C for 30 min.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_CVD_APP",
                    run_id,
                    "reactor_process_gas",
                    deposition["process_stage_id"],
                    "stage_type;reactor_type;reactor_material;reactor_setup_summary;temperature_setpoint_C;carbon_source;inert_gas;inert_gas_flow_original;process_note",
                    "SPAN_6CDCB2A7E061034C7990",
                    f"Uncondensed pyrolysis gases pass over Ni foam in the second reactor at {item['cvd']} C.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_CVD_SIZE",
                    run_id,
                    "reactor_process_gas",
                    deposition["process_stage_id"],
                    "reactor_size_summary",
                    "SPAN_5F4ACF44D5EC7EE88DCD",
                    "Both stainless-steel reactor tubes are reported as 80 cm long with 4 cm inner diameter.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_CVD_CATLOAD",
                    run_id,
                    "reactor_process_gas",
                    deposition["process_stage_id"],
                    "catalyst_loading_mass_g",
                    "SPAN_4AD86E43849E90A78626",
                    "Every experiment uses 0.15 g nickel foam.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_CVD_COOL",
                    run_id,
                    "reactor_process_gas",
                    deposition["process_stage_id"],
                    "cooling_condition",
                    "SPAN_A24CE2EF28FA6E986FF3",
                    "After reaction, both reactors cool to room temperature under continued nitrogen flow.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_PROD_TYPE",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "secondary_result_summary;CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;morphology;characterization_methods",
                    "SPAN_170C39FA6116F3DB6B8C",
                    "TEM identifies the nickel-foam carbon deposit as multiwall carbon nanotubes.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_PROD_YIELD",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "primary_yield_metric;yield_original;yield_definition_original;yield_value_standardized;yield_unit_standardized",
                    "SPAN_1E6DED6AC05BB35E1574",
                    f"Figure 5 reports {item['yield']}% for HR {item['hr']} C/min and CVD {item['cvd']} C on the Equation-1 mass-gain basis.",
                    linked_issue_id=yield_issue,
                ),
                evidence_row(
                    source_id,
                    f"{ev}_PROD_DIAM",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "outer_diameter_mean_nm",
                    (
                        "SPAN_521B99EB77733D3EC7A9"
                        if item["cvd"] == 800
                        else "SPAN_6784C35D63F4680B4B33"
                        if item["hr"] in {10, 20}
                        else "SPAN_1E6DED6AC05BB35E1574"
                    ),
                    f"The run-linked SEM/TEM series reports a mean diameter of {item['diameter']} nm.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_PROD_RAMAN",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "Raman_ratio_type;Raman_ratio_value;purity_basis;characterization_methods",
                    "SPAN_7E34205A20452FB82BB5" if item["hr"] in {10, 20} else "SPAN_26272C61E0D13F906168",
                    f"The run-linked Raman series reports I_D/I_G {item['raman']}; no quantitative purity is inferred.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_COST",
                    run_id,
                    "cost_scale_review",
                    run_id,
                    "record_level",
                    "SPAN_6CDCB2A7E061034C7990",
                    "The paper reports 5 g feed and 0.15 g catalyst experiments but no formal scale class or quantitative production cost.",
                    value_status="review_assessment",
                ),
            ]
        )

    write_package(package, tables)
    write_review(
        package,
        {
            "source_id": source_id,
            "review_status": "extracted_needs_supervisory_review",
            "reviewer": "Codex",
            "source_identity_checked": True,
            "campaign_reconciliation": {
                "result_linked_campaigns_in_paper": 5,
                "extracted_runs": 5,
                "negative_runs_preserved": 0,
                "matrix_note": "Three CVD temperatures at HR 5 and three heating rates at CVD 700 share the HR5/CVD700 point, yielding five unique campaigns rather than six duplicated rows.",
            },
            "pdf_visual_review": {
                "completed": True,
                "pages_checked": [3, 4, 7, 8, 9, 10],
                "objects_checked": ["Figure 1 apparatus", "method continuation across columns", "Figures 4-6 microscopy/Raman/yield", "Figure 7 summary", "conclusion"],
            },
            "pressure_policy_check": "Reaction pressure is not reported and remains empty.",
            "cross_run_inheritance_check": "Only run-linked diameter and Raman values are assigned; condition-unlinked Figure 3 dimensions remain in the issue log.",
            "yield_basis_check": "The mass-gain denominator is preserved exactly and is not relabeled as plastic conversion or pure-CNT yield.",
        },
    )
    update_manifest(
        source_id,
        "extracted_needs_supervisory_review",
        package_path=package.relative_to(REDO_ROOT).as_posix(),
    )
    return package


def build_lit_2af90445(context: SourceContext) -> Path:
    """Il'in et al. 2018, four-temperature PECVD VACNT series."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    runs = [
        {"temp": 650, "diameter": 25, "diameter_text": "25 +/- 3 nm", "height": "65 +/- 5 nm", "individual": "not_reported", "alignment": "vertically aligned array with disoriented CNTs also present", "raman": ""},
        {"temp": 700, "diameter": 25, "diameter_text": "25 +/- 4 nm", "height": "66 +/- 5 nm", "individual": "not_reported", "alignment": "vertically aligned array; disoriented CNTs removed", "raman": "0.92"},
        {"temp": 750, "diameter": 44, "diameter_text": "44 +/- 3 nm; individual CNTs 70 +/- 3 nm", "height": "array 80 +/- 9 nm; individual CNTs 350 +/- 10 nm", "individual": "individual larger CNT population observed", "alignment": "vertically aligned array", "raman": "0.88"},
        {"temp": 800, "diameter": 51, "diameter_text": "51 +/- 6 nm; individual CNTs 52 +/- 2 nm", "height": "array 100 +/- 12 nm; individual CNTs up to 600 +/- 14 nm", "individual": "individual taller CNT population observed", "alignment": "vertically aligned array", "raman": "0.90"},
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [
            source_master_row(context, "Complete 650, 700, 750, and 800 C PECVD temperature series with SEM geometry and Raman structure results.")
        ],
        "source_run": [],
        "catalyst_system": [],
        "reactor_process_gas": [],
        "yield_quality": [],
        "cost_scale_review": [],
        "evidence_index": [],
        "review_issue_log": [],
    }
    for index, item in enumerate(runs, start=1):
        temp = item["temp"]
        run = source_run_row(
            source_id,
            f"PECVD_{temp}",
            f"PECVD VACNT growth at {temp} C",
            f"Ni/Cr/Si PECVD for 20 min at {temp} C in NH3/C2H2; MWCNT array mean diameter {item['diameter_text']} and height {item['height']}.",
            data_type="experimental_condition",
        )
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label="10 nm Ni catalyst / 20 nm Cr buffer / Si(100)",
            active_metals="Ni",
            support_material="Si(100) wafer with 20 nm Cr buffer sublayer",
            precursor_summary="10 nm nickel catalytic film",
            preparation_method="magnetron sputtering of Cr buffer and Ni catalytic films",
        )
        process = process_row(
            run_id,
            1,
            "plasma_enhanced_CVD_growth",
            reactor_type="NANOFAB NTK-9 PECVD module",
            reactor_setup_summary="top-growth mechanism on Ni/Cr/Si wafer",
            temperature_setpoint_C=str(temp),
            holding_time_min="20",
            pressure_original="4.5 Torr",
            pressure_kPa="0.600",
            carbon_source="C2H2",
            carbon_source_flow_original="70 sccm",
            carbon_source_flow_sccm="70",
            reducing_gas="NH3",
            reducing_gas_flow_original="210 sccm",
            reducing_gas_flow_sccm="210",
            total_flow_original="280 sccm",
            total_flow_sccm="280",
            gas_composition_summary="NH3 210 sccm; C2H2 70 sccm",
            process_note="No plasma power or catalyst activation sequence was reported.",
        )
        product = yield_row(
            run_id,
            primary_yield_metric="qualitative VACNT formation with SEM geometry",
            yield_original="VACNT array formed",
            yield_definition_original="SEM-observed vertically aligned nanotube array; no gravimetric yield reported",
            yield_standardization_note="No mass yield or conversion was reported.",
            secondary_result_summary=(
                f"Array diameter {item['diameter_text']}; height {item['height']}; {item['individual']}."
            ),
            CNT_type_reported="vertically aligned carbon nanotubes",
            CNT_type_confirmed="multiwall CNT inferred by reported absence of RBM in Raman spectra",
            product_mixture_summary="VACNT array; non-CNT carbon fraction not quantified",
            CNT_type_evidence="D/G Raman modes and absence of RBM from 0-200 cm-1 for all four samples",
            RBM_peak_reported="absent in 0-200 cm-1 range",
            outer_diameter_mean_nm=str(item["diameter"]),
            outer_diameter_range_nm=item["diameter_text"],
            length_summary=item["height"],
            morphology="top-grown multiwall carbon nanotubes",
            alignment_or_array=item["alignment"],
            Raman_ratio_type="I_D/I_G" if item["raman"] else "not_reported",
            Raman_ratio_value=item["raman"],
            characterization_methods="SEM; Raman",
            notes="The paper reports array height in nanometres; units are preserved exactly despite the unusually short values.",
        )
        cost = cost_row(
            run_id,
            scale_level_demonstrated="not_reported",
            scale_level_claimed="not_reported",
            quantitative_cost_reported="not_reported",
        )
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].append(process)
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        ev = f"{source_id}_EV_{index:02d}"
        result_span = "SPAN_FDEC626E17C5C84D37A1" if temp == 800 else "SPAN_54212F6913E944ACF067"
        tables["evidence_index"].extend(
            [
                evidence_row(
                    source_id,
                    f"{ev}_CAT",
                    run_id,
                    "catalyst_system",
                    catalyst["catalyst_id"],
                    "catalyst_label;active_metals;support_material;precursor_summary;preparation_method",
                    "SPAN_750658F882BE506FD0DD",
                    "The catalyst stack is 10 nm Ni on a 20 nm Cr buffer on Si(100), formed by magnetron sputtering.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_PROC",
                    run_id,
                    "reactor_process_gas",
                    process["process_stage_id"],
                    "stage_type;reactor_type;reactor_setup_summary;holding_time_min;pressure_original;carbon_source;carbon_source_flow_original;carbon_source_flow_sccm;reducing_gas;reducing_gas_flow_original;reducing_gas_flow_sccm;gas_composition_summary;process_note",
                    "SPAN_365F3A0E561CD0EC7671",
                    f"PECVD at {temp} C uses NH3 210 sccm and C2H2 70 sccm at 4.5 Torr for 20 min.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_PROC_TEMP",
                    run_id,
                    "reactor_process_gas",
                    process["process_stage_id"],
                    "temperature_setpoint_C",
                    result_span,
                    f"The run-linked result panel identifies the PECVD sample grown at {temp} C.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_PRESS_NORM",
                    run_id,
                    "reactor_process_gas",
                    process["process_stage_id"],
                    "pressure_kPa",
                    "SPAN_365F3A0E561CD0EC7671",
                    "4.5 Torr is normalized to 0.600 kPa.",
                    value_status="normalized",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_FLOW_CALC",
                    run_id,
                    "reactor_process_gas",
                    process["process_stage_id"],
                    "total_flow_original;total_flow_sccm",
                    "SPAN_365F3A0E561CD0EC7671",
                    "The total 280 sccm is calculated from reported 210 sccm NH3 plus 70 sccm C2H2.",
                    value_status="calculated",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_PROD_GEOM",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "primary_yield_metric;yield_original;yield_definition_original;secondary_result_summary;outer_diameter_mean_nm;outer_diameter_range_nm;length_summary;morphology;alignment_or_array;characterization_methods",
                    result_span,
                    f"SEM reports the run-linked VACNT geometry and alignment at {temp} C.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_PROD_TYPE",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;RBM_peak_reported;morphology;characterization_methods",
                    "SPAN_FDEC626E17C5C84D37A1",
                    "All four samples show D/G modes and no RBM from 0-200 cm-1, which the authors use to identify multiwall CNTs.",
                ),
                evidence_row(
                    source_id,
                    f"{ev}_COST",
                    run_id,
                    "cost_scale_review",
                    run_id,
                    "record_level",
                    "SPAN_365F3A0E561CD0EC7671",
                    "The paper reports wafer PECVD conditions but no formal production scale or quantitative cost.",
                    value_status="review_assessment",
                ),
            ]
        )
        if item["raman"]:
            tables["evidence_index"].append(
                evidence_row(
                    source_id,
                    f"{ev}_PROD_RAMAN",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "Raman_ratio_type;Raman_ratio_value",
                    "SPAN_2C65F5CA33D44A00C68A",
                    f"The reported I_D/I_G at {temp} C is {item['raman']}.",
                )
            )
    write_package(package, tables)
    write_review(
        package,
        {
            "source_id": source_id,
            "review_status": "extracted_needs_supervisory_review",
            "reviewer": "Codex",
            "source_identity_checked": True,
            "campaign_reconciliation": {
                "result_linked_campaigns_in_paper": 4,
                "extracted_runs": 4,
                "negative_runs_preserved": 0,
                "matrix_note": "All four plotted temperatures were retained; the paper does not report I_D/I_G for 650 C, so that field remains blank for that run.",
            },
            "pdf_visual_review": {
                "completed": True,
                "pages_checked": [1, 2, 3],
                "objects_checked": ["methods", "Figure 1 SEM panels", "Figure 2 Raman spectra", "conclusion"],
            },
            "pressure_policy_check": "4.5 Torr is explicitly reported and normalized to 0.600 kPa; no atmospheric default is used.",
            "cross_run_inheritance_check": "Temperature-specific geometry and Raman values are isolated; the common no-RBM conclusion applies explicitly to all samples.",
            "unit_policy_check": "The paper's nanometre array-height units are preserved exactly and not silently changed to micrometres.",
        },
    )
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


def build_lit_2cbdcdc3(context: SourceContext) -> Path:
    """Dai et al. 2012, in-situ VACNT films for organic-vapor adsorption."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    runs = [
        {
            "code": "GROWTH20",
            "label": "In-situ VACNT film, 20 min growth at 650 C",
            "summary": (
                "Evaporated Fe/Ni catalyst on a GaPO4 resonator was reduced for "
                "90 min and grown for 20 min at 650 C; the resulting CNT film "
                "had a reported mass of 4.0 microg and toluene BET area of 290 mm2."
            ),
            "growth_min": "20",
            "mass_microg": "4.0",
            "mass_g": "0.0000040",
            "toluene_bet_mm2": "290",
            "cnt_reported": "multiwalled CNT film (authors attribute wall type to Ref. [2])",
            "cnt_confirmed": "not independently confirmed in the current paper",
            "type_evidence": (
                "The paper calls the studied films multiwalled CNTs while citing its "
                "earlier growth paper; no wall-count image or spectrum is supplied here."
            ),
            "secondary": (
                "Total BET surface area: toluene 290 mm2, hexane 73 mm2, "
                "cyclohexane 230 mm2, and 2-butanone 110 mm2; average 180 +/- "
                "100 mm2; specific BET surface area 45 +/- 25 m2/g."
            ),
            "bet_m2_g": "45",
            "application": (
                "Organic-vapor adsorption film; effective porosity 2%, projected "
                "patch area 38 mm2, effective density 0.03 g/cm3, and void volume "
                "greater than 90%."
            ),
            "result_span": "SPAN_71A5F0B9218D404D54EA",
        },
        {
            "code": "GROWTH5",
            "label": "In-situ CNT film, 5 min growth at 650 C",
            "summary": (
                "The fabrication growth time was lowered from 20 to 5 min at the "
                "reported 650 C growth temperature; the resulting CNT film had a "
                "mass of 3.1 microg and toluene BET area of 240 mm2."
            ),
            "growth_min": "5",
            "mass_microg": "3.1",
            "mass_g": "0.0000031",
            "toluene_bet_mm2": "240",
            "cnt_reported": "CNT film; wall count not separately stated for the 5 min device",
            "cnt_confirmed": "not independently confirmed in the current paper",
            "type_evidence": (
                "The result explicitly identifies a CNT film produced by the 5 min "
                "growth, but does not give a run-specific wall-count measurement."
            ),
            "secondary": "Toluene total BET surface area 240 mm2.",
            "bet_m2_g": "",
            "application": "Organic-vapor adsorption film with toluene BET area 240 mm2.",
            "result_span": "SPAN_71A5F0B9218D404D54EA",
        },
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [
            source_master_row(
                context,
                "Complete current-paper fabrication description, 20 min baseline film, 5 min growth-time variant, BET Table 2, and porosity/density discussion.",
            )
        ],
        "source_run": [],
        "catalyst_system": [],
        "reactor_process_gas": [],
        "yield_quality": [],
        "cost_scale_review": [],
        "evidence_index": [],
        "review_issue_log": [],
    }
    for index, item in enumerate(runs, start=1):
        run = source_run_row(
            source_id,
            item["code"],
            item["label"],
            item["summary"],
            data_type="experimental_condition",
        )
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label="evaporated Fe/Ni catalyst patch on SiO2/Cr/GaPO4",
            active_metals="Fe; Ni",
            support_material="GaPO4 crystal with Pt/Ti electrodes, 200 nm SiO2, and 3 nm Cr",
            metal_ratio_original="1 nm Ni; 1 nm Fe",
            precursor_summary="1 nm Ni and 1 nm Fe evaporated catalyst layers",
            preparation_method="evaporation",
            preparation_detail="7 mm diameter patch: 200 nm SiO2 / 3 nm Cr / 1 nm Ni / 1 nm Fe",
            reduction_condition="90 min reduction cycle; gas and temperature not restated",
            activation_condition="90 min reduction cycle before CNT growth",
        )
        process = process_row(
            run_id,
            1,
            "thermal_CVD_growth",
            reactor_type="thermal CVD system; detailed configuration referred to prior paper",
            reactor_setup_summary="in-situ CNT film growth on a catalyst-coated GaPO4 resonator",
            temperature_setpoint_C="650",
            holding_time_min=item["growth_min"],
            process_note=(
                "The current paper does not restate growth gas, gas flow, pressure, "
                "or reduction temperature. The 150 sccm argon flow belongs to the "
                "later adsorption test and is not assigned to CNT growth."
            ),
        )
        product = yield_row(
            run_id,
            primary_yield_metric="CNT film mass estimated from resonator frequency shift",
            yield_original=f"{item['mass_microg']} microg CNT film mass",
            yield_definition_original=(
                "film mass estimated from the resonant-frequency shift caused by film growth; "
                "a reproducible 1.1 microg thermal-cycling correction was applied"
            ),
            yield_calculation_method="piezoelectric resonator frequency-shift mass estimate",
            yield_value_standardized=item["mass_g"],
            yield_unit_standardized="g",
            yield_standardization_note=f"{item['mass_microg']} microg converted to {item['mass_g']} g.",
            secondary_result_summary=item["secondary"],
            CNT_type_reported=item["cnt_reported"],
            CNT_type_confirmed=item["cnt_confirmed"],
            product_mixture_summary="CNT film; non-CNT carbon fraction not quantified",
            CNT_type_evidence=item["type_evidence"],
            morphology="vertically aligned CNT film",
            BET_surface_area_product_m2_g=item["bet_m2_g"],
            characterization_methods="FESEM; GaPO4 crystal microbalance; organic-vapor BET analysis",
            application_property_summary=item["application"],
            notes=(
                f"The toluene BET value is a total film area ({item['toluene_bet_mm2']} mm2), "
                "not a mass-specific value. Growth gas and pressure remain unreported."
            ),
        )
        cost = cost_row(
            run_id,
            scale_level_demonstrated="not_reported",
            scale_level_claimed="not_reported",
            quantitative_cost_reported="not_reported",
        )
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].append(process)
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)

        prefix = f"{source_id}_EV_{index:02d}"
        method_issue_id = f"{source_id}_ISS_METHOD_{index:02d}"
        tables["evidence_index"].extend(
            [
                evidence_row(
                    source_id,
                    f"{prefix}_CAT",
                    run_id,
                    "catalyst_system",
                    catalyst["catalyst_id"],
                    "catalyst_label;active_metals;support_material;metal_ratio_original;precursor_summary;preparation_method;preparation_detail;reduction_condition;activation_condition",
                    "SPAN_A55DE9C505C90BA03343",
                    "A 7 mm evaporated catalyst patch contains 200 nm SiO2, 3 nm Cr, 1 nm Ni, and 1 nm Fe and undergoes a 90 min reduction cycle.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_PROC_COMMON",
                    run_id,
                    "reactor_process_gas",
                    process["process_stage_id"],
                    "stage_type;reactor_type;reactor_setup_summary;temperature_setpoint_C;process_note",
                    "SPAN_A55DE9C505C90BA03343",
                    "The current paper identifies in-situ CNT growth at 650 C and refers other CVD details to its prior paper.",
                    linked_issue_id=method_issue_id,
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_PROC_TIME",
                    run_id,
                    "reactor_process_gas",
                    process["process_stage_id"],
                    "holding_time_min",
                    (
                        "SPAN_A55DE9C505C90BA03343"
                        if item["growth_min"] == "20"
                        else item["result_span"]
                    ),
                    f"The current paper explicitly reports a {item['growth_min']} min CNT growth time for this device.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_MASS",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "primary_yield_metric;yield_original;secondary_result_summary;application_property_summary;notes",
                    item["result_span"],
                    f"The {item['growth_min']} min film has reported mass {item['mass_microg']} microg and toluene total BET area {item['toluene_bet_mm2']} mm2.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_MASS_METHOD",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "yield_definition_original;yield_calculation_method;characterization_methods",
                    "SPAN_139124B27277698A6110",
                    "Film mass is estimated from the growth-induced frequency shift with a 1.1 microg thermal-cycling correction; FESEM is also reported.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_MASS_NORM",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "yield_value_standardized;yield_unit_standardized;yield_standardization_note",
                    item["result_span"],
                    f"The reported {item['mass_microg']} microg film mass is normalized to {item['mass_g']} g.",
                    value_status="normalized",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_TYPE",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;morphology;characterization_methods",
                    (
                        "SPAN_642DE06591F5936E3037"
                        if item["growth_min"] == "20"
                        else item["result_span"]
                    ),
                    item["type_evidence"],
                    confidence="medium",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_COST",
                    run_id,
                    "cost_scale_review",
                    run_id,
                    "record_level",
                    "SPAN_A55DE9C505C90BA03343",
                    "The device-scale fabrication description contains no production-scale classification or quantitative cost.",
                    value_status="review_assessment",
                ),
            ]
        )
        if item["growth_min"] == "20":
            tables["evidence_index"].extend(
                [
                    evidence_row(
                        source_id,
                        f"{prefix}_BET_TABLE",
                        run_id,
                        "yield_quality",
                        product["product_id"],
                        "secondary_result_summary",
                        "SPAN_4E2AFC29BD0AA91899EB",
                        "Table 2 reports total BET areas of 290, 73, 230, and 110 mm2 for the four organic adsorbates.",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_BET_SPECIFIC",
                        run_id,
                        "yield_quality",
                        product["product_id"],
                        "secondary_result_summary;BET_surface_area_product_m2_g",
                        "SPAN_642DE06591F5936E3037",
                        "The average total area is 180 +/- 100 mm2 and the specific BET area is 45 +/- 25 m2/g.",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_POROSITY",
                        run_id,
                        "yield_quality",
                        product["product_id"],
                        "application_property_summary",
                        "SPAN_71A5F0B9218D404D54EA",
                        "The 7 mm patch has projected area 38 mm2 and previously measured porosity of 2%.",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_DENSITY",
                        run_id,
                        "yield_quality",
                        product["product_id"],
                        "application_property_summary",
                        "SPAN_48872C77A7FA23DE37B6",
                        "The calculated effective density is 0.03 g/cm3 and void volume is greater than 90%.",
                    ),
                ]
            )
        tables["review_issue_log"].append(
            issue_row(
                method_issue_id,
                source_id,
                run_id,
                "cited_method_not_reproduced",
                "reactor_process_gas",
                process["process_stage_id"],
                "process_note",
                (
                    "The current paper refers detailed VACNT growth conditions to Ref. [2]. "
                    "Only the 90 min reduction duration, growth time, and 650 C growth "
                    "temperature are retained; missing gas, flow, pressure, and reduction "
                    "temperature values were not inherited."
                ),
                evidence_ids=f"{prefix}_PROC_COMMON",
                severity="medium",
            )
        )
    write_package(package, tables)
    write_review(
        package,
        {
            "source_id": source_id,
            "review_status": "extracted_needs_supervisory_review",
            "reviewer": "Codex",
            "source_identity_checked": True,
            "campaign_reconciliation": {
                "result_linked_campaigns_in_paper": 2,
                "extracted_runs": 2,
                "negative_runs_preserved": 0,
                "matrix_note": (
                    "The 20 min baseline and the explicit 5 min growth-time variant are "
                    "separate runs; adsorption-test conditions are not synthesis runs."
                ),
            },
            "pdf_visual_review": {
                "completed": True,
                "pages_checked": [2, 3, 6],
                "objects_checked": [
                    "experimental catalyst/growth paragraph",
                    "Figure 1 FESEM micrographs",
                    "Table 2 BET surface areas",
                    "5 min versus 20 min comparison",
                ],
            },
            "pressure_policy_check": "Growth pressure is not reported and remains blank; no atmospheric value is introduced.",
            "cross_run_inheritance_check": (
                "The 5 min run receives only the common fabrication stack and the explicit "
                "single-variable growth-time change. The baseline film's multiwall attribution, "
                "specific BET area, porosity, and density are not copied to it."
            ),
            "unit_policy_check": (
                "Film masses are normalized from micrograms to grams with explicit normalized "
                "evidence rows; total BET film areas in mm2 are not confused with m2/g."
            ),
            "adsorption_flow_exclusion_check": (
                "The approximately 150 sccm argon flow is explicitly identified as the "
                "organic-vapor adsorption flow-cell condition and is excluded from CVD gas fields."
            ),
        },
    )
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


def build_lit_3e872882(context: SourceContext) -> Path:
    """Morant et al. 2019, selective AC-CVD SWNT forests on patterned TiN/Si."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    runs = [
        {
            "code": "TIN_LANE_POS",
            "label": "TiN lane adjacent to sputtered-Si, selective SWNT growth",
            "summary": "Mo/Co dip-coated patterned TiN/Si subjected to atmospheric AC-CVD; dense 8 micrometre VA-SWNT forest formed selectively on TiN lanes adjacent to sputtered-Si.",
            "support": "Si wafer coated with a 200 nm TiN lane adjacent to sputtered-Si",
            "cat_state": "Mo and Co oxides preferentially deposited on TiN and reduced to metallic nanoparticles during CVD",
            "outcome": "dense vertically aligned SWNT forest formed",
            "cnt_reported": "single-walled carbon nanotubes",
            "cnt_confirmed": "yes; RBM signal and HRTEM wall imaging reported",
            "type_evidence": "RBM below 300 cm-1 supports SWNT assignment; HRTEM was used for wall structure.",
            "diameter": "Raman-derived ca. 1.32 nm; HRTEM 3-5 nm",
            "length": "average forest height ca. 8 micrometres",
            "morphology": "densely packed vertically aligned forest",
            "alignment": "vertically aligned on TiN lanes",
            "app": "Field-emission cathode: field-enhancement factor ca. 1650 in the first test and close to 500 in the second and third tests.",
            "result_span": "SPAN_CE563DB3B165E74A2D3A",
            "result_confidence": "high",
        },
        {
            "code": "SPUTTERED_SI_NEG",
            "label": "Sputtered-Si lane, no SWNT growth",
            "summary": "The same patterned substrate and atmospheric AC-CVD exposure produced no observed SWNT growth on sputtered-Si lanes, where little catalyst was deposited.",
            "support": "sputtered-Si lane exposed by removal of the 200 nm TiN film",
            "cat_state": "nominal Mo/Co dip-coating, but XPS/AFM indicate little catalyst deposition on sputtered-Si",
            "outcome": "no SWNT growth observed",
            "cnt_reported": "not_observed",
            "cnt_confirmed": "negative result confirmed by FESEM and Raman mapping",
            "type_evidence": "FESEM and Raman mapping show absence of nanotubes on sputtered-Si.",
            "diameter": "",
            "length": "",
            "morphology": "no nanotube product observed",
            "alignment": "not_applicable",
            "app": "",
            "result_span": "SPAN_CE563DB3B165E74A2D3A",
            "result_confidence": "high",
        },
        {
            "code": "LARGE_TIN_NEG",
            "label": "Large TiN area away from sputtered-Si, no SWNT growth",
            "summary": "Within the patterned experiment, large TiN areas not near sputtered-Si did not show SWNT growth; the authors report that preferential catalyst deposition was no longer effective there.",
            "support": "large 200 nm TiN area not in the vicinity of sputtered-Si",
            "cat_state": "nominal Mo/Co dip-coating; preferential deposition on TiN versus sputtered-Si reported as ineffective for sufficiently large TiN areas",
            "outcome": "no SWNT growth observed over large TiN areas away from sputtered-Si",
            "cnt_reported": "not_observed",
            "cnt_confirmed": "negative spatial result reported from microscopy",
            "type_evidence": "The authors explicitly report no SWNT growth in large TiN regions away from sputtered-Si.",
            "diameter": "",
            "length": "",
            "morphology": "no nanotube product observed",
            "alignment": "not_applicable",
            "app": "",
            "result_span": "SPAN_3B38CE64AD032CE90885",
            "result_confidence": "medium",
        },
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [source_master_row(context, "Full HTML methods and results, including positive and negative spatial growth regions, Raman/HRTEM characterization, and field-emission testing.")],
        "source_run": [],
        "catalyst_system": [],
        "reactor_process_gas": [],
        "yield_quality": [],
        "cost_scale_review": [],
        "evidence_index": [],
        "review_issue_log": [],
    }
    for index, item in enumerate(runs, start=1):
        run = source_run_row(source_id, item["code"], item["label"], item["summary"], data_type="experimental_spatial_condition", confidence=item["result_confidence"])
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label="sequential dip-coated Mo/Co acetate catalyst",
            active_metals="Mo; Co",
            support_material=item["support"],
            promoter="Mo described as suppressing Co nanoparticle aggregation",
            precursor_summary="0.04% p/v Mo(II) acetate and 0.02% p/v Co(II) acetate tetrahydrate in ethanol",
            preparation_method="sequential dip-coating",
            preparation_detail="Mo solution dip-coat then 673 K calcination for 20 min; Co solution dip-coat then 673 K calcination for 20 min",
            calcination_condition="673 K for 20 min after each of the Mo and Co dip-coating steps",
            reduction_condition="1073 K for 10 min under 75% Ar / 25% H2 at total 320 sccm",
            phase_or_state_summary=item["cat_state"],
        )
        activation = process_row(
            run_id, 1, "catalyst_reduction",
            reactor_type="quartz tubular AC-CVD reactor",
            reactor_size_summary="25 mm inner diameter; 1000 mm length",
            reactor_setup_summary="substrate on quartz boat",
            temperature_setpoint_C="800",
            temperature_program_summary="heated to 1073 K at 30 K/min",
            holding_time_min="10",
            heating_rate_C_min="30",
            pressure_original="atmospheric pressure",
            pressure_kPa="101.325",
            reducing_gas="H2",
            inert_gas="Ar",
            total_flow_original="320 sccm",
            total_flow_sccm="320",
            gas_composition_summary="Ar 75 vol%; H2 25 vol%; combined flow 320 sccm",
        )
        growth = process_row(
            run_id, 2, "alcohol_catalytic_CVD_growth",
            reactor_type="quartz tubular AC-CVD reactor",
            reactor_size_summary="25 mm inner diameter; 1000 mm length",
            reactor_setup_summary="substrate on quartz boat",
            temperature_setpoint_C="800",
            holding_time_min="20",
            pressure_original="atmospheric pressure",
            pressure_kPa="101.325",
            carbon_source="ethanol/water vapor, 99.5:0.5 v/v",
            carbon_source_flow_original="delivered in 500 sccm N2 carrier",
            reducing_gas="H2",
            inert_gas="Ar; N2 carrier",
            cofeed_or_reactive_gas="N2 saturated with ethanol/water",
            cofeed_flow_original="500 sccm",
            cofeed_flow_sccm="500",
            gas_composition_summary="Ar/H2 flow retained at 320 sccm total; 500 sccm N2 saturated with 99.5:0.5 v/v ethanol/water added",
        )
        cooling = process_row(
            run_id, 3, "cooling",
            reactor_type="quartz tubular AC-CVD reactor",
            cooling_condition="oven heating stopped; cooled to room temperature under Ar",
            inert_gas="Ar",
            inert_gas_flow_original="300 sccm",
            inert_gas_flow_sccm="300",
            gas_composition_summary="Ar only after H2 and ethanol-saturated N2 were removed",
        )
        product = yield_row(
            run_id,
            primary_yield_metric="qualitative spatial SWNT growth outcome",
            yield_original=item["outcome"],
            yield_definition_original="microscopy- and Raman-resolved growth presence or absence by patterned substrate region",
            yield_standardization_note="No mass yield, conversion, or productivity was reported.",
            secondary_result_summary=(item["length"] if item["length"] else "No CNT geometry because no nanotubes were observed."),
            CNT_type_reported=item["cnt_reported"],
            CNT_type_confirmed=item["cnt_confirmed"],
            product_mixture_summary=("SWNT forest; non-CNT carbon fraction not quantified" if index == 1 else "no CNT product observed"),
            CNT_type_evidence=item["type_evidence"],
            SWCNT_or_few_wall_evidence_summary=("RBM below 300 cm-1 and HRTEM wall imaging" if index == 1 else "not_applicable; negative growth outcome"),
            RBM_peak_reported=("present below 300 cm-1" if index == 1 else "not_applicable"),
            outer_diameter_range_nm=item["diameter"],
            length_summary=item["length"],
            morphology=item["morphology"],
            alignment_or_array=item["alignment"],
            Raman_ratio_type=("G/D qualitative" if index == 1 else "not_applicable"),
            Raman_ratio_value="",
            Raman_laser_wavelength_nm=("532" if index == 1 else ""),
            characterization_methods="FESEM; HRTEM; Raman; XPS; AFM",
            application_property_summary=item["app"],
        )
        cost = cost_row(run_id, scale_level_demonstrated="patterned substrate laboratory experiment", scale_level_claimed="not_reported", quantitative_cost_reported="not_reported")
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].extend([activation, growth, cooling])
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        prefix = f"{source_id}_EV_{index:02d}"
        tables["evidence_index"].extend([
            evidence_row(source_id, f"{prefix}_CAT_PREP", run_id, "catalyst_system", catalyst["catalyst_id"], "catalyst_label;active_metals;promoter;precursor_summary;preparation_method;preparation_detail;calcination_condition", "SPAN_6D1C74C7D83342E5B9ED", "Sequential Mo and Co acetate dip-coating uses 0.04% and 0.02% p/v solutions with separate 673 K, 20 min calcinations."),
            evidence_row(source_id, f"{prefix}_CAT_SUPPORT", run_id, "catalyst_system", catalyst["catalyst_id"], "support_material", "SPAN_5254F99FDE357C8CF426", "The patterned support derives from a 200 nm TiN film deposited on Si(100), selectively removed to expose sputtered-Si lanes."),
            evidence_row(source_id, f"{prefix}_CAT_STATE", run_id, "catalyst_system", catalyst["catalyst_id"], "phase_or_state_summary", ("SPAN_BED929C7E6D984F17663" if index < 3 else item["result_span"]), "XPS and spatial-growth observations support the region-specific catalyst-deposition state.", confidence=item["result_confidence"]),
            evidence_row(source_id, f"{prefix}_CAT_REDUCE", run_id, "catalyst_system", catalyst["catalyst_id"], "reduction_condition", "SPAN_8A78352946DAC1A2DAE0", "Mo/Co oxides are reduced for 10 min at 1073 K under 75% Ar / 25% H2 at 320 sccm."),
            evidence_row(source_id, f"{prefix}_ACT_REPORTED", run_id, "reactor_process_gas", activation["process_stage_id"], "stage_type;reactor_type;reactor_size_summary;reactor_setup_summary;temperature_program_summary;holding_time_min;heating_rate_C_min;pressure_original;reducing_gas;inert_gas;total_flow_original;total_flow_sccm;gas_composition_summary", "SPAN_8A78352946DAC1A2DAE0", "Atmospheric tubular AC-CVD activation uses 1073 K, 30 K/min, 10 min and 320 sccm of 75% Ar/25% H2."),
            evidence_row(source_id, f"{prefix}_ACT_NORM", run_id, "reactor_process_gas", activation["process_stage_id"], "temperature_setpoint_C;pressure_kPa", "SPAN_8A78352946DAC1A2DAE0", "1073 K is normalized to approximately 800 C and explicit atmospheric pressure to 101.325 kPa.", value_status="normalized"),
            evidence_row(source_id, f"{prefix}_GROWTH_REPORTED", run_id, "reactor_process_gas", growth["process_stage_id"], "stage_type;reactor_type;reactor_size_summary;reactor_setup_summary;holding_time_min;pressure_original;carbon_source;carbon_source_flow_original;reducing_gas;inert_gas;cofeed_or_reactive_gas;cofeed_flow_original;cofeed_flow_sccm;gas_composition_summary", "SPAN_8A78352946DAC1A2DAE0", "Growth continues for about 20 min with the 320 sccm Ar/H2 stream and adds 500 sccm N2 saturated with 99.5:0.5 ethanol/water."),
            evidence_row(source_id, f"{prefix}_GROWTH_NORM", run_id, "reactor_process_gas", growth["process_stage_id"], "temperature_setpoint_C;pressure_kPa", "SPAN_8A78352946DAC1A2DAE0", "The retained 1073 K condition is normalized to approximately 800 C and atmospheric pressure to 101.325 kPa.", value_status="normalized"),
            evidence_row(source_id, f"{prefix}_COOL", run_id, "reactor_process_gas", cooling["process_stage_id"], "record_level", "SPAN_C80F53BEAA79A26C5D17", "Cooling is performed under 300 sccm Ar after stopping H2 and ethanol-saturated N2."),
            evidence_row(source_id, f"{prefix}_PROD", run_id, "yield_quality", product["product_id"], "primary_yield_metric;yield_original;yield_definition_original;yield_standardization_note;secondary_result_summary;CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;SWCNT_or_few_wall_evidence_summary;RBM_peak_reported;length_summary;morphology;alignment_or_array;characterization_methods", item["result_span"], "The run-specific patterned region preserves the reported positive or negative SWNT outcome.", confidence=item["result_confidence"]),
            evidence_row(source_id, f"{prefix}_COST", run_id, "cost_scale_review", run_id, "record_level", "SPAN_8A78352946DAC1A2DAE0", "The paper demonstrates a patterned-substrate laboratory AC-CVD experiment and reports no quantitative cost.", value_status="review_assessment"),
        ])
        if index == 1:
            tables["evidence_index"].extend([
                evidence_row(source_id, f"{prefix}_TYPE_DIAM", run_id, "yield_quality", product["product_id"], "CNT_type_reported;CNT_type_confirmed;CNT_type_evidence;SWCNT_or_few_wall_evidence_summary;RBM_peak_reported;outer_diameter_range_nm;Raman_ratio_type;characterization_methods", "SPAN_D78136937C076C603506", "Raman shows RBMs below 300 cm-1 and a ca. 1.32 nm derived diameter, while HRTEM gives 3-5 nm."),
                evidence_row(source_id, f"{prefix}_RAMAN_SETUP", run_id, "yield_quality", product["product_id"], "Raman_laser_wavelength_nm;characterization_methods", "SPAN_6B72D7624DBFFD80932E", "Raman characterization used a 532 nm laser and HRTEM was used for wall structure."),
                evidence_row(source_id, f"{prefix}_APP", run_id, "yield_quality", product["product_id"], "application_property_summary", "SPAN_A55CE34BDE34C03A8482", "Field-enhancement factor is ca. 1650 initially and close to 500 in the second and third tests."),
            ])
            issue_id = f"{source_id}_ISS_DIAMETER"
            tables["review_issue_log"].append(issue_row(issue_id, source_id, run_id, "measurement_method_conflict", "yield_quality", product["product_id"], "outer_diameter_range_nm", "Raman-derived diameter (ca. 1.32 nm) and HRTEM diameter (3-5 nm) disagree; both are preserved without selecting one as authoritative.", evidence_ids=f"{prefix}_TYPE_DIAM", severity="high", conflicting_values="Raman ca. 1.32 nm | HRTEM 3-5 nm"))
    write_package(package, tables)
    write_review(package, {
        "source_id": source_id,
        "review_status": "extracted_needs_supervisory_review",
        "reviewer": "Codex",
        "source_identity_checked": True,
        "campaign_reconciliation": {"result_linked_campaigns_in_paper": 3, "extracted_runs": 3, "negative_runs_preserved": 2, "matrix_note": "The positive adjacent-TiN lane and two explicitly reported no-growth spatial regions are kept as separate conditions."},
        "pdf_visual_review": {"completed": False, "pages_checked": [], "not_applicable_reason": "Local source is full HTML rather than PDF."},
        "html_source_review": {"completed": True, "sections_checked": ["2.1 Preparation of Substrates", "2.3 Growth of Vertically Aligned SWNTs", "3.1 Deposition of the Catalysts", "3.2 Growth of SWNTs", "Raman/HRTEM and field-emission results", "4. Conclusions"]},
        "pressure_policy_check": "Atmospheric pressure is explicit and normalized to 101.325 kPa.",
        "cross_run_inheritance_check": "Common fabrication and AC-CVD conditions are shared, while catalyst state and product outcome are isolated by the paper's spatial region descriptions.",
        "unit_policy_check": "1073 K is normalized to approximately 800 C; Raman and HRTEM diameter values are both retained and logged as a conflict.",
    })
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


def build_lit_436402da(context: SourceContext) -> Path:
    """Philippe et al. 2007, 17 current-paper fluidized-bed carbon-growth runs."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    gnfs = [
        (400, "~0.1", "0.14", "0.01", "0.12"),
        (450, "~0.15", "1.11", "0.08", "0.96"),
        (500, "0.4", "5.91", "0.43", "5.12"),
        (550, "0.35", "4.94", "0.36", "4.29"),
        (600, "0.4", "5.33", "0.38", "4.63"),
        (650, "0.3", "4.33", "0.31", "3.76"),
        (700, "0.4", "5.17", "0.37", "4.48"),
        (750, "0.3", "3.86", "0.28", "3.35"),
    ]
    fe_runs = [
        ("2-1", 2.5, 60, 0.5, 500, 60, 160, 120, "0.28", "~0.45", "7.8", "0.56"),
        ("2-2", 2.5, 60, 0.5, 550, 60, 160, 120, "0.55", "0.65", "15.3", "1.10"),
        ("2-3", 2.5, 60, 0.5, 600, 60, 160, 120, "0.95", "1.3", "26.4", "1.90"),
        ("2-4", 2.5, 60, 0.5, 650, 60, 160, 120, "1.35", "1.9", "37.6", "2.70"),
        ("2-5", 2.5, 60, 0.5, 700, 60, 160, 120, "1.28", "1.5", "35.5", "2.55"),
        ("2-6", 2.5, 60, 0.5, 750, 60, 160, 120, "1.23", "1.5", "34.2", "2.46"),
        ("5-1", 5.3, 120, 20, 650, 405, 685, 1200, "40.4", "36.1", "83.2", "2"),
        ("16-1", 16, 120, 200, 650, 11300, 6500, 3800, "535", "40", "39.5", "2.7"),
        ("16-2", 16, 120, 200, 650, 11300, 6500, 3800, "551", "38", "40.7", "2.75"),
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [source_master_row(context, "Current authors' Ni/Al2O3 GNF temperature series, Fe/Al2O3 MWCNT temperature series, and 5.3/16 cm scale-up runs; literature-review Table 1 excluded.")],
        "source_run": [], "catalyst_system": [], "reactor_process_gas": [],
        "yield_quality": [], "cost_scale_review": [], "evidence_index": [],
        "review_issue_log": [],
    }

    def append_common(
        *, code: str, label: str, summary: str, target_track: str,
        metal: str, loading: str, precursor: str, prep_modifier: str,
        reactor_diameter: str, reactor_material: str, reactor_height: str,
        scale: str, cat_mass: str, temp: str, hold: str,
        ethylene: str, nitrogen: str, hydrogen: str,
        product: dict[str, str], result_span: str, index: int,
    ) -> None:
        run = source_run_row(source_id, code, label, summary, target_track=target_track)
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label=f"{loading} wt% {metal}/Al2O3",
            active_metals=metal,
            support_material="Al2O3 powder support",
            precursor_summary=precursor,
            preparation_method="fluidized-bed organometallic CVD",
            preparation_modifier=prep_modifier,
            preparation_detail="organometallic precursor decomposed at 220 C in fluidized Al2O3 under N2; catalyst-preparation pressure 50 Torr",
            phase_or_state_summary=f"ICP metal loading {loading} wt%",
        )
        proc = process_row(
            run_id, 1, "fluidized_bed_CCVD_growth",
            reactor_type="vertical fluidized-bed CVD reactor",
            scale_level=scale,
            reactor_material=reactor_material,
            reactor_size_summary=f"{reactor_diameter} cm internal diameter{'; ' + reactor_height if reactor_height else ''}",
            reactor_setup_summary="gas distributor below fluidized catalyst powder",
            catalyst_loading_mass_g=cat_mass,
            temperature_setpoint_C=temp,
            holding_time_min=hold,
            carbon_source="ethylene",
            carbon_source_flow_original=f"{ethylene} sccm",
            carbon_source_flow_sccm=ethylene,
            reducing_gas="H2",
            reducing_gas_flow_original=f"{hydrogen} sccm",
            reducing_gas_flow_sccm=hydrogen,
            inert_gas="N2",
            inert_gas_flow_original=f"{nitrogen} sccm",
            inert_gas_flow_sccm=nitrogen,
            gas_composition_summary=f"C2H4 {ethylene} sccm; N2 {nitrogen} sccm; H2 {hydrogen} sccm",
            process_note="Growth pressure is not reported in the current paper and remains blank.",
        )
        yld = yield_row(run_id, **product)
        cost = cost_row(
            run_id,
            scale_level_demonstrated=scale,
            scale_level_claimed=("laboratory pilot scale" if scale == "laboratory pilot scale" else "not_reported"),
            quantitative_cost_reported="not_reported",
            scale_evidence_summary=f"Fluidized-bed reactor internal diameter {reactor_diameter} cm; catalyst charge {cat_mass} g.",
        )
        tables["source_run"].append(run); tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].append(proc); tables["yield_quality"].append(yld)
        tables["cost_scale_review"].append(cost)
        prefix = f"{source_id}_EV_{index:02d}"
        tables["evidence_index"].extend([
            evidence_row(source_id, f"{prefix}_CAT", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_20990C8C2C83C65BB56F", "Ni/Al2O3 and Fe/Al2O3 catalyst preparation, organometallic precursors, 220 C decomposition, 50 Torr, and ICP loadings are reported in the Experimental section."),
            evidence_row(source_id, f"{prefix}_PROC", run_id, "reactor_process_gas", proc["process_stage_id"], "record_level", result_span, "The run-resolved table supplies reactor diameter, duration where reported, catalyst mass, temperature, and C2H4/N2/H2 flows."),
            evidence_row(source_id, f"{prefix}_PROC_SETUP", run_id, "reactor_process_gas", proc["process_stage_id"], "reactor_material;reactor_size_summary", ("SPAN_20990C8C2C83C65BB56F" if reactor_diameter == "2.5" else "SPAN_49320820874BB7C3EDE9"), "The Experimental section reports the 2.5 cm by 20 cm quartz reactor and the 5.3/16 cm, 304L stainless-steel scale-up reactors."),
            evidence_row(source_id, f"{prefix}_PROC_CHARGE", run_id, "reactor_process_gas", proc["process_stage_id"], "catalyst_loading_mass_g", ("SPAN_49320820874BB7C3EDE9" if reactor_diameter == "2.5" else result_span), "The current-paper experimental description or run table reports the catalyst charge for this reactor campaign."),
            evidence_row(source_id, f"{prefix}_PROD", run_id, "yield_quality", yld["product_id"], "record_level", result_span, "The run-resolved result table supplies product amount or productivity, ethylene conversion, and final bed height."),
            evidence_row(source_id, f"{prefix}_COST", run_id, "cost_scale_review", run_id, "record_level", result_span, "Reactor diameter and catalyst charge support the demonstrated scale classification; no quantitative cost is reported.", value_status="review_assessment"),
        ])

    index = 0
    for temp, bed, conversion, productivity, activity in gnfs:
        index += 1
        diameter = "50-60" if temp <= 500 else "10-20"
        product = dict(
            primary_yield_metric="carbon productivity per initial catalyst mass",
            yield_original=f"X={productivity} gC/gcatalyst; ethylene conversion {conversion}%; final fixed-bed height {bed} cm; activity {activity} gC/gNi/h",
            yield_definition_original="X is grams of deposited carbon per gram of initial catalyst",
            yield_value_standardized=productivity,
            yield_unit_standardized="gC/gcatalyst",
            carbon_source_conversion_percent=conversion,
            secondary_result_summary=f"Final fixed-bed height {bed} cm; catalytic activity {activity} gC/gNi/h.",
            CNT_type_reported="graphite nanofiber (GNF), not a CNT product",
            CNT_type_confirmed="not_applicable",
            product_mixture_summary="diameter-homogeneous GNF; no additional product observed",
            CNT_type_evidence="TEM identifies graphitic nanofibers rather than nanotubes.",
            outer_diameter_range_nm=diameter,
            morphology="graphite nanofibers",
            characterization_methods="TEM; SEM; Raman; TGA; BET",
            notes="This GNF series is preserved because it is a current-paper comparative carbon-growth campaign; target_track is carbon_nanofiber_production.",
        )
        if temp == 650:
            product.update(
                Raman_ratio_type="I_D/I_G", Raman_ratio_value="0.92",
                purified_product_purity_wt_percent="95",
                purity_basis="post-purification TGA; 5 wt% remaining Ni",
                residue_summary="5 wt% remaining nickel",
                BET_surface_area_product_m2_g="167",
                post_treatment_or_purification="purified product; purification procedure not restated in this result paragraph",
            )
        append_common(
            code=f"GNF_NI_{temp}", label=f"Ni/Al2O3 GNF growth at {temp} C",
            summary=f"0.5 g of 8.4 wt% Ni/Al2O3 in a 2.5 cm fluidized-bed reactor with 60/160/120 sccm C2H4/N2/H2; at {temp} C, GNF productivity was {productivity} gC/gcatalyst.",
            target_track="carbon_nanofiber_production", metal="Ni", loading="8.4",
            precursor="nickelocene", prep_modifier="H2 co-reactant",
            reactor_diameter="2.5", reactor_material="quartz", reactor_height="20 cm height",
            scale="laboratory fluidized-bed", cat_mass="0.5", temp=str(temp), hold="",
            ethylene="60", nitrogen="160", hydrogen="120", product=product,
            result_span="SPAN_38A7E37C4271D21C4320", index=index,
        )
        if temp == 650:
            yld = tables["yield_quality"][-1]; run_id = yld["run_id"]
            tables["evidence_index"].append(evidence_row(source_id, f"{source_id}_EV_{index:02d}_GNF_QUALITY", run_id, "yield_quality", yld["product_id"], "Raman_ratio_type;Raman_ratio_value;purified_product_purity_wt_percent;purity_basis;residue_summary;BET_surface_area_product_m2_g;post_treatment_or_purification;outer_diameter_range_nm;characterization_methods", "SPAN_C9F9D300AE8A97C33FA3", "The purified 650 C GNF has I_D/I_G 0.92, 95% purity, 5% Ni residue, and BET area 167 m2/g; the temperature-dependent diameter range is also reported."))

    for code, diam, hold, cat_mass, temp, ethylene, nitrogen, hydrogen, mass, bed, conversion, productivity in fe_runs:
        index += 1
        is_small = code.startswith("2-")
        is_5 = code == "5-1"
        scale = "laboratory fluidized-bed" if is_small else ("scaled laboratory fluidized-bed" if is_5 else "laboratory pilot scale")
        reactor_material = "quartz" if is_small else "304L stainless steel"
        diameter_for_record = "5.3" if is_5 else str(diam)
        product = dict(
            primary_yield_metric="CNT mass and productivity per initial catalyst mass",
            yield_original=f"CNT produced {mass} g; X={productivity} gC/gcatalyst; ethylene conversion {conversion}%; final fixed-bed height {bed} cm",
            yield_definition_original="CNT produced is recovered carbon nanotube mass; X is grams of deposited carbon per gram of initial catalyst",
            yield_value_standardized=mass,
            yield_unit_standardized="g CNT",
            CNT_yield_per_catalyst_g_gcat=productivity,
            carbon_source_conversion_percent=conversion,
            secondary_result_summary=f"Final fixed-bed height {bed} cm.",
            CNT_type_reported="multi-walled carbon nanotubes",
            CNT_type_confirmed="TEM and Raman characterization reported for the campaign",
            product_mixture_summary=("MWCNT with filamentous-carbon by-product from large catalyst particles" if code == "2-2" else "MWCNT; no additional product quantified"),
            CNT_type_evidence="TEM shows multiwall structure; Raman D and G bands are reported.",
            outer_diameter_range_nm=("10-20" if is_small and temp >= 550 else ""),
            morphology="MWCNT network on fragmented catalyst grains",
            characterization_methods="SEM; TEM; Raman; TGA; BET",
        )
        if code == "2-4":
            product.update(
                Raman_ratio_type="I_D/I_G", Raman_ratio_value="1.02",
                purified_product_purity_wt_percent="98.5",
                purity_basis="post-purification TGA mass loss; 1.5 wt% remaining Fe",
                residue_summary="1.5 wt% remaining iron",
                BET_surface_area_product_m2_g="327",
                post_treatment_or_purification="purified MWCNT product; procedure not restated in this result paragraph",
            )
        if not is_small:
            product["product_mixture_summary"] = "purified MWCNT; TGA/TEM/Raman reported complete selectivity"
            product["CNT_type_evidence"] = "TGA, TEM, and Raman show complete selectivity and structural features matching the 2.5 cm reactor product."
        if code.startswith("16-"):
            product["application_property_summary"] = "Laboratory pilot-scale MWCNT production rate exceeds 260 g/h."
        append_common(
            code=f"MWCNT_FE_{code.replace('-', '_')}", label=f"Fe/Al2O3 MWCNT run {code} at {temp} C",
            summary=f"Run {code}: {cat_mass} g of 9.6 wt% Fe/Al2O3 in a {diameter_for_record} cm fluidized-bed reactor for {hold} min at {temp} C; {mass} g CNT produced and X={productivity} gC/gcatalyst.",
            target_track="CNT_production", metal="Fe", loading="9.6",
            precursor="iron pentacarbonyl", prep_modifier="water-vapor co-reactant",
            reactor_diameter=diameter_for_record, reactor_material=reactor_material,
            reactor_height=("20 cm height" if is_small else "1 m height"),
            scale=scale, cat_mass=str(cat_mass), temp=str(temp), hold=str(hold),
            ethylene=str(ethylene), nitrogen=str(nitrogen), hydrogen=str(hydrogen),
            product=product, result_span="SPAN_BE842B1E8AA6678D95B6", index=index,
        )
        yld = tables["yield_quality"][-1]; run_id = yld["run_id"]
        if is_small and temp >= 550:
            tables["evidence_index"].append(evidence_row(source_id, f"{source_id}_EV_{index:02d}_DIAM", run_id, "yield_quality", yld["product_id"], "CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;outer_diameter_range_nm;morphology;characterization_methods", "SPAN_A88FC8C22F4F2AF78C8F", "The Fe/Al2O3 campaign is identified as graphitic MWCNT; TEM reports homogeneous 10-20 nm external diameters above 550 C."))
        if code == "2-4":
            tables["evidence_index"].append(evidence_row(source_id, f"{source_id}_EV_{index:02d}_QUALITY", run_id, "yield_quality", yld["product_id"], "Raman_ratio_type;Raman_ratio_value;purified_product_purity_wt_percent;purity_basis;residue_summary;BET_surface_area_product_m2_g;post_treatment_or_purification", "SPAN_A88FC8C22F4F2AF78C8F", "Purified 650 C MWCNT has I_D/I_G 1.02, 98.5% TGA mass loss, 1.5% Fe residue, and BET area 327 m2/g."))
        if not is_small:
            span = "SPAN_7EAA8A198D4856851B17" if is_5 else "SPAN_A1523B938D73F59E4570"
            fields = "CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;characterization_methods"
            if code.startswith("16-"):
                fields += ";application_property_summary"
            tables["evidence_index"].append(evidence_row(source_id, f"{source_id}_EV_{index:02d}_SCALE_QUALITY", run_id, "yield_quality", yld["product_id"], fields, span, "Scale-up products are reported completely selective by TGA/TEM/Raman; the 16 cm pilot exceeds 260 g/h."))

    write_package(package, tables)
    write_review(package, {
        "source_id": source_id, "review_status": "extracted_needs_supervisory_review",
        "reviewer": "Codex", "source_identity_checked": True,
        "campaign_reconciliation": {"result_linked_campaigns_in_paper": 17, "extracted_runs": 17, "negative_runs_preserved": 0, "matrix_note": "All eight Ni/Al2O3 GNF temperature rows, six 2.5 cm Fe/Al2O3 rows, one 5.3 cm scale-up row, and two 16 cm reproducibility rows are retained. Literature-review Table 1 is excluded."},
        "pdf_visual_review": {"completed": True, "pages_checked": [7, 9, 10, 11], "objects_checked": ["Table 2 Ni series", "Tables 3-4 Fe run matrix and results", "Figures 9-10 SEM/TEM", "16 cm scale-up discussion"]},
        "pressure_policy_check": "Catalyst-preparation pressure of 50 Torr is kept only in catalyst preparation detail. CNT/GNF growth pressure is not reported and remains blank.",
        "cross_run_inheritance_check": "650 C Raman/TGA/BET values are assigned only to the named 650 C small-reactor runs; scale-up runs receive only the explicitly stated complete-selectivity/structural-equivalence claims.",
        "unit_policy_check": "Table X values are preserved as gC/gcatalyst; activity values in gC/gMetal/h are not misfiled as catalyst-mass productivity.",
    })
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


def build_lit_4421747a(context: SourceContext) -> Path:
    """Qi et al. 2016, four-temperature Co@CNTs-graphene hybrid series."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    runs = [
        {"code": "G400", "temp": 400, "mass": "0.033", "reps": "1.7; 1.5; 1.8", "ms": "23.9", "rl": "-65.6", "morph": "graphene sheets, CNTs, and dispersed Co nanoparticles", "span": "SPAN_B4FF15C924C721E29863"},
        {"code": "G450", "temp": 450, "mass": "0.055", "reps": "2.8; 2.8; 2.7", "ms": "21.2", "rl": "-58.1", "morph": "Co@CNTs-graphene hybrid with more CNT than G400", "span": "SPAN_52E8E492A4CAC7A4669B"},
        {"code": "G500", "temp": 500, "mass": "0.075", "reps": "3.7; 3.8; 3.8", "ms": "18.6", "rl": "-41.1", "morph": "hollow CNTs with Co at CNT tips and in graphene sheets; more CNT than G400/G450", "span": "SPAN_52E8E492A4CAC7A4669B"},
        {"code": "G550", "temp": 550, "mass": "0.1893", "reps": "9.6; 9.3; 9.5", "ms": "10.9", "rl": "-47.5", "morph": "CNT-rich Co@CNTs-graphene hybrid; graphene seldom observed", "span": "SPAN_DBC8BBB8886F0CF91753"},
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [source_master_row(context, "Complete G400/G450/G500/G550 temperature series, triplicate total-product yields, microscopy, magnetization, and microwave-absorption results.")],
        "source_run": [], "catalyst_system": [], "reactor_process_gas": [],
        "yield_quality": [], "cost_scale_review": [], "evidence_index": [],
        "review_issue_log": [],
    }
    for index, item in enumerate(runs, start=1):
        run = source_run_row(
            source_id, item["code"], f"{item['code']} acetylene pyrolysis at {item['temp']} C",
            f"0.02 g Co3O4/RGO was exposed to acetylene for 2 h at atmospheric pressure and {item['temp']} C; about {item['mass']} g of Co@CNTs-graphene hybrid was collected.",
            data_type="experimental_condition",
        )
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label="purchased Co3O4/reduced-graphene-oxide catalyst precursor",
            active_metals="Co (formed in situ from Co3O4)",
            support_material="reduced graphene oxide",
            precursor_summary="Co3O4/RGO composite purchased from XFNANO",
            preparation_method="used as purchased without further purification",
            phase_or_state_summary="Co3O4 nanoparticles anchored on RGO before acetylene exposure; reduced to Co during reaction",
        )
        proc = process_row(
            run_id, 1, "acetylene_CVD_growth",
            reactor_type="quartz reaction tube in tube furnace",
            reactor_setup_summary="0.02 g Co3O4/RGO dispersed on a ceramic plate inside the quartz tube",
            catalyst_loading_mass_g="0.02",
            temperature_setpoint_C=str(item["temp"]),
            holding_time_min="",
            cooling_condition="cooled to room temperature in Ar",
            pressure_original="atmospheric pressure",
            pressure_kPa="",
            carbon_source="acetylene",
            inert_gas="Ar during heating and cooling; flow not reported",
            gas_composition_summary="acetylene introduced at the selected temperature; Ar used for heating and cooling",
            process_note="Acetylene pyrolysis was carried out for 2 h; acetylene and argon flow rates are not reported.",
        )
        product = yield_row(
            run_id,
            primary_yield_metric="total collected Co@CNTs-graphene hybrid mass and m_total/m_catalyst replicate ratios",
            yield_original=f"about {item['mass']} g product; triplicate total-product yields {item['reps']} gtotal/gcatalyst",
            yield_definition_original="Table 1 defines yield as m_total/m_catalyst; values describe total hybrid, not isolated CNT mass",
            yield_calculation_method="three reported m_total/m_catalyst measurements per nominal temperature",
            yield_standardization_note="Triplicate total-hybrid ratios are preserved without averaging and are not relabeled as CNT yield.",
            secondary_result_summary=f"Saturation magnetization: {item['ms']} emu/g.",
            CNT_type_reported="carbon nanotubes; wall count not reported",
            CNT_type_confirmed="hollow CNT structure confirmed by TEM; wall count not established",
            product_mixture_summary="ternary Co@CNTs-graphene hybrid; component mass fractions not fully quantified",
            CNT_type_evidence="SEM/TEM show CNTs and Co nanoparticles encapsulated by CNT/graphitic layers.",
            morphology=item["morph"],
            characterization_methods="XRD; Raman; FTIR; SEM; TEM; EDS; magnetometry; microwave network analysis",
            application_property_summary=f"Saturation magnetization {item['ms']} emu/g; minimum microwave reflection loss approximately {item['rl']} dB.",
            notes="Collected mass includes Co, CNTs, and graphene and must not be interpreted as pure CNT mass.",
        )
        cost = cost_row(
            run_id,
            scale_level_demonstrated="laboratory tube-furnace batch",
            scale_level_claimed="large-scale synthesis claimed by authors",
            scale_evidence_summary=f"0.02 g catalyst precursor and about {item['mass']} g collected hybrid for this run",
            scale_up_issue="The paper uses 'large-scale' language, but the reported batch contains only 0.02 g catalyst precursor and sub-gram product.",
            quantitative_cost_reported="not_reported",
        )
        tables["source_run"].append(run); tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].append(proc); tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        prefix = f"{source_id}_EV_{index:02d}"
        scale_issue = f"{source_id}_ISS_SCALE_{index:02d}"
        tables["evidence_index"].extend([
            evidence_row(source_id, f"{prefix}_CAT", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_5BFCEEA16FBBDACFA97B", "The Co3O4/RGO precursor was purchased and used without further purification; 0.02 g was placed on a ceramic plate in the quartz tube."),
            evidence_row(source_id, f"{prefix}_PROC", run_id, "reactor_process_gas", proc["process_stage_id"], "record_level", "SPAN_5BFCEEA16FBBDACFA97B", f"The method reports the {item['temp']} C, 2 h atmospheric acetylene run, Ar heating/cooling, 0.02 g precursor, and product mass."),
            evidence_row(source_id, f"{prefix}_YIELD_METHOD", run_id, "yield_quality", product["product_id"], "primary_yield_metric;yield_original;yield_definition_original;yield_calculation_method;yield_standardization_note;notes", "SPAN_5BFCEEA16FBBDACFA97B", f"Methods report about {item['mass']} g collected product from 0.02 g precursor; Table 1 supplies three total-product/catalyst ratios."),
            evidence_row(source_id, f"{prefix}_YIELD_REPS", run_id, "yield_quality", product["product_id"], "primary_yield_metric;yield_original;yield_definition_original;yield_calculation_method;yield_standardization_note", "SPAN_5D4304A7948E156F1A95", f"Table 1 reports triplicate m_total/m_catalyst values {item['reps']} for {item['code']}.", linked_issue_id=(f"{source_id}_ISS_G450_TEMP" if item["code"] == "G450" else "not_applicable")),
            evidence_row(source_id, f"{prefix}_PROD", run_id, "yield_quality", product["product_id"], "CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;morphology;characterization_methods", item["span"], f"Run-specific SEM/TEM observations identify the {item['code']} Co@CNTs-graphene hybrid morphology."),
            evidence_row(source_id, f"{prefix}_MAG", run_id, "yield_quality", product["product_id"], "secondary_result_summary;application_property_summary", "SPAN_5D4304A7948E156F1A95", f"Table 1 reports saturation magnetization {item['ms']} emu/g for {item['code']}."),
            evidence_row(source_id, f"{prefix}_RL", run_id, "yield_quality", product["product_id"], "application_property_summary", "SPAN_8FA53BB68C002ADD76C5", f"The abstract reports minimum reflection loss {item['rl']} dB for the {item['temp']} C hybrid."),
            evidence_row(source_id, f"{prefix}_COST", run_id, "cost_scale_review", run_id, "record_level", "SPAN_5BFCEEA16FBBDACFA97B", "The 0.02 g precursor and sub-gram product mass demonstrate laboratory batch scale despite the paper's large-scale wording; no cost is reported.", value_status="review_assessment", linked_issue_id=scale_issue),
        ])
        tables["review_issue_log"].append(issue_row(
            scale_issue, source_id, run_id, "scale_claim_not_demonstrated", "cost_scale_review", run_id, "scale_up_issue",
            "The authors describe large-scale synthesis, but the disclosed experiment uses 0.02 g catalyst precursor and produces less than 0.2 g total hybrid.",
            evidence_ids=f"{prefix}_COST", severity="medium",
        ))
        if item["code"] == "G450":
            tables["review_issue_log"].append(issue_row(
                f"{source_id}_ISS_G450_TEMP", source_id, run_id, "internal_table_label_conflict",
                "reactor_process_gas", proc["process_stage_id"], "temperature_setpoint_C",
                "Methods, abstract, sample code, and surrounding series identify G450 as 450 C, while printed Table 1 labels its temperature 550 C. The run is retained at 450 C and the printed conflict is logged.",
                evidence_ids=f"{prefix}_PROC;{prefix}_YIELD_REPS", severity="high",
                conflicting_values="450 C in methods/series | 550 C in printed Table 1",
            ))
    write_package(package, tables)
    write_review(package, {
        "source_id": source_id, "review_status": "extracted_needs_supervisory_review",
        "reviewer": "Codex", "source_identity_checked": True,
        "campaign_reconciliation": {"result_linked_campaigns_in_paper": 4, "extracted_runs": 4, "negative_runs_preserved": 0, "matrix_note": "Four nominal temperature samples are retained. Three yield measurements per sample are preserved within the run rather than assigned fabricated replicate identities."},
        "pdf_visual_review": {"completed": True, "pages_checked": [3, 4, 5, 6, 13], "objects_checked": ["Figures 2-5 XRD/Raman/SEM/TEM", "printed Table 1", "material-preparation paragraph"]},
        "pressure_policy_check": "Atmospheric pressure is explicit and retained verbatim; gas flows remain unreported and no numeric pressure default is introduced.",
        "cross_run_inheritance_check": "Temperature-specific product masses, yield triplicates, magnetization, morphology, and reflection loss are isolated by G400/G450/G500/G550.",
        "unit_policy_check": "m_total/m_catalyst is retained as total-hybrid yield and is not placed in the CNT-yield field.",
        "conflict_check": "The visually confirmed G450/550 Table 1 temperature mislabel is retained as a high-severity conflict rather than silently corrected.",
    })
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


def build_lit_4b3d3c5c(context: SourceContext) -> Path:
    """Wei et al., remote-plasma ethanol SWCNT power and temperature matrices."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    chirality = {
        675: "(7,3) 18.9%; (6,5) 24.9%; (7,5) 10.7%; (8,4) 9.5%; (7,6) 5.7%",
        725: "(7,3) 12.6%; (6,5) 25.8%; (7,5) 14.9%; (8,4) 10.6%; (7,6) 6.2%",
        750: "(7,3) 5.5%; (6,5) 24.0%; (7,5) 20.8%; (8,4) 17.0%; (7,6) 7.9%",
        775: "(6,5) 13.3%; (7,5) 30.1%; (8,4) 20.2%; (7,6) 11.1%",
        800: "(6,5) 10.4%; (7,5) 26.6%; (8,4) 21.7%; (7,6) 13.4%",
        825: "(6,5) 6.4%; (7,5) 24.6%; (8,4) 23.4%; (7,6) 16.1%",
    }
    conditions = [
        {"code": "P0_T775", "power": 0, "temp": 775, "mix": "47.8 wt% amorphous/defective carbon; 52.2 wt% SWCNT; no MWCNT or graphite detected", "special": "thermal ethanol decomposition produced SWCNT bundles without plasma"},
        {"code": "P200_T775", "power": 200, "temp": 775, "mix": "40.5 wt% amorphous/defective carbon; 59.5 wt% SWCNT; no MWCNT or graphite detected", "special": "optimum reported condition; (7,5) plus (8,4) exceed 50% of observed semiconducting species"},
        {"code": "P250_T775", "power": 250, "temp": 775, "mix": "53.2 wt% amorphous/defective carbon; 37.6 wt% SWCNT; 4.2 wt% MWCNT; 5.0 wt% graphite", "special": "highest power produced MWCNT and graphite impurities"},
        {"code": "P200_T625", "power": 200, "temp": 625, "mix": "few SWCNTs; weak RBM signal", "special": "low-growth endpoint"},
        {"code": "P200_T675", "power": 200, "temp": 675, "mix": "SWCNT product with PL-resolved chirality distribution", "special": ""},
        {"code": "P200_T725", "power": 200, "temp": 725, "mix": "SWCNT product with PL-resolved chirality distribution", "special": "(6,5) was the major named species"},
        {"code": "P200_T750", "power": 200, "temp": 750, "mix": "SWCNT product with PL-resolved chirality distribution", "special": "minimum amorphous-carbon formation indicated by D/G trend"},
        {"code": "P200_T800", "power": 200, "temp": 800, "mix": "SWCNT product with PL-resolved chirality distribution", "special": "larger-diameter species dominate relative to low-temperature samples"},
        {"code": "P200_T825", "power": 200, "temp": 825, "mix": "SWCNT product with PL-resolved chirality distribution", "special": "larger-diameter species dominate relative to low-temperature samples"},
        {"code": "P200_T875", "power": 200, "temp": 875, "mix": "few SWCNTs; weak RBM signal", "special": "high-temperature low-growth endpoint"},
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [source_master_row(context, "All unique 775 C plasma-power conditions and 200 W temperature-series conditions, including low-growth endpoints and Tables 1-2.")],
        "source_run": [], "catalyst_system": [], "reactor_process_gas": [],
        "yield_quality": [], "cost_scale_review": [], "evidence_index": [],
        "review_issue_log": [],
    }
    for index, item in enumerate(conditions, start=1):
        temp = item["temp"]; power = item["power"]
        run = source_run_row(
            source_id, item["code"], f"Co-MCM-41 ethanol growth at {temp} C and {power} W",
            f"After H2 reduction, 80 mg of 1 wt% Co-MCM-41 was exposed to remote-plasma ethanol for 30 min at {temp} C and {power} W; {item['mix']}.",
            data_type="experimental_condition",
        )
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label="1 wt% Co incorporated MCM-41",
            active_metals="Co",
            support_material="MCM-41 silica",
            preparation_method="prepared by prior published procedure; current paper reports quality controls",
            preparation_detail="current-paper quality controls: BET surface area >1000 m2/g; pore-size-distribution FWHM <0.2 nm",
            calcination_condition="air at 500 C",
            reduction_condition="heated from room temperature to 500 C at 10 C/min under 80 sccm atmospheric-pressure H2",
            phase_or_state_summary="fresh Co is incorporated in MCM-41; no Co3O4/CoO features below 500 C in TPR",
        )
        reduction = process_row(
            run_id, 1, "catalyst_reduction",
            reactor_type="quartz-tube remote-plasma CVD system",
            reactor_setup_summary="80 mg catalyst in boat downstream of the remote plasma source",
            temperature_setpoint_C="500",
            heating_rate_C_min="10",
            pressure_original="atmospheric pressure during H2 reduction",
            reducing_gas="H2",
            reducing_gas_flow_original="80 sccm",
            reducing_gas_flow_sccm="80",
            cooling_condition="H2 purged with Ar after reduction",
        )
        growth = process_row(
            run_id, 2, ("thermal_ethanol_CVD_growth" if power == 0 else "remote_plasma_ethanol_CVD_growth"),
            reactor_type="quartz-tube remote-plasma CVD system",
            reactor_setup_summary="ethanol vapor passes through remote plasma zone before reaching catalyst boat",
            temperature_setpoint_C=str(temp),
            holding_time_min="30",
            pressure_original="reactor evacuated to 0.1 mbar before plasma; ethanol reservoir operated at 2 mbar",
            carbon_source="ethanol vapor",
            inert_gas="Ar purge/cooling; flow not reported",
            gas_composition_summary="ethanol vapor feed; no feed flow reported",
            process_note=f"remote plasma power {power} W; each parameter set repeated at least three times",
        )
        chirality_summary = chirality.get(temp, "") if power == 200 else ""
        diameter = ("0.70-0.90" if temp in {675, 725, 750} else ("0.76-0.90" if temp in {775, 800, 825} and power == 200 else ""))
        product = yield_row(
            run_id,
            primary_yield_metric="qualitative SWCNT abundance and run-specific carbon-species/chirality composition",
            yield_original="no mass yield reported",
            yield_definition_original="SEM/Raman/absorption/PL/TGA-resolved product abundance and composition",
            yield_standardization_note="No gravimetric CNT yield or carbon conversion was reported.",
            secondary_result_summary=(f"Major-semiconducting-species PL shares: {chirality_summary}. {item['special']}" if chirality_summary else item["special"]),
            CNT_type_reported="single-walled carbon nanotubes",
            CNT_type_confirmed="RBM, resonant absorption, and PL features confirm SWCNTs",
            product_mixture_summary=item["mix"],
            CNT_type_evidence="RBM peaks, split G band, resonant S11/S22 absorption, and PL-assigned (n,m) species",
            SWCNT_or_few_wall_evidence_summary="SWCNT Raman RBM and PL chirality assignments reported",
            RBM_peak_reported=("weak" if temp in {625, 875} else "present"),
            outer_diameter_range_nm=diameter,
            morphology="SWCNT bundles on Co-MCM-41 catalyst",
            Raman_ratio_type="D/G qualitative trend; numeric graph values not transcribed",
            characterization_methods="SEM; Raman; UV-vis-NIR absorption; PL; TGA",
            notes="At least three syntheses were performed per parameter set, but replicate-level raw values were not reported.",
        )
        cost = cost_row(run_id, scale_level_demonstrated="laboratory quartz-tube batch", scale_level_claimed="not_reported", quantitative_cost_reported="not_reported")
        tables["source_run"].append(run); tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].extend([reduction, growth]); tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        prefix = f"{source_id}_EV_{index:02d}"
        condition_span = ("SPAN_3D4AC8CB2919C48129D2" if temp in chirality and power == 200 else ("SPAN_987754437CA186A993A3" if temp == 775 and power in {0, 250} else "SPAN_BE7013BE34693C28C6BD"))
        tables["evidence_index"].extend([
            evidence_row(source_id, f"{prefix}_CAT", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_DDDA3B057CDE2D2DBC1C", "The paper reports 1 wt% Co-MCM-41, 500 C calcination, >1000 m2/g surface area, <0.2 nm pore-distribution FWHM, and 80 mg catalyst charge."),
            evidence_row(source_id, f"{prefix}_RED", run_id, "reactor_process_gas", reduction["process_stage_id"], "record_level", "SPAN_3F920F31FE643700C3EA", "Reduction uses atmospheric H2 at 80 sccm while heating to 500 C at 10 C/min, followed by Ar purge."),
            evidence_row(source_id, f"{prefix}_GROW_COMMON", run_id, "reactor_process_gas", growth["process_stage_id"], "reactor_type;reactor_setup_summary;holding_time_min;pressure_original;carbon_source;inert_gas;gas_composition_summary", "SPAN_3F920F31FE643700C3EA", "Growth uses ethanol vapor for 30 min after evacuation to 0.1 mbar, with the ethanol reservoir at 2 mbar; cooling is under Ar."),
            evidence_row(source_id, f"{prefix}_GROW_COND", run_id, "reactor_process_gas", growth["process_stage_id"], "stage_type;temperature_setpoint_C;process_note", ("SPAN_ED0FC218FF560C28D62B" if temp == 775 and power in {0, 200, 250} else condition_span), f"The run matrix identifies {temp} C and {power} W; the Methods state at least three repeats per parameter set."),
            evidence_row(source_id, f"{prefix}_PROD_COMMON", run_id, "yield_quality", product["product_id"], "primary_yield_metric;yield_original;yield_definition_original;yield_standardization_note;CNT_type_reported;CNT_type_confirmed;CNT_type_evidence;SWCNT_or_few_wall_evidence_summary;RBM_peak_reported;morphology;Raman_ratio_type;characterization_methods;notes", "SPAN_F9232808C6635B2C1A72", "SEM, Raman, absorption, and PL identify SWCNTs under the studied conditions; no mass yield is reported."),
            evidence_row(source_id, f"{prefix}_PROD_COND", run_id, "yield_quality", product["product_id"], "secondary_result_summary;product_mixture_summary;outer_diameter_range_nm", condition_span, "The run-specific TGA composition, low-growth endpoint, or Table 2 chirality distribution is preserved for this condition."),
            evidence_row(source_id, f"{prefix}_COST", run_id, "cost_scale_review", run_id, "record_level", "SPAN_DDDA3B057CDE2D2DBC1C", "The 80 mg catalyst charge demonstrates laboratory batch scale; no cost is reported.", value_status="review_assessment"),
        ])
        if temp == 775 and power == 200:
            tables["evidence_index"].append(evidence_row(source_id, f"{prefix}_PROD_MIX", run_id, "yield_quality", product["product_id"], "product_mixture_summary", "SPAN_987754437CA186A993A3", "Table 1 reports 40.5 wt% amorphous/defective carbon and 59.5 wt% SWCNT with no detected MWCNT or graphite for 200 W."))
    write_package(package, tables)
    write_review(package, {
        "source_id": source_id, "review_status": "extracted_needs_supervisory_review", "reviewer": "Codex", "source_identity_checked": True,
        "campaign_reconciliation": {"result_linked_campaigns_in_paper": 10, "extracted_runs": 10, "negative_runs_preserved": 2, "matrix_note": "Three unique 775 C power conditions and eight 200 W temperature conditions are retained, with the shared 775 C/200 W condition included only once. 625 and 875 C low-growth endpoints are preserved."},
        "pdf_visual_review": {"completed": True, "pages_checked": [5, 8, 12, 14, 17, 19], "objects_checked": ["RPE-CVD schematic and method", "Figure 2 condition labels", "Table 1 carbon composition", "Figure 7 temperature Raman series", "Table 2 chirality matrix", "conclusion"]},
        "pressure_policy_check": "Atmospheric H2 reduction, 0.1 mbar reactor evacuation, and 2 mbar ethanol-reservoir pressure are kept as distinct contexts; no single growth pressure is invented.",
        "cross_run_inheritance_check": "TGA composition is limited to the three measured power conditions; Table 2 chirality percentages are limited to its six temperatures; low-growth endpoints receive only their reported qualitative observations.",
        "unit_policy_check": "The 80 mg charge is preserved in narrative/setup rather than silently normalized into a g-only field; graph-only D/G values are not digitized.",
    })
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


def build_lit_5925fb1b(context: SourceContext) -> Path:
    """Konno et al. 2013, biased-H2 activation-time matrix on Fe/Si."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    production = {
        0: {"yield": "2.6", "shape": "mainly particulate deposited carbon", "cnt": "not_observed", "length": "", "diam": "", "raman": ""},
        1: {"yield": "11.3", "shape": "fibrous vertically grown product", "cnt": "multi-walled carbon nanotubes", "length": "15.4 micrometres", "diam": "15.4", "raman": "0.71"},
        5: {"yield": "6.3", "shape": "fibrous vertically grown product", "cnt": "multi-walled carbon nanotubes", "length": "21.7 micrometres", "diam": "12.6", "raman": "0.68"},
        10: {"yield": "15.8", "shape": "fibrous vertically grown product", "cnt": "multi-walled carbon nanotubes", "length": "30.7 micrometres", "diam": "22.5", "raman": "0.56"},
        20: {"yield": "22.0", "shape": "fibrous vertically grown product", "cnt": "multi-walled carbon nanotubes", "length": "28.5 micrometres", "diam": "15.3", "raman": "0.52"},
        30: {"yield": "20.7", "shape": "fibrous vertically grown product", "cnt": "multi-walled carbon nanotubes", "length": "24.6 micrometres", "diam": "9.8", "raman": "0.72"},
    }
    conditions = [0, 1, 5, 10, 15, 20, 30]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [source_master_row(context, "Six methane-decomposition runs from Table 1 plus the separate 15 min catalyst-activation microscopy condition; figures and internal text conflicts reviewed.")],
        "source_run": [], "catalyst_system": [], "reactor_process_gas": [],
        "yield_quality": [], "cost_scale_review": [], "evidence_index": [],
        "review_issue_log": [],
    }
    for index, treatment in enumerate(conditions, start=1):
        is_activation_only = treatment == 15
        result = production.get(treatment)
        run = source_run_row(
            source_id,
            (f"ACT_{treatment}_CHAR" if is_activation_only else f"H2_{treatment}_GROWTH"),
            (f"Fe/Si activation-only microscopy at {treatment} min" if is_activation_only else f"Methane plasma growth after {treatment} min biased-H2 activation"),
            (
                "Catalyst surface after 15 min biased H2 plasma was characterized by SEM; no corresponding methane-growth product row is reported."
                if is_activation_only
                else f"Fe/Si received {treatment} min biased-H2 activation before 30 min methane/H2 microwave-plasma growth at 600 C; deposited-carbon yield {result['yield']} gC/gcatalyst and product {result['cnt']}."
            ),
            data_type=("catalyst_characterization_condition" if is_activation_only else "experimental_condition"),
            target_track=("catalyst_activation" if is_activation_only else "CNT_production"),
        )
        run_id = run["run_id"]
        state = (
            "untreated 10 nm Fe film on Si" if treatment == 0 else
            "lumpy Fe surface after 1 min biased-H2 plasma" if treatment == 1 else
            "cohered Fe surface after 5-10 min biased-H2 plasma" if treatment in {5, 10} else
            "Fe particles formed after more than 10 min biased-H2 plasma; particle size decreases with further treatment"
        )
        catalyst = catalyst_row(
            run_id,
            catalyst_label="10 nm RF-sputtered Fe film on Si wafer",
            active_metals="Fe",
            support_material="10 mm x 10 mm silicon wafer",
            preparation_method="RF sputtering at 20 W",
            preparation_detail="10 nm Fe deposited on Si; catalyst positioned 650 mm from waveguide",
            activation_condition=("no biased-H2 activation" if treatment == 0 else f"{treatment} min, 500 W microwave, -150 V bias, 550 C, H2 80 ml/min, initial pressure 180 Pa"),
            phase_or_state_summary=state,
        )
        activation = process_row(
            run_id, 1, ("no_plasma_activation" if treatment == 0 else "biased_hydrogen_plasma_activation"),
            reactor_type="low-pressure flow-type remote microwave-plasma reactor",
            reactor_setup_summary="Fe/Si catalyst 650 mm from waveguide",
            temperature_setpoint_C="550",
            holding_time_min=str(treatment),
            pressure_original="initial pressure 180 Pa",
            reducing_gas="H2",
            reducing_gas_flow_original="80 ml/min",
            gas_composition_summary="H2 activation gas",
            process_note=("no biased activation; treatment time 0 min" if treatment == 0 else "500 W microwave; -150 V bias"),
        )
        stages = [activation]
        if not is_activation_only:
            growth = process_row(
                run_id, 2, "methane_microwave_plasma_decomposition",
                reactor_type="low-pressure flow-type remote microwave-plasma reactor",
                reactor_setup_summary="Fe/Si catalyst heated under non-biased conditions",
                temperature_setpoint_C="600",
                holding_time_min="30",
                pressure_original="initial pressure 254 Pa",
                carbon_source="methane",
                reducing_gas="H2 cofeed",
                total_flow_original="100 ml/min",
                gas_composition_summary="CH4:H2 molar ratio 1:4; combined flow 100 ml/min",
                process_note="500 W microwave field; component flow rates not separately reported",
            )
            stages.append(growth)
            product = yield_row(
                run_id,
                primary_yield_metric="deposited carbon mass per Fe/Si catalyst mass",
                yield_original=f"{result['yield']} gC/gcatalyst deposited carbon",
                yield_definition_original="amount of deposited carbon divided by weight of Fe/Si catalyst",
                yield_value_standardized=result["yield"],
                yield_unit_standardized="gC/gcatalyst",
                CNT_yield_per_catalyst_g_gcat=(result["yield"] if treatment > 0 else ""),
                yield_standardization_note=("Table identifies fibrous multi-walled CNT product." if treatment > 0 else "Deposited carbon is mainly particulate and is not counted as CNT yield."),
                secondary_result_summary="Run-resolved methane conversion and hydrogen-distribution values are figure-only and are not digitized.",
                CNT_type_reported=result["cnt"],
                CNT_type_confirmed=("parallel graphitic walls confirmed by TEM" if treatment > 0 else "no CNT structure reported"),
                product_mixture_summary=("MWCNT deposited carbon; non-CNT fraction not quantified" if treatment > 0 else "mainly particulate carbon"),
                CNT_type_evidence=("Table 1 and TEM identify multi-walled structure" if treatment > 0 else "Table 1 reports no CNT shape/structure"),
                outer_diameter_mean_nm=result["diam"],
                length_summary=result["length"],
                morphology=result["shape"],
                alignment_or_array=("vertical growth on Fe surface" if treatment > 0 else "not_applicable"),
                Raman_ratio_type=("I_D/I_G" if treatment > 0 else "not_reported"),
                Raman_ratio_value=result["raman"],
                characterization_methods="SEM; TEM; Raman; gas chromatography",
            )
        else:
            product = yield_row(
                run_id,
                primary_yield_metric="not_applicable; catalyst-activation microscopy only",
                yield_original="no methane-growth product result reported at 15 min activation",
                yield_definition_original="not_applicable",
                yield_standardization_note="This condition is retained solely to preserve the catalyst-surface activation matrix.",
                CNT_type_reported="not_reported",
                CNT_type_confirmed="not_applicable",
                product_mixture_summary="not_reported",
                CNT_type_evidence="not_applicable; catalyst-activation microscopy only and no growth product reported",
                characterization_methods="SEM of Fe catalyst surface",
            )
        cost = cost_row(run_id, scale_level_demonstrated="laboratory wafer reactor", scale_level_claimed="not_reported", quantitative_cost_reported="not_reported")
        tables["source_run"].append(run); tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].extend(stages); tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        prefix = f"{source_id}_EV_{index:02d}"
        tables["evidence_index"].extend([
            evidence_row(source_id, f"{prefix}_CAT_BASE", run_id, "catalyst_system", catalyst["catalyst_id"], "catalyst_label;active_metals;support_material;preparation_method;preparation_detail;activation_condition", "SPAN_827A3B1DF2AD78200C5A", "Methods report the 10 mm square Si wafer, 10 nm Fe film, 20 W RF sputtering, 650 mm placement, and biased-H2 activation conditions."),
            evidence_row(source_id, f"{prefix}_CAT_STATE", run_id, "catalyst_system", catalyst["catalyst_id"], "phase_or_state_summary", "SPAN_7700D778413AE7D26361", "SEM describes the treatment-time-dependent Fe surface as lumpy, cohered, or particulate."),
            evidence_row(source_id, f"{prefix}_ACT", run_id, "reactor_process_gas", activation["process_stage_id"], "record_level", "SPAN_827A3B1DF2AD78200C5A", "Activation uses H2 at 80 ml/min, 180 Pa initial pressure, 500 W microwave, -150 V, 550 C, and the run-specific treatment time."),
            evidence_row(source_id, f"{prefix}_COST", run_id, "cost_scale_review", run_id, "record_level", "SPAN_827A3B1DF2AD78200C5A", "The 10 mm square wafer setup demonstrates laboratory scale; no cost is reported.", value_status="review_assessment"),
        ])
        if is_activation_only:
            tables["evidence_index"].append(evidence_row(source_id, f"{prefix}_PROD_NA", run_id, "yield_quality", product["product_id"], "record_level", "SPAN_7700D778413AE7D26361", "The 15 min condition appears in catalyst-surface SEM as an activation-only condition; no methane-growth product is assigned."))
        else:
            tables["evidence_index"].extend([
                evidence_row(source_id, f"{prefix}_GROW", run_id, "reactor_process_gas", growth["process_stage_id"], "record_level", "SPAN_827A3B1DF2AD78200C5A", "Methane/H2 (1:4) at 100 ml/min and initial 254 Pa is exposed to 500 W microwave for 30 min with catalyst at 600 C."),
                evidence_row(source_id, f"{prefix}_PROD", run_id, "yield_quality", product["product_id"], "record_level", "SPAN_78D4407043F3C31BB316", "Table 1 supplies treatment-linked deposited-carbon yield, product shape/structure, CNT length in micrometres, diameter in nanometres, and I_D/I_G."),
            ])
            if treatment == 10:
                tables["review_issue_log"].append(issue_row(
                    f"{source_id}_ISS_LENGTH_UNIT", source_id, run_id, "internal_unit_conflict", "yield_quality", product["product_id"], "length_summary",
                    "Printed Table 1 labels CNT length in micrometres and gives 30.7 at 10 min, while abstract/results prose call the maximum length 30.7 nm. The table unit is retained and the conflict is not silently resolved.",
                    evidence_ids=f"{prefix}_PROD", severity="high", conflicting_values="30.7 micrometres in Table 1 | 30.7 nm in prose",
                ))
            if treatment == 20:
                tables["review_issue_log"].append(issue_row(
                    f"{source_id}_ISS_MAX_YIELD_TIME", source_id, run_id, "internal_run_assignment_conflict", "yield_quality", product["product_id"], "yield_original",
                    "Table 1 and main results assign 22.0 gC/gcatalyst to 20 min, whereas the conclusion assigns 22 gC/gcatalyst to 10 min. The table-linked 20 min value is retained.",
                    evidence_ids=f"{prefix}_PROD", severity="high", conflicting_values="20 min in table/main results | 10 min in conclusion",
                ))
            if treatment == 5:
                tables["review_issue_log"].append(issue_row(
                    f"{source_id}_ISS_CH4_CONVERSION", source_id, run_id, "internal_result_conflict", "yield_quality", product["product_id"], "secondary_result_summary",
                    "The abstract reports methane conversion up to 93% at 5 min, while the main text/figure describes approximately 83% decreasing toward 76%. No exact conversion is assigned to the run.",
                    evidence_ids=f"{prefix}_PROD", severity="high", conflicting_values="93% at 5 min in abstract | about 83-to-76% trend in main text/figure",
                ))
    write_package(package, tables)
    write_review(package, {
        "source_id": source_id, "review_status": "extracted_needs_supervisory_review", "reviewer": "Codex", "source_identity_checked": True,
        "campaign_reconciliation": {"result_linked_campaigns_in_paper": 7, "extracted_runs": 7, "negative_runs_preserved": 1, "matrix_note": "Six Table 1 methane-growth runs are retained, including the 0 min non-CNT result. The separate 15 min activation-only SEM condition is preserved without fabricating a growth product."},
        "pdf_visual_review": {"completed": True, "pages_checked": [2, 3, 4, 5], "objects_checked": ["experimental apparatus/method", "Figures 2-7 activation and gas-result trends", "printed Table 1", "Figure 8 TEM"]},
        "pressure_policy_check": "180 Pa activation pressure and 254 Pa methane-growth pressure are kept in their proper stages; no atmospheric/default pressure is introduced.",
        "cross_run_inheritance_check": "Only Table 1's run-linked yield, morphology, length, diameter, and Raman ratio are assigned; figure-only conversion values are not guessed or copied.",
        "unit_policy_check": "Printed micrometre CNT-length units are preserved, with the contradictory prose nanometre unit logged as high severity.",
        "conflict_check": "Length unit, maximum-yield treatment time, and methane-conversion conflicts are explicitly logged.",
    })
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


def build_lit_60168627(context: SourceContext) -> Path:
    """Liu et al. 2012, catalyst-free seeded SWCNT vapour-phase epitaxy."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    reported_cases = [
        {
            "code": "76_ETHANOL_QUARTZ",
            "label": "(7,6) seed, ethanol VPE on quartz",
            "seed": "chirality-pure (7,6) SWCNT seed",
            "substrate": "quartz",
            "feed": "ethanol",
            "gas": "300 sccm H2; 160 sccm Ar through 0 C ethanol bubbler",
            "result": "positive",
            "summary": "Cloned (7,6) SWCNTs averaged 34.5 +/- 17.7 micrometres versus 0.34 +/- 0.15 micrometres before cloning; measured diameter approximately 0.9 nm.",
            "length": "34.5 +/- 17.7 micrometres after cloning; 0.34 +/- 0.15 micrometres before cloning",
            "diameter": "0.9",
            "morphology": "long cloned SWCNTs; horizontally aligned on quartz",
            "raman": "265 cm-1 RBM; predominant (7,6) chirality with minority impurity peaks",
            "result_span": "SPAN_FD215FD3D8F211C4784E",
        },
        {
            "code": "76_METHANE_QUARTZ",
            "label": "(7,6) seed, methane VPE on quartz",
            "seed": "chirality-pure (7,6) SWCNT seed",
            "substrate": "quartz",
            "feed": "methane",
            "gas": "2,000 sccm CH4; 300 sccm H2",
            "result": "positive",
            "summary": "SEM shows cloned (7,6) nanotubes on quartz using methane VPE.",
            "length": "tens of micrometres; no run-specific distribution reported",
            "diameter": "",
            "morphology": "long cloned SWCNTs on quartz",
            "raman": "(7,6) chirality preserved; run-specific Raman spectrum not separately linked to feedstock",
            "result_span": "SPAN_36FA294D4B563210E2FC",
        },
        {
            "code": "65_METHANE_QUARTZ",
            "label": "(6,5) seed, methane VPE on quartz",
            "seed": "chirality-pure (6,5) SWCNT seed",
            "substrate": "quartz",
            "feed": "methane",
            "gas": "2,000 sccm CH4; 300 sccm H2",
            "result": "positive",
            "summary": "SEM shows cloned (6,5) nanotubes on quartz using methane VPE.",
            "length": "tens of micrometres; no run-specific distribution reported",
            "diameter": "",
            "morphology": "long cloned SWCNTs on quartz",
            "raman": "(6,5) electronic type confirmed in cloned-nanotube devices; no run-specific RBM value reported",
            "result_span": "SPAN_F2DA289B7C76794444C5",
        },
        {
            "code": "65_ETHANOL_QUARTZ",
            "label": "(6,5) seed, ethanol VPE on quartz",
            "seed": "chirality-pure (6,5) SWCNT seed",
            "substrate": "quartz",
            "feed": "ethanol",
            "gas": "300 sccm H2; 160 sccm Ar through 0 C ethanol bubbler",
            "result": "positive",
            "summary": "SEM shows cloned (6,5) nanotubes on quartz using ethanol VPE.",
            "length": "tens of micrometres; no run-specific distribution reported",
            "diameter": "",
            "morphology": "long cloned SWCNTs on quartz",
            "raman": "(6,5) electronic type confirmed in cloned-nanotube devices; no run-specific RBM value reported",
            "result_span": "SPAN_F2DA289B7C76794444C5",
        },
        {
            "code": "77_METHANE_QUARTZ",
            "label": "(7,7) seed, methane VPE on quartz",
            "seed": "chirality-pure (7,7) SWCNT seed",
            "substrate": "quartz",
            "feed": "methane",
            "gas": "2,000 sccm CH4; 300 sccm H2",
            "result": "positive",
            "summary": "SEM demonstrates methane VPE cloning of metallic (7,7) SWCNTs on quartz.",
            "length": "tens of micrometres; no run-specific distribution reported",
            "diameter": "",
            "morphology": "cloned metallic SWCNTs on quartz",
            "raman": "249 cm-1 RBM supports (7,7) chirality; feedstock linkage is from the SEM case",
            "result_span": "SPAN_DC9BD9B9684A167714BE",
        },
        {
            "code": "77_METHANE_SIO2",
            "label": "(7,7) seed, methane VPE on Si/SiO2",
            "seed": "chirality-pure (7,7) SWCNT seed",
            "substrate": "Si/SiO2",
            "feed": "methane",
            "gas": "2,000 sccm CH4; 300 sccm H2",
            "result": "positive",
            "summary": "SEM demonstrates methane VPE cloning of (7,7) SWCNTs on Si/SiO2; Raman after VPE has a predominant 249 cm-1 RBM.",
            "length": "tens of micrometres; no run-specific distribution reported",
            "diameter": "",
            "morphology": "randomly oriented cloned metallic SWCNTs on Si/SiO2",
            "raman": "predominant 249 cm-1 RBM after VPE",
            "result_span": "SPAN_DC9BD9B9684A167714BE",
        },
        {
            "code": "76_SIO2_FEED_UNLINKED",
            "label": "(7,6) seed VPE on Si/SiO2; feed not linked",
            "seed": "chirality-pure (7,6) SWCNT seed",
            "substrate": "Si/SiO2",
            "feed": "not_run_linked",
            "gas": "not_run_linked",
            "result": "positive",
            "summary": "The substrate comparison shows random orientation for cloned (7,6) SWCNTs on Si/SiO2, but the figure caption does not identify methane versus ethanol for this panel.",
            "length": "tens of micrometres; no run-specific distribution reported",
            "diameter": "",
            "morphology": "randomly oriented cloned SWCNTs on Si/SiO2",
            "raman": "(7,6) chirality context; no feed-linked Raman result assigned",
            "result_span": "SPAN_36FA294D4B563210E2FC",
        },
    ]
    controls = [
        ("BLANK_QUARTZ", "blank quartz substrate control", "blank quartz substrate", "No nanotube growth was observed after annealing and VPE."),
        ("DNA_ONLY_QUARTZ", "DNA-only quartz control", "quartz deposited with DNA solution but no nanotube seed", "No nanotube growth was observed after annealing and VPE."),
        ("IMPROPER_ANNEAL", "seeded control without proper annealing", "chirality-pure SWCNT seeds; exact chirality not linked", "Cloning yield was extremely low and only curvy nanotube bundles were visible after growth."),
    ]
    optima = [
        ("OPT_H300_AR160", "ethanol-flow optimization optimum at H2 300 / Ar 160", "300 sccm H2; 160 sccm Ar through ethanol bubbler", "Highest cloned-nanotube density in the hydrogen-flow series."),
        ("OPT_H250_AR128", "ethanol-flow optimization optimum at H2 250 / Ar 128", "250 sccm H2; 128 sccm Ar through ethanol bubbler", "Highest cloned-nanotube density in the argon-flow series."),
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [source_master_row(context, "Seven figure-linked positive VPE cases, three negative controls, and two exact optimization optima reconstructed; incomplete supplementary matrices are not guessed.")],
        "source_run": [], "catalyst_system": [], "reactor_process_gas": [],
        "yield_quality": [], "cost_scale_review": [], "evidence_index": [],
        "review_issue_log": [],
    }

    def add_seed_and_common(run_id: str, seed: str, substrate: str, *, growth_feed: str, gas_summary: str, common_recipe: bool) -> tuple[dict[str, str], list[dict[str, str]]]:
        catalyst = catalyst_row(
            run_id,
            catalyst_label="metal-catalyst-free chirality-pure SWCNT seed",
            active_metals="none",
            support_material=substrate,
            preparation_method="DNA-based chromatographic separation; drop deposition",
            preparation_detail=f"{seed}; approximately 0.5 micrograms/mL seed solution, incubated 30 min to 1 week, rinsed and blow-dried",
            activation_condition="air anneal 200 C for 30 min; then 400 C under 300 sccm H2 and 3 min water-vapour treatment using 100 sccm Ar through a room-temperature bubbler",
            phase_or_state_summary="open, activated SWCNT seed ends; no metal catalyst",
        )
        stages = [
            process_row(run_id, 1, "seed_deposition", reactor_type="substrate drop-deposition preparation", reactor_setup_summary=f"seed deposited on {substrate}", process_note="approximately 0.5 micrograms/mL seed solution; incubation 30 min to 1 week; gentle water rinse and blow-dry"),
            process_row(run_id, 2, "air_annealing", reactor_type="2.54 cm (1 inch) tube furnace", temperature_setpoint_C="200", holding_time_min="30", gas_composition_summary="air", process_note="DNA removal and seed-end activation sequence"),
            process_row(run_id, 3, "hydrogen_and_water_vapour_annealing", reactor_type="2.54 cm (1 inch) tube furnace", temperature_setpoint_C="400", holding_time_min="3", reducing_gas="H2", reducing_gas_flow_original="300 sccm", inert_gas="Ar through room-temperature water bubbler", inert_gas_flow_original="100 sccm", process_note="water-vapour flow starts after 400 C is reached; 3 min treatment"),
        ]
        if common_recipe:
            stages.append(process_row(run_id, 4, "vapour_phase_epitaxy", reactor_type="tube-furnace VPE", temperature_setpoint_C="900", holding_time_min="15", carbon_source=growth_feed, gas_composition_summary=gas_summary, process_note="300 sccm H2 used during temperature ramp-up; catalyst-free growth from SWCNT seed ends"))
        return catalyst, stages

    for index, case in enumerate(reported_cases, start=1):
        run = source_run_row(source_id, case["code"], case["label"], case["summary"])
        run_id = run["run_id"]
        catalyst, stages = add_seed_and_common(run_id, case["seed"], case["substrate"], growth_feed=case["feed"], gas_summary=case["gas"], common_recipe=True)
        product = yield_row(
            run_id,
            primary_yield_metric="qualitative successful SWCNT cloning; no mass yield reported",
            yield_original="successful cloning observed; quantitative mass yield not reported",
            yield_definition_original="cloning outcome assessed by AFM/SEM and chirality by Raman/electrical measurement",
            yield_standardization_note="No mass or molar yield is inferred from microscopy.",
            CNT_type_reported="single-wall carbon nanotubes",
            CNT_type_confirmed=case["raman"],
            product_mixture_summary="cloned SWCNTs grown from chirality-pure seeds; non-CNT fraction not quantified",
            CNT_type_evidence="seed chirality, microscopy, Raman and/or electrical characterization",
            outer_diameter_mean_nm=case["diameter"],
            length_summary=case["length"],
            morphology=case["morphology"],
            alignment_or_array=("horizontally aligned" if case["substrate"] == "quartz" else "random orientation"),
            characterization_methods="AFM; SEM; Raman spectroscopy; electrical measurements for semiconducting cloned tubes",
        )
        cost = cost_row(run_id, scale_level_demonstrated="laboratory 1 inch tube furnace", scale_level_claimed="not_reported", quantitative_cost_reported="not_reported")
        tables["source_run"].append(run); tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].extend(stages); tables["yield_quality"].append(product); tables["cost_scale_review"].append(cost)
        prefix = f"{source_id}_EV_{index:02d}"
        tables["evidence_index"].extend([
            evidence_row(source_id, f"{prefix}_SEED", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_B51C0D5D5B7182EE8D99", "Methods identify the chirality-pure seed, catalyst-free deposition, substrate, concentration, incubation, and activation sequence."),
            evidence_row(source_id, f"{prefix}_DEPOSIT", run_id, "reactor_process_gas", stages[0]["process_stage_id"], "record_level", "SPAN_B51C0D5D5B7182EE8D99", "Methods report drop deposition of approximately 0.5 micrograms/mL seed solution, 30 min to 1 week incubation, rinsing, and blow-drying on quartz or Si/SiO2."),
            evidence_row(source_id, f"{prefix}_ANNEAL", run_id, "reactor_process_gas", stages[1]["process_stage_id"], "record_level", "SPAN_B51C0D5D5B7182EE8D99", "Methods report the 200 C air anneal for 30 min followed by 400 C hydrogen and 3 min water-vapour treatment."),
            evidence_row(source_id, f"{prefix}_WATER", run_id, "reactor_process_gas", stages[2]["process_stage_id"], "record_level", "SPAN_B51C0D5D5B7182EE8D99", "Methods report 400 C under 300 sccm H2 and a 3 min water-vapour treatment supplied by 100 sccm Ar through a room-temperature bubbler."),
            evidence_row(source_id, f"{prefix}_GROW_TEMP", run_id, "reactor_process_gas", stages[-1]["process_stage_id"], "record_level", "SPAN_B51C0D5D5B7182EE8D99", "Methods report catalyst-free VPE at 900 C after the annealing sequence."),
            evidence_row(source_id, f"{prefix}_GROW_FLOW", run_id, "reactor_process_gas", stages[-1]["process_stage_id"], "record_level", "SPAN_320CDD99CC1EB1B39E49", "Methods report 15 min growth and the separate ethanol or methane flow recipes; an unlinked feed is explicitly retained as not run linked."),
            evidence_row(source_id, f"{prefix}_RESULT", run_id, "yield_quality", product["product_id"], "record_level", case["result_span"], case["summary"]),
            evidence_row(source_id, f"{prefix}_COST", run_id, "cost_scale_review", run_id, "record_level", "SPAN_B51C0D5D5B7182EE8D99", "Methods demonstrate a laboratory 2.54 cm tube furnace and do not report cost.", value_status="review_assessment"),
        ])
        if case["code"] == "76_ETHANOL_QUARTZ":
            tables["evidence_index"].extend([
                evidence_row(source_id, f"{prefix}_LENGTH", run_id, "yield_quality", product["product_id"], "length_summary", "SPAN_36FA294D4B563210E2FC", "Figure 2 and adjacent text report 34.5 +/- 17.7 micrometres after cloning and 0.34 +/- 0.15 micrometres before cloning."),
                evidence_row(source_id, f"{prefix}_DIAM", run_id, "yield_quality", product["product_id"], "outer_diameter_mean_nm", "SPAN_FD215FD3D8F211C4784E", "The measured cloned-tube diameter is approximately 0.9 nm."),
                evidence_row(source_id, f"{prefix}_RAMAN", run_id, "yield_quality", product["product_id"], "CNT_type_confirmed", "SPAN_9A1F3C1C7F3CC2F733D2", "The predominant 265 cm-1 RBM supports (7,6) chirality; minority impurity peaks are also acknowledged."),
            ])
    next_index = len(reported_cases) + 1
    for code, label, substrate_seed, result_text in controls:
        run = source_run_row(source_id, code, label, result_text, data_type="negative_control", target_track="CNT_production_control")
        run_id = run["run_id"]
        catalyst = catalyst_row(run_id, catalyst_label="no metal catalyst", active_metals="none", support_material="quartz", preparation_method=substrate_seed, preparation_detail="control described in Results", activation_condition=("air and water-vapour annealing followed by VPE" if code != "IMPROPER_ANNEAL" else "without proper annealing treatment; exact omitted condition is only in unavailable Supplementary Information"), phase_or_state_summary="control condition")
        process = process_row(run_id, 1, "control_vpe_sequence", reactor_type="tube-furnace VPE", process_note=("air and water-vapour annealing followed by VPE; feed and flow are not linked to the control in the main paper" if code != "IMPROPER_ANNEAL" else "VPE after an underspecified improper-annealing condition; no numeric annealing value inferred"))
        product = yield_row(run_id, primary_yield_metric="qualitative negative-control outcome", yield_original=result_text, yield_definition_original="microscopy observation", yield_standardization_note="No numeric yield is inferred.", CNT_type_reported=("not_observed" if code != "IMPROPER_ANNEAL" else "curvy nanotube bundles at extremely low cloning yield"), CNT_type_confirmed=("no nanotube growth observed" if code != "IMPROPER_ANNEAL" else "low-yield bundled nanotubes"), product_mixture_summary=result_text, CNT_type_evidence="main-text control observation", morphology=("no nanotube product" if code != "IMPROPER_ANNEAL" else "only curvy nanotube bundles"), characterization_methods="microscopy; Supplementary figures cited by main text")
        cost = cost_row(run_id, scale_level_demonstrated="laboratory control", scale_level_claimed="not_reported", quantitative_cost_reported="not_reported")
        tables["source_run"].append(run); tables["catalyst_system"].append(catalyst); tables["reactor_process_gas"].append(process); tables["yield_quality"].append(product); tables["cost_scale_review"].append(cost)
        span = "SPAN_FD215FD3D8F211C4784E" if code != "IMPROPER_ANNEAL" else "SPAN_0FADF60E5F61031371B9"
        prefix = f"{source_id}_EV_{next_index:02d}"; next_index += 1
        tables["evidence_index"].extend([
            evidence_row(source_id, f"{prefix}_CONTROL", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", span, result_text),
            evidence_row(source_id, f"{prefix}_PROCESS", run_id, "reactor_process_gas", process["process_stage_id"], "record_level", span, "The control sequence is preserved only to the specificity reported in the main paper."),
            evidence_row(source_id, f"{prefix}_RESULT", run_id, "yield_quality", product["product_id"], "record_level", span, result_text),
            evidence_row(source_id, f"{prefix}_COST", run_id, "cost_scale_review", run_id, "record_level", span, "Laboratory control; no cost reported.", value_status="review_assessment"),
        ])
    for code, label, gas, result_text in optima:
        run = source_run_row(source_id, code, label, result_text, target_track="VPE_flow_optimization")
        run_id = run["run_id"]
        catalyst, stages = add_seed_and_common(run_id, "similar-density chirality-pure SWCNT seeds; exact chirality not linked", "substrate not linked in optimization paragraph", growth_feed="ethanol", gas_summary=gas, common_recipe=True)
        product = yield_row(run_id, primary_yield_metric="qualitative cloned-nanotube density", yield_original=result_text, yield_definition_original="SEM examination of nanotube length, density and uniformity", yield_standardization_note="Only the exact optimum described in text is retained; image-only values are not digitized.", CNT_type_reported="cloned single-wall carbon nanotubes", CNT_type_confirmed="SWCNT cloning optimization", product_mixture_summary="cloned nanotubes; non-CNT fraction not quantified", CNT_type_evidence="SEM and seeded-VPE context", morphology="highest-density cloned nanotubes within the stated flow series", characterization_methods="SEM")
        cost = cost_row(run_id, scale_level_demonstrated="laboratory optimization sample", scale_level_claimed="not_reported", quantitative_cost_reported="not_reported")
        tables["source_run"].append(run); tables["catalyst_system"].append(catalyst); tables["reactor_process_gas"].extend(stages); tables["yield_quality"].append(product); tables["cost_scale_review"].append(cost)
        prefix = f"{source_id}_EV_{next_index:02d}"; next_index += 1
        tables["evidence_index"].extend([
            evidence_row(source_id, f"{prefix}_SEED", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_B51C0D5D5B7182EE8D99", "Methods identify the seed preparation, approximately 0.5 micrograms/mL concentration, incubation, and the 200/400 C activation sequence with 100 sccm bubbler flow."),
            evidence_row(source_id, f"{prefix}_DEPOSIT", run_id, "reactor_process_gas", stages[0]["process_stage_id"], "record_level", "SPAN_B51C0D5D5B7182EE8D99", "Methods report the seed drop-deposition and incubation procedure."),
            evidence_row(source_id, f"{prefix}_AIR", run_id, "reactor_process_gas", stages[1]["process_stage_id"], "record_level", "SPAN_B51C0D5D5B7182EE8D99", "Methods report air annealing at 200 C for 30 min in the 2.54 cm tube furnace."),
            evidence_row(source_id, f"{prefix}_WATER", run_id, "reactor_process_gas", stages[2]["process_stage_id"], "record_level", "SPAN_B51C0D5D5B7182EE8D99", "Methods report 400 C, 300 sccm H2, and 3 min water-vapour treatment using 100 sccm Ar."),
            evidence_row(source_id, f"{prefix}_GROW_TEMP", run_id, "reactor_process_gas", stages[-1]["process_stage_id"], "record_level", "SPAN_B51C0D5D5B7182EE8D99", "Methods report VPE at 900 C."),
            evidence_row(source_id, f"{prefix}_GROW_TIME", run_id, "reactor_process_gas", stages[-1]["process_stage_id"], "record_level", "SPAN_320CDD99CC1EB1B39E49", "Methods report 15 min ethanol VPE and describe the ten-sample flow optimization."),
            evidence_row(source_id, f"{prefix}_PROCESS", run_id, "reactor_process_gas", stages[-1]["process_stage_id"], "record_level", "SPAN_5865A421B95510140B63", f"Methods explicitly identify the optimum flow condition: {gas}."),
            evidence_row(source_id, f"{prefix}_RESULT", run_id, "yield_quality", product["product_id"], "record_level", "SPAN_5865A421B95510140B63", result_text),
            evidence_row(source_id, f"{prefix}_COST", run_id, "cost_scale_review", run_id, "record_level", "SPAN_320CDD99CC1EB1B39E49", "Laboratory optimization sample; no cost reported.", value_status="review_assessment"),
        ])
    tables["review_issue_log"].append(issue_row(
        f"{source_id}_ISS_SUPPLEMENTARY_MATRIX", source_id, tables["source_run"][-1]["run_id"], "incomplete_local_supplementary_matrix", "source_run", tables["source_run"][-1]["run_id"], "run_summary",
        "The paper reports ten ethanol-optimization samples and cites Supplementary Table S1/Fig. S3, but the local PDF contains only the main article. Only the two text-explicit optima are reconstructed; remaining settings and image-only outcomes are not guessed.",
        evidence_ids=f"{source_id}_EV_{len(reported_cases)+len(controls)+1:02d}_PROCESS;{source_id}_EV_{len(reported_cases)+len(controls)+2:02d}_PROCESS", severity="high", conflicting_values="10 samples reported | 2 exact optimum conditions recoverable from local main text",
    ))
    write_package(package, tables)
    write_review(package, {
        "source_id": source_id, "review_status": "extracted_needs_supervisory_review", "reviewer": "Codex", "source_identity_checked": True,
        "campaign_reconciliation": {"result_linked_campaigns_in_paper": 12, "extracted_runs": 12, "negative_runs_preserved": 3, "matrix_note": "Seven figure-linked positive cases, three negative controls, and two text-explicit ethanol-flow optima are retained. The other eight members of the ten-sample optimization matrix are not reconstructable from the local main article and are not fabricated."},
        "pdf_visual_review": {"completed": True, "pages_checked": [2, 3, 6], "objects_checked": ["Figure 1 process schematic", "Figure 2 AFM/SEM and length histograms", "Figure 3 Raman panels", "Methods flow recipes"]},
        "pressure_policy_check": "No pressure is reported for VPE; the pressure field remains blank and no atmospheric default is introduced.",
        "cross_run_inheritance_check": "Feedstock is assigned only when the figure caption links it. The (7,6)/SiO2 substrate panel and negative controls retain unlinked feed/flow rather than inheriting another run's recipe.",
        "unit_policy_check": "PDF glyphs visually verified: the cloned-tube length is 34.5 +/- 17.7 micrometres, seed length 0.34 +/- 0.15 micrometres, and diameter approximately 0.9 nm.",
        "conflict_check": "No internal numeric conflict found; incomplete supplementary optimization details are logged as a high-severity coverage issue.",
    })
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


BUILDERS = {
    "LIT_004FAE25B3DA5255": build_lit_004fae25,
    "LIT_1E15BC8013D45B19": build_lit_1e15bc80,
    "LIT_2220A162F1244DB9": build_lit_2220a162,
    "LIT_26E8CF0B49DA2722": build_lit_26e8cf0b,
    "LIT_2AF904451035F138": build_lit_2af90445,
    "LIT_2CBDCDC33D48CCD2": build_lit_2cbdcdc3,
    "LIT_3E872882CF7C68F1": build_lit_3e872882,
    "LIT_436402DA7A57D194": build_lit_436402da,
    "LIT_4421747A539A3C4E": build_lit_4421747a,
    "LIT_4B3D3C5CD3B8D731": build_lit_4b3d3c5c,
    "LIT_5925FB1BAD7692D5": build_lit_5925fb1b,
    "LIT_60168627B3641616": build_lit_60168627,
}

NON_EXTRACTABLE = {
    "LIT_0D3B0A5D40602AEC": {
        "reason": (
            "Density-functional-theory study of SWCNT/GNR fragment stability; "
            "the paper contains no performed CNT synthesis experiment or "
            "source-linked experimental catalyst/process/result campaign."
        ),
        "evidence_sections": [
            "Abstract",
            "2. Computational model",
            "3. Results and discussion",
            "4. Conclusions",
        ],
        "pdf_pages_checked": [1, 4],
    },
    "LIT_25AA283F6C91E22D": {
        "reason": (
            "All-electron DFT-GGA study of Fe4Cn(CO)m cluster energetics and "
            "SWCNT nucleation; no CNT synthesis experiment performed in this paper."
        ),
        "evidence_sections": [
            "Abstract",
            "2. DFT-GGA Simulations of HiPco",
            "3. Geometry Patterns in Fe4Cn",
            "4. Conclusion",
        ],
        "pdf_pages_checked": [1, 6],
    },
    "LIT_29ED431CB9D4E128": {
        "reason": (
            "The local HTML artifact is a subscription preview containing only the abstract, "
            "references, and access controls. It names variables studied but supplies no "
            "run-resolved catalyst/process/result values; no run was fabricated from the abstract."
        ),
        "evidence_sections": [
            "Abstract",
            "subscription-content notice",
            "References",
            "Cite this article",
        ],
        "pdf_pages_checked": [],
    },
    "LIT_54F61DEC2F1C7FEB": {
        "reason": (
            "The local HTML artifact is a subscription preview containing an abstract but no "
            "methods, run matrix, or numeric result table. Catalyst and outcome claims in the "
            "abstract are not sufficient to reconstruct run-resolved experiments safely."
        ),
        "evidence_sections": [
            "Abstract",
            "subscription-content notice",
            "References",
            "Cite this article",
        ],
        "pdf_pages_checked": [],
    },
}


def main() -> None:
    available = contexts()
    for source_id, builder in BUILDERS.items():
        print(builder(available[source_id]))
    for source_id, disposition in NON_EXTRACTABLE.items():
        print(
            mark_non_extractable(
                available[source_id],
                reason=disposition["reason"],
                evidence_sections=disposition["evidence_sections"],
                pdf_pages_checked=disposition["pdf_pages_checked"],
            )
        )


if __name__ == "__main__":
    main()
