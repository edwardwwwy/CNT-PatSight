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


def build_lit_87b8240d(context: SourceContext) -> Path:
    """Kimura et al. 2013, feedstock matrix plus TDN/benzaldehyde demo."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    campaigns = [
        ("ACETYLENE", "acetylene", "3.23", "823", "10.8", "0.039", "3.1"),
        ("ETHYLENE", "ethylene", "3.09", "938", "12.4", "0.033", "3.0"),
        ("BUTADIENE", "1,3-butadiene", "3.29", "817", "15", "0.040", "2.5"),
        ("PROPANE", "propane", "4.67", "1352", "5.4", "0.035", "2.8"),
        ("BUTANE", "butane", "4.98", "1508", "7.8", "0.033", "2.9"),
        ("N_HEXANE", "n-hexane", "2.75", "971", "6.2", "0.028", "3.0"),
        ("T_DN", "trans-decahydronaphthalene", "1.36", "400", "15.2", "0.034", "2.8"),
        ("P_XYLENE", "p-xylene", "0.76", "163", "5.7", "0.046", ""),
        ("DICYCLOPENTADIENE", "dicyclopentadiene", "2.03", "655", "14.0", "0.031", ""),
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [
            source_master_row(
                context,
                "Ten-feedstock water-assisted CVD matrix (including the failed methane campaign), Table 2, Figures 1-4, Methods, and the separate TDN/benzaldehyde demonstration.",
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

    def add_common_rows(
        run: dict[str, str], carbon_source: str
    ) -> tuple[dict[str, str], list[dict[str, str]], dict[str, str]]:
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label="sputtered Al2O3/Fe thin-film catalyst",
            active_metals="Fe",
            support_material="40 nm Al2O3 layer",
            preparation_method="sequential sputtering",
            preparation_detail="40 nm Al2O3 / 1.5 nm Fe",
            activation_condition="nanoparticle formation at 750 C under He/H2 = 1/9",
            phase_or_state_summary="Fe nanoparticles formed in situ before feedstock-specific growth",
        )
        stages = [
            process_row(
                run_id,
                1,
                "nanoparticle_formation",
                reactor_type="1 inch fully automated CVD system with exchange chamber",
                temperature_setpoint_C="750",
                gas_composition_summary="He/H2 = 1/9",
                process_note="Common catalyst nanoparticle-formation step used to remove catalyst formation as a variable.",
            ),
            process_row(
                run_id,
                2,
                "water_assisted_CVD_growth",
                reactor_type="1 inch fully automated CVD system with exchange chamber",
                temperature_range_reported_C="725-900",
                temperature_program_summary="Adjusted from the common 750 C nanoparticle-formation condition to a feedstock-specific optimized growth temperature; the per-feedstock setting is not tabulated.",
                holding_time_min="10",
                carbon_source=carbon_source,
                inert_gas="He",
                cofeed_or_reactive_gas="water growth enhancer",
                cofeed_flow_original="50-500 ppm water; feedstock-specific optimized level not reported",
                gas_composition_summary="Feedstock level and water level were optimized separately; feedstock-specific flows are not reported.",
                process_note="The paper gives conflicting common total flows (1 L/min in Results and 500 sccm in Methods), so no total-flow value is selected.",
            ),
        ]
        cost = cost_row(
            run_id,
            scale_level_demonstrated="1 inch automated CVD research system",
            scale_level_claimed="not_reported",
            quantitative_cost_reported="not_reported",
            review_note="The article reports an automated research system and about 2000 optimization syntheses; no quantitative cost is reported.",
        )
        return catalyst, stages, cost

    for index, (code, feedstock, yield_value, height, gd, density, diameter) in enumerate(
        campaigns, start=1
    ):
        run = source_run_row(
            source_id,
            code,
            f"water-assisted CVD with {feedstock}",
            f"Feedstock-specific optimized water-assisted CVD campaign producing a vertically aligned SWCNT forest; Table 2 reports {yield_value} mg/cm2 forest yield.",
        )
        run_id = run["run_id"]
        catalyst, stages, cost = add_common_rows(run, feedstock)
        product = yield_row(
            run_id,
            primary_yield_metric="CNT forest mass per substrate area",
            yield_original=f"{yield_value} mg/cm2",
            yield_definition_original="mass of the CNT forest per substrate area",
            yield_value_standardized=yield_value,
            yield_unit_standardized="mg/cm2",
            yield_standardization_note="Direct transcription from Table 2; no conversion performed.",
            secondary_result_summary=f"forest height {height} um; bulk forest density {density} g/cm3",
            CNT_type_reported="single-wall carbon nanotube forest",
            CNT_type_confirmed="forest primarily composed of SWCNTs (>90%); any DWCNT occurrence was not feedstock-resolved",
            product_mixture_summary="vertically aligned forest primarily composed of SWCNTs; non-CNT impurity fraction not quantified per feedstock",
            CNT_type_evidence="RBM Raman profiles and TEM; Table 2 feedstock-specific characterization",
            outer_diameter_mean_nm=diameter or "not_reported",
            length_summary=f"forest height {height} um",
            morphology="vertically aligned SWCNT forest",
            alignment_or_array="vertically aligned forest",
            Raman_ratio_type="G/D",
            Raman_ratio_value=gd,
            Raman_laser_wavelength_nm="532",
            characterization_methods="gravimetric forest yield; height; bulk density; Raman spectroscopy; FTIR; TEM",
            notes="A dash in the Table 2 diameter column is retained as not_reported, never as zero.",
        )
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].extend(stages)
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        prefix = f"{source_id}_EV_{index:02d}"
        tables["evidence_index"].extend(
            [
                evidence_row(source_id, f"{prefix}_CAT", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_36246A46423A464D69BE", "Methods report the common sputtered 40 nm Al2O3 / 1.5 nm Fe catalyst and 750 C He/H2 nanoparticle-formation step."),
                evidence_row(source_id, f"{prefix}_FORM", run_id, "reactor_process_gas", stages[0]["process_stage_id"], "record_level", "SPAN_36246A46423A464D69BE", "Methods report the 1 inch automated CVD system and common 750 C, He/H2 = 1/9 nanoparticle-formation step."),
                evidence_row(source_id, f"{prefix}_GROW", run_id, "reactor_process_gas", stages[1]["process_stage_id"], "record_level", "SPAN_36246A46423A464D69BE", "Methods report 10 min growth, 725-900 C optimized temperatures, water at 50-500 ppm, He carrier gas, and feedstock-specific optimization."),
                evidence_row(source_id, f"{prefix}_FLOW_CONFLICT", run_id, "reactor_process_gas", stages[1]["process_stage_id"], "record_level", "SPAN_0AA8EE9FE744693B6657", "Results describe a 1 L/min standard process while Methods state 500 sccm; the output retains the conflict and leaves total flow blank."),
                evidence_row(source_id, f"{prefix}_TABLE2", run_id, "yield_quality", product["product_id"], "record_level", "SPAN_D031297F17756C4E70AF", "Table 2 supplies feedstock-specific yield, height, G/D, density and, where reported, diameter."),
                evidence_row(source_id, f"{prefix}_IDENTITY", run_id, "yield_quality", product["product_id"], "CNT_type_reported;CNT_type_confirmed;product_mixture_summary;CNT_type_evidence;morphology;alignment_or_array;characterization_methods", "SPAN_7EF4C227D6BFD58CF8D8", "Results report SWCNT forests for all feedstocks except methane and describe RBM Raman and TEM confirmation."),
                evidence_row(source_id, f"{prefix}_PURITY", run_id, "yield_quality", product["product_id"], "CNT_type_confirmed;product_mixture_summary", "SPAN_93ECAF269AB8D297E018", "Results report that each forest was primarily SWCNT (>90%); any double-wall contribution was not assigned to individual feedstocks."),
                evidence_row(source_id, f"{prefix}_RAMAN", run_id, "yield_quality", product["product_id"], "Raman_laser_wavelength_nm", "SPAN_841C0F564742832EDE65", "Methods report Raman excitation at 532 nm."),
                evidence_row(source_id, f"{prefix}_COST", run_id, "cost_scale_review", run_id, "record_level", "SPAN_36246A46423A464D69BE", "Methods demonstrate a 1 inch automated CVD research system; cost fields are not reported.", value_status="review_assessment"),
            ]
        )

    methane = source_run_row(
        source_id,
        "METHANE_FAILED",
        "water-assisted CVD methane campaign",
        "Methane was tested as the tenth feedstock but did not form a SWCNT forest in this catalyst/growth system.",
        data_type="negative_control",
        target_track="CNT_production_control",
    )
    methane_id = methane["run_id"]
    catalyst, stages, cost = add_common_rows(methane, "methane")
    methane_product = yield_row(
        methane_id,
        primary_yield_metric="qualitative forest-growth outcome",
        yield_original="no SWCNT forest formed",
        yield_definition_original="forest presence/absence in Figure 1 and Results",
        yield_standardization_note="No numeric yield is inferred for the failed methane campaign.",
        CNT_type_reported="not_observed",
        CNT_type_confirmed="no SWCNT forest formed",
        product_mixture_summary="failed forest-growth campaign; no successful CNT product fields inherited",
        CNT_type_evidence="Results explicitly identify methane as the sole exception among the ten feedstocks.",
        morphology="no forest observed",
        characterization_methods="Figure 1 digital sample image and result narrative",
        notes="Success-only Table 2 values, diameter, density, Raman and aligned-forest fields are intentionally absent.",
    )
    tables["source_run"].append(methane)
    tables["catalyst_system"].append(catalyst)
    tables["reactor_process_gas"].extend(stages)
    tables["yield_quality"].append(methane_product)
    tables["cost_scale_review"].append(cost)
    prefix = f"{source_id}_EV_10"
    tables["evidence_index"].extend(
        [
            evidence_row(source_id, f"{prefix}_CAT", methane_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_36246A46423A464D69BE", "Methods report the common catalyst and nanoparticle-formation step."),
            evidence_row(source_id, f"{prefix}_FORM", methane_id, "reactor_process_gas", stages[0]["process_stage_id"], "record_level", "SPAN_36246A46423A464D69BE", "Methods report the common 750 C He/H2 nanoparticle-formation step."),
            evidence_row(source_id, f"{prefix}_GROW", methane_id, "reactor_process_gas", stages[1]["process_stage_id"], "record_level", "SPAN_36246A46423A464D69BE", "Methods report the water-assisted feedstock-optimization process; methane is one of the ten feedstocks in Figure 1."),
            evidence_row(source_id, f"{prefix}_FLOW_CONFLICT", methane_id, "reactor_process_gas", stages[1]["process_stage_id"], "record_level", "SPAN_0AA8EE9FE744693B6657", "Results and Methods conflict on common total flow, so total flow remains blank."),
            evidence_row(source_id, f"{prefix}_FAIL", methane_id, "yield_quality", methane_product["product_id"], "record_level", "SPAN_CA968277D41EFA251DFD", "Results explicitly state that forests were grown from all investigated feedstocks except methane."),
            evidence_row(source_id, f"{prefix}_COST", methane_id, "cost_scale_review", methane_id, "record_level", "SPAN_36246A46423A464D69BE", "Methods demonstrate a 1 inch automated CVD research system; cost is not reported.", value_status="review_assessment"),
        ]
    )

    combo = source_run_row(
        source_id,
        "TDN_BENZALDEHYDE_DEMO",
        "TDN carbon source with benzaldehyde growth enhancer",
        "Separate two-CVD-process demonstration that a TDN/benzaldehyde ambient can form a CNT forest; the individual gases alone did not form forests.",
        data_type="demonstration_run",
    )
    combo_id = combo["run_id"]
    combo_catalyst = catalyst_row(
        combo_id,
        catalyst_label="sputtered Al2O3/Fe thin-film catalyst",
        active_metals="Fe",
        support_material="40 nm Al2O3 layer",
        preparation_method="sequential sputtering",
        preparation_detail="40 nm Al2O3 / 1.5 nm Fe",
        activation_condition="nanoparticle formation under standard conditions before growth",
        phase_or_state_summary="Fe nanoparticles formed in situ",
    )
    combo_process = process_row(
        combo_id,
        1,
        "TDN_benzaldehyde_CVD_demonstration",
        reactor_type="1 inch fully automated CVD system with exchange chamber",
        temperature_setpoint_C="750",
        carbon_source="trans-decahydronaphthalene (TDN)",
        cofeed_or_reactive_gas="benzaldehyde (BA) growth enhancer",
        cofeed_flow_original="BA concentration approximately 1/1500 of TDN",
        total_flow_original="approximately 1000 sccm",
        total_flow_sccm="~1000",
        gas_composition_summary="TDN supplies carbon; oxygen-containing benzaldehyde is the growth enhancer.",
        process_note="Two CVD processes were used to adjust the relative TDN/BA level; other conditions were described as similar to the standard process.",
    )
    combo_product = yield_row(
        combo_id,
        primary_yield_metric="qualitative CNT forest formation",
        yield_original="CNT forest synthesized; numeric yield not reported",
        yield_definition_original="demonstration of forest formation from the combined TDN/benzaldehyde ambient",
        yield_standardization_note="No numeric yield, diameter or selectivity is inferred.",
        CNT_type_reported="carbon nanotube forest",
        CNT_type_confirmed="not_reported",
        product_mixture_summary="CNT forest from combined TDN and benzaldehyde; individual-gas controls did not form forests",
        CNT_type_evidence="main-text demonstration narrative",
        morphology="CNT forest",
        characterization_methods="main-text forest observation; sample was not quantitatively characterized",
        notes="The article only expects similarity to the separately characterized TDN/water forest; expected 2.8 nm and 93% values are not copied into this run.",
    )
    combo_cost = cost_row(
        combo_id,
        scale_level_demonstrated="1 inch automated CVD research system",
        scale_level_claimed="not_reported",
        quantitative_cost_reported="not_reported",
        review_note="Two CVD trials were required to adjust the TDN/benzaldehyde ratio; no cost is reported.",
    )
    tables["source_run"].append(combo)
    tables["catalyst_system"].append(combo_catalyst)
    tables["reactor_process_gas"].append(combo_process)
    tables["yield_quality"].append(combo_product)
    tables["cost_scale_review"].append(combo_cost)
    tables["evidence_index"].extend(
        [
            evidence_row(source_id, f"{source_id}_EV_11_CAT", combo_id, "catalyst_system", combo_catalyst["catalyst_id"], "record_level", "SPAN_36246A46423A464D69BE", "Methods report the common sputtered Al2O3/Fe catalyst used for the study."),
            evidence_row(source_id, f"{source_id}_EV_11_PROCESS", combo_id, "reactor_process_gas", combo_process["process_stage_id"], "record_level", "SPAN_CE51C41B28482F1770E2", "The demonstration uses TDN as carbon source and benzaldehyde at approximately 1/1500 of TDN as growth enhancer, with standard-like 750 C and 1000 sccm conditions."),
            evidence_row(source_id, f"{source_id}_EV_11_RESULT", combo_id, "yield_quality", combo_product["product_id"], "record_level", "SPAN_CE51C41B28482F1770E2", "The combined TDN/benzaldehyde ambient formed a CNT forest, while either gas alone did not."),
            evidence_row(source_id, f"{source_id}_EV_11_LIMIT", combo_id, "yield_quality", combo_product["product_id"], "record_level", "SPAN_3D258EA5C74EDA933CF6", "The sample was not quantitatively characterized; diameter and selectivity are expectations from a separate TDN/water case and are not transferred."),
            evidence_row(source_id, f"{source_id}_EV_11_COST", combo_id, "cost_scale_review", combo_id, "record_level", "SPAN_CE51C41B28482F1770E2", "The demonstration required two CVD processes and reports no cost.", value_status="review_assessment"),
        ]
    )
    first_growth = tables["reactor_process_gas"][1]
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{source_id}_ISS_TOTAL_FLOW_CONFLICT",
                source_id,
                tables["source_run"][0]["run_id"],
                "conflicting_reported_value",
                "reactor_process_gas",
                first_growth["process_stage_id"],
                "total_flow_original",
                "Results state a 1 L/min standard total flow, while Methods state 500 sccm. No value is selected for the feedstock matrix.",
                evidence_ids=f"{source_id}_EV_01_GROW;{source_id}_EV_01_FLOW_CONFLICT",
                severity="high",
                conflicting_values="1 L/min | 500 sccm",
            ),
            issue_row(
                f"{source_id}_ISS_COMBO_CHARACTERIZATION",
                source_id,
                combo_id,
                "expected_value_not_measured",
                "yield_quality",
                combo_product["product_id"],
                "outer_diameter_mean_nm",
                "The TDN/benzaldehyde forest was not quantitatively characterized. The paper only expects similarity to a separate TDN/water case, so 2.8 nm and 93% selectivity remain absent.",
                evidence_ids=f"{source_id}_EV_11_LIMIT",
                severity="medium",
                conflicting_values="expected ~2.8 nm and ~93% | not measured for combo",
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
                "result_linked_campaigns_in_paper": 11,
                "extracted_runs": 11,
                "negative_runs_preserved": 1,
                "matrix_note": "All ten Figure 1 feedstocks are retained, including failed methane and the previously omitted successful p-xylene row. The separate TDN/benzaldehyde demonstration is an eleventh run.",
            },
            "pdf_visual_review": {
                "completed": True,
                "pages_checked": [2, 3, 4, 5, 6],
                "objects_checked": ["Table 1 feedstock matrix", "Figure 1 ten feedstocks and methane failure", "Table 2 nine successful feedstock rows", "Figures 2-4 Raman/TEM/trend plots", "Methods catalyst and CVD conditions", "TDN/benzaldehyde demonstration narrative"],
            },
            "pressure_policy_check": "The 1 atm value on page 6 belongs to a standard gas-flow-to-molar-input calculation, not a reported reactor pressure. All reactor pressure fields remain blank.",
            "cross_run_inheritance_check": "Methane retains no successful forest, alignment, diameter, density or Raman values. Table 2 values are assigned only to their feedstock rows; dash diameters remain not_reported.",
            "unit_policy_check": "Table 2 units were visually checked on page 4: yield mg/cm2, height um, density g/cm3 and diameter nm. Values are transcribed without conversion.",
            "conflict_check": "The 1 L/min versus 500 sccm common total-flow conflict is logged and neither value is selected for the matrix. Expected TDN/benzaldehyde diameter/selectivity are not treated as measurements.",
        },
    )
    update_manifest(
        source_id,
        "extracted_needs_supervisory_review",
        package_path=package.relative_to(REDO_ROOT).as_posix(),
    )
    return package


def build_lit_bd24584c(context: SourceContext) -> Path:
    """Wirth et al. 2012, three in-situ XRD routes plus ETEM nucleation."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    groups = [
        {
            "code": "FIG2_MIXED_METALLIC",
            "label": "Figure 2 mixed-metallic Fe route",
            "summary": "Representative member of the 12-run in-situ XRD series: alpha/gamma metallic Fe remains active during CNT growth without detected carbide.",
            "phase": "mixed alpha-Fe/gamma-Fe metallic route during growth; no carbide detected",
            "result_span": "SPAN_E930D3421D08A0FED2BC",
            "diameter_mean": "",
            "diameter_range": "",
            "diameter_note": "No figure-specific tube diameter is reported for the Figure 2 representative.",
        },
        {
            "code": "FIG3_GAMMA_FE",
            "label": "Figure 3 gamma-Fe-dominant route",
            "summary": "Representative in-situ XRD run with gamma-Fe dominant during growth and no detected carbide; CNTs averaged 26 nm in diameter.",
            "phase": "gamma-Fe-dominant metallic route during growth; no carbide detected",
            "result_span": "SPAN_E930D3421D08A0FED2BC",
            "diameter_mean": "26",
            "diameter_range": "9-50",
            "diameter_note": "standard deviation 11 nm",
        },
        {
            "code": "FIG4_CARBIDE",
            "label": "Figure 4 cementite-dominant carbide route",
            "summary": "Representative in-situ XRD run in which cementite becomes the dominant growth-stage phase; CNTs averaged 24 nm in diameter.",
            "phase": "cementite-dominant carbide route during growth with alpha-Fe/gamma-Fe also present",
            "result_span": "SPAN_181FABA80420DCF58523",
            "diameter_mean": "24",
            "diameter_range": "11-49",
            "diameter_note": "standard deviation 9 nm",
        },
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [
            source_master_row(
                context,
                "Three figure-defined phase-evolution groups representing 12 nominally repeated in-situ XRD CVD runs, plus the separate ETEM CNT-nucleation experiment.",
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

    direct_anneal_fields = ";".join(
        [
            "stage_type",
            "reactor_type",
            "temperature_setpoint_C",
            "pressure_original",
            "reducing_gas",
            "reducing_gas_flow_original",
            "reducing_gas_flow_sccm",
            "inert_gas",
            "inert_gas_flow_original",
            "inert_gas_flow_sccm",
            "gas_composition_summary",
        ]
    )
    direct_growth_fields = ";".join(
        [
            "stage_type",
            "reactor_type",
            "temperature_setpoint_C",
            "pressure_original",
            "carbon_source",
            "carbon_source_flow_original",
            "carbon_source_flow_sccm",
            "reducing_gas",
            "reducing_gas_flow_original",
            "reducing_gas_flow_sccm",
            "inert_gas",
            "inert_gas_flow_original",
            "inert_gas_flow_sccm",
            "gas_composition_summary",
        ]
    )

    for index, item in enumerate(groups, start=1):
        run = source_run_row(
            source_id,
            item["code"],
            item["label"],
            item["summary"],
            data_type="experimental_series",
        )
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label="oxide-supported thermally evaporated Fe film",
            active_metals="Fe",
            support_material="thermal SiO2 or sputtered Al2O3 on silicon; figure-to-support mapping not reported",
            preparation_method="thermal evaporation of Fe onto oxide-supported silicon wafer",
            preparation_detail="nominally 8 nm Fe film",
            activation_condition="single-step hydrogen-containing anneal before acetylene exposure",
            phase_or_state_summary=item["phase"],
        )
        stages = [
            process_row(
                run_id,
                1,
                "Ar_H2_annealing",
                reactor_type="synchrotron cold-wall reactor chamber",
                temperature_setpoint_C="750",
                pressure_original="~150 mbar",
                pressure_kPa="~15",
                reducing_gas="H2",
                reducing_gas_flow_original="10 sccm",
                reducing_gas_flow_sccm="10",
                inert_gas="Ar",
                inert_gas_flow_original="30 sccm",
                inert_gas_flow_sccm="30",
                gas_composition_summary="Ar/H2 = 30/10 sccm",
                process_note="Stage II; approximate pressure and original gas flows retained.",
            ),
            process_row(
                run_id,
                2,
                "acetylene_CNT_growth",
                reactor_type="synchrotron cold-wall reactor chamber",
                temperature_setpoint_C="750",
                pressure_original="~150 mbar",
                pressure_kPa="~15",
                carbon_source="C2H2",
                carbon_source_flow_original="1 sccm",
                carbon_source_flow_sccm="1",
                reducing_gas="H2",
                reducing_gas_flow_original="10 sccm",
                reducing_gas_flow_sccm="10",
                inert_gas="Ar",
                inert_gas_flow_original="30 sccm",
                inert_gas_flow_sccm="30",
                gas_composition_summary="C2H2 added to the 30 sccm Ar / 10 sccm H2 annealing flow",
                process_note="Stage III; no exact growth duration is reported. The chamber is pumped out and the sample cools in vacuum after CVD.",
            ),
        ]
        product = yield_row(
            run_id,
            primary_yield_metric="qualitative CNT growth",
            yield_original="CNT growth confirmed by post-growth SEM; quantitative yield not reported",
            yield_definition_original="ex-situ SEM confirmation across the repeated in-situ runs",
            yield_standardization_note="No mass yield is inferred; the paper only states that yields are similar across routes.",
            CNT_type_reported="predominantly multi-walled carbon nanotubes",
            CNT_type_confirmed="predominantly multi-walled, partly defective CNTs",
            product_mixture_summary="predominantly MWCNTs with some bamboo-type structures and graphite-cage-encapsulated catalyst particles",
            CNT_type_evidence="post-growth SEM and TEM",
            outer_diameter_mean_nm=item["diameter_mean"] or "not_reported",
            outer_diameter_range_nm=item["diameter_range"] or "not_reported",
            morphology="entangled MWCNTs with some bamboo-type structures",
            characterization_methods="in-situ GIXRD; ex-situ SEM; HR-TEM",
            notes=item["diameter_note"],
        )
        cost = cost_row(
            run_id,
            scale_level_demonstrated="synchrotron in-situ cold-wall reactor experiment",
            scale_level_claimed="not_reported",
            quantitative_cost_reported="not_reported",
            review_note="No quantitative cost or production scale is reported.",
        )
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].extend(stages)
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        prefix = f"{source_id}_EV_{index:02d}"
        tables["evidence_index"].extend(
            [
                evidence_row(source_id, f"{prefix}_CAT_METHOD", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_5BFC850BD9A3FF3004B9", "Methods report the two possible oxide supports, nominal 8 nm Fe film, annealing recipe and 12 nominally repeated samples."),
                evidence_row(source_id, f"{prefix}_CAT_ROUTE", run_id, "catalyst_system", catalyst["catalyst_id"], "phase_or_state_summary", item["result_span"], item["summary"]),
                evidence_row(source_id, f"{prefix}_REACTOR", run_id, "reactor_process_gas", stages[0]["process_stage_id"], "reactor_type", "SPAN_AA0F98EE4E7F69B00512", "Experimental section identifies the synchrotron cold-wall reactor chamber."),
                evidence_row(source_id, f"{prefix}_ANNEAL", run_id, "reactor_process_gas", stages[0]["process_stage_id"], direct_anneal_fields, "SPAN_AEE4186784B2DBE19DBB", "Methods report 750 C annealing in 30 sccm Ar and 10 sccm H2 at approximately 150 mbar."),
                evidence_row(source_id, f"{prefix}_ANNEAL_KPA", run_id, "reactor_process_gas", stages[0]["process_stage_id"], "pressure_kPa", "SPAN_AEE4186784B2DBE19DBB", "Approximate conversion of ~150 mbar to ~15 kPa; original pressure retained.", value_status="normalized"),
                evidence_row(source_id, f"{prefix}_GROW", run_id, "reactor_process_gas", stages[1]["process_stage_id"], direct_growth_fields, "SPAN_AEE4186784B2DBE19DBB", "Methods report addition of 1 sccm acetylene to the Ar/H2 flow; Figure 1 and Results confirm 750 C for growth."),
                evidence_row(source_id, f"{prefix}_GROW_KPA", run_id, "reactor_process_gas", stages[1]["process_stage_id"], "pressure_kPa", "SPAN_AEE4186784B2DBE19DBB", "Approximate conversion of ~150 mbar to ~15 kPa; original pressure retained.", value_status="normalized"),
                evidence_row(source_id, f"{prefix}_RESULT", run_id, "yield_quality", product["product_id"], "record_level", item["result_span"], item["summary"]),
                evidence_row(source_id, f"{prefix}_PRODUCT_COMMON", run_id, "yield_quality", product["product_id"], "record_level", "SPAN_E930D3421D08A0FED2BC", "Results confirm CNT growth for all main-series samples and report predominantly multi-walled products with bamboo-type structures and encapsulated catalyst particles."),
                evidence_row(source_id, f"{prefix}_COST", run_id, "cost_scale_review", run_id, "record_level", "SPAN_AA0F98EE4E7F69B00512", "The source demonstrates a synchrotron cold-wall reactor experiment; cost and production scale are not reported.", value_status="review_assessment"),
            ]
        )

    etem = source_run_row(
        source_id,
        "ETEM_CNT_NUCLEATION",
        "ETEM Fe nanoparticle restructuring and CNT nucleation",
        "Separate environmental-TEM experiment showing reduction/restructuring of an Fe nanoparticle and lift-off nucleation of a CNT carbon cap under acetylene.",
        target_track="CNT_nucleation_mechanism",
    )
    etem_id = etem["run_id"]
    etem_catalyst = catalyst_row(
        etem_id,
        catalyst_label="Fe film on SiOx-covered Mo-TEM grid",
        active_metals="Fe",
        support_material="SiOx-covered Mo-TEM grid",
        preparation_method="thermal evaporation",
        preparation_detail="0.7 nm Fe film; lamp heated in air before ETEM loading",
        activation_condition="1.3 mbar NH3 at 650 C for 1 hour; treatment did not fully reduce oxidized Fe",
        phase_or_state_summary="initially oxidized Fe nanoparticle that restructures/reduces under acetylene",
    )
    etem_stages = [
        process_row(
            etem_id,
            1,
            "NH3_pretreatment",
            reactor_type="modified environmental TEM with differential pumping",
            temperature_setpoint_C="650",
            holding_time_min="60",
            pressure_original="1.3 mbar",
            pressure_kPa="0.13",
            cofeed_or_reactive_gas="NH3",
            process_note="The low-pressure NH3 treatment was insufficient to fully reduce the oxidized Fe catalyst.",
        ),
        process_row(
            etem_id,
            2,
            "ETEM_acetylene_CNT_nucleation",
            reactor_type="modified environmental TEM with differential pumping",
            temperature_setpoint_C="650",
            pressure_original="~10^-2 mbar",
            pressure_kPa="~0.001",
            carbon_source="undiluted C2H2",
            gas_composition_summary="undiluted acetylene under ETEM differential-pumping conditions",
            process_note="Figure 6 records Fe-particle restructuring, reduction and CNT nucleation; exact growth duration is not reported.",
        ),
    ]
    etem_product = yield_row(
        etem_id,
        primary_yield_metric="qualitative CNT nucleation observation",
        yield_original="CNT nucleation observed by carbon-cap lift-off",
        yield_definition_original="time-resolved ETEM observation",
        yield_standardization_note="No bulk yield or tube diameter is inferred from the image sequence.",
        CNT_type_reported="carbon nanotube; wall number not reported",
        CNT_type_confirmed="CNT nucleation from reduced Fe particle",
        product_mixture_summary="single observed CNT nucleation sequence; bulk product composition not applicable",
        CNT_type_evidence="ETEM image sequence and FFT",
        morphology="carbon cap lifts off from a reduced Fe particle and develops into a CNT",
        characterization_methods="environmental TEM; FFT; time-resolved video",
    )
    etem_cost = cost_row(
        etem_id,
        scale_level_demonstrated="environmental-TEM mechanistic experiment",
        scale_level_claimed="not_reported",
        quantitative_cost_reported="not_reported",
        review_note="Mechanistic microscopy experiment; no production cost or scale is reported.",
    )
    tables["source_run"].append(etem)
    tables["catalyst_system"].append(etem_catalyst)
    tables["reactor_process_gas"].extend(etem_stages)
    tables["yield_quality"].append(etem_product)
    tables["cost_scale_review"].append(etem_cost)
    tables["evidence_index"].extend(
        [
            evidence_row(source_id, f"{source_id}_EV_04_CAT", etem_id, "catalyst_system", etem_catalyst["catalyst_id"], "record_level", "SPAN_C91CFC18784746E1E6CD", "Methods report the 0.7 nm Fe/SiOx/Mo-TEM preparation, air heating and 1.3 mbar NH3 treatment at 650 C for 1 hour."),
            evidence_row(source_id, f"{source_id}_EV_04_PRETREAT", etem_id, "reactor_process_gas", etem_stages[0]["process_stage_id"], "stage_type;reactor_type;temperature_setpoint_C;pressure_original;cofeed_or_reactive_gas", "SPAN_3883E4C962DE97B43DA1", "Methods report the modified ETEM and NH3 pretreatment at 650 C and 1.3 mbar for 1 hour."),
            evidence_row(source_id, f"{source_id}_EV_04_PRETREAT_TIME", etem_id, "reactor_process_gas", etem_stages[0]["process_stage_id"], "holding_time_min", "SPAN_3883E4C962DE97B43DA1", "Normalized conversion of the reported 1 hour pretreatment to 60 minutes.", value_status="normalized"),
            evidence_row(source_id, f"{source_id}_EV_04_PRETREAT_KPA", etem_id, "reactor_process_gas", etem_stages[0]["process_stage_id"], "pressure_kPa", "SPAN_3883E4C962DE97B43DA1", "Normalized conversion of 1.3 mbar to 0.13 kPa.", value_status="normalized"),
            evidence_row(source_id, f"{source_id}_EV_04_GROW", etem_id, "reactor_process_gas", etem_stages[1]["process_stage_id"], "stage_type;reactor_type;temperature_setpoint_C;pressure_original;carbon_source;gas_composition_summary", "SPAN_E8FA5612372E2AEF5D00", "Methods report undiluted acetylene at approximately 10^-2 mbar; Figure 6 reports the 650 C ETEM sequence."),
            evidence_row(source_id, f"{source_id}_EV_04_GROW_TEMP", etem_id, "reactor_process_gas", etem_stages[1]["process_stage_id"], "temperature_setpoint_C", "SPAN_D6B162647D9169108E8C", "Results identify the ETEM image sequence at 650 C."),
            evidence_row(source_id, f"{source_id}_EV_04_GROW_KPA", etem_id, "reactor_process_gas", etem_stages[1]["process_stage_id"], "pressure_kPa", "SPAN_E8FA5612372E2AEF5D00", "Normalized conversion of approximately 10^-2 mbar to approximately 0.001 kPa.", value_status="normalized"),
            evidence_row(source_id, f"{source_id}_EV_04_RESULT", etem_id, "yield_quality", etem_product["product_id"], "record_level", "SPAN_0B70AB2C95BE40F9310A", "The ETEM sequence shows carbon-cap lift-off and CNT nucleation from a reduced Fe particle."),
            evidence_row(source_id, f"{source_id}_EV_04_COST", etem_id, "cost_scale_review", etem_id, "record_level", "SPAN_C91CFC18784746E1E6CD", "The work demonstrates an ETEM mechanistic experiment and reports no cost or production scale.", value_status="review_assessment"),
        ]
    )
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{source_id}_ISS_REPLICATE_GROUPING",
                source_id,
                tables["source_run"][0]["run_id"],
                "series_members_not_individually_resolvable",
                "source_run",
                tables["source_run"][0]["run_id"],
                "run_summary",
                "The article reports 12 nominally repeated in-situ XRD runs but publishes three representative/grouped phase-evolution cases. Three group-level records are retained; nine unspecified members are not fabricated.",
                evidence_ids=f"{source_id}_EV_01_CAT_METHOD;{source_id}_EV_03_RESULT",
                severity="high",
                conflicting_values="12 physical repeats | 3 published representative groups",
            ),
            issue_row(
                f"{source_id}_ISS_SUPPORT_MAPPING",
                source_id,
                tables["source_run"][0]["run_id"],
                "run_level_support_not_reported",
                "catalyst_system",
                tables["catalyst_system"][0]["catalyst_id"],
                "support_material",
                "Both SiO2 and Al2O3 supports were used, but the Figure 2-4 representative cases are not mapped to a specific support. The alternatives are retained without cross-run assignment.",
                evidence_ids=f"{source_id}_EV_01_CAT_METHOD",
                severity="medium",
                conflicting_values="SiO2 | Al2O3; figure mapping not reported",
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
                "result_linked_campaigns_in_paper": 4,
                "extracted_runs": 4,
                "negative_runs_preserved": 0,
                "matrix_note": "Three group-level in-situ XRD records preserve the Figure 2-4 phase routes representing 12 nominal repeats. The separate ETEM nucleation experiment is the fourth record; unspecified repeat members are not invented.",
            },
            "pdf_visual_review": {
                "completed": True,
                "pages_checked": [3, 4, 5, 6, 7, 16, 17, 18, 19, 20, 22],
                "objects_checked": ["Experimental Section recipes", "Figure 1 four-stage CVD schematic", "Figures 2-4 phase-route XRD/SEM/TEM panels", "Figure 3 and Figure 4 diameter-linked samples", "Figure 6 ETEM nucleation sequence"],
            },
            "pressure_policy_check": "The source reports approximately 150 mbar for the main CVD and separate 1.3 mbar / approximately 10^-2 mbar ETEM conditions. Original approximate forms are retained; kPa fields are explicitly normalized and preserve approximation.",
            "cross_run_inheritance_check": "The 26 nm and 24 nm distributions are confined to the Figure 3 and Figure 4 samples. Figure 2 remains without a diameter. SiO2/Al2O3 support alternatives are not assigned to individual figures because the mapping is absent.",
            "unit_policy_check": "Visual review confirms 26 +/- 11 nm (9-50 nm), 24 +/- 9 nm (11-49 nm), approximately 150 mbar, 30/10/1 sccm and 750 C for the main XRD series.",
            "conflict_check": "No contradictory product values were found. The unresolved 12-repeat-to-3-group representation and support mapping are logged rather than silently expanded or assigned.",
        },
    )
    update_manifest(
        source_id,
        "extracted_needs_supervisory_review",
        package_path=package.relative_to(REDO_ROOT).as_posix(),
    )
    return package


