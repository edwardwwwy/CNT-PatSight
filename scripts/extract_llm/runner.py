from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .package import build_package, canonical_json
from .normalizer import normalize_payload
from .validator import validate_payload


RUNNER_VERSION = "qwen_llama_completion_v1"
DEFAULT_MODEL = Path("models/Qwen3-14B-Q4_K_M.gguf")
DEFAULT_SCHEMA = Path("config/llm_extraction.schema.json")
DEFAULT_PROMPT = Path("config/prompts/qwen_cnt_extraction_v1.txt")
DEFAULT_SECTION_CSV = Path("data/interim/extraction_candidates/paper_text_section.csv")
DEFAULT_SPAN_CSV = Path("data/interim/extraction_candidates/candidate_experiment_span.csv")
DEFAULT_STAGE_DIR = Path("data/interim/llm_extraction")
DEFAULT_REVIEW_DIR = Path("data/review/llm_extraction")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_first_json(stdout: str) -> tuple[dict[str, Any], int]:
    start = stdout.find("{")
    if start < 0:
        raise ValueError("llama-completion stdout did not contain a JSON object")
    raw = stdout[start:]
    repaired: list[str] = []
    in_string = False
    escaped = False
    repair_count = 0
    for char in raw:
        if in_string and not escaped and ord(char) < 32:
            repair_count += 1
            repaired.append({"\n": "\\n", "\r": "\\r", "\t": "\\t"}.get(char, f"\\u{ord(char):04x}"))
            continue
        repaired.append(char)
        if char == '"' and not escaped:
            in_string = not in_string
        escaped = char == "\\" and not escaped
        if char != "\\":
            escaped = False
    decoder = json.JSONDecoder()
    value, _ = decoder.raw_decode("".join(repaired))
    if not isinstance(value, dict):
        raise ValueError("llama-completion output JSON was not an object")
    return value, repair_count


