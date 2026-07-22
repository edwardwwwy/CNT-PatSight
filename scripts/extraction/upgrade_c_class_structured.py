#!/usr/bin/env python3
"""Upgrade C-class placeholder ledgers to source-grounded eight-table records.

The extractor deliberately treats each unique, parser-selected evidence block
as an independent reported condition.  It never joins facts across blocks.
For review articles this produces ``literature_reported_condition`` rows,
making the secondary nature of the evidence explicit.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import io
import json
import re
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.extraction.batch_common import (
    ROOT,
    TABLES,
    EvidenceStore,
    catalyst_row,
    cost_row,
    evidence_row,
    issue_row,
    process_row,
    row,
    run_row,
    write_table,
    yield_row,
)
from scripts.extraction.package_io import write_extraction_package
from scripts.validation.validate_tables import DEFAULT_DICTIONARY, DEFAULT_SCHEMA, validate


BATCH_ID = "C_CLASS_450_20260720"
CLASS_ROOT = ROOT / "data/interim/extraction/C"
PACKAGE_ROOT = CLASS_ROOT
ARCHIVE_ROOT = ROOT / "runs/extraction/C/superseded" / BATCH_ID
REPORT_ROOT = ROOT / "runs/extraction/C/structured_batches" / BATCH_ID
META_DB = ROOT / "data/raw/literature/metadata/literature.sqlite3"
CANDIDATE_DB = ROOT / "cache/databases/extraction_candidates.sqlite3"

METALS = (
    "Fe", "Co", "Ni", "Mo", "Cu", "Mn", "Ru", "Pt", "Pd", "Cr", "Au",
    "Ag", "V", "W",
)
SUPPORTS = (
    "Al2O3", "MgO", "SiO2", "TiO2", "ZrO2", "CeO2", "CaO", "ZnO",
    "ZSM-5", "HZSM-5", "MCM-41", "SBA-15", "activated carbon",
    "stainless steel", "quartz", "zeolite",
)
CARBON_SOURCES = (
    "methane", "acetylene", "ethylene", "ethane", "propane", "benzene",
    "toluene", "xylene", "hexane", "cyclohexane", "natural gas", "coal gas",
    "carbon monoxide", "CO", "polyethylene", "HDPE", "LDPE", "polypropylene",
    "PP", "polystyrene", "PS", "PET", "PVC", "plastic", "waste oil",
    "engine oil", "kerosene", "diesel", "LPG", "biogas",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean(text: Any) -> str:
    return " ".join(str(text or "").replace("\u00ad", "").split())


def first_match(pattern: str, text: str, flags: int = re.I) -> str:
    match = re.search(pattern, text, flags)
    return clean(match.group(1)) if match else ""


def all_matches(pattern: str, text: str, flags: int = re.I) -> list[str]:
    return list(dict.fromkeys(clean(item) for item in re.findall(pattern, text, flags)))


def source_metadata(source_id: str) -> dict[str, Any]:
    with sqlite3.connect(META_DB) as connection:
        connection.row_factory = sqlite3.Row
        result = connection.execute("SELECT * FROM works WHERE source_id = ?", (source_id,)).fetchone()
    if result is None:
        raise KeyError(f"Unknown source_id: {source_id}")
    return dict(result)


def candidate_spans(source_id: str) -> list[dict[str, Any]]:
    with sqlite3.connect(CANDIDATE_DB) as connection:
        connection.row_factory = sqlite3.Row
        return [
            dict(item)
            for item in connection.execute(
                """
                SELECT s.*, p.section_name_raw, p.section_name_normalized
                FROM candidate_experiment_span AS s
                LEFT JOIN paper_text_section AS p ON p.section_id = s.section_id
                WHERE s.source_id = ?
                ORDER BY s.page_range, s.span_id
                """,
                (source_id,),
            )
        ]


def fact_score(text: str) -> int:
    patterns = (
        r"\b(?:CNTs?|carbon nanotubes?|MWCNTs?|SWCNTs?)\b",
        r"\b(?:catalyst|CVD|CCVD|pyrolysis|decomposition|reactor)\b",
        r"\b\d+(?:\.\d+)?\s*(?:°\s*)?C\b",
        r"\b\d+(?:\.\d+)?\s*(?:wt\.?\s*%|%|g\s*/\s*100\s*g|g/g|nm|h|min)\b",
        r"\b(?:yield|conversion|purity|diameter|length|productivity)\b",
        r"\b(?:Fe|Co|Ni|Mo|Cu|Mn|Ru|Pt|Pd|Cr)(?:\b|[-/])",
        r"\b(?:methane|acetylene|ethylene|plastic|polyethylene|polypropylene|HDPE|LDPE|PP|PS|PET|PVC)\b",
    )
    return sum(bool(re.search(pattern, text, re.I)) for pattern in patterns)


def select_blocks(spans: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return unique evidence blocks with enough scientific content to structure."""
    unique: dict[str, dict[str, Any]] = {}
    for span in spans:
        text = clean(span.get("text"))
        section = clean(span.get("section_name_raw") or span.get("section_name_normalized"))
        if len(text) < 80 or re.search(r"\b(references|bibliography)\b", section, re.I):
            continue
        key = re.sub(r"\W+", "", text).lower()
        current = unique.get(key)
        if current is None or float(span.get("confidence_score") or 0) > float(current.get("confidence_score") or 0):
            unique[key] = span
    ranked = sorted(
        unique.values(),
        key=lambda item: (-fact_score(clean(item.get("text"))), str(item.get("page_range") or ""), str(item.get("span_id"))),
    )
    selected = [item for item in ranked if fact_score(clean(item.get("text"))) >= 4]
    if not selected and ranked:
        selected = ranked[:1]
    return selected