def build_lit_a2ad11a6(context: SourceContext) -> Path:
    """Lin et al. 2015, four patterned VACNT-bundle field emitters."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    samples = [
        {
            "code": "A",
            "arrangement": "square",
            "pitch": "30",
            "ratio": "2",
            "bundle_density": "1.0 x 10^5 cm^-2",
            "turn_on": "2.0",
            "beta": "1020",
            "stability": "higher current density with stronger long-term fluctuations",
        },
        {
            "code": "B",
            "arrangement": "square",
            "pitch": "45",
            "ratio": "3",
            "bundle_density": "4.9 x 10^4 cm^-2",
            "turn_on": "2.8",
            "beta": "840",
            "stability": "most stable long-term field-emission response among the four samples",
        },
        {
            "code": "C",
            "arrangement": "hexagonal",
            "pitch": "30",
            "ratio": "2",
            "bundle_density": "1.6 x 10^5 cm^-2",
            "turn_on": "1.6",
            "beta": "1770",
            "stability": "lowest turn-on field and highest enhancement factor, with stronger long-term fluctuations",
        },
        {
            "code": "D",
            "arrangement": "hexagonal",
            "pitch": "45",
            "ratio": "3",
            "bundle_density": "7.0 x 10^4 cm^-2",
            "turn_on": "2.5",
            "beta": "905",
            "stability": "more stable long-term response than the R=2 samples",
        },
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [
            source_master_row(
                context,
                "Four Table 1 patterned VACNT-bundle samples A-D are retained as separate result-linked runs and reconciled to Table 2 field-emission results.",
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
    for index, sample in enumerate(samples, start=1):
        run = source_run_row(
            source_id,
            f"SAMPLE_{sample['code']}",
            f"Sample {sample['code']}: {sample['arrangement']} VACNT bundles, R={sample['ratio']}",
            (
                f"Thermal-CVD VACNT bundles on a photolithographically patterned Fe/Al/Si catalyst; "
                f"{sample['arrangement']} arrangement, {sample['pitch']} micrometre pitch, "
                f"15 micrometre bundle height, and the source-linked Table 2 field-emission result."
            ),
        )
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label="3 nm Fe catalyst film on 5 nm Al buffer over patterned Si",
            active_metals="Fe",
            support_material="silicon substrate with 5 nm Al buffer layer",
            preparation_method="photolithography followed by electron-beam evaporation",
            preparation_detail=(
                f"10 micrometre circular catalyst sites in a {sample['arrangement']} arrangement "
                f"with {sample['pitch']} micrometre centre-to-centre pitch; 5 nm Al and 3 nm Fe films"
            ),
        )
        growth = process_row(
            run_id,
            1,
            "thermal_chemical_vapor_deposition",
            reactor_type="thermal CVD system",
            temperature_setpoint_C="750",
            pressure_original="4 Torr working pressure",
            pressure_kPa="0.533",
            carbon_source="C2H2",
            process_note=(
                "Growth time was adjusted to obtain a 15 micrometre VACNT-bundle height; "
                "the exact time and acetylene flow were not reported."
            ),
        )
        product = yield_row(
            run_id,
            primary_yield_metric="not_reported",
            yield_original="not_reported",
            yield_definition_original="not_reported",
            secondary_result_summary=(
                f"Sample {sample['code']} turn-on field {sample['turn_on']} V micrometre^-1, "
                f"enhancement factor {sample['beta']}, and VACNT-bundle number density "
                f"{sample['bundle_density']}; {sample['stability']}."
            ),
            CNT_type_reported="vertically aligned carbon nanotubes (VACNTs)",
            CNT_type_confirmed="vertically aligned CNT bundle morphology confirmed by SEM; wall count not reported",
            product_mixture_summary="not_reported",
            CNT_type_evidence="SEM shows cylindrical bundles composed of dense CNTs aligned vertically to the Si substrate",
            length_summary="bundle height 15 micrometres; individual-CNT length not separately reported",
            morphology="cylindrical VACNT bundle approximately 10 micrometres in diameter and 15 micrometres high",
            alignment_or_array=(
                f"vertically aligned CNT bundles in a {sample['arrangement']} array at "
                f"{sample['pitch']} micrometre pitch; interbundle-distance/height ratio R={sample['ratio']}"
            ),
            characterization_methods="SEM; field-emission J-E and Fowler-Nordheim analysis; long-term stability test; fluorescence imaging",
            application_property_summary=(
                f"Field emitter: turn-on field {sample['turn_on']} V micrometre^-1, "
                f"enhancement factor {sample['beta']}, bundle number density {sample['bundle_density']}."
            ),
            notes="Field-emission performance is reported for the patterned bundle array rather than an individual CNT.",
        )
        cost = cost_row(
            run_id,
            scale_level_demonstrated="laboratory patterned-substrate CVD experiment",
            scale_level_claimed="not_reported",
            scale_evidence_summary="Photolithography, thin-film deposition, thermal CVD, and field-emission testing were demonstrated on patterned silicon samples.",
            quantitative_cost_reported="not_reported",
        )
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].append(growth)
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        prefix = f"{source_id}_EV_{index:02d}"
        tables["evidence_index"].extend(
            [
                evidence_row(
                    source_id,
                    f"{prefix}_CAT_METHOD",
                    run_id,
                    "catalyst_system",
                    catalyst["catalyst_id"],
                    "record_level",
                    "SPAN_E2FBC3E9B5EFD0FA74D0",
                    "Methods report the patterned Si substrate, 5 nm Al buffer, 3 nm Fe catalyst, electron-beam evaporation, and the shared thermal-CVD recipe.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_CAT_PATTERN",
                    run_id,
                    "catalyst_system",
                    catalyst["catalyst_id"],
                    "record_level",
                    "SPAN_C7B1B6B201724CDE9304",
                    f"Printed Table 1 maps sample {sample['code']} to its {sample['arrangement']} arrangement, {sample['pitch']} micrometre pitch, 15 micrometre height, and R={sample['ratio']}.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_PROCESS",
                    run_id,
                    "reactor_process_gas",
                    growth["process_stage_id"],
                    "stage_type;reactor_type;temperature_setpoint_C;pressure_original;carbon_source;process_note",
                    "SPAN_E2FBC3E9B5EFD0FA74D0",
                    "Methods identify acetylene thermal CVD at 750 C and 4 Torr; growth time controls the 15 micrometre bundle height but its exact value is omitted.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_PRESSURE_NORMALIZED",
                    run_id,
                    "reactor_process_gas",
                    growth["process_stage_id"],
                    "pressure_kPa",
                    "SPAN_E2FBC3E9B5EFD0FA74D0",
                    "The reported 4 Torr working pressure is converted to 0.533 kPa.",
                    value_status="normalized",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_PRODUCT",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "record_level",
                    "SPAN_E2FBC3E9B5EFD0FA74D0",
                    "Methods and SEM results report dense, vertically aligned cylindrical CNT bundles about 10 micrometres in diameter and 15 micrometres high.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_ARRANGEMENT",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "record_level",
                    "SPAN_C7B1B6B201724CDE9304",
                    f"Table 1 links sample {sample['code']} to the run-specific array geometry and pitch.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_FIELD_EMISSION",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "record_level",
                    "SPAN_DD36536E961186B124AE",
                    f"Printed Table 2 links sample {sample['code']} to turn-on field, enhancement factor, and bundle number density.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_STABILITY",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "record_level",
                    "SPAN_5AA42E57A380B33C9DE9",
                    "The long-term field-emission discussion distinguishes the more fluctuating R=2 samples from the more stable R=3 samples and identifies sample B as most stable.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_COST",
                    run_id,
                    "cost_scale_review",
                    run_id,
                    "record_level",
                    "SPAN_E2FBC3E9B5EFD0FA74D0",
                    "The demonstrated patterned-substrate CVD setup is assessed as laboratory scale; no quantitative cost is reported.",
                    value_status="review_assessment",
                ),
            ]
        )
        tables["review_issue_log"].append(
            issue_row(
                f"{source_id}_ISS_{sample['code']}_GROWTH_TIME",
                source_id,
                run_id,
                "missing_run_parameter",
                "reactor_process_gas",
                growth["process_stage_id"],
                "holding_time_min",
                "The source says growth time was adjusted to control the common 15 micrometre bundle height but does not report the time for this sample; no value is inferred.",
                evidence_ids=f"{prefix}_PROCESS",
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
                "result_linked_campaigns_in_paper": 4,
                "extracted_runs": 4,
                "negative_runs_preserved": 0,
                "matrix_note": "Samples A-D in printed Table 1 are four distinct patterned catalyst/growth products and are mapped one-to-one to the printed Table 2 field-emission outcomes.",
            },
            "pdf_visual_review": {
                "completed": True,
                "pages_checked": [1, 2, 3, 4, 5, 6],
                "objects_checked": ["Methods recipe", "Table 1 sample/geometry matrix", "Figures 1-2 SEM morphology", "Table 2 field-emission metrics", "Figures 4-6 stability and fluorescence", "Conclusions"],
            },
            "pressure_policy_check": "The reported 4 Torr working pressure is retained and normalized to 0.533 kPa; no unreported atmospheric pressure is introduced.",
            "cross_run_inheritance_check": "Each sample retains only its own Table 1 geometry and Table 2 field-emission values. Shared catalyst/CVD conditions are explicitly stated as common in Methods.",
            "unit_policy_check": "The PDF confirms 5 nm Al, 3 nm Fe, 750 C, 4 Torr, 10/15/30/45 micrometre dimensions, and the four printed field-emission values.",
            "conflict_check": "No contradictory sample mapping was found. Exact growth times and acetylene flow are absent and remain unfilled, with a per-run issue recorded.",
        },
    )
    update_manifest(
        source_id,
        "extracted_needs_supervisory_review",
        package_path=package.relative_to(REDO_ROOT).as_posix(),
    )
    return package


def build_lit_ed1d628b(context: SourceContext) -> Path:
    """Bouanis et al. 2011, Ru-SAM hot-filament CVD comparison and temperature series."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    runs = [
        {
            "code": "HF_COMPARE_OFF_900",
            "label": "Hot-filament comparison: classical CVD at 900 C",
            "series": "hot-filament comparison",
            "temperature": "900",
            "hot_filament": False,
            "result_span": "SPAN_E3EA52282556050D813D",
            "result": "SWCNTs formed, but with lower density and shorter length than the hot-filament-assisted comparison sample",
            "cnt_type": "single-walled carbon nanotubes (SWCNTs)",
            "confirmed": "RBM peaks at 135 and 197 cm^-1 confirm SWCNTs",
            "rbm": "135 and 197 cm^-1",
            "diameter": "1.2-1.8",
            "raman_value": "0.15",
            "raman_summary": "I_D/I_G 0.15",
            "morphology": "lower-density, shorter SWCNT film than the 900 C hot-filament-assisted comparison",
            "alignment": "not_reported",
        },
        {
            "code": "HF_COMPARE_ON_900",
            "label": "Hot-filament comparison: HFCVD at 900 C",
            "series": "hot-filament comparison",
            "temperature": "900",
            "hot_filament": True,
            "result_span": "SPAN_E3EA52282556050D813D",
            "result": "Hot-filament assistance increased RBM intensity, RBM peak count, SWCNT density, and SWCNT length",
            "cnt_type": "single-walled carbon nanotubes (SWCNTs)",
            "confirmed": "stronger and more numerous RBM modes plus SEM morphology confirm SWCNTs",
            "rbm": "multiple stronger RBM modes; exact peak list not stated in prose",
            "diameter": "",
            "raman_value": "0.09",
            "raman_summary": "I_D/I_G 0.09",
            "morphology": "higher-density, longer SWCNT film than the 900 C classical-CVD comparison",
            "alignment": "not_reported",
        },
        {
            "code": "TEMP_HF_800",
            "label": "HFCVD temperature series at 800 C",
            "series": "HFCVD temperature series",
            "temperature": "800",
            "hot_filament": True,
            "result_span": "SPAN_0BDE4DD2E4FF92B19BEC",
            "result": "No CNT growth was observed; Raman features were very weak, I_D/I_G was near unity, and no RBM peaks were observed",
            "cnt_type": "not_observed",
            "confirmed": "no CNT growth by SEM/AFM and no RBM evidence",
            "rbm": "not_observed",
            "diameter": "",
            "raman_value": "",
            "raman_summary": "I_D/I_G near unity",
            "morphology": "no CNT growth observed",
            "alignment": "not_applicable",
        },
        {
            "code": "TEMP_HF_900",
            "label": "HFCVD temperature series at 900 C",
            "series": "HFCVD temperature series",
            "temperature": "900",
            "hot_filament": True,
            "result_span": "SPAN_0BDE4DD2E4FF92B19BEC",
            "result": "Quite dense, well-crystallized SWCNTs with RBM-derived diameters of 1.78, 1.66, and 1.28 nm",
            "cnt_type": "single-walled carbon nanotubes (SWCNTs)",
            "confirmed": "RBM peaks at 139, 149, and 193 cm^-1 plus SEM/AFM confirm SWCNTs",
            "rbm": "139, 149 and 193 cm^-1",
            "diameter": "1.28-1.78",
            "raman_value": "",
            "raman_summary": "I_D/I_G lower than 0.09",
            "morphology": "quite dense SWCNT film",
            "alignment": "less straight and less aligned than the 1000 C product",
        },
        {
            "code": "TEMP_HF_1000",
            "label": "HFCVD temperature series at 1000 C",
            "series": "HFCVD temperature series",
            "temperature": "1000",
            "hot_filament": True,
            "result_span": "SPAN_0BDE4DD2E4FF92B19BEC",
            "result": "Quite dense SWCNTs with a larger-diameter preference and straighter, better-aligned morphology than at lower temperatures",
            "cnt_type": "single-walled carbon nanotubes (SWCNTs)",
            "confirmed": "RBM peaks at 138 and 196 cm^-1 plus SEM/AFM confirm SWCNTs",
            "rbm": "138 and 196 cm^-1",
            "diameter": "",
            "raman_value": "",
            "raman_summary": "I_D/I_G approximately 0.2",
            "morphology": "quite dense SWCNT film; straighter nanotubes than at lower temperatures",
            "alignment": "better aligned than products grown at lower temperatures",
        },
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [
            source_master_row(
                context,
                "The two-sample 900 C hot-filament comparison and the separate three-temperature HFCVD series are retained as five figure-linked records; the duplicate nominal 900 C HFCVD condition is not silently deduplicated across series.",
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
            (
                f"{item['series']} using a Ru-porphyrin-derived catalyst at {item['temperature']} C for 30 min; "
                f"{item['result']}."
            ),
        )
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label="Ru tetraphenyl-porphyrin self-assembled-monolayer-derived catalyst",
            active_metals="Ru",
            support_material="RCA-cleaned silicon oxide substrate",
            precursor_summary="Ru tetraphenyl porphyrin carbonyl complex, 1 mg/mL in anhydrous dichloromethane",
            preparation_method="pyridine-terminated silanisation followed by Ru-porphyrin self-assembly",
            preparation_detail=(
                "Silanisation overnight in anhydrous toluene under argon using 100 mg organosilane per 100 mL; "
                "the pyridine-functionalized substrate anchors the Ru-porphyrin monolayer"
            ),
        )
        activation = process_row(
            run_id,
            1,
            "hydrogen_hot_filament_activation",
            reactor_type="quartz-tube hot-filament CVD system",
            holding_time_min="5",
            pressure_original="90 mbar",
            pressure_kPa="9",
            reducing_gas="hydrogen",
            process_note="Hydrogen filament operated at 160 W and approximately 1900 C to burn the organic monolayer and free the Ru catalyst.",
        )
        growth_note = (
            "Methane filament was not powered for this classical-CVD comparison condition."
            if not item["hot_filament"]
            else "Methane filament operated at 1700 C and 120 W; hot-filament methane pre-dissociation was enabled."
        )
        growth = process_row(
            run_id,
            2,
            ("classical_thermal_CVD" if not item["hot_filament"] else "hot_filament_assisted_CVD"),
            reactor_type=("quartz-tube thermal CVD" if not item["hot_filament"] else "quartz-tube hot-filament-assisted CVD"),
            reactor_setup_summary="Quartz tube in a cylindrical heater with separate 0.38 mm tungsten filaments for methane and hydrogen; residual base pressure 10^-6 mbar before gas feed.",
            temperature_setpoint_C=item["temperature"],
            holding_time_min="30",
            carbon_source="methane",
            carbon_source_flow_original="10 sccm in the figure caption",
            carbon_source_flow_sccm="10",
            reducing_gas="hydrogen",
            gas_composition_summary="Methods state CH4 relative concentration 10%; figure captions state CH4 10 sccm.",
            process_note=growth_note + " The actual CNT-growth pressure and hydrogen flow were not reported.",
        )
        product = yield_row(
            run_id,
            primary_yield_metric="not_reported",
            yield_original="not_reported",
            yield_definition_original="not_reported",
            secondary_result_summary=item["result"] + "; " + item["raman_summary"] + ".",
            CNT_type_reported=item["cnt_type"],
            CNT_type_confirmed=item["confirmed"],
            product_mixture_summary=("weak carbonaceous Raman signal with no CNT growth" if item["temperature"] == "800" else "not_reported"),
            CNT_type_evidence=("absence of RBM peaks and absence of CNTs in SEM/AFM" if item["temperature"] == "800" else "Raman RBM signatures with SEM and AFM morphology"),
            RBM_peak_reported=item["rbm"],
            outer_diameter_range_nm=item["diameter"],
            morphology=item["morphology"],
            alignment_or_array=item["alignment"],
            Raman_ratio_type="I_D/I_G",
            Raman_ratio_value=item["raman_value"],
            characterization_methods="SEM; AFM; confocal Raman spectroscopy",
            notes=f"Result belongs to the {item['series']}; no gravimetric CNT yield was reported.",
        )
        cost = cost_row(
            run_id,
            scale_level_demonstrated="laboratory quartz-tube CVD experiment",
            scale_level_claimed="not_reported",
            scale_evidence_summary="A homemade quartz-tube reactor with two independently powered tungsten filaments was used.",
            quantitative_cost_reported="not_reported",
        )
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].extend([activation, growth])
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        prefix = f"{source_id}_EV_{index:02d}"
        tables["evidence_index"].extend(
            [
                evidence_row(
                    source_id,
                    f"{prefix}_CAT_PREP",
                    run_id,
                    "catalyst_system",
                    catalyst["catalyst_id"],
                    "record_level",
                    "SPAN_B5462E0A116C82655E31",
                    "Catalyst preparation begins with overnight pyridine-terminated silanisation of RCA-cleaned silicon oxide using 100 mg organosilane per 100 mL under argon.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_CAT_RU",
                    run_id,
                    "catalyst_system",
                    catalyst["catalyst_id"],
                    "record_level",
                    "SPAN_2B1577F61DFF3835179A",
                    "The source identifies the Ru tetraphenyl-porphyrin carbonyl complex at 1 mg/mL in anhydrous dichloromethane.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_CAT_ROUTE",
                    run_id,
                    "catalyst_system",
                    catalyst["catalyst_id"],
                    "record_level",
                    "SPAN_A95F611EB71455C4363A",
                    "The two-step route coordinates Ru ions in a self-assembled Ru-porphyrin monolayer to pyridine groups on the silanized substrate.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_ACTIVATION",
                    run_id,
                    "reactor_process_gas",
                    activation["process_stage_id"],
                    "stage_type;reactor_type;holding_time_min;pressure_original;reducing_gas;process_note",
                    "SPAN_D62C8FD165FBF1432AA6",
                    "Before growth, the sample receives 5 min of hydrogen at 90 mbar activated by a 160 W, approximately 1900 C hot filament.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_ACT_PRESSURE_NORMALIZED",
                    run_id,
                    "reactor_process_gas",
                    activation["process_stage_id"],
                    "pressure_kPa",
                    "SPAN_D62C8FD165FBF1432AA6",
                    "The reported 90 mbar activation pressure is converted to 9 kPa.",
                    value_status="normalized",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_REACTOR",
                    run_id,
                    "reactor_process_gas",
                    growth["process_stage_id"],
                    "record_level",
                    "SPAN_202462C1D67D482FDC2D",
                    "The homemade reactor is a quartz tube in a cylindrical heater with methane/H2 feeds, a 10^-6 mbar residual base pressure, and two 0.38 mm tungsten filaments.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_GROWTH_COMMON",
                    run_id,
                    "reactor_process_gas",
                    growth["process_stage_id"],
                    "record_level",
                    "SPAN_D62C8FD165FBF1432AA6",
                    "Methods report 30 min growth from 800 to 1000 C with methane at 10% relative concentration and classical or hot-filament-assisted operation.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_GROWTH_FIGURE",
                    run_id,
                    "reactor_process_gas",
                    growth["process_stage_id"],
                    "record_level",
                    ("SPAN_026DE49B573C0425026F" if item["series"] == "hot-filament comparison" else "SPAN_47FFC0CDCED5301153DA"),
                    "Figure-linked growth evidence supplies the series temperature, 30 min duration, and the caption's 10 sccm methane expression.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_HF_POWER",
                    run_id,
                    "reactor_process_gas",
                    growth["process_stage_id"],
                    "record_level",
                    ("SPAN_B5FDFDA52988DB545DCA" if item["hot_filament"] else "SPAN_D62C8FD165FBF1432AA6"),
                    ("The HFCVD methane filament is operated at 1700 C and 120 W." if item["hot_filament"] else "The source distinguishes the classical-CVD condition from the HFCVD condition."),
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_PRODUCT",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "record_level",
                    item["result_span"],
                    item["result"],
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_PRODUCT_QUALITY",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "record_level",
                    ("SPAN_D62C8FD165FBF1432AA6" if item["series"] == "hot-filament comparison" else "SPAN_151378D6306543221A0B"),
                    item["raman_summary"],
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_CHARACTERIZATION",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "record_level",
                    "SPAN_8E2F410747A370D06217",
                    "The products were characterized by AFM, SEM, and high-resolution confocal Raman spectroscopy.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_COST",
                    run_id,
                    "cost_scale_review",
                    run_id,
                    "record_level",
                    "SPAN_202462C1D67D482FDC2D",
                    "The demonstrated homemade quartz-tube/tungsten-filament setup is assessed as laboratory scale; the paper reports no quantitative cost.",
                    value_status="review_assessment",
                ),
            ]
        )
        if item["temperature"] == "1000":
            tables["evidence_index"].append(
                evidence_row(
                    source_id,
                    f"{prefix}_ALIGNMENT",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "record_level",
                    "SPAN_20C7F201F1FDCB4328C0",
                    "At 1000 C the CNTs are reported to be straighter and better aligned than at lower temperatures.",
                )
            )
        tables["review_issue_log"].extend(
            [
                issue_row(
                    f"{source_id}_ISS_{index:02d}_CH4_EXPRESSION",
                    source_id,
                    run_id,
                    "feed_reporting_ambiguity",
                    "reactor_process_gas",
                    growth["process_stage_id"],
                    "gas_composition_summary",
                    "Methods give methane as a 10% relative concentration, while the Figure 1/3 captions give 10 sccm. Both original expressions are retained; no total flow is inferred.",
                    evidence_ids=f"{prefix}_GROWTH_COMMON;{prefix}_GROWTH_FIGURE",
                    severity="high",
                    conflicting_values="10% relative concentration | 10 sccm",
                ),
                issue_row(
                    f"{source_id}_ISS_{index:02d}_GROWTH_PRESSURE",
                    source_id,
                    run_id,
                    "missing_run_parameter",
                    "reactor_process_gas",
                    growth["process_stage_id"],
                    "pressure_original",
                    "The paper reports 90 mbar for the pre-growth H2 activation and 10^-6 mbar as residual base pressure, but not the CNT-growth pressure; neither value is inherited into growth.",
                    evidence_ids=f"{prefix}_ACTIVATION;{prefix}_REACTOR",
                    severity="medium",
                ),
            ]
        )
    tables["review_issue_log"].append(
        issue_row(
            f"{source_id}_ISS_900_SERIES_IDENTITY",
            source_id,
            f"{source_id}_TEMP_HF_900",
            "series_identity_ambiguity",
            "yield_quality",
            f"{source_id}_TEMP_HF_900_PROD",
            "record_level",
            "The hot-filament comparison and the temperature series both contain a nominal 900 C HFCVD condition, but the paper does not state that they are the same physical specimen. They are retained as separate figure-linked records.",
            evidence_ids=f"{source_id}_EV_02_PRODUCT;{source_id}_EV_04_PRODUCT",
            severity="medium",
            conflicting_values="Figure 1/2 comparison series | Figure 3/4 temperature series",
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
                "result_linked_campaigns_in_paper": 5,
                "extracted_runs": 5,
                "negative_runs_preserved": 1,
                "matrix_note": "Two Figure 1/2 hot-filament-comparison records and three Figure 3/4 temperature-series records are retained. The two nominal 900 C HFCVD records remain separate because cross-series specimen identity is not stated.",
            },
            "pdf_visual_review": {
                "completed": True,
                "pages_checked": [2, 3, 4, 5],
                "objects_checked": ["catalyst preparation", "two-filament reactor recipe", "Figure 1 Raman hot-filament comparison", "Figure 2 SEM comparison", "Figure 3 temperature-series Raman", "Figure 4 SEM/AFM temperature series", "Conclusion"],
            },
            "pressure_policy_check": "The 90 mbar value is confined to pre-growth H2 activation and normalized to 9 kPa. Residual base pressure 10^-6 mbar is kept only in the reactor setup; growth pressure remains blank.",
            "cross_run_inheritance_check": "Figure 1/2 hot-filament outcomes and Figure 3/4 temperature outcomes are assigned only within their stated series. The failed 800 C condition is retained without successful-SWCNT diameter fields.",
            "unit_policy_check": "The PDF confirms 5 min, 90 mbar, approximately 1900 C/160 W activation, 30 min growth, 1700 C/120 W methane filament, and the printed Raman/diameter values. The 10% versus 10 sccm feed expressions are not silently reconciled.",
            "conflict_check": "Feed-expression ambiguity and duplicate nominal 900 C series identity are logged. No growth pressure or hydrogen flow is invented.",
        },
    )
    update_manifest(
        source_id,
        "extracted_needs_supervisory_review",
        package_path=package.relative_to(REDO_ROOT).as_posix(),
    )
    return package


