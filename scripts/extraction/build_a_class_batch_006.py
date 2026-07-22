#!/usr/bin/env python3
"""Build the sixth evidence-grounded A-class extraction batch."""
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


BATCH_NUMBER = 6
BATCH_NAME = f"{BATCH_ID}_BATCH_{BATCH_NUMBER:03d}"
BATCH_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/A/batches" / BATCH_ID
REPORT_ROOT.mkdir(parents=True, exist_ok=True)
SOURCE_ID = "LIT_777170442739602C"

RUNS = [
    {
        "code": "R01",
        "catalyst": "NiO/alpha-Al2O3",
        "metals": "Ni",
        "ratio": "same metal:Al2O3 molar ratio as the supported controls",
        "temperature": 900,
        "yield": "13.0",
        "result": (
            "Filamentous carbon/CNCs up to 10 micrometers long and generally "
            "larger than 100 nm in diameter; amorphous carbon was also present."
        ),
        "confidence": "high",
    },
    {
        "code": "R02",
        "catalyst": "Co3O4/alpha-Al2O3",
        "metals": "Co",
        "ratio": "same metal:Al2O3 molar ratio as the supported controls",
        "temperature": 900,
        "yield": "18.3",
        "result": (
            "Multi-walled, bamboo-like CNCs with amorphous carbon present; "
            "carbon yield exceeded the Ni control."
        ),
        "confidence": "high",
    },
    {
        "code": "R03",
        "catalyst": "NiCo2O4/alpha-Al2O3",
        "metals": "Ni; Co",
        "ratio": "Ni:Co = 1:2 molar precursor ratio",
        "temperature": 800,
        "yield": "12.5",
        "raman": "1.29",
        "result": (
            "Low catalytic activity; no developed CNT forest and deposited "
            "carbon was predominantly poorly graphitized/amorphous."
        ),
        "confidence": "high",
    },
    {
        "code": "R04",
        "catalyst": "NiCo2O4/alpha-Al2O3",
        "metals": "Ni; Co",
        "ratio": "Ni:Co = 1:2 molar precursor ratio",
        "temperature": 900,
        "yield": "24.0",
        "raman": "0.55",
        "result": (
            "Dense forests of smooth, several-micrometer multi-walled "
            "bamboo-like CNCs; smaller diameter than the monometallic products."
        ),
        "confidence": "high",
    },
    {
        "code": "R05",
        "catalyst": "NiCo2O4/alpha-Al2O3",
        "metals": "Ni; Co",
        "ratio": "Ni:Co = 1:2 molar precursor ratio",
        "temperature": 950,
        "yield": "25.5",
        "raman": "0.57",
        "result": (
            "Highest carbon yield; CNC diameter decreased and length increased "
            "relative to 900 C; high-aspect-ratio multi-walled bamboo-like CNCs."
        ),
        "confidence": "high",
    },
    {
        "code": "R06",
        "catalyst": "NiCo2O4/alpha-Al2O3",
        "metals": "Ni; Co",
        "ratio": "Ni:Co = 1:2 molar precursor ratio",
        "temperature": 1000,
        "yield": "7.5",
        "raman": "0.74",
        "result": (
            "Catalyst sintering/deactivation; dense forest disappeared and only "
            "a few small-aspect-ratio CNCs/CNC embryos remained in amorphous carbon."
        ),
        "confidence": "high",
    },
]


def add_observation(
    tables: dict[str, list[dict[str, str]]],
    store: EvidenceStore,
    suffix: str,
    span_id: str,
    summary: str,
) -> str:
    evidence_id = f"EVD_{SOURCE_ID}_OBS_{suffix}"
    item = evidence_row(
        store,
        SOURCE_ID,
        evidence_id,
        "not_applicable",
        "source_master",
        SOURCE_ID,
        "source_section_scope",
        span_id,
        summary,
    )
    item["evidence_type"] = "source_observation"
    tables["evidence_index"].append(item)
    return evidence_id


def yield_span(run: dict[str, Any]) -> str:
    if run["code"] in {"R01", "R02", "R04"}:
        return "SPAN_5D5E8FDE38E48CE834B5"
    if run["code"] == "R03":
        return "SPAN_E38E04D397B9C0622A24"
    if run["code"] == "R05":
        return "SPAN_08F503CCAE9BEBB1AD36"
    return "SPAN_AEBCF2C747F7A299EC22"