def metal_summary(text: str) -> str:
    found = [metal for metal in METALS if re.search(rf"(?<![A-Za-z]){re.escape(metal)}(?![a-z])", text)]
    return "; ".join(dict.fromkeys(found)) or "not_reported"


def support_summary(text: str) -> str:
    normalized = text.replace(" ", "")
    found = []
    for support in SUPPORTS:
        if support.lower().replace(" ", "") in normalized.lower():
            found.append(support)
    if re.search(r"(?:supported\s+on|carbon[- ]supported|/)\s*(?:CNTs?|carbon)\b", text, re.I):
        found.append("CNT/carbon support")
    return "; ".join(dict.fromkeys(found)) or "not_reported"


def carbon_source_summary(text: str) -> str:
    found = [item for item in CARBON_SOURCES if item != "CO" and re.search(rf"(?<![A-Za-z]){re.escape(item)}(?![A-Za-z])", text, re.I)]
    return "; ".join(dict.fromkeys(found)) or "not_reported"


def temperature_values(text: str) -> list[str]:
    values = all_matches(r"(\d+(?:\.\d+)?(?:\s*[–-]\s*\d+(?:\.\d+)?)?\s*(?:°\s*)?C)\b", text)
    kept = []
    for value in values:
        first_number = float(re.search(r"\d+(?:\.\d+)?", value).group())
        if "°" in value or first_number >= 100:
            kept.append(value)
    return kept


def duration_values(text: str) -> list[str]:
    return all_matches(r"(\d+(?:\.\d+)?(?:\s*[–-]\s*\d+(?:\.\d+)?)?\s*(?:h|hours?|min|minutes?))\b", text)


def method_value(text: str) -> str:
    methods = []
    for label, pattern in (
        ("chemical_vapor_deposition", r"\b(?:CVD|CCVD|chemical vapou?r deposition)\b"),
        ("pyrolysis_catalysis", r"\bpyrolys(?:is|ed)\b"),
        ("catalytic_methane_decomposition", r"\b(?:CMD|methane decomposition)\b"),
        ("arc_discharge", r"\barc discharge\b"),
    ):
        if re.search(pattern, text, re.I):
            methods.append(label)
    return "; ".join(methods) or "not_reported"


def reactor_value(text: str) -> str:
    reactors = []
    for label, pattern in (
        ("fluidized_bed", r"fluidi[sz]ed[- ]bed"),
        ("fixed_bed", r"fixed[- ]bed"),
        ("two_stage_quartz", r"two[- ]stage.{0,40}quartz"),
        ("two_stage", r"two[- ]stage"),
        ("quartz_tube", r"quartz (?:tube|reactor)"),
        ("tubular_reactor", r"tubular reactor"),
        ("autoclave", r"autoclave"),
    ):
        if re.search(pattern, text, re.I | re.S):
            reactors.append(label)
    return "; ".join(reactors) or "not_reported"


def gas_values(text: str) -> tuple[str, str, str, str]:
    hydrogen = "H2" if re.search(r"\b(?:H2|hydrogen)\b", text, re.I) else "not_reported"
    inert = []
    if re.search(r"\b(?:N2|nitrogen)\b", text, re.I):
        inert.append("N2")
    if re.search(r"\b(?:Ar|argon)\b", text, re.I):
        inert.append("Ar")
    cofeed = []
    if re.search(r"\b(?:steam|water input|H2O)\b", text, re.I):
        cofeed.append("steam")
    if re.search(r"\boxygen\b|\bO2\b", text, re.I):
        cofeed.append("O2")
    gas_summary = "; ".join(item for item in (hydrogen if hydrogen != "not_reported" else "", *inert, *cofeed) if item)
    return hydrogen, "; ".join(inert) or "not_reported", "; ".join(cofeed) or "not_reported", gas_summary or "not_reported"


