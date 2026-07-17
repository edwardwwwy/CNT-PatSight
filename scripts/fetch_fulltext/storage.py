from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from scripts.io_utils import replace_with_retry, unique_part_path

from .models import ArtifactRecord, MetadataRecord


FULLTEXT_COLUMNS = [
    "fulltext_id", "source_id", "doi", "title", "fulltext_type", "fulltext_url",
    "local_path", "fetch_status", "failure_reason", "content_hash", "content_bytes",
    "media_type", "http_status", "url_source", "content_scope", "validation_note",
    "is_primary", "acquisition_step", "version_type", "version_relation",
    "related_source_id", "created_at", "updated_at", "last_checked_at",
]

COVERAGE_COLUMNS = [
    "source_id", "doi", "title", "availability_status", "primary_fulltext_type",
    "primary_local_path", "successful_artifact_count", "failed_attempt_count",
    "failure_reasons", "last_checked_at", "fulltext_status", "acquisition_status",
    "failure_reason", "publisher_url", "manual_access_url",
]

QUEUE_COLUMNS = [
    "queue_id", "source_id", "work_id", "title", "doi", "priority_tier",
    "production_lane", "queue_priority", "priority_reason", "topic_relevance_score",
    "evidence_likelihood_score", "citation_count", "preferred_format",
    "candidate_url", "url_source", "access_type", "license", "download_status",
    "http_status", "content_type", "resolved_url", "attempt_count", "max_attempts",
    "last_attempt_at", "local_path", "file_size", "sha256", "failure_reason",
    "rule_version", "created_at", "updated_at", "metadata_enrichment_status",
    "fulltext_status", "acquisition_status", "publisher_url", "manual_access_url",
]

QUEUE_STATUSES = {
    "queued", "downloading", "downloaded", "validated", "not_pdf", "blocked",
    "paywalled", "not_found", "failed_retryable", "failed_final", "local_existing",
}


def _queue_table_sql(*, if_not_exists: bool = False) -> str:
    clause = "IF NOT EXISTS " if if_not_exists else ""
    return f"""
        CREATE TABLE {clause}fulltext_acquisition_queue (
            queue_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL UNIQUE,
            work_id TEXT NOT NULL,
            title TEXT NOT NULL,
            doi TEXT NOT NULL DEFAULT '',
            priority_tier TEXT NOT NULL CHECK(priority_tier IN ('A','B','C','M')),
            production_lane TEXT NOT NULL CHECK(production_lane IN ('A','B','C','D')),
            queue_priority INTEGER NOT NULL,
            priority_reason TEXT NOT NULL DEFAULT '',
            topic_relevance_score REAL NOT NULL DEFAULT 0,
            evidence_likelihood_score REAL NOT NULL DEFAULT 0,
            citation_count INTEGER NOT NULL DEFAULT 0,
            preferred_format TEXT NOT NULL CHECK(preferred_format IN ('local_pdf','pdf','html','landing_page')),
            candidate_url TEXT NOT NULL DEFAULT '',
            url_source TEXT NOT NULL DEFAULT '',
            access_type TEXT NOT NULL DEFAULT 'unknown',
            license TEXT NOT NULL DEFAULT '',
            download_status TEXT NOT NULL DEFAULT 'queued' CHECK(download_status IN (
                'queued','downloading','downloaded','validated','not_pdf','blocked',
                'paywalled','not_found','failed_retryable','failed_final','local_existing'
            )),
            http_status INTEGER,
            content_type TEXT NOT NULL DEFAULT '',
            resolved_url TEXT NOT NULL DEFAULT '',
            attempt_count INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 3,
            last_attempt_at TEXT NOT NULL DEFAULT '',
            local_path TEXT NOT NULL DEFAULT '',
            file_size INTEGER NOT NULL DEFAULT 0,
            sha256 TEXT NOT NULL DEFAULT '',
            failure_reason TEXT NOT NULL DEFAULT '',
            rule_version TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            batch_id TEXT NOT NULL DEFAULT '',
            lease_owner TEXT NOT NULL DEFAULT '',
            lease_at TEXT NOT NULL DEFAULT '',
            next_attempt_at TEXT NOT NULL DEFAULT '',
            parse_status TEXT NOT NULL DEFAULT '',
            fulltext_relevance_status TEXT NOT NULL DEFAULT '',
            identity_check_status TEXT NOT NULL DEFAULT 'not_checked',
            metadata_enrichment_status TEXT NOT NULL DEFAULT '',
            fulltext_status TEXT NOT NULL DEFAULT 'pending',
            acquisition_status TEXT NOT NULL DEFAULT 'queued',
            publisher_url TEXT NOT NULL DEFAULT '',
            manual_access_url TEXT NOT NULL DEFAULT ''
        )
    """


