from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from collections import Counter
from contextlib import closing
from pathlib import Path
from typing import Any

from scripts.io_utils import utc_now


ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_VERSION = "screening_benchmark_v1.1"
DEFAULT_COUNTS = {"A": 30, "B": 25, "C": 20, "M": 20, "R": 25}
HUMAN_COLUMNS = [
    "human_is_target_synthesis",
    "human_tier",
    "human_extractability",
    "human_reason",
    "reviewer_notes",
    "error_type",
    "possible_duplicate_missed",
    "reviewer",
    "reviewed_at",
]
OUTPUT_COLUMNS = [
    "benchmark_id",
    "source_id",
    "sample_stratum",
    "sample_reason",
    "title",
    "doi",
    "year",
    "journal",
    "document_type",
    "abstract",
    "auto_tier",
    "auto_topic_score",
    "auto_evidence_score",
    "auto_access_score",
    "auto_reason",
    "auto_positive_reasons",
    "auto_negative_reasons",
    "screening_rule_version",
    "dedup_status",
    "dedup_reasons",
    "conflict_reasons",
    "source_record_count",
    "source_apis",
    *HUMAN_COLUMNS,
]

DEDUP_HUMAN_COLUMNS = [
    "human_merge_correct",
    "human_relation",
    "human_reason",
    "error_type",
    "reviewer",
    "reviewed_at",
]
DEDUP_COLUMNS = [
    "dedup_audit_id", "decision_id", "audit_stratum", "match_type", "decision",
    "similarity", "incoming_source_api", "incoming_external_id", "incoming_title",
    "incoming_doi", "incoming_year", "incoming_document_type", "incoming_authors",
    "incoming_journal", "resolved_source_id", "resolved_title", "resolved_doi",
    "resolved_year", "resolved_document_type", "resolved_authors", "resolved_journal",
    "related_source_id", "related_title", "related_doi", "related_year",
    "related_document_type", "related_authors", "related_journal", "dedup_reasons",
    "conflict_reasons", "dedup_rule_version", *DEDUP_HUMAN_COLUMNS,
]