def build_lit_d74c5abb(context: SourceContext) -> Path:
    """Jeon et al. 2008, Müller-catalyst serpentine-CNT orientation and mechanism matrix."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    runs = [
        {
            "code": "MULLER_ANGLE_0",
            "label": "Müller catalyst, gas-flow/step-edge angle 0 degrees",
            "kind": "orientation",
            "angle": "0",
            "result": "Mostly straight growth; more than 2 continuous regularly spaced turns were rare",
            "morphology": "mostly straight CNTs with rare serpentine sequences longer than 2 turns",
            "result_span": "SPAN_1370DDFC021988789B56",
        },
        {
            "code": "MULLER_ANGLE_45",
            "label": "Müller catalyst, gas-flow/step-edge angle 45 degrees",
            "kind": "orientation",
            "angle": "45",
            "result": "Serpentine CNTs formed; more than 20 continuous regular turns were rare and straight segments before turns were approximately 10-30 micrometres",
            "morphology": "serpentine CNTs with fewer than 20 continuous regular turns in most cases and approximately 10-30 micrometre straight segments",
            "result_span": "SPAN_1370DDFC021988789B56",
        },
        {
            "code": "MULLER_ANGLE_90",
            "label": "Müller catalyst, gas-flow/step-edge angle 90 degrees",
            "kind": "orientation",
            "angle": "90",
            "result": "More than 50 continuous serpentine turns were frequently observed and straight segments before turns were approximately 5-15 micrometres",
            "morphology": "dense serpentine CNTs with frequently more than 50 turns and approximately 5-15 micrometre straight segments",
            "result_span": "SPAN_1370DDFC021988789B56",
        },
        {
            "code": "FECL3_DENSITY_CONTROL",
            "label": "FeCl3 catalyst-density control",
            "kind": "fecl3_control",
            "angle": "",
            "result": "Concentrated FeCl3 regions produced extremely straight, dense CNTs, whereas sparse isolated catalyst locations initiated serpentine CNTs",
            "morphology": "spatially mixed straight/dense and serpentine/sparse CNT growth controlled by FeCl3 aggregation",
            "result_span": "SPAN_18592166DD97628E9131",
        },
        {
            "code": "MULLER_HFO2_BARRIER",
            "label": "Müller catalyst with HfO2 barrier stripes",
            "kind": "barrier",
            "angle": "",
            "result": "Serpentine lateral undulation was lost or became straight over the HfO2 barrier and resumed after crossing it",
            "morphology": "serpentine CNT becomes straight over the 1 nm HfO2 stripe and resumes lateral undulation beyond the barrier",
            "result_span": "SPAN_D84A8CC1672882E57CBC",
        },
        {
            "code": "MULLER_FLOW_GT100_SERIES",
            "label": "Müller catalyst, flow-rate series above 100 sccm",
            "kind": "high_flow_series",
            "angle": "",
            "result": "Flow rates greater than 100 sccm under the study growth conditions reduced the yield of serpentine CNTs",
            "morphology": "serpentine CNT morphology; run-resolved turn geometry not reported for the high-flow series",
            "result_span": "SPAN_F1DB05C888C5568D765B",
        },
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [
            source_master_row(
                context,
                "Six result-linked records preserve three Müller-catalyst orientation samples, one FeCl3 catalyst-density control, one HfO2-barrier mechanism sample, and one group-level high-flow low-yield series.",
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
        is_fecl3 = item["kind"] == "fecl3_control"
        is_high_flow = item["kind"] == "high_flow_series"
        run = source_run_row(
            source_id,
            item["code"],
            item["label"],
            item["result"],
            data_type=("experimental_series" if is_high_flow else "experimental_condition"),
        )
        run_id = run["run_id"]
        if is_fecl3:
            catalyst = catalyst_row(
                run_id,
                catalyst_label="FeCl3 in ethanol catalyst-density control",
                active_metals="Fe",
                support_material="quartz substrate",
                precursor_summary="1:10 solution of FeCl3 and ethanol",
                preparation_method="solution deposition; drying produced a concentrated aggregation stripe",
                preparation_detail="High-concentration FeCl3 stripe and sparse isolated catalyst regions coexist on the control substrate.",
            )
        else:
            modifier = (
                "Atomic-layer-deposited HfO2 stripes, 50 micrometres wide, 1 nm high, and 150 micrometre pitch, parallel to the quartz step edge"
                if item["kind"] == "barrier"
                else ""
            )
            catalyst = catalyst_row(
                run_id,
                catalyst_label="Fe-Mo Müller supramolecular cluster catalyst with Keggin-ion core",
                active_metals="Fe; Mo",
                support_material="cleaved quartz substrate",
                precursor_summary="Müller catalyst diluted in ethanol to 10^-7-10^-8 mol/L",
                preparation_method="wet deposition by cotton swab after quartz orientation and air annealing",
                preparation_modifier=modifier,
                preparation_detail="Quartz was cleaved to the desired orientation, annealed in air at 900 C for approximately 8 h, and coated with catalyst solution at one edge.",
            )
        stages: list[dict[str, str]] = []
        if is_fecl3:
            growth = process_row(
                run_id,
                1,
                "comparative_CVD_growth",
                reactor_type="quartz-tube CVD comparison",
                carbon_source="ethanol",
                process_note="The FeCl3 control is presented as a catalyst-density comparison under the study growth conditions; its pretreatment, exact orientation, and run-specific gas recipe are not separately reported.",
            )
            stages.append(growth)
        else:
            oxidation = process_row(
                run_id,
                1,
                "catalyst_oxidation",
                reactor_type="1-inch quartz tube",
                reactor_size_summary="1-inch quartz tube",
                temperature_setpoint_C="500",
                holding_time_min="60",
                process_note="Catalyst-coated quartz sample oxidized for one hour; oxidizing atmosphere not stated.",
            )
            reduction = process_row(
                run_id,
                2,
                "catalyst_reduction",
                reactor_type="1-inch quartz tube",
                temperature_setpoint_C="750",
                holding_time_min="60",
                reducing_gas="H2",
                reducing_gas_flow_original="100 sccm",
                reducing_gas_flow_sccm="100",
                inert_gas="Ar",
                inert_gas_flow_original="300 sccm",
                inert_gas_flow_sccm="300",
                gas_composition_summary="300 sccm Ar and 100 sccm H2",
                process_note="Nanoparticle reduction for one hour after Ar purge.",
            )
            if is_high_flow:
                growth = process_row(
                    run_id,
                    3,
                    "ethanol_CVD_high_flow_series",
                    reactor_type="1-inch quartz-tube CVD",
                    temperature_setpoint_C="880",
                    carbon_source="ethanol vapor from bubbler",
                    cofeed_or_reactive_gas="Ar and H2 carrier gases",
                    total_flow_original=">100 sccm; component flows not reported",
                    process_note="Group-level higher-flow series under the study growth conditions; exact points, gas split, and growth time are not reported.",
                )
            else:
                growth = process_row(
                    run_id,
                    3,
                    "ethanol_bubbler_CVD_growth",
                    reactor_type="1-inch quartz-tube CVD",
                    temperature_setpoint_C="880",
                    holding_time_min="30",
                    carbon_source="ethanol vapor from an ice-bath bubbler",
                    reducing_gas="H2",
                    reducing_gas_flow_original="10 sccm",
                    reducing_gas_flow_sccm="10",
                    inert_gas="Ar",
                    inert_gas_flow_original="20 sccm",
                    inert_gas_flow_sccm="20",
                    gas_composition_summary="20 sccm Ar and 10 sccm H2 passed through an ethanol bubbler in an ice bath",
                    process_note="CNT growth for approximately 30 min; reactor pressure not reported.",
                )
            stages.extend([oxidation, reduction, growth])
        product = yield_row(
            run_id,
            primary_yield_metric=("qualitative serpentine-CNT yield" if is_high_flow else "not_reported"),
            yield_original=("reduced yield at flow rates >100 sccm" if is_high_flow else "not_reported"),
            yield_definition_original=("qualitative comparison with the standard-flow growth" if is_high_flow else "not_reported"),
            secondary_result_summary=item["result"],
            CNT_type_reported="carbon nanotubes; wall number not assigned to this run",
            CNT_type_confirmed="not_reported",
            product_mixture_summary="not_reported",
            CNT_type_evidence="SEM identifies CNT structures; Table 1 AFM diameter samples are not mapped to synthesis-run identities",
            morphology=item["morphology"],
            alignment_or_array=(
                f"gas-flow direction at {item['angle']} degrees to the quartz step edge"
                if item["angle"]
                else "not_reported"
            ),
            characterization_methods=("SEM" if item["kind"] != "high_flow_series" else "not_reported"),
            notes="No gravimetric CNT yield or run-specific wall-count assignment is reported.",
        )
        cost = cost_row(
            run_id,
            scale_level_demonstrated="laboratory quartz-tube substrate-growth experiment",
            scale_level_claimed="not_reported",
            scale_evidence_summary=("A 1-inch quartz-tube sequence was demonstrated." if not is_fecl3 else "A catalyst-density comparison was demonstrated on quartz."),
            quantitative_cost_reported="not_reported",
        )
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].extend(stages)
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        prefix = f"{source_id}_EV_{index:02d}"
        if is_fecl3:
            tables["evidence_index"].extend(
                [
                    evidence_row(
                        source_id,
                        f"{prefix}_CATALYST",
                        run_id,
                        "catalyst_system",
                        catalyst["catalyst_id"],
                        "record_level",
                        "SPAN_1370DDFC021988789B56",
                        "The catalyst-density control uses a 1:10 FeCl3/ethanol solution.",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_GROWTH",
                        run_id,
                        "reactor_process_gas",
                        growth["process_stage_id"],
                        "record_level",
                        "SPAN_18592166DD97628E9131",
                        "Figure 2(a) is the FeCl3 catalyst-density growth control; run-specific pretreatment and gas values are not separately supplied.",
                    ),
                ]
            )
        else:
            tables["evidence_index"].extend(
                [
                    evidence_row(
                        source_id,
                        f"{prefix}_CAT_IDENTITY",
                        run_id,
                        "catalyst_system",
                        catalyst["catalyst_id"],
                        "record_level",
                        "SPAN_3B051C314C3B2B06568B",
                        "The Müller catalyst is a homogeneous Fe-Mo supramolecular cluster complex with a Keggin-ion core.",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_CAT_CONCENTRATION",
                        run_id,
                        "catalyst_system",
                        catalyst["catalyst_id"],
                        "record_level",
                        "SPAN_16ABDCA5B3F9C6ADC69B",
                        "The source reports Müller catalyst diluted in ethanol to 10^-7-10^-8 mol/L.",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_CAT_SUBSTRATE_PREP",
                        run_id,
                        "catalyst_system",
                        catalyst["catalyst_id"],
                        "record_level",
                        "SPAN_E1A5CF6B1964A30D5706",
                        "Quartz is oriented, annealed in air at 900 C for approximately 8 h, and coated at one edge with catalyst solution.",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_OXIDATION",
                        run_id,
                        "reactor_process_gas",
                        oxidation["process_stage_id"],
                        "stage_type;reactor_type;reactor_size_summary;temperature_setpoint_C;process_note",
                        "SPAN_E1A5CF6B1964A30D5706",
                        "The coated sample is oxidized for one hour at 500 C in a 1-inch quartz tube.",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_OXIDATION_TIME_NORMALIZED",
                        run_id,
                        "reactor_process_gas",
                        oxidation["process_stage_id"],
                        "holding_time_min",
                        "SPAN_E1A5CF6B1964A30D5706",
                        "One hour is normalized to 60 min.",
                        value_status="normalized",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_REDUCTION",
                        run_id,
                        "reactor_process_gas",
                        reduction["process_stage_id"],
                        "stage_type;reactor_type;temperature_setpoint_C;reducing_gas;reducing_gas_flow_original;reducing_gas_flow_sccm;inert_gas;inert_gas_flow_original;inert_gas_flow_sccm;gas_composition_summary;process_note",
                        "SPAN_E1A5CF6B1964A30D5706",
                        "Nanoparticles are reduced for one hour at 750 C in 300 sccm Ar and 100 sccm H2.",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_REDUCTION_TIME_NORMALIZED",
                        run_id,
                        "reactor_process_gas",
                        reduction["process_stage_id"],
                        "holding_time_min",
                        "SPAN_E1A5CF6B1964A30D5706",
                        "One hour is normalized to 60 min.",
                        value_status="normalized",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_GROWTH",
                        run_id,
                        "reactor_process_gas",
                        growth["process_stage_id"],
                        "record_level",
                        ("SPAN_F1DB05C888C5568D765B" if is_high_flow else "SPAN_E1A5CF6B1964A30D5706"),
                        ("The group-level >100 sccm series is reported to reduce serpentine yield." if is_high_flow else "Growth uses 20 sccm Ar and 10 sccm H2 through an ice-bath ethanol bubbler at 880 C for approximately 30 min."),
                    ),
                ]
            )
            if is_high_flow:
                tables["evidence_index"].append(
                    evidence_row(
                        source_id,
                        f"{prefix}_GROWTH_COMMON_CONTEXT",
                        run_id,
                        "reactor_process_gas",
                        growth["process_stage_id"],
                        "record_level",
                        "SPAN_E1A5CF6B1964A30D5706",
                        "The study's base growth context uses an ethanol bubbler at 880 C; the high-flow series does not report its component split or exact duration.",
                    )
                )
        if item["kind"] == "barrier":
            tables["evidence_index"].append(
                evidence_row(
                    source_id,
                    f"{prefix}_BARRIER_PREP",
                    run_id,
                    "catalyst_system",
                    catalyst["catalyst_id"],
                    "record_level",
                    "SPAN_D3E7FE17B6EAB20EEF18",
                    "ALD HfO2 stripes are 50 micrometres wide, 1 nm high, on 150 micrometre pitch, parallel to the step edge.",
                )
            )
        tables["evidence_index"].extend(
            [
                evidence_row(
                    source_id,
                    f"{prefix}_PRODUCT",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "record_level",
                    item["result_span"],
                    item["result"],
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_COST",
                    run_id,
                    "cost_scale_review",
                    run_id,
                    "record_level",
                    ("SPAN_18592166DD97628E9131" if is_fecl3 else "SPAN_E1A5CF6B1964A30D5706"),
                    "The demonstrated substrate-growth setup is assessed as laboratory scale; no quantitative cost is reported.",
                    value_status="review_assessment",
                ),
            ]
        )
        if item["kind"] == "orientation":
            tables["evidence_index"].append(
                evidence_row(
                    source_id,
                    f"{prefix}_ORIENTATION_GEOMETRY",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "record_level",
                    "SPAN_18592166DD97628E9131",
                    "The orientation comparison reports the run-linked straight-segment ranges and turn-count differences for the 0, 45, and 90 degree samples.",
                )
            )
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{source_id}_ISS_TABLE1_MAPPING",
                source_id,
                f"{source_id}_MULLER_ANGLE_90",
                "cross_run_result_mapping_missing",
                "yield_quality",
                f"{source_id}_MULLER_ANGLE_90_PROD",
                "outer_diameter_range_nm",
                "Table 1 reports seven AFM/SEM diameter-curvature samples but does not map them to the 0/45/90 degree, FeCl3, or HfO2 synthesis records. No diameter is inherited into those runs.",
                evidence_ids=f"{source_id}_EV_03_PRODUCT",
                severity="high",
            ),
            issue_row(
                f"{source_id}_ISS_FECL3_PROCESS",
                source_id,
                f"{source_id}_FECL3_DENSITY_CONTROL",
                "missing_run_parameter",
                "reactor_process_gas",
                f"{source_id}_FECL3_DENSITY_CONTROL_S01",
                "record_level",
                "The FeCl3 control is described as a growth experiment, but its exact pretreatment, orientation, temperature, flow split, duration, and pressure are not separately stated; standard Müller-run values are not copied into it.",
                evidence_ids=f"{source_id}_EV_04_GROWTH",
                severity="medium",
            ),
            issue_row(
                f"{source_id}_ISS_HIGH_FLOW_SERIES",
                source_id,
                f"{source_id}_MULLER_FLOW_GT100_SERIES",
                "series_resolution_limit",
                "reactor_process_gas",
                f"{source_id}_MULLER_FLOW_GT100_SERIES_S03",
                "total_flow_original",
                "Only the range >100 sccm and the reduced-yield outcome are reported for the high-flow controls; exact setpoints, repetitions, component split, and duration are unavailable, so one group-level record is retained.",
                evidence_ids=f"{source_id}_EV_06_GROWTH",
                severity="high",
                conflicting_values=">100 sccm series; exact points not reported",
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
                "result_linked_campaigns_in_paper": 6,
                "extracted_runs": 6,
                "negative_runs_preserved": 1,
                "matrix_note": "Three printed Figure 1 orientation samples, the Figure 2(a) FeCl3 density control, the Figure 2(b-c) HfO2 barrier sample, and one explicitly group-level >100 sccm low-yield series are retained.",
            },
            "pdf_visual_review": {
                "completed": True,
                "pages_checked": [1, 2, 3, 4, 5, 6],
                "objects_checked": ["Müller catalyst and CVD recipe", "Figure 1 orientation matrix", "Figure 2 FeCl3 and HfO2 controls", "Table 1 diameter-curvature matrix", "Figures 3-5 morphology/electrical data", "Conclusion"],
            },
            "pressure_policy_check": "The paper does not report reactor pressure for oxidation, reduction, or CNT growth; all pressure fields remain blank.",
            "cross_run_inheritance_check": "Orientation-specific turn counts and straight-segment lengths stay with their 0/45/90 degree samples. Table 1 diameters are not assigned because their synthesis-run mapping is absent. Standard Müller process values are not copied into the FeCl3 control.",
            "unit_policy_check": "One-hour oxidation/reduction durations are normalized to 60 min with explicit normalized evidence. Approximate 30 min growth and original sccm/temperature values are retained.",
            "conflict_check": "FeCl3 process incompleteness, Table 1 run mapping, and the unresolved >100 sccm series resolution are logged; no exact high-flow setpoint is fabricated.",
        },
    )
    update_manifest(
        source_id,
        "extracted_needs_supervisory_review",
        package_path=package.relative_to(REDO_ROOT).as_posix(),
    )
    return package


def build_lit_d5bd8bd5(context: SourceContext) -> Path:
    """Pint et al. 2009, odako SWNT growth on grafoil and carbon fibre."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    runs = [
        {
            "code": "GRAFOIL_LP_1P4",
            "substrate": "grafoil carbon surface",
            "pressure": "1.4",
            "pressure_kPa": "0.187",
            "duration": "15",
            "high_pressure": False,
            "result_span": "SPAN_2B1F5B3CCDAC6EE80D7A",
            "result": "Uniform, dense odako SWNT fibrils grew across the grafoil surface at 1.4 Torr for 15 min",
        },
        {
            "code": "GRAFOIL_HP_25",
            "substrate": "grafoil carbon surface",
            "pressure": "25",
            "pressure_kPa": "3.33",
            "duration": "30",
            "high_pressure": True,
            "result_span": "SPAN_2B1F5B3CCDAC6EE80D7A",
            "result": "Uniform, dense odako fibrils grew across the grafoil surface at 25 Torr for 30 min with faster growth",
        },
        {
            "code": "CARBON_FIBER_LP_1P4",
            "substrate": "carbon-fiber weave",
            "pressure": "1.4",
            "pressure_kPa": "0.187",
            "duration": "",
            "high_pressure": False,
            "result_span": "SPAN_2BB04E7179DCBF0C8169",
            "result": "Odako SWNT fibrils grew uniformly on catalyst-coated carbon-fiber surfaces at 1.4 Torr",
        },
        {
            "code": "CARBON_FIBER_HP_25",
            "substrate": "carbon-fiber weave",
            "pressure": "25",
            "pressure_kPa": "3.33",
            "duration": "",
            "high_pressure": True,
            "result_span": "SPAN_CDEC306C5C425415F047",
            "result": "Elevated-pressure odako growth produced longer fibrils on carbon-fiber surfaces and was demonstrated over a full weave strand",
        },
        {
            "code": "CARBON_FIBER_FE_ONLY_CONTROL",
            "substrate": "carbon-fiber surface",
            "pressure": "",
            "pressure_kPa": "",
            "duration": "",
            "high_pressure": False,
            "result_span": "SPAN_3C901043551AC486C7E3",
            "result": "A 1 nm Fe layer deposited directly on carbon fiber without the alumina overlayer produced no measurable CNT growth",
            "negative": True,
        },
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [
            source_master_row(
                context,
                "Four substrate-pressure odako products (grafoil and carbon fibre at 1.4 and 25 Torr) plus the Fe-only/no-alumina zero-growth control are retained. Representative Raman/TEM diameter data are not assigned because the specimen mapping is absent.",
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
        is_control = item.get("negative", False)
        run = source_run_row(
            source_id,
            item["code"],
            (f"Odako growth on {item['substrate']} at {item['pressure']} Torr" if not is_control else "Fe-only carbon-fiber control without Al2O3"),
            item["result"],
        )
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label=("1 nm e-beam Fe on carbon fiber without oxide support" if is_control else "1 nm Fe with 5 nm Al2O3 overlayer on carbon surface"),
            active_metals="Fe",
            support_material=item["substrate"],
            preparation_method="electron-beam deposition",
            preparation_detail=(
                "1 nm Fe deposited directly onto carbon fiber; no alumina overlayer"
                if is_control
                else "1 nm Fe deposited directly onto the carbon surface followed immediately by a 5 nm Al2O3 overlayer"
            ),
        )
        stages: list[dict[str, str]] = []
        if is_control:
            growth = process_row(
                run_id,
                1,
                "water_assisted_CVD_control",
                reactor_type="water-assisted CVD control",
                process_note="The Fe-only control was exposed to the study growth protocol, but its pressure, flow, activation, temperature, and duration are not separately identified.",
            )
            stages.append(growth)
        else:
            activation = process_row(
                run_id,
                1,
                "atomic_hydrogen_catalyst_activation",
                reactor_type="water-assisted CVD with tungsten hot filament",
                holding_time_min="0.5",
                reducing_gas="H2",
                process_note="30 s exposure to tungsten-hot-filament-generated atomic hydrogen immediately before growth after rapid insertion into a pre-heated furnace.",
            )
            growth = process_row(
                run_id,
                2,
                "water_assisted_acetylene_CVD_growth",
                reactor_type="water-assisted low-pressure CVD",
                temperature_setpoint_C="750",
                holding_time_min=item["duration"],
                pressure_original=f"{item['pressure']} Torr",
                pressure_kPa=item["pressure_kPa"],
                carbon_source="C2H2",
                carbon_source_flow_original="2 sccm",
                carbon_source_flow_sccm="2",
                reducing_gas="H2",
                reducing_gas_flow_original="400 sccm",
                reducing_gas_flow_sccm="400",
                cofeed_or_reactive_gas="H2O",
                cofeed_flow_original="2 sccm",
                cofeed_flow_sccm="2",
                gas_composition_summary="400 sccm H2, 2 sccm H2O, and 2 sccm C2H2",
                process_note=(
                    "Elevated pressure increases acetylene partial pressure and growth rate, with some double- and few-walled tubes forming amid the SWNT population."
                    if item["high_pressure"]
                    else "Low-pressure water-assisted odako growth."
                ),
            )
            stages.extend([activation, growth])
        if is_control:
            product = yield_row(
                run_id,
                primary_yield_metric="qualitative CNT growth observation",
                yield_original="no measurable carbon nanotube growth",
                yield_definition_original="control observation",
                secondary_result_summary=item["result"],
                CNT_type_reported="not_observed",
                CNT_type_confirmed="no measurable CNT growth",
                product_mixture_summary="not_reported",
                CNT_type_evidence="control experiment reports no measurable carbon nanotube growth",
                morphology="no CNT growth observed",
                alignment_or_array="not_applicable",
                characterization_methods="not_reported",
                notes="Negative control retained to preserve the demonstrated requirement for the alumina overlayer.",
            )
        else:
            product = yield_row(
                run_id,
                primary_yield_metric="not_reported",
                yield_original="not_reported",
                yield_definition_original="not_reported",
                secondary_result_summary=item["result"],
                CNT_type_reported=("predominantly single-walled carbon nanotubes with some double- and few-walled tubes" if item["high_pressure"] else "single-walled carbon nanotubes (SWNTs)"),
                CNT_type_confirmed="dense aligned SWNT fibrils identified by SEM; run-specific Raman/TEM specimen mapping not reported",
                product_mixture_summary=("SWNT population with some double- and few-walled CNTs" if item["high_pressure"] else "dense SWNT array fibrils"),
                CNT_type_evidence="The source identifies the odako products as dense SWNT arrays; elevated pressure introduces some double-/few-walled tubes.",
                wall_number_summary=("mainly single-walled with some double- and few-walled tubes" if item["high_pressure"] else "single-walled"),
                morphology=(
                    "cylindrical odako fibrils anchored to carbon fiber, with alumina flakes capping exposed fibril ends"
                    if "fiber" in item["substrate"]
                    else "individual compact odako fibrils of dense aligned SWNTs, with alumina flakes supporting catalyst at fibril tips"
                ),
                alignment_or_array="dense aligned SWNT arrays bundled into odako fibrils and anchored at the carbon interface",
                characterization_methods="SEM",
                notes="No gravimetric yield is reported; representative Raman/TEM diameter data are not mapped to this substrate-pressure run.",
            )
        cost = cost_row(
            run_id,
            scale_level_demonstrated="laboratory substrate CVD experiment",
            scale_level_claimed=("full carbon-fiber weave strand demonstration" if item["code"] == "CARBON_FIBER_HP_25" else "not_reported"),
            scale_evidence_summary=("Growth was demonstrated across a full strand of carbon-fiber weave." if item["code"] == "CARBON_FIBER_HP_25" else "Growth was demonstrated on carbon-surface specimens."),
            quantitative_cost_reported="not_reported",
        )
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].extend(stages)
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        prefix = f"{source_id}_EV_{index:02d}"
        tables["evidence_index"].append(
            evidence_row(
                source_id,
                f"{prefix}_CATALYST",
                run_id,
                "catalyst_system",
                catalyst["catalyst_id"],
                "record_level",
                ("SPAN_3C901043551AC486C7E3" if is_control else "SPAN_2836B776A2E4D2182987"),
                ("The negative control uses 1 nm Fe directly on carbon fiber without the alumina support." if is_control else "Odako catalyst preparation uses 1 nm e-beam Fe followed by a 5 nm Al2O3 overlayer on grafoil or carbon fiber."),
            )
        )
        if is_control:
            tables["evidence_index"].extend(
                [
                    evidence_row(
                        source_id,
                        f"{prefix}_PROCESS",
                        run_id,
                        "reactor_process_gas",
                        growth["process_stage_id"],
                        "record_level",
                        "SPAN_3C901043551AC486C7E3",
                        "The Fe-only sample is explicitly identified as a growth control, but its run-specific CVD parameters are not restated.",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_PRODUCT",
                        run_id,
                        "yield_quality",
                        product["product_id"],
                        "record_level",
                        "SPAN_3C901043551AC486C7E3",
                        "The 1 nm Fe-only carbon-fiber control produced no measurable CNT growth.",
                    ),
                ]
            )
        else:
            tables["evidence_index"].extend(
                [
                    evidence_row(
                        source_id,
                        f"{prefix}_ACTIVATION",
                        run_id,
                        "reactor_process_gas",
                        activation["process_stage_id"],
                        "stage_type;reactor_type;reducing_gas;process_note",
                        "SPAN_16B140CE09721FAA7D7D",
                        "Atomic hydrogen generated by a tungsten hot filament activates the catalyst for 30 s immediately before growth.",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_ACTIVATION_TIME_NORMALIZED",
                        run_id,
                        "reactor_process_gas",
                        activation["process_stage_id"],
                        "holding_time_min",
                        "SPAN_16B140CE09721FAA7D7D",
                        "The reported 30 s activation is converted to 0.5 min.",
                        value_status="normalized",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_GROWTH_RECIPE",
                        run_id,
                        "reactor_process_gas",
                        growth["process_stage_id"],
                        "stage_type;reactor_type;temperature_setpoint_C;carbon_source;carbon_source_flow_original;carbon_source_flow_sccm;reducing_gas;reducing_gas_flow_original;reducing_gas_flow_sccm;cofeed_or_reactive_gas;cofeed_flow_original;cofeed_flow_sccm;gas_composition_summary;process_note",
                        "SPAN_349C9147C2A3A2D63E53",
                        "The water-assisted recipe uses 400 sccm H2, 2 sccm H2O, and 2 sccm C2H2 at 750 C; 25 Torr raises acetylene partial pressure and growth rate.",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_GROWTH_PRESSURE",
                        run_id,
                        "reactor_process_gas",
                        growth["process_stage_id"],
                        "pressure_original",
                        ("SPAN_2B1F5B3CCDAC6EE80D7A" if "GRAFOIL" in item["code"] else "SPAN_2BB04E7179DCBF0C8169"),
                        f"The figure-linked {item['substrate']} specimen is assigned to {item['pressure']} Torr.",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_PRESSURE_NORMALIZED",
                        run_id,
                        "reactor_process_gas",
                        growth["process_stage_id"],
                        "pressure_kPa",
                        ("SPAN_2B1F5B3CCDAC6EE80D7A" if "GRAFOIL" in item["code"] else "SPAN_2BB04E7179DCBF0C8169"),
                        f"The reported {item['pressure']} Torr is converted to {item['pressure_kPa']} kPa.",
                        value_status="normalized",
                    ),
                ]
            )
            if item["duration"]:
                tables["evidence_index"].append(
                    evidence_row(
                        source_id,
                        f"{prefix}_GROWTH_TIME",
                        run_id,
                        "reactor_process_gas",
                        growth["process_stage_id"],
                        "holding_time_min",
                        "SPAN_2B1F5B3CCDAC6EE80D7A",
                        f"Figure 3 links {item['pressure']} Torr grafoil growth to {item['duration']} min.",
                    )
                )
            tables["evidence_index"].append(
                evidence_row(
                    source_id,
                    f"{prefix}_PRODUCT",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "record_level",
                    item["result_span"],
                    item["result"],
                )
            )
            if item["high_pressure"]:
                tables["evidence_index"].append(
                    evidence_row(
                        source_id,
                        f"{prefix}_WALL_MIXTURE",
                        run_id,
                        "yield_quality",
                        product["product_id"],
                        "record_level",
                        "SPAN_B8CA535B9AC656B4687E",
                        "Elevated pressure gives faster growth at the expense of some double- and few-walled tubes within the SWNT population.",
                    )
                )
        tables["evidence_index"].append(
            evidence_row(
                source_id,
                f"{prefix}_COST",
                run_id,
                "cost_scale_review",
                run_id,
                "record_level",
                item["result_span"],
                "The demonstrated carbon-surface growth is assessed as laboratory scale; the carbon-fiber high-pressure specimen also demonstrates full-strand coverage. No quantitative cost is reported.",
                value_status="review_assessment",
            )
        )
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{source_id}_ISS_REPRESENTATIVE_CHARACTERIZATION",
                source_id,
                f"{source_id}_GRAFOIL_LP_1P4",
                "cross_run_result_mapping_missing",
                "yield_quality",
                f"{source_id}_GRAFOIL_LP_1P4_PROD",
                "outer_diameter_mean_nm",
                "Raman and TEM provide a representative odako diameter/wall distribution, including an approximately 3.1 nm peak and a few 2-3-wall tubes, but the specimen is not mapped to a substrate-pressure run. Those values are not inherited.",
                evidence_ids=f"{source_id}_EV_01_PRODUCT",
                severity="high",
            ),
            issue_row(
                f"{source_id}_ISS_CARBON_FIBER_DURATION",
                source_id,
                f"{source_id}_CARBON_FIBER_LP_1P4",
                "missing_run_parameter",
                "reactor_process_gas",
                f"{source_id}_CARBON_FIBER_LP_1P4_S02",
                "holding_time_min",
                "Figure 6 maps carbon-fiber products to 1.4 and 25 Torr but does not restate their growth durations. The grafoil Figure 3 durations are not copied across substrates.",
                evidence_ids=f"{source_id}_EV_03_GROWTH_PRESSURE;{source_id}_EV_04_GROWTH_PRESSURE",
                severity="medium",
            ),
            issue_row(
                f"{source_id}_ISS_CONTROL_PROCESS",
                source_id,
                f"{source_id}_CARBON_FIBER_FE_ONLY_CONTROL",
                "missing_run_parameter",
                "reactor_process_gas",
                f"{source_id}_CARBON_FIBER_FE_ONLY_CONTROL_S01",
                "record_level",
                "The Fe-only negative control is explicit, but its exact activation, pressure, temperature, gas flows, and duration are not separately identified; successful-run values are not copied into it.",
                evidence_ids=f"{source_id}_EV_05_PROCESS",
                severity="medium",
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
                "negative_runs_preserved": 1,
                "matrix_note": "Figure 3 supplies two grafoil pressure runs; Figure 6 supplies two carbon-fiber pressure runs (with Figure 7 as scale evidence for the high-pressure fibre run); the Fe-only/no-alumina control is retained as the fifth record.",
            },
            "pdf_visual_review": {
                "completed": True,
                "pages_checked": [1, 2, 3, 4, 5, 6, 7, 8],
                "objects_checked": ["Experimental recipe", "Figure 1 odako mechanism", "Figures 2-3 grafoil products", "Figures 4-5 Raman/TEM characterization", "Figure 6 carbon-fiber pressure products", "Figure 7 full-strand demonstration", "Conclusions"],
            },
            "pressure_policy_check": "Growth pressures 1.4 and 25 Torr remain run-specific and are normalized to 0.187 and 3.33 kPa. No pressure is assigned to the atomic-H activation or Fe-only control.",
            "cross_run_inheritance_check": "Grafoil durations 15/30 min are not copied to carbon-fiber runs. Representative Raman/TEM diameters and wall counts are not assigned because their substrate-pressure identity is absent. High-pressure wall-mixture language is confined to 25 Torr runs.",
            "unit_policy_check": "The 30 s activation is normalized to 0.5 min with explicit evidence. Original Torr and sccm values are preserved with separate kPa normalization evidence.",
            "conflict_check": "No contradictory pressure or flow values were found. Missing carbon-fiber durations, Fe-only control parameters, and representative-product mapping are logged instead of inferred.",
        },
    )
    update_manifest(
        source_id,
        "extracted_needs_supervisory_review",
        package_path=package.relative_to(REDO_ROOT).as_posix(),
    )
    return package