def yield_values(text: str) -> dict[str, str]:
    contextual_yields = []
    for pattern in (
        r"(?:CNT|carbon|hydrogen|H2|product)\s*yield(?:s|ed)?(?:\s+of|\s+was|\s+were|\s+at|\s*=)?\s*(\d+(?:\.\d+)?\s*(?:wt\.?\s*)?%)",
        r"yield(?:s|ed)?[^.;]{0,35}?(\d+(?:\.\d+)?\s*(?:wt\.?\s*)?%)",
        r"(\d+(?:\.\d+)?\s*wt\.?\s*%)\s+(?:of\s+)?(?:carbon\s+nanotubes?|CNTs?)",
    ):
        contextual_yields.extend(all_matches(pattern, text))
    mass_yields = all_matches(r"(\d+(?:\.\d+)?\s*g\s*(?:H2|H₂)?\s*(?:per|/)\s*100\s*g(?:\s+(?:plastic|feed))?)", text)
    conversion = first_match(r"(?:methane|plastic|carbon source)?\s*conversion(?:\s+of)?\s*(\d+(?:\.\d+)?\s*%)", text)
    purity = first_match(r"(?:CNT\s*)?purit(?:y|ies)(?:\s+of|\s+more than|\s+exceeding)?\s*(\d+(?:\.\d+)?\s*%)", text)
    diameter = first_match(r"(?:diameters?|diameter)\s*(?:of|were|was|between|ranged?\s+from|=|:)??\s*(\d+(?:\.\d+)?(?:\s*(?:and|to|–|-)\s*\d+(?:\.\d+)?)?\s*nm)", text)
    length = first_match(r"(?:lengths?|length)\s*(?:of|were|was|between|ranged?\s+from|=|:)??\s*(\d+(?:\.\d+)?(?:\s*(?:and|to|–|-)\s*\d+(?:\.\d+)?)?\s*(?:nm|µm|um|mm))", text)
    cnt_type = []
    for label, pattern in (("SWCNT", r"\bSWCNTs?\b|single[- ]walled"), ("MWCNT", r"\bMWCNTs?\b|multi[- ]walled"), ("CNT", r"\bCNTs?\b|carbon nanotubes?")):
        if re.search(pattern, text, re.I):
            cnt_type.append(label)
    if "SWCNT" in cnt_type or "MWCNT" in cnt_type:
        cnt_type = [item for item in cnt_type if item != "CNT"]
    reported = list(dict.fromkeys(mass_yields + contextual_yields))
    return {
        "yield_original": "; ".join(reported) or "not_reported",
        "conversion": conversion or "",
        "purity": purity or "",
        "diameter": diameter or "",
        "length": length or "not_reported",
        "cnt_type": "; ".join(cnt_type) or "not_reported",
    }


def make_master(meta: dict[str, Any], block_count: int) -> dict[str, str]:
    local_path = f"data/interim/parsed_text/by_source/{meta['source_id']}.parsed.json"
    return row(
        "source_master",
        source_id=meta["source_id"],
        source_type=meta.get("source_type") or "paper",
        source_title=meta.get("title") or meta["source_id"],
        publication_year=meta.get("year") or "not_reported",
        authors_or_assignee=meta.get("authors") or "not_reported",
        publication_venue=meta.get("journal") or "not_reported",
        doi_or_patent_no=meta.get("doi") or "not_reported",
        source_link=meta.get("source_link") or "not_reported",
        source_database="local_metadata_registry",
        source_language=meta.get("language") or "not_reported",
        local_file_path=local_path,
        pdf_status=meta.get("pdf_status") or "local_parsed_text",
        screening_class="candidate_extract",
        source_section_scope=f"{block_count} unique source-grounded condition blocks structured without cross-block joins.",
        extraction_status="needs_review",
        review_status="pending_review",
        notes="C class; automated source-grounded eight-table extraction; no placeholder ledger; domain_expert_verified=false.",
    )


