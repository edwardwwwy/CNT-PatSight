from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.parse_fulltext.extractor import PARSER_VERSION
from scripts.production.staging import (
    allowed_field_map, build_staging_rows, validate_payload,
    validate_rows_with_formal_validator,
)
from scripts.production.store import ProductionStore, utc_now
from scripts.production.workers import (
    assign_batches, atomic_json, fulltext_worker, monitor_worker, pid_alive,
    qwen_worker, sync_parse_status,
)


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = ROOT / "data/interim/runtime"
ACTIVE_CONFIG = RUNTIME_DIR / "active_config.json"
FREEZE_MANIFEST = RUNTIME_DIR / "production_freeze_manifest.json"
SMOKE_REPORT = RUNTIME_DIR / "smoke_test_report.json"
ACTIVE_EXTRACTION_SCHEMA = RUNTIME_DIR / "config/llm_extraction_v0.2.active.schema.json"
PRODUCTION_DB = Path("data/interim/llm_extraction/llm_extraction.sqlite3")
FULLTEXT_DB = Path("data/raw/fulltext/fulltext.sqlite3")
CANDIDATE_DB = Path("data/interim/extraction_candidates/extraction_candidates.sqlite3")
METADATA_DB = Path("data/raw/metadata/snapshots/screening_rules_v1.2/literature.sqlite3")
SNAPSHOT_DIR = Path("data/raw/metadata/snapshots/screening_rules_v1.2")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tracked_asset_paths() -> list[Path]:
    paths = [
        ROOT / SNAPSHOT_DIR / "literature_master.csv",
        ROOT / SNAPSHOT_DIR / "literature.sqlite3",
        ROOT / SNAPSHOT_DIR / "screening_rules.json",
        ROOT / "config/screening_rules.json",
        ROOT / "config/schema.json",
        ROOT / "config/field_dictionary.csv",
    ]
    for directory in sorted((ROOT / "data/interim").glob("P*")):
        if (directory / "source_master.csv").exists():
            paths.extend(sorted(path for path in directory.iterdir() if path.is_file()))
    connection = sqlite3.connect(ROOT / METADATA_DB)
    for (local_path,) in connection.execute("SELECT pdf_path FROM works WHERE pdf_path!=''"):
        path = Path(local_path)
        path = path if path.is_absolute() else ROOT / path
        if path.exists():
            paths.append(path)
    connection.close()
    return list(dict.fromkeys(path.resolve() for path in paths))


def build_freeze_manifest() -> dict[str, Any]:
    snapshot = json.loads((ROOT / SNAPSHOT_DIR / "snapshot_manifest.json").read_text(encoding="utf-8-sig"))
    if snapshot.get("canonical_work_count") != 1487:
        raise RuntimeError("frozen_snapshot_count_not_1487")
    counts = {row["tier"]: row["count"] for row in snapshot.get("tier_counts", [])}
    if counts != {"A": 208, "B": 371, "C": 450, "M": 35, "R": 423}:
        raise RuntimeError(f"unexpected_v1.2_tier_counts:{counts}")
    files = []
    for path in tracked_asset_paths():
        files.append({
            "path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return {
        "freeze_version": "production_v1", "created_at": utc_now(),
        "metadata_snapshot": "screening_rules_v1.2", "canonical_work_count": 1487,
        "tier_counts": counts, "files": files,
        "write_policy": "production workers may not write any listed path",
    }


def verify_freeze(manifest: dict[str, Any] | None = None) -> None:
    manifest = manifest or json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))
    failures = []
    for item in manifest["files"]:
        path = Path(item["path"])
        path = path if path.is_absolute() else ROOT / path
        if not path.exists() or path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"]:
            failures.append(item["path"])
    if failures:
        raise RuntimeError("frozen_asset_mismatch:" + ";".join(failures))


