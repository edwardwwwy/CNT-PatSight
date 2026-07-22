#!/usr/bin/env python3
"""Convert the complete B-tier evidence export into atomic structured facts.

The B tier is a screening queue, so the parser evidence cannot safely be
flattened into experimental ``source_run`` rows without an evidence reviewer
confirming the run boundaries.  This module therefore emits a lossless,
long-form structure: every candidate span is represented once, while every
reported measurement and recognized scientific entity is an additional row
linked to the same immutable span.

The output is suitable for evidence review and later eight-table mapping.  It
never synthesizes a catalyst/process/result combination that is not explicit
in a source span.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[2]
BATCH_ID = "B_CLASS_371_20260719"
INPUT_ROOT = ROOT / "runs" / "extraction" / "B" / "batches" / BATCH_ID
OUTPUT_ROOT = INPUT_ROOT / "structured_evidence"

SPAN_FIELDS = (
    "source_id",
    "span_id",
    "section_name_normalized",
    "section_name_raw",
    "page_range",
    "span_type",
    "confidence_rule",
    "confidence_score",
    "text",
)
OBSERVATION_FIELDS = (
    "observation_id",
    "source_id",
    "span_id",
    "section_name_normalized",
    "section_name_raw",
    "page_range",
    "span_type",
    "observation_kind",
    "canonical_table",
    "canonical_field",
    "value_raw",
    "value_normalized",
    "unit",
    "qualifier",
    "value_status",
    "confidence",
    "evidence_text",
)
MEASUREMENT_FIELDS = (
    "measurement_id",
    "source_id",
    "span_id",
    "section_name_normalized",
    "page_range",
    "span_type",
    "canonical_table",
    "canonical_field",
    "value_raw",
    "value_normalized",
    "unit",
    "context",
    "value_status",
    "confidence",
    "evidence_text",
)
ENTITY_FIELDS = (
    "entity_id",
    "source_id",
    "span_id",
    "section_name_normalized",
    "page_range",
    "span_type",
    "entity_class",
    "canonical_table",
    "canonical_field",
    "value_raw",
    "value_normalized",
    "value_status",
    "confidence",
    "evidence_text",
)

NUMBER = r"[-+]?\d+(?:\.\d+)?"
RANGE = rf"{NUMBER}(?:\s*(?:-|–|−|to)\s*{NUMBER})?"
UNIT = (
    r"°\s*C|℃|\bK\b|\bsccm\b|cm3\s*/\s*min|mL\s*/\s*min|"
    r"L\s*/\s*min|\bmin(?:utes?)?\b|\bhours?\b|\bh\b|wt\.?\s*%|"
    r"%|g\s*/\s*g(?:cat|\s*metal)?|gcat(?:\s*[-−]?1)?|"
    r"mg|\bg\b|\bbar\b|\bkPa\b|\bMPa\b|\batm\b|\bTorr\b|"
    r"\bnm\b|[µu]m|\bcm\b|\bmm\b|\beV\b|W\s*/\s*m\s*K"
)
MEASUREMENT_RE = re.compile(rf"(?P<value>{RANGE})\s*(?P<unit>{UNIT})", re.IGNORECASE)

ENTITY_PATTERNS: tuple[tuple[str, str, str, str, tuple[str, ...]], ...] = (
    (
        "catalyst_metal",
        "catalyst_system",
        "active_metals",
        "Fe",
        (r"\bFe\b", r"\biron\b"),
    ),
    (
        "catalyst_metal",
        "catalyst_system",
        "active_metals",
        "Co",
        (r"\bCo\b", r"\bcobalt\b"),
    ),
    (
        "catalyst_metal",
        "catalyst_system",
        "active_metals",
        "Ni",
        (r"\bNi\b", r"\bnickel\b"),
    ),
    (
        "catalyst_metal",
        "catalyst_system",
        "active_metals",
        "Mo",
        (r"\bMo\b", r"\bmolybdenum\b"),
    ),
    (
        "catalyst_metal",
        "catalyst_system",
        "active_metals",
        "Cu",
        (r"\bCu\b", r"\bcopper\b"),
    ),
    (
        "catalyst_metal",
        "catalyst_system",
        "active_metals",
        "Mn",
        (r"\bMn\b", r"\bmanganese\b"),
    ),
    (
        "catalyst_metal",
        "catalyst_system",
        "active_metals",
        "Ru",
        (r"\bRu\b", r"\bruthenium\b"),
    ),
    (
        "catalyst_metal",
        "catalyst_system",
        "active_metals",
        "Pt",
        (r"\bPt\b", r"\bplatinum\b"),
    ),
    (
        "carbon_source",
        "reactor_process_gas",
        "carbon_source",
        "CH4",
        (r"\bCH4\b", r"\bmethane\b"),
    ),
    (
        "carbon_source",
        "reactor_process_gas",
        "carbon_source",
        "C2H2",
        (r"\bC2H2\b", r"\bacetylene\b"),
    ),
    (
        "carbon_source",
        "reactor_process_gas",
        "carbon_source",
        "C2H4",
        (r"\bC2H4\b", r"\bethylene\b"),
    ),
    (
        "carbon_source",
        "reactor_process_gas",
        "carbon_source",
        "ethanol",
        (r"\bethanol\b",),
    ),
    (
        "carbon_source",
        "reactor_process_gas",
        "carbon_source",
        "benzene",
        (r"\bbenzene\b",),
    ),
    (
        "carbon_source",
        "reactor_process_gas",
        "carbon_source",
        "toluene",
        (r"\btoluene\b",),
    ),
    (
        "carbon_source",
        "reactor_process_gas",
        "carbon_source",
        "natural gas",
        (r"\bnatural gas\b",),
    ),
    (
        "carbon_source",
        "reactor_process_gas",
        "carbon_source",
        "biogas",
        (r"\bbiogas\b",),
    ),
    (
        "reaction_gas",
        "reactor_process_gas",
        "reducing_gas",
        "H2",
        (r"\bH2\b", r"\bhydrogen\b"),
    ),
    (
        "reaction_gas",
        "reactor_process_gas",
        "inert_gas",
        "N2",
        (r"\bN2\b", r"\bnitrogen\b"),
    ),
    (
        "reaction_gas",
        "reactor_process_gas",
        "inert_gas",
        "Ar",
        (r"\bAr\b", r"\bargon\b"),
    ),
    (
        "reaction_gas",
        "reactor_process_gas",
        "cofeed_or_reactive_gas",
        "CO2",
        (r"\bCO2\b", r"\bcarbon dioxide\b"),
    ),
    (
        "process",
        "reactor_process_gas",
        "stage_type",
        "CVD",
        (r"\b(?:chemical vapou?r deposition|CVD|CCVD|PECVD|FCCVD)\b",),
    ),
    (
        "process",
        "reactor_process_gas",
        "stage_type",
        "pyrolysis",
        (r"\bpyrolysis\b",),
    ),
    (
        "cnt_type",
        "yield_quality",
        "CNT_type_reported",
        "SWCNT",
        (r"\b(?:single[- ]?walled carbon nanotubes?|SWCNTs?)\b",),
    ),
    (
        "cnt_type",
        "yield_quality",
        "CNT_type_reported",
        "MWCNT",
        (r"\b(?:multi[- ]?walled carbon nanotubes?|MWCNTs?)\b",),
    ),
    (
        "cnt_type",
        "yield_quality",
        "CNT_type_reported",
        "DWCNT",
        (r"\b(?:double[- ]?walled carbon nanotubes?|DWCNTs?)\b",),
    ),
    (
        "characterization",
        "yield_quality",
        "characterization_methods",
        "TEM",
        (r"\bH?RTEM\b", r"\bTEM\b"),
    ),
    (
        "characterization",
        "yield_quality",
        "characterization_methods",
        "SEM",
        (r"\bFE-?SEM\b", r"\bSEM\b"),
    ),
    (
        "characterization",
        "yield_quality",
        "characterization_methods",
        "Raman",
        (r"\bRaman\b",),
    ),
    (
        "characterization",
        "yield_quality",
        "characterization_methods",
        "XRD",
        (r"\bXRD\b",),
    ),
    (
        "characterization",
        "yield_quality",
        "characterization_methods",
        "TGA",
        (r"\bTGA\b", r"\bthermogravimetric\b"),
    ),
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, headers: Sequence[str], rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: "" if row.get(field) is None else row.get(field) for field in headers})
            count += 1
    return count


def _confidence(score: str) -> str:
    try:
        numeric = float(score)
    except ValueError:
        return "low"
    if numeric >= 0.85:
        return "high"
    if numeric >= 0.55:
        return "medium"
    return "low"


def _default_mapping(span_type: str) -> tuple[str, str]:
    return {
        "catalyst": ("catalyst_system", "notes"),
        "process": ("reactor_process_gas", "process_note"),
        "gas": ("reactor_process_gas", "gas_composition_summary"),
        "yield": ("yield_quality", "secondary_result_summary"),
        "characterization": ("yield_quality", "characterization_methods"),
        "purification": ("yield_quality", "post_treatment_or_purification"),
        "scale_safety": ("cost_scale_review", "review_note"),
    }.get(span_type, ("source_evidence", "text"))


def _context(text: str, start: int, end: int, width: int = 90) -> str:
    return " ".join(text[max(0, start - width) : min(len(text), end + width)].split())


def _measurement_mapping(unit: str, context: str) -> tuple[str, str]:
    normalized_unit = unit.lower().replace(" ", "")
    lower = context.lower()
    if "°" in unit or unit in {"℃", "K"}:
        return "reactor_process_gas", "temperature_setpoint_C"
    if normalized_unit in {"min", "minute", "minutes", "h", "hour", "hours"}:
        return "reactor_process_gas", "holding_time_min"
    if any(token in normalized_unit for token in ("sccm", "ml/min", "cm3/min", "l/min")):
        if any(token in lower for token in ("methane", "ch4", "acetylene", "c2h2", "ethanol", "ethylene", "c2h4")):
            return "reactor_process_gas", "carbon_source_flow_original"
        return "reactor_process_gas", "total_flow_original"
    if normalized_unit in {"bar", "kpa", "mpa", "atm", "torr"}:
        return "reactor_process_gas", "pressure_original"
    if normalized_unit in {"nm", "µm", "um", "cm", "mm"}:
        if "diameter" in lower:
            return "yield_quality", "outer_diameter_range_nm"
        if any(token in lower for token in ("length", "height", "long")):
            return "yield_quality", "length_summary"
    if any(token in lower for token in ("yield", "productivity", "conversion", "selectivity")):
        return "yield_quality", "yield_original"
    if "%" in normalized_unit and any(token in lower for token in ("carbon content", "purity", "tga")):
        return "yield_quality", "TGA_carbon_content_wt_percent"
    if "raman" in lower and any(token in lower for token in ("id/ig", "i_d/i_g", "ig/id")):
        return "yield_quality", "Raman_ratio_value"
    return "source_evidence", "numeric_observation"


def _observation_row(span: dict[str, str]) -> dict[str, str]:
    table, field = _default_mapping(span["span_type"])
    return {
        "observation_id": f"OBS_{span['source_id']}_{span['span_id']}_TEXT",
        "source_id": span["source_id"],
        "span_id": span["span_id"],
        "section_name_normalized": span["section_name_normalized"],
        "section_name_raw": span["section_name_raw"],
        "page_range": span["page_range"],
        "span_type": span["span_type"],
        "observation_kind": "source_evidence",
        "canonical_table": table,
        "canonical_field": field,
        "value_raw": span["text"],
        "value_normalized": "",
        "unit": "",
        "qualifier": span["confidence_rule"],
        "value_status": "reported",
        "confidence": _confidence(span["confidence_score"]),
        "evidence_text": span["text"],
    }


def _measurement_rows(span: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, match in enumerate(MEASUREMENT_RE.finditer(span["text"]), start=1):
        value = match.group("value")
        unit = match.group("unit")
        context = _context(span["text"], match.start(), match.end())
        table, field = _measurement_mapping(unit, context)
        rows.append(
            {
                "measurement_id": f"MEAS_{span['source_id']}_{span['span_id']}_{index:03d}",
                "source_id": span["source_id"],
                "span_id": span["span_id"],
                "section_name_normalized": span["section_name_normalized"],
                "page_range": span["page_range"],
                "span_type": span["span_type"],
                "canonical_table": table,
                "canonical_field": field,
                "value_raw": f"{value} {unit}",
                "value_normalized": "",
                "unit": unit,
                "context": context,
                "value_status": "reported",
                "confidence": _confidence(span["confidence_score"]),
                "evidence_text": span["text"],
            }
        )
    return rows


def _entity_rows(span: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for entity_class, table, field, normalized, patterns in ENTITY_PATTERNS:
        match = next((re.search(pattern, span["text"], re.IGNORECASE) for pattern in patterns if re.search(pattern, span["text"], re.IGNORECASE)), None)
        if match is None:
            continue
        key = entity_class, field, normalized
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "entity_id": f"ENT_{span['source_id']}_{span['span_id']}_{len(rows) + 1:03d}",
                "source_id": span["source_id"],
                "span_id": span["span_id"],
                "section_name_normalized": span["section_name_normalized"],
                "page_range": span["page_range"],
                "span_type": span["span_type"],
                "entity_class": entity_class,
                "canonical_table": table,
                "canonical_field": field,
                "value_raw": match.group(0),
                "value_normalized": normalized,
                "value_status": "reported",
                "confidence": _confidence(span["confidence_score"]),
                "evidence_text": span["text"],
            }
        )
    return rows


def _validate_inputs(manifest: list[dict[str, str]], spans: list[dict[str, str]]) -> None:
    required = {"source_id", "extraction_state"}
    if not manifest or required - set(manifest[0]):
        raise ValueError("B-class manifest is missing required fields")
    if not spans or set(SPAN_FIELDS) - set(spans[0]):
        raise ValueError("B-class candidate evidence is missing required fields")
    evidence_sources = {
        row["source_id"]
        for row in manifest
        if row["extraction_state"] == "candidate_evidence_exported_needs_review"
    }
    if {row["source_id"] for row in spans} != evidence_sources:
        raise ValueError("Candidate evidence coverage does not match the B-class manifest")


def build_structured_evidence(replace: bool = False) -> dict[str, Any]:
    """Create the lossless B-tier structured-evidence dataset."""
    if OUTPUT_ROOT.exists() and not replace:
        raise FileExistsError(f"Structured B-class output already exists: {OUTPUT_ROOT}; pass --replace to refresh it")
    manifest = _read_csv(INPUT_ROOT / "manifest.csv")
    spans = _read_csv(INPUT_ROOT / "candidate_evidence.csv")
    _validate_inputs(manifest, spans)

    observations = [_observation_row(span) for span in spans]
    measurements = [row for span in spans for row in _measurement_rows(span)]
    entities = [row for span in spans for row in _entity_rows(span)]
    source_summary: list[dict[str, Any]] = []
    measurement_counts = Counter(row["source_id"] for row in measurements)
    entity_counts = Counter(row["source_id"] for row in entities)
    span_counts = Counter(row["source_id"] for row in spans)
    for source_id in sorted(span_counts):
        source_summary.append(
            {
                "source_id": source_id,
                "candidate_span_count": span_counts[source_id],
                "atomic_evidence_count": span_counts[source_id],
                "measurement_count": measurement_counts[source_id],
                "entity_count": entity_counts[source_id],
                "status": "structured_evidence_needs_run_level_review",
            }
        )

    OUTPUT_ROOT.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".b_class_structured.", dir=OUTPUT_ROOT.parent))
    try:
        existing = [
            row
            for row in manifest
            if row["extraction_state"] == "existing_curated_package"
        ]
        unavailable = [
            row
            for row in manifest
            if row["extraction_state"] == "fulltext_or_parse_unavailable"
        ]
        row_counts = {
            "source_registry": _write_csv(temporary / "source_registry.csv", list(manifest[0]), manifest),
            "atomic_observations": _write_csv(
                temporary / "atomic_observations.csv", OBSERVATION_FIELDS, observations
            ),
            "measurements": _write_csv(temporary / "measurements.csv", MEASUREMENT_FIELDS, measurements),
            "entities": _write_csv(temporary / "entities.csv", ENTITY_FIELDS, entities),
            "source_summary": _write_csv(
                temporary / "source_summary.csv",
                (
                    "source_id",
                    "candidate_span_count",
                    "atomic_evidence_count",
                    "measurement_count",
                    "entity_count",
                    "status",
                ),
                source_summary,
            ),
            "existing_structured_packages": _write_csv(
                temporary / "existing_structured_packages.csv", list(manifest[0]), existing
            ),
            "unavailable_sources": _write_csv(
                temporary / "unavailable_sources.csv", list(manifest[0]), unavailable
            ),
        }
        summary = {
            "batch_id": BATCH_ID,
            "source_registry_count": len(manifest),
            "structured_evidence_source_count": len(source_summary),
            "atomic_observation_count": len(observations),
            "measurement_count": len(measurements),
            "entity_count": len(entities),
            "existing_eight_table_package_count": len(existing),
            "unavailable_source_count": len(unavailable),
            "row_counts": row_counts,
            "value_status": "reported_from_source_span",
            "run_boundary_status": "not_reconstructed; requires independent evidence review",
            "coverage": "Every candidate evidence span in the B-class evidence export has one atomic observation row.",
        }
        (temporary / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        if OUTPUT_ROOT.exists():
            shutil.rmtree(OUTPUT_ROOT)
        shutil.move(str(temporary), str(OUTPUT_ROOT))
        return summary
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def main() -> None:
    parser = argparse.ArgumentParser(description="Structure the complete B-class evidence registry.")
    parser.add_argument("--replace", action="store_true", help="Refresh the existing derived structure.")
    args = parser.parse_args()
    print(json.dumps(build_structured_evidence(args.replace), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