def build_lit_65c8bd1b(context: SourceContext) -> Path:
    """He et al. 2016, partially carbon-coated Co catalysts for selective SWCNT growth."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    runs = [
        {
            "code": "PARTIAL_CO_1P7NM",
            "label": "Partially carbon-coated Co catalyst, 1.7 nm SWCNT product",
            "kind": "partial",
            "summary": "The standard partially carbon-coated Co catalyst produced isolated SWCNTs centred at 1.7 nm with very high semiconducting content.",
            "diameter_mean": "1.7",
            "diameter_range": "1.6-1.9",
            "cnt_result": "SWCNTs; approximately 98% semiconducting by 160 Raman spectra and approximately 99% by absorption analysis",
            "morphology": "isolated, straight, randomly dispersed SWCNTs approximately 10 micrometres long",
            "result_span": "SPAN_C20A7F719450CA135ABB",
        },
        {
            "code": "EXPOSED_CO_CONTROL",
            "label": "Fully exposed Co catalyst comparison",
            "kind": "exposed",
            "summary": "A fully exposed, uncoated Co catalyst comparison produced a broad RBM distribution containing both semiconducting and metallic SWCNTs.",
            "diameter_mean": "",
            "diameter_range": "",
            "cnt_result": "SWCNTs with broad Raman RBM distribution from both semiconducting and metallic tubes",
            "morphology": "not_reported",
            "result_span": "SPAN_2ED7F97931E6B5F117F9",
        },
        {
            "code": "PARTIAL_CO_2P1NM",
            "label": "Larger exposed-area carbon-coated Co catalyst, 2.1 nm product",
            "kind": "tuned",
            "summary": "Increasing the exposed Co area by stronger hydrogen heat treatment produced SWCNTs with a 2.1 nm mean diameter and approximately 96% semiconducting content.",
            "diameter_mean": "2.1",
            "diameter_range": "2.0-2.2",
            "cnt_result": "SWCNTs with approximately 96% semiconducting content",
            "morphology": "not_reported",
            "result_span": "SPAN_7A17878DDC01492C98C7",
        },
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [
            source_master_row(
                context,
                "Three result-linked records: standard partially carbon-coated Co, fully exposed Co comparison, and larger-exposed-area 2.1 nm tuning condition.",
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
        if item["kind"] == "exposed":
            catalyst = catalyst_row(
                run_id,
                catalyst_label="fully exposed Co nanoparticles from block-copolymer template",
                active_metals="Co",
                support_material="Si/SiO2 substrate",
                precursor_summary="cobalt cyanide complex adsorbed on a PS-b-P4VP thin film",
                preparation_method="block-copolymer templating with solvent annealing omitted; 750 C air treatment for 5 min removed the carbon/polymer coating",
                calcination_condition="750 C in air for 5 min",
                phase_or_state_summary="uncoated, fully exposed Co nanoparticles",
            )
        else:
            heat = (
                "200 sccm H2 at 500 C for 5 min followed by 700 C for 5 min"
                if item["kind"] == "partial"
                else "stronger H2 heat treatment culminating at 800 C for 10 min; the printed method also mentions an intervening 700 C for 10 min step"
            )
            catalyst = catalyst_row(
                run_id,
                catalyst_label="acorn-like partially carbon-coated Co nanoparticles",
                active_metals="Co",
                support_material="Si/SiO2 substrate",
                precursor_summary="cobalt cyanide complex adsorbed on self-assembled PS-b-P4VP nanodomains",
                preparation_method="block-copolymer self-assembly, precursor adsorption, air plasma opening, and hydrogen thermal reduction",
                reduction_condition=heat,
                phase_or_state_summary="Co nanoparticle partially coated with carbon",
                catalyst_particle_size_mean_nm=("3.1" if item["kind"] == "partial" else ""),
                catalyst_particle_size_range_nm=("2.5-4.5" if item["kind"] == "partial" else ""),
            )
        growth = process_row(
            run_id,
            1,
            "ethanol_CVD_growth",
            reactor_type="horizontal quartz-tube CVD furnace",
            reactor_size_summary="25 mm diameter quartz tube",
            temperature_setpoint_C="700",
            temperature_program_summary="substrate inserted into reactor centre after furnace reached 700 C",
            holding_time_min="10-25",
            carbon_source="ethanol vapor from bubbler in a 35 C water bath",
            carbon_source_flow_original="75 sccm Ar passed through ethanol bubbler",
            reducing_gas="H2",
            reducing_gas_flow_original="200 sccm",
            reducing_gas_flow_sccm="200",
            inert_gas="Ar",
            inert_gas_flow_original="75 sccm",
            inert_gas_flow_sccm="75",
            gas_composition_summary="75 sccm Ar through a 35 C ethanol bubbler plus 200 sccm H2",
            cooling_condition="cooled to room temperature under Ar/H2",
            process_note="The same printed CVD recipe is explicitly used for the exposed-Co and diameter-tuning comparisons.",
        )
        product = yield_row(
            run_id,
            primary_yield_metric="not_reported",
            yield_original="not_reported",
            secondary_result_summary=item["cnt_result"],
            yield_definition_original="not_reported",
            CNT_type_reported="single-walled carbon nanotubes",
            CNT_type_confirmed="SWCNT",
            CNT_type_evidence="TEM, multi-wavelength Raman spectroscopy, optical absorption, and electron diffraction",
            outer_diameter_mean_nm=item["diameter_mean"],
            outer_diameter_range_nm=item["diameter_range"],
            length_summary=("approximately 10 micrometres" if item["kind"] == "partial" else "not_reported"),
            morphology=item["morphology"],
            characterization_methods="SEM; TEM; Raman spectroscopy; UV-vis-NIR absorption; electron diffraction",
            notes="No gravimetric CNT yield is reported for this comparison.",
        )
        cost = cost_row(
            run_id,
            scale_level_demonstrated="laboratory substrate CVD",
            scale_level_claimed="not_reported",
            scale_evidence_summary="CNTs were grown on catalyst-coated Si/SiO2 substrates in a 25 mm quartz tube.",
            quantitative_cost_reported="not_reported",
        )
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].append(growth)
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        prefix = f"{source_id}_EV_{index:02d}"
        tables["evidence_index"].extend(
            [
                evidence_row(
                    source_id,
                    f"{prefix}_CATALYST",
                    run_id,
                    "catalyst_system",
                    catalyst["catalyst_id"],
                    "record_level",
                    (
                        "SPAN_2ED7F97931E6B5F117F9"
                        if item["kind"] == "exposed"
                        else (
                            "SPAN_2AB2D21B8D4FFD5E93DC"
                            if item["kind"] == "partial"
                            else "SPAN_35998E3DF954E6DC5A5B"
                        )
                    ),
                    "The source describes the run-specific Co exposure/carbon-coating preparation.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_GROWTH",
                    run_id,
                    "reactor_process_gas",
                    growth["process_stage_id"],
                    "record_level",
                    "SPAN_9A40B4B910B402AAA7F9",
                    "Growth used a 25 mm quartz tube at 700 C with 75 sccm Ar through a 35 C ethanol bubbler and 200 sccm H2 for 10-25 min.",
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_PRODUCT",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "record_level",
                    item["result_span"],
                    item["cnt_result"],
                ),
                evidence_row(
                    source_id,
                    f"{prefix}_COST",
                    run_id,
                    "cost_scale_review",
                    run_id,
                    "record_level",
                    "SPAN_9A40B4B910B402AAA7F9",
                    "The demonstrated setup is assessed as laboratory substrate CVD; quantitative cost was not reported.",
                    value_status="review_assessment",
                ),
            ]
        )
        if item["kind"] == "partial":
            tables["evidence_index"].extend(
                [
                    evidence_row(
                        source_id,
                        f"{prefix}_CATALYST_SIZE",
                        run_id,
                        "catalyst_system",
                        catalyst["catalyst_id"],
                        "catalyst_particle_size_mean_nm;catalyst_particle_size_range_nm",
                        "SPAN_32EA2CF762A9C8F7E643",
                        "More than 90% of catalyst particles were 2.5-4.5 nm with a 3.1 nm mean diameter.",
                    ),
                    evidence_row(
                        source_id,
                        f"{prefix}_PRODUCT_RANGE_AND_ABSORPTION",
                        run_id,
                        "yield_quality",
                        product["product_id"],
                        "outer_diameter_range_nm;secondary_result_summary",
                        "SPAN_18372861E31BDB5BDDB3",
                        "The main product spans 1.6-1.9 nm and absorption analysis gives approximately 99% semiconducting content.",
                    ),
                ]
            )
        elif item["kind"] == "tuned":
            tables["evidence_index"].append(
                evidence_row(
                    source_id,
                    f"{prefix}_PRODUCT_DIAMETER_RANGE",
                    run_id,
                    "yield_quality",
                    product["product_id"],
                    "outer_diameter_range_nm;secondary_result_summary",
                    "SPAN_EA9E7CB38B1CA3EE47B0",
                    "The tuned product has a 2.0-2.2 nm diameter range and approximately 96% semiconducting content.",
                )
            )
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{source_id}_ISS_TUNING_HEAT_SEQUENCE",
                source_id,
                f"{source_id}_PARTIAL_CO_2P1NM",
                "ambiguous_process_sequence",
                "catalyst_system",
                f"{source_id}_PARTIAL_CO_2P1NM_CAT",
                "reduction_condition",
                "The method grammatically lists changes from 500 C/5 min to 700 C/10 min and to 800 C/10 min, while the discussion directly links the 2.1 nm product to 800 C/10 min. The exact sequence is retained in prose and not split into fabricated runs.",
                evidence_ids=f"{source_id}_EV_03_CATALYST;{source_id}_EV_03_PRODUCT",
                severity="high",
            ),
            issue_row(
                f"{source_id}_ISS_GROWTH_TIME_RANGE",
                source_id,
                f"{source_id}_PARTIAL_CO_1P7NM",
                "series_resolution_limit",
                "reactor_process_gas",
                f"{source_id}_PARTIAL_CO_1P7NM_S01",
                "holding_time_min",
                "The paper reports a 10-25 min growth-time range but does not map an exact time to each product comparison.",
                evidence_ids=f"{source_id}_EV_01_GROWTH",
                severity="medium",
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
                "result_linked_campaigns_in_paper": 3,
                "extracted_runs": 3,
                "negative_runs_preserved": 1,
                "matrix_note": "The standard partially coated catalyst, fully exposed comparison, and 2.1 nm tuning result remain separate.",
            },
            "pdf_visual_review": {
                "completed": True,
                "pages_checked": [1, 2, 3, 4, 5, 6, 7, 8],
                "objects_checked": ["Figures 1-4 catalyst/product evidence", "Discussion comparison", "Methods catalyst preparation", "Methods CVD recipe"],
            },
            "pressure_policy_check": "Reactor pressure is not reported and remains blank for all three runs.",
            "cross_run_inheritance_check": "The 1.7 nm diameter range and high semiconducting fractions stay with the standard run; the exposed-Co comparator receives no diameter; the 2.1 nm result stays with the stronger-treatment run.",
            "unit_policy_check": "Original sccm, C, nm, and min values are retained; no unsupported pressure conversion is introduced.",
            "conflict_check": "The ambiguous thermal-treatment grammar and unmapped 10-25 min growth-time range are explicitly logged.",
        },
    )
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


def build_lit_b917c961(context: SourceContext) -> Path:
    """Yang et al. 2023, in-situ VACNT growth on carbon-fibre fabric."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    run = source_run_row(
        source_id,
        "FECO_CF_VACNT",
        "Fe/Co nitrate on carbon-fibre fabric, 660 C acetylene CVD",
        "Fe/Co-catalysed CVD grew several-micrometre VACNTs vertically around carbon fibres, forming intertwined three-dimensional fibre networks.",
    )
    run_id = run["run_id"]
    catalyst = catalyst_row(
        run_id,
        catalyst_label="Fe/Co nitrate-coated carbon-fibre fabric",
        active_metals="Fe; Co",
        support_material="3K plain-woven carbon-fibre fabric",
        precursor_summary="mixed 1 mol/L Fe(NO3)3 and 1 mol/L Co(NO3)2 solutions",
        preparation_method="20 min immersion followed by oven drying",
        drying_condition="200 C for 1 h",
        preparation_detail="Carbon-fibre fabric was immersed in the mixed nitrate solutions for 20 min and dried to evaporate water.",
    )
    growth = process_row(
        run_id,
        1,
        "acetylene_CVD_growth",
        reactor_type="tube furnace",
        temperature_setpoint_C="660",
        holding_time_min="30",
        carbon_source="C2H2",
        carbon_source_flow_original="40 mL/min",
        carbon_source_flow_sccm="40",
        inert_gas="N2",
        inert_gas_flow_original="100 mL/min",
        inert_gas_flow_sccm="100",
        gas_composition_summary="100 mL/min N2 and 40 mL/min C2H2",
        process_note="Pressure was not reported.",
    )
    product = yield_row(
        run_id,
        primary_yield_metric="not_reported",
        yield_original="not_reported",
        yield_definition_original="not_reported",
        secondary_result_summary="Several-micrometre CNTs grew vertically around and fully wrapped the carbon-fibre trunks.",
        CNT_type_reported="vertically aligned carbon nanotubes",
        CNT_type_confirmed="not_reported",
        CNT_type_evidence="SEM morphology; wall number was not established in the source",
        length_summary="several micrometres",
        morphology="vertically aligned CNTs intertwined into a three-dimensional network around carbon fibres",
        alignment_or_array="quasi-vertically aligned around carbon-fibre surface",
        characterization_methods="SEM; BET N2 adsorption/desorption",
        application_property_summary="Used as an interfacial reinforcement in CFRP; the CNT-grown-plus-RPC composite reached 718.86 MPa flexural strength, 27.1% above untreated composite.",
        notes="Composite mechanical performance is downstream application evidence, not CNT synthesis yield.",
    )
    cost = cost_row(
        run_id,
        scale_level_demonstrated="laboratory fabric treatment",
        scale_level_claimed="potential manufacturing route for high-strength CFRP",
        scale_evidence_summary="CNTs were grown directly on woven carbon-fibre fabric and incorporated into ten-ply CFRP test coupons.",
        quantitative_cost_reported="not_reported",
    )
    tables = {
        "source_master": [source_master_row(context, "One result-linked CNT growth condition on carbon-fibre fabric; RPC and composite curing are downstream processing, not separate CNT synthesis runs.")],
        "source_run": [run],
        "catalyst_system": [catalyst],
        "reactor_process_gas": [growth],
        "yield_quality": [product],
        "cost_scale_review": [cost],
        "evidence_index": [
            evidence_row(source_id, f"{source_id}_EV_01_CATALYST", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_158C2FAA17BB02803FEE", "Carbon-fibre fabric was immersed in 1 mol/L Fe and Co nitrate solutions for 20 min and dried at 200 C for 1 h."),
            evidence_row(source_id, f"{source_id}_EV_01_GROWTH", run_id, "reactor_process_gas", growth["process_stage_id"], "record_level", "SPAN_192EE084C661C9B7FE89", "CNT growth used 100 mL/min N2 and 40 mL/min C2H2 at 660 C for 30 min."),
            evidence_row(source_id, f"{source_id}_EV_01_PRODUCT", run_id, "yield_quality", product["product_id"], "record_level", "SPAN_1844F6A44B866B1173F8", "SEM showed several-micrometre CNTs growing vertically around carbon fibres and intertwining into a three-dimensional network."),
            evidence_row(source_id, f"{source_id}_EV_01_APPLICATION", run_id, "yield_quality", product["product_id"], "application_property_summary", "SPAN_206586880112B7044EE3", "The CNT-grown-plus-RPC composite reached 718.86 MPa flexural strength, 27.1% above the untreated composite."),
            evidence_row(source_id, f"{source_id}_EV_01_COST", run_id, "cost_scale_review", run_id, "record_level", "SPAN_158C2FAA17BB02803FEE", "The demonstrated woven-fabric treatment is assessed as laboratory scale; no quantitative cost is reported.", value_status="review_assessment"),
        ],
        "review_issue_log": [
            issue_row(
                f"{source_id}_ISS_WALL_NUMBER",
                source_id,
                run_id,
                "missing_product_subtype_evidence",
                "yield_quality",
                product["product_id"],
                "CNT_type_confirmed",
                "The paper calls the product VACNTs but does not establish single-wall or multi-wall identity; wall number is not inferred from morphology.",
                evidence_ids=f"{source_id}_EV_01_PRODUCT",
                severity="medium",
            )
        ],
    }
    write_package(package, tables)
    write_review(
        package,
        {
            "source_id": source_id,
            "review_status": "extracted_needs_supervisory_review",
            "reviewer": "Codex",
            "source_identity_checked": True,
            "campaign_reconciliation": {"result_linked_campaigns_in_paper": 1, "extracted_runs": 1, "negative_runs_preserved": 0},
            "pdf_visual_review": {"completed": False, "pages_checked": [], "not_applicable_reason": "Local source is HTML rather than PDF."},
            "html_source_review": {"completed": True, "sections_checked": ["2.2 Starting Materials", "Figure 2 growth scheme", "3.1 Microstructure", "4. Conclusions"]},
            "pressure_policy_check": "Pressure is not reported and remains blank.",
            "cross_run_inheritance_check": "Only one CNT synthesis condition exists; RPC/composite test groups are not duplicated as growth runs.",
            "unit_policy_check": "mL/min gas flows are normalized one-to-one to sccm at the reporting level.",
            "conflict_check": "VACNT wall number is not reported and is logged rather than inferred.",
        },
    )
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


def build_lit_c604f012(context: SourceContext) -> Path:
    """Mirza Gheitaghy et al. 2020, patterned VA-MWCNT pillar LPCVD."""
    source_id = context.source_id
    package = SHARD_ROOT / source_id
    run = source_run_row(
        source_id,
        "FE_TIN_VAMWCNT_PILLARS",
        "Patterned Fe/TiN VA-MWCNT pillar growth",
        "A patterned 5 nm Fe catalyst on Ti/TiN-coated silicon produced 120 micrometre-tall VA-MWCNT pillars with lithographically varied pillar diameters.",
    )
    run_id = run["run_id"]
    catalyst = catalyst_row(
        run_id,
        catalyst_label="patterned Fe film on Ti/TiN diffusion-barrier stack",
        active_metals="Fe",
        support_material="Si wafer with Ti/TiN diffusion-barrier stack",
        precursor_summary="5 nm Fe film deposited by electron-beam evaporation",
        preparation_method="optical lithography, Fe e-beam evaporation, and lift-off",
        preparation_detail="Photoresist pattern defines circular CNT growth regions; TiN acts as the catalyst diffusion barrier.",
    )
    growth = process_row(
        run_id,
        1,
        "LPCVD_growth",
        reactor_type="LPCVD reactor",
        process_note="Pillar diameter was set by catalyst lithography rather than a change in the CVD recipe. Numeric method values were visually checked but are omitted here because the immutable candidate ledger did not capture the supporting paragraph.",
    )
    product = yield_row(
        run_id,
        primary_yield_metric="not_reported",
        yield_original="not_reported",
        yield_definition_original="not_reported",
        secondary_result_summary="VA-MWCNT pillars were approximately 120 micrometres tall; pillar diameters ranged from 30 to 150 micrometres.",
        CNT_type_reported="vertically aligned multi-walled carbon nanotubes",
        CNT_type_confirmed="MWCNT",
        CNT_type_evidence="TEM and SEM",
        outer_diameter_mean_nm="30",
        length_summary="pillar height 120 +/- 5 micrometres",
        morphology="vertically aligned MWCNT arrays patterned as cylindrical pillars",
        alignment_or_array="vertical pillars; lithographic pillar diameter 30-150 micrometres",
        characterization_methods="SEM; TEM; Raman spectroscopy; FIB; EDX",
        notes="The 30-150 micrometre values are pillar diameters, not nanotube outer diameters. Individual nanotube diameter is 30 +/- 4 nm.",
    )
    cost = cost_row(
        run_id,
        scale_level_demonstrated="wafer microfabrication and commercial LPCVD",
        scale_level_claimed="superconducting vertical-interconnect concept",
        scale_evidence_summary="Patterned growth was demonstrated on a Si wafer in a commercial AIXTRON reactor.",
        reactor_capacity_or_throughput="wafer diameter and reactor throughput not entered because ledger support is incomplete",
        quantitative_cost_reported="not_reported",
    )
    tables = {
        "source_master": [source_master_row(context, "One common LPCVD synthesis recipe produced a lithographic pillar-diameter matrix; downstream NbTiN ALD coatings and compression tests are not separate CNT growth runs.")],
        "source_run": [run],
        "catalyst_system": [catalyst],
        "reactor_process_gas": [growth],
        "yield_quality": [product],
        "cost_scale_review": [cost],
        "evidence_index": [
            evidence_row(source_id, f"{source_id}_EV_01_CATALYST", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_FD21E5F3BB8ABE0B0EA0", "Figure 1 describes the Ti/TiN barrier, optical lithography, 5 nm Fe evaporation, lift-off, and patterned CNT growth regions."),
            evidence_row(source_id, f"{source_id}_EV_01_GROWTH", run_id, "reactor_process_gas", growth["process_stage_id"], "stage_type;reactor_type;process_note", "SPAN_4264F0052239494B6AEE", "The abstract identifies low-pressure chemical vapor deposition as the VA-MWCNT growth method; unsupported numeric method values remain omitted."),
            evidence_row(source_id, f"{source_id}_EV_01_PILLARS", run_id, "yield_quality", product["product_id"], "record_level", "SPAN_DB862CEC5763FFAAA026", "The study fabricated 30-150 micrometre-diameter MWCNT pillars approximately 120 micrometres high."),
            evidence_row(source_id, f"{source_id}_EV_01_CNT_DIAMETER", run_id, "yield_quality", product["product_id"], "outer_diameter_mean_nm", "SPAN_EAD611F7657A9BD181BE", "TEM/SEM analysis reports an individual nanotube average diameter of 30 +/- 4 nm."),
            evidence_row(source_id, f"{source_id}_EV_01_COST", run_id, "cost_scale_review", run_id, "record_level", "SPAN_67D46CFAF948FFD15753", "The 100 mm wafer and commercial reactor demonstration is assessed as wafer-scale microfabrication; no quantitative cost is reported.", value_status="review_assessment"),
        ],
        "review_issue_log": [
            issue_row(
                f"{source_id}_ISS_PROCESS_LEDGER_GAP",
                source_id,
                run_id,
                "evidence_ledger_coverage_gap",
                "reactor_process_gas",
                growth["process_stage_id"],
                "record_level",
                "The PDF methods visually report the LPCVD temperature, pressure, flows, and duration, but the immutable candidate ledger does not contain that paragraph. Numeric process fields are left blank pending ledger repair rather than supported by a mismatched span.",
                evidence_ids=f"{source_id}_EV_01_CATALYST",
                severity="high",
            )
        ],
    }
    write_package(package, tables)
    write_review(
        package,
        {
            "source_id": source_id,
            "review_status": "extracted_needs_supervisory_review",
            "reviewer": "Codex",
            "source_identity_checked": True,
            "campaign_reconciliation": {"result_linked_campaigns_in_paper": 1, "extracted_runs": 1, "negative_runs_preserved": 0, "matrix_note": "Pillar diameters are lithographic product geometries under one common growth recipe."},
            "pdf_visual_review": {"completed": True, "pages_checked": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], "objects_checked": ["Section 2.1 LPCVD recipe", "Figure 1 process flow", "Figure 2 morphology", "Raman spectra", "compression-series figures"]},
            "pressure_policy_check": "The PDF reports pressure, but it remains blank in the tables because the immutable evidence ledger did not capture the supporting methods paragraph.",
            "cross_run_inheritance_check": "NbTiN coating thicknesses and compression-test pillar diameters are downstream variants and are not represented as separate CNT synthesis runs.",
            "unit_policy_check": "30 +/- 4 nm individual-tube diameter is kept separate from 30-150 micrometre pillar diameter and 120 micrometre pillar height.",
            "conflict_check": "No conflicting synthesis values were found in the visually checked methods and figure caption.",
        },
    )
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


def build_lit_9d1d16c5(context: SourceContext) -> Path:
    """El-Hendawy et al. 2009, nine MgO-supported Fe/Mo/Ce catalysts."""
    source_id = context.source_id
    matrix = [
        ("FE100", "Fe100", "Fe", "100 Fe : 0 Mo : 0 Ce", "10.9", "0.09", "Yes", "212"),
        ("MO100", "Mo100", "Mo", "0 Fe : 100 Mo : 0 Ce", "12.2", "0.78", "No", ""),
        ("CE100", "Ce100", "Ce", "0 Fe : 0 Mo : 100 Ce", "10.3", "0.92", "No", ""),
        ("CE10", "Ce10", "Fe; Ce", "90 Fe : 0 Mo : 10 Ce", "14.2", "0.10", "Yes", "188"),
        ("CE50", "Ce50", "Fe; Ce", "50 Fe : 0 Mo : 50 Ce", "13.6", "0.20", "Yes", "188"),
        ("CE90", "Ce90", "Fe; Ce", "10 Fe : 0 Mo : 90 Ce", "13.6", "0.81", "Yes", "188"),
        ("MO10", "Mo10", "Fe; Mo", "90 Fe : 10 Mo : 0 Ce", "18.8", "0.11", "Yes", "212"),
        ("MO50", "Mo50", "Fe; Mo", "50 Fe : 50 Mo : 0 Ce", "30.3", "0.17", "Yes", "212"),
        ("MO90", "Mo90", "Fe; Mo", "10 Fe : 90 Mo : 0 Ce", "15.9", "0.40", "Yes", "212"),
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [source_master_row(context, "Nine catalyst compositions from Table 1 are reconciled one-to-one with the nine Table 2 outcomes.")],
        "source_run": [],
        "catalyst_system": [],
        "reactor_process_gas": [],
        "yield_quality": [],
        "cost_scale_review": [],
        "evidence_index": [],
        "review_issue_log": [],
    }
    for index, (code, label, metals, ratio, carbon_mass, dg, rbm, rbm_peak) in enumerate(matrix, 1):
        run = source_run_row(
            source_id,
            code,
            label,
            f"Methane CVD using the {label} MgO-supported catalyst; Table 2 reports {carbon_mass} mg graphitic carbon and D/G {dg}.",
        )
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label=f"{label} on MgO",
            active_metals=metals,
            support_material="MgO nanopowder",
            metal_ratio_original=ratio,
            precursor_summary="iron nitrate, cerium nitrate, and ammonium molybdate as applicable",
            preparation_method="aqueous slurry mixing followed by drying and grinding",
            preparation_detail="total metal loading 28 mol.% relative to MgO; stirred 20 min and ultrasonicated 10 min",
            drying_condition="80 C overnight",
        )
        process = process_row(
            run_id,
            1,
            "methane_CVD_growth",
            reactor_type="tube furnace",
            reactor_material="alumina",
            reactor_size_summary="25.4 mm diameter alumina work tube",
            catalyst_loading_mass_g="0.1",
            temperature_setpoint_C="900",
            heating_rate_C_min="30",
            holding_time_min="30",
            cooling_condition="400 cm3/min argon; sample removed below 200 C",
            carbon_source="methane",
            carbon_source_flow_original="200 cm3/min",
            carbon_source_flow_sccm="200",
            inert_gas="Ar",
            inert_gas_flow_original="400 cm3/min",
            inert_gas_flow_sccm="400",
        )
        product = yield_row(
            run_id,
            primary_yield_metric="graphitic carbon mass",
            yield_original=f"{carbon_mass} mg graphitic C",
            yield_definition_original="graphitic carbon determined by high-temperature burn-off in TGA",
            yield_calculation_method="TGA high-temperature carbon burn-off",
            secondary_result_summary=f"D/G-band ratio {dg}; RBM detected: {rbm}" + (f"; most intense RBM {rbm_peak} cm-1" if rbm_peak else ""),
            CNT_type_reported="single-walled carbon nanotubes" if rbm == "Yes" else "no or very few single-walled carbon nanotubes",
            CNT_type_confirmed="SWCNT" if rbm == "Yes" else "not_reported",
            product_mixture_summary="graphitic carbon with SWCNT RBM evidence" if rbm == "Yes" else "graphitic carbon with no detected RBM",
            CNT_type_evidence="Raman RBM" if rbm == "Yes" else "Raman spectroscopy did not detect RBM",
            RBM_peak_reported=(f"{rbm_peak} cm-1" if rbm_peak else "not_detected"),
            Raman_ratio_type="D/G integrated-area ratio",
            Raman_ratio_value=dg,
            characterization_methods="Raman spectroscopy; TGA; SEM; TEM",
            notes="The reported graphitic-carbon mass is preserved and is not relabelled as an exact CNT mass.",
        )
        cost = cost_row(
            run_id,
            scale_level_demonstrated="laboratory tube-furnace batch",
            scale_level_claimed="not_reported",
            scale_evidence_summary="A powdered catalyst charge was processed in an alumina tube furnace.",
            quantitative_cost_reported="not_reported",
            cost_driver_summary="methane, argon, furnace heat, and supported catalyst preparation",
            industrial_readiness_assessment="laboratory comparison study",
        )
        issue_id = f"{source_id}_ISS_{index:02d}_YIELD_BASIS"
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].append(process)
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        tables["evidence_index"].extend(
            [
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_CAT", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_3547BE8D3B0F42D420DD", f"Table 1 identifies {label}, its Fe/Mo/Ce proportions, MgO support, total metal loading, and preparation sequence."),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_PROC", run_id, "reactor_process_gas", process["process_stage_id"], "record_level", "SPAN_E001FC1DD3506591BFDA", "The common methane-CVD paragraph reports catalyst mass, tube size, temperature, heating rate, gas flows, duration, and cooling condition."),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_PROD", run_id, "yield_quality", product["product_id"], "record_level", "SPAN_3BF5A2FA447FD562D7A2", f"Table 2 reports the graphitic-carbon mass, D/G ratio, RBM detection, and RBM peak for {label}.", linked_issue_id=issue_id),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_COST", run_id, "cost_scale_review", run_id, "record_level", "SPAN_E001FC1DD3506591BFDA", "The reported apparatus supports a laboratory tube-furnace assessment; no quantitative cost is reported.", value_status="review_assessment"),
            ]
        )
        tables["review_issue_log"].append(
            issue_row(
                issue_id,
                source_id,
                run_id,
                "yield_definition_scope",
                "yield_quality",
                product["product_id"],
                "yield_original",
                "Table 2 reports graphitic-carbon mass. The authors state that this closely represents CNT mass, but it is retained as graphitic carbon rather than converted to an exact CNT yield.",
                evidence_ids=f"{source_id}_EV_{index:02d}_PROD",
                severity="medium",
            )
        )
    package = SHARD_ROOT / source_id
    write_package(package, tables)
    write_review(
        package,
        {
            "source_id": source_id,
            "review_status": "source_review_complete_needs_supervisory_review",
            "reviewer": "Codex",
            "source_identity_checked": True,
            "evidence_sections_checked": ["2.1 Catalyst preparation", "2.2 Sample analysis", "Table 1", "Table 2", "Results and discussion"],
            "campaign_reconciliation": {"result_linked_campaigns_in_paper": 9, "extracted_runs": 9, "negative_runs_preserved": 2},
            "pdf_visual_review": {"completed": True, "pages_checked": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12], "objects_checked": ["Table 1 catalyst matrix", "Table 2 outcome matrix", "Raman and microscopy figures"]},
            "matrix_coverage_check": "All nine Table 1 catalysts map one-to-one to all nine Table 2 rows; Mo100 and Ce100 negative/near-negative SWCNT outcomes are retained.",
            "yield_policy_check": "Graphitic-carbon TGA mass is not silently relabelled as CNT mass.",
        },
    )
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


