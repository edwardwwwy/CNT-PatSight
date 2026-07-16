from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


DOI_PREFIX_RE = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.I)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
NON_WORD_RE = re.compile(r"[^a-z0-9]+")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_doi(value: Any) -> str:
    if not value:
        return ""
    doi = DOI_PREFIX_RE.sub("", str(value).strip()).strip().lower()
    return doi.rstrip(".,; ")


def normalize_title(value: Any) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", html.unescape(str(value))).encode("ascii", "ignore").decode("ascii")
    return SPACE_RE.sub(" ", NON_WORD_RE.sub(" ", text.lower())).strip()


def stable_source_id(doi: str, title: str, year: int | None) -> str:
    identity = f"doi:{normalize_doi(doi)}" if doi else f"title:{normalize_title(title)}|year:{year or ''}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16].upper()
    return f"LIT_{digest}"


def strip_markup(value: Any) -> str:
    if not value:
        return ""
    text = TAG_RE.sub(" ", str(value))
    return SPACE_RE.sub(" ", html.unescape(text)).strip()


def first_text(value: Any) -> str:
    if isinstance(value, list):
        return str(value[0]).strip() if value else ""
    return str(value).strip() if value is not None else ""


def first_year(*date_parts: Any) -> int | None:
    for item in date_parts:
        try:
            if isinstance(item, dict):
                parts = item.get("date-parts") or []
                if parts and parts[0]:
                    return int(parts[0][0])
            elif item:
                match = re.search(r"\b(18|19|20)\d{2}\b", str(item))
                if match:
                    return int(match.group(0))
        except (TypeError, ValueError, IndexError):
            continue
    return None


def reconstruct_openalex_abstract(index: Any) -> str:
    if not isinstance(index, dict):
        return ""
    positions: list[tuple[int, str]] = []
    for token, offsets in index.items():
        if not isinstance(offsets, list):
            continue
        for offset in offsets:
            if isinstance(offset, int):
                positions.append((offset, str(token)))
    return " ".join(token for _, token in sorted(positions))


def unique_text(values: Iterable[Any]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        text = SPACE_RE.sub(" ", str(value or "")).strip()
        key = text.casefold()
        if text and key not in seen:
            seen.add(key)
            output.append(text)
    return output


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def redact_url(url: str) -> str:
    """Remove credentials and personal email parameters from archived request metadata."""

    parts = urlsplit(url)
    sensitive = {"api_key", "apikey", "key", "token", "access_token", "email", "mailto"}
    query = [(key, "<redacted>" if key.lower() in sensitive else value) for key, value in parse_qsl(parts.query)]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

