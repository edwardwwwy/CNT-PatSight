#!/usr/bin/env python3
"""Build the eleventh evidence-grounded A-class extraction batch."""

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


BATCH_NUMBER = 11
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ID = "LIT_9A3617C1B429A8F2"


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


def append_pdf_figure_evidence(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    run_id: str,
    code: str,
    ratio: str,
) -> None:
    is_a_series = code.startswith("A")
    page = "59" if is_a_series else "78"
    figure = "3.10" if is_a_series else "3.19"
    fallback_span = (
        "SPAN_1D894C087CF30CED73C9" if is_a_series else "SPAN_A3583E91006286F8DFA8"
    )
    evidence = evidence_row(
        store,
        SOURCE_ID,
        f"EVD_{run_id}_RAMAN_FIGURE",
        run_id,
        "yield_quality",
        f"{run_id}_PROD",
        "Raman_ratio_value",
        fallback_span,
        f"Visually verified Raman D/G area ratio for recipe {code}.",
    )
    evidence.update(
        {
            "evidence_type": "pdf_figure_annotation",
            "source_section": f"Figure {figure}, combined Raman spectra",
            "source_locator": f"PDF page {page}",
            "source_object_ref": (
                f"data/raw/literature/pdf/{SOURCE_ID}_f693f3e87d7e.pdf#page={page}"
            ),
            "evidence_text": (
                f"Figure {figure} annotation for recipe {code}: R = A_D/A_G = {ratio}."
            ),
            "evidence_summary": (
                f"PDF figure annotation confirms recipe {code} "
                f"Raman D/G area ratio {ratio}."
            ),
            "notes": (
                "Value visually transcribed from the locally stored PDF figure; "
                "pending independent evidence review."
            ),
        }
    )
    tables["evidence_index"].append(evidence)


def ferritin_catalyst(run_id: str) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label=("ferritin-derived Fe nanoparticles on porous Al2O3/SiO2/Si"),
        active_metals="Fe",
        support_material="porous Al2O3 on 500 nm SiO2/Si",
        promoter="not_applicable",
        metal_ratio_original=(
            "4 nm Al buffer; ferritin solution 0.424-2.12 vol% in water"
        ),
        metal_ratio_standardized="not_applicable",
        precursor_summary=(
            "centrifuged Sigma-Aldrich ferritin solution, 0.424-2.12 vol% in water"
        ),
        preparation_method=(
            "Al_e_beam_evaporation_O2_plasma_oxidation_ferritin_spin_coating"
        ),
        preparation_modifier="UV-ozone protein-shell removal",
        preparation_detail=(
            "Deposit 4 nm Al at 8 A/s on p-type <100> Si with "
            "500 nm thermal SiO2; oxidize 10 min in 20 sccm O2 at "
            "300 W and 250 mTorr; spin-coat ferritin at 4000 rpm for 1 min."
        ),
        drying_condition="not_reported",
        calcination_condition="not_applicable",
        reduction_condition=(
            "250 sccm H2 while heating from 500 to 900 C before growth"
        ),
        activation_condition=(
            "UV-ozone at 50 C for 105 min to remove ferritin protein shell"
        ),
        post_preparation_condition="porous alumina-supported ferritin-derived Fe",
        catalyst_particle_size_mean_nm="not_reported",
        catalyst_particle_size_range_nm="not_reported",
        catalyst_particle_size_qualifier=(
            "separate-grid observation not mapped to the growth substrate"
        ),
        phase_or_state_summary="ferritin Fe core after protein-shell removal",
        dispersion_summary="ferritin deposited over porous alumina buffer",
        deactivation_summary=(
            "high-ethylene A6 showed carbon buildup and apparent poisoning"
        ),
        notes=(
            "Separate HR-TEM specimens showed ferritin particles around "
            "6-8 nm and metal cores about 6 nm, but these were on formvar/"
            "lacey-formvar grids rather than the CVD growth substrate."
        ),
    )