def build_config() -> dict[str, Any]:
    model = ROOT / "models/Qwen3-14B-Q4_K_M.gguf"
    runtime = ROOT / ".tools/llama.cpp/current/llama-completion.exe"
    small_files = {
        "prompt": ROOT / "config/prompts/qwen_cnt_extraction_v2.txt",
        "extraction_schema": ACTIVE_EXTRACTION_SCHEMA,
        "formal_schema": ROOT / "config/schema.json",
        "field_dictionary": ROOT / "config/field_dictionary.csv",
        "unit_rules": ROOT / "config/llm_unit_rules_v1.json",
        "runtime": runtime,
    }
    if not model.exists() or not runtime.exists():
        raise FileNotFoundError("Qwen model or llama-completion runtime missing")
    manifest = {
        "model_version": {"path": model.relative_to(ROOT).as_posix(), "bytes": model.stat().st_size, "sha256": sha256_file(model)},
        "versions": {name: {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)} for name, path in small_files.items()},
        "parser_version": PARSER_VERSION,
        "extraction_rule_version": "continuous_pipeline_v1",
        "generation": {"device": "Vulkan0", "context_size": 24576, "max_tokens": 15000, "temperature": 0, "seed": 42, "timeout_seconds": 1200},
    }
    snapshot_id = "CFG_" + hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()[:20].upper()
    return {
        "config_snapshot_id": snapshot_id,
        "model_path": model.relative_to(ROOT).as_posix(),
        "runtime_path": runtime.relative_to(ROOT).as_posix(),
        "prompt_path": "config/prompts/qwen_cnt_extraction_v2.txt",
        "extraction_schema_path": ACTIVE_EXTRACTION_SCHEMA.relative_to(ROOT).as_posix(),
        "unit_rules_path": "config/llm_unit_rules_v1.json",
        "metadata_db": METADATA_DB.as_posix(), "fulltext_db": FULLTEXT_DB.as_posix(),
        "candidate_db": CANDIDATE_DB.as_posix(), "production_db": PRODUCTION_DB.as_posix(),
        "device": "Vulkan0", "context_size": 24576, "max_tokens": 15000,
        "timeout_seconds": 1200, "config_manifest": manifest,
    }


def build_active_extraction_schema() -> None:
    """Materialize field-name-constrained JSON Schema from the formal contract."""
    base = json.loads((ROOT / "config/llm_extraction_v0.2.schema.json").read_text(encoding="utf-8"))
    formal = json.loads((ROOT / "config/schema.json").read_text(encoding="utf-8"))
    allowed = allowed_field_map(formal)
    definitions = {
        "run": "source_run", "catalyst": "catalyst_system",
        "process": "reactor_process_gas", "product": "yield_quality",
        "cost": "cost_scale_review",
    }
    evidence_or_null = {"oneOf": [{"$ref": "#/$defs/evidence_value"}, {"type": "null"}]}
    for definition, table in definitions.items():
        base["$defs"][definition]["properties"]["fields"] = {
            "type": "object", "additionalProperties": False,
            "properties": {field: evidence_or_null for field in allowed[table]},
        }
    array_limits = {
        "run_candidates": 8,
        "catalyst_candidates": 8,
        "process_stage_candidates": 24,
        "product_candidates": 8,
        "cost_scale_candidates": 8,
        "review_issues": 12,
    }
    for collection, maximum in array_limits.items():
        base["properties"][collection]["maxItems"] = maximum
    issue_fields = [
        "issue_type", "target_table", "target_record_id", "target_field",
        "issue_summary", "conflicting_values", "severity",
    ]
    base["$defs"]["issue"]["properties"]["fields"] = {
        "type": "object", "additionalProperties": False,
        "properties": {field: evidence_or_null for field in issue_fields},
    }
    atomic_json(ACTIVE_EXTRACTION_SCHEMA, base)


