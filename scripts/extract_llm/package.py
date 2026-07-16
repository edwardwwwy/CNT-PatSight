from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


PACKAGE_VERSION = "candidate_package_v1"
SPACE_RE = re.compile(r"\s+")

SECTION_PRIORITY = {
    "catalyst_preparation": 100,
    "cvd_growth": 100,
    "experimental": 95,
    "methods": 90,
    "tables": 85,
    "results": 80,
    "characterization": 75,
    "discussion": 65,
    "conclusion": 60,
    "abstract": 50,
    "supplementary_hints": 45,
    "introduction": 35,
    "figure_captions": 30,
    "other": 20,
    "references": 5,
    "title": 1,
}

SPAN_PRIORITY = {
    "yield": 100,
    "process": 95,
    "gas": 95,
    "catalyst": 90,
    "characterization": 80,
    "purification": 70,
    "scale_safety": 55,
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _normalize_text(text: str) -> str:
    return SPACE_RE.sub(" ", text).strip().lower()


def _page_start(page_range: str) -> int:
    match = re.search(r"\d+", page_range or "")
    return int(match.group()) if match else 999999


def _content_hash(rows: list[dict[str, str]]) -> str:
    hashes = sorted({row.get("input_content_hash", "") for row in rows if row.get("input_content_hash")})
    if hashes:
        return hashes[0]
    return hashlib.sha256("".join(row.get("text", "") for row in rows).encode("utf-8")).hexdigest()


def _merge_duplicate_spans(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for row in rows:
        text = row.get("text", "").strip()
        if len(text) < 40:
            continue
        key = _normalize_text(text)
        current = merged.get(key)
        payload = {
            "span_id": row["span_id"],
            "duplicate_span_ids": [row["span_id"]],
            "section_id": row.get("section_id", ""),
            "span_type": row.get("span_type", ""),
            "span_types": [row.get("span_type", "")],
            "text": text,
            "confidence_rule": row.get("confidence_rule", ""),
            "confidence_score": float(row.get("confidence_score") or 0),
            "matched_keywords": [x.strip() for x in row.get("matched_keywords", "").split(";") if x.strip()],
            "page_range": row.get("page_range", ""),
        }
        if current is None:
            merged[key] = payload
            continue
        current["duplicate_span_ids"].append(row["span_id"])
        if row.get("span_type") and row["span_type"] not in current["span_types"]:
            current["span_types"].append(row["span_type"])
        current["matched_keywords"] = sorted(set(current["matched_keywords"] + payload["matched_keywords"]))
        current["confidence_score"] = max(current["confidence_score"], payload["confidence_score"])
        if _page_start(payload["page_range"]) < _page_start(current["page_range"]):
            current["page_range"] = payload["page_range"]
    return list(merged.values())


def build_package(
    source_id: str,
    section_csv: Path,
    span_csv: Path,
    max_chars: int = 28000,
    max_spans: int = 100,
) -> dict[str, Any]:
    sections = [row for row in _read_csv(section_csv) if row.get("source_id") == source_id]
    spans = [row for row in _read_csv(span_csv) if row.get("source_id") == source_id]
    if not sections and not spans:
        raise ValueError(f"No parser candidate rows found for source_id={source_id}")
    title = next((row.get("text", "") for row in sections if row.get("section_name_normalized") == "title"), source_id)
    content_hash = _content_hash(sections or spans)
    section_map = {row.get("section_id", ""): row for row in sections}
    merged = _merge_duplicate_spans(spans)

    def rank(item: dict[str, Any]) -> tuple[float, int, int, str]:
        section = section_map.get(item["section_id"], {})
        section_name = section.get("section_name_normalized", "other")
        type_priority = max((SPAN_PRIORITY.get(name, 0) for name in item["span_types"]), default=0)
        score = item["confidence_score"] * 10 + SECTION_PRIORITY.get(section_name, 0) + type_priority / 10
        return (-score, _page_start(item["page_range"]), -len(item["text"]), item["span_id"])

    selected: list[dict[str, Any]] = []
    used_chars = 0
    for item in sorted(merged, key=rank):
        if len(selected) >= max_spans:
            break
        if selected and used_chars + len(item["text"]) > max_chars:
            continue
        section = section_map.get(item["section_id"], {})
        item = dict(item)
        item["section_name_normalized"] = section.get("section_name_normalized", "other")
        item["section_name_raw"] = section.get("section_name_raw", "")
        item["page_start"] = section.get("page_start", "")
        item["page_end"] = section.get("page_end", "")
        selected.append(item)
        used_chars += len(item["text"])

    section_catalog: list[dict[str, str]] = []
    seen_sections: set[tuple[str, str]] = set()
    repeated_limit = {"tables": 3, "figure_captions": 3}
    repeated_counts: defaultdict[str, int] = defaultdict(int)
    for row in sections:
        normalized = row.get("section_name_normalized", "")
        if normalized in {"title", "references"}:
            continue
        raw = row.get("section_name_raw", "")
        key = (normalized, raw)
        if key in seen_sections:
            continue
        if normalized in repeated_limit and repeated_counts[normalized] >= repeated_limit[normalized]:
            continue
        seen_sections.add(key)
        repeated_counts[normalized] += 1
        section_catalog.append({
            "section_id": row.get("section_id", ""),
            "section_name_raw": raw,
            "section_name_normalized": normalized,
            "page_start": row.get("page_start", ""),
            "page_end": row.get("page_end", ""),
        })
    return {
        "package_version": PACKAGE_VERSION,
        "source_id": source_id,
        "source_title": title,
        "input_content_hash": content_hash,
        "sections": section_catalog,
        "spans": selected,
        "selection_stats": {
            "all_section_rows": len(sections),
            "all_span_rows": len(spans),
            "unique_span_texts": len(merged),
            "selected_spans": len(selected),
            "selected_text_chars": used_chars,
            "max_chars": max_chars,
            "max_spans": max_spans,
        },
    }


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