def iron_catalyst(run_id: str) -> dict[str, str]:
    return catalyst_row(
        run_id,
        catalyst_label="e-beam-deposited Fe film on porous Al2O3/SiO2/Si",
        active_metals="Fe",
        support_material="porous Al2O3 on 500 nm SiO2/Si",
        promoter="not_applicable",
        metal_ratio_original="15 nm Al underlayer; 1-1.5 nm Fe film",
        metal_ratio_standardized="not_applicable",
        precursor_summary="elemental Al and Fe evaporation layers",
        preparation_method=(
            "Al_e_beam_evaporation_O2_plasma_oxidation_Fe_e_beam_evaporation"
        ),
        preparation_modifier="air annealing to break Fe film into particles",
        preparation_detail=(
            "Deposit 15 nm Al at 8 A/s on p-type <100> Si with "
            "500 nm thermal SiO2; oxidize 10 min in 20 sccm O2 at "
            "300 W and 250 mTorr; deposit 1-1.5 nm Fe at about 1 A/s."
        ),
        drying_condition="not_applicable",
        calcination_condition="air, 400 C, 6 h",
        reduction_condition=(
            "250 sccm H2 while heating from 500 to 900 C before growth"
        ),
        activation_condition="air annealing broke the Fe film into particles",
        post_preparation_condition="Fe partly oxidized as Fe2O3",
        catalyst_particle_size_mean_nm="not_reported",
        catalyst_particle_size_range_nm="not_reported",
        catalyst_particle_size_qualifier="not_reported",
        phase_or_state_summary="Fe, partly oxidized as Fe2O3",
        dispersion_summary="annealed Fe particles on porous alumina",
        deactivation_summary=("high-ethylene B6 produced extensive amorphous carbon"),
    )


def process_stages(
    run_id: str,
    methane: int,
    ethylene: int,
    argon: int,
) -> list[dict[str, str]]:
    carbon_parts = []
    if methane:
        carbon_parts.append(f"CH4 {methane} sccm")
    if ethylene:
        carbon_parts.append(f"C2H4 {ethylene} sccm")
    carbon_source = "; ".join(
        gas for gas, flow in (("CH4", methane), ("C2H4", ethylene)) if flow
    )
    carbon_flow = "; ".join(carbon_parts)
    setup = (
        "EasyTube 1000 thermally driven CVD; 2 in diameter quartz-tube "
        "reactor; substrate loaded on quartz platform; gases controlled by MFC."
    )
    return [
        process_row(
            run_id,
            1,
            "argon_purge_and_heat",
            reactor_type="horizontal thermal CVD furnace",
            reactor_material="quartz tube",
            reactor_size_summary="2 in reactor-chamber diameter",
            reactor_setup_summary=setup,
            temperature_setpoint_C="500",
            temperature_program_summary=(
                "Purge with Ar while heating until 500 C and stabilization."
            ),
            holding_time_min="not_reported",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source="not_applicable",
            reducing_gas="not_applicable",
            inert_gas="Ar",
            inert_gas_flow_original="1000 sccm",
            inert_gas_flow_sccm="1000",
            total_flow_original="1000 sccm",
            total_flow_sccm="1000",
            gas_composition_summary="Ar purge",
        ),
        process_row(
            run_id,
            2,
            "hydrogen_reduction_and_heat",
            reactor_type="horizontal thermal CVD furnace",
            reactor_material="quartz tube",
            reactor_size_summary="2 in reactor-chamber diameter",
            reactor_setup_summary=setup,
            temperature_setpoint_C="900",
            temperature_range_reported_C="500-900",
            temperature_program_summary=(
                "Switch from Ar to H2 at 500 C and heat to 900 C."
            ),
            holding_time_min="not_reported",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source="not_applicable",
            reducing_gas="H2",
            reducing_gas_flow_original="250 sccm",
            reducing_gas_flow_sccm="250",
            inert_gas="not_applicable",
            total_flow_original="250 sccm",
            total_flow_sccm="250",
            gas_composition_summary="H2 catalyst reduction",
        ),
        process_row(
            run_id,
            3,
            "CNT_growth",
            reactor_type="horizontal thermal CVD furnace",
            reactor_material="quartz tube",
            reactor_size_summary="2 in reactor-chamber diameter",
            reactor_setup_summary=setup,
            temperature_setpoint_C="900",
            temperature_program_summary="isothermal CVD growth at 900 C",
            holding_time_min="15",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source=carbon_source or "not_applicable",
            carbon_source_flow_original=carbon_flow or "not_applicable",
            carbon_source_flow_sccm=(
                str(methane + ethylene) if (methane == 0 or ethylene == 0) else ""
            ),
            reducing_gas="H2",
            reducing_gas_flow_original="500 sccm",
            reducing_gas_flow_sccm="500",
            inert_gas="Ar" if argon else "not_applicable",
            inert_gas_flow_original=(f"{argon} sccm" if argon else "not_applicable"),
            inert_gas_flow_sccm=str(argon) if argon else "",
            cofeed_or_reactive_gas="not_applicable",
            total_flow_original=("not_reported; component flows retained separately"),
            total_flow_sccm="",
            gas_composition_summary=(
                f"CH4 {methane} sccm; C2H4 {ethylene} sccm; "
                f"Ar {argon} sccm; H2 500 sccm"
            ),
            process_note=(
                "Growth gas monitored by quadrupole mass spectrometry. "
                "Total flow is calculated from reported component flows."
            ),
        ),
        process_row(
            run_id,
            4,
            "argon_hydrogen_cooling",
            reactor_type="horizontal thermal CVD furnace",
            reactor_material="quartz tube",
            reactor_size_summary="2 in reactor-chamber diameter",
            reactor_setup_summary=setup,
            temperature_setpoint_C="300",
            temperature_range_reported_C="900-300",
            temperature_program_summary=(
                "After growth, cool from 900 C to 300 C under Ar/H2."
            ),
            holding_time_min="not_reported",
            cooling_condition="1000 sccm Ar and 50 sccm H2 to 300 C",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source="not_applicable",
            reducing_gas="H2",
            reducing_gas_flow_original="50 sccm",
            reducing_gas_flow_sccm="50",
            inert_gas="Ar",
            inert_gas_flow_original="1000 sccm",
            inert_gas_flow_sccm="1000",
            total_flow_original=("not_reported; component flows retained separately"),
            total_flow_sccm="",
            gas_composition_summary="Ar/H2 cooling mixture",
        ),
        process_row(
            run_id,
            5,
            "final_argon_purge",
            reactor_type="horizontal thermal CVD furnace",
            reactor_material="quartz tube",
            reactor_size_summary="2 in reactor-chamber diameter",
            reactor_setup_summary=setup,
            temperature_setpoint_C="not_reported",
            temperature_program_summary="final purge before unloading",
            holding_time_min="not_reported",
            pressure_original="not_reported",
            pressure_kPa="",
            carbon_source="not_applicable",
            reducing_gas="not_applicable",
            inert_gas="Ar",
            inert_gas_flow_original="not_reported",
            total_flow_original="not_reported",
            gas_composition_summary="Ar final purge",
        ),
    ]