def migrate_unsuccessful_tasks_to_config(config: dict[str, Any]) -> int:
    """Reset only non-successful tasks after a systemic configuration repair."""
    with ProductionStore(ROOT / PRODUCTION_DB, ROOT / "config/schema.json") as store:
        rows = store.connection.execute(
            "SELECT task_id,config_snapshot_id FROM qwen_tasks WHERE task_status!='succeeded' AND config_snapshot_id!=?",
            (config["config_snapshot_id"],),
        ).fetchall()
        now = utc_now()
        for row in rows:
            store.connection.execute(
                """
                UPDATE qwen_tasks SET config_snapshot_id=?,task_status='pending',
                    extraction_disposition='candidate_extract',attempt_count=0,
                    lease_owner='',claimed_at='',heartbeat_at='',request_hash='',
                    raw_result_path='',last_error='',updated_at=? WHERE task_id=?
                """,
                (config["config_snapshot_id"], now, row["task_id"]),
            )
            store.connection.execute(
                "INSERT INTO task_events(task_id,event_type,detail_json,created_at) VALUES (?,?,?,?)",
                (row["task_id"], "systemic_configuration_repair", json.dumps({"old_config": row["config_snapshot_id"], "new_config": config["config_snapshot_id"]}), now),
            )
        store.connection.commit()
        return len(rows)


def seed_reviewed_candidates(config: dict[str, Any]) -> int:
    review_path = ROOT / "data/review/fulltext_pilot_v1/fulltext_relevance_review.csv"
    candidate_connection = sqlite3.connect(ROOT / CANDIDATE_DB)
    candidate_connection.row_factory = sqlite3.Row
    seeded = 0
    with review_path.open(encoding="utf-8-sig", newline="") as handle, ProductionStore(ROOT / PRODUCTION_DB, ROOT / "config/schema.json") as store:
        for priority, row in enumerate(csv.DictReader(handle), start=1):
            if row.get("candidate_extract_approved") != "1":
                continue
            parsed = candidate_connection.execute(
                "SELECT input_content_hash,parse_status FROM parse_source_status WHERE source_id=?",
                (row["source_id"],),
            ).fetchone()
            if parsed is None or parsed["parse_status"] != "success":
                raise RuntimeError(f"approved_candidate_missing_parse:{row['source_id']}")
            input_hash = str(parsed["input_content_hash"])
            task_id = "QT_" + hashlib.sha256(f"{row['source_id']}|{input_hash}|{config['config_snapshot_id']}".encode()).hexdigest()[:20].upper()
            seeded += int(store.enqueue(task_id, row["source_id"], input_hash, config["config_snapshot_id"], priority))
    candidate_connection.close()
    return seeded


def verify_reviewed_candidates_once(config: dict[str, Any]) -> int:
    """Require every approved pilot source once; allow later producer additions."""
    review_path = ROOT / "data/review/fulltext_pilot_v1/fulltext_relevance_review.csv"
    with review_path.open(encoding="utf-8-sig", newline="") as handle:
        approved = {
            row["source_id"] for row in csv.DictReader(handle)
            if row.get("candidate_extract_approved") == "1"
        }
    with ProductionStore(ROOT / PRODUCTION_DB, ROOT / "config/schema.json") as store:
        placeholders = ",".join("?" for _ in approved)
        rows = store.connection.execute(
            f"""SELECT source_id,COUNT(*) AS n FROM qwen_tasks
                WHERE config_snapshot_id=? AND source_id IN ({placeholders})
                GROUP BY source_id""",
            (config["config_snapshot_id"], *sorted(approved)),
        ).fetchall()
    counts = {row["source_id"]: int(row["n"]) for row in rows}
    invalid = {source_id: counts.get(source_id, 0) for source_id in approved if counts.get(source_id, 0) != 1}
    if invalid:
        raise RuntimeError(f"approved_qwen_queue_not_exactly_once:{invalid}")
    return len(approved)