def build_tables(meta: dict[str, Any], spans: list[dict[str, Any]], store: EvidenceStore) -> dict[str, list[dict[str, str]]]:
    source_id = str(meta["source_id"])
    blocks = select_blocks(spans)
    if not blocks:
        raise ValueError(f"No source-grounded condition block available for {source_id}")
    title = clean(meta.get("title"))
    lead_text = " ".join(clean(item.get("text"))[:500] for item in blocks[:3])
    is_review = bool(re.search(r"\breview\b|\brecent advances\b|\breported (?:on|that)\b", title + " " + lead_text, re.I))
    data_type = "literature_reported_condition" if is_review else "experimental_condition_block"
    tables: dict[str, list[dict[str, str]]] = {name: [] for name in TABLES}
    tables["source_master"].append(make_master(meta, len(blocks)))

    for index, block in enumerate(blocks, start=1):
        text = clean(block.get("text"))
        digest = hashlib.sha1(str(block["span_id"]).encode("utf-8")).hexdigest()[:8].upper()
        code = f"R{index:03d}_{digest}"
        run_id = f"{source_id}_{code}"
        run = run_row(
            source_id,
            code,
            f"Reported condition block {index:03d}",
            text[:480],
            "medium" if is_review else "high",
        )
        run["data_type"] = data_type
        run["relevance_class"] = "C"
        run["notes"] = "Independent source block; facts were not joined with another block."
        tables["source_run"].append(run)

        temps = temperature_values(text)
        durations = duration_values(text)
        reducing, inert, cofeed, gas_summary = gas_values(text)
        yields = yield_values(text)
        active_metals = metal_summary(text)
        support = support_summary(text)
        method = method_value(text)
        reactor = reactor_value(text)
        carbon_source = carbon_source_summary(text)

        catalyst_id = f"{run_id}_CAT"
        loading = first_match(r"(\d+(?:\.\d+)?\s*wt\.?\s*%)", text)
        preparation = first_match(r"\b(impregnation|co-precipitation|coprecipitation|sol-gel|Stöber|hydrothermal|calcination)\b", text)
        reduction = first_match(r"(?:pre-?reduced|reduced|reduction)(?:\s+at|\s+in)?\s*([^.;]{0,80})", text)
        tables["catalyst_system"].append(
            catalyst_row(
                run_id,
                catalyst_id=catalyst_id,
                catalyst_label=f"{active_metals} on {support}" if support != "not_reported" else active_metals,
                active_metals=active_metals,
                support_material=support,
                metal_ratio_original=loading or "not_reported",
                preparation_method=preparation or "not_reported",
                preparation_detail=text[:320] if any(item != "not_reported" for item in (active_metals, support, preparation or "not_reported")) else "not_reported",
                reduction_condition=reduction or "not_reported",
                deactivation_summary="sintering mentioned" if re.search(r"sinter", text, re.I) else "not_reported",
                notes="Values reported in this evidence block only.",
            )
        )

        stage_id = f"{run_id}_S01"
        pressure = first_match(r"(\d+(?:\.\d+)?\s*(?:atm|bar|kPa|MPa))", text)
        tables["reactor_process_gas"].append(
            process_row(
                run_id,
                1,
                method,
                process_stage_id=stage_id,
                reactor_type=reactor,
                scale_level="not_reported",
                temperature_setpoint_C=first_match(r"(\d+(?:\.\d+)?)", temps[0]) if len(temps) == 1 else "",
                temperature_range_reported_C="; ".join(temps) or "not_reported",
                temperature_program_summary="; ".join(temps) or "not_reported",
                holding_time_min="not_reported",
                pressure_original=pressure or "not_reported",
                pressure_kPa="",
                carbon_source=carbon_source,
                reducing_gas=reducing,
                inert_gas=inert,
                cofeed_or_reactive_gas=cofeed,
                gas_composition_summary=gas_summary,
                GHSV_or_residence_time="; ".join(durations) or "not_reported",
                process_note="Reported condition block; no cross-block reconstruction.",
            )
        )

        product_id = f"{run_id}_PROD"
        tables["yield_quality"].append(
            yield_row(
                run_id,
                product_id=product_id,
                primary_yield_metric="reported yield/conversion/quality values",
                yield_original=yields["yield_original"],
                yield_definition_original="as reported in source block",
                carbon_source_conversion_percent=yields["conversion"],
                secondary_result_summary=text[:360],
                CNT_type_reported=yields["cnt_type"],
                CNT_type_confirmed="not_applicable",
                CNT_type_evidence="source text",
                outer_diameter_range_nm=yields["diameter"],
                length_summary=yields["length"],
                purified_product_purity_wt_percent=yields["purity"],
                characterization_methods="; ".join(all_matches(r"\b(TEM|SEM|FESEM|FE-SEM|Raman|TGA|XRD|BET)\b", text)) or "not_reported",
                notes="Reported values retained without unit conversion or inferred denominator.",
            )
        )

        cost_record_id = run_id
        scale_terms = all_matches(r"\b(lab(?:oratory)?[- ]scale|pilot[- ]scale|industrial[- ]scale|commercial(?: production)?|scale[- ]up|scalable)\b", text)
        safety_terms = all_matches(r"\b(toxic|hazard|explosion|flammable|corrosive|HCl|emission|waste)\b", text)
        tables["cost_scale_review"].append(
            cost_row(
                run_id,
                scale_level_demonstrated="not_reported",
                scale_level_claimed="; ".join(scale_terms) or "not_reported",
                scale_evidence_summary=text[:300] if scale_terms else "not_reported",
                quantitative_cost_reported="no",
                quantitative_cost_summary="not_reported",
                cost_driver_summary="high-temperature energy demand" if re.search(r"energy.{0,40}(?:temperature|demand|consumption)", text, re.I) else "not_reported",
                safety_risk="; ".join(safety_terms) or "not_reported",
                emission_or_waste="; ".join(safety_terms) or "not_reported",
                industrial_readiness_assessment="source claim only" if scale_terms else "not_reported",
                reproduction_value="medium" if temps or active_metals != "not_reported" else "low",
                reproduction_priority="pending_review",
                recommended_next_action="verify against cited primary study" if is_review else "verify full experimental context",
                review_note="No quantitative cost inferred.",
            )
        )

        evidence_specs = (
            ("CAT", "catalyst_system", catalyst_id, "active_metals; support_material; metal_ratio_original; preparation_method; reduction_condition"),
            ("PROC", "reactor_process_gas", stage_id, "stage_type; reactor_type; temperature_setpoint_C; temperature_range_reported_C; pressure_original; carbon_source; reducing_gas; inert_gas; cofeed_or_reactive_gas; gas_composition_summary; GHSV_or_residence_time"),
            ("PROD", "yield_quality", product_id, "yield_original; carbon_source_conversion_percent; CNT_type_reported; outer_diameter_range_nm; length_summary; purified_product_purity_wt_percent; characterization_methods"),
            ("SCALE", "cost_scale_review", cost_record_id, "scale_level_claimed; scale_evidence_summary; cost_driver_summary; safety_risk; emission_or_waste; industrial_readiness_assessment"),
        )
        evidence_ids = []
        for suffix, target_table, target_id, target_fields in evidence_specs:
            evidence_id = f"EVD_{source_id}_{digest}_{suffix}"
            evidence = evidence_row(
                store,
                source_id,
                evidence_id,
                run_id,
                target_table,
                target_id,
                target_fields,
                str(block["span_id"]),
                f"Source block supporting linked {target_table} record.",
                confidence="medium" if is_review else "high",
            )
            evidence["evidence_type"] = "review_report" if is_review else "direct_report"
            tables["evidence_index"].append(evidence)
            evidence_ids.append(evidence_id)

        tables["review_issue_log"].append(
            issue_row(
                f"{source_id}_ISSUE_{index:03d}",
                source_id,
                run_id,
                "secondary_source_limit" if is_review else "context_boundary",
                "source_run",
                run_id,
                "record_level",
                "Review-derived condition; verify against cited primary study before formal use."
                if is_review
                else "Condition block was not joined to facts outside its source span.",
                "; ".join(evidence_ids),
                "medium" if is_review else "low",
            )
        )
    return tables