def product_row(run_id: str, config: dict[str, Any]) -> dict[str, str]:
    code = str(config["code"])
    successful_swcnt = code in {"A1", "A2", "B1", "B2"}
    no_growth = code in {"A3", "B3"}
    return yield_row(
        run_id,
        primary_yield_metric="qualitative_CNT_abundance_by_SEM",
        yield_original=str(config["outcome"]),
        yield_definition_original=(
            "Qualitative substrate-surface CNT abundance and morphology by SEM; "
            "mass yield and carbon conversion were not reported."
        ),
        yield_calculation_method="qualitative microscopy characterization",
        yield_value_standardized="",
        yield_unit_standardized="not_applicable",
        secondary_result_summary=str(config["detail"]),
        CNT_type_reported=(
            "no significant CNT growth" if no_growth else "carbon nanotubes"
        ),
        CNT_type_confirmed=("SWCNTs" if successful_swcnt else "not_applicable"),
        product_mixture_summary=str(config["mixture"]),
        CNT_type_evidence=str(config["identity"]),
        SWCNT_or_few_wall_evidence_summary=(
            str(config["swcnt_evidence"])
            if successful_swcnt
            else "No run-specific SWCNT confirmation."
        ),
        RBM_peak_reported="yes" if successful_swcnt else "no",
        outer_diameter_range_nm=str(config["diameter"]),
        wall_number_summary=str(config["walls"]),
        length_summary=str(config["length"]),
        morphology=str(config["morphology"]),
        alignment_or_array="not_reported",
        Raman_ratio_type=(
            "D-band/G-band integrated-area ratio"
            if config["raman"] != "not_applicable"
            else "not_applicable"
        ),
        Raman_ratio_value=str(config["raman"]),
        Raman_laser_wavelength_nm=("532" if code.startswith("A") else "514"),
        purity_basis="not_reported",
        residue_summary=str(config["residue"]),
        amorphous_carbon_level=str(config["amorphous"]),
        characterization_methods=(
            "SEM; HR-TEM; Raman spectroscopy; QMS"
            if successful_swcnt
            else "SEM; Raman spectroscopy; QMS"
        ),
        post_treatment_or_purification="none reported",
        purification_condition="not_applicable",
        notes=(
            "Raman A4-A6 and B4-B6 ratios were visually checked on PDF "
            "figures 3.10 and 3.19. Diameter fields for A1/A2 and B1/B2 "
            "use RBM-derived SWCNT diameters; SEM/TEM bundle ranges are "
            "retained in secondary_result_summary."
        ),
    )


