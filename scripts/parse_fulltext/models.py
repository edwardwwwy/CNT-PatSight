from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PageText:
    page_number: int
    text: str


@dataclass(slots=True)
class TextSection:
    section_id: str
    source_id: str
    input_fulltext_id: str
    input_content_hash: str
    section_name_raw: str
    section_name_normalized: str
    section_order: int
    text: str
    page_start: int | None
    page_end: int | None
    extractor: str
    needs_review: int = 1


@dataclass(slots=True)
class CandidateSpan:
    source_id: str
    span_id: str
    input_fulltext_id: str
    section_id: str
    span_type: str
    text: str
    confidence_rule: str
    confidence_score: float
    matched_keywords: str
    page_range: str
    needs_review: int = 1


@dataclass(slots=True)
class ExtractionOutput:
    sections: list[TextSection] = field(default_factory=list)
    spans: list[CandidateSpan] = field(default_factory=list)
    raw_text: str = ""
    extractor: str = ""
    warnings: list[str] = field(default_factory=list)
    parse_quality: str = "metadata_only"
    page_count: int = 0
    extracted_char_count: int = 0
    table_count: int = 0
    reference_section_detected: int = 0
    experimental_section_detected: int = 0
    ocr_required: int = 0
    fulltext_relevance_status: str = "needs_fulltext_review"
    candidate_extract_eligible: int = 0
    promotion_reason: str = ""