def build_accessible_observation_tables(meta: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    """Structure the accessible abstract/title when lawful full text is absent."""
    source_id = str(meta["source_id"])
    abstract = clean(meta.get("abstract"))
    text = abstract or clean(meta.get("title"))
    evidence_scope = "abstract" if abstract else "title_metadata"
    run_id = f"{source_id}_ACCESSIBLE_OBSERVATION"
    catalyst_id = f"{run_id}_CAT"
    stage_id = f"{run_id}_S01"
    product_id = f"{run_id}_PROD"
    tables: dict[str, list[dict[str, str]]] = {name: [] for name in TABLES}
    tables["source_master"].append(
        row(
            "source_master",
            source_id=source_id,
            source_type=meta.get("source_type") or "paper",
            source_title=meta.get("title") or source_id,
            publication_year=meta.get("year") or "not_reported",
            authors_or_assignee=meta.get("authors") or "not_reported",
            publication_venue=meta.get("journal") or "not_reported",
            doi_or_patent_no=meta.get("doi") or "not_reported",
            source_link=meta.get("source_link") or "not_reported",
            source_database="local_metadata_registry",
            source_language=meta.get("language") or "not_reported",
            local_file_path="not_available",
            pdf_status=meta.get("pdf_status") or "lawful_fulltext_unavailable",
            screening_class="source_observation_only",
            source_section_scope=f"{evidence_scope} only; lawful full text unavailable after acquisition attempts.",
            extraction_status="needs_review",
            review_status="pending_review",
            notes="C class; accessible source evidence structured; no experimental facts inferred beyond the cited scope.",
        )
    )

    data_type = "abstract_reported_condition" if fact_score(text) >= 3 else "source_observation_no_extractable_condition"
    run = run_row(
        source_id,
        "ACCESSIBLE_OBSERVATION",
        f"Accessible {evidence_scope} observation",
        text[:480],
        "low",
    )
    run["data_type"] = data_type
    run["relevance_class"] = "C"
    run["notes"] = f"Evidence scope is {evidence_scope}; this is not represented as a full-text experimental run."
    tables["source_run"].append(run)

    temps = temperature_values(text)
    durations = duration_values(text)
    reducing, inert, cofeed, gas_summary = gas_values(text)
    yields = yield_values(text)
    active_metals = metal_summary(text)
    support = support_summary(text)
    method = method_value(text)
    reactor = reactor_value(text)
    carbon_source = carbon_source_summary(text)

    tables["catalyst_system"].append(
        catalyst_row(
            run_id,
            catalyst_id=catalyst_id,
            catalyst_label=f"{active_metals} on {support}" if support != "not_reported" else active_metals,
            active_metals=active_metals,
            support_material=support,
            metal_ratio_original=first_match(r"(\d+(?:\.\d+)?\s*wt\.?\s*%)", text) or "not_reported",
            preparation_method=first_match(r"\b(impregnation|co-precipitation|coprecipitation|sol-gel|Stöber|hydrothermal|calcination)\b", text) or "not_reported",
            preparation_detail=text[:320] if active_metals != "not_reported" else "not_reported",
            reduction_condition="not_reported",
            notes=f"Only values explicitly present in the accessible {evidence_scope} are populated.",
        )
    )
    tables["reactor_process_gas"].append(
        process_row(
            run_id,
            1,
            method,
            process_stage_id=stage_id,
            reactor_type=reactor,
            scale_level="not_reported",
            temperature_setpoint_C=first_match(r"(\d+(?:\.\d+)?)", temps[0]) if len(temps) == 1 else "",
            temperature_range_reported_C="; ".join(temps) or "not_reported",
            holding_time_min="not_reported",
            pressure_original=first_match(r"(\d+(?:\.\d+)?\s*(?:atm|bar|kPa|MPa))", text) or "not_reported",
            pressure_kPa="",
            carbon_source=carbon_source,
            reducing_gas=reducing,
            inert_gas=inert,
            cofeed_or_reactive_gas=cofeed,
            gas_composition_summary=gas_summary,
            GHSV_or_residence_time="; ".join(durations) or "not_reported",
            process_note=f"Accessible {evidence_scope} only; no full-text reconstruction.",
        )
    )
    tables["yield_quality"].append(
        yield_row(
            run_id,
            product_id=product_id,
            primary_yield_metric="reported accessible-scope yield/conversion/quality values",
            yield_original=yields["yield_original"],
            yield_definition_original="as reported in accessible evidence" if yields["yield_original"] != "not_reported" else "not_reported",
            carbon_source_conversion_percent=yields["conversion"],
            secondary_result_summary=text[:360],
            CNT_type_reported=yields["cnt_type"],
            CNT_type_confirmed="not_applicable",
            CNT_type_evidence=evidence_scope,
            outer_diameter_range_nm=yields["diameter"],
            length_summary=yields["length"],
            purified_product_purity_wt_percent=yields["purity"],
            characterization_methods="; ".join(all_matches(r"\b(TEM|SEM|FESEM|FE-SEM|Raman|TGA|XRD|BET)\b", text)) or "not_reported",
            notes="No value was inferred from inaccessible full text.",
        )
    )
    scale_terms = all_matches(r"\b(lab(?:oratory)?[- ]scale|pilot[- ]scale|industrial[- ]scale|commercial(?: production)?|scale[- ]up|scalable)\b", text)
    safety_terms = all_matches(r"\b(toxic|hazard|explosion|flammable|corrosive|HCl|emission|waste)\b", text)
    tables["cost_scale_review"].append(
        cost_row(
            run_id,
            scale_level_demonstrated="not_reported",
            scale_level_claimed="; ".join(scale_terms) or "not_reported",
            scale_evidence_summary=text[:300] if scale_terms else "not_reported",
            quantitative_cost_reported="no",
            quantitative_cost_summary="not_reported",
            cost_driver_summary="not_reported",
            safety_risk="; ".join(safety_terms) or "not_reported",
            emission_or_waste="; ".join(safety_terms) or "not_reported",
            industrial_readiness_assessment="not_reported",
            reproduction_value="low",
            reproduction_priority="fulltext_required",
            recommended_next_action="obtain lawful full text or author manuscript",
            review_note=f"Assessment limited to {evidence_scope}.",
        )
    )

    evidence_specs = (
        ("CAT", "catalyst_system", catalyst_id, "active_metals; support_material; metal_ratio_original; preparation_method"),
        ("PROC", "reactor_process_gas", stage_id, "stage_type; reactor_type; temperature_setpoint_C; temperature_range_reported_C; carbon_source; gas_composition_summary"),
        ("PROD", "yield_quality", product_id, "yield_original; carbon_source_conversion_percent; CNT_type_reported; outer_diameter_range_nm; length_summary; purified_product_purity_wt_percent; characterization_methods"),
        ("SCALE", "cost_scale_review", run_id, "scale_level_claimed; scale_evidence_summary; safety_risk; emission_or_waste"),
    )
    evidence_ids = []
    for suffix, target_table, target_id, fields in evidence_specs:
        evidence_id = f"EVD_{source_id}_ACCESSIBLE_{suffix}"
        tables["evidence_index"].append(
            row(
                "evidence_index",
                evidence_id=evidence_id,
                source_id=source_id,
                run_id=run_id,
                target_table=target_table,
                target_record_id=target_id,
                target_fields=fields,
                evidence_type="abstract_report" if abstract else "title_metadata",
                value_status="reported" if abstract else "not_reported",
                source_section=evidence_scope,
                source_locator=f"local_metadata_registry.{evidence_scope}",
                source_object_ref="not_applicable",
                evidence_text=text,
                evidence_summary=f"Accessible {evidence_scope} supporting this record; lawful full text unavailable.",
                confidence="low",
                linked_issue_id=f"{source_id}_ISSUE_ACCESS_SCOPE",
                notes="Evidence scope is explicit; inaccessible content was not inferred.",
            )
        )
        evidence_ids.append(evidence_id)
    tables["review_issue_log"].append(
        issue_row(
            f"{source_id}_ISSUE_ACCESS_SCOPE",
            source_id,
            run_id,
            "fulltext_unavailable_scope",
            "source_run",
            run_id,
            "record_level",
            f"Only {evidence_scope} evidence was legally accessible; full experimental coverage is not claimed.",
            "; ".join(evidence_ids),
            "high",
        )
    )
    return tables


def publish(source_id: str, tables: dict[str, list[dict[str, str]]]) -> dict[str, int]:
    destination = PACKAGE_ROOT / f"{source_id}.extraction.json"
    if destination.exists():
        ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination, ARCHIVE_ROOT / destination.name)
    write_extraction_package(
        source_id,
        "C",
        tables,
        extraction_status="needs_review",
        replace=True,
    )
    return {table: len(tables[table]) for table in TABLES}