def cost_review(run_id: str) -> dict[str, str]:
    return cost_row(
        run_id,
        scale_level_demonstrated="lab_batch",
        scale_level_claimed="not_reported",
        scale_evidence_summary=(
            "Single substrate run in a 2 in EasyTube 1000 quartz-tube CVD "
            "reactor; no production-scale demonstration."
        ),
        reactor_capacity_or_throughput="15-min substrate growth run",
        continuous_operation_time_h="not_applicable",
        catalyst_lifetime_or_reuse="not_reported",
        batch_stability="single recipe run; repeat count not reported",
        scale_up_issue=(
            "Ferritin deposition or ultrathin Fe-film uniformity, catalyst "
            "agglomeration, gas utilization and amorphous-carbon control."
        ),
        cost_driver_summary=(
            "Si/SiO2 substrate, e-beam evaporation, O2 plasma or ferritin "
            "processing, 900 C furnace duty, H2 and hydrocarbon flow."
        ),
        safety_risk=(
            "Methane/ethylene and hydrogen at 900 C; pyrophoric or flammable "
            "gas controls and CNT nanoparticle handling are required."
        ),
        emission_or_waste=(
            "Unreacted hydrocarbon/H2 exhaust, high gas throughput, metal/"
            "substrate waste and amorphous-carbon deposits; not quantified."
        ),
        industrial_readiness_assessment=(
            "Mechanistic laboratory comparison; insufficient for scale design."
        ),
        reproduction_value="high for recipe comparison after source verification",
        reproduction_priority="high",
        recommended_next_action=(
            "Repeat recipes with quantitative carbon conversion, product mass, "
            "catalyst density and replicate statistics."
        ),
    )


