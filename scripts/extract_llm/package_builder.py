from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


SECTION_PRIORITY = {
    "catalyst_preparation": 0,
    "cvd_growth": 0,
    "experimental": 1,
    "methods": 1,
    "results": 2,
    "characterization": 2,
    "tables": 2,
    "conclusion": 3,
    "figure_captions": 4,
    "abstract": 5,
    "other": 6,
}
SPAN_PRIORITY = {
    "process": 0,
    "gas": 0,
    "catalyst": 0,
    "yield": 1,
    "characterization": 2,
    "purification": 3,
    "scale_safety": 3,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _page_number(value: str) -> int:
    match = re.search(r"\d+", value or "")
    return int(match.group()) if match else 10**9


def build_input_package(
    source_id: str,
    section_csv: Path,
    span_csv: Path,
    max_chars: int = 26000,
) -> dict[str, Any]:
    sections = [row for row in read_csv(section_csv) if row["source_id"] == source_id]
    spans = [row for row in read_csv(span_csv) if row["source_id"] == source_id]
    if not sections:
        raise ValueError(f"No parsed sections found for {source_id}")
    if not spans:
        raise ValueError(f"No candidate spans found for {source_id}")

    section_by_id = {row["section_id"]: row for row in sections}
    title_row = next((row for row in sections if row["section_name_normalized"] == "title"), sections[0])
    content_hash = title_row["input_content_hash"]

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in spans:
        grouped[normalized_text(row["text"])].append(row)

    candidates: list[dict[str, Any]] = []
    for text_key, rows in grouped.items():
        rows.sort(key=lambda row: (SPAN_PRIORITY.get(row["span_type"], 9), row["span_id"]))
        representative = rows[0]
        section = section_by_id.get(representative["section_id"], {})
        span_types = sorted({row["span_type"] for row in rows}, key=lambda value: SPAN_PRIORITY.get(value, 9))
        keywords: set[str] = set()
        for row in rows:
            keywords.update(item.strip() for item in row["matched_keywords"].split(";") if item.strip())
        candidates.append(
            {
                "span_id": min(row["span_id"] for row in rows),
                "span_types": span_types,
                "section_name": section.get("section_name_normalized", "other"),
                "section_name_raw": section.get("section_name_raw", ""),
                "page_range": representative["page_range"],
                "confidence_score": max(float(row["confidence_score"] or 0) for row in rows),
                "matched_keywords": sorted(keywords),
                "text": text_key,
            }
        )

    candidates.sort(
        key=lambda item: (
            SECTION_PRIORITY.get(item["section_name"], 9),
            min(SPAN_PRIORITY.get(value, 9) for value in item["span_types"]),
            -item["confidence_score"],
            _page_number(item["page_range"]),
            item["span_id"],
        )
    )

    selected: list[dict[str, Any]] = []
    selected_chars = 0
    for candidate in candidates:
        cost = len(candidate["text"]) + 240
        if selected and selected_chars + cost > max_chars:
            continue
        selected.append(candidate)
        selected_chars += cost

    type_counts: dict[str, int] = defaultdict(int)
    for item in selected:
        for span_type in item["span_types"]:
            type_counts[span_type] += 1

    return {
        "source_id": source_id,
        "source_title": normalized_text(title_row["text"]),
        "input_content_hash": content_hash,
        "input_layer": "candidate_experiment_span",
        "selection_policy": "deduplicated_priority_v1",
        "selection_summary": {
            "original_span_rows": len(spans),
            "deduplicated_span_rows": len(candidates),
            "selected_span_rows": len(selected),
            "selected_text_chars": selected_chars,
            "max_text_chars": max_chars,
            "selected_type_counts": dict(sorted(type_counts.items())),
        },
        "candidate_spans": selected,
    }


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

