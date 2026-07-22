from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.parse_fulltext.extractor import PARSER_VERSION
from scripts.io_utils import atomic_write_json, utc_now
from scripts.production.staging import export_staging_package
from scripts.production.store import ProductionStore
from scripts.production.workers import (
    fulltext_worker,
    monitor_worker,
    pid_alive,
    reconcile_candidate_queue,
    register_curated_source_exclusions,
)
from scripts.validation.validate_tables import validate_dictionary


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = ROOT / "runs/production/runtime"
ACTIVE_CONFIG = RUNTIME_DIR / "active_config.json"
FREEZE_MANIFEST = RUNTIME_DIR / "production_freeze_manifest.json"
SMOKE_REPORT = RUNTIME_DIR / "smoke_test_report.json"
PRODUCTION_DB = Path("cache/databases/extraction_control.sqlite3")
FULLTEXT_DB = Path("data/raw/literature/metadata/fulltext_registry/fulltext.sqlite3")
CANDIDATE_DB = Path("cache/databases/extraction_candidates.sqlite3")
METADATA_DB = Path("data/raw/literature/metadata/snapshots/screening_rules_v1.2/literature.sqlite3")
SNAPSHOT_DIR = Path("data/raw/literature/metadata/snapshots/screening_rules_v1.2")
COMPONENTS = ("fulltext_producer", "pipeline_monitor")


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
        ROOT / "config/review_policy.json",
    ]
    seed_root = ROOT / "data/benchmark/fixtures/six_papers"
    for directory in sorted(seed_root.glob("P*")):
        if (directory / "source_master.csv").exists():
            paths.extend(sorted(path for path in directory.iterdir() if path.is_file()))
    return list(dict.fromkeys(path.resolve() for path in paths if path.exists()))


def build_freeze_manifest() -> dict[str, Any]:
    snapshot = json.loads(
        (ROOT / SNAPSHOT_DIR / "snapshot_manifest.json").read_text(
            encoding="utf-8-sig"
        )
    )
    files = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in tracked_asset_paths()
    ]
    return {
        "freeze_version": "production_v2_no_local_model",
        "created_at": utc_now(),
        "metadata_snapshot": "screening_rules_v1.2",
        "canonical_work_count": snapshot.get("canonical_work_count"),
        "tier_counts": {
            row["tier"]: row["count"] for row in snapshot.get("tier_counts", [])
        },
        "files": files,
        "write_policy": "production workers may not write any listed path",
    }


def verify_freeze(manifest: dict[str, Any] | None = None) -> None:
    manifest = manifest or json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))
    failures: list[str] = []
    for item in manifest["files"]:
        path = ROOT / item["path"]
        if (
            not path.exists()
            or path.stat().st_size != item["bytes"]
            or sha256_file(path) != item["sha256"]
        ):
            failures.append(item["path"])
    if failures:
        raise RuntimeError("frozen_asset_mismatch:" + ";".join(failures))


def build_config() -> dict[str, Any]:
    versioned_files = {
        "formal_schema": ROOT / "config/schema.json",
        "field_dictionary": ROOT / "config/field_dictionary.csv",
        "extraction_schema": ROOT / "config/extraction_result_v0.2.schema.json",
        "run_plan_schema": ROOT / "config/run_plan_v1.schema.json",
        "unit_rules": ROOT / "config/extraction_unit_rules_v1.json",
        "review_policy": ROOT / "config/review_policy.json",
    }
    versions = {
        name: {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(path),
        }
        for name, path in versioned_files.items()
    }
    manifest = {
        "versions": versions,
        "parser_version": PARSER_VERSION,
        "extraction_mode": "reviewer_evidence_grounded",
        "local_model_runtime": False,
    }
    snapshot_id = (
        "CFG_"
        + hashlib.sha256(
            json.dumps(manifest, sort_keys=True).encode("utf-8")
        ).hexdigest()[:20].upper()
    )
    return {
        "config_snapshot_id": snapshot_id,
        "metadata_db": METADATA_DB.as_posix(),
        "fulltext_db": FULLTEXT_DB.as_posix(),
        "candidate_db": CANDIDATE_DB.as_posix(),
        "production_db": PRODUCTION_DB.as_posix(),
        "staging_root": "cache/staging/eight_tables",
        "review_root": "data/interim/review_queue/extraction",
        "extractor": "reviewer",
        "config_manifest": manifest,
    }