def write_production_manifest() -> int:
    fulltext = sqlite3.connect(ROOT / FULLTEXT_DB)
    fulltext.row_factory = sqlite3.Row
    fulltext.execute("ATTACH DATABASE ? AS candidate", (str(ROOT / CANDIDATE_DB),))
    rows = fulltext.execute(
        """
        SELECT q.source_id,q.priority_tier,q.batch_id,q.candidate_url,q.access_type,
               q.download_status,q.attempt_count,q.local_path,q.sha256,
               COALESCE(p.parse_status,q.parse_status,'') parse_status,
               COALESCE(p.fulltext_relevance_status,q.fulltext_relevance_status,'') fulltext_relevance_status,
               q.failure_reason,q.queue_priority
        FROM fulltext_acquisition_queue q
        LEFT JOIN candidate.parse_source_status p ON p.source_id=q.source_id
        ORDER BY CASE q.priority_tier WHEN 'A' THEN 0 ELSE 1 END,q.queue_priority,q.source_id
        """
    ).fetchall()
    path = ROOT / "data/raw/fulltext/fulltext_production_manifest.csv"
    columns = [d[0] for d in fulltext.execute("SELECT q.source_id,q.priority_tier,q.batch_id,q.candidate_url,q.access_type,q.download_status,q.attempt_count,q.local_path,q.sha256,COALESCE(p.parse_status,q.parse_status,'') parse_status,COALESCE(p.fulltext_relevance_status,q.fulltext_relevance_status,'') fulltext_relevance_status,q.failure_reason,q.queue_priority FROM fulltext_acquisition_queue q LEFT JOIN candidate.parse_source_status p ON p.source_id=q.source_id LIMIT 0").description]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(dict(row) for row in rows)
    fulltext.close()
    return len(rows)


def prepare() -> dict[str, Any]:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    if FREEZE_MANIFEST.exists():
        freeze = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))
        verify_freeze(freeze)
    else:
        freeze = build_freeze_manifest()
        atomic_json(FREEZE_MANIFEST, freeze)
    build_active_extraction_schema()
    config = build_config()
    atomic_json(ACTIVE_CONFIG, config)
    with ProductionStore(ROOT / PRODUCTION_DB, ROOT / "config/schema.json") as store:
        store.register_config(config["config_snapshot_id"], config["config_manifest"])
        store.integrity_check()
    migrated = migrate_unsuccessful_tasks_to_config(config)
    assign_batches(ROOT / FULLTEXT_DB)
    sync_parse_status(ROOT, ROOT / FULLTEXT_DB, ROOT / CANDIDATE_DB)
    manifest_rows = write_production_manifest()
    seeded = seed_reviewed_candidates(config)
    approved_verified = verify_reviewed_candidates_once(config)
    with ProductionStore(ROOT / PRODUCTION_DB, ROOT / "config/schema.json") as store:
        summary = store.task_summary()
    result = {
        "status": "prepared", "config_snapshot_id": config["config_snapshot_id"],
        "manifest_rows": manifest_rows, "new_tasks_seeded": seeded,
        "approved_pilot_tasks_verified_once": approved_verified,
        "tasks_reset_after_systemic_repair": migrated,
        "qwen_task_status": summary, "freeze_manifest": FREEZE_MANIFEST.relative_to(ROOT).as_posix(),
    }
    atomic_json(RUNTIME_DIR / "prepare_report.json", result)
    return result


def evidence(value: Any, quote: str, unit: str | None = None) -> dict[str, Any]:
    return {
        "value_raw": value, "value_normalized": value, "unit": unit,
        "evidence_text": quote, "evidence_section": "Experimental", "evidence_page": 1,
        "confidence": "high", "value_status": "reported",
    }