def build_lit_f140d55e(context: SourceContext) -> Path:
    """Park et al. 2023, wafer-scale SWCNT forest parameter scans."""
    source_id = context.source_id
    series = [
        ("STANDARD", "standard recipe", "experimental_condition", "standard", "Standard wafer-scale SWCNT forest recipe.", "SPAN_CBCA0D478FEA4A2C26C9", "Standard forests contained more than 96% SWCNTs with about 2 nm average diameter."),
        ("TIME_SCAN", "growth-time scan", "experimental_series", "time", "Growth duration was scanned; forest mass increased linearly and mass kinetics remained constant.", "SPAN_76BE708A7CB64843FF33", "Forest mass increased linearly with growth time, giving constant mass kinetics over the tested range."),
        ("ACETYLENE_SCAN", "acetylene-partial-pressure scan", "experimental_series", "acetylene", "Acetylene partial pressure was scanned up to a 30-fold precursor-concentration range.", "SPAN_A0D92EC2D2155196C6B7", "Mass kinetics increased linearly with acetylene partial pressure up to a limit."),
        ("HYDROGEN_SCAN", "hydrogen-partial-pressure scan", "experimental_series", "hydrogen", "Hydrogen partial pressure was scanned at constant 80 mbar growth pressure.", "SPAN_7A5AD1394BB1E0BF8879", "At 80 mbar, mass kinetics increased slightly with hydrogen partial pressure."),
        ("PRESSURE_CONST_PARTIAL", "pressure scan at constant acetylene partial pressure", "experimental_series", "pressure", "Growth pressure was scanned from 20 to 790 mbar while acetylene partial pressure was held constant.", "SPAN_BFC31E2B81A43E362F77", "Mass kinetics decayed inversely as total pressure increased at constant acetylene partial pressure."),
        ("PRESSURE_CONST_FLOW", "pressure scan at constant acetylene flow", "experimental_series", "pressure", "Growth pressure was scanned from 20 to 790 mbar while acetylene flow was held constant.", "SPAN_BFC31E2B81A43E362F77", "A shallow mass-kinetics maximum occurred as pressure increased at constant acetylene flow."),
        ("FLOW_CONST_PARTIAL", "total-flow scan at constant acetylene partial pressure", "experimental_series", "flow", "Total gas flow was scanned over an up-to-8-fold range while acetylene partial pressure was held constant.", "SPAN_7A5AD1394BB1E0BF8879", "Mass kinetics increased as total flow increased at constant acetylene partial pressure."),
        ("FLOW_CONST_FLOW", "total-flow scan at constant acetylene flow", "experimental_series", "flow", "Total gas flow was scanned over an up-to-8-fold range while acetylene flow was held constant.", "SPAN_7A5AD1394BB1E0BF8879", "Mass kinetics decreased as total flow increased at constant acetylene flow."),
        ("TEMPERATURE_SCAN", "growth-temperature scan", "experimental_series", "temperature", "Growth temperature was scanned from 700 to 900 C at 80 mbar.", "SPAN_7A80C6F4108D3CF2432C", "Preliminary temperature data showed weak mass-kinetics scaling over 700-900 C."),
        ("AREA_SCAN", "catalyst-area scan", "experimental_series", "area", "Catalyst substrate area was scanned from 1 to 180 cm2.", "SPAN_4886FFB884738CCD18AC", "Mass kinetics decreased inversely with catalyst area."),
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [source_master_row(context, "One standard recipe and nine source-declared parameter-scan series are represented without fabricating unreported individual scan points.")],
        "source_run": [],
        "catalyst_system": [],
        "reactor_process_gas": [],
        "yield_quality": [],
        "cost_scale_review": [],
        "evidence_index": [],
        "review_issue_log": [],
    }
    for index, (code, label, data_type, variant, process_note, outcome_span, outcome) in enumerate(series, 1):
        run = source_run_row(source_id, code, label, outcome, data_type=data_type)
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label="400 A Al2O3 / 0.5 A Mo / 5.5 A Fe thin-film stack",
            active_metals="Fe; Mo",
            support_material="silicon wafer with Al2O3 underlayer",
            metal_ratio_original="400 A Al2O3 / 0.5 A Mo / 5.5 A Fe",
            precursor_summary="e-beam-evaporated Al2O3, Mo, and Fe thin films",
            preparation_method="e-beam evaporation onto silicon wafer",
        )
        process_values: dict[str, str] = {
            "reactor_type": "AIXTRON Black Magic cold-wall CVD furnace",
            "reactor_setup_summary": "graphite heating stage, quartz showerhead, and mass-flow-controlled gas delivery",
            "temperature_setpoint_C": "800",
            "pressure_original": "80 mbar",
            "carbon_source": "C2H2",
            "carbon_source_flow_original": "4 sccm",
            "carbon_source_flow_sccm": "4",
            "reducing_gas": "H2",
            "reducing_gas_flow_original": "700 sccm",
            "reducing_gas_flow_sccm": "700",
            "inert_gas": "Ar",
            "inert_gas_flow_original": "400 sccm",
            "inert_gas_flow_sccm": "400",
            "cofeed_or_reactive_gas": "H2O",
            "cofeed_flow_original": "100-200 ppm by volume",
            "process_note": process_note,
        }
        if variant == "acetylene":
            process_values.pop("carbon_source_flow_original")
            process_values.pop("carbon_source_flow_sccm")
        elif variant == "hydrogen":
            process_values.pop("reducing_gas_flow_original")
            process_values.pop("reducing_gas_flow_sccm")
        elif variant == "pressure":
            process_values["pressure_original"] = "20-790 mbar"
        elif variant == "flow":
            for field in ["carbon_source_flow_original", "carbon_source_flow_sccm", "reducing_gas_flow_original", "reducing_gas_flow_sccm", "inert_gas_flow_original", "inert_gas_flow_sccm"]:
                process_values.pop(field)
        elif variant == "temperature":
            process_values.pop("temperature_setpoint_C")
            process_values["temperature_range_reported_C"] = "700-900"
        process = process_row(run_id, 1, "SWCNT_forest_growth", **process_values)
        if variant == "standard":
            product = yield_row(
                run_id,
                primary_yield_metric="CNT forest mass kinetics",
                yield_original="not_reported",
                yield_definition_original="mass accumulation rate per unit catalyst area",
                secondary_result_summary=outcome,
                CNT_type_reported="single-walled carbon nanotube forest",
                CNT_type_confirmed="SWCNT",
                CNT_type_evidence="HRTEM and Raman RBM",
                outer_diameter_mean_nm="2",
                outer_diameter_range_nm="maximum 5",
                alignment_or_array="vertically aligned forest",
                purified_product_purity_wt_percent="96",
                purity_basis=">96% single-wall selectivity",
                characterization_methods="HRTEM; Raman spectroscopy; SEM; gravimetry",
            )
        else:
            product = yield_row(
                run_id,
                primary_yield_metric="CNT forest mass kinetics",
                yield_original="not_reported",
                yield_definition_original="mass accumulation rate per unit catalyst area",
                secondary_result_summary=outcome,
                CNT_type_reported="single-walled carbon nanotube forest",
                CNT_type_confirmed="SWCNT",
                CNT_type_evidence="HRTEM and Raman RBM across the scanned parameter space",
                outer_diameter_range_nm="2-2.3",
                alignment_or_array="vertically aligned forest",
                purity_basis="single-wall selectivity 96.6-99+% across the scanned parameter space",
                characterization_methods="HRTEM; Raman spectroscopy; SEM; gravimetry",
                notes="Structural fields are series-level ranges reported across the multidimensional scan, not values assigned to an unreported individual point.",
            )
        cost = cost_row(
            run_id,
            scale_level_demonstrated="wafer-scale batch CVD",
            scale_level_claimed="large-area SWCNT forest synthesis",
            scale_evidence_summary="Uniform SWCNT forests were shown on 4-in and 6-in silicon wafers.",
            reactor_capacity_or_throughput="graphite stage accommodates up to 6-in wafers",
            quantitative_cost_reported="not_reported",
            scale_up_issue="mass kinetics depends on gas diffusion, total flow, pressure, and catalyst area",
            industrial_readiness_assessment="wafer-scale research demonstration",
        )
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].append(process)
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        tables["evidence_index"].extend(
            [
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_CAT", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_6DC4C158638E27C4C291", "The Methods report the silicon wafer, catalyst-film stack, e-beam deposition, reactor, and standard anneal recipe."),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_PROC_A", run_id, "reactor_process_gas", process["process_stage_id"], "record_level", "SPAN_6DC4C158638E27C4C291", "The standard recipe reports reactor configuration, pressure, temperature, Ar/H2 flows, and water cofeed."),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_PROC_B", run_id, "reactor_process_gas", process["process_stage_id"], "record_level", "SPAN_D9AC2E80A88AA88E4BF3", "The growth step adds acetylene and explains how pressure and temperature scans depart from the standard recipe."),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_PROC_RANGE", run_id, "reactor_process_gas", process["process_stage_id"], "process_note;pressure_original;temperature_range_reported_C", "SPAN_370758231A36DE2478C8", "The conclusion reports the precursor, area, pressure, and flow ranges covered by the multidimensional scans."),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_OUTCOME", run_id, "yield_quality", product["product_id"], "secondary_result_summary", outcome_span, outcome),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_STRUCT", run_id, "yield_quality", product["product_id"], "record_level", ("SPAN_CBCA0D478FEA4A2C26C9" if variant == "standard" else "SPAN_370758231A36DE2478C8"), "The source reports standard-recipe or scan-wide SWCNT selectivity and diameter characteristics."),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_COST_A", run_id, "cost_scale_review", run_id, "record_level", "SPAN_6DC4C158638E27C4C291", "The reactor stage accommodates wafers up to 6 in.", value_status="review_assessment"),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_COST_B", run_id, "cost_scale_review", run_id, "record_level", "SPAN_A27B561B7A02B541D47E", "The figure shows uniform forests grown on 4-in and 6-in silicon wafers.", value_status="review_assessment"),
            ]
        )
        if variant != "standard":
            issue_id = f"{source_id}_ISS_{index:02d}_SERIES_RESOLUTION"
            tables["review_issue_log"].append(
                issue_row(
                    issue_id,
                    source_id,
                    run_id,
                    "series_point_resolution",
                    "source_run",
                    run_id,
                    "data_type",
                    "The main text and figure establish a parameter-scan series and its trend, but do not enumerate every plotted condition in machine-readable text. The series is preserved as one record rather than fabricating point-level runs.",
                    evidence_ids=f"{source_id}_EV_{index:02d}_OUTCOME",
                    severity="medium",
                )
            )
    package = SHARD_ROOT / source_id
    write_package(package, tables)
    write_review(
        package,
        {
            "source_id": source_id,
            "review_status": "source_review_complete_needs_supervisory_review",
            "reviewer": "Codex",
            "source_identity_checked": True,
            "evidence_sections_checked": ["2.1 CNT synthesis", "3.2 Parametric scans", "3.2.1 Mass kinetics", "3.2.2 CNT forest properties", "Figures 3-7", "Tables 1-2"],
            "campaign_reconciliation": {"result_linked_campaigns_in_paper": 10, "extracted_runs": 10, "negative_runs_preserved": 0},
            "pdf_visual_review": {"completed": True, "pages_checked": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39], "objects_checked": ["standard-recipe methods", "Figure 3 parametric scans", "Figures 4-7 structure and validation plots", "Tables 1-2"]},
            "series_resolution_check": "The source's parameter scans are series-level records because exact plotted point sets are not machine-readable in the immutable evidence ledger.",
            "cross_run_inheritance_check": "Only the declared standard recipe is inherited; the scanned variable is explicitly removed or replaced in each series record.",
        },
    )
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