def doctor() -> dict[str, Any]:
    """Check public repository assets without requiring private/local data."""
    errors: list[str] = []
    config_files = sorted((ROOT / "config").glob("*.json"))
    parsed_configs: dict[str, Any] = {}
    schema_count = 0

    for path in config_files:
        try:
            parsed = json.loads(path.read_text(encoding="utf-8-sig"))
            parsed_configs[path.name] = parsed
            if path.name.endswith(".schema.json"):
                Draft202012Validator.check_schema(parsed)
                schema_count += 1
        except (OSError, ValueError, TypeError, SchemaError) as exc:
            errors.append(f"{path.relative_to(ROOT).as_posix()}: {exc}")

    formal_schema = parsed_configs.get("schema.json")
    dictionary_path = ROOT / "config/field_dictionary.csv"
    if not isinstance(formal_schema, dict):
        errors.append("config/schema.json: missing or invalid")
    elif not dictionary_path.is_file():
        errors.append("config/field_dictionary.csv: missing")
    else:
        validate_dictionary(formal_schema, dictionary_path, errors)

    temporary_database = "not_checked"
    if isinstance(formal_schema, dict):
        try:
            with TemporaryDirectory(prefix="cnt_patsight_doctor_") as directory:
                database = Path(directory) / "production.sqlite3"
                with ProductionStore(database, ROOT / "config/schema.json") as store:
                    store.integrity_check()
            temporary_database = "ok"
        except (OSError, ValueError, sqlite3.Error) as exc:
            temporary_database = "failed"
            errors.append(f"temporary_database: {exc}")

    return {
        "checked_at": utc_now(),
        "valid": not errors,
        "config_files": len(config_files),
        "json_schemas": schema_count,
        "temporary_database": temporary_database,
        "errors": errors,
    }


def prepare() -> dict[str, Any]:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    freeze = build_freeze_manifest()
    atomic_write_json(FREEZE_MANIFEST, freeze)
    config = build_config()
    with ProductionStore(ROOT / PRODUCTION_DB, ROOT / "config/schema.json") as store:
        store.register_config(config["config_snapshot_id"], config["config_manifest"])
        exclusions = register_curated_source_exclusions(ROOT, store)
        store.integrity_check()
    atomic_write_json(ACTIVE_CONFIG, config)
    enqueued = reconcile_candidate_queue(ROOT, config)
    report = {
        "prepared_at": utc_now(),
        "config_snapshot_id": config["config_snapshot_id"],
        "local_model_runtime": False,
        "curated_exclusions_added": exclusions,
        "candidate_tasks_enqueued": enqueued,
    }
    atomic_write_json(RUNTIME_DIR / "prepare_report.json", report)
    return report


def load_config() -> dict[str, Any]:
    if not ACTIVE_CONFIG.exists():
        raise FileNotFoundError("run prepare first")
    return json.loads(ACTIVE_CONFIG.read_text(encoding="utf-8"))


def smoke_test() -> dict[str, Any]:
    config = load_config()
    verify_freeze()
    required = [
        ROOT / config["metadata_db"],
        ROOT / config["fulltext_db"],
        ROOT / config["candidate_db"],
        ROOT / "config/schema.json",
        ROOT / "config/field_dictionary.csv",
    ]
    missing = [path.relative_to(ROOT).as_posix() for path in required if not path.exists()]
    with ProductionStore(
        ROOT / config["production_db"], ROOT / "config/schema.json"
    ) as store:
        store.integrity_check()
        task_counts = store.task_summary(config["config_snapshot_id"])
    report = {
        "checked_at": utc_now(),
        "valid": not missing,
        "missing": missing,
        "task_counts": task_counts,
        "local_model_runtime": False,
    }
    atomic_write_json(SMOKE_REPORT, report)
    if missing:
        raise FileNotFoundError(";".join(missing))
    return report


def component_info(component: str) -> dict[str, Any]:
    pid_path = RUNTIME_DIR / "pids" / f"{component}.pid"
    heartbeat = RUNTIME_DIR / "heartbeats" / f"{component}.json"
    pid = int(pid_path.read_text(encoding="ascii")) if pid_path.exists() else 0
    detail = (
        json.loads(heartbeat.read_text(encoding="utf-8"))
        if heartbeat.exists()
        else {}
    )
    return {"component": component, "pid": pid, "alive": pid_alive(pid), **detail}