def write_report(batch_number: int, results: list[dict[str, Any]]) -> None:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {
        "batch_id": BATCH_ID,
        "batch_number": batch_number,
        "completed_at": now_utc(),
        "sources": results,
    }
    (REPORT_ROOT / f"batch_{batch_number:03d}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def read_source_ids(path: Path) -> list[str]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [row_["source_id"] for row_ in csv.DictReader(handle) if row_.get("source_id")]


def parsed_c_source_ids() -> list[str]:
    with sqlite3.connect(META_DB) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("ATTACH DATABASE ? AS candidate", (str(CANDIDATE_DB),))
        return [
            str(item["source_id"])
            for item in connection.execute(
                """
                SELECT w.source_id
                FROM works AS w
                JOIN candidate.parse_source_status AS p USING (source_id)
                WHERE w.priority_tier = 'C'
                  AND p.parse_status = 'success'
                  AND COALESCE(p.span_count, 0) > 0
                ORDER BY w.source_id
                """
            )
        ]


def package_is_structured(source_id: str) -> bool:
    path = PACKAGE_ROOT / source_id / "source_run.csv"
    if not path.is_file():
        return False
    with path.open(encoding="utf-8-sig", newline="") as handle:
        first = next(csv.DictReader(handle), None)
    return bool(first and first.get("data_type") not in {"source_evidence_ledger", "source_status_ledger", ""})


def remaining_ledger_source_ids() -> list[str]:
    source_ids = []
    for package in sorted(item for item in PACKAGE_ROOT.iterdir() if item.is_dir()):
        path = package / "source_run.csv"
        if not path.is_file():
            continue
        with path.open(encoding="utf-8-sig", newline="") as handle:
            first = next(csv.DictReader(handle), None)
        if first and first.get("data_type") in {"source_evidence_ledger", "source_status_ledger"}:
            source_ids.append(package.name)
    return source_ids


def process_batch(source_ids: list[str], batch_number: int) -> list[dict[str, Any]]:
    store = EvidenceStore()
    results: list[dict[str, Any]] = []
    try:
        for source_id in source_ids:
            try:
                meta = source_metadata(source_id)
                spans = candidate_spans(source_id)
                tables = build_tables(meta, spans, store)
                counts = publish(source_id, tables)
                results.append({"source_id": source_id, "status": "structured", "candidate_spans": len(spans), "row_counts": counts})
                print(f"{source_id}: {counts['source_run']} structured records", flush=True)
            except Exception as exc:  # Continue the requested uninterrupted batch run.
                results.append({"source_id": source_id, "status": "failed", "error": str(exc)})
                print(f"{source_id}: FAILED: {exc}", flush=True)
    finally:
        store.close()
    write_report(batch_number, results)
    return results


def process_observation_batch(source_ids: list[str], batch_number: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for source_id in source_ids:
        try:
            meta = source_metadata(source_id)
            tables = build_accessible_observation_tables(meta)
            counts = publish(source_id, tables)
            scope = "abstract" if clean(meta.get("abstract")) else "title_metadata"
            results.append({"source_id": source_id, "status": "accessible_observation", "scope": scope, "row_counts": counts})
            print(f"{source_id}: accessible {scope} structured", flush=True)
        except Exception as exc:
            results.append({"source_id": source_id, "status": "failed", "error": str(exc)})
            print(f"{source_id}: FAILED: {exc}", flush=True)
    write_report(batch_number, results)
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", action="append", default=[])
    parser.add_argument("--source-list", type=Path)
    parser.add_argument("--batch-number", type=int)
    parser.add_argument("--all-parsed", action="store_true")
    parser.add_argument("--all-remaining-observations", action="store_true")
    parser.add_argument("--start-report-batch", type=int, default=2)
    parser.add_argument("--max-batches", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.all_remaining_observations:
        source_ids = remaining_ledger_source_ids()
        batches = [source_ids[index:index + 5] for index in range(0, len(source_ids), 5)]
        if args.max_batches is not None:
            batches = batches[: max(0, args.max_batches)]
        all_results: list[dict[str, Any]] = []
        for offset, batch in enumerate(batches):
            batch_number = args.start_report_batch + offset
            print(f"C accessible-evidence batch {batch_number:03d}: {', '.join(batch)}", flush=True)
            all_results.extend(process_observation_batch(batch, batch_number))
        completed = sum(item.get("status") == "accessible_observation" for item in all_results)
        failed = sum(item.get("status") == "failed" for item in all_results)
        print(json.dumps({"accessible_observations": completed, "failed": failed, "batches": len(batches)}, ensure_ascii=False), flush=True)
        return

    if args.all_parsed:
        source_ids = [source_id for source_id in parsed_c_source_ids() if not package_is_structured(source_id)]
        batches = [source_ids[index:index + 5] for index in range(0, len(source_ids), 5)]
        if args.max_batches is not None:
            batches = batches[: max(0, args.max_batches)]
        all_results: list[dict[str, Any]] = []
        for offset, batch in enumerate(batches):
            batch_number = args.start_report_batch + offset
            print(f"C structured batch {batch_number:03d}: {', '.join(batch)}", flush=True)
            all_results.extend(process_batch(batch, batch_number))
        structured = sum(item.get("status") == "structured" for item in all_results)
        failed = sum(item.get("status") == "failed" for item in all_results)
        print(json.dumps({"structured": structured, "failed": failed, "batches": len(batches)}, ensure_ascii=False), flush=True)
        return

    source_ids = list(dict.fromkeys(args.source_id + (read_source_ids(args.source_list) if args.source_list else [])))
    if not source_ids or len(source_ids) > 5:
        raise ValueError("Provide between one and five source IDs per batch")
    if args.batch_number is None:
        raise ValueError("--batch-number is required for an explicit batch")
    process_batch(source_ids, args.batch_number)


if __name__ == "__main__":
    main()