def portable_path(path: Path) -> str:
    """Return repository-relative paths for artifacts stored in public JSON."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def stable_order(source_id: str, seed: str) -> str:
    return hashlib.sha256(f"{seed}|{source_id}".encode("utf-8")).hexdigest()


def load_existing(path: Path, key: str = "source_id") -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle) if row.get(key)}


def _json_text(value: str) -> str:
    try:
        payload = json.loads(value or "[]")
    except json.JSONDecodeError:
        return value or ""
    if isinstance(payload, list):
        return "; ".join(str(item) for item in payload)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _authors_text(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return str(value or "")


def generate(database: Path, output: Path, seed: str) -> dict[str, Any]:
    existing = load_existing(output)
    with closing(sqlite3.connect(database)) as connection:
        connection.row_factory = sqlite3.Row
        rows = [dict(row) for row in connection.execute(
            """
            SELECT w.*,
                   COUNT(r.external_id) AS source_record_count,
                   GROUP_CONCAT(DISTINCT r.source_api) AS source_apis
            FROM works AS w
            LEFT JOIN work_source_records AS r ON r.source_id = w.source_id
            GROUP BY w.source_id
            """
        )]

    by_tier: dict[str, list[dict[str, Any]]] = {tier: [] for tier in DEFAULT_COUNTS}
    for row in rows:
        tier = str(row.get("priority_tier") or "")
        if tier in by_tier:
            by_tier[tier].append(row)

    selected: dict[str, tuple[dict[str, Any], str, str]] = {}
    for tier, count in DEFAULT_COUNTS.items():
        ordered = sorted(by_tier[tier], key=lambda row: stable_order(str(row["source_id"]), seed))
        for row in ordered[:count]:
            selected[str(row["source_id"])] = (row, tier, f"stratified_tier_{tier}")

    for row in rows:
        if row.get("dedup_status") != "needs_review":
            continue
        source_id = str(row["source_id"])
        if source_id in selected:
            current, stratum, reason = selected[source_id]
            selected[source_id] = (current, stratum, reason + "; dedup_review_all")
        else:
            selected[source_id] = (row, "DEDUP_REVIEW", "dedup_review_all")

    output.parent.mkdir(parents=True, exist_ok=True)
    rendered: list[dict[str, Any]] = []
    for source_id, (row, stratum, reason) in sorted(
        selected.items(), key=lambda item: (item[1][1], stable_order(item[0], seed))
    ):
        old = existing.get(source_id, {})
        human = {column: old.get(column, "") for column in HUMAN_COLUMNS}
        if not human["human_is_target_synthesis"] and old.get("human_include"):
            human["human_is_target_synthesis"] = {
                "include": "yes",
                "exclude": "no",
                "indeterminate": "indeterminate",
            }.get(old["human_include"].strip().lower(), old["human_include"])
        rendered.append(
            {
                "benchmark_id": f"BM_{hashlib.sha256((BENCHMARK_VERSION + '|' + source_id).encode()).hexdigest()[:16].upper()}",
                "source_id": source_id,
                "sample_stratum": stratum,
                "sample_reason": reason,
                "title": row.get("title") or "",
                "doi": row.get("doi") or "",
                "year": row.get("year") or "",
                "journal": row.get("journal") or "",
                "document_type": row.get("document_type") or "",
                "abstract": row.get("abstract") or "",
                "auto_tier": row.get("priority_tier") or "",
                "auto_topic_score": row.get("topic_relevance_score") or 0,
                "auto_evidence_score": row.get("metadata_evidence_likelihood_score") or 0,
                "auto_access_score": row.get("access_score") or 0,
                "auto_reason": row.get("priority_tier_reason") or "",
                "auto_positive_reasons": _json_text(str(row.get("topic_positive_reasons_json") or "[]")),
                "auto_negative_reasons": _json_text(str(row.get("topic_negative_reasons_json") or "[]")),
                "screening_rule_version": row.get("screening_rule_version") or "",
                "dedup_status": row.get("dedup_status") or "",
                "dedup_reasons": _json_text(str(row.get("dedup_reasons_json") or "[]")),
                "conflict_reasons": _json_text(str(row.get("conflict_reasons_json") or "[]")),
                "source_record_count": row.get("source_record_count") or 0,
                "source_apis": row.get("source_apis") or "",
                **human,
            }
        )
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rendered)
    return {
        "benchmark_version": BENCHMARK_VERSION,
        "generated_at": utc_now(),
        "seed": seed,
        "rows": len(rendered),
        "sample_distribution": dict(Counter(row["sample_stratum"] for row in rendered)),
        "tier_population": {tier: len(items) for tier, items in by_tier.items()},
        "preserved_review_rows": sum(
            1 for row in rendered if any(row[column] for column in HUMAN_COLUMNS)
        ),
        "output": portable_path(output),
    }


def generate_dedup_audit(
    database: Path,
    output: Path,
    seed: str,
    doi_count: int = 15,
    external_id_count: int = 5,
) -> dict[str, Any]:
    existing = load_existing(output, "decision_id")
    with closing(sqlite3.connect(database)) as connection:
        connection.row_factory = sqlite3.Row
        decisions = [dict(row) for row in connection.execute(
            "SELECT * FROM dedup_decision_log ORDER BY decision_id"
        )]
        works = {
            str(row["source_id"]): dict(row)
            for row in connection.execute("SELECT * FROM works")
        }
        source_records: dict[tuple[str, str], dict[str, Any]] = {}
        for row in connection.execute(
            "SELECT source_api,external_id,normalized_json FROM work_source_records"
        ):
            try:
                payload = json.loads(str(row["normalized_json"] or "{}"))
            except json.JSONDecodeError:
                payload = {}
            source_records[(str(row["source_api"]), str(row["external_id"]))] = payload

    auto_by_type: dict[str, dict[str, dict[str, Any]]] = {
        match_type: {} for match_type in ("external_id", "doi", "title_exact", "title_fuzzy")
    }


    for row in decisions:
        match_type = str(row.get("match_type") or "")
        if row.get("decision") != "auto_merge" or match_type not in auto_by_type:
            continue
        group_key = str(row.get("resolved_source_id") or row.get("decision_id"))
        auto_by_type[match_type].setdefault(group_key, row)

    selected: list[tuple[dict[str, Any], str]] = []
    for match_type, requested, label in (
        ("external_id", external_id_count, "external_id_sample"),
        ("doi", doi_count, "doi_sample"),
    ):
        groups = list(auto_by_type[match_type].items())
        groups.sort(key=lambda item: stable_order(item[0], f"{seed}|dedup|{match_type}"))
        selected.extend((row, label) for _, row in groups[:requested])
    for match_type in ("title_exact", "title_fuzzy"):
        groups = sorted(auto_by_type[match_type].items(), key=lambda item: item[0])
        selected.extend((row, f"{match_type}_all") for _, row in groups)
    selected.extend(
        (row, "conflict_review_all")
        for row in decisions
        if row.get("decision") == "review_required"
    )

    def work_fields(source_id: str, prefix: str) -> dict[str, Any]:
        row = works.get(source_id, {})
        return {
            f"{prefix}_source_id": source_id,
            f"{prefix}_title": row.get("title") or "",
            f"{prefix}_doi": row.get("doi") or "",
            f"{prefix}_year": row.get("year") or "",
            f"{prefix}_document_type": row.get("document_type") or "",
            f"{prefix}_authors": _authors_text(row.get("authors")),
            f"{prefix}_journal": row.get("journal") or "",
        }

    rendered: list[dict[str, Any]] = []
    for row, stratum in selected:
        decision_id = str(row["decision_id"])
        old = existing.get(decision_id, {})
        incoming = source_records.get(
            (str(row.get("incoming_source_api") or ""), str(row.get("incoming_external_id") or "")),
            {},
        )
        resolved_id = str(row.get("resolved_source_id") or "")
        related_id = str(row.get("related_source_id") or "")
        rendered.append({
            "dedup_audit_id": f"DA_{hashlib.sha256((BENCHMARK_VERSION + '|' + decision_id).encode()).hexdigest()[:16].upper()}",
            "decision_id": decision_id,
            "audit_stratum": stratum,
            "match_type": row.get("match_type") or "",
            "decision": row.get("decision") or "",
            "similarity": row.get("similarity") if row.get("similarity") is not None else "",
            "incoming_source_api": row.get("incoming_source_api") or "",
            "incoming_external_id": row.get("incoming_external_id") or "",
            "incoming_title": incoming.get("title") or row.get("incoming_title") or "",
            "incoming_doi": incoming.get("doi") or row.get("incoming_doi") or "",
            "incoming_year": incoming.get("year") or "",
            "incoming_document_type": incoming.get("document_type") or "",
            "incoming_authors": _authors_text(incoming.get("authors")),
            "incoming_journal": incoming.get("journal") or "",
            **work_fields(resolved_id, "resolved"),
            **work_fields(related_id, "related"),
            "dedup_reasons": _json_text(str(row.get("dedup_reasons_json") or "[]")),
            "conflict_reasons": _json_text(str(row.get("conflict_reasons_json") or "[]")),
            "dedup_rule_version": row.get("dedup_rule_version") or "",
            **{column: old.get(column, "") for column in DEDUP_HUMAN_COLUMNS},
        })

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DEDUP_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rendered)
    return {
        "rows": len(rendered),
        "audit_distribution": dict(Counter(row["audit_stratum"] for row in rendered)),
        "auto_merge_group_population": {
            match_type: len(groups) for match_type, groups in auto_by_type.items()
        },
        "preserved_review_rows": sum(
            1 for row in rendered if any(row[column] for column in DEDUP_HUMAN_COLUMNS)
        ),
        "output": portable_path(output),
    }


def refresh_predictions(database: Path, input_csv: Path) -> dict[str, Any]:
    with input_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or OUTPUT_COLUMNS)
    with closing(sqlite3.connect(database)) as connection:
        connection.row_factory = sqlite3.Row
        works = {
            str(row["source_id"]): dict(row)
            for row in connection.execute("SELECT * FROM works")
        }
    missing = sorted({row["source_id"] for row in rows} - set(works))
    if missing:
        raise RuntimeError(
            f"Benchmark source IDs missing from metadata database: {missing}"
        )
    for row in rows:
        work = works[row["source_id"]]
        row.update(
            {
                "title": work.get("title") or "",
                "doi": work.get("doi") or "",
                "year": work.get("year") or "",
                "journal": work.get("journal") or "",
                "document_type": work.get("document_type") or "",
                "abstract": work.get("abstract") or "",
                "auto_tier": work.get("priority_tier") or "",
                "auto_topic_score": work.get("topic_relevance_score") or 0,
                "auto_evidence_score": work.get(
                    "metadata_evidence_likelihood_score"
                )
                or 0,
                "auto_access_score": work.get("access_score") or 0,
                "auto_reason": work.get("priority_tier_reason") or "",
                "auto_positive_reasons": _json_text(
                    str(work.get("topic_positive_reasons_json") or "[]")
                ),
                "auto_negative_reasons": _json_text(
                    str(work.get("topic_negative_reasons_json") or "[]")
                ),
                "screening_rule_version": work.get("screening_rule_version")
                or "",
                "dedup_status": work.get("dedup_status") or "",
                "dedup_reasons": _json_text(
                    str(work.get("dedup_reasons_json") or "[]")
                ),
                "conflict_reasons": _json_text(
                    str(work.get("conflict_reasons_json") or "[]")
                ),
            }
        )
    with input_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    return {
        "refreshed_rows": len(rows),
        "screening_rule_versions": dict(
            Counter(row["screening_rule_version"] for row in rows)
        ),
        "prediction_distribution": dict(
            Counter(
                row["auto_tier"]
                for row in rows
                if row.get("sample_stratum") in DEFAULT_COUNTS
            )
        ),
        "output": portable_path(input_csv),
    }


def _review_label(value: str) -> str | None:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "include"}:
        return "include"
    if normalized in {"0", "false", "no", "n", "exclude"}:
        return "exclude"
    if normalized in {"indeterminate", "uncertain", "cannot_determine"}:
        return "indeterminate"
    return None


def _merge_label(value: str) -> str | None:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "correct"}:
        return "correct"
    if normalized in {"0", "false", "no", "n", "incorrect"}:
        return "incorrect"
    if normalized in {"indeterminate", "uncertain"}:
        return "indeterminate"
    return None


def _screening_row_complete(row: dict[str, str]) -> bool:
    return all((
        _review_label(row.get("human_is_target_synthesis", "")) is not None,
        row.get("human_tier", "").strip() in DEFAULT_COUNTS,
        row.get("human_extractability", "").strip().lower() in {
            "extractable",
            "possibly_extractable",
            "source_observation_only",
            "background_reference",
            "not_extractable",
            "indeterminate",
        },
        bool(row.get("human_reason", "").strip()),
        bool(row.get("reviewer", "").strip()),
        bool(row.get("reviewed_at", "").strip()),
    ))


def _dedup_row_complete(row: dict[str, str]) -> bool:
    return all((
        _merge_label(row.get("human_merge_correct", "")) in {"correct", "incorrect"},
        row.get("human_relation", "").strip().lower() in {
            "same_work",
            "distinct_work",
            "version_relation",
            "indeterminate",
        },
        bool(row.get("reviewer", "").strip()),
        bool(row.get("reviewed_at", "").strip()),
    ))


def summarize(
    input_csv: Path,
    dedup_csv: Path,
    database: Path,
    manifest_json: Path,
    output_json: Path,
    errors_csv: Path,
) -> dict[str, Any]:
    with input_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    with dedup_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        dedup_rows = list(csv.DictReader(handle))
    design_manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    design_population = {
        str(tier): int(count) for tier, count in design_manifest["tier_population"].items()
    }
    with closing(sqlite3.connect(database)) as connection:
        current_population = {
            str(tier): int(count)
            for tier, count in connection.execute(
                "SELECT priority_tier,COUNT(*) FROM works GROUP BY priority_tier"
            )
        }
        dedup_population = {
            str(match_type): int(count)
            for match_type, count in connection.execute(
                """
                SELECT match_type,COUNT(DISTINCT resolved_source_id)
                FROM dedup_decision_log
                WHERE decision='auto_merge'
                GROUP BY match_type
                """
            )
        }
    stratified = [row for row in rows if row.get("sample_stratum") in DEFAULT_COUNTS]
    by_tier = {
        tier: [row for row in stratified if row.get("sample_stratum") == tier]
        for tier in DEFAULT_COUNTS
    }

    def ratio(numerator: float, denominator: float) -> float | None:
        return round(numerator / denominator, 4) if denominator else None

    tier_stats: dict[str, dict[str, Any]] = {}
    weighted_targets: dict[str, float] = {}
    for tier, tier_rows in by_tier.items():
        completed_rows = [row for row in tier_rows if _screening_row_complete(row)]
        labels = [
            _review_label(row.get("human_is_target_synthesis", "")) for row in completed_rows
        ]
        counts = Counter(label for label in labels if label)
        sample_size = len(tier_rows)
        weight = design_population.get(tier, 0) / sample_size if sample_size else 0.0
        weighted_targets[tier] = counts["include"] * weight
        tier_stats[tier] = {
            "population": design_population.get(tier, 0),
            "sample_size": sample_size,
            "weight": round(weight, 6),
            "reviewed": len(completed_rows),
            "include": counts["include"],
            "exclude": counts["exclude"],
            "indeterminate": counts["indeterminate"],
            "weighted_target_estimate": round(weighted_targets[tier], 4),
            "complete": len(completed_rows) == sample_size,
        }

    all_complete = all(stats["complete"] for stats in tier_stats.values())
    completed_stratified = [row for row in stratified if _screening_row_complete(row)]
    sample_weights = {
        tier: (design_population.get(tier, 0) / len(by_tier[tier]) if by_tier[tier] else 0.0)
        for tier in DEFAULT_COUNTS
    }

    def row_weight(row: dict[str, str]) -> float:
        return sample_weights.get(row.get("sample_stratum", ""), 0.0)

    def weighted_count(predicate: Any) -> float:
        return sum(row_weight(row) for row in completed_stratified if predicate(row))

    target_weight = weighted_count(
        lambda row: _review_label(row.get("human_is_target_synthesis", "")) == "include"
    )
    predicted_a_weight = weighted_count(lambda row: row.get("auto_tier") == "A")
    predicted_ab_weight = weighted_count(lambda row: row.get("auto_tier") in {"A", "B"})
    predicted_r_weight = weighted_count(lambda row: row.get("auto_tier") == "R")
    predicted_m_weight = weighted_count(lambda row: row.get("auto_tier") == "M")
    a_precision = (
        ratio(weighted_count(lambda row: row.get("auto_tier") == "A" and _review_label(row.get("human_is_target_synthesis", "")) == "include"), predicted_a_weight)
        if all_complete else None
    )
    ab_recall = (
        ratio(weighted_count(lambda row: row.get("auto_tier") in {"A", "B"} and _review_label(row.get("human_is_target_synthesis", "")) == "include"), target_weight)
        if all_complete else None
    )
    r_false_kill = (
        ratio(weighted_count(lambda row: row.get("auto_tier") == "R" and _review_label(row.get("human_is_target_synthesis", "")) == "include"), predicted_r_weight)
        if all_complete else None
    )
    ab_non_target = (
        ratio(weighted_count(lambda row: row.get("auto_tier") in {"A", "B"} and _review_label(row.get("human_is_target_synthesis", "")) == "exclude"), predicted_ab_weight)
        if all_complete else None
    )
    m_indeterminate = (
        ratio(weighted_count(lambda row: row.get("auto_tier") == "M" and _review_label(row.get("human_is_target_synthesis", "")) == "indeterminate"), predicted_m_weight)
        if all_complete else None
    )
    r_false_kill_sample_count = (
        sum(
            row.get("auto_tier") == "R"
            and _review_label(row.get("human_is_target_synthesis", "")) == "include"
            for row in completed_stratified
        ) if all_complete else None
    )
    predicted_r_sample_count = sum(row.get("auto_tier") == "R" for row in completed_stratified)
    r_rule_of_three_upper = (
        round(3 / predicted_r_sample_count, 4)
        if all_complete and r_false_kill_sample_count == 0 and predicted_r_sample_count else None
    )
    if not all_complete:
        r_action = "pending_review"
    else:
        assert r_false_kill_sample_count is not None
        if r_false_kill_sample_count >= 2:
            r_action = "modify_rules_before_release"
        elif r_false_kill_sample_count == 1:
            r_action = "analyze_error_and_expand_R_sample"
        else:
            r_action = "expand_R_boundary_sample_by_50_to_75_before_declaring_stable"

    dedup_by_reason: dict[str, dict[str, Any]] = {}
    for match_type in ("external_id", "doi", "title_exact", "title_fuzzy"):
        reason_rows = [
            row for row in dedup_rows
            if row.get("decision") == "auto_merge" and row.get("match_type") == match_type
        ]
        completed_rows = [row for row in reason_rows if _dedup_row_complete(row)]
        labels = [_merge_label(row.get("human_merge_correct", "")) for row in completed_rows]
        reviewed_labels = [label for label in labels if label in {"correct", "incorrect"}]
        false_merges = sum(label == "incorrect" for label in reviewed_labels)
        dedup_by_reason[match_type] = {
            "population_groups": dedup_population.get(match_type, 0),
            "audit_rows": len(reason_rows),
            "reviewed": len(completed_rows),
            "false_merges": false_merges,
            "false_merge_rate": ratio(false_merges, len(reviewed_labels)),
            "all_groups_in_audit": len(reason_rows) == dedup_population.get(match_type, 0)
            if match_type in {"title_exact", "title_fuzzy"} else False,
        }
    fuzzy = dedup_by_reason["title_fuzzy"]
    if fuzzy["population_groups"] == 0:
        fuzzy_gate = "not_applicable_no_fuzzy_auto_merges"
    elif fuzzy["reviewed"] < fuzzy["audit_rows"]:
        fuzzy_gate = "pending"
    elif fuzzy["false_merges"] == 0:
        fuzzy_gate = "pass"
    else:
        fuzzy_gate = "fail"

    def dedup_gate(match_type: str) -> str:
        stats = dedup_by_reason[match_type]
        if stats["population_groups"] == 0:
            return "not_applicable_no_auto_merges"
        if stats["reviewed"] < stats["audit_rows"]:
            return "pending"
        return "pass" if stats["false_merges"] == 0 else "fail"

    conflict_rows = [row for row in dedup_rows if row.get("decision") == "review_required"]
    completed_conflicts = [row for row in conflict_rows if _dedup_row_complete(row)]
    incorrect_conflict_decisions = sum(
        _merge_label(row.get("human_merge_correct", "")) == "incorrect"
        for row in completed_conflicts
    )
    if len(completed_conflicts) < len(conflict_rows):
        conflict_gate = "pending"
    else:
        conflict_gate = "pass" if incorrect_conflict_decisions == 0 else "fail"

    def threshold_status(value: float | None, threshold: float, direction: str) -> str:
        if value is None:
            return "pending"
        passed = value >= threshold if direction == "min" else value <= threshold
        return "pass" if passed else "fail"

    reviewed_stratified = sum(stats["reviewed"] for stats in tier_stats.values())
    r_false_kill_count = r_false_kill_sample_count
    release_gates = {
        "A_precision_gte_0.85": threshold_status(a_precision, 0.85, "min"),
        "AB_weighted_recall_gte_0.90": threshold_status(ab_recall, 0.90, "min"),
        "R_false_kill_lte_0.05": threshold_status(r_false_kill, 0.05, "max"),
        "R_false_kill_count_lte_1": threshold_status(r_false_kill_count, 1, "max"),
        "external_id_auto_merge_no_error": dedup_gate("external_id"),
        "doi_auto_merge_no_error": dedup_gate("doi"),
        "doi_conflict_decisions_correct": conflict_gate,
    }
    required_gate_values = list(release_gates.values())
    if any(value == "fail" for value in required_gate_values):
        benchmark_decision = "fail_export_errors_and_revise_rules"
    elif any(value == "pending" for value in required_gate_values):
        benchmark_decision = "pending_review"
    else:
        benchmark_decision = "pass_freeze_and_start_30_fulltext_pilot"
    summary = {
        "benchmark_version": BENCHMARK_VERSION,
        "summarized_at": utc_now(),
        "screening_sample_rows": len(rows),
        "stratified_sample_rows": len(stratified),
        "special_screening_rows": len(rows) - len(stratified),
        "reviewed_stratified_rows": reviewed_stratified,
        "review_completion": ratio(reviewed_stratified, len(stratified)),
        "sampling_design_rule_version": design_manifest.get("benchmark_version", ""),
        "sampling_design_population": design_population,
        "current_corpus_tier_population": current_population,
        "A_precision": a_precision,
        "AB_target_recall_weighted_estimate": ab_recall,
        "R_false_kill_rate": r_false_kill,
        "R_false_kill_count": r_false_kill_count,
        "R_rule_of_three_95pct_upper_if_zero": r_rule_of_three_upper,
        "R_followup_action": r_action,
        "AB_obvious_non_target_rate": ab_non_target,
        "M_indeterminate_rate": m_indeterminate,
        "tier_statistics": tier_stats,
        "prediction_statistics": {
            tier: {
                "sample_count": sum(row.get("auto_tier") == tier for row in completed_stratified),
                "weighted_population_estimate": round(weighted_count(lambda row, value=tier: row.get("auto_tier") == value), 4),
                "weighted_target_estimate": round(weighted_count(lambda row, value=tier: row.get("auto_tier") == value and _review_label(row.get("human_is_target_synthesis", "")) == "include"), 4),
                "weighted_non_target_estimate": round(weighted_count(lambda row, value=tier: row.get("auto_tier") == value and _review_label(row.get("human_is_target_synthesis", "")) == "exclude"), 4),
            }
            for tier in DEFAULT_COUNTS
        },
        "weighted_target_estimates": {tier: round(value, 4) for tier, value in weighted_targets.items()},
        "dedup_audit_rows": len(dedup_rows),
        "dedup_by_match_type": dedup_by_reason,
        "dedup_conflict_review": {
            "rows": len(conflict_rows),
            "reviewed": len(completed_conflicts),
            "incorrect_decisions": incorrect_conflict_decisions,
        },
        "release_gates": release_gates,
        "diagnostic_gates": {
            "title_fuzzy_false_merge_eq_0": fuzzy_gate,
            "AB_obvious_non_target_lte_0.10": threshold_status(ab_non_target, 0.10, "max"),
            "M_indeterminate_rate": "informational",
        },
        "benchmark_decision": benchmark_decision,
        "error_type_distribution": dict(Counter(
            row["error_type"] for row in stratified
            if _screening_row_complete(row) and row.get("error_type")
        )),
        "note": (
            "Release metrics remain null until every corresponding stratum is reviewed. "
            "Indeterminate records are reported separately and are not counted as target papers."
        ),
    }
    error_rows: list[dict[str, Any]] = []
    for row in completed_stratified:
        label = _review_label(row.get("human_is_target_synthesis", ""))
        classes: list[str] = []
        if label == "include" and row.get("auto_tier") not in {"A", "B"}:
            classes.append("false_negative_target")
        if label == "exclude" and row.get("auto_tier") in {"A", "B"}:
            classes.append("false_positive_candidate")
        if label == "include" and row.get("auto_tier") == "R":
            classes.append("R_false_kill")
        if row.get("human_tier") and row.get("human_tier") != row.get("auto_tier"):
            classes.append("tier_disagreement")
        if not classes:
            continue
        error_rows.append({
            "source_id": row.get("source_id", ""),
            "title": row.get("title", ""),
            "doi": row.get("doi", ""),
            "sample_stratum": row.get("sample_stratum", ""),
            "sample_weight": round(row_weight(row), 6),
            "auto_tier": row.get("auto_tier", ""),
            "human_is_target_synthesis": row.get("human_is_target_synthesis", ""),
            "human_tier": row.get("human_tier", ""),
            "human_extractability": row.get("human_extractability", ""),
            "error_class": ";".join(classes),
            "error_type": row.get("error_type", ""),
            "human_reason": row.get("human_reason", ""),
            "auto_reason": row.get("auto_reason", ""),
            "screening_rule_version": row.get("screening_rule_version", ""),
        })
    error_fields = [
        "source_id", "title", "doi", "sample_stratum", "sample_weight", "auto_tier",
        "human_is_target_synthesis", "human_tier", "human_extractability", "error_class",
        "error_type", "human_reason", "auto_reason", "screening_rule_version",
    ]
    errors_csv.parent.mkdir(parents=True, exist_ok=True)
    with errors_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=error_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(error_rows)
    summary["error_case_rows"] = len(error_rows)
    summary["dynamic_error_class_distribution"] = dict(Counter(
        error_class for row in error_rows for error_class in row["error_class"].split(";")
    ))
    summary["errors_csv"] = portable_path(errors_csv)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create and score a reproducible evidence-review screening benchmark.")
    parser.add_argument("--database", type=Path, default=ROOT / "data/raw/metadata/literature.sqlite3")
    parser.add_argument("--csv", type=Path, default=ROOT / "data/review/screening_benchmark/screening_benchmark.csv")
    parser.add_argument("--dedup-csv", type=Path, default=ROOT / "data/review/screening_benchmark/dedup_audit.csv")
    parser.add_argument("--summary", type=Path, default=ROOT / "data/review/screening_benchmark/benchmark_metrics.json")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/review/screening_benchmark/benchmark_manifest.json")
    parser.add_argument("--errors-csv", type=Path, default=ROOT / "data/review/screening_benchmark/benchmark_errors.csv")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("generate")
    create.add_argument("--seed", default="cnt-patsight-benchmark-v1")
    create.add_argument("--doi-audit-count", type=int, default=15)
    create.add_argument("--external-id-audit-count", type=int, default=5)
    sub.add_parser("refresh", help="Refresh automatic predictions without resampling or changing reviewer labels.")
    sub.add_parser("summarize")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "generate":
        result = generate(args.database.resolve(), args.csv.resolve(), args.seed)
        result["dedup_audit"] = generate_dedup_audit(
            args.database.resolve(),
            args.dedup_csv.resolve(),
            args.seed,
            max(0, args.doi_audit_count),
            max(0, args.external_id_audit_count),
        )
        args.manifest.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.manifest.resolve().write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    elif args.command == "refresh":
        result = refresh_predictions(args.database.resolve(), args.csv.resolve())
    else:
        result = summarize(
            args.csv.resolve(),
            args.dedup_csv.resolve(),
            args.database.resolve(),
            args.manifest.resolve(),
            args.summary.resolve(),
            args.errors_csv.resolve(),
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
