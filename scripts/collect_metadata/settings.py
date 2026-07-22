from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def load_dotenv(path: Path) -> None:
    """Small dotenv reader; existing process environment values take precedence."""

    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if name:
            os.environ.setdefault(name, value)


def _positive_int(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, default))
    except ValueError:
        return default
    return max(1, value)


@dataclass(slots=True)
class Credentials:
    openalex_api_key: str
    semantic_scholar_api_key: str
    crossref_email: str
    unpaywall_email: str
    timeout_seconds: int
    max_retries: int

    @classmethod
    def from_env(cls, env_file: Path) -> "Credentials":
        load_dotenv(env_file)
        return cls(
            openalex_api_key=os.environ.get("OPENALEX_API_KEY", "").strip(),
            semantic_scholar_api_key=(
                os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "").strip()
                or os.environ.get("S2_API_KEY", "").strip()
            ),
            crossref_email=os.environ.get("CROSSREF_EMAIL", "").strip(),
            unpaywall_email=os.environ.get("UNPAYWALL_EMAIL", "").strip(),
            timeout_seconds=_positive_int("HTTP_TIMEOUT_SECONDS", 30),
            max_retries=_positive_int("HTTP_MAX_RETRIES", 4),
        )

    def availability(self) -> dict[str, bool]:
        return {
            "openalex": bool(self.openalex_api_key),
            "semantic_scholar": bool(self.semantic_scholar_api_key),
            "crossref": True,
            "crossref_polite_pool": bool(self.crossref_email),
            "unpaywall": bool(self.unpaywall_email),
        }


@dataclass(slots=True)
class SearchSettings:
    queries: list[dict[str, str]]
    max_results_per_query: int
    max_enrich_records: int
    title_similarity_threshold: float
    title_review_threshold: float
    title_min_length: int
    crossref_interval: float
    unpaywall_interval: float
    enabled_sources: list[str]

    @classmethod
    def from_file(cls, path: Path) -> "SearchSettings":
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        defaults = payload.get("defaults", {})
        queries = []
        for index, item in enumerate(payload.get("queries", []), start=1):
            query = str(item.get("query", "")).strip()
            if query:
                queries.append({"query_id": str(item.get("query_id") or f"query_{index:02d}"), "query": query})
        if not queries:
            raise ValueError(f"No usable queries found in {path}")
        return cls(
            queries=queries,
            max_results_per_query=max(1, int(defaults.get("max_results_per_query", 50))),
            max_enrich_records=max(0, int(defaults.get("max_enrich_records", 200))),
            title_similarity_threshold=float(defaults.get("title_similarity_threshold", 0.97)),
            title_review_threshold=float(defaults.get("title_review_threshold", 0.92)),
            title_min_length=max(1, int(defaults.get("title_min_length", 30))),
            crossref_interval=max(0.0, float(defaults.get("crossref_request_interval_seconds", 0.1))),
            unpaywall_interval=max(0.0, float(defaults.get("unpaywall_request_interval_seconds", 0.1))),
            enabled_sources=[str(item) for item in payload.get("enabled_sources", ["openalex"])],
        )


@dataclass(slots=True)
class Paths:
    root: Path
    env_file: Path
    config_file: Path
    screening_rules_file: Path
    database: Path
    master_csv: Path
    raw_responses: Path
    run_reports: Path

    @classmethod
    def defaults(cls, root: Path = ROOT) -> "Paths":
        metadata = root / "data" / "raw" / "literature" / "metadata"
        return cls(
            root=root,
            env_file=root / ".env",
            config_file=root / "config" / "literature_search.json",
            screening_rules_file=root / "config" / "screening_rules.json",
            database=metadata / "literature.sqlite3",
            master_csv=metadata / "literature_master.csv",
            raw_responses=root / "data/raw/api_responses",
            run_reports=root / "runs/metadata",
        )
