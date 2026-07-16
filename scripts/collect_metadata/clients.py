from __future__ import annotations

import json
import random
import re
import threading
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, quote, urlencode, urlsplit
from urllib.request import Request, urlopen

from .models import ApiResponse, NormalizedWork, SourceBatch
from .utils import (
    first_text,
    first_year,
    json_dumps,
    normalize_doi,
    reconstruct_openalex_abstract,
    redact_url,
    strip_markup,
    unique_text,
    utc_now,
)


class RawArchive:
    def __init__(self, base_dir: Path, root: Path, run_id: str):
        self.base_dir = base_dir / run_id
        self.root = root
        self._counter = 0
        self._lock = threading.Lock()

    def save(
        self,
        source_api: str,
        request_kind: str,
        method: str,
        url: str,
        request_headers: dict[str, str],
        request_body: Any,
        status_code: int,
        response_headers: dict[str, str],
        response_body: Any,
        error: str,
        collected_at: str,
    ) -> str:
        with self._lock:
            self._counter += 1
            counter = self._counter
        target_dir = self.base_dir / source_api
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_kind = re.sub(r"[^a-zA-Z0-9_-]+", "_", request_kind).strip("_")[:60] or "request"
        path = target_dir / f"{counter:05d}_{safe_kind}.json"
        sensitive_names = {"api_key", "apikey", "key", "token", "access_token", "email", "mailto"}
        secrets = [
            value
            for key, value in parse_qsl(urlsplit(url).query)
            if key.lower() in sensitive_names and value
        ]
        secrets.extend(
            value
            for key, value in request_headers.items()
            if key.lower() in {"x-api-key", "authorization", "crossref-plus-api-token"} and value
        )
        safe_headers = {}
        for key, value in request_headers.items():
            if key.lower() in {"x-api-key", "authorization", "crossref-plus-api-token"}:
                safe_headers[key] = "<redacted>"
            else:
                safe_headers[key] = self._redact_value(value, secrets)
        artifact = {
            "request": {
                "source_api": source_api,
                "request_kind": request_kind,
                "method": method,
                "url": redact_url(url),
                "headers": safe_headers,
                "body": self._redact_value(request_body, secrets),
            },
            "response": {
                "status_code": status_code,
                "headers": self._redact_value(response_headers, secrets),
                "body": self._redact_value(response_body, secrets),
                "error": self._redact_value(error, secrets),
            },
            "collected_at": collected_at,
        }
        path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    @classmethod
    def _redact_value(cls, value: Any, secrets: list[str]) -> Any:
        if isinstance(value, dict):
            return {key: cls._redact_value(item, secrets) for key, item in value.items()}
        if isinstance(value, list):
            return [cls._redact_value(item, secrets) for item in value]
        if isinstance(value, tuple):
            return [cls._redact_value(item, secrets) for item in value]
        if not isinstance(value, str):
            return value
        redacted = value
        for secret in secrets:
            if secret:
                redacted = redacted.replace(secret, "<redacted>")
        return re.sub(
            r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
            "<redacted-email>",
            redacted,
            flags=re.I,
        )