def smoke_test() -> dict[str, Any]:
    if not ACTIVE_CONFIG.exists():
        prepare()
    config = json.loads(ACTIVE_CONFIG.read_text(encoding="utf-8"))
    quote = "Fe and Mo on MgO were heated at 750 °C under methane for 30 min and produced multi-walled carbon nanotubes."
    package = {
        "source_id": "SMOKE_SOURCE", "source_title": "Smoke test", "input_content_hash": "a" * 64,
        "spans": [{"span_id": "SPAN_001", "text": quote}],
    }
    payload = {
        "schema_version": "0.2", "source_id": "SMOKE_SOURCE", "input_content_hash": "a" * 64,
        "run_candidates": [{"candidate_run_id": "RUN_CAND_001", "fields": {"run_summary": evidence("CNT synthesis", quote)}}],
        "catalyst_candidates": [{"candidate_catalyst_id": "CAT_CAND_001", "candidate_run_id": "RUN_CAND_001", "fields": {
            "catalyst_label": evidence("Fe-Mo/MgO", quote), "active_metals": evidence(["Fe", "Mo"], quote),
            "support_material": evidence("MgO", quote), "preparation_method": evidence("not_reported", quote),
        }}],
        "process_stage_candidates": [{"candidate_stage_id": "STAGE_CAND_001", "candidate_run_id": "RUN_CAND_001", "fields": {
            "stage_type": evidence("cnt_growth", quote), "temperature_setpoint_C": evidence(750, quote, "°C"),
            "holding_time_min": evidence(30, quote, "min"), "carbon_source": evidence("methane", quote),
        }}],
        "product_candidates": [{"candidate_product_id": "PROD_CAND_001", "candidate_run_id": "RUN_CAND_001", "fields": {
            "primary_yield_metric": evidence("reported_yield_other", quote), "yield_original": evidence("produced", quote),
            "CNT_type_reported": evidence("MWCNT", quote),
        }}],
        "cost_scale_candidates": [], "review_issues": [], "extraction_notes": "mock",
    }
    extraction_schema = json.loads((ROOT / config["extraction_schema_path"]).read_text(encoding="utf-8"))
    formal_schema = json.loads((ROOT / "config/schema.json").read_text(encoding="utf-8"))
    unit_rules = json.loads((ROOT / config["unit_rules_path"]).read_text(encoding="utf-8"))
    validation = validate_payload(payload, package, extraction_schema, formal_schema, unit_rules)
    if not validation["valid"]:
        raise RuntimeError(f"mock_validation_failed:{validation}")
    metadata = {"source_type": "paper", "title": "Smoke test", "year": 2026}
    rows = build_staging_rows(payload, metadata, formal_schema, "REV_SMOKE")
    validate_rows_with_formal_validator(rows, formal_schema, ROOT / "config/schema.json", ROOT / "config/field_dictionary.csv")
    import tempfile
    with tempfile.TemporaryDirectory(prefix="cnt_patsight_smoke_") as temporary:
        db = Path(temporary) / "smoke.sqlite3"
        with ProductionStore(db, ROOT / "config/schema.json") as store:
            store.register_config("SMOKE_CFG", {})
            task_id = "SMOKE_TASK"
            store.enqueue(task_id, "SMOKE_SOURCE", "a" * 64, "SMOKE_CFG", 1)
            task = store.claim("smoke-worker")
            assert task is not None
            rolled_back = False
            try:
                store.write_staging(task, "REV_SMOKE", rows, validation, fail_after_table="source_run")
            except RuntimeError:
                rolled_back = store.connection.execute("SELECT COUNT(*) FROM source_master").fetchone()[0] == 0
            if not rolled_back:
                raise RuntimeError("transaction_rollback_smoke_failed")
            store.write_staging(task, "REV_SMOKE", rows, validation)
            store.finish_task(task_id, "succeeded", "needs_review")
            stale_id = "SMOKE_STALE"
            store.enqueue(stale_id, "STALE_SOURCE", "b" * 64, "SMOKE_CFG", 2)
            store.claim("dead-worker")
            old = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
            store.connection.execute("UPDATE qwen_tasks SET heartbeat_at=? WHERE task_id=?", (old, stale_id))
            store.connection.commit()
            recovered = store.recover_stale(utc_now())
            if recovered != 1:
                raise RuntimeError("stale_recovery_smoke_failed")
            store.integrity_check()
    result = {"status": "passed", "validation": validation, "transaction_rollback": "passed", "stale_recovery": "passed", "completed_at": utc_now()}
    atomic_json(SMOKE_REPORT, result)
    return result


def load_config() -> dict[str, Any]:
    if not ACTIVE_CONFIG.exists():
        raise RuntimeError("run prepare first")
    return json.loads(ACTIVE_CONFIG.read_text(encoding="utf-8"))


