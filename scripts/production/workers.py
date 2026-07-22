from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import sqlite3
import threading
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts.fetch_fulltext.pipeline import FulltextPipeline
from scripts.io_utils import atomic_write_json
from scripts.parse_fulltext.pipeline import ParsePipeline
from scripts.production.store import ProductionStore, utc_now


CURATED_EXCLUSION_REASON = "existing_curated_eight_table_package"


def curated_source_packages(root: Path) -> dict[str, str]:
    """Return direct per-source packages that must not be re-enqueued."""
    packages: dict[str, str] = {}
    for source_master in sorted((root / "data/benchmark/fixtures/six_papers").glob("P*/source_master.csv")):
        source_id = source_master.parent.name
        packages[source_id] = source_master.parent.relative_to(root).as_posix()
    return packages


def register_curated_source_exclusions(root: Path, store: ProductionStore) -> int:
    added = 0
    for source_id, evidence_path in curated_source_packages(root).items():
        added += int(store.exclude_source(
            source_id, CURATED_EXCLUSION_REASON, evidence_path,
        ))
    return added


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        # os.kill(pid, 0) is not a reliable existence probe for detached
        # Windows processes. Query a real process handle so status/start never
        # mistake a live worker for a stale lock and launch a duplicate.
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_int
        handle = kernel32.OpenProcess(0x1000, 0, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return ctypes.get_last_error() == 5  # access denied still means alive
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
        atomic_write_json(self.heartbeat_path, {
            "component": self.component, "pid": self.pid, "host": self.host,
            "state": self._state, "detail": self._detail, "heartbeat_at": utc_now(),
        })


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
        "production_lane": "TEXT NOT NULL DEFAULT 'A'",
        "metadata_enrichment_status": "TEXT NOT NULL DEFAULT ''",
        "fulltext_status": "TEXT NOT NULL DEFAULT 'pending'",
        "acquisition_status": "TEXT NOT NULL DEFAULT 'queued'",
        "publisher_url": "TEXT NOT NULL DEFAULT ''",
        "manual_access_url": "TEXT NOT NULL DEFAULT ''",
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
    for lane in ("A", "B", "C", "D"):
        rows = connection.execute(
            "SELECT source_id FROM fulltext_acquisition_queue WHERE production_lane=? ORDER BY queue_priority,source_id",
            (lane,),
        ).fetchall()
        for index, row in enumerate(rows):
            # A has four monitoring checkpoints 50/50/50/58. B uses seven
            # groups of 50 and a final group of 21.
            if lane == "A":
                batch = 1 if index < 50 else 2 if index < 100 else 3 if index < 150 else 4
            else:
                batch = index // 50 + 1
            connection.execute(
                "UPDATE fulltext_acquisition_queue SET batch_id=? WHERE source_id=?",
                (f"{lane}_{batch:02d}", row["source_id"]),
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
        lane = ""
        for candidate_lane in ("A", "B", "C", "D"):
            open_count = connection.execute(
                """SELECT COUNT(*) FROM fulltext_acquisition_queue WHERE production_lane=? AND
                   ((download_status IN ('queued','failed_retryable','downloading')
                     AND (attempt_count < max_attempts OR acquisition_status='retry_pending'))
                     OR (download_status IN ('validated','local_existing') AND parse_status!='success'))""",
                (candidate_lane,),
            ).fetchone()[0]
            if open_count:
                lane = candidate_lane
                break
        if not lane:
            connection.commit()
            return None
        row = connection.execute(
            """
            SELECT source_id FROM fulltext_acquisition_queue
            WHERE production_lane=? AND (lease_owner='' OR lease_at < ?)
              AND ((download_status IN ('queued','failed_retryable','downloading')
                    AND (attempt_count < max_attempts OR acquisition_status='retry_pending'))
                   OR (download_status IN ('validated','local_existing') AND parse_status!='success'))
              AND (next_attempt_at='' OR next_attempt_at<=?)
            ORDER BY queue_priority,source_id LIMIT 1
            """,
            (lane, (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat().replace("+00:00", "Z"), now),
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


def _active_enqueue_config(root: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    path = root / "runs/production/runtime/active_config.json"
    if not path.is_file():
        return fallback
    active = json.loads(path.read_text(encoding="utf-8"))
    if active.get("candidate_db") != fallback.get("candidate_db") or active.get("production_db") != fallback.get("production_db"):
        raise RuntimeError("active_config_queue_database_mismatch")
    return active


def enqueue_auto_candidate(root: Path, config: dict[str, Any], source_id: str) -> bool:
    config = _active_enqueue_config(root, config)
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
        register_curated_source_exclusions(root, store)
        return store.enqueue(task_id, source_id, input_hash, config["config_snapshot_id"], 1000, "candidate_extract")


def reconcile_candidate_queue(root: Path, config: dict[str, Any]) -> int:
    """Idempotently enqueue every currently eligible parsed source.

    This closes the crash window between a successful parse commit and the
    per-source enqueue call. It never removes the separately approved pilot
    tasks, even when a later Python rule classifies one as a review boundary.
    """
    config = _active_enqueue_config(root, config)
    connection = sqlite3.connect(root / config["candidate_db"])
    connection.row_factory = sqlite3.Row
    try:
        candidates = connection.execute(
            """SELECT source_id,input_content_hash FROM parse_source_status
               WHERE parse_status='success' AND candidate_extract_eligible=1
               ORDER BY source_id"""
        ).fetchall()
    finally:
        connection.close()
    enqueued = 0
    with ProductionStore(root / config["production_db"], root / "config/schema.json") as store:
        register_curated_source_exclusions(root, store)
        for row in candidates:
            source_id = str(row["source_id"])
            input_hash = str(row["input_content_hash"])
            task_id = "EXT_" + hashlib.sha256(
                f"{source_id}|{input_hash}|{config['config_snapshot_id']}".encode()
            ).hexdigest()[:20].upper()
            enqueued += int(store.enqueue(
                task_id, source_id, input_hash, config["config_snapshot_id"],
                1000, "candidate_extract",
            ))
    return enqueued


def fulltext_worker(root: Path, config: dict[str, Any]) -> None:
    runtime = ComponentRuntime(root / "runs/production/runtime", "fulltext_producer")
    runtime.acquire()
    worker_id = runtime.component + f":{runtime.pid}"
    fulltext_db = root / config["fulltext_db"]
    candidate_db = root / config["candidate_db"]
    with ProductionStore(root / config["production_db"], root / "config/schema.json") as store:
        register_curated_source_exclusions(root, store)
    fetcher = FulltextPipeline(
        root, root / config["metadata_db"], fulltext_db,
        root / "data/raw/literature/pdf", root / "data/raw/literature/html",
        root / "runs/fulltext", root / "data/raw/literature/metadata/fulltext_registry/fulltext_source.csv",
        root / "data/raw/literature/metadata/fulltext_registry/fulltext_coverage.csv", root / ".env",
        queue_csv=root / "data/raw/literature/metadata/fulltext_registry/fulltext_acquisition_queue.csv",
        max_queue_attempts=3, verified_candidates_csv=root / "data/raw/literature/metadata/fulltext_registry/verified_oa_candidates.csv",
    )
    queue_plan = fetcher.build_queue()
    assign_batches(fulltext_db)
    try:
        runtime.log(
            "fulltext producer started lanes="
            + json.dumps(queue_plan.get("production_lane_counts", {}), sort_keys=True)
        )
        while not runtime.should_stop():
            sync_parse_status(root, fulltext_db, candidate_db)
            reconciled = reconcile_candidate_queue(root, config)
            if reconciled:
                runtime.log(f"reconciled {reconciled} missing extraction task(s)")
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
                    root / "data/interim/parsed_text/by_source", root / "data/interim/parsed_text/by_source",
                    root / "cache/exports/paper_text_section.csv",
                    root / "cache/exports/candidate_experiment_span.csv",
                    root / "cache/exports/parse_source_status.csv",
                    root / "runs/parse",
                    ocr_queue_csv=root / "cache/exports/ocr_queue.csv",
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
    stop = root / "runs/production/runtime/stop" / f"{component}.stop"
    stop.parent.mkdir(parents=True, exist_ok=True)
    stop.write_text(f"{utc_now()} {reason}", encoding="utf-8")


def _verify_frozen_assets(root: Path) -> list[str]:
    manifest_path = root / "runs/production/runtime/production_freeze_manifest.json"
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
    runtime = ComponentRuntime(root / "runs/production/runtime", "pipeline_monitor")
    runtime.acquire()
    report_dir = root / "runs/production/runtime/monitor"
    report_dir.mkdir(parents=True, exist_ok=True)
    previous: dict[str, int] = {}
    producer_log = root / "runs/production/runtime/logs/fulltext_producer.log"
    producer_offset = producer_log.stat().st_size if producer_log.exists() else 0
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
                    task_counts = store.task_summary(config["config_snapshot_id"])
            except Exception as exc:
                task_counts = {}
                alerts.append({"type": "production_database_integrity", "error": f"{type(exc).__name__}:{exc}", "component": "all"})
            producer_error, producer_repeats, producer_offset = _new_repeated_log_error(producer_log, producer_offset)
            failed_growth = task_counts.get("failed_final", 0) - previous.get("failed_final", task_counts.get("failed_final", 0))
            validation_growth = task_counts.get("validation_failed", 0) - previous.get("validation_failed", task_counts.get("validation_failed", 0))
            if failed_growth >= 2 or validation_growth >= 2:
                alerts.append({"type": "extraction_queue_failure_growth", "failed_growth": failed_growth, "validation_growth": validation_growth, "component": "pipeline_monitor"})
            if producer_repeats >= 3:
                alerts.append({"type": "producer_repeated_error", "repeated_error": producer_error, "count": producer_repeats, "component": "fulltext_producer"})
            previous = dict(task_counts)
            for alert in alerts:
                component = alert["component"]
                if component == "all":
                    _request_component_stop(root, "fulltext_producer", alert["type"])
                else:
                    _request_component_stop(root, component, alert["type"])
            report = {
                "checked_at": checked_at, "status": "alert" if alerts else "healthy",
                "task_counts": task_counts, "alerts": alerts,
                "producer_repeated_error_count": producer_repeats,
            }
            atomic_write_json(report_dir / "latest.json", report)
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