class JsonHttpClient:
    RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}

    def __init__(self, archive: RawArchive, timeout_seconds: int = 30, max_retries: int = 4):
        self.archive = archive
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def request(
        self,
        source_api: str,
        request_kind: str,
        method: str,
        base_url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        json_body: Any = None,
    ) -> ApiResponse:
        params = {key: value for key, value in (params or {}).items() if value not in (None, "")}
        query = urlencode(params, doseq=True)
        url = f"{base_url}{'&' if '?' in base_url else '?'}{query}" if query else base_url
        request_headers = {"Accept": "application/json", **(headers or {})}
        body_bytes = None
        if json_body is not None:
            body_bytes = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
        last_response: ApiResponse | None = None
        for attempt in range(1, self.max_retries + 1):
            collected_at = utc_now()
            status_code = 0
            response_headers: dict[str, str] = {}
            response_body: Any = None
            error = ""
            retry_after = 0.0
            try:
                request = Request(url, data=body_bytes, headers=request_headers, method=method.upper())
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    status_code = int(response.status)
                    response_headers = dict(response.headers.items())
                    raw_body = response.read().decode("utf-8", errors="replace")
                    response_body = self._decode_body(raw_body)
            except HTTPError as exc:
                status_code = int(exc.code)
                response_headers = dict(exc.headers.items()) if exc.headers else {}
                raw_body = exc.read().decode("utf-8", errors="replace")
                response_body = self._decode_body(raw_body)
                error = f"HTTP {status_code}: {self._error_detail(response_body)}"
                retry_after = self._retry_after(response_headers)
            except (URLError, TimeoutError, OSError) as exc:
                error = f"{type(exc).__name__}: {exc}"
                response_body = {"transport_error": str(exc)}
            raw_path = self.archive.save(
                source_api,
                request_kind,
                method.upper(),
                url,
                request_headers,
                json_body,
                status_code,
                response_headers,
                response_body,
                error,
                collected_at,
            )
            last_response = ApiResponse(
                source_api=source_api,
                request_kind=request_kind,
                status_code=status_code,
                data=response_body,
                raw_path=raw_path,
                collected_at=collected_at,
                error=error,
            )
            if 200 <= status_code < 300:
                return last_response
            if attempt >= self.max_retries or (status_code and status_code not in self.RETRY_STATUS):
                return last_response
            delay = retry_after or min(30.0, 2 ** (attempt - 1) + random.random())
            time.sleep(delay)
        assert last_response is not None
        return last_response

    @staticmethod
    def _decode_body(raw_body: str) -> Any:
        if not raw_body:
            return None
        try:
            return json.loads(raw_body)
        except json.JSONDecodeError:
            return raw_body

    @staticmethod
    def _error_detail(body: Any) -> str:
        if isinstance(body, dict):
            return str(body.get("error") or body.get("message") or body)[:500]
        return str(body)[:500]

    @staticmethod
    def _retry_after(headers: dict[str, str]) -> float:
        value = next((v for k, v in headers.items() if k.lower() == "retry-after"), "")
        try:
            return min(60.0, max(0.0, float(value)))
        except ValueError:
            return 0.0


class OpenAlexClient:
    BASE_URL = "https://api.openalex.org/works"

    def __init__(self, http: JsonHttpClient, api_key: str, user_agent: str):
        self.http = http
        self.api_key = api_key
        self.user_agent = user_agent

    def search(self, query_id: str, query: str, limit: int) -> SourceBatch:
        if not self.api_key:
            return SourceBatch(skipped_reason="OPENALEX_API_KEY is missing")
        batch = SourceBatch()
        cursor = "*"
        while len(batch.records) < limit and cursor:
            per_page = min(100, limit - len(batch.records))
            response = self.http.request(
                "openalex",
                f"search_{query_id}",
                "GET",
                self.BASE_URL,
                params={
                    "search": query,
                    "per_page": per_page,
                    "cursor": cursor,
                    "api_key": self.api_key,
                },
                headers={"User-Agent": self.user_agent},
            )
            payload = response.data if isinstance(response.data, dict) else {}
            results = payload.get("results") if isinstance(payload.get("results"), list) else []
            response.returned_count = len(results)
            batch.responses.append(response)
            if response.error:
                break
            meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
            if batch.api_total is None and isinstance(meta.get("count"), int):
                batch.api_total = int(meta["count"])
            for item in results:
                if isinstance(item, dict):
                    normalized = normalize_openalex(item, response.collected_at)
                    if normalized.title:
                        batch.records.append((normalized, response.raw_path))
            next_cursor = meta.get("next_cursor")
            if not results or not next_cursor or next_cursor == cursor:
                break
            cursor = str(next_cursor)
        return batch


class SemanticScholarClient:
    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/batch"
    FIELDS = (
        "paperId,externalIds,url,title,abstract,venue,year,publicationDate,authors,"
        "citationCount,isOpenAccess,openAccessPdf,journal,publicationTypes"
    )

    def __init__(self, http: JsonHttpClient, api_key: str, user_agent: str):
        self.http = http
        self.api_key = api_key
        self.user_agent = user_agent

    def enrich(self, dois: list[str]) -> SourceBatch:
        if not self.api_key:
            return SourceBatch(skipped_reason="SEMANTIC_SCHOLAR_API_KEY is missing")
        batch = SourceBatch()
        for index in range(0, len(dois), 500):
            chunk = dois[index : index + 500]
            response = self.http.request(
                "semantic_scholar",
                f"doi_batch_{index // 500 + 1}",
                "POST",
                self.BASE_URL,
                params={"fields": self.FIELDS},
                headers={"User-Agent": self.user_agent, "x-api-key": self.api_key},
                json_body={"ids": [f"DOI:{doi}" for doi in chunk]},
            )
            items = response.data if isinstance(response.data, list) else []
            response.returned_count = sum(1 for item in items if isinstance(item, dict))
            batch.responses.append(response)
            if response.error:
                continue
            for item in items:
                if isinstance(item, dict):
                    normalized = normalize_semantic_scholar(item, response.collected_at)
                    if normalized.title:
                        batch.records.append((normalized, response.raw_path))
        batch.api_total = len(batch.records)
        return batch