class LlmExtractionRunner:
    def __init__(
        self,
        root: Path,
        model_path: Path,
        schema_path: Path,
        prompt_path: Path,
        section_csv: Path,
        span_csv: Path,
        stage_dir: Path = DEFAULT_STAGE_DIR,
        review_dir: Path = DEFAULT_REVIEW_DIR,
        runtime_path: Path | None = None,
        device: str = "Vulkan0",
        context_size: int = 16384,
        max_tokens: int = 7500,
        max_chars: int = 10000,
        max_spans: int = 80,
        timeout_seconds: int = 900,
    ) -> None:
        self.root = root.resolve()
        self.model_path = (self.root / model_path).resolve() if not model_path.is_absolute() else model_path.resolve()
        self.schema_path = (self.root / schema_path).resolve() if not schema_path.is_absolute() else schema_path.resolve()
        self.prompt_path = (self.root / prompt_path).resolve() if not prompt_path.is_absolute() else prompt_path.resolve()
        self.section_csv = (self.root / section_csv).resolve() if not section_csv.is_absolute() else section_csv.resolve()
        self.span_csv = (self.root / span_csv).resolve() if not span_csv.is_absolute() else span_csv.resolve()
        self.stage_dir = (self.root / stage_dir).resolve() if not stage_dir.is_absolute() else stage_dir.resolve()
        self.review_dir = (self.root / review_dir).resolve() if not review_dir.is_absolute() else review_dir.resolve()
        self.runtime_path = (self.root / runtime_path).resolve() if runtime_path and not runtime_path.is_absolute() else (runtime_path.resolve() if runtime_path else None)
        self.device = device
        self.context_size = context_size
        self.max_tokens = max_tokens
        self.max_chars = max_chars
        self.max_spans = max_spans
        self.timeout_seconds = timeout_seconds

    @property
    def request_dir(self) -> Path:
        return self.stage_dir / "requests"

    @property
    def raw_dir(self) -> Path:
        return self.stage_dir / "raw"

    @property
    def validated_dir(self) -> Path:
        return self.stage_dir / "validated"

    @property
    def report_dir(self) -> Path:
        return self.stage_dir / "reports"

    def runtime_executable(self) -> Path:
        if self.runtime_path:
            return self.runtime_path
        bundled = self.root / ".tools/llama.cpp/current/llama-completion.exe"
        if bundled.exists():
            return bundled
        raise FileNotFoundError("No llama-completion executable; pass --runtime or install the local runtime")

    def package(self, source_id: str) -> dict[str, Any]:
        return build_package(source_id, self.section_csv, self.span_csv, self.max_chars, self.max_spans)

    def request_identity(self, package: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        model_stat = self.model_path.stat()
        identity = {
            "runner_version": RUNNER_VERSION,
            "model_name": self.model_path.name,
            "model_size": model_stat.st_size,
            "model_mtime_ns": model_stat.st_mtime_ns,
            "schema_sha256": hashlib.sha256(self.schema_path.read_bytes()).hexdigest(),
            "prompt_sha256": hashlib.sha256(self.prompt_path.read_bytes()).hexdigest(),
            "package": package,
            "device": self.device,
            "context_size": self.context_size,
            "max_tokens": self.max_tokens,
        }
        request_hash = hashlib.sha256(canonical_json(identity).encode("utf-8")).hexdigest()[:20]
        return request_hash, identity

    def _prompt(self, package: dict[str, Any]) -> str:
        instruction = self.prompt_path.read_text(encoding="utf-8").replace("{{INPUT_JSON}}", json.dumps(package, ensure_ascii=False, indent=2))
        return "<|im_start|>system\nYou are a strict scientific extractor. Output only the requested JSON. /no_think<|im_end|>\n<|im_start|>user\n" + instruction + "<|im_end|>\n<|im_start|>assistant\n"

    def _paths(self, source_id: str, request_hash: str) -> dict[str, Path]:
        stem = f"{source_id}__{request_hash}"
        return {
            "package": self.request_dir / f"{stem}.package.json",
            "prompt": self.request_dir / f"{stem}.prompt.txt",
            "stdout": self.raw_dir / f"{stem}.stdout.txt",
            "stderr": self.raw_dir / f"{stem}.stderr.txt",
            "validated": self.validated_dir / f"{stem}.json",
            "report": self.report_dir / f"{stem}.json",
        }

    def prepare(self, source_id: str) -> dict[str, Any]:
        package = self.package(source_id)
        request_hash, identity = self.request_identity(package)
        paths = self._paths(source_id, request_hash)
        write_json(paths["package"], package)
        paths["prompt"].parent.mkdir(parents=True, exist_ok=True)
        paths["prompt"].write_text(self._prompt(package), encoding="utf-8")
        return {"source_id": source_id, "request_hash": request_hash, "package": package, "identity": identity, "paths": paths}

    def run_one(self, source_id: str, force: bool = False) -> dict[str, Any]:
        prepared = self.prepare(source_id)
        paths = prepared["paths"]
        if paths["validated"].exists() and not force:
            validation = read_json(paths["report"]).get("validation", {}) if paths["report"].exists() else {}
            return {"source_id": source_id, "request_hash": prepared["request_hash"], "status": "cache_hit", "validation": validation, "paths": {key: str(value.relative_to(self.root)) for key, value in paths.items()}}
        executable = self.runtime_executable()
        command = [
            str(executable), "-m", str(self.model_path), "-dev", self.device, "-ngl", "all",
            "-c", str(self.context_size), "-n", str(self.max_tokens), "-b", "512", "-ub", "256",
            "-ctk", "q8_0", "-ctv", "q8_0", "-fa", "on", "--temp", "0", "--seed", "42",
            "--no-conversation", "--single-turn", "--simple-io", "--color", "off", "--no-display-prompt",
            "--no-warmup", "--json-schema-file", str(self.schema_path), "--file", str(paths["prompt"]),
        ]
        started = utc_now()
        try:
            completed = subprocess.run(command, cwd=self.root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=self.timeout_seconds)
            stdout = completed.stdout
            stderr = completed.stderr
            paths["stdout"].parent.mkdir(parents=True, exist_ok=True)
            paths["stdout"].write_text(stdout, encoding="utf-8")
            paths["stderr"].write_text(stderr, encoding="utf-8")
            payload, json_repair_count = extract_first_json(stdout)
            normalized_payload, normalization_issues = normalize_payload(payload, prepared["package"], self.schema_path)
            validation = validate_payload(normalized_payload, prepared["package"], self.schema_path)
            for issue in normalization_issues:
                validation["issues"].append({**issue, "severity": "warning"})
            validation["warning_count"] += len(normalization_issues)
            validation["normalization_issue_count"] = len(normalization_issues)
            write_json(paths["validated"], normalized_payload)
            status = "validated_needs_review" if validation["valid"] else "validation_failed"
            error = "" if completed.returncode == 0 else f"llama_completion_returncode_{completed.returncode}"
        except Exception as exc:
            stdout = locals().get("stdout", "")
            stderr = locals().get("stderr", "")
            paths["stdout"].parent.mkdir(parents=True, exist_ok=True)
            paths["stdout"].write_text(stdout, encoding="utf-8")
            paths["stderr"].write_text(stderr, encoding="utf-8")
            validation = {"valid": False, "status": "runner_failed", "error_count": 1, "warning_count": 0, "issues": [{"code": "runner_error", "message": str(exc), "severity": "error"}], "counts": {}, "evidence_field_coverage": {}}
            status = "runner_failed"
            error = str(exc)
        report = {
            "runner_version": RUNNER_VERSION,
            "source_id": source_id,
            "request_hash": prepared["request_hash"],
            "status": status,
            "started_at": started,
            "completed_at": utc_now(),
            "error": error,
            "json_repair_count": locals().get("json_repair_count", 0),
            "normalization_issue_count": len(locals().get("normalization_issues", [])),
            "model": str(self.model_path.relative_to(self.root)) if self.model_path.is_relative_to(self.root) else str(self.model_path),
            "runtime": str(executable.relative_to(self.root)) if 'executable' in locals() and executable.is_relative_to(self.root) else str(locals().get("executable", "")),
            "package_stats": prepared["package"].get("selection_stats", {}),
            "validation": validation,
            "paths": {key: str(value.relative_to(self.root)) for key, value in paths.items()},
        }
        write_json(paths["report"], report)
        return report

    def run(self, source_ids: Iterable[str], force: bool = False) -> dict[str, Any]:
        reports = [self.run_one(source_id, force=force) for source_id in source_ids]
        summary = {
            "runner_version": RUNNER_VERSION,
            "status": "complete" if all(report.get("status") in {"validated_needs_review", "cache_hit"} for report in reports) else "partial",
            "source_count": len(reports),
            "validated": sum(report.get("status") == "validated_needs_review" for report in reports),
            "cache_hits": sum(report.get("status") == "cache_hit" for report in reports),
            "failed": sum(report.get("status") not in {"validated_needs_review", "cache_hit"} for report in reports),
            "reports": reports,
            "completed_at": utc_now(),
        }
        write_json(self.report_dir / "latest.json", summary)
        return summary