def status() -> dict[str, Any]:
    config = load_config()
    with ProductionStore(
        ROOT / config["production_db"], ROOT / "config/schema.json"
    ) as store:
        tasks = store.task_summary(config["config_snapshot_id"])
        dispositions = store.disposition_summary(config["config_snapshot_id"])
        staged_sources = store.staged_source_count()
    return {
        "checked_at": utc_now(),
        "components": [component_info(component) for component in COMPONENTS],
        "tasks": tasks,
        "dispositions": dispositions,
        "staged_sources": staged_sources,
        "extractor": config["extractor"],
        "local_model_runtime": False,
    }


def _creation_flags() -> int:
    return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def start_components() -> dict[str, Any]:
    load_config()
    started: list[dict[str, Any]] = []
    for component in COMPONENTS:
        info = component_info(component)
        if info["alive"]:
            continue
        stdout_path = RUNTIME_DIR / "logs" / f"{component}.stdout.log"
        stderr_path = RUNTIME_DIR / "logs" / f"{component}.stderr.log"
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        with stdout_path.open("a", encoding="utf-8") as stdout_handle, stderr_path.open(
            "a", encoding="utf-8"
        ) as stderr_handle:
            process = subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "worker", component],
                cwd=ROOT,
                stdout=stdout_handle,
                stderr=stderr_handle,
                creationflags=_creation_flags(),
            )
        started.append({"component": component, "pid": process.pid})
    return {"started_at": utc_now(), "started": started}


def request_stop(all_components: bool = True) -> dict[str, Any]:
    components = COMPONENTS if all_components else ("fulltext_producer",)
    requested = []
    for component in components:
        path = RUNTIME_DIR / "stop" / f"{component}.stop"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{utc_now()} user_requested", encoding="utf-8")
        requested.append(component)
    return {"requested_at": utc_now(), "components": requested}


def export_review_packages(source_id: str | None = None) -> dict[str, Any]:
    config = load_config()
    formal_schema = json.loads(
        (ROOT / "config/schema.json").read_text(encoding="utf-8")
    )
    exported: dict[str, list[str]] = {}
    with ProductionStore(
        ROOT / config["production_db"], ROOT / "config/schema.json"
    ) as store:
        if source_id:
            source_ids = [source_id]
        else:
            source_ids = [
                row[0]
                for row in store.connection.execute(
                    "SELECT source_id FROM staging_state ORDER BY source_id"
                )
            ]
        for current in source_ids:
            rows = store.read_staging_rows(current)
            if not any(rows.values()):
                continue
            revision = store.connection.execute(
                "SELECT revision_id FROM staging_state WHERE source_id=?",
                (current,),
            ).fetchone()
            if not revision:
                continue
            output = ROOT / config["staging_root"] / "review_packages" / current / revision[0]
            paths = export_staging_package(
                rows,
                formal_schema,
                output,
                ROOT / "config/schema.json",
                ROOT / "config/field_dictionary.csv",
            )
            exported[current] = [path.relative_to(ROOT).as_posix() for path in paths]
    return {"exported_at": utc_now(), "packages": exported}


def worker(component: str) -> None:
    config = load_config()
    if component == "fulltext_producer":
        fulltext_worker(ROOT, config)
    elif component == "pipeline_monitor":
        monitor_worker(ROOT, config)
    else:
        raise ValueError(component)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CNT-PatSight metadata/full-text production controller"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("doctor", "prepare", "smoke-test", "start", "status", "resume"):
        sub.add_parser(name)
    stop = sub.add_parser("stop")
    stop.add_argument("--all", action="store_true")
    export = sub.add_parser("export-review")
    export.add_argument("--source-id")
    worker_parser = sub.add_parser("worker")
    worker_parser.add_argument("component", choices=COMPONENTS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        result = doctor()
    elif args.command == "prepare":
        result = prepare()
    elif args.command == "smoke-test":
        result = smoke_test()
    elif args.command in {"start", "resume"}:
        result = start_components()
    elif args.command == "status":
        result = status()
    elif args.command == "stop":
        result = request_stop(args.all)
    elif args.command == "export-review":
        result = export_review_packages(args.source_id)
    else:
        worker(args.component)
        return 0
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("valid", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