class CrossrefClient:
    BASE_URL = "https://api.crossref.org/v1/works"

    def __init__(self, http: JsonHttpClient, email: str, user_agent: str, interval: float):
        self.http = http
        self.email = email
        self.user_agent = user_agent
        self.interval = interval

    def enrich(self, dois: list[str]) -> SourceBatch:
        batch = SourceBatch()
        for index, doi in enumerate(dois):
            if index and self.interval:
                time.sleep(self.interval)
            response = self.http.request(
                "crossref",
                f"doi_{index + 1}",
                "GET",
                f"{self.BASE_URL}/{quote(doi, safe='/')}",
                params={"mailto": self.email},
                headers={"User-Agent": self.user_agent},
            )
            payload = response.data if isinstance(response.data, dict) else {}
            item = payload.get("message") if isinstance(payload.get("message"), dict) else None
            response.returned_count = 1 if item else 0
            batch.responses.append(response)
            if item:
                normalized = normalize_crossref(item, response.collected_at)
                if normalized.title:
                    batch.records.append((normalized, response.raw_path))
        batch.api_total = len(batch.records)
        return batch


class UnpaywallClient:
    BASE_URL = "https://api.unpaywall.org/v2"

    def __init__(self, http: JsonHttpClient, email: str, user_agent: str, interval: float):
        self.http = http
        self.email = email
        self.user_agent = user_agent
        self.interval = interval

    def enrich(self, dois: list[str]) -> SourceBatch:
        if not self.email:
            return SourceBatch(skipped_reason="UNPAYWALL_EMAIL is missing")
        batch = SourceBatch()
        for index, doi in enumerate(dois):
            if index and self.interval:
                time.sleep(self.interval)
            response = self.http.request(
                "unpaywall",
                f"doi_{index + 1}",
                "GET",
                f"{self.BASE_URL}/{quote(doi, safe='/')}",
                params={"email": self.email},
                headers={"User-Agent": self.user_agent},
            )
            item = response.data if isinstance(response.data, dict) and not response.error else None
            response.returned_count = 1 if item else 0
            batch.responses.append(response)
            if item:
                normalized = normalize_unpaywall(item, response.collected_at)
                if normalized.title:
                    batch.records.append((normalized, response.raw_path))
        batch.api_total = len(batch.records)
        return batch


def normalize_openalex(item: dict[str, Any], collected_at: str) -> NormalizedWork:
    primary = item.get("primary_location") if isinstance(item.get("primary_location"), dict) else {}
    best_oa = item.get("best_oa_location") if isinstance(item.get("best_oa_location"), dict) else {}
    source = primary.get("source") if isinstance(primary.get("source"), dict) else {}
    open_access = item.get("open_access") if isinstance(item.get("open_access"), dict) else {}
    authors = []
    for authorship in item.get("authorships") or []:
        if isinstance(authorship, dict) and isinstance(authorship.get("author"), dict):
            authors.append(authorship["author"].get("display_name"))
    external_id = str(item.get("id") or "").rsplit("/", 1)[-1]
    doi = normalize_doi(item.get("doi") or (item.get("ids") or {}).get("doi"))
    return NormalizedWork(
        source_api="openalex",
        external_id=external_id or doi,
        title=first_text(item.get("display_name") or item.get("title")),
        document_type=first_text(item.get("type")),
        doi=doi,
        abstract=reconstruct_openalex_abstract(item.get("abstract_inverted_index")),
        authors=unique_text(authors),
        year=_int_or_none(item.get("publication_year")),
        journal=first_text(source.get("display_name")),
        publisher=first_text(source.get("host_organization_name")),
        publication_date=first_text(item.get("publication_date")),
        citation_count=_int_or_none(item.get("cited_by_count")),
        source_url=first_text(item.get("doi") or item.get("id")),
        open_access_status=first_text(open_access.get("oa_status")) or ("open" if open_access.get("is_oa") else "closed"),
        pdf_url=first_text(best_oa.get("pdf_url") or primary.get("pdf_url")),
        html_url=first_text(best_oa.get("landing_page_url") or primary.get("landing_page_url")),
        language=first_text(item.get("language")),
        collected_at=collected_at,
    )


