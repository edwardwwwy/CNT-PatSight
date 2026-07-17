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

SLOT_PATTERNS = {
    "catalyst_preparation": (
        r"catalysts? (?:are |were )?synthesi[sz]ed",
        r"impregnation",
        r"hydrotherm",
        r"precursor",
        r"sonicat",
        r"metal content",
        r"mol mol",
    ),
    "shared_reaction_conditions": (
        r"horizontal quartz tube",
        r"porcelain boat",
        r"\b150\s*mg\b",
        r"\b850\s*(?:1c|°c|c)\b",
        r"\b30\s*min",
        r"pure ch",
        r"\b20\s*ml\s*min",
        r"cooled.*helium",
    ),
    "catalyst_labels": (
        r"all catalysts are denoted",
        r"respectively",
        r"fe[/–—-].*mgo",
        r"mo/mgo",
        r"fe.*0[.?]1mo",
        r"fe.*0[.?]5mo",
        r"fe.*1mo",
    ),
    "yield_productivity": (
        r"carbon productivity",
        r"\byield\b",
        r"gcat",
        r"g g",
        r"weight loss",
        r"residual weight",
    ),
    "cnt_dimensions_tem": (
        r"inner diameter",
        r"outer diameter",
        r"\btem\b",
        r"swcnt",
        r"dwcnt",
        r"mwcnt",
        r"no evidence of cnt",
    ),
    "raman": (
        r"raman",
        r"id/ig",
        r"i.?/i.",
        r"d band",
        r"g band",
        r"532\s*nm",
    ),
    "tga_graphitic": (
        r"\btga\b",
        r"graphitic carbon",
        r"graphitization",
        r"thermal stability",
        r"600\s*(?:1c|°c|c)",
    ),
    "lifetime_scale": (
        r"lifetime",
        r"beyond 1 hour",
        r"15 to 60 minutes",
        r"plateauing within 30 minutes",
        r"sustained activity",
        r"scale",
        r"continuous",
    ),
    "figures_tables": (
        r"\bfig\.",
        r"\btable\b",
        r"red column",
        r"blue square",
        r"figure",
    ),
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
        if _page_start(str(payload["page_range"])) < _page_start(
            str(current["page_range"])
        ):
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


def build_slotted_package(
    source_id: str,
    section_csv: Path,
    span_csv: Path,
    max_per_slot: int = 4,
    max_total_chars: int = 32000,
) -> dict[str, Any]:
    """Select evidence by scientific information slot instead of global rank.

    A span can satisfy several slots and is stored only once. Slot membership
    remains explicit so run planning and per-run extraction can preserve
    preparation, shared conditions, result identity, characterization, and
    scale/lifetime coverage independently.
    """
    sections = [row for row in _read_csv(section_csv) if row.get("source_id") == source_id]
    spans = [row for row in _read_csv(span_csv) if row.get("source_id") == source_id]
    if not sections and not spans:
        raise ValueError(f"No parser candidate rows found for source_id={source_id}")
    title = next(
        (
            row.get("text", "")
            for row in sections
            if row.get("section_name_normalized") == "title"
        ),
        source_id,
    )
    content_hash = _content_hash(sections or spans)
    section_map = {row.get("section_id", ""): row for row in sections}
    merged = _merge_duplicate_spans(spans)

    slot_candidates: dict[str, list[tuple[tuple[float, int, int, str], dict[str, Any]]]] = {
        slot: [] for slot in SLOT_PATTERNS
    }
    for item in merged:
        normalized = _normalize_text(item["text"])
        section = section_map.get(item["section_id"], {})
        section_name = section.get("section_name_normalized", "other")
        for slot, patterns in SLOT_PATTERNS.items():
            hits = sum(bool(re.search(pattern, normalized, re.IGNORECASE)) for pattern in patterns)
            if slot == "figures_tables" and section_name in {"figure_captions", "tables"}:
                hits += 2
            if not hits:
                continue
            rank = (
                -(hits * 100 + item["confidence_score"] * 10 + SECTION_PRIORITY.get(section_name, 0)),
                _page_start(item["page_range"]),
                -len(item["text"]),
                item["span_id"],
            )
            slot_candidates[slot].append((rank, item))

    selected_by_id: dict[str, dict[str, Any]] = {}
    slot_coverage: dict[str, list[str]] = {}
    for slot, candidates in slot_candidates.items():
        chosen: list[str] = []
        for _, item in sorted(candidates, key=lambda pair: pair[0])[:max_per_slot]:
            chosen.append(item["span_id"])
            current = selected_by_id.setdefault(item["span_id"], dict(item))
            current.setdefault("slots", [])
            if slot not in current["slots"]:
                current["slots"].append(slot)
        slot_coverage[slot] = chosen

    def selected_rank(item: dict[str, Any]) -> tuple[int, int, str]:
        slot_weight = max(
            (
                list(SLOT_PATTERNS).index(slot)
                for slot in item.get("slots", [])
            ),
            default=len(SLOT_PATTERNS),
        )
        return slot_weight, _page_start(item.get("page_range", "")), item["span_id"]

    selected: list[dict[str, Any]] = []
    used_chars = 0
    for item in sorted(selected_by_id.values(), key=selected_rank):
        if selected and used_chars + len(item["text"]) > max_total_chars:
            continue
        section = section_map.get(item["section_id"], {})
        payload = dict(item)
        payload["slots"] = sorted(payload.get("slots", []))
        payload["section_name_normalized"] = section.get(
            "section_name_normalized", "other"
        )
        payload["section_name_raw"] = section.get("section_name_raw", "")
        payload["page_start"] = section.get("page_start", "")
        payload["page_end"] = section.get("page_end", "")
        selected.append(payload)
        used_chars += len(payload["text"])

    return {
        "package_version": "candidate_package_slotted_v1",
        "source_id": source_id,
        "source_title": title,
        "input_content_hash": content_hash,
        "spans": selected,
        "slot_coverage": slot_coverage,
        "selection_stats": {
            "all_section_rows": len(sections),
            "all_span_rows": len(spans),
            "unique_span_texts": len(merged),
            "selected_spans": len(selected),
            "selected_text_chars": used_chars,
            "max_per_slot": max_per_slot,
            "max_total_chars": max_total_chars,
        },
    }


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