def artifact_id(source_id: str, fulltext_type: str, location: str) -> str:
    digest = hashlib.sha256(f"{source_id}|{fulltext_type}|{location}".encode("utf-8")).hexdigest()[:20].upper()
    return f"FT_{digest}"


class FulltextStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self._create_schema()

    def __enter__(self) -> "FulltextStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.connection.close()

    def _create_schema(self) -> None:
        self._migrate_queue_schema()
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS fetch_runs (
                run_id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                config_json TEXT NOT NULL,
                summary_json TEXT NOT NULL DEFAULT '{}',
                error_message TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS fulltext_source (
                fulltext_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                doi TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL,
                fulltext_type TEXT NOT NULL CHECK(fulltext_type IN ('pdf','html','local_pdf')),
                fulltext_url TEXT NOT NULL DEFAULT '',
                local_path TEXT NOT NULL DEFAULT '',
                fetch_status TEXT NOT NULL CHECK(fetch_status IN ('success','failed','skipped')),
                failure_reason TEXT NOT NULL DEFAULT '',
                content_hash TEXT NOT NULL DEFAULT '',
                content_bytes INTEGER NOT NULL DEFAULT 0,
                media_type TEXT NOT NULL DEFAULT '',
                http_status INTEGER,
                url_source TEXT NOT NULL DEFAULT '',
                content_scope TEXT NOT NULL DEFAULT 'unknown',
                validation_note TEXT NOT NULL DEFAULT '',
                is_primary INTEGER NOT NULL DEFAULT 0,
                acquisition_step INTEGER NOT NULL DEFAULT 0,
                version_type TEXT NOT NULL DEFAULT 'published',
                version_relation TEXT NOT NULL DEFAULT 'same_record',
                related_source_id TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_checked_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_fulltext_source_source ON fulltext_source(source_id);
            CREATE INDEX IF NOT EXISTS idx_fulltext_source_hash ON fulltext_source(content_hash);
            CREATE INDEX IF NOT EXISTS idx_fulltext_source_status ON fulltext_source(fetch_status, content_scope);

            CREATE TABLE IF NOT EXISTS fetch_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL REFERENCES fetch_runs(run_id),
                source_id TEXT NOT NULL,
                action TEXT NOT NULL,
                url TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            """
        )
        self._ensure_columns(
            "fulltext_source",
            {
                "acquisition_step": "INTEGER NOT NULL DEFAULT 0",
                "version_type": "TEXT NOT NULL DEFAULT 'published'",
                "version_relation": "TEXT NOT NULL DEFAULT 'same_record'",
                "related_source_id": "TEXT NOT NULL DEFAULT ''",
            },
        )
        self.connection.execute(
            """
            UPDATE fulltext_source
            SET version_type='unknown_legacy',version_relation='not_assessed'
            WHERE acquisition_step=0
              AND version_type='published'
              AND version_relation='same_record'
            """
        )
        self.connection.execute(_queue_table_sql(if_not_exists=True))
        self._ensure_columns(
            "fulltext_acquisition_queue",
            {
                "fulltext_status": "TEXT NOT NULL DEFAULT 'pending'",
                "acquisition_status": "TEXT NOT NULL DEFAULT 'queued'",
                "publisher_url": "TEXT NOT NULL DEFAULT ''",
                "manual_access_url": "TEXT NOT NULL DEFAULT ''",
            },
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_fulltext_queue_order "
            "ON fulltext_acquisition_queue(download_status,production_lane,queue_priority)"
        )
        self.connection.commit()

    def _ensure_columns(self, table: str, declarations: dict[str, str]) -> None:
        columns = {str(item[1]) for item in self.connection.execute(f"PRAGMA table_info({table})")}
        for name, declaration in declarations.items():
            if name not in columns:
                self.connection.execute(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {declaration}')

    def _migrate_queue_schema(self) -> None:
        row = self.connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='fulltext_acquisition_queue'"
        ).fetchone()
        if row is None:
            return
        columns = {str(item[1]) for item in self.connection.execute("PRAGMA table_info(fulltext_acquisition_queue)")}
        sql = str(row[0] or "")
        if "production_lane" in columns and "'C'" in sql and "'M'" in sql:
            return
        legacy = "fulltext_acquisition_queue_legacy"
        self.connection.execute("PRAGMA foreign_keys=OFF")
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            self.connection.execute(f"DROP TABLE IF EXISTS {legacy}")
            self.connection.execute(f"ALTER TABLE fulltext_acquisition_queue RENAME TO {legacy}")
            self.connection.execute(_queue_table_sql())
            old_columns = {str(item[1]) for item in self.connection.execute(f"PRAGMA table_info({legacy})")}
            new_columns = [str(item[1]) for item in self.connection.execute("PRAGMA table_info(fulltext_acquisition_queue)")]
            insert_columns: list[str] = []
            select_expressions: list[str] = []
            for column in new_columns:
                if column == "production_lane":
                    insert_columns.append(column)
                    select_expressions.append("CASE priority_tier WHEN 'M' THEN 'D' ELSE priority_tier END")
                elif column in old_columns:
                    insert_columns.append(column)
                    select_expressions.append('"' + column.replace('"', '""') + '"')
            quoted = ",".join('"' + column.replace('"', '""') + '"' for column in insert_columns)
            self.connection.execute(
                f"INSERT INTO fulltext_acquisition_queue ({quoted}) "
                f"SELECT {','.join(select_expressions)} FROM {legacy}"
            )
            self.connection.execute(f"DROP TABLE {legacy}")
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        finally:
            self.connection.execute("PRAGMA foreign_keys=ON")

    def sync_queue(self, rows: list[dict[str, Any]]) -> int:
        """Upsert queue planning fields without overwriting acquisition results."""

        now_rows = []
        reset_source_ids: list[str] = []
        for row in rows:
            queue_id = str(row["queue_id"])
            existing = self.connection.execute(
                """
                SELECT download_status,created_at,rule_version
                FROM fulltext_acquisition_queue WHERE source_id=?
                """,
                (row["source_id"],),
            ).fetchone()
            status = str(existing["download_status"]) if existing else str(row.get("download_status") or "queued")
            created_at = str(existing["created_at"]) if existing else str(row["created_at"])
            terminal_status = status in {"not_found", "paywalled", "blocked", "not_pdf", "failed_final"}
            rule_changed = bool(existing) and str(existing["rule_version"] or "") != str(row["rule_version"])
            if terminal_status and (row.get("reset_terminal") or rule_changed):
                status = "queued"
                reset_source_ids.append(str(row["source_id"]))
            now_rows.append(
                (
                    queue_id, row["source_id"], row["work_id"], row["title"], row.get("doi") or "",
                    row["priority_tier"], row["production_lane"], row["queue_priority"], row.get("priority_reason", ""),
                    row.get("topic_relevance_score", 0), row.get("evidence_likelihood_score", 0),
                    row.get("citation_count", 0), row["preferred_format"], row.get("candidate_url", ""),
                    row.get("url_source", ""), row.get("access_type", "unknown"), row.get("license", ""),
                    status, row.get("max_attempts", 3), row["rule_version"], created_at, row["updated_at"],
                    row.get("metadata_enrichment_status", ""), row.get("fulltext_status", "pending"),
                    row.get("acquisition_status", "queued"), row.get("publisher_url", ""),
                    row.get("manual_access_url", ""),
                )
            )
        self.connection.executemany(
            """
            INSERT INTO fulltext_acquisition_queue(
                queue_id,source_id,work_id,title,doi,priority_tier,production_lane,queue_priority,
                priority_reason,topic_relevance_score,evidence_likelihood_score,citation_count,
                preferred_format,candidate_url,url_source,access_type,license,download_status,
                max_attempts,rule_version,created_at,updated_at,metadata_enrichment_status,
                fulltext_status,acquisition_status,publisher_url,manual_access_url
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(source_id) DO UPDATE SET
                work_id=excluded.work_id,title=excluded.title,doi=excluded.doi,
                priority_tier=excluded.priority_tier,production_lane=excluded.production_lane,
                queue_priority=excluded.queue_priority,
                priority_reason=excluded.priority_reason,
                topic_relevance_score=excluded.topic_relevance_score,
                evidence_likelihood_score=excluded.evidence_likelihood_score,
                citation_count=excluded.citation_count,preferred_format=excluded.preferred_format,
                candidate_url=excluded.candidate_url,url_source=excluded.url_source,
                access_type=excluded.access_type,license=excluded.license,
                max_attempts=excluded.max_attempts,rule_version=excluded.rule_version,
                metadata_enrichment_status=excluded.metadata_enrichment_status,
                publisher_url=excluded.publisher_url,
                manual_access_url=excluded.manual_access_url,
                updated_at=excluded.updated_at
            """,
            now_rows,
        )
        for source_id in reset_source_ids:
            self.connection.execute(
                """
                UPDATE fulltext_acquisition_queue
                SET download_status='queued',fulltext_status='pending',acquisition_status='queued',
                    failure_reason='',http_status=NULL,content_type='',resolved_url='',
                    local_path='',file_size=0,sha256='',last_attempt_at='',
                    next_attempt_at='',lease_owner='',lease_at='',attempt_count=0
                WHERE source_id=?
                """,
                (source_id,),
            )
        self.connection.execute(
            """
            UPDATE fulltext_acquisition_queue
            SET fulltext_status='available',
                acquisition_status=CASE
                    WHEN download_status='local_existing' THEN 'local_existing'
                    WHEN acquisition_status IN ('','pending','queued') THEN 'validated'
                    ELSE acquisition_status
                END,
                failure_reason=''
            WHERE download_status IN ('validated','local_existing')
            """
        )
        current_ids = [str(row["source_id"]) for row in rows]
        if current_ids:
            placeholders = ",".join("?" for _ in current_ids)
            self.connection.execute(
                f"DELETE FROM fulltext_acquisition_queue WHERE source_id NOT IN ({placeholders})",
                current_ids,
            )
        else:
            self.connection.execute("DELETE FROM fulltext_acquisition_queue")
        self.connection.commit()
        return len(now_rows)

    def queued_source_ids(self, limit: int | None = None, force: bool = False) -> list[str]:
        statuses = ["queued", "failed_retryable", "downloading"]
        params: list[Any] = []
        if force:
            where = "1=1"
        else:
            placeholders = ",".join("?" for _ in statuses)
            where = (
                f"download_status IN ({placeholders}) "
                "AND (attempt_count < max_attempts OR acquisition_status='retry_pending')"
            )
            params.extend(statuses)
        sql = f"SELECT source_id FROM fulltext_acquisition_queue WHERE {where} ORDER BY queue_priority,source_id"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        return [str(row[0]) for row in self.connection.execute(sql, params)]

    def all_queue_source_ids(self) -> list[str]:
        return [
            str(row[0])
            for row in self.connection.execute(
                "SELECT source_id FROM fulltext_acquisition_queue ORDER BY queue_priority,source_id"
            )
        ]

    def queue_attempt_count(self, source_id: str) -> tuple[int, int]:
        row = self.connection.execute(
            "SELECT attempt_count,max_attempts FROM fulltext_acquisition_queue WHERE source_id=?",
            (source_id,),
        ).fetchone()
        return (int(row[0]), int(row[1])) if row else (0, 3)

    def mark_queue_attempt(self, source_id: str, now: str) -> None:
        self.connection.execute(
            """
            UPDATE fulltext_acquisition_queue
            SET download_status='downloading',attempt_count=attempt_count+1,
                last_attempt_at=?,updated_at=?,failure_reason=''
            WHERE source_id=?
            """,
            (now, now, source_id),
        )
        self.connection.commit()

    def update_queue_status(
        self,
        source_id: str,
        status: str,
        now: str,
        *,
        http_status: int | None = None,
        content_type: str = "",
        resolved_url: str = "",
        local_path: str = "",
        file_size: int = 0,
        sha256: str = "",
        failure_reason: str = "",
        url_source: str = "",
        access_type: str = "",
        license: str = "",
        fulltext_status: str = "",
        acquisition_status: str = "",
        publisher_url: str = "",
        manual_access_url: str = "",
    ) -> None:
        if status not in QUEUE_STATUSES:
            raise ValueError(f"Unsupported queue status: {status}")
        fields: dict[str, Any] = {
            "download_status": status,
            "http_status": http_status,
            "content_type": content_type,
            "resolved_url": resolved_url,
            "local_path": local_path,
            "file_size": file_size,
            "sha256": sha256,
            "failure_reason": failure_reason,
            "updated_at": now,
        }
        if url_source:
            fields["url_source"] = url_source
        if access_type:
            fields["access_type"] = access_type
        if license:
            fields["license"] = license
        if fulltext_status:
            fields["fulltext_status"] = fulltext_status
        if acquisition_status:
            fields["acquisition_status"] = acquisition_status
        if publisher_url:
            fields["publisher_url"] = publisher_url
        if manual_access_url:
            fields["manual_access_url"] = manual_access_url
        assignments = ",".join(f"{name}=?" for name in fields)
        self.connection.execute(
            f"UPDATE fulltext_acquisition_queue SET {assignments} WHERE source_id=?",
            [*fields.values(), source_id],
        )
        self.connection.commit()

    def export_queue(self, path: Path) -> int:
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = self.connection.execute(
            "SELECT * FROM fulltext_acquisition_queue ORDER BY queue_priority,source_id"
        ).fetchall()
        temporary = unique_part_path(path)
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=QUEUE_COLUMNS, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow({column: row[column] if row[column] is not None else "" for column in QUEUE_COLUMNS})
        replace_with_retry(temporary, path)
        return len(rows)

    def queue_summary(self) -> dict[str, Any]:
        statuses = {
            str(row["download_status"]): int(row["count"])
            for row in self.connection.execute(
                "SELECT download_status,COUNT(*) count FROM fulltext_acquisition_queue GROUP BY download_status"
            )
        }
        tiers = {
            str(row["priority_tier"]): int(row["count"])
            for row in self.connection.execute(
                "SELECT priority_tier,COUNT(*) count FROM fulltext_acquisition_queue GROUP BY priority_tier"
            )
        }
        return {"queue_rows": sum(statuses.values()), "queue_status_distribution": statuses, "queue_tier_distribution": tiers}

    def start_run(self, run_id: str, started_at: str, config: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT INTO fetch_runs(run_id,started_at,status,config_json) VALUES (?,?,'running',?)",
            (run_id, started_at, json.dumps(config, ensure_ascii=False, sort_keys=True)),
        )
        self.connection.commit()

    def finish_run(self, run_id: str, completed_at: str, status: str, summary: dict[str, Any], error: str = "") -> None:
        self.connection.execute(
            "UPDATE fetch_runs SET completed_at=?,status=?,summary_json=?,error_message=? WHERE run_id=?",
            (completed_at, status, json.dumps(summary, ensure_ascii=False, sort_keys=True), error, run_id),
        )
        self.connection.commit()

    def record_event(self, run_id: str, source_id: str, action: str, status: str, created_at: str, url: str = "", detail: str = "") -> None:
        self.connection.execute(
            "INSERT INTO fetch_events(run_id,source_id,action,url,status,detail,created_at) VALUES (?,?,?,?,?,?,?)",
            (run_id, source_id, action, url, status, detail, created_at),
        )
        self.connection.commit()

    def upsert_artifact(self, record: ArtifactRecord) -> str:
        location = record.fulltext_url or record.local_path
        fulltext_id = artifact_id(record.source_id, record.fulltext_type, location)
        existing = self.connection.execute(
            "SELECT fetch_status FROM fulltext_source WHERE fulltext_id=?", (fulltext_id,)
        ).fetchone()
        if existing and existing["fetch_status"] == "success" and record.fetch_status != "success":
            self.connection.execute(
                "UPDATE fulltext_source SET last_checked_at=?,updated_at=? WHERE fulltext_id=?",
                (record.last_checked_at, record.updated_at, fulltext_id),
            )
        else:
            values = record.to_dict()
            # Metadata APIs legitimately return a missing DOI as NULL.  The
            # acquisition table uses an empty string for that state so every
            # failure/success path remains writable and rerunnable.
            values["doi"] = values.get("doi") or ""
            columns = [column for column in FULLTEXT_COLUMNS if column != "fulltext_id"]
            placeholders = ",".join("?" for _ in columns)
            updates = ",".join(f"{column}=excluded.{column}" for column in columns if column != "created_at")
            self.connection.execute(
                f"""
                INSERT INTO fulltext_source(fulltext_id,{','.join(columns)})
                VALUES (?,{placeholders})
                ON CONFLICT(fulltext_id) DO UPDATE SET {updates}
                """,
                [fulltext_id] + [values[column] for column in columns],
            )
        self.connection.commit()
        return fulltext_id

    def successful_artifacts(self, source_id: str) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT * FROM fulltext_source
            WHERE source_id=? AND fetch_status='success' AND content_scope='fulltext'
            ORDER BY CASE fulltext_type WHEN 'local_pdf' THEN 1 WHEN 'pdf' THEN 2 ELSE 3 END, created_at
            """,
            (source_id,),
        ).fetchall()

    def exhausted_candidate_urls(self, source_id: str) -> set[str]:
        return {
            str(row[0])
            for row in self.connection.execute(
                """
                SELECT DISTINCT fulltext_url FROM fulltext_source
                WHERE source_id=? AND fulltext_url<>''
                  AND fetch_status IN ('failed','skipped')
                """,
                (source_id,),
            )
        }

    def successful_path_for_hash(self, content_hash: str) -> str:
        row = self.connection.execute(
            """
            SELECT local_path FROM fulltext_source
            WHERE content_hash=? AND fetch_status='success' AND local_path<>''
            ORDER BY CASE fulltext_type WHEN 'local_pdf' THEN 1 WHEN 'pdf' THEN 2 ELSE 3 END
            LIMIT 1
            """,
            (content_hash,),
        ).fetchone()
        return str(row[0]) if row else ""

    def refresh_primary(self, source_id: str) -> None:
        self.connection.execute("UPDATE fulltext_source SET is_primary=0 WHERE source_id=?", (source_id,))
        row = self.connection.execute(
            """
            SELECT fulltext_id FROM fulltext_source
            WHERE source_id=? AND fetch_status='success' AND content_scope='fulltext'
            ORDER BY CASE fulltext_type WHEN 'local_pdf' THEN 1 WHEN 'pdf' THEN 2 ELSE 3 END, created_at
            LIMIT 1
            """,
            (source_id,),
        ).fetchone()
        if row:
            self.connection.execute("UPDATE fulltext_source SET is_primary=1 WHERE fulltext_id=?", (row[0],))
        self.connection.commit()

    def primary_artifacts(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT * FROM fulltext_source WHERE is_primary=1 AND fetch_status='success' ORDER BY source_id"
        ).fetchall()

    def latest_run(self) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT * FROM fetch_runs ORDER BY started_at DESC LIMIT 1").fetchone()
        if not row:
            return None
        data = dict(row)
        data["config"] = json.loads(data.pop("config_json"))
        data["summary"] = json.loads(data.pop("summary_json"))
        return data

    def export(self, metadata: Iterable[MetadataRecord], source_csv: Path, coverage_csv: Path) -> tuple[int, int]:
        source_csv.parent.mkdir(parents=True, exist_ok=True)
        rows = self.connection.execute("SELECT * FROM fulltext_source ORDER BY source_id, is_primary DESC, fulltext_type, fulltext_url").fetchall()
        source_temporary = unique_part_path(source_csv)
        with source_temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FULLTEXT_COLUMNS, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow({column: row[column] if row[column] is not None else "" for column in FULLTEXT_COLUMNS})
        replace_with_retry(source_temporary, source_csv)

        records = list(metadata)
        coverage_temporary = unique_part_path(coverage_csv)
        with coverage_temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=COVERAGE_COLUMNS, lineterminator="\n")
            writer.writeheader()
            for record in records:
                artifacts = self.connection.execute(
                    "SELECT * FROM fulltext_source WHERE source_id=? ORDER BY is_primary DESC, fulltext_type",
                    (record.source_id,),
                ).fetchall()
                successes = [row for row in artifacts if row["fetch_status"] == "success" and row["content_scope"] == "fulltext"]
                failures = [row for row in artifacts if row["fetch_status"] in {"failed", "skipped"}]
                primary = next((row for row in successes if row["is_primary"]), successes[0] if successes else None)
                checked = max((str(row["last_checked_at"]) for row in artifacts), default="")
                queue = self.connection.execute(
                    """
                    SELECT fulltext_status,acquisition_status,failure_reason,publisher_url,manual_access_url
                    FROM fulltext_acquisition_queue WHERE source_id=?
                    """,
                    (record.source_id,),
                ).fetchone()
                fulltext_status = (
                    "available"
                    if successes
                    else str(queue["fulltext_status"] if queue else "pending")
                )
                acquisition_status = (
                    "acquired"
                    if successes
                    else str(queue["acquisition_status"] if queue else "not_started")
                )
                terminal_reason = (
                    ""
                    if successes
                    else str(queue["failure_reason"] if queue else "")
                )
                fallback_publisher_url = (
                    f"https://doi.org/{record.doi}"
                    if record.doi
                    else record.source_link or record.html_url
                )
                writer.writerow(
                    {
                        "source_id": record.source_id,
                        "doi": record.doi,
                        "title": record.title,
                        "availability_status": "available" if successes else "unavailable",
                        "primary_fulltext_type": primary["fulltext_type"] if primary else "",
                        "primary_local_path": primary["local_path"] if primary else "",
                        "successful_artifact_count": len(successes),
                        "failed_attempt_count": len(failures),
                        "failure_reasons": "; ".join(sorted({str(row["failure_reason"]) for row in failures if row["failure_reason"]})),
                        "last_checked_at": checked,
                        "fulltext_status": fulltext_status,
                        "acquisition_status": acquisition_status,
                        "failure_reason": terminal_reason,
                        "publisher_url": str(queue["publisher_url"] if queue else fallback_publisher_url),
                        "manual_access_url": str(queue["manual_access_url"] if queue else ""),
                    }
                )
        replace_with_retry(coverage_temporary, coverage_csv)
        return len(rows), len(records)

    def coverage_summary(self, metadata: Iterable[MetadataRecord]) -> dict[str, Any]:
        available = 0
        unavailable: list[dict[str, str]] = []
        type_counts = {"local_pdf": 0, "pdf": 0, "html": 0}
        for record in metadata:
            rows = self.successful_artifacts(record.source_id)
            if rows:
                available += 1
                primary_type = str(rows[0]["fulltext_type"])
                type_counts[primary_type] += 1
            else:
                reasons = self.connection.execute(
                    "SELECT DISTINCT failure_reason FROM fulltext_source WHERE source_id=? AND failure_reason<>''",
                    (record.source_id,),
                ).fetchall()
                unavailable.append(
                    {
                        "source_id": record.source_id,
                        "reason": "; ".join(str(row[0]) for row in reasons) or "no_successful_fulltext_candidate",
                    }
                )
        return {
            "metadata_total": available + len(unavailable),
            "available_sources": available,
            "unavailable_sources": len(unavailable),
            "primary_type_distribution": type_counts,
            "unavailable_detail": unavailable,
        }