def component_info(component: str) -> dict[str, Any]:
    pid_path = RUNTIME_DIR / "pids" / f"{component}.pid"
    heartbeat_path = RUNTIME_DIR / "heartbeats" / f"{component}.json"
    pid = int(pid_path.read_text(encoding="ascii")) if pid_path.exists() else 0
    heartbeat = json.loads(heartbeat_path.read_text(encoding="utf-8")) if heartbeat_path.exists() else {}
    age = None
    if heartbeat.get("heartbeat_at"):
        stamp = datetime.fromisoformat(heartbeat["heartbeat_at"].replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - stamp).total_seconds()
    return {"pid": pid, "alive": pid_alive(pid), "heartbeat_age_seconds": age, "state": heartbeat.get("state", "missing"), "heartbeat": heartbeat_path.relative_to(ROOT).as_posix(), "log": (RUNTIME_DIR / "logs" / f"{component}.log").relative_to(ROOT).as_posix()}


def funnel() -> dict[str, Any]:
    fulltext = sqlite3.connect(ROOT / FULLTEXT_DB)
    fulltext.row_factory = sqlite3.Row
    ft = {row["download_status"]: row["n"] for row in fulltext.execute("SELECT download_status,COUNT(*) n FROM fulltext_acquisition_queue GROUP BY download_status")}
    tiers = {row["priority_tier"]: row["n"] for row in fulltext.execute("SELECT priority_tier,COUNT(*) n FROM fulltext_acquisition_queue GROUP BY priority_tier")}
    fulltext.close()
    candidate = sqlite3.connect(ROOT / CANDIDATE_DB)
    candidate.row_factory = sqlite3.Row
    quality = {row["parse_quality"]: row["n"] for row in candidate.execute("SELECT parse_quality,COUNT(*) n FROM parse_source_status GROUP BY parse_quality")}
    relevance = {row["fulltext_relevance_status"]: row["n"] for row in candidate.execute("SELECT fulltext_relevance_status,COUNT(*) n FROM parse_source_status GROUP BY fulltext_relevance_status")}
    candidate.close()
    with ProductionStore(ROOT / PRODUCTION_DB, ROOT / "config/schema.json") as store:
        tasks = store.task_summary(); dispositions = store.disposition_summary(); staged = store.staged_source_count()
        task_sources = int(store.connection.execute("SELECT COUNT(DISTINCT source_id) FROM qwen_tasks").fetchone()[0])
    formal = 0
    for path in (ROOT / "data/interim").glob("P*/source_master.csv"):
        with path.open(encoding="utf-8-sig", newline="") as handle:
            formal += sum(1 for row in csv.DictReader(handle) if row.get("screening_class") == "formal_extract")
    acquired = sum(ft.get(name, 0) for name in ("validated", "local_existing"))
    failed = sum(ft.get(name, 0) for name in ("blocked", "paywalled", "not_found", "failed_final", "not_pdf"))
    return {
        "metadata_total": 1487, "A_total": tiers.get("A", 0), "B_total": tiers.get("B", 0),
        "fulltext_queued": ft.get("queued", 0) + ft.get("failed_retryable", 0),
        "fulltext_acquired": acquired, "fulltext_failed": failed,
        "parsed_good": quality.get("good", 0), "parsed_partial": quality.get("partial", 0),
        "candidate_extract": max(relevance.get("candidate_extract", 0), task_sources),
        "qwen_pending": tasks.get("pending", 0) + tasks.get("failed_retryable", 0) + tasks.get("interrupted", 0),
        "qwen_running": tasks.get("running", 0), "qwen_succeeded": tasks.get("succeeded", 0),
        "validation_failed": tasks.get("validation_failed", 0),
        "needs_review": dispositions.get("needs_review", 0), "staged_sources": staged,
        "formal_extract": formal,
    }