def morphology_span(run: dict[str, Any]) -> str:
    if run["code"] == "R01":
        return "SPAN_F17B825D5EB660A0A451"
    if run["code"] in {"R02", "R04"}:
        return "SPAN_48A649B5C4B87CFAD97E"
    if run["code"] in {"R03", "R05"}:
        return "SPAN_08F503CCAE9BEBB1AD36"
    return "SPAN_534AF4CE1A4FDD974DF9"


def build(
    metadata: dict[str, Any],
    store: EvidenceStore,
) -> dict[str, list[dict[str, str]]]:
    tables = {name: [] for name in TABLES}
    tables["source_master"].append(
        master_row(
            metadata,
            (
                "Hydrothermal catalyst preparation; two-stage waste-polyethylene "
                "pyrolysis/catalysis; catalyst-composition and temperature series; "
                "TPO, Raman, SEM and TEM product evidence."
            ),
        )
    )
    tables["source_master"][0]["local_file_path"] = (
        f"data/interim/parsed_text/by_source/{SOURCE_ID}.parsed.json"
    )

    for run in RUNS:
        run_id = f"{SOURCE_ID}_{run['code']}"
        temperature = int(run["temperature"])
        bimetallic = run["metals"] == "Ni; Co"
        tables["source_run"].append(
            run_row(
                SOURCE_ID,
                str(run["code"]),
                (
                    f"{run['catalyst']} / waste polyethylene / "
                    f"{temperature} C catalysis"
                ),
                (
                    f"Two-stage catalytic pyrolysis of 4 g post-consumer "
                    f"polyethylene over 1 g {run['catalyst']}; {run['result']}"
                ),
                str(run["confidence"]),
            )
        )
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                catalyst_label=str(run["catalyst"]),
                active_metals=str(run["metals"]),
                support_material="alpha-Al2O3",
                promoter="not_applicable",
                metal_ratio_original=str(run["ratio"]),
                metal_ratio_standardized=(
                    "Ni:Co = 1:2 molar"
                    if bimetallic
                    else "not_reported for monometallic control"
                ),
                precursor_summary=(
                    "Ni(NO3)2·6H2O; Co(NO3)2·6H2O; urea; alpha-Al2O3"
                    if bimetallic
                    else (
                        "Ni(NO3)2·6H2O; urea; alpha-Al2O3"
                        if run["metals"] == "Ni"
                        else "Co(NO3)2·6H2O; urea; alpha-Al2O3"
                    )
                ),
                preparation_method="hydrothermal",
                preparation_modifier="urea_assisted; ball_milling",
                preparation_detail=(
                    "Metal nitrate(s) and urea were dissolved in 30 mL DI water; "
                    "0.72 g alpha-Al2O3 was added, hydrothermally treated at "
                    "120 C for 8 h, centrifuged, freeze-dried, ball-milled for "
                    "10 h at 300 rpm, and annealed."
                ),
                drying_condition="freeze-dried after centrifugation",
                calcination_condition="annealed at 700 C for 2 h in air",
                reduction_condition=(
                    "in-situ reduction by plastic-derived reducing gases during catalysis"
                ),
                activation_condition="not_separately_reported",
                phase_or_state_summary=(
                    "supported NiCo2O4 spinel before reaction"
                    if bimetallic
                    else "supported monometallic oxide control"
                ),
                dispersion_summary="alpha-Al2O3 support used to limit catalyst agglomeration",
                deactivation_summary=(
                    "metal-particle sintering at 1000 C"
                    if temperature == 1000
                    else "not_reported"
                ),
            )
        )
        common_setup = (
            "Modified two-stage system with connected Al2O3 tube furnaces: "
            "plastic in the pyrolysis furnace and catalyst on an Al2O3 bed "
            "in the catalytic furnace."
        )
        tables["reactor_process_gas"].extend(
            [
                process_row(
                    run_id,
                    1,
                    "plastic_pyrolysis",
                    reactor_type="modified two-stage tube-furnace reactor",
                    reactor_material="Al2O3 tubes and crucible",
                    reactor_setup_summary=common_setup,
                    catalyst_loading_mass_g="not_applicable",
                    temperature_setpoint_C="800",
                    temperature_program_summary=(
                        "4 g polyethylene heated from 50 C to 800 C at "
                        "200 C/h and held at 800 C for 1 h."
                    ),
                    holding_time_min="60",
                    pressure_original="not_reported",
                    pressure_kPa="not_reported",
                    carbon_source="post-consumer polyethylene",
                    carbon_source_flow_original="4 g solid plastic batch",
                    cofeed_or_reactive_gas="Air (as printed in the source)",
                    cofeed_flow_original="not_reported",
                    gas_composition_summary="Air atmosphere reported; no flow rate given",
                ),
                process_row(
                    run_id,
                    2,
                    "catalytic_CNC_growth",
                    reactor_type="modified two-stage tube-furnace reactor",
                    reactor_material="Al2O3 tube; Al2O3 catalyst bed",
                    reactor_setup_summary=common_setup,
                    catalyst_loading_mass_g="1",
                    temperature_setpoint_C=str(temperature),
                    temperature_program_summary=(
                        "Catalytic furnace preheated to the selected setpoint "
                        "before plastic heating."
                    ),
                    holding_time_min="60",
                    pressure_original="not_reported",
                    pressure_kPa="not_reported",
                    carbon_source="post-consumer polyethylene pyrolysis vapours",
                    carbon_source_flow_original="vapours from 4 g plastic batch",
                    cofeed_or_reactive_gas="Air (as printed in the source)",
                    cofeed_flow_original="not_reported",
                    gas_composition_summary=(
                        "Plastic-derived vapours in reported Air atmosphere; "
                        "gas flow not reported"
                    ),
                ),
            ]
        )
        mixture = str(run["result"])
        if run["code"] in {"R03", "R06"}:
            cnt_confirmed = "mixed/limited CNT evidence"
        else:
            cnt_confirmed = "MWCNT composites"
        tables["yield_quality"].append(
            yield_row(
                run_id,
                primary_yield_metric="carbon_deposit_yield_per_plastic_feed",
                yield_original=f"{run['yield']} wt.% carbon yield",
                yield_definition_original=(
                    "(mass of carbon-deposited catalyst minus fresh catalyst "
                    "mass) divided by plastic feed mass"
                ),
                yield_calculation_method="reported Equation (1), gravimetric",
                yield_value_standardized=str(run["yield"]),
                yield_unit_standardized="wt.% of plastic feed",
                yield_standardization_note=(
                    "This is total deposited-carbon yield, not isolated CNT yield."
                ),
                secondary_result_summary=mixture,
                CNT_type_reported="multi-walled carbon nanotube composites",
                CNT_type_confirmed=cnt_confirmed,
                product_mixture_summary=(
                    f"{mixture} Yield includes graphitic and amorphous carbon "
                    "deposited with the catalyst."
                ),
                CNT_type_evidence="SEM and TEM; source conclusion reports multi-walled bamboo-like CNCs.",
                length_summary=(
                    "up to 10 micrometers"
                    if run["code"] == "R01"
                    else (
                        "several micrometers"
                        if run["code"] == "R04"
                        else "qualitative only"
                    )
                ),
                outer_diameter_range_nm=(
                    ">100" if run["code"] == "R01" else "not_reported"
                ),
                wall_number_summary="multi-walled",
                morphology="bamboo-like CNCs; particle-wire-tube growth mechanism",
                alignment_or_array=(
                    "dense CNC forest"
                    if run["code"] == "R04"
                    else (
                        "forest absent/poorly developed"
                        if run["code"] in {"R03", "R06"}
                        else "not_reported"
                    )
                ),
                Raman_ratio_type="ID/IG" if run.get("raman") else "not_reported",
                Raman_ratio_value=str(run.get("raman") or "not_reported"),
                Raman_laser_wavelength_nm="514.5",
                purity_basis="TPO/DTA and Raman describe mixed deposited carbon",
                amorphous_carbon_level=(
                    "predominant"
                    if run["code"] in {"R03", "R06"}
                    else "present"
                ),
                characterization_methods="SEM; TEM; Raman; TPO/TGA; DTA; XRD",
                post_treatment_or_purification="none reported",
                purification_condition="not_applicable",
            )
        )
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                reactor_capacity_or_throughput="4 g plastic; 1 g catalyst per batch; 1 h hold",
                continuous_operation_time_h="not_applicable",
                catalyst_lifetime_or_reuse="not_reported",
                batch_stability="single laboratory batch per condition",
                scale_up_issue=(
                    "Catalyst agglomeration/sintering limits CNT formation; "
                    "no continuous-feed or reuse demonstration."
                ),
                cost_driver_summary=(
                    "Waste polyethylene feed and oxide catalyst route; "
                    "no quantitative catalyst, energy or purification cost."
                ),
                safety_risk=(
                    "High-temperature plastic pyrolysis; the paper prints Air "
                    "atmosphere but gives no flow or off-gas treatment details."
                ),
                emission_or_waste="Plastic-derived gases and mixed deposited carbon; not quantified.",
            )
        )

        cat_span = "SPAN_37CBEDC312E0AE6F1083"
        if not bimetallic:
            cat_span = "SPAN_1A63C18316140468C822"
        evidence_specs = [
            (
                "CAT",
                "catalyst_system",
                f"{run_id}_CAT",
                (
                    "catalyst_label;active_metals;support_material;promoter;"
                    "metal_ratio_original;metal_ratio_standardized;precursor_summary;"
                    "preparation_method;preparation_modifier;preparation_detail;"
                    "drying_condition;calcination_condition;phase_or_state_summary"
                ),
                cat_span,
                "Catalyst identity and preparation.",
            ),
            (
                "PYROLYSIS",
                "reactor_process_gas",
                f"{run_id}_S01",
                (
                    "reactor_type;reactor_material;reactor_setup_summary;"
                    "temperature_setpoint_C;temperature_program_summary;"
                    "holding_time_min;carbon_source;carbon_source_flow_original;"
                    "cofeed_or_reactive_gas;gas_composition_summary"
                ),
                "SPAN_5EEC626E7BD279AB7455",
                "Two-stage setup and plastic-pyrolysis program.",
            ),
            (
                "GROWTH",
                "reactor_process_gas",
                f"{run_id}_S02",
                (
                    "reactor_type;reactor_material;reactor_setup_summary;"
                    "catalyst_loading_mass_g;temperature_setpoint_C;"
                    "temperature_program_summary;holding_time_min;carbon_source;"
                    "carbon_source_flow_original;cofeed_or_reactive_gas;"
                    "gas_composition_summary"
                ),
                "SPAN_5EEC626E7BD279AB7455",
                "Catalyst loading and selected catalytic temperature.",
            ),
            (
                "YIELD",
                "yield_quality",
                f"{run_id}_PROD",
                (
                    "primary_yield_metric;yield_original;yield_value_standardized;"
                    "yield_unit_standardized;secondary_result_summary;"
                    "product_mixture_summary;amorphous_carbon_level"
                ),
                yield_span(run),
                "Run-specific carbon yield and product-quality trend.",
            ),
            (
                "YIELD_BASIS",
                "yield_quality",
                f"{run_id}_PROD",
                (
                    "yield_definition_original;yield_calculation_method;"
                    "yield_standardization_note;Raman_laser_wavelength_nm;"
                    "characterization_methods"
                ),
                "SPAN_D9E07981B94CD1488855",
                "Carbon-yield equation and Raman method.",
            ),
            (
                "MORPHOLOGY",
                "yield_quality",
                f"{run_id}_PROD",
                (
                    "CNT_type_reported;CNT_type_confirmed;CNT_type_evidence;"
                    "length_summary;outer_diameter_range_nm;wall_number_summary;"
                    "morphology;alignment_or_array"
                ),
                morphology_span(run),
                "Microscopy-based product identity and morphology.",
            ),
            (
                "CONCLUSION",
                "yield_quality",
                f"{run_id}_PROD",
                "CNT_type_reported;wall_number_summary;morphology",
                "SPAN_B1A98006E76E1AFBC577",
                "Multi-walled bamboo-like identity and growth mechanism.",
            ),
            (
                "SCALE",
                "cost_scale_review",
                run_id,
                (
                    "scale_level_demonstrated;reactor_capacity_or_throughput;"
                    "batch_stability;scale_up_issue;cost_driver_summary;"
                    "safety_risk;emission_or_waste"
                ),
                "SPAN_5EEC626E7BD279AB7455",
                "Laboratory batch mass, duration, reactor and atmosphere.",
            ),
        ]
        if run.get("raman"):
            evidence_specs.append(
                (
                    "RAMAN",
                    "yield_quality",
                    f"{run_id}_PROD",
                    "Raman_ratio_type;Raman_ratio_value;Raman_laser_wavelength_nm",
                    "SPAN_584F6CCC96136DB7AA28",
                    "Temperature-specific ID/IG values and Raman method.",
                )
            )
        for suffix, table, record_id, fields, span_id, summary in evidence_specs:
            evidence = evidence_row(
                store,
                SOURCE_ID,
                f"EVD_{run_id}_{suffix}",
                run_id,
                table,
                record_id,
                fields,
                span_id,
                summary,
            )
            if suffix == "RAMAN":
                raman_sentences = {
                    "R03": (
                        "At 800 C, the ID/IG value was 1.29, indicating poor "
                        "graphitization degree."
                    ),
                    "R04": (
                        "At 900 C, the ID/IG value reached 0.55, indicating "
                        "improved graphitization."
                    ),
                    "R05": (
                        "At 950 C, the ID/IG value reached 0.57, indicating "
                        "improved graphitization."
                    ),
                    "R06": (
                        "At 1000 C, the ID/IG value increased to 0.74, "
                        "indicating decreased graphitization degree."
                    ),
                }
                evidence["evidence_text"] = raman_sentences[str(run["code"])]
                evidence["notes"] = (
                    "Faithful normalized transcription of the local parsed-text "
                    "sentence; the candidate span has duplicated character-level "
                    "PDF extraction artifacts."
                )
            tables["evidence_index"].append(evidence)

    unsupported = add_observation(
        tables,
        store,
        "UNSUPPORTED_NICO_FAILURE",
        "SPAN_3006C45CD1CE364B6EDB",
        (
            "Unsupported NiCo2O4 collapsed and agglomerated during CVD; most "
            "deposited carbon did not form CNTs, with only one sub-micrometer "
            "tube observed and catalyst particles larger than 200 nm."
        ),
    )
    unsupported_tpo = add_observation(
        tables,
        store,
        "UNSUPPORTED_NICO_TPO",
        "SPAN_CC6FDF1995B64CE5A0A1",
        (
            "The unsupported NiCo material showed about 76 wt.% TPO loss, but "
            "this is mixed deposited carbon and is not an isolated CNT yield."
        ),
    )
    first_run = f"{SOURCE_ID}_R01"
    tables["review_issue_log"].extend(
        [
            issue_row(
                f"{SOURCE_ID}_ISSUE_ATMOSPHERE_001",
                SOURCE_ID,
                first_run,
                "source_conflict",
                "reactor_process_gas",
                f"{first_run}_S01",
                "cofeed_or_reactive_gas",
                (
                    "The experimental section explicitly prints 'Air atmosphere', "
                    "which is unusual for plastic-pyrolysis CNT growth and no flow "
                    "rate is supplied. Verify against the PDF/typesetting or authors."
                ),
                f"EVD_{first_run}_PYROLYSIS",
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_YIELD_BASIS_001",
                SOURCE_ID,
                f"{SOURCE_ID}_R05",
                "definition_ambiguity",
                "yield_quality",
                f"{SOURCE_ID}_R05_PROD",
                "yield_original",
                (
                    "Reported yield is total carbon deposited per plastic feed, "
                    "including amorphous/graphitic carbon and catalyst-associated "
                    "material; it must not be interpreted as purified CNT yield."
                ),
                (
                    f"EVD_{SOURCE_ID}_R05_YIELD;"
                    f"EVD_{SOURCE_ID}_R05_YIELD_BASIS"
                ),
                "high",
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_DUPLICATE_900_001",
                SOURCE_ID,
                f"{SOURCE_ID}_R04",
                "run_split_uncertainty",
                "source_run",
                f"{SOURCE_ID}_R04",
                "run_summary",
                (
                    "The NiCo/alpha-Al2O3 900 C condition appears in both the "
                    "catalyst-composition and temperature comparisons. It is "
                    "represented once as one physical condition."
                ),
                (
                    f"EVD_{SOURCE_ID}_R04_YIELD;"
                    f"EVD_{SOURCE_ID}_R04_GROWTH"
                ),
            ),
            issue_row(
                f"{SOURCE_ID}_ISSUE_UNSUPPORTED_001",
                SOURCE_ID,
                first_run,
                "critical_data_gap",
                "source_run",
                first_run,
                "run_summary",
                (
                    "The unsupported NiCo2O4 failure experiment has direct "
                    "microscopy/TPO results but the local text does not identify a "
                    "complete distinct reaction program. It is retained as source "
                    "observation rather than a fabricated formal run."
                ),
                f"{unsupported};{unsupported_tpo}",
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
