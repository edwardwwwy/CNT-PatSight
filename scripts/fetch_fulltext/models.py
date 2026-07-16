from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MetadataRecord:
    source_id: str
    doi: str
    title: str
    abstract: str = ""
    pdf_url: str = ""
    html_url: str = ""
    pdf_path: str = ""
    priority_tier: str = ""
    topic_relevance_score: float = 0.0
    evidence_likelihood_score: float = 0.0
    access_score: float = 0.0
    citation_count: int = 0
    open_access_status: str = "unknown"
    field_sources_json: str = "{}"
    screening_rule_version: str = ""


@dataclass(slots=True)
class UrlCandidate:
    url: str
    expected_type: str
    url_source: str
    access_type: str = "unknown"
    license: str = ""


@dataclass(slots=True)
class FetchResult:
    requested_url: str
    final_url: str
    status_code: int
    media_type: str
    body: bytes
    error: str = ""


@dataclass(slots=True)
class HtmlInspection:
    title: str = ""
    text: str = ""
    headings: list[str] = field(default_factory=list)
    pdf_links: list[str] = field(default_factory=list)
    is_likely_fulltext: bool = False
    validation_note: str = ""


@dataclass(slots=True)
class ArtifactRecord:
    source_id: str
    doi: str
    title: str
    fulltext_type: str
    fulltext_url: str
    local_path: str
    fetch_status: str
    failure_reason: str
    content_hash: str
    content_bytes: int
    media_type: str
    http_status: int | None
    url_source: str
    content_scope: str
    validation_note: str
    created_at: str
    updated_at: str
    last_checked_at: str
    is_primary: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
        }
