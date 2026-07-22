#!/usr/bin/env python3
"""Source-specific builders and dispositions for supervised B-class redo shard 01."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Callable

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


SHARD = 1
SHARD_ROOT = REDO_ROOT / "shards" / f"{SHARD:02d}"
MANIFEST = SHARD_ROOT / "shard_manifest.csv"


def contexts() -> dict[str, SourceContext]:
    return {item.source_id: item for item in load_available_sources() if item.shard == SHARD}


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
    for item in rows:
        if item["source_id"] == source_id:
            item["redo_status"] = status
            item["package_path"] = package_path
            item["blocking_reason"] = blocking_reason
            break
    else:
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


def mark_disposition(
    context: SourceContext,
    *,
    status: str,
    reason: str,
    evidence_sections: list[str],
    pdf_pages_checked: list[int],
) -> Path:
    package = SHARD_ROOT / context.source_id
    package.mkdir(parents=True, exist_ok=True)
    is_pdf = context.local_source_path.lower().endswith(".pdf")
    review_status = "non_extractable" if status == "non_extractable" else "blocked"
    write_review(
        package,
        {
            "source_id": context.source_id,
            "review_status": review_status,
            "reviewer": "Codex",
            "source_identity_checked": True,
            "disposition": status,
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
                    "objects_checked": ["title and abstract", "methods or body", "source identity"],
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
        status,
        package_path=package.relative_to(REDO_ROOT).as_posix(),
        blocking_reason=reason,
    )
    return package


def build_lit_0cf79bcc(context: SourceContext) -> Path:
    """Wongchoosuk et al. 2010, cyclic growth/etch MWCNT synthesis."""
    source_id = context.source_id
    run = source_run_row(
        source_id,
        "CYCLIC_CVD",
        "cyclic acetylene CVD with water etching",
        "Thermal CVD growth and water-assisted selective etching were alternated for five cycles to produce MWCNTs.",
    )
    run_id = run["run_id"]
    catalyst = catalyst_row(
        run_id,
        catalyst_label="10 nm aluminium oxide / 5 nm stainless-steel catalyst stack",
        active_metals="stainless-steel catalyst layer; elemental composition not reported",
        support_material="silicon (100) substrate",
        metal_ratio_original="10 nm aluminium oxide / 5 nm stainless steel",
        preparation_method="reactive sputtering",
    )
    growth = process_row(
        run_id,
        1,
        "thermal_CVD_growth",
        reactor_type="thermal CVD reactor",
        temperature_setpoint_C="700",
        holding_time_min="3",
        carbon_source="acetylene",
        reducing_gas="hydrogen",
        gas_composition_summary="acetylene/hydrogen ratio 3.6:1",
        process_note="Growth stage alternated with water-assisted selective etching for five cycles.",
    )
    etch = process_row(
        run_id,
        2,
        "water_assisted_selective_etching",
        reactor_type="thermal CVD reactor",
        holding_time_min="3",
        inert_gas="Ar",
        cofeed_or_reactive_gas="water vapor",
        cofeed_flow_original="300 ppm",
        process_note="Water vapor was introduced by bubbling argon through liquid water; growth and etching were repeated for five cycles.",
    )
    product = yield_row(
        run_id,
        primary_yield_metric="not_reported",
        yield_original="not_reported",
        yield_definition_original="not_reported",
        secondary_result_summary="MWCNT diameter approximately 35 nm and length approximately 26 micrometres; electrical conductivity approximately 75 S/cm.",
        CNT_type_reported="multi-walled carbon nanotubes",
        CNT_type_confirmed="MWCNT",
        CNT_type_evidence="HR-TEM; approximately 14 walls",
        outer_diameter_mean_nm="35",
        wall_number_summary="approximately 14 walls; reported wall-width measure approximately 4.6 nm",
        length_summary="approximately 26 micrometres",
        morphology="multi-walled nanotubes",
        characterization_methods="SEM; HR-TEM; four-point probe",
    )
    cost = cost_row(
        run_id,
        scale_level_demonstrated="laboratory substrate CVD",
        scale_level_claimed="not_reported",
        scale_evidence_summary="Catalyst-coated silicon substrate processed by cyclic CVD and water etching.",
        quantitative_cost_reported="not_reported",
        scale_up_issue="five alternating growth and etch cycles increase recipe complexity",
        industrial_readiness_assessment="laboratory materials synthesis",
    )
    tables = {
        "source_master": [source_master_row(context, "One cyclic MWCNT synthesis protocol precedes sensor-film fabrication; the latter is not a separate CNT growth run.")],
        "source_run": [run],
        "catalyst_system": [catalyst],
        "reactor_process_gas": [growth, etch],
        "yield_quality": [product],
        "cost_scale_review": [cost],
        "evidence_index": [
            evidence_row(source_id, f"{source_id}_EV_CAT", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_D1BA17C49D6102FD5297", "The preparation section reports catalyst-stack thicknesses, substrate, and sputter deposition."),
            evidence_row(source_id, f"{source_id}_EV_GROWTH", run_id, "reactor_process_gas", growth["process_stage_id"], "record_level", "SPAN_D1BA17C49D6102FD5297", "The section reports CVD temperature, duration, gas ratio, and repeated cyclic sequence."),
            evidence_row(source_id, f"{source_id}_EV_ETCH", run_id, "reactor_process_gas", etch["process_stage_id"], "record_level", "SPAN_D1BA17C49D6102FD5297", "The section reports the water-vapor concentration, argon bubbler, etch duration, and cycle count."),
            evidence_row(source_id, f"{source_id}_EV_PRODUCT_A", run_id, "yield_quality", product["product_id"], "record_level", "SPAN_D1BA17C49D6102FD5297", "SEM and electrical measurements report MWCNT diameter, length, and conductivity."),
            evidence_row(source_id, f"{source_id}_EV_PRODUCT_B", run_id, "yield_quality", product["product_id"], "record_level", "SPAN_1C215AA2F1C72B26EA1A", "HR-TEM confirms the multi-walled structure, reported wall-width measure, wall count, and layer spacing."),
            evidence_row(source_id, f"{source_id}_EV_COST", run_id, "cost_scale_review", run_id, "record_level", "SPAN_D1BA17C49D6102FD5297", "The substrate process and five-cycle sequence support a laboratory-scale review; cost is not quantified.", value_status="review_assessment"),
        ],
        "review_issue_log": [
            issue_row(
                f"{source_id}_ISS_FLOW_SPLIT",
                source_id,
                run_id,
                "gas_flow_not_reported",
                "reactor_process_gas",
                growth["process_stage_id"],
                "carbon_source_flow_sccm",
                "Only the acetylene/hydrogen ratio is reported; individual flow rates are left blank.",
                evidence_ids=f"{source_id}_EV_GROWTH",
                severity="medium",
            )
        ],
    }
    package = SHARD_ROOT / source_id
    write_package(package, tables)
    write_review(
        package,
        {
            "source_id": source_id,
            "review_status": "source_review_complete_needs_supervisory_review",
            "reviewer": "Codex",
            "source_identity_checked": True,
            "evidence_sections_checked": ["2.1 Preparation of Materials", "2.2 Fabrication of MWCNT-doped film", "Figures 1-2"],
            "campaign_reconciliation": {"result_linked_campaigns_in_paper": 1, "extracted_runs": 1, "negative_runs_preserved": 0},
            "pdf_visual_review": {"completed": False, "pages_checked": [], "not_applicable_reason": "Local source is HTML rather than PDF."},
            "html_source_review": {"completed": True, "sections_checked": ["2.1 Preparation of Materials", "Figures 1-2", "Conclusion"]},
            "cross_run_inheritance_check": "Sensor-film fabrication is downstream use of the synthesized MWCNT powder and is not represented as a CNT growth run.",
        },
    )
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


def build_lit_1d9479e2(context: SourceContext) -> Path:
    """Williamson et al. 2019, floating-catalyst CNT/NCNT synthesis variants."""
    source_id = context.source_id
    variants = [
        ("FE_NCNT", "Fe@NCNT", "Fe", "1.0 g ferrocene in 50 mL acetonitrile", "acetonitrile", "SPAN_53B80294398D204A56B0", "1.5 g raw Fe@NCNT catalyst from a 40 mL injection"),
        ("FE_CNT", "Fe@CNT", "Fe", "1.0 g ferrocene in 50 mL toluene", "toluene", "SPAN_4DF10768F51BFC48B3D3", "not_reported"),
        ("RUFE_NCNT_LOW", "Ru,Fe@NCNT-0.05/0.95", "Ru; Fe", "0.05 g ruthenocene / 0.95 g ferrocene in 50 mL acetonitrile", "acetonitrile", "SPAN_5AAB4DDAF3725D03AFA6", "not_reported"),
        ("RUFE_NCNT_HIGH", "Ru,Fe@NCNT-0.20/1.0", "Ru; Fe", "0.20 g ruthenocene / 1.0 g ferrocene in 50 mL acetonitrile", "acetonitrile", "SPAN_5AAB4DDAF3725D03AFA6", "not_reported"),
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [source_master_row(context, "Four performed floating-catalyst CNT/NCNT growth compositions are separated from downstream activation, Ru post-doping, and methanation tests.")],
        "source_run": [],
        "catalyst_system": [],
        "reactor_process_gas": [],
        "yield_quality": [],
        "cost_scale_review": [],
        "evidence_index": [],
        "review_issue_log": [],
    }
    for index, (code, label, metals, precursor, solvent, variant_span, yield_value) in enumerate(variants, 1):
        run = source_run_row(source_id, code, label, f"Floating-catalyst CVD synthesis of {label} using {solvent} as the carbon-source solvent.")
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label=label,
            active_metals=metals,
            support_material="unsupported floating catalyst",
            metal_ratio_original=precursor,
            precursor_summary=precursor,
            preparation_method="organometallic precursor dissolved in carbon-source solvent and injected into a tubular CVD reactor",
            phase_or_state_summary="metal nanoparticles nucleate CNT growth and remain embedded in the CNT structure",
        )
        process = process_row(
            run_id,
            1,
            "floating_catalyst_CVD",
            reactor_type="tubular furnace",
            reactor_material="quartz",
            reactor_size_summary="25 mm ID x 28 mm OD x 122 cm length quartz tube",
            temperature_setpoint_C="790",
            carbon_source=solvent,
            carbon_source_flow_original="40 mL solution injected at 10 mL/h",
            reducing_gas="H2",
            reducing_gas_flow_original="50 sccm",
            reducing_gas_flow_sccm="50",
            inert_gas="Ar",
            inert_gas_flow_original="400 sccm",
            inert_gas_flow_sccm="400",
            process_note="CVD precursor injection continued for 4 hours.",
        )
        if yield_value == "not_reported":
            product = yield_row(
                run_id,
                primary_yield_metric="not_reported",
                yield_original="not_reported",
                yield_definition_original="not_reported",
                secondary_result_summary=f"CVD-synthesized {label}; quantitative CNT production yield not reported for this composition.",
                CNT_type_reported="nitrogen-doped carbon nanotubes" if "NCNT" in label else "carbon nanotubes",
                CNT_type_confirmed="not_reported",
                CNT_type_evidence="Raman, SEM, TEM, XRD, XPS, and EDX characterization",
                characterization_methods="Raman spectroscopy; SEM; TEM; XRD; XPS; EDX",
            )
        else:
            product = yield_row(
                run_id,
                primary_yield_metric="raw catalyst product mass",
                yield_original=yield_value,
                yield_definition_original="raw Fe@NCNT catalyst recovered from a 40 mL precursor-solution injection",
                secondary_result_summary="Typical 40 mL injection yielded approximately 1.5 g raw Fe@NCNT catalyst.",
                CNT_type_reported="nitrogen-doped carbon nanotubes",
                CNT_type_confirmed="not_reported",
                CNT_type_evidence="Raman, SEM, TEM, XRD, XPS, and EDX characterization",
                characterization_methods="Raman spectroscopy; SEM; TEM; XRD; XPS; EDX",
            )
        cost = cost_row(
            run_id,
            scale_level_demonstrated="laboratory tubular-furnace batch",
            scale_level_claimed="not_reported",
            scale_evidence_summary="A precursor solution was injected into a quartz tube furnace and raw catalyst was collected from the tube.",
            reactor_capacity_or_throughput="40 mL solution injection over 4 h in a 25 mm ID tube",
            quantitative_cost_reported="not_reported",
            cost_driver_summary="organometallic precursor, carbon-source solvent, hydrogen, argon, and furnace heat",
            industrial_readiness_assessment="laboratory catalyst-support synthesis",
        )
        tables["source_run"].append(run)
        tables["catalyst_system"].append(catalyst)
        tables["reactor_process_gas"].append(process)
        tables["yield_quality"].append(product)
        tables["cost_scale_review"].append(cost)
        tables["evidence_index"].extend(
            [
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_CAT_BASE", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_53B80294398D204A56B0", "The Experimental section reports the ferrocene/acetonitrile base precursor and floating-catalyst role."),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_CAT_VARIANT", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", variant_span, f"The source identifies the precursor composition and solvent change for {label}."),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_PROCESS", run_id, "reactor_process_gas", process["process_stage_id"], "record_level", "SPAN_53B80294398D204A56B0", "The Experimental section reports solution injection, reactor dimensions, temperature, duration, hydrogen flow, and argon flow."),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_PROCESS_VARIANT", run_id, "reactor_process_gas", process["process_stage_id"], "carbon_source", variant_span, f"The variant evidence identifies {solvent} as the carbon-source solvent."),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_PRODUCT", run_id, "yield_quality", product["product_id"], "record_level", ("SPAN_53B80294398D204A56B0" if yield_value != "not_reported" else variant_span), f"The source identifies CVD-synthesized {label}" + (" and the typical recovered mass." if yield_value != "not_reported" else "; composition-specific yield is not reported.")),
                evidence_row(source_id, f"{source_id}_EV_{index:02d}_COST", run_id, "cost_scale_review", run_id, "record_level", "SPAN_53B80294398D204A56B0", "The reported reactor, injection volume, duration, and recovery support a laboratory batch assessment; quantitative cost is absent.", value_status="review_assessment"),
            ]
        )
        if yield_value == "not_reported":
            tables["review_issue_log"].append(
                issue_row(
                    f"{source_id}_ISS_{index:02d}_YIELD",
                    source_id,
                    run_id,
                    "composition_specific_yield_missing",
                    "yield_quality",
                    product["product_id"],
                    "yield_original",
                    "The paper confirms this CVD composition but does not report a composition-specific CNT product yield; the base-process typical mass is not inherited.",
                    evidence_ids=f"{source_id}_EV_{index:02d}_PRODUCT",
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
            "evidence_sections_checked": ["Experimental: Materials naming convention", "Preparation of underlying Fe@NCNT", "Preparation of CVD-doped Ru,Fe@NCNT", "Catalyst characterization"],
            "campaign_reconciliation": {"result_linked_campaigns_in_paper": 4, "extracted_runs": 4, "negative_runs_preserved": 0},
            "pdf_visual_review": {"completed": True, "pages_checked": [11, 12], "objects_checked": ["underlying Fe@NCNT method", "CVD-doped Ru,Fe@NCNT compositions", "activation and characterization methods"]},
            "cross_run_inheritance_check": "The typical 1.5 g recovered mass is retained only for the base Fe@NCNT recipe and not copied to the solvent or ruthenocene variants.",
            "scope_check": "Post-synthesis activation, wet Ru impregnation, and methanation trials are excluded from CNT growth runs.",
        },
    )
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


def build_lit_7f4bcfd4(context: SourceContext) -> Path:
    """Zheng et al. 2004, centimetre-scale SWNT growth from ethanol."""
    source_id = context.source_id
    run = source_run_row(
        source_id,
        "ULTRALONG_SWNT",
        "4 cm individual SWNT",
        "Fe-catalysed ethanol CVD on silicon produced an individual 4 cm single-wall carbon nanotube.",
    )
    run_id = run["run_id"]
    catalyst = catalyst_row(
        run_id,
        catalyst_label="0.1 M FeCl3 dip-pen catalyst",
        active_metals="Fe",
        support_material="silicon substrate",
        metal_ratio_original="0.1 M FeCl3 solution",
        precursor_summary="FeCl3 solution applied to one end of the silicon substrate",
        preparation_method="dip-pen application followed by calcination",
        phase_or_state_summary="mobile Fe catalyst particle consistent with tip growth",
    )
    calcination = process_row(
        run_id,
        1,
        "catalyst_calcination",
        reactor_type="horizontal quartz tube furnace",
        reactor_size_summary="2.5 cm quartz tube",
        temperature_setpoint_C="900",
        holding_time_min="30",
        reducing_gas="H2",
        inert_gas="Ar",
        gas_composition_summary="Ar + 6% H2",
        total_flow_original="30 cm3/min",
    )
    growth = process_row(
        run_id,
        2,
        "ethanol_CVD_growth",
        reactor_type="horizontal quartz tube furnace",
        reactor_size_summary="2.5 cm quartz tube",
        temperature_setpoint_C="900",
        holding_time_min="60",
        carbon_source="ethanol vapour",
        carbon_source_flow_original="carrier mixture bubbled through ethanol at 20 cm3/min",
        reducing_gas="H2",
        inert_gas="Ar",
        gas_composition_summary="Ar + 6% H2 carrier mixture",
        cooling_condition="growth stopped by switching to Ar + 6% H2 and cooling the furnace",
    )
    product = yield_row(
        run_id,
        primary_yield_metric="individual SWNT length",
        yield_original="4 cm",
        yield_definition_original="length of an individual SWNT traced by 230 SEM images on a 4.8 cm silicon substrate",
        secondary_result_summary="Calculated growth rate 11 micrometres/s over the 1 h synthesis; sampled nanotube diameters ranged from 1.31 to 2.25 nm.",
        CNT_type_reported="single-wall carbon nanotube",
        CNT_type_confirmed="SWCNT",
        CNT_type_evidence="SEM, AFM and Raman RBM/G-band measurements",
        outer_diameter_range_nm="1.31-2.25",
        length_summary="individual nanotube length 4 cm; nanotubes longer than 2.5 cm consistently obtained over a wide parameter window",
        morphology="ultralong individual nanotube lying on silicon substrate",
        characterization_methods="SEM; AFM; Raman spectroscopy",
    )
    cost = cost_row(
        run_id,
        scale_level_demonstrated="laboratory substrate CVD",
        scale_level_claimed="commercial applications discussed",
        scale_evidence_summary="A 4 cm individual SWNT was grown on a 4.8 cm silicon substrate in a 2.5 cm quartz tube furnace.",
        quantitative_cost_reported="not_reported",
        cost_driver_summary="furnace heat, FeCl3 catalyst, ethanol, argon and hydrogen",
        scale_up_issue="nanotube density and length depend on catalyst concentration, growth temperature and substrate oxide",
        industrial_readiness_assessment="laboratory proof of centimetre-scale continuous SWNT growth",
    )
    tables = {
        "source_master": [source_master_row(context, "The paper's representative one-hour ultralong-SWNT recipe is extracted as one run; qualitative parameter-window observations are not fabricated into point runs.")],
        "source_run": [run],
        "catalyst_system": [catalyst],
        "reactor_process_gas": [calcination, growth],
        "yield_quality": [product],
        "cost_scale_review": [cost],
        "evidence_index": [
            evidence_row(source_id, f"{source_id}_EV_CAT", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_FEE05A386A583B0C7670", "The synthesis paragraph reports the 0.1 M FeCl3 dip-pen catalyst on silicon."),
            evidence_row(source_id, f"{source_id}_EV_CALC", run_id, "reactor_process_gas", calcination["process_stage_id"], "record_level", "SPAN_A3D2EBF475BC5C698E33", "The synthesis paragraph reports tube size, catalyst calcination temperature and time, carrier composition, and flow."),
            evidence_row(source_id, f"{source_id}_EV_GROWTH_A", run_id, "reactor_process_gas", growth["process_stage_id"], "record_level", "SPAN_A3D2EBF475BC5C698E33", "The synthesis paragraph identifies ethanol CVD in the quartz tube and the 900 C synthesis condition."),
            evidence_row(source_id, f"{source_id}_EV_GROWTH_B", run_id, "reactor_process_gas", growth["process_stage_id"], "record_level", "SPAN_81D3FB7F1699B769C421", "The continuation reports the 20 cm3/min ethanol-bubbler flow, one-hour duration, termination gas, and cooling."),
            evidence_row(source_id, f"{source_id}_EV_PRODUCT_A", run_id, "yield_quality", product["product_id"], "record_level", "SPAN_4DE72EC5786D713855DA", "The source reports the 4 cm individual SWNT, 4.8 cm substrate, and 230-image SEM trace."),
            evidence_row(source_id, f"{source_id}_EV_PRODUCT_B", run_id, "yield_quality", product["product_id"], "record_level", "SPAN_C807C892DA6B5D24D9C0", "The source reports the one-hour calculated 11 micrometres/s growth rate and repeatable lengths above 2.5 cm."),
            evidence_row(source_id, f"{source_id}_EV_PRODUCT_C", run_id, "yield_quality", product["product_id"], "record_level", "SPAN_20E368C702B31C7711BF", "Raman RBM measurements support SWNT assignment and the reported 1.31-2.25 nm diameter range."),
            evidence_row(source_id, f"{source_id}_EV_COST", run_id, "cost_scale_review", run_id, "record_level", "SPAN_5FB46776323FABAC5E17", "The centimetre-scale result and commercial-applications discussion support the scale review; cost is not quantified.", value_status="review_assessment"),
        ],
        "review_issue_log": [
            issue_row(
                f"{source_id}_ISS_WINDOW",
                source_id,
                run_id,
                "parameter_window_not_point_resolved",
                "source_run",
                run_id,
                "run_description",
                "The paper states that catalyst concentration and growth temperature affect density and length but does not publish the point matrix; only the fully described representative recipe is extracted.",
                evidence_ids=f"{source_id}_EV_PRODUCT_B",
                severity="medium",
            )
        ],
    }
    package = SHARD_ROOT / source_id
    write_package(package, tables)
    write_review(
        package,
        {
            "source_id": source_id,
            "review_status": "source_review_complete_needs_supervisory_review",
            "reviewer": "Codex",
            "source_identity_checked": True,
            "evidence_sections_checked": ["title and opening result", "synthesis paragraph", "Figures 1-5", "closing discussion"],
            "campaign_reconciliation": {"result_linked_campaigns_in_paper": 1, "extracted_runs": 1, "negative_runs_preserved": 0},
            "pdf_visual_review": {"completed": True, "pages_checked": [1, 2, 3, 4], "objects_checked": ["title and source identity", "synthesis paragraph", "SEM/AFM/Raman figures", "closing discussion and references"]},
            "cross_run_inheritance_check": "Qualitative parameter effects are retained as an unresolved experimental series and not expanded into synthetic point records.",
        },
    )
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


def build_lit_9181ccce(context: SourceContext) -> Path:
    """Hao et al. 2016, Fe- and FeCo-filled multiwall CNT synthesis."""
    source_id = context.source_id
    variants = [
        ("FECO_FILLED", "FeCo-filled CNTs", "Fe; Co", "ferrocene and cobaltocene in trichlorobenzene", "trichlorobenzene", "30", "0.84", "bamboo-like multiwall CNTs filled with Fe-Co alloy"),
        ("FE_FILLED", "Fe-filled CNTs", "Fe", "ferrocene in dichlorobenzene", "dichlorobenzene", "", "0.51", "bamboo-like multiwall CNTs with Fe-filled cavities"),
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [source_master_row(context, "Two metal-filled CNT syntheses described in the Materials and Methods are extracted; the separately provided fluidized-bed MWCNT material is not treated as a performed run.")],
        "source_run": [], "catalyst_system": [], "reactor_process_gas": [], "yield_quality": [], "cost_scale_review": [], "evidence_index": [], "review_issue_log": [],
    }
    for index, (code, label, metals, precursor, solvent, duration, dg, morphology) in enumerate(variants, 1):
        run = source_run_row(source_id, code, label, f"Floating-catalyst CVD synthesis of {label} from {precursor}.")
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label=label,
            active_metals=metals,
            support_material="unsupported floating catalyst",
            precursor_summary=precursor,
            preparation_method="organometallic precursor solution injected by syringe pump into a CVD reactor",
            phase_or_state_summary="metal or alloy encapsulated within multiwall CNT cavities",
        )
        process_values: dict[str, str] = {
            "reactor_type": "tubular CVD furnace",
            "reactor_material": "quartz",
            "temperature_setpoint_C": "860",
            "carbon_source": solvent,
            "reducing_gas": "H2",
            "reducing_gas_flow_original": "3000 sccm",
            "reducing_gas_flow_sccm": "3000",
            "inert_gas": "Ar",
            "inert_gas_flow_original": "2000 sccm",
            "inert_gas_flow_sccm": "2000",
            "cooling_condition": "natural cooling to room temperature" if duration else "not_reported",
        }
        if duration:
            process_values["holding_time_min"] = duration
        process = process_row(run_id, 1, "floating_catalyst_CVD", **process_values)
        product = yield_row(
            run_id,
            primary_yield_metric="not_reported",
            yield_original="not_reported",
            yield_definition_original="not_reported",
            secondary_result_summary=f"Raman ID/IG ratio {dg}; {morphology}.",
            CNT_type_reported="metal-filled carbon nanotubes",
            CNT_type_confirmed="MWCNT",
            CNT_type_evidence="HRTEM shows more than ten carbon layers",
            wall_number_summary="more than ten carbon layers",
            morphology=morphology,
            Raman_ratio_type="ID/IG",
            Raman_ratio_value=dg,
            characterization_methods="TEM; HRTEM; Raman spectroscopy",
        )
        cost = cost_row(
            run_id,
            scale_level_demonstrated="laboratory tubular-CVD batch",
            scale_level_claimed="not_reported",
            scale_evidence_summary="Precursor solution was syringe-pumped into a heated tubular CVD reactor.",
            quantitative_cost_reported="not_reported",
            cost_driver_summary="organometallic precursor, chlorinated aromatic solvent, hydrogen, argon, and furnace heat",
            safety_risk="chlorinated aromatic solvent and hydrogen handling",
            industrial_readiness_assessment="laboratory material synthesis",
        )
        tables["source_run"].append(run); tables["catalyst_system"].append(catalyst); tables["reactor_process_gas"].append(process); tables["yield_quality"].append(product); tables["cost_scale_review"].append(cost)
        tables["evidence_index"].extend([
            evidence_row(source_id, f"{source_id}_EV_{index:02d}_CAT", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_FFD905A476E402FECFA1", "The Methods identify the organometallic precursor and chlorinated aromatic solvent."),
            evidence_row(source_id, f"{source_id}_EV_{index:02d}_PROCESS", run_id, "reactor_process_gas", process["process_stage_id"], "record_level", "SPAN_FFD905A476E402FECFA1", "The Methods report reactor type, temperature, argon and hydrogen flows, and the FeCo-run duration and cooling."),
            evidence_row(source_id, f"{source_id}_EV_{index:02d}_PRODUCT_A", run_id, "yield_quality", product["product_id"], "record_level", "SPAN_E08C7DB37C7058948AC5", "HRTEM reports multiwall structure and metal-filled morphology."),
            evidence_row(source_id, f"{source_id}_EV_{index:02d}_PRODUCT_B", run_id, "yield_quality", product["product_id"], "record_level", "SPAN_5A43D64E2CA4F4D69316", "The Raman section reports separate ID/IG ratios for FeCo-CNTs and Fe-CNTs."),
            evidence_row(source_id, f"{source_id}_EV_{index:02d}_COST", run_id, "cost_scale_review", run_id, "record_level", "SPAN_FFD905A476E402FECFA1", "The syringe-pump tubular-CVD setup supports a laboratory-scale review; cost is not quantified.", value_status="review_assessment"),
        ])
        if not duration:
            tables["review_issue_log"].append(issue_row(f"{source_id}_ISS_FE_DURATION", source_id, run_id, "duration_not_reported", "reactor_process_gas", process["process_stage_id"], "holding_time_min", "The Fe-filled CNT paragraph repeats temperature and gas flows but does not restate a duration; the FeCo duration is not inherited.", evidence_ids=f"{source_id}_EV_{index:02d}_PROCESS", severity="medium"))
    package = SHARD_ROOT / source_id
    write_package(package, tables)
    write_review(package, {
        "source_id": source_id, "review_status": "source_review_complete_needs_supervisory_review", "reviewer": "Codex", "source_identity_checked": True,
        "evidence_sections_checked": ["Materials and Methods: Sample preparation", "Characterization of CNTs", "Figure 1"],
        "campaign_reconciliation": {"result_linked_campaigns_in_paper": 2, "extracted_runs": 2, "negative_runs_preserved": 0},
        "pdf_visual_review": {"completed": True, "pages_checked": [3, 5], "objects_checked": ["sample-preparation method", "TEM/HRTEM and Raman characterization"]},
        "cross_run_inheritance_check": "The FeCo run duration is not inherited by the Fe-only run, and the externally provided MWCNT material is excluded from performed runs.",
    })
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


def build_lit_954c0d69(context: SourceContext) -> Path:
    """Mo et al. 2024, VACNT template and patterned device-wafer growths."""
    source_id = context.source_id
    variants = [
        ("FIVE_MIN", "5 min VACNT height test", "5", "96.3", "", "SPAN_51980A2AC11ED264C526", "laboratory patterned-array test", "not_reported"),
        ("DEVICE_WAFER", "patterned accelerometer VACNT wafer", "", "10", "9.6-11.2", "SPAN_9D83644B9A541AA63566", "4-inch device wafer", "MEMS composite fabrication"),
    ]
    tables: dict[str, list[dict[str, str]]] = {
        "source_master": [source_master_row(context, "The reported five-minute height test and the patterned four-inch device-wafer growth are retained as separate VACNT records; downstream SiC infiltration is excluded.")],
        "source_run": [], "catalyst_system": [], "reactor_process_gas": [], "yield_quality": [], "cost_scale_review": [], "evidence_index": [], "review_issue_log": [],
    }
    for index, (code, label, duration, height, height_range, product_span, demonstrated, claimed) in enumerate(variants, 1):
        run = source_run_row(source_id, code, label, f"VACNT growth on an evaporated Al2O3/Fe catalyst stack; reported array height {height} micrometres.")
        run_id = run["run_id"]
        catalyst = catalyst_row(
            run_id,
            catalyst_label="20 nm Al2O3 / 2 nm Fe thin-film catalyst",
            active_metals="Fe",
            support_material="silicon substrate with SiO2 diffusion barrier",
            metal_ratio_original="20 nm Al2O3 / 2 nm Fe",
            precursor_summary="electron-beam-evaporated Al2O3 and Fe films",
            preparation_method="electron-beam evaporation" + (" with lithographic lift-off patterning" if code == "DEVICE_WAFER" else ""),
        )
        activation = process_row(
            run_id, 1, "catalyst_activation", reactor_type="Aixtron Blackmagic CVD", temperature_setpoint_C="500", holding_time_min="3", reducing_gas="H2",
        )
        growth_values: dict[str, str] = {
            "reactor_type": "Aixtron Blackmagic CVD",
            "temperature_setpoint_C": "600",
            "pressure_original": "80 mbar",
            "carbon_source": "C2H2",
            "carbon_source_flow_original": "50 sccm",
            "carbon_source_flow_sccm": "50",
            "reducing_gas": "H2",
            "reducing_gas_flow_original": "700 sccm",
            "reducing_gas_flow_sccm": "700",
        }
        if duration:
            growth_values["holding_time_min"] = duration
        else:
            growth_values["process_note"] = "Device-wafer growth duration is not reported; the resulting wafer-scale height range is retained in the product record."
        growth = process_row(run_id, 2, "VACNT_growth", **growth_values)
        product = yield_row(
            run_id,
            primary_yield_metric="VACNT array height",
            yield_original=(f"{height} micrometres" if not height_range else f"approximately {height} micrometres; wafer range {height_range} micrometres"),
            yield_definition_original="vertical CNT array height measured by SEM",
            secondary_result_summary=(f"Highest array from a 5 min deposition reached {height} micrometres." if code == "FIVE_MIN" else f"Patterned 4-inch wafer array height varied from {height_range} micrometres from edge to center."),
            CNT_type_reported="vertically aligned carbon nanotube array",
            CNT_type_confirmed="not_reported",
            CNT_type_evidence="SEM array morphology",
            length_summary=(f"array height {height} micrometres" if not height_range else f"array height {height_range} micrometres across the 4-inch wafer"),
            morphology="vertically aligned CNT array",
            alignment_or_array="VACNT array",
            characterization_methods="SEM",
        )
        cost = cost_row(
            run_id,
            scale_level_demonstrated=demonstrated,
            scale_level_claimed=claimed,
            scale_evidence_summary=("A five-minute patterned-array height test was demonstrated." if code == "FIVE_MIN" else "A patterned VACNT array was grown across a 4-inch device wafer."),
            reactor_capacity_or_throughput="single-zone Aixtron Blackmagic wafer CVD",
            quantitative_cost_reported="not_reported",
            scale_up_issue="height non-uniformity from single-zone furnace temperature distribution" if code == "DEVICE_WAFER" else "growth rate decreases with catalyst depletion",
            industrial_readiness_assessment="MEMS process demonstration" if code == "DEVICE_WAFER" else "laboratory growth characterization",
        )
        tables["source_run"].append(run); tables["catalyst_system"].append(catalyst); tables["reactor_process_gas"].extend([activation, growth]); tables["yield_quality"].append(product); tables["cost_scale_review"].append(cost)
        tables["evidence_index"].extend([
            evidence_row(source_id, f"{source_id}_EV_{index:02d}_CAT", run_id, "catalyst_system", catalyst["catalyst_id"], "record_level", "SPAN_FEF9AD90FCC09A496C5A", "The Materials and methods report the SiO2 barrier and 20 nm Al2O3 / 2 nm Fe e-beam-evaporated catalyst stack."),
            evidence_row(source_id, f"{source_id}_EV_{index:02d}_ACT", run_id, "reactor_process_gas", activation["process_stage_id"], "record_level", "SPAN_F45AD94F207CC673BC22", "The source reports hydrogen activation at 500 C for 3 min."),
            evidence_row(source_id, f"{source_id}_EV_{index:02d}_GROWTH", run_id, "reactor_process_gas", growth["process_stage_id"], "record_level", "SPAN_F45AD94F207CC673BC22", "The source reports reactor, temperature, pressure, and H2/C2H2 flows for VACNT growth."),
            evidence_row(source_id, f"{source_id}_EV_{index:02d}_PRODUCT", run_id, "yield_quality", product["product_id"], "record_level", product_span, "The source reports the record-specific VACNT height and morphology."),
            evidence_row(source_id, f"{source_id}_EV_{index:02d}_COST", run_id, "cost_scale_review", run_id, "record_level", product_span, "The reported test structure or four-inch wafer supports the scale assessment; no quantitative cost is reported.", value_status="review_assessment"),
        ])
        if not duration:
            tables["review_issue_log"].append(issue_row(f"{source_id}_ISS_DEVICE_DURATION", source_id, run_id, "duration_not_reported", "reactor_process_gas", growth["process_stage_id"], "holding_time_min", "The device-wafer section reports the height range but not the growth duration; the five-minute characterization duration is not inherited.", evidence_ids=f"{source_id}_EV_{index:02d}_PRODUCT", severity="medium"))
    package = SHARD_ROOT / source_id
    write_package(package, tables)
    write_review(package, {
        "source_id": source_id, "review_status": "source_review_complete_needs_supervisory_review", "reviewer": "Codex", "source_identity_checked": True,
        "evidence_sections_checked": ["Materials and methods", "CNT growth", "Figure 2", "Figure 6 process overview"],
        "campaign_reconciliation": {"result_linked_campaigns_in_paper": 2, "extracted_runs": 2, "negative_runs_preserved": 0},
        "pdf_visual_review": {"completed": True, "pages_checked": [2, 3, 7], "objects_checked": ["catalyst and CVD method", "five-minute array-height result", "patterned wafer process and height range"]},
        "cross_run_inheritance_check": "The five-minute duration is not copied into the device-wafer record; post-growth SiC LPCVD filling is excluded from CNT synthesis stages.",
    })
    update_manifest(source_id, "extracted_needs_supervisory_review", package_path=package.relative_to(REDO_ROOT).as_posix())
    return package


BUILDERS: dict[str, Callable[[SourceContext], Path]] = {
    "LIT_0CF79BCC68CC6093": build_lit_0cf79bcc,
    "LIT_1D9479E2BC5CDCEF": build_lit_1d9479e2,
    "LIT_7F4BCFD45E802E6F": build_lit_7f4bcfd4,
    "LIT_9181CCCE7A19C985": build_lit_9181ccce,
    "LIT_954C0D690A6F7711": build_lit_954c0d69,
}


NON_EXTRACTABLE = {
    "LIT_04A53D0FAD58D6F5": {
        "reason": "First-principles calculation study of carbon binding, diffusion, and CNT edge stability on metal nanoparticles; it reports no performed CNT synthesis experiment.",
        "evidence_sections": ["Abstract", "computational model", "CVD growth discussion", "Conclusion"],
        "pdf_pages_checked": [1, 2],
    },
    "LIT_1F7E1502476BD217": {
        "reason": "The local HTML is a subscription preview containing only the abstract, references, and purchase notice. It does not expose the run matrix, full methods, or result tables needed for source-grounded extraction.",
        "evidence_sections": ["Abstract", "Buy Now", "References"],
        "pdf_pages_checked": [],
    },
    "LIT_4DC70416A368D5D9": {
        "reason": "The study acid-oxidizes existing MWNTs and coats them with ZnO nanoparticles for photocatalysis. It does not perform or report a source-linked CNT growth campaign.",
        "evidence_sections": ["Abstract", "3. Experimental", "Results and discussion", "5. Conclusion"],
        "pdf_pages_checked": [1, 2, 3],
    },
    "LIT_85779E66B8B0D55E": {
        "reason": "Commercially purchased MWCNTs are acid-functionalized and combined with graphene oxide and L-cysteine for an electrochemical sensor; no CNT synthesis is performed.",
        "evidence_sections": ["Abstract", "Experimental: Reagents", "Segmentation and carboxylation of MWCNTs", "Results"],
        "pdf_pages_checked": [1, 2, 3],
    },
    "LIT_83FA0F9754638BBF": {
        "reason": "The registered source is an InTech book chapter that synthesizes and re-presents the authors' previously published CVD/PECVD results. It does not identify a new, source-specific performed run matrix suitable for primary experimental extraction.",
        "evidence_sections": ["chapter title and Introduction", "CVD versus PECVD overview", "process-parameter sections", "references"],
        "pdf_pages_checked": [1, 2, 17, 18],
    },
    "LIT_8A5EA97C89EE7A6D": {
        "reason": "The article develops a theoretical chirality-selection model and compares it with reported experiments; it contains no performed CNT synthesis campaign.",
        "evidence_sections": ["Abstract", "Results and discussion", "Conclusion"],
        "pdf_pages_checked": [],
    },
    "LIT_A7F841B38540268D": {
        "reason": "The source is explicitly an overview/review of CNT synthesis, properties, and applications and reports no new performed CNT synthesis experiment.",
        "evidence_sections": ["Title page", "Abstract", "2. Synthesis of carbon nanotubes", "Conclusion"],
        "pdf_pages_checked": [1, 2],
    },
    "LIT_B6488B8B0C2B42E3": {
        "reason": "The local HTML contains an abstract and citation metadata but no full experimental section or point-resolved growth matrix, so the reported length series cannot be reconstructed safely.",
        "evidence_sections": ["Abstract", "citation metadata", "References"],
        "pdf_pages_checked": [],
    },
    "LIT_E88F2527485B87CB": {
        "reason": "The source identifies itself as a review of prior CNT growth, placement, assembly, and transistor work; its recipes summarize earlier publications rather than a new performed synthesis campaign in this source.",
        "evidence_sections": ["Abstract", "Introduction", "Placement, alignment and diameter control", "device sections"],
        "pdf_pages_checked": [1, 2, 3, 4],
    },
    "LIT_F2D0EAEF6124778C": {
        "reason": "The article is explicitly labeled 'NANO REVIEW' and reviews published PECVD CNT synthesis and plasma-modification studies; its recipes and figures are attributed to prior references rather than a new performed campaign.",
        "evidence_sections": ["title page and abstract", "review organization", "PECVD literature examples", "Conclusion and references"],
        "pdf_pages_checked": [1, 2, 9, 10],
    },
}


BLOCKED = {
    "LIT_DD8F9900B35A354B": {
        "reason": "Source identity mismatch: metadata names 'State of Transition Metal Catalysts During Carbon Nanotube Growth', but the registered local PDF is the unrelated Science article 'Single-nanowire spectrometers'. A correct source artifact is required.",
        "evidence_sections": ["registered local artifact title page", "registered local artifact page 2"],
        "pdf_pages_checked": [1, 2],
    },
    "LIT_E2B9EA84E3DC4B68": {
        "reason": "Source identity mismatch: metadata names an in-situ XPS CNT-forest study, while its registry path resolves to the same unrelated 'Single-nanowire spectrometers' PDF used by another source. A correct source artifact is required.",
        "evidence_sections": ["fulltext registry path", "resolved artifact title page", "parsed source package"],
        "pdf_pages_checked": [1, 2],
    },
}


def main() -> None:
    available = contexts()
    for source_id, builder in BUILDERS.items():
        print(builder(available[source_id]))
    for source_id, disposition in NON_EXTRACTABLE.items():
        print(
            mark_disposition(
                available[source_id],
                status="non_extractable",
                reason=disposition["reason"],
                evidence_sections=disposition["evidence_sections"],
                pdf_pages_checked=disposition["pdf_pages_checked"],
            )
        )
    for source_id, disposition in BLOCKED.items():
        print(
            mark_disposition(
                available[source_id],
                status="blocked_source_identity_mismatch",
                reason=disposition["reason"],
                evidence_sections=disposition["evidence_sections"],
                pdf_pages_checked=disposition["pdf_pages_checked"],
            )
        )


if __name__ == "__main__":
    main()