CONFIGS: list[dict[str, Any]] = [
    {
        "code": "A1",
        "catalyst": "ferritin",
        "methane": 950,
        "ethylene": 20,
        "argon": 0,
        "outcome": "massive CNT growth; quantitative mass yield not reported",
        "detail": (
            "SEM CNT/bundle structures 17-26 nm; HR-TEM SWNT/bundle rough "
            "diameters 2.04-11.40 nm; RBM diameters 0.9, 1.0 and 1.3 nm."
        ),
        "mixture": "Mostly bundled SWCNTs with fullerene nanobuds.",
        "identity": "HR-TEM single walls and three fitted RBM peaks.",
        "swcnt_evidence": (
            "HR-TEM found mostly SWCNTs; RBM peaks at 188.6, 234.9 and 266.4 cm-1."
        ),
        "diameter": "0.9-1.3",
        "walls": "single-walled; bundles common",
        "length": "not quantitatively reported",
        "morphology": "straight and branched/bundle structures",
        "raman": "0.56",
        "residue": "fullerenes/nanobuds observed",
        "amorphous": "low relative to A4-A6; not quantified",
    },
    {
        "code": "A2",
        "catalyst": "ferritin",
        "methane": 850,
        "ethylene": 20,
        "argon": 0,
        "outcome": "massive CNT growth; quantitative mass yield not reported",
        "detail": (
            "SEM CNT/bundle structures 17-23 nm; HR-TEM SWNT/bundle rough "
            "diameters 2.20-11.45 nm; RBM diameters 1.0, 1.3 and 1.4 nm."
        ),
        "mixture": "Mostly bundled SWCNTs with fullerene nanobuds.",
        "identity": "HR-TEM single walls and three fitted RBM peaks.",
        "swcnt_evidence": (
            "HR-TEM found mostly SWCNTs; RBM peaks at 170.0, 188.4 and 237.8 cm-1."
        ),
        "diameter": "1.0-1.4",
        "walls": "single-walled; bundles common",
        "length": "not quantitatively reported",
        "morphology": "straight and branched/bundle structures",
        "raman": "0.41",
        "residue": "fullerenes/nanobuds observed",
        "amorphous": "low relative to A4-A6; not quantified",
    },
    {
        "code": "A3",
        "catalyst": "ferritin",
        "methane": 850,
        "ethylene": 0,
        "argon": 0,
        "outcome": "almost no CNT growth on a very clean substrate",
        "detail": "Methane-only negative-control recipe at 900 C.",
        "mixture": "No significant CNT product.",
        "identity": "SEM and Raman showed no significant CNT growth.",
        "diameter": "not_applicable",
        "walls": "not_applicable",
        "length": "not_applicable",
        "morphology": "no significant CNT morphology",
        "raman": "not_applicable",
        "residue": "not_reported",
        "amorphous": "not significant by reported SEM/Raman observations",
    },
    {
        "code": "A4",
        "catalyst": "ferritin",
        "methane": 0,
        "ethylene": 20,
        "argon": 0,
        "outcome": "CNTs grew, but less growth than mixed-feed A1/A2",
        "detail": "Low-abundance CNT growth from ethylene/H2 feed.",
        "mixture": "Defective CNT product; wall count not established.",
        "identity": "SEM CNT morphology and Raman D/G bands.",
        "diameter": "not_reported",
        "walls": "not_reported",
        "length": "not_reported",
        "morphology": "low-abundance CNT structures",
        "raman": "1.67",
        "residue": "not_reported",
        "amorphous": "high defect/disordered-carbon signal",
    },
    {
        "code": "A5",
        "catalyst": "ferritin",
        "methane": 0,
        "ethylene": 20,
        "argon": 850,
        "outcome": "CNT growth more pronounced than A4 but below A1/A2",
        "detail": "More/longer CNTs than A4 after adding 850 sccm Ar.",
        "mixture": "Defective CNT product; wall count not established.",
        "identity": "SEM CNT morphology and Raman D/G bands.",
        "diameter": "not_reported",
        "walls": "not_reported",
        "length": "longer than A4; no absolute value",
        "morphology": "moderate CNT growth",
        "raman": "1.52",
        "residue": "not_reported",
        "amorphous": "high defect/disordered-carbon signal; below A4/A6 ratio",
    },
    {
        "code": "A6",
        "catalyst": "ferritin",
        "methane": 0,
        "ethylene": 108,
        "argon": 0,
        "outcome": "short, fat CNTs with substantial amorphous carbon",
        "detail": "High ethylene caused carbon buildup and apparent poisoning.",
        "mixture": "CNTs plus extensive amorphous carbon.",
        "identity": "SEM CNT morphology and Raman D/G bands.",
        "diameter": "not_reported",
        "walls": "not_reported",
        "length": "short; no absolute value",
        "morphology": "short and fat CNTs",
        "raman": "1.65",
        "residue": "carbon buildup on catalyst/substrate",
        "amorphous": "extensive",
    },
    {
        "code": "B1",
        "catalyst": "iron",
        "methane": 650,
        "ethylene": 10,
        "argon": 0,
        "outcome": "tremendous CNT growth; quantitative mass yield not reported",
        "detail": (
            "SEM CNT/bundle structures 17-30 nm; HR-TEM SWNT/bundle rough "
            "diameters 1.6-12.8 nm; RBM diameters 1.2, 1.3 and 1.4 nm."
        ),
        "mixture": (
            "Mostly bundled SWCNTs with some double-, triple- and multi-walled "
            "CNTs and fullerene nanobuds."
        ),
        "identity": "HR-TEM single walls/multiwalls and three fitted RBM peaks.",
        "swcnt_evidence": (
            "HR-TEM found mostly SWCNTs; RBM peaks at 172.3, 180.6 and 192.8 cm-1."
        ),
        "diameter": "1.2-1.4",
        "walls": "mostly single-walled; some double/triple/multi-walled CNTs",
        "length": "not quantitatively reported",
        "morphology": "straight and branched/bundle structures",
        "raman": "0.15",
        "residue": "fullerenes/nanobuds observed",
        "amorphous": "low relative to B4-B6; not quantified",
    },
    {
        "code": "B2",
        "catalyst": "iron",
        "methane": 550,
        "ethylene": 10,
        "argon": 0,
        "outcome": "tremendous CNT growth; quantitative mass yield not reported",
        "detail": (
            "SEM CNT/bundle structures 15-24 nm; HR-TEM SWNT/bundle rough "
            "diameters 1.8-21.0 nm; RBM diameters 1.3 and 1.4 nm."
        ),
        "mixture": (
            "Mostly bundled SWCNTs with some double-, triple- and multi-walled "
            "CNTs and fullerene nanobuds."
        ),
        "identity": "HR-TEM single walls/multiwalls and two fitted RBM peaks.",
        "swcnt_evidence": (
            "HR-TEM found mostly SWCNTs; RBM peaks at 172.6 and 179.0 cm-1."
        ),
        "diameter": "1.3-1.4",
        "walls": "mostly single-walled; some double/triple/multi-walled CNTs",
        "length": "not quantitatively reported",
        "morphology": "straight and branched/bundle structures",
        "raman": "0.16",
        "residue": "fullerenes/nanobuds observed",
        "amorphous": "low relative to B4-B6; not quantified",
    },
    {
        "code": "B3",
        "catalyst": "iron",
        "methane": 550,
        "ethylene": 0,
        "argon": 0,
        "outcome": "almost no CNT growth",
        "detail": "Methane-only negative-control recipe at 900 C.",
        "mixture": "No significant CNT product.",
        "identity": "SEM and Raman showed no significant CNT growth.",
        "diameter": "not_applicable",
        "walls": "not_applicable",
        "length": "not_applicable",
        "morphology": "no significant CNT morphology",
        "raman": "not_applicable",
        "residue": "not_reported",
        "amorphous": "not significant by reported SEM/Raman observations",
    },
    {
        "code": "B4",
        "catalyst": "iron",
        "methane": 0,
        "ethylene": 10,
        "argon": 0,
        "outcome": "CNTs grew, but not in a large amount",
        "detail": "Low-abundance CNT growth from ethylene/H2 feed.",
        "mixture": "Defective CNT product; wall count not established.",
        "identity": "SEM CNT morphology and Raman D/G bands.",
        "diameter": "not_reported",
        "walls": "not_reported",
        "length": "not_reported",
        "morphology": "low-abundance CNT structures",
        "raman": "0.66",
        "residue": "not_reported",
        "amorphous": "higher defect signal than B1/B2",
    },
    {
        "code": "B5",
        "catalyst": "iron",
        "methane": 0,
        "ethylene": 10,
        "argon": 550,
        "outcome": "CNT growth more significant than B4",
        "detail": "Adding 550 sccm Ar increased CNT growth relative to B4.",
        "mixture": "Defective CNT product; wall count not established.",
        "identity": "SEM CNT morphology and Raman D/G bands.",
        "diameter": "not_reported",
        "walls": "not_reported",
        "length": "not_reported",
        "morphology": "moderate CNT growth",
        "raman": "0.35",
        "residue": "not_reported",
        "amorphous": "lower defect ratio than B4/B6",
    },
    {
        "code": "B6",
        "catalyst": "iron",
        "methane": 0,
        "ethylene": 70,
        "argon": 0,
        "outcome": "CNTs accompanied by large amounts of amorphous carbon",
        "detail": "Highest ethylene flow produced the highest Raman D/G ratio.",
        "mixture": "CNTs plus extensive amorphous carbon.",
        "identity": "SEM CNT morphology and Raman D/G bands.",
        "diameter": "not_reported",
        "walls": "not_reported",
        "length": "not_reported",
        "morphology": "CNTs embedded in disordered-carbon buildup",
        "raman": "0.92",
        "residue": "large amorphous-carbon buildup",
        "amorphous": "extensive",
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
                "Master's thesis catalyst preparation, twelve EasyTube 1000 "
                "CVD recipes A1-A6/B1-B6, SEM/HR-TEM/Raman/QMS outcomes and "
                "mechanistic comparison of methane/ethylene feeds."
            ),
        )
    )
    tables["source_master"][0]["local_file_path"] = (
        f"data/interim/parsed_text/by_source/{SOURCE_ID}.parsed.json"
    )
    tables["source_master"][0]["notes"] += (
        " PDF pages 59 and 78 were visually checked to read graph-embedded "
        "Raman D/G area ratios for A1-A6 and B1-B6."
    )

    for config in CONFIGS:
        code = str(config["code"])
        run_id = f"{SOURCE_ID}_{code}"
        gases = (
            f"CH4 {config['methane']}, C2H4 {config['ethylene']}, "
            f"Ar {config['argon']}, H2 500 sccm"
        )
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                code,
                f"Recipe {code}; {config['catalyst']} catalyst; {gases}",
                (
                    f"900 C for 15 min; {config['outcome']}; "
                    f"Raman D/G area ratio {config['raman']}."
                ),
                "high",
            )
        )
        tables["catalyst_system"].append(
            ferritin_catalyst(run_id)
            if config["catalyst"] == "ferritin"
            else iron_catalyst(run_id)
        )
        tables["reactor_process_gas"].extend(
            process_stages(
                run_id,
                int(config["methane"]),
                int(config["ethylene"]),
                int(config["argon"]),
            )
        )
        tables["yield_quality"].append(product_row(run_id, config))
        tables["cost_scale_review"].append(cost_review(run_id))

        if config["catalyst"] == "ferritin":
            append_evidence(
                tables,
                store,
                run_id,
                "CAT_PREP",
                "catalyst_system",
                f"{run_id}_CAT",
                "record_level",
                "SPAN_09CD49804D80AFD7773E",
                "Ferritin catalyst substrate, Al/O2-plasma buffer and spin coat.",
            )
            append_evidence(
                tables,
                store,
                run_id,
                "CAT_SIZE",
                "catalyst_system",
                f"{run_id}_CAT",
                "notes;catalyst_particle_size_qualifier",
                "SPAN_08B57A87206D4A8AF0AD",
                "Separate ferritin-core HR-TEM size observations.",
            )
        else:
            append_evidence(
                tables,
                store,
                run_id,
                "CAT_BUFFER",
                "catalyst_system",
                f"{run_id}_CAT",
                "support_material;metal_ratio_original;preparation_detail",
                "SPAN_96F6623FF1B1CB3D67BD",
                "Fe-catalyst SiO2/Si substrate and porous-alumina preparation.",
            )
            append_evidence(
                tables,
                store,
                run_id,
                "CAT_FE",
                "catalyst_system",
                f"{run_id}_CAT",
                "record_level",
                "SPAN_60DA37E23450F03B0091",
                "Fe-film deposition, air anneal and partial Fe2O3 state.",
            )

        common_stage_summaries = {
            1: "Common 1000 sccm Ar purge and heat to 500 C.",
            2: "Common 250 sccm H2 catalyst reduction and heat to 900 C.",
            3: "Common 900 C, 15-min CVD growth procedure.",
            4: "Common 1000 sccm Ar/50 sccm H2 cooling to 300 C.",
            5: "Common final Ar purge before sample unloading.",
        }
        for order, summary in common_stage_summaries.items():
            append_evidence(
                tables,
                store,
                run_id,
                f"COMMON_S{order:02d}",
                "reactor_process_gas",
                f"{run_id}_S{order:02d}",
                "record_level",
                "SPAN_747E0A2DC424A632EE8D",
                summary,
            )
        append_evidence(
            tables,
            store,
            run_id,
            "RECIPE_FEEDS",
            "reactor_process_gas",
            f"{run_id}_S03",
            "carbon_source;carbon_source_flow_original;reducing_gas;"
            "reducing_gas_flow_original;inert_gas;inert_gas_flow_original;"
            "gas_composition_summary",
            "SPAN_5705F697B093E974FE96",
            f"Table 2.1 component flows for recipe {code}.",
        )
        if code.startswith("A"):
            outcome_span = (
                "SPAN_C8585C2C5A755404F127"
                if code in {"A5", "A6"}
                else "SPAN_DAD8D0A7DD71FD23EF1B"
            )
            raman_span = (
                "SPAN_45F0C5A9F623CDA99B9B"
                if code == "A1"
                else (
                    "SPAN_8470E24F2446ED215B85"
                    if code == "A2"
                    else "SPAN_1D894C087CF30CED73C9"
                )
            )
        else:
            outcome_span = "SPAN_DBD7026D19FF75DB14CA"
            raman_span = (
                "SPAN_75D998030C2CC6117A1A"
                if code in {"B1", "B2"}
                else "SPAN_A3583E91006286F8DFA8"
            )
        append_evidence(
            tables,
            store,
            run_id,
            "OUTCOME",
            "yield_quality",
            f"{run_id}_PROD",
            "yield_original;secondary_result_summary;product_mixture_summary;"
            "morphology;length_summary;amorphous_carbon_level",
            outcome_span,
            f"SEM abundance/morphology outcome for recipe {code}.",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "RAMAN",
            "yield_quality",
            f"{run_id}_PROD",
            "Raman_ratio_type;RBM_peak_reported",
            raman_span,
            f"Raman identity/quality observations for recipe {code}.",
        )
        append_evidence(
            tables,
            store,
            run_id,
            "RAMAN_LASER",
            "yield_quality",
            f"{run_id}_PROD",
            "Raman_laser_wavelength_nm",
            "SPAN_295945F41D501635BDD2",
            ("A-series used 532 nm Raman excitation; B-series used 514 nm excitation."),
        )
        if config["raman"] != "not_applicable":
            append_pdf_figure_evidence(
                tables,
                store,
                run_id,
                code,
                str(config["raman"]),
            )

        if code in {"A1", "A2"}:
            append_evidence(
                tables,
                store,
                run_id,
                "SEM_DIAMETER",
                "yield_quality",
                f"{run_id}_PROD",
                "secondary_result_summary;morphology",
                "SPAN_903C8C7FA8FF183BDD6A",
                "A1/A2 SEM structure diameter and morphology comparison.",
            )
            append_evidence(
                tables,
                store,
                run_id,
                "TEM_IDENTITY",
                "yield_quality",
                f"{run_id}_PROD",
                "CNT_type_confirmed;product_mixture_summary;CNT_type_evidence",
                "SPAN_07D1ACADB6990E4176B6",
                "A1/A2 HR-TEM evidence that most observed tubes were SWCNTs.",
            )
            append_evidence(
                tables,
                store,
                run_id,
                "RBM_DIAMETER",
                "yield_quality",
                f"{run_id}_PROD",
                "SWCNT_or_few_wall_evidence_summary;outer_diameter_range_nm",
                (
                    "SPAN_45F0C5A9F623CDA99B9B"
                    if code == "A1"
                    else "SPAN_8470E24F2446ED215B85"
                ),
                f"Recipe {code} fitted RBM peaks and calculated SWCNT diameters.",
            )
        elif code in {"B1", "B2"}:
            append_evidence(
                tables,
                store,
                run_id,
                "SEM_DIAMETER",
                "yield_quality",
                f"{run_id}_PROD",
                "secondary_result_summary;morphology",
                "SPAN_C6A775EEDA9F83FE4F0F",
                "B1/B2 SEM structure diameter and morphology comparison.",
            )
            append_evidence(
                tables,
                store,
                run_id,
                "TEM_IDENTITY",
                "yield_quality",
                f"{run_id}_PROD",
                "CNT_type_confirmed;product_mixture_summary;CNT_type_evidence",
                "SPAN_E8F7CD2BE8E9824268D6",
                "B1/B2 HR-TEM SWCNT and multiwall observations.",
            )
            append_evidence(
                tables,
                store,
                run_id,
                "RBM_DIAMETER",
                "yield_quality",
                f"{run_id}_PROD",
                "SWCNT_or_few_wall_evidence_summary;outer_diameter_range_nm",
                "SPAN_75D998030C2CC6117A1A",
                f"Recipe {code} fitted RBM peaks and calculated SWCNT diameters.",
            )

        append_evidence(
            tables,
            store,
            run_id,
            "COST_REVIEW",
            "cost_scale_review",
            run_id,
            "record_level",
            "SPAN_62E36C5EB931E68D8CB6",
            "Scale/cost/safety review based on reported laboratory apparatus.",
            "review_assessment",
        )

    a1 = f"{SOURCE_ID}_A1"
    a4 = f"{SOURCE_ID}_A4"
    b1 = f"{SOURCE_ID}_B1"
    b3 = f"{SOURCE_ID}_B3"
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_001",
                SOURCE_ID,
                a1,
                "critical_data_gap",
                "yield_quality",
                f"{a1}_PROD",
                "yield_original",
                (
                    "All twelve recipes report qualitative abundance and "
                    "characterization only; no CNT mass yield, catalyst-normalized "
                    "productivity or carbon conversion is provided."
                ),
                f"EVD_{a1}_OUTCOME",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PRESSURE_001",
                SOURCE_ID,
                a1,
                "critical_data_gap",
                "reactor_process_gas",
                f"{a1}_S03",
                "pressure_original",
                (
                    "The run-specific CVD procedure does not explicitly state "
                    "operating pressure. It is retained as not_reported rather "
                    "than inferred from the thesis's general CVD discussion."
                ),
                f"EVD_{a1}_COMMON_S03",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_B_FLOW_001",
                SOURCE_ID,
                b1,
                "source_conflict",
                "reactor_process_gas",
                f"{b1}_S03",
                "carbon_source_flow_original",
                (
                    "The B1/B2 SEM-introduction sentence says 20 sccm C2H4, "
                    "but Tables 2.1 and 3.8 plus the B1/B2 TEM section consistently "
                    "state 10 sccm. The structured recipes use 10 sccm."
                ),
                f"EVD_{b1}_RECIPE_FEEDS;EVD_{b1}_SEM_DIAMETER",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_B_TEM_LABEL_001",
                SOURCE_ID,
                b1,
                "source_typographical_error",
                "yield_quality",
                f"{b1}_PROD",
                "secondary_result_summary",
                (
                    "Tables 3.6/3.7 in the B1/B2 section mistakenly call the "
                    "corresponding recipes A1/A2. Section context, figures and "
                    "feed descriptions establish that they are B1/B2."
                ),
                f"EVD_{b1}_TEM_IDENTITY",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_RAMAN_GRAPH_001",
                SOURCE_ID,
                a4,
                "figure_value_transcription",
                "yield_quality",
                f"{a4}_PROD",
                "Raman_ratio_value",
                (
                    "A4-A6 and B4-B6 D/G area ratios are graph annotations, not "
                    "repeated numerically in prose. PDF pages 59 and 78 were "
                    "visually checked; values remain pending independent evidence review."
                ),
                f"EVD_{a4}_RAMAN;EVD_{SOURCE_ID}_B4_RAMAN",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_NEGATIVE_RUN_001",
                SOURCE_ID,
                b3,
                "definition_ambiguity",
                "yield_quality",
                f"{b3}_PROD",
                "CNT_type_reported",
                (
                    "A3 and B3 are retained as explicit negative experiments "
                    "because SEM/Raman found almost no significant CNT growth."
                ),
                f"EVD_{SOURCE_ID}_A3_OUTCOME;EVD_{b3}_OUTCOME",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_PARTICLE_CONTEXT_001",
                SOURCE_ID,
                a1,
                "definition_ambiguity",
                "catalyst_system",
                f"{a1}_CAT",
                "catalyst_particle_size_qualifier",
                (
                    "Ferritin particle/core sizes were measured on separate "
                    "formvar or lacey-formvar TEM specimens, not directly on "
                    "the CVD growth substrate."
                ),
                f"EVD_{a1}_CAT_SIZE",
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