def build_lit_8af8b4db(context: SourceContext) -> Path:
    """Chen et al. 2023, waste-plastic pyrolysis over SS 316 mesh."""
    source_id = context.source_id
    records = [
        {"code": "PRETREATMENT_MATRIX", "label": "Raw/A/C/A+C pretreatment matrix", "kind": "pretreatment", "data_type": "experimental_series", "span": "SPAN_EC65E5B3235036D326F1"},
        {"code": "REUSE_SERIES", "label": "catalyst reuse series", "kind": "reuse", "data_type": "experimental_series", "span": "SPAN_2DE31D7701033E6314FF"},
        {"code": "TEMPERATURE_SERIES", "label": "catalytic-temperature series", "kind": "temperature", "data_type": "experimental_series", "span": "SPAN_7D04839B646D693E9909"},
        {"code": "CATALYST_RATIO_SERIES", "label": "SS 316-to-PP mass-ratio series", "kind": "ratio", "data_type": "experimental_series", "span": "SPAN_4C5C8CFE115911982771"},
        {"code": "LDPE", "label": "LDPE feedstock", "kind": "feedstock", "feedstock": "LDPE", "carbon_yield": "59.4", "data_type": "experimental_run", "span": "SPAN_384185DFA09CFA115855"},
        {"code": "HDPE", "label": "HDPE feedstock", "kind": "feedstock", "feedstock": "HDPE", "carbon_yield": "64.1", "data_type": "experimental_run", "span": "SPAN_384185DFA09CFA115855"},
        {"code": "PP", "label": "PP feedstock", "kind": "feedstock", "feedstock": "PP", "carbon_yield": "67.6", "data_type": "experimental_run", "span": "SPAN_384185DFA09CFA115855"},
        {"code": "GPPS", "label": "GPPS feedstock", "kind": "feedstock", "feedstock": "GPPS", "carbon_yield": "78.0", "data_type": "experimental_run", "span": "SPAN_384185DFA09CFA115855"},
        {"code": "HIPS", "label": "HIPS feedstock", "kind": "feedstock", "feedstock": "HIPS", "carbon_yield": "80.9", "data_type": "experimental_run", "span": "SPAN_384185DFA09CFA115855"},
        {"code": "ETHYLENE_CONTROL", "label": "ethylene model-compound control", "kind": "ethylene", "data_type": "experimental_run", "span": "SPAN_7C7DFDA1EA1D563D1C0F"},
        {"code": "BENZENE_CONTROL", "label": "benzene model-compound control", "kind": "benzene", "data_type": "experimental_run", "span": "SPAN_48D6E17F7EDABF64D7D8"},
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [source_master_row(context, "Pretreatment, reuse, temperature, catalyst/feed ratio, five plastic feedstocks, and two model-compound controls are reconciled as eleven source-declared records.")],
        "source_run": [],
        "catalyst_system": [],
        "reactor_process_gas": [],
        "yield_quality": [],
        "cost_scale_review": [],
        "evidence_index": [],
        "review_issue_log": [],
    }
    for index, item in enumerate(records, 1):
        kind = item["kind"]
        if kind == "pretreatment":
            summary = "Raw, acid-etched, calcined, and acid-plus-calcined SS 316 catalysts were compared; solid yield rose from 11.0 to 47.6 wt.% with A+C pretreatment."
        elif kind == "reuse":
            summary = "A+C-pretreated SS 316 was reused for 10 cycles; peak MWCNT yield was 662.0 mg per g plastic in cycle 3 and cumulative product was about 6 g."
        elif kind == "temperature":
            summary = "A 600-900 C catalytic-temperature series identified 800 C as preferred, with 662.0 mg MWCNT per g plastic and D/G 0.64."
        elif kind == "ratio":
            summary = "The SS 316-to-PP mass ratio was scanned from 0 to 30; product yields showed no obvious difference above 15."
        elif kind == "feedstock":
            summary = f"{item['feedstock']} produced {item['carbon_yield']} wt.% carbon, of which more than 96% was identified as MWCNTs."
        elif kind == "ethylene":
            summary = "Ethylene model-compound control formed CNTs through a VLS pathway involving Fe3C and liquid-like particles."
        else:
            summary = "Benzene model-compound control formed CNTs through a VSS pathway involving a solid Fe-Ni alloy."
        run = source_run_row(source_id, item["code"], item["label"], summary, data_type=item["data_type"])
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label="A+C-pretreated SS 316 mesh monolith" if kind != "pretreatment" else "Raw/A/C/A+C SS 316 pretreatment matrix",
            active_metals="Fe; Ni",
            support_material="self-supported multilayer stainless-steel 316 mesh",
            preparation_method="acid etching followed by air calcination" if kind != "pretreatment" else "raw, acid etching, air calcination, and combined acid-plus-calcination variants",
            preparation_detail="1 M HCl at 60 C for 12 h; air at 750 C for 15 min with 35 C/min ramp",
            drying_condition="ethanol-cleaned and dried overnight at 105 C",
            calcination_condition="750 C in air for 15 min at 35 C/min" if kind != "pretreatment" else "variant-dependent",
            phase_or_state_summary="50 mm high, 15 mm outer-diameter hollow mesh cylinder",
        )
        if kind in {"ethylene", "benzene"}:
            carbon_source = "C2H4" if kind == "ethylene" else "C6H6"
            process = process_row(
                run_id,
                1,
                "model_compound_control",
                reactor_type="not_reported",
                carbon_source=carbon_source,
                process_note="Model compound used to distinguish the CNT growth mechanism; exact control flow and duration are not reported in the main-text evidence ledger.",
            )
        else:
            process_values: dict[str, str] = {
                "reactor_type": "two-stage fixed-bed system",
                "reactor_material": "quartz",
                "reactor_size_summary": "upper section 26 mm x 300 mm; lower section 16 mm x 300 mm",
                "reactor_setup_summary": "plastic pyrolysis in the upper heated section followed by catalytic deposition in the lower heated section",
                "catalyst_loading_mass_g": "15",
                "heating_rate_C_min": "20",
                "inert_gas": "N2",
                "inert_gas_flow_original": "50 mL/min",
                "inert_gas_flow_sccm": "50",
                "carbon_source": item.get("feedstock", "waste plastic"),
            }
            if kind == "temperature":
                process_values["temperature_range_reported_C"] = "600-900"
                process_values["process_note"] = "Catalytic deposition temperatures tested: 600, 700, 800, and 900 C."
            elif kind == "ratio":
                process_values["carbon_source"] = "PP"
                process_values["process_note"] = "SS 316 catalyst-to-PP mass ratio scanned from 0 to 30; no obvious differences above 15."
            elif kind == "reuse":
                process_values["process_note"] = "MWCNTs were ultrasonically separated after each cycle; the recovered catalyst was reused and recalcinated after cycle 5."
            elif kind == "pretreatment":
                process_values["process_note"] = "Common plastic pyrolysis-catalysis process used to compare Raw, A, C, and A+C catalyst variants."
            else:
                process_values["process_note"] = f"Waste-plastic universality test using {item['feedstock']}."
            process = process_row(run_id, 1, "plastic_pyrolysis_catalysis", **process_values)
        if kind == "pretreatment":
            product = yield_row(
                run_id,
                primary_yield_metric="solid carbon yield",
                yield_original="11.0-47.6 wt.% solid yield",
                yield_definition_original="solid product mass fraction across the pretreatment comparison",
                secondary_result_summary="A+C pretreatment increased solid yield from 11.0 wt.% to 47.6 wt.%; filamentous carbon was mainly MWCNTs.",
                CNT_type_reported="multi-walled carbon nanotubes",
                CNT_type_confirmed="MWCNT",
                CNT_type_evidence="SEM and TEM",
                morphology="filamentous carbon mainly composed of MWCNTs",
                characterization_methods="SEM; TEM",
            )
        elif kind == "reuse":
            product = yield_row(
                run_id,
                primary_yield_metric="MWCNT yield and cumulative recovered mass",
                yield_original="maximum 662.0 mg g_plastic^-1 in cycle 3; approximately 6 g cumulative after 10 cycles",
                yield_definition_original="MWCNT mass per mass of plastic and cumulative MWCNT mass over reuse cycles",
                secondary_result_summary="Peak yield occurred in cycle 3; activity was recoverable by recalcination and approximately 6 g MWCNTs were collected after 10 cycles.",
                CNT_type_reported="multi-walled carbon nanotubes",
                CNT_type_confirmed="MWCNT",
                CNT_type_evidence="microscopy and recovered product identification",
                post_treatment_or_purification="ultrasonic separation from the monolithic catalyst after each cycle",
            )
        elif kind == "temperature":
            product = yield_row(
                run_id,
                primary_yield_metric="MWCNT mass per plastic feed",
                yield_original="662.0 mg g_plastic^-1 at 800 C",
                yield_definition_original="MWCNT mass per mass of plastic feed",
                secondary_result_summary="At 800 C the H2 yield was 51.3 mmol g_plastic^-1 and the MWCNT D/G ratio was 0.64.",
                CNT_type_reported="multi-walled carbon nanotubes",
                CNT_type_confirmed="MWCNT",
                CNT_type_evidence="Raman and microscopy",
                Raman_ratio_type="D/G",
                Raman_ratio_value="0.64",
                characterization_methods="Raman spectroscopy; microscopy",
            )
        elif kind == "ratio":
            product = yield_row(
                run_id,
                primary_yield_metric="solid yield trend",
                yield_original="not_reported",
                yield_definition_original="solid product yield over catalyst-to-PP mass-ratio scan",
                secondary_result_summary="Adding SS 316 sharply increased solid yield; no obvious differences were observed when the mass ratio exceeded 15.",
                CNT_type_reported="multi-walled carbon nanotubes",
                CNT_type_confirmed="MWCNT",
                CNT_type_evidence="study product identification",
            )
        elif kind == "feedstock":
            product = yield_row(
                run_id,
                primary_yield_metric="carbon yield",
                yield_original=f"{item['carbon_yield']} wt.% carbon",
                yield_definition_original="carbon-product mass fraction from the plastic feedstock",
                secondary_result_summary=f"More than 96% of the {item['feedstock']} carbon product was identified as MWCNTs.",
                CNT_type_reported="multi-walled carbon nanotubes",
                CNT_type_confirmed="MWCNT",
                CNT_type_evidence="more than 96% product identification",
                purified_product_purity_wt_percent="96",
                purity_basis=">96% of carbon product identified as MWCNTs",
                characterization_methods="TEM; product-yield analysis",
                notes="The reported carbon yield is retained as carbon yield and is not converted into an exact MWCNT yield.",
            )
        elif kind == "ethylene":
            product = yield_row(
                run_id,
                primary_yield_metric="not_reported",
                yield_original="not_reported",
                yield_definition_original="not_reported",
                secondary_result_summary="Fe3C and liquid-like particles inside CNT cavities supported a vapor-liquid-solid mechanism.",
                CNT_type_reported="carbon nanotubes",
                CNT_type_confirmed="not_reported",
                CNT_type_evidence="microscopy and phase identification",
                product_mixture_summary="CNTs with encapsulated Fe3C/liquid-like particles",
            )
        else:
            product = yield_row(
                run_id,
                primary_yield_metric="not_reported",
                yield_original="not_reported",
                yield_definition_original="not_reported",
                secondary_result_summary="The Fe-Ni catalyst remained solid and CNT growth followed a vapor-solid-solid mechanism; carbon yield was higher than in the ethylene control.",
                CNT_type_reported="carbon nanotubes",
                CNT_type_confirmed="not_reported",
                CNT_type_evidence="solid-state catalyst observation and control comparison",
                product_mixture_summary="CNTs grown from benzene over solid Fe-Ni alloy",
            )
        cost = cost_row(
            run_id,
            scale_level_demonstrated="laboratory two-stage fixed-bed batch",
            scale_level_claimed="massive industrial-scale MWCNT production",
            scale_evidence_summary="A self-supported monolithic mesh acts as both active component and support and permits physical CNT separation.",
            reactor_capacity_or_throughput="15 g monolithic catalyst charge",
            catalyst_lifetime_or_reuse="at least 10 cycles",
            catalyst_reuse_cycles="10",
            quantitative_cost_reported="not_reported",
            cost_driver_summary="waste-plastic feed, reactor heat, nitrogen, catalyst pretreatment, and ultrasonic CNT separation",
            emission_or_waste="waste plastic converted to carbon products and gas; quantitative emissions not reported",
            industrial_readiness_assessment="laboratory demonstration with repeat-use and scale-up claim",
        )
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].append(process)
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        tables["evidence_index"].extend(
            [
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_CAT_A", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_174E118370956E68EEA2", "The Methods report SS 316 monolith geometry and the acid/calcination pretreatment sequence."),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_CAT_B", run_id, "catalyst_system", catalyst["catalyst_id"], "active_metals", "SPAN_497A4789C42AC873FC28", "Microscopy and elemental mapping identify Fe-Ni alloy participation in CNT growth."),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_PROC", run_id, "reactor_process_gas", process["process_stage_id"], "record_level", (item["span"] if kind in {"ethylene", "benzene"} else "SPAN_12B28DD108E21440FBDD"), "The source reports the model compound or the common two-stage fixed-bed plastic pyrolysis-catalysis setup."),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_VARIANT", run_id, "reactor_process_gas", process["process_stage_id"], "record_level", item["span"], "The source identifies the record-specific pretreatment, reuse, temperature, ratio, feedstock, or model-compound variable."),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_PROD", run_id, "yield_quality", product["product_id"], "record_level", item["span"], "The source reports the record-specific yield, quality, or mechanism outcome."),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_COST_A", run_id, "cost_scale_review", run_id, "record_level", "SPAN_12B28DD108E21440FBDD", "The apparatus and catalyst charge support a laboratory fixed-bed assessment.", value_status="review_assessment"),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_COST_B", run_id, "cost_scale_review", run_id, "record_level", "SPAN_7E3362C159DF32835932", "The monolith reuse, physical separation, and industrial-scale claim support the scale review.", value_status="review_assessment"),
            ]
        )
        if kind == "reuse":
            tables["evidence_index"].append(
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_PROD_CUMULATIVE", run_id, "yield_quality", product["product_id"], "record_level", "SPAN_303A6F72C38E0855415C", "The source reports recalcination recovery and approximately 6 g cumulative MWCNTs after 10 reuse cycles.")
            )
        if kind in {"pretreatment", "reuse", "temperature", "ratio"}:
            issue_id = f"{source_id}_ISS_{index:02d}_SERIES_RESOLUTION"
            tables["review_issue_log"].append(
                issue_row(
                    issue_id,
                    source_id,
                    run_id,
                    "series_point_resolution",
                    "source_run",
                    run_id,
                    "data_type",
                    "The HTML main text supports the experimental series and key endpoints but not every supplementary plotted point. The series is represented once rather than inventing point-level runs.",
                    evidence_ids=f"{source_id}_EV_{index:02d}_PROD",
                    severity="medium",
                )
            )
        elif kind == "feedstock":
            issue_id = f"{source_id}_ISS_{index:02d}_YIELD_BASIS"
            tables["review_issue_log"].append(
                issue_row(
                    issue_id,
                    source_id,
                    run_id,
                    "yield_definition_scope",
                    "yield_quality",
                    product["product_id"],
                    "yield_original",
                    "The source reports total carbon yield and separately states that more than 96% was identified as MWCNTs. The carbon yield is not converted into an exact MWCNT yield.",
                    evidence_ids=f"{source_id}_EV_{index:02d}_PROD",
                    severity="medium",
                )
            )
    package = SHARD_ROOT / source_id
    write_package(package, tables)
    write_review(
        package,
        {
            "source_id": source_id,
            "review_status": "source_review_complete_needs_supervisory_review",
            "reviewer": "Codex",
            "source_identity_checked": True,
            "evidence_sections_checked": ["Catalyst preparation", "Pyrolysis-catalysis process", "Catalytic performance", "Reuse", "Temperature and mass-ratio effects", "Waste-plastic universality", "Mechanism controls"],
            "campaign_reconciliation": {"result_linked_campaigns_in_paper": 11, "extracted_runs": 11, "negative_runs_preserved": 0},
            "pdf_visual_review": {"completed": False, "pages_checked": [], "not_applicable_reason": "Local full text is HTML rather than PDF."},
            "html_source_review": {"completed": True, "sections_checked": ["Methods", "Figures 1-4 and captions", "Results", "Discussion"]},
            "series_resolution_check": "Pretreatment, reuse, temperature, and ratio sweeps remain series-level because supplementary point matrices are not present in the immutable main-text ledger.",
            "yield_policy_check": "Feedstock carbon yields are not silently relabelled as exact MWCNT yields; the separate >96% MWCNT identification is retained as its basis.",
            "cross_run_inheritance_check": "The grouped 20-50 nm diameter range is not copied into individual feedstock rows, and exact control-compound flow or duration is left unreported.",
        },
    )
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
    "LIT_65C8BD1BF4B591DD": build_lit_65c8bd1b,
    "LIT_87B8240D8CDFE77C": build_lit_87b8240d,
    "LIT_8AF8B4DBFDD89066": build_lit_8af8b4db,
    "LIT_9D1D16C5D2C154FD": build_lit_9d1d16c5,
    "LIT_A2AD11A61964181A": build_lit_a2ad11a6,
    "LIT_BD24584C41DAE4DD": build_lit_bd24584c,
    "LIT_B917C9617169F443": build_lit_b917c961,
    "LIT_C604F0126CF213E1": build_lit_c604f012,
    "LIT_D5BD8BD50A4E57A2": build_lit_d5bd8bd5,
    "LIT_D74C5ABB8CDC64C5": build_lit_d74c5abb,
    "LIT_ED1D628BC55C93F4": build_lit_ed1d628b,
    "LIT_F140D55ED8245E17": build_lit_f140d55e,
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
    "LIT_B49F1E2FC9A56304": {
        "reason": (
            "The experiment deposits graphitic/graphene shells onto pre-existing arc-discharge "
            "SWCNT paper and a pre-existing vertically aligned MWCNT forest. It thickens and "
            "encapsulates those CNT substrates but does not synthesize a new CNT campaign, so the "
            "methane-CVD conditions belong to graphene growth rather than CNT synthesis."
        ),
        "evidence_sections": [
            "Abstract",
            "Results and Figures 1-2",
            "Methods: Materials synthesis",
            "Author contributions",
        ],
        "pdf_pages_checked": [1, 2, 4],
    },
    "LIT_E047BBA44C22AA22": {
        "reason": (
            "The paper acid-treats an existing MWCNT material, loads Ni and Pt nanoparticles onto "
            "it, and evaluates NO2 removal. It reports no source-linked CNT growth recipe or CNT "
            "synthesis result; the performed synthesis is the supported Ni-Pt catalyst only."
        ),
        "evidence_sections": [
            "Abstract",
            "2.1 Material",
            "2.2 Acid treatment of multi-walled carbon nanotubes",
            "2.3 Preparation and synthesis of Ni-Pt/MWCNT nanocatalysts",
            "4. Conclusion",
        ],
        "pdf_pages_checked": [1, 2, 3, 8, 9],
    },
    "LIT_E7868486310B8B49": {
        "reason": (
            "The abstract explicitly describes the article as a brief review, and the body "
            "summarizes CNT synthesis methods, solar-cell concepts, and literature-derived "
            "performance tables without a reproducible CNT synthesis experiment performed in "
            "this paper."
        ),
        "evidence_sections": [
            "Abstract",
            "I. Introduction",
            "CNT synthesis-method overview and literature tables",
            "VI. Conclusion",
            "References",
        ],
        "pdf_pages_checked": [1, 2, 9, 10, 11],
    },
    "LIT_E9E787428CFD3649": {
        "reason": (
            "This is a review of published VACNT growth on flexible metal substrates. Its "
            "abstract and highlights state that substrate, catalyst, process, CNT-characteristic, "
            "and application results are reviewed; the document provides no new performed CNT "
            "synthesis campaign attributable to this source."
        ),
        "evidence_sections": [
            "Highlights",
            "Abstract",
            "Table of Contents",
            "8. Conclusion",
            "References",
        ],
        "pdf_pages_checked": [1, 3, 4, 5, 78, 79],
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
