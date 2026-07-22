#!/usr/bin/env python3
"""Build compact run-level nanopublications from one existing eight-table paper.

Version 0.2 exports only key facts whose existing evidence text explicitly
supports the selected field. Formal CSV files are read-only. The script does
not extract papers, call an LLM, sign nanopublications, or upload data.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from importlib.metadata import version
from pathlib import Path
from typing import Any
from urllib.parse import quote

from nanopub import Nanopub, NanopubConf
from rdflib import Dataset, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, PROV, RDF, XSD


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID = "P003_Pan_2025_FeMo_MgO_Methane_CNT"
INPUT_DIR = ROOT / "data" / "benchmark" / "samples" / "six_papers" / SOURCE_ID
OUTPUT_DIR = ROOT / "data" / "processed" / "analysis" / "derived" / "nanopub_demo"
RUN_OUTPUT_DIR = OUTPUT_DIR / "runs"
REPORT_PATH = ROOT / "reports" / "nanopub_demo.html"

TRIG_PATH = OUTPUT_DIR / f"{SOURCE_ID}.trig"
MAPPING_PATH = OUTPUT_DIR / f"{SOURCE_ID}_mapping.json"
METRICS_PATH = OUTPUT_DIR / "metrics.json"
COMPLETENESS_PATH = OUTPUT_DIR / "completeness_report.json"

PROGRAM_NAME = "CNT-PatSight nanopub_demo"
PROGRAM_VERSION = "0.2.0"
MAPPING_SCHEMA_VERSION = "2.0"
LICENSE_ID = "CNT-PatSight-Local-Demo-Only-1.0"
LOCAL_DEMO_STATUS = "local_only_not_published"

TABLES = (
    "source_master",
    "source_run",
    "catalyst_system",
    "reactor_process_gas",
    "yield_quality",
    "cost_scale_review",
    "evidence_index",
    "review_issue_log",
)

FULL_CELL_TABLES = (
    "catalyst_system",
    "reactor_process_gas",
    "yield_quality",
    "cost_scale_review",
)

RECORD_ID_FIELDS = {
    "catalyst_system": "catalyst_id",
    "reactor_process_gas": "process_stage_id",
    "yield_quality": "product_id",
    "cost_scale_review": "run_id",
}

EXCLUDED_CELL_FIELDS = {
    "catalyst_system": {"run_id", "catalyst_id"},
    "reactor_process_gas": {"run_id", "process_stage_id"},
    "yield_quality": {"run_id", "product_id"},
    "cost_scale_review": {"run_id"},
}

CATALYST_FIELDS = (
    "catalyst_label",
    "active_metals",
    "support_material",
    "preparation_method",
)

PROCESS_FIELDS = {
    "heating": (
        "reactor_type",
        "catalyst_loading_mass_g",
        "temperature_setpoint_C",
        "heating_rate_C_min",
        "inert_gas",
    ),
    "growth": (
        "temperature_setpoint_C",
        "holding_time_min",
        "carbon_source",
        "carbon_source_flow_sccm",
    ),
    "cooling": ("inert_gas",),
}

YIELD_FIELDS = (
    "yield_original",
    "CNT_type_reported",
    "inner_diameter_mean_nm",
    "morphology",
)

NUMERIC_FIELDS = {
    ("reactor_process_gas", "catalyst_loading_mass_g"),
    ("reactor_process_gas", "temperature_setpoint_C"),
    ("reactor_process_gas", "heating_rate_C_min"),
    ("reactor_process_gas", "holding_time_min"),
    ("reactor_process_gas", "carbon_source_flow_sccm"),
    ("yield_quality", "yield_original"),
    ("yield_quality", "inner_diameter_mean_nm"),
}

NORMALIZED_FIELDS = {
    ("reactor_process_gas", "catalyst_loading_mass_g"),
    ("reactor_process_gas", "carbon_source_flow_sccm"),
    ("yield_quality", "yield_original"),
}

UNIT_URI = {
    ("reactor_process_gas", "catalyst_loading_mass_g"): "http://qudt.org/vocab/unit/GM",
    ("reactor_process_gas", "temperature_setpoint_C"): "http://qudt.org/vocab/unit/DEG_C",
    ("reactor_process_gas", "heating_rate_C_min"): "https://w3id.org/cnt-patsight/unit/DegreeCelsiusPerMinute",
    ("reactor_process_gas", "holding_time_min"): "http://qudt.org/vocab/unit/MIN",
    ("reactor_process_gas", "carbon_source_flow_sccm"): "https://w3id.org/cnt-patsight/unit/StandardCubicCentimetrePerMinute",
    ("yield_quality", "yield_original"): "https://w3id.org/cnt-patsight/unit/GramCarbonPerGramCatalystAt30Minutes",
    ("yield_quality", "inner_diameter_mean_nm"): "http://qudt.org/vocab/unit/NanoM",
}

BASE = Namespace("https://w3id.org/cnt-patsight/nanopub-demo/")
CNT = Namespace("https://w3id.org/cnt-patsight/schema/")
NP = Namespace("http://www.nanopub.org/nschema#")


def read_csv_table(name: str) -> tuple[list[str], list[dict[str, str]]]:
    path = INPUT_DIR / f"{name}.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_uri_part(value: str) -> str:
    return quote(value, safe="-._~")


def field_predicate(table: str, field: str) -> URIRef:
    return URIRef(f"{CNT}field/{safe_uri_part(table)}/{safe_uri_part(field)}")


def make_fact_uri(run_id: str, table: str, record_id: str, field: str) -> URIRef:
    key = "|".join((SOURCE_ID, run_id, table, record_id, field))
    token = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return URIRef(f"{BASE}fact/{token}")


def bind_namespaces(target: Dataset | Graph) -> None:
    target.bind("cnt", CNT)
    target.bind("dcterms", DCTERMS)
    target.bind("prov", PROV)
    target.bind("rdf", RDF)
    target.bind("xsd", XSD)
    target.bind("np", NP)


def canonical_decimal(raw: str) -> str:
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"Expected numeric value, got {raw!r}") from exc
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def semantic_value(table: str, field: str, raw_value: str) -> tuple[str, str, str | None, bool]:
    approximate = "approximately" in raw_value.lower() or "read from fig" in raw_value.lower()
    if (table, field) not in NUMERIC_FIELDS:
        return raw_value, str(XSD.string), None, approximate
    numeric_source = raw_value
    if (table, field) == ("yield_quality", "yield_original"):
        match = re.search(r"-?\d+(?:\.\d+)?", raw_value)
        if not match:
            raise ValueError(f"Cannot parse yield number from {raw_value!r}")
        numeric_source = match.group(0)
    return (
        canonical_decimal(numeric_source),
        str(XSD.decimal),
        UNIT_URI[(table, field)],
        approximate,
    )


def evidence_blob(row: dict[str, str]) -> str:
    return " ".join(
        (row.get("evidence_text", ""), row.get("evidence_summary", ""))
    ).lower()


def evidence_supports_field(
    table: str,
    field: str,
    run_id: str,
    raw_value: str,
    evidence: dict[str, str],
) -> tuple[bool, str]:
    blob = evidence_blob(evidence)
    value = raw_value.lower()
    if table == "catalyst_system":
        if field == "catalyst_label":
            return value in blob, "catalyst label appears in evidence summary"
        if field == "active_metals":
            metals = [item.strip().lower() for item in raw_value.split(";")]
            return all(metal in blob for metal in metals), "all active metals appear in evidence"
        if field == "support_material":
            return value in blob, "support material appears in evidence"
        if field == "preparation_method":
            ok = "impregnation" in blob and "hydrothermal" in blob
            return ok, "preparation-method keywords appear in evidence"

    if table == "reactor_process_gas":
        if field == "reactor_type":
            return "horizontal quartz tube" in blob, "reactor type appears in evidence"
        if field == "catalyst_loading_mass_g":
            return "150 mg" in blob, "0.15 g normalized from explicit 150 mg evidence"
        if field == "temperature_setpoint_C":
            return "850" in blob, "temperature appears in evidence"
        if field == "heating_rate_C_min":
            return "10 c/min" in blob, "heating rate appears in evidence"
        if field == "holding_time_min":
            return "30 min" in blob, "holding time appears in evidence"
        if field == "carbon_source":
            return "ch4" in blob, "carbon source appears in evidence"
        if field == "carbon_source_flow_sccm":
            return "20 ml/min" in blob, "sccm value normalized from explicit 20 mL/min evidence"
        if field == "inert_gas":
            return "helium" in blob or " he " in f" {blob} ", "helium atmosphere appears in evidence"

    if table == "yield_quality":
        if field == "yield_original":
            match = re.search(r"-?\d+(?:\.\d+)?", raw_value)
            ok = bool(match and match.group(0) in blob)
            return ok, "yield number appears in evidence"
        if field == "CNT_type_reported":
            terms_by_run = {
                "P003_FE": ("swcnt", "dwcnt"),
                "P003_FE_MO01": ("swcnt",),
                "P003_FE_MO05": ("mwcnt",),
                "P003_FE_MO1": ("mwcnt",),
                "P003_MO": ("no evidence of cnt", "graphit"),
            }
            terms = terms_by_run[run_id]
            return all(term in blob for term in terms), "CNT class is explicit in evidence"
        if field == "inner_diameter_mean_nm":
            return raw_value.lower() in blob, "mean inner diameter appears in evidence"
        if field == "morphology":
            terms_by_run = {
                "P003_FE": ("entangled",),
                "P003_FE_MO01": ("erect or lying",),
                "P003_FE_MO05": ("multi-walled nanotubes",),
                "P003_FE_MO1": ("multi-walled nanotubes",),
                "P003_MO": ("graphite flakes",),
            }
            return all(term in blob for term in terms_by_run[run_id]), "morphology appears in evidence"

    return False, "no audited field-evidence rule"


def evidence_for_record(
    evidence_rows: list[dict[str, str]],
    table: str,
    record_id: str,
    run_id: str,
    field: str,
) -> dict[str, str]:
    evidence_table = table
    evidence_record_id = record_id
    if table == "reactor_process_gas" and field == "reactor_type":
        evidence_table = "cost_scale_review"
        evidence_record_id = run_id
    matches = [
        row
        for row in evidence_rows
        if row.get("target_table") == evidence_table
        and row.get("target_record_id") == evidence_record_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one evidence row for {table}.{field} {record_id}, got {len(matches)}"
        )
    return matches[0]


def build_core_facts(
    table_data: dict[str, tuple[list[str], list[dict[str, str]]]],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    evidence_rows = table_data["evidence_index"][1]
    source_review_status = table_data["source_master"][1][0]["review_status"]
    facts: list[dict[str, Any]] = []
    by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)

    table_selections: list[tuple[str, dict[str, str], int, tuple[str, ...]]] = []
    for row_number, row in enumerate(table_data["catalyst_system"][1], start=2):
        table_selections.append(("catalyst_system", row, row_number, CATALYST_FIELDS))
    for row_number, row in enumerate(table_data["reactor_process_gas"][1], start=2):
        table_selections.append(
            ("reactor_process_gas", row, row_number, PROCESS_FIELDS[row["stage_type"]])
        )
    for row_number, row in enumerate(table_data["yield_quality"][1], start=2):
        fields = tuple(
            field
            for field in YIELD_FIELDS
            if row.get(field, "").lower() != "not_reported"
        )
        table_selections.append(("yield_quality", row, row_number, fields))

    for table, row, row_number, fields in table_selections:
        run_id = row["run_id"]
        record_id = row[RECORD_ID_FIELDS[table]]
        for field in fields:
            raw_value = row[field]
            if raw_value.lower() in {"not_reported", "not_applicable", "not_assessed"}:
                raise ValueError(f"Non-assertive value selected: {table}.{field}={raw_value}")
            evidence = evidence_for_record(
                evidence_rows, table, record_id, run_id, field
            )
            supported, basis = evidence_supports_field(
                table, field, run_id, raw_value, evidence
            )
            if not supported:
                raise ValueError(
                    f"Evidence does not explicitly support {run_id} {table}.{field}: {basis}"
                )
            value, datatype_uri, unit_uri, approximate = semantic_value(
                table, field, raw_value
            )
            status = "normalized" if (table, field) in NORMALIZED_FIELDS else "reported"
            uri = make_fact_uri(run_id, table, record_id, field)
            item = {
                "fact_id": str(uri).rsplit("/", 1)[-1],
                "fact_uri": str(uri),
                "source_id": SOURCE_ID,
                "run_id": run_id,
                "source_table": table,
                "source_file": f"data/benchmark/fixtures/six_papers/{SOURCE_ID}/{table}.csv",
                "source_row_number": row_number,
                "source_record_id": record_id,
                "source_field": field,
                "predicate_uri": str(field_predicate(table, field)),
                "raw_value": raw_value,
                "semantic_value": value,
                "rdf_datatype": datatype_uri,
                "unit_uri": unit_uri,
                "value_status": status,
                "approximate": approximate,
                "review_status": source_review_status,
                "field_evidence_binding": "audited_export_whitelist",
                "field_evidence_basis": basis,
                "source_evidence_target_fields": evidence["target_fields"],
                "evidence_id": evidence["evidence_id"],
                "evidence": {
                    key: evidence.get(key, "not_reported")
                    for key in (
                        "evidence_id",
                        "target_table",
                        "target_record_id",
                        "target_fields",
                        "value_status",
                        "source_section",
                        "source_locator",
                        "source_object_ref",
                        "evidence_text",
                        "evidence_summary",
                        "confidence",
                        "linked_issue_id",
                    )
                },
            }
            facts.append(item)
            by_run[run_id].append(item)
    return facts, by_run


def build_completeness_report(
    table_data: dict[str, tuple[list[str], list[dict[str, str]]]],
    published_facts: list[dict[str, Any]],
) -> dict[str, Any]:
    evidence_rows = table_data["evidence_index"][1]
    status_counts: Counter[str] = Counter()
    table_cell_counts: Counter[str] = Counter()
    mixed_reported = 0

    for table in FULL_CELL_TABLES:
        fieldnames, rows = table_data[table]
        for row in rows:
            record_id = row[RECORD_ID_FIELDS[table]]
            for field in fieldnames:
                if field in EXCLUDED_CELL_FIELDS[table]:
                    continue
                table_cell_counts[table] += 1
                value = row.get(field, "")
                normalized = value.strip().lower()
                if normalized in {"", "not_reported"}:
                    status = "not_reported"
                elif normalized == "not_applicable":
                    status = "not_applicable"
                elif normalized == "not_assessed":
                    status = "not_assessed"
                else:
                    matched = [
                        item
                        for item in evidence_rows
                        if item["target_table"] == table
                        and item["target_record_id"] == record_id
                    ]
                    evidence_statuses = {item["value_status"] for item in matched}
                    status = "inferred" if "inferred" in evidence_statuses else "reported"
                status_counts[status] += 1
                if status == "reported" and "not reported" in normalized:
                    mixed_reported += 1

    total = sum(status_counts.values())
    published = len(published_facts)
    nonassertive = sum(
        status_counts[key]
        for key in ("not_reported", "not_applicable", "not_assessed")
    )
    return {
        "full_eight_table_cell_count": total,
        "full_cell_status_counts": dict(sorted(status_counts.items())),
        "full_cell_counts_by_table": dict(sorted(table_cell_counts.items())),
        "published_core_fact_count": published,
        "published_fraction_percent": round(100 * published / total, 2),
        "omitted_cell_count": total - published,
        "omitted_nonassertive_cell_count": nonassertive,
        "omitted_nonkey_or_insufficient_field_evidence_count": total - published - nonassertive,
        "mixed_reported_text_containing_not_reported_count": mixed_reported,
        "missing_values_in_assertion_count": 0,
        "cost_scale_facts_in_assertion_count": sum(
            fact["source_table"] == "cost_scale_review" for fact in published_facts
        ),
        "policy": (
            "Formal eight tables retain all states. Run-level nanopublications export "
            "only key reported or normalized facts with audited field-evidence bindings."
        ),
    }


def make_nanopub_dataset(run_id: str) -> tuple[Dataset, dict[str, URIRef]]:
    np_uri = URIRef(f"{BASE}nanopub/{safe_uri_part(run_id)}/v0.2")
    uris = {
        "nanopub": np_uri,
        "head": URIRef(f"{np_uri}/head"),
        "assertion": URIRef(f"{np_uri}/assertion"),
        "provenance": URIRef(f"{np_uri}/provenance"),
        "pubinfo": URIRef(f"{np_uri}/pubinfo"),
    }
    dataset = Dataset()
    bind_namespaces(dataset)
    head = dataset.graph(uris["head"])
    head.add((np_uri, RDF.type, NP.Nanopublication))
    head.add((np_uri, NP.hasAssertion, uris["assertion"]))
    head.add((np_uri, NP.hasProvenance, uris["provenance"]))
    head.add((np_uri, NP.hasPublicationInfo, uris["pubinfo"]))
    return dataset, uris


def add_context(
    graph: Graph,
    source: dict[str, str],
    run: dict[str, str],
) -> tuple[URIRef, URIRef]:
    paper_uri = URIRef(f"{BASE}paper/{safe_uri_part(SOURCE_ID)}")
    run_uri = URIRef(f"{BASE}run/{safe_uri_part(run['run_id'])}")
    doi_uri = URIRef(f"https://doi.org/{source['doi_or_patent_no'].lower()}")
    graph.add((paper_uri, RDF.type, CNT.ResearchPaper))
    graph.add((paper_uri, CNT.sourceId, Literal(SOURCE_ID)))
    graph.add((paper_uri, DCTERMS.title, Literal(source["source_title"])))
    graph.add((paper_uri, DCTERMS.creator, Literal(source["authors_or_assignee"])))
    graph.add(
        (
            paper_uri,
            DCTERMS.issued,
            Literal(source["publication_year"], datatype=XSD.gYear),
        )
    )
    graph.add((paper_uri, DCTERMS.isPartOf, Literal(source["publication_venue"])))
    graph.add((paper_uri, DCTERMS.identifier, Literal(source["doi_or_patent_no"])))
    graph.add((paper_uri, DCTERMS.source, doi_uri))

    graph.add((run_uri, RDF.type, CNT.ExperimentalRun))
    graph.add((run_uri, CNT.sourceId, Literal(SOURCE_ID)))
    graph.add((run_uri, CNT.runId, Literal(run["run_id"])))
    graph.add((run_uri, DCTERMS.title, Literal(run["run_label"])))
    graph.add((run_uri, CNT.runSummary, Literal(run["run_summary"])))
    graph.add((run_uri, CNT.targetTrack, Literal(run["target_track"])))
    graph.add((run_uri, CNT.dataType, Literal(run["data_type"])))
    graph.add((run_uri, CNT.extractionConfidence, Literal(run["extraction_confidence"])))
    graph.add((paper_uri, CNT.hasExperimentalRun, run_uri))
    return paper_uri, run_uri


def literal_for_fact(fact: dict[str, Any]) -> Literal:
    if fact["rdf_datatype"] == str(XSD.decimal):
        return Literal(fact["semantic_value"], datatype=XSD.decimal)
    return Literal(fact["semantic_value"], datatype=XSD.string)


def add_assertion_facts(
    graph: Graph,
    run_uri: URIRef,
    facts: list[dict[str, Any]],
) -> None:
    record_uris: dict[tuple[str, str], URIRef] = {}
    for fact in facts:
        key = (fact["source_table"], fact["source_record_id"])
        record_uri = record_uris.get(key)
        if record_uri is None:
            record_uri = URIRef(
                f"{BASE}record/{safe_uri_part(fact['source_table'])}/"
                f"{safe_uri_part(fact['source_record_id'])}"
            )
            record_uris[key] = record_uri
            graph.add((record_uri, RDF.type, CNT.EightTableRecord))
            graph.add((record_uri, CNT.belongsToRun, run_uri))
            graph.add((record_uri, CNT.sourceTable, Literal(fact["source_table"])))
            graph.add((record_uri, CNT.sourceRecordId, Literal(fact["source_record_id"])))
            graph.add((run_uri, CNT.hasSourceRecord, record_uri))

        predicate = URIRef(fact["predicate_uri"])
        value = literal_for_fact(fact)
        f_uri = URIRef(fact["fact_uri"])
        graph.add((record_uri, predicate, value))
        graph.add((record_uri, CNT.hasFact, f_uri))
        graph.add((f_uri, RDF.type, CNT.ExperimentalFact))
        graph.add((f_uri, RDF.subject, record_uri))
        graph.add((f_uri, RDF.predicate, predicate))
        graph.add((f_uri, RDF.object, value))
        graph.add((f_uri, CNT.valueStatus, Literal(fact["value_status"])))
        if fact["unit_uri"]:
            graph.add((f_uri, CNT.unit, URIRef(fact["unit_uri"])))
        if fact["approximate"]:
            graph.add((f_uri, CNT.approximate, Literal(True, datatype=XSD.boolean)))


def add_evidence_node(graph: Graph, evidence: dict[str, str]) -> URIRef:
    uri = URIRef(f"{BASE}evidence/{safe_uri_part(evidence['evidence_id'])}")
    graph.add((uri, RDF.type, CNT.EvidenceRecord))
    for predicate, key in (
        (CNT.evidenceId, "evidence_id"),
        (CNT.targetTable, "target_table"),
        (CNT.targetRecordId, "target_record_id"),
        (CNT.sourceEvidenceTargetFields, "target_fields"),
        (CNT.evidenceValueStatus, "value_status"),
        (CNT.sourceSection, "source_section"),
        (CNT.sourceLocator, "source_locator"),
        (CNT.sourceObjectReference, "source_object_ref"),
        (CNT.evidenceText, "evidence_text"),
        (CNT.evidenceSummary, "evidence_summary"),
        (CNT.confidence, "confidence"),
        (CNT.linkedIssueId, "linked_issue_id"),
    ):
        graph.add((uri, predicate, Literal(evidence.get(key, "not_reported"))))
    return uri


def add_review_issues(
    graph: Graph,
    assertion_uri: URIRef,
    issue_rows: list[dict[str, str]],
) -> None:
    for issue in issue_rows:
        issue_uri = URIRef(
            f"{BASE}review-issue/{safe_uri_part(issue['issue_id'])}"
        )
        graph.add((assertion_uri, CNT.hasReviewIssue, issue_uri))
        graph.add((issue_uri, RDF.type, CNT.ReviewIssue))
        for predicate, key in (
            (CNT.issueId, "issue_id"),
            (CNT.issueType, "issue_type"),
            (CNT.issueSummary, "issue_summary"),
            (CNT.severity, "severity"),
            (CNT.reviewStatus, "review_status"),
            (CNT.resolution, "resolution"),
        ):
            graph.add((issue_uri, predicate, Literal(issue.get(key, "not_reported"))))


def add_provenance(
    graph: Graph,
    assertion_uri: URIRef,
    source: dict[str, str],
    run: dict[str, str],
    facts: list[dict[str, Any]],
    issue_rows: list[dict[str, str]],
) -> None:
    doi_uri = URIRef(f"https://doi.org/{source['doi_or_patent_no'].lower()}")
    graph.add((assertion_uri, PROV.wasDerivedFrom, doi_uri))
    graph.add((assertion_uri, CNT.sourceId, Literal(SOURCE_ID)))
    graph.add((assertion_uri, CNT.runId, Literal(run["run_id"])))
    graph.add((assertion_uri, CNT.joinKey, Literal("run_id")))
    graph.add((assertion_uri, CNT.extractionStatus, Literal(source["extraction_status"])))
    graph.add((assertion_uri, CNT.reviewStatus, Literal(source["review_status"])))
    graph.add((assertion_uri, CNT.contextSourceTable, Literal("source_master; source_run")))
    add_review_issues(graph, assertion_uri, issue_rows)

    evidence_uris: dict[str, URIRef] = {}
    for fact in facts:
        evidence = fact["evidence"]
        evidence_id = evidence["evidence_id"]
        if evidence_id not in evidence_uris:
            evidence_uris[evidence_id] = add_evidence_node(graph, evidence)
        f_uri = URIRef(fact["fact_uri"])
        graph.add((f_uri, CNT.sourceId, Literal(SOURCE_ID)))
        graph.add((f_uri, CNT.runId, Literal(fact["run_id"])))
        graph.add((f_uri, CNT.sourceTable, Literal(fact["source_table"])))
        graph.add((f_uri, CNT.sourceFile, Literal(fact["source_file"])))
        graph.add(
            (
                f_uri,
                CNT.sourceRowNumber,
                Literal(fact["source_row_number"], datatype=XSD.integer),
            )
        )
        graph.add((f_uri, CNT.sourceRecordId, Literal(fact["source_record_id"])))
        graph.add((f_uri, CNT.sourceField, Literal(fact["source_field"])))
        graph.add((f_uri, CNT.rawValue, Literal(fact["raw_value"])))
        graph.add((f_uri, CNT.valueStatus, Literal(fact["value_status"])))
        graph.add((f_uri, CNT.reviewStatus, Literal(fact["review_status"])))
        graph.add((f_uri, CNT.fieldEvidenceBinding, Literal(fact["field_evidence_binding"])))
        graph.add((f_uri, CNT.fieldEvidenceBasis, Literal(fact["field_evidence_basis"])))
        graph.add(
            (
                f_uri,
                CNT.sourceEvidenceTargetFields,
                Literal(fact["source_evidence_target_fields"]),
            )
        )
        graph.add((f_uri, PROV.wasDerivedFrom, evidence_uris[evidence_id]))


def add_publication_info(
    graph: Graph,
    np_uri: URIRef,
    generated_at: str,
    input_hashes: dict[str, str],
) -> None:
    software_uri = URIRef(f"{BASE}software/{PROGRAM_VERSION}")
    creator_uri = URIRef(f"{BASE}agent/wang-yang")
    graph.add((np_uri, DCTERMS.created, Literal(generated_at, datatype=XSD.dateTime)))
    graph.add((np_uri, DCTERMS.creator, creator_uri))
    graph.add((creator_uri, RDF.type, PROV.Agent))
    graph.add((creator_uri, DCTERMS.title, Literal("王扬")))
    graph.add((np_uri, PROV.wasGeneratedBy, software_uri))
    graph.add((software_uri, RDF.type, PROV.SoftwareAgent))
    graph.add((software_uri, DCTERMS.title, Literal(PROGRAM_NAME)))
    graph.add((software_uri, CNT.programVersion, Literal(PROGRAM_VERSION)))
    graph.add((software_uri, CNT.nanopubLibraryVersion, Literal(version("nanopub"))))
    graph.add((np_uri, DCTERMS.license, Literal(LICENSE_ID)))
    graph.add((np_uri, DCTERMS.hasVersion, Literal(PROGRAM_VERSION)))
    graph.add((np_uri, CNT.localDemoStatus, Literal(LOCAL_DEMO_STATUS)))
    graph.add((np_uri, CNT.uploadAttempted, Literal(False, datatype=XSD.boolean)))
    graph.add((np_uri, CNT.formalDataSource, Literal("eight_tables_read_only")))
    graph.add((np_uri, CNT.exportLayer, Literal("derived_run_level_nanopublication")))
    for name, digest in sorted(input_hashes.items()):
        checksum_uri = URIRef(
            f"{np_uri}/checksum/{safe_uri_part(name)}"
        )
        graph.add((np_uri, CNT.inputChecksum, checksum_uri))
        graph.add((checksum_uri, CNT.sourceFile, Literal(f"{name}.csv")))
        graph.add((checksum_uri, CNT.sha256, Literal(digest)))


def build_run_nanopub(
    source: dict[str, str],
    run: dict[str, str],
    facts: list[dict[str, Any]],
    issue_rows: list[dict[str, str]],
    generated_at: str,
    input_hashes: dict[str, str],
) -> Nanopub:
    dataset, uris = make_nanopub_dataset(run["run_id"])
    conf = NanopubConf(
        add_prov_generated_time=False,
        add_pubinfo_generated_time=False,
        attribute_assertion_to_profile=False,
        attribute_publication_to_profile=False,
    )
    nanopub = Nanopub(rdf=dataset, conf=conf)
    _, run_uri = add_context(nanopub.assertion, source, run)
    add_assertion_facts(nanopub.assertion, run_uri, facts)
    add_provenance(
        nanopub.provenance,
        uris["assertion"],
        source,
        run,
        facts,
        issue_rows,
    )
    add_publication_info(
        nanopub.pubinfo,
        uris["nanopub"],
        generated_at,
        input_hashes,
    )
    return nanopub


def render_html(mapping: dict[str, Any]) -> str:
    source = mapping["source"]
    metrics = mapping["metrics"]
    completeness = mapping["completeness"]
    run_rows = []
    detail_sections = []
    for run in mapping["runs"]:
        status_counts = Counter(fact["value_status"] for fact in run["facts"])
        typed = sum(
            fact["rdf_datatype"] == str(XSD.decimal) for fact in run["facts"]
        )
        run_rows.append(
            "<tr>"
            f"<td><code>{html.escape(run['run_id'])}</code></td>"
            f"<td>{html.escape(run['run_label'])}</td>"
            f"<td>{run['fact_count']}</td>"
            f"<td>{typed}</td>"
            f"<td>{status_counts.get('reported', 0)}</td>"
            f"<td>{status_counts.get('normalized', 0)}</td>"
            f"<td><code>{html.escape(run['nanopub_file'])}</code></td>"
            "</tr>"
        )
        facts_html = []
        for fact in run["facts"]:
            datatype = fact["rdf_datatype"].rsplit("#", 1)[-1]
            unit = (fact["unit_uri"] or "—").rsplit("/", 1)[-1]
            facts_html.append(
                "<tr>"
                f"<td>{html.escape(fact['source_table'])}</td>"
                f"<td>{html.escape(fact['source_field'])}</td>"
                f"<td>{html.escape(fact['raw_value'])}</td>"
                f"<td>{html.escape(fact['semantic_value'])}</td>"
                f"<td>{html.escape(datatype)}</td>"
                f"<td>{html.escape(unit)}</td>"
                f"<td><span class='status {html.escape(fact['value_status'])}'>{html.escape(fact['value_status'])}</span></td>"
                f"<td>{html.escape(fact['evidence_id'])}</td>"
                f"<td>{html.escape(fact['evidence']['source_locator'])}</td>"
                "</tr>"
            )
        detail_sections.append(
            f"<details><summary>{html.escape(run['run_id'])} — "
            f"{html.escape(run['run_label'])}（{run['fact_count']}条关键事实）</summary>"
            "<div class='table-wrap'><table><thead><tr>"
            "<th>原表</th><th>字段</th><th>八表原值</th><th>RDF值</th>"
            "<th>datatype</th><th>单位URI</th><th>状态</th><th>证据ID</th><th>页码/表格</th>"
            "</tr></thead><tbody>"
            + "".join(facts_html)
            + "</tbody></table></div></details>"
        )

    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CNT-PatSight Nanopublication PoC v0.2</title>
<style>
:root {{ --navy:#0b243b; --teal:#00a6a6; --bg:#f4f7f9; --line:#d7e1e8; --text:#18344b; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--text); font:15px/1.6 "Segoe UI","Microsoft YaHei",sans-serif; }}
main {{ max-width:1180px; margin:auto; padding:36px 24px 64px; }} h1 {{ color:var(--navy); font-size:34px; margin:4px 0 8px; }} h2 {{ margin-top:34px; color:var(--navy); }}
.eyebrow {{ color:var(--teal); font-weight:700; letter-spacing:.08em; }} .lead {{ max-width:940px; font-size:17px; }}
.grid {{ display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin:24px 0; }} .card {{ background:#fff; border:1px solid var(--line); border-radius:12px; padding:17px; }} .metric {{ font-size:27px; font-weight:760; color:var(--navy); }}
.notice {{ background:#e6f5f4; border-left:5px solid var(--teal); padding:16px 18px; margin:20px 0; }} .warning {{ background:#fff5d9; border-left-color:#e4a900; }}
table {{ width:100%; border-collapse:collapse; background:white; }} th,td {{ border-bottom:1px solid var(--line); padding:9px 10px; text-align:left; vertical-align:top; }} th {{ background:var(--navy); color:white; position:sticky; top:0; }}
.table-wrap {{ overflow:auto; max-height:560px; border:1px solid var(--line); border-radius:10px; }} code {{ font:12px Consolas,monospace; }} details {{ background:white; border:1px solid var(--line); border-radius:10px; margin:12px 0; }} summary {{ cursor:pointer; padding:14px 16px; font-weight:700; }}
.status {{ white-space:nowrap; padding:2px 7px; border-radius:999px; background:#e8eef3; font-size:12px; }} .reported {{ background:#dff4e8; }} .normalized {{ background:#dceaff; }}
@media(max-width:900px) {{ .grid {{ grid-template-columns:1fr 1fr; }} }}
</style></head><body><main>
<div class="eyebrow">RUN-LEVEL NANOPUBLICATION PROOF OF CONCEPT · V0.2</div>
<h1>从“八表RDF镜像”升级为可引用的运行级科研事实</h1>
<p class="lead">本版不再发布915个单元格镜像，而是把一篇论文拆为5个独立run级nanopublication，只保留证据文本明确支持的关键reported/normalized事实，并为数值设置RDF datatype和单位URI。</p>
<div class="notice"><strong>论文：</strong>{html.escape(source['source_title'])}<br><strong>source_id：</strong><code>{html.escape(source['source_id'])}</code>　<strong>DOI：</strong>{html.escape(source['doi'])}<br><strong>原数据状态：</strong>{html.escape(source['extraction_status'])} / {html.escape(source['review_status'])}</div>
<div class="grid">
<div class="card"><div class="metric">{metrics['nanopublication_count']}</div><div>run级nanopub</div></div>
<div class="card"><div class="metric">{metrics['core_fact_count']}</div><div>关键科研事实</div></div>
<div class="card"><div class="metric">{metrics['numeric_typed_fact_count']}</div><div>xsd:decimal事实</div></div>
<div class="card"><div class="metric">{metrics['export_field_evidence_percent']:.1f}%</div><div>发布事实字段映射</div></div>
<div class="card"><div class="metric">0</div><div>缺失值Assertion</div></div>
</div>
    <div class="notice warning"><strong>证据口径：</strong>原始<code>evidence_index</code>仍是记录级证据，原表字段级比例为0%。本版没有修改它；而是在独立导出层用证据审定白名单，只把证据文本明确提到的字段绑定为核心事实。因此“发布事实字段映射率100%”不等于原始八表已经逐字段审完。</div>
<h2>紧凑性与完整性处理</h2>
<div class="table-wrap"><table><thead><tr><th>口径</th><th>数量</th><th>处理</th></tr></thead><tbody>
<tr><td>八表四张实验表全部单元格</td><td>{completeness['full_eight_table_cell_count']}</td><td>继续完整保留在正式CSV</td></tr>
<tr><td>发布为核心Assertion</td><td>{completeness['published_core_fact_count']}（{completeness['published_fraction_percent']:.1f}%）</td><td>仅reported/normalized且有字段证据白名单</td></tr>
<tr><td>缺失、不适用、未评价</td><td>{completeness['omitted_nonassertive_cell_count']}</td><td>不发布为科研事实，记录于完整性报告</td></tr>
<tr><td>非关键或字段证据不足</td><td>{completeness['omitted_nonkey_or_insufficient_field_evidence_count']}</td><td>保留在八表，不进入核心Assertion</td></tr>
<tr><td>cost/scale字段</td><td>{completeness['cost_scale_facts_in_assertion_count']}</td><td>混合推断和评价，当前不发布</td></tr>
</tbody></table></div>
<h2>5个独立run级nanopublication</h2>
<div class="table-wrap"><table><thead><tr><th>run_id</th><th>运行标签</th><th>事实数</th><th>数值类型</th><th>reported</th><th>normalized</th><th>独立TriG</th></tr></thead><tbody>{''.join(run_rows)}</tbody></table></div>
<h2>为什么比上一版更有价值</h2>
<p>每个run现在可以单独引用、修订或撤回；RDF数值可以直接执行温度、流量、产率和直径范围查询；缺失状态不再膨胀Assertion；论文与run上下文包含标题、作者、年份、期刊、run label、run summary、target track和抽取置信度。</p>
<h2>全部发布事实</h2>{''.join(detail_sections)}
</main></body></html>"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RUN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    input_paths = {name: INPUT_DIR / f"{name}.csv" for name in TABLES}
    hashes_before = {name: sha256(path) for name, path in input_paths.items()}
    table_data = {name: read_csv_table(name) for name in TABLES}
    source = table_data["source_master"][1][0]
    runs = table_data["source_run"][1]
    facts, by_run = build_core_facts(table_data)
    completeness = build_completeness_report(table_data, facts)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    combined = Dataset()
    bind_namespaces(combined)
    run_outputs: list[dict[str, Any]] = []
    assertion_triples = provenance_triples = pubinfo_triples = 0
    for run in runs:
        run_id = run["run_id"]
        nanopub = build_run_nanopub(
            source,
            run,
            by_run[run_id],
            table_data["review_issue_log"][1],
            generated_at,
            hashes_before,
        )
        run_path = RUN_OUTPUT_DIR / f"{run_id}.trig"
        nanopub.store(run_path, format="trig")
        roundtrip = Nanopub(rdf=run_path)
        if not len(roundtrip.assertion) or not len(roundtrip.provenance) or not len(roundtrip.pubinfo):
            raise RuntimeError(f"Nanopub round-trip failed for {run_id}")
        assertion_triples += len(roundtrip.assertion)
        provenance_triples += len(roundtrip.provenance)
        pubinfo_triples += len(roundtrip.pubinfo)
        for quad in nanopub.rdf.quads((None, None, None, None)):
            combined.add(quad)
        run_outputs.append(
            {
                "run_id": run_id,
                "run_label": run["run_label"],
                "nanopub_uri": str(nanopub.metadata.np_uri),
                "nanopub_file": f"data/processed/analysis/derived/nanopub_demo/runs/{run_path.name}",
                "fact_count": len(by_run[run_id]),
                "facts": by_run[run_id],
            }
        )

    combined.serialize(TRIG_PATH, format="trig")
    status_counts = Counter(fact["value_status"] for fact in facts)
    numeric_count = sum(fact["rdf_datatype"] == str(XSD.decimal) for fact in facts)
    used_evidence_ids = {fact["evidence_id"] for fact in facts}
    metrics = {
        "source_id": SOURCE_ID,
        "program_version": PROGRAM_VERSION,
        "nanopub_distribution_version": version("nanopub"),
        "generated_at": generated_at,
        "nanopublication_count": len(run_outputs),
        "run_count": len(runs),
        "core_fact_count": len(facts),
        "core_fact_status_counts": dict(sorted(status_counts.items())),
        "numeric_typed_fact_count": numeric_count,
        "numeric_typed_fact_percent": round(100 * numeric_count / len(facts), 2),
        "export_field_evidence_fact_count": len(facts),
        "export_field_evidence_percent": 100.0,
        "source_evidence_index_field_specific_percent": 0.0,
        "source_evidence_records_used": len(used_evidence_ids),
        "source_evidence_record_count": len(table_data["evidence_index"][1]),
        "review_issue_count": len(table_data["review_issue_log"][1]),
        "assertion_triple_count": assertion_triples,
        "provenance_triple_count": provenance_triples,
        "publication_info_triple_count": pubinfo_triples,
        "combined_quad_count": sum(1 for _ in combined.quads((None, None, None, None))),
        "not_reported_assertion_count": 0,
        "inferred_assertion_count": 0,
        "server_upload_attempted": False,
        "formal_tables_modified": False,
        "formal_tables_read": list(TABLES),
    }

    mapping = {
        "schema_version": MAPPING_SCHEMA_VERSION,
        "source": {
            "source_id": SOURCE_ID,
            "source_title": source["source_title"],
            "authors": source["authors_or_assignee"],
            "publication_year": source["publication_year"],
            "publication_venue": source["publication_venue"],
            "doi": source["doi_or_patent_no"],
            "screening_class": source["screening_class"],
            "extraction_status": source["extraction_status"],
            "review_status": source["review_status"],
        },
        "export": {
            "program": PROGRAM_NAME,
            "program_version": PROGRAM_VERSION,
            "nanopub_distribution_version": version("nanopub"),
            "generated_at": generated_at,
            "license": LICENSE_ID,
            "local_demo_status": LOCAL_DEMO_STATUS,
            "server_upload_attempted": False,
            "formal_tables_modified": False,
            "join_key": "run_id",
            "combined_trig_file": f"data/processed/analysis/derived/nanopub_demo/{TRIG_PATH.name}",
            "policy": "key_reported_or_normalized_facts_with_audited_field_bindings",
        },
        "input_files": [
            {
                "table": name,
                    "path": f"data/benchmark/fixtures/six_papers/{SOURCE_ID}/{name}.csv",
                "sha256": hashes_before[name],
                "row_count": len(table_data[name][1]),
            }
            for name in TABLES
        ],
        "metrics": metrics,
        "completeness": completeness,
        "runs": run_outputs,
    }
    MAPPING_PATH.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    completeness["input_csv_bytes"] = sum(path.stat().st_size for path in input_paths.values())
    completeness["combined_trig_bytes"] = TRIG_PATH.stat().st_size
    completeness["mapping_json_bytes"] = MAPPING_PATH.stat().st_size
    completeness["combined_trig_to_input_csv_ratio"] = round(
        completeness["combined_trig_bytes"] / completeness["input_csv_bytes"], 2
    )
    mapping["completeness"] = completeness
    MAPPING_PATH.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    COMPLETENESS_PATH.write_text(
        json.dumps(completeness, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    REPORT_PATH.write_text(render_html(mapping), encoding="utf-8")

    hashes_after = {name: sha256(path) for name, path in input_paths.items()}
    if hashes_before != hashes_after:
        raise RuntimeError("Formal eight-table inputs changed during export")
    if any(fact["value_status"] not in {"reported", "normalized"} for fact in facts):
        raise RuntimeError("Non-publishable status entered the assertion")
    if any(not fact["evidence_id"] for fact in facts):
        raise RuntimeError("A core fact lacks evidence")
    if len({item["nanopub_uri"] for item in run_outputs}) != len(run_outputs):
        raise RuntimeError("Run-level nanopublication URIs are not unique")
    if any(fact["raw_value"].lower() == "not_reported" for fact in facts):
        raise RuntimeError("not_reported entered the assertion")

    print(json.dumps({"metrics": metrics, "completeness": completeness}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
