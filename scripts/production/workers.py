from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import sqlite3
import subprocess
import threading
import time
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts.extract_llm.package import build_package, canonical_json
from scripts.extract_llm.runner import extract_first_json
from scripts.fetch_fulltext.pipeline import FulltextPipeline
from scripts.parse_fulltext.pipeline import ParsePipeline
from scripts.production.staging import (
    build_staging_rows,
    collapse_identical_candidate_duplicates,
    package_with_contract,
    validate_payload,
    validate_rows_with_formal_validator,
)
from scripts.production.store import ProductionStore, utc_now


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class ComponentRuntime:
    def __init__(self, runtime_dir: Path, component: str):
        self.component = component
        self.pid = os.getpid()
        self.host = socket.gethostname()
        self.lock_path = runtime_dir / "locks" / f"{component}.lock.json"
        self.pid_path = runtime_dir / "pids" / f"{component}.pid"
        self.heartbeat_path = runtime_dir / "heartbeats" / f"{component}.json"
        self.stop_path = runtime_dir / "stop" / f"{component}.stop"
        self.log_path = runtime_dir / "logs" / f"{component}.log"
        self._state = "starting"
        self._detail: dict[str, Any] = {}
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def acquire(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        if self.lock_path.exists():
            try:
                lock = json.loads(self.lock_path.read_text(encoding="utf-8"))
                old_pid = int(lock.get("pid", 0))
            except Exception:
                old_pid = 0
            if pid_alive(old_pid):
                raise RuntimeError(f"duplicate_component_start:{self.component}:pid={old_pid}")
            self.lock_path.unlink(missing_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        fd = os.open(self.lock_path, flags)
        try:
            os.write(fd, json.dumps({"pid": self.pid, "host": self.host, "started_at": utc_now()}).encode("utf-8"))
        finally:
            os.close(fd)
        self.pid_path.parent.mkdir(parents=True, exist_ok=True)
        self.pid_path.write_text(str(self.pid), encoding="ascii")
        self.stop_path.unlink(missing_ok=True)
        self._thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._thread.start()

    def set_state(self, state: str, **detail: Any) -> None:
        self._state = state
        self._detail = detail
        self._write_heartbeat()

    def should_stop(self) -> bool:
        return self._stop.is_set() or self.stop_path.exists()

    def log(self, message: str) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{utc_now()} {message}\n")

    def release(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        self.set_state("stopped")
        self.pid_path.unlink(missing_ok=True)
        self.lock_path.unlink(missing_ok=True)

    def _heartbeat_loop(self) -> None:
        while not self._stop.wait(10):
            self._write_heartbeat()

    def _write_heartbeat(self) -> None:
        atomic_json(self.heartbeat_path, {
            "component": self.component, "pid": self.pid, "host": self.host,
            "state": self._state, "detail": self._detail, "heartbeat_at": utc_now(),
        })


class QwenRunner:
    def __init__(self, root: Path, config: dict[str, Any], runtime: ComponentRuntime):
        self.root = root
        self.config = config
        self.runtime = runtime
        self.model = root / config["model_path"]
        self.executable = root / config["runtime_path"]
        self.schema_path = root / config["extraction_schema_path"]
        self.prompt_path = root / config["prompt_path"]
        self.section_csv = root / "data/interim/extraction_candidates/paper_text_section.csv"
        self.span_csv = root / "data/interim/extraction_candidates/candidate_experiment_span.csv"
        self.raw_root = root / "data/interim/llm_extraction/raw_v0.2"
        self.formal_schema = json.loads((root / "config/schema.json").read_text(encoding="utf-8"))

    def build_package(self, source_id: str) -> dict[str, Any]:
        # Keep enough experimental evidence for extraction while reserving model
        # context for a complete schema-constrained response.
        package = build_package(source_id, self.section_csv, self.span_csv, 9000, 60)
        return package_with_contract(package, self.formal_schema)

    def run(self, task: dict[str, Any], package: dict[str, Any], store: ProductionStore) -> tuple[dict[str, Any], str, str]:
        identity = {
            "source_id": task["source_id"], "input_hash": task["input_content_hash"],
            "config_snapshot_id": task["config_snapshot_id"], "package": package,
        }
        request_hash = hashlib.sha256(canonical_json(identity).encode("utf-8")).hexdigest()[:20]
        attempt = int(task["attempt_count"])
        attempt_dir = self.raw_root / task["source_id"] / task["task_id"] / f"attempt_{attempt:03d}"
        if attempt_dir.exists():
            attempt_dir = attempt_dir.with_name(f"attempt_{attempt:03d}_{uuid.uuid4().hex[:6]}")
        attempt_dir.mkdir(parents=True, exist_ok=False)
        atomic_json(attempt_dir / "package.json", package)
        prompt_template = self.prompt_path.read_text(encoding="utf-8")
        prompt_body = prompt_template.replace("{{INPUT_JSON}}", json.dumps(package, ensure_ascii=False, indent=2))
        prompt = "<|im_start|>system\nYou are a strict scientific extractor. Output JSON only. /no_think<|im_end|>\n<|im_start|>user\n" + prompt_body + "<|im_end|>\n<|im_start|>assistant\n"
        (attempt_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        command = [
            str(self.executable), "-m", str(self.model), "-dev", self.config["device"],
            "-ngl", "all", "-c", str(self.config["context_size"]), "-n", str(self.config["max_tokens"]),
            "-b", "512", "-ub", "256", "-ctk", "q8_0", "-ctv", "q8_0", "-fa", "on",
            "--temp", "0", "--seed", "42", "--no-conversation", "--single-turn", "--simple-io",
            "--color", "off", "--no-display-prompt", "--no-warmup",
            "--json-schema-file", str(self.schema_path), "--file", str(attempt_dir / "prompt.txt"),
        ]
        self.runtime.set_state("running_inference", source_id=task["source_id"], task_id=task["task_id"])
        stdout_path = attempt_dir / "stdout.txt"
        stderr_path = attempt_dir / "stderr.txt"
        # On Windows an unread PIPE can fill after roughly 4 KiB and truncate
        # or deadlock long JSON. Stream directly to files while polling.
        with stdout_path.open("w", encoding="utf-8") as stdout_handle, stderr_path.open("w", encoding="utf-8") as stderr_handle:
            process = subprocess.Popen(command, cwd=self.root, stdout=stdout_handle, stderr=stderr_handle, text=True, encoding="utf-8", errors="replace")
            deadline = time.monotonic() + int(self.config["timeout_seconds"])
            while process.poll() is None:
                if time.monotonic() > deadline:
                    process.kill()
                    process.wait(timeout=30)
                    raise TimeoutError("qwen_inference_timeout")
                store.heartbeat_task(task["task_id"], self.runtime.component + f":{self.runtime.pid}")
                time.sleep(5)
        stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
        stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
        if process.returncode != 0:
            raise RuntimeError(f"llama_completion_returncode_{process.returncode}")
        payload, repair_count = extract_first_json(stdout)
        atomic_json(attempt_dir / "result.json", payload)
        atomic_json(attempt_dir / "run.json", {
            "request_hash": request_hash, "returncode": process.returncode,
            "json_control_character_repairs": repair_count, "completed_at": utc_now(),
        })
        return payload, request_hash, attempt_dir.relative_to(self.root).as_posix()


def qwen_worker(root: Path, config: dict[str, Any]) -> None:
    runtime = ComponentRuntime(root / "data/interim/runtime", "qwen_consumer")
    runtime.acquire()
    worker_id = runtime.component + f":{runtime.pid}"
    store = ProductionStore(root / config["production_db"], root / "config/schema.json")
    runner = QwenRunner(root, config, runtime)
    extraction_schema = json.loads((root / config["extraction_schema_path"]).read_text(encoding="utf-8"))
    formal_schema = json.loads((root / "config/schema.json").read_text(encoding="utf-8"))
    unit_rules = json.loads((root / config["unit_rules_path"]).read_text(encoding="utf-8"))
    try:
        runtime.log("qwen consumer started")
        while not runtime.should_stop():
            task = store.claim(worker_id)
            if task is None:
                runtime.set_state("idle_waiting_for_tasks")
                time.sleep(30)
                continue
            try:
                package = runner.build_package(task["source_id"])
                if package["input_content_hash"] != task["input_content_hash"]:
                    raise ValueError("queued_input_hash_no_longer_matches_parser_output")
                raw_payload, request_hash, raw_path = runner.run(task, package, store)
                payload, collapsed = collapse_identical_candidate_duplicates(raw_payload)
                if collapsed:
                    atomic_json(root / raw_path / "normalized_result.json", payload)
                report = validate_payload(payload, package, extraction_schema, formal_schema, unit_rules)
                if collapsed:
                    report["warnings"].append({
                        "code": "identical_candidate_duplicates_collapsed",
                        "message": json.dumps(collapsed, ensure_ascii=False),
                    })
                    report["warning_count"] = len(report["warnings"])
                atomic_json(root / raw_path / "validation.json", report)
                if not report["valid"]:
                    retry = int(task["attempt_count"]) < int(task["max_attempts"])
                    store.finish_task(task["task_id"], "validation_failed" if not retry else "failed_retryable", "reextract_required", request_hash=request_hash, raw_result_path=raw_path, error=json.dumps(report["errors"], ensure_ascii=False))
                    continue
                revision_id = f"REV_{request_hash.upper()}"
                metadata = load_metadata(root / config["metadata_db"], task["source_id"])
                rows = build_staging_rows(payload, metadata, formal_schema, revision_id)
                validate_rows_with_formal_validator(rows, formal_schema, root / "config/schema.json", root / "config/field_dictionary.csv")
                store.write_staging(task, revision_id, rows, report)
                store.finish_task(task["task_id"], "succeeded", "needs_review", request_hash=request_hash, raw_result_path=raw_path)
                runtime.log(f"succeeded {task['source_id']} {request_hash}")
            except Exception as exc:
                retry = int(task["attempt_count"]) < int(task["max_attempts"])
                store.finish_task(task["task_id"], "failed_retryable" if retry else "failed_final", "reextract_required", error=f"{type(exc).__name__}:{exc}")
                runtime.log(f"failed {task['source_id']} {type(exc).__name__}:{exc}")
        runtime.log("qwen consumer stop requested")
    finally:
        store.close()
        runtime.release()


def load_metadata(metadata_db: Path, source_id: str) -> dict[str, Any]:
    connection = sqlite3.connect(metadata_db)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute("SELECT * FROM works WHERE source_id=?", (source_id,)).fetchone()
        if row is None:
            raise KeyError(f"metadata_source_missing:{source_id}")
        return dict(row)
    finally:
        connection.close()


def _ensure_fulltext_runtime_columns(fulltext_db: Path) -> None:
    connection = sqlite3.connect(fulltext_db)
    columns = {r[1] for r in connection.execute("PRAGMA table_info(fulltext_acquisition_queue)")}
    additions = {
        "batch_id": "TEXT NOT NULL DEFAULT ''",
        "lease_owner": "TEXT NOT NULL DEFAULT ''",
        "lease_at": "TEXT NOT NULL DEFAULT ''",
        "next_attempt_at": "TEXT NOT NULL DEFAULT ''",
        "parse_status": "TEXT NOT NULL DEFAULT ''",
        "fulltext_relevance_status": "TEXT NOT NULL DEFAULT ''",
        "identity_check_status": "TEXT NOT NULL DEFAULT 'not_checked'",
    }
    for name, declaration in additions.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE fulltext_acquisition_queue ADD COLUMN {name} {declaration}")
    connection.commit()
    connection.close()


def assign_batches(fulltext_db: Path) -> None:
    _ensure_fulltext_runtime_columns(fulltext_db)
    connection = sqlite3.connect(fulltext_db)
    connection.row_factory = sqlite3.Row
    for tier in ("A", "B"):
        rows = connection.execute(
            "SELECT source_id FROM fulltext_acquisition_queue WHERE priority_tier=? ORDER BY queue_priority,source_id",
            (tier,),
        ).fetchall()
        for index, row in enumerate(rows):
            # A has four monitoring checkpoints 50/50/50/58. B uses seven
            # groups of 50 and a final group of 21.
            if tier == "A":
                batch = 1 if index < 50 else 2 if index < 100 else 3 if index < 150 else 4
            else:
                batch = index // 50 + 1
            connection.execute(
                "UPDATE fulltext_acquisition_queue SET batch_id=? WHERE source_id=?",
                (f"{tier}_{batch:02d}", row["source_id"]),
            )
    connection.commit()
    connection.close()


def sync_parse_status(root: Path, fulltext_db: Path, candidate_db: Path) -> None:
    connection = sqlite3.connect(fulltext_db)
    connection.execute("ATTACH DATABASE ? AS candidate", (str(candidate_db),))
    connection.execute(
        """
        UPDATE fulltext_acquisition_queue SET
            parse_status=COALESCE((SELECT parse_status FROM candidate.parse_source_status p WHERE p.source_id=fulltext_acquisition_queue.source_id),''),
            fulltext_relevance_status=COALESCE((SELECT fulltext_relevance_status FROM candidate.parse_source_status p WHERE p.source_id=fulltext_acquisition_queue.source_id),'')
        """
    )
    connection.commit()
    connection.close()


def claim_fulltext(fulltext_db: Path, worker_id: str) -> str | None:
    connection = sqlite3.connect(fulltext_db, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("BEGIN IMMEDIATE")
    now = utc_now()
    try:
        # A must reach success/terminal outcomes before B starts.
        a_open = connection.execute(
            """SELECT COUNT(*) FROM fulltext_acquisition_queue WHERE priority_tier='A' AND
               ((download_status IN ('queued','failed_retryable','downloading') AND attempt_count < max_attempts)
                OR (download_status IN ('validated','local_existing') AND parse_status!='success'))"""
        ).fetchone()[0]
        tier = "A" if a_open else "B"
        row = connection.execute(
            """
            SELECT source_id FROM fulltext_acquisition_queue
            WHERE priority_tier=? AND (lease_owner='' OR lease_at < ?)
              AND ((download_status IN ('queued','failed_retryable','downloading') AND attempt_count < max_attempts)
                   OR (download_status IN ('validated','local_existing') AND parse_status!='success'))
              AND (next_attempt_at='' OR next_attempt_at<=?)
            ORDER BY queue_priority,source_id LIMIT 1
            """,
            (tier, (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat().replace("+00:00", "Z"), now),
        ).fetchone()
        if row is None:
            connection.commit()
            return None
        connection.execute(
            "UPDATE fulltext_acquisition_queue SET lease_owner=?,lease_at=? WHERE source_id=?",
            (worker_id, now, row["source_id"]),
        )
        connection.commit()
        return str(row["source_id"])
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def release_fulltext(fulltext_db: Path, source_id: str, retry_delay_seconds: int = 0) -> None:
    next_attempt = ""
    if retry_delay_seconds:
        next_attempt = (datetime.now(timezone.utc) + timedelta(seconds=retry_delay_seconds)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    connection = sqlite3.connect(fulltext_db)
    connection.execute(
        "UPDATE fulltext_acquisition_queue SET lease_owner='',lease_at='',next_attempt_at=? WHERE source_id=?",
        (next_attempt, source_id),
    )
    connection.commit()
    connection.close()


def enqueue_auto_candidate(root: Path, config: dict[str, Any], source_id: str) -> bool:
    candidate_db = root / config["candidate_db"]
    connection = sqlite3.connect(candidate_db)
    connection.row_factory = sqlite3.Row
    row = connection.execute("SELECT * FROM parse_source_status WHERE source_id=?", (source_id,)).fetchone()
    connection.close()
    if row is None or row["parse_status"] != "success" or not int(row["candidate_extract_eligible"]):
        return False
    input_hash = str(row["input_content_hash"])
    task_id = "QT_" + hashlib.sha256(f"{source_id}|{input_hash}|{config['config_snapshot_id']}".encode()).hexdigest()[:20].upper()
    with ProductionStore(root / config["production_db"], root / "config/schema.json") as store:
        return store.enqueue(task_id, source_id, input_hash, config["config_snapshot_id"], 1000, "candidate_extract")


def fulltext_worker(root: Path, config: dict[str, Any]) -> None:
    runtime = ComponentRuntime(root / "data/interim/runtime", "fulltext_producer")
    runtime.acquire()
    worker_id = runtime.component + f":{runtime.pid}"
    fulltext_db = root / config["fulltext_db"]
    candidate_db = root / config["candidate_db"]
    assign_batches(fulltext_db)
    fetcher = FulltextPipeline(
        root, root / config["metadata_db"], fulltext_db,
        root / "data/raw/fulltext/pdf", root / "data/raw/fulltext/html",
        root / "data/raw/fulltext/reports", root / "data/raw/fulltext/fulltext_source.csv",
        root / "data/raw/fulltext/fulltext_coverage.csv", root / ".env",
        queue_csv=root / "data/raw/fulltext/fulltext_acquisition_queue.csv",
        max_queue_attempts=3, verified_candidates_csv=root / "data/raw/fulltext/verified_oa_candidates.csv",
    )
    try:
        runtime.log("fulltext producer started")
        while not runtime.should_stop():
            sync_parse_status(root, fulltext_db, candidate_db)
            source_id = claim_fulltext(fulltext_db, worker_id)
            if source_id is None:
                runtime.set_state("idle_waiting_for_fulltext_tasks")
                time.sleep(30)
                continue
            runtime.set_state("processing_source", source_id=source_id)
            try:
                fetcher.run([source_id], 1, from_queue=True)
                parser = ParsePipeline(
                    root, root / config["metadata_db"], fulltext_db, candidate_db,
                    root / "data/raw/fulltext/text", root / "data/interim/parsed_text",
                    root / "data/interim/extraction_candidates/paper_text_section.csv",
                    root / "data/interim/extraction_candidates/candidate_experiment_span.csv",
                    root / "data/interim/extraction_candidates/parse_source_status.csv",
                    root / "data/interim/extraction_candidates/reports",
                    ocr_queue_csv=root / "data/interim/extraction_candidates/ocr_queue.csv",
                )
                parser.run([source_id], 1)
                sync_parse_status(root, fulltext_db, candidate_db)
                enqueue_auto_candidate(root, config, source_id)
                release_fulltext(fulltext_db, source_id)
                runtime.log(f"processed {source_id}")
            except Exception as exc:
                connection = sqlite3.connect(fulltext_db)
                row = connection.execute("SELECT attempt_count,download_status FROM fulltext_acquisition_queue WHERE source_id=?", (source_id,)).fetchone()
                connection.close()
                delay = (300, 1800, 7200)[min(max((row[0] if row else 1) - 1, 0), 2)] if row and row[1] == "failed_retryable" else 0
                release_fulltext(fulltext_db, source_id, delay)
                runtime.log(f"source failure {source_id} {type(exc).__name__}:{exc}")
        runtime.log("fulltext producer stop requested")
    finally:
        runtime.release()


def _request_component_stop(root: Path, component: str, reason: str) -> None:
    stop = root / "data/interim/runtime/stop" / f"{component}.stop"
    stop.parent.mkdir(parents=True, exist_ok=True)
    stop.write_text(f"{utc_now()} {reason}", encoding="utf-8")


def _verify_frozen_assets(root: Path) -> list[str]:
    manifest_path = root / "data/interim/runtime/production_freeze_manifest.json"
    if not manifest_path.exists():
        return ["freeze_manifest_missing"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    for item in manifest.get("files", []):
        path = Path(item["path"])
        path = path if path.is_absolute() else root / path
        if not path.exists() or path.stat().st_size != item["bytes"]:
            failures.append(str(item["path"]))
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != item["sha256"]:
            failures.append(str(item["path"]))
    return failures


def _new_repeated_log_error(log_path: Path, offset: int) -> tuple[str, int, int]:
    if not log_path.exists():
        return "", 0, 0
    size = log_path.stat().st_size
    if size < offset:
        offset = 0
    with log_path.open("rb") as handle:
        handle.seek(offset)
        lines = handle.read().decode("utf-8", errors="replace").splitlines()
    messages = []
    for line in lines:
        if " source failure " in line or " failed " in line:
            message = re.sub(r"^\S+\s+", "", line)
            message = re.sub(r"\b(?:LIT_[A-Z0-9]+|P\d+_[^ ]+)\b", "<source>", message)
            messages.append(message)
    if not messages:
        return "", 0, size
    message, count = Counter(messages).most_common(1)[0]
    return message, count, size


def monitor_worker(root: Path, config: dict[str, Any], interval_seconds: int = 600) -> None:
    """Local ten-minute watchdog; pauses systemic failures, never edits facts."""
    runtime = ComponentRuntime(root / "data/interim/runtime", "pipeline_monitor")
    runtime.acquire()
    report_dir = root / "data/interim/runtime/monitor"
    report_dir.mkdir(parents=True, exist_ok=True)
    previous: dict[str, int] = {}
    producer_log = root / "data/interim/runtime/logs/fulltext_producer.log"
    qwen_log = root / "data/interim/runtime/logs/qwen_consumer.log"
    producer_offset = producer_log.stat().st_size if producer_log.exists() else 0
    qwen_offset = qwen_log.stat().st_size if qwen_log.exists() else 0
    try:
        runtime.log("pipeline monitor started interval_seconds=600")
        while not runtime.should_stop():
            checked_at = utc_now()
            alerts: list[dict[str, Any]] = []
            frozen_failures = _verify_frozen_assets(root)
            if frozen_failures:
                alerts.append({"type": "frozen_asset_mismatch", "files": frozen_failures, "component": "all"})
            try:
                with ProductionStore(root / config["production_db"], root / "config/schema.json") as store:
                    store.integrity_check()
                    task_counts = store.task_summary()
            except Exception as exc:
                task_counts = {}
                alerts.append({"type": "production_database_integrity", "error": f"{type(exc).__name__}:{exc}", "component": "all"})
            producer_error, producer_repeats, producer_offset = _new_repeated_log_error(producer_log, producer_offset)
            qwen_error, qwen_repeats, qwen_offset = _new_repeated_log_error(qwen_log, qwen_offset)
            failed_growth = task_counts.get("failed_final", 0) - previous.get("failed_final", task_counts.get("failed_final", 0))
            validation_growth = task_counts.get("validation_failed", 0) - previous.get("validation_failed", task_counts.get("validation_failed", 0))
            if failed_growth >= 2 or validation_growth >= 2 or qwen_repeats >= 3:
                alerts.append({"type": "qwen_systemic_failure", "failed_growth": failed_growth, "validation_growth": validation_growth, "repeated_error": qwen_error, "component": "qwen_consumer"})
            if producer_repeats >= 3:
                alerts.append({"type": "producer_repeated_error", "repeated_error": producer_error, "count": producer_repeats, "component": "fulltext_producer"})
            previous = dict(task_counts)
            for alert in alerts:
                component = alert["component"]
                if component == "all":
                    _request_component_stop(root, "fulltext_producer", alert["type"])
                    _request_component_stop(root, "qwen_consumer", alert["type"])
                else:
                    _request_component_stop(root, component, alert["type"])
            report = {
                "checked_at": checked_at, "status": "alert" if alerts else "healthy",
                "task_counts": task_counts, "alerts": alerts,
                "producer_repeated_error_count": producer_repeats,
                "qwen_repeated_error_count": qwen_repeats,
            }
            atomic_json(report_dir / "latest.json", report)
            with (report_dir / "history.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(report, ensure_ascii=False) + "\n")
            runtime.set_state("alert_paused" if alerts else "healthy_waiting", **report)
            runtime.log(json.dumps(report, ensure_ascii=False))
            # Ten-minute interval with responsive cooperative stop checks.
            for _ in range(max(1, interval_seconds // 10)):
                if runtime.should_stop():
                    break
                time.sleep(10)
    finally:
        runtime.release()