def normalize_semantic_scholar(item: dict[str, Any], collected_at: str) -> NormalizedWork:
    external_ids = item.get("externalIds") if isinstance(item.get("externalIds"), dict) else {}
    pdf = item.get("openAccessPdf") if isinstance(item.get("openAccessPdf"), dict) else {}
    journal = item.get("journal") if isinstance(item.get("journal"), dict) else {}
    authors = [author.get("name") for author in item.get("authors") or [] if isinstance(author, dict)]
    return NormalizedWork(
        source_api="semantic_scholar",
        external_id=first_text(item.get("paperId") or external_ids.get("DOI")),
        title=first_text(item.get("title")),
        document_type=first_text(item.get("publicationTypes")),
        doi=normalize_doi(external_ids.get("DOI")),
        abstract=strip_markup(item.get("abstract")),
        authors=unique_text(authors),
        year=_int_or_none(item.get("year")),
        journal=first_text(item.get("venue") or journal.get("name")),
        publication_date=first_text(item.get("publicationDate")),
        citation_count=_int_or_none(item.get("citationCount")),
        source_url=first_text(item.get("url")),
        open_access_status="open" if item.get("isOpenAccess") else "closed",
        pdf_url=first_text(pdf.get("url")),
        html_url=first_text(item.get("url")),
        collected_at=collected_at,
    )


def normalize_crossref(item: dict[str, Any], collected_at: str) -> NormalizedWork:
    authors = []
    for author in item.get("author") or []:
        if isinstance(author, dict):
            authors.append(" ".join(part for part in (author.get("given"), author.get("family")) if part))
    links = item.get("link") if isinstance(item.get("link"), list) else []
    pdf_url = ""
    html_url = ""
    for link in links:
        if not isinstance(link, dict):
            continue
        content_type = str(link.get("content-type") or "").lower()
        url = first_text(link.get("URL"))
        if "pdf" in content_type and not pdf_url:
            pdf_url = url
        elif "html" in content_type and not html_url:
            html_url = url
    year = first_year(item.get("published-print"), item.get("published-online"), item.get("published"), item.get("created"))
    date_parts = (item.get("published-print") or item.get("published-online") or item.get("published") or {}).get("date-parts", [])
    publication_date = "-".join(str(part).zfill(2) for part in date_parts[0]) if date_parts and date_parts[0] else ""
    doi = normalize_doi(item.get("DOI"))
    return NormalizedWork(
        source_api="crossref",
        external_id=doi,
        title=first_text(item.get("title")),
        document_type=first_text(item.get("type")),
        doi=doi,
        abstract=strip_markup(item.get("abstract")),
        authors=unique_text(authors),
        year=year,
        journal=first_text(item.get("container-title")),
        publisher=first_text(item.get("publisher")),
        publication_date=publication_date,
        citation_count=_int_or_none(item.get("is-referenced-by-count")),
        source_url=first_text(item.get("URL")) or (f"https://doi.org/{doi}" if doi else ""),
        open_access_status="unknown",
        pdf_url=pdf_url,
        html_url=html_url or first_text(item.get("URL")),
        language=first_text(item.get("language")),
        collected_at=collected_at,
    )


def normalize_unpaywall(item: dict[str, Any], collected_at: str) -> NormalizedWork:
    best = item.get("best_oa_location") if isinstance(item.get("best_oa_location"), dict) else {}
    authors = []
    for author in item.get("z_authors") or []:
        if isinstance(author, dict):
            authors.append(" ".join(part for part in (author.get("given"), author.get("family")) if part))
    doi = normalize_doi(item.get("doi"))
    return NormalizedWork(
        source_api="unpaywall",
        external_id=doi,
        title=first_text(item.get("title")),
        document_type=first_text(item.get("genre")),
        doi=doi,
        authors=unique_text(authors),
        year=_int_or_none(item.get("year")),
        journal=first_text(item.get("journal_name")),
        publisher=first_text(item.get("publisher")),
        source_url=f"https://doi.org/{doi}" if doi else "",
        open_access_status=first_text(item.get("oa_status")) or ("open" if item.get("is_oa") else "closed"),
        pdf_url=first_text(best.get("url_for_pdf")),
        html_url=first_text(best.get("url_for_landing_page") or best.get("url")),
        collected_at=collected_at,
    )


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None
