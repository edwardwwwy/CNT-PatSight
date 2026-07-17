from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from scripts.io_utils import utc_now


TASK_STATUSES = {
    "pending", "running", "succeeded", "validation_failed",
    "failed_retryable", "failed_final", "interrupted",
}
DISPOSITIONS = {
    "candidate_extract", "needs_review", "reextract_required", "rejected_extract",
}


def _q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


class ProductionStore:
    """Queue control and isolated eight-table staging storage."""

    def __init__(self, path: Path, formal_schema_path: Path):
        self.path = path
        self.schema = json.loads(formal_schema_path.read_text(encoding="utf-8"))
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, timeout=30)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA journal_mode=WAL")
        self._create_schema()

    def __enter__(self) -> "ProductionStore":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS config_snapshots (
                config_snapshot_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                manifest_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS extraction_tasks (
                task_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                input_content_hash TEXT NOT NULL,
                config_snapshot_id TEXT NOT NULL REFERENCES config_snapshots(config_snapshot_id),
                task_status TEXT NOT NULL CHECK(task_status IN (
                    'pending','running','succeeded','validation_failed',
                    'failed_retryable','failed_final','interrupted'
                )),
                extraction_disposition TEXT NOT NULL CHECK(extraction_disposition IN (
                    'candidate_extract','needs_review','reextract_required','rejected_extract'
                )),
                priority INTEGER NOT NULL DEFAULT 0,
                attempt_count INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                lease_owner TEXT NOT NULL DEFAULT '',
                claimed_at TEXT NOT NULL DEFAULT '',
                heartbeat_at TEXT NOT NULL DEFAULT '',
                request_hash TEXT NOT NULL DEFAULT '',
                raw_result_path TEXT NOT NULL DEFAULT '',
                last_error TEXT NOT NULL DEFAULT '',
                worker_status TEXT NOT NULL DEFAULT 'pending',
                validation_status TEXT NOT NULL DEFAULT 'not_run',
                staging_status TEXT NOT NULL DEFAULT 'not_staged',
                superseded_by TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(source_id,input_content_hash,config_snapshot_id)
            );
            CREATE INDEX IF NOT EXISTS idx_extraction_claim
                ON extraction_tasks(task_status,priority,created_at);
            CREATE TABLE IF NOT EXISTS source_exclusions (
                source_id TEXT PRIMARY KEY,
                reason TEXT NOT NULL,
                evidence_path TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS task_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL REFERENCES extraction_tasks(task_id),
                event_type TEXT NOT NULL,
                detail_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS staging_state (
                source_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL REFERENCES extraction_tasks(task_id),
                revision_id TEXT NOT NULL,
                input_content_hash TEXT NOT NULL,
                config_snapshot_id TEXT NOT NULL,
                extraction_disposition TEXT NOT NULL,
                silver_reference INTEGER NOT NULL DEFAULT 0,
                domain_expert_verified INTEGER NOT NULL DEFAULT 0,
                validator_report_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS staging_withdrawals (
                withdrawal_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                task_id TEXT NOT NULL REFERENCES extraction_tasks(task_id),
                reason TEXT NOT NULL,
                snapshot_path TEXT NOT NULL,
                deleted_rows_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self._ensure_column("extraction_tasks", "worker_status", "TEXT NOT NULL DEFAULT 'pending'")
        self._ensure_column("extraction_tasks", "validation_status", "TEXT NOT NULL DEFAULT 'not_run'")
        self._ensure_column("extraction_tasks", "staging_status", "TEXT NOT NULL DEFAULT 'not_staged'")
        self._ensure_column("extraction_tasks", "superseded_by", "TEXT NOT NULL DEFAULT ''")
        tables = self.schema["tables"]
        for table_name, definition in tables.items():
            columns = definition["columns"]
            identity = definition["row_identity"]
            parts = [f"{_q(column)} TEXT NOT NULL DEFAULT ''" for column in columns]
            parts.append("PRIMARY KEY (" + ",".join(_q(c) for c in identity) + ")")
            for fk in definition.get("foreign_keys", []):
                ref_table, ref_column = fk["references"].split(".")
                parts.append(
                    f"FOREIGN KEY ({_q(fk['column'])}) REFERENCES {_q(ref_table)}({_q(ref_column)})"
                )
            sql = f"CREATE TABLE IF NOT EXISTS {_q(table_name)} ({','.join(parts)})"
            self.connection.execute(sql)
        self.connection.commit()

    def _ensure_column(self, table: str, column: str, declaration: str) -> None:
        columns = {str(row[1]) for row in self.connection.execute(f"PRAGMA table_info({_q(table)})")}
        if column not in columns:
            self.connection.execute(
                f"ALTER TABLE {_q(table)} ADD COLUMN {_q(column)} {declaration}"
            )

    def integrity_check(self) -> None:
        result = self.connection.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise sqlite3.DatabaseError(f"integrity_check_failed:{result}")
        fk = self.connection.execute("PRAGMA foreign_key_check").fetchall()
        if fk:
            raise sqlite3.IntegrityError(f"foreign_key_check_failed:{len(fk)}")

    def register_config(self, snapshot_id: str, manifest: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO config_snapshots VALUES (?,?,?)",
            (snapshot_id, utc_now(), json.dumps(manifest, ensure_ascii=False, sort_keys=True)),
        )
        self.connection.commit()

    def enqueue(
        self,
        task_id: str,
        source_id: str,
        input_hash: str,
        config_snapshot_id: str,
        priority: int,
        disposition: str = "candidate_extract",
    ) -> bool:
        if disposition not in DISPOSITIONS:
            raise ValueError(disposition)
        if self.is_source_excluded(source_id):
            return False
        now = utc_now()
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO extraction_tasks(
                task_id,source_id,input_content_hash,config_snapshot_id,task_status,
                extraction_disposition,priority,created_at,updated_at
            ) VALUES (?,?,?,?,'pending',?,?,?,?)
            """,
            (task_id, source_id, input_hash, config_snapshot_id, disposition, priority, now, now),
        )
        self.connection.commit()
        return cursor.rowcount == 1

    def claim(self, worker_id: str, config_snapshot_id: str | None = None) -> dict[str, Any] | None:
        now = utc_now()
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            sql = """
                SELECT q.* FROM extraction_tasks q
                WHERE task_status IN ('pending','failed_retryable','interrupted')
                  AND attempt_count < max_attempts
                  AND NOT EXISTS (
                      SELECT 1 FROM source_exclusions e
                      WHERE e.source_id=q.source_id
                  )
            """
            params: tuple[Any, ...] = ()
            if config_snapshot_id is not None:
                sql += " AND config_snapshot_id=?"
                params = (config_snapshot_id,)
            sql += " ORDER BY priority,created_at,task_id LIMIT 1"
            row = self.connection.execute(sql, params).fetchone()
            if row is None:
                self.connection.commit()
                return None
            updated = self.connection.execute(
                """
                UPDATE extraction_tasks SET task_status='running',attempt_count=attempt_count+1,
                    worker_status='running',validation_status='not_run',
                    staging_status='not_staged',superseded_by='',
                    lease_owner=?,claimed_at=?,heartbeat_at=?,updated_at=?
                WHERE task_id=? AND task_status=?
                """,
                (worker_id, now, now, now, row["task_id"], row["task_status"]),
            )
            if updated.rowcount != 1:
                self.connection.rollback()
                return None
            self._event(row["task_id"], "claimed", {"worker_id": worker_id}, commit=False)
            self.connection.commit()
            return dict(self.connection.execute("SELECT * FROM extraction_tasks WHERE task_id=?", (row["task_id"],)).fetchone())
        except Exception:
            self.connection.rollback()
            raise

    def exclude_source(self, source_id: str, reason: str, evidence_path: str = "") -> bool:
        """Persistently prevent an already curated source from re-entering extraction."""
        now = utc_now()
        existed = self.connection.execute(
            "SELECT 1 FROM source_exclusions WHERE source_id=?", (source_id,)
        ).fetchone() is not None
        self.connection.execute(
            """
            INSERT INTO source_exclusions(source_id,reason,evidence_path,created_at,updated_at)
            VALUES (?,?,?,?,?)
            ON CONFLICT(source_id) DO UPDATE SET
                reason=excluded.reason,evidence_path=excluded.evidence_path,
                updated_at=excluded.updated_at
            """,
            (source_id, reason, evidence_path, now, now),
        )
        running = self.connection.execute(
            "SELECT task_id FROM extraction_tasks WHERE source_id=? AND task_status='running'",
            (source_id,),
        ).fetchall()
        self.connection.execute(
            """
            UPDATE extraction_tasks SET task_status='interrupted',lease_owner='',
                heartbeat_at='',last_error=?,updated_at=?
            WHERE source_id=? AND task_status='running'
            """,
            (f"excluded_source:{reason}", now, source_id),
        )
        for row in running:
            self._event(
                str(row["task_id"]), "source_excluded",
                {"reason": reason, "evidence_path": evidence_path}, commit=False,
            )
        self.connection.commit()
        return not existed

    def is_source_excluded(self, source_id: str) -> bool:
        return self.connection.execute(
            "SELECT 1 FROM source_exclusions WHERE source_id=?", (source_id,)
        ).fetchone() is not None

    def exclusion_summary(self) -> dict[str, int]:
        return {
            str(row["reason"]): int(row["n"])
            for row in self.connection.execute(
                "SELECT reason,COUNT(*) n FROM source_exclusions GROUP BY reason"
            )
        }

    def heartbeat_task(self, task_id: str, worker_id: str) -> None:
        now = utc_now()
        self.connection.execute(
            "UPDATE extraction_tasks SET heartbeat_at=?,updated_at=? WHERE task_id=? AND lease_owner=? AND task_status='running'",
            (now, now, task_id, worker_id),
        )
        self.connection.commit()

    def finish_task(
        self,
        task_id: str,
        status: str,
        disposition: str,
        *,
        request_hash: str = "",
        raw_result_path: str = "",
        error: str = "",
    ) -> None:
        if status not in TASK_STATUSES or disposition not in DISPOSITIONS:
            raise ValueError(f"invalid task state {status}/{disposition}")
        now = utc_now()
        worker_status = "completed" if status in {"succeeded", "validation_failed"} else "failed"
        validation_status = (
            "passed" if status == "succeeded"
            else "failed_semantic_validation" if status == "validation_failed"
            else "not_completed"
        )
        staging_status = "staged" if status == "succeeded" else "not_staged"
        self.connection.execute(
            """
            UPDATE extraction_tasks SET task_status=?,extraction_disposition=?,request_hash=?,
                raw_result_path=?,last_error=?,worker_status=?,validation_status=?,
                staging_status=?,superseded_by='',lease_owner='',heartbeat_at=?,updated_at=?
            WHERE task_id=?
            """,
            (
                status, disposition, request_hash, raw_result_path, error,
                worker_status, validation_status, staging_status,
                now, now, task_id,
            ),
        )
        self._event(task_id, status, {"disposition": disposition, "error": error}, commit=False)
        self.connection.commit()

    def recover_stale(self, stale_before: str) -> int:
        rows = self.connection.execute(
            "SELECT task_id FROM extraction_tasks WHERE task_status='running' AND heartbeat_at < ?",
            (stale_before,),
        ).fetchall()
        now = utc_now()
        for row in rows:
            self.connection.execute(
                """UPDATE extraction_tasks SET task_status='interrupted',lease_owner='',
                   last_error='stale_running_recovered',updated_at=? WHERE task_id=?""",
                (now, row["task_id"]),
            )
            self._event(row["task_id"], "interrupted", {"reason": "stale_running_recovered"}, commit=False)
        self.connection.commit()
        return len(rows)

    def write_staging(
        self,
        task: dict[str, Any],
        revision_id: str,
        rows_by_table: dict[str, list[dict[str, Any]]],
        validator_report: dict[str, Any],
        fail_after_table: str | None = None,
    ) -> None:
        source_id = task["source_id"]
        tables = self.schema["tables"]
        delete_order = [
            "review_issue_log", "evidence_index", "cost_scale_review", "yield_quality",
            "reactor_process_gas", "catalyst_system", "source_run", "source_master",
        ]
        insert_order = list(tables)
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            run_ids = [r[0] for r in self.connection.execute(
                "SELECT run_id FROM source_run WHERE source_id=?", (source_id,)
            ).fetchall()]
            for table in delete_order:
                if table == "source_master":
                    self.connection.execute("DELETE FROM source_master WHERE source_id=?", (source_id,))
                elif table == "source_run":
                    self.connection.execute("DELETE FROM source_run WHERE source_id=?", (source_id,))
                elif table in {"evidence_index", "review_issue_log"}:
                    self.connection.execute(f"DELETE FROM {_q(table)} WHERE source_id=?", (source_id,))
                elif run_ids:
                    placeholders = ",".join("?" for _ in run_ids)
                    self.connection.execute(f"DELETE FROM {_q(table)} WHERE run_id IN ({placeholders})", run_ids)
            for table in insert_order:
                columns = tables[table]["columns"]
                for row in rows_by_table.get(table, []):
                    values = [self._cell(row.get(column, "")) for column in columns]
                    self.connection.execute(
                        f"INSERT INTO {_q(table)} ({','.join(_q(c) for c in columns)}) VALUES ({','.join('?' for _ in columns)})",
                        values,
                    )
                if fail_after_table == table:
                    raise RuntimeError(f"injected_failure_after_{table}")
            self.connection.execute(
                """
                INSERT INTO staging_state VALUES (?,?,?,?,?,'needs_review',0,0,?,?)
                ON CONFLICT(source_id) DO UPDATE SET
                    task_id=excluded.task_id,revision_id=excluded.revision_id,
                    input_content_hash=excluded.input_content_hash,
                    config_snapshot_id=excluded.config_snapshot_id,
                    extraction_disposition='needs_review',silver_reference=0,
                    domain_expert_verified=0,validator_report_json=excluded.validator_report_json,
                    updated_at=excluded.updated_at
                """,
                (
                    source_id, task["task_id"], revision_id, task["input_content_hash"],
                    task["config_snapshot_id"], json.dumps(validator_report, ensure_ascii=False), utc_now(),
                ),
            )
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def read_staging_rows(self, source_id: str) -> dict[str, list[dict[str, Any]]]:
        rows: dict[str, list[dict[str, Any]]] = {name: [] for name in self.schema["tables"]}
        rows["source_master"] = [
            dict(row) for row in self.connection.execute(
                "SELECT * FROM source_master WHERE source_id=?", (source_id,)
            )
        ]
        rows["source_run"] = [
            dict(row) for row in self.connection.execute(
                "SELECT * FROM source_run WHERE source_id=? ORDER BY run_id", (source_id,)
            )
        ]
        run_ids = [row["run_id"] for row in rows["source_run"]]
        for table in ("catalyst_system", "reactor_process_gas", "yield_quality", "cost_scale_review"):
            if not run_ids:
                continue
            placeholders = ",".join("?" for _ in run_ids)
            identity = self.schema["tables"][table]["row_identity"]
            order = ",".join(_q(column) for column in identity)
            rows[table] = [
                dict(row) for row in self.connection.execute(
                    f"SELECT * FROM {_q(table)} WHERE run_id IN ({placeholders}) ORDER BY {order}",
                    run_ids,
                )
            ]
        for table in ("evidence_index", "review_issue_log"):
            identity = self.schema["tables"][table]["row_identity"]
            order = ",".join(_q(column) for column in identity)
            rows[table] = [
                dict(row) for row in self.connection.execute(
                    f"SELECT * FROM {_q(table)} WHERE source_id=? ORDER BY {order}",
                    (source_id,),
                )
            ]
        return rows

    def withdraw_staging(self, source_id: str, reason: str) -> dict[str, int]:
        """Remove a derived staging mirror when a curated package already exists.

        Immutable raw attempts and task history are intentionally retained.
        """
        counts: dict[str, int] = {}
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            task_rows = self.connection.execute(
                "SELECT task_id FROM extraction_tasks WHERE source_id=? ORDER BY created_at,task_id",
                (source_id,),
            ).fetchall()
            staging_snapshot = self.read_staging_rows(source_id)
            snapshot_path = self._write_withdrawal_snapshot(source_id, reason, staging_snapshot)
            run_ids = [
                str(row[0]) for row in self.connection.execute(
                    "SELECT run_id FROM source_run WHERE source_id=?", (source_id,)
                )
            ]
            for table in ("review_issue_log", "evidence_index"):
                cursor = self.connection.execute(
                    f"DELETE FROM {_q(table)} WHERE source_id=?", (source_id,)
                )
                counts[table] = cursor.rowcount
            for table in ("cost_scale_review", "yield_quality", "reactor_process_gas", "catalyst_system"):
                if run_ids:
                    placeholders = ",".join("?" for _ in run_ids)
                    cursor = self.connection.execute(
                        f"DELETE FROM {_q(table)} WHERE run_id IN ({placeholders})", run_ids,
                    )
                    counts[table] = cursor.rowcount
                else:
                    counts[table] = 0
            counts["source_run"] = self.connection.execute(
                "DELETE FROM source_run WHERE source_id=?", (source_id,)
            ).rowcount
            counts["source_master"] = self.connection.execute(
                "DELETE FROM source_master WHERE source_id=?", (source_id,)
            ).rowcount
            counts["staging_state"] = self.connection.execute(
                "DELETE FROM staging_state WHERE source_id=?", (source_id,)
            ).rowcount
            for row in task_rows:
                self.connection.execute(
                    """
                    UPDATE extraction_tasks SET staging_status='withdrawn',superseded_by=?,updated_at=?
                    WHERE task_id=?
                    """,
                    (reason, utc_now(), row["task_id"]),
                )
                withdrawal_id = "WD_" + uuid.uuid4().hex[:20].upper()
                self.connection.execute(
                    """
                    INSERT INTO staging_withdrawals(
                        withdrawal_id,source_id,task_id,reason,snapshot_path,
                        deleted_rows_json,created_at
                    ) VALUES (?,?,?,?,?,?,?)
                    """,
                    (
                        withdrawal_id, source_id, str(row["task_id"]), reason,
                        snapshot_path, json.dumps(counts, ensure_ascii=False, sort_keys=True),
                        utc_now(),
                    ),
                )
                self._event(
                    str(row["task_id"]), "staging_withdrawn",
                    {
                        "reason": reason, "deleted_rows": counts,
                        "snapshot_path": snapshot_path,
                    },
                    commit=False,
                )
            self.connection.commit()
            return counts
        except Exception:
            self.connection.rollback()
            raise

    def mark_semantic_failure(
        self,
        task_id: str,
        *,
        superseded_by: str,
        error_codes: list[str],
        raw_result_path: str = "",
    ) -> None:
        """Record completed inference whose data failed semantic validation."""
        now = utc_now()
        error = json.dumps(
            {"error_codes": error_codes, "superseded_by": superseded_by},
            ensure_ascii=False,
            sort_keys=True,
        )
        self.connection.execute(
            """
            UPDATE extraction_tasks SET
                task_status='validation_failed',
                extraction_disposition='reextract_required',
                worker_status='completed',
                validation_status='failed_semantic_validation',
                staging_status='withdrawn',
                superseded_by=?,
                raw_result_path=CASE WHEN ?!='' THEN ? ELSE raw_result_path END,
                last_error=?,
                lease_owner='',
                heartbeat_at=?,
                updated_at=?
            WHERE task_id=?
            """,
            (
                superseded_by, raw_result_path, raw_result_path,
                error, now, now, task_id,
            ),
        )
        self._event(
            task_id,
            "failed_semantic_validation",
            {
                "error_codes": error_codes,
                "superseded_by": superseded_by,
                "worker_status": "completed",
                "staging_status": "withdrawn",
            },
            commit=False,
        )
        self.connection.commit()

    def record_withdrawal_snapshot(
        self,
        source_id: str,
        task_id: str,
        reason: str,
        rows: dict[str, list[dict[str, Any]]],
        deleted_rows: dict[str, int],
    ) -> str:
        """Persist a retroactive or pre-delete immutable staging snapshot."""
        snapshot_path = self._write_withdrawal_snapshot(source_id, reason, rows)
        self.connection.execute(
            """
            INSERT INTO staging_withdrawals(
                withdrawal_id,source_id,task_id,reason,snapshot_path,
                deleted_rows_json,created_at
            ) VALUES (?,?,?,?,?,?,?)
            """,
            (
                "WD_" + uuid.uuid4().hex[:20].upper(),
                source_id, task_id, reason, snapshot_path,
                json.dumps(deleted_rows, ensure_ascii=False, sort_keys=True),
                utc_now(),
            ),
        )
        self._event(
            task_id,
            "withdrawal_snapshot_recorded",
            {
                "reason": reason,
                "snapshot_path": snapshot_path,
                "deleted_rows": deleted_rows,
            },
            commit=False,
        )
        self.connection.commit()
        return snapshot_path

    def _write_withdrawal_snapshot(
        self,
        source_id: str,
        reason: str,
        rows: dict[str, list[dict[str, Any]]],
    ) -> str:
        directory = self.path.parent / "withdrawn_staging" / source_id
        directory.mkdir(parents=True, exist_ok=True)
        stamp = utc_now().replace(":", "").replace("-", "")
        path = directory / f"{stamp}_{uuid.uuid4().hex[:8]}.json"
        payload = {
            "source_id": source_id,
            "reason": reason,
            "withdrawn_at": utc_now(),
            "rows": rows,
        }
        temporary = path.with_suffix(path.suffix + ".part")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path.as_posix()

    def record_task_event(self, task_id: str, event_type: str, detail: dict[str, Any]) -> None:
        self._event(task_id, event_type, detail, commit=True)

    @staticmethod
    def _cell(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        if isinstance(value, bool):
            return "1" if value else "0"
        return str(value)

    def _event(self, task_id: str, event_type: str, detail: dict[str, Any], *, commit: bool) -> None:
        self.connection.execute(
            "INSERT INTO task_events(task_id,event_type,detail_json,created_at) VALUES (?,?,?,?)",
            (task_id, event_type, json.dumps(detail, ensure_ascii=False), utc_now()),
        )
        if commit:
            self.connection.commit()

    def task_summary(self, config_snapshot_id: str | None = None) -> dict[str, int]:
        sql = """SELECT task_status,COUNT(*) n FROM extraction_tasks q
                 WHERE NOT EXISTS (
                     SELECT 1 FROM source_exclusions e WHERE e.source_id=q.source_id
                 )"""
        params: tuple[Any, ...] = ()
        if config_snapshot_id is not None:
            sql += " AND config_snapshot_id=?"
            params = (config_snapshot_id,)
        sql += " GROUP BY task_status"
        return {
            str(row["task_status"]): int(row["n"])
            for row in self.connection.execute(sql, params)
        }

    def disposition_summary(self, config_snapshot_id: str | None = None) -> dict[str, int]:
        sql = """SELECT extraction_disposition,COUNT(*) n FROM extraction_tasks q
                 WHERE NOT EXISTS (
                     SELECT 1 FROM source_exclusions e WHERE e.source_id=q.source_id
                 )"""
        params: tuple[Any, ...] = ()
        if config_snapshot_id is not None:
            sql += " AND config_snapshot_id=?"
            params = (config_snapshot_id,)
        sql += " GROUP BY extraction_disposition"
        return {
            str(row["extraction_disposition"]): int(row["n"])
            for row in self.connection.execute(sql, params)
        }

    def staged_source_count(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM staging_state").fetchone()[0])