def status() -> dict[str, Any]:
    result = {"components": {name: component_info(name) for name in ("fulltext_producer", "qwen_consumer", "pipeline_monitor")}, "funnel": funnel(), "checked_at": utc_now()}
    atomic_json(RUNTIME_DIR / "funnel.json", result)
    return result


def start_components() -> dict[str, Any]:
    verify_freeze()
    if not SMOKE_REPORT.exists() or json.loads(SMOKE_REPORT.read_text(encoding="utf-8")).get("status") != "passed":
        raise RuntimeError("smoke-test must pass before start")
    existing = status()["components"]
    commands = {}
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    for component, worker in (("fulltext_producer", "fulltext"), ("qwen_consumer", "qwen"), ("pipeline_monitor", "monitor")):
        if existing[component]["alive"]:
            commands[component] = {"pid": existing[component]["pid"], "action": "already_running"}
            continue
        (RUNTIME_DIR / "stop" / f"{component}.stop").unlink(missing_ok=True)
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "worker", worker], cwd=ROOT,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=creationflags, close_fds=True,
        )
        commands[component] = {"launcher_pid": process.pid, "action": "started"}
    deadline = time.monotonic() + 25
    healthy = False
    latest = {}
    while time.monotonic() < deadline:
        time.sleep(2)
        latest = status()
        components = latest["components"].values()
        healthy = all(c["alive"] and c["heartbeat_age_seconds"] is not None and c["heartbeat_age_seconds"] < 15 for c in components)
        if healthy:
            break
    if not healthy:
        request_stop(True)
        raise RuntimeError(f"background_health_check_failed:{latest}")
    return {
        "status": "healthy", "launch": commands, **latest,
        "progress_command": "python scripts/production/pipeline.py status --watch",
        "stop_command": "python scripts/production/pipeline.py stop --all",
        "resume_command": "python scripts/production/pipeline.py resume",
    }


def request_stop(all_components: bool) -> dict[str, Any]:
    names = ("fulltext_producer", "qwen_consumer", "pipeline_monitor") if all_components else ()
    for name in names:
        path = RUNTIME_DIR / "stop" / f"{name}.stop"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(utc_now(), encoding="ascii")
    return {"status": "stop_requested", "components": list(names)}


def resume() -> dict[str, Any]:
    verify_freeze()
    config = load_config()
    stale_before = (datetime.now(timezone.utc) - timedelta(seconds=60)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    with ProductionStore(ROOT / config["production_db"], ROOT / "config/schema.json") as store:
        recovered = store.recover_stale(stale_before)
        store.integrity_check()
    for path in (RUNTIME_DIR / "stop").glob("*.stop"):
        path.unlink(missing_ok=True)
    result = start_components()
    result["recovered_stale_tasks"] = recovered
    return result


def worker(component: str) -> None:
    verify_freeze()
    config = load_config()
    if component == "fulltext": fulltext_worker(ROOT, config)
    elif component == "qwen": qwen_worker(ROOT, config)
    elif component == "monitor": monitor_worker(ROOT, config)
    else: raise ValueError(component)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CNT-PatSight continuous producer/consumer control")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    sub.add_parser("smoke-test")
    sub.add_parser("start")
    stat = sub.add_parser("status"); stat.add_argument("--watch", action="store_true"); stat.add_argument("--interval", type=int, default=10)
    stop = sub.add_parser("stop"); stop.add_argument("--all", action="store_true", required=True)
    sub.add_parser("resume")
    work = sub.add_parser("worker"); work.add_argument("component", choices=["fulltext", "qwen", "monitor"])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "prepare": result = prepare()
    elif args.command == "smoke-test": result = smoke_test()
    elif args.command == "start": result = start_components()
    elif args.command == "stop": result = request_stop(args.all)
    elif args.command == "resume": result = resume()
    elif args.command == "worker": worker(args.component); return 0
    elif args.command == "status":
        if args.watch:
            try:
                while True:
                    print(json.dumps(status(), ensure_ascii=False, indent=2)); time.sleep(max(1, args.interval))
            except KeyboardInterrupt: return 0
        result = status()
    else: raise AssertionError(args.command)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
