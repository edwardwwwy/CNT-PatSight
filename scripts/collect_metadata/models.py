from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class NormalizedWork:
    """Provider-independent paper metadata before canonical merging."""

    source_api: str
    external_id: str
    title: str
    source_type: str = "paper"
    document_type: str = ""
    source_database: str = ""
    doi: str = ""
    abstract: str = ""
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    journal: str = ""
    publisher: str = ""
    publication_date: str = ""
    citation_count: int | None = None
    source_url: str = ""
    open_access_status: str = "unknown"
    pdf_url: str = ""
    html_url: str = ""
    language: str = ""
    collected_at: str = ""
    manual_source_id: str = ""
    screening_class: str = ""
    pdf_status: str = ""
    pdf_path: str = ""
    extraction_status: str = "needs_review"
    review_status: str = "pending_review"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ApiResponse:
    source_api: str
    request_kind: str
    status_code: int
    data: Any
    raw_path: str
    collected_at: str
    returned_count: int = 0
    error: str = ""


@dataclass(slots=True)
class SourceBatch:
    records: list[tuple[NormalizedWork, str]] = field(default_factory=list)
    responses: list[ApiResponse] = field(default_factory=list)
    api_total: int | None = None
    skipped_reason: str = ""


@dataclass(slots=True)
class UpsertResult:
    source_id: str
    action: str
    match_type: str
    changed_fields: list[str] = field(default_factory=list)
    dedup_status: str = "unique"
    similarity: float | None = None
    related_source_id: str = ""
    dedup_reasons: list[str] = field(default_factory=list)
    conflict_reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MatchDecision:
    source_id: str | None
    match_type: str
    decision: str
    similarity: float | None = None
    related_source_id: str = ""
    dedup_reasons: list[str] = field(default_factory=list)
    conflict_reasons: list[str] = field(default_factory=list)
